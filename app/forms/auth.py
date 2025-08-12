#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Authentication Forms
User login, registration, and profile management forms.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo

class LoginForm(FlaskForm):
    """
    User login form with email and password validation.
    Used for customer and admin authentication.
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    """
    User registration form for new customer accounts.
    Includes validation for all required user information.
    """
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    address = TextAreaField('Address', validators=[Optional()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class ProfileForm(FlaskForm):
    """
    User profile update form.
    Allows users to modify their account information.
    """
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    address = TextAreaField('Address', validators=[Optional()])
    submit = SubmitField('Update Profile')

class ChangePasswordForm(FlaskForm):
    """
    Password change form for existing users.
    Requires current password verification.
    """
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                   validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class ForgotPasswordForm(FlaskForm):
    """
    Forgot password form for password reset requests.
    Sends reset link to user's email.
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    """
    Reset password form for users with valid reset tokens.
    Allows setting new password without current password.
    """
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')