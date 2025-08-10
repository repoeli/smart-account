"""
API views for the Smart Accounts Management System.
Defines REST API endpoints for user management and receipt processing.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils import timezone
import requests
import logging
import uuid

from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, EmailVerificationSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer, UserProfileSerializer,
    ReceiptUploadSerializer, ReceiptUploadResponseSerializer, ReceiptParseResponseSerializer,
    ReceiptReprocessSerializer, ReceiptValidateSerializer, ReceiptCategorizeSerializer,
    ReceiptUpdateSerializer, ReceiptManualCreateSerializer, ReceiptListResponseSerializer,
    ReceiptDetailResponseSerializer, ReceiptStatisticsResponseSerializer,
    ReceiptReprocessResponseSerializer, ReceiptValidateResponseSerializer,
    ReceiptCategorizeResponseSerializer, CreateFolderSerializer, MoveFolderSerializer,
    SearchReceiptsSerializer, AddTagsSerializer, BulkOperationSerializer,
    MoveReceiptsToFolderSerializer, FolderResponseSerializer, SearchResultsSerializer,
    UserStatisticsResponseSerializer, ReceiptSearchRequestSerializer, ReceiptSearchResponseSerializer
)
from infrastructure.ocr.services import OCRService, OCRMethod
from domain.receipts.entities import ReceiptType
from django.conf import settings

logger = logging.getLogger(__name__)

class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Return health status."""
        return Response({
            'status': 'healthy',
            'message': 'Backend is running',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)


class FileInfoView(APIView):
    """
    Diagnostics endpoint to inspect stored files (Cloudinary or local).
    GET /api/v1/files/info?url=<file_url>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        url = request.query_params.get('url')
        if not url:
            return Response({"detail": "url query param is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from infrastructure.storage.services import FileStorageService
            svc = FileStorageService()
            ok, info, err = svc.get_file_info(url)
            if ok:
                return Response({"success": True, "info": info}, status=status.HTTP_200_OK)
            return Response({"success": False, "error": err}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserRegistrationView(APIView):
    """
    API view for user registration.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Register a new user."""
        serializer = UserRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'validation_error',
                    'validation_errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoUserRepository
            from domain.accounts.services import UserDomainService
            from infrastructure.email.services import EmailService
            from application.accounts.use_cases import UserRegistrationUseCase
            
            user_repository = DjangoUserRepository()
            user_domain_service = UserDomainService()
            email_service = EmailService()
            
            # Initialize use case
            registration_use_case = UserRegistrationUseCase(
                user_repository=user_repository,
                user_domain_service=user_domain_service,
                email_service=email_service
            )
            
            # Execute registration
            result = registration_use_case.execute(serializer.validated_data)
            
            # Add success field to match API response format
            response_data = {
                'success': True,
                **result
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'registration_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserLoginView(APIView):
    """
    API view for user login.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Authenticate user and return JWT tokens."""
        serializer = UserLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'validation_error',
                    'validation_errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoUserRepository
            from domain.accounts.services import UserDomainService
            from application.accounts.use_cases import UserLoginUseCase
            
            user_repository = DjangoUserRepository()
            user_domain_service = UserDomainService()
            
            # Initialize use case
            login_use_case = UserLoginUseCase(
                user_repository=user_repository,
                user_domain_service=user_domain_service
            )
            
            # Execute login
            result = login_use_case.execute(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            
            # Add success indicator to response
            response_data = {
                'success': True,
                **result
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'login_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailVerificationView(APIView):
    """
    API view for email verification.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Verify user email with token."""
        serializer = EmailVerificationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'validation_error',
                    'validation_errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoUserRepository
            from domain.accounts.services import UserDomainService
            from application.accounts.use_cases import EmailVerificationUseCase
            
            user_repository = DjangoUserRepository()
            user_domain_service = UserDomainService()
            
            # Initialize use case
            verification_use_case = EmailVerificationUseCase(
                user_repository=user_repository,
                user_domain_service=user_domain_service
            )
            
            # Execute verification
            result = verification_use_case.execute(
                token=serializer.validated_data['token']
            )
            
            return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'verification_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetRequestView(APIView):
    """
    API view for password reset request.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Request password reset."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'validation_error',
                    'validation_errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoUserRepository
            from infrastructure.email.services import EmailService
            from domain.accounts.services import UserDomainService
            
            user_repository = DjangoUserRepository()
            email_service = EmailService()
            user_domain_service = UserDomainService()
            
            # Find user by email
            from domain.common.entities import Email
            email_obj = Email(serializer.validated_data['email'])
            user = user_repository.get_by_email(email_obj.address)
            
            if user:
                # Generate reset token
                reset_token = user_domain_service.generate_verification_token(user)
                
                # Send reset email
                email_service.send_password_reset_email(
                    to_email=user.email.address,
                    user_name=f"{user.first_name} {user.last_name}",
                    reset_token=reset_token
                )
            
            # Always return success for security (don't reveal if email exists)
            return Response({
                'success': True,
                'message': 'If an account with this email exists, a password reset link has been sent.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'password_reset_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetConfirmView(APIView):
    """
    API view for password reset confirmation.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Confirm password reset with token and new password."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'validation_error',
                    'validation_errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoUserRepository
            from domain.accounts.services import UserDomainService, PasswordService
            from django.contrib.auth.hashers import make_password
            
            user_repository = DjangoUserRepository()
            user_domain_service = UserDomainService()
            
            # Validate token and get user
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['password']
            
            # Validate password strength
            password_result = PasswordService.validate_password(new_password)
            if not password_result.is_valid:
                return Response(
                    {
                        'success': False,
                        'error': 'validation_error',
                        'message': f"Invalid password: {'; '.join(password_result.errors)}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # For now, decode token to get user email (simplified)
            # In production, you'd validate the token properly
            try:
                import base64
                import json
                decoded = base64.urlsafe_b64decode(token + '==').decode('utf-8')
                token_data = json.loads(decoded)
                user_email = token_data.get('email')
            except:
                return Response(
                    {
                        'success': False,
                        'error': 'invalid_token',
                        'message': 'Invalid or expired reset token'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find user and update password
            user = user_repository.get_by_email(user_email)
            if not user:
                return Response(
                    {
                        'success': False,
                        'error': 'invalid_token',
                        'message': 'Invalid or expired reset token'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update password
            user._password_hash = make_password(new_password)
            user_repository.save(user)
            
            return Response({
                'success': True,
                'message': 'Password has been reset successfully. You can now login with your new password.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'password_reset_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileView(APIView):
    """
    API view for user profile management.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user profile."""
        try:
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoUserRepository
            from application.accounts.use_cases import UserProfileUseCase
            
            user_repository = DjangoUserRepository()
            
            # Initialize use case
            profile_use_case = UserProfileUseCase(user_repository=user_repository)
            
            # Execute get profile
            result = profile_use_case.get_profile(user_id=request.user.id)
            
            return Response({'success': True, **result}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'profile_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request):
        """Update user profile."""
        serializer = UserProfileSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'validation_error',
                    'validation_errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoUserRepository
            from application.accounts.use_cases import UserProfileUseCase
            
            user_repository = DjangoUserRepository()
            
            # Initialize use case
            profile_use_case = UserProfileUseCase(user_repository=user_repository)
            
            # Execute update profile
            result = profile_use_case.update_profile(
                user_id=request.user.id,
                profile_data=serializer.validated_data
            )
            
            return Response({'success': True, **result}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'profile_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReceiptUploadView(APIView):
    """
    API view for receipt upload.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Upload a receipt."""
        serializer = ReceiptUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'validation_error',
                    'validation_errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get file data
            uploaded_file = serializer.validated_data['file']
            receipt_type = serializer.validated_data['receipt_type']
            ocr_method_param = serializer.validated_data.get('ocr_method', 'auto')
            
            # Read file data
            file_data = uploaded_file.read()
            filename = uploaded_file.name
            mime_type = uploaded_file.content_type
            
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoReceiptRepository
            from domain.receipts.services import FileValidationService, ReceiptBusinessService
            from infrastructure.storage.services import FileStorageService
            from infrastructure.ocr.services import OCRService, OCRMethod
            from application.receipts.use_cases import ReceiptUploadUseCase
            
            receipt_repository = DjangoReceiptRepository()
            file_validation_service = FileValidationService()
            file_storage_service = FileStorageService()
            ocr_service = OCRService()
            receipt_business_service = ReceiptBusinessService()
            
            # Initialize use case
            upload_use_case = ReceiptUploadUseCase(
                receipt_repository=receipt_repository,
                file_validation_service=file_validation_service,
                file_storage_service=file_storage_service,
                ocr_service=ocr_service,
                receipt_business_service=receipt_business_service
            )
            
            # Convert receipt type to enum
            from domain.receipts.entities import ReceiptType
            receipt_type_enum = ReceiptType(receipt_type)
            
            # Convert OCR method to enum
            ocr_method_enum = None
            if ocr_method_param == 'paddle_ocr':
                ocr_method_enum = OCRMethod.PADDLE_OCR
            elif ocr_method_param == 'openai_vision':
                ocr_method_enum = OCRMethod.OPENAI_VISION
            elif ocr_method_param == 'auto':
                ocr_method_enum = None  # Use default/preferred method
            
            # Execute upload use case
            result = upload_use_case.execute(
                user=request.user,
                file_data=file_data,
                filename=filename,
                mime_type=mime_type,
                receipt_type=receipt_type_enum,
                ocr_method=ocr_method_enum
            )
            
            # Return response
            response_serializer = ReceiptUploadResponseSerializer(data=result)
            response_serializer.is_valid()
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED if result['success'] else status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'upload_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReceiptManualCreateView(APIView):
    """Create a receipt manually without OCR. Optional Cloudinary upload when file_url provided.
    Aligns with docs US-006 for manual entry.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from infrastructure.database.repositories import DjangoReceiptRepository
        from domain.receipts.services import FileValidationService
        from infrastructure.storage.services import FileStorageService
        from domain.receipts.entities import Receipt as DomainReceipt, ReceiptStatus, OCRData, FileInfo
        serializer = ReceiptManualCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'success': False, 'error': 'validation_error', 'validation_errors': serializer.errors}, status=400)

        data = serializer.validated_data
        upload_to_cloud = bool(data.get('upload_to_cloudinary'))
        provided_url = data.get('file_url')
        uploaded_file = request.FILES.get('file')
        filename = data.get('filename') or (uploaded_file.name if uploaded_file else 'manual.jpg')
        mime_type = data.get('mime_type') or (uploaded_file.content_type if uploaded_file else 'image/jpeg')

        file_url = provided_url
        cloudinary_public_id = None
        storage_provider = None

        try:
            if uploaded_file:
                file_bytes = uploaded_file.read()
                if upload_to_cloud:
                    from infrastructure.storage.adapters.cloudinary_store import CloudinaryStorageAdapter
                    cloud = CloudinaryStorageAdapter()
                    asset = cloud.upload(file_bytes=file_bytes, filename=filename, mime=mime_type)
                    file_url = asset.secure_url
                    storage_provider = 'cloudinary'
                    cloudinary_public_id = asset.public_id
                else:
                    # local storage fallback
                    storage_service = FileStorageService()
                    ok, url, _err = storage_service.upload_file_from_memory(file_bytes, filename)
                    if ok:
                        file_url = url
                        storage_provider = 'local'
            elif provided_url and upload_to_cloud and 'res.cloudinary.com' not in provided_url:
                # migrate external URL to Cloudinary
                resp = requests.get(provided_url, timeout=30)
                resp.raise_for_status()
                from infrastructure.storage.adapters.cloudinary_store import CloudinaryStorageAdapter
                cloud = CloudinaryStorageAdapter()
                asset = cloud.upload(file_bytes=resp.content, filename=filename, mime=mime_type)
                file_url = asset.secure_url
                storage_provider = 'cloudinary'
                cloudinary_public_id = asset.public_id
        except Exception:
            pass

        # Build receipt directly (no OCR)
        try:
            repo = DjangoReceiptRepository()
            file_validation = FileValidationService()
            if not file_url:
                # If no URL is available, create a synthetic local file URL for tracking
                file_url = getattr(settings, 'PUBLIC_BASE_URL', 'http://127.0.0.1:8000') + '/media/receipts/placeholder.jpg'

            fi: FileInfo = file_validation.get_file_info(filename, 0, mime_type, file_url)
            receipt = DomainReceipt(
                id=str(uuid.uuid4()),
                user=request.user,
                file_info=fi,
                status=ReceiptStatus.PROCESSED if any([data.get('merchant_name'), data.get('total_amount'), data.get('date')]) else ReceiptStatus.UPLOADED,
                receipt_type=ReceiptType(data.get('receipt_type') or 'purchase'),
            )
            # telemetry
            try:
                if storage_provider:
                    receipt.metadata.custom_fields['storage_provider'] = storage_provider
                if cloudinary_public_id:
                    receipt.metadata.custom_fields['cloudinary_public_id'] = cloudinary_public_id
            except Exception:
                pass

            # manual OCR fields
            if any([data.get('merchant_name'), data.get('total_amount'), data.get('date')]):
                receipt.ocr_data = OCRData(
                    merchant_name=data.get('merchant_name') or '',
                    total_amount=None,
                    currency=data.get('currency') or 'GBP',
                    date=None,
                    confidence_score=1.0,
                )
            if receipt.metadata and data.get('notes'):
                receipt.metadata.notes = data.get('notes')

            saved = repo.save(receipt)
            return Response({'success': True, 'receipt_id': saved.id, 'file_url': saved.file_info.file_url}, status=200)
        except Exception as e:
            return Response({'success': False, 'error': 'manual_create_error', 'message': str(e)}, status=500)


class ReceiptParseView(APIView):
    """
    POST /api/v1/receipts/parse?engine=paddle|openai&source=file|url
    - If source=file: multipart upload, stored to Cloudinary first
    - If source=url: JSON body {"url": "..."}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            engine = request.query_params.get('engine', getattr(settings, 'OCR_ENGINE_DEFAULT', 'paddle'))
            source = request.query_params.get('source', 'file')

            # Prepare providers
            from application.receipts.ports import OCRProvider
            from infrastructure.storage.adapters.cloudinary_store import CloudinaryStorageAdapter
            from infrastructure.ocr.adapters.paddle_http import PaddleOCRHTTPAdapter
            from infrastructure.ocr.adapters.openai_vision import OpenAIVisionAdapter

            storage = CloudinaryStorageAdapter()

            def call_provider(provider: OCRProvider, *, file_bytes=None, url=None, filename: str = None):
                options = {"filename": filename} if filename else {}
                return provider.parse_receipt(file_bytes=file_bytes, url=url, options=options)

            # Handle input
            if source == 'file':
                if 'file' not in request.FILES:
                    return Response({"detail": "file is required"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                f = request.FILES['file']
                if f.size > getattr(settings, 'MAX_RECEIPT_MB', 10) * 1024 * 1024:
                    return Response({"detail": "File too large"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                file_bytes = f.read()
                filename = f.name
                if engine == 'openai':
                    provider = OpenAIVisionAdapter(storage=storage)
                    extraction = call_provider(provider, file_bytes=file_bytes, filename=filename)
                else:
                    provider = PaddleOCRHTTPAdapter()
                    extraction = call_provider(provider, file_bytes=file_bytes, filename=filename)
            else:
                data = request.data or {}
                url = data.get('url')
                if not url:
                    return Response({"detail": "url is required"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                if engine == 'openai':
                    provider = OpenAIVisionAdapter(storage=storage)
                    extraction = call_provider(provider, url=url)
                else:
                    provider = PaddleOCRHTTPAdapter()
                    extraction = call_provider(provider, url=url)

            # Uniform response
            from .serializers import ReceiptParseResponseSerializer
            ser = ReceiptParseResponseSerializer(extraction.model_dump())
            return Response(ser.data, status=status.HTTP_200_OK)

        except requests.Timeout:
            return Response({"detail": "OCR provider timeout"}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except Exception as e:
            # Optional fallback
            if engine == 'openai' and getattr(settings, 'FALLBACK_TO_PADDLE', True):
                try:
                    from infrastructure.ocr.adapters.paddle_http import PaddleOCRHTTPAdapter
                    provider = PaddleOCRHTTPAdapter()
                    if source == 'file' and 'file' in request.FILES:
                        f = request.FILES['file']
                        extraction = provider.parse_receipt(file_bytes=f.read(), options={"filename": f.name})
                    else:
                        extraction = provider.parse_receipt(url=(request.data or {}).get('url'))
                    from .serializers import ReceiptParseResponseSerializer
                    ser = ReceiptParseResponseSerializer(extraction.model_dump())
                    return Response(ser.data, status=status.HTTP_200_OK)
                except Exception:
                    pass
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReceiptReprocessView(APIView):
    """
    API view for receipt reprocessing.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, receipt_id):
        """Reprocess a receipt with different OCR method."""
        serializer = ReceiptReprocessSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'validation_error',
                    'validation_errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get OCR method
            ocr_method_param = serializer.validated_data['ocr_method']
            
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoReceiptRepository
            from domain.receipts.services import ReceiptBusinessService, ReceiptValidationService
            from infrastructure.ocr.services import OCRService, OCRMethod
            from application.receipts.use_cases import ReceiptReprocessUseCase
            
            receipt_repository = DjangoReceiptRepository()
            ocr_service = OCRService()
            receipt_business_service = ReceiptBusinessService()
            receipt_validation_service = ReceiptValidationService()
            
            # Initialize use case
            reprocess_use_case = ReceiptReprocessUseCase(
                receipt_repository=receipt_repository,
                ocr_service=ocr_service,
                receipt_business_service=receipt_business_service,
                receipt_validation_service=receipt_validation_service
            )
            
            # Convert OCR method to enum
            ocr_method_enum = None
            if ocr_method_param == 'paddle_ocr':
                ocr_method_enum = OCRMethod.PADDLE_OCR
            elif ocr_method_param == 'openai_vision':
                ocr_method_enum = OCRMethod.OPENAI_VISION
            elif ocr_method_param == 'auto':
                ocr_method_enum = None  # Use default/preferred method
            
            # Execute reprocess use case
            result = reprocess_use_case.execute(
                receipt_id=receipt_id,
                user=request.user,
                ocr_method=ocr_method_enum
            )
            
            # Return response
            response_serializer = ReceiptReprocessResponseSerializer(data=result)
            response_serializer.is_valid()
            
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'reprocess_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReceiptValidateView(APIView):
    """
    API view for receipt validation and correction.
    """
    permission_classes = [IsAuthenticated]
    
    def put(self, request, receipt_id):
        """Validate and correct receipt data."""
        serializer = ReceiptValidateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'validation_error',
                    'validation_errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoReceiptRepository
            from domain.receipts.services import ReceiptValidationService, ReceiptDataEnrichmentService
            from application.receipts.use_cases import ReceiptValidateUseCase
            from infrastructure.database.models import UserAuditLog
            
            receipt_repository = DjangoReceiptRepository()
            receipt_validation_service = ReceiptValidationService()
            receipt_enrichment_service = ReceiptDataEnrichmentService()
            
            # Initialize use case
            validate_use_case = ReceiptValidateUseCase(
                receipt_repository=receipt_repository,
                receipt_validation_service=receipt_validation_service,
                receipt_enrichment_service=receipt_enrichment_service
            )
            
            # Execute validation use case
            result = validate_use_case.execute(
                receipt_id=receipt_id,
                user=request.user,
                corrections=serializer.validated_data
            )
            
            # Return response
            response_serializer = ReceiptValidateResponseSerializer(data=result)
            response_serializer.is_valid()

            # Audit log for validation/edit
            try:
                UserAuditLog.objects.create(
                    user=request.user,
                    event_type='receipt_validate',
                    event_data={
                        'receipt_id': str(receipt_id),
                        'corrections': serializer.validated_data,
                        'result': response_serializer.data,
                    },
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )
            except Exception:
                pass
            
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'validation_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReceiptCategorizeView(APIView):
    """
    API view for receipt categorization.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, receipt_id):
        """Auto-categorize a receipt."""
        serializer = ReceiptCategorizeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'validation_error',
                    'validation_errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoReceiptRepository
            from domain.receipts.services import ReceiptBusinessService, ReceiptDataEnrichmentService
            from application.receipts.use_cases import ReceiptCategorizeUseCase
            
            receipt_repository = DjangoReceiptRepository()
            receipt_business_service = ReceiptBusinessService()
            receipt_enrichment_service = ReceiptDataEnrichmentService()
            
            # Initialize use case
            categorize_use_case = ReceiptCategorizeUseCase(
                receipt_repository=receipt_repository,
                receipt_business_service=receipt_business_service,
                receipt_enrichment_service=receipt_enrichment_service
            )
            
            # Execute categorization use case
            result = categorize_use_case.execute(
                receipt_id=receipt_id,
                user=request.user
            )
            
            # Return response
            response_serializer = ReceiptCategorizeResponseSerializer(data=result)
            response_serializer.is_valid()
            
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'categorization_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReceiptStatisticsView(APIView):
    """
    API view for receipt statistics.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get receipt processing statistics."""
        try:
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoReceiptRepository
            from application.receipts.use_cases import ReceiptStatisticsUseCase
            
            receipt_repository = DjangoReceiptRepository()
            
            # Initialize use case
            statistics_use_case = ReceiptStatisticsUseCase(receipt_repository=receipt_repository)
            
            # Execute statistics use case
            result = statistics_use_case.execute(user=request.user)
            
            # Return response
            response_serializer = ReceiptStatisticsResponseSerializer(data=result)
            response_serializer.is_valid()
            
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'statistics_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReceiptListView(APIView):
    """
    API view for listing receipts with enhanced search and cursor pagination.
    Supports both legacy offset pagination and new cursor-based pagination.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List user receipts with optional filtering, search, and cursor pagination."""
        try:
            # Check if this is a search request (has search parameters)
            if self._is_search_request(request):
                return self._handle_search_request(request)
            else:
                return self._handle_legacy_request(request)
                
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'list_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _is_search_request(self, request):
        """Check if this request has search parameters."""
        search_params = ['q', 'status', 'currency', 'provider', 'dateFrom', 'dateTo', 
                        'amountMin', 'amountMax', 'confidenceMin', 'sort', 'order', 'cursor']
        return any(request.query_params.get(param) for param in search_params)
    
    def _handle_legacy_request(self, request):
        """Handle legacy offset-based pagination request."""
        # Get query parameters
        status_param = request.query_params.get('status')
        receipt_type_param = request.query_params.get('receipt_type')
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        # Initialize dependencies
        from infrastructure.database.repositories import DjangoReceiptRepository
        from application.receipts.use_cases import ReceiptListUseCase
        from domain.receipts.entities import ReceiptStatus, ReceiptType
        
        receipt_repository = DjangoReceiptRepository()
        
        # Initialize use case
        list_use_case = ReceiptListUseCase(receipt_repository=receipt_repository)
        
        # Convert parameters to enums
        status_enum = ReceiptStatus(status_param) if status_param else None
        receipt_type_enum = ReceiptType(receipt_type_param) if receipt_type_param else None
        
        # Execute list use case
        result = list_use_case.execute(
            user=request.user,
            status=status_enum,
            receipt_type=receipt_type_enum,
            limit=limit,
            offset=offset
        )
        
        # Return response
        response_serializer = ReceiptListResponseSerializer(data=result)
        response_serializer.is_valid()
        
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
        )
    
    def _handle_search_request(self, request):
        """Handle search request with cursor pagination."""
        try:
            # Validate request parameters
            serializer = ReceiptSearchRequestSerializer(data=request.query_params)
            if not serializer.is_valid():
                return Response(
                    {
                        'success': False,
                        'error': 'validation_error',
                        'message': 'Invalid parameters',
                        'details': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            params = serializer.validated_data

            # Enforce account scope: provided accountId must match the authenticated user id
            if str(params.get('accountId')) != str(request.user.id):
                return Response(
                    {
                        'success': False,
                        'error': 'forbidden',
                        'message': 'accountId does not match the current user'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Initialize dependencies
            from infrastructure.pagination.cursor import CursorPagination
            
            # Build search filters
            filters = self._build_search_filters(params)
            
            # Handle cursor pagination
            cursor_info = None
            if params.get('cursor'):
                try:
                    cursor_info = CursorPagination.decode_cursor(params['cursor'])
                except ValueError as e:
                    return Response(
                        {
                            'success': False,
                            'error': 'invalid_cursor',
                            'message': f'Invalid cursor: {str(e)}'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Execute search with cursor pagination
            result = self._execute_search(
                user=request.user,
                filters=filters,
                sort=params['sort'],
                order=params['order'],
                limit=params['limit'],
                cursor_info=cursor_info
            )
            
            # Build response
            response_data = self._build_response(result, params, cursor_info)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'search_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _build_search_filters(self, params):
        """Build search filters from request parameters."""
        filters = {}
        
        # Search query
        if params.get('q'):
            filters['search_query'] = params['q']
        
        # Status filter
        if params.get('status'):
            filters['statuses'] = [s.strip() for s in params['status'].split(',')]
        
        # Currency filter
        if params.get('currency'):
            filters['currencies'] = [c.strip() for c in params['currency'].split(',')]
        
        # Provider filter
        if params.get('provider'):
            filters['providers'] = [p.strip() for p in params['provider'].split(',')]
        
        # Date range
        if params.get('dateFrom'):
            filters['date_from'] = params['dateFrom']
        if params.get('dateTo'):
            filters['date_to'] = params['dateTo']
        
        # Amount range
        if params.get('amountMin'):
            filters['amount_min'] = params['amountMin']
        if params.get('amountMax'):
            filters['amount_max'] = params['amountMax']
        
        # Confidence filter
        if params.get('confidenceMin'):
            filters['confidence_min'] = params['confidenceMin']
        
        return filters
    
    def _execute_search(self, user, filters, sort, order, limit, cursor_info):
        """Execute the search query with cursor pagination."""
        from django.db import connection
        from infrastructure.database.models import Receipt

        if connection.vendor != 'postgresql':
            # Fallback path for SQLite or other backends that don't support JSON key transforms reliably
            base_qs = Receipt.objects.filter(user_id=user.id)
            # Sort order first (created_at only for fallback)
            base_qs = base_qs.order_by('-created_at', '-id') if order == 'desc' else base_qs.order_by('created_at', 'id')

            # Materialize then filter in Python (acceptable for dev/small datasets)
            all_items = list(base_qs)

            def text_contains(val, needle):
                if not val:
                    return False
                try:
                    return needle.lower() in str(val).lower()
                except Exception:
                    return False

            # Apply filters in Python
            q = filters.get('search_query')
            if q:
                all_items = [r for r in all_items if (
                    text_contains((r.ocr_data or {}).get('merchant_name'), q)
                    or text_contains((r.metadata or {}).get('notes'), q)
                    or text_contains((r.ocr_data or {}).get('receipt_number'), q)
                )]

            if filters.get('statuses'):
                allowed = set(filters['statuses'])
                all_items = [r for r in all_items if r.status in allowed]

            if filters.get('currencies'):
                allowed = set(filters['currencies'])
                all_items = [r for r in all_items if (r.ocr_data or {}).get('currency') in allowed]

            if filters.get('providers'):
                allowed = set(filters['providers'])
                all_items = [r for r in all_items if ((r.metadata or {}).get('custom_fields') or {}).get('storage_provider') in allowed]

            if filters.get('date_from'):
                all_items = [r for r in all_items if r.created_at.date() >= filters['date_from']]
            if filters.get('date_to'):
                all_items = [r for r in all_items if r.created_at.date() <= filters['date_to']]

            def to_decimal(v):
                try:
                    return float(v)
                except Exception:
                    return None

            if filters.get('amount_min'):
                mn = to_decimal(filters['amount_min'])
                if mn is not None:
                    all_items = [r for r in all_items if to_decimal((r.ocr_data or {}).get('total_amount')) is not None and to_decimal((r.ocr_data or {}).get('total_amount')) >= mn]
            if filters.get('amount_max'):
                mx = to_decimal(filters['amount_max'])
                if mx is not None:
                    all_items = [r for r in all_items if to_decimal((r.ocr_data or {}).get('total_amount')) is not None and to_decimal((r.ocr_data or {}).get('total_amount')) <= mx]

            if filters.get('confidence_min'):
                mn = to_decimal(filters['confidence_min'])
                if mn is not None:
                    all_items = [r for r in all_items if to_decimal((r.ocr_data or {}).get('confidence_score')) is not None and to_decimal((r.ocr_data or {}).get('confidence_score')) >= mn]

            # Cursor - fallback: use created_at/id only when a cursor is present
            if cursor_info:
                key_val, key_id = cursor_info.key
                from datetime import datetime, date
                if isinstance(key_val, str):
                    try:
                        key_date = datetime.fromisoformat(key_val).date()
                    except Exception:
                        key_date = None
                elif isinstance(key_val, (datetime, date)):
                    key_date = key_val if isinstance(key_val, date) else key_val.date()
                else:
                    key_date = None

                def cmp_before(r):
                    if key_date is None:
                        return True
                    return (r.created_at.date(), str(r.id)) < (key_date, key_id) if cursor_info.order == 'desc' else (r.created_at.date(), str(r.id)) > (key_date, key_id)

                all_items = [r for r in all_items if cmp_before(r)]

            # Slice +1 to detect next
            results = all_items[: limit + 1]
            has_next = len(results) > limit
            if has_next:
                results = results[:-1]

            return {
                'receipts': results,
                'has_next': has_next,
                'has_prev': cursor_info is not None,
                'total_count': None,
            }

        # PostgreSQL optimized path with safe fallback on error
        try:
            queryset = Receipt.objects.filter(user_id=user.id)
            queryset = self._apply_filters(queryset, filters)
            if cursor_info:
                queryset = self._apply_cursor_pagination(queryset, cursor_info, sort)
            queryset = self._apply_sorting(queryset, sort, order)
            results = list(queryset[: limit + 1])
            has_next = len(results) > limit
            if has_next:
                results = results[:-1]
            return {
                'receipts': results,
                'has_next': has_next,
                'has_prev': cursor_info is not None,
                'total_count': None,
            }
        except Exception as e:
            # Log and fallback to Python evaluation to avoid 500s in development
            import logging
            logging.getLogger(__name__).exception("Search PG path failed; falling back to safe path: %s", e)
            return self._execute_search(user, filters, sort, order, limit, cursor_info=None)
    
    def _apply_filters(self, queryset, filters):
        """Apply search filters to the queryset."""
        from django.db import connection
        from django.db.models import Q, DecimalField, FloatField, DateField
        from django.db.models.functions import Cast
        is_pg = connection.vendor == 'postgresql'
        KeyTextTransform = None
        if is_pg:
            try:
                # Modern Django
                from django.db.models.fields.json import KeyTextTransform as _KTT  # type: ignore
                KeyTextTransform = _KTT
            except Exception:
                try:
                    # Older Django (Postgres contrib)
                    from django.contrib.postgres.fields.jsonb import KeyTextTransform as _KTT  # type: ignore
                    KeyTextTransform = _KTT
                except Exception:
                    is_pg = False
        
        # Search query across merchant, notes, receipt_number
        if filters.get('search_query'):
            search_query = filters['search_query']
            queryset = queryset.filter(
                Q(ocr_data__merchant_name__icontains=search_query)
                | Q(metadata__notes__icontains=search_query)
                | Q(ocr_data__receipt_number__icontains=search_query)
            )
        
        # Status filter
        if filters.get('statuses'):
            queryset = queryset.filter(status__in=filters['statuses'])
        
        # Currency filter
        if filters.get('currencies'):
            queryset = queryset.filter(ocr_data__currency__in=filters['currencies'])
        
        # Provider filter
        if filters.get('providers'):
            queryset = queryset.filter(metadata__custom_fields__storage_provider__in=filters['providers'])
        
        # Date range: fall back to created_at date to avoid casting arbitrary text dates in JSON
        if filters.get('date_from'):
            queryset = queryset.filter(created_at__date__gte=filters['date_from'])
        if filters.get('date_to'):
            queryset = queryset.filter(created_at__date__lte=filters['date_to'])
        
        # Amount range (cast JSON text to numeric when supported)
        if filters.get('amount_min'):
            if is_pg and KeyTextTransform:
                queryset = queryset.annotate(
                    _amt_val=Cast(
                        KeyTextTransform('total_amount', 'ocr_data'),
                        output_field=DecimalField(max_digits=12, decimal_places=2),
                    )
                ).filter(
                    _amt_val__gte=filters['amount_min']
                )
            else:
                # Best-effort on non-PG: try direct filter (may be lexicographic)
                queryset = queryset.filter(ocr_data__total_amount__gte=str(filters['amount_min']))
        if filters.get('amount_max'):
            if is_pg and KeyTextTransform:
                queryset = queryset.annotate(
                    _amt_val=Cast(
                        KeyTextTransform('total_amount', 'ocr_data'),
                        output_field=DecimalField(max_digits=12, decimal_places=2),
                    )
                ).filter(
                    _amt_val__lte=filters['amount_max']
                )
            else:
                queryset = queryset.filter(ocr_data__total_amount__lte=str(filters['amount_max']))
        
        # Confidence filter (cast JSON text to float when supported)
        if filters.get('confidence_min'):
            if is_pg and KeyTextTransform:
                queryset = queryset.annotate(
                    _conf_val=Cast(KeyTextTransform('confidence_score', 'ocr_data'), output_field=FloatField())
                ).filter(
                    _conf_val__gte=filters['confidence_min']
                )
            else:
                queryset = queryset.filter(ocr_data__confidence_score__gte=str(filters['confidence_min']))
        
        return queryset
    
    def _apply_cursor_pagination(self, queryset, cursor_info, sort):
        """Apply cursor-based pagination to the queryset."""
        from django.db import connection
        from django.db.models import Q, DecimalField, FloatField, DateField, F
        from django.db.models.functions import Cast
        is_pg = connection.vendor == 'postgresql'
        KeyTextTransform = None
        if is_pg:
            try:
                from django.db.models.fields.json import KeyTextTransform as _KTT  # type: ignore
                KeyTextTransform = _KTT
            except Exception:
                try:
                    from django.contrib.postgres.fields.jsonb import KeyTextTransform as _KTT  # type: ignore
                    KeyTextTransform = _KTT
                except Exception:
                    is_pg = False
        if cursor_info.order == 'desc':
            # For descending order, get rows with (sort_value, id) < (cursor_sort_value, cursor_id)
            if sort == 'date':
                # Compare directly on created_at date for robustness
                queryset = queryset.filter(
                    Q(created_at__date__lt=cursor_info.key[0]) | (Q(created_at__date=cursor_info.key[0]) & Q(id__lt=cursor_info.key[1]))
                )
            elif sort == 'amount' and is_pg and KeyTextTransform:
                sort_val = Cast(
                    KeyTextTransform('total_amount', 'ocr_data'),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
                queryset = queryset.annotate(_sort_val=sort_val).filter(
                    Q(_sort_val__lt=cursor_info.key[0]) | (Q(_sort_val=cursor_info.key[0]) & Q(id__lt=cursor_info.key[1]))
                )
            elif sort == 'merchant' and is_pg and KeyTextTransform:
                queryset = queryset.annotate(_sort_val=KeyTextTransform('merchant_name', 'ocr_data')).filter(
                    Q(_sort_val__lt=cursor_info.key[0]) | (Q(_sort_val=cursor_info.key[0]) & Q(id__lt=cursor_info.key[1]))
                )
            elif sort == 'confidence' and is_pg and KeyTextTransform:
                sort_val = Cast(KeyTextTransform('confidence_score', 'ocr_data'), output_field=FloatField())
                queryset = queryset.annotate(_sort_val=sort_val).filter(
                    Q(_sort_val__lt=cursor_info.key[0]) | (Q(_sort_val=cursor_info.key[0]) & Q(id__lt=cursor_info.key[1]))
                )
        else:
            # For ascending order, get rows with (sort_value, id) > (cursor_sort_value, cursor_id)
            if sort == 'date':
                queryset = queryset.filter(
                    Q(created_at__date__gt=cursor_info.key[0]) | (Q(created_at__date=cursor_info.key[0]) & Q(id__gt=cursor_info.key[1]))
                )
            elif sort == 'amount' and is_pg and KeyTextTransform:
                sort_val = Cast(
                    KeyTextTransform('total_amount', 'ocr_data'),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
                queryset = queryset.annotate(_sort_val=sort_val).filter(
                    Q(_sort_val__gt=cursor_info.key[0]) | (Q(_sort_val=cursor_info.key[0]) & Q(id__gt=cursor_info.key[1]))
                )
            elif sort == 'merchant' and is_pg and KeyTextTransform:
                queryset = queryset.annotate(_sort_val=KeyTextTransform('merchant_name', 'ocr_data')).filter(
                    Q(_sort_val__gt=cursor_info.key[0]) | (Q(_sort_val=cursor_info.key[0]) & Q(id__gt=cursor_info.key[1]))
                )
            elif sort == 'confidence' and is_pg and KeyTextTransform:
                sort_val = Cast(KeyTextTransform('confidence_score', 'ocr_data'), output_field=FloatField())
                queryset = queryset.annotate(_sort_val=sort_val).filter(
                    Q(_sort_val__gt=cursor_info.key[0]) | (Q(_sort_val=cursor_info.key[0]) & Q(id__gt=cursor_info.key[1]))
                )
        
        return queryset
    
    def _apply_sorting(self, queryset, sort, order):
        """Apply sorting to the queryset."""
        from django.db import connection
        from django.db.models import DecimalField, FloatField, DateField, F
        from django.db.models.functions import Cast
        is_pg = connection.vendor == 'postgresql'
        KeyTextTransform = None
        if is_pg:
            try:
                from django.db.models.fields.json import KeyTextTransform as _KTT  # type: ignore
                KeyTextTransform = _KTT
            except Exception:
                try:
                    from django.contrib.postgres.fields.jsonb import KeyTextTransform as _KTT  # type: ignore
                    KeyTextTransform = _KTT
                except Exception:
                    is_pg = False
        if sort == 'date':
            # order directly on created_at for maximum compatibility
            if order == 'desc':
                return queryset.order_by('-created_at', '-id')
            return queryset.order_by('created_at', 'id')
        elif sort == 'amount' and is_pg and KeyTextTransform:
            sort_val = Cast(
                KeyTextTransform('total_amount', 'ocr_data'),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        elif sort == 'confidence' and is_pg and KeyTextTransform:
            sort_val = Cast(KeyTextTransform('confidence_score', 'ocr_data'), output_field=FloatField())
        elif sort == 'merchant' and is_pg and KeyTextTransform:
            sort_val = KeyTextTransform('merchant_name', 'ocr_data')
        else:
            # Fallback for non-postgres or unsupported sort fields
            sort_val = Cast(F('created_at'), output_field=DateField())

        queryset = queryset.annotate(_sort_val=sort_val)
        if order == 'desc':
            queryset = queryset.order_by('-_sort_val', '-id')
        else:
            queryset = queryset.order_by('_sort_val', 'id')
        
        return queryset
    
    def _build_response(self, result, params, cursor_info):
        """Build the API response with cursor pagination."""
        from infrastructure.pagination.cursor import CursorPagination
        
        # Transform receipts to API format
        items = []
        for receipt in result['receipts']:
            items.append({
                'id': str(receipt.id),
                'merchant': receipt.ocr_data.get('merchant_name', '') if receipt.ocr_data else '',
                'date': receipt.ocr_data.get('date', '') if receipt.ocr_data else '',
                'amount': float(receipt.ocr_data.get('total_amount', 0)) if receipt.ocr_data else 0,
                'currency': receipt.ocr_data.get('currency', 'GBP') if receipt.ocr_data else 'GBP',
                'status': receipt.status,
                'confidence': receipt.ocr_data.get('confidence_score', 0) if receipt.ocr_data else 0,
                'provider': receipt.metadata.get('custom_fields', {}).get('storage_provider', '') if receipt.metadata else '',
                'thumbnailUrl': receipt.file_url
            })
        
        # Build pagination info
        page_info = {
            'nextCursor': None,
            'prevCursor': None,
            'hasNext': result['has_next'],
            'hasPrev': result['has_prev']
        }
        
        # Generate next cursor if there are more results
        if result['has_next'] and result['receipts']:
            last_receipt = result['receipts'][-1]
            sort_value = self._get_sort_value(last_receipt, params['sort'])
            page_info['nextCursor'] = CursorPagination.encode_cursor(
                sort=params['sort'],
                order=params['order'],
                sort_value=sort_value,
                receipt_id=str(last_receipt.id)
            )
        
        # Generate previous cursor if we have a current cursor
        if cursor_info and result['receipts']:
            first_receipt = result['receipts'][0]
            sort_value = self._get_sort_value(first_receipt, params['sort'])
            page_info['prevCursor'] = CursorPagination.encode_cursor(
                sort=params['sort'],
                order=params['order'],
                sort_value=sort_value,
                receipt_id=str(first_receipt.id)
            )
        
        return {
            'items': items,
            'pageInfo': page_info,
            'totalCount': result['total_count']
        }
    
    def _get_sort_value(self, receipt, sort_field):
        """Get the sort value for a receipt based on the sort field."""
        if sort_field == 'date':
            return receipt.ocr_data.get('date') if receipt.ocr_data else None
        elif sort_field == 'amount':
            return receipt.ocr_data.get('total_amount') if receipt.ocr_data else 0
        elif sort_field == 'merchant':
            return receipt.ocr_data.get('merchant_name') if receipt.ocr_data else ''
        elif sort_field == 'confidence':
            return receipt.ocr_data.get('confidence_score') if receipt.ocr_data else 0
        return None


class ReceiptDetailView(APIView):
    """
    API view for receipt details.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, receipt_id):
        """Get receipt details."""
        try:
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoReceiptRepository
            from application.receipts.use_cases import ReceiptDetailUseCase
            
            receipt_repository = DjangoReceiptRepository()
            
            # Initialize use case
            detail_use_case = ReceiptDetailUseCase(receipt_repository=receipt_repository)
            
            # Execute detail use case
            result = detail_use_case.execute(
                receipt_id=receipt_id,
                user=request.user
            )
            
            # Return response
            response_serializer = ReceiptDetailResponseSerializer(data=result)
            response_serializer.is_valid()
            
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'detail_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReceiptUpdateView(APIView):
    """
    API view for updating receipt metadata.
    """
    permission_classes = [IsAuthenticated]
    
    def put(self, request, receipt_id):
        """Update receipt metadata."""
        serializer = ReceiptUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'validation_error',
                    'validation_errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoReceiptRepository
            from domain.receipts.services import ReceiptValidationService
            from application.receipts.use_cases import ReceiptUpdateUseCase
            from infrastructure.database.models import UserAuditLog
            
            receipt_repository = DjangoReceiptRepository()
            receipt_validation_service = ReceiptValidationService()
            
            # Initialize use case
            update_use_case = ReceiptUpdateUseCase(
                receipt_repository=receipt_repository,
                receipt_validation_service=receipt_validation_service
            )
            
            # Execute update use case
            result = update_use_case.execute(
                receipt_id=receipt_id,
                user=request.user,
                metadata=serializer.validated_data
            )
            
            try:
                UserAuditLog.objects.create(
                    user=request.user,
                    event_type='receipt_update',
                    event_data={
                        'receipt_id': str(receipt_id),
                        'metadata': serializer.validated_data,
                        'result': result,
                    },
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )
            except Exception:
                pass

            return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'update_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 


class ReceiptSearchView(APIView):
    """
    Enhanced API view for searching receipts with cursor-based pagination.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Search receipts with advanced filtering and cursor pagination."""
        try:
            # Validate request parameters
            serializer = ReceiptSearchRequestSerializer(data=request.query_params)
            if not serializer.is_valid():
                return Response(
                    {
                        'success': False,
                        'error': 'validation_error',
                        'message': 'Invalid parameters',
                        'details': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            params = serializer.validated_data
            
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoReceiptRepository
            from infrastructure.pagination.cursor import CursorPagination
            
            receipt_repository = DjangoReceiptRepository()
            
            # Build search filters
            filters = self._build_search_filters(params)
            
            # Handle cursor pagination
            cursor_info = None
            if params.get('cursor'):
                try:
                    cursor_info = CursorPagination.decode_cursor(params['cursor'])
                except ValueError as e:
                    return Response(
                        {
                            'success': False,
                            'error': 'invalid_cursor',
                            'message': f'Invalid cursor: {str(e)}'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Execute search with cursor pagination
            result = self._execute_search(
                receipt_repository=receipt_repository,
                user=request.user,
                filters=filters,
                sort=params['sort'],
                order=params['order'],
                limit=params['limit'],
                cursor_info=cursor_info
            )
            
            # Build response
            response_data = self._build_response(result, params, cursor_info)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'search_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _build_search_filters(self, params):
        """Build search filters from request parameters."""
        filters = {}
        
        # Search query
        if params.get('q'):
            filters['search_query'] = params['q']
        
        # Status filter
        if params.get('status'):
            filters['statuses'] = [s.strip() for s in params['status'].split(',')]
        
        # Currency filter
        if params.get('currency'):
            filters['currencies'] = [c.strip() for c in params['currency'].split(',')]
        
        # Provider filter
        if params.get('provider'):
            filters['providers'] = [p.strip() for p in params['provider'].split(',')]
        
        # Date range
        if params.get('dateFrom'):
            filters['date_from'] = params['dateFrom']
        if params.get('dateTo'):
            filters['date_to'] = params['dateTo']
        
        # Amount range
        if params.get('amountMin'):
            filters['amount_min'] = params['amountMin']
        if params.get('amountMax'):
            filters['amount_max'] = params['amountMax']
        
        # Confidence filter
        if params.get('confidenceMin'):
            filters['confidence_min'] = params['confidenceMin']
        
        return filters
    
    def _execute_search(self, receipt_repository, user, filters, sort, order, limit, cursor_info):
        """Execute the search query with cursor pagination."""
        # This is a simplified implementation - in production, you'd want to use
        # raw SQL or Django ORM with proper indexing for performance
        
        # Get base queryset
        from infrastructure.database.models import Receipt
        queryset = Receipt.objects.filter(user_id=user.id)
        
        # Apply filters
        queryset = self._apply_filters(queryset, filters)
        
        # Apply cursor pagination
        if cursor_info:
            queryset = self._apply_cursor_pagination(queryset, cursor_info, sort)
        
        # Apply sorting
        queryset = self._apply_sorting(queryset, sort, order)
        
        # Apply limit and get results
        results = list(queryset[:limit + 1])  # +1 to check if there's a next page
        
        # Check if there are more results
        has_next = len(results) > limit
        if has_next:
            results = results[:-1]  # Remove the extra item
        
        return {
            'receipts': results,
            'has_next': has_next,
            'has_prev': cursor_info is not None,
            'total_count': None  # Not calculating total for performance
        }
    
    def _apply_filters(self, queryset, filters):
        """Apply search filters to the queryset."""
        from django.db.models import Q
        
        # Search query across merchant, notes, receipt_number
        if filters.get('search_query'):
            search_query = filters['search_query']
            queryset = queryset.filter(
                Q(ocr_data__merchant_name__icontains=search_query) |
                Q(metadata__notes__icontains=search_query) |
                Q(metadata__custom_fields__receipt_number__icontains=search_query)
            )
        
        # Status filter
        if filters.get('statuses'):
            queryset = queryset.filter(status__in=filters['statuses'])
        
        # Currency filter
        if filters.get('currencies'):
            queryset = queryset.filter(ocr_data__currency__in=filters['currencies'])
        
        # Provider filter
        if filters.get('providers'):
            queryset = queryset.filter(metadata__custom_fields__storage_provider__in=filters['providers'])
        
        # Date range
        if filters.get('date_from'):
            queryset = queryset.filter(ocr_data__date__gte=filters['date_from'])
        if filters.get('date_to'):
            queryset = queryset.filter(ocr_data__date__lte=filters['date_to'])
        
        # Amount range
        if filters.get('amount_min'):
            queryset = queryset.filter(ocr_data__total_amount__gte=filters['amount_min'])
        if filters.get('amount_max'):
            queryset = queryset.filter(ocr_data__total_amount__lte=filters['amount_max'])
        
        # Confidence filter
        if filters.get('confidence_min'):
            queryset = queryset.filter(ocr_data__confidence_score__gte=filters['confidence_min'])
        
        return queryset
    
    def _apply_cursor_pagination(self, queryset, cursor_info, sort):
        """Apply cursor-based pagination to the queryset."""
        from infrastructure.pagination.cursor import CursorPagination
        
        # Map API sort fields to database fields
        sort_field_mapping = {
            'date': 'ocr_data__date',
            'amount': 'ocr_data__total_amount',
            'merchant': 'ocr_data__merchant_name',
            'confidence': 'ocr_data__confidence_score'
        }
        
        db_sort_field = sort_field_mapping.get(sort, 'ocr_data__date')
        
        # Build where clause for cursor pagination
        where_clause, params = CursorPagination.build_where_clause(cursor_info, db_sort_field)
        
        # Apply the cursor filter
        from django.db.models import Q
        if cursor_info.order == 'desc':
            # For descending order, get rows with (sort_value, id) < (cursor_sort_value, cursor_id)
            queryset = queryset.extra(
                where=[where_clause],
                params=params
            )
        else:
            # For ascending order, get rows with (sort_value, id) > (cursor_sort_value, cursor_id)
            queryset = queryset.extra(
                where=[where_clause],
                params=params
            )
        
        return queryset
    
    def _apply_sorting(self, queryset, sort, order):
        """Apply sorting to the queryset."""
        # Map API sort fields to database fields
        sort_field_mapping = {
            'date': 'ocr_data__date',
            'amount': 'ocr_data__total_amount',
            'merchant': 'ocr_data__merchant_name',
            'confidence': 'ocr_data__confidence_score'
        }
        
        db_sort_field = sort_field_mapping.get(sort, 'ocr_data__date')
        
        if order == 'desc':
            queryset = queryset.order_by(f'-{db_sort_field}', '-id')
        else:
            queryset = queryset.order_by(db_sort_field, 'id')
        
        return queryset
    
    def _build_response(self, result, params, cursor_info):
        """Build the API response with cursor pagination."""
        from infrastructure.pagination.cursor import CursorPagination
        
        # Transform receipts to API format
        items = []
        for receipt in result['receipts']:
            items.append({
                'id': str(receipt.id),
                'merchant': receipt.ocr_data.get('merchant_name', '') if receipt.ocr_data else '',
                'date': receipt.ocr_data.get('date', '') if receipt.ocr_data else '',
                'amount': float(receipt.ocr_data.get('total_amount', 0)) if receipt.ocr_data else 0,
                'currency': receipt.ocr_data.get('currency', 'GBP') if receipt.ocr_data else 'GBP',
                'status': receipt.status,
                'confidence': receipt.ocr_data.get('confidence_score', 0) if receipt.ocr_data else 0,
                'provider': receipt.metadata.get('custom_fields', {}).get('storage_provider', '') if receipt.metadata else '',
                'thumbnailUrl': receipt.file_url
            })
        
        # Build pagination info
        page_info = {
            'nextCursor': None,
            'prevCursor': None,
            'hasNext': result['has_next'],
            'hasPrev': result['has_prev']
        }
        
        # Generate next cursor if there are more results
        if result['has_next'] and result['receipts']:
            last_receipt = result['receipts'][-1]
            sort_value = self._get_sort_value(last_receipt, params['sort'])
            page_info['nextCursor'] = CursorPagination.encode_cursor(
                sort=params['sort'],
                order=params['order'],
                sort_value=sort_value,
                receipt_id=str(last_receipt.id)
            )
        
        # Generate previous cursor if we have a current cursor
        if cursor_info and result['receipts']:
            first_receipt = result['receipts'][0]
            sort_value = self._get_sort_value(first_receipt, params['sort'])
            page_info['prevCursor'] = CursorPagination.encode_cursor(
                sort=params['sort'],
                order=params['order'],
                sort_value=sort_value,
                receipt_id=str(first_receipt.id)
            )
        
        return {
            'items': items,
            'pageInfo': page_info,
            'totalCount': result['total_count']
        }
    
    def _get_sort_value(self, receipt, sort_field):
        """Get the sort value for a receipt based on the sort field."""
        if sort_field == 'date':
            return receipt.ocr_data.get('date') if receipt.ocr_data else None
        elif sort_field == 'amount':
            return receipt.ocr_data.get('total_amount') if receipt.ocr_data else 0
        elif sort_field == 'merchant':
            return receipt.ocr_data.get('merchant_name') if receipt.ocr_data else ''
        elif sort_field == 'confidence':
            return receipt.ocr_data.get('confidence_score') if receipt.ocr_data else 0
        return None 