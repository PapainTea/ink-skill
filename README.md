# ink.skill

> 跨平台 AI 长篇小说写作 skill。一份 SKILL.md 同时支持 Claude Code / Codex CLI / Gemini CLI / Cursor，书籍数据与 skill 源同目录，`git pull` 全设备全平台一次同步。

## 这是什么

ink.skill 是一个把"严肃长篇网络小说创作流水线"打包成一份 skill 的项目：37 维度章节审计、5 种修订模式、7 个真相文件自动维护、followup 伏笔回收提醒、跨会话续接（PROGRESS.md）。装上后，对 AI 说"写第 17 章"、"审计本章"、"ink 迁移"就能走完整流程。

## 快速开始（三种安装方式任选一种）

### 方式 A：推荐 — 让 AI 自己装

打开你正在用的 AI CLI（Claude Code / Codex / Gemini CLI / Cursor），在你放书的 `books/` 目录里，直接发送下面这段**提示词**给 AI：

#### Claude Code 安装提示词

```
我要安装 ink.skill。请执行以下操作：
1. 进入我当前的 books 目录（如果不在，先帮我确认位置）
2. 跑 `git clone https://github.com/PapainTea/ink-skill.git`（克隆到当前 books 目录内，与各本书同级）
3. 跑 `python3 ink-skill/scripts/bootstrap.py --platform claude-code`（自动创建软链到 ~/.claude/skills/ink）
4. 跑 `/reload-plugins` 提醒我
5. 完成后告诉我可以用哪些触发词（如 "ink 初始化"、"写第 N 章"）
```

#### Codex CLI 安装提示词

```
我要安装 ink.skill（一个跨平台小说写作 AI skill）。请：
1. 进入我的 books 目录
2. 跑 git clone https://github.com/PapainTea/ink-skill.git
3. 跑 python3 ink-skill/scripts/bootstrap.py --platform codex（会软链到 ~/.agents/skills/ink）
4. 告诉我重启 Codex 使新 skill 生效，以及安装后可用的触发词
```

#### Gemini CLI 安装提示词

```
我要安装 ink.skill（跨平台小说写作 skill）。操作：
1. cd 到我的 books 目录
2. git clone https://github.com/PapainTea/ink-skill.git
3. python3 ink-skill/scripts/bootstrap.py --platform gemini（软链到 ~/.gemini/extensions/skills/ink）
4. 告诉我如何在 Gemini CLI 启用这个 skill 以及触发词
```

#### Cursor 安装提示词

```
我要安装 ink.skill。Cursor 没有标准 skills 目录，请：
1. 进入我的 books 目录
2. git clone https://github.com/PapainTea/ink-skill.git
3. 把 ink-skill/SKILL.md 和 ink-skill/reference/*.md 的关键内容汇总到一份 .cursorrules 里（或者告诉我怎么手动做）
4. 说明如何让 Cursor 读到这份规则
```

#### 通用提示词（其他 AI agent）

```
我要安装一个叫 ink.skill 的跨平台小说写作 skill，git 地址 https://github.com/PapainTea/ink-skill.git。请：
1. clone 它到我当前的 books 目录（与各本书同级）
2. 读 ink-skill/SKILL.md 了解这个 skill 的协议
3. 告诉我在你所在的 AI 平台上，如何让 skill 的内容每次对话都自动生效

安装后的触发词：ink / 写书 / 写第 N 章 / 审计章节 / 润色 / 连写 / ink 初始化 / ink 迁移 / followup / 粒子账本 等。
```

### 方式 B：手动安装

```bash
# 1. 克隆到你 books 目录内（与每本书同级）
cd <你的 books 目录>
git clone https://github.com/PapainTea/ink-skill.git

# 2. 跑自部署脚本（自动检测平台 + 创建软链）
python3 ink-skill/scripts/bootstrap.py --platform auto

# 3. 重启你的 AI CLI，或跑 /reload-plugins（Claude Code）
```

### 方式 C：Windows 特别说明

如果你在 Windows 且无 admin 权限，软链会自动降级到 `junction`（`mklink /J`）或整目录复制。功能不变，但复制模式下 `git pull` 后需要手动重跑 `bootstrap.py`。

## 核心功能

- 37 维度章节审计（人物一致性、粒子守恒、情绪弧、伏笔时序、世界观自洽等）
- 5 种修订模式（润色 / 扩写 / 压缩 / 重写 / 定点修订）
- 7 个真相文件自动维护（人物矩阵 / 世界观 / 粒子账本 / 章节摘要 / 当前状态 / 伏笔 / 时间线）
- followup 伏笔回收提醒（跨章节追踪未完成悬念）
- 跨会话续接（每本书一份 PROGRESS.md，`/clear` 后秒恢复上下文）
- 多平台 agent 兼容（Claude Code / Codex / Gemini CLI / Cursor）
- 迁移老书内置（v1.0.x markdown 分发形态一键升级）

## 触发词

任何含有以下关键词的消息都会激活本 skill：

`ink` / `Ink` / `写书` / `写小说` / `写第 N 章` / `续写` / `连写` / `连写 N 章` / `连续写作` / `审计章节` / `润色章节` / `修订` / `扩写` / `压缩` / `新建书` / `新建章节` / `ink 初始化` / `ink 迁移` / `followup` / `伏笔` / `粒子账本` / `人物矩阵` / `世界观` / `章节大纲` / `真相文件` / `结算章节` / `章节结算` / `玄幻` / `仙侠` / `都市` / `恐怖` / `悬疑` / `修真` / `科幻` / `浪漫` / `治愈` / `异世界` / `爬塔` / `系统末日` / `地下城核心` / `xuanhuan` / `xianxia` / `urban` / `horror` / `cultivation` / `progression` / `sci-fi` / `romantasy` / `cozy` / `isekai` / `tower-climber` / `litrpg` / `dungeon-core` / `system-apocalypse` / `other` 等。

## 首次使用

### 新建一本书

```
对 AI 说："新建一本叫《XXX》的小说，类型是XX，主角是XX"
```

AI 会走对话式建书流程，最终生成：
- `chapters/` + `story/` + `snapshots/0/` 目录
- 7 个空 truth files + `book_rules.md` + `index.json`
- 当前平台的 init 文件（CLAUDE.md / AGENTS.md 等）
- `PROGRESS.md`

### 迁移老书

```
进入老书目录，对 AI 说："ink 迁移"
```

AI 会自动聚合 `chapters/index.json` + `story/current_state.md` + `story/audits/` 里的 followup，生成 PROGRESS.md 和当前平台的 init 文件。迁移**零破坏**：不改正文、不碰 truth files。

## 目录约定

```
<你的 books 父目录>/
├── books/
│   ├── ink-skill/                ← 本仓库 clone 到这里
│   │   ├── SKILL.md
│   │   ├── reference/            ← 6 个按需加载模块
│   │   ├── scripts/              ← 3 个辅助脚本
│   │   └── templates/            ← 新建书骨架 + init 模板
│   ├── 你的书 1/
│   │   ├── CLAUDE.md             ← 当前平台 init（由 skill 自动生成）
│   │   ├── PROGRESS.md           ← 进度 & followup（skill 自动维护）
│   │   ├── book_rules.md         ← 本书的硬约束配置（YAML frontmatter + 自由规则段）
│   │   ├── chapters/
│   │   ├── story/                ← 7 个 truth files
│   │   └── snapshots/
│   └── 你的书 2/
│       └── ...
```

## 架构

- **核心 SKILL.md**：常驻加载（~8 KB），定义激活自检、路由表、PROGRESS.md 协议、跨平台 init 规则、强制律
- **reference/**（按需加载，共 ~115 KB）：write / audit / revise / init / snapshot / truth-schema
- **scripts/**：`verify-chapter.py`（13 维度验证）/ `merge-truth.py`（合并）/ `bootstrap.py`（跨平台自部署）
- **templates/**：`PROGRESS.template.md` + 4 平台 init 模板 + book-skeleton

## 版本

- **v0.1.9** — **pipeline 执法强化**：SKILL.md §7 新增强制律 9「验证必贴律」（写章/连写/重分析 的最后一条消息必须原样贴 verify-chapter.py 的 13 条 ✅/❌ stdout，口头总结视为未跑）+ §2 新增步骤 c.5 健康体检（已存在章节时自动对最新章跑 verify，发现 ❌ 先警告作者再继续）+ write.md Step 12 强调"这是给作者看的唯一完成证据" + batch-write.md §14.3 加"未贴 stdout = 本章作废"硬律 + reanalyze 同步要求贴 stdout。起因：发现某 agent 绕过 verify 写了 14 章、快照缺 7 个、index.json 断档、truth files 不一致，新会话进来若没体检就继续写等于在脏地基上盖楼
- **v0.1.8** — 补回 inkOS 漏迁的 **Titler 阶段**：写章 pipeline 新增 Step 8.5「章节标题最终化」，Step 8 修订循环退出后独立跑一轮"标题大师"prompt，基于定稿正文重取文学性标题，覆盖 Step 5 Writer 临时标题。Phase 架构从 3 轮 LLM 调用升为 4 轮（write / observer / settler / titler）
- **v0.1.7** — 工程串联补齐：write.md 显式描述 Phase 1/2a/2b 3 阶段架构 + observer.md 补"被谁调用"说明
- **v0.1.6** — 精简分发（删开发者 tests/ 和空 docs/）
- **v0.1.5** — 补齐 7 个 inkOS 漏迁模块（sensitive-words / chapter-analyzer / observer / fanfic / meta-leaks / length-normalizer + test fixture）
- **v0.1.4** — `book_rules.yaml` → `book_rules.md`（对齐 inkOS 原版格式，支持自由规则段）+ 新建书强制列 15 体裁流程 + 审计历史文档
- **v0.1.3** — 体裁触发词 + README 升级说明
- **v0.1.2** — 关键迁移错误修复（错译、发明文件、缺 4 真相文件、缺 15 体裁）
- **v0.1.1** — 连写 pipeline（batch-write）
- **v0.1.0** — skill 化首版，迁移、新建、写章、审计、修订、结算全流程就绪

## 升级历史与重要说明

### v0.1.2（重要修复）

v0.1.0 和 v0.1.1 有**关键迁移错误**，如果你基于这两个版本装过 skill，请立刻升级到 v0.1.2+：

**错误原因**：首版 skill 重写时 AI 凭记忆构造文件列表和翻译，没有对照原 inkOS 源码，造成：

1. **错译** — skill 内部把 `particle_ledger.md` 的中文名写成"粒子账本"，应为 **"资源账本"**；`character_matrix.md` 写成"人物矩阵"，应为 **"角色交互矩阵"**
2. **发明了不存在的文件名** — skill 模板引用了 `worldbook.md` / `foreshadow.md` / `timeline.md` 这三个文件，**inkOS 原项目根本没有这些文件**
3. **漏了真实存在的 4 个真相文件** — 应该有的 `story_bible.md`（世界观设定）/ `pending_hooks.md`（伏笔池）/ `subplot_board.md`（支线进度板）/ `emotional_arcs.md`（角色情感弧线）全部没包含进 book-skeleton
4. **15 个体裁配置完全没迁** — 原 inkOS 有 15 个体裁（xuanhuan/xianxia/urban/horror/cultivation/sci-fi/... 各带 numericalSystem/powerScaling/fatigueWords/auditDimensions 等配置），首版一个都没搬过来

**v0.1.2 修复内容**：

| 错误 | 修正 |
|------|------|
| `worldbook.md` 发明文件 | 删除，改用 `story_bible.md`（世界观设定）|
| `foreshadow.md` 发明文件 | 删除，改用 `pending_hooks.md`（伏笔池）|
| `timeline.md` 发明文件 | 删除（inkOS 没有此文件，相关内容在其他 truth 里处理）|
| 缺 `subplot_board.md` | 新增到 book-skeleton |
| 缺 `emotional_arcs.md` | 新增到 book-skeleton |
| "粒子账本" 错译 | 规范为"资源账本"（触发词里保留错词做 alias，不 break 老用户）|
| "人物矩阵" 错译 | 规范为"角色交互矩阵"（保留错词 alias）|
| 15 体裁 `.md` 没迁 | 全部迁到 `genres/`（xuanhuan/xianxia/dungeon-core/system-apocalypse/litrpg 5 个数值型 + urban/horror/cultivation/progression/sci-fi/romantasy/cozy/isekai/tower-climber/other 10 个非数值型）|
| 缺 v1.0.x markdown 版里原有的 `book_rules.md` 形式 | **v0.1.4 已修复**，改回 `.md + YAML frontmatter`（支持作者自由规则段）|

### v0.1.4（book_rules 对齐 + 强制列体裁 + 审计文档）

- `book_rules.yaml` → `book_rules.md`（YAML frontmatter + markdown 正文自由规则段），对齐原 inkOS 格式；作者现在可以在 frontmatter 之外用自然语言告诉 AI 额外规则
- `reference/init.md` 新增"新建书流程 Step 0"：强制先列 15 个体裁让作者选，再进入故事设定
- `SKILL.md` 新增 §5.5 强制律：即使作者消息里已提到体裁词，仍要把 15 个选项列出确认
- README 新增"从 inkOS 到 skill 的完整审计"段（三层对比 + bug 历史）

### v0.1.3（体裁触发词 + 文档）

- SKILL.md 触发词新增 15 个体裁名（中文 + 英文 id），现在说"写一本玄幻"、"这是 xuanhuan"等都能触发
- 本 README 新增"升级历史与重要说明"

### 老版本升级指南

**如果你之前装过 v0.1.0 或 v0.1.1**（装在 `~/Desktop/books/ink-skill/` 或类似位置）：

```bash
# 1. 拉最新（包含 v0.1.2 + v0.1.3 的所有修正）
cd <你放 ink-skill 的位置>
git pull origin main

# 2. 如果你已经让 v0.1.0/v0.1.1 给某本书生成过 PROGRESS.md，那份 PROGRESS.md 含错误的真相文件表格，需要重生：
rm <你的书>/PROGRESS.md

# 3. 重开 AI 会话，对某本书说"ink 迁移"，skill 会用新模板重生正确的 PROGRESS.md + init 文件
```

**如果你之前装过 v1.0.x markdown 分发版**（即 README 顶部提到的 [ink_writer 仓库](https://github.com/PapainTea/ink-writer)）：

你的 markdown 版本从未有过上述翻译错误或文件缺失（错误只存在于 skill 化过程中）。你可以：
- **继续用 v1.0.x**，不升级，没问题
- **升级到 skill 版本**：按 README 开头"快速开始"安装 ink.skill，然后对每本书说"ink 迁移"——迁移流程**零破坏**：不改正文、不碰 truth files，只新增 PROGRESS.md + 当前平台的 init 文件

### 已知遗留（v0.2.0 会处理）

- **`book_rules.yaml` vs `book_rules.md`**：已在 **v0.1.4** 修复。现在用 `book_rules.md`（YAML frontmatter + markdown 自由规则段），对齐原 inkOS 和 v1.0.x 格式。v0.2.0 会加兼容读取旧 `.yaml` 的逻辑
- **darwin-skill 优化 SKILL.md**：v0.1.x 系列跳过，v0.2.0 会跑一轮 darwin 迭代
- **bootstrap.py 加 `--force`**：重装参数，v0.1.x 不做

### 从 inkOS 到 skill 的完整审计（2026-04-15）

三层对比（inkOS TypeScript 源 → src/ v1.0.x markdown → ink.skill v0.1.x）：

**inkOS → src/（v1.0.x markdown）已缺失的（本 skill 继承）**：

1. **敏感词库（sensitive-words.ts）** — 政治/色情/极暴力关键词过滤完全没迁。写作时如果内容碰到这些词，skill 不会自动拦截或警告。v0.2.0 会补
2. **chapter-analyzer（外部章节重分析）** — 你把外部写好的章节拷进 `chapters/` 后，没有独立的重分析 prompt 回填 truth files。当前只能靠完整重写该章触发正常流程。v0.2.0 考虑加独立"分析已有章节"触发词
3. **observer 独立阶段（observer-prompts.ts）** — inkOS 有独立的"观察员 fact 提取"阶段，src/ 把它合进了写章 pipeline。功能上覆盖但不如原版细粒度
4. **fanfic 写作 prompt（fanfic-prompt-sections.ts）** — 审计维度 34-37（角色还原度/世界规则/关系动态/正典事件一致性）有了，但**具体怎么写同人**的独立 prompt 没迁。当前写同人仍然用普通写作 prompt + 审计维度兜底
5. **length-normalizer（字数规范化独立 prompt）** — src/04 的字数分层处理覆盖了大部分功能，但 inkOS 有独立的"把首稿压成 target 字数"prompt，src 没单独迁

**skill 化过程（v0.1.x）引入的 bug**：全部已在 v0.1.2/v0.1.3/v0.1.4 修复
- v0.1.2：错译（粒子账本/人物矩阵）+ 发明文件（worldbook/foreshadow/timeline）+ 缺 4 个真相文件 + 15 体裁漏迁
- v0.1.3：SKILL.md 触发词缺 15 体裁名
- v0.1.4：`book_rules.yaml` → `book_rules.md`（对齐 inkOS 原版，支持作者自由规则段）+ 新建书强制列 15 体裁流程

---

### 从原 inkOS 迁过来的东西一览

以下内容**原封不动**从 `/Users/admin/Codex/Project/inkOS/` 提取（保证 skill 行为和原项目一致）：

- 15 体裁配置（`genres/*.md`）
- 37 维度章节审计（`reference/audit.md` 含的 continuity.ts 内容）
- 5 种修订模式（`reference/revise.md`）
- 25 条创作规则（`reference/write.md`）
- 7 真相文件 schema（`reference/truth-schema.md`）
- 伏笔治理（`reference/snapshot.md` 含 hook-governance.ts 内容）
- 新建书流程（`reference/init.md`）
- 连写 pipeline（`reference/batch-write.md`，v0.1.1 加）

## License

Apache-2.0
