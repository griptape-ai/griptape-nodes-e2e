---
name: griptape-nodes-e2e-inspect
description: >-
  Confirm a Griptape Node's parameter configurations against a live engine via MCP tools,
  guided by a survey document from the griptape-nodes-e2e-survey skill. Produces a structured
  markdown inspection report with live-confirmed parameter details for each configuration.
compatibility: Requires an MCP connection to a running griptape-nodes engine.
metadata:
  author: the-foundry-visionmongers
  version: '0.5'
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
- **Error behaviours** — the survey's "Error Behavior" section lists pre-execution validation
  rules, runtime error conditions, input coercion rules, and visual indicators. Use these to guide
  Step 5.

______________________________________________________________________

## MCP Tools Used

All interaction is via MCP tool calls to the running engine. No SDK or Python code is required.

| MCP tool                         | Purpose                                                                                                                 |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `CreateNodeRequest`              | Create a node instance. Args: `node_type`, `specific_library_name`.                                                     |
| `ListParametersOnNodeRequest`    | List current parameter names on a node. Args: `node_name`.                                                              |
| `GetParameterDetailsRequest`     | Get full schema for one parameter. Args: `node_name`, `parameter_name`.                                                 |
| `SetParameterValueRequest`       | Change a parameter value (may trigger mutations). Args: `node_name`, `parameter_name`, `value`.                         |
| `GetParameterValueRequest`       | Read the current value of a parameter. Args: `node_name`, `parameter_name`.                                             |
| `CreateConnectionRequest`        | Connect two parameters. Args: `source_node_name`, `source_parameter_name`, `target_node_name`, `target_parameter_name`. |
| `DeleteConnectionRequest`        | Disconnect two parameters. Same args as `CreateConnectionRequest`.                                                      |
| `DeleteNodeRequest`              | Delete a node when done. Args: `node_name`.                                                                             |
| `ResolveNodeRequest`             | Execute a single node's `process()`. Args: `node_name`. Used to trigger runtime errors.                                 |
| `GetNodeResolutionStateRequest`  | Check node resolution state after execution. Args: `node_name`.                                                         |
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

1. **Find a suitable helper node.** The survey names the source parameter type needed to trigger
   the mutation (e.g. `model ← PromptModelConfig`). Consult the `griptape-nodes-e2e-wiki` skill's
   reference pages to find a node that provides an output of the required type. The wiki's Input
   Providers, Type Converters, Control Flow, and Utility sections catalogue nodes by their output
   types and wiring guidance. If no wiki reference covers the needed type, use
   `ListNodeTypesInLibraryRequest` to search the engine's registered libraries directly.
2. Create the helper node (`CreateNodeRequest` with the node type found above).
3. Call `CreateConnectionRequest` to connect the helper node's output to the target node's input.
4. Call `ListParametersOnNodeRequest` and `GetParameterDetailsRequest` to capture the changed
   parameter surface.
5. Call `DeleteConnectionRequest` to disconnect.
6. Optionally confirm the parameter surface reverts to the pre-connection state.
7. Call `DeleteNodeRequest` to delete the helper node.

If the survey lists no connection-driven configurations, skip this step.

### Step 5: Explore error behaviours

The survey document's "Error Behavior" section lists the expected error mechanisms. Confirm each
one against the live engine. **Create a fresh target node for this step** — error exploration may
leave the node in an unrecoverable state.

#### 5a. Input coercion (before_value_set / set_parameter_value)

For each coercion rule listed in the survey:

1. Call `SetParameterValueRequest` with the bad input value.
2. Call `GetParameterValueRequest` on the same parameter to read back the stored value.
3. Confirm the value was coerced to the expected default (e.g. non-string → `""`, non-dict → `{}`).
4. Record the actual coerced value in the output table.

If `SetParameterValueRequest` returns a failure instead of silently coercing, record that as a
discrepancy from the survey.

#### 5b. Pre-execution validation (validate_before_node_run)

For each validation rule listed in the survey:

1. Set the target node's parameters to trigger the validation error (e.g. leave a required
   parameter empty, set a value out of range).
2. Call `ResolveNodeRequest` on the target node.
3. Confirm the result is a failure with the expected error message pattern.
4. Record the actual error message.

**Important:** After testing each validation rule, reset the parameter to a valid state before
testing the next rule, or delete and recreate the node.

#### 5c. Runtime errors in process()

For each runtime error listed in the survey:

**If the node is a SuccessFailureNode:** Test both paths:

1. **Graceful failure (Failed output connected):**

   - Create a helper node with a control input to receive the `failure` output. Consult the
     `griptape-nodes-e2e-wiki` skill — the Utility section lists nodes suitable as failure-path
     sinks (e.g. `LoggerNode` has a hidden `exec_in`).
   - Connect the target node's `failure` control output to the helper node's `exec_in`.
   - Set the target node's parameters to trigger the runtime error.
   - Call `ResolveNodeRequest` on the target node.
   - Confirm the resolve succeeds (flow did not crash).
   - Call `GetParameterValueRequest` for `was_successful` — confirm it is `False`.
   - Call `GetParameterValueRequest` for `result_details` — confirm it contains a meaningful error
     message.
   - Disconnect and delete the helper node.

2. **Hard failure (Failed output not connected):**

   - Ensure the target node's `failure` output has no connections.
   - Set the target node's parameters to trigger the same runtime error.
   - Call `ResolveNodeRequest` on the target node.
   - Confirm the result is a failure (the flow errored).

**If the node is not a SuccessFailureNode:** Test the hard failure only:

1. Set parameters to trigger the runtime error.
2. Call `ResolveNodeRequest` on the target node.
3. Confirm the result is a failure.

#### 5d. Visual indicators (ParameterMessage / BadgeData)

For each visual indicator listed in the survey, trigger the condition and check whether the
parameter surface changes (e.g. a `ParameterMessage` element appears). This may require calling
`ListParametersOnNodeRequest` after triggering the condition to detect new elements.

Not all visual indicators are detectable through MCP — some are purely UI-side. Note any indicators
you cannot confirm as "Not confirmable via MCP" in the output.

### Step 6: Delete the target node

Call `DeleteNodeRequest` to clean up. If you created a fresh node in Step 5, delete that one too.

### Step 7: Assess testability

Review everything discovered in Steps 2–5 and determine whether the node can support a full e2e
test suite. A node is **blocked** if any configuration that should work (per the survey) is broken
in the live engine — for example:

- A parameter cannot be set to a value the survey says it should accept.
- A connection that should be valid is rejected by the engine.
- `ResolveNodeRequest` crashes or hangs on a configuration that should succeed.
- A `SuccessFailureNode`'s graceful failure path does not work (flow crashes even with `failure`
  connected).
- The node cannot be created at all (`CreateNodeRequest` fails).
- Output parameters produce no value or the wrong type on a valid configuration.
- Any discrepancy from the survey that prevents a test case from being written.

**If any blockers are found:** The inspection report must end with a prominent `## Verdict` section
that says `BLOCKED` and lists every blocker with enough detail for a developer to reproduce it. Do
**not** silently note blockers in the Notes section — they must be called out in the Verdict.

**If no blockers are found:** The Verdict section says `PASS` and briefly confirms the node is
ready for e2e test generation.

After writing the report, **tell the user directly** whether the node passed or is blocked. If
blocked, summarise the blockers in your response — do not make the user read the report to discover
that the node is broken.

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

## Error Behavior

### Base class: <SuccessFailureNode | ControlNode | DataNode | BaseNode>
<Confirmed base class and whether status parameters exist.>

### Input coercion

| Parameter | Bad Input | Expected Coerced To | Actual Coerced To | Status |
|-----------|-----------|--------------------|--------------------|--------|
| ...       | ...       | ...                | ...                | ...    |

<Status = "Confirmed" if actual matches expected, "Discrepancy" if not. If none, write "None.">

### Pre-execution validation (validate_before_node_run)

| Condition | Parameter | Expected Error | Actual Error | Status |
|-----------|-----------|----------------|--------------|--------|
| ...       | ...       | ...            | ...          | ...    |

<If none, write "None.">

### Runtime errors (process)

| Condition | Error Type | Graceful Path | Hard Failure Path | Status |
|-----------|-----------|---------------|-------------------|--------|
| ...       | ...       | ...           | ...               | ...    |

<Graceful Path = "Flow continues, was_successful=False, result_details=<message>" or "N/A" if not a
SuccessFailureNode. Hard Failure Path = "Flow errored" or description of actual behaviour.
Status = "Confirmed" or "Discrepancy".
If none, write "None.">

### Visual indicators

<Results of visual indicator checks, or "None." if none listed in survey.>

## Notes

<Any observations, non-blocking discrepancies from the survey, or edge cases discovered during
inspection. Blockers do NOT go here — they go in the Verdict.>

## Verdict

**PASS** — All configurations confirmed. Node is ready for e2e test generation.

_or_

**BLOCKED** — The following issues prevent a full e2e test suite:

1. <Blocker description with steps to reproduce.>
2. <Blocker description with steps to reproduce.>
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

- **Use a fresh node for error exploration.** Steps 2–4 (parameter surface exploration) may leave
  the node in a specific configuration. Error exploration (Step 5) should start with a clean node
  to avoid interference. Create a new instance of the same node type at the start of Step 5.

- **SuccessFailureNode requires two tests per error.** Every runtime error on a
  `SuccessFailureNode` produces different behaviour depending on whether the `failure` output is
  connected. Test both: the graceful path (connected — flow continues, `was_successful=False`) and
  the hard failure path (not connected — flow errors). Both are valid, testable outcomes.

- **Coercion happens at design time, not execution time.** Input coercion (§5a) is triggered by
  `SetParameterValueRequest`, not `ResolveNodeRequest`. You can confirm it without executing the
  node — just set the value and read it back.

- **Some error paths may be unreachable via MCP.** If a runtime error requires specific data
  flowing through connections at execution time (e.g. a connected input providing a value of the
  wrong runtime type), it may not be triggerable through `SetParameterValueRequest` alone. Note
  these as "Requires workflow execution to test" in the output and skip them — the e2e test itself
  will cover them.
