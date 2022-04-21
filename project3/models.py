from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
	user_id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(24), nullable=False, unique=True)
	pw_hash = db.Column(db.String(64), nullable=False)
	chatroom = db.relationship('Chatroom', backref='holder')
	message = db.relationship('Message', backref='sender')
		
	def __init__(self, username, pw_hash):
		self.username = username
		self.pw_hash = pw_hash

	def __repr__(self):
		return '<User {}>'.format(self.username)

class Chatroom(db.Model):
	chatroom_id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.Text, nullable=False)
	holder_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
	message = db.relationship('Message', backref='room')

	def __init__(self, title, holder_id):
		self.holder_id = holder_id
		self.title = title


	def __repr__(self):
		return '<Message {}>'.format(self.chatroom_id)

class Message(db.Model):
	message_id = db.Column(db.Integer, primary_key=True)
	content = db.Column(db.Text, nullable=False)
	chatroom_id = db.Column(db.Integer, db.ForeignKey('chatroom.chatroom_id'), nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
	time = db.Column(db.DateTime, nullable=False)

	def __init__(self, content, chatroom_id, user_id, time):
		self.content = content
		self.chatroom_id = chatroom_id
		self.user_id = user_id
		self.time = time
