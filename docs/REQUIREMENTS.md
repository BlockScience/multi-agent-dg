# Requirements — Discourse Graph Package

## Scope

A Python package implementing a discourse graph information model for
systems engineering design rationale, backed by OWL 2 DL / SHACL / SPARQL,
with a policy-controlled multi-agent sharing mechanism.

Demo target: a Marimo notebook showing AliceGroup (systems architecture)
and BobGroup (propulsion subsystem) maintaining distinct, partially
overlapping discourse graphs for a lunar transfer stage propulsion trade study.

---

## Functional requirements

### FR-ONT — Ontology

#### FR-ONT-DG — dg: namespace (conformant to discoursegraphs.com base grammar)

| ID | Requirement |
|---|---|
| FR-ONT-DG-1 | The `dg:` ontology SHALL be serialised as OWL 2 DL Turtle in `ontology_dg.py`. |
| FR-ONT-DG-2 | The `dg:` ontology SHALL implement exactly the node types in the discoursegraphs.com base grammar: `dg:Question` (QUE), `dg:Claim` (CLM), `dg:Evidence` (EVD), `dg:Source`. |
| FR-ONT-DG-3 | All `dg:` node classes SHALL be subclasses of `dg:DiscourseNode`, which SHALL be a subclass of `prov:Entity`. |
| FR-ONT-DG-4 | The `dg:` ontology SHALL implement exactly the three base grammar relations: `dg:informs` (EVD→QUE), `dg:supports` (EVD→CLM), `dg:opposes` (EVD→CLM). |
| FR-ONT-DG-5 | The `dg:` ontology SHALL NOT declare `dg:answers` or `dg:cites`. These predicates have no basis in the base grammar and are replaced by `eng:` terms. |
| FR-ONT-DG-6 | The `dg:` ontology SHALL declare infrastructure classes: `dg:Agent`, `dg:SharingPolicy`, `dg:IngestedNode`. |
| FR-ONT-DG-7 | The `dg:` ontology SHALL declare datatype properties: `dg:content`, `dg:created`, `dg:ingestedAt`, `dg:policyName`. |

#### FR-ONT-ENG — eng: namespace (engineering design rationale extension)

| ID | Requirement |
|---|---|
| FR-ONT-ENG-1 | The `eng:` ontology SHALL be serialised as OWL 2 DL Turtle in `ontology_eng.py` and SHALL declare `owl:imports <http://example.org/dg/1.0/>`. |
| FR-ONT-ENG-2 | The `eng:` ontology SHALL declare `eng:Decision` as a subclass of both `dg:DiscourseNode` and `prov:Entity`. |
| FR-ONT-ENG-3 | The `eng:` ontology SHALL declare `eng:decision` with domain `eng:Decision` and range `dg:Question`. |
| FR-ONT-ENG-4 | The `eng:` ontology SHALL declare `eng:opens` with domain `eng:Decision` and range `dg:Question`, representing a downstream question opened by a decision. |
| FR-ONT-ENG-5 | The `eng:` ontology SHALL declare `eng:justification` with domain `eng:Decision` and range `dg:DiscourseNode`. |
| FR-ONT-ENG-6 | The `eng:` ontology SHALL declare `eng:Assumption` as a subclass of `dg:Claim`. An Assumption is a Claim accepted without requiring further Evidence within a declared analysis scope. |
| FR-ONT-ENG-7 | The `eng:` ontology SHALL declare `eng:assumptionScope` as a datatype property (xsd:string) with domain `eng:Assumption`. |
| FR-ONT-ENG-8 | The `eng:` ontology SHALL declare `eng:decisionStatus` as a datatype property (xsd:string) on `eng:Decision`. |
| FR-ONT-ENG-9 | The `eng:` namespace stub SHALL carry the same production replacement notice as `dg:`. |

### FR-SHACL — Validation shapes

| ID | Requirement |
|---|---|
| FR-SHACL-1 | SHACL shapes for both `dg:` and `eng:` SHALL be serialised as Turtle in a single `shapes.py`, loadable independently of the ontologies. |
| FR-SHACL-2 | `dg:QuestionShape` (QS-1): every `dg:Question` MUST have exactly one `dg:content` (xsd:string) and exactly one `rdfs:label` (xsd:string). |
| FR-SHACL-3 | `dg:ClaimShape` (CS-1): every `dg:Claim` MUST have exactly one `dg:content` and exactly one `rdfs:label`. Applies to `eng:Assumption` via SHACL subclass inheritance. |
| FR-SHACL-4 | `dg:EvidenceShape` (ES-1): every `dg:Evidence` MUST have exactly one `dg:content` and exactly one `rdfs:label`. |
| FR-SHACL-5 | `dg:EvidenceRelationShape` (ES-2): every `dg:Evidence` MUST have at least one of `dg:supports`, `dg:opposes`, or `dg:informs`. |
| FR-SHACL-6 | `dg:SourceShape` (SS-1): every `dg:Source` MUST have exactly one `dg:content` and exactly one `rdfs:label`. |
| FR-SHACL-7 | `dg:IngestedNodeShape` (IS-1): every `dg:IngestedNode` MUST have `prov:wasAttributedTo` (min 1) and `dg:ingestedAt` (xsd:dateTime, min 1). |
| FR-SHACL-8 | `eng:DecisionShape` (DS-1): every `eng:Decision` MUST have: `dg:content` ×1, `rdfs:label` ×1, `eng:decision` to a `dg:Question` (min 1), `eng:justification` to a `dg:DiscourseNode` (min 1), `eng:decisionStatus` ×1 with value in {provisional, final, superseded}. |
| FR-SHACL-9 | `eng:AssumptionShape` (AS-1): every `eng:Assumption` MUST have exactly one `eng:assumptionScope` (xsd:string). CS-1 applies via subclass inheritance and need not be restated. |
| FR-SHACL-10 | `eng:OpensDisjointShape` (OP-1): SHACL-SPARQL constraint. For any `eng:Decision`, the set of Questions targeted by `eng:opens` MUST be disjoint from the set targeted by `eng:decision`. A Decision cannot open the same Question it resolves. |
| FR-SHACL-11 | Each shape violation SHALL carry a `sh:message` prefixed with its requirement ID (e.g. "OP-1: ..."). |

### FR-AGENT — Agent identity

| ID | Requirement |
|---|---|
| FR-AGENT-1 | An `Agent` SHALL be a dataclass carrying a human-readable `name` and a base `namespace` IRI (must end with `/`). |
| FR-AGENT-2 | The `Agent` SHALL deterministically derive: `agent_uri`, `node_uri(local_id)`, `graph_uri(name)`, `policy_uri(name)` from the base namespace. |
| FR-AGENT-3 | Two distinct `Agent` instances with distinct `namespace` values SHALL produce non-overlapping URI spaces. |

### FR-PYDANTIC — Node models

| ID | Requirement |
|---|---|
| FR-PYD-1 | Each concrete node type SHALL have a Pydantic `BaseModel` subclass: `Question`, `Claim`, `Evidence`, `Source`, `Decision`, `Assumption`. |
| FR-PYD-2 | Each model SHALL carry `content: str`, `label: str` as required fields. `Decision` additionally carries `status: Literal["provisional", "final", "superseded"]`. `Assumption` additionally carries `scope: str` (maps to `eng:assumptionScope`). |
| FR-PYD-3 | `Assumption` SHALL be a subclass of the `Claim` Pydantic model, mirroring the OWL subclass relationship `eng:Assumption rdfs:subClassOf dg:Claim`. |
| FR-PYD-3 | Pydantic models SHALL be the **primary user-facing API** for node creation. `DiscourseGraph.add()` SHALL accept a Pydantic node model and return a `URIRef`. |
| FR-PYD-4 | The raw `add_node(node_type, content, label)` method SHALL remain available for programmatic and test use but SHALL NOT be the recommended API for users. |
| FR-PYD-5 | Pydantic validation SHALL run at Python call time (before any RDF is written). SHACL validation via `verify()` is a second independent layer over the serialized graph. Both layers enforcing the same constraints is intentional. |
| FR-PYD-6 | A Pydantic model instance SHALL be serializable to a dict of RDF triple tuples via a `.to_triples(uri)` method, enabling round-trip testing between the Python and RDF representations. |
| FR-PYD-7 | The `ValidationReport` returned by `verify()` SHALL be a Pydantic model, not a plain dataclass, so that it is serializable to JSON for logging and downstream tooling. |



| ID | Requirement |
|---|---|
| FR-DG-1 | `DiscourseGraph` SHALL use an `rdflib.ConjunctiveGraph` as its internal quad store (`_store`). |
| FR-DG-2 | `DiscourseGraph` SHALL maintain a private `rdflib.Graph` (`_policy`) that is NEVER added to `_store`. This is the structural enforcement mechanism for boundary policy isolation. |
| FR-DG-3 | `DiscourseGraph` SHALL accept a `verify_on_write: bool` constructor flag. |
| FR-DG-4 | When `verify_on_write=True`, `add_node` SHALL raise `ValueError` on: invalid `node_type`, empty `content`, empty `label`. |
| FR-DG-5 | When `verify_on_write=True`, `add_edge` SHALL raise `ValueError` on: predicate not in discourse predicates, subject type violating predicate domain, object type violating predicate range. |
| FR-DG-6 | When `verify_on_write=False`, `add_node` and `add_edge` SHALL write unconditionally. |
| FR-DG-7 | Relational SHACL constraints (CS-1 `dg:answers`, ES-2) SHALL only be checked by `verify()`, never by `add_node`/`add_edge`, because they require full graph context. |
| FR-DG-8 | `add_node` SHALL mint a UUID-suffixed URI, write `rdf:type`, `rdf:type dg:DiscourseNode`, `rdf:type prov:Entity`, `dg:content`, `rdfs:label`, `dg:created` to the target named graph. |
| FR-DG-9 | `add_node` SHALL accept an optional `graph_uri`; defaulting to `agent.graph_uri("local")`. |
| FR-DG-10 | `add_edge` SHALL accept an optional `graph_uri`; defaulting to `agent.graph_uri("local")`. |
| FR-DG-11 | `verify(graph_uri=None)` SHALL run full pyshacl validation against the named graph (or all of `_store` if `None`) and return a `ValidationReport`. `_policy` SHALL never be included. |
| FR-DG-12 | `named_graphs()` SHALL return the list of named graph URIs in `_store`. |
| FR-DG-13 | `triple_count(graph_uri=None)` SHALL return triple count for the named graph or all of `_store`. |

### FR-POLICY — Sharing policy

| ID | Requirement |
|---|---|
| FR-POL-1 | `declare_sharing_policy(name, grantee_uri, source_graph_uri, include_types, include_nodes, exclude_nodes)` SHALL store policy triples in `_policy` only, never in `_store`. |
| FR-POL-2 | The policy SHALL record: `dg:SharingPolicy` type, `dg:policyName`, `dg:grantee`, `dg:sourceGraph`, `dg:created`, and all include/exclude lists. |
| FR-POL-3 | The permitted node set SHALL be computed as: `(type_matches ∪ explicit_includes) \ explicit_excludes`. |
| FR-POL-4 | `type_matches` SHALL be the set of nodes in `source_graph_uri` whose `rdf:type` matches any URI in `include_types`. |
| FR-POL-5 | `explicit_includes` SHALL be the set of node URIs in `include_nodes` that exist in `source_graph_uri` (silently drops URIs not present). |
| FR-POL-6 | `explicit_excludes` SHALL have highest precedence: any node in `exclude_nodes` is removed from the permitted set regardless of type or include rules. |
| FR-POL-7 | `_compile_policy(policy_uri)` SHALL produce a SPARQL CONSTRUCT string from policy RDF without Alice writing SPARQL directly. |
| FR-POL-8 | The generated CONSTRUCT SHALL scope its `WHERE` clause to the named graph declared in `dg:sourceGraph` via a `GRAPH` clause. |
| FR-POL-9 | The generated CONSTRUCT SHALL include a triple `(s, p, o)` iff: `s ∈ permitted` AND (`isLiteral(o)` OR `p ∉ discourse_predicates` OR `o ∈ permitted`). This is the **edge-bounding rule**. |
| FR-POL-10 | `export_policy(policy_name, grantee_uri)` SHALL verify the declared grantee matches `grantee_uri` before executing the CONSTRUCT. |
| FR-POL-11 | `export_policy` SHALL assert three post-conditions before returning (see FR-INV). |
| FR-POL-12 | `pull_from(other, policy_name)` SHALL call `other.export_policy(policy_name, self.agent.uri)` then `self.ingest(...)`. |

### FR-INGEST — Ingest

| ID | Requirement |
|---|---|
| FR-ING-1 | `ingest(subgraph, source_agent_uri)` SHALL copy all triples from `subgraph` into a new named graph `agent.graph_uri("ingested-<src_slug>")`. |
| FR-ING-2 | For each `dg:DiscourseNode` in the ingested subgraph, `ingest` SHALL add: `rdf:type dg:IngestedNode`, `prov:wasAttributedTo <source_agent_uri>`, `dg:ingestedAt <now>`. |
| FR-ING-3 | `ingest` SHALL return the ingested named graph URI. |

### FR-VIZ — Visualization

| ID | Requirement |
|---|---|
| FR-VIZ-1 | A `visualize_graph(dg, graph_uri=None, ax=None)` function SHALL render a discourse graph as a `networkx` directed graph on a `matplotlib` Axes. |
| FR-VIZ-2 | Nodes SHALL be colored by `rdf:type`: Question=blue, Claim=green, Evidence=amber, Source=gray, IngestedNode=orange border. |
| FR-VIZ-3 | Edge labels SHALL use the local name of the predicate (e.g. "supports", "answers"). |
| FR-VIZ-4 | Ingested nodes SHALL be visually distinguished (dashed border or distinct color). |

---

## Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-1 | The package SHALL have no external HTTP dependencies at runtime. All ontology/shapes are bundled as string constants or local files. |
| NFR-2 | All SHACL shapes SHALL be independently testable without the OWL ontology. |
| NFR-3 | All post-conditions in `export_policy` SHALL be expressed as Python `assert` statements with descriptive messages. |
| NFR-4 | No SPARQL string SHALL be constructed by user-facing code. All SPARQL is generated by `_compile_policy`. |
| NFR-5 | The `_policy` graph SHALL be a structurally separate `rdflib.Graph` instance, never passed to `_store.get_context()` or added via `_store.addN()`. |
| NFR-6 | Test coverage target: ≥90% for `discourse_graph.py`. |
| NFR-7 | All public methods SHALL have type annotations. |
| NFR-8 | Scientific Python style: no frameworks beyond those in BOM.md. |

---

## Invariants

These are the formally stated properties that the implementation must preserve.
Each is tested explicitly in the test suite and asserted in `export_policy`.

| ID | Invariant | Enforcement point |
|---|---|---|
| INV-P1 | No excluded node URI appears as subject or object of a discourse edge in the exported graph. | `assert` in `export_policy` |
| INV-P2 | Every discourse edge `(s, p, o)` in the exported graph satisfies `s ∈ permitted ∧ o ∈ permitted`. | `assert` in `export_policy` |
| INV-P3 | `_policy is not _store` — the policy graph object is structurally isolated. | `assert` in `export_policy` |
| INV-P4 | `_policy` is never passed as an argument to `ConjunctiveGraph` methods. | Code review / structural |
| INV-P5 | `verify()` never includes `_policy` in the validation target. | `_flat_graph()` implementation |

---

## Out of scope (this version)

- Persistent storage (all graphs are in-memory)
- Authentication or cryptographic policy enforcement
- OWL 2 DL reasoning (inference=rdfs only via pyshacl)
- Concurrent write access
- SPARQL endpoint / HTTP API
- MCP server interface (documented as future layer)
