from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, FloatField, IntegerField, BooleanField, FileField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    """User login form."""
    email = StringField('ईमेल / Email', validators=[DataRequired(), Email()], 
                       render_kw={"placeholder": "your@email.com"})
    password = PasswordField('पासवर्ड / Password', validators=[DataRequired()],
                           render_kw={"placeholder": "Enter your password"})

class RegisterForm(FlaskForm):
    """User registration form."""
    username = StringField('प्रयोगकर्ता नाम / Username', 
                          validators=[DataRequired(), Length(min=3, max=20)],
                          render_kw={"placeholder": "Choose a username"})
    email = StringField('ईमेल / Email', validators=[DataRequired(), Email()],
                       render_kw={"placeholder": "your@email.com"})
    full_name = StringField('पूरा नाम / Full Name', validators=[DataRequired()],
                          render_kw={"placeholder": "Your full name"})
    phone = StringField('फोन नम्बर / Phone Number', validators=[DataRequired()],
                       render_kw={"placeholder": "98XXXXXXXX"})
    address = TextAreaField('ठेगाना / Address', validators=[DataRequired()],
                          render_kw={"placeholder": "Your delivery address", "rows": 3})
    password = PasswordField('पासवर्ड / Password', 
                           validators=[DataRequired(), Length(min=6)],
                           render_kw={"placeholder": "Choose a strong password"})
    password2 = PasswordField('पासवर्ड पुष्टि / Confirm Password',
                            validators=[DataRequired(), EqualTo('password')],
                            render_kw={"placeholder": "Confirm your password"})

class ProductForm(FlaskForm):
    """Admin product management form."""
    name = StringField('Product Name (English)', validators=[DataRequired()])
    name_nepali = StringField('Product Name (Nepali)', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price per KG (NPR)', validators=[DataRequired(), NumberRange(min=0)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    meat_type = SelectField('Meat Type', choices=[('pork', 'Pork'), ('buffalo', 'Buffalo')], validators=[DataRequired()])
    preparation_type = SelectField('Preparation Type', 
                                 choices=[('fresh', 'Fresh'), ('processed', 'Processed'), ('marinated', 'Marinated')],
                                 validators=[DataRequired()])
    stock_kg = FloatField('Stock (KG)', validators=[DataRequired(), NumberRange(min=0)])
    min_order_kg = FloatField('Minimum Order (KG)', validators=[DataRequired(), NumberRange(min=0.1)])
    freshness_hours = IntegerField('Freshness (Hours)', validators=[DataRequired(), NumberRange(min=0)])
    cooking_tips = TextAreaField('Cooking Tips')
    is_featured = BooleanField('Featured Product')
    is_active = BooleanField('Active', default=True)
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])

class CartForm(FlaskForm):
    """Add to cart form."""
    product_id = HiddenField(validators=[DataRequired()])
    quantity = FloatField('Quantity (KG)', validators=[DataRequired(), NumberRange(min=0.1, max=50)],
                         render_kw={"step": "0.1", "min": "0.1"})

class CheckoutForm(FlaskForm):
    """Checkout form."""
    delivery_address = TextAreaField('डेलिभरी ठेगाना / Delivery Address', 
                                   validators=[DataRequired()],
                                   render_kw={"rows": 3})
    delivery_phone = StringField('डेलिभरी फोन / Delivery Phone', 
                                validators=[DataRequired()],
                                render_kw={"placeholder": "98XXXXXXXX"})
    payment_method = SelectField('भुक्तानी तरिका / Payment Method',
                               choices=[
                                   ('cod', 'Cash on Delivery / घरमै पैसा तिर्ने'),
                                   ('esewa', 'eSewa'),
                                   ('khalti', 'Khalti'),
                                   ('mobile_banking', 'Mobile Banking'),
                                   ('bank_transfer', 'Bank Transfer')
                               ],
                               validators=[DataRequired()])
    special_instructions = TextAreaField('विशेष निर्देशन / Special Instructions',
                                       render_kw={"rows": 2, "placeholder": "Any special requirements..."})

class ReviewForm(FlaskForm):
    """Product review form."""
    rating = SelectField('Rating', 
                        choices=[(5, '5 Stars - Excellent'), (4, '4 Stars - Very Good'), 
                                (3, '3 Stars - Good'), (2, '2 Stars - Fair'), (1, '1 Star - Poor')],
                        coerce=int, validators=[DataRequired()])
    comment = TextAreaField('Review Comment', 
                          render_kw={"rows": 4, "placeholder": "Share your experience with this product..."})
    image = FileField('Review Image (Optional)', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])

class OrderStatusForm(FlaskForm):
    """Admin order status update form."""
    status = SelectField('Order Status',
                        choices=[
                            ('pending', 'Pending'),
                            ('confirmed', 'Confirmed'),
                            ('processing', 'Processing'),
                            ('out_for_delivery', 'Out for Delivery'),
                            ('delivered', 'Delivered'),
                            ('cancelled', 'Cancelled')
                        ],
                        validators=[DataRequired()])
    payment_status = SelectField('Payment Status',
                               choices=[
                                   ('pending', 'Pending'),
                                   ('paid', 'Paid'),
                                   ('failed', 'Failed')
                               ],
                               validators=[DataRequired()])

class InvoiceForm(FlaskForm):
    """Invoice generation form."""
    notes = TextAreaField('Additional Notes')
    tax_rate = FloatField('Tax Rate (%)', default=13.0, validators=[NumberRange(min=0, max=100)])
    delivery_charge = FloatField('Delivery Charge', default=0, validators=[NumberRange(min=0)])

class StockAlertForm(FlaskForm):
    """Stock alert configuration form."""
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    threshold_kg = FloatField('Alert Threshold (KG)', validators=[DataRequired(), NumberRange(min=0.1)])
    is_active = BooleanField('Active Alert', default=True)

class NotificationTemplateForm(FlaskForm):
    """Notification template form."""
    name = StringField('Template Name', validators=[DataRequired()])
    type = SelectField('Type', choices=[('email', 'Email'), ('sms', 'SMS')], validators=[DataRequired()])
    event = SelectField('Event', 
                       choices=[
                           ('order_placed', 'Order Placed'),
                           ('order_status_change', 'Order Status Change'),
                           ('low_stock', 'Low Stock Alert'),
                           ('payment_received', 'Payment Received')
                       ],
                       validators=[DataRequired()])
    subject = StringField('Subject (Email only)')
    body_template = TextAreaField('Message Template', validators=[DataRequired()],
                                 render_kw={"rows": 6})
    is_active = BooleanField('Active', default=True)

class SalesReportForm(FlaskForm):
    """Sales report generation form."""
    start_date = StringField('Start Date', validators=[DataRequired()],
                           render_kw={"type": "date"})
    end_date = StringField('End Date', validators=[DataRequired()],
                         render_kw={"type": "date"})
    report_type = SelectField('Report Type',
                            choices=[
                                ('daily', 'Daily Report'),
                                ('weekly', 'Weekly Report'),
                                ('monthly', 'Monthly Report'),
                                ('custom', 'Custom Date Range')
                            ],
                            validators=[DataRequired()])

class CategoryForm(FlaskForm):
    """Category management form."""
    name = StringField('Category Name (English)', validators=[DataRequired()])
    name_nepali = StringField('Category Name (Nepali)', validators=[DataRequired()])
    description = TextAreaField('Description')
    is_active = BooleanField('Active', default=True)

class OrderFilterForm(FlaskForm):
    """Order filtering form."""
    status = SelectField('Status', 
                        choices=[('', 'All Statuses')] + [
                            ('pending', 'Pending'),
                            ('confirmed', 'Confirmed'),
                            ('processing', 'Processing'),
                            ('out_for_delivery', 'Out for Delivery'),
                            ('delivered', 'Delivered'),
                            ('cancelled', 'Cancelled')
                        ])
    payment_method = SelectField('Payment Method',
                               choices=[('', 'All Methods')] + [
                                   ('cod', 'Cash on Delivery'),
                                   ('esewa', 'eSewa'),
                                   ('khalti', 'Khalti'),
                                   ('mobile_banking', 'Mobile Banking'),
                                   ('bank_transfer', 'Bank Transfer')
                               ])
    date_from = StringField('From Date', render_kw={"type": "date"})
    date_to = StringField('To Date', render_kw={"type": "date"})
    customer_search = StringField('Customer Name/Email')

class BulkActionForm(FlaskForm):
    """Bulk actions for orders/products."""
    action = SelectField('Action',
                        choices=[
                            ('', 'Select Action'),
                            ('mark_processing', 'Mark as Processing'),
                            ('mark_delivered', 'Mark as Delivered'),
                            ('export_csv', 'Export to CSV'),
                            ('export_pdf', 'Export to PDF')
                        ])
    selected_items = StringField('Selected Items')
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, IntegerField, BooleanField, SelectField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo, ValidationError
from wtforms.widgets import TextArea

class LoginForm(FlaskForm):
    """User login form."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    """User registration form."""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class ProductForm(FlaskForm):
    """Product creation/edit form with Nepali Unicode support and numeric validation."""

    # Text fields with Nepali Unicode support
    name = StringField('Product Name (English)', validators=[
        DataRequired(message="Product name is required"),
        Length(max=120, message="Product name must be less than 120 characters")
    ], render_kw={
        "placeholder": "Enter product name in English",
        "class": "form-control"
    })

    name_nepali = StringField('उत्पादनको नाम (नेपाली)', validators=[
        DataRequired(message="नेपाली नाम आवश्यक छ / Nepali name is required"),
        Length(max=120, message="नेपाली नाम १२० अक्षरभन्दा कम हुनुपर्छ")
    ], render_kw={
        "placeholder": "नेपालीमा उत्पादनको नाम लेख्नुहोस्",
        "class": "form-control nepali-text",
        "lang": "ne",
        "dir": "ltr"
    })

    description = TextAreaField('विवरण / Description', validators=[
        DataRequired(message="Product description is required")
    ], render_kw={
        "placeholder": "Enter detailed product description in English and Nepali",
        "class": "form-control nepali-text",
        "rows": "4"
    })

    # Numeric fields with strict validation - only numbers allowed
    price = FloatField('मूल्य प्रति केजी / Price per KG (NPR)', validators=[
        DataRequired(message="Price is required"),
        NumberRange(min=0.01, message="Price must be greater than 0")
    ], render_kw={
        "placeholder": "Enter price in numbers only (e.g. 850.50)",
        "class": "form-control numeric-only",
        "step": "0.01",
        "min": "0.01",
        "pattern": "[0-9]+(\.[0-9]{1,2})?",
        "title": "Please enter numbers only (decimals allowed)"
    })

    stock_kg = FloatField('स्टक मात्रा / Stock Quantity (KG)', validators=[
        DataRequired(message="Stock quantity is required"),
        NumberRange(min=0, message="Stock cannot be negative")
    ], render_kw={
        "placeholder": "Enter stock in KG (numbers only)",
        "class": "form-control numeric-only",
        "step": "0.1",
        "min": "0",
        "pattern": "[0-9]+(\.[0-9]{1,2})?",
        "title": "Please enter numbers only (decimals allowed)"
    })

    min_order_kg = FloatField('न्यूनतम अर्डर / Minimum Order (KG)', validators=[
        DataRequired(message="Minimum order quantity is required"),
        NumberRange(min=0.1, message="Minimum order must be at least 0.1 KG")
    ], default=0.5, render_kw={
        "placeholder": "Minimum order quantity (numbers only)",
        "class": "form-control numeric-only",
        "step": "0.1",
        "min": "0.1",
        "pattern": "[0-9]+(\.[0-9]{1,2})?",
        "title": "Please enter numbers only (decimals allowed)"
    })

    # Other form fields
    category_id = SelectField('श्रेणी / Category', coerce=int, validators=[
        DataRequired(message="Please select a category")
    ])

    meat_type = SelectField('मासुको प्रकार / Meat Type', choices=[
        ('pork', 'Pork / सुंगुर'),
        ('buffalo', 'Buffalo / भैंसी'),
        ('chicken', 'Chicken / कुखुरा'),
        ('goat', 'Goat / खसी')
    ], validators=[DataRequired(message="Please select meat type")])

    preparation_type = SelectField('तयारी प्रकार / Preparation Type', choices=[
        ('fresh', 'Fresh / ताजा'),
        ('processed', 'Processed / प्रशोधित'),
        ('marinated', 'Marinated / मसला लगाएको')
    ], default='fresh')

    freshness_hours = IntegerField('ताजापन घण्टा / Freshness Hours', validators=[
        DataRequired(message="Freshness hours is required"),
        NumberRange(min=1, max=168, message="Freshness hours must be between 1-168 hours")
    ], default=24, render_kw={
        "placeholder": "Hours since processing (numbers only)",
        "class": "form-control numeric-only",
        "min": "1",
        "max": "168",
        "pattern": "[0-9]+",
        "title": "Please enter numbers only (1-168)"
    })

    cooking_tips = TextAreaField('खाना पकाउने सुझाव / Cooking Tips', validators=[Optional()], render_kw={
        "placeholder": "Enter cooking tips and suggestions in English and Nepali",
        "class": "form-control nepali-text",
        "rows": "3"
    })

    is_featured = BooleanField('विशेष उत्पादन / Featured Product')
    is_active = BooleanField('सक्रिय / Active', default=True)

    image = FileField('उत्पादनको तस्बिर / Product Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only image files are allowed!')
    ])

    submit = SubmitField('Save Product')

    def validate_price(self, price):
        """Custom validation for price field to ensure only numeric input."""
        try:
            # Convert to float to check if it's a valid number
            float_value = float(price.data)
            if float_value <= 0:
                raise ValidationError('❌ मूल्य शून्यभन्दा बढी हुनुपर्छ / Price must be greater than 0')
        except (ValueError, TypeError):
            raise ValidationError('❌ मूल्यमा केवल संख्या मात्र लेख्नुहोस् / Please enter numbers only in price field')

    def validate_stock_kg(self, stock_kg):
        """Custom validation for stock field to ensure only numeric input."""
        try:
            # Convert to float to check if it's a valid number
            float_value = float(stock_kg.data)
            if float_value < 0:
                raise ValidationError('❌ स्टक ऋणात्मक हुन सक्दैन / Stock cannot be negative')
        except (ValueError, TypeError):
            raise ValidationError('❌ स्टकमा केवल संख्या मात्र लेख्नुहोस् / Please enter numbers only in stock field')

    def validate_min_order_kg(self, min_order_kg):
        """Custom validation for minimum order field to ensure only numeric input."""
        try:
            # Convert to float to check if it's a valid number
            float_value = float(min_order_kg.data)
            if float_value < 0.1:
                raise ValidationError('❌ न्यूनतम अर्डर ०.१ केजीभन्दा कम हुन सक्दैन / Minimum order cannot be less than 0.1 KG')
        except (ValueError, TypeError):
            raise ValidationError('❌ न्यूनतम अर्डरमा केवल संख्या मात्र लेख्नुहोस् / Please enter numbers only in minimum order field')

    def validate_freshness_hours(self, freshness_hours):
        """Custom validation for freshness hours field to ensure only numeric input."""
        try:
            # Convert to int to check if it's a valid number
            int_value = int(freshness_hours.data)
            if int_value < 1 or int_value > 168:
                raise ValidationError('❌ ताजापन १ देखि १६८ घण्टाको बीचमा हुनुपर्छ / Freshness must be between 1-168 hours')
        except (ValueError, TypeError):
            raise ValidationError('❌ ताजापन घण्टामा केवल संख्या मात्र लेख्नुहोस् / Please enter numbers only in freshness hours field')

class CartForm(FlaskForm):
    """Add to cart form with enhanced validation."""
    product_id = HiddenField('Product ID', validators=[DataRequired(message='❌ Product ID required')])
    quantity = FloatField('मात्रा / Quantity (KG)', validators=[
        DataRequired(message='❌ मात्रा आवश्यक छ / Quantity is required'),
        NumberRange(min=0.1, max=100, message='❌ मात्रा ०.१ देखि १०० किलोको बीचमा हुनुपर्छ / Quantity must be between 0.1 and 100 kg')
    ], render_kw={
        "step": "0.1", 
        "min": "0.1", 
        "max": "100",
        "class": "form-control",
        "placeholder": "Enter quantity in kg"
    })

class UpdateCartForm(FlaskForm):
    """Update cart item form."""
    product_id = HiddenField('Product ID', validators=[DataRequired(message="Product ID is required")])
    quantity = FloatField('मात्रा / Quantity (KG)', validators=[
        DataRequired(message="Quantity is required"),
        NumberRange(min=0.1, max=100, message="Quantity must be between 0.1 and 100 kg")
    ], default=1.0, render_kw={
        "class": "form-control numeric-only",
        "step": "0.1",
        "min": "0.1",
        "max": "100",
        "placeholder": "Enter quantity in KG",
        "pattern": "[0-9]+(\.[0-9]{1,2})?",
        "title": "Please enter numbers only (decimals allowed)"
    })
    submit = SubmitField('कार्टमा राख्नुहोस् / Add to Cart')

    def validate_quantity(self, quantity):
        """Custom validation for quantity field to ensure only numeric input."""
        try:
            # Convert to float to check if it's a valid number
            float_value = float(quantity.data)
            if float_value <= 0:
                raise ValidationError('❌ मात्रा शून्यभन्दा बढी हुनुपर्छ / Quantity must be greater than 0')
            if float_value > 100:
                raise ValidationError('❌ एक पटकमा १०० केजीभन्दा बढी अर्डर गर्न सकिँदैन / Cannot order more than 100 kg at once')
        except (ValueError, TypeError):
            raise ValidationError('❌ मात्रामा केवल संख्या मात्र लेख्नुहोस् / Please enter numbers only in quantity field')

class CheckoutForm(FlaskForm):
    """Checkout form."""
    delivery_address = TextAreaField('Delivery Address', validators=[DataRequired()])
    delivery_phone = StringField('Delivery Phone', validators=[DataRequired(), Length(max=20)])
    payment_method = SelectField('Payment Method', choices=[
        ('cod', 'Cash on Delivery / घरमा पैसा तिर्ने'),
        ('esewa', 'eSewa'),
        ('khalti', 'Khalti'),
        ('bank_transfer', 'Bank Transfer / बैंक ट्रान्सफर')
    ], validators=[DataRequired()])
    special_instructions = TextAreaField('Special Instructions', validators=[Optional()])
    submit = SubmitField('Place Order')

class ReviewForm(FlaskForm):
    """Product review form."""
    rating = SelectField('Rating', choices=[
        (5, '5 Stars - Excellent'),
        (4, '4 Stars - Good'),
        (3, '3 Stars - Average'),
        (2, '2 Stars - Poor'),
        (1, '1 Star - Terrible')
    ], coerce=int, validators=[DataRequired()])
    comment = TextAreaField('Review Comment', validators=[Optional(), Length(max=500)])
    image = FileField('Review Image (Optional)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    submit = SubmitField('Submit Review')

class OrderStatusForm(FlaskForm):
    """Order status update form."""
    status = SelectField('Order Status', choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], validators=[DataRequired()])
    payment_status = SelectField('Payment Status', choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ], validators=[DataRequired()])
    submit = SubmitField('Update Status')

class InvoiceForm(FlaskForm):
    """Invoice editing form."""
    notes = TextAreaField('Invoice Notes', validators=[Optional()])
    delivery_charge = FloatField('Delivery Charge', validators=[DataRequired(), NumberRange(min=0)], default=50.0)
    tax_rate = FloatField('Tax Rate (%)', validators=[DataRequired(), NumberRange(min=0, max=100)], default=13.0)
    submit = SubmitField('Update Invoice')

class StockAlertForm(FlaskForm):
    """Stock alert configuration form."""
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    threshold_kg = FloatField('Alert Threshold (KG)', validators=[DataRequired(), NumberRange(min=0)], default=5.0)
    is_active = BooleanField('Active Alert', default=True)
    submit = SubmitField('Save Alert')

class NotificationTemplateForm(FlaskForm):
    """Notification template form."""
    name = StringField('Template Name', validators=[DataRequired(), Length(max=100)])
    type = SelectField('Type', choices=[
        ('email', 'Email'),
        ('sms', 'SMS')
    ], validators=[DataRequired()])
    event = SelectField('Event', choices=[
        ('order_placed', 'Order Placed'),
        ('order_status_change', 'Order Status Change'),
        ('low_stock', 'Low Stock Alert'),
        ('new_customer', 'New Customer Registration')
    ], validators=[DataRequired()])
    subject = StringField('Subject (Email only)', validators=[Optional(), Length(max=200)])
    body_template = TextAreaField('Message Template', validators=[DataRequired()], widget=TextArea())
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Template')

class SalesReportForm(FlaskForm):
    """Sales report generation form."""
    start_date = StringField('Start Date', validators=[DataRequired()])
    end_date = StringField('End Date', validators=[DataRequired()])
    report_type = SelectField('Report Type', choices=[
        ('daily', 'Daily Sales'),
        ('weekly', 'Weekly Sales'),
        ('monthly', 'Monthly Sales'),
        ('product', 'Product Performance'),
        ('customer', 'Customer Analysis')
    ], validators=[DataRequired()])
    submit = SubmitField('Generate Report')

class CategoryForm(FlaskForm):
    """Category creation/edit form."""
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    name_nepali = StringField('Nepali Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Category')

class OrderFilterForm(FlaskForm):
    """Order filtering form."""
    status = SelectField('Status', choices=[
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], default='')
    date_from = StringField('From Date')
    date_to = StringField('To Date')
    customer_search = StringField('Customer Search')
    submit = SubmitField('Filter')

class RemoveCartForm(FlaskForm):
    """Remove item from cart form."""
    product_id = HiddenField('Product ID', validators=[DataRequired(message="Product ID is required")])
    submit = SubmitField('हटाउनुहोस् / Remove')

class BulkActionForm(FlaskForm):
    """Bulk action form for orders."""
    action = SelectField('Action', choices=[
        ('', 'Select Action'),
        ('confirm', 'Confirm Orders'),
        ('processing', 'Mark as Processing'),
        ('out_for_delivery', 'Mark as Out for Delivery'),
        ('delivered', 'Mark as Delivered'),
        ('export_selected', 'Export Selected')
    ], validators=[DataRequired()])
    submit = SubmitField('Execute')