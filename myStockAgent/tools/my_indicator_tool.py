"""
技术指标工具 - MACD / 成交量分析 / 止损位计算
复用 my_ma_tool 的K线数据接口
"""
import pathlib
from tools.my_ma_tool import _fetch_kline, _normalize_code, _calc_ma


# ========== MACD ==========
def _calc_ema(data: list, period: int) -> list:
    """计算指数移动平均"""
    ema = [0.0] * len(data)
    ema[0] = data[0]
    k = 2 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = data[i] * k + ema[i - 1] * (1 - k)
    return ema


def calc_macd(closes: list, fast: int = 12, slow: int = 26, signal: int = 9):
    """计算MACD指标，返回 (dif_list, dea_list, macd_bar_list)"""
    ema_fast = _calc_ema(closes, fast)
    ema_slow = _calc_ema(closes, slow)
    dif = [f - s for f, s in zip(ema_fast, ema_slow)]
    dea = _calc_ema(dif, signal)
    macd_bar = [2 * (d - e) for d, e in zip(dif, dea)]
    return dif, dea, macd_bar


def analyze_macd(code: str) -> str:
    """MACD分析：DIF/DEA金叉死叉 + 零轴位置 + 柱状图趋势"""
    klines = _fetch_kline(code, days=60)
    if len(klines) < 30:
        return f"K线数据不足(仅{len(klines)}条)，无法计算MACD"

    closes = [k["close"] for k in klines]
    dif, dea, macd_bar = calc_macd(closes)

    cur_dif = dif[-1]
    cur_dea = dea[-1]
    cur_bar = macd_bar[-1]
    prev_bar = macd_bar[-2]

    # 金叉死叉判断
    if dif[-2] <= dea[-2] and cur_dif > cur_dea:
        cross = "MACD金叉(DIF上穿DEA，买入信号)"
    elif dif[-2] >= dea[-2] and cur_dif < cur_dea:
        cross = "MACD死叉(DIF下穿DEA，卖出信号)"
    elif cur_dif > cur_dea:
        cross = "DIF在DEA上方(多头持有)"
    else:
        cross = "DIF在DEA下方(空头观望)"

    # 零轴位置
    if cur_dif > 0 and cur_dea > 0:
        axis = "零轴上方(强势区域)"
    elif cur_dif < 0 and cur_dea < 0:
        axis = "零轴下方(弱势区域)"
    else:
        axis = "零轴附近(多空转换)"

    # 柱状图趋势
    if cur_bar > 0 and cur_bar > prev_bar:
        bar_trend = "红柱放大(多头增强)"
    elif cur_bar > 0 and cur_bar < prev_bar:
        bar_trend = "红柱缩短(多头减弱)"
    elif cur_bar < 0 and cur_bar < prev_bar:
        bar_trend = "绿柱放大(空头增强)"
    elif cur_bar < 0 and cur_bar > prev_bar:
        bar_trend = "绿柱缩短(空头减弱，可能见底)"
    else:
        bar_trend = "柱状图持平"

    result = (
        f"--- MACD ---\n"
        f"DIF: {cur_dif:.3f}  DEA: {cur_dea:.3f}  MACD柱: {cur_bar:.3f}\n"
        f"信号: {cross}\n"
        f"位置: {axis}\n"
        f"柱状: {bar_trend}"
    )
    return result


# ========== 成交量分析 ==========
def analyze_volume(code: str) -> str:
    """成交量分析：量比、放量/缩量判断、量价配合"""
    klines = _fetch_kline(code, days=30)
    if len(klines) < 10:
        return "K线数据不足，无法分析成交量"

    volumes = [k["volume"] for k in klines]
    closes = [k["close"] for k in klines]

    cur_vol = volumes[-1]
    avg_5 = sum(volumes[-6:-1]) / 5   # 前5日均量(不含今天)
    avg_10 = sum(volumes[-11:-1]) / 10 if len(volumes) >= 11 else avg_5

    # 量比
    vol_ratio = cur_vol / avg_5 if avg_5 > 0 else 0

    # 放量/缩量判断
    if vol_ratio >= 2.0:
        vol_state = "显著放量(量比{:.2f})".format(vol_ratio)
    elif vol_ratio >= 1.3:
        vol_state = "温和放量(量比{:.2f})".format(vol_ratio)
    elif vol_ratio >= 0.7:
        vol_state = "成交量平稳(量比{:.2f})".format(vol_ratio)
    else:
        vol_state = "明显缩量(量比{:.2f})".format(vol_ratio)

    # 量价配合
    price_up = closes[-1] > closes[-2]
    vol_up = cur_vol > avg_5

    if price_up and vol_up:
        vp = "量价齐升(健康上涨)"
    elif price_up and not vol_up:
        vp = "价升量缩(上涨乏力，注意回调)"
    elif not price_up and vol_up:
        vp = "放量下跌(抛压较重)"
    else:
        vp = "缩量下跌(恐慌情绪不重，可能企稳)"

    result = (
        f"--- 成交量 ---\n"
        f"今日: {cur_vol:.0f}手  5日均量: {avg_5:.0f}手  量比: {vol_ratio:.2f}\n"
        f"状态: {vol_state}\n"
        f"量价: {vp}"
    )
    return result


# ========== 止损位计算 ==========
def calc_stop_loss(code: str) -> str:
    """计算建议止损位：基于MA20支撑、近10日低点、固定比例三重参考"""
    klines = _fetch_kline(code, days=30)
    if len(klines) < 20:
        return "K线数据不足，无法计算止损位"

    closes = [k["close"] for k in klines]
    lows = [k["low"] for k in klines]
    price = closes[-1]

    # 方法1: MA20支撑位
    ma20 = _calc_ma(closes, 20)[-1]

    # 方法2: 近10日最低点
    low_10 = min(lows[-10:])

    # 方法3: 固定比例(成本价-7%)
    fixed_pct = price * 0.93

    # 综合止损位: 取MA20和近10日低点中较高的(更保守)
    support = max(ma20, low_10)
    stop_loss = max(support, fixed_pct)  # 不低于-7%
    loss_pct = (price - stop_loss) / price * 100

    result = (
        f"--- 止损参考 ---\n"
        f"当前价: {price:.2f}\n"
        f"MA20支撑: {ma20:.2f}\n"
        f"近10日低点: {low_10:.2f}\n"
        f"固定止损(-7%): {fixed_pct:.2f}\n"
        f"建议止损位: {stop_loss:.2f} (距当前 -{loss_pct:.1f}%)\n"
        f"提示: 跌破止损位建议减仓或离场，严格执行纪律"
    )
    return result


# ========== 综合技术分析(一次调用全部) ==========
def full_technical_analysis(code: str) -> str:
    """综合技术分析：MACD + 成交量 + 止损位，一次返回全部结果"""
    parts = []
    parts.append(analyze_macd(code))
    parts.append("")
    parts.append(analyze_volume(code))
    parts.append("")
    parts.append(calc_stop_loss(code))
    return "\n".join(parts)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
    print(full_technical_analysis("600519"))
