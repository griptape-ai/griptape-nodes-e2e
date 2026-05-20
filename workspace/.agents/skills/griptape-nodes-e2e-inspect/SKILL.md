---
name: griptape-nodes-e2e-inspect
description: >-
  Confirm a Griptape Node's parameter configurations against a live engine via MCP tools,
  guided by a survey document from the griptape-nodes-e2e-survey skill. Produces a structured
  markdown inspection report with live-confirmed parameter details for each configuration.
compatibility: Requires an MCP connection to a running griptape-nodes engine.
metadata:
  author: the-foundry-visionmongers
  version: '0.8'
---

# Inspecting Griptape Nodes

## Purpose

Given a target node type (e.g. `AssertStrings` in `Griptape Nodes Testing Library`), confirm its
full parameter surface against a live engine — including dynamic parameters that change across
configurations (value-driven, connection-driven, and UI-message-driven).

The output is a structured markdown file saved to the workspace at
`workspace/inspections/<NodeType>.inspect.md`. Downstream agents or humans use this document to
plan test workflows or generate scripts; this skill is not concerned with how the output is
consumed.

______________________________________________________________________

## Survey Input

Before starting live exploration, read the survey document at
`workspace/inspections/<NodeType>.survey.md`. It lists all configuration axes discovered by static
analysis and predicts the parameter surface for each.

A survey document is **required**. If `workspace/inspections/<NodeType>.survey.md` does not exist,
stop and run the `griptape-nodes-e2e-survey` skill first. The survey provides the configuration
axes to explore — without it, the inspection cannot systematically cover all parameter mutations.

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
  rules, runtime error conditions, design-time input handling rules, and visual indicators. Use
  these to guide Step 6.

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
| `EnsureWorkflowAndFlowRequest`   | Bootstrap a workflow and flow context. Used for runtime validation (Step 6a) when the node needs a flow to execute.     |
| `StartFlowRequest`               | Execute a flow. Use with `wait_for_completion: true` for runtime validation.                                            |
| `ClearAllObjectStateRequest`     | Reset engine state. Use between runtime validation runs to ensure clean state.                                          |
| `ListRegisteredLibrariesRequest` | List available libraries. Use to find which library a helper node type belongs to.                                      |
| `ListNodeTypesInLibraryRequest`  | List node types in a library. Use to locate helper nodes for connection-driven testing. Args: `library`.                |

______________________________________________________________________

## Choosing Helper Nodes

Whenever you need a helper node — an input provider, a type converter, a failure-path sink, or any
node to connect to the target — consult the `griptape-nodes-e2e-wiki` skill **first**. The wiki's
reference pages catalogue nodes by purpose and output type, with wiring guidance for each. Do NOT
explore libraries via `ListNodeTypesInLibraryRequest` or `ListRegisteredLibrariesRequest` unless
the wiki does not cover the type you need.

______________________________________________________________________

## Exploration Workflow

### Step 0: Read the survey document

Read `workspace/inspections/<NodeType>.survey.md` and use it to plan your exploration. Note all
configuration axes listed.

### Step 1: Clear engine state

Call `ClearAllObjectStateRequest` with `i_know_what_im_doing: true` to wipe any existing workflow,
then call `EnsureWorkflowAndFlowRequest` to create a fresh, empty workspace. This guarantees a
clean starting point — leftover nodes from a previous session will interfere with inspection.

### Step 2: Create the target node

Call `CreateNodeRequest` with the target `node_type` and `specific_library_name`. Note the returned
`node_name` (e.g. `AssertStrings_1`).

### Step 3: Capture the default parameter state

1. Call `ListParametersOnNodeRequest` with the `node_name` to get all parameter names.
2. For each parameter name, call `GetParameterDetailsRequest` to get its full schema.
3. Record for each parameter: `name`, `type`, `input_types`, `output_type`, `allowed_modes`,
   `default_value`, `tooltip`, and whether it has an `options`/`choices` field (indicating a
   dropdown).

### Step 4: Explore value-driven configurations

For each configuration axis identified in the survey:

1. Call `SetParameterValueRequest` to set the controlling parameter to the target value.
2. Call `ListParametersOnNodeRequest` again.
3. For any parameters that appeared, disappeared, or might have changed, call
   `GetParameterDetailsRequest`.
4. Record the full parameter surface for this configuration.
5. Reset the controlling parameter to its default before exploring the next configuration.

### Step 5: Explore connection-driven configurations

For each connection-driven configuration identified in the survey:

1. **Find a suitable helper node.** The survey names the source parameter type needed to trigger
   the mutation (e.g. `model ← PromptModelConfig`). Use the `griptape-nodes-e2e-wiki` skill to find
   a node that provides an output of the required type. Only fall back to
   `ListNodeTypesInLibraryRequest` if the wiki does not cover the needed type.
2. Create the helper node (`CreateNodeRequest` with the node type found above).
3. **Record the helper node** — note its node type, library name, the parameter used, and its
   purpose (e.g. "str output source for output_if_true"). You will include these in the Confirmed
   Helper Nodes table in the output.
4. Call `CreateConnectionRequest` to connect the helper node's output to the target node's input.
5. Call `ListParametersOnNodeRequest` and `GetParameterDetailsRequest` to capture the changed
   parameter surface.
6. Call `DeleteConnectionRequest` to disconnect.
7. Optionally confirm the parameter surface reverts to the pre-connection state.
8. Call `DeleteNodeRequest` to delete the helper node.

If the survey lists no connection-driven configurations, skip this step.

### Step 6: Validate runtime behaviour

After confirming parameter surfaces (Steps 3–5), validate that each configuration actually produces
output when executed. This step records **observed runtime behaviour** — what inputs were used,
what outputs were produced, and which control paths were taken. These observations feed directly
into the workflow skill as confirmed expected values.

**Create a fresh target node for this step** — surface exploration in Steps 3–5 may have left the
node in a specific state.

#### 6a. Happy-path validation

For each configuration that was confirmed in Steps 3–5, run a basic validation:

1. Set the target node's parameters to a representative state for that configuration (reuse the
   same values and connections used during surface confirmation).
2. If the node requires input connections to execute (e.g. `ControlNode` with `exec_in`), create a
   minimal flow context — use `EnsureWorkflowAndFlowRequest` and
   `StartFlowRequest(wait_for_completion=true)` instead of `ResolveNodeRequest`.
3. After execution, call `GetParameterValueRequest` on each output parameter to read the produced
   values.
4. Record the observation: input values, output values, control path taken (if observable), and
   whether execution succeeded.
5. Clean up any helper nodes created for this validation.

Not every configuration needs a separate execution — if two configurations differ only in their
parameter surface (not their runtime behaviour), one execution covering the shared logic is
sufficient. Use judgement: the goal is to give the workflow skill at least one confirmed
input→output pair per configuration, not exhaustive functional testing.

**Record helpers used during validation** in the Confirmed Helper Nodes table, alongside helpers
from Step 5.

#### 6b. Error behaviours

The survey document's "Error Behavior" section lists the expected error mechanisms. Confirm each
one against the live engine. Create a fresh target node if the previous validation left the node in
an unrecoverable state.

#### 6c. Design-time input handling (before_value_set / set_parameter_value)

For each design-time input handling rule listed in the survey:

1. Call `SetParameterValueRequest` with the input value described in the survey.
2. Call `GetParameterValueRequest` on the same parameter to read back the stored value.
3. Confirm the value was transformed as expected (e.g. non-string → `""`, non-dict → `{}`).
4. Record the actual result in the output table.

If `SetParameterValueRequest` returns a failure instead of silently handling the value, record that
as a discrepancy from the survey.

#### 6d. Pre-execution validation (validate_before_node_run)

For each validation rule listed in the survey:

1. Set the target node's parameters to trigger the validation error (e.g. leave a required
   parameter empty, set a value out of range).
2. Call `ResolveNodeRequest` on the target node.
3. Confirm the result is a failure with the expected error message pattern.
4. Record the actual error message.

**Important:** After testing each validation rule, reset the parameter to a valid state before
testing the next rule, or delete and recreate the node.

#### 6e. Runtime errors in process()

For each runtime error listed in the survey:

**If the node is a SuccessFailureNode:** Test both paths:

1. **Graceful failure (Failed output connected):**

   - Create a helper node with a control input to receive the `failure` output. Use the
     `griptape-nodes-e2e-wiki` skill to find a suitable failure-path sink (e.g. `LoggerNode` has a
     hidden `exec_in`).
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

#### 6f. Visual indicators (ParameterMessage / BadgeData)

For each visual indicator listed in the survey, trigger the condition and check whether the
parameter surface changes (e.g. a `ParameterMessage` element appears). This may require calling
`ListParametersOnNodeRequest` after triggering the condition to detect new elements.

Not all visual indicators are detectable through MCP — some are purely UI-side. Note any indicators
you cannot confirm as "Not confirmable via MCP" in the output.

### Step 7: Delete the target node

Call `DeleteNodeRequest` to clean up. If you created fresh nodes in Step 6, delete those too.

### Step 8: Assess testability

Review everything discovered in Steps 3–6 and determine whether the node can support a full e2e
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

Save the inspection report to `workspace/inspections/<NodeType>.inspect.md`.

Structure:

```markdown
# <NodeType> — <Library Name>

Inspected against live engine on <date>.

## Configuration: default
<!-- id: config_default -->

| Name | Direction | Type | Input Types | Output Type | Default | Constraints |
|------|-----------|------|-------------|-------------|---------|-------------|
| ...  | ...       | ...  | ...         | ...         | ...     | ...         |

## Configuration: <param_name> = "<value>"
<!-- id: config_<param_name>_eq_<value> -->

Changes from default: <brief description of what changed>

| Name | Direction | Type | Input Types | Output Type | Default | Constraints |
|------|-----------|------|-------------|-------------|---------|-------------|
| ...  | ...       | ...  | ...         | ...         | ...     | ...         |

## Configuration: <param_name> ← <source_type> (connected)
<!-- id: config_<param_name>_connected -->

Changes from default: <brief description of what changed>

| Name | Direction | Type | Input Types | Output Type | Default | Constraints |
|------|-----------|------|-------------|-------------|---------|-------------|
| ...  | ...       | ...  | ...         | ...         | ...     | ...         |

## Error Behavior

### Base class: <SuccessFailureNode | ControlNode | DataNode | BaseNode>
<Confirmed base class and whether status parameters exist.>

### Design-time input handling
<!-- id: error_design_time_input -->

| Parameter | Input | Expected Result | Actual Result | Status |
|-----------|-------|-----------------|---------------|--------|
| ...       | ...   | ...             | ...           | ...    |

<Status = "Confirmed" if actual matches expected, "Discrepancy" if not. If none, write "None.">

### Pre-execution validation (validate_before_node_run)

| ID | Condition | Parameter | Expected Error | Actual Error | Status |
|----|-----------|-----------|----------------|--------------|--------|
| ...| ...       | ...       | ...            | ...          | ...    |

<Each row gets a unique ID used as the workflow filename suffix. Use the pattern
`error_pre_execution_<condition>` where `<condition>` is a short snake_case descriptor (e.g.
`error_pre_execution_empty_key`, `error_pre_execution_invalid_type`). If there is only one
validation condition, use `error_pre_execution_validation` as the ID.
If none, write "None.">

### Runtime errors (process)

| ID | Condition | Error Type | Graceful Path | Hard Failure Path | Status |
|----|-----------|-----------|---------------|-------------------|--------|
| ...| ...       | ...       | ...           | ...               | ...    |

<Each row gets a unique ID used as the workflow filename suffix. Use the pattern
`error_runtime_<condition>` where `<condition>` is a short snake_case descriptor (e.g.
`error_runtime_key_not_found`, `error_runtime_non_dict_input`). If there is only one runtime
error condition, use `error_runtime` as the ID.

Graceful Path = "Flow continues, was_successful=False, result_details=<message>" or "N/A" if not a
SuccessFailureNode. Hard Failure Path = "Flow errored" or description of actual behaviour.
Status = "Confirmed" or "Discrepancy".
If none, write "None.">

### Visual indicators

<Results of visual indicator checks, or "None." if none listed in survey.>

## MCP Constraints

Parameters that require special handling when interacted with via MCP tools. These are operational
quirks discovered during inspection — not parameter constraints visible in the UI, but behaviours
specific to the MCP interface that the workflow skill must follow.

| Parameter | Constraint | Workaround |
|-----------|-----------|------------|
| <e.g. default_value_if_not_found> | <e.g. SetParameterValueRequest fails without data_type — engine infers "any", rejected by allowed list> | <e.g. Always pass data_type="str" (or concrete type)> |

<If no MCP-specific constraints were discovered, write "None.">

## Confirmed Helper Nodes

Helper nodes used during inspection. Downstream skills should reuse these rather than
re-discovering them.

| Purpose | Node Type | Library | Parameter | Direction | Type |
|---------|-----------|---------|-----------|-----------|------|
| <role in testing, e.g. "str source for output_if_true"> | <e.g. TextInput> | <e.g. Griptape Nodes Library> | <e.g. text> | <output> | <str> |
| <e.g. "str consumer for output assertion"> | <e.g. AssertStrings> | <e.g. Griptape Nodes Testing Library> | <e.g. actual> | <input> | <str> |
| <e.g. "failure-path sink"> | <e.g. LoggerNode> | <e.g. Griptape Nodes Library> | <e.g. exec_in> | <control-in> | <control> |

<Include every helper node used in Steps 5 and 6, regardless of whether it was deleted after use.
Group by purpose. If no helpers were needed (e.g. no connection-driven configurations or error
tests), write "None.">

## Runtime Observations

Confirmed input→output behaviour observed during Step 6a. These are facts, not predictions — the
workflow skill should use them as expected values.

| Configuration | Inputs | Outputs | Control Path | Status |
|---------------|--------|---------|-------------|--------|
| <config name or section ID> | <param=value, param=value> | <param=value, param=value> | <e.g. "Then", "exec_out", or "—"> | <Resolved / Errored> |

<Each row is one execution. "Inputs" lists the parameter values set before execution. "Outputs"
lists the output parameter values read after execution. "Control Path" notes which control output
was taken, if observable (e.g. for IfElse: "Then" or "Else"; for ControlNode: "exec_out"; write
"—" if not observable or not applicable). "Status" is "Resolved" if execution succeeded, "Errored"
if it failed.

Not every configuration needs a separate row — if two configurations share runtime behaviour,
one observation covering the shared logic is sufficient. The goal is at least one confirmed
input→output pair per configuration that the workflow skill will need to build a test for.

If no runtime validation was performed (e.g. node requires external resources), write "None." and
explain why.>

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

### Section IDs

Configuration and design-time sections use an `<!-- id: lower_snake_case_id -->` HTML comment on
the line immediately after the heading. Pre-execution validation and runtime error sections use an
ID column in their table — each row gets its own unique ID. Downstream skills use these IDs as
workflow filenames — they must be unique within the document and suitable for use in a file path
(lowercase, underscores, no spaces or special characters).

**Naming conventions:**

| Section type                    | ID pattern                        | Example                         |
| ------------------------------- | --------------------------------- | ------------------------------- |
| Default configuration           | `config_default`                  | `config_default`                |
| Value-driven configuration      | `config_<param>_eq_<value>`       | `config_operator_eq_contains`   |
| Connection-driven configuration | `config_<param>_connected`        | `config_model_connected`        |
| Design-time input handling      | `error_design_time_input`         | `error_design_time_input`       |
| Pre-execution validation        | `error_pre_execution_<condition>` | `error_pre_execution_empty_key` |
| Runtime errors                  | `error_runtime_<condition>`       | `error_runtime_key_not_found`   |

Sanitise values for the ID: replace spaces with `_`, remove quotes and special characters,
lowercase everything. For deduplicated configurations (e.g. `model = "gpt-4o" | "gpt-4o-mini"`),
use the first value in the ID.

Sections that are **not testable** — `## Static parameters`, `## MCP Constraints`,
`## Confirmed Helper Nodes`, `## Runtime Observations`, `## Notes`, `## Verdict`, `### Base class`,
`### Visual indicators` — do **not** get IDs.

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

- **Use fresh nodes for validation and error exploration.** Steps 3–5 (parameter surface
  exploration) may leave the node in a specific configuration. Step 6 (runtime validation and error
  exploration) should start with a clean node to avoid interference.

- **SuccessFailureNode requires two tests per error.** Every runtime error on a
  `SuccessFailureNode` produces different behaviour depending on whether the `failure` output is
  connected. Test both: the graceful path (connected — flow continues, `was_successful=False`) and
  the hard failure path (not connected — flow errors). Both are valid, testable outcomes.

- **Design-time input handling happens at set time, not execution time.** All behaviour in §6c
  (coercion, normalisation, value transformation) is triggered by `SetParameterValueRequest`, not
  `ResolveNodeRequest`. You can confirm it without executing the node — just set the value and read
  it back. This also means it cannot be re-tested by re-running a saved workflow, since the saved
  state already contains the transformed value.

- **Some error paths may be unreachable via MCP.** If a runtime error requires specific data
  flowing through connections at execution time (e.g. a connected input providing a value of the
  wrong runtime type), it may not be triggerable through `SetParameterValueRequest` alone. Note
  these as "Requires workflow execution to test" in the output and skip them — the e2e test itself
  will cover them.

- **Record MCP constraints as you go.** During any step, if an MCP tool call fails or requires
  non-obvious arguments to succeed (e.g. `SetParameterValueRequest` needs `data_type`, or a
  connection is rejected despite matching types), record it in the `## MCP Constraints` table — do
  not bury it in Notes. The workflow skill depends on these to avoid repeating the same failures.
