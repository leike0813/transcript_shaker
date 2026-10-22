# Design

## Context

见 `proposal.md`。约束：Skill 只用标准库（不能 import `yaml`）；`compact` 与 `digest` 必须共用一套确定性输出；交接文档属于用户按需触发的 Agent 动作，不是档位。

## Goals / Non-Goals

**Goals:**

- 一条渲染管线支持 markdown / yaml 两种格式，四个档位。
- `compact` 与 `digest` 的脚本产出字节相同（只差自述字段），交给 Agent 的后续动作不同。

**Non-Goals:**

- 不实现 YAML 解析（只写）。
- 不让脚本生成摘要或交接文档正文（那部分必须由 Agent 写）。

## Decisions

**1. 手写最小 YAML 序列化器，不用 PyYAML。** Skill 声明零依赖；输出只需覆盖 dict / list / str / int。裸标量仅限 `[A-Za-z_][A-Za-z0-9_.-]*`，其余双引号转义——这样时间戳不会被解析成 timestamp、`2026` 不会被解析成 int。多行文本用字面块 `|` / `|-`。

**2. `full` = `max_chars=0`。** `truncate` 对 `limit <= 0` 原样返回，因此 `full` 不需要独立渲染路径，CLI 把 `max_chars` 置 0 即可。

**3. `compact` 与 `digest` 共用一个 `digest_entries`。** 两者只差 header 里的 `profile` 字段；`digest` 与 `compact` 的语义差异落在 `SKILL.md` 的 Agent 职责，不落在脚本。这样「共用一套精简输出」是结构保证，而不是文档约定。

**4. 相邻同键才折叠。** 折叠键为 `(是否工具, tool, call, status)`：连续相同的 `pytest -q` 合成一条 `×N`，不同命令各自成条，消息条目永不折叠。

**5. 档位互斥而非覆盖。** `--max-chars` 只属于 `default`，其它档位给出即退出码 2；避免「传了却被静默忽略」。

## Risks / Trade-offs

- **YAML 手写序列化的边界**：首行带空格、以多个换行结尾的多行文本退回双引号单行形式；用 PyYAML 回读验证覆盖真实 transcript。
- **`compact` 丢弃命令与结果**：需要原文时用 `default` / `full`；`SKILL.md` 易错点已写明。
