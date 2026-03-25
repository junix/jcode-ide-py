## C-001 统一错误处理策略
- 状态：todo
- 文件：src/jcode_ide/client.py, src/jcode_ide/discovery.py, src/jcode_ide/fallback.py
- 原因：当前混合使用：异常（`IDEError` 层级）、返回特殊值（`DiffResult(status="error")`）、静默失败（`_LoggerProxy` 内部吞异常）。跨模块不一致导致调用方需记忆每个 API 的行为
- 本轮建议闭环：定义清晰的错误契约：1) 网络/协议层抛异常；2) 业务层（如 diff 被拒）返回带状态的结果；3) 内部工具（日志）可静默但需可配置。更新所有调用方适配
- 范围：cross-module
- 风险：medium（影响调用方）
- 测试：需补充错误场景的集成测试

## C-002 改善可测试性：注入与 mock 友好
- 状态：todo
- 文件：src/jcode_ide/discovery.py, src/jcode_ide/client.py
- 原因：`IDEServerDiscovery` 硬编码 `PORT_FILE_DIR`，`_ping_server` 内部创建 `httpx.AsyncClient`，`_is_process_alive` 调用 `os.kill`。这些外部依赖难以 mock，测试需依赖真实文件系统和进程
- 本轮建议闭环：1) 通过参数或依赖注入传递关键依赖；2) 提取外部调用为可替换的接口；3) 为 `client.py` 提供 mock 友好的 HTTP 层抽象
- 范围：cross-module
- 风险：medium（重构接口）
- 测试：重构后补充 mock 测试，减少 e2e 依赖

## C-003 重构超时与重试策略
- 状态：todo
- 文件：src/jcode_ide/protocol.py, src/jcode_ide/client.py, src/jcode_ide/discovery.py
- 原因：超时值分散在 `protocol.py` 和各方法中，单位转换（ms->s）重复出现，且无重试机制。当网络抖动时 `open_diff` 可能失败
- 本轮建议闭环：1) 集中管理超时配置；2) 统一单位处理；3) 为关键操作（ping、diff）添加可配置的重试逻辑；4) 考虑为长期阻塞操作（diff）提供取消机制
- 范围：few files
- 风险：medium（时序敏感）
- 测试：需补充超时和重试场景
