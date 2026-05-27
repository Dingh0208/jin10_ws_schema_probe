from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from config import PUSH_QUEUE_PATH, QQ_SENT_LOG_PATH


def now_local_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def append_jsonl_flush(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        file.flush()


def build_queue_id(item: dict[str, Any]) -> str:
    news_id = str(item.get("news_id") or "").strip()
    reason_type = str(item.get("reason_type") or "UNKNOWN").strip() or "UNKNOWN"
    if news_id:
        return f"{news_id}:{reason_type}"

    content = str(item.get("content") or item.get("push_text") or "")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    return f"content:{digest}:{reason_type}"


def _load_queue_ids_from_jsonl(path: Path) -> set[str]:
    ids: set[str] = set()
    if not path.exists():
        return ids

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            queue_id = str(payload.get("queue_id") or "").strip()
            if queue_id:
                ids.add(queue_id)
    return ids


def load_existing_queue_ids(queue_path: Path = PUSH_QUEUE_PATH) -> set[str]:
    return _load_queue_ids_from_jsonl(queue_path)


def load_sent_queue_ids(sent_log_path: Path = QQ_SENT_LOG_PATH) -> set[str]:
    return _load_queue_ids_from_jsonl(sent_log_path)


def build_push_item(msg: dict[str, Any], score_result: dict[str, Any], receive_time: str, push_text: str) -> dict[str, Any]:
    fields = score_result.get("fields") or {}
    content = fields.get("body") or fields.get("title") or fields.get("meta") or json.dumps(msg, ensure_ascii=False, sort_keys=True)
    news_id = str(msg.get("id") or "").strip()
    item = {
        "queue_id": "",
        "news_id": news_id,
        "time": msg.get("time") or receive_time,
        "reason_type": score_result.get("reason_type") or "UNKNOWN",
        "score": score_result.get("score"),
        "matched_keywords": score_result.get("matched_keywords") or [],
        "content": content,
        "push_text": push_text,
        "source": "jin10",
        "status": "pending",
        "created_at": now_local_iso(),
    }
    item["queue_id"] = build_queue_id(item)
    return item


def enqueue_push_item(item: dict[str, Any], queue_path: Path = PUSH_QUEUE_PATH, sent_log_path: Path = QQ_SENT_LOG_PATH) -> bool:
    queue_id = str(item.get("queue_id") or build_queue_id(item)).strip()
    if not queue_id:
        raise ValueError("queue_id is empty")
    item["queue_id"] = queue_id

    if queue_id in load_existing_queue_ids(queue_path):
        return False
    if queue_id in load_sent_queue_ids(sent_log_path):
        return False

    append_jsonl_flush(queue_path, item)
    return True


def read_offset(offset_path: Path) -> int:
    try:
        return int(offset_path.read_text(encoding="utf-8").strip() or "0")
    except Exception:
        return 0


def write_offset(offset_path: Path, offset: int) -> None:
    offset_path.parent.mkdir(parents=True, exist_ok=True)
    with offset_path.open("w", encoding="utf-8") as file:
        file.write(str(max(0, offset)) + "\n")
        file.flush()


def consume_queue_incrementally(
    queue_path: Path,
    offset_path: Path,
    handle_message: Callable[[dict[str, Any]], bool],
) -> int:
    """
    Read push_queue.jsonl from the last byte offset.
    A successful handler call advances the offset. Failure stops this pass so
    the same line can be retried next time.
    """
    if not queue_path.exists():
        return 0

    file_size = queue_path.stat().st_size
    offset = read_offset(offset_path)
    if offset > file_size:
        offset = 0
        write_offset(offset_path, offset)

    processed = 0
    with queue_path.open("rb") as file:
        file.seek(offset)
        while True:
            line_start = file.tell()
            line = file.readline()
            if not line:
                break
            if not line.endswith(b"\n"):
                break

            next_offset = file.tell()
            try:
                payload = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                file.seek(line_start)
                break

            try:
                ok = handle_message(payload)
            except Exception:
                ok = False

            if not ok:
                break

            write_offset(offset_path, next_offset)
            processed += 1

    return processed
