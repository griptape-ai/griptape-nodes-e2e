# griptape-nodes-e2e
# Copyright (c) 2026 The Foundry Visionmongers Ltd
"""Async client for building and executing test workflows against griptape-nodes-app."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Self

from griptape_nodes.api_client import Client, RequestClient

from griptape_nodes_e2e.models import FlowResult, NodeHandle, ParameterSchema

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from types import TracebackType

logger = logging.getLogger(__name__)

DEFAULT_URL = "ws://localhost:8125/ws/engines/events"
DEFAULT_TIMEOUT_MS = 30_000


class NodeTestClient:
    """Async client for building and executing test workflows.

    Wraps ``griptape_nodes.api_client.Client`` and ``RequestClient`` to provide
    high-level methods for creating nodes, setting parameters, connecting nodes, and
    executing flows against a running ``griptape-nodes-app`` instance.

    Use :meth:`session` to set up a clean workflow context:

    ::

        async with client.session() as flow_name:
            node = await client.create_node("TextNode")
            ...

    """

    def __init__(
        self,
        url: str = DEFAULT_URL,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
    ) -> None:
        """Initialise the client.

        :param url: WebSocket URL of the ``websocket_direct`` driver.
        :param timeout_ms: Default request timeout in milliseconds.

        """
        self._url = url
        self._timeout_ms = timeout_ms
        self._client: Client | None = None
        self._request_client: RequestClient | None = None
        self._session_id: str | None = None
        self._flow_name: str | None = None
        self._flow_completion_future: asyncio.Future[FlowResult] | None = None

    async def __aenter__(self) -> Self:
        """Connect to the engine and prepare for requests.

        :returns: The connected client instance.

        """
        self._client = Client(api_key="dummy", url=self._url)
        await self._client.__aenter__()

        self._request_client = RequestClient(
            client=self._client,
            request_topic_fn=self._request_topic,
            response_topic_fn=self._response_topic,
        )
        await self._request_client.__aenter__()

        self._client.add_message_filter(self._execution_event_filter)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Disconnect from the engine.

        :param exc_type: Exception type, if any.
        :param exc_val: Exception value, if any.
        :param exc_tb: Traceback, if any.

        """
        if self._client is not None:
            self._client.remove_message_filter(self._execution_event_filter)

        if self._request_client is not None:
            await self._request_client.__aexit__(exc_type, exc_val, exc_tb)
            self._request_client = None

        if self._client is not None:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
            self._client = None

    # --- Session context manager ---

    @asynccontextmanager
    async def session(self, workflow_name: str = "TestWorkflow") -> AsyncIterator[str]:
        """Set up a clean workflow context and yield the flow name.

        Handles session start, state clearing, workflow context creation, and flow
        creation automatically. On exit the state is cleared again.

        :param workflow_name: Name for the workflow context.

        :yields str: The auto-generated flow name (pass to ``start_flow`` if needed).

        """
        await self._start_session()
        await self._clear_state()
        await self._set_workflow_context(workflow_name)
        flow_name = await self._create_flow()
        try:
            yield flow_name
        finally:
            await self._clear_state()

    # --- Nodes ---

    async def create_node(
        self,
        node_type: str,
        library: str | None = None,
        flow: str | None = None,
    ) -> NodeHandle:
        """Create a node instance in the engine.

        :param node_type: Class name of the node to create.
        :param library: Library to search for the node type.
        :param flow: Flow to create the node in.

        :returns: A handle to the created node.

        """
        payload: dict[str, Any] = {"node_type": node_type}
        if library is not None:
            payload["specific_library_name"] = library
        if flow is not None:
            payload["override_parent_flow_name"] = flow

        result = await self._request("CreateNodeRequest", payload)
        node_result = result["result"]
        return NodeHandle(
            name=node_result["node_name"],
            node_type=node_result["node_type"],
            library=node_result.get("specific_library_name", library or ""),
        )

    async def delete_node(self, node_name: str) -> None:
        """Delete a node from the engine.

        :param node_name: Name of the node to delete.

        """
        await self._request("DeleteNodeRequest", {"node_name": node_name})

    async def get_all_node_info(self, node_name: str) -> dict[str, Any]:
        """Get comprehensive information about a node.

        :param node_name: Name of the node.

        :returns: Full node info dictionary from the engine.

        """
        result = await self._request("GetAllNodeInfoRequest", {"node_name": node_name})
        return result["result"]

    # --- Parameters ---

    async def set_parameter(self, node_name: str, parameter_name: str, value: Any) -> None:
        """Set a parameter value on a node.

        :param node_name: Name of the node.
        :param parameter_name: Name of the parameter.
        :param value: Value to set.

        """
        await self._request(
            "SetParameterValueRequest",
            {"node_name": node_name, "parameter_name": parameter_name, "value": value},
        )

    async def get_parameter(self, node_name: str, parameter_name: str) -> Any:
        """Get the current value of a parameter.

        :param node_name: Name of the node.
        :param parameter_name: Name of the parameter.

        :returns: The parameter value.

        """
        result = await self._request(
            "GetParameterValueRequest",
            {"node_name": node_name, "parameter_name": parameter_name},
        )
        return result["result"]["value"]

    async def get_parameter_details(self, node_name: str, parameter_name: str) -> ParameterSchema:
        """Get detailed parameter schema information.

        :param node_name: Name of the node.
        :param parameter_name: Name of the parameter.

        :returns: ParameterSchema with full metadata.

        """
        result = await self._request(
            "GetParameterDetailsRequest",
            {"node_name": node_name, "parameter_name": parameter_name},
        )
        r = result["result"]
        return ParameterSchema(
            name=parameter_name,
            type=r["type"],
            input_types=r["input_types"],
            output_type=r["output_type"],
            default_value=r["default_value"],
            mode_allowed_input=r["mode_allowed_input"],
            mode_allowed_property=r["mode_allowed_property"],
            mode_allowed_output=r["mode_allowed_output"],
            settable=r.get("settable", False),
            private=r.get("private", False),
        )

    async def list_parameters(self, node_name: str) -> list[str]:
        """List all parameter names on a node.

        :param node_name: Name of the node.

        :returns: List of parameter names.

        """
        result = await self._request("ListParametersOnNodeRequest", {"node_name": node_name})
        return result["result"]["parameter_names"]

    # --- Connections ---

    async def connect(
        self,
        source_node: str,
        source_param: str,
        target_node: str,
        target_param: str,
    ) -> None:
        """Create a connection between two node parameters.

        :param source_node: Name of the source node.
        :param source_param: Name of the source parameter.
        :param target_node: Name of the target node.
        :param target_param: Name of the target parameter.

        """
        await self._request(
            "CreateConnectionRequest",
            {
                "source_node_name": source_node,
                "source_parameter_name": source_param,
                "target_node_name": target_node,
                "target_parameter_name": target_param,
            },
        )

    async def disconnect(
        self,
        source_node: str,
        source_param: str,
        target_node: str,
        target_param: str,
    ) -> None:
        """Delete a connection between two node parameters.

        :param source_node: Name of the source node.
        :param source_param: Name of the source parameter.
        :param target_node: Name of the target node.
        :param target_param: Name of the target parameter.

        """
        await self._request(
            "DeleteConnectionRequest",
            {
                "source_node_name": source_node,
                "source_parameter_name": source_param,
                "target_node_name": target_node,
                "target_parameter_name": target_param,
            },
        )

    # --- Execution ---

    async def start_flow(self, flow_name: str | None = None) -> None:
        """Start executing a flow.

        :param flow_name: Name of the flow to start. Defaults to the flow created by
            :meth:`session`.

        :raises RuntimeError: If no flow name is provided and no session is active.

        """
        if flow_name is None:
            flow_name = self._flow_name
        if flow_name is None:
            msg = "Attempted to start flow. Failed because no flow name was provided and no session is active."
            raise RuntimeError(msg)

        self._flow_completion_future = asyncio.get_event_loop().create_future()
        await self._request("StartFlowRequest", {"flow_name": flow_name})

    async def wait_for_flow_completion(self, deadline_seconds: float = 60.0) -> FlowResult:
        """Wait for the currently running flow to complete.

        Must be called after ``start_flow``.

        :param deadline_seconds: Maximum seconds to wait.

        :returns: The flow execution result.

        :raises TimeoutError: If the flow does not complete in time.
        :raises RuntimeError: If start_flow was not called first.

        """
        if self._flow_completion_future is None:
            msg = "Attempted to wait for flow completion. Failed because start_flow was not called first."
            raise RuntimeError(msg)

        result = await asyncio.wait_for(self._flow_completion_future, timeout=deadline_seconds)
        self._flow_completion_future = None
        return result

    # --- Workflows ---

    async def save_workflow(self, file_name: str) -> None:
        """Save the current workflow.

        :param file_name: Name of the file to save to.

        """
        await self._request("SaveWorkflowRequest", {"file_name": file_name})

    async def load_workflow(self, file_path: str) -> None:
        """Load a workflow from a file, clearing current state.

        :param file_path: Path to the workflow file.

        """
        await self._request("RunWorkflowFromScratchRequest", {"file_path": file_path})

    # --- Raw request ---

    async def request(self, request_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Send an arbitrary request to the engine.

        Use this for request types not covered by a dedicated method.

        :param request_type: The request type name.
        :param payload: Request payload fields.

        :returns: The result payload dictionary.

        :raises RuntimeError: If the client is not connected.

        """
        return await self._request(request_type, payload)

    # --- Private helpers ---

    async def _start_session(self) -> str:
        """Start a new session on the engine.

        :returns: The session ID.

        """
        result = await self._request("AppStartSessionRequest", {})
        session_id: str = result["result"]["session_id"]
        self._session_id = session_id
        return session_id

    async def _set_workflow_context(self, workflow_name: str = "TestWorkflow") -> None:
        """Set the active workflow context.

        :param workflow_name: Name for the workflow context.

        """
        await self._request("SetWorkflowContextRequest", {"workflow_name": workflow_name})

    async def _create_flow(self, flow_name: str | None = None, parent_flow_name: str | None = None) -> str:
        """Create a new flow in the engine and store its name.

        :param flow_name: Optional name for the flow (auto-generated if None).
        :param parent_flow_name: Parent flow to nest under (None for top-level).

        :returns: The name of the created flow.

        """
        result = await self._request(
            "CreateFlowRequest",
            {
                "parent_flow_name": parent_flow_name,
                "flow_name": flow_name,
                "set_as_new_context": True,
            },
        )
        created_name: str = result["result"]["flow_name"]
        self._flow_name = created_name
        return created_name

    async def _clear_state(self) -> None:
        """Clear all object state in the engine."""
        await self._request(
            "ClearAllObjectStateRequest",
            {"i_know_what_im_doing": True},
        )
        self._flow_name = None

    async def _request(self, request_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a request and return the result payload.

        :param request_type: The request type name.
        :param payload: Request payload fields.

        :returns: The result payload dictionary.

        :raises RuntimeError: If the client is not connected.

        """
        if self._request_client is None:
            msg = "Attempted to send request. Failed because client is not connected."
            raise RuntimeError(msg)

        return await self._request_client.request(
            request_type,
            payload,
            timeout_ms=self._timeout_ms,
        )

    def _request_topic(self) -> str:
        """Get the current request topic.

        :returns: The request topic string.

        """
        if self._session_id:
            return f"sessions/{self._session_id}/request"
        return "request"

    def _response_topic(self) -> str:
        """Get the current response topic.

        :returns: The response topic string.

        """
        if self._session_id:
            return f"sessions/{self._session_id}/response"
        return "response"

    async def _execution_event_filter(self, message: dict[str, Any]) -> bool:
        """Filter execution events to detect flow completion.

        The engine wraps execution payloads in an ``ExecutionEvent`` whose serialised
        form looks like:

        ::

            {
                "type": "execution_event",
                "payload": {
                    "payload_type": "ControlFlowResolvedEvent",
                    "payload": { ...fields... }
                }
            }

        We match on ``payload_type`` and read data from the inner ``payload.payload``
        dict.

        :param message: The incoming WebSocket message.

        :returns: True if the message was claimed.

        """
        if self._flow_completion_future is None:
            return False
        if self._flow_completion_future.done():
            return False

        outer_payload = message.get("payload", {})
        # The discriminator is "payload_type", set by BaseEvent.dict().
        payload_type = outer_payload.get("payload_type", "")
        # The actual event data lives one level deeper.
        inner_payload = outer_payload.get("payload", {})

        if payload_type == "ControlFlowResolvedEvent":
            outputs = inner_payload.get("parameter_output_values", {})
            self._flow_completion_future.set_result(FlowResult(success=True, outputs=outputs))
            return True

        if payload_type == "ControlFlowCancelledEvent":
            error = inner_payload.get("result_details") or "Flow was cancelled"
            if isinstance(error, dict):
                error = str(error)
            self._flow_completion_future.set_result(FlowResult(success=False, error=error))
            return True

        return False
