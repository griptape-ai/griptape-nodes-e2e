# AGENTS.md

This workspace is for authoring end-to-end tests against a running
[Griptape Nodes](https://github.com/griptape-ai/griptape-nodes) engine.

______________________________________________________________________

## Quick Start

Use the `griptape-nodes-e2e-pipeline` skill to run the full test generation pipeline:

```
/griptape-nodes-e2e-pipeline IfElse
```

The pipeline orchestrates all four phases below in sequence, confirms the output directory with
you, presents the test plan for approval, and gates workflow generation on that approval. You can
also resume from any step (e.g. "start from plan" or "just run workflows").

______________________________________________________________________

## Phases

The pipeline runs these phases. Each can also be invoked individually via its own skill if needed.

1. **Survey** (`griptape-nodes-e2e-survey`) — Analyse the target node's source code. Produces
   `inspections/<NodeType>.survey.md` mapping all configuration axes — value-driven,
   connection-driven, and UI-message-driven.

2. **Inspect** (`griptape-nodes-e2e-inspect`) — Confirm parameter configurations against a live
   engine, guided by the survey document. Produces `inspections/<NodeType>.inspect.md`.

3. **Plan** (`griptape-nodes-e2e-plan`) — Propose a test matrix of parameter-value configurations.
   Reads the inspection report and survey, classifies parameters, applies coverage heuristics, and
   produces a self-contained test plan at `inspections/<NodeType>.plan.md`. The plan includes
   everything the next phase needs: configuration test rows, error test sections, helper nodes, MCP
   constraints, and runtime observations. A human *must* review and approve the plan before
   proceeding. The skill also supports editing an existing plan.

4. **Build** (`griptape-nodes-e2e-workflow`) — Build, validate, and save test workflows via MCP
   tools. Reads the test plan (its sole input), creates one workflow per testable section, executes
   each against the live engine, and saves the results to `tests/<NodeType>/`. The
   `griptape-nodes-e2e-wiki` skill is consulted automatically for helper node selection and wiring
   guidance.

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
