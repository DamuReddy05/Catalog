#!/usr/bin/env python3
from flask import Flask, url_for, render_template
from flask import request, redirect, jsonify, flash
from flask import session as login_session
import random
import string
import requests
import os


from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from database_setup import Base, CarBrand, Car, User, wishList


app = Flask(__name__)


APP_ROUTE = os.path.dirname(os.path.abspath(__file__))


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Car.Showroom.Application"


# Connect to Database and create database session
engine = create_engine(
    'sqlite:///carshowroom.db',
    connect_args={
        'check_same_thread': False},
    echo=True)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()


# create new user
def createUser(login_session):
    name = login_session['username']
    email = login_session['email']
    user_pic = login_session['picture']
    data = User(name=name, email=email, user_pic=user_pic)
    session.add(data)
    session.commit()
    data = session.query(User).filter_by(email=email).one_or_none()
    flash("New User " + name + " created")
    return data.id

# get userid with email


def getUserId(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(
            string.ascii_uppercase +
            string.digits +
            string.ascii_lowercase) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# JSON APIs to view company Information
@app.route('/companies/json')
def carBrandjson():
    brand = session.query(CarBrand)
    return jsonify(brands=[i.serialize for i in brand])


@app.route('/companies/<int:carBrand_id>/json')
def carsJson(carBrand_id):
    carbran = session.query(Car).filter_by(CarBrand_id=carBrand_id).all()
    return jsonify(cars=[i.serialize for i in carbran])


@app.route('/companies/<int:carBrand_id>/<int:car_id>/json')
def singleCarJson(carBrand_id, car_id):
    single = session.query(Car).filter_by(id=car_id).all()
    return jsonify(cardetailes=[i.serialize for i in single])


# show all companies
@app.route('/')
@app.route('/companies')
def carBrand():
    comp = session.query(CarBrand).all()
    sender = 'carBrand'
    print(sender)
    if 'email' in login_session:
        owner = getUserId(login_session['email'])
        return render_template(
            'CarBrand.html',
            comp=comp,
            owner=owner,
            sender=sender)
    else:
        return render_template('CarBrand.html', comp=comp, sender=sender)


# create new brand
@app.route('/companies/new', methods=['POST'])
def newcarBrand():
    user_id = getUserId(login_session['email'])
    name = request.form['name']
    image = request.files['imagefile']
    target = os.path.join(APP_ROUTE, "static/images/CarBrand/")
    a = "static/images/CarBrand/"
    if not os.path.isdir(target):
        os.mkdir(target)

    filename = image.filename
    destiny = "".join([a, filename])
    image.save(destiny)

    newcomp = CarBrand(name=name, image=destiny, user_id=user_id)
    session.add(newcomp)
    session.commit()
    flash("New Brand " + name + " created by " + login_session['username'])
    return redirect(url_for('carBrand'))


# Edit brand


@app.route('/companies/<int:carBrand_id>/edit', methods=["POST"])
def editBrand(carBrand_id):
    brand = session.query(CarBrand).filter_by(id=carBrand_id).one()
    user_id = getUserId(login_session['email'])
    if user_id == brand.user_id:
        if request.method == 'POST':
            brand.name = request.form['name']
            target = os.path.join(APP_ROUTE, "static/images/CarBrand/")
            a = "static/images/CarBrand/"
            if not os.path.isdir(target):
                os.mkdir(target)
            if request.files.get('imagefile'):
                image = request.files['imagefile']
                filename = image.filename
                destiny = "".join([a, filename])
                image.save(destiny)
                brand.image = destiny
            session.add(brand)
            session.commit()
            flash("Brand " + brand.name + " updated")
            return redirect(url_for('carBrand'))


# show a specific car
@app.route('/companies/<int:carBrand_id>/<int:car_id>/')
def singleCar(carBrand_id, car_id):
    brand = session.query(CarBrand).filter_by(id=carBrand_id).one()
    carbran = session.query(Car).filter_by(id=car_id).one()
    if 'username' in login_session:
        user_id = getUserId(login_session['email'])
        return render_template(
            'singlecar.html',
            brand=brand,
            user_id=user_id,
            car=carbran)
    else:
        return render_template('singlecar.html', brand=brand, car=carbran)


# show all cars
@app.route("/companies/<int:carBrand_id>")
def cars(carBrand_id):
    items = session.query(Car).filter_by(CarBrand_id=carBrand_id)
    brand = session.query(CarBrand).filter_by(id=carBrand_id).one()
    sender = 'cars'
    if 'username' in login_session:
        user_id = getUserId(login_session['email'])
        print(user_id, items, brand.id)
        return render_template(
            'cars.html',
            brand=brand,
            user_id=user_id,
            cars=items,
            sender=sender)
    else:
        return render_template(
            'cars.html',
            brand=brand,
            cars=items,
            sender=sender)


# create a new car
@app.route("/companies/<int:carBrand_id>/newcar", methods=['POST'])
def newCar(carBrand_id):
    newid = session.query(Car).order_by("-id").first()
    if not newid:
        id = 1
    else:
        id = newid.id + 1
    user_id = getUserId(login_session['email'])
    name = request.form['name']
    desc = request.form['desc']
    price = request.form['price']
    year = request.form['year']
    type = request.form['type']
    variant = request.form['variant']
    milage = request.form['milage']

    target = os.path.join(APP_ROUTE, "static/images/Cars/%s/" % id)
    a = "static/images/Cars/%s/" % id
    if not os.path.isdir(target):
        os.mkdir(target)

    image1 = request.files['image1']
    filename = image1.filename
    destiny = "".join([a, filename])
    image1.save(destiny)
    image1 = destiny

    image2 = request.files['image2']
    filename = image2.filename
    destiny = "".join([a, filename])
    image2.save(destiny)
    image2 = destiny

    image3 = request.files['image3']
    filename = image3.filename
    destiny = "".join([a, filename])
    image3.save(destiny)
    image3 = destiny

    image4 = request.files['image4']
    filename = image4.filename
    destiny = "".join([a, filename])
    image4.save(destiny)
    image4 = destiny

    newitem = Car(
        user_id=user_id,
        CarBrand_id=carBrand_id,
        name=name,
        description=desc,
        price=price,
        year=year,
        type=type,
        variant=variant,
        milage=milage,
        image1=image1,
        image2=image2,
        image3=image3,
        image4=image4)
    session.add(newitem)
    session.commit()
    flash("New Car " + name + " has been added by" + login_session['username'])
    return redirect(url_for('cars', carBrand_id=carBrand_id))


# edit a car
@app.route(
    '/companies/<int:carBrand_id>/<int:car_id>/edit',
    methods=[
        'GET',
        'POST'])
def editCar(carBrand_id, car_id):
    car = session.query(Car).filter_by(id=car_id).one()
    user_id = getUserId(login_session['email'])
    if request.method == 'POST':
        car.name = request.form['name']
        car.desc = request.form['desc']
        car.price = request.form['price']
        car.year = request.form['year']
        if request.form.get('type'):
            car.type = request.form['type']
        if request.form.get('variant'):
            car.variant = request.form['variant']
        car.milage = request.form['milage']

        target = os.path.join(APP_ROUTE, "static/images/Cars/%s/" % car_id)
        a = "static/images/Cars/%s/" % car_id
        if not os.path.isdir(target):
            os.mkdir(target)

        if request.files.get('image1'):
            image1 = request.files['image1']
            filename = image1.filename
            destiny = "".join([a, filename])
            image1.save(destiny)
            car.image1 = destiny

        if request.files.get('image2'):
            image2 = request.files['image2']
            filename = image2.filename
            destiny = "".join([a, filename])
            image2.save(destiny)
            car.image2 = destiny

        if request.files.get('image3'):
            image3 = request.files['image3']
            filename = image3.filename
            destiny = "".join([a, filename])
            image3.save(destiny)
            car.image3 = destiny

        if request.files.get('image4'):
            image4 = request.files['image4']
            filename = image4.filename
            destiny = "".join([a, filename])
            image4.save(destiny)
            car.image4 = destiny

        session.add(car)
        session.commit()
        flash("car details has been updated")
        return redirect(url_for('cars', carBrand_id=carBrand_id))
    elif 'username' in login_session:
        return render_template(
            'editcar.html',
            carbran=car,
            user_id=user_id,
            carBrand_id=carBrand_id)


# delete a car
@app.route(
    "/companies/<int:carBrand_id>/<int:car_id>/delete",
    methods=[
        'GET',
        'POST'])
def deleteCar(carBrand_id, car_id):
    carbran = session.query(Car).filter_by(id=car_id).one()
    user_id = getUserId(login_session['email'])
    if user_id == carbran.user_id:
        if request.method == 'POST':
            a = "static/images/Cars/%s" % car_id
            os.remove(carbran.image1)
            os.remove(carbran.image2)
            os.remove(carbran.image3)
            os.remove(carbran.image4)
            os.rmdir(a)
            session.delete(carbran)
            session.commit()
            flash("A car has been deleted by you ! Hope it is sold")
            return redirect(url_for('cars', carBrand_id=carBrand_id))
        else:
            return render_template(
                'deletecar.html',
                car_id=car_id,
                carBrand_id=carBrand_id)


# add specific car to wishlist
@app.route('/companies/<int:user_id>/<int:carBrand_id>/<int:car_id>/wishlist')
def addWishlist(user_id, car_id, carBrand_id):
    data = session.query(wishList).filter(
        and_(
            wishList.user_id == user_id,
            wishList.Car_id == car_id)).all()
    if data:
        flash("Car is already added to your wishlist")
        return redirect(
            url_for(
                'singleCar',
                carBrand_id=carBrand_id,
                car_id=car_id))
    newitem = wishList(user_id=user_id, Car_id=car_id)
    session.add(newitem)
    session.commit()
    flash("Car added to your wishList")
    return redirect(
        url_for(
            'singleCar',
            carBrand_id=carBrand_id,
            car_id=car_id))


# show logedin user wishlist
@app.route('/wishlist')
def wishlist():
    user_id = getUserId(login_session['email'])
    wish = session.query(wishList).filter_by(user_id=user_id).all()
    sender = "wish"
    wishcars = []
    for i in wish:
        wishcars.append(session.query(Car).filter_by(id=i.Car_id).one())
    print(wishcars)
    return render_template(
        'wishlist.html',
        wishcars=wishcars,
        user_id=user_id,
        sender=sender)


# delete a car from wishlist
@app.route('/wishlist/<int:car_id>/<int:user_id>/delete')
def delwish(car_id, user_id):
    session.query(wishList).filter(
        and_(
            wishList.user_id == user_id,
            wishList.Car_id == car_id)).delete()
    session.commit()
    flash("This Car is deleted from your wishlist")
    return redirect(url_for('wishlist'))


# clear the wishlist
@app.route('/wishlist/<int:user_id>/delete')
def clearwish(user_id):
    session.query(wishList).filter_by(user_id=user_id).delete()
    session.commit()
    flash("your wishlist is cleared")
    return redirect(url_for('wishlist'))


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
    print('error in g connect is', result.get('error'))
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        print('in result.get("error")')
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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps
                                 ('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    b = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % b
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print result
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
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps(
                'Failed to revoke token for given user.',
                400))
        response.headers['Content-Type'] = 'application/json'
        return response


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
