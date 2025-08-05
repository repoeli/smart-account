"""
File storage services for Smart Accounts Management System.
Handles file upload, storage, and management using Cloudinary.
"""

import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Optional, Tuple
from django.conf import settings


class FileStorageService:
    """Service for handling file storage operations."""
    
    def __init__(self):
        """Initialize Cloudinary configuration."""
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET
        )
    
    def upload_file(self, file_path: str, folder: str = "receipts") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload a file to Cloudinary.
        
        Args:
            file_path: Path to the file to upload
            folder: Cloudinary folder to store the file in
            
        Returns:
            Tuple of (success, file_url, error_message)
        """
        try:
            # Upload file to Cloudinary
            result = cloudinary.uploader.upload(
                file_path,
                folder=folder,
                resource_type="auto",
                use_filename=True,
                unique_filename=True,
                overwrite=False
            )
            
            return True, result['secure_url'], None
            
        except Exception as e:
            return False, None, str(e)
    
    def upload_file_from_memory(self, file_data: bytes, filename: str, folder: str = "receipts") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload a file from memory to Cloudinary.
        
        Args:
            file_data: File data as bytes
            filename: Name of the file
            folder: Cloudinary folder to store the file in
            
        Returns:
            Tuple of (success, file_url, error_message)
        """
        try:
            # Upload file from memory to Cloudinary
            result = cloudinary.uploader.upload(
                file_data,
                folder=folder,
                resource_type="auto",
                public_id=filename,
                use_filename=True,
                unique_filename=True,
                overwrite=False
            )
            
            return True, result['secure_url'], None
            
        except Exception as e:
            return False, None, str(e)
    
    def delete_file(self, file_url: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a file from Cloudinary.
        
        Args:
            file_url: URL of the file to delete
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Extract public_id from URL
            public_id = self._extract_public_id_from_url(file_url)
            if not public_id:
                return False, "Could not extract public_id from URL"
            
            # Delete file from Cloudinary
            result = cloudinary.uploader.destroy(public_id)
            
            if result.get('result') == 'ok':
                return True, None
            else:
                return False, f"Failed to delete file: {result.get('result')}"
                
        except Exception as e:
            return False, str(e)
    
    def get_file_info(self, file_url: str) -> Tuple[bool, Optional[dict], Optional[str]]:
        """
        Get information about a file from Cloudinary.
        
        Args:
            file_url: URL of the file
            
        Returns:
            Tuple of (success, file_info, error_message)
        """
        try:
            # Extract public_id from URL
            public_id = self._extract_public_id_from_url(file_url)
            if not public_id:
                return False, None, "Could not extract public_id from URL"
            
            # Get file info from Cloudinary
            result = cloudinary.api.resource(public_id)
            
            return True, {
                'public_id': result['public_id'],
                'format': result['format'],
                'width': result['width'],
                'height': result['height'],
                'bytes': result['bytes'],
                'url': result['secure_url'],
                'created_at': result['created_at']
            }, None
            
        except Exception as e:
            return False, None, str(e)
    
    def _extract_public_id_from_url(self, file_url: str) -> Optional[str]:
        """
        Extract public_id from Cloudinary URL.
        
        Args:
            file_url: Cloudinary URL
            
        Returns:
            Public ID or None if extraction fails
        """
        try:
            # Parse URL to extract public_id
            # Example URL: https://res.cloudinary.com/cloud_name/image/upload/v1234567890/folder/filename.jpg
            parts = file_url.split('/')
            
            # Find the upload part
            upload_index = -1
            for i, part in enumerate(parts):
                if part == 'upload':
                    upload_index = i
                    break
            
            if upload_index == -1:
                return None
            
            # Extract public_id (everything after upload)
            public_id_parts = parts[upload_index + 2:]  # Skip version number
            
            # Remove file extension
            if public_id_parts:
                last_part = public_id_parts[-1]
                if '.' in last_part:
                    public_id_parts[-1] = last_part.rsplit('.', 1)[0]
            
            return '/'.join(public_id_parts)
            
        except Exception:
            return None
    
    def generate_upload_preset(self, folder: str = "receipts") -> str:
        """
        Generate upload preset for client-side uploads.
        
        Args:
            folder: Folder to store uploaded files
            
        Returns:
            Upload preset name
        """
        # In a real implementation, you would create and return an upload preset
        # For now, return a default preset
        return f"smart_accounts_{folder}"
    
    def validate_file_size(self, file_size: int, max_size: int = 10 * 1024 * 1024) -> bool:
        """
        Validate file size.
        
        Args:
            file_size: Size of the file in bytes
            max_size: Maximum allowed file size in bytes
            
        Returns:
            True if file size is valid, False otherwise
        """
        return file_size <= max_size
    
    def validate_file_type(self, filename: str, allowed_extensions: set = None) -> bool:
        """
        Validate file type based on extension.
        
        Args:
            filename: Name of the file
            allowed_extensions: Set of allowed file extensions
            
        Returns:
            True if file type is valid, False otherwise
        """
        if allowed_extensions is None:
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp'}
        
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in allowed_extensions 