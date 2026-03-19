"""Agent dataclass for the discourse-graph package.

# NAMESPACE STUB: replace with firm-controlled IRI before production use.

An Agent represents an aggregate actor — an organisation, team, or working
group — that owns a single ``DiscourseGraph`` instance.  That instance is a
locally consistent subgraph of a larger distributed graph that no single agent
possesses in full.  The ``name`` field should identify the owning group (e.g.
``"AliceGroup"``, ``"PropulsionTeam"``), not an individual person.

In a multi-agent model, each participating group holds its own ``Agent`` /
``DiscourseGraph`` pair.  Sharing is mediated by policy: one group's graph is
never directly merged into another's; it is exported under an explicit sharing
policy and ingested into the recipient's named-graph store with provenance
triples that record the origin.
"""
from __future__ import annotations

from dataclasses import dataclass

from rdflib import URIRef


@dataclass
class Agent:
    """Aggregate actor that owns a ``DiscourseGraph`` instance.

    An Agent is an organisation, team, or working group — the collective
    actor responsible for maintaining a locally consistent subgraph.  It is
    not an individual person.

    Parameters
    ----------
    name : str
        Human-readable identifier for the group, e.g. ``"AliceGroup"`` or
        ``"PropulsionTeam"``.
    namespace : str
        Base IRI for all URIs minted by this agent.  **Must end with** ``"/"``.
        Example: ``"http://example.org/alice/"``

    Notes
    -----
    URI scheme (all derived deterministically from ``namespace``):

    * Agent:   ``<namespace>agent``
    * Node:    ``<namespace>node/<local_id>``
    * Graph:   ``<namespace>graph/<name>``
    * Policy:  ``<namespace>policy/<name>``
    """

    name: str
    namespace: str

    def __post_init__(self) -> None:
        if not self.namespace.endswith("/"):
            raise ValueError(
                f"Agent namespace must end with '/': {self.namespace!r}"
            )

    @property
    def uri(self) -> URIRef:
        """URI identifying this agent: ``<namespace>agent``."""
        return URIRef(self.namespace + "agent")

    def node_uri(self, local_id: str) -> URIRef:
        """URI for a node owned by this agent: ``<namespace>node/<local_id>``.

        Parameters
        ----------
        local_id : str
            A short, URL-safe identifier for the node, e.g. ``"q1"`` or
            ``"decision-biprop"``.
        """
        return URIRef(self.namespace + "node/" + local_id)

    def graph_uri(self, name: str = "local") -> URIRef:
        """URI for a named graph owned by this agent: ``<namespace>graph/<name>``.

        Parameters
        ----------
        name : str
            Graph name.  Defaults to ``"local"`` for the agent's own graph.
            Use ``"ingested-<slug>"`` for graphs containing data received from
            another agent.
        """
        return URIRef(self.namespace + "graph/" + name)

    def policy_uri(self, name: str) -> URIRef:
        """URI for a sharing policy declared by this agent: ``<namespace>policy/<name>``.

        Parameters
        ----------
        name : str
            Policy name, e.g. ``"evidence-sharing"`` or ``"arch-claim"``.
        """
        return URIRef(self.namespace + "policy/" + name)
