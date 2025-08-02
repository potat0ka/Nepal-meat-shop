from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, BooleanField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo, Optional
from wtforms.widgets import TextArea

class LoginForm(FlaskForm):
    """User login form."""
    email = StringField('ईमेल / Email', validators=[DataRequired(), Email()])
    password = PasswordField('पासवर्ड / Password', validators=[DataRequired()])
    submit = SubmitField('लगइन / Login')

class RegisterForm(FlaskForm):
    """User registration form."""
    username = StringField('प्रयोगकर्ता नाम / Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('ईमेल / Email', validators=[DataRequired(), Email()])
    full_name = StringField('पूरा नाम / Full Name', validators=[DataRequired(), Length(min=2, max=50)])
    phone = StringField('फोन नम्बर / Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    address = TextAreaField('ठेगाना / Address', validators=[Optional(), Length(max=500)])
    password = PasswordField('पासवर्ड / Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('पासवर्ड पुष्टि / Confirm Password', 
                             validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('दर्ता गर्नुहोस् / Register')

class ProductForm(FlaskForm):
    """Product add/edit form."""
    name = StringField('Product Name (English)', validators=[DataRequired(), Length(max=120)])
    name_nepali = StringField('Product Name (Nepali)', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=1000)])
    price = FloatField('Price per KG (NPR)', validators=[DataRequired(), NumberRange(min=0.01)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    meat_type = SelectField('Meat Type', choices=[
        ('pork', 'सुंगुर / Pork'),
        ('buffalo', 'भैंसी / Buffalo'),
        ('chicken', 'कुखुरा / Chicken'),
        ('goat', 'खसी / Goat')
    ], validators=[DataRequired()])
    preparation_type = SelectField('Preparation Type', choices=[
        ('fresh', 'Fresh'),
        ('processed', 'Processed'),
        ('marinated', 'Marinated'),
        ('smoked', 'Smoked')
    ], default='fresh')
    stock_kg = FloatField('Stock (KG)', validators=[DataRequired(), NumberRange(min=0)])
    min_order_kg = FloatField('Minimum Order (KG)', validators=[DataRequired(), NumberRange(min=0.1)], default=0.5)
    freshness_hours = IntegerField('Freshness Hours', validators=[DataRequired(), NumberRange(min=1)], default=24)
    cooking_tips = TextAreaField('Cooking Tips', validators=[Optional(), Length(max=1000)])
    is_featured = BooleanField('Featured Product')
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')])
    submit = SubmitField('Save Product')

class CartForm(FlaskForm):
    """Add to cart form."""
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    quantity = FloatField('मात्रा / Quantity (KG)', validators=[DataRequired(), NumberRange(min=0.1, max=50)])
    submit = SubmitField('कार्टमा थप्नुहोस् / Add to Cart')

class UpdateCartForm(FlaskForm):
    """Update cart item form."""
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    quantity = FloatField('Quantity (KG)', validators=[DataRequired(), NumberRange(min=0.1, max=50)])
    submit = SubmitField('Update')

class RemoveCartForm(FlaskForm):
    """Remove from cart form."""
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    submit = SubmitField('Remove')

class CheckoutForm(FlaskForm):
    """Checkout form."""
    delivery_address = TextAreaField('डेलिभरी ठेगाना / Delivery Address', 
                                   validators=[DataRequired(), Length(min=10, max=500)])
    delivery_phone = StringField('डेलिभरी फोन / Delivery Phone', 
                                validators=[DataRequired(), Length(min=10, max=15)])
    payment_method = SelectField('भुक्तानी विधि / Payment Method', choices=[
        ('cod', 'Cash on Delivery / घरमा पैसा तिर्नुहोस्'),
        ('esewa', 'eSewa'),
        ('khalti', 'Khalti'),
        ('bank', 'Bank Transfer')
    ], validators=[DataRequired()])
    special_instructions = TextAreaField('विशेष निर्देशन / Special Instructions', 
                                       validators=[Optional(), Length(max=500)])
    submit = SubmitField('अर्डर दिनुहोस् / Place Order')

class ReviewForm(FlaskForm):
    """Product review form."""
    rating = SelectField('Rating', choices=[
        (5, '⭐⭐⭐⭐⭐ Excellent'),
        (4, '⭐⭐⭐⭐ Good'),
        (3, '⭐⭐⭐ Average'),
        (2, '⭐⭐ Below Average'),
        (1, '⭐ Poor')
    ], coerce=int, validators=[DataRequired()])
    comment = TextAreaField('समीक्षा / Review', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('समीक्षा पठाउनुहोस् / Submit Review')

class OrderStatusForm(FlaskForm):
    """Order status update form (Admin)."""
    status = SelectField('Order Status', choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], validators=[DataRequired()])
    submit = SubmitField('Update Status')

class CategoryForm(FlaskForm):
    """Category add/edit form."""
    name = StringField('Category Name (English)', validators=[DataRequired(), Length(max=100)])
    name_nepali = StringField('Category Name (Nepali)', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Category')

class OrderFilterForm(FlaskForm):
    """Order filter form (Admin)."""
    status = SelectField('Status', choices=[
        ('', 'All Orders'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ])
    submit = SubmitField('Filter')
