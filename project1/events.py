import time
import os
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, _app_ctx_stack
from werkzeug.security import check_password_hash, generate_password_hash

from models import db, User, Event

# create our little application :)
app = Flask(__name__)

# configuration
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'events.db')

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


def get_user(username):
	"""Convenience method to look up the id for a username."""
	rv = User.query.filter_by(username=username).first()
	return rv if rv else None

def get_user_id(username):
	"""Convenience method to look up the id for a username."""
	rv = User.query.filter_by(username=username).first()
	return rv.user_id if rv else None


def format_datetime(timestamp):
	"""Format a timestamp for display."""
	return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')

def convert_datetime(date_time):
	try:
		datetime_str = datetime.strptime(date_time, '%d/%m/%Y %H:%M')
		return datetime_str
	except ValueError:
		return None


def gravatar_url(email, size=80):
	"""Return the gravatar image for the given email address."""
	return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
		(md5(email.strip().lower().encode('utf-8')).hexdigest(), size)


@app.before_request
def before_request():
	g.user = None
	if 'user_id' in session:
		g.user = User.query.filter_by(user_id=session['user_id']).first()

@app.route('/')
def mainpage():
	"""Shows a users mainpage or if no user is logged in it will
	redirect to the public mainpage.  This mainpage shows the user's
	messages as well as all the messages of followed users.
	"""
	if not g.user:
		return redirect(url_for('public_events'))

	u = g.user
	display_ids = []
	for f in u.attend:
		display_ids.append(f.event_id)

	my_events = Event.query.filter(Event.event_id.in_(display_ids)).order_by(Event.start_date.asc()).limit(PER_PAGE).all()
	
	events_hold = Event.query.filter_by(holder_id=u.user_id).all()

	events_id_hold = []
	for f in events_hold:
		events_id_hold.append(f.event_id)

	public_events = Event.query.order_by(Event.start_date.asc()).limit(PER_PAGE).all()
	return render_template('mainpage.html', events=public_events, events_hold=events_hold, my_events=my_events, events_id_hold=events_id_hold)


@app.route('/public/')
def public_events():
	"""Displays the latest messages of all users."""
	public_events = Event.query.order_by(Event.start_date.asc()).limit(PER_PAGE).all()
	return render_template('mainpage.html', events=public_events)


@app.route('/<username>')
def user_events(username):
	"""Display's a users tweets."""
	user = get_user(username)
	cur_user = g.user
	if user is None:
		abort(404)

	events = Event.query.filter_by(holder_id=user.user_id).order_by(Event.start_date.asc()).limit(PER_PAGE).all()

	events_hold = []
	if cur_user is not None and user.user_id == cur_user.user_id:
		for f in Event.query.filter_by(holder_id=user.user_id).all():
			events_hold.append(f.event_id)

	return render_template('mainpage.html', events=events, profile_user=user, events_hold=events_hold)


@app.route('/<username>/<title>/register')
def register_event(username, title):
	"""Adds the current user as follower of the given user."""
	if not g.user:
		abort(401)
	user = User.query.filter_by(username=username).first()
	participant = User.query.filter_by(user_id=session['user_id']).first()
	event = Event.query.filter_by(title=title).first()
	if user is None:
		abort(404)

	#check if the user is the holder
	if participant.user_id == event.holder_id:
		flash('You are the holder, you cannot register')
		return redirect(url_for('public_events'))
	#check if the user has already join the event
	already = User.query.filter_by(user_id=participant.user_id).first().attend.filter_by(event_id=event.event_id).first() is not None
	if already:
		flash("You can only register this event once")
		return redirect(url_for('mainpage'))
	User.query.filter_by(user_id=session['user_id']).first().attend.append(event)
	db.session.commit()

	flash('You have registered the event')
	return redirect(url_for('mainpage'))


@app.route('/<username>/<title>/unregister')
def unregister_event(username, title):
	"""Removes the current user as follower of the given user."""
	if not g.user:
		abort(401)
	user = User.query.filter_by(username=username).first()
	participant = User.query.filter_by(user_id=session['user_id']).first()
	event = Event.query.filter_by(title=title).first()
	if user is None:
		abort(404)

	#check if the user is the holder
	if participant.user_id == event.holder_id:
		flash('You are the holder, you cannot unregister')
		return redirect(url_for('public_events'))

	#check if the user has already join the event
	already = User.query.filter_by(user_id=participant.user_id).first().attend.filter_by(event_id=event.event_id).first() is not None
	if not already:
		flash("You cannot unregister without having registered")
		return redirect(url_for('public_events'))
	
	User.query.filter_by(user_id=session['user_id']).first().attend.remove(event)
	db.session.commit()

	flash('You have unregistered the event')
	return redirect(url_for('mainpage'))


@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
	"""Registers a new message for the user."""
	if 'user_id' not in session:
		abort(401)
	error = None
	if request.method == 'POST':
		if not request.form['title']:
			error = "you have to enter a title"
		elif not request.form['start_date']:
			error = "you have to decide a start date"
		elif not request.form['end_date']:
			error = "you have to decide an end date"
		elif Event.query.filter_by(title=request.form['title']).first() is not None:
			error = "the name of the event already exists"
		elif convert_datetime(request.form['start_date']) is None:
			error = "Please follow the time format"
		elif convert_datetime(request.form['end_date']) is None:
			error = "Please follow the time format"
		else:
			db.session.add(Event(request.form['title'], session['user_id'], request.form['description'], convert_datetime(request.form['start_date']), convert_datetime(request.form['end_date'])))
			db.session.commit()
			flash('Your event is created')
			return redirect(url_for('mainpage'))
	return render_template('event_creation.html', error = error)

@app.route('/cancel_event')
def cancel():
	if 'user_id' not in session:
		abort(401)
	user = g.user
	events = Event.query.filter_by(holder_id=user.user_id).all()
	return render_template('event_cancel.html', events=events)

@app.route('/cancel_event/<title>')
def cancel_event(title):
	if 'user_id' not in session:
		abort(401)
	event = Event.query.filter_by(title=title).first()

	if event is None:
		return redirect(url_for('mainpage'))
	Event.query.filter_by(title=title).delete()
	db.session.commit()
	flash("You have deleted the event")
	return redirect('mainpage')


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
	return redirect(url_for('public_events'))


# add some filters to jinja
app.jinja_env.filters['datetimeformat'] = format_datetime
app.jinja_env.filters['gravatar'] = gravatar_url
