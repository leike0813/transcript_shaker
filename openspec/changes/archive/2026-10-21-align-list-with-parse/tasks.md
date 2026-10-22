# Tasks

## 1. 定位

- [x] 1.1 `locate.py`：`Source.skip` 字段、command-code 的 `*.checkpoints.jsonl`、跳过 0 字节文件
- [x] 1.2 `locate.py` + `cli.py`：`match` 参数与 `--match`（仅 `--list`，转写模式退出码 2）

## 2. 识别

- [x] 2.1 `grok.py`：`_looks_like_grok_file` 整文件判据作为回退
- [x] 2.2 `kimi_code.py`：`metadata` + `protocol_version` 作为会话头判据

## 3. 测试

- [x] 3.1 `test_locate.py` 追加 4 个用例（0 字节、checkpoints、`match`、`--match` 互斥）
- [x] 3.2 `test_harness_adapters.py` 追加 2 个用例与 `grok_partial`、`kimi_empty` fixture

## 4. 文档

- [x] 4.1 `SKILL.md`：`--match`、command-code 检查点、grok/kimi 空会话、0 字节过滤（7 处）

## 5. 收口

- [x] 5.1 `pytest` 全绿（114 个）
- [x] 5.2 全量 census：本机候选 0 失败
- [x] 5.3 `openspec validate align-list-with-parse --strict` 无 error/warning
- [x] 5.4 `openspec archive align-list-with-parse -y` 归档并更新主 spec
