from PySide6.QtWidgets import (
    QMainWindow, QMenuBar, QToolBar, QFileDialog,
    QMessageBox, QStatusBar, QSplitter, QGroupBox,
    QVBoxLayout, QHBoxLayout, QWidget, QComboBox,
    QLabel, QPushButton, QProgressBar,
)
from PySide6.QtCore import Qt
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
