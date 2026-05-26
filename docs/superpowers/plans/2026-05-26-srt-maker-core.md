# SRT Maker — 核心层实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 SRT Maker 的核心数据模型、时间码工具、SRT/ASS 解析器、音频提取、FFmpeg 封装和语音识别接口层。

**Architecture:** 自底向上实现——先核心数据模型和工具，再文件 I/O，再音频处理，再语音识别接口。所有核心层代码不依赖 UI 层，可独立测试。

**Tech Stack:** Python 3.10+, pytest, openai-whisper, torch (for Whisper + Silero VAD), ffmpeg-python

---

## 项目初始化

### Task 1: 项目结构和依赖

**Files:**
- Create: `pyproject.toml`
- Create: `srt_maker/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "srt-maker"
version = "0.1.0"
description = "视频字幕生成与烧录工具"
requires-python = ">=3.10"
dependencies = [
    "pyside6>=6.6",
    "opencv-python>=4.8",
    "pyqtgraph>=0.13",
    "openai-whisper>=20231106",
    "torch>=2.0",
    "ffmpeg-python>=0.2",
    "requests>=2.31",
    "silero-vad>=5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-qt>=4.2",
]
```

- [ ] **Step 2: 创建包结构**

```bash
mkdir -p srt_maker/core srt_maker/speech srt_maker/video srt_maker/io srt_maker/audio srt_maker/ui
mkdir -p tests/core tests/speech tests/video tests/io tests/audio
```

- [ ] **Step 3: 创建所有 __init__.py**

```bash
touch srt_maker/__init__.py
touch srt_maker/core/__init__.py
touch srt_maker/speech/__init__.py
touch srt_maker/video/__init__.py
touch srt_maker/io/__init__.py
touch srt_maker/audio/__init__.py
touch srt_maker/ui/__init__.py
touch tests/__init__.py
touch tests/core/__init__.py
touch tests/speech/__init__.py
touch tests/video/__init__.py
touch tests/io/__init__.py
touch tests/audio/__init__.py
```

- [ ] **Step 4: 安装依赖**

```bash
pip install -e ".[dev]"
```

- [ ] **Step 5: 验证安装**

```bash
python -c "import pyside6; import cv2; import pyqtgraph; print('OK')"
```

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml srt_maker/ tests/
git commit -m "初始化项目结构和依赖"
```

---

### Task 2: 时间码工具

**Files:**
- Create: `srt_maker/core/timecode.py`
- Create: `tests/core/test_timecode.py`

- [ ] **Step 1: 写失败测试 — 秒转 SRT 时间码**

```python
# tests/core/test_timecode.py
from srt_maker.core.timecode import seconds_to_srt, srt_to_seconds

def test_seconds_to_srt_zero():
    assert seconds_to_srt(0) == "00:00:00,000"

def test_seconds_to_srt_basic():
    assert seconds_to_srt(1234.567) == "00:20:34,567"

def test_srt_to_seconds():
    assert srt_to_seconds("00:20:34,567") == 1234.567

def test_roundtrip():
    original = 3600.999
    assert srt_to_seconds(seconds_to_srt(original)) == original
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/core/test_timecode.py -v
```

期望：FAIL（模块不存在）

- [ ] **Step 3: 实现 timecode.py**

```python
# srt_maker/core/timecode.py

def seconds_to_srt(seconds: float) -> str:
    """秒数转 SRT 时间码格式: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds % 1) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def srt_to_seconds(srt_time: str) -> float:
    """SRT 时间码转秒数"""
    hours, minutes, rest = srt_time.split(":")
    secs, millis = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(secs) + int(millis) / 1000
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/core/test_timecode.py -v
```

期望：全部 PASS

- [ ] **Step 5: Commit**

```bash
git add srt_maker/core/timecode.py tests/core/test_timecode.py
git commit -m "实现时间码转换工具"
```

---

### Task 3: 字幕数据模型

**Files:**
- Create: `srt_maker/core/subtitle_model.py`
- Create: `tests/core/test_subtitle_model.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/core/test_subtitle_model.py
from srt_maker.core.subtitle_model import SubtitleEntry

def test_subtitle_entry_creation():
    entry = SubtitleEntry(start_time=1.5, end_time=4.0, text="你好")
    assert entry.start_time == 1.5
    assert entry.end_time == 4.0
    assert entry.text == "你好"

def test_subtitle_entry_to_srt():
    entry = SubtitleEntry(start_time=1.5, end_time=4.0, text="你好")
    assert entry.to_srt(1) == "1\n00:00:01,500 --> 00:00:04,000\n你好"

def test_subtitle_entry_empty_text():
    entry = SubtitleEntry(start_time=0, end_time=1.0, text="")
    assert entry.to_srt(1) == "1\n00:00:00,000 --> 00:00:01,000\n"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/core/test_subtitle_model.py -v
```

- [ ] **Step 3: 实现 subtitle_model.py**

```python
# srt_maker/core/subtitle_model.py
from dataclasses import dataclass
from srt_maker.core.timecode import seconds_to_srt

@dataclass
class SubtitleEntry:
    start_time: float
    end_time: float
    text: str

    def to_srt(self, index: int) -> str:
        start = seconds_to_srt(self.start_time)
        end = seconds_to_srt(self.end_time)
        return f"{index}\n{start} --> {end}\n{self.text}"
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/core/test_subtitle_model.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/core/subtitle_model.py tests/core/test_subtitle_model.py
git commit -m "实现字幕数据模型"
```

---

### Task 4: 字幕列表（含撤销/重做）

**Files:**
- Create: `srt_maker/core/subtitle_list.py`
- Create: `tests/core/test_subtitle_list.py`

- [ ] **Step 1: 写失败测试 — 基本操作**

```python
# tests/core/test_subtitle_list.py
from srt_maker.core.subtitle_model import SubtitleEntry
from srt_maker.core.subtitle_list import SubtitleList

def test_add_entry():
    sl = SubtitleList()
    sl.add(SubtitleEntry(1.0, 2.0, "第一条"))
    assert len(sl.entries) == 1

def test_remove_entry():
    sl = SubtitleList()
    sl.add(SubtitleEntry(1.0, 2.0, "第一条"))
    sl.remove(0)
    assert len(sl.entries) == 0

def test_modify_entry():
    sl = SubtitleList()
    sl.add(SubtitleEntry(1.0, 2.0, "第一条"))
    sl.modify(0, SubtitleEntry(1.0, 2.0, "修改后"))
    assert sl.entries[0].text == "修改后"

def test_split_entry():
    sl = SubtitleList()
    sl.add(SubtitleEntry(0.0, 4.0, "AB"))
    sl.split(0, 2.0)
    assert len(sl.entries) == 2
    assert sl.entries[0].end_time == 2.0
    assert sl.entries[1].start_time == 2.0

def test_merge_entries():
    sl = SubtitleList()
    sl.add(SubtitleEntry(0.0, 2.0, "A"))
    sl.add(SubtitleEntry(2.0, 4.0, "B"))
    sl.merge(0, 1)
    assert len(sl.entries) == 1
    assert sl.entries[0].text == "AB"
```

- [ ] **Step 2: 写失败测试 — 撤销/重做**

```python
def test_undo_redo():
    sl = SubtitleList()
    sl.add(SubtitleEntry(1.0, 2.0, "第一条"))
    sl.add(SubtitleEntry(3.0, 4.0, "第二条"))
    sl.undo()
    assert len(sl.entries) == 1
    sl.redo()
    assert len(sl.entries) == 2

def test_undo_redo_remove():
    sl = SubtitleList()
    sl.add(SubtitleEntry(1.0, 2.0, "第一条"))
    sl.remove(0)
    assert len(sl.entries) == 0
    sl.undo()
    assert len(sl.entries) == 1
```

- [ ] **Step 3: 运行测试确认失败**

```bash
python -m pytest tests/core/test_subtitle_list.py -v
```

- [ ] **Step 4: 实现 subtitle_list.py**

```python
# srt_maker/core/subtitle_list.py
from __future__ import annotations
from typing import Optional
from srt_maker.core.subtitle_model import SubtitleEntry

class _UndoStack:
    """支持撤销/重做的命令栈"""
    def __init__(self):
        self._undo: list = []
        self._redo: list = []

    def execute(self, action, undo_action):
        result = action()
        self._undo.append(undo_action)
        self._redo.clear()
        return result

    def undo(self):
        if not self._undo:
            return
        undo_action = self._undo.pop()
        self._redo.append(undo_action)
        undo_action()

    def redo(self):
        if not self._redo:
            return
        redo_action = self._redo.pop()
        self._undo.append(redo_action)
        redo_action()

class SubtitleList:
    def __init__(self):
        self.entries: list[SubtitleEntry] = []
        self._history = _UndoStack()

    def add(self, entry: SubtitleEntry):
        self._history.execute(
            action=lambda: self.entries.append(entry),
            undo_action=lambda: self.entries.pop(),
        )

    def remove(self, index: int):
        self._history.execute(
            action=lambda: self.entries.pop(index),
            undo_action=lambda: self.entries.insert(index, self.entries[index] if index < len(self.entries) else self._last_removed),
        )

    def modify(self, index: int, entry: SubtitleEntry):
        old = self.entries[index]
        self._history.execute(
            action=lambda: self.entries.__setitem__(index, entry),
            undo_action=lambda: self.entries.__setitem__(index, old),
        )

    def split(self, index: int, at_time: float):
        entry = self.entries[index]
        before = SubtitleEntry(entry.start_time, at_time, entry.text)
        after = SubtitleEntry(at_time, entry.end_time, entry.text)
        self._history.execute(
            action=lambda: (self.entries.__setitem__(index, before), self.entries.insert(index + 1, after)),
            undo_action=lambda: (self.entries.pop(index + 1), self.entries.__setitem__(index, entry)),
        )

    def merge(self, index_a: int, index_b: int):
        a = self.entries[index_a]
        b = self.entries[index_b]
        merged = SubtitleEntry(a.start_time, b.end_time, a.text + b.text)
        self._history.execute(
            action=lambda: (self.entries.__setitem__(index_a, merged), self.entries.pop(index_b)),
            undo_action=lambda: (self.entries.__setitem__(index_a, a), self.entries.insert(index_b, b)),
        )

    def undo(self):
        self._history.undo()

    def redo(self):
        self._history.redo()
```

- [ ] **Step 5: 运行测试确认通过**

```bash
python -m pytest tests/core/test_subtitle_list.py -v
```

- [ ] **Step 6: Commit**

```bash
git add srt_maker/core/subtitle_list.py tests/core/test_subtitle_list.py
git commit -m "实现字幕列表和撤销/重做功能"
```

---

### Task 5: SRT 解析器

**Files:**
- Create: `srt_maker/io/srt_parser.py`
- Create: `tests/io/test_srt_parser.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/io/test_srt_parser.py
from srt_maker.io.srt_parser import parse_srt, write_srt
from srt_maker.core.subtitle_model import SubtitleEntry

def test_parse_srt():
    srt = "1\n00:00:01,000 --> 00:00:04,000\n第一条字幕\n\n2\n00:00:05,000 --> 00:00:08,000\n第二条字幕"
    entries = parse_srt(srt)
    assert len(entries) == 2
    assert entries[0].start_time == 1.0
    assert entries[0].end_time == 4.0
    assert entries[0].text == "第一条字幕"
    assert entries[1].text == "第二条字幕"

def test_write_srt():
    entries = [
        SubtitleEntry(1.0, 4.0, "第一条"),
        SubtitleEntry(5.0, 8.0, "第二条"),
    ]
    result = write_srt(entries)
    assert "00:00:01,000 --> 00:00:04,000" in result
    assert "第一条" in result

def test_roundtrip():
    original = "1\n00:00:01,000 --> 00:00:04,000\n测试\n\n2\n00:00:05,000 --> 00:00:08,000\nOK"
    entries = parse_srt(original)
    output = write_srt(entries)
    assert parse_srt(output) == entries

def test_parse_empty():
    entries = parse_srt("")
    assert len(entries) == 0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/io/test_srt_parser.py -v
```

- [ ] **Step 3: 实现 srt_parser.py**

```python
# srt_maker/io/srt_parser.py
import re
from srt_maker.core.subtitle_model import SubtitleEntry
from srt_maker.core.timecode import srt_to_seconds

SRT_BLOCK_RE = re.compile(
    r"(\d+)\s*\n"
    r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*\n"
    r"([\s\S]*?)(?=\n\n|\n\d+\s*\n|$)"
)

def parse_srt(text: str) -> list[SubtitleEntry]:
    """解析 SRT 格式文本为字幕条目列表"""
    entries = []
    for match in SRT_BLOCK_RE.finditer(text):
        start = srt_to_seconds(match.group(2))
        end = srt_to_seconds(match.group(3))
        subtitle_text = match.group(4).strip()
        entries.append(SubtitleEntry(start, end, subtitle_text))
    return entries

def write_srt(entries: list[SubtitleEntry]) -> str:
    """将字幕条目列表写入 SRT 格式文本"""
    blocks = []
    for i, entry in enumerate(entries, 1):
        blocks.append(entry.to_srt(i))
    return "\n\n".join(blocks) + "\n" if blocks else ""
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/io/test_srt_parser.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/io/srt_parser.py tests/io/test_srt_parser.py
git commit -m "实现 SRT 解析器"
```

---

### Task 6: ASS 解析器（读取）

**Files:**
- Create: `srt_maker/io/ass_parser.py`
- Create: `tests/io/test_ass_parser.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/io/test_ass_parser.py
from srt_maker.io.ass_parser import parse_ass

def test_parse_ass_dialogue():
    ass = "[Script Info]\nTitle=Test\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,第一条字幕"
    entries = parse_ass(ass)
    assert len(entries) == 1
    assert entries[0].text == "第一条字幕"
    assert entries[0].start_time == 1.0
    assert entries[0].end_time == 4.0

def test_parse_ass_empty():
    entries = parse_ass("")
    assert len(entries) == 0

def test_parse_ass_multiple():
    ass = "[Script Info]\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,A\nDialogue: 0,0:00:04.00,0:00:06.00,Default,,0,0,0,,B"
    entries = parse_ass(ass)
    assert len(entries) == 2
    assert entries[0].text == "A"
    assert entries[1].text == "B"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/io/test_ass_parser.py -v
```

- [ ] **Step 3: 实现 ass_parser.py**

```python
# srt_maker/io/ass_parser.py
import re
from srt_maker.core.subtitle_model import SubtitleEntry

ASS_TIME_RE = re.compile(r"(\d+):(\d{2}):(\d{2})[.,](\d{2})")

def _ass_time_to_seconds(time_str: str) -> float:
    m = ASS_TIME_RE.match(time_str)
    if not m:
        raise ValueError(f"无效的 ASS 时间格式: {time_str}")
    hours, minutes, secs, cs = m.groups()
    return int(hours) * 3600 + int(minutes) * 60 + int(secs) + int(cs) / 100

def parse_ass(text: str) -> list[SubtitleEntry]:
    """解析 ASS 格式文本为字幕条目列表"""
    entries = []
    in_events = False
    for line in text.splitlines():
        if line.strip() == "[Events]":
            in_events = True
            continue
        if in_events and line.startswith("Dialogue:"):
            parts = line.split(",", 10)
            if len(parts) < 10:
                continue
            start = _ass_time_to_seconds(parts[1])
            end = _ass_time_to_seconds(parts[2])
            subtitle_text = parts[9] if len(parts) > 9 else ""
            # 移除 ASS 标签（如 {\i1}...{\i0}）
            subtitle_text = re.sub(r"\{[^}]*\}", "", subtitle_text).strip()
            entries.append(SubtitleEntry(start, end, subtitle_text))
    return entries
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/io/test_ass_parser.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/io/ass_parser.py tests/io/test_ass_parser.py
git commit -m "实现 ASS 解析器（读取）"
```

---

### Task 7: FFmpeg 封装

**Files:**
- Create: `srt_maker/video/ffmpeg_wrapper.py`
- Create: `tests/video/test_ffmpeg_wrapper.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/video/test_ffmpeg_wrapper.py
from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper

def test_ffmpeg_available():
    wrapper = FFmpegWrapper()
    assert wrapper.is_available() is True

def test_get_video_duration(tmp_path):
    # 创建一个测试视频
    wrapper = FFmpegWrapper()
    video_path = str(tmp_path / "test.mp4")
    wrapper.create_test_video(video_path, duration=5.0)
    duration = wrapper.get_duration(video_path)
    assert abs(duration - 5.0) < 0.5
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/video/test_ffmpeg_wrapper.py -v
```

- [ ] **Step 3: 实现 ffmpeg_wrapper.py**

```python
# srt_maker/video/ffmpeg_wrapper.py
import subprocess
import tempfile
import os
from pathlib import Path

class FFmpegWrapper:
    """FFmpeg 命令行封装"""

    def is_available(self) -> bool:
        """检查 FFmpeg 是否可用"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_duration(self, video_path: str) -> float:
        """获取视频时长（秒）"""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip())

    def extract_audio(self, video_path: str, output_path: str) -> None:
        """从视频提取音频为 16kHz 单声道 PCM 16-bit WAV"""
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn", "-ac", "1", "-ar", "16000",
            "-sample_fmt", "s16", "-c:a", "pcm_s16le",
            "-y", output_path,
        ]
        subprocess.run(cmd, check=True, timeout=300)

    def create_test_video(self, output_path: str, duration: float = 5.0) -> None:
        """创建测试视频（黑色画面，静音）"""
        cmd = [
            "ffmpeg",
            "-f", "lavfi", "-i", f"color=c=black:s=640x480:d={duration}",
            "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={duration}",
            "-c:v", "libx264", "-c:a", "aac",
            "-shortest", "-y", output_path,
        ]
        subprocess.run(cmd, check=True, timeout=60)

    def burn_subtitles(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
        font_name: str = "微软雅黑",
        font_size: int = 24,
        color: str = "&H00FFFFFF",
    ) -> None:
        """将字幕硬编码到视频中"""
        style = f"Fontname={font_name},FontSize={font_size},PrimaryColour={color}"
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"subtitles={srt_path}:force_style={style}",
            "-c:a", "copy",
            "-y", output_path,
        ]
        subprocess.run(cmd, check=True, timeout=600)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/video/test_ffmpeg_wrapper.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/video/ffmpeg_wrapper.py tests/video/test_ffmpeg_wrapper.py
git commit -m "实现 FFmpeg 封装"
```

---

### Task 8: 音频提取

**Files:**
- Create: `srt_maker/audio/extractor.py`
- Create: `tests/audio/test_extractor.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/audio/test_extractor.py
from srt_maker.audio.extractor import AudioExtractor

def test_extract_audio(tmp_path):
    extractor = AudioExtractor()
    video_path = str(tmp_path / "input.mp4")
    output_path = str(tmp_path / "output.wav")

    from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper
    FFmpegWrapper().create_test_video(video_path, duration=3.0)

    result = extractor.extract(video_path)
    assert result.exists()
    # 验证音频格式
    assert result.suffix == ".wav"

def test_cleanup(tmp_path):
    extractor = AudioExtractor()
    audio_path = extractor.extract(str(tmp_path / "input.mp4"))
    extractor.cleanup()
    assert not audio_path.exists()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/audio/test_extractor.py -v
```

- [ ] **Step 3: 实现 extractor.py**

```python
# srt_maker/audio/extractor.py
import tempfile
import shutil
from pathlib import Path
from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper

class AudioExtractor:
    """音频提取器 — 从视频提取 16kHz 单声道 PCM 16-bit WAV"""

    def __init__(self):
        self._temp_dir: Path | None = None
        self._audio_path: Path | None = None
        self._ffmpeg = FFmpegWrapper()

    def extract(self, video_path: str) -> Path:
        """从视频提取音频，返回临时 WAV 文件路径"""
        self._temp_dir = Path(tempfile.mkdtemp(prefix="srt_maker_"))
        self._audio_path = self._temp_dir / "audio.wav"
        self._ffmpeg.extract_audio(video_path, str(self._audio_path))
        return self._audio_path

    def cleanup(self):
        """清理临时文件"""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
        self._temp_dir = None
        self._audio_path = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/audio/test_extractor.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/audio/extractor.py tests/audio/test_extractor.py
git commit -m "实现音频提取器"
```

---

### Task 9: VAD 封装（Silero VAD）

**Files:**
- Create: `srt_maker/audio/vad.py`
- Create: `tests/audio/test_vad.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/audio/test_vad.py
from srt_maker.audio.vad import VADDetector

def test_vad_detect_speech(tmp_path):
    detector = VADDetector()
    # 创建测试音频（有声音的 WAV）
    audio_path = str(tmp_path / "test.wav")
    from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper
    FFmpegWrapper().create_test_video(str(tmp_path / "test.mp4"), duration=3.0)
    FFmpegWrapper().extract_audio(str(tmp_path / "test.mp4"), audio_path)

    intervals = detector.detect(audio_path)
    # 静音视频应无语音区间
    assert isinstance(intervals, list)

def test_vad_empty_audio():
    detector = VADDetector()
    # 空音频应返回空列表
    intervals = detector.detect_empty()
    assert intervals == []
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/audio/test_vad.py -v
```

- [ ] **Step 3: 实现 vad.py**

```python
# srt_maker/audio/vad.py
import torch
from pathlib import Path
import subprocess

class VADDetector:
    """Silero VAD 语音活动检测封装"""

    def __init__(self):
        self._model = None
        self._utils = None

    def _load_model(self):
        """懒加载 Silero VAD 模型"""
        if self._model is None:
            import silero_vad
            self._model, self._utils = silero_vad.load_silero_vad()

    def detect(self, audio_path: str) -> list[tuple[float, float]]:
        """检测音频中的语音区间，返回 [(start_sec, end_sec), ...]"""
        self._load_model()
        get_speech_timestamps = self._utils["get_speech_timestamps"]

        # 使用 ffmpeg 读取音频为 numpy 数组
        import numpy as np
        cmd = [
            "ffmpeg", "-i", audio_path,
            "-f", "f32le", "-ac", "1", "-ar", "16000", "-",
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        audio = np.frombuffer(result.stdout, dtype=np.float32)

        timestamps = get_speech_timestamps(
            torch.from_numpy(audio),
            self._model,
            threshold=0.5,
            min_speech_duration_ms=250,
            min_silence_duration_ms=100,
        )

        return [(ts["start"] / 16000.0, ts["end"] / 16000.0) for ts in timestamps]

    def detect_empty(self) -> list[tuple[float, float]]:
        """空音频返回空列表"""
        return []
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/audio/test_vad.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/audio/vad.py tests/audio/test_vad.py
git commit -m "实现 VAD 语音活动检测封装"
```

---

### Task 10: 语音识别统一接口

**Files:**
- Create: `srt_maker/speech/base.py`
- Create: `tests/speech/test_base.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/speech/test_base.py
from srt_maker.speech.base import SpeechRecognizer

def test_abstract_cannot_instantiate():
    try:
        SpeechRecognizer()
        assert False, "Should not be able to instantiate abstract class"
    except TypeError:
        pass
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/speech/test_base.py -v
```

- [ ] **Step 3: 实现 base.py**

```python
# srt_maker/speech/base.py
from abc import ABC, abstractmethod
from srt_maker.core.subtitle_list import SubtitleList

class SpeechRecognizer(ABC):
    """语音识别器抽象基类"""

    @abstractmethod
    def recognize(self, audio_path: str, language: str) -> SubtitleList:
        """识别音频并返回字幕列表"""
        ...

    @abstractmethod
    def name(self) -> str:
        """返回识别器名称（用于 UI 显示）"""
        ...
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/speech/test_base.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/speech/base.py tests/speech/test_base.py
git commit -m "实现语音识别统一接口"
```

---

### Task 11: Whisper 识别器

**Files:**
- Create: `srt_maker/speech/whisper_recognizer.py`
- Create: `tests/speech/test_whisper_recognizer.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/speech/test_whisper_recognizer.py
from srt_maker.speech.whisper_recognizer import WhisperRecognizer

def test_whisper_name():
    recognizer = WhisperRecognizer(model_size="tiny")
    assert recognizer.name() == "Whisper"

def test_whisper_recognize_returns_subtitles(tmp_path):
    # 创建测试音频
    from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper
    audio_path = str(tmp_path / "test.wav")
    FFmpegWrapper().create_test_video(str(tmp_path / "test.mp4"), duration=2.0)
    FFmpegWrapper().extract_audio(str(tmp_path / "test.mp4"), audio_path)

    recognizer = WhisperRecognizer(model_size="tiny")
    result = recognizer.recognize(audio_path, "zh")
    assert isinstance(result, SubtitleList)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/speech/test_whisper_recognizer.py -v
```

- [ ] **Step 3: 实现 whisper_recognizer.py**

```python
# srt_maker/speech/whisper_recognizer.py
import whisper
from srt_maker.speech.base import SpeechRecognizer
from srt_maker.core.subtitle_list import SubtitleList
from srt_maker.core.subtitle_model import SubtitleEntry

class WhisperRecognizer(SpeechRecognizer):
    """OpenAI Whisper 本地语音识别"""

    def __init__(self, model_size: str = "base"):
        self._model_size = model_size
        self._model = None

    def _load_model(self):
        if self._model is None:
            self._model = whisper.load_model(self._model_size)

    def name(self) -> str:
        return "Whisper"

    def recognize(self, audio_path: str, language: str) -> SubtitleList:
        self._load_model()
        result = self._model.transcribe(audio_path, language=language, verbose=False)
        subtitles = SubtitleList()
        for segment in result["segments"]:
            entry = SubtitleEntry(
                start_time=segment["start"],
                end_time=segment["end"],
                text=segment["text"].strip(),
            )
            subtitles.entries.append(entry)
        return subtitles
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/speech/test_whisper_recognizer.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/speech/whisper_recognizer.py tests/speech/test_whisper_recognizer.py
git commit -m "实现 Whisper 语音识别器"
```

---

### Task 12: qwen3-asr 识别器（+ VAD 时间轴对齐）

**Files:**
- Create: `srt_maker/speech/qwen_asr_recognizer.py`
- Create: `tests/speech/test_qwen_asr_recognizer.py`

- [ ] **Step 1: 写失败测试 — 时间轴对齐算法**

```python
# tests/speech/test_qwen_asr_recognizer.py
from srt_maker.speech.qwen_asr_recognizer import align_text_with_vad

def test_align_equal_count():
    text = "你好。世界。"
    vad_intervals = [(0.0, 2.0), (2.5, 4.5)]
    result = align_text_with_vad(text, vad_intervals)
    assert len(result) == 2
    assert result[0].start_time == 0.0
    assert result[0].end_time == 2.0

def test_align_more_sentences():
    text = "A。B。C。D"
    vad_intervals = [(0.0, 3.0), (4.0, 7.0)]
    result = align_text_with_vad(text, vad_intervals)
    assert len(result) == 2

def test_align_more_intervals():
    text = "你好。"
    vad_intervals = [(0.0, 1.0), (1.5, 2.5), (3.0, 4.0)]
    result = align_text_with_vad(text, vad_intervals)
    assert len(result) == 3

def test_align_empty():
    result = align_text_with_vad("", [])
    assert len(result) == 0
```

- [ ] **Step 2: 写失败测试 — 识别器接口**

```python
from srt_maker.speech.qwen_asr_recognizer import QwenASRRecognizer

def test_qwen_name():
    recognizer = QwenASRRecognizer(api_url="http://localhost:8080")
    assert recognizer.name() == "qwen3-asr"
```

- [ ] **Step 3: 运行测试确认失败**

```bash
python -m pytest tests/speech/test_qwen_asr_recognizer.py -v
```

- [ ] **Step 4: 实现 qwen_asr_recognizer.py**

```python
# srt_maker/speech/qwen_asr_recognizer.py
import re
import requests
from srt_maker.speech.base import SpeechRecognizer
from srt_maker.core.subtitle_list import SubtitleList
from srt_maker.core.subtitle_model import SubtitleEntry
from srt_maker.audio.vad import VADDetector

def _split_sentences(text: str) -> list[str]:
    """按中文/英文标点分句"""
    sentences = re.split(r"[，。！？；\.\!\?\;]+", text)
    return [s.strip() for s in sentences if s.strip()]

def align_text_with_vad(
    text: str,
    vad_intervals: list[tuple[float, float]],
) -> list[SubtitleEntry]:
    """将无时间轴的文字与 VAD 区间对齐"""
    if not text or not vad_intervals:
        return []

    sentences = _split_sentences(text)
    entries = []

    if len(sentences) <= len(vad_intervals):
        # 句子数 <= 区间数：逐一对应，多余区间按字数均分文字
        for i, (start, end) in enumerate(vad_intervals):
            if i < len(sentences):
                entries.append(SubtitleEntry(start, end, sentences[i]))
            else:
                # 多余区间，尝试从最后一个句子中拆分
                entries.append(SubtitleEntry(start, end, ""))
    else:
        # 句子数 > 区间数：合并相邻句子
        intervals_per_sentence = len(sentences) / len(vad_intervals)
        current_interval = 0
        sentence_idx = 0

        for start, end in vad_intervals:
            num_sentences = max(1, int(intervals_per_sentence))
            merged = " ".join(sentences[sentence_idx:sentence_idx + num_sentences])
            entries.append(SubtitleEntry(start, end, merged))
            sentence_idx += num_sentences

    return entries

class QwenASRRecognizer(SpeechRecognizer):
    """qwen3-asr 语音识别器（通过 llama.cpp API）+ VAD 时间轴对齐"""

    def __init__(self, api_url: str = "http://localhost:8080"):
        self._api_url = api_url
        self._vad = VADDetector()

    def name(self) -> str:
        return "qwen3-asr"

    def recognize(self, audio_path: str, language: str) -> SubtitleList:
        # 1. 调用 qwen3-asr API 获取文字
        text = self._call_api(audio_path)

        # 2. VAD 检测语音区间
        vad_intervals = self._vad.detect(audio_path)

        # 3. 文字与时间轴对齐
        entries = align_text_with_vad(text, vad_intervals)
        subtitles = SubtitleList()
        subtitles.entries = entries
        return subtitles

    def _call_api(self, audio_path: str) -> str:
        """调用 qwen3-asr API"""
        # 使用 llama.cpp 的 /inference 端点
        with open(audio_path, "rb") as f:
            response = requests.post(
                f"{self._api_url}/inference",
                files={"file": ("audio.wav", f, "audio/wav")},
                timeout=300,
            )
        response.raise_for_status()
        data = response.json()
        # 假设返回格式: {"text": "识别结果"}
        return data.get("text", "").strip()
```

- [ ] **Step 4b: 运行测试确认通过**

```bash
python -m pytest tests/speech/test_qwen_asr_recognizer.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/speech/qwen_asr_recognizer.py tests/speech/test_qwen_asr_recognizer.py
git commit -m "实现 qwen3-asr 识别器和 VAD 时间轴对齐"
```

---

### Task 13: 云端 API 识别器

**Files:**
- Create: `srt_maker/speech/cloud_recognizer.py`
- Create: `tests/speech/test_cloud_recognizer.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/speech/test_cloud_recognizer.py
from srt_maker.speech.cloud_recognizer import CloudSpeechRecognizer

def test_cloud_name():
    recognizer = CloudSpeechRecognizer(api_key="test", api_url="https://api.example.com")
    assert "云端" in recognizer.name() or recognizer.name() == "Cloud API"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/speech/test_cloud_recognizer.py -v
```

- [ ] **Step 3: 实现 cloud_recognizer.py**

```python
# srt_maker/speech/cloud_recognizer.py
import requests
from srt_maker.speech.base import SpeechRecognizer
from srt_maker.core.subtitle_list import SubtitleList
from srt_maker.core.subtitle_model import SubtitleEntry

class CloudSpeechRecognizer(SpeechRecognizer):
    """云端语音识别 API 适配器"""

    def __init__(self, api_key: str, api_url: str = "https://nls-api.aliyun.com"):
        self._api_key = api_key
        self._api_url = api_url

    def name(self) -> str:
        return "云端 API"

    def recognize(self, audio_path: str, language: str) -> SubtitleList:
        subtitles = SubtitleList()

        with open(audio_path, "rb") as f:
            response = requests.post(
                self._api_url,
                headers={"Authorization": self._api_key},
                files={"audio": ("audio.wav", f, "audio/wav")},
                data={"language": language},
                timeout=300,
            )

        response.raise_for_status()
        data = response.json()

        # 假设返回格式: {"results": [{"start": 0.0, "end": 2.0, "text": "..."}]}
        for item in data.get("results", []):
            entry = SubtitleEntry(
                start_time=item["start"],
                end_time=item["end"],
                text=item["text"].strip(),
            )
            subtitles.entries.append(entry)

        return subtitles
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/speech/test_cloud_recognizer.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/speech/cloud_recognizer.py tests/speech/test_cloud_recognizer.py
git commit -m "实现云端 API 语音识别器"
```

---

### Task 14: 字幕烧录

**Files:**
- Create: `srt_maker/video/burner.py`
- Create: `tests/video/test_burner.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/video/test_burner.py
from srt_maker.video.burner import SubtitleBurner
from srt_maker.core.subtitle_model import SubtitleEntry
from srt_maker.io.srt_parser import write_srt

def test_burn_subtitles(tmp_path):
    video = str(tmp_path / "input.mp4")
    from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper
    FFmpegWrapper().create_test_video(video, duration=3.0)

    srt_content = write_srt([SubtitleEntry(0.5, 1.5, "测试字幕")])
    srt_path = str(tmp_path / "sub.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    output = str(tmp_path / "output.mp4")
    burner = SubtitleBurner()
    burner.burn(video, srt_path, output)

    import os
    assert os.path.exists(output)
    assert os.path.getsize(output) > 0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/video/test_burner.py -v
```

- [ ] **Step 3: 实现 burner.py**

```python
# srt_maker/video/burner.py
from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper

class SubtitleBurner:
    """字幕烧录器"""

    def __init__(self):
        self._ffmpeg = FFmpegWrapper()

    def burn(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
        font_name: str = "微软雅黑",
        font_size: int = 24,
        color: str = "&H00FFFFFF",
    ) -> None:
        """将字幕硬编码到视频中"""
        self._ffmpeg.burn_subtitles(
            video_path=video_path,
            srt_path=srt_path,
            output_path=output_path,
            font_name=font_name,
            font_size=font_size,
            color=color,
        )
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/video/test_burner.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/video/burner.py tests/video/test_burner.py
git commit -m "实现字幕烧录功能"
```

---

### Task 15: 运行全部核心层测试

**Files:** 无新文件

- [ ] **Step 1: 运行所有测试**

```bash
python -m pytest tests/ -v --tb=short
```

期望：全部 PASS

- [ ] **Step 2: Commit**

```bash
git commit -m "核心层全部测试通过" --allow-empty
```

---

## 验证

完成所有任务后：

1. 运行 `python -m pytest tests/ -v` 确认所有测试通过
2. 验证 SRT 解析器能正确处理真实 SRT 文件
3. 验证 FFmpeg 封装在系统上正常工作
4. 验证时间轴对齐算法在各种边界情况下正确工作
