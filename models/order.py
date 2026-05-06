"""Order domain model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

@dataclass
class Order:
    """Represents a delivery order with priority and SLA tracking."""
    
    order_id: str
    timestamp: datetime
    location: Tuple[int, int]
    prep_time_minutes: int
    priority: str
    sla_minutes: int
    status: str = "PENDING"
    assigned_agent_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate fields immediately upon instantiation."""
        if self.priority.lower() not in ["high", "normal", "low"]:
            raise ValueError(f"Invalid priority level: {self.priority}")
        if self.prep_time_minutes < 0 or self.sla_minutes < 0:
            raise ValueError("Time values cannot be negative.")

    def is_overdue(self, current_time: datetime) -> bool:
        """Return True if the order's SLA deadline has passed."""
        elapsed_time = (current_time - self.timestamp).total_seconds() / 60.0
        return elapsed_time > self.sla_minutes