from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import wave


class WaveformView(QWidget):
    """音频波形图组件 — 使用 PyQtGraph 绘制音频波形"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._audio_data = None
        self._sample_rate = 16000
        self._subtitle_regions = []

        self._plot = pg.PlotWidget(background="w", axisItems={"bottom": pg.AxisItem("bottom")})
        self._plot.showGrid(x=True, y=True, alpha=0.3)
        self._plot.setLabel("bottom", "时间 (秒)")
        self._plot.setYRange(-1.1, 1.1)

    def load_audio(self, audio_path: str) -> None:
        """加载 WAV 音频并绘制波形

        Args:
            audio_path: WAV 音频文件路径（16kHz 单声道 PCM 16-bit）
        """
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
        """高亮字幕区间

        Args:
            start: 开始时间（秒）
            end: 结束时间（秒）
            color: 高亮区域颜色 (R, G, B, A)
        """
        region = pg.LinearRegionItem([start, end], brush=pg.mkBrush(color), movable=False)
        self._plot.addItem(region)
        self._subtitle_regions.append(region)

    def clear_highlights(self):
        """清除所有字幕高亮区域"""
        for region in self._subtitle_regions:
            self._plot.removeItem(region)
        self._subtitle_regions.clear()
