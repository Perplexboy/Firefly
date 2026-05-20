#!/usr/bin/env python3
"""
Claude Code Chat Exporter — 导出 Claude Code 对话记录为 Markdown 文件
=========================================================================

每次与 Claude Code 对话结束后，自动（或手动）将当前会话的完整聊天记录
保存为格式化的 Markdown 文档，存储于项目根目录。

输出文件命名:  talk_YYYY_MM_DD_HH_mm.md

用法:
    python scripts/export_chat.py                    # 导出当前会话
    python scripts/export_chat.py --session <id>     # 导出指定会话
    python scripts/export_chat.py --all              # 导出本项目所有会话
    python scripts/export_chat.py --dir ./chats      # 指定输出目录
    python scripts/export_chat.py --latest           # 导出最新一次会话

支持场景:
    - Windows 本地打开项目 (Git Bash / PowerShell / CMD)
    - WSL Remote 远程打开项目
    - SSH Remote / Dev Container 远程打开项目

语言选择: Python
    - VS Code Remote 环境下 Python 几乎总是可用
    - 跨平台路径处理能力强
    - 无需编译，直接运行
    - JSONL 解析简洁
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
EXPORT_TRACKER = ".chat_exports.json"  # 记录已导出会话的跟踪文件
CST = timezone(timedelta(hours=8))     # 北京时间


# ---------------------------------------------------------------------------
# 环境检测
# ---------------------------------------------------------------------------

def is_wsl() -> bool:
    """检测当前是否在 WSL 环境中运行。"""
    if sys.platform == "win32":
        return False
    try:
        with open("/proc/version", "r", encoding="utf-8") as f:
            return "microsoft" in f.read().lower()
    except (FileNotFoundError, PermissionError):
        return False


def get_home_dir() -> Path:
    """获取用户主目录，兼容 Windows / WSL / Linux。"""
    if sys.platform == "win32":
        return Path(os.environ.get("USERPROFILE", Path.home()))
    return Path.home()


def find_claude_sessions_dir() -> Optional[Path]:
    """
    定位 Claude Code 的 sessions 存储目录。

    Claude Code 将所有对话存储在:
      ~/.claude/projects/<project-hash>/
    其中 <project-hash> 是项目路径的规范化哈希。
    """
    home = get_home_dir()
    candidates = [
        home / ".claude" / "projects",
    ]
    # WSL 环境下，额外尝试通过 Windows 路径访问
    if is_wsl():
        win_user = os.environ.get("USER", os.environ.get("USERNAME", ""))
        if win_user:
            candidates.append(
                Path(f"/mnt/c/Users/{win_user}/.claude/projects")
            )

    for p in candidates:
        if p.exists() and p.is_dir():
            return p.resolve()
    return None


def find_project_sessions(sessions_dir: Path, project_dir: Path) -> List[Path]:
    """
    在 sessions 目录中查找属于当前项目的所有 JSONL 会话文件。

    匹配策略:
      1. 读取每个 JSONL 文件的第一条有效记录，检查其 cwd 是否匹配
      2. 同时匹配目录名（project-hash）
    """
    project_str = str(project_dir.resolve()).replace("\\", "/").lower()

    jsonl_files = sorted(
        sessions_dir.glob("**/*.jsonl"), key=lambda f: f.stat().st_mtime
    )

    matching = []
    for jf in jsonl_files:
        if not _jsonl_matches_project(jf, project_str):
            continue
        matching.append(jf)

    return matching


def _jsonl_matches_project(jsonl_path: Path, project_str: str) -> bool:
    """检查 JSONL 文件是否属于指定项目（通过第一行的 cwd 匹配）。"""
    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cwd = obj.get("cwd", "")
                if not cwd:
                    continue
                cwd_norm = cwd.replace("\\", "/").lower()
                if cwd_norm == project_str or cwd_norm.startswith(
                    project_str
                ):
                    return True
                # WSL mount path matching (/mnt/c/... vs C:\...)
                if cwd_norm.startswith("/mnt/"):
                    win_path = _wsl_to_win(cwd_norm)
                    if win_path and (
                        win_path == project_str
                        or win_path.startswith(project_str)
                    ):
                        return True
                break  # Only check first line with cwd
    except (OSError, UnicodeDecodeError):
        pass
    return False


def _wsl_to_win(wsl_path: str) -> Optional[str]:
    """将 /mnt/c/... 路径转回 C:/... 格式用于比较。"""
    parts = wsl_path.lstrip("/").split("/", 2)
    if len(parts) >= 2 and parts[0] == "mnt" and len(parts[1]) == 1:
        drive = parts[1].upper()
        rest = parts[2] if len(parts) > 2 else ""
        return f"{drive}:/{rest}".lower()
    return None


def get_session_id_from_env() -> Optional[str]:
    """从环境变量获取当前 Claude Code 会话 ID。"""
    return os.environ.get("CLAUDE_CODE_SESSION_ID")


# ---------------------------------------------------------------------------
# JSONL 解析
# ---------------------------------------------------------------------------

def parse_session_jsonl(jsonl_path: Path) -> Dict:
    """
    解析单个 JSONL 会话文件，提取会话元数据和对话轮次。

    返回:
        {
            "session_id": str,
            "cwd": str,
            "git_branch": str,
            "start_time": datetime,
            "end_time": datetime,
            "turns": [
                {"index": int, "user": str, "assistant": str, "timestamp": str}
            ]
        }
    """
    session_id = None
    cwd = ""
    git_branch = ""
    start_time = None
    end_time = None
    turns: List[Dict] = []
    current_turn: Dict = {}
    turn_index = 0

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            t = obj.get("type", "")

            # 提取会话元数据
            if not session_id:
                session_id = obj.get("sessionId", "")
            if not cwd:
                cwd = obj.get("cwd", "")
            if not git_branch:
                git_branch = obj.get("gitBranch", "")

            # 提取时间戳
            ts_str = obj.get("timestamp", "")
            ts = _parse_iso_time(ts_str)

            if t == "user":
                # 保存上一轮
                if current_turn and current_turn.get("user") is not None:
                    turns.append(current_turn)
                current_turn = {"index": turn_index, "timestamp": ts_str}
                turn_index += 1
                msg = obj.get("message", {})
                content = msg.get("content", [])
                user_texts = []
                for c in content:
                    if c.get("type") == "text":
                        user_texts.append(c["text"].strip())
                # Join user texts with double newlines, or use empty string
                if user_texts:
                    current_turn["user"] = "\n\n".join(user_texts)
                else:
                    current_turn["user"] = ""
                current_turn["assistant"] = ""

            elif t == "assistant":
                if not current_turn:
                    continue
                msg = obj.get("message", {})
                content = msg.get("content", [])
                assistant_parts = []
                for c in content:
                    if c.get("type") == "text":
                        assistant_parts.append(c["text"])
                    elif c.get("type") == "tool_use":
                        name = c.get("name", "unknown")
                        inp = c.get("input", {})
                        assistant_parts.append(_render_tool_use(name, inp))
                    elif c.get("type") == "thinking":
                        thinking_text = c.get("thinking", "")
                        if thinking_text:
                            details = (
                                "<details>\n"
                                "<summary>Thinking</summary>\n\n"
                                f"{thinking_text}\n\n"
                                "</details>"
                            )
                            assistant_parts.append(details)
                if current_turn.get("assistant"):
                    current_turn["assistant"] += (
                        "\n\n" + "\n\n".join(assistant_parts)
                    )
                else:
                    current_turn["assistant"] = "\n\n".join(assistant_parts)

            elif t == "last-prompt":
                # 标记会话结束
                if not end_time and ts:
                    end_time = ts

            # 跟踪时间范围
            if ts:
                if start_time is None:
                    start_time = ts
                end_time = ts

    # 保存最后一轮
    has_content = current_turn.get("user") or current_turn.get("assistant")
    if current_turn and has_content:
        turns.append(current_turn)

    return {
        "session_id": session_id or jsonl_path.stem,
        "cwd": cwd,
        "git_branch": git_branch,
        "start_time": start_time,
        "end_time": end_time,
        "turns": turns,
    }


def _render_tool_use(name: str, inp: Dict) -> str:
    """将工具调用渲染为可读的 Markdown 文本。"""
    # 简化显示，隐藏过长的内容
    display = {}
    for k, v in inp.items():
        s = str(v)
        if len(s) > 200:
            s = s[:200] + "..."
        display[k] = s

    lines = [
        f"**🔧 {name}**",
        "",
        "```json",
        json.dumps(display, ensure_ascii=False, indent=2),
        "```",
    ]
    return "\n".join(lines)


def _parse_iso_time(ts: Optional[str]) -> Optional[datetime]:
    """解析 ISO 8601 格式时间字符串。"""
    if not ts:
        return None
    try:
        ts_clean = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_clean)
    except (ValueError, TypeError):
        return None


def _fmt_time(dt: Optional[datetime]) -> str:
    """格式化为北京时间 HH:MM:SS。"""
    if dt is None:
        return "??:??:??"
    return dt.astimezone(CST).strftime("%H:%M:%S")


def _fmt_date(dt: Optional[datetime]) -> str:
    """格式化为北京时间 YYYY-MM-DD。"""
    if dt is None:
        return "????-??-??"
    return dt.astimezone(CST).strftime("%Y-%m-%d")


def generate_filename(session: Dict) -> str:
    """根据会话开始时间生成文件名: talk_YYYY_MM_DD_HH_mm.md"""
    start = session.get("start_time")
    if start is None:
        start = datetime.now(CST)
    local = start.astimezone(CST)
    return f"talk_{local.strftime('%Y_%m_%d_%H_%M')}.md"


# ---------------------------------------------------------------------------
# Markdown 构建
# ---------------------------------------------------------------------------

def build_markdown(session: Dict, project_dir: Path) -> str:
    """将会话数据组装为 Markdown 文档。"""
    lines: List[str] = []
    lines.append("# Claude Code 对话记录")
    lines.append("")
    lines.append(f"**日期**: {_fmt_date(session.get('start_time'))}")
    lines.append(
        f"**时间**: {_fmt_time(session.get('start_time'))} "
        f"— {_fmt_time(session.get('end_time'))}"
    )
    lines.append(f"**工作目录**: `{project_dir}`")
    lines.append(f"**会话 ID**: `{session.get('session_id', 'unknown')}`")
    if session.get("git_branch"):
        lines.append(f"**Git 分支**: `{session['git_branch']}`")
    lines.append("")
    lines.append("---")
    lines.append("")

    turns = session.get("turns", [])
    if not turns:
        lines.append("*此会话暂无对话记录。*")
        lines.append("")
        return "\n".join(lines)

    for turn in turns:
        idx = turn.get("index", 0)
        user_msg = turn.get("user", "").strip()
        assistant_msg = turn.get("assistant", "").strip()
        ts = _parse_iso_time(turn.get("timestamp"))

        lines.append(f"## 第 {idx + 1} 轮对话")
        lines.append("")

        if user_msg:
            lines.append(f"### 用户 ({_fmt_time(ts)})")
            lines.append("")
            lines.append(user_msg)
            lines.append("")

        if assistant_msg:
            lines.append("### Claude Code")
            lines.append("")
            lines.append(assistant_msg)
            lines.append("")

        lines.append("---")
        lines.append("")

    # 去掉末尾多余的 ---
    while lines and lines[-1].strip() in ("---", ""):
        lines.pop()

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 导出跟踪
# ---------------------------------------------------------------------------

def load_exported_sessions(output_dir: Path) -> Dict[str, str]:
    """读取导出跟踪文件。"""
    tracker = output_dir / EXPORT_TRACKER
    if not tracker.exists():
        return {}
    try:
        with open(tracker, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_exported_sessions(output_dir: Path, data: Dict[str, str]) -> None:
    """写入导出跟踪文件。"""
    tracker = output_dir / EXPORT_TRACKER
    with open(tracker, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# 主导出逻辑
# ---------------------------------------------------------------------------

def export_chat(
    project_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    export_all: bool = False,
    latest_only: bool = False,
    session_id: Optional[str] = None,
) -> List[Path]:
    """
    主导出函数。

    参数:
        project_dir: 项目根目录，默认当前工作目录
        output_dir:  输出目录，默认项目根目录
        export_all:  导出所有会话（包括已导出的）
        latest_only: 仅导出最新一次会话
        session_id:  指定要导出的会话 ID
    """
    if project_dir is None:
        project_dir = Path.cwd()
    else:
        project_dir = project_dir.resolve()

    if output_dir is None:
        output_dir = project_dir
    else:
        output_dir = output_dir.resolve()

    output_dir.mkdir(parents=True, exist_ok=True)

    # 定位 sessions 目录
    sessions_dir = find_claude_sessions_dir()
    if sessions_dir is None:
        print(
            "Error: Cannot find Claude Code sessions directory "
            "(~/.claude/projects/)"
        )
        print(
            "  Please make sure Claude Code extension "
            "is installed and has been used."
        )
        sys.exit(1)

    print(f"Sessions dir: {sessions_dir}")
    print(f"Project dir:  {project_dir}")

    # 查找项目会话
    jsonl_files = find_project_sessions(sessions_dir, project_dir)
    if not jsonl_files:
        print("Warning: No Claude Code chat sessions found for this project.")
        print(f"  Project path: {project_dir}")
        return []

    print(f"Found {len(jsonl_files)} session(s)")

    # 加载跟踪
    exported = load_exported_sessions(output_dir)

    # 过滤会话
    if session_id:
        jsonl_files = [f for f in jsonl_files if f.stem == session_id]
        if not jsonl_files:
            print(f"Error: Session {session_id} not found.")
            sys.exit(1)
    elif latest_only:
        jsonl_files = [jsonl_files[-1]]

    exported_files: List[Path] = []

    for jf in jsonl_files:
        sid = jf.stem

        # 检查是否已导出
        if not export_all and sid in exported:
            print(f"Skip (already exported): {exported[sid]}")
            continue

        # 解析会话
        session = parse_session_jsonl(jf)
        turns = session.get("turns", [])
        if not turns:
            print(f"Skip (empty): {sid[:8]}...")
            continue

        # 构建 Markdown
        md_content = build_markdown(session, project_dir)

        # 生成文件名
        filename = generate_filename(session)
        output_path = output_dir / filename

        # 文件名冲突处理
        counter = 1
        stem = filename[:-3]
        while output_path.exists():
            output_path = output_dir / f"{stem}_{counter}.md"
            counter += 1

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        exported[sid] = output_path.name
        exported_files.append(output_path)

        print(
            f"Exported: {output_path.name}  "
            f"({_fmt_date(session.get('start_time'))} "
            f"{_fmt_time(session.get('start_time'))}, "
            f"{len(turns)} turns)"
        )

    # 保存跟踪
    save_exported_sessions(output_dir, exported)

    if not exported_files:
        print("No new sessions to export.")
    else:
        print(
            f"\nDone! {len(exported_files)} file(s) "
            f"exported to: {output_dir}"
        )

    return exported_files


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Claude Code chat sessions to Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/export_chat.py                    # Export current session
  python scripts/export_chat.py --all              # Export all sessions
  python scripts/export_chat.py --latest           # Export latest session only
  python scripts/export_chat.py --dir ./chats      # Output to a directory
  python scripts/export_chat.py --session <id>     # Export specific session
        """,
    )
    parser.add_argument(
        "--project", "-p",
        type=Path,
        default=None,
        help="Project root directory (default: current working directory)",
    )
    parser.add_argument(
        "--dir", "-d",
        type=Path,
        default=None,
        help="Output directory (default: project root)",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Export all sessions, including previously exported ones",
    )
    parser.add_argument(
        "--latest", "-l",
        action="store_true",
        help="Export only the latest session",
    )
    parser.add_argument(
        "--session", "-s",
        type=str,
        default=None,
        help="Export a specific session by ID",
    )

    args = parser.parse_args()

    session_id = args.session or get_session_id_from_env()

    # 无会话 ID 且未指定筛选条件时，默认导出最新会话
    if not args.all and not args.latest and not session_id:
        args.latest = True

    export_chat(
        project_dir=args.project,
        output_dir=args.dir,
        export_all=args.all,
        latest_only=bool(args.latest and not args.session),
        session_id=session_id if not args.all and not args.latest else None,
    )


if __name__ == "__main__":
    main()
