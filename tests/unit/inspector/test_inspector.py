# griptape-nodes-e2e
# Copyright (c) 2026 The Foundry Visionmongers Ltd
"""Unit tests for griptape_nodes_e2e.inspector."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from griptape_nodes_e2e.inspector import NodeInspector
from griptape_nodes_e2e.models import NodeHandle, NodeSchema, NodeSummary, ParameterSchema


@pytest.fixture
def mock_client():
    """Create a mock NodeTestClient."""
    client = AsyncMock()
    client.request = AsyncMock()
    client.create_node = AsyncMock()
    client.list_parameters = AsyncMock()
    client.get_parameter_details = AsyncMock()
    client.delete_node = AsyncMock()

    # session() must be an async context manager that yields a flow name.
    @asynccontextmanager
    async def _mock_session(workflow_name="TestWorkflow"):  # noqa: RUF029
        yield "ControlFlow_1"

    client.session = _mock_session
    return client


@pytest.fixture
def inspector(mock_client):
    """Create a NodeInspector with a mock client."""
    return NodeInspector(client=mock_client)


class TestListNodes:
    """Tests for NodeInspector.list_nodes."""

    @pytest.mark.asyncio
    async def test_list_nodes_single_library(self, inspector, mock_client):
        """Lists nodes from a specific library."""
        mock_client.request.return_value = {"result": {"node_types": ["TextNode", "Agent"]}}

        summaries = await inspector.list_nodes(library="Griptape Nodes Library")

        assert len(summaries) == 2
        assert all(isinstance(s, NodeSummary) for s in summaries)
        assert summaries[0].node_type == "TextNode"
        assert summaries[0].library == "Griptape Nodes Library"
        assert summaries[1].node_type == "Agent"

    @pytest.mark.asyncio
    async def test_list_nodes_all_libraries(self, inspector, mock_client):
        """Lists nodes from all registered libraries."""
        mock_client.request.side_effect = [
            {"result": {"library_names": ["LibA", "LibB"]}},
            {"result": {"node_types": ["NodeX"]}},
            {"result": {"node_types": ["NodeY", "NodeZ"]}},
        ]

        summaries = await inspector.list_nodes()

        assert len(summaries) == 3
        assert summaries[0].library == "LibA"
        assert summaries[1].library == "LibB"
        assert summaries[2].library == "LibB"


class TestInspectNode:
    """Tests for NodeInspector.inspect_node."""

    @pytest.mark.asyncio
    async def test_inspect_node_returns_schema(self, inspector, mock_client):
        """Creates a transient node, inspects params, and deletes it."""
        mock_client.create_node.return_value = NodeHandle(name="TextNode_tmp", node_type="TextNode", library="Lib")
        mock_client.list_parameters.return_value = ["text", "output"]
        mock_client.get_parameter_details.side_effect = [
            ParameterSchema(
                name="text",
                type="str",
                input_types=["str"],
                output_type="str",
                default_value="",
                mode_allowed_input=True,
                mode_allowed_property=True,
                mode_allowed_output=True,
                settable=True,
                private=False,
            ),
            ParameterSchema(
                name="output",
                type="str",
                input_types=[],
                output_type="str",
                default_value=None,
                mode_allowed_input=False,
                mode_allowed_property=False,
                mode_allowed_output=True,
                settable=False,
                private=False,
            ),
        ]

        schema = await inspector.inspect_node("Lib", "TextNode")

        assert isinstance(schema, NodeSchema)
        assert schema.node_type == "TextNode"
        assert schema.library == "Lib"
        assert len(schema.parameters) == 2
        assert schema.parameters[0].name == "text"
        assert schema.parameters[1].name == "output"

        # Verify the transient node was cleaned up
        mock_client.delete_node.assert_called_once_with("TextNode_tmp")

    @pytest.mark.asyncio
    async def test_inspect_node_cleans_up_on_error(self, inspector, mock_client):
        """Deletes the transient node even if inspection fails."""
        mock_client.create_node.return_value = NodeHandle(name="Bad_tmp", node_type="Bad", library="Lib")
        mock_client.list_parameters.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            await inspector.inspect_node("Lib", "Bad")

        mock_client.delete_node.assert_called_once_with("Bad_tmp")
