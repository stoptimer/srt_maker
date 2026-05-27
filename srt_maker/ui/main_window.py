from PySide6.QtWidgets import (
    QMainWindow, QMenuBar, QToolBar, QFileDialog,
    QMessageBox, QStatusBar, QSplitter, QGroupBox,
    QVBoxLayout, QHBoxLayout, QWidget, QComboBox,
    QLabel, QPushButton, QProgressBar,
)
from PySide6.QtCore import Qt, QThread
from srt_maker.ui.video_preview import VideoPreview
from srt_maker.ui.recognition_worker import RecognitionWorker
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
        self._worker: RecognitionWorker | None = None
        self._worker_thread: QThread | None = None
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
        self._undo_action = edit_menu.addAction("撤销")
        self._undo_action.triggered.connect(self._do_undo)
        self._undo_action.setEnabled(False)
        self._redo_action = edit_menu.addAction("重做")
        self._redo_action.triggered.connect(self._do_redo)
        self._redo_action.setEnabled(False)

        recognize_menu = menu_bar.addMenu("识别")
        self._start_recognition_action = recognize_menu.addAction("开始识别")
        self._start_recognition_action.triggered.connect(self._start_recognition)

        burn_menu = menu_bar.addMenu("烧录")
        burn_action = burn_menu.addAction("烧录字幕")
        burn_action.triggered.connect(self._burn_subtitles)

        # 设置菜单
        settings_menu = menu_bar.addMenu("设置")
        settings_action = settings_menu.addAction("设置")
        settings_action.triggered.connect(self._show_settings)

        help_menu = menu_bar.addMenu("帮助")
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self._show_about)

    def _setup_toolbar(self):
        toolbar = QToolBar("主工具栏")

        self._recognizer_combo = QComboBox()
        self._recognizer_combo.addItems(["Whisper", "qwen3-asr", "云端API"])
        toolbar.addWidget(QLabel("识别方式:"))
        toolbar.addWidget(self._recognizer_combo)

        self._model_size_combo = QComboBox()
        self._model_size_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self._model_size_combo.setCurrentText("base")
        toolbar.addWidget(QLabel("模型:"))
        toolbar.addWidget(self._model_size_combo)

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
            try:
                self.video_preview.load_video(path)
                self._video_path = path
                self.statusBar().showMessage(f"已加载: {path}")
            except ValueError as e:
                QMessageBox.critical(self, "错误", str(e))

    def _import_subtitles(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入字幕", "", "字幕文件 (*.srt *.ass)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                if path.endswith(".srt"):
                    from srt_maker.io.srt_parser import parse_srt
                    self._subtitles.replace(parse_srt(content))
                elif path.endswith(".ass"):
                    from srt_maker.io.ass_parser import parse_ass
                    self._subtitles.replace(parse_ass(content))
                self.subtitle_editor.load_subtitles(self._subtitles)
                self.statusBar().showMessage(f"已导入: {path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入字幕失败: {e}")

    def _export_srt(self):
        if not self._subtitles.entries:
            QMessageBox.information(self, "提示", "没有可导出的字幕")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 SRT", "", "SRT 文件 (*.srt)"
        )
        if path:
            try:
                content = write_srt(self._subtitles.entries)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.statusBar().showMessage(f"已导出: {path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def _start_recognition(self):
        """开始语音识别流程"""
        if not self._video_path:
            QMessageBox.warning(self, "提示", "请先打开视频文件")
            return

        # 检查 FFmpeg 是否可用
        from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper
        if not FFmpegWrapper().is_available():
            QMessageBox.critical(
                self, "错误",
                "未找到 FFmpeg，请先安装 FFmpeg 并将其添加到系统 PATH 中，\n"
                "或通过设置配置 FFmpeg 路径。"
            )
            return

        # 获取用户设置
        recognizer_type = self._recognizer_combo.currentText()
        language_map = {"中文": "zh", "英文": "en", "自动": "auto"}
        language = language_map.get(self._language_combo.currentText(), "auto")
        model_size = self._model_size_combo.currentText()

        # 创建 worker 和线程
        self._worker = RecognitionWorker()
        self._worker_thread = QThread()

        self._worker.moveToThread(self._worker_thread)

        # 连接信号
        self._worker_thread.started.connect(
            lambda: self._worker.start(
                self._video_path, recognizer_type, language, model_size
            )
        )
        self._worker.progress.connect(self._on_recognition_progress)
        self._worker.finished.connect(self._on_recognition_finished)
        self._worker.error.connect(self._on_recognition_error)

        # 启动
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self._start_recognition_action.setEnabled(False)
        self._undo_action.setEnabled(False)
        self._redo_action.setEnabled(False)
        self._worker_thread.start()

    def _on_recognition_progress(self, text: str, percentage: int):
        """更新识别进度"""
        self.progress.setValue(percentage)
        self.statusBar().showMessage(text)

    def _on_recognition_finished(self, subtitles: SubtitleList):
        """识别完成 — 加载结果"""
        self._subtitles.replace(subtitles.entries)
        self.subtitle_editor.load_subtitles(self._subtitles)

        # 加载音频波形
        if self._worker and self._worker.last_audio_path:
            self.waveform.load_audio(str(self._worker.last_audio_path))

        # 高亮所有字幕区间
        self.waveform.clear_highlights()
        for entry in subtitles.entries:
            self.waveform.highlight_subtitle(entry.start_time, entry.end_time)

        self.statusBar().showMessage(f"识别完成，共 {len(subtitles.entries)} 条字幕")
        self._cleanup_worker()

    def _on_recognition_error(self, message: str):
        """识别失败 — 显示错误"""
        QMessageBox.critical(self, "识别失败", message)
        self._cleanup_worker()

    def _cleanup_worker(self):
        """清理工作线程资源"""
        if self._worker_thread:
            self._worker_thread.quit()
            if not self._worker_thread.wait(5000):
                self._worker_thread.terminate()
                self._worker_thread.wait()
            self._worker_thread.deleteLater()
            self._worker_thread = None
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
        self.progress.setVisible(False)
        self.progress.setValue(0)
        self._start_recognition_action.setEnabled(True)
        self._undo_action.setEnabled(True)
        self._redo_action.setEnabled(True)

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
            self.waveform.clear_highlights()
            self.waveform.highlight_subtitle(entry.start_time, entry.end_time)

    def _do_undo(self):
        """执行撤销并更新菜单状态"""
        self._subtitles.undo()
        self._undo_action.setEnabled(self._subtitles.can_undo())
        self._redo_action.setEnabled(self._subtitles.can_redo())

    def _do_redo(self):
        """执行重做并更新菜单状态"""
        self._subtitles.redo()
        self._undo_action.setEnabled(self._subtitles.can_undo())
        self._redo_action.setEnabled(self._subtitles.can_redo())

    def _show_settings(self):
        """显示设置对话框"""
        from srt_maker.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()

    def _show_about(self):
        QMessageBox.about(self, "关于", "SRT Maker\n视频字幕生成与烧录工具")
