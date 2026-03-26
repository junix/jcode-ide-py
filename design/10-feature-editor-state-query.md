# 编辑器状态查询 API

## 概述

IDEClient 提供只读 API 查询编辑器状态：`get_open_files()`、`get_active_editor()` 和 `get_selection()`，用于获取 IDE 上下文信息。

**分数**: 75/100
- 业务核心度: 12/20 - 辅助功能
- 用户影响: 20/25 - 上下文感知编辑
- 代码投入: 13/15 - 实现完整
- 架构支撑度: 10/15 - 独立功能
- 独特性与复杂度: 20/25 - IDE 状态映射

## 概览

```mermaid
graph TB
    get_open_files -->|files[]| OpenFileInfo
    get_active_editor -->|editor?| ActiveEditorInfo
    get_selection -->|selection?| SelectionInfo

    OpenFileInfo --> path
    OpenFileInfo --> language_id
    OpenFileInfo --> is_dirty

    ActiveEditorInfo --> file_path
    ActiveEditorInfo --> cursor_position[Position: line, character]
    ActiveEditorInfo --> visible_range[Range: start, end]

    SelectionInfo --> file_path
    SelectionInfo --> range
    SelectionInfo --> text
```

## 设计意图

### 解决的问题

- Agent 需要知道用户在哪个文件工作
- 获取当前编辑器光标位置
- 获取用户选中的文本

### 设计决策

- **只读操作**: 不修改 IDE 状态
- **可并发**: 不受 `_diff_lock` 限制
- **返回 Optional**: 编辑器可能没有打开的文件

## 契约

| API | 返回类型 | 说明 |
|-----|----------|------|
| `get_open_files` | `list[OpenFileInfo]` | 所有打开的文件 |
| `get_active_editor` | `ActiveEditorInfo?` | 当前激活的编辑器 |
| `get_selection` | `SelectionInfo?` | 当前选中的文本 |

### 数据类型

```python
# client.py:46-77
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
```

## API 参考

```python
# client.py:156-162
async def get_open_files(self) -> list[OpenFileInfo]:
    response = await self._call_tool(ToolNames.GET_OPEN_FILES, {}, timeout=DEFAULT_TOOL_TIMEOUT_MS / 1000)
    files = response.get("files", [])
    return [
        OpenFileInfo(
            path=file_info["path"],
            language_id=file_info.get("languageId", ""),
            is_dirty=file_info.get("isDirty", False)
        )
        for file_info in files
    ]

# client.py:164-180
async def get_active_editor(self) -> ActiveEditorInfo | None:
    response = await self._call_tool(ToolNames.GET_ACTIVE_EDITOR, {}, timeout=DEFAULT_TOOL_TIMEOUT_MS / 1000)
    if not response.get("hasActiveEditor"):
        return None
    # ... parse cursor and visible range
    return ActiveEditorInfo(...)

# client.py:182-196
async def get_selection(self) -> SelectionInfo | None:
    response = await self._call_tool(ToolNames.GET_SELECTION, {}, timeout=DEFAULT_TOOL_TIMEOUT_MS / 1000)
    if not response.get("hasSelection"):
        return None
    # ... parse range and text
    return SelectionInfo(...)
```

## 集成矩阵

| 依赖 | 接口语义 | 失败策略 |
|------|----------|----------|
| `ToolNames.GET_OPEN_FILES` | 获取文件列表 | 超时抛出 `IDEConnectionError` |
| `ToolNames.GET_ACTIVE_EDITOR` | 获取编辑器信息 | 超时抛出 `IDEConnectionError` |
| `ToolNames.GET_SELECTION` | 获取选中文本 | 超时抛出 `IDEConnectionError` |

## 使用示例

```python
async with IDEClient(server) as client:
    # 获取所有打开的文件
    files = await client.get_open_files()
    for f in files:
        print(f"{f.path} ({f.language_id}, dirty={f.is_dirty})")

    # 获取当前编辑器
    editor = await client.get_active_editor()
    if editor:
        print(f"Editing: {editor.file_path}")
        print(f"Cursor: line {editor.cursor_position.line}, char {editor.cursor_position.character}")
        print(f"Visible: {editor.visible_range.start.line}-{editor.visible_range.end.line}")

    # 获取选中文本
    selection = await client.get_selection()
    if selection and selection.text:
        print(f"Selected: {selection.text[:50]}...")
```

## 限制与权衡

- **隐私设置**: `content_sharing_disabled` 可能阻止获取选中文本
- **IDE 依赖**: 需要 IDE 扩展支持
- **不返回内容**: `get_open_files` 不返回文件内容
- **时序问题**: 获取时刻的状态可能已变化

## 相关特性

- [04-feature-mcp-protocol.md](04-feature-mcp-protocol.md) - MCP 协议定义
- [05-feature-diff-view.md](05-feature-diff-view.md) - Diff 操作
- [03-api-and-usage.md](03-api-and-usage.md) - API 使用指南
