"""
API views for the Smart Accounts Management System.
Defines REST API endpoints for user management and receipt processing.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, EmailVerificationSerializer,
    UserProfileSerializer, ReceiptUploadSerializer, ReceiptUploadResponseSerializer,
    ReceiptListResponseSerializer, ReceiptDetailResponseSerializer,
    ReceiptUpdateSerializer, ReceiptReprocessSerializer, ReceiptValidateSerializer,
    ReceiptCategorizeSerializer, ReceiptStatisticsResponseSerializer,
    ReceiptReprocessResponseSerializer, ReceiptValidateResponseSerializer,
    ReceiptCategorizeResponseSerializer
)
from infrastructure.ocr.services import OCRService, OCRMethod
from domain.receipts.entities import ReceiptType


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
            from domain.accounts.services import PasswordService, EmailVerificationService
            from application.accounts.use_cases import UserRegistrationUseCase
            
            user_repository = DjangoUserRepository()
            password_service = PasswordService()
            email_verification_service = EmailVerificationService()
            
            # Initialize use case
            registration_use_case = UserRegistrationUseCase(
                user_repository=user_repository,
                password_service=password_service,
                email_verification_service=email_verification_service
            )
            
            # Execute registration
            result = registration_use_case.execute(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                first_name=serializer.validated_data.get('first_name', ''),
                last_name=serializer.validated_data.get('last_name', ''),
                company_name=serializer.validated_data.get('company_name', ''),
                business_type=serializer.validated_data.get('business_type', ''),
                tax_id=serializer.validated_data.get('tax_id', ''),
                vat_number=serializer.validated_data.get('vat_number', '')
            )
            
            return Response(result, status=status.HTTP_201_CREATED if result['success'] else status.HTTP_400_BAD_REQUEST)
            
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
            from domain.accounts.services import PasswordService
            from application.accounts.use_cases import UserLoginUseCase
            
            user_repository = DjangoUserRepository()
            password_service = PasswordService()
            
            # Initialize use case
            login_use_case = UserLoginUseCase(
                user_repository=user_repository,
                password_service=password_service
            )
            
            # Execute login
            result = login_use_case.execute(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            
            return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_401_UNAUTHORIZED)
            
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
            from domain.accounts.services import EmailVerificationService
            from application.accounts.use_cases import EmailVerificationUseCase
            
            user_repository = DjangoUserRepository()
            email_verification_service = EmailVerificationService()
            
            # Initialize use case
            verification_use_case = EmailVerificationUseCase(
                user_repository=user_repository,
                email_verification_service=email_verification_service
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
            result = profile_use_case.execute(user=request.user)
            
            return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
            
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
            result = profile_use_case.execute(
                user=request.user,
                profile_data=serializer.validated_data
            )
            
            return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
            
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
        serializer = ReceiptUploadSerializer(data=request.data, files=request.FILES)
        
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
    API view for listing receipts.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List user receipts with optional filtering."""
        try:
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
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'list_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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