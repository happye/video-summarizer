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
- **智能跳过已处理视频**，避免重复下载和API调用
- **中文文件名保留**，不乱码

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

### 5. 依赖版本管理

为确保系统稳定性，我们提供了详细的依赖版本记录。如果遇到环境问题，可以使用以下命令安装特定版本的依赖：

```bash
pip install -r dependencies.txt
```

`dependencies.txt`文件包含了所有依赖的详细版本信息，确保系统在不同环境中都能正常运行。

## 使用方法

### 方式一：使用启动脚本（推荐）

双击运行 `run.ps1`，按提示选择：

1. **选择LLM提供商**：输入 1 (Kimi)、2 (DeepSeek) 或 3 (Ollama)
2. **选择总结模式**：输入 1 (Outline)、2 (Timeline) 或 3 (MapReduce)
3. **输入视频URL**：直接粘贴URL，或按回车使用默认测试视频

```powershell
# PowerShell 中运行
.\run.ps1
```

### 方式二：命令行直接运行

#### 命令行参数

- `--url`：视频URL（支持YouTube、Bilibili等）
- `--file`：本地视频文件路径
- `--llm`：LLM提供商（`kimi`、`deepseek`、`ollama`，默认`kimi`）
- `--mode`：总结模式（`outline`、`timeline`、`mapreduce`，默认`outline`）
- `--detail-level`：总结详细程度（1-5，默认2）
- `--bullet-count`：要点数量（默认10）

#### 示例命令

**使用 Kimi 处理在线视频（默认）**
```bash
python main.py --url "https://www.bilibili.com/video/BV1bpQeY2EvH"
```

**使用 DeepSeek 处理在线视频**
```bash
python main.py --url "https://www.bilibili.com/video/BV1bpQeY2EvH" --llm deepseek
```

**使用 Kimi 处理本地视频**
```bash
python main.py --file "path/to/video.mp4" --llm kimi --mode outline
```

**使用 DeepSeek 生成时间线总结**
```bash
python main.py --url "视频URL" --llm deepseek --mode timeline
```

### 方式三：API连通性测试

测试各模型API是否配置正确：

```bash
# 测试 Kimi
python test_kimi.py

# 测试 DeepSeek
python test_deepseek.py
```

## 输出结果

处理完成后，系统会在 `output` 目录下创建以视频名称命名的文件夹，包含以下文件：

- `<视频名称>.mp4`：下载或复制的视频文件
- `transcript.json`：完整的语音转录结果
- `chunks.json`：文本分段结果
- `partial_summary.json`：部分总结结果（用于调试）
- `summary.md`：最终的视频总结（Markdown格式）

## 智能跳过机制

如果 `output/<视频名称>/` 目录下已经存在：
- 视频文件（`.mp4`）
- 总结文件（`summary.md`）

系统会自动跳过下载和处理，直接输出提示信息。这避免了：
- 重复下载相同视频
- 重复调用API产生额外费用
- 重复生成相同内容

如需重新处理，请删除对应的 `output/<视频名称>/` 文件夹。

## 常见问题

### 1. GPU加速问题

如果系统没有使用GPU，请检查：
- 已安装CUDA兼容的PyTorch
- GPU驱动已正确安装
- 系统支持CUDA

### 2. API超时问题

系统已实现自动重试机制：
- 超时：最多重试5次，动态增加等待时间
- 限流(429)：指数退避重试
- 代理错误：快速失败，提示检查代理设置

### 3. 视频下载失败

请确保网络连接稳定，并且视频URL格式正确。系统支持大多数主流视频平台。

### 4. 中文文件名乱码

已修复。系统现在会：
- 正确读取中文视频标题
- 保留中文字符在文件名中
- 自动替换Windows非法字符（`:`、`|`、`?`、`*`等）

### 5. 长视频处理中断

对于超长视频（20+ chunk），系统会自动：
- 估算上下文token数
- 超过限制时压缩历史消息为摘要
- 保留最近的消息和系统提示

## 故障排除

- **错误：FileNotFoundError**：检查文件路径是否正确，确保文件存在
- **错误：APIError**：检查API密钥是否正确，网络连接是否稳定
- **错误：CUDA out of memory**：尝试使用更小的视频或降低模型大小
- **错误：ProxyError**：请求可能过大，或代理设置有问题，尝试减少上下文大小

## 性能优化

- 使用GPU加速可以显著提高转录速度
- 对于长视频，建议使用MapReduce模式进行总结
- 调整 `CHUNK_SIZE` 和 `CHUNK_OVERLAP` 参数可以优化分段效果
- **DeepSeek v4** 支持 384K 上下文，可以处理更长的视频而无需频繁分段

## 项目结构

```
video-summarizer/
├── main.py                      # 主入口
├── config.py                    # 配置文件（API密钥等）
├── run.ps1                      # 启动脚本
├── CHANGELOG.md                 # 版本记录
├── README.md                    # 使用文档
├── requirements.txt             # Python依赖
├── llm/                         # LLM客户端
│   ├── base_client.py           # 通用基类（上下文管理、重试）
│   ├── kimi_client.py           # Kimi客户端
│   ├── deepseek_client.py       # DeepSeek客户端
│   ├── ollama_client.py         # Ollama客户端
│   └── adapter.py               # 适配器
├── pipeline/                    # 处理流程
│   ├── download.py              # 视频下载
│   ├── transcribe.py            # 语音转录
│   ├── chunker.py               # 文本分段
│   ├── summarize.py             # 总结调度
│   └── output.py                # 输出处理
├── summarizers/                 # 总结策略
│   ├── outline_summary.py       # 大纲模式
│   ├── timeline_summary.py      # 时间线模式
│   └── map_reduce.py            # MapReduce模式
└── output/                      # 输出目录
```

## 版本信息

当前版本：**v1.2.0** (2026-04-24)

查看完整版本记录：[CHANGELOG.md](CHANGELOG.md)

## 联系方式

如有问题或建议，请联系项目维护者。
