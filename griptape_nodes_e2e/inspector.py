# griptape-nodes-e2e
# Copyright (c) 2026 The Foundry Visionmongers Ltd
"""Introspect node types using a live engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from griptape_nodes_e2e.models import NodeSchema, NodeSummary, ParameterSchema

if TYPE_CHECKING:
    from griptape_nodes_e2e.client import NodeTestClient


class NodeInspector:
    """Introspect node types by creating transient nodes on a live engine.

    Uses a ``NodeTestClient`` to create a temporary node instance, gather full parameter
    details, then delete it. This gives the authoritative runtime schema for any node
    type.

    """

    def __init__(self, client: NodeTestClient) -> None:
        """Initialise the inspector.

        :param client: A connected ``NodeTestClient`` instance.

        """
        self._client = client

    async def list_nodes(self, library: str | None = None) -> list[NodeSummary]:
        """List available node types, optionally filtered by library.

        :param library: Library name to filter by, or None for all.

        :returns: List of node summaries with metadata.

        """
        if library is not None:
            libraries = [library]
        else:
            result = await self._client.request("ListRegisteredLibrariesRequest", {})
            libraries = result["result"]["library_names"]

        summaries: list[NodeSummary] = []
        for lib_name in libraries:
            result = await self._client.request("ListNodeTypesInLibraryRequest", {"library": lib_name})
            node_types: list[str] = result["result"]["node_types"]
            summaries.extend(
                NodeSummary(
                    node_type=node_type,
                    library=lib_name,
                    category="",
                    description="",
                    display_name=node_type,
                    tags=[],
                )
                for node_type in node_types
            )

        return summaries

    async def inspect_node(self, library: str, node_type: str) -> NodeSchema:
        """Get the full parameter schema for a node type.

        Creates a transient node, inspects all parameters, then deletes it.

        :param library: Library containing the node type.
        :param node_type: Class name of the node to inspect.

        :returns: Complete node schema with all parameter details.

        """
        # A session context is needed so the engine has an active flow.
        async with self._client.session():
            handle = await self._client.create_node(node_type, library=library)

            try:
                param_names = await self._client.list_parameters(handle.name)
                parameters: list[ParameterSchema] = []
                for param_name in param_names:
                    schema = await self._client.get_parameter_details(handle.name, param_name)
                    parameters.append(schema)
            finally:
                await self._client.delete_node(handle.name)

        return NodeSchema(
            node_type=node_type,
            library=library,
            category="",
            description="",
            tags=[],
            parameters=parameters,
        )
