# 版本记录

## v1.6.0 (2026-07-01)

### 重磅更新

- **转录模型升级**：Whisper → Qwen3-ASR-1.7B（阿里开源，Apache 2.0，中文 CER ~3.76%）
  - 中文识别精度大幅提升，达开源免费模型 Top 级别
  - 原生支持长音频（内部按 1200 秒自动分块，无需手动 VAD）
  - **自带标点符号输出**，解决了转录文本无标点导致分句困难的问题
  - 通过 `qwen-asr` PyPI 包加载，Windows 兼容
  - 移除 whisperx / pyannote-audio / ctranslate2 / pyav 等旧依赖
- **超长上下文优化**：充分利用 DeepSeek(378K) / Kimi(194K) 上下文窗口
  - CHUNK_SIZE 1200 → 8000，CHUNK_OVERLAP 200 → 800
  - `map_reduce.py` 新增单次全量模式：token 估算 ≤ 80% 上下文阈值时，单次 LLM 调用处理全部转录文本
  - 超出阈值才降级为传统 map-reduce

### Bug 修复

- **ffmpeg 管道阻塞**：`capture_output=True` 导致 ffmpeg stderr 进度输出填满管道缓冲区在 Windows 死锁，改为 `stdout=DEVNULL, stderr=PIPE`
- **Qwen3-ASR 模型加载到 CPU**：`Qwen3ASRModel.from_pretrained` 不会自动放到 GPU，加载后手动 `_model.model.to("cuda")`，否则推理慢 100 倍
- **语言参数错误**：`language="zh"` 不被 qwen-asr 接受，改为 `language="Chinese"`（全称）
- **librosa 加载超慢**：36 分钟音频 librosa.load 要几十秒，改用 `soundfile.read`（0.1 秒）
- **max_new_tokens 不足**：默认 512 对长音频不够（20 分钟中文约需 6000 tokens），设为 8192

### 性能数据

- 36 分钟中文视频：转录约 5 分钟（11752 字符），总结 49.81 秒（DeepSeek 单次全量，5445 字符摘要）
- GPU 利用率 93%（RTX 4080 SUPER，fp16，显存占用 15.6GB）

---

## v1.5.0 (2026-05-26)

### 新增功能

- **本地视频循环模式**：`--local-loop` 参数，专门用于循环处理本地已下载的视频
  - 直接输入视频文件路径或目录路径即可处理，无需 `file`/`local` 前缀
  - 自动识别路径类型（文件/目录）和视频格式
  - 支持运行中切换 LLM、摘要模式、强制重处理
  - 处理完自动等待下一个输入，`exit`/`quit`/`q` 退出
  - run.ps1 新增选项4：Local video loop

### Bug 修复

- **文件自复制导致 WinError 32**：`_process_file` 检测源文件与目标文件相同时跳过复制，直接使用原路径
- **路径特殊字符解析容错**：引号成对剥离、命令匹配收紧、`os.path.normpath()` 规范化路径
- **Args 类循环内重复创建**：提取为模块级 `ProcessArgs` 类，消除循环内重复定义
- **chunk_transcript() 多余参数报错**：移除调用时误传的 `llm_provider` 参数
- **中文纠错 segments 映射失败**：用 `difflib.SequenceMatcher` 字符级对齐替换 `split()` 分词映射，彻底修复中文场景下纠错结果无法写回 segments 的问题
- **纠错文本丢失**：`transcript_loader` 优先读取 JSON `text` 字段（纠错后的完整文本），不再仅从 segments 拼接
- **download_video 返回值解包报错**：`_process_url` 接收 3 个返回值并传入 `video_ext`，修复 `too many values to unpack`

---

## v1.4.0 (2026-05-23)

### 新增功能

- **仅下载模式**：下载视频但不转录和总结
  - 命令行参数 `--download-only`：`python main.py --url "视频URL" --download-only`
  - 交互模式命令 `download <视频链接>`：仅下载，不触发转录和总结
  - run.ps1 新增选项2：Download only（连续下载循环，输入 q 退出）
  - 仅下载模式下跳过 LLM 选择、API Key 检查、总结模式选择

### Bug 修复

- **下载标题被 yt-dlp 警告污染**：标题获取和下载流程分离 stderr，过滤 WARNING/ERROR 行，防止警告信息被当作视频标题
- **视频文件扩展名硬编码 .mp4**：`set_paths()` 和 `download_video()` 支持实际扩展名（.webm/.mkv/.mp4），不再强制 .mp4
- **下载成功但 yt-dlp 返回非0退出码时误报失败**：检查 temp 目录是否有视频文件，有则视为成功
- **SingleArgs 缺少 no_correct 属性**：`--no-correct` 参数在单次模式下被忽略
- **correct.py 纠错词数不匹配时静默丢弃结果**：添加警告日志
- **base_client.py retry_delay 被永久修改**：Timeout 重试改为局部计算退避时间，不污染实例变量

---

## v1.3.0 (2026-05-09)

### 新增功能

- **交互模式**：`python main.py` 或 `python main.py -i` 进入交互循环，处理完不退出，可连续处理多个视频
  - 支持 `url`/`local`/`file` 命令切换输入方式
  - 支持 `llm`/`mode`/`force` 命令实时切换模型和模式
  - 自动识别粘贴的URL或路径
- **本地视频目录**：`--local <目录>` 直接处理已下载的视频，跳过下载步骤，输出写入原目录
- **AI缓存命中日志**：前台输出 + `logs/ai_cache.log` 本地文件双记录
  - 支持 DeepSeek `prompt_cache_hit_tokens` / `prompt_cache_miss_tokens`
  - 支持 Kimi K2.x `cached_tokens` / `prompt_tokens_details.cached_tokens`
  - 每次请求显示 CACHE HIT / CACHE PARTIAL / CACHE MISS
  - 会话结束时输出缓存统计摘要
- **费曼学习法提示词优化**：outline_summary.py 提示词融入费曼学习法
  - 专业术语必须用大白话解释
  - 关键观点必须引用视频原话并展开说明
  - 抽象概念必须举例或打比方
- **run.ps1 双模式**：启动时选择交互模式或单次模式
- **AI转录纠错**：转录后自动用AI修正同音字、专业术语误识别等错误
  - 纠错结果保存为 `transcript_corrected.json`，不覆盖原始文件
  - 生成 `transcript_correction_diff.json` 差异记录，可追溯修改
  - 纠错失败自动降级到原始 transcript
  - `--no-correct` 参数可跳过纠错步骤

### 修复

- **修复 BV 号大小写导致 Bilibili 下载失败**：交互输入不再将 URL 小写化
- **修复 URL 反引号污染**：清理用户输入中可能包含的反引号和引号
- **修复调试命令缺少 cookies**：`--list-formats` 调试请求现在也携带 cookies
- **修复启动卡顿**：pipeline 模块改为懒加载，交互模式秒进（不再预加载 torch/whisper）

### 优化

- DeepSeek 上下文限制从 350K 调整为 378K tokens
- `ai_logger.py` 修复 `_detect_cache_hit` 逻辑，新增 Kimi `cached_tokens` 字段支持
- `ai_logger.py` 新增 `prompt_cache_miss_tokens` 追踪

---

## v1.2.0 (2026-04-24)

### 新增功能

- **DeepSeek API 完整集成**
  - 支持 `deepseek-v4-pro` 和 `deepseek-v4-flash` 模型
  - 充分利用 384K 上下文窗口
  - 独立的 API 连通性测试脚本 `test_deepseek.py`

- **通用 LLM 客户端基类**
  - 提取 `BaseLLMClient` 基类，统一上下文管理、重试、错误处理
  - 智能上下文压缩（token 估算、消息摘要、健康检查）

- **增强的启动脚本**
  - `run.ps1` 支持交互式选择 LLM 提供商和总结模式

### 修复与优化

- 修复中文文件名乱码问题
- 智能跳过已处理视频
- 修复 Kimi 长文本处理代理错误
- DeepSeek API URL 和模型名称修正

---

## v1.1.0 (2026-04-24)

### 新增功能

- Kimi 模型升级到 `kimi-k2.6`
- 性能追踪系统

### 修复

- 修复 GitHub 推送时的大文件问题

---

## v1.0.0 (2026-03-14)

### 主要功能

- 完整的视频总结流程：下载、转录、分段、总结
- 支持多种视频平台（YouTube、Bilibili等）
- 三种总结模式：大纲、时间线、MapReduce
- GPU加速的语音识别（OpenAI Whisper）
- 智能文本分段与上下文管理

## 未来计划

- [x] 支持 DeepSeek 模型
- [x] 交互模式
- [x] 本地视频目录处理
- [ ] 增加视频字幕提取功能
- [ ] 添加用户界面
- [ ] 支持更多语言的总结
