"""Tests for discourse_graph/models.py — FR-PYD-1 through FR-PYD-7.

Each test function is named test_<req_id>_<description> where possible.
"""
from __future__ import annotations

import pytest
import rdflib
from rdflib import RDF, Graph, Literal, URIRef
from rdflib.namespace import PROV

from discourse_graph.models import (
    Assumption,
    Claim,
    Decision,
    Evidence,
    NODE_TYPE_MAP,
    Question,
    Source,
)
from discourse_graph.namespaces import DG, ENG, load_combined_ontology
from discourse_graph.shapes import load_shapes


# ── Shared fixtures ───────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def shapes_graph() -> Graph:
    return load_shapes()


@pytest.fixture(scope="module")
def ont_graph() -> Graph:
    return load_combined_ontology()


# ── FR-PYD-1: all types instantiate ──────────────────────────────────────────


def test_fr_pyd_1_all_types_instantiate() -> None:
    """FR-PYD-1: Each of the 6 model classes instantiates with valid fields."""
    Question(content="What is the mass budget?", label="Q1-Mass")
    Claim(content="Bipropellant is baseline.", label="C1-Biprop")
    Evidence(content="Delta-V analysis: 3.2 km/s.", label="E1-DeltaV")
    Source(content="AIAA propulsion handbook.", label="S1-AIAA")
    Decision(content="Select MMH/NTO.", label="D1-Select", status="provisional")
    Assumption(content="SEP not viable.", label="A1-SEP", scope="Phase A")


def test_node_type_map_complete() -> None:
    """FR-PYD-1: NODE_TYPE_MAP contains an entry for all 6 model classes."""
    expected = {Question, Claim, Evidence, Source, Decision, Assumption}
    assert set(NODE_TYPE_MAP.keys()) == expected


# ── FR-PYD-2: field constraints ───────────────────────────────────────────────


@pytest.mark.parametrize("cls,kwargs", [
    (Question,   {"label": "Q1"}),
    (Claim,      {"label": "C1"}),
    (Evidence,   {"label": "E1"}),
    (Source,     {"label": "S1"}),
    (Decision,   {"label": "D1"}),
    (Assumption, {"label": "A1", "scope": "x"}),
])
def test_fr_pyd_2_content_required(cls, kwargs) -> None:
    """FR-PYD-2: All models raise pydantic.ValidationError when content=""."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        cls(content="", **kwargs)


@pytest.mark.parametrize("cls,kwargs", [
    (Question,   {"content": "x"}),
    (Claim,      {"content": "x"}),
    (Evidence,   {"content": "x"}),
    (Source,     {"content": "x"}),
    (Decision,   {"content": "x"}),
    (Assumption, {"content": "x", "scope": "x"}),
])
def test_fr_pyd_2_label_required(cls, kwargs) -> None:
    """FR-PYD-2: All models raise pydantic.ValidationError when label=""."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        cls(label="", **kwargs)


def test_fr_pyd_2_decision_status_valid() -> None:
    """FR-PYD-2: Decision with valid status succeeds; invalid status raises."""
    from pydantic import ValidationError
    Decision(content="x", label="y", status="provisional")
    Decision(content="x", label="y", status="final")
    Decision(content="x", label="y", status="superseded")
    with pytest.raises(ValidationError):
        Decision(content="x", label="y", status="cancelled")


def test_fr_pyd_2_assumption_scope_required() -> None:
    """FR-PYD-2: Assumption without scope raises pydantic.ValidationError."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Assumption(content="x", label="y")  # type: ignore[call-arg]


# ── FR-PYD-3: Python class hierarchy mirrors OWL ─────────────────────────────


def test_fr_pyd_3_assumption_is_claim_subclass() -> None:
    """FR-PYD-3: isinstance(Assumption(...), Claim) is True."""
    a = Assumption(content="x", label="y", scope="z")
    assert isinstance(a, Claim)


def test_fr_pyd_3_assumption_owl_subclass(ont_graph: Graph) -> None:
    """FR-PYD-3: ENG.Assumption is declared rdfs:subClassOf DG.Claim in merged ontology."""
    from rdflib import RDFS
    assert (ENG.Assumption, RDFS.subClassOf, DG.Claim) in ont_graph


# ── FR-PYD-5: Pydantic checks before RDF ─────────────────────────────────────


def test_fr_pyd_5_pydantic_validates_before_rdf() -> None:
    """FR-PYD-5: pydantic.ValidationError is raised before any rdflib Graph is touched."""
    from pydantic import ValidationError
    # Patch Graph.__init__ to detect if it is called during the failed construction.
    import rdflib as _rdflib
    original_init = _rdflib.Graph.__init__
    touched = []
    def spy_init(self, *args, **kwargs):
        touched.append(True)
        return original_init(self, *args, **kwargs)
    _rdflib.Graph.__init__ = spy_init
    try:
        with pytest.raises(ValidationError):
            Question(content="", label="q")
    finally:
        _rdflib.Graph.__init__ = original_init
    assert not touched, "rdflib.Graph was instantiated during failed Pydantic construction"


# ── FR-PYD-6: to_triples() ───────────────────────────────────────────────────


def test_fr_pyd_6_to_triples_question() -> None:
    """FR-PYD-6: Question.to_triples() includes rdf:type dg:Question, dg:content, rdfs:label."""
    from rdflib import RDFS
    uri = URIRef("http://test/q1")
    triples = Question(content="What is mass?", label="Q1").to_triples(uri)
    pred_obj = {(p, o) for _, p, o in triples}
    assert (RDF.type, DG.Question) in pred_obj
    assert any(p == DG.content for _, p, _ in triples)
    assert any(p == RDFS.label for _, p, _ in triples)


def test_fr_pyd_6_to_triples_decision() -> None:
    """FR-PYD-6: Decision.to_triples() includes eng:decisionStatus."""
    uri = URIRef("http://test/d1")
    triples = Decision(content="Select MMH/NTO.", label="D1", status="final").to_triples(uri)
    pred_obj = {(p, o) for _, p, o in triples}
    assert (ENG.decisionStatus, Literal("final", datatype=rdflib.XSD.string)) in pred_obj


def test_fr_pyd_6_to_triples_assumption() -> None:
    """FR-PYD-6: Assumption.to_triples() includes eng:assumptionScope."""
    uri = URIRef("http://test/a1")
    triples = Assumption(content="SEP not viable.", label="A1", scope="Phase A").to_triples(uri)
    assert any(p == ENG.assumptionScope for _, p, _ in triples)


def test_assumption_all_three_rdf_types() -> None:
    """FR-PYD-6: Assumption.to_triples() includes rdf:type eng:Assumption, dg:Claim, dg:DiscourseNode."""
    uri = URIRef("http://test/a1")
    triples = Assumption(content="x", label="y", scope="z").to_triples(uri)
    types = {o for _, p, o in triples if p == RDF.type}
    assert ENG.Assumption in types
    assert DG.Claim in types
    assert DG.DiscourseNode in types


def test_fr_pyd_6_round_trip_shacl_all_types(shapes_graph: Graph, ont_graph: Graph) -> None:
    """FR-PYD-6: For each model type, to_triples() → Graph → pyshacl.validate → conforms=True."""
    import pyshacl

    base_uri = "http://test/"

    # Helper to build URIRef
    def u(local: str) -> URIRef:
        return URIRef(base_uri + local)

    test_cases: list[tuple] = []

    # Question — QS-1: content + label only
    q = Question(content="What is mass?", label="Q1")
    g_q = Graph()
    for t in q.to_triples(u("q1")):
        g_q.add(t)
    test_cases.append(("Question", g_q))

    # Claim — CS-1: content + label only
    c = Claim(content="Bipropellant is baseline.", label="C1")
    g_c = Graph()
    for t in c.to_triples(u("c1")):
        g_c.add(t)
    test_cases.append(("Claim", g_c))

    # Evidence — ES-1 + ES-2: needs at least one relation edge
    e = Evidence(content="Delta-V: 3.2 km/s.", label="E1")
    g_e = Graph()
    for t in e.to_triples(u("e1")):
        g_e.add(t)
    # Add a Claim target + dg:supports edge to satisfy ES-2
    g_e.add((u("c_target"), RDF.type, DG.Claim))
    g_e.add((u("c_target"), DG.content, Literal("target claim", datatype=rdflib.XSD.string)))
    g_e.add((u("c_target"), rdflib.RDFS.label, Literal("C-target", datatype=rdflib.XSD.string)))
    g_e.add((u("e1"), DG.supports, u("c_target")))
    test_cases.append(("Evidence", g_e))

    # Source — SS-1: content + label only
    s = Source(content="AIAA handbook.", label="S1")
    g_s = Graph()
    for t in s.to_triples(u("s1")):
        g_s.add(t)
    test_cases.append(("Source", g_s))

    # Decision — DS-1: needs eng:decision + eng:justification edges
    d = Decision(content="Select MMH/NTO.", label="D1", status="provisional")
    g_d = Graph()
    for t in d.to_triples(u("d1")):
        g_d.add(t)
    # Add Question target for eng:decision
    g_d.add((u("q_target"), RDF.type, DG.Question))
    g_d.add((u("q_target"), DG.content, Literal("open question", datatype=rdflib.XSD.string)))
    g_d.add((u("q_target"), rdflib.RDFS.label, Literal("Q-target", datatype=rdflib.XSD.string)))
    g_d.add((u("d1"), ENG.decision, u("q_target")))
    # Add Claim as justification
    g_d.add((u("c_just"), RDF.type, DG.Claim))
    g_d.add((u("c_just"), DG.content, Literal("justification", datatype=rdflib.XSD.string)))
    g_d.add((u("c_just"), rdflib.RDFS.label, Literal("C-just", datatype=rdflib.XSD.string)))
    g_d.add((u("d1"), ENG.justification, u("c_just")))
    test_cases.append(("Decision", g_d))

    # Assumption — CS-1 + AS-1: content + label + scope
    a = Assumption(content="SEP not viable.", label="A1", scope="Phase A")
    g_a = Graph()
    for t in a.to_triples(u("a1")):
        g_a.add(t)
    test_cases.append(("Assumption", g_a))

    for name, data_graph in test_cases:
        conforms, _, report_text = pyshacl.validate(
            data_graph,
            shacl_graph=shapes_graph,
            ont_graph=ont_graph,
            inference="rdfs",
            abort_on_first=False,
        )
        assert conforms, f"{name} round-trip failed SHACL:\n{report_text}"


# ── FR-PYD-7: VerificationReport serialises to JSON ──────────────────────────


def test_fr_pyd_7_verification_report_json() -> None:
    """FR-PYD-7: VerificationReport.model_dump() runs without error."""
    from discourse_graph.report import VerificationReport  # deferred — report.py created in step 13
    r = VerificationReport(
        conforms=True,
        report_text="Validation Report\nConforms: True",
        results_graph=Graph(),
    )
    dump = r.model_dump()
    assert isinstance(dump, dict)
    assert dump["conforms"] is True


# ── SHACL subclass inheritance tests ─────────────────────────────────────────


def test_assumption_cs1_inherited_via_shacl(shapes_graph: Graph, ont_graph: Graph) -> None:
    """FR-SHACL-3: Assumption without dg:content fails CS-1 via SHACL subclass inheritance."""
    import pyshacl

    uri = URIRef("http://test/a_bad")
    g = Graph()
    # Add Assumption with label but NO content — should fail CS-1
    g.add((uri, RDF.type, ENG.Assumption))
    g.add((uri, RDF.type, DG.Claim))
    g.add((uri, RDF.type, DG.DiscourseNode))
    g.add((uri, RDF.type, PROV.Entity))
    g.add((uri, rdflib.RDFS.label, Literal("A-bad", datatype=rdflib.XSD.string)))
    g.add((uri, ENG.assumptionScope, Literal("Phase A", datatype=rdflib.XSD.string)))

    conforms, _, report_text = pyshacl.validate(
        g,
        shacl_graph=shapes_graph,
        ont_graph=ont_graph,
        inference="rdfs",
        abort_on_first=False,
    )
    assert not conforms
    assert "CS-1" in report_text


def test_assumption_as1_scope_required(shapes_graph: Graph, ont_graph: Graph) -> None:
    """FR-SHACL-9: Assumption without eng:assumptionScope fails AS-1."""
    import pyshacl

    uri = URIRef("http://test/a_noscope")
    g = Graph()
    g.add((uri, RDF.type, ENG.Assumption))
    g.add((uri, RDF.type, DG.Claim))
    g.add((uri, RDF.type, DG.DiscourseNode))
    g.add((uri, RDF.type, PROV.Entity))
    g.add((uri, DG.content, Literal("SEP not viable.", datatype=rdflib.XSD.string)))
    g.add((uri, rdflib.RDFS.label, Literal("A-noscope", datatype=rdflib.XSD.string)))
    # No eng:assumptionScope

    conforms, _, report_text = pyshacl.validate(
        g,
        shacl_graph=shapes_graph,
        ont_graph=ont_graph,
        inference="rdfs",
        abort_on_first=False,
    )
    assert not conforms
    assert "AS-1" in report_text
