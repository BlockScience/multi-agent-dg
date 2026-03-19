# Architecture — Discourse Graph Package

## Concept of operations

### Audience

Semantic web practitioners who understand RDF, OWL, SHACL, and SPARQL.
The adoption barrier is not comprehension — it is **ceremony**.
Writing Turtle by hand to assert a claim, running a SPARQL query to find
supporting evidence, validating a graph by invoking pyshacl directly: these
are all tractable but they impose a high interaction cost that discourages
routine use.

The goal of this package is to eliminate that cost without hiding the
capability. The analogy is scientific Python:

| Scientific Python | This package |
|---|---|
| `numpy` hides LAPACK/BLAS | `DiscourseGraph` hides `ConjunctiveGraph` |
| `sklearn` hides convex optimization | `ValidationReport` hides `pyshacl.validate` |
| `pandas` hides memory layout | Pydantic node models hide Turtle/RDF triples |
| The underlying formalism is always accessible | The RDF store is always accessible via `._store` |

A user who knows numpy doesn't need to know real analysis to use it
productively. A user who knows this package doesn't need to know that
SHACL is running on every write when `verify_on_write=True`. But an
expert user who knows both can drop to the lower layer at any time —
and that is a feature, not a concession.

### The adoption problem being solved

The audience has been using a bespoke SQL database with a common remote
for collaborative discourse graph curation. That architecture works but
has a specific failure mode: **the ontology, the policy, and the
verification are all implicit**. The schema lives in a migration file.
The sharing policy is an access control list. Validation is ad hoc.
Collaboration means "don't step on each other."

What this package makes explicit:

| Currently implicit | Made explicit by |
|---|---|
| Schema / ontology | OWL 2 DL Turtle, versioned, composable |
| Node constraints | SHACL shapes with requirement IDs |
| Sharing policy | RDF triples in `_policy`, compiled to SPARQL |
| Provenance | PROV-O triples on every ingested node |
| Verification | `verify()` returning typed `ValidationReport` |

The demo does not need to explain what RDF is. It needs to show that
adopting this stack costs less than they think, because the ceremony is
handled by the package.

### Schema composability as a first-class demonstration

The `dg:` / `eng:` split is not just an architectural decision — it is a
**live demonstration of OWL composability** for the audience. They watch
`dg:` (the upstream base grammar from discoursegraphs.com) stay untouched
while `eng:` (the engineering extension) adds `eng:Decision` and two
predicates without violating a single `dg:` constraint. SHACL validation
confirms this at runtime.

The message: you can faithfully adopt an upstream ontology and extend it
for your domain without forking it, without violating it, and without
asking anyone's permission. This is the OWL extension pattern working as
designed — but most practitioners have never seen it demonstrated cleanly
in Python.

### Pydantic as the primary API layer

Pydantic node models are the **primary user-facing API**, not an optional
wrapper. The RDF store is the numpy array underneath: always there, never
directly touched in normal use, fully accessible when you need it.

```
User code
  └── Pydantic node models        Question, Claim, Evidence, Decision
        └── DiscourseGraph methods  add(), add_edge(), verify(), export_policy()
              └── rdflib ConjunctiveGraph   (quad store — the numpy layer)
                    └── pyshacl             (invoked by verify())
                    └── SPARQL CONSTRUCT    (invoked by export_policy())
```

The Pydantic model carries the type information and validates at Python
time. The SHACL shape validates the same constraints at graph time. This
redundancy is intentional: Pydantic catches errors at the call site with
a clean Python traceback; SHACL catches them in the serialized graph
regardless of how it was written. Both layers are needed for a robust
system; neither should be visible to a user just trying to add a claim.

### Demo narrative arc

```
Act 1 — Setup (cells 1–5)
  Import the package. Load the ontologies. Create two agents.
  Audience sees: five lines of Python. No Turtle. No SPARQL.

Act 2 — Individual graphs (cells 6–11)
  Alice and Bob each build their discourse graphs independently.
  Alice adds D1 (eng:Decision) with eng:opens → Q2 — the first eng: nodes.
  Both graphs validate; reports show requirement IDs, not SHACL internals.
  Audience sees: Python objects. Typed validation results.

Act 3 — Policy declaration (cells 12–17)
  Alice declares TWO policies in Python.
  Each policy is stored as RDF — show the Turtle serialization.
  Each policy compiles to SPARQL — show the generated queries.
  Audience sees: their Python calls produced formal, inspectable artifacts.
  This is the "lift the hood" moment. The formalism was there all along.

Act 4 — Sharing (cells 18–26)
  Policy A: Alice pushes E1 (Evidence). Bob uses it directly.
  Policy B: Alice pushes C1 (Claim, backing hidden). Bob promotes it
            to eng:Assumption with explicit scope and prov:wasDerivedFrom.
  Bob's D2 is now grounded in: his own C3, E3, Alice's E1 (direct),
  and A1 (his Assumption derived from Alice's hidden-backing Claim).
  Audience sees: the two patterns side by side — Evidence used directly,
  Claim-with-hidden-backing promoted to explicit Assumption.
  Invariants asserted for both exports.

Act 5 — Visualization (cells 27–28)
  Side-by-side graph visualization.
  Shared nodes highlighted; hidden nodes absent from Bob's panel.
  A1 annotated with wasDerivedFrom back to C1*.
  Epistemic status summary table.
  Audience sees: the policy held, and Bob's graph is epistemically honest.
```

---

## Ontology provenance and conformance

### `dg:` — original authorship, conformant to discoursegraphs.com base grammar

`dg:` (`http://example.org/dg/1.0/`) is an **original ontology authored by
this project**. It is not imported from an external registry. The namespace
IRI is a W3C example stub; it must be replaced with a firm-controlled HTTPS
IRI or registered PURL before production use.

The `dg:` ontology is a **semantic web implementation of the information
model specified by the discoursegraphs.com project** (Joel Chan et al.,
University of Maryland / Homeworld Collective). Our ontology must not
violate their canonical model. The authoritative specification is at
https://discoursegraphs.com/docs/roam/base-grammar.

**discoursegraphs.com canonical base grammar (our compliance target):**

| Element | Kind | Our `dg:` term |
|---|---|---|
| QUE — Question | Node class | `dg:Question` |
| CLM — Claim | Node class | `dg:Claim` |
| EVD — Evidence | Node class | `dg:Evidence` |
| Source | Node class | `dg:Source` |
| EVD informs QUE | Relation | `dg:informs` |
| EVD supports CLM | Relation | `dg:supports` |
| EVD opposes CLM | Relation | `dg:opposes` |

**Compliance constraint:** `dg:` introduces no node types or relations that
contradict the above. Any predicate whose domain or range conflicts with the
base grammar is a conformance violation and must not be merged.

### `eng:` — domain extension for engineering design rationale

The base grammar intentionally stops at evidence and claims. It does not
define how a group *closes* on a design question — it is domain-agnostic.
For systems engineering design rationale, groups must record concrete
committed choices. The `eng:` namespace provides this without modifying `dg:`.

`eng:` (`http://example.org/eng/1.0/`) is a **declared extension** of the
discoursegraphs.com model. It adds one node type and two relations that are
not present in the base grammar and are not implied by it:

| Element | Kind | Replaces |
|---|---|---|
| `eng:Decision` | Node class | *(new — no base grammar equivalent)* |
| `eng:decision` | Relation (Decision → QUE) | `dg:answers` (removed) |
| `eng:justification` | Relation (Decision → CLM or EVD) | `dg:cites` (removed) |

**Rationale:** `dg:answers` and `dg:cites` were invented predicates that had
no basis in the base grammar. They are replaced by `eng:` terms that carry
explicit engineering semantics. `eng:Decision` is a first-class node so that
decisions can carry status (`provisional`, `final`, `superseded`), authorship
(`prov:wasAttributedTo`), and timestamp — properties a Claim does not
semantically warrant.

**Traversal chain enabled by `eng:`:**

```
dg:QUE ←[eng:decision]— eng:Decision —[eng:opens]→        dg:QUE (downstream)
                        —[eng:justification]→ dg:CLM
                        —[eng:justification]→ dg:EVD
                        —[eng:justification]→ eng:Assumption
                        —[eng:justification]→ dg:Source
```

Reads: "this decision resolves that question, opens these downstream
questions, and is grounded in these claims, evidence, assumptions, and
sources." This is the full engineering closure and continuation pattern
the base grammar does not provide and does not preclude.

**Termination taxonomy:**

| Node | Subclass of | Termination semantics |
|---|---|---|
| `dg:Source` | `dg:DiscourseNode` | Grounded — chain ends at external literature or data |
| `eng:Assumption` | `dg:Claim` | Bounded — chain ends by declared scope; further Evidence not demanded |

### The seam: `dg:Question` as the join point

`dg:Question` is the **only node type shared across both namespaces**. It is
declared in `dg:` (as QUE in the base grammar) and appears as the range of
`eng:decision`. This is the intentional and natural seam between the two
ontologies.

**Intended lifecycle across the seam:**

```
1. OPEN    — pose a design question as dg:Question
2. EXPLORE — accumulate dg:Claim, dg:Evidence, eng:Assumption nodes
             via dg: relations (supports, opposes, informs)
             eng:Assumption terminates a reasoning branch by scope
             declaration; dg:Source terminates by grounding
3. CLOSE   — commit an eng:Decision that:
               eng:decision  → the Question being resolved
               eng:justification → supporting CLM, EVD, Assumption, Source
               eng:opens     → downstream Questions opened by the decision
4. RECURSE — downstream Questions from eng:opens restart the cycle

The dg:Question individual is NEVER mutated or deleted.
Closure is asserted by the existence of an eng:decision edge.
Continuation is asserted by the existence of eng:opens edges.
The graph is a DAG as long as no Decision opens a Question
already in its own ancestry (not enforced by OWL; future SHACL-SPARQL).
```

**Why this seam prevents scope creep in `eng:`:**

There is no `eng:Question` and there should never be one. If you find
yourself wanting to introduce `eng:Question`, that is a signal that the
concept belongs in `dg:` instead — either as a `dg:Question` individual or
as an extension to the base grammar proposed to the discoursegraphs.com team.
The `eng:` namespace is strictly for engineering-closure concepts that have
no home in the base grammar. `dg:Question` already covers design questions
completely; the extension only needs to know how to *close* them.

**Conformance implication:**

Because `dg:Question` is a base-grammar type, any `dg:Question` individual
in an `eng:`-extended graph is still fully valid as a discourse graph node.
An agent that understands only `dg:` and not `eng:` can still read, query,
and share `dg:Question`, `dg:Claim`, and `dg:Evidence` nodes without error.
The `eng:Decision` nodes are simply invisible to that agent — they are
additive, not substitutive. This is the correct extension pattern for a
declared extension of the base grammar.

---

## Conceptual layers

```
┌────────────────────────────────────────────────────────────┐
│  Layer 4 — Application / Demo                               │
│  marimo notebook: AliceGroup ↔ BobGroup sharing demo        │
│  discourse_graph_demo.py                                     │
└─────────────────────────────┬──────────────────────────────┘
                              │ uses
┌─────────────────────────────▼──────────────────────────────┐
│  Layer 3 — Python interface                                  │
│  discourse_graph.py                                          │
│  Agent · DiscourseGraph · ValidationReport · visualize()    │
└──────────┬──────────────────────────────────┬──────────────┘
           │ validates via                    │ stores in
┌──────────▼──────────┐          ┌────────────▼─────────────┐
│  Layer 2 — SHACL    │          │  Layer 2 — RDF store     │
│  shapes.ttl (dg+eng) │          │  rdflib.ConjunctiveGraph │
│  7 node shapes       │          │  (named-graph quad store)│
│  6 req IDs          │          └────────────┬─────────────┘
└──────────┬──────────┘                       │ typed by
           │ references                        │
┌──────────▼──────────────────────────────────▼─────────────┐
│  Layer 1 — OWL 2 DL Ontologies                              │
│  ontology_dg.ttl   — dg: conformant to discoursegraphs.com  │
│  ontology_eng.ttl  — eng: extension for design rationale    │
│  namespace stubs: replace before production                  │
│  imports: prov-o (W3C), rdf/rdfs/xsd/owl (W3C)              │
└────────────────────────────────────────────────────────────┘
```

---

## File / module layout

```
discourse-graph/
├── pyproject.toml
├── README.md
│
├── discourse_graph/           # installable package
│   ├── __init__.py            # public re-exports
│   ├── namespaces.py          # DG and ENG Namespace objects + load_combined_ontology()
│   ├── ontology_dg.py         # DG_ONTOLOGY_TTL constant + load_dg_ontology()
│   ├── ontology_eng.py        # ENG_ONTOLOGY_TTL constant + load_eng_ontology()
│   ├── shapes.py              # SHACL_TTL constant (dg + eng shapes) + load_shapes()
│   ├── models.py              # Pydantic node models — primary user-facing API
│   │                          # Question, Claim, Evidence, Source, Decision
│   │                          # NODE_TYPE_MAP: type → URIRef
│   ├── agent.py               # Agent dataclass
│   ├── graph.py               # DiscourseGraph class
│   │                          # add(node: DiscourseNode) — primary write method
│   │                          # add_node() — raw method, available for tests
│   ├── policy.py              # SharingPolicy compilation helpers
│   ├── report.py              # ValidationReport (Pydantic model, JSON-serializable)
│   └── viz.py                 # visualize_graph(), visualize_sharing()
│
├── tests/
│   ├── test_ontology_dg.py    # FR-ONT-DG-* — dg: classes, properties, conformance
│   ├── test_ontology_eng.py   # FR-ONT-ENG-* — eng: classes, properties
│   ├── test_shacl.py          # FR-SHACL-* — each shape with valid + invalid data
│   ├── test_models.py         # FR-PYD-* — Pydantic validation, to_triples round-trip
│   ├── test_agent.py          # FR-AGENT-* — URI derivation, namespace isolation
│   ├── test_graph.py          # FR-DG-* — add(), add_edge(), verify()
│   ├── test_policy.py         # FR-POL-*, INV-P1/P2/P3
│   ├── test_ingest.py         # FR-ING-* — provenance triples, graph naming
│   └── test_invariants.py     # INV-P1..P5 standalone assertion tests
│
└── notebooks/
    └── discourse_graph_demo.py   # marimo notebook (Layer 4)
```

---

## Internal architecture of DiscourseGraph

```
DiscourseGraph
│
├── agent: Agent
│   └── namespace → deterministic URI space
│
├── _store: ConjunctiveGraph          ← ALL queryable data lives here
│   ├── NamedGraph <agent/graph/local>
│   │   └── agent's own nodes + edges
│   └── NamedGraph <agent/graph/ingested-{src}>
│       └── nodes received via ingest() + provenance triples
│
├── _policy: Graph                    ← STRUCTURALLY ISOLATED (never in _store)
│   └── dg:SharingPolicy individuals
│       ├── dg:grantee
│       ├── dg:sourceGraph           (named graph URI in _store)
│       ├── dg:includesType*
│       ├── dg:includesNode*
│       └── dg:excludesNode*
│
├── _ontology: Graph                  ← read-only, passed in at construction
└── _shapes: Graph                    ← read-only, passed in at construction
```

### Named graph URI scheme

| Graph name | URI pattern | Contents |
|---|---|---|
| `local` | `{namespace}graph/local` | Agent's own authored nodes |
| `ingested-{slug}` | `{namespace}graph/ingested-{slug}` | Nodes received from one source agent |
| `_policy` (NOT in store) | standalone `Graph` object | Policy declarations |

### `verify_on_write` flag behavior

```
verify_on_write=True
  add_node → structural check (type, non-empty content, label) → commit
  add_edge → structural check (predicate valid, domain/range) → commit
  Note: relational SHACL (CS-1 dg:answers, ES-2) NOT checked here —
        these require full graph context and are deferred to verify()

verify_on_write=False
  add_node → unconditional commit
  add_edge → unconditional commit

verify(graph_uri=None) → always available, runs full pyshacl
  graph_uri=<uri>  → validate single named graph
  graph_uri=None   → union of all named graphs in _store
  _policy          → NEVER included (structural isolation)
```

---

## Policy compilation pipeline

```
Alice (Python API)
  │
  │  declare_sharing_policy(
  │      name="delta-v-evidence",
  │      grantee_uri=bob.agent.uri,
  │      source_graph_uri=alice.local_graph_uri,
  │      include_types=[DG.Evidence],
  │      include_nodes=[alice_E1],
  │      exclude_nodes=[alice_E2],
  │  )
  │
  ▼
  _policy Graph (RDF triples, never in _store)
  alice:policy/delta-v-evidence
      a dg:SharingPolicy ;
      dg:grantee         bob:agent ;
      dg:sourceGraph     alice:graph/local ;
      dg:includesType    dg:Evidence ;
      dg:includesNode    alice:node/e1-delta-v-{uid} ;
      dg:excludesNode    alice:node/e2-schedule-{uid} ;
      dg:policyName      "delta-v-evidence" ;
      dg:created         "..."^^xsd:dateTime .
  │
  │  export_policy("delta-v-evidence", bob.agent.uri)
  │
  ▼
  _compile_policy(policy_uri)
  │
  ├── Phase 1 (Python): materialise permitted set
  │     type_matches     = {E1, ...}      ← all dg:Evidence in source graph
  │     explicit_incl    = {E1}           ← add explicitly named
  │     explicit_excl    = {E2}           ← remove
  │     permitted        = {E1}           ← (type_matches ∪ incl) \ excl
  │
  └── Phase 2 (SPARQL CONSTRUCT generation)
        CONSTRUCT { ?s ?p ?o }
        WHERE {
          GRAPH <alice:graph/local> {
            ?s ?p ?o .
            VALUES ?s { <alice:node/e1-...> }
            FILTER (
              isLiteral(?o)
              || ?p NOT IN ( dg:answers dg:supports ... )
              || ?o IN ( <alice:node/e1-...> )
            )
          }
        }
        ↑
        Edge-bounding rule enforced in FILTER:
        literal objects always exported,
        non-discourse predicates (rdf:type, rdfs:label, dg:content, prov:*)
        always exported, discourse edges only when object is also permitted.
  │
  ▼
  Execute CONSTRUCT against _store
  │
  ├── Post-condition P1: excluded nodes absent from export
  ├── Post-condition P2: all discourse edges are endpoint-bounded
  └── Post-condition P3: _policy ≠ _store (structural isolation)
  │
  ▼
  return (exported_Graph, sparql_string)
```

---

## Ingest pipeline

```
Bob (Python API)
  │
  ├── push path:  alice.export_policy(...) → bob.ingest(subgraph, alice.agent.uri)
  └── pull path:  bob.pull_from(alice, "delta-v-evidence")
                  └── calls alice.export_policy() then self.ingest()
  │
  ingest(subgraph, source_agent_uri)
  │
  ├── Create named graph: bob:graph/ingested-{alice-slug}
  ├── Copy all triples from subgraph
  └── For each dg:DiscourseNode in subgraph:
        add rdf:type dg:IngestedNode
        add prov:wasAttributedTo <alice:agent>
        add dg:ingestedAt <now>
  │
  return ingested_graph_uri
```

---

## Multi-agent state diagram

```
INITIAL STATE
  alice._store                         bob._store
  ┌──────────────────────────┐         ┌─────────────────────┐
  │ graph/local              │         │ graph/local         │
  │   Q1, C1, C2             │         │   Q2, C3, E3, D2   │
  │   E1 (Policy A target)   │         │                     │
  │   E2 (hidden)            │         │                     │
  │   D1 —opens→ Q2          │         │                     │
  └──────────────────────────┘         └─────────────────────┘
  alice._policy
  ┌──────────────────────────┐
  │ policy/evidence-sharing  │  ← never visible to Bob
  │   includesType: Evidence │
  │   excludesNode: E2       │
  │ policy/arch-claim        │  ← never visible to Bob
  │   includesNode: C1       │
  └──────────────────────────┘

AFTER POLICY A (E1 shared — Evidence used directly)
  alice._store (unchanged)             bob._store
  ┌──────────────────────────┐         ┌──────────────────────────┐
  │ graph/local              │         │ graph/local              │
  │   Q1, C1, C2             │         │   Q2, C3, E3, D2        │
  │   E1, E2, D1             │         │                          │
  └──────────────────────────┘         ├──────────────────────────┤
                                        │ graph/ingested-alice     │
                                        │   E1* (Evidence)         │
                                        │   + prov:wasAttributedTo │
                                        │   + dg:informs Q2        │
                                        │   + eng:justification D2 │
                                        └──────────────────────────┘

AFTER POLICY B (C1 shared — Claim promoted to Assumption)
  alice._store (unchanged)             bob._store
                                        ┌──────────────────────────┐
                                        │ graph/local (additions)  │
                                        │   A1 (eng:Assumption)    │
                                        │     wasDerivedFrom C1*   │
                                        │     wasAttributedTo alice│
                                        │     scope: "Phase A..."  │
                                        │   D2 —justification→ A1 │
                                        ├──────────────────────────┤
                                        │ graph/ingested-alice     │
                                        │   (E1* from Policy A)    │
                                        │   C1* (IngestedNode)     │
                                        │   + prov:wasAttributedTo │
                                        └──────────────────────────┘

WHAT BOB KNOWS ABOUT ALICE
  ✓  E1 content, provenance (wasAttributedTo Alice)
  ✓  C1 content, provenance (wasAttributedTo Alice)
  ✓  That A1 is derived from Alice's C1
  ✗  E2 exists at all
  ✗  D1 exists or what it decided
  ✗  That E1 supports C1 (edge dropped — C1 not in Policy A permitted set)
  ✗  Count of Alice's hidden nodes
  ✗  Any edge involving E2, D1, C2
```

---

## SPARQL usage map

| Method | SPARQL type | Scope |
|---|---|---|
| `_compile_policy` | CONSTRUCT | scoped to `GRAPH <source_graph_uri>` |
| `verify` | none — delegates to pyshacl | flat Graph (never _policy) |
| `pull_from` | delegates to `export_policy` | same as above |
| `named_graphs` | none — uses rdflib API | `_store.contexts()` |

No user-facing method accepts or emits a SPARQL string.
SPARQL is an implementation detail of `_compile_policy`.

---

## Alignment to external ontologies

| Term | Aligned to | Alignment type |
|---|---|---|
| `dg:DiscourseNode` | `prov:Entity` | `rdfs:subClassOf` |
| `dg:Agent` | `prov:Agent` | `rdfs:subClassOf` |
| `eng:Decision` | `dg:DiscourseNode`, `prov:Entity` | `rdfs:subClassOf` both |
| `dg:IngestedNode` | PROV-O derivation pattern | `prov:wasAttributedTo`, `prov:wasDerivedFrom` (future) |
| `dg:Question` | discoursegraphs.com QUE | conformant implementation |
| `dg:Claim` | discoursegraphs.com CLM, `swan:Claim`, `aif:I-node` | conformant / informal alignment |
| `dg:Evidence` | discoursegraphs.com EVD, `mp:Evidence`, `aif:I-node` | conformant / informal alignment |
| `dg:supports` | discoursegraphs.com "EVD supports CLM" | conformant implementation |
| `dg:opposes` | discoursegraphs.com "EVD opposes CLM" | conformant implementation |
| `dg:informs` | discoursegraphs.com "EVD informs QUE" | conformant implementation |

Full OWL imports and formal alignment deferred until namespace is minted
at a resolvable PURL or firm-controlled HTTPS IRI.
