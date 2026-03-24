"""
MCP protocol definitions for IDE integration.
"""

from typing import Literal

PROTOCOL_VERSION = "1.0.0"
NAMESPACE = "letta.ide.v1"


class ToolNames:
    PING = f"{NAMESPACE}.ping"
    OPEN_DIFF = f"{NAMESPACE}.openDiff"
    CLOSE_DIFF = f"{NAMESPACE}.closeDiff"
    GET_OPEN_FILES = f"{NAMESPACE}.getOpenFiles"
    GET_ACTIVE_EDITOR = f"{NAMESPACE}.getActiveEditor"
    GET_SELECTION = f"{NAMESPACE}.getSelection"


DiffStatus = Literal["accepted", "rejected", "error"]

MCP_TOOLS = [
    {"name": ToolNames.PING, "description": "Health check and identity verification", "inputSchema": {"type": "object", "properties": {}, "required": []}},
    {
        "name": ToolNames.OPEN_DIFF,
        "description": "Open a diff view for a file in the IDE and block until the user accepts or rejects it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filePath": {"type": "string", "description": "Absolute file path"},
                "newContent": {"type": "string", "description": "New content to show in the diff"},
            },
            "required": ["filePath", "newContent"],
        },
    },
    {
        "name": ToolNames.CLOSE_DIFF,
        "description": "Close an open diff view, causing the corresponding openDiff call to return 'rejected'",
        "inputSchema": {
            "type": "object",
            "properties": {"filePath": {"type": "string", "description": "Path whose diff should be closed"}},
            "required": ["filePath"],
        },
    },
    {"name": ToolNames.GET_OPEN_FILES, "description": "Return the list of files currently open in the IDE", "inputSchema": {"type": "object", "properties": {}, "required": []}},
    {"name": ToolNames.GET_ACTIVE_EDITOR, "description": "Return the active editor info, including cursor position", "inputSchema": {"type": "object", "properties": {}, "required": []}},
    {"name": ToolNames.GET_SELECTION, "description": "Return the current editor selection (subject to privacy settings)", "inputSchema": {"type": "object", "properties": {}, "required": []}},
]

DEFAULT_DIFF_TIMEOUT_MS = 300_000
DEFAULT_PING_TIMEOUT_MS = 2_000
DEFAULT_TOOL_TIMEOUT_MS = 30_000
