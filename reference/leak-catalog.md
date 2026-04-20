# leak-catalog — 语义泄漏模式自迭代库

> 本文件由 `verify-chapter.py --mechanical-only` 在启动时读取，解析两个 sentinel 之间的 markdown 表，追加到机械扫描的禁令列表。
>
> **设计目的**：让 skill **每次发现新的漏网泄漏模式都能追加进来**，无需改 Python 代码、无需发版。模式对全书全章永久生效。

## 何时追加新行

- **Step 10.5 全章通读自检** 时发现一个 regex 现在抓不到、但语义上属于账本 / 学术 / 元叙事 / 列表编号 / 等号赋值 / 元字面量类的新泄漏 → 追加
- 作者主动说"以后禁止 X 这种写法" → 追加

## 如何追加

1. 把新模式加到下方 `LEAK-CATALOG-START` / `LEAK-CATALOG-END` 之间的 markdown 表中
2. 列格式严格（下方示例行已演示）：
   ```
   | <类别标签> | `<单行 Python regex>` | <一个简短示例文本> | <YYYY-MM-DD> | <来源：某书 chN> |
   ```
3. **正则必须用反引号包起来**，否则 parser 跳过该行
4. 示例列要是**原文正面文本**（不要写"错误"或"✗"字样，parser 会测试 regex 是否确能匹配示例，不匹配的行会被跳过并打 warning）
5. 追加后**不用重发版**，下次 `verify-chapter.py --mechanical-only` 自动生效

## 正则书写提示

- 中文字符类：`[\u4e00-\u9fa5]`
- 混合数字：`[0-9零一二三四五六七八九十百千]`
- 词边界在中文场景下不好用，尽量用"上下文字符"锚定而不是 `\b`
- 小心误伤：例如"第三坎""两息""一刻"都是合法古风用法，不要拉太宽

## 模式表

<!-- LEAK-CATALOG-START -->

| 类别 | 正则 | 示例 | 日期 | 来源 |
|---|---|---|---|---|

<!-- LEAK-CATALOG-END -->

（初始空表——v0.1.17 内置的 7 条 regex 仍 hardcoded 在 `scripts/verify-chapter.py` 的 `FORBIDDEN_PATTERNS` 中，本表专收后续发现的增量模式。）

## 与硬编码规则的分工

| 层 | 在哪里 | 动时机 | 动机 |
|---|------|------|------|
| 基底规则（破折号 / 不是而是 / markdown 结构 / v0.1.17 七条 leak regex）| `scripts/verify-chapter.py` FORBIDDEN_PATTERNS | 改 Python 代码 + 发 skill 新版 | 核心、稳定、不频繁变 |
| 增量规则（未来每次发现的新模式）| 本文件 LEAK-CATALOG 段 | 加一行 markdown | 自由生长，无需发版 |

如果增量表某条模式被多本书反复命中（> 3 次）并证明稳定，可在下个 skill 发版时把它"毕业"到 FORBIDDEN_PATTERNS 硬编码层，并从本表删除。
