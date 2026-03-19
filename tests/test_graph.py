"""Tests for DiscourseGraph — FR-DG-1 through FR-DG-13.

Change 2026-03-19: Added two FR-DG-5 test rows pinning that
_check_add_edge() validates only DISCOURSE_PREDICATES; non-discourse
predicates are unconditionally accepted.
"""
from __future__ import annotations

import pytest
from rdflib import RDF, RDFS, XSD, ConjunctiveGraph, Graph, Literal, URIRef
from rdflib.namespace import PROV

from discourse_graph.agent import Agent
from discourse_graph.graph import DiscourseGraph
from discourse_graph.models import Question
from discourse_graph.namespaces import DG, ENG
from discourse_graph.namespaces import load_combined_ontology
from discourse_graph.ontology_dg import load_dg_ontology
from discourse_graph.report import VerificationReport
from discourse_graph.shapes import load_shapes


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def alice_agent() -> Agent:
    return Agent("AliceGroup", "http://example.org/alice/")


@pytest.fixture
def ontology() -> Graph:
    return load_combined_ontology()


@pytest.fixture
def shapes() -> Graph:
    return load_shapes()


@pytest.fixture
def dg(alice_agent: Agent, ontology: Graph, shapes: Graph) -> DiscourseGraph:
    """Default DiscourseGraph with verify_on_write=False."""
    return DiscourseGraph(alice_agent, ontology, shapes, verify_on_write=False)


@pytest.fixture
def dg_strict(alice_agent: Agent, ontology: Graph, shapes: Graph) -> DiscourseGraph:
    """DiscourseGraph with verify_on_write=True."""
    return DiscourseGraph(alice_agent, ontology, shapes, verify_on_write=True)


@pytest.fixture
def populated_dg(dg: DiscourseGraph, alice_agent: Agent):
    """DiscourseGraph with three nodes and one edge."""
    e_uri = dg.add_node(DG.Evidence, "Delta-V budget analysis", "E1")
    c_uri = dg.add_node(DG.Claim, "Bipropellant is baseline", "C1")
    q_uri = dg.add_node(DG.Question, "What propulsion?", "Q1")
    dg.add_edge(e_uri, DG.supports, c_uri)
    return dg, e_uri, c_uri, q_uri


# ── FR-DG-1: _store is ConjunctiveGraph ───────────────────────────────────────


def test_fr_dg_1_store_is_conjunctive_graph(dg: DiscourseGraph) -> None:
    """FR-DG-1: _store is rdflib.ConjunctiveGraph."""
    assert type(dg._store).__name__ == "ConjunctiveGraph"
    assert isinstance(dg._store, ConjunctiveGraph)


# ── FR-DG-2: _policy is isolated Graph, not in _store ─────────────────────────


def test_fr_dg_2_policy_not_in_store(dg: DiscourseGraph) -> None:
    """FR-DG-2: _policy is a separate Graph instance never in _store."""
    # Object identity
    assert dg._policy is not dg._store
    # _policy is not reachable as a named-graph context in _store
    assert not any(ctx is dg._policy for ctx in dg._store.contexts())


# ── FR-DG-3: verify_on_write flag accepted ────────────────────────────────────


def test_fr_dg_3_verify_on_write_flag(
    alice_agent: Agent, ontology: Graph, shapes: Graph
) -> None:
    """FR-DG-3: Constructor accepts verify_on_write=True and False."""
    dg_f = DiscourseGraph(alice_agent, ontology, shapes, verify_on_write=False)
    dg_t = DiscourseGraph(alice_agent, ontology, shapes, verify_on_write=True)
    assert dg_f._verify_on_write is False
    assert dg_t._verify_on_write is True


# ── FR-DG-4: verify_on_write raises for invalid node ─────────────────────────


def test_fr_dg_4_add_node_invalid_type_raises(dg_strict: DiscourseGraph) -> None:
    """FR-DG-4: verify_on_write=True: unknown node type raises ValueError."""
    with pytest.raises(ValueError, match="Unknown node type"):
        dg_strict.add_node(URIRef("http://bad/type"), "content", "label")


def test_fr_dg_4_add_node_empty_content_raises(dg_strict: DiscourseGraph) -> None:
    """FR-DG-4: verify_on_write=True: empty content raises ValueError."""
    with pytest.raises(ValueError, match="content must be non-empty"):
        dg_strict.add_node(DG.Question, "", "label")


# ── FR-DG-5: verify_on_write validates only discourse predicates ──────────────


def test_fr_dg_5_add_edge_invalid_predicate_raises(
    dg_strict: DiscourseGraph,
) -> None:
    """FR-DG-5: verify_on_write=True: bad subject type for discourse pred raises."""
    # Need nodes in store first so type checking can fire
    q_uri = dg_strict.add_node(DG.Question, "Q?", "Q1")
    c_uri = dg_strict.add_node(DG.Claim, "C.", "C1")
    # dg:informs requires Evidence domain; Question is wrong domain
    with pytest.raises(ValueError):
        dg_strict.add_edge(q_uri, DG.informs, q_uri)


def test_fr_dg_5_add_edge_domain_violation_raises(
    dg_strict: DiscourseGraph,
) -> None:
    """FR-DG-5: verify_on_write=True: wrong domain type raises ValueError."""
    q_uri = dg_strict.add_node(DG.Question, "Q?", "Q1")
    c_uri = dg_strict.add_node(DG.Claim, "C.", "C1")
    # dg:supports domain is Evidence; Claim is wrong domain
    with pytest.raises(ValueError):
        dg_strict.add_edge(c_uri, DG.supports, c_uri)


def test_fr_dg_5_non_discourse_predicate_accepted(
    dg_strict: DiscourseGraph,
) -> None:
    """FR-DG-5: verify_on_write=True: non-discourse predicates never raise."""
    e_uri = dg_strict.add_node(DG.Evidence, "analysis", "E1")
    c_uri = dg_strict.add_node(DG.Claim, "claim", "C1")
    # prov:wasDerivedFrom is not a discourse predicate — must not raise
    dg_strict.add_edge(e_uri, PROV.wasDerivedFrom, c_uri)
    # rdfs:seeAlso is not a discourse predicate — must not raise
    dg_strict.add_edge(e_uri, RDFS.seeAlso, c_uri)


def test_fr_dg_5_discourse_predicate_domain_violation_raises(
    dg_strict: DiscourseGraph,
) -> None:
    """FR-DG-5: verify_on_write=True: dg:supports with wrong range raises."""
    e_uri = dg_strict.add_node(DG.Evidence, "analysis", "E1")
    q_uri = dg_strict.add_node(DG.Question, "Q?", "Q1")
    # dg:supports range is Claim; Question is wrong range
    with pytest.raises(ValueError):
        dg_strict.add_edge(e_uri, DG.supports, q_uri)


# ── FR-DG-6: verify_on_write=False writes unconditionally ─────────────────────


def test_fr_dg_6_unconditional_write(dg: DiscourseGraph) -> None:
    """FR-DG-6: verify_on_write=False: malformed node writes without raising."""
    # Bad type — no exception with verify_on_write=False
    uri = dg.add_node(URIRef("http://bad/type"), "x", "y")
    assert isinstance(uri, URIRef)


# ── FR-DG-7: relational SHACL deferred to verify() ───────────────────────────


def test_fr_dg_7_relational_shacl_deferred(dg: DiscourseGraph) -> None:
    """FR-DG-7: Isolated Evidence node doesn't raise at add_node; verify() reports ES-2.

    Note: ES-2 uses sh:or (OrConstraintComponent), so pyshacl nests the message
    inside the outer constraint violation text rather than attaching it as a direct
    sh:resultMessage.  Therefore the check uses report_text (which contains all
    nested text) rather than violation_ids() (which only sees top-level sh:resultMessage).
    """
    # Add Evidence without any discourse edge — structural check passes
    e_uri = dg.add_node(DG.Evidence, "orphan evidence", "E-orphan")
    # add_node did not raise; now verify() should catch the ES-2 violation
    report = dg.verify()
    assert report.conforms is False
    # ES-2 message is in the report text (nested in OrConstraintComponent)
    assert "ES-2" in report.report_text


def test_fr_dg_7_violation_ids_works_for_simple_violations(
    dg: DiscourseGraph, alice_agent: Agent
) -> None:
    """FR-DG-7 (coverage): violation_ids() correctly extracts IDs from simple sh:property violations.

    QS-1 uses sh:property (PropertyConstraintComponent), not sh:or — its
    sh:resultMessage is a direct top-level triple, so violation_ids() must return it.
    This confirms the ES-2 / report_text check above is specific to OrConstraint
    nesting, not a general relaxation of violation_ids() coverage.
    """
    # Inject a Question node without dg:content directly into the store,
    # bypassing add_node so the content triple is absent.
    q_uri = URIRef("http://example.org/alice/node/q-no-content")
    ctx = dg._store.get_context(alice_agent.graph_uri("local"))
    ctx.add((q_uri, RDF.type, DG.Question))
    ctx.add((q_uri, RDF.type, DG.DiscourseNode))
    ctx.add((q_uri, RDF.type, PROV.Entity))
    ctx.add((q_uri, RDFS.label, Literal("Q-no-content", datatype=XSD.string)))
    # dg:content deliberately absent → QS-1 violation

    report = dg.verify()
    assert report.conforms is False
    # QS-1 uses sh:property → direct sh:resultMessage → must appear in violation_ids()
    assert "QS-1" in report.violation_ids()


# ── FR-DG-8: add_node and add() write required triples ───────────────────────


def test_fr_dg_8_add_node_writes_required_triples(
    dg: DiscourseGraph, alice_agent: Agent
) -> None:
    """FR-DG-8: add_node writes exactly the 6 required triples."""
    uri = dg.add_node(DG.Question, "What propulsion?", "Q1")
    local = dg._store.get_context(alice_agent.graph_uri("local"))

    assert (uri, RDF.type, DG.Question) in local
    assert (uri, RDF.type, DG.DiscourseNode) in local
    assert (uri, RDF.type, PROV.Entity) in local
    # dg:content present
    content_vals = list(local.objects(uri, DG.content))
    assert len(content_vals) == 1
    assert str(content_vals[0]) == "What propulsion?"
    # rdfs:label present
    label_vals = list(local.objects(uri, RDFS.label))
    assert len(label_vals) == 1
    assert str(label_vals[0]) == "Q1"
    # dg:created present
    created_vals = list(local.objects(uri, DG.created))
    assert len(created_vals) == 1


def test_fr_dg_8_add_primary_matches_add_node(
    dg: DiscourseGraph,
) -> None:
    """FR-DG-8: add(Question(...)) produces the same triple types as add_node(DG.Question,...)."""
    uri_pydantic = dg.add(Question(content="What propulsion?", label="Q-pydantic"))
    uri_raw = dg.add_node(DG.Question, "What propulsion?", "Q-raw")

    # Both should have rdf:type dg:Question
    assert any(True for _ in dg._store.triples((uri_pydantic, RDF.type, DG.Question)))
    assert any(True for _ in dg._store.triples((uri_raw, RDF.type, DG.Question)))
    # Both should have rdf:type dg:DiscourseNode
    assert any(True for _ in dg._store.triples((uri_pydantic, RDF.type, DG.DiscourseNode)))
    assert any(True for _ in dg._store.triples((uri_raw, RDF.type, DG.DiscourseNode)))
    # Both should have dg:content
    assert list(dg._store.triples((uri_pydantic, DG.content, None)))
    assert list(dg._store.triples((uri_raw, DG.content, None)))
    # Both should have dg:created
    assert list(dg._store.triples((uri_pydantic, DG.created, None)))
    assert list(dg._store.triples((uri_raw, DG.created, None)))


# ── FR-DG-9: add_node defaults to agent.graph_uri("local") ───────────────────


def test_fr_dg_9_add_node_default_graph(
    dg: DiscourseGraph, alice_agent: Agent
) -> None:
    """FR-DG-9: Without graph_uri, node is written to agent.graph_uri('local')."""
    dg.add_node(DG.Question, "Q?", "Q1")
    local_uri = alice_agent.graph_uri("local")
    assert dg.triple_count(local_uri) > 0
    # Confirm the named graph appears in named_graphs()
    assert local_uri in dg.named_graphs()


# ── FR-DG-10: add_edge defaults to agent.graph_uri("local") ──────────────────


def test_fr_dg_10_add_edge_default_graph(
    dg: DiscourseGraph, alice_agent: Agent
) -> None:
    """FR-DG-10: Without graph_uri, edge is written to agent.graph_uri('local')."""
    e_uri = dg.add_node(DG.Evidence, "analysis", "E1")
    c_uri = dg.add_node(DG.Claim, "claim", "C1")
    dg.add_edge(e_uri, DG.supports, c_uri)
    local_uri = alice_agent.graph_uri("local")
    local = dg._store.get_context(local_uri)
    assert (e_uri, DG.supports, c_uri) in local


# ── FR-DG-11: verify() returns VerificationReport excluding _policy ───────────


def test_fr_dg_11_verify_returns_report(dg: DiscourseGraph) -> None:
    """FR-DG-11: verify() returns a VerificationReport instance."""
    # Add a valid node + edge so pyshacl has something to validate
    e_uri = dg.add_node(DG.Evidence, "analysis", "E1")
    c_uri = dg.add_node(DG.Claim, "claim", "C1")
    dg.add_edge(e_uri, DG.supports, c_uri)
    report = dg.verify()
    assert isinstance(report, VerificationReport)
    assert isinstance(report.conforms, bool)


def test_fr_dg_11_verify_excludes_policy(dg: DiscourseGraph) -> None:
    """FR-DG-11: Triples in _policy are invisible to pyshacl.validate.

    An orphan dg:Evidence node (no discourse edges) directly in _policy
    would trigger SHACL ES-2 if seen.  If verify() correctly excludes
    _policy, it returns conforms=True for an otherwise valid store.
    """
    # Add a valid Evidence + Claim + edge to the store
    e_uri = dg.add_node(DG.Evidence, "valid evidence", "E-valid")
    c_uri = dg.add_node(DG.Claim, "claim", "C1")
    dg.add_edge(e_uri, DG.supports, c_uri)

    # Inject an orphan Evidence triple directly into _policy — should be invisible
    fake_uri = URIRef("http://example.org/fake/orphan-evidence")
    dg._policy.add((fake_uri, RDF.type, DG.Evidence))
    dg._policy.add((fake_uri, RDF.type, DG.DiscourseNode))
    dg._policy.add((fake_uri, RDF.type, PROV.Entity))
    dg._policy.add((fake_uri, DG.content, Literal("orphan", datatype=XSD.string)))
    dg._policy.add((fake_uri, RDFS.label, Literal("orphan", datatype=XSD.string)))

    report = dg.verify()
    # The _policy orphan Evidence must not cause an ES-2 violation
    assert report.conforms is True


# ── FR-DG-12: named_graphs() ─────────────────────────────────────────────────


def test_fr_dg_12_named_graphs(dg: DiscourseGraph, alice_agent: Agent) -> None:
    """FR-DG-12: named_graphs() returns a list of URIRef values."""
    dg.add_node(DG.Question, "Q?", "Q1")
    graphs = dg.named_graphs()
    assert isinstance(graphs, list)
    assert all(isinstance(g, URIRef) for g in graphs)
    assert alice_agent.graph_uri("local") in graphs


# ── FR-DG-13: triple_count() ─────────────────────────────────────────────────


def test_fr_dg_13_triple_count(
    dg: DiscourseGraph, alice_agent: Agent
) -> None:
    """FR-DG-13: triple_count() works per-graph and total."""
    dg.add_node(DG.Question, "Q?", "Q1")
    dg.add_node(DG.Claim, "C.", "C1")

    local_uri = alice_agent.graph_uri("local")
    local_count = dg.triple_count(local_uri)
    total_count = dg.triple_count()

    assert local_count > 0
    assert total_count >= local_count
