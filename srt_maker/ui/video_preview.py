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
        self._play_btn = QPushButton("播放")
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

        self._fps = self._cap.get(cv2.CAP_PROP_FPS)
        self._duration = self._cap.get(cv2.CAP_PROP_FRAME_COUNT) / self._fps
        total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._seek_slider.setMaximum(total_frames)

    def duration(self) -> float:
        """返回视频时长（秒）"""
        return self._duration

    def current_time(self) -> float:
        """返回当前播放时间（秒）"""
        if self._cap is None:
            return 0.0
        return self._cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

    def seek(self, time_sec: float) -> None:
        """跳转到指定时间（秒）"""
        if self._cap is None:
            return
        frame = int(time_sec * self._fps)
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
        self._seek_slider.setValue(frame)
        self._show_frame()

    def toggle_play(self) -> None:
        """切换播放/暂停"""
        if self._playing:
            self._stop()
        else:
            self._start()

    def _start(self) -> None:
        """开始播放"""
        self._playing = True
        self._play_btn.setText("暂停")
        interval = max(1, int(1000 / self._fps))
        self._timer.start(interval)

    def _stop(self) -> None:
        """停止播放"""
        self._playing = False
        self._play_btn.setText("播放")
        self._timer.stop()

    def _on_timer(self) -> None:
        """定时器回调 — 显示下一帧"""
        self._show_frame()

    def _show_frame(self) -> None:
        """显示当前帧"""
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
        """拖动进度条回调"""
        if self._cap is None:
            return
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, value)
        self._show_frame()

    def closeEvent(self, event) -> None:
        """关闭事件 — 释放资源"""
        self._stop()
        if self._cap is not None:
            self._cap.release()
        super().closeEvent(event)
