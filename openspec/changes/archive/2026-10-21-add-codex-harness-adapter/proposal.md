# Proposal

## Why

`transcript_shaker` 要把各 Agent Harness 的本地会话记录裁剪转写成可读日志，而 Codex 是它要覆盖的第一个 harness。仓库目前没有任何代码：没有 transcript 解析、没有裁剪规则、没有输出格式。没有第一个 adapter，就没有统一事件契约，后续 harness 也无从接入。

## What Changes

- 新增 harness adapter 契约：adapter 负责把某个 harness 的本地 transcript 解析成统一事件流（用户/助手/系统消息 + 工具调用），并能按文件内容自动识别所属 harness。
- 新增 Codex adapter：解析 Codex rollout JSONL（`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`，含 `.jsonl.zst` 压缩），同时覆盖 paginated 与 legacy 两种历史模式。
- 新增裁剪规则：隐藏 thinking；工具结果与 system/developer 消息按上限截断并标注省略字符数；工具命令原文与用户/助手消息保留全文。
- 新增固定 Markdown 输出格式与命令行入口 `transcript_shaker <transcript>`。
- 新增 skill 包 `transcript-shaker/`（`SKILL.md` + `scripts/`），并修正 `AGENTS.md` 中写错的发布目录名。

## Capabilities

### New Capabilities
- `harness-adapter`: 把某个 Agent Harness 的本地 transcript 识别、解析、裁剪并转写为固定的 Markdown 日志

### Modified Capabilities

## Impact

- 新增 `transcript-shaker/`：`SKILL.md`、`scripts/transcript_shaker/`（事件模型、渲染、CLI、adapters）、`scripts/tests/`。
- 新增 OpenSpec change `openspec/changes/add-codex-harness-adapter/`。
- 修改 `AGENTS.md` 一行（发布目录笔误）。
- 运行时零第三方依赖：脚本只用标准库；`.zst` 解压依次尝试 Python 3.14 `compression.zstd`、`zstandard` 包、`zstd` 命令行。
