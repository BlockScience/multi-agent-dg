# WORKPLAN.md — Discourse Graph Package

Active build document. Tracks what to implement, in what order, how to
verify it, and where the critical constraints live. Read alongside
`CLAUDE.md` (session config) and `docs/REQUIREMENTS.md` (requirement IDs
referenced throughout).

---

## Collaboration model

| Role | Responsibility |
|---|---|
| **You (human)** | Review and approve each WP plan before implementation begins; run commands; QA at each checkpoint |
| **Claude** | Present a WP-level plan for approval, then implement all files in that WP after approval |

### Session protocol

1. **Plan phase (before each WP):** Claude presents a detailed plan for the WP — file-by-file breakdown, design decisions, test strategy, known risks. You review, request changes, and explicitly approve before any code is written.
2. **Implementation phase (after approval):** Claude writes all files in the WP following the approved plan and the file creation order in `CLAUDE.md`. Tests written alongside implementation.
3. **QA phase (checkpoint):** You run `pytest` against the completed WP and work through the QA checklist. No work on the next WP begins until the checkpoint passes.
4. Commits happen at each checkpoint in conventional-commit format.

The approval gate is at the **WP level**: approve the plan → implement the WP → QA → approve the next plan.

**Mid-WP escalation rule:** If during implementation a question arises that requires adjusting or reinterpreting the design documents, Claude stops immediately, describes the issue, and waits for resolution before writing any further code. Do not patch around design ambiguities — surface them.

**Design doc change log rule:** Any change to a design document (`docs/ARCHITECTURE.md`, `docs/REQUIREMENTS.md`, `docs/DESIGN.md`, `docs/BOM.md`) must be accompanied by a new entry appended to the change log at the bottom of that document. Format: `| YYYY-MM-DD | <what changed> | <why / decision trigger> |`. Append only — do not edit past records.

### What Claude will not do without being asked

- Modify `pyproject.toml`
- Proceed past a checkpoint without explicit approval
- Add predicates to `dg:` (only to `eng:`, or raise a question)
- Use `pip install` instead of `uv pip install`
- Write SPARQL strings outside `_compile_policy()`
- Use `add_node()` in the notebook (only `add()`)

---

## Architecture constraints — read before writing any code

### INV-P1 through INV-P5 (non-negotiable invariants)

| ID | Statement | Enforced by |
|---|---|---|
| INV-P1 | No excluded node URI appears as subject or object of any discourse edge in the exported graph | `assert` in `export_policy()` + `test_invariants.py` |
| INV-P2 | Every discourse edge `(s,p,o)` in the export satisfies `s ∈ permitted ∧ o ∈ permitted` | `assert` in `export_policy()` + `test_invariants.py` |
| INV-P3 | `_policy is not _store` — object identity, not equality | `assert` in `export_policy()` + `test_invariants.py` |
| INV-P4 | `_policy` is never passed to any `ConjunctiveGraph` method | Linter comment `# INV-P4: _policy never enters _store` at every `_store` write site; verified in code review at CP-3 |
| INV-P5 | `verify()` never includes `_policy` in its validation target | `_flat_graph()` implementation; verified in `test_invariants.py` |

### `_policy` structural isolation

The comment `# INV-P3: _policy never enters _store` must appear at every
site where `_store` is written to. Any line that passes `_policy` to
`_store.get_context()`, `_store.addN()`, or any SPARQL query string is a
critical defect. This isolation IS the policy enforcement mechanism.

### No SPARQL in user-facing code (NFR-4)

The only method that constructs a SPARQL string is `_compile_policy()` in
`graph.py`. No other method, test fixture, or notebook cell may construct,
accept, or emit a SPARQL string. SPARQL is an implementation detail.

### `dg:` namespace conformance (FR-ONT-DG-5)

`ontology_dg.py` must not declare `dg:answers`, `dg:cites`, or any
predicate not in the discoursegraphs.com base grammar. Engineering closure
predicates go in `eng:`. Checked in `test_ontology_dg.py`.

### Pydantic is the primary API (FR-PYD-3)

`DiscourseGraph.add(node: DiscourseNode)` is the primary write method.
The notebook must use `add()` exclusively — never `add_node()`.
`add_node()` is for tests and internal use only.

---

## WP-1 — Ontology and SHACL foundation

**Checkpoint CP-1: after step 9. All ontology + shapes tests must pass
before any models or graph code is written.**

### Objectives

- Establish `dg:` ontology conformant to the discoursegraphs.com base grammar.
- Establish `eng:` extension with `owl:imports <dg:>`.
- Establish SHACL shapes for all 10 shapes (QS-1 through OP-1).
- Verify shapes are independently testable without the OWL ontology.
- Verify `dg:` contains no forbidden predicates.

### Files to create, in order

| Step | File | Key content |
|---|---|---|
| 1 | `pyproject.toml` | From `docs/BOM.md` stub — do not modify after creation |
| 2 | `discourse_graph/__init__.py` | Empty re-export stub only |
| 3 | `discourse_graph/namespaces.py` | `DG`, `ENG` Namespace objects; `load_combined_ontology()` |
| 4 | `discourse_graph/ontology_dg.py` | `DG_ONTOLOGY_TTL` constant; `load_dg_ontology() -> rdflib.Graph` |
| 5 | `discourse_graph/ontology_eng.py` | `ENG_ONTOLOGY_TTL` constant; `load_eng_ontology() -> rdflib.Graph`; `owl:imports <dg:>` |
| 6 | `discourse_graph/shapes.py` | `SHACL_TTL` constant (all 10 shapes); `load_shapes() -> rdflib.Graph` |
| 7 | `tests/test_ontology_dg.py` | FR-ONT-DG-1 through FR-ONT-DG-7 |
| 8 | `tests/test_ontology_eng.py` | FR-ONT-ENG-1 through FR-ONT-ENG-9 |
| 9 | `tests/test_shacl.py` | FR-SHACL-2 through FR-SHACL-10; valid/invalid/message for each shape |

### Tests — WP-1

#### test_ontology_dg.py

| Test name | Req ID | Assertion |
|---|---|---|
| `test_fr_ont_dg_1_parses` | FR-ONT-DG-1 | `load_dg_ontology()` returns non-empty `Graph` without parse error |
| `test_fr_ont_dg_2_question_class` | FR-ONT-DG-2 | `DG.Question` declared as `owl:Class` |
| `test_fr_ont_dg_2_claim_class` | FR-ONT-DG-2 | `DG.Claim` declared as `owl:Class` |
| `test_fr_ont_dg_2_evidence_class` | FR-ONT-DG-2 | `DG.Evidence` declared as `owl:Class` |
| `test_fr_ont_dg_2_source_class` | FR-ONT-DG-2 | `DG.Source` declared as `owl:Class` |
| `test_fr_ont_dg_3_subclass_discourse_node` | FR-ONT-DG-3 | All four node classes have `rdfs:subClassOf dg:DiscourseNode` |
| `test_fr_ont_dg_3_discourse_node_subclass_prov` | FR-ONT-DG-3 | `dg:DiscourseNode rdfs:subClassOf prov:Entity` |
| `test_fr_ont_dg_4_informs` | FR-ONT-DG-4 | `dg:informs` has domain `Evidence`, range `Question` |
| `test_fr_ont_dg_4_supports` | FR-ONT-DG-4 | `dg:supports` has domain `Evidence`, range `Claim` |
| `test_fr_ont_dg_4_opposes` | FR-ONT-DG-4 | `dg:opposes` has domain `Evidence`, range `Claim` |
| `test_fr_ont_dg_5_no_answers` | FR-ONT-DG-5 | `DG.answers` does not appear anywhere in the graph |
| `test_fr_ont_dg_5_no_cites` | FR-ONT-DG-5 | `DG.cites` does not appear anywhere in the graph |
| `test_fr_ont_dg_6_agent_class` | FR-ONT-DG-6 | `dg:Agent rdfs:subClassOf prov:Agent` |
| `test_fr_ont_dg_6_sharing_policy_class` | FR-ONT-DG-6 | `dg:SharingPolicy` declared as `owl:Class` |
| `test_fr_ont_dg_6_ingested_node_class` | FR-ONT-DG-6 | `dg:IngestedNode` declared as `owl:Class` |
| `test_fr_ont_dg_7_datatype_properties` | FR-ONT-DG-7 | `dg:content`, `dg:created`, `dg:ingestedAt`, `dg:policyName` declared as `owl:DatatypeProperty` |

#### test_ontology_eng.py

| Test name | Req ID | Assertion |
|---|---|---|
| `test_fr_ont_eng_1_parses_and_imports` | FR-ONT-ENG-1 | Parses; ontology IRI has `owl:imports <dg:>` |
| `test_fr_ont_eng_2_decision_subclass` | FR-ONT-ENG-2 | `eng:Decision rdfs:subClassOf dg:DiscourseNode` and `prov:Entity` |
| `test_fr_ont_eng_3_decision_predicate` | FR-ONT-ENG-3 | `eng:decision` has domain `Decision`, range `dg:Question` |
| `test_fr_ont_eng_4_opens_predicate` | FR-ONT-ENG-4 | `eng:opens` has domain `Decision`, range `dg:Question` |
| `test_fr_ont_eng_5_justification_predicate` | FR-ONT-ENG-5 | `eng:justification` has domain `Decision`, range `dg:DiscourseNode` |
| `test_fr_ont_eng_6_assumption_subclass_claim` | FR-ONT-ENG-6 | `eng:Assumption rdfs:subClassOf dg:Claim` |
| `test_fr_ont_eng_7_assumption_scope_property` | FR-ONT-ENG-7 | `eng:assumptionScope` declared as `owl:DatatypeProperty`, range `xsd:string` |
| `test_fr_ont_eng_8_decision_status_property` | FR-ONT-ENG-8 | `eng:decisionStatus` declared as `owl:DatatypeProperty` on `eng:Decision` |
| `test_fr_ont_eng_9_namespace_stub_comment` | FR-ONT-ENG-9 | Source file contains the namespace stub replacement notice |
| `test_fr_ont_eng_10_option_predicate` | FR-ONT-ENG-10 | `eng:option` has domain `dg:Claim`, range `dg:Question` |
| `test_seam_dg_question_only_shared` | ARCH | `eng:` must not re-declare `dg:` node classes; cross-namespace references (dg:Claim as domain) are permitted |

#### test_shacl.py

Parametrised across all 10 shapes. Pattern: valid fixture → `conforms=True`;
invalid fixture → `conforms=False`; message check → violation text contains req ID.

| Test / shape | Req ID | Additional assertion |
|---|---|---|
| QS-1 (QuestionShape) | FR-SHACL-2 | Missing `dg:content` → violation; message contains "QS-1" |
| CS-1 (ClaimShape) | FR-SHACL-3 | Missing `dg:content` → violation; message contains "CS-1" |
| ES-1 (EvidenceShape) | FR-SHACL-4 | Missing `rdfs:label` → violation; message contains "ES-1" |
| ES-2 (EvidenceRelationShape) | FR-SHACL-5 | Evidence with no `supports/opposes/informs` → violation; message contains "ES-2" |
| SS-1 (SourceShape) | FR-SHACL-6 | Missing `dg:content` → violation; message contains "SS-1" |
| IS-1 (IngestedNodeShape) | FR-SHACL-7 | Missing `prov:wasAttributedTo` → violation; message contains "IS-1" |
| DS-1 (DecisionShape) | FR-SHACL-8 | Missing `eng:decision` edge → violation; `decisionStatus "cancelled"` → violation; message contains "DS-1" |
| AS-1 (AssumptionShape) | FR-SHACL-9 | Missing `eng:assumptionScope` → violation; Assumption inherits CS-1 (missing `dg:content` also fails); message contains "AS-1" |
| OP-1 (OpensDisjointShape) | FR-SHACL-10 | `eng:decision` and `eng:opens` to same `Question` → violation; distinct targets → conforms; message contains "OP-1" |
| All shapes carry req IDs | FR-SHACL-11 | Every shape has at least one `sh:message` containing its requirement ID prefix |

### WP-1 QA checklist

Run `pytest tests/test_ontology_dg.py tests/test_ontology_eng.py tests/test_shacl.py -v`.

- [ ] All 16 `test_ontology_dg.py` tests pass.
- [ ] All 10 `test_ontology_eng.py` tests pass, including the seam test.
- [ ] All `test_shacl.py` parametrised tests pass; parametrised count covers all 10 shapes.
- [ ] `python -c "from discourse_graph.ontology_dg import load_dg_ontology; g = load_dg_ontology(); print(len(g))"` prints a non-zero triple count without error.
- [ ] `python -c "from discourse_graph.ontology_dg import DG_ONTOLOGY_TTL; assert 'dg:answers' not in DG_ONTOLOGY_TTL; assert 'dg:cites' not in DG_ONTOLOGY_TTL; print('clean')"` prints `clean`.
- [ ] `python -c "from discourse_graph.shapes import load_shapes; g = load_shapes(); print(len(g))"` prints a non-zero triple count.
- [ ] Both ontology files contain the `# NAMESPACE STUB: replace with firm-controlled IRI before production use.` comment.
- [ ] `eng:` imports `dg:` via `owl:imports` (visible in `ENG_ONTOLOGY_TTL` and confirmed by the test).
- [ ] No `eng:Question` class declared anywhere.

### Reference patterns — WP-1

- **Ontology modularity** (flexo experiments 12–13): `dg:` is the sealed upstream ontology; `eng:` extends via `owl:imports` without modifying `dg:`. The seam is intentionally narrow — `dg:Question` only.
- **Verification as separate concern**: `shapes.py` loads independently of both ontology files. `test_shacl.py` builds minimal RDF fixtures without loading the OWL ontology.

---

## WP-2 — Pydantic models and Agent identity

**Checkpoint CP-2: after step 13. Models + Agent + Report tests must pass
before any graph, policy, or ingest code is written.**

### Objectives

- Implement Pydantic node models as the primary user API.
- Implement `VerificationReport` as a Pydantic model (JSON-serializable).
- Implement `Agent` dataclass (aggregate actor — organisation/team, not individual) with deterministic URI derivation.
- Verify Python-layer type hierarchy mirrors OWL subclass hierarchy.
- Verify `to_triples()` round-trip (model → triples → SHACL verifies).

### Files to create, in order

| Step | File | Key content |
|---|---|---|
| 10 | `discourse_graph/models.py` | `DiscourseNode`, `Question`, `Claim`, `Evidence`, `Source`, `Decision`, `Assumption`; `NODE_TYPE_MAP`; `to_triples()` |
| 11 | `tests/test_models.py` | FR-PYD-1 through FR-PYD-7 |
| 12 | `discourse_graph/agent.py` | `Agent` dataclass with `uri`, `node_uri()`, `graph_uri()`, `policy_uri()` |
| 13 | `discourse_graph/report.py` + `tests/test_agent.py` | `VerificationReport` Pydantic model; Agent URI derivation and isolation tests |

Note: `report.py` is written here (step 13) because it has no dependency
on `graph.py`. This avoids circular imports when `graph.py` imports both.

### Tests — WP-2

#### test_models.py

| Test name | Req ID | Assertion |
|---|---|---|
| `test_fr_pyd_1_all_types_instantiate` | FR-PYD-1 | Each of the 6 model classes instantiates with valid fields |
| `test_fr_pyd_2_content_required` | FR-PYD-2 | All models raise `ValidationError` when `content=""` |
| `test_fr_pyd_2_label_required` | FR-PYD-2 | All models raise `ValidationError` when `label=""` |
| `test_fr_pyd_2_decision_status_valid` | FR-PYD-2 | `Decision(status="provisional")` valid; `status="cancelled"` raises `ValidationError` |
| `test_fr_pyd_2_assumption_scope_required` | FR-PYD-2 | `Assumption` without `scope` raises `ValidationError` |
| `test_fr_pyd_3_assumption_is_claim_subclass` | FR-PYD-3 | `isinstance(Assumption(...), Claim)` is `True` |
| `test_fr_pyd_3_assumption_owl_subclass` | FR-PYD-3 | `ENG.Assumption` listed as subclass of `DG.Claim` in combined ontology |
| `test_fr_pyd_5_pydantic_validates_before_rdf` | FR-PYD-5 | `ValidationError` from Pydantic is raised before any rdflib graph is touched |
| `test_fr_pyd_6_to_triples_question` | FR-PYD-6 | `Question.to_triples(uri)` includes `rdf:type dg:Question`, `dg:content`, `rdfs:label` |
| `test_fr_pyd_6_to_triples_decision` | FR-PYD-6 | `Decision.to_triples(uri)` includes `eng:decisionStatus` |
| `test_fr_pyd_6_to_triples_assumption` | FR-PYD-6 | `Assumption.to_triples(uri)` includes `eng:assumptionScope` |
| `test_fr_pyd_6_round_trip_shacl_all_types` | FR-PYD-6 | For each model type: instantiate → `to_triples()` → write to fresh `rdflib.Graph` → `pyshacl.validate` against shapes → `conforms=True` |
| `test_fr_pyd_7_verification_report_json` | FR-PYD-7 | `VerificationReport` instance serializes to JSON without error |
| `test_assumption_cs1_inherited_via_shacl` | FR-SHACL-3 | Assumption without `dg:content` fails CS-1 via SHACL subclass inheritance |
| `test_assumption_as1_scope_required` | FR-SHACL-9 | Assumption without `eng:assumptionScope` fails AS-1 |
| `test_assumption_all_three_rdf_types` | FR-PYD-6 | `Assumption.to_triples()` includes `rdf:type eng:Assumption`, `rdf:type dg:Claim`, `rdf:type dg:DiscourseNode` |
| `test_node_type_map_complete` | FR-PYD-1 | `NODE_TYPE_MAP` contains an entry for all 6 model classes |

#### test_agent.py

| Test name | Req ID | Assertion |
|---|---|---|
| `test_fr_agent_1_name_and_namespace` | FR-AGENT-1 | `Agent(name="Alice", namespace="http://a/")` stores both fields |
| `test_fr_agent_1_namespace_must_end_slash` | FR-AGENT-1 | `Agent(namespace="http://a")` raises `ValueError` |
| `test_fr_agent_2_agent_uri` | FR-AGENT-2 | `agent.uri == URIRef("http://a/agent")` |
| `test_fr_agent_2_node_uri` | FR-AGENT-2 | `agent.node_uri("q1") == URIRef("http://a/node/q1")` |
| `test_fr_agent_2_graph_uri_local` | FR-AGENT-2 | `agent.graph_uri() == URIRef("http://a/graph/local")` |
| `test_fr_agent_2_graph_uri_named` | FR-AGENT-2 | `agent.graph_uri("ingested-bob") == URIRef("http://a/graph/ingested-bob")` |
| `test_fr_agent_2_policy_uri` | FR-AGENT-2 | `agent.policy_uri("evidence-sharing") == URIRef("http://a/policy/evidence-sharing")` |
| `test_fr_agent_3_disjoint_namespaces` | FR-AGENT-3 | Alice's and Bob's URIs do not intersect for any of: `uri`, `node_uri("x")`, `graph_uri("local")`, `policy_uri("p")` |
| `test_report_conforms_status` | FR-PYD-7 | `ValidationReport(conforms=True, ...).status == "CONFORMS ✓"` |
| `test_report_violation_status` | FR-PYD-7 | `ValidationReport(conforms=False, ...).status == "VIOLATIONS FOUND ✗"` |
| `test_report_violation_ids_extracted` | FR-PYD-7 | `violation_ids()` extracts requirement IDs (e.g. "CS-1", "ES-2") from report text |

### WP-2 QA checklist

Run `pytest tests/test_models.py tests/test_agent.py -v`.

- [ ] All 17 `test_models.py` tests pass, including all 6-type SHACL round-trip tests.
- [ ] All 11 `test_agent.py` tests pass.
- [ ] `python -c "from discourse_graph.models import Assumption, Claim; a = Assumption(content='x', label='y', scope='z'); print(isinstance(a, Claim))"` prints `True`.
- [ ] `python -c "from discourse_graph.models import Decision; Decision(content='x', label='y', status='cancelled')"` raises `pydantic.ValidationError`.
- [ ] `Assumption.to_triples()` output includes all three `rdf:type` triples: `eng:Assumption`, `dg:Claim`, `dg:DiscourseNode`.
- [ ] `VerificationReport` serializes to JSON (`.model_dump()` runs without error).

### Reference patterns — WP-2

- **Pydantic for all structured data** (mtg-colors-personality-test/src): `VerificationReport`, `InferenceResult` are Pydantic models for JSON-serializability. Same pattern applies here.
- **SHACL-before-write guard**: `verify_on_write=True` is a guard that gates write transitions — the Pydantic `ValidationError` is the Python-layer guard; SHACL is the RDF-layer guard. Neither replaces the other.
- **Structured views as verification**: `to_triples()` makes the Pydantic-to-RDF round-trip testable. The SHACL round-trip test is the verification step.

---

## WP-3 — Core graph, policy, and ingest

**Checkpoint CP-3: after step 20. All core tests must pass before
visualization or notebook work begins. Most complex work package.**

### Objectives

- Implement `DiscourseGraph` with `_store` / `_policy` structural isolation.
- Implement `declare_sharing_policy()` and `_compile_policy()`.
- Implement `export_policy()` with INV-P1/P2/P3 asserts.
- Implement `ingest()` and `pull_from()`.
- Verify all 5 invariants as standalone unit tests.

### Files to create, in order

| Step | File | Key content |
|---|---|---|
| 14 | *(confirm `report.py` complete — no changes needed)* | — |
| 15 | `discourse_graph/policy.py` | `DISCOURSE_PREDICATES` frozenset; policy helper functions if factored out |
| 16 | `discourse_graph/graph.py` | `DiscourseGraph` full implementation: `_DISCOURSE_PREDICATES`, `_PRED_DOMAIN_RANGE`, `_VALID_NODE_TYPES`; all public methods |
| 17 | `tests/test_graph.py` | FR-DG-1 through FR-DG-13 |
| 18 | `tests/test_policy.py` | FR-POL-1 through FR-POL-12; INV-P1/P2/P3 |
| 19 | `tests/test_ingest.py` | FR-ING-1 through FR-ING-3 |
| 20 | `tests/test_invariants.py` | INV-P1 through INV-P5, standalone minimal fixtures |

### Tests — WP-3

#### test_graph.py

> **Change 2026-03-19:** Added two FR-DG-5 test rows pinning that
> `_check_add_edge()` validates only `DISCOURSE_PREDICATES`; non-discourse
> predicates are unconditionally accepted.

| Test name | Req ID | Assertion |
|---|---|---|
| `test_fr_dg_1_store_is_conjunctive_graph` | FR-DG-1 | `type(dg._store).__name__ == "ConjunctiveGraph"` |
| `test_fr_dg_2_policy_not_in_store` | FR-DG-2 | `dg._policy is not dg._store`; `dg._policy` not in `dg._store.contexts()` |
| `test_fr_dg_3_verify_on_write_flag` | FR-DG-3 | Constructor accepts `verify_on_write=True/False` |
| `test_fr_dg_4_add_node_invalid_type_raises` | FR-DG-4 | `verify_on_write=True`: `add_node(URIRef("bad:type"), ...)` raises `ValueError` |
| `test_fr_dg_4_add_node_empty_content_raises` | FR-DG-4 | `verify_on_write=True`: `add_node(..., content="", ...)` raises `ValueError` |
| `test_fr_dg_5_add_edge_invalid_predicate_raises` | FR-DG-5 | `verify_on_write=True`: `add_edge(s, URIRef("bad:pred"), o)` raises `ValueError` |
| `test_fr_dg_5_add_edge_domain_violation_raises` | FR-DG-5 | Edge with wrong subject type raises `ValueError` |
| `test_fr_dg_5_non_discourse_predicate_accepted` | FR-DG-5 | `verify_on_write=True`: `add_edge(s, PROV.wasDerivedFrom, o)` does NOT raise |
| `test_fr_dg_5_discourse_predicate_domain_violation_raises` | FR-DG-5 | `verify_on_write=True`: `add_edge(evidence_uri, DG.supports, question_uri)` raises `ValueError` (wrong domain) |
| `test_fr_dg_6_unconditional_write` | FR-DG-6 | `verify_on_write=False`: malformed node writes without raising |
| `test_fr_dg_7_relational_shacl_deferred` | FR-DG-7 | Adding `dg:Evidence` node without relations does not raise in `add_node`; violation appears in `verify()` |
| `test_fr_dg_8_add_node_writes_required_triples` | FR-DG-8 | `add_node()` writes `rdf:type`, `rdf:type dg:DiscourseNode`, `rdf:type prov:Entity`, `dg:content`, `rdfs:label`, `dg:created` |
| `test_fr_dg_8_add_primary_matches_add_node` | FR-DG-8 | `add(Question(...))` writes the same triples as `add_node(DG.Question, ...)` |
| `test_fr_dg_9_add_node_default_graph` | FR-DG-9 | Without `graph_uri`, node written to `agent.graph_uri("local")` |
| `test_fr_dg_10_add_edge_default_graph` | FR-DG-10 | Without `graph_uri`, edge written to `agent.graph_uri("local")` |
| `test_fr_dg_11_verify_returns_report` | FR-DG-11 | `verify()` returns `VerificationReport` instance |
| `test_fr_dg_11_verify_excludes_policy` | FR-DG-11 | Triples in `_policy` do not appear in the graph passed to `pyshacl.validate` |
| `test_fr_dg_12_named_graphs` | FR-DG-12 | `named_graphs()` returns a list of `URIRef` values |
| `test_fr_dg_13_triple_count` | FR-DG-13 | `triple_count()` returns correct count; `triple_count(graph_uri)` returns scoped count |

#### test_policy.py

| Test name | Req ID | Assertion |
|---|---|---|
| `test_fr_pol_1_policy_in_policy_only` | FR-POL-1 | Policy triples exist in `_policy`; same URIs absent from all `_store` contexts |
| `test_fr_pol_2_policy_triples_complete` | FR-POL-2 | Declared policy has `dg:SharingPolicy`, `dg:policyName`, `dg:grantee`, `dg:sourceGraph`, `dg:created` |
| `test_fr_pol_3_permitted_set_type_filter` | FR-POL-3 | `include_types=[DG.Evidence]` → permitted set includes all Evidence nodes in source graph |
| `test_fr_pol_4_type_matches` | FR-POL-4 | Nodes matched by `include_types` are in permitted; non-matching types are not |
| `test_fr_pol_5_explicit_includes_filtered` | FR-POL-5 | Absent node silently dropped from permitted; present node included |
| `test_fr_pol_6_excludes_precedence` | FR-POL-6 | `include_nodes=[E2]` and `exclude_nodes=[E2]` → E2 not in permitted |
| `test_fr_pol_7_compile_returns_sparql_string` | FR-POL-7 | `_compile_policy()` returns non-empty string starting with `CONSTRUCT` |
| `test_fr_pol_8_sparql_scoped_to_graph` | FR-POL-8 | Generated SPARQL contains `GRAPH <source_graph_uri>` |
| `test_fr_pol_9_edge_bounding_evidence` | FR-POL-9 | E1→C1 `dg:supports` edge absent from Policy A export (C1 not in permitted) |
| `test_fr_pol_9_edge_bounding_claim` | FR-POL-9 | No incoming discourse edges on C1 in Policy B export |
| `test_fr_pol_10_grantee_mismatch_raises` | FR-POL-10 | `export_policy("p", wrong_grantee_uri)` raises `ValueError` |
| `test_fr_pol_11_postconditions_asserted` | FR-POL-11 | Manually inject a bad triple, confirm `export_policy()` raises `AssertionError` |
| `test_fr_pol_12_pull_from_calls_ingest` | FR-POL-12 | `bob.pull_from(alice, "evidence-sharing")` → ingested triples in Bob's `_store` |
| `test_policy_isolation` | INV-P3 | `alice._policy is not alice._store` |
| `test_policy_not_in_store` | INV-P4 | Policy URI absent from all contexts in `alice._store` |
| `test_two_policies_independent` | FR-POL-3 | Policy A and B permitted sets are disjoint |
| `test_inv_p1_excluded_absent` | INV-P1 | E2 absent from export as both subject and object |
| `test_inv_p2_all_edges_bounded` | INV-P2 | Every discourse edge `(s,p,o)` in export: `s ∈ permitted ∧ o ∈ permitted` |

#### test_ingest.py

| Test name | Req ID | Assertion |
|---|---|---|
| `test_fr_ing_1_copy_triples_to_named_graph` | FR-ING-1 | All triples from subgraph appear in `bob:graph/ingested-alice` |
| `test_fr_ing_1_graph_name_slug` | FR-ING-1 | Named graph URI is `agent.graph_uri("ingested-<alice_slug>")` |
| `test_fr_ing_2_ingested_node_type` | FR-ING-2 | Each `dg:DiscourseNode` in subgraph gets `rdf:type dg:IngestedNode` in Bob's store |
| `test_fr_ing_2_prov_attributed` | FR-ING-2 | Each ingested node has `prov:wasAttributedTo <alice_agent_uri>` |
| `test_fr_ing_2_ingested_at_datetime` | FR-ING-2 | Each ingested node has `dg:ingestedAt` as `xsd:dateTime` literal |
| `test_fr_ing_3_returns_graph_uri` | FR-ING-3 | `ingest()` returns a `URIRef` for the new named graph |
| `test_is1_passes_after_ingest` | FR-SHACL-7 | After `ingest()`, `bob.verify()` passes IS-1 for all ingested nodes |

#### test_invariants.py

Standalone, domain-agnostic. Build minimal fixtures — do not use
Alice/Bob demo content. These tests are documentation of system properties.

| Test name | Invariant | Assertion |
|---|---|---|
| `test_inv_p1_excluded_node_absent_subject` | INV-P1 | Excluded node does not appear as `?s` in any discourse triple of export |
| `test_inv_p1_excluded_node_absent_object` | INV-P1 | Excluded node does not appear as `?o` in any discourse triple of export |
| `test_inv_p2_all_discourse_edges_endpoint_bounded` | INV-P2 | For every discourse edge in export: `s ∈ permitted ∧ o ∈ permitted` |
| `test_inv_p3_policy_object_identity` | INV-P3 | `dg._policy is not dg._store` immediately after construction |
| `test_inv_p3_policy_not_a_context_in_store` | INV-P3 | `dg._policy` not returned by `dg._store.contexts()` at any point |
| `test_inv_p4_linter_comment_present` | INV-P4 | `graph.py` source contains `# INV-P3: _policy never enters _store` (read file, grep string) |
| `test_inv_p5_verify_excludes_policy_triples` | INV-P5 | Add triple directly to `_policy`; call `verify()`; confirm triple absent from validation graph |

### WP-3 QA checklist

Run `pytest tests/test_graph.py tests/test_policy.py tests/test_ingest.py tests/test_invariants.py -v`.

- [ ] All tests pass. Expect 50+ tests across the four files.
- [ ] Manual isolation check: in `graph.py`, every line that calls `_store.addN`, `_store.get_context`, `_store.add`, or constructs a SPARQL string has the `# INV-P3: _policy never enters _store` comment. None of them reference `_policy`.
- [ ] Manual SPARQL check: grep `graph.py` for `"SELECT"`, `"CONSTRUCT"`. Each must appear only inside `_compile_policy()`. No other method contains a SPARQL fragment.
- [ ] Manual Alice demo REPL run: create Alice and Bob, add Alice's 6 nodes + 7 edges (from `docs/DESIGN.md §8`), call `alice_dg.verify()` → `conforms=True`, export Policy A (E1 in, E2 out, E1→C1 edge absent), export Policy B (C1 in, E1/E2 out, no incoming discourse edges on C1), have Bob ingest both, call `bob_dg.verify()` → `conforms=True`.
- [ ] Confirm `export_policy()` raises `AssertionError` if you manually corrupt the export to include an excluded node.
- [ ] Confirm `export_policy()` raises `ValueError` with a non-matching `grantee_uri`.

### Reference patterns — WP-3

- **ConjunctiveGraph with named graph separation** (mtg-colors-personality-test/src): `_store` holds all queryable named graphs; `_policy` is structurally outside. One ConjunctiveGraph for live data, one isolated Graph for metadata that must never contaminate queries.
- **SHACL-before-write** (mtg-colors): `verify_on_write=True` is a version of build-temp-graph / validate / commit-only-if-conforms, constrained to structural checks.
- **Conflict non-commutativity** (flexo experiments): `_store` accepts everything unconditionally; `verify()` is the semantic check layer. The two layers are not redundant — they serve different invariants at different times.
- **SHACL + SPARQL oracle two-layer verification**: SHACL validates node structure; `_compile_policy()` enforces the policy boundary. These are the two oracle layers.

---

## WP-4 — Visualization and demo notebook

**Checkpoint CP-4: after step 22. Demo must run end-to-end without errors
and all in-notebook assertions must pass.**

### Objectives

- Implement `visualize_graph()` and `visualize_sharing()` with correct node colors.
- Write the marimo notebook in five acts using exactly the domain content from `docs/DESIGN.md §8`.
- Verify all in-notebook assertions pass (INV-P1/P2/P3, conformance, OP-1).
- Confirm Act 3 "lift the hood" cells print both `_policy` Turtle and compiled SPARQL.

### Files to create, in order

| Step | File | Key content |
|---|---|---|
| 21 | `discourse_graph/viz.py` | `visualize_graph()`, `visualize_sharing()` |
| 22 | `notebooks/discourse_graph_demo.py` | marimo notebook, 29 cells, five acts, exact domain content from `DESIGN.md §8` |

### Tests — WP-4

Add smoke tests (new file `tests/test_viz.py` or append to `test_graph.py`):

| Test name | Req ID | Assertion |
|---|---|---|
| `test_fr_viz_1_returns_axes` | FR-VIZ-1 | `visualize_graph(dg)` returns `matplotlib.axes.Axes` |
| `test_fr_viz_2_node_color_map_complete` | FR-VIZ-2 | Color map in `viz.py` has entries for all 6 node types including `Decision` and `Assumption` |
| `test_fr_viz_3_edge_label_local_name` | FR-VIZ-3 | Edge label for `dg:supports` is `"supports"` (local name extraction) |
| `test_fr_viz_4_ingested_node_distinguished` | FR-VIZ-4 | `dg:IngestedNode` nodes get `edgecolors='darkorange'` |

### Notebook QA — act-by-act walkthrough

Run `marimo run notebooks/discourse_graph_demo.py`.

#### Act 1 (cells 1–5): Setup

- [ ] Cell 0: BLUF hook renders. Opening sentence bold. Link to `https://discoursegraphs.com/docs/roam/base-grammar` present. Layer table and two-policy summary visible below.
- [ ] Cell 1: Only `discourse_graph` imports visible. No `rdflib`, `pyshacl`, or SPARQL imports in the cell.
- [ ] Cell 2: Prints triple counts for `dg:` and `eng:` ontologies (non-zero).
- [ ] Cell 3: Prints shape names with requirement IDs (QS-1 through OP-1).
- [ ] Cell 4: Prints Alice and Bob namespace IRIs.
- [ ] Cell 5: Constructs `alice_dg` with `verify_on_write=False`, `bob_dg` with `verify_on_write=True`.

#### Act 2 (cells 6–11): Individual graphs

- [ ] Cell 6: Alice's 6 nodes added via `add()` (not `add_node()`); 10 edges added.
  - Q1 "What propulsion architecture minimises total system mass?"
  - C1 "Chemical bipropellant (MMH/NTO) is baseline"
  - C2 "Solar electric propulsion not viable (schedule constraint)"
  - E1 "Delta-V budget analysis: 3.2 km/s"
  - E2 "Schedule constraint: SEP requires >90 days"
  - D1 "Select MMH/NTO bipropellant" with `eng:opens → Q2`
- [ ] Cell 7: `alice_dg.verify()` → `assert report.conforms` passes.
- [ ] Cell 8: Alice's graph renders; D1 and `eng:opens` edge to Q2 visible.
- [ ] Cell 9: Bob's 4 initial nodes added (Q2, C3, E3, D2).
- [ ] Cell 10: `bob_dg.verify()` → `assert report.conforms` passes.
- [ ] Cell 11: Bob's pre-sharing graph renders (4 nodes only).

#### Act 3 (cells 12–17): Policy declaration — the pedagogical payoff

- [ ] Cell 12: `alice_dg.declare_sharing_policy("evidence-sharing", ...)` called; policy URI printed.
- [ ] Cell 13: `alice_dg._policy.serialize(format="turtle")` printed. Output must show `dg:SharingPolicy`, `dg:grantee`, `dg:sourceGraph`, include/exclude lists.
- [ ] Cell 14: `_compile_policy(...)` output printed. Must show `CONSTRUCT`, `GRAPH <alice:graph/local>`, `VALUES ?s { ... }`, and the edge-bounding `FILTER`.
- [ ] Cell 15: `alice_dg.declare_sharing_policy("arch-claim", ...)` called; second policy URI printed.
- [ ] Cell 16: Updated `_policy` Turtle shows two `dg:SharingPolicy` individuals.
- [ ] Cell 17: Policy B SPARQL printed. Contrast visible: `includesNode` for C1, no `includesType`.

#### Act 4 (cells 18–26): Sharing

- [ ] Cell 18: `export_policy("evidence-sharing", bob_agent.uri)` returns `(exported_A, sparql_A)`.
  - `# INV-P1: excluded node E2 absent from exported graph` — assert passes.
  - `# INV-P2: E1→C1 edge absent (C1 not in permitted set)` — assert passes.
- [ ] Cell 19: `bob_dg.ingest(exported_A, alice_agent.uri)` returns ingested graph URI; printed.
- [ ] Cell 20: Bob adds `dg:informs` E1→Q2 and `eng:justification` D2→E1.
- [ ] Cell 21: `export_policy("arch-claim", bob_agent.uri)` returns `(exported_B, sparql_B)`.
  - C1 present; E1/E2 absent; no incoming discourse edges on C1.
- [ ] Cell 22: Bob ingests C1 from Policy B.
- [ ] Cell 23: Bob creates A1 (`eng:Assumption`) with `prov:wasDerivedFrom` C1* and declared scope.
- [ ] Cell 24: `bob_dg.add_edge(bob_D2, ENG.justification, bob_A1)` — D2 grounded in A1.
- [ ] Cell 25: `bob_dg.verify()` → `assert report.conforms` passes; AS-1 and IS-1 both satisfied.
- [ ] Cell 26: INV-P1/P2/P3 assertions printed for both exports with invariant ID labels.
  - `# INV-P1:`, `# INV-P2:`, `# INV-P3:` comments label each assert.
  - OP-1 disjointness check on D1 (`decision_targets.isdisjoint(opens_targets)`) passes.

#### Act 5 (cells 27–28): Visualization

- [ ] Cell 27: `visualize_sharing(alice_dg, bob_dg, shared_node_uris)` renders side-by-side figure.
  - Alice's panel shows all nodes including E2 (not shared) and D1 (not shared).
  - Bob's panel shows E1* and C1* with orange borders. A1 noted as "(assumed)".
- [ ] Cell 28: Epistemic status table renders with all 7 rows:

| Node in Bob | Origin | Bob's epistemic status |
|---|---|---|
| Q2, C3, E3, D2 | Bob (local) | Bob's own reasoning |
| E1* | Alice via Policy A | Empirical finding, provenance traced |
| C1* | Alice via Policy B | Ingested claim, no visible backing |
| A1 | Bob (derived) | Explicit Assumption from C1*, scope declared |

### WP-4 QA checklist

- [ ] `pytest tests/test_viz.py -v` (or smoke tests) pass.
- [ ] `marimo run notebooks/discourse_graph_demo.py` runs end-to-end without errors.
- [ ] All `assert` statements in the notebook pass.
- [ ] Act 3 cells print non-empty Turtle (contains `dg:SharingPolicy`) and non-empty SPARQL (contains `CONSTRUCT`).
- [ ] No `add_node()` calls in the notebook. Grep to confirm.
- [ ] No SPARQL strings constructed in notebook code. `CONSTRUCT`/`SELECT`/`WHERE` appear only in printed output, not in code that builds them.
- [ ] Namespace stub comment present in `ontology_dg.py`, `ontology_eng.py`, `namespaces.py`. Grep to confirm.

### Reference patterns — WP-4

- **Structured views as verification** (mtg-colors): `visualize_sharing()` makes the policy outcome visually verifiable. The audience sees E2 and D1 are absent from Bob's panel without inspecting RDF.
- **Event logging / print-as-documentation**: every `add()`, `ingest()`, and `export_policy()` call in the notebook is followed by a print confirming what was written. This is documentation, not debugging.

---

## Checkpoint summary

| CP | After step | Condition to proceed | Commit message |
|---|---|---|---|
| CP-1 | 9 | All ontology + shapes tests green | `feat: add dg: and eng: ontologies and SHACL shapes` |
| CP-2 | 13 | Models + Agent + Report tests green | `feat: add Pydantic node models, Agent, ValidationReport` |
| CP-3 | 20 | All core graph/policy/ingest/invariant tests green | `feat: add DiscourseGraph with policy-controlled sharing` |
| CP-4 | 22 | Viz + notebook complete, all assertions pass | `feat: add visualization and marimo demo notebook` |

---

## File creation index

| Step | File | WP |
|---|---|---|
| 1 | `pyproject.toml` | WP-1 |
| 2 | `discourse_graph/__init__.py` | WP-1 |
| 3 | `discourse_graph/namespaces.py` | WP-1 |
| 4 | `discourse_graph/ontology_dg.py` | WP-1 |
| 5 | `discourse_graph/ontology_eng.py` | WP-1 |
| 6 | `discourse_graph/shapes.py` | WP-1 |
| 7 | `tests/test_ontology_dg.py` | WP-1 |
| 8 | `tests/test_ontology_eng.py` | WP-1 |
| 9 | `tests/test_shacl.py` | WP-1 → **CP-1** |
| 10 | `discourse_graph/models.py` | WP-2 |
| 11 | `tests/test_models.py` | WP-2 |
| 12 | `discourse_graph/agent.py` | WP-2 |
| 13 | `discourse_graph/report.py` + `tests/test_agent.py` | WP-2 → **CP-2** |
| 14 | *(confirm `report.py` complete)* | WP-3 |
| 15 | `discourse_graph/policy.py` | WP-3 |
| 16 | `discourse_graph/graph.py` | WP-3 |
| 17 | `tests/test_graph.py` | WP-3 |
| 18 | `tests/test_policy.py` | WP-3 |
| 19 | `tests/test_ingest.py` | WP-3 |
| 20 | `tests/test_invariants.py` | WP-3 → **CP-3** |
| 21 | `discourse_graph/viz.py` | WP-4 |
| 22 | `notebooks/discourse_graph_demo.py` | WP-4 → **CP-4** |

---

## Change log

| Date | What changed | Why / decision trigger |
|---|---|---|
| 2026-03-19 | Initial document created | Work package structure, collaboration model, QA checklists, and reference patterns established |
| 2026-03-19 | Rename `ValidationReport` → `VerificationReport` throughout; clarify `Agent` as aggregate actor; test name `test_fr_pyd_7_validation_report_json` → `test_fr_pyd_7_verification_report_json`; CP-2 commit message updated | SHACL is deterministic machine-checked rule enforcement (verification); "validation" reserved for judgement-requiring checks. Agent is an organisation/team owning a locally consistent subgraph. |
| 2026-03-19 | Added FR-ONT-ENG-10 (`eng:option`) to WP-3 test table; WP-4 cell 6 edge count 8 → 10 | `eng:option` predicate added to make candidate options explicit in alternatives analysis |
