import ollama
from config import OLLAMA_MODEL
from utils.ai_logger import get_cache_logger
import time

def ollama_generate(prompt):
    """Generate text using Ollama local model"""
    try:
        start = time.time()
        response = ollama.generate(
            model=OLLAMA_MODEL,
            prompt=prompt
        )
        duration = time.time() - start

        usage = {
            "prompt_tokens": response.get("prompt_eval_count", 0),
            "completion_tokens": response.get("eval_count", 0),
            "total_tokens": response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
        }

        cache_logger = get_cache_logger()
        cache_logger.log_request(OLLAMA_MODEL, 1, usage["prompt_tokens"], 1)
        cache_logger.log_response(
            model=OLLAMA_MODEL,
            request_num=1,
            duration=duration,
            usage=usage,
            headers={}
        )

        return response.get("response", "")
    except Exception as e:
        raise Exception(f"Error generating text with Ollama: {str(e)}")
