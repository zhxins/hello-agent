import os
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict


load_dotenv(Path(__file__).parent / ".env")

class HelloAgentLLM:
    """
    "Hello, Agents"定制的客户端
    用于调用任何兼容openai接口的服务，并默认使用流式响应
    """
    def __init__(self, model: str = None, api_key: str = None, base_url: str = None, timeout: int = None):
        self.model = model or os.getenv("MODEL_ID")
        apiKey = api_key or os.getenv("API_KEY")
        baseUrl = base_url or os.getenv("BASE_URL")
        timeout = timeout or int(os.getenv("TIMEOUT", 60))

        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("请检查环境变量是否正确设置")
        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)


    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        """
        调用模型，并返回完整的流式响应
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            reseponse = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=temperature,
            )

            # 处理流式响应
            print("✅ 大语言模型响应成功:")
            collected_content = []
            for chunk in reseponse:
                if not chunk.choices:
                    continue

                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_content.append(content)
            print()
            return "".join(collected_content)
        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return None

if __name__ == "__main__":
    # 1. 初始化LLM客户端 (请确保你的 .env 和 llm_client.py 文件配置正确)
    try:
        llm_client = HelloAgentLLM()
    # 2. 创建一个提示词，并调用模型生成响应
        message = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "写一个快速排序算法"}
        ]
        response = llm_client.think(message)
        print(response)
    except Exception as e:
        print(f"初始化LLM客户端时出错: {e}")
        exit()
