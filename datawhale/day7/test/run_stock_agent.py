"""
ReAct股票助手 - 独立运行版
基于DeepSeek API + 腾讯行情，演示完整的 Thought -> Action -> Observation 循环
使用框架封装的 HelloAgentsLLM 调用LLM
"""
import os
import re
import sys
import pathlib

from dotenv import load_dotenv

# 加载.env
load_dotenv(pathlib.Path(__file__).parent.parent / ".env")

# 导入框架core和股票工具
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from core.llm import HelloAgentsLLM
from my_stock_tool import query_stock
from my_ma_tool import analyze_ma


# ========== 工具注册表 ==========
TOOLS = {
    "stock_query": {
        "func": query_stock,
        "description": "查询A股实时行情。输入股票代码(如600519、000001)，返回当前价格、涨跌幅等信息。",
    },
    "ma_analysis": {
        "func": analyze_ma,
        "description": "均线分析。输入股票代码，返回MA5/MA10/MA20数值、金叉死叉信号、多空排列和买卖建议。",
    },
}


def get_tools_description() -> str:
    """生成工具描述文本，嵌入prompt"""
    lines = []
    for name, info in TOOLS.items():
        lines.append(f"- {name}: {info['description']}")
    return "\n".join(lines)


# ========== ReAct Prompt模板 ==========
REACT_PROMPT = """你是一个智能股票助手。你可以使用以下工具：

{tools}

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

用户问题: {question}

{history}"""


# ========== LLM实例（使用框架封装的HelloAgentsLLM） ==========
llm = HelloAgentsLLM(
    provider="deepseek",
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL", "https://api.deepseek.com"),
    model=os.getenv("LLM_MODEL_ID", "deepseek-chat"),
    temperature=0.1,  # 低温度，让ReAct格式输出更稳定
    max_tokens=1024,
)


def call_llm(prompt: str) -> str:
    """通过HelloAgentsLLM调用DeepSeek"""
    messages = [{"role": "user", "content": prompt}]
    return llm.invoke(messages)


# ========== 解析LLM输出 ==========
def parse_action(text: str):
    """从LLM输出中提取Action"""
    match = re.search(r"Action:\s*(.+)", text)
    if not match:
        return None, None
    action_str = match.group(1).strip()

    # 匹配 tool_name[input]
    m = re.match(r"(\w+)\[(.*)\]", action_str, re.DOTALL)
    if m:
        return m.group(1), m.group(2)
    return action_str, ""


# ========== ReAct主循环 ==========
def run_agent(question: str, max_steps: int = 5, verbose: bool = True):
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
    print("  ReAct 股票助手 (输入 quit 退出)")
    print("  示例: 贵州茅台现在多少钱？")
    print("  示例: 帮我看看平安银行和招商银行哪个涨得多")
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
