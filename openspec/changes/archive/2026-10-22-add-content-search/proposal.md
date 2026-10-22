# Proposal

## Why

用户常只记得某次会话里说过的一句话、一个报错文本或一个关键词，却说不清是哪个文件。现有 `--list` 只按路径与修改时间列候选，6 个 harness 全库已有数千个文件，靠时间猜文件名不成立。实测（2026-10-22，本机）：omp 全库 310 个文件 493MB，原始字节扫描 + 3 词项计数 1.8s；adapter 全量解析只有 49MB/s（10.0s / 49MB），codex 全库 3GB 解析需 ~300s。所以按内容定位必须走字节扫描，不能复用解析路径。

## What Changes

- 新增 `scripts/transcript_shaker/search.py`：流式字节扫描（4 MiB 分块，`.zst` / `.zstd` 三选一解压），对查询词项计数，不解析事件流。
- 新增 `--search TEXT`，必须配 `--harness`（本期不做跨 harness 检索）；`kilo-code` 因一个库文件含多个会话而不支持。
- 排序按「命中词项数 → 最弱词项出现次数 → 修改时间 → 路径」，并把歧义算成 `# ambiguous: yes|no` 交给 Agent 判断。
- `SKILL.md` 增加「内容检索」小节与两条分支规则（harness 未知先问用户；命中不唯一先让用户选）；`references/script-usage.md` 承载完整输出契约。
- 新增 `tests/test_search.py`。

## Capabilities

### New Capabilities

（无：复用 `harness-adapter`。）

### Modified Capabilities

- `harness-adapter`: 新增「内容检索（`--search`）」一项要求；`--list` 与转写行为不变。

## Impact

- 新增 `transcript-shaker/scripts/transcript_shaker/search.py`、`transcript-shaker/scripts/tests/test_search.py`。
- 修改 `transcript-shaker/scripts/transcript_shaker/cli.py`（`--search` 参数、与 `--list`/转写互斥、检索分支）。
- 修改 `transcript-shaker/SKILL.md`、`transcript-shaker/references/script-usage.md`。
- 依赖：无新增（只用标准库与既有 zstd 三选一通路）；不落盘、不支持 `--out`。
