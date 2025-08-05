"""
API views for the Smart Accounts Management System.
Implements REST API endpoints following Clean Architecture principles.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.utils import timezone

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    CustomTokenObtainPairSerializer,
    UserResponseSerializer,
    ErrorResponseSerializer
)
from application.accounts.use_cases import (
    UserRegistrationUseCase,
    UserLoginUseCase,
    EmailVerificationUseCase,
    UserProfileUseCase
)
from infrastructure.database.repositories import UserRepository
from domain.accounts.services import UserDomainService
from infrastructure.email.services import EmailService


class UserRegistrationView(APIView):
    """
    API view for user registration.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle user registration."""
        serializer = UserRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'validation_error',
                    'message': 'Invalid registration data',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize use case with dependencies
            user_repository = UserRepository()
            user_domain_service = UserDomainService()
            email_service = EmailService()
            
            registration_use_case = UserRegistrationUseCase(
                user_repository=user_repository,
                user_domain_service=user_domain_service,
                email_service=email_service
            )
            
            # Execute registration use case
            result = registration_use_case.execute(serializer.validated_data)
            
            # Return success response
            response_serializer = UserResponseSerializer(data=result)
            response_serializer.is_valid()
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except ValidationError as e:
            return Response(
                {
                    'error': 'validation_error',
                    'message': str(e),
                    'details': {}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            return Response(
                {
                    'error': 'business_error',
                    'message': str(e),
                    'details': {}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'error': 'server_error',
                    'message': 'An unexpected error occurred',
                    'details': {}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserLoginView(APIView):
    """
    API view for user login.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle user login."""
        serializer = UserLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'validation_error',
                    'message': 'Invalid login data',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize use case with dependencies
            user_repository = UserRepository()
            user_domain_service = UserDomainService()
            
            login_use_case = UserLoginUseCase(
                user_repository=user_repository,
                user_domain_service=user_domain_service
            )
            
            # Execute login use case
            result = login_use_case.execute(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            
            # Return success response
            response_serializer = UserResponseSerializer(data=result)
            response_serializer.is_valid()
            
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )
            
        except ValidationError as e:
            return Response(
                {
                    'error': 'validation_error',
                    'message': str(e),
                    'details': {}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            return Response(
                {
                    'error': 'authentication_error',
                    'message': str(e),
                    'details': {}
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {
                    'error': 'server_error',
                    'message': 'An unexpected error occurred',
                    'details': {}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token view with additional user data.
    """
    serializer_class = CustomTokenObtainPairSerializer


class EmailVerificationView(APIView):
    """
    API view for email verification.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle email verification."""
        serializer = EmailVerificationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'validation_error',
                    'message': 'Invalid verification data',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize use case with dependencies
            user_repository = UserRepository()
            user_domain_service = UserDomainService()
            
            verification_use_case = EmailVerificationUseCase(
                user_repository=user_repository,
                user_domain_service=user_domain_service
            )
            
            # Execute verification use case
            result = verification_use_case.execute(serializer.validated_data['token'])
            
            # Return success response
            response_serializer = UserResponseSerializer(data=result)
            response_serializer.is_valid()
            
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )
            
        except ValueError as e:
            return Response(
                {
                    'error': 'verification_error',
                    'message': str(e),
                    'details': {}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'error': 'server_error',
                    'message': 'An unexpected error occurred',
                    'details': {}
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
            # Initialize use case
            user_repository = UserRepository()
            profile_use_case = UserProfileUseCase(user_repository=user_repository)
            
            # Get profile
            profile_data = profile_use_case.get_profile(request.user.id)
            
            # Return profile data
            return Response(
                profile_data,
                status=status.HTTP_200_OK
            )
            
        except ValueError as e:
            return Response(
                {
                    'error': 'not_found',
                    'message': str(e),
                    'details': {}
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    'error': 'server_error',
                    'message': 'An unexpected error occurred',
                    'details': {}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request):
        """Update user profile."""
        serializer = UserProfileUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'validation_error',
                    'message': 'Invalid profile data',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize use case
            user_repository = UserRepository()
            profile_use_case = UserProfileUseCase(user_repository=user_repository)
            
            # Update profile
            updated_profile = profile_use_case.update_profile(
                user_id=request.user.id,
                profile_data=serializer.validated_data
            )
            
            # Return updated profile
            return Response(
                updated_profile,
                status=status.HTTP_200_OK
            )
            
        except ValueError as e:
            return Response(
                {
                    'error': 'not_found',
                    'message': str(e),
                    'details': {}
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    'error': 'server_error',
                    'message': 'An unexpected error occurred',
                    'details': {}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetRequestView(APIView):
    """
    API view for password reset request.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle password reset request."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'validation_error',
                    'message': 'Invalid email address',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # TODO: Implement password reset request logic
            # This will be implemented in the next iteration
            
            return Response(
                {
                    'message': 'If an account with this email exists, a password reset link has been sent.'
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {
                    'error': 'server_error',
                    'message': 'An unexpected error occurred',
                    'details': {}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetConfirmView(APIView):
    """
    API view for password reset confirmation.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle password reset confirmation."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'validation_error',
                    'message': 'Invalid reset data',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # TODO: Implement password reset confirmation logic
            # This will be implemented in the next iteration
            
            return Response(
                {
                    'message': 'Password has been reset successfully.'
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {
                    'error': 'server_error',
                    'message': 'An unexpected error occurred',
                    'details': {}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint.
    """
    return Response(
        {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'service': 'Smart Accounts Management System'
        },
        status=status.HTTP_200_OK
    )


# Receipt Views
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


class ReceiptListView(APIView):
    """
    API view for listing receipts.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of user receipts."""
        try:
            # Get query parameters
            status_param = request.query_params.get('status')
            receipt_type_param = request.query_params.get('receipt_type')
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))
            
            # Convert parameters to enums if provided
            from domain.receipts.entities import ReceiptStatus, ReceiptType
            status = ReceiptStatus(status_param) if status_param else None
            receipt_type = ReceiptType(receipt_type_param) if receipt_type_param else None
            
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoReceiptRepository
            from application.receipts.use_cases import ReceiptListUseCase
            
            receipt_repository = DjangoReceiptRepository()
            list_use_case = ReceiptListUseCase(receipt_repository=receipt_repository)
            
            # Execute list use case
            result = list_use_case.execute(
                user=request.user,
                status=status,
                receipt_type=receipt_type,
                limit=limit,
                offset=offset
            )
            
            # Return response
            response_serializer = ReceiptListResponseSerializer(data=result)
            response_serializer.is_valid()
            
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
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
            detail_use_case = ReceiptDetailUseCase(receipt_repository=receipt_repository)
            
            # Execute detail use case
            result = detail_use_case.execute(receipt_id=receipt_id, user=request.user)
            
            if not result['success']:
                return Response(
                    {
                        'success': False,
                        'error': result['error']
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Return response
            response_serializer = ReceiptDetailResponseSerializer(data=result)
            response_serializer.is_valid()
            
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
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
            
            # Return response
            response_serializer = ReceiptUpdateResponseSerializer(data=result)
            response_serializer.is_valid()
            
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'update_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 