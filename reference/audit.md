# audit — 章节审计参考

> 本模块由 ink.skill 在用户意图为"审计章节"时 Read。
> 输出：`<书根>/story/audits/ch-N.md`（Obsidian callout 格式）。
> 审计结束后回填 `PROGRESS.md` 的 📌 活跃 followup 段。

---

## 系统角色

你是一位严格的<题材名>网络小说审稿编辑。你的任务是对章节进行连续性、一致性和质量审查。

### 严重度速查（每次写 issue 前先自问）

**在给 issue 标 severity 前，先判断"这个问题是本章已写内容的硬伤，还是后续章节需要做的事"**：

- **本章已写内容的硬伤**（角色 OOC / 信息越界 / 破折号 / 不是而是 / AI 标记词超标 / 字数异常等）→ `critical` 或 `warning`
- **本章没问题，但后续章需要动作**（"ch 20 记得回收 H053" / "沈烬线需要在 ch 22 深化" / "支线 S003 两章没推进，ch 18 要动一下"）→ **`followup`**（**绝对不能标 warning**，会误触发 spot-fix 循环）
- **纯说明 / 作者声明 / 设计理由**（"本章是刻意压抑章节"）→ `info`

一条硬规则：**当你打算给某 issue 标 warning 时，先问自己"这个问题是本章已写内容错了，还是提醒未来章节要做某事？"**——如果是后者，改 followup。

---

（若本书在 `book_rules.md` 中配置了主角锁定，system prompt 会追加：`主角人设锁定：<主角名>，<性格锁定列表>，行为约束：<行为约束列表>`）

（若 `genre profile` 启用了 `eraResearch`，system prompt 会追加联网搜索提示：`你有联网搜索能力（search_web / fetch_url）。对于涉及真实年代、人物、事件、地理、政策的内容，你必须用search_web核实，不可凭记忆判断。至少对比2个来源交叉验证。`）

## 触发时机

- 用户说"审计第 N 章" / "审稿第 N 章" / "check chapter N"
- 写章 pipeline 末尾自动触发
- reviser 修订完成后的回归审计

## 前置动作（必读）

审计开始前**必须**连续 Read 3 个规则模块（每个都是独立的规则常量）：
- `reference/writing-bans.md`——核心硬性禁令（破折号 / 不是而是 / markdown 泄漏 / 分析术语等），对应维度 10 / 部分维度 6 / 27 的机械扫描线
- `reference/post-write-validator.md`——12 条机械规则的完整定义，可选择性跑完整扫描作为 audit md 的"机械层证据"
- `reference/sensitive-words.md`——60 词敏感词表，对应维度 27

**为什么要三份都 Read**：audit 不仅判"语义不合理"（37 维度主体），也要核对"机械违规"（禁令+敏感词+post-write）。这三份是确定性规则的独立源，audit.md 里的维度描述只是 pointer，具体规则以那三份为准。

## 审计维度清单（维度 0 + 1–37，第 0 条与 32 / 33 一样**永远启用**）

以下维度按 id 顺序列出，note 为每个维度在 prompt 中附带的解释说明。实际启用的维度集合由 `genre profile.auditDimensions` + `book_rules.additionalAuditDimensions` + always-active（0 / 32 / 33）+ 条件激活（12 年代考据、28–31 番外专用、34–37 同人专用）决定。

0. **current_state 硬约束覆盖**（**永远启用** · v0.1.16 Fix #2）— 读上一章 Settler 写入 `story/current_state.md` 的「🔴 结构性硬约束」段（如存在）。对每一条硬约束，在本章 audit md 里以**固定标题** `## 硬约束覆盖` 的表格输出 ✓/❌/🟨 判定 + 一句说明：

   ```markdown
   ## 硬约束覆盖

   | 硬约束（来自 current_state.md 🔴 段）| 本章是否覆盖 | 说明 |
   |---|---|---|
   | 约束 1 原文（截前 40 字）| ✓/❌/🟨 | 本章第 N 场景 / 第 N 段落如何覆盖 |
   | 约束 2 原文 | ✓/❌/🟨 | ... |
   ```

   - `✓` = 本章正文已兑现该约束
   - `❌` = 未覆盖 → 本章 audit 必须自动进入 Followup（ch+1 硬节点）
   - `🟨` = 部分覆盖 / 与约束精神一致但执行不完整

   **缺失该段 = 审计未完成**（verify-chapter.py v0.1.16 的 Layer 3 会检查："若 current_state 有 🔴 硬约束段，本章 audit md 必须含 `## 硬约束覆盖` 段"，缺则 warning）。若 current_state 无 🔴 硬约束段（通常是 ch1 或刚 init 的书），本段可写"本章无上游硬约束"一行。

1. OOC检查 — 角色是否偏离性格底色；同人"canon 模式"下严格检查，"ooc 模式"下仅记录不判定失败
2. 时间线检查 —（基础维度，无额外 note）
3. 设定冲突 —（基础维度，无额外 note）
4. 战力崩坏 —（基础维度，无额外 note）
5. 数值检查 —（基础维度，无额外 note）
6. 伏笔检查 —（基础维度，无额外 note）
7. 节奏检查 —（基础维度，无额外 note）
8. 文风检查 —（基础维度，无额外 note）
9. 信息越界 —（基础维度，无额外 note，实际交叉 character_matrix 信息边界表）
10. 词汇疲劳 — 高疲劳词：<题材疲劳词列表>。同时检查AI标记词（仿佛/不禁/宛如/竟然/忽然/猛地）密度，每3000字超过1次即warning
11. 利益链断裂 —（基础维度，无额外 note）
12. 年代考据 — 年代：<period, region>（仅在 `eraResearch` 或 `eraConstraints.enabled` 时激活）
13. 配角降智 —（基础维度，无额外 note）
14. 配角工具人化 —（基础维度，无额外 note）
15. 爽点虚化 — 爽点类型：<题材爽点类型列表>
16. 台词失真 —（基础维度，无额外 note）
17. 流水账 —（基础维度，无额外 note）
18. 知识库污染 —（基础维度，无额外 note）
19. 视角一致性 — 检查视角切换是否有过渡、是否与设定视角一致
20. 段落等长 —（基础维度，无额外 note）
21. 套话密度 —（基础维度，无额外 note）
22. 公式化转折 —（基础维度，无额外 note）
23. 列表式结构 —（基础维度，无额外 note）
24. 支线停滞 — 对照 subplot_board 和 chapter_summaries：如果任何支线超过5章未被提及或推进→warning。如果存在支线但近3章完全没有任何支线推进→warning
25. 弧线平坦 — 对照 emotional_arcs 和 chapter_summaries：如果主要角色连续3章情绪状态无变化（没有新的压力、释放、转变）→warning。注意区分"角色处境未变"和"角色内心未变"
26. 节奏单调 — 对照 chapter_summaries 的章节类型分布：连续≥3章相同类型（如连续3个事件章/战斗章/布局章）→warning。≥5章没有出现回收章或高潮章→warning。请明确列出最近章节的类型序列
27. 敏感词检查 —（基础维度，无额外 note）
28. 正传事件冲突 — 检查番外事件是否与正典约束表矛盾（番外专用，`parent_canon.md` 存在且非同人模式时启用）
29. 未来信息泄露 — 检查角色是否引用了分歧点之后才揭示的信息（参照信息边界表）（番外专用）
30. 世界规则跨书一致性 — 检查番外是否违反正传世界规则（力量体系、地理、阵营）（番外专用）
31. 番外伏笔隔离 — 检查番外是否越权回收正传伏笔（warning级别）（番外专用）
32. 读者期待管理 — 检查：章尾是否有钩子？最近3-5章内是否有爽点落地？是否存在超过3章的情绪压制无释放？读者的情绪缺口是否在积累或被满足？（**永远启用**）
33. 大纲偏离检测 — 对照 volume_outline：本章内容是否对应卷纲中当前章节范围的剧情节点？是否跳过了节点或提前消耗了后续节点？剧情推进速度是否与卷纲规划的章节跨度匹配？如果卷纲规划某段剧情跨N章但实际1-2章就讲完→critical（**永远启用**）
34. 角色还原度 — 同人专用，有条件启用；检查对话语癖、说话方式、行为是否符合 fanfic_canon.md 中的角色档案。偏离需有明确的情境动机
35. 世界规则遵守 — 同人专用，有条件启用；检查章节是否违反 fanfic_canon.md 中的世界规则（地理、力量体系、阵营关系）
36. 关系动态 — 同人专用，有条件启用；检查关系推进是否合理、是否与 fanfic_canon.md 中的关键关系对齐或有意义地发展
37. 正典事件一致性 — 同人专用，有条件启用；检查章节是否与 fanfic_canon.md 中的关键事件时间线矛盾

## 审计上下文（必读真相文件）

审计 LLM 的 user prompt 中会拼入以下上下文（存在则拼，不存在则跳过）：

- `current_state.md` —— 当前状态卡（总是读）
- `particle_ledger.md` —— 资源账本
- `pending_hooks.md` —— 伏笔池（`filterHooks` 过滤已回收）
- `subplot_board.md` —— 支线进度板（`filterSubplots` 过滤已关闭）
- `emotional_arcs.md` —— 情感弧线（`filterEmotionalArcs` 保留最近 N 章）
- `character_matrix.md` —— 角色交互矩阵（`filterCharacterMatrix` 按卷纲角色过滤）
- `chapter_summaries.md` —— 章节摘要（`filterSummaries` 保留最近 N 章，用于节奏检查）
- `volume_outline.md` —— 卷纲（用于大纲偏离检测）
- 上一章全文 —— 用于衔接检查
- `style_guide.md`（或 `book_rules.md` body fallback）—— 文风指南
- `parent_canon.md` —— 番外正典参照（若存在）
- `fanfic_canon.md` —— 同人正典参照（若存在）

## 持久化位置

审计结果落盘到 **`story/audits/ch-<N>.md`**，使用 Obsidian Callout 格式高亮显示。

每章一个 markdown 文件（不是 index.json 字段，不是 JSON），便于：
- 双链跳转（Obsidian 等知识管理工具直接打开）
- 阅读友好（callout 自动高亮，按严重度上色）
- 加入快照（与 truth files 一起 cp 进 snapshots/N/）
- Git diff 友好（markdown 比 JSON 更易读）

### 文件格式（Obsidian Callout）

```markdown
# 第 <N> 章审计：<章节标题>

> [!error] critical
> **<维度>**：<问题描述>
>
> **建议**：<修改建议>

> [!warning] warning
> **<维度>**：<问题描述>
>
> **建议**：<修改建议>

> [!info] info
> **<维度>**：<说明>

> [!tip] followup
> **后续跟进**：<描述后续章节需要关注的事>
>
> **触发章**：<预计在 ch X 处理>

---

**总结**：<一句话审计结论>

**审计时间**：<ISO 时间戳>
**通过状态**：passed=true / false
```

### Callout 类型映射

| 严重度 | Obsidian Callout | 颜色（默认主题）|
|--------|-----------------|---------------|
| critical | `> [!error] critical` | 红色 |
| warning | `> [!warning] warning` | 黄色 |
| info | `> [!info] info` | 蓝色 |
| **followup** | `> [!tip] followup` | **绿色** |

### 文件位置约束

- 路径：`<书籍根>/story/audits/ch-<N>.md`（编号不补零，便于人眼阅读）
- 同一章多次审计：覆盖（保留最新版本）
- 历史审计版本：在 `snapshots/N/audits/ch-<N>.md` 自动归档（写完第 N 章快照时一并保存）

### 与原项目的差异

原项目把审计结果存进 `chapters/index.json` 的 `auditIssues` 字段（`["[severity] description", ...]` 字符串数组）。skill 模式改成 markdown 文件，理由：

1. **可读性**：JSON 数组在编辑器里是一坨字符串，markdown + callout 在 Obsidian 直接高亮分级
2. **快照一致性**：truth files 是 markdown 进快照，审计也跟进保持一致
3. **作者参与**：作者可以直接在审计 md 里加注释（如「此 warning 不修，故意如此」），下次审计 LLM 看到能尊重作者意图
4. **零中间格式**：不需要把 JSON 数组反序列化为可读形式，markdown 本身就是可读形式

**index.json 中不再保留 `auditIssues` 字段。**

## 输出格式

审计 LLM 运行时必须输出合法 JSON（用于解析）：

```json
{
  "passed": true/false,
  "issues": [
    {
      "severity": "critical|warning|followup|info",
      "category": "审查维度名称",
      "description": "具体问题描述",
      "suggestion": "修改建议（followup 时改为 triggerChapter）",
      "triggerChapter": "ch N（仅 followup 用，预计哪章处理）"
    }
  ],
  "summary": "一句话总结审查结论"
}
```

### 严重度规则

- `critical` —— **本章存在阻断级问题**，必须修（OOC / 信息越界 / 设定冲突 / 战力崩坏 等影响本章内容的）
- `warning` —— **本章写作质量问题**，建议修（词汇疲劳 / 节奏 / 配角工具人化 等本章已落笔的问题）
- `followup` —— **后续章节需要关注的事**，不修本章（如"ch 20 记得回收 H053"、"沈烬线需要在 ch 22 深化"）
- `info` —— 纯说明 / 作者声明（如"本章是刻意压抑章节，符合卷纲节奏"）

**严重度判定原则**：
- 如果问题是**本章已写内容的硬伤** → `critical` 或 `warning`
- 如果问题是**本章没问题但后续章需要动作** → `followup`（不可标 warning，避免误触 spot-fix）
- 如果是**当前无 action，仅记录** → `info`

**`passed` 规则**：只有存在 `critical` 时 `passed=false`。warning / followup / info 都不导致 `passed=false`。

**spot-fix 循环退出条件**（write / batch-write 共用）：`0 critical AND 0 warning`（followup + info 不触发修订循环，也不阻塞进入下一章）。

## 3 类执行策略

37 个维度按判断难度分成 3 类，LLM 在审稿时应采用对应策略：

### 机械可判断类

直接算法 / 规则即可判定，LLM 只需对照事实：

- 数值一致性（资源期初/变动/期末对账）
- 禁止句式 / 敏感词
- 词汇疲劳（AI 标记词密度）
- 段落等长检查

### 需要 truth file 交叉比对类

LLM 需要对照真相文件做一致性判断：

- OOC 检查（对照 character_matrix 角色档案）
- 信息越界（对照 character_matrix 信息边界表）
- 设定冲突（对照 story_bible、volume_outline）
- 战力崩坏（对照 particle_ledger、story_bible 力量体系）
- 大纲偏离（对照 volume_outline）
- 支线停滞 / 弧线平坦（对照 subplot_board / emotional_arcs / chapter_summaries）

### 需要主观判断类

LLM 综合判断，可能存在争议：

- 节奏检查 / 节奏单调
- 配角工具人化 / 配角降智
- 台词失真 / 文风检查
- 读者期待管理
- 爽点虚化

对这 3 类的划分不影响输出格式，只影响 LLM 在每个维度上投入的分析深度和佐证要求。

---

## 附录 A：敏感词检测（维度 38，规则性）

> 从 inkOS sensitive-words.ts 迁入。非 LLM 判断，确定性词表匹配。

维度 38 是规则性检测，不属于 37 维度的主观判断类，作为附加维度常驻启用（与维度 32/33 一样永远启用）。

- 命中政治敏感词 → `severity: critical`（必须删除，无法发布）
- 命中色情/极暴力词 → `severity: warning`（建议替换或弱化）
- 命中自定义词（`book_rules.md` 中 `customSensitiveWords` 字段）→ `severity: warning`

完整词表见 `reference/sensitive-words.md`。

---

## 附录 B：Meta 泄漏规则库（非 LLM 规则性检测）

> 从 inkOS meta-leaks.ts 迁入。用于在审计章节时扫描正文是否含 meta-information 泄漏（破坏读者沉浸感）。
> 这是**规则性检测**（确定性 regex 或字符串匹配），不是 LLM 主观判断。

### 1. 章节 meta 引用泄漏（warning）

正文出现以下 pattern → severity=warning：

**显式章节引用**（`第X章`，排除标题行和书名号包裹的情况）：
- 正则：`/第[一二三四五六七八九十百千万\d]+章/g`
- 排除：以 `#` 开头的标题行；被 `《》` 包裹的书名内部
- 建议："如果是角色讨论书中书内容则可忽略，否则改为具体情节描述替代章节号引用"

**隐式章节引用**（上/前/后几章 + 动词）：
- 正则：`/(?:上|前|后)几?章(?:提到|说过|出现|描述|讲过|写过|说的|提过)/g`
- 建议："改为具体情节回忆或时间描述，避免引用章节概念"

### 2. Hook ID 泄漏（critical）

正文出现形如 `H001`、`H002` 等内部 hook 标识符 → severity=critical：

- 正则（带中文边界）：`H\d{3,}`（中文标点或空白或行首/行尾为边界）
- 建议："删除钩子 ID，改用具体情节描述"

### 3. 系统标签泄漏（critical）

正文出现 `=== UPPERCASE_TAG ===` 格式的系统分隔标签 → severity=critical：

- 正则：`/===\s*[A-Z_]+\s*===/g`
- 说明：如 `=== UPDATED_LEDGER ===`、`=== CHAPTER_CONTENT ===` 等，这些是 LLM 输出格式残留
- 建议："删除系统标签，这些内容不应出现在正文中"

### 4. JSON 字段名泄漏（critical）

正文出现以下 camelCase 内部字段名 → severity=critical：

词表：`hookOps`、`hook_id`、`startChapter`、`expectedPayoff`、`currentStatePatch`、`chapterSummary`、`runtimeStateDelta`、`subplotOps`、`emotionalArcOps`、`characterMatrixOps`、`lastAdvancedChapter`、`currentLocation`、`protagonistState`、`currentGoal`、`currentConstraint`、`currentAlliances`、`currentConflict`

- 建议："删除内部字段名，改用自然语言描述"

### 5. 审计集成

每次 Step 7 审计扫描本附录定义的 4 类 pattern。命中后按 severity 上报 issue，category 为 `meta-reference` 或 `system-id-leak`。

Meta 泄漏检测与写后校验（12 条）并行，不互相替代：
- 写后校验（Step 6）：重点查禁止句式/Markdown 标记/机械规则
- Meta 泄漏（Step 7 审计附录 B）：重点查 meta 引用/系统 ID 泄漏/JSON 字段名

## §7 Followup 段强制约束（v0.1.10 新增）

> 本节**覆盖**上文关于 followup 的既有描述，在执行上优先生效。既有语义定义仍然有效（`followup` = 后续章节需要动作，不是本章问题），本节补齐工程约束。

### §7.1 audit md 末尾必须有 `## Followup` 段

每份 `story/audits/ch-<N>.md` 的**最后一个 `##` 段**必须是 `## Followup`。无例外。

**格式**：checklist

```markdown
## Followup

- [ ] ch 18-20：验证借影单独代价是否有累积征兆（来源：ch17 新增）
- [ ] ch 18-22：顾家渗透侯府杂役班调查结果（来源：ch17 新增）
- [x] ch 17：确认镜核双轨分离（来源：ch16 继承 → 本章已消化）
- [ ] ch 20+：H038 真牌线窗口末激活（来源：ch16 继承 → 本章未消化，继续）
```

**字段约定**：
- `- [ ]` = 未消化（到本章为止仍然有效，继续向后传）
- `- [x]` = 已在本章消化（保留在 audit 里做审计痕迹，但不再进 PROGRESS.md 活跃列表）
- **ch X-Y** = 预期窗口
- **来源** = 本条第一次出现在哪一章（继承链可见），以及本章动作（新增 / 继承 / 已消化）

**空段也必写**（占位）：

```markdown
## Followup

- 本章无新增 followup；上章继承项无未消化。
```

**缺段 = audit 未完成**：verify-chapter.py Layer 2 会增补一条检查，`## Followup` 段不存在 → ❌。

### §7.2 Step 7 审计第一动作 = 继承上章 followup

写新 audit 前**第一件事**：

1. Read `story/audits/ch-<N-1>.md` 的 `## Followup` 段
2. 对每条状态为 `[ ]` 的条目逐条决定：
   - **本章已消化** → 在新 audit 里写 `- [x] ... (来源：ch<M> 继承 → 本章已消化：<一句话说明是如何消化的>)`
   - **本章未消化** → 原样搬到新 audit 里，继续 `[ ]`，来源字段追加"→ 本章未消化，继续"
3. Read 上章 `current_state.md` 或 `snapshots/<N-1>/current_state.md` 的"审计纠偏"段，扫里面 severity=warning 但含未来导向语义（**若 / 后续 / 需注意 / 监测 / 未来 / ch X+ / 建议 ch X 起**）的条目，按规则迁移到新 audit 的 `## Followup`（标"来源：ch(N-1) current_state 审计纠偏"）
4. **再**开始本章 37 维度 audit。本章新发现的 followup 按 §7.1 格式追加在 `## Followup` 段末尾。

**绝不允许**：
- 写 audit 时跳过继承、只写本章发现的 followup（上章的没消化项会凭空消失）
- 把已继承项静默删除（即使已经没意义，也要标 `[x]` + 一句"ch X 起已不再适用，关闭"）

### §7.3 Step 9 Settler 最后动作 = 重算 PROGRESS.md 活跃 followup 段

Settler 更新完 7 个 truth files 后、Step 10 Snapshot 前，**必须**重算 `PROGRESS.md` 的 `📌 活跃 followup` 段：

1. grep 所有 `story/audits/ch-*.md` 的 `## Followup` 段
2. 聚合其中状态为 `[ ]` 的条目（已 `[x]` 的不进活跃列表）
3. 按预期窗口 `ch X-Y` 的 X 升序排列
4. 重写 `PROGRESS.md` 📌 活跃 followup 段

**格式**：

```markdown
## 📌 活跃 followup  <!-- replace-on-update; 从 story/audits/ 重算 -->

- [ ] ch 18-20：验证借影单独代价累积征兆（来源 ch17）
- [ ] ch 18-22：顾家渗透侯府杂役班调查结果（来源 ch17）
- [ ] ch 20+：H038 真牌线窗口末激活（来源 ch8）
```

漏跑 / 跑错 → verify-chapter.py Layer 2 补一条检查，比对聚合结果与 PROGRESS.md 实际写入内容，不一致 → ❌。

### §7.4 为什么这么严

v0.1.9 前这套机制**定义齐全但实际 0 使用**——定义的 `followup` severity 在全书历史 audit 里出现 0 次，跨章监测项全部被倾倒进 `current_state.md` 审计纠偏段，每章 Settler 覆盖时凭 LLM 心情决定保留哪条，**每一章都在静默丢 followup**（实测镜源逆刻 ch17 Settler 就丢了 ch16 的"六叔姓陈"监测项）。

v0.1.10 把这套机制从"推荐规范"升级为"工程硬约束"：
- audit md 末尾强制 `## Followup` 段（缺段 = 审计未完成）
- Step 7 强制继承上章未消化项（不迁移 = 违约）
- Step 9 Settler 强制重算 PROGRESS.md 活跃 followup 段（不重算 = 违约）
- verify-chapter.py 在 Layer 2 双重兜底

**current_state.md 的"审计纠偏"段保留**但**不再是 followup 的唯一载体**——它只放"下一章写作时必看"的硬性结构约束（类似硬节点 checklist）。跨章监测一律走 audit `## Followup` → PROGRESS.md。
