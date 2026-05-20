# CancelWorkflow

**Library:** Griptape Nodes Library **Class:** `CancelWorkflow` **Base class:** `BaseNode`
**Category:** execution_flow **Display name:** Cancel Workflow

## Description

Unconditionally crashes the flow by raising a `RuntimeError` with a configurable message. Use as a
sentinel on control paths that should never be reached — if the flow reaches this node, something
went wrong.

## Parameters

| Name                  | Type      | Modes           | Default                                                  | Description                             |
| --------------------- | --------- | --------------- | -------------------------------------------------------- | --------------------------------------- |
| `exec_in`             | `control` | INPUT           | —                                                        | Control flow input.                     |
| `cancellation_reason` | `str`     | INPUT, PROPERTY | `"Cancelled running workflow via Cancel Workflow Node."` | Error message passed to `RuntimeError`. |

## Error Behaviour

**Always crashes.** The node's `process()` raises `RuntimeError(cancellation_reason)`
unconditionally. There is no success path — this node exists solely to abort the flow.

## Use When

- You need a **sentinel for unexpected control paths** in a test workflow. For example, when
  testing `IfElse` with `evaluate=false`, the `Then` branch should never fire. Connect `Then` to a
  `CancelWorkflow` node so the flow crashes with a clear message if the wrong branch is taken.
- You need an **explicit failure point** that produces a descriptive error message in CI output.

## Example Wiring

As an unexpected-branch sentinel:

```
IfElse.Then  →  CancelWorkflow.exec_in
(set CancelWorkflow.cancellation_reason = "Then branch should not fire when evaluate=false")
```
