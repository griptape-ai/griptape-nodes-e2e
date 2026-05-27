# griptape-nodes-e2e
# Copyright (c) 2026 The Foundry Visionmongers Ltd
"""Start a configured griptape-nodes-app engine for ad-hoc local testing.

Spins up a fresh workspace with an ephemeral port so you can point an external MCP agent
at the engine's WebSocket endpoint.

Usage:

::

    python tests/adhoc/start_engine.py \
        --library-path /path/to/lib1/griptape_nodes_library.json \
        --library-path /path/to/lib2/griptape_nodes_library.json \
        --api-key sk-... \
        --mcp-port 8126

The script prints the WebSocket URL on stdout once the engine is ready, then blocks
until you press Ctrl-C.

"""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess  # noqa: S404
import sys
import tempfile
import time
from pathlib import Path

# -- Constants ----------------------------------------------------------------

ENGINE_HOST = "127.0.0.1"
ENGINE_STARTUP_TIMEOUT = 60.0
ENGINE_STARTUP_POLL_INTERVAL = 0.5


# -- Public entry point -------------------------------------------------------


def main() -> None:
    """Parse arguments and run the engine until interrupted."""
    args = _parse_args()

    # Resolve library paths early so we fail fast on typos.
    library_paths = _resolve_library_paths(args.library_path)
    api_key = args.api_key or os.environ.get("GT_CLOUD_API_KEY", "dummy")
    mcp_port: int = args.mcp_port

    port = _find_free_port()
    tmp_config = Path(tempfile.mkdtemp(prefix="gtn_adhoc_config_"))
    tmp_workspace = Path(tempfile.mkdtemp(prefix="gtn_adhoc_workspace_"))
    tmp_data = Path(tempfile.mkdtemp(prefix="gtn_adhoc_data_"))

    _create_engine_config(tmp_config, tmp_workspace, port, library_paths)

    env = _build_env(tmp_config, tmp_data, api_key, mcp_port, port)
    proc = _start_engine(env)

    # Forward SIGINT / SIGTERM to the child so Ctrl-C shuts everything down.
    _install_signal_handlers(proc)

    ws_url = f"ws://{ENGINE_HOST}:{port}/ws/engines/events"
    mcp_url = f"http://{ENGINE_HOST}:{mcp_port}/mcp" if mcp_port else "http://<engine-assigned>:<ephemeral>/mcp"

    try:
        _wait_for_engine(ENGINE_HOST, port, ENGINE_STARTUP_TIMEOUT)
    except TimeoutError:
        proc.terminate()
        proc.wait(timeout=5)
        stdout = proc.stdout.read() if proc.stdout else ""
        print(f"Engine failed to start within {ENGINE_STARTUP_TIMEOUT}s.", file=sys.stderr)  # noqa: T201
        print(f"Output:\n{stdout}", file=sys.stderr)  # noqa: T201
        sys.exit(1)

    print(f"\n{'=' * 60}")  # noqa: T201
    print("Engine ready!")  # noqa: T201
    print(f"  WebSocket : {ws_url}")  # noqa: T201
    print(f"  MCP (SSE) : {mcp_url}")  # noqa: T201
    print(f"  Config    : {tmp_config}")  # noqa: T201
    print(f"  Workspace : {tmp_workspace}")  # noqa: T201
    print(f"  PID       : {proc.pid}")  # noqa: T201
    print(f"{'=' * 60}")  # noqa: T201
    print("Press Ctrl-C to stop.\n")  # noqa: T201

    # Stream engine stdout so the user can see logs.
    try:
        _stream_output(proc)
    except KeyboardInterrupt:
        pass
    finally:
        _shutdown(proc)


# -- Argument parsing ---------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    """Build and parse CLI arguments.

    :returns: Parsed arguments namespace.

    """
    parser = argparse.ArgumentParser(
        description="Start a griptape-nodes-app engine for local ad-hoc testing.",
    )
    parser.add_argument(
        "--library-path",
        action="append",
        default=[],
        help="Path to a griptape_nodes_library.json file to register. May be repeated.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="GT_CLOUD_API_KEY value. Falls back to $GT_CLOUD_API_KEY, then 'dummy'.",
    )
    parser.add_argument(
        "--mcp-port",
        type=int,
        default=0,
        help="Port for the MCP SSE server (GTN_MCP_SERVER_PORT). 0 = ephemeral (default).",
    )
    return parser.parse_args()


# -- Path validation ----------------------------------------------------------


def _resolve_library_paths(raw_paths: list[str]) -> list[str]:
    """Resolve and validate library JSON paths.

    :param raw_paths: Raw path strings from CLI arguments.

    :returns: List of resolved absolute path strings.

    :raises SystemExit: If any path does not exist.

    """
    resolved: list[str] = []
    for raw in raw_paths:
        p = Path(raw).resolve()
        if not p.exists():
            print(f"Error: library path does not exist: {p}", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        resolved.append(str(p))
    return resolved


# -- Config creation ----------------------------------------------------------


def _create_engine_config(
    base: Path,
    workspace: Path,
    port: int,
    library_paths: list[str],
) -> None:
    """Populate a temporary XDG config directory for the engine.

    :param base: Path to use as XDG_CONFIG_HOME.
    :param workspace: Path to use as workspace_directory.
    :param port: Port for the websocket_direct driver.
    :param library_paths: Resolved library JSON paths to register.

    """
    config_dir = base / "griptape_nodes"
    config_dir.mkdir(parents=True, exist_ok=True)

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
    (config_dir / "griptape_nodes_config.json").write_text(json.dumps(config, indent=2))
    (config_dir / ".env").write_text("GT_CLOUD_API_KEY=dummy\n")


# -- Environment & process management ----------------------------------------


def _build_env(config_home: Path, data_home: Path, api_key: str, mcp_port: int, ws_port: int) -> dict[str, str]:
    """Build the environment dict for the engine subprocess.

    :param config_home: XDG_CONFIG_HOME override.
    :param data_home: XDG_DATA_HOME override.
    :param api_key: GT_CLOUD_API_KEY value.
    :param mcp_port: Port for the MCP SSE server (0 = ephemeral).
    :param ws_port: Port of the local websocket_direct driver.

    :returns: Environment variable mapping.

    """
    env = {
        **os.environ,
        "XDG_CONFIG_HOME": str(config_home),
        "XDG_DATA_HOME": str(data_home),
        "GT_CLOUD_API_KEY": api_key,
        "GTN_MCP_TOOLS_MODE": "extended",
        "GTN_MCP_SERVER_PORT": str(mcp_port),
        "GTN_LIBRARIES_SYNC": "false",
        "GTN_REGISTER_ADVANCED_LIBRARY": "false",
        # Point the MCP server's internal Client at the local websocket_direct
        # driver instead of the cloud API so requests are routed locally.
        "GRIPTAPE_NODES_API_BASE_URL": f"http://{ENGINE_HOST}:{ws_port}",
    }
    # Disable licensing for local testing.
    env.pop("GRIPTAPE_NODES_LICENSE", None)
    return env


def _start_engine(env: dict[str, str]) -> subprocess.Popen[str]:
    """Launch the gtna engine subprocess.

    :param env: Environment variables for the subprocess.

    :returns: The running subprocess handle.

    """
    gtna_path = str(Path(sys.executable).parent / "gtna")
    return subprocess.Popen(  # noqa: S603
        [gtna_path, "engine"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _install_signal_handlers(proc: subprocess.Popen[str]) -> None:
    """Forward termination signals to the child process.

    :param proc: The engine subprocess to forward signals to.

    """

    def _handler(signum: int, _frame: object) -> None:
        proc.send_signal(signum)

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def _stream_output(proc: subprocess.Popen[str]) -> None:
    """Stream the engine's stdout to the console until the process exits.

    :param proc: The engine subprocess.

    """
    if proc.stdout is None:
        proc.wait()
        return
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    proc.wait()


def _shutdown(proc: subprocess.Popen[str]) -> None:
    """Gracefully terminate the engine subprocess.

    :param proc: The engine subprocess to stop.

    """
    if proc.poll() is not None:
        return
    print("\nShutting down engine...", file=sys.stderr)  # noqa: T201
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    print(f"Engine stopped (pid={proc.pid}).", file=sys.stderr)  # noqa: T201


# -- Network helpers ----------------------------------------------------------


def _find_free_port() -> int:
    """Bind to port 0 and return the OS-assigned ephemeral port.

    :returns: A free TCP port number.

    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((ENGINE_HOST, 0))
        return s.getsockname()[1]


def _wait_for_engine(host: str, port: int, timeout: float) -> None:
    """Block until the engine accepts a TCP connection.

    Uses a plain TCP socket probe instead of a WebSocket handshake so we don't need an
    async event loop or the websockets library.

    :param host: Host to connect to.
    :param host: Host to connect to.
    :param port: Port to connect to.
    :param timeout: Maximum seconds to wait.

    :raises TimeoutError: If the engine does not start in time.

    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(ENGINE_STARTUP_POLL_INTERVAL)
    msg = f"Attempted to connect to engine at {host}:{port}. Failed because timeout of {timeout}s was exceeded."
    raise TimeoutError(msg)


if __name__ == "__main__":
    main()
