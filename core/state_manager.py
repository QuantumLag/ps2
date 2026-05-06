import heapq
from typing import List, Dict, Optional
from models.agent import Agent
from models.order import Order

class StateManager:
    """
    The 'Source of Truth' for the system. 
    Manages Issue 4 (Queueing) and Issue 5 (Registry).
    """
    def __init__(self, agents: List[Agent]):
        # Issue 5: Registry of all agents for O(1) lookup[cite: 4, 7]
        self.agents: Dict[str, Agent] = {a.agent_id: a for a in agents}
        
        # Issue 4: Priority Queue (Min-Heap)
        self.order_queue = []
        self.priority_map = {"high": 0, "normal": 1, "low": 2}

    def add_orders_to_queue(self, orders: List[Order]):
        """
        Takes validated Order objects and pushes them into the priority heap.
        Ensures High priority is popped before Normal/Low[cite: 4, 9].
        """
        for order in orders:
            # Map priority labels to integers
            p_rank = self.priority_map.get(order.priority.lower(), 1)
            # Tuple: (priority_rank, arrival_time, order_object)
            heapq.heappush(self.order_queue, (p_rank, order.timestamp, order))

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
