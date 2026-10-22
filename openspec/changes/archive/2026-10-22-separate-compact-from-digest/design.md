# Design

## Context

见 `proposal.md`。约束：脚本只能产出确定性结果，因此脚本能做的只有「同一份 transcript 的不同裁剪程度」；摘要必须由 Agent 写。

## Goals / Non-Goals

**Goals:**

- `compact` 与 `default` / `full` 输出同一文档类型 `# Transcript`，逐事件编号，只压内容。
- 摘要（digest）明确为 Agent 交付物，脚本不提供该档位。

**Non-Goals:**

- 不让脚本生成摘要或交接文档正文。
- 不为 `compact` 保留工具结果、工具参数、折叠计数。

## Decisions

**1. 删掉 `digest.py`，compact 复用 `render_markdown` / `render_yaml`。** 只加一个 `prepare_compact(events)` 预处理步骤，把事件改写成「已压缩」的形态；渲染、编号、头部全部复用。这样「compact 是 transcript」由代码结构保证，不需要第二套文档类型。

**2. `- profile:` 行只在非 default 档位出现。** 默认输出必须逐字节不变（11 个 fixture 校验）；`full` / `compact` 加一行自述，读者才知道手里的文档被裁剪过。

**3. compact 不合并、不删条目。** 合并相邻工具调用属于聚合，是摘要的动作；compact 只压缩每条事件的内容，事件条数与 `default` 一致。

**4. 非 completed 才保留状态。** `- status: completed` 在长会话里逐条重复上百次，是纯噪声；错误/中断状态照常保留。

**5. `--profile digest` 直接移除，不留别名。** 保留别名等于把一个不可能有确定性语义的值挂在 CLI 上，正是本次要消除的混淆。

## Risks / Trade-offs

- **移除 `--profile digest` 是破坏性 CLI 变更**：该 skill 尚未发布，且旧值本身就是错的；`--help` 与 `SKILL.md` 都已列出合法取值。
- **compact 工具小节可能只剩标题行**（非 shell 工具既无命令也无结果）：这是「只留名字」的直接后果，需要细节时改用 `default` / `full`。
