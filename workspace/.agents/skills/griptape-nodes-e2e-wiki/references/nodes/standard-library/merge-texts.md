# MergeTexts

**Library:** Griptape Nodes Library **Class:** `MergeTexts` **Base class:** `DataNode`
**Category:** text **Display name:** Merge Texts

## Description

Merges up to 4 text inputs into a single string, joined by a configurable separator. Useful for
combining multiple outputs into a single string for assertion, or for building up a prompt input
from parts.

## Parameters

| Name           | Type   | Modes           | Default    | Description                                                             |
| -------------- | ------ | --------------- | ---------- | ----------------------------------------------------------------------- |
| `input_1`      | `str`  | INPUT, PROPERTY | `""`       | First text input.                                                       |
| `input_2`      | `str`  | INPUT, PROPERTY | `""`       | Second text input.                                                      |
| `input_3`      | `str`  | INPUT, PROPERTY | `""`       | Third text input.                                                       |
| `input_4`      | `str`  | INPUT, PROPERTY | `""`       | Fourth text input.                                                      |
| `merge_string` | `str`  | INPUT, PROPERTY | `"\\n\\n"` | Separator string between inputs. `\\n` is converted to actual newlines. |
| `whitespace`   | `bool` | INPUT, PROPERTY | `False`    | Whether to trim whitespace from each input and the final result.        |
| `output`       | `str`  | OUTPUT          | —          | The merged text result.                                                 |

## Use When

- You need to combine multiple text values into a single string before passing to a node under test
  (e.g. building a multi-part prompt).
- You need to concatenate multiple outputs from parallel nodes before asserting on the combined
  result.
- Empty inputs are automatically skipped (not included in the merge).

## Example Wiring

```
TextInput_1.text  →  MergeTexts.input_1
TextInput_2.text  →  MergeTexts.input_2
(set MergeTexts.merge_string = " " as PROPERTY)
MergeTexts.output →  NodeUnderTest.prompt
```
