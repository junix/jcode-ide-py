# 功能文档种子生成提示词

你是一名 Staff 级技术写作者/工程师。基于《代码库功能调研》（见 `design/init.md`）的产出，为排名前 {N} 个功能生成简洁但可扩展的文档种子。

“功能”指用户可见能力：通过 CLI、API、SDK、配置或集成入口暴露。优先提供可操作的指导与可运行示例，并给出明确的扩展路径，让后续维护者无需再次调研即可扩充细节。

## 输入
- 调研结果：叙述性总结、排序清单，以及机器可读的 `features[]` 对象
- 代码仓库根路径：{path or URL}
- 文档目录：固定为 `design/`
- 约束：{时间限制、可忽略部分}

## 目标
- 为每个功能产出简洁但可执行的文档种子（stub）
- 文档全部放置在 `design/` 目录下，统一使用编号前缀与固定命名规则（见下文）
- 示例可运行且含导入；H2/H3 层级清晰；先解释再给代码
- 提供明确的扩展指引，便于后续直接深化
- 若存在 MCP 表面（Tools、Resources、Resource Templates、Prompts），需显式点明

## 方法
1. 命名与位置：所有文档写入 `design/` 目录，采用两位数编号前缀 + kebab-case 文件名：`NN-<slug>.md`。
   - 固定前三个文档（无论功能排名与数量）：
     - `00-architecture-overview.md`
     - `01-core-concepts.md`
     - `02-basic-usage.md`
   - 其余功能文档从 `03-` 开始顺延（例如：`03-authentication.md`、`04-server-composition.md` ...），编号稳定且不回收。
2. 将 `features[]` 中的功能映射为 `design/NN-<slug>.md` 页面，确定清晰的标题与 slug（slug 与文件名一致）。
3. 基于 `pitch`、`entry_points`、`access`、`usage_snippet`、`dependencies`、`tests`、`docs`、`limitations`、`open_questions`、`doc_outline` 综合生成文档种子。
4. 保持可扫读与可执行；尽量给出 `path:line` 级引用。
5. 添加“扩展指引（扩展指引）”段落，列出具体的后续补充项与占位符。

## 交付物
- 文档规划总览：设计文档的章节结构与顺序（位于 `design/`）
- 固定前三页：`00-architecture-overview.md`、`01-core-concepts.md`、`02-basic-usage.md`
- 文档种子：每个功能一页，含前言信息与内容骨架
- 机器可读规范块：用于后续自动化（路径、slug、标题、标签、扩展任务）

## 单功能文档模板
按功能排名依次生成 Markdown 文件，使用如下结构：

---
Title: {Feature Name}
Slug: {slug}
Description: {one-line purpose}
Tags: [{tags}]
Audience: {beginner | intermediate | advanced}
Reading Time: {3–6 minutes}
---

## 概览
- 一段话说明该功能能做什么。
- 主要使用表面：CLI/API/SDK/配置；如有 MCP 表面（Tools/Resources/Resource Templates/Prompts）需注明。
- 代码位置：如 `src/path/file.py:line`。

## 何时使用
- 典型适用场景。
- 常见陷阱与快速建议。

## 快速开始
- 先决条件。
- 最小可运行示例（≤15 行）或命令序列（含导入/CLI）。

## 关键 API / CLI
- 用户首先调用的标识符/命令清单。
- 每项一行简述，并给出 `path:line` 引用。

## 集成与交互
- 依赖项、相关功能，以及如何组合使用。

## 限制
- 已知约束与注意事项。

## 扩展指引（扩展指引）
- 后续可增加的内容：性能、安全、错误处理、高级用法、迁移说明。
- 需引用或扩展的测试：提供 `tests/...:line`。
- 需要补充的流程/架构图。
- 需要确认的开放问题。

## 参考
- 代码引用、关键测试与相关文档页面。

---

## 文档规划总览
请给出 `design/` 目录下页面的组织方案：
- 分类：按用户意图分组（如：入门、核心功能、集成、参考）
- 顺序：固定前三页为架构/概念/基础使用，其后按功能排名与依赖关系排序
- 文件名与 slug：两位编号前缀 + kebab-case，稳定且可预测
- 示例结构（可按实际功能调整）：
  - `design/00-architecture-overview.md`
  - `design/01-core-concepts.md`
  - `design/02-basic-usage.md`
  - `design/03-authentication.md`
  - `design/04-server-composition.md`
  - `design/05-proxy-servers.md`
  - `design/06-openapi-integration.md`
  - `design/07-client-transports.md`
  - `design/08-middleware-system.md`
  - `design/09-tool-transformations.md`
  - `design/10-deployment.md`

## 输出格式
1) 面向人类的摘要
- 4–6 句话说明如何基于调研结果推导出本次文档集
- 分类清单、页面顺序与简要理由

2) 文档种子清单（简明）
- 每个文档列出：`path`、`slug`、`title`、1–2 句摘要，以及将包含的初始 H2/H3 目录（路径一律位于 `design/` 且使用 `NN-<slug>.md`）

3) 机器可读规范块
```
repo: {repo}
generated_at: {ISO8601}
docs:
  - feature_name: string
    rank: number
    path: string               # 例如：design/03-{slug}.md
    slug: string               # kebab-case（与文件名中 {slug} 一致）
    index: number              # 文件编号（两位数），前三页固定为 0、1、2，功能页从 3 起
    title: string
    description: string
    tags: [string]
    audience: string
    example: |                 # ≤15 行，可运行
      ...
    references:
      code: ["path:line", ...]
      tests: ["path:line", ...]
      docs: ["path", ...]
    limitations: [string]
    expansion_tasks:           # 后续可直接执行的具体 TODO
      - short actionable item
```

## 约定
- 单页控制在 ≤400 字的正文 + 1 个最小示例
- 所有文件放在 `design/` 目录，文件名采用两位编号前缀 + kebab-case
- 前三页固定为：`00-architecture-overview.md`、`01-core-concepts.md`、`02-basic-usage.md`
- 尽量提供 `path:line` 引用
- 避免模糊描述；优先以测试/示例为证据
- 用语清晰、祈使、关注“用户如何做”

## 质量核对（逐页）
- 标题具体、面向行动
- 示例可直接运行（含导入/CLI）
- 至少 3 处 `path:line` 级引用（代码/测试）
- 限制明确
- “扩展指引”列出 3–6 条具体后续项
- 导航标题与 slug 清晰稳定
