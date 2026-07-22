#!/usr/bin/env python3
"""Install hongduixiang and its independent goutoujunshi dependency."""

from __future__ import annotations

from pathlib import Path


SKILL_NAMES = ("girlfriend-reply-coach", "goutoujunshi")
ENVIRONMENT_DIRS = {"codex": ".codex", "claude": ".claude"}


class InstallError(RuntimeError):
    """Raised when installation cannot complete safely."""


def installation_targets(home: Path, target: str) -> dict[str, Path]:
    if target not in {"codex", "claude", "both"}:
        raise InstallError(f"无效 target：{target}")
    environments = ("codex", "claude") if target == "both" else (target,)
    return {
        f"{environment}:{skill_name}": home
        / ENVIRONMENT_DIRS[environment]
        / "skills"
        / skill_name
        for environment in environments
        for skill_name in SKILL_NAMES
    }


def _skill_name(skill_file: Path) -> str:
    text = skill_file.read_text(encoding="utf-8")
    if not text.strip():
        raise InstallError(f"SKILL.md 为空：{skill_file}")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise InstallError(f"SKILL.md 缺少 YAML frontmatter：{skill_file}")
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("'\"")
    raise InstallError(f"SKILL.md frontmatter 缺少 name：{skill_file}")


def find_goutoujunshi_skill(repo_root: Path) -> Path:
    candidates = (repo_root, repo_root / "goutoujunshi")
    existing = [candidate for candidate in candidates if (candidate / "SKILL.md").is_file()]
    if not existing:
        raise InstallError(f"下载仓库中找不到 goutoujunshi/SKILL.md：{repo_root}")
    valid = [candidate for candidate in existing if _skill_name(candidate / "SKILL.md") == "goutoujunshi"]
    if len(valid) != 1:
        raise InstallError("goutoujunshi SKILL.md 的 name 必须唯一且等于 goutoujunshi")
    return valid[0]
