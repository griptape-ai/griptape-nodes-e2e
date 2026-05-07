# griptape-nodes-e2e
# Copyright (c) 2026 The Foundry Visionmongers Ltd
"""Integration smoke test — requires a running griptape-nodes-app engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from griptape_nodes_e2e.client import NodeTestClient

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_session_context_manager(node_client: NodeTestClient) -> None:
    """Session context manager sets up and tears down cleanly."""
    async with node_client.session() as flow_name:
        assert flow_name
        assert isinstance(flow_name, str)


async def test_create_and_delete_node(node_client: NodeTestClient) -> None:
    """Can create a node and then delete it."""
    async with node_client.session():
        handle = await node_client.create_node("AssertTrue")

        assert handle.name
        assert handle.node_type == "AssertTrue"

        await node_client.delete_node(handle.name)


async def test_set_and_get_parameter(node_client: NodeTestClient) -> None:
    """Set a parameter value and read it back."""
    async with node_client.session():
        handle = await node_client.create_node("AssertTrue")

        await node_client.set_parameter(handle.name, "message", "hello world")
        value = await node_client.get_parameter(handle.name, "message")

        assert value == "hello world"


async def test_list_parameters(node_client: NodeTestClient) -> None:
    """List parameters on a created node."""
    async with node_client.session():
        handle = await node_client.create_node("AssertTrue")

        params = await node_client.list_parameters(handle.name)

        assert isinstance(params, list)
        assert len(params) > 0
        assert "value" in params


async def test_execute_flow(node_client: NodeTestClient) -> None:
    """Build a simple graph, execute it, and verify completion."""
    async with node_client.session():
        handle = await node_client.create_node("AssertTrue")
        await node_client.set_parameter(handle.name, "value", True)

        await node_client.start_flow()
        result = await node_client.wait_for_flow_completion(deadline_seconds=30.0)

        assert result.success
