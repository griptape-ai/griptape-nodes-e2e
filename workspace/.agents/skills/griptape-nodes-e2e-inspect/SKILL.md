---
name: griptape-nodes-e2e-inspect
description: >-
  Enumerate all possible input and output parameter configurations of a Griptape Node by
  interacting with a live engine via MCP tools. Use when you need to discover a node's full
  parameter surface — including dynamic parameters that change when dropdown values are modified. 
  Produces a CSV table of valid input/output combinations as output.
compatibility: Requires an MCP connection to a running griptape-nodes engine.
metadata:
  author: the-foundry-visionmongers
  version: '0.2'
---

# Inspecting Griptape Nodes

## Purpose

Given a target node type (e.g. `AssertStrings` in `Griptape Nodes Testing Library`), produce a
complete table of its valid input and output parameters — including variants caused by dynamic
parameter mutations when dropdown values change.

The output is a CSV file saved to the workspace. Downstream agents or humans use this CSV to plan
test workflows or generate scripts; this skill is not concerned with how the CSV is consumed.

______________________________________________________________________

## Why Iterative Exploration Is Necessary

Many Griptape Nodes have **dynamic parameters**. Changing a dropdown or mode value triggers the
node to add, remove, or change parameters at runtime. A single snapshot of the default state misses
these variants.

There is **no single API call** that reveals all possible parameter states. You must create a live
node instance and iteratively modify its configurable parameters, observing what changes after each
modification.

______________________________________________________________________

## MCP Tools Used

All interaction is via MCP tool calls to the running engine. No SDK or Python code is required.

| MCP tool                      | Purpose                                                                                         |
| ----------------------------- | ----------------------------------------------------------------------------------------------- |
| `CreateNodeRequest`           | Create a node instance. Args: `node_type`, `specific_library_name`.                             |
| `ListParametersOnNodeRequest` | List current parameter names on a node. Args: `node_name`.                                      |
| `GetParameterDetailsRequest`  | Get full schema for one parameter. Args: `node_name`, `parameter_name`.                         |
| `SetParameterValueRequest`    | Change a parameter value (may trigger mutations). Args: `node_name`, `parameter_name`, `value`. |
| `DeleteNodeRequest`           | Delete the node when done. Args: `node_name`.                                                   |

______________________________________________________________________

## Exploration Workflow

### Step 1: Create the node

Call `CreateNodeRequest` with the target `node_type` and `specific_library_name`. Note the returned
`node_name` (e.g. `AssertStrings_1`).

### Step 2: Capture the default parameter state

1. Call `ListParametersOnNodeRequest` with the `node_name` to get all parameter names.
2. For each parameter name, call `GetParameterDetailsRequest` to get its full schema.
3. Record for each parameter: `name`, `type`, `input_types`, `output_type`, `allowed_modes`,
   `default_value`, `tooltip`, and whether it has an `options`/`choices` field (indicating a
   dropdown).

### Step 3: Identify dropdown parameters

A parameter is a dropdown if its details include a `choices` or `options` field listing the allowed
values. These are the parameters that can potentially trigger dynamic mutations when changed.

### Step 4: Iterate over each dropdown's options

For each dropdown parameter, for each of its possible values:

1. Call `SetParameterValueRequest` to set the dropdown to that value.
2. Call `ListParametersOnNodeRequest` again.
3. Compare the new parameter list to the previous one. Note any parameters that appeared or
   disappeared.
4. Call `GetParameterDetailsRequest` for any newly appeared parameters.

### Step 5: Recurse for newly discovered dropdowns

If changing a dropdown reveals new parameters that themselves have dropdown options, repeat step 4
for those as well.

### Step 6: Reset between explorations

After exploring one dropdown's options, set it back to its default value before exploring another
dropdown, so you get a clean baseline for comparison.

### Step 7: Delete the node

Call `DeleteNodeRequest` to clean up.

______________________________________________________________________

## Output Format

Produce a CSV file with one row per parameter per configuration variant. Save it to the workspace
at a path like `inspections/<NodeType>.csv`.

### CSV columns

```
configuration,name,direction,type,input_types,output_type,default_value,options,tooltip
```

| Column          | Description                                                                                                                               |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `configuration` | Which dropdown state produced this parameter. `default` for the initial state, or `param_name=value` for a variant (e.g. `model=gpt-4o`). |
| `name`          | Parameter name (e.g. `actual`, `operator`, `output`).                                                                                     |
| `direction`     | One of: `input`, `output`, `input/output`, `property`. Derived from `allowed_modes`.                                                      |
| `type`          | Parameter type (e.g. `str`, `float`, `ImageUrlArtifact`).                                                                                 |
| `input_types`   | Semicolon-separated list of types accepted as input connections (e.g. `str;json`). Empty if output-only.                                  |
| `output_type`   | Type produced when used as an output connection. Empty if input-only.                                                                     |
| `default_value` | Default value, or empty if none.                                                                                                          |
| `options`       | Semicolon-separated list of allowed values if dropdown, otherwise empty.                                                                  |
| `tooltip`       | Human-readable description.                                                                                                               |

### Deriving `direction` from `allowed_modes`

| `allowed_modes` contains            | `direction` value |
| ----------------------------------- | ----------------- |
| INPUT and OUTPUT                    | `input/output`    |
| INPUT only (no OUTPUT)              | `input`           |
| OUTPUT only (no INPUT)              | `output`          |
| PROPERTY only (no INPUT, no OUTPUT) | `property`        |
| INPUT and PROPERTY (no OUTPUT)      | `input`           |
| OUTPUT and PROPERTY (no INPUT)      | `output`          |

### Example CSV

```csv
configuration,name,direction,type,input_types,output_type,default_value,options,tooltip
default,actual,input,str,str,,"",,The actual string value.
default,expected,input,str,str,,"",,The expected string value or pattern.
default,operator,input,str,str,,==,==;!=;contains;not contains;starts_with;ends_with;regex,The comparison operator to apply.
default,message,input,str,str,,"",,Optional custom message on failure.
default,exec_output,output,str,,str,,,Execution flow output.
default,was_successful,output,bool,,bool,,,Whether the assertion passed.
default,result_details,output,str,,str,,,Details about the assertion result.
```

______________________________________________________________________

## Tips

- **Not all dropdowns cause mutations.** Some dropdowns (e.g. `operator` on assertion nodes) change
  behaviour without changing the parameter set. If the parameter list is unchanged after setting a
  dropdown, you can skip recording a separate variant — just note the dropdown's options in the
  `default` row.
- **Deduplicate configurations.** If two dropdown values produce identical parameter sets, keep
  only one row set and note both values (e.g. `model=gpt-4o;model=gpt-4o-mini`).
- **Ignore internal parameters.** Parameters marked `private: true` or with names starting with `_`
  are internal engine plumbing. Exclude them from the CSV.
- **Quote CSV values properly.** Tooltips and default values may contain commas. Use standard CSV
  quoting (double-quote fields containing commas, quotes, or newlines).
