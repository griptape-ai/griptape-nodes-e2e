# IfElse

**Library:** Griptape Nodes Library **Class:** `IfElse` **Base class:** `BaseNode` **Category:**
execution_flow **Display name:** IfElse

## Description

Branches a workflow based on whether a value is truthy or falsy. Evaluates the `evaluate` parameter
and routes execution through either `Then` or `Else` control outputs. Optionally passes through
data via `output_if_true` / `output_if_false` → `output`, selecting the value matching the chosen
branch.

The data inputs (`output_if_true`, `output_if_false`) and the `output` parameter participate in a
type-negotiation system: when `output` is connected to a downstream node, the accepted input types
narrow to what that downstream node accepts; when an upstream node connects to one of the data
inputs, all parameters lock to that specific type.

## Parameters

### Control parameters

| Name      | Type      | Modes  | Default | Description                                  |
| --------- | --------- | ------ | ------- | -------------------------------------------- |
| `exec_in` | `control` | INPUT  | —       | Control flow input.                          |
| `Then`    | `control` | OUTPUT | —       | Control flow taken when `evaluate` is true.  |
| `Else`    | `control` | OUTPUT | —       | Control flow taken when `evaluate` is false. |

### Data parameters

| Name              | Type   | Modes           | Default | Description                                                 |
| ----------------- | ------ | --------------- | ------- | ----------------------------------------------------------- |
| `evaluate`        | `bool` | INPUT, PROPERTY | `False` | The value to evaluate. Accepts `bool`, `int`, `str`.        |
| `output_if_true`  | `any`  | INPUT           | —       | Data to pass through when condition is true. (Collapsible)  |
| `output_if_false` | `any`  | INPUT           | —       | Data to pass through when condition is false. (Collapsible) |
| `output`          | `ALL`  | OUTPUT          | —       | The selected data value based on evaluation. (Collapsible)  |

### Truthiness rules for `evaluate`

| Input type | Falsy values                                                                                     | Truthy          |
| ---------- | ------------------------------------------------------------------------------------------------ | --------------- |
| `bool`     | `False`                                                                                          | `True`          |
| `int`      | `0`                                                                                              | any non-zero    |
| `str`      | `""`, `"false"`, `"f"`, `"no"`, `"n"`, `"0"`, `"0.0"`, `"none"`, `"null"`, `"off"`, `"disabled"` | everything else |

Other types raise `TypeError`.

## Error Behaviour

**Base class:** `BaseNode` — unhandled exceptions in `process()` crash the flow. Not a
`SuccessFailureNode`.

**Runtime error:** If `evaluate` receives a value that is not `str`, `int`, or `bool`, the node
raises `TypeError("Unsupported type for evaluate: <type>")`, crashing the flow unconditionally.

No `validate_before_node_run()` override. No input coercion.

## Use When

- You need to **branch a test workflow** based on a condition — e.g. test one path for valid input
  and another for invalid input.
- You need a **data selector** that passes through one of two values based on a boolean.
- You need a node with **any-type inputs** as a downstream connection target when testing nodes
  that output dynamic types.

## Example Wiring

As a control flow branch:

```
(set IfElse.evaluate = True as PROPERTY)
NodeBefore.exec_out  →  IfElse.exec_in
IfElse.Then          →  HappyPathNode.exec_in
IfElse.Else          →  ErrorPathNode.exec_in
```

As a data pass-through:

```
TextInput.text       →  IfElse.output_if_true
OtherInput.text      →  IfElse.output_if_false
BoolInput.value      →  IfElse.evaluate
IfElse.output        →  AssertEqual.actual
```
