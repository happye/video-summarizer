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
