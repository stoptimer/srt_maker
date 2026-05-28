# SRT Maker — 视频字幕生成与烧录工具

桌面应用程序，支持从视频中通过 AI 语音识别自动生成字幕，提供字幕编辑功能，并将字幕硬编码烧录到视频中。

## 功能特性

- **三种语音识别方式**：OpenAI Whisper（本地 GPU 加速）、qwen3-asr（llama.cpp 本地部署）、云端 API（阿里云 NLS）
- **可视化字幕编辑**：表格编辑、撤销/重做、拆分/合并字幕条目
- **音频波形图**：实时显示音频波形，高亮字幕对应区间
- **视频预览**：逐帧播放视频，支持拖动进度条
- **字幕烧录**：将字幕硬编码到视频中，支持自定义字体、大小和颜色
- **超长字幕自动拆分**：避免 FFmpeg libass 换行导致第二行被裁剪
- **导入/导出**：支持 SRT 和 ASS 格式导入，SRT 格式导出

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| UI 框架 | PySide6 (Qt6) |
| 本地语音识别 | OpenAI Whisper + llama.cpp (qwen3-asr) |
| 云端语音识别 | 阿里云 NLS |
| VAD | Silero VAD |
| 视频处理 | FFmpeg |
| 波形图 | PyQtGraph |
| 视频预览 | OpenCV |
| 目标平台 | Windows 11 |

## 安装

```bash
# 克隆仓库
git clone git@github.com:stoptimer/srt_maker.git
cd srt_maker

# 安装依赖
pip install -e ".[dev]"
```

## 运行

```bash
python -m srt_maker.main
```

## 环境要求

### FFmpeg（必需）

程序依赖 FFmpeg 进行音频提取和字幕烧录。FFmpeg 路径按以下优先级解析：

1. 设置对话框中配置的 `ffmpeg_dir`
2. 打包目录下的 `ffmpeg/`（PyInstaller 打包后）
3. `FFMPEG_DIR` 环境变量
4. 系统 PATH

如果未找到 FFmpeg，程序会提示用户通过"设置 > 设置"配置路径。

### GPU 加速（可选）

Whisper 识别支持 CUDA GPU 加速。需要安装 CUDA 版本的 PyTorch：

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### qwen3-asr（可选）

需要运行 llama.cpp 服务，默认地址 `http://localhost:8080`。

## 数据流

```
视频文件 → FFmpeg 提取音频(16kHz 单声道 PCM 16-bit WAV)
  → 语音识别器(Whisper / qwen3-asr / 云端 API)
  → 字幕数据(SubtitleEntry 列表)
  → UI 展示(波形图 + 字幕表格)
  → 用户编辑
  → 导出 SRT 或 FFmpeg 烧录
```

## 项目结构

```
srt_maker/
├── main.py                # 入口
├── core/                  # 核心业务层（不依赖 UI）
│   ├── subtitle_model.py  # SubtitleEntry 数据类
│   ├── subtitle_list.py   # SubtitleList（含撤销/重做）
│   ├── timecode.py        # 时间码工具
│   ├── config.py          # 配置文件管理
│   └── logger.py          # 日志系统
├── speech/                # 语音识别层
│   ├── base.py            # SpeechRecognizer ABC
│   ├── whisper_recognizer.py
│   ├── qwen_asr_recognizer.py
│   └── cloud_recognizer.py
├── video/                 # 视频处理层
│   ├── ffmpeg_wrapper.py  # FFmpeg 封装
│   └── burner.py          # 字幕烧录
├── audio/                 # 音频处理层
│   ├── extractor.py       # 音频提取
│   └── vad.py             # VAD 封装
├── io/                    # 文件 I/O 层
│   ├── srt_parser.py      # SRT 读写
│   └── ass_parser.py      # ASS 读取
└── ui/                    # UI 层
    ├── main_window.py
    ├── video_preview.py
    ├── waveform_view.py
    ├── subtitle_editor.py
    ├── style_panel.py
    ├── recognition_worker.py
    ├── burn_worker.py
    ├── settings_dialog.py
    └── log_viewer.py
```

## 测试

```bash
pytest -v
```

## 打包

```bash
pyinstaller srt_maker.spec
```
