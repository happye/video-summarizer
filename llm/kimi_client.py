import requests
from config import KIMI_API_KEY
import time
from datetime import datetime

class PerformanceTracker:
    def __init__(self):
        self.metrics = []
        self.start_time = None

    def start_request(self):
        self.start_time = time.time()
        return self.start_time

    def end_request(self, success=True, error=None):
        if self.start_time is None:
            return

        end_time = time.time()
        duration = end_time - self.start_time

        metric = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "success": success,
            "error": error
        }
        self.metrics.append(metric)

        # 输出性能信息
        print(f"[PERF] Request duration: {duration:.2f}s")
        if not success:
            print(f"[PERF] Error: {error}")

        self.start_time = None
        return duration

    def get_summary(self):
        if not self.metrics:
            return "No metrics recorded"

        total_duration = sum(m["duration"] for m in self.metrics)
        success_count = sum(1 for m in self.metrics if m["success"])
        fail_count = len(self.metrics) - success_count

        summary = f"""
[PERF] Performance Summary:
  Total requests: {len(self.metrics)}
  Successful: {success_count}
  Failed: {fail_count}
  Total duration: {total_duration:.2f}s
  Average duration: {total_duration/len(self.metrics):.2f}s
"""
        return summary

class KimiClient:
    def __init__(self, max_context_messages=30, max_tokens_per_request=80000):
        self.messages = []
        self.max_retries = 5
        self.timeout = 180
        self.retry_delay = 5
        self.perf_tracker = PerformanceTracker()
        self.request_count = 0
        self.max_context_messages = max_context_messages
        self.max_tokens_per_request = max_tokens_per_request  # 最大请求token数
        self.context_summary = ""

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

    def _check_session_health(self):
        """检查会话健康状态"""
        if self.request_count > 0 and self.request_count % 10 == 0:
            print(f"[PERF] Session health check: {self.request_count} requests processed")
            print(f"[PERF] Current context size: {len(self.messages)} messages")

            # 估算上下文大小
            total_tokens = self._estimate_request_tokens()
            print(f"[PERF] Estimated context tokens: {total_tokens}")

            # 如果上下文过大，触发压缩
            if total_tokens > 80000:  # 80k tokens
                print("[PERF] Context too large, triggering compression...")
                self._check_and_compress_context()

    def generate(self, prompt, reset_context=False):
        """Generate text using Kimi API with context management and performance tracking"""
        if not KIMI_API_KEY:
            raise ValueError("Kimi API key is not set in config.py")

        if reset_context:
            self.messages = []
            self.request_count = 0
            self.context_summary = ""
            print("[PERF] Context reset, starting new session")

        self.request_count += 1
        print(f"[PERF] Request #{self.request_count}, Context size: {len(self.messages)} messages")

        # 检查会话健康状态
        self._check_session_health()

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
                print(f"[PERF] Attempt {attempt + 1}/{self.max_retries}: Sending request ({request_tokens} tokens)...")
                request_start = self.perf_tracker.start_request()

                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)

                if response.status_code != 200:
                    print(f"[PERF] API Error: {response.status_code} - {response.text}")
                response.raise_for_status()

                result = response.json()
                assistant_message = result["choices"][0]["message"]

                # Add assistant response to context
                self.messages.append(assistant_message)

                duration = self.perf_tracker.end_request(success=True)
                print(f"[PERF] Request completed successfully in {duration:.2f}s")

                return assistant_message["content"]
            except requests.exceptions.Timeout as e:
                duration = self.perf_tracker.end_request(success=False, error="Timeout")
                print(f"[PERF] Timeout after {duration:.2f}s (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay
                    print(f"[PERF] Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    self.retry_delay *= 2
                else:
                    raise Exception(f"Error generating text with Kimi after {self.max_retries} attempts: {str(e)}")
            except requests.exceptions.HTTPError as e:
                duration = self.perf_tracker.end_request(success=False, error=f"HTTP {e.response.status_code}")
                if e.response.status_code == 429:
                    print(f"[PERF] Rate limit exceeded (429) (attempt {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        backoff_time = self.retry_delay * (2 ** attempt)
                        print(f"[PERF] Waiting {backoff_time}s before retry...")
                        time.sleep(backoff_time)
                    else:
                        raise Exception(f"Rate limit exceeded after {self.max_retries} attempts. Please try again later.")
                else:
                    raise Exception(f"HTTP Error generating text with Kimi: {str(e)}")
            except requests.exceptions.ConnectionError as e:
                duration = self.perf_tracker.end_request(success=False, error="Connection Error")
                error_str = str(e)

                # 判断是否是代理错误（ProxyError）
                if "ProxyError" in error_str or "Unable to connect to proxy" in error_str:
                    print(f"[PERF] Proxy connection failed: {error_str}")
                    # 代理错误通常无法通过重试解决，直接报错
                    raise Exception(f"Proxy connection failed. The request may be too large or the proxy is unavailable. "
                                    f"Try reducing context size or check proxy settings. Error: {error_str}")

                print(f"[PERF] Connection error (attempt {attempt + 1}/{self.max_retries}): {error_str}")
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"[PERF] Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Connection error after {self.max_retries} attempts: {error_str}")
            except Exception as e:
                self.perf_tracker.end_request(success=False, error=str(e))
                raise Exception(f"Error generating text with Kimi: {str(e)}")

    def get_performance_summary(self):
        return self.perf_tracker.get_summary()

def kimi_generate(prompt):
    """Backward compatibility function"""
    client = KimiClient()
    return client.generate(prompt, reset_context=True)
