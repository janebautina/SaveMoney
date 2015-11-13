import sys
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
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
    savings_id = Column(Integer, ForeignKey('savings.id'))
    savings = relationship(Savings)

engine = create_engine('sqlite:///savemoney.db')
# Initialize database schema (create tables)
Base.metadata.create_all(engine)
