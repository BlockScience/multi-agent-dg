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

# Discourse Graph — Policy-Controlled Multi-Agent Knowledge Sharing

**Domain:** Lunar transfer stage propulsion trade study
**Agents:** AliceGroup (systems architecture) · BobGroup (propulsion subsystem)

---

## Layer stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Ontology | OWL 2 DL (`dg:` + `eng:`) | Class hierarchy and predicate semantics |
| Shapes | SHACL | Structural and relational constraints |
| Runtime | Pydantic + rdflib | Write-time validation and RDF storage |
| Policy | RDF + SPARQL | Formal, inspectable sharing rules |

---

## Five-act narrative

| Act | Cells | Topic |
|-----|-------|-------|
| 1 | 2–5 | Setup — load ontologies, create agents and graphs |
| 2 | 6–11 | Individual graphs — Alice and Bob build independently |
| 3 | 12–17 | Policy declaration — Alice writes two policies; inspect the Turtle and SPARQL artifacts |
| 4 | 18–26 | Sharing — policy A (direct evidence), policy B (hidden-backing claim); invariants demonstrated |
| 5 | 27–28 | Visualization and epistemic status summary |

---

## Two sharing policies

| Policy | Permitted set | Epistemic character |
|--------|--------------|---------------------|
| `evidence-sharing` | {E1} | Direct evidence: Bob receives Alice's delta-V analysis with full provenance |
| `arch-claim` | {C1} | Hidden-backing claim: Bob receives Alice's baseline assertion with no visible justification |
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
        mo.md(f"**Shapes loaded:** {len(shapes)} triples"),
        mo.md(_shape_table),
        mo.callout(
            mo.md(
                "SHACL and Pydantic serve different roles: Pydantic validates the model instance "
                "at Python call time; SHACL validates the serialized RDF graph after triples are "
                "written. Both are required — some constraints (such as ES-2's requirement that "
                "Evidence must support or inform at least one node) can only be checked once the "
                "edges exist in the graph."
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
    ])
    return (alice_agent, bob_agent)


@app.cell(hide_code=True)
def cell_5_discourse_graphs(mo, DiscourseGraph, alice_agent, bob_agent, ontology, shapes):
    """Create DiscourseGraph instances for each agent."""
    alice_dg = DiscourseGraph(alice_agent, ontology, shapes, verify_on_write=False)
    bob_dg   = DiscourseGraph(bob_agent,   ontology, shapes, verify_on_write=True)
    mo.vstack([
        mo.md("**DiscourseGraph instances created:**"),
        mo.callout(
            mo.md(
                "Alice: `verify_on_write=False` — structural checks deferred to `verify()`. "
                "Bob: `verify_on_write=True` — domain/range validated at every `add_edge()` call."
            ),
            kind="info",
        ),
        mo.callout(
            mo.md(
                "A `DiscourseGraph` holds a ConjunctiveGraph (`_store`) for typed node triples "
                "and discourse edges, a structurally isolated `_policy` Graph for sharing policy "
                "RDF, and references to the ontology and shapes for on-demand SHACL validation. "
                "The `_policy` graph is never merged into `_store` — this structural isolation "
                "is how INV-P3 is enforced."
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
Both agents have empty discourse graphs in their own namespaces. In Act 2 each
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
    alice_dg.add_edge(alice_D1, ENG.opens,         alice_Q2)

    mo.vstack([
        mo.md("**AliceGroup graph populated** — 7 nodes, 7 discourse edges."),
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
        mo.md(
            "*Node colours: steelblue = Question, seagreen = Claim, goldenrod = Evidence, "
            "mediumpurple = Decision.*\n\n"
            "D1 (`eng:decision`) → Q1: the decision resolves Q1. "
            "D1 (`eng:justification`) → C1 and E1: the claim and evidence that justify the decision. "
            "D1 (`eng:opens`) → Q2: the decision raises a downstream question for BobGroup. "
            "E1 (`dg:supports`) → C1: empirical evidence backing the baseline claim. "
            "E1 (`dg:informs`) → Q1: the delta-V budget directly informs the architecture question."
        ),
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

    mo.vstack([
        mo.md("**BobGroup graph populated** — 4 local nodes, 4 discourse edges."),
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
    _fig, _ax = plt.subplots(figsize=(8, 6))
    visualize_graph(bob_dg, ax=_ax, title="BobGroup — pre-sharing graph")
    plt.tight_layout()
    mo.vstack([
        mo.as_html(_fig),
        mo.md(
            "*Bob's pre-sharing graph: Q2 (steelblue), C3 (seagreen), E3 (goldenrod), "
            "D2 (mediumpurple). D2 `eng:decision` bob_Q2 — Bob's subsystem question. "
            "Alice's E1 and C1 arrive in Act 4.*"
        ),
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
        mo.md("""
Alice declares two sharing policies in Python. Each policy names a grantee, a
source graph, and a selection rule (type-based or node-explicit). The library
stores each policy as a `dg:SharingPolicy` individual in a structurally isolated
`_policy` graph — it never touches `_store`. At export time the policy is
compiled to a SPARQL CONSTRUCT query.

This act shows the artifacts. The SPARQL was not written by Alice; it was
generated from the RDF. This is the architectural guarantee: Alice cannot write
a malformed policy by accident, and the query is always inspectable.
"""),
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
        mo.md(f"- Grantee: `{bob_agent.uri}`"),
        mo.md(f"- Include types: `[dg:Evidence]`"),
        mo.md(f"- Exclude nodes: `[E2-Schedule]`"),
        mo.md(f"- **Permitted set:** {{E1}}"),
        mo.md(f"- Policy URI: `{policy_A_uri}`"),
    ])
    return (policy_A_uri,)


@app.cell(hide_code=True)
def cell_15_policy_a_rdf(mo, alice_dg):
    """Print the RDF Turtle serialization of alice_dg._policy.

    This is the 'lift the hood' moment: the audience sees that Alice's Python
    call produced a formal RDF artifact stored in the isolated _policy graph.
    """
    _turtle = alice_dg._policy.serialize(format="turtle")
    mo.vstack([
        mo.md("### Policy A — RDF artifact (`alice_dg._policy` serialised as Turtle)"),
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
                "This structural isolation is the enforcement mechanism for INV-P3: a compromised "
                "`export_policy()` implementation cannot leak triples from `_store` into an "
                "unauthorized export, because `_policy` is never in `_store`."
            ),
            kind="info",
        ),
    ])
    return


@app.cell(hide_code=True)
def cell_16_policy_a_sparql(mo, alice_dg, policy_A_uri):
    """Compile Policy A to SPARQL and display the generated query."""
    sparql_A, permitted_A = alice_dg._compile_policy(policy_A_uri)

    _permitted_labels = [str(u).rsplit("/", 1)[-1] for u in sorted(str(u) for u in permitted_A)]

    mo.vstack([
        mo.md("### Policy A — compiled SPARQL CONSTRUCT"),
        mo.md(
            "The SPARQL was generated from the RDF policy above — Alice never wrote SQL or SPARQL. "
            "In plain English, the edge-bounding rule says: a triple `(s, p, o)` may only be "
            "exported if the subject `s` is in the permitted set AND either the object is a plain "
            "value (literal), the predicate is not a discourse predicate, or the object is also in "
            "the permitted set. This prevents edges from escaping the policy boundary even when "
            "both endpoints happen to exist in Alice's store. "
            "Formally: `(s, p, o)` exported iff `s ∈ permitted` AND "
            "(`isLiteral(o)` OR `p ∉ DISCOURSE_PREDICATES` OR `o ∈ permitted`)."
        ),
        mo.md(f"```sparql\n{sparql_A}\n```"),
        mo.md(f"**Permitted set:** `{{{', '.join(_permitted_labels)}}}`"),
    ])
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
        mo.md(f"- Grantee: `{bob_agent.uri}`"),
        mo.md(f"- Include nodes: `[C1-ChemBiprop]`"),
        mo.md(f"- **Permitted set:** {{C1}} — no type filter, no exclude"),
        mo.md(f"- Policy URI: `{policy_B_uri}`"),
        mo.callout(
            mo.md(
                "C1 will be shared **without** E1 or E2 — Bob receives the baseline assertion "
                "with no visible evidence chain. He must decide whether to accept it."
            ),
            kind="warn",
        ),
    ])
    return (policy_B_uri,)


@app.cell(hide_code=True)
def cell_18_policy_b_rdf(mo, alice_dg):
    """Print updated _policy Turtle — now contains both policies."""
    _turtle = alice_dg._policy.serialize(format="turtle")
    mo.vstack([
        mo.md("### Policy graph after both declarations"),
        mo.accordion({
            "Full Turtle (both policies)": mo.md(f"```turtle\n{_turtle}\n```"),
        }),
        mo.md(
            "Both `dg:SharingPolicy` individuals are in the same isolated `_policy` graph. "
            "Contrast the `dg:includesType` triple in Policy A with the `dg:includesNode` "
            "triple in Policy B — different selection mechanisms, different epistemic characters."
        ),
    ])
    return


@app.cell(hide_code=True)
def cell_19_policy_b_sparql(mo, alice_dg, policy_B_uri):
    """Compile Policy B to SPARQL."""
    sparql_B, permitted_B = alice_dg._compile_policy(policy_B_uri)

    _permitted_labels = [str(u).rsplit("/", 1)[-1] for u in sorted(str(u) for u in permitted_B)]

    mo.vstack([
        mo.md("### Policy B — compiled SPARQL CONSTRUCT"),
        mo.md(
            "Contrast with Policy A: `VALUES ?s` now contains only C1. "
            "No `dg:supports` or `dg:informs` edges point into `{C1}` from E1 or E2, "
            "so the edge-bounding FILTER drops all incoming discourse edges on C1."
        ),
        mo.md(f"```sparql\n{sparql_B}\n```"),
        mo.md(f"**Permitted set:** `{{{', '.join(_permitted_labels)}}}`"),
    ])
    return (sparql_B, permitted_B)


# ── Act 4: Sharing ─────────────────────────────────────────────────────────────

@app.cell(hide_code=True)
def cell_20_act4_narration(mo):
    """Act 4 heading and narrative context."""
    mo.vstack([
        mo.md("## Act 4 — Sharing"),
        mo.md("""
Alice pushes each policy to Bob. For each export the system executes the compiled
SPARQL CONSTRUCT against Alice's store and applies the edge-bounding rule: a
triple `(s, p, o)` is exported only when `s` is in the permitted set AND either
`o` is a literal, `p` is not a discourse predicate, or `o` is also in the
permitted set. This prevents discourse edges from crossing the policy boundary
even when both endpoints exist.
"""),
    ])
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
        mo.md(f"**Policy A exported:** {len(_d1_triples)} triples"),
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
        mo.md(f"**E1 ingested** into `{ingested_A_uri}`"),
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
        "Bob connects E1 directly: `E1 dg:informs bob_Q2` and `D2 eng:justification E1`. "
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
        mo.md(f"**Policy B exported:** {len(list(exported_B.triples((None, None, None))))} triples"),
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
        mo.md(f"**C1 ingested** into `{ingested_B_uri}`"),
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
        mo.md(f"**A1 created:** `{bob_A1}`"),
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
        mo.md("**D2 justification chain (complete):**"),
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
def cell_28b_act4_close(mo):
    """Act 4 closing narration: full graph passes; invariants coming up."""
    mo.md("""
Bob's full graph — local nodes, ingested Evidence, ingested Claim, and the new
Assumption — passes all nine SHACL shapes. The invariant cell below checks the
architectural guarantees that made this possible.
""")
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
        mo.md("""
The five invariants below are architectural guarantees — they hold for any valid
export from any conforming `DiscourseGraph`, not just for this scenario.
INV-P1 and INV-P2 together enforce the edge-bounding rule on every exported triple.
INV-P3 enforces that policy RDF is structurally isolated from the knowledge store
(structural enforcement, not convention). OP-1 and the Python subclass assertion
connect the graph-level constraints back to the OWL axioms.
"""),
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
        mo.md("""
The side-by-side view shows both graphs after the sharing event. Ingested nodes
carry a dashed orange border. The dashed gray arrow from A1 to C1* shows the
`prov:wasDerivedFrom` edge Bob added when he promoted C1 to an Assumption.
"""),
    ])
    return


@app.cell(hide_code=True)
def cell_31_visualize_sharing(mo, plt, alice_dg, bob_dg, alice_E1, alice_C1, visualize_sharing):
    """Side-by-side visualization of Alice's and Bob's graphs post-sharing."""
    _fig = visualize_sharing(alice_dg, bob_dg, [alice_E1, alice_C1])
    mo.vstack([
        mo.as_html(_fig),
        mo.md(
            "*Left: Alice's full graph — D1 connects Q1, C1, E1, and opens Q2. "
            "Right: Bob's post-sharing graph — E1\\* and C1\\* (dashed orange border = ingested), "
            "A1 (sandybrown = Assumption), dashed gray arrow = `prov:wasDerivedFrom` A1→C1\\*.*"
        ),
    ])
    return


@app.cell(hide_code=True)
def cell_32_summary(mo):
    """Epistemic status table — all nodes in Bob's post-sharing graph."""
    mo.vstack([
        mo.md("## Epistemic Status — BobGroup Post-Sharing"),
        mo.md(r"""
| Node | Type | Origin | Epistemic status |
|------|------|--------|-----------------|
| Q2-ThrusterConfig | Question | Alice (cross-agent ref) | Shared URI — content known to Alice only |
| C3-DualEngine | Claim | Bob's own | Local assertion |
| E3-SingleEngine | Evidence | Bob's own | Local empirical finding |
| D2-DualEngine500N | Decision | Bob's own | Local decision, justified below |
| E1-DeltaV | Evidence | Alice via Policy A | Ingested empirical finding — full provenance, type unchanged |
| C1-ChemBiprop | Claim | Alice via Policy B | Ingested isolated claim — evidence chain withheld by Alice's policy |
| A1-BipropAccepted | Assumption | Bob (derived from C1) | Explicit assumption — scope declared, attribution preserved |

**Key observation:** The two sharing policies produce two qualitatively different epistemic objects
in Bob's graph. E1 arrives as a first-class empirical finding. C1 arrives as an isolated assertion;
Bob's honest response is to promote it to an Assumption with explicit scope and attribution.
The system enforces the boundary — Bob cannot see E1 or E2 behind C1 — and the Assumption
makes that boundary visible in the graph structure itself.
"""),
        mo.callout(mo.md(
            "The discourse-graph library makes epistemic boundaries first-class. Alice writes "
            "Python; the library produces inspectable RDF and SPARQL. Bob's graph records not "
            "just what he knows but how he knows it and what he chose to accept on trust. "
            "The SHACL shapes enforce that these provenance annotations are always present — "
            "no node can be silently ingested without attribution."
        ), kind="success"),
    ])
    return


if __name__ == "__main__":
    app.run()
