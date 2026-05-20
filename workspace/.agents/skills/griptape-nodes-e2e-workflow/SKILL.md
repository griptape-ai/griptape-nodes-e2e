---
name: griptape-nodes-e2e-workflow
description: >-
  Build, validate, and save test workflows for a Griptape Node via MCP tools, driven by the
  inspection report from the griptape-nodes-e2e-inspect skill. Produces one saved workflow per
  testable section — configuration tests, design-time input handling checks, validation tests, and runtime
  error tests.
compatibility: Requires an MCP connection to a running griptape-nodes engine.
metadata:
  author: the-foundry-visionmongers
  version: '0.4'
---

# Building Test Workflows for Griptape Nodes

## Purpose

Given a target node's inspection report (`workspace/inspections/<NodeType>.inspect.md`), build one
test workflow per testable section. Each workflow exercises a specific aspect of the node — a
parameter configuration, a design-time input handling check, a validation rule, or a runtime error
condition. Workflows are built, executed against the live engine for validation, and saved as
reusable `.py` workflow files.

This skill creates engine-native workflows that can be loaded and re-run via
`RunWorkflowFromScratchRequest` at any time.

______________________________________________________________________

## Input

Before starting, read these documents:

1. **Inspection report** — `workspace/inspections/<NodeType>.inspect.md`. This is the primary
   input. Each testable section has an `<!-- id: section_id -->` comment that becomes the workflow
   filename.
2. **Confirmed Helper Nodes** — the inspection report's `## Confirmed Helper Nodes` table lists
   every helper node (input providers, assertion nodes, failure-path sinks) that was validated
   during inspection. **Use these directly** — do not re-discover helper nodes via
   `ListNodeTypesInLibraryRequest` or `DescribeNodeTypeRequest`.
3. **Runtime Observations** — the inspection report's `## Runtime Observations` table lists
   confirmed input→output pairs for each configuration. **Use these as expected values** in
   assertion nodes — they are confirmed facts from the live engine, not predictions.
4. **MCP Constraints** — the inspection report's `## MCP Constraints` table lists parameters that
   require special MCP arguments (e.g. `data_type` must be passed to `SetParameterValueRequest`).
   **Follow these constraints exactly** when setting parameter values in workflows — they prevent
   failures that are not obvious from the parameter schema.
5. **Wiki references** — consult the `griptape-nodes-e2e-wiki` skill's reference pages only when
   the inspection report's helper nodes table does not cover a node type you need (e.g. for an
   assertion node not used during inspection).

The inspection report is **required**. If it does not exist, stop and run the
`griptape-nodes-e2e-inspect` skill first.

**Check the Verdict first.** If the inspection report's `## Verdict` says `BLOCKED`, stop
immediately. Report the blockers to the user — do not attempt to build workflows for a blocked
node.

______________________________________________________________________

## MCP Tools Used

All interaction is via MCP tool calls to the running engine.

| MCP tool                         | Purpose                                                           |
| -------------------------------- | ----------------------------------------------------------------- |
| `EnsureWorkflowAndFlowRequest`   | Bootstrap a fresh workflow and flow context for each test.        |
| `CreateNodeRequest`              | Create node instances (target node, input providers, assertions). |
| `SetParameterValueRequest`       | Configure parameter values on any node.                           |
| `GetParameterValueRequest`       | Read back parameter values (for design-time checks and outputs).  |
| `CreateConnectionRequest`        | Wire node outputs to inputs.                                      |
| `DeleteConnectionRequest`        | Disconnect nodes (for connection-driven teardown).                |
| `DeleteNodeRequest`              | Remove helper nodes after use.                                    |
| `ListParametersOnNodeRequest`    | Discover parameters on a node.                                    |
| `GetParameterDetailsRequest`     | Get full schema for a parameter.                                  |
| `AutoLayoutFlowRequest`          | Arrange nodes in a readable grid before saving.                   |
| `StartFlowRequest`               | Execute the workflow (with `wait_for_completion: true`).          |
| `GetNodeResolutionStateRequest`  | Check whether a node resolved, errored, or is still executing.    |
| `ResolveNodeRequest`             | Execute a single node (for validation checks).                    |
| `SaveWorkflowRequest`            | Save the workflow to a `.py` file.                                |
| `ClearAllObjectStateRequest`     | Reset engine state between workflows.                             |
| `EventRequestBatch`              | Batch multiple requests in a single round trip for efficiency.    |
| `ListRegisteredLibrariesRequest` | Discover available libraries.                                     |
| `ListNodeTypesInLibraryRequest`  | Find node types within a library.                                 |

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

**Choose input providers from the inspection report's Confirmed Helper Nodes table.** The inspect
skill already validated which node types work for each parameter type. Only fall back to the wiki
if the helper nodes table doesn't cover the type you need.

Set the input provider's value via `SetParameterValueRequest` before connecting. The inspect
report's parameter tables tell you the type and any constraints for each input.

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

### Use the inspection report's helper nodes and observations first

The inspection report provides two tables that eliminate most discovery work:

- **Confirmed Helper Nodes** — lists every helper node validated during inspection, with library
  name, parameter, and type. Use these directly for input providers and assertion nodes.
- **Runtime Observations** — lists confirmed input→output pairs for each configuration. Use these
  as expected values in assertion nodes.

Only consult the `griptape-nodes-e2e-wiki` skill if you need a node type not listed in the helper
nodes table (e.g. a type converter or a different assertion node).

______________________________________________________________________

## Workflow Types

The inspection report contains several types of testable sections, identified by their
`<!-- id: ... -->` comment. Each type requires a different workflow structure.

### Configuration tests (`config_*`)

These test that the node produces correct outputs for a given parameter configuration.

**Structure:**

1. Create the target node.
2. For each input parameter listed in the configuration table: create an input provider node of the
   matching type, set its value, and connect it to the target node's input.
3. If the configuration is value-driven (e.g. `config_operator_eq_contains`): set the controlling
   parameter on the target node to the specified value.
4. If the configuration is connection-driven (e.g. `config_model_connected`): create the
   appropriate helper node and connect it.
5. Create assertion nodes for each output parameter that should be verified. Wire the target node's
   output to the assertion node's `actual` input. For the `expected` value, create an input
   provider node of the matching type (e.g. `TextInput` for strings, `IntegerInput` for ints) and
   connect it to the assertion's `expected` input. This makes expected values visible in the saved
   workflow. **Do not** set `expected` as a PROPERTY via `SetParameterValueRequest` — `type="any"`
   parameters have no UI widget, so the value would be invisible when reviewing the workflow.
6. If the target node has multiple control outputs (e.g. `IfElse` with `Then`/`Else`), connect the
   unexpected branch to a `CancelWorkflow` node with a descriptive `cancellation_reason`.
7. Execute and validate.

**Choosing expected values:** The inspection report's `## Runtime Observations` table contains
confirmed input→output pairs from the live engine. **Use these as your primary source for expected
values** — they are facts, not predictions. Match the inputs you set in the workflow to the inputs
recorded in the observations table, and use the corresponding outputs as assertion expected values.

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

**Do not re-run these checks.** If every row in the inspect report's "Design-time input handling"
table has `Status: Confirmed`, copy the results directly into the summary report as PASS. Only
re-run a check if the inspect report shows `Status: Discrepancy` or `Status: Unknown`.

If the section contains "None.", skip it entirely.

### Pre-execution validation tests (`error_pre_execution_*`)

These verify that the node rejects invalid parameter states before `process()` runs. These **are**
workflows — the node is created in an invalid state and the flow is expected to error when run.

If the section contains "None.", skip it entirely.

**Structure:**

For each row in the "Pre-execution validation" table:

1. Create the target node.
2. Set parameters to trigger the validation error described in the "Condition" column. If the
   condition is "parameter is empty", leave the parameter at its default (or explicitly set it to
   an empty value). If the condition requires a specific invalid value, set it.
3. Do **not** connect any input provider nodes for the parameter being validated — the point is to
   test the invalid state.
4. Execute — the flow should fail. Confirm via the `StartFlowRequest` result or
   `GetNodeResolutionStateRequest` that the node errored with a message matching the "Actual Error"
   column.

Save each validation workflow as `<NodeType>__<row_id>.py`, using the ID from the table row (e.g.
`DictGetValueByKey__error_pre_execution_empty_key.py`).

### Runtime error tests (`error_runtime_*`)

These verify that the node raises errors correctly during `process()`. These **are** workflows
because the error conditions often depend on data flowing through connections at execution time.
Each row in the inspect report's "Runtime errors" table has its own ID.

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

**For non-SuccessFailureNode nodes — hard failure only:**

A `BaseNode` has no failure path — unhandled exceptions crash the flow. The test verifies the
crash.

1. Create the target node.
2. Set parameters to trigger the runtime error.
3. Execute — the flow should crash.
4. Confirm via the `StartFlowRequest` result or `GetNodeResolutionStateRequest`.

Save as `<NodeType>__<row_id>.py`.

If the section contains "None.", skip it entirely.

______________________________________________________________________

## Execution & Validation

After building each workflow, validate it by running it:

1. Call `AutoLayoutFlowRequest` to arrange nodes in a readable layout.
2. Call `StartFlowRequest` with `wait_for_completion: true` and a generous `completion_timeout_ms`
   (30000 ms for simple workflows, longer for complex ones).
3. Check the result:
   - **Success result** — the workflow executed and all assertion nodes passed. Record as PASS.
   - **Failure result** — either the workflow errored or an assertion failed. For runtime error
     tests on `BaseNode` (non-SuccessFailureNode) targets that expect the flow to crash, a failure
     result is the correct outcome — record as PASS. For all other workflows (configuration tests,
     SuccessFailureNode error tests), a failure result means something is wrong — record as FAIL
     and include the error details.

______________________________________________________________________

## Save & Copy

After a workflow passes validation:

1. Call `SaveWorkflowRequest` with:
   - `file_name` = `<NodeType>__<section_id>` (e.g. `AssertStrings__config_default`)
   - `display_name` = `<NodeType> — <section_id>` (e.g. `AssertStrings — config_default`)
2. The response includes `file_path` — the full path where the engine saved the `.py` file.
3. Copy the file to the workspace: `workspace/tests/<NodeType>/<section_id>.py`.
4. Create the `workspace/tests/<NodeType>/` directory if it doesn't exist.

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
`workspace/inspections/<NodeType>.workflows.md`.

```markdown
# <NodeType> — Workflow Summary

Generated on <date>.

## Workflows

| Section ID | Type | Status | Workflow File |
|------------|------|--------|---------------|
| config_default | Configuration | PASS | tests/<NodeType>/config_default.py |
| config_operator_eq_contains | Configuration | PASS | tests/<NodeType>/config_operator_eq_contains.py |
| error_design_time_input | Design-time | PASS (3/3 checks) | (no workflow) |
| error_pre_execution_empty_key | Validation | PASS | tests/<NodeType>/error_pre_execution_empty_key.py |
| error_runtime_key_not_found | Runtime | PASS | tests/<NodeType>/error_runtime_key_not_found.py |

## Failures

<If any workflows or checks failed, list them here with error details. If all passed, write "None.">
```

______________________________________________________________________

## Complete Lifecycle

For each testable section in the inspection report:

1. Read the section and its <!-- id: section_id --> comment.
2. Determine the workflow type (configuration, design-time input handling, validation, runtime).
3. If design-time input handling:
   - Copy confirmed results from inspect report to summary (do not re-run)
   - Re-run only if any row has Status: Discrepancy or Unknown
4. If configuration, validation, or runtime:
   - EnsureWorkflowAndFlowRequest (display_name = "<NodeType> — \<section_id>")
   - CreateNodeRequest for target node
   - CreateNodeRequest for input providers
   - SetParameterValueRequest to configure all nodes
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
5. After all sections: write summary report.

______________________________________________________________________

## Tips

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

- **Match the inspect report's confirmed values.** The inspection report's "Actual" columns are the
  ground truth. If the report says a design-time handler produces `""`, assert for `""`, even if
  the survey predicted something different.

- **Library names matter.** When creating nodes via `CreateNodeRequest`, always pass
  `specific_library_name` to avoid ambiguity. The inspection report's Confirmed Helper Nodes table
  includes the library name for every helper. The inspection report's header includes the library
  name for the target node.

- **SuccessFailureNode error tests wire both paths.** Every runtime error on a `SuccessFailureNode`
  gets one workflow with both `failure` (→ assertion) and `exec_out` (→ `CancelWorkflow`)
  connected. The flow succeeds if the expected failure path fires; it crashes if the unexpected
  success path fires.
