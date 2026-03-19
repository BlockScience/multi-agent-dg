"""Policy constants for the discourse-graph package.

# NAMESPACE STUB: replace with firm-controlled IRI before production use.

This module owns the :data:`DISCOURSE_PREDICATES` frozenset — the seven
predicates that are subject to the edge-bounding rule on policy export —
and the private helper constants used by ``DiscourseGraph._check_add_edge``
and ``DiscourseGraph._compile_policy``.

Keeping these constants in a separate module allows ``test_invariants.py``
to import ``DISCOURSE_PREDICATES`` directly without importing the full
``DiscourseGraph`` class.
"""
from __future__ import annotations

from rdflib import URIRef

from discourse_graph.namespaces import DG, ENG

# NAMESPACE STUB: replace with firm-controlled IRI before production use.

#: The seven discourse predicates subject to the edge-bounding rule on export.
#: A triple ``(s, p, o)`` is exported iff
#: ``s ∈ permitted ∧ (isLiteral(o) ∨ p ∉ DISCOURSE_PREDICATES ∨ o ∈ permitted)``.
DISCOURSE_PREDICATES: frozenset[URIRef] = frozenset({
    DG.informs,         # dg:Evidence → dg:Question
    DG.supports,        # dg:Evidence → dg:Claim
    DG.opposes,         # dg:Evidence → dg:Claim
    ENG.decision,       # eng:Decision → dg:Question
    ENG.opens,          # eng:Decision → dg:Question
    ENG.justification,  # eng:Decision → dg:DiscourseNode (any)
    ENG.option,         # dg:Claim → dg:Question
})

#: Domain / range table for structural validation in ``_check_add_edge``.
#: Keys are discourse predicates; values are ``(expected_domain, expected_range)``
#: OWL class URIs.  Checked when ``verify_on_write=True``.
#:
#: ``ENG.justification`` has range ``DG.DiscourseNode`` (abstract superclass) —
#: any node that carries ``rdf:type dg:DiscourseNode`` satisfies the range.
_PRED_DOMAIN_RANGE: dict[URIRef, tuple[URIRef, URIRef]] = {
    DG.informs:         (DG.Evidence,    DG.Question),
    DG.supports:        (DG.Evidence,    DG.Claim),
    DG.opposes:         (DG.Evidence,    DG.Claim),
    ENG.decision:       (ENG.Decision,   DG.Question),
    ENG.opens:          (ENG.Decision,   DG.Question),
    ENG.justification:  (ENG.Decision,   DG.DiscourseNode),
    ENG.option:         (DG.Claim,       DG.Question),
}

#: All valid OWL class URIs for discourse nodes.  Used by ``_check_add_node``
#: and ``_get_concrete_type`` in ``DiscourseGraph``.
_VALID_NODE_TYPES: frozenset[URIRef] = frozenset({
    DG.Question,
    DG.Claim,
    DG.Evidence,
    DG.Source,
    ENG.Decision,
    ENG.Assumption,
})
