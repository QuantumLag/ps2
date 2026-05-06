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
    
    def validate_delivery_path(self, agent_id: str, order: Order, environment: EnvironmentGraph) -> bool:
        """
        Check if a path exists before allowing assignment.
        Addresses Issue 17: Graph Connectivity.
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False
            
        # Check if distance lookup returns a valid float (not infinity/null)
        dist = environment.distance(
            f"{agent.current_location[0]},{agent.current_location[1]}", 
            f"{order.location_x},{order.location_y}"
        )
        
        if dist >= float('inf') or dist < 0:
            print(f"CRITICAL: No path from Agent {agent_id} to Order {order.order_id}")
            return False
        return True

    def assign_order(self, order_id: str, agent_id: str) -> None:
        """Record an assignment between an order and an agent."""
        # TODO: Update agent and order states.
        self.active_assignments[order_id] = agent_id

    def release_order(self, order_id: str) -> None:
        """Release an order assignment."""
        # TODO: Update agent and order states.
        self.active_assignments.pop(order_id, None)

    def complete_delivery(self, order: Order, agent_id: str, completion_time: datetime) -> None:
        """
        Transitions an order to DELIVERED and updates agent state.
        Fulfills Issue 10 requirements.
        """
        # SAFETY GUARD (Issue 17)
        agent = self.get_agent(agent_id)
        if not agent:
            print(f"ERROR: Agent {agent_id} not found in registry. Skipping update.")
            return
        # 1. Update Order State
        order.state = "DELIVERED"
        order.actual_delivery_time = completion_time

        # 2. Update Agent State (Issue 5 & 10)
        agent = self.get_agent(agent_id)
        if agent:
            # Move agent physically to the customer's location
            agent.current_location = (order.location_x, order.location_y)
            # Remove from agent's internal list and flip availability back to True
            agent.complete_order(order.order_id)

        # 3. Clean up the Global Registry
        # This removes the order from the "In-Progress" dictionary
        self.release_order(order.order_id)

        # 4. Record SLA Violation (Issue 13)
        # Assuming your Order model has a timestamp and sla_minutes
        deadline = order.timestamp + pd.Timedelta(minutes=order.sla_minutes)
        order.is_sla_violated = completion_time > deadline
        
        if order.is_sla_violated:
            print(f"SLA Violation: {order.order_id} delivered at {completion_time}")    

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Retrieve a registered agent by ID."""
        return self.agent_registry.get(agent_id)

    def list_agents(self) -> List[Agent]:
        """Return all registered agents."""
        return list(self.agent_registry.values())

    def list_pending_orders(self) -> List[Order]:
        """Return pending orders without mutating the queue."""
        return [item[2] for item in self.pending_orders]

def get_optimal_route(self, agent_id: str, new_order: Order, environment: EnvironmentGraph) -> Tuple[List[str], float]:
        """
        Calculates the most efficient sequence for an agent with multiple orders.
        Addresses Issue 19: Dynamic Re-routing.
        """
        agent = self.get_agent(agent_id)
        if not agent or not agent.active_orders:
            # If no active orders, the route is just to the new order
            dist = environment.distance(
                f"{agent.current_location[0]},{agent.current_location[1]}",
                f"{new_order.location[0]},{new_order.location[1]}"
            )
            return [new_order.order_id], dist

        # Existing order details
        current_order_id = agent.active_orders[0]
        current_order = self.get_order_by_id(current_order_id) # Helper needed to fetch Order object
        
        # Define the three points for distance lookup
        start = f"{agent.current_location[0]},{agent.current_location[1]}"
        pos_current = f"{current_order.location[0]},{current_order.location[1]}"
        pos_new = f"{new_order.location[0]},{new_order.location[1]}"

        # Option 1: Finish current delivery, then go to new one
        # Path: Start -> Current -> New
        cost_1 = environment.distance(start, pos_current) + environment.distance(pos_current, pos_new)
        
        # Option 2: Pivot to new delivery, then finish current one
        # Path: Start -> New -> Current
        cost_2 = environment.distance(start, pos_new) + environment.distance(pos_new, pos_current)

        if cost_1 <= cost_2:
            return [current_order_id, new_order.order_id], cost_1
        else:
            return [new_order.order_id, current_order_id], cost_2