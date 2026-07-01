# 项目规则（VideoSummarize）

## 项目结构

```
main.py              # 入口、ProcessArgs、process_video 流水线
config.py            # 配置（API 密钥、CHUNK_SIZE、路径）— 在 .gitignore 中
pipeline/            # 转录、纠错、分块
summarizers/         # 三种摘要策略
llm/                 # LLM 适配器（Kimi/DeepSeek/Ollama）
utils/               # 工具函数
docs/                # 面向人类的文档
run.ps1              # PowerShell 启动器
```

## 红线（违反即事故）

- **禁止修改 `config.py` 中的 API 密钥并提交**（该文件在 .gitignore）
- **禁止用 `capture_output=True` 调用 ffmpeg** — Windows 上 stderr 管道会死锁
- **禁止用 `librosa.load` 加载长音频** — 36 分钟音频要几十秒，改用 `soundfile.read`
- **Qwen3-ASR 加载后必须手动 `.to("cuda")`** — `from_pretrained` 不会自动放到 GPU
- **qwen-asr 语言参数用全称 `"Chinese"`**，不是 `"zh"`
- **禁止改动 `main.py` 中 `process_video` 的返回值数量约定** — 多处按位置解包

## 命令速查

```bash
python main.py                                    # 交互模式
python main.py --local-loop --llm kimi            # 本地视频循环
python main.py --url "https://..." --llm deepseek # URL 处理
python main.py --file "video.mp4" --download-only # 仅下载
.\run.ps1                                         # PowerShell 菜单
```

## 踩坑警示

| 症状 | 根因 | 修复 |
|------|------|------|
| ASR 推理极慢（GPU 闲置） | 模型在 CPU | `_model.model.to("cuda")` |
| ffmpeg 卡住不返回 | stderr 管道满 | `stdout=DEVNULL, stderr=PIPE` |
| 中文纠错 segments 映射失败 | `split()` 对中文无效 | `difflib.SequenceMatcher` 字符级对齐 |
| `too many values to unpack` | `download_video` 返回 3 值 | 检查接收变量数 |
| ModelScope 下载路径异常 | Windows `.`→`___` 转换 | `_MODEL_CANDIDATES` 多路径兜底 |
| 生成内容被截断 | `max_new_tokens=512` 太小 | 设为 8192 |

## 深入文档指针

| 想了解 | 看这里 |
|--------|--------|
| 系统架构、数据流、模块职责 | docs/architecture.md |
| 配置项、命令行参数、模型选择 | docs/configuration.md |
| 故障排查、缓存日志、跳过机制 | docs/runbook.md |
| 新增模块/LLM/摘要策略、踩坑全记录 | docs/development.md |
| 完整版本变更历史 | CHANGELOG.md |
