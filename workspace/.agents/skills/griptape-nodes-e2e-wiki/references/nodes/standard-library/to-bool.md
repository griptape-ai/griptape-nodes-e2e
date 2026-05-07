# ToBool

**Library:** Griptape Nodes Library **Class:** `ToBool` **Base class:** `DataNode` **Category:**
convert **Display name:** To Bool

## Description

Converts any incoming value to a boolean. Handles common string truthy/falsy patterns (`"true"`,
`"yes"`, `"1"` → `True`; `"false"`, `"no"`, `"0"` → `False`). Numbers: non-zero → `True`.
Collections: non-empty → `True`.

## Parameters

| Name     | Type   | Modes            | Default | Description                            |
| -------- | ------ | ---------------- | ------- | -------------------------------------- |
| `from`   | `any`  | INPUT            | `""`    | The data to convert. Accepts any type. |
| `output` | `bool` | OUTPUT, PROPERTY | `""`    | The converted data as a bool.          |

## Conversion Rules

- `bool` → pass-through
- `str` → `"true"/"yes"/"y"/"1"/"t"` (case-insensitive) → `True`; `"false"/"no"/"n"/"0"/"f"` →
  `False`; other non-empty → `True`
- `int` / `float` → `!= 0`
- `dict` / `list` / `tuple` / `set` → non-empty is `True`
- `None` → `False`

## Use When

- The node under test outputs a value you need as `bool` for `AssertTrue` or `AssertEqual`.
- Wire `NodeUnderTest.<output>` → `ToBool.from`, then `ToBool.output` → `AssertTrue.value` or
  `AssertEqual.actual`.

## Example Wiring

```
NodeUnderTest.result  →  ToBool.from
ToBool.output         →  AssertTrue.value
```
