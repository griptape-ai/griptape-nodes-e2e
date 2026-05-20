# JsonInput

**Library:** Griptape Nodes Library **Class:** `JsonInput` **Base class:** `DataNode` **Category:**
json **Display name:** JSON Input

## Description

Provides a JSON value as a property. The `json` parameter is PROPERTY + OUTPUT (not INPUT), so it
cannot receive a connection — set its value directly as a JSON string in the property panel. The
node coerces string values via `repair_json()` with a fallback to `json.loads()`; dict values pass
through as-is.

## Parameters

| Name   | Type   | Modes            | Default | Description                                                                                                |
| ------ | ------ | ---------------- | ------- | ---------------------------------------------------------------------------------------------------------- |
| `json` | `json` | PROPERTY, OUTPUT | `"{}"`  | JSON data. Accepts `json`, `str`, or `dict` as input_types but only via PROPERTY (no inbound connections). |

## Use When

- You need to provide a `json` or `dict` input to the node under test via a literal value.
- Useful when the node under test accepts `json` or `dict` input_types and you want to set the
  value directly rather than constructing it from `Dictionary` + list nodes.
- Wire `JsonInput.json` → `NodeUnderTest.<json_input>`.

## Example Wiring

```
(set JsonInput.json = '{"name": "test", "value": 42}' as PROPERTY)
JsonInput.json  →  NodeUnderTest.config
```
