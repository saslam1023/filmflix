# Classes
# Define login form
from wtforms import StringField, SubmitField
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Login')

# Define registration form
class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Register')

# Define forgot password form
class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')

# Define verification form 
class VerifyCodeForm(FlaskForm):
    verification_code = StringField('Verification Code', validators=[DataRequired()])
    submit = SubmitField('Submit')

# Define verification form 
class ResetForm(FlaskForm):
    token = StringField('Token', validators=[DataRequired()])
    new_password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Submit')
