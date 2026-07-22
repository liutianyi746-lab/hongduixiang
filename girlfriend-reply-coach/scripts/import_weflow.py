#!/usr/bin/env python3
"""Locally normalize WeFlow-like TXT, JSON, and JSONL chat exports."""

from __future__ import annotations

import json
import re
import argparse
from pathlib import Path
from typing import Any, NamedTuple


class Message(NamedTuple):
    timestamp: str
    sender: str
    content: str
    kind: str


class ImportResult(NamedTuple):
    messages: list[Message]
    skipped_count: int
    warnings: list[str]


HEADER_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+['\"](?P<sender>.+?)['\"]\s*$"
)
MEDIA_VALUES = {"[表情包]", "[图片]", "[视频]", "[语音]", "[文件]"}
SYSTEM_MARKERS = (
    "撤回了一条消息",
    "现在可以开始聊天了",
    "你已添加了",
    "以上是打招呼的内容",
)
TIME_FIELDS = ("timestamp", "time", "datetime", "createTime")
SENDER_FIELDS = ("sender", "senderName", "name", "nickname")
CONTENT_FIELDS = ("content", "text", "message", "msg")


def _first(record: dict[str, Any], fields: tuple[str, ...]) -> Any:
    for field in fields:
        value = record.get(field)
        if value is not None and str(value).strip():
            return value
    return None


def _kind(content: str, declared: Any = None) -> str:
    declared_text = str(declared or "").lower()
    if any(marker in content for marker in SYSTEM_MARKERS) or declared_text in {
        "system",
        "notice",
    }:
        return "system"
    if content in MEDIA_VALUES or declared_text in {
        "image",
        "video",
        "audio",
        "file",
        "sticker",
        "media",
    }:
        return "media"
    return "text"


def normalize_record(record: dict[str, Any]) -> tuple[Message | None, str | None]:
    timestamp = _first(record, TIME_FIELDS)
    sender = _first(record, SENDER_FIELDS)
    content = _first(record, CONTENT_FIELDS)
    if timestamp is None or sender is None or content is None:
        return None, "记录缺少时间、发送者或正文"
    content_text = str(content).strip()
    if not content_text:
        return None, "记录正文为空"
    return (
        Message(
            timestamp=str(timestamp).strip(),
            sender=str(sender).strip(),
            content=content_text,
            kind=_kind(content_text, record.get("type") or record.get("msgType")),
        ),
        None,
    )


def parse_txt(text: str) -> ImportResult:
    messages: list[Message] = []
    warnings: list[str] = []
    current: dict[str, Any] | None = None
    body: list[str] = []
    orphan_lines: list[str] = []

    def flush() -> None:
        nonlocal current, body
        if current is None:
            return
        current["content"] = "\n".join(body).strip()
        message, warning = normalize_record(current)
        if message is not None:
            messages.append(message)
        elif warning:
            warnings.append(warning)
        current = None
        body = []

    for raw_line in text.splitlines():
        match = HEADER_RE.match(raw_line)
        if match:
            flush()
            current = match.groupdict()
            continue
        if current is not None:
            body.append(raw_line)
        elif raw_line.strip():
            orphan_lines.append(raw_line.strip())
    flush()
    if orphan_lines:
        warnings.append(f"有 {len(orphan_lines)} 行无法归入任何受支持的消息")
    return ImportResult(messages, len(warnings), warnings)


def _collect_json_records(items: list[Any]) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            records.append(item)
        else:
            warnings.append(f"第 {index} 条不是消息对象")
    return records, warnings


def _records_from_json(value: Any) -> tuple[list[dict[str, Any]], list[str]]:
    if isinstance(value, list):
        return _collect_json_records(value)
    if isinstance(value, dict):
        for field in ("messages", "records", "data"):
            nested = value.get(field)
            if isinstance(nested, list):
                return _collect_json_records(nested)
    raise ValueError("JSON 顶层必须是消息数组，或包含 messages/records/data 数组")


def _normalize_records(records: list[dict[str, Any]]) -> ImportResult:
    messages: list[Message] = []
    warnings: list[str] = []
    for index, record in enumerate(records, start=1):
        message, warning = normalize_record(record)
        if message is not None:
            messages.append(message)
        else:
            warnings.append(f"第 {index} 条：{warning}")
    return ImportResult(messages, len(warnings), warnings)


def parse_json(text: str) -> ImportResult:
    records, initial_warnings = _records_from_json(json.loads(text))
    result = _normalize_records(records)
    return ImportResult(
        result.messages,
        result.skipped_count + len(initial_warnings),
        initial_warnings + result.warnings,
    )


def parse_jsonl(text: str) -> ImportResult:
    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            warnings.append(f"第 {line_number} 行不是有效 JSON：{exc.msg}")
            continue
        if not isinstance(value, dict):
            warnings.append(f"第 {line_number} 行不是消息对象")
            continue
        records.append(value)
    result = _normalize_records(records)
    return ImportResult(
        result.messages,
        result.skipped_count + len(warnings),
        warnings + result.warnings,
    )


def to_evidence(result: ImportResult) -> dict[str, Any]:
    text_messages = [
        message._asdict() for message in result.messages if message.kind == "text"
    ]
    media_count = sum(message.kind == "media" for message in result.messages)
    return {
        "messages": text_messages,
        "message_type_counts": {"media": media_count} if media_count else {},
        "skipped_count": result.skipped_count,
        "warnings": result.warnings,
    }


def _git_worktree_root(path: Path) -> Path | None:
    candidate = path.resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for parent in (candidate, *candidate.parents):
        if (parent / ".git").exists():
            return parent
    return None


def _ensure_private_output(path: Path) -> None:
    worktree = _git_worktree_root(path)
    if worktree is not None:
        raise ValueError(f"拒绝把私人聊天输出写入 Git 工作区：{worktree}")


def import_file(path: str | Path) -> ImportResult:
    source = Path(path)
    text = source.read_text(encoding="utf-8-sig")
    suffix = source.suffix.lower()
    if suffix == ".txt":
        result = parse_txt(text)
    elif suffix == ".json":
        result = parse_json(text)
    elif suffix in {".jsonl", ".ndjson"}:
        result = parse_jsonl(text)
    else:
        raise ValueError(f"不支持的导出格式：{suffix or '无扩展名'}")
    if not result.messages:
        raise ValueError("没有识别到可靠消息；请检查格式和发送者字段")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="在本地解析聊天导出；默认只输出统计，不输出消息正文。"
    )
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        help="明确指定后才把标准化消息写入本地 JSON 文件",
    )
    args = parser.parse_args()
    result = import_file(args.source)
    if args.output:
        _ensure_private_output(args.output)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                to_evidence(result),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                "message_count": len(result.messages),
                "skipped_count": result.skipped_count,
                "warning_count": len(result.warnings),
                "output": str(args.output) if args.output else None,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
