from day4_memory import RefectionAgent


class MyReflectionAgent(RefectionAgent):
    """
    一个自定义的 Reflection 智能体，用于处理特定的任务。
    """
    def __init__(self, name: str, llm_client, max_iterations=3):
        super().__init__(llm_client, max_iterations)