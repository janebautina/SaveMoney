import sys
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy import create_engine
from flask import session as login_session
import random
import string


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    savings = relationship("Savings", 
      cascade = "delete, delete-orphan, save-update")


class Savings(Base):
    __tablename__ = 'savings'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    items = relationship("Items", 
      cascade = "delete, delete-orphan, save-update")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
          'name': self.name,
          'id': self.id,
          }


class Items(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    price = Column(Float(presicion=2), default=0)
    picture_path = Column(String(1024))
    savings_id = Column(Integer, ForeignKey('savings.id'))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
                 'description': self.description,
                 'id': self.id,
                 'price': self.price,
                 'picture_path': self.picture_path,
             }

engine = create_engine('postgresql://catalog:catalogpwd@localhost/savemoney')
Base.metadata.create_all(engine)
