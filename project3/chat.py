import time
import os
import json
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, _app_ctx_stack
from werkzeug.security import check_password_hash, generate_password_hash

from models import db, User, Chatroom, Message

# create our little application :)
app = Flask(__name__)

# configuration
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'chat.db')

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


def get_user_id(username):
	"""Convenience method to look up the id for a username."""
	rv = User.query.filter_by(username=username).first()
	return rv.user_id if rv else None
	
def convert_datetime(date_time):
	try:
		datetime_str = datetime.strptime(date_time, '%d/%m/%Y %H:%M')
		return datetime_str
	except ValueError:
		return None

def format_datetime(timestamp):
	"""Format a timestamp for display."""
	return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')


@app.before_request
def before_request():
	g.user = None
	g.chatroom = None

	if 'user_id' in session:
		g.user = User.query.filter_by(user_id=session['user_id']).first()
	if 'chatroom_id' in session:
		g.chatroom = Chatroom.query.filter_by(chatroom_id=session['chatroom_id']).first()

@app.route('/')
def mainpage():
	"""Shows a users mainpage or if no user is logged in it will
	redirect to the public mainpage.  This mainpage shows the user's
	messages as well as all the messages of followed users.
	"""
	if not g.user:
		return redirect(url_for('login'))

	return redirect(url_for('public_chatroom'))


@app.route('/public/')
def public_chatroom():
	"""Displays the latest messages of all users."""
	if not g.user:
		return redirect(url_for('login'))

	u = g.user
	chatrooms = Chatroom.query.order_by(Chatroom.title.asc()).limit(PER_PAGE).all()
	return render_template('mainpage.html', rooms=chatrooms)


@app.route('/<chatroom>')
def chatroom(chatroom):
	"""Display's a users tweets."""
	if not g.user:
		return redirect(url_for('login'))

	if (g.chatroom and g.chatroom.title != chatroom):
		flash('You already attended a room: "' + g.chatroom.title + '"')
		return redirect(url_for('mainpage'))

	chatroom = Chatroom.query.filter_by(title=chatroom).first()
	if chatroom is None:
		abort(404)
	session['chatroom_id'] = chatroom.chatroom_id

	messages = Message.query.filter_by(chatroom_id=chatroom.chatroom_id).order_by(Message.time.asc()).limit(PER_PAGE).all()

	return render_template('chatroom.html', messages=messages, title=chatroom.title)

@app.route('/leaveroom')
def leaveroom():
	if not g.chatroom:
		return redirect(url_for('mainpage'))
	flash('You left the room')
	session.pop('chatroom_id', None)

	return redirect(url_for('mainpage'))

@app.route('/getMessages')
def getMessages():
	if 'user_id' not in session:
		redirect(url_for('login'))
	if 'chatroom_id' not in session:
		redirect(url_for('mainpage'))
	chatroom = Chatroom.query.filter_by(chatroom_id=session['chatroom_id']).first()
	if chatroom is None:
		return json.dumps("500")
	messages = []
	for m in Message.query.filter_by(chatroom_id=session['chatroom_id']).order_by(Message.time.asc()).all():
		messages.append([m.sender.username, m.content, str(m.time.strftime("%Y-%m-%d, %H:%M"))])
	temp = [["adf", "bfsd"], ["cfd", "defd"]]
	return json.dumps(messages)

@app.route('/getChatroom')
def getChatroom():
	if chatroom not in session:
		abort(401)
	return json.dumps(g.chatroom.title)

@app.route('/new_message', methods=["POST"])
def add_message():
	if 'user_id' not in session:
		abort(401)

	if not g.chatroom:
		abort(401)
	chatroom = g.chatroom;
	time = datetime.now()
	db.session.add(Message(request.form['content'], chatroom.chatroom_id, g.user.user_id, time))
	db.session.commit();

	messages = []
	for m in Message.query.filter_by(chatroom_id=g.chatroom.chatroom_id).order_by(Message.time.asc()).all():
		messages.append([m.sender.username, m.content, str(m.time.strftime("%Y-%m-%d, %H:%M"))])
	temp = [["adf", "bfsd"], ["cfd", "defd"]]
	return json.dumps(messages)


@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
	"""Registers a new message for the user."""
	if 'user_id' not in session:
		abort(401)
	error = None
	if request.method == 'POST':
		if not request.form['title']:
			error = "you have to enter a title"
		elif Chatroom.query.filter_by(title=request.form['title']).first() is not None:
			error = "the name of the event already exists"
		else:
			db.session.add(Chatroom(request.form['title'], session['user_id']))
			db.session.commit()
			flash('Your chatroom is created')
			return redirect(url_for('mainpage'))
	return render_template('room_creation.html', error = error)

@app.route('/cancel_room', methods=['GET', 'POST'])
def cancel_room():
	if 'user_id' not in session:
		redirect(url_for('mainpage'))
	if request.method == 'POST':
		room = Chatroom.query.filter_by(title=request.form['title']).first()
		if room is None:
			return redirect(url_for('mainpage'))
		Event.query.filter_by(title=title).delete()
		db.session.commit()
		flash("You have deleted the event")
		return redirect('public_chatroom')

	user = g.user
	chatroom = Chatroom.query.filter_by(holder_id=user.user_id).all()
	return render_template('room_cancel.html', rooms=chatroom)


@app.route('/cancel_room/<title>')
def cancel(title):
	if 'user_id' not in session:
		redirect(url_for('mainpage'))

	room = Chatroom.query.filter_by(title=title).first()

	if room is None:
		error = "Room does not exists"
		return render_template('mainpage.html', error = error)
	Chatroom.query.filter_by(title=room.title).delete()
	Message.query.filter_by(chatroom_id=room.chatroom_id).delete()
	db.session.commit()
	flash("You have deleted the room")
	return redirect(url_for('public_chatroom'))


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
			flash('You were logged in')
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
			flash('You were successfully registered and can login now')
			return redirect(url_for('login'))
	return render_template('register.html', error=error)


@app.route('/logout/')
def logout():
	"""Logs the user out."""
	flash('You were logged out')
	session.pop('user_id', None)
	session.pop('chatroom_id', None)
	return redirect(url_for('login'))


# add some filters to jinja
app.jinja_env.filters['datetimeformat'] = format_datetime
