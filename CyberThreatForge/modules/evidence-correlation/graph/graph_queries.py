"""Graph query engine for evidence correlation graphs.

Provides shortest-path, community detection, centrality analysis,
subgraph extraction, pattern matching, and temporal subgraph queries.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, Optional, Union

import networkx as nx
from networkx.algorithms import community
from networkx.algorithms import centrality as nx_centrality

from .graph_builder import EvidenceGraph, EdgeType


class CommunityResult:
    def __init__(self, community_id: int, nodes: list[dict[str, Any]], size: int, modularity: float):
        self.community_id = community_id
        self.nodes = nodes
        self.size = size
        self.modularity = modularity

    def to_dict(self) -> dict[str, Any]:
        return {
            "community_id": self.community_id,
            "nodes": self.nodes,
            "size": self.size,
            "modularity": self.modularity,
        }


class CentralityResult:
    def __init__(self, node_id: str, label: str, node_type: str, score: float):
        self.node_id = node_id
        self.label = label
        self.node_type = node_type
        self.score = score

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "node_type": self.node_type,
            "score": self.score,
        }


class PatternMatch:
    def __init__(self, nodes: list[str], edges: list[tuple[str, str]], pattern_type: str, score: float):
        self.nodes = nodes
        self.edges = edges
        self.pattern_type = pattern_type
        self.score = score

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": [[s, t] for s, t in self.edges],
            "pattern_type": self.pattern_type,
            "score": self.score,
        }


class GraphQueryEngine:
    def __init__(self, evidence_graph: EvidenceGraph):
        self._eg = evidence_graph

    @property
    def graph(self) -> nx.MultiDiGraph:
        return self._eg.graph

    def shortest_path(
        self,
        source_id: str,
        target_id: str,
        weight: Optional[str] = "weight",
    ) -> Optional[list[str]]:
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            return None
        try:
            g_simple = nx.Graph(self.graph)
            path = nx.shortest_path(g_simple, source=source_id, target=target_id, weight=weight)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def shortest_path_details(
        self,
        source_id: str,
        target_id: str,
    ) -> Optional[dict[str, Any]]:
        path = self.shortest_path(source_id, target_id)
        if not path:
            return None
        g_simple = nx.Graph(self.graph)
        try:
            length = nx.shortest_path_length(g_simple, source=source_id, target=target_id, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            length = float("inf")

        node_details = []
        for nid in path:
            nd = dict(self.graph.nodes[nid])
            nd["node_id"] = nid
            node_details.append(nd)

        return {
            "path": path,
            "length": length,
            "node_count": len(path),
            "nodes": node_details,
        }

    def all_shortest_paths(
        self,
        source_id: str,
        target_id: str,
        max_paths: int = 10,
    ) -> list[list[str]]:
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            return []
        try:
            g_simple = nx.Graph(self.graph)
            paths = list(nx.all_shortest_paths(g_simple, source=source_id, target=target_id))
            return paths[:max_paths]
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def detect_communities_louvain(
        self,
        resolution: float = 1.0,
        min_size: int = 2,
    ) -> list[CommunityResult]:
        g_undirected = self._eg.to_undirected()
        if g_undirected.number_of_nodes() < 2:
            return []

        try:
            partition = community.louvain_communities(g_undirected, resolution=resolution)
        except (ImportError, Exception):
            partition = community.greedy_modularity_communities(g_undirected)

        communities: list[CommunityResult] = []
        for cid, node_set in enumerate(partition):
            if len(node_set) < min_size:
                continue
            node_details = []
            for nid in node_set:
                nd = dict(self.graph.nodes[nid])
                nd["node_id"] = nid
                node_details.append(nd)
            try:
                modularity_val = community.modularity(g_undirected, partition)
            except Exception:
                modularity_val = 0.0
            communities.append(CommunityResult(
                community_id=cid,
                nodes=node_details,
                size=len(node_set),
                modularity=modularity_val,
            ))

        return communities

    def detect_communities_label_propagation(
        self,
        min_size: int = 2,
    ) -> list[CommunityResult]:
        g_undirected = self._eg.to_undirected()
        if g_undirected.number_of_nodes() < 2:
            return []

        try:
            partition_gen = community.label_propagation_communities(g_undirected)
            communities: list[CommunityResult] = []
            for cid, node_set in enumerate(partition_gen):
                if len(node_set) < min_size:
                    continue
                node_details = []
                for nid in node_set:
                    nd = dict(self.graph.nodes[nid])
                    nd["node_id"] = nid
                    node_details.append(nd)
                communities.append(CommunityResult(
                    community_id=cid,
                    nodes=node_details,
                    size=len(node_set),
                    modularity=0.0,
                ))
            return communities
        except Exception:
            return []

    def centrality_degree(self, top_k: int = 20) -> list[CentralityResult]:
        g_simple = nx.Graph(self.graph)
        cent = nx_centrality.degree_centrality(g_simple)
        return self._top_centrality(cent, top_k)

    def centrality_betweenness(self, top_k: int = 20, normalized: bool = True) -> list[CentralityResult]:
        g_simple = nx.Graph(self.graph)
        cent = nx_centrality.betweenness_centrality(g_simple, normalized=normalized)
        return self._top_centrality(cent, top_k)

    def centrality_pagerank(self, top_k: int = 20, alpha: float = 0.85) -> list[CentralityResult]:
        g_simple = nx.Graph(self.graph)
        try:
            cent = nx_centrality.pagerank(g_simple, alpha=alpha)
        except Exception:
            cent = nx_centrality.degree_centrality(g_simple)
        return self._top_centrality(cent, top_k)

    def extract_subgraph(
        self,
        node_ids: list[str],
        depth: int = 0,
    ) -> Optional[dict[str, Any]]:
        if not node_ids:
            return None

        if depth > 0:
            neighbors: set[str] = set(node_ids)
            current = set(node_ids)
            for _ in range(depth):
                next_ring: set[str] = set()
                for nid in current:
                    if self.graph.has_node(nid):
                        next_ring.update(self.graph.successors(nid))
                        next_ring.update(self.graph.predecessors(nid))
                neighbors.update(next_ring)
                current = next_ring
            node_ids = list(neighbors)

        sub = self.graph.subgraph(node_ids)
        return nx.node_link_data(sub)

    def extract_subgraph_by_type(
        self,
        node_type: str,
        edge_type: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        nodes_to_include = [
            nid for nid, ndata in self.graph.nodes(data=True)
            if ndata.get("node_type") == node_type
        ]
        if not nodes_to_include:
            return None

        if edge_type:
            edge_filter: list[tuple[str, str]] = []
            for u, v, key, edata in self.graph.edges(keys=True, data=True):
                if edata.get("edge_type") == edge_type:
                    edge_filter.append((u, v))
            edge_nodes = set()
            for u, v in edge_filter:
                if u in nodes_to_include or v in nodes_to_include:
                    edge_nodes.add(u)
                    edge_nodes.add(v)
            nodes_to_include = list(edge_nodes)

        sub = self.graph.subgraph(nodes_to_include)
        return nx.node_link_data(sub)

    def detect_motifs(
        self,
        motif_size: int = 3,
        max_motifs: int = 20,
    ) -> list[PatternMatch]:
        g_undirected = self._eg.to_undirected()
        if g_undirected.number_of_nodes() < motif_size:
            return []

        matches: list[PatternMatch] = []
        try:
            subgraphs = list(nx.enumerate_all_cliques(g_undirected))
            clique_motifs = [sg for sg in subgraphs if len(sg) == motif_size]
            for sub_nodes in clique_motifs[:max_motifs]:
                edges = list(g_undirected.subgraph(sub_nodes).edges())
                matches.append(PatternMatch(
                    nodes=list(sub_nodes),
                    edges=edges,
                    pattern_type=f"K{motif_size}_clique",
                    score=1.0,
                ))
        except Exception:
            from itertools import combinations
            all_nodes = list(g_undirected.nodes())
            if len(all_nodes) >= motif_size:
                for combo in combinations(all_nodes, min(motif_size, len(all_nodes))):
                    sub = g_undirected.subgraph(combo)
                    edge_count = sub.number_of_edges()
                    if edge_count > 0:
                        matches.append(PatternMatch(
                            nodes=list(combo),
                            edges=list(sub.edges()),
                            pattern_type="connected_subgraph",
                            score=edge_count / (motif_size * (motif_size - 1) / 2),
                        ))
                        if len(matches) >= max_motifs:
                            break

        return matches[:max_motifs]

    def temporal_subgraph(
        self,
        start_time: str,
        end_time: str,
    ) -> Optional[dict[str, Any]]:
        node_filter: list[str] = []
        for nid, ndata in self.graph.nodes(data=True):
            ts = ndata.get("timestamp")
            if ts and self._in_window(ts, start_time, end_time):
                node_filter.append(nid)

        if not node_filter:
            return None

        sub = self.graph.subgraph(node_filter)
        return nx.node_link_data(sub)

    def temporal_subgraph_edges(
        self,
        start_time: str,
        end_time: str,
    ) -> Optional[dict[str, Any]]:
        node_ids: set[str] = set()
        edge_list: list[tuple[str, str]] = []
        for u, v, key, edata in self.graph.edges(keys=True, data=True):
            ts = edata.get("timestamp")
            if ts and self._in_window(ts, start_time, end_time):
                node_ids.add(u)
                node_ids.add(v)
                edge_list.append((u, v))

        if not node_ids:
            return None

        sub = self.graph.subgraph(list(node_ids))
        return nx.node_link_data(sub)

    def node_count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for _, ndata in self.graph.nodes(data=True):
            counts[ndata.get("node_type", "unknown")] += 1
        return dict(counts)

    def edge_count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for _, _, edata in self.graph.edges(data=True):
            counts[edata.get("edge_type", "unknown")] += 1
        return dict(counts)

    def graph_summary(self) -> dict[str, Any]:
        g_undirected = nx.Graph(self.graph)
        comps = list(nx.connected_components(g_undirected)) if g_undirected.number_of_nodes() > 0 else []
        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "node_types": self.node_count_by_type(),
            "edge_types": self.edge_count_by_type(),
            "connected_components": len(comps),
            "largest_component_size": max((len(c) for c in comps), default=0),
            "density": nx.density(g_undirected),
            "is_directed": self.graph.is_directed(),
            "has_multiedges": self.graph.is_multigraph(),
        }

    def _top_centrality(self, cent: dict[str, float], top_k: int) -> list[CentralityResult]:
        sorted_nodes = sorted(cent.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results: list[CentralityResult] = []
        for nid, score in sorted_nodes:
            ndata = dict(self.graph.nodes[nid]) if self.graph.has_node(nid) else {}
            results.append(CentralityResult(
                node_id=nid,
                label=ndata.get("label", nid),
                node_type=ndata.get("node_type", "unknown"),
                score=score,
            ))
        return results

    @staticmethod
    def _in_window(ts: str, start: str, end: str) -> bool:
        try:
            dt = datetime.fromisoformat(ts)
            dt_start = datetime.fromisoformat(start)
            dt_end = datetime.fromisoformat(end)
            return dt_start <= dt <= dt_end
        except (ValueError, TypeError):
            return start <= ts <= end
