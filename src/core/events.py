"""Event system for inter-module communication.

Design Pattern: Publisher-Subscriber (Observer Pattern)
- Modules publish events without knowing who listens
- Modules subscribe to events without knowing who publishes
- Loose coupling enables modularity
"""

import asyncio
from typing import (
    Dict,
    List,
    Set,
    Optional,
    Callable,
    Any,
)
from datetime import datetime
import uuid

from .types import Event, EventHandler
from .exceptions import (
    EventError,
    EventPublishError,
    EventSubscriptionError,
    UnknownEventError,
)
from .logger import get_logger

logger = get_logger(__name__)


class EventBus:
    """Central event bus for publishing and subscribing to events.
    
    Thread-safe and async-safe event distribution system.
    """

    def __init__(self, max_queue_size: int = 1000):
        """Initialize event bus.
        
        Args:
            max_queue_size: Maximum size of event queue per subscriber
        """
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._max_queue_size = max_queue_size
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._registered_events: Set[str] = set()
        self._lock = asyncio.Lock()

    async def register_event(self, event_name: str) -> None:
        """Register a new event type.
        
        Args:
            event_name: Name of the event to register
        """
        async with self._lock:
            self._registered_events.add(event_name)
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            logger.debug(f"Registered event: {event_name}")

    async def subscribe(
        self,
        event_name: str,
        handler: EventHandler,
        handler_name: Optional[str] = None,
    ) -> Callable[[], Any]:
        """Subscribe to an event.
        
        Args:
            event_name: Name of event to subscribe to
            handler: Async function to handle the event
            handler_name: Optional name for debugging
            
        Returns:
            Unsubscribe function to remove handler
            
        Raises:
            UnknownEventError: If event type not registered
            EventSubscriptionError: If subscription fails
        """
        try:
            if event_name not in self._registered_events:
                raise UnknownEventError(event_name)

            async with self._lock:
                if event_name not in self._subscribers:
                    self._subscribers[event_name] = []

                self._subscribers[event_name].append(handler)

            handler_display = handler_name or getattr(handler, "__name__", "<unknown>")
            logger.debug(
                f"Subscribed handler '{handler_display}' to event '{event_name}'"
            )

            # Return unsubscribe function
            async def unsubscribe() -> None:
                await self.unsubscribe(event_name, handler)

            return unsubscribe

        except UnknownEventError:
            raise
        except Exception as e:
            handler_display = handler_name or getattr(handler, "__name__", "<unknown>")
            raise EventSubscriptionError(
                event_name=event_name,
                handler_name=handler_display,
                reason=str(e),
                original_error=e,
            )

    async def unsubscribe(
        self,
        event_name: str,
        handler: EventHandler,
    ) -> None:
        """Unsubscribe from an event.
        
        Args:
            event_name: Name of event
            handler: Handler function to remove
        """
        try:
            async with self._lock:
                if event_name in self._subscribers:
                    # Remove handler by identity
                    self._subscribers[event_name] = [
                        h for h in self._subscribers[event_name] if h is not handler
                    ]
                    logger.debug(
                        f"Unsubscribed handler from event '{event_name}'"
                    )
        except Exception as e:
            logger.error(f"Error unsubscribing from event '{event_name}': {e}")

    async def publish(
        self,
        event: Event,
        wait_for_handlers: bool = False,
    ) -> None:
        """Publish an event to all subscribers.
        
        Args:
            event: Event to publish
            wait_for_handlers: If True, wait for all handlers to complete
                             If False, handlers run in background
                             
        Raises:
            UnknownEventError: If event type not registered
            EventPublishError: If publishing fails
        """
        try:
            if event.name not in self._registered_events:
                raise UnknownEventError(event.name)

            if not event.correlation_id:
                event.correlation_id = str(uuid.uuid4())

            handlers = self._subscribers.get(event.name, [])

            if not handlers:
                logger.debug(f"Published event '{event.name}' with no subscribers")
                return

            logger.debug(
                f"Publishing event '{event.name}' to {len(handlers)} handlers"
            )

            # Create tasks for all handlers
            tasks = [self._call_handler(handler, event) for handler in handlers]

            if wait_for_handlers:
                # Wait for all handlers
                await asyncio.gather(*tasks, return_exceptions=True)
            else:
                # Schedule handlers as background tasks
                for task in tasks:
                    asyncio.create_task(task)

        except UnknownEventError:
            raise
        except Exception as e:
            raise EventPublishError(
                event_name=event.name,
                reason=str(e),
                original_error=e,
            )

    async def _call_handler(
        self,
        handler: EventHandler,
        event: Event,
    ) -> None:
        """Safely call a handler with exception handling.
        
        Args:
            handler: Handler function
            event: Event to pass to handler
        """
        try:
            await handler(event)
        except Exception as e:
            handler_name = getattr(handler, "__name__", "<unknown>")
            logger.error(
                f"Error in handler '{handler_name}' for event '{event.name}': {e}",
                exc_info=True,
            )

    async def get_subscriber_count(self, event_name: str) -> int:
        """Get number of subscribers to an event.
        
        Args:
            event_name: Event name
            
        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event_name, []))

    async def get_registered_events(self) -> List[str]:
        """Get list of registered event names.
        
        Returns:
            List of event names
        """
        return list(self._registered_events)

    async def clear(self) -> None:
        """Clear all subscribers and events."""
        async with self._lock:
            self._subscribers.clear()
            self._registered_events.clear()
            logger.debug("Cleared all events and subscribers")


# Global event bus instance
_event_bus: Optional[EventBus] = None


async def get_event_bus() -> EventBus:
    """Get or create the global event bus.
    
    Returns:
        Global EventBus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def initialize_event_bus() -> EventBus:
    """Initialize the global event bus.
    
    Returns:
        Initialized EventBus
    """
    global _event_bus
    _event_bus = EventBus()
    logger.info("Event bus initialized")
    return _event_bus
