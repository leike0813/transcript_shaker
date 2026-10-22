# Proposal

## Why

上一个 change（`add-output-profiles-and-yaml`）把 `compact` 与 `digest` 定义成同一套脚本输出，前提是错的：`compact` 仍然是 transcript，只是比 `default` 压得更狠；`digest` 是基于 transcript 的摘要，脚本不可能确定性产出。结果是 `--profile digest` 实际吐出的是压缩后的 transcript，且文档类型被改成 `# Transcript digest`，与「compact 是 transcript」的语义冲突。

## What Changes

- `render.py`：新增 `prepare_compact`（消息按角色分档截断、工具只留名字与状态、shell 命令前 160 字符、丢弃结果），删除 `digest.py` 与 `# Transcript digest` 文档类型；`render_markdown` 增加 `profile` 参数，仅 `full` / `compact` 写入 `- profile:` 行。
- `cli.py`：`--profile` 只接受 `default` / `full` / `compact`；`compact` 走同一渲染管线，`--max-chars` 仍只属于 `default`。
- `SKILL.md`：档位说明改为「三档都是同一文档类型」；摘要与交接合并为 Agent 动作小节，写明素材用 `--profile compact`、digest 四节 ≤40 行、交接五节与脱敏。
- 测试：`test_digest.py` → `test_compact.py`；CLI 用例改为断言 compact 仍是 `# Transcript`、`--profile digest` 被拒。

## Capabilities

### New Capabilities

（无。）

### Modified Capabilities

- `harness-adapter`: 「输出档位」整体重写为三档 + 文档类型不变；新增「摘要与交接由 Agent 撰写」；「Markdown 输出格式」去掉 `# Transcript digest` 文档类型；「YAML 输出」三个档位统一顶层键 `events`；「CLI 参数契约」明确 `--profile digest` 为非法取值。

## Impact

- 修改 `scripts/transcript_shaker/render.py`、`cli.py`、`SKILL.md`、`tests/test_cli.py`；删除 `digest.py` 与 `test_digest.py`；新增 `tests/test_compact.py`。
- 输出契约变化：`compact` 的 Markdown/YAML 由 digest 形状改回 transcript 形状（`# Transcript`、`events` 逐条）；`--profile digest` 不再存在。
- 依赖：无新增。
