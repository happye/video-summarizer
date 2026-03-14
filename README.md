# 视频总结系统使用文档

## 项目简介

视频总结系统是一个基于AI的工具，能够自动下载视频、提取音频、转录内容、分段处理并生成详细的视频总结。系统支持多种视频平台，包括YouTube、Bilibili等。

## 功能特点

- 自动视频下载与处理
- GPU加速的语音识别（使用OpenAI Whisper）
- 智能文本分段与上下文管理
- 基于Kimi API的高质量视频总结
- 按视频名称分类的目录结构
- 支持多种总结模式（大纲、时间线、MapReduce）

## 系统要求

- Python 3.10+
- CUDA兼容的GPU（推荐，用于加速语音识别）
- 足够的磁盘空间（用于存储视频和处理文件）
- 稳定的网络连接（用于下载视频和调用API）

## 安装步骤

### 1. 克隆项目

```bash
git clone <项目地址>
cd <项目目录>
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置API密钥

编辑 `config.py` 文件，填写你的Kimi API密钥：

```python
KIMI_API_KEY = "your_kimi_api_key_here"
```

### 4. 安装yt-dlp

系统会自动下载并配置yt-dlp，用于视频下载。

## 使用方法

### 命令行参数

- `--url`：视频URL（支持YouTube、Bilibili等）
- `--file`：本地视频文件路径
- `--llm`：LLM提供商（支持ollama、kimi、deepseek，默认kimi）
- `--mode`：总结模式（支持outline、timeline、mapreduce，默认outline）
- `--detail-level`：总结详细程度（1-5，默认2）
- `--bullet-count`：要点数量（默认10）

### 示例命令

#### 1. 处理在线视频

```bash
python main.py --url "https://www.bilibili.com/video/BV1bpQeY2EvH" --llm kimi --mode outline
```

#### 2. 处理本地视频

```bash
python main.py --file "path/to/video.mp4" --llm kimi --mode outline
```

## 输出结果

处理完成后，系统会在 `output` 目录下创建以视频名称命名的文件夹，包含以下文件：

- `<视频名称>.mp4`：下载或复制的视频文件
- `transcript.json`：完整的语音转录结果
- `chunks.json`：文本分段结果
- `partial_summary.json`：部分总结结果（用于调试）
- `summary.md`：最终的视频总结（Markdown格式）

## 常见问题

### 1. GPU加速问题

如果系统没有使用GPU，请检查：
- 已安装CUDA兼容的PyTorch
- GPU驱动已正确安装
- 系统支持CUDA

### 2. API超时问题

系统已实现自动重试机制，默认最多重试3次。如果仍然超时，请检查网络连接或尝试使用更短的视频。

### 3. 视频下载失败

请确保网络连接稳定，并且视频URL格式正确。系统支持大多数主流视频平台。

## 故障排除

- **错误：FileNotFoundError**：检查文件路径是否正确，确保文件存在
- **错误：APIError**：检查API密钥是否正确，网络连接是否稳定
- **错误：CUDA out of memory**：尝试使用更小的视频或降低模型大小

## 性能优化

- 使用GPU加速可以显著提高转录速度
- 对于长视频，建议使用MapReduce模式进行总结
- 调整 `CHUNK_SIZE` 和 `CHUNK_OVERLAP` 参数可以优化分段效果

## 联系方式

如有问题或建议，请联系项目维护者。