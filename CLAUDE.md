# CLAUDE.md — Development instructions for Claude Code

This file configures the Claude Code development session for the
`discourse-graph` package. Read it fully before writing any code.

---

## Project summary

A Python package implementing the discoursegraphs.com information model
as a semantic web stack (OWL 2 DL / SHACL / SPARQL / PROV-O) with a
Pydantic-first Python interface and a policy-controlled multi-agent
sharing mechanism.

The full design is in `docs/`. Read in this order:
1. `docs/ARCHITECTURE.md` — ConOps, layers, policy pipeline
2. `docs/REQUIREMENTS.md` — all functional requirements with IDs
3. `docs/DESIGN.md` — ontology Turtle, SHACL Turtle, class APIs, notebook spec
4. `docs/BOM.md` — dependencies, pyproject.toml

Do not write code until you have read all four documents.

---

## Environment

This project uses `uv` for environment and dependency management.

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev,notebook]"
```

Never use `pip install` directly. Always use `uv pip install`.
Never modify `pyproject.toml` without being asked.

---

## Development protocol

### Test-driven development is mandatory

Write tests before or alongside implementation code. Every public method
must have tests that map to requirement IDs from `docs/REQUIREMENTS.md`.
Test functions must be named `test_<req_id>_<description>` where possible,
e.g. `test_fr_pol_3_permitted_set_type_filter`.

### File creation order

Create files in this order. Do not skip ahead.

```
1. pyproject.toml
2. discourse_graph/__init__.py          (empty re-export stub)
3. discourse_graph/namespaces.py
4. discourse_graph/ontology_dg.py
5. discourse_graph/ontology_eng.py      (imports dg:)
6. discourse_graph/shapes.py
7. tests/test_ontology_dg.py
8. tests/test_ontology_eng.py
9. tests/test_shacl.py
10. discourse_graph/models.py
11. tests/test_models.py
12. discourse_graph/agent.py
13. tests/test_agent.py
14. discourse_graph/report.py
15. discourse_graph/policy.py
16. discourse_graph/graph.py
17. tests/test_graph.py
18. tests/test_policy.py
19. tests/test_ingest.py
20. tests/test_invariants.py
21. discourse_graph/viz.py
22. notebooks/discourse_graph_demo.py
```

Run `pytest` after each pair (implementation + test file). Do not proceed
to the next file if tests are failing.

### Ask before proceeding past a checkpoint

Stop and ask for review at these checkpoints:
- After step 9 (all ontology + shapes tests passing)
- After step 13 (models + agent tests passing)
- After step 20 (all core tests passing, before viz and notebook)
- After step 22 (complete)

---

## Architecture constraints — enforce these without exception

### INV-P1 through INV-P5 are non-negotiable

These invariants are documented in `docs/REQUIREMENTS.md` under "Invariants".
They must be expressed as Python `assert` statements in `export_policy()`
AND as standalone tests in `test_invariants.py`.

### `_policy` must be structurally isolated from `_store`

`DiscourseGraph._policy` is a standalone `rdflib.Graph` instance.
It must NEVER be:
- passed to `self._store.get_context()`
- added via `self._store.addN()`
- included in `self._flat_graph()`
- referenced in any SPARQL query string

This structural isolation IS the enforcement mechanism for INV-P3.
A linter comment `# INV-P3: _policy never enters _store` must appear
at every point where `_store` is written to.

### No SPARQL in user-facing code

The only method that generates a SPARQL string is `_compile_policy()`.
No other method may construct, accept, or emit a SPARQL string.
SPARQL is an implementation detail of the policy layer.

### `dg:` namespace conformance

The `dg:` ontology (`ontology_dg.py`) must not contain:
- `dg:answers`
- `dg:cites`
- Any predicate not in the discoursegraphs.com base grammar

If you are tempted to add a predicate to `dg:`, add it to `eng:` instead
or raise a question in a comment for human review.

### Pydantic is the primary API

`DiscourseGraph.add(node: DiscourseNode)` is the primary write method.
`add_node(node_type, content, label)` is a secondary method for internal
and test use. The notebook demo must use only `add()` — never `add_node()`.

### `eng:Decision` requires `eng:decision` and `eng:justification` edges

A `Decision` node is only meaningful when connected. The SHACL shape DS-1
enforces this at graph validation time. The Pydantic model alone is
insufficient — the edge requirements can only be checked after the edges
are added. The notebook must call `verify()` after adding Decision edges
and assert conformance before proceeding.

---

## Key design decisions — do not relitigate these

These were decided explicitly and are recorded in `docs/ARCHITECTURE.md`.
Do not propose alternatives without flagging them as deviations.

| Decision | Rationale |
|---|---|
| `dg:Question` is the seam between `dg:` and `eng:` | Only shared type; `eng:Decision` resolves it via `eng:decision` |
| Policy stored as RDF in `_policy`, compiled to SPARQL | Alice writes Python; the system produces inspectable formal artifacts |
| Named-graph policy granularity (not node-level) | Cleaner access boundary; Alice organizes at write time |
| Edge-bounding rule on export | `(s,p,o)` exported iff `s ∈ permitted ∧ (isLiteral(o) ∨ p ∉ discourse_preds ∨ o ∈ permitted)` |
| `verify_on_write` flag | Structural checks at write time; relational SHACL deferred to `verify()` |
| Pydantic + SHACL redundancy | Pydantic catches at call site; SHACL catches in serialized graph; both required |

---

## Namespace stubs

Both namespaces are W3C example IRIs — placeholders only.

```
http://example.org/dg/1.0/    →  replace with firm-controlled IRI
http://example.org/eng/1.0/   →  replace with firm-controlled IRI
```

Every file that declares these IRIs must carry this comment:
```python
# NAMESPACE STUB: replace with firm-controlled IRI before production use.
```

---

## Demo notebook requirements

The notebook is `notebooks/discourse_graph_demo.py` (marimo format).

### Narrative contract

The notebook tells a story in five acts (see `docs/ARCHITECTURE.md` §Demo
narrative arc). The acts must be clearly delimited by marimo `mo.md()` cells
with act headings. The audience is semantic web practitioners; do not explain
what RDF is.

### Act 3 is the pedagogical payoff

Act 3 (cells 12–14) must show:
1. Alice's Python call to `declare_sharing_policy()`
2. The Turtle serialization of `alice_dg._policy` — print it
3. The compiled SPARQL string from `_compile_policy()` — print it

This is the "lift the hood" moment. The audience sees that their Python
call produced formal, inspectable artifacts. This must not be skipped
or compressed.

### Assertions are documentation

Every `assert` in the notebook is documentation of a system property.
Label each one with the invariant ID it demonstrates:

```python
# INV-P1: excluded node E2 absent from exported graph
assert not any(exported.triples((alice_e2, None, None)))
```

### Domain content

Use exactly the content specified in `docs/DESIGN.md` §8 Domain content.
Do not invent alternative content. The propulsion trade study scenario
was chosen deliberately to make the `eng:Decision` node's purpose clear.

---

## Style

- Scientific Python: `numpy`-style docstrings, type annotations on all
  public methods, no frameworks beyond those in `docs/BOM.md`
- Rust-style naming for constants: `ONTOLOGY_TTL`, `SHACL_TTL`,
  `NODE_TYPE_MAP`, `DISCOURSE_PREDICATES`
- All Turtle strings are module-level constants, not inline in functions
- No `print()` in library code — only in notebook cells and test fixtures
  when diagnosing failures
- Prefer `frozenset` for sets that must not be mutated after construction

---

## Git

Initialize the repo with:

```bash
git init
git add .
git commit -m "chore: initial project scaffold from design documents"
```

Commit after each passing checkpoint. Commit messages follow
conventional commits: `feat:`, `test:`, `fix:`, `docs:`, `chore:`.
