"""
Base repository interfaces for Smart Accounts Management System.
Following the Repository pattern from Domain-Driven Design.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
from .entities import Entity, AggregateRoot

T = TypeVar('T', bound=Entity)
AR = TypeVar('AR', bound=AggregateRoot)


class Repository(ABC, Generic[T]):
    """Base repository interface for entities."""
    
    @abstractmethod
    def get_by_id(self, id: str) -> Optional[T]:
        """Get an entity by its ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """Get all entities."""
        pass
    
    @abstractmethod
    def add(self, entity: T) -> T:
        """Add a new entity."""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    def delete(self, entity: T) -> None:
        """Delete an entity."""
        pass
    
    @abstractmethod
    def exists(self, id: str) -> bool:
        """Check if an entity exists by ID."""
        pass


class AggregateRepository(Repository[AR]):
    """Base repository interface for aggregate roots."""
    
    @abstractmethod
    def get_by_id(self, id: str) -> Optional[AR]:
        """Get an aggregate by its ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[AR]:
        """Get all aggregates."""
        pass
    
    @abstractmethod
    def add(self, aggregate: AR) -> AR:
        """Add a new aggregate."""
        pass
    
    @abstractmethod
    def update(self, aggregate: AR) -> AR:
        """Update an existing aggregate."""
        pass
    
    @abstractmethod
    def delete(self, aggregate: AR) -> None:
        """Delete an aggregate."""
        pass
    
    @abstractmethod
    def exists(self, id: str) -> bool:
        """Check if an aggregate exists by ID."""
        pass


class UnitOfWork(ABC):
    """Unit of Work pattern interface."""
    
    @abstractmethod
    def __enter__(self):
        """Enter the unit of work context."""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the unit of work context."""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Commit all changes."""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """Rollback all changes."""
        pass
    
    @abstractmethod
    def begin_transaction(self) -> None:
        """Begin a new transaction."""
        pass


class Specification(ABC):
    """Base specification interface for querying entities."""
    
    @abstractmethod
    def is_satisfied_by(self, entity: T) -> bool:
        """Check if an entity satisfies this specification."""
        pass
    
    def and_(self, other: 'Specification') -> 'AndSpecification':
        """Combine this specification with another using AND."""
        return AndSpecification(self, other)
    
    def or_(self, other: 'Specification') -> 'OrSpecification':
        """Combine this specification with another using OR."""
        return OrSpecification(self, other)
    
    def not_(self) -> 'NotSpecification':
        """Negate this specification."""
        return NotSpecification(self)


class AndSpecification(Specification):
    """Combines two specifications with AND logic."""
    
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, entity: T) -> bool:
        return self.left.is_satisfied_by(entity) and self.right.is_satisfied_by(entity)


class OrSpecification(Specification):
    """Combines two specifications with OR logic."""
    
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, entity: T) -> bool:
        return self.left.is_satisfied_by(entity) or self.right.is_satisfied_by(entity)


class NotSpecification(Specification):
    """Negates a specification."""
    
    def __init__(self, specification: Specification):
        self.specification = specification
    
    def is_satisfied_by(self, entity: T) -> bool:
        return not self.specification.is_satisfied_by(entity)


class QueryRepository(Repository[T]):
    """Repository interface with query capabilities."""
    
    @abstractmethod
    def find_by_specification(self, specification: Specification) -> List[T]:
        """Find entities that satisfy a specification."""
        pass
    
    @abstractmethod
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """Find entities by criteria."""
        pass
    
    @abstractmethod
    def count_by_specification(self, specification: Specification) -> int:
        """Count entities that satisfy a specification."""
        pass
    
    @abstractmethod
    def exists_by_specification(self, specification: Specification) -> bool:
        """Check if any entity satisfies a specification."""
        pass


class PaginationParams:
    """Parameters for pagination."""
    
    def __init__(self, page: int = 1, page_size: int = 20):
        self.page = max(1, page)
        self.page_size = max(1, min(page_size, 100))  # Limit to 100 items per page
    
    @property
    def offset(self) -> int:
        """Calculate the offset for pagination."""
        return (self.page - 1) * self.page_size


class PaginatedResult:
    """Result of a paginated query."""
    
    def __init__(self, items: List[T], total_count: int, pagination: PaginationParams):
        self.items = items
        self.total_count = total_count
        self.pagination = pagination
    
    @property
    def total_pages(self) -> int:
        """Calculate the total number of pages."""
        return (self.total_count + self.pagination.page_size - 1) // self.pagination.page_size
    
    @property
    def has_next(self) -> bool:
        """Check if there are more pages."""
        return self.pagination.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Check if there are previous pages."""
        return self.pagination.page > 1


class PaginatedRepository(QueryRepository[T]):
    """Repository interface with pagination capabilities."""
    
    @abstractmethod
    def find_paginated(
        self, 
        pagination: PaginationParams,
        specification: Optional[Specification] = None,
        order_by: Optional[str] = None
    ) -> PaginatedResult:
        """Find entities with pagination."""
        pass 