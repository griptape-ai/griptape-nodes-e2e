# ToInteger

**Library:** Griptape Nodes Library **Class:** `ToInteger` **Base class:** `DataNode` **Category:**
convert **Display name:** To Integer

## Description

Converts any incoming value to an integer. For strings, extracts the first integer found using
regex. For dicts, finds the first non-zero integer value. Returns `0` on failure.

## Parameters

| Name     | Type  | Modes            | Default | Description                            |
| -------- | ----- | ---------------- | ------- | -------------------------------------- |
| `from`   | `any` | INPUT            | `""`    | The data to convert. Accepts any type. |
| `output` | `int` | OUTPUT, PROPERTY | `""`    | The converted data as an integer.      |

## Conversion Rules

- `int` / `float` → direct cast (float truncated)
- `str` → regex extracts first integer (e.g. `"page 7 of 10"` → `7`)
- `dict` → searches values for first non-zero integer
- `None` / unconvertible → `0`

## Use When

- The node under test outputs a value you need as `int` for `AssertNumbers` or further wiring.
- Wire `NodeUnderTest.<output>` → `ToInteger.from`, then `ToInteger.output` →
  `AssertNumbers.actual`.

## Example Wiring

```
GetListLength.length  →  ToInteger.from
ToInteger.output      →  AssertNumbers.actual
(set AssertNumbers.expected = 5 as PROPERTY)
(set AssertNumbers.operator = "==" as PROPERTY)
```
