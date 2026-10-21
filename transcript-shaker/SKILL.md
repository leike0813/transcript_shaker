---
name: transcript-shaker
description: 把 Agent Harness 的本地会话记录（transcript）列出、裁剪并转写为精炼的 Markdown 日志。当用户要求查找最近的 Agent 会话记录，或整理、精炼、导出、转写某次会话（如 Codex rollout、Claude Code、omp、DeepSeek Harness）时使用。
---

# transcript-shaker

## 目标

把一段 Agent 会话的本地 transcript 转成按时间顺序排列的 Markdown 日志：保留 user/assistant/system 消息与工具调用，隐藏 thinking，截断冗长的工具结果。只做定位、格式转换与裁剪。

## 非目标

- 不解释、总结、评价会话内容。用户要摘要时明确说明超出本 skill 职责。
- 不把子代理/子会话 transcript 拼进主会话；需要时逐个文件运行、分别交付。
- 不为支持范围以外的 harness 现场编写解析逻辑。

## 输入输出契约

输入（二选一）：

- transcript 文件路径（绝对、相对或 `~` 开头）；或
- `--list`，无文件输入，从本机固定的 harness 目录列出候选。

输出：

- 转写：Markdown 写 stdout，或 `--out PATH` 写到文件（父目录自动创建）。
  - 会话头：`# Transcript · <harness> · <开始时间>`，随后列出 harness、session、source、cwd、origin、history、events。
  - 每个事件：`## <序号> · <种类>[ · <工具名>][ · <时间戳>]`；工具事件含 `- status:`、调用块与结果块。
- `--list`：首行 `# candidates: N`；其后每行 `<修改时间>\t<harness>\t<绝对路径>`，按修改时间倒序；无候选时只输出首行。
- 交付时说明输出位置与事件条数（取自 `events:` 行）。

## 禁止事项

- **不得手工解析 transcript，或用其他工具重新拼接输出**。识别、解析、裁剪、渲染一律由脚本完成。
- **不得修改、移动、删除原 transcript 文件**。
- **不得输出 thinking / reasoning 内容**。
- **不得对支持范围以外的 harness 伪造解析结果**；直接说明尚未支持。
- **不得把 `--list` 的候选列表当作转写结果交付**；必须对选中的文件运行转写。

## 执行流程

1. **确定文件**。
   - 用户已给出路径：直接使用。
   - 用户只给描述：运行 `--list`（可加 `--harness`、`--since`、`--limit`），按修改时间、路径中的项目名和文件名时间戳挑选。
   - 唯一合理候选：直接转写。
   - 多个候选无法区分：列出候选（时间、harness、路径）问用户要哪一个，不要猜。
   - 没有候选：说明 `--list` 扫描的是下表目录，请用户给出文件路径。
2. **转写**。运行下面的脚本命令；默认写 stdout，用户要文件时加 `--out`。
3. **交付**。说明输出路径、harness、事件条数；多个文件分别转写、分别说明。脚本退出码非 0 时，把 stderr 原文转述给用户，不要自行修复或改写 transcript。

## LLM 与脚本职责

- LLM 负责：从用户描述推断 harness、时间、项目线索；在候选中做选择或追问；决定输出位置；交付说明。
- 脚本负责：候选扫描、格式识别、解析、thinking 过滤、截断、Markdown 渲染、退出码。
- 不要用 `ls`/`find`/`sed`/`awk` 替代 `--list` 或转写，也不要写临时解析脚本。

## 脚本

```bash
python3 <skill_dir>/scripts/transcript_shaker/__main__.py --list [--harness NAME] [--limit N] [--since YYYY-MM-DD]
python3 <skill_dir>/scripts/transcript_shaker/__main__.py <transcript> [--max-chars N] [--out PATH]
```

- `<skill_dir>`：本 `SKILL.md` 所在目录；脚本可在任意 cwd 运行。
- `--harness` 取值（也是支持范围）：`codex`、`claude-code`、`qwen-code`、`command-code`、`codebuddy`、`gemini-cli`、`pi`、`omp`、`minimax-code`、`kilo-code`、`cline`、`multicoder`、`grok`、`kimi-code`、`deepseek-harness`。
- `--limit`：`--list` 最多输出条数，默认 20。
- `--since`：`--list` 只看修改时间不早于该本地日期的文件。
- `--max-chars`：工具结果与 system/developer 消息的截断上限，默认 2000。
- 退出码：0 成功；1 文件不存在/不可读/格式无法识别/解压失败；2 参数错误。
- 依赖：仅标准库，Python ≥3.9。`.jsonl.zst`/`.jsonl.zstd` 解压三选一：Python 3.14 `compression.zstd`、`zstandard` 包、`zstd` 命令行。`kilo.db` 用标准库 `sqlite3` 只读打开。
- `--help` 输出完整参数与示例。

## 支持范围

下表同时是 `--list` 的扫描范围；用户直接给路径时按“备注”判断。脚本一次只解析传入的那一个文件。

| harness | 传入文件 | 备注 |
|---|---|---|
| codex | `$CODEX_HOME/sessions/*/*/*/rollout-*`（或 `.jsonl.zst`）；归档在 `$CODEX_HOME/archived_sessions/` | 旧版本 rollout 也支持；`CODEX_HOME` 未设置时用 `~/.codex` |
| claude-code | `~/.claude/projects/*/<session-uuid>.jsonl` | `subagents/agent-*.jsonl` 是子代理会话，需单独传入 |
| qwen-code | `~/.qwen/projects/*/chats/<uuid>.jsonl` | 同目录 `<uuid>.runtime.json`、`meta.json` 不是正文 |
| command-code | `~/.commandcode/projects/*/*.jsonl` | `~/.commandcode/sessions/hooks-audit-*.jsonl` 是审计日志，不支持 |
| codebuddy | `~/.codebuddy/projects/*/*.jsonl` | 0 字节文件很常见，跳过 |
| gemini-cli | `~/.gemini/tmp/*/chats/session-*.json` | 同一会话可能有两份副本，按 `sessionId` 取一份 |
| pi | `~/.pi/agent/sessions/*/*.jsonl` | 一个文件一个会话 |
| omp | `~/.omp/agent/sessions/*/*.jsonl` | `<会话>/<Agent>.jsonl` 是子代理会话，需单独传入 |
| minimax-code | `~/.minimax/v2/sessions/*/*/*/*/messages.jsonl` | 会话 id 与开始时间取自同目录 `manifest.json` |
| kilo-code | `~/.local/share/kilo/kilo.db` | 整个库，只取最新的一个会话 |
| cline | `~/.cline/data/sessions/*/*.messages.json` | 同目录 `<id>.json` 提供 cwd 与真实开始时间 |
| multicoder | `~/.multicoder/content/ses_*.json` | 无逐条时间戳 |
| grok | `~/.grok/sessions/*/*/chat_history.jsonl` | 只读这一份；同目录 `updates.jsonl`、`events.jsonl` 是重复流 |
| kimi-code | `~/.kimi-code/sessions/*/session_*/agents/main/wire.jsonl` | `agents/agent-*/wire.jsonl` 是子代理会话，需单独传入 |
| deepseek-harness | `~/.dsh/sessions/*/*/session*.jsonl.zstd` | 子会话是独立目录，需单独传入 |

## 裁剪与输出规则

- thinking / reasoning 一律不输出。
- 工具结果截断到上限并附 `[... truncated N chars ...]`；shell 类工具的命令原文保留全文。
- 非 shell 工具的参数按同一上限截断。
- 用户与助手消息完整保留；system/developer 消息截断到上限。
- 子代理 / 子会话的 transcript 不自动拼接。

## 易错点

- `--list` 只看路径和修改时间，不读内容：0 字节文件、二进制库也会被列出；能否解析以实际运行结果为准。
- codex 超过 7 天的会话被压成 `.jsonl.zst`，修改时间是压缩时间；按会话发生时间挑选时看文件名里的时间戳（本地时间）。
- gemini-cli 同一会话可能有两份副本，任选其一；要按 `sessionId` 判断时读文件内容，不要靠文件名。
- kilo-code 传整个 `kilo.db`，只转写库中最新的会话；要其它会话需先导出。
- claude-code、omp、kimi-code 的子代理文件是独立会话；用户要看完整调用链时逐个运行并分别交付。
- 部分会话含孤立代理项（如 `\ud83e`），脚本已替换，不要为此改动原文件。

## 成功标准

- 交付的 Markdown 首行为 `# Transcript · <harness> · <开始时间>`，harness 与用户描述或 `--list` 结果一致。
- 输出中不含任何 thinking/reasoning 文本；超限的工具结果带 `[... truncated N chars ...]`。
- 用户只给模糊描述时，最终转写的是真实存在的文件，并且在交付说明中给出该路径与事件条数。

## 参考资料

本 skill 不依赖外部 references；参数与示例由脚本 `--help` 提供，支持矩阵与裁剪规则都在本文件内。
