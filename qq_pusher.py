from __future__ import annotations

import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import config
from push_queue import append_jsonl_flush, consume_queue_incrementally, load_sent_queue_ids, now_local_iso, write_offset


def _build_onebot_request(api_url: str, payload: dict[str, Any]) -> urllib.request.Request:
    url = api_url
    headers = {"Content-Type": "application/json"}
    if config.QQ_ACCESS_TOKEN and config.QQ_ACCESS_TOKEN_MODE == "header":
        headers["Authorization"] = f"Bearer {config.QQ_ACCESS_TOKEN}"
    elif config.QQ_ACCESS_TOKEN and config.QQ_ACCESS_TOKEN_MODE == "query":
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urllib.parse.urlencode({'access_token': config.QQ_ACCESS_TOKEN})}"

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return urllib.request.Request(url, data=body, headers=headers, method="POST")


def post_onebot(api_url: str, payload: dict[str, Any]) -> tuple[int, str]:
    request = _build_onebot_request(api_url, payload)
    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read(2000).decode("utf-8", errors="replace")
        return response.status, body


def send_to_qq_group(text: str) -> bool:
    """
    Encapsulates the actual QQ group send operation.
    Current implementation supports OneBot-compatible HTTP POST.
    """
    if not config.QQ_PUSH_ENABLED:
        print("[QQ_DISABLED] QQ_PUSH_ENABLED=False; not sending.", flush=True)
        return False

    try:
        status, body = post_onebot(config.QQ_BOT_API_URL, {"group_id": config.QQ_GROUP_ID, "message": text})
    except Exception as exc:
        print(f"send_test=failed error={type(exc).__name__}: {exc}", flush=True)
        return 1
    if not 200 <= status < 300:
        return False
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return True
    return payload.get("retcode") in (0, None)


def write_sent(item: dict[str, Any]) -> None:
    append_jsonl_flush(
        config.QQ_SENT_LOG_PATH,
        {
            "queue_id": item.get("queue_id"),
            "news_id": item.get("news_id"),
            "reason_type": item.get("reason_type"),
            "score": item.get("score"),
            "sent_at": now_local_iso(),
            "status": "sent",
        },
    )


def write_failed(item: dict[str, Any], error: str) -> None:
    append_jsonl_flush(
        config.QQ_FAILED_LOG_PATH,
        {
            "queue_id": item.get("queue_id"),
            "news_id": item.get("news_id"),
            "reason_type": item.get("reason_type"),
            "score": item.get("score"),
            "failed_at": now_local_iso(),
            "status": "failed",
            "error": error,
        },
    )


def format_preview(item: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"queue_id={item.get('queue_id')}",
            f"reason_type={item.get('reason_type')} score={item.get('score')}",
            str(item.get("push_text") or ""),
        ]
    )


def make_handler(dry_run: bool, sent_ids: set[str]):
    def handle(item: dict[str, Any]) -> bool:
        queue_id = str(item.get("queue_id") or "").strip()
        if not queue_id:
            write_failed(item, "missing queue_id")
            return False

        if item.get("status") != "pending":
            return True

        if queue_id in sent_ids:
            print(f"[SKIP_SENT] queue_id={queue_id}", flush=True)
            return True

        if dry_run:
            print("[DRY_RUN]\n" + format_preview(item), flush=True)
            return True

        text = str(item.get("push_text") or "").strip()
        if not text:
            write_failed(item, "empty push_text")
            return False

        try:
            if not send_to_qq_group(text):
                write_failed(item, "send_to_qq_group returned false")
                return False
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            write_failed(item, f"{type(exc).__name__}: {exc}")
            return False

        write_sent(item)
        sent_ids.add(queue_id)
        print(f"[SENT] queue_id={queue_id}", flush=True)
        time.sleep(random.uniform(1, 3))
        return True

    return handle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Consume Jin10 push queue and send QQ group messages.")
    parser.add_argument("--dry-run", action="store_true", help="Print pending messages without sending QQ.")
    parser.add_argument("--once", action="store_true", help="Scan the queue once and exit.")
    parser.add_argument("--loop", action="store_true", help="Continuously scan the queue.")
    parser.add_argument("--interval", type=float, default=3.0, help="Loop scan interval in seconds.")
    parser.add_argument(
        "--advance-offset",
        action="store_true",
        help="In dry-run mode, advance the real push_queue.offset instead of the dry-run offset.",
    )
    parser.add_argument("--test-api", action="store_true", help="Probe OneBot status APIs without sending messages.")
    parser.add_argument("--send-test", help="Send exactly one test message and exit without touching queue logs.")
    return parser.parse_args()


def api_base_url() -> str:
    return config.QQ_BOT_API_URL.rsplit("/", 1)[0]


def summarize_body(body: str) -> str:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return body[:500]
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict):
        for key in ("user_id", "self_id", "uin", "qq"):
            if key in data:
                value = str(data[key])
                data[key] = value[:3] + "***" + value[-2:] if len(value) > 5 else "***"
    return json.dumps(payload, ensure_ascii=False)[:500]


def test_api() -> int:
    base_url = api_base_url()
    print(f"base_url={base_url}", flush=True)
    ok_count = 0
    for endpoint in ("get_status", "get_login_info", "get_version_info"):
        api_url = f"{base_url}/{endpoint}"
        try:
            status, body = post_onebot(api_url, {})
        except Exception as exc:
            print(f"{endpoint}: failed error={type(exc).__name__}: {exc}", flush=True)
            continue
        ok_count += 1
        print(f"{endpoint}: ok status={status} body={summarize_body(body)}", flush=True)
    return 0 if ok_count else 1


def send_test_message(text: str) -> int:
    if not config.QQ_PUSH_ENABLED:
        print("send_test=blocked reason=QQ_PUSH_ENABLED_FALSE", flush=True)
        return 1
    if not str(config.QQ_GROUP_ID).strip():
        print("send_test=blocked reason=QQ_GROUP_ID_EMPTY", flush=True)
        return 1

    status, body = post_onebot(config.QQ_BOT_API_URL, {"group_id": config.QQ_GROUP_ID, "message": text})
    print(f"send_test_http_status={status}", flush=True)
    print(f"send_test_response={summarize_body(body)}", flush=True)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return 0 if 200 <= status < 300 else 1
    return 0 if payload.get("retcode") == 0 else 1


def main() -> int:
    args = parse_args()
    if args.test_api:
        return test_api()
    if args.send_test is not None:
        return send_test_message(args.send_test)

    loop = args.loop
    once = args.once or not loop
    offset_path = config.PUSH_QUEUE_OFFSET_PATH
    if args.dry_run and not args.advance_offset:
        offset_path = config.PUSH_QUEUE_DRY_RUN_OFFSET_PATH

    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    config.PUSH_QUEUE_PATH.touch(exist_ok=True)
    if not offset_path.exists():
        write_offset(offset_path, 0)

    sent_ids = load_sent_queue_ids(config.QQ_SENT_LOG_PATH)
    handler = make_handler(args.dry_run, sent_ids)

    while True:
        processed = consume_queue_incrementally(config.PUSH_QUEUE_PATH, offset_path, handler)
        print(f"[QUEUE_SCAN] processed={processed} offset_path={offset_path}", flush=True)
        if once:
            return 0
        time.sleep(max(args.interval, 1.0))


if __name__ == "__main__":
    sys.exit(main())
