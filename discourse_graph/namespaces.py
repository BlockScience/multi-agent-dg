"""Shared RDF namespace objects for the discourse-graph package.

# NAMESPACE STUB: replace with firm-controlled IRI before production use.
"""
from __future__ import annotations

import rdflib
from rdflib import Namespace


# NAMESPACE STUB: replace with firm-controlled IRI before production use.
DG = Namespace("http://example.org/dg/1.0/")

# NAMESPACE STUB: replace with firm-controlled IRI before production use.
ENG = Namespace("http://example.org/eng/1.0/")


def load_combined_ontology() -> rdflib.Graph:
    """Load ``dg:`` and ``eng:`` ontologies merged into one Graph for pyshacl.

    Returns
    -------
    rdflib.Graph
        Union of all triples from both ontologies. Suitable for passing as the
        ``ont_graph`` argument to :func:`pyshacl.validate`. Each call returns a
        fresh :class:`rdflib.Graph` instance.

    Notes
    -----
    Imports are resolved lazily to avoid circular imports at module load time.
    rdflib does **not** automatically follow ``owl:imports`` — the two ontology
    graphs are merged explicitly here.
    """
    # Deferred imports to break the potential circular import chain:
    # namespaces ← ontology_dg ← namespaces
    from discourse_graph.ontology_dg import load_dg_ontology
    from discourse_graph.ontology_eng import load_eng_ontology

    return load_dg_ontology() + load_eng_ontology()
