#!/usr/bin/env python3
"""
merge-truth.py — 确定性合并 inkOS 真相文件

使用场景（按 02-truth-schema.md 的 merge 边界规则）：
- 从快照恢复后重建
- 批量 rebuild（ledger / hooks 等）
- 导入外部章节

不用于日常写章结算（日常结算由 LLM 自己 read→modify→write）。

用法：
    python3 merge-truth.py <file_type> <existing_path> <incoming_path> [--out <output_path>]

file_type 枚举：
    ledger / hooks / subplots / emotional_arcs / chapter_summaries / character_matrix

行为：
    1. 读取现有文件 + 新增文件
    2. 按文件类型的合并 key 去重合并（同 key 覆盖，新 key 追加）
    3. Schema 守卫：header 不一致/列数不对 → 报错退出，不覆盖
    4. 写入输出路径（默认覆盖 existing_path）

退出码：
    0 = 成功
    1 = schema 不一致 / 解析失败
    2 = 文件不存在
"""

import argparse
import hashlib
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# --- 合并 key 定义（与 02-truth-schema.md 一致）---

MERGE_KEYS = {
    "ledger": [6],              # 事件ID（第 7 列，0-index 6）
    "hooks": [0],               # hook_id
    "subplots": [0],            # 支线ID
    "emotional_arcs": [0, 1],   # 角色 + 章节
    "chapter_summaries": [0],   # 章节号
}

# character_matrix 是 3 子表，特殊处理
MATRIX_SECTION_KEYS = {
    "角色档案": [0],            # 角色
    "相遇记录": [0, 1],         # 角色A + 角色B
    "信息边界": [0, 3],         # 角色 + 信息来源章
}

# Sentinel（从 02-truth-schema.md）
SENTINELS = {
    "☆ 资源账本无变动 ☆",
    "☆ 伏笔池无变动 ☆",
    "☆ 支线进度板无变动 ☆",
    "☆ 情感弧线无变动 ☆",
    "☆ 角色交互矩阵无变动 ☆",
    "☆ 章节摘要无变动 ☆",
    "(资源账本未更新)",
    "(伏笔池未更新)",
    "(支线板未更新)",
}


def is_sentinel(content: str) -> bool:
    stripped = content.strip()
    return stripped in SENTINELS


def parse_table(markdown: str) -> Tuple[List[str], List[str], List[List[str]], List[str]]:
    """
    解析一个 markdown 表格。
    返回 (leading_lines, header_cells, data_rows, trailing_lines)。
    header_cells 为空则表示没找到表格。
    """
    lines = markdown.splitlines()
    leading = []
    header_cells = []
    separator_idx = -1
    data_rows = []
    trailing = []

    # 找第一个表格行
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|"):
            header_cells = split_row(line)
            # 下一行应该是 separator
            if i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
                sep_line = lines[i + 1]
                if "---" in sep_line:
                    separator_idx = i + 1
                    break
        leading.append(line)
        i += 1

    if not header_cells or separator_idx == -1:
        return leading, [], [], []

    # 读 data rows
    j = separator_idx + 1
    while j < len(lines):
        line = lines[j]
        if line.strip().startswith("|"):
            data_rows.append(split_row(line))
        else:
            break
        j += 1

    # 剩下的是 trailing
    trailing = lines[j:]

    return leading, header_cells, data_rows, trailing


def split_row(line: str) -> List[str]:
    """拆分 markdown 表格行为 cell 列表。"""
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def render_row(cells: List[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def build_key(row: List[str], key_cols: List[int]) -> str:
    return "::".join(row[i] if i < len(row) else "" for i in key_cols)


def normalize_headers(a: List[str], b: List[str]) -> bool:
    """Schema 守卫：比较两个 header 是否一致（列数 + 列名）。"""
    if len(a) != len(b):
        return False
    return [h.strip() for h in a] == [h.strip() for h in b]


def merge_table(existing: str, incoming: str, key_cols: List[int]) -> str:
    """
    按 key 列合并两个表格。返回合并后的 markdown。
    """
    if is_sentinel(incoming):
        # 新内容是 sentinel → 保留 existing
        return existing

    ex_leading, ex_header, ex_rows, ex_trailing = parse_table(existing)
    in_leading, in_header, in_rows, _ = parse_table(incoming)

    # 如果 existing 没表格，直接用 incoming
    if not ex_header:
        return incoming

    # Schema 守卫
    if in_header and not normalize_headers(ex_header, in_header):
        raise ValueError(
            f"Schema mismatch: existing header {ex_header} != incoming header {in_header}"
        )

    # 建索引：key → row
    index = {}
    order = []
    for row in ex_rows:
        key = build_key(row, key_cols)
        if key not in index:
            order.append(key)
        index[key] = row

    # 应用 incoming：同 key 覆盖，新 key 追加
    for row in in_rows:
        key = build_key(row, key_cols)
        if key not in index:
            order.append(key)
        index[key] = row

    merged_rows = [index[k] for k in order]

    # 重建
    header_line = render_row(ex_header)
    sep_line = "| " + " | ".join("-" * max(3, len(h)) for h in ex_header) + " |"
    output_lines = list(ex_leading) + [header_line, sep_line] + [render_row(r) for r in merged_rows]
    if ex_trailing:
        output_lines.extend(ex_trailing)
    return "\n".join(output_lines)


# --- Ledger 特殊：normalize + auto event-id fallback ---

def auto_event_id(row: List[str]) -> str:
    """为缺失事件ID 的 ledger 行生成确定性 fallback ID。"""
    content = "|".join(row[:6])
    digest = hashlib.sha1(content.encode("utf-8")).hexdigest()[:6]
    chapter = row[0] if row else "0"
    return f"auto-ch{chapter}-{digest}"


def normalize_ledger(markdown: str) -> str:
    """补齐 6 列 ledger 为 7 列（加事件ID），修正缺失的事件ID。"""
    leading, header, rows, trailing = parse_table(markdown)
    if not header:
        return markdown

    LEDGER_HEADER = ["章节", "资源名称", "期初", "变动", "期末", "事由", "事件ID"]

    # 6 列 → 7 列
    if len(header) == 6 and header == LEDGER_HEADER[:6]:
        header = LEDGER_HEADER
        rows = [row + [auto_event_id(row)] for row in rows]
    elif len(header) != 7:
        raise ValueError(f"Unexpected ledger header: {header}")

    # 补齐缺失事件ID
    for i, row in enumerate(rows):
        if len(row) < 7:
            row = row + [""] * (7 - len(row))
            rows[i] = row
        if not row[6].strip():
            row[6] = auto_event_id(row)

    header_line = render_row(header)
    sep_line = "| " + " | ".join("-" * max(3, len(h)) for h in header) + " |"
    out = list(leading) + [header_line, sep_line] + [render_row(r) for r in rows]
    if trailing:
        out.extend(trailing)
    return "\n".join(out)


# --- Character matrix：3 子表特殊合并 ---

def parse_sections(markdown: str) -> Tuple[List[str], List[Tuple[str, str]]]:
    """解析 character_matrix：返回 (top_lines, [(heading, body), ...])"""
    lines = markdown.splitlines()
    top = []
    sections = []
    current_heading = None
    current_body = []
    for line in lines:
        if line.startswith("### "):
            if current_heading:
                sections.append((current_heading, "\n".join(current_body)))
            current_heading = line[4:].strip()
            current_body = []
        elif current_heading:
            current_body.append(line)
        else:
            top.append(line)
    if current_heading:
        sections.append((current_heading, "\n".join(current_body)))
    return top, sections


def merge_character_matrix(existing: str, incoming: str) -> str:
    """4-case merge for character_matrix."""
    if is_sentinel(incoming):
        return existing

    _, ex_sections = parse_sections(existing)
    _, in_sections = parse_sections(incoming)

    ex_is_sectioned = len(ex_sections) > 0
    in_is_sectioned = len(in_sections) > 0

    if not ex_is_sectioned and not in_is_sectioned:
        # 都是扁平 → 按 [0] 合并
        return merge_table(existing, incoming, [0])
    if not ex_is_sectioned and in_is_sectioned:
        # 升级到 3-sub → 接受 incoming
        return incoming
    if ex_is_sectioned and not in_is_sectioned:
        # 拒绝 schema 退化 → 保留 existing
        return existing

    # 都是 3-sub → 按 section 合并
    ex_map = {h: b for h, b in ex_sections}
    in_map = {h: b for h, b in in_sections}
    all_headings = list(ex_map.keys())
    for h in in_map:
        if h not in all_headings:
            all_headings.append(h)

    merged_parts = ["# 角色交互矩阵", ""]
    for h in all_headings:
        key_cols = MATRIX_SECTION_KEYS.get(h, [0])
        ex_body = ex_map.get(h, "")
        in_body = in_map.get(h, "")
        if ex_body and in_body:
            merged = merge_table(ex_body, in_body, key_cols)
        else:
            merged = ex_body or in_body
        merged_parts.append(f"### {h}")
        merged_parts.append(merged)
        merged_parts.append("")

    return "\n".join(merged_parts)


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="确定性合并 inkOS 真相文件")
    parser.add_argument("file_type", choices=list(MERGE_KEYS.keys()) + ["character_matrix"])
    parser.add_argument("existing_path")
    parser.add_argument("incoming_path")
    parser.add_argument("--out", help="输出路径（默认覆盖 existing_path）")
    args = parser.parse_args()

    existing = Path(args.existing_path)
    incoming = Path(args.incoming_path)

    if not existing.exists():
        print(f"错误：existing 文件不存在: {existing}", file=sys.stderr)
        sys.exit(2)
    if not incoming.exists():
        print(f"错误：incoming 文件不存在: {incoming}", file=sys.stderr)
        sys.exit(2)

    existing_text = existing.read_text(encoding="utf-8")
    incoming_text = incoming.read_text(encoding="utf-8")

    try:
        if args.file_type == "ledger":
            existing_text = normalize_ledger(existing_text)
            incoming_text = normalize_ledger(incoming_text)
            merged = merge_table(existing_text, incoming_text, MERGE_KEYS["ledger"])
        elif args.file_type == "character_matrix":
            merged = merge_character_matrix(existing_text, incoming_text)
        else:
            key_cols = MERGE_KEYS[args.file_type]
            merged = merge_table(existing_text, incoming_text, key_cols)
    except ValueError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.out) if args.out else existing
    out_path.write_text(merged, encoding="utf-8")
    print(f"合并完成：{out_path}")


if __name__ == "__main__":
    main()
