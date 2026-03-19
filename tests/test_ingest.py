"""Tests for DiscourseGraph.ingest() — FR-ING-1 through FR-ING-3."""
from __future__ import annotations

import pytest
from rdflib import RDF, RDFS, XSD, Graph, Literal, URIRef
from rdflib.namespace import PROV

from discourse_graph.agent import Agent
from discourse_graph.graph import DiscourseGraph
from discourse_graph.namespaces import DG
from discourse_graph.namespaces import load_combined_ontology
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
def bob_dg(bob_agent: Agent, ontology: Graph, shapes: Graph) -> DiscourseGraph:
    return DiscourseGraph(bob_agent, ontology, shapes)


@pytest.fixture
def e1_uri() -> URIRef:
    return URIRef("http://example.org/alice/node/e1-fixture")


@pytest.fixture
def alice_subgraph(e1_uri: URIRef) -> Graph:
    """Minimal rdflib.Graph representing a single Evidence node from Alice."""
    g = Graph()
    g.add((e1_uri, RDF.type, DG.Evidence))
    g.add((e1_uri, RDF.type, DG.DiscourseNode))   # required for FR-ING-2 detection
    g.add((e1_uri, RDF.type, PROV.Entity))
    g.add((e1_uri, DG.content, Literal("Delta-V budget analysis", datatype=XSD.string)))
    g.add((e1_uri, RDFS.label, Literal("E1-DeltaV", datatype=XSD.string)))
    return g


# ── FR-ING-1: ingest copies triples to named graph ───────────────────────────


def test_fr_ing_1_copy_triples_to_named_graph(
    bob_dg: DiscourseGraph, alice_subgraph: Graph, alice_agent: Agent, e1_uri: URIRef
) -> None:
    """FR-ING-1: All triples from subgraph appear in the ingested named graph."""
    ingested_uri = bob_dg.ingest(alice_subgraph, alice_agent.uri)
    ingested_ctx = bob_dg._store.get_context(ingested_uri)

    # Every original triple must be present
    for triple in alice_subgraph:
        assert triple in ingested_ctx, f"Missing triple: {triple}"


def test_fr_ing_1_graph_name_slug(
    bob_dg: DiscourseGraph, alice_subgraph: Graph,
    alice_agent: Agent, bob_agent: Agent, e1_uri: URIRef
) -> None:
    """FR-ING-1: Named graph URI follows agent.graph_uri('ingested-alice') convention.

    Slug 'alice' is derived from alice_agent.uri = '.../alice/agent'
    by taking the second-to-last path segment.
    """
    ingested_uri = bob_dg.ingest(alice_subgraph, alice_agent.uri)
    expected_uri = bob_agent.graph_uri("ingested-alice")
    assert ingested_uri == expected_uri


# ── FR-ING-2: ingested nodes annotated with IngestedNode type ────────────────


def test_fr_ing_2_ingested_node_type(
    bob_dg: DiscourseGraph, alice_subgraph: Graph, alice_agent: Agent, e1_uri: URIRef
) -> None:
    """FR-ING-2: Each dg:DiscourseNode in subgraph gets rdf:type dg:IngestedNode."""
    ingested_uri = bob_dg.ingest(alice_subgraph, alice_agent.uri)
    ingested_ctx = bob_dg._store.get_context(ingested_uri)

    assert (e1_uri, RDF.type, DG.IngestedNode) in ingested_ctx


def test_fr_ing_2_prov_attributed(
    bob_dg: DiscourseGraph, alice_subgraph: Graph, alice_agent: Agent, e1_uri: URIRef
) -> None:
    """FR-ING-2: Each ingested node has prov:wasAttributedTo <alice_agent.uri>."""
    ingested_uri = bob_dg.ingest(alice_subgraph, alice_agent.uri)
    ingested_ctx = bob_dg._store.get_context(ingested_uri)

    assert (e1_uri, PROV.wasAttributedTo, alice_agent.uri) in ingested_ctx


def test_fr_ing_2_ingested_at_datetime(
    bob_dg: DiscourseGraph, alice_subgraph: Graph, alice_agent: Agent, e1_uri: URIRef
) -> None:
    """FR-ING-2: Each ingested node has dg:ingestedAt as xsd:dateTime literal."""
    ingested_uri = bob_dg.ingest(alice_subgraph, alice_agent.uri)
    ingested_ctx = bob_dg._store.get_context(ingested_uri)

    ingested_at_vals = list(ingested_ctx.objects(e1_uri, DG.ingestedAt))
    assert len(ingested_at_vals) == 1
    assert ingested_at_vals[0].datatype == XSD.dateTime


# ── FR-ING-3: ingest returns URIRef ──────────────────────────────────────────


def test_fr_ing_3_returns_graph_uri(
    bob_dg: DiscourseGraph, alice_subgraph: Graph, alice_agent: Agent
) -> None:
    """FR-ING-3: ingest() returns a URIRef for the new named graph."""
    result = bob_dg.ingest(alice_subgraph, alice_agent.uri)
    assert isinstance(result, URIRef)


# ── FR-SHACL-7: IS-1 passes after ingest ─────────────────────────────────────


def test_is1_passes_after_ingest(
    bob_dg: DiscourseGraph, alice_subgraph: Graph, alice_agent: Agent, e1_uri: URIRef
) -> None:
    """FR-SHACL-7: After ingest(), bob.verify() passes IS-1 for ingested nodes.

    IS-1 requires that every dg:IngestedNode has prov:wasAttributedTo.
    Ingest must add this triple so IS-1 is satisfied.
    """
    ingested_uri = bob_dg.ingest(alice_subgraph, alice_agent.uri)
    report = bob_dg.verify(ingested_uri)
    assert "IS-1" not in report.violation_ids(), (
        f"IS-1 violated after ingest. Report:\n{report.summary()}"
    )
