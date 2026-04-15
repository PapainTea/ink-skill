# hook-governance — 伏笔治理参考

> 本模块由 ink.skill 在结算章节（Step 9 Settler）/ 审计伏笔动态 / 查询陈旧伏笔时被 settler / writer / auditor 隐式调用。
> 独立于本模块的入口触发词："陈旧伏笔" / "列出未回收伏笔" / "H038 到期"——skill §3 路由表走查询类分支直接 Grep pending_hooks，不一定 Read 本模块。
> 本模块的规则由 `reference/settler.md`、`reference/write.md` 的 Step 9、`reference/audit.md` 的伏笔维度 26 共同依赖。

---


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
