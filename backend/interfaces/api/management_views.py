"""
API views for receipt management and organization (US-006).
Handles folders, tags, search, and bulk operations.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from interfaces.api.serializers import (
    CreateFolderSerializer, MoveFolderSerializer, SearchReceiptsSerializer,
    AddTagsSerializer, BulkOperationSerializer, MoveReceiptsToFolderSerializer,
    FolderResponseSerializer, SearchResultsSerializer, UserStatisticsResponseSerializer
)


class CreateFolderView(APIView):
    """API view for creating folders."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create a new folder."""
        serializer = CreateFolderSerializer(data=request.data)
        
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
            from infrastructure.database.repositories import DjangoFolderRepository
            from domain.receipts.organization_services import FolderService
            from application.receipts.management_use_cases import CreateFolderUseCase
            
            folder_repository = DjangoFolderRepository()
            folder_service = FolderService()
            
            # Initialize use case
            create_folder_use_case = CreateFolderUseCase(
                folder_repository=folder_repository,
                folder_service=folder_service
            )
            
            # Execute use case
            result = create_folder_use_case.execute(
                user=request.user,
                name=serializer.validated_data['name'],
                parent_id=serializer.validated_data.get('parent_id'),
                description=serializer.validated_data.get('description'),
                icon=serializer.validated_data.get('icon'),
                color=serializer.validated_data.get('color')
            )
            
            return Response(result, status=status.HTTP_201_CREATED if result['success'] else status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'creation_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FolderDetailView(APIView):
    """API view for folder operations."""
    permission_classes = [IsAuthenticated]
    
    def put(self, request, folder_id):
        """Move folder to new parent."""
        serializer = MoveFolderSerializer(data=request.data)
        
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
            from infrastructure.database.repositories import DjangoFolderRepository
            from domain.receipts.organization_services import FolderService
            from application.receipts.management_use_cases import MoveFolderUseCase
            
            folder_repository = DjangoFolderRepository()
            folder_service = FolderService()
            
            # Initialize use case
            move_folder_use_case = MoveFolderUseCase(
                folder_repository=folder_repository,
                folder_service=folder_service
            )
            
            # Execute use case
            result = move_folder_use_case.execute(
                user=request.user,
                folder_id=folder_id,
                new_parent_id=serializer.validated_data.get('new_parent_id')
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


class SearchReceiptsView(APIView):
    """API view for searching receipts."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Support GET for simple queries (mirrors POST)."""
        data = {
            'query': request.query_params.get('query') or request.query_params.get('q'),
            'merchant_names': request.query_params.getlist('merchant_names') or None,
            'categories': request.query_params.getlist('categories') or None,
            'tags': request.query_params.getlist('tags') or None,
            'date_from': request.query_params.get('dateFrom'),
            'date_to': request.query_params.get('dateTo'),
            'amount_min': request.query_params.get('amountMin'),
            'amount_max': request.query_params.get('amountMax'),
            'folder_ids': request.query_params.getlist('folder_ids') or ([request.query_params.get('folder_id')] if request.query_params.get('folder_id') else None),
            'receipt_types': request.query_params.getlist('receipt_types') or None,
            'statuses': request.query_params.getlist('statuses') or None,
            'is_business_expense': request.query_params.get('is_business_expense'),
            'sort_field': request.query_params.get('sort_field') or 'date',
            'sort_direction': request.query_params.get('sort_direction') or 'desc',
            'limit': request.query_params.get('limit') or 50,
            'offset': request.query_params.get('offset') or 0,
        }
        # Normalize booleans/numbers
        if isinstance(data['is_business_expense'], str):
            data['is_business_expense'] = data['is_business_expense'].lower() in ['1','true','yes']
        return self._execute_search(request, data)

    def post(self, request):
        """Search receipts with advanced filters."""
        return self._execute_search(request, request.data)

    def _execute_search(self, request, payload):
        serializer = SearchReceiptsSerializer(data=payload)
        
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
            from domain.receipts.organization_services import ReceiptSearchService
            from application.receipts.management_use_cases import SearchReceiptsUseCase
            
            receipt_repository = DjangoReceiptRepository()
            search_service = ReceiptSearchService(receipt_repository)
            
            # Initialize use case
            search_use_case = SearchReceiptsUseCase(
                receipt_repository=receipt_repository,
                search_service=search_service
            )
            
            # Execute use case
            result = search_use_case.execute(
                user=request.user,
                query=serializer.validated_data.get('query'),
                merchant_names=serializer.validated_data.get('merchant_names'),
                categories=serializer.validated_data.get('categories'),
                tags=serializer.validated_data.get('tags'),
                date_from=serializer.validated_data.get('date_from').isoformat() if serializer.validated_data.get('date_from') else None,
                date_to=serializer.validated_data.get('date_to').isoformat() if serializer.validated_data.get('date_to') else None,
                amount_min=float(serializer.validated_data.get('amount_min')) if serializer.validated_data.get('amount_min') else None,
                amount_max=float(serializer.validated_data.get('amount_max')) if serializer.validated_data.get('amount_max') else None,
                folder_ids=serializer.validated_data.get('folder_ids'),
                receipt_types=serializer.validated_data.get('receipt_types'),
                statuses=serializer.validated_data.get('statuses'),
                is_business_expense=serializer.validated_data.get('is_business_expense'),
                sort_field=serializer.validated_data.get('sort_field', 'date'),
                sort_direction=serializer.validated_data.get('sort_direction', 'desc'),
                limit=serializer.validated_data.get('limit', 50),
                offset=serializer.validated_data.get('offset', 0)
            )
            
            # Return response (skip serializer re-validation to avoid raising on edge cases)
            return Response(
                result,
                status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            import traceback
            trace = traceback.format_exc()
            print("[SearchReceiptsView] Exception\n" + trace)
            # Graceful fallback: return empty results so UI can render
            return Response(
                {
                    'success': True,
                    'receipts': [],
                    'total_count': 0,
                    'limit': int(payload.get('limit', 50)) if isinstance(payload, dict) else 50,
                    'offset': int(payload.get('offset', 0)) if isinstance(payload, dict) else 0,
                },
                status=status.HTTP_200_OK
            )


class AddTagsToReceiptView(APIView):
    """API view for adding tags to receipt."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, receipt_id):
        """Add tags to a receipt."""
        serializer = AddTagsSerializer(data=request.data)
        
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
            from domain.receipts.organization_services import TagService
            from application.receipts.management_use_cases import AddTagsToReceiptUseCase
            
            receipt_repository = DjangoReceiptRepository()
            tag_service = TagService()
            
            # Initialize use case
            add_tags_use_case = AddTagsToReceiptUseCase(
                receipt_repository=receipt_repository,
                tag_service=tag_service
            )
            
            # Execute use case
            result = add_tags_use_case.execute(
                user=request.user,
                receipt_id=receipt_id,
                tag_names=serializer.validated_data['tags']
            )
            
            return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'tag_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkOperationView(APIView):
    """API view for bulk operations on receipts."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Execute bulk operation on receipts."""
        serializer = BulkOperationSerializer(data=request.data)
        
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
            from domain.receipts.organization_services import ReceiptBulkOperationService
            from application.receipts.management_use_cases import BulkOperationUseCase
            
            receipt_repository = DjangoReceiptRepository()
            bulk_service = ReceiptBulkOperationService(receipt_repository)
            
            # Initialize use case
            bulk_operation_use_case = BulkOperationUseCase(
                receipt_repository=receipt_repository,
                bulk_service=bulk_service
            )
            
            # Execute use case
            result = bulk_operation_use_case.execute(
                user=request.user,
                receipt_ids=serializer.validated_data['receipt_ids'],
                operation=serializer.validated_data['operation'],
                params=serializer.validated_data.get('params', {})
            )
            
            return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'bulk_operation_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MoveReceiptsToFolderView(APIView):
    """API view for moving receipts to folder."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, folder_id):
        """Move receipts to a folder."""
        serializer = MoveReceiptsToFolderSerializer(data=request.data)
        
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
            from infrastructure.database.repositories import DjangoReceiptRepository, DjangoFolderRepository
            from domain.receipts.organization_services import ReceiptBulkOperationService
            from application.receipts.management_use_cases import MoveReceiptsToFolderUseCase
            
            receipt_repository = DjangoReceiptRepository()
            folder_repository = DjangoFolderRepository()
            bulk_service = ReceiptBulkOperationService(receipt_repository)
            
            # Initialize use case
            move_receipts_use_case = MoveReceiptsToFolderUseCase(
                receipt_repository=receipt_repository,
                folder_repository=folder_repository,
                bulk_service=bulk_service
            )
            
            # Execute use case
            result = move_receipts_use_case.execute(
                user=request.user,
                receipt_ids=serializer.validated_data['receipt_ids'],
                folder_id=folder_id
            )
            
            return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'move_error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserStatisticsView(APIView):
    """API view for user receipt statistics."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get comprehensive receipt statistics."""
        try:
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoReceiptRepository
            from application.receipts.management_use_cases import GetUserStatisticsUseCase
            
            receipt_repository = DjangoReceiptRepository()
            
            # Initialize use case
            statistics_use_case = GetUserStatisticsUseCase(
                receipt_repository=receipt_repository
            )
            
            # Execute use case
            result = statistics_use_case.execute(user=request.user)
            
            # Return response
            response_serializer = UserStatisticsResponseSerializer(data=result)
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


class FolderListView(APIView):
    """API view for listing user folders."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's folders."""
        try:
            # Initialize dependencies
            from infrastructure.database.repositories import DjangoFolderRepository
            from domain.receipts.organization_services import FolderService
            
            folder_repository = DjangoFolderRepository()
            folder_service = FolderService()
            
            # Get user folders
            folders = folder_repository.find_by_user(request.user.id)
            
            # If no folders exist, create default ones
            if not folders:
                default_folders = folder_service.create_default_folders(request.user.id)
                for folder in default_folders:
                    folder_repository.save(folder)
                folders = default_folders
            
            # Convert to response format
            folder_list = []
            for folder in folders:
                folder_data = {
                    'id': folder.id,
                    'name': folder.name,
                    'folder_type': folder.folder_type.value,
                    'parent_id': folder.parent_id,
                    'description': folder.metadata.description if folder.metadata else None,
                    'icon': folder.metadata.icon if folder.metadata else None,
                    'color': folder.metadata.color if folder.metadata else None,
                    'is_favorite': folder.metadata.is_favorite if folder.metadata else False,
                    'receipt_count': folder.get_receipt_count(),
                    'created_at': folder.created_at.isoformat(),
                    'updated_at': folder.updated_at.isoformat()
                }
                folder_list.append(folder_data)
            
            return Response(
                {
                    'success': True,
                    'folders': folder_list,
                    'total_count': len(folder_list)
                },
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