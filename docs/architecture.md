# 系统架构

## 处理流水线

所有输入模式最终汇聚到同一条处理链：

```
输入源（URL / 本地文件 / 本地目录）
  ↓
download（仅 URL 模式）
  ↓
transcribe（WhisperX GPU 转录）
  ↓
correct（AI 纠错，可选）
  ↓
chunk（文本分段）
  ↓
summarize（LLM 生成摘要）
  ↓
output（写入 Markdown）
```

每个阶段独立、可替换、基于中间文件。中间文件确保可调试、可断点续跑。

## 运行模式

| 模式 | 入口 | 说明 |
|------|------|------|
| 交互模式 | `python main.py` / `run.ps1` 选项1 | 循环处理，支持 url/local/file/download 命令 |
| 仅下载 | `run.ps1` 选项2 | 连续下载视频，不转录不总结 |
| 单次模式 | `python main.py --url/file/local ...` | 处理一个视频后退出 |
| 本地循环 | `python main.py --local-loop` / `run.ps1` 选项4 | 专门循环处理本地视频，直接输入路径 |

## 模块职责

### main.py — 入口与调度

- `ProcessArgs`：统一的参数容器（模块级类）
- `process_video()`：核心处理链（transcribe → correct → chunk → summarize → output）
- `_process_url()`：URL 模式，下载后调用 process_video
- `_process_local()`：本地目录模式，在原目录处理
- `_process_file()`：本地文件模式，复制到 output 后处理
- `interactive_mode()`：交互循环，通过 handle_command 分发
- `local_loop_mode()`：本地视频循环，直接输入路径

### pipeline/ — 处理流程

| 文件 | 函数 | 输入 | 输出 |
|------|------|------|------|
| `download.py` | `download_video(url)` → `(path, name, ext)` | URL | 视频文件 |
| `transcribe.py` | `transcribe_video(path)` → `transcript_path` | 视频文件 | transcript.json |
| `correct.py` | `correct_transcript(path, llm_provider)` → `corrected_path` | transcript.json | transcript_corrected.json |
| `chunker.py` | `chunk_transcript(path)` → `chunks` | transcript JSON | chunks.json |
| `summarize.py` | `generate_summary(chunks, llm, mode, ...)` → `summary` | chunks | partial_summary.json |
| `output.py` | `write_output(summary, mode)` | summary 文本 | summary.md |

### llm/ — LLM 客户端

| 文件 | 说明 |
|------|------|
| `base_client.py` | 通用基类：上下文管理、重试、缓存日志 |
| `kimi_client.py` | Kimi (Moonshot AI) 客户端 |
| `deepseek_client.py` | DeepSeek 客户端 |
| `ollama_client.py` | Ollama 本地模型客户端 |
| `adapter.py` | 统一适配器，根据 provider 选择客户端 |

### summarizers/ — 摘要策略

| 文件 | 模式 | 输出格式 | 适用场景 |
|------|------|---------|---------|
| `outline_summary.py` | outline | `I. → A. → 1.` 层次编号 | 知识讲座、投资分析 |
| `timeline_summary.py` | timeline | `MM:SS 事件描述` | 直播回放、会议记录 |
| `map_reduce.py` | mapreduce | 要点式综合摘要 | 超长视频 + Ollama |

### utils/ — 工具模块

| 文件 | 说明 |
|------|------|
| `transcript_loader.py` | 加载 transcript JSON，优先读 `text` 字段，fallback 从 segments 拼接 |
| `ai_logger.py` | AI 缓存命中日志（前台 + `logs/ai_cache.log`） |

## 数据流与文件结构

处理一个视频后，`output/<视频名称>/` 目录下生成：

```
output/<视频名称>/
├── <视频名称>.mp4          # 原始视频
├── transcript.json         # WhisperX 转录结果
├── transcript_corrected.json  # 纠错后的转录（含 text 字段）
├── transcript_correction_diff.json  # 纠错差异记录
├── chunks.json             # 文本分段
├── partial_summary.json    # 部分摘要（调试用）
└── summary.md              # 最终摘要
```

## 纠错模块工作原理

1. 从 transcript.json 读取 segments，拼接为完整文本
2. 发送给 LLM 修正同音字、专业术语误识别等
3. 用 `difflib.SequenceMatcher` 字符级对齐，将纠错结果映射回各 segment
4. 纠错文本同时写入 JSON 的 `text` 字段（确保下游即使映射失败也能读到纠错文本）
5. `transcript_loader` 优先读 `text` 字段，fallback 从 segments 拼接
