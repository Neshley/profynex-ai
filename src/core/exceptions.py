"""Custom exception hierarchy for Profynex AI.

Design Principles:
- Each exception has a specific purpose
- Exceptions include context and recovery suggestions
- Exceptions are serializable for logging and API responses
- Inheritance hierarchy allows targeted error handling
"""

from typing import Any, Optional, Dict
from enum import Enum


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    CRITICAL = "critical"  # System cannot continue
    ERROR = "error"        # Operation failed, system continues
    WARNING = "warning"    # Operation partially succeeded
    INFO = "info"          # Informational only


class ProfynexException(Exception):
    """Base exception for all Profynex AI errors.
    
    Attributes:
        message: Human-readable error message
        code: Machine-readable error code (e.g., 'MEMORY_001')
        severity: Error severity level
        context: Additional context about the error
        recovery_suggestion: Suggested action to recover from error
        original_error: Original exception if this wraps another
    """

    code: str = "UNKNOWN_ERROR"
    severity: ErrorSeverity = ErrorSeverity.ERROR
    default_message: str = "An unknown error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        code: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None,
        context: Optional[Dict[str, Any]] = None,
        recovery_suggestion: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize exception.
        
        Args:
            message: Error message (uses default if not provided)
            code: Error code (uses class default if not provided)
            severity: Error severity (uses class default if not provided)
            context: Additional context dictionary
            recovery_suggestion: How to recover from this error
            original_error: Original exception being wrapped
        """
        self.message = message or self.default_message
        self.code = code or self.code
        self.severity = severity or self.severity
        self.context = context or {}
        self.recovery_suggestion = recovery_suggestion
        self.original_error = original_error

        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to serializable dictionary.
        
        Returns:
            Dictionary with all exception details
        """
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "severity": self.severity.value,
            "context": self.context,
            "recovery_suggestion": self.recovery_suggestion,
        }

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message='{self.message}', code='{self.code}')"


# ============================================================================
# CONFIGURATION EXCEPTIONS
# ============================================================================


class ConfigurationError(ProfynexException):
    """Error in application configuration."""

    code = "CONFIG_001"
    default_message = "Configuration error"
    severity = ErrorSeverity.CRITICAL


class MissingConfigurationError(ConfigurationError):
    """Required configuration value is missing."""

    code = "CONFIG_002"
    default_message = "Required configuration value is missing"

    def __init__(
        self,
        config_key: str,
        **kwargs,
    ):
        super().__init__(
            message=f"Missing required configuration: {config_key}",
            recovery_suggestion=f"Set the {config_key} environment variable or configuration value",
            context={"config_key": config_key},
            **kwargs,
        )


class InvalidConfigurationError(ConfigurationError):
    """Configuration value is invalid."""

    code = "CONFIG_003"
    default_message = "Invalid configuration value"

    def __init__(
        self,
        config_key: str,
        expected_type: str,
        actual_value: Any,
        **kwargs,
    ):
        super().__init__(
            message=f"Invalid configuration for {config_key}: expected {expected_type}, got {type(actual_value).__name__}",
            recovery_suggestion=f"Ensure {config_key} is of type {expected_type}",
            context={
                "config_key": config_key,
                "expected_type": expected_type,
                "actual_value": str(actual_value),
            },
            **kwargs,
        )


# ============================================================================
# EVENT SYSTEM EXCEPTIONS
# ============================================================================


class EventError(ProfynexException):
    """Error in event system."""

    code = "EVENT_001"
    default_message = "Event system error"
    severity = ErrorSeverity.ERROR


class EventPublishError(EventError):
    """Failed to publish event."""

    code = "EVENT_002"
    default_message = "Failed to publish event"

    def __init__(
        self,
        event_name: str,
        reason: str,
        **kwargs,
    ):
        super().__init__(
            message=f"Failed to publish event '{event_name}': {reason}",
            context={"event_name": event_name, "reason": reason},
            **kwargs,
        )


class EventSubscriptionError(EventError):
    """Failed to subscribe to event."""

    code = "EVENT_003"
    default_message = "Failed to subscribe to event"

    def __init__(
        self,
        event_name: str,
        handler_name: str,
        reason: str,
        **kwargs,
    ):
        super().__init__(
            message=f"Failed to subscribe handler '{handler_name}' to event '{event_name}': {reason}",
            context={
                "event_name": event_name,
                "handler_name": handler_name,
                "reason": reason,
            },
            **kwargs,
        )


class UnknownEventError(EventError):
    """Event type is not registered."""

    code = "EVENT_004"
    default_message = "Unknown event type"

    def __init__(
        self,
        event_name: str,
        **kwargs,
    ):
        super().__init__(
            message=f"Event type '{event_name}' is not registered",
            recovery_suggestion=f"Register the event type before publishing or subscribing",
            context={"event_name": event_name},
            **kwargs,
        )


# ============================================================================
# DEPENDENCY INJECTION EXCEPTIONS
# ============================================================================


class ContainerError(ProfynexException):
    """Error in dependency injection container."""

    code = "DI_001"
    default_message = "Dependency injection container error"
    severity = ErrorSeverity.ERROR


class ServiceNotFoundError(ContainerError):
    """Service not registered in container."""

    code = "DI_002"
    default_message = "Service not found in container"

    def __init__(
        self,
        service_name: str,
        **kwargs,
    ):
        super().__init__(
            message=f"Service '{service_name}' is not registered in the container",
            recovery_suggestion=f"Register '{service_name}' before resolving it",
            context={"service_name": service_name},
            **kwargs,
        )


class ServiceResolutionError(ContainerError):
    """Failed to resolve service from container."""

    code = "DI_003"
    default_message = "Failed to resolve service"

    def __init__(
        self,
        service_name: str,
        reason: str,
        **kwargs,
    ):
        super().__init__(
            message=f"Failed to resolve service '{service_name}': {reason}",
            context={"service_name": service_name, "reason": reason},
            **kwargs,
        )


class DuplicateServiceError(ContainerError):
    """Service already registered in container."""

    code = "DI_004"
    default_message = "Service already registered"

    def __init__(
        self,
        service_name: str,
        **kwargs,
    ):
        super().__init__(
            message=f"Service '{service_name}' is already registered",
            recovery_suggestion=f"Use a different service name or unregister the existing service first",
            context={"service_name": service_name},
            **kwargs,
        )


# ============================================================================
# CONTEXT EXCEPTIONS
# ============================================================================


class ContextError(ProfynexException):
    """Error in context management."""

    code = "CTX_001"
    default_message = "Context management error"
    severity = ErrorSeverity.ERROR


class ContextNotFoundError(ContextError):
    """Context value not found."""

    code = "CTX_002"
    default_message = "Context value not found"

    def __init__(
        self,
        key: str,
        **kwargs,
    ):
        super().__init__(
            message=f"Context value for key '{key}' not found",
            recovery_suggestion=f"Ensure the context is set before accessing '{key}'",
            context={"key": key},
            **kwargs,
        )


class InvalidContextError(ContextError):
    """Context is in invalid state."""

    code = "CTX_003"
    default_message = "Context is in invalid state"

    def __init__(
        self,
        reason: str,
        **kwargs,
    ):
        super().__init__(
            message=f"Context is in invalid state: {reason}",
            context={"reason": reason},
            **kwargs,
        )


# ============================================================================
# PLUGIN EXCEPTIONS
# ============================================================================


class PluginError(ProfynexException):
    """Error in plugin system."""

    code = "PLUGIN_001"
    default_message = "Plugin system error"
    severity = ErrorSeverity.ERROR


class PluginNotFoundError(PluginError):
    """Plugin not found."""

    code = "PLUGIN_002"
    default_message = "Plugin not found"

    def __init__(
        self,
        plugin_name: str,
        **kwargs,
    ):
        super().__init__(
            message=f"Plugin '{plugin_name}' not found",
            recovery_suggestion=f"Ensure the plugin '{plugin_name}' is installed and registered",
            context={"plugin_name": plugin_name},
            **kwargs,
        )


class PluginLoadError(PluginError):
    """Failed to load plugin."""

    code = "PLUGIN_003"
    default_message = "Failed to load plugin"

    def __init__(
        self,
        plugin_name: str,
        reason: str,
        **kwargs,
    ):
        super().__init__(
            message=f"Failed to load plugin '{plugin_name}': {reason}",
            context={"plugin_name": plugin_name, "reason": reason},
            **kwargs,
        )


class InvalidPluginError(PluginError):
    """Plugin does not meet requirements."""

    code = "PLUGIN_004"
    default_message = "Invalid plugin"

    def __init__(
        self,
        plugin_name: str,
        reason: str,
        **kwargs,
    ):
        super().__init__(
            message=f"Plugin '{plugin_name}' is invalid: {reason}",
            context={"plugin_name": plugin_name, "reason": reason},
            **kwargs,
        )


# ============================================================================
# HEALTH CHECK EXCEPTIONS
# ============================================================================


class HealthCheckError(ProfynexException):
    """Error in health check system."""

    code = "HEALTH_001"
    default_message = "Health check error"
    severity = ErrorSeverity.WARNING


class ServiceUnhealthyError(HealthCheckError):
    """Service failed health check."""

    code = "HEALTH_002"
    default_message = "Service is unhealthy"
    severity = ErrorSeverity.WARNING

    def __init__(
        self,
        service_name: str,
        reason: str,
        **kwargs,
    ):
        super().__init__(
            message=f"Service '{service_name}' is unhealthy: {reason}",
            recovery_suggestion=f"Check the logs and configuration for service '{service_name}'",
            context={"service_name": service_name, "reason": reason},
            **kwargs,
        )
