# GetListLength

**Library:** Griptape Nodes Library **Class:** `GetListLength` **Base class:** `ControlNode`
**Category:** lists **Display name:** Get List Length

## Description

Takes a list and outputs its length as an integer. Useful for asserting that a node produced the
expected number of items.

## Parameters

| Name     | Type   | Modes  | Default | Description                                                         |
| -------- | ------ | ------ | ------- | ------------------------------------------------------------------- |
| `items`  | `list` | INPUT  | —       | List of items to measure.                                           |
| `length` | `int`  | OUTPUT | —       | The length of the input list. Returns `0` if list is empty or None. |

## Use When

- The node under test outputs a `list` and you want to assert on its length rather than its
  contents.
- Wire `NodeUnderTest.<list_output>` → `GetListLength.items`, then `GetListLength.length` →
  `AssertNumbers.actual`.

## Example Wiring

```
NodeUnderTest.results  →  GetListLength.items
GetListLength.length   →  AssertNumbers.actual
(set AssertNumbers.expected = 3 as PROPERTY)
(set AssertNumbers.operator = "==" as PROPERTY)
```
