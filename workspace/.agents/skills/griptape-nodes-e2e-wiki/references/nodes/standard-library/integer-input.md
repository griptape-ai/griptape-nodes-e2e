# IntegerInput

**Library:** Griptape Nodes Library **Class:** `IntegerInput` **Base class:** `DataNode`
**Category:** number **Display name:** Integer Input

## Description

Provides an integer value. The simplest way to furnish an `int` input to a node under test.

## Parameters

| Name      | Type  | Modes            | Default | Description       |
| --------- | ----- | ---------------- | ------- | ----------------- |
| `integer` | `int` | OUTPUT, PROPERTY | `0`     | An integer value. |

## Use When

- You need to provide a literal `int` value to the node under test.
- Wire `IntegerInput.integer` → `NodeUnderTest.<int_input>`.

## Example Wiring

```
(set IntegerInput.integer = 42 as PROPERTY)
IntegerInput.integer  →  NodeUnderTest.max_items
```
