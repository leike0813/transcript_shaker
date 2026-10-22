# Tasks

## 1. 检索实现

- [x] 1.1 新增 `search.py`：`tokenize`、`iter_chunks`（流式 + zstd 三选一）、`count_terms`、`Match`、`search`、`is_ambiguous`、`render_matches`
- [x] 1.2 `cli.py`：`--search` 参数、与 `--list` / 转写互斥、缺 `--harness` 与 `kilo-code` 报错、检索分支在「缺少 transcript」检查之前返回

## 2. 测试

- [x] 2.1 新增 `test_search.py`：全命中 / 最弱词项排序 / 部分命中 / 歧义阈值 / 参数互斥 / 空查询 / `--limit` 截行 / `--match` `--since` / 大小写与去重 / 零命中 / zstd 通路 / 单元级排序与歧义

## 3. 文档

- [x] 3.1 `SKILL.md`：何时使用、输入输出契约、执行流程、脚本调用、内容检索小节、易错点、成功标准、参考资料
- [x] 3.2 `references/script-usage.md`：调用形态、参数表、`### --search` 输出契约、示例、边界情况、常见错误

## 4. 收口

- [x] 4.1 `pytest` 全绿（143 passed）
- [x] 4.2 本机 omp / codex 语料实测检索与退出码
- [x] 4.3 `openspec validate add-content-search --strict`、`openspec archive add-content-search -y`、`openspec validate --all`
