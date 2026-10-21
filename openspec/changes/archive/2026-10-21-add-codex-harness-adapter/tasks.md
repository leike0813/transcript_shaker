# Tasks

## 1. 核心骨架

- [x] 1.1 新建 `transcript-shaker/scripts/transcript_shaker/` 包目录，写 `model.py` 的 `Event`、`Session` dataclass（字段与 `design.md` 决定 2 一致），验证：`python3 -c "import sys; sys.path.insert(0,'transcript-shaker/scripts'); from transcript_shaker.model import Event, Session; print(Event(kind='message').kind)"` 输出 `message`
- [x] 1.2 写 `adapters/base.py`（`Adapter` 协议）与 `adapters/__init__.py`（`ADAPTERS`、`UnsupportedTranscript`、`detect_adapter`），验证：导入 `detect_adapter` 并对任意不存在格式的 JSON 抛出 `UnsupportedTranscript`
- [x] 1.3 写 `render.py`（`DEFAULT_MAX_CHARS = 2000`、`truncate`、`render_markdown`），实现固定 Markdown 结构与裁剪策略，验证：`test_render.py` 全部通过
- [x] 1.4 写 `cli.py` 与 `__main__.py`（参数、退出码、stderr 文案与 `design.md` 决定 7 一致），验证：无参数运行退出码 2 且打印用法，`--help` 正常输出

## 2. Codex adapter

- [x] 2.1 写 `adapters/codex.py` 的读取层 `_iter_records` 与 `.zst` 三档解压回退，验证：对未压缩与 `.zst` fixture 读取到的记录条数一致
- [x] 2.2 实现 `detect`（内容判据）与两遍解析（session_meta + 模式判定 → 事件输出），验证：`detect_adapter` 在 fixture 上返回 codex adapter，在普通 JSON 上抛 `UnsupportedTranscript`
- [x] 2.3 实现 paginated 流映射表（13 种 item 类型，`Extension`/`Reasoning` 跳过）与 `response_item` developer/system 消息采集，验证：`test_codex_adapter.py` 的 paginated 用例通过，且无重复 assistant 事件
- [x] 2.4 实现 legacy 流映射（`message`、`function_call(_output)`、`custom_tool_call(_output)`、`local_shell_call(_output)`、`web_search_call`、`event_msg` 消息），验证：legacy fixture 的 `function_call` 事件 `result` 等于对应 output，工具名为 `mcp:demo.search`

## 3. Skill 文档与仓库修正

- [x] 3.1 写 `transcript-shaker/SKILL.md`（frontmatter：`name: transcript-shaker` + 两句话 `description`；正文含输入、输出、脚本用法、执行流程、裁剪规则、约束），验证：按文档命令对真实 rollout 跑一次能产出日志
- [x] 3.2 修正 `AGENTS.md` 发布目录一行 `paper-humanizer` → `transcript-shaker`，验证：`grep -n "发布目录" AGENTS.md` 显示 `transcript-shaker`

## 4. 测试

- [x] 4.1 写 `scripts/tests/conftest.py`（把 `scripts/` 插入 `sys.path`）与两份合成 fixture（paginated / legacy），验证：fixture 每行都是合法 JSON 且不含真实用户内容
- [x] 4.2 写 `test_codex_adapter.py`（事件序列、reasoning 不出现、去重、call_id 回填、未知行跳过、detect、`.zst` 等价），验证：`uv run --project "/home/joshua/.ar" --locked -- python -m pytest transcript-shaker/scripts/tests -q` 通过
- [x] 4.3 写 `test_render.py` 与 `test_cli.py`（截断标记与省略量、消息保留策略、Markdown 结构与围栏加长、退出码与 stderr 文案），验证：同上 pytest 命令全绿

## 5. 端到端验证

- [x] 5.1 对真实 paginated rollout（`~/.codex/sessions/2026/10/21/rollout-2026-10-21T17-27-25-01a15dc9-7223-7cb0-8cbd-341f055e0717.jsonl`）运行 CLI 产出 `/tmp/codex-transcript.md`，验证：首行 `# Transcript · codex · ...`、有 user/assistant 小节、工具小节为 `exec_command`、结果块含 `[... truncated N chars ...]`、全文检索不到 reasoning 文本
- [x] 5.2 对真实 legacy 压缩样本（`~/.codex/sessions/2025/12/30/rollout-2025-12-30T23-30-57-019b6fe2-4333-7022-884b-a6dd8ef93818.jsonl.zst`）产出 `/tmp/codex-transcript-legacy.md`，验证：`- history: legacy` 且出现 `mcp:propmtx.recall` 工具小节
- [x] 5.3 运行 `openspec validate add-codex-harness-adapter --strict`，验证：无 error 与 warning

## Workflow follow-up

- change 归档在用户评审通过后执行（`openspec archive add-codex-harness-adapter`）。
