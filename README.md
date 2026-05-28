# SRT Maker

[English](#srt-maker) | [中文](#srt-maker--视频字幕生成与烧录工具)

---

Generate subtitles from video via AI speech recognition, edit them visually, and burn them into the final video.

## Quick Start

```bash
git clone https://github.com/stoptimer/srt_maker.git
cd srt_maker
pip install -e "."

python -m srt_maker.main
```

## Requirements

| Dependency | Description |
|------------|-------------|
| Python 3.10+ | Runtime |
| FFmpeg | Required for audio extraction and subtitle burning |
| CUDA (optional) | GPU acceleration for Whisper |

### FFmpeg Configuration

FFmpeg path resolved in this order:

1. `ffmpeg_dir` configured in app settings
2. `ffmpeg/` next to the executable (bundled with PyInstaller builds)
3. `FFMPEG_DIR` environment variable
4. System PATH

If FFmpeg is not found, the app will prompt you to configure the path via settings.

### GPU Acceleration (Optional)

Install CUDA-enabled PyTorch for faster Whisper recognition:

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## Features

- **Speech recognition**: Three engines — Whisper (local), qwen3-asr (llama.cpp local deployment), cloud API (Alibaba Cloud NLS)
- **Subtitle editing**: Table editor with undo/redo, split/merge entries
- **Waveform view**: Audio waveform visualization with subtitle interval highlights
- **Video preview**: Play video with auto-highlight of current subtitle
- **Subtitle burning**: Hardcode subtitles into video with customizable font, size, and color
- **Import/Export**: Import SRT and ASS formats, export SRT

## Using as a Library

```python
import asyncio
from srt_maker.audio.extractor import AudioExtractor
from srt_maker.speech.whisper_recognizer import WhisperRecognizer
from srt_maker.io.srt_parser import write_srt
from srt_maker.video.burner import SubtitleBurner

async def main():
    with AudioExtractor() as extractor:
        audio_path = extractor.extract("input.mp4")

        recognizer = WhisperRecognizer(model="base")
        subtitles = await recognizer.recognize(audio_path, "zh")

    print(write_srt(subtitles.entries))

    burner = SubtitleBurner()
    burner.burn("input.mp4", "subtitle.srt", "output.mp4")

asyncio.run(main())
```

See [Usage Guide](docs/usage.md) for more API examples.

## Development

```bash
pip install -e ".[dev]"
pytest -v
pyinstaller srt_maker.spec
```

## Tech Stack

Python 3.10+ · PySide6 · OpenAI Whisper · qwen3-asr · FFmpeg · Silero VAD · PyQtGraph · OpenCV

## Project Structure

```
srt_maker/
├── main.py                # Entry point
├── core/                  # Core business layer (UI-independent)
│   ├── subtitle_model.py  # SubtitleEntry data class
│   ├── subtitle_list.py   # SubtitleList with undo/redo
│   ├── timecode.py        # Timecode utilities
│   ├── config.py          # Configuration management
│   └── logger.py          # Logging system
├── speech/                # Speech recognition layer
│   ├── base.py            # SpeechRecognizer abstract interface
│   ├── whisper_recognizer.py
│   ├── qwen_asr_recognizer.py
│   └── cloud_recognizer.py
├── video/                 # Video processing layer
│   ├── ffmpeg_wrapper.py  # FFmpeg wrapper
│   └── burner.py          # Subtitle burning
├── audio/                 # Audio processing layer
│   ├── extractor.py       # Audio extraction
│   └── vad.py             # VAD speech activity detection
├── io/                    # File I/O layer
│   ├── srt_parser.py      # SRT read/write
│   └── ass_parser.py      # ASS reading
└── ui/                    # UI layer
    ├── main_window.py     # Main window
    ├── video_preview.py   # Video preview
    ├── waveform_view.py   # Waveform display
    ├── subtitle_editor.py # Subtitle editor
    ├── style_panel.py     # Style panel
    ├── recognition_worker.py
    ├── burn_worker.py
    ├── settings_dialog.py
    └── log_viewer.py
```

---

# SRT Maker — 视频字幕生成与烧录工具

从视频中通过 AI 语音识别自动生成字幕，支持可视化编辑和硬编码烧录。

## 快速开始

```bash
git clone https://github.com/stoptimer/srt_maker.git
cd srt_maker
pip install -e "."

python -m srt_maker.main
```

## 环境要求

| 依赖 | 说明 |
|------|------|
| Python 3.10+ | 运行环境 |
| FFmpeg | 必需，用于音频提取和字幕烧录 |
| CUDA（可选） | Whisper GPU 加速 |

### FFmpeg 配置

FFmpeg 路径按以下优先级解析：

1. 程序设置中配置的 `ffmpeg_dir`
2. 打包目录下的 `ffmpeg/`（PyInstaller 打包后自动附带）
3. `FFMPEG_DIR` 环境变量
4. 系统 PATH

未找到 FFmpeg 时程序会提示通过设置界面配置路径。

### GPU 加速（可选）

安装 CUDA 版本的 PyTorch 以加速 Whisper 识别：

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## 功能

- **语音识别**：支持 Whisper（本地）、qwen3-asr（llama.cpp 本地部署）、云端 API（阿里云 NLS）三种识别方式
- **字幕编辑**：表格编辑、撤销/重做、拆分/合并字幕条目
- **波形图**：音频波形可视化，高亮字幕对应区间
- **视频预览**：播放视频，自动高亮当前字幕
- **字幕烧录**：硬编码烧录到视频，支持自定义字体、大小和颜色
- **导入/导出**：支持 SRT 和 ASS 格式导入，SRT 格式导出

## 作为库使用

```python
import asyncio
from srt_maker.audio.extractor import AudioExtractor
from srt_maker.speech.whisper_recognizer import WhisperRecognizer
from srt_maker.io.srt_parser import write_srt
from srt_maker.video.burner import SubtitleBurner

async def main():
    with AudioExtractor() as extractor:
        audio_path = extractor.extract("input.mp4")

        recognizer = WhisperRecognizer(model="base")
        subtitles = await recognizer.recognize(audio_path, "zh")

    print(write_srt(subtitles.entries))

    burner = SubtitleBurner()
    burner.burn("input.mp4", "subtitle.srt", "output.mp4")

asyncio.run(main())
```

更多 API 示例见 [使用说明](docs/usage.md)。

## 开发

```bash
pip install -e ".[dev]"
pytest -v
pyinstaller srt_maker.spec
```

## 技术栈

Python 3.10+ · PySide6 · OpenAI Whisper · qwen3-asr · FFmpeg · Silero VAD · PyQtGraph · OpenCV

## 项目结构

```
srt_maker/
├── main.py                # 入口
├── core/                  # 核心业务层（不依赖 UI）
│   ├── subtitle_model.py  # SubtitleEntry 数据类
│   ├── subtitle_list.py   # 字幕列表（含撤销/重做）
│   ├── timecode.py        # 时间码工具
│   ├── config.py          # 配置管理
│   └── logger.py          # 日志系统
├── speech/                # 语音识别层
│   ├── base.py            # SpeechRecognizer 抽象接口
│   ├── whisper_recognizer.py
│   ├── qwen_asr_recognizer.py
│   └── cloud_recognizer.py
├── video/                 # 视频处理层
│   ├── ffmpeg_wrapper.py  # FFmpeg 封装
│   └── burner.py          # 字幕烧录
├── audio/                 # 音频处理层
│   ├── extractor.py       # 音频提取
│   └── vad.py             # VAD 语音活动检测
├── io/                    # 文件 I/O 层
│   ├── srt_parser.py      # SRT 读写
│   └── ass_parser.py      # ASS 读取
└── ui/                    # UI 层
    ├── main_window.py     # 主窗口
    ├── video_preview.py   # 视频预览
    ├── waveform_view.py   # 波形图
    ├── subtitle_editor.py # 字幕编辑器
    ├── style_panel.py     # 样式面板
    ├── recognition_worker.py
    ├── burn_worker.py
    ├── settings_dialog.py
    └── log_viewer.py
```
