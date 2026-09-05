"""个人工作流归档 — 确定性落库（无 LLM）。

归属：JulianWang-workflow（个人 MCP / 工作流起点）
非 cit-workflow 业务仓库。

能力：
  - mode=new|supplement|auto
  - lineage：父会话建卡后写入 active lineage；fork 子会话 mode=auto 可追加到同一张卡
  - category：debug | experience | knowledge（广泛工作记录，不只 debug）
"""

from __future__ import annotations

import json
import re
import secrets
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DEFAULT_KB = Path(r"D:\Workspace\GDocuments\embedded-workflow-lab\knowledge-base")
DEFAULT_REPO = Path(r"D:\Workspace\GDocuments\embedded-workflow-lab")
INBOX_DIR = Path(r"D:\Workspace\.archive-inbox")
LAST_MARKER = INBOX_DIR / ".last-archive.json"
ACTIVE_LINEAGE = INBOX_DIR / ".lineage-active.json"
LINEAGES_DIR = INBOX_DIR / "lineages"

LINEAGE_TTL_DAYS = 14
_THEME_MAX_CHARS = 60
_WIN_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

CATEGORY_SPEC: dict[str, dict[str, str]] = {
    "debug": {
        "dir": "debug-records",
        "prefix": "EXP-DEBUG",
        "id_re": r"^EXP-DEBUG-(\d+)",
    },
    "experience": {
        "dir": "work-records",
        "prefix": "EXP-WORK",
        "id_re": r"^EXP-WORK-(\d+)",
    },
    "knowledge": {
        "dir": "knowledge",
        "prefix": "KB-NOTE",
        "id_re": r"^KB-NOTE-(\d+)",
    },
}


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _normalize_category(category: str) -> str:
    c = (category or "debug").strip().lower()
    aliases = {
        "debug": "debug",
        "dbg": "debug",
        "复盘": "debug",
        "experience": "experience",
        "exp": "experience",
        "经验": "experience",
        "work": "experience",
        "knowledge": "knowledge",
        "kb": "knowledge",
        "知识点": "knowledge",
        "知识": "knowledge",
    }
    if c not in aliases:
        raise ValueError(f"category 仅支持 debug|experience|knowledge，收到: {category}")
    return aliases[c]


def _next_id(records_dir: Path, category: str) -> tuple[str, int]:
    spec = CATEGORY_SPEC[category]
    id_re = re.compile(spec["id_re"], re.I)
    max_n = 0
    if records_dir.is_dir():
        for p in records_dir.glob("*.md"):
            m = id_re.match(p.name)
            if m:
                max_n = max(max_n, int(m.group(1)))
    return spec["prefix"], max_n + 1


def _sanitize_theme(theme: str, max_chars: int = _THEME_MAX_CHARS) -> str:
    theme = _WIN_FORBIDDEN.sub("", theme).strip().strip(".")
    theme = re.sub(r"\s+", "-", theme)
    theme = re.sub(r"-{2,}", "-", theme)
    if not theme:
        return "工作记录"
    if len(theme) <= max_chars:
        return theme
    cut = theme[:max_chars]
    for sep in ("-", "_", "与", "及", "：", ":"):
        idx = cut.rfind(sep)
        if idx >= max_chars // 2:
            cut = cut[:idx]
            break
    return cut.rstrip("-_.") or theme[:max_chars]


def _theme_from_inbox(inbox_path: Path, body: str, title: str = "") -> str:
    if title and title.strip():
        return _sanitize_theme(title.strip())
    stem = inbox_path.stem
    theme = re.sub(r"^\d{4}-\d{2}-\d{2}_", "", stem).strip() or "工作记录"
    if theme and theme != "工作记录":
        return _sanitize_theme(theme)
    for line in body.splitlines():
        if line.startswith("# "):
            return _sanitize_theme(line[2:].strip() or theme)
    return _sanitize_theme(theme)


def _strip_frontmatter(text: str) -> tuple[dict[str, str], str]:
    text = text.lstrip("\ufeff")
    if not text.startswith("---"):
        return {}, text.strip()
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text.strip()
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, parts[2].strip()


def _normalize_heading_spacing(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    in_fence = False
    heading_re = re.compile(r"^#{1,6}\s")
    for i, line in enumerate(lines):
        out.append(line)
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if heading_re.match(line) and i + 1 < len(lines):
            nxt = lines[i + 1]
            if nxt.strip() and not heading_re.match(nxt):
                out.append("")
    return "\n".join(out)


def _ensure_daily_notes(daily_path: Path, card_rel: str, mode: str, tip: str = "") -> None:
    today = _today()
    if not daily_path.exists():
        daily_path.parent.mkdir(parents=True, exist_ok=True)
        content = (
            f"---\n日期: {today}\n星期: \n标签:\n  - 日记\n  - 工作\n"
            f"项目: 个人工作流\n状态:\n---\n\n"
            f"## 知识库沉淀\n\n"
            f"- 新入库：{card_rel}（本日工作记录归档）\n"
        )
        daily_path.write_text(content, encoding="utf-8")
        return

    text = daily_path.read_text(encoding="utf-8")
    marker = "补充归档" if mode == "supplement" else "新入库"
    line = f"- {marker}：{card_rel}（本日工作记录归档）"
    if tip:
        line += f" — {tip}"
    if "## 知识库沉淀" in text or "## 📥 知识库沉淀" in text:
        for heading in ("## 📥 知识库沉淀\n", "## 知识库沉淀\n"):
            if heading in text:
                text = text.replace(heading, f"{heading}\n{line}\n", 1)
                break
    else:
        text = text.rstrip() + f"\n\n## 知识库沉淀\n\n{line}\n"
    daily_path.write_text(text, encoding="utf-8")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _new_lineage_id() -> str:
    return f"L{_today().replace('-', '')}-{secrets.token_hex(3)}"


def _lineage_expired(meta: dict[str, Any]) -> bool:
    exp = meta.get("expires_at") or ""
    if not exp:
        return False
    try:
        return datetime.fromisoformat(exp) < datetime.now()
    except ValueError:
        return False


def _write_lineage(
    *,
    lineage_id: str,
    card_path: Path,
    theme: str,
    category: str,
    mode: str,
) -> dict[str, Any]:
    expires = (datetime.now() + timedelta(days=LINEAGE_TTL_DAYS)).isoformat(timespec="seconds")
    meta = {
        "lineage_id": lineage_id,
        "card_path": str(card_path),
        "theme": theme,
        "category": category,
        "mode": mode,
        "date": _today(),
        "updated_at": _now_stamp(),
        "created_at": _now_iso(),
        "expires_at": expires,
        "note": "续写本卡请显式 mode=supplement 或 auto+lineage_id/target_card；fork 新主题请 mode=new/auto（默认新开 md）",
    }
    prev = _read_json(LINEAGES_DIR / f"{lineage_id}.json")
    if prev.get("created_at"):
        meta["created_at"] = prev["created_at"]
    _write_json(LINEAGES_DIR / f"{lineage_id}.json", meta)
    _write_json(ACTIVE_LINEAGE, meta)
    _write_json(
        LAST_MARKER,
        {
            "card_path": str(card_path),
            "theme": theme,
            "mode": mode,
            "date": _today(),
            "updated_at": _now_stamp(),
            "lineage_id": lineage_id,
            "category": category,
        },
    )
    return meta


def _resolve_lineage(lineage_id: str = "") -> dict[str, Any] | None:
    if lineage_id:
        meta = _read_json(LINEAGES_DIR / f"{lineage_id}.json")
        if meta and not _lineage_expired(meta):
            return meta
        if LINEAGES_DIR.is_dir():
            for m in LINEAGES_DIR.glob(f"*{lineage_id}*.json"):
                meta = _read_json(m)
                if meta and not _lineage_expired(meta):
                    return meta
        return None

    active = _read_json(ACTIVE_LINEAGE)
    if active and not _lineage_expired(active) and active.get("card_path"):
        if Path(active["card_path"]).is_file():
            return active
    return None


def archive_status() -> str:
    active = _read_json(ACTIVE_LINEAGE)
    last = _read_json(LAST_MARKER)
    lines = ["[JulianWang-workflow] archive status"]
    if active:
        expired = _lineage_expired(active)
        lines.append(
            f"active_lineage: {active.get('lineage_id')} ({'EXPIRED' if expired else 'OK'})"
        )
        lines.append(f"  card: {active.get('card_path')}")
        lines.append(f"  category: {active.get('category')}")
        lines.append(f"  expires_at: {active.get('expires_at')}")
    else:
        lines.append("active_lineage: (none)")
    if last:
        lines.append(f"last_archive: {last.get('card_path')}")
        lines.append(f"  lineage_id: {last.get('lineage_id', '')}")
    else:
        lines.append("last_archive: (none)")
    return "\n".join(lines)


def _resolve_supplement_target(
    records_dir: Path,
    target_card: str,
    theme: str,
    lineage_id: str = "",
) -> tuple[Path | None, str]:
    if target_card:
        p = Path(target_card)
        if not p.is_absolute():
            cand = records_dir / target_card
            if cand.is_file():
                return cand, "target_card"
            matches = list(records_dir.glob(f"*{target_card}*"))
            if matches:
                return matches[0], "target_card-glob"
            return None, "target_card-missing"
        return (p, "target_card-abs") if p.is_file() else (None, "target_card-missing")

    lin = _resolve_lineage(lineage_id)
    if lin and lin.get("card_path"):
        lp = Path(lin["card_path"])
        if lp.is_file():
            return lp, f"lineage:{lin.get('lineage_id')}"

    last = _read_json(LAST_MARKER)
    if last.get("card_path"):
        lp = Path(last["card_path"])
        if lp.is_file():
            return lp, "last-archive"

    if theme:
        for p in sorted(records_dir.glob(f"*_{_today()}_*.md"), reverse=True):
            if theme in p.name:
                return p, "theme-today"
    todays = sorted(records_dir.glob(f"*_{_today()}_*.md"), reverse=True)
    if todays:
        return todays[0], "today-latest"
    return None, "none"


def _git_commit_push(repo: Path, rel_files: list[str], message: str, push: bool) -> str:
    if not (repo / ".git").exists():
        return "[WARN] 非 git 仓库，已跳过 commit/push"

    for f in rel_files:
        r = _git(repo, "add", "--", f)
        if r.returncode != 0:
            return f"[ERR] git add 失败: {r.stderr.strip() or r.stdout.strip()}"

    st = _git(repo, "status", "--porcelain", "--", *rel_files)
    if not (st.stdout or "").strip():
        return "[WARN] 无文件变更，跳过 commit/push"

    r = _git(repo, "commit", "-m", message)
    if r.returncode != 0:
        return f"[ERR] git commit 失败: {r.stderr.strip() or r.stdout.strip()}"

    h = _git(repo, "rev-parse", "--short", "HEAD")
    short = (h.stdout or "").strip() or "?"
    lines = [f"commit: {short} — {message}"]

    if push:
        p = _git(repo, "push", "origin", "HEAD")
        if p.returncode != 0:
            lines.append(f"[WARN] push 失败: {p.stderr.strip() or p.stdout.strip()}")
        else:
            lines.append("push: origin OK")
    else:
        lines.append("push: skipped")

    return "\n".join(lines)


def _decide_mode(mode: str, target_card: str, lineage_id: str) -> str:
    """mode 语义（2026-09-01 修订）：

    - new / supplement：字面执行
    - auto：**默认新建卡**（fork 子会话通常是新主题/新任务，不应默默拼到父卡）
    - 仅当调用方**显式**传了 target_card 或 lineage_id 时，auto 才转为 supplement

    同对话续写请用 mode=supplement（或 auto + lineage_id/target_card），不要依赖「磁盘上有 active lineage」。
    """
    mode = (mode or "new").strip().lower()
    if mode not in ("new", "supplement", "auto"):
        raise ValueError(f"mode 仅支持 new|supplement|auto，收到: {mode}")
    if mode != "auto":
        return mode
    # 显式续档意图才追加；裸 auto / fork 默认新开 md
    if (target_card or "").strip():
        return "supplement"
    if (lineage_id or "").strip() and _resolve_lineage(lineage_id):
        return "supplement"
    return "new"


def archive_inbox(
    inbox_path: str,
    mode: str = "new",
    target_card: str = "",
    title: str = "",
    module: str = "其他",
    status: str = "已解决",
    related: str = "",
    category: str = "debug",
    lineage_id: str = "",
    kb_root: str = "",
    repo_root: str = "",
    push: bool = True,
) -> str:
    """执行归档。mode=new|supplement|auto。返回短文本结果。"""
    try:
        category_n = _normalize_category(category)
        mode_n = _decide_mode(mode, target_card, lineage_id)
    except ValueError as e:
        return f"[ERR] {e}"

    kb = Path(kb_root) if kb_root else DEFAULT_KB
    repo = Path(repo_root) if repo_root else DEFAULT_REPO
    spec = CATEGORY_SPEC[category_n]
    records_dir = kb / spec["dir"]
    daily_dir = kb / "daily-notes"
    records_dir.mkdir(parents=True, exist_ok=True)
    daily_dir.mkdir(parents=True, exist_ok=True)
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    LINEAGES_DIR.mkdir(parents=True, exist_ok=True)

    inbox = Path(inbox_path)
    if not inbox.is_file():
        return f"[ERR] inbox 不存在: {inbox}"

    raw = inbox.read_text(encoding="utf-8")
    meta_in, body = _strip_frontmatter(raw)
    if not body.strip():
        return "[ERR] inbox 内容为空"

    if meta_in.get("类别") or meta_in.get("category"):
        try:
            category_n = _normalize_category(
                meta_in.get("类别") or meta_in.get("category") or category_n
            )
            spec = CATEGORY_SPEC[category_n]
            records_dir = kb / spec["dir"]
            records_dir.mkdir(parents=True, exist_ok=True)
        except ValueError as e:
            return f"[ERR] {e}"

    theme = _theme_from_inbox(inbox, body, title=title)
    card_title = (title or theme).strip() or theme
    today = _today()

    if mode_n == "supplement":
        lin = _resolve_lineage(lineage_id)
        search_dir = records_dir
        if lin and lin.get("card_path"):
            search_dir = Path(lin["card_path"]).parent

        target, reason = _resolve_supplement_target(
            search_dir, target_card, theme, lineage_id=lineage_id
        )
        if not target:
            for cat, sp in CATEGORY_SPEC.items():
                d = kb / sp["dir"]
                target, reason = _resolve_supplement_target(
                    d, target_card, theme, lineage_id=lineage_id
                )
                if target:
                    category_n = cat
                    break
        if not target:
            return (
                "[ERR] 补充归档失败：找不到目标卡。\n"
                "请传 target_card / lineage_id，或先 mode=new；"
                "fork 场景请确认父会话已归档且 lineage 未过期。\n"
                f"{archive_status()}"
            )

        tip = "同对话补充"
        if reason.startswith("lineage"):
            tip = "lineage/fork 补充"
        elif reason == "last-archive":
            tip = "last-archive 补充"

        stamp = _now_stamp()
        block = (
            f"\n\n---\n\n## 补充归档（{stamp}）\n\n"
            f"**来源 inbox**：`{inbox.name}`\n\n"
            f"**解析**：{reason}\n\n"
            f"{_normalize_heading_spacing(body.strip())}\n"
        )
        with target.open("a", encoding="utf-8") as f:
            f.write(block)

        text = target.read_text(encoding="utf-8")
        if related and related not in text[:400]:
            text2 = text.replace("关联: ", f"关联: {related} / ", 1)
            if text2 != text:
                target.write_text(text2, encoding="utf-8")

        lid = (
            lineage_id
            or (lin or {}).get("lineage_id")
            or _read_json(LAST_MARKER).get("lineage_id")
            or _new_lineage_id()
        )
        lin_meta = _write_lineage(
            lineage_id=str(lid),
            card_path=target,
            theme=theme,
            category=category_n,
            mode="supplement",
        )

        try:
            card_rel = str(target.relative_to(kb)).replace("\\", "/")
        except ValueError:
            card_rel = target.name
        daily_path = daily_dir / f"{today}.md"
        _ensure_daily_notes(daily_path, card_rel, "supplement", tip=tip)

        files = [
            str(target.relative_to(repo)).replace("\\", "/"),
            str(daily_path.relative_to(repo)).replace("\\", "/"),
        ]
        commit_msg = f"docs: 补充工作记录归档（{card_rel}）"
        git_info = _git_commit_push(repo, files, commit_msg, push=push)
        return (
            f"[OK] 补充归档完成\n"
            f"模式: supplement (requested={mode})\n"
            f"类别: {category_n}\n"
            f"lineage_id: {lin_meta['lineage_id']}\n"
            f"解析: {reason}\n"
            f"复盘卡: {target}\n"
            f"daily-notes: {daily_path}\n"
            f"{git_info}"
        )

    prefix, num = _next_id(records_dir, category_n)
    fname = f"{prefix}-{num:03d}_{today}_{theme}.md"
    card_path = records_dir / fname

    fm_date = meta_in.get("日期") or today
    fm_project = meta_in.get("项目") or "个人工作流"
    fm_module = meta_in.get("CIT模块") or meta_in.get("模块") or module
    fm_status = meta_in.get("状态") or status
    fm_related = meta_in.get("关联") or related or ""

    if not any(line.startswith("# ") for line in body.splitlines()[:5]):
        body_out = f"# {card_title}\n\n{body.strip()}\n"
    else:
        body_out = body.strip() + "\n"
    body_out = _normalize_heading_spacing(body_out)

    card_text = (
        f"---\n"
        f"日期: {fm_date}\n"
        f"项目: {fm_project}\n"
        f"类别: {category_n}\n"
        f"模块: {fm_module}\n"
        f"关联: {fm_related}\n"
        f"状态: {fm_status}\n"
        f"---\n\n"
        f"{body_out}"
    )
    card_path.write_text(card_text, encoding="utf-8")

    lid = lineage_id.strip() or _new_lineage_id()
    lin_meta = _write_lineage(
        lineage_id=lid,
        card_path=card_path,
        theme=theme,
        category=category_n,
        mode="new",
    )

    card_rel = f"{spec['dir']}/{fname}"
    daily_path = daily_dir / f"{today}.md"
    _ensure_daily_notes(daily_path, card_rel, "new")

    files = [
        str(card_path.relative_to(repo)).replace("\\", "/"),
        str(daily_path.relative_to(repo)).replace("\\", "/"),
    ]
    commit_msg = f"docs: 新建工作记录归档（{card_rel}）"
    git_info = _git_commit_push(repo, files, commit_msg, push=push)
    return (
        f"[OK] 新建归档完成\n"
        f"模式: new (requested={mode})\n"
        f"类别: {category_n}\n"
        f"lineage_id: {lin_meta['lineage_id']}\n"
        f"复盘卡: {card_path}\n"
        f"daily-notes: {daily_path}\n"
        f"fork提示: 子会话若是新主题，用 mode=auto/new 单开 md；"
        f"仅当要续写本卡时传 lineage_id={lin_meta['lineage_id']} 或 mode=supplement\n"
        f"{git_info}"
    )
