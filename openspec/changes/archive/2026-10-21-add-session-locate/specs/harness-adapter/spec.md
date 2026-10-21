# harness-adapter delta

## ADDED Requirements

### Requirement: 候选 transcript 定位

系统 SHALL 提供 `--list` 模式，按每个 harness 的固定目录扫描候选 transcript，只读取路径与修改时间，不解析文件内容；输出 SHALL 为稳定文本：首行 `# candidates: <N>`，其后每行 `<修改时间>\t<harness>\t<绝对路径>`，按修改时间倒序排列。

#### Scenario: 列出全部 harness 的候选

- **WHEN** 用户运行 `--list`
- **THEN** 系统扫描 15 个 harness 的固定目录，输出 `# candidates: N` 与最多 20 行候选

#### Scenario: 过滤候选

- **WHEN** 用户运行 `--list --harness codex --since 2026-10-20 --limit 5`
- **THEN** 只输出 codex 且修改日期不早于 2026-10-20 的候选，最多 5 行

#### Scenario: 无候选

- **WHEN** 扫描目录不存在或没有匹配文件
- **THEN** 系统只输出 `# candidates: 0` 并以退出码 0 结束

#### Scenario: 不读内容

- **WHEN** 候选文件内容为空或不是 transcript
- **THEN** 该文件仍被列出，`--list` 不报格式错误

### Requirement: CLI 参数契约

系统 SHALL 把参数用法错误（`--list` 与 transcript/`--max-chars`/`--out` 同用、缺少输入、过滤参数脱离 `--list`、非正整数、非法日期、未知 harness）以退出码 2 结束；文件与格式错误 SHALL 以退出码 1 结束；成功 SHALL 以退出码 0 结束。

#### Scenario: 互斥参数

- **WHEN** 用户同时给出 transcript 路径与 `--list`
- **THEN** 系统在 stderr 说明冲突并以退出码 2 结束

#### Scenario: 缺少输入

- **WHEN** 用户既不给 transcript 也不给 `--list`
- **THEN** 系统以退出码 2 结束

#### Scenario: 过滤参数脱离列表

- **WHEN** 用户在转写模式下给出 `--harness`、`--since` 或 `--limit`
- **THEN** 系统以退出码 2 结束

#### Scenario: 非法数值

- **WHEN** `--limit` 或 `--max-chars` 为 0 或负数
- **THEN** 系统以退出码 2 结束
