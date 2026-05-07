# AssertNumbers

**Library:** Griptape Nodes Testing Library **Class:** `AssertNumbers` **Base class:**
`SuccessFailureNode` **Category:** assert **Display name:** Assert Numbers

## Description

Asserts a numeric comparison between `actual` and `expected` using a selectable relational
operator. Both inputs are typed `float`, but integer values work fine due to Python's numeric
coercion. Use this whenever a node produces a numeric output and you want to check exact equality
or a relational bound.

## Parameters

| Name       | Type    | Modes           | Default | Options                          | Description                                               |
| ---------- | ------- | --------------- | ------- | -------------------------------- | --------------------------------------------------------- |
| `actual`   | `float` | INPUT, PROPERTY | `0`     | —                                | The actual numeric value produced by the node under test. |
| `expected` | `float` | INPUT, PROPERTY | `0`     | —                                | The expected numeric value or bound.                      |
| `operator` | `str`   | INPUT, PROPERTY | `"=="`  | `==`, `!=`, `<`, `>`, `<=`, `>=` | The relational operator to apply.                         |
| `message`  | `str`   | INPUT, PROPERTY | `""`    | —                                | Optional custom message prepended to the failure detail.  |

### Operator semantics

| Operator | Passes when          |
| -------- | -------------------- |
| `==`     | `actual == expected` |
| `!=`     | `actual != expected` |
| `<`      | `actual < expected`  |
| `>`      | `actual > expected`  |
| `<=`     | `actual <= expected` |
| `>=`     | `actual >= expected` |

## Failure Behaviour

If the comparison returns `False`, raises `AssertionError` and the flow fails. `result_details`
contains: `"<message>: Assertion failed: <actual> <operator> <expected>"`.

## Use When

- The node under test produces a `float` or `int` output.
- You need to assert an exact value (`==`) or a bound (`>=`, `<`, etc.) — e.g. a confidence score
  is above a threshold, a word count is positive, a duration is within limits.
- `int` outputs can be wired directly; Python coerces them to `float` transparently.

## Example Wiring

```
ScoreNode.confidence  →  AssertNumbers.actual
(set AssertNumbers.expected = 0.8 as PROPERTY)
(set AssertNumbers.operator = ">=" as PROPERTY)
```
