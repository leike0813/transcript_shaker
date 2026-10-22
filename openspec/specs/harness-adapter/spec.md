# harness-adapter Specification

## Purpose
把某个 Agent Harness 的本地 transcript 识别、解析、裁剪并转写为固定的 Markdown 日志，供人与其它 Agent 阅读。

## Requirements

### Requirement: Transcript 格式识别

系统 SHALL 依据文件内容（而非仅文件名）判定 transcript 所属 harness，并在无法判定时报错，错误信息 SHALL 列出当前已支持的 harness。

#### Scenario: 识别 Codex rollout

- **WHEN** 传入含 `session_meta`、`response_item` 或 `event_msg` 记录的 JSONL 文件
- **THEN** 系统判定为 codex 并用 Codex adapter 解析

#### Scenario: 无法识别格式

- **WHEN** 传入不含任何已知记录类型的 JSON 文件
- **THEN** 系统报错并列出已支持 harness，以非 0 退出码结束

### Requirement: Codex rollout 解析

系统 SHALL 解析 Codex rollout 的会话元数据与事件记录，按文件顺序输出统一事件流；同一文件同时存在两种历史模式的数据时 SHALL 只取一种，不得让同一内容出现两次。

#### Scenario: 存在工具类 item

- **WHEN** `event_msg/item_completed` 中出现 `CommandExecution`、`McpToolCall` 等工具类条目
- **THEN** 事件流取自 item 记录，`response_item` 中的同内容不再出现

#### Scenario: 缺少工具类 item

- **WHEN** `item_completed` 中没有任何工具类条目
- **THEN** 事件流取自 `response_item`，`function_call` 与其 `function_call_output` 按 `call_id` 配对

#### Scenario: 未知记录与损坏行

- **WHEN** 文件中存在未知 `type` 或不可解析的行
- **THEN** 系统跳过该行且解析继续进行

### Requirement: 事件归一

系统 SHALL 把解析结果归一为消息事件与工具事件：消息事件含角色（user/assistant/system）、正文与来源时间戳；工具事件含工具名、调用内容、结果与状态。

#### Scenario: 消息与工具并存

- **WHEN** 转换一个含消息与工具调用的会话
- **THEN** 事件序列同时含消息事件与工具事件，工具事件能同时给出调用内容与结果

### Requirement: 隐藏 thinking

系统 SHALL 不输出任何 reasoning/thinking 内容，也不为它生成事件。

#### Scenario: 含 reasoning 的会话

- **WHEN** 会话含 `Reasoning` item 或 `reasoning` response_item
- **THEN** 输出中不出现其文本，事件计数中也没有 thinking 条目

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

### Requirement: 压缩文件与错误处理

系统 SHALL 支持 zstd 压缩的 transcript；文件缺失、不可读或解压能力不可用时 SHALL 给出明确错误并以非 0 退出码结束。

#### Scenario: 压缩文件

- **WHEN** 传入 `.jsonl.zst` 且具备解压能力
- **THEN** 与同内容的未压缩文件产出等价事件流

#### Scenario: 文件缺失

- **WHEN** 传入的路径不存在
- **THEN** 系统报错说明文件不存在，以非 0 退出码结束

### Requirement: 多 harness 内容识别

系统 SHALL 依据文件内容识别 15 个 harness（codex、claude-code、qwen-code、command-code、codebuddy、gemini-cli、pi、omp、minimax-code、kilo-code、cline、multicoder、grok、kimi-code、deepseek-harness），识别顺序 SHALL 保证格式特异的 harness 先于通用格式匹配；无法识别时报错并列出全部支持名。会话在任何正文产生前中断时（只剩会话头、配置事件或未回复的 user 消息），系统 SHALL 仍按该 harness 识别，并输出空事件流。

#### Scenario: 通用格式不抢占特异格式

- **WHEN** 传入 omp 的 JSONL（首条为带 `pad` 的 `title` 记录）或 command-code 的 JSONL（`message.meta` 存在）
- **THEN** 系统判定为 omp 与 command-code，而不是判为 pi 或 pi 系其它 harness

#### Scenario: 二进制库与压缩转录

- **WHEN** 传入 SQLite 数据库文件或 `.jsonl.zstd`
- **THEN** JSONL adapter 快速跳过（不逐行解析二进制内容），由对应的 SQLite / 压缩流 adapter 识别

#### Scenario: 中断的会话仍被识别

- **WHEN** grok 的 `chat_history.jsonl` 只有 `system` 与 `user` 记录（模型未回复），或 kimi 的 `wire.jsonl` 只有 `metadata` 与 `config.update`
- **THEN** 系统分别判定为 grok 与 kimi-code，转写结果的事件计数为 0 或仅含已有消息，不报 `unsupported transcript format`

#### Scenario: 无法识别格式

- **WHEN** 传入的文件不含任何已注册 harness 的记录特征
- **THEN** 系统以非 0 退出码结束，错误信息包含 `unsupported transcript format` 与完整支持列表

### Requirement: Claude 系与命令式 JSONL 解析

对 claude-code、command-code、codebuddy、qwen-code，系统 SHALL 把工具调用的结果按调用 id 回填到对应工具事件，SHALL 丢弃 thinking/reasoning 内容，且 DID NOT 允许同一次工具调用产生两个事件。

#### Scenario: 工具调用与结果配对

- **WHEN** 文件先出现 `tool_use` / `function_call` / `functionCall` 记录，随后出现带同一 id 的结果记录
- **THEN** 事件流里该工具事件的结果字段为结果记录的正文，状态反映成功或错误

#### Scenario: 思考内容不输出

- **WHEN** 记录含 `thinking`、`reasoning`、`think` 块或独立的推理记录
- **THEN** 这些内容不出现在任何事件的任何字段

#### Scenario: 摘要副本不重复正文

- **WHEN** codebuddy 文件含 `summary` 记录（首条 user 消息的截断副本）
- **THEN** 该记录不产生消息事件

### Requirement: pi 系 JSONL 解析

对 pi、omp、minimax-code，系统 SHALL 只消费 `message` 记录，丢弃 `title`、`model_change`、`thinking_level_change`、`custom`、`session_init` 等非对话记录；`toolCall` 与 `toolResult` SHALL 按调用 id 配对。

#### Scenario: 工具执行轨迹不翻倍

- **WHEN** omp 文件含 `type=="custom"` 且 `customType=="tool_execution_start"` 的记录
- **THEN** 该记录不产生工具事件，工具数量与该会话实际调用次数一致

#### Scenario: 工具结果为错误

- **WHEN** `toolResult` 的 `isError` 为真
- **THEN** 对应工具事件的状态为错误，正文为结果文本

### Requirement: 单文档 JSON 解析

对 gemini-cli、cline、multicoder，系统 SHALL 读取单个 JSON 文档并按其 `messages[]` 顺序输出事件；正文为空的消息 SHALL 不产生事件。

#### Scenario: 内联工具结果

- **WHEN** gemini-cli 的 `gemini` 消息内 `toolCalls[]` 自带 `result`
- **THEN** 系统为每个 toolCall 产出一个工具事件，调用参数与结果取自该 toolCall

#### Scenario: 系统提示词只在开头出现

- **WHEN** cline 文档含非空 `system_prompt`
- **THEN** 事件流最前出现一条 system 消息，且后续消息不重复该内容

### Requirement: 事件型与 SQLite 解析

对 grok、kimi-code、deepseek-harness、kilo-code，系统 SHALL 只消费承载正文的记录：grok 的 `chat_history.jsonl`、kimi 的 `agent.message.appended`、deepseek-harness 的 `*/message` 与 `tool/call`、kilo 的 `message` 与 `part` 表；索引流、增量流与重复副本 SHALL 不计入事件。

#### Scenario: 增量与事件副本不重复

- **WHEN** deepseek-harness 会话同时含 `assistant/chunk`、`text-chunks`、`reasoning-chunks` 与 `assistant/message`
- **THEN** 同一段正文只出现一次

#### Scenario: 多会话数据库

- **WHEN** kilo 数据库内存在多个会话
- **THEN** 系统只解析 `time_created` 最新的一个会话，并在会话元数据中写入该会话 id

### Requirement: 候选 transcript 定位

系统 SHALL 提供 `--list` 模式，按每个 harness 的固定目录扫描候选 transcript，只读取路径、文件大小与修改时间，不解析文件内容；系统 SHALL 跳过 0 字节文件与该 harness 声明为非正文的文件名（当前为 command-code 的 `*.checkpoints.jsonl`），并 SHALL 支持按路径子串过滤（不区分大小写）。输出 SHALL 为稳定文本：首行 `# candidates: <N>`，其后每行 `<修改时间>\t<harness>\t<绝对路径>`，按修改时间倒序排列；`N` SHALL 等于过滤后实际输出的行数。

#### Scenario: 列出全部 harness 的候选

- **WHEN** 用户运行 `--list`
- **THEN** 系统扫描 15 个 harness 的固定目录，输出 `# candidates: N` 与最多 20 行候选

#### Scenario: 过滤候选

- **WHEN** 用户运行 `--list --harness codex --since 2026-10-20 --limit 5`
- **THEN** 只输出 codex 且修改日期不早于 2026-10-20 的候选，最多 5 行

#### Scenario: 按路径子串过滤

- **WHEN** 用户运行 `--list --match riskflow`
- **THEN** 只输出路径包含 `riskflow`（不区分大小写）的候选，计数行与实际行数一致

#### Scenario: 跳过必然不可解析的候选

- **WHEN** 扫描目录中存在 0 字节文件或 `*.checkpoints.jsonl`
- **THEN** 这些文件不出现在输出中，其它非 transcript 内容仍被列出（`--list` 不报格式错误）

#### Scenario: 不读内容

- **WHEN** 候选文件是二进制库或内容不是 transcript
- **THEN** 该文件仍被列出，`--list` 不报格式错误；能否解析由转写时判定

#### Scenario: 无候选

- **WHEN** 扫描目录不存在或没有匹配文件
- **THEN** 系统只输出 `# candidates: 0` 并以退出码 0 结束

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

### Requirement: 输出档位（三档）

系统 SHALL 提供 `--profile` 三个压缩档位：`default`（默认，工具结果与 system 消息按 `--max-chars` 截断）、`full`（任何字段都不截断）、`compact`（消息按角色分档截断，工具只保留名字与状态）。三个档位 SHALL 输出同一文档类型 `# Transcript`、逐事件编号，事件条数 SHALL 与 `default` 一致；`compact` 的脚本产出 MUST NOT 合并或删除事件。系统 MUST NOT 提供摘要或交接档位。`full` 与 `compact` 的会话头 SHALL 含 `- profile: <档位>` 行，`default` MUST NOT 含。

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

#### Scenario: compact 允许删除无关条目

- **WHEN** Agent 交付 `compact` 档位的 transcript 而用户只关心其中一部分
- **THEN** Agent MAY 删除与用户问题无关的条目或合并同类条目，MUST NOT 补写脚本已丢弃的工具参数与结果，也 MUST NOT 新增结论或评价

### Requirement: 摘要与交接由 Agent 撰写

系统 MUST NOT 提供摘要或交接档位。digest 与 handoff SHALL 是 Agent 在某个压缩档位的 transcript 之上撰写的独立文档；`handoff` SHALL 只在用户明确要求交接时撰写。附加文档的格式 SHALL 与 `--format` 一致，结构 SHALL 来自 skill 包 `assets/` 下的对应模版（`.md` / `.yaml`），Agent MUST NOT 自创结构。digest SHALL 为四节且全文不超过 40 行；handoff SHALL 为五节并 SHALL 脱敏敏感信息、按路径引用而非复制原文。当压缩档位不是 `compact` 时，Agent SHALL 额外以 `--profile compact` 取素材，不得把交付档位的全文用于撰写附加文档。

#### Scenario: 摘要由 Agent 起草

- **WHEN** 用户要求摘要或提要
- **THEN** Agent 先取得 `compact` 素材，再按 `assets/digest.md` 或 `assets/digest.yaml` 起草四节、全文不超过 40 行的文档交付；脚本不产出该文档

#### Scenario: 用户要求交接

- **WHEN** 用户要求把会话交接给下一次会话
- **THEN** Agent 按 `assets/handoff.md` 或 `assets/handoff.yaml` 撰写五节文档，敏感信息脱敏，引用按路径而非复制原文

#### Scenario: 非 compact 档位下的附加输出

- **WHEN** 用户选择 `default` 或 `full` 压缩并同时要求 digest 或 handoff
- **THEN** Agent 交付该档位的 transcript，并额外运行一次 `--profile compact` 取素材来写附加文档

#### Scenario: 附加文档跟随格式轴

- **WHEN** 用户选择 `--format yaml` 并要求 digest 或 handoff
- **THEN** 附加文档使用 `assets/` 下对应的 YAML 模版，顶层键与模版一致，且能被 YAML 解析器读回

### Requirement: Skill 说明与模版资产

`SKILL.md` 的 frontmatter `description` SHALL 使用英文，只描述「做什么」与「何时使用」，MUST NOT 枚举 harness 名称。`SKILL.md` SHALL 说明压缩、附加输出、格式三个正交轴的产出、取舍与适用场景，并 SHALL 给出三者组合时脚本的调用次数；`SKILL.md` 的输入输出契约 SHALL 描述本 skill 的输入（自由文本，可以为空）与输出，MUST NOT 把脚本的参数契约当作 skill 契约。`SKILL.md` SHALL 只列脚本参数含义与一个调用示例，完整用法 SHALL 由 `references/script-usage.md` 承载。`assets/` SHALL 提供 digest 与 handoff 的 Markdown 与 YAML 四个模版，`SKILL.md` SHALL 要求 Agent 使用它们。

#### Scenario: 读 SKILL.md 后能选定模式

- **WHEN** Agent 只读 `SKILL.md` 就遇到「导出完整命令与结果」「给这段会话写摘要」「交接给下一次会话」「给程序解析」四类请求
- **THEN** 分别选定 `full` + 无附加 + markdown、`compact` 素材 + digest、`compact` 素材 + handoff、以及 `yaml` 格式，无需再读其他文件

#### Scenario: 脚本说明分居两处

- **WHEN** Agent 需要某个参数的完整约束或退出码含义
- **THEN** `SKILL.md` 给出指向 `references/script-usage.md` 的索引，后者给出完整手册，两者不重复维护同一张支持矩阵

#### Scenario: 模版缺失或残留占位符

- **WHEN** Agent 写完 digest 或 handoff
- **THEN** 文档结构与 `assets/` 对应模版一致，且不残留 `<...>` 占位符
