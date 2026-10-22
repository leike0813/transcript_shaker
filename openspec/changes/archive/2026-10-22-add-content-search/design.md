# Design

## Context

见 `proposal.md`。约束：Skill 零第三方依赖；检索要在数秒内扫完数百 MB；输出要能被 Agent 直接判断「这是不是目标会话」，而不是让它自己算阈值。

## Goals / Non-Goals

**Goals:**

- 单个 harness 内按内容定位 transcript，耗时随语料线性增长且常数小。
- 排序与歧义判定由脚本确定性给出，Agent 只做分支。
- 压缩会话（`.zst` / `.zstd`）与明文同样参与检索。

**Non-Goals:**

- 不做跨 harness 检索（用户只给内容线索时，harness 由用户确认）。
- 不做倒排索引、结果缓存、snippet 摘要、编辑距离或语义检索。
- 不解析事件流，也不按 `role` 之类的字段过滤。

## Decisions

**1. 匹配原始字节，不解析 JSON 事件流。** 实测 omp 全库 310 文件 / 493MB：字节扫描 + 3 词项计数 1.8s，adapter 全量解析 10.0s（49MB/s）；codex 全库 3GB 解析约 300s，字节扫描 9s，zstd 解压 + 扫描 294MB/s。扫描是唯一「快」的路径，且无需按 harness 猜 schema。

**2. 不做倒排索引与结果缓存。** 语料随时间增长，缓存要处理失效与多词项组合，收益低于复杂度；先用 `--since` / `--match` 缩小语料。

**3. 不按 `"role":"system"` 之类过滤行。** 实测 omp 全库 305/310 个文件都含 `compact`、`档位`，逐行核对命中行是 `role=assistant` 的 thinking / toolCall，噪声来自真实对话内容；加过滤既无收益，又引入按 harness 猜 schema 的脆弱逻辑。

**4. 排名用最弱词项出现次数（`min(counts)`）而非总和。** 实测 "embedding cache" 用总和会把 16333 次 `cache` 的文件顶到第一，改用 min 后第一名是真正密集讨论 embedding 的会话（539 vs 469）。

**5. 歧义由脚本算成 `# ambiguous: yes|no`。** 判定为：首位是部分命中，或首位 `score` 小于第二位两倍。Agent 只做分支，不自行做算术。

**6. 单文件读失败跳过而非中断。** 一个损坏的 `.zst` 不该让整次检索失败；被跳过的文件不出现在输出里。

**7. zstd 用流式 Popen，不用 `capture_output`。** 既有 `adapters/_support.py` 的 `zstd -dc` 分支会把整个解压结果读进内存；单份 codex 会话解压后可达数百 MB，检索必须逐块读 `stdout`。也不复用 `iter_lines`：它产出解码后的文本行，对本需求是 3–4 倍内存与时间开销。

**8. 字节小写只覆盖 ASCII。** 文档按此措辞，不宣称 Unicode 大小写不敏感；中文查询按空白/标点切词，不切词时整句作为一个词项子串匹配。

## Risks / Trade-offs

- **命中数不等于命中质量**：system 提示与工具 schema 也参与匹配。缓解：文档要求用有区分度的 2–3 个词项。
- **codex 全库较慢**：4000+ 个 `.zst` 需解压，预计 30–60s。缓解：文档要求先用 `--since` / `--match`。
- **`kilo-code` 不支持**：一个 SQLite 库含多个会话，路径级定位没有意义；以退出码 2 明确拒绝。
- **部分命中时 `score` 为 0**：词项未全命中时 `min(counts)` 恒为 0，此时靠「命中词项数」与 `ambiguous` 分支；这是刻意的，不引入加权打分。
