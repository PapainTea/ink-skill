# revise — 章节修订参考

> 本模块由 ink.skill 在用户意图为"润色 / 修订 / 重写 / 扩写 / 压缩"时 Read。
> 修订后必须跑 reference/audit.md 重新审计，通过后才能更新 index.json 的 status。

---

# 修订系统

## 系统角色

你是一位专业的<题材名>网络小说修稿编辑。你的任务是根据审稿意见对章节进行修正。

（若本书在 `book_rules.md` 中配置了主角锁定，system prompt 会追加：`主角人设锁定：<主角名>，<性格锁定列表>。修改不得违反人设。`）

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

**⚠️ 特殊执行路径**：rework 不走修订 LLM 的 partial-patch 流程，而是：
1. 预校验 `snapshots/(N-1)/` 完整性（含 `current_state.md` + `pending_hooks.md`）
2. `restoreState(N-1)` 恢复所有真相文件到上一章完成态
3. 删除 `chapters/000N_*.md` 及所有 > N 的章节
4. 从 `chapters/index.json` 删除 ch ≥ N 条目
5. 清理 `pipeline-cache/N/` 避免 stale cache
6. `refreshMemoryFromRestoredState(N-1)` 重建 memory.db
7. 调 `_writeNextChapterLocked` 走**完整写章 pipeline**（planner → composer → writer → settler → auditor → …）

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
8. 保持章节字数在目标区间内（依据 `book_rules.yaml.length` 配置，详见 §03）；只有在修复关键问题确实需要时才允许轻微偏离

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
- 若 `book_rules.yaml.length` 已配置 —— 字数护栏段：`target / softMin-softMax / hardMin-hardMax`（详见 §03）

## 质量 Gate

Reviser 修订结果只有在**不让劣化指标变坏**的前提下才被接受：

- blocking 级审稿问题数**不得增加**
- AI-tell（AI 痕迹标记词）计数**不得上升**
- 若劣化 → runner 层回滚到修订前的版本，并可触发重试或升级模式（spot-fix → rewrite → rework）

此 gate 由 `runner.ts` 的 reviseDraft 持久化段实施，不是 reviser 本身的约束。

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
- 首稿字数 < `softMin`，且 PRE_WRITE_CHECK 未声明"允许偏短" → 触发扩写模式
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
- Soft Range: <softMin>-<softMax>
- Hard Range: <hardMin>-<hardMax>
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
- 修正后字数仍在 soft range 之外时：报 warning，但不再次递归（最多修正一次）

### 触发逻辑（来自 write pipeline Step 6）

```
originalCount = countChapterLength(content, countingMode)

if originalCount > hardMax:
    mode = "compress"
elif originalCount < softMin and not PRE_WRITE_CHECK.allowShort:
    mode = "expand"
else:
    mode = "none"（跳过）

if mode != "none":
    调用 length-normalizer，一次修正
```

### 与 revise.md compress/expand 模式的区别

| 维度 | length-normalizer（本附录）| compress/expand 修订模式 |
|------|--------------------------|------------------------|
| 触发方 | 写章 pipeline 自动调用 | 作者手动触发 |
| 目的 | 机械性达标 | 风格性优化 |
| 修正次数 | 严格一次 | 可多轮 |
| 输出格式 | 纯正文（无 PATCHES / FIXED_ISSUES）| 标准修订格式（FIXED_ISSUES + PATCHES 等）|
| truth files 更新 | 不更新（字数规范化不改事实）| 更新受影响的 truth files |
