# Jin10 WebSocket Macro Filter

## Project Structure

- `probe.py`: connects to Jin10 WebSocket, records raw messages, runs filtering, and appends push candidates to the queue.
- `news_filter.py`: keyword lists, scoring rules, `score_news()`, `should_push()`, and text extraction.
- `push_queue.py`: JSONL queue writer and offset-based incremental consumer.
- `qq_pusher.py`: independent QQ group push worker.
- `config.py`: paths and QQ HTTP API configuration.
- `logs/raw_messages.log`: all raw Jin10 messages.
- `logs/pushed_news.log`: messages the filter decided should be pushed.
- `logs/skipped_news.log`: messages skipped by the filter, with reasons.
- `logs/push_queue.jsonl`: pending QQ push queue.
- `logs/push_queue.offset`: real QQ worker byte offset.
- `logs/qq_sent.log`: QQ messages successfully sent.
- `logs/qq_failed.log`: QQ send failures.

## Data Flow

Jin10 WebSocket -> `probe.py` -> `news_filter.py` -> `logs/push_queue.jsonl` -> `qq_pusher.py` -> QQ group.

`pushed_news.log` means the filter matched the message. It does not mean QQ delivery succeeded. QQ delivery status is recorded in `qq_sent.log` and `qq_failed.log`.

## Run the News Receiver

Copy `.env.example` to `.env`, configure `JIN10_WS_URL`, then run:

```bash
python3 probe.py
```

## Run the QQ Pusher

Preview queued messages without sending QQ:

```bash
python3 qq_pusher.py --dry-run --once
```

Run continuously:

```bash
python3 qq_pusher.py --loop --interval 3
```

Dry-run uses `logs/push_queue.dry_run.offset` by default so it does not advance the real `logs/push_queue.offset`. To test the real offset deliberately:

```bash
python3 qq_pusher.py --dry-run --once --advance-offset
```

## Enable Real QQ Push

Set the deployment values in `.env`:

```bash
QQ_PUSH_ENABLED=true
QQ_BOT_API_URL=http://127.0.0.1:3000/send_group_msg
QQ_GROUP_ID=your_group_id
QQ_ACCESS_TOKEN=
QQ_ACCESS_TOKEN_MODE=none
```

Do not commit real access tokens, QQ group IDs, WebSocket URLs, or proxy credentials.

## Modify News Filtering Rules

Only edit `news_filter.py` when optimizing keywords, scoring, or skip rules. `probe.py` should remain focused on receiving messages and appending queue items. `qq_pusher.py` should not import or call the news filter.

## Queue Offset Troubleshooting

`qq_pusher.py` reads `push_queue.jsonl` from the byte position stored in `push_queue.offset`. If the queue file is truncated or rotated and the offset is larger than the file size, the consumer resets the offset to `0`.

To replay from the beginning, stop `qq_pusher.py` and set:

```bash
printf '0\n' > logs/push_queue.offset
```

Dry-run offset is separate:

```bash
printf '0\n' > logs/push_queue.dry_run.offset
```

## Network and Proxy Notes

The server already has a global proxy. Do not install or reconfigure proxy clients for this project. If dependency downloads fail, first inspect the command error output and basic network reachability. Do not write proxy subscription links, access tokens, or node information into code, logs, or this README.
