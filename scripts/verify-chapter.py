#!/usr/bin/env python3
"""
verify-chapter.py — 章节完成后的三层不变量验证

按 src/04-write-pipeline.md Step 12 和 CLAUDE.md §6.7 设计：

Layer 1 强制不变量（必须满足）：
  - chapters/<NNNN>_<标题>.md 存在且非空
  - chapters/index.json 有该章条目且 status ∈ {approved, audited}
  - story/snapshots/<N>/ 存在且含 7 个 truth files + audits/
  - story/current_state.md 的"当前章节"字段 == N
  - story/chapter_summaries.md 最后一行是 ch N
  - story/audits/ch-<N>.md 存在（除非配置 pipeline.autoRunAudit=false）

Layer 2 机械规则（必须通过）：
  - 正文破折号 == 0
  - 正文"不是...而是..." == 0
  - 分析术语 == 0
  - markdown 结构泄漏（---/###/**/列表）== 0
  - 字数 ≥ hardMin（除非作者声明允许偏短，但仍要 ≥ hardMin）

Layer 3 条件性副作用（按结算摘要/sentinel 判断）：
  - 对于每个 truth file（subplot_board / emotional_arcs / character_matrix /
    particle_ledger / pending_hooks）：如果 audits/ch-N.md 或结算摘要声明了"本章推进 X"，
    对应 truth file 必须有对应变化；反之未声明则不检查

用法：
    python3 verify-chapter.py <books-root> <书名> <N>

退出码：
    0  = 全部通过
    1  = Layer 1 失败
    2  = Layer 2 失败
    3  = Layer 3 失败
    99 = 用法错误
"""

import argparse
import json
import re
import sys
from pathlib import Path


def fail(layer: int, msg: str) -> None:
    print(f"❌ Layer {layer} FAIL: {msg}", file=sys.stderr)


def ok(msg: str) -> None:
    print(f"✅ {msg}")


def count_cjk(text: str) -> int:
    return sum(1 for c in text if "\u4e00" <= c <= "\u9fff")


def parse_yaml_frontmatter(md_text: str) -> dict:
    """粗略解析 markdown 文件的 YAML frontmatter（不依赖 PyYAML，只抽我们需要的字段）"""
    if not md_text.startswith("---"):
        return {}
    try:
        end = md_text.index("\n---\n", 4)
    except ValueError:
        return {}
    yaml_block = md_text[3:end]
    result = {}
    # 极简解析：只处理 key: value 和 key: 下的嵌套（2 层）
    current_parent = None
    for line in yaml_block.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith("  ") and ":" in line:
            # 嵌套字段
            if current_parent is None:
                continue
            key, _, val = line.strip().partition(":")
            val = val.strip()
            if val == "":
                continue
            # 去引号
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            # 转数字/布尔
            if val.lower() in ("true", "false"):
                val = val.lower() == "true"
            elif val.isdigit():
                val = int(val)
            elif val.replace(".", "", 1).isdigit():
                val = float(val)
            result.setdefault(current_parent, {})[key.strip()] = val
        elif ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            val = val.strip()
            if val == "":
                current_parent = key.strip()
                result[current_parent] = {}
            else:
                current_parent = None
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                result[key.strip()] = val
    return result


def get_length_config(book_dir: Path) -> dict:
    """读 book_rules.md 的 length 字段。若未配置，返回默认值"""
    book_rules = book_dir / "story/book_rules.md"
    defaults = {
        "target": 4500,
        "softMinPct": 10,
        "softMaxPct": 10,
        "hardMinPct": 20,
        "hardMaxPct": 20,
        "countingMode": "zh_chars",
        "enforceSoftMin": True,
        "enforceHardMin": True,
    }
    if not book_rules.exists():
        return defaults
    fm = parse_yaml_frontmatter(book_rules.read_text(encoding="utf-8"))
    length = fm.get("length", {})
    out = {**defaults, **length}
    return out


def compute_length_thresholds(cfg: dict) -> dict:
    t = cfg["target"]
    return {
        "target": t,
        "softMin": int(t * (1 - cfg["softMinPct"] / 100)),
        "softMax": int(t * (1 + cfg["softMaxPct"] / 100)),
        "hardMin": int(t * (1 - cfg["hardMinPct"] / 100)),
        "hardMax": int(t * (1 + cfg["hardMaxPct"] / 100)),
    }


# ==============================================================
# Layer 1: 强制不变量
# ==============================================================

def verify_layer1(book_dir: Path, N: int) -> tuple[bool, list]:
    errors = []

    # 1. chapters/<NNNN>_*.md 存在
    ch_pattern = f"{N:04d}_*.md"
    chapters = list((book_dir / "chapters").glob(ch_pattern))
    if not chapters:
        errors.append(f"chapters/{ch_pattern} 不存在")
        chapter_file = None
    else:
        chapter_file = chapters[0]
        if chapter_file.stat().st_size == 0:
            errors.append(f"{chapter_file.name} 是空文件")

    # 2. index.json 有该章条目且 status ∈ {approved, audited}
    index_path = book_dir / "chapters/index.json"
    if not index_path.exists():
        errors.append("chapters/index.json 不存在")
    else:
        data = json.loads(index_path.read_text(encoding="utf-8"))
        entry = next((c for c in data if c.get("number") == N), None)
        if not entry:
            errors.append(f"index.json 无 ch{N} 条目")
        else:
            status = entry.get("status")
            if status not in ("approved", "audited"):
                errors.append(
                    f"index.json ch{N}.status = '{status}'，应为 approved 或 audited"
                )

    # 3. snapshots/<N>/ 存在 + 7 个 truth files
    snap = book_dir / f"story/snapshots/{N}"
    required_truth_files = [
        "current_state.md",
        "particle_ledger.md",
        "pending_hooks.md",
        "subplot_board.md",
        "emotional_arcs.md",
        "character_matrix.md",
        "chapter_summaries.md",
    ]
    if not snap.is_dir():
        errors.append(f"snapshots/{N}/ 目录不存在")
    else:
        for tf in required_truth_files:
            if not (snap / tf).exists():
                errors.append(f"snapshots/{N}/{tf} 缺失")

    # 4. current_state.md 的"当前章节"字段 >= N
    # （严格等于只适用于最新章。对历史章节做 verify 时，current_state 可能已被更新到更高章号）
    cs_path = book_dir / "story/current_state.md"
    if not cs_path.exists():
        errors.append("story/current_state.md 不存在")
    else:
        cs_text = cs_path.read_text(encoding="utf-8")
        m = re.search(r"\|\s*当前章节\s*\|\s*(\d+)", cs_text)
        if not m:
            errors.append("current_state.md 没有'当前章节'行")
        elif int(m.group(1)) < N:
            errors.append(
                f"current_state.md 当前章节 = {m.group(1)}，应 ≥ {N}"
                f"（说明 ch{N} 写完后未更新 current_state）"
            )

    # 5. chapter_summaries.md 包含 ch N 行
    cs_md = book_dir / "story/chapter_summaries.md"
    if not cs_md.exists():
        errors.append("story/chapter_summaries.md 不存在")
    else:
        text = cs_md.read_text(encoding="utf-8")
        if not re.search(rf"^\|\s*{N}\s*\|", text, re.MULTILINE):
            errors.append(f"chapter_summaries.md 没有 ch{N} 行")

    # 6. audits/ch-N.md 存在（除非 autoRunAudit=false）
    book_rules = book_dir / "story/book_rules.md"
    auto_audit = True
    if book_rules.exists():
        fm = parse_yaml_frontmatter(book_rules.read_text(encoding="utf-8"))
        pipeline = fm.get("pipeline", {})
        if pipeline.get("autoRunAudit") is False:
            auto_audit = False
    if auto_audit:
        audit_path = book_dir / f"story/audits/ch-{N}.md"
        if not audit_path.exists():
            errors.append(
                f"audits/ch-{N}.md 不存在（pipeline.autoRunAudit=true 时必须存在）"
            )

    return (len(errors) == 0, errors)


# ==============================================================
# Layer 2: 机械规则
# ==============================================================

FORBIDDEN_PATTERNS = [
    ("破折号 ——", re.compile(r"——")),
    ("不是...而是...", re.compile(r"不是[^，。！？\n]{0,30}[，,]?\s*而是")),
    (
        "分析术语",
        re.compile(
            r"核心动机|信息边界|信息落差|核心风险|利益最大化|"
            r"当前处境|行为约束|性格过滤|情绪外化|锚定效应|沉没成本|认知共鸣"
        ),
    ),
    ("markdown 水平线 ---", re.compile(r"^---$", re.MULTILINE)),
    ("markdown 标题 ##", re.compile(r"^#{2,6} ", re.MULTILINE)),  # 正文不允许 2-6 级标题
    ("markdown 行内代码 `", re.compile(r"`[^`\n]+`")),
    ("markdown 代码块 ```", re.compile(r"```")),
    ("markdown 列表 `- `", re.compile(r"^[-*] ", re.MULTILINE)),
    ("markdown 有序列表", re.compile(r"^\d+\. ", re.MULTILINE)),
    ("markdown 粗体 **", re.compile(r"\*\*[^*\n]+\*\*")),
    ("markdown callout", re.compile(r"^> \[!", re.MULTILINE)),
]


def verify_layer2(book_dir: Path, N: int, allow_short: bool = False) -> tuple[bool, list]:
    errors = []

    # 读章节正文
    chapters = list((book_dir / "chapters").glob(f"{N:04d}_*.md"))
    if not chapters:
        return (False, ["chapters/<N>.md 不存在（Layer 1 应该已经报过）"])
    content = chapters[0].read_text(encoding="utf-8")

    # 跳过第一行的 # 第 N 章 <标题>
    body_lines = content.splitlines()
    if body_lines and body_lines[0].startswith("# 第"):
        body = "\n".join(body_lines[1:])
    else:
        body = content

    # 扫描禁令
    for name, pattern in FORBIDDEN_PATTERNS:
        matches = pattern.findall(body)
        if matches:
            errors.append(f"正文出现 {name}，数量 {len(matches)}")

    # 字数检查
    cfg = get_length_config(book_dir)
    th = compute_length_thresholds(cfg)
    word_count = count_cjk(body) if cfg["countingMode"] == "zh_chars" else len(body.split())

    if word_count < th["hardMin"]:
        errors.append(
            f"字数 {word_count} < hardMin {th['hardMin']}（硬违规，即使声明允许偏短也不放过）"
        )
    elif word_count < th["softMin"] and not allow_short:
        errors.append(
            f"字数 {word_count} < softMin {th['softMin']}（若本章允许偏短，请用 --allow-short）"
        )
    elif word_count > th["hardMax"]:
        errors.append(
            f"字数 {word_count} > hardMax {th['hardMax']}（超长，需压缩）"
        )

    # v0.1.10: Followup 机制强制约束
    followup_errors = verify_followup_mechanism(book_dir, N)
    errors.extend(followup_errors)

    return (len(errors) == 0, errors)


def _parse_audit_followup_section(audit_path: Path) -> tuple[bool, list]:
    """
    返回 (has_followup_section, open_items)。
    open_items 是 [ ] 状态的 followup 条目文本列表。
    """
    if not audit_path.exists():
        return (False, [])
    text = audit_path.read_text(encoding="utf-8")
    # 找 `## Followup` 段（允许 `## Followup` 或 `## Followup（跨章监测项）` 等）
    m = re.search(r"^## Followup\b.*?$", text, re.MULTILINE)
    if not m:
        return (False, [])
    # 段内容 = 从标题之后到下一个 `## ` 或文件末尾
    start = m.end()
    next_h = re.search(r"^## ", text[start:], re.MULTILINE)
    section = text[start:start + next_h.start()] if next_h else text[start:]
    open_items = [
        line.strip() for line in section.splitlines()
        if re.match(r"^\s*-\s*\[\s*\]\s", line)
    ]
    return (True, open_items)


def verify_followup_mechanism(book_dir: Path, N: int) -> list:
    """
    v0.1.10 新增 Layer 2 检查：
      (a) audits/ch-N.md 末尾必须有 `## Followup` 段（缺段 = ❌）
      (b) PROGRESS.md 的活跃 followup 内容 = 所有 audits/ch-*.md `## Followup` 里 [ ] 条目聚合（不一致 = ❌）
    """
    errors = []
    audit_path = book_dir / f"story/audits/ch-{N}.md"
    # 检查 a
    if audit_path.exists():
        has_section, _ = _parse_audit_followup_section(audit_path)
        if not has_section:
            errors.append(
                f"FOLLOWUP: audits/ch-{N}.md 缺 `## Followup` 段（v0.1.10 起强制）"
            )
    # 检查 b
    progress_path = book_dir / "PROGRESS.md"
    if not progress_path.exists():
        return errors  # 无 PROGRESS.md 时不检查这项
    progress_text = progress_path.read_text(encoding="utf-8")
    m = re.search(r"^## 📌 活跃 followup.*?$", progress_text, re.MULTILINE)
    if not m:
        errors.append("FOLLOWUP: PROGRESS.md 缺 `## 📌 活跃 followup` 段")
        return errors
    start = m.end()
    next_h = re.search(r"^## ", progress_text[start:], re.MULTILINE)
    progress_section = progress_text[start:start + next_h.start()] if next_h else progress_text[start:]
    progress_items = {
        line.strip() for line in progress_section.splitlines()
        if re.match(r"^\s*-\s*\[\s*\]\s", line)
    }
    # 聚合所有 audits/ch-*.md 的 [ ] followup
    aggregated = set()
    audits_dir = book_dir / "story/audits"
    if audits_dir.exists():
        for ap in sorted(audits_dir.glob("ch-*.md")):
            _, items = _parse_audit_followup_section(ap)
            aggregated.update(items)
    # 允许描述略有不同（PROGRESS.md 可能带"来源 chX"括号），做宽松匹配：
    # 只要 audit open items 的核心 description 能在 progress 某行里找到子串即可
    def normalize(s):
        return re.sub(r"\s+", "", s.lower())
    progress_normalized = [normalize(p) for p in progress_items]
    missing = []
    for item in aggregated:
        # 提取"冒号后"的核心描述
        core = item.split("：", 1)[-1].split(":", 1)[-1]
        core_n = normalize(core)
        if not any(core_n[:20] in pn for pn in progress_normalized):
            missing.append(item)
    if missing:
        errors.append(
            f"FOLLOWUP: PROGRESS.md 活跃 followup 段与 audits 聚合不一致，缺 {len(missing)} 条（例：{missing[0][:60]}）"
        )
    return errors


# ==============================================================
# Layer 3: 条件性副作用
# ==============================================================

def verify_layer3(book_dir: Path, N: int) -> tuple[bool, list]:
    """
    读 audits/ch-N.md 的 callout 内容，推断本章应该更新的 truth files。
    典型信号：
      - callout 里提 "H004 推进" → pending_hooks.md 必须含 ch15 相关更新
      - callout 里提 "S003 关闭" → subplot_board.md 该支线 status 应 resolved
      - callout 里提 "新增 X 角色" → character_matrix.md 有新行
      - callout 里提 "ledger / 资源 / 情报权" → particle_ledger.md 有 ch N 行
    如果 audits 未声明某个 truth file 变动 → 不检查（条件性）
    """
    errors = []
    audit_path = book_dir / f"story/audits/ch-{N}.md"
    if not audit_path.exists():
        return (True, [])  # Layer 1 已处理
    audit_text = audit_path.read_text(encoding="utf-8").lower()

    checks = [
        (
            ["hook", "伏笔", "h0", "h1", "h2"],
            "pending_hooks.md",
            None,  # 不检查特定行数变化，只检查文件 mtime 新于章节正文即可；这里简化为存在即可
        ),
        (
            ["subplot", "支线", "s00", "s01"],
            "subplot_board.md",
            None,
        ),
        (
            ["emotional", "情感", "情绪"],
            "emotional_arcs.md",
            lambda text: re.search(rf"\|\s*[^|]+\s*\|\s*{N}\s*\|", text) is not None,
        ),
        (
            ["ledger", "资源", "情报权", "账本"],
            "particle_ledger.md",
            lambda text: re.search(rf"^\|\s*{N}\s*\|", text, re.MULTILINE) is not None,
        ),
        (
            ["character", "角色", "matrix"],
            "character_matrix.md",
            None,
        ),
    ]

    for keywords, tf_name, extra_check in checks:
        mentioned = any(kw in audit_text for kw in keywords)
        if not mentioned:
            continue  # 审计未声明 → 不检查
        tf_path = book_dir / f"story/{tf_name}"
        if not tf_path.exists():
            errors.append(f"审计声明涉及 {tf_name} 但文件不存在")
            continue
        if extra_check:
            tf_text = tf_path.read_text(encoding="utf-8")
            if not extra_check(tf_text):
                errors.append(f"审计声明 ch{N} 推进 {tf_name}，但文件里找不到 ch{N} 相关行")

    return (len(errors) == 0, errors)


# ==============================================================
# Followup 修复（--fix-progress）
# ==============================================================

def recompute_progress_followup(book_dir: Path) -> tuple[bool, int]:
    """
    聚合所有 audits/ch-*.md `## Followup` 段里的 [ ] 条目，重写 PROGRESS.md 的
    `## 📌 活跃 followup` 段。只覆盖这一段，其他段一字不动。
    返回 (修改成功, 写入条数)。
    """
    audits_dir = book_dir / "story/audits"
    progress_path = book_dir / "PROGRESS.md"
    if not progress_path.exists():
        return (False, 0)
    open_items = []
    if audits_dir.exists():
        def _ch_num(p: Path) -> int:
            m = re.search(r"ch-(\d+)", p.name)
            return int(m.group(1)) if m else 0
        for ap in sorted(audits_dir.glob("ch-*.md"), key=_ch_num):
            _, items = _parse_audit_followup_section(ap)
            open_items.extend(items)
    text = progress_path.read_text(encoding="utf-8")
    new_block = "## 📌 活跃 followup  <!-- replace-on-update; 从 story/audits/ 重算 -->\n\n"
    new_block += "> 每次 Settler 结束前从所有 `story/audits/ch-*.md` 的 `## Followup` 段里 `[ ]` 条目聚合。\n\n"
    if not open_items:
        new_block += "- 暂无活跃 followup\n"
    else:
        for item in open_items:
            new_block += item + "\n"
    new_block += "\n"
    pattern = re.compile(r"^## 📌 活跃 followup.*?(?=^## )", re.MULTILINE | re.DOTALL)
    if not pattern.search(text):
        return (False, 0)  # PROGRESS.md 无该段，拒绝盲写
    new_text = pattern.sub(new_block, text)
    progress_path.write_text(new_text, encoding="utf-8")
    return (True, len(open_items))


# ==============================================================
# Main
# ==============================================================

def classify_l1_errors(errors: list) -> dict:
    """将 Layer 1 错误按环节归类，便于生成 per-step checklist"""
    buckets = {
        "正文": [],
        "index.json": [],
        "snapshot": [],
        "current_state": [],
        "chapter_summaries": [],
        "audit": [],
    }
    for e in errors:
        if "chapters/" in e and "index.json" not in e:
            buckets["正文"].append(e)
        elif "index.json" in e:
            buckets["index.json"].append(e)
        elif "snapshots/" in e:
            buckets["snapshot"].append(e)
        elif "current_state" in e:
            buckets["current_state"].append(e)
        elif "chapter_summaries" in e:
            buckets["chapter_summaries"].append(e)
        elif "audit" in e:
            buckets["audit"].append(e)
    return buckets


def classify_l2_errors(errors: list) -> dict:
    """将 Layer 2 错误按环节归类"""
    buckets = {"机械禁令": [], "字数": [], "followup": []}
    for e in errors:
        if e.startswith("FOLLOWUP:"):
            buckets["followup"].append(e.replace("FOLLOWUP: ", "", 1))
        elif "字数" in e:
            buckets["字数"].append(e)
        else:
            buckets["机械禁令"].append(e)
    return buckets


def classify_l3_errors(errors: list) -> dict:
    """将 Layer 3 错误按 truth file 归类"""
    buckets = {
        "pending_hooks": [],
        "subplot_board": [],
        "emotional_arcs": [],
        "particle_ledger": [],
        "character_matrix": [],
    }
    for e in errors:
        for tf in buckets:
            if tf in e:
                buckets[tf].append(e)
                break
    return buckets


def print_step(label: str, errors: list) -> bool:
    """单个环节的 ✅/❌ 行，返回 True 表示通过"""
    if not errors:
        print(f"  ✅ {label}")
        return True
    print(f"  ❌ {label}")
    for e in errors:
        print(f"       · {e}")
    return False


def main():
    parser = argparse.ArgumentParser(description="章节完成流程审核（per-step checklist）")
    parser.add_argument("books_root", help="books 根目录绝对路径")
    parser.add_argument("book_name", help="书名")
    parser.add_argument("N", type=int, help="章节号")
    parser.add_argument(
        "--allow-short",
        action="store_true",
        help="允许字数低于 softMin（需在 PRE_WRITE_CHECK 声明）",
    )
    parser.add_argument(
        "--fix-progress",
        action="store_true",
        help="仅在检测到 PROGRESS.md 活跃 followup 段与 audits 聚合不一致时，自动重写该段（只覆盖 📌 活跃 followup 段，其他段不动）。重写完成后重跑一遍 Layer 2 再输出。",
    )
    args = parser.parse_args()

    book_dir = Path(args.books_root) / args.book_name
    if not book_dir.is_dir():
        print(f"❌ 书籍目录不存在：{book_dir}", file=sys.stderr)
        sys.exit(99)

    print(f"=== 第 {args.N} 章流程审核（{args.book_name}）===\n")

    # 跑三层检查（保留内部逻辑不变）
    ok1, errs1 = verify_layer1(book_dir, args.N)
    ok2, errs2 = verify_layer2(book_dir, args.N, allow_short=args.allow_short)
    ok3, errs3 = verify_layer3(book_dir, args.N)

    # --fix-progress: 若 Layer 2 里有 followup 段不一致错误，重写后重跑 Layer 2
    if args.fix_progress:
        needs_fix = any(
            e.startswith("FOLLOWUP:") and "活跃 followup 段与 audits 聚合不一致" in e
            for e in errs2
        )
        if needs_fix:
            fixed, n = recompute_progress_followup(book_dir)
            if fixed:
                print(f"🔧 --fix-progress 已生效：PROGRESS.md 📌 活跃 followup 段重写 {n} 条\n")
                ok2, errs2 = verify_layer2(book_dir, args.N, allow_short=args.allow_short)
            else:
                print("⚠️ --fix-progress 无法生效：PROGRESS.md 不存在或无 📌 活跃 followup 段\n")

    l1 = classify_l1_errors(errs1)
    l2 = classify_l2_errors(errs2)
    l3 = classify_l3_errors(errs3)

    # Per-step checklist 输出
    print("【Step 5 · 写正文】")
    s_write = print_step("chapters/<N>_*.md 存在且非空", l1["正文"])
    print()

    print("【Step 6 · 机械规则校验】")
    s_ban = print_step(
        "禁令扫描（破折号/不是而是/分析术语/markdown 泄漏）",
        l2["机械禁令"],
    )
    s_len = print_step("字数区间检查", l2["字数"])
    print()

    print("【Step 7 · 审计】")
    s_audit = print_step("story/audits/ch-N.md 存在", l1["audit"])
    s_fup = print_step("audit 末尾 `## Followup` 段存在（v0.1.10）", l2["followup"])
    print()

    print("【Step 9 · 结算：7 个 truth files】")
    s_cs = print_step(f"current_state.md 当前章节 ≥ {args.N}", l1["current_state"])
    s_sum = print_step("chapter_summaries.md 含 ch N 行", l1["chapter_summaries"])
    # Layer 3 条件性（只有审计声明涉及时才检查）
    s_hooks = print_step(
        "pending_hooks.md（若审计声明涉及）", l3["pending_hooks"]
    )
    s_sub = print_step(
        "subplot_board.md（若审计声明涉及）", l3["subplot_board"]
    )
    s_emo = print_step(
        "emotional_arcs.md（若审计声明涉及）", l3["emotional_arcs"]
    )
    s_led = print_step(
        "particle_ledger.md（若审计声明涉及）", l3["particle_ledger"]
    )
    s_cm = print_step(
        "character_matrix.md（若审计声明涉及）", l3["character_matrix"]
    )
    print()

    print("【Step 10 · 快照】")
    s_snap = print_step(
        f"snapshots/{args.N}/ 存在且含 7 个 truth files", l1["snapshot"]
    )
    print()

    print("【Step 11 · 索引更新】")
    s_idx = print_step(
        "index.json 含 ch N 条目且 status ∈ {approved, audited}", l1["index.json"]
    )
    print()

    # 汇总
    all_steps = [s_write, s_ban, s_len, s_audit, s_fup, s_cs, s_sum,
                 s_hooks, s_sub, s_emo, s_led, s_cm, s_snap, s_idx]
    total_pass = sum(1 for s in all_steps if s)
    total = len(all_steps)

    print("=" * 50)
    if ok1 and ok2 and ok3:
        print(f"✅ 流程审核全部通过（{total}/{total} 环节）")
        print(f"🎉 第 {args.N} 章完成")
        sys.exit(0)
    else:
        print(f"❌ 流程审核未通过（{total_pass}/{total} 环节）")
        # 保留原有 exit code 语义
        if not ok1:
            print("   · Layer 1 失败：补齐上方 ❌ 的强制不变量环节")
            sys.exit(1)
        if not ok2:
            print("   · Layer 2 失败：回到 Step 6 机械规则检查 + 修订")
            sys.exit(2)
        if not ok3:
            print("   · Layer 3 失败：审计声明与 truth file 改动不一致，补 Step 9 结算")
            sys.exit(3)


if __name__ == "__main__":
    main()
