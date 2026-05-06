"""Entry point for the Smart Delivery Dispatch System."""

from __future__ import annotations

from core.dispatcher import Dispatcher
from core.optimizer import SimulatedAnnealingOptimizer
from core.state_manager import StateManager
from models.environment import EnvironmentGraph


def main() -> None:
    """Bootstrap the dispatch system."""
    # TODO: Load data, initialize environment, and start dispatcher.
    state_manager = StateManager()
    optimizer = SimulatedAnnealingOptimizer()
    environment = EnvironmentGraph(nodes=[], edges={})
    dispatcher = Dispatcher(state_manager, optimizer, environment)
    dispatcher.start()


if __name__ == "__main__":
    main()
