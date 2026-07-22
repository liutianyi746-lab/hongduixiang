#!/usr/bin/env python3
"""Install hongduixiang and its independent goutoujunshi dependency."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Callable


SKILL_NAMES = ("girlfriend-reply-coach", "create-hong", "goutoujunshi")
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


def _validate_targets(targets: dict[str, Path]) -> None:
    if not targets:
        raise InstallError("安装目标不能为空")
    for key, target in targets.items():
        try:
            environment, skill_name = key.split(":", 1)
        except ValueError as exc:
            raise InstallError(f"无效安装目标标识：{key}") from exc
        if environment not in ENVIRONMENT_DIRS or skill_name not in SKILL_NAMES:
            raise InstallError(f"拒绝未知安装目标：{key}")
        expected_tail = Path(ENVIRONMENT_DIRS[environment]) / "skills" / skill_name
        if tuple(target.parts[-3:]) != tuple(expected_tail.parts):
            raise InstallError(f"安装目标路径与标识不匹配：{target}")


def _remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def install_sources(
    local_skill: Path,
    goutoujunshi_skill: Path,
    targets: dict[str, Path],
    *,
    force: bool,
    copytree: Callable[[Path, Path], Path] = shutil.copytree,
    creator_skill: Path | None = None,
) -> tuple[Path, ...]:
    _validate_targets(targets)
    if _skill_name(local_skill / "SKILL.md") != "girlfriend-reply-coach":
        raise InstallError("本地 SKILL.md 的 name 必须等于 girlfriend-reply-coach")
    if _skill_name(goutoujunshi_skill / "SKILL.md") != "goutoujunshi":
        raise InstallError("第三方 SKILL.md 的 name 必须等于 goutoujunshi")
    creator = creator_skill or local_skill.parent / "create-hong"
    if _skill_name(creator / "SKILL.md") != "create-hong":
        raise InstallError("本地 SKILL.md 的 name 必须等于 create-hong")

    conflicts = [target for target in targets.values() if target.exists()]
    if conflicts and not force:
        joined = "\n".join(str(path) for path in conflicts)
        raise InstallError(f"以下 Skill 已存在；如需覆盖请使用 --force：\n{joined}")

    token = uuid.uuid4().hex
    backups: dict[Path, Path] = {}
    temporary_paths: list[Path] = []
    installed: list[Path] = []
    sources = {
        "girlfriend-reply-coach": local_skill,
        "create-hong": creator,
        "goutoujunshi": goutoujunshi_skill,
    }

    try:
        for key, target in targets.items():
            skill_name = key.split(":", 1)[1]
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                backup = target.parent / f".{target.name}.backup-{token}"
                target.replace(backup)
                backups[target] = backup

            temporary = target.parent / f".{target.name}.installing-{token}"
            temporary_paths.append(temporary)
            copytree(sources[skill_name], temporary)
            temporary.replace(target)
            installed.append(target)

        for backup in backups.values():
            _remove_tree(backup)
        return tuple(installed)
    except Exception as exc:
        for temporary in temporary_paths:
            _remove_tree(temporary)
        for target in reversed(installed):
            _remove_tree(target)
        restore_errors = []
        for target, backup in backups.items():
            try:
                _remove_tree(target)
                if backup.exists():
                    backup.replace(target)
            except Exception as restore_exc:  # pragma: no cover - catastrophic filesystem failure
                restore_errors.append(f"{target}: {restore_exc}")
        detail = f"安装失败，已回滚：{exc}"
        if restore_errors:
            detail += "；恢复失败：" + "; ".join(restore_errors)
        raise InstallError(detail) from exc


def clone_goutoujunshi(
    repo_url: str,
    destination: Path,
    *,
    runner: Callable[..., object] = subprocess.run,
) -> Path:
    command = ["git", "clone", "--depth", "1", repo_url, str(destination)]
    try:
        result = runner(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise InstallError("找不到 git，请先安装 Git 并确保它位于 PATH 中") from exc
    if getattr(result, "returncode", 1) != 0:
        stderr = str(getattr(result, "stderr", "")).strip()
        raise InstallError(f"克隆 goutoujunshi 失败：{stderr or 'git 未提供错误详情'}")
    return destination


def _conflicting_targets(targets: dict[str, Path]) -> list[Path]:
    return [path for path in targets.values() if path.exists()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="同时安装 hongduixiang 与独立的 goutoujunshi Skill。"
    )
    parser.add_argument("--target", choices=("codex", "claude", "both"), required=True)
    parser.add_argument("--force", action="store_true", help="事务式覆盖已有 Skill")
    parser.add_argument(
        "--goutoujunshi-repo",
        default="https://github.com/powerycy/goutoujunshi.git",
        help="goutoujunshi Git 仓库地址",
    )
    args = parser.parse_args(argv)

    try:
        repository_root = Path(__file__).resolve().parent
        local_skill = repository_root / "girlfriend-reply-coach"
        creator_skill = repository_root / "create-hong"
        if not (local_skill / "SKILL.md").is_file():
            raise InstallError(f"找不到本地 girlfriend-reply-coach/SKILL.md：{local_skill}")
        targets = installation_targets(Path.home(), args.target)
        conflicts = _conflicting_targets(targets)
        if conflicts and not args.force:
            joined = "\n".join(str(path) for path in conflicts)
            raise InstallError(f"以下 Skill 已存在；如需覆盖请使用 --force：\n{joined}")

        print("第三方提示：goutoujunshi 为独立项目，未获官方背书。")
        print("许可：PolyForm Noncommercial License 1.0.0")
        print(f"来源：{args.goutoujunshi_repo}")
        with tempfile.TemporaryDirectory(prefix="hongduixiang-install-") as temporary:
            checkout = Path(temporary) / "goutoujunshi-repo"
            clone_goutoujunshi(args.goutoujunshi_repo, checkout)
            goutoujunshi_skill = find_goutoujunshi_skill(checkout)
            installed = install_sources(
                local_skill,
                goutoujunshi_skill,
                targets,
                force=args.force,
                creator_skill=creator_skill,
            )
        print("安装成功：")
        for path in installed:
            print(f"- {path}")
        print("请重新启动 Codex / Claude Code 以加载新 Skill。")
        return 0
    except InstallError as exc:
        parser.exit(1, f"安装失败：{exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
