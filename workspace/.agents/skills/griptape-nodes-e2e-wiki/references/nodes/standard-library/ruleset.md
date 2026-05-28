# Ruleset

**Library:** Griptape Nodes Library **Class:** `Ruleset` **Base class:** `DataNode` **Category:**
rules **Display name:** Ruleset

## Description

Creates a `Ruleset` from a name and a set of rules (one per double-newline-separated block). The
output is a Griptape `Ruleset` object suitable for connecting to nodes that accept `Ruleset` or
`list[Ruleset]` parameters (e.g. `Agent.rulesets`).

## Parameters

| Name      | Type      | Modes            | Default      | Description                                                             |
| --------- | --------- | ---------------- | ------------ | ----------------------------------------------------------------------- |
| `name`    | `str`     | INPUT, PROPERTY  | `"Behavior"` | The ruleset name.                                                       |
| `rules`   | `str`     | INPUT, PROPERTY  | `""`         | Rules text. Separate individual rules with double newlines (`\n\n`).    |
| `ruleset` | `Ruleset` | PROPERTY, OUTPUT | `null`       | The created `Ruleset` instance. Connect to a `Ruleset`-accepting param. |

## Use When

- You need to provide a `Ruleset` value to a node under test (e.g. `Agent.rulesets`).
- Set `name` and `rules` as properties, then connect `ruleset` to the target.
- For `ParameterList`-style inputs like `Agent.rulesets`, use `AddParameterToNodeRequest` to create
  a slot on the target, then connect `Ruleset.ruleset` to that slot.

## Example Wiring

```
(set Ruleset.name = "TestRules" as PROPERTY)
(set Ruleset.rules = "Always respond in English\n\nBe concise" as PROPERTY)
Ruleset.ruleset  →  Agent.rulesets (via AddParameterToNodeRequest slot)
```

To wire to an expander-style `ParameterList` input:

1. `AddParameterToNodeRequest(node_name="Agent_1", parent_container_name="rulesets")` → returns
   slot name (e.g. `rulesets_ParameterListUniqueParamID_abc123`)
2. `CreateConnectionRequest(source="Ruleset_1", source_param="ruleset", target="Agent_1", target_param="rulesets_ParameterListUniqueParamID_abc123")`
