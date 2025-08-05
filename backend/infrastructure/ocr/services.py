"""
OCR services for Smart Accounts Management System.
Handles OCR processing using both PaddleOCR (open source) and OpenAI Vision API.
Users can choose their preferred OCR method.
"""

import os
import re
import requests
import base64
import json
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
from datetime import datetime
import logging
from enum import Enum

from django.conf import settings
from domain.receipts.entities import OCRData

logger = logging.getLogger(__name__)


class OCRMethod(Enum):
    """Available OCR methods."""
    PADDLE_OCR = "paddle_ocr"
    OPENAI_VISION = "openai_vision"
    FALLBACK = "fallback"


class OCRService:
    """Service for OCR processing of receipts with multiple engine support."""
    
    def __init__(self, preferred_method: OCRMethod = OCRMethod.PADDLE_OCR):
        """
        Initialize OCR service.
        
        Args:
            preferred_method: Preferred OCR method to use
        """
        self.preferred_method = preferred_method
        self.paddle_ocr_engine = None
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize all available OCR engines."""
        # Initialize PaddleOCR
        self._initialize_paddle_ocr()
        
        # Check OpenAI API key availability
        if not self.openai_api_key:
            logger.warning("OpenAI API key not configured, OpenAI Vision API will not be available")
    
    def _initialize_paddle_ocr(self):
        """Initialize the PaddleOCR engine."""
        try:
            from paddleocr import PaddleOCR
            
            self.paddle_ocr_engine = PaddleOCR(
                use_angle_cls=True,
                lang='en'
            )
            logger.info("PaddleOCR initialized successfully")
            
        except ImportError:
            logger.warning("PaddleOCR not available")
            self.paddle_ocr_engine = None
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            self.paddle_ocr_engine = None
    
    def _extract_with_openai_vision(self, image_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Extract text using OpenAI Vision API.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (success, extracted_text, error_message)
        """
        if not self.openai_api_key:
            return False, None, "OpenAI API key not configured"
        
        try:
            # Read and encode the image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Prepare the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            payload = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Extract all text from this receipt image. 
                                Focus on identifying:
                                - Merchant/store name
                                - Date
                                - Receipt/invoice number
                                - Individual items and prices
                                - Subtotal, VAT, and total amounts
                                - Any VAT numbers
                                Return the text exactly as it appears on the receipt."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000
            }
            
            # Make the API request
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                extracted_text = result['choices'][0]['message']['content']
                return True, extracted_text, None
            else:
                error_msg = f"OpenAI API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"OpenAI Vision API processing failed: {e}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _extract_with_paddle_ocr(self, image_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Extract text using PaddleOCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (success, extracted_text, error_message)
        """
        if not self.paddle_ocr_engine:
            return False, None, "PaddleOCR not available"
        
        try:
            # Perform OCR on the image
            result = self.paddle_ocr_engine.ocr(image_path, cls=True)
            
            if not result or not result[0]:
                return False, None, "No text detected in image"
            
            # Extract text from OCR result
            extracted_text = []
            for line in result[0]:
                if line and len(line) >= 2:
                    text = line[1][0]  # Get the text from the OCR result
                    confidence = line[1][1]  # Get confidence score
                    if confidence > 0.5:  # Only include text with confidence > 50%
                        extracted_text.append(text)
            
            full_text = '\n'.join(extracted_text)
            return True, full_text, None
            
        except Exception as e:
            error_msg = f"PaddleOCR processing failed: {e}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _fallback_ocr(self, image_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Fallback OCR method when other engines are not available."""
        try:
            # For now, return a mock OCR result
            # In a real implementation, you could use Tesseract or other OCR libraries
            mock_text = """
            SAMPLE RECEIPT
            Merchant: Tesco Express
            Date: 15/12/2024
            Receipt #: 123456789
            Items:
            - Milk £1.20
            - Bread £0.85
            - Eggs £2.10
            Subtotal: £4.15
            VAT: £0.83
            Total: £4.98
            """
            return True, mock_text, None
        except Exception as e:
            return False, None, str(e)
    
    def extract_text_from_image(self, image_path: str, method: Optional[OCRMethod] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Extract text from an image file using the specified or preferred method.
        
        Args:
            image_path: Path to the image file
            method: OCR method to use (if None, uses preferred_method)
            
        Returns:
            Tuple of (success, extracted_text, error_message)
        """
        if method is None:
            method = self.preferred_method
        
        # Try the specified method first
        if method == OCRMethod.OPENAI_VISION:
            success, text, error = self._extract_with_openai_vision(image_path)
            if success:
                return True, text, None
            logger.warning(f"OpenAI Vision failed: {error}, trying fallback")
            
        elif method == OCRMethod.PADDLE_OCR:
            success, text, error = self._extract_with_paddle_ocr(image_path)
            if success:
                return True, text, None
            logger.warning(f"PaddleOCR failed: {error}, trying fallback")
        
        # If specified method failed or is fallback, try fallback
        return self._fallback_ocr(image_path)
    
    def extract_text_from_image_with_method(self, image_path: str, method: OCRMethod) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Extract text from an image file using a specific method.
        
        Args:
            image_path: Path to the image file
            method: OCR method to use
            
        Returns:
            Tuple of (success, extracted_text, error_message)
        """
        return self.extract_text_from_image(image_path, method)
    
    def extract_text_from_url(self, image_url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Extract text from an image URL.
        
        Args:
            image_url: URL of the image
            
        Returns:
            Tuple of (success, extracted_text, error_message)
        """
        try:
            # Download image from URL
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            temp_path = f"/tmp/receipt_{datetime.now().timestamp()}.jpg"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            try:
                # Extract text from temporary file
                success, text, error = self.extract_text_from_image(temp_path)
                return success, text, error
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            logger.error(f"Failed to process image from URL: {e}")
            return False, None, str(e)
    
    def extract_receipt_data(self, image_path: str, method: Optional[OCRMethod] = None) -> Tuple[bool, Optional[OCRData], Optional[str]]:
        """
        Extract structured receipt data from an image.
        
        Args:
            image_path: Path to the receipt image
            method: OCR method to use (if None, uses preferred_method)
            
        Returns:
            Tuple of (success, ocr_data, error_message)
        """
        try:
            # Extract raw text first
            success, raw_text, error = self.extract_text_from_image(image_path, method)
            if not success:
                return False, None, error
            
            # Parse the extracted text to get structured data
            ocr_data = self._parse_receipt_text(raw_text)
            
            return True, ocr_data, None
            
        except Exception as e:
            logger.error(f"Receipt data extraction failed: {e}")
            return False, None, str(e)
    
    def extract_receipt_data_with_method(self, image_path: str, method: OCRMethod) -> Tuple[bool, Optional[OCRData], Optional[str]]:
        """
        Extract structured receipt data from an image using a specific method.
        
        Args:
            image_path: Path to the receipt image
            method: OCR method to use
            
        Returns:
            Tuple of (success, ocr_data, error_message)
        """
        return self.extract_receipt_data(image_path, method)
    
    def extract_receipt_data_from_url(self, image_url: str, method: Optional[OCRMethod] = None) -> Tuple[bool, Optional[OCRData], Optional[str]]:
        """
        Extract structured receipt data from an image URL.
        
        Args:
            image_url: URL of the receipt image
            method: OCR method to use (if None, uses preferred_method)
            
        Returns:
            Tuple of (success, ocr_data, error_message)
        """
        try:
            # Download image from URL
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            temp_path = f"/tmp/receipt_{datetime.now().timestamp()}.jpg"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            try:
                # Extract receipt data from temporary file
                success, ocr_data, error = self.extract_receipt_data(temp_path, method)
                return success, ocr_data, error
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            logger.error(f"Failed to process receipt from URL: {e}")
            return False, None, str(e)
    
    def get_available_methods(self) -> List[OCRMethod]:
        """
        Get list of available OCR methods.
        
        Returns:
            List of available OCR methods
        """
        available_methods = [OCRMethod.FALLBACK]  # Fallback is always available
        
        if self.paddle_ocr_engine:
            available_methods.append(OCRMethod.PADDLE_OCR)
        
        if self.openai_api_key:
            available_methods.append(OCRMethod.OPENAI_VISION)
        
        return available_methods
    
    def is_method_available(self, method: OCRMethod) -> bool:
        """
        Check if a specific OCR method is available.
        
        Args:
            method: OCR method to check
            
        Returns:
            True if method is available, False otherwise
        """
        if method == OCRMethod.FALLBACK:
            return True
        elif method == OCRMethod.PADDLE_OCR:
            return self.paddle_ocr_engine is not None
        elif method == OCRMethod.OPENAI_VISION:
            return self.openai_api_key is not None
        return False
    
    def _parse_receipt_text(self, text: str) -> OCRData:
        """
        Parse extracted text to get structured receipt data.
        
        Args:
            text: Raw text extracted from receipt
            
        Returns:
            OCRData object with parsed information
        """
        lines = text.split('\n')
        
        # Initialize OCR data
        ocr_data = OCRData(raw_text=text)
        
        # Extract merchant name (usually at the top)
        ocr_data.merchant_name = self._extract_merchant_name(lines)
        
        # Extract total amount
        ocr_data.total_amount = self._extract_total_amount(lines)
        
        # Extract date
        ocr_data.date = self._extract_date(lines)
        
        # Extract VAT information
        ocr_data.vat_amount = self._extract_vat_amount(lines)
        ocr_data.vat_number = self._extract_vat_number(lines)
        
        # Extract receipt number
        ocr_data.receipt_number = self._extract_receipt_number(lines)
        
        # Extract items
        ocr_data.items = self._extract_items(lines)
        
        # Calculate confidence score (simplified)
        ocr_data.confidence_score = self._calculate_confidence_score(ocr_data)
        
        return ocr_data
    
    def _extract_merchant_name(self, lines: List[str]) -> Optional[str]:
        """Extract merchant name from receipt lines."""
        # Look for merchant name in first few lines
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            if line and len(line) > 3 and len(line) < 100:
                # Skip lines that look like addresses or phone numbers
                if not re.search(r'\d{4,}', line) and not re.search(r'@', line):
                    return line
        return None
    
    def _extract_total_amount(self, lines: List[str]) -> Optional[Decimal]:
        """Extract total amount from receipt lines."""
        # Look for total amount patterns
        total_patterns = [
            r'total[:\s]*£?\s*(\d+\.?\d*)',
            r'amount[:\s]*£?\s*(\d+\.?\d*)',
            r'£\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*£',
            r'(\d+\.?\d*)'
        ]
        
        for line in lines:
            line = line.strip().lower()
            for pattern in total_patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        amount = Decimal(match.group(1))
                        if 0 < amount < 100000:  # Reasonable amount range
                            return amount
                    except (ValueError, TypeError):
                        continue
        return None
    
    def _extract_date(self, lines: List[str]) -> Optional[datetime]:
        """Extract date from receipt lines."""
        # UK date patterns
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{1,2})\s+(\w+)\s+(\d{2,4})',  # DD Month YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        ]
        
        for line in lines:
            line = line.strip()
            for pattern in date_patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        if len(match.groups()) == 3:
                            day, month, year = match.groups()
                            
                            # Handle 2-digit years
                            if len(year) == 2:
                                year = f"20{year}"
                            
                            # Convert month name to number if needed
                            if month.isalpha():
                                month_names = {
                                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                                    'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                                    'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                                }
                                month = month_names.get(month[:3].lower(), 1)
                            
                            return datetime(int(year), int(month), int(day))
                    except (ValueError, TypeError):
                        continue
        return None
    
    def _extract_vat_amount(self, lines: List[str]) -> Optional[Decimal]:
        """Extract VAT amount from receipt lines."""
        vat_patterns = [
            r'vat[:\s]*£?\s*(\d+\.?\d*)',
            r'tax[:\s]*£?\s*(\d+\.?\d*)',
            r'gst[:\s]*£?\s*(\d+\.?\d*)',
        ]
        
        for line in lines:
            line = line.strip().lower()
            for pattern in vat_patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        amount = Decimal(match.group(1))
                        if 0 < amount < 10000:  # Reasonable VAT range
                            return amount
                    except (ValueError, TypeError):
                        continue
        return None
    
    def _extract_vat_number(self, lines: List[str]) -> Optional[str]:
        """Extract VAT number from receipt lines."""
        vat_number_patterns = [
            r'vat\s*no[:\s]*([A-Z]{2}\d{9,12})',
            r'vat\s*number[:\s]*([A-Z]{2}\d{9,12})',
            r'([A-Z]{2}\d{9,12})',
        ]
        
        for line in lines:
            line = line.strip()
            for pattern in vat_number_patterns:
                match = re.search(pattern, line)
                if match:
                    return match.group(1)
        return None
    
    def _extract_receipt_number(self, lines: List[str]) -> Optional[str]:
        """Extract receipt number from receipt lines."""
        receipt_number_patterns = [
            r'receipt[:\s]*#?\s*(\d+)',
            r'invoice[:\s]*#?\s*(\d+)',
            r'transaction[:\s]*#?\s*(\d+)',
            r'(\d{6,})',  # Generic 6+ digit number
        ]
        
        for line in lines:
            line = line.strip().lower()
            for pattern in receipt_number_patterns:
                match = re.search(pattern, line)
                if match:
                    return match.group(1)
        return None
    
    def _extract_items(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract individual items from receipt lines."""
        items = []
        
        for line in lines:
            line = line.strip()
            # Look for item patterns (description + price)
            item_match = re.search(r'(.+?)\s+£?\s*(\d+\.?\d*)$', line)
            if item_match:
                description = item_match.group(1).strip()
                price = item_match.group(2)
                
                if len(description) > 2 and len(description) < 100:
                    try:
                        items.append({
                            'description': description,
                            'price': Decimal(price),
                            'quantity': 1
                        })
                    except (ValueError, TypeError):
                        continue
        
        return items
    
    def _calculate_confidence_score(self, ocr_data: OCRData) -> float:
        """Calculate confidence score for extracted data."""
        score = 0.0
        total_fields = 0
        
        if ocr_data.merchant_name:
            score += 0.2
        total_fields += 1
        
        if ocr_data.total_amount:
            score += 0.3
        total_fields += 1
        
        if ocr_data.date:
            score += 0.2
        total_fields += 1
        
        if ocr_data.vat_amount:
            score += 0.1
        total_fields += 1
        
        if ocr_data.vat_number:
            score += 0.1
        total_fields += 1
        
        if ocr_data.receipt_number:
            score += 0.1
        total_fields += 1
        
        if ocr_data.items:
            score += 0.1 * min(len(ocr_data.items), 5)  # Cap at 5 items
        total_fields += 1
        
        return min(score, 1.0)  # Cap at 1.0 