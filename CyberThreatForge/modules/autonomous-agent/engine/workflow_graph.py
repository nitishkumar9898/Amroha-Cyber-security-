import uuid
from collections import defaultdict, deque
from typing import Any, Callable, Optional


class CycleDetectedError(Exception):
    pass


class NodeNotFoundError(Exception):
    pass


class GraphNode:
    def __init__(
        self,
        node_id: str,
        label: str = "",
        data: Optional[dict[str, Any]] = None,
    ):
        self.id = node_id
        self.label = label
        self.data = data or {}
        self.status: str = "pending"
        self.result: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "status": self.status,
            "data": self.data,
        }


class GraphEdge:
    def __init__(
        self,
        source: str,
        target: str,
        condition: Optional[Callable[..., bool]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.source = source
        self.target = target
        self.condition = condition
        self.metadata = metadata or {}

    def evaluate(self, context: dict[str, Any]) -> bool:
        if self.condition is None:
            return True
        return self.condition(context)


class WorkflowGraph:
    def __init__(self):
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []
        self._adjacency: dict[str, list[str]] = defaultdict(list)
        self._reverse_adj: dict[str, list[str]] = defaultdict(list)
        self._state: dict[str, Any] = {}

    def add_node(self, node_id: str, label: str = "", data: Optional[dict[str, Any]] = None) -> GraphNode:
        if node_id in self._nodes:
            raise ValueError(f"Node {node_id} already exists")
        node = GraphNode(node_id, label, data)
        self._nodes[node_id] = node
        return node

    def remove_node(self, node_id: str) -> None:
        if node_id not in self._nodes:
            raise NodeNotFoundError(f"Node {node_id} not found")
        self._edges = [e for e in self._edges if e.source != node_id and e.target != node_id]
        self._adjacency.pop(node_id, None)
        self._reverse_adj.pop(node_id, None)
        for src in list(self._adjacency):
            self._adjacency[src] = [t for t in self._adjacency[src] if t != node_id]
        for tgt in list(self._reverse_adj):
            self._reverse_adj[tgt] = [s for s in self._reverse_adj[tgt] if s != node_id]
        del self._nodes[node_id]

    def add_edge(
        self,
        source: str,
        target: str,
        condition: Optional[Callable[..., bool]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> GraphEdge:
        if source not in self._nodes:
            raise NodeNotFoundError(f"Source node {source} not found")
        if target not in self._nodes:
            raise NodeNotFoundError(f"Target node {target} not found")
        edge = GraphEdge(source, target, condition, metadata)
        self._edges.append(edge)
        self._adjacency[source].append(target)
        self._reverse_adj[target].append(source)

        if self._detect_cycle():
            self._edges.pop()
            self._adjacency[source].remove(target)
            self._reverse_adj[target].remove(source)
            raise CycleDetectedError(f"Adding edge {source} -> {target} would create a cycle")

        return edge

    def _detect_cycle(self) -> bool:
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in self._adjacency.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        for nid in self._nodes:
            if nid not in visited:
                if dfs(nid):
                    return True
        return False

    def topological_sort(self) -> list[str]:
        in_degree: dict[str, int] = {nid: 0 for nid in self._nodes}
        for edge in self._edges:
            in_degree[edge.target] += 1

        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        result: list[str] = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in self._adjacency.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self._nodes):
            raise CycleDetectedError("Graph contains a cycle, cannot perform topological sort")

        return result

    def get_parallel_layers(self) -> list[list[str]]:
        in_degree: dict[str, int] = {nid: 0 for nid in self._nodes}
        for edge in self._edges:
            in_degree[edge.target] += 1

        layers: list[list[str]] = []
        remaining = set(self._nodes.keys())

        while remaining:
            current_layer = [nid for nid in remaining if in_degree.get(nid, 0) == 0]
            if not current_layer:
                raise CycleDetectedError("Graph contains a cycle, cannot compute layers")
            layers.append(current_layer)
            for nid in current_layer:
                remaining.remove(nid)
                for neighbor in self._adjacency.get(nid, []):
                    in_degree[neighbor] = max(0, in_degree[neighbor] - 1)

        return layers

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def get_edge_conditions(self, source: str, target: str) -> list[GraphEdge]:
        return [e for e in self._edges if e.source == source and e.target == target]

    def get_dependents(self, node_id: str) -> list[str]:
        return self._adjacency.get(node_id, [])

    def get_dependencies(self, node_id: str) -> list[str]:
        return self._reverse_adj.get(node_id, [])

    def get_upstream_nodes(self, node_id: str) -> set[str]:
        upstream: set[str] = set()

        def walk(nid: str) -> None:
            for dep in self._reverse_adj.get(nid, []):
                if dep not in upstream:
                    upstream.add(dep)
                    walk(dep)

        walk(node_id)
        return upstream

    def get_downstream_nodes(self, node_id: str) -> set[str]:
        downstream: set[str] = set()

        def walk(nid: str) -> None:
            for dep in self._adjacency.get(nid, []):
                if dep not in downstream:
                    downstream.add(dep)
                    walk(dep)

        walk(node_id)
        return downstream

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)

    def set_state(self, key: str, value: Any) -> None:
        self._state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def update_state(self, updates: dict[str, Any]) -> None:
        self._state.update(updates)

    def clear_state(self) -> None:
        self._state.clear()

    def reset_node_status(self) -> None:
        for node in self._nodes.values():
            node.status = "pending"
            node.result = None

    def find_path(self, source: str, target: str) -> list[str]:
        if source not in self._nodes or target not in self._nodes:
            return []
        visited: set[str] = set()
        queue: deque[tuple[str, list[str]]] = deque([(source, [source])])
        while queue:
            current, path = queue.popleft()
            if current == target:
                return path
            visited.add(current)
            for neighbor in self._adjacency.get(current, []):
                if neighbor not in visited:
                    queue.append((neighbor, [*path, neighbor]))
        return []

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "condition": str(e.condition) if e.condition else None,
                }
                for e in self._edges
            ],
            "state": self._state,
        }
