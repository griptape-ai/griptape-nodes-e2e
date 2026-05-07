# Parameter Type → Assertion Node Compatibility

Use this table when you know the output parameter type of the node under test and need to pick an
assertion node.

## Compatibility Matrix

✅ = accepts this type directly ⚠️ = works but with caveats (see notes) ❌ = not suitable

| Output parameter type   | [AssertEqual](nodes/testing-library/assert-equal.md) | [AssertTrue](nodes/testing-library/assert-true.md) | [AssertStrings](nodes/testing-library/assert-strings.md) | [AssertNumbers](nodes/testing-library/assert-numbers.md) | [AssertFileExists](nodes/testing-library/assert-file-exists.md) |
| ----------------------- | ---------------------------------------------------- | -------------------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------- |
| `str`                   | ✅ exact equality                                    | ⚠️ truthy only                                     | ✅ full operator set                                     | ❌                                                       | ❌                                                              |
| `float`                 | ✅ exact equality                                    | ⚠️ truthy only (non-zero)                          | ❌                                                       | ✅ full operator set                                     | ❌                                                              |
| `int`                   | ✅ exact equality                                    | ⚠️ truthy only (non-zero)                          | ❌                                                       | ✅ coerced to float                                      | ❌                                                              |
| `bool`                  | ✅ e.g. `expected=True`                              | ✅ primary choice                                  | ❌                                                       | ❌                                                       | ❌                                                              |
| `any`                   | ✅ primary choice                                    | ✅ presence check                                  | ⚠️ only if value is str                                  | ⚠️ only if value is numeric                              | ❌                                                              |
| file path (`str`/`any`) | ✅ exact path equality                               | ❌                                                 | ✅ path pattern checks                                   | ❌                                                       | ✅ existence check                                              |

## Decision Guide

**I have a `str` output and want to check…**

- Exact value → `AssertEqual` or `AssertStrings` with `==`
- Substring present → `AssertStrings` with `contains`
- Pattern match → `AssertStrings` with `regex`
- Non-empty → `AssertTrue`

**I have a `float` or `int` output and want to check…**

- Exact value → `AssertNumbers` with `==`
- Above a threshold → `AssertNumbers` with `>=` or `>`
- Within a range → chain two `AssertNumbers` nodes (`>= lower` and `<= upper`)
- Non-zero → `AssertTrue`

**I have a `bool` output and want to check…**

- Is `True` → `AssertTrue` (simplest)
- Is `False` → `AssertEqual` with `expected=False`

**I have a file path output and want to check…**

- File was created → `AssertFileExists`
- File is at a specific known path → `AssertFileExists` with path as PROPERTY
- File path string matches expected → `AssertStrings`

**I have an `any`-typed output and want to check…**

- General equality → `AssertEqual`
- Is truthy/present → `AssertTrue`
- Then cast to a specific type in upstream node if possible and use type-specific assertion

## Notes

- `AssertNumbers.actual` is typed `float`. Wiring an `int` output works due to Python numeric
  coercion, but the engine must be able to cast the value.
- `AssertStrings` operators `contains`, `starts_with`, `ends_with`, and `regex` treat `expected` as
  the pattern/substring and `actual` as the subject — not the reverse.
- `AssertFileExists` resolves paths through `File(path).resolve()` which expands project macros.
  Raw OS paths also work.
- All assertion nodes share the optional `message` parameter for custom failure messages — always
  set it to something descriptive so failures are easy to diagnose.
