# jcode-ide-py

IDE integration client that bridges jcode Agent with VS Code / JetBrains IDE extensions via MCP (Model Context Protocol). When a user runs jcode inside an IDE, the agent's file edits are presented as diff previews that the user can accept or reject directly in the editor. The library includes server discovery (port-file scanning with workspace matching and nonce-verified ping), a JSON-RPC 2.0 client with Bearer token auth, and a terminal-based fallback that renders unified diffs via rich when no IDE is available.

## Build / Test / Install

```bash
just build    # uv build
just test     # uv run -m pytest
just install  # library package — no binary to install
```

## Quick Start

```python
import asyncio
from jcode_ide import IDEClient, IDEServerDiscovery, TerminalConfirmation

async def main():
    # Discover a running IDE extension
    server = await IDEServerDiscovery.find_server(workspace_path="/path/to/project")
    if server is None:
        # Fallback: terminal-based confirmation
        fallback = TerminalConfirmation()
        await fallback.confirm_write("src/main.py", 'print("hello")\n')
        return

    # Open a diff in the IDE and wait for the user
    async with IDEClient(server) as client:
        result = await client.open_diff("src/main.py", 'print("hello")\n')
        print(result.accepted, result.status)

asyncio.run(main())
```

## Key Concepts

- **IDEServerDiscovery** -- locates a running IDE extension via port files in `~/.tmp/letta/ide/`, filtering by live process PID and verifying identity with a nonce ping. Supports environment variable override (`LETTA_IDE_SERVER_PORT`) and workspace-path matching for multi-window setups.
- **IDEClient** -- async HTTP client that calls IDE MCP tools (`openDiff`, `closeDiff`, `getOpenFiles`, `getActiveEditor`, `getSelection`). Diff operations are serialized with a lock to prevent overlapping views.
- **TerminalConfirmation** -- fallback when no IDE is detected; renders a unified diff with syntax highlighting and prompts the user in the terminal.

## Requirements

- Python 3.12+
- httpx, rich
