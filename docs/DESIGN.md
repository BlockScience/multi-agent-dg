# Design — Discourse Graph Package

## 1. Ontologies

### 1a. `dg:` ontology (discourse_graph/ontology_dg.py)

Strict implementation of the discoursegraphs.com base grammar.
**No predicates may be added here that are not in the base grammar.**
Stored as `DG_ONTOLOGY_TTL` constant; loaded via `load_dg_ontology() -> rdflib.Graph`.

```turtle
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dg:   <http://example.org/dg/1.0/> .

<http://example.org/dg/1.0/>
    a owl:Ontology ;
    rdfs:label "Discourse Graph Ontology — conformant implementation" ;
    rdfs:comment """
        Implements the discoursegraphs.com base grammar as OWL 2 DL.
        Canonical spec: https://discoursegraphs.com/docs/roam/base-grammar
        Namespace stub: replace with firm-controlled IRI before production.
    """ ;
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
```

### 1b. `eng:` ontology (discourse_graph/ontology_eng.py)

Domain extension for systems engineering design rationale.
Adds `eng:Decision` and two relations not present in the base grammar.
Imports `dg:` ontology.
Stored as `ENG_ONTOLOGY_TTL` constant; loaded via `load_eng_ontology() -> rdflib.Graph`.

```turtle
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
    rdfs:comment """
        Extends dg: with Decision nodes and engineering-closure relations.
        Use when discourse graph participants must record committed design choices.
        Namespace stub: replace with firm-controlled IRI before production.
    """ ;
    owl:versionInfo "1.0.0" .

# ── Node class ────────────────────────────────────────────────────────────────

eng:Decision a owl:Class ;
    rdfs:subClassOf dg:DiscourseNode ;
    rdfs:subClassOf prov:Entity ;
    rdfs:label "Decision" ;
    rdfs:comment """
        A concrete, committed engineering choice that resolves a design question.
        Distinct from dg:Claim (an assertion) in that it carries status and
        records the moment of commitment.
        Status values: provisional | final | superseded
    """ .

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
    rdfs:comment """
        eng:Decision eng:decision dg:Question
        A decision resolves (closes) a design question.
        Replaces the non-conformant dg:answers predicate.
        SHACL shape OP-1 enforces that eng:opens and eng:decision
        on the same Decision node never target the same Question.
    """ .

eng:opens a owl:ObjectProperty ;
    rdfs:domain eng:Decision ;
    rdfs:range  dg:Question ;
    rdfs:label  "opens" ;
    rdfs:comment """
        eng:Decision eng:opens dg:Question
        A decision opens a downstream design question.
        Committing to a choice typically surfaces new questions
        that must be resolved in subsequent engineering work.
        Must target a DIFFERENT Question than eng:decision on the
        same Decision node (enforced by SHACL shape OP-1).
    """ .

eng:justification a owl:ObjectProperty ;
    rdfs:domain eng:Decision ;
    rdfs:range  dg:DiscourseNode ;
    rdfs:label  "justification" ;
    rdfs:comment """
        eng:Decision eng:justification dg:Claim | dg:Evidence |
                                       eng:Assumption | dg:Source
        A decision is grounded in claims, evidence, assumptions,
        or source documents.
        Range is dg:DiscourseNode to permit all node types as object.
        Replaces the non-conformant dg:cites predicate.
    """ .

# ── Assumption class ──────────────────────────────────────────────────────────

eng:Assumption a owl:Class ;
    rdfs:subClassOf dg:Claim ;
    rdfs:label "Assumption" ;
    rdfs:comment """
        A proposition accepted without requiring further Evidence within
        the declared analysis scope. Subclass of dg:Claim — an Assumption
        IS a Claim; it signals that recursive Evidence is not demanded here.

        Termination semantics:
          dg:Source    → grounded termination (external literature/data)
          eng:Assumption → bounded termination (accepted by scope declaration)

        SPARQL NOTE: queries for dg:Claim will match Assumptions via
        subclass inference. Filter with FILTER NOT EXISTS { ?x a eng:Assumption }
        when only non-assumption Claims are intended.
    """ .

# ── Assumption datatype property ──────────────────────────────────────────────

eng:assumptionScope a owl:DatatypeProperty ;
    rdfs:domain eng:Assumption ;
    rdfs:range  xsd:string ;
    rdfs:label  "assumption scope" ;
    rdfs:comment """
        Declares the analysis scope within which this assumption is accepted.
        Example: "lunar transfer stage Phase A trade study".
        Mandatory (enforced by SHACL shape AS-1).
    """ .
```

### 1c. Combined load function (discourse_graph/namespaces.py)

```python
from rdflib import Namespace

DG  = Namespace("http://example.org/dg/1.0/")
ENG = Namespace("http://example.org/eng/1.0/")

def load_combined_ontology() -> rdflib.Graph:
    """Load dg: and eng: ontologies merged into one Graph for pyshacl."""
```

### 1d. The seam — design note for implementors

`dg:Question` is the **only term referenced by both ontologies**. It is the
range of `eng:decision` in `ontology_eng.py` and a base-grammar class in
`ontology_dg.py`. No other cross-namespace term references exist.

When writing code that handles node types or predicate dispatch, the rule is:

- If a concept belongs to the *open discourse* (posing questions, making
  claims, citing evidence) → it goes in `dg:` or is proposed to the
  discoursegraphs.com team as a base grammar extension.
- If a concept belongs to *engineering closure* (committing a choice,
  recording status, grounding a decision) → it goes in `eng:`.
- `dg:Question` is the bridge: it is *posed* in `dg:` discourse and
  *resolved* in `eng:` engineering action. It is never duplicated or
  subclassed in `eng:`.

In `graph.py`, `_VALID_NODE_TYPES` and `_DISCOURSE_PREDICATES` MUST include
both `dg:` and `eng:` terms. The `DiscourseGraph` class is namespace-agnostic
with respect to which ontology a node or predicate comes from — it validates
against the combined ontology and shapes graph.

---

## 2. SHACL shapes (discourse_graph/shapes.py)

All shapes for both `dg:` and `eng:` in one file.
Stored as `SHACL_TTL`; loaded via `load_shapes() -> rdflib.Graph`.

**Shape inventory:**

| Shape | Req ID | Target class | Key constraints |
|---|---|---|---|
| `dg:QuestionShape` | QS-1 | `dg:Question` | content ×1, label ×1 |
| `dg:ClaimShape` | CS-1 | `dg:Claim` | content ×1, label ×1 |
| `dg:EvidenceShape` | ES-1 | `dg:Evidence` | content ×1, label ×1 |
| `dg:EvidenceRelationShape` | ES-2 | `dg:Evidence` | supports OR opposes OR informs ≥1 |
| `dg:SourceShape` | SS-1 | `dg:Source` | content ×1, label ×1 |
| `dg:IngestedNodeShape` | IS-1 | `dg:IngestedNode` | wasAttributedTo ≥1, ingestedAt ≥1 |
| `eng:DecisionShape` | DS-1 | `eng:Decision` | content ×1, label ×1, decision ≥1, justification ≥1, decisionStatus ×1 |
| `eng:AssumptionShape` | AS-1 | `eng:Assumption` | content ×1, label ×1, assumptionScope ×1 |
| `eng:OpensDisjointShape` | OP-1 | `eng:Decision` | SHACL-SPARQL: eng:opens and eng:decision must not target same Question |

Note on CS-1 and AS-1: `eng:Assumption` is a subclass of `dg:Claim` so
`dg:ClaimShape` (CS-1) already applies to Assumptions via SHACL's
`sh:targetClass` subclass inheritance. `eng:AssumptionShape` (AS-1) is
additive — it enforces the `assumptionScope` property which Claims do
not carry.

```turtle
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
# The CLM↔QUE relationship is captured via eng:Decision eng:decision dg:Question.
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
dg:EvidenceRelationShape a sh:NodeShape ;
    sh:targetClass dg:Evidence ;
    sh:message "ES-2: Evidence must support, oppose, or inform at least one node." ;
    sh:or (
        [ sh:property [ sh:path dg:supports ; sh:minCount 1 ] ]
        [ sh:property [ sh:path dg:opposes  ; sh:minCount 1 ] ]
        [ sh:property [ sh:path dg:informs  ; sh:minCount 1 ] ]
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
        sh:in ( "provisional" "final" "superseded" ) ;
        sh:message "DS-1: Decision must have decisionStatus of provisional, final, or superseded."
    ] .

# AS-1 ────────────────────────────────────────────────────────────────────────
# eng:Assumption is a subclass of dg:Claim, so CS-1 already applies via
# SHACL subclass inheritance. AS-1 is additive: enforces assumptionScope.
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
        sh:select """
            SELECT $this ?question
            WHERE {
                $this eng:decision ?question .
                $this eng:opens   ?question .
            }
        """ ;
    ] .
```

---

## 3. Pydantic node models (discourse_graph/models.py)

These are the **primary user-facing API**. A user who only ever touches
this file and `DiscourseGraph.add()` / `add_edge()` has a complete,
validated, provenance-aware discourse graph without writing a line of
RDF, Turtle, SHACL, or SPARQL.

```python
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field

class DiscourseNode(BaseModel):
    """
    Base model for all discourse graph nodes.
    Corresponds to dg:DiscourseNode in the OWL ontology.

    Fields
    ------
    content : the body text of the node (maps to dg:content)
    label   : short human-readable identifier (maps to rdfs:label)
    """
    content: str = Field(..., min_length=1)
    label:   str = Field(..., min_length=1)

class Question(DiscourseNode):
    """dg:Question — an open design or research question. (base grammar: QUE)"""

class Claim(DiscourseNode):
    """dg:Claim — a proposed answer or interpretive assertion. (base grammar: CLM)"""

class Evidence(DiscourseNode):
    """dg:Evidence — an empirical or analytical result. (base grammar: EVD)"""

class Source(DiscourseNode):
    """dg:Source — a document, model, or dataset."""

class Decision(DiscourseNode):
    """
    eng:Decision — a committed engineering choice that resolves a design question.

    Fields
    ------
    status  : lifecycle stage of the decision
              'provisional' — working assumption, may be revised
              'final'       — committed, requires change control to revise
              'superseded'  — replaced by a newer Decision node
    """
    status: Literal["provisional", "final", "superseded"] = "provisional"

class Assumption(Claim):
    """
    eng:Assumption — a Claim accepted without requiring further Evidence
    within a declared analysis scope.

    Subclass of dg:Claim — an Assumption IS a Claim. The subclass signals
    that recursive Evidence is not demanded; the chain terminates here by
    scope declaration rather than by grounding in external literature.

    Contrast with dg:Source (grounded termination: chain ends at external
    evidence). Both serve as justified stopping points; Assumption is
    explicitly bounded by the declared scope.

    Fields
    ------
    scope : the analysis scope within which this assumption is accepted,
            e.g. "lunar transfer stage Phase A trade study".
            Maps to eng:assumptionScope (xsd:string).
    """
    scope: str = Field(..., min_length=1)
```

### Type → OWL class mapping

```python
# discourse_graph/models.py
NODE_TYPE_MAP: dict[type[DiscourseNode], URIRef] = {
    Question:   DG.Question,
    Claim:      DG.Claim,
    Evidence:   DG.Evidence,
    Source:     DG.Source,
    Decision:   ENG.Decision,
    Assumption: ENG.Assumption,   # subclass of dg:Claim in OWL;
                                  # subclass of Claim in Python
}
```

### `to_triples(uri)` method

Each model implements `to_triples(uri: URIRef) -> list[tuple]` returning
the RDF triples that `DiscourseGraph.add()` will write. This enables
round-trip testing: construct a model, call `to_triples`, write to a
fresh Graph, validate with SHACL, assert conformance. The Pydantic
validation and the SHACL validation should agree on every valid and
invalid instance.

```python
# Example for Decision
def to_triples(self, uri: URIRef) -> list[tuple]:
    from rdflib import RDF, RDFS, XSD, Literal
    from rdflib.namespace import PROV
    return [
        (uri, RDF.type,           ENG.Decision),
        (uri, RDF.type,           DG.DiscourseNode),
        (uri, RDF.type,           PROV.Entity),
        (uri, DG.content,         Literal(self.content)),
        (uri, RDFS.label,         Literal(self.label)),
        (uri, ENG.decisionStatus, Literal(self.status)),
        # dg:created added by DiscourseGraph.add(), not the model
    ]
```

### `DiscourseGraph.add()` — primary write method

```python
def add(
    self,
    node: DiscourseNode,
    graph_uri: Optional[URIRef] = None,
) -> URIRef:
    """
    Primary user-facing write method.
    Accepts a Pydantic node model; writes RDF triples to the named graph.

    Pydantic validation runs at call time (Python layer).
    SHACL validation runs when verify() is called (graph layer).

    verify_on_write=True additionally runs structural checks
    (type validity, domain/range) at write time — these are the
    subset of constraints checkable without full graph context.

    Returns the URI of the created node.
    """
```

## 4. Agent (discourse_graph/agent.py)

An `Agent` is an **aggregate actor** — an organisation, team, or working group
— that owns a single `DiscourseGraph` instance.  That instance is a locally
consistent subgraph of a larger distributed graph that no single agent
possesses in full.  The `name` field identifies the owning group (e.g.
`"AliceGroup"`, `"PropulsionTeam"`), not an individual person.

```python
@dataclass
class Agent:
    name: str         # owning group e.g. "AliceGroup" — not an individual
    namespace: str    # base IRI, must end with "/"
                      # e.g. "http://example.org/alice/"

    @property
    def uri(self) -> URIRef:
        """<namespace>agent"""

    def node_uri(self, local_id: str) -> URIRef:
        """<namespace>node/<local_id>"""

    def graph_uri(self, name: str = "local") -> URIRef:
        """<namespace>graph/<name>"""

    def policy_uri(self, name: str) -> URIRef:
        """<namespace>policy/<name>"""
```

---

## 5. VerificationReport (discourse_graph/report.py)

SHACL enforces deterministic, machine-checked constraints — that is
*verification*, not validation.  Validation is reserved for assessments that
require human judgement or domain expertise outside the software.

```python
class VerificationReport:
    conforms:      bool
    report_text:   str           # raw pyshacl text output
    results_graph: rdflib.Graph  # sh:ValidationResult nodes

    @property
    def status(self) -> str:
        """'CONFORMS ✓' or 'VIOLATIONS FOUND ✗'"""

    def summary(self) -> str:
        """
        One-line-per-violation string.
        Extracts sh:resultMessage literals from results_graph.
        Prefixed with status line.
        """

    def violation_ids(self) -> list[str]:
        """
        Extract requirement IDs from sh:resultMessage strings.
        Pattern: leading token before ':' e.g. 'CS-1', 'ES-2'.
        """
```

---

## 6. DiscourseGraph (discourse_graph/graph.py)

### 5.1 Constructor

```python
class DiscourseGraph:
    def __init__(
        self,
        agent: Agent,
        ontology: rdflib.Graph,
        shapes: rdflib.Graph,
        verify_on_write: bool = False,
    ) -> None:
```

Internal state initialised:
- `_store = ConjunctiveGraph()` — quad store, never contains `_policy`
- `_policy = Graph()` — private, structurally isolated
- `_local_graph_uri = agent.graph_uri("local")`
- Agent identity triples written to local named graph on construction

### 6.2 Class constants

```python
# All predicates subject to edge-bounding on export
_DISCOURSE_PREDICATES: frozenset[URIRef] = frozenset({
    DG.informs,           # EVD → QUE
    DG.supports,          # EVD → CLM
    DG.opposes,           # EVD → CLM
    ENG.decision,         # Decision → QUE  (resolves)
    ENG.opens,            # Decision → QUE  (opens downstream)
    ENG.justification,    # Decision → CLM | EVD | Assumption | Source
})

# Domain/range table for verify_on_write structural checks
_PRED_DOMAIN_RANGE: dict[URIRef, tuple[URIRef, URIRef]] = {
    DG.informs:          (DG.Evidence,    DG.Question),
    DG.supports:         (DG.Evidence,    DG.Claim),
    DG.opposes:          (DG.Evidence,    DG.Claim),
    ENG.decision:        (ENG.Decision,   DG.Question),
    ENG.opens:           (ENG.Decision,   DG.Question),
    ENG.justification:   (ENG.Decision,   DG.DiscourseNode),  # range is open
}

# All valid node types (used in add_node / add type check)
_VALID_NODE_TYPES: frozenset[URIRef] = frozenset({
    DG.Question,
    DG.Claim,
    DG.Evidence,
    DG.Source,
    ENG.Decision,
    ENG.Assumption,    # subclass of dg:Claim in OWL
})
```

### 5.3 Public write API

```python
def add_node(
    self,
    node_type: URIRef,
    content: str,
    label: str,
    graph_uri: Optional[URIRef] = None,
) -> URIRef:
    """
    Add a discourse node to a named graph (default: local).

    Writes:
      rdf:type <node_type>
      rdf:type dg:DiscourseNode
      rdf:type prov:Entity
      dg:content <content>
      rdfs:label <label>
      dg:created <now>^^xsd:dateTime

    verify_on_write=True: raises ValueError on invalid type, empty content/label.
    Returns: node URI.
    """

def add_edge(
    self,
    subject: URIRef,
    predicate: URIRef,
    obj: URIRef,
    graph_uri: Optional[URIRef] = None,
) -> None:
    """
    Add a typed edge between two discourse nodes.

    verify_on_write=True: validates only predicates in DISCOURSE_PREDICATES
    (domain/range check). Non-discourse predicates (e.g. prov:wasDerivedFrom,
    prov:wasAttributedTo) are always accepted without validation.
    # CHANGE 2026-03-19: clarified that _check_add_edge validates DISCOURSE_PREDICATES only.
    # Non-discourse predicates (prov:*, rdfs:*, etc.) are unconditionally accepted.
    """
```

### 5.4 Validation API

```python
def verify(
    self,
    graph_uri: Optional[URIRef] = None,
) -> VerificationReport:
    """
    Full SHACL shape verification.
    graph_uri=None → union of all named graphs in _store.
    _policy is NEVER included.
    """
```

### 5.5 Policy API

```python
def declare_sharing_policy(
    self,
    name: str,
    grantee_uri: URIRef,
    source_graph_uri: URIRef,
    include_types: Optional[list[URIRef]] = None,
    include_nodes: Optional[list[URIRef]] = None,
    exclude_nodes: Optional[list[URIRef]] = None,
) -> URIRef:
    """
    Store policy as RDF triples in _policy (never in _store).
    Returns policy URI.
    """

def export_policy(
    self,
    policy_name: str,
    grantee_uri: URIRef,
) -> tuple[rdflib.Graph, str]:
    """
    Compile policy to SPARQL, execute against _store, assert invariants.
    Returns (exported_Graph, sparql_string).

    Raises ValueError if grantee_uri does not match declared grantee.
    Raises AssertionError if any of INV-P1, INV-P2, INV-P3 are violated.
    """
```

### 5.6 Ingest API

```python
def ingest(
    self,
    subgraph: rdflib.Graph,
    source_agent_uri: URIRef,
    graph_name: Optional[str] = None,
) -> URIRef:
    """
    Copy subgraph into new named graph, add provenance triples.
    Returns ingested named graph URI.
    """

def pull_from(
    self,
    other: "DiscourseGraph",
    policy_name: str,
) -> tuple[URIRef, str]:
    """
    Bob-side pull: calls other.export_policy(), then self.ingest().
    Returns (ingested_graph_uri, sparql_string).
    """
```

### 5.7 Introspection API

```python
def named_graphs(self) -> list[URIRef]
def triple_count(self, graph_uri: Optional[URIRef] = None) -> int
```

### 5.8 Private helpers (no public contract)

```python
def _slug(label: str, max_len: int = 28) -> str
def _new_node_uri(self, label: str) -> URIRef
def _now(self) -> Literal          # xsd:dateTime
def _get_concrete_type(self, node_uri: URIRef) -> Optional[URIRef]
def _flat_graph(self, graph_uri: Optional[URIRef] = None) -> Graph
def _check_add_node(self, node_type, content, label) -> None
# CHANGE 2026-03-19: added predicate-scope constraint for _check_add_edge.
def _check_add_edge(self, subject, predicate, obj) -> None
    # Only validates predicates in DISCOURSE_PREDICATES; non-discourse predicates are a no-op.
def _compile_policy(self, policy_uri: URIRef) -> tuple[str, frozenset[URIRef]]
```

---

## 7. Visualization (discourse_graph/viz.py)

```python
def visualize_graph(
    dg: DiscourseGraph,
    graph_uri: Optional[URIRef] = None,
    ax: Optional[matplotlib.axes.Axes] = None,
    title: Optional[str] = None,
) -> matplotlib.axes.Axes:
    """
    Render the discourse graph as a networkx DiGraph on matplotlib Axes.

    Node color by rdf:type:
      dg:Question  → steelblue
      dg:Claim     → seagreen
      dg:Evidence  → goldenrod
      dg:Source    → slategray

    Ingested nodes (rdf:type dg:IngestedNode):
      → orange node border (edgecolors='darkorange', linewidths=2.5)

    Edge labels: local name of predicate (e.g. "supports", "answers")
    Layout: networkx.spring_layout with fixed seed for reproducibility
    """

def visualize_sharing(
    alice_dg: DiscourseGraph,
    bob_dg: DiscourseGraph,
    shared_node_uris: list[URIRef],
    fig: Optional[matplotlib.figure.Figure] = None,
) -> matplotlib.figure.Figure:
    """
    Side-by-side figure: Alice's graph (left) and Bob's graph (right).
    Shared nodes highlighted in both panels (red border).
    Figure title: "AliceGroup ↔ BobGroup — policy-bounded sharing"
    """
```

---

## 8. Notebook spec (notebooks/discourse_graph_demo.py)

### Narrative

The notebook tells the story of a **lunar transfer stage propulsion trade
study**. AliceGroup (systems architecture) and BobGroup (propulsion subsystem)
work in parallel. Alice declares **two sharing policies** with different
epistemic characters, demonstrating the contrast between sharing Evidence
(used directly by Bob) and sharing a Claim whose backing evidence is hidden
(promoted by Bob to an explicit `eng:Assumption`).

The two-policy structure makes the epistemological distinction concrete:

- **Policy A — evidence sharing:** Alice shares E1 (delta-V Evidence). Bob
  receives an empirical finding with provenance. He uses it directly as
  Evidence in his own reasoning chain. No type change.

- **Policy B — claim sharing with hidden backing:** Alice shares C1
  (bipropellant Claim) without sharing E1 or E2. Bob receives an assertion
  with no visible justification chain. In Bob's epistemic context this is
  structurally an assumption. Bob explicitly promotes it to `eng:Assumption`,
  recording the scope and the derivation from Alice's Claim via
  `prov:wasDerivedFrom`. The ingested C1 node is not mutated.

Together these two patterns cover the space of trusted cross-agent knowledge
transfer and make the role of `eng:Assumption` semantically clear to the
audience: it is not a weaker Claim — it is an honest epistemic act.

The demo also shows `eng:opens`: Alice's D1 decision explicitly opens Q2
(the thruster configuration question), making the design process traversable
as a directed graph from Q1 through D1 to Q2.

### Cell sequence

| Cell | Act | Title | Content |
|---|---|---|---|
| 0 | — | Header | `mo.md(...)` — title, domain, layer table, two-policy summary |
| 1 | 1 | Imports | `from discourse_graph import ..., DISCOURSE_PREDICATES` — no RDF imports visible |
| 2 | 1 | Ontology | `load_dg_ontology()`, `load_eng_ontology()` — print triple counts |
| 3 | 1 | SHACL shapes | `load_shapes()` — print shape names and req IDs |
| 4 | 1 | Agents | Construct `alice_agent`, `bob_agent` — print namespaces |
| 5 | 1 | DiscourseGraphs | `alice_dg` (verify_on_write=False), `bob_dg` (verify_on_write=True) |
| 6 | 2 | Populate Alice | `add()` × 6, `add_edge()` × 7 — print node URIs and labels |
| 7 | 2 | Validate Alice | `alice_dg.verify()` — print report, assert conforms |
| 8 | 2 | Visualize Alice | `visualize_graph(alice_dg)` — full graph including D1, eng:opens |
| 9 | 2 | Populate Bob | `add()` × 4, `add_edge()` × 3 — print node URIs |
| 10 | 2 | Validate Bob | `bob_dg.verify()` — print report, assert conforms |
| 11 | 2 | Visualize Bob | `visualize_graph(bob_dg)` — pre-sharing state |
| 12 | 3 | Policy A declared | `policy_A_uri = alice_dg.declare_sharing_policy("evidence-sharing", ...)` — print URI; returns `policy_A_uri` |
| 13 | 3 | Policy A RDF | Print `alice_dg._policy` serialised as Turtle — lift the hood |
| 14 | 3 | Policy A SPARQL | `sparql_A, permitted_A = alice_dg._compile_policy(policy_A_uri)` — print SPARQL string; returns `(sparql_A, permitted_A)` |
| 15 | 3 | Policy B declared | `policy_B_uri = alice_dg.declare_sharing_policy("arch-claim", ...)` — print URI; returns `policy_B_uri` |
| 16 | 3 | Policy B RDF | Print updated `alice_dg._policy` Turtle — show second policy added |
| 17 | 3 | Policy B SPARQL | `sparql_B, permitted_B = alice_dg._compile_policy(policy_B_uri)` — print SPARQL string; returns `(sparql_B, permitted_B)` |
| 18 | 4 | Push Policy A | `exported_A, _ = alice_dg.export_policy("evidence-sharing", bob_agent.uri)` |
| 19 | 4 | Bob ingests A | `bob_dg.ingest(exported_A, alice_agent.uri)` — E1 arrives as Evidence |
| 20 | 4 | Bob uses E1 | `e1_ingested = alice_E1` (ingested nodes retain their original URI — no new URI is minted); `bob_dg.add_edge(e1_ingested, DG.informs, bob_Q2)` |
| 21 | 4 | Push Policy B | `exported_B, _ = alice_dg.export_policy("arch-claim", bob_agent.uri)` |
| 22 | 4 | Bob ingests B | `bob_dg.ingest(exported_B, alice_agent.uri)` — C1 arrives, no backing |
| 23 | 4 | Bob promotes C1 | `bob_A1 = bob_dg.add(Assumption(..., scope="Phase A trade study"))` then `bob_dg.add_edge(bob_A1, PROV.wasDerivedFrom, alice_C1)` and `bob_dg.add_edge(bob_A1, PROV.wasAttributedTo, alice_agent.uri)` |
| 24 | 4 | Bob's Decision | `bob_dg.add_edge(bob_D2, ENG.justification, bob_A1)` — grounds D2 in Assumption |
| 25 | 4 | Validate Bob | `bob_dg.verify()` — assert AS-1 and IS-1 both pass |
| 26 | 4 | Invariant check | Print INV-P1/P2/P3 for both exports, labeled clearly |
| 27 | 5 | Visualize sharing | `visualize_sharing(alice_dg, bob_dg, ...)` — side by side |
| 28 | 5 | Summary table | `mo.md(...)` — epistemic status table (see below) |

### Domain content

**AliceGroup (verify_on_write=False)**

| ID | Type | Label | Content | Edges |
|---|---|---|---|---|
| Q1 | `dg:Question` | Q1-PropArch | What propulsion architecture minimises total system mass for the lunar transfer stage? | — |
| C1 | `dg:Claim` | C1-ChemBiprop | Chemical bipropellant (MMH/NTO) is the baseline propulsion architecture. | — |
| C2 | `dg:Claim` | C2-SEPNotViable | Solar electric propulsion is not viable within the 6-day transit schedule constraint. | — |
| E1 | `dg:Evidence` | E1-DeltaV | Delta-V budget analysis: 3.2 km/s total ΔV required for trans-lunar injection plus lunar orbit insertion. | `dg:supports` C1, `dg:informs` Q1 |
| E2 | `dg:Evidence` | E2-Schedule | Schedule constraint analysis: SEP spiral transfer requires >90 days; mission requirement is ≤6 days. | `dg:supports` C2 |
| D1 | `eng:Decision` | D1-SelectBiprop | Select MMH/NTO bipropellant architecture for lunar transfer stage propulsion. | `eng:decision` Q1, `eng:justification` C1, `eng:justification` E1, `eng:opens` Q2\* |

\* `eng:opens` Q2 is added after Q2 exists in AliceGroup's graph. In the demo
Alice adds Q2 as a locally tracked downstream question before declaring
policies, so D1 can record `eng:opens` Q2 at population time. The audience
sees the full design graph in Alice's visualization (cell 8).

**Alice's two sharing policies:**

| Policy name | include_types | include_nodes | exclude_nodes | Permitted set |
|---|---|---|---|---|
| `evidence-sharing` | `[dg:Evidence]` | — | `[E2]` | {E1} |
| `arch-claim` | — | `[C1]` | — | {C1} |

Note: E1 and E2 are excluded from `arch-claim` by not being in the permitted
set (no include_types, only explicit C1). E1's edge `dg:supports C1` is
dropped by the edge-bounding rule because E1 ∉ permitted. Bob receives C1
as a structurally isolated Claim with no visible justification chain.

D1, C2, E2, Q2 are excluded from both policies. Alice has not shared her
architecture decision, her schedule analysis, or her downstream question
with BobGroup.

**BobGroup (verify_on_write=True)**

Initial population — before any sharing:

| ID | Type | Label | Content | Edges |
|---|---|---|---|---|
| Q2 | `dg:Question` | Q2-ThrusterConfig | What thruster configuration meets the 3.2 km/s ΔV requirement? | — |
| C3 | `dg:Claim` | C3-DualEngine | Dual-engine 500N bipropellant configuration meets the ΔV requirement with adequate thrust margin. | — |
| E3 | `dg:Evidence` | E3-SingleEngine | Single-engine configuration yields insufficient thrust margin at 0.85 reliability. | `dg:supports` C3 |
| D2 | `eng:Decision` | D2-DualEngine500N | Select dual 500N bipropellant engines for lunar transfer stage propulsion subsystem. | `eng:decision` Q2, `eng:justification` C3, `eng:justification` E3 |

After Policy A ingest (E1 arrives as Evidence):

| ID | Type | Label | Content | Edges added |
|---|---|---|---|---|
| E1\* | `dg:Evidence`, `dg:IngestedNode` | E1-DeltaV | *(Alice's content, unchanged)* | `dg:informs` Q2 |

Bob adds `dg:informs` E1→Q2 directly — the delta-V finding is an empirical
result; its ontological type does not change on receipt. Bob also adds
`eng:justification` D2→E1 to ground his decision in the ingested evidence.

After Policy B ingest (C1 arrives as Claim with no visible backing):

| ID | Type | Label | Content | Edges added |
|---|---|---|---|---|
| C1\* | `dg:Claim`, `dg:IngestedNode` | C1-ChemBiprop | *(Alice's content, unchanged)* | — |

Bob creates a new local Assumption derived from the ingested C1:

| ID | Type | Label | Content | Edges |
|---|---|---|---|---|
| A1 | `eng:Assumption` | A1-BipropAccepted | Bipropellant architecture accepted from AliceGroup systems architecture analysis. Evidence chain not available in this graph. | *(see note)* |
| — | — | — | scope: "Lunar transfer stage Phase A propulsion subsystem trade study" | — |

> **Note:** `prov:wasDerivedFrom` and `prov:wasAttributedTo` are object properties
> (edges), not Pydantic model fields. They are added via `add_edge()` after `add()`:
> `bob_dg.add_edge(bob_A1, PROV.wasDerivedFrom, alice_C1)` and
> `bob_dg.add_edge(bob_A1, PROV.wasAttributedTo, alice_agent.uri)`.

Bob then adds `eng:justification` D2→A1. D2 is now grounded in:
- C3 (Bob's own Claim)
- E3 (Bob's own Evidence)
- E1\* (Alice's Evidence, used directly)
- A1 (Bob's Assumption derived from Alice's Claim with hidden backing)

### Epistemic status summary table (cell 28)

```
| Node in Bob's graph | Origin | Bob's epistemic status |
|---|---|---|
| Q2 | Bob (local) | Bob's own open question |
| C3 | Bob (local) | Bob's own claim |
| E3 | Bob (local) | Bob's own evidence |
| D2 | Bob (local) | Bob's committed decision |
| E1* | Alice via Policy A | Empirical finding, accepted as-is, provenance traced |
| C1* | Alice via Policy B | Ingested claim, no visible backing — do not use directly |
| A1  | Bob (local, derived) | Explicit acceptance of C1*, scope declared, chain terminated |
```

The key distinction: E1\* is used directly because it is an empirical result
whose type does not depend on its provenance. C1\* is not used directly in
Bob's Decision — A1 is. A1 is Bob's honest record that he is accepting
an assertion from Alice without her evidence chain.

### Key assertions in notebook

```python
# Cell 7: Alice validates before sharing
assert report_alice.conforms, "Alice's graph must conform before sharing"

# Cell 18: Policy A export contains E1 and not E2
assert any(exported_A.triples((alice_E1, None, None))), \
    "Policy A must include E1"
assert not any(exported_A.triples((alice_E2, None, None))), \
    "INV-P1: Policy A must exclude E2"
# Edge E1→C1 absent because C1 not in Policy A permitted set
assert not any(exported_A.triples((alice_E1, DG.supports, alice_C1))), \
    "INV-P2: edge E1→C1 dropped — C1 not in permitted set"

# Cell 21: Policy B export contains C1 and not E1/E2
assert any(exported_B.triples((alice_C1, None, None))), \
    "Policy B must include C1"
assert not any(exported_B.triples((alice_E1, None, None))), \
    "INV-P1: Policy B must not include E1 (not in permitted set)"
assert not any(exported_B.triples((alice_E2, None, None))), \
    "INV-P1: Policy B must not include E2"
# C1 arrives with no dg:supports or dg:informs edges — isolated
assert not any(exported_B.triples((None, DG.supports, alice_C1))), \
    "INV-P2: no incoming evidence edges on C1 in Policy B export"

# Cell 25: Bob's full graph conforms after Assumption promotion
report_bob_post = bob_dg.verify()
assert report_bob_post.conforms, \
    f"Bob post-sharing: {report_bob_post.summary()}"

# Cell 26: INV-P2 both exports — all discourse edges endpoint-bounded
for label, exported, permitted in [
    ("Policy A", exported_A, permitted_A),
    ("Policy B", exported_B, permitted_B),
]:
    for s, p, o in exported:
        if p in DISCOURSE_PREDICATES:
            assert s in permitted, \
                f"{label} INV-P2: edge subject {s} not in permitted set"
            assert o in permitted, \
                f"{label} INV-P2: edge object {o} not in permitted set"

# Cell 26: A1 is a subclass of Claim — isinstance mirrors OWL subclass
assert isinstance(Assumption(
    label="test", content="test", scope="test"), Claim
), "Assumption must be a subclass of Claim in Python"

# Cell 26: eng:opens and eng:decision do not share a target on D1
decision_targets = set(alice_dg._store.objects(alice_D1, ENG.decision))
opens_targets    = set(alice_dg._store.objects(alice_D1, ENG.opens))
assert decision_targets.isdisjoint(opens_targets), \
    "OP-1: eng:opens and eng:decision must not share a Question on D1"
```

### Visualization spec additions

The `visualize_graph` color map must include:

| Type | Color | Border |
|---|---|---|
| `dg:Question` | steelblue | — |
| `dg:Claim` | seagreen | — |
| `dg:Evidence` | goldenrod | — |
| `dg:Source` | slategray | — |
| `eng:Decision` | mediumpurple | — |
| `eng:Assumption` | sandybrown | — |
| `dg:IngestedNode` | *(inherits type color)* | darkorange dashed border, linewidth 2.5 |

In `visualize_sharing`, the side-by-side figure must annotate:
- Nodes in Bob's panel that are `dg:IngestedNode` with a label suffix `*(Alice)`
- A1 in Bob's panel with a label suffix `*(assumed)` and an arrow from A1
  back toward C1\* with label `wasDerivedFrom` in a muted style

---

## 9. Test requirements (tests/)

Each test file maps to requirement IDs.

### test_shacl.py — parametrised

For each shape (QS-1, CS-1, ES-1, ES-2, SS-1, IS-1, DS-1, AS-1, OP-1):
1. **valid fixture**: construct a minimally valid node → `pyshacl.validate` → assert `conforms=True`
2. **invalid fixture**: omit the required property → assert `conforms=False`
3. **message fixture**: check that `sh:resultMessage` contains the requirement ID

Additional AS-1 tests:
- `test_as1_inherits_cs1`: Assumption without content fails CS-1 (subclass inheritance)
- `test_as1_claim_query_includes_assumption`: SPARQL for `dg:Claim` returns Assumption instances

Additional OP-1 tests:
- `test_op1_valid`: Decision with `eng:decision` → Q1 and `eng:opens` → Q2 (distinct) → conforms
- `test_op1_violation`: Decision with both `eng:decision` and `eng:opens` → same Question → violation

### test_policy.py

| Test | Assertion |
|---|---|
| `test_policy_isolation` | `alice._policy is not alice._store` |
| `test_policy_not_in_store` | policy URI absent from all `alice._store` named graphs |
| `test_permitted_set_type` | include_types=[Evidence] → E1 and E2 in permitted before exclude |
| `test_excluded_removed` | exclude_nodes=[E2] → E2 not in permitted |
| `test_excludes_take_precedence` | include_nodes=[E2] and exclude_nodes=[E2] → E2 not in permitted |
| `test_inv_p1` | excluded node absent from exported graph as subject and object |
| `test_inv_p2` | all discourse edges endpoint-bounded in export |
| `test_inv_p3` | `assert alice._policy is not alice._store` holds after export |
| `test_grantee_mismatch` | export with wrong grantee raises ValueError |
| `test_sparql_scoped` | generated SPARQL contains `GRAPH <source_graph_uri>` |
| `test_edge_bounding_evidence` | E1→C1 edge absent from Policy A export (C1 not permitted) |
| `test_edge_bounding_claim` | no incoming Evidence edges on C1 in Policy B export |
| `test_two_policies_independent` | Policy A and Policy B share no permitted nodes |

### test_invariants.py

Directly test INV-P1 through INV-P5 as standalone unit tests,
independent of the demo domain content.

### test_models.py — trusted ingestion pattern

| Test | Assertion |
|---|---|
| `test_assumption_is_claim_subclass` | `isinstance(Assumption(...), Claim)` is True |
| `test_assumption_owl_subclass` | `ENG.Assumption` in ontology subclasses of `DG.Claim` |
| `test_assumption_cs1_inherited` | Assumption without content fails CS-1 via SHACL subclass |
| `test_assumption_as1_scope` | Assumption without scope fails AS-1 |
| `test_assumption_prov_derivation` | `to_triples` includes `prov:wasDerivedFrom` when set |

---

## Change log

| Date | What changed | Why / decision trigger |
|---|---|---|
| 2026-03-19 | Initial document created | Project scaffold — ontology, SHACL, class APIs, notebook spec, domain content established |
| 2026-03-19 | Rename `ValidationReport` → `VerificationReport`; clarify `Agent` as aggregate actor | SHACL is deterministic machine-checked rule enforcement (verification); "validation" reserved for judgement-requiring checks. Agent is an organisation/team owning a locally consistent subgraph, not an individual. |

