# Design

## Context

见 `proposal.md`。约束：脚本只能确定性产出 transcript；摘要与交接必须由 Agent 写；skill 包只用标准库。

## Goals / Non-Goals

**Goals:**

- 三个轴正交、可自由组合，组合时脚本调用次数有确定规则。
- Agent 只读 SKILL.md 就能选定压缩档位、是否需要附加文档、用哪种格式。
- 附加文档结构由模版固定，不再依赖散文描述。

**Non-Goals:**

- 不给脚本增加摘要 / 交接参数：脚本无法确定性产出这两类文档，加参数只会得到空枚举值。

## Decisions

**1. 附加输出轴不进 CLI。** digest / handoff 的内容由 Agent 生成，脚本能做的只有产出素材。非 compact 档位要附加输出时多跑一次 `--profile compact`，用两次调用表达「交付物 + 素材」，比在脚本里拼两种文档简单且不引入占位符。

**2. 模版按格式各存一份，共四个文件。** 若只存 Markdown 模版再让 Agent 推导 YAML 结构，每次都要做一次键名设计；四个文件把结构钉死，也让「格式轴同时作用于附加文档」可验证。

**3. 支持矩阵只留在 SKILL.md。** `references/script-usage.md` 用一节指向它，避免两张表分头漂移。

**4. compact 的语义加工止于删减与合并。** 脚本产出保持逐事件编号、条数不变；Agent 只能做减法，不能补写脚本已丢弃的工具参数与结果。

## Risks / Trade-offs

- **四个模版的维护成本**：模版是纯文本，结构变化时需同步改 Markdown 与 YAML 两份；由 spec 的「附加文档跟随格式轴」场景兜底。
- **SKILL.md 变长**：轴表与组合表占篇幅，但换来「读一遍就能选模式」；脚本细节已移出到 `references/`。
