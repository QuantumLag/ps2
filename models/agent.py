"""Agent domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class Agent:
    """Represents a delivery agent with capacity and rating."""

    agent_id: str
    current_location: Tuple[int, int]
    rating: float
    availability: bool = True
    active_orders: List[str] = field(default_factory=list)
    cumulative_assignments: int = 0

    def __post_init__(self) -> None:
        """Validate agent initialization."""
        if not (0.0 <= self.rating <= 5.0):
            raise ValueError(f"Agent rating {self.rating} is out of bounds (0.0 - 5.0).")

    def can_accept(self) -> bool:
        """Return True if the agent has not exceeded the 2-order maximum."""
        # This fulfills the hackathon constraint: "Each agent can handle up to 2 active orders"
        return len(self.active_orders) < 2

    def assign_order(self, order_id: str) -> None:
        """Assign an order to this agent and update state."""
        self.active_orders.append(order_id)
        self.cumulative_assignments += 1
        if not self.can_accept():
            self.availability = False

    def complete_order(self, order_id: str) -> None:
        """Remove a completed order and update availability."""
        if order_id in self.active_orders:
            self.active_orders.remove(order_id)
        self.availability = True
