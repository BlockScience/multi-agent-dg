"""Pydantic node models for the discourse-graph package.

# NAMESPACE STUB: replace with firm-controlled IRI before production use.

These are the primary user-facing API. A user who only ever touches this
module and ``DiscourseGraph.add()`` / ``add_edge()`` has a complete,
verified, provenance-aware discourse graph without writing a line of RDF,
Turtle, SHACL, or SPARQL.

Terminology note
----------------
``to_triples()`` produces RDF triples that ``DiscourseGraph.add()`` writes to
the store.  ``dg:created`` is intentionally absent from ``to_triples()`` —
it is stamped by ``DiscourseGraph.add()`` at write time, not by the model.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from rdflib import RDF, RDFS, XSD, Literal as RDFLiteral, URIRef
from rdflib.namespace import PROV

from discourse_graph.namespaces import DG, ENG


# ── Base model ────────────────────────────────────────────────────────────────


class DiscourseNode(BaseModel):
    """Base model for all discourse graph nodes.

    Corresponds to ``dg:DiscourseNode`` in the OWL ontology.

    Parameters
    ----------
    content : str
        Body text of the node (maps to ``dg:content``). Must be non-empty.
    label : str
        Short human-readable identifier (maps to ``rdfs:label``). Must be
        non-empty.
    """

    content: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)

    def to_triples(self, uri: URIRef) -> list[tuple]:
        """Return RDF triples representing this node.

        Parameters
        ----------
        uri : URIRef
            The subject URI for the node.

        Returns
        -------
        list[tuple]
            List of ``(subject, predicate, object)`` triples suitable for
            insertion into an ``rdflib.Graph``.  Does not include
            ``dg:created`` — that is stamped by ``DiscourseGraph.add()``.
        """
        rdf_type = NODE_TYPE_MAP[type(self)]
        return [
            (uri, RDF.type, rdf_type),
            (uri, RDF.type, DG.DiscourseNode),
            (uri, RDF.type, PROV.Entity),
            (uri, DG.content, RDFLiteral(self.content, datatype=XSD.string)),
            (uri, RDFS.label, RDFLiteral(self.label, datatype=XSD.string)),
        ]


# ── Base-grammar node types ───────────────────────────────────────────────────


class Question(DiscourseNode):
    """``dg:Question`` — an open design or research question.

    Base grammar node type: QUE.
    """


class Claim(DiscourseNode):
    """``dg:Claim`` — a proposed answer or interpretive assertion.

    Base grammar node type: CLM.
    """


class Evidence(DiscourseNode):
    """``dg:Evidence`` — an empirical or analytical result.

    Base grammar node type: EVD.  Must be connected to at least one other node
    via ``dg:supports``, ``dg:opposes``, or ``dg:informs`` (enforced by SHACL
    shape ES-2 at verification time, not at construction time).
    """


class Source(DiscourseNode):
    """``dg:Source`` — a document, model, or dataset.

    Represents grounded termination of an evidence chain: the chain ends at an
    external artifact whose provenance lies outside this graph.
    """


# ── Engineering extension node types ─────────────────────────────────────────


class Decision(DiscourseNode):
    """``eng:Decision`` — a committed engineering choice that resolves a design question.

    A Decision is only meaningful when connected via ``eng:decision`` (to the
    Question it resolves) and ``eng:justification`` (to supporting Claims,
    Evidence, Assumptions, or Sources).  SHACL shape DS-1 enforces these edge
    requirements at verification time.

    Parameters
    ----------
    status : {"provisional", "final", "superseded"}
        Lifecycle stage of the decision.

        * ``provisional`` — working assumption, may be revised.
        * ``final`` — committed; requires change control to revise.
        * ``superseded`` — replaced by a newer Decision node.
    """

    status: Literal["provisional", "final", "superseded"] = "provisional"

    def to_triples(self, uri: URIRef) -> list[tuple]:
        """Return RDF triples representing this Decision node.

        Parameters
        ----------
        uri : URIRef
            The subject URI for the node.

        Returns
        -------
        list[tuple]
            Triples include ``eng:decisionStatus`` in addition to the common
            node triples.  Does not include ``dg:created``.
        """
        return [
            (uri, RDF.type, ENG.Decision),
            (uri, RDF.type, DG.DiscourseNode),
            (uri, RDF.type, PROV.Entity),
            (uri, DG.content, RDFLiteral(self.content, datatype=XSD.string)),
            (uri, RDFS.label, RDFLiteral(self.label, datatype=XSD.string)),
            (uri, ENG.decisionStatus, RDFLiteral(self.status, datatype=XSD.string)),
        ]


class Assumption(Claim):
    """``eng:Assumption`` — a Claim accepted without requiring further Evidence.

    An Assumption IS a Claim (Python subclass mirrors OWL subclass).  The
    subclass signals bounded termination of the evidence chain: recursive
    Evidence is not demanded; the chain ends here by scope declaration rather
    than by grounding in external literature.

    Contrast with ``dg:Source`` (grounded termination: chain ends at external
    evidence).  Both are justified stopping points; Assumption is explicitly
    bounded by the declared scope.

    The ``prov:wasDerivedFrom`` edge is added by the caller after construction
    when the Assumption is derived from an ingested node.

    Parameters
    ----------
    scope : str
        The analysis scope within which this assumption is accepted, e.g.
        ``"lunar transfer stage Phase A trade study"``.  Maps to
        ``eng:assumptionScope``.
    """

    scope: str = Field(..., min_length=1)

    def to_triples(self, uri: URIRef) -> list[tuple]:
        """Return RDF triples representing this Assumption node.

        Parameters
        ----------
        uri : URIRef
            The subject URI for the node.

        Returns
        -------
        list[tuple]
            Explicitly includes ``rdf:type eng:Assumption``, ``rdf:type dg:Claim``,
            and ``rdf:type dg:DiscourseNode`` so that SHACL shapes CS-1 (via
            subclass targeting) and AS-1 both apply without requiring RDFS
            inference on the stored triples.  Also includes ``eng:assumptionScope``.
        """
        return [
            (uri, RDF.type, ENG.Assumption),
            (uri, RDF.type, DG.Claim),        # explicit — CS-1 targets dg:Claim
            (uri, RDF.type, DG.DiscourseNode),
            (uri, RDF.type, PROV.Entity),
            (uri, DG.content, RDFLiteral(self.content, datatype=XSD.string)),
            (uri, RDFS.label, RDFLiteral(self.label, datatype=XSD.string)),
            (uri, ENG.assumptionScope, RDFLiteral(self.scope, datatype=XSD.string)),
        ]


# ── OWL class mapping ─────────────────────────────────────────────────────────

#: Maps each Pydantic node class to its corresponding OWL class URI.
#: Must be defined after all six classes to avoid forward-reference NameError.
NODE_TYPE_MAP: dict[type[DiscourseNode], URIRef] = {
    Question: DG.Question,
    Claim: DG.Claim,
    Evidence: DG.Evidence,
    Source: DG.Source,
    Decision: ENG.Decision,
    Assumption: ENG.Assumption,  # subclass of dg:Claim in OWL; subclass of Claim in Python
}
