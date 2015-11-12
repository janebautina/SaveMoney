from flask import Flask, render_template, request, redirect, url_for, flash, jsonify    
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Savings, Items

engine = create_engine('sqlite:///savemoney.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()

@app.route('/')
@app.route('/savings') 
@app.route('/savings/') 

def allSavings():
  savings  = session.query(Savings).all()
  return render_template('savingslist.html', savings = savings)


@app.route('/savings/new/', methods=['GET', 'POST'])
@app.route('/savings/new', methods=['GET', 'POST'])
def newSavings():
  return "New"
   

@app.route('/savings/<int:savings_id>/edit/', methods=['GET', 'POST'])
@app.route('/savings/<int:savings_id>/edit', methods=['GET', 'POST'])
def editSavings(savings_id):
  return "Hello Edit" 

@app.route('/savings/<int:savings_id>/delete/', methods=['GET', 'POST'])
@app.route('/savings/<int:savings_id>/delete', methods=['GET', 'POST'])
def deleteSavings(savings_id):
  return "Hello Delete"


@app.route('/savings/<int:savings_id>/')
@app.route('/savings/<int:savings_id>/items')
def savingsList(savings_id):
  # take first saving out the database
  savings = session.query(Savings).filter_by(id = savings_id).one()
  #list all savings items
  items = session.query(Items).filter_by(savings_id = savings_id)
  return render_template('menu.html', savings = savings, items = items)

@app.route('/savings/<int:savings_id>/items/new', methods=['GET', 'POST'])
@app.route('/savings/<int:savings_id>/items/new', methods=['GET', 'POST'])
def newSavingItem(savings_id):
  if request.method == 'POST':
    newItem =Items(
      name        = request.form['name'],
      description = request.form['description'],
      price       = request.form['price'],
      savings_id = savings_id)
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
      editedItem.name = request.form['name']
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