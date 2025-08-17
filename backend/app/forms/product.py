#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Product Forms
Product management, categories, and review forms.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class ProductForm(FlaskForm):
    """
    Product creation and editing form for admin users.
    Includes all product details and validation.
    """
    name = StringField('Product Name', validators=[DataRequired(), Length(max=120)])
    name_nepali = StringField('Product Name (Nepali)', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price per kg (रू)', validators=[DataRequired(), NumberRange(min=0.01)])
    category_id = SelectField('Category', coerce=str, validators=[DataRequired()])
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

class CategoryForm(FlaskForm):
    """
    Category creation and editing form.
    Supports bilingual category names.
    """
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    name_nepali = StringField('Category Name (Nepali)', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Category')

class ReviewForm(FlaskForm):
    """
    Product review form for customers.
    Allows rating and comment submission.
    """
    rating = SelectField('Rating', 
                        choices=[(5, '5 Stars'), (4, '4 Stars'), (3, '3 Stars'), (2, '2 Stars'), (1, '1 Star')],
                        coerce=int, validators=[DataRequired()])
    comment = TextAreaField('Review', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Submit Review')

class ProductFilterForm(FlaskForm):
    """
    Product filtering form for search and categorization.
    Helps users find specific products.
    """
    category = SelectField('Category', choices=[('all', 'All Categories')], default='all')
    meat_type = SelectField('Meat Type', 
                           choices=[('all', 'All Types'), ('pork', 'Pork'), ('buffalo', 'Buffalo')], 
                           default='all')
    sort_by = SelectField('Sort By', 
                         choices=[('name', 'Name'), ('price_low', 'Price: Low to High'), 
                                ('price_high', 'Price: High to Low'), ('newest', 'Newest First')],
                         default='name')
    submit = SubmitField('Filter')