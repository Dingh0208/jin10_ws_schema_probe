from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from impact_analyzer import (  # noqa: E402
    IMPACT_ANALYSIS_LOG_PATH,
    analyze_market_impact,
    append_impact_to_push_text,
    format_impact_for_qq,
    log_impact_analysis,
)


def assert_direction(name: str, impact: dict, asset: str, allowed: set[str]) -> None:
    actual = impact[asset]["direction"]
    if actual not in allowed:
        raise AssertionError(f"{name} {asset}: expected one of {sorted(allowed)}, got {actual}")


def main() -> int:
    cases = [
        (
            "CPI高于预期",
            "美国CPI高于预期，美债收益率上行，纳指期货跳水",
            {
                "BTC": {"利空"},
                "黄金": {"利空", "不确定"},
                "美股": {"利空"},
                "原油": {"中性"},
            },
        ),
        (
            "伊以冲突",
            "伊朗称将回应以色列袭击，市场避险情绪升温，原油和黄金拉升",
            {
                "原油": {"利多"},
                "黄金": {"利多"},
                "美股": {"利空"},
                "BTC": {"不确定", "利空"},
            },
        ),
        (
            "ETH ETF获批",
            "SEC批准以太坊现货ETF上市",
            {
                "BTC": {"利多", "中性"},
                "黄金": {"中性"},
                "原油": {"中性"},
                "美股": {"中性", "利多"},
            },
        ),
        (
            "OPEC减产",
            "OPEC宣布延长减产，国际油价上涨",
            {
                "原油": {"利多"},
                "黄金": {"中性"},
                "美股": {"利空", "不确定"},
                "BTC": {"中性"},
            },
        ),
        (
            "非农弱于预期",
            "美国非农就业弱于预期，市场押注美联储提前降息",
            {
                "BTC": {"利多"},
                "美股": {"利多"},
                "黄金": {"利多"},
                "原油": {"中性", "不确定"},
            },
        ),
        (
            "美伊全面停火",
            "伊朗官员称根据美伊初步协议草案，美方将在所有战线停火60天，特别是在黎巴嫩境内",
            {
                "BTC": {"利多"},
                "原油": {"利空"},
                "黄金": {"利空"},
                "美股": {"利多"},
            },
        ),
    ]

    outputs = []
    for name, text, expected in cases:
        impact = analyze_market_impact(text, {"text": text, "matched_keywords": []})
        for asset, allowed in expected.items():
            assert_direction(name, impact, asset, allowed)
        if name == "美伊全面停火" and impact["BTC"]["confidence"] != "高":
            raise AssertionError(f"{name} BTC: expected confidence 高, got {impact['BTC']['confidence']}")
        qq_text = format_impact_for_qq(impact)
        for item in impact.values():
            if len(item["reason"]) > 30:
                raise AssertionError(f"{name}: reason too long: {item['reason']}")
        outputs.append({"name": name, "text": text, "impact": impact, "qq_text": qq_text})
        print(name, json.dumps(impact, ensure_ascii=False, sort_keys=True))
        print(qq_text)

    old_size = IMPACT_ANALYSIS_LOG_PATH.stat().st_size if IMPACT_ANALYSIS_LOG_PATH.exists() else 0
    log_impact_analysis(cases[0][1], outputs[0]["impact"], {"sample": True})
    new_size = IMPACT_ANALYSIS_LOG_PATH.stat().st_size
    if new_size <= old_size:
        raise AssertionError("impact_analysis.log was not written")

    long_push = "标题\n内容：" + ("美国CPI高于预期，" * 120)
    final_push = append_impact_to_push_text(long_push, outputs[0]["qq_text"], max_chars=1200)
    if len(final_push) > 1200:
        raise AssertionError(f"QQ push too long: {len(final_push)}")
    if "【市场影响判断】" not in final_push:
        raise AssertionError("impact block missing after truncation")

    print("impact_analyzer_test=passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
