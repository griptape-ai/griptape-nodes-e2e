# AssertStrings

**Library:** Griptape Nodes Testing Library **Class:** `AssertStrings` **Base class:**
`SuccessFailureNode` **Category:** assert **Display name:** Assert Strings

## Description

Asserts a string comparison between `actual` and `expected` using a selectable operator. The
richest assertion node for string outputs — covers exact equality, inequality, substring
containment, prefix/suffix checks, and full regex matching.

## Parameters

| Name       | Type  | Modes           | Default | Options                                                                     | Description                                                       |
| ---------- | ----- | --------------- | ------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `actual`   | `str` | INPUT, PROPERTY | `""`    | —                                                                           | The actual string produced by the node under test.                |
| `expected` | `str` | INPUT, PROPERTY | `""`    | —                                                                           | The expected string or pattern. For `regex`, this is the pattern. |
| `operator` | `str` | INPUT, PROPERTY | `"=="`  | `==`, `!=`, `contains`, `not contains`, `starts_with`, `ends_with`, `regex` | The comparison operator to apply.                                 |
| `message`  | `str` | INPUT, PROPERTY | `""`    | —                                                                           | Optional custom message prepended to the failure detail.          |

### Operator semantics

| Operator       | Passes when                               |
| -------------- | ----------------------------------------- |
| `==`           | `actual == expected`                      |
| `!=`           | `actual != expected`                      |
| `contains`     | `expected in actual`                      |
| `not contains` | `expected not in actual`                  |
| `starts_with`  | `actual.startswith(expected)`             |
| `ends_with`    | `actual.endswith(expected)`               |
| `regex`        | `re.search(expected, actual)` is not None |

## Failure Behaviour

If the comparison returns `False`, raises `AssertionError` and the flow fails. `result_details`
contains: `"<message>: Assertion failed: <actual!r> <operator> <expected!r>"`.

## Use When

- The node under test produces a `str` output.
- You need anything beyond exact equality: substring checks, prefix/suffix, or regex patterns.
- Prefer over `AssertEqual` for string outputs whenever the comparison is non-trivial.

## Example Wiring

```
SummaryNode.summary  →  AssertStrings.actual
(set AssertStrings.expected = "key topic" as PROPERTY)
(set AssertStrings.operator = "contains" as PROPERTY)
```
