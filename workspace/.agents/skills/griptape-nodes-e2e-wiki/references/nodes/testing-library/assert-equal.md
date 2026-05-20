# AssertEqual

**Library:** Griptape Nodes Testing Library **Class:** `AssertEqual` **Base class:**
`SuccessFailureNode` **Category:** assert **Display name:** Assert Equal

## Description

Asserts that two values are equal using Python's `==` operator. Accepts any type for both `actual`
and `expected`, so it can validate string, numeric, boolean, list, and dict outputs without needing
a type-specific assertion node.

## Parameters

| Name       | Type  | Modes           | Default | Description                                                                                    |
| ---------- | ----- | --------------- | ------- | ---------------------------------------------------------------------------------------------- |
| `actual`   | `any` | INPUT, PROPERTY | `None`  | The actual value produced by the node under test.                                              |
| `expected` | `any` | INPUT, PROPERTY | `None`  | The expected value to compare against. Set as a PROPERTY when the expected value is a literal. |
| `message`  | `str` | INPUT, PROPERTY | `""`    | Optional custom message prepended to the failure detail.                                       |

## Failure Behaviour

If `actual != expected`, the node calls `_handle_failure_exception(AssertionError(...))`. This
raises an `AssertionError` which causes the flow to fail. The `result_details` output parameter
contains the full failure message: `"<message>: Assertion failed: <actual!r> != <expected!r>"`.

## Important: `type="any"` Has No UI Widget

Both `actual` and `expected` have `type="any"`, which means the engine does not render a value
widget for them. You cannot set or inspect their values visually in the editor. To make expected
values visible when reviewing a saved workflow, **always connect `expected` to an upstream input
provider node** (e.g. `TextInput`, `IntegerInput`, `FloatInput`, `BoolInput`) rather than setting
it as a PROPERTY via `SetParameterValueRequest`.

The same applies to `actual` — it should always be connected to the node under test's output.

## Use When

- The node under test produces a value of any type and you want to assert exact equality.
- You want a single general-purpose assertion rather than a type-specific one.

Prefer `AssertStrings` when you need flexible string operators (contains, regex). Prefer
`AssertNumbers` when you need relational numeric operators (`<`, `>=`, etc.).

## Example Wiring

```
NodeUnderTest.output     →  AssertEqual.actual
TextInput_Expected.text  →  AssertEqual.expected
(set TextInput_Expected.value = "hello world" as PROPERTY)
```
