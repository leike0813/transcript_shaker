# Tasks

## 1. 共享读取层与 codex 重构

- [x] 1.1 新建 `adapters/_support.py`：`as_text` / `text_blocks` / `join_argv` / `iso_from_ms` / `message_event` / `tool_event` / `iter_lines`（`.zst`/`.zstd`）/ `iter_records` / `head_records` / `load_json_doc` / `ResultBinder`
- [x] 1.2 `head_records`、`load_json_doc` 增加二进制探测，避免按行解析 SQLite 等二进制文件
- [x] 1.3 `codex.py` 改为复用 `_support`（删除本地副本，工具结果回填改用 `ResultBinder`）

验证：`uv run --project "/home/joshua/.ar" --locked -- python -m pytest transcript-shaker/scripts/tests -q` 全绿；kilo 库 detect 耗时从 48 秒降到 0.15 秒

## 2. 识别注册表

- [x] 2.1 `adapters/__init__.py` 按「先特异、后通用」登记 15 个 adapter
- [x] 2.2 每个 adapter 的 `detect` 只读内容、捕获 `OSError`/`RuntimeError`/`sqlite3.Error`

验证：14 个真实文件各自 `detect_adapter(...).name` 命中预期 harness，无串台

## 3. Claude 系与命令式 JSONL

- [x] 3.1 `claude_code.py`：`text`/`tool_use`/`tool_result`，thinking 与 `api-request*`/`attachment` 丢弃
- [x] 3.2 `command_code.py`：`message.content` 块 + `session` 头
- [x] 3.3 `codebuddy.py`：`input_text`/`output_text`、`function_call`/`function_call_result`、`summary` 丢弃
- [x] 3.4 `qwen_code.py`：无 `type` 的 parts、`functionCall`/`functionResponse`、`provenance` 过滤、`thought` 标记排除

## 4. pi 系 JSONL

- [x] 4.1 `pi_family.py`：共用消息映射（user/developer/assistant/toolResult）
- [x] 4.2 `PiAdapter`、`OmpAdapter` 会话头与 title 槽
- [x] 4.3 `MinimaxAdapter`：`{message_id, turn_id, message}` 外壳 + `manifest.json` 元数据

## 5. 单文档 JSON

- [x] 5.1 `gemini_cli.py`：`user`/`gemini`/`info`/`error`，内联 `toolCalls[].result`
- [x] 5.2 `cline.py`：`system_prompt` + 消息块 + 同目录 `<id>.json` 的 cwd/started
- [x] 5.3 `multicoder.py`：`parts` 的 `text`/`reasoning`/`tool-*`

## 6. 事件型与 SQLite

- [x] 6.1 `grok.py`：只读 `chat_history.jsonl`，`summary.json` 取元数据
- [x] 6.2 `kimi_code.py`：只消费 `agent.message.appended`，`state.json` 取 cwd/createdAt（毫秒或 ISO）
- [x] 6.3 `deepseek_harness.py`：`session`/`user/message`/`assistant/message`/`tool/call`/`tool/result`
- [x] 6.4 `kilo_code.py`：只读 URI 连库，只解析最新会话，`part` 的 `text`/`tool`

## 7. 渲染与文档

- [x] 7.1 `render.py` 的 `SHELL_TOOLS` 覆盖各 harness 实测 shell 工具名
- [x] 7.2 `SKILL.md` 增加 15 行支持矩阵（传哪个文件）+ 子代理文件单独传入 + kilo 只取最新会话
- [x] 7.3 `model.py` 的 `Session.history` 注释说明只有 codex 使用
- [x] 7.4 `cli.py` 输出前把孤立代理项替换掉（部分 dsh 会话的 JSON 带 `\ud83e` 之类，直接写会抛 `UnicodeEncodeError`）

验证：对真实 Claude/Qwen/Kimi 文件运行 CLI，`run_shell_command`/`bash`/`Bash` 的命令块不再出现截断标记

## 8. 测试

- [x] 8.1 每 harness 一份合成 fixture（含 user/assistant/tool+结果/thinking marker/该 harness 特有噪音）
- [x] 8.2 `test_harness_adapters.py`：表驱动断言 detect 名、事件序列、thinking 不泄漏、工具结果配对、会话元数据
- [x] 8.3 针对性用例：omp `custom/tool_execution_start` 不翻倍、codebuddy `summary` 不产消息、grok 合成 user 跳过、dsh replace 消息跳过、dsh 压缩与未压缩结果一致、dsh 只有会话头也能识别、kilo 只输出最新会话

验证：`uv run --project "/home/joshua/.ar" --locked -- python -m pytest transcript-shaker/scripts/tests -q` → 97 passed

## 9. 端到端与收口

- [x] 9.1 14 个真实文件各跑一次 `--out`，检查表头 harness 名、事件数 > 0、无 reasoning 泄漏
- [x] 9.2 codex 回归：`history: paginated`、`exec_command` 小节、截断标记仍在
- [x] 9.3 冒烟：非 transcript 文件（`AGENTS.md`）退出码 1 且 stderr 含 `unsupported transcript format` 与完整 15 个支持名
- [x] 9.4 `openspec validate add-more-harness-adapters --strict` 无 error/warning
