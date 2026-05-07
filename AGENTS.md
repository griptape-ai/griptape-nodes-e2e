# AGENTS.md

This file provides guidance to AI coding agents working in this repository.

______________________________________________________________________

## Project Overview

`griptape-nodes-e2e` is an AI-assisted end-to-end testing framework for
[Griptape Nodes](https://github.com/griptape-ai/griptape-nodes).

### The `workspace/` directory

The `workspace/` directory is the working directory for agent sessions that create e2e tests. It
has its own `AGENTS.md`, skills, and MCP configuration. When an agent is launched to survey,
inspect, or test a node, it should be rooted in `workspace/` — not the repository root.

The repository root contains the SDK source code (`griptape_nodes_e2e/`), unit/integration tests
(`tests/`), and development tooling. These are separate concerns: you develop the SDK here at the
root, and you *use* the SDK (via agent skills) from `workspace/`.

______________________________________________________________________

## Development Commands

All static analysis and linting is consolidated under a single `pre-commit` call:

```bash
pre-commit run --all-files
```

This runs ruff (lint + format), mdformat, docstrfmt, pydoclint, pyright, and gitlint in one pass.
**After every substantial change, run this command and fix all issues it raises before moving on.**

Dependencies are managed with `uv`. To install everything (including dev dependencies):

```bash
uv sync --all-groups
```

To install the pre-commit hooks locally:

```bash
pre-commit install
```

______________________________________________________________________

## Iteration Loop

Follow this loop for every change, no matter how small:

0. **Write a test** — write one or more tests that prove the change will work. Tests live under
   `tests/unit/` or `tests/integration/`, mirroring the source tree (e.g.
   `griptape_nodes_e2e/foo/bar.py` → `tests/unit/foo/test_bar.py`). Mark async test functions with
   `@pytest.mark.asyncio`.
1. **Make the change** — implement the feature or fix.
2. **Run static checks** — `pre-commit run --all-files`. Fix every issue before continuing.
3. **Run tests with coverage** — verify the suite passes and coverage does not drop:
   ```bash
   uv run slipcover --branch --source griptape_nodes_e2e --fail-under 90 -m pytest
   ```
   `--branch` catches untested conditional paths; `--fail-under 90` exits with code 2 if overall
   coverage falls below 90 %. If you add code you must add tests that cover it. Adjust
   `--fail-under` upward as the codebase matures; never lower it.
4. **Fix issues** — resolve every failure from steps 2 and 3 before continuing.
5. **Repeat** — continue to the next change.

______________________________________________________________________

## Code Style

### Copyright Header

Every file that supports comments **must** begin with this header:

```python
# griptape-nodes-e2e
# Copyright (c) 2026 The Foundry Visionmongers Ltd
```

For YAML, TOML, and other non-Python formats that support `#` comments, use the same header.
Markdown files are exempt.

### Code Organisation — Highest-Level First

Within every module, place high-level code **above** the lower-level code it depends on.
Concretely:

- Public API (classes, functions intended for callers) comes before internal helpers.
- Within a class, use this member order:
  1. Class attributes
  2. `__init__`
  3. Other dunder methods
  4. Properties
  5. Public instance methods (high-level callers above the helpers they use)
  6. Private instance methods
  7. Class methods
  8. Static methods

This means a reader can understand *what* a module does before diving into *how*.

### Imports

- All imports must be at the top of the file — no lazy imports inside functions unless the only way
  to break a circular dependency.
- If a lazy import is unavoidable, add a comment naming the circular dependency.
- Use `isort`-compatible ordering (enforced by ruff rule `I`).

### Logic Flow

- Prefer simple, explicit `if`/`else` statements over ternary operators or nested conditionals.
- **Evaluate all failure cases first.** Every validation check, error condition, and guard clause
  goes at the top of the function with an immediate `return`/`raise`. The success path is always
  last.
- Break complex nested expressions into clearly named intermediate variables.

### Return Values

- Avoid returning bare tuples. Use `dataclasses`, named `TypedDict`s, or `NamedTuple`s when
  multiple values must be returned together.

### Exception Handling

- Only wrap code that is *known* to raise the caught exception — keep `try` blocks as small as
  possible.
- Catch the most specific exception type available. Never use bare `except:` or `except Exception:`
  unless explicitly justified with a comment.
- Include context in error messages:
  `"Attempted to <action>. Failed with <data> because <reason>."`.

### Docstrings

- All public classes, methods, and functions must have docstrings.
- Use **Sphinx-style** docstrings (`:param name:`, `:returns:`, `:raises:`), enforced by
  `pydoclint` (style = sphinx in `pyproject.toml`).
- Format docstrings to the line length enforced by `docstrfmt` (88 chars).
- Document all parameters; omit `*args`/`**kwargs` unless meaningful.

### Comments

- Add inline code comments frequently. If in doubt, add a comment. Explain *why* something is done,
  not just *what*.

### Type Annotations

- All function signatures (arguments and return types) must be fully annotated.
- Use `from __future__ import annotations` at the top of every module to enable PEP 563 postponed
  evaluation.
- Avoid `Any` except where genuinely unavoidable (the ruff rule `ANN401` is intentionally relaxed
  for `**kwargs` in base-class overrides only).

______________________________________________________________________

## Markdown and Documentation

- All Markdown is formatted by `mdformat` (wrap = 99, numbered lists).
- Run `pre-commit run --all-files` to check and fix Markdown files.

______________________________________________________________________

## Commit Messages

Commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/)
specification, enforced by `gitlint`. Allowed types:

- `feat` — new feature
- `fix` — bug fix
- `refactor` — code restructure without behaviour change
- `deps` — dependency updates
- `chore` — maintenance (build, tooling, config)
- `docs` — documentation only
- `ci` — CI/CD pipeline changes

Format: `<type>: <short description>` (imperative mood, no trailing period).

### Commit Discipline

Each commit must be **self-contained** — the codebase must be in a valid, non-broken state after
every single commit. Nothing should be left "pending further changes". Keep commits as small as
reasonably possible while satisfying this requirement.

If an issue is discovered with a previous commit during the same development session, use
autosquash-style fixup commits:

```bash
git commit --fixup=<sha>   # or --squash=<sha> if the message needs rewriting
```

These will be squashed into their targets during interactive rebase before merge. Never force-push
to shared branches without coordination.

______________________________________________________________________

## Pre-commit Hook Reference

| Hook          | What it checks                                              |
| ------------- | ----------------------------------------------------------- |
| `ruff-check`  | Python linting (see `[tool.ruff.lint]` in `pyproject.toml`) |
| `ruff-format` | Python formatting                                           |
| `mdformat`    | Markdown formatting                                         |
| `docstrfmt`   | Docstring formatting                                        |
| `pydoclint`   | Docstring completeness (Sphinx style)                       |
| `pyright`     | Static type checking                                        |
| `gitlint`     | Commit message format                                       |
