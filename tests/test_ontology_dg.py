"""Tests for the dg: ontology — FR-ONT-DG-1 through FR-ONT-DG-7."""
from __future__ import annotations

import pytest
from rdflib import OWL, RDF, RDFS, XSD, URIRef
from rdflib.namespace import PROV

from discourse_graph.namespaces import DG
from discourse_graph.ontology_dg import DG_ONTOLOGY_TTL, load_dg_ontology


@pytest.fixture(scope="module")
def dg_graph():
    """Load dg: ontology once per test module."""
    return load_dg_ontology()


# FR-ONT-DG-1 ─────────────────────────────────────────────────────────────────

def test_fr_ont_dg_1_parses(dg_graph):
    """FR-ONT-DG-1: load_dg_ontology() returns a non-empty Graph without parse error."""
    assert len(dg_graph) > 0


# FR-ONT-DG-2 ─────────────────────────────────────────────────────────────────

def test_fr_ont_dg_2_question_class(dg_graph):
    """FR-ONT-DG-2: dg:Question declared as owl:Class."""
    assert (DG.Question, RDF.type, OWL.Class) in dg_graph


def test_fr_ont_dg_2_claim_class(dg_graph):
    """FR-ONT-DG-2: dg:Claim declared as owl:Class."""
    assert (DG.Claim, RDF.type, OWL.Class) in dg_graph


def test_fr_ont_dg_2_evidence_class(dg_graph):
    """FR-ONT-DG-2: dg:Evidence declared as owl:Class."""
    assert (DG.Evidence, RDF.type, OWL.Class) in dg_graph


def test_fr_ont_dg_2_source_class(dg_graph):
    """FR-ONT-DG-2: dg:Source declared as owl:Class."""
    assert (DG.Source, RDF.type, OWL.Class) in dg_graph


# FR-ONT-DG-3 ─────────────────────────────────────────────────────────────────

def test_fr_ont_dg_3_subclass_discourse_node(dg_graph):
    """FR-ONT-DG-3: All four node classes are subclasses of dg:DiscourseNode."""
    for cls in [DG.Question, DG.Claim, DG.Evidence, DG.Source]:
        assert (cls, RDFS.subClassOf, DG.DiscourseNode) in dg_graph, (
            f"{cls} must be rdfs:subClassOf dg:DiscourseNode"
        )


def test_fr_ont_dg_3_discourse_node_subclass_prov(dg_graph):
    """FR-ONT-DG-3: dg:DiscourseNode is rdfs:subClassOf prov:Entity."""
    assert (DG.DiscourseNode, RDFS.subClassOf, PROV.Entity) in dg_graph


# FR-ONT-DG-4 ─────────────────────────────────────────────────────────────────

def test_fr_ont_dg_4_informs(dg_graph):
    """FR-ONT-DG-4: dg:informs has domain dg:Evidence and range dg:Question."""
    assert (DG.informs, RDF.type, OWL.ObjectProperty) in dg_graph
    assert (DG.informs, RDFS.domain, DG.Evidence) in dg_graph
    assert (DG.informs, RDFS.range, DG.Question) in dg_graph


def test_fr_ont_dg_4_supports(dg_graph):
    """FR-ONT-DG-4: dg:supports has domain dg:Evidence and range dg:Claim."""
    assert (DG.supports, RDF.type, OWL.ObjectProperty) in dg_graph
    assert (DG.supports, RDFS.domain, DG.Evidence) in dg_graph
    assert (DG.supports, RDFS.range, DG.Claim) in dg_graph


def test_fr_ont_dg_4_opposes(dg_graph):
    """FR-ONT-DG-4: dg:opposes has domain dg:Evidence and range dg:Claim."""
    assert (DG.opposes, RDF.type, OWL.ObjectProperty) in dg_graph
    assert (DG.opposes, RDFS.domain, DG.Evidence) in dg_graph
    assert (DG.opposes, RDFS.range, DG.Claim) in dg_graph


# FR-ONT-DG-5 ─────────────────────────────────────────────────────────────────

def test_fr_ont_dg_5_no_answers(dg_graph):
    """FR-ONT-DG-5: dg:answers must NOT appear anywhere in the ontology."""
    # Check both graph triples and raw Turtle string (catches any form)
    assert not any(True for _ in dg_graph.triples((DG.answers, None, None)))
    assert not any(True for _ in dg_graph.triples((None, DG.answers, None)))
    assert not any(True for _ in dg_graph.triples((None, None, DG.answers)))
    assert "dg:answers" not in DG_ONTOLOGY_TTL
    assert str(DG.answers) not in DG_ONTOLOGY_TTL


def test_fr_ont_dg_5_no_cites(dg_graph):
    """FR-ONT-DG-5: dg:cites must NOT appear anywhere in the ontology."""
    assert not any(True for _ in dg_graph.triples((DG.cites, None, None)))
    assert not any(True for _ in dg_graph.triples((None, DG.cites, None)))
    assert not any(True for _ in dg_graph.triples((None, None, DG.cites)))
    assert "dg:cites" not in DG_ONTOLOGY_TTL
    assert str(DG.cites) not in DG_ONTOLOGY_TTL


# FR-ONT-DG-6 ─────────────────────────────────────────────────────────────────

def test_fr_ont_dg_6_agent_class(dg_graph):
    """FR-ONT-DG-6: dg:Agent is rdfs:subClassOf prov:Agent."""
    assert (DG.Agent, RDFS.subClassOf, PROV.Agent) in dg_graph


def test_fr_ont_dg_6_sharing_policy_class(dg_graph):
    """FR-ONT-DG-6: dg:SharingPolicy declared as owl:Class."""
    assert (DG.SharingPolicy, RDF.type, OWL.Class) in dg_graph


def test_fr_ont_dg_6_ingested_node_class(dg_graph):
    """FR-ONT-DG-6: dg:IngestedNode declared as owl:Class."""
    assert (DG.IngestedNode, RDF.type, OWL.Class) in dg_graph


# FR-ONT-DG-7 ─────────────────────────────────────────────────────────────────

def test_fr_ont_dg_7_datatype_properties(dg_graph):
    """FR-ONT-DG-7: content, created, ingestedAt, policyName are owl:DatatypeProperty."""
    for prop in [DG.content, DG.created, DG.ingestedAt, DG.policyName]:
        assert (prop, RDF.type, OWL.DatatypeProperty) in dg_graph, (
            f"{prop} must be declared as owl:DatatypeProperty"
        )
