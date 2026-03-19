"""Tests for the eng: ontology — FR-ONT-ENG-1 through FR-ONT-ENG-9."""
from __future__ import annotations

import inspect

import pytest
from rdflib import OWL, RDF, RDFS, XSD, URIRef
from rdflib.namespace import PROV

import discourse_graph.ontology_eng as _eng_mod
from discourse_graph.namespaces import DG, ENG
from discourse_graph.ontology_dg import load_dg_ontology
from discourse_graph.ontology_eng import ENG_ONTOLOGY_TTL, load_eng_ontology


@pytest.fixture(scope="module")
def eng_graph():
    """Load eng: ontology once per test module."""
    return load_eng_ontology()


@pytest.fixture(scope="module")
def merged_graph():
    """Merged dg: + eng: for tests that need cross-namespace subclass reasoning."""
    return load_dg_ontology() + load_eng_ontology()


# FR-ONT-ENG-1 ────────────────────────────────────────────────────────────────

def test_fr_ont_eng_1_parses_and_imports(eng_graph):
    """FR-ONT-ENG-1: Parses without error and declares owl:imports <dg:>."""
    assert len(eng_graph) > 0
    eng_ont_iri = URIRef("http://example.org/eng/1.0/")
    dg_ont_iri = URIRef("http://example.org/dg/1.0/")
    assert (eng_ont_iri, OWL.imports, dg_ont_iri) in eng_graph


# FR-ONT-ENG-2 ────────────────────────────────────────────────────────────────

def test_fr_ont_eng_2_decision_subclass(eng_graph):
    """FR-ONT-ENG-2: eng:Decision is rdfs:subClassOf dg:DiscourseNode and prov:Entity."""
    assert (ENG.Decision, RDFS.subClassOf, DG.DiscourseNode) in eng_graph
    assert (ENG.Decision, RDFS.subClassOf, PROV.Entity) in eng_graph


# FR-ONT-ENG-3 ────────────────────────────────────────────────────────────────

def test_fr_ont_eng_3_decision_predicate(eng_graph):
    """FR-ONT-ENG-3: eng:decision has domain eng:Decision and range dg:Question."""
    assert (ENG.decision, RDF.type, OWL.ObjectProperty) in eng_graph
    assert (ENG.decision, RDFS.domain, ENG.Decision) in eng_graph
    assert (ENG.decision, RDFS.range, DG.Question) in eng_graph


# FR-ONT-ENG-4 ────────────────────────────────────────────────────────────────

def test_fr_ont_eng_4_opens_predicate(eng_graph):
    """FR-ONT-ENG-4: eng:opens has domain eng:Decision and range dg:Question."""
    assert (ENG.opens, RDF.type, OWL.ObjectProperty) in eng_graph
    assert (ENG.opens, RDFS.domain, ENG.Decision) in eng_graph
    assert (ENG.opens, RDFS.range, DG.Question) in eng_graph


# FR-ONT-ENG-5 ────────────────────────────────────────────────────────────────

def test_fr_ont_eng_5_justification_predicate(eng_graph):
    """FR-ONT-ENG-5: eng:justification has domain eng:Decision and range dg:DiscourseNode."""
    assert (ENG.justification, RDF.type, OWL.ObjectProperty) in eng_graph
    assert (ENG.justification, RDFS.domain, ENG.Decision) in eng_graph
    assert (ENG.justification, RDFS.range, DG.DiscourseNode) in eng_graph


# FR-ONT-ENG-6 ────────────────────────────────────────────────────────────────

def test_fr_ont_eng_6_assumption_subclass_claim(eng_graph):
    """FR-ONT-ENG-6: eng:Assumption is rdfs:subClassOf dg:Claim."""
    assert (ENG.Assumption, RDFS.subClassOf, DG.Claim) in eng_graph


# FR-ONT-ENG-7 ────────────────────────────────────────────────────────────────

def test_fr_ont_eng_7_assumption_scope_property(eng_graph):
    """FR-ONT-ENG-7: eng:assumptionScope is owl:DatatypeProperty with range xsd:string."""
    assert (ENG.assumptionScope, RDF.type, OWL.DatatypeProperty) in eng_graph
    assert (ENG.assumptionScope, RDFS.range, XSD.string) in eng_graph


# FR-ONT-ENG-8 ────────────────────────────────────────────────────────────────

def test_fr_ont_eng_8_decision_status_property(eng_graph):
    """FR-ONT-ENG-8: eng:decisionStatus is owl:DatatypeProperty on eng:Decision."""
    assert (ENG.decisionStatus, RDF.type, OWL.DatatypeProperty) in eng_graph
    assert (ENG.decisionStatus, RDFS.domain, ENG.Decision) in eng_graph


# FR-ONT-ENG-9 ────────────────────────────────────────────────────────────────

def test_fr_ont_eng_9_namespace_stub_comment():
    """FR-ONT-ENG-9: Source file carries the namespace stub replacement notice."""
    source = inspect.getsource(_eng_mod)
    assert "NAMESPACE STUB: replace with firm-controlled IRI before production use." in source


# FR-ONT-ENG-10 ───────────────────────────────────────────────────────────────

def test_fr_ont_eng_10_option_predicate(eng_graph):
    """FR-ONT-ENG-10: eng:option domain dg:Claim, range dg:Question."""
    pred = ENG.option
    assert (pred, RDF.type, OWL.ObjectProperty) in eng_graph
    assert (pred, RDFS.domain, DG.Claim) in eng_graph
    assert (pred, RDFS.range, DG.Question) in eng_graph


# ARCH ────────────────────────────────────────────────────────────────────────

def test_seam_dg_question_only_shared():
    """ARCH: eng: must not re-declare dg: node classes.

    dg:Question is the intentional seam — referenced as range of eng:decision, eng:opens,
    and eng:option.
    dg:DiscourseNode is referenced as superclass of eng:Decision and range of eng:justification.
    dg:Claim is referenced as domain of eng:option.
    Re-declaring any of these as eng:Question, eng:Claim, etc. is forbidden.
    Cross-namespace references (dg:Claim as a domain) are permitted.
    """
    # These would violate the seam design
    forbidden = [
        "eng:Question",    # must not exist — dg:Question is the shared term
        "eng:Claim",       # must not exist — dg:Claim is the shared term
        "eng:Evidence",    # must not exist
        "eng:Source",      # must not exist
    ]
    for term in forbidden:
        assert term not in ENG_ONTOLOGY_TTL, (
            f"eng: ontology must not declare {term}; "
            f"dg:Question is the only cross-namespace seam."
        )
