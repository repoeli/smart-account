"""
Application use cases for receipt management.
Defines business logic and orchestration for receipt operations.
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from domain.receipts.entities import (
    Receipt, ReceiptStatus, ReceiptType, FileInfo, OCRData, ReceiptMetadata
)
from domain.receipts.repositories import ReceiptRepository
from domain.receipts.services import (
    FileValidationService, ReceiptValidationService, ReceiptBusinessService
)
from domain.accounts.entities import User
from infrastructure.storage.services import FileStorageService
from infrastructure.ocr.services import OCRService, OCRMethod


class ReceiptUploadUseCase:
    """Use case for uploading and processing receipts."""
    
    def __init__(self,
                 receipt_repository: ReceiptRepository,
                 file_validation_service: FileValidationService,
                 file_storage_service: FileStorageService,
                 ocr_service: OCRService,
                 receipt_business_service: ReceiptBusinessService):
        self.receipt_repository = receipt_repository
        self.file_validation_service = file_validation_service
        self.file_storage_service = file_storage_service
        self.ocr_service = ocr_service
        self.receipt_business_service = receipt_business_service
    
    def execute(self, 
                user: User,
                file_data: bytes,
                filename: str,
                mime_type: str,
                receipt_type: ReceiptType = ReceiptType.PURCHASE,
                ocr_method: Optional[OCRMethod] = None) -> Dict[str, Any]:
        """
        Execute receipt upload use case.
        
        Args:
            user: The user uploading the receipt
            file_data: File data as bytes
            filename: Name of the file
            mime_type: MIME type of the file
            receipt_type: Type of receipt
            
        Returns:
            Dictionary with result information
        """
        try:
            # Step 1: Validate file
            file_size = len(file_data)
            is_valid, validation_errors = self.file_validation_service.validate_file(
                filename, file_size, mime_type
            )
            
            if not is_valid:
                return {
                    'success': False,
                    'error': 'File validation failed',
                    'validation_errors': validation_errors
                }
            
            # Step 2: Upload file to storage
            upload_success, file_url, upload_error = self.file_storage_service.upload_file_from_memory(
                file_data, filename
            )
            
            if not upload_success:
                return {
                    'success': False,
                    'error': 'File upload failed',
                    'upload_error': upload_error
                }
            
            # Step 3: Create file info
            file_info = self.file_validation_service.get_file_info(
                filename, file_size, mime_type, file_url
            )
            
            # Step 4: Create receipt entity
            receipt_id = str(uuid.uuid4())
            receipt = Receipt(
                id=receipt_id,
                user=user,
                file_info=file_info,
                status=ReceiptStatus.UPLOADED,
                receipt_type=receipt_type
            )
            
            # Step 5: Save receipt to repository
            saved_receipt = self.receipt_repository.save(receipt)
            
            # Step 6: Process OCR asynchronously (in real implementation, this would be a background task)
            # For now, we'll process it synchronously
            ocr_result = self._process_ocr_async(saved_receipt, ocr_method)
            
            return {
                'success': True,
                'receipt_id': receipt_id,
                'file_url': file_url,
                'status': saved_receipt.status.value,
                'ocr_processed': ocr_result['success'],
                'ocr_data': ocr_result.get('ocr_data'),
                'ocr_error': ocr_result.get('error')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Receipt upload failed: {str(e)}'
            }
    
    def _process_ocr_async(self, receipt: Receipt, ocr_method: Optional[OCRMethod] = None) -> Dict[str, Any]:
        """
        Process OCR for a receipt (simulated async processing).
        
        Args:
            receipt: The receipt to process
            ocr_method: OCR method to use (if None, uses default)
            
        Returns:
            Dictionary with OCR processing result
        """
        try:
            # Update status to processing
            receipt.status = ReceiptStatus.PROCESSING
            self.receipt_repository.save(receipt)
            
            # Extract OCR data from file URL
            ocr_success, ocr_data, ocr_error = self.ocr_service.extract_receipt_data_from_url(
                receipt.file_info.file_url, ocr_method
            )
            
            if ocr_success and ocr_data:
                # Validate OCR data
                is_valid, validation_errors = self.receipt_validation_service.validate_ocr_data(ocr_data)
                
                if is_valid:
                    # Process OCR data and update receipt
                    receipt.process_ocr_data(ocr_data)
                    
                    # Suggest category based on business rules
                    suggested_category = self.receipt_business_service.suggest_category(receipt)
                    if suggested_category:
                        receipt.metadata.category = suggested_category
                    
                    # Determine if it's a business expense
                    is_business_expense = self.receipt_business_service.is_business_expense(receipt)
                    receipt.metadata.is_business_expense = is_business_expense
                    
                    # Save updated receipt
                    self.receipt_repository.save(receipt)
                    
                    return {
                        'success': True,
                        'ocr_data': {
                            'merchant_name': ocr_data.merchant_name,
                            'total_amount': str(ocr_data.total_amount) if ocr_data.total_amount else None,
                            'currency': ocr_data.currency,
                            'date': ocr_data.date.isoformat() if ocr_data.date else None,
                            'confidence_score': ocr_data.confidence_score
                        }
                    }
                else:
                    # OCR data validation failed
                    receipt.mark_as_failed(f"OCR data validation failed: {', '.join(validation_errors)}")
                    self.receipt_repository.save(receipt)
                    
                    return {
                        'success': False,
                        'error': f"OCR data validation failed: {', '.join(validation_errors)}"
                    }
            else:
                # OCR processing failed
                receipt.mark_as_failed(f"OCR processing failed: {ocr_error}")
                self.receipt_repository.save(receipt)
                
                return {
                    'success': False,
                    'error': f"OCR processing failed: {ocr_error}"
                }
                
        except Exception as e:
            # Mark receipt as failed
            receipt.mark_as_failed(f"OCR processing error: {str(e)}")
            self.receipt_repository.save(receipt)
            
            return {
                'success': False,
                'error': f"OCR processing error: {str(e)}"
            }


class ReceiptListUseCase:
    """Use case for listing user receipts."""
    
    def __init__(self, receipt_repository: ReceiptRepository):
        self.receipt_repository = receipt_repository
    
    def execute(self, 
                user: User,
                status: Optional[ReceiptStatus] = None,
                receipt_type: Optional[ReceiptType] = None,
                limit: int = 50,
                offset: int = 0) -> Dict[str, Any]:
        """
        Execute receipt list use case.
        
        Args:
            user: The user requesting receipts
            status: Filter by receipt status
            receipt_type: Filter by receipt type
            limit: Number of receipts to return
            offset: Number of receipts to skip
            
        Returns:
            Dictionary with receipt list and metadata
        """
        try:
            # Get receipts based on filters
            if status:
                receipts = self.receipt_repository.find_by_status(user, status, limit, offset)
            elif receipt_type:
                receipts = self.receipt_repository.find_by_type(user, receipt_type, limit, offset)
            else:
                receipts = self.receipt_repository.find_by_user(user, limit, offset)
            
            # Convert to response format
            receipt_list = []
            for receipt in receipts:
                receipt_data = {
                    'id': receipt.id,
                    'filename': receipt.file_info.filename,
                    'status': receipt.status.value,
                    'receipt_type': receipt.receipt_type.value,
                    'created_at': receipt.created_at.isoformat(),
                    'updated_at': receipt.updated_at.isoformat(),
                    'file_url': receipt.file_info.file_url
                }
                
                # Add OCR data if available
                if receipt.ocr_data:
                    receipt_data['ocr_data'] = {
                        'merchant_name': receipt.ocr_data.merchant_name,
                        'total_amount': str(receipt.ocr_data.total_amount) if receipt.ocr_data.total_amount else None,
                        'currency': receipt.ocr_data.currency,
                        'date': receipt.ocr_data.date.isoformat() if receipt.ocr_data.date else None,
                        'confidence_score': receipt.ocr_data.confidence_score
                    }
                
                # Add metadata if available
                if receipt.metadata:
                    receipt_data['metadata'] = {
                        'category': receipt.metadata.category,
                        'tags': receipt.metadata.tags,
                        'notes': receipt.metadata.notes,
                        'is_business_expense': receipt.metadata.is_business_expense,
                        'tax_deductible': receipt.metadata.tax_deductible
                    }
                
                receipt_list.append(receipt_data)
            
            # Get total count
            total_count = self.receipt_repository.count_by_user(user)
            
            return {
                'success': True,
                'receipts': receipt_list,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to retrieve receipts: {str(e)}'
            }


class ReceiptDetailUseCase:
    """Use case for getting receipt details."""
    
    def __init__(self, receipt_repository: ReceiptRepository):
        self.receipt_repository = receipt_repository
    
    def execute(self, receipt_id: str, user: User) -> Dict[str, Any]:
        """
        Execute receipt detail use case.
        
        Args:
            receipt_id: ID of the receipt to retrieve
            user: The user requesting the receipt
            
        Returns:
            Dictionary with receipt details
        """
        try:
            # Get receipt by ID
            receipt = self.receipt_repository.find_by_id(receipt_id)
            
            if not receipt:
                return {
                    'success': False,
                    'error': 'Receipt not found'
                }
            
            # Check if user owns the receipt
            if receipt.user.id != user.id:
                return {
                    'success': False,
                    'error': 'Access denied'
                }
            
            # Convert to response format
            receipt_data = {
                'id': receipt.id,
                'filename': receipt.file_info.filename,
                'file_size': receipt.file_info.file_size,
                'mime_type': receipt.file_info.mime_type,
                'file_url': receipt.file_info.file_url,
                'status': receipt.status.value,
                'receipt_type': receipt.receipt_type.value,
                'created_at': receipt.created_at.isoformat(),
                'updated_at': receipt.updated_at.isoformat(),
                'processed_at': receipt.processed_at.isoformat() if receipt.processed_at else None
            }
            
            # Add OCR data if available
            if receipt.ocr_data:
                receipt_data['ocr_data'] = {
                    'merchant_name': receipt.ocr_data.merchant_name,
                    'total_amount': str(receipt.ocr_data.total_amount) if receipt.ocr_data.total_amount else None,
                    'currency': receipt.ocr_data.currency,
                    'date': receipt.ocr_data.date.isoformat() if receipt.ocr_data.date else None,
                    'vat_amount': str(receipt.ocr_data.vat_amount) if receipt.ocr_data.vat_amount else None,
                    'vat_number': receipt.ocr_data.vat_number,
                    'receipt_number': receipt.ocr_data.receipt_number,
                    'items': receipt.ocr_data.items,
                    'confidence_score': receipt.ocr_data.confidence_score,
                    'raw_text': receipt.ocr_data.raw_text
                }
            
            # Add metadata if available
            if receipt.metadata:
                receipt_data['metadata'] = {
                    'category': receipt.metadata.category,
                    'tags': receipt.metadata.tags,
                    'notes': receipt.metadata.notes,
                    'is_business_expense': receipt.metadata.is_business_expense,
                    'tax_deductible': receipt.metadata.tax_deductible,
                    'custom_fields': receipt.metadata.custom_fields
                }
            
            return {
                'success': True,
                'receipt': receipt_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to retrieve receipt: {str(e)}'
            }


class ReceiptUpdateUseCase:
    """Use case for updating receipt metadata."""
    
    def __init__(self, 
                 receipt_repository: ReceiptRepository,
                 receipt_validation_service: ReceiptValidationService):
        self.receipt_repository = receipt_repository
        self.receipt_validation_service = receipt_validation_service
    
    def execute(self, 
                receipt_id: str, 
                user: User, 
                metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute receipt update use case.
        
        Args:
            receipt_id: ID of the receipt to update
            user: The user updating the receipt
            metadata: New metadata to apply
            
        Returns:
            Dictionary with update result
        """
        try:
            # Get receipt by ID
            receipt = self.receipt_repository.find_by_id(receipt_id)
            
            if not receipt:
                return {
                    'success': False,
                    'error': 'Receipt not found'
                }
            
            # Check if user owns the receipt
            if receipt.user.id != user.id:
                return {
                    'success': False,
                    'error': 'Access denied'
                }
            
            # Create new metadata
            new_metadata = ReceiptMetadata(
                category=metadata.get('category'),
                tags=metadata.get('tags', []),
                notes=metadata.get('notes'),
                is_business_expense=metadata.get('is_business_expense', False),
                tax_deductible=metadata.get('tax_deductible', False),
                custom_fields=metadata.get('custom_fields', {})
            )
            
            # Validate metadata
            is_valid, validation_errors = self.receipt_validation_service.validate_metadata(new_metadata)
            
            if not is_valid:
                return {
                    'success': False,
                    'error': 'Metadata validation failed',
                    'validation_errors': validation_errors
                }
            
            # Update receipt metadata
            receipt.update_metadata(new_metadata)
            
            # Save updated receipt
            updated_receipt = self.receipt_repository.save(receipt)
            
            return {
                'success': True,
                'receipt_id': receipt_id,
                'message': 'Receipt updated successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to update receipt: {str(e)}'
            } 