# ink.skill 回归测试 fixture

## test-book/

最小可用的测试书，用于验证：
- `verify-chapter.py` 在各边界条件下的行为
- 字数不足（softMin 之下）的路径
- Step 1-12 全部通过的路径

## 跑法

```bash
# 从 ink-skill 根目录跑（skill_root 指向 ink-skill 仓库根目录）
python3 scripts/verify-chapter.py tests test-book 1

# 期望：exit=2（fixture 章节 80 字 < softMin 90，偏短路径测试）
# 12/13 环节应通过，字数检查失败符合预期
```

## fixture 结构

```
test-book/
├── chapters/
│   ├── index.json
│   └── 0001_临界.md        # 故意偏短（约 80 字），用于测试字数不足路径
└── story/
    ├── audits/              # 审计文件目录
    ├── snapshots/           # 快照目录
    ├── book_rules.md        # 含 softMin=90, hardMin=72 配置
    ├── current_state.md
    ├── chapter_summaries.md
    ├── character_matrix.md
    ├── emotional_arcs.md
    ├── particle_ledger.md
    ├── pending_hooks.md
    └── subplot_board.md
```

## 维护说明

- 不要修改 `0001_临界.md` 的字数，这是故意的边界测试用例
- 如果 `book_rules.md` 的 `softMin` 字段改动，同步更新本 README 的期望 exit code 说明
- 新增测试场景时，在此目录新建 `test-book-N/` 子目录，并在本 README 补充说明
