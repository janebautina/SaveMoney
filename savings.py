from flask import Flask, render_template, request, redirect, url_for, flash, jsonify  
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Savings, Items, User
import os, errno

from werkzeug import secure_filename
import time
from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import inspect

CLIENT_ID = json.loads(open('client_secret.json','r').read())['web']['client_id']
APPLICATION_NAME = "Savings"

engine = create_engine('sqlite:///savemoneywithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()

image_storage_dir = '/vagrant/MoneySaver/static/images/uploads'
if not os.path.exists(image_storage_dir):
  os.mkdir(image_storage_dir)

@app.route('/')
@app.route('/savings') 
@app.route('/savings/') 
def allSavings():
  savings  = session.query(Savings).all()
  total_sum = 0
  for saving in savings:
    total_sum += list_sums(saving.id)
  if 'username' not in login_session:
    return render_template('publicsavings.html', savings_and_sums = [(s, list_sums(s.id)) for s in savings], sum = total_sum)
  else:
    return render_template('savingslist.html', savings_and_sums = [(s, list_sums(s.id)) for s in savings], sum = total_sum)

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase+ string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

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
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    #credentials = AccessTokenCredentials(session['credentials'], 'user-agent-value')
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

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response


    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id
 
    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()
    #data = json.loads(answer.text)

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    #see if user exists, if it doesn't make a new one
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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

# FB Connect--------------------------------------------------------------------
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        print "request.args.get('state')=" + str(request.args.get('state'))
        print "login_session['state']=" + str(login_session['state'])
        response = make_response(json.dumps('Invalid state parameter.'),        )
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    app_id = json.loads(open('fb_client_secrets.json','r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json','r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
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

    #Profile picture
    url = 'https://graph.facebook.com/v2.5/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]
    #see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id= createUser(login_session)
    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = "https://graph.facebook.com/%s/permissions?access_token=%s" % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        print "Hello"
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            print "Hello"
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

#-------------------------------------------------------------------------------

def list_sums(savings_id):
  savings = session.query(Savings).filter_by(id = savings_id).one()
  items = session.query(Items).filter_by(savings_id = savings_id)
  sum = 0
  for item in items:
    sum += item.price
  return sum


@app.route('/savings/new/', methods=['GET', 'POST'])
@app.route('/savings/new', methods=['GET', 'POST'])
def newSavings():
  if request.method == 'POST':
    if 'name' in request.form:
      if request.form['name']!='':
        newSaving = Savings(name = request.form['name'])
        session.add(newSaving)
        session.commit()
        flash("New saving was created!")
    return redirect(url_for('allSavings'))
  else:
    return render_template('newsaving.html')
  
   
@app.route('/savings/<int:savings_id>/edit/', methods=['GET', 'POST'])
@app.route('/savings/<int:savings_id>/edit', methods=['GET', 'POST'])
def editSavings(savings_id):
  editedSaving = session.query(Savings).filter_by(id = savings_id).one()
  if request.method == 'POST':
    if 'name' in request.form:
      if request.form['name']!='':
        editedSaving.name = request.form['name']
    session.add(editedSaving)
    session.commit()
    flash("Saving has been updated!")
    return redirect(url_for('allSavings'))
  else:
    return render_template('editsaving.html', saving = editedSaving)

@app.route('/savings/<int:savings_id>/delete/', methods=['GET', 'POST'])
@app.route('/savings/<int:savings_id>/delete', methods=['GET', 'POST'])
def deleteSavings(savings_id):
  deletedSaving = session.query(Savings).filter_by(id = savings_id).one()
  listItems = session.query(Items).filter_by(savings_id = deletedSaving.id)
  if request.method == 'POST':
    for item in listItems:
      deletefile(deletedItem.picture_path)
    session.delete(deletedSaving)
    session.commit()
    flash("Saving has been deleted!")
    return redirect(url_for('allSavings'))
  else:
    return render_template('deletesaving.html', saving = deletedSaving)
#-------------------------------------------------------------------------------

@app.route('/savings/<int:savings_id>/')
@app.route('/savings/<int:savings_id>/items')
def savingsList(savings_id):
  # take first saving out the database
  savings = session.query(Savings).filter_by(id = savings_id).one()
  #list all savings items
  items = session.query(Items).filter_by(savings_id = savings_id)
  creator = session.query(User).filter_by(id = savings.user_id).one()
  if 'username' not in login_session:
    return render_template('publicmenu.html', savings = savings, 
        items_with_picture_urls = [
          (item, 
            "images/uploads/" + os.path.basename(item.picture_path)
              if item.picture_path else None
          )
          for item in items
        ])
  else:
      return render_template('menu.html', creator = creator, savings = savings, 
        items_with_picture_urls = [
          (item, 
            "images/uploads/" + os.path.basename(item.picture_path)
              if item.picture_path else None
          )
          for item in items
        ])

def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ['.jpg', '.png', '.gif']

@app.route('/savings/<int:savings_id>/items/new', methods=['GET', 'POST'])
@app.route('/savings/<int:savings_id>/items/new', methods=['GET', 'POST'])
def newSavingItem(savings_id):
  if request.method == 'POST':
      if 'name' in request.form:
        if request.form['name'] != '':
          newName = request.form['name']
          if 'picture' in request.files:
            if request.files['picture']:
              picture_file = request.files['picture']
              random_string = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))
              # Prefix the uploaded file name with the current timestamp and a random
              # string to reduce the probability of collisions.
              upload_base_name = time.strftime('%Y-%m-%d_%H_%M_%S') + '_' + random_string + '_' + secure_filename(picture_file.filename)
              upload_path = os.path.join(image_storage_dir, upload_base_name)
              newDescription = request.form['description']
              if 'price' in request.form:
                if request.form['price'] != '':
                  newPrice = request.form['price']
                else: 
                  newPrice = 0.0
              newItem = Items(
                name        = newName,
                description = newDescription,
                price       = newPrice,
                savings_id  = savings_id,
                picture_path = upload_path
              )
              picture_file.save(upload_path)
              session.add(newItem)
              session.commit()
              flash("new saving item was created!")
      return redirect(url_for('savingsList', savings_id = savings_id))
  else:
    return render_template('newsavingsitem.html', savings_id = savings_id)

@app.route('/savings/<int:savings_id>/items/<int:items_id>/edit', methods = ['GET', 'POST'])
@app.route('/savings/<int:savings_id>/items/<int:items_id>/edit/', methods = ['GET', 'POST'])
def editSavingsItem(savings_id, items_id):
  editedItem = session.query(Items).filter_by(id = items_id).one()
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
        picture_file = request.files['picture']
        random_string = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))
      # Prefix the uploaded file name with the current timestamp and a random
      # string to reduce the probability of collisions.
        upload_base_name = \
          time.strftime('%Y-%m-%d_%H_%M_%S') + '_' + random_string + '_' + \
          secure_filename(picture_file.filename)
        upload_path = os.path.join(image_storage_dir, upload_base_name)  
        editedItem.picture_path = upload_path
        picture_file.save(upload_path)
    session.add(editedItem)
    session.commit()
    flash("Saving item has been updated!")
    return redirect(url_for('savingsList', savings_id = savings_id))
  else:
    return render_template('editedsavingsitem.html', savings_id = savings_id, items_id = items_id, item = editedItem)

def deletefile(name):
  os.system('rm '+ name)

@app.route('/savings/<int:savings_id>/items/<int:items_id>/delete', methods = ['GET', 'POST'])
@app.route('/savings/<int:savings_id>/items/<int:items_id>/delete/', methods = ['GET', 'POST'])
def deleteSavingsItem(savings_id, items_id):
  deletedItem = session.query(Items).filter_by(id = items_id).one()
  if request.method == 'POST':
    deletefile(deletedItem.picture_path)
    session.delete(deletedItem)
    session.commit()
    flash("Saving item has been deleted!")
    return redirect(url_for('savingsList', savings_id = savings_id))
  else:
    return render_template('deletesavingsitem.html', item = deletedItem)

if __name__ =='__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True # reload if see any code changes
  app.run(host = '0.0.0.0', port = 8080)