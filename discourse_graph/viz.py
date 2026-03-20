"""Visualization helpers for DiscourseGraph instances.

# NAMESPACE STUB: replace with firm-controlled IRI before production use.

Provides two public functions:

- :func:`visualize_graph` — render a single DiscourseGraph as a directed
  node-edge diagram with typed node colours and ingested-node borders.
- :func:`visualize_sharing` — side-by-side figure comparing two graphs after
  a sharing event, with prov:wasDerivedFrom edges rendered in the receiver's
  panel.

All rendering is built on top of the private helper
:func:`_build_discourse_graph_nx`, which uses only the public DiscourseGraph
query API (:meth:`~discourse_graph.graph.DiscourseGraph.nodes`,
:meth:`~discourse_graph.graph.DiscourseGraph.node_data`,
:meth:`~discourse_graph.graph.DiscourseGraph.discourse_edges`).

The one exception is :func:`visualize_sharing`, which accesses
``bob_dg._store`` directly to retrieve ``prov:wasDerivedFrom`` triples — these
are not discourse predicates, so they are invisible to ``discourse_edges()``.
This access is documented inline.
"""
from __future__ import annotations

from typing import Optional

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
from rdflib import URIRef
from rdflib.namespace import PROV

from discourse_graph.graph import DiscourseGraph
from discourse_graph.namespaces import DG, ENG

# NAMESPACE STUB: replace with firm-controlled IRI before production use.

# ── FR-VIZ-2 node colour map ──────────────────────────────────────────────────
# Priority order matters: ENG.Assumption is checked before DG.Claim because
# Assumption.to_triples() writes *both* rdf:type ENG.Assumption and DG.Claim.
_COLOR_PRIORITY: list[tuple[URIRef, str]] = [
    (ENG.Assumption, "sandybrown"),
    (ENG.Decision,   "mediumpurple"),
    (DG.Question,    "steelblue"),
    (DG.Claim,       "seagreen"),
    (DG.Evidence,    "goldenrod"),
    (DG.Source,      "slategray"),
]
_DEFAULT_NODE_COLOR = "lightgray"

# Ingested node border style (FR-VIZ-2)
_INGESTED_EDGE_COLOR = "darkorange"
_INGESTED_LINE_WIDTH = 2.5

# Default node border
_DEFAULT_EDGE_COLOR = "#333333"
_DEFAULT_LINE_WIDTH = 1.0

# Node size and font
_NODE_SIZE = 1_800
_LABEL_FONT_SIZE = 8
_EDGE_LABEL_FONT_SIZE = 7


def _pred_label(pred_uri: URIRef) -> str:
    """Extract the local name from a predicate URI for edge labelling."""
    s = str(pred_uri)
    fragment = s.rsplit("#", 1)
    if len(fragment) == 2:
        return fragment[1]
    return s.rsplit("/", 1)[-1]


def _build_discourse_graph_nx(
    dg: DiscourseGraph,
    graph_uri: Optional[URIRef] = None,
    seed: int = 42,
) -> tuple[nx.DiGraph, dict, dict, dict, set]:
    """Build a networkx DiGraph from *dg* using only the public query API.

    Parameters
    ----------
    dg :
        The discourse graph to render.
    graph_uri :
        When given, restrict to a single named graph context.

    Returns
    -------
    tuple
        ``(G, pos, label_map, color_map, ingested_set)`` where

        - *G* — networkx DiGraph with node URIs as vertex IDs
        - *pos* — spring-layout position dict (seed=42 for reproducibility)
        - *label_map* — ``{uri: rdfs:label}`` for node labels
        - *color_map* — ``{uri: color_string}`` per FR-VIZ-2
        - *ingested_set* — set of URIRefs flagged as dg:IngestedNode
    """
    # ── 1. Collect all DiscourseNode URIs ─────────────────────────────────────
    all_nodes = dg.nodes(graph_uri=graph_uri)

    # ── 2. Build type-aware colour map (priority order prevents Assumption
    #       being coloured as Claim due to subclass triple overlap) ─────────────
    type_sets: dict[URIRef, set[URIRef]] = {
        t: set(dg.nodes(type_uri=t, graph_uri=graph_uri))
        for t, _ in _COLOR_PRIORITY
    }

    def _node_color(uri: URIRef) -> str:
        for type_uri, color in _COLOR_PRIORITY:
            if uri in type_sets[type_uri]:
                return color
        return _DEFAULT_NODE_COLOR

    color_map: dict[URIRef, str] = {uri: _node_color(uri) for uri in all_nodes}

    # ── 3. Collect per-node metadata (label, is_ingested) ────────────────────
    label_map: dict[URIRef, str] = {}
    ingested_set: set[URIRef] = set()

    for uri in all_nodes:
        data = dg.node_data(uri)
        label = data.get("label") or str(uri).rsplit("/", 1)[-1]
        label_map[uri] = label
        if data.get("is_ingested"):
            ingested_set.add(uri)

    # ── 4. Build networkx DiGraph from discourse edges ────────────────────────
    G: nx.DiGraph = nx.DiGraph()
    G.add_nodes_from(all_nodes)

    edge_label_map: dict[tuple, str] = {}
    for s, p, o in dg.discourse_edges(graph_uri=graph_uri):
        # Include nodes that appear only as edge endpoints (e.g. cross-agent refs)
        if s not in G:
            G.add_node(s)
            label_map[s] = str(s).rsplit("/", 1)[-1]
            color_map[s] = _DEFAULT_NODE_COLOR
        if o not in G:
            G.add_node(o)
            label_map[o] = str(o).rsplit("/", 1)[-1]
            color_map[o] = _DEFAULT_NODE_COLOR
        G.add_edge(s, o, predicate=p)
        # For multi-edges between the same pair, last predicate wins in label
        edge_label_map[(s, o)] = _pred_label(p)

    # ── 5. Layout ─────────────────────────────────────────────────────────────
    if len(G.nodes) > 0:
        pos = nx.spring_layout(G, seed=seed, k=2.0)
    else:
        pos = {}

    return G, pos, label_map, color_map, ingested_set


# ── Public functions ───────────────────────────────────────────────────────────


def visualize_graph(
    dg: DiscourseGraph,
    ax: Optional[matplotlib.axes.Axes] = None,
    title: Optional[str] = None,
    graph_uri: Optional[URIRef] = None,
    _seed: int = 42,
) -> matplotlib.axes.Axes:
    """Render *dg* as a directed node-edge diagram.

    Parameters
    ----------
    dg :
        The discourse graph to render.
    ax :
        Matplotlib Axes to draw into.  When ``None``, a new figure is created
        and the axes is returned.
    title :
        Panel title.  Defaults to ``dg._agent.name``.
    graph_uri :
        When given, render only triples from that named graph context.

    Returns
    -------
    matplotlib.axes.Axes
        The axes the diagram was drawn into.

    Notes
    -----
    Ingested nodes (``dg:IngestedNode``) are drawn with a darkorange dashed
    border (linewidth 2.5) per FR-VIZ-2.  Regular nodes use a thin dark border.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 7))

    G, pos, label_map, color_map, ingested_set = _build_discourse_graph_nx(dg, graph_uri, seed=_seed)

    if len(G.nodes) == 0:
        ax.set_title(title or dg._agent.name)
        ax.axis("off")
        return ax

    regular_nodes = [n for n in G.nodes if n not in ingested_set]
    ingested_nodes = [n for n in G.nodes if n in ingested_set]

    # ── Pass 1: regular nodes ─────────────────────────────────────────────────
    if regular_nodes:
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=regular_nodes,
            node_color=[color_map[n] for n in regular_nodes],
            node_size=_NODE_SIZE,
            edgecolors=_DEFAULT_EDGE_COLOR,
            linewidths=_DEFAULT_LINE_WIDTH,
            ax=ax,
        )

    # ── Pass 2: ingested nodes (orange solid border, then set dashed) ─────────
    if ingested_nodes:
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=ingested_nodes,
            node_color=[color_map[n] for n in ingested_nodes],
            node_size=_NODE_SIZE,
            edgecolors=_INGESTED_EDGE_COLOR,
            linewidths=_INGESTED_LINE_WIDTH,
            ax=ax,
        )
        # Set dashed linestyle on the most-recently drawn PathCollection
        ax.collections[-1].set_linestyle("dashed")

    # ── Edges ─────────────────────────────────────────────────────────────────
    nx.draw_networkx_edges(
        G, pos,
        arrows=True,
        arrowsize=18,
        connectionstyle="arc3,rad=0.1",
        ax=ax,
    )

    # ── Edge labels ───────────────────────────────────────────────────────────
    edge_labels = {
        (s, o): _pred_label(d["predicate"])
        for s, o, d in G.edges(data=True)
    }
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=edge_labels,
        font_size=_EDGE_LABEL_FONT_SIZE,
        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75),
        ax=ax,
    )

    # ── Node labels ───────────────────────────────────────────────────────────
    nx.draw_networkx_labels(
        G, pos,
        labels=label_map,
        font_size=_LABEL_FONT_SIZE,
        ax=ax,
    )

    ax.set_title(title or dg._agent.name, fontsize=11)
    ax.axis("off")
    return ax


def visualize_sharing(
    alice_dg: DiscourseGraph,
    bob_dg: DiscourseGraph,
    shared_node_uris: list[URIRef],
) -> matplotlib.figure.Figure:
    """Render Alice's and Bob's graphs side-by-side after a sharing event.

    Parameters
    ----------
    alice_dg :
        The sharing agent's graph (left panel).
    bob_dg :
        The receiving agent's graph (right panel).  Ingested nodes are shown
        with a dashed orange border.  ``prov:wasDerivedFrom`` edges (e.g.
        Assumption → shared Claim) are rendered as dashed gray arrows.
    shared_node_uris :
        URIs of nodes that were shared (used in the figure caption; the
        ingested border on Bob's panel is derived from ``dg:IngestedNode``
        type, not from this list).

    Returns
    -------
    matplotlib.figure.Figure
        The composed figure.

    Notes
    -----
    This function accesses ``bob_dg._store`` directly to retrieve
    ``prov:wasDerivedFrom`` triples, which are not discourse predicates and
    are therefore invisible to :meth:`~discourse_graph.graph.DiscourseGraph.discourse_edges`.
    """
    import matplotlib.lines as _mlines
    from matplotlib.patches import ConnectionPatch as _CP

    fig, (ax_alice, ax_bob) = plt.subplots(1, 2, figsize=(18, 8))

    visualize_graph(
        alice_dg,
        ax=ax_alice,
        title=f"{alice_dg._agent.name} — post-sharing",
    )

    visualize_graph(
        bob_dg,
        ax=ax_bob,
        title=f"{bob_dg._agent.name} — post-sharing",
        _seed=94,
    )

    # ── Vertical instance-boundary divider ────────────────────────────────────
    _divider = _mlines.Line2D(
        [0.5, 0.5], [0.04, 0.96],
        transform=fig.transFigure,
        color="lightgray",
        linewidth=1.5,
        linestyle=(0, (8, 4)),
        zorder=0,
    )
    fig.add_artist(_divider)
    fig.text(0.497, 0.97, "instance boundary", ha="right", va="bottom",
             fontsize=7, color="lightgray", transform=fig.transFigure)

    # ── Cross-panel provenance arrows (shared node in Alice → ingested in Bob) ─
    # Seeds match the panels drawn above (bob uses seed=94 for A1 placement).
    _, alice_pos, _, _, alice_ingested = _build_discourse_graph_nx(alice_dg)
    _, bob_pos, _, _, bob_ingested = _build_discourse_graph_nx(bob_dg, seed=94)

    # Alice-originated nodes shared to Bob (Alice panel → Bob panel)
    for _node in bob_ingested:
        if _node in alice_pos and _node in bob_pos:
            _conn = _CP(
                xyA=alice_pos[_node], xyB=bob_pos[_node],
                coordsA="data", coordsB="data",
                axesA=ax_alice, axesB=ax_bob,
                color="silver", linestyle="dashed",
                lw=1.2, arrowstyle="-|>", mutation_scale=12,
                zorder=1,
            )
            fig.add_artist(_conn)

    # Bob-originated nodes shared to Alice (Bob panel → Alice panel)
    for _node in alice_ingested:
        if _node in bob_pos and _node in alice_pos:
            _conn = _CP(
                xyA=bob_pos[_node], xyB=alice_pos[_node],
                coordsA="data", coordsB="data",
                axesA=ax_bob, axesB=ax_alice,
                color="silver", linestyle="dashed",
                lw=1.2, arrowstyle="-|>", mutation_scale=12,
                zorder=1,
            )
            fig.add_artist(_conn)

    # ── Overlay prov:wasDerivedFrom edges on Bob's panel ─────────────────────
    # These are PROV edges, not discourse predicates, so discourse_edges() does
    # not include them.  Direct _store access is required here.

    prov_edges = list(bob_dg._store.triples((None, PROV.wasDerivedFrom, None)))
    for subj, _, obj in prov_edges:
        if subj not in bob_pos or obj not in bob_pos:
            continue
        sx, sy = bob_pos[subj]
        ox, oy = bob_pos[obj]
        ax_bob.annotate(
            "",
            xy=(ox, oy),
            xytext=(sx, sy),
            arrowprops=dict(
                arrowstyle="->",
                color="gray",
                linestyle="dashed",
                lw=1.5,
                connectionstyle="arc3,rad=0.15",
            ),
        )
        # Label midpoint
        mx, my = (sx + ox) / 2, (sy + oy) / 2
        ax_bob.text(
            mx, my, "wasDerivedFrom",
            fontsize=6, color="gray", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7),
        )

    fig.suptitle(
        f"{alice_dg._agent.name} ↔ {bob_dg._agent.name} — policy-bounded sharing",
        fontsize=13,
        y=1.01,
    )
    plt.tight_layout()
    return fig
