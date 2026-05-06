# griptape-nodes-e2e
# Copyright (c) 2026 The Foundry Visionmongers Ltd
"""Unit tests for griptape_nodes_e2e.client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from griptape_nodes_e2e.client import NodeTestClient
from griptape_nodes_e2e.models import FlowResult, NodeHandle, ParameterSchema


@pytest.fixture
def mock_client():
    """Create a mock Client instance."""
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    client.add_message_filter = MagicMock()
    client.remove_message_filter = MagicMock()
    client.subscribe = AsyncMock()
    return client


@pytest.fixture
def mock_request_client():
    """Create a mock RequestClient instance."""
    rc = AsyncMock()
    rc.__aenter__ = AsyncMock(return_value=rc)
    rc.__aexit__ = AsyncMock(return_value=None)
    rc.request = AsyncMock()
    return rc


@pytest_asyncio.fixture
async def connected_client(mock_client, mock_request_client):
    """Provide a NodeTestClient that is already connected with mocks."""
    with (
        patch("griptape_nodes_e2e.client.Client", return_value=mock_client),
        patch("griptape_nodes_e2e.client.RequestClient", return_value=mock_request_client),
    ):
        client = NodeTestClient(url="ws://test:8125/ws/engines/events")
        async with client:
            yield client, mock_request_client


class TestNodeTestClientLifecycle:
    """Tests for client connection lifecycle."""

    @pytest.mark.asyncio
    async def test_context_manager_connects(self, mock_client, mock_request_client):
        """Entering context connects Client and RequestClient."""
        with (
            patch("griptape_nodes_e2e.client.Client", return_value=mock_client),
            patch("griptape_nodes_e2e.client.RequestClient", return_value=mock_request_client),
        ):
            client = NodeTestClient()
            async with client:
                mock_client.__aenter__.assert_called_once()
                mock_request_client.__aenter__.assert_called_once()
                mock_client.add_message_filter.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_disconnects(self, mock_client, mock_request_client):
        """Exiting context disconnects both clients."""
        with (
            patch("griptape_nodes_e2e.client.Client", return_value=mock_client),
            patch("griptape_nodes_e2e.client.RequestClient", return_value=mock_request_client),
        ):
            client = NodeTestClient()
            async with client:
                pass
            mock_request_client.__aexit__.assert_called_once()
            mock_client.__aexit__.assert_called_once()
            mock_client.remove_message_filter.assert_called_once()


class TestNodeTestClientSession:
    """Tests for session context manager."""

    @pytest.mark.asyncio
    async def test_session_sets_up_and_tears_down(self, connected_client):
        """Session context manager starts session, sets workflow, creates flow, and clears on exit."""
        client, mock_rc = connected_client

        # Configure sequential responses for the four setup calls + final clear_state.
        mock_rc.request.side_effect = [
            # _start_session -> AppStartSessionRequest
            {"result": {"session_id": "sess-123"}},
            # _clear_state -> ClearAllObjectStateRequest
            {"result": {}},
            # _set_workflow_context -> SetWorkflowContextRequest
            {"result": {}},
            # _create_flow -> CreateFlowRequest
            {"result": {"flow_name": "ControlFlow_1"}},
            # _clear_state on exit -> ClearAllObjectStateRequest
            {"result": {}},
        ]

        async with client.session() as flow_name:
            assert flow_name == "ControlFlow_1"

        # Verify all five requests were made.
        assert mock_rc.request.call_count == 5
        call_types = [c.args[0] for c in mock_rc.request.call_args_list]
        assert call_types == [
            "AppStartSessionRequest",
            "ClearAllObjectStateRequest",
            "SetWorkflowContextRequest",
            "CreateFlowRequest",
            "ClearAllObjectStateRequest",
        ]

    @pytest.mark.asyncio
    async def test_session_stores_session_id(self, connected_client):
        """Session sets session_id so topics are session-scoped."""
        client, mock_rc = connected_client
        mock_rc.request.side_effect = [
            {"result": {"session_id": "sess-456"}},
            {"result": {}},
            {"result": {}},
            {"result": {"flow_name": "ControlFlow_1"}},
            {"result": {}},
        ]

        async with client.session():
            assert client._request_topic() == "sessions/sess-456/request"
            assert client._response_topic() == "sessions/sess-456/response"


class TestNodeTestClientNodes:
    """Tests for node operations."""

    @pytest.mark.asyncio
    async def test_create_node(self, connected_client):
        """create_node sends CreateNodeRequest and returns NodeHandle."""
        client, mock_rc = connected_client
        mock_rc.request.return_value = {
            "result": {
                "node_name": "TextNode_1",
                "node_type": "TextNode",
                "specific_library_name": "Griptape Nodes Library",
            }
        }

        handle = await client.create_node("TextNode", library="Griptape Nodes Library")

        assert isinstance(handle, NodeHandle)
        assert handle.name == "TextNode_1"
        assert handle.node_type == "TextNode"
        mock_rc.request.assert_called_once_with(
            "CreateNodeRequest",
            {"node_type": "TextNode", "specific_library_name": "Griptape Nodes Library"},
            timeout_ms=30_000,
        )

    @pytest.mark.asyncio
    async def test_create_node_minimal(self, connected_client):
        """create_node works with just node_type."""
        client, mock_rc = connected_client
        mock_rc.request.return_value = {
            "result": {
                "node_name": "Agent_1",
                "node_type": "Agent",
            }
        }

        handle = await client.create_node("Agent")

        assert handle.name == "Agent_1"
        assert handle.node_type == "Agent"

    @pytest.mark.asyncio
    async def test_delete_node(self, connected_client):
        """delete_node sends DeleteNodeRequest."""
        client, mock_rc = connected_client
        mock_rc.request.return_value = {"result": {}}

        await client.delete_node("TextNode_1")

        mock_rc.request.assert_called_once_with("DeleteNodeRequest", {"node_name": "TextNode_1"}, timeout_ms=30_000)


class TestNodeTestClientParameters:
    """Tests for parameter operations."""

    @pytest.mark.asyncio
    async def test_set_parameter(self, connected_client):
        """set_parameter sends SetParameterValueRequest."""
        client, mock_rc = connected_client
        mock_rc.request.return_value = {"result": {}}

        await client.set_parameter("TextNode_1", "text", "hello")

        mock_rc.request.assert_called_once_with(
            "SetParameterValueRequest",
            {"node_name": "TextNode_1", "parameter_name": "text", "value": "hello"},
            timeout_ms=30_000,
        )

    @pytest.mark.asyncio
    async def test_get_parameter(self, connected_client):
        """get_parameter returns the parameter value."""
        client, mock_rc = connected_client
        mock_rc.request.return_value = {"result": {"value": "hello world"}}

        value = await client.get_parameter("TextNode_1", "text")

        assert value == "hello world"

    @pytest.mark.asyncio
    async def test_get_parameter_details(self, connected_client):
        """get_parameter_details returns ParameterSchema."""
        client, mock_rc = connected_client
        mock_rc.request.return_value = {
            "result": {
                "type": "str",
                "input_types": ["str"],
                "output_type": "str",
                "default_value": "",
                "mode_allowed_input": True,
                "mode_allowed_property": True,
                "mode_allowed_output": True,
                "settable": True,
                "private": False,
            }
        }

        schema = await client.get_parameter_details("TextNode_1", "text")

        assert isinstance(schema, ParameterSchema)
        assert schema.name == "text"
        assert schema.type == "str"
        assert schema.settable is True

    @pytest.mark.asyncio
    async def test_list_parameters(self, connected_client):
        """list_parameters returns parameter names."""
        client, mock_rc = connected_client
        mock_rc.request.return_value = {"result": {"parameter_names": ["text", "output"]}}

        params = await client.list_parameters("TextNode_1")

        assert params == ["text", "output"]


class TestNodeTestClientConnections:
    """Tests for connection operations."""

    @pytest.mark.asyncio
    async def test_connect(self, connected_client):
        """Connect sends CreateConnectionRequest."""
        client, mock_rc = connected_client
        mock_rc.request.return_value = {"result": {}}

        await client.connect("TextNode_1", "output", "Agent_1", "prompt")

        mock_rc.request.assert_called_once_with(
            "CreateConnectionRequest",
            {
                "source_node_name": "TextNode_1",
                "source_parameter_name": "output",
                "target_node_name": "Agent_1",
                "target_parameter_name": "prompt",
            },
            timeout_ms=30_000,
        )

    @pytest.mark.asyncio
    async def test_disconnect(self, connected_client):
        """Disconnect sends DeleteConnectionRequest."""
        client, mock_rc = connected_client
        mock_rc.request.return_value = {"result": {}}

        await client.disconnect("TextNode_1", "output", "Agent_1", "prompt")

        mock_rc.request.assert_called_once_with(
            "DeleteConnectionRequest",
            {
                "source_node_name": "TextNode_1",
                "source_parameter_name": "output",
                "target_node_name": "Agent_1",
                "target_parameter_name": "prompt",
            },
            timeout_ms=30_000,
        )


class TestNodeTestClientExecution:
    """Tests for flow execution."""

    @pytest.mark.asyncio
    async def test_start_flow(self, connected_client):
        """start_flow sends StartFlowRequest."""
        client, mock_rc = connected_client
        mock_rc.request.return_value = {"result": {}}

        await client.start_flow("ControlFlow_1")

        mock_rc.request.assert_called_once_with("StartFlowRequest", {"flow_name": "ControlFlow_1"}, timeout_ms=30_000)

    @pytest.mark.asyncio
    async def test_start_flow_uses_session_flow_name(self, connected_client):
        """start_flow defaults to the flow name from the active session."""
        client, mock_rc = connected_client
        mock_rc.request.side_effect = [
            {"result": {"session_id": "s1"}},
            {"result": {}},
            {"result": {}},
            {"result": {"flow_name": "ControlFlow_1"}},
            {"result": {}},  # start_flow
            {"result": {}},  # clear_state on exit
        ]

        async with client.session():
            await client.start_flow()

        # The start_flow call (5th request) should use the session's flow name.
        start_flow_call = mock_rc.request.call_args_list[4]
        assert start_flow_call.args == ("StartFlowRequest", {"flow_name": "ControlFlow_1"})

    @pytest.mark.asyncio
    async def test_start_flow_no_session_raises(self, connected_client):
        """start_flow with no argument and no session raises RuntimeError."""
        client, _ = connected_client

        with pytest.raises(RuntimeError, match="no flow name"):
            await client.start_flow()

    @pytest.mark.asyncio
    async def test_wait_for_flow_completion_resolved(self, connected_client):
        """wait_for_flow_completion returns success on ControlFlowResolvedEvent."""
        client, mock_rc = connected_client
        mock_rc.request.return_value = {"result": {}}

        await client.start_flow("ControlFlow_1")

        # Simulate engine sending a ControlFlowResolvedEvent.
        message = {
            "payload": {
                "payload_type": "ControlFlowResolvedEvent",
                "payload": {"parameter_output_values": {"TextNode_1": {"text": "hi"}}},
            }
        }
        claimed = await client._execution_event_filter(message)

        assert claimed is True
        result = await client.wait_for_flow_completion(deadline_seconds=1.0)
        assert isinstance(result, FlowResult)
        assert result.success is True
        assert result.outputs == {"TextNode_1": {"text": "hi"}}

    @pytest.mark.asyncio
    async def test_wait_for_flow_completion_cancelled(self, connected_client):
        """wait_for_flow_completion returns failure on ControlFlowCancelledEvent."""
        client, mock_rc = connected_client
        mock_rc.request.return_value = {"result": {}}

        await client.start_flow("ControlFlow_1")

        message = {
            "payload": {
                "payload_type": "ControlFlowCancelledEvent",
                "payload": {"result_details": "Node failed"},
            }
        }
        await client._execution_event_filter(message)

        result = await client.wait_for_flow_completion(deadline_seconds=1.0)
        assert result.success is False
        assert result.error == "Node failed"

    @pytest.mark.asyncio
    async def test_wait_for_flow_completion_timeout(self, connected_client):
        """wait_for_flow_completion raises TimeoutError when no event arrives."""
        client, mock_rc = connected_client
        mock_rc.request.return_value = {"result": {}}

        await client.start_flow("ControlFlow_1")

        with pytest.raises(TimeoutError):
            await client.wait_for_flow_completion(deadline_seconds=0.01)

    @pytest.mark.asyncio
    async def test_wait_without_start_raises(self, connected_client):
        """wait_for_flow_completion raises RuntimeError if start_flow not called."""
        client, _ = connected_client

        with pytest.raises(RuntimeError, match="start_flow was not called"):
            await client.wait_for_flow_completion()


class TestNodeTestClientTopics:
    """Tests for topic resolution."""

    @pytest.mark.asyncio
    async def test_topics_before_session(self, connected_client):
        """Topics default to 'request'/'response' before session."""
        client, _ = connected_client

        assert client._request_topic() == "request"
        assert client._response_topic() == "response"

    @pytest.mark.asyncio
    async def test_topics_after_session(self, connected_client):
        """Topics switch to session-scoped inside session context."""
        client, mock_rc = connected_client
        mock_rc.request.side_effect = [
            {"result": {"session_id": "abc-123"}},
            {"result": {}},
            {"result": {}},
            {"result": {"flow_name": "ControlFlow_1"}},
            {"result": {}},
        ]

        async with client.session():
            assert client._request_topic() == "sessions/abc-123/request"
            assert client._response_topic() == "sessions/abc-123/response"


class TestExecutionEventFilter:
    """Tests for the execution event message filter."""

    @pytest.mark.asyncio
    async def test_filter_ignores_unrelated_messages(self, connected_client):
        """Filter returns False for non-execution messages."""
        client, mock_rc = connected_client
        mock_rc.request.return_value = {"result": {}}

        await client.start_flow("ControlFlow_1")

        message = {"payload": {"payload_type": "NodeResolvedEvent", "payload": {"node_name": "X"}}}
        claimed = await client._execution_event_filter(message)
        assert claimed is False

    @pytest.mark.asyncio
    async def test_filter_ignores_when_no_flow_running(self, connected_client):
        """Filter returns False when no flow is awaiting completion."""
        client, _ = connected_client

        message = {"payload": {"payload_type": "ControlFlowResolvedEvent", "payload": {"parameter_output_values": {}}}}
        claimed = await client._execution_event_filter(message)
        assert claimed is False
