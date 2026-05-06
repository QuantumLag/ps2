"""Configuration for the Smart Delivery Dispatch System."""

from core.optimizer import ScoringWeights

# Default scoring weights (Issue 7)
# Customize these to tune optimizer behavior

DEFAULT_WEIGHTS = ScoringWeights(
    delivery_time_weight=0.30,      # Minimize travel + prep time
    sla_risk_weight=0.35,           # Avoid SLA violations (most important)
    fairness_weight=0.20,           # Balance workload
    priority_weight=0.10,           # Respect order priority
    agent_rating_weight=0.05        # Quality preference
)

# High SLA compliance configuration
SLA_FIRST_WEIGHTS = ScoringWeights(
    delivery_time_weight=0.20,
    sla_risk_weight=0.50,           # 50% weight on SLA!
    fairness_weight=0.15,
    priority_weight=0.10,
    agent_rating_weight=0.05
)

# Balanced configuration
BALANCED_WEIGHTS = ScoringWeights(
    delivery_time_weight=0.25,
    sla_risk_weight=0.25,
    fairness_weight=0.25,
    priority_weight=0.15,
    agent_rating_weight=0.10
)

# Speed-first configuration
SPEED_FIRST_WEIGHTS = ScoringWeights(
    delivery_time_weight=0.50,      # 50% weight on speed!
    sla_risk_weight=0.20,
    fairness_weight=0.15,
    priority_weight=0.10,
    agent_rating_weight=0.05
)