# Design

## Context

见 `proposal.md`。以下约束直接决定实现形态：

- Codex 同一份 rollout 里，工具调用在 `event_msg/item_completed`（富结构）与 `response_item/custom_tool_call`（模型原始格式）各有一份；0.77.0 及更早的版本则只在 `response_item/function_call` 里有工具调用，`item_completed` 只含消息与 reasoning。
- 本地 435 个样本全部是 `history_mode: "paginated"`，但上游仍保留 legacy 模式与 `codex migrate-rollouts` 迁移命令，legacy 线程在用户历史中真实存在。
- 超过 7 天的 rollout 文件被后台压成 `.jsonl.zst`（Python 3.12/3.13 无标准库 zstd）。
- skill 脚本要能被 Agent 直接执行，不能要求先安装依赖。

## Goals / Non-Goals

**Goals:**

- 一个可运行的 Codex adapter：真实 rollout（含压缩与 legacy）→ 固定 Markdown 日志。
- 一个后续 harness 可复用的最小契约：adapter 接口 + 统一事件模型 + 渲染/裁剪层。
- 脚本零第三方依赖、Python ≥3.9 可直接运行。

**Non-Goals:**

- 不做 transcript 语义分析（摘要、主题识别、问答）。
- 不做文件定位 UI：由 Agent 按 `SKILL.md` 的流程定位文件。
- 不做 Markdown 以外的输出格式。
- 不覆盖本 change 之外的 harness。

## Decisions

**1. 双流择一，而不是合并。** paginated 判据：`item_completed` 中出现过任一工具类 item（`CommandExecution`/`McpToolCall`/`FileChange`/`WebSearch`/`CollabAgentToolCall`/`ImageView`/`SubAgentActivity`/`Extension`）→ 事件流取自 item；否则取自 `response_item`。理由：0.162/0.163 两条流完全镜像，合并必然重复；0.77 及更早的工具只存在于 `response_item`，只读 item 会丢全部工具调用。备选"按 call_id 去重合并"被否决：两流的 ID 体系不同（`custom_tool_call.call_id` vs `CommandExecution.process_id`），去重规则不可靠。

**2. 事件模型分消息与工具两类，工具调用与结果分开承载。** 裁剪策略对二者不同（命令保全文、结果截断），分字段才能各自施加策略。备选"统一成 role/content 的聊天消息"被否决：会把工具结果混进正文字段，渲染时无法区分。

**3. 裁剪放在渲染层。** IR 保留原文，`render_markdown` 时按 `max_chars` 裁剪。理由：同一份 IR 可复用于未来其它输出格式；adapter 只做忠实解析。

**4. 输出格式只做 Markdown。** 项目要求"固定、易被人与 Agent 消费"的格式；先定死一种，CSV/YAML/JSON 留到有真实消费方时再加。

**5. adapter 按内容识别。** 判据是首行可解析出的记录 `type` 属于已知集合。文件名规则随版本变化（`rollout-*.jsonl` 与 `*.jsonl.zst` 并存），内容特征更稳。备选"按扩展名 + 路径前缀匹配"被否决：`CODEX_HOME` 可重定向，路径不固定。

**6. `.zst` 解压三档回退。** Python 3.14 `compression.zstd` → `zstandard` 包 → `zstd -dc` 命令行 → 明确报错。理由：零依赖优先，但不能因缺库而完全无法处理旧会话。

**7. 脚本零安装可执行。** `__main__.py` 把 `scripts/` 插入 `sys.path` 后再导入包，Agent 用 `python3 <skill>/scripts/transcript_shaker/__main__.py` 即可，不要求 cwd 或 `PYTHONPATH`。备选"pip 安装成包"被否决：skill 包不应要求安装步骤。

## Risks / Trade-offs

- **Codex 未来新增 item 类型** → 未知类型默认跳过、不报错；`TOOL_ITEM_TYPES` 与映射表集中在一处，新增类型只需加一行。
- **legacy 模式无官方字段文档** → 依赖本机实测样本（cli 0.77.0）；字段缺失一律按空处理，输出降级但不崩。
- **双流判据依赖"新版本工具一定进 item 流"** → 若未来版本把工具挪回 `response_item`，表现为事件流缺失工具；修正方式是调整判据，禁止改成合并两条流（会重复）。
- **`.zst` 支持依赖环境** → 三档回退覆盖多数情况；都不可用时 CLI 给出明确错误而非静默失败。
- **截断上限固定 2000 字符** → 极长的用户粘贴内容仍会完整保留（按设计），输出可能偏长；可用 `--max-chars` 调整工具结果部分。
