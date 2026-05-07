# AssertTrue

**Library:** Griptape Nodes Testing Library **Class:** `AssertTrue` **Base class:**
`SuccessFailureNode` **Category:** assert **Display name:** Assert True

## Description

Asserts that a value is truthy using Python's `bool()` cast. Useful when the node under test
produces a boolean flag, a non-empty string, or a non-zero number and you only care that the value
is truthy rather than equal to a specific expected value.

## Parameters

| Name      | Type  | Modes           | Default | Description                                                            |
| --------- | ----- | --------------- | ------- | ---------------------------------------------------------------------- |
| `value`   | `any` | INPUT, PROPERTY | `None`  | The value to assert is truthy. Wire from the node under test's output. |
| `message` | `str` | INPUT, PROPERTY | `""`    | Optional custom message prepended to the failure detail.               |

## Failure Behaviour

If `bool(value)` is `False`, the node calls `_handle_failure_exception(AssertionError(...))`. The
flow fails. The `result_details` output contains:
`"<message>: Assertion failed: <value!r> is not truthy"`.

## Use When

- The node produces a `bool` output and you want to assert it is `True`.
- The node produces a non-empty string, non-zero number, or non-empty collection and you only need
  to assert that the result is present/non-empty rather than matching a specific value.
- Simpler than `AssertEqual` when you just need presence/success rather than exact equality.

## Example Wiring

```
SomeNode.success_flag  →  AssertTrue.value
(no expected value needed)
```
