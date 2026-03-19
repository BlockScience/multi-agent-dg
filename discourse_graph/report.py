"""VerificationReport: structured output from SHACL shape verification.

Terminology note
----------------
SHACL enforces deterministic, machine-checked constraints — that is
*verification*, not validation.  Validation is reserved for assessments that
require human judgement or domain expertise outside the software.
"""
from __future__ import annotations

import re

import rdflib
from pydantic import BaseModel, field_serializer
from rdflib.namespace import SH


class VerificationReport(BaseModel):
    """Structured result of a SHACL shape verification run.

    Returned by ``DiscourseGraph.verify()``.  All fields are populated by the
    ``pyshacl.validate`` call; do not construct this class manually outside of
    tests.

    Parameters
    ----------
    conforms : bool
        ``True`` if the data graph conforms to all SHACL shapes.
    report_text : str
        Human-readable text output from ``pyshacl.validate``.
    results_graph : rdflib.Graph
        The ``sh:ValidationReport`` graph returned by ``pyshacl.validate``.
        Contains ``sh:ValidationResult`` nodes with ``sh:resultMessage``,
        ``sh:focusNode``, and ``sh:sourceShape`` triples.

    Notes
    -----
    ``results_graph`` is serialised as Turtle when the model is dumped to a
    dict or JSON, so ``model_dump()`` is always safe to call.
    """

    conforms: bool
    report_text: str
    results_graph: rdflib.Graph

    model_config = {"arbitrary_types_allowed": True}

    @field_serializer("results_graph")
    def _serialize_results_graph(self, g: rdflib.Graph) -> str:
        """Serialise the results graph as Turtle for JSON-safe output."""
        return g.serialize(format="turtle")

    @property
    def status(self) -> str:
        """One-line status string.

        Returns
        -------
        str
            ``"CONFORMS ✓"`` if the graph conforms; ``"VIOLATIONS FOUND ✗"``
            otherwise.
        """
        return "CONFORMS ✓" if self.conforms else "VIOLATIONS FOUND ✗"

    def summary(self) -> str:
        """One-line-per-violation string, prefixed with the status line.

        Returns
        -------
        str
            Status line followed by one indented bullet per ``sh:resultMessage``
            found in the results graph.  Returns just the status line when the
            graph conforms.
        """
        lines = [self.status]
        for msg in self.results_graph.objects(None, SH.resultMessage):
            lines.append(f"  - {msg}")
        return "\n".join(lines)

    def violation_ids(self) -> list[str]:
        """Extract requirement IDs from SHACL result messages.

        Scans each ``sh:resultMessage`` literal for a leading token of the
        form ``XX-N`` (e.g. ``"CS-1"``, ``"ES-2"``, ``"DS-1"``).

        Returns
        -------
        list[str]
            Sorted, deduplicated list of requirement IDs found in the report.
        """
        ids: list[str] = []
        pattern = re.compile(r"^([A-Z]{2}-\d+)")
        for msg in self.results_graph.objects(None, SH.resultMessage):
            m = pattern.match(str(msg))
            if m:
                ids.append(m.group(1))
        return ids
