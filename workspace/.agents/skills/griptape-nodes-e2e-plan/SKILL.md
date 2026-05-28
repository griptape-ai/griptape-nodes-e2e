---
name: griptape-nodes-e2e-plan
description: >-
  Propose a complete test plan for a Griptape Node, driven by the inspection report and survey
  document. The plan is a self-contained test specification — the only input the workflow skill
  needs. It includes parameter-value configurations, error test sections, helper nodes, MCP
  constraints, and everything else required to generate test workflows. Supports both creating new
  plans and editing existing ones. The output root directory must be provided in the task prompt.
compatibility: Requires inspection and survey documents from prior skill runs.
metadata:
  author: the-foundry-visionmongers
  version: '0.2'
---

# Planning Tests for Griptape Nodes

## Purpose

Given a target node's inspection report and survey document, produce a **complete test plan** that
the `griptape-nodes-e2e-workflow` skill consumes as its sole input. The plan is self-contained —
the workflow skill does not read the inspection report or survey document.

The plan includes:

- **Configuration tests** — parameter-value permutations that exercise different code paths,
  including both the inspection's structural configurations and new plan-proposed permutations.
- **Error tests** — pre-execution validation rules and runtime error conditions, pulled forward
  from the inspection report.
- **Operational context** — helper nodes, MCP constraints, runtime observations, and the default
  parameter surface, all carried forward from the inspection report so the workflow skill has
  everything it needs in one document.

The output is a structured markdown file saved to `{output_root}/inspections/<NodeType>.plan.md`.
The `griptape-nodes-e2e-workflow` skill **requires** this file as its only input.

______________________________________________________________________

## Modes of Operation

This skill operates in one of two modes depending on whether a plan file already exists:

### Mode 1: Create a new plan

When `{output_root}/inspections/<NodeType>.plan.md` does **not** exist:

1. Read the inspection report and survey document.
2. Classify every settable parameter.
3. Identify parameter interactions.
4. Propose test configurations using the coverage heuristics.
5. Pull forward error tests, helper nodes, MCP constraints, and runtime observations from the
   inspection report.
6. Write the plan file.

### Mode 2: Edit an existing plan

When `{output_root}/inspections/<NodeType>.plan.md` **already exists**:

1. Read the existing plan file, the inspection report, and the survey document.
2. Apply the changes requested in the task prompt.
3. Typical edits include:
   - Adding new test configurations (the user names a parameter combination and the skill fills in
     the full row with rationale).
   - Removing configurations (the skill moves them to the Rejected table with the user's reason).
   - Promoting rejected configurations (move from Rejected to Proposed).
   - Changing parameter values within a configuration.
   - Re-classifying a parameter (e.g. the user knows that `quality` exercises different backend
     paths and should be `behavioral`, not `pass-through`).
4. Write the updated plan file.

______________________________________________________________________

## Output Root

The output root directory is provided in your task prompt as an absolute path. Use it exactly as
given. Do not infer, guess, or silently default to any other path. If your task prompt does not
contain an explicit output root path, stop immediately and return an error message stating that the
output root directory was not provided.

Plans are read from and saved to `{output_root}/inspections/`. Store the confirmed path and use it
for all file reads and writes throughout this skill.

______________________________________________________________________

## Input Documents

The plan synthesizes two complementary upstream documents, each with a distinct role:

- **Inspection report** = source of truth for **what the engine actually does** — live-confirmed
  parameter surfaces, testability tags, MCP constraints, helper nodes, runtime observations, error
  confirmation status, and routing determinations. Provides the operational facts that the workflow
  skill needs.
- **Survey document** = source of truth for **why the code does what it does** — code paths,
  per-value conditional logic, validation rules, the complete error catalog, and parameter
  semantics. Drives parameter classification and coverage reasoning.

1. **Inspection report** (required) — `{output_root}/inspections/<NodeType>.inspect.md`.
2. **Survey document** (required) — `{output_root}/inspections/<NodeType>.survey.md`.
3. **Existing plan** (optional) — `{output_root}/inspections/<NodeType>.plan.md`. If this file
   exists, the skill operates in Edit mode.

If the inspection report does not exist, stop and tell the user to run the
`griptape-nodes-e2e-inspect` skill first. If the survey does not exist, stop and tell the user to
run the `griptape-nodes-e2e-survey` skill first.

**Check the inspection Verdict first.** If the verdict says `BLOCKED`, stop immediately and report
the blockers — do not plan tests for a blocked node.

______________________________________________________________________

## Parameter Classification

For every parameter listed in the inspection report's default configuration table, classify it into
one of these categories. The classification drives the coverage rules that determine how many tests
are proposed for each parameter.

| Category       | Description                                                                                                                                        | Coverage Rule                                                                                                                                                                        |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `axis`         | Already an inspection configuration section — this parameter's values change the parameter surface (visibility, types, constraints).               | Already covered by existing `config_*` tests. Do not propose additional tests unless the axis was only partially exercised (e.g. three values but only one tested).                  |
| `behavioral`   | The node has per-value logic for this parameter — different code paths, validation rules, output mutations, or backend implementation differences. | Test each value that exercises a **distinct code path**. Group values that follow the same path.                                                                                     |
| `pass-through` | The parameter value is forwarded to an external API or downstream node without node-side conditional logic.                                        | Test **one** non-default value to confirm wiring. More than one adds cost without coverage.                                                                                          |
| `range`        | Bounded numeric parameter (slider).                                                                                                                | Test **boundary values** — min, max, and one representative middle — but only if the boundaries exercise different logic. If the value is simply forwarded, treat as `pass-through`. |
| `interaction`  | This parameter's valid values depend on another parameter (or vice versa).                                                                         | Enumerate the **valid and invalid combinations** not already covered by error tests.                                                                                                 |
| `output`       | Read-only output parameter (`settable=false`).                                                                                                     | Skip — asserted in configuration tests.                                                                                                                                              |
| `control`      | Control-flow parameter (`exec_in`, `exec_out`, `failure`).                                                                                         | Skip.                                                                                                                                                                                |
| `fixed`        | Not settable, property-only with no behavioural variation, or already fully covered by error tests.                                                | Skip.                                                                                                                                                                                |

### How to determine the category

Use the **survey document** as the primary source for understanding parameter semantics:

1. **Read the survey's validation table** — if a parameter appears in validation conditions with
   per-value logic (e.g. different size rules for GPT Image 1 vs GPT Image 2), classify it as
   `behavioral`.

2. **Read the survey's runtime errors table** — if a parameter is involved in runtime error
   conditions, check whether different values trigger different error paths.

3. **Read the survey's `process()` analysis** — if the survey describes conditional logic based on
   the parameter value (e.g. model-specific API endpoints, per-format file handling), classify as
   `behavioral`.

4. **Read the survey's design-time handlers** — if the parameter interacts with other parameters at
   set time (e.g. `output_format` drives `output_compression` visibility), classify the
   interaction.

5. **If the survey does not mention per-value logic for the parameter**, and the parameter appears
   to be forwarded directly to an API call or downstream node, classify as `pass-through`.

6. **ParameterList (expander) parameters are testable** If a parameter is a `ParameterList`
   container (the inspection's MCP Constraints table will say "Expander UI" or "ParameterList"), it
   can be connected to via `AddParameterToNodeRequest` + connection. Check the wiki for a source
   node that provides the element type. Classify the parameter as `pass-through` (one test with one
   connected item) or `behavioral` (if different items produce different node-side behaviour). **Do
   not classify as `fixed`** simply because the parameter requires a connection rather than a
   `SetParameterValueRequest`.

7. **When in doubt, classify as `behavioral`** — it is better to propose a test that the user
   removes than to miss a test that catches a real bug.

### User override

The user may disagree with a classification. If the user says a parameter should be in a different
category (e.g. "I know the backend uses different auth for each model — classify `model` as
behavioral"), update the classification and regenerate the affected test configurations.

______________________________________________________________________

## Coverage Heuristics

After classifying parameters, generate test configurations using these rules:

### Rule 1: Don't duplicate existing coverage

The inspection report already defines configuration sections (`config_*`) that test parameter
surface mutations. These are pulled forward into the plan's configuration tests table. Do not
propose new tests that duplicate them.

### Rule 2: One test per distinct code path for behavioral parameters

For each `behavioral` parameter, identify the distinct code paths from the survey:

- If model A and model B share identical node-side logic, group them.
- If model A and model C follow different paths (different validation, different API handling),
  propose separate tests.

### Rule 3: One non-default value for pass-through parameters

For each `pass-through` parameter, propose exactly one test with a non-default value. Choose the
value that is most different from the default (e.g. if default is "medium", test "low" rather than
"high" — it exercises the same path but maximises value diversity).

If multiple pass-through parameters exist, **combine them** into a single test where practical.
There is no need for a separate workflow per pass-through parameter unless they interact.

### Rule 4: Boundary values for range parameters

For `range` parameters that have node-side logic at boundaries (e.g. `n` controls output slot
visibility), propose tests at meaningful boundaries. If the value is simply forwarded, treat as
pass-through and test one non-default value.

### Rule 5: Enumerate interaction combinations

For parameters classified as `interaction`, list all valid combinations not already covered.
Invalid combinations should already be covered by `error_pre_execution_*` tests.

### Rule 6: Flag API-calling tests

For nodes that call external APIs (proxied services, cloud endpoints), every happy-path test costs
real money/time. Mark each proposed configuration with whether it requires an API call. The user
can then make cost-aware decisions about which to keep.

### Rule 7: Combine where possible

If two proposed tests differ only in pass-through parameters, combine them into one test that
exercises both non-default values simultaneously. Fewer workflows is better than more workflows
when the coverage is the same.

### Rule 8: Use source node chains for connection-required parameters

Some parameters cannot be supplied via `SetParameterValueRequest` — their type (e.g.
`ImageUrlArtifact`, `AudioArtifact`) cannot be represented as a raw MCP property value. The
inspection's MCP Constraints table will flag these. **Do not reject these parameters** on the
grounds that they "require connection" or add "complexity." Connection-based inputs are exactly
what the helper node system exists for.

**Two structural patterns exist — identify which applies from the constraints column:**

**Pattern A — single-connection list parameters** (no "Expander UI" in constraints): the parameter
expects a whole `list[X]` value as one connection. Use `CreateList`: connect per-item source nodes
to `CreateList.items_0`, `items_1`, … and wire `CreateList.output` to the target parameter.

**Pattern B — expander-style ParameterList parameters** ("Expander UI" or "ParameterList" in
constraints): the parameter is a `ParameterList` container that creates individual named slots as
items are added. Use `AddParameterToNodeRequest` to create a slot, then connect a source node to
the returned slot name. **No `CreateList` needed.**.

To propose a test for a connection-required parameter:

1. Check the parameter's type and constraints (from the Default Parameter Surface table).
2. Determine the structural pattern (A or B above).
3. Look in the wiki for a source node that produces the element type — for example:
   - `ImageUrlArtifact` → `CreateColorBars` (local, no API call)
   - `str` → `TextInput`
   - `AudioArtifact` → `LoadAudio`
4. Propose the configuration test with the source connection in the "Parameters Changed from
   Default" column and note the helper nodes required.
5. If no compatible source node exists in the wiki, note this explicitly in the Omitted Tests
   section rather than silently skipping it.

Connecting one or two source nodes is **not** "functional integration testing" — it is the normal
pattern for verifying that a connection-driven input parameter is correctly wired. Omitting
coverage of a core input parameter because it requires a source connection leaves a real gap.

______________________________________________________________________

## Assembling the Plan

The plan is the **sole input** to the workflow skill. Everything the workflow skill needs must be
in the plan. Assemble it from both upstream documents:

### From the inspection report (copy directly)

These sections contain live-confirmed operational facts. Copy or adapt them directly.

- **Default parameter surface** — copy the `config_default` parameter table verbatim into the
  plan's `## Default Parameter Surface` section.
- **Configuration tests** — each `config_*` section becomes a row in the configuration tests table
  with its ID, testability tag, parameters changed, and source `inspection`.
- **Helper nodes** — copy the `## Confirmed Helper Nodes` table verbatim.
- **MCP constraints** — copy the `## MCP Constraints` table verbatim.
- **Runtime observations** — copy the `## Runtime Observations` table verbatim.
- **Verdict and caveats** — copy verbatim. If BLOCKED, the plan should not have been created.

### Error tests (synthesized from both)

The survey provides the complete error catalog (conditions, expected errors, error types). The
inspection provides confirmation results (actual errors, routing determination, testability). The
plan combines both:

- **Design-time input handling** — copy the inspection's table directly (the inspection already
  tested these and recorded the actual results).
- **Pre-execution validation** — for each condition in the survey's validation table, include the
  condition and expected error from the survey, plus the actual error and status from the
  inspection. Omit conditions the inspection marked as unreachable via MCP — note them in the
  Omitted Tests section.
- **Runtime errors** — for each condition in the survey's runtime errors table, include the
  condition and error type from the survey. The key fact the inspection adds is the **routing**
  (`graceful` or `status-only`) — this tells the workflow skill whether to test the `failure`
  branch or just assert `was_successful=False`. Include the routing and confirmation status from
  the inspection.
- **Base class** — note the base class from the survey and whether `failure` / `was_successful` /
  `result_details` parameters exist. The workflow skill uses this to choose between
  SuccessFailureNode wiring and TryCatchGroup.

______________________________________________________________________

## Output Format

Save the plan to `{output_root}/inspections/<NodeType>.plan.md`.

```markdown
# {{NodeType}} — Test Plan

Generated on {{date}}.
Based on: `{{NodeType}}.inspect.md`, `{{NodeType}}.survey.md`

## Node Identity

- **Node type:** `{{NodeType}}`
- **Library:** `{{Library Name}}`
- **Base class:** `{{SuccessFailureNode | ControlNode | DataNode | BaseNode}}`
- **Status parameters:** {{`was_successful` (bool), `result_details` (str) — or "None"}}
- **Control outputs:** {{`exec_out` (display: "Succeeded"), `failure` (display: "Failed") — or as
  applicable}}

## Default Parameter Surface

The baseline parameter table. All configuration tests start from these defaults — only the
parameters listed in each test's "Parameters Changed" column are modified.

| Name | Direction | Type | Input Types | Output Type | Default | Constraints |
|------|-----------|------|-------------|-------------|---------|-------------|
| ... | ... | ... | ... | ... | ... | ... |

## Parameter Classification

| Parameter | Category | Values | Rationale |
|-----------|----------|--------|-----------|
| {{name}} | {{category}} | {{list of possible values}} | {{why this category}} |
| ... | ... | ... | ... |

Parameters omitted (output, control, fixed): {{comma-separated list of skipped parameter names}}

## Interactions

| Parameters | Interaction | Existing Coverage |
|------------|-------------|-------------------|
| {{param_a}} × {{param_b}} | {{description}} | {{section ID if tested, or "Not covered"}} |

{{If no interactions, write "None."}}

## Configuration Tests

Each row becomes one test workflow. The workflow skill creates the target node, sets the listed
parameters (leaving all others at defaults), wires assertion nodes to outputs, and executes.

| ID | Parameters Changed from Default | Source | Testability | API Call? | Rationale |
|----|--------------------------------|--------|-------------|-----------|-----------|
| config_default | (none — all defaults) | inspection | static-workflow | {{yes/no}} | Baseline configuration |
| `config_<axis>` | {{param}}={{value}} | inspection | static-workflow | {{yes/no}} | {{from inspection section}} |
| `config_<name>` | {{param}}={{value}}, {{param}}={{value}} | plan | static-workflow | {{yes/no}} | {{coverage rationale}} |
| ... | ... | ... | ... | ... | ... |

{{IDs use the `config_` prefix. For inspection-sourced rows, use the original section ID. For
plan-proposed rows, use short descriptive snake_case names.

Rows with Testability = `construction-time` are skipped by the workflow skill — they are included
for completeness but cannot be tested by saved workflows.}}

## Rejected Configurations

Parameter combinations explicitly excluded, with rationale. The user can promote any of these
to the Configuration Tests table.

| Parameters | Reason |
|------------|--------|
| {{param}}={{value}} | {{why excluded — e.g. "same code path as `config_<other>`"}} |
| ... | ... |

## Error Tests

### Design-time input handling
**ID:** `error_design_time_input` · **Testability:** `{{static-workflow | construction-time}}`

| Parameter | Input | Result | Status |
|-----------|-------|--------|--------|
| ... | ... | ... | ... |

{{Copied from inspection. If "None.", write "None."}}

### Pre-execution validation

| ID | Condition | Parameter | Expected Error | Actual Error | Status |
|----|-----------|-----------|----------------|--------------|--------|
| `error_pre_execution_<condition>` | {{condition description}} | {{param}} | {{expected}} | {{actual}} | {{Confirmed / Discrepancy}} |
| ... | ... | ... | ... | ... | ... |

{{Condition and Expected Error from survey; Actual Error and Status from inspection. Omit rows
the inspection marked as unreachable via MCP — list them in the Omitted Tests section below.}}

### Runtime errors

| ID | Condition | Error Type | Routing | Status |
|----|-----------|------------|---------|--------|
| `error_runtime_<condition>` | {{condition}} | {{type}} | {{graceful / status-only / —}} | {{Confirmed / Not confirmed}} |
| ... | ... | ... | ... | ... |

{{Condition and Error Type from survey; Routing and Status from inspection. Routing = "graceful"
(routes through `failure` when connected, crashes when not), "status-only" (routes through
`exec_out`, sets was_successful=False), or "—" if the inspection could not confirm.
If none, write "None."}}

### Visual indicators

{{Copied from inspection, or "None."}}

## Omitted Tests

Tests from the inspection or survey that cannot be generated as workflows.

| ID or Condition | Reason |
|----------------|--------|
| {{e.g. error_pre_execution_n_out_of_range}} | {{e.g. Not reachable via MCP — slider enforces bounds}} |
| ... | ... |

## Helper Nodes

Helper nodes confirmed during inspection. The workflow skill uses these directly.

| Purpose | Node Type | Library | Parameter | Direction | Type |
|---------|-----------|---------|-----------|-----------|------|
| ... | ... | ... | ... | ... | ... |

## MCP Constraints

Parameters that require special handling when interacted with via MCP tools.

| Parameter | Constraint | Workaround |
|-----------|-----------|------------|
| ... | ... | ... |

{{If none, write "None."}}

## Runtime Observations

Confirmed input→output behaviour from inspection. The workflow skill uses these as expected
values in assertion nodes.

| Configuration | Inputs | Outputs | Control Path | Status |
|---------------|--------|---------|-------------|--------|
| ... | ... | ... | ... | ... |

## Caveats

{{Any caveats from the inspection verdict, environment dependencies, or test limitations.}}

## Approval

Review the Configuration Tests and Rejected Configurations tables above. To modify:
- **Remove a test:** delete its row from Configuration Tests (optionally move to Rejected).
- **Add a test:** add a new row with an ID, parameters, source=`plan`, and rationale.
- **Promote a rejected test:** move its row from Rejected to Configuration Tests and add an ID.
- **Change values:** edit the "Parameters Changed from Default" cell directly.

Alternatively, ask the agent to make changes — it can re-read this plan file and apply edits
with full context from the inspection and survey documents.

When satisfied, run the `griptape-nodes-e2e-workflow` skill to generate workflows from this plan.
```

______________________________________________________________________

## Section ID Naming

Plan-proposed test configurations use the `config_` prefix, following the same conventions as
inspection section IDs:

| Pattern                    | Example                    |
| -------------------------- | -------------------------- |
| Single parameter varied    | `config_model_gpt1`        |
| Multiple parameters varied | `config_transparent_png`   |
| Boundary test              | `config_n_max`             |
| Combined pass-through      | `config_passthrough_combo` |

Use short, descriptive snake_case names. Avoid encoding parameter values literally when they are
long — use a descriptive label instead (e.g. `config_model_gpt1` not
`config_model_eq_gpt_image_1`).

______________________________________________________________________

## Tips

- **Err on the side of proposing.** It is cheap for the user to delete a row. It is expensive for
  the user to discover a missing test after workflows are generated.

- **Be explicit about API cost.** For API-calling nodes, add a note at the top of the Configuration
  Tests table estimating the number of API calls the full test suite will make. This helps the user
  make informed cost decisions.

- **`GT_CLOUD_API_KEY` is always available.** The griptape-nodes engine has `GT_CLOUD_API_KEY`
  configured in its secrets. This key acts as a proxy for external services (OpenAI, Anthropic,
  etc.) via the Griptape Cloud proxy. Any node whose source code checks for `GT_CLOUD_API_KEY`,
  `GT_CLOUD_PROXY_API_KEY`, or uses the Griptape Cloud proxy — such as `OpenAiImageGeneration`,
  `Agent`, or any model-calling node — **can and should be executed** during test generation. Do
  not mark these tests as "save without execution" or flag `GT_CLOUD_API_KEY` absence as a caveat.
  However, if a node requires a *different* credential (e.g. a direct `OPENAI_API_KEY` that is not
  covered by the proxy, or a non-Griptape third-party key), that credential may genuinely be absent
  — note it as a caveat. The `API Call?` column in the Configuration Tests table is informational
  (it tells the user about cost), not a gate on execution.

- **Group pass-through parameters aggressively.** If `quality`, `moderation`, and `size` are all
  pass-through for the same node, one test with all three set to non-default values provides the
  same coverage as three separate tests. Propose the combined test and reject the individual ones.

- **Respect the inspection's MCP Constraints.** If the inspection report notes that a parameter
  value cannot be set via MCP (e.g. slider enforcement, dropdown restriction), note this in the
  Rationale column. The workflow skill will need to use workarounds (e.g. TextInput connection to
  bypass a dropdown).

- **Connection-required parameters must still be tested.** If MCP constraints say a parameter
  cannot be set via `SetParameterValueRequest` (its type is an artifact or structured object), look
  for a compatible source node in the wiki and propose a connection-based test (see Rule 8). Check
  constraints for "Expander UI" to determine whether to wire directly to a slot (`param_0`) or use
  `CreateList`. Do not reject on complexity — a single source node connection is a legitimate
  parameter test, not an integration test.

- **Don't test the external API.** The purpose of e2e tests is to verify the **node's** behaviour —
  that parameters are wired correctly, validation fires, error paths work, and outputs are
  produced. Testing whether the OpenAI API actually generates a good image for quality="high" vs
  quality="low" is out of scope.

- **No caveats for `GT_CLOUD_API_KEY`.** Since `GT_CLOUD_API_KEY` is always available (see above),
  do not write caveats like "requires API credentials" or "save without execution if no key" for
  nodes that use the Griptape Cloud proxy. Only write credential caveats for nodes that require a
  specific non-proxy key that is genuinely absent.

- **Pull forward faithfully.** When copying sections from the inspection report (helper nodes, MCP
  constraints, runtime observations, error tables), copy them verbatim. The plan is the workflow
  skill's only source of truth — anything omitted will be invisible to the workflow skill.

- **Keep the plan up to date.** If you re-run the inspection (e.g. after a node code change),
  re-run the plan skill in Edit mode to reconcile the plan with the updated inspection. The plan
  should always reflect the latest inspection results.
