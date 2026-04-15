# observer — 章节 fact 提取独立阶段参考

> 本模块由 ink.skill 在需要"从章节正文独立提取所有 facts"时 Read。
> 相对于 reference/write.md 里的写章流程，observer 是更细粒度的 fact 提取子阶段，可单独触发。
> 对应 inkOS observer-prompts.ts。设计原则：**宁多勿少**——过度提取比遗漏更安全，后续 truth files 合并时可以裁剪。

---

## 调用者

本模块作为 **prompt 源** 被以下流程调用：

1. **reference/write.md** 的 Phase 2a（写章后 fact 提取，独立 LLM 调用 → Phase 2b Settler 再合 truth files）
2. 作者显式说"帮我提取第 N 章 facts"时（独立触发，不走写章 / reanalyze 整流程）

**不调用本模块的流程**：
- `reference/reanalyze-chapter.md` —— inkOS 原版 `chapter-analyzer.ts` 是**单阶段 LLM 调用**（一次性完成 fact 提取 + 7 truth files 更新），不套用 write.md 的 observer/settler 两阶段。reanalyze Step 2 的 prompt 来自 chapter-analyzer.ts，不是本文件

本模块**只是 prompt 文档**，无副作用（不写文件、不调脚本）。调用者读完本文件后按 prompt 和格式输出 observations 文本。

---

## 使用场景

- 写章 pipeline 内部：Phase 2a（必跑）+ Phase 2b Settler 接着用这批 observations 产 truth files delta
- 写章产出后的"自检"子步骤：LLM 写完正文怀疑某些事实没落 truth files 时，先跑一遍 observer 对照
- 作者显式复核："帮我梳理一下第 N 章有哪些关键事实变化"（独立使用）

**不适用的场景**：reanalyze-chapter（回填历史章）用单阶段 chapter-analyzer prompt，不调 observer——详见 `reference/reanalyze-chapter.md` Step 2 说明。

---

## System Prompt（中文版）

```
你是一个事实提取专家。阅读章节正文，提取每一个可观察到的事实变化。

## 提取类别

1. **角色行为**：谁做了什么，对谁，为什么
2. **位置变化**：谁去了哪里，从哪里来
3. **资源变化**：获得、失去、消耗了什么，具体数量
4. **关系变化**：新相遇、信任/不信任转变、结盟、背叛
5. **情绪变化**：角色情绪从X到Y，触发事件是什么
6. **信息流动**：谁知道了什么新信息，谁仍然不知情
7. **剧情线索**：新埋下的悬念、已有线索的推进、线索的解答
8. **时间推进**：过了多少时间，提到的时间标记
9. **身体状态**：受伤、恢复、疲劳、战力变化

## 规则

- 只从正文提取——不推测可能发生的事
- 宁多勿少：不确定是否重要时也要记录
- 具体化："主角左肩旧伤开裂" 而非 "主角受伤了"
- 记录章节内的时间标记
- 标注每个场景中在场的角色
```

---

## System Prompt（英文版，书语言为 en 时使用）

```
【LANGUAGE OVERRIDE】ALL output MUST be in English.

You are a fact extraction specialist. Read the chapter text and extract EVERY observable fact change.

## Extraction Categories

1. **Character actions**: Who did what, to whom, why
2. **Location changes**: Who moved where, from where
3. **Resource changes**: Items gained, lost, consumed, quantities
4. **Relationship changes**: New encounters, trust/distrust shifts, alliances, betrayals
5. **Emotional shifts**: Character mood before → after, trigger event
6. **Information flow**: Who learned what, who is still unaware
7. **Plot threads**: New mysteries planted, existing threads advanced, threads resolved
8. **Time progression**: How much time passed, time markers mentioned
9. **Physical state**: Injuries, healing, fatigue, power changes

## Rules

- Extract from the TEXT ONLY — do not infer what might happen
- Over-extract: if unsure whether something is significant, include it
- Be specific: "Character's left arm fractured" not "Character got hurt"
- Include chapter-internal time markers
- Note which characters are present in each scene
```

---

## User Prompt

```
（中文）请提取第 N 章「<标题>」中的所有事实：

<正文内容>
```

```
（英文）Extract all facts from Chapter N "<Title>":

<chapter content>
```

---

## 输出格式

```
=== OBSERVATIONS ===

[角色行为]
- <角色名>: <行为/状态变化> (场景: <地点>)

[位置变化]
- <角色> 从 <A> 到 <B>

[资源变化]
- <角色> 获得/失去 <物品> (数量: <n>)

[关系变化]
- <角色A> → <角色B>: <变化描述>

[情绪变化]
- <角色>: <之前> → <之后> (触发: <事件>)

[信息流动]
- <角色> 得知: <事实> (来源: <途径>)
- <角色> 仍不知: <事实>

[剧情线索]
- 新埋: <描述>
- 推进: <已有线索> — <进展>
- 回收: <线索> — <解答>

[时间]
- <时间标记、时长>

[身体状态]
- <角色>: <受伤/恢复/疲劳/战力变化>
```

---

## 和写章 Phase 2b Settler 的协作关系

- **observer**（本模块 / write.md Phase 2a）= fact 提取独立阶段，输出 `=== OBSERVATIONS ===` 段，**只读正文**，不写任何文件
- **settler**（`reference/settler.md` / write.md Phase 2b）= 把 observations 合进 7 个 truth files，输出 7 个 `=== UPDATED_XXX ===` 段
- 两阶段严格分离：Phase 2a 结束时 LLM 手头**只有 observations，没碰任何 truth file**；Phase 2b 开始时 LLM 收到 observations + 当前 7 个 truth files 副本，才产 delta

**和 reanalyze 的差异**：reanalyze 不套两阶段——`reference/reanalyze-chapter.md` Step 2 的 prompt 来自 inkOS 原版 chapter-analyzer.ts，**一次 LLM 调用同时做 fact 提取 + truth files 更新**。两种实现路径都有道理（前者解耦，后者简洁），按 inkOS 原项目的历史设计分工，写章用两阶段，reanalyze 用单阶段。
