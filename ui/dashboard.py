"""Streamlit dashboard for the Smart Delivery Dispatch System."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.dispatcher import Dispatcher
from core.optimizer import SimulatedAnnealingOptimizer, ScoringWeights
from core.state_manager import StateManager
from data.loader import DataLoader
from models.agent import Agent
from models.environment import EnvironmentGraph
from models.order import Order
from utils.logger import get_logger
from utils.metrics import MetricsCalculator

logger = get_logger(__name__)


# Page configuration
st.set_page_config(page_title="Quantum Dispatch Console", layout="wide", initial_sidebar_state="expanded")


# Session state initialization
if "dispatcher" not in st.session_state:
    st.session_state.dispatcher = None
    st.session_state.state_manager = None
    st.session_state.optimizer = None
    st.session_state.environment = None
    st.session_state.metrics_calculator = None
    st.session_state.agents = []
    st.session_state.orders = []
    st.session_state.completed_orders = []
    st.session_state.event_log = []
    st.session_state.dispatch_cycles = 0
    st.session_state.start_time = datetime.now()
    st.session_state.scoring_weights = ScoringWeights()
    st.session_state.last_optimization_result = None


@st.cache_resource
def load_system():
    """Load or initialize the dispatch system."""
    try:
        data_dir = Path(__file__).parent.parent / "data" / "raw"
        loader = DataLoader()

        # Initialize state manager
        state_manager = StateManager(
            agents_path=str(data_dir / "agents.csv"),
            constraints_path=str(data_dir / "constraints.csv"),
        )

        # Load orders
        state_manager.load_orders(str(data_dir / "orders.csv"))

        # Load environment
        environment = loader.load_environment(str(data_dir / "environment_edges.csv"))

        # Initialize optimizer and dispatcher
        optimizer = SimulatedAnnealingOptimizer(weights=st.session_state.scoring_weights)
        metrics_calculator = MetricsCalculator()

        dispatcher = Dispatcher(state_manager, optimizer, environment, metrics=metrics_calculator)

        # Convert to Agent objects
        agents_list = []
        for agent_id, agent_info in state_manager.agent_registry.items():
            agent = Agent(
                agent_id=agent_id,
                current_location=agent_info["pos"],
                rating=agent_info["rating"],
                active_orders=agent_info["active_orders"],
                cumulative_assignments=agent_info["completed_count"],
            )
            agents_list.append(agent)

        # Get pending orders from queue
        orders_list = []
        temp_queue = list(state_manager.order_queue)
        for priority, timestamp, order_id, order_data in temp_queue:
            order = Order(
                order_id=order_data.get("order_id", order_id),
                timestamp=datetime.now(),
                location=(order_data.get("location_x", 0), order_data.get("location_y", 0)),
                prep_time_minutes=int(order_data.get("prep_time_minutes", 10)),
                priority=order_data.get("priority", "normal"),
                sla_minutes=int(order_data.get("sla_minutes", 60)),
            )
            orders_list.append(order)

        logger.info(f"System loaded: {len(agents_list)} agents, {len(orders_list)} orders")

        return dispatcher, state_manager, optimizer, environment, agents_list, orders_list, metrics_calculator

    except Exception as e:
        logger.error(f"Failed to load system: {e}")
        # Fallback
        state_manager = StateManager(agents_path="", constraints_path="")
        optimizer = SimulatedAnnealingOptimizer()
        environment = EnvironmentGraph(nodes=[], edges={})
        metrics_calculator = MetricsCalculator()
        dispatcher = Dispatcher(state_manager, optimizer, environment, metrics=metrics_calculator)
        return dispatcher, state_manager, optimizer, environment, [], [], metrics_calculator


def initialize_system():
    """Initialize system on first load."""
    if st.session_state.dispatcher is None:
        (
            st.session_state.dispatcher,
            st.session_state.state_manager,
            st.session_state.optimizer,
            st.session_state.environment,
            st.session_state.agents,
            st.session_state.orders,
            st.session_state.metrics_calculator,
        ) = load_system()
        st.session_state.event_log.append(
            {
                "timestamp": datetime.now(),
                "type": "SYSTEM_START",
                "message": f"System initialized with {len(st.session_state.agents)} agents, {len(st.session_state.orders)} orders",
            }
        )


def render_environment_map(agents: List[Agent], orders: List[Order], assignments: dict):
    """Render interactive Plotly map of environment."""
    fig = go.Figure()

    # Agents (circles colored by rating)
    agent_x = [a.current_location[0] for a in agents]
    agent_y = [a.current_location[1] for a in agents]
    agent_ratings = [a.rating for a in agents]
    agent_labels = [
        f"<b>{a.agent_id}</b><br>Rating: {a.rating}★<br>Active: {len(a.active_orders)} orders"
        for a in agents
    ]

    fig.add_trace(
        go.Scatter(
            x=agent_x,
            y=agent_y,
            mode="markers",
            marker=dict(
                size=12,
                color=agent_ratings,
                colorscale="RdBu_r",
                showscale=False,
                line=dict(color="darkblue", width=2),
                colorbar=dict(title="Agent Rating", thickness=15, len=0.7),
            ),
            text=agent_labels,
            hoverinfo="text",
            name="Agents",
            showlegend=True,
        )
    )

    # Orders (stars colored by status)
    priority_to_size = {"high": 18, "normal": 14, "low": 10}
    order_x = [o.location[0] for o in orders]
    order_y = [o.location[1] for o in orders]
    order_colors = [
        "red" if o.status == "PENDING" else "green" if o.status == "ASSIGNED" else "gray" for o in orders
    ]
    order_sizes = [priority_to_size.get(o.priority, 14) for o in orders]
    order_labels = [f"<b>{o.order_id}</b><br>Priority: {o.priority}<br>SLA: {o.sla_minutes}min" for o in orders]

    fig.add_trace(
        go.Scatter(
            x=order_x,
            y=order_y,
            mode="markers",
            marker=dict(
                size=order_sizes,
                symbol="star",
                color=order_colors,
                line=dict(color="darkred", width=1.5),
            ),
            text=order_labels,
            hoverinfo="text",
            name="Orders",
            showlegend=True,
        )
    )

    # Assignment lines
    for order_id, agent_id in assignments.items():
        agent = next((a for a in agents if a.agent_id == agent_id), None)
        order = next((o for o in orders if o.order_id == order_id), None)
        if agent and order:
            fig.add_trace(
                go.Scatter(
                    x=[agent.current_location[0], order.location[0]],
                    y=[agent.current_location[1], order.location[1]],
                    mode="lines",
                    line=dict(color="rgba(100, 100, 100, 0.5)", width=2, dash="dash"),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

    fig.update_layout(
        title="Real-Time Environment Map",
        xaxis_title="X Coordinate",
        yaxis_title="Y Coordinate",
        hovermode="closest",
        height=500,
        template="plotly_light",
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_metrics_cards(delivery_metrics: dict, sla_metrics: dict, fairness_metrics: dict):
    """Render metrics in 3-column layout."""
    col1, col2, col3 = st.columns(3)

    # Delivery Time Metrics
    with col1:
        st.metric(
            "Avg Delivery Time",
            f"{delivery_metrics.get('overall', {}).get('mean_minutes', 0):.1f} min",
            delta=f"σ: {delivery_metrics.get('overall', {}).get('std_dev', 0):.1f}",
        )
        st.caption(f"Range: {delivery_metrics.get('overall', {}).get('min', 0):.1f} - {delivery_metrics.get('overall', {}).get('max', 0):.1f} min")

    # SLA Compliance Metrics
    with col2:
        compliance = sla_metrics.get("overall", {}).get("compliance_rate", 0.0) * 100
        color = "🟢" if compliance >= 90 else "🟡" if compliance >= 70 else "🔴"
        st.metric(
            f"{color} SLA Compliance",
            f"{compliance:.1f}%",
            delta=f"Violations: {sla_metrics.get('overall', {}).get('violation_count', 0)}",
        )

    # Fairness Metrics
    with col3:
        fairness = fairness_metrics.get("fairness_score", 0.0)
        color = "🟢" if fairness >= 0.8 else "🟡" if fairness >= 0.6 else "🔴"
        st.metric(
            f"{color} Load Fairness",
            f"{fairness:.2f}",
            delta=f"Range: {fairness_metrics.get('min_assignments', 0)} - {fairness_metrics.get('max_assignments', 0)} orders",
        )


def render_event_log(event_log: List[dict]):
    """Render scrollable event log."""
    st.subheader("📋 Dispatch Event Log")

    # Display most recent events (reversed order)
    log_text = ""
    for event in reversed(event_log[-50:]):  # Last 50 events
        timestamp = event["timestamp"].strftime("%H:%M:%S") if isinstance(event["timestamp"], datetime) else str(event["timestamp"])
        event_type = event["type"]

        if event_type == "DISPATCH_COMPLETE":
            icon = "✓"
            msg = f"  → {event.get('message', 'Dispatch complete')}"
        elif event_type == "ASSIGNMENT":
            icon = "→"
            msg = f"  → {event.get('message', 'Assignment made')}"
        elif event_type == "WARNING":
            icon = "⚠️"
            msg = f"  → {event.get('message', 'Warning')}"
        elif event_type == "ERROR":
            icon = "✗"
            msg = f"  → {event.get('message', 'Error')}"
        else:
            icon = "•"
            msg = f"  → {event.get('message', event_type)}"

        log_text += f"[{timestamp}] {icon} {msg}\n"

    st.text_area("Recent Events", value=log_text, height=150, disabled=True)


def run_dispatch_cycle():
    """Execute a dispatch cycle."""
    if not st.session_state.agents or not st.session_state.orders:
        st.warning("⚠️ System not properly initialized")
        return

    try:
        with st.spinner("🔄 Running optimization..."):
            # Get current state
            agents = st.session_state.agents
            orders = st.session_state.orders

            # Run optimizer
            result = st.session_state.optimizer.optimize(agents, orders, st.session_state.environment)

            # Apply assignments
            assignments_made = 0
            for order_id, agent_id in result.assignments.items():
                st.session_state.state_manager.apply_assignment(agent_id, order_id)
                assignments_made += 1

                # Log assignment
                st.session_state.event_log.append(
                    {
                        "timestamp": datetime.now(),
                        "type": "ASSIGNMENT",
                        "message": f"Assigned {order_id} to {agent_id}",
                    }
                )

            # Store optimization result
            st.session_state.last_optimization_result = result

            # Log dispatch cycle
            st.session_state.dispatch_cycles += 1
            st.session_state.event_log.append(
                {
                    "timestamp": datetime.now(),
                    "type": "DISPATCH_COMPLETE",
                    "message": f"Dispatch cycle #{st.session_state.dispatch_cycles}: {assignments_made} assignments, score: {result.score:.2f}, latency: {result.metadata.get('latency_ms', 0):.1f}ms",
                }
            )

            st.success(f"✓ Made {assignments_made} assignments in {result.metadata.get('latency_ms', 0):.1f}ms")

    except Exception as e:
        logger.error(f"Dispatch error: {e}")
        st.error(f"✗ Dispatch failed: {e}")
        st.session_state.event_log.append(
            {
                "timestamp": datetime.now(),
                "type": "ERROR",
                "message": f"Dispatch failed: {str(e)}",
            }
        )


def export_metrics():
    """Export current metrics as JSON."""
    if not st.session_state.agents:
        st.warning("No agents to export")
        return

    # Calculate metrics
    metrics_calc = st.session_state.metrics_calculator
    delivery_metrics = metrics_calc.calculate_delivery_time_metrics(st.session_state.completed_orders)
    sla_metrics = metrics_calc.calculate_sla_compliance(st.session_state.completed_orders)
    fairness_metrics = metrics_calc.calculate_workload_fairness(st.session_state.agents)

    # Build optimization metadata
    opt_metadata = {}
    if st.session_state.last_optimization_result:
        opt_metadata = {
            "last_score": st.session_state.last_optimization_result.score,
            "last_latency_ms": st.session_state.last_optimization_result.metadata.get("latency_ms", 0),
        }

    # Export
    export_data = metrics_calc.export_metrics_json(
        delivery_metrics=delivery_metrics,
        sla_metrics=sla_metrics,
        fairness_metrics=fairness_metrics,
        optimization_metadata=opt_metadata,
        agents_count=len(st.session_state.agents),
        environment_nodes=len(st.session_state.environment.nodes) if st.session_state.environment else 0,
        environment_edges=len(st.session_state.environment.edges) if st.session_state.environment else 0,
    )

    # Download button
    json_str = json.dumps(export_data, indent=2, default=str)
    st.download_button(
        label="📥 Download Metrics JSON",
        data=json_str,
        file_name=f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
    )


def main():
    """Main dashboard."""
    # Custom CSS
    st.markdown(
        """
        <style>
        .main { background: linear-gradient(120deg, #f7f1e5 0%, #f1f4ff 45%, #f7f1e5 100%); }
        h1 { font-family: 'Playfair Display', serif; letter-spacing: 0.5px; color: #0b355d; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header
    st.title("🚀 Quantum Dispatch Console")
    st.caption("Smart Delivery Dispatch System - Simulated Annealing Optimization in Action")

    # Initialize system
    initialize_system()

    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Optimizer Controls")

        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Run Dispatch", use_container_width=True):
                run_dispatch_cycle()
                st.rerun()

        with col2:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        st.divider()

        # Weight sliders
        st.subheader("📊 Scoring Weights")
        delivery_weight = st.slider("Delivery Time", 0.0, 1.0, 0.30, 0.05)
        sla_weight = st.slider("SLA Risk", 0.0, 1.0, 0.35, 0.05)
        fairness_weight = st.slider("Fairness", 0.0, 1.0, 0.20, 0.05)
        priority_weight = st.slider("Priority", 0.0, 1.0, 0.10, 0.05)
        rating_weight = st.slider("Agent Rating", 0.0, 1.0, 0.05, 0.05)

        # Normalize weights
        total = delivery_weight + sla_weight + fairness_weight + priority_weight + rating_weight
        if total > 0:
            normalized_weights = ScoringWeights(
                delivery_time_weight=delivery_weight / total,
                sla_risk_weight=sla_weight / total,
                fairness_weight=fairness_weight / total,
                priority_weight=priority_weight / total,
                agent_rating_weight=rating_weight / total,
            )
            st.session_state.scoring_weights = normalized_weights
            if st.session_state.optimizer:
                st.session_state.optimizer.weights = normalized_weights

        # Display normalized values
        with st.expander("📈 Normalized Values"):
            col_a, col_b, col_c = st.columns(3)
            col_a.caption(f"Delivery: {normalized_weights.delivery_time_weight:.2%}")
            col_b.caption(f"SLA: {normalized_weights.sla_risk_weight:.2%}")
            col_c.caption(f"Fairness: {normalized_weights.fairness_weight:.2%}")

        st.divider()

        # Export metrics
        if st.button("📊 Export Metrics", use_container_width=True):
            export_metrics()

        st.divider()

        # System info
        st.subheader("📌 System Status")
        uptime = (datetime.now() - st.session_state.start_time).total_seconds()
        st.metric("Agents", len(st.session_state.agents))
        st.metric("Orders", len(st.session_state.orders))
        st.metric("Dispatch Cycles", st.session_state.dispatch_cycles)
        st.metric("Uptime", f"{int(uptime)}s")

    # Main content
    if st.session_state.agents and st.session_state.orders:
        # Derive assignments from agent active_orders
        assignments = {}
        for agent in st.session_state.agents:
            for order_id in agent.active_orders:
                assignments[order_id] = agent.agent_id

        # Map and controls
        render_environment_map(st.session_state.agents, st.session_state.orders, assignments)

        st.divider()

        # Metrics
        st.subheader("📊 Performance Metrics")
        metrics_calc = st.session_state.metrics_calculator

        # Calculate metrics
        delivery_metrics = metrics_calc.calculate_delivery_time_metrics(st.session_state.completed_orders)
        sla_metrics = metrics_calc.calculate_sla_compliance(st.session_state.completed_orders)
        fairness_metrics = metrics_calc.calculate_workload_fairness(st.session_state.agents)

        render_metrics_cards(delivery_metrics, sla_metrics, fairness_metrics)

        st.divider()

        # Event log
        render_event_log(st.session_state.event_log)
    else:
        st.info("💡 System initializing... Please wait or try refreshing the page.")


if __name__ == "__main__":
    main()
