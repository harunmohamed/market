import os
from datetime import datetime
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from market import app, db, bcrypt, mail
from market.forms import RegistrationForm, LoginForm, PostForm, HomeForm, CommentForm, UpdateAccountForm, MessageForm
from market.models import User, Post, Message as m, Comment
from market.functions import profile_img, market_img, post_img
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message


@app.before_request
def before_request():
	if current_user.is_authenticated:
		current_user.last_seen = datetime.utcnow()
		db.session.commit()

@app.route('/layout')
def layout():
	users = User.query.all()
	return render_template('layout.html', users=users)



@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
	form = HomeForm()
	if form.validate_on_submit():
		if form.image.data:
			picture = post_img(form.image.data)
			post = Post(title=form.title.data, content=form.content.data, image=picture, author=current_user)
		else:
			post = Post(title=form.title.data, content=form.content.data, author=current_user)
		db.session.add(post)
		db.session.commit()
		flash('Your Post Has been Created!', 'info')
		return redirect(url_for('home'))
	hour = datetime.now().hour
	greeting = "Good morning" if 5<=hour<12 else "Good afternoon" if hour<18 else "Good evening"
	posts = Post.query.filter_by(author=current_user).order_by(Post.date_posted.desc())
	return render_template('home.html', posts=posts, title=current_user.username.title() + "'s Market", form=form, greeting=greeting)



@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(name=form.username.name, username=form.username.data.lower(), email=form.email.data, password=hashed_password)
		db.session.add(user)
		db.session.commit()
		flash(f'Account Created for {form.username.data}! You can now log in', 'info')
		return redirect(url_for('login'))
	return render_template('register.html', title="Register", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data.lower()).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('home'))
		else:
			flash(f'Login Unsuccesful! Please try again.', 'danger')
	return render_template('login.html', title="Login", form=form)


@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('login'))


@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
	form = PostForm()
	if form.validate_on_submit():
			picture = post_img(form.image.data)
			post = Post(title=form.title.data, content=form.content.data, sold=form.sold.data, image=picture,\
				tags=form.tags.data, price=form.price.data, author=current_user)
			db.session.add(post)
			db.session.commit()
			flash('Your Post Has been Created!', 'info')
			return redirect(url_for('home'))
	return render_template('create_post.html', title='New Post', form=form)

@app.route('/post/<int:post_id>', methods=["GET", "POST"])
@login_required
def post(post_id):
	post = Post.query.get_or_404(post_id)
	users = User.query.all()
	form = CommentForm()
	if form.validate_on_submit():
		comment = Comment(body=form.body.data, post=post, author=current_user)
		db.session.add(comment)
		db.session.commit()
		flash('Your comment has been published.')
		return redirect(url_for('post', post_id=post.id))
	return render_template('post.html',title=post.title, post=post, form=form, users=users)



@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
	post = Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.title = form.title.data
		post.content = form.content.data
		post.tags = form.tags.data
		post.price = form.price.data
		post.sold = form.sold.data
		post.image = post_img(form.image.data)
		db.session.commit()
		flash('Your post has been updated!', 'info')
		return redirect(url_for('post', post_id=post.id))
	elif request.method == 'GET':
		form.title.data = post.title
		form.content.data = post.content
		form.image.data = post.image
		form.tags.data = post.tags
		form.price.data = post.price
		form.sold.data = post.sold
	return render_template('create_post.html', title='Update Post',
						   form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
	post = Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)
	db.session.delete(post)
	db.session.commit()
	flash('Your post has been deleted!', 'info')
	return redirect(url_for('home'))

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
	form = UpdateAccountForm()
	if form.validate_on_submit():
		if form.picture.data:
			pic = profile_img(form.picture.data)
			current_user.dp = pic
		current_user.name = form.name.data
		current_user.username = form.username.data.lower()
		current_user.bio = form.bio.data
		current_user.email = form.email.data
		current_user.location = form.location.data
		current_user.contact = form.contact.data
		db.session.commit()
		flash('Your Account has been updated', 'success')
		return redirect(url_for('account'))
	elif request.method == 'GET':
		form.name.data = current_user.name
		form.username.data = current_user.username
		form.bio.data = current_user.bio
		form.email.data = current_user.email
		form.location.data = current_user.location
		form.contact.data = current_user.contact
	dp = url_for('static', filename='profile_pics/' + current_user.dp)
	return render_template('account.html', title='Account', dp=dp, form=form)

@app.route("/<string:username>", methods=['GET', 'POST'])
@login_required
def user_posts(username):
	username = username.lower()
	user = User.query.filter_by(username=username).first_or_404()
	users = User.query.all()
	posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc())
	return render_template('profile.html', user=user, users=users,posts=posts, title=user.name.title())

@app.route('/m/<recipient>', methods=['GET', 'POST'])
@login_required
def message(recipient):
	current_user.last_message_read_time = datetime.utcnow()
	db.session.commit()
	recipient = recipient.lower()
	user = User.query.filter_by(username=recipient).first_or_404()
	current_user.last_message_read_time = datetime.utcnow()
	db.session.commit()
	#if user == current_user:
		#return redirect(url_for('messages'))
	form = MessageForm()
	if form.validate_on_submit():
		msg = m(author=current_user, recipient=user, body=form.message.data)
		db.session.add(msg)
		db.session.commit()
		flash('Your message has been sent.', 'info')
		return redirect(url_for('message', recipient=recipient))
	sent = current_user.messages_sent.filter_by(recipient_id=user.id)
	received = current_user.messages_received.filter_by(sender_id=user.id)
	messages = sent.union(received).order_by(m.timestamp.asc())

	#adding all names of people who texted me to recent chats
	messages_received = current_user.messages_received.order_by(m.timestamp.desc())
	messages_sent = current_user.messages_sent.order_by(m.timestamp.desc())
	recent_chats = list()
	for message in messages_received:
		recent_chats.append(message.author)
	for message in messages_sent:
		recent_chats.append(message.recipient)
	recent_chats = list(dict.fromkeys(recent_chats))

	return render_template('send_message.html', recipient=recipient, title="Chat with " + recipient.title() , user=user, form=form, messages=messages, recent_chats=recent_chats)


@app.route('/messages')
@login_required
def messages():
	current_user.last_message_read_time = datetime.utcnow()
	db.session.commit()
	messages_received = current_user.messages_received.order_by(m.timestamp.desc())
	messages_sent = current_user.messages_sent.order_by(m.timestamp.desc())

	#recent chats
	recent_chats = list()
	for message in messages_received:
		recent_chats.append(message.author)
	for message in messages_sent:
		recent_chats.append(message.recipient)
	recent_chats = list(dict.fromkeys(recent_chats))

	users = User.query.all()
	hour = datetime.now().hour
	greeting = "Good morning" if 5<=hour<12 else "Good afternoon" if hour<18 else "Good evening"
	return render_template('messages.html', users=users, greeting=greeting, recent_chats=recent_chats, messages_sent=messages_sent, messages_received=messages_received)

@app.route('/account/delete')
@login_required
def delete_account():
	db.session.delete(current_user)
	db.session.commit()
	flash('Your account has been successfully deleted.', 'success')
	return redirect(url_for('home'))

@app.route('/admin/delete/<string:username>')
@login_required
def admin_delete_account(username):
	username = username.lower()
	user = User.query.filter_by(username=username).first()
	if current_user.username == 'harun':
		db.session.delete(user)
		db.session.commit()
		flash('Account Successfully deleted by Admin.', 'info')
	return redirect(url_for('home', user=user))


#Error Handlers
@app.errorhandler(404)
def not_found_error(error):
	return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden_route_error(error):
	return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(error):
	db.session.rollback()
	return render_template('500.html'), 500
