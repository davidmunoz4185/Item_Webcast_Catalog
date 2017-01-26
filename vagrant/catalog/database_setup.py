import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()

def get_current_time():
    return datetime.datetime.now()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
        	'id': self.id,
            'name': self.name,
        }

class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    description = Column(String(750))
    cat_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    date = Column(DateTime, default=get_current_time, onupdate=get_current_time)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


    @property
    def serialize(self):
		return {
			'cat_id': self.cat_id,
			'description': self.description,
			'id': self.id,
			'title': self.title,
		}

engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)