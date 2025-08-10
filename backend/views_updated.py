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
                    "success": False,
                    "error": "list_error",
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _is_search_request(self, request):
        """Check if this request has search parameters."""
        search_params = ["q", "status", "currency", "provider", "dateFrom", "dateTo", 
                        "amountMin", "amountMax", "confidenceMin", "sort", "order", "cursor"]
        return any(request.query_params.get(param) for param in search_params)
    
    def _handle_legacy_request(self, request):
        """Handle legacy offset-based pagination request."""
        # Get query parameters
        status_param = request.query_params.get("status")
        receipt_type_param = request.query_params.get("receipt_type")
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))
        
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
            receipt_type=status_enum,
            limit=limit,
            offset=offset
        )
        
        # Return response
        response_serializer = ReceiptListResponseSerializer(data=result)
        response_serializer.is_valid()
        
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK if result["success"] else status.HTTP_400_BAD_REQUEST
        )
    
    def _handle_search_request(self, request):
        """Handle search request with cursor pagination."""
        try:
            # Validate request parameters
            serializer = ReceiptSearchRequestSerializer(data=request.query_params)
            if not serializer.is_valid():
                return Response(
                    {
                        "success": False,
                        "error": "validation_error",
                        "message": "Invalid parameters",
                        "details": serializer.errors
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
            if params.get("cursor"):
                try:
                    cursor_info = CursorPagination.decode_cursor(params["cursor"])
                except ValueError as e:
                    return Response(
                        {
                            "success": False,
                            "error": "invalid_cursor",
                            "message": f"Invalid cursor: {str(e)}"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Execute search with cursor pagination
            result = self._execute_search(
                receipt_repository=receipt_repository,
                user=request.user,
                filters=filters,
                sort=params["sort"],
                order=params["order"],
                limit=params["limit"],
                cursor_info=cursor_info
            )
            
            # Build response
            response_data = self._build_response(result, params, cursor_info)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": "search_error",
                    "message": str(e)
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
                    "success": False,
                    "error": "list_error",
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _is_search_request(self, request):
        """Check if this request has search parameters."""
        search_params = ["q", "status", "currency", "provider", "dateFrom", "dateTo", 
                        "amountMin", "amountMax", "confidenceMin", "sort", "order", "cursor"]
        return any(request.query_params.get(param) for param in search_params)
    
    def _handle_legacy_request(self, request):
        """Handle legacy offset-based pagination request."""
        # Get query parameters
        status_param = request.query_params.get("status")
        receipt_type_param = request.query_params.get("receipt_type")
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))
        
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
            receipt_type=status_enum,
            limit=limit,
            offset=offset
        )
        
        # Return response
        response_serializer = ReceiptListResponseSerializer(data=result)
        response_serializer.is_valid()
        
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK if result["success"] else status.HTTP_400_BAD_REQUEST
        )
    
    def _handle_search_request(self, request):
        """Handle search request with cursor pagination."""
        try:
            # Validate request parameters
            serializer = ReceiptSearchRequestSerializer(data=request.query_params)
            if not serializer.is_valid():
                return Response(
                    {
                        "success": False,
                        "error": "validation_error",
                        "message": "Invalid parameters",
                        "details": serializer.errors
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
            if params.get("cursor"):
                try:
                    cursor_info = CursorPagination.decode_cursor(params["cursor"])
                except ValueError as e:
                    return Response(
                        {
                            "success": False,
                            "error": "invalid_cursor",
                            "message": f"Invalid cursor: {str(e)}"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Execute search with cursor pagination
            result = self._execute_search(
                receipt_repository=receipt_repository,
                user=request.user,
                filters=filters,
                sort=params["sort"],
                order=params["order"],
                limit=params["limit"],
                cursor_info=cursor_info
            )
            
            # Build response
            response_data = self._build_response(result, params, cursor_info)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": "search_error",
                    "message": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    
    def _build_search_filters(self, params):
        """Build search filters from request parameters."""
        filters = {}
        
        # Search query
        if params.get("q"):
            filters["search_query"] = params["q"]
        
        # Status filter
        if params.get("status"):
            filters["statuses"] = [s.strip() for s in params["status"].split(",")]
        
        # Currency filter
        if params.get("currency"):
            filters["currencies"] = [c.strip() for c in params["currency"].split(",")]
        
        # Provider filter
        if params.get("provider"):
            filters["providers"] = [p.strip() for p in params["provider"].split(",")]
        
        # Date range
        if params.get("dateFrom"):
            filters["date_from"] = params["dateFrom"]
        if params.get("dateTo"):
            filters["date_to"] = params["dateTo"]
        
        # Amount range
        if params.get("amountMin"):
            filters["amount_min"] = params["amountMin"]
        if params.get("amountMax"):
            filters["amount_max"] = params["amountMax"]
        
        # Confidence filter
        if params.get("confidenceMin"):
            filters["confidence_min"] = params["confidenceMin"]
        
        return filters
    
    def _execute_search(self, receipt_repository, user, filters, sort, order, limit, cursor_info):
        """Execute the search query with cursor pagination."""
        # Get base queryset
        queryset = receipt_repository.get_user_receipts(user)
        
        # Apply filters
        queryset = self._apply_filters(queryset, filters)
        
        # Apply cursor pagination
        if cursor_info:
            queryset = self._apply_cursor_pagination(queryset, cursor_info, sort)
        
        # Apply sorting
        queryset = self._apply_sorting(queryset, sort, order)
        
        # Apply limit and get results
        results = list(queryset[:limit + 1])  # +1 to check if there is a next page
        
        # Check if there are more results
        has_next = len(results) > limit
        if has_next:
            results = results[:-1]  # Remove the extra item
        
        return {
            "receipts": results,
            "has_next": has_next,
            "has_prev": cursor_info is not None,
            "total_count": None  # Not calculating total for performance
        }
