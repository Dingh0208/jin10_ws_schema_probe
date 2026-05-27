from __future__ import annotations

import json
import os
import re
import signal
import sys
import time
import hashlib
import traceback
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args: object, **kwargs: object) -> bool:
        return False

if TYPE_CHECKING:
    from websocket import WebSocketApp

from shape_detector import classify_message_kind, get_structure_signature, top_level_keys

from config import (
    BASE_DIR,
    DATA_DIR,
    LOG_DIR,
    RAW_MESSAGES_PATH,
    NON_JSON_PATH,
    SCHEMA_STATS_PATH,
    SCHEMA_SAMPLES_PATH,
    RAW_MESSAGES_LOG_PATH,
    FILTER_HITS_LOG_PATH,
    PUSHED_NEWS_PATH,
    SKIPPED_NEWS_PATH,
    SEEN_NEWS_IDS_PATH,
    ERRORS_LOG_PATH,
    DEDUP_CACHE_PATH,
    DEDUP_TTL_SECONDS,
    QQ_BOT_API_URL,
    QQ_FAILED_LOG_PATH,
    QQ_GROUP_ID,
    QQ_PUSH_ENABLED,
    QQ_SENT_LOG_PATH,
    WRITE_LEGACY_RAW_JSONL,
    WRITE_NON_JSON_DEBUG_LOG,
    WRITE_SCHEMA_DEBUG_LOGS,
)
from impact_analyzer import (
    analyze_market_impact,
    append_impact_to_push_text,
    format_impact_for_qq,
    log_impact_analysis,
)
from news_filter import (
    build_push_text,
    evaluate_news,
    extract_text_fields,
    full_news_text,
    is_push_candidate,
    message_id,
    primary_news_content,
    score_news,
)
from push_queue import build_push_item, enqueue_push_item
from qq_pusher import post_onebot


SUBSCRIBE_MESSAGE = {"type": "subscribe", "channels": ["flash"]}
SAVE_EVERY_MESSAGES = 20
SAVE_EVERY_SECONDS = 60
MAX_SAMPLES_PER_SCHEMA = 3

schema_stats: dict[str, dict[str, Any]] = {}
schema_samples: dict[str, list[dict[str, Any]]] = {}
seen_news_ids: set[str] = set()
dedup_cache: dict[str, float] = {}
message_count = 0
last_save_time = 0.0
stop_requested = False
active_ws: Any | None = None


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def mask_ws_url(url: str) -> str:
    return re.sub(r"([?&]token=)[^&]*", r"\1***", url, flags=re.IGNORECASE)


def ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        file.flush()


def append_text(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(text + "\n")
        file.flush()


def log_error(event: str, exc: Any | None = None, **extra: Any) -> None:
    payload: dict[str, Any] = {
        "time": now_iso(),
        "event": event,
        **extra,
    }
    if exc is not None:
        payload["error_type"] = type(exc).__name__
        payload["error"] = str(exc)
        payload["traceback"] = traceback.format_exc()
    try:
        append_jsonl(ERRORS_LOG_PATH, payload)
    except Exception as write_exc:
        print(f"[ERROR] write errors.log failed: {write_exc}", flush=True)


def load_seen_news_ids() -> None:
    seen_news_ids.clear()
    if not SEEN_NEWS_IDS_PATH.exists():
        return

    try:
        for line in SEEN_NEWS_IDS_PATH.read_text(encoding="utf-8").splitlines():
            news_id = line.strip()
            if news_id:
                seen_news_ids.add(news_id)
    except Exception as exc:
        log_error("load_seen_news_ids_failed", exc)
        print(f"[ERROR] load seen ids failed: {exc}", flush=True)


def mark_seen_news_id(news_id: str) -> None:
    if not news_id or news_id in seen_news_ids:
        return
    seen_news_ids.add(news_id)
    append_text(SEEN_NEWS_IDS_PATH, news_id)


def load_dedup_cache() -> None:
    dedup_cache.clear()
    if not DEDUP_CACHE_PATH.exists():
        return
    try:
        payload = json.loads(DEDUP_CACHE_PATH.read_text(encoding="utf-8") or "{}")
        if isinstance(payload, dict):
            now_ts = time.time()
            for key, value in payload.items():
                try:
                    ts = float(value)
                except (TypeError, ValueError):
                    continue
                if now_ts - ts <= DEDUP_TTL_SECONDS:
                    dedup_cache[str(key)] = ts
    except Exception as exc:
        log_error("load_dedup_cache_failed", exc)


def save_dedup_cache() -> None:
    try:
        DEDUP_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEDUP_CACHE_PATH.write_text(json.dumps(dedup_cache, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    except Exception as exc:
        log_error("save_dedup_cache_failed", exc)


def prune_dedup_cache() -> None:
    now_ts = time.time()
    expired = [key for key, ts in dedup_cache.items() if now_ts - ts > DEDUP_TTL_SECONDS]
    for key in expired:
        dedup_cache.pop(key, None)


def build_dedup_hash(msg: dict[str, Any], text: str) -> str:
    fields = extract_text_fields(msg)
    core = {
        "id": message_id(msg),
        "time": msg.get("time") or "",
        "title": fields.get("title") or "",
        "content": fields.get("body") or text,
    }
    if not core["id"]:
        core.pop("id", None)
    raw = json.dumps(core, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def truncate_text(text: str, max_chars: int = 800) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1] + "..."


def build_realtime_push_text(msg: dict[str, Any], receive_time: str, evaluation: dict[str, Any]) -> str:
    keywords = ", ".join(evaluation.get("matched_keywords") or []) or evaluation.get("hit_type") or "market_related"
    hit_type = str(evaluation.get("hit_type") or "market_related_hit")
    final_score = int(evaluation.get("final_score") or 0)
    label = "高相关" if final_score >= 12 else "宏观影响" if hit_type == "macro_market_hit" else ""
    title = f"【金十快讯｜{hit_type}{'｜' + label if label else ''}】"
    return "\n".join(
        [
            title,
            "",
            f"时间：{msg.get('time') or receive_time}",
            f"关键词：{keywords}",
            f"评分：{final_score}",
            f"内容：{truncate_text(str(evaluation.get('text') or primary_news_content(msg)))}",
        ]
    )


def append_market_impact_to_push_text(push_text: str, text: str, evaluation: dict[str, Any]) -> str:
    try:
        impact = analyze_market_impact(text, evaluation)
        try:
            log_impact_analysis(text, impact, evaluation)
        except Exception as log_exc:
            log_error("impact_analysis_log_failed", log_exc, text=text[:500])
        impact_text = format_impact_for_qq(impact)
        return append_impact_to_push_text(push_text, impact_text)
    except Exception as exc:
        log_error("impact_analysis_failed", exc, text=text[:500])
        return push_text


def write_filter_hit(
    receive_time: str,
    msg: dict[str, Any],
    dedup_hash: str,
    push_text: str,
    evaluation: dict[str, Any],
) -> None:
    append_jsonl(
        FILTER_HITS_LOG_PATH,
        {
            "receive_time": receive_time,
            "news_id": message_id(msg),
            "news_time": msg.get("time") or receive_time,
            "dedup_hash": dedup_hash,
            "text": evaluation.get("text") or primary_news_content(msg),
            "final_score": evaluation.get("final_score"),
            "hit_type": evaluation.get("hit_type"),
            "matched_keywords": evaluation.get("matched_keywords") or [],
            "crypto_score": evaluation.get("crypto_score"),
            "macro_score": evaluation.get("macro_score"),
            "market_score": evaluation.get("market_score"),
            "risk_score": evaluation.get("risk_score"),
            "policy_score": evaluation.get("policy_score"),
            "noise_score": evaluation.get("noise_score"),
            "decision": evaluation.get("decision"),
            "push_text": push_text,
        },
    )


def write_qq_sent(item: dict[str, Any]) -> None:
    append_jsonl(QQ_SENT_LOG_PATH, item)


def write_qq_failed(item: dict[str, Any]) -> None:
    append_jsonl(ERRORS_LOG_PATH, {**item, "time": now_iso(), "event": "onebot_send_failed"})


def send_realtime_push(
    receive_time: str,
    msg: dict[str, Any],
    dedup_hash: str,
    push_text: str,
    evaluation: dict[str, Any],
) -> bool:
    base_record = {
        "queue_id": dedup_hash,
        "dedup_hash": dedup_hash,
        "news_id": message_id(msg),
        "news_time": msg.get("time") or receive_time,
        "hit_type": evaluation.get("hit_type"),
        "final_score": evaluation.get("final_score"),
        "matched_keywords": evaluation.get("matched_keywords") or [],
        "crypto_score": evaluation.get("crypto_score"),
        "macro_score": evaluation.get("macro_score"),
        "market_score": evaluation.get("market_score"),
        "risk_score": evaluation.get("risk_score"),
        "policy_score": evaluation.get("policy_score"),
        "noise_score": evaluation.get("noise_score"),
        "group_id": QQ_GROUP_ID,
        "api_url": QQ_BOT_API_URL,
        "push_text": push_text,
    }
    if not QQ_PUSH_ENABLED:
        print(f"[QQ_DISABLED] dedup_hash={dedup_hash}", flush=True)
        return True

    try:
        status, body = post_onebot(QQ_BOT_API_URL, {"group_id": QQ_GROUP_ID, "message": push_text})
    except Exception as exc:
        http_status = exc.code if isinstance(exc, urllib.error.HTTPError) else None
        response_text = ""
        if isinstance(exc, urllib.error.HTTPError):
            try:
                response_text = exc.read(2000).decode("utf-8", errors="replace")
            except Exception:
                response_text = ""
        write_qq_failed(
            {
                **base_record,
                "status": "failed",
                "failed_at": now_iso(),
                "http_status": http_status,
                "response": response_text,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        log_error("onebot_api_exception", exc, dedup_hash=dedup_hash, news_id=message_id(msg))
        return False

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        payload = None
    ok = 200 <= status < 300 and isinstance(payload, dict) and payload.get("retcode") == 0
    record = {
        **base_record,
        "http_status": status,
        "response": body,
        "sent_at" if ok else "failed_at": now_iso(),
        "status": "sent" if ok else "failed",
    }
    if ok:
        write_qq_sent(record)
        return True
    record["error"] = "OneBot response not success"
    write_qq_failed(record)
    return False


def handle_realtime_filter(receive_time: str, msg: Any, raw_text: str) -> None:
    if not isinstance(msg, dict):
        return

    if not is_push_candidate(msg):
        return

    text = full_news_text(msg)
    evaluation = evaluate_news(msg)
    if evaluation.get("decision") != "push":
        return

    dedup_hash = build_dedup_hash(msg, text)
    prune_dedup_cache()
    if dedup_hash in dedup_cache:
        print(f"[DUPLICATE] hash={dedup_hash} id={message_id(msg) or '-'}", flush=True)
        return

    push_text = build_realtime_push_text(msg, receive_time, evaluation)
    push_text = append_market_impact_to_push_text(push_text, text, evaluation)
    write_filter_hit(receive_time, msg, dedup_hash, push_text, evaluation)
    sent_or_dry_run = send_realtime_push(receive_time, msg, dedup_hash, push_text, evaluation)
    if sent_or_dry_run:
        dedup_cache[dedup_hash] = time.time()
        save_dedup_cache()
        news_id = message_id(msg)
        if news_id:
            mark_seen_news_id(news_id)
        keywords = evaluation.get("matched_keywords") or []
        print(f"[REALTIME_PUSH] hash={dedup_hash} id={news_id or '-'} hits={','.join(keywords)}", flush=True)


def handle_macro_filter(receive_time: str, msg: Any, raw_text: str) -> None:
    if not isinstance(msg, dict):
        return

    if message_id(msg) in seen_news_ids:
        write_skipped_message(receive_time, raw_text, "duplicate_id", None)
        return

    if not is_push_candidate(msg):
        write_skipped_message(receive_time, raw_text, "not_push_candidate", None)
        return

    score_result = score_news(msg)
    if score_result["score"] >= 5:
        news_id = message_id(msg)
        if news_id:
            mark_seen_news_id(news_id)

        push_text = build_push_text(msg, receive_time, score_result)
        item = build_push_item(msg, score_result, receive_time, push_text)
        queued = enqueue_push_item(item)
        append_jsonl(
            PUSHED_NEWS_PATH,
            {
                "queue_id": item["queue_id"],
                "news_id": news_id,
                "time": item["time"],
                "reason_type": score_result.get("reason_type") or "UNKNOWN",
                "score": score_result["score"],
                "matched_keywords": score_result.get("matched_keywords") or [],
                "push_reason": score_result.get("push_reason") or "",
                "queued": queued,
                "raw_text": raw_text,
            },
        )
        print(
            "[MACRO_MATCH] "
            f"id={news_id or '-'} queue_id={item['queue_id']} queued={queued} "
            f"score={score_result['score']} "
            f"type={score_result.get('reason_type') or 'UNKNOWN'} "
            f"hits={','.join(score_result['matched_keywords'][:8])}",
            flush=True,
        )
        return

    write_skipped_message(receive_time, raw_text, score_result["decision"], score_result)


def write_skipped_message(
    receive_time: str,
    raw_text: str,
    reason: str,
    score_result: dict[str, Any] | None,
) -> None:
    payload = {
        "receive_time": receive_time,
        "reason": reason,
        "score": score_result["score"] if score_result else None,
        "matched_keywords": score_result["matched_keywords"] if score_result else [],
        "score_reasons": score_result["reasons"] if score_result else [],
        "push_reason": score_result["push_reason"] if score_result else None,
        "skip_reason": score_result["skip_reason"] if score_result else reason,
        "skipped_reason": score_result["skip_reason"] if score_result else reason,
        "reason_type": score_result["reason_type"] if score_result else None,
        "raw_text": raw_text,
    }
    append_jsonl(SKIPPED_NEWS_PATH, payload)


def save_schema_files() -> None:
    global last_save_time
    if not WRITE_SCHEMA_DEBUG_LOGS:
        last_save_time = time.monotonic()
        return
    ensure_log_dir()
    with SCHEMA_STATS_PATH.open("w", encoding="utf-8") as file:
        json.dump(schema_stats, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")
    with SCHEMA_SAMPLES_PATH.open("w", encoding="utf-8") as file:
        json.dump(schema_samples, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")
    last_save_time = time.monotonic()


def save_if_needed(force: bool = False) -> None:
    if force:
        save_schema_files()
        return

    elapsed = time.monotonic() - last_save_time
    if message_count > 0 and (message_count % SAVE_EVERY_MESSAGES == 0 or elapsed >= SAVE_EVERY_SECONDS):
        save_schema_files()


def handle_json_message(receive_time: str, data: Any, raw_text: str) -> None:
    signature, shape = get_structure_signature(data)
    kind = classify_message_kind(data)
    is_new_schema = signature not in schema_stats

    if is_new_schema:
        schema_stats[signature] = {
            "count": 0,
            "first_seen": receive_time,
            "last_seen": receive_time,
            "message_kind": kind,
            "shape": shape,
        }
        schema_samples[signature] = []

    stat = schema_stats[signature]
    stat["count"] += 1
    stat["last_seen"] = receive_time
    stat["message_kind"] = kind

    if len(schema_samples[signature]) < MAX_SAMPLES_PER_SCHEMA:
        schema_samples[signature].append(
            {
                "receive_time": receive_time,
                "raw_json": data,
            }
        )

    print(f"[MESSAGE] length={len(raw_text)} schema={signature} kind={kind} count={stat['count']}", flush=True)

    if is_new_schema:
        print(f"[NEW_SCHEMA] schema={signature} kind={kind} keys={top_level_keys(data)}", flush=True)


def on_open(ws: WebSocketApp) -> None:
    try:
        ws.send(json.dumps(SUBSCRIBE_MESSAGE, ensure_ascii=False))
        print("[OPEN] connected, subscribe sent channels=flash", flush=True)
    except Exception as exc:
        log_error("subscribe_failed", exc)
        print(f"[ERROR] subscribe failed: {exc}", flush=True)


def on_message(ws: WebSocketApp, message: Any) -> None:
    global message_count

    receive_time = now_iso()
    raw_text = message if isinstance(message, str) else str(message)
    message_count += 1

    try:
        append_jsonl(RAW_MESSAGES_LOG_PATH, {"receive_time": receive_time, "raw_text": raw_text})
        if WRITE_LEGACY_RAW_JSONL:
            append_jsonl(RAW_MESSAGES_PATH, {"receive_time": receive_time, "raw_text": raw_text})
    except Exception as exc:
        log_error("write_raw_failed", exc)
        print(f"[ERROR] write raw failed: {exc}", flush=True)

    try:
        data = json.loads(raw_text)
    except Exception as exc:
        if WRITE_NON_JSON_DEBUG_LOG:
            try:
                append_text(NON_JSON_PATH, f"{receive_time}\t{type(exc).__name__}: {exc}\tlength={len(raw_text)}")
            except Exception as write_exc:
                log_error("write_non_json_failed", write_exc)
                print(f"[ERROR] write non-json failed: {write_exc}", flush=True)
        log_error("json_parse_failed", exc, raw_text=raw_text[:1000])
        print(f"[MESSAGE] length={len(raw_text)} schema=non_json kind=unknown count={message_count}", flush=True)
        save_if_needed()
        return

    try:
        if WRITE_SCHEMA_DEBUG_LOGS:
            handle_json_message(receive_time, data, raw_text)
        try:
            handle_realtime_filter(receive_time, data, raw_text)
        except Exception as filter_exc:
            log_error("realtime_filter_failed", filter_exc, raw_text=raw_text[:1000])
            print(f"[ERROR] macro filter failed: {filter_exc}", flush=True)
        save_if_needed()
    except Exception as exc:
        log_error("handle_message_failed", exc, raw_text=raw_text[:1000])
        print(f"[ERROR] handle message failed: {exc}", flush=True)


def on_error(ws: WebSocketApp, error: Any) -> None:
    log_error("websocket_error", None, error=str(error))
    print(f"[ERROR] websocket: {error}", flush=True)


def on_close(ws: WebSocketApp, close_status_code: Any, close_msg: Any) -> None:
    log_error("websocket_closed", None, close_status_code=close_status_code, close_msg=close_msg)
    print(f"[CLOSE] code={close_status_code} msg={close_msg}", flush=True)


def request_stop(signum: int | None = None, frame: Any | None = None) -> None:
    global stop_requested
    stop_requested = True
    print("[STOP] graceful shutdown requested", flush=True)
    if active_ws is not None:
        try:
            active_ws.close()
        except Exception as exc:
            log_error("websocket_close_failed", exc)
            print(f"[ERROR] close failed: {exc}", flush=True)


def load_ws_url() -> str:
    load_dotenv(BASE_DIR / ".env")
    ws_url = os.getenv("JIN10_WS_URL", "").strip()
    if not ws_url:
        raise RuntimeError("JIN10_WS_URL is missing in .env")
    return ws_url


def run() -> int:
    global active_ws, last_save_time

    try:
        from websocket import WebSocketApp
    except ImportError as exc:
        print(f"[ERROR] missing dependency: {exc}. Install with `pip install -r requirements.txt`.", flush=True)
        return 1

    ensure_log_dir()
    last_save_time = time.monotonic()
    load_seen_news_ids()
    load_dedup_cache()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    try:
        ws_url = load_ws_url()
    except Exception as exc:
        log_error("config_load_failed", exc)
        print(f"[ERROR] config: {exc}", flush=True)
        return 1

    print(f"[START] url={mask_ws_url(ws_url)}", flush=True)

    reconnect_delay = 3
    while not stop_requested:
        active_ws = WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        try:
            active_ws.run_forever(ping_interval=20, ping_timeout=10)
        except KeyboardInterrupt:
            request_stop()
            break
        except Exception as exc:
            log_error("run_forever_failed", exc)
            print(f"[ERROR] run_forever failed: {exc}", flush=True)
        finally:
            active_ws = None
            save_if_needed(force=True)

        if stop_requested:
            break

        print(f"[RECONNECT] sleeping={reconnect_delay}s", flush=True)
        time.sleep(reconnect_delay)
        reconnect_delay = min(reconnect_delay * 2, 60)

    save_if_needed(force=True)
    print("[EXIT] schema files saved", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(run())
