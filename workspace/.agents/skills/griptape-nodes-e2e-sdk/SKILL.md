---
name: griptape-nodes-e2e-sdk
description: >-
  Write end-to-end pytest tests for Griptape Nodes. Use when generating or modifying tests that
  exercise node behaviour via the griptape-nodes-e2e SDK — creating nodes, setting parameters,
  connecting them, executing flows, and asserting on outputs.
compatibility: Requires Python 3.12+ and a running griptape-nodes-app engine with websocket_direct.
metadata:
  author: the-foundry-visionmongers
  version: '0.1'
---

# Writing E2E Tests for Griptape Nodes

## Agent Workflow

Follow this sequence when generating a test for a node:

1. **Discover nodes** — call `ListAvailableNodes` (or `ListRegisteredLibrariesRequest` +
   `ListNodeTypesInLibraryRequest`) to get a catalogue of available node types.
2. **Inspect the target node** — call `InspectNodeType(library, node_type)` to get the full runtime
   parameter schema (creates a transient node, gathers details, deletes it).
3. **Write the test** — produce a pytest async test using the SDK that creates nodes, sets
   parameters, connects them, executes the flow, and asserts on outputs.

## SDK Quick Reference

```python
from griptape_nodes_e2e.client import NodeTestClient

async with NodeTestClient() as client:
    session_id = await client.start_session()

    # Create nodes
    node = await client.create_node("TextNode")

    # Set parameters
    await client.set_parameter(node.name, "text", "hello")

    # Connect nodes
    await client.connect(src.name, "output", dst.name, "input")

    # Execute
    await client.start_flow()
    result = await client.wait_for_flow_completion()

    # Assert
    assert result.success
    value = await client.get_parameter(node.name, "output")

    # Cleanup
    await client.clear_state()
```

### Methods

| Method                                                                     | Description                         |
| -------------------------------------------------------------------------- | ----------------------------------- |
| `start_session() -> str`                                                   | Start a session, returns session ID |
| `create_node(node_type, library=None, flow=None) -> NodeHandle`            | Create a node instance              |
| `delete_node(node_name) -> None`                                           | Delete a node                       |
| `get_all_node_info(node_name) -> dict`                                     | Get comprehensive node info         |
| `set_parameter(node_name, parameter_name, value) -> None`                  | Set a parameter value               |
| `get_parameter(node_name, parameter_name) -> Any`                          | Get current value                   |
| `get_parameter_details(node_name, parameter_name) -> ParameterSchema`      | Get schema                          |
| `list_parameters(node_name) -> list[str]`                                  | List parameter names                |
| `connect(source_node, source_param, target_node, target_param) -> None`    | Wire nodes                          |
| `disconnect(source_node, source_param, target_node, target_param) -> None` | Unwire                              |
| `start_flow(flow_name="ControlFlow_1") -> None`                            | Start executing                     |
| `wait_for_flow_completion(deadline_seconds=60.0) -> FlowResult`            | Wait for result                     |
| `clear_state() -> None`                                                    | Clear all engine state              |
| `save_workflow(file_name) -> None`                                         | Save workflow to file               |
| `load_workflow(file_path) -> None`                                         | Load workflow (clears state first)  |
| `request(request_type, payload) -> dict`                                   | Send any raw request                |

### NodeInspector

```python
from griptape_nodes_e2e.inspector import NodeInspector

inspector = NodeInspector(client=client)
summaries = await inspector.list_nodes(library="Griptape Nodes Library")
schema = await inspector.inspect_node("Griptape Nodes Library", "TextNode")
```

## Test Structure

Every test must:

1. Be marked `@pytest.mark.asyncio` and `@pytest.mark.integration`.
2. Accept the `node_client: NodeTestClient` fixture (session-scoped, pre-connected).
3. Call `start_session()` at the top.
4. Call `clear_state()` at the end.

```python
import pytest
from griptape_nodes_e2e.client import NodeTestClient

@pytest.mark.asyncio
@pytest.mark.integration
async def test_text_node(node_client: NodeTestClient) -> None:
    """Test that TextNode passes text through."""
    await node_client.start_session()

    text_node = await node_client.create_node("TextNode")
    await node_client.set_parameter(text_node.name, "text", "hello world")

    await node_client.start_flow()
    result = await node_client.wait_for_flow_completion()

    assert result.success
    output = await node_client.get_parameter(text_node.name, "output")
    assert output == "hello world"

    await node_client.clear_state()
```

## Assertion Nodes

The `griptape-nodes-library-testing` library provides in-graph assertion nodes:

| Node               | Description                                 |
| ------------------ | ------------------------------------------- |
| `AssertEqual`      | Asserts `actual == expected`                |
| `AssertTrue`       | Asserts a value is truthy                   |
| `AssertStrings`    | String comparison with selectable operator  |
| `AssertNumbers`    | Numeric comparison with selectable operator |
| `AssertFileExists` | Asserts a file exists at the given path     |

Wire them downstream to validate outputs within the execution engine itself. If any assertion node
fails, the flow will fail (they raise `AssertionError`).

## Gotchas

- The `node_client` fixture connects to `GTN_E2E_URL` (default
  `ws://localhost:8125/ws/engines/events`). The engine must be running before tests execute.
- `wait_for_flow_completion` listens for `ControlFlowResolvedEvent` or `ControlFlowCancelledEvent`.
  If neither arrives within the deadline, `TimeoutError` is raised.
- `create_node` returns a `NodeHandle` — use `handle.name` for all subsequent calls, not the node
  type string.
- The engine auto-generates node names (e.g. `TextNode_1`). Never hardcode node names across tests.
- `clear_state()` requires `{"i_know_what_im_doing": True}` internally — the SDK handles this.
- Workflow files are Python scripts (`.py`), not JSON. `save_workflow` generates them via AST;
  `load_workflow` executes them with `exec()`.
