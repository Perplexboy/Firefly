#!/usr/bin/env python3
"""
Export GitHub Copilot Chat sessions to Markdown.

输出文件命名: talk_YYYY_MM_DD_HH_mm.md
默认输出目录: 项目根目录（当前工作目录）
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CST = timezone(timedelta(hours=8))
EXPORT_TRACKER = ".copilot_chat_exports.json"


# ---------------------------------------------------------------------------
# 环境与路径
# ---------------------------------------------------------------------------

def is_wsl() -> bool:
    if sys.platform == "win32":
        return False
    try:
        with open("/proc/version", "r", encoding="utf-8") as f:
            return "microsoft" in f.read().lower()
    except (OSError, UnicodeDecodeError):
        return False


def get_home_dir() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("USERPROFILE", str(Path.home())))
    return Path.home()


def _wsl_to_win(path_str: str) -> Optional[str]:
    p = path_str.replace("\\", "/")
    if not p.startswith("/mnt/"):
        return None
    parts = p.split("/", 4)
    # /mnt/c/Users/...
    if len(parts) < 4 or len(parts[2]) != 1:
        return None
    drive = parts[2].upper()
    rest = parts[3] if len(parts) == 4 else parts[3] + "/" + parts[4]
    return f"{drive}:/{rest}".lower()


def normalize_path_for_compare(p: str) -> str:
    s = p.strip().replace("\\", "/")
    if s.startswith("file:///"):
        s = s[8:]
    s = s.replace("%20", " ")
    s = s.lower()
    if s.startswith("/mnt/"):
        w = _wsl_to_win(s)
        if w:
            return w
    return s


def get_possible_vscode_user_dirs() -> List[Path]:
    candidates: List[Path] = []

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidates.append(Path(appdata) / "Code" / "User")
    else:
        # WSL / Linux Remote
        candidates.append(get_home_dir() / ".vscode-server" / "data" / "User")
        candidates.append(get_home_dir() / ".config" / "Code" / "User")

        # WSL 下尝试读取 Windows 侧 Code 用户目录
        if is_wsl():
            win_user = (
                os.environ.get("USERNAME")
                or os.environ.get("USER")
                or ""
            )
            if win_user:
                candidates.append(
                    Path(f"/mnt/c/Users/{win_user}/AppData/Roaming/Code/User")
                )

    # 去重 + 保留存在目录
    unique: List[Path] = []
    seen = set()
    for c in candidates:
        key = str(c)
        if key not in seen and c.exists():
            seen.add(key)
            unique.append(c)
    return unique


def get_session_id_from_env() -> Optional[str]:
    keys = [
        "COPILOT_CHAT_SESSION_ID",
        "GITHUB_COPILOT_CHAT_SESSION_ID",
        "CHAT_SESSION_ID",
        "CLAUDE_CODE_SESSION_ID",  # 兼容环境
    ]
    for k in keys:
        v = os.environ.get(k)
        if v:
            return v.strip()
    return None


# ---------------------------------------------------------------------------
# 日志发现
# ---------------------------------------------------------------------------

def discover_copilot_jsonl_files() -> List[Path]:
    files: List[Path] = []

    # 1) 优先尝试当前会话日志目录
    target_log_dir = os.environ.get("VSCODE_TARGET_SESSION_LOG", "").strip()
    if target_log_dir:
        base = Path(target_log_dir)
        if base.exists():
            files.extend(base.glob("**/*.jsonl"))

    # 2) 扫描 VS Code User/workspaceStorage
    for user_dir in get_possible_vscode_user_dirs():
        ws = user_dir / "workspaceStorage"
        if not ws.exists():
            continue

        patterns = [
            "**/GitHub.copilot-chat/debug-logs/**/*.jsonl",
            "**/GitHub.copilot-chat/debug-logs/*.jsonl",
            "**/github.copilot-chat/transcripts/**/*.jsonl",
            "**/github.copilot-chat/transcripts/*.jsonl",
            "**/*copilot*chat*/**/*.jsonl",
        ]
        for pat in patterns:
            files.extend(ws.glob(pat))

    # 去重 + 仅文件
    uniq: Dict[str, Path] = {}
    for f in files:
        if f.is_file():
            uniq[str(f.resolve())] = f.resolve()

    # 按修改时间升序，后面选 latest 时取最后一个
    out = sorted(uniq.values(), key=lambda p: p.stat().st_mtime)
    return out


def _jsonl_maybe_matches_project(jsonl_path: Path, project_dir: Path) -> bool:
    project_norm = normalize_path_for_compare(str(project_dir.resolve()))

    # 读取前若干行找 cwd/workspace/folder/path 等字段
    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if idx > 80:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                candidates = extract_possible_paths(obj)
                for c in candidates:
                    c_norm = normalize_path_for_compare(c)
                    if (
                        c_norm == project_norm
                        or c_norm.startswith(project_norm + "/")
                        or project_norm.startswith(c_norm + "/")
                    ):
                        return True
        # 没有可判断字段时，保守返回 True（避免漏会话）
        return True
    except (OSError, UnicodeDecodeError):
        return False


def extract_possible_paths(obj: Any) -> List[str]:
    found: List[str] = []
    keys = {
        "cwd", "workspace", "workspacePath", "folder",
        "rootPath", "projectPath", "path",
    }

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if k in keys and isinstance(v, str):
                    found.append(v)
                walk(v)
        elif isinstance(x, list):
            for i in x:
                walk(i)

    walk(obj)
    return found


# ---------------------------------------------------------------------------
# 解析 JSONL
# ---------------------------------------------------------------------------

def _parse_iso_time(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _fmt_date(dt: Optional[datetime]) -> str:
    if not dt:
        return "????-??-??"
    return dt.astimezone(CST).strftime("%Y-%m-%d")


def _fmt_time(dt: Optional[datetime]) -> str:
    if not dt:
        return "??:??:??"
    return dt.astimezone(CST).strftime("%H:%M:%S")


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        parts = []
        for item in value:
            t = _to_text(item)
            if t:
                parts.append(t)
        return "\n\n".join(parts).strip()
    if isinstance(value, dict):
        # 常见字段优先
        for k in ("text", "content", "message", "body", "prompt", "response"):
            if k in value:
                t = _to_text(value.get(k))
                if t:
                    return t
        # 兼容 OpenAI/工具结构
        if "type" in value and value.get("type") == "text" and "text" in value:
            return _to_text(value.get("text"))
        # 最后兜底输出 JSON
        try:
            return json.dumps(value, ensure_ascii=False, indent=2)
        except TypeError:
            return str(value)
    return str(value)


def _extract_role_and_text(obj: Dict[str, Any]) -> Tuple[Optional[str], str]:
    # role/type/event/kind 等多字段兼容
    role = obj.get("role")
    t = str(obj.get("type", "")).lower()
    e = str(obj.get("event", "")).lower()
    k = str(obj.get("kind", "")).lower()

    merged_tag = " ".join([str(role or "").lower(), t, e, k])

    text = ""
    for key in ("message", "content", "text", "body", "prompt", "response"):
        if key in obj:
            text = _to_text(obj[key])
            if text:
                break

    if "user" in merged_tag:
        return "user", text
    if (
        "assistant" in merged_tag
        or "copilot" in merged_tag
        or "model" in merged_tag
    ):
        return "assistant", text

    # 没明确角色时，尝试依据字段猜
    if role in ("user", "assistant"):
        return role, text

    return None, text


def _extract_tool_markdown(obj: Dict[str, Any]) -> Optional[str]:
    raw = json.dumps(obj, ensure_ascii=False)
    low = raw.lower()
    tool_kw = (
        "tool", "function_call", "tool_use",
        "toolrequest", "command",
    )
    if not any(x in low for x in tool_kw):
        return None

    name = ""
    for key in ("name", "toolName", "tool", "function"):
        v = obj.get(key)
        if isinstance(v, str) and v:
            name = v
            break

    payload = obj.get("input")
    if payload is None:
        payload = obj.get("arguments")
    if payload is None:
        payload = obj.get("params")
    if payload is None:
        payload = obj

    try:
        payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
    except TypeError:
        payload_str = str(payload)

    title = f"工具调用: {name}" if name else "工具调用"
    return "\n".join(
        [
            f"> {title}",
            ">",
            "> ```json",
            payload_str,
            "> ```",
        ]
    )


def parse_session_jsonl(jsonl_path: Path) -> Dict[str, Any]:
    session_id = jsonl_path.stem
    cwd = ""
    git_branch = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    turns: List[Dict[str, Any]] = []
    current_turn: Dict[str, Any] = {}
    turn_index = 0
    end_detected = False

    def flush_turn() -> None:
        nonlocal current_turn
        has_content = (
            current_turn.get("user")
            or current_turn.get("assistant")
        )
        if current_turn and has_content:
            turns.append(current_turn)
        current_turn = {}

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if isinstance(obj.get("sessionId"), str) and obj["sessionId"]:
                session_id = obj["sessionId"]
            if not cwd and isinstance(obj.get("cwd"), str):
                cwd = obj.get("cwd", "")
            if not git_branch and isinstance(obj.get("gitBranch"), str):
                git_branch = obj.get("gitBranch", "")

            ts_raw = (
                obj.get("timestamp")
                or obj.get("time")
                or obj.get("createdAt")
                or obj.get("ts")
                or ""
            )
            ts = _parse_iso_time(str(ts_raw)) if ts_raw else None

            if ts:
                if start_time is None:
                    start_time = ts
                end_time = ts

            raw_low = json.dumps(obj, ensure_ascii=False).lower()
            end_markers = (
                "last-prompt" in raw_low
                or "session.end" in raw_low
                or "chat.finished" in raw_low
            )
            if end_markers:
                end_detected = True

            role, text = _extract_role_and_text(obj)
            tool_md = _extract_tool_markdown(obj)

            if role == "user":
                flush_turn()
                current_turn = {
                    "index": turn_index,
                    "timestamp": ts_raw if ts_raw else "",
                    "user": text.strip(),
                    "assistant": "",
                }
                turn_index += 1
                if tool_md:
                    current_turn["assistant"] = tool_md
                continue

            if role == "assistant":
                if not current_turn:
                    current_turn = {
                        "index": turn_index,
                        "timestamp": ts_raw if ts_raw else "",
                        "user": "",
                        "assistant": "",
                    }
                    turn_index += 1
                if text.strip():
                    if current_turn["assistant"]:
                        current_turn["assistant"] += "\n\n" + text.strip()
                    else:
                        current_turn["assistant"] = text.strip()
                if tool_md:
                    if current_turn["assistant"]:
                        current_turn["assistant"] += "\n\n" + tool_md
                    else:
                        current_turn["assistant"] = tool_md
                continue

            # role 不明但有工具/文本时，附加到 assistant
            if tool_md or text.strip():
                if not current_turn:
                    current_turn = {
                        "index": turn_index,
                        "timestamp": ts_raw if ts_raw else "",
                        "user": "",
                        "assistant": "",
                    }
                    turn_index += 1
                chunk = tool_md if tool_md else text.strip()
                if chunk:
                    if current_turn["assistant"]:
                        current_turn["assistant"] += "\n\n" + chunk
                    else:
                        current_turn["assistant"] = chunk

    flush_turn()

    return {
        "session_id": session_id,
        "cwd": cwd,
        "git_branch": git_branch,
        "start_time": start_time,
        "end_time": end_time,
        "turns": turns,
        "ended": end_detected,
        "source": str(jsonl_path),
    }


# ---------------------------------------------------------------------------
# Markdown 与文件命名
# ---------------------------------------------------------------------------

def generate_filename(session: Dict[str, Any]) -> str:
    start = session.get("start_time")
    if start is None:
        start = datetime.now(CST)
    local = start.astimezone(CST)
    return f"talk_{local.strftime('%Y_%m_%d_%H_%M')}.md"


def build_markdown(session: Dict[str, Any], project_dir: Path) -> str:
    lines: List[str] = []
    lines.append("# Copilot Chat 对话记录")
    lines.append("")
    lines.append(f"**日期**: {_fmt_date(session.get('start_time'))}")
    lines.append(
        f"**时间**: {_fmt_time(session.get('start_time'))} "
        f"- {_fmt_time(session.get('end_time'))}"
    )
    lines.append(f"**工作目录**: {project_dir}")
    lines.append(f"**会话 ID**: {session.get('session_id', 'unknown')}")
    if session.get("git_branch"):
        lines.append(f"**Git 分支**: {session['git_branch']}")
    lines.append(f"**来源日志**: {session.get('source', '')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    turns = session.get("turns", [])
    if not turns:
        lines.append("*此会话暂无可解析对话记录。*")
        return "\n".join(lines)

    for turn in turns:
        idx = int(turn.get("index", 0)) + 1
        ts = _parse_iso_time(turn.get("timestamp", ""))
        user_msg = str(turn.get("user", "")).strip()
        assistant_msg = str(turn.get("assistant", "")).strip()

        lines.append(f"## 第 {idx} 轮对话")
        lines.append("")

        if user_msg:
            lines.append(f"### 用户 ({_fmt_time(ts)})")
            lines.append("")
            lines.append(user_msg)
            lines.append("")

        if assistant_msg:
            lines.append("### Copilot")
            lines.append("")
            lines.append(assistant_msg)
            lines.append("")

        lines.append("---")
        lines.append("")

    while lines and lines[-1].strip() in ("", "---"):
        lines.pop()

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 导出跟踪
# ---------------------------------------------------------------------------

def load_exported_sessions(output_dir: Path) -> Dict[str, str]:
    tracker = output_dir / EXPORT_TRACKER
    if not tracker.exists():
        return {}
    try:
        with open(tracker, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def save_exported_sessions(output_dir: Path, data: Dict[str, str]) -> None:
    tracker = output_dir / EXPORT_TRACKER
    with open(tracker, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# 过滤与导出
# ---------------------------------------------------------------------------

def find_project_sessions(project_dir: Path) -> List[Path]:
    candidates = discover_copilot_jsonl_files()
    return [
        f for f in candidates
        if _jsonl_maybe_matches_project(f, project_dir)
    ]


def filter_sessions(
    files: List[Path],
    *,
    session_id: Optional[str],
    latest_only: bool
) -> List[Path]:
    if not files:
        return []

    if session_id:
        filtered = []
        sid_low = session_id.lower()
        for f in files:
            if sid_low in f.stem.lower() or sid_low in str(f).lower():
                filtered.append(f)
            else:
                # 试着解析 sessionId
                try:
                    s = parse_session_jsonl(f)
                    if str(s.get("session_id", "")).lower() == sid_low:
                        filtered.append(f)
                except OSError:
                    pass
        return filtered

    if latest_only:
        return [files[-1]]

    return files


def export_chat(
    project_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    export_all: bool = False,
    latest_only: bool = False,
    session_id: Optional[str] = None,
) -> List[Path]:
    if project_dir is None:
        project_dir = Path.cwd().resolve()
    else:
        project_dir = project_dir.resolve()

    if output_dir is None:
        output_dir = project_dir
    else:
        output_dir = output_dir.resolve()

    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_files = find_project_sessions(project_dir)
    if not jsonl_files:
        print(
            "Warning: No Copilot chat session jsonl "
            "files found for this project."
        )
        print(f"  Project path: {project_dir}")
        return []

    jsonl_files = filter_sessions(
        jsonl_files, session_id=session_id, latest_only=latest_only
    )
    if not jsonl_files:
        print("Warning: No matching sessions found after filter.")
        return []

    exported = load_exported_sessions(output_dir)
    exported_files: List[Path] = []

    for jf in jsonl_files:
        sid_key = jf.stem

        if not export_all and sid_key in exported:
            print(f"Skip (already exported): {exported[sid_key]}")
            continue

        try:
            session = parse_session_jsonl(jf)
        except OSError as e:
            print(f"Skip (read failed): {jf} -> {e}")
            continue

        turns = session.get("turns", [])
        if not turns:
            print(f"Skip (empty/no turns): {jf.name}")
            continue

        md = build_markdown(session, project_dir)
        filename = generate_filename(session)
        output_path = output_dir / filename

        # 冲突处理
        counter = 1
        stem = filename[:-3]
        while output_path.exists():
            output_path = output_dir / f"{stem}_{counter}.md"
            counter += 1

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)

        exported[sid_key] = output_path.name
        exported_files.append(output_path)
        print(
            f"Exported: {output_path.name} "
            f"({_fmt_date(session.get('start_time'))} "
            f"{_fmt_time(session.get('start_time'))}, "
            f"{len(turns)} turns)"
        )

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
# 监听模式
# ---------------------------------------------------------------------------

def watch_and_export(
    project_dir: Path,
    output_dir: Path,
    session_id: Optional[str],
    inactivity_seconds: int = 120,
    poll_seconds: int = 2,
) -> List[Path]:
    files = find_project_sessions(project_dir)
    if not files:
        print("Error: no candidate session files found.")
        return []

    # watch 时默认单会话
    target_list = filter_sessions(
        files,
        session_id=session_id,
        latest_only=(session_id is None),
    )
    if not target_list:
        print("Error: no target session file matched for watch.")
        return []

    target = target_list[-1]
    print(f"Watching: {target}")

    last_mtime = target.stat().st_mtime
    last_size = target.stat().st_size
    last_change_at = time.time()
    ended = False

    try:
        while True:
            try:
                st = target.stat()
                changed = (
                    st.st_mtime != last_mtime
                    or st.st_size != last_size
                )
                if changed:
                    last_mtime = st.st_mtime
                    last_size = st.st_size
                    last_change_at = time.time()

                    # 每次变化后尝试检测是否结束
                    session = parse_session_jsonl(target)
                    if session.get("ended"):
                        print("Detected session end marker. Exporting...")
                        ended = True
                        break
            except OSError:
                # 文件暂不可读时等待
                pass

            if time.time() - last_change_at >= inactivity_seconds:
                print(
                    f"No new log activity for "
                    f"{inactivity_seconds}s. Exporting..."
                )
                break

            time.sleep(poll_seconds)

    except KeyboardInterrupt:
        print("\nInterrupted by user. Exporting now...")

    # 导出单个目标文件
    sid = None
    if session_id:
        sid = session_id
    elif ended:
        # 可选保留 None，直接 latest_only 导出
        sid = None

    return export_chat(
        project_dir=project_dir,
        output_dir=output_dir,
        export_all=False,
        latest_only=(sid is None),
        session_id=sid,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export GitHub Copilot Chat sessions to Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/export_copilot_chat.py
  python scripts/export_copilot_chat.py --latest
  python scripts/export_copilot_chat.py --all
  python scripts/export_copilot_chat.py --session <id>
  python scripts/export_copilot_chat.py --watch
  python scripts/export_copilot_chat.py --dir ./chats
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
        help="Export latest session only",
    )
    parser.add_argument(
        "--session", "-s",
        type=str,
        default=None,
        help="Export a specific session by session id or id fragment",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help=(
            "Watch one session log and export "
            "when session ends or on inactivity/Ctrl+C"
        ),
    )
    parser.add_argument(
        "--inactivity",
        type=int,
        default=120,
        help="Watch mode inactivity timeout in seconds (default: 120)",
    )

    args = parser.parse_args()

    project_dir = (
        args.project.resolve() if args.project
        else Path.cwd().resolve()
    )
    output_dir = args.dir.resolve() if args.dir else project_dir

    # 默认行为：当前会话优先，取不到就 latest
    env_session = get_session_id_from_env()
    effective_session = args.session or env_session

    if args.watch:
        watch_and_export(
            project_dir=project_dir,
            output_dir=output_dir,
            session_id=effective_session,
            inactivity_seconds=max(10, args.inactivity),
        )
        return

    # 逻辑优先级：
    # --all > (--session/env_session) > --latest > default(latest)
    if args.all:
        export_chat(
            project_dir=project_dir,
            output_dir=output_dir,
            export_all=True,
            latest_only=False,
            session_id=None,
        )
        return

    if effective_session:
        export_chat(
            project_dir=project_dir,
            output_dir=output_dir,
            export_all=False,
            latest_only=False,
            session_id=effective_session,
        )
        return

    # 无 session id 时，--latest 或默认都走 latest
    export_chat(
        project_dir=project_dir,
        output_dir=output_dir,
        export_all=False,
        latest_only=True,
        session_id=None,
    )


if __name__ == "__main__":
    main()
