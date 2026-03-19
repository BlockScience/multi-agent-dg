"""``dg:`` ontology — conformant implementation of the discoursegraphs.com base grammar.

# NAMESPACE STUB: replace with firm-controlled IRI before production use.
"""
from __future__ import annotations

import rdflib
from rdflib import Graph

# NAMESPACE STUB: replace with firm-controlled IRI before production use.
DG_ONTOLOGY_TTL: str = """\
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dg:   <http://example.org/dg/1.0/> .

<http://example.org/dg/1.0/>
    a owl:Ontology ;
    rdfs:label "Discourse Graph Ontology — conformant implementation" ;
    rdfs:comment \"\"\"
        Implements the discoursegraphs.com base grammar as OWL 2 DL.
        Canonical spec: https://discoursegraphs.com/docs/roam/base-grammar
        Namespace stub: replace with firm-controlled IRI before production.
    \"\"\" ;
    owl:versionInfo "1.0.0" .

# ── Node classes (base grammar: QUE, CLM, EVD, Source) ───────────────────────

dg:DiscourseNode a owl:Class ;
    rdfs:subClassOf prov:Entity ;
    rdfs:label "Discourse Node" ;
    rdfs:comment "Abstract superclass for all base-grammar node types." .

dg:Question a owl:Class ;
    rdfs:subClassOf dg:DiscourseNode ;
    rdfs:label "Question" ;
    rdfs:comment "QUE — an open research or design question." .

dg:Claim a owl:Class ;
    rdfs:subClassOf dg:DiscourseNode ;
    rdfs:label "Claim" ;
    rdfs:comment "CLM — a proposed answer or interpretive assertion." .

dg:Evidence a owl:Class ;
    rdfs:subClassOf dg:DiscourseNode ;
    rdfs:label "Evidence" ;
    rdfs:comment "EVD — an empirical or analytical result." .

dg:Source a owl:Class ;
    rdfs:subClassOf dg:DiscourseNode ;
    rdfs:label "Source" ;
    rdfs:comment "A document, model, or dataset." .

# ── Infrastructure classes ────────────────────────────────────────────────────

dg:Agent a owl:Class ;
    rdfs:subClassOf prov:Agent ;
    rdfs:label "Agent" .

dg:SharingPolicy a owl:Class ;
    rdfs:label "Sharing Policy" .

dg:IngestedNode a owl:Class ;
    rdfs:label "Ingested Node" ;
    rdfs:comment "Role type applied to nodes received from another agent." .

# ── Relations (base grammar: informs, supports, opposes) ─────────────────────

dg:informs a owl:ObjectProperty ;
    rdfs:domain dg:Evidence ;
    rdfs:range  dg:Question ;
    rdfs:label  "informs" ;
    rdfs:comment "EVD informs QUE — base grammar relation." .

dg:supports a owl:ObjectProperty ;
    rdfs:domain dg:Evidence ;
    rdfs:range  dg:Claim ;
    rdfs:label  "supports" ;
    rdfs:comment "EVD supports CLM — base grammar relation." .

dg:opposes a owl:ObjectProperty ;
    rdfs:domain dg:Evidence ;
    rdfs:range  dg:Claim ;
    rdfs:label  "opposes" ;
    rdfs:comment "EVD opposes CLM — base grammar relation." .

# ── Policy properties ─────────────────────────────────────────────────────────

dg:grantee      a owl:ObjectProperty ; rdfs:domain dg:SharingPolicy ; rdfs:range dg:Agent .
dg:sourceGraph  a owl:ObjectProperty ; rdfs:domain dg:SharingPolicy .
dg:includesType a owl:ObjectProperty ; rdfs:domain dg:SharingPolicy .
dg:includesNode a owl:ObjectProperty ; rdfs:domain dg:SharingPolicy .
dg:excludesNode a owl:ObjectProperty ; rdfs:domain dg:SharingPolicy .

# ── Datatype properties ───────────────────────────────────────────────────────

dg:content    a owl:DatatypeProperty ;
    rdfs:domain dg:DiscourseNode ; rdfs:range xsd:string .

dg:created    a owl:DatatypeProperty ;
    rdfs:domain dg:DiscourseNode ; rdfs:range xsd:dateTime .

dg:ingestedAt a owl:DatatypeProperty ;
    rdfs:domain dg:IngestedNode ;  rdfs:range xsd:dateTime .

dg:policyName a owl:DatatypeProperty ;
    rdfs:domain dg:SharingPolicy ; rdfs:range xsd:string .
"""


def load_dg_ontology() -> rdflib.Graph:
    """Load the ``dg:`` ontology from the bundled Turtle constant.

    Returns
    -------
    rdflib.Graph
        Parsed OWL 2 DL ontology for the ``dg:`` namespace. Each call returns a
        fresh :class:`rdflib.Graph` instance; the constant is never mutated.

    Notes
    -----
    rdflib does **not** dereference external IRIs at parse time, satisfying
    NFR-1 (no external HTTP dependencies). The PROV-O prefix is declared
    inline in ``DG_ONTOLOGY_TTL`` so rdflib can resolve ``prov:Entity`` and
    ``prov:Agent`` CURIEs without a network fetch.
    """
    g = Graph()
    g.parse(data=DG_ONTOLOGY_TTL, format="turtle")
    return g
