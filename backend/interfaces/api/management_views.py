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
        """Extremely defensive GET: return empty results if anything looks off."""
        try:
            qp = request.query_params
            payload = {
                'query': qp.get('query') or qp.get('q') or None,
                'merchant_names': [m for m in qp.getlist('merchant_names') if m],
                'categories': [c for c in qp.getlist('categories') if c],
                'tags': [t for t in qp.getlist('tags') if t],
                'date_from': qp.get('dateFrom') or None,
                'date_to': qp.get('dateTo') or None,
                'amount_min': qp.get('amountMin') or None,
                'amount_max': qp.get('amountMax') or None,
                'folder_ids': [f for f in (qp.getlist('folder_ids') or ([qp.get('folder_id')] if qp.get('folder_id') else [])) if f],
                'client_ids': [c for c in qp.getlist('client_ids') if c],
                'receipt_types': [r for r in qp.getlist('receipt_types') if r],
                'statuses': [s for s in qp.getlist('statuses') if s],
                'is_business_expense': qp.get('is_business_expense') or None,
                'has_transaction': qp.get('has_transaction') or None,
                'has_folder': qp.get('has_folder') or None,
                'sort_field': qp.get('sort_field') or 'date',
                'sort_direction': qp.get('sort_direction') or 'desc',
                'limit': int(qp.get('limit') or 50),
                'offset': int(qp.get('offset') or 0),
            }
            # Hand off to the shared executor which already has robust fallbacks
            return self._execute_search(request, payload)
        except Exception:
            import traceback
            print("[SearchReceiptsView.get] Fatal exception before execute\n" + traceback.format_exc())
            return Response(
                {
                    'success': True,
                    'receipts': [],
                    'total_count': 0,
                    'limit': 50,
                    'offset': 0,
                    'error': 'A fatal error occurred while parsing search parameters.'
                },
                status=status.HTTP_200_OK
            )

    def _execute_search(self, request, payload):
        """Shared executor for GET/POST with robust fallbacks to avoid 500s."""
        serializer = SearchReceiptsSerializer(data=payload)
        
        if not serializer.is_valid():
            # Return empty results rather than 400 to keep UI stable
            return Response(
                {
                    'success': True,
                    'receipts': [],
                    'total_count': 0,
                    'limit': int(payload.get('limit', 50)) if isinstance(payload, dict) else 50,
                    'offset': int(payload.get('offset', 0)) if isinstance(payload, dict) else 0,
                    'validation_errors': serializer.errors,
                    'error': 'Search parameter validation failed.'
                },
                status=status.HTTP_200_OK
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

            vd = serializer.validated_data
            # Execute use case
            result = search_use_case.execute(
                user=request.user,
                query=vd.get('query'),
                merchant_names=vd.get('merchant_names'),
                categories=vd.get('categories'),
                tags=vd.get('tags'),
                date_from=vd.get('date_from').isoformat() if vd.get('date_from') else None,
                date_to=vd.get('date_to').isoformat() if vd.get('date_to') else None,
                amount_min=float(vd.get('amount_min')) if vd.get('amount_min') else None,
                amount_max=float(vd.get('amount_max')) if vd.get('amount_max') else None,
                folder_ids=vd.get('folder_ids'),
                client_ids=vd.get('client_ids'),
                receipt_types=vd.get('receipt_types'),
                statuses=vd.get('statuses'),
                is_business_expense=vd.get('is_business_expense'),
                has_transaction=vd.get('has_transaction'),
                has_folder=vd.get('has_folder'),
                sort_field=vd.get('sort_field', 'date'),
                sort_direction=vd.get('sort_direction', 'desc'),
                limit=vd.get('limit', 50),
                offset=vd.get('offset', 0)
            )

            return Response(
                result,
                status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            import traceback
            print("[SearchReceiptsView] Exception\n" + traceback.format_exc())
            # Graceful fallback: return empty results so UI can render
            return Response(
                {
                    'success': True,
                    'receipts': [],
                    'total_count': 0,
                    'limit': int(payload.get('limit', 50)) if isinstance(payload, dict) else 50,
                    'offset': int(payload.get('offset', 0)) if isinstance(payload, dict) else 0,
                    'error': 'An unexpected error occurred during the search operation.'
                },
                status=status.HTTP_200_OK
            )

    def post(self, request):
        """Search receipts with advanced filters (POST)."""
        return self._execute_search(request, request.data)


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