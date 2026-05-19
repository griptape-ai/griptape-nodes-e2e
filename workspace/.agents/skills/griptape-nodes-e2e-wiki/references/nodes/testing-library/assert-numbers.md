# AssertNumbers

**Library:** Griptape Nodes Testing Library **Class:** `AssertNumbers` **Base class:**
`SuccessFailureNode` **Category:** assert **Display name:** Assert Numbers

## Description

Asserts a numeric comparison between `actual` and `expected` using a selectable relational
operator. Both inputs are typed `float`. Use this whenever a node produces a **`float`** output and
you want to check exact equality or a relational bound.

> **`int` output type is not compatible.** The engine enforces strict type matching on connections:
> a parameter with `output_type="int"` cannot connect to `actual` (which accepts only `float`). The
> connection is rejected at wiring time, even though Python would coerce the value at runtime. If
> the node under test produces an `int` output (e.g. after design-time type narrowing), use
> `AssertEqual` instead — its `actual` parameter accepts `any`.

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

- The node under test produces a **`float`** output (not `int` — see note above).
- You need to assert an exact value (`==`) or a bound (`>=`, `<`, etc.) — e.g. a confidence score
  is above a threshold, a word count is positive, a duration is within limits.

## Example Wiring

```
ScoreNode.confidence  →  AssertNumbers.actual
(set AssertNumbers.expected = 0.8 as PROPERTY)
(set AssertNumbers.operator = ">=" as PROPERTY)
```
