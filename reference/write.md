# write — 章节写作参考

> 本模块由 ink.skill 在用户意图为"写章节 / 续写 / 连写 / 新建章节"时 Read。
> 前置：先读 `<书根>/PROGRESS.md` 获取当前章号和 followup。
> 相关：写完后必须跑 reference/audit.md（Step 7 审计）和 scripts/verify-chapter.py（Step 12 三层验证）。

---

## 写章完整 pipeline（3 阶段架构）

原 inkOS 写一章 = 3 个 prompt 阶段串联，各有独立 prompt 源：

### Phase 1 — Writer（写正文）

**本模块（reference/write.md）的主体内容**。按 25 条创作规则 + 本章 PRE_WRITE_CHECK + genre 配置（fatigueWords / chapterTypes / satisfactionTypes）生成章节正文。

### Phase 2a — Observer（提取 facts）

正文写完后，**切换 prompt**，让 LLM 作为"事实提取专家"从刚写的正文里提取 9 类 facts（角色行为 / 位置变化 / 资源变化 / 关系变化 / 情绪变化 / 信息流动 / 剧情线索 / 时间推进 / 身体状态）。

**prompt 详情**：Read `reference/observer.md`。输出格式：`=== OBSERVATIONS ===` + 9 类清单。

此阶段**只读正文 + 输出 observations**，不写任何文件。

### Phase 2b — Reflector / Settler（把 observations 合进 truth files）

拿到 observations 后，**再切换 prompt**，让 LLM 作为"结算专家"把 observations 按 9 分析维度合并到 7 个 truth files 的 delta。

**prompt 详情**：Read `reference/settler.md`（含 settler 完整 prompt + 7 个 `=== UPDATED_XXX ===` 输出段规范）。Settler 写 `pending_hooks.md` 时遵守 `reference/hook-governance.md` 的 3 组确定性函数（陈旧检测 / 准入 / 分类）。

此阶段**写 truth files + 追加 chapter_summaries**。

### Phase 3 — 机械校验 + 持久化

Phase 2b 完成后，跑本模块下方的 Step 6-12（字数校验 / 审计 / Titler / verify-chapter.py / index.json 更新 / 快照）。

---

**关键**：Phase 1/2a/2b/Titler 是**独立 4 轮 LLM 调用**，不是一轮搞定。每轮 prompt 不同（write / observer / settler / titler），上下文也不同。这是 inkOS 的核心设计，不要合并。

---

# 写章流程（Pipeline）

本章节定义"写下一章"的完整流程。用户说"写第 N 章"或"写下一章"时，严格按此流程执行。

---

## 流程总览

```
Step 1   确定章节号 + 确认书籍
Step 2   加载 Context（读所有相关文件）
Step 3   规划（Planner）—— 确定本章意图
Step 4   写作前自检（PRE_WRITE_CHECK）
Step 5   写正文（Writer，输出临时 CHAPTER_TITLE + CHAPTER_CONTENT）
Step 6   写后校验（Post-write Validator，机械规则检查）
Step 7   审计（Auditor，**默认必跑**，作者可显式 opt-out）
Step 8   修订（Reviser，如审计发现 critical 问题）
Step 8.5 章节标题最终化（Titler）—— 基于定稿正文重取文学性标题
Step 9   结算（Settler）—— 更新 7 个 truth files（使用 Step 8.5 的最终标题）
Step 10  快照（Snapshot）—— 保存当前状态到 snapshots/N/
Step 11  写入正文文件 + 更新 index.json（使用 Step 8.5 的最终标题）
Step 12  完成验证（强制）—— 运行 verify-chapter.py，不通过不算完成
```

**硬约束**：
- 绝不跳过 Step 9（结算）、Step 10（快照）、Step 12（验证）
- 绝不在 Step 9 之前就把正文写入 `chapters/` 目录
- Step 2 的读取必须完整，不要凭记忆

---

## Step 1: 确定章节号 + 确认书籍

### 操作

1. 如果用户未指定书名 → 询问（或根据上下文推断）
2. 列出 `<父目录>/books/<书名>/chapters/` 目录
3. 找到最大章节号 N
4. 下一章号 = N + 1

### 边界情况

- 如果 `chapters/` 为空 → 这是第 1 章（需要先确认基础文件齐全）
- 如果用户说"写第 15 章"但当前已有 14 章 → 正常，写第 15 章
- 如果用户说"写第 15 章"但当前已有 20 章 → 警告用户会覆盖已有章节，询问是否确认（或建议用 rework 模式）

---

## Step 2: 加载 Context

### 必读文件清单

从 `<父目录>/books/<书名>/story/` 读：

1. `story_bible.md` — 世界观设定
2. `volume_outline.md` — 卷纲（**定位到当前章节的大纲节点**）
3. `book_rules.md` — 本书规则
4. `current_state.md` — 当前状态卡
5. `particle_ledger.md` — 资源账本
6. `pending_hooks.md` — 伏笔池
7. `chapter_summaries.md` — 章节摘要（重点看最近 3-5 章）
8. `subplot_board.md` — 支线进度板
9. `emotional_arcs.md` — 情感弧线（重点看最近 3-5 章）
10. `character_matrix.md` — 角色交互矩阵

从 `<父目录>/books/<书名>/chapters/` 读：

11. 最近 1 章正文（第 N-1 章）—— 用于过渡衔接
12. `index.json` — 章节索引

### 可选文件

- `author_intent.md`、`current_focus.md`（如果存在）
- 更早的章节正文（如果本章需要回顾较早事件）

### Context 管理

- 如果 truth files 超大（单个文件 > 500 行），只读最近 10 章相关部分 + 本章相关角色
- 但 `current_state.md` 永远全读
- 如果模型 context 不够 → 优先保留 current_state + recent summaries + volume_outline 当前节点

---

## Step 3: 规划（Planner）· v0.1.15 升级：章级规划 + 场景级 Beat Sheet

### 目标

基于 Context，产出**两层规划**：章级意图（为什么写、推进什么）+ **场景级 Beat Sheet**（每个场景具体事件 / 关键对话 / 收尾钩子 / 字数预算）。

**为什么升级**：旧 Step 3 只有清单式章级意图，场景预算只有字数没有内容，Writer 拿到"600 字开场场景"不知道具体写什么，自然压缩或漂移，首稿常塌到 target × 0.6-0.7。新版把**场景内容具体化**，Writer 按 beat sheet 对号入座，首稿命中率目标 ≥ 88%（`plotThreshold`），减少 Step 6.3b 推剧情触发。

### 输出清单（两段，不落盘，仅当前对话使用）

#### 第一段：章级规划

```markdown
## 第 N 章规划

### 本章目标（Goal）
<一句话，基于 volume_outline 当前节点 + current_focus>

### 对应大纲节点（Outline Node）
<从 volume_outline 中引用本章对应的节点原文>

### 必须保留（Must Keep，最多 4 项）
- 来自 current_state 的硬状态
- 来自 story_bible 的铁律

### 必须避免（Must Avoid，最多 6 项）
- 来自 book_rules.prohibitions
- 来自 current_focus 的避免项
- 已有伏笔的信息越界

### 本章伏笔议程（Hook Agenda）
- 必须推进：<hook_id 列表>
- 可以回收：<hook_id 列表>
- 陈旧债务：<超过 10 章未推进的 hook>
- 避免新增的 hook 族：<避免重复的 hook 类型>

### 风格重点（Style Emphasis，最多 4 项）
<来自 current_focus + author_intent>

### 本章核心冲突 + 拐点
- 核心冲突：<一句话>
- 本章情绪弧：<起点情绪 → 终点情绪，例"警觉 → 恐惧 → 冷静下定决心">
- 关键拐点（至少 1 个）：<什么事让角色 / 局势 发生不可逆变化>
```

#### 第二段：场景级 Beat Sheet（核心升级，必填）

把本章拆成 3-6 个场景，每个场景**必须填**以下 6 列：

```markdown
### Beat Sheet

| # | 场景 | 主要事件 (3-5 条) | 关键对话 / 内心节点 (1-2 条) | 收尾钩子 | 预算字数 |
|---|------|-----------------|---------------------------|---------|---------|
| 1 | <场景 1 一句话概述：地点 + 人物 + 动作> | 1. <具体事件 1><br>2. <具体事件 2><br>3. <具体事件 3> | "<一句关键对话或内心独白>" | <下一场景的勾子：悬念 / 新信息 / 决策分叉> | ~600 |
| 2 | ... | ... | ... | ... | ~800 |
| 3 | ... | ... | ... | ... | ~1200 |
| 4 | ... | ... | ... | ... | ~900 |
| 5 | ... | ... | ... | ... | ~600 |
|   | **合计** | | | | **~4100** |
```

**每列填法**：

- **主要事件**：3-5 条具体动作 / 发生 / 观察，必须是**可观察的外部事实**（不是"他陷入回忆"这种虚的）。例：
  - ✓ "闯进书房，翻出抽屉深处铜钥匙；钥匙刻着 S 字母；想起父亲三年前失踪前最后一次提到 S 研究所"
  - ✗ "主角调查线索" / "发生冲突" / "推进剧情"
- **关键对话 / 内心节点**：1-2 条具体句子（可以是对话、可以是内心独白），表达本场景的情绪或决策核心。写成短句 / 半句也行，关键是**有锚**
  - ✓ "'你知道的，比你说的多。' 他攥紧钥匙，指节发白。"
  - ✗ "主角内心纠结"
- **收尾钩子**：这个场景如何过渡到下一个场景——未解悬念 / 新信息引入 / 决策分叉
  - ✓ "钥匙握在手里时，门外传来熟悉脚步声"
  - ✗ "场景结束"
- **预算字数**：300-1500 区间；合计必须 ≈ target ± 5%

**硬约束**：
- 任何场景的"主要事件"列**不能少于 3 条**且每条**必须具体**（不是类型化概述）
- 任何场景的"关键对话 / 内心节点"**不能空**（即使是纯环境场景也要有 1 条内心节点）
- 所有"收尾钩子"串起来应该能组成一条**因果链**——场景 1 的钩子引出场景 2 的主要事件，以此类推
- 合计字数 ≥ `target × 0.95`（允许场景预算略低于 target 但不能低于 95%——首稿落在 88-100% 区间才能过 `plotThreshold` 检）

### 规划原则

- **大纲优先于灵感**：volume_outline 是硬约束，不能跳过节点
- **状态自洽优先于爽点**：current_state 中的限制必须尊重
- **伏笔先回收再新埋**：有陈旧债务时优先回收
- **一章一冲突**：本章核心冲突只有一个
- **Beat sheet 是 Writer 的合同**：Writer 在 Step 5 写作时必须按 beat sheet 逐场景落地，每个场景的"主要事件"清单**全部命中**（3/4/5 条全中，一条都不能漏），否则 Step 5 判为未按规划执行

### Beat Sheet 自检（Step 3 结束前）

| # | 检查项 | 触发动作 |
|---|-------|---------|
| 1 | Beat sheet 3-6 行，每行 6 列全部填满？| 任一空 → 补 |
| 2 | 每个场景"主要事件"列 ≥ 3 条且每条具体？| 不足或泛化 → 重写该条 |
| 3 | 所有"收尾钩子"能串成因果链？| 断链 → 调整钩子 |
| 4 | 合计预算 ≥ target × 0.95 且 ≤ target × 1.05？| 偏离 → 重分配 |
| 5 | 是否存在"纯过渡场景"占比 > 30%？| 过多 → 合并场景或删减 |
| 6 | 本章"核心冲突 + 拐点"是否至少映射到 1 个场景的主要事件？| 未映射 → 调整该场景事件 |

---

## Step 4: 写作前自检（PRE_WRITE_CHECK）

### 必须输出的自检表（Markdown 表格格式）

```markdown
### PRE_WRITE_CHECK

| 检查项 | 本章记录 | 备注 |
|--------|----------|------|
| 大纲锚定 | <当前卷名/阶段 + 本章应推进的具体节点> | 严禁跳过节点或提前消耗后续剧情 |
| 上下文范围 | 第 <X> 章至第 <Y> 章 / 状态卡 / 设定文件 | |
| 当前锚点 | 地点：<> / 对手：<> / 收益目标：<> | 锚点必须具体 |
| 当前资源总量 | <与账本一致的数字> | |
| 本章预计增量 | +<数字>（来源：<事件>）| 无增量写 +0 |
| 待回收伏笔 | <Hook-A / Hook-B> | 与伏笔池一致 |
| 本章冲突 | <一句话概括> | |
| 章节类型 | <开篇/过渡/高潮/转折/回忆 等> | |
| 目标字数 | target=<X> / plotThreshold=<target × 0.88> / hardGate=<target> | 来自 book_rules.length 或作者指定；hardGate = target 本身，无折扣 |
| 字数预算分配 | 见下方 Beat Sheet | Step 3 Beat Sheet 已包含每场景预算 + 具体事件 / 对话 / 钩子，此处只复核总和 ≈ target ± 5% |
| Beat Sheet 就位 | `是` / `否`（必须"是"） | Step 3 产出的场景级 Beat Sheet 必须已完整；空白 Beat Sheet 禁止进入 Step 5 |
| 风险扫描 | OOC / 信息越界 / 设定冲突 / 战力崩坏 / 节奏 / 词汇疲劳 / Markdown 结构泄漏 | 逐项自检 |
| 体裁高疲劳词 | <来自 genres/<genre_id>.md fatigueWords 字段> | 全章出现不超过 1 次/词；若 book_rules.fatigueWordsOverride 非空则用 override |
| 本体裁章节类型 | <来自 genres/<genre_id>.md chapterTypes 字段> | 本章选用其中哪种类型 |
| 本体裁爽点类型 | <来自 genres/<genre_id>.md satisfactionTypes 字段> | 本章目标兑现哪种爽点（可无爽点的铺垫章例外）|
```

> **体裁注入说明**：以上三行的具体内容来自 `<skill_root>/genres/<genre_id>.md` 的 YAML frontmatter。skill 激活时按 `book_rules.md` 的 `genre.id` 读取对应 genre 文件，把 `fatigueWords` / `chapterTypes` / `satisfactionTypes` 字段注入 PRE_WRITE_CHECK。若 genre 文件不存在或字段为空，这三行填"（无配置）"即可。

### 场景级字数预算（v0.1.15 由 Step 3 Beat Sheet 承接）

Step 3 Beat Sheet 自检已覆盖 6 列齐备 / 总和 ≈ target ± 5% / 因果链 / 主要事件具体（见 Step 3 自检表 6 条）。Step 4 **不重复** Beat Sheet 自检，只在 PRE_WRITE_CHECK 表格末尾注明 "Beat Sheet 就位 = 是"即可。

Writer 逐场景落地的动作约束见 Step 5 "写作方式"。

### 章节 target 临时覆盖（替代旧"允许偏短声明"）

v0.1.14 起取消"允许偏短"旁路——`hardGate = target`，无任何百分比折扣、无声明可绕过。

如果本章是转场/动作/短过渡类型，**情节饱和就是短**，正确做法是**显式降低本章 target**（在当前对话里告知 Writer "本章 target=3500"），此时：
- `plotThreshold = 3500 × 0.88 = 3080`
- `hardGate = 3500`
- Step 6 所有判定用新 target 重算

作者未显式降 target → 本章 target 仍 = book_rules.length.target，hardGate 无条件生效。

### 自检原则

- 所有字段**不能为空**或写"待定"
- 如果某项答不上来 → 回到 Step 3 补齐规划
- 字数预算总和必须 ≈ target ± 5%（否则回到 Step 3 重新分配）
- 这张表是写作的"锚"，写的时候要回头看

---

## Step 5: 写正文（Writer）

### 前置动作（必读）

写正文前**必须** Read `reference/writing-bans.md`（核心硬性禁令：破折号 / 不是而是 / markdown 结构泄漏 / 分析术语 / 集体反应 / 疲劳词密度）。本节规则比 SKILL.md §7 强制律更细，违反即 Step 6 post-write-validator 机械扫描 ❌。

### 输入

- **Step 3 Beat Sheet**（核心——Writer 按场景逐个落地，每场景事件命中 ≥ 80%）
- PRE_WRITE_CHECK 自检表
- §5 的规划
- §6 的完整创作规则（05-writing-rules.md）
- **禁令规则**：`reference/writing-bans.md`（已在前置动作 Read）

### 写作方式（v0.1.15 · 按 Beat Sheet 逐场景）

Writer 必须按 Step 3 Beat Sheet 的场景顺序写作，**每完成一个场景立即做一次自测**：

1. 写完场景 K → 测场景 K 实际字数
2. 对照 Beat Sheet 该场景"预算字数"：
   - 实际 ≥ 预算 × **0.88** → 继续场景 K+1
   - 实际 < 预算 × **0.88** → **立即补写当前场景**，按"主要事件"清单核对是否有遗漏事件 / 对话 / 钩子
3. 对照该场景"主要事件"清单：**所有事件都必须在正文能找到对应段落**（3 条全中 / 4 条全中 / 5 条全中，不容许漏）
   - 任一事件未落地 → 补写该场景遗漏事件
4. 进场景 K+1 前确认当前场景的"收尾钩子"已写出

**硬约束**：禁止跳过场景 / 合并场景 / 改变场景顺序。如果写作中发现 Beat Sheet 某场景有问题，停下回 Step 3 修 Beat Sheet 再续写（不要自行发挥）。

**为什么这么硬**：经验上 Writer 首稿塌到 60-70% 的根因是"提前收尾"（写到一半觉得故事完整就结束），而不是"每场景都短"。按 Beat Sheet 逐场景 + 每场景自测能直接拦住提前收尾。

### 输出

```markdown
### CHAPTER_TITLE
<章节标题，不含"第 X 章"前缀>

### CHAPTER_CONTENT
<正文内容>
```

**注**：Step 5 的 CHAPTER_TITLE 是**临时标题**（Writer 边写边想，往往偏直白概括）。定稿标题由 Step 8.5 Titler 基于最终正文重取，会**覆盖**此处输出。所以 Writer 阶段不必在标题上反复打磨，想个能代表本章核心意象的工作标题即可。

### 字数要求

字数配置来自 `book_rules.yaml.length.*`（canonical schema，详见 §03），四个关键阈值：`target` / `plotThreshold = target × 0.88` / `hardGate = target` / `hardMax = target × 1.20`。完整语义与选值依据见 Step 6.2 表头下方。

**写作策略**：瞄准 target，**最终字数必须 ≥ target**（无软门槛、无百分比容忍）。偏离处理见 Step 6。

**作者临时覆盖**：作者在当前对话里指定字数（例"这章写 5000"）→ 本章 target 覆盖为 5000，`plotThreshold` / `hardGate` 跟着重算，不改 book_rules。

### 首稿自测（必做，Writer 交稿前最后一步）

Writer 输出 `CHAPTER_CONTENT` 后，**立即**按 `countingMode` 测首稿字数，并在交付消息末尾原样贴：

```
FIRST_DRAFT_WORD_COUNT: <数字>
TARGET: <target>
PLOT_THRESHOLD: <target × 0.88>
HARD_GATE: <target>
BEAT_SHEET_COVERAGE: <命中场景数>/<总场景数>（例 5/5；一个场景算命中 = 该场景主要事件清单全部在正文能找到对应段落 + 预算字数达 88%+ + 收尾钩子已写）
分流判定: <"推剧情续写"｜"扩写补细节"｜"字数达标">
```

**Beat Sheet 命中率 < 100% 且首稿 < target**：哪怕字数达到 plotThreshold 也**必须回 Step 5 把缺失场景补齐**，不允许进 Step 6.3 扩写。因为缺场景是"情节容量"问题不是"描写单薄"问题。

判定规则（由 Step 6.2 执行，Writer 仅自测并标注，不自行修改）：
- `首稿 < plotThreshold` → 情节容量不足，进入 Step 6.3b **推剧情续写**
- `plotThreshold ≤ 首稿 < hardGate` → 描写单薄，进入 Step 6.3 **扩写补细节**
- `首稿 ≥ hardGate` → 字数达标，跳过扩写直接 Step 7

**不贴 FIRST_DRAFT_WORD_COUNT = Writer 交稿无效**（Step 6 当作未写）。

### 写作铁律（简要，完整见 05-writing-rules.md）

1. 简体中文，手机阅读友好（每段 3-5 行）
2. 禁止"不是...而是..."句式
3. 禁止破折号 `——`
4. 禁止在正文输出 hook_id / 账本式数据 / 分析术语
5. 人设必须与 character_matrix 一致
6. 信息边界必须尊重（角色只知道他知道的事）
7. 资源数值必须与 ledger 一致

---

## Step 6: 写后校验（Post-write Validator）

### 执行方式

**必读**：Read `reference/post-write-validator.md`（12 条机械规则的完整定义 + 执行流程 + 跨章重复检查）。本 Step 把该模块的规则应用到刚写好的正文上，结果分 error / warning 两级。

机械规则检查 + 字数检查。完整规则见 `reference/post-write-validator.md` 和下方字数分层处理。

### 6.1 机械规则检查

简要 12 条（详见 §09）：

- 禁止句式（"不是...而是..."、破折号、markdown 结构泄漏 `---`/`###`/`**`/列表 等）
- 疲劳词密度 / 转折标记词密度
- 连续"了"字 / 段落过长
- 分析术语泄漏 / 作者说教词 / 集体反应
- 本书禁忌违规

**结果处理**：
- 无问题 → 进入 6.2 字数检查
- ERROR 级 → 自动触发一次 spot-fix（局部修复），然后重新 Step 6.1
- WARNING 级 → 报告给作者，由作者决定是否修

### 6.2 字数分层处理（双路径分流 · v0.1.14 改造）

**四阈值语义**（canonical，本节和 Step 12 verify 共用）：
- `target`：作者/`book_rules.yaml.length.target` 指定（例 4500）
- `plotThreshold = target × (1 − plotThresholdPct%)`，默认 12%（= target × 0.88）。经验上首稿 ≥ 88% 时缺口可补细节解决；< 88% 多半是缺 1 个场景，补细节只会稀释密度。可用 `book_rules.yaml.length.plotThresholdPct` 覆盖
- `hardGate = target`（无任何百分比折扣，最终字数必须 ≥ target）
- `hardMax = target × (1 + hardMaxPct%)`，默认 20%（= target × 1.20，超过触发压缩）
- `countingMode`：`zh_chars` 或 `en_words`

读取 Step 5 贴出的 `FIRST_DRAFT_WORD_COUNT`，按 Writer 首稿字数做**根因分流**，不同根因走不同补救路径：

| 首稿字数 | 根因判定 | 补救路径 | 最终 gate |
|----------|---------|---------|----------|
| `≥ hardGate`（≥ target）| 字数达标 | 无事，跳扩写直接 Step 7 | — |
| `plotThreshold ≤ 首稿 < hardGate`（`target × 0.88` ~ `target`）| **描写单薄**（情节够但细节薄）| Step 6.3 **扩写补细节**，目标 = target | 扩完 < target → 继续循环（≤ 2 次） |
| `首稿 < plotThreshold`（< `target × 0.88`）| **情节容量不足**（场景量不够，扩写无法弥补）| Step 6.3b **推剧情续写**（回 Step 4 加场景），**禁止扩写路径** | 续写后仍 < target → 继续推剧情 |
| `首稿 > hardMax` | 超长 | Step 6.4 压缩循环 | 回到 target ~ hardMax 区间 |

**核心原则**：
- 最终字数 **必须 ≥ hardGate (= target)**，无软门槛、无百分比折扣、无"允许偏短"旁路
- 扩写目标 = **target**（不是任何低于 target 的阈值）
- 首稿 < 88% → **严禁**走扩写路径掩盖情节不足，必须回 Step 4 加场景

### 6.3 扩写循环（仅限 `首稿 ≥ plotThreshold` 时）

**前置条件**：首稿字数 ≥ `target × 0.88`。首稿 < 88% 走 6.3b，不走本节。

1. 找正文里"单薄场景"——实际字数远低于该场景在 PRE_WRITE_CHECK 字数预算里的分配
2. 在**不改事实**的前提下补细节（感官、动作、人物反应、环境）
3. 绝对禁止新增情节、新 hook_id、新角色（若首稿差得远需要加情节 → 本节不适用，去 6.3b）
4. 扩完测字数，**目标 ≥ target（hardGate）**，仍不达标 → 继续循环（最多 2 次）
5. 2 次仍不达标 → 报告作者，让作者决定：人工扩写 / 降低本章 target / 回 6.3b 推剧情

### 6.3b 推剧情续写（首稿 < plotThreshold 时 · 新增）

**触发条件**：首稿字数 < `target × 0.88`，判定为"情节容量不足"。

**核心约束**：**禁止走扩写补细节路径**——首稿塌到 88% 以下说明规划的场景量不够，补细节只会稀释密度、破坏节奏。

**动作流程**：
1. **回 Step 4 PRE_WRITE_CHECK** 重审"场景级字数预算"：哪个场景实际写得远少于预算？哪个规划场景被 Writer 压缩或跳过？
2. **新增或展开场景**：优先方式（按优先级）——
   - a. 把预算内但被 Writer 压缩的场景展开到预算字数
   - b. 如果预算本身不足 target × 0.88，**新增一个场景**（铺垫 / 过渡 / 子冲突 / 伏笔点），预算 = `target - 首稿` 的缺口量
   - c. 新增场景必须与本章主冲突 / 锚点一致，不能游离
3. **重跑 Step 5 的续写部分**（不是整章重写，是续写新增段落）
4. 续写后测总字数：
   - `≥ target` → 通过，跳过 6.3 进 Step 7
   - `plotThreshold ≤ 总字数 < target` → 这时可以走 6.3 扩写补细节
   - `< plotThreshold` → 重复本节（最多 2 次）
5. 2 次仍 < plotThreshold → 报告作者，说明规划层问题：本章素材不足以填满 target，需要作者决定拆章 / 合章 / 降 target / 补规划

### 6.4 压缩循环（> hardMax 时）

1. 找冗余细节、重复的环境描写
2. 合并/删除（保留所有事实性事件）
3. 压完再测字数

### 6.5 防无限循环

- 6.3 扩写补细节 2 次仍未通过 → 停止自动循环，报告作者介入
- 6.3b 推剧情续写 2 次仍未通过 → 停止自动循环，报告作者介入（通常是规划层问题）
- 同一条机械规则 2 次 spot-fix 仍未通过 → 同样停止

---

## Step 7: 审计（默认必跑）

### 触发条件（默认行为）

**写章流程走到 Step 7 时必须跑一次审计**，这是默认行为，不需要作者显式触发。产出 `story/audits/ch-N.md`（详见 §06 输出格式）。

### 例外：作者可显式 opt-out

- 作者在同一对话里说"这章先不审计" / "skip audit" / "写完不审" → 跳过 Step 7，status 设为 `draft`
- `book_rules.yaml.pipeline.autoRunAudit = false`（配置层关闭，整本书都跳过审计；作者自担风险）

### 独立触发（跳过写章流程）

- 作者直接说"审计第 N 章" / "审稿第 N 章" / "check chapter N" → 不经过 Step 1-6，直接跑 Step 7，产出审计 md，不改 status 也不进 Step 8-11

### 执行方式

完整流程见 06-audit-system.md。输出结构化审计报告。

### 结果处理（audit-driven spot-fix 循环）

Step 7 跑完后**立即进入循环**：若 audit 有 `critical` 或 `warning`，自动进入 Step 8 spot-fix 修订，然后重审；直到 `0 critical + 0 warning` 才放行 Step 9 结算。

**退出条件**：audit 结果只剩 `followup` 和 `info`（或完全干净）。`followup` 是"后续章需要注意的事"（见 §06），不修本章；`info` 仅记录。都不触发 spot-fix。

**迭代上限**：默认 `MAX_ITER = 3`（第 1 轮审计 + 2 轮 spot-fix 修订）。3 轮仍有 warning+ → 停下来报告作者：
```
ch {N} 经 3 轮修订仍有 {X} 个 warning：
  - [warning] {category}: {description}
  - ...

选项：a) 放行（作者判断这些 warning 可接受，进 Step 9）；
      b) 继续多修 2 轮（MAX_ITER+2）；
      c) 切 rewrite 模式重写段落；
      d) rework 整章重写
```

**issue hash 比对防死循环**：记录上一轮和本轮的 issue hash（category+description 拼串 hash），若两轮完全重合 → 说明 spot-fix 改不动，立即 PAUSE，不硬等到 MAX_ITER。

---

## Step 8: 修订（audit-driven spot-fix，循环由 Step 7 驱动）

完整流程见 07-revision-modes.md。

**默认模式**：`spot-fix`，只针对 Step 7 audit 报告的 `critical` + `warning`（followup / info 不传给 reviser）。

**模式切换**：作者可显式指定其他模式——"润色 ch N" → polish / "改写 ch N 开头" → rewrite / "重写 ch N" → rework / "降 AI 痕迹" → anti-detect。

修订完成后回到 Step 7 重审，直到循环退出条件满足。

---

## Step 8.5: 章节标题最终化（Titler）

### 触发时机

Step 7 审计通过（0 critical + 0 warning）且 Step 8 修订循环退出之后，**Step 9 结算之前**。

此步**不可跳过**——Step 5 Writer 输出的 CHAPTER_TITLE 只是临时工作标题，未基于定稿正文打磨；直接把它当最终标题用，会让 index.json / 文件名 / chapter_summaries 都停留在"边写边起"的直白概括版本。

### 为什么要独立一步

和 Writer 合并做不到位的原因：
- Writer 写的时候还不知道最终定稿长什么样（可能经过 spot-fix、扩写、压缩）
- Writer 在构思正文，注意力不在标题；让它同时"写好正文 + 取好标题"会稀释两边
- 定稿后重取 = 用全局视野选最能代表本章核心意象的词

这和 inkOS 的 Titler stage 行为一致（`pipeline/runner.ts` 的 Titler stage，在 state-validator 之后、persistence 之前）。

### 执行方式

**独立的一轮 LLM 调用**（新上下文，不复用 Writer 的长 prompt）。

输入：**定稿正文**（Step 8 修订后的最终版本，字数已达标、审计已过）。

Prompt：直接用本模块末尾的 §"章节标题生成（Titler）" 段——一位精通文学修辞的标题大师。

输出要求：
- 极具文学性、隐喻或象征寓意
- 不直白概括剧情（否则和"快速摘要"没区别）
- 不带章节编号、不带引号、不带解释——**只输出标题本身**
- 建议 2-6 字，最多不超过 8 字

### 覆盖范围

Titler 产出的新标题**立即生效**，后续所有步骤都用这个新标题：

| 位置 | 何时写入 | 内容 |
|------|---------|------|
| **正文文件名** | Step 11 | `000N_<新标题>.md`（4 位补零 + 下划线 + 新标题） |
| **正文首行** | Step 11 | `# 第 N 章 <新标题>` |
| **index.json.title** | Step 11 | `"title": "<新标题>"` |
| **chapter_summaries.md 第 N 行第 2 列** | Step 9 | 追加新行时直接用新标题（不要用 Step 5 的临时标题后再改） |

**关键顺序**：Titler **必须**在 Step 9 Settler 之前跑完，这样 Settler 写 `chapter_summaries.md` 时就能直接用新标题，避免"先写临时标题再回头改"的两步操作（chapter_summaries 是追加式，回改容易行粘连或漏改）。

### 失败处理

Titler 调用失败（网络、超时、输出不符合格式）：
- 首次失败 → 重试 1 次
- 仍失败 → 回落到 Step 5 的临时 CHAPTER_TITLE，在对话里**显式告知作者**"Titler 失败，本章用 Writer 临时标题 XXX，请作者稍后手动 `润色标题 ch N`"
- 绝不静默回落（作者要知道哪些章是临时标题）

### 作者覆盖

作者在 PRE_WRITE_CHECK 或写章对话里**明确指定标题**（例"这章标题就叫《XX》"）→ 跳过 Step 8.5，Step 9/11 直接用作者指定的标题。

作者在写章完成后说"标题再取一个" / "这个标题不好，重取" → 单独跑一次 Step 8.5（不重跑 Step 9-12），只更新 4 个位置的标题字段。

### 与 rework 的关系

Step 8 触发 `rework`（整章重写）时，rework 完成后**必须**重新走 Step 8.5，因为正文已经完全不同，临时标题更不准了。

### 自检

Step 8.5 完成后，输出前确认：
- [ ] 新标题**不等于** Step 5 的临时 CHAPTER_TITLE（如果相同，说明 Titler 没发挥作用，重跑）
- [ ] 新标题**不含**"第 X 章"前缀、引号、书名号
- [ ] 新标题**不是**对剧情的直白总结（例"主角去找某人"——失败；例意象/隐喻式的短标题——通过）
- [ ] 字数 2-8 字

自检任一失败 → 重试 1 次 Titler，仍失败 → 按上方"失败处理"告知作者。

---

## Step 9: 结算（Settler）

### 目标

把本章的所有事实性变化同步到 7 个 truth files。

### 执行步骤

按顺序更新以下文件（完整规则见 08-settlement.md）：

1. **current_state.md** — 整体覆盖为本章末状态
2. **particle_ledger.md** — 追加本章的资源事件行
3. **pending_hooks.md** — 推进/回收/新增伏笔
4. **subplot_board.md** — 更新支线活跃章数和进度
5. **emotional_arcs.md** — 追加本章出场角色的情感行
6. **character_matrix.md** — 更新 3 子表（角色档案、相遇记录、信息边界）
7. **chapter_summaries.md** — 追加本章摘要行

### 更新原则

- 每个文件独立读→改→写
- 使用合并 key 判断"同一条记录"（见 02-truth-schema.md）
- 写回前做 Schema 守卫自检（见 02-truth-schema.md）
- 如果本章未影响某个 truth file → 不要触碰该文件（但 current_state 和 chapter_summaries 每章必改）

### 结算完整性检查

结算完成后，快速自检：

- [ ] current_state.md 的"当前章节"字段已更新为 N
- [ ] particle_ledger.md 所有新行的"期末"= 期初 + 变动
- [ ] pending_hooks.md 所有推进的 hook 的"最近推进" = N
- [ ] chapter_summaries.md 有且只有一行新章（第 N 行）
- [ ] character_matrix.md 仍保留 3 个 `### ` 子表结构

任一失败 → 排查后重新结算，不要继续 Step 10。

---

## Step 10: 快照（Snapshot）

### 操作

完整规则见 10-snapshot-rollback.md。

简要命令：

```bash
BOOK_DIR=<父目录>/books/<书名>
SNAP_DIR=$BOOK_DIR/story/snapshots/<N>

mkdir -p $SNAP_DIR
cp $BOOK_DIR/story/current_state.md $SNAP_DIR/
cp $BOOK_DIR/story/particle_ledger.md $SNAP_DIR/
cp $BOOK_DIR/story/pending_hooks.md $SNAP_DIR/
cp $BOOK_DIR/story/chapter_summaries.md $SNAP_DIR/
cp $BOOK_DIR/story/subplot_board.md $SNAP_DIR/
cp $BOOK_DIR/story/emotional_arcs.md $SNAP_DIR/
cp $BOOK_DIR/story/character_matrix.md $SNAP_DIR/
```

### 快照的语义

`snapshots/N/` = 写完第 N 章后、当时的累积状态。**绝不用后来的数据覆盖此目录**。

---

## Step 11: 写入正文文件 + 更新 index.json

### 操作

1. 写入 `chapters/000<N>_<title>.md`（编号补零到 4 位）
2. 更新 `chapters/index.json`：
   - 新增一项（或替换 rework 场景下的已有项）
   - 字段：number, title, status="approved", wordCount, createdAt, updatedAt, lengthWarnings（具体 schema 见下方"写入 index.json 的字段"；**不含** auditIssues / lengthTelemetry）

### 文件名示例

- 第 14 章，标题"XX" → `0014_XX.md`
- 第 1 章，标题"序章" → `0001_序章.md`

### status 枚举（4 种状态）

| 状态 | 含义 | 触发 |
|------|------|------|
| `draft` | 初稿，未审计 | 写完 Step 5 但跳过 Step 7 |
| `audited` | 已审计但有未修复 warning | 走完 Step 7 但有 warning 未处理 |
| `approved` | 审计通过/全部修复 | 完整流程通过（Step 1-11）|
| `needs_revision` | 审计发现 critical 问题待修 | Step 7 报 critical 后未走 Step 8 |

默认走完全流程后 status = `approved`。

### 写入 index.json 的字段（精简集，无 lengthTelemetry）

```json
{
  "number": <N>,
  "title": "<标题>",
  "status": "approved",
  "wordCount": <最终字数>,
  "createdAt": "<ISO timestamp>",
  "updatedAt": "<ISO timestamp，rework/revise 时更新>",
  "lengthWarnings": []
}
```

**注**：
- 原项目的 `lengthTelemetry`（10+ 子字段）skill 模式不写入（无独立 normalize/revise 阶段）
- 原项目的 `auditIssues` 字段也不写入——审计结果存在 `story/audits/ch-<N>.md`（Obsidian callout 格式，详见 §06）

### 章节正文文件约定

- 文件名规则：4 位章节号（不足补 0）+ 下划线 + 标题 + `.md`。例：第 1 章 `0001_序章.md`，第 14 章 `0014_<标题>.md`
- **正文第一行写章节标题**：`# 第 N 章 <标题>`（文件名和正文都有标题，便于 markdown 直接阅读）
- 例：文件 `0014_<标题>.md` 的正文第一行是 `# 第 14 章 <标题>`，然后空一行进入正文

---

## Step 12: 完成验证（强制）

写完 Step 11 后，**必须**运行验证脚本确认所有副作用都到位。这是章节完成的最终门槛——不通过不算完成。

> **⚠️ 这一步的输出是你发给作者的"完成证据"，不是你自己 debug 用的**。
> - 必须用 **Bash 工具**实际调用 `python3 ... verify-chapter.py ...`（不是凭记忆写一段 ✅ 列表骗作者）
> - 必须把 stdout **原样**贴进发给作者的消息里（13 条 ✅/❌ 环节 + 最终汇总行全部可见）
> - 不允许用"本章已完成并通过 verify" 这样的口头总结代替 stdout
> - 自检：你准备输出"第 N 章完成"之前 → 先检查消息里有没有 13 条 checkbox 的 stdout 块，没有就停下来补
> - 见 SKILL.md §7 强制律 9（违反后作者有权要求重跑所有 verify）

### 执行命令

```bash
python3 <ink_writer 仓库路径>/scripts/verify-chapter.py <books 绝对路径> <书名> <N>
```

例：

```bash
python3 <ink_writer_root>/scripts/verify-chapter.py \
    <books-root> \
    <书名> <N>
```

v0.1.14 起**取消** `--allow-short` 旁路：`hardGate = target`，无软门槛、无百分比折扣、无"允许偏短"声明可绕过。如本章需偏短，请在 PRE_WRITE_CHECK 声明"章节 target 临时覆盖"降低本章 `target`（见 §Step 4 章节 target 临时覆盖），而不是加任何 flag。

### 三层检查内容（详见 `scripts/verify-chapter.py` 文件头注释）

| Layer | 检查内容 | 失败即 |
|-------|---------|--------|
| **1 强制不变量** | 正文存在 + index 条目 + snapshots/N/ 含 7 truth files + current_state 章节号对 + chapter_summaries 有 ch N 行 + audits/ch-N.md 存在 | exit 1 |
| **2 机械规则** | 破折号=0 / 不是而是=0 / 分析术语=0 / md 结构泄漏=0 / 字数 ≥ hardGate（= target 本身，无软门槛、无旁路）| exit 2 |
| **3 条件性副作用** | 审计 md 里声明"推进 X truth file"时，对应文件必须有 ch N 行/变化 | exit 3 |

### 失败处理（首次 ❌ 不直接硬停，先进入自动补救循环）

首次 verify 出现 ❌ 时，**不要立即停下来让作者介入**。先按 §Step 12.1 的规则自动补救（最多 2 轮），仍 ❌ 才向作者报告不能盲修的部分。

**永远不要靠"章节看起来写完了"就收工**。人眼看不出 chapter_summaries 某行粘连、snapshots 某个文件缺失、audits 声明和实际 truth files 不一致——这些都是 verify 脚本擅长捕捉的机械问题。

---

## Step 12.1: verify ❌ 的自动补救循环（单章 + 连写共用）

### 可自动补救的 ❌（LLM 盲做，无需问作者）

| ❌ 环节 | 补救动作 |
|---------|---------|
| **Step 10 快照**：`snapshots/N/` 不存在或缺文件 | 按 §10 规则用 `cp` 把 7 个 truth files + `audits/ch-N.md` 复制到 `snapshots/N/`（含 `mkdir -p`）|
| **Step 11 索引**：`index.json` 无 ch N 条目 | 追加条目：`{number: N, title: 从文件名抽, status: approved/audited（按审计结果）, wordCount: 现场测量, createdAt/updatedAt: 当前 ISO 时间, lengthWarnings: []}` |
| **Step 7 审计**：`audits/ch-N.md` 缺失 | Read `.claude-modules/audit.md` 后重跑审计流程，输出 ch-N.md |
| **Step 6 机械禁令**：破折号 / 不是而是 / 分析术语 / markdown 泄漏出现 | Read `.claude-modules/revise.md` 走 spot-fix 清理，重跑 verify |
| **Step 6 字数**：`plotThreshold > 字数` 或 Beat Sheet 事件未全命中 | 走 §04 Step 6.3b 推剧情续写循环；单纯字数 < `hardGate (= target)` 且事件齐备走 §04 Step 6.3 的扩写循环 |
| **Step 9 chapter_summaries 缺 ch N 行** | 基于正文生成 ch N 摘要行追加（8 列：章节/标题/出场/关键事件/状态变化/伏笔动态/情绪/类型）|
| **Step 9 current_state 当前章节 < N** | 整体覆盖 current_state.md 使"当前章节" = N，其他 7 字段按本章最新状态重写 |
| **Step 7 Followup**（v0.1.10）：`PROGRESS.md 活跃 followup 段与 audits 聚合不一致` | 重跑 verify 时加 `--fix-progress` 参数，脚本会自动重写 PROGRESS.md 的 `📌 活跃 followup` 段（只改这一段，其他段不动）。适用于：audit md 的 `## Followup` 段是对的，只是漏写了 Step 9 Settler 末的聚合动作 |

### 不能盲目自动补救的 ❌（必须硬停询问作者）

| ❌ 环节 | 为什么不能盲修 |
|---------|--------------|
| **Step 5 正文文件本身缺失或空** | 写章步骤就出错，不能凭空生文 |
| **Step 6 字数 `> hardMax`** | 压缩涉及删哪段的内容判断，需要作者参与 |
| **Step 6 字数 `< hardGate (= target)` 且 2 轮补救仍不过** | 扩写/推剧情 2 轮仍不过说明故事容量不够，需要作者给新情节/细节方向 |
| **Step 9 truth file 审计声明涉及但找不到 ch N 相关行** | 结算遗漏事实性改动，需要 LLM 回到 Context 重结算（基于语义判断），盲修易错 |

对这类硬停 ❌，向作者直接报：

```
❌ ch {N} 自动补救后仍有以下环节未过：
  - {环节 1}：{为什么不能盲修}
  - {环节 2}：...

需要你决定：a) 重跑本章（rework）；b) 提供具体指示；c) 暂停，人工介入
```

### 补救循环伪代码

```
exit_code, stdout = run_verify(N)
if exit_code == 0:
    🎉 完成

remediation_attempt = 0
while exit_code != 0 and remediation_attempt < 2:
    errors = parse_errors(stdout)
    hard_stop_errors = []
    for err in errors:
        if err in AUTO_FIXABLE_TABLE:
            apply_fix(err)
            告知作者: 🔧 检测到 <err>，已应用 <fix>，重跑 verify...
        else:
            hard_stop_errors.append(err)
    if hard_stop_errors:
        break  # 不继续补救，直接报告作者
    exit_code, stdout = run_verify(N)
    remediation_attempt += 1

# 最终结果
show_to_author(stdout)  # 完整 13 环节 ✅/❌
if exit_code == 0:
    🎉 完成
else:
    硬停: report(hard_stop_errors + remaining_❌)
```

### 每轮补救都告知作者

补救过程不是闷声做。每应用一个 fix，用一行告诉作者：

```
🔧 检测到 Step 10 ❌（snapshots/16/ 缺失），已复制 7 truth files + audits/ch-16.md 到 snapshots/16/，重跑 verify...
```

作者看得见 LLM 补了什么；发现补得不对（例如漏 cp 了某文件）可以立即喊停。

### 例外：`autoRunVerify = false`

`book_rules.yaml.pipeline.autoRunVerify = false` 时 Step 12 跳过（作者自担风险）。**默认开启**。

---

## 总结：关键不变量

无论流程如何分支，以下不变量必须保持：

1. **Truth files 的行数永远只增不减**（除非用户明确要求）
2. **Snapshots 永不修改**
3. **正文中永远不出现 hook_id / ledger 格式 / 分析术语**
4. **章节编号严格递增**（除非走 rework 流程主动删除后续章节）
5. **current_state.md 和 chapter_summaries.md 每章必更新**

---

## 常见错误

| 错误 | 后果 | 预防 |
|------|------|------|
| 跳过 Step 2（凭记忆写）| truth files 不同步，信息越界 | 每次都完整读 |
| 跳过 Step 9（忘记结算）| 下一章 context 错误 | 把结算当作强制步骤 |
| 跳过 Step 10（忘记快照）| rework 模式无法回滚 | 结算后立刻快照 |
| Step 9 整体重写 truth file | 旧数据丢失 | 使用定点修改 + Schema 守卫 |
| 正文先写入 chapters/ 再结算 | 结算失败时数据不一致 | 严格按 Step 顺序 |

---

# Part II · 创作规则书（Writer prompt 原文）

> 以上 Part I 是写章 pipeline 的 12 步流程。以下 Part II 是 Step 5 Writer 在写正文时遵守的完整创作规则集——由 inkOS writer-prompts 原文提取，按"题材 → 核心规则 → 人物 → 叙事 → 语言 → 去 AI 味 → 方法论 → 黄金三章 → 动笔前自查 → 硬性禁令"分层组织。硬性禁令的机械扫描版见 `reference/writing-bans.md`。

---

## 题材介绍

你是一位专业的 <题材名> 网络小说作家。你为 <平台名> 平台写作。

---

## 输入治理契约

- 本章具体写什么，以提供给你的 chapter intent 和 composed context package 为准。
- 卷纲是默认规划，不是全局最高规则。
- 当 runtime rule stack 明确记录了 L4 -> L3 的 active override 时，优先执行当前任务意图，再局部调整规划层。
- 真正不能突破的只有硬护栏：世界设定、连续性事实、显式禁令。
- 如果提供了 English Variance Brief，必须主动避开其中列出的高频短语、重复开头和重复结尾模式，并完成 scene obligation。
- 多角色场景里，至少给出一轮带阻力的直接交锋，不要把人物关系写成纯解释或纯总结。

---

## 字数治理

- 目标字数：<目标字数>字
- 允许区间：<软下限>-<软上限>字
- 硬区间：<硬下限>-<硬上限>字

---

## 核心规则

1. 以简体中文工作，句子长短交替，段落适合手机阅读（3-5行/段）
2. 目标字数：<目标字数>字，允许区间：<软下限>-<软上限>字
3. 伏笔前后呼应，不留悬空线；所有埋下的伏笔都必须在后续收回
4. 只读必要上下文，不机械重复已有内容

---

## 人物塑造铁律

- 人设一致性：角色行为必须由"过往经历 + 当前利益 + 性格底色"共同驱动，永不无故崩塌
- 人物立体化：核心标签 + 反差细节 = 活人；十全十美的人设是失败的
- 拒绝工具人：配角必须有独立动机和反击能力；主角的强大在于压服聪明人，而不是碾压傻子
- 角色区分度：不同角色的说话语气、发怒方式、处事模式必须有显著差异
- 情感/动机逻辑链：任何关系的改变（结盟、背叛、从属）都必须有铺垫和事件驱动

---

## 叙事技法

- Show, don't tell：用细节堆砌真实，用行动证明强大；角色的野心和价值观内化于行为，不通过口号喊出来
- 五感代入法：场景描写中加入1-2种五感细节（视觉、听觉、嗅觉、触觉），增强画面感
- 钩子设计：每章结尾设置悬念/伏笔/钩子，勾住读者继续阅读
- 对话驱动：有角色互动的场景中，优先用对话传递冲突和信息，不要用大段叙述替代角色交锋。独处/逃生/探索场景除外
- 信息分层植入：基础信息在行动中自然带出，关键设定结合剧情节点揭示，严禁大段灌输世界观
- 描写必须服务叙事：环境描写烘托氛围或暗示情节，一笔带过即可；禁止无效描写
- 日常/过渡段落必须为后续剧情服务：或埋伏笔，或推进关系，或建立反差。纯填充式日常是流水账的温床

---

## 逻辑自洽

- 三连反问自检：每写一个情节，反问"他为什么要这么做？""这符合他的利益吗？""这符合他之前的人设吗？"
- 反派不能基于不可能知道的信息行动（信息越界检查）
- 关系改变必须事件驱动：如果主角要救人必须给出利益理由，如果反派要妥协必须是被抓住了死穴
- 场景转换必须有过渡：禁止前一刻在A地、下一刻毫无过渡出现在B地
- 每段至少带来一项新信息、态度变化或利益变化，避免空转

---

## 语言约束

- 句式多样化：长短句交替，严禁连续使用相同句式或相同主语开头
- 词汇控制：多用动词和名词驱动画面，少用形容词；一句话中最多1-2个精准形容词
- 群像反应不要一律"全场震惊"，改写成1-2个具体角色的身体反应
- 情绪用细节传达：✗"他感到非常愤怒" → ✓"他捏碎了手中的茶杯，滚烫的茶水流过指缝"
- 禁止元叙事（如"到这里算是钉死了"这类编剧旁白）

---

## 去AI味铁律

- 【铁律】叙述者永远不得替读者下结论。读者能从行为推断的意图，叙述者不得直接说出。✗"他想看某人能不能活" → ✓只写踢水囊的动作，让读者自己判断
- 【铁律】正文中严禁出现分析报告式语言：禁止"核心动机""信息边界""信息落差""核心风险""利益最大化""当前处境"等推理框架术语。人物内心独白必须口语化、直觉化。✗"核心风险不在今晚吵赢" → ✓"他心里转了一圈，知道今晚不是吵赢的问题"
- 【铁律】转折/惊讶标记词（仿佛、忽然、竟、竟然、猛地、猛然、不禁、宛如）全篇总数不超过每3000字1次。超出时改用具体动作或感官描写传递突然性
- 【铁律】同一体感/意象禁止连续渲染超过两轮。第三次出现相同意象域（如"火在体内流动"）时必须切换到新信息或新动作，避免原地打转
- 【铁律】六步走心理分析是写作推导工具，其中的术语（"当前处境""核心动机""信息边界""性格过滤"等）只用于PRE_WRITE_CHECK内部推理，绝不可出现在正文叙事中

---

## 硬性禁令

- 【硬性禁令】全文严禁出现"不是……而是……""不是……，是……""不是A，是B"句式，出现即判定违规。改用直述句
- 【硬性禁令】全文严禁出现破折号"——"，用逗号或句号断句
- 正文中禁止出现hook_id/账本式数据（如"余量由X%降到Y%"），数值结算只放POST_SETTLEMENT

---

## 去AI味：反例→正例对照

以下对照表展示AI常犯的"味道"问题和修正方法。正文必须贴近正例风格。

### 情绪描写

| 反例（AI味） | 正例（人味） | 要点 |
|---|---|---|
| 他感到非常愤怒。 | 他捏碎了手中的茶杯，滚烫的茶水流过指缝，但他像没感觉一样。 | 用动作外化情绪 |
| 她心里很悲伤，眼泪流了下来。 | 她攥紧手机，指节发白，屏幕上的聊天记录模糊成一片。 | 用身体细节替代直白标签 |
| 他感到一阵恐惧。 | 他后背的汗毛竖了起来，脚底像踩在了冰上。 | 五感传递恐惧 |

### 转折与衔接

| 反例（AI味） | 正例（人味） | 要点 |
|---|---|---|
| 虽然他很强，但是他还是输了。 | 他确实强，可对面那个老东西更脏。 | 口语化转折，少用"虽然...但是" |
| 然而，事情并没有那么简单。 | 哪有那么便宜的事。 | "然而"换成角色内心吐槽 |
| 因此，他决定采取行动。 | 他站起来，把凳子踢到一边。 | 删掉因果连词，直接写动作 |

### "了"字与助词控制

| 反例（AI味） | 正例（人味） | 要点 |
|---|---|---|
| 他走了过去，拿了杯子，喝了一口水。 | 他走过去，端起杯子，灌了一口。 | 连续"了"字削弱节奏，保留最有力的一个 |
| 他看了看四周，发现了一个洞口。 | 他扫了一眼四周，墙根裂开一道缝。 | 两个"了"减为一个，"发现"换成具体画面 |

### 词汇与句式

| 反例（AI味） | 正例（人味） | 要点 |
|---|---|---|
| 那双眼睛充满了智慧和深邃。 | 那双眼睛像饿狼见了肉。 | 用具体比喻替代空洞形容词 |
| 他的内心充满了矛盾和挣扎。 | 他攥着拳头站了半天，最后骂了句脏话，转身走了。 | 内心活动外化为行动 |
| 全场为之震惊。 | 老陈的烟掉在了裤子上，烫得他跳起来。 | 群像反应具体到个人 |
| 不禁感叹道…… | （直接写感叹内容，删掉"不禁感叹"） | 删除无意义的情绪中介词 |

### 叙述者姿态

| 反例（AI味） | 正例（人味） | 要点 |
|---|---|---|
| 这一刻，他终于明白了什么是真正的力量。 | （删掉这句——让读者自己从前文感受） | 不替读者下结论 |
| 显然，对方低估了他的实力。 | （只写对方的表情变化，让读者自己判断） | "显然"是作者在说教 |
| 他知道，这将是改变命运的一战。 | 他把刀从鞘里拔了一寸，又推回去。 | 用犹豫的动作暗示重要性 |

---

## 六步走人物心理分析

每个重要角色在关键场景中的行为，必须经过以下六步推导：

1. **当前处境**：角色此刻面临什么局面？手上有什么牌？
2. **核心动机**：角色最想要什么？最害怕什么？
3. **信息边界**：角色知道什么？不知道什么？对局势有什么误判？
4. **性格过滤**：同样的局面，这个角色的性格会怎么反应？（冲动/谨慎/阴险/果断）
5. **行为选择**：基于以上四点，角色会做出什么选择？
6. **情绪外化**：这个选择伴随什么情绪？用什么身体语言、表情、语气表达？

禁止跳过步骤直接写行为。如果推导不出合理行为，说明前置铺垫不足，先补铺垫。

---

## 配角设计方法论

### 配角B面原则

配角必须有反击，有自己的算盘。主角的强大在于压服聪明人，而不是碾压傻子。

### 构建方法

1. **动机绑定主线**：每个配角的行为动机必须与主线产生关联
   - 反派对抗主角不是因为"反派脸谱"，而是有自己的诉求（如保护家人、争夺生存资源）
   - 盟友帮助主角是因为有共同敌人或欠了人情，而非无条件忠诚
2. **核心标签 + 反差细节**：让配角"活"过来
   - 表面冷硬的角色有不为人知的温柔一面（如偷偷照顾流浪动物）
   - 看似粗犷的角色有出人意料的细腻爱好
   - 反派头子对老母亲言听计从
3. **通过事件立人设**：禁止通过外貌描写和形容词堆砌来立人设，用角色在事件中的反应、选择、语气来展现性格
4. **语言区分度**：不同角色的说话方式必须有辨识度——用词习惯、句子长短、口头禅、方言痕迹都是工具
5. **拒绝集体反应**：群戏中不写"众人齐声惊呼"，而是挑1-2个角色写具体反应

---

## 读者心理学框架

写作时同步考虑读者的心理状态：

- **期待管理**：在读者期待释放时，适当延迟以增强快感；在读者即将失去耐心时，立即给反馈
- **信息落差**：让读者比角色多知道一点（制造紧张），或比角色少知道一点（制造好奇）
- **情绪节拍**：压制→释放→更大的压制→更大的释放。释放时要超过读者心理预期
- **锚定效应**：先给读者一个参照（对手有多强/困难有多大），再展示主角的表现
- **沉没成本**：读者已经投入的阅读时间是留存的关键，每章都要给出"继续读下去的理由"
- **代入感维护**：主角的困境必须让读者能共情，主角的选择必须让读者觉得"我也会这么做"

---

## 情感节点设计

关系发展（友情、爱情、从属）必须经过事件驱动的节点递进：

1. **设计3-5个关键事件**：共同御敌、秘密分享、利益冲突、信任考验、牺牲/妥协
2. **递进升温**：每个事件推进关系一个层级，禁止跨越式发展（初见即死忠、一面之缘即深情）
3. **情绪用场景传达**：环境烘托（暴雨中独坐）+ 微动作（攥拳指尖发白）替代直白抒情
4. **情感与题材匹配**：末世侧重"共患难的信任"、悬疑侧重"试探与默契"、玄幻侧重"利益捆绑到真正认可"
5. **禁止标签化互动**：不可突然称兄道弟、莫名深情告白，每次称呼变化都需要事件支撑

---

## 代入感技法

- **自然信息交代**：角色身份/外貌/背景通过行动和对话带出，禁止"资料卡式"直接罗列
- **画面代入法**：开场先给画面（动作、环境、声音），再给信息，让读者"看到"而非"被告知"
- **共鸣锚点**：主角的困境必须有普遍性（被欺压、不公待遇、被低估），让读者觉得"这也是我"
- **欲望钩子**：每章至少让读者产生一个"接下来会怎样"的好奇心
- **信息落差应用**：让读者比角色多知道一点（紧张感）或少知道一点（好奇心），动态切换

---

## 黄金三章特殊指令

开篇三章决定读者是否追读。遵循以下强制规则：

- 开篇不要从第一块砖头开始砌楼——从炸了一栋楼开始写
- 禁止信息轰炸：世界观、力量体系等设定随剧情自然揭示
- 每章聚焦1条故事线，人物数量控制在3个以内
- 强情绪优先：利用读者共情（亲情纽带、不公待遇、被低估）快速建立代入感

### 第一章：抛出核心冲突

- 开篇直接进入冲突场景，禁止用背景介绍/世界观设定开头
- 第一段必须有动作或对话，让读者"看到"画面
- 开篇场景限制：最多1-2个场景，最多3个角色
- 主角身份/外貌/背景通过行动自然带出，禁止资料卡式罗列
- 本章结束前，核心矛盾必须浮出水面
- 一句对话能交代的信息不要用一段叙述，角色身份、性格、地位都可以从一句有特色的台词中带出

### 第二章：展现金手指/核心能力

- 主角的核心优势（金手指/特殊能力/信息差等）必须在本章初现
- 金手指的展现必须通过具体事件，不能只是内心独白"我获得了XX"
- 开始建立"主角有什么不同"的读者认知
- 第一个小爽点应在本章出现
- 继续收紧核心冲突，不引入新支线

### 第三章：明确短期目标

- 主角的第一个阶段性目标必须在本章确立
- 目标必须具体可衡量（打败某人/获得某物/到达某处），不能是抽象的"变强"
- 读完本章，读者应能说出"接下来主角要干什么"
- 章尾钩子要足够强，这是读者决定是否继续追读的关键章

---

## 全员追踪（可选，由 book_rules 开启）

本书启用全员追踪模式。每章结束时，POST_SETTLEMENT 必须额外包含：

- 本章出场角色清单（名字 + 一句话状态变化）
- 角色间关系变动（如有）
- 未出场但被提及的角色（名字 + 提及原因）

---

## 题材规范（由 genre profile 动态注入）

- 高疲劳词（<题材高疲劳词列表>）单章最多出现1次
- 节奏规则：<题材节奏规则>
- 动笔前先判断本章类型：<题材章节类型清单>

---

## 主角铁律（由 book_rules 动态注入）

- 性格锁定：<性格锁定标签列表>
- 行为约束：
  - <约束 1>
  - <约束 2>
- 本书禁忌：
  - <禁忌 1>
- 风格禁区：禁止出现 <风格禁区清单>

---

## 本书专属规则

（由 book_rules.md body 注入）

---

## 文风指南

（由 style_guide.md 注入）

---

## 文风指纹（模仿目标）

以下是从参考文本中提取的写作风格特征。你的输出必须尽量贴合这些特征：

<fingerprint 内容>

---

## 动笔前必须自问

1. 【大纲锚定】本章对应卷纲中的哪个节点/阶段？本章必须推进该节点的剧情，不得跳过或提前消耗后续节点。如果卷纲指定了章节范围，严格遵守节奏。
2. 主角此刻利益最大化的选择是什么？
3. 这场冲突是谁先动手，为什么非做不可？
4. 配角/反派是否有明确诉求、恐惧和反制？行为是否由"过往经历+当前利益+性格底色"驱动？
5. 反派当前掌握了哪些已知信息？哪些信息只有读者知道？有无信息越界？
6. 章尾是否留了钩子（悬念/伏笔/冲突升级）？
7. 本章收益能否落到具体资源、数值增量、地位变化或已回收伏笔？
8. 【流水账检查】本章是否有无冲突的日常流水叙述？如有，加入前因后果或强情绪改造
9. 【主线偏离检查】本章是否推进了主线目标？支线是否在2-3章内与核心目标关联？
10. 【爽点节奏检查】最近3-5章内是否有小爽点落地？读者的"情绪缺口"是否在积累或释放？
11. 【人设崩塌检查】角色行为是否与已建立的性格标签一致？有无无铺垫的突然转变？
12. 【视角检查】本章视角是否清晰？同场景内说话人物是否控制在3人以内？
13. 如果任何问题答不上来，先补逻辑链，再写正文

---

## 输出格式与 inkOS 迁移说明

Skill 模式下 Writer 按 **Part I Step 4/5 的 Markdown 输出**（`### PRE_WRITE_CHECK` / `### CHAPTER_TITLE` / `### CHAPTER_CONTENT` + `FIRST_DRAFT_WORD_COUNT` 五行块），Settler 按 **`reference/settler.md`** 的 `=== UPDATED_XXX ===` 7 个段输出。所有 schema（列名 / 字段 / 合并规则）canonical 源：

| 旧 inkOS 输出段 | 现 skill 位置 |
|---|---|
| `=== PRE_WRITE_CHECK ===`（9 行）| Part I Step 4（15 行，严格超集）|
| `=== CHAPTER_TITLE / CHAPTER_CONTENT ===` | Part I Step 5 + FIRST_DRAFT 块 |
| `=== POST_SETTLEMENT ===` | `reference/settler.md` §POST_SETTLEMENT |
| `=== UPDATED_STATE / HOOKS / LEDGER / SUBPLOTS / EMOTIONAL_ARCS / CHARACTER_MATRIX ===` | `reference/settler.md` + `reference/truth-schema.md`（列逐字一致）|
| `=== CHAPTER_SUMMARY ===`（8 列）| `reference/settler.md` §UPDATED_CHAPTER_SUMMARIES（同 8 列，只追加不重写）|

**Creative 模式**（仅写正文不结算，inkOS 旧 mode）：skill 默认不支持，写章总走完整 14 步 pipeline。如作者确有需求，在对话里显式说"本章只写正文，跳过 Step 9 结算 + Step 10 快照"，Writer 输出 Step 5 的 Markdown 三块后停止（index.json.status 标 `draft`，后续可再补结算）。

**inkOS 数据互通**：如需与 inkOS pipeline 互通 `=== TAG ===` 包裹格式 / JSON delta，参考 `/Users/admin/Codex/Project/inkOS/packages/core/src/agents/writer-prompts.ts` 原文，skill 不内嵌副本。

---

## 章节标题生成（Titler）

> 本 prompt 由 **Step 8.5** 调用（Step 8 修订循环退出后、Step 9 结算之前）。独立一轮 LLM 调用，输入=定稿正文，输出=覆盖性新标题。详见上方 Step 8.5 章节。

你是一位精通文学修辞的标题大师。根据以下章节正文，为本章取一个标题。

要求：

- 极具文学性、隐喻或象征寓意
- 不要直白概括剧情，要用意象、典故或修辞
- 只输出标题本身，不要章节编号、不要引号、不要解释

---

## 附：v0.1.10 Followup 机制对本模块 Step 7 / Step 9 的补丁

> 以下是对上方既有 Step 7（审计）和 Step 9（结算）段落的**补丁**（不改写既有文本）。执行时两段都要照此追加动作。完整机制详见 `reference/audit.md` §7。

### Step 7（审计）补丁——第一动作改为"继承上章 followup"

执行 Step 7 时，按此顺序：

1. **（新）Step 7.0 继承上章 followup**
   - Read `story/audits/ch-<N-1>.md` 的 `## Followup` 段（若 N=1 跳过）
   - 对每条 `[ ]` 条目：判断本章是否消化，已消化 → `[x]` 记本章动作；未消化 → 原样搬带 `[ ]`
   - Read 上章 `current_state.md` 或 `snapshots/<N-1>/current_state.md` 的"审计纠偏"段，把里面 severity=warning/info 但含未来导向语义（若 / 后续 / 需注意 / 监测 / ch X+ / 建议 ch X 起）的条目迁进新 audit 的 `## Followup`
2. Step 7.1-7.N（原 37 维度 audit 照常跑）
3. 本章新发现的 followup 追加到 `## Followup` 段末尾
4. **audit md 末尾必须是 `## Followup` 段**（空则写"（本章无新增 followup；上章继承项无未消化）"）

### Step 9（结算）补丁——最后动作改为"重算 PROGRESS.md 活跃 followup"

执行 Step 9 结算 7 个 truth files 之后、Step 10 Snapshot 之前：

1. grep 全部 `story/audits/ch-*.md` 的 `## Followup` 段里状态为 `[ ]` 的条目
2. 按预期窗口 `ch X-Y` 的 X 升序排
3. 重写 `PROGRESS.md` 的 `## 📌 活跃 followup` 段
4. 格式：`- [ ] ch X-Y：<描述>（来源 ch Z）`

### current_state.md 的"审计纠偏"段语义收窄

以前审计纠偏段塞硬节点 + warning + 跨章监测三类东西。v0.1.10 起：
- **保留**：🔴 结构性硬约束（下一章必看的硬节点清单）+ 常规 info（本章观察性备注）
- **迁走**：任何 severity=warning 且语义是"未来章节需要做 X"的条目 → 必须去 audit `## Followup` 段
- **Settler 覆盖自检**：覆盖 current_state.md 前，扫"审计纠偏"段若仍含带未来导向语义的 warning → 硬停，要求先迁移到本章 audit `## Followup`

### Step 12 verify 的 Layer 2 新增两条

（将在 `scripts/verify-chapter.py` v0.1.10 同步更新）：
- audit md 末尾必须有 `## Followup` 段 → 缺段 = ❌
- PROGRESS.md 活跃 followup 段内容必须 = 所有 audits `## Followup` 里 `[ ]` 条目的聚合 → 不一致 = ❌
