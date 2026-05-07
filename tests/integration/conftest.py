# griptape-nodes-e2e
# Copyright (c) 2026 The Foundry Visionmongers Ltd
"""Integration test conftest — starts a griptape-nodes-app engine for the test session."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import socket
import subprocess  # noqa: S404
import sys
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
import websockets
from griptape_nodes_e2e.client import NodeTestClient

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

logger = logging.getLogger(__name__)

ENGINE_HOST = "127.0.0.1"
ENGINE_STARTUP_TIMEOUT = 60.0
ENGINE_STARTUP_POLL_INTERVAL = 0.5
# Longer request timeout for integration tests — library loading can take 30s+.
CLIENT_REQUEST_TIMEOUT_MS = 120_000

# Library JSON files within git submodules under resources/.
RESOURCES_DIR = Path(__file__).parent / "resources"
LIBRARY_JSON_FILES = [
    RESOURCES_DIR / "griptape-nodes-library-testing" / "griptape_nodes_library.json",
]


# --- Public fixtures (highest-level first) ---


@pytest_asyncio.fixture(scope="session")
async def node_client(engine_process: subprocess.Popen[str]) -> AsyncGenerator[NodeTestClient, None]:
    """Provide a connected NodeTestClient for the integration test session.

    :param engine_process: The running engine subprocess (ensures ordering).

    :yields NodeTestClient: A connected client.

    """
    port = engine_process._port  # type: ignore[attr-defined]
    url = f"ws://{ENGINE_HOST}:{port}/ws/engines/events"
    client = NodeTestClient(url=url, timeout_ms=CLIENT_REQUEST_TIMEOUT_MS)
    async with client:
        yield client


@pytest.fixture(scope="session")
def engine_process() -> Generator[subprocess.Popen[str], None, None]:
    """Start a griptape-nodes-app engine subprocess for the test session.

    Uses an ephemeral port to avoid collisions with other running engines or parallel
    test runs.

    :yields: The engine subprocess handle (with ``_port`` attribute set).

    """
    port = _find_free_port()
    tmp_config = tempfile.mkdtemp(prefix="gtn_e2e_config_")
    tmp_workspace = tempfile.mkdtemp(prefix="gtn_e2e_workspace_")
    tmp_data = tempfile.mkdtemp(prefix="gtn_e2e_data_")

    _create_engine_config_dir(Path(tmp_config), Path(tmp_workspace), port)

    env = {
        **os.environ,
        "XDG_CONFIG_HOME": tmp_config,
        "XDG_DATA_HOME": tmp_data,
        "GT_CLOUD_API_KEY": "dummy",
        "GTN_MCP_TOOLS_MODE": "extended",
        "GTN_LIBRARIES_SYNC": "false",
        "GTN_REGISTER_ADVANCED_LIBRARY": "false",
    }
    # Remove GRIPTAPE_NODES_LICENSE to disable licensing
    env.pop("GRIPTAPE_NODES_LICENSE", None)

    gtna_path = str(Path(sys.executable).parent / "gtna")
    logger.info("Starting engine: %s engine (port=%d, config=%s)", gtna_path, port, tmp_config)

    proc = subprocess.Popen(  # noqa: S603
        [gtna_path, "engine"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # Attach the port so fixtures can read it.
    proc._port = port  # type: ignore[attr-defined]

    try:
        _wait_for_engine(ENGINE_HOST, port, ENGINE_STARTUP_TIMEOUT)
        logger.info("Engine ready on %s:%d (pid=%d)", ENGINE_HOST, port, proc.pid)
    except TimeoutError:
        proc.terminate()
        proc.wait(timeout=5)
        stdout = proc.stdout.read() if proc.stdout else ""
        msg = f"Engine failed to start within {ENGINE_STARTUP_TIMEOUT}s.\nOutput:\n{stdout}"
        pytest.fail(msg)

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    logger.info("Engine stopped (pid=%d)", proc.pid)


# --- Private helpers ---


def _find_free_port() -> int:
    """Bind to port 0 and return the OS-assigned ephemeral port.

    :returns: A free TCP port number.

    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((ENGINE_HOST, 0))
        return s.getsockname()[1]


def _create_engine_config_dir(base: Path, workspace: Path, port: int) -> None:
    """Populate a temporary XDG config directory for the engine.

    :param base: Path to use as XDG_CONFIG_HOME.
    :param workspace: Path to use as workspace_directory.
    :param port: Port for the websocket_direct driver.

    """
    config_dir = base / "griptape_nodes"
    config_dir.mkdir(parents=True, exist_ok=True)

    library_paths = [str(p.resolve()) for p in LIBRARY_JSON_FILES if p.exists()]

    config = {
        "workspace_directory": str(workspace),
        "app_events": {
            "on_app_initialization_complete": {
                "libraries_to_register": library_paths,
                "libraries_to_download": [],
            },
        },
        "ipc_drivers": [
            {"name": "websocket_api", "driver_type": "websocket_api", "enabled": False},
            {
                "name": "websocket_direct",
                "driver_type": "websocket_direct",
                "enabled": True,
                "host": ENGINE_HOST,
                "port": port,
            },
            {"name": "local_socket", "driver_type": "local_socket", "enabled": False},
        ],
    }
    (config_dir / "griptape_nodes_config.json").write_text(json.dumps(config))
    (config_dir / ".env").write_text("GT_CLOUD_API_KEY=dummy\n")


def _wait_for_engine(host: str, port: int, timeout: float) -> None:
    """Block until the WebSocket server accepts a connection.

    :param host: Host to connect to.
    :param port: Port to connect to.
    :param timeout: Maximum seconds to wait.

    :raises TimeoutError: If the engine does not start in time.

    """
    deadline = time.monotonic() + timeout
    url = f"ws://{host}:{port}/ws/engines/events"
    loop = asyncio.new_event_loop()
    try:
        while time.monotonic() < deadline:
            try:
                loop.run_until_complete(_probe_ws(url))
            except (OSError, websockets.exceptions.WebSocketException):
                time.sleep(ENGINE_STARTUP_POLL_INTERVAL)
            else:
                return
    finally:
        loop.close()
    msg = f"Attempted to connect to engine at {url}. Failed because timeout of {timeout}s was exceeded."
    raise TimeoutError(msg)


async def _probe_ws(url: str) -> None:
    """Try to open and immediately close a WebSocket connection.

    :param url: WebSocket URL to probe.

    """
    async with websockets.connect(url):
        pass
