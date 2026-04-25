# 版本记录

## v1.2.0 (2026-04-24)

### 新增功能

- **DeepSeek API 完整集成**
  - 支持 `deepseek-v4-pro` 和 `deepseek-v4-flash` 模型
  - 充分利用 384K 上下文窗口（之前被限制为 64K）
  - 独立的 API 连通性测试脚本 `test_deepseek.py`
  - API 文档：https://api-docs.deepseek.com/

- **通用 LLM 客户端基类**
  - 提取 `BaseLLMClient` 基类，统一上下文管理、重试、错误处理
  - Kimi 和 DeepSeek 共享相同的超长文本处理能力
  - 智能上下文压缩（token 估算、消息摘要、健康检查）
  - 代理错误快速失败，避免无意义重试

- **增强的启动脚本**
  - `run.ps1` 支持交互式选择 LLM 提供商（Kimi / DeepSeek / Ollama）
  - 支持交互式选择总结模式（Outline / Timeline / MapReduce）
  - 自动检测对应 API Key 是否配置

### 修复与优化

- **修复中文文件名乱码问题**
  - `subprocess` 添加 `encoding='utf-8'` 正确读取中文标题
  - yt-dlp 添加 `--no-restrict-filenames` 保留 Unicode 字符
  - 统一返回清理后的文件名，确保路径合法

- **智能跳过已处理视频**
  - 如果 `output` 目录已存在视频和总结文件，自动跳过下载和处理
  - 避免重复下载和重复调用 API

- **修复 Kimi 长文本处理代理错误**
  - 上下文超过 20 个 chunk 时不再无限重连
  - Token 超过限制时自动压缩历史消息

- **DeepSeek API 修正**
  - 修复 API URL：`https://api.deepseek.com/chat/completions`
  - 更新模型名称：`deepseek-v4-pro`
  - 增加超时时间到 300 秒

### 配置变更

- `config.py` 新增 `DEEPSEEK_API_KEY` 配置项
- DeepSeek 默认上下文限制：350K tokens（之前 60K）
- DeepSeek 默认消息限制：100 条（之前 30 条）

---

## v1.1.0 (2026-04-24)

### 新增功能

- Kimi 模型升级到 `kimi-k2.6`
- 性能追踪系统（请求耗时、成功率统计）

### 修复

- 修复 GitHub 推送时的大文件问题
- 清理仓库，排除 `yt-dlp` 等超大文件

---

## v1.0.0 (2026-03-14)

### 主要功能

- 实现了完整的视频总结流程：下载、转录、分段、总结
- 支持多种视频平台（YouTube、Bilibili等）
- 支持本地视频文件处理
- 提供三种总结模式：大纲、时间线、MapReduce
- 按视频名称分类的目录结构
- GPU加速的语音识别
- 智能文本分段与上下文管理
- 基于Kimi API的高质量视频总结

### 技术实现

- 使用OpenAI Whisper进行语音识别
- 使用PyTorch和CUDA进行GPU加速
- 使用yt-dlp进行视频下载
- 使用LangChain进行文本分段
- 使用Kimi API进行文本总结
- 实现了API调用的重试机制
- 动态路径管理，支持按视频名称分类

### 配置选项

- 可配置LLM提供商（kimi、ollama、deepseek）
- 可配置总结模式和详细程度
- 可调整文本分段参数

### 优化与修复

- 修复了PyTorch 2.6序列化问题
- 修复了Kimi API超时问题
- 优化了上下文管理，提高总结连贯性
- 优化了目录结构，提高文件管理效率
- 修复了路径处理中的空格和中文字符问题

## 未来计划

- [x] 支持 DeepSeek 模型
- [ ] 增加视频字幕提取功能
- [ ] 优化长视频处理能力
- [ ] 添加用户界面
- [ ] 支持更多语言的总结
- [ ] 增加视频内容分析功能
