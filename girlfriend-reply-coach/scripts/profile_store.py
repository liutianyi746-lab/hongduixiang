#!/usr/bin/env python3
"""Manage evidence-backed relationship profiles in a caller-supplied private root."""

from __future__ import annotations

import json
import shutil
import uuid
import argparse
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CLASSIFICATIONS = {"已确认事实", "高置信度模式", "待验证推测"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_slug(slug: str) -> str:
    if not slug or slug in {".", ".."} or any(char in slug for char in "/\\"):
        raise ValueError("档案标识只能是单个目录名")
    return slug


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _inside(root: Path, target: Path) -> bool:
    root_resolved = root.resolve()
    target_resolved = target.resolve()
    return target_resolved != root_resolved and root_resolved in target_resolved.parents


def _git_worktree_root(path: Path) -> Path | None:
    candidate = path.resolve()
    for parent in (candidate, *candidate.parents):
        if (parent / ".git").exists():
            return parent
    return None


def default_private_root() -> Path:
    configured = os.environ.get("GIRLFRIEND_REPLY_COACH_DATA")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".codex" / "private" / "girlfriend-reply-coach").resolve()


def self_voice_status(root: str | Path) -> dict[str, Any]:
    path = Path(root).resolve() / "self-voice.json"
    if not path.is_file():
        return {"status": "missing", "path": str(path), "pattern_count": 0}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "corrupt", "path": str(path), "pattern_count": 0}
    if not isinstance(value, dict) or not isinstance(value.get("patterns"), list):
        return {"status": "corrupt", "path": str(path), "pattern_count": 0}
    patterns = [item for item in value["patterns"] if isinstance(item, dict) and item]
    return {
        "status": "valid" if patterns else "empty",
        "path": str(path),
        "pattern_count": len(patterns),
    }


def _ensure_private_root(root: Path) -> None:
    worktree = _git_worktree_root(root)
    if worktree is not None:
        raise ValueError(f"拒绝把私人人物档案写入 Git 工作区：{worktree}")


def create_profile(root: str | Path, slug: str, alias: str) -> Path:
    root_path = Path(root).resolve()
    _ensure_private_root(root_path)
    safe_slug = _safe_slug(slug)
    profile_dir = root_path / "people" / safe_slug
    profile_dir.mkdir(parents=True, exist_ok=True)
    created_at = _now()
    profile_path = profile_dir / "profile.json"
    if not profile_path.exists():
        _write_json(
            profile_path,
            {
                "schema_version": 1,
                "alias": alias,
                "authorization": {"confirmed": False},
                "sender_mapping": {"self": [], "partner": []},
                "text_message_counts": {"self": 0, "partner": 0},
                "created_at": created_at,
                "updated_at": created_at,
                "claims": [],
            },
        )
    generation_path = profile_dir / "generation.json"
    if not generation_path.exists():
        _write_json(
            generation_path,
            {
                "schema_version": 1,
                "slug": safe_slug,
                "skill_name": f"hong-{safe_slug}",
                "profile_version": None,
                "confirmed_summary_hash": None,
                "generated_at": None,
                "install_targets": [],
                "skill_paths": [],
                "needs_regeneration": True,
            },
        )
    voice_delta_path = profile_dir / "voice-delta.json"
    if not voice_delta_path.exists():
        _write_json(
            voice_delta_path,
            {
                "schema_version": 1,
                "person_id": safe_slug,
                "updated_at": created_at,
                "patterns": [],
                "corrections": [],
            },
        )
    self_voice = root_path / "self-voice.json"
    if not self_voice.exists():
        _write_json(
            self_voice,
            {"schema_version": 1, "updated_at": created_at, "patterns": [], "corrections": []},
        )
    manifest_path = root_path / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else {"schema_version": 1, "profiles": {}}
    )
    manifest["profiles"][safe_slug] = {
        "alias": alias,
        "path": f"people/{safe_slug}/profile.json",
        "voice_delta_path": f"people/{safe_slug}/voice-delta.json",
        "updated_at": created_at,
    }
    _write_json(manifest_path, manifest)
    return profile_dir


def read_profile(profile_dir: str | Path) -> dict[str, Any]:
    return json.loads((Path(profile_dir) / "profile.json").read_text(encoding="utf-8"))


def add_claim(
    profile_dir: str | Path,
    *,
    content: str,
    classification: str,
    evidence: list[str],
    confidence: float,
    contexts: list[str],
    conflicts_with: list[str] | None = None,
) -> str:
    profile_dir_path = Path(profile_dir).resolve()
    _ensure_private_root(profile_dir_path)
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"无效分类：{classification}")
    if not evidence:
        raise ValueError("人物结论必须包含证据")
    if not 0 <= confidence <= 1:
        raise ValueError("置信度必须在 0 到 1 之间")
    normalized_contexts = sorted({item.strip() for item in contexts if item.strip()})
    if classification == "高置信度模式" and len(normalized_contexts) < 2:
        raise ValueError("高置信度模式必须由至少两个独立情境支持")
    profile_path = profile_dir_path / "profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    claim_id = uuid.uuid4().hex
    timestamp = _now()
    conflict_ids = list(dict.fromkeys(conflicts_with or []))
    known_claims = {claim["id"]: claim for claim in profile["claims"]}
    unknown_conflicts = [item for item in conflict_ids if item not in known_claims]
    if unknown_conflicts:
        raise ValueError(f"找不到冲突结论：{', '.join(unknown_conflicts)}")
    profile["claims"].append(
        {
            "id": claim_id,
            "content": content,
            "classification": classification,
            "evidence": evidence,
            "contexts": normalized_contexts,
            "confidence": max(0.0, round(confidence - 0.15, 4)) if conflict_ids else confidence,
            "conflicts_with": conflict_ids,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    )
    for conflict_id in conflict_ids:
        existing = known_claims[conflict_id]
        if claim_id not in existing["conflicts_with"]:
            existing["conflicts_with"].append(claim_id)
        existing["confidence"] = max(0.0, round(existing["confidence"] - 0.15, 4))
        existing["updated_at"] = timestamp
    profile["updated_at"] = timestamp
    _write_json(profile_path, profile)
    return claim_id


def deletion_plan(root: str | Path, slug: str) -> dict[str, Any]:
    root_path = Path(root).resolve()
    _ensure_private_root(root_path)
    safe_slug = _safe_slug(slug)
    targets = [
        root_path / "people" / safe_slug,
        root_path / "derived" / safe_slug,
        root_path / "raw" / safe_slug,
    ]
    for target in targets:
        if not _inside(root_path, target):
            raise ValueError("拒绝删除私有数据根目录之外的路径")
    target_strings = [str(target.resolve()) for target in targets]
    token_source = "\n".join([str(root_path), safe_slug, *target_strings])
    token = hashlib.sha256(token_source.encode("utf-8")).hexdigest()[:16]
    return {"targets": target_strings, "confirmation_token": token}


def delete_profile(root: str | Path, slug: str, confirmation_token: str) -> None:
    root_path = Path(root).resolve()
    safe_slug = _safe_slug(slug)
    plan = deletion_plan(root_path, safe_slug)
    if confirmation_token != plan["confirmation_token"]:
        raise ValueError("删除确认令牌与当前目标不匹配")
    targets = [Path(item) for item in plan["targets"]]
    for target in targets:
        if target.exists():
            shutil.rmtree(target)
    manifest_path = root_path / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.get("profiles", {}).pop(safe_slug, None)
        _write_json(manifest_path, manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description="管理本地私人人物档案。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--root", type=Path, default=default_private_root())
    create_parser.add_argument("--slug", required=True)
    create_parser.add_argument("--alias", required=True)

    preview_parser = subparsers.add_parser("preview-delete")
    preview_parser.add_argument("--root", type=Path, default=default_private_root())
    preview_parser.add_argument("--slug", required=True)

    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("--root", type=Path, default=default_private_root())
    delete_parser.add_argument("--slug", required=True)
    delete_parser.add_argument("--confirm", required=True)

    args = parser.parse_args()
    if args.command == "create":
        profile_dir = create_profile(args.root, args.slug, args.alias)
        print(json.dumps({"profile_dir": str(profile_dir)}, ensure_ascii=False))
        return 0
    if args.command == "preview-delete":
        print(json.dumps(deletion_plan(args.root, args.slug), ensure_ascii=False))
        return 0
    delete_profile(args.root, args.slug, args.confirm)
    print(json.dumps({"deleted": args.slug}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
