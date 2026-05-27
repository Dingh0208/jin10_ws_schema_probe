import hashlib
import json
from typing import Any


def detect_shape(value: Any, depth: int = 0, max_depth: int = 5) -> Any:
    """Return a value-independent JSON-compatible structure shape."""
    if depth > max_depth:
        return "..."

    if isinstance(value, dict):
        keys = sorted(str(key) for key in value.keys())
        fields = {
            str(key): detect_shape(value[key], depth + 1, max_depth)
            for key in sorted(value.keys(), key=lambda item: str(item))
        }
        return {
            "_type": "object",
            "keys": keys,
            "fields": fields,
        }

    if isinstance(value, list):
        return {
            "_type": "array",
            "len_hint": len(value),
            "item": detect_shape(value[0], depth + 1, max_depth) if value else "empty",
        }

    if isinstance(value, str):
        return "str"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if value is None:
        return "null"

    return type(value).__name__


def get_structure_signature(value: Any, max_depth: int = 5) -> tuple[str, Any]:
    shape = detect_shape(value, max_depth=max_depth)
    shape_text = json.dumps(shape, sort_keys=True, ensure_ascii=False)
    signature = hashlib.sha256(shape_text.encode("utf-8")).hexdigest()[:12]
    return signature, shape


def classify_message_kind(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True).lower()

    if any(word in text for word in ("ping", "pong", "heartbeat")):
        return "heartbeat"

    if "error" in text or _has_non_success_code_or_status(value):
        return "error"

    if any(word in text for word in ("subscribe", "success", "ok")):
        return "subscribe_ack"

    if any(word in text for word in ("data", "list", "items", "news", "flash")):
        return "data_message"

    return "unknown"


def top_level_keys(value: Any) -> str:
    if isinstance(value, dict):
        return ",".join(sorted(str(key) for key in value.keys()))
    if isinstance(value, list):
        return "[]"
    return type(value).__name__


def _has_non_success_code_or_status(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in {"code", "status"} and _looks_like_error_status(item):
                return True
            if _has_non_success_code_or_status(item):
                return True

    if isinstance(value, list):
        return any(_has_non_success_code_or_status(item) for item in value)

    return False


def _looks_like_error_status(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False

    if isinstance(value, int):
        return value not in {0, 200}

    if isinstance(value, float):
        return value not in {0.0, 200.0}

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"", "0", "200", "ok", "success", "succeeded", "true"}:
            return False
        if normalized in {"error", "failed", "fail", "false", "unauthorized", "forbidden"}:
            return True
        if normalized.isdigit():
            return int(normalized) not in {0, 200}

    return False
