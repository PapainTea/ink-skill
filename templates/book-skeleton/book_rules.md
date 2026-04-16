---
# 机器可读的硬约束配置（YAML frontmatter）

length:
  target: 4500           # 单章目标字数；hardGate = target 本身（v0.1.14 硬门槛，无折扣、无 allow-short 旁路）
  plotThresholdPct: 12   # plotThreshold = target × (1 - 12%) = 3960（首稿剧情完成度阈值）
  hardMaxPct: 30         # hardMax = target × (1 + 30%) = 5850
  countingMode: chinese  # chinese / english

hardRules:
  noMarkdownInProse: true       # 禁止正文出现 markdown 结构化标记（---, ##, **, ``` 等）
  noAnalysisTerms: true         # 禁止"显然 / 明显"等分析术语
  noAIMarkerWords: true         # 禁止"忽然 / 突然"等 AI 标记词
  banEmDash: true               # 禁用破折号 ——
  banContrastiveBuTing: true    # 禁用"不是 X 而是 Y"句式

pipeline:
  autoRunAudit: true            # Step 7 审计默认必跑
  autoRunVerify: true           # Step 12 三层验证默认必跑
  autoExpandIfShort: true       # 字数 < hardGate 时默认扩写一次（走 Step 6.3 / 6.3b 循环）

genre:
  id: {{genre_id}}              # 从 skill 的 genres/ 选一个，如 xuanhuan / urban / other
  name: {{genre_name_cn}}       # 对应的中文名
---

# 本书写作规则

## 作者定的额外规则（自由书写段）

这一段由作者自由写，告诉 AI：
- 这本书的独特禁忌（比如"主角永远不能主动求和"）
- 语感要求（比如"旁白尽量克制，不要过多心理活动"）
- 特殊设定（比如"本书武功招式名固定，见附录"）
- 反复强调的底色（比如"这是一本刑侦悬疑，所有推理要经得起推敲"）

**空则删除本段即可。AI 会回退到 frontmatter 里的硬约束 + genre 配置 + 全局创作规则。**

## 关于本书

**书名**: {{book_name}}  
**体裁**: {{genre_name_cn}} ({{genre_id}})  
**开始时间**: {{created_at}}  
**作者**: {{author_name_optional}}
