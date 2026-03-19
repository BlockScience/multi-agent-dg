# discourse-graph

A Python package implementing the [discoursegraphs.com](https://discoursegraphs.com)
information model as a semantic web stack with a clean Pythonic interface.

Built for systems engineering design rationale but faithful to the upstream
discourse graph base grammar (Question / Claim / Evidence).

---

## What this is

A collaborative knowledge graph where distinct agents (teams, individuals,
systems) maintain their own discourse graphs and share subgraphs under
explicitly declared, policy-enforced boundaries.

The semantic web stack (OWL 2 DL / SHACL / SPARQL / PROV-O) provides
rigor, composability, and serialization. The Python interface (Pydantic
node models, typed methods) means you never write Turtle or SPARQL to
do normal work.

```python
from discourse_graph import Question, Claim, Evidence, Decision
from discourse_graph import DiscourseGraph, Agent

alice = Agent("AliceGroup", "http://example.org/alice/")
dg = DiscourseGraph(alice)

q1 = dg.add(Question(
    label="Q1-PropArch",
    content="What propulsion architecture minimises total system mass?",
))
c1 = dg.add(Claim(
    label="C1-ChemBiprop",
    content="Chemical bipropellant (MMH/NTO) is the baseline architecture.",
))
e1 = dg.add(Evidence(
    label="E1-DeltaV",
    content="Delta-V budget: 3.2 km/s required for TLI + LOI.",
))

dg.add_edge(e1, supports, c1)
dg.add_edge(e1, informs,  q1)

report = dg.verify()
print(report.status)  # CONFORMS ✓
```

---

## Ontology structure

Two namespaces, one seam:

| Namespace | Source | Purpose |
|---|---|---|
| `dg:` | [discoursegraphs.com base grammar](https://discoursegraphs.com/docs/roam/base-grammar) | Questions, Claims, Evidence, Sources + base relations |
| `eng:` | This project (declared extension) | Decision nodes, engineering closure relations |

`dg:Question` is the join point. Questions are posed in `dg:`,
resolved by `eng:Decision` via `eng:decision`. The extension adds
without violating.

---

## Multi-agent sharing

Agents maintain distinct graphs. Sharing is governed by explicitly
declared policies stored as RDF, compiled to SPARQL at export time.

```python
alice_dg.declare_sharing_policy(
    name="delta-v-evidence",
    grantee_uri=bob.agent.uri,
    source_graph_uri=alice_dg.local_graph_uri,
    include_types=[DG.Evidence],
    exclude_nodes=[alice_e2],   # hidden — Bob cannot see or infer this
)

# push path
exported, sparql = alice_dg.export_policy("delta-v-evidence", bob.agent.uri)
bob_dg.ingest(exported, alice.agent.uri)

# pull path (equivalent)
bob_dg.pull_from(alice_dg, "delta-v-evidence")
```

Boundary invariants are formally asserted after every export:
- No excluded node appears in the exported graph
- All discourse edges are endpoint-bounded within the permitted set
- The policy graph is structurally isolated from the data store

---

## Project layout

```
discourse-graph/
├── discourse_graph/
│   ├── namespaces.py       DG, ENG Namespace objects
│   ├── ontology_dg.py      OWL 2 DL — dg: (base grammar)
│   ├── ontology_eng.py     OWL 2 DL — eng: (extension)
│   ├── shapes.py           SHACL shapes (QS-1 CS-1 ES-1 ES-2 SS-1 IS-1 DS-1)
│   ├── models.py           Pydantic node models (primary API)
│   ├── agent.py            Agent dataclass
│   ├── graph.py            DiscourseGraph class
│   ├── policy.py           SharingPolicy compilation
│   ├── report.py           ValidationReport (Pydantic, JSON-serializable)
│   └── viz.py              networkx + matplotlib visualization
├── tests/
├── notebooks/
│   └── discourse_graph_demo.py   marimo demo notebook
└── docs/
    ├── ARCHITECTURE.md
    ├── REQUIREMENTS.md
    ├── DESIGN.md
    └── BOM.md
```

---

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
# create and activate virtual environment
uv venv
source .venv/bin/activate       # macOS / Linux
.venv\Scripts\activate          # Windows

# install package with all dependencies
uv pip install -e ".[dev,notebook]"
```

### Running tests

```bash
pytest --cov=discourse_graph --cov-report=term-missing
```

### Running the demo notebook

```bash
marimo edit notebooks/discourse_graph_demo.py
```

---

## Namespace stubs

Both `http://example.org/dg/1.0/` and `http://example.org/eng/1.0/` are
W3C example IRIs used as placeholders. Replace with firm-controlled HTTPS
IRIs or registered PURLs before production use.

---

## Documentation

Full design documentation is in `docs/`:

| File | Contents |
|---|---|
| `ARCHITECTURE.md` | ConOps, layer diagram, policy pipeline, multi-agent state |
| `REQUIREMENTS.md` | Functional requirements with IDs, invariants |
| `DESIGN.md` | Ontology Turtle, SHACL Turtle, class API, notebook spec |
| `BOM.md` | Dependencies, pyproject.toml |

---

## Relationship to discoursegraphs.com

This package is an independent implementation of the
[discoursegraphs.com](https://discoursegraphs.com) information model,
not an official product of the Homeworld Collective or the OASIS Lab.
The `dg:` ontology conforms to the published base grammar.
The `eng:` extension is original work.
