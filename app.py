from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Brand, Model, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

engine = create_engine('sqlite:///carmodels.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# home page before log in
@app.route('/')
@app.route('/home')
def home():
    if 'username' not in login_session:
        brand = session.query(Brand).order_by(asc(Brand.name))
        return render_template('brands.html', brands=brand)
    else:
        return redirect('/home/in')


# show models in the brand before log in
@app.route('/home/<int:brand_id>/')
def showbrand(brand_id):
    brand = session.query(Brand).filter_by(id=brand_id).one()
    models = session.query(Model).filter_by(brand_id=brand_id).all()
    return render_template('models.html', brand=brand, models=models)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user '
                                            'is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;' \
              '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke '
                                            'token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/home/signedin', methods=['GET', 'POST'])
def signed():
    if 'username' not in login_session:
        print("not in")
        return redirect('/login')
    else:
        return redirect('/home/in')


# home menu after log in
@app.route('/home/in')
def home2():
    if 'username' not in login_session:
        print("not in")
        return redirect('/login')
    else:
        brand = session.query(Brand).order_by(asc(Brand.name))
        return render_template('addbrand.html', brands=brand)


@app.route('/home/signedin/<int:brand_id>/')
def menuwithfunctions(brand_id):
    if 'username' not in login_session:
        print("not in")
        return redirect('/login')
    else:
        brand = session.query(Brand).filter_by(id=brand_id).one()
        models = session.query(Model).filter_by(brand_id=brand_id).all()
        return render_template('menufunctions.html',
                               brand=brand, models=models)


@app.route('/home/signedin/<int:brand_id>/new', methods=['GET', 'POST'])
def newMenuItem(brand_id):
    if 'username' not in login_session:
        print("not in")
        return redirect('/login')
    else:
        if request.method == 'POST':
            newItem = Model(name=request.form['name'], brand_id=brand_id,
                            description="no description yet",
                            cc="unknown cc", picture=login_session['email'])
            session.add(newItem)
            session.commit()
            flash("new car model created!")
            return redirect(url_for('menuwithfunctions', brand_id=brand_id))
        else:
            return render_template('newmenuitem.html', brand_id=brand_id)


@app.route('/home/signedin/<int:brand_id>/<int:model_id>/edit',
           methods=['GET', 'POST'])
def editMenuItem(brand_id, model_id):
    if 'username' not in login_session:
        print("not in")
        return redirect('/login')
    else:
        editedItem = session.query(Model).filter_by(id=model_id).one()
        if login_session['email'] == editedItem.picture:
            if request.method == 'POST':
                if request.form['name']:
                    editedItem.name = request.form['name']
                if request.form['cc']:
                    editedItem.cc = request.form['cc']
                if request.form['description']:
                    editedItem.description = request.form['description']
                session.add(editedItem)
                session.commit()
                flash("Item is Edited ")
                return redirect(url_for('menuwithfunctions',
                                        brand_id=brand_id))
            else:
                return render_template(
                    'editmenuitem.html', brand_id=brand_id,
                    model_id=model_id, item=editedItem)
        else:
            return redirect(url_for('menuwithfunctions',
                                    brand_id=brand_id))


@app.route('/home/signedin/<int:brand_id>/<int:model_id>/delete',
           methods=['GET', 'POST'])
def deleteMenuItem(brand_id, model_id):
    if 'username' not in login_session:
        print("not in")
        return redirect('/login')
    else:
        itemToDelete = session.query(Model).filter_by(id=model_id).one()
        if login_session['email'] == itemToDelete.picture:
            if request.method == 'POST':
                session.delete(itemToDelete)
                session.commit()
                flash("Item is Deleted ")
                return redirect(url_for('menuwithfunctions',
                                        brand_id=brand_id))
            else:
                return render_template('deletemenuitem.html',
                                       item=itemToDelete)
        else:
            return redirect(url_for('menuwithfunctions', brand_id=brand_id))


@app.route('/home/<int:brand_id>/<int:model_id>/description/')
def getdiscription(brand_id, model_id):
    descrip = session.query(Model).filter_by(id=model_id).one()
    return descrip.description


@app.route('/home/in/addbrand/', methods=['GET', 'POST'])
def addbrand():
    if 'username' not in login_session:
        print("not in")
        return redirect('/login')
    else:
        if request.method == 'POST':
            newItem = Brand(name=request.form['name'])
            session.add(newItem)
            session.commit()
            flash("new brand created!")
            return redirect(url_for('home2'))
        else:
            return render_template('newbrand.html')


# return json for the models in the brand with brand_id
# example
# http://localhost:8080/models/1/JSON
@app.route('/models/<int:brand_id>/JSON')
def carBrandJSON(brand_id):
    items = session.query(Model).filter_by(brand_id=brand_id).all()
    return jsonify(models=[i.serialize for i in items])


@app.route('/models/<int:brand_id>/<int:model_id>/JSON')
def carModelJSON(brand_id, model_id):
    item = session.query(Model).filter_by(id=model_id).one()
    return jsonify(models=[item.serialize])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'

    app.debug = True
    app.run(host='0.0.0.0', port=8080)
