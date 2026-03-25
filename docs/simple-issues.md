## S-001 统一 fallback.py 中的异常处理
- 状态：todo
- 文件：src/jcode_ide/fallback.py
- 原因：`confirm_delete` 的 `except Exception` 吞异常且只打日志，`confirm_write` 的 `except Exception` 也是吞异常。应考虑是否需要向上传播或提供更细粒度控制
- 本轮目标：决定是否保留静默处理，或改为可选异常模式
- 范围：1 file
- 风险：low
- 测试：已有测试覆盖两种路径

## S-002 重构 _LoggerProxy._render 的错误处理
- 状态：todo
- 文件：src/jcode_ide/_logging.py
- 原因：message.format 失败后退路是拼接，但拼接逻辑在 `_render` 内部，导致重复代码。此外 `bind` 部分未格式化可能泄漏非字符串类型
- 本轮目标：提取拼接逻辑为辅助函数，为 `bind` 添加 repr 处理
- 范围：1 file
- 风险：low
- 测试：需要补充 format 失败的单元测试

## S-003 修复 IDEServerDiscovery.PORT_FILE_DIR 硬编码
- 状态：todo
- 文件：src/jcode_ide/discovery.py
- 原因：`PORT_FILE_DIR` 硬编码为 `~/.tmp/letta/ide`，不利于测试和配置
- 本轮目标：允许通过环境变量或构造参数覆盖
- 范围：1 file
- 风险：low
- 测试：已有测试用例，调整后需验证

## S-004 优化 ServerInfo.base_url 为属性
- 状态：todo
- 文件：src/jcode_ide/discovery.py, src/jcode_ide/client.py
- 原因：`base_url` 已是 `@property`，但 `IDEServerDiscovery._ping_server` 和 `client.py` 中多次构造相同 URL。应封装为单一入口
- 本轮目标：确认 `base_url` 使用位置，确保全部使用属性而非手动拼接
- 范围：2 files
- 风险：low
- 测试：现有测试覆盖

## S-005 改进 _is_process_alive 的类型安全
- 状态：todo
- 文件：src/jcode_ide/discovery.py
- 原因：`_is_process_alive(pid: int | None)` 接收 `None` 但立即检查并返回 `False`，类型签名可收紧为 `int` 并在调用处处理 `None`
- 本轮目标：修改签名，调用处显式处理 `None`（已有 `_scan_port_files` 已过滤）
- 范围：1 file
- 风险：low
- 测试：现有测试

## S-006 优化 _parse_port_file 的异常处理
- 状态：todo
- 文件：src/jcode_ide/discovery.py
- 原因：`_parse_port_file` 在 `KeyError` 时抛出，但调用方 `_load_server_by_port` 和 `_scan_port_files` 捕获 `KeyError` 并吞掉。应使用更明确的异常（如 `PortFileParseError`）便于区分
- 本轮目标：创建自定义异常 `PortFileParseError`，替换抛出与捕获逻辑
- 范围：1 file
- 风险：low
- 测试：补充解析失败场景

## S-007 简化 _LoggerProxy 的方法签名
- 状态：todo
- 文件：src/jcode_ide/_logging.py
- 原因：所有日志方法都带 `bind` 和 `exc_info`，但大多数调用不使用 `bind`。可改为仅保留必要参数，或提供重载
- 本轮目标：评估 `bind` 使用频率，若使用少则移至关键字参数
- 范围：1 file
- 风险：low（内部 API）
- 测试：补充调用场景

## S-008 避免重复计算路径
- 状态：todo
- 文件：src/jcode_ide/discovery.py
- 原因：`_load_server_by_port` 中遍历文件后调用 `_parse_port_file`，但 `_parse_port_file` 内部又 `read_text`。可考虑缓存或提前读取
- 本轮目标：确认性能影响，若频繁调用则优化
- 范围：1 file
- 风险：low
- 测试：现有测试

## S-009 修复 _ping_server 的 nonce 比较逻辑
- 状态：todo
- 文件：src/jcode_ide/discovery.py
- 原因：`_ping_server` 中 `nonce = result.get("result", {}).get("nonce")`，但 ping 响应结构可能变化。应显式检查 `result` 存在性并处理缺失情况
- 本轮目标：添加 `result` 检查，缺失时返回 `False` 并记录
- 范围：1 file
- 风险：low
- 测试：补充 ping 失败场景

## S-010 统一 client.py 中的超时单位
- 状态：todo
- 文件：src/jcode_ide/client.py
- 原因：`DEFAULT_DIFF_TIMEOUT_MS` 等以毫秒定义，但传递给 httpx 时除以 1000 转为秒。应在调用层统一转换，避免散落在多处
- 本轮目标：在 `_call_tool` 入口统一转换，调用方传毫秒
- 范围：1 file
- 风险：low
- 测试：现有测试

## S-011 优化 DiffResult 的默认值
- 状态：todo
- 文件：src/jcode_ide/client.py
- 原因：`DiffResult(content=None, error=None)`，但 `status="error"` 时 `error` 应有值。可添加 `__post_init__` 确保一致性
- 本轮目标：添加 `__post_init__` 检查，`status="error"` 时若 `error` 为空则设为默认消息
- 范围：1 file
- 风险：low
- 测试：补充构造测试

## S-012 避免重复的 Position/Range 构造
- 状态：todo
- 文件：src/jcode_ide/client.py
- 原因：`get_active_editor` 和 `get_selection` 中都有嵌套的 `get` 链，可提取为辅助函数
- 本轮目标：提取 `_parse_position` 和 `_parse_range` 辅助函数
- 范围：1 file
- 风险：low
- 测试：现有测试覆盖
