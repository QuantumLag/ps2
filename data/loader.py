"""Data ingestion layer for CSV processing."""

from __future__ import annotations

import csv
import os
import logging
from datetime import datetime
from typing import List

from models.agent import Agent
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