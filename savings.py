from flask import Flask, render_template, request, redirect, url_for
from flask import flash, jsonify, make_response
from flask import session as login_session

from functools import wraps

import os
import errno
import json
import inspect
import requests
import httplib2
import time
import random
import string

import sys

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker

from PIL import Image, ExifTags
from PIL.Image import core as _imaging

from database_setup import Base, Savings, Items, User

from werkzeug import secure_filename

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

base_dir = '/var/www/html'

app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'))
app.secret_key = 'super_secret_key'
app.debug = True

google_client_secret_path = os.path.join(base_dir, 'client_secret.json')
CLIENT_ID = json.loads(open(google_client_secret_path, 'r').read())['web']['client_id']
APPLICATION_NAME = "Savings"

#engine = create_engine('sqlite:///savemoneywithusers.db')
#engine = create_engine('postgresql://catalog:catalogpwd@127.0.0.1/savemoney')
engine = create_engine('postgresql://savemoneyadmin:savemoneyadminpwd@127.0.0.1/savemoney')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

image_storage_dir = os.path.join(base_dir, 'static/images/uploads')
""" The direstory's path where uploaded images are stored.
"""
# if image_storage_dir doesn't exist, make the directory
if not os.path.exists(image_storage_dir):
    os.mkdir(image_storage_dir)

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


# ------------auxiliary functions--------------------------------------------
def rotate_image(image_path):
    """ Function that rotates an image based exif orientation

        Args:
            image_path (string): an image to rotate path 

        Returns: 
            string: rotated image path

        Raises:
            AttributeError: if there is no exif data

    """
    # Open file with Pillow
    image = Image.open(image_path)
    # If no ExifTags, no rotating needed
    # Grab orientation value.
    try:
        if hasattr(image, '_getexif'): # only present in JPEGs
            for orientation in ExifTags.TAGS.keys(): 
                if ExifTags.TAGS[orientation]=='Orientation':
                    print "Hello"
                    return image_path
        image_exif = image._getexif()
        print "rotate" + image_exif
    except AttributeError:
        print >>sys.stderr, "Cannot get EXIF data for %s" % image_path
        return image_path

    if image_exif is None:
        return image_path
    if image_exif:
        image_orientation = image_exif[274]
    # Rotate depending on orientation.
    if image_orientation == 3:
        angle = 180
    elif image_orientation == 6:
        angle = 270
    elif image_orientation == 8:
        angle = 90
    else:
        print >>sys.stderr, "Unknown image orientation: %s, not rotating" % \
            image_orientation
        return image_path
    rotated = image.rotate(angle, expand=1)
    #rotated.thumbnail(size, Image.ANTIALIAS)  
    # Save rotated image.
    path_without_ext, ext = os.path.splitext(image_path)
    new_image_path = path_without_ext + '__rotated' + ext
    rotated.save(new_image_path)
    os.remove(image_path)
    return new_image_path


def line_number(): 
    """Returns the current line number in our program. This is mostly used 
    for debugging http://code.activestate.com/recipes/145297-grabbing-the
    -current-line-number-easily/

    """
    return inspect.currentframe().f_back.f_lineno


def allowed_file(filename):
    """Check whath files are allowed to upload from local machine

    """
    return '.' in filename and \
      filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def getUserInfo(user_id):
    """Retrives the user information.

    Args: 
        user_id(int): user id

    Returns: 
        list: user's id, name, email and picture path

    """
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """Retrives user id by given email

    Args:
        email(String): user email

    Returns:
        int: user id if it's exists

    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def createUser(login_session):
    """Creates a new user using his/her facebook or google+ information
    
    Args:
        login_session: facebook or google+ login_session

    Returns:
        int: new user id

    """
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def list_sums(savings_id):
    """Calculates the sum of all saving items

    Args: 
        savings_id(int): saving id

    Returns:
         int: sum of saving items prices

    """
    savings = session.query(Savings).filter_by(id=savings_id).one()
    items = session.query(Items).filter_by(savings_id=savings_id)
    sum = 0
    for item in items:
        sum += item.price
    return sum

# -------------END auxiliary functions----------------------------------------
# -------------Users login functions------------------------------------------


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in login_session:
            return redirect(url_for('showLogin', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login')
def showLogin():
    """Shows login page
    """
    state = ''.join(random.choice(string.ascii_uppercase +
                    string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template(
      'login.html', STATE=state, google_oauth_client_id=CLIENT_ID)

# --------------END Users login functions-------------------------------------

# --------------JSON APIs-----------------------------------------------------


@app.route('/savings/<int:savings_id>/items/JSON')
def restaurantMenuJSON(savings_id):
    saving = session.query(Savings).filter_by(id=savings_id).one()
    items = session.query(Items).filter_by(savings_id=savings_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/savings/<int:savings_id>/items/<int:items_id>/JSON')
def menuItemJSON(savings_id, items_id):
    item = session.query(Items).filter_by(id=items_id).one()
    return jsonify(item=item.serialize)


@app.route('/users/JSON')
def usersJSON():
    users = session.query(User).all()
    return jsonify(users=[u.serialize for u in users])


@app.route('/savings/JSON')
def savingsJSON():
    savings = session.query(Savings).all()
    return jsonify(savings=[s.serialize for s in savings])


# -----------------GOOGLE_OAUTH2_CONNECT-------------------------------------


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Google+ login
    """
    print "This is gconnect"
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(google_client_secret_path, scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError, ex:
        print "FlowExchangeError: %s" % repr(ex)
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

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
   
    # pip install flask==0.9, please read readme.txt file
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
          json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    print 'credentials=%s' % repr(credentials)
    login_session['credentials'] = credentials.to_json()
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "' + \
              'width: 300px; ' + \
              'height: 300px; ' + \
              'border-radius: 150px; ' + \
              '-webkit-border-radius: 150px; ' + \
              '-moz-border-radius: 150px;' + \
              '"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "Returning output: %s" % repr(output)
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """ Google+ logout
    """
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'
                                 ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    #print "disconnect: credentials=%s" % repr(credentials)
    credentials = json.loads(credentials)
    access_token = credentials["access_token"]
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(json.dumps(
          'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# -----------------------Facebook_Connect------------------------------------


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """Facebook login
    """
    if request.args.get('state') != login_session['state']:
        print "request.args.get('state')=" + str(request.args.get('state'))
        print "login_session['state']=" + str(login_session['state'])
        response = make_response(json.dumps('Invalid state parameter.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    fb_client_secrets = \
      json.loads(open(os.path.join(base_dir, 'fb_client_secrets.json'),
        'r').read())
    app_id = fb_client_secrets['web']['app_id']
    app_secret = fb_client_secrets['web']['app_secret']
    url = (
      'https://graph.facebook.com/oauth/access_token?grant_type=' +
      'fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s'
    ) % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    userinfo_url = "https://graph.facebook.com/v2.5/me"
    token = result.split("&")[0]
    url = 'https://graph.facebook.com/v2.5/me?%s&fields=name,id,email' % token
    h = httplib2.Http()

    result = h.request(url, 'GET')[1]

    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Profile picture
    url = (
      'https://graph.facebook.com/v2.5/me/picture?' +
      '%s&redirect=0&height=200&width=200'
    ) % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]
    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "' + \
              'width: 300px; ' + \
              'height: 300px; ' + \
              'border-radius: 150px; ' + \
              '-webkit-border-radius: 150px; ' + \
              '-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    """Facebook logout
    """
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = "https://graph.facebook.com/%s/permissions?access_token=%s" % (
      facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/disconnect')
def disconnect():
    """Facebook/Google+ logout
    """
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('allSavings'))
    else:
        flash("You were not been logged in to begin with!")
        return redirect(url_for('allSavings'))

# ------------------END_Facebook_Connect-------------------------------------


@app.route('/')
@app.route('/savings')
@app.route('/savings/')
def allSavings():
    """Shows Savings list
    """
    savings = session.query(Savings).all()
    total_sum = 0
    for saving in savings:
        total_sum += list_sums(saving.id)
    if 'username' not in login_session:
        return render_template('publicsavings.html',
                    savings_and_sums=[(s, list_sums(s.id)) for s in savings],
                    sum=total_sum)
    else:
        return render_template('savingslist.html',
                    savings_and_sums=[(s, list_sums(s.id)) for s in savings],
                    sum=total_sum)


@app.route('/savings/new/', methods=['GET', 'POST'])
@app.route('/savings/new', methods=['GET', 'POST'])
@login_required
def newSavings(): 
    """Shows a page for creating new saving
    """
    if request.method == 'POST':
        if 'name' in request.form:
            if request.form['name'] != '':
                newSaving = Savings(name=request.form['name'], 
                    user_id = login_session['user_id'])
                session.add(newSaving)
                session.commit()
                flash("New saving was created!")
        return redirect(url_for('allSavings'))
    else:
        return render_template('newsaving.html')


@app.route('/savings/<int:savings_id>/edit/', methods=['GET', 'POST'])
@app.route('/savings/<int:savings_id>/edit', methods=['GET', 'POST'])
@login_required
def editSavings(savings_id):
    """Shows a page for editing a saving
    """
    editedSaving = session.query(Savings).filter_by(id=savings_id).one()
    if editedSaving.user_id != login_session['user_id']:
        return """
          <body onload='alert("You are not authorized to edit this saving!"); 
          location.href="/";'>
        """
    if request.method == 'POST':
        if 'name' in request.form:
            if request.form['name'] != '':
                editedSaving.name = request.form['name']
                session.add(editedSaving)
                session.commit()
                flash("Saving has been updated!")
        return redirect(url_for('allSavings'))
    else:
        return render_template('editsaving.html', saving=editedSaving)


@app.route('/savings/<int:savings_id>/delete/', methods=['GET', 'POST'])
@app.route('/savings/<int:savings_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteSavings(savings_id):
    """Shows a page for deleting a saving
    """
    deletedSaving = session.query(Savings).filter_by(id=savings_id).one()
    listItems = session.query(Items).filter_by(savings_id=deletedSaving.id)
    if deletedSaving.user_id != login_session['user_id']:
        return """
          <body onload='alert("You are not authorized to delete this saving!"); 
          location.href="/";'>
        """
    if request.method == 'POST':
        for item in listItems:
            os.remove(item.picture_path)
        session.delete(deletedSaving)
        session.commit()
        flash("Saving has been deleted!")
        return redirect(url_for('allSavings'))
    else:
        return render_template('deletesaving.html', saving=deletedSaving)
# ----------------------------------------------------------------------------


@app.route('/savings/<int:savings_id>/items', methods=['GET', 'POST'])
@app.route('/savings/<int:savings_id>/items/', methods=['GET', 'POST'])
def savingsList(savings_id):
    """Shows a list of all saving items
    """
    # take first saving out the database
    savings = session.query(Savings).filter_by(id=savings_id).one()
    # list all savings items
    items = session.query(Items).filter_by(savings_id=savings_id)
    creator = session.query(User).filter_by(id=savings.user_id).one()

    items_with_picture_urls = [
        (
            item,
            "images/uploads/" + os.path.basename(item.picture_path)
                if item.picture_path else None
        )
        for item in items
    ]
    if 'username' not in login_session:
        return render_template('publicmenu.html', savings=savings,
                  items_with_picture_urls=items_with_picture_urls)
    else:
        return render_template('menu.html', creator=creator, savings=savings,
                  items_with_picture_urls=items_with_picture_urls)


@app.route('/savings/<int:savings_id>/items/new', methods=['GET', 'POST'])
@app.route('/savings/<int:savings_id>/items/new', methods=['GET', 'POST'])
@login_required
def newSavingItem(savings_id):
    """Shows a page for creating a new saving item
    """
    saving = session.query(Savings).filter_by(id=savings_id).one()
    if saving.user_id != login_session['user_id']:
        return """
          <body onload='alert("You are not authorized to add a new item!"); 
          location.href="/";'>
        """
    if request.method == 'POST':
        if 'name' in request.form:
            if request.form['name'] != '':
                newName = request.form['name']
                if 'picture' in request.files:
                    if request.files['picture']:
                        picture_file = request.files['picture']
                        random_string = ''.join(random.SystemRandom().choice(
                          string.ascii_uppercase + string.digits
                        ) for _ in range(8))
                        # Prefix the uploaded file name with the current
                        # timestamp and a random string to reduce the
                        # probability of collisions.
                        upload_base_name = time.strftime(
                          '%Y-%m-%d_%H_%M_%S') + '_' + \
                          random_string + '_' + \
                          secure_filename(picture_file.filename)
                        upload_path = os.path.join(
                          image_storage_dir, upload_base_name)
                        newDescription = request.form['description']
                        if 'price' in request.form:
                            if request.form['price'] != '':
                                newPrice = request.form['price']
                            else:
                                newPrice = 0.0
                        picture_file.save(upload_path)
                        upload_path = rotate_image(upload_path)
                        newItem = Items(
                          name=newName,
                          description=newDescription,
                          price=newPrice,
                          savings_id=savings_id,
                          picture_path=upload_path
                        )                      
                        session.add(newItem)
                        session.commit()
                        flash("new saving item was created!")
        return redirect(url_for('savingsList', savings_id=savings_id))
    else:
        return render_template('newsavingsitem.html', savings_id=savings_id)


@app.route('/savings/<int:savings_id>/items/<int:items_id>/edit',
  methods=['GET', 'POST'])
@app.route('/savings/<int:savings_id>/items/<int:items_id>/edit/',
  methods=['GET', 'POST'])
@login_required
def editSavingsItem(savings_id, items_id):
    """Shows a page for editing saving item
    """
    saving = session.query(Savings).filter_by(id=savings_id).one()
    if saving.user_id != login_session['user_id']:
        return """
          <body onload='alert("You are not authorized to edit items!"); 
          location.href="/";'>
        """
    editedItem = session.query(Items).filter_by(id=items_id).one()
    if request.method == 'POST':
        if 'name' in request.form:
            if request.form['name'] != '':
                editedItem.name = request.form['name']
        if 'description' in request.form:
            if request.form['description'] != '':
                editedItem.description = request.form['description']
        if 'price' in request.form:
            if request.form['price'] != '':
                editedItem.price = float(request.form['price'])
        if 'picture' in request.files:
            if request.files['picture']:
                oldPath=editedItem.picture_path
                picture_file = request.files['picture']
                random_string = ''.join(random.SystemRandom().choice(
                  string.ascii_uppercase + string.digits
                  ) for _ in range(8))
                # Prefix the uploaded file name with the current
                # timestamp and a random
                # string to reduce the probability of collisions.
                upload_base_name = \
                  time.strftime('%Y-%m-%d_%H_%M_%S') + '_' + \
                  random_string + '_' + secure_filename(picture_file.filename)
                upload_path = os.path.join(image_storage_dir,
                  upload_base_name)
                picture_file.save(upload_path)
                upload_path = rotate_image(upload_path)
                editedItem.picture_path = upload_path
                if os.path.exists(oldPath):
                    os.remove(oldPath)
        session.add(editedItem)
        session.commit()
        flash("Saving item has been updated!")
        return redirect(url_for('savingsList', savings_id=savings_id))
    else:
        return render_template('editedsavingsitem.html', savings_id=savings_id,
          items_id=items_id, item=editedItem)


@app.route('/savings/<int:savings_id>/items/<int:items_id>/delete',
  methods=['GET', 'POST'])
@app.route('/savings/<int:savings_id>/items/<int:items_id>/delete/',
 methods=['GET', 'POST'])
@login_required
def deleteSavingsItem(savings_id, items_id):
    """Shows a page for deleting items
    """
    saving = session.query(Savings).filter_by(id=savings_id).one()
    if saving.user_id != login_session['user_id']:
        return """
          <body onload='alert("You are not authorized to delete items!"); 
          location.href="/";'>
        """
    deletedItem = session.query(Items).filter_by(id=items_id).one()
    if request.method == 'POST':
        if os.path.exists(deletedItem.picture_path):
            os.remove(deletedItem.picture_path)
        session.delete(deletedItem)
        session.commit()
        flash("Saving item has been deleted!")
        return redirect(url_for('savingsList', savings_id=savings_id))
    else:
        return render_template('menu.html', item=deletedItem)

if __name__ == '__main__':
    app.debug = True  # reload if see any code changes
    app.run(host='0.0.0.0', port=8080)
