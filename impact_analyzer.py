from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from config import LOG_DIR
except ImportError:  # pragma: no cover - allows standalone script execution.
    LOG_DIR = Path(__file__).resolve().parent / "logs"


ASSETS = ("BTC", "原油", "黄金", "美股")
IMPACT_ANALYSIS_LOG_PATH = LOG_DIR / "impact_analysis.log"
MAX_QQ_MESSAGE_CHARS = 1200


@dataclass(frozen=True)
class Signal:
    score: int
    reason: str
    any_of: tuple[str, ...] = ()
    all_of: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()


def analyze_market_impact(text: str, evaluation: dict | None = None) -> dict:
    """
    Rule-based impact judgment for the assets used in QQ pushes.

    The function intentionally has no network, external API, or model dependency.
    Scores are clipped to the -3..+3 range and mapped to Chinese directions.
    """
    combined_text = _build_combined_text(text, evaluation)
    normalized = _normalize(combined_text)
    context = _detect_context(normalized, evaluation)

    result: dict[str, dict[str, Any]] = {}
    for asset in ASSETS:
        hits = _match_asset_signals(asset, normalized)
        result[asset] = _summarize_asset(asset, hits, normalized, context)
    return result


def format_impact_for_qq(impact: dict) -> str:
    lines = ["——", "【市场影响判断】"]
    for asset in ASSETS:
        item = impact.get(asset) or {}
        direction = str(item.get("direction") or "不确定")
        confidence = str(item.get("confidence") or "低")
        reason = _limit_reason(str(item.get("reason") or "证据不足，方向不明"))
        lines.append(f"{asset}：{direction}（{confidence}）｜{reason}")
    return "\n".join(lines)


def append_impact_to_push_text(push_text: str, impact_text: str, max_chars: int = MAX_QQ_MESSAGE_CHARS) -> str:
    base_text = push_text.strip()
    suffix = impact_text.strip()
    combined = f"{base_text}\n\n{suffix}" if base_text else suffix
    if len(combined) <= max_chars:
        return combined

    separator_len = 2 if base_text and suffix else 0
    allowed_base_len = max(0, max_chars - len(suffix) - separator_len)
    shortened = _truncate_content_line(base_text, allowed_base_len)
    combined = f"{shortened}\n\n{suffix}" if shortened else suffix
    if len(combined) <= max_chars:
        return combined

    shortened = _hard_truncate(shortened, allowed_base_len)
    return f"{shortened}\n\n{suffix}" if shortened else suffix


def log_impact_analysis(text: str, impact: dict, evaluation: dict | None = None) -> None:
    IMPACT_ANALYSIS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "time": _now_iso(),
        "text": text,
        "impact": impact,
        "evaluation": evaluation or {},
    }
    with IMPACT_ANALYSIS_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        file.flush()


SIGNALS: dict[str, tuple[Signal, ...]] = {
    "BTC": (
        Signal(2, "降息预期升温支撑风险资产", any_of=("降息预期升温", "提前降息", "押注美联储提前降息", "美联储提前降息")),
        Signal(2, "通胀低于预期提振风险偏好", any_of=("通胀低于预期", "cpi低于预期", "pce低于预期")),
        Signal(2, "美债收益率下行利好流动性", any_of=("美债收益率下行", "美债收益率下降", "美债收益率回落", "美债收益率走低")),
        Signal(1, "美元走弱利好BTC", any_of=("美元走弱", "美元下跌", "美元回落", "美元走低")),
        Signal(2, "ETF获批改善加密情绪", any_of=("etf获批", "etf批准", "现货etf获批", "现货etf上市"), all_of=("etf",)),
        Signal(2, "ETF获批改善加密情绪", all_of=("sec", "etf", "批准")),
        Signal(2, "机构买入提振需求预期", any_of=("机构买入", "机构增持", "买入比特币", "增持btc")),
        Signal(1, "监管积极信号改善情绪", any_of=("sec释放积极信号", "监管积极信号")),
        Signal(4, "全面停火缓和地缘风险，利好BTC", any_of=("全面停火", "停火60天", "所有战线"), all_of=("美伊",), blockers=("违反停火", "停火破裂", "未达成", "破裂")),
        Signal(2, "停火缓和地缘风险，风险资产修复", any_of=("停火协议", "停火", "和谈", "地缘风险缓和", "地缘局势缓和"), all_of=("伊朗",), blockers=("全面停火", "停火60天", "所有战线", "违反停火", "停火破裂", "未达成", "破裂")),
        Signal(1, "风险偏好升温支撑BTC", any_of=("风险偏好升温", "风险资产上涨", "纳指上涨", "纳斯达克上涨")),
        Signal(1, "宽松预期改善流动性", any_of=("宽松", "流动性增加", "流动性宽松"), blockers=("降息推迟", "降息预期下降", "降息预期降温", "不急于降息")),
        Signal(1, "非农偏弱推升降息预期", any_of=("非农弱于预期", "就业弱于预期")),
        Signal(-2, "加息预期压制风险资产", any_of=("加息", "加息预期升温")),
        Signal(-2, "降息推迟压制风险偏好", any_of=("降息推迟", "推迟降息", "不急于降息", "降息预期下降", "降息预期降温", "降息预期回落")),
        Signal(-2, "CPI高于预期压制BTC", any_of=("通胀高于预期", "cpi高于预期", "pce高于预期")),
        Signal(-1, "非农强劲削弱降息预期", any_of=("非农强于预期", "就业强于预期")),
        Signal(-2, "美债收益率上行压制流动性", any_of=("美债收益率上行", "美债收益率上升", "美债收益率上涨", "美债收益率走高")),
        Signal(-1, "美元走强压制BTC", any_of=("美元走强", "美元上涨", "美元指数走强", "美元指数上涨")),
        Signal(-2, "SEC执法打压加密情绪", any_of=("sec执法", "sec起诉", "监管执法")),
        Signal(-2, "交易所调查打压加密情绪", any_of=("交易所被调查", "币安被调查", "coinbase被调查")),
        Signal(-2, "ETF受阻打压加密情绪", any_of=("etf推迟", "etf延期", "etf拒绝", "拒绝etf", "推迟etf")),
        Signal(-1, "风险资产下跌拖累BTC", any_of=("风险资产下跌", "纳指跳水", "纳指期货跳水", "纳斯达克跳水", "纳指下跌")),
        Signal(-1, "流动性收紧压制BTC", any_of=("流动性收紧", "流动性趋紧")),
        Signal(-1, "避险升温使风险资产承压", any_of=("避险升温", "避险情绪升温", "市场恐慌")),
        Signal(-1, "地缘风险压制风险资产", any_of=("袭击", "报复", "导弹", "空袭", "冲突升级"), all_of=("伊朗", "以色列")),
    ),
    "原油": (
        Signal(2, "中东冲突推升供应风险", any_of=("中东冲突升级", "伊朗以色列冲突升级")),
        Signal(2, "中东冲突推升供应风险", any_of=("袭击", "报复", "导弹", "空袭", "冲突升级"), all_of=("伊朗", "以色列")),
        Signal(2, "供应受限支撑油价", any_of=("俄罗斯供应受限", "供应受限", "制裁导致供应减少", "供应减少")),
        Signal(2, "OPEC减产支撑油价", any_of=("opec减产", "opec+减产", "延长减产", "宣布减产")),
        Signal(2, "原油库存下降支撑油价", any_of=("原油库存下降", "原油库存减少", "库存下降", "库存减少"), all_of=("原油",)),
        Signal(2, "霍尔木兹风险威胁供应", any_of=("霍尔木兹海峡风险", "霍尔木兹风险", "霍尔木兹海峡")),
        Signal(1, "地缘风险升温支撑油价", any_of=("地缘风险升温", "地缘冲突", "战争升级")),
        Signal(1, "需求强于预期支撑油价", any_of=("需求强于预期", "需求改善")),
        Signal(1, "油价拉升确认利多", any_of=("原油拉升", "油价上涨", "油价拉升", "国际油价上涨", "原油和黄金拉升")),
        Signal(-2, "停火和谈缓和供应风险", any_of=("停火", "和谈", "停火协议"), blockers=("破裂", "未达成")),
        Signal(-2, "OPEC增产压制油价", any_of=("opec增产", "opec+增产", "宣布增产")),
        Signal(-2, "原油库存增加压制油价", any_of=("原油库存增加", "原油库存上升", "库存增加", "库存上升"), all_of=("原油",)),
        Signal(-2, "需求疲软压制油价", any_of=("需求疲软", "需求下降", "中国需求下降")),
        Signal(-1, "衰退预期削弱原油需求", any_of=("经济衰退预期", "衰退风险", "衰退担忧")),
        Signal(-2, "供应恢复压制油价", any_of=("供应恢复", "产量恢复")),
        Signal(-2, "地缘风险缓和压制油价", any_of=("地缘风险缓和", "地缘局势缓和")),
        Signal(-1, "油价下跌确认利空", any_of=("原油下跌", "油价下跌", "国际油价下跌")),
    ),
    "黄金": (
        Signal(2, "避险升温支撑黄金", any_of=("避险升温", "避险情绪升温", "市场恐慌")),
        Signal(2, "地缘冲突支撑黄金避险", any_of=("战争升级", "地缘冲突", "地缘风险升温", "冲突升级")),
        Signal(2, "地缘冲突支撑黄金避险", any_of=("袭击", "报复", "导弹", "空袭", "冲突升级"), all_of=("伊朗", "以色列")),
        Signal(2, "美债收益率下行利好黄金", any_of=("美债收益率下行", "美债收益率下降", "美债收益率回落", "美债收益率走低")),
        Signal(1, "美元走弱支撑黄金", any_of=("美元走弱", "美元下跌", "美元回落", "美元走低")),
        Signal(2, "降息预期升温支撑黄金", any_of=("降息预期升温", "提前降息", "押注美联储提前降息", "美联储提前降息")),
        Signal(2, "金融风险提升避险需求", any_of=("金融风险", "银行危机", "系统性风险")),
        Signal(1, "通胀担忧支撑黄金", any_of=("通胀担忧", "通胀压力")),
        Signal(1, "黄金拉升确认利多", any_of=("黄金拉升", "金价上涨", "黄金上涨", "原油和黄金拉升")),
        Signal(1, "非农偏弱推升降息预期", any_of=("非农弱于预期", "就业弱于预期")),
        Signal(-2, "美债收益率上行压制黄金", any_of=("美债收益率上行", "美债收益率上升", "美债收益率上涨", "美债收益率走高")),
        Signal(-1, "美元走强压制黄金", any_of=("美元走强", "美元上涨", "美元指数走强", "美元指数上涨")),
        Signal(-2, "加息预期升温压制黄金", any_of=("加息预期升温", "加息")),
        Signal(-2, "降息预期下降压制黄金", any_of=("降息预期下降", "降息预期降温", "降息推迟", "推迟降息", "不急于降息")),
        Signal(-1, "风险偏好升温削弱避险", any_of=("风险偏好升温", "股市大涨", "纳指上涨", "纳斯达克上涨")),
        Signal(-2, "避险降温压制黄金", any_of=("避险降温", "停火", "和谈"), blockers=("破裂", "未达成")),
        Signal(-1, "黄金下跌确认利空", any_of=("黄金下跌", "金价下跌")),
    ),
    "美股": (
        Signal(2, "降息预期升温提振估值", any_of=("降息预期升温", "提前降息", "押注美联储提前降息", "美联储提前降息")),
        Signal(2, "CPI低于预期利好估值", any_of=("cpi低于预期", "通胀低于预期")),
        Signal(2, "PCE低于预期利好估值", any_of=("pce低于预期",)),
        Signal(1, "非农偏弱推升降息预期", any_of=("非农弱于预期", "就业弱于预期"), blockers=("衰退", "恐慌")),
        Signal(2, "美债收益率下行利好估值", any_of=("美债收益率下行", "美债收益率下降", "美债收益率回落", "美债收益率走低")),
        Signal(1, "流动性宽松提振美股", any_of=("流动性宽松", "流动性增加", "宽松")),
        Signal(2, "科技股利好提振美股", any_of=("科技股利好", "ai需求强劲", "芯片股利好")),
        Signal(1, "风险偏好升温利好美股", any_of=("风险偏好升温", "纳指上涨", "纳斯达克上涨", "风险资产上涨")),
        Signal(1, "贸易缓和改善风险偏好", any_of=("贸易缓和", "关税缓和")),
        Signal(1, "地缘风险缓和利好美股", any_of=("地缘风险缓和", "地缘局势缓和", "停火", "和谈"), blockers=("破裂", "未达成")),
        Signal(-2, "CPI高于预期压制估值", any_of=("cpi高于预期", "通胀高于预期")),
        Signal(-2, "PCE高于预期压制估值", any_of=("pce高于预期",)),
        Signal(-2, "非农强劲削弱降息预期", any_of=("非农强于预期", "就业强于预期")),
        Signal(-2, "加息预期升温压制估值", any_of=("加息预期升温", "加息")),
        Signal(-2, "美债收益率上行压制估值", any_of=("美债收益率上行", "美债收益率上升", "美债收益率上涨", "美债收益率走高")),
        Signal(-1, "美元走强压制风险资产", any_of=("美元走强", "美元上涨", "美元指数走强", "美元指数上涨")),
        Signal(-1, "地缘冲突压制风险偏好", any_of=("地缘冲突升级", "战争升级", "地缘风险升温")),
        Signal(-1, "地缘冲突压制风险偏好", any_of=("袭击", "报复", "导弹", "空袭", "冲突升级"), all_of=("伊朗", "以色列")),
        Signal(-1, "油价上涨加大通胀压力", any_of=("原油大涨", "原油拉升", "油价上涨", "油价拉升", "国际油价上涨", "原油和黄金拉升")),
        Signal(-2, "衰退风险压制美股", any_of=("衰退风险", "经济衰退预期", "衰退担忧")),
        Signal(-2, "金融风险压制美股", any_of=("金融风险", "银行危机", "系统性风险")),
        Signal(-1, "科技股监管风险压制估值", any_of=("科技股监管风险", "反垄断调查", "监管风险")),
        Signal(-2, "纳指跳水显示风险偏好转弱", any_of=("纳指跳水", "纳指期货跳水", "纳斯达克跳水")),
    ),
}


def _build_combined_text(text: str, evaluation: dict | None) -> str:
    parts = [text or ""]
    if isinstance(evaluation, dict):
        eval_text = evaluation.get("text")
        if eval_text:
            parts.append(str(eval_text))
        keywords = evaluation.get("matched_keywords") or []
        if isinstance(keywords, list):
            parts.append(" ".join(str(item) for item in keywords))
    return " ".join(part for part in parts if part)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text.casefold())


def _detect_context(normalized: str, evaluation: dict | None) -> dict[str, bool]:
    hit_type = str(evaluation.get("hit_type") or "") if isinstance(evaluation, dict) else ""
    has_crypto = _has_any(
        normalized,
        ("btc", "比特币", "eth", "以太坊", "加密货币", "数字资产", "现货etf", "coinbase", "binance", "币安"),
    ) or hit_type == "direct_crypto_hit"
    has_oil = _has_any(normalized, ("原油", "石油", "油价", "opec", "霍尔木兹"))
    has_gold = _has_any(normalized, ("黄金", "金价", "避险"))
    has_macro = _has_any(normalized, ("cpi", "pce", "非农", "美联储", "降息", "加息", "通胀", "美债", "美元")) or hit_type in {
        "macro_market_hit",
        "us_economy_hit",
    }
    has_geo = _has_any(normalized, ("伊朗", "以色列", "中东", "战争", "地缘", "袭击", "导弹", "空袭", "霍尔木兹")) or hit_type == "us_iran_war_hit"
    has_stock = _has_any(normalized, ("美股", "纳指", "纳斯达克", "标普", "道指", "科技股"))
    return {
        "crypto": has_crypto,
        "oil": has_oil,
        "gold": has_gold,
        "macro": has_macro,
        "geo": has_geo,
        "stock": has_stock,
        "pure_crypto": has_crypto and not (has_oil or has_gold or has_macro or has_geo or has_stock),
        "pure_geo": has_geo and not (has_crypto or has_macro),
    }


def _match_asset_signals(asset: str, normalized: str) -> list[Signal]:
    hits = []
    for signal in SIGNALS[asset]:
        if _matches_signal(normalized, signal):
            hits.append(signal)
    return hits


def _matches_signal(normalized: str, signal: Signal) -> bool:
    if signal.blockers and _has_any(normalized, signal.blockers):
        return False
    if signal.all_of and not all(_contains(normalized, item) for item in signal.all_of):
        return False
    if signal.any_of and not _has_any(normalized, signal.any_of):
        return False
    return bool(signal.any_of or signal.all_of)


def _summarize_asset(asset: str, hits: list[Signal], normalized: str, context: dict[str, bool]) -> dict[str, Any]:
    if not hits:
        if len(normalized) < 8:
            return _result("不确定", "低", 0, "新闻信息不足")
        return _neutral_result(asset, context)

    pos_score = sum(signal.score for signal in hits if signal.score > 0)
    neg_score = -sum(signal.score for signal in hits if signal.score < 0)
    raw_score = pos_score - neg_score

    if pos_score and neg_score and abs(raw_score) <= 1:
        return _result("不确定", "低", 0, "多空信号接近，方向不明")

    score = _clamp_score(raw_score)
    if score > 0:
        direction = "利多"
        reason = _build_reason(signal.reason for signal in hits if signal.score > 0)
    elif score < 0:
        direction = "利空"
        reason = _build_reason(signal.reason for signal in hits if signal.score < 0)
    else:
        direction = "中性"
        reason = _neutral_reason(asset, context)

    confidence = _confidence(abs(raw_score), len(hits), len(normalized), direction)
    return _result(direction, confidence, score, reason)


def _neutral_result(asset: str, context: dict[str, bool]) -> dict[str, Any]:
    if asset == "原油" and context.get("pure_crypto"):
        return _result("中性", "低", 0, "未直接涉及能源供需")
    if asset == "原油" and context.get("macro"):
        return _result("中性", "低", 0, "宏观新闻未直接涉及原油")
    return _result("中性", "低", 0, _neutral_reason(asset, context))


def _neutral_reason(asset: str, context: dict[str, bool]) -> str:
    if asset == "BTC":
        return "未直接涉及加密或流动性"
    if asset == "原油":
        return "未直接涉及能源供需"
    if asset == "黄金":
        return "未直接涉及避险或利率"
    return "未直接涉及美股核心因素"


def _result(direction: str, confidence: str, score: int, reason: str) -> dict[str, Any]:
    return {
        "direction": direction,
        "confidence": confidence,
        "score": _clamp_score(score),
        "reason": _limit_reason(reason),
    }


def _confidence(strength: int, hit_count: int, text_len: int, direction: str) -> str:
    if direction == "不确定" or text_len < 8:
        return "低"
    if strength >= 4 or (strength >= 3 and hit_count >= 2):
        return "高"
    if strength >= 2 or hit_count >= 2:
        return "中"
    return "低"


def _build_reason(reasons: Any) -> str:
    deduped: list[str] = []
    for reason in reasons:
        if reason and reason not in deduped:
            deduped.append(str(reason))
    return _limit_reason("，".join(deduped) if deduped else "证据不足，方向不明")


def _limit_reason(reason: str, max_chars: int = 30) -> str:
    compact = " ".join(str(reason).split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3] + "..."


def _clamp_score(score: int) -> int:
    return max(-3, min(3, int(score)))


def _has_any(normalized: str, patterns: tuple[str, ...]) -> bool:
    return any(_contains(normalized, pattern) for pattern in patterns)


def _contains(normalized: str, pattern: str) -> bool:
    return _normalize(pattern) in normalized


def _truncate_content_line(text: str, allowed_len: int) -> str:
    if len(text) <= allowed_len:
        return text

    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if not line.startswith("内容："):
            continue

        excess = len(text) - allowed_len
        body = line.removeprefix("内容：")
        new_body_len = max(0, len(body) - excess - 3)
        lines[idx] = "内容：" + (body[:new_body_len] + "..." if new_body_len > 0 else "...")
        shortened = "\n".join(lines)
        if len(shortened) <= allowed_len:
            return shortened
        break

    return _hard_truncate(text, allowed_len)


def _hard_truncate(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[: max_chars - 3] + "..."


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
