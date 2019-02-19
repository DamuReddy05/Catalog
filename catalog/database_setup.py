#! /usr/bin/env python3
from sqlalchemy import ForeignKey, Integer, String, Column
import os
import sys
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    """docstring for User"""
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    email = Column(String(20), nullable=False)
    user_pic = Column(String(250), nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'email': self.email,
            'user_pic': self.user_pic,
        }


class CarBrand(Base):

    __tablename__ = "CarBrand"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    ratings = Column(Integer)
    image = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'ratings': self.ratings,
            'image': self.image,

        }


class Car(Base):
    """docstring for Car"""
    __tablename__ = 'car'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(300), nullable=False)
    price = Column(String(10), nullable=False)
    variant = Column(String(10), nullable=False)
    milage = Column(String(15), nullable=False)
    year = Column(Integer, nullable=False)
    type = Column(String(20), nullable=False)
    ratings = Column(Integer)
    image1 = Column(String(100), nullable=False)
    image2 = Column(String(100), nullable=False)
    image3 = Column(String(100), nullable=False)
    image4 = Column(String(100), nullable=False)
    CarBrand_id = Column(Integer, ForeignKey('CarBrand.id'))
    user_id = Column(Integer, ForeignKey('user.id'))

    CarBrand = relationship(CarBrand)
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'variant': self.variant,
            'milage': self.milage,
            'year': self.year,
            'type': self.type,
            'ratings': self.ratings,
            'image1': self.image1,
            'image2': self.image2,
            'image3': self.image3,
            'image4': self.image4,
        }


class wishList(Base):
    """docstring for wishList"""
    __tablename__ = "wishlist"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    Car_id = Column(Integer, ForeignKey('car.id'))

    user = relationship(User)
    car = relationship(Car)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'Car_id': self.Car_id,
        }


engine = create_engine('sqlite:///carshowroom.db')

Base.metadata.create_all(engine)
