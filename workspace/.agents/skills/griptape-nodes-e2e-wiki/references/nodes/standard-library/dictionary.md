# Dictionary

**Library:** Griptape Nodes Library **Class:** `Dictionary` **Base class:** `ControlNode`
**Category:** dict **Display name:** Create Dictionary

## Description

Creates a dictionary by zipping a list of keys with a list of values. Keys are coerced to strings.
If `values` is shorter than `keys`, missing values default to `None`. Mismatched lengths do not
raise errors.

## Parameters

| Name     | Type        | Modes           | Default | Description                                                                                                  |
| -------- | ----------- | --------------- | ------- | ------------------------------------------------------------------------------------------------------------ |
| `keys`   | `list[str]` | INPUT, PROPERTY | `[]`    | List of dictionary keys.                                                                                     |
| `values` | `list`      | INPUT, PROPERTY | `[]`    | List of dictionary values. Accepts `list[str]`, `list[int]`, `list[float]`, `list[bool]`, or generic `list`. |
| `dict`   | `dict`      | OUTPUT          | `{}`    | The constructed dictionary.                                                                                  |

## Important: `dict` is OUTPUT-only, `keys`/`values` require list connections in the UI

The `dict` parameter cannot be set directly — it has no PROPERTY or INPUT mode. The dictionary must
be constructed at runtime from `keys` and `values`.

In the UI, `keys` and `values` cannot be edited directly as properties — they require upstream list
node connections. Via `SetParameterValueRequest`, values can be set programmatically (e.g.
`keys=["color"]`, `values=["blue"]`) and will appear in the UI (read-only), but this is an MCP-only
capability.

**For single-entry dicts, prefer `KeyValuePair`** — it has directly editable `key` and `value`
properties and requires no list nodes. Use `Dictionary` when you need multi-key dicts.

## Use When

- You need to provide a multi-key `dict` input to the node under test.
- Pair with `CreateTextList` or `CreateList` to build the key and value lists.
- For single-entry dicts, use [KeyValuePair](key-value-pair.md) instead.

## Example Wiring

```
CreateTextList_keys.output    →  Dictionary.keys
CreateList_values.output      →  Dictionary.values
Dictionary.dict               →  NodeUnderTest.input_dict
```
