"""Tests for Core Infrastructure Module.

Tests cover all components with comprehensive scenarios.
"""

import pytest
import asyncio
from datetime import datetime

from src.core.exceptions import (
    ProfynexException,
    ConfigurationError,
    MissingConfigurationError,
    InvalidConfigurationError,
    EventPublishError,
    EventSubscriptionError,
    UnknownEventError,
    ServiceNotFoundError,
    ServiceResolutionError,
    DuplicateServiceError,
    ContextNotFoundError,
    InvalidContextError,
)
from src.core.types import (
    Event,
    EventHandler,
    HealthStatus,
    Ok,
    Err,
)
from src.core.events import EventBus
from src.core.container import Container, ServiceLifetime
from src.core.context import (
    OperationContext,
    ContextManager,
    context_scope,
    get_correlation_id,
)
from src.core.health import HealthCheckRegistry


# ============================================================================
# EXCEPTION TESTS
# ============================================================================


class TestExceptionHierarchy:
    """Test exception hierarchy and serialization."""

    def test_base_exception_creation(self):
        """Test creating base exception."""
        exc = ProfynexException(
            message="Test error",
            code="TEST_001",
            context={"key": "value"},
        )
        assert exc.message == "Test error"
        assert exc.code == "TEST_001"
        assert exc.context == {"key": "value"}

    def test_exception_serialization(self):
        """Test exception to_dict serialization."""
        exc = MissingConfigurationError(
            config_key="API_KEY",
        )
        data = exc.to_dict()
        assert data["code"] == "CONFIG_002"
        assert data["context"]["config_key"] == "API_KEY"
        assert "recovery_suggestion" in data

    def test_missing_configuration_error(self):
        """Test missing configuration error."""
        exc = MissingConfigurationError(config_key="DEBUG")
        assert "DEBUG" in str(exc)
        assert "CONFIG_002" in str(exc)

    def test_invalid_configuration_error(self):
        """Test invalid configuration error."""
        exc = InvalidConfigurationError(
            config_key="PORT",
            expected_type="int",
            actual_value="invalid",
        )
        assert "PORT" in str(exc)
        assert "CONFIG_003" in str(exc)

    def test_exception_with_original_error(self):
        """Test exception wrapping original error."""
        original = ValueError("Original error")
        exc = ProfynexException(
            message="Wrapped error",
            original_error=original,
        )
        assert exc.original_error is original


# ============================================================================
# EVENT SYSTEM TESTS
# ============================================================================


class TestEventBus:
    """Test event bus functionality."""

    @pytest.fixture
    async def bus(self):
        """Create event bus for testing."""
        return EventBus()

    @pytest.mark.asyncio
    async def test_register_event(self, bus):
        """Test event registration."""
        await bus.register_event("test.event")
        events = await bus.get_registered_events()
        assert "test.event" in events

    @pytest.mark.asyncio
    async def test_subscribe_to_event(self, bus):
        """Test subscribing to event."""
        await bus.register_event("test.event")
        
        called = False
        
        async def handler(event: Event):
            nonlocal called
            called = True
        
        await bus.subscribe("test.event", handler)
        unsubscribe = await bus.subscribe("test.event", handler)
        
        event = Event("test.event")
        await bus.publish(event, wait_for_handlers=True)
        
        assert called

    @pytest.mark.asyncio
    async def test_unsubscribe_from_event(self, bus):
        """Test unsubscribing from event."""
        await bus.register_event("test.event")
        
        call_count = 0
        
        async def handler(event: Event):
            nonlocal call_count
            call_count += 1
        
        unsubscribe = await bus.subscribe("test.event", handler)
        
        event = Event("test.event")
        await bus.publish(event, wait_for_handlers=True)
        assert call_count == 1
        
        await unsubscribe()
        
        await bus.publish(event, wait_for_handlers=True)
        assert call_count == 1  # Should not be called again

    @pytest.mark.asyncio
    async def test_publish_unknown_event_fails(self, bus):
        """Test publishing unknown event raises error."""
        event = Event("unknown.event")
        with pytest.raises(UnknownEventError):
            await bus.publish(event)

    @pytest.mark.asyncio
    async def test_subscribe_to_unknown_event_fails(self, bus):
        """Test subscribing to unknown event raises error."""
        async def handler(event: Event):
            pass
        
        with pytest.raises(UnknownEventError):
            await bus.subscribe("unknown.event", handler)

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, bus):
        """Test event delivery to multiple subscribers."""
        await bus.register_event("test.event")
        
        calls = []
        
        async def handler1(event: Event):
            calls.append(1)
        
        async def handler2(event: Event):
            calls.append(2)
        
        await bus.subscribe("test.event", handler1)
        await bus.subscribe("test.event", handler2)
        
        event = Event("test.event")
        await bus.publish(event, wait_for_handlers=True)
        
        assert len(calls) == 2
        assert set(calls) == {1, 2}

    @pytest.mark.asyncio
    async def test_event_data_passed_to_handler(self, bus):
        """Test event data is passed to handlers."""
        await bus.register_event("test.event")
        
        received_data = {}
        
        async def handler(event: Event):
            received_data.update(event.data)
        
        await bus.subscribe("test.event", handler)
        
        event = Event("test.event", data={"message": "hello"})
        await bus.publish(event, wait_for_handlers=True)
        
        assert received_data == {"message": "hello"}

    @pytest.mark.asyncio
    async def test_subscriber_count(self, bus):
        """Test getting subscriber count."""
        await bus.register_event("test.event")
        
        async def handler1(event: Event):
            pass
        
        async def handler2(event: Event):
            pass
        
        count = await bus.get_subscriber_count("test.event")
        assert count == 0
        
        await bus.subscribe("test.event", handler1)
        count = await bus.get_subscriber_count("test.event")
        assert count == 1
        
        await bus.subscribe("test.event", handler2)
        count = await bus.get_subscriber_count("test.event")
        assert count == 2


# ============================================================================
# DEPENDENCY INJECTION TESTS
# ============================================================================


class TestContainer:
    """Test dependency injection container."""

    @pytest.fixture
    def container(self):
        """Create container for testing."""
        return Container()

    class TestService:
        """Test service class."""
        def __init__(self, name: str = "test"):
            self.name = name

    def test_register_service(self, container):
        """Test registering a service."""
        container.register(self.TestService)
        assert container.is_registered(self.TestService)

    def test_resolve_service(self, container):
        """Test resolving a service."""
        container.register(self.TestService)
        instance = container.resolve(self.TestService)
        assert isinstance(instance, self.TestService)

    def test_resolve_not_registered_fails(self, container):
        """Test resolving unregistered service raises error."""
        with pytest.raises(ServiceNotFoundError):
            container.resolve(self.TestService)

    def test_duplicate_registration_fails(self, container):
        """Test duplicate service registration fails."""
        container.register(self.TestService)
        with pytest.raises(DuplicateServiceError):
            container.register(self.TestService)

    def test_singleton_lifetime(self, container):
        """Test singleton lifetime creates single instance."""
        container.register(
            self.TestService,
            lifetime=ServiceLifetime.SINGLETON,
        )
        
        instance1 = container.resolve(self.TestService)
        instance2 = container.resolve(self.TestService)
        
        assert instance1 is instance2

    def test_transient_lifetime(self, container):
        """Test transient lifetime creates new instances."""
        container.register(
            self.TestService,
            lifetime=ServiceLifetime.TRANSIENT,
        )
        
        instance1 = container.resolve(self.TestService)
        instance2 = container.resolve(self.TestService)
        
        assert instance1 is not instance2

    def test_register_singleton_instance(self, container):
        """Test registering singleton instance."""
        instance = self.TestService(name="singleton")
        container.register_singleton(self.TestService, instance=instance)
        
        resolved = container.resolve(self.TestService)
        assert resolved is instance
        assert resolved.name == "singleton"

    def test_unregister_service(self, container):
        """Test unregistering a service."""
        container.register(self.TestService)
        assert container.is_registered(self.TestService)
        
        container.unregister(self.TestService)
        assert not container.is_registered(self.TestService)

    def test_get_registered_services(self, container):
        """Test getting list of registered services."""
        container.register(self.TestService)
        services = container.get_registered_services()
        assert "TestService" in services

    def test_clear_container(self, container):
        """Test clearing all services."""
        container.register(self.TestService)
        container.clear()
        assert not container.is_registered(self.TestService)


# ============================================================================
# CONTEXT MANAGEMENT TESTS
# ============================================================================


class TestOperationContext:
    """Test operation context."""

    def test_create_context(self):
        """Test creating operation context."""
        ctx = OperationContext(user_id="user123")
        assert ctx.user_id == "user123"
        assert ctx.operation_id is not None
        assert ctx.correlation_id is not None

    def test_set_and_get_value(self):
        """Test setting and getting context values."""
        ctx = OperationContext()
        ctx.set_value("stage", "processing")
        assert ctx.get_value("stage") == "processing"

    def test_get_missing_value_raises_error(self):
        """Test getting missing value raises error."""
        ctx = OperationContext()
        with pytest.raises(ContextNotFoundError):
            ctx.get_value("missing")

    def test_get_missing_value_with_default(self):
        """Test getting missing value with default."""
        ctx = OperationContext()
        value = ctx.get_value("missing", default="default_value")
        assert value == "default_value"

    def test_has_value(self):
        """Test checking if value exists."""
        ctx = OperationContext()
        assert not ctx.has_value("key")
        ctx.set_value("key", "value")
        assert ctx.has_value("key")

    def test_context_to_dict(self):
        """Test converting context to dictionary."""
        ctx = OperationContext(user_id="user123")
        data = ctx.to_dict()
        assert data["user_id"] == "user123"
        assert "operation_id" in data
        assert "correlation_id" in data

    @pytest.mark.asyncio
    async def test_context_scope(self):
        """Test context scope manager."""
        async with context_scope(user_id="user123") as ctx:
            current = ContextManager.current_context()
            assert current.user_id == "user123"
        
        # Context should be cleared after scope
        assert ContextManager.get_context() is None

    @pytest.mark.asyncio
    async def test_get_correlation_id(self):
        """Test getting correlation ID from context."""
        async with context_scope() as ctx:
            correlation_id = get_correlation_id()
            assert correlation_id == ctx.correlation_id


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================


class TestHealthCheckRegistry:
    """Test health check registry."""

    @pytest.fixture
    def registry(self):
        """Create registry for testing."""
        return HealthCheckRegistry()

    @pytest.mark.asyncio
    async def test_register_health_check(self, registry):
        """Test registering health check."""
        async def check_service():
            return {
                "status": HealthStatus.HEALTHY,
                "timestamp": datetime.utcnow().timestamp(),
                "checks": {},
            }
        
        registry.register_check("service", check_service)
        assert "service" in registry._checks

    @pytest.mark.asyncio
    async def test_check_service(self, registry):
        """Test running health check for service."""
        async def check_service():
            return {
                "status": HealthStatus.HEALTHY,
                "timestamp": datetime.utcnow().timestamp(),
                "checks": {"service": "ok"},
            }
        
        registry.register_check("service", check_service)
        result = await registry.check_service("service")
        
        assert result["status"] == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_check_all(self, registry):
        """Test running all health checks."""
        async def check1():
            return {
                "status": HealthStatus.HEALTHY,
                "timestamp": datetime.utcnow().timestamp(),
                "checks": {},
            }
        
        async def check2():
            return {
                "status": HealthStatus.HEALTHY,
                "timestamp": datetime.utcnow().timestamp(),
                "checks": {},
            }
        
        registry.register_check("service1", check1)
        registry.register_check("service2", check2)
        
        results = await registry.check_all()
        assert len(results) == 2
        assert "service1" in results
        assert "service2" in results

    @pytest.mark.asyncio
    async def test_overall_status_healthy(self, registry):
        """Test overall status when all services healthy."""
        async def check():
            return {
                "status": HealthStatus.HEALTHY,
                "timestamp": datetime.utcnow().timestamp(),
                "checks": {},
            }
        
        registry.register_check("service", check)
        await registry.check_all()
        
        status = await registry.get_overall_status()
        assert status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_overall_status_unhealthy(self, registry):
        """Test overall status when any service unhealthy."""
        async def check_healthy():
            return {
                "status": HealthStatus.HEALTHY,
                "timestamp": datetime.utcnow().timestamp(),
                "checks": {},
            }
        
        async def check_unhealthy():
            return {
                "status": HealthStatus.UNHEALTHY,
                "timestamp": datetime.utcnow().timestamp(),
                "checks": {},
            }
        
        registry.register_check("service1", check_healthy)
        registry.register_check("service2", check_unhealthy)
        await registry.check_all()
        
        status = await registry.get_overall_status()
        assert status == HealthStatus.UNHEALTHY


# ============================================================================
# RESULT TYPE TESTS
# ============================================================================


class TestResultTypes:
    """Test Ok/Err result types."""

    def test_ok_result(self):
        """Test Ok result."""
        result = Ok("success")
        assert result.is_ok()
        assert not result.is_err()
        assert result.unwrap() == "success"

    def test_err_result(self):
        """Test Err result."""
        error = ValueError("error")
        result = Err(error)
        assert not result.is_ok()
        assert result.is_err()
        
        with pytest.raises(ValueError):
            result.unwrap()

    def test_unwrap_or_ok(self):
        """Test unwrap_or with Ok result."""
        result = Ok("value")
        assert result.unwrap_or("default") == "value"

    def test_unwrap_or_err(self):
        """Test unwrap_or with Err result."""
        result = Err(ValueError())
        assert result.unwrap_or("default") == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
