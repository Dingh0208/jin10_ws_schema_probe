from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import probe
from news_filter import evaluate_news


def make_msg(content: str, news_id: str = "sample") -> dict:
    return {
        "type": "flash",
        "action": 1,
        "id": news_id,
        "time": "2026-05-27 13:00:00",
        "data": {"content": content, "title": "", "source": "金十数据"},
        "important": 0,
        "tags": [],
        "remark": [],
        "extras": {"ad": False},
    }


def assert_case(name: str, content: str, expected_decision: str, expected_hit_type: str) -> None:
    result = evaluate_news(make_msg(content, name))
    actual = (result["decision"], result["hit_type"])
    expected = (expected_decision, expected_hit_type)
    print(name, json.dumps(result, ensure_ascii=False, sort_keys=True))
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected}, got {actual}")


def assert_min_score(name: str, content: str, min_score: int) -> None:
    result = evaluate_news(make_msg(content, name))
    if int(result["final_score"]) < min_score:
        raise AssertionError(f"{name}: expected final_score >= {min_score}, got {result['final_score']}")


def test_dedup() -> None:
    msg = make_msg("BTC突破关键阻力位，现报69000美元", "dedup-test")
    text = probe.full_news_text(msg)
    first = probe.build_dedup_hash(msg, text)
    second = probe.build_dedup_hash(msg, text)
    if first != second:
        raise AssertionError("dedup hash is not stable")


def test_dry_run() -> None:
    old_enabled = probe.QQ_PUSH_ENABLED
    try:
        probe.QQ_PUSH_ENABLED = False
        msg = make_msg("美国SEC推迟以太坊现货ETF审批，ETH短线下跌", "dry-run-test")
        evaluation = evaluate_news(msg)
        ok = probe.send_realtime_push("2026-05-27T13:00:00+08:00", msg, "dry-run-hash", "dry-run message", evaluation)
        if not ok:
            raise AssertionError("dry-run send should return true without QQ")
    finally:
        probe.QQ_PUSH_ENABLED = old_enabled


def main() -> int:
    cases = [
        ("A", "美国SEC推迟以太坊现货ETF审批，ETH短线下跌", "push", "direct_crypto_hit"),
        ("B", "美国CPI高于预期，美债收益率上升，纳指期货跳水", "push", "macro_market_hit"),
        ("C", "伊朗称将回应以色列袭击，黄金原油拉升，市场避险升温", "push", "us_iran_war_hit"),
        ("D", "某公司发布季度财报，营收同比增长", "skip", "pure_noise"),
        ("E", "某国外交部发言人表示关注地区局势", "skip", "pure_noise"),
        ("F", "BTC突破关键阻力位，现报69000美元", "push", "direct_crypto_hit"),
        ("G", "美联储官员表示仍需观察通胀数据，暂不急于降息", "push", "us_economy_hit"),
        ("H", "美国对伊朗导弹发射装置发动空袭，伊朗称将报复", "push", "us_iran_war_hit"),
        ("I", "特朗普表示将很快宣布新的关税政策", "push", "trump_hit"),
        ("J", "Solarpro公司发布季度财报，营收同比增长", "skip", "pure_noise"),
        ("K", "某AI服务器企业表示算力需求增长明显", "skip", "pure_noise"),
        ("L", "伊朗官员：根据美伊初步协议草案 美将在所有战线停火60天，特别是在黎巴嫩境内", "push", "us_iran_war_hit"),
        ("M", "美方与伊方据称接近达成停火协议，黎巴嫩方向将同步降温", "push", "us_iran_war_hit"),
        ("N", "霍尔木兹海峡附近发生军事冲突，油轮通行风险上升", "push", "us_iran_war_hit"),
        ("O", "美伊战争风险升温，美方进行新的军事部署", "push", "us_iran_war_hit"),
        ("P", "美国消费者信心指数公布，基本符合预期", "skip", "pure_noise"),
        ("Q", "美国CPI低于预期，美债收益率下行，纳指期货拉升", "push", "macro_market_hit"),
        ("R", "欧洲央行宣布降息25个基点", "skip", "pure_noise"),
        ("S", "美国地区银行股暴跌，引发系统性风险担忧", "push", "systemic_risk_hit"),
        ("T", "某地方银行破产处置完成", "skip", "pure_noise"),
        ("U", "SEC主席发表公开演讲", "skip", "pure_noise"),
        ("V", "SEC批准比特币现货ETF期权上市", "push", "direct_crypto_hit"),
        ("W", "美伊战争爆发，伊朗袭击美军基地", "push", "us_iran_war_hit"),
        ("X", "【美伊前景仍不明朗但市场存乐观预期 预计油价将震荡运行】金十期货研报显示，油价短线维持震荡", "skip", "pure_noise"),
        ("Y", "特朗普表示将在伊朗问题上推动达成协议", "push", "trump_hit"),
        ("Z", "霍尔木兹海峡持续封锁，全球油轮通行受阻", "push", "us_iran_war_hit"),
    ]
    for args in cases:
        assert_case(*args)
    assert_min_score(
        "major_ceasefire_score",
        "伊朗官员：根据美伊初步协议草案 美将在所有战线停火60天，特别是在黎巴嫩境内",
        12,
    )
    test_dedup()
    test_dry_run()
    print("filter_regression_test=passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
