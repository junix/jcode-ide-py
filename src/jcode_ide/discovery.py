from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import httpx

from ._logging import get_logger
from .protocol import ToolNames

logger = get_logger(__name__)


@dataclass
class ServerInfo:
    port: int
    auth_token: str
    workspace_path: str
    pid: int
    created_at: int
    instance_nonce: str

    @property
    def base_url(self) -> str:
        return f"http://localhost:{self.port}"


class IDEServerDiscovery:
    PORT_FILE_DIR: ClassVar[Path] = Path.home() / ".tmp" / "letta" / "ide"

    @classmethod
    async def find_server(
        cls,
        workspace_path: str | None = None,
        verify_ping: bool = True,
    ) -> ServerInfo | None:
        if port_str := os.environ.get("LETTA_IDE_SERVER_PORT"):
            try:
                server = cls._load_server_by_port(int(port_str))
                if server and (not verify_ping or await cls._ping_server(server)):
                    logger.debug("Found IDE server from environment variable: port={}", server.port)
                    return server
            except ValueError:
                logger.warning("Invalid LETTA_IDE_SERVER_PORT: {}", port_str)

        candidates = cls._scan_port_files()
        logger.debug("Found {} IDE server candidates", len(candidates))

        if workspace_path:
            workspace_path = str(Path(workspace_path).resolve())
            for server in candidates:
                if server.workspace_path == workspace_path:
                    if not verify_ping or await cls._ping_server(server):
                        logger.debug("Found workspace-matched IDE server: port={}", server.port)
                        return server

        for server in candidates:
            if not verify_ping or await cls._ping_server(server):
                logger.debug("Found first available IDE server: port={}", server.port)
                return server

        logger.debug("No IDE server available")
        return None

    @classmethod
    def _load_server_by_port(cls, port: int) -> ServerInfo | None:
        if not cls.PORT_FILE_DIR.exists():
            return None

        for path in cls.PORT_FILE_DIR.glob(f"letta-ide-server-*-{port}.json"):
            try:
                return cls._parse_port_file(path)
            except (json.JSONDecodeError, OSError, KeyError):
                continue
        return None

    @classmethod
    def _scan_port_files(cls) -> list[ServerInfo]:
        if not cls.PORT_FILE_DIR.exists():
            return []

        servers: list[ServerInfo] = []
        for path in cls.PORT_FILE_DIR.glob("letta-ide-server-*.json"):
            try:
                server = cls._parse_port_file(path)
                if server and cls._is_process_alive(server.pid):
                    servers.append(server)
            except (json.JSONDecodeError, OSError, KeyError) as exc:
                logger.debug("Failed to parse port file {}: {}", path, exc)
                continue

        return sorted(servers, key=lambda server: server.created_at, reverse=True)

    @classmethod
    def _parse_port_file(cls, path: Path) -> ServerInfo:
        data = json.loads(path.read_text())
        return ServerInfo(
            port=data["port"],
            auth_token=data["authToken"],
            workspace_path=data["workspacePath"],
            pid=data["pid"],
            created_at=data["createdAt"],
            instance_nonce=data["instanceNonce"],
        )

    @classmethod
    async def _ping_server(cls, server: ServerInfo) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.post(
                    f"{server.base_url}/mcp",
                    headers={"Authorization": f"Bearer {server.auth_token}"},
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {"name": ToolNames.PING, "arguments": {}},
                        "id": 1,
                    },
                )
                result = response.json()
                nonce = result.get("result", {}).get("nonce")
                if nonce == server.instance_nonce:
                    return True
                logger.debug("Nonce mismatch: expected={}, got={}", server.instance_nonce, nonce)
                return False
        except Exception as exc:
            logger.debug("IDE server ping failed (port {}): {}", server.port, exc)
            return False

    @classmethod
    def _is_process_alive(cls, pid: int | None) -> bool:
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    @classmethod
    def cleanup_stale_port_files(cls) -> int:
        if not cls.PORT_FILE_DIR.exists():
            return 0

        removed = 0
        for path in cls.PORT_FILE_DIR.glob("letta-ide-server-*.json"):
            try:
                data = json.loads(path.read_text())
                pid = data.get("pid")
                if not cls._is_process_alive(pid):
                    path.unlink()
                    removed += 1
                    logger.debug("Removed stale IDE port file: {}", path)
            except (json.JSONDecodeError, OSError) as exc:
                logger.debug("Failed to process port file {}: {}", path, exc)
                continue

        return removed
