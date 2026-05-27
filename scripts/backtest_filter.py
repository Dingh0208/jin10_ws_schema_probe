from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
from news_filter import evaluate_news, is_push_candidate, message_id
from probe import build_dedup_hash


def load_raw_messages(path: Path) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    if not path.exists():
        return messages
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            wrapper = json.loads(line)
            raw_text = wrapper.get("raw_text") if isinstance(wrapper, dict) else None
            msg = json.loads(raw_text) if isinstance(raw_text, str) else wrapper
        except Exception:
            continue
        if isinstance(msg, dict):
            messages.append(msg)
    return messages


def load_raw_messages_from_paths(paths: list[Path]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        for msg in load_raw_messages(path):
            key = json.dumps(
                {
                    "id": msg.get("id"),
                    "time": msg.get("time"),
                    "type": msg.get("type"),
                    "event": msg.get("event"),
                    "data": msg.get("data"),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            if key in seen:
                continue
            seen.add(key)
            messages.append(msg)
    return messages


def load_old_sent_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    if not path.exists():
        return ids
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            item = json.loads(line)
        except Exception:
            continue
        for key in ("news_id", "dedup_hash", "queue_id"):
            value = str(item.get(key) or "").strip()
            if value:
                ids.add(value)
    return ids


def sample_lines(items: list[dict[str, Any]], limit: int = 8) -> str:
    lines = []
    for item in items[:limit]:
        text = str(item.get("text") or "").replace("\n", " ")[:220]
        lines.append(
            f"- `{item.get('time')}` `{item.get('hit_type')}` score={item.get('final_score')} "
            f"keywords={item.get('matched_keywords')} text={text}"
        )
    return "\n".join(lines) if lines else "- 无"


def main() -> int:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    messages = load_raw_messages_from_paths([config.RAW_MESSAGES_LOG_PATH, config.RAW_MESSAGES_PATH])
    old_sent_ids = load_old_sent_ids(config.QQ_SENT_LOG_PATH)

    total_candidates = 0
    pushes: list[dict[str, Any]] = []
    filtered_noise: list[dict[str, Any]] = []
    old_pushed_new_skip: list[dict[str, Any]] = []
    new_push_old_not_sent: list[dict[str, Any]] = []
    counter: Counter[str] = Counter()
    tier_counter: Counter[str] = Counter()

    seen_hashes: set[str] = set()
    for msg in messages:
        if not is_push_candidate(msg):
            continue
        total_candidates += 1
        evaluation = evaluate_news(msg)
        text = str(evaluation.get("all_text") or "")
        dedup_hash = build_dedup_hash(msg, text)
        news_id = message_id(msg)
        if evaluation["noise_score"] > 0 and evaluation["decision"] != "push":
            filtered_noise.append(evaluation)
        old_was_sent = bool((news_id and news_id in old_sent_ids) or dedup_hash in old_sent_ids or any(str(item).startswith(news_id) for item in old_sent_ids if news_id))
        if evaluation["decision"] == "push" and dedup_hash not in seen_hashes:
            seen_hashes.add(dedup_hash)
            pushes.append(evaluation)
            counter[str(evaluation["hit_type"])] += 1
            tier_counter[str(evaluation.get("impact_tier") or "unknown")] += 1
            if not old_was_sent:
                new_push_old_not_sent.append(evaluation)
        elif old_was_sent:
            old_pushed_new_skip.append(evaluation)

    push_ratio = (len(pushes) / total_candidates * 100) if total_candidates else 0.0
    hit_type_lines = "\n".join(f"- {name}：{count}" for name, count in sorted(counter.items())) or "- 无"
    tier_lines = "\n".join(f"- {name}：{count}" for name, count in sorted(tier_counter.items())) or "- 无"
    report = f"""# Filter Backtest Report

## Rule Summary

新算法使用加密市场影响优先的分层评分：`final_score = crypto_score + macro_score + market_score + risk_score + policy_score - noise_score`。

- `direct_crypto_hit`：BTC/ETH/比特币/以太坊/交易所/稳定币/现货 ETF/链上等直接加密命中。
- `macro_market_hit` / `us_economy_hit`：只保留 CPI/PCE/非农/FOMC/降息加息/美元美债/流动性等高影响美国宏观，普通宏观默认过滤。
- `us_iran_war_hit`：美伊/中东战争开启或停止、袭击、导弹、制裁、停火、霍尔木兹/油轮航运风险。
- `systemic_risk_hit`：美国/美元/稳定币相关金融风险、银行危机、流动性危机、稳定币脱锚等。
- `geopolitical_market_hit`：其他地缘风险事件，且出现黄金/原油/美元/美股/风险资产/避险等市场影响。
- `trump_hit`：特朗普相关新闻。
- `pure_noise`：普通公司、财报、外交表态、广告、摘要和无市场影响内容。

当前建议阈值：`{config.PUSH_SCORE_THRESHOLD if hasattr(config, 'PUSH_SCORE_THRESHOLD') else 7}`。

## Statistics

- 总候选新闻数：{total_candidates}
- 新算法会推送：{len(pushes)}
- 推送比例：{push_ratio:.2f}%
- 按 hit_type 统计：
{hit_type_lines}
- 按 impact_tier 统计：
{tier_lines}
- 被 noise_score 过滤数量：{len(filtered_noise)}
- 相比旧 `qq_sent.log`，新增会推送：{len(new_push_old_not_sent)}
- 旧推送但新算法不会推：{len(old_pushed_new_skip)}

## Example Hits

{sample_lines(pushes)}

## Example Filtered Noise

{sample_lines(filtered_noise)}

## Newly Pushed Compared With Old Logs

{sample_lines(new_push_old_not_sent)}

## Old Pushed But New Algorithm Skips

{sample_lines(old_pushed_new_skip)}

## Possible False Positives

{sample_lines([item for item in pushes if item.get('noise_score', 0) > 0])}

## Possible False Negatives

- 需要人工复核 `raw_messages.log` 中未命中但包含弱宏观/弱地缘词的新闻。
- 当前策略偏保守，普通市场波动、普通非美国央行利率新闻默认过滤。

## Threshold Recommendation

- 当前阈值 7 比较保守，适合减少 QQ 群误报。
- 如果后续漏报 BTC/ETH 生态新闻，可优先补充 `CRYPTO_STRONG_KEYWORDS`，不建议直接降低阈值。
"""
    report_path = config.LOG_DIR / "filter_backtest_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"report_path={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
