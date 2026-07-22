#!/usr/bin/env python3
"""Create profile-gated, privacy-safe hong-<slug> skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
RESERVED_SLUGS = {"hong", "create-hong", "update-hong"}
TARGET_DIRS = {"codex": ".codex", "claude": ".claude"}


class GenerationError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def validate_slug(slug: str) -> str:
    if slug in RESERVED_SLUGS or not SLUG_RE.fullmatch(slug):
        raise ValueError("slug 只能使用小写字母、数字和单连字符，且不能使用保留字")
    return slug


def _paths(root: Path, slug: str) -> tuple[Path, Path, Path, Path]:
    person = root / "people" / slug
    return (
        root / "self-voice.json",
        person / "profile.json",
        person / "voice-delta.json",
        person / "generation.json",
    )


def profile_version(root: Path, slug: str) -> str:
    validate_slug(slug)
    self_voice, profile, delta, _ = _paths(root, slug)
    values = [_read_json(path) for path in (self_voice, profile, delta)]
    if any(value is None for value in values):
        raise GenerationError("无法计算档案版本：三份档案必须存在且为合法 JSON")
    return hashlib.sha256(_canonical(values)).hexdigest()


def build_summary(root: Path, slug: str) -> dict[str, Any]:
    validate_slug(slug)
    self_voice_path, profile_path, delta_path, _ = _paths(root, slug)
    self_voice = _read_json(self_voice_path) or {}
    profile = _read_json(profile_path) or {}
    delta = _read_json(delta_path) or {}
    return {
        "slug": slug,
        "alias": profile.get("alias"),
        "authorization_confirmed": bool(profile.get("authorization", {}).get("confirmed")),
        "sender_mapping": profile.get("sender_mapping", {}),
        "text_message_counts": profile.get("text_message_counts", {}),
        "self_patterns": self_voice.get("patterns", []),
        "voice_delta_patterns": delta.get("patterns", []),
        "profile_version": profile_version(root, slug)
        if self_voice and profile and delta
        else None,
    }


def summary_hash(summary: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(summary)).hexdigest()


def generation_issues(
    root: Path,
    slug: str,
    confirmed_summary_hash: str,
    target: str,
) -> list[str]:
    issues: list[str] = []
    try:
        validate_slug(slug)
    except ValueError as exc:
        return [str(exc)]
    if target not in {"codex", "claude", "both"}:
        issues.append("安装目标必须是 codex、claude 或 both")
    self_voice_path, profile_path, delta_path, _ = _paths(root, slug)
    self_voice = _read_json(self_voice_path)
    profile = _read_json(profile_path)
    delta = _read_json(delta_path)
    if self_voice is None:
        issues.append("缺少或损坏 self-voice.json")
    if profile is None:
        issues.append("缺少或损坏 profile.json")
    if delta is None:
        issues.append("缺少或损坏 voice-delta.json")
    profile = profile or {}
    if not profile.get("authorization", {}).get("confirmed"):
        issues.append("尚未确认资料使用授权")
    mapping = profile.get("sender_mapping", {})
    self_aliases = {str(item) for item in mapping.get("self", []) if str(item)}
    partner_aliases = {str(item) for item in mapping.get("partner", []) if str(item)}
    if not self_aliases:
        issues.append("本人发送者映射为空")
    if not partner_aliases:
        issues.append("对象发送者映射为空")
    if self_aliases & partner_aliases:
        issues.append("本人和对象发送者映射存在重叠")
    counts = profile.get("text_message_counts", {})
    if int(counts.get("self", 0) or 0) < 1:
        issues.append("缺少本人文本消息证据")
    if int(counts.get("partner", 0) or 0) < 1:
        issues.append("缺少对象文本消息证据")
    if delta is not None and delta.get("person_id") != slug:
        issues.append("voice-delta.json 的 person_id 与 slug 不一致")
    current_hash = summary_hash(build_summary(root, slug))
    if not confirmed_summary_hash or confirmed_summary_hash != current_hash:
        issues.append("用户确认摘要哈希与当前档案不一致")
    return issues


def render_thin_skill(slug: str, expected_profile_version: str) -> dict[str, str]:
    validate_slug(slug)
    skill_name = f"hong-{slug}"
    skill = f"""---
name: {skill_name}
description: Use when 用户已经完成本地建档并明确调用 {skill_name} 处理该绑定对象的当前聊天。
---

# {skill_name}

本 Skill 固定绑定 `{slug}`，不得切换、猜测或回退到其他对象。

## 运行门槛

1. 按 `GIRLFRIEND_REPLY_COACH_DATA` 环境变量或默认私有目录解析档案根目录。
2. 读取本目录 `binding.json`，并检查对应 `profile.json`、`voice-delta.json`、共享 `self-voice.json` 和 `generation.json`。
3. 档案组合版本必须等于 `{expected_profile_version}`，且 `needs_regeneration` 必须为 `false`。
4. 任一条件不满足就停止，提示运行 `/create-hong {slug}` 或 `/update-hong {slug}`；不得生成临时回复。

## 联动

门槛通过后，必须先使用 `goutoujunshi` 生成关系判断和原始话术，再建立事实、责任、边界、承诺、行动及安全提示的语义锁。只使用本人通用语气和 `{slug}` 对应的对象专属语气进行忠实改写。

不得改变原意、泄露私人档案、冒充对象、混用其他人物资料或弱化安全提示。
"""
    binding = {
        "schema_version": 1,
        "slug": slug,
        "expected_profile_version": expected_profile_version,
        "private_root_resolution": "environment-or-default",
    }
    return {
        "SKILL.md": skill,
        "binding.json": json.dumps(binding, ensure_ascii=False, indent=2) + "\n",
    }


def write_thin_skill(destination: Path, slug: str, expected_profile_version: str) -> Path:
    rendered = render_thin_skill(slug, expected_profile_version)
    destination.mkdir(parents=True, exist_ok=False)
    for name, content in rendered.items():
        (destination / name).write_text(content, encoding="utf-8")
    return destination


def generated_targets(home: Path, slug: str, target: str) -> dict[str, Path]:
    validate_slug(slug)
    if target not in {"codex", "claude", "both"}:
        raise GenerationError("安装目标必须是 codex、claude 或 both")
    environments = ("codex", "claude") if target == "both" else (target,)
    return {
        environment: home / TARGET_DIRS[environment] / "skills" / f"hong-{slug}"
        for environment in environments
    }


def _remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def install_generated_skill(
    source: Path,
    targets: dict[str, Path],
    *,
    force: bool,
    copytree: Callable[[Path, Path], Path] = shutil.copytree,
) -> tuple[Path, ...]:
    if not targets or any(key not in TARGET_DIRS for key in targets):
        raise GenerationError("包含未知生成 Skill 安装目标")
    conflicts = [path for path in targets.values() if path.exists()]
    if conflicts and not force:
        raise GenerationError("生成 Skill 已存在；确认更新后使用 force：\n" + "\n".join(map(str, conflicts)))
    token = uuid.uuid4().hex
    backups: dict[Path, Path] = {}
    temporaries: list[Path] = []
    installed: list[Path] = []
    try:
        for path in targets.values():
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                backup = path.parent / f".{path.name}.backup-{token}"
                path.replace(backup)
                backups[path] = backup
            temporary = path.parent / f".{path.name}.installing-{token}"
            temporaries.append(temporary)
            copytree(source, temporary)
            temporary.replace(path)
            installed.append(path)
        for backup in backups.values():
            _remove_tree(backup)
        return tuple(installed)
    except Exception as exc:
        for temporary in temporaries:
            _remove_tree(temporary)
        for path in reversed(installed):
            _remove_tree(path)
        for path, backup in backups.items():
            _remove_tree(path)
            if backup.exists():
                backup.replace(path)
        raise GenerationError(f"生成 Skill 安装失败，已回滚：{exc}") from exc


def generate_for_profile(
    private_root: Path,
    home: Path,
    slug: str,
    confirmed_summary_hash: str,
    target: str,
    *,
    force: bool,
    copytree: Callable[[Path, Path], Path] = shutil.copytree,
) -> tuple[Path, ...]:
    issues = generation_issues(private_root, slug, confirmed_summary_hash, target)
    if issues:
        raise GenerationError("生成门槛未通过：\n- " + "\n- ".join(issues))
    version = profile_version(private_root, slug)
    targets = generated_targets(home, slug, target)
    with tempfile.TemporaryDirectory(prefix=f"hong-{slug}-") as temporary:
        source = Path(temporary) / f"hong-{slug}"
        write_thin_skill(source, slug, version)
        installed = install_generated_skill(source, targets, force=force, copytree=copytree)
    _, _, _, generation_path = _paths(private_root, slug)
    _write_json(
        generation_path,
        {
            "schema_version": 1,
            "slug": slug,
            "skill_name": f"hong-{slug}",
            "profile_version": version,
            "confirmed_summary_hash": confirmed_summary_hash,
            "generated_at": _now(),
            "install_targets": list(targets),
            "skill_paths": [str(path.resolve()) for path in installed],
            "needs_regeneration": False,
        },
    )
    return installed


def prepare_profile(
    root: Path,
    slug: str,
    alias: str,
    self_aliases: list[str],
    partner_aliases: list[str],
    self_count: int,
    partner_count: int,
    *,
    authorized: bool,
) -> None:
    validate_slug(slug)
    self_voice_path, profile_path, delta_path, generation_path = _paths(root, slug)
    if not self_voice_path.exists():
        _write_json(self_voice_path, {"schema_version": 1, "patterns": [], "corrections": []})
    profile = _read_json(profile_path) or {"schema_version": 1, "claims": []}
    profile.update(
        {
            "alias": alias,
            "authorization": {"confirmed": authorized},
            "sender_mapping": {"self": self_aliases, "partner": partner_aliases},
            "text_message_counts": {"self": self_count, "partner": partner_count},
            "updated_at": _now(),
        }
    )
    _write_json(profile_path, profile)
    if not delta_path.exists():
        _write_json(delta_path, {"schema_version": 1, "person_id": slug, "patterns": [], "corrections": []})
    generation = _read_json(generation_path) or {"schema_version": 1, "slug": slug, "skill_name": f"hong-{slug}"}
    generation["needs_regeneration"] = True
    _write_json(generation_path, generation)


def mark_stale(root: Path, slug: str) -> None:
    validate_slug(slug)
    _, _, _, generation_path = _paths(root, slug)
    generation = _read_json(generation_path)
    if generation is None:
        raise GenerationError("generation.json 不存在")
    generation["needs_regeneration"] = True
    _write_json(generation_path, generation)


def default_private_root() -> Path:
    import os

    configured = os.environ.get("GIRLFRIEND_REPLY_COACH_DATA")
    return Path(configured).expanduser().resolve() if configured else (Path.home() / ".codex/private/girlfriend-reply-coach").resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="先建档，再生成固定绑定对象的 hong Skill。")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--root", type=Path, default=default_private_root())
    prepare.add_argument("--slug", required=True)
    prepare.add_argument("--alias", required=True)
    prepare.add_argument("--self-alias", action="append", required=True)
    prepare.add_argument("--partner-alias", action="append", required=True)
    prepare.add_argument("--self-count", type=int, required=True)
    prepare.add_argument("--partner-count", type=int, required=True)
    prepare.add_argument("--authorized", action="store_true", required=True)
    preview = sub.add_parser("preview")
    preview.add_argument("--root", type=Path, default=default_private_root())
    preview.add_argument("--slug", required=True)
    generate = sub.add_parser("generate")
    generate.add_argument("--root", type=Path, default=default_private_root())
    generate.add_argument("--home", type=Path, default=Path.home())
    generate.add_argument("--slug", required=True)
    generate.add_argument("--confirm-hash", required=True)
    generate.add_argument("--target", choices=("codex", "claude", "both"), required=True)
    generate.add_argument("--force", action="store_true")
    stale = sub.add_parser("mark-stale")
    stale.add_argument("--root", type=Path, default=default_private_root())
    stale.add_argument("--slug", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            prepare_profile(args.root, args.slug, args.alias, args.self_alias, args.partner_alias, args.self_count, args.partner_count, authorized=args.authorized)
            print(json.dumps({"prepared": args.slug}, ensure_ascii=False))
        elif args.command == "preview":
            summary = build_summary(args.root, args.slug)
            print(json.dumps({"summary": summary, "confirmation_hash": summary_hash(summary)}, ensure_ascii=False, indent=2))
        elif args.command == "generate":
            paths = generate_for_profile(args.root, args.home, args.slug, args.confirm_hash, args.target, force=args.force)
            print(json.dumps({"installed": [str(path) for path in paths]}, ensure_ascii=False))
        else:
            mark_stale(args.root, args.slug)
            print(json.dumps({"stale": args.slug}, ensure_ascii=False))
        return 0
    except (ValueError, GenerationError) as exc:
        parser.exit(1, f"失败：{exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
