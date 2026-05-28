# Calculator

**Library:** Griptape Nodes Library **Class:** `Calculator` **Base class:** `DataNode` (via
`BaseTool`) **Category:** tools **Display name:** Calculator Tool

## Description

Provides a `Tool` that performs mathematical calculations. The simplest tool node available — no
external dependencies, no API keys, no file I/O. Ideal as a test input when the node under test
accepts a `Tool` or `list[Tool]` parameter (e.g. `Agent.tools`).

## Parameters

| Name         | Type   | Modes           | Default | Description                                                                     |
| ------------ | ------ | --------------- | ------- | ------------------------------------------------------------------------------- |
| `tool`       | `Tool` | OUTPUT          | `null`  | The created `CalculatorTool` instance. Connect to a `Tool`-accepting parameter. |
| `off_prompt` | `bool` | INPUT, PROPERTY | `false` | Whether the tool operates off-prompt. Hidden by default on this node.           |

## Use When

- You need to provide a `Tool` value to a node under test (e.g. `Agent.tools`).
- Prefer this over other tool nodes (`WebSearch`, `FileManager`) because it has no external
  dependencies — it works locally with no API keys or file paths.
- For `ParameterList`-style inputs like `Agent.tools`, use `AddParameterToNodeRequest` to create a
  slot on the target, then connect `Calculator.tool` to that slot.

## Example Wiring

```
Calculator.tool  →  Agent.tools (via AddParameterToNodeRequest slot)
```

To wire to an expander-style `ParameterList` input:

1. `AddParameterToNodeRequest(node_name="Agent_1", parent_container_name="tools")` → returns slot
   name (e.g. `tools_ParameterListUniqueParamID_abc123`)
2. `CreateConnectionRequest(source="Calculator_1", source_param="tool", target="Agent_1", target_param="tools_ParameterListUniqueParamID_abc123")`
