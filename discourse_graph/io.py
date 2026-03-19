"""File-based import/export utilities for DiscourseGraph.

# NAMESPACE STUB: replace with firm-controlled IRI before production use.

Functions
---------
save_store       Serialize _store (ConjunctiveGraph) to a file.
load_store       Parse a file into _store (additive).
save_policy      Serialize _policy (Graph) to a file.
load_policy      Parse a policy RDF file into _policy (additive).
save_policy_sparql  Compile a policy to SPARQL and save as a text file.

Design notes
------------
* TriG (``.trig``) is the default store format — it is the only rdflib
  format that preserves named-graph structure losslessly in a single file.
* Turtle (``.ttl``) is the default policy format — consistent with the
  ontology/shapes patterns used throughout the codebase.
* All load functions are **additive**: they call ``graph.parse()`` which
  adds triples to the existing graph.  Load into a fresh ``DiscourseGraph``
  for a clean restore.
* SPARQL export (``save_policy_sparql``) produces an inspection/logging
  artifact only.  SPARQL is never imported back — NFR-4 requires that
  SPARQL generation is confined to ``_compile_policy()`` in ``graph.py``.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from rdflib import URIRef

if TYPE_CHECKING:
    from discourse_graph.graph import DiscourseGraph

# ── Format registry ─────────────────────────────────────────────────────────

_FORMAT_BY_EXT: dict[str, str] = {
    ".ttl": "turtle",
    ".trig": "trig",
    ".nq": "nquads",
    ".nt": "ntriples",
    ".jsonld": "json-ld",
    ".n3": "n3",
}


def _detect_format(path: Path, given: Optional[str]) -> str:
    """Return the serialization format string.

    Parameters
    ----------
    path :
        File path whose suffix is used for auto-detection.
    given :
        Explicit format override; returned as-is when not ``None``.

    Raises
    ------
    ValueError
        If *given* is ``None`` and the file suffix is not in the registry.
    """
    if given is not None:
        return given
    ext = path.suffix.lower()
    if ext not in _FORMAT_BY_EXT:
        raise ValueError(
            f"Cannot auto-detect RDF format for extension {ext!r}. "
            f"Pass format= explicitly.  Known extensions: "
            f"{', '.join(sorted(_FORMAT_BY_EXT))}."
        )
    return _FORMAT_BY_EXT[ext]


# ── Store I/O ────────────────────────────────────────────────────────────────


def save_store(
    dg: "DiscourseGraph",
    path: "Path | str",
    format: str = "trig",
) -> None:
    """Serialize ``dg._store`` (all named graphs) to a file.

    Parameters
    ----------
    dg :
        The ``DiscourseGraph`` whose store is serialized.
    path :
        Destination file path.  The file is created or overwritten.
    format :
        rdflib serialization format string.  Defaults to ``"trig"`` which
        preserves named-graph structure losslessly.  Other useful values:
        ``"nquads"``, ``"turtle"``, ``"json-ld"``.

    Notes
    -----
    TriG is the recommended format for ``_store`` because it is the only
    widely-supported format that encodes both triples and graph names in
    one file.  N-Quads (``"nquads"``) is an equivalent machine-exchange
    alternative.  Turtle loses named-graph information.
    """
    path = Path(path)
    dg._store.serialize(destination=str(path), format=format)


def load_store(
    dg: "DiscourseGraph",
    path: "Path | str",
    format: Optional[str] = None,
) -> None:
    """Parse a serialized store file into ``dg._store`` (additive).

    Parameters
    ----------
    dg :
        The ``DiscourseGraph`` whose store receives the parsed triples.
    path :
        Source file path.
    format :
        rdflib serialization format string.  When ``None``, auto-detected
        from the file extension using the built-in registry.

    Notes
    -----
    This operation is **additive**: existing triples in ``_store`` are
    retained.  For a clean restore, load into a freshly constructed
    ``DiscourseGraph``.
    """
    path = Path(path)
    fmt = _detect_format(path, format)
    dg._store.parse(source=str(path), format=fmt)


# ── Policy I/O ───────────────────────────────────────────────────────────────


def save_policy(
    dg: "DiscourseGraph",
    path: "Path | str",
    format: str = "turtle",
) -> None:
    """Serialize ``dg._policy`` (the policy RDF graph) to a file.

    Parameters
    ----------
    dg :
        The ``DiscourseGraph`` whose policy graph is serialized.
    path :
        Destination file path.  The file is created or overwritten.
    format :
        rdflib serialization format string.  Defaults to ``"turtle"``
        which is human-readable and consistent with the ontology/shapes
        patterns used throughout the codebase.

    Notes
    -----
    The output file contains ``dg:SharingPolicy`` triples in exactly the
    structure that :meth:`~discourse_graph.graph.DiscourseGraph.declare_sharing_policy`
    writes.  Another agent can load this file via :func:`load_policy` and
    immediately call ``export_policy()`` without authoring Python.
    """
    path = Path(path)
    dg._policy.serialize(destination=str(path), format=format)


def load_policy(
    dg: "DiscourseGraph",
    path: "Path | str",
    format: Optional[str] = None,
) -> None:
    """Parse a policy RDF file into ``dg._policy`` (additive).

    Parameters
    ----------
    dg :
        The ``DiscourseGraph`` whose policy graph receives the parsed triples.
    path :
        Source file path.  Must contain ``dg:SharingPolicy`` triples.
    format :
        rdflib serialization format string.  When ``None``, auto-detected
        from the file extension using the built-in registry.

    Notes
    -----
    After this call, ``dg.export_policy(policy_name, grantee_uri)`` works
    exactly as if the policy had been declared in Python via
    ``declare_sharing_policy()``.  This allows agents to receive and apply
    a sharing policy without authoring it.

    The operation is **additive**: existing policy triples are retained.
    """
    path = Path(path)
    fmt = _detect_format(path, format)
    dg._policy.parse(source=str(path), format=fmt)


# ── SPARQL export ────────────────────────────────────────────────────────────


def save_policy_sparql(
    dg: "DiscourseGraph",
    policy_name: str,
    grantee_uri: URIRef,
    path: "Path | str",
    override: bool = False,
) -> None:
    """Compile a policy to SPARQL and save the string to a text file.

    Parameters
    ----------
    dg :
        The ``DiscourseGraph`` that owns the policy.
    policy_name :
        The ``dg:policyName`` of the policy to compile.
    grantee_uri :
        The grantee URI.  Must match the declared grantee unless *override*
        is ``True``.
    path :
        Destination file path.  Conventionally uses a ``.sparql`` suffix.
    override :
        When ``True``, bypass the grantee equality check so the **policy
        author** can inspect their own compiled SPARQL without acting as
        the grantee.  Defaults to ``False`` (accidental-export guard active).
        INV-P1/P2/P3 assertions in ``export_policy()`` are unaffected.

    Notes
    -----
    The written SPARQL string is an **inspection/logging artifact only**.
    It is not imported back into any ``DiscourseGraph`` — SPARQL generation
    is confined to ``_compile_policy()`` per NFR-4.
    """
    path = Path(path)
    _, sparql_string = dg.export_policy(policy_name, grantee_uri, override=override)
    path.write_text(sparql_string, encoding="utf-8")
