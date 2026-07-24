"""Health check system for monitoring service health.

Design Pattern: Health Check Pattern
- Register health checks for services
- Perform periodic health checks
- Report overall system health
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from enum import Enum

from .types import HealthStatus, HealthCheckResult, HealthCheck
from .exceptions import ServiceUnhealthyError
from .logger import get_logger

logger = get_logger(__name__)


class HealthCheckRegistry:
    """Registry for health checks.
    
    Manages and runs health checks for all services.
    """

    def __init__(self):
        """Initialize health check registry."""
        self._checks: Dict[str, HealthCheck] = {}
        self._last_results: Dict[str, HealthCheckResult] = {}
        self._check_interval: float = 30.0  # seconds
        self._running: bool = False

    def register_check(
        self,
        service_name: str,
        check: HealthCheck,
    ) -> None:
        """Register a health check for a service.
        
        Args:
            service_name: Name of the service
            check: Async callable that returns HealthCheckResult
        """
        self._checks[service_name] = check
        logger.debug(f"Registered health check for service '{service_name}'")

    def unregister_check(self, service_name: str) -> None:
        """Unregister a health check.
        
        Args:
            service_name: Name of the service
        """
        if service_name in self._checks:
            del self._checks[service_name]
            logger.debug(f"Unregistered health check for service '{service_name}'")

    async def check_service(
        self,
        service_name: str,
    ) -> Optional[HealthCheckResult]:
        """Run health check for a specific service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Health check result or None if no check registered
        """
        if service_name not in self._checks:
            return None

        try:
            check = self._checks[service_name]
            result = await check()
            self._last_results[service_name] = result
            return result
        except Exception as e:
            logger.error(
                f"Health check failed for service '{service_name}': {e}",
                exc_info=True,
            )
            result: HealthCheckResult = {
                "status": HealthStatus.UNHEALTHY,
                "timestamp": datetime.utcnow().timestamp(),
                "checks": {"error": str(e)},
                "message": f"Health check failed: {e}",
            }
            self._last_results[service_name] = result
            return result

    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks.
        
        Returns:
            Dictionary of results by service name
        """
        logger.debug(f"Running {len(self._checks)} health checks")

        tasks = {
            name: self.check_service(name)
            for name in self._checks.keys()
        }

        results = {}
        for name, task in tasks.items():
            result = await task
            if result:
                results[name] = result

        return results

    async def get_overall_status(self) -> HealthStatus:
        """Get overall system health status.
        
        Returns:
            Overall health status
        """
        if not self._last_results:
            return HealthStatus.UNKNOWN

        # Check if any service is unhealthy
        for result in self._last_results.values():
            if result["status"] == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY

        # Check if any service is degraded
        for result in self._last_results.values():
            if result["status"] == HealthStatus.DEGRADED:
                return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    async def get_summary(self) -> Dict[str, Any]:
        """Get health check summary.
        
        Returns:
            Summary dictionary
        """
        overall_status = await self.get_overall_status()
        
        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": self._last_results,
            "service_count": len(self._checks),
        }

    def set_check_interval(self, interval: float) -> None:
        """Set the interval for automatic health checks.
        
        Args:
            interval: Interval in seconds
        """
        self._check_interval = interval
        logger.debug(f"Set health check interval to {interval} seconds")

    async def start(self) -> None:
        """Start periodic health checks."""
        if self._running:
            return

        self._running = True
        logger.info("Starting periodic health checks")
        
        while self._running:
            try:
                await self.check_all()
            except Exception as e:
                logger.error(f"Error during periodic health check: {e}", exc_info=True)
            
            await asyncio.sleep(self._check_interval)

    async def stop(self) -> None:
        """Stop periodic health checks."""
        self._running = False
        logger.info("Stopped periodic health checks")


# Global health check registry
_health_registry: Optional[HealthCheckRegistry] = None


def get_health_registry() -> HealthCheckRegistry:
    """Get or create the global health check registry.
    
    Returns:
        Global HealthCheckRegistry instance
    """
    global _health_registry
    if _health_registry is None:
        _health_registry = HealthCheckRegistry()
    return _health_registry
