---
name: griptape-nodes-e2e-pipeline
description: >-
  End-to-end test generation pipeline for a Griptape Node. Orchestrates the survey, inspect, plan,
  and workflow skills in sequence. Confirms the output directory with the user, manages subagent
  execution, presents the test plan for approval, and gates workflow generation on that approval.
compatibility: Requires an MCP connection to a running griptape-nodes engine (extended tools mode).
metadata:
  author: the-foundry-visionmongers
  version: '0.1'
---

# E2E Test Generation Pipeline

## Purpose

Orchestrate the full end-to-end test generation pipeline for a Griptape Node:

1. **Survey** — static analysis of the node's source code.
2. **Inspect** — live confirmation against the running engine.
3. **Plan** — propose a test matrix for user approval.
4. **Workflow** — generate and save test workflows.

This skill runs in the main conversation and handles **all user interaction** — confirming the
output directory, presenting the test plan, collecting approval, and relaying results. Each step is
delegated to a subagent that invokes the corresponding skill.

______________________________________________________________________

## Inputs

Before starting, collect two pieces of information:

1. **Node class name** — the target node to test (e.g. `Agent`).
2. **Output root directory** — the absolute path where artifacts are written. Inspections go to
   `{output_root}/inspections/` and test workflows go to `{output_root}/tests/<NodeType>/`.

If the user's message already contains both values, use them directly. Otherwise use
`AskUserQuestion` to collect whatever is missing. Suggest the current working directory as the
default output root.

______________________________________________________________________

## Resuming the Pipeline

The user may want to resume from a specific step — for example, re-running only the plan step after
manually editing the inspection report, or jumping straight to workflow generation after approving
a plan in a previous session.

If the user's message specifies a starting step (e.g. "start from plan", "just run workflows",
"re-run inspect"), skip earlier steps. Before skipping, verify the required input files exist:

| Step     | Required input files                                                      |
| -------- | ------------------------------------------------------------------------- |
| Survey   | (none)                                                                    |
| Inspect  | `{output_root}/inspections/<NodeType>.survey.md`                          |
| Plan     | `{output_root}/inspections/<NodeType>.survey.md`, `<NodeType>.inspect.md` |
| Workflow | `{output_root}/inspections/<NodeType>.plan.md`                            |

If a required file is missing, tell the user and ask whether to run the missing step first.

______________________________________________________________________

## Execution

### Step 1: Survey

Spawn an Agent subagent with this prompt (substitute `{node_name}` and `{output_root}`):

> Invoke the /griptape-nodes-e2e-survey skill to survey the **{node_name}** node. The output root
> directory is `{output_root}`.

Wait for the subagent to complete. If it reports an error, tell the user and stop.

After success, confirm to the user: "Survey complete. Proceeding to inspect."

### Step 2: Inspect

Spawn an Agent subagent with this prompt:

> Invoke the /griptape-nodes-e2e-inspect skill to inspect the **{node_name}** node. The output root
> directory is `{output_root}`.

Wait for the subagent to complete. If the subagent reports a **BLOCKED** verdict, tell the user the
specific blockers and **stop** — do not proceed to the plan step.

After success (verdict: PASS), confirm to the user: "Inspection complete (verdict: PASS).
Proceeding to plan."

### Step 3: Plan

Spawn an Agent subagent with this prompt:

> Invoke the /griptape-nodes-e2e-plan skill to create a test plan for the **{node_name}** node. The
> output root directory is `{output_root}`.

Wait for the subagent to complete.

### Step 4: Present the Plan

Read the plan file at `{output_root}/inspections/{node_name}.plan.md`. Present a focused summary to
the user covering these sections:

1. **Configuration Tests** — show the full table from the `## Configuration Tests` section.
2. **Error Tests** — summarise counts: how many pre-execution validation tests, how many runtime
   error tests, and the design-time input handling status.
3. **Rejected Configurations** — show the table from `## Rejected Configurations` if it has any
   rows.
4. **Caveats** — mention any environment dependencies or limitations from the `## Caveats` section.

Then use `AskUserQuestion` to ask the user what to do next:

- **Approve** — proceed to workflow generation.
- **Edit** — describe the changes (the user will provide change instructions in a free-text
  response or via the "Other" option).

### Step 5: Plan Edit Loop

If the user requests edits:

1. Collect the user's change description. This may come from the `AskUserQuestion` response text or
   from a follow-up message.

2. Spawn an Agent subagent with this prompt:

   > Invoke the /griptape-nodes-e2e-plan skill to edit the existing test plan for the
   > **{node_name}** node. The output root directory is `{output_root}`.
   >
   > Apply these changes: {user_requested_changes}

3. Wait for the subagent to complete.

4. Go back to **Step 4** — re-read the updated plan file and present it again.

Repeat until the user approves.

### Step 6: Workflow Generation

Once the user approves the plan, spawn an Agent subagent with this prompt:

> Invoke the /griptape-nodes-e2e-workflow skill to generate test workflows for the **{node_name}**
> node. The output root directory is `{output_root}`.

Wait for the subagent to complete.

### Step 7: Present Results

Read the workflow summary at `{output_root}/inspections/{node_name}.workflows.md`. Present to the
user:

- Total number of workflows generated.
- Pass / fail / skipped counts.
- Any failures with error details.
- Location of saved workflow files.

______________________________________________________________________

## Error Handling

- If any subagent fails, report the error to the user and ask whether to retry the step or stop.
- If the inspection verdict is BLOCKED, stop after inspect and report the blockers — do not proceed
  to plan.
- If the user cancels during the plan approval loop, stop without running workflows.
