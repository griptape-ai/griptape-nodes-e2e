---
name: griptape-nodes-e2e-survey
description: >-
  Given a node class name, locate its source code via MCP tools and analyse it to enumerate all
  parameter configurations — value-driven, connection-driven, and UI-message-driven. Produces a
  survey document that guides the inspect skill's live exploration.
compatibility: Requires an MCP connection to a running griptape-nodes engine (extended tools mode).
metadata:
  author: the-foundry-visionmongers
  version: '0.4'
---

# Surveying Griptape Nodes

## Purpose

Given a target node class name, locate its source code via MCP tools, read it, and produce a
markdown document listing every **configuration axis** and the expected parameter surface for each.
This document feeds into the `griptape-nodes-e2e-inspect` skill, which confirms predictions against
a live engine.

A configuration axis is anything that changes the node's parameter surface at design time —
dropdown values, slider positions, boolean toggles, incoming connections, UI buttons, or batch
transitions. The survey captures all of these uniformly.

______________________________________________________________________

## MCP Tools Used

Source paths are discovered at runtime via MCP tools. No user-provided paths are needed.

| MCP tool                         | Purpose                                                                   |
| -------------------------------- | ------------------------------------------------------------------------- |
| `ListRegisteredLibrariesRequest` | List all registered library names.                                        |
| `ListNodeTypesInLibraryRequest`  | List node class names in a library. Args: `library`.                      |
| `GetLibrarySourceInfoRequest`    | Get the filesystem path of a library's source directory. Args: `library`. |
| `GetEngineSourceInfoRequest`     | Get the filesystem path of the engine source tree.                        |

______________________________________________________________________

## Locating the Source Code

### Step 1: Find the node's library

Call `ListRegisteredLibrariesRequest` to get all library names. For each library, call
`ListNodeTypesInLibraryRequest` and check whether the target class name appears.

- **Found in exactly one library** — proceed with that library.
- **Found in multiple libraries** — stop and ask the user which library they mean.
- **Not found in any library** — stop and tell the user the class name was not found.

Record the **library name** — it is included in the survey output header and used by the inspect
skill.

### Step 2: Get source paths

Call both MCP tools to get filesystem paths:

1. `GetLibrarySourceInfoRequest` with the library name — returns `library_directory` (the directory
   containing `griptape_nodes_library.json` and node source files).
2. `GetEngineSourceInfoRequest` — returns `package_directory` (the engine source root).

### Step 3: Find the node's file path

Read `griptape_nodes_library.json` in the library directory. Locate the entry in the `"nodes"`
array whose `"class_name"` matches the target node type. The `"file_path"` field gives the path to
the Python file, relative to the library directory.

### Step 4: Read the node source

Read the Python file at the resolved path.

### Step 5: Follow the inheritance chain

If the node inherits from a base class:

- **Within the same library** — follow the import and read the parent class file.
- **From the engine** (`griptape_nodes.exe_types`) — read the base class from the engine source
  directory returned by `GetEngineSourceInfoRequest`. The relevant files are under `exe_types/`
  (e.g. `node_types.py` for `BaseNode`, `DataNode`, `ControlNode`, `SuccessFailureNode`). Common
  base classes:
  - `BaseNode` — minimal, no extra parameters.
  - `DataNode` — adds hidden control parameters (`exec_in`, `exec_out`).
  - `SuccessFailureNode` — adds control parameters (`exec_in`, `exec_out`, `failure`). Subclasses
    typically also call `_create_status_parameters()` to add `was_successful` and `result_details`.

Stop following the chain when you reach an engine base class (these are well-known and don't need
further traversal).

______________________________________________________________________

## What to Extract

### 1. Static parameters

Parameters added in `__init__` via `add_parameter()` calls that are **always present** regardless
of configuration. For each, note:

- `name` — the parameter name string.
- `type` — the `type` argument (e.g. `"str"`, `"int"`, `"ImageUrlArtifact"`).
- `input_types` — the `input_types` list if provided, otherwise inferred from `type`.
- `output_type` — the `output_type` if provided.
- `allowed_modes` — the set of `ParameterMode` values (INPUT, OUTPUT, PROPERTY).
- `default_value` — the `default_value` argument if present.
- `tooltip` — the `tooltip` string.
- `traits` — any traits applied, especially:
  - `Options(choices=[...])` — marks a dropdown; list all choices.
  - `Slider(min=..., max=...)` — marks a slider; note range.
  - `AddParameterButton(...)` — marks a user-extensible parameter set.
- `hide` — whether `hide=True` is passed to the Parameter constructor.

### 2. Value-driven configurations

Look for `after_value_set` method overrides. For each controlling parameter (one that triggers
parameter surface changes when its value is set), document:

- Which parameter controls the transition.
- For each value (or value range), what changes: parameters added, removed, shown, hidden, types
  changed, traits modified, modes changed.

**Important:** Not all `after_value_set` handlers cause parameter surface mutations. Some only
update output values or trigger recomputation. Only document configurations where the parameter
**surface** changes (parameters added, removed, hidden, shown, types changed, modes changed).

Patterns to look for:

- `add_parameter()` / `remove_parameter_element_by_name()` — parameters created or destroyed.
- `hide_parameter_by_name()` / `show_parameter_by_name()` — visibility toggled.
- `parameter.type = ...` / `parameter.input_types = ...` — type changed dynamically.
- Trait manipulation (adding/removing `Options`, changing `choices`).

### 3. Connection-driven configurations

Look for overrides of:

- `after_incoming_connection(source_node, source_parameter, target_parameter)`
- `after_outgoing_connection(target_node, target_parameter, source_parameter)`
- `after_incoming_connection_removed(...)`
- `after_outgoing_connection_removed(...)`

Connection callbacks can only inspect **static type metadata** from the connected parameter —
`type`, `output_type`, `input_types`. They never see runtime data values. This means
connection-driven configurations are fully deterministic based on the type of the connected node's
parameter.

For each connection-driven configuration, document:

- Which target parameter triggers the behaviour.
- What source parameter property is inspected (typically `output_type`).
- What changes when connected: parameters hidden/shown, types changed, traits added/removed, modes
  changed.
- What happens when disconnected (the `_removed` variant) — typically a revert to default state.

Name connection-driven configurations by what is connected, not by the callback method. For
example: `model ← PromptModelConfig (connected)` not `after_incoming_connection for model`.

### 4. UI-message-driven configurations

Look for:

- `on_node_message_received` method overrides.
- Parameters with the `AddParameterButton` trait.

Document what parameters can be added by user action and what template they follow.

### 5. ParameterTransitionComponent configurations

Look for use of `ParameterTransitionComponent` with `transition_to()` calls. These perform batch
transitions that add, remove, and replace parameters in a single operation. Document:

- Which parameter controls the transition (typically a dropdown).
- For each transition target, the set of `TransitionParameter` entries: name, allowed_modes,
  input_types, output_type.

### 6. Base class contributions

Document parameters or hooks inherited from parent classes. For well-known engine base classes, use
the following reference:

| Base class           | Inherited parameters                                                                                             | Error handling                                                                                                               |
| -------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `BaseNode`           | (none beyond engine internals)                                                                                   | Unhandled exceptions in `process()` crash the flow with `NodeErrorEvent`.                                                    |
| `ControlNode`        | `exec_in` (control-in), `exec_out` (control-out)                                                                 | Same as `BaseNode`.                                                                                                          |
| `DataNode`           | `exec_in` (control-in, hidden), `exec_out` (control-out, hidden)                                                 | Same as `BaseNode`.                                                                                                          |
| `SuccessFailureNode` | `exec_in` (control-in), `exec_out` (control-out, display "Succeeded"), `failure` (control-out, display "Failed") | `_handle_failure_exception(e)`: if `failure` output is connected → logs error, continues along "Failed" path; else → raises. |

**`_create_status_parameters()` (opt-in):** Many `SuccessFailureNode` subclasses call this helper
in their `__init__` to add `was_successful` (output, bool) and `result_details` (output, str)
inside a collapsible "Status" `ParameterGroup`. Check whether the target node calls it — if so,
include these parameters in the survey. They are added to the node's element tree via a
`ParameterGroup`, not as top-level parameters.

### 7. Error behaviours

Nodes surface errors through several distinct mechanisms. The survey must identify which ones a
node uses so the inspect skill can confirm them against the live engine and the test matrix can
cover failure paths.

#### 7a. SuccessFailureNode base class

If the node (or any ancestor) extends `SuccessFailureNode`, it automatically has:

- **Two control outputs:** `exec_out` (display "Succeeded") and `failure` (display "Failed").
- **`_handle_failure_exception(exception)`** — behaviour depends on whether the `failure` output
  has outgoing connections:
  - **Connected:** logs the error and continues execution along the "Failed" path (graceful
    failure).
  - **Not connected:** raises the exception, crashing the flow with a `NodeErrorEvent`.
- **Status parameters** (if `_create_status_parameters()` is called in `__init__`):
  `was_successful` (bool, output) and `result_details` (str, output) inside a collapsible "Status"
  `ParameterGroup`.

Document: that the node is a `SuccessFailureNode`, whether it calls `_create_status_parameters()`,
and all call sites of `_handle_failure_exception` with the conditions that trigger them.

#### 7b. Pre-execution validation (`validate_before_node_run`)

Look for overrides of `validate_before_node_run()`. This method runs before `process()` and returns
a list of `Exception` objects. If any are returned, the workflow transitions to `ERRORED` and
`process()` never runs.

For each validation check, document:

- Which parameter is being validated.
- What condition triggers the error (empty, wrong type, out of range, etc.).
- The error message pattern.

Also check for `validate_before_workflow_run()`, which runs before the entire workflow starts.

Common helper: `validate_empty_parameter(param, additional_msg)` — returns a `ValueError` if the
named parameter is empty or whitespace-only.

#### 7c. Design-time input handling (`before_value_set` / `set_parameter_value`)

Some nodes perform non-trivial work when parameter values are set at design time, rather than
waiting until `process()` runs. This is a broader category than just error handling — it includes
any transformation, normalisation, or side effect triggered by setting a parameter value. Look for:

- `before_value_set()` overrides that silently convert invalid types to safe defaults (e.g.
  non-string key → `""`, non-dict input → `{}`).
- `set_parameter_value()` overrides that intercept and normalise values before calling `super()`.
- Any logic in these methods that mutates other parameters, changes types, or updates traits as a
  side effect of setting a value. (Note: `after_value_set` mutations are already covered in §2
  "Value-driven configurations" — this section covers `before_value_set` / `set_parameter_value`
  specifically.)

For each design-time input handler, document:

- Which parameter is affected.
- What input triggers the behaviour (bad type, out-of-range value, specific value pattern).
- What the result is (coerced value, rejected value, side effect on other parameters).

These typically do not raise exceptions — they silently fix the value. Tests should verify the
transformation happened (the parameter holds the normalised value, not the original).

**Testing limitation:** All design-time parameter behaviour — coercion, parameter surface mutations
(§2), type narrowing, and trait updates — fires when `SetParameterValueRequest` is called, not
during workflow execution. A saved workflow captures the *result* of this work (the final parameter
state), not the *trigger*. This means design-time behaviour cannot be re-tested by re-running a
saved workflow; it can only be confirmed during the inspect phase or via pytest tests that create a
fresh node and set values.

#### 7d. Runtime errors in `process()`

Look for `raise` statements (or calls to methods that raise) inside `process()` and any methods it
calls. For each:

- What condition triggers the error.
- What exception type is raised.
- Whether the raise is wrapped in `_handle_failure_exception()` (SuccessFailureNode graceful path)
  or bare (crashes the flow unconditionally).

Pay special attention to nodes with `type="any"` or `input_types=["any"]` parameters — these accept
anything at connection time but typically validate at runtime, making them the most likely source
of interesting error paths.

#### 7e. ParameterMessage and BadgeData indicators

Look for:

- `ParameterMessage(variant="error", ...)` or `ParameterMessage(variant="warning", ...)` added to
  the node.
- `set_badge(variant="error"|"warning", ...)` calls.

These are visual indicators that don't affect execution flow. Document when they are shown and what
triggers them, but note that they are informational, not flow-controlling.

### 8. Control parameters

Control parameters (`ControlParameterInput`, `ControlParameterOutput`) govern execution flow. They
are structurally distinct from data parameters — they have type `"control"`, and are rendered at
the top or bottom of the node.

Include control parameters in the default configuration table. Use direction `control-in` or
`control-out` rather than `input`/`output` to distinguish them from data parameters. Note display
names (e.g. "Succeeded", "Failed") since these are what the UI shows.

Control parameters inherited from base classes should be listed in the base class table (see above)
and included in every configuration table.

______________________________________________________________________

## Output Format

Save the survey document to `workspace/inspections/<NodeType>.survey.md` (relative to the project
root, **not** relative to the skill directory).

Structure:

```markdown
# <NodeType> — <Library Name>

**Source:** `<relative file path from library subdirectory>`
**Base class:** `<ClassName>`
**Category:** `<category from library manifest>`

## Static parameters

Parameters present in all configurations.

| Name | Direction | Type | Input Types | Default | Constraints |
|------|-----------|------|-------------|---------|-------------|
| ...  | ...       | ...  | ...         | ...     | ...         |

## Configuration: default

The parameter surface when the node is first created, before any value changes or connections.
Lists all visible parameters including those inherited from the base class.

| Name | Direction | Type | Input Types | Default | Constraints |
|------|-----------|------|-------------|---------|-------------|
| ...  | ...       | ...  | ...         | ...     | ...         |

## Configuration: <param_name> = "<value>"

Changes from default: <brief description of what changed>

| Name | Direction | Type | Input Types | Default | Constraints |
|------|-----------|------|-------------|---------|-------------|
| ...  | ...       | ...  | ...         | ...     | ...         |

## Configuration: <param_name> ← <source_type> (connected)

Changes from default: <brief description of what changed>

| Name | Direction | Type | Input Types | Default | Constraints |
|------|-----------|------|-------------|---------|-------------|
| ...  | ...       | ...  | ...         | ...     | ...         |

## Configuration: AddParameterButton

User can add parameters via the "+" button. Each added parameter has:
<description of the template — name pattern, type, modes, etc.>

## Error Behavior

### Base class: <SuccessFailureNode | ControlNode | DataNode | BaseNode>
<If SuccessFailureNode: note the Succeeded/Failed control outputs and whether
_create_status_parameters() is called.>

### Pre-execution validation (validate_before_node_run)

| Condition | Parameter | Expected Error |
|-----------|-----------|----------------|
| ...       | ...       | ...            |

<If validate_before_node_run is not overridden, write "None." instead of the table.>

### Runtime errors (process)

| Condition | Error Type | Graceful | Notes |
|-----------|-----------|----------|-------|
| ...       | ...       | ...      | ...   |

<Graceful = "Yes" if the raise is wrapped in _handle_failure_exception (SuccessFailureNode only),
"No" if bare. If no runtime errors, write "None.">

### Design-time input handling (before_value_set / set_parameter_value)

| Parameter | Input | Result | Notes |
|-----------|-------|--------|-------|
| ...       | ...   | ...    | ...   |

<If none, write "None.">

### Visual indicators (ParameterMessage / BadgeData)

<Describe any error/warning messages or badges, what triggers them, and when they appear.
If none, write "None.">

## Notes

<Any caveats, edge cases, or observations about the node's behaviour that the inspect skill
should be aware of. Flag uncertainty with "?" annotations.>
```

### Column definitions

| Column        | Description                                                                                                              |
| ------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `Name`        | Parameter name.                                                                                                          |
| `Direction`   | One of: `control-in`, `control-out`, `input`, `output`, `input/output`, `property`. Derived from type and allowed_modes. |
| `Type`        | Parameter type (e.g. `str`, `int`, `ImageUrlArtifact`).                                                                  |
| `Input Types` | Semicolon-separated types accepted as input connections. Empty if output-only.                                           |
| `Default`     | Default value, or empty if none.                                                                                         |
| `Constraints` | Dropdown choices, slider range, or other constraints. Empty if unconstrained.                                            |

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

### Annotating hidden parameters

Parameters can be hidden in two ways:

- `hide=True` kwarg in the `Parameter(...)` constructor.
- `parameter.ui_options["hide"] = True` set after construction (e.g. `DataNode` hides its control
  parameters this way).

Both make the parameter invisible by default. Include hidden parameters in the default
configuration table with `(hidden)` after the name.

______________________________________________________________________

## Tips

- **Skip the "Static parameters" section for non-dynamic nodes.** If the node has no value-driven,
  connection-driven, or UI-message-driven configurations, the "Static parameters" and
  "Configuration: default" tables are identical. In this case, omit the "Static parameters" section
  and use "Configuration: default" as the single parameter table.

- **Focus on parameter surface changes.** The goal is to enumerate configurations where the set of
  parameters or their types/modes change. Internal logic (how values are computed) is out of scope.

- **Visibility patterns.** Some nodes pre-create all parameters and toggle visibility rather than
  adding/removing dynamically. For example, `MathExpression` creates 26 hidden variable inputs
  (a–z) and shows/hides them based on a slider value. In these cases, describe the pattern (e.g.
  "`num_variables` slider [1–26] controls visibility of letter-named inputs a through z") rather
  than listing 26 separate configurations.

- **Connection configurations are typed.** Connection-driven changes depend only on the connected
  parameter's static type metadata. Name the configuration by the connecting type, not the callback
  method. E.g. `model ← PromptModelConfig (connected)`.

- **Inheritance matters.** Many parameters come from base classes. Always check the parent class
  and include inherited parameters in the default configuration table.

- **Flag uncertainty.** The survey is a static analysis aid. Runtime behaviour may differ from what
  the source code suggests. Append `?` to any value you are unsure about, and note the uncertainty
  in the Notes section. The inspect skill will confirm against the live engine.

- **One configuration per heading.** Each configuration that produces a distinct parameter surface
  gets its own `## Configuration:` heading. If multiple values produce the same surface, group them
  under one heading and list all values (e.g.
  `## Configuration: model = "gpt-4o" | "gpt-4o-mini"`).

- **Keep tables complete.** Each configuration table should list **all** visible parameters for
  that configuration, not just the ones that changed. This makes each table self-contained for
  downstream consumers.

- **Trace error paths through helper methods.** `process()` often delegates to private methods like
  `_get_value()` or `_validate_inputs()`. Follow all call chains to find `raise` statements — they
  may be several levels deep. For each, note whether the caller wraps it in
  `_handle_failure_exception()`.

- **Design-time input handling ≠ runtime errors.** If `before_value_set()` or
  `set_parameter_value()` silently converts or normalises a value, that is design-time input
  handling (§7c), not a runtime error (§7d). Both are important but they produce different test
  cases: design-time handling tests verify the normalised value; runtime error tests verify the
  exception or graceful failure path. Design-time behaviour also cannot be re-tested by re-running
  a saved workflow — it must be confirmed during inspection or via pytest.
