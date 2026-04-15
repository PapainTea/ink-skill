# batch-write — 连写（批量写章）参考

> 本模块由 ink.skill 在用户意图为"连写 X-Y 章 / 连续写 N 章 / 批量写 / 连写"时 Read。
> 前置：先读 `<书根>/PROGRESS.md` 获取当前章号和 followup。
> 本模块调用 reference/write.md（单章 pipeline）+ reference/audit.md（审计）+ reference/revise.md（spot-fix），以 core loop 串起来。

---

# 连写流程（batch-write）

**这是你刚刚 Read 的按需模块 `batch-write.md`**。作者触发"连写 X-Y 章"、"连续写 N 章"、"批量写"等意图时进入本流程。

---

## §14.0 核心循环

```
for N in [start..end]:
    iter = 0
    while iter < MAX_ITER:
        if iter == 0:
            # 第一轮：完整写章 14 步 pipeline（按 reference/write.md）
            run write_pipeline(N)
            # 含 Step 1-4 准备 / Step 5 Writer / Step 6 post-write-validator
            # / Step 7 audit / Step 8 reviser / Step 8.5 Titler / Step 9 Settler
        else:
            # 后续轮：针对性 spot-fix（按 reference/revise.md）
            # 只传 critical + warning 给 reviser，followup/info **不传**（见 §14.2）
            issues_to_fix = [i for i in last_audit.issues if i.severity in ("critical", "warning")]
            if not issues_to_fix:
                break  # 只剩 followup/info，不用修，直接退出本章循环
            run spot_fix_revision(N, issues_to_fix)

        # 审计
        audit_result = run_audit(N)
        last_audit = audit_result   # 记录给下一轮 spot-fix 用

        if audit_result.criticals == 0 and audit_result.warnings == 0:
            break  # 本章通过，只剩 followup/info 或 0 问题

        iter += 1

    if iter >= MAX_ITER and still has warnings+:
        PAUSE — 报告作者当前状态，询问："ch N 经 {MAX_ITER} 轮修订仍有 X 个 warning，是否继续 ch N+1？还是停下来人工介入？"
        # 作者说继续 → 放行此章走 Step 8.5 Titler + snapshot + verify 即可
        # 作者说停 → 本次连写结束，保留已完成的章

    # 每章独立走 Step 8.5 Titler + 结算 + 快照 + 流程审核（不能合并多章）
    run_titler(N)      # Step 8.5：基于定稿正文重取章节标题
    run_settle(N)      # Step 9：更新 7 truth files
    run_snapshot(N)    # Step 10：冻结 snapshots/N/

    # 强制流程审核：跑 verify-chapter.py 并把完整 ✅/❌ checklist 贴给作者
    verify_stdout, exit_code = run_verify(N)
    show_to_author(verify_stdout)  # 14 个环节逐项可见（v0.1.10 起含 Followup 段检查）

    if exit_code != 0:
        STOP — 具体报告哪个环节 ❌、需要补齐什么，不继续下一章
```

---

## §14.1 为什么要迭代上限

纯 prompt 的 audit→spot-fix 循环**没有自然收敛保证**：
- 修订可能产生新 warning（例如删掉一个"猛地"改的表达，引入一个新的陈词滥调）
- 某些维度是主观的（节奏单调、读者期待管理），LLM 反复 spot-fix 可能左右摇摆
- 有些 warning 是设计使然（例如黄金第二章"小爽点缺席"是卷纲刻意布置），硬要 fix 会破坏剧情

**默认 `MAX_ITER = 3`**：
- 第 1 轮：完整写章 + 初审
- 第 2 轮：spot-fix + 复审
- 第 3 轮：再一轮 spot-fix + 终审
- 还没 clean → 系统性问题，作者介入

作者可在命令里覆盖："**最多 5 轮**" / "**不设上限**"（不设上限仍要每轮报告进度，让作者随时喊停）。

---

## §14.2 决定何时"触发针对性修订"

**触发条件**：audit_result 含 **≥ 1 个 `critical`** 或 **≥ 1 个 `warning`**。
**不触发条件**：只剩 `followup` 和/或 `info`（或完全干净）。

**注意 followup 和 info 的区别**（严重度定义见 §06）：
- `followup` = 后续章节需要关注的事（如"ch 20 回收 H053"），**不是本章写作问题**，不修
- `info` = 纯说明（如"本章是刻意压抑章节"），不需动作

两者都**不触发 spot-fix 循环**，直接放行本章进入 Step 9 结算 + snapshot + verify。

### 针对性修订的 input

把 audit 报告里的 **每一条 critical 和 warning** 都作为 input 给 reviser，格式：

```
本章 audit 发现以下问题，请在 spot-fix 模式下逐条修正：

[critical] <维度>：<问题描述>
  建议：<修改建议>

[warning] <维度>：<问题描述>
  建议：<修改建议>

...
```

reviser 按 `reference/revise.md` 的 spot-fix 模式执行：只动问题句 + 前后各一句，保留其他所有内容原封不动。

### 修订后必须重审

**不能假设 spot-fix 把所有 warning 清零了**。修订后立即重跑完整 audit（37 维度），比对：
- 原 critical/warning 是否消失？
- 修订后是否出现**新**的 critical/warning？

### 避免死循环的额外保险

- 记录最近 2 轮的 audit issues（issue 的 category + description 拼 hash）
- 若本轮 issues 与上一轮**完全重合**（hash 一致）→ 说明 spot-fix 改不动，立即 PAUSE 报告作者
- 若本轮 issues 数 ≥ 上一轮 → 也 PAUSE（越修越差）

---

## §14.3 章间边界与中断

### 每章独立结算 + 快照 + 流程审核（强制）

连写循环不允许"写完 5 章再批量结算"——每章必须完整跑完：

1. Settler（更新 7 个 truth files）
2. Snapshot（保存到 `snapshots/N/`）
3. **流程审核**：用 Bash 工具调用 `python3 <SKILL_DIR>/scripts/verify-chapter.py <booksRoot> <书名> <N>`（`<SKILL_DIR>` 解析规则见 SKILL.md §8；若 PRE_WRITE_CHECK 声明"允许偏短"追加 `--allow-short`）
4. **把 verify-chapter.py 的 stdout 完整贴给作者**（14 个 ✅/❌ 环节 + 最终汇总行，v0.1.10 起含 Followup 段检查）

**理由**：truth files 是下一章 context 的基础，结算不及时会让下一章 planner 读到错误的状态卡。流程审核是**最后的兜底**，你（LLM）自己可能漏 Step 10/11，verify 脚本会把漏掉的环节用 ❌ 显式抓出来，作者一眼就能看到。

### ⚠️ 未贴 stdout = 本章作废（连写专用硬律）

连写场景下，LLM 有天然的偷懒诱因——一次回复里处理 14 章，用"ch 1-14 全部通过"一笔带过就想往下走。**禁止**。

强制约束（见 SKILL.md §7 强制律 9）：
- **每章**都必须单独贴一块 verify stdout（14 条 ✅/❌ 环节，含 v0.1.10 新增的 Followup 段检查），不允许只贴一次汇总
- 若作者看到一段"ch N-M 均已完成"但没看到 M-N+1 份 verify stdout → **已写的那几章视为作废，必须逐章重跑 verify 并贴输出**
- 在 stdout 贴出来之前，**index.json 里那章的 status 不允许写 `approved`**（最多写 `draft`）
- 即使用了 `run_in_background` 跑连写，每章回报时也必须把当章 verify stdout 贴出来

### 硬停条件（不继续下一章）

1. `verify-chapter.py` exit code 非 0 **且自动补救（见 §14.3.1）仍无法过** → 报作者具体哪些 ❌，不继续下一章
2. 作者在对话中说"停"/"暂停"/"先看看"/"打断"
3. 单章迭代达到 MAX_ITER 且作者选择不继续

### 软停条件（询问作者后决定）

- 单章迭代达到 MAX_ITER 但 verify 能过 → 问作者是否放行此章继续下一章

---

## §14.3.1 verify ❌ 的自动补救

**完整规则见 `reference/write.md` 的 §Step 12.1（单章 + 连写共用）**——定义了哪些 ❌ 可以盲修、哪些必须硬停问作者、补救循环伪代码、每步告知作者的格式。

连写场景下的特别约束：
- 补救最多 **2 轮**，仍 ❌ → 硬停，**不进入下一章**
- 补救期间作者说"停" → 立即中断连写（保留已完成章节 + 当前章的半修复状态）
- 补救成功后，仍按 §14.4 把最终 14 环节 ✅ checklist 贴给作者看，再继续下一章

---

## §14.4 输出格式（每章完成时必须给作者看）

每章完成后的输出**必须包含两块**：连写进度小结 + verify 完整 checklist。

### 块 1：连写进度小结

```markdown
## 第 {N} 章完成
- 迭代轮数：{iter} / {MAX_ITER}
- 最终 audit：{criticals} critical, {warnings} warning, {infos} info
- 字数：{word_count} chars（target={target}）
- 文件：chapters/{NNNN}_{title}.md

待写：ch {N+1} ~ ch {end}（剩 {end - N} 章）
```

### 块 2：流程审核（把 verify-chapter.py stdout 原样贴出来）

直接把脚本输出的 14 个 ✅/❌ 环节贴给作者（v0.1.10 起含 Followup 段检查），例如：

```
=== 第 {N} 章流程审核（{书名}）===

【Step 5 · 写正文】
  ✅ chapters/<N>_*.md 存在且非空

【Step 6 · 机械规则校验】
  ✅ 禁令扫描（破折号/不是而是/分析术语/markdown 泄漏）
  ✅ 字数区间检查

【Step 7 · 审计】
  ✅ story/audits/ch-N.md 存在
  ✅ audit 末尾 `## Followup` 段存在（v0.1.10）

【Step 9 · 结算：7 个 truth files】
  ✅ current_state.md 当前章节 ≥ {N}
  ✅ chapter_summaries.md 含 ch N 行
  ✅ pending_hooks.md（若审计声明涉及）
  ✅ subplot_board.md（若审计声明涉及）
  ✅ emotional_arcs.md（若审计声明涉及）
  ✅ particle_ledger.md（若审计声明涉及）
  ✅ character_matrix.md（若审计声明涉及）

【Step 10 · 快照】
  ✅ snapshots/{N}/ 存在且含 7 个 truth files

【Step 11 · 索引更新】
  ✅ index.json 含 ch N 条目且 status ∈ {approved, audited}

==================================================
✅ 流程审核全部通过（14/14 环节）
🎉 第 {N} 章完成
```

**如果任一环节 ❌**，立即进入硬停条件 1——向作者报告具体哪一环节挂了、如何补齐，**不自动进入下一章**。

每 3 章或达到中间节点（例如卷纲的关键节点章）可以给一次小结：

```markdown
## 连写进度小结（ch {start} ~ ch {N}）
- 完成 {N - start + 1} 章
- 平均迭代轮数：{avg_iter}
- 触发 PAUSE 次数：{pause_count}
- 发现的系统性问题：{list}
```

---

## §14.5 与单章写作的关系

连写 = 单章流程的循环执行 + audit 驱动的自动修订。本模块**不重新定义**：
- 写章流程（读 `reference/write.md`）
- 审计流程（读 `reference/audit.md`）
- 修订流程（读 `reference/revise.md`）

**首次进入连写时，必须依次 Read 上述 3 个模块**（读完后 session 内都可用），再开始循环。

---

## §14.6 使用示例

### 作者命令

> "连写 16-20 章"

### LLM 响应（期望行为）

1. Read `write.md` / `audit.md` / `revise.md`（如 session 首次触发）
2. 对 ch 16-20 逐章执行本模块 §14.0 循环
3. 每章结束给 §14.4 格式的进度卡
4. 遇到 PAUSE 条件立即询问作者
5. 全部完成后给 §14.4 最终小结

### 作者可覆盖的参数

- "连写 16-20 章，最多 5 轮修订" → MAX_ITER = 5
- "连写 16-20 章，不自动修订" → 每章只跑 1 轮（出 warning 也不循环，直接到下一章）
- "连写 16-20 章，critical 才修订" → 只在 critical 时触发 spot-fix，warning 放行（更宽松）

---

## §14.7 风险与限制

| 风险 | 缓解 |
|------|------|
| drift 复利：上一章的带病状态污染下一章 context | 每章必须 verify 通过才能继续；verify 失败硬停 |
| LLM 把 warning 修出新 warning | MAX_ITER 上限 + issue hash 比对检测"循环没进展" |
| 某些 warning 是卷纲设计（无需修） | 作者可覆盖 "critical 才修订" 模式；或设 `ignore_warnings: [维度1, 维度2]` 白名单（本模块当前不实现白名单，作者可手动跳过） |
| 长对话 context 累积 | 连写 ≥ 5 章时，每 3 章做一次小结压缩；必要时作者主动 `/clear` 开新对话继续 |

---

## §14.8 不做的事

- **不做无人值守的长时间连写**（作者必须在对话中，随时响应 PAUSE）
- **不合并 snapshot**（每章独立）
- **不跨章 rework**（rework 是单章流程，不能"连续 rework 3 章"，那叫回滚重写卷）
