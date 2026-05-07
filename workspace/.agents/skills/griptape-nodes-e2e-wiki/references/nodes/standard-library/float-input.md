# FloatInput

**Library:** Griptape Nodes Library **Class:** `FloatInput` **Base class:** `DataNode`
**Category:** number **Display name:** Float Input

## Description

Provides a float value. The simplest way to furnish a `float` input to a node under test.

## Parameters

| Name    | Type    | Modes            | Default | Description    |
| ------- | ------- | ---------------- | ------- | -------------- |
| `float` | `float` | OUTPUT, PROPERTY | `0.0`   | A float value. |

## Use When

- You need to provide a literal `float` value to the node under test.
- Wire `FloatInput.float` → `NodeUnderTest.<float_input>`.

## Example Wiring

```
(set FloatInput.float = 3.14 as PROPERTY)
FloatInput.float  →  NodeUnderTest.temperature
```
