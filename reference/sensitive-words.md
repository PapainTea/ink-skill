# sensitive-words — 敏感词检测参考

> 本模块由 ink.skill 在审计章节时自动参考（作为 reference/audit.md 的补充）。
> 非 LLM 规则检测：确定性地扫正文是否含敏感词，命中按 severity 上报。
> 不需要 LLM 判断，属于机械规则层（同 meta-leaks、机械规则检查）。

---

## Severity 分类

### block（必删）— 政治敏感词

命中任意一词 → 审计 issue severity=**critical**，描述"检测到政治敏感词"，建议"必须删除或替换，否则无法发布"。

词表（来自 inkOS sensitive-words.ts POLITICAL_WORDS）：

```
习近平、习主席、习总书记、共产党、中国共产党、共青团
六四、天安门事件、天安门广场事件、法轮功、法轮大法
台独、藏独、疆独、港独
新疆集中营、再教育营
维吾尔、达赖喇嘛、达赖
刘晓波、艾未未、赵紫阳
文化大革命、文革、大跃进
反右运动、镇压、六四屠杀
中南海、政治局常委
翻墙、防火长城
```

### warn（提醒）— 色情敏感词

命中任意一词 → 审计 issue severity=**warning**，描述"检测到色情敏感词"，建议"替换或弱化，避免平台审核问题"。

词表（来自 inkOS SEXUAL_WORDS）：

```
性交、做爱、口交、肛交、自慰、手淫
阴茎、阴道、阴蒂、乳房、乳头
射精、高潮、潮吹
淫荡、淫乱、荡妇、婊子
强奸、轮奸
```

### warn（提醒）— 极端暴力词

命中任意一词 → 审计 issue severity=**warning**，描述"检测到极端暴力词"，建议"替换或弱化，避免平台审核问题"。

词表（来自 inkOS VIOLENCE_EXTREME）：

```
肢解、碎尸、挖眼、剥皮、开膛破肚
虐杀、凌迟、活剥、活埋、烹煮活人
```

---

## 自定义词表

作者可在 `book_rules.md` 里添加 `customSensitiveWords` 字段（列表），LLM 扫描时一并检测，全部按 severity=warning 处理：

```yaml
customSensitiveWords:
  - "某词A"
  - "某词B"
```

---

## 审计集成

每次 Step 7 审计时，LLM 对照本文件三个词表扫描正文：

1. 发现 block 级（政治敏感词）→ 上报 `severity: critical`，category: `敏感词`
2. 发现 warn 级（色情/极暴力/自定义）→ 上报 `severity: warning`，category: `敏感词`
3. 报告格式：`检测到<类别>：「词A」×N 次、「词B」×M 次`

审计维度 27（敏感词检查）= 本文件定义的检测逻辑。

---

## 说明

- 本模块是**规则性检测**，不需要 LLM 语义判断
- 扫描是逐词精确匹配（不是语义近似匹配）
- 同一词多次出现：计数后一次性上报（不是每次出现报一条 issue）
- 书名/地名引用了敏感词（如书中书的书名用书名号包裹）：LLM 可酌情忽略，但须在 info 级注明
