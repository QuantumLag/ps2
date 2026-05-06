"""Environment and routing domain model."""

from __future__ import annotations

import heapq
from collections import defaultdict
from typing import Dict, Iterable, List, Set, Tuple, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


class EnvironmentGraph:
    """Graph representation of the environment and distances using shortest path algorithms."""

    def __init__(
        self,
        nodes: Iterable[str],
        edges: Dict[Tuple[str, str], float],
        distance_matrix: Dict[Tuple[str, str], float] | None = None,
    ) -> None:
        self.nodes: Set[str] = set(nodes)
        self.edges: Dict[Tuple[str, str], float] = dict(edges)
        self.distance_matrix: Dict[Tuple[str, str], float] = distance_matrix or {}
        self.adjacency: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        
        if nodes and edges:
            self._build_adjacency()

    def _build_adjacency(self) -> None:
        """Build adjacency list from edges for efficient traversal."""
        self.adjacency.clear()
        for (source, target), distance in self.edges.items():
            self.adjacency[source].append((target, distance))

    def add_edge(self, source: str, target: str, distance: float) -> None:
        """Add a directed edge to the environment graph with validation."""
        if source not in self.nodes or target not in self.nodes:
            raise ValueError(f"Edge nodes must exist in graph. Source: {source}, Target: {target}")
        if distance < 0:
            raise ValueError(f"Distance cannot be negative: {distance}")
        
        self.edges[(source, target)] = distance
        self.adjacency[source].append((target, distance))
        logger.debug(f"Added edge {source} -> {target} (distance: {distance})")

    def compute_distance_matrix(self) -> None:
        """Compute all-pairs shortest distances using Floyd-Warshall or Dijkstra."""
        if not self.nodes:
            logger.warning("Cannot compute distance matrix for empty graph.")
            return
        
        num_nodes = len(self.nodes)
        
        # Floyd-Warshall for small graphs (≤ 100 nodes): O(n³)
        if num_nodes <= 100:
            logger.info(f"Using Floyd-Warshall for {num_nodes} nodes.")
            self._floyd_warshall()
        # Dijkstra from each node for larger graphs: O(n * (e log n))
        else:
            logger.info(f"Using Dijkstra for {num_nodes} nodes.")
            self._dijkstra_all_pairs()

    def _floyd_warshall(self) -> None:
        """Floyd-Warshall algorithm for all-pairs shortest paths. O(n³) time."""
        nodes_list = sorted(list(self.nodes))
        node_to_idx = {node: i for i, node in enumerate(nodes_list)}
        n = len(nodes_list)
        
        # Initialize distance matrix with infinity
        dist = [[float('inf')] * n for _ in range(n)]
        
        # Distance from node to itself is 0
        for i in range(n):
            dist[i][i] = 0.0
        
        # Add direct edge weights
        for (source, target), distance in self.edges.items():
            i, j = node_to_idx[source], node_to_idx[target]
            dist[i][j] = min(dist[i][j], distance)
        
        # Relax edges through intermediate nodes
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if dist[i][k] != float('inf') and dist[k][j] != float('inf'):
                        dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
        
        # Store results in distance_matrix
        self.distance_matrix = {}
        for i in range(n):
            for j in range(n):
                if dist[i][j] != float('inf'):
                    self.distance_matrix[(nodes_list[i], nodes_list[j])] = dist[i][j]
        
        logger.info(f"Floyd-Warshall computed {len(self.distance_matrix)} distances.")

    def _dijkstra_all_pairs(self) -> None:
        """Run Dijkstra from each node for larger graphs."""
        self.distance_matrix = {}
        for source in self.nodes:
            distances = self._dijkstra(source)
            for target, distance in distances.items():
                if distance != float('inf'):
                    self.distance_matrix[(source, target)] = distance

    def _dijkstra(self, start: str) -> Dict[str, float]:
        """Dijkstra's algorithm from a single source node. O(e log n) time."""
        distances = {node: float('inf') for node in self.nodes}
        distances[start] = 0.0
        pq = [(0.0, start)]
        visited = set()
        
        while pq:
            current_dist, current_node = heapq.heappop(pq)
            
            if current_node in visited:
                continue
            visited.add(current_node)
            
            # Skip if we've found a better path already
            if current_dist > distances[current_node]:
                continue
            
            # Relax edges from current node
            for neighbor, weight in self.adjacency[current_node]:
                new_distance = current_dist + weight
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    heapq.heappush(pq, (new_distance, neighbor))
        
        return distances

    def distance(self, source: str, target: str) -> float:
        """Return the cached shortest distance between two nodes. O(1) lookup."""
        if not self.distance_matrix:
            self.compute_distance_matrix()
        
        key = (source, target)
        if key not in self.distance_matrix:
            return float('inf')
        return self.distance_matrix[key]

    def neighbors(self, node: str) -> List[str]:
        """Return direct neighbors for a given node."""
        if node not in self.adjacency:
            return []
        return [neighbor for neighbor, _ in self.adjacency[node]]

    def has_path(self, source: str, target: str) -> bool:
        """Check if a valid path exists between two nodes."""
        if source == target:
            return True
        distance = self.distance(source, target)
        return distance != float('inf')