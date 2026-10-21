# Proposal

## Why

15 个 harness 的根目录在本机全部存在，候选 transcript 超过 6000 个；用户常只给“昨天那次”“omp 里那个”这类模糊描述。现状只有 codex 有一段手写 `ls -t` 定位说明，其余 14 个 harness 要 Agent 临场拼 glob，候选取舍不稳定；`SKILL.md` 也缺少 skill-smith 要求的必需章节。

## What Changes

- 新增 `locate.py` 与 `--list` 模式：按 15 个 harness 的固定目录扫描候选，只 stat 不读内容，输出稳定 TSV（`# candidates: N` + `<mtime>\t<harness>\t<path>`，按 mtime 倒序）。
- `--list` 支持 `--harness`（15 个枚举值）、`--limit`（默认 20）、`--since YYYY-MM-DD`；`--list` 与 transcript/`--max-chars`/`--out` 互斥。
- CLI 增加 `--help` 示例；`--max-chars`、`--limit` 要求正整数；参数错误退出码 2。
- 重写 `SKILL.md`：补齐目标、非目标、I/O 契约、禁止事项、执行流程、LLM/脚本职责、易错点、成功标准、参考资料；删除只覆盖 codex 的手工定位段，改为 `--list` 流程。

## Capabilities

### New Capabilities

（无：复用 `harness-adapter`。）

### Modified Capabilities

- `harness-adapter`: 新增“候选 transcript 定位”与“CLI 参数契约”两项要求；转写行为不变。

## Impact

- 新增 `transcript-shaker/scripts/transcript_shaker/locate.py`。
- 修改 `transcript-shaker/scripts/transcript_shaker/cli.py`（双模式参数、校验、示例）。
- 重写 `transcript-shaker/SKILL.md`。
- 新增 `transcript-shaker/scripts/tests/test_locate.py`。
- 依赖：无新增；`--list` 只用标准库。
