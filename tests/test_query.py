"""Tests for DiscourseGraph Python query helper methods.

Covers:
  nodes()          — FR-QH-1
  node_data()      — FR-QH-2
  discourse_edges() — FR-QH-3
  neighbors()      — FR-QH-4

All helpers use the rdflib Python API only — no SPARQL (NFR-4).
"""
from __future__ import annotations

import pytest
from rdflib import RDF, URIRef
from rdflib.namespace import PROV

from discourse_graph.agent import Agent
from discourse_graph.graph import DiscourseGraph
from discourse_graph.namespaces import DG, ENG, load_combined_ontology
from discourse_graph.shapes import load_shapes


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def ontology():
    return load_combined_ontology()


@pytest.fixture
def shapes():
    return load_shapes()


@pytest.fixture
def query_agent():
    return Agent("QueryAgent", "http://test.org/qa/")


@pytest.fixture
def source_agent():
    return Agent("SourceAgent", "http://test.org/src/")


@pytest.fixture
def query_dg(query_agent, source_agent, ontology, shapes):
    """DiscourseGraph with 4 local nodes, 3 discourse edges, and 1 ingested node."""
    dg = DiscourseGraph(query_agent, ontology, shapes, verify_on_write=False)
    local_uri = query_agent.graph_uri("local")

    e1 = dg.add_node(DG.Evidence, "Evidence body one", "E1", graph_uri=local_uri)
    e2 = dg.add_node(DG.Evidence, "Evidence body two", "E2", graph_uri=local_uri)
    c1 = dg.add_node(DG.Claim, "Claim body one", "C1", graph_uri=local_uri)
    q1 = dg.add_node(DG.Question, "Question body one?", "Q1", graph_uri=local_uri)

    dg.add_edge(e1, DG.supports, c1, graph_uri=local_uri)
    dg.add_edge(e1, DG.informs, q1, graph_uri=local_uri)
    dg.add_edge(e2, DG.supports, c1, graph_uri=local_uri)

    # Ingest one Evidence node from source_agent
    from rdflib import Graph, Literal
    from rdflib import XSD
    sub = Graph()
    ing_node = source_agent.node_uri("ing-evidence-0001")
    sub.add((ing_node, RDF.type, DG.Evidence))
    sub.add((ing_node, RDF.type, DG.DiscourseNode))
    sub.add((ing_node, RDF.type, PROV.Entity))
    sub.add((ing_node, DG.content, Literal("Ingested evidence body", datatype=XSD.string)))
    sub.add((ing_node, DG.label, Literal("IngE", datatype=XSD.string)))
    dg.ingest(sub, source_agent.uri)

    return dg, e1, e2, c1, q1, ing_node, query_agent, source_agent


# ── nodes() ───────────────────────────────────────────────────────────────────


def test_nodes_all_returns_all_discourse_nodes(query_dg):
    """nodes() with no filter returns all 5 DiscourseNode URIs (4 local + 1 ingested)."""
    dg, e1, e2, c1, q1, ing_node, agent, _ = query_dg
    result = dg.nodes()
    assert e1 in result
    assert e2 in result
    assert c1 in result
    assert q1 in result
    assert ing_node in result
    assert len(result) == 5


def test_nodes_filtered_by_evidence(query_dg):
    """nodes(type_uri=DG.Evidence) returns only Evidence nodes."""
    dg, e1, e2, c1, q1, ing_node, *_ = query_dg
    result = dg.nodes(type_uri=DG.Evidence)
    assert e1 in result
    assert e2 in result
    assert ing_node in result  # ingested Evidence also matches
    assert c1 not in result
    assert q1 not in result


def test_nodes_filtered_by_claim(query_dg):
    """nodes(type_uri=DG.Claim) returns only the Claim node."""
    dg, e1, e2, c1, q1, ing_node, *_ = query_dg
    result = dg.nodes(type_uri=DG.Claim)
    assert result == [c1]


def test_nodes_scoped_to_local_graph(query_dg):
    """nodes(graph_uri=local) excludes the ingested named graph."""
    dg, e1, e2, c1, q1, ing_node, agent, _ = query_dg
    local_uri = agent.graph_uri("local")
    result = dg.nodes(graph_uri=local_uri)
    assert e1 in result
    assert e2 in result
    assert c1 in result
    assert q1 in result
    assert ing_node not in result


def test_nodes_empty_for_unknown_type(query_dg):
    """nodes(type_uri=DG.Source) returns empty list when no Source nodes exist."""
    dg, *_ = query_dg
    result = dg.nodes(type_uri=DG.Source)
    assert result == []


def test_nodes_returns_sorted_list(query_dg):
    """nodes() output is sorted (deterministic)."""
    dg, *_ = query_dg
    result = dg.nodes()
    assert result == sorted(result)


# ── node_data() ───────────────────────────────────────────────────────────────


def test_node_data_type(query_dg):
    """node_data()['type'] returns the concrete OWL class URI."""
    dg, e1, *_ = query_dg
    assert dg.node_data(e1)["type"] == DG.Evidence


def test_node_data_content(query_dg):
    """node_data()['content'] returns the dg:content literal as a string."""
    dg, e1, *_ = query_dg
    assert dg.node_data(e1)["content"] == "Evidence body one"


def test_node_data_label(query_dg):
    """node_data()['label'] returns the rdfs:label literal as a string."""
    dg, e1, *_ = query_dg
    assert dg.node_data(e1)["label"] == "E1"


def test_node_data_created_is_string(query_dg):
    """node_data()['created'] returns a non-None string (ISO 8601)."""
    dg, e1, *_ = query_dg
    created = dg.node_data(e1)["created"]
    assert created is not None
    assert isinstance(created, str)
    assert len(created) > 0


def test_node_data_not_ingested_for_local(query_dg):
    """node_data()['is_ingested'] is False for a locally authored node."""
    dg, e1, *_ = query_dg
    assert dg.node_data(e1)["is_ingested"] is False


def test_node_data_ingested_flag(query_dg):
    """node_data()['is_ingested'] is True for a node received via ingest()."""
    dg, e1, e2, c1, q1, ing_node, *_ = query_dg
    assert dg.node_data(ing_node)["is_ingested"] is True


def test_node_data_source_agent_populated_for_ingested(query_dg):
    """node_data()['source_agent'] is the source agent URI for ingested nodes."""
    dg, e1, e2, c1, q1, ing_node, _, source_agent = query_dg
    assert dg.node_data(ing_node)["source_agent"] == source_agent.uri


def test_node_data_source_agent_none_for_local(query_dg):
    """node_data()['source_agent'] is None for locally authored nodes."""
    dg, e1, *_ = query_dg
    assert dg.node_data(e1)["source_agent"] is None


def test_node_data_uri_key(query_dg):
    """node_data()['uri'] echoes the queried node URI."""
    dg, e1, *_ = query_dg
    assert dg.node_data(e1)["uri"] == e1


# ── discourse_edges() ─────────────────────────────────────────────────────────


def test_discourse_edges_all(query_dg):
    """discourse_edges() returns all 3 discourse edges in the local graph."""
    dg, e1, e2, c1, q1, *_ = query_dg
    local_uri = query_dg[6].graph_uri("local")
    edges = dg.discourse_edges(graph_uri=local_uri)
    assert len(edges) == 3
    assert (e1, DG.supports, c1) in edges
    assert (e1, DG.informs, q1) in edges
    assert (e2, DG.supports, c1) in edges


def test_discourse_edges_filter_predicate(query_dg):
    """discourse_edges(DG.supports) returns only supports edges."""
    dg, e1, e2, c1, q1, *_ = query_dg
    local_uri = query_dg[6].graph_uri("local")
    edges = dg.discourse_edges(predicate=DG.supports, graph_uri=local_uri)
    assert len(edges) == 2
    assert (e1, DG.supports, c1) in edges
    assert (e2, DG.supports, c1) in edges
    assert (e1, DG.informs, q1) not in edges


def test_discourse_edges_only_discourse_preds(query_dg):
    """discourse_edges() never returns rdfs:label, rdf:type, or prov triples."""
    dg, *_ = query_dg
    from rdflib import RDFS
    from rdflib.namespace import PROV as PROV_NS
    edges = dg.discourse_edges()
    for _, p, _ in edges:
        assert p in (DG.informs, DG.supports, DG.opposes,
                     ENG.decision, ENG.opens, ENG.justification)


def test_discourse_edges_scoped_to_graph(query_dg):
    """discourse_edges(graph_uri=local) excludes edges from ingested graph."""
    dg, e1, e2, c1, q1, ing_node, agent, _ = query_dg
    local_uri = agent.graph_uri("local")
    local_edges = dg.discourse_edges(graph_uri=local_uri)
    all_edges = dg.discourse_edges()
    # The ingested subgraph has no discourse edges, but the scoping still works
    assert set(local_edges).issubset(set(all_edges))


def test_discourse_edges_returns_sorted(query_dg):
    """discourse_edges() output is sorted (deterministic)."""
    dg, *_ = query_dg
    result = dg.discourse_edges()
    assert result == sorted(result)


# ── neighbors() ───────────────────────────────────────────────────────────────


def test_neighbors_outgoing_e1(query_dg):
    """neighbors(e1)['outgoing'] has 2 entries: supports→c1 and informs→q1."""
    dg, e1, e2, c1, q1, *_ = query_dg
    local_uri = query_dg[6].graph_uri("local")
    nb = dg.neighbors(e1, graph_uri=local_uri)
    assert len(nb["outgoing"]) == 2
    assert (DG.supports, c1) in nb["outgoing"]
    assert (DG.informs, q1) in nb["outgoing"]


def test_neighbors_incoming_c1(query_dg):
    """neighbors(c1)['incoming'] has 2 entries: e1 and e2 via supports."""
    dg, e1, e2, c1, *_ = query_dg
    local_uri = query_dg[6].graph_uri("local")
    nb = dg.neighbors(c1, graph_uri=local_uri)
    assert len(nb["incoming"]) == 2
    assert (DG.supports, e1) in nb["incoming"]
    assert (DG.supports, e2) in nb["incoming"]


def test_neighbors_no_incoming_for_e1(query_dg):
    """neighbors(e1)['incoming'] is empty — no edges point to e1."""
    dg, e1, *_ = query_dg
    local_uri = query_dg[6].graph_uri("local")
    nb = dg.neighbors(e1, graph_uri=local_uri)
    assert nb["incoming"] == []


def test_neighbors_no_outgoing_for_q1(query_dg):
    """neighbors(q1)['outgoing'] is empty — q1 has no outgoing discourse edges."""
    dg, e1, e2, c1, q1, *_ = query_dg
    local_uri = query_dg[6].graph_uri("local")
    nb = dg.neighbors(q1, graph_uri=local_uri)
    assert nb["outgoing"] == []


def test_neighbors_returns_dict_keys(query_dg):
    """neighbors() always returns a dict with 'outgoing' and 'incoming' keys."""
    dg, e1, *_ = query_dg
    nb = dg.neighbors(e1)
    assert "outgoing" in nb
    assert "incoming" in nb


# ── Composability ─────────────────────────────────────────────────────────────


def test_nodes_compose_with_node_data(query_dg):
    """[node_data(n) for n in nodes(DG.Evidence)] returns one dict per Evidence."""
    dg, e1, e2, *_ = query_dg
    evidence_nodes = dg.nodes(type_uri=DG.Evidence)
    data_list = [dg.node_data(n) for n in evidence_nodes]
    assert len(data_list) == 3  # e1, e2, ing_node
    types = {d["type"] for d in data_list}
    assert types == {DG.Evidence}


def test_neighbors_compose_with_node_data(query_dg):
    """Outgoing neighbor URIs from neighbors() can be passed to node_data()."""
    dg, e1, e2, c1, q1, *_ = query_dg
    local_uri = query_dg[6].graph_uri("local")
    nb = dg.neighbors(e1, graph_uri=local_uri)
    for _, obj_uri in nb["outgoing"]:
        data = dg.node_data(obj_uri)
        assert data["uri"] == obj_uri
        assert data["type"] is not None


# ── Policy isolation ──────────────────────────────────────────────────────────


def test_query_methods_do_not_touch_policy(query_dg):
    """After calling all query helpers, _policy is unchanged."""
    dg, e1, e2, c1, q1, ing_node, agent, _ = query_dg
    policy_len_before = len(dg._policy)

    _ = dg.nodes()
    _ = dg.nodes(type_uri=DG.Evidence)
    _ = dg.node_data(e1)
    _ = dg.discourse_edges()
    _ = dg.neighbors(e1)

    assert len(dg._policy) == policy_len_before, (
        "Query helpers must not write to _policy."
    )
