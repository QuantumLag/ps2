"""Metrics calculations for dispatch performance."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from models.agent import Agent
from models.order import Order


class MetricsCalculator:
    """Computes SLA, fairness, and timing metrics."""

    def compute_sla_compliance(self, orders: List[Order], now: Optional[datetime] = None) -> float:
        """Return SLA compliance ratio for a set of orders."""
        # TODO: Implement SLA compliance calculation.
        return 0.0

    def compute_workload_fairness(self, agents: List[Agent]) -> float:
        """Return a fairness score for agent workloads."""
        # TODO: Implement workload fairness calculation.
        return 0.0

    def average_delivery_time(self, orders: List[Order]) -> Optional[float]:
        """Return the average delivery time in minutes if available."""
        # TODO: Implement delivery time calculation.
        return None
