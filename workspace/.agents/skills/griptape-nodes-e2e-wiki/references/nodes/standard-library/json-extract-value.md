# JsonExtractValue

**Library:** Griptape Nodes Library **Class:** `JsonExtractValue` **Base class:** `DataNode`
**Category:** json **Display name:** JSON Extract Value

## Description

Extracts values from JSON data using JMESPath expressions. Powerful for reaching deep into
structured output (nested dicts, arrays) to pull out the specific value you want to assert on.
Accepts JSON strings, dicts, or `json`-typed parameters.

## Parameters

| Name     | Type   | Modes           | Default | Description                                                                    |
| -------- | ------ | --------------- | ------- | ------------------------------------------------------------------------------ |
| `json`   | `json` | INPUT, PROPERTY | `"{}"`  | Input JSON data to extract from. Accepts `json`, `str`, or `dict` input types. |
| `path`   | `str`  | INPUT, PROPERTY | `""`    | JMESPath expression (e.g. `user.name`, `items[0].title`, `[*].assignee`).      |
| `output` | `json` | OUTPUT          | —       | The extracted value(s). Returns `{}` if path matches nothing.                  |

## JMESPath Quick Reference

| Expression      | Meaning                                 |
| --------------- | --------------------------------------- |
| `foo.bar`       | Nested key access                       |
| `items[0]`      | First element of array                  |
| `items[-1]`     | Last element of array                   |
| `[*].name`      | All `name` fields from array of objects |
| `length(items)` | Count of items (returns int)            |

## Use When

- The node under test outputs a complex JSON/dict structure and you need a specific nested value
  for assertion.
- More powerful than `DictGetValueByKey` for nested access or array operations.
- Wire `NodeUnderTest.<json_output>` → `JsonExtractValue.json`, set `path` as PROPERTY, then wire
  `JsonExtractValue.output` → type converter or assertion node.

## Example Wiring

```
AgentNode.output             →  JsonExtractValue.json
(set JsonExtractValue.path = "result.score" as PROPERTY)
JsonExtractValue.output      →  ToFloat.from
ToFloat.output               →  AssertNumbers.actual
(set AssertNumbers.expected = 0.8 as PROPERTY)
(set AssertNumbers.operator = ">=" as PROPERTY)
```
