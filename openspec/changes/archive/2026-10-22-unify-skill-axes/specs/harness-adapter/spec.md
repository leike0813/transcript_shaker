# harness-adapter delta

## MODIFIED Requirements

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

## ADDED Requirements

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
