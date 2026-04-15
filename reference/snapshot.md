# snapshot — 快照、结算、伏笔治理参考

> 本模块由 ink.skill 在用户意图为"章节结算 / 创建快照 / 回滚 / 查伏笔"时 Read。
> 快照路径：`<书根>/story/snapshots/N/`（7 个 truth files + audits/）。

---

# 快照与回滚

快照是 inkOS 的"时间机器"，用于回滚错误章节、支持 rework、数据恢复。搞错快照语义会造成不可逆的数据污染，本章必读必守。

---

## 1. 快照语义（关键约定）

**`story/snapshots/N/` = 写完第 N 章之后当时的累积状态**

- 不是"最终结果的副本"
- 不是"第 N 章这一章的内容"
- 是"写完 ch N 这一刻，7 个真相文件应有的全貌"

例如：`snapshots/5/particle_ledger.md` 应该包含 ch0 初始化行 + ch1 ~ ch5 所有资源变动行，但绝不能包含 ch6+ 的数据。

---

## 2. 四条硬约束（任何操作/脚本必守）

1. **绝不向 `snapshots/N/` 写入第 N 章之后才出现的数据**
2. **绝不批量用一个最终结果覆盖所有快照**（所有快照会全部退化成"最终态"，历史丢失）
3. **绝不修改 `snapshots/N/` 下的任何已有文件**（它是当时的真实状态，不是可编辑的工作区）
4. **恢复 / 重建时必须逐章"递增生成"每个快照**（从 ch1 开始，按正文 diff 累积到 ch N）

违反任一条 = 快照系统作废 = 回滚不可信 = 未来 bug 调查无据可依。

---

## 3. 每章写完后的快照命令

Writer 流程末尾会自动调用 `state.snapshotState(bookId, N)`。手动执行等价命令：

```bash
BOOK_DIR=<父目录>/books/<书名>
CHAPTER_NUM=<N>
SNAP_DIR="$BOOK_DIR/story/snapshots/$CHAPTER_NUM"
mkdir -p "$SNAP_DIR"

cp "$BOOK_DIR/story/current_state.md"       "$SNAP_DIR/"
cp "$BOOK_DIR/story/particle_ledger.md"     "$SNAP_DIR/"
cp "$BOOK_DIR/story/pending_hooks.md"       "$SNAP_DIR/"
cp "$BOOK_DIR/story/chapter_summaries.md"   "$SNAP_DIR/"
cp "$BOOK_DIR/story/subplot_board.md"       "$SNAP_DIR/"
cp "$BOOK_DIR/story/emotional_arcs.md"      "$SNAP_DIR/"
cp "$BOOK_DIR/story/character_matrix.md"    "$SNAP_DIR/"

# 审计 md 一并归档（如果 audits/ 目录存在）
if [ -d "$BOOK_DIR/story/audits" ]; then
  mkdir -p "$SNAP_DIR/audits"
  cp "$BOOK_DIR/story/audits/"*.md "$SNAP_DIR/audits/" 2>/dev/null || true
fi

# 注：skill 模式不创建 story/state/ 目录（原项目 pipeline 产物，已废弃）
```

---

## 4. 回滚到第 N 章的命令

**回滚前先做安全备份**：

```bash
BOOK_DIR=<父目录>/books/<书名>
TS=$(date +%Y%m%d%H%M%S)
cp -R "$BOOK_DIR/story" "$BOOK_DIR/story.backup-$TS"
```

**反向 cp（从 snapshot 覆盖 current）**：

```bash
TARGET=<N>
SNAP_DIR="$BOOK_DIR/story/snapshots/$TARGET"

cp "$SNAP_DIR/current_state.md"       "$BOOK_DIR/story/"
cp "$SNAP_DIR/particle_ledger.md"     "$BOOK_DIR/story/"
cp "$SNAP_DIR/pending_hooks.md"       "$BOOK_DIR/story/"
cp "$SNAP_DIR/chapter_summaries.md"   "$BOOK_DIR/story/"
cp "$SNAP_DIR/subplot_board.md"       "$BOOK_DIR/story/"
cp "$SNAP_DIR/emotional_arcs.md"      "$BOOK_DIR/story/"
cp "$SNAP_DIR/character_matrix.md"    "$BOOK_DIR/story/"

# 审计 md 也一并恢复（覆盖现有 audits/）
if [ -d "$SNAP_DIR/audits" ]; then
  rm -rf "$BOOK_DIR/story/audits"
  cp -R "$SNAP_DIR/audits" "$BOOK_DIR/story/"
fi
```

**回滚后的章节清理**（回滚到 ch N 意味着 ch N+1 及之后作废）：

```bash
# 删除 > N 的正文
for f in "$BOOK_DIR/chapters/"*.md; do
  num=$(basename "$f" | cut -d_ -f1 | sed 's/^0*//')
  if [ "$num" -gt "$TARGET" ]; then
    rm "$f"
  fi
done

# 从 chapters/index.json 里删除 > N 的条目（用 jq 或手动编辑）
jq --argjson N "$TARGET" '.chapters |= map(select(.number <= $N))' \
   "$BOOK_DIR/chapters/index.json" > /tmp/idx.json \
   && mv /tmp/idx.json "$BOOK_DIR/chapters/index.json"

# 删除 > N 的快照
for d in "$BOOK_DIR/story/snapshots/"*/; do
  num=$(basename "$d")
  if [ "$num" -gt "$TARGET" ]; then
    rm -rf "$d"
  fi
done

# 清理 pipeline-cache/（可选，避免 stale）
rm -rf "$BOOK_DIR/story/runtime/pipeline-cache"

# 重建 memory.db（从恢复后的 markdown）
# 通过 CLI 或 runner.refreshMemoryFromRestoredState 完成
```

---

## 5. Rework 模式的 7 步完整流程

触发："重写第 N 章"。这是"回滚 + 重生成"的组合操作，由 `runner.reworkChapterFromPreviousSnapshot` 封装。

1. **预校验**：确认 `snapshots/(N-1)/` 存在且包含 `current_state.md` + `pending_hooks.md`（否则拒绝执行）
2. **restoreState(N-1)**：从 `snapshots/(N-1)/` 反向 cp 7 个真相文件到 `story/`
3. **删除章节正文**：删除 `chapters/000N_*.md` 以及所有 > N 的章节文件
4. **更新 index.json**：从 chapter index 删除 ch ≥ N 的条目
5. **清理 pipeline-cache**：`rm -rf story/runtime/pipeline-cache/N/` 避免 stale cache 干扰
6. **refreshMemoryFromRestoredState(N-1)**：重建 `memory.db`，让 SQLite 事实索引回到 ch N-1 的状态
7. **调 `_writeNextChapterLocked`**：跑完整 Writer pipeline 生成新的第 N 章（book lock 已持有，走 locked 版本避免死锁）

详细写章流程见 [04-write-pipeline.md](./04-write-pipeline.md)。
# 伏笔治理

伏笔治理层提供三组确定性函数，协助 settler / writer 在伏笔生命周期中做出合理判断：陈旧债务检测、新伏笔准入、以及 disposition 分类。

## 1. 陈旧伏笔债务（`collectStaleHookDebt`）

### 判定规则

- **陈旧阈值**：默认 `staleAfterChapters = 10`（章）
- **截止章号**：`staleCutoff = chapterNumber - staleAfterChapters`
- **陈旧条件**（三条同时满足）：
  1. `hook.status` **不是** `resolved`，也**不是** `deferred`
  2. `hook.startChapter ≤ chapterNumber`（已经登场了）
  3. `hook.lastAdvancedChapter ≤ staleCutoff`（已经 10 章以上没推进了）

### 排序

按以下优先级升序：

1. `lastAdvancedChapter`（越久没推进排越前）
2. `startChapter`（越早登场排越前）
3. `hookId`（字典序）

### 使用场景

在写章时，把陈旧 hook 列表以 prompt 片段的形式**显式塞给 settler** / writer：

> 以下 hook 已经 <N> 章未推进，优先处理（推进 / 延后 / 回收三选一）：……

**不加硬约束**，避免 LLM 为了完成指标乱 resolve 重要伏笔。

## 2. 新伏笔准入（`evaluateHookAdmission`）

判断一个候选新 hook 是否应该被接纳进伏笔池。返回 `{ admit, reason, matchedHookId? }`。

### 拒绝原因

| reason | 触发条件 |
|---|---|
| `missing_type` | 候选 hook 的 `type` 经 normalize 后为空 |
| `missing_payoff_signal` | 候选 hook 的 `expectedPayoff` + `notes` 经 trim 后都为空，没有任何回收信号 |
| `duplicate_family` | 与某个现存活跃 hook 视为同一"伏笔家族" |

### Duplicate family 判定

对候选和现存 hook 各自把 `type + expectedPayoff + notes` 拼接并 normalize（小写、只保留字母数字和中日韩统一表意字符、空格归一）。

1. **完全相等**：normalized 文本完全一致 → duplicate
2. **同 type 且重叠**：候选和现存的 `type` normalize 后相等，**且**满足以下任一：
   - 英文 term 重叠 `≥ 2`（term = 长度 `≥ 4` 且不在 stop-word 表里的单词）
   - 中文 bigram 重叠 `≥ 3`（bigram = 长度 `≥ 2` 的中文段里的 2 字滑窗）

### Stop words（英文 term 提取时过滤）

`that` / `this` / `with` / `from` / `into` / `still` / `just` / `have` / `will` / `reveal`

## 3. Disposition 分类（`classifyHookDisposition`）

给定 `hookId` 和本章的 `RuntimeStateDelta`，返回本章对该 hook 做了什么：

| 返回值 | 判定顺序与条件 |
|---|---|
| `defer` | `hookId` 出现在 `delta.hookOps.defer` |
| `resolve` | `hookId` 出现在 `delta.hookOps.resolve` |
| `advance` | `delta.hookOps.upsert` 中存在 `hookId` 对应项，且 `lastAdvancedChapter === delta.chapter` |
| `mention` | `hookId` 出现在 `delta.hookOps.mention` |
| `none` | 以上都不满足 |

判定顺序固定：`defer → resolve → advance → mention → none`，命中即返回。

## HookOps 语义表

| 操作 | 含义 | 何时使用 |
|---|---|---|
| `upsert` | 新建 / 更新 hook 的完整记录（包含 `lastAdvancedChapter`）| 新伏笔登场，或旧伏笔状态真正改变（有新事实/证据/风险升级/范围收缩）|
| `mention` | 仅记录"本章被提到" | 旧伏笔被提及但**没有**新增信息或状态变化——不更新 `lastAdvancedChapter` |
| `resolve` | 标记回收 | 伏笔在本章被明确揭示、解决、或不再成立 |
| `defer` | 标记延后 | 超过阈值章节未推进，暂时挂起，备注原因 |

**铁律**：不要把"再次提到""换说法重述""抽象复盘"当成 `upsert` 推进。只有状态真的变了，才 `upsert`；只是被提到的，放进 `mention`。
# 状态结算

## 系统角色

你是状态追踪分析师。给定新章节正文和当前 truth 文件，你的任务是产出更新后的 truth 文件。

## 工作模式

你不是在写作。你的任务是：

1. 仔细阅读正文，提取所有状态变化
2. 基于"当前追踪文件"做增量更新
3. 严格按照 === TAG === 格式输出

## 分析维度

从正文中提取以下信息：

- 角色出场、退场、状态变化（受伤/突破/死亡等）
- 位置移动、场景转换
- 物品/资源的获得与消耗
- 伏笔的埋设、推进、回收
- 情感弧线变化
- 支线进展
- 角色间关系变化、新的信息边界

## 数值验算铁律

- 必须在 `UPDATED_LEDGER` 中追踪正文中出现的所有资源变动（金钱、物品、伤势、人脉、情报等）
- **期初 + 增量 = 期末**，三项必须可验算

## 伏笔追踪规则（严格执行）

- **新伏笔**：只有当正文中出现一个会延续到后续章节、且有具体回收方向的未解问题时，才新增 `hook_id`。不要为旧 hook 的换说法、重述、抽象总结再开新 hook
- **提及伏笔**：已有伏笔在本章被提到，但没有新增信息、没有改变读者或角色对该问题的理解 → 放入 `mention` 数组，不要更新"最近推进"
- **推进伏笔**：已有伏笔在本章出现了新的事实、证据、关系变化、风险升级或范围收缩 → **必须**更新"最近推进"列为当前章节号，更新状态和备注
- **回收伏笔**：伏笔在本章被明确揭示、解决、或不再成立 → 状态改为"已回收"，备注回收方式
- **延后伏笔**：超过 5 章未推进 → 标注"延后"，备注原因
- **铁律**：不要把"再次提到""换个说法重述""抽象复盘"当成推进。只有状态真的变了，才更新最近推进。只是出现过的旧 hook，放进 mention 数组

## 全员追踪（当 `enableFullCastTracking` 开启时）

`POST_SETTLEMENT` 必须额外包含：本章出场角色清单、角色间关系变动、未出场但被提及的角色。

## 输出格式（必须严格遵循）

### `=== POST_SETTLEMENT ===`

（简要说明本章有哪些状态变动、伏笔推进、结算注意事项；允许 Markdown 表格或要点）

### `=== RUNTIME_STATE_DELTA ===`

必须输出 JSON，不要输出 Markdown，不要加解释。

```json
{
  "chapter": <N>,
  "currentStatePatch": {
    "currentLocation": "可选",
    "protagonistState": "可选",
    "currentGoal": "可选",
    "currentConstraint": "可选",
    "currentAlliances": "可选",
    "currentConflict": "可选"
  },
  "hookOps": {
    "upsert": [
      {
        "hookId": "mentor-oath",
        "startChapter": 8,
        "type": "relationship",
        "status": "progressing",
        "lastAdvancedChapter": <N>,
        "expectedPayoff": "揭开师债真相",
        "notes": "本章为何推进/延后/回收"
      }
    ],
    "mention": ["本章只是被提到、没有真实推进的 hookId"],
    "resolve": ["已回收的 hookId"],
    "defer": ["需要标记延后的 hookId"]
  },
  "chapterSummary": {
    "chapter": <N>,
    "title": "本章标题",
    "characters": "角色1,角色2",
    "events": "一句话概括关键事件",
    "stateChanges": "一句话概括状态变化",
    "hookActivity": "mentor-oath advanced",
    "mood": "紧绷",
    "chapterType": "主线推进"
  },
  "subplotOps": [],
  "emotionalArcOps": [],
  "characterMatrixOps": [],
  "notes": []
}
```

### `=== UPDATED_LEDGER ===`

按 7 列账本 schema 输出完整最新 Markdown（列定义与事件 ID 规则见 `02-truth-schema.md`）。

### `=== UPDATED_SUBPLOTS ===`

输出完整的最新支线进度板 Markdown；即使本章无新增支线，也要输出沿用后的完整表格，不能留空。

### `=== UPDATED_EMOTIONAL_ARCS ===`

输出完整的最新情感弧线 Markdown；即使本章变化很小，也要保留完整表格。

### `=== UPDATED_CHARACTER_MATRIX ===`

输出完整的最新角色交互矩阵，必须严格按照下面 3 个 `### ` 子表的结构输出。即使某子表本章无变化，也要完整保留之前的所有行，不能留空。

```markdown
### 角色档案
| 角色 | 核心标签 | 反差细节 | 说话风格 | 性格底色 | 与主角关系 | 核心动机 | 当前目标 |
|------|----------|----------|----------|----------|------------|----------|----------|
（每行一个角色。Section 0 的 key 是第 0 列"角色"。）

### 相遇记录
| 角色A | 角色B | 首次相遇章 | 最近交互章 | 关系性质 | 关系变化 |
|-------|-------|------------|------------|----------|----------|
（每行一对角色。Section 1 的 key 是前两列 [角色A, 角色B]。不要为从未交互的角色对创建行。）

### 信息边界
| 角色 | 已知信息 | 未知信息 | 信息来源章 |
|------|----------|----------|------------|
（每行一条"某角色知道/不知道某关键信息"的记录。Section 2 的 key 是第 0 列 + 第 3 列 [角色, 信息来源章]。）
```

## 关键规则

1. 状态卡和伏笔池必须基于"当前追踪文件"做增量更新，不是从零开始
2. 正文中的每一个事实性变化都必须反映在对应的追踪文件中
3. 不要遗漏细节：数值变化、位置变化、关系变化、信息变化都要记录
4. 角色交互矩阵中的"信息边界"要准确——角色只知道他在场时发生的事
5. `RUNTIME_STATE_DELTA` 只负责 `current_state` / `hooks` / `chapterSummary` 的增量 JSON；`UPDATED_LEDGER`（如有）、`UPDATED_SUBPLOTS`、`UPDATED_EMOTIONAL_ARCS`、`UPDATED_CHARACTER_MATRIX` 必须输出完整最新 Markdown
6. 所有章节号字段都必须是整数，不能写自然语言
7. 如果旧 hook 只是被提到、没有真实状态变化，把它放进 `mention`，不要更新 `lastAdvancedChapter`
8. 如果本章推进了旧 hook，`lastAdvancedChapter` 必须等于当前章号
9. 如果回收或延后 hook，必须放在 `resolve` / `defer` 数组里
10. `chapterSummary.chapter` 必须等于当前章节号
11. 如果当前文件不存在或只有表头，也必须输出一个可直接写回磁盘的完整骨架
