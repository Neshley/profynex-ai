"""Guide to using the Core Infrastructure Module.

This guide covers all components of the core infrastructure and how to use them
in your own code.
"""

# ============================================================================
# TABLE OF CONTENTS
# ============================================================================
# 1. Exception Handling
# 2. Event System
# 3. Dependency Injection
# 4. Context Management
# 5. Health Checks
# 6. Type System
# 7. Integration Example


# ============================================================================
# 1. EXCEPTION HANDLING
# ============================================================================

"""
The exception system provides semantic error codes and context.

Key Benefits:
- Specific error codes for programmatic handling
- Automatic recovery suggestions
- Full context preservation
- Serializable for logging/APIs
- Error hierarchy for targeted handling
"""

# Basic usage
from src.core.exceptions import (
    ProfynexException,
    MissingConfigurationError,
    InvalidConfigurationError,
    ServiceNotFoundError,
)

# Example: Creating custom exceptions
try:
    # Simulating missing config
    api_key = None
    if not api_key:
        raise MissingConfigurationError(config_key="OPENAI_API_KEY")
except MissingConfigurationError as e:
    print(f"Error: {e.message}")
    print(f"Code: {e.code}")
    print(f"Suggestion: {e.recovery_suggestion}")
    print(f"Severity: {e.severity.value}")

# Example: Exception serialization for logging
try:
    raise InvalidConfigurationError(
        config_key="PORT",
        expected_type="int",
        actual_value="invalid",
    )
except ProfynexException as e:
    error_data = e.to_dict()
    # Send to logging service
    print(error_data)
    # Output: {'type': 'InvalidConfigurationError', 'message': '...', 'code': 'CONFIG_003', ...}

# Example: Wrapping exceptions
try:
    try:
        # Some operation
        result = int("invalid")
    except ValueError as e:
        # Wrap in custom exception with additional context
        raise ProfynexException(
            message="Failed to parse configuration value",
            code="PARSE_ERROR",
            context={"input": "invalid"},
            original_error=e,
        )
except ProfynexException as e:
    print(f"Original error: {e.original_error}")


# ============================================================================
# 2. EVENT SYSTEM
# ============================================================================

"""
The event system enables loose coupling between modules.
Modules communicate by publishing and subscribing to events.

Key Benefits:
- Loose coupling (modules don't know about each other)
- Asynchronous communication
- Easy to test (can publish events without real implementations)
- Extensible (add handlers without modifying source)
"""

import asyncio
from src.core.events import EventBus, get_event_bus
from src.core.types import Event


async def event_system_example():
    # Get the global event bus
    bus = await get_event_bus()
    
    # Register event types
    await bus.register_event("user.spoke")
    await bus.register_event("vision.screen_updated")
    await bus.register_event("memory.stored")
    
    # Subscribe to an event
    async def handle_user_spoke(event: Event):
        text = event.data.get("text")
        print(f"User said: {text}")
        # Parse the text and determine what to do
        # This might trigger other events
    
    # Subscribe with a named handler (for debugging)
    unsubscribe = await bus.subscribe(
        "user.spoke",
        handle_user_spoke,
        handler_name="ConversationHandler"
    )
    
    # Subscribe multiple handlers to same event
    async def log_user_input(event: Event):
        print(f"Logging input: {event.data}")
    
    await bus.subscribe(
        "user.spoke",
        log_user_input,
        handler_name="LoggingHandler"
    )
    
    # Publish an event
    event = Event(
        "user.spoke",
        data={"text": "Hello, Aurora"},
        source="voice_module",
    )
    
    # Wait for handlers to complete
    await bus.publish(event, wait_for_handlers=True)
    
    # Or publish without waiting (background processing)
    await bus.publish(event, wait_for_handlers=False)
    
    # Unsubscribe when done
    await unsubscribe()
    
    # Get subscriber count
    count = await bus.get_subscriber_count("user.spoke")
    print(f"Subscribers to 'user.spoke': {count}")


# ============================================================================
# 3. DEPENDENCY INJECTION
# ============================================================================

"""
Dependency injection enables loose coupling and easy testing.
Services are registered once and resolved as needed.

Key Benefits:
- Loose coupling between services
- Easy to test (inject mocks)
- Automatic dependency resolution
- Configurable lifetimes (singleton, transient, scoped)
"""

from src.core.container import Container, ServiceLifetime


class DatabaseService:
    """Example database service."""
    async def connect(self):
        print("Connecting to database...")
    
    async def query(self, sql: str):
        return [{"id": 1, "name": "test"}]


class ConversationRepository:
    """Repository that depends on database."""
    def __init__(self, db: DatabaseService):
        self.db = db
    
    async def get_conversation(self, user_id: str):
        return await self.db.query(
            f"SELECT * FROM conversations WHERE user_id = '{user_id}'"
        )


class ConversationService:
    """Service that depends on repository."""
    def __init__(self, repo: ConversationRepository):
        self.repo = repo
    
    async def get_user_history(self, user_id: str):
        return await self.repo.get_conversation(user_id)


# Set up dependency injection
container = Container()

# Register services with different lifetimes
container.register(
    DatabaseService,
    lifetime=ServiceLifetime.SINGLETON,  # Single instance for entire app
)

container.register(
    ConversationRepository,
    lifetime=ServiceLifetime.TRANSIENT,  # New instance each time
)

container.register(
    ConversationService,
    lifetime=ServiceLifetime.SINGLETON,  # Single instance for entire app
)

# Resolve service (dependencies injected automatically)
service = container.resolve(ConversationService)

# Check if service is registered
if container.is_registered(DatabaseService):
    print("Database service is registered")

# Get list of all registered services
services = container.get_registered_services()
print(f"Registered services: {services}")

# Unregister service
container.unregister(DatabaseService)

# Clear all services
container.clear()

# Register singleton instance
db_instance = DatabaseService()
container.register_singleton(
    DatabaseService,
    instance=db_instance,
)

# Or register with factory function
def create_database():
    db = DatabaseService()
    # Do some initialization
    return db

container.register(
    DatabaseService,
    factory=create_database,
    lifetime=ServiceLifetime.SINGLETON,
)


# ============================================================================
# 4. CONTEXT MANAGEMENT
# ============================================================================

"""
Context management tracks operation metadata across async calls.
Useful for correlation IDs, user info, and request-scoped data.

Key Benefits:
- Track operations across module boundaries
- Correlation IDs for debugging
- Request-scoped data without passing through functions
- Async-safe with proper cleanup
"""

from src.core.context import (
    OperationContext,
    ContextManager,
    context_scope,
    get_correlation_id,
    get_operation_id,
    get_user_id,
)


async def context_example():
    # Create operation context manually
    ctx = OperationContext(
        user_id="user123",
        session_id="session456",
    )
    
    # Set context manually
    ContextManager.set_context(ctx)
    
    # Access context from anywhere
    current_ctx = ContextManager.current_context()
    print(f"Operation ID: {current_ctx.operation_id}")
    print(f"Correlation ID: {current_ctx.correlation_id}")
    
    # Get specific values
    correlation_id = get_correlation_id()
    user_id = get_user_id()
    operation_id = get_operation_id()
    
    # Use context_scope for cleaner code
    async with context_scope(
        user_id="user456",
        correlation_id="corr789"
    ) as ctx:
        print(f"Inside scope: {ctx.operation_id}")
        
        # Store custom data
        ctx.set_value("processing_stage", "vision_analysis")
        ctx.set_value("screen_state", "typing")
        
        # Retrieve custom data
        stage = ctx.get_value("processing_stage")
        screen_state = ctx.get_value("screen_state", default="idle")
        
        # Check if value exists
        if ctx.has_value("processing_stage"):
            print(f"Processing: {stage}")
        
        # Create child context
        child_ctx = ContextManager.create_child_context(
            user_id="same_user"
        )
        # Child inherits correlation ID from parent
        print(f"Child correlation ID: {child_ctx.correlation_id}")
    
    # Context automatically cleared after scope
    assert ContextManager.get_context() is None


# ============================================================================
# 5. HEALTH CHECKS
# ============================================================================

"""
Health checks monitor the status of services.
Useful for detecting failures and reporting system status.

Key Benefits:
- Monitor individual service health
- Aggregate overall system status
- Periodic automatic checks
- Easy integration with monitoring systems
"""

from src.core.health import get_health_registry
from src.core.types import HealthStatus
from datetime import datetime


async def health_check_example():
    registry = get_health_registry()
    
    # Define health check for database
    async def check_database_health():
        try:
            # Simulate database connectivity check
            await asyncio.sleep(0.1)
            return {
                "status": HealthStatus.HEALTHY,
                "timestamp": datetime.utcnow().timestamp(),
                "checks": {
                    "connection": "ok",
                    "query_time_ms": 5,
                },
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "timestamp": datetime.utcnow().timestamp(),
                "message": str(e),
                "checks": {"error": str(e)},
            }
    
    # Define health check for memory
    async def check_memory_health():
        # Check if memory usage is acceptable
        try:
            # Simulate memory check
            memory_usage = 65  # percentage
            
            if memory_usage > 90:
                status = HealthStatus.UNHEALTHY
            elif memory_usage > 75:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return {
                "status": status,
                "timestamp": datetime.utcnow().timestamp(),
                "checks": {"memory_usage_percent": memory_usage},
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNKNOWN,
                "timestamp": datetime.utcnow().timestamp(),
                "message": str(e),
            }
    
    # Register health checks
    registry.register_check("database", check_database_health)
    registry.register_check("memory", check_memory_health)
    
    # Check individual service
    db_health = await registry.check_service("database")
    print(f"Database health: {db_health['status']}")
    
    # Check all services
    all_results = await registry.check_all()
    for service, result in all_results.items():
        print(f"{service}: {result['status']}")
    
    # Get overall system status
    overall_status = await registry.get_overall_status()
    print(f"Overall system status: {overall_status}")
    
    # Get health summary
    summary = await registry.get_summary()
    print(f"Health summary: {summary}")
    
    # Set check interval and start periodic checks
    registry.set_check_interval(30.0)  # Check every 30 seconds
    
    # Start periodic health checks (runs in background)
    # await registry.start()
    
    # Later, stop periodic checks
    # await registry.stop()


# ============================================================================
# 6. TYPE SYSTEM
# ============================================================================

"""
The type system provides type hints and protocols for IDE support.
Use these types for full autocomplete and type checking.
"""

from src.core.types import (
    Event,
    EventHandler,
    Ok,
    Err,
    Result,
    HealthStatus,
    HealthCheckResult,
)


# Use Result type for functional error handling
def process_user_input(text: str) -> Result:
    """Process user input, returning Ok or Err."""
    try:
        if not text.strip():
            return Err(ValueError("Input cannot be empty"))
        return Ok(text.strip())
    except Exception as e:
        return Err(e)


# Use result
result = process_user_input("hello")
if result.is_ok():
    text = result.unwrap()
    print(f"Processing: {text}")
else:
    error = result.unwrap_or("Unknown error")
    print(f"Error: {error}")


# ============================================================================
# 7. INTEGRATION EXAMPLE
# ============================================================================

"""
Complete example showing how all components work together.
"""


class Vision:
    """Vision module for screen analysis."""
    def __init__(self, bus: EventBus):
        self.bus = bus
    
    async def analyze_screen(self):
        async with context_scope(
            metadata={"module": "vision"},
        ) as ctx:
            print(f"[Vision] Analyzing screen...")
            
            # Do screen analysis
            await asyncio.sleep(0.1)
            
            # Publish event
            event = Event(
                "vision.screen_updated",
                data={
                    "text": "Welcome to Aurora",
                    "applications": ["VS Code", "Chrome"],
                },
                source="vision",
            )
            await self.bus.publish(event)


class Conversation:
    """Conversation module."""
    def __init__(self, bus: EventBus):
        self.bus = bus
    
    async def initialize(self):
        await self.bus.subscribe(
            "user.spoke",
            self.handle_user_spoke,
            handler_name="ConversationHandler",
        )
        await self.bus.subscribe(
            "vision.screen_updated",
            self.handle_vision_update,
            handler_name="VisionContextUpdater",
        )
    
    async def handle_user_spoke(self, event: Event):
        async with context_scope() as ctx:
            ctx.set_value("processing_stage", "conversation")
            text = event.data.get("text")
            print(f"[Conversation] Processing: {text}")
            await asyncio.sleep(0.1)
    
    async def handle_vision_update(self, event: Event):
        async with context_scope() as ctx:
            ctx.set_value("screen_context", event.data)
            print(f"[Conversation] Screen context updated")


async def main():
    """Main application."""
    # Initialize event bus
    bus = await get_event_bus()
    
    # Register events
    await bus.register_event("user.spoke")
    await bus.register_event("vision.screen_updated")
    
    # Set up health checks
    registry = get_health_registry()
    
    async def check_event_bus():
        return {
            "status": HealthStatus.HEALTHY,
            "timestamp": datetime.utcnow().timestamp(),
            "checks": {"subscribers": await bus.get_subscriber_count("user.spoke")},
        }
    
    registry.register_check("event_bus", check_event_bus)
    
    # Create modules
    vision = Vision(bus)
    conversation = Conversation(bus)
    
    # Initialize
    await conversation.initialize()
    
    # Simulate events
    print("\n=== Simulation ===")
    
    # Vision analyzes screen
    await vision.analyze_screen()
    await asyncio.sleep(0.1)
    
    # User speaks
    user_event = Event(
        "user.spoke",
        data={"text": "What's on my screen?"},
        source="voice",
    )
    await bus.publish(user_event, wait_for_handlers=True)
    
    print("\n=== Health Status ===")
    summary = await registry.get_summary()
    print(f"Overall status: {summary['overall_status']}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())


# ============================================================================
# BEST PRACTICES
# ============================================================================

"""
1. Exception Handling
   - Catch specific exceptions when possible
   - Always include recovery_suggestion in custom exceptions
   - Wrap external errors in ProfynexException

2. Event System
   - Register all events at startup
   - Use descriptive event names (format: "module.action")
   - Keep handlers lightweight (offload heavy work)
   - Always unsubscribe when done with handlers

3. Dependency Injection
   - Register services at application startup
   - Use singletons for expensive resources (DB, API clients)
   - Use transient for stateless services
   - Always register interfaces, not implementations

4. Context Management
   - Use context_scope for all async operations
   - Store correlation IDs for debugging
   - Keep context data lightweight
   - Always clear context after use (context_scope handles this)

5. Health Checks
   - Register health checks for all critical services
   - Make checks fast (set timeout)
   - Include specific details in check results
   - Use DEGRADED status for non-critical issues

6. Type System
   - Always use type hints for function parameters and returns
   - Use Result type for operations that might fail
   - Use Protocol for interface definitions
   - Leverage IDE autocomplete by using proper types
"""
