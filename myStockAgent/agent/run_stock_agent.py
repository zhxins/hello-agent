"""
ReAct股票助手
基于DeepSeek API + 腾讯行情，调用完整的 Thought -> Action -> Observation 循环
使用框架封装的 HelloAgentsLLM 调用LLM
"""
import os
import re

from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM

load_dotenv()

from tools.my_stock_tool import query_stock
from tools.my_ma_tool import analyze_ma
from tools.my_indicator_tool import full_technical_analysis


# ========== 组合工具：行情 + 均线 + MACD + 量价 + 止损 ==========
def stock_full_analysis(code: str) -> str:
    """个股综合技术分析：实时行情 + 均线 + MACD + 成交量 + 止损位，一次全出。"""
    quote = query_stock(code)
    ma = analyze_ma(code)
    tech = full_technical_analysis(code)
    return f"{quote}\n\n{ma}\n\n{tech}"


# ========== 工具注册表 ==========
TOOLS = {
    "stock_analysis": {
        "func": stock_full_analysis,
        "description": "个股综合分析(默认使用)。输入股票代码，返回实时行情+均线+MACD+量价+止损位+买卖建议。",
    },
    "stock_query": {
        "func": query_stock,
        "description": "仅查询实时行情(价格/涨跌/成交量)。输入股票代码。",
    },
    "ma_analysis": {
        "func": analyze_ma,
        "description": "仅做均线分析(MA5/MA10/MA20金叉死叉)。输入股票代码。",
    },
}


def get_tools_description() -> str:
    """生成工具描述文本，嵌入prompt"""
    lines = []
    for name, info in TOOLS.items():
        lines.append(f"- {name}: {info['description']}")
    return "\n".join(lines)


# ========== ReAct Prompt模板 ==========
REACT_PROMPT = """你是一个专业的A股投资助手。你可以使用以下工具：

{tools}

重要规则：
- 当用户询问任何个股时，默认使用 stock_analysis 工具，一次性获取行情+均线分析+买卖建议
- 只有用户明确只要价格或只要均线时，才用单独的 stock_query 或 ma_analysis
- 对比多只股票时，对每只分别调用 stock_analysis

请严格按照以下格式回答：

Thought: 我需要思考如何回答用户的问题
Action: tool_name[tool_input]
Observation: (工具返回的结果，由系统填写)
... (可以重复多轮 Thought/Action/Observation)
Thought: 我现在知道最终答案了
Action: Finish[最终回答内容]

注意：
- 每次只能调用一个工具
- Action格式必须是 tool_name[输入参数]
- 如果不需要工具，直接 Thought + Action: Finish[回答]
- 不要自己编写Observation，输出Action后立即停止，Observation由系统填写

用户问题: {question}

{history}"""


# ========== LLM实例（使用框架封装的HelloAgentsLLM） ==========
llm = HelloAgentsLLM(
    provider="deepseek",
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL", "https://api.deepseek.com"),
    model=os.getenv("LLM_MODEL_ID", "deepseek-chat"),
    temperature=0.1,  # 低温度，让ReAct格式输出更稳定
    max_tokens=2048,
)


def call_llm(prompt: str) -> str:
    """HelloAgentsLLM调用"""
    messages = [{"role": "user", "content": prompt}]
    return llm.invoke(messages)


# ========== 解析LLM输出 ==========
def parse_action(text: str):
    """从LLM输出中提取Action"""
    match = re.search(r"Action:\s*(.+)", text, re.DOTALL)
    if not match:
        return None, None
    action_str = match.group(1).strip()

    # 匹配 tool_name[input]
    m = re.match(r"(\w+)\[(.*)\]", action_str, re.DOTALL)
    if m:
        return m.group(1), m.group(2)

    # 兜底: Finish[内容被截断(没有闭合])，仍视为结束
    if action_str.startswith("Finish["):
        return "Finish", action_str[7:]

    return action_str, ""


# ========== ReAct主循环 ==========
def run_agent(question: str, max_steps: int = 3, verbose: bool = True):
    """运行ReAct Agent"""
    history = ""
    tools_desc = get_tools_description()

    if verbose:
        print(f"\n{'='*50}")
        print(f"问题: {question}")
        print(f"{'='*50}")

    for step in range(max_steps):
        # 构建prompt
        prompt = REACT_PROMPT.format(
            tools=tools_desc,
            question=question,
            history=history,
        )

        # 调用LLM
        llm_output = call_llm(prompt)

        if verbose:
            print(f"\n--- Step {step + 1} ---")
            print(llm_output)

        # 解析Action
        tool_name, tool_input = parse_action(llm_output)

        if tool_name is None:
            # LLM没按格式输出，把整段当最终回答
            return llm_output

        # 判断是否结束
        if tool_name == "Finish":
            if verbose:
                print(f"\n{'='*50}")
                print(f"最终回答: {tool_input}")
            return tool_input

        # 执行工具
        if tool_name in TOOLS:
            try:
                observation = TOOLS[tool_name]["func"](tool_input)
            except Exception as e:
                observation = f"工具执行出错: {e}"
        else:
            observation = f"未知工具: {tool_name}，可用工具: {list(TOOLS.keys())}"

        if verbose:
            print(f"\nObservation: {observation}")

        # 追加到history
        history += f"\n{llm_output}\nObservation: {observation}\n"

    return "达到最大步数限制，未能得出最终答案。"


# ========== 交互式运行 ==========
if __name__ == "__main__":
    print("=" * 50)
    print("  AI 股票助手 (输入 quit 退出)")
    print("  示例: 贵州茅台现在多少钱？")
    print("  示例: 帮我分析平安银行的买卖建议")
    print("=" * 50)

    while True:
        try:
            question = input("\n你: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        answer = run_agent(question)
