"""Metrics calculations for dispatch performance."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from models.agent import Agent
from models.order import Order


class MetricsCalculator:
    """Computes SLA, fairness, and timing metrics."""

    def calculate_delivery_time_metrics(
        self,
        completed_orders: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Issue 12: Calculate average delivery time overall and by priority level.
        Uses Welford's algorithm for online mean/variance.

        Args:
            completed_orders: List of dicts with keys:
                - 'delivery_time_minutes': float
                - 'priority': str ('high', 'normal', 'low')

        Returns:
            {
                "overall": {
                    "mean_minutes": float,
                    "std_dev": float,
                    "min": float,
                    "max": float,
                    "count": int
                },
                "by_priority": {
                    "high": {...},
                    "normal": {...},
                    "low": {...}
                },
                "sla_pressure_score": float
            }
        """
        if not completed_orders:
            completed_orders = []

        if not completed_orders:
            return {
                "overall": {
                    "mean_minutes": 0.0,
                    "std_dev": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "count": 0,
                },
                "by_priority": {
                    "high": {"mean": 0.0, "std_dev": 0.0, "count": 0},
                    "normal": {"mean": 0.0, "std_dev": 0.0, "count": 0},
                    "low": {"mean": 0.0, "std_dev": 0.0, "count": 0},
                },
                "sla_pressure_score": 0.0,
            }

        # Overall stats using Welford's algorithm
        n = 0
        mean = 0.0
        m2 = 0.0
        min_time = float("inf")
        max_time = float("-inf")
        total_sla_pressure = 0.0

        # By-priority stats
        by_priority = {"high": [], "normal": [], "low": []}

        for order in completed_orders:
            delivery_time = order.get("delivery_time_minutes", 0.0)
            priority = order.get("priority", "normal").lower()

            # Welford update for overall
            n += 1
            delta = delivery_time - mean
            mean += delta / n
            delta2 = delivery_time - mean
            m2 += delta * delta2

            min_time = min(min_time, delivery_time)
            max_time = max(max_time, delivery_time)

            # Track by priority
            if priority in by_priority:
                by_priority[priority].append(delivery_time)

            # SLA pressure
            sla_minutes = order.get("sla_minutes", 60.0)
            if sla_minutes > 0:
                total_sla_pressure += delivery_time / sla_minutes

        # Calculate overall std dev
        std_dev = (m2 / n) ** 0.5 if n > 1 else 0.0

        # Calculate by-priority stats
        by_priority_stats = {}
        for priority, times in by_priority.items():
            if times:
                n_p = len(times)
                mean_p = sum(times) / n_p
                var_p = sum((x - mean_p) ** 2 for x in times) / n_p
                std_p = var_p ** 0.5
                by_priority_stats[priority] = {
                    "mean": round(mean_p, 2),
                    "std_dev": round(std_p, 2),
                    "count": n_p,
                }
            else:
                by_priority_stats[priority] = {
                    "mean": 0.0,
                    "std_dev": 0.0,
                    "count": 0,
                }

        sla_pressure = total_sla_pressure / n if n > 0 else 0.0

        return {
            "overall": {
                "mean_minutes": round(mean, 2),
                "std_dev": round(std_dev, 2),
                "min": round(min_time if min_time != float("inf") else 0.0, 2),
                "max": round(max_time if max_time != float("-inf") else 0.0, 2),
                "count": n,
            },
            "by_priority": by_priority_stats,
            "sla_pressure_score": round(min(sla_pressure, 1.0), 2),
        }

    def calculate_sla_compliance(
        self,
        completed_orders: Optional[List[Dict]] = None,
        now: Optional[datetime] = None,
    ) -> Dict:
        """
        Issue 13: Track SLA violations and calculate compliance rate as percentage.

        Args:
            completed_orders: List of dicts with keys:
                - 'delivery_time_minutes': float
                - 'sla_minutes': float
                - 'priority': str

        Returns:
            {
                "overall": {
                    "compliance_rate": float (0.0-1.0),
                    "violation_rate": float (0.0-1.0),
                    "violation_count": int,
                    "delivered_count": int,
                    "avg_margin_minutes": float
                },
                "by_priority": {
                    "high": {...},
                    "normal": {...},
                    "low": {...}
                }
            }
        """
        if not completed_orders:
            completed_orders = []

        if not completed_orders:
            return {
                "overall": {
                    "compliance_rate": 1.0,
                    "violation_rate": 0.0,
                    "violation_count": 0,
                    "delivered_count": 0,
                    "avg_margin_minutes": 0.0,
                },
                "by_priority": {
                    "high": {
                        "compliance_rate": 1.0,
                        "violation_count": 0,
                        "avg_margin": 0.0,
                    },
                    "normal": {
                        "compliance_rate": 1.0,
                        "violation_count": 0,
                        "avg_margin": 0.0,
                    },
                    "low": {
                        "compliance_rate": 1.0,
                        "violation_count": 0,
                        "avg_margin": 0.0,
                    },
                },
            }

        # Overall tracking
        total_count = len(completed_orders)
        violation_count = 0
        total_margin = 0.0

        # By-priority tracking
        by_priority = {"high": {"violations": 0, "count": 0, "margins": []},
                       "normal": {"violations": 0, "count": 0, "margins": []},
                       "low": {"violations": 0, "count": 0, "margins": []}}

        for order in completed_orders:
            delivery_time = order.get("delivery_time_minutes", 0.0)
            sla_minutes = order.get("sla_minutes", 60.0)
            priority = order.get("priority", "normal").lower()

            # Margin = SLA deadline - delivery time (positive = early, negative = late)
            margin = sla_minutes - delivery_time

            # Track by priority
            if priority in by_priority:
                by_priority[priority]["count"] += 1
                by_priority[priority]["margins"].append(margin)

                if margin < 0:  # SLA violated
                    violation_count += 1
                    by_priority[priority]["violations"] += 1

            total_margin += margin

        # Calculate rates
        compliance_rate = 1.0 - (violation_count / total_count) if total_count > 0 else 1.0
        violation_rate = violation_count / total_count if total_count > 0 else 0.0
        avg_margin = total_margin / total_count if total_count > 0 else 0.0

        # By-priority stats
        by_priority_stats = {}
        for priority, data in by_priority.items():
            if data["count"] > 0:
                comp_rate = 1.0 - (data["violations"] / data["count"])
                avg_marg = sum(data["margins"]) / len(data["margins"])
                by_priority_stats[priority] = {
                    "compliance_rate": round(comp_rate, 3),
                    "violation_count": data["violations"],
                    "avg_margin": round(avg_marg, 2),
                }
            else:
                by_priority_stats[priority] = {
                    "compliance_rate": 1.0,
                    "violation_count": 0,
                    "avg_margin": 0.0,
                }

        return {
            "overall": {
                "compliance_rate": round(compliance_rate, 3),
                "violation_rate": round(violation_rate, 3),
                "violation_count": violation_count,
                "delivered_count": total_count,
                "avg_margin_minutes": round(avg_margin, 2),
            },
            "by_priority": by_priority_stats,
        }

    def calculate_workload_fairness(
        self,
        agents: Optional[List[Agent]] = None,
    ) -> Dict:
        """
        Issue 14: Calculate load variance and distribution across agents.
        Uses Gini coefficient for inequality measure.

        Args:
            agents: List of Agent objects

        Returns:
            {
                "variance": float,
                "std_deviation": float,
                "mean_assignments": float,
                "min_assignments": int,
                "max_assignments": int,
                "assignment_range": int,
                "gini_coefficient": float (0=perfect, 1=max inequality),
                "fairness_score": float (1-gini, higher=fairer)
            }
        """
        if not agents:
            agents = []

        if not agents:
            return {
                "variance": 0.0,
                "std_deviation": 0.0,
                "mean_assignments": 0.0,
                "min_assignments": 0,
                "max_assignments": 0,
                "assignment_range": 0,
                "gini_coefficient": 0.0,
                "fairness_score": 1.0,
            }

        # Get assignment counts
        assignments = [len(agent.active_orders) + agent.cumulative_assignments for agent in agents]

        n = len(assignments)
        if n == 0:
            return {
                "variance": 0.0,
                "std_deviation": 0.0,
                "mean_assignments": 0.0,
                "min_assignments": 0,
                "max_assignments": 0,
                "assignment_range": 0,
                "gini_coefficient": 0.0,
                "fairness_score": 1.0,
            }

        # Calculate mean
        mean = sum(assignments) / n

        # Calculate variance
        variance = sum((x - mean) ** 2 for x in assignments) / n
        std_dev = variance ** 0.5

        # Calculate Gini coefficient
        # Gini = sum(|a - b| for all pairs) / (2 * n * mean)
        gini_sum = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                gini_sum += abs(assignments[i] - assignments[j])
        gini_sum *= 2  # Account for both directions

        if mean > 0:
            gini = gini_sum / (2 * n * mean)
        else:
            gini = 0.0

        # Fairness score (1 - gini, where 1 = perfect fairness)
        fairness_score = 1.0 - gini

        return {
            "variance": round(variance, 2),
            "std_deviation": round(std_dev, 2),
            "mean_assignments": round(mean, 2),
            "min_assignments": min(assignments),
            "max_assignments": max(assignments),
            "assignment_range": max(assignments) - min(assignments),
            "gini_coefficient": round(min(gini, 1.0), 3),
            "fairness_score": round(max(fairness_score, 0.0), 3),
        }

    def export_metrics_json(
        self,
        delivery_metrics: Optional[Dict] = None,
        sla_metrics: Optional[Dict] = None,
        fairness_metrics: Optional[Dict] = None,
        optimization_metadata: Optional[Dict] = None,
        agents_count: int = 0,
        environment_nodes: int = 0,
        environment_edges: int = 0,
    ) -> Dict:
        """
        Issue 15: Export all metrics in structured JSON format.

        Args:
            delivery_metrics: Output from calculate_delivery_time_metrics()
            sla_metrics: Output from calculate_sla_compliance()
            fairness_metrics: Output from calculate_workload_fairness()
            optimization_metadata: Dict with 'latency_ms', 'score', etc.
            agents_count: Total agents in system
            environment_nodes: Total nodes in environment graph
            environment_edges: Total edges in environment graph

        Returns:
            Complete metrics JSON dict
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_orders": 0,
                "total_assignments": 0,
                "total_deliveries": 0,
                "pending_orders": 0,
                "system_uptime_seconds": 0,
            },
            "delivery_time": delivery_metrics or {},
            "sla_compliance": sla_metrics or {},
            "workload_fairness": fairness_metrics or {},
            "optimization": optimization_metadata or {
                "avg_latency_ms": 0.0,
                "max_latency_ms": 0.0,
                "min_latency_ms": 0.0,
                "cycles_run": 0,
                "avg_score": 0.0,
                "throughput_orders_per_minute": 0.0,
            },
            "dataset_info": {
                "agents_count": agents_count,
                "environment_nodes": environment_nodes,
                "environment_edges": environment_edges,
                "augmentation_used": "None",
            },
        }

    def compute_sla_compliance(self, orders: List[Order], now: Optional[datetime] = None) -> float:
        """Return SLA compliance ratio for a set of orders."""
        if not orders:
            return 1.0

        compliant = sum(1 for o in orders if not o.is_overdue(now or datetime.now()))
        return compliant / len(orders) if orders else 0.0

    def compute_workload_fairness(self, agents: List[Agent]) -> float:
        """Return a fairness score for agent workloads (0-1, higher is fairer)."""
        if not agents:
            return 1.0

        metrics = self.calculate_workload_fairness(agents)
        return metrics.get("fairness_score", 0.0)

    def average_delivery_time(self, orders: List[Order]) -> Optional[float]:
        """Return the average delivery time in minutes if available."""
        if not orders:
            return None

        metrics = self.calculate_delivery_time_metrics([])
        return metrics.get("overall", {}).get("mean_minutes")
