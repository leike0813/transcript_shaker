# harness-adapter delta

## ADDED Requirements

### Requirement: 输出档位

系统 SHALL 提供 `--profile` 四个档位：`default`（默认，按 `--max-chars` 截断）、`full`（不截断）、`compact`（精简过程）、`digest`（供 Agent 起草 digest 文档）。`compact` 与 `digest` SHALL 共用同一套确定性精简输出，两者产出的差异仅限自述档位的字段；Agent 对 `compact` 的输出 MAY 再删减条目后交付，但 MUST NOT 补写内容；Agent MUST 依据 `digest` 的输出总结并起草 digest 文档（主题行 + 会话 / 源 / 规模三行元数据 + 目标 / 过程要点 / 结论与产出 / 遗留问题四节，全文不超过 40 行），MUST NOT 直接交付该输出。交接文档 SHALL 只在用户明确要求交接时撰写，此时 Agent MUST 生成含目标、进展、待决策、建议技能、引用五节的文档，并 SHALL 脱敏敏感信息、按路径引用而非复制原文。

#### Scenario: default 档位行为不变

- **WHEN** 用户不带 `--profile` 运行转写
- **THEN** 输出与既有 Markdown 契约一致，工具结果与 system 消息按 `--max-chars` 截断

#### Scenario: full 档位不截断

- **WHEN** 用户运行 `--profile full`
- **THEN** 输出不含任何 `[... truncated N chars ...]` 标记，命令、结果、system 消息保持原文

#### Scenario: compact 与 digest 共用精简输出

- **WHEN** 用户分别运行 `--profile compact` 与 `--profile digest`
- **THEN** 两者的脚本产出除档位自述字段外完全相同，且工具条目只含工具类型、次数与 shell 类工具的命令前 160 字符

#### Scenario: compact 的 Agent 后处理

- **WHEN** 用户要求精简过程记录
- **THEN** Agent 交付脚本输出或删除其中与问题无关的条目，不新增结论或评价

#### Scenario: digest 的 Agent 后处理

- **WHEN** 用户要求摘要或提要
- **THEN** Agent 先运行脚本取得精简输出，再据其起草 digest 文档；交付物中不出现脚本的 `# Transcript digest` 原文，也不因此自动生成交接文档

#### Scenario: 用户要求交接

- **WHEN** 用户要求把会话交接给下一次会话
- **THEN** Agent 撰写含目标、进展、待决策、建议技能、引用五节的交接文档，敏感信息脱敏，引用按路径而非复制原文

### Requirement: YAML 输出

系统 SHALL 支持 `--format yaml`，在四个档位下输出可被 YAML 解析器读回的文档；多行文本 SHALL 使用字面块标量，其余字符串 SHALL 按需加双引号以避免被解析成数字、布尔或时间类型。`default` / `full` 档位的顶层键 SHALL 为 `harness`、`profile`、`session`、`source`、`cwd`、`started`、`origin`、`history`、`events`；`compact` / `digest` 档位 SHALL 为 `harness`、`profile`、`session`、`source`、`cwd`、`started`、`origin`、`history`、`event_count`、`entries`。空值字段 SHALL 整键省略。

#### Scenario: 默认档位的 YAML

- **WHEN** 用户运行 `--format yaml`
- **THEN** 首键为 `harness`，第二键为 `profile: default`，`events` 为逐事件 mapping 序列，多行结果以 `|-` 块标量呈现

#### Scenario: YAML 类型安全

- **WHEN** 字段值形如 `2026-01-01T00:00:00Z`、`/tmp/x.jsonl` 或含 `: ` 的文本
- **THEN** 该值以双引号形式输出，解析后仍是字符串

#### Scenario: 精简档位的 YAML

- **WHEN** 用户运行 `--profile compact --format yaml`
- **THEN** 输出含 `event_count` 与 `entries`，工具条目不出现 `call`（非 shell）与 `result`，其中 `count` 为整数

#### Scenario: 空事件流

- **WHEN** 转写的会话没有任何事件
- **THEN** YAML 输出 `events: []`（或 `entries: []`）且不报错

## MODIFIED Requirements

### Requirement: 工具结果截断

系统 SHALL 保留工具调用的命令原文，并把工具结果截断到指定上限（默认 2000 字符），在截断处标注被省略的字符数；上限为 0 时 SHALL 不截断（`--profile full`）；`compact` / `digest` 档位按「输出档位」的精简规则处理，不适用本条。

#### Scenario: 结果超限

- **WHEN** 工具结果长度超过上限
- **THEN** 输出只含前 N 字符并附 `[... truncated M chars ...]` 标记

#### Scenario: 结果未超限

- **WHEN** 工具结果长度不超过上限
- **THEN** 输出完整结果且无截断标记

#### Scenario: 上限为 0

- **WHEN** 用户运行 `--profile full`
- **THEN** 工具结果完整输出，不带截断标记

### Requirement: 消息保留策略

系统 SHALL 完整保留用户与助手消息正文，并按与工具结果相同的上限截断 system/developer 消息，截断处同样标注省略量；上限为 0（`--profile full`）时 SHALL 不截断；`compact` / `digest` 档位按「输出档位」的分档上限（system 300、user/assistant 1200）处理。

#### Scenario: 超长消息

- **WHEN** 用户消息长度超过上限
- **THEN** 输出仍包含完整正文

#### Scenario: 超长系统消息

- **WHEN** system 消息长度超过上限
- **THEN** 输出被截断并带有省略标记

#### Scenario: full 档位的长消息

- **WHEN** 用户运行 `--profile full` 且 system 消息超长
- **THEN** 输出完整正文，不带截断标记

### Requirement: Markdown 输出格式

系统 SHALL 输出固定结构的 Markdown：会话头包含 harness、session、源文件、cwd、origin、history 模式与事件计数，其后每个事件对应一个按序编号的小节，小节标题含种类、标签与时间戳。`compact` / `digest` 档位 SHALL 输出独立文档类型 `# Transcript digest`，其头部另含 `profile`、`entries` 行，工具小节不含结果块；其余形状由「输出档位」规定。

#### Scenario: 渲染会话

- **WHEN** 转换含消息与工具调用的会话
- **THEN** 首行为 `# Transcript · <harness> · <开始时间>`，且每个事件对应一个 `## <序号> · <种类>` 小节

#### Scenario: 工具小节内容

- **WHEN** 事件为工具调用
- **THEN** 小节含状态行、命令块与结果块

#### Scenario: 围栏安全

- **WHEN** 正文包含连续反引号
- **THEN** 围栏自动加长，不破坏 Markdown 结构

#### Scenario: 精简档位的标题

- **WHEN** 用户运行 `--profile compact` 或 `--profile digest`
- **THEN** 首行为 `# Transcript digest · <harness> · <开始时间>`，且头部含 `- profile:` 与 `- entries:` 行

### Requirement: CLI 参数契约

系统 SHALL 把参数用法错误（`--list` 与 transcript/`--max-chars`/`--out`/`--format`/`--profile` 同用、缺少输入、过滤参数（`--harness`/`--since`/`--limit`/`--match`）脱离 `--list`、`--max-chars` 与非 `default` 档位同用、非正整数、非法日期、未知 harness、未知档位或格式）以退出码 2 结束；文件与格式错误 SHALL 以退出码 1 结束；成功 SHALL 以退出码 0 结束。

#### Scenario: 互斥参数

- **WHEN** 用户同时给出 transcript 路径与 `--list`
- **THEN** 系统在 stderr 说明冲突并以退出码 2 结束

#### Scenario: 缺少输入

- **WHEN** 用户既不给 transcript 也不给 `--list`
- **THEN** 系统以退出码 2 结束

#### Scenario: 过滤参数脱离列表

- **WHEN** 用户在转写模式下给出 `--harness`、`--since`、`--limit` 或 `--match`
- **THEN** 系统以退出码 2 结束

#### Scenario: 非法数值

- **WHEN** `--limit` 或 `--max-chars` 为 0 或负数
- **THEN** 系统以退出码 2 结束

#### Scenario: 截断上限脱离默认档位

- **WHEN** 用户给出 `--max-chars` 且档位不是 `default`
- **THEN** 系统以退出码 2 结束，不产生任何输出

#### Scenario: 档位与格式脱离转写

- **WHEN** 用户在 `--list` 模式下给出 `--profile` 或 `--format`
- **THEN** 系统以退出码 2 结束
