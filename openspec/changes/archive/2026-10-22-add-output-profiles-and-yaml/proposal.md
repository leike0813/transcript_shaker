# Proposal

## Why

现在只有一种输出：默认截断的 Markdown 全过程转写。用户需要三种新形态——完整原文（不截断）、给人和 Agent 读的精简过程（工具只留类型）、以及提要形态（digest，去掉过程转写的冗余而不是生成交接文档）——以及机器可解析的 YAML。当前 `render_markdown` 把截断写死在渲染里，没有档位与格式维度。

## What Changes

- 新增 `yamlout.py`：零依赖 YAML 序列化，输出可被 `yaml.safe_load` 读回。
- `render.py`：截断上移为 `prepare_events`；抽出 `meta_lines` / `events_line`；新增 `render_yaml`。
- 新增 `digest.py`：`compact` 与 `digest` 共用的精简输出（消息按角色分档截断、工具折叠为类型 + 次数、shell 命令保留前 160 字）。
- `cli.py`：新增 `--format markdown|yaml`、`--profile default|full|compact|digest`；`--max-chars` 只允许 `default`；两个新参数不可与 `--list` 同用。
- `SKILL.md`：新增「输出档位」小节与 digest 文档契约（Agent 起草），并写明交接文档只在用户要求交接时另行撰写。

## Capabilities

### New Capabilities

（无：复用 `harness-adapter`。）

### Modified Capabilities

- `harness-adapter`: 新增「输出档位」与「YAML 输出」两条 Requirement；「工具结果截断」「消息保留策略」「Markdown 输出格式」补上档位作用域；「CLI 参数契约」加入 `--format` / `--profile`。

## Impact

- 修改 `scripts/transcript_shaker/render.py`、`cli.py`；新增 `yamlout.py`、`digest.py`。
- 新增 `tests/test_digest.py`；`tests/test_render.py`、`tests/test_cli.py` 追加用例。
- 修改 `SKILL.md`。
- 依赖：无新增（仍只用标准库）。
