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
		
		# Load agents
		agents = loader.load_agents(str(agents_path))
		logger.info(f"✓ Loaded {len(agents)} agents")
		
		# Initialize state manager with loaded agents
		state_manager = StateManager(agents=agents)
		
		# Load orders into queue
		orders = loader.load_orders(str(orders_path))
		state_manager.add_orders_to_queue(orders)
		logger.info(f"✓ Loaded {len(orders)} orders")
		
		# Load environment
		environment = loader.load_environment(str(environment_path))
		logger.info(f"✓ Loaded environment with {len(environment.nodes)} nodes")
		
		# Create optimizer and dispatcher
		optimizer = SimulatedAnnealingOptimizer()
		dispatcher = Dispatcher(state_manager, optimizer, environment)
		logger.info("✓ Dispatcher initialized")
		
		# Run a single dispatch cycle
		logger.info("\n" + "=" * 70)
		logger.info("Running dispatch cycle...")
		logger.info("=" * 70)
		
		# Run optimizer manually with loaded data
		result = optimizer.optimize(agents, orders, environment)
		
		# Apply assignments from optimizer result
		assignments_made = 0
		for order_id, agent_id in result.assignments.items():
			if agent_id in state_manager.agents:
				state_manager.agents[agent_id].active_orders.append(order_id)
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
		for agent in state_manager.list_agents():
			load = len(agent.active_orders)
			logger.info(f"  • {agent.agent_id}: {load}/2 orders")
		
		logger.info("\n✓ System ready for continuous dispatch")
		
	except FileNotFoundError as e:
		logger.error(f"Data file not found: {e}")
		raise
		
	except Exception as e:
		logger.error(f"Error during startup: {e}", exc_info=True)
		raise


if __name__ == "__main__":
	main()