"""Standalone invariant tests — INV-P1 through INV-P5.

These tests are domain-agnostic.  They use minimal synthetic fixtures
and do not reference Alice/Bob scenario content.  Each test is machine-
readable documentation of a non-negotiable system property.

INV-P1: No excluded node URI appears as subject or object of any
        discourse edge in the exported graph.
INV-P2: Every discourse edge (s,p,o) in the export satisfies
        s ∈ permitted ∧ o ∈ permitted.
INV-P3: _policy is not _store (object identity).
INV-P4: _policy never passed to any ConjunctiveGraph method
        (enforced by the linter comment # INV-P3: _policy never enters _store
        at every _store write site in graph.py).
INV-P5: verify() never includes _policy in its validation target.
"""
from __future__ import annotations

import importlib.util
import pathlib

import pytest
from rdflib import RDF, RDFS, XSD, Graph, Literal, URIRef
from rdflib.namespace import PROV

from discourse_graph.agent import Agent
from discourse_graph.graph import DiscourseGraph
from discourse_graph.namespaces import DG
from discourse_graph.namespaces import load_combined_ontology
from discourse_graph.policy import DISCOURSE_PREDICATES
from discourse_graph.shapes import load_shapes


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def ontology() -> Graph:
    return load_combined_ontology()


@pytest.fixture
def shapes() -> Graph:
    return load_shapes()


@pytest.fixture
def test_agent() -> Agent:
    return Agent("TestAgent", "http://test.org/ta/")


@pytest.fixture
def grantee_agent() -> Agent:
    return Agent("GranteeAgent", "http://test.org/ga/")


@pytest.fixture
def minimal_dg(test_agent: Agent, ontology: Graph, shapes: Graph):
    """DiscourseGraph with one Evidence, one Claim, one Question, and one edge.

    Returns (dg, e_uri, c_uri, q_uri, local_uri).
    """
    dg = DiscourseGraph(test_agent, ontology, shapes, verify_on_write=False)
    e_uri = dg.add_node(DG.Evidence, "Synthetic evidence body", "SynE")
    c_uri = dg.add_node(DG.Claim, "Synthetic claim body", "SynC")
    q_uri = dg.add_node(DG.Question, "Synthetic question?", "SynQ")
    dg.add_edge(e_uri, DG.supports, c_uri)
    local_uri = test_agent.graph_uri("local")
    return dg, e_uri, c_uri, q_uri, local_uri


# ── INV-P1: excluded node absent as subject of discourse edge ────────────────


def test_inv_p1_excluded_node_absent_subject(
    minimal_dg, grantee_agent: Agent
) -> None:
    """INV-P1: Excluded node does not appear as ?s in any discourse triple of export."""
    dg, e_uri, c_uri, q_uri, local_uri = minimal_dg

    # Include e_uri but then exclude it too → permitted = empty
    dg.declare_sharing_policy(
        "test-excl-subj",
        grantee_agent.uri,
        local_uri,
        include_nodes=[e_uri],
        exclude_nodes=[e_uri],
    )
    exported, _ = dg.export_policy("test-excl-subj", grantee_agent.uri)

    # e_uri is excluded — must not appear as subject of any discourse edge
    for s, p, o in exported:
        if p in DISCOURSE_PREDICATES:
            assert s != e_uri, (
                f"INV-P1: excluded node {e_uri!r} appears as subject of {p!r}."
            )


# ── INV-P1: excluded node absent as object of discourse edge ─────────────────


def test_inv_p1_excluded_node_absent_object(
    minimal_dg, grantee_agent: Agent
) -> None:
    """INV-P1: Excluded node does not appear as ?o in any discourse triple of export."""
    dg, e_uri, c_uri, q_uri, local_uri = minimal_dg

    # Include evidence (permitted), exclude the claim (which is its edge target)
    dg.declare_sharing_policy(
        "test-excl-obj",
        grantee_agent.uri,
        local_uri,
        include_nodes=[e_uri],
        exclude_nodes=[c_uri],
    )
    exported, _ = dg.export_policy("test-excl-obj", grantee_agent.uri)

    # c_uri is excluded — must not appear as object of any discourse edge
    for s, p, o in exported:
        if p in DISCOURSE_PREDICATES:
            if not isinstance(o, Literal):
                assert o != c_uri, (
                    f"INV-P1: excluded node {c_uri!r} appears as object of {p!r}."
                )


# ── INV-P2: all discourse edge endpoints in permitted set ────────────────────


def test_inv_p2_all_discourse_edges_endpoint_bounded(
    minimal_dg, grantee_agent: Agent
) -> None:
    """INV-P2: For every discourse edge in export: s ∈ permitted ∧ o ∈ permitted.

    Policy includes only e_uri; the dg:supports edge (e_uri → c_uri)
    must be absent because c_uri is not in permitted.
    """
    dg, e_uri, c_uri, q_uri, local_uri = minimal_dg

    policy_uri = dg.declare_sharing_policy(
        "test-bounded",
        grantee_agent.uri,
        local_uri,
        include_nodes=[e_uri],   # c_uri NOT included
    )
    _, permitted = dg._compile_policy(policy_uri)
    exported, _ = dg.export_policy("test-bounded", grantee_agent.uri)

    # Verify INV-P2 manually (in addition to the assert in export_policy)
    for s, p, o in exported:
        if p in DISCOURSE_PREDICATES:
            assert s in permitted, f"INV-P2: subject {s!r} not in permitted"
            if not isinstance(o, Literal):
                assert o in permitted, f"INV-P2: object {o!r} not in permitted"

    # Specifically: the E→C discourse edge must be absent
    assert (e_uri, DG.supports, c_uri) not in exported


# ── INV-P3: _policy is not _store (object identity) ─────────────────────────


def test_inv_p3_policy_object_identity(
    minimal_dg,
) -> None:
    """INV-P3: dg._policy is not dg._store immediately after construction."""
    dg, *_ = minimal_dg
    assert dg._policy is not dg._store


def test_inv_p3_policy_not_a_context_in_store(
    minimal_dg,
) -> None:
    """INV-P3: dg._policy is not returned by dg._store.contexts() at any point."""
    dg, e_uri, c_uri, q_uri, local_uri = minimal_dg

    # Check by object identity (not equality) across all contexts
    assert not any(ctx is dg._policy for ctx in dg._store.contexts()), (
        "INV-P3: _policy found as a context in _store."
    )

    # Declare a policy and check again
    dg.declare_sharing_policy(
        "test-iso",
        URIRef("http://test.org/ga/agent"),
        local_uri,
        include_nodes=[e_uri],
    )
    assert not any(ctx is dg._policy for ctx in dg._store.contexts()), (
        "INV-P3: _policy found as a context in _store after declare_sharing_policy."
    )


# ── INV-P4: linter comment present in graph.py source ───────────────────────


def test_inv_p4_linter_comment_present() -> None:
    """INV-P4: graph.py source contains the required linter comment at _store write sites.

    This is a structural guard — not a runtime test.  It reads the source
    file and asserts the comment string is present.
    """
    spec = importlib.util.find_spec("discourse_graph.graph")
    assert spec is not None, "Cannot locate discourse_graph.graph module."

    source_path = pathlib.Path(spec.origin)
    source_text = source_path.read_text(encoding="utf-8")

    required_comment = "# INV-P3: _policy never enters _store"
    assert required_comment in source_text, (
        f"Required linter comment {required_comment!r} not found in graph.py. "
        "Every _store write site must carry this comment."
    )


# ── INV-P5: verify() excludes _policy triples from validation ────────────────


def test_inv_p5_verify_excludes_policy_triples(
    minimal_dg,
) -> None:
    """INV-P5: Triples injected directly into _policy are invisible to pyshacl.

    An orphan dg:Evidence node (no discourse edges) in _policy would fail
    SHACL shape ES-2 if seen.  If _flat_graph() correctly excludes _policy,
    verify() returns conforms=True for the otherwise-valid store.
    """
    dg, e_uri, c_uri, q_uri, local_uri = minimal_dg

    # Inject an orphan Evidence node directly into _policy (bypassing all APIs)
    orphan_uri = URIRef("http://test.org/ta/policy-orphan")
    dg._policy.add((orphan_uri, RDF.type, DG.Evidence))
    dg._policy.add((orphan_uri, RDF.type, DG.DiscourseNode))
    dg._policy.add((orphan_uri, RDF.type, PROV.Entity))
    dg._policy.add((orphan_uri, DG.content, Literal("orphan", datatype=XSD.string)))
    dg._policy.add((orphan_uri, RDFS.label, Literal("orphan", datatype=XSD.string)))

    # The _store already has a valid E→C edge from the minimal_dg fixture
    report = dg.verify()

    # If _policy is invisible to pyshacl, the orphan Evidence triggers no ES-2
    assert "ES-2" not in report.violation_ids(), (
        "INV-P5: _policy orphan Evidence triggered ES-2 — _policy leaked into verify()."
    )
