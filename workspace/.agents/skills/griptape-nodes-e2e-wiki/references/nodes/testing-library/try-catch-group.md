# TryCatchGroup

**Library:** Griptape Nodes Testing Library **Class:** `TryCatchGroup` **Base class:**
`SubflowNodeGroup` **Category:** execution **Display name:** Try Catch Group

## Description

A group node that wraps child nodes and catches any exceptions they raise during execution. If all
child nodes succeed, the Succeeded control output fires. If any child node raises an exception
(propagated as a `RuntimeError` from the subflow), the Failed control output fires and the error
message is available on `error_message`.

This effectively converts any node(s) into a SuccessFailureNode-like construct, enabling test
workflows to assert on error conditions in nodes that raise exceptions rather than using the
SuccessFailureNode base class.

## Parameters

| Name            | Type      | Modes  | Default | Description                                                     |
| --------------- | --------- | ------ | ------- | --------------------------------------------------------------- |
| `exec_in`       | `control` | INPUT  | —       | Standard control flow input.                                    |
| `exec_out`      | `control` | OUTPUT | —       | Fires when all child nodes execute successfully ("Succeeded").  |
| `failure`       | `control` | OUTPUT | —       | Fires when a child node raises an exception ("Failed").         |
| `error_message` | `str`     | OUTPUT | `""`    | The error message from the caught exception (empty on success). |

## Behaviour

- **Success path:** `execute_subflow()` completes without error → `exec_out` fires, `error_message`
  is `""`.
- **Failure path:** `execute_subflow()` raises `RuntimeError` → `failure` fires, `error_message`
  contains the exception message string.
- **Before execution:** `get_next_control_output()` returns `None` and sets `stop_flow = True`
  (standard group node behaviour — the group must execute before routing).

## Important Limitations

- Only catches exceptions that escape the child node's `process()` method. Nodes that swallow their
  own exceptions internally (e.g. `ExecutePython`) will appear as successes to TryCatchGroup.
- Nodes based on `SuccessFailureNode` that have their `failure` output connected will route errors
  through their own failure path instead of raising — TryCatchGroup won't see them as failures. To
  test with TryCatchGroup, ensure the inner node's `failure` output has no connections so
  `_handle_failure_exception` re-raises.

## Use When

- Testing runtime error conditions in nodes that are NOT `SuccessFailureNode` subclasses.
- Testing that a node raises the expected exception under specific input conditions, while keeping
  the overall test workflow passing (not crashing).
- Pair with `AssertStrings` on `error_message` to verify the error text, and `CancelWorkflow` on
  the `exec_out` (Succeeded) path to flag unexpected success.

## Example Wiring

```
TryCatchGroup [contains: TargetNode with error-triggering inputs]
  TryCatchGroup.failure       →  AssertStrings.exec_in  (assert error_message)
  TryCatchGroup.error_message →  AssertStrings.actual
  TextInput.text ("expected error text")  →  AssertStrings.expected
  TryCatchGroup.exec_out      →  CancelWorkflow.exec_in (unexpected success = fail)
```
