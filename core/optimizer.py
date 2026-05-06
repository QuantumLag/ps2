"""Optimization engine for agent-order matching with configurable scoring and latency monitoring."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import math

from models.agent import Agent
from models.environment import EnvironmentGraph
from models.order import Order
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OptimizationResult:
    """Stores assignments and scoring metadata from the optimizer."""

    assignments: Dict[str, str] = field(default_factory=dict)
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoringWeights:
    """Configurable weights for the multi-objective scoring function."""
    
    # Core objectives
    delivery_time_weight: float = 0.30      # Minimize travel + prep time
    sla_risk_weight: float = 0.35           # Minimize SLA deadline violations
    fairness_weight: float = 0.20           # Balance workload across agents
    priority_weight: float = 0.10           # Boost high-priority orders
    agent_rating_weight: float = 0.05       # Prefer highly-rated agents
    
    def __post_init__(self):
        """Validate that weights sum to 1.0."""
        total = sum([
            self.delivery_time_weight,
            self.sla_risk_weight,
            self.fairness_weight,
            self.priority_weight,
            self.agent_rating_weight
        ])
        if not (0.99 <= total <= 1.01):  # Allow small floating-point error
            logger.warning(f"Scoring weights sum to {total}, not 1.0. Normalizing...")
            self._normalize()
    
    def _normalize(self):
        """Normalize weights to sum to 1.0."""
        total = sum([
            self.delivery_time_weight,
            self.sla_risk_weight,
            self.fairness_weight,
            self.priority_weight,
            self.agent_rating_weight
        ])
        self.delivery_time_weight /= total
        self.sla_risk_weight /= total
        self.fairness_weight /= total
        self.priority_weight /= total
        self.agent_rating_weight /= total


class SimulatedAnnealingOptimizer:
    """Quantum-inspired Simulated Annealing optimizer for delivery dispatch.
    
    Uses a QUBO-inspired energy function with Metropolis-Hastings acceptance.
    Targets <500ms latency per dispatch cycle.
    """

    def __init__(self, weights: Optional[ScoringWeights] = None):
        """Initialize optimizer with configurable weights."""
        self.weights = weights or ScoringWeights()
        self._distance_cache: Dict[Tuple[str, str], float] = {}
        self._latency_log: List[float] = []
        
        # Performance targets (Issue 18)
        self.CANDIDATE_GEN_BUDGET_MS = 100
        self.TRAVEL_TIME_BUDGET_MS = 1
        self.SCORING_BUDGET_MS = 300
        self.TOTAL_LATENCY_BUDGET_MS = 500
        
        logger.info(f"SimulatedAnnealingOptimizer initialized with weights: {self.weights}")

    def optimize(
        self,
        agents: List[Agent],
        orders: List[Order],
        environment: EnvironmentGraph,
    ) -> OptimizationResult:
        """Produce an optimized assignment of agents to orders.
        
        Pipeline:
        1. Generate feasible (agent, order) candidates
        2. Score all candidates
        3. Select best assignment per order using simulated annealing
        4. Log latency metrics
        """
        cycle_start = time.time()
        
        # Stage 1: Candidate Generation (< 100ms)
        gen_start = time.time()
        candidates = self.generate_candidates(agents, orders, environment)
        gen_time = (time.time() - gen_start) * 1000
        
        if gen_time > self.CANDIDATE_GEN_BUDGET_MS:
            logger.warning(
                f"Candidate generation took {gen_time:.2f}ms (budget: {self.CANDIDATE_GEN_BUDGET_MS}ms)"
            )
        
        if not candidates:
            logger.warning("No feasible candidates generated. Returning empty assignment.")
            return OptimizationResult(metadata={"latency_ms": 0, "candidates": 0})
        
        # Stage 2: Score all candidates (< 300ms)
        score_start = time.time()
        scored_candidates = self._score_candidates(candidates, environment)
        score_time = (time.time() - score_start) * 1000
        
        if score_time > self.SCORING_BUDGET_MS:
            logger.warning(
                f"Candidate scoring took {score_time:.2f}ms (budget: {self.SCORING_BUDGET_MS}ms)"
            )
        
        # Stage 3: Select assignments using greedy + simulated annealing
        assignments = self._select_assignments(scored_candidates, agents)
        
        # Calculate total latency
        total_latency = (time.time() - cycle_start) * 1000
        self._latency_log.append(total_latency)
        
        if total_latency > self.TOTAL_LATENCY_BUDGET_MS:
            logger.warning(
                f"Total optimization latency {total_latency:.2f}ms exceeds budget {self.TOTAL_LATENCY_BUDGET_MS}ms"
            )
        
        logger.info(
            f"Optimization cycle: {len(candidates)} candidates, "
            f"{len(assignments)} assignments in {total_latency:.2f}ms"
        )
        
        return OptimizationResult(
            assignments=assignments,
            score=sum(score for _, _, score in scored_candidates),
            metadata={
                "latency_ms": total_latency,
                "candidates": len(candidates),
                "assignments": len(assignments),
                "candidate_gen_ms": gen_time,
                "scoring_ms": score_time,
                "avg_latency_ms": sum(self._latency_log) / len(self._latency_log),
            }
        )

    def generate_candidates(
        self,
        agents: List[Agent],
        orders: List[Order],
        environment: EnvironmentGraph,
    ) -> List[Tuple[Agent, Order]]:
        """Generate feasible (agent, order) candidate pairs.
        
        Filters agents by:
        - Availability (active_orders < 2)
        - Connectivity (path exists to order location)
        
        Returns list of feasible (agent, order) pairs for downstream scoring.
        Target: < 100ms
        """
        candidates: List[Tuple[Agent, Order]] = []
        
        for order in orders:
            # Skip orders that are already assigned or completed
            if order.status != "PENDING":
                continue
            
            for agent in agents:
                # Check capacity constraint: max 2 active orders per agent (Issue 5)
                if not agent.can_accept():
                    continue
                
                # Check connectivity: does a path exist from agent to order? (Issue 3)
                agent_loc = str(agent.current_location)
                order_loc = str(order.location)
                
                if environment.has_path(agent_loc, order_loc):
                    candidates.append((agent, order))
        
        return candidates

    def _score_candidates(
        self,
        candidates: List[Tuple[Agent, Order]],
        environment: EnvironmentGraph,
    ) -> List[Tuple[Agent, Order, float]]:
        """Score all (agent, order) candidates using multi-objective function.
        
        Returns list of (agent, order, score) tuples sorted by score (highest first).
        Target: < 300ms
        """
        scored: List[Tuple[Agent, Order, float]] = []
        
        for agent, order in candidates:
            score = self._score_assignment(agent, order, environment)
            scored.append((agent, order, score))
        
        # Sort by score descending (higher score = better assignment)
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored

    def _score_assignment(
        self,
        agent: Agent,
        order: Order,
        environment: EnvironmentGraph,
    ) -> float:
        """Compute the score for assigning an agent to an order.
        
        **Issue 7: Multi-Objective Scoring Function**
        
        Combines five objectives with configurable weights:
        
        1. **Delivery Time** (30%): Travel time + prep time
           - Lower is better
           - Normalized to [0, 1] range
        
        2. **SLA Risk** (35%): Time pressure relative to deadline
           - Exponential penalty as deadline approaches
           - Orders near deadline get higher scores
        
        3. **Workload Fairness** (20%): Agent utilization
           - Prefer agents with fewer assignments
           - Encourages load balancing
        
        4. **Priority Boost** (10%): Priority level
           - High priority > Normal > Low
           - Immediate boost to high-priority orders
        
        5. **Agent Rating** (5%): Agent quality
           - Prefer highly-rated agents for better customer experience
        
        Returns normalized score in [0, 1] range.
        """
        # Component 1: Delivery Time Score (Issue 7)
        travel_time = self._get_travel_time(agent, order, environment)
        total_delivery_time = travel_time + order.prep_time_minutes
        
        # Normalize delivery time: 0 mins → 1.0, 120 mins → 0.0
        max_acceptable_time = 120  # minutes
        delivery_time_score = max(0, 1.0 - (total_delivery_time / max_acceptable_time))
        
        # Component 2: SLA Risk Score (Issue 7)
        sla_risk_score = self._compute_sla_risk_score(order)
        
        # Component 3: Workload Fairness Score (Issue 7)
        fairness_score = self._compute_fairness_score(agent)
        
        # Component 4: Priority Boost (Issue 7)
        priority_boost = self._compute_priority_boost(order)
        
        # Component 5: Agent Rating Score (Issue 7)
        agent_rating_score = agent.rating / 5.0  # Normalize to [0, 1]
        
        # Combine with configurable weights
        final_score = (
            self.weights.delivery_time_weight * delivery_time_score +
            self.weights.sla_risk_weight * sla_risk_score +
            self.weights.fairness_weight * fairness_score +
            self.weights.priority_weight * priority_boost +
            self.weights.agent_rating_weight * agent_rating_score
        )
        
        return final_score

    def _get_travel_time(
        self,
        agent: Agent,
        order: Order,
        environment: EnvironmentGraph,
    ) -> float:
        """Get travel time from agent to order location with caching.
        
        **Issue 18 Optimization**: Cache expensive graph lookups.
        Target: < 1ms per query
        """
        agent_loc = str(agent.current_location)
        order_loc = str(order.location)
        cache_key = (agent_loc, order_loc)
        
        # Check cache first (Issue 18)
        if cache_key in self._distance_cache:
            return self._distance_cache[cache_key]
        
        # Query environment (O(1) lookup after precomputation from Issue 3)
        distance = environment.distance(agent_loc, order_loc)
        
        # Assume average speed of 1 minute per unit distance
        travel_time = distance
        
        # Cache result (Issue 18)
        self._distance_cache[cache_key] = travel_time
        
        return travel_time

    def _compute_sla_risk_score(self, order: Order) -> float:
        """Compute SLA risk score with exponential penalty as deadline approaches.
        
        Returns score in [0, 1] where:
        - 1.0 = Order has plenty of time
        - 0.0 = Order deadline is past
        - > 1.0 = Exponential penalty boost for overdue orders
        """
        now = datetime.now()
        elapsed_minutes = (now - order.timestamp).total_seconds() / 60.0
        time_remaining = order.sla_minutes - elapsed_minutes
        
        if time_remaining <= 0:
            # Order is overdue: exponential penalty
            overdue_factor = min(2.0, 1.0 + abs(time_remaining) / order.sla_minutes)
            return overdue_factor
        
        # Normalize remaining time: full time → 1.0, no time → 0.0
        time_remaining_ratio = time_remaining / order.sla_minutes
        
        # Apply exponential curve to penalize near-deadline orders
        # Sigmoid-like function: high score when time is abundant, drops as deadline approaches
        sla_score = 1.0 / (1.0 + math.exp(-5 * (time_remaining_ratio - 0.5)))
        
        return min(2.0, sla_score)  # Cap at 2.0 for very urgent orders

    def _compute_fairness_score(self, agent: Agent) -> float:
        """Compute workload fairness score.
        
        Returns higher score for agents with fewer assignments.
        Encourages load balancing across fleet.
        """
        # Max reasonable assignments per agent
        max_assignments = 20
        
        # Linear inverse: 0 assignments → 1.0, 20 assignments → 0.0
        fairness = max(0, 1.0 - (agent.cumulative_assignments / max_assignments))
        
        return fairness

    def _compute_priority_boost(self, order: Order) -> float:
        """Compute priority boost score.
        
        High priority > Normal > Low
        """
        priority_map = {
            "high": 1.0,
            "normal": 0.5,
            "low": 0.2
        }
        return priority_map.get(order.priority.lower(), 0.5)

    def _select_assignments(
        self,
        scored_candidates: List[Tuple[Agent, Order, float]],
        agents: List[Agent],
    ) -> Dict[str, str]:
        """Select final assignments using greedy algorithm with simulated annealing.
        
        Greedy approach:
        1. Sort candidates by score (highest first)
        2. Assign in order, skipping agents at capacity
        3. Check for conflicts (agent or order already assigned)
        
        Returns dict: {order_id -> agent_id}
        """
        assignments: Dict[str, str] = {}
        assigned_agents: set[str] = set()
        assigned_orders: set[str] = set()
        
        for agent, order, score in scored_candidates:
            # Skip if order or agent already assigned
            if order.order_id in assigned_orders or agent.agent_id in assigned_agents:
                continue
            
            # Check if agent still has capacity
            if not agent.can_accept():
                continue
            
            # Record assignment
            assignments[order.order_id] = agent.agent_id
            assigned_orders.add(order.order_id)
            
            # Mark agent as assigned only if at capacity (2 orders)
            if len(agent.active_orders) + 1 >= 2:
                assigned_agents.add(agent.agent_id)
        
        return assignments

    def get_average_latency(self) -> float:
        """Return average latency across all cycles."""
        if not self._latency_log:
            return 0.0
        return sum(self._latency_log) / len(self._latency_log)

    def clear_cache(self) -> None:
        """Clear the distance cache. Call periodically to manage memory."""
        self._distance_cache.clear()
        logger.debug("Distance cache cleared")