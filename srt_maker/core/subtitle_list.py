from __future__ import annotations

from typing import Callable

from srt_maker.core.subtitle_model import SubtitleEntry


class _UndoStack:
    """支持撤销/重做的命令栈"""

    def __init__(self) -> None:
        self._undo: list[tuple[Callable[[], None], Callable[[], None]]] = []
        self._redo: list[tuple[Callable[[], None], Callable[[], None]]] = []

    def execute(self, action: Callable[[], None], undo_action: Callable[[], None]) -> None:
        """执行一个操作并记录其撤销动作"""
        action()
        self._undo.append((action, undo_action))
        self._redo.clear()

    def undo(self) -> None:
        """撤销上一次操作"""
        if not self._undo:
            return
        action, undo_action = self._undo.pop()
        undo_action()
        self._redo.append((action, undo_action))

    def redo(self) -> None:
        """重做上一次撤销的操作"""
        if not self._redo:
            return
        action, undo_action = self._redo.pop()
        action()
        self._undo.append((action, undo_action))


class SubtitleList:
    """字幕列表，支持增删改、拆分、合并以及撤销/重做"""

    def __init__(self) -> None:
        self.entries: list[SubtitleEntry] = []
        self._history = _UndoStack()

    # ---- 基本操作 ----

    def replace(self, entries: list[SubtitleEntry]) -> None:
        """替换整个字幕列表（用于导入操作，支持撤销）"""
        old_entries = list(self.entries)
        new_entries = list(entries)
        self._history.execute(
            action=lambda: (
                self.entries.clear(),
                self.entries.extend(new_entries),
            ),
            undo_action=lambda: (
                self.entries.clear(),
                self.entries.extend(old_entries),
            ),
        )

    def add(self, entry: SubtitleEntry) -> None:
        """添加字幕条目"""
        self._history.execute(
            action=lambda: self.entries.append(entry),
            undo_action=lambda: self.entries.pop(),
        )

    def remove(self, index: int) -> None:
        """移除指定索引的字幕条目"""
        entry = self.entries[index]  # 在移除前保存，供撤销使用
        self._history.execute(
            action=lambda: self.entries.pop(index),
            undo_action=lambda: self.entries.insert(index, entry),
        )

    def modify(self, index: int, entry: SubtitleEntry) -> None:
        """修改指定索引的字幕条目"""
        old = self.entries[index]
        self._history.execute(
            action=lambda: self.entries.__setitem__(index, entry),
            undo_action=lambda: self.entries.__setitem__(index, old),
        )

    # ---- 拆分与合并 ----

    def split(self, index: int, at_time: float) -> None:
        """在指定时间将字幕条目拆分为两条"""
        entry = self.entries[index]
        before = SubtitleEntry(entry.start_time, at_time, entry.text)
        after = SubtitleEntry(at_time, entry.end_time, entry.text)
        self._history.execute(
            action=lambda: (
                self.entries.__setitem__(index, before),
                self.entries.insert(index + 1, after),
            ),
            undo_action=lambda: (
                self.entries.pop(index + 1),
                self.entries.__setitem__(index, entry),
            ),
        )

    def merge(self, index_a: int, index_b: int) -> None:
        """合并两条相邻字幕条目"""
        a = self.entries[index_a]
        b = self.entries[index_b]
        merged = SubtitleEntry(a.start_time, b.end_time, a.text + b.text)
        self._history.execute(
            action=lambda: (
                self.entries.__setitem__(index_a, merged),
                self.entries.pop(index_b),
            ),
            undo_action=lambda: (
                self.entries.__setitem__(index_a, a),
                self.entries.insert(index_b, b),
            ),
        )

    # ---- 撤销/重做 ----

    def can_undo(self) -> bool:
        """返回是否可以撤销"""
        return len(self._history._undo) > 0

    def can_redo(self) -> bool:
        """返回是否可以重做"""
        return len(self._history._redo) > 0

    def undo(self) -> None:
        """撤销上一次操作"""
        self._history.undo()

    def redo(self) -> None:
        """重做上一次撤销的操作"""
        self._history.redo()
