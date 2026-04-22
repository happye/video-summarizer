from llm.ollama_client import ollama_generate
from llm.kimi_client import kimi_generate
from llm.deepseek_client import deepseek_generate

class LLMAdapter:
    def __init__(self, provider):
        self.provider = provider
    
    def generate(self, prompt):
        if self.provider == "ollama":
            return ollama_generate(prompt)
        elif self.provider == "kimi":
            return kimi_generate(prompt)
        elif self.provider == "deepseek":
            return deepseek_generate(prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
