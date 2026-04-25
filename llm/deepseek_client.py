from llm.base_client import BaseLLMClient
from config import DEEPSEEK_API_KEY

class DeepSeekClient(BaseLLMClient):
    """DeepSeek API Client

    Official API Docs: https://api-docs.deepseek.com/api/create-chat-completion/
    Base URL: https://api.deepseek.com/chat/completions
    Models: deepseek-v4-pro, deepseek-chat
    Context Length: 64K tokens
    """

    def __init__(self, max_context_messages=30, max_tokens_per_request=60000):
        super().__init__(
            api_key=DEEPSEEK_API_KEY,
            model="deepseek-v4-pro",
            api_url="https://api.deepseek.com/chat/completions",
            max_context_messages=max_context_messages,
            max_tokens_per_request=max_tokens_per_request,
            max_retries=5,
            timeout=180,
            retry_delay=5
        )

    def _build_request_data(self):
        """DeepSeek 特定的请求体构建"""
        return {
            "model": self.model,
            "messages": self.messages,
            "temperature": 0.7,
            "max_tokens": 4096,
            "stream": False
        }


def deepseek_generate(prompt):
    """Backward compatibility function"""
    client = DeepSeekClient()
    return client.generate(prompt, reset_context=True)
