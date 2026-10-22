# harness-adapter delta

## ADDED Requirements

### Requirement: 内容检索（--search）

系统 SHALL 提供 `--search TEXT` 按内容定位 transcript，匹配对象 SHALL 是文件原始字节（zstd 文件为其解压后字节），MUST NOT 解析事件流。查询 SHALL 按空白切为小写词项并去重。一个文件为全命中 SHALL 以「每个词项出现次数均 > 0」判定；若不存在全命中文件，系统 SHALL 输出至少命中一个词项的部分命中。系统 SHALL 只在 `--harness` 指定的单个 harness 内检索，MUST NOT 自动跨 harness 检索；`--harness` 缺失 SHALL 以退出码 2 结束，`kilo-code` SHALL 以退出码 2 结束（一个库文件含多个会话）。

#### Scenario: 单 harness 命中定位

- **WHEN** 用户运行 `--search "embedding cache" --harness omp`
- **THEN** 只扫描 omp 目录下的候选，输出全部词项都命中的文件，按词项命中数、最弱词项出现次数、修改时间降序排列

#### Scenario: 缺少 harness 不检索

- **WHEN** 用户只给内容线索运行 `--search` 而没有 `--harness`
- **THEN** 以退出码 2 结束并在 stderr 说明内容检索暂不跨 harness，系统不扫描任何文件

#### Scenario: 部分命中退回

- **WHEN** 没有任何文件命中全部词项
- **THEN** 输出至少命中一个词项的文件，行的词项计数形如 `terms=1/3`，且 `ambiguous` 为 `yes`

#### Scenario: 压缩会话参与检索

- **WHEN** 候选是 `.jsonl.zst` 且解压能力可用
- **THEN** 按解压后字节计数；解压能力不可用时该文件被跳过，检索不中断

#### Scenario: 词项太少不报错

- **WHEN** 查询去空白后为空
- **THEN** 以退出码 2 结束，不扫描语料
