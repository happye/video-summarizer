import requests
import time
from datetime import datetime
from utils.ai_logger import get_cache_logger

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


class BaseLLMClient:
    """通用LLM客户端基类，提供上下文管理、重试、错误处理等通用功能"""

    def __init__(self, api_key, model, api_url,
                 max_context_messages=30,
                 max_tokens_per_request=80000,
                 max_retries=5,
                 timeout=180,
                 retry_delay=5):
        self.api_key = api_key
        self.model = model
        self.api_url = api_url
        self.messages = []
        self.max_retries = max_retries
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.perf_tracker = PerformanceTracker()
        self.request_count = 0
        self.max_context_messages = max_context_messages
        self.max_tokens_per_request = max_tokens_per_request
        self.context_summary = ""
        self.last_finish_reason = None
        self.last_usage = {}

    def _estimate_tokens(self, text):
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_words = len(text.split())
        english_words = max(0, total_words - chinese_chars)
        return max(1, int(chinese_chars / 1.5 + english_words / 0.25))

    def _estimate_request_tokens(self):
        return sum(self._estimate_tokens(msg.get("content", "")) for msg in self.messages)

    def _manage_context(self):
        if len(self.messages) > self.max_context_messages:
            print(f"[LLM] 上下文消息数 ({len(self.messages)}) 超过限制 ({self.max_context_messages}), 压缩中...")

            system_messages = [msg for msg in self.messages if msg.get("role") == "system"]
            recent_messages = self.messages[-(self.max_context_messages // 2):]

            middle_messages = self.messages[len(system_messages):-len(recent_messages)]
            if middle_messages:
                summary_text = " ".join([msg.get("content", "")[:200] for msg in middle_messages])
                summary_message = {
                    "role": "system",
                    "content": f"[历史摘要] {summary_text}"
                }
                self.messages = system_messages + [summary_message] + recent_messages
                print(f"[LLM] 上下文压缩: {len(self.messages) + len(middle_messages)} → {len(self.messages)} 条消息")

    def _check_and_compress_context(self):
        total_tokens = self._estimate_request_tokens()

        if total_tokens > self.max_tokens_per_request:
            print(f"[LLM] 请求tokens ({total_tokens}) 超过限制 ({self.max_tokens_per_request}), 压缩中...")

            keep_first = 1 if self.messages and self.messages[0].get("role") == "system" else 0
            recent_count = min(5, len(self.messages) // 3)

            if len(self.messages) > keep_first + recent_count:
                old_messages = self.messages[keep_first:-recent_count]
                recent_messages = self.messages[-recent_count:]

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
                print(f"[LLM] 上下文压缩: {total_tokens} → {new_tokens} tokens, {len(self.messages)} 条消息")

    def _check_session_health(self):
        if self.request_count > 0 and self.request_count % 10 == 0:
            print(f"[LLM] 会话健康检查: 已处理 {self.request_count} 个请求, 上下文: {len(self.messages)} 条消息")

            total_tokens = self._estimate_request_tokens()

            health_threshold = int(self.max_tokens_per_request * 0.5)
            if total_tokens > health_threshold:
                print(f"[LLM] 上下文tokens ({total_tokens}) 超过阈值 ({health_threshold}), 触发压缩...")
                self._check_and_compress_context()

    def _build_request_data(self):
        return {
            "model": self.model,
            "messages": self.messages,
            "timeout": self.timeout
        }

    def _parse_response(self, response_json):
        return response_json["choices"][0]["message"]

    def generate(self, prompt, reset_context=False):
        if not self.api_key:
            raise ValueError(f"API key is not set in config.py")

        if reset_context:
            self.messages = []
            self.request_count = 0
            self.context_summary = ""
            print(f"[LLM] 上下文已重置, 开始新会话 [{self.model}]")

        self.request_count += 1
        print(f"[LLM] 请求 #{self.request_count}, 上下文: {len(self.messages)} 条消息")

        self._check_session_health()

        self.messages.append({
            "role": "user",
            "content": prompt
        })

        self._manage_context()
        self._check_and_compress_context()

        for attempt in range(self.max_retries):
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                data = self._build_request_data()

                request_tokens = self._estimate_request_tokens()
                cache_logger = get_cache_logger()
                cache_logger.log_request(self.model, self.request_count, request_tokens, attempt + 1)
                print(f"[LLM] 尝试 {attempt + 1}/{self.max_retries}: 发送请求 ({request_tokens} tokens)...")
                request_start = self.perf_tracker.start_request()

                response = requests.post(self.api_url, headers=headers, json=data, timeout=self.timeout)

                if response.status_code != 200:
                    print(f"[LLM] API错误: HTTP {response.status_code} - {response.text[:500]}")
                response.raise_for_status()

                result = response.json()
                assistant_message = self._parse_response(result)

                self.last_finish_reason = result["choices"][0].get("finish_reason", "unknown")
                self.last_usage = result.get("usage", {})

                self.messages.append(assistant_message)

                duration = self.perf_tracker.end_request(success=True)

                completion_tokens = self.last_usage.get("completion_tokens", 0)
                content_length = len(assistant_message.get("content", "") or "")
                print(f"[LLM] 请求成功: {duration:.2f}s, 输出: {completion_tokens} tokens/{content_length} 字符, finish_reason={self.last_finish_reason}")

                if self.last_finish_reason == "length":
                    print(f"[LLM] ⚠ 输出被截断! finish_reason=length, 输出达到max_tokens上限, 内容不完整")

                cache_logger.log_response(
                    model=self.model,
                    request_num=self.request_count,
                    duration=duration,
                    usage=result.get("usage", {}),
                    headers=dict(response.headers)
                )

                return assistant_message["content"]

            except requests.exceptions.Timeout as e:
                duration = self.perf_tracker.end_request(success=False, error="Timeout")
                print(f"[LLM] 超时: {duration:.2f}s (尝试 {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"[LLM] 等待 {wait_time}s 后重试...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Timeout after {self.max_retries} attempts: {str(e)}")

            except requests.exceptions.HTTPError as e:
                duration = self.perf_tracker.end_request(success=False, error=f"HTTP {e.response.status_code}")
                if e.response.status_code == 429:
                    print(f"[LLM] 限流 (429) (尝试 {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        backoff_time = self.retry_delay * (2 ** attempt)
                        print(f"[LLM] 等待 {backoff_time}s 后重试...")
                        time.sleep(backoff_time)
                    else:
                        raise Exception(f"Rate limit exceeded after {self.max_retries} attempts. Please try again later.")
                else:
                    raise Exception(f"HTTP Error: {str(e)}")

            except requests.exceptions.ConnectionError as e:
                duration = self.perf_tracker.end_request(success=False, error="Connection Error")
                error_str = str(e)

                if "ProxyError" in error_str or "Unable to connect to proxy" in error_str:
                    print(f"[LLM] 代理连接失败: {error_str}")
                    raise Exception(f"Proxy connection failed. The request may be too large or the proxy is unavailable. "
                                    f"Try reducing context size or check proxy settings. Error: {error_str}")

                print(f"[LLM] 连接错误 (尝试 {attempt + 1}/{self.max_retries}): {error_str}")
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"[LLM] 等待 {wait_time}s 后重试...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Connection error after {self.max_retries} attempts: {error_str}")

            except Exception as e:
                self.perf_tracker.end_request(success=False, error=str(e))
                raise Exception(f"Error generating text: {str(e)}")

    def get_performance_summary(self):
        return self.perf_tracker.get_summary()
