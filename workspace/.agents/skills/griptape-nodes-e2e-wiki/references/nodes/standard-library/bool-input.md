# BoolInput

**Library:** Griptape Nodes Library **Class:** `BoolInput` **Base class:** `DataNode` **Category:**
number **Display name:** Bool Input

## Description

Provides a boolean value. The simplest way to furnish a `bool` input to a node under test.

## Parameters

| Name   | Type   | Modes            | Default | Description      |
| ------ | ------ | ---------------- | ------- | ---------------- |
| `bool` | `bool` | OUTPUT, PROPERTY | `False` | A boolean value. |

## Use When

- You need to provide a literal `bool` value (`True` or `False`) to the node under test.
- Wire `BoolInput.bool` → `NodeUnderTest.<bool_input>`.

## Example Wiring

```
(set BoolInput.bool = True as PROPERTY)
BoolInput.bool  →  NodeUnderTest.enabled
```
