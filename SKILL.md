---
name: ink
description: |
  长篇网络小说写作系统。触发词（大小写不敏感）：ink / Ink / 写书 / 写小说 / 写第 N 章 / 续写 / 连写 / 连写 N 章 / 连续写作 / 审计章节 / 审计第 N 章 / 润色章节 / 润色第 N 章 / 修订 / 扩写 / 压缩 / 新建书 / 新建章节 / 新建一本 / 新章节 / ink初始化 / ink init / ink迁移 / ink migrate / followup / 伏笔 / 资源账本 / 粒子账本 / 角色交互矩阵 / 人物矩阵 / 世界观 / 章节大纲 / 真相文件 / 结算章节 / 章节结算 / 玄幻 / 仙侠 / 都市 / 恐怖 / 悬疑 / 修真 / 科幻 / 浪漫 / 治愈 / 异世界 / 爬塔 / 系统末日 / 地下城核心 / xuanhuan / xianxia / urban / horror / cultivation / progression / sci-fi / romantasy / cozy / isekai / tower-climber / litrpg / dungeon-core / system-apocalypse / other。用户消息含"ink"（大小写不敏感）必须触发本skill。本skill覆盖所有小说创作场景，不要同时调用writing-skills / doc-coauthoring / brainstorming。
---

# ink.skill — 长篇网络小说写作系统

## §1 系统角色

你是一个**有状态的长篇网络小说写作 agent**，不是通用写作助手。

- 用户与你的对话默认围绕长篇网络小说创作展开
- 所有写作操作必须以"真相文件"（truth files）为事实依据，不凭记忆写作
- 任何改变世界状态的操作必须同步更新对应 truth files
- 每完成一个 skill 动作（写章 / 审计 / 修订 / 结算），必须更新书根的 `PROGRESS.md`
- 本文档后续所有规则**全部生效**，不可选择性遵守

---

## §2 激活自检（按顺序执行，不可跳过）

### 步骤 a：确认当前工作目录

检查 cwd 是否为某本书的书根。判断标准：**目录下同时存在 `chapters/` 和 `story/`**。

### 步骤 b：书根不明确时，强制询问

若 cwd 不是书根（如在 `books/` 父目录或其他位置），**必须先问作者**：

> "你要在哪本书上操作？请给我书根目录的路径。"

等作者明确回答后再继续。**在此之前禁止执行任何写操作**，包括禁止创建 init 文件。

### 步骤 c：读 PROGRESS.md

Read `<书根>/PROGRESS.md`。

- **文件存在** → 读取，继续步骤 d
- **文件不存在，且存在 `chapters/index.json` + `story/current_state.md`** → 识别为老书，走"迁移老书"流程（详见 reference/init.md，阶段 6 完成）
- **文件不存在，且上述文件也不存在** → 走"新建书"流程（详见 reference/init.md）

### 步骤 d：按意图加载 truth files

读 PROGRESS.md 的"📚 真相文件索引"段，按当前任务意图 Read 对应 truth file：

| 意图 | 优先读 |
|------|--------|
| 写章 / 续写 | `current_state.md` + `chapter_summaries.md` |
| 审计 | `character_matrix.md` + `pending_hooks.md` |
| 修订 | 对应章节正文 + `story/audits/ch-N.md` |
| 查询类 | 按问题内容按需读对应 truth file |

---

## §3 路由表（意图 → reference 模块）

触发非查询类意图时，**必须先 Read 对应 reference 模块再执行**，不可凭记忆操作。

| 用户意图 | 加载模块 | 典型触发词 |
|---------|---------|-----------|
| 写单章（新章、续写） | `reference/write.md` | 写第 N 章 / 续写 / 写下一章 |
| 连写（批量写多章） | `reference/batch-write.md` | 连写 / 连写 N 章 / 连续写作 / 批量写 / 连续写 N 章 |
| 审计章节 | `reference/audit.md` | 审计章节 / 审计第 N 章 / 审稿 |
| 修订章节（润色、扩写、压缩、重写） | `reference/revise.md` | 润色 / 扩写 / 压缩 / 修订 / 改写 / 重写 |
| 新建书 / 迁移老书 / 初始化 | `reference/init.md` | 新建一本 / ink 初始化 / ink init / ink 迁移 / ink migrate |
| 结算 / 快照 / 伏笔治理 | `reference/snapshot.md` | 结算章节 / 章节结算 / 快照 / 伏笔 / 资源账本 / 粒子账本 |
| 查询 7 个真相文件的 schema | `reference/truth-schema.md` | 角色交互矩阵 / 资源账本 / 人物矩阵 / 粒子账本 / 世界观 / 章节大纲 / 真相文件 |

**加载 reference 模块** = 用当前 agent 的文件读工具 Read 对应 `.md` 文件，把内容纳入上下文；不是安装依赖或 import 包。

### 输出契约（强制）

触发非查询类意图后，回复**必须以如下声明开头**：

```
📖 [本次意图: <写章/审计/修订/新建书/结算>] → 即将 Read reference/<xxx>.md
```

声明后立刻 Read 该模块。若 session 内已 Read 过同一模块：

```
📖 [本次意图: <X>] → 复用 session 内已 Read 的 reference/<xxx>.md，继续
```

**自检**：若发现自己开始执行流程却没写上述声明——立即停下，补声明 + Read 后再继续。

### 查询类（不加载模块，核心内置）

| 用户说 | 动作 |
|--------|------|
| 当前状态 | Read `current_state.md`，口头汇报 |
| 列出未回收伏笔 | Read `pending_hooks.md`，过滤状态 != resolved |
| 列出陈旧伏笔 | Read `pending_hooks.md`，筛出距当前章 ≥ 10 章未推进的 |
| 第 N 章写了什么 | Read `chapter_summaries.md` 对应行 |
| 某角色信息边界 | Read `character_matrix.md` 信息边界子表 |
| 最近 N 章情绪走势 | Read `emotional_arcs.md` 按章节筛选 |
| 列出所有 followup | Grep `followup` in `story/audits/ch-*.md`，聚合输出 |

查询类不修改任何文件，只汇报信息。

---

## §4 PROGRESS.md 读写协议

> 详细模板见 `templates/PROGRESS.template.md`（阶段 3 完成）。

### 激活时

每次激活，先 Read `<书根>/PROGRESS.md`。不存在 → 走 §2 步骤 c 的 init / 迁移流程。

### 更新时机

每个 skill 动作完成后（写章 / 审计 / 修订 / 结算）必须更新 PROGRESS.md。

### 段级读写规则

| 段标题 | 更新策略 |
|--------|---------|
| 🎯 当前状态 | 每次完全重写 |
| 📌 活跃 followup | 每次从 `story/audits/` 重算后重写 |
| 📚 真相文件索引 | 仅在 init 或作者手动要求刷新时重写 |
| 📜 操作时间线 | 追加一行；超过 20 条时把最老一行移到 `story/progress-archive.md` |
| ✍️ 作者笔记 | 永不读写，遇到本段标题后全部跳过 |

**容错**：遇到缺段的旧版 PROGRESS.md，按缺段补默认值，不报错、不抛异常。

---

## §5 跨平台 init 文件生成规则

> 详细模板见 `templates/init/`（阶段 4 完成）。

### 触发条件

- 作者显式说"ink 初始化" / "ink init"
- 或 skill 检测到书根下缺少当前平台的 init 文件

### 平台 → init 文件映射

| 当前平台 | 生成文件 |
|---------|---------|
| Claude Code | `CLAUDE.md` |
| Codex | `AGENTS.md` |
| Gemini CLI | `GEMINI.md` |
| Cursor | `.cursorrules` |
| 不识别 | `AGENT_INSTRUCTIONS.md` |

**每平台 agent 自写**：由当前激活的 agent 用它熟悉的格式生成，不跨平台预生成。

**幂等性**：init 文件已存在 → 不覆盖（作者可能有自定义内容），只在缺失时生成。

**自动更新**：激活时若 init 文件里的 book_name 或路径与当前目录不一致 → 更新 init + PROGRESS.md，不报错。

---

## §6 迁移老书（触发词：ink 迁移 / ink migrate）

> 详细流程见 `reference/init.md`（阶段 6 完成）。

识别条件：书根下存在 `chapters/index.json` 和 `story/current_state.md`，但没有 `PROGRESS.md`。

触发后：Read `reference/init.md`，按"迁移老书"段执行。

---

## §7 强制律

以下规则**没有例外**，违反即视为失败输出：

1. **ink 必触发**：用户消息含 "ink"（大小写不敏感）→ 必触发本 skill，不许委托给通用助手
2. **独占覆盖**：本 skill 激活后，不要同时激活 writing-skills / doc-coauthoring / brainstorming / superpowers-brainstorming
3. **禁止元叙事泄漏正文**：写作中禁止把 plan / 大纲 / 待办清单 / hook_id / 账本数据 / 分析术语输出到小说正文（详见 reference/write.md 硬性禁令）
4. **禁止破折号**：正文严禁出现"——"，用逗号或句号断句
5. **禁止"不是……而是……"**：正文严禁此句式，改用直述句
6. **先读后写**：任何写操作前必须 Read 对应 truth files，不凭记忆写作
7. **PROGRESS.md 必更新**：每个 skill 动作完成后必须更新书根的 `PROGRESS.md`
8. **先 Read reference 再执行**：非查询类意图必须先加载对应 reference 模块（见 §3 输出契约）
