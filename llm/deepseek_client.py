from llm.base_client import BaseLLMClient
from config import DEEPSEEK_API_KEY

class DeepSeekClient(BaseLLMClient):
    """DeepSeek API Client

    Official API Docs: https://api-docs.deepseek.com/api/create-chat-completion/
    Base URL: https://api.deepseek.com/chat/completions
    Models: deepseek-v4-pro, deepseek-v4-flash
    Context Length: 1M tokens, Max Output: 384K tokens (v4 series)
    """

    def __init__(self, max_context_messages=100, max_tokens_per_request=350000):
        super().__init__(
            api_key=DEEPSEEK_API_KEY,
            model="deepseek-v4-pro",
            api_url="https://api.deepseek.com/chat/completions",
            max_context_messages=max_context_messages,
            max_tokens_per_request=max_tokens_per_request,
            max_retries=5,
            timeout=300,
            retry_delay=5
        )
        self.thinking_enabled = True

    def _build_request_data(self):
        data = {
            "model": self.model,
            "messages": self.messages,
            "temperature": 0.7,
            "max_tokens": 384000,
            "stream": False
        }
        if not self.thinking_enabled:
            data["thinking"] = {"type": "disabled"}
        return data


def deepseek_generate(prompt):
    """Backward compatibility function"""
    client = DeepSeekClient()
    return client.generate(prompt, reset_context=True)
