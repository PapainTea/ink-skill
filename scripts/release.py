#!/usr/bin/env python3
"""release.py — 发 ink.skill 新版，保持本地粒度 + 远程 squash 的 A+B 模式。

用法：
    python3 scripts/release.py <tag> "<commit msg>"

示例：
    python3 scripts/release.py v0.1.18 "feat: xxx 修复 + yyy 新增"

行为：
    1. fetch origin 拿最新远程 main SHA
    2. 建一个 _release tmp 分支指到 origin/main
    3. git read-tree -u --reset main —— 把本地 main 整棵树装上去
    4. commit 成单一 squash commit（message = 第 2 个参数）
    5. force push _release:main
    6. 打 tag + push tag
    7. 切回 main + 删 _release

结果：
    - 本地 main 完全不动（保留你写的每一个细粒度 commit）
    - origin/main 新增一条发版节点 commit（squash 版，对应 tag）
    - A（本地粒度）+ B（远程 squash）分叉状态维持
"""

import os
import subprocess
import sys


def run(cmd, check=True, capture=False):
    print(f"$ {cmd}")
    result = subprocess.run(
        cmd, shell=True, check=check, capture_output=capture, text=True
    )
    return result.stdout.strip() if capture else None


def main():
    if len(sys.argv) < 3:
        print("用法: release.py <tag> <commit-msg>")
        print('示例: release.py v0.1.18 "feat: 某某修复"')
        sys.exit(2)

    tag, msg = sys.argv[1], sys.argv[2]

    # 切到 skill 根（脚本自身的父目录的父目录）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(os.path.dirname(script_dir))

    # 预检：当前必须在 main 上，工作区必须干净
    current = run("git rev-parse --abbrev-ref HEAD", capture=True)
    if current != "main":
        print(f"❌ 当前分支 {current}，必须先 checkout main")
        sys.exit(2)
    if run("git status --porcelain", capture=True):
        print("❌ 工作区不干净，先 commit 或 stash")
        sys.exit(2)

    # 1. fetch
    run("git fetch origin")

    # 2. 拿 origin/main SHA
    base = run("git rev-parse origin/main", capture=True)
    print(f"squash 基线：{base}")

    # 3. 建 _release 在 base
    run(f"git branch -f _release {base}")
    run("git checkout _release")

    try:
        # 4. load main 整棵树
        run("git read-tree -u --reset main")

        # 5. commit（若无 diff 则终止；避免空 commit）
        if not run("git status --porcelain", capture=True):
            print("⚠ 本地 main 与远程 main 内容一致，无需发版")
            run("git checkout main")
            run("git branch -D _release")
            sys.exit(1)
        # 用 heredoc 风格传 msg，避免 shell 转义问题
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(msg)
            msg_file = f.name
        run(f"git commit -F {msg_file}")
        os.unlink(msg_file)

        # 6. force push
        run("git push --force origin _release:main")

        # 7. tag + push
        run(f"git tag {tag}")
        run(f"git push origin {tag}")

    finally:
        # 切回 main + 清理 _release
        run("git checkout main")
        run("git branch -D _release", check=False)

    print(f"\n✅ 发版 {tag} 完成")
    print("   本地 main（粒度）和 origin/main（squash）维持 A+B 分叉")


if __name__ == "__main__":
    main()
