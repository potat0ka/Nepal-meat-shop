#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Order & Cart Forms
Shopping cart, checkout, and order management forms.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SelectField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class CartForm(FlaskForm):
    """
    Simple cart form for adding products to cart.
    CSRF protection disabled for AJAX compatibility.
    """
    product_id = HiddenField('Product ID')
    quantity = FloatField('Quantity (kg)', validators=[NumberRange(min=0.1)], default=2.0)

    # Remove CSRF protection for this form to avoid validation issues
    class Meta:
        csrf = False

class UpdateCartForm(FlaskForm):
    """
    Update cart item quantity form.
    CSRF protection disabled for AJAX compatibility.
    """
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    quantity = FloatField('Quantity (kg)', validators=[DataRequired(), NumberRange(min=0.1)])
    submit = SubmitField('Update')
    
    # Remove CSRF protection for this form to avoid validation issues
    class Meta:
        csrf = False

class RemoveCartForm(FlaskForm):
    """
    Remove item from cart form.
    CSRF protection disabled for AJAX compatibility.
    """
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    submit = SubmitField('Remove')
    
    # Remove CSRF protection for this form to avoid validation issues
    class Meta:
        csrf = False

class CheckoutForm(FlaskForm):
    """
    Comprehensive checkout form with delivery and payment options.
    Supports map-based address selection and multiple payment methods.
    """
    delivery_address = TextAreaField('Delivery Address', validators=[DataRequired()])
    delivery_latitude = HiddenField('Latitude', validators=[Optional()])
    delivery_longitude = HiddenField('Longitude', validators=[Optional()])
    delivery_formatted_address = HiddenField('Formatted Address', validators=[Optional()])
    delivery_phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    payment_method = SelectField('Payment Method',
                                choices=[
                                    ('cod', 'Cash on Delivery / घरमा पैसा तिर्ने'),
                                    ('esewa', 'eSewa Digital Wallet / ईसेवा'),
                                    ('khalti', 'Khalti Digital Wallet / खल्ती'),
                                    ('ime_pay', 'IME Pay / आईएमई पे'),
                                    ('fonepay', 'FonePay / फोनपे'),
                                    ('prabhupay', 'PrabhuPay / प्रभुपे'),
                                    ('cellpay', 'CellPay / सेलपे'),
                                    ('smartchoice', 'SmartChoice Payment / स्मार्टच्वाइस'),
                                    ('connectips', 'ConnectIPS / कनेक्टआईपीएस'),
                                    ('mobile_banking', 'Mobile Banking / मोबाइल बैंकिङ'),
                                    ('internet_banking', 'Internet Banking / इन्टरनेट बैंकिङ'),
                                    ('bank_transfer', 'Bank Transfer / बैंक ट्रान्सफर'),
                                    ('nabil_bank', 'Nabil Bank / नबिल बैंक'),
                                    ('nic_asia', 'NIC Asia Bank / एनआईसी एशिया बैंक'),
                                    ('global_ime', 'Global IME Bank / ग्लोबल आईएमई बैंक'),
                                    ('himalayan_bank', 'Himalayan Bank / हिमालयन बैंक'),
                                    ('standard_chartered', 'Standard Chartered / स्ट्यान्डर्ड चार्टर्ड'),
                                    ('everest_bank', 'Everest Bank / एभरेष्ट बैंक'),
                                    ('nepal_bank', 'Nepal Bank Limited / नेपाल बैंक लिमिटेड'),
                                    ('rastriya_banijya', 'Rastriya Banijya Bank / राष्ट्रिय बाणिज्य बैंक')
                                ],
                                validators=[DataRequired()])
    special_instructions = TextAreaField('Special Instructions', validators=[Optional()])
    submit = SubmitField('Place Order')

class OrderStatusForm(FlaskForm):
    """
    Order status update form for admin users.
    Manages order lifecycle from pending to delivered.
    """
    status = SelectField('Status',
                        choices=[
                            ('pending', 'Pending'),
                            ('confirmed', 'Confirmed'),
                            ('processing', 'Processing'),
                            ('out_for_delivery', 'Out for Delivery'),
                            ('delivered', 'Delivered'),
                            ('cancelled', 'Cancelled')
                        ],
                        validators=[DataRequired()])
    submit = SubmitField('Update Status')

class OrderFilterForm(FlaskForm):
    """
    Order filtering form for admin dashboard.
    Helps filter orders by status and other criteria.
    """
    status = SelectField('Status', choices=[('all', 'All Orders')] + [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], default='all')
    submit = SubmitField('Filter')