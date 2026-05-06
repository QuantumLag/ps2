"""Main orchestration layer for dispatching orders."""

from __future__ import annotations

from typing import Optional

from core.optimizer import SimulatedAnnealingOptimizer
from core.state_manager import StateManager
from models.environment import EnvironmentGraph
from utils.metrics import MetricsCalculator


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
        """Run a single dispatch cycle."""
        # TODO: Collect state, run optimizer, and update assignments.
        pass

    def start(self) -> None:
        """Start continuous dispatching."""
        # TODO: Implement continuous dispatch loop.
        self._running = True

    def stop(self) -> None:
        """Stop continuous dispatching."""
        self._running = False
