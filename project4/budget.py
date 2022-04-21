# Copyright 2015, Kevin Burke, Kyle Conroy, Ryan Horn, Frank Stratton, Guillaume Binet
# Created as documentation for Flask-RESTful Flask extension
import time
import os
from flask import jsonify, json
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, _app_ctx_stack
from flask_restful import reqparse, abort, Api, Resource
from werkzeug.security import check_password_hash, generate_password_hash

from models import db, User, Category, Purchase


app = Flask(__name__)
api = Api(app)

# configuration
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'budget.db')

app.config.from_object(__name__)
app.config.from_envvar('EVENT_SETTINGS', silent=True)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #here to silence deprecation warning

db.init_app(app)


@app.cli.command('initdb')
def initdb_command():
	"""Creates the database tables."""
	db.drop_all()
	db.create_all()
	print('Initialized the database.')


def abort_if_cat_doesnt_exist(cat_id):
	if cat_id not in category:
		abort(404, message="category {} doesn't exist".format(cat_id))

def convert_datetime(date_time):
	try:
		datetime_str = datetime.strptime(date_time, '%d/%m/%Y')
		return datetime_str
	except ValueError:
		return None

class CatList(Resource):
	def get(self):
		category = []
		for c in Category.query.filter_by(user_id=g.user.user_id).order_by(Category.title.asc()).all():
			category.append({"id": c.cat_id, "title": c.title, "budget": c.budget, "spend": 0})
		#temp = [["adf", "bfsd"], ["a", "b"]]
		#return json.dumps(temp)
		return jsonify(category)

	def post(self):
		if 'user_id' not in session:
			abort(401)
		title = request.form['title']
		budget = request.form['budget']
		db.session.add(Category(g.user.user_id, title, budget))
		db.session.commit()

		category = []
		for c in Category.query.filter_by(user_id=g.user.user_id).order_by(Category.title.asc()).all():
			category.append({"id": c.cat_id, "title": c.title, "budget": c.budget, "spend": 0})
		return '', 201

class Cat(Resource):
	def delete(self, categoryId):
		print("deleteing cat_id = " + categoryId)
		Purchase.query.filter_by(cat_id=categoryId).update({'cat_id': -1});
		db.session.commit()
		Category.query.filter_by(cat_id=categoryId).delete()
		db.session.commit()

		purchases = []
		for p in Purchase.query.filter_by(user_id=g.user.user_id).all():
			purchases.append({"cat_id": p.cat_id, "description": p.description, "amount": p.amount})
		return '', 204

class Purch(Resource):
	def get(self):
		
		purchases = []
		for p in Purchase.query.filter_by(user_id=g.user.user_id).all():
			purchases.append({"cat_id": p.cat_id, "description": p.description, "amount": p.amount, "year": p.date.year, "month": p.date.month})
		temp = [["cdf", "s"], ["a", "b"]]
		return jsonify(purchases)

	def post(self):
		if 'user_id' not in session:
			abort(401)		
		category = request.form['cat']
		amount = request.form['amount']
		des = request.form['des']
		date = request.form['date']
		cat = Category.query.filter_by(title=category, user_id=g.user.user_id).first()
		if cat is None:
			cat_id = -1
		else:
			cat_id = cat.cat_id
		
		db.session.add(Purchase(g.user.user_id, cat_id, amount, des, convert_datetime(date)))
		db.session.commit()

		purchases = []
		for p in Purchase.query.filter_by(user_id=g.user.user_id).all():
			purchases.append({"cat_id": p.cat_id, "description": p.description, "amount": p.amount})
		temp = [["cdf", "s"], ["a", "b"]]
		return '', 201
##
## Actually setup the Api resource routing here
##
api.add_resource(CatList, '/cats')
api.add_resource(Cat, '/cats/<categoryId>')
api.add_resource(Purch, '/purchases')

@app.before_request
def before_request():
	g.user = None
	if 'user_id' in session:
		g.user = User.query.filter_by(user_id=session['user_id']).first()

def get_user_id(username):
	"""Convenience method to look up the id for a username."""
	rv = User.query.filter_by(username=username).first()
	return rv.user_id if rv else None


@app.route('/')
def mainpage():
	if not g.user:
		return redirect(url_for('login'))

	return render_template('mainpage.html', month=11)


@app.route('/login/', methods=['GET', 'POST'])
def login():
	"""Logs the user in."""
	if g.user:
		return redirect(url_for('mainpage'))
	error = None
	if request.method == 'POST':

		user = User.query.filter_by(username=request.form['username']).first()
		if user is None:
			error = 'Invalid username'
		elif not check_password_hash(user.pw_hash, request.form['password']):
			error = 'Invalid password'
		else:
			session['user_id'] = user.user_id
			return redirect(url_for('mainpage'))
	return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
	"""Registers the user."""
	if g.user:
		return redirect(url_for('mainpage'))
	error = None
	if request.method == 'POST':
		if not request.form['username']:
			error = 'You have to enter a username'
		elif not request.form['password']:
			error = 'You have to enter a password'
		elif request.form['password'] != request.form['password2']:
			error = 'The two passwords do not match'
		elif get_user_id(request.form['username']) is not None:
			error = 'The username is already taken'
		else:
			db.session.add(User(request.form['username'], generate_password_hash(request.form['password'])))
			db.session.commit()
			return redirect(url_for('login'))
	return render_template('register.html', error=error)

@app.route('/logout/')
def logout():
	"""Logs the user out."""
	flash('You were logged out')
	session.pop('user_id', None)
	return redirect(url_for('login'))


if __name__ == '__main__':
	app.run(debug=True)

