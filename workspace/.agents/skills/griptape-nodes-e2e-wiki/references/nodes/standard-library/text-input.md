# TextInput

**Library:** Griptape Nodes Library **Class:** `TextInput` **Base class:** `DataNode` **Category:**
text **Display name:** Text Input

## Description

Provides a string value. The simplest way to furnish a `str` input to a node under test. Set the
`text` property to a literal value; it passes through unchanged on execution.

## Parameters

| Name   | Type  | Modes            | Default | Description                                          |
| ------ | ----- | ---------------- | ------- | ---------------------------------------------------- |
| `text` | `str` | OUTPUT, PROPERTY | `""`    | The text content to pass to another node. Multiline. |

## Use When

- You need to provide a literal `str` value to any input parameter on the node under test.
- Wire `TextInput.text` → `NodeUnderTest.<str_input>`.
- Set the value as a PROPERTY before execution.

## Example Wiring

```
(set TextInput.text = "hello world" as PROPERTY)
TextInput.text  →  NodeUnderTest.prompt
```
