"""
A股均线分析工具 - MA5/MA10/MA20 金叉死叉判断
数据源: 腾讯财经日K接口(前复权)
"""
import requests


def _normalize_code(code: str) -> str:
    """标准化股票代码，自动补全交易所前缀。支持 600916 / sh600916 / 600916.SH 等格式"""
    code = code.strip().lower()
    # 去掉 .sh / .sz 后缀 (如 600916.sh -> 600916)
    if code.endswith((".sh", ".sz")):
        code = code[:-3]
    if not code.startswith(("sh", "sz")):
        if code.startswith(("6", "9")):
            code = "sh" + code
        elif code.startswith(("0", "2", "3")):
            code = "sz" + code
    return code


def _fetch_kline(code: str, days: int = 30) -> list:
    """获取日K线数据，返回 [{date, open, close, high, low, volume}, ...]"""
    code = _normalize_code(code)
    if not code.startswith(("sh", "sz")):
        return []

    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,{days},qfq"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
    except Exception:
        return []

    # 解析: data -> {code} -> "qfqday" or "day"
    stock_data = data.get("data", {}).get(code, {})
    klines = stock_data.get("qfqday") or stock_data.get("day") or []

    result = []
    for k in klines:
        if len(k) >= 6:
            result.append({
                "date": k[0],
                "open": float(k[1]),
                "close": float(k[2]),
                "high": float(k[3]),
                "low": float(k[4]),
                "volume": float(k[5]),
            })
    return result


def _calc_ma(closes: list, period: int) -> list:
    """计算移动平均线，返回与closes等长的列表(前period-1个为None)"""
    ma = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        ma[i] = sum(closes[i - period + 1: i + 1]) / period
    return ma


def _detect_cross(ma_short: list, ma_long: list) -> str:
    """检测最近一次金叉/死叉(看最后两天的交叉)"""
    valid = [(s, l) for s, l in zip(ma_short, ma_long) if s is not None and l is not None]
    if len(valid) < 2:
        return "数据不足"

    prev_s, prev_l = valid[-2]
    curr_s, curr_l = valid[-1]

    if prev_s <= prev_l and curr_s > curr_l:
        return "金叉(短期上穿长期，买入信号)"
    elif prev_s >= prev_l and curr_s < curr_l:
        return "死叉(短期下穿长期，卖出信号)"
    elif curr_s > curr_l:
        return "短期在长期上方(多头)"
    else:
        return "短期在长期下方(空头)"


def analyze_ma(code: str) -> str:
    """
    均线分析。输入股票代码(如600519)，返回MA5/MA10/MA20数值、
    金叉死叉信号、多空排列判断和买卖建议。
    """
    klines = _fetch_kline(code, days=30)
    if len(klines) < 20:
        return f"K线数据不足(仅{len(klines)}条)，无法计算MA20"

    closes = [k["close"] for k in klines]
    latest = klines[-1]

    ma5 = _calc_ma(closes, 5)
    ma10 = _calc_ma(closes, 10)
    ma20 = _calc_ma(closes, 20)

    cur_ma5 = ma5[-1]
    cur_ma10 = ma10[-1]
    cur_ma20 = ma20[-1]

    # 交叉信号
    cross_5_10 = _detect_cross(ma5, ma10)
    cross_5_20 = _detect_cross(ma5, ma20)
    cross_10_20 = _detect_cross(ma10, ma20)

    # 多空排列
    if cur_ma5 > cur_ma10 > cur_ma20:
        trend = "多头排列(MA5>MA10>MA20)，趋势向好"
    elif cur_ma5 < cur_ma10 < cur_ma20:
        trend = "空头排列(MA5<MA10<MA20)，趋势走弱"
    else:
        trend = "均线交织，方向不明"

    # 价格与均线关系
    price = latest["close"]
    above_count = sum([price > cur_ma5, price > cur_ma10, price > cur_ma20])
    if above_count == 3:
        pos = "股价站上所有均线，强势"
    elif above_count == 0:
        pos = "股价跌破所有均线，弱势"
    else:
        pos = f"股价在{above_count}条均线上方"

    # 综合建议
    buy_signals = 0
    if "金叉" in cross_5_10 or "多头" in cross_5_10: buy_signals += 1
    if "金叉" in cross_5_20 or "多头" in cross_5_20: buy_signals += 1
    if "多头" in trend: buy_signals += 1
    if above_count == 3: buy_signals += 1

    sell_signals = 0
    if "死叉" in cross_5_10 or "空头" in cross_5_10: sell_signals += 1
    if "死叉" in cross_5_20 or "空头" in cross_5_20: sell_signals += 1
    if "空头" in trend: sell_signals += 1
    if above_count == 0: sell_signals += 1

    if buy_signals >= 3:
        advice = "综合偏多，可考虑逢低买入"
    elif sell_signals >= 3:
        advice = "综合偏空，建议观望或减仓"
    else:
        advice = "信号不一致，建议等待方向明确再操作"

    result = (
        f"【{code} 均线分析】({latest['date']})\n"
        f"收盘价: {price}\n"
        f"MA5:  {cur_ma5:.2f}\n"
        f"MA10: {cur_ma10:.2f}\n"
        f"MA20: {cur_ma20:.2f}\n"
        f"\n--- 交叉信号 ---\n"
        f"MA5/MA10: {cross_5_10}\n"
        f"MA5/MA20: {cross_5_20}\n"
        f"MA10/MA20: {cross_10_20}\n"
        f"\n--- 趋势判断 ---\n"
        f"排列: {trend}\n"
        f"位置: {pos}\n"
        f"\n--- 综合建议 ---\n"
        f"{advice}"
    )
    return result


if __name__ == "__main__":
    print(analyze_ma("600519"))
    print()
    print(analyze_ma("000001"))
