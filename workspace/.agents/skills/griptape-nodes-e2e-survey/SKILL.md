---
name: griptape-nodes-e2e-survey
description: >-
  Analyse a Griptape Node's Python source code to enumerate all parameter configurations —
  value-driven, connection-driven, and UI-message-driven. Produces a survey document that
  guides the inspect skill's live exploration.
metadata:
  author: the-foundry-visionmongers
  version: '0.1'
---

# Surveying Griptape Nodes

## Purpose

Given a target node type and library name, read the node's Python source code and produce a
markdown document listing every **configuration axis** and the expected parameter surface for each.
This document feeds into the `griptape-nodes-e2e-inspect` skill, which confirms predictions against
a live engine.

A configuration axis is anything that changes the node's parameter surface at design time —
dropdown values, slider positions, boolean toggles, incoming connections, UI buttons, or batch
transitions. The survey captures all of these uniformly.

______________________________________________________________________

## Locating the Source Code

### Step 1: Get the library root directory

Ask the user for the **library root directory** — the directory that contains library
subdirectories. For example: `/home/user/workspace/GriptapeNodes/libraries/`.

If the user has already provided this path earlier in the conversation, do not ask again.

### Step 2: Find the matching library subdirectory

The user will specify the library name as it appears in the engine (e.g.
`Griptape Nodes Testing Library`). Find the matching subdirectory by reading the
`griptape_nodes_library.json` file in each subdirectory under the library root until you find the
one whose `"name"` field matches.

```bash
# Example: find all library manifests
find <library_root> -maxdepth 2 -name "griptape_nodes_library.json"
```

Read each manifest and compare the `"name"` field to the user's library name.

### Step 3: Find the node's file path

In the matching `griptape_nodes_library.json`, locate the entry in the `"nodes"` array whose
`"class_name"` matches the target node type. The `"file_path"` field gives the path to the Python
file, relative to the library subdirectory.

### Step 4: Read the node source

Read the Python file at the resolved path.

### Step 5: Follow the inheritance chain

If the node inherits from a base class:

- **Within the same library** — follow the import and read the parent class file.
- **From the engine** (`griptape_nodes.exe_types`) — read the engine's base class to identify
  inherited parameters and lifecycle hooks. Common base classes:
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

| Base class           | Inherited parameters                                                                                             |
| -------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `BaseNode`           | (none beyond engine internals)                                                                                   |
| `DataNode`           | `exec_in` (control-in, hidden), `exec_out` (control-out, hidden)                                                 |
| `SuccessFailureNode` | `exec_in` (control-in), `exec_out` (control-out, display "Succeeded"), `failure` (control-out, display "Failed") |

**`_create_status_parameters()` (opt-in):** Many `SuccessFailureNode` subclasses call this helper
in their `__init__` to add `was_successful` (output, bool) and `result_details` (output, str)
inside a collapsible "Status" `ParameterGroup`. Check whether the target node calls it — if so,
include these parameters in the survey. They are added to the node's element tree via a
`ParameterGroup`, not as top-level parameters.

### 7. Control parameters

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

Save the survey document to `inspections/<NodeType>.survey.md`.

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
