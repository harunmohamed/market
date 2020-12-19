import os
from datetime import datetime
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from diary import app, db, bcrypt, mail
from diary.forms import RegistrationForm, LoginForm, PostForm, HomeForm, CommentForm
from diary.models import User, Post, Product, Message as m, Comment
from diary.functions import profile_img, market_img, post_img
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
			post = Post(title=form.title.data, content=form.content.data, anonymous=form.anonymous.data, image=picture, author=current_user)
		else:
			post = Post(title=form.title.data, content=form.content.data, anonymous=form.anonymous.data, author=current_user)
		db.session.add(post)
		db.session.commit()
		flash('Your Post Has been Created!', 'info')
		return redirect(url_for('home'))
	hour = datetime.now().hour
	greeting = "Good morning" if 5<=hour<12 else "Good afternoon" if hour<18 else "Good evening"
	posts = Post.query.filter_by(author=current_user).order_by(Post.date_posted.desc())
	return render_template('home.html', posts=posts, title=current_user.username.title() + "'s Diary", form=form, greeting=greeting)



@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(username=form.username.data.lower(), email=form.email.data, password=hashed_password)
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
		if form.image.data:
			picture = post_img(form.image.data)
			post = Post(title=form.title.data, content=form.content.data,anonymous=form.anonymous.data, image=picture, author=current_user)
			db.session.add(post)
			db.session.commit()
			flash('Your Post Has been Created!', 'info')
			return redirect(url_for('home'))
		else:
			post = Post(title=form.title.data, content=form.content.data,anonymous=form.anonymous.data, author=current_user)
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
		if form.image.data:
			post.image = post_img(form.image.data)
		db.session.commit()
		flash('Your post has been updated!', 'info')
		return redirect(url_for('post', post_id=post.id))
	elif request.method == 'GET':
		form.title.data = post.title
		form.content.data = post.content
		form.image.data = post.image
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
