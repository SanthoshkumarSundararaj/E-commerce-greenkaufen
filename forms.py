from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo

class SignupForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UpdateProfileForm(FlaskForm):
    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password')
    birthdate = StringField('Birthdate')
    newsletter = BooleanField('Newsletter')
    submit = SubmitField('Update Profile')

class UpdateAddressForm(FlaskForm):
    billing_name = StringField('Billing Name')
    street = StringField('Street')
    postal = StringField('Postal Code')
    city = StringField('City')
    submit = SubmitField('Update Address')

class BulkEnquiryForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile = StringField('Mobile', validators=[DataRequired()])
    company = StringField('Company')
    product = StringField('Product', validators=[DataRequired()])
    quantity = StringField('Quantity', validators=[DataRequired()])
    message = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Submit Enquiry')
