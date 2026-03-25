"""IDE 集成客户端——jcode 与 VS Code/JetBrains 扩展的通信桥梁。

架构角色
--------
本库实现了 jcode Agent 与 IDE 扩展之间的 MCP（Model Context Protocol）通信。
当用户在 IDE 中运行 jcode 时，Agent 的文件编辑操作可以通过 IDE 展示 diff 预览，
用户在 IDE 中直接接受或拒绝修改（ADR-307）。

通信模型
--------
::

    jcode Agent
        ↓ open_diff(file, new_content)
    IDEClient (httpx async)
        ↓ POST /mcp  (JSON-RPC 2.0, Bearer token auth)
    IDE Extension (VS Code MCP Server)
        ↓ 展示 diff 视图，等待用户操作
    IDEClient ← response (accepted/rejected/error)

服务发现（IDEServerDiscovery）
------------------------------
IDE 扩展启动时在 ``~/.tmp/letta/ide/`` 目录写入端口文件
（``letta-ide-server-<nonce>-<port>.json``），包含 port、authToken、
workspacePath、pid、instanceNonce 等信息。发现流程：

1. 优先检查环境变量 ``LETTA_IDE_SERVER_PORT``（用于测试或固定端口场景）
2. 扫描端口文件，过滤掉进程已退出的条目
3. 按 workspace_path 精确匹配（多窗口场景）
4. ping 验证（nonce 匹配确认身份）

降级策略
--------
当 IDE 不可用时（无服务发现、ping 失败），上游可降级使用
``TerminalConfirmation``——在终端中通过 rich 渲染 unified diff 并
请求用户确认。

关键约束
--------
- ``_diff_lock``：diff 操作全局串行化，防止多个工具调用同时打开 diff 视图
  导致 IDE 状态混乱。
- MCP 工具命名空间：``letta.ide.v1.*``，带版本号便于后续协议演进。
"""

from .client import DiffResult, IDEClient
from .discovery import IDEServerDiscovery, ServerInfo
from .fallback import TerminalConfirmation

__all__ = [
    "IDEServerDiscovery",
    "ServerInfo",
    "IDEClient",
    "DiffResult",
    "TerminalConfirmation",
]
