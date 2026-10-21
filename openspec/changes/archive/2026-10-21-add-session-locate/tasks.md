# Tasks

## 1. 定位模块

- [x] 1.1 新建 `transcript_shaker/locate.py`：`Source`、`HARNESS_SOURCES`、`Candidate`、`find_candidates`、`render_candidates`
- [x] 1.2 根目录调用时解析，`CODEX_HOME` 覆盖 `~/.codex`；`stat` 失败跳过；按 mtime 倒序、路径升序去重排序

## 2. CLI 双模式

- [x] 2.1 `transcript` 改 `nargs="?"`，新增 `--list` / `--harness` / `--limit` / `--since`，`--max-chars` 默认改 `None` 后回落到 `DEFAULT_MAX_CHARS`
- [x] 2.2 互斥与缺失校验用 `parser.error`（退出码 2）；`--list` 分支输出候选后返回 0
- [x] 2.3 `--help` 加 examples epilog；`--harness` 用 `choices` 列出 15 个枚举值

## 3. 测试

- [x] 3.1 新建 `scripts/tests/test_locate.py`：覆盖 11 个用例（扫描覆盖、排序、过滤、空结果、不读内容、CODEX_HOME、退出码 2）
- [x] 3.2 既有 97 个测试不改断言，全部保持通过

## 4. 文档

- [x] 4.1 重写 `SKILL.md`：skill-smith 要求的必需章节 + 支持矩阵；删除“Codex transcript 定位”
- [x] 4.2 description 同时覆盖“查找最近会话”与“转写某次会话”

## 5. 收口

- [x] 5.1 `pytest` 全绿；`--list` 在真实 HOME 上输出候选并与 `--help` 一致
- [x] 5.2 `openspec validate add-session-locate --strict` 无 error/warning
- [x] 5.3 `openspec archive add-session-locate -y` 归档并更新主 spec
