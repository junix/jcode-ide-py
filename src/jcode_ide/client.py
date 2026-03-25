from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx

from ._logging import get_logger
from .protocol import DEFAULT_DIFF_TIMEOUT_MS, DEFAULT_TOOL_TIMEOUT_MS, DiffStatus, ToolNames

if TYPE_CHECKING:
    from .discovery import ServerInfo

logger = get_logger(__name__)


class IDEError(Exception):
    pass


class IDEConnectionError(IDEError):
    pass


class IDEToolError(IDEError):
    pass


@dataclass
class DiffResult:
    status: DiffStatus
    content: str | None = None
    error: str | None = None

    @property
    def accepted(self) -> bool:
        return self.status == "accepted"

    @property
    def rejected(self) -> bool:
        return self.status == "rejected"


@dataclass
class OpenFileInfo:
    path: str
    language_id: str
    is_dirty: bool


@dataclass
class Position:
    line: int
    character: int


@dataclass
class Range:
    start: Position
    end: Position


@dataclass
class ActiveEditorInfo:
    file_path: str
    language_id: str
    cursor_position: Position
    visible_range: Range


@dataclass
class SelectionInfo:
    file_path: str
    range: Range
    text: str | None
    content_sharing_disabled: bool = False


class IDEClient:
    """IDE MCP 客户端——通过 HTTP JSON-RPC 调用 IDE 扩展的 MCP 工具。

    生命周期
    --------
    支持两种使用模式：
    - **上下文管理器模式**（推荐）：``async with IDEClient(info) as client:``
      复用同一个 httpx.AsyncClient 连接池。
    - **即用即弃模式**：不使用 async with，每次 _call_tool 创建临时 client
      并在调用后关闭。适用于偶发调用。

    并发约束
    --------
    ``_diff_lock`` 保证同一时刻只有一个 open_diff 操作在进行。这是必要的，
    因为 VS Code 只能同时显示一个 diff 视图——并发打开会导致前一个被覆盖。
    其他只读操作（get_open_files、get_selection 等）不受此锁限制。
    """

    def __init__(self, server_info: ServerInfo):
        self.server_info = server_info
        self._diff_lock = asyncio.Lock()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> IDEClient:
        logger.debug("Opening IDE client connection", bind={"server_url": self.server_info.base_url})
        self._client = httpx.AsyncClient(
            base_url=self.server_info.base_url,
            headers={"Authorization": f"Bearer {self.server_info.auth_token}"},
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            logger.debug("Closing IDE client connection")
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client:
            return self._client
        return httpx.AsyncClient(
            base_url=self.server_info.base_url,
            headers={"Authorization": f"Bearer {self.server_info.auth_token}"},
        )

    async def ping(self) -> dict[str, Any]:
        return await self._call_tool(ToolNames.PING, {}, timeout=DEFAULT_TOOL_TIMEOUT_MS / 1000)

    async def open_diff(self, file_path: str, new_content: str, *, timeout: float | None = None) -> DiffResult:
        if timeout is None:
            timeout = DEFAULT_DIFF_TIMEOUT_MS / 1000

        async with self._diff_lock:
            try:
                logger.debug(
                    "Opening IDE diff view",
                    bind={"file_path": file_path, "timeout": timeout, "content_length": len(new_content)},
                )
                response = await self._call_tool(
                    ToolNames.OPEN_DIFF,
                    {"filePath": file_path, "newContent": new_content},
                    timeout=timeout,
                )
                logger.debug("Received IDE diff result", bind={"status": response.get("status", "error")})
                return DiffResult(
                    status=response.get("status", "error"),
                    content=response.get("content"),
                    error=response.get("error"),
                )
            except IDEError as exc:
                logger.error("IDE diff operation failed", bind={"file_path": file_path, "error": str(exc)})
                return DiffResult(status="error", error=str(exc))

    async def close_diff(self, file_path: str) -> None:
        await self._call_tool(ToolNames.CLOSE_DIFF, {"filePath": file_path}, timeout=DEFAULT_TOOL_TIMEOUT_MS / 1000)

    async def get_open_files(self) -> list[OpenFileInfo]:
        response = await self._call_tool(ToolNames.GET_OPEN_FILES, {}, timeout=DEFAULT_TOOL_TIMEOUT_MS / 1000)
        files = response.get("files", [])
        return [
            OpenFileInfo(path=file_info["path"], language_id=file_info.get("languageId", ""), is_dirty=file_info.get("isDirty", False))
            for file_info in files
        ]

    async def get_active_editor(self) -> ActiveEditorInfo | None:
        response = await self._call_tool(ToolNames.GET_ACTIVE_EDITOR, {}, timeout=DEFAULT_TOOL_TIMEOUT_MS / 1000)
        if not response.get("hasActiveEditor"):
            return None

        cursor = response.get("cursorPosition", {})
        visible = response.get("visibleRange", {})

        return ActiveEditorInfo(
            file_path=response["filePath"],
            language_id=response.get("languageId", ""),
            cursor_position=Position(line=cursor.get("line", 0), character=cursor.get("character", 0)),
            visible_range=Range(
                start=Position(line=visible.get("start", {}).get("line", 0), character=visible.get("start", {}).get("character", 0)),
                end=Position(line=visible.get("end", {}).get("line", 0), character=visible.get("end", {}).get("character", 0)),
            ),
        )

    async def get_selection(self) -> SelectionInfo | None:
        response = await self._call_tool(ToolNames.GET_SELECTION, {}, timeout=DEFAULT_TOOL_TIMEOUT_MS / 1000)
        if not response.get("hasSelection"):
            return None

        range_data = response.get("range", {})
        return SelectionInfo(
            file_path=response["filePath"],
            range=Range(
                start=Position(line=range_data.get("start", {}).get("line", 0), character=range_data.get("start", {}).get("character", 0)),
                end=Position(line=range_data.get("end", {}).get("line", 0), character=range_data.get("end", {}).get("character", 0)),
            ),
            text=response.get("text"),
            content_sharing_disabled=response.get("contentSharingDisabled", False),
        )

    async def _call_tool(self, name: str, arguments: dict[str, Any], *, timeout: float = 30.0) -> dict[str, Any]:
        client = self._get_client()
        should_close = self._client is None

        try:
            logger.debug("Calling IDE MCP tool", bind={"tool": name, "timeout": timeout, "args": list(arguments.keys())})
            response = await client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "method": "tools/call", "params": {"name": name, "arguments": arguments}, "id": 1},
                timeout=timeout,
            )
            response.raise_for_status()
            result = response.json()

            if isinstance(result, dict) and "jsonrpc" not in result and "result" not in result and "error" in result:
                logger.error("IDE server authentication error", bind={"error": result.get("error")})
                raise IDEConnectionError(f"Server error: {result.get('error')}")

            if "error" in result:
                error = result["error"]
                message = error.get("message") if isinstance(error, dict) else str(error)
                logger.error("IDE RPC error", bind={"error": message})
                raise IDEToolError(f"RPC error: {message}")

            tool_result = result.get("result", {})
            if name != ToolNames.OPEN_DIFF and tool_result.get("status") == "error":
                error_msg = tool_result.get("error", "Unknown error")
                logger.error("IDE tool execution error", bind={"tool": name, "error": error_msg})
                raise IDEToolError(error_msg)

            return tool_result
        except httpx.TimeoutException as exc:
            logger.error("IDE request timed out", bind={"tool": name, "timeout": timeout})
            raise IDEConnectionError(f"Request timed out after {timeout}s") from exc
        except httpx.HTTPError as exc:
            logger.error("IDE HTTP request failed", bind={"tool": name, "error": str(exc)})
            raise IDEConnectionError(f"HTTP error: {exc}") from exc
        finally:
            if should_close:
                await client.aclose()
