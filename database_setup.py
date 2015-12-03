import sys
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy_imageattach.entity import Image, image_attachment
from sqlalchemy import create_engine

Base = declarative_base()

class Savings(Base):
  __tablename__ = 'savings'
  id = Column(Integer, primary_key = True)
  name = Column(String(80), nullable = False)

class Items(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key = True)
    name = Column(String(80), nullable = False)
    description = Column(String(250))
    price = Column(Float(presicion=2), default = 0)
    date = Column(DateTime, onupdate=datetime.datetime.now)
    picture = image_attachment('ItemPicture')
    savings_id = Column(Integer, ForeignKey('savings.id'))
    savings = relationship(Savings)

class Goals(Base):
    __tablename__ = 'goals'
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    price = Column(Float(presicion=2), default = 0)
    photoFileName = Column(String, nullable = False)

class ItemPicture(Base, Image):
    """Item picture model."""
    __tablename__ = 'item_picture'
    item_id = Column(Integer, ForeignKey('items.id'), primary_key=True)
    items = relationship(Items)



engine = create_engine('sqlite:///savemoney.db')
Base.metadata.create_all(engine)
