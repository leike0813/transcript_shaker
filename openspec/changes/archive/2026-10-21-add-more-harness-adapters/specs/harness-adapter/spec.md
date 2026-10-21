# harness-adapter delta

## ADDED Requirements

### Requirement: 多 harness 内容识别

系统 SHALL 依据文件内容识别 15 个 harness（codex、claude-code、qwen-code、command-code、codebuddy、gemini-cli、pi、omp、minimax-code、kilo-code、cline、multicoder、grok、kimi-code、deepseek-harness），识别顺序 SHALL 保证格式特异的 harness 先于通用格式匹配；无法识别时报错并列出全部支持名。

#### Scenario: 通用格式不抢占特异格式

- **WHEN** 传入 omp 的 JSONL（首条为带 `pad` 的 `title` 记录）或 command-code 的 JSONL（`message.meta` 存在）
- **THEN** 系统判定为 omp 与 command-code，而不是判为 pi 或 pi 系其它 harness

#### Scenario: 二进制库与压缩转录

- **WHEN** 传入 SQLite 数据库文件或 `.jsonl.zstd`
- **THEN** JSONL adapter 快速跳过（不逐行解析二进制内容），由对应的 SQLite / 压缩流 adapter 识别

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
