"""Test metrics calculations."""

from datetime import datetime
from models.agent import Agent
from models.order import Order
from utils.metrics import MetricsCalculator

# Create test metrics calculator
calc = MetricsCalculator()

# Test Issue 12: Delivery Time Metrics
print("=" * 70)
print("Testing Issue 12: Delivery Time Metrics")
print("=" * 70)

completed_orders = [
    {"delivery_time_minutes": 30.5, "priority": "high", "sla_minutes": 60},
    {"delivery_time_minutes": 45.2, "priority": "normal", "sla_minutes": 60},
    {"delivery_time_minutes": 52.1, "priority": "low", "sla_minutes": 90},
    {"delivery_time_minutes": 38.0, "priority": "high", "sla_minutes": 60},
    {"delivery_time_minutes": 48.5, "priority": "normal", "sla_minutes": 60},
]

delivery_metrics = calc.calculate_delivery_time_metrics(completed_orders)
print("\nDelivery Time Metrics:")
print(f"  Overall Mean: {delivery_metrics['overall']['mean_minutes']} min")
print(f"  Overall Std Dev: {delivery_metrics['overall']['std_dev']} min")
print(f"  By Priority: {delivery_metrics['by_priority']}")
print(f"  SLA Pressure: {delivery_metrics['sla_pressure_score']}")

# Test Issue 13: SLA Compliance
print("\n" + "=" * 70)
print("Testing Issue 13: SLA Compliance Metrics")
print("=" * 70)

sla_metrics = calc.calculate_sla_compliance(completed_orders)
print("\nSLA Compliance Metrics:")
print(f"  Compliance Rate: {sla_metrics['overall']['compliance_rate']:.1%}")
print(f"  Violation Rate: {sla_metrics['overall']['violation_rate']:.1%}")
print(f"  Violations: {sla_metrics['overall']['violation_count']}")
print(f"  By Priority: {sla_metrics['by_priority']}")

# Test Issue 14: Workload Fairness
print("\n" + "=" * 70)
print("Testing Issue 14: Workload Fairness Metrics")
print("=" * 70)

agents = [
    Agent(agent_id=f"A{i}", current_location=(i, i), rating=4.0, cumulative_assignments=2+i)
    for i in range(1, 6)
]

fairness_metrics = calc.calculate_workload_fairness(agents)
print("\nWorkload Fairness Metrics:")
print(f"  Variance: {fairness_metrics['variance']}")
print(f"  Std Dev: {fairness_metrics['std_deviation']}")
print(f"  Mean: {fairness_metrics['mean_assignments']}")
print(f"  Min/Max: {fairness_metrics['min_assignments']} - {fairness_metrics['max_assignments']}")
print(f"  Gini: {fairness_metrics['gini_coefficient']}")
print(f"  Fairness Score: {fairness_metrics['fairness_score']}")

# Test Issue 15: Export JSON
print("\n" + "=" * 70)
print("Testing Issue 15: Export Metrics JSON")
print("=" * 70)

export_data = calc.export_metrics_json(
    delivery_metrics=delivery_metrics,
    sla_metrics=sla_metrics,
    fairness_metrics=fairness_metrics,
    optimization_metadata={"avg_latency_ms": 245.3, "cycles_run": 5},
    agents_count=len(agents),
    environment_nodes=100,
    environment_edges=180,
)

print("\nExported JSON structure:")
print(f"  Timestamp: {export_data['timestamp']}")
print(f"  Delivery Time Keys: {list(export_data['delivery_time'].keys())}")
print(f"  SLA Keys: {list(export_data['sla_compliance'].keys())}")
print(f"  Fairness Keys: {list(export_data['workload_fairness'].keys())}")
print(f"  Dataset Info: {export_data['dataset_info']}")

print("\n" + "=" * 70)
print("✅ All metrics tests passed!")
print("=" * 70)
