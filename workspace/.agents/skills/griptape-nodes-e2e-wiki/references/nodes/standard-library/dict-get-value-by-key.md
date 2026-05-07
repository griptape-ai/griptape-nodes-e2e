# DictGetValueByKey

**Library:** Griptape Nodes Library **Class:** `DictGetValueByKey` **Base class:** `ControlNode`
**Category:** dict **Display name:** Get Dictionary Value by Key

## Description

Extracts a value from a dictionary by key. Optionally returns a default value if the key is not
found (or raises an exception if configured to do so). Useful for pulling a specific field from a
dict output so it can be individually asserted.

## Parameters

| Name                          | Type   | Modes           | Default | Description                                                                           |
| ----------------------------- | ------ | --------------- | ------- | ------------------------------------------------------------------------------------- |
| `dict`                        | `dict` | INPUT, PROPERTY | `{}`    | Dictionary to get value from.                                                         |
| `key`                         | `str`  | INPUT, PROPERTY | `""`    | Key to lookup in the dictionary.                                                      |
| `supply_default_if_not_found` | `bool` | INPUT, PROPERTY | `True`  | If True, return default value when key not found. If False, raise exception.          |
| `default_value_if_not_found`  | `any`  | INPUT, PROPERTY | —       | Default value returned when key is missing and `supply_default_if_not_found` is True. |
| `value`                       | `any`  | OUTPUT          | —       | The value found at the specified key (or the default).                                |

## Use When

- The node under test outputs a `dict` and you want to assert on a specific key's value.
- Wire `NodeUnderTest.<dict_output>` → `DictGetValueByKey.dict`, set `key` as PROPERTY, then wire
  `DictGetValueByKey.value` → an assertion node (or a type converter first).

## Example Wiring

```
NodeUnderTest.metadata     →  DictGetValueByKey.dict
(set DictGetValueByKey.key = "status" as PROPERTY)
DictGetValueByKey.value    →  AssertEqual.actual
(set AssertEqual.expected = "success" as PROPERTY)
```
