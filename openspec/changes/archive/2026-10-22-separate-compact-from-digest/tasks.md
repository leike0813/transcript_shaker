# Tasks

## 1. 代码

- [x] 1.1 `render.py`：新增 `prepare_compact`；`render_markdown` 增加 `profile` 参数（仅非 default 写 `- profile:` 行）
- [x] 1.2 `cli.py`：`--profile` 收为 `default` / `full` / `compact`，`compact` 走同一渲染管线；删除 `DIGEST_PROFILES`
- [x] 1.3 删除 `digest.py` 与 `# Transcript digest` 文档类型

## 2. 测试

- [x] 2.1 删除 `test_digest.py`，新增 `test_compact.py`（分档截断、命令只留前 160 字、逐事件编号、YAML 形状、default 无 profile 行）
- [x] 2.2 `test_cli.py`：compact 仍是 `# Transcript`；`--profile digest` 退出码 2
- [x] 2.3 `pytest` 全绿（127 个）

## 3. 文档

- [x] 3.1 `SKILL.md`：输出档位改写为三档同一文档类型；新增「摘要与交接」小节；参数、流程、易错点、成功标准同步

## 4. 收口

- [x] 4.1 真实 transcript 实测：default / full / compact 行数与事件数，default 输出与改动前逐字节一致
- [x] 4.2 `openspec validate separate-compact-from-digest --strict` 无 error/warning
- [x] 4.3 `openspec archive separate-compact-from-digest -y` 归档并更新主 spec
