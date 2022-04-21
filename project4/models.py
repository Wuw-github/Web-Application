from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
	user_id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(24), nullable=False, unique=True)
	pw_hash = db.Column(db.String(64), nullable=False)
	category = db.relationship('Category', backref='holder')
	pur = db.relationship('Purchase', backref='purchased_by')
		
	def __init__(self, username, pw_hash):
		self.username = username
		self.pw_hash = pw_hash


class Category(db.Model):
	cat_id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
	title = db.Column(db.Text, nullable=False)
	budget = db.Column(db.Integer, nullable=False)

	def __init__(self, user_id, title, budget):
		self.user_id = user_id
		self.title = title
		self.budget = budget

class Purchase(db.Model):
	pur_id = db.Column(db.Integer, primary_key=True)
	cat_id = db.Column(db.Integer, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
	amount = db.Column(db.Integer, nullable=False)
	description = db.Column(db.Text, nullable=False)
	date = db.Column(db.DateTime, nullable=False)

	def __init__(self, user_id, cat_id, amount, description, date):
		self.user_id = user_id
		self.cat_id = cat_id
		self.amount = amount
		self.description = description
		self.date = date
