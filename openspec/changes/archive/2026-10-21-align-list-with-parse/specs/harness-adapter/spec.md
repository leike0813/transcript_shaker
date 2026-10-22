# harness-adapter delta

## MODIFIED Requirements

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

系统 SHALL 把参数用法错误（`--list` 与 transcript/`--max-chars`/`--out` 同用、缺少输入、过滤参数（`--harness`/`--since`/`--limit`/`--match`）脱离 `--list`、非正整数、非法日期、未知 harness）以退出码 2 结束；文件与格式错误 SHALL 以退出码 1 结束；成功 SHALL 以退出码 0 结束。

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
