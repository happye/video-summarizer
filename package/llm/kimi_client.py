import requests
from config import KIMI_API_KEY
import time

class KimiClient:
    def __init__(self, max_context_messages=30, max_tokens_per_request=80000):
        self.messages = []
        self.max_retries = 3
        self.timeout = 120
        self.retry_delay = 5
        self.max_context_messages = max_context_messages
        self.max_tokens_per_request = max_tokens_per_request

    def _estimate_tokens(self, text):
        """估算文本的token数量（粗略估计：中文约1.5字符/token，英文约0.25词/token）"""
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        english_words = len(text.split()) - chinese_chars
        return int(chinese_chars / 1.5 + english_words / 0.25)

    def _estimate_request_tokens(self):
        """估算当前请求的总token数"""
        return sum(self._estimate_tokens(msg.get("content", "")) for msg in self.messages)

    def _manage_context(self):
        """智能上下文管理：严格控制上下文大小"""
        if len(self.messages) > self.max_context_messages:
            print(f"[PERF] Context size ({len(self.messages)}) exceeds limit ({self.max_context_messages}), compressing...")

            # 保留系统消息（如果有）和最近的消息
            system_messages = [msg for msg in self.messages if msg.get("role") == "system"]
            recent_messages = self.messages[-(self.max_context_messages // 2):]

            # 对中间的消息进行摘要
            middle_messages = self.messages[len(system_messages):-len(recent_messages)]
            if middle_messages:
                # 创建摘要
                summary_text = " ".join([msg.get("content", "")[:200] for msg in middle_messages])
                summary_message = {
                    "role": "system",
                    "content": f"[历史摘要] {summary_text}"
                }
                self.messages = system_messages + [summary_message] + recent_messages
                print(f"[PERF] Context compressed from {len(self.messages) + len(middle_messages)} to {len(self.messages)} messages")

    def _check_and_compress_context(self):
        """检查并压缩上下文，确保不超过token限制"""
        total_tokens = self._estimate_request_tokens()

        if total_tokens > self.max_tokens_per_request:
            print(f"[PERF] Request tokens ({total_tokens}) exceed limit ({self.max_tokens_per_request}), compressing...")

            # 保留第一条消息（通常是系统提示）和最近的消息
            keep_first = 1 if self.messages and self.messages[0].get("role") == "system" else 0
            recent_count = min(5, len(self.messages) // 3)  # 保留最近1/3的消息，最多5条

            if len(self.messages) > keep_first + recent_count:
                old_messages = self.messages[keep_first:-recent_count]
                recent_messages = self.messages[-recent_count:]

                # 创建旧消息的摘要
                summary_parts = []
                for msg in old_messages:
                    content = msg.get("content", "")
                    if len(content) > 100:
                        content = content[:100] + "..."
                    summary_parts.append(f"[{msg.get('role')}] {content}")

                summary_text = " | ".join(summary_parts)
                if len(summary_text) > 1000:
                    summary_text = summary_text[:1000] + "..."

                summary_message = {
                    "role": "system",
                    "content": f"[历史摘要] {summary_text}"
                }

                first_message = [self.messages[0]] if keep_first > 0 else []
                self.messages = first_message + [summary_message] + recent_messages

                new_tokens = self._estimate_request_tokens()
                print(f"[PERF] Context compressed from {total_tokens} to {new_tokens} tokens, {len(self.messages)} messages")

    def generate(self, prompt, reset_context=False):
        """Generate text using Kimi API with context management"""
        if not KIMI_API_KEY:
            raise ValueError("Kimi API key is not set in config.py")

        if reset_context:
            self.messages = []

        # Add user message to context
        self.messages.append({
            "role": "user",
            "content": prompt
        })

        # 管理上下文大小
        self._manage_context()
        self._check_and_compress_context()

        for attempt in range(self.max_retries):
            try:
                url = "https://api.moonshot.cn/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {KIMI_API_KEY}"
                }
                data = {
                    "model": "kimi-k2.6",
                    "messages": self.messages,
                    "timeout": self.timeout
                }

                # 估算请求大小
                request_tokens = self._estimate_request_tokens()
                print(f"Attempt {attempt + 1}/{self.max_retries}: Sending request ({request_tokens} tokens)...")
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)

                if response.status_code != 200:
                    print(f"Kimi API Error: {response.status_code} - {response.text}")
                response.raise_for_status()

                result = response.json()
                assistant_message = result["choices"][0]["message"]

                # Add assistant response to context
                self.messages.append(assistant_message)

                return assistant_message["content"]
            except requests.exceptions.Timeout as e:
                print(f"Timeout error (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    self.retry_delay *= 2
                else:
                    raise Exception(f"Error generating text with Kimi after {self.max_retries} attempts: {str(e)}")
            except requests.exceptions.ConnectionError as e:
                error_str = str(e)

                # 判断是否是代理错误（ProxyError）
                if "ProxyError" in error_str or "Unable to connect to proxy" in error_str:
                    print(f"Proxy connection failed: {error_str}")
                    raise Exception(f"Proxy connection failed. The request may be too large or the proxy is unavailable. "
                                    f"Try reducing context size or check proxy settings. Error: {error_str}")

                print(f"Connection error (attempt {attempt + 1}/{self.max_retries}): {error_str}")
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Connection error after {self.max_retries} attempts: {error_str}")
            except Exception as e:
                raise Exception(f"Error generating text with Kimi: {str(e)}")

def kimi_generate(prompt):
    """Backward compatibility function"""
    client = KimiClient()
    return client.generate(prompt, reset_context=True)
