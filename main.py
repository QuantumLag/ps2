"""Entry point for the Smart Delivery Dispatch System."""

from __future__ import annotations

from pathlib import Path

from core.dispatcher import Dispatcher
from core.optimizer import SimulatedAnnealingOptimizer
from core.state_manager import StateManager
from data.loader import DataLoader
from models.agent import Agent
from models.order import Order
from models.environment import EnvironmentGraph
from utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
	"""Bootstrap the dispatch system and run a dispatch cycle."""
	logger.info("=" * 70)
	logger.info("Smart Delivery Dispatch System - Starting")
	logger.info("=" * 70)
	
	# Paths to data files
	data_dir = Path(__file__).parent / "data" / "raw"
	agents_path = data_dir / "agents.csv"
	orders_path = data_dir / "orders.csv"
	environment_path = data_dir / "environment_edges.csv"
	constraints_path = data_dir / "constraints.csv"
	
	try:
		# Load data
		logger.info("Loading data from CSV files...")
		loader = DataLoader()
		
		# Initialize state manager with data paths
		state_manager = StateManager(
			agents_path=str(agents_path),
			constraints_path=str(constraints_path)
		)
		logger.info(f"✓ Loaded {len(state_manager.agent_registry)} agents")
		
		# Load orders into queue
		state_manager.load_orders(str(orders_path))
		logger.info(f"✓ Loaded {len(state_manager.order_queue)} orders")
		
		# Load environment
		environment = loader.load_environment(str(environment_path))
		logger.info(f"✓ Loaded environment with {len(environment.nodes)} nodes")
		
		# Convert agent registry to Agent objects for optimizer
		agents_for_optimizer = []
		for agent_id, agent_info in state_manager.agent_registry.items():
			agent = Agent(
				agent_id=agent_id,
				current_location=agent_info["pos"],
				rating=agent_info["rating"],
				active_orders=agent_info["active_orders"],
				cumulative_assignments=agent_info["completed_count"]
			)
			agents_for_optimizer.append(agent)
		
		# Convert order queue to Order objects for optimizer
		orders_for_optimizer = []
		# Make a copy to avoid modifying the original queue
		import heapq
		temp_queue = list(state_manager.order_queue)
		for priority, timestamp, order_id, order_data in temp_queue:
			from datetime import datetime
			order = Order(
				order_id=order_data.get('order_id', order_id),
				timestamp=datetime.now(),  # Use current time for now
				location=(order_data.get('location_x', 0), order_data.get('location_y', 0)),
				prep_time_minutes=int(order_data.get('prep_time_minutes', 10)),
				priority=order_data.get('priority', 'normal'),
				sla_minutes=int(order_data.get('sla_minutes', 60))
			)
			orders_for_optimizer.append(order)
		
		logger.info(f"✓ Converted {len(agents_for_optimizer)} agents and {len(orders_for_optimizer)} orders")
		
		# Initialize optimizer and dispatcher
		optimizer = SimulatedAnnealingOptimizer()
		dispatcher = Dispatcher(state_manager, optimizer, environment)
		logger.info("✓ Dispatcher initialized")
		
		# Run a single dispatch cycle
		logger.info("\n" + "=" * 70)
		logger.info("Running dispatch cycle...")
		logger.info("=" * 70)
		
		# Run optimizer manually
		result = optimizer.optimize(agents_for_optimizer, orders_for_optimizer, environment)
		
		# Apply assignments from optimizer result
		assignments_made = 0
		for order_id, agent_id in result.assignments.items():
			success = state_manager.apply_assignment(agent_id, order_id)
			if success:
				assignments_made += 1
				logger.info(f"  → Assigned {order_id} to {agent_id}")
		
		# Display results
		logger.info("\n" + "=" * 70)
		logger.info("Dispatch Cycle Complete")
		logger.info("=" * 70)
		logger.info(f"Assignments made: {assignments_made}")
		logger.info(f"Optimization score: {result.score:.2f}")
		logger.info(f"Latency: {result.metadata.get('latency_ms', 0):.2f}ms")
		
		# Show agent loads
		logger.info("\nAgent Loads:")
		for agent_id, agent_info in state_manager.agent_registry.items():
			load = len(agent_info['active_orders'])
			logger.info(f"  • {agent_id}: {load}/{state_manager.max_capacity} orders")
		
		logger.info("\n✓ System ready for continuous dispatch")
		
	except FileNotFoundError as e:
		logger.error(f"Data file not found: {e}")
		logger.info("\nTrying with mock data instead...")
		
		# Fallback: use mock data
		state_manager = StateManager(agents_path="", constraints_path="")
		optimizer = SimulatedAnnealingOptimizer()
		environment = EnvironmentGraph(nodes=[], edges={})
		dispatcher = Dispatcher(state_manager, optimizer, environment)
		
		logger.info("✓ System initialized with empty state (ready for data injection)")
		
	except Exception as e:
		logger.error(f"Error during startup: {e}", exc_info=True)
		raise


if __name__ == "__main__":
	main()