---
name: griptape-nodes-e2e-inspect
description: >-
  Confirm a Griptape Node's parameter configurations against a live engine via MCP tools,
  guided by a survey document from the griptape-nodes-e2e-survey skill. Produces a structured
  markdown inspection report with live-confirmed parameter details for each configuration.
compatibility: Requires an MCP connection to a running griptape-nodes engine.
metadata:
  author: the-foundry-visionmongers
  version: '0.3'
---

# Inspecting Griptape Nodes

## Purpose

Given a target node type (e.g. `AssertStrings` in `Griptape Nodes Testing Library`), confirm its
full parameter surface against a live engine — including dynamic parameters that change across
configurations (value-driven, connection-driven, and UI-message-driven).

The output is a structured markdown file saved to the workspace at
`inspections/<NodeType>.inspect.md`. Downstream agents or humans use this document to plan test
workflows or generate scripts; this skill is not concerned with how the output is consumed.

______________________________________________________________________

## Survey Input

Before starting live exploration, read the survey document at `inspections/<NodeType>.survey.md`.
It lists all configuration axes discovered by static analysis and predicts the parameter surface
for each.

A survey document is **required**. If `inspections/<NodeType>.survey.md` does not exist, stop and
run the `griptape-nodes-e2e-survey` skill first. The survey provides the configuration axes to
explore — without it, the inspection cannot systematically cover all parameter mutations.

Use the survey to guide exploration:

- **Value-driven configurations** — the survey lists which parameters to set and to which values.
  You know exactly what to try instead of blindly iterating all dropdowns.
- **Connection-driven configurations** — the survey lists which parameters to connect and what
  source types to use. You must create appropriate helper nodes, connect them, observe changes,
  then disconnect and clean up.
- **UI-message-driven configurations** — the survey describes parameters that can be added via
  buttons. Where possible, exercise these via `SetParameterValueRequest` or equivalent MCP calls.
- **Discrepancies** — if the live engine produces a parameter surface that differs from the
  survey's prediction, note the discrepancy inline in the output.

______________________________________________________________________

## MCP Tools Used

All interaction is via MCP tool calls to the running engine. No SDK or Python code is required.

| MCP tool                         | Purpose                                                                                                                 |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `CreateNodeRequest`              | Create a node instance. Args: `node_type`, `specific_library_name`.                                                     |
| `ListParametersOnNodeRequest`    | List current parameter names on a node. Args: `node_name`.                                                              |
| `GetParameterDetailsRequest`     | Get full schema for one parameter. Args: `node_name`, `parameter_name`.                                                 |
| `SetParameterValueRequest`       | Change a parameter value (may trigger mutations). Args: `node_name`, `parameter_name`, `value`.                         |
| `CreateConnectionRequest`        | Connect two parameters. Args: `source_node_name`, `source_parameter_name`, `target_node_name`, `target_parameter_name`. |
| `DeleteConnectionRequest`        | Disconnect two parameters. Same args as `CreateConnectionRequest`.                                                      |
| `DeleteNodeRequest`              | Delete a node when done. Args: `node_name`.                                                                             |
| `ListRegisteredLibrariesRequest` | List available libraries. Use to find which library a helper node type belongs to.                                      |
| `ListNodeTypesInLibraryRequest`  | List node types in a library. Use to locate helper nodes for connection-driven testing. Args: `library`.                |

______________________________________________________________________

## Exploration Workflow

### Step 0: Read the survey document

Read `inspections/<NodeType>.survey.md` and use it to plan your exploration. Note all configuration
axes listed.

### Step 1: Create the target node

Call `CreateNodeRequest` with the target `node_type` and `specific_library_name`. Note the returned
`node_name` (e.g. `AssertStrings_1`).

### Step 2: Capture the default parameter state

1. Call `ListParametersOnNodeRequest` with the `node_name` to get all parameter names.
2. For each parameter name, call `GetParameterDetailsRequest` to get its full schema.
3. Record for each parameter: `name`, `type`, `input_types`, `output_type`, `allowed_modes`,
   `default_value`, `tooltip`, and whether it has an `options`/`choices` field (indicating a
   dropdown).

### Step 3: Explore value-driven configurations

For each configuration axis identified in the survey:

1. Call `SetParameterValueRequest` to set the controlling parameter to the target value.
2. Call `ListParametersOnNodeRequest` again.
3. For any parameters that appeared, disappeared, or might have changed, call
   `GetParameterDetailsRequest`.
4. Record the full parameter surface for this configuration.
5. Reset the controlling parameter to its default before exploring the next configuration.

### Step 4: Explore connection-driven configurations

For each connection-driven configuration identified in the survey:

1. Create a helper node of the required type (e.g. `CreateNodeRequest` with the source node type).
2. Call `CreateConnectionRequest` to connect the helper node's output to the target node's input.
3. Call `ListParametersOnNodeRequest` and `GetParameterDetailsRequest` to capture the changed
   parameter surface.
4. Call `DeleteConnectionRequest` to disconnect.
5. Optionally confirm the parameter surface reverts to the pre-connection state.
6. Call `DeleteNodeRequest` to delete the helper node.

If the survey lists no connection-driven configurations, skip this step.

### Step 5: Delete the target node

Call `DeleteNodeRequest` to clean up.

______________________________________________________________________

## Output Format

Save the inspection report to `inspections/<NodeType>.inspect.md`.

Structure:

```markdown
# <NodeType> — <Library Name>

Inspected against live engine on <date>.

## Configuration: default

| Name | Direction | Type | Input Types | Output Type | Default | Constraints |
|------|-----------|------|-------------|-------------|---------|-------------|
| ...  | ...       | ...  | ...         | ...         | ...     | ...         |

## Configuration: <param_name> = "<value>"

Changes from default: <brief description of what changed>

| Name | Direction | Type | Input Types | Output Type | Default | Constraints |
|------|-----------|------|-------------|-------------|---------|-------------|
| ...  | ...       | ...  | ...         | ...         | ...     | ...         |

## Configuration: <param_name> ← <source_type> (connected)

Changes from default: <brief description of what changed>

| Name | Direction | Type | Input Types | Output Type | Default | Constraints |
|------|-----------|------|-------------|-------------|---------|-------------|
| ...  | ...       | ...  | ...         | ...         | ...     | ...         |

## Notes

<Any observations, discrepancies from the survey, or edge cases discovered during inspection.>
```

### Column definitions

| Column        | Description                                                                                                                |
| ------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `Name`        | Parameter name.                                                                                                            |
| `Direction`   | One of: `control-in`, `control-out`, `input`, `output`, `input/output`, `property`. Derived from type and `allowed_modes`. |
| `Type`        | Parameter type (e.g. `str`, `int`, `ImageUrlArtifact`).                                                                    |
| `Input Types` | Semicolon-separated types accepted as input connections. Empty if output-only.                                             |
| `Output Type` | Type produced when used as an output connection. Empty if input-only.                                                      |
| `Default`     | Default value, or empty if none.                                                                                           |
| `Constraints` | Dropdown choices, slider range, or other constraints. Empty if unconstrained.                                              |

### Deriving Direction from allowed_modes

| Condition                           | Direction value |
| ----------------------------------- | --------------- |
| type is `"control"` and INPUT       | `control-in`    |
| type is `"control"` and OUTPUT      | `control-out`   |
| INPUT and OUTPUT                    | `input/output`  |
| INPUT only (no OUTPUT)              | `input`         |
| OUTPUT only (no INPUT)              | `output`        |
| PROPERTY only (no INPUT, no OUTPUT) | `property`      |
| INPUT and PROPERTY (no OUTPUT)      | `input`         |
| OUTPUT and PROPERTY (no INPUT)      | `output`        |

### Key differences from the survey format

- All values are **confirmed from the live engine**, not inferred from source code.
- The **Output Type** column is included (the engine's `GetParameterDetailsRequest` is the
  authority for this value).
- Any **discrepancies** between survey predictions and live results are noted inline with the
  affected row or in the Notes section.

______________________________________________________________________

## Tips

- **Not all dropdowns cause mutations.** Some dropdowns (e.g. `operator` on assertion nodes) change
  behaviour without changing the parameter set. If the parameter list is unchanged after setting a
  dropdown, you can skip recording a separate configuration — just note the dropdown's options in
  the `default` row's Constraints column.

- **Deduplicate configurations.** If two values produce identical parameter surfaces, keep only one
  configuration heading and list both values (e.g.
  `## Configuration: model = "gpt-4o" | "gpt-4o-mini"`).

- **Ignore internal parameters.** Parameters with `private: true` in their schema are internal
  engine plumbing. Exclude them from the output. Do not use naming conventions (e.g. `_` prefix) to
  infer privacy — use the `private` field from `GetParameterDetailsRequest`.

- **Keep tables complete.** Each configuration table should list **all** visible parameters for
  that configuration, not just the ones that changed. This makes each table self-contained.

- **Clean up helper nodes.** When exploring connection-driven configurations, always delete helper
  nodes after disconnecting. Do not leave orphan nodes in the engine.

- **Reset between configurations.** After exploring one configuration, reset the controlling
  parameter to its default value before exploring the next, so you get a clean baseline for
  comparison.

- **Flag survey discrepancies.** If a parameter's live details differ from the survey prediction,
  add `(survey predicted: <value>)` after the actual value in the table, and note it in the Notes
  section.
