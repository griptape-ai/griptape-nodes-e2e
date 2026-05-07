# ToText

**Library:** Griptape Nodes Library **Class:** `ToText` **Base class:** `DataNode` **Category:**
convert **Display name:** To Text

## Description

Converts any incoming value to a string using Python's `str()`. Useful as an adapter between a node
whose output type is not `str` and an assertion node that requires `str` input (e.g.
`AssertStrings`).

## Parameters

| Name     | Type  | Modes            | Default | Description                            |
| -------- | ----- | ---------------- | ------- | -------------------------------------- |
| `from`   | `any` | INPUT            | `""`    | The data to convert. Accepts any type. |
| `output` | `str` | OUTPUT, PROPERTY | `""`    | The converted data as text. Multiline. |

## Use When

- The node under test outputs a non-string type (dict, list, int, etc.) and you want to assert on
  its string representation using `AssertStrings`.
- Wire `NodeUnderTest.<output>` → `ToText.from`, then `ToText.output` → `AssertStrings.actual`.

## Example Wiring

```
NodeUnderTest.count  →  ToText.from
ToText.output        →  AssertStrings.actual
(set AssertStrings.expected = "42" as PROPERTY)
(set AssertStrings.operator = "==" as PROPERTY)
```
