"""
rcaground/bench/dependency.py — Hallucinated Dependency Rate (HDR).

A claimed causal edge (source, target) says a fault propagated from source to
target. Faults flow against call edges, so the edge is structurally plausible
when the target reaches the source along caller -> callee edges.
"""

from __future__ import annotations

from typing import Iterable, Optional

import networkx as nx

from rcaground.agents.rca import Claim

CLASSES = ("consistent", "call_direction", "unsupported", "unknown_service")


def classify_edge(edge: tuple[str, str], topology: nx.DiGraph) -> str:
    source, target = edge
    if source not in topology or target not in topology:
        return "unknown_service"
    if nx.has_path(topology, target, source):
        return "consistent"
    if nx.has_path(topology, source, target):
        return "call_direction"
    return "unsupported"


def hallucinated_dependency_rate(
    claims: Iterable[Claim], topology: Optional[nx.DiGraph]
) -> Optional[dict]:
    """Per-case HDR over the distinct, non-self edges claimed.

    None when there is no topology or no claimed edge. `hdr` is None when every
    edge is `unknown_service` (empty denominator); counts are still returned.
    """
    edges = {e for c in claims for e in c.causal_edges if e[0] != e[1]}
    if not edges or topology is None or topology.number_of_nodes() == 0:
        return None
    counts = dict.fromkeys(CLASSES, 0)
    for e in edges:
        counts[classify_edge(e, topology)] += 1
    classified = len(edges) - counts["unknown_service"]
    return {
        "hdr": counts["unsupported"] / classified if classified else None,
        **counts,
        "n_edges": len(edges),
    }
