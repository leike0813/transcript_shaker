# transcript_shaker （Agent transcript 精炼工具）

## 项目背景

- 本项目是一个 **Agent Skill** 开发项目，并非常规软件工程项目
- 本项目旨在开发一个用于将各类 Agent Harness 产生的 transcript （本地会话记录） 提取为一份精炼的日志型文档，供用户阅读或供其他 Agent 消费

## 目标

- **识别用户意图**：本 Skill 的输入为自由文本。用户可能直接给出一个transcript文件路径，也可能给一个模糊的搜索请求，Agent 应根据用户的输入尝试锁定具体的transcript文件并识别出该文件是哪个Agent Harness的（优先通过用户描述或文件路径判断，若判断不了则解析格式来判断）
- **使用脚本进行transcript过滤**：保留关键消息（system、user、assistant），隐藏thinking，对工具调用进行截断（保留调用命令，截断结果）
- **转写transcript**：用一个固定的、易于被人类和Agent消费的格式（可能是markdown/CSV/yaml等）转写transcript。

## 非目标

- **不尝试去理解和分析transcript**：本skill不包含对transcript本身的语义判断需求，Agent的工作其实到识别用户意图和transcript格式就结束了，剩下的过滤和转写都是确定逻辑（用脚本实现）
- **不一定需要覆盖所有harness**：由于编写harness adapter才是本skill的重点，首期可以覆盖10个左右主流harness

## 你该做什么

- 本文档仅是一份宏观指导，距离可供 Agent 实施的详细指令（SKILL.md）还有不小距离
- 你的任务是，基于目前的宏观指令，生成符合 Open Agent Skills 规范的 Skill 包。本项目 Skill 包的发布目录为 `transcript-shaker` （与 Skill 名称一致）
- 本项目是 Agent Skill 开发项目，其核心是用自然语言（面向LLM的语言风格）编写 Skill 包的核心指令文件 `SKILL.md`，明确 Skill 的输入/输出格式、任务目标/非目标、关键约束、执行流程
- 为实现 Skill 的既定目的，可以适当地编写 Python 脚本，用于在 Skill 执行过程中将一部分确定性的、重复性大的业务逻辑从 Agent LLM 的职责中 offload。尤其是各 Agent Harness 的 transcript 的适配和转换，应该由脚本而非 Agent 处理。不过需要注意，所有编写的脚本都需要在 `SKILL.md` 中显式说明其用途、调用方法和调用时机。

## 你不该做什么

- **避免生成不符合 Open Agent Skills 规范的文件**：Open Agent Skills 规范规定，一个 Skill 包中必须有一个位于包根目录的 `SKILL.md` 作为 Agent 直接读取的核心指令文件。核心指令文件不宜过长。按需执行的补充指令、参考文档等可放在 Skill 包中的 `references` 目录中（需要在 `SKILL.md` 中声明其用途及用法）；Python 脚本放在 Skill 包中的 `scripts` 目录中；其它资产文件可放在 Skill 包中的 `assets` 目录中。
- **避免在 `SKILL.md` 中添加对 Skill 执行没有帮助的信息**: `SKILL.md` 中应仅包含对 Skill 执行具有约束作用或帮助作用的指令。一切面向用户的提示、说明，以及错误的、自相矛盾的、模棱两可的指令均不应该出现在 `SKILL.md`中

## 参考资料

- 需要关于Agent Harness的知识，可以使用 `agent-harness-wiki` MCP工具进行查询
- `references/omp-shake-implementation.md`：oh-my-pi中的 `shake` 功能的分析报告