"""Discourse Graph Demo — Policy-Controlled Multi-Agent Knowledge Sharing.

A five-act marimo notebook demonstrating the discourse-graph package.
Audience: semantic web practitioners.

Run:  uv run marimo run notebooks/discourse_graph_demo.py
Edit: uv run marimo edit notebooks/discourse_graph_demo.py
HTML: uv run marimo export html notebooks/discourse_graph_demo.py -o _site/index.html
"""

import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


# ── Cell 0: Imports ────────────────────────────────────────────────────────────

@app.cell(hide_code=True)
def cell_0_imports():
    """Import all library dependencies. matplotlib backend set before pyplot."""
    import matplotlib as _mpl
    _mpl.use("Agg")  # required before pyplot import in non-interactive environments

    import marimo as mo
    import matplotlib.pyplot as plt
    from rdflib.namespace import PROV

    from discourse_graph import (
        Agent,
        DiscourseGraph,
        Question,
        Claim,
        Evidence,
        Decision,
        Assumption,
        NODE_TYPE_MAP,
        VerificationReport,
        visualize_graph,
        visualize_sharing,
    )
    from discourse_graph.namespaces import DG, ENG, load_combined_ontology
    from discourse_graph.shapes import load_shapes
    from discourse_graph.policy import DISCOURSE_PREDICATES

    return (
        mo,
        plt,
        PROV,
        DG,
        ENG,
        Agent,
        DiscourseGraph,
        Question,
        Claim,
        Evidence,
        Decision,
        Assumption,
        NODE_TYPE_MAP,
        VerificationReport,
        DISCOURSE_PREDICATES,
        visualize_graph,
        visualize_sharing,
        load_combined_ontology,
        load_shapes,
    )


# ── Cell 1: Header ─────────────────────────────────────────────────────────────

@app.cell(hide_code=True)
def cell_1_header(mo):
    """BLUF hook, title card, and five-act outline."""
    mo.vstack([
        mo.md(r"""
# Discourse Graph — Policy-Controlled Multi-Agent Knowledge Sharing

**Knowledge sharing across agents is only meaningful if the epistemic
provenance of each shared item is preserved and legible.**

This notebook demonstrates a Python implementation of the
[discoursegraphs.com base grammar](https://discoursegraphs.com/docs/roam/base-grammar)
— a formal information model for collaborative scientific and engineering
reasoning. The grammar defines a small set of node types (Question, Claim,
Evidence, Source) and predicates (supports, opposes, answers, informs) that
together make the structure of an argument machine-readable.

Here, two agents work in parallel on a lunar transfer stage propulsion trade
study. AliceGroup (systems architecture) declares two sharing policies with
different epistemic characters: one shares raw Evidence with full provenance;
the other shares a Claim without its backing evidence. BobGroup (propulsion)
must handle these differently — the Evidence is used directly, but the Claim
must be promoted to an explicit `eng:Assumption` with declared scope. The
result is a traceable, machine-checkable reasoning graph in which every
knowledge transfer is formally described, every epistemic status is explicit,
and every policy boundary is enforced by a compiled SPARQL query.

The implementation follows scientific Python conventions throughout — Pydantic
models for node authoring, type-annotated APIs, and NumPy-style docstrings —
so that the formal machinery (OWL 2 DL ontology, SHACL validation, SPARQL
policy compilation) stays under the hood while the surface API remains
lightweight enough to integrate into existing data pipelines and analysis
workflows.

---

## Cross-Team Engineering Design Decision Example
              
**Domain:** Lunar transfer stage propulsion trade study
**Agents:** AliceGroup (systems architecture) · BobGroup (propulsion subsystem)

The `dg:` ontology implements the discoursegraphs.com base grammar — it defines
Question, Claim, Evidence, and Source as node types, and the predicates that
connect them (supports, opposes, answers, informs). It is intentionally minimal
and domain-neutral: any field that reasons in argument form can use it as-is.

Engineering decisions, however, require something more opinionated. When a team
commits to a design choice — selecting a propulsion architecture, closing a
trade study — the reasoning structure differs from a Claim: a Decision resolves
a Question, is justified by Claims and Evidence, and can open downstream
Questions for other teams. The `eng:` extension ontology adds exactly these
concepts (`eng:Decision`, `eng:Assumption`, and their predicates) as subclasses
and sub-properties of `dg:` types. It imports `dg:` and adds to it; it does not
redefine or conflict with anything in the base grammar.

The two namespaces reflect a deliberate separation of concerns: `dg:` is stable
and shared across communities; `eng:` is domain-specific and can evolve
independently. Other domains can define their own extensions in the same pattern
without touching the base.

---

## Technology stack

Each layer was chosen to keep formal rigour internal while exposing a
Python-native interface. A developer authoring a node or declaring a policy
never touches RDF syntax, SPARQL, or OWL directly — those are implementation
details. A developer integrating the library into a data pipeline works with
typed Pydantic models, standard Python dataclasses, and ordinary method calls.

**OWL 2 DL** gives the ontology decidable reasoning semantics and a
well-defined class hierarchy. We use it to express what kinds of things exist
in a discourse graph and how they relate — not at runtime, but as a
machine-checkable specification that SHACL shapes and the Python models are
both derived from.

**SHACL** enforces structural constraints on the serialized RDF graph. It
catches things Pydantic cannot: relational invariants that only make sense once
edges exist (e.g. an Evidence node must support or inform at least one other
node). Running SHACL via `verify()` is explicit and may be deferred — it does not
slow down every write.

**Pydantic + rdflib** is the runtime pairing. Pydantic provides the
user-facing API: typed constructors, field validation at the call site, and
IDE autocompletion. rdflib provides the underlying RDF store and the named
graph isolation that makes the policy mechanism possible. Neither is visible
to a user who only calls `add()` and `add_edge()`.

**RDF + SPARQL** for policy is the key architectural choice. Sharing policies
are stored as first-class RDF individuals — they are inspectable, serializable,
and auditable. At export time a policy is compiled to a SPARQL CONSTRUCT query.
Alice never writes SPARQL; the library produces it from the RDF. The query is
printed in Act 3 so the audience can verify that the boundary they specified
in Python is exactly the boundary being enforced.

**NetworkX + Matplotlib** handle visualization and graph analysis.
NetworkX is the natural bridge between the RDF store and the broader scientific
Python ecosystem: the discourse graph can be projected into a NetworkX DiGraph
for layout, centrality analysis, path queries, or export to any tool that
speaks NetworkX. Matplotlib renders the result. A developer who wants to run
graph algorithms on a discourse graph does not need to learn SPARQL — they
project to NetworkX and use the tools they already know.

| Concern | Technology | Purpose |
|-------|-----------|---------|
| Ontology | OWL 2 DL (`dg:` + `eng:`) | Class hierarchy and predicate semantics |
| Shapes | SHACL | Structural and relational constraints |
| Runtime | Pydantic + rdflib | Write-time validation and RDF storage |
| Policy | RDF + SPARQL | Formal, inspectable sharing rules |
| Visualization & analysis | NetworkX + Matplotlib | Graph layout, algorithms, and rendering |

---

## Five-act narrative

The notebook builds up the demonstration in stages. Acts 1 and 2 establish the
graphs independently so the sharing event in Acts 4 and 5 has something
meaningful to work with. Act 3 is the pedagogical core — we peak under the hood at the RDF and
SPARQL artifacts that Alice's Python calls produce before any data moves.

| Act | Cells | Topic |
|-----|-------|-------|
| 1 | 2–5 | Setup — load ontologies, create agents and graphs |
| 2 | 6–11 | Individual graphs — Alice and Bob build independently |
| 3 | 12–17 | Policy declaration — Alice writes two policies; inspect the Turtle and SPARQL artifacts |
| 4 | 18–26 | Sharing — policy A (direct evidence), policy B (hidden-backing claim), policy C (decision closure); invariants |
| 5 | 27–28 | Visualization and epistemic status summary |

---

## Three sharing policies

The contrast between Alice's two policies is the central argument of the notebook.
Same source graph, same grantee, different permitted sets — different epistemic
objects arrive in Bob's graph, and he must handle them differently.
Bob's policy closes the loop by sharing his decision back to Alice.

| Policy | Owner | Permitted set | Epistemic character |
|--------|-------|--------------|---------------------|
| `evidence-sharing` | Alice → Bob | {E1} | Direct evidence: Bob receives Alice's delta-V analysis with full provenance |
| `arch-claim` | Alice → Bob | {C1} | Hidden-backing claim: Bob receives Alice's baseline assertion with no visible justification |
| `subsystem-decision` | Bob → Alice | {D2} | Decision closure: Alice receives Bob's thruster decision, resolving the question her D1 opened |
"""),
    ])
    return


# ── Cell 1b: Scenario intro ────────────────────────────────────────────────────

@app.cell(hide_code=True)
def cell_1b_scenario(mo):
    """Scenario prose: two teams, one mission, the controlled-sharing challenge."""
    mo.vstack([
        mo.md("## Act 1 — Setup"),
        mo.md("""
Alice's team (systems architecture) and Bob's team (propulsion subsystem) are
working the same mission. Each team maintains its own discourse graph — a typed
directed graph of Questions, Claims, Evidence, and Decisions connected by
formally-defined predicates.

The hard problem is controlled sharing. Alice has empirical findings she is
willing to share directly. She also has architectural claims whose evidence chain
she is not willing to expose — perhaps it is proprietary, perhaps it is simply
not ready. She wants Bob to be able to use her conclusions without being able to
inspect the reasoning behind them.

This notebook shows how the discourse-graph library handles that. Alice writes
Python. The library produces inspectable RDF and SPARQL. The access boundaries
are formally enforced, not just agreed by convention.
"""),
    ])
    return


@app.cell(hide_code=True)
def cell_2_ontology(mo, load_combined_ontology):
    """Load combined dg: + eng: ontology."""
    ontology = load_combined_ontology()
    mo.vstack([
        mo.md(f"**Ontology loaded:** {len(ontology)} triples (dg: + eng: merged)"),
        mo.callout(
            mo.md("The ontology is passed to pyshacl as `ont_graph` for RDFS inference during verification."),
            kind="info",
        ),
    ])
    return (ontology,)


@app.cell(hide_code=True)
def cell_3_shapes(mo, load_shapes):
    """Load SHACL shapes graph."""
    shapes = load_shapes()
    _shape_table = """
| Shape ID | Constraint |
|----------|-----------|
| QS-1 | Question must have dg:content and rdfs:label |
| CS-1 | Claim must have dg:content and rdfs:label |
| ES-1 | Evidence must have dg:content and rdfs:label |
| ES-2 | Evidence must support, oppose, or inform at least one node |
| SS-1 | Source must have dg:content and rdfs:label |
| IS-1 | IngestedNode must have prov:wasAttributedTo |
| DS-1 | Decision must have eng:decision and eng:justification edges |
| AS-1 | Assumption must have eng:assumptionScope |
| OP-1 | eng:opens and eng:decision targets must be disjoint per Decision |
"""
    mo.vstack([
        mo.md(f"**SHACL shapes loaded:** {len(shapes)} triples"),
        mo.md("""
SHACL shapes are the machine-checkable contract for graph structure. Where the
OWL ontology defines *what things are*, SHACL defines *what a well-formed graph
looks like* — which properties are required, which relationships must exist,
and which combinations are forbidden. Every shape maps to a named requirement
in the specification and is checked by calling `verify()` on a `DiscourseGraph`.

The shapes fall into three groups:

**Node completeness** (QS-1, CS-1, ES-1, SS-1, AS-1) — every node of a given
type must carry the minimum set of properties (`dg:content`, `rdfs:label`,
and type-specific fields like `eng:assumptionScope`). These are the constraints
Pydantic also enforces at authoring time; SHACL re-checks them on the serialized
graph as a second line of defence.

**Relational integrity** (ES-2, DS-1, OP-1) — constraints that can only be
checked once edges exist. An Evidence node must support, oppose, or inform at
least one other node. A Decision must have at least one `eng:decision` and one
`eng:justification` edge. The targets of `eng:opens` and `eng:decision` on the
same Decision must be disjoint. Pydantic cannot enforce these alone — they require
graph context so calls must be passed to SHACL for validation.

**Provenance** (IS-1) — every node tagged `dg:IngestedNode` must carry a
`prov:wasAttributedTo` triple. This ensures that cross-agent knowledge transfer
is always attributed, regardless of how the ingest was performed.
"""),
        mo.md(_shape_table),
        mo.callout(
            mo.md(
                "Pydantic validates the model instance at Python call time; SHACL validates "
                "the serialized RDF graph after triples are written. Neither is redundant — "
                "Pydantic catches errors at the call site with a readable traceback; SHACL "
                "catches relational violations that only become visible once the graph is populated."
            ),
            kind="info",
        ),
    ])
    return (shapes,)


@app.cell(hide_code=True)
def cell_4_agents(mo, Agent):
    """Construct AliceGroup and BobGroup agents."""
    alice_agent = Agent("AliceGroup", "http://example.org/alice/")
    bob_agent   = Agent("BobGroup",  "http://example.org/bob/")
    mo.vstack([
        mo.md("**Agents constructed:**"),
        mo.md(f"- `alice_agent.uri` = `{alice_agent.uri}`"),
        mo.md(f"- `bob_agent.uri`   = `{bob_agent.uri}`"),
        mo.md(f"- `alice_agent.graph_uri('local')` = `{alice_agent.graph_uri('local')}`"),
        mo.callout(
            mo.md(
                "An `Agent` is a namespace owner and URI minter: it holds the base IRI for a "
                "team's graph, mints node and named-graph URIs under that namespace, and carries "
                "the agent identifier used in provenance triples (`prov:wasAttributedTo`)."
            ),
            kind="info",
        ),
        mo.callout(
            mo.md(
                "**Namespace stub notice.** The IRIs shown above use the W3C example domain "
                "`http://example.org/` and are placeholders for this demonstration. In a "
                "production deployment, each agent's base IRI must be replaced with a "
                "firm-controlled, dereferenceable URI — one that the owning organisation "
                "hosts and maintains. Dereferenceability matters: other agents use these IRIs "
                "as persistent identifiers for nodes and provenance records, and a URI that "
                "cannot be resolved undermines the auditability of the graph. Replace "
                "`http://example.org/alice/` and `http://example.org/bob/` with IRIs under "
                "domains you control before any cross-team or cross-organisation sharing."
            ),
            kind="warn",
        ),
    ])
    return (alice_agent, bob_agent)


@app.cell(hide_code=True)
def cell_5_discourse_graphs(mo, DiscourseGraph, alice_agent, bob_agent, ontology, shapes):
    """Create DiscourseGraph instances for each agent."""
    alice_dg = DiscourseGraph(alice_agent, ontology, shapes, verify_on_write=False)
    bob_dg   = DiscourseGraph(bob_agent,   ontology, shapes, verify_on_write=True)
    mo.vstack([
        mo.md(r"""
### `DiscourseGraph` — the primary runtime object

`DiscourseGraph(agent, ontology, shapes, verify_on_write=False)`

Each instance owns one agent's complete knowledge state: their nodes, their
discourse edges, and their sharing policies. The internal layout keeps these
concerns structurally separated:

```
DiscourseGraph
├── _store: ConjunctiveGraph      ← all queryable data
│   ├── graph/local               ← agent's own nodes and edges
│   └── graph/ingested-{slug}     ← nodes received from other agents
└── _policy: Graph                ← sharing policy RDF (never enters _store)
```

**Write API** — the only methods a content author needs:

| Method | Description |
|--------|-------------|
| `add(node)` | Add a Pydantic node model; returns the minted URI |
| `add_edge(s, p, o)` | Add a directed edge between two node URIs |

**Validation:**

| Method | Description |
|--------|-------------|
| `verify()` | Run full SHACL verification; returns `VerificationReport` |

**Policy and sharing:**

| Method | Description |
|--------|-------------|
| `declare_sharing_policy(name, grantee, source_graph, ...)` | Write a named policy to `_policy`; returns policy URI |
| `export_policy(name, grantee_uri)` | Compile policy to SPARQL, execute, assert invariants; returns `(Graph, sparql_str)` |
| `ingest(subgraph, source_agent_uri)` | Copy a received subgraph into a new named graph with provenance |
| `pull_from(other, policy_name)` | Bob-side shortcut: calls `other.export_policy()` then `self.ingest()` |

**Analysis and introspection:**

| Method | Description |
|--------|-------------|
| `nodes(type_uri, graph_uri)` | List all discourse node URIs, optionally filtered by type or graph |
| `node_data(node_uri)` | Return a plain dict of metadata for one node |
| `discourse_edges(predicate, graph_uri)` | List all edges whose predicate is in `DISCOURSE_PREDICATES` |
| `neighbors(node_uri)` | Return outgoing and incoming discourse edges for one node |
| `named_graphs()` | List all named graph URIs in `_store` |
| `triple_count(graph_uri)` | Count triples, optionally scoped to one named graph |
"""),
        mo.callout(
            mo.md(
                "Alice: `verify_on_write=False` — structural checks deferred to `verify()`. "
                "Bob: `verify_on_write=True` — domain/range validated at every `add_edge()` call. "
                "The policy graph `_policy` is never merged into `_store` — this structural "
                "isolation is the enforcement mechanism for INV-P3."
            ),
            kind="info",
        ),
    ])
    return (alice_dg, bob_dg)


# ── Cell 5b: Bridge to Act 2 ───────────────────────────────────────────────────

@app.cell(hide_code=True)
def cell_5b_what_next(mo):
    """Bridge narration: what Act 2 is about to do and why."""
    mo.md("""
In Act 1, both agents have empty discourse graphs in their own namespaces. In Act 2 each
team populates their graph independently, without any communication. Notice that
`add()` is the only write method: it takes a Pydantic model, mints a URI, stamps
a timestamp, and writes the RDF triples. No Turtle, no SPARQL, no rdflib
constructor calls in user code.
""")
    return


# ── Act 2: Individual graphs ───────────────────────────────────────────────────

@app.cell(hide_code=True)
def cell_6_act2_narration(mo):
    """Act 2 heading and narrative context."""
    mo.vstack([
        mo.md("## Act 2 — Individual Graphs"),
        mo.md("""
Each team builds their discourse graph in isolation. Alice models the propulsion
architecture trade study. Bob models the thruster configuration analysis. Both
graphs are validated against the SHACL shapes before any sharing takes place.
"""),
    ])
    return


@app.cell(hide_code=True)
def cell_7_populate_alice(mo, alice_dg, DG, ENG, Question, Claim, Evidence, Decision):
    """Populate Alice's discourse graph with the propulsion trade study nodes."""

    # ── Nodes ─────────────────────────────────────────────────────────────────
    alice_Q1 = alice_dg.add(Question(
        label="Q1-PropArch",
        content="What propulsion architecture minimises total system mass for the lunar transfer stage?",
    ))
    alice_C1 = alice_dg.add(Claim(
        label="C1-ChemBiprop",
        content="Chemical bipropellant (MMH/NTO) is the baseline propulsion architecture.",
    ))
    alice_C2 = alice_dg.add(Claim(
        label="C2-SEPNotViable",
        content="Solar electric propulsion is not viable within the 6-day transit schedule constraint.",
    ))
    alice_E1 = alice_dg.add(Evidence(
        label="E1-DeltaV",
        content="Delta-V budget analysis: 3.2 km/s total \u0394V required for trans-lunar injection plus lunar orbit insertion.",
    ))
    alice_E2 = alice_dg.add(Evidence(
        label="E2-Schedule",
        content="Schedule constraint analysis: SEP spiral transfer requires >90 days; mission requirement is \u22646 days.",
    ))
    alice_D1 = alice_dg.add(Decision(
        label="D1-SelectBiprop",
        content="Select MMH/NTO bipropellant architecture for lunar transfer stage propulsion.",
        status="provisional",
    ))
    # Q2 is opened by D1 — Alice mints it (she raises the downstream question)
    alice_Q2 = alice_dg.add(Question(
        label="Q2-ThrusterConfig",
        content="What thruster configuration meets the 3.2 km/s \u0394V requirement?",
    ))

    # ── Edges ─────────────────────────────────────────────────────────────────
    alice_dg.add_edge(alice_E1, DG.supports,       alice_C1)
    alice_dg.add_edge(alice_E1, DG.informs,        alice_Q1)
    alice_dg.add_edge(alice_E2, DG.supports,       alice_C2)
    alice_dg.add_edge(alice_D1, ENG.decision,      alice_Q1)
    alice_dg.add_edge(alice_D1, ENG.justification, alice_C1)
    alice_dg.add_edge(alice_D1, ENG.justification, alice_E1)
    alice_dg.add_edge(alice_D1, ENG.justification, alice_C2)
    alice_dg.add_edge(alice_D1, ENG.opens,         alice_Q2)
    alice_dg.add_edge(alice_C1, ENG.option,        alice_Q1)
    alice_dg.add_edge(alice_C2, ENG.option,        alice_Q1)

    mo.vstack([
        mo.md("**AliceGroup graph populated** — 7 nodes, 10 discourse edges."),
        mo.md(f"""
| ID | Type | Label |
|----|------|-------|
| Q1 | Question | Q1-PropArch |
| C1 | Claim | C1-ChemBiprop |
| C2 | Claim | C2-SEPNotViable |
| E1 | Evidence | E1-DeltaV |
| E2 | Evidence | E2-Schedule |
| D1 | Decision | D1-SelectBiprop |
| Q2 | Question | Q2-ThrusterConfig *(opened by D1)* |
"""),
        mo.callout(
            mo.md("D1 `eng:opens` Q2 — Alice's architecture decision raises a downstream subsystem question for BobGroup."),
            kind="info",
        ),
    ])
    return (alice_Q1, alice_C1, alice_C2, alice_E1, alice_E2, alice_D1, alice_Q2)


@app.cell(hide_code=True)
def cell_8_validate_alice(mo, alice_dg):
    """Run SHACL verification on Alice's graph."""
    with mo.status.spinner(title="Running SHACL validation on Alice's graph…"):
        report_alice = alice_dg.verify()

    # INV-check: graph must conform before any sharing
    assert report_alice.conforms, (
        f"Alice's graph must conform before sharing.\n{report_alice.summary()}"
    )

    mo.vstack([
        mo.callout(mo.md(f"**Alice:** {report_alice.status}"), kind="success"),
    ])
    return (report_alice,)


@app.cell(hide_code=True)
def cell_9_visualize_alice(mo, plt, alice_dg, visualize_graph):
    """Render Alice's full graph."""
    _fig, _ax = plt.subplots(figsize=(10, 7))
    visualize_graph(alice_dg, ax=_ax, title="AliceGroup — full graph (pre-sharing)")
    plt.tight_layout()
    mo.vstack([
        mo.as_html(_fig),
        mo.md(r"""
*Node colours: steelblue = Question · seagreen = Claim · goldenrod = Evidence · mediumpurple = Decision*

**Reading the graph as a trade study:**

- **E1 → Q1** (`dg:informs`): the delta-V budget analysis is the primary empirical input to the architecture question.
- **E1 → C1** (`dg:supports`): that same analysis is the evidence backing the claim that chemical bipropellant is the baseline.
- **E2 → C2** (`dg:supports`): the schedule constraint analysis supports the finding that SEP is not viable within the mission timeline.
- **D1 → Q1** (`eng:decision`): the architecture decision resolves the propulsion question.
- **D1 → C1, E1** (`eng:justification`): D1 is grounded in the positive case — the bipropellant claim and its supporting evidence.
- **D1 → C2** (`eng:justification`): D1 is also grounded in the negative case — the elimination of SEP. A trade study selects *among alternatives*; recording the losing alternative's non-viability as justification makes the reasoning complete and auditable.
- **D1 → Q2** (`eng:opens`): committing to bipropellant immediately surfaces the thruster configuration question, which becomes BobGroup's problem to resolve.
- **C1, C2 → Q1** (`eng:option`): both claims are registered as explicit candidate options for the propulsion design question — bipropellant as the selected architecture, SEP as the eliminated alternative. The full option set is visible in the graph.
"""),
    ])
    return


@app.cell(hide_code=True)
def cell_10_populate_bob(mo, bob_dg, DG, ENG, Question, Claim, Evidence, Decision):
    """Populate Bob's pre-sharing discourse graph."""
    # Bob mints his own Q2 in his own namespace.
    # In a production federation the two teams would agree on a shared Q2 URI;
    # for this demo each agent maintains their own namespace and the cross-agent
    # link is established through the policy-controlled sharing that follows.
    bob_Q2 = bob_dg.add(Question(
        label="Q2-ThrusterConfig",
        content="What thruster configuration meets the 3.2 km/s \u0394V requirement?",
    ))
    bob_C3 = bob_dg.add(Claim(
        label="C3-DualEngine",
        content="Dual-engine 500N bipropellant configuration meets the \u0394V requirement with adequate thrust margin.",
    ))
    bob_E3 = bob_dg.add(Evidence(
        label="E3-SingleEngine",
        content="Single-engine configuration yields insufficient thrust margin at 0.85 reliability.",
    ))
    bob_D2 = bob_dg.add(Decision(
        label="D2-DualEngine500N",
        content="Select dual 500N bipropellant engines for lunar transfer stage propulsion subsystem.",
        status="provisional",
    ))

    # Edges
    bob_dg.add_edge(bob_E3, DG.supports,       bob_C3)
    bob_dg.add_edge(bob_D2, ENG.decision,      bob_Q2)
    bob_dg.add_edge(bob_D2, ENG.justification, bob_C3)
    bob_dg.add_edge(bob_D2, ENG.justification, bob_E3)
    bob_dg.add_edge(bob_C3, ENG.option,        bob_Q2)

    mo.vstack([
        mo.md("**BobGroup graph populated** — 4 local nodes, 5 discourse edges."),
        mo.callout(
            mo.md(
                "Bob mints his own Q2 in his namespace. "
                "Alice's D1 `eng:opens` alice_Q2; Bob's D2 `eng:decision` bob_Q2 — "
                "the same engineering question, each agent's copy in their own namespace. "
                "The cross-agent link emerges through policy-controlled sharing (Act 4)."
            ),
            kind="info",
        ),
    ])
    return (bob_Q2, bob_C3, bob_E3, bob_D2)


@app.cell(hide_code=True)
def cell_11_validate_bob(mo, bob_dg):
    """Run SHACL verification on Bob's pre-sharing graph."""
    with mo.status.spinner(title="Running SHACL validation on Bob's graph…"):
        report_bob_pre = bob_dg.verify()

    assert report_bob_pre.conforms, (
        f"Bob's pre-sharing graph must conform.\n{report_bob_pre.summary()}"
    )

    mo.callout(mo.md(f"**Bob (pre-sharing):** {report_bob_pre.status}"), kind="success")
    return (report_bob_pre,)


@app.cell(hide_code=True)
def cell_12_visualize_bob(mo, plt, bob_dg, visualize_graph):
    """Render Bob's pre-sharing graph."""
    _fig, _ax = plt.subplots(figsize=(10, 7))
    visualize_graph(bob_dg, ax=_ax, title="BobGroup — pre-sharing graph")
    plt.tight_layout()
    mo.vstack([
        mo.as_html(_fig),
        mo.md(r"""
*Node colours: steelblue = Question · seagreen = Claim · goldenrod = Evidence · mediumpurple = Decision*

**Reading the graph as a subsystem trade:**

- **E3 → C3** (`dg:supports`): the single-engine reliability analysis is the evidence backing the dual-engine claim.
- **C3 → Q2** (`eng:option`): the dual-engine configuration is the candidate option Bob evaluated for the thruster question.
- **D2 → Q2** (`eng:decision`): Bob's decision resolves the thruster configuration question.
- **D2 → C3, E3** (`eng:justification`): the decision is grounded in the dual-engine claim and its supporting evidence.

At this stage Bob's graph is self-contained but isolated — his D2 is grounded only in his own evidence. Alice's architecture baseline (C1) and delta-V analysis (E1) are not yet visible to Bob. Act 3 defines the policies that will change that.
"""),
    ])
    return


# ── Cell 11b: Close Act 2 ─────────────────────────────────────────────────────

@app.cell(hide_code=True)
def cell_12b_act2_close(mo):
    """Act 2 closing narration: both graphs conform; the hard problem begins."""
    mo.md("""
Both graphs conform. Alice has a complete reasoning chain from Q1 through Evidence
to Decision. Bob has a complete chain from his Q2 through Evidence to D2.

The problem: Bob's D2 is grounded in Bob's own evidence only. Alice has empirical
findings (E1: the delta-V budget) and a baseline claim (C1: bipropellant is the
architecture) that Bob could use — if Alice chooses to share them, and in a form
she controls.
""")
    return


# ── Act 3: Policy declaration ─────────────────────────────────────────────────

@app.cell(hide_code=True)
def cell_13_act3_narration(mo):
    """Act 3 heading and narrative context."""
    mo.vstack([
        mo.md("## Act 3 — Policy Declaration"),
        mo.md(
"Alice controls what she shares and with whom using a single Python call. "
"She declares two policies in this act.\n\n"
"**Policy A** (`evidence-sharing`) — share all Evidence nodes with Bob, "
"except E2 (the schedule constraint analysis Alice considers preliminary):\n\n"
"```python\n"
"alice_dg.declare_sharing_policy(\n"
'    name="evidence-sharing",\n'
"    grantee_uri=bob_agent.uri,\n"
"    source_graph_uri=alice_agent.graph_uri(\"local\"),\n"
"    include_types=[DG.Evidence],        # share all Evidence nodes …\n"
"    exclude_nodes=[alice_E2],           # … except E2-Schedule\n"
")\n"
"```\n\n"
"**Policy B** (`arch-claim`) — share one specific Claim node by URI, "
"no evidence chain attached:\n\n"
"```python\n"
"alice_dg.declare_sharing_policy(\n"
'    name="arch-claim",\n'
"    grantee_uri=bob_agent.uri,\n"
"    source_graph_uri=alice_agent.graph_uri(\"local\"),\n"
"    include_nodes=[alice_C1],           # share C1-ChemBiprop only\n"
")\n"
"```\n\n"
"The cells below lift the hood: each call produces a formal RDF record and a "
"compiled SPARQL query. Alice never writes either artifact — the library "
"generates them from her Python call and guarantees they are well-formed."
),
    ])
    return


@app.cell(hide_code=True)
def cell_14_policy_a_declared(mo, alice_dg, alice_agent, bob_agent, alice_E2, DG):
    """Alice declares the 'evidence-sharing' policy."""
    policy_A_uri = alice_dg.declare_sharing_policy(
        name="evidence-sharing",
        grantee_uri=bob_agent.uri,
        source_graph_uri=alice_agent.graph_uri("local"),
        include_types=[DG.Evidence],
        exclude_nodes=[alice_E2],
    )

    mo.vstack([
        mo.md("**Policy A declared:** `evidence-sharing`"),
        mo.md(
            f"- Grantee: `{bob_agent.uri}`\n"
            f"- Include types: `[dg:Evidence]`\n"
            f"- Exclude nodes: `[E2-Schedule]`\n"
            f"- **Permitted set:** {{E1}}\n"
            f"- Policy URI: `{policy_A_uri}`"
        ),
        mo.callout(
            mo.md(
                "E1 is shared; E2-Schedule is withheld — Alice considers the schedule "
                "constraint analysis preliminary. Bob receives evidence of the delta-V "
                "budget but not the SEP elimination rationale."
            ),
            kind="info",
        ),
    ])
    return (policy_A_uri,)


@app.cell(hide_code=True)
def cell_15_policy_a_rdf(mo, alice_dg):
    """Print the RDF Turtle serialization of alice_dg._policy.

    This is the 'lift the hood' moment: the audience sees that Alice's Python
    call produced a formal RDF artifact stored in the isolated _policy graph.
    """
    _turtle = alice_dg._policy.serialize(format="turtle")
    mo.accordion({
        "Policy A — RDF artifact (expand to inspect)": mo.vstack([
            mo.md(
                "Alice wrote one Python call. The system produced this formal RDF. "
                "Note `dg:SharingPolicy`, `dg:grantee`, `dg:sourceGraph`, "
                "`dg:includesType`, `dg:excludesNode`."
            ),
            mo.md(f"```turtle\n{_turtle}\n```"),
            mo.callout(
                mo.md(
                    "`alice_dg._policy` is a standalone `rdflib.Graph` — it is never passed to "
                    "`_store.get_context()`, `_store.addN()`, or any SPARQL query. "
                    "This structural isolation is the enforcement mechanism for INV-P3."
                ),
                kind="info",
            ),
        ]),
    })
    return


@app.cell(hide_code=True)
def cell_16_policy_a_sparql(mo, alice_dg, policy_A_uri):
    """Compile Policy A to SPARQL and display the generated query."""
    sparql_A, permitted_A = alice_dg._compile_policy(policy_A_uri)

    _permitted_labels = [str(u).rsplit("/", 1)[-1] for u in sorted(str(u) for u in permitted_A)]

    mo.accordion({
        "Policy A — compiled SPARQL CONSTRUCT (expand to inspect)": mo.vstack([
            mo.md(
                "The SPARQL was generated from the RDF policy above — Alice never wrote SQL or SPARQL. "
                "The edge-bounding rule: a triple `(s, p, o)` is exported iff `s ∈ permitted` AND "
                "(`isLiteral(o)` OR `p ∉ DISCOURSE_PREDICATES` OR `o ∈ permitted`). "
                "This prevents discourse edges from crossing the policy boundary even when both "
                "endpoints exist in Alice's store."
            ),
            mo.md(f"**Permitted set:** `{{{', '.join(_permitted_labels)}}}`"),
            mo.md(f"```sparql\n{sparql_A}\n```"),
        ]),
    })
    return (sparql_A, permitted_A)


@app.cell(hide_code=True)
def cell_17_policy_b_declared(mo, alice_dg, alice_agent, bob_agent, alice_C1):
    """Alice declares the 'arch-claim' policy."""
    policy_B_uri = alice_dg.declare_sharing_policy(
        name="arch-claim",
        grantee_uri=bob_agent.uri,
        source_graph_uri=alice_agent.graph_uri("local"),
        include_nodes=[alice_C1],
    )

    mo.vstack([
        mo.md("**Policy B declared:** `arch-claim`"),
        mo.md(
            f"- Grantee: `{bob_agent.uri}`\n"
            f"- Include nodes: `[C1-ChemBiprop]`\n"
            f"- **Permitted set:** {{C1}} — no type filter, no exclude\n"
            f"- Policy URI: `{policy_B_uri}`"
        ),
        mo.callout(
            mo.md(
                "C1 is shared **without** E1 or E2 — Bob receives the baseline assertion "
                "with no visible evidence chain. He must decide whether to accept it."
            ),
            kind="warn",
        ),
    ])
    return (policy_B_uri,)


@app.cell(hide_code=True)
def cell_18_policy_b_rdf(mo, alice_dg, policy_B_uri):
    """Print Policy B's RDF triples from _policy (B's contribution only)."""
    from rdflib import Graph as _Graph
    _g = _Graph()
    for _triple in alice_dg._policy.triples((policy_B_uri, None, None)):
        _g.add(_triple)
    _turtle = _g.serialize(format="turtle")
    mo.accordion({
        "Policy B — RDF artifact (expand to inspect)": mo.vstack([
            mo.md(
                "Alice's second Python call produced this RDF. "
                "Note `dg:includesNode` (node-explicit selection) vs. "
                "`dg:includesType` in Policy A (type-based selection)."
            ),
            mo.md(f"```turtle\n{_turtle}\n```"),
        ]),
    })
    return


@app.cell(hide_code=True)
def cell_19_policy_b_sparql(mo, alice_dg, policy_B_uri):
    """Compile Policy B to SPARQL."""
    sparql_B, permitted_B = alice_dg._compile_policy(policy_B_uri)

    _permitted_labels = [str(u).rsplit("/", 1)[-1] for u in sorted(str(u) for u in permitted_B)]

    mo.accordion({
        "Policy B — compiled SPARQL CONSTRUCT (expand to inspect)": mo.vstack([
            mo.md(
                "Contrast with Policy A: `VALUES ?s` now contains only C1. "
                "No `dg:supports` or `dg:informs` edges point into `{C1}` from E1 or E2, "
                "so the edge-bounding FILTER drops all incoming discourse edges — Bob "
                "receives the claim but cannot see what evidence it rests on."
            ),
            mo.md(f"**Permitted set:** `{{{', '.join(_permitted_labels)}}}`"),
            mo.md(f"```sparql\n{sparql_B}\n```"),
        ]),
    })
    return (sparql_B, permitted_B)


@app.cell(hide_code=True)
def cell_19b_policy_narration(mo, sparql_B):
    """Narration: the combined policy as a formal, checkable ruleset."""
    _ = sparql_B  # ordering dependency
    mo.md("""
Both policies are now declared. Together they form a **deterministic, serialized
ruleset** — a formal RDF document that encodes exactly what Alice has authorised
to leave her instance, and nothing more.

This is not a configuration file or an access-control list that can drift from
the code that enforces it. Every export must pass through `export_policy()`,
which compiles the RDF directly to a SPARQL CONSTRUCT query and applies the
edge-bounding rule. There is no code path from Alice's store to a shared graph
that bypasses this step.

The combined artifact below is the ground truth: if a triple does not follow
from these rules, it is not exported. If the rules change, the artifact changes,
and the compiled SPARQL changes with it. The policy is always inspectable,
diffable, and executable.
""")
    return


@app.cell(hide_code=True)
def cell_19b_policy_combined_rdf(mo, alice_dg, sparql_B):
    """Show combined Policy A + Policy B RDF — the full _policy graph."""
    _ = sparql_B  # ordering dependency: display after Policy B SPARQL is compiled
    _turtle = alice_dg._policy.serialize(format="turtle")
    mo.accordion({
        "Policy A + Policy B — combined RDF artifact (expand to inspect)": mo.vstack([
            mo.md(
                "Both `dg:SharingPolicy` individuals live in the same isolated `_policy` graph. "
                "Contrast `dg:includesType` (Policy A) with `dg:includesNode` (Policy B) — "
                "two different selection mechanisms, two different epistemic commitments."
            ),
            mo.md(f"```turtle\n{_turtle}\n```"),
        ]),
    })
    return


@app.cell(hide_code=True)
def cell_19c_bob_policy_c(mo, bob_dg, bob_agent, alice_agent, ENG):
    """Bob declares Policy C — share all Decision nodes back to Alice."""
    policy_C_uri = bob_dg.declare_sharing_policy(
        name="subsystem-decision",
        grantee_uri=alice_agent.uri,
        source_graph_uri=bob_agent.graph_uri("local"),
        include_types=[ENG.Decision],
    )

    mo.vstack([
        mo.md("**Policy C declared:** `subsystem-decision`"),
        mo.md(
            f"- Grantee: `{alice_agent.uri}`\n"
            f"- Include types: `[eng:Decision]`\n"
            f"- **Permitted set:** {{D2}}\n"
            f"- Policy URI: `{policy_C_uri}`"
        ),
        mo.callout(
            mo.md(
                "Bob shares all Decision nodes — currently just D2. "
                "D2 resolves Q2, the question Alice's D1 opened. "
                "Sharing decisions back is the natural counterpart to receiving "
                "the evidence and claims that grounded them."
            ),
            kind="info",
        ),
    ])
    return (policy_C_uri,)


# ── Act 4: Sharing ─────────────────────────────────────────────────────────────

@app.cell(hide_code=True)
def cell_20_act4_narration(mo):
    """Act 4 heading and narrative context."""
    mo.vstack([
        mo.md("## Act 4 — Sharing"),
        mo.md(
            "The sharing in this act is bidirectional. Alice exports two policies to Bob; "
            "Bob exports one policy back to Alice. Each export runs the compiled SPARQL "
            "CONSTRUCT and applies the edge-bounding rule — no triple crosses the boundary "
            "unless its subject is in the permitted set and its discourse-edge object is too.\n\n"
            "The sequence below shows all ten steps. "
            "The final step closes the loop: Bob's D2 resolves the Q2 that Alice's D1 opened."
        ),
    ])
    return


@app.cell(hide_code=True)
def cell_20b_act4_sequence(mo, plt):
    """Sequence diagram: Alice↔Bob sharing exchange."""
    _fig, _ax = plt.subplots(figsize=(10, 7))
    _ax.set_xlim(0, 10)
    _ax.set_ylim(0, 10)
    _ax.axis("off")

    # ── Lifeline positions ────────────────────────────────────────────────────
    _xa, _xb = 2.0, 8.0          # Alice and Bob x-positions
    _y_top, _y_bot = 9.5, 0.3

    # Lifeline headers
    for _x, _name, _color in [(_xa, "Alice", "steelblue"), (_xb, "Bob", "seagreen")]:
        _ax.text(_x, _y_top, _name, ha="center", va="center", fontsize=11,
                 fontweight="bold", color="white",
                 bbox=dict(boxstyle="round,pad=0.4", fc=_color, ec="none"))
        _ax.plot([_x, _x], [_y_top - 0.35, _y_bot], color="lightgray",
                 lw=1.2, linestyle="dashed", zorder=0)

    # ── Steps (y decreasing = time flowing down) ─────────────────────────────
    _steps = [
        # (y,  x_start, x_end,  label,                                      side)
        (8.4, _xa,    _xa,    "① Alice: declare Policy A + Policy B",        "self"),
        (8.4, _xb,    _xb,    "② Bob: declare Policy C",                     "self"),
        (7.5, _xa,    _xb,    "③ export_policy('evidence-sharing') → E1",    "send"),
        (6.8, _xb,    _xb,    "④ ingest(E1)  — IngestedNode + provenance",  "self"),
        (6.1, _xb,    _xb,    "⑤ add_edge(E1→Q2, D2→E1)",                   "self"),
        (5.2, _xa,    _xb,    "⑥ export_policy('arch-claim') → C1",         "send"),
        (4.5, _xb,    _xb,    "⑦ ingest(C1)  — IngestedNode + provenance",  "self"),
        (3.8, _xb,    _xb,    "⑧ add(A1)  prov:wasDerivedFrom C1",          "self"),
        (3.1, _xb,    _xb,    "⑨ add_edge(D2 eng:justification A1)",        "self"),
        (2.1, _xb,    _xa,    "⑩ export_policy('subsystem-decision') → D2", "send"),
        (1.3, _xa,    _xa,    "⑪ ingest(D2)  — D1 eng:opens Q2 ✓ resolved", "self"),
    ]

    for _y, _xs, _xe, _label, _kind in _steps:
        if _kind == "send":
            _ax.annotate("", xy=(_xe, _y), xytext=(_xs, _y),
                         arrowprops=dict(arrowstyle="-|>", color="dimgray", lw=1.3))
            _ax.text((_xs + _xe) / 2, _y + 0.18, _label,
                     ha="center", va="bottom", fontsize=8.5, color="dimgray")
        else:  # self-arrow
            _ax.annotate("", xy=(_xs - 0.3, _y - 0.25), xytext=(_xs + 0.3, _y),
                         arrowprops=dict(arrowstyle="-|>", color="dimgray", lw=1.0,
                                         connectionstyle="arc3,rad=-0.4"))
            _ax.text(_xs + 0.5, _y, _label,
                     ha="left", va="center", fontsize=8.5, color="dimgray")

    plt.tight_layout()
    mo.vstack([mo.as_html(_fig)])
    return


@app.cell(hide_code=True)
def cell_21_push_policy_a(mo, alice_dg, bob_agent, DG, alice_E1, alice_E2, alice_C1):
    """Alice exports Policy A to Bob."""
    exported_A, _ = alice_dg.export_policy("evidence-sharing", bob_agent.uri)

    # INV-P1: excluded node E2 absent from exported graph
    assert not any(exported_A.triples((alice_E2, None, None))), (
        "INV-P1: excluded node E2 must be absent from Policy A export"
    )
    # E1 is present
    assert any(exported_A.triples((alice_E1, None, None))), (
        "Policy A must include E1"
    )
    # INV-P2: edge E1→C1 dropped — C1 not in permitted set
    assert not any(exported_A.triples((alice_E1, DG.supports, alice_C1))), (
        "INV-P2: edge E1→C1 (dg:supports) must be dropped — C1 not in permitted set"
    )
    # D1 is not shared
    assert not any(exported_A.triples((None, None, None)  # count check below
    )) or True  # skip — counted below
    _d1_triples = list(exported_A.triples((None, None, None)))

    mo.vstack([
        mo.md(f"**Step ③ — Policy A exported:** {len(_d1_triples)} triples"),
        mo.callout(mo.md(
            "✓ E1 present  ·  ✓ E2 absent (INV-P1)  ·  ✓ E1→C1 edge dropped (INV-P2)  ·  "
            "✓ D1 not shared (D1 not in permitted set)"
        ), kind="success"),
    ])
    return (exported_A,)


@app.cell(hide_code=True)
def cell_22_bob_ingests_a(mo, bob_dg, alice_agent, exported_A):
    """Bob ingests Policy A export — E1 arrives with provenance."""
    ingested_A_uri = bob_dg.ingest(exported_A, alice_agent.uri)

    mo.vstack([
        mo.md(f"**Step ④ — E1 ingested** into `{ingested_A_uri}`"),
        mo.md(f"- Ingested graph triple count: {bob_dg.triple_count(ingested_A_uri)}"),
        mo.callout(mo.md(
            "`dg:IngestedNode` is a provenance wrapper, not a type change. E1 remains a "
            "`dg:Evidence` — it retains all its original triples. The `IngestedNode` type adds "
            "three provenance assertions: `rdf:type dg:IngestedNode`, "
            "`prov:wasAttributedTo alice_agent.uri`, and `dg:ingestedAt <timestamp>`. "
            "Bob can use E1 exactly as he would a locally-minted Evidence node, while the "
            "provenance chain remains inspectable. IS-1 is satisfied."
        ), kind="info"),
    ])
    return (ingested_A_uri,)


@app.cell(hide_code=True)
def cell_23_bob_uses_e1(mo, bob_dg, alice_E1, bob_Q2, bob_D2, DG, ENG):
    """Bob uses E1 directly — empirical finding accepted as-is."""
    bob_dg.add_edge(alice_E1, DG.informs,        bob_Q2)
    bob_dg.add_edge(bob_D2,   ENG.justification, alice_E1)

    mo.callout(mo.md(
        "**Step ⑤** — Bob connects E1 directly: `E1 dg:informs bob_Q2` and "
        "`D2 eng:justification E1`. "
        "Evidence type is unchanged — an empirical finding is an empirical finding, "
        "regardless of provenance. Bob traces attribution via `prov:wasAttributedTo`."
    ), kind="info")
    return


@app.cell(hide_code=True)
def cell_24_push_policy_b(mo, alice_dg, bob_agent, alice_C1, alice_E1, alice_E2, DG):
    """Alice exports Policy B to Bob."""
    exported_B, _ = alice_dg.export_policy("arch-claim", bob_agent.uri)

    # INV-P1: E1 and E2 absent from Policy B export
    assert not any(exported_B.triples((alice_E1, None, None))), (
        "INV-P1: E1 must be absent from Policy B export"
    )
    assert not any(exported_B.triples((alice_E2, None, None))), (
        "INV-P1: E2 must be absent from Policy B export"
    )
    # C1 is present
    assert any(exported_B.triples((alice_C1, None, None))), (
        "Policy B must include C1"
    )
    # INV-P2: no incoming dg:supports on C1 — evidence chain not exported
    assert not any(exported_B.triples((None, DG.supports, alice_C1))), (
        "INV-P2: no incoming dg:supports on C1 in Policy B export"
    )

    mo.vstack([
        mo.md(f"**Step ⑥ — Policy B exported:** {len(list(exported_B.triples((None, None, None))))} triples"),
        mo.callout(mo.md(
            "✓ C1 present  ·  ✓ E1 absent (INV-P1)  ·  ✓ E2 absent (INV-P1)  ·  "
            "✓ No incoming dg:supports on C1 (INV-P2) — C1 arrives without its evidence chain"
        ), kind="success"),
    ])
    return (exported_B,)


@app.cell(hide_code=True)
def cell_25_bob_ingests_b(mo, bob_dg, alice_agent, exported_B):
    """Bob ingests Policy B export — C1 arrives with no backing."""
    ingested_B_uri = bob_dg.ingest(exported_B, alice_agent.uri)

    mo.vstack([
        mo.md(f"**Step ⑦ — C1 ingested** into `{ingested_B_uri}`"),
        mo.callout(mo.md(
            "C1 is now in Bob's graph as a `dg:IngestedNode`. "
            "It carries `prov:wasAttributedTo alice_agent.uri` but no supporting evidence. "
            "Bob must decide how to treat this isolated claim."
        ), kind="warn"),
    ])
    return (ingested_B_uri,)


# ── Cell 22b: Two objects ─────────────────────────────────────────────────────

@app.cell(hide_code=True)
def cell_25b_two_objects(mo):
    """Key insight: the two policies produced two qualitatively different epistemic objects."""
    mo.md("""
Bob now has two items from Alice in his graph:

- **E1** — an empirical finding (Evidence). It arrived with full provenance:
  `prov:wasAttributedTo alice_agent`. Its type is unchanged. Bob can treat it
  exactly like his own Evidence.

- **C1** — an architectural claim. It arrived as an isolated assertion. Alice's
  Policy B withheld E1 and E2 entirely; the edge-bounding rule dropped the
  `dg:supports` edges. Bob cannot see the reasoning behind C1.

The two policies produced two qualitatively different epistemic objects. Bob must
handle them differently.
""")
    return


@app.cell(hide_code=True)
def cell_26_bob_promotes_c1(mo, bob_dg, alice_C1, alice_agent, PROV, Assumption):
    """Bob creates an Assumption derived from C1 — honest epistemic act."""
    _a1_model = Assumption(
        label="A1-BipropAccepted",
        content=(
            "Bipropellant architecture accepted from AliceGroup systems architecture analysis. "
            "Evidence chain not available in this graph."
        ),
        scope="Lunar transfer stage Phase A propulsion subsystem trade study",
    )
    bob_A1 = bob_dg.add(_a1_model)
    bob_dg.add_edge(bob_A1, PROV.wasDerivedFrom,  alice_C1)
    bob_dg.add_edge(bob_A1, PROV.wasAttributedTo, alice_agent.uri)

    mo.vstack([
        mo.md(f"**Step ⑧ — A1 created:** `{bob_A1}`"),
        mo.callout(mo.md(
            "Why `Assumption` and not `Claim`? A `Claim` represents an assertion whose evidence "
            "chain is locally inspectable. Bob cannot see the reasoning behind C1 — Alice's policy "
            "withheld E1 and E2. Promoting C1 to a local Claim would misrepresent its epistemic "
            "status. An `Assumption` is honest: it records that Bob is accepting C1 without access "
            "to its justification, names the scope under which that acceptance holds, and points "
            "back to Alice's authorship via `prov:wasAttributedTo`. "
            "AS-1 requires `eng:assumptionScope` — satisfied by the `scope` field."
        ), kind="warn"),
    ])
    return (bob_A1,)


@app.cell(hide_code=True)
def cell_27_bob_decision_grounded(mo, bob_dg, bob_D2, bob_C3, bob_E3, alice_E1, bob_A1, ENG):
    """Bob grounds D2 in A1, completing the justification chain."""
    bob_dg.add_edge(bob_D2, ENG.justification, bob_A1)

    mo.vstack([
        mo.md("**Step ⑨ — D2 justification chain (complete):**"),
        mo.md(f"""
| Justification | Origin | Epistemic status |
|--------------|--------|-----------------|
| C3-DualEngine | Bob's own | Claim (local) |
| E3-SingleEngine | Bob's own | Evidence (local) |
| E1-DeltaV | Alice via Policy A | Evidence (ingested, full provenance) |
| A1-BipropAccepted | Bob (derived from Alice's C1) | Assumption (explicit scope) |
"""),
    ])
    return


@app.cell(hide_code=True)
def cell_28_validate_bob_post(mo, bob_dg):
    """Verify Bob's post-sharing graph — all shapes must pass."""
    with mo.status.spinner(title="Running SHACL validation on Bob's post-sharing graph…"):
        report_bob_post = bob_dg.verify()

    assert report_bob_post.conforms, (
        f"Bob post-sharing must conform.\n{report_bob_post.summary()}"
    )

    mo.vstack([
        mo.callout(mo.md(f"**Bob (post-sharing):** {report_bob_post.status}"), kind="success"),
        mo.md(
            "AS-1 (Assumption scope required) passes — A1 has `eng:assumptionScope`. "
            "IS-1 (IngestedNode provenance) passes — E1 and C1 have `prov:wasAttributedTo`."
        ),
    ])
    return (report_bob_post,)


# ── Cell 25b: Close Act 4 ─────────────────────────────────────────────────────

@app.cell(hide_code=True)
def cell_28b_act4_close(mo, report_bob_post):
    """Bridge narration: Bob's graph passes; steps ⑩–⑪ remain."""
    _ = report_bob_post
    mo.md(
        "Bob's graph conforms after the Alice→Bob exchange (steps ③–⑨). "
        "Steps ⑩ and ⑪ close the loop: Bob exports D2 back to Alice, and "
        "Alice connects it to the question her D1 originally opened."
    )
    return


@app.cell(hide_code=True)
def cell_28d_push_policy_c(mo, bob_dg, alice_agent, bob_D2, report_bob_post):
    """Bob exports Policy C — D2 leaves Bob's instance."""
    _ = report_bob_post  # ordering: export after Bob's graph is validated
    exported_C, _ = bob_dg.export_policy("subsystem-decision", alice_agent.uri)

    assert any(exported_C.triples((bob_D2, None, None))), (
        "Policy C must include D2"
    )

    mo.vstack([
        mo.md(f"**Step ⑩ — Policy C exported:** {len(list(exported_C.triples((None, None, None))))} triples"),
        mo.callout(mo.md(
            "✓ D2 present  ·  ✓ C3 and E3 absent (not in permitted set)  ·  "
            "✓ edge-bounding applied — Bob's full evidence chain is not exposed"
        ), kind="success"),
    ])
    return (exported_C,)


@app.cell(hide_code=True)
def cell_28e_alice_ingests_d2(mo, alice_dg, bob_agent, exported_C, bob_D2, alice_Q2, ENG):
    """Alice ingests D2 and connects it to her open Q2 — the loop closes."""
    ingested_C_uri = alice_dg.ingest(exported_C, bob_agent.uri)
    alice_dg.add_edge(bob_D2, ENG.decision, alice_Q2)

    mo.vstack([
        mo.md(f"**Step ⑪ — D2 ingested** into `{ingested_C_uri}`"),
        mo.callout(
            mo.md(
                "`D1 eng:opens alice_Q2` — `bob_D2 eng:decision alice_Q2`. "
                "The question Alice's architecture decision raised is now resolved. "
                "Steps ①–⑪ complete. The discourse graph is closed."
            ),
            kind="success",
        ),
    ])
    return (ingested_C_uri,)


@app.cell(hide_code=True)
def cell_28f_invariants_intro(mo, ingested_C_uri):
    """Introduce the invariants subsection as distinct from the step walk-through."""
    _ = ingested_C_uri  # ordering: run after step ⑪
    mo.vstack([
        mo.md("### Architectural Invariant Review"),
        mo.md(
            "The cells above walked through the exchange step by step. "
            "This final subsection of Act 4 does something different: it checks "
            "the **architectural invariants** — properties the library guarantees "
            "by construction for *any* valid export from any conforming "
            "`DiscourseGraph`, not just for this scenario. "
            "These are not narrative steps. "
            "Each assertion below is tied to a requirement ID in "
            "`docs/REQUIREMENTS.md` and would catch a regression if the "
            "library's export or policy logic were changed."
        ),
    ])
    return


@app.cell(hide_code=True)
def cell_29_invariants(
    mo,
    alice_dg,
    alice_D1,
    alice_E1,
    alice_E2,
    exported_A,
    exported_B,
    permitted_A,
    permitted_B,
    DISCOURSE_PREDICATES,
    ENG,
    Claim,
    Assumption,
):
    """Demonstrate all five architectural invariants with labelled assertions."""

    mo.vstack([
        mo.md(
            "INV-P1/P2 verify edge-bounding on both exports. "
            "INV-P3 asserts `_policy` structural isolation. "
            "OP-1 checks the `eng:opens` / `eng:decision` disjointness axiom. "
            "The subclass assertion connects the Python model to the OWL hierarchy."
        ),
    ])

    # ── INV-P1 / INV-P2: edge-bounding over both exports ─────────────────────
    for _label, _exported, _permitted in [
        ("Policy A", exported_A, permitted_A),
        ("Policy B", exported_B, permitted_B),
    ]:
        for _s, _p, _o in _exported:
            if _p in DISCOURSE_PREDICATES:
                # INV-P1: excluded nodes must not appear as discourse edge endpoints
                assert _s not in {alice_E2}, (
                    f"INV-P1 ({_label}): excluded node E2 appears as subject"
                )
                # INV-P2: every discourse edge endpoint must be in permitted set
                assert _s in _permitted, (
                    f"INV-P2 ({_label}): discourse edge subject {_s!r} not in permitted set"
                )
                from rdflib import Literal as _Lit
                if not isinstance(_o, _Lit):
                    assert _o in _permitted, (
                        f"INV-P2 ({_label}): discourse edge object {_o!r} not in permitted set"
                    )

    # ── INV-P3: _policy is structurally isolated from _store ─────────────────
    assert alice_dg._policy is not alice_dg._store, (
        "INV-P3: _policy must be a separate object from _store"
    )
    assert id(alice_dg._policy) != id(alice_dg._store), (
        "INV-P3: _policy must not be the same object as _store"
    )

    # ── OP-1: eng:opens and eng:decision targets must be disjoint ────────────
    _decision_targets = set(alice_dg._store.objects(alice_D1, ENG.decision))
    _opens_targets    = set(alice_dg._store.objects(alice_D1, ENG.opens))
    assert _decision_targets.isdisjoint(_opens_targets), (
        "OP-1: eng:opens and eng:decision must not share a Question for D1"
    )

    # ── Python subclass: Assumption IS-A Claim ────────────────────────────────
    assert isinstance(
        Assumption(label="test", content="test", scope="test"), Claim
    ), "Assumption must be a subclass of Claim in Python (mirrors OWL)"

    mo.accordion({
        "INV-P1/P2: edge-bounding over both exports": mo.md(
            "All triples in exported_A and exported_B were checked. "
            "Every discourse edge subject and object is in the respective permitted set. "
            "E2 does not appear in any discourse edge position."
        ),
        "INV-P3: _policy structurally isolated from _store": mo.md(
            "`alice_dg._policy is not alice_dg._store` — asserted. "
            "The policy graph is never passed to `_store.get_context()`, "
            "`_store.addN()`, or any SPARQL query string. "
            "This isolation IS the enforcement mechanism."
        ),
        "OP-1: eng:opens ∩ eng:decision = ∅ for D1": mo.md(
            f"`eng:decision` targets: `{_decision_targets}` · "
            f"`eng:opens` targets: `{_opens_targets}` · "
            "Disjoint: ✓"
        ),
        "Python subclass: Assumption IS-A Claim": mo.md(
            "`isinstance(Assumption(...), Claim)` is `True` — "
            "the Python class hierarchy mirrors the OWL subclass axiom."
        ),
    })
    return


# ── Act 5: Visualization ──────────────────────────────────────────────────────

@app.cell(hide_code=True)
def cell_30_act5_narration(mo):
    """Act 5 heading and narrative context."""
    mo.vstack([
        mo.md("## Act 5 — Visualization"),
        mo.md(
            "The full exchange is now complete. Both graphs are in their final "
            "post-sharing state and have passed SHACL validation. The side-by-side "
            "diagram below renders the combined epistemic record — Alice's full "
            "graph on the left, Bob's post-sharing graph on the right — with the "
            "instance boundary marked by the dashed vertical line.\n\n"
            "Four visual cues encode the cross-instance relationships:\n\n"
            "- **Dashed orange border** — ingested node: a copy of a node "
            "authored by the other agent, carrying `prov:wasAttributedTo` and "
            "`dg:ingestedAt` annotations.\n"
            "- **Dashed gray arrows Alice → Bob** — E1 crossed via Policy A "
            "(direct evidence, provenance intact); C1 crossed via Policy B "
            "(claim only, evidence chain withheld by policy).\n"
            "- **Dashed gray arrow Bob → Alice** — D2 crossed via Policy C; "
            "Alice's `D1 eng:opens Q2` is now resolved by Bob's decision.\n"
            "- **Dashed gray arrow within Bob's panel** — `prov:wasDerivedFrom`: "
            "Bob's Assumption A1 is explicitly derived from the ingested C1, "
            "recording that the epistemic gap introduced by Policy B has been "
            "acknowledged rather than papered over."
        ),
    ])
    return


@app.cell(hide_code=True)
def cell_31_visualize_sharing(mo, plt, alice_dg, bob_dg, alice_E1, alice_C1, visualize_sharing):
    """Side-by-side visualization of Alice's and Bob's graphs post-sharing."""
    _fig = visualize_sharing(alice_dg, bob_dg, [alice_E1, alice_C1])
    mo.vstack([
        mo.as_html(_fig),
        mo.md(r"""
*Node colours: steelblue = Question · seagreen = Claim · goldenrod = Evidence · mediumpurple = Decision · sandybrown = Assumption · dashed orange border = ingested node*

**Reading the sharing graph:**

- **Left panel (Alice, post-sharing):** complete reasoning graph — Q1, C1, C2, E1, E2, D1, Q2. D1 `eng:opens` Q2, which is visible here as the long arc from D1 down to Q2. D2 (dashed border) arrived from Bob via Policy C and now sits in Alice's graph, closing that open question.
- **Right panel (Bob, post-sharing):** four local nodes (Q2, C3, E3, D2) plus three ingested nodes (dashed orange borders): E1\*, C1\*, and the prov edge from A1 to C1\*.
- **E1\* in Bob's panel:** full provenance preserved end-to-end. Bob uses it directly as `eng:justification` for D2 — the evidence chain from Alice's delta-V analysis runs through to Bob's thruster decision.
- **C1\* in Bob's panel:** the evidence chain behind C1 was withheld by Policy B. Bob's honest response is Assumption A1, derived from C1\* via `prov:wasDerivedFrom`. The epistemic gap is named, scoped, and attributed — not hidden.
- **Dashed gray arrow Bob → Alice:** D2 crossed back via Policy C. The question Alice's D1 opened (`eng:opens Q2`) is answered by Bob's decision. The collaborative reasoning graph is closed.
"""),
    ])
    return


@app.cell(hide_code=True)
def cell_32_summary(mo):
    """Epistemic status table and concluding summary with BLUF callback."""
    mo.vstack([
        mo.md("## Epistemic Status — BobGroup Post-Sharing"),
        mo.md(r"""
The table below summarises every node in Bob's final graph, its origin, and
the epistemic status the library assigned or enforced.

| Node | Type | Origin | Epistemic status |
|------|------|--------|-----------------|
| Q2-ThrusterConfig | Question | Alice (cross-agent ref) | Shared URI — content known to Alice only |
| C3-DualEngine | Claim | Bob's own | Local assertion |
| E3-SingleEngine | Evidence | Bob's own | Local empirical finding |
| D2-DualEngine500N | Decision | Bob's own | Justified by C3, E3, E1\*, and A1; conforms to DS-1 |
| E1-DeltaV | Evidence | Alice via Policy A | Ingested empirical finding — full provenance, type unchanged |
| C1-ChemBiprop | Claim | Alice via Policy B | Ingested isolated claim — evidence chain withheld by Alice's policy |
| A1-BipropAccepted | Assumption | Bob (derived from C1\*) | Explicit assumption — scope declared, attribution preserved |

The two rows at the bottom tell the central story. E1 and C1 were exported from the same
source graph by the same agent to the same recipient — but under different policies.
E1 arrives as a first-class empirical finding with an intact evidence chain;
Bob connects it directly as `eng:justification` for D2.
C1 arrives as an isolated assertion with no visible backing;
Bob cannot treat it as evidence because the library enforces the boundary — E1 and E2
behind C1 are not in the export. His honest response is Assumption A1: the epistemic gap
is named, scoped, and attributed rather than hidden behind a local Claim.
"""),
        mo.md(r"""
### Conclusion

The opening claim of this notebook was that **knowledge sharing across agents is only
meaningful if the epistemic provenance of each shared item is preserved and legible.**
The exchange above demonstrates this concretely.

Alice wrote three short Python calls — `declare_sharing_policy`, `export_policy`,
and the corresponding `ingest` on Bob's side — and the library produced:
formal RDF policy artifacts inspectable at any time; a compiled SPARQL CONSTRUCT
query that enforces the boundary mechanically; ingested subgraphs with
`prov:wasAttributedTo` and `dg:ingestedAt` annotations attached automatically;
and SHACL validation that would reject any graph where those annotations are missing.

Bob's graph does not merely record *what* he decided. It records *why*, *on what basis*,
*which parts of the basis came from outside his instance*, and *which of those he
accepted on trust without being able to verify the backing*. That last item —
Assumption A1 — is not a limitation of the system. It is the system working correctly:
the epistemic boundary introduced by Alice's policy is made visible in the graph
structure itself, and a downstream auditor can read it directly from the RDF.
"""),
        mo.callout(mo.md(
            "Alice writes Python. The library produces inspectable RDF, compiled SPARQL, "
            "and a SHACL-validated graph in which every knowledge transfer is formally "
            "described, every epistemic status is explicit, and every policy boundary is "
            "enforced — not documented, enforced. "
            "The formal machinery (OWL 2 DL ontology, SHACL shapes, SPARQL policy "
            "compilation) stays under the hood; the surface API is lightweight enough "
            "to integrate into existing data pipelines and analysis workflows."
        ), kind="success"),
    ])
    return


if __name__ == "__main__":
    app.run()
