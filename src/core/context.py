"""Context management for operations and requests.

Design Pattern: Context Manager + ThreadLocal/AsyncLocal
- Manage per-operation context (correlation IDs, user info, etc.)
- Support nested contexts
- Async-safe with asyncio support
"""

import asyncio
import contextvars
from typing import Any, Dict, Optional
from datetime import datetime
import uuid

from .exceptions import ContextNotFoundError, InvalidContextError
from .logger import get_logger

logger = get_logger(__name__)

# AsyncVar to store context per task
_context_var: contextvars.ContextVar["OperationContext"] = contextvars.ContextVar(
    "operation_context", default=None
)


class OperationContext:
    """Context for a single operation or request.
    
    Stores metadata that should be available throughout an operation:
    - Correlation ID for tracking across modules
    - User information
    - Session information
    - Custom metadata
    """

    def __init__(
        self,
        operation_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize operation context.
        
        Args:
            operation_id: Unique ID for this operation
            correlation_id: ID to track related operations
            user_id: ID of the user initiating the operation
            session_id: Session ID
            metadata: Additional metadata dict
        """
        self.operation_id = operation_id or str(uuid.uuid4())
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self.metadata: Dict[str, Any] = metadata or {}
        self.created_at = datetime.utcnow()
        self._parent_context: Optional["OperationContext"] = None

    def set_value(self, key: str, value: Any) -> None:
        """Set a value in context metadata.
        
        Args:
            key: Key name
            value: Value to store
        """
        self.metadata[key] = value
        logger.debug(
            f"Set context value: {key}",
            extra={"operation_id": self.operation_id},
        )

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from context metadata.
        
        Args:
            key: Key name
            default: Default value if key not found
            
        Returns:
            Value from metadata or default
            
        Raises:
            ContextNotFoundError: If key not found and default is None
        """
        if key not in self.metadata:
            if default is None:
                raise ContextNotFoundError(key)
            return default
        return self.metadata[key]

    def has_value(self, key: str) -> bool:
        """Check if a key exists in context.
        
        Args:
            key: Key name
            
        Returns:
            True if key exists
        """
        return key in self.metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "operation_id": self.operation_id,
            "correlation_id": self.correlation_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"OperationContext("
            f"operation_id={self.operation_id}, "
            f"correlation_id={self.correlation_id}, "
            f"user_id={self.user_id}"
            f")"
        )


class ContextManager:
    """Manager for operation contexts.
    
    Handles setting, getting, and clearing contexts for async operations.
    """

    @staticmethod
    def set_context(context: OperationContext) -> None:
        """Set the current operation context.
        
        Args:
            context: Context to set
        """
        _context_var.set(context)
        logger.debug(
            f"Set operation context",
            extra={"operation_id": context.operation_id},
        )

    @staticmethod
    def get_context() -> Optional[OperationContext]:
        """Get the current operation context.
        
        Returns:
            Current context or None if not set
        """
        return _context_var.get()

    @staticmethod
    def current_context() -> OperationContext:
        """Get the current operation context.
        
        Returns:
            Current context
            
        Raises:
            InvalidContextError: If no context is set
        """
        context = _context_var.get()
        if context is None:
            raise InvalidContextError("No context is currently set")
        return context

    @staticmethod
    def clear_context() -> None:
        """Clear the current operation context."""
        _context_var.set(None)
        logger.debug("Cleared operation context")

    @staticmethod
    def create_child_context(
        parent: Optional[OperationContext] = None,
        **kwargs,
    ) -> OperationContext:
        """Create a child context that inherits from parent.
        
        Args:
            parent: Parent context (uses current if not provided)
            **kwargs: Arguments for new context
            
        Returns:
            New child context
        """
        if parent is None:
            parent = ContextManager.get_context()

        # Create new context inheriting correlation ID
        correlation_id = kwargs.get(
            "correlation_id",
            parent.correlation_id if parent else str(uuid.uuid4()),
        )

        child = OperationContext(
            correlation_id=correlation_id,
            user_id=kwargs.get("user_id", parent.user_id if parent else None),
            session_id=kwargs.get(
                "session_id", parent.session_id if parent else None
            ),
            metadata=kwargs.get("metadata", {}),
        )

        if parent:
            child._parent_context = parent

        return child


class context_scope:
    """Async context manager for setting operation context.
    
    Usage:
        async with context_scope(operation_id="123"):
            # Inside this block, context is available
            ctx = ContextManager.current_context()
    """

    def __init__(
        self,
        context: Optional[OperationContext] = None,
        **kwargs,
    ):
        """Initialize context scope.
        
        Args:
            context: Context to use (creates new if not provided)
            **kwargs: Arguments for context creation
        """
        self.context = context or OperationContext(**kwargs)
        self.previous_context: Optional[OperationContext] = None

    async def __aenter__(self) -> OperationContext:
        """Enter async context."""
        self.previous_context = ContextManager.get_context()
        ContextManager.set_context(self.context)
        return self.context

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        if self.previous_context:
            ContextManager.set_context(self.previous_context)
        else:
            ContextManager.clear_context()


# Helper functions for common operations


def get_correlation_id() -> str:
    """Get correlation ID from current context.
    
    Returns:
        Correlation ID or empty string if no context
    """
    context = ContextManager.get_context()
    return context.correlation_id if context else ""


def get_operation_id() -> str:
    """Get operation ID from current context.
    
    Returns:
        Operation ID or empty string if no context
    """
    context = ContextManager.get_context()
    return context.operation_id if context else ""


def get_user_id() -> Optional[str]:
    """Get user ID from current context.
    
    Returns:
        User ID or None if not set
    """
    context = ContextManager.get_context()
    return context.user_id if context else None
