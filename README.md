# 视频总结系统

基于 AI 的视频总结工具：自动下载视频、转录语音、纠错、分段、生成结构化摘要。

## 快速开始

```bash
git clone https://github.com/happye/video-summarizer
cd video-summarizer
pip install -r requirements.txt
```

编辑 `config.py` 填写 API 密钥，然后运行：

```powershell
.\run.ps1
```

或直接进入交互模式：

```bash
python main.py
```

## 功能一览

- 自动视频下载（YouTube、Bilibili 等）
- GPU 加速语音识别（Qwen3-ASR，中文专精，自带标点）
- AI 转录纠错（同音字、术语误识别）
- 三种摘要模式：大纲 / 时间线 / MapReduce
- 三种 LLM 提供商：Kimi / DeepSeek / Ollama
- 四种运行模式：交互 / 仅下载 / 单次 / 本地循环
- 智能跳过已处理视频，AI 缓存命中日志

## 命令示例

```bash
python main.py                                          # 交互模式
python main.py --local-loop --llm kimi                  # 本地视频循环
python main.py --url "https://..." --llm deepseek       # URL 处理
python main.py --local "D:\Videos" --mode timeline      # 本地目录
python main.py --file "video.mp4" --download-only       # 仅下载
```

## 摘要模式

| 模式 | 输出格式 | 适用场景 |
|------|---------|---------|
| **Outline** | `I. → A. → 1.` 层次编号 | 知识讲座、投资分析（推荐） |
| **Timeline** | `MM:SS 事件描述` | 直播回放、会议记录 |
| **MapReduce** | 要点式综合摘要 | 超长视频；DeepSeek/Kimi 单次全量优先 |

## 文档

| 文档 | 说明 |
|------|------|
| [架构设计](docs/architecture.md) | 系统架构、处理流水线、模块职责、数据流 |
| [配置说明](docs/configuration.md) | config.py 配置项、命令行参数、交互命令 |
| [运维手册](docs/runbook.md) | 故障排查、缓存日志、跳过机制 |
| [开发指南](docs/development.md) | 新增模块/LLM/摘要策略、踩坑记录 |
| [版本记录](CHANGELOG.md) | 完整版本变更历史 |

## 版本

当前版本：**v1.6.0** (2026-07-01)
