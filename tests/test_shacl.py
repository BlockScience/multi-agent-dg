"""SHACL shape tests — FR-SHACL-2 through FR-SHACL-10.

Each shape gets:
  1. A valid fixture that must produce conforms=True.
  2. An invalid fixture (missing required property) that must produce conforms=False.
  3. A message check asserting the violation text contains the requirement ID.

All calls use ``inference="rdfs"`` so SHACL subclass inheritance applies
(CS-1 → Assumption; DS-1 → Decision via subClassOf dg:DiscourseNode).
"""
from __future__ import annotations

import datetime

import pytest
from rdflib import XSD, Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import PROV
import pyshacl

from discourse_graph.namespaces import DG, ENG, load_combined_ontology
from discourse_graph.shapes import load_shapes

SH = Namespace("http://www.w3.org/ns/shacl#")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def shapes_graph():
    return load_shapes()


@pytest.fixture(scope="module")
def ont_graph():
    return load_combined_ontology()


# ── Validation helper ─────────────────────────────────────────────────────────

def validate(data_graph: Graph, shapes_graph: Graph, ont_graph: Graph):
    """Thin wrapper around pyshacl.validate with consistent options."""
    conforms, results_graph, results_text = pyshacl.validate(
        data_graph,
        shacl_graph=shapes_graph,
        ont_graph=ont_graph,
        inference="rdfs",
        abort_on_first=False,
    )
    return conforms, results_graph, results_text


def _req_in_messages(results_graph: Graph, req_id: str) -> bool:
    """Return True if *req_id* appears in any sh:resultMessage in results_graph."""
    messages = list(results_graph.objects(None, SH.resultMessage))
    return any(req_id in str(m) for m in messages)


# ── QS-1: QuestionShape ───────────────────────────────────────────────────────

def test_fr_shacl_2_question_shape_valid(shapes_graph, ont_graph):
    """QS-1: Valid Question with content + label conforms."""
    g = Graph()
    q = URIRef("http://test/q1")
    g.add((q, RDF.type, DG.Question))
    g.add((q, DG.content, Literal("What is the propulsion architecture?", datatype=XSD.string)))
    g.add((q, RDFS.label, Literal("Q1", datatype=XSD.string)))
    conforms, _, _ = validate(g, shapes_graph, ont_graph)
    assert conforms


def test_fr_shacl_2_question_shape_missing_content(shapes_graph, ont_graph):
    """QS-1: Question without dg:content violates the shape."""
    g = Graph()
    q = URIRef("http://test/q1")
    g.add((q, RDF.type, DG.Question))
    g.add((q, RDFS.label, Literal("Q1", datatype=XSD.string)))
    conforms, results_graph, results_text = validate(g, shapes_graph, ont_graph)
    assert not conforms
    assert _req_in_messages(results_graph, "QS-1") or "QS-1" in results_text


def test_fr_shacl_2_question_shape_missing_label(shapes_graph, ont_graph):
    """QS-1: Question without rdfs:label violates the shape."""
    g = Graph()
    q = URIRef("http://test/q1")
    g.add((q, RDF.type, DG.Question))
    g.add((q, DG.content, Literal("A question", datatype=XSD.string)))
    conforms, results_graph, results_text = validate(g, shapes_graph, ont_graph)
    assert not conforms
    assert _req_in_messages(results_graph, "QS-1") or "QS-1" in results_text


# ── CS-1: ClaimShape ─────────────────────────────────────────────────────────

def test_fr_shacl_3_claim_shape_valid(shapes_graph, ont_graph):
    """CS-1: Valid Claim with content + label conforms."""
    g = Graph()
    c = URIRef("http://test/c1")
    g.add((c, RDF.type, DG.Claim))
    g.add((c, DG.content, Literal("A claim.", datatype=XSD.string)))
    g.add((c, RDFS.label, Literal("C1", datatype=XSD.string)))
    conforms, _, _ = validate(g, shapes_graph, ont_graph)
    assert conforms


def test_fr_shacl_3_claim_shape_missing_content(shapes_graph, ont_graph):
    """CS-1: Claim without dg:content violates the shape."""
    g = Graph()
    c = URIRef("http://test/c1")
    g.add((c, RDF.type, DG.Claim))
    g.add((c, RDFS.label, Literal("C1", datatype=XSD.string)))
    conforms, results_graph, results_text = validate(g, shapes_graph, ont_graph)
    assert not conforms
    assert _req_in_messages(results_graph, "CS-1") or "CS-1" in results_text


# ── ES-1: EvidenceShape ───────────────────────────────────────────────────────

def test_fr_shacl_4_evidence_shape_valid(shapes_graph, ont_graph):
    """ES-1: Valid Evidence (with a relation to satisfy ES-2) conforms."""
    g = Graph()
    e = URIRef("http://test/e1")
    c = URIRef("http://test/c1")
    g.add((e, RDF.type, DG.Evidence))
    g.add((e, DG.content, Literal("Evidence text.", datatype=XSD.string)))
    g.add((e, RDFS.label, Literal("E1", datatype=XSD.string)))
    g.add((c, RDF.type, DG.Claim))
    g.add((c, DG.content, Literal("A claim.", datatype=XSD.string)))
    g.add((c, RDFS.label, Literal("C1", datatype=XSD.string)))
    g.add((e, DG.supports, c))
    conforms, _, _ = validate(g, shapes_graph, ont_graph)
    assert conforms


def test_fr_shacl_4_evidence_shape_missing_label(shapes_graph, ont_graph):
    """ES-1: Evidence without rdfs:label violates ES-1."""
    g = Graph()
    e = URIRef("http://test/e1")
    c = URIRef("http://test/c1")
    g.add((e, RDF.type, DG.Evidence))
    g.add((e, DG.content, Literal("Evidence text.", datatype=XSD.string)))
    # no rdfs:label
    g.add((c, RDF.type, DG.Claim))
    g.add((c, DG.content, Literal("A claim.", datatype=XSD.string)))
    g.add((c, RDFS.label, Literal("C1", datatype=XSD.string)))
    g.add((e, DG.supports, c))
    conforms, results_graph, results_text = validate(g, shapes_graph, ont_graph)
    assert not conforms
    assert _req_in_messages(results_graph, "ES-1") or "ES-1" in results_text


# ── ES-2: EvidenceRelationShape ───────────────────────────────────────────────

def test_fr_shacl_5_evidence_relation_valid_supports(shapes_graph, ont_graph):
    """ES-2: Evidence with dg:supports conforms."""
    g = Graph()
    e = URIRef("http://test/e1")
    c = URIRef("http://test/c1")
    g.add((e, RDF.type, DG.Evidence))
    g.add((e, DG.content, Literal("Ev.", datatype=XSD.string)))
    g.add((e, RDFS.label, Literal("E1", datatype=XSD.string)))
    g.add((c, RDF.type, DG.Claim))
    g.add((c, DG.content, Literal("Cl.", datatype=XSD.string)))
    g.add((c, RDFS.label, Literal("C1", datatype=XSD.string)))
    g.add((e, DG.supports, c))
    conforms, _, _ = validate(g, shapes_graph, ont_graph)
    assert conforms


def test_fr_shacl_5_evidence_relation_valid_informs(shapes_graph, ont_graph):
    """ES-2: Evidence with dg:informs conforms."""
    g = Graph()
    e = URIRef("http://test/e1")
    q = URIRef("http://test/q1")
    g.add((e, RDF.type, DG.Evidence))
    g.add((e, DG.content, Literal("Ev.", datatype=XSD.string)))
    g.add((e, RDFS.label, Literal("E1", datatype=XSD.string)))
    g.add((q, RDF.type, DG.Question))
    g.add((q, DG.content, Literal("Q?", datatype=XSD.string)))
    g.add((q, RDFS.label, Literal("Q1", datatype=XSD.string)))
    g.add((e, DG.informs, q))
    conforms, _, _ = validate(g, shapes_graph, ont_graph)
    assert conforms


def test_fr_shacl_5_evidence_relation_missing(shapes_graph, ont_graph):
    """ES-2: Evidence without any relation (supports/opposes/informs) violates ES-2."""
    g = Graph()
    e = URIRef("http://test/e1")
    g.add((e, RDF.type, DG.Evidence))
    g.add((e, DG.content, Literal("Evidence text.", datatype=XSD.string)))
    g.add((e, RDFS.label, Literal("E1", datatype=XSD.string)))
    conforms, results_graph, results_text = validate(g, shapes_graph, ont_graph)
    assert not conforms
    assert _req_in_messages(results_graph, "ES-2") or "ES-2" in results_text


# ── SS-1: SourceShape ─────────────────────────────────────────────────────────

def test_fr_shacl_6_source_shape_valid(shapes_graph, ont_graph):
    """SS-1: Valid Source with content + label conforms."""
    g = Graph()
    s = URIRef("http://test/s1")
    g.add((s, RDF.type, DG.Source))
    g.add((s, DG.content, Literal("A reference document.", datatype=XSD.string)))
    g.add((s, RDFS.label, Literal("S1", datatype=XSD.string)))
    conforms, _, _ = validate(g, shapes_graph, ont_graph)
    assert conforms


def test_fr_shacl_6_source_shape_missing_content(shapes_graph, ont_graph):
    """SS-1: Source without dg:content violates the shape."""
    g = Graph()
    s = URIRef("http://test/s1")
    g.add((s, RDF.type, DG.Source))
    g.add((s, RDFS.label, Literal("S1", datatype=XSD.string)))
    conforms, results_graph, results_text = validate(g, shapes_graph, ont_graph)
    assert not conforms
    assert _req_in_messages(results_graph, "SS-1") or "SS-1" in results_text


# ── IS-1: IngestedNodeShape ───────────────────────────────────────────────────

def _ts() -> Literal:
    return Literal(datetime.datetime.utcnow().isoformat(), datatype=XSD.dateTime)


def test_fr_shacl_7_ingested_node_shape_valid(shapes_graph, ont_graph):
    """IS-1: IngestedNode with wasAttributedTo + ingestedAt conforms."""
    g = Graph()
    n = URIRef("http://test/n1")
    agent = URIRef("http://test/agent")
    g.add((n, RDF.type, DG.IngestedNode))
    g.add((n, PROV.wasAttributedTo, agent))
    g.add((n, DG.ingestedAt, _ts()))
    conforms, _, _ = validate(g, shapes_graph, ont_graph)
    assert conforms


def test_fr_shacl_7_ingested_node_shape_missing_attribution(shapes_graph, ont_graph):
    """IS-1: IngestedNode without prov:wasAttributedTo violates the shape."""
    g = Graph()
    n = URIRef("http://test/n1")
    g.add((n, RDF.type, DG.IngestedNode))
    g.add((n, DG.ingestedAt, _ts()))
    conforms, results_graph, results_text = validate(g, shapes_graph, ont_graph)
    assert not conforms
    assert _req_in_messages(results_graph, "IS-1") or "IS-1" in results_text


def test_fr_shacl_7_ingested_node_shape_missing_ingested_at(shapes_graph, ont_graph):
    """IS-1: IngestedNode without dg:ingestedAt violates the shape."""
    g = Graph()
    n = URIRef("http://test/n1")
    agent = URIRef("http://test/agent")
    g.add((n, RDF.type, DG.IngestedNode))
    g.add((n, PROV.wasAttributedTo, agent))
    conforms, results_graph, results_text = validate(g, shapes_graph, ont_graph)
    assert not conforms
    assert _req_in_messages(results_graph, "IS-1") or "IS-1" in results_text


# ── DS-1: DecisionShape ───────────────────────────────────────────────────────

def _make_valid_decision_graph() -> tuple[Graph, URIRef, URIRef, URIRef]:
    """Return (graph, decision_uri, question_uri, claim_uri) for a valid Decision."""
    g = Graph()
    d = URIRef("http://test/d1")
    q = URIRef("http://test/q1")
    c = URIRef("http://test/c1")
    g.add((d, RDF.type, ENG.Decision))
    g.add((d, DG.content, Literal("A committed choice.", datatype=XSD.string)))
    g.add((d, RDFS.label, Literal("D1", datatype=XSD.string)))
    g.add((d, ENG.decisionStatus, Literal("provisional", datatype=XSD.string)))
    g.add((q, RDF.type, DG.Question))
    g.add((q, DG.content, Literal("Q?", datatype=XSD.string)))
    g.add((q, RDFS.label, Literal("Q1", datatype=XSD.string)))
    g.add((c, RDF.type, DG.Claim))
    g.add((c, DG.content, Literal("C.", datatype=XSD.string)))
    g.add((c, RDFS.label, Literal("C1", datatype=XSD.string)))
    g.add((d, ENG.decision, q))
    g.add((d, ENG.justification, c))
    return g, d, q, c


def test_fr_shacl_8_decision_shape_valid(shapes_graph, ont_graph):
    """DS-1: Valid Decision with all required fields and edges conforms."""
    g, _, _, _ = _make_valid_decision_graph()
    conforms, _, _ = validate(g, shapes_graph, ont_graph)
    assert conforms


def test_fr_shacl_8_decision_shape_missing_decision_edge(shapes_graph, ont_graph):
    """DS-1: Decision without eng:decision edge violates the shape."""
    g, d, q, c = _make_valid_decision_graph()
    g.remove((d, ENG.decision, q))
    conforms, results_graph, results_text = validate(g, shapes_graph, ont_graph)
    assert not conforms
    assert _req_in_messages(results_graph, "DS-1") or "DS-1" in results_text


def test_fr_shacl_8_decision_shape_missing_justification(shapes_graph, ont_graph):
    """DS-1: Decision without eng:justification violates the shape."""
    g, d, q, c = _make_valid_decision_graph()
    g.remove((d, ENG.justification, c))
    conforms, results_graph, results_text = validate(g, shapes_graph, ont_graph)
    assert not conforms
    assert _req_in_messages(results_graph, "DS-1") or "DS-1" in results_text


def test_fr_shacl_8_decision_shape_invalid_status(shapes_graph, ont_graph):
    """DS-1: Decision with decisionStatus='cancelled' (invalid) violates the shape."""
    g, d, q, c = _make_valid_decision_graph()
    g.remove((d, ENG.decisionStatus, Literal("provisional", datatype=XSD.string)))
    g.add((d, ENG.decisionStatus, Literal("cancelled", datatype=XSD.string)))
    conforms, results_graph, results_text = validate(g, shapes_graph, ont_graph)
    assert not conforms
    assert _req_in_messages(results_graph, "DS-1") or "DS-1" in results_text


def test_fr_shacl_8_decision_shape_all_valid_statuses(shapes_graph, ont_graph):
    """DS-1: All three valid decisionStatus values (provisional, final, superseded) conform."""
    for status in ["provisional", "final", "superseded"]:
        g, d, _, _ = _make_valid_decision_graph()
        g.remove((d, ENG.decisionStatus, Literal("provisional", datatype=XSD.string)))
        g.add((d, ENG.decisionStatus, Literal(status, datatype=XSD.string)))
        conforms, _, _ = validate(g, shapes_graph, ont_graph)
        assert conforms, f"decisionStatus='{status}' should conform but did not"


# ── AS-1: AssumptionShape ─────────────────────────────────────────────────────

def test_fr_shacl_9_assumption_shape_valid(shapes_graph, ont_graph):
    """AS-1: Valid Assumption with content + label + scope conforms."""
    g = Graph()
    a = URIRef("http://test/a1")
    g.add((a, RDF.type, ENG.Assumption))
    g.add((a, DG.content, Literal("An assumption.", datatype=XSD.string)))
    g.add((a, RDFS.label, Literal("A1", datatype=XSD.string)))
    g.add((a, ENG.assumptionScope, Literal("Phase A trade study", datatype=XSD.string)))
    conforms, _, _ = validate(g, shapes_graph, ont_graph)
    assert conforms


def test_fr_shacl_9_assumption_shape_missing_scope(shapes_graph, ont_graph):
    """AS-1: Assumption without eng:assumptionScope violates the shape."""
    g = Graph()
    a = URIRef("http://test/a1")
    g.add((a, RDF.type, ENG.Assumption))
    g.add((a, DG.content, Literal("An assumption.", datatype=XSD.string)))
    g.add((a, RDFS.label, Literal("A1", datatype=XSD.string)))
    conforms, results_graph, results_text = validate(g, shapes_graph, ont_graph)
    assert not conforms
    assert _req_in_messages(results_graph, "AS-1") or "AS-1" in results_text


def test_fr_shacl_9_assumption_inherits_cs1_missing_content(shapes_graph, ont_graph):
    """AS-1 + CS-1: Assumption without dg:content violates CS-1 via subclass inheritance."""
    g = Graph()
    a = URIRef("http://test/a1")
    g.add((a, RDF.type, ENG.Assumption))
    # no dg:content — should fail CS-1 via eng:Assumption rdfs:subClassOf dg:Claim
    g.add((a, RDFS.label, Literal("A1", datatype=XSD.string)))
    g.add((a, ENG.assumptionScope, Literal("Phase A trade study", datatype=XSD.string)))
    conforms, results_graph, results_text = validate(g, shapes_graph, ont_graph)
    assert not conforms
    assert _req_in_messages(results_graph, "CS-1") or "CS-1" in results_text


# ── OP-1: OpensDisjointShape ──────────────────────────────────────────────────

def _make_op1_graph() -> tuple[Graph, URIRef, URIRef, URIRef]:
    """Return (graph, decision, q1, q2) with all DS-1 requirements satisfied."""
    g = Graph()
    d = URIRef("http://test/d1")
    q1 = URIRef("http://test/q1")
    q2 = URIRef("http://test/q2")
    c = URIRef("http://test/c1")
    g.add((d, RDF.type, ENG.Decision))
    g.add((d, DG.content, Literal("A decision.", datatype=XSD.string)))
    g.add((d, RDFS.label, Literal("D1", datatype=XSD.string)))
    g.add((d, ENG.decisionStatus, Literal("provisional", datatype=XSD.string)))
    g.add((q1, RDF.type, DG.Question))
    g.add((q1, DG.content, Literal("Q1?", datatype=XSD.string)))
    g.add((q1, RDFS.label, Literal("Q1", datatype=XSD.string)))
    g.add((q2, RDF.type, DG.Question))
    g.add((q2, DG.content, Literal("Q2?", datatype=XSD.string)))
    g.add((q2, RDFS.label, Literal("Q2", datatype=XSD.string)))
    g.add((c, RDF.type, DG.Claim))
    g.add((c, DG.content, Literal("C.", datatype=XSD.string)))
    g.add((c, RDFS.label, Literal("C1", datatype=XSD.string)))
    g.add((d, ENG.decision, q1))
    g.add((d, ENG.justification, c))
    return g, d, q1, q2


def test_fr_shacl_10_op1_valid_different_questions(shapes_graph, ont_graph):
    """OP-1: Decision with eng:decision→Q1 and eng:opens→Q2 (distinct) conforms."""
    g, d, q1, q2 = _make_op1_graph()
    g.add((d, ENG.opens, q2))  # different Question from eng:decision target
    conforms, _, _ = validate(g, shapes_graph, ont_graph)
    assert conforms


def test_fr_shacl_10_op1_violation_same_question(shapes_graph, ont_graph):
    """OP-1: Decision with eng:decision and eng:opens targeting the same Question violates OP-1."""
    g, d, q1, q2 = _make_op1_graph()
    g.add((d, ENG.opens, q1))  # same as eng:decision target → OP-1 violation
    conforms, results_graph, results_text = validate(g, shapes_graph, ont_graph)
    assert not conforms
    assert _req_in_messages(results_graph, "OP-1") or "OP-1" in results_text


def test_fr_shacl_10_op1_no_opens_conforms(shapes_graph, ont_graph):
    """OP-1: Decision with eng:decision but no eng:opens conforms (OP-1 does not fire)."""
    g, d, q1, q2 = _make_op1_graph()
    # No eng:opens added — OP-1 SPARQL SELECT returns zero rows → no violation
    conforms, _, _ = validate(g, shapes_graph, ont_graph)
    assert conforms


# ── All shapes carry req IDs ──────────────────────────────────────────────────

def test_all_shapes_carry_req_ids(shapes_graph):
    """FR-SHACL-11: Every SHACL shape has at least one sh:message containing its req ID."""
    from discourse_graph.shapes import SHACL_TTL
    expected_ids = ["QS-1", "CS-1", "ES-1", "ES-2", "SS-1", "IS-1", "DS-1", "AS-1", "OP-1"]
    for req_id in expected_ids:
        assert req_id in SHACL_TTL, f"SHACL_TTL must contain at least one sh:message with '{req_id}'"
