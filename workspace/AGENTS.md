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

3. **Build** — Use the `griptape-nodes-e2e-workflow` skill to build, validate, and save test
   workflows via MCP tools. The skill reads the inspection report, creates one workflow per
   testable section, executes each against the live engine, and saves the results to
   `tests/<NodeType>/`. The `griptape-nodes-e2e-wiki` skill is consulted automatically for helper
   node selection and wiring guidance.

______________________________________________________________________

## Directory Layout

| Path                | Purpose                                                                                           |
| ------------------- | ------------------------------------------------------------------------------------------------- |
| `inspections/`      | Survey (`.survey.md`), inspection (`.inspect.md`), and workflow summary (`.workflows.md`) outputs |
| `tests/<NodeType>/` | Saved test workflow files (`.py`), one per testable section                                       |
| `.agents/skills/`   | Skill definitions (survey, inspect, wiki, workflow)                                               |
| `.mcp.json`         | MCP server connection to griptape-nodes                                                           |

______________________________________________________________________

## Prerequisites

- A running `griptape-nodes` engine with MCP server connectable.
- The `griptape-nodes-e2e` Python package installed (from the parent directory):
  ```bash
  cd .. && uv sync --all-groups
  ```
