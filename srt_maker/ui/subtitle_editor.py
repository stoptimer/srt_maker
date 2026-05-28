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
        """加载字幕数据到表格"""
        self._subtitles = subtitles
        self.setRowCount(len(subtitles.entries))
        for i, entry in enumerate(subtitles.entries):
            self._set_row(i, entry)

    def row_count(self) -> int:
        """返回当前表格行数"""
        return self.rowCount()

    def _set_row(self, row: int, entry: SubtitleEntry) -> None:
        """设置表格行的内容"""
        self.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.setItem(row, 1, QTableWidgetItem(seconds_to_srt(entry.start_time)))
        self.setItem(row, 2, QTableWidgetItem(seconds_to_srt(entry.end_time)))
        self.setItem(row, 3, QTableWidgetItem(entry.text))

    def _on_selection_changed(self):
        """选中行变化时触发信号"""
        selected = self.selectedItems()
        if selected:
            row = selected[0].row()
            self.selection_changed.emit(row)

    def _on_double_clicked(self, row: int, col: int):
        """双击单元格时触发信号"""
        self.double_clicked.emit(row)

    def current_row(self) -> int:
        """返回当前选中行索引，未选中时返回 -1"""
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
            try:
                start = srt_to_seconds(start_text) if start_text else 0.0
                end = srt_to_seconds(end_text) if end_text else 0.0
            except ValueError:
                start = 0.0
                end = 0.0
            subtitles.entries.append(SubtitleEntry(start, end, text))
        return subtitles
