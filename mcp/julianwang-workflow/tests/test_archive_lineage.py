"""Archive mode semantics self-test (JulianWang-workflow)."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import archive as arch  # noqa: E402


def _write_inbox(inbox_dir: Path, name: str, body: str) -> Path:
    p = inbox_dir / name
    p.write_text(body, encoding="utf-8")
    return p


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="cit_arch_"))
    kb = tmp / "knowledge-base"
    repo = tmp
    inbox = tmp / "inbox"
    inbox.mkdir(parents=True)
    for d in ("debug-records", "work-records", "knowledge", "daily-notes"):
        (kb / d).mkdir(parents=True)

    arch.INBOX_DIR = inbox
    arch.LAST_MARKER = inbox / ".last-archive.json"
    arch.ACTIVE_LINEAGE = inbox / ".lineage-active.json"
    arch.LINEAGES_DIR = inbox / "lineages"

    parent_inbox = _write_inbox(
        inbox,
        "2026-09-01_parent.md",
        "## 背景（Context）\n\n父主题 A。\n\n## 问题（What）\n\n父任务。\n",
    )
    r1 = arch.archive_inbox(
        inbox_path=str(parent_inbox),
        mode="new",
        title="父主题A",
        category="experience",
        kb_root=str(kb),
        repo_root=str(repo),
        push=False,
    )
    assert "[OK] 新建归档完成" in r1, r1
    active = json.loads(arch.ACTIVE_LINEAGE.read_text(encoding="utf-8"))
    lineage_id = active["lineage_id"]
    parent_card = Path(active["card_path"])

    # Fork = new topic: bare auto must NOT append parent
    fork_inbox = _write_inbox(
        inbox,
        "2026-09-01_fork-new-topic.md",
        "## 背景（Context）\n\nFork 后新主题 B。\n\n## 问题（What）\n\n应单开 md。\n",
    )
    r2 = arch.archive_inbox(
        inbox_path=str(fork_inbox),
        mode="auto",
        title="子主题B-fork新开",
        category="experience",
        kb_root=str(kb),
        repo_root=str(repo),
        push=False,
    )
    print("--- fork auto (expect NEW) ---")
    print(r2)
    assert "[OK] 新建归档完成" in r2, r2
    assert parent_card.read_text(encoding="utf-8").count("## 补充归档") == 0
    work_cards = list((kb / "work-records").glob("*.md"))
    assert len(work_cards) == 2, work_cards

    # Explicit continue still works
    cont = _write_inbox(
        inbox,
        "2026-09-01_continue-parent.md",
        "## 问题（What）\n\n显式续写父主题。\n",
    )
    r3 = arch.archive_inbox(
        inbox_path=str(cont),
        mode="auto",
        lineage_id=lineage_id,
        title="续写父主题A",
        kb_root=str(kb),
        repo_root=str(repo),
        push=False,
    )
    print("--- explicit lineage (expect SUPPLEMENT) ---")
    print(r3)
    assert "[OK] 补充归档完成" in r3, r3
    assert "显式续写父主题" in parent_card.read_text(encoding="utf-8")

    shutil.rmtree(tmp, ignore_errors=True)
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
