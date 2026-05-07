# AssertFileExists

**Library:** Griptape Nodes Testing Library **Class:** `AssertFileExists` **Base class:**
`SuccessFailureNode` **Category:** assert **Display name:** Assert File Exists

## Description

Asserts that a file exists at the given path. The path is resolved through the Griptape Nodes
`File` abstraction, which supports project macros (e.g. `{outputs}/result.txt`). Useful for
validating that a node which generates or writes a file actually produced output on disk.

## Parameters

| Name        | Type  | Modes           | Default | Description                                                                                                                                                                   |
| ----------- | ----- | --------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `file_path` | `any` | INPUT, PROPERTY | `""`    | Path to check. Supports project macros such as `{outputs}`, `{inputs}`, `{workspace}`. Can be a string literal set as PROPERTY or wired from a node that outputs a file path. |
| `message`   | `str` | INPUT, PROPERTY | `""`    | Optional custom message prepended to the failure detail.                                                                                                                      |

## Failure Behaviour

Two distinct failure modes:

1. **Path cannot be resolved** — `File(file_path).resolve()` raises `FileLoadError`. The node
   records the error in `result_details` and raises `AssertionError`. Flow fails.
2. **Path resolves but file does not exist** — `Path(resolved_path).exists()` returns `False`. The
   node records `"Assertion failed: no file found at <path>"` and raises `AssertionError`. Flow
   fails.

On success, `result_details` contains `"Assertion passed: file exists at <resolved_path>"`.

## Use When

- The node under test writes a file (image, text, CSV, etc.) and you want to confirm the file was
  created at the expected location.
- The output of the node under test is a file path string — wire it to `file_path`.
- The expected path is known at build time — set `file_path` as a PROPERTY using a macro.

**Note:** This node only checks existence, not content. To validate file contents, read the file
and wire its content to `AssertStrings` or `AssertEqual`.

## Example Wiring

```
ImageGeneratorNode.output_path  →  AssertFileExists.file_path
(or set file_path = "{outputs}/generated.png" as PROPERTY)
```
