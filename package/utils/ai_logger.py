import os
from datetime import datetime

AI_CACHE_LOG_HEADER = "[AI-CACHE]"

class AICacheLogger:
    """AI 缓存命中日志记录器 — 前台输出 + 本地文件"""

    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "ai_cache.log")
        self._reset_stats()

    def _reset_stats(self):
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_partials = 0
        self.cache_misses = 0
        self.total_prompt_tokens = 0
        self.total_cached_tokens = 0
        self.total_miss_tokens = 0
        self.total_completion_tokens = 0
        self.session_model = ""

    def log_request(self, model, request_num, request_tokens, attempt):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"{AI_CACHE_LOG_HEADER} [{ts}] [{model}] Request #{request_num} (attempt {attempt}): Sending {request_tokens} tokens"
        self._emit(msg)

    def log_response(self, model, request_num, duration, usage, headers):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cache_hit = self._detect_full_cache_hit(headers, usage)
        cache_tokens = self._get_cache_hit_tokens(usage)

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        if cache_hit:
            cache_label = "CACHE HIT"
        elif cache_tokens > 0:
            cache_label = f"CACHE PARTIAL ({cache_tokens} tokens)"
        else:
            cache_label = "CACHE MISS"

        self._emit(f"{AI_CACHE_LOG_HEADER} [{ts}] [{model}] Request #{request_num}: {cache_label} | Duration: {duration:.2f}s")
        self._emit(f"{AI_CACHE_LOG_HEADER}   Tokens: prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}")

        if cache_tokens > 0 and prompt_tokens > 0:
            hit_rate = cache_tokens / prompt_tokens * 100
            self._emit(f"{AI_CACHE_LOG_HEADER}   Cached: {cache_tokens}/{prompt_tokens} prompt tokens ({hit_rate:.1f}% hit rate)")

        miss_tokens = usage.get("prompt_cache_miss_tokens", 0)
        if miss_tokens > 0:
            self._emit(f"{AI_CACHE_LOG_HEADER}   Cache miss tokens: {miss_tokens}")

        relevant_headers = {k: v for k, v in headers.items() if "cache" in k.lower() or "x-ds-" in k.lower()}
        if relevant_headers:
            self._emit(f"{AI_CACHE_LOG_HEADER}   Response headers: {relevant_headers}")

        self.total_requests += 1
        self.session_model = model
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_cached_tokens += cache_tokens
        self.total_miss_tokens += miss_tokens
        if cache_hit:
            self.cache_hits += 1
        elif cache_tokens > 0:
            self.cache_partials += 1
        else:
            self.cache_misses += 1

    def log_summary(self):
        if self.total_requests == 0:
            return

        lines = [
            f"{AI_CACHE_LOG_HEADER} {'='*60}",
            f"{AI_CACHE_LOG_HEADER} Session Cache Summary [{self.session_model}]",
            f"{AI_CACHE_LOG_HEADER}   Total requests: {self.total_requests}",
            f"{AI_CACHE_LOG_HEADER}   Cache hits: {self.cache_hits} | Partials: {self.cache_partials} | Misses: {self.cache_misses}",
            f"{AI_CACHE_LOG_HEADER}   Total prompt tokens: {self.total_prompt_tokens}",
            f"{AI_CACHE_LOG_HEADER}   Total cached tokens: {self.total_cached_tokens}",
            f"{AI_CACHE_LOG_HEADER}   Total miss tokens: {self.total_miss_tokens}",
            f"{AI_CACHE_LOG_HEADER}   Total completion tokens: {self.total_completion_tokens}",
        ]

        if self.total_prompt_tokens > 0:
            overall_hit_rate = self.total_cached_tokens / self.total_prompt_tokens * 100
            lines.append(f"{AI_CACHE_LOG_HEADER}   Overall cache hit rate: {overall_hit_rate:.1f}%")

        if self.total_requests <= 1:
            lines.append(f"{AI_CACHE_LOG_HEADER}   Note: Only 1 request sent, cache requires >= 2 requests with shared prefix")

        lines.append(f"{AI_CACHE_LOG_HEADER} {'='*60}")

        for line in lines:
            self._emit(line)

    @staticmethod
    def _get_cache_hit_tokens(usage):
        """从 usage 中提取各模型的缓存命中 token 数"""
        # DeepSeek: prompt_cache_hit_tokens
        ds_hit = usage.get("prompt_cache_hit_tokens", 0)
        if ds_hit > 0:
            return ds_hit
        # Kimi K2.x: cached_tokens (顶层或 prompt_tokens_details 内)
        kimi_cached = usage.get("cached_tokens", 0) or usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)
        if kimi_cached > 0:
            return kimi_cached
        # Anthropic (via proxy): cache_read_input_tokens
        anthropic_cached = usage.get("cache_read_input_tokens", 0)
        if anthropic_cached > 0:
            return anthropic_cached
        return 0

    @staticmethod
    def _detect_full_cache_hit(headers, usage):
        """检测是否全部 prompt tokens 都命中缓存"""
        # HTTP 响应头方式（部分 CDN/代理）
        if headers.get("X-DS-Cache-Hit", "").lower() == "true":
            return True
        if headers.get("x-cache-hit", "").lower() == "true":
            return True
        if headers.get("x-cache-lookup", "").lower() == "hit":
            return True
        if headers.get("x-cache-status", "").lower() == "hit":
            return True

        prompt_tokens = usage.get("prompt_tokens", 0)

        # DeepSeek: prompt_cache_hit_tokens == prompt_tokens → 完全命中
        ds_hit = usage.get("prompt_cache_hit_tokens", 0)
        if ds_hit > 0 and ds_hit == prompt_tokens:
            return True

        # Kimi K2.x: cached_tokens == prompt_tokens → 完全命中
        kimi_cached = usage.get("cached_tokens", 0) or usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)
        if kimi_cached > 0 and kimi_cached == prompt_tokens:
            return True

        return False

    def _emit(self, msg):
        print(msg)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception:
            pass


_cache_logger = None

def get_cache_logger():
    global _cache_logger
    if _cache_logger is None:
        _cache_logger = AICacheLogger()
    return _cache_logger