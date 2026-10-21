# Proposal

## Why

现在只支持 Codex 一个 harness，用户实际的会话散落在 Claude Code、Qwen、pi/omp、Kimi、DeepSeek Harness 等十几个 harness 里，遇到非 Codex 文件只能报 `unsupported transcript format`。这些 harness 的 transcript 都已在本机实测存在且格式可解析，扩展成本低、收益直接。

## What Changes

- 抽出共享读取层 `adapters/_support.py`：JSONL/zstd 逐行读取、单 JSON 文档读取、正文块提取、epoch 毫秒转 ISO、工具调用与结果的按 id 回填；`codex.py` 改为复用，行为不变。
- 新增 14 个 adapter：claude-code、qwen-code、command-code、codebuddy、gemini-cli、pi、omp、minimax-code、kilo-code、cline、multicoder、grok、kimi-code、deepseek-harness。
- 注册表按「先特异、后通用」的顺序登记 15 个 adapter，识别仍只看文件内容；无法识别时报错并列出全部支持名。
- `render.py` 的 shell 工具集扩充为各 harness 实测的 shell 工具名，使命令原文不再被截断。
- `SKILL.md` 增加支持矩阵：每个 harness 该传哪个文件（glob）及两条约束（子代理文件不自动拼接；kilo 库只取最新会话）。
- 新增 `zstd` 不依赖外部包的解压链沿用既有实现，后缀从 `.zst` 扩到 `.zst`/`.zstd`；SQLite 用标准库 `sqlite3` 只读打开。零新增依赖。

## Capabilities

### New Capabilities

（无：复用已归档的 `harness-adapter`。）

### Modified Capabilities

- `harness-adapter`: 识别范围从 1 个 harness 扩到 15 个，并新增各 harness 的解析要求（工具配对、thinking 丢弃、噪音记录跳过、多会话数据库的取用规则）。

## Impact

- `transcript-shaker/scripts/transcript_shaker/adapters/`：新增 `_support.py` 与 13 个 adapter 模块（pi 系三合一），`codex.py` 改为复用共享工具，`__init__.py` 登记 15 个 adapter。
- `transcript-shaker/scripts/transcript_shaker/render.py`：`SHELL_TOOLS` 扩充。
- `transcript-shaker/SKILL.md`：新增支持矩阵与文件定位约束。
- 测试：新增 `scripts/tests/test_harness_adapters.py` 与每 harness 一份合成 fixture；codex 既有 23 个测试作为重构回归网。
- 依赖：无新增；`.zstd` 解压优先 Python 3.14 `compression.zstd`，其次 `zstandard` 包，最后 `zstd` 命令行。
