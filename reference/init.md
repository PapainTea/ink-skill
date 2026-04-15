# init — 新建书 / 迁移老书参考

> 本模块由 ink.skill 在用户意图为"新建书 / ink 迁移 / ink 初始化"时 Read。
>
> **两种场景**：
> - **新建书**：从 `templates/book-skeleton/` 复制骨架 + 作者对话填充 5 个基础文件
> - **迁移老书**：检测 `chapters/index.json` 和 `story/current_state.md` 存在 → 自动回填 PROGRESS.md + 各平台 init 文件
>
> 迁移流程详细步骤见本文件下方"迁移老书"段（阶段 6 补全）。

---

## 新建书流程（必读）

**Step 0 — 强制列题材**：用户说"新建一本 XX"时，**第一件事**不是问故事设定，而是**列出全部 15 个可选题材**（含中文名 + 英文 id + 是否数值型），让作者明确选一个：

```
📚 ink.skill 支持的 15 个体裁：

### 数值型体裁（会创建 particle_ledger.md 资源账本）

1. **玄幻** (xuanhuan) — 典型爽点：打脸 / 升级突破 / 收益兑现
2. **仙侠** (xianxia) — 修炼体系严格的东方幻想
3. **地下城核心** (dungeon-core) — 你就是副本本体
4. **系统末日** (system-apocalypse) — 末世生存 + 游戏化系统
5. **LitRPG** (litrpg) — 完全游戏化的世界

### 非数值型体裁（不创建 particle_ledger.md，只用 subplot_board + character_matrix）

6. **都市** (urban) — 现代都市背景
7. **恐怖/悬疑** (horror) — 心理恐怖、超自然、悬疑推理
8. **修真** (cultivation) — 修炼色彩较轻的东方玄幻
9. **渐进成长** (progression) — 偏西式进化设定
10. **科幻** (sci-fi) — 硬科幻 / 软科幻
11. **浪漫奇幻** (romantasy) — 爱情 + 奇幻
12. **治愈/轻松** (cozy) — 慢生活、日常、低冲突
13. **异世界转生** (isekai) — 穿越 / 重生 / 异世
14. **爬塔** (tower-climber) — 层层关卡、step-by-step 挑战
15. **其他/通用** (other) — 不明确分类时的 fallback

请告诉我你要写的是哪一种？（回复体裁中文名或 id 即可）
```

**不要跳过这一步**。即使作者已经告诉你故事大概，也要先让他确认体裁——因为体裁决定：
- 是否创建 `particle_ledger.md`（只有 5 个数值型体裁创建）
- 启用哪些审计维度（从 37 维度里选）
- 典型章节类型（战斗章/布局章/过渡章/回收章等）
- 禁忌词 / 疲劳词 / 爽点类型

**Step 1 — 读取对应题材配置**：作者选完后，Read `<skill_root>/genres/<genre_id>.md`，把 YAML frontmatter + 正文全部纳入上下文。

（体裁配置在 skill 流程里的完整集成方式见本文件末尾"体裁配置在 skill 流程里的实际集成"段。）

**Step 2 — 从 book-skeleton 复制骨架到 `<父目录>/books/<书名>/`**：

按体裁类型决定是否复制 `particle_ledger.md`：
- 数值型体裁 → 复制 7 truth files（含 particle_ledger）+ `book_rules.md` + `volume_outline.md`（初始为空大纲）+ `chapters/` + `snapshots/0/`
- 非数值型体裁 → 同上但 **跳过 particle_ledger.md**，因为这个体裁不用数值系统

**Step 3 — 填充 `book_rules.md` 的 frontmatter**：
- `genre.id` = 作者选的 id
- `genre.name` = 对应中文名
- `{{book_name}}` = 作者给的书名
- `{{created_at}}` = 当前时间

**Step 4 — 对话式填充基础设定**：和作者对话填 `story_bible.md`（世界观）/ `volume_outline.md`（第一卷 10-20 章大纲）/ `character_matrix.md`（主角 + 2-3 配角基本档案）。

**Step 5 — 生成当前平台的 init 文件**（CLAUDE.md / AGENTS.md 等）+ 初始化 `PROGRESS.md`。

---

# 新建书流程（详细步骤）

**触发**：用户说"新建一本书" / "建一本新书" / "我想写一本 XX"。

**核心思路**：直接对话产出，不用 Architect 那套重型 prompt。作者告诉 Claude 想写什么，Claude 边问边产出 5 个基础文件 + 初始化目录结构 + 创建 snapshots/0/。

---

## 1. 对话采集（边问边写，不一次性问完）

按需采集，不要一次性问太多。最少需要：

| 必问 | 用途 |
|------|------|
| **书名** | 决定目录名 `<父目录>/books/<书名>/` |
| **题材方向** | 玄幻 / 都市 / 科幻 / 同人 / ... 决定写作风格倾向 |
| **主角设定** | 一两句话即可：身份 + 核心优势 + 性格底色 |
| **故事梗概** | 一段话：起点 + 主线冲突 + 大致目标 |

可选（不要一次问完，作者愿意补就补）：
- 平台口味（起点 / 番茄 / 晋江 / ...）
- 目标卷数 / 每章字数
- 语言（默认中文）
- 是否有特殊禁忌 / 不写的元素

**对话原则**：
- 作者说"随便"或拒绝细化时，Claude 直接产出合理默认值，不强迫用户决策
- 不需要逐项填表——作者一段话讲完想法，Claude 自己提取 + 补全
- 给作者看草稿，让作者改（不要假装一次成）

---

## 2. 产出 5 个基础文件

收集到足够信息后，Claude 直接写出以下 5 个文件（写到 `<父目录>/books/<书名>/story/` 下）：

| 文件 | 内容 | schema 参考 |
|------|------|------------|
| `story_bible.md` | 世界观 / 主角 / 阵营与角色 / 地理环境 / 标题与梗概 | §03 基础文件规范 |
| `volume_outline.md` | 卷规划（至少第一卷）+ 黄金三章法则 | §03 |
| `book_rules.md` | YAML frontmatter（主角锁定 / 题材锁 / 禁忌 / 疲劳词）+ 正文（叙事视角 / 核心冲突驱动）| §03 |
| `current_state.md` | 第 0 章初始状态卡（7 个字段，全部填初始值）| §02 |
| `pending_hooks.md` | 伏笔池表头 + 初始伏笔（最近推进列填 `0`）| §02 |

**写法**：用 Write 工具一次写一个文件。每写完一个让作者看一眼（作者可以不看，但要给机会改）。

---

## 3. 自动初始化的 4 个空真相文件

5 个基础文件写完后，Claude 自动创建 4 个空表头的真相文件：

| 文件 | 初始内容 |
|------|---------|
| `particle_ledger.md` | 7 列表头 + `init-0` 行（`\| 0 \| - \| 0 \| 0 \| 0 \| 开书初始 \| init-0 \|`）|
| `subplot_board.md` | 9 列表头（无数据行）|
| `emotional_arcs.md` | 6 列表头（无数据行）|
| `character_matrix.md` | 3 子表骨架（### 角色档案 / ### 相遇记录 / ### 信息边界，每个子表只有表头）|

详细 schema 见 §02。

---

## 4. 初始化目录结构

```bash
BOOK_DIR=<父目录>/books/<书名>
mkdir -p "$BOOK_DIR/story/audits"
mkdir -p "$BOOK_DIR/story/snapshots"
mkdir -p "$BOOK_DIR/chapters"
```

---

## 5. 创建 snapshots/0/

5 个基础文件 + 4 个空真相文件全部就位后，立刻 cp 一份到 `snapshots/0/`，作为"第 0 章虚拟快照"——后续 rework 第 1 章时需要从这个快照恢复。

```bash
SNAP_DIR="$BOOK_DIR/story/snapshots/0"
mkdir -p "$SNAP_DIR"

cp "$BOOK_DIR/story/current_state.md"       "$SNAP_DIR/"
cp "$BOOK_DIR/story/particle_ledger.md"     "$SNAP_DIR/"
cp "$BOOK_DIR/story/pending_hooks.md"       "$SNAP_DIR/"
cp "$BOOK_DIR/story/chapter_summaries.md"   "$SNAP_DIR/" 2>/dev/null || echo "" > "$SNAP_DIR/chapter_summaries.md"
cp "$BOOK_DIR/story/subplot_board.md"       "$SNAP_DIR/"
cp "$BOOK_DIR/story/emotional_arcs.md"      "$SNAP_DIR/"
cp "$BOOK_DIR/story/character_matrix.md"    "$SNAP_DIR/"
```

详细快照语义见 §10。

---

## 6. 创建空 chapters/index.json

```bash
echo "[]" > "$BOOK_DIR/chapters/index.json"
```

JSON 数组（不是 `{chapters: []}` 包裹），对齐原项目格式。

---

## 7. 完成后告诉作者下一步

Claude 完成上述全部步骤后，主动告诉作者：

> 「书已建好。下一步：
> 1. 看一眼 `story/story_bible.md` 和 `story/volume_outline.md`，不满意可以告诉我改
> 2. 准备好就说『写第 1 章』」

不要默认作者立刻开始写。给一个停下来审阅的窗口。

---

## 8. 与原项目的差异

| 原项目（Architect agent）| skill 模式 |
|------------------------|-----------|
| 单次 LLM call 一次性产出 5 个 section（temperature 0.8 / maxTokens 16384）| 多轮对话，按需问、按需产出 |
| 用 `=== SECTION: <name> ===` 切分输出 | 直接 Write 单个文件 |
| 严格 JSON schema 校验 | LLM 自己保证格式正确 + 作者审阅 |
| 必须收齐所有信息才开始 | 作者愿意省略的字段直接给默认值 |

skill 模式更轻——没有 Architect agent 的 system prompt 模板（节省几百行），靠对话自然推进。
# 基础文件规范

基础文件是一本书的"根基"，在新建书时由 Architect 生成或用户手写，之后每一轮写章、审稿、修订都会读它们。一共 5 个，其中 2 个可选。

所有基础文件位于 `<父目录>/books/<书名>/story/` 下。

---

## 1. story_bible.md — 世界观设定

**用途**：本书的"圣经"，定义世界、主角、势力、地图、书名与简介。所有 agent 都会读它，用来保证设定不漂移。

**谁写**：Architect 初始化时生成草稿，用户可手动编辑补充。

**谁读**：Writer / Auditor / Reviser / Planner / Composer 全链路都读。

**格式**：5 个二级标题 section。

```markdown
## 01_世界观
世界观设定、核心规则体系（时代框架、社会结构、能量/资源规则、世界核心定律等）

## 02_主角
主角设定：
- 身份（社会身份/职业/出身）
- 金手指（核心优势/能力）
- 性格底色（3-5 个关键词）
- 行为边界（3-5 条，什么事主角不会做）

## 03_势力与人物
主要势力及重要配角。每个配角必须写：
- 名字
- 身份
- 核心动机
- 与主角关系
- 独立目标（不是工具人）

## 04_地理与环境
主要地图、核心场景、环境特色

## 05_书名与简介
- 书名（题材 + 核心爽点 + 主角行为式长书名）
- 简介（300 字内，三选一）：
  1. 冲突开篇法（困境 → 金手指 → 悬念）
  2. 高度概括法（只挑主线 + 留悬念）
  3. 小剧场法（经典桥段作引子）
```

---

## 2. volume_outline.md — 卷纲

**用途**：全书卷级规划，写章前 Writer/Planner 会读。

**谁写**：Architect 生成草稿，用户强烈建议手动调整（这是全书骨架）。

**谁读**：Planner / Composer / Writer / Auditor / Reviser。

**格式**：

```markdown
## 第 1 卷：<卷名>
- 章节范围：1-30
- 核心冲突：<一句话>
- 关键转折：
  - 第 N 章：<转折点>
- 收益目标：读完本卷读者应该获得什么爽点 / 期待什么

## 第 2 卷：...

### 黄金三章法则（前三章必须遵循）

- **第 1 章：抛出核心冲突**
  - 开篇直接进入冲突场景
  - 禁止大段背景介绍 / 世界观灌输
  - 第一段必须有动作或对话
  - 章末核心矛盾必须浮出水面
- **第 2 章：展现金手指 / 核心能力**
  - 主角核心优势必须在本章初现
  - 必须通过具体事件展示，不能只是描述
  - 第一个小爽点必须在本章出现
- **第 3 章：明确短期目标**
  - 主角第一个阶段性目标必须确立
  - 目标具体可衡量（不是"变强"这种虚的）
  - 章尾钩子足够强，给读者追读理由
```

---

## 3. book_rules.md — 本书规则

**用途**：本书的硬性规则（YAML），以及叙事视角/冲突驱动的指导（正文）。Writer/Auditor 把它当硬约束。

**谁写**：Architect 生成草稿，用户可调。

**谁读**：Writer / Auditor / Reviser（作为 rule stack 加载）。

**格式**：YAML frontmatter + 正文。

```markdown
---
version: "1.0"
protagonist:
  name: <主角名>
  personalityLock: [关键词1, 关键词2, 关键词3]        # 3-5 个
  behavioralConstraints: [约束1, 约束2, 约束3]       # 3-5 条
genreLock:
  primary: <题材 id>                                 # 例 xianxia / urban
  forbidden: [文风1, 文风2]                          # 禁止混入的 2-3 种文风
numericalSystemOverrides:                            # 可选，仅数值系题材
  hardCap: <硬上限>
  resourceTypes: [资源1, 资源2]
prohibitions:
  - <本书级禁忌 1>
  - <本书级禁忌 2>
chapterTypesOverride: []
fatigueWordsOverride: []                             # 覆盖题材默认的疲劳词列表
additionalAuditDimensions: []                        # 追加自定义审稿维度
enableFullCastTracking: false                        # 是否全员角色追踪

length:                                              # 字数配置（canonical，详见 §04 / §09）
  target: 4500                                         # 目标字数
  softMinPct: 10                                       # softMin = target × (1 - 10%) = 4050
  softMaxPct: 10                                       # softMax = target × (1 + 10%) = 4950
  hardMinPct: 20                                       # hardMin = target × (1 - 20%) = 3600
  hardMaxPct: 20                                       # hardMax = target × (1 + 20%) = 5400
  countingMode: zh_chars                               # zh_chars / en_words
  enforceSoftMin: true                                 # 字数 < softMin 时默认扩写（可 PRE_WRITE_CHECK 声明例外跳过）
  enforceHardMin: true                                 # 字数 < hardMin 时硬 block 必须扩写

hardRules:                                           # 硬性规则开关（默认全开，作者可关掉某项）
  banDash: true                                        # 禁止破折号 ——
  banBushiErshi: true                                  # 禁止「不是…而是…」句式
  banAnalysisTerms: true                               # 禁止分析术语（核心动机/信息边界 等）
  banCollectiveShock: true                             # 禁止集体反应套话
  banMarkdownLeakage: true                             # 禁止 md 结构化标记泄漏（--- / ### / ** / 列表等）
  maxMarkerWordsPer3000: 1                             # 转折/惊讶标记词上限（每 3000 字 1 次）

pipeline:                                            # 写章流程行为开关
  autoRunAudit: true                                   # Step 7 审计默认必跑（详见 §04 Step 7）
  autoRunVerify: true                                  # Step 12 完成后必跑 verify-chapter.py（详见 §04 Step 12）
  autoExpandIfShort: true                              # 字数不足时自动扩写循环
---

## 叙事视角
（第几人称，视角切换规则，叙事距离偏好）

## 核心冲突驱动
（本书的核心矛盾和推动力来源）
```

---

## 4. current_state.md — 当前状态卡

**用途**：当前章节结束时的"状态快照卡"，每写完一章被覆盖一次。

**谁写**：Architect 生成初始版（第 0 章），之后 Writer/Settler 每章覆盖。

**谁读**：所有 agent（最重要的上下文之一）。

**格式**：

```markdown
| 字段       | 值                    |
|------------|-----------------------|
| 当前章节   | <N>                   |
| 当前位置   | <地点>                |
| 主角状态   | <情况>                |
| 当前目标   | <目标>                |
| 当前限制   | <限制条件>            |
| 当前敌我   | <敌对/盟友关系>       |
| 当前冲突   | <当前冲突>            |
```

---

## 5. author_intent.md — 作者意图（可选）

**用途**：用户向 AI 表达的"我想写成什么样"、全书主题、风格偏好。

**谁写**：用户手写（Architect 不生成）。

**谁读**：Writer / Reviser（作为软指导，不是硬约束）。

**格式**：自由 Markdown。

---

## 6. current_focus.md — 当前聚焦（可选）

**用途**：用户在当前阶段想强调的内容（例如"最近 3 章重点铺设 <支线 X>"、"降低感情戏比重"）。

**谁写**：用户手写，可随时更新。

**谁读**：Writer / Planner / Composer。

**格式**：自由 Markdown，通常很短（几句话 ~ 一段）。

---

## 迁移老书到 ink.skill 形态

**触发词**：`ink 迁移` / `迁移本书` / `升级到 skill 版本` / `ink migrate`。

### 识别条件

skill 一激活，检查当前书根是否为"老书"：
- 存在 `chapters/index.json` 和 `story/current_state.md` 且至少有 1 章已写
- **不存在** `PROGRESS.md`（存在则走幂等性补齐路径，见下方）

若识别为老书 → 提示作者"检测到老书，是否迁移？"，得到确认后执行迁移流程。

### 幂等性检查（R8）

重复执行"ink 迁移"是安全的：
- 若 `PROGRESS.md` **已存在**：仅**补齐缺段**，不全量重写；追加操作时间线前检测末 5 条中是否已有"迁移完成"事件，有则跳过追加
- 若对应平台 init 文件（CLAUDE.md / AGENTS.md / GEMINI.md / .cursorrules）**已存在**：不覆盖，提示作者"init 文件已存在，保持不动"

### 迁移流程（6 步）

**Step 1**: Read `chapters/index.json`
- 获取章节清单 + status + wordCount + createdAt/updatedAt
- 计算 `last_approved_chapter` = 最后一条 `status=approved` 的章号
- 计算 `next_chapter` = 最后一条 `status != approved` 的章号，或 `last_approved_chapter + 1`

**Step 2**: Read `story/current_state.md`
- 获取故事当前状态描述
- 用于填充 PROGRESS.md 的"当前状态"段

**Step 3**: 聚合 `story/audits/ch-*.md`
- 遍历所有文件，抽取 severity=followup 的条目
- 记录每条的：章号来源 / 原文 / 涉及章节（若提及）

**Step 4**: 生成 / 补齐 `PROGRESS.md`

**情况 A：PROGRESS.md 不存在（首次迁移）**

从 `templates/PROGRESS.template.md` 复制模板，填充占位符：
- `{{book_name}}` → 从当前书目录名推断
- `{{last_approved_chapter}}` / `{{word_count}}` / `{{approved_date}}` → 从 Step 1 结果
- `{{next_chapter}}` → 从 Step 1 结果
- `{{last_action_timestamp}}` → 当前 ISO 时间
- `{{last_action_summary}}` → `迁移完成（原 markdown-instruction 形态 → ink.skill）`
- `{{book_root_abs_path}}` → 当前书根绝对路径
- `{{ts1}}` / `{{action1}}` → 与 last_action 同

活跃 followup 段：把 Step 3 聚合出的条目写入，格式：
```
- [ ] ch{来源章} {原文截取 80 字内}
```

在 PROGRESS.md 末尾（"作者笔记"段**之前**）追加一段"📋 迁移原始数据（临时）"：
```markdown
## 📋 迁移原始数据（临时，作者核对无误后可删）  <!-- migration-dump -->

> 迁移时自动把 audits/ 的完整 severity 明细 dump 到这里，便于作者核对。
> 核对完成后可以整段删除本段。

<逐章 dump 每个 audit 的完整内容，按 ch 升序>
```

**情况 B：PROGRESS.md 已存在（幂等）**

- 只补齐缺段，按 SKILL.md §4 容错规则
- 操作时间线段检查末 5 条是否已含"迁移完成"，有则跳过追加
- 不重新 dump 迁移原始数据段（首次已有）
- 不覆盖作者笔记段

**Step 5**: 生成当前平台的 init 文件

按 SKILL.md §5 规则（当前平台 agent 自写）：
- Claude Code → 从 `templates/init/CLAUDE.md.template` 填充 `{{book_name}}` 写入当前书根 `CLAUDE.md`
- Codex → `AGENTS.md.template` → `AGENTS.md`
- Gemini CLI → `GEMINI.md.template` → `GEMINI.md`
- Cursor → `cursorrules.template` → `.cursorrules`

若 init 文件已存在 → 跳过不覆盖。

**Step 6**: 向作者报告

输出一段总结：
- 本次迁移覆盖章节范围（如 ch1–15）
- 生成的文件清单（PROGRESS.md、当前平台 init 文件）
- 活跃 followup 条数
- 老版 `<父目录>/books/CLAUDE.md`（v1.0.x markdown 分发） + `.claude-modules/` 与新 init 文件并存说明（R11）：
  > 老版 `CLAUDE.md` 与新 init 不冲突。你可以保留（作备份，新版更精确）或删除（不再回滚 v1.0.x 时）。建议先跑 1-2 个会话验证无问题再决定删除。
- 下一步建议（新写章、审计、结算等）

**不删除旧文件**：skill 永不主动删除 v1.0.x 分发的 `books/CLAUDE.md` 和 `.claude-modules/`（R11）。

### 误迁移时的回滚

若作者反悔：
1. 删除本次生成的 `PROGRESS.md` 和 `<platform>.md`
2. 不需要回滚其他文件（迁移不改 truth files、不动章节正文、不创建快照）

迁移流程本身**设计为零破坏**：只读老数据，只新增 PROGRESS.md 和 init 文件。

---

## 附录：体裁选择与配置加载

**新建书时的体裁选择**：

ink.skill 支持 15 个体裁配置，位于 `<skill_root>/genres/<genre-id>.md`。创建书时让作者从以下列表选一个：

**数值型体裁**（会创建 `particle_ledger.md` 资源账本）：
- `xuanhuan` — 玄幻
- `xianxia` — 仙侠
- `dungeon-core` — 地下城核心（LitRPG 子类）
- `system-apocalypse` — 系统末日
- `litrpg` — LitRPG（游戏系统）

**非数值型体裁**（不创建 `particle_ledger.md`，只用 subplot_board + character_matrix）：
- `urban` — 都市
- `horror` — 恐怖/悬疑
- `cultivation` — 修真（软系统，区别于 xianxia 的硬修炼）
- `progression` — 渐进成长
- `sci-fi` — 科幻
- `romantasy` — 浪漫奇幻
- `cozy` — 治愈/轻松
- `isekai` — 异世界转生
- `tower-climber` — 爬塔
- `other` — 其他/通用

**加载规则**：
1. 新建书时读取所选体裁的 `.md`（含 YAML frontmatter：`chapterTypes` / `fatigueWords` / `satisfactionTypes` / `auditDimensions` 等）
2. 把关键字段注入 `<书根>/book_rules.yaml` 的对应段（或保留作为独立 book 元信息）
3. 写作/审计时 skill 加载当前体裁的配置，把"题材禁忌""数值规则""节奏规则""章节类型"等纳入上下文

**关键字段含义**：
- `numericalSystem: true/false` — 是否启用资源账本
- `powerScaling: true/false` — 是否有力量等级体系
- `eraResearch: true/false` — 是否需要时代考据（历史/科幻常需要）
- `chapterTypes` — 本体裁典型章节类型（战斗章 / 布局章 / 过渡章 / 回收章 等）
- `fatigueWords` — 本体裁易滥用词汇（写作时需避免）
- `satisfactionTypes` — 本体裁典型爽点类型
- `pacingRule` — 节奏规则（如"三章内必有明确反馈"）
- `auditDimensions` — 启用的审计维度编号（37 维度中选哪些）

**作者未选体裁时**：默认 `other`，加载 `genres/other.md`。

---

## 附录：数据目录结构参考（原 src/01-data-structure.md）

> 本段由 v0.1.0 → v0.1.1 补齐。描述作者 books/ 目录的规范布局、`.ink-writer.yaml` 配置、7 truth files 清单、章节文件命名约定等。新建书 / 迁移老书时作为参考。

## 标准布局

作者选一个父目录（任意位置），在其下固定有一个叫 `books` 的子目录。`books/` 下每本书占一个目录。books 根目录还包含一份配置文件 `.ink-writer.yaml`：

```
<父目录>/books/                      # books 根目录（`books` 是固定命名）
├── .ink-writer.yaml                 # 配置文件（首次对话后自动创建，详见 §00 系统角色）
├── <书名1>/                          # 某本书
├── <书名2>/
└── ...
```

每本书的数据存放在 `<父目录>/books/<书名>/` 下，结构固定：

```
<父目录>/books/<书名>/
├── story/                          # 世界状态层（truth files + 基础文件）
│   │
│   ├── 【基础文件（用户手写或 Architect 生成，少改）】
│   ├── story_bible.md              # 世界观设定
│   ├── volume_outline.md           # 卷纲 / 章节大纲
│   ├── book_rules.md               # 本书专属规则（YAML frontmatter + 正文）
│   ├── author_intent.md            # 作者意图（可选）
│   ├── current_focus.md            # 当前聚焦（可选）
│   │
│   ├── 【7 个真相文件（每章结算后更新）】
│   ├── current_state.md            # 当前状态卡（字段键值表）
│   ├── particle_ledger.md          # 资源账本（7 列）
│   ├── pending_hooks.md            # 伏笔池（7 列）
│   ├── subplot_board.md            # 支线进度板（9 列）
│   ├── emotional_arcs.md           # 情感弧线（6 列）
│   ├── character_matrix.md         # 角色交互矩阵（3 子表）
│   ├── chapter_summaries.md        # 章节摘要（8 列）
│   │
│   ├── audits/                     # 审计结果（每章一个 md，Obsidian callout 格式）
│   │   ├── ch-1.md                 # 第 1 章审计
│   │   ├── ch-2.md
│   │   └── ...                     # 详见 §06 审计系统
│   │
│   └── snapshots/                  # 历史快照（只读档案）
│       ├── 0/                      # 开书初始状态（新建书时创建）
│       ├── 1/                      # 写完第 1 章后的状态
│       ├── 2/                      # 写完第 2 章后的状态
│       └── ...                     # 每章一个目录
│           ├── current_state.md    # 快照版本
│           ├── particle_ledger.md
│           ├── pending_hooks.md
│           ├── subplot_board.md
│           ├── emotional_arcs.md
│           ├── character_matrix.md
│           ├── chapter_summaries.md
│           └── audits/             # 该章及之前的审计 md（与 truth files 一并归档）
│               └── ch-N.md
│
└── chapters/                       # 章节正文
    ├── 0001_<标题>.md              # 正文：第一行 `# 第 N 章 <标题>`，文件名也带标题
    ├── 0002_<标题>.md
    ├── ...
    └── index.json                  # 章节索引（含标题、状态、字数等元数据）
```

### 不创建的目录（与原项目差异）

skill 模式不创建以下目录——它们是原项目 pipeline / memory 检索的辅助产物，skill 模式下 LLM 直接读 truth files 完成全部工作：

| 不创建 | 原项目用途 | skill 模式为何不需要 |
|--------|----------|---------------------|
| `story/state/` | 结构化 JSON 事实索引（给 memory.db 做 source of truth） | Markdown truth files 本身就是事实层，无需重复 |
| `story/runtime/` | pipeline 中间产物（chapter intent / context package / rule stack / trace） | skill 模式无 planner/composer 分阶段，没有中间产物 |
| `story/memory.db` | SQLite 事实索引（给 retrieveMemorySelection 做 context 选择） | LLM 直接读 truth files，1M context 放得下 |

如果未来书超长（>100 章）需要 context 检索，可以按需重新引入 memory.db。当前默认不维护。

## 快照语义（重要）

`snapshots/N/` 表示"**写完第 N 章后、当时的累积状态**"，不是"最终结果的副本"。

**硬约束**（任何操作都要遵守）：
1. 绝不向 `snapshots/N/` 写入第 N 章之后才出现的数据
2. 绝不批量用一个最终结果覆盖所有快照
3. 绝不修改 `snapshots/N/` 下的任何文件
4. 恢复/重建时必须逐章"递增生成"每个快照

## chapter index.json 结构

`chapters/index.json` 是 JSON 数组（不是 `{chapters: [...]}` 对象包裹），每个元素代表一章：

```json
[
  {
    "number": 1,
    "title": "<标题>",
    "status": "approved",
    "wordCount": 3240,
    "createdAt": "2026-01-15T12:00:00.000Z",
    "updatedAt": "2026-01-15T12:00:00.000Z",
    "lengthWarnings": []
  }
]
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `number` | int | 章节号 |
| `title` | string | 章节标题（不含"第 X 章"前缀）|
| `status` | enum | `draft` / `audited` / `approved` / `needs_revision`（4 种状态，**用于判断章节是否过审**） |
| `wordCount` | int | 最终字数（按 zh_chars 计数） |
| `createdAt` | ISO timestamp | 首次创建时间 |
| `updatedAt` | ISO timestamp | 最后修订时间 |
| `lengthWarnings` | string[] | 字数超出软/硬区间的警告 |

**注**：审计结果**不在 index.json 内**，而是写入 `story/audits/ch-<N>.md`（详见 §06）。

### status 状态机（判断章节是否过审）

| 状态 | 含义 | 触发 |
|------|------|------|
| `draft` | 初稿，未审计 | 写完 Step 5 但跳过 Step 7 |
| `audited` | 已审计但有未修复 warning | 走完 Step 7 但有 warning 未处理 |
| `approved` | 审计通过/全部修复 | 完整流程通过 |
| `needs_revision` | 审计发现 critical 问题待修 | Step 7 报 critical 后未走 Step 8 |

### 文件名命名约定

- 章节文件命名规则：**4 位章节号 + 下划线 + 标题 + .md**。章节号不足 4 位前面补 0。
  - 第 1 章 → `0001_序章.md`
  - 第 14 章 → `0014_<标题>.md`
  - 第 150 章 → `0150_xxx.md`
  - 第 1500 章 → `1500_xxx.md`
- 补零目的：让文件按文件名排序时章节顺序自然正确（否则 `1.md, 10.md, 11.md, 2.md` 会乱）
- Truth file 备份（如恢复操作）：`<filename>.backup-<YYYYMMDDhhmmss>`

## 文件命名约定

- 章节文件命名：4 位章节号（不足补 0）+ 下划线 + 标题 + `.md`。例：第 1 章 `0001_序章.md` / 第 14 章 `0014_<标题>.md` / 第 150 章 `0150_<标题>.md`
- 标题中的特殊字符保留（空格、中文标点都可以，文件系统能处理）
- Truth files 文件名全小写 + 下划线，不带 extension 前缀

## 读取优先级

当 LLM 加载 context 时，按此优先级读取：

1. **必读（写章/审计都要）**：current_state.md, story_bible.md, volume_outline.md, book_rules.md
2. **写章必读**：所有 7 个 truth files + 最近 1-2 章正文
3. **审计必读**：被审章节正文 + 前一章正文 + 所有 truth files
4. **修订必读**：被修章节正文 + 审计结果 + current_state + ledger + hooks

---

## 体裁配置在 skill 流程里的实际集成

新建书或激活老书时，按以下步骤把 genre 配置注入写章和审计流程：

### 加载步骤

1. 从 `<书根>/story/book_rules.md` frontmatter 的 `genre.id` 字段获取体裁 ID
2. Read `<skill_root>/genres/<genre_id>.md`（skill 仓库根目录下的 genres/ 目录）
3. 从该文件的 YAML frontmatter 提取以下字段，注入当前 session 上下文：

| 字段 | 类型 | 用途 |
|------|------|------|
| `auditDimensions` | 数组（维度编号）| 写章审计时只启用这些编号的维度（见 reference/audit.md 37 维度）|
| `fatigueWords` | 数组（词语）| 写章时加入 PRE_WRITE_CHECK 风险扫描；post-write 机械校验规则 4 |
| `chapterTypes` | 数组（章节类型名）| PRE_WRITE_CHECK 的"章节类型"枚举；多章连写时节奏检测基准 |
| `satisfactionTypes` | 数组（爽点类型名）| 写章 PRE_WRITE_CHECK 中的"爽点目标"清单；审计维度 15 爽点虚化的参照 |
| `numericalSystem` | bool | true → 创建并维护 particle_ledger.md；false → 跳过账本相关步骤 |
| `powerScaling` | bool | true → 写章时关注战力数值一致性；审计维度 4 战力崩坏强制启用 |
| `eraResearch` | bool | true → 审计维度 12 年代考据启用，提示 LLM 联网核实历史细节 |

### 写章时的注入（Step 4 PRE_WRITE_CHECK）

在 PRE_WRITE_CHECK 的"风险扫描"行之后，追加体裁注入块：

```
| 体裁高疲劳词 | <fatigueWords 列表> | 全章出现不超过 1 次/词 |
| 本体裁章节类型 | <chapterTypes 列表> | 本章选用其中哪种 |
| 本体裁爽点类型 | <satisfactionTypes 列表> | 本章目标兑现哪种爽点 |
```

### 审计时的注入（Step 7）

- 只启用 `auditDimensions` 列表内的维度编号（以及永远启用的 32/33/38）
- 维度 10 词汇疲劳的"高疲劳词"字段 → 用 `fatigueWords` 填充
- 维度 15 爽点虚化的"爽点类型"字段 → 用 `satisfactionTypes` 填充
- 若 `eraResearch=true` → 启用维度 12 年代考据，并在 system prompt 末尾追加联网搜索指令

### 书没有配置 genre.id 时

- 默认 `genre_id = "other"`，加载 `genres/other.md`
- `other` 体裁启用全部 37 个基础维度，fatigueWords/chapterTypes/satisfactionTypes 为空列表（不额外限制）
