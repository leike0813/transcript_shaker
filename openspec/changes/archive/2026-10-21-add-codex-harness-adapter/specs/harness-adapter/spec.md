# Spec Delta

## Purpose

把某个 Agent Harness 的本地 transcript 识别、解析、裁剪并转写为固定的 Markdown 日志，供人与其它 Agent 阅读。

## ADDED Requirements

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

系统 SHALL 保留工具调用的命令原文，并把工具结果截断到指定上限（默认 2000 字符），在截断处标注被省略的字符数。

#### Scenario: 结果超限

- **WHEN** 工具结果长度超过上限
- **THEN** 输出只含前 N 字符并附 `[... truncated M chars ...]` 标记

#### Scenario: 结果未超限

- **WHEN** 工具结果长度不超过上限
- **THEN** 输出完整结果且无截断标记

### Requirement: 消息保留策略

系统 SHALL 完整保留用户与助手消息正文，并按与工具结果相同的上限截断 system/developer 消息，截断处同样标注省略量。

#### Scenario: 超长消息

- **WHEN** 用户消息长度超过上限
- **THEN** 输出仍包含完整正文

#### Scenario: 超长系统消息

- **WHEN** system 消息长度超过上限
- **THEN** 输出被截断并带有省略标记

### Requirement: Markdown 输出格式

系统 SHALL 输出固定结构的 Markdown：会话头包含 harness、session、源文件、cwd、origin、history 模式与事件计数，其后每个事件对应一个按序编号的小节，小节标题含种类、标签与时间戳。

#### Scenario: 渲染会话

- **WHEN** 转换含消息与工具调用的会话
- **THEN** 首行为 `# Transcript · <harness> · <开始时间>`，且每个事件对应一个 `## <序号> · <种类>` 小节

#### Scenario: 工具小节内容

- **WHEN** 事件为工具调用
- **THEN** 小节含状态行、命令块与结果块

#### Scenario: 围栏安全

- **WHEN** 正文包含连续反引号
- **THEN** 围栏自动加长，不破坏 Markdown 结构

### Requirement: 压缩文件与错误处理

系统 SHALL 支持 zstd 压缩的 transcript；文件缺失、不可读或解压能力不可用时 SHALL 给出明确错误并以非 0 退出码结束。

#### Scenario: 压缩文件

- **WHEN** 传入 `.jsonl.zst` 且具备解压能力
- **THEN** 与同内容的未压缩文件产出等价事件流

#### Scenario: 文件缺失

- **WHEN** 传入的路径不存在
- **THEN** 系统报错说明文件不存在，以非 0 退出码结束
