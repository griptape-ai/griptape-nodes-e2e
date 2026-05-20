# KeyValuePair

**Library:** Griptape Nodes Library **Class:** `KeyValuePair` **Base class:** `ControlNode`
**Category:** dict **Display name:** Key Value Pair

## Description

Creates a single-entry dictionary from a key and a value. Both `key` and `value` are INPUT +
PROPERTY, so they can be set directly in the property panel or connected from upstream nodes. The
`dictionary` output updates live as values change (via `after_value_set`), before execution.

This is the simplest way to produce a `dict` in a test workflow — no list nodes required.

## Parameters

| Name         | Type   | Modes           | Default           | Description                                                         |
| ------------ | ------ | --------------- | ----------------- | ------------------------------------------------------------------- |
| `key`        | `str`  | INPUT, PROPERTY | `""`              | Key for the dictionary entry.                                       |
| `value`      | `str`  | INPUT, PROPERTY | `None`            | Value for the dictionary entry. Accepts `any` type via connections. |
| `dictionary` | `dict` | OUTPUT          | `{"key":"value"}` | The constructed single-entry dictionary.                            |

## Important: single-entry only

The output is always a single-entry dict: `{<key>: <value>}`. For multi-key dicts, either:

- Use multiple `KeyValuePair` nodes and merge them via `MergeKeyValuePairs`, or
- Use `Dictionary` with `keys` and `values` lists.

## Use When

- You need a simple `dict` input with one key-value pair for the node under test.
- Preferred over `Dictionary` for single-entry dicts because both `key` and `value` are directly
  editable as properties — no list construction needed.
- Wire `KeyValuePair.dictionary` → `NodeUnderTest.<dict_input>`.

## Example Wiring

```
(set KeyValuePair.key = "color" as PROPERTY)
(set KeyValuePair.value = "blue" as PROPERTY)
KeyValuePair.dictionary  →  NodeUnderTest.input_dict
```
