# revise — 章节修订参考

> 本模块由 ink.skill 在用户意图为"润色 / 修订 / 重写 / 扩写 / 压缩"时 Read。
> 修订后必须跑 reference/audit.md 重新审计，通过后才能更新 index.json 的 status。

---

# 修订系统

## 系统角色

你是一位专业的<题材名>网络小说修稿编辑。你的任务是根据审稿意见对章节进行修正。

（若本书在 `book_rules.md` 中配置了主角锁定，system prompt 会追加：`主角人设锁定：<主角名>，<性格锁定列表>。修改不得违反人设。`）

## 前置动作（必读）

修订任何正文前**必须** Read `reference/writing-bans.md`（核心硬性禁令：破折号 / 不是而是 / markdown 结构泄漏 / 分析术语 / 集体反应 / 疲劳词密度）。**修订劣化最常见场景就是引入新的禁令违规**（修一个问题引入两个新问题），事先把禁令加载进 context 能显著降低这类失败。

## 5 种修订模式

### polish 润色

**触发**："润色第 N 章"

**改动幅度**：单句 / 表达层面

**规则**：

> 润色：只改表达、节奏、段落呼吸，不改事实与剧情结论。禁止：增删段落、改变人名/地名/物品名、增加新情节或新对话、改变因果关系。只允许：替换用词、调整句序、修改标点节奏

### rewrite 改写

**触发**："改写第 N 章"

**改动幅度**：段落级（问题段落及其直接上下文）

**规则**：

> 改写：允许重组问题段落、调整画面和叙述力度，但优先保留原文的绝大部分句段。除非问题跨越整章，否则禁止整章推倒重写；只能围绕问题段落及其直接上下文改写，同时保留核心事实与人物动机

### rework 重写（特殊路径）

**触发**："重写第 N 章"

**改动幅度**：整章重生成

**规则**：

> 重写：可重构场景推进和冲突组织，但不改主设定和大事件结果

**⚠️ 特殊执行路径**：rework 不是打补丁，是**完全重生成整章**。skill 里按以下 5 步执行（对应 inkOS `runner.ts::reworkChapterFromPreviousSnapshot`）：

1. **校验前章快照**：`snapshots/(N-1)/` 必须含完整 7 个 truth files + `audits/ch-(N-1).md`，缺任一文件 → 硬停问作者（不完整无法恢复基线）。若作者要 rework 的是 ch 1，用 `snapshots/0/`（新建书时产的初始快照）
2. **恢复前章末状态**：`cp snapshots/(N-1)/*.md story/` 把 7 个 truth files 覆盖回 ch N-1 结束时的状态。注意 `audits/` 子目录不 copy，保留当前 `story/audits/` 不动
3. **删除 N 起所有章节**：rm `chapters/000N_*.md` 及所有 `chapters/000M_*.md`（M > N），同时 rm `story/audits/ch-N.md` 及更高章的 audit、rm `story/snapshots/N/` 及更高章的 snapshot
4. **更新 index.json**：删除 number ≥ N 的所有条目
5. **走完整写章 pipeline**：Read `reference/write.md`，从 Step 1 开始走 14 步（含 Step 8.5 Titler / Step 9 Settler / Step 10 Snapshot / Step 12 verify 全部），产全新 ch N。若作者希望继续重写 ch N+1 后续章节，手动逐章触发"写第 N+1 章"

**对作者的警告**（rework 触发时必须先告知）：

> ⚠️ rework ch N 会**丢弃** ch N+1 到最新章的全部内容（它们基于旧 ch N 状态接力写，与新 ch N 语义不一致）。被丢弃的章节数 = M - N + 1（M = 最新章）。你确认吗？ [y/n]

得到 `y` 才执行 Step 3 删除。

因此 rework 会更新全部 7 个真相文件，而非 partial-patch 模式的 3 个。

### anti-detect 反检测改写

**触发**："反检测第 N 章" / "降 AI 痕迹"

**改动幅度**：全文扫描 + 定向改写

**规则**：

> 反检测改写：在保持剧情不变的前提下，降低AI生成可检测性。
>
> 改写手法（附正例）：
> 1. 打破句式规律：连续短句 → 长短交替，句式不可预测
> 2. 口语化替代：✗"然而事情并没有那么简单" → ✓"哪有那么便宜的事"
> 3. 减少"了"字密度：✗"他走了过去，拿了杯子" → ✓"他走过去，端起杯子"
> 4. 转折词降频：✗"虽然…但是…" → ✓ 用角色内心吐槽或直接动作切换
> 5. 情绪外化：✗"他感到愤怒" → ✓"他捏碎了茶杯，滚烫的茶水流过指缝"
> 6. 删掉叙述者结论：✗"这一刻他终于明白了力量" → ✓ 只写行动，让读者自己感受
> 7. 群像反应具体化：✗"全场震惊" → ✓"老陈的烟掉在裤子上，烫得他跳起来"
> 8. 段落长度差异化：不再等长段落，有的段只有一句话，有的段七八行
> 9. 消灭"不禁""仿佛""宛如"等AI标记词：换成具体感官描写

### spot-fix 定点修复（默认模式）

**触发**："修第 N 章的 X 问题" / "spot-fix 第 N 章"

**改动幅度**：问题句及其前后各一句

**规则**：

> 定点修复：只修改审稿意见指出的具体句子或段落，其余所有内容必须原封不动保留。修改范围限定在问题句子及其前后各一句。禁止改动无关段落

**附加硬约束**：

- spot-fix 只能输出局部补丁，禁止输出整章改写
- `TARGET_TEXT` 必须能在原文中**唯一命中**
- 如果需要大面积改写，说明无法安全 spot-fix，并让 PATCHES 留空（由用户换模式重试）

## 通用修稿原则

1. 按模式控制修改幅度
2. 修根因，不做表面润色
3. 资源/数值错误必须精确修正，前后对账
4. 伏笔状态必须与伏笔池同步
5. 不改变剧情走向和核心冲突
6. 保持原文的语言风格和节奏
7. 修改后同步更新状态卡、账本、伏笔池
8. 保持章节字数在目标区间内（依据 `book_rules.md` frontmatter 的 `length` 配置，详见 reference/truth-schema.md）；只有在修复关键问题确实需要时才允许轻微偏离

### 严重度过滤（audit-driven spot-fix 专用）

当 reviser 被 §04 Step 7-8 的 audit-driven 循环调起时（不是作者手动触发），input 里的 audit issues **只处理 `critical` 和 `warning`**：

- `critical` → 必须修
- `warning` → 必须修
- **`followup` → 忽略**（这是后续章节跟进项，不是本章写作问题，见 §06）
- **`info` → 忽略**（纯说明，不需要动作）

如果 audit 只剩 followup + info（无 critical/warning），**不启动 reviser**——直接进 Step 9 结算。

作者手动触发修订（"润色 ch N" / "改写 ch N"）时忽略此过滤，按作者指令执行。

## 输出格式

### spot-fix 模式

```
=== FIXED_ISSUES ===
(逐条说明修正了什么，一行一条；如果无法安全定点修复，也在这里说明)

=== PATCHES ===
(只输出需要替换的局部补丁，不得输出整章重写。格式如下，可重复多个 PATCH 区块)
--- PATCH 1 ---
TARGET_TEXT:
(必须从原文中精确复制、且能唯一命中的原句或原段)
REPLACEMENT_TEXT:
(替换后的局部文本)
--- END PATCH ---

=== UPDATED_STATE ===
(更新后的完整状态卡)

=== UPDATED_LEDGER ===
(更新后的完整资源账本，遵循 7 列 schema 含事件ID)

=== UPDATED_HOOKS ===
(更新后的完整伏笔池)

=== UPDATED_SUBPLOTS ===
=== UPDATED_EMOTIONAL_ARCS ===
=== UPDATED_CHARACTER_MATRIX ===
=== UPDATED_CHAPTER_SUMMARIES ===
```

### polish / rewrite / anti-detect 模式

```
=== FIXED_ISSUES ===
(逐条说明修正了什么，一行一条)

=== REVISED_CONTENT ===
(修正后的完整正文)

=== UPDATED_STATE ===
(更新后的完整状态卡)

=== UPDATED_LEDGER ===
(更新后的完整资源账本，遵循 7 列 schema 含事件ID)

=== UPDATED_HOOKS ===
(更新后的完整伏笔池)

=== UPDATED_SUBPLOTS ===
=== UPDATED_EMOTIONAL_ARCS ===
=== UPDATED_CHARACTER_MATRIX ===
=== UPDATED_CHAPTER_SUMMARIES ===
```

## Sentinel 哨兵占位符系统

4 个"附加真相文件"（subplots / emotional_arcs / character_matrix / chapter_summaries）默认**不改**，LLM 只在真正影响到它们时才输出新版。否则原样复制 sentinel 字符串，持久化层检测到 sentinel 就跳过 writeFile，保留磁盘原文件不动。

### 4 个 sentinel 字符串（中文）

- `☆ 支线进度板无变动 ☆`
- `☆ 情感弧线无变动 ☆`
- `☆ 角色交互矩阵无变动 ☆`
- `☆ 章节摘要无变动 ☆`

### 每个 UPDATED_XXX 段的 prompt 指令

```
=== UPDATED_SUBPLOTS ===
默认原样输出 `☆ 支线进度板无变动 ☆`。仅当本次修订实际影响了支线推进、状态或回收时，才输出完整的支线进度板（保留表头，按原列顺序）。

=== UPDATED_EMOTIONAL_ARCS ===
默认原样输出 `☆ 情感弧线无变动 ☆`。仅当本次修订实际改变了角色的情绪状态、触发事件或弧线方向时，才输出完整的情感弧线表。

=== UPDATED_CHARACTER_MATRIX ===
默认原样输出 `☆ 角色交互矩阵无变动 ☆`。仅当本次修订引入/删除角色、改变角色关系或角色信息边界时，才输出完整的 3 子表角色交互矩阵（### 角色档案 / ### 相遇记录 / ### 信息边界）。

=== UPDATED_CHAPTER_SUMMARIES ===
默认原样输出 `☆ 章节摘要无变动 ☆`。仅当本次修订改变了本章的关键事件、出场人物、状态变化或章节类型时，才输出完整的章节摘要表（保留 8 列结构）。
```

## 修稿上下文（必读真相文件）

reviser LLM 的 user prompt 中会拼入以下上下文：

- **审稿问题列表**（来自 auditor 产出的 issues，按 `[severity] category: description` + `建议: suggestion` 格式罗列）
- `current_state.md`
- `particle_ledger.md`
- `pending_hooks.md`（governed mode 用 `buildGovernedHookWorkingSet`，否则 `filterHooks`）
- `volume_outline.md`
- `story_bible.md`（非 governed mode 下）
- `character_matrix.md`（governed mode / 过滤后）
- `chapter_summaries.md`（filterSummaries）
- `subplot_board.md`（filterSubplots）
- `emotional_arcs.md`（filterEmotionalArcs）
- `style_guide.md`（或 `book_rules.md` body fallback）
- `parent_canon.md`（番外专用）
- `fanfic_canon.md`（同人专用，额外约束"角色对话必须保留原作语癖"）
- 若 `book_rules.md` frontmatter 的 `length` 已配置 —— 字数护栏段：`target / plotThreshold (= target × 0.88) / hardGate (= target) / hardMax`

## 质量 Gate（v0.1.10+：修订后必须重跑 audit，且把对比贴给作者）

> inkOS 原版有代码层自动 gate（`runner.ts::reviseDraft` 持久化段比对修订前后的 blocking issues 和 AI-tell 计数，劣化就回滚）。**skill 没有代码执行能力，做不到自动 gate**，所以这个机制降级为**LLM 自律 + 强制输出证据**——同级别严格度于 SKILL.md §7 强制律 9 验证必贴律。

### 强制律（与 SKILL.md §7 规则 9 同级）

任何 revise 动作（polish / rewrite / spot-fix / anti-detect，rework 走独立 pipeline 不适用）**完成后、递交之前**：

1. **必须** Read `reference/audit.md`，对修订后的正文跑完整 37 维 audit 流程
2. **必须**把以下对比**原样**贴给作者，放在发给作者的消息里（不是 debug log）：

```
## 修订前 audit
- critical: X 条
- warning: Y 条
- info: Z 条
- followup: W 条

## 修订后 audit（重跑完整 37 维）
- critical: X' 条
- warning: Y' 条
- info: Z' 条
- followup: W' 条
```

3. **判定规则**（LLM 自检）：

| 情况 | 判定 | 动作 |
|------|------|------|
| X' = 0 且 Y' ≤ Y | ✅ 修订成功 | 递交，更新 index.json status |
| X' > 0 或 Y' > Y | ❌ **修订劣化** | **回滚**（丢弃本次修订输出，正文恢复修订前版本），向作者报告具体哪条 issue 恶化了，询问："a) 换模式重试（spot-fix → rewrite → rework）；b) 忽略这次修订；c) 你人工介入" |
| X' = X 且 Y' = Y 但 issue 内容变了 | ⚠️ 中性 | 贴对比给作者决定是否采用 |

### 视为违规（= 修订未完成）的 4 种情形

同 SKILL.md §7 规则 9 的"验证必贴律"同构：

- 只口头总结（"修好了"/"issues 清零"）而不贴对比
- 只跑机械 grep（破折号 / 不是而是），不跑完整 37 维 audit
- 声称"audit 通过"但未实际 Read audit.md 走流程——自检：*我 Read audit.md 了吗？没有 → 未跑*
- 贴截取版（只贴汇总 X/Y/Z 而不对比前后）

### 自检触发点

准备说"修订完成"/"修好了"/"已处理 issues"/"更新 status approved"**之前** → 检查消息里上方 3 行内有无"修订前/后 audit 对比块"，没有就停下来补跑 audit + 贴对比。

### 为什么这么严

spot-fix 的最常见失败模式是"**修一个问题引入两个新问题**"（LLM 在替换句子时用到禁词、或拉长句子导致疲劳词密度上升）。没有强制重审 gate，劣化修订会静默进入 status approved，污染后续章节的 audit 基线（因为下一章的 audit 会以为 ch N 是干净的，实际上坏在那里没人发现）。此 gate 把"改完就完"的懒惰路径堵死。

## 持久化写入矩阵

| 模式 | 写入文件数 | 写入哪些 |
|---|---|---|
| polish / rewrite / anti-detect / spot-fix | 3 + (0..4) | `current_state` / `particle_ledger`（经 `mergeLedgerForPersistence`）/ `pending_hooks`（经 `mergeTableMarkdownByKey`）/ 另加 0–4 个附加真相文件（仅当 LLM 输出非 sentinel 时）|
| rework | 7 | 走完整写章 pipeline，7 个真相文件全部更新 |

---

## 附录：字数规范化独立 Prompt（length-normalizer）

> 从 inkOS length-normalizer.ts 迁入。用于在首稿字数与 target 偏差较大时进行独立的字数规范化修订。
> 与 compress/expand 修订模式的区别：compress/expand 服务于**风格性修订**（去啰嗦、加丰满），length-normalizer 服务于**机械性规范化**（首稿严重偏离 target 时自动调用，一次修正不递归）。

### 使用场景

- 首稿字数 > `hardMax` → 触发压缩模式
- 首稿字数 < `hardGate (= target)` → 触发扩写模式（v0.1.14 起无"允许偏短"旁路；如需偏短，请在 PRE_WRITE_CHECK 里临时覆盖本章 target）
- 由写章 pipeline Step 6 自动调用，不需要作者手动触发

### System Prompt（压缩和扩写通用）

```
你是一位章节长度修正器。你的任务是对章节正文做一次单次修正，只能执行一次，不得递归重写。

修正目标：
- <compress|expand> 章节长度到给定目标区间
- 保留章节原有事实、关键钩子、角色名和必须保留的标记
- 不要引入新的支线、未来揭示或额外总结
- 不要在正文外输出任何解释
```

### User Prompt

```
请对下面正文做一次<压缩|扩写>修正。

## Length Spec
- Target: <target>
- Plot Threshold: <plotThreshold>（= target × 0.88，首稿命中阈值）
- Hard Gate: <hardGate>（= target，最终硬门槛，无折扣）
- Hard Max: <hardMax>
- Counting Mode: <countingMode>

## Current Count
<当前字数>

## Correction Rules
- 只修正一次，不要递归
- 保留正文中的关键标记、人物名、地点名和已有事实
- 不要凭空新增子情节
- 不要插入解释性总结或分析
- 输出修正后的完整正文，不要加标签

## Chapter Content
<正文内容>
```

### 输出处理

- LLM 输出完整修正后正文（不加 === TAG === 标签）
- 若 LLM 输出包含 markdown 代码块（` ``` `），提取代码块内容
- 若输出包含常见包裹行（"以下是修正后的正文"等）则去除
- 修正后字数仍低于 `hardGate` 或高于 `hardMax`：报 warning，但不再次递归（最多修正一次）——后续由写章 pipeline Step 6.3/6.3b 的扩写/推剧情循环接手

### 触发逻辑（来自 write pipeline Step 6）

```
originalCount = countChapterLength(content, countingMode)

if originalCount > hardMax:
    mode = "compress"
elif originalCount < hardGate:  # hardGate = target，v0.1.14 起无 allowShort 旁路
    mode = "expand"
else:
    mode = "none"（跳过）

if mode != "none":
    调用 length-normalizer，一次修正
```

### compress/expand 不是 revise mode（澄清）

旧版文档曾暗示 revise.md 有 "compress/expand 修订模式"。**这是错的**。inkOS 源码 `reviser.ts:37` 明确定义：

```typescript
export type ReviseMode = "polish" | "rewrite" | "rework" | "anti-detect" | "spot-fix";
```

5 种 mode，**没有 compress/expand**。

**compress/expand 是 length-normalizer 的内部模式**（见上方 §触发逻辑），不是 revise mode。作者**不能**用"压缩 ch N" / "扩写 ch N"这类触发词手动调 revise——字数偏离由写章 Step 6 自动调 length-normalizer 处理，一次修正不递归。如果作者想手动对章节做风格上的"缩写/扩展"，走 `rewrite`（段落级改写）或 `polish`（只改表达）。
| truth files 更新 | 不更新（字数规范化不改事实）| 更新受影响的 truth files |
