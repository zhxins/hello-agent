"""
A股实时行情查询工具 - 基于腾讯财经API
用法: 输入股票代码(如 600519、000001、sh600519)，返回实时行情
"""
import requests
import pathlib


def query_stock(code: str) -> str:
    """查询A股实时行情。输入股票代码，如 600519(贵州茅台)、000001(平安银行)。"""
    code = code.strip().lower()

    # 自动补全交易所前缀
    if not code.startswith(("sh", "sz")):
        if code.startswith(("6", "9")):
            code = "sh" + code
        elif code.startswith(("0", "2", "3")):
            code = "sz" + code
        else:
            return f"无法识别的股票代码: {code}"

    url = f"http://qt.gtimg.cn/q={code}"
    try:
        resp = requests.get(url, timeout=10)
        resp.encoding = "gbk"
        text = resp.text.strip()
    except Exception as e:
        return f"请求失败: {e}"

    # 解析: v_sh600519="1~贵州茅台~600519~2050.00~..."
    if '="' not in text:
        return f"未找到股票 {code} 的数据"

    data = text.split('="')[1].rstrip('";')
    fields = data.split("~")

    if len(fields) < 45:
        return f"数据格式异常，字段数不足: {len(fields)}"

    # 腾讯API字段索引(常用的)
    name = fields[1]
    stock_code = fields[2]
    price = fields[3]        # 当前价
    prev_close = fields[4]   # 昨收
    open_price = fields[5]   # 今开
    volume = fields[6]       # 成交量(手)
    high = fields[33]        # 最高
    low = fields[34]         # 最低
    change = fields[31]      # 涨跌额
    change_pct = fields[32]  # 涨跌幅%
    turnover = fields[37]    # 成交额(万)
    pe = fields[39]          # 市盈率
    market_cap = fields[45] if len(fields) > 45 else "N/A"  # 总市值(亿)

    result = (
        f"【{name}】({stock_code})\n"
        f"当前价: {price}  涨跌: {change} ({change_pct}%)\n"
        f"今开: {open_price}  最高: {high}  最低: {low}  昨收: {prev_close}\n"
        f"成交量: {volume}手  成交额: {turnover}万\n"
        f"市盈率: {pe}  总市值: {market_cap}亿"
    )
    return result


def create_stock_registry():
    """创建包含股票查询工具的ToolRegistry（配合hello-agents框架使用）"""
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
    from tools.registry import ToolRegistry

    registry = ToolRegistry()
    registry.register_function(
        name="stock_query",
        description="查询A股实时行情。输入股票代码(如600519、000001)，返回当前价格、涨跌幅等信息。",
        func=query_stock,
    )
    return registry


if __name__ == "__main__":
    print(query_stock("600519"))
    print()
    print(query_stock("000001"))
