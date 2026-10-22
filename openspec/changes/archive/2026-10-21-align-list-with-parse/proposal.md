# Proposal

## Why

对 15 个 harness 的 6320 个真实候选逐一跑转写，99 个必然失败：command-code 148 个候选里 74 个是 `*.checkpoints.jsonl`（检查点元数据，不是对话）；codebuddy 14 个、minimax-code 7 个是 0 字节文件；grok 1 个会话因模型未回复（只有 system/user 记录）被拒；kimi-code 3 个会话因只有会话头与配置事件被拒。`--list` 把这些必然失败的路径当作候选列出，Agent 选到后会拿到 `unsupported transcript format`。

## What Changes

- `locate.py`：跳过 0 字节文件与 `Source.skip` 声明的非正文文件名（command-code 的 `*.checkpoints.jsonl`）；新增 `match` 参数做路径子串过滤（不区分大小写）。
- `cli.py`：新增 `--match TEXT`，仅用于 `--list`；转写模式下给出 `--match` 以退出码 2 结束。
- `grok.py`：保留逐记录判据，新增整文件判据——纯对话类型 + grok 专有键（`synthetic_reason`/`prompt_index`/`model_id`/`tool_calls`/`tool_call_id`），使模型未回复的会话可识别并输出 system/user 事件。
- `kimi_code.py`：`metadata`（带 `protocol_version`）也算识别依据，只有会话头与配置事件的空会话输出 0 事件。
- `SKILL.md`：补充 `--match`、command-code 检查点文件、grok/kimi 空会话、0 字节过滤的说明。

## Capabilities

### New Capabilities

（无：复用 `harness-adapter`。）

### Modified Capabilities

- `harness-adapter`: 「候选 transcript 定位」增加跳过规则与 `--match`；「CLI 参数契约」增加 `--match` 互斥；「多 harness 内容识别」增加中断会话仍识别的场景。

## Impact

- 修改 `transcript-shaker/scripts/transcript_shaker/locate.py`、`cli.py`、`adapters/grok.py`、`adapters/kimi_code.py`。
- 修改 `transcript-shaker/SKILL.md`。
- 新增 `scripts/tests/fixtures/grok_partial/`、`scripts/tests/fixtures/kimi_empty/`；`tests/test_locate.py` 与 `tests/test_harness_adapters.py` 追加用例。
- 依赖：无新增。
