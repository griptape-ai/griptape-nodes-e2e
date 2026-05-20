# LoggerNode

**Library:** Griptape Nodes Library **Class:** `LoggerNode` **Base class:** `DataNode`
**Category:** misc **Display name:** Logger

## Description

Logs messages to the console with configurable log levels and formatting. Has a `passthrough`
parameter of `type="any"` that accepts any connection — useful as a generic downstream sink or
debug probe. The node's hidden control parameters (`exec_in`, `exec_out`) are inherited from
`DataNode`.

## Parameters

| Name                | Type   | Modes           | Default  | Description                                                                         |
| ------------------- | ------ | --------------- | -------- | ----------------------------------------------------------------------------------- |
| `log_level`         | `str`  | INPUT, PROPERTY | `"INFO"` | Log level. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.                |
| `log_message`       | `str`  | INPUT, PROPERTY | `""`     | The message to log. Multiline.                                                      |
| `include_node_name` | `bool` | INPUT, PROPERTY | `True`   | Whether to include the node name prefix in log output.                              |
| `output`            | `str`  | OUTPUT          | `""`     | The formatted log message (markdown code block with level and aligned text).        |
| `passthrough`       | `any`  | INPUT, PROPERTY | —        | Optional any-type input. Connect to force evaluation order without data dependency. |

## Error Behaviour

**Base class:** `DataNode` — unhandled exceptions in `process()` crash the flow. No
`SuccessFailureNode` failure path.

No `validate_before_node_run()` override. An empty `log_message` is allowed (the node logs a blank
line).

## Use When

- You need a **generic downstream sink** that accepts any output type — connect the node under
  test's output to `passthrough` to force evaluation without type constraints.
- You want to **inspect a value during debugging** — the `output` parameter shows the formatted log
  message on the node, and the message is also written to the console logger.

## Example Wiring

```
NodeUnderTest.some_output  →  LoggerNode.passthrough
(set LoggerNode.log_message = "checkpoint reached" as PROPERTY)
```
