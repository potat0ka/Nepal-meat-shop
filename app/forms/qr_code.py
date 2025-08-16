#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - QR Code Management Forms
Forms for managing payment QR codes.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class QRCodeForm(FlaskForm):
    """Form for uploading and managing QR codes."""
    
    payment_method = StringField(
        'Payment Method',
        validators=[DataRequired(), Length(min=2, max=50)],
        render_kw={'readonly': True}
    )
    
    description = TextAreaField(
        'Description',
        validators=[Length(max=500)],
        render_kw={'placeholder': 'Optional description for this QR code...'}
    )
    
    qr_image = FileField(
        'QR Code Image',
        validators=[
            FileRequired(),
            FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
        ]
    )
    
    submit = SubmitField('Upload QR Code')

class QRCodeUpdateForm(FlaskForm):
    """Form for updating existing QR codes."""
    
    payment_method = StringField(
        'Payment Method',
        validators=[DataRequired(), Length(min=2, max=50)],
        render_kw={'readonly': True}
    )
    
    description = TextAreaField(
        'Description',
        validators=[Length(max=500)],
        render_kw={'placeholder': 'Optional description for this QR code...'}
    )
    
    qr_image = FileField(
        'New QR Code Image (optional)',
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
        ]
    )
    
    submit = SubmitField('Update QR Code')

class PaymentMethodForm(FlaskForm):
    """Form for adding new payment methods."""
    
    method_id = StringField(
        'Payment Method ID',
        validators=[DataRequired(), Length(min=2, max=50)],
        render_kw={'placeholder': 'e.g., paytm, gpay, etc.'}
    )
    
    name = StringField(
        'Payment Method Name',
        validators=[DataRequired(), Length(min=2, max=100)],
        render_kw={'placeholder': 'e.g., PayTM, Google Pay, etc.'}
    )
    
    name_nepali = StringField(
        'Nepali Name',
        validators=[DataRequired(), Length(min=2, max=100)],
        render_kw={'placeholder': 'e.g., पेटीएम, गुगल पे, etc.'}
    )
    
    submit = SubmitField('Add Payment Method')