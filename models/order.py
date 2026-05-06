"""Order domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Order:
    """Represents a delivery order with priority and SLA tracking."""

    order_id: str
    priority: int
    sla_deadline: datetime
    pickup_node: str
    dropoff_node: str
    weight: int
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    assigned_agent_id: Optional[str] = None

    def is_overdue(self, now: Optional[datetime] = None) -> bool:
        """Return True if the order's SLA deadline has passed."""
        # TODO: Implement SLA overdue check.
        return False
