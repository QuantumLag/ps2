# core/state_manager.py
import heapq
from typing import List, Dict
from models.agent import Agent
from models.order import Order

class StateManager:
    def __init__(self, agents: List[Agent]):
        # Map for O(1) lookup of agents by ID
        self.agents = {a.agent_id: a for a in agents}
        self.order_queue = [] # Our Priority Heap[cite: 4]
        self.priority_map = {"high": 0, "normal": 1, "low": 2}

    def add_orders_to_queue(self, orders: List[Order]):
        """Issue 4: Sorting by Priority then Time[cite: 4]."""
        for order in orders:
            p_val = self.priority_map.get(order.priority.lower(), 1)
            # Heap sorts by priority, then arrival time[cite: 4]
            heapq.heappush(self.order_queue, (p_val, order.timestamp, order))

    def get_pending_orders(self, batch_size: int = 10) -> List[Order]:
        """Returns a batch of the highest priority orders for optimization."""
        batch = []
        for _ in range(min(batch_size, len(self.order_queue))):
            batch.append(heapq.heappop(self.order_queue)[2])
        return batch

    def apply_assignments(self, assignments: Dict[str, str]):
        """Issue 9: Linking orders to agents[cite: 4]."""
        for order_id, agent_id in assignments.items():
            agent = self.agents.get(agent_id)
            if agent:
                agent.assign_order(order_id) # Marks agent as busy[cite: 7]