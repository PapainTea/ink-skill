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

`ink` / `Ink` / `写书` / `写小说` / `写第 N 章` / `续写` / `连写` / `连写 N 章` / `连续写作` / `审计章节` / `润色章节` / `修订` / `扩写` / `压缩` / `新建书` / `新建章节` / `ink 初始化` / `ink 迁移` / `followup` / `伏笔` / `粒子账本` / `人物矩阵` / `世界观` / `章节大纲` / `真相文件` / `结算章节` / `章节结算` 等。

## 首次使用

### 新建一本书

```
对 AI 说："新建一本叫《XXX》的小说，类型是XX，主角是XX"
```

AI 会走对话式建书流程，最终生成：
- `chapters/` + `story/` + `snapshots/0/` 目录
- 7 个空 truth files + `book_rules.yaml` + `index.json`
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
│   │   ├── book_rules.yaml       ← 本书的硬约束配置
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

- **v0.1.0**（当前）— skill 化首版，迁移、新建、写章、审计、修订、结算全流程就绪

## License

Apache-2.0
