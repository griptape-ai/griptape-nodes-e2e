# griptape-nodes-e2e

Agent-driven end-to-end testing for
[Griptape Nodes](https://github.com/griptape-ai/griptape-nodes).

## Overview

This repository provides a **skill-based pipeline** that uses a coding harness (Claude Code) to
generate end-to-end test workflows for Griptape Nodes. The pipeline inspects node source code and a
live engine to produce test plans and executable workflows.

### Pipeline Phases

1. **Survey** - Static analysis of a node's source code. Enumerates all parameter configurations
   (value-driven, connection-driven, UI-message-driven). Output: `inspections/<Node>.survey.md`.
2. **Inspect** - Live confirmation of parameter behaviours against a running engine via MCP tools.
   Output: `inspections/<Node>.inspect.md`.
3. **Plan** - Proposes a test matrix of parameter-value configurations, error cases, and helper
   nodes. Output: `inspections/<Node>.plan.md`. Requires human review and approval.
4. **Build** - Constructs, validates, and saves test workflows via MCP tools. Reads the approved
   plan as its sole input. Output: `tests/<Node>/`.

## Repository Structure

| Path                  | Purpose                                                        |
| --------------------- | -------------------------------------------------------------- |
| `workspace/`          | Working directory for agent sessions that generate e2e tests   |
| `workspace/.agents/`  | Skill definitions (survey, inspect, plan, workflow, wiki, etc) |
| `griptape_nodes_e2e/` | Python package - currently a stub for potential future SDK use |

The `workspace/` directory has its own `AGENTS.md`, MCP configuration, and skill definitions. When
running the pipeline, the coding harness should be rooted in `workspace/`.

This (root) directory is the working directory for **developing** the skills, tooling, and any
future SDK code.

## Development

### Quick start

Install dependencies and pre-commit hooks:

```bash
uv sync --all-groups
pre-commit install
```

### Static Analysis

All linting and formatting is consolidated under a single `pre-commit` call:

```bash
pre-commit run --all-files
```

This runs ruff (lint + format), mdformat, docstrfmt, pydoclint, pyright.

In addition, gitlint is used to check commit messages on commit (see [.gitlint](./.gitlint) for
rules)

To run linters/formatters individually (auto-fixing where possible):

```bash
uv run mdformat *.md workspace/
uv run ruff format
uv run ruff check --fix
uv run docstrfmt .
uv run pydoclint .
uv run pyright .
```
