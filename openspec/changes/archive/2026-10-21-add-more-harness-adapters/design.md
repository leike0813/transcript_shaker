# Design

## Context

14 个 harness 的本地 transcript 在同一台机器上共存，格式差异集中在四处：存储形态（JSONL / zstd 压缩 JSONL / 单个 JSON 文档 / SQLite）、正文载体（`message.content` / `parts` / 独立事件）、工具调用回填方式（id 配对 / 内联结果 / 独立记录），以及夹杂的非对话记录（thinking、请求快照、流式增量、UI 状态）。

已实测的分布：

| 形态 | harness |
|---|---|
| JSONL，一条记录一轮对话 | claude-code、qwen-code、command-code、codebuddy、pi、omp、minimax-code、grok、kimi-code |
| 单个 JSON 文档 | gemini-cli、cline、multicoder |
| SQLite | kilo-code |
| zstd 压缩 JSONL | deepseek-harness（codex 同族） |

Codex 已有实现把读取、事件构造、id 回填写在自己的模块里；继续复制 14 份会让同一段逻辑长 15 个变体。

## Decisions

**1. 共享 `_support.py`，不复制 15 份辅助函数。** 读取（`iter_records` / `iter_lines` / `load_json_doc`）、正文提取（`text_blocks`）、事件构造（`message_event` / `tool_event`）、毫秒转 ISO（`iso_from_ms`）、id 回填（`ResultBinder`）只有一份实现。`codex.py` 改为复用，现有测试即行为回归网。

**2. 识别仍只看内容 + 固定优先级。** 注册顺序（codex → kimi → dsh → codebuddy → command-code → omp → minimax → pi → claude → qwen → grok → gemini → cline → multicoder → kilo）让特异判据先于宽判据，例如 command-code 的 `message.meta` 先于 pi 的 `type=="message"`、omp 的 `title` 槽先于 pi 的 `type=="session"`。禁止退化成按路径判定：路径随用户的 home 布局漂移，内容不会。

**3. detect 阶段做二进制探测。** 一次实测暴露：kilo 的 1 GB SQLite 库会让前面 13 个 JSONL adapter 各按行解析一遍（48 秒）。因此 `head_records` 与 `load_json_doc` 在读之前探测前 8 KB 是否含 NUL 字节，是则直接判定非本格式；kilo 解析从 48 秒降到 0.15 秒，同时避免把任意二进制当 JSONL 解析。

**4. `.zstd` 并入既有解压链。** 顺序为 Python 3.14 `compression.zstd` → `zstandard` 包 → `zstd` 命令行；三者都不可用时报错并让 CLI 非 0 退出，其余 14 个 adapter 不受影响。

**5. 多会话 SQLite 库只解析最新会话。** kilo 库有 1656 个会话、8 万个 part；全部输出会串台，也无法在 Markdown 里表达会话边界。取 `time_created` 最新的一个会话，并在 `Session.session_id` 写明是哪一个；其它会话需要单独导出。

**6. 子代理文件不自动拼接。** 各 harness 的子代理 transcript 是独立文件（Claude 的 `subagents/agent-*.jsonl`、omp 的 `<会话>/<Agent>.jsonl`、Kimi 的 `agents/agent-*/wire.jsonl`、dsh 的独立子会话目录）。自动合并需要跨文件事件排序与归属标注，属于另一件事；`SKILL.md` 明确要求用户单独传入。

**7. thinking 一律丢弃。** 各 harness 的推理内容明文程度不同，且对阅读会话史没有价值；统一丢弃可让输出与 harness 无关。

**8. 事件型日志按 type 白名单消费。** deepseek-harness 有 24 种事件、kimi wire 有 30 余种，其中大量是流式增量与索引。用白名单（`user/message`、`assistant/message`、`tool/call`、`tool/result`；`agent.message.appended`）而非黑名单，新版本新增的事件类型默认不进入事件流。

## Risks

- **上游格式随版本漂移。** 缓解：未知记录类型一律跳过；正文为空的消息不产出事件；`detect` 只依赖少数稳定字段，判断失败时由 CLI 报错而不是产出空文档。
- **宽判据误判。** 已用真实文件逐一验证 14 个 harness 的表头名与事件数；若后续出现串台，以真实文件结果为准调整优先级或增加更特异的字段，不改为按路径判定。
- **kilo 库结构变化。** `detect` 要求 `session`、`message`、`part` 三表同时存在；缺失时不识别为 kilo，避免静默产出空文档。
- **大文件端到端耗时。** 解析是单遍流式；zstd 走命令行时会整文件解压，但只对压缩过的会话生效，不影响其余格式。
