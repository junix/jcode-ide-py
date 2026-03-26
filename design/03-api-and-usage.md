# API 参考与使用

## 概述

`jcode-ide-py` 提供异步优先的 API，通过 `IDEClient` 与 IDE 扩展通信，支持上下文管理器模式复用连接池。

## 快速开始

### 安装

```bash
pip install jcode-ide-py
```

### 基本使用

```python
from jcode_ide import IDEClient, IDEServerDiscovery

# 发现 IDE 服务器
server = await IDEServerDiscovery.find_server(workspace_path="/path/to/project")
if not server:
    print("IDE not available")
    exit(1)

# 使用上下文管理器
async with IDEClient(server) as client:
    result = await client.open_diff("/path/to/file.py", new_content)

    if result.accepted:
        print("User accepted the changes")
    elif result.rejected:
        print("User rejected the changes")
    else:
        print(f"Error: {result.error}")
```

## 核心 API

### IDEServerDiscovery

| 方法 | 说明 | 签名 |
|------|------|------|
| `find_server` | 查找可用的 IDE 服务器 | `(workspace_path?, verify_ping?) → ServerInfo?` |
| `cleanup_stale_port_files` | 清理已崩溃 IDE 的端口文件 | `() → int` |

```python
# 精确匹配 workspace
server = await IDEServerDiscovery.find_server(
    workspace_path="/path/to/project",
    verify_ping=True  # 默认 True，验证 nonce
)

# 任意可用服务器
server = await IDEServerDiscovery.find_server()

# 环境变量强制端口（测试用）
import os
os.environ["LETTA_IDE_SERVER_PORT"] = "8123"
```

### IDEClient

| 方法 | 说明 | 签名 |
|------|------|------|
| `ping` | 健康检查与身份验证 | `() → dict` |
| `open_diff` | 打开 diff 视图并等待用户操作 | `(file_path, new_content, timeout?) → DiffResult` |
| `close_diff` | 关闭 diff 视图 | `(file_path) → None` |
| `get_open_files` | 获取所有打开的文件 | `() → list[OpenFileInfo]` |
| `get_active_editor` | 获取当前激活的编辑器信息 | `() → ActiveEditorInfo?` |
| `get_selection` | 获取当前选中的文本 | `() → SelectionInfo?` |

```python
async with IDEClient(server_info) as client:
    # Diff 操作（全局串行化）
    result = await client.open_diff(
        "src/main.py",
        "new content here",
        timeout=300.0  # 默认 300 秒
    )

    # 只读操作（可并发）
    files = await client.get_open_files()
    editor = await client.get_active_editor()
    selection = await client.get_selection()
```

### DiffResult

```python
@dataclass
class DiffResult:
    status: DiffStatus  # "accepted" | "rejected" | "error"
    content: str | None = None
    error: str | None = None

    @property
    def accepted(self) -> bool: ...
    @property
    def rejected(self) -> bool: ...
```

### TerminalConfirmation（降级方案）

```python
from jcode_ide import TerminalConfirmation

fallback = TerminalConfirmation()

# 降级使用终端确认
if await fallback.confirm_write("/path/to/file.py", new_content):
    print("User confirmed in terminal")
```

## 常见模式

### 模式 1：IDE 可用时使用 diff，不可用时降级

```python
from jcode_ide import IDEClient, IDEServerDiscovery, TerminalConfirmation

server = await IDEServerDiscovery.find_server()
if server:
    async with IDEClient(server) as client:
        result = await client.open_diff(path, content)
        return result.accepted
else:
    fallback = TerminalConfirmation()
    return await fallback.confirm_write(path, content)
```

### 模式 2：查询编辑器状态

```python
async with IDEClient(server) as client:
    # 获取打开的文件列表
    for f in await client.get_open_files():
        print(f"{f.path} ({f.language_id})")

    # 获取当前编辑器
    editor = await client.get_active_editor()
    if editor:
        print(f"Line {editor.cursor_position.line}")
```

## 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LETTA_IDE_SERVER_PORT` | 强制使用指定端口 | 无 |

### 协议常量

```python
from jcode_ide.protocol import (
    PROTOCOL_VERSION,  # "1.0.0"
    NAMESPACE,        # "letta.ide.v1"
    DEFAULT_DIFF_TIMEOUT_MS,    # 300_000 (5 min)
    DEFAULT_PING_TIMEOUT_MS,    # 2_000
    DEFAULT_TOOL_TIMEOUT_MS,    # 30_000
)
```

## 最佳实践

### ✓ 推荐：上下文管理器模式

```python
async with IDEClient(info) as client:
    result = await client.open_diff(path, content)
```

### ✗ 避免：即用即弃模式（频繁调用）

```python
# 每次调用都创建新连接
for path in paths:
    client = IDEClient(info)
    await client.open_diff(path, content)  # 性能开销大
```

### ✓ 正确：处理 IDE 不可用情况

```python
server = await IDEServerDiscovery.find_server()
if not server:
    fallback = TerminalConfirmation()
    # 使用降级方案
```

### ✓ 注意：diff 操作是串行化的

`open_diff` 受 `_diff_lock` 保护，多个并发调用会排队等待。
