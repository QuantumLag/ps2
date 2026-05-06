# Smart Delivery Dispatch System

## Team Information
- **Team Name**: Logic Lauds
- **Year**: 1st
- **All-Female Team**: No

## Architecture Overview

#### Describe your approach here. Keep it short and clear.

We use a **Quantum-Inspired Simulated Annealing** approach to solve dispatching as a global optimization problem. By treating the fleet as a single interconnected system, we use the Metropolis-Hastings algorithm to "tunnel" through local inefficiencies and find a global energy minimum for city-wide logistics.

- **What is your dispatch strategy?**
  A **Global Optimization Strategy** that models assignments as a physical system. The engine iteratively swaps assignments and uses a "temperature" variable to accept or reject moves, ensuring the system converges on the most efficient total dispatch plan rather than just local "best fits".

- **How do you score agents for incoming orders?**
  Assignments are evaluated via a **Multi-Objective Cost Function**[cite: 2]:
  - **Travel Time:** Real-time distance lookups adjusted by dynamic traffic multipliers.
  - **Performance:** Weighting based on agent ratings for high-stakes deliveries.
  - **Fairness:** A penalty on overworked agents to ensure sustainable workload distribution.

- **How do you manage SLA deadlines, priority orders, and agent capacity?**
  - **Priority & SLA:** A **Priority Queue** sorts orders by tier (High > Normal > Low), while the cost function applies an exponential penalty as SLA deadlines approach.
  - **Capacity:** A **Hard Constraint Barrier** is enforced; any assignment exceeding the 2-order-per-agent limit is given an infinite cost, making it mathematically impossible to select.

- **What are the main steps in your pipeline?**
  1. **Ingestion:** Validate and load CSV data for agents, orders, and edges.
  2. **Precomputation:** Generate a shortest-path matrix for $O(1)$ routing lookups.
  3. **Optimization:** Run the annealing loop to "collapse" the best assignment state.
  4. **Execution:** Atomically update states and record real-time performance metrics.


**Note:** Please do not change the format or spelling of anything in this README. The fields are extracted using a script, so any changes to the structure or formatting may break the extraction process.
