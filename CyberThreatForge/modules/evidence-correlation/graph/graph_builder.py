"""Evidence correlation graph builder with NetworkX.

Constructs a heterogeneous graph from forensic evidence across all modules,
supporting deduplication, temporal weighting, and chain-of-custody integration.
"""

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import networkx as nx


class NodeType(str, Enum):
    FILE = "file"
    IP = "ip"
    DOMAIN = "domain"
    EMAIL = "email"
    PERSON = "person"
    DEVICE = "device"
    LOCATION = "location"
    EVENT = "event"
    ORGANIZATION = "organization"


class EdgeType(str, Enum):
    COMMUNICATES = "communicates"
    ACCESSES = "accesses"
    CONTAINS = "contains"
    SIMILAR_TO = "similar_to"
    OWNED_BY = "owned_by"
    LOCATED_AT = "located_at"
    TEMPORAL_FOLLOWS = "temporal_follows"


class GraphNode:
    def __init__(
        self,
        node_id: str,
        node_type: NodeType,
        label: str,
        metadata: Optional[dict[str, Any]] = None,
        case_id: str = "",
        domain: str = "",
        timestamp: Optional[str] = None,
    ):
        self.node_id = node_id
        self.node_type = node_type
        self.label = label
        self.metadata = metadata or {}
        self.case_id = case_id
        self.domain = domain
        self.timestamp = timestamp

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "label": self.label,
            "metadata": self.metadata,
            "case_id": self.case_id,
            "domain": self.domain,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphNode":
        return cls(
            node_id=data["node_id"],
            node_type=NodeType(data["node_type"]),
            label=data["label"],
            metadata=data.get("metadata", {}),
            case_id=data.get("case_id", ""),
            domain=data.get("domain", ""),
            timestamp=data.get("timestamp"),
        )


class GraphEdge:
    def __init__(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        weight: float = 1.0,
        metadata: Optional[dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.edge_type = edge_type
        self.weight = weight
        self.metadata = metadata or {}
        self.timestamp = timestamp

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "weight": self.weight,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class EvidenceGraph:
    def __init__(self):
        self._graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self._node_index: dict[str, dict[str, str]] = defaultdict(dict)

    @property
    def graph(self) -> nx.MultiDiGraph:
        return self._graph

    def add_node(self, node: GraphNode) -> str:
        key = self._dedup_key(node)
        existing = self._node_index[node.node_type.value].get(key)
        if existing:
            self._merge_node(existing, node)
            return existing

        attrs = node.to_dict()
        self._graph.add_node(node.node_id, **attrs)
        self._node_index[node.node_type.value][key] = node.node_id
        return node.node_id

    def add_edge(self, edge: GraphEdge) -> str:
        if not self._graph.has_node(edge.source_id) or not self._graph.has_node(edge.target_id):
            raise ValueError(f"Cannot add edge: source or target node missing")

        edge_id = self._edge_id(edge)
        attrs = edge.to_dict()
        self._graph.add_edge(edge.source_id, edge.target_id, key=edge_id, **attrs)
        return edge_id

    def add_evidence_item(
        self,
        evidence: dict[str, Any],
        case_id: str = "",
        domain: str = "",
    ) -> list[str]:
        added: list[str] = []
        nodes = self._evidence_to_nodes(evidence, case_id, domain)
        for node in nodes:
            uid = self.add_node(node)
            added.append(uid)

        edges = self._evidence_to_edges(evidence, nodes)
        for edge in edges:
            try:
                eid = self.add_edge(edge)
                added.append(eid)
            except ValueError:
                pass

        return added

    def remove_node(self, node_id: str) -> bool:
        if not self._graph.has_node(node_id):
            return False
        node_data = self._graph.nodes[node_id]
        ntype = node_data.get("node_type", "")
        label = node_data.get("label", "")
        key = self._hash_key(ntype, label)
        if key in self._node_index.get(ntype, {}):
            del self._node_index[ntype][key]
        self._graph.remove_node(node_id)
        return True

    def clear(self):
        self._graph.clear()
        self._node_index.clear()

    def node_count(self) -> int:
        return self._graph.number_of_nodes()

    def edge_count(self) -> int:
        return self._graph.number_of_edges()

    def get_node(self, node_id: str) -> Optional[dict[str, Any]]:
        if self._graph.has_node(node_id):
            return dict(self._graph.nodes[node_id])
        return None

    def get_neighbors(
        self, node_id: str, edge_type: Optional[EdgeType] = None
    ) -> list[tuple[str, dict[str, Any], str]]:
        results: list[tuple[str, dict[str, Any], str]] = []
        if not self._graph.has_node(node_id):
            return results
        for _, target, key, data in self._graph.edges(node_id, keys=True, data=True):
            if edge_type is None or data.get("edge_type") == edge_type.value:
                results.append((target, dict(self._graph.nodes[target]), key))
        return results

    def serialize(self) -> dict[str, Any]:
        return nx.node_link_data(self._graph)

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "EvidenceGraph":
        eg = cls()
        eg._graph = nx.node_link_graph(data)
        for nid, ndata in eg._graph.nodes(data=True):
            ntype = ndata.get("node_type", "")
            label = ndata.get("label", "")
            if ntype and label:
                key = eg._hash_key(ntype, label)
                eg._node_index[ntype][key] = nid
        return eg

    def to_undirected(self) -> nx.Graph:
        return nx.Graph(self._graph)

    def _dedup_key(self, node: GraphNode) -> str:
        return self._hash_key(node.node_type.value, node.label)

    def _hash_key(self, ntype: str, label: str) -> str:
        raw = f"{ntype}:{label.lower().strip()}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _merge_node(self, existing_id: str, incoming: GraphNode):
        existing_data = self._graph.nodes[existing_id]
        existing_data["metadata"].update(incoming.metadata)
        if incoming.case_id and incoming.case_id not in existing_data.get("case_id", ""):
            existing_data["case_id"] = incoming.case_id
        if incoming.domain and incoming.domain not in existing_data.get("domain", ""):
            existing_data["domain"] = incoming.domain
        ts_a = existing_data.get("timestamp")
        ts_b = incoming.timestamp
        if ts_a and ts_b:
            existing_data["timestamp"] = max(ts_a, ts_b)
        elif ts_b:
            existing_data["timestamp"] = ts_b

    def _edge_id(self, edge: GraphEdge) -> str:
        raw = json.dumps({
            "s": edge.source_id,
            "t": edge.target_id,
            "t": edge.edge_type.value,
        }, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _evidence_to_nodes(
        self,
        evidence: dict[str, Any],
        case_id: str,
        domain: str,
    ) -> list[GraphNode]:
        nodes: list[GraphNode] = []
        ts = evidence.get("timestamp") or datetime.now(timezone.utc).isoformat()

        for key, val in evidence.get("files", {}).items():
            if isinstance(val, dict):
                nodes.append(GraphNode(
                    node_id=val.get("id", f"file_{key}"),
                    node_type=NodeType.FILE,
                    label=val.get("path", key),
                    metadata=val,
                    case_id=case_id,
                    domain=domain,
                    timestamp=ts,
                ))

        for ip in evidence.get("ip_addresses", []):
            nodes.append(GraphNode(
                node_id=f"ip_{ip}",
                node_type=NodeType.IP,
                label=ip,
                metadata={"address": ip},
                case_id=case_id,
                domain=domain,
                timestamp=ts,
            ))

        for dom in evidence.get("domains", []):
            nodes.append(GraphNode(
                node_id=f"domain_{dom}",
                node_type=NodeType.DOMAIN,
                label=dom,
                metadata={"domain": dom},
                case_id=case_id,
                domain=domain,
                timestamp=ts,
            ))

        for email in evidence.get("emails", []):
            nodes.append(GraphNode(
                node_id=f"email_{hashlib.md5(email.encode()).hexdigest()}",
                node_type=NodeType.EMAIL,
                label=email,
                metadata={"address": email},
                case_id=case_id,
                domain=domain,
                timestamp=ts,
            ))

        for person in evidence.get("persons", []):
            name = person if isinstance(person, str) else person.get("name", "unknown")
            nodes.append(GraphNode(
                node_id=f"person_{hashlib.md5(name.encode()).hexdigest()}",
                node_type=NodeType.PERSON,
                label=name,
                metadata=person if isinstance(person, dict) else {"name": person},
                case_id=case_id,
                domain=domain,
                timestamp=ts,
            ))

        for device in evidence.get("devices", []):
            dev_id = device if isinstance(device, str) else device.get("id", device.get("name", "unknown"))
            nodes.append(GraphNode(
                node_id=f"device_{hashlib.md5(str(dev_id).encode()).hexdigest()}",
                node_type=NodeType.DEVICE,
                label=str(dev_id),
                metadata=device if isinstance(device, dict) else {"id": device},
                case_id=case_id,
                domain=domain,
                timestamp=ts,
            ))

        for loc in evidence.get("locations", []):
            lat = loc.get("latitude", 0) if isinstance(loc, dict) else 0
            lon = loc.get("longitude", 0) if isinstance(loc, dict) else 0
            loc_id = f"loc_{lat}_{lon}"
            nodes.append(GraphNode(
                node_id=loc_id,
                node_type=NodeType.LOCATION,
                label=f"({lat}, {lon})",
                metadata=loc if isinstance(loc, dict) else {},
                case_id=case_id,
                domain=domain,
                timestamp=ts,
            ))

        for event in evidence.get("events", []):
            evt_id = event.get("id", f"evt_{hashlib.md5(json.dumps(event, default=str).encode()).hexdigest()[:12]}")
            nodes.append(GraphNode(
                node_id=evt_id,
                node_type=NodeType.EVENT,
                label=event.get("type", "unknown_event"),
                metadata=event,
                case_id=case_id,
                domain=domain,
                timestamp=event.get("timestamp", ts),
            ))

        for org in evidence.get("organizations", []):
            org_name = org if isinstance(org, str) else org.get("name", "unknown")
            nodes.append(GraphNode(
                node_id=f"org_{hashlib.md5(org_name.encode()).hexdigest()}",
                node_type=NodeType.ORGANIZATION,
                label=org_name,
                metadata=org if isinstance(org, dict) else {"name": org},
                case_id=case_id,
                domain=domain,
                timestamp=ts,
            ))

        return nodes

    def _evidence_to_edges(
        self,
        evidence: dict[str, Any],
        nodes: list[GraphNode],
    ) -> list[GraphEdge]:
        edges: list[GraphEdge] = []
        node_map = {n.node_id: n for n in nodes}

        for conn in evidence.get("communications", []):
            src = conn.get("source", "")
            tgt = conn.get("target", "")
            src_id = f"ip_{src}" if src else None
            tgt_id = f"ip_{tgt}" if tgt else None
            if src_id and tgt_id and src_id in node_map and tgt_id in node_map:
                edges.append(GraphEdge(
                    source_id=src_id,
                    target_id=tgt_id,
                    edge_type=EdgeType.COMMUNICATES,
                    weight=conn.get("weight", 1.0),
                    metadata=conn,
                    timestamp=conn.get("timestamp"),
                ))

        for access in evidence.get("accesses", []):
            src = access.get("actor", "")
            tgt = access.get("target", "")
            src_id = None
            tgt_id = None
            for nid, node in node_map.items():
                if node.label == src or nid == src:
                    src_id = nid
                if node.label == tgt or nid == tgt:
                    tgt_id = nid
            if src_id and tgt_id:
                edges.append(GraphEdge(
                    source_id=src_id,
                    target_id=tgt_id,
                    edge_type=EdgeType.ACCESSES,
                    weight=access.get("weight", 1.0),
                    metadata=access,
                    timestamp=access.get("timestamp"),
                ))

        file_ids = [n.node_id for n in nodes if n.node_type == NodeType.FILE]
        for fid in file_ids:
            parent = evidence.get("container_id")
            if parent and parent in node_map:
                edges.append(GraphEdge(
                    source_id=parent,
                    target_id=fid,
                    edge_type=EdgeType.CONTAINS,
                    weight=1.0,
                ))

        ip_nodes = [n for n in nodes if n.node_type == NodeType.IP]
        domain_nodes = [n for n in nodes if n.node_type == NodeType.DOMAIN]
        for ip_node in ip_nodes:
            for dom_node in domain_nodes:
                edges.append(GraphEdge(
                    source_id=ip_node.node_id,
                    target_id=dom_node.node_id,
                    edge_type=EdgeType.ACCESSES,
                    weight=0.8,
                    metadata={"relationship": "ip_to_domain"},
                ))

        _all_ids = list(node_map.keys())
        for i in range(len(_all_ids)):
            for j in range(i + 1, len(_all_ids)):
                a_id = _all_ids[i]
                b_id = _all_ids[j]
                ts_a = node_map[a_id].timestamp
                ts_b = node_map[b_id].timestamp
                if ts_a and ts_b:
                    try:
                        dt_a = datetime.fromisoformat(ts_a)
                        dt_b = datetime.fromisoformat(ts_b)
                        if dt_a < dt_b:
                            edges.append(GraphEdge(
                                source_id=a_id,
                                target_id=b_id,
                                edge_type=EdgeType.TEMPORAL_FOLLOWS,
                                weight=self._temporal_weight(dt_a, dt_b),
                                timestamp=ts_b,
                            ))
                    except (ValueError, TypeError):
                        pass

        return edges

    @staticmethod
    def _temporal_weight(dt_a: datetime, dt_b: datetime) -> float:
        delta = abs((dt_b - dt_a).total_seconds())
        if delta == 0:
            return 1.0
        return max(0.1, min(1.0, 3600.0 / delta))
