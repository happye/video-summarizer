# 开发指南

## 项目结构

```
video-summarizer/
├── main.py                      # 主入口
├── config.py                    # 配置文件
├── run.ps1                      # 启动脚本
├── pipeline/                    # 处理流程
│   ├── download.py              # 视频下载
│   ├── transcribe.py            # 语音转录
│   ├── correct.py               # 转录纠错
│   ├── chunker.py               # 文本分段
│   ├── summarize.py             # 摘要调度
│   └── output.py                # 输出处理
├── llm/                         # LLM 客户端
│   ├── base_client.py           # 通用基类
│   ├── kimi_client.py           # Kimi 客户端
│   ├── deepseek_client.py       # DeepSeek 客户端
│   ├── ollama_client.py         # Ollama 客户端
│   └── adapter.py               # 适配器
├── summarizers/                 # 摘要策略
│   ├── outline_summary.py       # 大纲模式
│   ├── timeline_summary.py      # 时间线模式
│   └── map_reduce.py            # MapReduce 模式
├── utils/                       # 工具模块
│   ├── transcript_loader.py     # 转录文本加载
│   └── ai_logger.py             # AI 缓存日志
├── docs/                        # 项目文档
│   ├── architecture.md          # 系统架构
│   ├── configuration.md         # 配置说明
│   ├── runbook.md               # 运维手册
│   └── development.md           # 开发指南（本文件）
└── output/                      # 输出目录
```

## 设计原则

1. **线性流水线**：每个阶段独立、可替换、基于中间文件
2. **懒加载**：pipeline 模块按需导入，交互模式秒进
3. **中间文件持久化**：确保可调试、可断点续跑、可崩溃恢复
4. **统一参数容器**：`ProcessArgs` 类作为模块级类，所有模式共用

## 新增 LLM 提供商

1. 在 `llm/` 下创建新客户端文件，如 `llm/new_provider_client.py`
2. 继承 `BaseLLMClient`，实现 `generate()` 方法
3. 在 `llm/adapter.py` 中注册新提供商
4. 在 `config.py` 中添加 API 密钥配置
5. 在 `main.py` 的 argparse 和交互命令中添加选项
6. 在 `run.ps1` 中添加选项

## 新增摘要策略

1. 在 `summarizers/` 下创建新策略文件
2. 实现摘要生成函数，接收 chunks 和参数，返回摘要文本
3. 在 `pipeline/summarize.py` 的 `generate_summary()` 中注册
4. 在 `main.py` 的 argparse 和交互命令中添加模式选项

## 新增处理阶段

1. 在 `pipeline/` 下创建新模块
2. 在 `process_video()` 中插入调用
3. 确保中间文件读写一致（输入路径、输出路径）

## 纠错模块注意事项

- 纠错使用 `difflib.SequenceMatcher` 做字符级对齐，将纠错文本映射回 segments
- 纠错文本同时写入 JSON 的 `text` 字段，确保下游即使映射失败也能读到纠错文本
- `transcript_loader` 优先读 `text` 字段，fallback 从 segments 拼接
- 不要用 `split()` 做中文分词映射，中文没有空格分词

## 踩坑记录

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| `WinError 32` 文件被占用 | 复制文件到自身 | 比较源和目标绝对路径，相同则跳过 |
| 中文路径解析错误 | 未处理引号/特殊字符 | 成对引号剥离、`os.path.normpath()` |
| 纠错 segments 映射失败 | `split()` 对中文无效 | 用 `difflib` 字符级对齐 |
| `too many values to unpack` | 函数返回值与接收变量数不匹配 | 检查函数签名的返回值数量 |
| ffmpeg 死锁 | `capture_output=True` 的 stderr 管道被填满 | `stdout=DEVNULL, stderr=PIPE` |
| Qwen3-ASR 推理极慢 | 模型加载到 CPU | 加载后手动 `_model.model.to("cuda")` |
| `language="zh"` 报错 | qwen-asr 要求语言全称 | 改为 `language="Chinese"` |
| librosa 加载超慢 | 默认走重采样路径 | 改用 `soundfile.read`（已是 16kHz 无需重采样） |
| 生成内容被截断 | 默认 `max_new_tokens=512` | 设为 8192 |

## 转录模型开发注意事项

- **模型路径**：ModelScope 在 Windows 下载时 `.` 会被替换为 `___`，所以 `Qwen3-ASR-1.7B` 实际目录是 `Qwen3-ASR-1___7B`
- **GPU 迁移**：`Qwen3ASRModel.from_pretrained(path, dtype=...)` 不会自动放到 GPU，必须加载后手动 `.to("cuda")`
- **长音频分块**：qwen-asr 内部按 `MAX_ASR_INPUT_SECONDS=1200`（20 分钟）自动分块，无需手动 VAD
- **标点符号**：Qwen3-ASR 自带标点输出，无需额外的标点恢复模型
- **音频输入**：传 `(numpy_array, sample_rate)` 元组，避免 qwen-asr 内部 subprocess 加载文件（Windows 兼容性更好）
