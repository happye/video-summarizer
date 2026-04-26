from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.transcript_loader import load_transcript
import json
import os

# 各模型官方上下文长度（tokens）和对应的字符限制
# 预留 6000 tokens 给 prompt + response
MODEL_CHUNK_LIMITS = {
    "kimi": {
        "context_tokens": 200000,
        "usable_tokens": 194000,  # 200K - 6K reserve
        "chars_per_token": 1.5,   # 中文约 1.5 字符/token
        "max_chars": 130000       # 194K / 1.5 ≈ 129K, 取整
    },
    "deepseek": {
        "context_tokens": 384000,
        "usable_tokens": 378000,  # 384K - 6K reserve
        "chars_per_token": 1.5,
        "max_chars": 250000       # 378K / 1.5 ≈ 252K, 取整
    },
    "ollama": {
        "context_tokens": 128000,
        "usable_tokens": 122000,  # 128K - 6K reserve
        "chars_per_token": 1.5,
        "max_chars": 80000        # 122K / 1.5 ≈ 81K, 取整
    }
}

def chunk_transcript(transcript_path, llm_provider="kimi"):
    """Split transcript into chunks based on LLM's actual context window"""
    print("Chunking transcript...")

    # Load transcript
    full_transcript = load_transcript(transcript_path)
    transcript_length = len(full_transcript)
    print(f"Transcript length: {transcript_length} characters")

    # Get model limits
    model_config = MODEL_CHUNK_LIMITS.get(llm_provider, MODEL_CHUNK_LIMITS["kimi"])
    max_chars = model_config["max_chars"]
    context_tokens = model_config["context_tokens"]

    print(f"LLM Provider: {llm_provider}")
    print(f"Model context window: {context_tokens} tokens")
    print(f"Max chars per chunk: {max_chars} (reserved 6K tokens for prompt/response)")

    if transcript_length <= max_chars:
        # 短视频：直接一个 chunk 处理
        print(f"Short transcript, processing as single chunk")
        chunks = [full_transcript]
    else:
        # 长视频：按模型能力切分，目标是最少的 chunk 数
        # 重叠设为 5% 以减少冗余
        overlap = min(2000, int(max_chars * 0.05))
        chunk_size = max_chars - overlap  # 实际每 chunk 的有效内容

        # 计算预估 chunk 数
        estimated_chunks = (transcript_length - overlap) // chunk_size + 1
        print(f"Long transcript, splitting into ~{estimated_chunks} chunks")
        print(f"Chunk size: {chunk_size}, overlap: {overlap}")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len
        )
        chunks = splitter.split_text(full_transcript)

    # Import CHUNKS_PATH after setting paths
    from config import CHUNKS_PATH
    print(f"CHUNKS_PATH: {CHUNKS_PATH}")

    # Ensure the directory exists
    chunks_dir = os.path.dirname(CHUNKS_PATH)
    if not os.path.exists(chunks_dir):
        os.makedirs(chunks_dir, exist_ok=True)
        print(f"Created directory: {chunks_dir}")

    # Save chunks to JSON
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Transcript split into {len(chunks)} chunk(s)")

    # 如果 chunk 数仍然很多，给出警告
    if len(chunks) > 5:
        print(f"[WARNING] {len(chunks)} chunks detected. Consider using a model with larger context window.")

    return chunks
