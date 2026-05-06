"""Main orchestration layer for dispatching orders."""

from __future__ import annotations

from typing import Optional

from core.optimizer import SimulatedAnnealingOptimizer
from core.state_manager import StateManager
from models.environment import EnvironmentGraph
from utils.logger import get_logger
from utils.metrics import MetricsCalculator

logger = get_logger(__name__)


class Dispatcher:
    """Coordinates state, optimization, and dispatch cycles."""

    def __init__(
        self,
        state_manager: StateManager,
        optimizer: SimulatedAnnealingOptimizer,
        environment: EnvironmentGraph,
        metrics: Optional[MetricsCalculator] = None,
    ) -> None:
        self._state_manager = state_manager
        self._optimizer = optimizer
        self._environment = environment
        self._metrics = metrics or MetricsCalculator()
        self._running = False

    def dispatch_once(self) -> None:
        """Run a single dispatch cycle.
        
        Steps:
        1. Collect current agents and pending orders from state
        2. Run optimizer to compute assignments
        3. Apply assignments to state
        4. Log results and metrics
        """
        # Collect state
        agents = self._state_manager.list_agents()
        pending_orders = self._state_manager.list_pending_orders()
        
        if not agents:
            logger.warning("No agents available for dispatch")
            return
        
        if not pending_orders:
            logger.info("No pending orders for dispatch")
            return
        
        logger.info(f"Dispatch cycle: {len(agents)} agents, {len(pending_orders)} pending orders")
        
        # Run optimizer
        result = self._optimizer.optimize(agents, pending_orders, self._environment)
        
        # Apply assignments
        assignments_made = 0
        for order_id, agent_id in result.assignments.items():
            self._state_manager.assign_order(order_id, agent_id)
            assignments_made += 1
            logger.info(f"  → Assigned {order_id} to {agent_id}")
        
        logger.info(f"Dispatch cycle complete: {assignments_made} assignments made")
        logger.info(f"Optimization score: {result.score:.2f}")
        logger.info(f"Latency: {result.metadata.get('latency_ms', 0):.2f}ms")

    def start(self) -> None:
        """Start continuous dispatching."""
        self._running = True
        logger.info("Dispatcher started (continuous mode)")

    def stop(self) -> None:
        """Stop continuous dispatching."""
        self._running = False
        logger.info("Dispatcher stopped")
