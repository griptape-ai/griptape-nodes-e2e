# griptape-nodes-e2e
# Copyright (c) 2026 The Foundry Visionmongers Ltd
"""Pytest fixtures and markers for griptape-nodes E2E tests.

Import this module's fixtures via pytest_plugins or conftest.py:

::

    pytest_plugins = ["griptape_nodes_e2e.fixtures"]

"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from griptape_nodes_e2e.client import NodeTestClient
from griptape_nodes_e2e.inspector import NodeInspector

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

DEFAULT_ENGINE_URL = "ws://localhost:8125/ws/engines/events"


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers.

    :param config: The pytest config object.

    """
    config.addinivalue_line("markers", "integration: marks tests requiring a running engine")
    config.addinivalue_line("markers", "llm: marks tests that call real LLM APIs")


@pytest_asyncio.fixture(scope="session")
async def node_client() -> AsyncGenerator[NodeTestClient, None]:
    """Provide a connected NodeTestClient for the test session.

    Connects to the URL specified by the ``GTN_E2E_URL`` environment variable, or
    ``ws://localhost:8125/ws/engines/events`` by default.

    :yields NodeTestClient: A connected NodeTestClient instance.

    """
    url = os.environ.get("GTN_E2E_URL", DEFAULT_ENGINE_URL)
    client = NodeTestClient(url=url)
    async with client:
        yield client


@pytest.fixture(scope="session")
def node_inspector(node_client: NodeTestClient) -> NodeInspector:
    """Provide a NodeInspector for the test session.

    :param node_client: The connected client fixture.

    :returns: A NodeInspector instance.

    """
    return NodeInspector(client=node_client)
