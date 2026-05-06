"""Data ingestion layer for CSV processing."""

from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import Dict, List, Set, Tuple

from models.agent import Agent
from models.environment import EnvironmentGraph
from models.order import Order
from data.validator import MissingDataError, InvalidValueError
from utils.logger import get_logger

logger = get_logger(__name__)

class DataLoader:
    """Handles parsing and validation of CSV inputs."""

    @staticmethod
    def load_orders(filepath: str) -> List[Order]:
        """Load and validate orders from CSV."""
        if not os.path.exists(filepath):
            logger.error(f"Failed to load orders: {filepath} not found.")
            raise MissingDataError(f"Required file missing: {filepath}")

        orders: List[Order] = []
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row_num, row in enumerate(reader, start=2):
                try:
                    order = Order(
                        order_id=row['order_id'],
                        timestamp=datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S"),
                        location=(int(row['location_x']), int(row['location_y'])),
                        prep_time_minutes=int(row['prep_time_minutes']),
                        priority=row['priority'].lower(),
                        sla_minutes=int(row['sla_minutes'])
                    )
                    orders.append(order)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Malformed order data at row {row_num} (ID: {row.get('order_id', 'Unknown')}): {e}. Skipping row.")
        
        logger.info(f"Successfully loaded {len(orders)} valid orders.")
        return orders

    @staticmethod
    def load_agents(filepath: str) -> List[Agent]:
        """Load and validate agents from CSV."""
        if not os.path.exists(filepath):
            logger.error(f"Failed to load agents: {filepath} not found.")
            raise MissingDataError(f"Required file missing: {filepath}")

        agents: List[Agent] = []
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row_num, row in enumerate(reader, start=2):
                try:
                    agent = Agent(
                        agent_id=row['agent_id'],
                        current_location=(int(row['current_x']), int(row['current_y'])),
                        rating=float(row['rating'])
                    )
                    agents.append(agent)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Malformed agent data at row {row_num} (ID: {row.get('agent_id', 'Unknown')}): {e}. Skipping row.")
                    
        logger.info(f"Successfully loaded {len(agents)} valid agents.")
        return agents
    
    @staticmethod
    def load_environment(filepath: str) -> EnvironmentGraph:
        """Load and validate environment graph from CSV with edges and distances."""
        if not os.path.exists(filepath):
            logger.error(f"Failed to load environment: {filepath} not found.")
            raise MissingDataError(f"Required file missing: {filepath}")

        nodes: Set[str] = set()
        edges: Dict[Tuple[str, str], float] = {}
        
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Handle both coordinate-based and node-based formats
                    if 'from_x' in row and 'from_y' in row:
                        # Coordinate-based format
                        source = f"({row['from_x']},{row['from_y']})"
                        target = f"({row['to_x']},{row['to_y']})"
                        distance = float(row.get('distance_minutes', 0))
                    else:
                        # Node-based format
                        source = str(row['source']).strip()
                        target = str(row['target']).strip()
                        distance = float(row['distance'])
                    
                    # Validate distance
                    if distance < 0:
                        logger.warning(f"Negative distance at row {row_num}: {distance}. Skipping row.")
                        continue
                    
                    # Add nodes and edge
                    nodes.add(source)
                    nodes.add(target)
                    edges[(source, target)] = distance
                    
                except (KeyError, ValueError) as e:
                    logger.warning(f"Malformed environment data at row {row_num}: {e}. Skipping row.")
        
        if not nodes or not edges:
            logger.error("No valid environment data found.")
            raise InvalidValueError("Environment graph has no valid nodes or edges.")
        
        logger.info(f"Successfully loaded environment: {len(nodes)} nodes, {len(edges)} edges.")
        
        # Create graph and precompute all-pairs shortest paths
        environment = EnvironmentGraph(nodes=nodes, edges=edges)
        environment.compute_distance_matrix()
        
        return environment