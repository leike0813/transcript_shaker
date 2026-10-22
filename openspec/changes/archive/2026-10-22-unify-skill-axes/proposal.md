# Proposal

## Why

现在的 SKILL.md 把「模式」混成单一的 `--profile`，摘要 / 交接只是被顺带提到的 Agent 动作，没有说明产出、取舍与适用场景；它也无法支撑本 skill 作为常驻辅助技能被按需调用——Agent 读完不知道该选哪个档位、要不要附加文档、格式怎么配合。脚本用法、附加文档结构与模版也都没有落盘位置：参数说明挤在 SKILL.md 里，digest / handoff 的结构只写在散文里，Agent 每次都要重新推断格式。

## What Changes

- 把模式统一为三个正交轴：压缩（`--profile`）、附加输出（无 / digest / handoff）、格式（`--format`），并给出组合时脚本调用次数的规则（非 compact 且要附加输出时多跑一次 `--profile compact` 取素材）。
- `SKILL.md` 重写：`description` 改英文且去掉 harness 枚举；新增「何时使用」触发清单；「输入输出契约」改为 skill 级（自由文本输入，可为空）；轴表写清产出 / 取舍 / 场景；脚本只留参数表与一个示例。
- 新增 `references/script-usage.md`：参数约束、退出码、输出契约、依赖、示例、边界情况、常见错误。
- 新增 `assets/digest.md`、`assets/digest.yaml`、`assets/handoff.md`、`assets/handoff.yaml` 四个模版，`SKILL.md` 要求 Agent 使用。
- `compact` 明确为「脚本确定性产出 + Agent 可做有限语义加工（删减 / 合并条目，不得补写）」。
- Python 代码零改动。

## Capabilities

### New Capabilities

（无。）

### Modified Capabilities

- `harness-adapter`: 「输出档位（三档）」补上 compact 的语义加工边界；「摘要与交接由 Agent 撰写」改为附加输出轴（模版、格式跟随、非 compact 档位取素材规则）；新增「Skill 说明与模版资产」规范 SKILL.md 的结构与资产位置。

## Impact

- 重写 `SKILL.md`；新增 `references/script-usage.md` 与 `assets/` 下四个模版。
- `scripts/` 不变；测试不变（127 个）。
- 无新增依赖。
