# griptape-nodes-e2e
# Copyright (c) 2026 The Foundry Visionmongers Ltd
"""Typed result models for the E2E testing SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NodeHandle:
    """Reference to a created node instance in the engine.

    :param name: The engine-assigned name of the node instance.
    :param node_type: The class name of the node type.
    :param library: The library the node was created from.

    """

    name: str
    node_type: str
    library: str


@dataclass
class ParameterSchema:
    """Full schema of a single parameter on a node.

    :param name: Parameter name.
    :param type: Parameter type string.
    :param input_types: Accepted input types when connected as input.
    :param output_type: Type exposed when connected as output.
    :param default_value: Default value if any.
    :param mode_allowed_input: Whether input mode is allowed.
    :param mode_allowed_property: Whether property mode is allowed.
    :param mode_allowed_output: Whether output mode is allowed.
    :param settable: Whether the parameter can be set directly.
    :param private: Whether the parameter is private.

    """

    name: str
    type: str
    input_types: list[str]
    output_type: str
    default_value: Any | None
    mode_allowed_input: bool
    mode_allowed_property: bool
    mode_allowed_output: bool
    settable: bool
    private: bool


@dataclass
class NodeSchema:
    """Complete schema of a node type including all parameters.

    :param node_type: The class name of the node type.
    :param library: The library containing the node.
    :param category: Node category within the library.
    :param description: Human-readable description.
    :param tags: Search/filter tags.
    :param parameters: Full parameter schemas for the node.

    """

    node_type: str
    library: str
    category: str
    description: str
    tags: list[str]
    parameters: list[ParameterSchema]


@dataclass
class NodeSummary:
    """Lightweight catalogue entry for a node type.

    :param node_type: The class name of the node type.
    :param library: The library containing the node.
    :param category: Node category within the library.
    :param description: Human-readable description.
    :param display_name: Display name for UI.
    :param tags: Search/filter tags.

    """

    node_type: str
    library: str
    category: str
    description: str
    display_name: str
    tags: list[str]


@dataclass
class FlowResult:
    """Result of executing a flow.

    :param success: Whether the flow completed successfully.
    :param outputs: Mapping of node names to their parameter output values.
    :param error: Error message if the flow failed.

    """

    success: bool
    outputs: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
