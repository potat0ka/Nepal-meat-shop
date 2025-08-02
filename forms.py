# Improved CartForm validation with custom validation for product_id.
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, BooleanField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo, ValidationError
import re

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
    """Form for adding/editing products."""
    name = StringField('Product Name', validators=[DataRequired(), Length(min=2, max=120)])
    name_nepali = StringField('Product Name (Nepali)', validators=[DataRequired(), Length(min=2, max=120)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=500)])
    price = FloatField('Price per kg', validators=[DataRequired(), NumberRange(min=1, message='Price must be at least Rs. 1')])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    meat_type = SelectField('Meat Type', choices=[('pork', 'Pork'), ('buffalo', 'Buffalo')], validators=[DataRequired()])
    preparation_type = SelectField('Preparation Type', choices=[('fresh', 'Fresh'), ('processed', 'Processed')], validators=[DataRequired()])
    stock_kg = FloatField('Stock (kg)', validators=[DataRequired(), NumberRange(min=0, message='Stock cannot be negative')])
    min_order_kg = FloatField('Minimum Order (kg)', validators=[DataRequired(), NumberRange(min=0.1, message='Minimum order must be at least 0.1 kg')])
    freshness_hours = IntegerField('Freshness (hours)', validators=[Optional(), NumberRange(min=1, max=72, message='Freshness must be between 1-72 hours')])
    cooking_tips = TextAreaField('Cooking Tips', validators=[Optional(), Length(max=300)])
    is_featured = BooleanField('Featured Product')
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save Product')

    def validate_price(self, field):
        """Custom validation for price field."""
        try:
            value = float(field.data)
            if value <= 0:
                raise ValidationError('Price must be greater than 0')
        except (ValueError, TypeError):
            raise ValidationError('Please enter a valid price')

    def validate_stock_kg(self, field):
        """Custom validation for stock field."""
        try:
            value = float(field.data)
            if value < 0:
                raise ValidationError('Stock cannot be negative')
        except (ValueError, TypeError):
            raise ValidationError('Please enter a valid stock amount')

    def validate_min_order_kg(self, field):
        """Custom validation for minimum order field."""
        try:
            value = float(field.data)
            if value <= 0:
                raise ValidationError('Minimum order must be greater than 0')
        except (ValueError, TypeError):
            raise ValidationError('Please enter a valid minimum order amount')

class CartForm(FlaskForm):
    """Form for adding items to cart."""
    product_id = HiddenField('Product ID', validators=[DataRequired(message="उत्पादन चयन गर्नुहोस् / Product selection is required")])
    quantity = FloatField('Quantity (kg)', validators=[
        DataRequired(message="मात्रा आवश्यक / Quantity is required"),
        NumberRange(min=2.0, max=100, message="मात्रा २ देखि १०० केजी बीचमा हुनुपर्छ / Quantity must be between 2 and 100 kg")
    ])

    def validate_product_id(self, field):
        """Custom validation for product_id."""
        if not field.data or field.data == '':
            raise ValidationError('उत्पादन चयन गर्नुहोस् / Product selection is required')

        try:
            product_id = int(field.data)
            from models import Product
            product = Product.query.get(product_id)
            if not product or not product.is_active:
                raise ValidationError('वैध उत्पादन चयन गर्नुहोस् / Please select a valid product')
        except (ValueError, TypeError):
            raise ValidationError('वैध उत्पादन चयन गर्नुहोस् / Please select a valid product')

class UpdateCartForm(FlaskForm):
    """Form for updating cart item quantity."""
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    quantity = FloatField('Quantity (kg)', validators=[DataRequired(), NumberRange(min=0.1, max=100, message='Quantity must be between 0.1 and 100 kg')])
    submit = SubmitField('Update')

class RemoveCartForm(FlaskForm):
    """Form for removing items from cart."""
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
        ('esewa', 'eSewa Digital Wallet'),
        ('khalti', 'Khalti Digital Wallet'),
        ('phonepay', 'PhonePay'),
        ('mobile_banking', 'Mobile Banking'),
        ('bank_transfer', 'Bank Transfer')
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
```# Improved CartForm validation with custom validation for product_id.
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, BooleanField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo, ValidationError
import re

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
    """Form for adding/editing products."""
    name = StringField('Product Name', validators=[DataRequired(), Length(min=2, max=120)])
    name_nepali = StringField('Product Name (Nepali)', validators=[DataRequired(), Length(min=2, max=120)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=500)])
    price = FloatField('Price per kg', validators=[DataRequired(), NumberRange(min=1, message='Price must be at least Rs. 1')])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    meat_type = SelectField('Meat Type', choices=[('pork', 'Pork'), ('buffalo', 'Buffalo')], validators=[DataRequired()])
    preparation_type = SelectField('Preparation Type', choices=[('fresh', 'Fresh'), ('processed', 'Processed')], validators=[DataRequired()])
    stock_kg = FloatField('Stock (kg)', validators=[DataRequired(), NumberRange(min=0, message='Stock cannot be negative')])
    min_order_kg = FloatField('Minimum Order (kg)', validators=[DataRequired(), NumberRange(min=0.1, message='Minimum order must be at least 0.1 kg')])
    freshness_hours = IntegerField('Freshness (hours)', validators=[Optional(), NumberRange(min=1, max=72, message='Freshness must be between 1-72 hours')])
    cooking_tips = TextAreaField('Cooking Tips', validators=[Optional(), Length(max=300)])
    is_featured = BooleanField('Featured Product')
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save Product')

    def validate_price(self, field):
        """Custom validation for price field."""
        try:
            value = float(field.data)
            if value <= 0:
                raise ValidationError('Price must be greater than 0')
        except (ValueError, TypeError):
            raise ValidationError('Please enter a valid price')

    def validate_stock_kg(self, field):
        """Custom validation for stock field."""
        try:
            value = float(field.data)
            if value < 0:
                raise ValidationError('Stock cannot be negative')
        except (ValueError, TypeError):
            raise ValidationError('Please enter a valid stock amount')

    def validate_min_order_kg(self, field):
        """Custom validation for minimum order field."""
        try:
            value = float(field.data)
            if value <= 0:
                raise ValidationError('Minimum order must be greater than 0')
        except (ValueError, TypeError):
            raise ValidationError('Please enter a valid minimum order amount')

class CartForm(FlaskForm):
    """Form for adding items to cart."""
    product_id = HiddenField('Product ID', validators=[DataRequired(message="उत्पादन चयन गर्नुहोस् / Product selection is required")])
    quantity = FloatField('Quantity (kg)', validators=[
        DataRequired(message="मात्रा आवश्यक / Quantity is required"),
        NumberRange(min=2.0, max=100, message="मात्रा २ देखि १०० केजी बीचमा हुनुपर्छ / Quantity must be between 2 and 100 kg")
    ])

    def validate_product_id(self, field):
        """Custom validation for product_id."""
        if not field.data or field.data == '':
            raise ValidationError('उत्पादन चयन गर्नुहोस् / Product selection is required')

        try:
            product_id = int(field.data)
            from models import Product
            product = Product.query.get(product_id)
            if not product or not product.is_active:
                raise ValidationError('वैध उत्पादन चयन गर्नुहोस् / Please select a valid product')
        except (ValueError, TypeError):
            raise ValidationError('वैध उत्पादन चयन गर्नुहोस् / Please select a valid product')

class UpdateCartForm(FlaskForm):
    """Form for updating cart item quantity."""
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    quantity = FloatField('Quantity (kg)', validators=[DataRequired(), NumberRange(min=0.1, max=100, message='Quantity must be between 0.1 and 100 kg')])
    submit = SubmitField('Update')

class RemoveCartForm(FlaskForm):
    """Form for removing items from cart."""
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
        ('esewa', 'eSewa Digital Wallet'),
        ('khalti', 'Khalti Digital Wallet'),
        ('phonepay', 'PhonePay'),
        ('mobile_banking', 'Mobile Banking'),
        ('bank_transfer', 'Bank Transfer')
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