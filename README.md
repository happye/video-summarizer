# 视频总结系统使用文档

## 项目简介

视频总结系统是一个基于AI的工具，能够自动下载视频、提取音频、转录内容、分段处理并生成详细的视频总结。系统支持多种视频平台，包括YouTube、Bilibili等。

## 功能特点

- 自动视频下载与处理
- GPU加速的语音识别（使用OpenAI Whisper）
- 智能文本分段与上下文管理
- **支持多种LLM提供商**：Kimi (Moonshot AI)、DeepSeek、Ollama
- 按视频名称分类的目录结构
- 支持多种总结模式（大纲、时间线、MapReduce）
- **交互模式**：处理完不退出，连续处理多个视频
- **本地视频循环模式**：`--local-loop`，专门循环处理本地视频文件/目录，直接输入路径即可
- **本地视频目录**：直接处理已下载的视频，跳过下载步骤
- **AI缓存命中日志**：前台+本地文件双记录，追踪API缓存效率
- **费曼学习法提示词**：专业术语通俗解释、原话引用、举例说明
- **AI转录纠错**：转录后自动用AI修正同音字、专业术语误识别等错误
- **仅下载模式**：`--download-only` 或交互命令 `download`，只下载视频不转录总结
- 智能跳过已处理视频，避免重复下载和API调用
- 中文文件名保留，不乱码

## 系统要求

- Python 3.10+
- CUDA兼容的GPU（推荐，用于加速语音识别）
- 足够的磁盘空间（用于存储视频和处理文件）
- 稳定的网络连接（用于下载视频和调用API）

## 支持的LLM模型

| 提供商 | 模型 | 上下文长度 | 特点 |
|--------|------|-----------|------|
| **Kimi** | `kimi-k2.6` | 200K+ | 默认推荐，超长上下文，适合长视频 |
| **DeepSeek** | `deepseek-v4-pro` | 384K | 高性价比，推理能力强 |
| **DeepSeek** | `deepseek-v4-flash` | 384K | 更快更便宜，适合快速处理 |
| **Ollama** | `qwen2.5` 等本地模型 | 取决于模型 | 本地运行，无需联网 |

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/happye/video-summarizer
cd video-summarizer
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置API密钥

编辑 `config.py` 文件，填写你的API密钥：

```python
# Kimi API Key (默认推荐)
KIMI_API_KEY = "your_kimi_api_key_here"

# DeepSeek API Key (可选)
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"
```

- Kimi API Key: https://platform.moonshot.cn/
- DeepSeek API Key: https://platform.deepseek.com/

### 4. 安装yt-dlp

系统会自动下载并配置yt-dlp，用于视频下载。

## 使用方法

### 方式一：交互模式（推荐）

双击运行 `run.ps1`，选择交互模式，可连续处理多个视频：

```powershell
.\run.ps1
```

交互模式支持以下命令：

| 命令 | 说明 |
|------|------|
| `url <视频链接>` | 从URL下载并处理 |
| `download <视频链接>` | 仅下载视频，不转录和总结 |
| `local <目录路径>` | 处理本地视频目录 |
| `file <文件路径>` | 处理本地视频文件 |
| `llm <kimi/deepseek/ollama>` | 切换LLM模型 |
| `mode <outline/timeline/mapreduce>` | 切换摘要模式 |
| `force` | 切换强制重处理 |
| `help` | 显示帮助 |
| `exit` / `quit` / `q` | 退出 |

直接粘贴URL或路径也可自动识别。

### 方式二：命令行直接运行

#### 命令行参数

| 参数 | 说明 |
|------|------|
| `--url` | 视频URL（支持YouTube、Bilibili等） |
| `--file` | 本地视频文件路径 |
| `--local` | 本地视频目录路径（跳过下载，直接处理） |
| `--llm` | LLM提供商（`kimi`、`deepseek`、`ollama`，默认`kimi`） |
| `--mode` | 总结模式（`outline`、`timeline`、`mapreduce`，默认`outline`） |
| `--detail-level` | 总结详细程度（1-5，默认2） |
| `--bullet-count` | 要点数量（默认10） |
| `--force` | 强制重新处理已存在的视频 |
| `--no-correct` | 跳过转录纠错步骤 |
| `--download-only` | 仅下载视频，跳过转录和总结 |
| `--interactive` / `-i` | 交互模式 |
| `--local-loop` | 本地视频循环模式（连续处理本地视频文件/目录） |

#### 示例命令

```bash
# 交互模式（无参数自动进入）
python main.py

# 本地视频循环模式
python main.py --local-loop --llm kimi --mode outline

# 从URL下载并处理
python main.py --url "https://www.bilibili.com/video/BV1bpQeY2EvH"

# 使用DeepSeek处理
python main.py --url "视频URL" --llm deepseek

# 处理本地视频目录
python main.py --local "D:\Videos\我的视频" --llm deepseek

# 处理本地视频文件
python main.py --file "path/to/video.mp4" --llm kimi --mode outline

# 生成时间线总结
python main.py --url "视频URL" --llm deepseek --mode timeline

# 仅下载视频，不转录和总结
python main.py --url "视频URL" --download-only
```

### 方式三：API连通性测试

```bash
python test_kimi.py
python test_deepseek.py
```

## 总结模式对比

| 模式 | 输出格式 | 适用场景 | 深度 |
|------|---------|---------|------|
| **Outline（大纲）** | `I. → A. → 1.` 层次编号 | 知识讲座、投资分析、教程等有逻辑结构的视频 | ⭐⭐⭐⭐⭐ 最深 |
| **Timeline（时间线）** | `MM:SS 事件描述` | 直播回放、会议记录等需按时间定位的视频 | ⭐⭐⭐ 中等 |
| **MapReduce（分治）** | 要点式综合摘要 | 超长视频+Ollama本地模型 | ⭐⭐⭐ 中等 |

**推荐**：日常用 Outline，需定位时间点用 Timeline，Ollama处理超长视频用 MapReduce。

## 输出结果

### URL模式

处理完成后，系统会在 `output` 目录下创建以视频名称命名的文件夹：

- `<视频名称>.mp4`：下载的视频文件
- `transcript.json`：完整的语音转录结果
- `chunks.json`：文本分段结果
- `partial_summary.json`：部分总结结果（调试用）
- `summary.md`：最终的视频总结

### 本地目录模式（--local）

所有输出直接写入传入的目录，不复制视频文件：

- `transcript.json`、`chunks.json`、`summary.md` 等

## AI缓存命中日志

系统自动记录API缓存命中情况，前台输出+本地文件双记录：

- 日志文件：`logs/ai_cache.log`
- 支持的缓存字段：
  - DeepSeek：`prompt_cache_hit_tokens` / `prompt_cache_miss_tokens`
  - Kimi K2.x：`cached_tokens` / `prompt_tokens_details.cached_tokens`
- 每次请求显示：CACHE HIT / CACHE PARTIAL / CACHE MISS
- 会话结束时输出缓存统计摘要

## 智能跳过机制

- 如果 `output/<视频名称>/` 已存在视频和总结文件，自动跳过
- 使用 `--force` 参数强制重新处理
- 交互模式下用 `force` 命令切换

## 常见问题

### GPU加速问题

确保已安装CUDA兼容的PyTorch，GPU驱动正确。

### API超时

系统已实现自动重试机制（最多5次，指数退避），代理错误快速失败。

### 视频下载失败

- 确保网络连接稳定
- Bilibili视频需要cookies（系统已自动配置）
- BV号大小写敏感，直接粘贴URL即可，不要手动修改

### 中文文件名乱码

已修复，系统会正确读取中文标题并保留中文字符。

### 长视频处理

系统自动估算上下文token，超限时压缩历史消息，DeepSeek 384K上下文可处理超长视频。

## 故障排除

| 错误 | 解决方案 |
|------|---------|
| FileNotFoundError | 检查文件路径是否正确 |
| APIError | 检查API密钥和网络连接 |
| CUDA out of memory | 使用更小的Whisper模型 |
| ProxyError | 减少上下文大小或检查代理设置 |
| Bilibili "deleted or geo-restricted" | 确认URL中BV号大小写正确 |

## 项目结构

```
video-summarizer/
├── main.py                      # 主入口（交互模式+单次模式）
├── config.py                    # 配置文件（API密钥等）
├── run.ps1                      # 启动脚本（交互/下载/单次/本地循环四模式）
├── CHANGELOG.md                 # 版本记录
├── README.md                    # 使用文档
├── requirements.txt             # Python依赖
├── llm/                         # LLM客户端
│   ├── base_client.py           # 通用基类（上下文管理、重试、缓存日志）
│   ├── kimi_client.py           # Kimi客户端
│   ├── deepseek_client.py       # DeepSeek客户端
│   ├── ollama_client.py         # Ollama客户端
│   └── adapter.py               # 适配器
├── pipeline/                    # 处理流程
│   ├── download.py              # 视频下载（URL清理、cookies）
│   ├── transcribe.py            # 语音转录（Whisper medium）
│   ├── correct.py               # 转录纠错（AI修正同音字/术语误识别）
│   ├── chunker.py               # 文本分段（模型自适应大小）
│   ├── summarize.py             # 总结调度（含缓存统计）
│   └── output.py                # 输出处理
├── summarizers/                 # 总结策略
│   ├── outline_summary.py       # 大纲模式（费曼学习法提示词）
│   ├── timeline_summary.py      # 时间线模式
│   └── map_reduce.py            # MapReduce模式
├── utils/                       # 工具模块
│   └── ai_logger.py             # AI缓存命中日志
└── output/                      # 输出目录
```

## 版本信息

当前版本：**v1.5.0** (2026-05-26)

查看完整版本记录：[CHANGELOG.md](CHANGELOG.md)

## 联系方式

如有问题或建议，请联系项目维护者。
