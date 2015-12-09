from flask import Flask, render_template, request, redirect, url_for, flash, jsonify  
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Savings, Items, Goals
import os, errno

from werkzeug import secure_filename
import time
import random
import string

engine = create_engine('sqlite:///savemoney.db')
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
  return render_template('savingslist.html',
    savings_and_sums = [(s, list_sums(s.id)) for s in savings],
    sum = total_sum)

def list_sums(savings_id):
  savings = session.query(Savings).filter_by(id = savings_id).one()
  items = session.query(Items).filter_by(savings_id = savings_id)
  sum = 0
  for item in items:
    sum += item.price
  return sum

@app.route('/goals/', methods=['GET', 'POST']) 
def rishGoal(): 
  return "Buy" 

@app.route('/savings/new/', methods=['GET', 'POST'])
@app.route('/savings/new', methods=['GET', 'POST'])
def newSavings():
  if request.method == 'POST':
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
  if request.method == 'POST':
    session.delete(deletedSaving)
    session.commit()
    flash("Saving has been deleted!")
    return redirect(url_for('allSavings'))
  else:
    return render_template('deletesaving.html', saving = deletedSaving)


@app.route('/savings/<int:savings_id>/')
@app.route('/savings/<int:savings_id>/items')
def savingsList(savings_id):
  # take first saving out the database
  savings = session.query(Savings).filter_by(id = savings_id).one()
  #list all savings items
  items = session.query(Items).filter_by(savings_id = savings_id)
  return render_template('menu.html', savings = savings, 
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
    picture_file = request.files['picture']
    random_string = ''.join(
      random.SystemRandom().choice(
        string.ascii_uppercase + string.digits
      ) for _ in range(8)
    )
    # Prefix the uploaded file name with the current timestamp and a random
    # string to reduce the probability of collisions.
    upload_base_name = \
      time.strftime('%Y-%m-%d_%H_%M_%S') + '_' + random_string + '_' + \
      secure_filename(picture_file.filename)
    upload_path = os.path.join(image_storage_dir, upload_base_name)

    newItem = Items(
      name        = request.form['name'],
      description = request.form['description'],
      price       = request.form['price'],
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

@app.route('/savings/<int:savings_id>/items/<int:items_id>/delete', methods = ['GET', 'POST'])
@app.route('/savings/<int:savings_id>/items/<int:items_id>/delete/', methods = ['GET', 'POST'])
def deleteSavingsItem(savings_id, items_id):
  deletedItem = session.query(Items).filter_by(id = items_id).one()
  if request.method == 'POST':
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