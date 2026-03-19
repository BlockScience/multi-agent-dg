"""``eng:`` ontology — engineering design rationale extension over ``dg:``.

# NAMESPACE STUB: replace with firm-controlled IRI before production use.
"""
from __future__ import annotations

import rdflib
from rdflib import Graph

# NAMESPACE STUB: replace with firm-controlled IRI before production use.
ENG_ONTOLOGY_TTL: str = """\
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dg:   <http://example.org/dg/1.0/> .
@prefix eng:  <http://example.org/eng/1.0/> .

<http://example.org/eng/1.0/>
    a owl:Ontology ;
    owl:imports <http://example.org/dg/1.0/> ;
    rdfs:label "Engineering Design Rationale Extension" ;
    rdfs:comment \"\"\"
        Extends dg: with Decision nodes and engineering-closure relations.
        Use when discourse graph participants must record committed design choices.
        Namespace stub: replace with firm-controlled IRI before production.
    \"\"\" ;
    owl:versionInfo "1.0.0" .

# ── Node class ────────────────────────────────────────────────────────────────

eng:Decision a owl:Class ;
    rdfs:subClassOf dg:DiscourseNode ;
    rdfs:subClassOf prov:Entity ;
    rdfs:label "Decision" ;
    rdfs:comment \"\"\"
        A concrete, committed engineering choice that resolves a design question.
        Distinct from dg:Claim (an assertion) in that it carries status and
        records the moment of commitment.
        Status values: provisional | final | superseded
    \"\"\" .

# ── Status vocabulary ─────────────────────────────────────────────────────────

eng:decisionStatus a owl:DatatypeProperty ;
    rdfs:domain eng:Decision ;
    rdfs:range  xsd:string ;
    rdfs:label  "decision status" ;
    rdfs:comment "One of: provisional, final, superseded." .

# ── Relations ─────────────────────────────────────────────────────────────────

eng:decision a owl:ObjectProperty ;
    rdfs:domain eng:Decision ;
    rdfs:range  dg:Question ;
    rdfs:label  "decision" ;
    rdfs:comment \"\"\"
        eng:Decision eng:decision dg:Question
        A decision resolves (closes) a design question.
        Replaces the non-conformant dg:answers predicate.
        SHACL shape OP-1 enforces that eng:opens and eng:decision
        on the same Decision node never target the same Question.
    \"\"\" .

eng:opens a owl:ObjectProperty ;
    rdfs:domain eng:Decision ;
    rdfs:range  dg:Question ;
    rdfs:label  "opens" ;
    rdfs:comment \"\"\"
        eng:Decision eng:opens dg:Question
        A decision opens a downstream design question.
        Committing to a choice typically surfaces new questions
        that must be resolved in subsequent engineering work.
        Must target a DIFFERENT Question than eng:decision on the
        same Decision node (enforced by SHACL shape OP-1).
    \"\"\" .

eng:justification a owl:ObjectProperty ;
    rdfs:domain eng:Decision ;
    rdfs:range  dg:DiscourseNode ;
    rdfs:label  "justification" ;
    rdfs:comment \"\"\"
        eng:Decision eng:justification dg:Claim | dg:Evidence |
                                       eng:Assumption | dg:Source
        A decision is grounded in claims, evidence, assumptions,
        or source documents.
        Range is dg:DiscourseNode to permit all node types as object.
        Replaces the non-conformant dg:cites predicate.
    \"\"\" .

# ── Assumption class ──────────────────────────────────────────────────────────

eng:Assumption a owl:Class ;
    rdfs:subClassOf dg:Claim ;
    rdfs:label "Assumption" ;
    rdfs:comment \"\"\"
        A proposition accepted without requiring further Evidence within
        the declared analysis scope. Subclass of dg:Claim — an Assumption
        IS a Claim; it signals that recursive Evidence is not demanded here.

        Termination semantics:
          dg:Source    → grounded termination (external literature/data)
          eng:Assumption → bounded termination (accepted by scope declaration)

        SPARQL NOTE: queries for dg:Claim will match Assumptions via
        subclass inference. Filter with FILTER NOT EXISTS { ?x a eng:Assumption }
        when only non-assumption Claims are intended.
    \"\"\" .

# ── Assumption datatype property ──────────────────────────────────────────────

eng:assumptionScope a owl:DatatypeProperty ;
    rdfs:domain eng:Assumption ;
    rdfs:range  xsd:string ;
    rdfs:label  "assumption scope" ;
    rdfs:comment \"\"\"
        Declares the analysis scope within which this assumption is accepted.
        Example: "lunar transfer stage Phase A trade study".
        Mandatory (enforced by SHACL shape AS-1).
    \"\"\" .
"""


def load_eng_ontology() -> rdflib.Graph:
    """Load the ``eng:`` ontology from the bundled Turtle constant.

    Returns
    -------
    rdflib.Graph
        Parsed OWL 2 DL ontology for the ``eng:`` namespace. Contains only
        ``eng:`` triples. The ``owl:imports`` triple is stored as data but
        rdflib does **not** automatically fetch or merge the imported ``dg:``
        ontology. To obtain the combined ontology use
        :func:`discourse_graph.namespaces.load_combined_ontology`.

        Each call returns a fresh :class:`rdflib.Graph` instance.
    """
    g = Graph()
    g.parse(data=ENG_ONTOLOGY_TTL, format="turtle")
    return g
