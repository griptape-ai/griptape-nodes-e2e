# ToFloat

**Library:** Griptape Nodes Library **Class:** `ToFloat` **Base class:** `DataNode` **Category:**
convert **Display name:** To Float

## Description

Converts any incoming value to a float. For strings, extracts the first number found using regex.
For dicts, finds the first non-zero numeric value. Useful as an adapter between a node whose output
is not natively `float` and `AssertNumbers`.

## Parameters

| Name     | Type    | Modes            | Default | Description                            |
| -------- | ------- | ---------------- | ------- | -------------------------------------- |
| `from`   | `any`   | INPUT            | `""`    | The data to convert. Accepts any type. |
| `output` | `float` | OUTPUT, PROPERTY | `""`    | The converted data as a float.         |

## Conversion Rules

- `int` / `float` → direct cast
- `str` → regex extracts first number (e.g. `"score: 3.5"` → `3.5`)
- `dict` → searches values for first non-zero number
- `None` / unconvertible → `0.0`

## Use When

- The node under test outputs a string containing a number (e.g. from LLM output) and you need to
  assert numerically using `AssertNumbers`.
- Wire `NodeUnderTest.<output>` → `ToFloat.from`, then `ToFloat.output` → `AssertNumbers.actual`.

## Example Wiring

```
AgentNode.output     →  ToFloat.from
ToFloat.output       →  AssertNumbers.actual
(set AssertNumbers.expected = 0.0 as PROPERTY)
(set AssertNumbers.operator = ">" as PROPERTY)
```
