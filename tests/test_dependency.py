import networkx as nx
import pytest

from rcaground.agents.rca import Claim
from rcaground.bench.dependency import classify_edge, hallucinated_dependency_rate


@pytest.fixture
def topo():
    g = nx.DiGraph([("frontend", "checkout"), ("checkout", "db")])
    g.add_nodes_from(["lonely", "other"])
    return g


def _claim(*edges):
    return Claim(text="t", evidence_ids=["kpi:db:cpu"], confidence=0.5, causal_edges=list(edges))


def test_classes(topo):
    assert classify_edge(("db", "frontend"), topo) == "consistent"
    assert classify_edge(("db", "checkout"), topo) == "consistent"
    assert classify_edge(("frontend", "db"), topo) == "call_direction"
    assert classify_edge(("lonely", "other"), topo) == "unsupported"
    assert classify_edge(("db", "ghost"), topo) == "unknown_service"
    assert classify_edge(("ghost", "db"), topo) == "unknown_service"


def test_cycle_is_consistent():
    g = nx.DiGraph([("a", "b"), ("b", "a")])
    assert classify_edge(("a", "b"), g) == "consistent"


def test_hdr_counts(topo):
    r = hallucinated_dependency_rate(
        [_claim(("db", "frontend"), ("lonely", "other")), _claim(("db", "ghost"), ("db", "frontend"))],
        topo,
    )
    assert r == {
        "hdr": 0.5, "consistent": 1, "call_direction": 0, "unsupported": 1,
        "unknown_service": 1, "n_edges": 3,
    }


def test_self_edges_ignored(topo):
    assert hallucinated_dependency_rate([_claim(("db", "db"))], topo) is None


def test_none_cases(topo):
    assert hallucinated_dependency_rate([_claim()], topo) is None
    assert hallucinated_dependency_rate([_claim(("db", "frontend"))], None) is None
    assert hallucinated_dependency_rate([_claim(("db", "frontend"))], nx.DiGraph()) is None


def test_all_unknown_has_no_rate(topo):
    r = hallucinated_dependency_rate([_claim(("x", "y"))], topo)
    assert r["hdr"] is None and r["unknown_service"] == 1 and r["n_edges"] == 1
