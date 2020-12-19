from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, RadioField, DateField
from flask_pagedown.fields import PageDownField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp
from diary.models import User

class RegistrationForm(FlaskForm):
	username = StringField('Username', validators = [DataRequired(), Length(min=2, max=20), Regexp(r'^[\w.-_.]+$', message='No Spaces. Use "-" or "_" or "." instead')]) 
	email = StringField('Email', validators = [DataRequired(), Email()])
	password = PasswordField('Password', validators = [DataRequired()])
	confirm_password = PasswordField('Confirm Password', validators = [DataRequired(), EqualTo('password')])
	submit = SubmitField('Sign Up')

	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user:
			raise ValidationError('That username is taken. Please choose a different one')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError('That email is taken. Please choose a different one')

	def validate_student_number(self, student_number):
		user = User.query.filter_by(student_number=student_number.data).first()
		if user:
			raise ValidationError('That Student Number is taken. Please choose a different one')


class LoginForm(FlaskForm):
	username = StringField('Username', validators = [DataRequired()]) #Email()
	password = PasswordField('Password', validators = [DataRequired()])
	remember = BooleanField('Remember Me')
	submit = SubmitField('Login')


class CommentForm(FlaskForm):
	body = StringField(('comment'), validators=[DataRequired(), Length(min=0, max=140)])
	submit = SubmitField('🛫 Post')

	
class PostForm(FlaskForm):
	title = StringField('Title') #validators=[DataRequired()]
	content = PageDownField('Content', validators=[DataRequired()])
	image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'jpeg' , 'png', 'gif'])])
	anonymous = BooleanField('Post Anonymously?')
	submit = SubmitField('🛫 Post')

#no markdown support for posts from home
class HomeForm(FlaskForm):
	title = StringField('Title') #validators=[DataRequired()]
	content = TextAreaField('Content', validators=[DataRequired()])
	image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'jpeg' , 'png', 'gif'])])
	anonymous = BooleanField('Post Anonymously?')
	submit = SubmitField('🛫 Post')
