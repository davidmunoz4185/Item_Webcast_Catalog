from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Category, Item

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()
"""
Users
"""

user = User(id = 1, name="Robo Barista", email="tinnyTim@udacity.com",
       		picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(user)
session.commit()

"""
Categories
"""

category = Category(id = 1, name = "Soccer", user_id = 1)
session.add(category)
session.commit()

category = Category(id = 2, name = "Basketball", user_id = 1)
session.add(category)
session.commit()

category = Category(id = 3, name = "Baseball", user_id = 1)
session.add(category)
session.commit()

category = Category(id = 4, name = "Frisbee", user_id = 1)
session.add(category)
session.commit()

category = Category(id = 5, name = "Snowboarding", user_id = 1)
session.add(category)
session.commit()

category = Category(id = 6, name = "Rock Climbing", user_id = 1)
session.add(category)
session.commit()

category = Category(id = 7, name = "Foosball", user_id = 1)
session.add(category)
session.commit()

category = Category(id = 8, name = "Skating", user_id = 1)
session.add(category)
session.commit()

category = Category(id = 9, name = "Hockey", user_id = 1)
session.add(category)
session.commit()

"""
Items
"""

item = Item(title = "Stick", description = "Stick in order to practice Hockey", cat_id = 9, user_id = 1)
session.add(item)
session.commit()

item = Item(title = "Goggles", description = "Goggles in order to practice SnowBoarding", cat_id = 5, user_id = 1)
session.add(item)
session.commit()

item = Item(title = "SnowBoard", description = "SnowBoard in order to practice SnowBoarding", cat_id = 5, user_id = 1)
session.add(item)
session.commit()

item = Item(title = "Two Shinguards", description = "Two Shingwards in order to practice Soccer", cat_id = 1, user_id = 1)
session.add(item)
session.commit()

item = Item(title = "Shinguards", description = "Shingwards in order to practice Soccer", cat_id = 1, user_id = 1)
session.add(item)
session.commit()

item = Item(title = "Frisbee", description = "Frisbee in order to practice Frisbee", cat_id = 4, user_id = 1)
session.add(item)
session.commit()

item = Item(title = "Bat", description = "Bat in order to practice Baseball", cat_id = 3, user_id = 1)
session.add(item)
session.commit()

item = Item(title = "Jersey", description = "Jersey in order to practice Soccer", cat_id = 1, user_id = 1)
session.add(item)
session.commit()

item = Item(title = "Soccer Cleats", description = "Soccer Cleats in order to practice Soccer", cat_id = 1, user_id = 1)
session.add(item)
session.commit()

