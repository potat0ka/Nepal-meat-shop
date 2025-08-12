#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - MongoDB Authentication Routes
User login, registration, and profile management routes for MongoDB.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.utils.mongo_db import mongo_db
from app.models.mongo_models import MongoUser
from app.forms import LoginForm, RegisterForm, ProfileForm, ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm
from app.utils import validate_phone_number, validate_email
from app.utils.file_utils import save_uploaded_file, delete_file, validate_image_file
import secrets
import hashlib
from datetime import datetime, timedelta

# Create authentication blueprint
mongo_auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@mongo_auth_bp.route('/login', methods=['GET', 'POST'])
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
        user = mongo_db.find_user_by_email(form.email.data)
        
        if user and user.check_password(form.password.data):
            # Successful login
            login_user(user, remember=form.remember_me.data)
            flash('लगइन सफल भयो / Login successful!', 'success')
            
            # Update last login
            from datetime import datetime
            user.last_login = datetime.utcnow()
            mongo_db.save_user(user)
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            # Failed login
            flash('गलत ईमेल वा पासवर्ड / Invalid email or password!', 'error')

    return render_template('auth/login.html', form=form)

@mongo_auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration page and processing.
    Redirects authenticated users to home page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        # Check if email already exists
        if mongo_db.find_user_by_email(form.email.data):
            flash('यो ईमेल पहिले नै प्रयोग भइसकेको छ! यदि तपाईंसँग खाता छ भने लगइन गर्नुहोस् वा पासवर्ड भुल्नुभयो भने रिसेट गर्नुहोस् / Email already registered! If you have an account, please login or reset your password if forgotten.', 'error')
            return render_template('auth/register.html', form=form)

        # Check if username already exists
        if mongo_db.find_user_by_username(form.username.data):
            flash('यो प्रयोगकर्ता नाम उपलब्ध छैन / Username not available!', 'error')
            return render_template('auth/register.html', form=form)

        # Check if phone number already exists
        if mongo_db.find_user_by_phone(form.phone.data):
            flash('यो फोन नम्बर पहिले नै प्रयोग भइसकेको छ! यदि तपाईंसँग खाता छ भने लगइन गर्नुहोस् वा पासवर्ड भुल्नुभयो भने रिसेट गर्नुहोस् / Phone number already registered! If you have an account, please login or reset your password if forgotten.', 'error')
            return render_template('auth/register.html', form=form)

        # Validate phone number format
        if not validate_phone_number(form.phone.data):
            flash('गलत फोन नम्बर / Invalid phone number format!', 'error')
            return render_template('auth/register.html', form=form)

        # Create new user
        user = MongoUser()
        user.username = form.username.data
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.phone = form.phone.data
        user.address = form.address.data
        user.set_password(form.password.data)

        try:
            mongo_db.save_user(user)
            flash('दर्ता सफल भयो! अब लगइन गर्नुहोस् / Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash('दर्ता गर्दा समस्या भयो / Registration failed. Please try again.', 'error')

    return render_template('auth/register.html', form=form)

@mongo_auth_bp.route('/logout')
@login_required
def logout():
    """
    User logout and redirect to home page.
    """
    logout_user()
    flash('लगआउट भयो / Logged out successfully!', 'info')
    return redirect(url_for('main.index'))

@mongo_auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    User profile view and edit page.
    """
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Check if email is being changed and already exists
        if form.email.data != current_user.email:
            if mongo_db.find_user_by_email(form.email.data):
                flash('यो ईमेल पहिले नै प्रयोग भइसकेको छ / Email already in use!', 'error')
                return render_template('auth/profile.html', form=form)

        # Check if username is being changed and already exists
        if form.username.data != current_user.username:
            if mongo_db.find_user_by_username(form.username.data):
                flash('यो प्रयोगकर्ता नाम उपलब्ध छैन / Username not available!', 'error')
                return render_template('auth/profile.html', form=form)

        # Validate phone number
        if not validate_phone_number(form.phone.data):
            flash('गलत फोन नम्बर / Invalid phone number format!', 'error')
            return render_template('auth/profile.html', form=form)

        # Handle profile picture upload
        if form.profile_picture.data:
            if validate_image_file(form.profile_picture.data):
                # Delete old profile picture if exists
                if current_user.profile_image:
                    delete_file(current_user.profile_image)
                
                # Save new profile picture
                profile_image_path = save_uploaded_file(form.profile_picture.data, 'profiles')
                if profile_image_path:
                    current_user.profile_image = profile_image_path
                    flash('प्रोफाइल फोटो अपडेट भयो / Profile photo updated!', 'success')
                else:
                    flash('प्रोफाइल फोटो अपलोड गर्दा समस्या भयो / Profile photo upload failed!', 'error')
            else:
                flash('गलत फाइल प्रकार! केवल JPG, PNG, GIF फाइलहरू मात्र / Invalid file type! Only JPG, PNG, GIF files allowed!', 'error')
                return render_template('auth/profile.html', form=form)

        # Update user information
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.full_name = form.full_name.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data

        try:
            mongo_db.save_user(current_user)
            flash('प्रोफाइल अपडेट भयो / Profile updated successfully!', 'success')
        except Exception as e:
            flash('प्रोफाइल अपडेट गर्दा समस्या भयो / Profile update failed.', 'error')

    return render_template('auth/profile.html', form=form)

@mongo_auth_bp.route('/change-password', methods=['GET', 'POST'])
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
            mongo_db.save_user(current_user)
            flash('पासवर्ड परिवर्तन भयो / Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            flash('पासवर्ड परिवर्तन गर्दा समस्या भयो / Password change failed.', 'error')

    return render_template('auth/change_password.html', form=form)

@mongo_auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Forgot password page - sends reset link to user's email.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = mongo_db.find_user_by_email(form.email.data)
        
        if user:
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            reset_token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
            
            # Set token expiry (1 hour from now)
            token_expiry = datetime.utcnow() + timedelta(hours=1)
            
            # Save reset token to user
            user.reset_token = reset_token_hash
            user.reset_token_expiry = token_expiry
            
            try:
                mongo_db.save_user(user)
                
                # In a real application, you would send an email here
                # For now, we'll just show the reset link in the flash message
                reset_url = url_for('auth.reset_password', token=reset_token, _external=True)
                
                # For development - show the reset link
                flash(f'पासवर्ड रिसेट लिङ्क: {reset_url} / Password reset link: {reset_url}', 'info')
                flash('यदि तपाईंको ईमेल हाम्रो सिस्टममा छ भने, तपाईंले पासवर्ड रिसेट लिङ्क प्राप्त गर्नुहुनेछ / If your email is in our system, you will receive a password reset link.', 'success')
                
            except Exception as e:
                flash('पासवर्ड रिसेट अनुरोध पठाउन असफल / Failed to send password reset request.', 'error')
        else:
            # Don't reveal if email exists or not for security
            flash('यदि तपाईंको ईमेल हाम्रो सिस्टममा छ भने, तपाईंले पासवर्ड रिसेट लिङ्क प्राप्त गर्नुहुनेछ / If your email is in our system, you will receive a password reset link.', 'success')

    return render_template('auth/forgot_password.html', form=form)

@mongo_auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Reset password page with token validation.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # Hash the provided token to compare with stored hash
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Find user with matching reset token
    user = mongo_db.find_user_by_reset_token(token_hash)
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash('अवैध वा म्याद सकिएको रिसेट लिङ्क / Invalid or expired reset link!', 'error')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Update user password
        user.set_password(form.password.data)
        
        # Clear reset token
        user.reset_token = None
        user.reset_token_expiry = None
        
        try:
            mongo_db.save_user(user)
            flash('पासवर्ड सफलतापूर्वक रिसेट भयो! अब लगइन गर्नुहोस् / Password reset successfully! Please login now.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash('पासवर्ड रिसेट गर्दा समस्या भयो / Password reset failed.', 'error')

    return render_template('auth/reset_password.html', form=form)