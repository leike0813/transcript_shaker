# Design

## Context

见 `proposal.md`。约束：`--list` 只能 stat，不解析内容（6320 个候选）；候选必须与可转写性对齐；识别仍以内容为准。

## Goals / Non-Goals

**Goals:**

- `--list` 不再输出必然不可解析的候选。
- 中断的会话（无助手回复、无正文事件）仍能识别并转写为空日志。

**Non-Goals:**

- 不做内容级预检（逐个 detect 6320 个文件会慢一个数量级）。
- 不改变 kilo-code「只取库中最新会话」的行为。

## Decisions

**1. 跳过规则用 stat 与文件名，不读内容。** 0 字节文件不可能解析；`*.checkpoints.jsonl` 是 command-code 的检查点元数据（`prompt` + `files` 快照，无助手回复），两者都能在不读内容的前提下排除。新增 `Source.skip` 而非在 `find_candidates` 里硬编码 harness 名，便于后续按需扩展。

**2. `--match` 只过滤路径。** 路径里的项目目录名（如 `-Workspace-Code-RiskFlow`）已能区分会话；读内容取标题会违反 stat-only 约束，且对 6320 个候选不可行。

**3. 空会话按「识别 → 0 事件」而不是「报错」。** 与既有 `_looks_like_dsh` + `test_dsh_session_header_alone_is_detected` 一致：会话存在但正文未产生时，输出 `events: 0` 比 `unsupported transcript format` 更准确。grok 无会话头记录，因此用整文件判据（所有记录类型属于 `DIALOG_TYPES`、无 `message`/`payload` 键、至少一条带 grok 专有键）；kimi 用 `metadata` + `protocol_version` 作会话头。

**4. 原逐记录判据保留。** grok 的 `_looks_like_grok` 不动，整文件判据只作为回退，避免带额外键的历史文件回归。

## Risks / Trade-offs

- **整文件判据可能误认**：一个来自未知 harness、只含 `{type, content, prompt_index}` 的文件会判为 grok。风险低于现状（真实 grok 会话被拒），且 grok 的 parse 对该形状产出正确事件。
- **跳过名单随 harness 升级漂移**：新出现的数据副本若被列出又解析失败，按同一模式在 `HARNESS_SOURCES` 加一条 `skip`。
