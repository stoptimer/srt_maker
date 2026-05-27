# 识别流程实现设计

## 概述

当前 `_start_recognition()` 方法是空壳，点击后只显示"识别中..."但无任何实际执行。本设计实现完整的语音识别流程：音频提取 → 识别器调用 → 结果展示，并通过 QThread 工作线程提供实时进度反馈。

## 背景

- **问题**：用户点击"开始识别"后，左下角状态栏显示"识别中..."，但没有任何实际执行，也没有进度反馈，用户无法判断是否正常运行。
- **根因**：`MainWindow._start_recognition()` 仅有 TODO 注释，未实现音频提取、识别器调用、结果展示等任何步骤。
- **目标**：实现完整的识别流程，用户能看到进度条动态更新，确认任务正在执行。

## 技术选型

**方案：QThread + QObject 信号槽**

为识别任务创建独立的 QThread 工作线程，通过 Qt Signal 将进度和结果传回主线程。这是 Qt 原生线程模式，与项目现有架构一致。

## 数据流

```
用户点击"开始识别"
  → 禁用菜单项，显示进度条，状态栏"正在提取音频..."
  → [子线程] AudioExtractor.extract() 提取音频
  → 进度信号: "正在提取音频...", 10%
  → [子线程] 根据选择创建识别器实例
  → 进度信号: "正在加载模型...", 20%
  → [子线程] recognizer.recognize(audio_path, language)
  → 进度信号: "正在识别语音...", 50%
  → [子线程] 识别完成，返回 SubtitleList
  → 进度信号: "正在处理结果...", 90%
  → [主线程] 加载字幕到表格、波形图
  → 进度信号: "识别完成", 100%
  → 恢复菜单项，隐藏进度条
```

## 新增文件

### `srt_maker/ui/recognition_worker.py`

识别工作线程对象，继承 `QObject`，通过 `moveToThread()` 放入 QThread 执行。

**信号定义**：
```python
progress = Signal(str, int)      # (步骤描述, 百分比)
finished = Signal(SubtitleList)  # 识别完成
error = Signal(str)              # 识别失败
```

**公开方法**：
```python
def start(self, video_path: str, recognizer_type: str, language: str, model_size: str = "base")
```

**内部流程**：
1. 发射 `progress("正在提取音频...", 10)`
2. 调用 `AudioExtractor.extract(video_path)` 获取音频路径
3. 发射 `progress("正在加载模型...", 20)`
4. 根据 `recognizer_type` 创建识别器实例：
   - `"Whisper"` → `WhisperRecognizer(model_size)`
   - `"qwen3-asr"` → `QwenASRRecognizer()`
   - `"云端API"` → `CloudSpeechRecognizer(api_key)`
5. 发射 `progress("正在识别语音...", 50)`
6. 调用 `asyncio.run(recognizer.recognize(audio_path, language))`
7. 发射 `progress("正在处理结果...", 90)`
8. 发射 `finished(subtitles)` 或 `error(message)`
9. 清理临时音频文件

**Whisper 模型缓存**：
类级别变量 `_model_cache: dict[str, whisper.Model] = {}`，按 model_size 缓存已加载模型，避免重复加载。WhisperRecognizer 的 `_load_model()` 方法改为从缓存读取。

## 修改文件

### `srt_maker/ui/main_window.py`

**新增成员变量**：
```python
self._worker: RecognitionWorker | None = None
self._worker_thread: QThread | None = None
```

**修改 `_start_recognition()` 方法**：
- 检查是否已有视频文件
- 创建 `RecognitionWorker` 和 `QThread`
- 连接信号：
  - `worker.progress` → 更新进度条和状态栏
  - `worker.finished` → 加载结果并清理
  - `worker.error` → 显示错误对话框并清理
- 启动线程，调用 `worker.start()`
- 禁用"开始识别"菜单项

**新增 `_on_recognition_finished()` 方法**：
- 将字幕加载到 `SubtitleEditor`
- 加载音频波形到 `WaveformView`
- 高亮所有字幕区间
- 更新状态栏显示字幕条数
- 清理线程资源

**新增 `_on_recognition_error()` 方法**：
- 弹出 QMessageBox 显示错误信息
- 清理线程资源

**新增 `_cleanup_worker()` 方法**：
- 停止线程、删除 worker 对象
- 恢复菜单项状态
- 隐藏进度条

### `srt_maker/speech/whisper_recognizer.py`

**修改 `_load_model()` 方法**：
- 使用类级别缓存 `_model_cache`，避免重复加载模型
- 缓存按 `model_size` 键值存储

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| FFmpeg 未安装 | 发射 error("未找到 FFmpeg，请安装后重试") |
| Whisper 模型下载失败 | 发射 error("模型下载失败，请检查网络连接") |
| qwen3-asr API 不可达 | 发射 error("无法连接 llama.cpp 服务，请检查服务是否运行") |
| 音频提取失败 | 发射 error(f"音频提取失败: {e}") |
| 识别超时 | 300 秒超时，发射 error("识别超时，请重试") |

## 测试策略

- **单元测试**：`RecognitionWorker.start()` 各步骤是否按序发射正确的进度信号
- **集成测试**：使用 Whisper mock 模型测试完整流程（视频→音频→识别→字幕）
- **UI 测试**：点击开始识别，验证进度条更新、状态栏变化、结果展示
