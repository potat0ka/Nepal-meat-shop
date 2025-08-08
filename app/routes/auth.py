#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Authentication Routes
User login, registration, and profile management routes.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.forms import LoginForm, RegisterForm, ProfileForm, ChangePasswordForm
from app.utils import validate_phone_number, validate_email

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login page and processing.
    Redirects authenticated users to home page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        # Find user by email
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            # Successful login
            login_user(user, remember=form.remember_me.data)
            flash('लगइन सफल भयो / Login successful!', 'success')
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            # Failed login
            flash('गलत ईमेल वा पासवर्ड / Invalid email or password!', 'error')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration page and processing.
    Redirects authenticated users to home page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        # Check if user already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('यो ईमेल पहिले नै प्रयोग भइसकेको छ / Email already registered!', 'error')
            return render_template('auth/register.html', form=form)

        if User.query.filter_by(username=form.username.data).first():
            flash('यो प्रयोगकर्ता नाम उपलब्ध छैन / Username not available!', 'error')
            return render_template('auth/register.html', form=form)

        # Validate phone number
        if not validate_phone_number(form.phone.data):
            flash('गलत फोन नम्बर / Invalid phone number format!', 'error')
            return render_template('auth/register.html', form=form)

        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            address=form.address.data
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
            flash('दर्ता सफल भयो! अब लगइन गर्नुहोस् / Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('दर्ता गर्दा समस्या भयो / Registration failed. Please try again.', 'error')

    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """
    User logout and redirect to home page.
    """
    logout_user()
    flash('लगआउट भयो / Logged out successfully!', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    User profile view and edit page.
    """
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Check if email is being changed and already exists
        if form.email.data != current_user.email:
            if User.query.filter_by(email=form.email.data).first():
                flash('यो ईमेल पहिले नै प्रयोग भइसकेको छ / Email already in use!', 'error')
                return render_template('auth/profile.html', form=form)

        # Check if username is being changed and already exists
        if form.username.data != current_user.username:
            if User.query.filter_by(username=form.username.data).first():
                flash('यो प्रयोगकर्ता नाम उपलब्ध छैन / Username not available!', 'error')
                return render_template('auth/profile.html', form=form)

        # Validate phone number
        if not validate_phone_number(form.phone.data):
            flash('गलत फोन नम्बर / Invalid phone number format!', 'error')
            return render_template('auth/profile.html', form=form)

        # Update user information
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.full_name = form.full_name.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data

        try:
            db.session.commit()
            flash('प्रोफाइल अपडेट भयो / Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('प्रोफाइल अपडेट गर्दा समस्या भयो / Profile update failed.', 'error')

    return render_template('auth/profile.html', form=form)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    Change user password page.
    """
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('हालको पासवर्ड गलत छ / Current password is incorrect!', 'error')
            return render_template('auth/change_password.html', form=form)

        # Update password
        current_user.set_password(form.new_password.data)
        
        try:
            db.session.commit()
            flash('पासवर्ड परिवर्तन भयो / Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash('पासवर्ड परिवर्तन गर्दा समस्या भयो / Password change failed.', 'error')

    return render_template('auth/change_password.html', form=form)