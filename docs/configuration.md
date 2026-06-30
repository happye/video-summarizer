# 配置说明

## config.py 配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `MODEL_PROVIDER` | str | `"kimi"` | 默认 LLM 提供商 |
| `OLLAMA_MODEL` | str | `"qwen2.5"` | Ollama 模型名称 |
| `KIMI_API_KEY` | str | `""` | Kimi (Moonshot AI) API 密钥 |
| `DEEPSEEK_API_KEY` | str | `""` | DeepSeek API 密钥 |
| `CHUNK_SIZE` | int | `8000` | 文本分段大小（字符数），充分利用 DeepSeek/Kimi 超长上下文 |
| `CHUNK_OVERLAP` | int | `800` | 分段重叠字符数 |
| `SUMMARY_STYLE` | str | `"outline"` | 默认摘要模式 |
| `SUMMARY_DETAIL_LEVEL` | int | `2` | 摘要详细程度（1-5） |
| `SUMMARY_BULLET_COUNT` | int | `10` | 要点数量 |
| `BASE_DIR` | str | `"output"` | 输出根目录 |

## API 密钥获取

| 提供商 | 获取地址 | 说明 |
|--------|---------|------|
| Kimi | https://platform.moonshot.cn/ | 默认推荐，超长上下文 |
| DeepSeek | https://platform.deepseek.com/ | 高性价比，384K 上下文 |
| Ollama | 无需密钥 | 本地运行，需先安装 Ollama |

## 支持的 LLM 模型

| 提供商 | 模型 | 上下文长度 | 特点 |
|--------|------|-----------|------|
| Kimi | `kimi-k2.6` | 200K+ | 默认推荐，超长上下文 |
| DeepSeek | `deepseek-v4-pro` | 384K | 推理能力强 |
| DeepSeek | `deepseek-v4-flash` | 384K | 更快更便宜 |
| Ollama | `qwen2.5` 等 | 取决于模型 | 本地运行，无需联网 |

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--url` | 视频 URL（支持 YouTube、Bilibili 等） |
| `--file` | 本地视频文件路径 |
| `--local` | 本地视频目录路径 |
| `--llm` | LLM 提供商（`kimi`/`deepseek`/`ollama`） |
| `--mode` | 摘要模式（`outline`/`timeline`/`mapreduce`） |
| `--detail-level` | 详细程度（1-5） |
| `--bullet-count` | 要点数量 |
| `--force` | 强制重新处理 |
| `--no-correct` | 跳过转录纠错 |
| `--download-only` | 仅下载视频 |
| `--interactive` / `-i` | 交互模式 |
| `--local-loop` | 本地视频循环模式 |

## 交互模式命令

| 命令 | 说明 |
|------|------|
| `url <链接>` | 从 URL 下载并处理 |
| `download <链接>` | 仅下载 |
| `local <目录>` | 处理本地目录 |
| `file <文件>` | 处理本地文件 |
| `llm <提供商>` | 切换 LLM |
| `mode <模式>` | 切换摘要模式 |
| `force` | 切换强制重处理 |
| `help` | 显示帮助 |
| `exit` / `quit` / `q` | 退出 |

## 支持的视频格式

`.mp4` `.mkv` `.webm` `.avi` `.mov` `.flv` `.wmv` `.ts` `.mp3` `.wav` `.m4a` `.flac`
