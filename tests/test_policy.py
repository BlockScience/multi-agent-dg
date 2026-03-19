"""Tests for DiscourseGraph sharing policy — FR-POL-1 through FR-POL-12.

Also covers INV-P1, INV-P2, INV-P3, INV-P4 at the policy-scenario level.
"""
from __future__ import annotations

import pytest
from rdflib import RDF, XSD, Graph, Literal, URIRef
from rdflib import ConjunctiveGraph

from discourse_graph.agent import Agent
from discourse_graph.graph import DiscourseGraph
from discourse_graph.namespaces import DG, ENG
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
def alice_agent() -> Agent:
    return Agent("AliceGroup", "http://example.org/alice/")


@pytest.fixture
def bob_agent() -> Agent:
    return Agent("BobGroup", "http://example.org/bob/")


@pytest.fixture
def alice_dg(alice_agent: Agent, ontology: Graph, shapes: Graph) -> DiscourseGraph:
    """Alice's DiscourseGraph with E1, E2, C1, Q1 and connecting edges."""
    dg = DiscourseGraph(alice_agent, ontology, shapes, verify_on_write=False)
    return dg


@pytest.fixture
def alice_scenario(alice_dg: DiscourseGraph, alice_agent: Agent):
    """Returns (alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_graph_uri)."""
    e1_uri = alice_dg.add_node(DG.Evidence, "Delta-V budget analysis: 3.2 km/s", "E1")
    e2_uri = alice_dg.add_node(DG.Evidence, "Schedule constraint: SEP requires >90 days", "E2")
    c1_uri = alice_dg.add_node(DG.Claim, "Chemical bipropellant is baseline", "C1")
    q1_uri = alice_dg.add_node(DG.Question, "What propulsion architecture?", "Q1")
    alice_dg.add_edge(e1_uri, DG.supports, c1_uri)
    alice_dg.add_edge(e1_uri, DG.informs, q1_uri)
    alice_dg.add_edge(e2_uri, DG.supports, c1_uri)
    local_uri = alice_agent.graph_uri("local")
    return alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri


# ── FR-POL-1: declare_sharing_policy stores only in _policy ──────────────────


def test_fr_pol_1_policy_in_policy_only(
    alice_scenario, bob_agent: Agent
) -> None:
    """FR-POL-1: Policy triples in _policy; policy URI absent from all _store contexts."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    policy_uri = alice_dg.declare_sharing_policy(
        "evidence-sharing",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
        exclude_nodes=[e2_uri],
    )

    # Policy URI must appear in _policy
    assert (policy_uri, RDF.type, DG.SharingPolicy) in alice_dg._policy

    # Policy URI must NOT appear as subject in any _store context
    store_subjects = {s for ctx in alice_dg._store.contexts() for s, p, o in ctx}
    assert policy_uri not in store_subjects


# ── FR-POL-2: policy records correct triples ─────────────────────────────────


def test_fr_pol_2_policy_triples_complete(
    alice_scenario, bob_agent: Agent
) -> None:
    """FR-POL-2: Declared policy has all 5 required metadata triples."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    policy_uri = alice_dg.declare_sharing_policy(
        "evidence-sharing",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
        exclude_nodes=[e2_uri],
    )

    assert (policy_uri, RDF.type, DG.SharingPolicy) in alice_dg._policy
    assert (policy_uri, DG.policyName, Literal("evidence-sharing", datatype=XSD.string)) in alice_dg._policy
    assert (policy_uri, DG.grantee, bob_agent.uri) in alice_dg._policy
    assert (policy_uri, DG.sourceGraph, local_uri) in alice_dg._policy
    # dg:created must be present
    created_vals = list(alice_dg._policy.objects(policy_uri, DG.created))
    assert len(created_vals) == 1


# ── FR-POL-3: permitted set = (type_matches ∪ includes) \ excludes ───────────


def test_fr_pol_3_permitted_set_type_filter(
    alice_scenario, bob_agent: Agent
) -> None:
    """FR-POL-3: include_types=[DG.Evidence] includes Evidence nodes only."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    policy_uri = alice_dg.declare_sharing_policy(
        "evidence-sharing",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
        exclude_nodes=[e2_uri],
    )

    _, permitted = alice_dg._compile_policy(policy_uri)

    assert e1_uri in permitted      # Evidence, not excluded
    assert e2_uri not in permitted  # Evidence but excluded
    assert c1_uri not in permitted  # Claim — not in include_types
    assert q1_uri not in permitted  # Question — not in include_types


# ── FR-POL-4: type_matches = nodes matching include_types ────────────────────


def test_fr_pol_4_type_matches(
    alice_scenario, bob_agent: Agent
) -> None:
    """FR-POL-4: type_matches picks up both E1 and E2 before exclude."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    # Policy without excludes to verify both Evidence nodes are matched
    policy_uri = alice_dg.declare_sharing_policy(
        "evidence-all",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
    )
    _, permitted = alice_dg._compile_policy(policy_uri)
    assert e1_uri in permitted
    assert e2_uri in permitted
    assert c1_uri not in permitted


# ── FR-POL-5: include_nodes drops absent URIs silently ───────────────────────


def test_fr_pol_5_explicit_includes_filtered(
    alice_scenario, bob_agent: Agent
) -> None:
    """FR-POL-5: Absent node URI silently dropped; present node included."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    absent_uri = URIRef("http://example.org/does-not-exist")
    policy_uri = alice_dg.declare_sharing_policy(
        "incl-test",
        bob_agent.uri,
        local_uri,
        include_nodes=[absent_uri, e1_uri],
    )
    _, permitted = alice_dg._compile_policy(policy_uri)

    assert e1_uri in permitted
    assert absent_uri not in permitted


# ── FR-POL-6: exclude_nodes highest precedence ───────────────────────────────


def test_fr_pol_6_excludes_precedence(
    alice_scenario, bob_agent: Agent
) -> None:
    """FR-POL-6: include_nodes=[E2] and exclude_nodes=[E2] → E2 not in permitted."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    policy_uri = alice_dg.declare_sharing_policy(
        "excl-test",
        bob_agent.uri,
        local_uri,
        include_nodes=[e2_uri],
        exclude_nodes=[e2_uri],
    )
    _, permitted = alice_dg._compile_policy(policy_uri)

    assert e2_uri not in permitted


# ── FR-POL-7: _compile_policy returns SPARQL CONSTRUCT string ────────────────


def test_fr_pol_7_compile_returns_sparql_string(
    alice_scenario, bob_agent: Agent
) -> None:
    """FR-POL-7: _compile_policy() returns non-empty CONSTRUCT string."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    policy_uri = alice_dg.declare_sharing_policy(
        "evidence-sharing",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
        exclude_nodes=[e2_uri],
    )
    sparql, permitted = alice_dg._compile_policy(policy_uri)

    assert isinstance(sparql, str)
    assert sparql.startswith("CONSTRUCT")
    assert "WHERE" in sparql


# ── FR-POL-8: SPARQL scoped to GRAPH <source_graph_uri> ──────────────────────


def test_fr_pol_8_sparql_scoped_to_graph(
    alice_scenario, bob_agent: Agent
) -> None:
    """FR-POL-8: Generated SPARQL contains GRAPH <source_graph_uri>."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    policy_uri = alice_dg.declare_sharing_policy(
        "evidence-sharing",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
    )
    sparql, _ = alice_dg._compile_policy(policy_uri)

    assert "GRAPH" in sparql
    assert str(local_uri) in sparql


# ── FR-POL-9: edge-bounding rule ─────────────────────────────────────────────


def test_fr_pol_9_edge_bounding_evidence(
    alice_scenario, bob_agent: Agent
) -> None:
    """FR-POL-9: E1→C1 dg:supports edge absent from Policy A export (C1 not permitted)."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    # Policy A: include Evidence, exclude E2
    alice_dg.declare_sharing_policy(
        "evidence-sharing",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
        exclude_nodes=[e2_uri],
    )
    exported, _ = alice_dg.export_policy("evidence-sharing", bob_agent.uri)

    # E1 present as subject (its own triples)
    assert any(True for _ in exported.triples((e1_uri, None, None)))
    # E2 absent entirely
    assert not any(True for _ in exported.triples((e2_uri, None, None)))
    # E1→C1 dg:supports edge absent: C1 is not permitted
    assert (e1_uri, DG.supports, c1_uri) not in exported
    # E1→Q1 dg:informs edge absent: Q1 is not permitted
    assert (e1_uri, DG.informs, q1_uri) not in exported


def test_fr_pol_9_edge_bounding_claim(
    alice_scenario, bob_agent: Agent
) -> None:
    """FR-POL-9: Policy B (C1 only): no incoming discourse edges on C1."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    # Policy B: include only C1 explicitly
    alice_dg.declare_sharing_policy(
        "arch-claim",
        bob_agent.uri,
        local_uri,
        include_nodes=[c1_uri],
    )
    exported, _ = alice_dg.export_policy("arch-claim", bob_agent.uri)

    # C1 is exported with its own triples
    assert any(True for _ in exported.triples((c1_uri, None, None)))
    # No discourse edges point TO c1 from e1/e2 (they are not permitted)
    for s, p, o in exported:
        if p in DISCOURSE_PREDICATES and o == c1_uri:
            pytest.fail(f"Unexpected incoming discourse edge: ({s!r}, {p!r}, {c1_uri!r})")


# ── FR-POL-10: grantee mismatch raises ValueError ────────────────────────────


def test_fr_pol_10_grantee_mismatch_raises(
    alice_scenario, bob_agent: Agent
) -> None:
    """FR-POL-10: export_policy with wrong grantee raises ValueError."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    alice_dg.declare_sharing_policy(
        "evidence-sharing",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
    )

    wrong_uri = URIRef("http://example.org/wrong/agent")
    with pytest.raises(ValueError, match="Grantee mismatch"):
        alice_dg.export_policy("evidence-sharing", wrong_uri)


# ── FR-POL-11: post-conditions asserted ──────────────────────────────────────


def test_fr_pol_11_postconditions_asserted(
    alice_scenario, bob_agent: Agent, monkeypatch
) -> None:
    """FR-POL-11: INV-P1 assert fires when _compile_policy returns bad SPARQL.

    The asserts in export_policy() are defense-in-depth against bugs in
    _compile_policy().  We monkeypatch _compile_policy to return a SPARQL
    CONSTRUCT that ignores the exclude list, causing an excluded node to
    appear in the exported graph, which should trigger the INV-P1 assert.
    """
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    alice_dg.declare_sharing_policy(
        "evidence-sharing",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
        exclude_nodes=[e2_uri],
    )

    # Build a "bad" SPARQL that returns E2 (the excluded node) as well
    # by using include_nodes for both e1 and e2 with no exclusion filter
    bad_sparql = (
        f"CONSTRUCT {{ ?s ?p ?o }}\n"
        f"WHERE {{\n"
        f"  GRAPH <{local_uri}> {{\n"
        f"    ?s ?p ?o .\n"
        f"    VALUES ?s {{ <{e1_uri}> <{e2_uri}> }}\n"
        f"  }}\n"
        f"}}"
    )
    # The permitted set excludes e2 — but the bad SPARQL includes it
    bad_permitted = frozenset({e1_uri})

    original_compile = alice_dg._compile_policy

    def patched_compile(policy_uri):
        return bad_sparql, bad_permitted

    monkeypatch.setattr(alice_dg, "_compile_policy", patched_compile)

    # The exported graph will contain e2 triples, but e2 is in excluded_uris.
    # INV-P1 or INV-P2 will fire depending on which discourse edge is evaluated
    # first (both are triggered by the bad SPARQL output).
    with pytest.raises(AssertionError, match="INV-P[12]"):
        alice_dg.export_policy("evidence-sharing", bob_agent.uri)


def test_fr_pol_11_inv_p1_fires_on_excluded_object(
    alice_agent: Agent, bob_agent: Agent,
    ontology: Graph, shapes: Graph, monkeypatch
) -> None:
    """FR-POL-11: INV-P1 fires specifically when excluded node appears as discourse *object*.

    Uses a minimal graph with exactly ONE discourse edge: E1 → dg:supports → C1.
    No other discourse edges exist, so the only discourse triple the bad SPARQL
    can return is (E1, dg:supports, C1).

    Assert execution order for that triple:
      1. INV-P1 subject: E1 not in excluded_uris → passes
      2. INV-P1 object:  C1 IN excluded_uris     → fires "INV-P1" (before INV-P2)

    This proves INV-P1 is specifically checked and not merely shadowed by INV-P2.
    """
    dg = DiscourseGraph(alice_agent, ontology, shapes)
    e1_uri = dg.add_node(DG.Evidence, "analysis", "E1")
    c1_uri = dg.add_node(DG.Claim, "claim", "C1")
    dg.add_edge(e1_uri, DG.supports, c1_uri)
    local_uri = alice_agent.graph_uri("local")

    # Policy: include E1, explicitly exclude C1
    dg.declare_sharing_policy(
        "inv-p1-obj-test",
        bob_agent.uri,
        local_uri,
        include_nodes=[e1_uri],
        exclude_nodes=[c1_uri],
    )

    # Bad SPARQL: returns ALL of E1's triples including E1→C1.
    # C1 appears as the discourse edge object — C1 is in excluded_uris.
    # No other discourse edges exist in this minimal graph, so INV-P2 cannot
    # fire before INV-P1 (only non-permitted object is C1, which is also excluded).
    bad_sparql = (
        f"CONSTRUCT {{ ?s ?p ?o }}\n"
        f"WHERE {{\n"
        f"  GRAPH <{local_uri}> {{\n"
        f"    ?s ?p ?o .\n"
        f"    VALUES ?s {{ <{e1_uri}> }}\n"
        f"  }}\n"
        f"}}"
    )
    # permitted = {e1_uri}; c1_uri in excluded_uris but NOT in permitted
    bad_permitted = frozenset({e1_uri})

    def patched_compile(policy_uri):
        return bad_sparql, bad_permitted

    monkeypatch.setattr(dg, "_compile_policy", patched_compile)

    # Assert order in export_policy for (E1, dg:supports, C1):
    #   assert E1 not in excluded_uris  → passes (E1 not excluded)
    #   assert C1 not in excluded_uris  → FAILS "INV-P1: excluded node...as object"
    with pytest.raises(AssertionError, match="INV-P1"):
        dg.export_policy("inv-p1-obj-test", bob_agent.uri)


def test_export_policy_empty_permitted_returns_empty_graph(
    alice_scenario, bob_agent: Agent
) -> None:
    """When permitted set is empty, export_policy returns an empty graph.

    This documents the early-return behaviour added to avoid a rdflib bug
    with empty VALUES clauses.  The SPARQL string must still be generated
    (for inspection), but the graph must be empty and no post-condition
    asserts fire spuriously.
    """
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    # include_nodes=[e1_uri], exclude_nodes=[e1_uri] → permitted = empty
    alice_dg.declare_sharing_policy(
        "empty-permitted",
        bob_agent.uri,
        local_uri,
        include_nodes=[e1_uri],
        exclude_nodes=[e1_uri],
    )
    exported, sparql = alice_dg.export_policy("empty-permitted", bob_agent.uri)

    # Graph must be empty — no triples should leak through
    assert len(exported) == 0, (
        f"Expected empty exported graph but got {len(exported)} triples."
    )
    # SPARQL string is still generated (for notebook inspection / logging)
    assert "CONSTRUCT" in sparql
    assert "VALUES" in sparql


# ── FR-POL-12: pull_from calls export_policy then ingest ─────────────────────


def test_fr_pol_12_pull_from_calls_ingest(
    alice_scenario, bob_agent: Agent, ontology: Graph, shapes: Graph
) -> None:
    """FR-POL-12: bob.pull_from(alice, ...) ingests triples into Bob's store."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    alice_dg.declare_sharing_policy(
        "evidence-sharing",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
        exclude_nodes=[e2_uri],
    )

    bob_dg = DiscourseGraph(bob_agent, ontology, shapes)
    ingested_uri, sparql = bob_dg.pull_from(alice_dg, "evidence-sharing")

    assert isinstance(ingested_uri, URIRef)
    assert bob_dg.triple_count(ingested_uri) > 0
    # E1 must be present in Bob's store
    assert any(True for _ in bob_dg._store.triples((e1_uri, None, None)))
    # E2 must not be present
    assert not any(True for _ in bob_dg._store.triples((e2_uri, None, None)))


# ── INV-P3: _policy object identity ──────────────────────────────────────────


def test_policy_isolation(alice_dg: DiscourseGraph) -> None:
    """INV-P3: alice._policy is not alice._store."""
    assert alice_dg._policy is not alice_dg._store


# ── INV-P4: policy URI absent from all _store contexts ───────────────────────


def test_policy_not_in_store(
    alice_scenario, bob_agent: Agent
) -> None:
    """INV-P4: Policy URI not in any _store context subject set."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    policy_uri = alice_dg.declare_sharing_policy(
        "evidence-sharing",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
    )

    all_store_subjects = {
        s
        for ctx in alice_dg._store.contexts()
        for s, p, o in ctx
    }
    assert policy_uri not in all_store_subjects


# ── FR-POL-3 (second): two policies are independent / disjoint ───────────────


def test_two_policies_independent(
    alice_scenario, bob_agent: Agent
) -> None:
    """FR-POL-3: Policy A (Evidence) and Policy B (Claim) permitted sets are disjoint."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    policy_a_uri = alice_dg.declare_sharing_policy(
        "evidence-sharing",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
        exclude_nodes=[e2_uri],
    )
    policy_b_uri = alice_dg.declare_sharing_policy(
        "arch-claim",
        bob_agent.uri,
        local_uri,
        include_nodes=[c1_uri],
    )

    _, permitted_a = alice_dg._compile_policy(policy_a_uri)
    _, permitted_b = alice_dg._compile_policy(policy_b_uri)

    # Policy A has E1; Policy B has C1; no overlap
    assert permitted_a.isdisjoint(permitted_b)


# ── INV-P1: excluded node absent from export ─────────────────────────────────


def test_inv_p1_excluded_absent(
    alice_scenario, bob_agent: Agent
) -> None:
    """INV-P1: E2 (excluded) does not appear in any triple of Policy A export."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    alice_dg.declare_sharing_policy(
        "evidence-sharing",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
        exclude_nodes=[e2_uri],
    )
    exported, _ = alice_dg.export_policy("evidence-sharing", bob_agent.uri)

    for s, p, o in exported:
        assert s != e2_uri, f"INV-P1: excluded node E2 appears as subject: {s!r}"
        assert o != e2_uri, f"INV-P1: excluded node E2 appears as object: {o!r}"


# ── INV-P2: all discourse edges bounded ──────────────────────────────────────


def test_inv_p2_all_edges_bounded(
    alice_scenario, bob_agent: Agent
) -> None:
    """INV-P2: Every discourse edge (s,p,o) in export: s ∈ permitted ∧ o ∈ permitted."""
    alice_dg, e1_uri, e2_uri, c1_uri, q1_uri, local_uri = alice_scenario

    policy_uri = alice_dg.declare_sharing_policy(
        "evidence-sharing",
        bob_agent.uri,
        local_uri,
        include_types=[DG.Evidence],
        exclude_nodes=[e2_uri],
    )
    _, permitted = alice_dg._compile_policy(policy_uri)
    exported, _ = alice_dg.export_policy("evidence-sharing", bob_agent.uri)

    from rdflib import Literal as RDFLiteral
    for s, p, o in exported:
        if p in DISCOURSE_PREDICATES:
            assert s in permitted, f"INV-P2: discourse subject {s!r} not in permitted"
            if not isinstance(o, RDFLiteral):
                assert o in permitted, f"INV-P2: discourse object {o!r} not in permitted"
