---
name: griptape-nodes-e2e-wiki
description: >-
  Reference wiki for planning Griptape Nodes test workflows. Use when deciding which nodes to
  create, how to wire them, and which assertion nodes to use to validate outputs — i.e. the
  planning phase that precedes code generation. Do NOT use for writing pytest code (use the
  griptape-nodes-e2e-sdk skill for that).
metadata:
  author: the-foundry-visionmongers
  version: '0.1'
---

# Griptape Nodes E2E Wiki

This wiki is a planning aid. Consult it when you need to answer questions like:

- "My node under test outputs a `float` — which assertion node validates that?"
- "I need a string comparison with a regex — what parameters does that node take?"
- "What libraries and node types are available for use as inputs or outputs in a test workflow?"

______________________________________________________________________

## How to Navigate

1. Use the **Quick Type Lookup** table below to jump from a parameter type to relevant assertion
   nodes.
2. Use the **Catalogue** to find the reference page for a specific node.
3. Open a reference page (links are relative to this file) to read the full parameter schema,
   failure behaviour, and wiring guidance.

______________________________________________________________________

## Quick Type Lookup

Start here when you know the output type of the node under test and need to pick an assertion node.

| Output type of node under test | Recommended assertion node(s)                                                                                                                                          |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `str`                          | [AssertStrings](references/nodes/testing-library/assert-strings.md) (rich operators), [AssertEqual](references/nodes/testing-library/assert-equal.md) (exact equality) |
| `float` / `int`                | [AssertNumbers](references/nodes/testing-library/assert-numbers.md)                                                                                                    |
| `bool`                         | [AssertTrue](references/nodes/testing-library/assert-true.md), [AssertEqual](references/nodes/testing-library/assert-equal.md)                                         |
| `any` (unknown / mixed)        | [AssertEqual](references/nodes/testing-library/assert-equal.md), [AssertTrue](references/nodes/testing-library/assert-true.md)                                         |
| file / path                    | [AssertFileExists](references/nodes/testing-library/assert-file-exists.md)                                                                                             |

______________________________________________________________________

## Catalogue

All reference pages are listed below with direct links. There are no intermediate index pages —
every link goes straight to the leaf page.

### Assertion Nodes — `Griptape Nodes Testing Library`

| Node               | Reference page                                                                  | One-line summary                                                                   |
| ------------------ | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `AssertEqual`      | [assert-equal.md](references/nodes/testing-library/assert-equal.md)             | Assert `actual == expected` for any type                                           |
| `AssertTrue`       | [assert-true.md](references/nodes/testing-library/assert-true.md)               | Assert a value is truthy                                                           |
| `AssertStrings`    | [assert-strings.md](references/nodes/testing-library/assert-strings.md)         | String comparison with `==`, `!=`, `contains`, `starts_with`, `ends_with`, `regex` |
| `AssertNumbers`    | [assert-numbers.md](references/nodes/testing-library/assert-numbers.md)         | Numeric comparison with `==`, `!=`, `<`, `>`, `<=`, `>=`                           |
| `AssertFileExists` | [assert-file-exists.md](references/nodes/testing-library/assert-file-exists.md) | Assert a file exists at a given path                                               |

### Input Providers — `Griptape Nodes Library`

Nodes that furnish literal values to the node under test's input parameters.

| Node           | Reference page                                                         | One-line summary                           |
| -------------- | ---------------------------------------------------------------------- | ------------------------------------------ |
| `TextInput`    | [text-input.md](references/nodes/standard-library/text-input.md)       | Provides a literal `str` value             |
| `FloatInput`   | [float-input.md](references/nodes/standard-library/float-input.md)     | Provides a literal `float` value           |
| `IntegerInput` | [integer-input.md](references/nodes/standard-library/integer-input.md) | Provides a literal `int` value             |
| `BoolInput`    | [bool-input.md](references/nodes/standard-library/bool-input.md)       | Provides a literal `bool` value            |
| `MergeTexts`   | [merge-texts.md](references/nodes/standard-library/merge-texts.md)     | Merge up to 4 text inputs with a separator |

### Type Converters — `Griptape Nodes Library`

Nodes that convert the output of the node under test into a type suitable for assertion.

| Node        | Reference page                                                   | One-line summary                            |
| ----------- | ---------------------------------------------------------------- | ------------------------------------------- |
| `ToText`    | [to-text.md](references/nodes/standard-library/to-text.md)       | Convert any → `str` (for `AssertStrings`)   |
| `ToFloat`   | [to-float.md](references/nodes/standard-library/to-float.md)     | Convert any → `float` (for `AssertNumbers`) |
| `ToInteger` | [to-integer.md](references/nodes/standard-library/to-integer.md) | Convert any → `int`                         |
| `ToBool`    | [to-bool.md](references/nodes/standard-library/to-bool.md)       | Convert any → `bool` (for `AssertTrue`)     |

### Control Flow — `Griptape Nodes Library`

Nodes that branch or sequence execution in a test workflow.

| Node             | Reference page                                                             | One-line summary                                                       |
| ---------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `IfElse`         | [if-else.md](references/nodes/standard-library/if-else.md)                 | Branch workflow on a boolean; optionally pass through a selected value |
| `CancelWorkflow` | [cancel-workflow.md](references/nodes/standard-library/cancel-workflow.md) | Crash the flow unconditionally — sentinel for unexpected control paths |

### Utility — `Griptape Nodes Library`

Nodes useful as sinks, probes, or helpers in test workflows.

| Node         | Reference page                                                     | One-line summary                                                        |
| ------------ | ------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| `LoggerNode` | [logger-node.md](references/nodes/standard-library/logger-node.md) | Log messages; `any`-type passthrough for debug probes and generic sinks |

### Output Extractors — `Griptape Nodes Library`

Nodes that extract a specific value from a complex output (list, dict, JSON) for assertion.

| Node                | Reference page                                                                         | One-line summary                             |
| ------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------- |
| `GetListLength`     | [get-list-length.md](references/nodes/standard-library/get-list-length.md)             | List → `int` length (for `AssertNumbers`)    |
| `GetFromList`       | [get-from-list.md](references/nodes/standard-library/get-from-list.md)                 | Extract item at index from a list            |
| `DictGetValueByKey` | [dict-get-value-by-key.md](references/nodes/standard-library/dict-get-value-by-key.md) | Extract value by key from a dict             |
| `JsonExtractValue`  | [json-extract-value.md](references/nodes/standard-library/json-extract-value.md)       | Extract nested value via JMESPath expression |

### Type Compatibility

| Page                                                                | One-line summary                                                          |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| [parameter-compatibility.md](references/parameter-compatibility.md) | Cross-reference table: parameter types → assertion nodes that accept them |

______________________________________________________________________

## Maintenance: Ingest Workflow

When you discover a new node (e.g. via iterative exploration or by reading source code), add it to
the wiki:

1. **Create a reference page** — follow the [Page Template](#page-template) below. Save it at
   `references/nodes/<library-slug>/<node-type-kebab>.md`.
2. **Add a catalogue entry** — add a row to the Catalogue table in this file linking directly to
   the new page.
3. **Update the Quick Type Lookup** — if the node accepts or produces types not already covered,
   add or update rows.
4. **Update parameter-compatibility.md** — add the node as a column and fill in the type rows.

Keep individual reference pages focused. The runtime is authoritative for parameter schema; this
wiki is a planning aid, not a contract.

______________________________________________________________________

## Page Template

Use this structure for every new node reference page:

```markdown
# <NodeType>

**Library:** <Library display name>
**Class:** `<ClassName>`
**Base class:** `<BaseClassName>`
**Category:** <category>
**Display name:** <display name>

## Description

<One paragraph description.>

## Parameters

| Name | Type | Modes | Default | Description |
| ---- | ---- | ----- | ------- | ----------- |
| `name` | `type` | INPUT, PROPERTY | `default` | Tooltip text |

## Failure Behaviour

<What happens when the assertion fails — exception type, flow impact.>

## Use When

<Guidance on which output types and scenarios this node is suited for. Include wiring advice.>

## Example Wiring

<Short prose or table showing which output parameter of which upstream node connects to which
input parameter of this node.>
```
