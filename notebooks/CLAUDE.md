# CLAUDE.md — Marimo notebook development

This file applies to every notebook in `notebooks/`. Read it before writing
or editing any `.py` notebook file. Marimo is **not Jupyter**. The rules
below are non-negotiable.

---

## 1. The reactive model

Marimo executes notebooks as a **reactive DAG**, not as a sequential script.

- Each cell is a **Python function** decorated with `@app.cell`.
- A cell's **function parameters are its inputs** — marimo resolves them from
  the return values of other cells automatically.
- A cell's **return tuple is its output** — anything a downstream cell needs
  must be returned.
- Execution order is determined by the dependency graph, not by file order.
- **A variable name may be returned by exactly one cell.** Returning the same
  name from two cells is a DAG conflict and will raise an error.

```
Cell A returns (foo, bar)
Cell B takes (foo) → can use foo, returns (baz,)
Cell C takes (bar, baz) → can use both, returns ()
```

Private (cell-local) variables are prefixed with `_`. They are never returned
and are invisible to other cells. Use this for all intermediate / throwaway
values.

---

## 2. Cell anatomy

```python
import marimo
__generated_with = "0.20.4"
app = marimo.App(width="medium")

@app.cell(hide_code=True)
def cell_1_introduction(mo):
    """One-line description of what this cell does."""
    _heading = mo.md("## Introduction")
    _body = mo.md("Some explanation.")
    mo.vstack([_heading, _body])
    return  # no output needed by downstream cells


@app.cell(hide_code=True)
def cell_2_build_graph(mo, load_dg_ontology, load_shapes):
    """Build the DiscourseGraph and return it for downstream cells."""
    from discourse_graph.ontology_dg import load_dg_ontology
    # ... (imports belonging here are fine as a rare exception)
    _dg = build_something()
    mo.md("Graph built.")
    return (_dg,)  # downstream cells that need _dg list it as a parameter


if __name__ == "__main__":
    app.run()
```

**Naming convention:** `def cell_<number>_<description>(<deps>):`

- Numbers match the narrative order (0, 1, 2 …).
- Description is a short snake_case phrase.
- Always use `hide_code=True` for publication-facing cells.

---

## 3. The imports cell

Put all library imports in cell 0. Return everything a downstream cell might
need. Use a leading underscore for implementation imports the reader shouldn't
see (`_sys`, `_re`, `_Path`, `_mpl`).

```python
@app.cell(hide_code=True)
def cell_0_imports():
    import marimo as mo
    import sys as _sys
    from pathlib import Path as _Path
    import matplotlib as _mpl
    _mpl.use("Agg")          # required before pyplot import
    import matplotlib.pyplot as plt
    import numpy as np

    # project imports
    from discourse_graph.ontology_dg import load_dg_ontology
    from discourse_graph.shapes import load_shapes
    from discourse_graph.namespaces import load_combined_ontology, DG, ENG

    return (mo, plt, np, load_dg_ontology, load_shapes,
            load_combined_ontology, DG, ENG)
```

---

## 4. State passing

Objects flow downstream via return/parameter only. There are no global
variables in marimo notebooks.

```python
# Cell A builds the graph and returns it
@app.cell(hide_code=True)
def cell_3_build(mo, Agent, DiscourseGraph, load_dg_ontology, load_shapes):
    _ont = load_dg_ontology()
    _shp = load_shapes()
    _agent = Agent(name="Alice", namespace="http://example.org/alice/")
    dg = DiscourseGraph(_agent, _ont, _shp)
    mo.md("Graph initialised.")
    return (dg,)

# Cell B receives dg as a parameter
@app.cell(hide_code=True)
def cell_4_populate(mo, dg, Question, Claim):
    q1 = dg.add(Question(content="What is X?", label="Q1"))
    c1 = dg.add(Claim(content="X is Y.", label="C1"))
    mo.md(f"Added Q1 → `{q1}`, C1 → `{c1}`")
    return (q1, c1)
```

---

## 5. UI component vocabulary

Use only these components. Do not invent alternatives.

### Layout

```python
mo.vstack([component_a, component_b, ...])   # vertical stack
mo.hstack([component_a, component_b, ...])   # horizontal stack (side-by-side)
```

### Content

```python
mo.md("## Heading\n\nMarkdown text.")        # markdown / headings
mo.md(rf"$$\mathbf{{x}} = {latex(expr)}$$") # LaTeX in raw f-string

mo.callout(mo.md("Text"), kind="info")       # kind: info | success | warn | danger
mo.as_html(fig)                              # matplotlib Figure → HTML widget
mo.as_html(df)                              # pandas DataFrame → HTML table
```

### Collapsible / tabbed

```python
mo.accordion({
    "Section title": mo.md("Content"),
    "Another section": mo.callout(mo.md("..."), kind="info"),
})

mo.ui.tabs({
    "Tab A": mo.vstack([...]),
    "Tab B": mo.accordion({...}),
})
```

### Interactive

```python
# Sliders — reactive; downstream cells receive the slider object and call .value
slider = mo.ui.slider(start=0.1, stop=1.0, step=0.05, value=0.5,
                      label=r"$v_E$ (max speed)")
mo.vstack([slider])
return (slider,)

# Downstream cell:
def cell_N(mo, slider):
    _val = slider.value   # float, updates reactively when slider moves
    ...
```

### Status / progress

```python
with mo.status.spinner(title="Running SHACL validation",
                       subtitle="This may take a moment…"):
    _report = dg.verify()
```

### Dynamic replacement

```python
mo.output.replace(mo.md(f"Result: {_result}"))
```

---

## 6. Markdown and LaTeX

Use raw strings so backslashes reach LaTeX:

```python
mo.md(r"""
## §3 — Policy compilation

The permitted set $P$ satisfies:

$$P = (T \cup I) \setminus E$$

where $T$ is type-matched, $I$ is explicitly included, $E$ is excluded.
""")
```

In f-strings, escape literal braces with `{{` / `}}`:

```python
mo.md(rf"""
$$\dot{{x}}_1 = {latex(expr)}$$
""")
```

---

## 7. Matplotlib figures

```python
@app.cell(hide_code=True)
def cell_N_plot(mo, plt, np, dg):
    _fig, _ax = plt.subplots(figsize=(8, 6))
    _ax.plot(...)
    _ax.set_title("...")
    plt.tight_layout()
    mo.vstack([
        mo.as_html(_fig),
        mo.md("*Figure caption.*"),
    ])
    return   # return (_fig,) only if a downstream cell needs the figure object
```

**Never call `plt.show()`.** Marimo displays figures via `mo.as_html()`.

---

## 8. Export commands

```bash
# Narrative demo (no sliders, static) — suitable for discourse_graph_demo.py
uv run marimo export html notebooks/discourse_graph_demo.py -o _site/index.html

# Interactive app (sliders work, runs in-browser via WebAssembly)
uv run marimo export html-wasm notebooks/discourse_graph_demo.py \
    -o _site/index.html --mode run
```

Use `html` for pure narrative notebooks (this project's demo).
Use `html-wasm` when the published notebook has interactive widgets.

---

## 9. Local development

```bash
uv run marimo edit notebooks/discourse_graph_demo.py   # editor with hot-reload
uv run marimo run  notebooks/discourse_graph_demo.py   # read-only app preview
```

---

## 10. What NOT to do — Jupyter anti-patterns

| Anti-pattern | Marimo alternative |
|---|---|
| `plt.show()` | `mo.as_html(_fig)` |
| `display(df)` | `mo.as_html(df)` |
| `print(x)` | `mo.md(f"{x}")` or return `x` |
| `from IPython.display import …` | (delete entirely) |
| Global variable `x = 1` outside a cell | Return `x` from a cell |
| Redefine `x` in a second cell | Each name returned by exactly one cell |
| Sequential script logic split across cells | Cells are functions, not continuations |
| `global` keyword | (never needed — use return/parameter) |
| Mutable closure state (`nonlocal`) | Use `mo.state()` if you need reactive state |
| `import X` scattered through multiple cells | All imports in cell 0 |

---

## 11. Narrative structure

Cells are chapters, not compute units. Each cell has one clear purpose:

- **Header / act title cell** — `mo.md()` only, sets the scene.
- **Setup cell** — builds objects, returns them, minimal display.
- **Narration cell** — renders results with explanation; heavy use of `mo.vstack`, `mo.accordion`, `mo.callout`.
- **Assertion cell** — documents a system property with a labelled `assert`.

Long computations belong in the library (`discourse_graph/`), not in notebook
cells. The notebook narrates and displays; the library computes.

For the `discourse_graph_demo.py` notebook specifically: cells follow a
five-act structure defined in `docs/DESIGN.md §8`. Act headings are
`mo.md()` cells with `## Act N — Title`. Every `assert` is labelled with its
invariant ID (e.g. `# INV-P1:`). The notebook must use `add()` exclusively —
never `add_node()`.
