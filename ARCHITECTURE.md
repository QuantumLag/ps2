# Project Architecture Overview

## Smart Delivery Dispatch System - Quantum-Inspired Optimization

### Design Philosophy
- **Modular**: Each concern has its own domain (models, optimization, state, data)
- **Type-Safe**: Strict type hints throughout (PEP 484)
- **Performance-First**: <500ms dispatch latency target
- **Extensible**: Easy to add new objectives, constraints, or scoring functions
- **Testable**: Clear separation of concerns enables unit/integration testing

---

## Module Breakdown

### 1. Models (`models/`)
**Domain**: Data structures representing the dispatch system

#### `agent.py`
- **Class**: `Agent`
- **Fields**: agent_id, current_location (x,y tuple), rating (0-5), active_orders list, cumulative_assignments
- **Methods**:
  - `can_accept()` → bool: Check if agent has capacity (max 2 orders)
  - `assign_order(order_id)` → None: Add order to agent's active list
  - `release_order(order_id)` → None: Remove order from agent
- **Validation**: Rating must be 0-5; capacity enforced at 2 max

#### `order.py`
- **Class**: `Order`
- **Fields**: order_id, timestamp, location (x,y), prep_time_minutes, priority (high/normal/low), sla_minutes, status, assigned_agent_id
- **Methods**:
  - `is_overdue(current_time)` → bool: Check if SLA deadline passed
- **Validation**: Priority enum; no negative times

#### `environment.py`
- **Class**: `EnvironmentGraph`
- **Algorithm Choices**:
  - Floyd-Warshall (O(n³)) for ≤100 nodes
  - Dijkstra all-pairs (O(n·e·log n)) for larger graphs
- **Methods**:
  - `compute_distance_matrix()`: All-pairs shortest paths
  - `distance(source, target)` → float: O(1) cached lookup
  - `neighbors(node)` → List[str]: Direct adjacency
  - `has_path(source, target)` → bool: Connectivity check

---

### 2. Core Logic (`core/`)
**Domain**: Optimization, state management, orchestration

#### `state_manager.py`
- **Class**: `StateManager`
- **Purpose**: Central registry for agents, orders, assignments
- **Key Data Structures**:
  - `agent_registry`: Dict[agent_id → Agent]
  - `order_queue`: Priority heap (priority, timestamp, order_id, data)
  - `active_assignments`: Dict[order_id → agent_id]
- **Methods**:
  - `register_agent(agent)` → None: Add agent to system
  - `add_order(order)` → None: Enqueue order by priority
  - `pop_next_order()` → Optional[Order]: Dequeue highest-priority order
  - `get_available_agents()` → List[str]: Agents with capacity
  - `assign_order(order_id, agent_id)` → None: Record assignment
  - `release_order(order_id)` → None: Unassign order

#### `optimizer.py`
- **Class**: `SimulatedAnnealingOptimizer`
- **Purpose**: Score and assign agents to orders
- **Scoring Model** (Issue 7):
  ```
  Score = 0.30 * delivery_time_score 
         + 0.35 * sla_risk_score 
         + 0.20 * fairness_score 
         + 0.10 * priority_boost 
         + 0.05 * agent_rating_score
  ```
- **Pipeline**:
  1. Generate feasible (agent, order) candidates (<100ms)
  2. Score all candidates (<300ms)
  3. Greedy assignment (best-score-first)
  4. Log latency metrics
- **Methods**:
  - `optimize(agents, orders, environment)` → OptimizationResult: Main entry
  - `generate_candidates()` → List[(Agent, Order)]: Filter by capacity/connectivity
  - `_score_candidates()` → List[(Agent, Order, float)]: Score and sort
  - `_score_assignment()` → float: Multi-objective function
  - `_compute_sla_risk_score()` → float: Exponential penalty for deadlines
  - `_compute_fairness_score()` → float: Load balancing incentive
  - `_compute_priority_boost()` → float: Priority level weighting

#### `dispatcher.py`
- **Class**: `Dispatcher`
- **Purpose**: Main orchestrator tying state, optimizer, and metrics together
- **Methods**:
  - `dispatch_once()` → None: Single optimization cycle
  - `start()` → None: Continuous dispatch loop
  - `stop()` → None: Halt dispatching

---

### 3. Data Layer (`data/`)
**Domain**: CSV parsing, validation, error handling

#### `validator.py`
- **Classes**:
  - `DataValidationError`: Base exception
  - `MissingDataError`: File/column not found
  - `InvalidValueError`: Data out of bounds/malformed
- **Class**: `DataValidator`
- **Methods**:
  - `validate_agents()` → None: Schema + range checks
  - `validate_orders()` → None: Schema + range checks
  - `validate_environment()` → None: Schema + range checks
  - `validate_constraints()` → None: Schema + range checks

#### `loader.py`
- **Class**: `DataLoader` (static methods)
- **Purpose**: Load and validate CSV files
- **Methods**:
  - `load_agents(filepath)` → List[Agent]
  - `load_orders(filepath)` → List[Order]
  - `load_environment(filepath)` → EnvironmentGraph
  - `load_constraints(filepath)` → Dict[str, any]
- **Error Handling**: Logs malformed rows; continues with valid data

---

### 4. Utilities (`utils/`)
**Domain**: Metrics, logging, observability

#### `metrics.py`
- **Class**: `MetricsCalculator`
- **Purpose**: Performance and fairness metrics
- **Methods**:
  - `compute_sla_compliance(orders, now?)` → float: % orders meeting SLA
  - `compute_workload_fairness(agents)` → float: Agent load balance score
  - `average_delivery_time(orders)` → Optional[float]: Minutes

#### `logger.py`
- **Function**: `get_logger(name, level?)` → logging.Logger
- **Purpose**: Standardized logging with timestamps
- **Features**: Stream handler, formatter, adjustable levels

---

### 5. UI Layer (`ui/`)
**Domain**: Streamlit dashboard (optional)

#### `dashboard.py`
- **Components**:
  - **Sidebar**: Sliders for SLA, Distance, Fairness weights
  - **Main Plot**: 2D environment with agents (blue dots), orders (red stars), assignments (dashed lines)
  - **Metrics Row**: Energy, SLA%, Agent Fairness (3 columns)
  - **Live Log**: Text area with latest dispatcher messages
- **Data**: Uses mock data for layout preview; ready for integration with StateManager

---

### 6. Entry Point

#### `main.py`
- **Function**: `main()` → None
- **Purpose**: Bootstrap the system
- **Workflow**:
  1. Load data via `DataLoader`
  2. Initialize `StateManager`
  3. Create `SimulatedAnnealingOptimizer`
  4. Build `EnvironmentGraph`
  5. Instantiate `Dispatcher`
  6. Start continuous dispatch

---

## Data Flow

```
CSV Files
  ↓
DataLoader.load_* (validates via DataValidator)
  ↓
StateManager (registers agents, queues orders)
  ↓
Dispatcher.dispatch_once()
  ├─→ Optimizer.optimize(agents, orders, environment)
  │   ├─→ generate_candidates() [filter by capacity]
  │   ├─→ _score_candidates() [multi-objective]
  │   └─→ _select_assignments() [greedy matching]
  ├─→ MetricsCalculator (compute SLA%, fairness, latency)
  └─→ Logger (output telemetry)
  ↓
Dashboard.update() [refresh metrics, plot, logs]
```

---

## Performance Targets (Issue 18)

| Component | Budget | Algorithm |
|-----------|--------|-----------|
| Candidate Generation | 100ms | Filter by capacity/connectivity |
| Scoring | 300ms | Multi-objective, cached distances |
| Distance Lookup | 1ms | O(1) hash table |
| Total Dispatch Cycle | 500ms | Includes all above + overhead |

---

## Configuration & Extensibility

### Customizable Weights (`ScoringWeights`)
```python
weights = ScoringWeights(
    delivery_time_weight=0.30,
    sla_risk_weight=0.35,
    fairness_weight=0.20,
    priority_weight=0.10,
    agent_rating_weight=0.05
)
optimizer = SimulatedAnnealingOptimizer(weights=weights)
```

### Constraint Support
- Max active orders per agent (default 2)
- Agent availability (status flag)
- SLA deadlines (exponential penalty)
- Connectivity (graph pathfinding)

---

## Testing Strategy

### Unit Tests
- `test_models.py`: Agent/Order/Graph validation
- `test_optimizer.py`: Scoring functions, candidate generation
- `test_data_loader.py`: CSV parsing, error handling

### Integration Tests
- `test_dispatch_cycle.py`: Full pipeline with sample data
- `test_state_consistency.py`: Concurrent assign/release operations

### Performance Tests
- `test_latency.py`: Verify <500ms per cycle
- `test_scaling.py`: Agent/order count scaling

---

## Known Limitations & Future Work

1. **Simulated Annealing**: Currently greedy; true SA cooling schedule TBD
2. **Concurrency**: Single-threaded; future multi-threaded dispatcher
3. **Persistence**: No database; in-memory only for hackathon
4. **Real-time Updates**: Dashboard uses polling; WebSocket upgrade pending
5. **Constraint Handling**: Hard constraints only; soft constraints TBD

---

## File Statistics

- Total files created: 14
- Total lines of boilerplate: ~1200
- Type hints coverage: 100%
- Docstring coverage: 100%
- TODO comments: ~25 (marking implementation points)

---

## References

- **Issue 1**: Order loading and SLA tracking → `Order` model, `DataLoader`
- **Issue 2**: System initialization → `StateManager.__init__`
- **Issue 3**: Environment connectivity → `EnvironmentGraph.has_path()`
- **Issue 4**: Priority queue → `StateManager.order_queue` (heapq)
- **Issue 5**: Agent registry → `StateManager.agent_registry`
- **Issue 7**: Multi-objective scoring → `Optimizer._score_assignment()`
- **Issue 18**: Performance monitoring → `MetricsCalculator`, `Optimizer._latency_log`

