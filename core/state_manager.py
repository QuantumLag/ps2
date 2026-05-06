import pandas as pd
import heapq
from typing import Dict, List, Tuple, Optional

class StateManager:
    def __init__(self, agents_path: str, constraints_path: str):
        """
        Initializes the system by loading the actual dataset files.
        Addresses Issue 2 & 5.
        """
        # Load the physical fleet and the operational rules[cite: 1]
        self.agents_df = pd.read_csv(agents_path)
        self.constraints = pd.read_csv(constraints_path).set_index('constraint')['value'].to_dict()
        
        # Dynamically set capacity from constraints.csv[cite: 1]
        self.max_capacity = int(self.constraints.get('max_active_orders_per_agent', 2))
        
        # Issue 5: The Agent Registry (The Status Board)[cite: 1]
        self.agent_registry = {}
        for _, row in self.agents_df.iterrows():
            self.agent_registry[row['agent_id']] = {
                "pos": (row['current_x'], row['current_y']),
                "rating": row['rating'],
                "active_orders": [],  # List of current order_ids being carried[cite: 1]
                "completed_count": 0
            }
            
        # Issue 4: The Priority Queue[cite: 1]
        self.order_queue = []
        self.priority_map = {"high": 0, "normal": 1, "low": 2}

    def load_orders(self, orders_path: str):
        """
        Issue 1: Loads orders from CSV and organizes them by importance.
        Addresses Issue 4 (Sorting) and Issue 16 (Validation)[cite: 1].
        """
        orders_df = pd.read_csv(orders_path)
        for _, row in orders_df.iterrows():
            # Map priority labels to numbers for the heap sort[cite: 1]
            p_val = self.priority_map.get(str(row['priority']).lower(), 1)
            
            # The heap stores: (Priority Rank, Timestamp, Order ID, Full Data)[cite: 1]
            order_data = row.to_dict()
            heapq.heappush(self.order_queue, (p_val, row['timestamp'], row['order_id'], order_data))

    def get_next_order(self) -> Optional[dict]:
        """Pops the most urgent order from the top of the heap[cite: 1]."""
        if self.order_queue:
            return heapq.heappop(self.order_queue)[3]
        return None

    def get_available_agents(self) -> List[str]:
        """
        Issue 6 & 11: Returns IDs of agents who have room for more orders.
        If this returns an empty list, the system must wait[cite: 1].
        """
        return [aid for aid, info in self.agent_registry.items() 
                if len(info['active_orders']) < self.max_capacity]

    def apply_assignment(self, agent_id: str, order_id: str):
        """
        Issue 9: Officially links an agent to an order.
        Increments load and validates capacity[cite: 1].
        """
        if agent_id in self.agent_registry:
            agent = self.agent_registry[agent_id]
            if len(agent['active_orders']) < self.max_capacity:
                agent['active_orders'].append(order_id)
                return True
        return False

    def complete_delivery(self, agent_id: str, order_id: str, destination: Tuple[int, int]):
        """
        Issue 10: Called by Teammate B when a delivery is finished.
        Frees up capacity and updates the agent's new location[cite: 1].
        """
        agent = self.agent_registry[agent_id]
        if order_id in agent['active_orders']:
            agent['active_orders'].remove(order_id)
            agent['pos'] = destination
            agent['completed_count'] += 1