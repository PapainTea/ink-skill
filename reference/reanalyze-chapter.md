# reanalyze-chapter — 重分析已有章节参考

> 本模块由 ink.skill 在用户意图为"重分析第 N 章 / 分析已有章节 / 从外部章节重建 truth files"时 Read。
>
> 用途：作者手动把外部写好的章节放进 `chapters/000N_<标题>.md` 后，skill 没有自动流程回填 7 个 truth files。这时触发本模块，分析章节正文并产出 7 个 truth files 的增量更新。
>
> 本模块相当于"没有 PRE_WRITE_CHECK 和 POST_SETTLEMENT 的写章 pipeline"——输入是已有正文，输出是 truth files 更新。

---

## 触发词

- 重分析第 N 章
- 分析已有章节
- 从外部章节导入 / 从外部章节重建 truth files
- 回填第 N 章的 truth files
- chapter-analyzer

---

## 前置步骤

在执行分析前，先确认以下条件：

1. `chapters/000N_*.md` 文件存在（章节正文已放好）
2. 7 个 truth files 存在（`current_state.md` / `particle_ledger.md` / `pending_hooks.md` / `chapter_summaries.md` / `subplot_board.md` / `emotional_arcs.md` / `character_matrix.md`）
3. 如果 `story/audits/ch-N.md` 已存在且为 `passed=true`，询问作者是否覆盖

---

## 流程（对应 inkOS chapter-analyzer.ts）

### Step 0: 前置动作（必读）

分析正文前**必须** Read `reference/writing-bans.md`（核心硬性禁令）——虽然 reanalyze 不产生新正文，但审计维度要核对已有正文是否违反禁令。Step 4.5 的回填审计也依赖这份规则。

### Step 1: 加载 Context

从 `<书根>/story/` 读取全部 truth files（同写章 Step 2 的必读文件清单）：

- `story_bible.md`
- `volume_outline.md`
- `book_rules.md`
- `current_state.md`
- `particle_ledger.md`
- `pending_hooks.md`
- `chapter_summaries.md`（最近 3-5 章）
- `subplot_board.md`
- `emotional_arcs.md`
- `character_matrix.md`

从 `chapters/` 读取：
- 目标章节正文 `000N_<标题>.md`（完整正文）
- `index.json`

### Step 2: 构建 System Prompt（单阶段，来自 inkOS chapter-analyzer.ts）

**重要**：reanalyze 是**单次 LLM 调用**完成 fact 提取 + 7 个 truth files 增量更新，**不**套用写章 pipeline 的 Phase 2a/2b 两阶段（Observer → Reflector）。后者只在写章时用（writer.ts + observer-prompts.ts），chapter-analyzer 在 inkOS 原版里就是单阶段。

下方 prompt 一字不差来自 inkOS `chapter-analyzer.ts` 的 `buildSystemPrompt()` zh 分支（英文书用 en 分支，见 inkOS 源码）：

```
你是小说连续性分析师。你的任务是分析一章已完成的小说正文，从中提取所有状态变化并更新追踪文件。

## 工作模式

你不是在写作，而是在分析已有正文。你需要：
1. 仔细阅读正文，提取所有关键信息
2. 基于"当前追踪文件"做增量更新
3. 输出格式与写章 pipeline 完全一致

## 分析维度

从正文中提取以下信息：
- 角色出场、退场、状态变化（受伤/突破/死亡等）
- 位置移动、场景转换
- 物品/资源的获得与消耗
- 伏笔的埋设、推进、回收
- 情感弧线变化
- 支线进展
- 角色间关系变化、新的信息边界
```

### Step 3: 构建 User Prompt

```
请分析第 N 章正文，更新所有追踪文件。

## 正文内容

<完整正文>

## 当前状态卡
<current_state.md>

## 当前资源账本
<particle_ledger.md>（全书种必备）

## 当前伏笔池
<pending_hooks.md>

## 已有章节摘要
<chapter_summaries.md 最近章节>

## 当前支线进度板
<subplot_board.md>

## 当前情感弧线
<emotional_arcs.md>

## 当前角色交互矩阵
<character_matrix.md>

## 世界观设定
<story_bible.md>

## 卷纲
<volume_outline.md>

请严格按照 === TAG === 格式输出分析结果。
```

### Step 4: 输出格式（=== TAG === 分隔，与写章 pipeline 一致）

```
=== CHAPTER_TITLE ===
（从正文标题行提取或推断章节标题，只输出标题文字）

=== CHAPTER_CONTENT ===
（原样输出正文内容，不做任何修改）

=== PRE_WRITE_CHECK ===
（留空，分析模式不需要写作自检）

=== POST_SETTLEMENT ===
（留空，分析模式不需要写后结算）

=== UPDATED_STATE ===
更新后的状态卡（Markdown 表格），反映本章结束时的最新状态：
| 字段 | 值 |
|------|-----|
| 当前章节 | N |
| 当前位置 | ... |
| 主角状态 | ... |
| 当前目标 | ... |
| 当前限制 | ... |
| 当前敌我 | ... |
| 当前冲突 | ... |

=== UPDATED_LEDGER ===
更新后的资源账本（7 列含事件ID，Markdown 表格），追踪正文中出现的所有资源变动

=== UPDATED_HOOKS ===
更新后的伏笔池（Markdown 表格），包含所有已知伏笔的最新状态：
| hook_id | 起始章节 | 类型 | 状态 | 最近推进 | 预期回收 | 备注 |

=== CHAPTER_SUMMARY ===
本章摘要（Markdown 表格行）：
| 章节 | 标题 | 出场人物 | 关键事件 | 状态变化 | 伏笔动态 | 情绪基调 | 章节类型 |

=== UPDATED_SUBPLOTS ===
更新后的支线进度板（Markdown 表格）
默认原样输出 `☆ 支线进度板无变动 ☆`，仅当本章有支线变化时才输出完整表格

=== UPDATED_EMOTIONAL_ARCS ===
更新后的情感弧线（Markdown 表格）
默认原样输出 `☆ 情感弧线无变动 ☆`，仅当本章有情感弧变化时才输出完整表格

=== UPDATED_CHARACTER_MATRIX ===
更新后的角色交互矩阵，严格按照 3 个 ### 子表结构：

### 角色档案
| 角色 | 核心标签 | 反差细节 | 说话风格 | 性格底色 | 与主角关系 | 核心动机 | 当前目标 |
|------|----------|----------|----------|----------|------------|----------|----------|

### 相遇记录
| 角色A | 角色B | 首次相遇章 | 最近交互章 | 关系性质 | 关系变化 |
|-------|-------|------------|------------|----------|----------|

### 信息边界
| 角色 | 已知信息 | 未知信息 | 信息来源章 |
|------|----------|----------|------------|

默认原样输出 `☆ 角色交互矩阵无变动 ☆`，仅当本章有角色变化时才输出完整 3 子表
```

### Step 4.5: 审计回填章节 + Followup 继承（v0.1.10 起强制）

reanalyze 虽然不走 PRE_WRITE_CHECK 和写章 Step 6-8 循环，但**必须产一份 audit md**（`story/audits/ch-N.md`），理由：
- 章节从外部导入或回填，也需要可审计的质量记录
- Followup 机制要求 audit 是继承链上的一环（见 `reference/audit.md` §7）

**执行顺序**：
1. Read `reference/audit.md` §7（Followup 段强制约束）
2. 继承上章 followup：Read `story/audits/ch-(N-1).md` 的 `## Followup` 段（若 N=1 跳过），对每条 `[ ]` 判断本章是否消化 → `[x]` 或原样 `[ ]` 搬过来；同时 Read 上章 `current_state.md` 审计纠偏段，把 forward-looking warning/info 迁入
3. 对新回填的 ch N 正文跑 37 维审计（用 Step 2 分析结果作为事实依据），产 `audits/ch-N.md`
4. audit md 末尾必须有 `## Followup` 段（规则同 v0.1.10）

### Step 5: 持久化（完整 7 truth files）

分析结果按写章 Step 9（结算）规则写入**全部 7 个** truth files：

| 文件 | 更新策略 | sentinel 处理 |
|------|---------|---------------|
| `current_state.md` | 全量覆盖 | — |
| `chapter_summaries.md` | 追加本章摘要行 | — |
| `particle_ledger.md` | 按 7 列 schema 增量合并（含事件ID） | Step 4 输出 `☆ 无变动 ☆` 时不写 |
| `pending_hooks.md` | 按 hook_id 合并 | — |
| `subplot_board.md` | 按子线 ID 合并 | Step 4 输出 `☆ 支线进度板无变动 ☆` 时不写 |
| `emotional_arcs.md` | 追加本章情感行 | Step 4 输出 `☆ 情感弧线无变动 ☆` 时不写 |
| `character_matrix.md` | 3 子表按合并 key 更新 | Step 4 输出 `☆ 角色交互矩阵无变动 ☆` 时不写 |

Step 5 完成后，**必须**重算 `PROGRESS.md` 的 `📌 活跃 followup` 段（聚合所有 audits 的 `[ ]` 条目，规则同 audit.md §7.3）。

### Step 6: 快照（强制）

**v0.1.10 起强制**：reanalyze 完成后必须产 `story/snapshots/N/`，与写章 Step 10 规则一致：

```bash
BOOK_DIR=<父目录>/books/<书名>
SNAP_DIR=$BOOK_DIR/story/snapshots/<N>
mkdir -p $SNAP_DIR
cp $BOOK_DIR/story/{current_state,particle_ledger,pending_hooks,chapter_summaries,subplot_board,emotional_arcs,character_matrix}.md $SNAP_DIR/
mkdir -p $SNAP_DIR/audits
cp $BOOK_DIR/story/audits/ch-N.md $SNAP_DIR/audits/
```

理由：Step 12 verify 会检查 `snapshots/N/` 存在，跳过快照 = verify 必 ❌。回填历史章如果不快照，未来 rework 那一章时无基线可恢复。

### Step 7: 更新 index.json

在 `chapters/index.json` 添加或更新本章条目：

```json
{
  "number": N,
  "title": "<章节标题>",
  "status": "approved",
  "wordCount": <字数>,
  "createdAt": "<ISO时间戳>",
  "updatedAt": "<ISO时间戳>",
  "lengthWarnings": []
}
```

### Step 8: 更新 PROGRESS.md

在"操作时间线"追加一行：`<时间> 重分析第 N 章，回填 truth files`

---

## 关键规则（来自 inkOS chapter-analyzer.ts）

1. 状态卡和伏笔池必须基于"当前追踪文件"做**增量更新**，不是从零开始
2. 正文中的每一个事实性变化都必须反映在对应的追踪文件中
3. 不要遗漏细节：数值变化、位置变化、关系变化、信息变化都要记录
4. 角色交互矩阵中的"信息边界"要准确——角色只知道他在场时发生的事
5. 分析模式下，PRE_WRITE_CHECK 和 POST_SETTLEMENT 留空，不填写

---

## 与写章 pipeline 的差异

| 项目 | 写章 pipeline | reanalyze（本模块）|
|------|--------------|-------------------|
| 输入 | LLM 生成正文 | 已有正文文件 |
| PRE_WRITE_CHECK | 必须填写 | 留空 |
| POST_SETTLEMENT | 必须填写 | 留空 |
| Observer/Reflector 两阶段 | ✅（writer.ts + observer-prompts.ts） | ❌ 单阶段（chapter-analyzer.ts 一次 LLM 调用） |
| Step 7 审计 | 37 维 + Followup 继承 | **同上**（v0.1.10 起强制，见 Step 4.5）|
| Step 10 快照 | 强制 | **强制**（v0.1.10 起，见 Step 6）|
| Step 12 verify | 强制运行 | **强制运行**（回填历史章同样要贴 stdout 给作者，见 SKILL.md §7 强制律 9）|
| 适用场景 | 正常写章 | 外部导入 / 补录历史章 |

## 级联重算策略（v0.1.10 明确：默认不做）

场景：书已写到 ch 17，作者说"重分析 ch 10"。

**默认行为**：reanalyze 只动 ch 10 一章（truth files delta + audits/ch-10.md + snapshots/10/），**不**重算 ch 11-17 的 audit。ch 11+ 的 truth files 状态可能因此与 ch 10 新结果有轻微漂移，但绝大多数场景下作者回填 ch 10 是小修（错别字、微调描写），truth files 不会大变。

**作者需要级联时**：手动逐章触发 `重分析 ch 11` → `重分析 ch 12` → ... 到最新章。skill 不提供批量级联命令，理由：
- 级联成本高（N 次 LLM 调用 + N 份 audit md 重写）
- 作者在 ch 11+ 的 audit 里可能手动改过 followup 标注（`[x]` 消化记录、来源链注释），级联会全部覆盖
- 真正需要从 ch 10 起全盘翻新，应该走 rework 流程（重写 ch 10 + 其后章节）而不是 reanalyze

如果你在 ch 11+ 发现 truth files 与 ch 10 新结果明显冲突（如主角状态接不上），单独触发那一章的 reanalyze 即可精修。
