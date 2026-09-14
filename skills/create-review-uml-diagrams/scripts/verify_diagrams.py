"""Run the automatic layer of STD-004 diagram validation."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path


IMAGE_LINK_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
HTML_IMAGE_RE = re.compile(r"<img\b[^>]*\bsrc=['\"]([^'\"]+)['\"]", re.IGNORECASE)
SOURCE_EXTENSIONS = {".puml", ".drawio", ".mmd", ".d2"}
EXPECTED_LAYOUTS = (
    ("plantuml", ".puml"),
    ("drawio", ".drawio"),
)


@dataclass
class Finding:
    code: str
    path: str
    message: str


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _is_absolute_reference(value: str) -> bool:
    value = value.strip().strip("<>")
    return bool(
        re.match(r"^[A-Za-z]:[\\/]", value)
        or value.startswith("/")
        or value.startswith("\\\\")
    )


def _check_svg(path: Path, root: Path, findings: list[Finding]) -> None:
    rel = _relative(path, root)
    if path.stat().st_size <= 100:
        findings.append(Finding("SVG_TOO_SMALL", rel, "SVG 必须大于 100 B"))
        return
    try:
        xml_root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        findings.append(Finding("SVG_INVALID", rel, f"SVG 无法解析: {exc}"))
        return
    if xml_root.tag.rsplit("}", 1)[-1].lower() != "svg":
        findings.append(Finding("SVG_ROOT", rel, "根元素不是 <svg>"))


def _check_pairs(root: Path, findings: list[Finding]) -> int:
    checked = 0
    diagrams = root / "docs" / "diagrams"
    for tool, extension in EXPECTED_LAYOUTS:
        source_dir = diagrams / tool / "source"
        rendered_dir = diagrams / tool / "rendered"
        if not source_dir.is_dir():
            continue
        for source in sorted(source_dir.glob(f"*{extension}")):
            checked += 1
            svg = rendered_dir / f"{source.stem}.svg"
            if not svg.is_file():
                findings.append(
                    Finding(
                        "PAIR_MISSING",
                        _relative(source, root),
                        f"缺少同名 SVG: {_relative(svg, root)}",
                    )
                )
            else:
                _check_svg(svg, root, findings)
            if extension == ".puml":
                text = source.read_text(encoding="utf-8", errors="replace")
                if re.search(r"(?im)^\s*skinparam\b", text):
                    findings.append(
                        Finding("PLANTUML_SKINPARAM", _relative(source, root), "禁止使用 skinparam")
                    )
    return checked


def _iter_markdown(root: Path):
    skipped = {".git", ".venv", "node_modules", "vendor"}
    for path in root.rglob("*.md"):
        if not any(part in skipped for part in path.parts):
            yield path


def _check_markdown(root: Path, findings: list[Finding]) -> int:
    checked = 0
    for path in _iter_markdown(root):
        checked += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        refs = IMAGE_LINK_RE.findall(text) + HTML_IMAGE_RE.findall(text)
        for ref in refs:
            clean = ref.split("#", 1)[0].split("?", 1)[0]
            suffix = Path(clean).suffix.lower()
            if _is_absolute_reference(clean):
                findings.append(
                    Finding("MARKDOWN_ABSOLUTE", _relative(path, root), f"图片使用绝对路径: {ref}")
                )
            if suffix in SOURCE_EXTENSIONS:
                findings.append(
                    Finding("MARKDOWN_SOURCE", _relative(path, root), f"图片直接引用源文件: {ref}")
                )
    return checked


def verify(project_root: Path) -> dict:
    root = project_root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"项目目录不存在: {root}")
    findings: list[Finding] = []
    source_count = _check_pairs(root, findings)
    markdown_count = _check_markdown(root, findings)
    return {
        "project_root": str(root),
        "automatic": {
            "status": "PASS" if not findings else "FAIL",
            "sources_checked": source_count,
            "markdown_files_checked": markdown_count,
            "findings": [asdict(item) for item in findings],
        },
        "manual_required": {
            "visual": "PENDING — 必须打开 SVG 在 100% 缩放下检查",
            "semantic_and_factual": "PENDING — 必须对照需求、接口、代码或评审材料检查",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = verify(args.project_root)
    except (OSError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        automatic = result["automatic"]
        print(f"Automatic: {automatic['status']}")
        print(f"Sources checked: {automatic['sources_checked']}")
        print(f"Markdown checked: {automatic['markdown_files_checked']}")
        for finding in automatic["findings"]:
            print(f"[{finding['code']}] {finding['path']}: {finding['message']}")
        print(result["manual_required"]["visual"])
        print(result["manual_required"]["semantic_and_factual"])
    return 0 if result["automatic"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
