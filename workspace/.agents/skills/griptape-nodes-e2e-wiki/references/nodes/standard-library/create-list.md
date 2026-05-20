# CreateList

**Library:** Griptape Nodes Library **Class:** `CreateList` **Base class:** `ControlNode`
**Category:** lists **Display name:** Create List

## Description

Takes a set of items and produces a `list` output. Items are added via a `ParameterList`
(expandable multi-slot input). Supports flattening nested lists, removing duplicates, and removing
blank items. Updates output reactively on every item change.

## Parameters

| Name                | Type        | Modes                   | Default | Description                                       |
| ------------------- | ----------- | ----------------------- | ------- | ------------------------------------------------- |
| `items`             | `list[any]` | INPUT, PROPERTY         | `None`  | Expandable list of items (any type per slot).     |
| `flatten_list`      | `bool`      | INPUT, PROPERTY, OUTPUT | `False` | Flatten nested lists into a single list.          |
| `remove_duplicates` | `bool`      | INPUT, PROPERTY, OUTPUT | `False` | Remove duplicate items (does not preserve order). |
| `remove_blank`      | `bool`      | INPUT, PROPERTY, OUTPUT | `False` | Remove items that are blank strings.              |
| `output`            | `list`      | OUTPUT                  | —       | The constructed list.                             |

The three boolean options are in a collapsed `list_options` group.

## Use When

- You need to provide a `list` input to the node under test.
- Connect individual input provider nodes (e.g. `TextInput`, `FloatInput`) to the `items`
  ParameterList slots, then wire `CreateList.output` downstream.

## Example Wiring

```
TextInput_1.text  →  CreateList.items_0
TextInput_2.text  →  CreateList.items_1
CreateList.output →  NodeUnderTest.input_list
```
