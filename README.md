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

### Prerequisites

Building the `griptape-nodes-app` package requires a public key for the license server. We do not
use licensing in this project, so can use a dummy key, e.g.

```bash
export GRIPTAPE_NODES_LICENSE_SERVER_PUBLIC_KEY=LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUNvd0JRWURLMlZ3QXlFQWdreTRWVHc2b05lZmdSTHFsNm5uTnNlS1R0c295UHlMS1NkazV4anNGTjg9Ci0tLS0tRU5EIFBVQkxJQyBLRVktLS0tLQo=
uv sync --dev
```

> Note: this will not be necessary once Python wheels are available for the `griptape-nodes-app`
> package.

### Static Analysis

All linting and formatting is consolidated under a single `pre-commit` call:

```bash
pre-commit run --all-files
```

This runs ruff (lint + format), mdformat, docstrfmt, pydoclint, pyright, and gitlint.
