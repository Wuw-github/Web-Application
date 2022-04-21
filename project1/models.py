from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
	user_id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(24), nullable=False, unique=True)
	pw_hash = db.Column(db.String(64), nullable=False)

	events = db.relationship('Event', backref='holder')
	
	attend = db.relationship('Event', secondary='attend', primaryjoin='User.user_id==attend.c.participant_id', secondaryjoin='Event.event_id==attend.c.event_id', backref=db.backref('attend_by', lazy='dynamic'), lazy='dynamic')
	
	def __init__(self, username, pw_hash):
		self.username = username
		self.pw_hash = pw_hash

	def __repr__(self):
		return '<User {}>'.format(self.username)

attend = db.Table('attend',
    db.Column('participant_id', db.Integer, db.ForeignKey('user.user_id')),
    db.Column('event_id', db.Integer, db.ForeignKey('event.event_id'))
)



class Event(db.Model):
	event_id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.Text, nullable=False)
	holder_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
	description = db.Column(db.Text, nullable=False)
	start_date = db.Column(db.DateTime, nullable=False)
	end_date = db.Column(db.DateTime, nullable=False)

	def __init__(self, title, holder_id, description, start_date, end_date):
		self.holder_id = holder_id
		self.title = title
		self.description = description
		self.start_date = start_date
		self.end_date = end_date

	def __repr__(self):
		return '<Message {}>'.format(self.event_id)
