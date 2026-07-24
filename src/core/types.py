"""Type definitions and protocols for Profynex AI.

Design Principles:
- Use Protocol for interface definitions (structural subtyping)
- Use TypedDict for data structures
- Use Literal for specific string values
- Full type hints for IDE support
"""

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    TypedDict,
    Union,
    runtime_checkable,
    Awaitable,
)
from enum import Enum
from abc import ABC, abstractmethod


# ============================================================================
# EVENT TYPES
# ============================================================================


class EventData(TypedDict, total=False):
    """Base event data structure."""
    timestamp: float
    source: str
    correlation_id: str


EventHandler = Callable[["Event"], Awaitable[None]]
"""Type for async event handlers."""


class Event:
    """Base event class.
    
    Events are the primary communication mechanism between modules.
    Each event has a name, data, and metadata.
    """

    def __init__(
        self,
        name: str,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ):
        """Initialize event.
        
        Args:
            name: Event name (e.g., 'user.spoke', 'vision.screen_updated')
            data: Event payload data
            source: Module that triggered the event
            correlation_id: Unique ID for tracking event chain
        """
        self.name = name
        self.data = data or {}
        self.source = source
        self.correlation_id = correlation_id

    def __str__(self) -> str:
        return f"Event(name={self.name}, source={self.source})"

    def __repr__(self) -> str:
        return f"Event(name='{self.name}', data={self.data}, source='{self.source}')"


# ============================================================================
# CONTAINER/DI TYPES
# ============================================================================


ServiceFactory = Callable[..., Any]
"""Type for service factory functions."""

ServiceLifetime = Enum("ServiceLifetime", "SINGLETON TRANSIENT SCOPED")
"""Service lifetime enum:
- SINGLETON: Single instance for entire application
- TRANSIENT: New instance every time
- SCOPED: Single instance per scope (e.g., per request)
"""


@runtime_checkable
class IService(Protocol):
    """Protocol for service objects.
    
    Any class implementing this protocol can be registered in the container.
    """

    async def initialize(self) -> None:
        """Initialize the service."""
        ...

    async def shutdown(self) -> None:
        """Shutdown the service."""
        ...


# ============================================================================
# CONTEXT TYPES
# ============================================================================


class ContextData(TypedDict, total=False):
    """Type for context data storage."""
    user_id: Optional[str]
    session_id: str
    operation_id: str
    correlation_id: str
    metadata: Dict[str, Any]


# ============================================================================
# PLUGIN TYPES
# ============================================================================


class PluginMetadata(TypedDict, total=False):
    """Plugin metadata structure."""
    name: str
    version: str
    author: str
    description: str
    entry_point: str
    min_version: str
    max_version: str
    dependencies: List[str]


@runtime_checkable
class IPlugin(Protocol):
    """Protocol for plugin objects.
    
    All plugins must implement this interface.
    """

    async def on_load(self) -> None:
        """Called when plugin is loaded."""
        ...

    async def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        ...


# ============================================================================
# HEALTH CHECK TYPES
# ============================================================================


class HealthStatus(str, Enum):
    """Health status enum."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckResult(TypedDict, total=False):
    """Health check result structure."""
    status: HealthStatus
    timestamp: float
    checks: Dict[str, Any]
    message: str


HealthCheck = Callable[[], Awaitable[HealthCheckResult]]
"""Type for async health check functions."""


# ============================================================================
# CONFIGURATION TYPES
# ============================================================================


class ConfigValue(TypedDict, total=False):
    """Configuration value structure."""
    name: str
    value: Any
    type: str
    required: bool
    default: Any
    description: str


# ============================================================================
# LOGGING TYPES
# ============================================================================


class LogRecord(TypedDict, total=False):
    """Log record structure."""
    timestamp: float
    level: str
    logger: str
    message: str
    module: str
    function: str
    line: int
    context: Dict[str, Any]


# ============================================================================
# RESULT TYPES
# ============================================================================


class ResultT(ABC):
    """Base class for result types.
    
    Result types wrap either a successful value or an error,
    providing a functional way to handle errors without exceptions.
    """

    @abstractmethod
    def is_ok(self) -> bool:
        """Check if result is successful."""
        ...

    @abstractmethod
    def is_err(self) -> bool:
        """Check if result is an error."""
        ...

    @abstractmethod
    def unwrap(self) -> Any:
        """Get the value or raise if error."""
        ...

    @abstractmethod
    def unwrap_or(self, default: Any) -> Any:
        """Get the value or return default if error."""
        ...


class Ok(ResultT):
    """Successful result."""

    def __init__(self, value: Any):
        self.value = value

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> Any:
        return self.value

    def unwrap_or(self, default: Any) -> Any:
        return self.value

    def __repr__(self) -> str:
        return f"Ok({self.value!r})"


class Err(ResultT):
    """Error result."""

    def __init__(self, error: Exception):
        self.error = error

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> Any:
        raise self.error

    def unwrap_or(self, default: Any) -> Any:
        return default

    def __repr__(self) -> str:
        return f"Err({self.error!r})"


Result = Union[Ok, Err]
"""Result type: either Ok(value) or Err(error)."""
