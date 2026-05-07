# GetFromList

**Library:** Griptape Nodes Library **Class:** `GetFromList` **Base class:** `ControlNode`
**Category:** lists **Display name:** Get From List

## Description

Extracts a single item from a list by index or position (start/end). Outputs the item with a
wildcard type compatible with any downstream input. Useful for pulling a specific element from a
list output so it can be individually asserted.

## Parameters

| Name       | Type   | Modes           | Default   | Description                                                     |
| ---------- | ------ | --------------- | --------- | --------------------------------------------------------------- |
| `items`    | `list` | INPUT           | —         | List of items to get an item from.                              |
| `position` | `str`  | PROPERTY        | `"index"` | How to select: `"index"`, `"start"`, or `"end"`. Options trait. |
| `index`    | `int`  | INPUT, PROPERTY | `0`       | Index to get the item from (when position is `"index"`).        |
| `item`     | `any`  | OUTPUT          | —         | The item at the specified position.                             |

## Use When

- The node under test outputs a `list` and you need to assert on a specific element.
- Use `position = "start"` for the first item, `"end"` for the last, or `"index"` with a specific
  index value.
- Wire `GetFromList.item` → an assertion node or a type converter if further transformation is
  needed.

## Example Wiring

```
NodeUnderTest.items    →  GetFromList.items
(set GetFromList.position = "start" as PROPERTY)
GetFromList.item       →  AssertEqual.actual
(set AssertEqual.expected = "first_value" as PROPERTY)
```
