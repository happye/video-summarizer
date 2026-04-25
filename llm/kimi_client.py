from llm.base_client import BaseLLMClient
from config import KIMI_API_KEY

class KimiClient(BaseLLMClient):
    """Kimi (Moonshot AI) Client"""

    def __init__(self, max_context_messages=30, max_tokens_per_request=80000):
        super().__init__(
            api_key=KIMI_API_KEY,
            model="kimi-k2.6",
            api_url="https://api.moonshot.cn/v1/chat/completions",
            max_context_messages=max_context_messages,
            max_tokens_per_request=max_tokens_per_request,
            max_retries=5,
            timeout=180,
            retry_delay=5
        )

    def _build_request_data(self):
        """Kimi 特定的请求体构建"""
        return {
            "model": self.model,
            "messages": self.messages,
            "timeout": self.timeout
        }


def kimi_generate(prompt):
    """Backward compatibility function"""
    client = KimiClient()
    return client.generate(prompt, reset_context=True)
