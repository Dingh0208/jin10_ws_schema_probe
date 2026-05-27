from __future__ import annotations

import json
import re
from typing import Any

PUSH_SCORE_THRESHOLD = 7

CRYPTO_STRONG_KEYWORDS = [
    "BTC",
    "ETH",
    "SOL",
    "XRP",
    "BNB",
    "DOGE",
    "比特币",
    "以太坊",
    "狗狗币",
    "加密货币",
    "虚拟资产",
    "数字资产",
    "数字货币",
    "稳定币",
    "USDT",
    "USDC",
    "Tether",
    "Circle",
    "链上",
    "币安",
    "Binance",
    "OKX",
    "Coinbase",
    "Kraken",
    "Bybit",
    "现货ETF",
    "现货比特币ETF",
    "现货以太坊ETF",
    "ETF净流入",
    "ETF净流出",
    "比特币ETF",
    "以太坊ETF",
    "灰度",
    "贝莱德",
    "MicroStrategy",
    "矿工",
    "挖矿",
    "矿池",
    "矿机",
    "爆仓",
    "清算",
    "巨鲸",
    "鲸鱼",
    "哈希率",
    "Gas",
    "DeFi",
    "Web3",
    "RWA",
    "质押",
    "L2",
    "L1",
    "Layer2",
    "Layer 2",
    "Solana",
]

CRYPTO_CONTEXT_KEYWORDS_V2 = ["ETF", "SEC", "CFTC", "交易所", "区块链", "钱包", "DEX"]

CRYPTO_REGULATORY_KEYWORDS = [
    "现货ETF",
    "ETF获批",
    "ETF批准",
    "ETF上市",
    "ETF推迟",
    "ETF延期",
    "ETF拒绝",
    "SEC批准",
    "SEC推迟",
    "SEC拒绝",
    "SEC起诉",
    "SEC执法",
    "CFTC起诉",
    "CFTC执法",
    "稳定币法案",
    "GENIUS法案",
    "加密法案",
    "数字资产法案",
    "战略比特币储备",
    "比特币储备",
]

US_MACRO_CRITICAL_KEYWORDS = [
    "核心CPI",
    "核心PCE",
    "CPI",
    "PCE",
    "非农",
    "NFP",
    "FOMC",
    "利率决议",
    "点阵图",
    "会议纪要",
    "鲍威尔",
    "美联储主席",
    "降息",
    "加息",
    "暂停降息",
    "暂停加息",
    "缩表",
    "扩表",
    "流动性",
    "美债收益率",
    "美国国债收益率",
    "国债收益率",
    "十年期美债",
    "10年期美债",
    "美元指数",
]

MACRO_SURPRISE_KEYWORDS = [
    "高于预期",
    "低于预期",
    "强于预期",
    "弱于预期",
    "不及预期",
    "超预期",
    "意外",
    "大幅",
    "创纪录",
    "创历史",
    "创阶段",
    "降至",
    "升至",
    "衰退",
]

US_ECONOMY_KEYWORDS = [
    "美国经济",
    "美国财政部",
    "贝森特",
    "美联储",
    "FOMC",
    "鲍威尔",
    "CPI",
    "PCE",
    "非农",
    "NFP",
    "ADP",
    "JOLTS",
    "初请失业金",
    "续请失业金",
    "失业率",
    "平均时薪",
    "零售销售",
    "消费者信心",
    "GDP",
    "PMI",
    "ISM",
    "通胀",
    "利率",
    "降息",
    "加息",
    "美债收益率",
    "美国国债收益率",
    "十年期美债",
    "10年期美债",
    "美元指数",
]

TRUMP_KEYWORDS = ["特朗普", "Trump", "美国总统"]

US_IRAN_WAR_SUBJECT_KEYWORDS = [
    "美伊",
    "美伊战争",
    "美伊双方",
    "美方",
    "伊方",
    "美国对伊朗",
    "伊朗对美国",
    "美国和伊朗",
    "美国与伊朗",
    "伊朗",
    "以色列",
    "黎巴嫩",
    "哈马斯",
    "胡塞武装",
    "真主党",
    "加沙",
    "红海",
    "霍尔木兹",
    "霍尔木兹海峡",
    "中东",
]

US_IRAN_WAR_ACTION_KEYWORDS = [
    "战争",
    "美伊战争",
    "战争开启",
    "战争爆发",
    "全面战争",
    "开战",
    "宣战",
    "冲突",
    "冲突升级",
    "空袭",
    "袭击",
    "导弹",
    "无人机",
    "报复",
    "制裁",
    "停火",
    "全面停火",
    "停火协议",
    "停战",
    "休战",
    "核设施",
    "军事",
    "军事行动",
    "军事打击",
    "军事冲突",
    "军事部署",
    "打击",
    "交火",
    "开火",
    "遇袭",
    "遭袭",
]

MACRO_STRONG_KEYWORDS = [
    "CPI",
    "PCE",
    "非农",
    "NFP",
    "ADP",
    "JOLTS",
    "失业率",
    "初请失业金",
    "续请失业金",
    "平均时薪",
    "零售销售",
    "消费者信心",
    "GDP",
    "PMI",
    "ISM",
    "美联储",
    "FOMC",
    "鲍威尔",
    "降息",
    "加息",
    "通胀",
    "利率",
    "美元指数",
    "美债收益率",
    "美国国债收益率",
    "国债收益率",
    "十年期美债",
    "10年期美债",
    "流动性",
    "缩表",
    "扩表",
]

MARKET_KEYWORDS_V2 = [
    "纳指",
    "纳斯达克",
    "标普",
    "标普500",
    "S&P 500",
    "道指",
    "美股",
    "美股期货",
    "科技股",
    "英伟达",
    "英伟达",
    "苹果",
    "特斯拉",
    "黄金",
    "原油",
    "油价",
    "美元",
    "美元指数",
    "美债",
    "美债收益率",
    "美国国债收益率",
    "国债收益率",
    "VIX",
    "恐慌指数",
]

MARKET_IMPACT_KEYWORDS = [
    "大涨",
    "大跌",
    "暴涨",
    "暴跌",
    "跳水",
    "拉升",
    "飙升",
    "重挫",
    "急跌",
    "急升",
    "突破",
    "跌破",
    "升破",
    "避险",
    "风险资产",
    "风险偏好",
    "风险情绪",
    "波动",
    "抛售",
    "上涨",
    "下跌",
    "走高",
    "走低",
]

RISK_KEYWORDS_V2 = [
    "战争",
    "美伊战争",
    "战争开启",
    "战争爆发",
    "全面战争",
    "开战",
    "宣战",
    "地缘",
    "美伊",
    "美伊双方",
    "美方",
    "伊方",
    "美国与伊朗",
    "美国和伊朗",
    "伊朗",
    "以色列",
    "黎巴嫩",
    "俄罗斯",
    "乌克兰",
    "哈马斯",
    "胡塞",
    "真主党",
    "红海",
    "霍尔木兹",
    "霍尔木兹海峡",
    "制裁",
    "空袭",
    "袭击",
    "停火",
    "全面停火",
    "停火协议",
    "所有战线",
    "导弹",
    "无人机",
    "军事",
    "军事行动",
    "军事打击",
    "军事冲突",
    "军事部署",
    "打击核设施",
    "核设施遭袭",
    "关闭霍尔木兹",
    "封锁霍尔木兹",
    "威胁关闭霍尔木兹",
    "恐袭",
    "冲突",
    "避险",
    "风险偏好",
    "核设施",
    "油轮",
    "商船",
    "金融风险",
    "银行危机",
    "系统性风险",
    "流动性危机",
    "美元荒",
    "稳定币脱锚",
    "USDT脱锚",
    "USDC脱锚",
]

MIDDLE_EAST_DEESCALATION_KEYWORDS = [
    "停火",
    "全面停火",
    "停火协议",
    "停火60天",
    "停战",
    "休战",
    "停火生效",
    "达成停火",
    "结束战争",
    "所有战线",
    "初步协议",
    "协议草案",
    "和谈",
]

MIDDLE_EAST_MAJOR_DEESCALATION_KEYWORDS = [
    "全面停火",
    "停火60天",
    "60天",
    "停战",
    "休战",
    "停火生效",
    "达成停火",
    "结束战争",
    "所有战线",
    "美伊初步协议",
    "初步协议草案",
    "协议草案",
]

MIDDLE_EAST_MAJOR_ESCALATION_KEYWORDS = [
    "战争开启",
    "战争爆发",
    "全面战争",
    "开战",
    "宣战",
    "冲突升级",
    "大规模袭击",
    "大规模空袭",
    "打击核设施",
    "核设施遭袭",
    "关闭霍尔木兹",
    "封锁霍尔木兹",
    "威胁关闭霍尔木兹",
    "袭击美军",
    "报复行动",
]

SYSTEMIC_RISK_KEYWORDS = [
    "金融风险",
    "银行危机",
    "系统性风险",
    "流动性危机",
    "信用风险",
    "信贷危机",
    "美元荒",
    "回购市场",
    "美债流动性",
    "挤兑",
    "银行挤兑",
    "银行股暴跌",
    "地区银行",
    "大型银行",
    "破产",
    "违约",
    "稳定币脱锚",
    "USDT脱锚",
    "USDC脱锚",
]

SYSTEMIC_ALWAYS_KEYWORDS = [
    "金融风险",
    "银行危机",
    "系统性风险",
    "流动性危机",
    "美元荒",
    "美债流动性",
    "稳定币脱锚",
    "USDT脱锚",
    "USDC脱锚",
]

SYSTEMIC_CONTEXTUAL_KEYWORDS = [
    "信用风险",
    "信贷危机",
    "回购市场",
    "挤兑",
    "银行挤兑",
    "银行股暴跌",
    "地区银行",
    "大型银行",
    "破产",
    "违约",
]

RESEARCH_NOISE_KEYWORDS = [
    "金十期货",
    "期货研报",
    "研报显示",
    "特约点评",
    "机构观点",
    "策略师表示",
    "分析师表示",
    "短线维持",
    "维持震荡",
    "震荡运行",
]

NOISE_KEYWORDS_V2 = [
    "公司公告",
    "季度财报",
    "财报",
    "营收同比",
    "董事长",
    "任命",
    "回购",
    "减持",
    "股权转让",
    "A股",
    "个股",
    "体育",
    "娱乐",
    "社会",
    "民生",
    "活动",
    "免责声明",
    "仅供参考",
    "不构成任何投资建议",
    "正在直播",
    "点击进入直播间",
    "VIP专享快讯",
    "解锁直达",
]

US_MACRO_FORCE_KEYWORDS = [
    "核心CPI",
    "核心PCE",
    "CPI",
    "PCE",
    "非农",
    "NFP",
]

US_MACRO_DATA_KEYWORDS = [
    "核心CPI",
    "核心PCE",
    "CPI",
    "PCE",
    "非农",
    "NFP",
    "ADP",
    "初请失业金",
    "续请失业金",
    "失业率",
    "平均时薪",
    "JOLTS",
    "职位空缺",
    "零售销售",
    "消费者信心",
    "GDP",
    "PMI",
    "通胀",
]

US_CONTEXT = [
    "美国",
    "美联储",
    "FOMC",
    "鲍威尔",
    "美元",
    "美债",
    "华尔街",
    "纽约联储",
    "费城联储",
    "亚特兰大联储",
    "克利夫兰联储",
    "芝加哥联储",
    "达拉斯联储",
    "旧金山联储",
    "CME",
    "美联储观察",
]

US_SPECIFIC_MACRO = [
    "非农",
    "NFP",
    "初请失业金",
    "续请失业金",
    "JOLTS",
    "ISM",
    "美联储褐皮书",
    "美联储会议纪要",
    "FOMC",
    "鲍威尔",
]

MACRO_TERMS = [
    "核心CPI",
    "核心PCE",
    "CPI",
    "PCE",
    "ADP",
    "失业率",
    "平均时薪",
    "职位空缺",
    "零售销售",
    "消费者信心",
    "GDP",
    "PMI",
    "通胀",
    "央行",
    "利率",
    "降息",
    "加息",
]

NON_US_MACRO_CONTEXT = [
    "加拿大",
    "加拿大央行",
    "欧洲央行",
    "欧元区",
    "德国",
    "法国",
    "英国",
    "英国央行",
    "日本",
    "日本央行",
    "澳大利亚",
    "澳洲联储",
    "新西兰",
    "瑞士",
    "瑞士央行",
    "韩国",
    "印度",
    "巴西",
    "墨西哥",
    "土耳其",
    "南非",
    "印尼",
    "泰国",
    "越南",
    "马来西亚",
    "新加坡",
]

NON_US_MACRO_OVERRIDE = [
    "比特币",
    "BTC",
    "以太坊",
    "ETH",
    "加密货币",
    "稳定币",
    "SEC",
    "CFTC",
    "币安",
    "Binance",
    "Coinbase",
    "伊朗",
    "以色列",
    "美国制裁",
    "关税",
    "特朗普",
]

FED_FORCE_KEYWORDS = [
    "CME美联储观察",
    "美联储观察",
    "美国利率期货",
    "FOMC",
    "利率决议",
    "鲍威尔",
    "点阵图",
    "会议纪要",
]

FED_EVENT_KEYWORDS = [
    "美联储",
    "FOMC",
    "利率决议",
    "鲍威尔",
    "点阵图",
    "会议纪要",
    "降息",
    "加息",
    "暂停降息",
    "暂停加息",
    "利率期货",
    "美国利率期货",
    "美联储观察",
    "CME美联储观察",
]

FED_OFFICIAL_KEYWORDS = [
    "威廉姆斯",
    "沃勒",
    "古尔斯比",
    "博斯蒂克",
    "哈玛克",
    "戴利",
    "卡什卡利",
    "洛根",
    "巴尔金",
    "梅斯特",
]

FED_OFFICIAL_CONTEXT_KEYWORDS = [
    "降息",
    "加息",
    "通胀",
    "利率",
    "就业",
    "经济",
    "货币政策",
    "鹰派",
    "鸽派",
]

GEOPOLITICAL_SUBJECT_KEYWORDS = [
    "伊朗",
    "伊方",
    "美伊战争",
    "以色列",
    "美国",
    "美方",
    "美伊双方",
    "美军",
    "胡塞武装",
    "哈马斯",
    "黎巴嫩",
    "真主党",
    "叙利亚",
    "伊拉克",
    "也门",
    "加沙",
    "红海",
    "霍尔木兹",
    "霍尔木兹海峡",
    "阿曼湾",
    "波斯湾",
    "中东",
    "南黎巴嫩",
    "以色列国防军",
    "伊朗革命卫队",
    "阿曼",
    "马斯喀特",
    "油轮",
    "船只",
    "海事",
    "海上贸易",
    "海上贸易行动办公室",
    "英国海事贸易组织",
    "英国海上贸易行动办公室",
]

GEOPOLITICAL_ACTION_KEYWORDS = [
    "导弹",
    "火箭弹",
    "空袭",
    "袭击",
    "爆炸",
    "遭遇爆炸",
    "报复",
    "轰炸",
    "拦截",
    "无人机",
    "军事",
    "军事行动",
    "军事打击",
    "军事冲突",
    "军事部署",
    "打击",
    "开火",
    "交火",
    "作战",
    "战备",
    "停火",
    "停火协议",
    "违反停火",
    "伤亡",
    "死亡",
    "受伤",
    "击落",
    "撤侨",
    "进入战备",
    "核设施",
    "核谈判",
    "制裁",
    "战争",
    "战争开启",
    "战争爆发",
    "全面战争",
    "开战",
    "宣战",
    "冲突升级",
    "威胁关闭",
    "关闭霍尔木兹",
    "封锁霍尔木兹",
    "威胁关闭霍尔木兹",
    "外部爆炸",
    "发生事件",
]

SHIPPING_RISK_ACTORS = [
    "油轮",
    "商船",
    "船只",
    "货轮",
    "海上贸易",
    "海事贸易",
    "英国海事贸易组织",
    "英国海上贸易行动办公室",
    "UKMTO",
    "红海",
    "阿曼",
    "阿曼湾",
    "霍尔木兹",
    "霍尔木兹海峡",
    "波斯湾",
    "也门",
    "胡塞武装",
]

SHIPPING_RISK_ACTIONS = [
    "爆炸",
    "外部爆炸",
    "遭遇爆炸",
    "意外事件",
    "袭击",
    "遭袭",
    "遇袭",
    "导弹",
    "无人机",
    "军事",
    "军事行动",
    "军事打击",
    "军事冲突",
    "关闭霍尔木兹",
    "封锁霍尔木兹",
    "封锁",
    "关闭",
    "恢复通航",
    "通航",
    "扣押",
    "失联",
    "起火",
    "受损",
    "求救",
    "报告事件",
    "发生事件",
    "护航",
    "引导",
    "恢复引导",
    "协助",
    "穿越",
    "航运问题",
    "受阻",
    "中断",
]

TRUMP_POLICY_SUBJECT_KEYWORDS = [
    "特朗普",
    "白宫",
    "美国总统",
    "美国财政部",
    "美国政府",
    "贝森特",
]

TRUMP_POLICY_ACTION_KEYWORDS = [
    "关税",
    "制裁",
    "贸易战",
    "行政令",
    "禁令",
    "加征",
    "对华",
    "美中",
    "债务上限",
    "政府关门",
    "财政刺激",
    "税改",
    "加密货币",
    "比特币",
    "战略储备",
]

MARKET_MOVE_TARGET_KEYWORDS = [
    "美元指数",
    "DXY",
    "美债收益率",
    "美国国债收益率",
    "10年期美债",
    "2年期美债",
    "30年期美债",
    "10年期收益率",
    "2年期收益率",
    "30年期收益率",
    "美国国债",
    "国债收益率",
    "纳指",
    "标普",
    "VIX",
    "恐慌指数",
    "黄金",
    "原油",
]

MARKET_MOVE_ACTION_KEYWORDS = [
    "大涨",
    "大跌",
    "暴涨",
    "暴跌",
    "跳水",
    "飙升",
    "拉升",
    "下滑",
    "回落",
    "走低",
    "走高",
    "跌回",
    "升至",
    "跌至",
    "突破",
    "跌破",
    "升破",
    "创历史新高",
    "创阶段新高",
    "创日内新高",
    "创日内新低",
]

DIRECT_CRYPTO_KEYWORDS = [
    "BTC",
    "ETH",
    "比特币",
    "以太坊",
    "加密货币",
    "数字资产",
    "稳定币",
    "USDT",
    "USDC",
    "比特币ETF",
    "以太坊ETF",
    "SEC",
    "CFTC",
    "Coinbase",
    "Binance",
    "币安",
    "OKX",
    "清算",
    "爆仓",
    "链上",
    "鲸鱼",
    "交易所被盗",
]

CONTEXTUAL_CRYPTO_KEYWORDS = ["钱包", "交易所", "区块链", "黑客攻击"]
CRYPTO_CONTEXT_KEYWORDS = [
    "BTC",
    "ETH",
    "比特币",
    "以太坊",
    "稳定币",
    "USDT",
    "USDC",
    "SEC",
    "CFTC",
    "Coinbase",
    "Binance",
    "币安",
    "OKX",
    "清算",
    "爆仓",
    "链上",
    "加密",
]

NOISE_KEYWORDS = [
    "A股",
    "个股",
    "公司公告",
    "回购",
    "减持",
    "股权转让",
    "异常波动",
    "股票交易异常波动",
    "研发阶段",
    "研发进展",
    "业绩预告",
    "董事长",
    "任命",
    "卸任",
    "产量",
    "库存",
    "氧化铝",
    "碳酸锂",
    "农产品",
    "金属",
    "化工品",
    "房地产",
    "地方产业",
    "消费级机器人",
]

COMPANY_NOISE_KEYWORDS = [
    "A股",
    "个股",
    "公司公告",
    "回购",
    "减持",
    "股权转让",
    "研发阶段",
    "研发进展",
    "董事长",
    "任命",
    "卸任",
    "业绩预告",
    "异常波动",
    "股票交易异常波动",
]

COMMODITY_NOISE_KEYWORDS = ["产量", "库存", "氧化铝", "碳酸锂", "农产品", "金属", "化工品"]

STRONG_NOISE_OVERRIDE_KEYWORDS = [
    "CPI",
    "PCE",
    "非农",
    "FOMC",
    "鲍威尔",
    "美联储",
    "BTC",
    "ETH",
    "比特币",
    "以太坊",
]

def extract_text_fields(msg: dict[str, Any]) -> dict[str, str]:
    title_parts: list[str] = []
    body_parts: list[str] = []
    meta_parts: list[str] = []

    def add(target: list[str], value: Any) -> None:
        if isinstance(value, str) and value.strip():
            target.append(value.strip())
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            target.append(str(value))

    add(title_parts, msg.get("title"))
    add(body_parts, msg.get("content"))
    add(meta_parts, msg.get("category"))
    add(meta_parts, msg.get("type"))

    data = msg.get("data")
    if isinstance(data, dict):
        add(title_parts, data.get("title"))
        add(body_parts, data.get("content"))
        add(meta_parts, data.get("source"))
        add(meta_parts, data.get("tag"))
        add(meta_parts, data.get("vip_title"))
        add(meta_parts, data.get("vip_desc"))
    elif isinstance(data, list):
        for item in data[:5]:
            if isinstance(item, dict):
                nested = extract_text_fields(item)
                add(title_parts, nested.get("title"))
                add(body_parts, nested.get("body"))
                add(meta_parts, nested.get("meta"))

    for item in msg.get("remark", []) if isinstance(msg.get("remark"), list) else []:
        if isinstance(item, dict):
            add(meta_parts, item.get("title"))
            add(meta_parts, item.get("content"))
            add(meta_parts, item.get("symbol"))
            add(meta_parts, item.get("category"))
            add(meta_parts, item.get("category_name"))
            add(meta_parts, item.get("name"))
        else:
            add(meta_parts, item)

    for item in msg.get("tags", []) if isinstance(msg.get("tags"), list) else []:
        if isinstance(item, dict):
            for value in item.values():
                add(meta_parts, value)
        else:
            add(meta_parts, item)

    return {
        "title": " ".join(_dedupe_text_parts(title_parts)),
        "body": " ".join(_dedupe_text_parts(body_parts)),
        "meta": " ".join(_dedupe_text_parts(meta_parts)),
    }


def score_news(msg: dict[str, Any]) -> dict[str, Any]:
    fields = extract_text_fields(msg)
    title_text = fields["title"]
    body_text = " ".join(part for part in (fields["body"], fields["meta"]) if part)
    all_text = " ".join(part for part in (title_text, body_text) if part)

    score = 0
    reasons: list[str] = []
    matched_keywords: list[str] = []
    reason_types: list[str] = []
    non_us_macro = _is_non_us_macro(all_text)
    if non_us_macro:
        macro_hits = _find_keywords(all_text, MACRO_TERMS + US_MACRO_DATA_KEYWORDS + FED_EVENT_KEYWORDS)
        return {
            "score": 0,
            "decision": "drop",
            "matched_keywords": macro_hits + _find_keywords(all_text, NON_US_MACRO_CONTEXT),
            "reasons": ["non_us_macro"],
            "reason_type": "UNKNOWN",
            "reason_types": [],
            "push_reason": "",
            "skip_reason": "non_us_macro",
            "fields": fields,
        }

    us_macro_hits = _find_allowed_us_macro_hits(all_text)
    us_macro_force_hits = _find_keywords(all_text, US_MACRO_FORCE_KEYWORDS)
    macro_term_hits = _find_keywords(all_text, MACRO_TERMS)
    allow_us_macro = is_us_macro(all_text) if macro_term_hits or us_macro_hits else False
    if us_macro_hits and allow_us_macro:
        score += 6
        reasons.append("美国核心宏观数据:+6")
        matched_keywords.extend(us_macro_hits)
        reason_types.append("US_MACRO")

    fed_force_hits = _find_keywords(all_text, FED_FORCE_KEYWORDS)
    fed_event_hits = _find_keywords(all_text, FED_EVENT_KEYWORDS)
    fed_official_hits = _find_keywords(all_text, FED_OFFICIAL_KEYWORDS)
    fed_context_hits = _find_keywords(all_text, FED_OFFICIAL_CONTEXT_KEYWORDS)
    fed_should_score = (bool(fed_force_hits) or bool(fed_official_hits and fed_context_hits)) and is_us_macro(all_text)
    if not fed_should_score and "美联储" in fed_event_hits and fed_context_hits and is_us_macro(all_text):
        fed_should_score = True
    if fed_should_score:
        score += 6
        reasons.append("FOMC/鲍威尔/利率事件:+6")
        matched_keywords.extend(fed_event_hits + fed_official_hits + fed_context_hits)
        reason_types.append("FED")

    shipping_actor_hits = _find_keywords(all_text, SHIPPING_RISK_ACTORS)
    shipping_action_hits = _find_keywords(all_text, SHIPPING_RISK_ACTIONS)
    shipping_combo = bool(shipping_actor_hits and shipping_action_hits)
    if shipping_combo:
        score += 6
        reasons.append("中东航运/能源风险:+6")
        matched_keywords.extend(shipping_actor_hits + shipping_action_hits)
        reason_types.append("ENERGY_SHIPPING_RISK")

    geo_subject_hits = _find_keywords(all_text, GEOPOLITICAL_SUBJECT_KEYWORDS)
    geo_action_hits = _find_keywords(all_text, GEOPOLITICAL_ACTION_KEYWORDS)
    geo_combo = _is_middle_east_geo_combo(all_text, geo_subject_hits, geo_action_hits)
    if geo_combo:
        score += 6
        reasons.append("地缘主体+战争升级动作:+6")
        matched_keywords.extend(geo_subject_hits + geo_action_hits)
        reason_types.append("MIDDLE_EAST_RISK")

    trump_subject_hits = _find_keywords(all_text, TRUMP_POLICY_SUBJECT_KEYWORDS)
    trump_action_hits = _find_keywords(all_text, TRUMP_POLICY_ACTION_KEYWORDS)
    trump_combo = bool(trump_subject_hits and trump_action_hits)
    if trump_combo:
        score += 5
        reasons.append("特朗普/美国政策主体+动作:+5")
        matched_keywords.extend(trump_subject_hits + trump_action_hits)
        reason_types.append("TRUMP_POLICY")

    direct_crypto_hits = _find_keywords(all_text, DIRECT_CRYPTO_KEYWORDS)
    contextual_crypto_hits = _find_contextual_keywords(all_text, CONTEXTUAL_CRYPTO_KEYWORDS, CRYPTO_CONTEXT_KEYWORDS)
    crypto_combo = bool(direct_crypto_hits or contextual_crypto_hits)
    if crypto_combo:
        score += 5
        reasons.append("直接加密相关:+5")
        matched_keywords.extend(direct_crypto_hits + contextual_crypto_hits)
        reason_types.append("CRYPTO_DIRECT")

    market_move_hits = _find_market_move_hits(all_text)
    if market_move_hits:
        score += 4
        reasons.append("市场异常波动组合:+4")
        matched_keywords.extend(market_move_hits)
        reason_types.append("MARKET_MOVE")
        score += 1
        reasons.append("市场异常波动达推送阈值:+1")

    if msg.get("important") == 1:
        score += 1
        reasons.append("important=1:+1")

    strong_override = bool(
        us_macro_force_hits
        or fed_force_hits
        or shipping_combo
        or geo_combo
        or trump_combo
        or _find_keywords(all_text, ["BTC", "ETH", "比特币", "以太坊"])
    )
    noise_hits = _find_keywords(all_text, NOISE_KEYWORDS)
    company_noise_hits = _find_keywords(all_text, COMPANY_NOISE_KEYWORDS)
    commodity_noise_hits = _find_keywords(all_text, COMMODITY_NOISE_KEYWORDS)
    if company_noise_hits and not strong_override:
        score -= 6
        reasons.append("A股/公司公告/个股噪音:-6")
        matched_keywords.extend(company_noise_hits)
    if commodity_noise_hits and not strong_override:
        score -= 4
        reasons.append("商品普通供需/产量/库存:-4")
        matched_keywords.extend(commodity_noise_hits)
    if _is_plain_company_news(all_text) and not strong_override:
        score -= 5
        reasons.append("普通公司新闻:-5")
    if noise_hits and strong_override:
        reasons.append("命中噪音词但有强事件覆盖")
        matched_keywords.extend(noise_hits)

    matched_keywords = _dedupe_text_parts(matched_keywords)
    decision = "push" if score >= 5 else "record" if score >= 3 else "drop"
    push_reason = ";".join(reasons) if decision == "push" else ""
    skip_reason = "" if decision == "push" else _build_skip_reason(reasons, noise_hits)

    return {
        "score": score,
        "decision": decision,
        "matched_keywords": matched_keywords,
        "reasons": reasons,
        "reason_type": _primary_reason_type(reason_types),
        "reason_types": _dedupe_text_parts(reason_types),
        "push_reason": push_reason,
        "skip_reason": skip_reason,
        "fields": fields,
    }


def should_push(msg: dict[str, Any]) -> bool:
    if not _is_push_candidate(msg):
        return False
    return score_news(msg)["score"] >= 5


IGNORED_TEXT_KEYS = {
    "id",
    "time",
    "action",
    "type",
    "m_type",
    "event",
    "url",
    "link",
    "href",
    "image",
    "pic",
    "avatar",
}


def iter_string_fields(value: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(value, str):
        text = value.strip()
        if text:
            strings.append(text)
    elif isinstance(value, dict):
        for key, item in value.items():
            if str(key) in IGNORED_TEXT_KEYS:
                continue
            strings.extend(iter_string_fields(item))
    elif isinstance(value, list):
        for item in value:
            strings.extend(iter_string_fields(item))
    return strings


def full_news_text(msg: dict[str, Any]) -> str:
    return " ".join(_dedupe_text_parts(iter_string_fields(msg)))


def primary_news_content(msg: dict[str, Any]) -> str:
    fields = extract_text_fields(msg)
    return fields.get("body") or fields.get("title") or fields.get("meta") or full_news_text(msg)


def _is_ascii_token(keyword: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9]+", keyword))


def _keyword_in_text(text: str, keyword: str) -> bool:
    if not text or not keyword:
        return False
    if _is_ascii_token(keyword):
        return bool(re.search(rf"(?<![A-Za-z0-9]){re.escape(keyword)}(?![A-Za-z0-9])", text, re.IGNORECASE))
    return keyword.lower() in text.lower()


def _find_any(text: str, keywords: list[str]) -> list[str]:
    return _dedupe_text_parts([keyword for keyword in keywords if _keyword_in_text(text, keyword)])


def _has_any(text: str, keywords: list[str]) -> bool:
    return bool(_find_any(text, keywords))


def _contains_us_context(text: str) -> bool:
    context = [keyword for keyword in US_CONTEXT if keyword != "美元"]
    return _has_any(text, context + ["美国", "华尔街", "纳指", "标普", "道指", "美股", "美债"])


def _contains_macro_market_impact(text: str) -> bool:
    return _has_any(text, MARKET_KEYWORDS_V2 + MARKET_IMPACT_KEYWORDS + ["风险资产", "风险偏好", "流动性", "美元指数", "美债收益率"])


def _contains_us_economy_news(text: str) -> bool:
    if _is_non_us_macro(text):
        return False
    return _contains_us_context(text) and _has_any(text, US_ECONOMY_KEYWORDS)


def _contains_crypto_regulatory_news(text: str) -> bool:
    if not _has_any(text, CRYPTO_REGULATORY_KEYWORDS):
        return False
    return _has_any(text, CRYPTO_STRONG_KEYWORDS + ["加密", "数字资产", "现货", "稳定币", "比特币", "以太坊"])


def _contains_critical_us_macro(text: str) -> bool:
    if _is_non_us_macro(text):
        return False
    return _contains_us_context(text) and _has_any(text, US_MACRO_CRITICAL_KEYWORDS)


def _contains_surprising_us_macro(text: str) -> bool:
    if _is_non_us_macro(text):
        return False
    return _contains_us_context(text) and _has_any(text, US_ECONOMY_KEYWORDS) and _has_any(text, MACRO_SURPRISE_KEYWORDS)


def _contains_systemic_risk(text: str) -> bool:
    if _has_any(text, SYSTEMIC_ALWAYS_KEYWORDS):
        return True
    if not _has_any(text, SYSTEMIC_CONTEXTUAL_KEYWORDS):
        return False
    return _has_any(text, ["美国", "美元", "美债", "华尔街", "稳定币", "USDT", "USDC", "加密", "全球"])


def _is_research_or_commentary_noise(text: str) -> bool:
    if not _has_any(text, RESEARCH_NOISE_KEYWORDS):
        return False
    return not _has_any(text, CRYPTO_STRONG_KEYWORDS + ["比特币", "以太坊", "BTC", "ETH", "稳定币脱锚", "USDT脱锚", "USDC脱锚"])


def _contains_trump_news(text: str) -> bool:
    if not _has_any(text, TRUMP_KEYWORDS):
        return False
    return _has_any(
        text,
        TRUMP_POLICY_ACTION_KEYWORDS
        + [
            "伊朗",
            "以色列",
            "战争",
            "停火",
            "协议",
            "霍尔木兹",
            "美联储",
            "鲍威尔",
            "降息",
            "加息",
            "CPI",
            "PCE",
            "美元",
            "美债",
            "比特币",
            "加密",
            "SEC",
        ],
    )


def _contains_us_iran_war_news(text: str) -> bool:
    direct_pair = _has_any(
        text,
        [
            "美伊",
            "美伊双方",
            "美国对伊朗",
            "伊朗对美国",
            "美国和伊朗",
            "美国与伊朗",
            "美伊战争",
            "美方和伊方",
            "美方与伊方",
            "伊方和美方",
            "伊方与美方",
        ],
    )
    middle_east_subject = _has_any(
        text,
        [
            "伊朗",
            "伊方",
            "以色列",
            "黎巴嫩",
            "真主党",
            "哈马斯",
            "胡塞武装",
            "加沙",
            "红海",
            "霍尔木兹",
            "霍尔木兹海峡",
            "中东",
            "美伊战争",
        ],
    )
    us_side_subject = _has_any(text, ["美国", "美方", "美军", "白宫", "特朗普"])
    subject_combo = _has_any(text, US_IRAN_WAR_SUBJECT_KEYWORDS) and (
        _has_any(text, ["伊朗", "以色列"]) or (middle_east_subject and us_side_subject)
    )
    return (direct_pair or subject_combo) and _has_any(text, US_IRAN_WAR_ACTION_KEYWORDS)


def _contains_geopolitical_market_impact(text: str) -> bool:
    return _has_any(
        text,
        [
            "黄金",
            "原油",
            "油价",
            "美元指数",
            "美股",
            "纳指",
            "标普",
            "VIX",
            "风险资产",
            "风险偏好",
            "避险",
            "加密市场",
            "比特币",
            "BTC",
            "ETH",
        ],
    ) and _has_any(text, MARKET_IMPACT_KEYWORDS + ["避险", "风险资产", "风险偏好", "拉升", "跳水", "暴涨", "暴跌", "大涨", "大跌"])


def _is_plain_noise(text: str) -> bool:
    if _has_any(text, CRYPTO_STRONG_KEYWORDS):
        return False
    company_noise = _has_any(text, ["公司公告", "季度财报", "财报", "营收同比", "董事长", "任命", "回购", "减持", "股权转让", "个股"])
    political_noise = _has_any(text, ["发言人表示", "表示关注", "会见", "访问", "抵达", "会议"]) and not _has_any(
        text, ["制裁", "导弹", "空袭", "袭击", "战争", "冲突", "黄金", "原油", "美元", "美股", "纳指", "风险资产", "避险"]
    )
    return company_noise or political_noise


def evaluate_news(msg: dict[str, Any], threshold: int = PUSH_SCORE_THRESHOLD) -> dict[str, Any]:
    fields = extract_text_fields(msg)
    text = full_news_text(msg)
    content = primary_news_content(msg)

    crypto_hits = _find_any(text, CRYPTO_STRONG_KEYWORDS)
    crypto_context_hits = _find_any(text, CRYPTO_CONTEXT_KEYWORDS_V2)
    crypto_regulatory_hits = _find_any(text, CRYPTO_REGULATORY_KEYWORDS)
    macro_hits = _find_any(text, MACRO_STRONG_KEYWORDS)
    us_economy_hits = _find_any(text, US_ECONOMY_KEYWORDS)
    critical_macro_hits = _find_any(text, US_MACRO_CRITICAL_KEYWORDS)
    market_hits = _find_any(text, MARKET_KEYWORDS_V2)
    market_impact_hits = _find_any(text, MARKET_IMPACT_KEYWORDS)
    risk_hits = _find_any(text, RISK_KEYWORDS_V2)
    systemic_risk_hits = _find_any(text, SYSTEMIC_RISK_KEYWORDS)
    noise_hits = _find_any(text, NOISE_KEYWORDS_V2)
    research_noise_hit = _is_research_or_commentary_noise(text)

    crypto_contextual = bool(crypto_context_hits and _has_any(text, CRYPTO_STRONG_KEYWORDS + ["现货", "加密", "数字资产"]))
    crypto_regulatory_hit = _contains_crypto_regulatory_news(text)
    crypto_score = 0
    if crypto_hits:
        crypto_score += 7
    if crypto_contextual:
        crypto_score += 3
    if crypto_regulatory_hit:
        crypto_score = max(crypto_score, 8)

    macro_score = 0
    us_macro_context = _contains_us_context(text) or _has_any(
        text,
        ["非农", "NFP", "FOMC", "鲍威尔", "美联储", "美元指数", "美债收益率", "十年期美债", "10年期美债"],
    )
    critical_us_macro_hit = _contains_critical_us_macro(text)
    surprising_us_macro_hit = _contains_surprising_us_macro(text)
    if macro_hits and us_macro_context and not _is_non_us_macro(text):
        macro_score += 4
        if _contains_macro_market_impact(text):
            macro_score += 2
        if critical_us_macro_hit:
            macro_score += 3
        elif surprising_us_macro_hit:
            macro_score += 2

    market_score = 0
    if market_hits:
        market_score += 1
    if market_hits and market_impact_hits:
        market_score += 2

    risk_score = 0
    if risk_hits:
        risk_score += 2
    shipping_risk_hit = is_shipping_risk(text)
    if shipping_risk_hit:
        risk_score += 5
    systemic_risk_hit = _contains_systemic_risk(text)
    if systemic_risk_hit:
        risk_score += 7
    if risk_hits and _contains_geopolitical_market_impact(text):
        risk_score += 3
    if _has_any(text, ["导弹", "空袭", "袭击", "战争", "制裁", "恐袭"]):
        risk_score += 1
    us_iran_war_hit = _contains_us_iran_war_news(text)
    if us_iran_war_hit:
        risk_score += 4
        if _has_any(text, MIDDLE_EAST_MAJOR_ESCALATION_KEYWORDS):
            risk_score += 6
        elif _has_any(text, MIDDLE_EAST_MAJOR_DEESCALATION_KEYWORDS):
            risk_score += 6
        elif _has_any(text, MIDDLE_EAST_DEESCALATION_KEYWORDS):
            risk_score += 2

    policy_hits = _find_any(text, TRUMP_KEYWORDS)
    policy_score = 0
    trump_hit = _contains_trump_news(text)
    if trump_hit:
        policy_score += 7

    noise_score = 0
    if noise_hits:
        noise_score += 2
    if research_noise_hit:
        noise_score += 8
    if _is_plain_noise(text):
        noise_score += 5
    if _is_digest_message(msg):
        noise_score += 8
    if _is_low_value_locked_or_promo(msg):
        noise_score += 8

    us_economy_hit = _contains_us_economy_news(text)
    macro_pushworthy = critical_us_macro_hit or surprising_us_macro_hit or _contains_macro_market_impact(text)
    if us_economy_hit and macro_pushworthy and macro_score < threshold:
        macro_score += threshold - macro_score

    final_score = crypto_score + macro_score + market_score + risk_score + policy_score - noise_score
    hit_type = "pure_noise"
    decision = "skip"

    if crypto_score >= 7 and final_score >= threshold:
        hit_type = "direct_crypto_hit"
        decision = "push"
    elif trump_hit and policy_score >= 7 and final_score >= threshold:
        hit_type = "trump_hit"
        decision = "push"
    elif us_iran_war_hit and risk_score >= 7 and final_score >= threshold:
        hit_type = "us_iran_war_hit"
        decision = "push"
    elif shipping_risk_hit and risk_score >= 7 and final_score >= threshold:
        hit_type = "us_iran_war_hit"
        decision = "push"
    elif systemic_risk_hit and risk_score >= 7 and final_score >= threshold:
        hit_type = "systemic_risk_hit"
        decision = "push"
    elif macro_score >= 6 and (market_score > 0 or _contains_macro_market_impact(text)) and final_score >= threshold:
        hit_type = "macro_market_hit"
        decision = "push"
    elif us_economy_hit and macro_pushworthy and macro_score >= threshold and final_score >= threshold:
        hit_type = "us_economy_hit"
        decision = "push"
    elif risk_score >= 5 and _contains_geopolitical_market_impact(text) and final_score >= threshold:
        hit_type = "geopolitical_market_hit"
        decision = "push"

    if noise_score >= 7 and crypto_score < 7 and macro_score < 7 and risk_score < 7 and policy_score < 7:
        hit_type = "pure_noise"
        decision = "skip"
    if research_noise_hit and crypto_score < 7 and not systemic_risk_hit:
        hit_type = "pure_noise"
        decision = "skip"

    matched_keywords = _dedupe_text_parts(
        crypto_hits
        + crypto_context_hits
        + crypto_regulatory_hits
        + macro_hits
        + us_economy_hits
        + critical_macro_hits
        + market_hits
        + market_impact_hits
        + risk_hits
        + systemic_risk_hits
        + policy_hits
    )
    impact_tier = "critical" if final_score >= 12 else "high" if final_score >= threshold else "watch" if final_score >= 4 else "noise"
    return {
        "time": msg.get("time") or "",
        "text": content,
        "all_text": text,
        "fields": fields,
        "final_score": final_score,
        "score": final_score,
        "threshold": threshold,
        "hit_type": hit_type,
        "reason_type": hit_type,
        "matched_keywords": matched_keywords,
        "crypto_score": crypto_score,
        "macro_score": macro_score,
        "market_score": market_score,
        "risk_score": risk_score,
        "policy_score": policy_score,
        "noise_score": noise_score,
        "noise_hits": noise_hits,
        "research_noise": research_noise_hit,
        "impact_tier": impact_tier,
        "decision": decision,
        "push_reason": hit_type if decision == "push" else "",
        "skip_reason": "" if decision == "push" else hit_type,
    }


def build_push_text(msg: dict[str, Any], receive_time: str, score_result: dict[str, Any]) -> str:
    fields = score_result["fields"]
    score = int(score_result["score"])
    keywords = ", ".join(score_result["matched_keywords"][:12]) or "宏观事件"
    content = fields["body"] or fields["title"] or fields["meta"] or json.dumps(msg, ensure_ascii=False, sort_keys=True)

    return "\n".join(
        [
            "【宏观快讯｜影响BTC/ETH】",
            f"类型：{score_result.get('reason_type') or 'UNKNOWN'}",
            f"时间：{msg.get('time') or receive_time}",
            f"评分：{score}",
            f"命中：{keywords}",
            "",
            content,
            "",
        ]
    )


def _is_push_candidate(msg: dict[str, Any]) -> bool:
    if msg.get("type") in {"connected", "subscribed"}:
        return False
    if msg.get("event") == "flash-hot-changed":
        return False
    if msg.get("type") != "flash":
        return False
    if msg.get("action") != 1:
        return False
    extras = msg.get("extras")
    if isinstance(extras, dict) and extras.get("ad") is True:
        return False
    if _is_low_value_locked_or_promo(msg):
        return False
    if _is_digest_message(msg):
        return False
    return True


def _message_id(msg: dict[str, Any]) -> str:
    value = msg.get("id")
    return str(value).strip() if value is not None else ""


def _is_digest_message(msg: dict[str, Any]) -> bool:
    fields = extract_text_fields(msg)
    text = "\n".join((fields["title"], fields["body"], fields["meta"]))
    if any(marker in text for marker in ("新闻联播主要内容", "金十期货整理", "金十数据整理", "今日重点关注的财经数据与事件")):
        return True
    if len(re.findall(r"[①②③④⑤⑥⑦⑧⑨⑩]", text)) >= 4:
        return True
    numbered_items = re.findall(r"(?:^|[\n。；;])\s*\d{1,2}[.、]", text)
    return len(numbered_items) >= 5


def _score_keyword_group(
    label: str,
    keywords: list[str],
    text: str,
    points: int,
    reasons: list[str],
    matched_keywords: list[str],
) -> int:
    hits = _find_keywords(text, keywords)
    if not hits:
        return 0
    reasons.append(f"{label}:+{points}")
    matched_keywords.extend(hits)
    return points


def _find_keywords(text: str, keywords: list[str]) -> list[str]:
    if not text:
        return []
    lowered = text.lower()
    hits = []
    for keyword in keywords:
        if keyword == "非农" and not _has_valid_nonfarm_hit(text):
            continue
        if keyword.lower() in lowered:
            hits.append(keyword)
    return _dedupe_text_parts(hits)


def _has_valid_nonfarm_hit(text: str) -> bool:
    return any(not _is_south_africa_agri_nonfarm_hit(text, match.start()) for match in re.finditer("非农", text))


def _is_south_africa_agri_nonfarm_hit(text: str, start: int) -> bool:
    if start <= 0 or text[start - 1] != "南":
        return False
    next_text = text[start + len("非农") : start + len("非农") + 2]
    return next_text.startswith(("民", "业", "产", "场", "作"))


def _find_contextual_keywords(text: str, keywords: list[str], context_keywords: list[str]) -> list[str]:
    keyword_hits = _find_keywords(text, keywords)
    if not keyword_hits:
        return []
    context_hits = _find_keywords(text, context_keywords)
    if not context_hits:
        return []
    return _dedupe_text_parts(keyword_hits + context_hits)


def _find_allowed_us_macro_hits(text: str) -> list[str]:
    hits = _find_keywords(text, US_MACRO_DATA_KEYWORDS)
    if not hits:
        return []

    always_allowed = {
        "核心CPI",
        "核心PCE",
        "CPI",
        "PCE",
        "非农",
        "NFP",
        "ADP",
        "初请失业金",
        "续请失业金",
        "失业率",
        "平均时薪",
        "JOLTS",
        "职位空缺",
        "ISM",
    }
    allowed = [hit for hit in hits if hit in always_allowed]
    broad_hits = [hit for hit in hits if hit not in always_allowed]
    data_context = _find_keywords(text, ["公布", "数据", "指数", "初值", "终值", "预期", "高于", "低于", "录得", "年率", "月率", "报告"])
    if broad_hits and data_context:
        allowed.extend(broad_hits)
    return _dedupe_text_parts(allowed)


def _is_middle_east_geo_combo(text: str, actor_hits: list[str], action_hits: list[str]) -> bool:
    if not actor_hits or not action_hits:
        return False

    broad_us_only = set(actor_hits).issubset({"美国", "美军"})
    if broad_us_only:
        middle_east_context = _find_keywords(
            text,
            [
                "伊朗",
                "以色列",
                "黎巴嫩",
                "真主党",
                "哈马斯",
                "胡塞武装",
                "也门",
                "红海",
                "霍尔木兹",
                "阿曼",
                "阿曼湾",
                "波斯湾",
                "中东",
                "加沙",
            ],
        )
        return bool(middle_east_context)

    return True


def _is_low_value_locked_or_promo(msg: dict[str, Any]) -> bool:
    fields = extract_text_fields(msg)
    text = " ".join((fields["title"], fields["body"], fields["meta"]))
    data = msg.get("data")
    if isinstance(data, dict) and data.get("lock") is True:
        return True
    return any(marker in text for marker in ("VIP专享快讯", "解锁直达", "正在直播", "点击进入直播间", "Live分析"))


def is_shipping_risk(text: str) -> bool:
    return bool(_find_keywords(text, SHIPPING_RISK_ACTORS) and _find_keywords(text, SHIPPING_RISK_ACTIONS))


def is_middle_east_risk(text: str) -> bool:
    actor_hits = _find_keywords(text, GEOPOLITICAL_SUBJECT_KEYWORDS)
    action_hits = _find_keywords(text, GEOPOLITICAL_ACTION_KEYWORDS)
    return _is_middle_east_geo_combo(text, actor_hits, action_hits)


def is_trump_policy(text: str) -> bool:
    return bool(_find_keywords(text, TRUMP_POLICY_SUBJECT_KEYWORDS) and _find_keywords(text, TRUMP_POLICY_ACTION_KEYWORDS))


def is_direct_crypto(text: str) -> bool:
    direct_crypto_hits = _find_keywords(text, DIRECT_CRYPTO_KEYWORDS)
    contextual_crypto_hits = _find_contextual_keywords(text, CONTEXTUAL_CRYPTO_KEYWORDS, CRYPTO_CONTEXT_KEYWORDS)
    return bool(direct_crypto_hits or contextual_crypto_hits)


def is_us_macro(text: str) -> bool:
    hit_macro_keywords = bool(_find_keywords(text, MACRO_TERMS + US_MACRO_DATA_KEYWORDS + FED_EVENT_KEYWORDS))
    if not hit_macro_keywords:
        return False
    has_us_context = bool(_find_keywords(text, US_CONTEXT))
    hit_us_specific_macro = bool(_find_keywords(text, US_SPECIFIC_MACRO))
    return has_us_context or hit_us_specific_macro


def _is_non_us_macro(text: str) -> bool:
    macro_hits = _find_keywords(text, MACRO_TERMS + US_MACRO_DATA_KEYWORDS + FED_EVENT_KEYWORDS)
    if not macro_hits:
        return False
    if _find_keywords(text, NON_US_MACRO_OVERRIDE):
        return False
    if not _find_keywords(text, NON_US_MACRO_CONTEXT):
        return False
    if is_middle_east_risk(text) or is_shipping_risk(text) or is_direct_crypto(text) or is_trump_policy(text):
        return False
    return not is_us_macro(text)


def _find_market_move_hits(text: str) -> list[str]:
    if not text:
        return []

    hits: list[str] = []
    market_targets = _find_keywords(text, MARKET_MOVE_TARGET_KEYWORDS)
    if not market_targets:
        return []

    for target in market_targets:
        if target in {"美元指数", "DXY"}:
            actions = _find_keywords(text, MARKET_MOVE_ACTION_KEYWORDS)
        elif target in {
            "美债收益率",
            "美国国债收益率",
            "10年期美债",
            "2年期美债",
            "30年期美债",
            "10年期收益率",
            "2年期收益率",
            "30年期收益率",
            "美国国债",
            "国债收益率",
        }:
            actions = _find_keywords(
                text,
                ["大涨", "大跌", "暴涨", "暴跌", "下滑", "回落", "走低", "走高", "跌回", "升至", "跌至", "突破", "跌破", "升破"],
            )
        elif target in {"纳指", "标普"}:
            actions = _find_keywords(text, ["跳水", "暴跌", "大跌", "大涨", "暴涨", "拉升", "走高", "走低", "创日内新高", "创日内新低"])
        elif target in {"VIX", "恐慌指数"}:
            actions = _find_keywords(text, ["飙升", "大涨", "暴涨", "拉升"])
        elif target == "黄金":
            actions = _find_keywords(text, ["飙升", "跳水", "大涨", "大跌", "暴涨", "暴跌", "创历史新高", "创阶段新高", "创日内新高", "创日内新低"])
        elif target == "原油":
            actions = _find_keywords(text, ["飙升", "大涨", "大跌", "暴涨", "暴跌", "跳水", "拉升", "回落"])
        else:
            actions = _find_keywords(text, MARKET_MOVE_ACTION_KEYWORDS)

        if actions:
            hits.extend([target] + actions)

    return _dedupe_text_parts(hits)


def _is_plain_company_news(text: str) -> bool:
    company_words = ["公司", "董事长", "任命", "卸任", "公告", "股份", "股东", "董事会"]
    high_impact_words = (
        US_MACRO_DATA_KEYWORDS
        + FED_EVENT_KEYWORDS
        + GEOPOLITICAL_ACTION_KEYWORDS
        + TRUMP_POLICY_ACTION_KEYWORDS
        + DIRECT_CRYPTO_KEYWORDS
    )
    return bool(_find_keywords(text, company_words)) and not bool(_find_keywords(text, high_impact_words))


def _build_skip_reason(reasons: list[str], noise_hits: list[str]) -> str:
    if noise_hits:
        return "noise:" + ",".join(_dedupe_text_parts(noise_hits)[:8])
    if reasons:
        return ";".join(reasons)
    return "score_below_threshold"


def _primary_reason_type(reason_types: list[str]) -> str:
    priority = [
        "US_MACRO",
        "FED",
        "ENERGY_SHIPPING_RISK",
        "MIDDLE_EAST_RISK",
        "TRUMP_POLICY",
        "CRYPTO_DIRECT",
        "MARKET_MOVE",
    ]
    for reason_type in priority:
        if reason_type in reason_types:
            return reason_type
    return "UNKNOWN"


def _all_positive_keywords() -> list[str]:
    return _dedupe_text_parts(
        DIRECT_CRYPTO_KEYWORDS
        + CONTEXTUAL_CRYPTO_KEYWORDS
        + US_MACRO_DATA_KEYWORDS
        + FED_EVENT_KEYWORDS
        + GEOPOLITICAL_SUBJECT_KEYWORDS
        + GEOPOLITICAL_ACTION_KEYWORDS
        + SHIPPING_RISK_ACTORS
        + SHIPPING_RISK_ACTIONS
        + TRUMP_POLICY_SUBJECT_KEYWORDS
        + TRUMP_POLICY_ACTION_KEYWORDS
        + MARKET_MOVE_TARGET_KEYWORDS
        + MARKET_MOVE_ACTION_KEYWORDS
    )


def _dedupe_text_parts(parts: list[str]) -> list[str]:
    seen = set()
    result = []
    for part in parts:
        normalized = str(part).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result




def is_push_candidate(msg: dict[str, Any]) -> bool:
    return _is_push_candidate(msg)


def message_id(msg: dict[str, Any]) -> str:
    return _message_id(msg)
