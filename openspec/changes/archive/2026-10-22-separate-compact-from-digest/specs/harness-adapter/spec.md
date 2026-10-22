# harness-adapter delta

## REMOVED Requirements

### Requirement: 输出档位

**Reason**: 该 Requirement 把 `compact` 与 `digest` 定义为同一套脚本输出，与事实不符——`compact` 是压缩后的 transcript，`digest` 是 Agent 依据 transcript 写的摘要，脚本无法确定性产出。`--profile digest` 也因此在实现中移除。

**Migration**: 由「输出档位与摘要」取代：`--profile` 只接受 `default` / `full` / `compact`；摘要改为 Agent 动作，素材取自 `--profile compact`。

## ADDED Requirements

### Requirement: 输出档位（三档）

系统 SHALL 提供 `--profile` 三个档位：`default`（默认，工具结果与 system 消息按 `--max-chars` 截断）、`full`（任何字段都不截断）、`compact`（消息按角色分档截断：system 300 字符、user 与 assistant 1200 字符；工具只保留名字与状态，shell 类工具另保留命令前 160 字符，不输出结果块）。三个档位 SHALL 输出同一文档类型 `# Transcript`、逐事件编号，事件条数 SHALL 与 `default` 一致；`compact` MUST NOT 合并或删除事件。`full` 与 `compact` 的会话头 SHALL 含 `- profile: <档位>` 行，`default` MUST NOT 含。

#### Scenario: default 档位行为不变

- **WHEN** 用户不带 `--profile` 运行转写
- **THEN** 输出与既有 Markdown 契约一致，工具结果与 system 消息按 `--max-chars` 截断，会话头不含 `- profile:` 行

#### Scenario: full 档位不截断

- **WHEN** 用户运行 `--profile full`
- **THEN** 输出不含任何 `[... truncated N chars ...]` 标记，命令、结果、system 消息保持原文

#### Scenario: compact 是压缩后的 transcript

- **WHEN** 用户运行 `--profile compact`
- **THEN** 首行仍为 `# Transcript · <harness> · <开始时间>`，会话头含 `- profile: compact`，事件条数与 `default` 相同，每个工具事件仍有独立小节

#### Scenario: compact 的消息分档截断

- **WHEN** `compact` 档位下 system 消息超过 300 字符、user 或 assistant 消息超过 1200 字符
- **THEN** 分别截断到 300 与 1200 字符并附 `[... truncated N chars ...]` 标记

#### Scenario: compact 的工具内容只剩类型

- **WHEN** `compact` 档位转写工具事件
- **THEN** 小节只含工具名与状态，shell 类工具附命令前 160 字符，结果与非 shell 工具的调用内容不出现

### Requirement: 摘要与交接由 Agent 撰写

系统 MUST NOT 提供摘要档位。摘要（digest）SHALL 是 Agent 依据某个档位的 transcript 起草的独立文档：主题行 + 会话 / 源 / 规模三行元数据 + 目标 / 过程要点 / 结论与产出 / 遗留问题四节，全文不超过 40 行，MUST NOT 与被压缩的 transcript 混为同一输出。交接文档 SHALL 只在用户明确要求交接时撰写，含目标、进展、待决策、建议技能、引用五节，并 SHALL 脱敏敏感信息、按路径引用而非复制原文。

#### Scenario: 摘要由 Agent 起草

- **WHEN** 用户要求摘要或提要
- **THEN** Agent 先运行 `--profile compact` 取素材，再起草 `# Digest · …` 文档（四节、全文不超过 40 行）交付；脚本没有摘要档位，也不因摘要请求自动生成交接文档

#### Scenario: 用户要求交接

- **WHEN** 用户要求把会话交接给下一次会话
- **THEN** Agent 撰写含目标、进展、待决策、建议技能、引用五节的交接文档，敏感信息脱敏，引用按路径而非复制原文

## MODIFIED Requirements

### Requirement: Markdown 输出格式

系统 SHALL 输出固定结构的 Markdown：会话头包含 harness、session、源文件、cwd、origin、history 模式与事件计数，其后每个事件对应一个按序编号的小节，小节标题含种类、标签与时间戳。`compact` 档位 SHALL 使用同一文档类型与同一编号规则，仅在会话头多一行 `- profile: compact`，并省略工具小节的结果块与非 shell 工具的调用块；`compact` MUST NOT 引入独立的 `# Transcript digest` 文档类型。

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

- **WHEN** 用户运行 `--profile compact`
- **THEN** 首行为 `# Transcript · <harness> · <开始时间>`，会话头含 `- profile: compact`，且不出现 `- entries:` 行或 `# Transcript digest` 标题

### Requirement: YAML 输出

系统 SHALL 支持 `--format yaml`，在三个档位下输出可被 YAML 解析器读回的文档；多行文本 SHALL 使用字面块标量，其余字符串 SHALL 按需加双引号以避免被解析成数字、布尔或时间类型。三个档位的顶层键均 SHALL 为 `harness`、`profile`、`session`、`source`、`cwd`、`started`、`origin`、`history`、`events`；`compact` 档位的每个事件 mapping SHALL 省略 `result`，非 shell 工具 SHALL 省略 `call`。空值字段 SHALL 整键省略。

#### Scenario: 默认档位的 YAML

- **WHEN** 用户运行 `--format yaml`
- **THEN** 首键为 `harness`，第二键为 `profile: default`，`events` 为逐事件 mapping 序列，多行结果以 `|-` 块标量呈现

#### Scenario: YAML 类型安全

- **WHEN** 字段值形如 `2026-01-01T00:00:00Z`、`/tmp/x.jsonl` 或含 `: ` 的文本
- **THEN** 该值以双引号形式输出，解析后仍是字符串

#### Scenario: 精简档位的 YAML

- **WHEN** 用户运行 `--profile compact --format yaml`
- **THEN** 输出 `profile: compact` 与逐事件 `events` 序列，工具条目不出现 `result`，非 shell 工具不出现 `call`，事件条数与 `default` 相同

#### Scenario: 空事件流

- **WHEN** 转写的会话没有任何事件
- **THEN** YAML 输出 `events: []` 且不报错

### Requirement: CLI 参数契约

系统 SHALL 把参数用法错误（`--list` 与 transcript/`--max-chars`/`--out`/`--format`/`--profile` 同用、缺少输入、过滤参数（`--harness`/`--since`/`--limit`/`--match`）脱离 `--list`、`--max-chars` 与非 `default` 档位同用、非正整数、非法日期、未知 harness、未知档位（含已移除的 `digest`）或格式）以退出码 2 结束；文件与格式错误 SHALL 以退出码 1 结束；成功 SHALL 以退出码 0 结束。`--profile` 的合法取值 SHALL 只有 `default`、`full`、`compact`。

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

#### Scenario: 不存在的档位

- **WHEN** 用户给出 `--profile digest`
- **THEN** 系统以退出码 2 结束，错误信息列出可用档位 `default`、`full`、`compact`
