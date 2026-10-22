# Tasks

## 1. 序列化

- [x] 1.1 新增 `yamlout.py`（`to_yaml` 与标量/块标量规则）
- [x] 1.2 `render.py`：`prepare_events`、`meta_lines`、`events_line`、`fence` 改名、`render_yaml`

## 2. 档位

- [x] 2.1 新增 `digest.py`：`digest_entries`、`render_digest`（compact / digest 共用）
- [x] 2.2 `cli.py`：`--format`、`--profile`、`--max-chars` 档位校验、渲染分发

## 3. 测试

- [x] 3.1 `test_render.py` 追加 3 个用例（full 不截断、YAML 结构、YAML 转义）
- [x] 3.2 新增 `test_digest.py` 6 个用例
- [x] 3.3 `test_cli.py` 追加 5 个用例

## 4. 文档

- [x] 4.1 `SKILL.md`：输出档位小节、digest 文档契约、按需交接规则、参数、流程、易错点、成功标准（10 处）

## 5. 收口

- [x] 5.1 `pytest` 全绿（128 个）
- [x] 5.2 真实 transcript 四档 × 两格式实测，YAML 用 PyYAML 回读
- [x] 5.3 `openspec validate add-output-profiles-and-yaml --strict` 无 error/warning
- [x] 5.4 `openspec archive add-output-profiles-and-yaml -y` 归档并更新主 spec
