"""Build, inspect, and install standards-backed agent skills.

The normative Markdown standard remains the source of truth. This tool creates
small, routed skill references and template assets, records hashes in the
maintenance manifest, and detects drift across installations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
DEFAULT_MANIFEST = HERE / "standards-manifest.json"
TOP_SECTION_RE = re.compile(r"^##\s+(\d+)\.\s+.+$", re.MULTILINE)
SUBSECTION_RE = re.compile(r"^###\s+(\d+\.\d+)\s+.+$", re.MULTILINE)
VERSION_RE = re.compile(r"版本：([^|\s]+)")
PLANTUML_BLOCK_RE = re.compile(r"```plantuml\s*\n(.*?)\n```", re.DOTALL)


class StandardsToSkillsError(RuntimeError):
    """Raised for manifest, build, or safe-install errors."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StandardsToSkillsError(f"无法读取维护清单 {path}: {exc}") from exc


def _write_manifest(data: dict[str, Any], path: Path = DEFAULT_MANIFEST) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _standard_config(
    manifest: dict[str, Any], standard_id: str
) -> dict[str, Any]:
    try:
        return manifest["standards"][standard_id]
    except KeyError as exc:
        known = ", ".join(sorted(manifest.get("standards", {}))) or "无"
        raise StandardsToSkillsError(
            f"维护清单中不存在 {standard_id}；当前条目: {known}"
        ) from exc


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_sha256(root: Path) -> str:
    if not root.is_dir():
        return ""
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _split_sections(markdown: str, pattern: re.Pattern[str]) -> dict[str, str]:
    matches = list(pattern.finditer(markdown))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        sections[match.group(1)] = markdown[match.start() : end].rstrip() + "\n"
    return sections


def _managed_marker(standard_id: str, source_sha256: str) -> str:
    return json.dumps(
        {
            "managed_by": "standards-to-skills",
            "standard_id": standard_id,
            "source_sha256": source_sha256,
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def build_standard_skill(
    standard_id: str = "STD-004", manifest_path: Path | str = DEFAULT_MANIFEST
) -> dict[str, Any]:
    """Regenerate managed references/assets and refresh manifest hashes."""
    manifest_path = Path(manifest_path)
    manifest = _load_manifest(manifest_path)
    config = _standard_config(manifest, standard_id)
    source = Path(manifest["source_root"]) / config["source_file"]
    skill_dir = Path(manifest["canonical_skills_root"]) / config["skill_name"]
    if not source.is_file():
        raise StandardsToSkillsError(f"规范源文件不存在: {source}")
    if not (skill_dir / "SKILL.md").is_file():
        raise StandardsToSkillsError(f"Skill 骨架不存在: {skill_dir / 'SKILL.md'}")

    markdown = source.read_text(encoding="utf-8")
    source_hash = _sha256_file(source)
    top_sections = _split_sections(markdown, TOP_SECTION_RE)
    references_dir = skill_dir / "references"
    assets_dir = skill_dir / "assets" / "plantuml"
    references_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    generated_references: list[str] = []
    for group in config["section_groups"]:
        missing = [number for number in group["sections"] if number not in top_sections]
        if missing:
            raise StandardsToSkillsError(
                f"{standard_id} 缺少清单声明的章节: {', '.join(missing)}"
            )
        body = "\n".join(top_sections[number].rstrip() for number in group["sections"])
        output = references_dir / group["file"]
        output.write_text(
            f"# {group['title']}\n\n"
            f"> 由 standards-to-skills 从 `{config['source_file']}` 自动生成。"
            "禁止直接编辑；应修改源规范后重新构建。\n"
            f"> 来源 SHA-256: `{source_hash}`\n\n{body}\n",
            encoding="utf-8",
        )
        generated_references.append(output.relative_to(skill_dir).as_posix())

    section_20 = top_sections.get("20")
    if not section_20:
        raise StandardsToSkillsError(f"{standard_id} 缺少模板章节 20")
    subsections = _split_sections(section_20, SUBSECTION_RE)
    generated_assets: list[str] = []
    for subsection, filename in config.get("template_assets", {}).items():
        subsection_text = subsections.get(subsection)
        if not subsection_text:
            raise StandardsToSkillsError(f"{standard_id} 缺少模板小节 {subsection}")
        block = PLANTUML_BLOCK_RE.search(subsection_text)
        if not block:
            raise StandardsToSkillsError(f"{standard_id} 的 {subsection} 不含 PlantUML 模板")
        output = assets_dir / filename
        output.write_text(block.group(1).rstrip() + "\n", encoding="utf-8")
        generated_assets.append(output.relative_to(skill_dir).as_posix())

    marker = skill_dir / ".standards-to-skills.json"
    marker.write_text(_managed_marker(standard_id, source_hash), encoding="utf-8")

    version_match = VERSION_RE.search(markdown[:500])
    config["source_version"] = version_match.group(1) if version_match else "unknown"
    config["source_sha256"] = source_hash
    config["built_at"] = _now()
    config["canonical_skill_sha256"] = _tree_sha256(skill_dir)
    manifest["updated_at"] = config["built_at"]
    _write_manifest(manifest, manifest_path)

    return {
        "standard_id": standard_id,
        "source": str(source),
        "source_version": config["source_version"],
        "source_sha256": source_hash,
        "skill": str(skill_dir),
        "skill_sha256": config["canonical_skill_sha256"],
        "generated_references": generated_references,
        "generated_assets": generated_assets,
    }


def get_standard_skill_status(
    standard_id: str = "STD-004", manifest_path: Path | str = DEFAULT_MANIFEST
) -> dict[str, Any]:
    """Return source, canonical-skill, and installation drift status."""
    manifest = _load_manifest(Path(manifest_path))
    config = _standard_config(manifest, standard_id)
    source = Path(manifest["source_root"]) / config["source_file"]
    skill_dir = Path(manifest["canonical_skills_root"]) / config["skill_name"]
    source_hash = _sha256_file(source) if source.is_file() else ""
    canonical_hash = _tree_sha256(skill_dir)
    expected_source_hash = config.get("source_sha256", "")
    expected_skill_hash = config.get("canonical_skill_sha256", "")

    installations: dict[str, Any] = {}
    for name, install in manifest["installations"].items():
        target = Path(install["skills_root"]) / config["skill_name"]
        target_hash = _tree_sha256(target)
        state = {
            "path": str(target),
            "exists": target.is_dir(),
            "sha256": target_hash,
            "in_sync": bool(canonical_hash and target_hash == canonical_hash),
        }
        if install.get("rule_file"):
            state["rule_file"] = install["rule_file"]
            state["rule_exists"] = Path(install["rule_file"]).is_file()
        if install.get("discovery"):
            state["discovery"] = install["discovery"]
        if install.get("activation"):
            state["activation"] = install["activation"]
        installations[name] = state

    manager_config = manifest.get("manager_skill", {})
    manager_name = manager_config.get("name", "standards-to-skills")
    manager_dir = Path(manifest["canonical_skills_root"]) / manager_name
    manager_hash = _tree_sha256(manager_dir)
    manager_installations: dict[str, Any] = {}
    for name, install in manifest["installations"].items():
        target = Path(install["skills_root"]) / manager_name
        target_hash = _tree_sha256(target)
        manager_state = {
            "path": str(target),
            "exists": target.is_dir(),
            "sha256": target_hash,
            "in_sync": bool(manager_hash and target_hash == manager_hash),
        }
        recorded_state = manager_config.get("installation_state", {}).get(name, {})
        for key in ("enabled", "activation_verified_at"):
            if key in recorded_state:
                manager_state[key] = recorded_state[key]
        manager_installations[name] = manager_state

    return {
        "standard_id": standard_id,
        "status": config.get("status", "unknown"),
        "manager_skill": {
            "name": manager_name,
            "path": str(manager_dir),
            "exists": manager_dir.is_dir(),
            "sha256": manager_hash,
            "drift": not manager_config.get("canonical_skill_sha256")
            or manager_hash != manager_config.get("canonical_skill_sha256"),
            "installations": manager_installations,
        },
        "source": {
            "path": str(source),
            "version": config.get("source_version", ""),
            "exists": source.is_file(),
            "sha256": source_hash,
            "drift": not expected_source_hash or source_hash != expected_source_hash,
        },
        "canonical_skill": {
            "path": str(skill_dir),
            "exists": skill_dir.is_dir(),
            "sha256": canonical_hash,
            "drift": not expected_skill_hash or canonical_hash != expected_skill_hash,
        },
        "installations": installations,
        "built_at": config.get("built_at", ""),
        "next_scope": config.get("maintenance", {}).get("next_scope", ""),
    }


def _validate_install_target(target_root: Path, target: Path, skill_name: str) -> None:
    if target != target_root / skill_name or target.name != skill_name:
        raise StandardsToSkillsError(f"拒绝非清单目标路径: {target}")


def _replace_managed_skill(source: Path, target: Path, standard_id: str) -> None:
    marker_name = ".standards-to-skills.json"
    if target.exists():
        marker = target / marker_name
        if not marker.is_file():
            raise StandardsToSkillsError(f"目标已存在且不受本工具管理，拒绝覆盖: {target}")
        try:
            marker_data = json.loads(marker.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise StandardsToSkillsError(f"目标管理标记损坏，拒绝覆盖: {marker}") from exc
        if marker_data.get("standard_id") != standard_id:
            raise StandardsToSkillsError(f"目标由其他规范管理，拒绝覆盖: {target}")

    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}-", dir=target.parent))
    staged_skill = staging / target.name
    backup = target.with_name(f".{target.name}.previous")
    try:
        shutil.copytree(source, staged_skill)
        if _tree_sha256(staged_skill) != _tree_sha256(source):
            raise StandardsToSkillsError(f"暂存副本哈希不一致: {target}")
        if backup.exists():
            shutil.rmtree(backup)
        if target.exists():
            target.rename(backup)
        staged_skill.rename(target)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if not target.exists() and backup.exists():
            backup.rename(target)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def sync_standard_skill(
    standard_id: str = "STD-004",
    targets: Iterable[str] = ("cursor", "claude"),
    apply: bool = False,
    manifest_path: Path | str = DEFAULT_MANIFEST,
) -> dict[str, Any]:
    """Preview or apply safe installs to manifest-declared targets."""
    manifest = _load_manifest(Path(manifest_path))
    config = _standard_config(manifest, standard_id)
    skill_dir = Path(manifest["canonical_skills_root"]) / config["skill_name"]
    if not skill_dir.is_dir():
        raise StandardsToSkillsError(f"Canonical Skill 不存在: {skill_dir}")

    results: dict[str, Any] = {}
    install_state = config.setdefault("installation_state", {})
    for name in targets:
        name = name.strip().lower()
        if not name:
            continue
        if name not in manifest["installations"]:
            raise StandardsToSkillsError(f"未知安装目标: {name}")
        target_root = Path(manifest["installations"][name]["skills_root"])
        target = target_root / config["skill_name"]
        _validate_install_target(target_root, target, config["skill_name"])
        before = _tree_sha256(target)
        if apply:
            _replace_managed_skill(skill_dir, target, standard_id)
        after = _tree_sha256(target)
        results[name] = {
            "path": str(target),
            "action": "installed" if apply else "preview",
            "before_sha256": before,
            "after_sha256": after,
            "in_sync": bool(after and after == _tree_sha256(skill_dir)),
        }
        if apply:
            previous_state = install_state.get(name, {})
            install_state[name] = {
                "path": str(target),
                "installed_at": _now(),
                "sha256": after,
                "in_sync": results[name]["in_sync"],
            }
            for key in ("enabled", "activation_verified_at"):
                if key in previous_state:
                    install_state[name][key] = previous_state[key]
    if apply:
        manifest["updated_at"] = _now()
        _write_manifest(manifest, Path(manifest_path))
    return {"standard_id": standard_id, "apply": apply, "targets": results}


def sync_manager_skill(
    targets: Iterable[str] = ("cursor", "claude"),
    apply: bool = False,
    manifest_path: Path | str = DEFAULT_MANIFEST,
) -> dict[str, Any]:
    """Preview or apply installs of the standards-to-skills manager Skill."""
    manifest_path = Path(manifest_path)
    manifest = _load_manifest(manifest_path)
    manager = manifest.get("manager_skill", {})
    skill_name = manager.get("name", "standards-to-skills")
    skill_dir = Path(manifest["canonical_skills_root"]) / skill_name
    if not (skill_dir / "SKILL.md").is_file():
        raise StandardsToSkillsError(f"Manager Skill 不存在: {skill_dir}")
    canonical_hash = _tree_sha256(skill_dir)
    results: dict[str, Any] = {}
    install_state = manager.setdefault("installation_state", {})
    for name in targets:
        name = name.strip().lower()
        if not name:
            continue
        if name not in manifest["installations"]:
            raise StandardsToSkillsError(f"未知安装目标: {name}")
        target_root = Path(manifest["installations"][name]["skills_root"])
        target = target_root / skill_name
        _validate_install_target(target_root, target, skill_name)
        before = _tree_sha256(target)
        if apply:
            _replace_managed_skill(skill_dir, target, "MANAGER")
        after = _tree_sha256(target)
        results[name] = {
            "path": str(target),
            "action": "installed" if apply else "preview",
            "before_sha256": before,
            "after_sha256": after,
            "in_sync": bool(after and after == canonical_hash),
        }
        if apply:
            previous_state = install_state.get(name, {})
            install_state[name] = {
                "path": str(target),
                "installed_at": _now(),
                "sha256": after,
                "in_sync": results[name]["in_sync"],
            }
            for key in ("enabled", "activation_verified_at"):
                if key in previous_state:
                    install_state[name][key] = previous_state[key]
    if apply:
        manager["canonical_skill_sha256"] = canonical_hash
        manifest["manager_skill"] = manager
        manifest["updated_at"] = _now()
        _write_manifest(manifest, manifest_path)
    return {"manager_skill": skill_name, "apply": apply, "targets": results}


def _parse_targets(values: list[str] | None) -> list[str]:
    if not values:
        return ["cursor", "claude"]
    return [part.strip() for value in values for part in value.split(",") if part.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("build", "status"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--standard", default="STD-004")
    sync = subparsers.add_parser("sync")
    sync.add_argument("--standard", default="STD-004")
    sync.add_argument("--target", action="append")
    sync.add_argument("--apply", action="store_true")
    sync_manager = subparsers.add_parser("sync-manager")
    sync_manager.add_argument("--target", action="append")
    sync_manager.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.command == "build":
            result = build_standard_skill(args.standard, args.manifest)
        elif args.command == "status":
            result = get_standard_skill_status(args.standard, args.manifest)
        elif args.command == "sync":
            result = sync_standard_skill(
                args.standard,
                _parse_targets(args.target),
                args.apply,
                args.manifest,
            )
        else:
            result = sync_manager_skill(
                _parse_targets(args.target),
                args.apply,
                args.manifest,
            )
    except StandardsToSkillsError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
