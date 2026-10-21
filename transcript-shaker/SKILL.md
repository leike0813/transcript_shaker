---
name: transcript-shaker
description: 把 Agent Harness 的本地会话记录（transcript）裁剪转写为一份精炼的 Markdown 日志。当用户要求整理、精炼、导出或"转写"某次 Agent 会话记录（例如 Codex rollout）时使用。
---

# transcript_shaker

## 用途

把一段 Agent 会话的本地 transcript 转成按时间顺序排列的 Markdown 日志：保留用户/助手/系统消息与工具调用，隐藏 thinking，截断冗长的工具输出。只做格式转换与裁剪，不解释、不总结会话内容。

## 输入

- 一个 transcript 文件路径（优先）；或
- 一句模糊描述（如"看看我今天那次 Codex 会话"），此时先按"Codex transcript 定位"找文件。

当前只支持 Codex rollout（`.jsonl` 与 `.jsonl.zst`）。识别不了格式时直接告诉用户尚未支持，不要自行猜测解析方式。

## 输出

一份 Markdown 日志：默认写到 stdout，或按用户要求落到文件（`--out`）。交付时说明输出路径与事件条数。

## 脚本

解析与转写全部由脚本完成，不要手工解析 transcript。

```bash
python3 <skill_dir>/scripts/transcript_shaker/__main__.py <transcript> [--max-chars N] [--out PATH]
```

- `<skill_dir>`：本 `SKILL.md` 所在目录。
- `<transcript>`：文件路径；支持 `~` 展开。
- `--max-chars`：工具结果与 system/developer 消息的截断上限，默认 2000 字符。
- `--out`：输出文件；缺省写 stdout。父目录不存在时自动创建。
- 依赖：只用 Python 标准库，要求 Python ≥3.9。`.jsonl.zst` 需要解压能力，三者任一即可：Python 3.14 `compression.zstd`、`zstandard` 包、`zstd` 命令行。
- 退出码：0 成功；1 文件不存在、不可读、格式无法识别或无法解压（原因写 stderr）。

调用时机：定位到 transcript 文件之后、向用户交付日志之前。

## Codex transcript 定位

1. 根目录：`$CODEX_HOME`，未设置时用 `~/.codex`。
2. 会话文件：`<root>/sessions/YYYY/MM/DD/rollout-<时间戳>-<thread_id>.jsonl`；超过 7 天的文件被压成同名 `.jsonl.zst`。归档会话在 `<root>/archived_sessions/`。
3. 按用户给的时间或项目线索缩小范围（目录就是本地日期，文件名里的时间戳也是本地时间）：

```bash
ls -t "${CODEX_HOME:-$HOME/.codex}"/sessions/*/*/*/rollout-* 2>/dev/null | head -5
```

4. 只有一个候选时直接用；多个候选且无法判断时，列出候选并问用户要哪一个。

## 裁剪与输出规则

- thinking / reasoning 一律不输出。
- 工具结果截断到上限并附 `[... truncated N chars ...]`；命令原文与用户/助手消息保留全文。
- system/developer 消息同样截断到上限。
- 输出结构：会话头（harness、session、源文件、cwd、origin、history 模式、事件计数），其后每个事件一个 `## <序号> · <种类>[ · <标签>][ · <时间戳>]` 小节；工具小节含状态行、命令块与结果块。

## 约束

- 不修改、不移动、不删除原 transcript 文件。
- 不对会话内容做语义判断或总结；用户要摘要时说明这不在本 skill 的职责内。
- 不手工解析 transcript，也不用其它工具重新拼接输出。
- 当前只支持 Codex；其它 harness 的 transcript 直接说明尚未支持，并给出文件路径供后续扩展。
