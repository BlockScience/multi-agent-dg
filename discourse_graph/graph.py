"""DiscourseGraph: the primary runtime for the discourse-graph package.

# NAMESPACE STUB: replace with firm-controlled IRI before production use.

INV-P3 architectural principle
-------------------------------
``_policy`` is a structurally isolated ``rdflib.Graph`` instance.  It must
NEVER be passed to ``_store.get_context()``, ``_store.addN()``,
``_store.add()``, or any SPARQL query string.  This isolation IS the policy
enforcement mechanism.  Every site where ``_store`` is written to carries the
comment::

    # INV-P3: _policy never enters _store

SPARQL isolation
----------------
The **only** method that constructs a SPARQL string is ``_compile_policy()``.
No other method, test, or notebook cell may build a SPARQL fragment.

Namespace stub
--------------
The IRIs ``http://example.org/dg/1.0/`` and ``http://example.org/eng/1.0/``
are W3C-example placeholders.  Replace with firm-controlled IRIs before
production use.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Optional

import pyshacl
import rdflib
from rdflib import RDF, RDFS, XSD
from rdflib import Graph, ConjunctiveGraph, URIRef, Literal
from rdflib.namespace import PROV

from discourse_graph.agent import Agent
from discourse_graph.models import DiscourseNode, NODE_TYPE_MAP
from discourse_graph.namespaces import DG, ENG
from discourse_graph.policy import (
    DISCOURSE_PREDICATES,
    _PRED_DOMAIN_RANGE,
    _VALID_NODE_TYPES,
)
from discourse_graph.report import VerificationReport

# NAMESPACE STUB: replace with firm-controlled IRI before production use.


class DiscourseGraph:
    """Runtime container for a single agent's discourse graph.

    Parameters
    ----------
    agent : Agent
        The owning agent whose namespace is used for all minted URIs.
    ontology : rdflib.Graph
        Combined ``dg:`` + ``eng:`` ontology graph (passed to pyshacl as
        ``ont_graph`` for RDFS inference during verification).
    shapes : rdflib.Graph
        SHACL shapes graph (from :func:`discourse_graph.shapes.load_shapes`).
    verify_on_write : bool
        When ``True``, :meth:`add_node` and :meth:`add_edge` perform
        structural checks at write time and raise :exc:`ValueError` on
        violations.  Relational constraints (e.g. ES-2) are always deferred
        to :meth:`verify`.  Defaults to ``False``.

    Notes
    -----
    Internal layout::

        DiscourseGraph
        ├── _store: ConjunctiveGraph        ← ALL queryable data
        │   ├── graph/local                 ← agent's own nodes
        │   └── graph/ingested-{slug}       ← received nodes
        ├── _policy: Graph                  ← STRUCTURALLY ISOLATED
        │   └── dg:SharingPolicy individuals
        ├── _ontology: Graph (read-only)
        └── _shapes: Graph (read-only)
    """

    def __init__(
        self,
        agent: Agent,
        ontology: rdflib.Graph,
        shapes: rdflib.Graph,
        verify_on_write: bool = False,
    ) -> None:
        self._agent = agent
        self._ontology = ontology
        self._shapes = shapes
        self._verify_on_write = verify_on_write

        # INV-P3: _policy never enters _store
        self._store = ConjunctiveGraph()

        # INV-P3: _policy never enters _store
        self._policy = Graph()

        # Write agent identity to local named graph.
        # INV-P3: _policy never enters _store
        local_ctx = self._store.get_context(self._agent.graph_uri("local"))
        local_ctx.add((self._agent.uri, RDF.type, DG.Agent))

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _slug(label: str, max_len: int = 28) -> str:
        """Convert *label* to a URL-safe slug of at most *max_len* chars."""
        slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
        return slug[:max_len]

    def _new_node_uri(self, label: str) -> URIRef:
        """Mint a deterministically-prefixed, UUID-suffixed node URI."""
        return self._agent.node_uri(f"{self._slug(label)}-{uuid.uuid4().hex[:8]}")

    def _now(self) -> Literal:
        """Return the current UTC time as an ``xsd:dateTime`` literal."""
        return Literal(datetime.now(timezone.utc).isoformat(), datatype=XSD.dateTime)

    def _get_concrete_type(self, node_uri: URIRef) -> Optional[URIRef]:
        """Return the first concrete node type found in *_store* for *node_uri*.

        Searches all named graph contexts in ``_store`` for an
        ``rdf:type`` triple whose object is in ``_VALID_NODE_TYPES``.

        Returns ``None`` when no matching type triple is found.
        """
        for _, _, type_uri in self._store.triples((node_uri, RDF.type, None)):
            if type_uri in _VALID_NODE_TYPES:
                return type_uri
        return None

    def _flat_graph(self, graph_uri: Optional[URIRef] = None) -> Graph:
        """Return a flat ``rdflib.Graph`` for pyshacl validation.

        Parameters
        ----------
        graph_uri :
            When given, copy only that named graph context.  When ``None``,
            union all named graph contexts in ``_store``.

        Notes
        -----
        ``_policy`` is **never** included here.

        # INV-P5: _policy never included in verification target
        """
        flat = Graph()
        if graph_uri is not None:
            for triple in self._store.get_context(graph_uri):
                flat.add(triple)
        else:
            empty_uri = URIRef("")
            for ctx in self._store.contexts():
                # Skip the default/empty graph.
                # INV-P5: _policy never included in verification target
                if isinstance(ctx.identifier, URIRef) and ctx.identifier == empty_uri:
                    continue
                for triple in ctx:
                    flat.add(triple)
        return flat

    def _check_add_node(
        self, node_type: URIRef, content: str, label: str
    ) -> None:
        """Raise ``ValueError`` if structural constraints are violated.

        Called when ``verify_on_write=True``.
        """
        if node_type not in _VALID_NODE_TYPES:
            raise ValueError(
                f"Unknown node type: {node_type!r}. "
                f"Must be one of {_VALID_NODE_TYPES}."
            )
        if not content:
            raise ValueError("content must be non-empty.")
        if not label:
            raise ValueError("label must be non-empty.")

    def _check_add_edge(
        self, subject: URIRef, predicate: URIRef, obj: URIRef
    ) -> None:
        """Raise ``ValueError`` if a discourse edge violates domain/range.

        Non-discourse predicates (``prov:*``, ``rdfs:*``, etc.) are
        unconditionally accepted.  Only predicates in
        ``DISCOURSE_PREDICATES`` are validated.

        Called when ``verify_on_write=True``.
        """
        if predicate not in DISCOURSE_PREDICATES:
            # Non-discourse predicate — unconditionally accepted.
            return

        if predicate not in _PRED_DOMAIN_RANGE:
            raise ValueError(f"Unknown discourse predicate: {predicate!r}.")

        expected_domain, expected_range = _PRED_DOMAIN_RANGE[predicate]

        # Domain check: subject must have rdf:type expected_domain in _store.
        subj_type = self._get_concrete_type(subject)
        if subj_type is not None:
            has_domain = any(
                True for _ in self._store.triples((subject, RDF.type, expected_domain))
            )
            if not has_domain:
                raise ValueError(
                    f"Predicate {predicate!r} requires subject of type "
                    f"{expected_domain!r}, but {subject!r} has type {subj_type!r}."
                )

        # Range check.
        obj_type = self._get_concrete_type(obj)
        if obj_type is not None:
            if predicate == ENG.justification:
                # Range is dg:DiscourseNode (abstract) — accept any subclass.
                has_range = any(
                    True for _ in self._store.triples((obj, RDF.type, DG.DiscourseNode))
                )
                if not has_range:
                    raise ValueError(
                        f"Predicate {predicate!r} requires object with "
                        f"rdf:type dg:DiscourseNode, but none found for {obj!r}."
                    )
            else:
                # For all other predicates, check the explicit range type.
                # Note: eng:Assumption satisfies dg:Claim range because
                # Assumption.to_triples() explicitly writes rdf:type dg:Claim.
                has_range = any(
                    True for _ in self._store.triples((obj, RDF.type, expected_range))
                )
                if not has_range:
                    raise ValueError(
                        f"Predicate {predicate!r} requires object of type "
                        f"{expected_range!r}, but {obj!r} has type {obj_type!r}."
                    )

    def _compile_policy(
        self, policy_uri: URIRef
    ) -> tuple[str, frozenset[URIRef]]:
        """Compile a sharing policy into a SPARQL CONSTRUCT string.

        This is the **only method in the codebase** that constructs a SPARQL
        string.  No other method may build, accept, or emit a SPARQL fragment.

        Parameters
        ----------
        policy_uri :
            The ``dg:SharingPolicy`` individual URI to compile.

        Returns
        -------
        tuple[str, frozenset[URIRef]]
            ``(sparql_string, permitted_set)`` where ``sparql_string`` is the
            SPARQL CONSTRUCT query and ``permitted_set`` is the materialised
            frozenset of permitted node URIs.

        Notes
        -----
        Phase 1 (Python): materialise the permitted set::

            permitted = (type_matches ∪ explicit_includes) \ explicit_excludes

        Phase 2 (string): generate the SPARQL CONSTRUCT with ``VALUES ?s``
        for subject scoping and a ``FILTER`` implementing the edge-bounding
        rule (FR-POL-9).
        """
        # ── Phase 1: materialise permitted set ────────────────────────────────
        source_graph_uri = next(self._policy.objects(policy_uri, DG.sourceGraph))
        include_types = list(self._policy.objects(policy_uri, DG.includesType))
        include_nodes = list(self._policy.objects(policy_uri, DG.includesNode))
        exclude_nodes = list(self._policy.objects(policy_uri, DG.excludesNode))

        source_ctx = self._store.get_context(source_graph_uri)
        source_subjects: set[URIRef] = set(source_ctx.subjects())

        # FR-POL-4: type_matches = nodes in source graph with include_types
        type_matches: set[URIRef] = set()
        for t in include_types:
            for s in source_ctx.subjects(RDF.type, t):
                type_matches.add(s)

        # FR-POL-5: explicit_incl: silently drop URIs absent from source graph
        explicit_incl: set[URIRef] = {
            n for n in include_nodes if n in source_subjects
        }

        # FR-POL-6: exclude_nodes has highest precedence
        permitted: frozenset[URIRef] = frozenset(
            (type_matches | explicit_incl) - set(exclude_nodes)
        )

        # ── Phase 2: SPARQL CONSTRUCT generation ──────────────────────────────
        # VALUES ?s uses space-separated URIs; IN() uses comma-separated URIs.
        perm_sorted = sorted(str(u) for u in permitted)
        perm_values = " ".join(f"<{u}>" for u in perm_sorted)
        perm_in = ", ".join(f"<{u}>" for u in perm_sorted)
        disc_not_in = ", ".join(
            f"<{u}>" for u in sorted(str(u) for u in DISCOURSE_PREDICATES)
        )

        # FR-POL-9: edge-bounding rule in FILTER.
        # (s,p,o) exported iff:
        #   s ∈ permitted AND (isLiteral(o) OR p ∉ DISCOURSE_PREDICATES OR o ∈ permitted)
        # The ?o IN () clause is intentionally empty when permitted is empty
        # (SPARQL 1.1 evaluates ?o IN () as false, which is correct behaviour).
        obj_in_clause = f"      || ?o IN ({perm_in})\n" if perm_in else ""

        sparql = (
            "CONSTRUCT { ?s ?p ?o }\n"
            "WHERE {\n"
            f"  GRAPH <{source_graph_uri}> {{\n"
            "    ?s ?p ?o .\n"
            f"    VALUES ?s {{ {perm_values} }}\n"
            "    FILTER (\n"
            "      isLiteral(?o)\n"
            f"      || ?p NOT IN ({disc_not_in})\n"
            f"{obj_in_clause}"
            "    )\n"
            "  }\n"
            "}"
        )

        return sparql, permitted

    # ── Public write methods ───────────────────────────────────────────────────

    def add(
        self,
        node: DiscourseNode,
        graph_uri: Optional[URIRef] = None,
    ) -> URIRef:
        """Add a Pydantic node to the graph (primary write API).

        Parameters
        ----------
        node :
            A :class:`~discourse_graph.models.DiscourseNode` subclass instance.
        graph_uri :
            Named graph to write to.  Defaults to
            ``agent.graph_uri("local")``.

        Returns
        -------
        URIRef
            The minted URI for the new node.

        Notes
        -----
        ``dg:created`` is stamped here, not in ``to_triples()``.  The notebook
        must use ``add()`` exclusively — never ``add_node()``.
        """
        node_type = NODE_TYPE_MAP[type(node)]
        if self._verify_on_write:
            self._check_add_node(node_type, node.content, node.label)

        uri = self._new_node_uri(node.label)
        target = graph_uri or self._agent.graph_uri("local")
        ctx = self._store.get_context(target)  # INV-P3: _policy never enters _store

        for triple in node.to_triples(uri):
            ctx.add(triple)  # INV-P3: _policy never enters _store

        # Stamp dg:created (not included in to_triples())
        ctx.add((uri, DG.created, self._now()))  # INV-P3: _policy never enters _store

        return uri

    def add_node(
        self,
        node_type: URIRef,
        content: str,
        label: str,
        graph_uri: Optional[URIRef] = None,
    ) -> URIRef:
        """Add a node by OWL class URI (secondary write API, for tests/internal use).

        Parameters
        ----------
        node_type :
            OWL class URI, e.g. ``DG.Evidence`` or ``ENG.Decision``.
        content :
            Node body text (``dg:content``).
        label :
            Short human-readable identifier (``rdfs:label``).
        graph_uri :
            Named graph to write to.  Defaults to
            ``agent.graph_uri("local")``.

        Returns
        -------
        URIRef
            The minted URI for the new node.
        """
        if self._verify_on_write:
            self._check_add_node(node_type, content, label)

        uri = self._new_node_uri(label)
        target = graph_uri or self._agent.graph_uri("local")
        ctx = self._store.get_context(target)  # INV-P3: _policy never enters _store

        # FR-DG-8: exactly these 6 triples
        ctx.add((uri, RDF.type, node_type))               # INV-P3: _policy never enters _store
        ctx.add((uri, RDF.type, DG.DiscourseNode))        # INV-P3: _policy never enters _store
        ctx.add((uri, RDF.type, PROV.Entity))             # INV-P3: _policy never enters _store
        ctx.add((uri, DG.content, Literal(content, datatype=XSD.string)))   # INV-P3: _policy never enters _store
        ctx.add((uri, RDFS.label, Literal(label, datatype=XSD.string)))     # INV-P3: _policy never enters _store
        ctx.add((uri, DG.created, self._now()))            # INV-P3: _policy never enters _store

        return uri

    def add_edge(
        self,
        subject: URIRef,
        predicate: URIRef,
        obj: URIRef,
        graph_uri: Optional[URIRef] = None,
    ) -> None:
        """Add a directed edge between two nodes.

        Parameters
        ----------
        subject :
            Source node URI.
        predicate :
            Predicate URI.  May be any URI; only discourse predicates are
            validated when ``verify_on_write=True``.
        obj :
            Target node URI.
        graph_uri :
            Named graph to write to.  Defaults to
            ``agent.graph_uri("local")``.
        """
        if self._verify_on_write:
            self._check_add_edge(subject, predicate, obj)

        target = graph_uri or self._agent.graph_uri("local")
        ctx = self._store.get_context(target)  # INV-P3: _policy never enters _store
        ctx.add((subject, predicate, obj))     # INV-P3: _policy never enters _store

    # ── Public validation method ───────────────────────────────────────────────

    def verify(
        self, graph_uri: Optional[URIRef] = None
    ) -> VerificationReport:
        """Run SHACL shape verification against the store.

        Parameters
        ----------
        graph_uri :
            When given, validate only that named graph.  When ``None``,
            validate all named graphs in ``_store``.

        Returns
        -------
        VerificationReport
            Structured result; ``conforms=True`` iff all shapes pass.

        Notes
        -----
        ``_policy`` is **never** included in the validation target.
        INV-P5: ``_flat_graph()`` explicitly excludes ``_policy``.
        """
        flat = self._flat_graph(graph_uri)  # INV-P5: _policy never included

        conforms, results_graph, report_text = pyshacl.validate(
            flat,
            shacl_graph=self._shapes,
            ont_graph=self._ontology,
            inference="rdfs",
            serialize_report_graph=False,
        )
        return VerificationReport(
            conforms=conforms,
            report_text=report_text,
            results_graph=results_graph,
        )

    # ── Public policy methods ──────────────────────────────────────────────────

    def declare_sharing_policy(
        self,
        name: str,
        grantee_uri: URIRef,
        source_graph_uri: URIRef,
        include_types: Optional[list[URIRef]] = None,
        include_nodes: Optional[list[URIRef]] = None,
        exclude_nodes: Optional[list[URIRef]] = None,
    ) -> URIRef:
        """Declare a named sharing policy.

        Writes policy triples to ``_policy`` only — **never** to ``_store``.

        Parameters
        ----------
        name :
            Policy name, e.g. ``"evidence-sharing"``.
        grantee_uri :
            URI of the agent authorised to call ``export_policy`` with this
            policy.
        source_graph_uri :
            Named graph URI whose nodes are subject to the policy filter.
        include_types :
            OWL class URIs: all nodes of these types in *source_graph_uri*
            are in the type-match set.
        include_nodes :
            Explicit node URIs to add to the permitted set (silently dropped
            if the URI is absent from *source_graph_uri*).
        exclude_nodes :
            Node URIs explicitly excluded; overrides type and include lists.

        Returns
        -------
        URIRef
            The policy URI ``<agent.namespace>policy/<name>``.
        """
        policy_uri = self._agent.policy_uri(name)

        # Write to _policy ONLY — never to _store.
        self._policy.add((policy_uri, RDF.type, DG.SharingPolicy))
        self._policy.add((policy_uri, DG.policyName, Literal(name, datatype=XSD.string)))
        self._policy.add((policy_uri, DG.grantee, grantee_uri))
        self._policy.add((policy_uri, DG.sourceGraph, source_graph_uri))
        self._policy.add((policy_uri, DG.created, self._now()))

        for t in (include_types or []):
            self._policy.add((policy_uri, DG.includesType, t))
        for n in (include_nodes or []):
            self._policy.add((policy_uri, DG.includesNode, n))
        for n in (exclude_nodes or []):
            self._policy.add((policy_uri, DG.excludesNode, n))

        return policy_uri

    def export_policy(
        self,
        policy_name: str,
        grantee_uri: URIRef,
        override: bool = False,
    ) -> tuple[rdflib.Graph, str]:
        """Export a subgraph according to a named sharing policy.

        Parameters
        ----------
        policy_name :
            The ``dg:policyName`` of the policy to compile and execute.
        grantee_uri :
            Must match the ``dg:grantee`` declared in the policy; raises
            :exc:`ValueError` if mismatched.  Ignored when *override* is
            ``True``.
        override :
            When ``True``, bypass the grantee equality check.  Use this
            only as the **policy author** inspecting your own compiled
            artifact — it does **not** disable INV-P1/P2/P3 assertions.
            Defaults to ``False`` (accidental-export guard active).

        Returns
        -------
        tuple[rdflib.Graph, str]
            ``(exported_graph, sparql_string)`` — the exported subgraph and
            the compiled SPARQL CONSTRUCT string (for inspection/logging).

        Raises
        ------
        ValueError
            If *policy_name* is not found or (when ``override=False``)
            *grantee_uri* does not match the declared grantee.
        AssertionError
            If post-conditions INV-P1, INV-P2, or INV-P3 are violated.
        """
        # Find policy URI by name.
        policy_uri: Optional[URIRef] = None
        for s in self._policy.subjects(DG.policyName, Literal(policy_name, datatype=XSD.string)):
            policy_uri = s
            break
        if policy_uri is None:
            raise ValueError(f"Policy {policy_name!r} not found in _policy graph.")

        # FR-POL-10: verify grantee match (bypassed when override=True).
        declared_grantee = next(self._policy.objects(policy_uri, DG.grantee), None)
        if not override and declared_grantee != grantee_uri:
            raise ValueError(
                f"Grantee mismatch: policy declares {declared_grantee!r}, "
                f"caller supplied {grantee_uri!r}."
            )

        # Compile the policy — the only SPARQL generation in the codebase.
        sparql_string, permitted = self._compile_policy(policy_uri)

        # Execute CONSTRUCT against _store.
        # Skip query execution when permitted is empty — rdflib's SPARQL evaluator
        # does not handle empty VALUES clauses reliably (rdflib bug).
        exported = Graph()
        if permitted:
            for triple in self._store.query(sparql_string):
                exported.add(triple)

        # ── Post-condition asserts ────────────────────────────────────────────
        # INV-P3: _policy never enters _store
        assert self._policy is not self._store, (
            "INV-P3: _policy is structurally isolated from _store"
        )

        excluded_uris: set[URIRef] = set(
            self._policy.objects(policy_uri, DG.excludesNode)
        )

        for s, p, o in exported:
            if p in DISCOURSE_PREDICATES:
                # INV-P1: no excluded node as subject or object of discourse edge
                assert s not in excluded_uris, (
                    f"INV-P1: excluded node {s!r} appears as subject of discourse edge."
                )
                if not isinstance(o, Literal):
                    assert o not in excluded_uris, (
                        f"INV-P1: excluded node {o!r} appears as object of discourse edge."
                    )
                # INV-P2: every discourse edge endpoint is in permitted set
                assert s in permitted, (
                    f"INV-P2: discourse edge subject {s!r} not in permitted set."
                )
                if not isinstance(o, Literal):
                    assert o in permitted, (
                        f"INV-P2: discourse edge object {o!r} not in permitted set."
                    )

        return exported, sparql_string

    def ingest(
        self,
        subgraph: rdflib.Graph,
        source_agent_uri: URIRef,
        graph_name: Optional[str] = None,
    ) -> URIRef:
        """Ingest a shared subgraph into this agent's store.

        Parameters
        ----------
        subgraph :
            The exported ``rdflib.Graph`` received from another agent.
        source_agent_uri :
            URI of the sharing agent (used for provenance triples and
            ingested graph name derivation).
        graph_name :
            Optional explicit graph name slug.  When ``None``, derived from
            *source_agent_uri* by taking the path segment before the final
            ``"agent"`` component.

        Returns
        -------
        URIRef
            The new named graph URI containing the ingested triples.
        """
        if graph_name is None:
            # Derive slug: "alice" from ".../alice/agent" per ARCHITECTURE.md
            parts = str(source_agent_uri).split("/")
            if len(parts) >= 2 and parts[-1] == "agent":
                slug = parts[-2]
            else:
                slug = parts[-1]
        else:
            slug = graph_name

        ingested_graph_uri = self._agent.graph_uri(f"ingested-{slug}")
        ctx = self._store.get_context(ingested_graph_uri)  # INV-P3: _policy never enters _store

        # FR-ING-1: copy all triples from subgraph.
        for triple in subgraph:
            ctx.add(triple)  # INV-P3: _policy never enters _store

        # FR-ING-2: for each dg:DiscourseNode, add provenance triples.
        discourse_nodes = {
            s for s, p, o in subgraph
            if p == RDF.type and o == DG.DiscourseNode
        }
        now = self._now()
        for node_uri in discourse_nodes:
            ctx.add((node_uri, RDF.type, DG.IngestedNode))              # INV-P3: _policy never enters _store
            ctx.add((node_uri, PROV.wasAttributedTo, source_agent_uri)) # INV-P3: _policy never enters _store
            ctx.add((node_uri, DG.ingestedAt, now))                     # INV-P3: _policy never enters _store

        return ingested_graph_uri

    def pull_from(
        self,
        other: "DiscourseGraph",
        policy_name: str,
    ) -> tuple[URIRef, str]:
        """Pull a shared subgraph from *other* using a named policy.

        Parameters
        ----------
        other :
            The sharing agent's ``DiscourseGraph``.
        policy_name :
            Name of the policy declared on *other*'s graph.

        Returns
        -------
        tuple[URIRef, str]
            ``(ingested_graph_uri, sparql_string)`` — the ingested named
            graph URI and the compiled SPARQL (for inspection/logging).
        """
        exported, sparql_string = other.export_policy(policy_name, self._agent.uri)
        ingested_uri = self.ingest(exported, other._agent.uri)
        return ingested_uri, sparql_string

    # ── Public introspection methods ───────────────────────────────────────────

    def named_graphs(self) -> list[URIRef]:
        """Return the list of named graph URIs in ``_store``.

        Returns
        -------
        list[URIRef]
            All named graph URIs (excludes the default empty-URI context).
        """
        empty_uri = URIRef("")
        return [
            ctx.identifier
            for ctx in self._store.contexts()
            if isinstance(ctx.identifier, URIRef)
            and ctx.identifier != empty_uri
        ]

    def triple_count(self, graph_uri: Optional[URIRef] = None) -> int:
        """Return the number of triples in ``_store``.

        Parameters
        ----------
        graph_uri :
            When given, return the count for that named graph only.
            When ``None``, return the total count across all named graphs.

        Returns
        -------
        int
            Triple count.
        """
        if graph_uri is not None:
            return len(self._store.get_context(graph_uri))
        return sum(len(ctx) for ctx in self._store.contexts())

    # ── Public query helpers ────────────────────────────────────────────────────

    def nodes(
        self,
        type_uri: Optional[URIRef] = None,
        graph_uri: Optional[URIRef] = None,
    ) -> list[URIRef]:
        """Return all ``dg:DiscourseNode`` subjects, optionally filtered.

        Parameters
        ----------
        type_uri :
            When given, restrict results to nodes that also have
            ``rdf:type <type_uri>`` (e.g. ``DG.Evidence``).
        graph_uri :
            When given, search only within that named graph context.
            When ``None``, search across all contexts in ``_store``.

        Returns
        -------
        list[URIRef]
            Sorted list of node URIs for deterministic output.
        """
        source = (
            self._store.get_context(graph_uri)
            if graph_uri is not None
            else self._store
        )
        result = {s for s, _, _ in source.triples((None, RDF.type, DG.DiscourseNode))}
        if type_uri is not None:
            typed = {s for s, _, _ in source.triples((None, RDF.type, type_uri))}
            result = result & typed
        return sorted(result)

    def node_data(self, node_uri: URIRef) -> dict:
        """Return a plain dict of metadata for a single node.

        Parameters
        ----------
        node_uri :
            URI of the node to inspect.

        Returns
        -------
        dict
            Keys: ``uri``, ``type``, ``content``, ``label``, ``created``,
            ``is_ingested``, ``source_agent``.  Unknown fields are ``None``.
        """
        data: dict = {
            "uri": node_uri,
            "type": self._get_concrete_type(node_uri),
            "content": None,
            "label": None,
            "created": None,
            "is_ingested": False,
            "source_agent": None,
        }
        for _, p, o in self._store.triples((node_uri, None, None)):
            if p == DG.content:
                data["content"] = str(o)
            elif p == RDFS.label:
                data["label"] = str(o)
            elif p == DG.created:
                data["created"] = str(o)
            elif p == RDF.type and o == DG.IngestedNode:
                data["is_ingested"] = True
            elif p == PROV.wasAttributedTo:
                data["source_agent"] = o
        return data

    def discourse_edges(
        self,
        predicate: Optional[URIRef] = None,
        graph_uri: Optional[URIRef] = None,
    ) -> list[tuple[URIRef, URIRef, URIRef]]:
        """Return discourse edges (triples whose predicate is in ``DISCOURSE_PREDICATES``).

        Parameters
        ----------
        predicate :
            When given, restrict to that specific predicate only.
        graph_uri :
            When given, search only within that named graph context.
            When ``None``, search across all contexts in ``_store``.

        Returns
        -------
        list[tuple[URIRef, URIRef, URIRef]]
            Sorted list of ``(subject, predicate, object)`` tuples.
        """
        source = (
            self._store.get_context(graph_uri)
            if graph_uri is not None
            else self._store
        )
        result = [
            (s, p, o)
            for s, p, o in source
            if p in DISCOURSE_PREDICATES
            and (predicate is None or p == predicate)
        ]
        return sorted(result)

    def neighbors(
        self,
        node_uri: URIRef,
        graph_uri: Optional[URIRef] = None,
    ) -> dict:
        """Return the discourse-edge neighborhood of a node.

        Parameters
        ----------
        node_uri :
            URI of the node to inspect.
        graph_uri :
            When given, restrict the edge search to that named graph.

        Returns
        -------
        dict
            ``{"outgoing": [(predicate, object), ...],
               "incoming": [(predicate, subject), ...]}``
            Only discourse predicates are included.
        """
        edges = self.discourse_edges(graph_uri=graph_uri)
        outgoing = [(p, o) for s, p, o in edges if s == node_uri]
        incoming = [(p, s) for s, p, o in edges if o == node_uri]
        return {"outgoing": outgoing, "incoming": incoming}
