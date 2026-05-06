"""Agent domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Agent:
    """Represents a delivery agent with capacity and rating."""

    agent_id: str
    name: str
    capacity: int
    rating: float
    current_load: int = 0
    tags: List[str] = field(default_factory=list)

    def can_accept(self, order_load: int) -> bool:
        """Return True if the agent can accept an order with the given load."""
        # TODO: Implement capacity and eligibility checks.
        return False

    def assign(self, order_id: str, order_load: int) -> None:
        """Assign an order to this agent and update its load."""
        # TODO: Implement assignment side effects.
        pass

    def release(self, order_id: str, order_load: int) -> None:
        """Release an order from this agent and update its load."""
        # TODO: Implement release side effects.
        pass
