"""Tests for discourse_graph.io — file-based import/export utilities.

Covers:
  save_store / load_store     — store round-trip (TriG, N-Quads, Turtle)
  save_policy / load_policy   — policy round-trip (Turtle)
  save_policy_sparql          — SPARQL export (inspection artifact)
  export_policy(override=...) — grantee-check bypass for policy author
  _detect_format              — auto-detection from file extension
"""
from __future__ import annotations

import pytest
from rdflib import URIRef

from discourse_graph.agent import Agent
from discourse_graph.graph import DiscourseGraph
from discourse_graph.io import (
    _detect_format,
    load_policy,
    load_store,
    save_policy,
    save_policy_sparql,
    save_store,
)
from discourse_graph.namespaces import DG, load_combined_ontology
from discourse_graph.shapes import load_shapes


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def ontology():
    return load_combined_ontology()


@pytest.fixture(scope="module")
def shapes():
    return load_shapes()


@pytest.fixture
def io_agent():
    return Agent("IOAgent", "http://test.org/io/")


@pytest.fixture
def bob_agent():
    return Agent("BobIO", "http://test.org/bob-io/")


@pytest.fixture
def io_dg(io_agent, bob_agent, ontology, shapes):
    """DiscourseGraph with 3 nodes, 2 edges, and one sharing policy."""
    dg = DiscourseGraph(io_agent, ontology, shapes, verify_on_write=False)
    local_uri = io_agent.graph_uri("local")

    e1 = dg.add_node(DG.Evidence, "E1 evidence body", "E1", graph_uri=local_uri)
    c1 = dg.add_node(DG.Claim, "C1 claim body", "C1", graph_uri=local_uri)
    q1 = dg.add_node(DG.Question, "Q1 question?", "Q1", graph_uri=local_uri)

    dg.add_edge(e1, DG.supports, c1, graph_uri=local_uri)
    dg.add_edge(e1, DG.informs, q1, graph_uri=local_uri)

    dg.declare_sharing_policy(
        "share-evidence",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
    )

    return dg, e1, c1, q1, io_agent, bob_agent


# ── Store round-trip ──────────────────────────────────────────────────────────


def test_save_load_store_triple_count(io_dg, tmp_path, ontology, shapes):
    """Triple count is preserved after save → load into fresh DG."""
    dg, e1, c1, q1, io_agent, _ = io_dg
    path = tmp_path / "store.trig"

    save_store(dg, path)

    fresh = DiscourseGraph(io_agent, ontology, shapes, verify_on_write=False)
    load_store(fresh, path)

    assert fresh.triple_count() == dg.triple_count()


def test_save_load_store_named_graphs(io_dg, tmp_path, ontology, shapes):
    """Named graph URIs are identical after TriG round-trip."""
    dg, e1, c1, q1, io_agent, _ = io_dg
    path = tmp_path / "store.trig"

    save_store(dg, path)

    fresh = DiscourseGraph(io_agent, ontology, shapes, verify_on_write=False)
    load_store(fresh, path)

    assert set(fresh.named_graphs()) == set(dg.named_graphs())


def test_save_load_store_node_data(io_dg, tmp_path, ontology, shapes):
    """node_data() fields (content, label, type) are intact after round-trip."""
    dg, e1, c1, q1, io_agent, _ = io_dg
    path = tmp_path / "store.trig"

    save_store(dg, path)

    fresh = DiscourseGraph(io_agent, ontology, shapes, verify_on_write=False)
    load_store(fresh, path)

    original = dg.node_data(e1)
    restored = fresh.node_data(e1)

    assert restored["content"] == original["content"]
    assert restored["label"] == original["label"]
    assert restored["type"] == original["type"]


def test_save_load_store_discourse_edges(io_dg, tmp_path, ontology, shapes):
    """discourse_edges() returns the same edges after round-trip."""
    dg, e1, c1, q1, io_agent, _ = io_dg
    path = tmp_path / "store.trig"

    save_store(dg, path)

    fresh = DiscourseGraph(io_agent, ontology, shapes, verify_on_write=False)
    load_store(fresh, path)

    assert set(fresh.discourse_edges()) == set(dg.discourse_edges())


def test_save_load_store_nquads_format(io_dg, tmp_path, ontology, shapes):
    """N-Quads format also preserves named graph structure."""
    dg, e1, c1, q1, io_agent, _ = io_dg
    path = tmp_path / "store.nq"

    save_store(dg, path, format="nquads")

    fresh = DiscourseGraph(io_agent, ontology, shapes, verify_on_write=False)
    load_store(fresh, path)

    assert set(fresh.named_graphs()) == set(dg.named_graphs())
    assert fresh.triple_count() == dg.triple_count()


def test_save_load_store_turtle_format(io_dg, tmp_path, ontology, shapes):
    """Turtle format: all triples present (named-graph context merged into default)."""
    dg, e1, c1, q1, io_agent, _ = io_dg
    path = tmp_path / "store.ttl"

    save_store(dg, path, format="turtle")

    fresh = DiscourseGraph(io_agent, ontology, shapes, verify_on_write=False)
    load_store(fresh, path, format="turtle")

    # Turtle loses named-graph context but all triples are present somewhere
    assert fresh.triple_count() >= dg.triple_count()


def test_full_store_export_import_loop(io_dg, tmp_path, ontology, shapes):
    """Full loop: build → save_store → new DG → load_store → nodes() same URIs."""
    dg, e1, c1, q1, io_agent, _ = io_dg
    path = tmp_path / "full_loop.trig"

    save_store(dg, path)

    fresh = DiscourseGraph(io_agent, ontology, shapes, verify_on_write=False)
    load_store(fresh, path)

    assert set(fresh.nodes()) == set(dg.nodes())


# ── Policy round-trip ─────────────────────────────────────────────────────────


def test_save_load_policy_triple_count(io_dg, tmp_path, ontology, shapes):
    """Policy triple count is preserved after save_policy → load_policy."""
    dg, e1, c1, q1, io_agent, _ = io_dg
    path = tmp_path / "policy.ttl"

    save_policy(dg, path)

    fresh = DiscourseGraph(io_agent, ontology, shapes, verify_on_write=False)
    load_policy(fresh, path)

    assert len(fresh._policy) == len(dg._policy)


def test_load_policy_enables_export_policy(io_dg, tmp_path, ontology, shapes):
    """After load_policy into a fresh DG, export_policy() succeeds."""
    dg, e1, c1, q1, io_agent, bob_agent = io_dg
    policy_path = tmp_path / "policy.ttl"
    store_path = tmp_path / "store.trig"

    save_policy(dg, policy_path)
    save_store(dg, store_path)

    fresh = DiscourseGraph(io_agent, ontology, shapes, verify_on_write=False)
    load_store(fresh, store_path)
    load_policy(fresh, policy_path)

    exported, sparql = fresh.export_policy("share-evidence", bob_agent.uri)
    assert len(exported) > 0


def test_load_policy_exported_graph_correct(io_dg, tmp_path, ontology, shapes):
    """Exported graph from loaded policy contains only Evidence nodes."""
    dg, e1, c1, q1, io_agent, bob_agent = io_dg
    policy_path = tmp_path / "policy.ttl"
    store_path = tmp_path / "store.trig"

    save_policy(dg, policy_path)
    save_store(dg, store_path)

    fresh = DiscourseGraph(io_agent, ontology, shapes, verify_on_write=False)
    load_store(fresh, store_path)
    load_policy(fresh, policy_path)

    exported, _ = fresh.export_policy("share-evidence", bob_agent.uri)

    from rdflib import RDF
    exported_types = {o for s, p, o in exported if p == RDF.type and o in (DG.Evidence, DG.Claim, DG.Question)}
    assert DG.Claim not in exported_types
    assert DG.Question not in exported_types


def test_full_policy_export_import_loop(io_dg, tmp_path, ontology, shapes):
    """Full loop: declare → save_policy → new DG → load_policy → export_policy works."""
    dg, e1, c1, q1, io_agent, bob_agent = io_dg
    policy_path = tmp_path / "full_policy_loop.ttl"
    store_path = tmp_path / "full_policy_loop.trig"

    save_policy(dg, policy_path)
    save_store(dg, store_path)

    fresh = DiscourseGraph(io_agent, ontology, shapes, verify_on_write=False)
    load_store(fresh, store_path)
    load_policy(fresh, policy_path)

    exported, sparql = fresh.export_policy("share-evidence", bob_agent.uri)
    assert "CONSTRUCT" in sparql
    assert len(exported) > 0


# ── SPARQL export ──────────────────────────────────────────────────────────────


def test_save_policy_sparql_creates_file(io_dg, tmp_path):
    """save_policy_sparql creates the output file."""
    dg, e1, c1, q1, io_agent, bob_agent = io_dg
    path = tmp_path / "policy.sparql"

    save_policy_sparql(dg, "share-evidence", bob_agent.uri, path)

    assert path.exists()


def test_save_policy_sparql_contains_construct(io_dg, tmp_path):
    """Saved SPARQL file contains the CONSTRUCT keyword."""
    dg, e1, c1, q1, io_agent, bob_agent = io_dg
    path = tmp_path / "policy.sparql"

    save_policy_sparql(dg, "share-evidence", bob_agent.uri, path)

    assert "CONSTRUCT" in path.read_text(encoding="utf-8")


def test_save_policy_sparql_contains_values(io_dg, tmp_path):
    """Saved SPARQL file contains the VALUES clause."""
    dg, e1, c1, q1, io_agent, bob_agent = io_dg
    path = tmp_path / "policy.sparql"

    save_policy_sparql(dg, "share-evidence", bob_agent.uri, path)

    assert "VALUES" in path.read_text(encoding="utf-8")


def test_save_policy_sparql_is_valid_utf8(io_dg, tmp_path):
    """Saved SPARQL file is valid UTF-8 text."""
    dg, e1, c1, q1, io_agent, bob_agent = io_dg
    path = tmp_path / "policy.sparql"

    save_policy_sparql(dg, "share-evidence", bob_agent.uri, path)

    content = path.read_text(encoding="utf-8")
    assert isinstance(content, str)
    assert len(content) > 0


def test_save_policy_sparql_grantee_mismatch_raises(io_dg, tmp_path):
    """Wrong grantee_uri raises ValueError when override=False (default)."""
    dg, e1, c1, q1, io_agent, _ = io_dg
    path = tmp_path / "policy.sparql"
    wrong_grantee = URIRef("http://test.org/nobody/agent")

    with pytest.raises(ValueError, match="Grantee mismatch"):
        save_policy_sparql(dg, "share-evidence", wrong_grantee, path)


def test_save_policy_sparql_override_bypasses_grantee_check(io_dg, tmp_path):
    """override=True lets the policy author export with a non-matching grantee_uri."""
    dg, e1, c1, q1, io_agent, bob_agent = io_dg
    path_normal = tmp_path / "normal.sparql"
    path_override = tmp_path / "override.sparql"
    wrong_grantee = URIRef("http://test.org/nobody/agent")

    save_policy_sparql(dg, "share-evidence", bob_agent.uri, path_normal)
    save_policy_sparql(dg, "share-evidence", wrong_grantee, path_override, override=True)

    # Both files contain the same SPARQL (override only skips the identity check)
    assert path_override.read_text(encoding="utf-8") == path_normal.read_text(encoding="utf-8")


# ── export_policy override flag ────────────────────────────────────────────────


def test_export_policy_override_bypasses_grantee_check(io_dg):
    """export_policy(override=True) succeeds even when grantee_uri doesn't match."""
    dg, e1, c1, q1, io_agent, _ = io_dg
    wrong_grantee = URIRef("http://test.org/nobody/agent")

    exported, sparql = dg.export_policy("share-evidence", wrong_grantee, override=True)

    assert "CONSTRUCT" in sparql


def test_export_policy_invariants_still_fire_with_override(io_dg, monkeypatch):
    """INV-P1/P2/P3 asserts are unaffected by override=True."""
    dg, e1, c1, q1, io_agent, _ = io_dg
    wrong_grantee = URIRef("http://test.org/nobody/agent")

    # Monkeypatch _compile_policy to return a graph that violates INV-P2
    from rdflib import Graph, Literal
    from discourse_graph.namespaces import DG
    local_uri = io_agent.graph_uri("local")

    # e1 is in permitted but c1 is NOT — unfiltered SPARQL will return (e1, supports, c1)
    # triggering INV-P2 for c1.  permitted must be non-empty to pass the early-return guard.
    permitted_set = frozenset({e1})

    def bad_compile(policy_uri):
        # Return a SPARQL that includes c1 (not in permitted)
        sparql = f"CONSTRUCT {{ ?s ?p ?o }} WHERE {{ GRAPH <{local_uri}> {{ ?s ?p ?o }} }}"
        return sparql, permitted_set

    monkeypatch.setattr(dg, "_compile_policy", bad_compile)

    with pytest.raises(AssertionError, match="INV-P[123]"):
        dg.export_policy("share-evidence", wrong_grantee, override=True)


# ── Format auto-detection ──────────────────────────────────────────────────────


def test_format_autodetect_trig(io_dg, tmp_path, ontology, shapes):
    """.trig extension is auto-detected as TriG format."""
    dg, e1, c1, q1, io_agent, _ = io_dg
    path = tmp_path / "autodetect.trig"

    save_store(dg, path)

    # Reload without explicit format — relies on extension detection
    fresh = DiscourseGraph(io_agent, ontology, shapes, verify_on_write=False)
    load_store(fresh, path)  # format=None → auto-detect

    assert fresh.triple_count() == dg.triple_count()


def test_format_autodetect_turtle(io_dg, tmp_path, ontology, shapes):
    """.ttl extension is auto-detected as Turtle format."""
    dg, e1, c1, q1, io_agent, _ = io_dg
    path = tmp_path / "autodetect.ttl"

    save_policy(dg, path)

    fresh = DiscourseGraph(io_agent, ontology, shapes, verify_on_write=False)
    load_policy(fresh, path)  # format=None → auto-detect

    assert len(fresh._policy) == len(dg._policy)


def test_format_unknown_extension_raises(io_dg, tmp_path):
    """.xyz extension raises ValueError from _detect_format."""
    dg, *_ = io_dg
    path = tmp_path / "unknown.xyz"

    with pytest.raises(ValueError, match="Cannot auto-detect"):
        load_store(dg, path)


def test_detect_format_explicit_overrides_extension(tmp_path):
    """Explicit format= parameter overrides auto-detection."""
    from pathlib import Path
    path = Path(tmp_path / "file.xyz")
    # Should not raise because format is given explicitly
    result = _detect_format(path, "turtle")
    assert result == "turtle"
