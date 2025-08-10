"""
Cursor-based pagination utility for the Smart Accounts Management System.

This module provides utilities for encoding and decoding cursor-based pagination
cursors, which are used for efficient pagination of large datasets.
"""

import base64
import json
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime


@dataclass
class CursorInfo:
    """Information contained in a pagination cursor."""
    sort: str
    order: str
    version: int
    key: List[Any]


class CursorPagination:
    """
    Cursor-based pagination utility.
    
    Cursors are base64url-encoded JSON objects containing:
    - sort: the field being sorted on
    - order: asc or desc
    - version: cursor format version for future compatibility
    - key: list of values for the sort field and tiebreaker (id)
    """
    
    VERSION = 1
    SUPPORTED_SORTS = {'date', 'amount', 'merchant', 'confidence'}
    SUPPORTED_ORDERS = {'asc', 'desc'}
    
    @classmethod
    def encode_cursor(cls, sort: str, order: str, sort_value: Any, receipt_id: str) -> str:
        """
        Encode a cursor from sort parameters and values.
        
        Args:
            sort: The field being sorted on
            order: Sort order (asc or desc)
            sort_value: The value of the sort field
            receipt_id: The receipt ID for tiebreaking
            
        Returns:
            Base64url-encoded cursor string
            
        Raises:
            ValueError: If sort or order is invalid
        """
        if sort not in cls.SUPPORTED_SORTS:
            raise ValueError(f"Unsupported sort field: {sort}")
        
        if order not in cls.SUPPORTED_ORDERS:
            raise ValueError(f"Unsupported order: {order}")
        
        # Handle different data types for proper JSON serialization
        if isinstance(sort_value, datetime):
            sort_value = sort_value.isoformat()
        elif isinstance(sort_value, Decimal):
            sort_value = float(sort_value)
        
        cursor_data = {
            "sort": sort,
            "order": order,
            "v": cls.VERSION,
            "key": [sort_value, receipt_id]
        }
        
        # Convert to JSON and encode as base64url
        json_str = json.dumps(cursor_data, separators=(',', ':'))
        base64_str = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
        
        return base64_str
    
    @classmethod
    def decode_cursor(cls, cursor: str) -> CursorInfo:
        """
        Decode a cursor string back to its components.
        
        Args:
            cursor: Base64url-encoded cursor string
            
        Returns:
            CursorInfo object containing the decoded cursor data
            
        Raises:
            ValueError: If cursor is invalid or malformed
        """
        try:
            # Decode base64url
            json_str = base64.urlsafe_b64decode(cursor.encode('utf-8')).decode('utf-8')
            cursor_data = json.loads(json_str)
            
            # Validate required fields
            required_fields = {'sort', 'order', 'v', 'key'}
            if not all(field in cursor_data for field in required_fields):
                raise ValueError("Missing required cursor fields")
            
            # Validate version
            if cursor_data['v'] != cls.VERSION:
                raise ValueError(f"Unsupported cursor version: {cursor_data['v']}")
            
            # Validate sort and order
            if cursor_data['sort'] not in cls.SUPPORTED_SORTS:
                raise ValueError(f"Unsupported sort field in cursor: {cursor_data['sort']}")
            
            if cursor_data['order'] not in cls.SUPPORTED_ORDERS:
                raise ValueError(f"Unsupported order in cursor: {cursor_data['order']}")
            
            # Validate key structure
            if not isinstance(cursor_data['key'], list) or len(cursor_data['key']) != 2:
                raise ValueError("Invalid key structure in cursor")
            
            return CursorInfo(
                sort=cursor_data['sort'],
                order=cursor_data['order'],
                version=cursor_data['v'],
                key=cursor_data['key']
            )
            
        except (base64.binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid cursor format: {e}")
    
    @classmethod
    def build_where_clause(cls, cursor_info: CursorInfo, sort_field: str) -> Tuple[str, List[Any]]:
        """
        Build a WHERE clause for cursor-based pagination.
        
        Args:
            cursor_info: Decoded cursor information
            sort_field: The database field name for sorting
            
        Returns:
            Tuple of (where_clause, parameters)
        """
        sort_value, receipt_id = cursor_info.key
        
        # Convert sort_value back to appropriate type if needed
        if sort_field == 'date':
            try:
                if isinstance(sort_value, str):
                    sort_value = datetime.fromisoformat(sort_value)
            except ValueError:
                pass
        
        if cursor_info.order == 'desc':
            # For descending order, get rows with (sort_value, id) < (cursor_sort_value, cursor_id)
            where_clause = f"({sort_field}, id) < (%s, %s)"
        else:
            # For ascending order, get rows with (sort_value, id) > (cursor_sort_value, cursor_id)
            where_clause = f"({sort_field}, id) > (%s, %s)"
        
        return where_clause, [sort_value, receipt_id]
    
    @classmethod
    def is_valid_cursor(cls, cursor: str) -> bool:
        """
        Check if a cursor string is valid without raising exceptions.
        
        Args:
            cursor: Cursor string to validate
            
        Returns:
            True if cursor is valid, False otherwise
        """
        try:
            cls.decode_cursor(cursor)
            return True
        except ValueError:
            return False
