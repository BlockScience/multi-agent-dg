"""Tests for discourse_graph/agent.py and discourse_graph/report.py.

Covers FR-AGENT-1 through FR-AGENT-3 and FR-PYD-7.
Test names follow test_<req_id>_<description> convention.
"""
from __future__ import annotations

import pytest
import rdflib
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import SH

from discourse_graph.agent import Agent
from discourse_graph.report import VerificationReport


# ── FR-AGENT-1: name and namespace storage ────────────────────────────────────


def test_fr_agent_1_name_and_namespace() -> None:
    """FR-AGENT-1: Agent stores name and namespace fields."""
    a = Agent(name="AliceGroup", namespace="http://example.org/alice/")
    assert a.name == "AliceGroup"
    assert a.namespace == "http://example.org/alice/"


def test_fr_agent_1_namespace_must_end_slash() -> None:
    """FR-AGENT-1: Agent raises ValueError when namespace has no trailing slash."""
    with pytest.raises(ValueError, match="must end with '/'"):
        Agent(name="Alice", namespace="http://example.org/alice")


# ── FR-AGENT-2: URI derivation ────────────────────────────────────────────────


def test_fr_agent_2_agent_uri() -> None:
    """FR-AGENT-2: agent.uri == <namespace>agent."""
    a = Agent(name="Alice", namespace="http://a/")
    assert a.uri == URIRef("http://a/agent")


def test_fr_agent_2_node_uri() -> None:
    """FR-AGENT-2: agent.node_uri(local_id) == <namespace>node/<local_id>."""
    a = Agent(name="Alice", namespace="http://a/")
    assert a.node_uri("q1") == URIRef("http://a/node/q1")


def test_fr_agent_2_graph_uri_local() -> None:
    """FR-AGENT-2: agent.graph_uri() defaults to <namespace>graph/local."""
    a = Agent(name="Alice", namespace="http://a/")
    assert a.graph_uri() == URIRef("http://a/graph/local")


def test_fr_agent_2_graph_uri_named() -> None:
    """FR-AGENT-2: agent.graph_uri(name) == <namespace>graph/<name>."""
    a = Agent(name="Alice", namespace="http://a/")
    assert a.graph_uri("ingested-bob") == URIRef("http://a/graph/ingested-bob")


def test_fr_agent_2_policy_uri() -> None:
    """FR-AGENT-2: agent.policy_uri(name) == <namespace>policy/<name>."""
    a = Agent(name="Alice", namespace="http://a/")
    assert a.policy_uri("evidence-sharing") == URIRef("http://a/policy/evidence-sharing")


# ── FR-AGENT-3: namespace isolation ──────────────────────────────────────────


def test_fr_agent_3_disjoint_namespaces() -> None:
    """FR-AGENT-3: Alice's and Bob's URIs do not intersect for any URI type."""
    alice = Agent(name="AliceGroup", namespace="http://example.org/alice/")
    bob = Agent(name="BobGroup", namespace="http://example.org/bob/")

    alice_uris = {
        alice.uri,
        alice.node_uri("x"),
        alice.graph_uri("local"),
        alice.policy_uri("p"),
    }
    bob_uris = {
        bob.uri,
        bob.node_uri("x"),
        bob.graph_uri("local"),
        bob.policy_uri("p"),
    }
    assert alice_uris.isdisjoint(bob_uris), (
        f"Alice and Bob share URIs: {alice_uris & bob_uris}"
    )


# ── FR-PYD-7: VerificationReport ─────────────────────────────────────────────


def test_report_conforms_status() -> None:
    """FR-PYD-7: VerificationReport.status == 'CONFORMS ✓' when conforms=True."""
    r = VerificationReport(conforms=True, report_text="", results_graph=Graph())
    assert r.status == "CONFORMS ✓"


def test_report_violation_status() -> None:
    """FR-PYD-7: VerificationReport.status == 'VIOLATIONS FOUND ✗' when conforms=False."""
    r = VerificationReport(conforms=False, report_text="", results_graph=Graph())
    assert r.status == "VIOLATIONS FOUND ✗"


def test_report_violation_ids_extracted() -> None:
    """FR-PYD-7: violation_ids() extracts requirement IDs from sh:resultMessage literals."""
    g = Graph()
    # Manually add sh:resultMessage triples that match the ID pattern
    result1 = URIRef("http://test/result1")
    result2 = URIRef("http://test/result2")
    g.add((result1, SH.resultMessage, Literal("CS-1: Claim must have exactly one dg:content.")))
    g.add((result2, SH.resultMessage, Literal("ES-2: Evidence must support, oppose, or inform.")))

    r = VerificationReport(conforms=False, report_text="", results_graph=g)
    ids = r.violation_ids()
    assert "CS-1" in ids
    assert "ES-2" in ids


def test_report_model_dump_json_safe() -> None:
    """FR-PYD-7: VerificationReport.model_dump() runs without error (results_graph serialised as Turtle)."""
    r = VerificationReport(conforms=True, report_text="Conforms: True", results_graph=Graph())
    dump = r.model_dump()
    assert isinstance(dump, dict)
    assert dump["conforms"] is True
    # results_graph serialised to string (Turtle), not raw Graph object
    assert isinstance(dump["results_graph"], str)
