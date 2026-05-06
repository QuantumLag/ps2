"""State management for agents, orders, and assignments."""

from __future__ import annotations

import heapq
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple

from models.agent import Agent
from models.order import Order


class StateManager:
    """Tracks agents, orders, and current assignments."""

    def __init__(self) -> None:
        self.agent_registry: Dict[str, Agent] = {}
        self.pending_orders: List[Tuple[int, int, Order]] = []
        self.active_assignments: Dict[str, str] = {}
        self._sequence_counter: int = 0

    def register_agent(self, agent: Agent) -> None:
        """Register a new agent with the system."""
        # TODO: Add validation and duplicate handling.
        self.agent_registry[agent.agent_id] = agent

    def add_order(self, order: Order) -> None:
        """Add an order to the priority queue."""
        # TODO: Implement priority and SLA-aware ordering.
        self._sequence_counter += 1
        heapq.heappush(self.pending_orders, (-order.priority, self._sequence_counter, order))

    def pop_next_order(self) -> Optional[Order]:
        """Pop the next order from the priority queue."""
        if not self.pending_orders:
            return None
        return heapq.heappop(self.pending_orders)[2]

    def assign_order(self, order_id: str, agent_id: str) -> None:
        """Record an assignment between an order and an agent."""
        # TODO: Update agent and order states.
        self.active_assignments[order_id] = agent_id

    def release_order(self, order_id: str) -> None:
        """Release an order assignment."""
        # TODO: Update agent and order states.
        self.active_assignments.pop(order_id, None)

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Retrieve a registered agent by ID."""
        return self.agent_registry.get(agent_id)

    def list_agents(self) -> List[Agent]:
        """Return all registered agents."""
        return list(self.agent_registry.values())

    def list_pending_orders(self) -> List[Order]:
        """Return pending orders without mutating the queue."""
        return [item[2] for item in self.pending_orders]
