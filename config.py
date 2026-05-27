from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args: object, **kwargs: object) -> bool:
        return False


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

RAW_MESSAGES_PATH = LOG_DIR / "raw_messages.jsonl"
NON_JSON_PATH = LOG_DIR / "non_json_messages.log"
SCHEMA_STATS_PATH = LOG_DIR / "schema_stats.json"
SCHEMA_SAMPLES_PATH = LOG_DIR / "schema_samples.json"
RAW_MESSAGES_LOG_PATH = LOG_DIR / "raw_messages.log"
FILTER_HITS_LOG_PATH = LOG_DIR / "filter_hits.log"
PUSHED_NEWS_PATH = LOG_DIR / "pushed_news.log"
SKIPPED_NEWS_PATH = LOG_DIR / "skipped_news.log"
SEEN_NEWS_IDS_PATH = LOG_DIR / "seen_news_ids.txt"
ERRORS_LOG_PATH = LOG_DIR / "errors.log"
DEDUP_CACHE_PATH = DATA_DIR / "dedup_cache.json"
DEDUP_TTL_SECONDS = 24 * 60 * 60
PUSH_SCORE_THRESHOLD = 7

PUSH_QUEUE_PATH = LOG_DIR / "push_queue.jsonl"
PUSH_QUEUE_OFFSET_PATH = LOG_DIR / "push_queue.offset"
PUSH_QUEUE_DRY_RUN_OFFSET_PATH = LOG_DIR / "push_queue.dry_run.offset"
QQ_SENT_LOG_PATH = LOG_DIR / "qq_sent.log"
QQ_FAILED_LOG_PATH = LOG_DIR / "qq_failed.log"

QQ_PUSH_ENABLED = os.getenv("QQ_PUSH_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
QQ_BOT_API_URL = os.getenv("QQ_BOT_API_URL", "http://127.0.0.1:3000/send_group_msg")
QQ_GROUP_ID = os.getenv("QQ_GROUP_ID", "")
QQ_ACCESS_TOKEN = os.getenv("QQ_ACCESS_TOKEN", "")
QQ_ACCESS_TOKEN_MODE = os.getenv("QQ_ACCESS_TOKEN_MODE", "none")  # none / header / query

WRITE_LEGACY_RAW_JSONL = False
WRITE_SCHEMA_DEBUG_LOGS = False
WRITE_NON_JSON_DEBUG_LOG = False

FILTER_KEYWORDS = [
    "BTC",
    "ETH",
    "比特币",
    "以太坊",
    "加密货币",
    "数字资产",
    "稳定币",
    "USDT",
    "USDC",
    "CFTC",
    "Coinbase",
    "Binance",
    "币安",
    "OKX",
    "链上",
    "爆仓",
    "清算",
    "CPI",
    "PCE",
    "核心CPI",
    "核心PCE",
    "非农",
    "NFP",
    "ADP",
    "FOMC",
    "美联储",
    "美联储观察",
    "鲍威尔",
    "降息",
    "加息",
    "通胀",
    "利率决议",
    "ETF",
    "SEC",
    "战争",
    "地缘",
    "霍尔木兹",
    "红海",
    "油轮",
    "商船",
    "导弹",
    "空袭",
    "袭击",
    "停火",
    "制裁",
    "伊朗",
    "以色列",
    "俄罗斯",
    "乌克兰",
    "特朗普",
    "关税",
]
