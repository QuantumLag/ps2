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

    def get_available_agents(self) -> List[Agent]:
        """
        Issue 6: Filters the registry for agents who can accept more orders.
        Uses the teammate's model method: can_accept()[cite: 3, 7].
        """
        return [a for a in self.agents.values() if a.can_accept()]

    def get_next_batch(self, batch_size: int = 10) -> List[Order]:
        """
        Pops the top 'N' orders from the heap to send to the Optimizer.
        Allows the 'Quantum' math to look at a cluster of orders.
        """
        batch = []
        for _ in range(min(batch_size, len(self.order_queue))):
            batch.append(heapq.heappop(self.order_queue)[2])
        return batch

    def apply_assignments(self, assignments: Dict[str, str]):
        """
        Issue 9: Officially links an Agent ID to an Order ID.
        Updates the agent's internal list of active_orders[cite: 4, 7].
        """
        for order_id, agent_id in assignments.items():
            agent = self.agents.get(agent_id)
            if agent and agent.can_accept():
                agent.assign_order(order_id) # Updates load and availability