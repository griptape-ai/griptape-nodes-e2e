# AGENTS.md

This workspace is for authoring end-to-end tests against a running
[Griptape Nodes](https://github.com/griptape-ai/griptape-nodes) engine.

______________________________________________________________________

## Workflow

Follow these three phases when creating a test for a node:

1. **Inspect** — Use the `griptape-nodes-e2e-inspect` skill to enumerate the target node's full
   parameter surface (including dynamic parameters that change when dropdown values are modified).
   This produces a CSV file in `inspections/`.

2. **Plan** — Use the `griptape-nodes-e2e-wiki` skill to decide which helper nodes (inputs,
   converters) and assertion nodes to wire up in the test workflow. Cross-reference the inspection
   CSV to confirm type compatibility.

3. **Code** — Use the `griptape-nodes-e2e-sdk` skill to write the pytest test. Tests live under
   `tests/` in this workspace.

______________________________________________________________________

## Directory Layout

| Path            | Purpose                                    |
| --------------- | ------------------------------------------ |
| `inspections/`  | CSV outputs from the inspect skill         |
| `tests/`        | Generated e2e test files                   |
| `.agents/skills/` | Skill definitions (inspect, wiki, sdk)   |
| `.mcp.json`     | MCP server connection to griptape-nodes    |

______________________________________________________________________

## Prerequisites

- A running `griptape-nodes` engine with MCP enabled at `http://localhost:7654/mcp`
- The `griptape-nodes-e2e` Python package installed (from the parent directory):
  ```bash
  cd .. && uv sync --all-groups
  ```
