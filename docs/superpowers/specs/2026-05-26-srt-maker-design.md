# SRT Maker — 视频字幕生成与烧录工具

## 概述

桌面应用程序，支持从视频中通过 AI 语音识别自动生成字幕，提供字幕编辑功能，并将字幕硬编码烧录到视频中。

## 技术栈

| 类别 | 选择 |
|------|------|
| 语言 | Python 3.10+ |
| UI 框架 | PySide6 (Qt6) |
| 本地语音识别 | OpenAI Whisper + llama.cpp 部署的 qwen3-asr |
| 云端语音识别 | 云端 API（阿里云/腾讯云等） |
| VAD（语音活动检测） | Silero VAD |
| 视频处理 | FFmpeg |
| 波形图 | PyQtGraph |
| 视频预览 | OpenCV + QLabel |
| 目标平台 | Windows 11 |

## 架构

### 模块划分

```
srt_maker/
├── ui/                    # UI 层
│   ├── main_window.py     # 主窗口
│   ├── video_preview.py   # 视频预览组件
│   ├── waveform_view.py   # 波形图组件
│   ├── subtitle_editor.py # 字幕编辑器（表格）
│   └── style_panel.py     # 字幕样式面板
├── core/                  # 核心业务层
│   ├── subtitle_model.py  # 字幕数据模型
│   ├── subtitle_list.py   # 字幕列表（含撤销/重做）
│   └── timecode.py        # 时间码工具
├── speech/                # 语音识别层
│   ├── base.py            # 抽象接口
│   ├── whisper_recognizer.py    # 本地 Whisper
│   ├── qwen_asr_recognizer.py  # qwen3-asr + VAD
│   └── cloud_recognizer.py      # 云端 API
├── video/                 # 视频处理层
│   ├── ffmpeg_wrapper.py  # FFmpeg 封装
│   ├── player.py          # 视频播放器
│   └── burner.py          # 字幕烧录
├── io/                    # 文件 I/O 层
│   ├── srt_parser.py      # SRT 读写
│   └── ass_parser.py      # ASS 读取
├── audio/                 # 音频处理层
│   ├── extractor.py       # 音频提取（FFmpeg）
│   └── vad.py             # VAD 封装（Silero）
└── main.py                # 入口
```

### 数据流

```
视频文件
  → FFmpeg 提取音频（16kHz 单声道 PCM 16-bit WAV）
  → 语音识别器（Whisper / qwen3-asr / 云端 API）
  → 字幕数据（SubtitleEntry 列表）
  → UI 展示（波形图 + 字幕表格）
  → 用户编辑
  → 导出 SRT 或 FFmpeg 烧录
```

## 语音识别层

### 统一接口

```python
class SpeechRecognizer(ABC):
    @abstractmethod
    async def recognize(self, audio_path: str, language: str) -> SubtitleList: ...
    @abstractmethod
    def on_progress(self) -> Signal: ...
```

### Whisper 识别器

- 使用 `openai-whisper` 库
- 直接返回带时间轴的字幕条目
- 支持模型选择（tiny/base/small/medium/large）
- 需要 GPU 获得较好性能

### qwen3-asr 识别器

- 调用 llama.cpp 部署的 qwen3-asr API
- **音频要求**：16kHz 单声道 WAV（PCM 16-bit），不满足需 FFmpeg 转换
- **返回纯文字**（无时间轴），需通过 VAD 生成时间轴

**时间轴对齐流程**：

1. FFmpeg 提取音频 → 16kHz 单声道 PCM 16-bit WAV
2. 音频送入 qwen3-asr API → 返回完整文字
3. 同一音频送入 Silero VAD → 返回语音区间列表
4. 文字分句（按标点符号：，。！？；）
5. 将分句按顺序分配到 VAD 区间：
   - 句子数 ≤ 区间数：逐一对应
   - 句子数 > 区间数：合并相邻句子到同一区间
   - 区间数 > 句子数：在句子内部按字数均分
6. 生成 SubtitleEntry 列表

### 云端 API 识别器

- 通过 HTTP 调用云端语音识别服务（首期支持阿里云语音识别）
- 返回带时间轴的字幕条目
- API Key 通过设置界面配置，存储于本地配置文件（不提交到版本控制）

## 音频预处理

**FFmpeg 转换命令**（所有识别方式统一）：

```bash
ffmpeg -i input.mp4 -vn -ac 1 -ar 16000 -sample_fmt s16 -c:a pcm_s16le output.wav
```

- `-vn`：去除视频流
- `-ac 1`：单声道
- `-ar 16000`：16kHz 采样率
- `-sample_fmt s16`：16-bit 采样格式
- `-c:a pcm_s16le`：PCM 编码

**临时文件管理**：提取的音频文件存于 `%TEMP%/srt_maker/`，识别完成后自动清理。

## UI 设计

### 主窗口布局（上下结构）

```
┌─────────────────────────────────────────────────────────┐
│  菜单栏: 文件 | 编辑 | 识别 | 烧录 | 帮助                    │
├─────────────────────────────────────────────────────────┤
│  工具栏: [打开视频] [开始识别 ▾] [导出SRT] [烧录字幕]      │
│           识别方式: [qwen3-asr ▾]  语言: [中文 ▾]         │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────────┬───────────────┐               │
│  │   视频预览区域         │   字幕样式    │               │
│  │   (OpenCV 帧渲染)     │   面板       │               │
│  │  [◀] [▶] [▌▌] 进度条  │  字体/大小/颜色 │             │
│  └──────────────────────┴───────────────┘               │
├─────────────────────────────────────────────────────────┤
│  音频波形图 (pyqtgraph) - 蓝色区块表示字幕区间             │
├─────────────────────────────────────────────────────────┤
│  字幕编辑器（表格：序号 | 开始时间 | 结束时间 | 文本）       │
├─────────────────────────────────────────────────────────┤
│  状态栏: 视频时长 | 字幕条数 | 状态                        │
└─────────────────────────────────────────────────────────┘
```

### 交互逻辑

- 点击波形图中的语音区间 → 定位到对应字幕条目
- 点击字幕列表 → 视频跳转到对应时间点，波形图高亮区间
- 拖拽波形图中的字幕边界 → 调整时间轴
- 右键字幕条目 → 拆分/合并/删除
- 视频播放时自动高亮当前字幕条目

## 数据模型

```python
@dataclass
class SubtitleEntry:
    start_time: float   # 开始时间（秒）
    end_time: float     # 结束时间（秒）
    text: str           # 字幕文本

class SubtitleList:
    entries: list[SubtitleEntry]
    # 支持撤销/重做（命令模式）
    # 操作：添加、删除、修改、拆分、合并
```

## 字幕烧录

**FFmpeg 硬编码**：

```bash
ffmpeg -i video.mp4 -vf "subtitles=subtitle.srt:force_style=Fontname=微软雅黑,FontSize=24,PrimaryColour=&H00FFFFFF" -c:a copy output.mp4
```

- 支持字体、大小、颜色设置
- 使用 FFmpeg 的 subtitles 滤镜
- 烧录前在视频预览中预览效果（生成临时带字幕视频）

## 文件 I/O

- **SRT**：完整读写支持
- **ASS**：读取支持（转换为内部模型）
- 导出时自动重新编号

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| FFmpeg 未安装 | 提示下载并配置路径 |
| 视频格式不支持 | 显示支持的格式列表 |
| 识别失败 | 显示错误原因，允许重试 |
| 磁盘空间不足 | 烧录前检查 |
| qwen3-asr API 不可用 | 提示检查 llama.cpp 服务 |

## 测试策略

- **单元测试**：SRT 解析、时间轴对齐算法、VAD 区间匹配、时间码转换
- **集成测试**：完整识别流程（视频 → 音频 → 识别 → 字幕）
- **UI 测试**：关键交互路径（打开视频、识别、编辑、导出、烧录）
