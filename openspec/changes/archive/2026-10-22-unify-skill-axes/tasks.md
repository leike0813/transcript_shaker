# Tasks

## 1. 资产

- [x] 1.1 新增 `references/script-usage.md`（参数约束、退出码、输出契约、依赖、示例、边界情况、常见错误）
- [x] 1.2 新增 `assets/digest.md`、`assets/digest.yaml`、`assets/handoff.md`、`assets/handoff.yaml`

## 2. 指令

- [x] 2.1 重写 `SKILL.md`：英文 `description`、何时使用、skill 级输入输出契约、三轴表、组合表、脚本参数表 + 示例、附加输出流程、禁止事项、支持范围（原样）、易错点、成功标准、参考资料

## 3. 收口

- [x] 3.1 `pytest` 仍全绿（127 个）
- [x] 3.2 三档 × 两格式转写实测，YAML 可 `safe_load`；四个模版可解析
- [x] 3.3 盲测：只给新 Agent `SKILL.md`，四类请求的模式选择与预期一致
- [x] 3.4 `openspec validate unify-skill-axes --strict` 无 error/warning
- [x] 3.5 `openspec archive unify-skill-axes -y` 归档并更新主 spec
