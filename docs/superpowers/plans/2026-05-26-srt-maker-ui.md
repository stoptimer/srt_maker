# SRT Maker — UI 层实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 SRT Maker 的 PySide6 桌面 UI，包括主窗口、视频预览、波形图、字幕编辑器、样式面板和入口点。

**Architecture:** 先实现各独立组件，再组合到主窗口。视频预览使用 OpenCV 逐帧读取 + QLabel 显示。波形图使用 PyQtGraph。字幕编辑器使用 QTableWidget。

**Tech Stack:** PySide6, OpenCV, PyQtGraph

---

## 前置条件

核心层（[2026-05-26-srt-maker-core.md](2026-05-26-srt-maker-core.md)）已完成。

---

### Task 1: 视频预览组件

**Files:**
- Create: `srt_maker/ui/video_preview.py`
- Create: `tests/ui/test_video_preview.py`

- [ ] **Step 0: 创建测试目录**

```bash
mkdir -p tests/ui
touch tests/ui/__init__.py
```

- [ ] **Step 1: 写失败测试**

```python
# tests/ui/test_video_preview.py
import pytest
from PySide6.QtWidgets import QApplication
from srt_maker.ui.video_preview import VideoPreview

@pytest.mark.qt_no_exception_capture
def test_video_preview_creation(qtbot):
    widget = VideoPreview()
    qtbot.add_widget(widget)
    assert widget is not None

@pytest.mark.qt_no_exception_capture
def test_video_preview_load_video(qtbot, tmp_path):
    from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper
    video_path = str(tmp_path / "test.mp4")
    FFmpegWrapper().create_test_video(video_path, duration=2.0)

    widget = VideoPreview()
    qtbot.add_widget(widget)
    widget.load_video(video_path)
    assert widget.duration() > 0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/ui/test_video_preview.py -v
```

- [ ] **Step 3: 实现 video_preview.py**

```python
# srt_maker/ui/video_preview.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap
import cv2

class VideoPreview(QWidget):
    """视频预览组件 — 使用 OpenCV 逐帧读取"""

    seek_requested = Signal(float)  # 跳转信号（秒）

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cap: cv2.VideoCapture | None = None
        self._duration = 0.0
        self._fps = 30.0
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer)
        self._playing = False
        self._current_frame = b""

        layout = QVBoxLayout(self)

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("background-color: #1a1a2e;")
        layout.addWidget(self._label)

        controls = QHBoxLayout()
        self._play_btn = QPushButton("▶")
        self._play_btn.clicked.connect(self.toggle_play)
        self._seek_slider = QSlider(Qt.Horizontal)
        self._seek_slider.valueChanged.connect(self._on_seek)
        controls.addWidget(self._play_btn)
        controls.addWidget(self._seek_slider)
        layout.addLayout(controls)

    def load_video(self, path: str) -> None:
        """加载视频文件"""
        self._stop()
        self._cap = cv2.VideoCapture(path)
        if not self._cap.isOpened():
            raise ValueError(f"无法打开视频: {path}")

        self._duration = self._cap.get(cv2.CAP_PROP_FRAME_COUNT) / self._fps
        self._fps = self._cap.get(cv2.CAP_PROP_FPS)
        self._duration = self._cap.get(cv2.CAP_PROP_FRAME_COUNT) / self._fps
        total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._seek_slider.setMaximum(total_frames)

    def duration(self) -> float:
        return self._duration

    def current_time(self) -> float:
        if self._cap is None:
            return 0.0
        return self._cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

    def seek(self, time_sec: float) -> None:
        if self._cap is None:
            return
        frame = int(time_sec * self._fps)
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
        self._seek_slider.setValue(frame)
        self._show_frame()

    def toggle_play(self) -> None:
        if self._playing:
            self._stop()
        else:
            self._start()

    def _start(self) -> None:
        self._playing = True
        self._play_btn.setText("⏸")
        interval = max(1, int(1000 / self._fps))
        self._timer.start(interval)

    def _stop(self) -> None:
        self._playing = False
        self._play_btn.setText("▶")
        self._timer.stop()

    def _on_timer(self) -> None:
        self._show_frame()

    def _show_frame(self) -> None:
        if self._cap is None:
            return
        ret, frame = self._cap.read()
        if not ret:
            self._stop()
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        qimg = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
        self._label.setPixmap(QPixmap.fromImage(qimg).scaled(
            self._label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        current_frame = int(self._cap.get(cv2.CAP_PROP_POS_FRAMES))
        self._seek_slider.setValue(current_frame)

    def _on_seek(self, value: int) -> None:
        if self._cap is None:
            return
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, value)
        self._show_frame()

    def closeEvent(self, event) -> None:
        self._stop()
        if self._cap is not None:
            self._cap.release()
        super().closeEvent(event)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/ui/test_video_preview.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/ui/video_preview.py tests/ui/test_video_preview.py
git commit -m "实现视频预览组件"
```

---

### Task 2: 波形图组件

**Files:**
- Create: `srt_maker/ui/waveform_view.py`
- Create: `tests/ui/test_waveform_view.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/ui/test_waveform_view.py
import pytest
from PySide6.QtWidgets import QApplication
from srt_maker.ui.waveform_view import WaveformView

@pytest.mark.qt_no_exception_capture
def test_waveform_creation(qtbot):
    widget = WaveformView()
    qtbot.add_widget(widget)
    assert widget is not None

@pytest.mark.qt_no_exception_capture
def test_waveform_load_audio(qtbot, tmp_path):
    from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper
    audio_path = str(tmp_path / "test.wav")
    FFmpegWrapper().create_test_video(str(tmp_path / "test.mp4"), duration=2.0)
    FFmpegWrapper().extract_audio(str(tmp_path / "test.mp4"), audio_path)

    widget = WaveformView()
    qtbot.add_widget(widget)
    widget.load_audio(audio_path)
    assert widget._audio_data is not None
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/ui/test_waveform_view.py -v
```

- [ ] **Step 3: 实现 waveform_view.py**

```python
# srt_maker/ui/waveform_view.py
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import wave

class WaveformView(QWidget):
    """音频波形图组件 — 使用 PyQtGraph"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._audio_data = None
        self._sample_rate = 16000

        self._plot = pg.PlotWidget(background="w", axisItems={"bottom": pg.AxisItem("bottom")})
        self._plot.showGrid(x=True, y=True, alpha=0.3)
        self._plot.setLabel("bottom", "时间 (秒)")
        self._plot.setYRange(-1.1, 1.1)

        self._subtitle_regions = []

    def load_audio(self, audio_path: str) -> None:
        """加载 WAV 音频并绘制波形"""
        with wave.open(audio_path, "rb") as wf:
            self._sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        self._audio_data = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
        self._audio_data = self._audio_data / 32768.0

        # 下采样以加速渲染
        max_points = 5000
        step = 1
        if len(self._audio_data) > max_points:
            step = len(self._audio_data) // max_points
            self._audio_data = self._audio_data[::step]

        time_axis = np.arange(len(self._audio_data)) * step / self._sample_rate

        self._plot.clear()
        self._plot.plot(time_axis, self._audio_data, pen=pg.mkPen("b", width=1))

    def highlight_subtitle(self, start: float, end: float, color: tuple = (0, 120, 215, 80)):
        """高亮字幕区间"""
        region = pg.LinearRegionItem([start, end], brush=pg.mkBrush(color), movable=False)
        self._plot.addItem(region)
        self._subtitle_regions.append(region)

    def clear_highlights(self):
        for region in self._subtitle_regions:
            self._plot.removeItem(region)
        self._subtitle_regions.clear()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/ui/test_waveform_view.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/ui/waveform_view.py tests/ui/test_waveform_view.py
git commit -m "实现波形图组件"
```

---

### Task 3: 字幕编辑器（表格）

**Files:**
- Create: `srt_maker/ui/subtitle_editor.py`
- Create: `tests/ui/test_subtitle_editor.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/ui/test_subtitle_editor.py
import pytest
from PySide6.QtWidgets import QApplication
from srt_maker.ui.subtitle_editor import SubtitleEditor
from srt_maker.core.subtitle_model import SubtitleEntry
from srt_maker.core.subtitle_list import SubtitleList

@pytest.mark.qt_no_exception_capture
def test_subtitle_editor_creation(qtbot):
    widget = SubtitleEditor()
    qtbot.add_widget(widget)
    assert widget is not None

@pytest.mark.qt_no_exception_capture
def test_subtitle_editor_load_data(qtbot):
    widget = SubtitleEditor()
    qtbot.add_widget(widget)
    subtitles = SubtitleList()
    subtitles.entries.append(SubtitleEntry(1.0, 4.0, "第一条"))
    subtitles.entries.append(SubtitleEntry(5.0, 8.0, "第二条"))
    widget.load_subtitles(subtitles)
    assert widget.row_count() == 2
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/ui/test_subtitle_editor.py -v
```

- [ ] **Step 3: 实现 subtitle_editor.py**

```python
# srt_maker/ui/subtitle_editor.py
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt, Signal
from srt_maker.core.subtitle_list import SubtitleList
from srt_maker.core.subtitle_model import SubtitleEntry
from srt_maker.core.timecode import seconds_to_srt

class SubtitleEditor(QTableWidget):
    """字幕编辑器 — 表格形式"""

    selection_changed = Signal(int)  # 选中行变化
    double_clicked = Signal(int)     # 双击行

    def __init__(self, parent=None):
        super().__init__(0, 4, parent)
        self.setHorizontalHeaderLabels(["#", "开始时间", "结束时间", "文本"])
        self._subtitles: SubtitleList | None = None

        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.setColumnWidth(0, 40)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.setColumnWidth(1, 140)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.setColumnWidth(2, 140)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.DoubleClicked)
        self.setSelectionMode(QTableWidget.SingleSelection)

        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.cellDoubleClicked.connect(self._on_double_clicked)

    def load_subtitles(self, subtitles: SubtitleList) -> None:
        self._subtitles = subtitles
        self.setRowCount(len(subtitles.entries))
        for i, entry in enumerate(subtitles.entries):
            self._set_row(i, entry)

    def row_count(self) -> int:
        return self.rowCount()

    def _set_row(self, row: int, entry: SubtitleEntry) -> None:
        self.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.setItem(row, 1, QTableWidgetItem(seconds_to_srt(entry.start_time)))
        self.setItem(row, 2, QTableWidgetItem(seconds_to_srt(entry.end_time)))
        self.setItem(row, 3, QTableWidgetItem(entry.text))

    def _on_selection_changed(self):
        selected = self.selectedItems()
        if selected:
            row = selected[0].row()
            self.selection_changed.emit(row)

    def _on_double_clicked(self, row: int, col: int):
        self.double_clicked.emit(row)

    def current_row(self) -> int:
        selected = self.selectedItems()
        if selected:
            return selected[0].row()
        return -1

    def get_subtitles(self) -> SubtitleList:
        """从表格读取字幕数据"""
        from srt_maker.core.timecode import srt_to_seconds
        subtitles = SubtitleList()
        for row in range(self.rowCount()):
            start_text = self.item(row, 1).text() if self.item(row, 1) else ""
            end_text = self.item(row, 2).text() if self.item(row, 2) else ""
            text = self.item(row, 3).text() if self.item(row, 3) else ""
            start = srt_to_seconds(start_text) if start_text else 0.0
            end = srt_to_seconds(end_text) if end_text else 0.0
            subtitles.entries.append(SubtitleEntry(start, end, text))
        return subtitles
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/ui/test_subtitle_editor.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/ui/subtitle_editor.py tests/ui/test_subtitle_editor.py
git commit -m "实现字幕编辑器组件"
```

---

### Task 4: 字幕样式面板

**Files:**
- Create: `srt_maker/ui/style_panel.py`
- Create: `tests/ui/test_style_panel.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/ui/test_style_panel.py
import pytest
from PySide6.QtWidgets import QApplication
from srt_maker.ui.style_panel import StylePanel

@pytest.mark.qt_no_exception_capture
def test_style_panel_creation(qtbot):
    widget = StylePanel()
    qtbot.add_widget(widget)
    assert widget is not None

@pytest.mark.qt_no_exception_capture
def test_style_panel_get_style(qtbot):
    widget = StylePanel()
    qtbot.add_widget(widget)
    style = widget.get_style()
    assert "font_name" in style
    assert "font_size" in style
    assert "color" in style
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/ui/test_style_panel.py -v
```

- [ ] **Step 3: 实现 style_panel.py**

```python
# srt_maker/ui/style_panel.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QSpinBox,
    QFrame, QGridLayout,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

class StylePanel(QWidget):
    """字幕样式面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel("字幕样式")
        label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(label)

        grid = QGridLayout()

        grid.addWidget(QLabel("字体:"), 0, 0)
        self._font_edit = QLineEdit("微软雅黑")
        grid.addWidget(self._font_edit, 0, 1)

        grid.addWidget(QLabel("大小:"), 1, 0)
        self._size_spin = QSpinBox()
        self._size_spin.setRange(8, 72)
        self._size_spin.setValue(24)
        grid.addWidget(self._size_spin, 1, 1)

        grid.addWidget(QLabel("颜色:"), 2, 0)
        self._color_frame = QFrame()
        self._color_frame.setFixedSize(40, 20)
        self._color_frame.setStyleSheet("background-color: white; border: 1px solid #999;")
        self._color = QColor(Qt.white)
        grid.addWidget(self._color_frame, 2, 1)

        layout.addLayout(grid)
        layout.addStretch()

    def get_style(self) -> dict:
        return {
            "font_name": self._font_edit.text(),
            "font_size": self._size_spin.value(),
            "color": self._color,
        }

    def set_style(self, style: dict):
        if "font_name" in style:
            self._font_edit.setText(style["font_name"])
        if "font_size" in style:
            self._size_spin.setValue(style["font_size"])
        if "color" in style:
            self._color = style["color"]
            self._color_frame.setStyleSheet(f"background-color: {style['color'].name()}; border: 1px solid #999;")
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/ui/test_style_panel.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/ui/style_panel.py tests/ui/test_style_panel.py
git commit -m "实现字幕样式面板"
```

---

### Task 5: 主窗口

**Files:**
- Create: `srt_maker/ui/main_window.py`
- Create: `tests/ui/test_main_window.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/ui/test_main_window.py
import pytest
from PySide6.QtWidgets import QApplication
from srt_maker.ui.main_window import MainWindow

@pytest.mark.qt_no_exception_capture
def test_main_window_creation(qtbot):
    window = MainWindow()
    qtbot.add_widget(window)
    assert window is not None
    assert window.windowTitle() == "SRT Maker"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/ui/test_main_window.py -v
```

- [ ] **Step 3: 实现 main_window.py**

```python
# srt_maker/ui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QMenuBar, QToolBar, QFileDialog,
    QMessageBox, QStatusBar, QSplitter, QGroupBox,
    QVBoxLayout, QHBoxLayout, QWidget, QComboBox,
    QLabel, QPushButton, QProgressBar,
)
from PySide6.QtCore import Qt, QThread
from srt_maker.ui.video_preview import VideoPreview
from srt_maker.ui.waveform_view import WaveformView
from srt_maker.ui.subtitle_editor import SubtitleEditor
from srt_maker.ui.style_panel import StylePanel
from srt_maker.core.subtitle_list import SubtitleList
from srt_maker.io.srt_parser import write_srt

class MainWindow(QMainWindow):
    """主窗口 — 上下布局"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SRT Maker")
        self.resize(1200, 800)
        self._video_path = None
        self._subtitles = SubtitleList()
        self._setup_ui()

    def _setup_ui(self):
        # 菜单栏
        self._setup_menu()

        # 工具栏
        self._setup_toolbar()

        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 上方：视频预览 + 样式面板
        top_splitter = QSplitter(Qt.Horizontal)

        self.video_preview = VideoPreview()
        top_splitter.addWidget(self.video_preview)

        self.style_panel = StylePanel()
        self.style_panel.setFixedWidth(160)
        top_splitter.addWidget(self.style_panel)

        layout.addWidget(top_splitter, 1)

        # 波形图
        self.waveform = WaveformView()
        waveform_container = QGroupBox("音频波形")
        wf_layout = QVBoxLayout(waveform_container)
        wf_layout.addWidget(self.waveform)
        waveform_container.setFixedHeight(150)
        layout.addWidget(waveform_container)

        # 字幕编辑器
        self.subtitle_editor = SubtitleEditor()
        layout.addWidget(self.subtitle_editor, 1)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # 状态栏
        self.statusBar().showMessage("就绪")

        # 信号连接
        self.subtitle_editor.selection_changed.connect(self._on_subtitle_selected)

    def _setup_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("文件")
        open_action = file_menu.addAction("打开视频")
        open_action.triggered.connect(self._open_video)

        import_action = file_menu.addAction("导入字幕")
        import_action.triggered.connect(self._import_subtitles)

        export_action = file_menu.addAction("导出 SRT")
        export_action.triggered.connect(self._export_srt)

        edit_menu = menu_bar.addMenu("编辑")
        undo_action = edit_menu.addAction("撤销")
        undo_action.triggered.connect(self._subtitles.undo)
        redo_action = edit_menu.addAction("重做")
        redo_action.triggered.connect(self._subtitles.redo)

        recognize_menu = menu_bar.addMenu("识别")
        start_action = recognize_menu.addAction("开始识别")
        start_action.triggered.connect(self._start_recognition)

        burn_menu = menu_bar.addMenu("烧录")
        burn_action = burn_menu.addAction("烧录字幕")
        burn_action.triggered.connect(self._burn_subtitles)

        help_menu = menu_bar.addMenu("帮助")
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self._show_about)

    def _setup_toolbar(self):
        toolbar = QToolBar("主工具栏")

        self._recognizer_combo = QComboBox()
        self._recognizer_combo.addItems(["Whisper", "qwen3-asr", "云端 API"])
        toolbar.addWidget(QLabel("识别方式:"))
        toolbar.addWidget(self._recognizer_combo)

        self._language_combo = QComboBox()
        self._language_combo.addItems(["中文", "英文", "自动"])
        toolbar.addWidget(QLabel("语言:"))
        toolbar.addWidget(self._language_combo)

        toolbar.addSeparator()

        burn_btn = QPushButton("烧录字幕")
        burn_btn.clicked.connect(self._burn_subtitles)
        toolbar.addWidget(burn_btn)

        self.addToolBar(toolbar)

    def _open_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开视频", "", "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm)"
        )
        if path:
            self._video_path = path
            self.video_preview.load_video(path)
            self.statusBar().showMessage(f"已加载: {path}")

    def _import_subtitles(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入字幕", "", "字幕文件 (*.srt *.ass)"
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if path.endswith(".srt"):
                from srt_maker.io.srt_parser import parse_srt
                self._subtitles = SubtitleList()
                self._subtitles.entries = parse_srt(content)
            elif path.endswith(".ass"):
                from srt_maker.io.ass_parser import parse_ass
                self._subtitles = SubtitleList()
                self._subtitles.entries = parse_ass(content)
            self.subtitle_editor.load_subtitles(self._subtitles)
            self.statusBar().showMessage(f"已导入: {path}")

    def _export_srt(self):
        if not self._subtitles.entries:
            QMessageBox.information(self, "提示", "没有可导出的字幕")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 SRT", "", "SRT 文件 (*.srt)"
        )
        if path:
            content = write_srt(self._subtitles.entries)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.statusBar().showMessage(f"已导出: {path}")

    def _start_recognition(self):
        if not self._video_path:
            QMessageBox.warning(self, "提示", "请先打开视频文件")
            return
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.statusBar().showMessage("识别中...")
        # TODO: 异步执行识别任务

    def _burn_subtitles(self):
        if not self._video_path:
            QMessageBox.warning(self, "提示", "请先打开视频文件")
            return
        if not self._subtitles.entries:
            QMessageBox.warning(self, "提示", "请先加载字幕")
            return
        # TODO: 执行烧录任务

    def _on_subtitle_selected(self, row: int):
        if row >= 0 and row < len(self._subtitles.entries):
            entry = self._subtitles.entries[row]
            self.video_preview.seek(entry.start_time)

    def _show_about(self):
        QMessageBox.about(self, "关于", "SRT Maker\n视频字幕生成与烧录工具")
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/ui/test_main_window.py -v
```

- [ ] **Step 5: Commit**

```bash
git add srt_maker/ui/main_window.py tests/ui/test_main_window.py
git commit -m "实现主窗口"
```

---

### Task 6: 入口点

**Files:**
- Create: `srt_maker/main.py`

- [ ] **Step 1: 创建 main.py**

```python
# srt_maker/main.py
import sys
from PySide6.QtWidgets import QApplication
from srt_maker.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证启动**

```bash
python -m srt_maker.main
```

期望：应用窗口正常显示

- [ ] **Step 3: Commit**

```bash
git add srt_maker/main.py
git commit -m "实现应用入口点"
```

---

### Task 7: 运行全部 UI 测试

**Files:** 无新文件

- [ ] **Step 1: 运行所有测试**

```bash
python -m pytest tests/ -v --tb=short
```

期望：全部 PASS

- [ ] **Step 2: Commit**

```bash
git commit -m "UI 层全部测试通过" --allow-empty
```

---

## 验证

完成所有任务后：

1. 运行 `python -m srt_maker.main` 启动应用
2. 验证主窗口布局正确（视频预览、波形图、字幕编辑器、样式面板）
3. 验证菜单和工具栏功能正常
4. 验证字幕导入/导出功能
5. 运行 `python -m pytest tests/ -v` 确认所有测试通过
