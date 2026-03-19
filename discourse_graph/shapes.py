"""SHACL shapes for all ``dg:`` and ``eng:`` node types.

This module has **no runtime dependency** on ``ontology_dg`` or
``ontology_eng`` and can be imported and tested independently (NFR-2).
All 10 shapes are encoded in the ``SHACL_TTL`` module-level constant.
"""
from __future__ import annotations

import rdflib
from rdflib import Graph

SHACL_TTL: str = """\
@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dg:   <http://example.org/dg/1.0/> .
@prefix eng:  <http://example.org/eng/1.0/> .

# QS-1 ────────────────────────────────────────────────────────────────────────
dg:QuestionShape a sh:NodeShape ;
    sh:targetClass dg:Question ;
    sh:property [
        sh:path dg:content ; sh:minCount 1 ; sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "QS-1: Question must have exactly one dg:content (xsd:string)."
    ] ;
    sh:property [
        sh:path rdfs:label ; sh:minCount 1 ; sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "QS-1: Question must have exactly one rdfs:label (xsd:string)."
    ] .

# CS-1 ────────────────────────────────────────────────────────────────────────
# Note: no dg:answers constraint — that predicate is not in the base grammar.
# The CLM<->QUE relationship is captured via eng:Decision eng:decision dg:Question.
dg:ClaimShape a sh:NodeShape ;
    sh:targetClass dg:Claim ;
    sh:property [
        sh:path dg:content ; sh:minCount 1 ; sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "CS-1: Claim must have exactly one dg:content (xsd:string)."
    ] ;
    sh:property [
        sh:path rdfs:label ; sh:minCount 1 ; sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "CS-1: Claim must have exactly one rdfs:label (xsd:string)."
    ] .

# ES-1 ────────────────────────────────────────────────────────────────────────
dg:EvidenceShape a sh:NodeShape ;
    sh:targetClass dg:Evidence ;
    sh:property [
        sh:path dg:content ; sh:minCount 1 ; sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "ES-1: Evidence must have exactly one dg:content (xsd:string)."
    ] ;
    sh:property [
        sh:path rdfs:label ; sh:minCount 1 ; sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "ES-1: Evidence must have exactly one rdfs:label (xsd:string)."
    ] .

# ES-2 ────────────────────────────────────────────────────────────────────────
# sh:message on each inner branch so "ES-2" appears in every violation message.
dg:EvidenceRelationShape a sh:NodeShape ;
    sh:targetClass dg:Evidence ;
    sh:or (
        [ sh:property [ sh:path dg:supports ; sh:minCount 1 ;
                        sh:message "ES-2: Evidence must support, oppose, or inform at least one node." ] ]
        [ sh:property [ sh:path dg:opposes  ; sh:minCount 1 ;
                        sh:message "ES-2: Evidence must support, oppose, or inform at least one node." ] ]
        [ sh:property [ sh:path dg:informs  ; sh:minCount 1 ;
                        sh:message "ES-2: Evidence must support, oppose, or inform at least one node." ] ]
    ) .

# SS-1 ────────────────────────────────────────────────────────────────────────
dg:SourceShape a sh:NodeShape ;
    sh:targetClass dg:Source ;
    sh:property [
        sh:path dg:content ; sh:minCount 1 ; sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "SS-1: Source must have exactly one dg:content (xsd:string)."
    ] ;
    sh:property [
        sh:path rdfs:label ; sh:minCount 1 ; sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "SS-1: Source must have exactly one rdfs:label (xsd:string)."
    ] .

# IS-1 ────────────────────────────────────────────────────────────────────────
dg:IngestedNodeShape a sh:NodeShape ;
    sh:targetClass dg:IngestedNode ;
    sh:property [
        sh:path prov:wasAttributedTo ; sh:minCount 1 ;
        sh:message "IS-1: Ingested node must carry prov:wasAttributedTo."
    ] ;
    sh:property [
        sh:path dg:ingestedAt ; sh:minCount 1 ; sh:datatype xsd:dateTime ;
        sh:message "IS-1: Ingested node must carry dg:ingestedAt (xsd:dateTime)."
    ] .

# DS-1 ────────────────────────────────────────────────────────────────────────
eng:DecisionShape a sh:NodeShape ;
    sh:targetClass eng:Decision ;
    sh:property [
        sh:path dg:content ; sh:minCount 1 ; sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "DS-1: Decision must have exactly one dg:content (xsd:string)."
    ] ;
    sh:property [
        sh:path rdfs:label ; sh:minCount 1 ; sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "DS-1: Decision must have exactly one rdfs:label (xsd:string)."
    ] ;
    sh:property [
        sh:path eng:decision ; sh:minCount 1 ;
        sh:class dg:Question ;
        sh:message "DS-1: Decision must resolve at least one dg:Question via eng:decision."
    ] ;
    sh:property [
        sh:path eng:justification ; sh:minCount 1 ;
        sh:class dg:DiscourseNode ;
        sh:message "DS-1: Decision must carry at least one eng:justification (CLM, EVD, Assumption, or Source)."
    ] ;
    sh:property [
        sh:path eng:decisionStatus ; sh:minCount 1 ; sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:in ( "provisional"^^xsd:string "final"^^xsd:string "superseded"^^xsd:string ) ;
        sh:message "DS-1: Decision must have decisionStatus of provisional, final, or superseded."
    ] .

# AS-1 ────────────────────────────────────────────────────────────────────────
# eng:Assumption is a subclass of dg:Claim, so CS-1 already applies via
# SHACL subclass inheritance (requires inference="rdfs" in pyshacl.validate).
# AS-1 is additive: enforces assumptionScope.
eng:AssumptionShape a sh:NodeShape ;
    sh:targetClass eng:Assumption ;
    sh:property [
        sh:path eng:assumptionScope ; sh:minCount 1 ; sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "AS-1: Assumption must declare exactly one eng:assumptionScope."
    ] .

# OP-1 ────────────────────────────────────────────────────────────────────────
# SHACL-SPARQL constraint: eng:opens and eng:decision on the same Decision
# must not target the same Question. A Decision cannot open the same
# Question it resolves.
eng:OpensDisjointShape a sh:NodeShape ;
    sh:targetClass eng:Decision ;
    sh:sparql [
        sh:message "OP-1: eng:opens and eng:decision must not target the same dg:Question." ;
        sh:prefixes [
            sh:declare [
                sh:prefix "eng" ;
                sh:namespace "http://example.org/eng/1.0/"^^xsd:anyURI
            ]
        ] ;
        sh:select \"\"\"
            SELECT $this ?question
            WHERE {
                $this eng:decision ?question .
                $this eng:opens   ?question .
            }
        \"\"\" ;
    ] .
"""


def load_shapes() -> rdflib.Graph:
    """Load all SHACL shapes from the bundled Turtle constant.

    Returns
    -------
    rdflib.Graph
        Parsed SHACL shapes graph covering all 10 shapes (QS-1 through OP-1).
        Suitable for the ``shacl_graph`` argument to :func:`pyshacl.validate`.
        Each call returns a fresh :class:`rdflib.Graph` instance.

    Notes
    -----
    This module has no runtime dependency on ``ontology_dg`` or
    ``ontology_eng`` (NFR-2: shapes are independently testable). When calling
    :func:`pyshacl.validate`, pass ``inference="rdfs"`` and the combined
    ontology as ``ont_graph`` to enable subclass inheritance (required for
    CS-1 to apply to ``eng:Assumption`` and DS-1 to ``eng:Decision``).
    """
    g = Graph()
    g.parse(data=SHACL_TTL, format="turtle")
    return g
