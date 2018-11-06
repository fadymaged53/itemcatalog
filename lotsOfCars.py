from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Brand, Base, Model, User

engine = create_engine('sqlite:///carmodels.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()


# Create dummy user
User1 = User(name="fady maged", email="fadymaged53@gmail.com")
session.add(User1)
session.commit()

# BMW
brand1 = Brand(user_id=1, name="BMW")

session.add(brand1)
session.commit()

menuItem2 = Model(user_id=1, name="118i", description="bmw first series ",
                     price="$20000", cc="1800cc", brand=brand1)

session.add(menuItem2)
session.commit()


menuItem1 = Model(user_id=1, name="220", description="bmw second series",
                     price="$22000", cc="2000cc", brand=brand1)

session.add(menuItem1)
session.commit()

menuItem2 = Model(user_id=1, name="318i", description="bmw third series",
                     price="$55000", cc="1800cc", brand=brand1)

session.add(menuItem2)
session.commit()

menuItem3 = Model(user_id=1, name="740L", description="bmw luxury car",
                     price="$100000", cc="4000cc", brand=brand1)

session.add(menuItem3)
session.commit()




# Mercedes
brand2 = Brand(user_id=1, name="Mercedes")

session.add(brand2)
session.commit()


menuItem1 = Model(user_id=1, name="A class", description="family car from Mercedes",
                     price="$20000", cc="1800cc", brand=brand2)

session.add(menuItem1)
session.commit()

menuItem2 = Model(user_id=1, name="B class",
                     description=" B class family car from Mercedes", price="$25000", cc="2000", brand=brand2)

session.add(menuItem2)
session.commit()

menuItem3 = Model(user_id=1, name="S class", description="luxury car from Mercedes",
                     price="110000", cc="4500cc", brand=brand2)

session.add(menuItem3)
session.commit()


# audi
brand1 = Brand(user_id=1, name="Audi")

session.add(brand1)
session.commit()


menuItem1 = Model(user_id=1, name="Q7", description="suv from audi",
                     price="$29999", cc="3000cc", brand=brand1)

session.add(menuItem1)
session.commit()




print ("added menu items!")
