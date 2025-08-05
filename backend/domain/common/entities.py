"""
Base domain entities for Smart Accounts Management System.
Following Domain-Driven Design patterns.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class DomainEvent:
    """Base class for domain events."""
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_on: datetime = field(default_factory=datetime.utcnow)
    event_type: str = field(init=False)
    
    def __post_init__(self):
        self.event_type = self.__class__.__name__


class ValueObject(ABC):
    """Base class for value objects."""
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self._get_equality_components() == other._get_equality_components()
    
    def __hash__(self) -> int:
        return hash(self._get_equality_components())
    
    @abstractmethod
    def _get_equality_components(self) -> tuple:
        """Return components used for equality comparison."""
        pass


class Entity(ABC):
    """Base class for domain entities."""
    
    def __init__(self, id: Optional[str] = None):
        self._id = id or str(uuid.uuid4())
        self._domain_events: List[DomainEvent] = []
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()
    
    @property
    def id(self) -> str:
        """Get the entity ID."""
        return self._id
    
    @property
    def created_at(self) -> datetime:
        """Get the creation timestamp."""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """Get the last update timestamp."""
        return self._updated_at
    
    def add_domain_event(self, event: DomainEvent) -> None:
        """Add a domain event to the entity."""
        self._domain_events.append(event)
    
    def clear_domain_events(self) -> List[DomainEvent]:
        """Clear and return all domain events."""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get all domain events without clearing them."""
        return self._domain_events.copy()
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def _update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self._updated_at = datetime.utcnow()


class AggregateRoot(Entity):
    """Base class for aggregate roots."""
    
    def __init__(self, id: Optional[str] = None):
        super().__init__(id)
        self._version = 0
    
    @property
    def version(self) -> int:
        """Get the aggregate version."""
        return self._version
    
    def increment_version(self) -> None:
        """Increment the aggregate version."""
        self._version += 1
    
    def add_domain_event(self, event: DomainEvent) -> None:
        """Add a domain event and increment version."""
        super().add_domain_event(event)
        self.increment_version()
        self._update_timestamp()


@dataclass
class Money(ValueObject):
    """Value object for monetary amounts."""
    
    amount: float
    currency: str = "GBP"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency cannot be empty")
    
    def _get_equality_components(self) -> tuple:
        return (self.amount, self.currency)
    
    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add money with different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def __sub__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot subtract money with different currencies")
        return Money(self.amount - other.amount, self.currency)
    
    def __mul__(self, factor: float) -> 'Money':
        return Money(self.amount * factor, self.currency)
    
    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"


@dataclass
class Email(ValueObject):
    """Value object for email addresses."""
    
    address: str
    
    def __post_init__(self):
        if not self.address or '@' not in self.address:
            raise ValueError("Invalid email address")
        self.address = self.address.lower().strip()
    
    def _get_equality_components(self) -> tuple:
        return (self.address,)
    
    def __str__(self) -> str:
        return self.address


@dataclass
class PhoneNumber(ValueObject):
    """Value object for phone numbers."""
    
    number: str
    country_code: str = "+44"
    
    def __post_init__(self):
        if not self.number:
            raise ValueError("Phone number cannot be empty")
        # Basic UK phone number validation
        if self.country_code == "+44":
            cleaned = ''.join(filter(str.isdigit, self.number))
            if len(cleaned) < 10 or len(cleaned) > 11:
                raise ValueError("Invalid UK phone number format")
    
    def _get_equality_components(self) -> tuple:
        return (self.number, self.country_code)
    
    def __str__(self) -> str:
        return f"{self.country_code} {self.number}"


@dataclass
class Address(ValueObject):
    """Value object for addresses."""
    
    street: str
    city: str
    postal_code: str
    country: str = "UK"
    
    def __post_init__(self):
        if not all([self.street, self.city, self.postal_code]):
            raise ValueError("Street, city, and postal code are required")
    
    def _get_equality_components(self) -> tuple:
        return (self.street, self.city, self.postal_code, self.country)
    
    def __str__(self) -> str:
        return f"{self.street}, {self.city}, {self.postal_code}, {self.country}"


@dataclass
class DateRange(ValueObject):
    """Value object for date ranges."""
    
    start_date: datetime
    end_date: datetime
    
    def __post_init__(self):
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")
    
    def _get_equality_components(self) -> tuple:
        return (self.start_date, self.end_date)
    
    def contains(self, date: datetime) -> bool:
        """Check if a date is within this range."""
        return self.start_date <= date <= self.end_date
    
    def overlaps(self, other: 'DateRange') -> bool:
        """Check if this range overlaps with another range."""
        return self.start_date < other.end_date and other.start_date < self.end_date
    
    def __str__(self) -> str:
        return f"{self.start_date.date()} to {self.end_date.date()}" 