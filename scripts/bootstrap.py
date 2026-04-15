#!/usr/bin/env python3
"""
ink.skill 自部署脚本。用户第一次 git clone 后，或手动"ink 安装到 X 平台"时调用。

检测当前 AI agent 平台，把当前 skill 目录部署到该平台的 skills 路径。
Mac/Linux 用软链（节省空间 + git pull 全平台同步）；
Windows 优先软链，失败降级到 junction（目录软链）或复制。
"""
import argparse
import os
import platform as sysplatform
import shutil
import subprocess
import sys
from pathlib import Path

PLATFORM_SKILL_PATHS = {
    "claude-code": Path.home() / ".claude" / "skills" / "ink",
    "codex": Path.home() / ".agents" / "skills" / "ink",
    "gemini": Path.home() / ".gemini" / "extensions" / "skills" / "ink",
    "cursor": None,  # Cursor 无标准 skills 路径
}


def detect_platform() -> str:
    """启发式检测当前平台。"""
    if os.environ.get("CLAUDECODE"):
        return "claude-code"
    if os.environ.get("CODEX_AGENT"):
        return "codex"
    if os.environ.get("GEMINI_CLI"):
        return "gemini"
    return "unknown"


def _link_or_copy(source: Path, target: Path) -> str:
    """
    三级降级：symlink → junction (Windows) → copytree。
    返回实际使用的方式："symlink" / "junction" / "copy"。
    """
    target.parent.mkdir(parents=True, exist_ok=True)

    # 尝试 1: 标准 symlink
    try:
        target.symlink_to(source, target_is_directory=True)
        return "symlink"
    except (OSError, NotImplementedError):
        if sysplatform.system() != "Windows":
            raise  # Mac/Linux 理论上不应失败

    # Windows fallback 1: directory junction (mklink /J，无需 admin)
    try:
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(target), str(source)],
            check=True,
            capture_output=True,
        )
        return "junction"
    except Exception:
        pass

    # Windows fallback 2: 整目录复制（失去 git pull 同步）
    shutil.copytree(source, target)
    print(
        f"[warn] 创建了复制（非软链）。日后 git pull 需手动重跑 bootstrap 才能同步。",
        file=sys.stderr,
    )
    return "copy"


def install(platform: str, source: Path) -> None:
    target = PLATFORM_SKILL_PATHS.get(platform)
    if target is None:
        print(f"[warn] {platform} 无标准 skills 路径，跳过自部署")
        return
    if target.exists() or target.is_symlink():
        print(f"[info] {target} 已存在，跳过（如要重装先删除）")
        return
    method = _link_or_copy(source, target)
    print(f"[ok] {method}：{target} → {source}")


def main() -> int:
    parser = argparse.ArgumentParser(description="ink.skill 跨平台自部署")
    parser.add_argument(
        "--platform",
        choices=list(PLATFORM_SKILL_PATHS.keys()) + ["auto"],
        default="auto",
        help="目标平台（默认 auto 自动检测）",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="skill 源目录（默认为本脚本的父目录，即整个 ink-skill/）",
    )
    args = parser.parse_args()

    platform = detect_platform() if args.platform == "auto" else args.platform
    print(f"[info] 检测到平台：{platform}")
    install(platform, args.source.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
