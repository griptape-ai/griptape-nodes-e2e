# AGENTS.md

This workspace is for authoring end-to-end tests against a running
[Griptape Nodes](https://github.com/griptape-ai/griptape-nodes) engine.

______________________________________________________________________

## Workflow

Follow these four phases when creating a test for a node:

1. **Survey** — Use the `griptape-nodes-e2e-survey` skill to analyse the target node's source code.
   This produces a survey document at `inspections/<NodeType>.survey.md` that maps all
   configuration axes — value-driven, connection-driven, and UI-message-driven.

2. **Inspect** — Use the `griptape-nodes-e2e-inspect` skill, guided by the survey document, to
   confirm parameter configurations against a live engine. This produces
   `inspections/<NodeType>.inspect.md`.

3. **Plan** — Use the `griptape-nodes-e2e-wiki` skill to decide which helper nodes (inputs,
   converters) and assertion nodes to wire up in the test workflow. Cross-reference the inspection
   report to confirm type compatibility.

4. **Code** — Use the `griptape-nodes-e2e-sdk` skill to write the pytest test. Tests live under
   `tests/` in this workspace.

______________________________________________________________________

## Directory Layout

| Path              | Purpose                                                      |
| ----------------- | ------------------------------------------------------------ |
| `inspections/`    | Survey (`.survey.md`) and inspection (`.inspect.md`) outputs |
| `tests/`          | Generated e2e test files                                     |
| `.agents/skills/` | Skill definitions (survey, inspect, wiki, sdk)               |
| `.mcp.json`       | MCP server connection to griptape-nodes                      |

______________________________________________________________________

## Prerequisites

- A running `griptape-nodes` engine with MCP server connectable.
- The `griptape-nodes-e2e` Python package installed (from the parent directory):
  ```bash
  cd .. && uv sync --all-groups
  ```
