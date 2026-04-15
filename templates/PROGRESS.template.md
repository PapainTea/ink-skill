# 📖 {{book_name}} 进度

> 本文件由 ink.skill 自动维护。**作者笔记段（最后一段）永不被覆盖。**
> 遇到缺段的老版本文件，按缺段补默认值，不报错。

## 🎯 当前状态  <!-- replace-on-update -->

- **最新已批准**：ch{{last_approved_chapter}}（{{word_count}} 字，{{approved_date}}）
- **下一章**：ch{{next_chapter}}
- **最近操作**：{{last_action_timestamp}} · {{last_action_summary}}
- **书根目录**：{{book_root_abs_path}}

## 📌 活跃 followup  <!-- replace-on-update; 从 story/audits/ 重算 -->

> 每次 skill 动作后根据所有 `audits/ch-*.md` 里 severity=followup 的条目重建；已解决的自动移除。
> 作者手动加的条目也保留（格式同下即可）。

- [ ] （若无则写：暂无活跃 followup）

## 📚 真相文件索引（读取提示）  <!-- replace-on-update; 仅 init 或作者明确要求时重写 -->

> skill 每次激活必读本段，然后按当前任务意图 Read 对应 truth file。

| 文件 | 位置 | 什么时候读 |
|------|------|------------|
| 角色交互矩阵 | `story/character_matrix.md` | 写章前、审计"人物一致性"维度；3 子表：角色档案/相遇记录/信息边界 |
| 世界观设定 | `story/story_bible.md` | 写涉及设定的章节前 |
| 资源账本 | `story/particle_ledger.md` | 写有物品/资源变动的场景前、审计"资源一致性"（全书种必备，记录金币/武器/兵力/人情债/合作链等任何要追踪的资源）|
| 章节摘要 | `story/chapter_summaries.md` | 写章前检查前情 |
| 当前状态卡 | `story/current_state.md` | 每次激活 |
| 伏笔池 | `story/pending_hooks.md` | 写章前检查待回收伏笔 |
| 支线进度板 | `story/subplot_board.md` | 写涉及支线推进的章节前 |
| 角色情感弧线 | `story/emotional_arcs.md` | 写涉及角色情绪转变的场景前 |
| 卷纲 | `story/volume_outline.md` | 写新章前参考当前卷的脉络 |

## 📜 操作时间线  <!-- append-only; 最多保留 20 条，溢出归档到 story/progress-archive.md -->

> 追加规则：每次 skill 动作结束后追加一行。不改旧行。条数超过 20 时，把最老一行整行移到 `story/progress-archive.md`（不存在则创建）。

- {{ts1}} · {{action1}}

## ✍️ 作者笔记（skill 不修改）  <!-- never-touched -->

> 本段以下的所有内容，skill 永远不读、不写、不引用。作者可以自由写任何东西。
> **遇到本段标题后，skill 应立即跳过剩余部分。**
