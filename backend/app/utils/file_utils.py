#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - File Utilities
File upload, management, and processing utilities.
"""

import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

def save_uploaded_file(file, folder):
    """
    Save uploaded file to the specified folder with unique naming.
    
    Args:
        file: The uploaded file object from Flask request
        folder: The subfolder name (e.g., 'products', 'reviews', 'profiles')
    
    Returns:
        str: The relative path to the saved file, or None if no file
    """
    if file and file.filename:
        # Get secure filename to prevent directory traversal attacks
        filename = secure_filename(file.filename)
        
        # Add timestamp and UUID to avoid filename conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Create folder path if it doesn't exist
        folder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(folder_path, exist_ok=True)
        
        # Save file to disk
        file_path = os.path.join(folder_path, unique_filename)
        file.save(file_path)
        
        # Return relative path for database storage
        return f"{folder}/{unique_filename}"
    
    return None

def delete_file(file_path):
    """
    Delete a file from the uploads directory.
    
    Args:
        file_path: Relative path to the file (e.g., 'products/image.jpg')
    
    Returns:
        bool: True if file was deleted, False otherwise
    """
    if not file_path:
        return False
    
    try:
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    except Exception as e:
        current_app.logger.error(f"Error deleting file {file_path}: {e}")
    
    return False

def get_file_url(file_path):
    """
    Get the URL for accessing an uploaded file.
    
    Args:
        file_path: Relative path to the file
    
    Returns:
        str: URL for accessing the file
    """
    if not file_path:
        return None
    
    from flask import url_for
    return url_for('static', filename=f'uploads/{file_path}')

def validate_image_file(file):
    """
    Validate that uploaded file is a valid image.
    
    Args:
        file: Uploaded file object
    
    Returns:
        bool: True if valid image, False otherwise
    """
    if not file or not file.filename:
        return False
    
    # Check file extension
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    return file_ext in allowed_extensions