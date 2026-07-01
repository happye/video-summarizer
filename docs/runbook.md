# 运维手册

## 快速启动

```powershell
.\run.ps1
```

选择运行模式：
1. 交互模式（推荐）
2. 仅下载
3. 单次模式
4. 本地视频循环

## 前置依赖

- Python 3.10+
- CUDA 兼容 GPU（推荐，加速语音识别，建议 ≥8GB 显存）
- ffmpeg（音频提取）
- Ollama（仅使用本地模型时需要）

## 故障排查

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `FileNotFoundError` | 文件路径错误 | 检查路径，中文路径需加引号 |
| `APIError` | API 密钥或网络问题 | 检查 config.py 密钥、网络连接 |
| `CUDA out of memory` | GPU 显存不足 | Qwen3-ASR fp16 需 ~16GB，可改 CPU 模式（慢） |
| ASR 推理极慢 | 模型加载到 CPU | 检查日志 `device: cuda`，确认 `_model.model.to("cuda")` |
| `language "zh" not supported` | 语言参数错误 | qwen-asr 要求全称 `Chinese`，不是 ISO code |
| ffmpeg 死锁 | `capture_output=True` 管道阻塞 | 已修复，用 `stdout=DEVNULL, stderr=PIPE` |
| `ProxyError` | 代理/上下文过大 | 减少上下文大小或检查代理 |
| Bilibili "deleted or geo-restricted" | BV 号大小写或地区限制 | 直接粘贴 URL，不要手动改 BV 号 |
| `[WinError 32]` | 文件被占用 | 关闭占用进程，或用 `--force` |
| `too many values to unpack` | download_video 返回值不匹配 | 确保使用最新代码 |

## AI 缓存日志

系统自动记录 API 缓存命中情况：
- 日志文件：`logs/ai_cache.log`
- DeepSeek：`prompt_cache_hit_tokens` / `prompt_cache_miss_tokens`
- Kimi K2.x：`cached_tokens` / `prompt_tokens_details.cached_tokens`
- 每次请求显示：CACHE HIT / CACHE PARTIAL / CACHE MISS

## 智能跳过机制

- `output/<视频名称>/` 已存在视频和 summary.md → 自动跳过
- `--force` 参数强制重新处理
- 交互模式用 `force` 命令切换

## 纠错相关

- 纠错结果保存为 `transcript_corrected.json`，不覆盖原始文件
- 生成 `transcript_correction_diff.json` 差异记录
- 纠错失败自动降级到原始 transcript
- `--no-correct` 参数可跳过纠错步骤
- 如需重新纠错，删除 `_corrected.json` 文件后重新运行

## API 连通性测试

```bash
python test_kimi.py
python test_deepseek.py
```
