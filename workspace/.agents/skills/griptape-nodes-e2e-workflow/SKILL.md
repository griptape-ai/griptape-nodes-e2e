---
name: griptape-nodes-e2e-workflow
description: >-
  Build, validate, and save test workflows for a Griptape Node via MCP tools, driven by the test
  plan. The plan is the sole input — it contains configuration tests, error tests, helper nodes,
  MCP constraints, and everything else needed to generate workflows. Produces one saved workflow
  per testable section. The output root directory must be provided in the task prompt.
compatibility: Requires an MCP connection to a running griptape-nodes engine.
metadata:
  author: the-foundry-visionmongers
  version: '0.7'
---

# Building Test Workflows for Griptape Nodes

## Purpose

Given a target node's test plan (`{output_root}/inspections/<NodeType>.plan.md`), build one test
workflow per testable section. Each workflow exercises a specific aspect of the node — a parameter
configuration, a design-time input handling check, a validation rule, or a runtime error condition.
Workflows are built, executed against the live engine for validation, and saved as reusable `.py`
workflow files.

This skill creates engine-native workflows that can be loaded and re-run via
`RunWorkflowFromScratchRequest` at any time.

______________________________________________________________________

## Output Root

The output root directory is provided in your task prompt as an absolute path. Use it exactly as
given. Do not infer, guess, or silently default to any other path. If your task prompt does not
contain an explicit output root path, stop immediately and return an error message stating that the
output root directory was not provided.

Plans are read from `{output_root}/inspections/` and test workflows are saved to
`{output_root}/tests/`. Store the confirmed path and use it for all file reads and writes
throughout this skill.

______________________________________________________________________

## Input

Read the test plan at `{output_root}/inspections/<NodeType>.plan.md`. If it does not exist, stop
and tell the user to run the `griptape-nodes-e2e-plan` skill first.

The plan contains the following sections, all of which this skill uses:

1. **Node Identity** — node type, library, base class, status parameters, and control outputs.
   Determines the error test workflow structure (SuccessFailureNode wiring vs TryCatchGroup).
2. **Default Parameter Surface** — the baseline parameter table. Configuration tests start from
   these defaults; only the parameters listed in each test row's "Parameters Changed" column are
   modified.
3. **Configuration Tests** — each row becomes one configuration test workflow. Rows with
   Testability = `construction-time` are skipped.
4. **Error Tests** — design-time input handling, pre-execution validation, and runtime error
   sections. Each confirmed row with a unique ID becomes one error test workflow.
5. **Helper Nodes** — confirmed helper nodes (input providers, assertion nodes, failure-path
   sinks). **Use these directly** — do not re-discover helper nodes via
   `ListNodeTypesInLibraryRequest` or `DescribeNodeTypeRequest`.
6. **MCP Constraints** — parameters that require special MCP arguments (e.g. `data_type` must be
   passed to `SetParameterValueRequest`). **Follow these constraints exactly.**
7. **Runtime Observations** — confirmed input→output pairs. **Use these as expected values** in
   assertion nodes — they are confirmed facts from the live engine, not predictions.
8. **Caveats** — environment dependencies, known limitations, and other notes affecting test
   execution.

Consult the `griptape-nodes-e2e-wiki` skill's reference pages only when the plan's Helper Nodes
table does not cover a node type you need (e.g. for an assertion node not used during inspection).

______________________________________________________________________

## MCP Tools Used

All interaction is via MCP tool calls to the running engine.

| MCP tool                         | Purpose                                                             |
| -------------------------------- | ------------------------------------------------------------------- |
| `EnsureWorkflowAndFlowRequest`   | Bootstrap a fresh workflow and flow context for each test.          |
| `CreateNodeRequest`              | Create node instances (target node, input providers, assertions).   |
| `SetParameterValueRequest`       | Configure parameter values on any node.                             |
| `GetParameterValueRequest`       | Read back parameter values (for design-time checks and outputs).    |
| `CreateConnectionRequest`        | Wire node outputs to inputs.                                        |
| `DeleteConnectionRequest`        | Disconnect nodes (for connection-driven teardown).                  |
| `DeleteNodeRequest`              | Remove helper nodes after use.                                      |
| `ListParametersOnNodeRequest`    | Discover parameters on a node.                                      |
| `GetParameterDetailsRequest`     | Get full schema for a parameter.                                    |
| `AutoLayoutFlowRequest`          | Arrange nodes in a readable grid before saving.                     |
| `StartFlowRequest`               | Execute the workflow (with `wait_for_completion: true`).            |
| `GetNodeResolutionStateRequest`  | Check whether a node resolved, errored, or is still executing.      |
| `ResolveNodeRequest`             | Execute a single node (for validation checks).                      |
| `SaveWorkflowRequest`            | Save the workflow to a `.py` file.                                  |
| `ClearAllObjectStateRequest`     | Reset engine state between workflows.                               |
| `EventRequestBatch`              | Batch multiple requests in a single round trip for efficiency.      |
| `ListRegisteredLibrariesRequest` | Discover available libraries.                                       |
| `ListNodeTypesInLibraryRequest`  | Find node types within a library.                                   |
| `AddParameterToNodeRequest`      | Create a slot on an expander-style ParameterList before connecting. |

______________________________________________________________________

## Workflow Design Principles

### Self-contained workflows

Each workflow is fully independent. It starts with `EnsureWorkflowAndFlowRequest` and ends with
`SaveWorkflowRequest` + `ClearAllObjectStateRequest`. A failure in one workflow does not prevent
building the next.

### Use input provider nodes for test data

Never rely on default values alone to exercise a node. Create explicit input provider nodes and
connect them to the target node's inputs. This makes the test data visible in the saved workflow
and easy to modify.

**Choose input providers from the plan's Helper Nodes table.** Only fall back to the wiki if the
helper nodes table doesn't cover the type you need.

Set the input provider's value via `SetParameterValueRequest` before connecting. The plan's Default
Parameter Surface table tells you the type and any constraints for each input.

### Use assertion nodes for validation

Wire the target node's outputs to assertion nodes (`AssertEqual`, `AssertStrings`, `AssertNumbers`,
`AssertTrue`) to validate correctness within the workflow itself. Consult the wiki's
[parameter compatibility matrix](references/parameter-compatibility.md) to pick the right assertion
node for each output type.

Always set the `message` parameter on assertion nodes to something descriptive — e.g.
`"<NodeType>.<param_name> should equal <expected>"`. This makes failures easy to diagnose when the
workflow is re-run later.

### Use CancelWorkflow for unexpected control paths

When a workflow tests a specific control branch, the *other* branch should never fire. Connect
unexpected control outputs to a `CancelWorkflow` node (from `Griptape Nodes Library`). This crashes
the flow with a descriptive error if the wrong branch is taken, making failures obvious in CI. Set
`cancellation_reason` to explain which path was unexpected — e.g.
`"Then branch should not fire when evaluate=false"`.

**Example:** When testing `IfElse` with `evaluate=false`, the `Else` branch is expected. Connect
`IfElse.Then → CancelWorkflow.exec_in` so the flow crashes if `Then` fires.

### Route SuccessFailureNode failure to the assertion node

When testing `SuccessFailureNode` **graceful failure** paths, connect the target node's `failure`
control output directly to the assertion node's `exec_in`. This gives the failure path somewhere to
go (enabling the graceful failure behaviour where `was_successful=False`), and also ensures the
assertion runs when the failure path is taken. There is no need for a separate sink node.

### Never connect assertion nodes' failure output

Assertion nodes (`AssertEqual`, `AssertTrue`, `AssertStrings`, `AssertNumbers`) are
`SuccessFailureNode`s with a `failure` control output. **Do not connect `failure` to anything.** If
the assertion fails, the flow must crash — this is the correct behaviour for CI, where a crashed
flow means a failed test. Connecting `failure` to a sink would make assertion failures graceful,
producing false positives when workflows are re-run.

### Never connect to hidden parameters

Some nodes (e.g. `DataNode` subclasses like `LoggerNode`) hide their control parameters (`exec_in`,
`exec_out`) via `ui_options["hide"]=True`. **Do not connect to hidden parameters.** The visual
display shows "Hidden & Connected", which makes the workflow impossible to understand when opened
in the editor. If you need a control-flow sink, use a node with visible control parameters (e.g.
`CancelWorkflow`).

### Use the plan's helper nodes and observations first

The plan provides two tables that eliminate most discovery work:

- **Helper Nodes** — lists every helper node validated during inspection, with library name,
  parameter, and type. Use these directly for input providers and assertion nodes.
- **Runtime Observations** — lists confirmed input→output pairs for each configuration. Use these
  as expected values in assertion nodes.

Only consult the `griptape-nodes-e2e-wiki` skill if you need a node type not listed in the helper
nodes table (e.g. a type converter or a different assertion node).

______________________________________________________________________

## Workflow Types

### Testability check — skip construction-time sections

Before processing any testable section, check its **Testability** value. If the value is
`construction-time`, **skip the section entirely** — do not build, execute, or save a workflow for
it. Record the skip in the summary as:

```
| section_id | Construction-time | SKIPPED — construction-time only; requires phase-2 test script | (no workflow) |
```

Construction-time sections document parameter surface mutations (type changes, `input_types`
narrowing) that occur during workflow construction and are baked into the saved state. A saved
workflow cannot re-test them.

If the value is `static-workflow`, process the section normally.

### Configuration tests (`config_*`)

These test that the node produces correct outputs for a given parameter configuration. Each row in
the plan's `## Configuration Tests` table becomes one workflow.

For each row, use the "Parameters Changed from Default" column to determine which parameters to
set. All parameters not listed should remain at their default values (from the plan's
`## Default Parameter Surface` table).

**Structure:**

1. Create the target node.
2. For each parameter listed in the row's "Parameters Changed from Default" column: set the
   parameter on the target node to the specified value (or create an input provider node and
   connect it, if the MCP Constraints table requires a connection to bypass enforcement).
3. For any required input parameters not listed in "Parameters Changed" (e.g. `prompt` needs a
   non-empty value for the node to execute): create an input provider node, set its value, and
   connect it.
4. Create assertion nodes for each output parameter that should be verified. Wire the target node's
   output to the assertion node's `actual` input. For the `expected` value, create an input
   provider node of the matching type (e.g. `TextInput` for strings, `IntegerInput` for ints) and
   connect it to the assertion's `expected` input. This makes expected values visible in the saved
   workflow. **Do not** set `expected` as a PROPERTY via `SetParameterValueRequest` — `type="any"`
   parameters have no UI widget, so the value would be invisible when reviewing the workflow.
5. If the target node has multiple control outputs (e.g. `IfElse` with `Then`/`Else`), connect the
   unexpected branch to a `CancelWorkflow` node with a descriptive `cancellation_reason`.
6. Execute and validate.

**Choosing expected values:** The plan's `## Runtime Observations` table contains confirmed
input→output pairs from the live engine. **Use these as your primary source for expected values** —
they are facts, not predictions. Match the inputs you set in the workflow to the inputs recorded in
the observations table, and use the corresponding outputs as assertion expected values.

If the observations table does not cover the specific input combination you need, or if you need to
use different inputs (e.g. to differentiate between configurations), derive expected values from
the node's description and the observation patterns. For simple pass-through nodes (e.g.
`TextInput`), the expected output equals the input. For transformation nodes (e.g. `ToFloat`),
compute the expected result.

**Example — testing `AssertStrings` in `config_default`:**

```
TextInput_1.text = "hello world"     →  AssertStrings_1.actual
TextInput_2.text = "hello world"     →  AssertStrings_1.expected
(AssertStrings_1.operator = "==" — already the default)
```

The workflow should execute successfully because `"hello world" == "hello world"`.

### Design-time input handling tests (`error_design_time_input`)

Design-time input handling (coercion, normalisation, value transformation) is confirmed during the
inspect phase and **cannot be re-tested by running a saved workflow** — the saved state contains
the already-transformed value, so the behaviour never re-fires on re-run.

**Do not re-run these checks.** If every row in the plan's "Design-time input handling" table has
`Status: Confirmed`, copy the results directly into the summary report as PASS. Only re-run a check
if the plan shows `Status: Discrepancy` or `Status: Unknown`.

If the section contains "None.", skip it entirely.

### Pre-execution validation tests (`error_pre_execution_*`)

These verify that the node rejects invalid parameter states before `process()` runs. Pre-execution
validation errors crash the flow before any control path fires — neither `failure` nor `exec_out`
resolves, regardless of the node's base class. To catch and assert on the error, wrap the target
node in a `TryCatchGroup` (from `Griptape Nodes Testing Library`).

If the section contains "None.", skip it entirely.

**Structure:**

For each row in the plan's "Pre-execution validation" table:

1. Create a `TryCatchGroup` node.
2. Create the target node **inside** the TryCatchGroup group.
3. Set parameters to trigger the validation error described in the "Condition" column. If the
   condition is "parameter is empty", leave the parameter at its default (or explicitly set it to
   an empty value). If the condition requires a specific invalid value, set it.
4. Do **not** connect any input provider nodes for the parameter being validated — the point is to
   test the invalid state.
5. Connect the TryCatchGroup's `failure` control output to an `AssertStrings` node's `exec_in`.
   This is the expected path — it fires when the child node's validation raises an exception.
6. Connect the TryCatchGroup's `exec_out` (Succeeded) control output to a `CancelWorkflow` node.
   This is the unexpected path — if the child node passes validation when it should fail, the flow
   crashes with a descriptive error.
7. Connect the TryCatchGroup's `error_message` output to `AssertStrings.actual`. Create a
   `TextInput` node with the expected error substring (from the plan's "Actual Error" column) and
   connect it to `AssertStrings.expected`. Set `AssertStrings.operator` to `contains`.
8. Execute and validate — the flow should succeed (not crash), the failure path should fire, and
   the assertion on the error message should pass.
9. **Do not** connect the `AssertStrings`'s own `failure` output — if the assertion fails, the flow
   should crash.

Save each validation workflow as `<NodeType>__<row_id>.py`, using the ID from the table row (e.g.
`DictGetValueByKey__error_pre_execution_empty_key.py`).

### Runtime error tests (`error_runtime_*`)

These verify that the node raises errors correctly during `process()`. These **are** workflows
because the error conditions often depend on data flowing through connections at execution time.
Each row in the plan's "Runtime errors" table has its own ID.

Check the plan's `## Node Identity` section for the base class to determine the workflow structure:

**For SuccessFailureNode nodes — one workflow per error, both paths wired:**

A `SuccessFailureNode` always routes through either `exec_out` (success) or `failure` (failure) —
it never crashes. The test verifies that the expected path fires and the unexpected path does not.

1. Create the target node.
2. Connect the target node's `failure` control output to an `AssertEqual` node's `exec_in`. This is
   the expected path — it fires when the error condition triggers.
3. Connect the target node's `exec_out` (success) control output to a `CancelWorkflow` node. This
   is the unexpected path — if the node succeeds when it should fail, the flow crashes with a
   descriptive error.
4. Set parameters to trigger the runtime error (per the "Condition" column).
5. Connect the target node's `was_successful` output to `AssertEqual.actual`. Create a `BoolInput`
   node, set its value to `False`, and connect it to `AssertEqual.expected`. This asserts that the
   target node reports failure.
6. Optionally wire `result_details` to an `AssertStrings` node to verify the error message.
7. Execute and validate — the flow should succeed (not crash), the failure path should fire, and
   the assertions should pass.
8. **Do not** connect the `AssertEqual`'s own `failure` output — if the assertion fails, the flow
   should crash.

Save this workflow as `<NodeType>__<row_id>.py` (e.g.
`DictGetValueByKey__error_runtime_key_not_found.py`).

**For non-SuccessFailureNode nodes — wrap in TryCatchGroup:**

A `BaseNode` has no failure path — unhandled exceptions crash the flow. To test that the error is
raised correctly while keeping the overall workflow passing, wrap the target node inside a
`TryCatchGroup` (from `Griptape Nodes Testing Library`). The group catches the exception and routes
control flow to Succeeded/Failed, just like a SuccessFailureNode.

1. Create a `TryCatchGroup` node.
2. Create the target node **inside** the TryCatchGroup group.
3. Set the target node's parameters to trigger the runtime error (per the "Condition" column).
4. Connect the TryCatchGroup's `failure` control output to an `AssertStrings` node's `exec_in`.
   This is the expected path — it fires when the child node raises an exception.
5. Connect the TryCatchGroup's `exec_out` (Succeeded) control output to a `CancelWorkflow` node.
   This is the unexpected path — if the child node succeeds when it should fail, the flow crashes
   with a descriptive error.
6. Connect the TryCatchGroup's `error_message` output to `AssertStrings.actual`. Create a
   `TextInput` node with the expected error substring and connect it to `AssertStrings.expected`.
   Set `AssertStrings.operator` to `contains`.
7. Execute and validate — the flow should succeed (not crash), the failure path should fire, and
   the assertion on the error message should pass.
8. **Do not** connect the `AssertStrings`'s own `failure` output — if the assertion fails, the flow
   should crash.

Save as `<NodeType>__<row_id>.py`.

If the section contains "None.", skip it entirely.

______________________________________________________________________

## Execution & Validation

After building each workflow, validate it by running it:

1. Call `AutoLayoutFlowRequest` to arrange nodes in a readable layout.
2. Call `StartFlowRequest` with `wait_for_completion: true` and a generous `completion_timeout_ms`
   (10000 ms for simple workflows, 300000 for complex ones that include a remote API call).
3. Check the result:
   - **Success result** — the workflow executed and all assertion nodes passed. Record as PASS.
   - **Failure result** — either the workflow errored or an assertion failed. A failure result
     means something is wrong — record as FAIL and include the error details.

______________________________________________________________________

## Save & Copy

After a workflow passes validation:

1. Call `SaveWorkflowRequest` with:
   - `file_name` = `<NodeType>__<section_id>` (e.g. `AssertStrings__config_default`)
   - `display_name` = `<NodeType> — <section_id>` (e.g. `AssertStrings — config_default`)
2. The response includes `file_path` — the full path where the engine saved the `.py` file.
3. Copy the file to `{output_root}/tests/<NodeType>/<section_id>.py`.
4. Create the `{output_root}/tests/<NodeType>/` directory if it doesn't exist.

After saving, call `ClearAllObjectStateRequest` to reset the engine for the next workflow.

Do **not** delete the workflow files from the engine's workspace directory. They should remain so
that humans can open and inspect them in the editor after generation.

______________________________________________________________________

## Cleanup

Between each workflow:

1. Call `ClearAllObjectStateRequest` with `i_know_what_im_doing: true`.
2. Wait for confirmation before starting the next workflow.

______________________________________________________________________

## Output Format

After processing all sections, write a summary report to
`{output_root}/inspections/<NodeType>.workflows.md`.

```markdown
# <NodeType> — Workflow Summary

Generated on <date>.
Plan: `<NodeType>.plan.md`

## Workflows

### Configuration tests

| Section ID | Parameters Changed | Source | Status | Workflow File |
|------------|-------------------|--------|--------|---------------|
| config_default | (all defaults) | inspection | PASS | {output_root}/tests/<NodeType>/config_default.py |
| config_<axis> | <param>=<value> | inspection | PASS | {output_root}/tests/<NodeType>/config_<axis>.py |
| config_<name> | <param>=<value> | plan | PASS | {output_root}/tests/<NodeType>/config_<name>.py |

### Error tests

| Section ID | Type | Status | Workflow File |
|------------|------|--------|---------------|
| error_design_time_input | Design-time | PASS (3/3 checks) | (no workflow) |
| error_pre_execution_<condition> | Validation | PASS | {output_root}/tests/<NodeType>/error_pre_execution_<condition>.py |
| error_runtime_<condition> | Runtime | PASS | {output_root}/tests/<NodeType>/error_runtime_<condition>.py |

### Omitted

| Section ID or Condition | Reason |
|------------------------|--------|
| <from plan's Omitted Tests table> | <reason> |

## Failures

<If any workflows or checks failed, list them here with error details. If all passed, write "None.">
```

______________________________________________________________________

## Complete Lifecycle

### Phase 0: Read the plan

1. Read the test plan at `{output_root}/inspections/<NodeType>.plan.md`. If it does not exist,
   **stop** and tell the user to run the `griptape-nodes-e2e-plan` skill first.
2. Read the plan's `## Node Identity` section to determine the node type, library, and base class.
3. Read the plan's `## Caveats` section for environment dependencies and limitations.
4. Build the list of workflows to generate:
   - From the **Configuration Tests** table: each row with Testability = `static-workflow`.
   - From the **Error Tests** section: each design-time, pre-execution, and runtime error section.
5. Note all helper nodes, MCP constraints, and runtime observations from the plan for use during
   workflow construction.

### Phase 1: Process error tests

For each error test section in the plan:

1. Check the testability tag. If `construction-time`, skip and record as SKIPPED.
2. Determine the type (design-time input handling, validation, runtime).
3. If design-time input handling:
   - Copy confirmed results from the plan to the summary (do not re-run)
   - Re-run only if any row has Status: Discrepancy or Unknown
4. If validation or runtime:
   - EnsureWorkflowAndFlowRequest (display_name = "<NodeType> — \<section_id>")
   - CreateNodeRequest for target node (use node type and library from Node Identity)
   - CreateNodeRequest for input providers
   - SetParameterValueRequest to configure all nodes (follow MCP Constraints)
   - CreateNodeRequest for assertion nodes, CancelWorkflow for unexpected paths
   - SetParameterValueRequest for assertion expected values and messages (use input provider nodes
     for expected values, not direct PROPERTY sets)
   - CreateConnectionRequest to wire everything
   - AutoLayoutFlowRequest
   - StartFlowRequest (wait_for_completion = true)
   - Check result — PASS or FAIL
   - SaveWorkflowRequest (file_name = "<NodeType>\_\_\<section_id>")
   - Copy saved file to tests/<NodeType>/\<section_id>.py
   - ClearAllObjectStateRequest

### Phase 2: Process configuration tests

For each row in the plan's Configuration Tests table with Testability = `static-workflow`:

1. Read the "Parameters Changed from Default" column and the Default Parameter Surface table.
2. Build the workflow:
   - EnsureWorkflowAndFlowRequest (display_name = "<NodeType> — \<section_id>")
   - CreateNodeRequest for target node
   - Set the parameters specified in the row
   - CreateNodeRequest for input providers (prompt text, etc.)
   - CreateNodeRequest for assertion nodes
   - SetParameterValueRequest for assertion expected values and messages
   - CreateConnectionRequest to wire everything
   - AutoLayoutFlowRequest
   - StartFlowRequest (wait_for_completion = true)
   - Check result — PASS or FAIL
   - SaveWorkflowRequest (file_name = "<NodeType>\_\_\<section_id>")
   - Copy saved file to tests/<NodeType>/\<section_id>.py
   - ClearAllObjectStateRequest

### Phase 3: Write summary report

After all sections and configuration rows: write the summary report.

______________________________________________________________________

## Tips

- **`GT_CLOUD_API_KEY` is always available — execute proxy-backed workflows.** The griptape-nodes
  engine has `GT_CLOUD_API_KEY` configured in its secrets. This key proxies requests to external
  services (OpenAI, Anthropic, etc.) via the Griptape Cloud proxy. Workflows for nodes that use
  this proxy should always be executed during test generation, not saved without execution. If a
  plan's Caveats section mentions `GT_CLOUD_API_KEY` or generic "API credentials" as a requirement,
  disregard it — that key is present. However, if the plan mentions a *different* credential that
  is genuinely absent (e.g. a direct third-party key not covered by the proxy), respect that
  caveat. Use a generous `completion_timeout_ms` (e.g. 300000 ms) for API-calling workflows since
  external calls are slower than local-only workflows.

- **Use `EventRequestBatch` for efficiency.** When creating multiple nodes or setting multiple
  parameter values, batch them into a single `EventRequestBatch` call. This reduces round trips and
  speeds up workflow construction. Batch independent operations (e.g. creating all input provider
  nodes at once), but keep dependent operations sequential (e.g. create a node before setting its
  parameters).

- **Auto-layout before saving.** Always call `AutoLayoutFlowRequest` before `SaveWorkflowRequest`.
  This ensures the workflow has a clean visual layout when opened in the editor, making it easier
  to inspect and debug.

- **Set descriptive assertion messages.** Every assertion node should have its `message` parameter
  set to describe what is being checked — e.g. `"ToFloat output should be 3.14 for input '3.14'"`.
  When a workflow fails on re-run, the message tells the operator exactly what went wrong without
  reading the graph.

- **Test data should be deterministic.** Choose input values that produce predictable,
  deterministic outputs. Avoid random data, timestamps, or values that depend on external state.
  Good examples: `"hello world"`, `42`, `3.14`, `True`.

- **Configuration tests need meaningful inputs.** Don't just set the controlling parameter —
  provide actual input data through input provider nodes and verify the output. A configuration
  test that only checks the parameter surface (without execution) is just repeating the inspect
  skill's work. Use the Runtime Observations table for confirmed input→output pairs.

- **Runtime error workflows should be minimal.** Only include the nodes necessary to trigger the
  error condition. Don't add extra input providers or assertions beyond what's needed to verify the
  error path.

- **Handle "None." sections gracefully.** If a section's content is just "None.", skip it entirely
  — don't create a workflow or record a check. Note the skip in the summary report.

- **Match the plan's confirmed values.** The plan's error tables carry forward the "Actual" columns
  from the inspection. These are the ground truth. If the plan says a design-time handler produces
  `""`, assert for `""`, even if you might expect something different.

- **Library names matter.** When creating nodes via `CreateNodeRequest`, always pass
  `specific_library_name` to avoid ambiguity. The plan's Helper Nodes table includes the library
  name for every helper. The plan's Node Identity section includes the library name for the target
  node.

- **SuccessFailureNode error tests wire both paths.** Every runtime error on a `SuccessFailureNode`
  gets one workflow with both `failure` (→ assertion) and `exec_out` (→ `CancelWorkflow`)
  connected. The flow succeeds if the expected failure path fires; it crashes if the unexpected
  success path fires.

- **Connecting to expander-style ParameterList inputs.** Some parameters (identified as
  `ui_options: {"expander": true}` in the plan's MCP Constraints table) do not accept a direct
  connection — the parameter is a container, not a slot. Before calling `CreateConnectionRequest`,
  you must create a slot with `AddParameterToNodeRequest`:

  1. Call `AddParameterToNodeRequest` with `node_name=<target_node>` and
     `parent_container_name=<param_name>` (e.g. `"input_images"`).
  2. The response `parameter_name` field contains the UUID slot name (e.g.
     `input_images_ParameterListUniqueParamID_<hex>`).
  3. Use that UUID slot name as `target_parameter_name` in `CreateConnectionRequest`.
