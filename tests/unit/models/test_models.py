# griptape-nodes-e2e
# Copyright (c) 2026 The Foundry Visionmongers Ltd
"""Unit tests for griptape_nodes_e2e.models."""

from __future__ import annotations

from griptape_nodes_e2e.models import (
    FlowResult,
    NodeHandle,
    NodeSchema,
    NodeSummary,
    ParameterSchema,
)


class TestNodeHandle:
    """Tests for NodeHandle dataclass."""

    def test_construction(self) -> None:
        """NodeHandle stores name, node_type, and library."""
        handle = NodeHandle(name="TextNode_1", node_type="TextNode", library="Griptape Nodes Library")

        assert handle.name == "TextNode_1"
        assert handle.node_type == "TextNode"
        assert handle.library == "Griptape Nodes Library"


class TestParameterSchema:
    """Tests for ParameterSchema dataclass."""

    def test_construction(self) -> None:
        """ParameterSchema stores all parameter metadata."""
        schema = ParameterSchema(
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
        )

        assert schema.name == "text"
        assert schema.type == "str"
        assert schema.input_types == ["str"]
        assert schema.output_type == "str"
        assert schema.default_value == ""
        assert schema.mode_allowed_input is True
        assert schema.mode_allowed_property is True
        assert schema.mode_allowed_output is True
        assert schema.settable is True
        assert schema.private is False

    def test_none_default(self) -> None:
        """ParameterSchema accepts None as default_value."""
        schema = ParameterSchema(
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
        )

        assert schema.default_value is None


class TestNodeSchema:
    """Tests for NodeSchema dataclass."""

    def test_construction(self) -> None:
        """NodeSchema stores node type metadata and parameters."""
        param = ParameterSchema(
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
        )
        schema = NodeSchema(
            node_type="TextNode",
            library="Griptape Nodes Library",
            category="Text",
            description="A simple text node",
            tags=["text", "string"],
            parameters=[param],
        )

        assert schema.node_type == "TextNode"
        assert schema.library == "Griptape Nodes Library"
        assert schema.category == "Text"
        assert schema.description == "A simple text node"
        assert schema.tags == ["text", "string"]
        assert len(schema.parameters) == 1
        assert schema.parameters[0].name == "text"


class TestNodeSummary:
    """Tests for NodeSummary dataclass."""

    def test_construction(self) -> None:
        """NodeSummary stores lightweight catalogue information."""
        summary = NodeSummary(
            node_type="TextNode",
            library="Griptape Nodes Library",
            category="Text",
            description="A simple text node",
            display_name="Text",
            tags=["text", "string"],
        )

        assert summary.node_type == "TextNode"
        assert summary.display_name == "Text"
        assert summary.tags == ["text", "string"]


class TestFlowResult:
    """Tests for FlowResult dataclass."""

    def test_success(self) -> None:
        """FlowResult represents a successful flow execution."""
        result = FlowResult(success=True, outputs={"TextNode_1": {"text": "hello"}})

        assert result.success is True
        assert result.outputs == {"TextNode_1": {"text": "hello"}}
        assert result.error is None

    def test_failure(self) -> None:
        """FlowResult represents a failed flow execution."""
        result = FlowResult(success=False, error="Node execution failed")

        assert result.success is False
        assert result.outputs == {}
        assert result.error == "Node execution failed"

    def test_defaults(self) -> None:
        """FlowResult defaults outputs to empty dict and error to None."""
        result = FlowResult(success=True)

        assert result.outputs == {}
        assert result.error is None
