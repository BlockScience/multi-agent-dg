# Bill of Materials — Discourse Graph Package

## Python version

Python 3.11+

## Runtime dependencies

| Package | Version constraint | Role |
|---|---|---|
| `rdflib` | `>=7.0` | RDF/OWL graph store, SPARQL engine, Turtle parser |
| `pyshacl` | `>=0.25` | SHACL validation engine |
| `pydantic` | `>=2.0` | Node models — primary user-facing API layer |
| `networkx` | `>=3.2` | Graph traversal and layout for visualization |
| `matplotlib` | `>=3.8` | Visualization rendering |

## Demo / notebook dependencies

| Package | Version constraint | Role |
|---|---|---|
| `marimo` | `>=0.10` | Reactive notebook runtime |

## Development / test dependencies

| Package | Version constraint | Role |
|---|---|---|
| `pytest` | `>=8.0` | Test runner |
| `pytest-cov` | `>=5.0` | Coverage reporting |

## Standard library dependencies (no install required)

| Module | Usage |
|---|---|
| `uuid` | Deterministic URI minting |
| `re` | Label slugification |
| `datetime` | xsd:dateTime literal generation |
| `dataclasses` | `Agent` record |
| `typing` | Type annotations |
| `hashlib` | Policy fingerprinting (future) |

## Namespace stubs (not packages)

| IRI | Status | Action required before production |
|---|---|---|
| `http://example.org/dg/1.0/` | W3C example stub | Replace with firm-controlled PURL or HTTPS IRI |
| `http://www.w3.org/ns/prov#` | W3C PROV-O (real) | No action — dereferenceable |
| `http://www.w3.org/ns/shacl#` | W3C SHACL (real) | No action — dereferenceable |

## pyproject.toml stub

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "discourse-graph"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "rdflib>=7.0",
    "pyshacl>=0.25",
    "pydantic>=2.0",
    "networkx>=3.2",
    "matplotlib>=3.8",
]

[project.optional-dependencies]
notebook = ["marimo>=0.10"]
dev = ["pytest>=8.0", "pytest-cov>=5.0"]
```
