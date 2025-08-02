from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, BooleanField, HiddenField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo
import uuid
from datetime import datetime

class LoginForm(FlaskForm):
    """User login form."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    """User registration form."""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    address = TextAreaField('Address', validators=[Optional()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class ProductForm(FlaskForm):
    """Product creation/edit form."""
    name = StringField('Product Name', validators=[DataRequired(), Length(max=120)])
    name_nepali = StringField('Product Name (Nepali)', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price per kg (रू)', validators=[DataRequired(), NumberRange(min=0.01)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    meat_type = SelectField('Meat Type', 
                           choices=[('pork', 'Pork / सुँगुर'), ('buffalo', 'Buffalo / भैंसी')],
                           validators=[DataRequired()])
    preparation_type = SelectField('Preparation Type',
                                 choices=[('fresh', 'Fresh / ताजा'), ('processed', 'Processed / प्रशोधित')],
                                 default='fresh')
    stock_kg = FloatField('Stock (kg)', validators=[DataRequired(), NumberRange(min=0)])
    min_order_kg = FloatField('Minimum Order (kg)', validators=[DataRequired(), NumberRange(min=0.1)], default=0.5)
    freshness_hours = IntegerField('Freshness (hours)', validators=[DataRequired(), NumberRange(min=1)], default=24)
    cooking_tips = TextAreaField('Cooking Tips', validators=[Optional()])
    is_featured = BooleanField('Featured Product')
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save Product')

class CartForm(FlaskForm):
    """Simple cart form without CSRF."""
    product_id = HiddenField('Product ID')
    quantity = FloatField('Quantity (kg)', validators=[NumberRange(min=0.1)], default=2.0)

    # Remove CSRF protection for this form to avoid validation issues
    class Meta:
        csrf = False

class UpdateCartForm(FlaskForm):
    """Update cart item form."""
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    quantity = FloatField('Quantity (kg)', validators=[DataRequired(), NumberRange(min=0.1)])
    submit = SubmitField('Update')

class RemoveCartForm(FlaskForm):
    """Remove cart item form."""
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    submit = SubmitField('Remove')

class CheckoutForm(FlaskForm):
    """Checkout form."""
    delivery_address = TextAreaField('Delivery Address', validators=[DataRequired()])
    delivery_phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    payment_method = SelectField('Payment Method',
                                choices=[
                                    ('cod', 'Cash on Delivery / घरमा पैसा तिर्ने'),
                                    ('esewa', 'eSewa'),
                                    ('khalti', 'Khalti'),
                                    ('phonepay', 'PhonePay'),
                                    ('mobile_banking', 'Mobile Banking'),
                                    ('bank_transfer', 'Bank Transfer')
                                ],
                                validators=[DataRequired()])
    special_instructions = TextAreaField('Special Instructions', validators=[Optional()])
    submit = SubmitField('Place Order')

class ReviewForm(FlaskForm):
    """Product review form."""
    rating = SelectField('Rating', choices=[(5, '5 Stars'), (4, '4 Stars'), (3, '3 Stars'), (2, '2 Stars'), (1, '1 Star')],
                        coerce=int, validators=[DataRequired()])
    comment = TextAreaField('Review', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Submit Review')

class OrderStatusForm(FlaskForm):
    """Order status update form."""
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

class CategoryForm(FlaskForm):
    """Category form."""
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    name_nepali = StringField('Category Name (Nepali)', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Category')

class OrderFilterForm(FlaskForm):
    """Order filtering form."""
    status = SelectField('Status', choices=[('all', 'All Orders')] + [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], default='all')
    submit = SubmitField('Filter')