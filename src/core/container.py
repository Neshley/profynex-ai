"""Dependency injection container.

Design Pattern: Service Locator + Factory Pattern
- Register services with different lifetimes
- Resolve services with dependency injection
- Support for factories and singletons
"""

from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Type,
    TypeVar,
)
from enum import Enum
import inspect

from .types import ServiceFactory, ServiceLifetime, IService
from .exceptions import (
    ServiceNotFoundError,
    ServiceResolutionError,
    DuplicateServiceError,
)
from .logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ServiceLifetime(str, Enum):
    """Service lifetime scope."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class ServiceDescriptor:
    """Describes how to create a service."""

    def __init__(
        self,
        service_type: Type,
        factory: Optional[ServiceFactory] = None,
        instance: Optional[Any] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ):
        """Initialize service descriptor.
        
        Args:
            service_type: Service interface type
            factory: Factory function to create instances
            instance: Pre-created instance (for singletons)
            lifetime: Service lifetime scope
        """
        self.service_type = service_type
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime
        self.name = service_type.__name__


class Container:
    """Dependency injection container.
    
    Manages service registration and resolution with support for
    different lifetimes (singleton, transient, scoped).
    """

    def __init__(self):
        """Initialize container."""
        self._services: Dict[str, ServiceDescriptor] = {}
        self._singletons: Dict[str, Any] = {}

    def register(
        self,
        service_type: Type[T],
        factory: Optional[ServiceFactory] = None,
        *,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        name: Optional[str] = None,
    ) -> None:
        """Register a service in the container.
        
        Args:
            service_type: Service interface/class type
            factory: Factory function (if None, uses service_type as factory)
            lifetime: Service lifetime scope
            name: Optional service name (defaults to class name)
            
        Raises:
            DuplicateServiceError: If service already registered
            InvalidConfigurationError: If configuration is invalid
        """
        service_name = name or service_type.__name__

        if service_name in self._services:
            raise DuplicateServiceError(service_name)

        # Use service_type as factory if not provided
        if factory is None:
            factory = service_type

        descriptor = ServiceDescriptor(
            service_type=service_type,
            factory=factory,
            lifetime=lifetime,
        )

        self._services[service_name] = descriptor
        logger.debug(
            f"Registered service '{service_name}' "
            f"with lifetime {lifetime.value}"
        )

    def register_singleton(
        self,
        service_type: Type[T],
        instance: Optional[T] = None,
        factory: Optional[Callable[[], T]] = None,
        name: Optional[str] = None,
    ) -> None:
        """Register a singleton service.
        
        Args:
            service_type: Service interface/class type
            instance: Pre-created instance
            factory: Factory to create the singleton
            name: Optional service name
        """
        service_name = name or service_type.__name__

        if service_name in self._services:
            raise DuplicateServiceError(service_name)

        descriptor = ServiceDescriptor(
            service_type=service_type,
            factory=factory,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON,
        )

        self._services[service_name] = descriptor

        # If instance provided, store it immediately
        if instance is not None:
            self._singletons[service_name] = instance

        logger.debug(f"Registered singleton service '{service_name}'")

    def resolve(
        self,
        service_type: Type[T],
        name: Optional[str] = None,
    ) -> T:
        """Resolve a service from the container.
        
        Args:
            service_type: Service type to resolve
            name: Optional service name
            
        Returns:
            Instance of the service
            
        Raises:
            ServiceNotFoundError: If service not registered
            ServiceResolutionError: If resolution fails
        """
        service_name = name or service_type.__name__

        if service_name not in self._services:
            raise ServiceNotFoundError(service_name)

        descriptor = self._services[service_name]

        try:
            # Check for singleton
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                if service_name not in self._singletons:
                    # Create singleton
                    instance = self._create_instance(descriptor)
                    self._singletons[service_name] = instance
                    logger.debug(f"Created singleton '{service_name}'")
                return self._singletons[service_name]

            # Transient or scoped - create new instance
            instance = self._create_instance(descriptor)
            logger.debug(f"Created {descriptor.lifetime.value} instance '{service_name}'")
            return instance

        except Exception as e:
            raise ServiceResolutionError(
                service_name=service_name,
                reason=str(e),
                original_error=e,
            )

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create an instance using the descriptor's factory.
        
        Args:
            descriptor: Service descriptor
            
        Returns:
            Created instance
        """
        if descriptor.instance is not None:
            return descriptor.instance

        if descriptor.factory is None:
            raise ServiceResolutionError(
                descriptor.name,
                "No factory or instance configured",
            )

        # Try to resolve constructor dependencies
        try:
            sig = inspect.signature(descriptor.factory)
            kwargs = {}

            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                # Try to resolve parameter from container
                if param.annotation != inspect.Parameter.empty:
                    try:
                        kwargs[param_name] = self.resolve(param.annotation)
                    except ServiceNotFoundError:
                        # Parameter not available in container
                        if param.default == inspect.Parameter.empty:
                            raise

            return descriptor.factory(**kwargs)

        except TypeError:
            # No parameter inspection available, try direct call
            return descriptor.factory()

    def is_registered(self, service_type: Type, name: Optional[str] = None) -> bool:
        """Check if a service is registered.
        
        Args:
            service_type: Service type
            name: Optional service name
            
        Returns:
            True if registered
        """
        service_name = name or service_type.__name__
        return service_name in self._services

    def unregister(
        self,
        service_type: Type,
        name: Optional[str] = None,
    ) -> None:
        """Unregister a service.
        
        Args:
            service_type: Service type
            name: Optional service name
        """
        service_name = name or service_type.__name__
        if service_name in self._services:
            del self._services[service_name]
            if service_name in self._singletons:
                del self._singletons[service_name]
            logger.debug(f"Unregistered service '{service_name}'")

    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._singletons.clear()
        logger.debug("Cleared container")

    def get_registered_services(self) -> list[str]:
        """Get list of registered service names.
        
        Returns:
            List of service names
        """
        return list(self._services.keys())


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get or create the global container.
    
    Returns:
        Global Container instance
    """
    global _container
    if _container is None:
        _container = Container()
    return _container


def initialize_container() -> Container:
    """Initialize the global container.
    
    Returns:
        Initialized Container
    """
    global _container
    _container = Container()
    logger.info("Container initialized")
    return _container
