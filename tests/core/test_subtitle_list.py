from srt_maker.core.subtitle_model import SubtitleEntry
from srt_maker.core.subtitle_list import SubtitleList


# ========== 基本操作 ==========

def test_add_entry():
    sl = SubtitleList()
    sl.add(SubtitleEntry(1.0, 2.0, "第一条"))
    assert len(sl.entries) == 1
    assert sl.entries[0].text == "第一条"

def test_add_multiple_entries():
    sl = SubtitleList()
    sl.add(SubtitleEntry(1.0, 2.0, "第一条"))
    sl.add(SubtitleEntry(3.0, 4.0, "第二条"))
    assert len(sl.entries) == 2

def test_remove_entry():
    sl = SubtitleList()
    sl.add(SubtitleEntry(1.0, 2.0, "第一条"))
    sl.remove(0)
    assert len(sl.entries) == 0

def test_remove_middle_entry():
    sl = SubtitleList()
    sl.add(SubtitleEntry(1.0, 2.0, "A"))
    sl.add(SubtitleEntry(2.0, 3.0, "B"))
    sl.add(SubtitleEntry(3.0, 4.0, "C"))
    sl.remove(1)
    assert len(sl.entries) == 2
    assert sl.entries[0].text == "A"
    assert sl.entries[1].text == "C"

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
    assert sl.entries[0].text == "AB"
    assert sl.entries[1].text == "AB"

def test_merge_entries():
    sl = SubtitleList()
    sl.add(SubtitleEntry(0.0, 2.0, "A"))
    sl.add(SubtitleEntry(2.0, 4.0, "B"))
    sl.merge(0, 1)
    assert len(sl.entries) == 1
    assert sl.entries[0].text == "AB"
    assert sl.entries[0].start_time == 0.0
    assert sl.entries[0].end_time == 4.0

# ========== 撤销/重做 ==========

def test_undo_redo_add():
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
    assert sl.entries[0].text == "第一条"

def test_undo_redo_modify():
    sl = SubtitleList()
    sl.add(SubtitleEntry(1.0, 2.0, "第一条"))
    sl.modify(0, SubtitleEntry(1.0, 2.0, "修改后"))
    assert sl.entries[0].text == "修改后"
    sl.undo()
    assert sl.entries[0].text == "第一条"
    sl.redo()
    assert sl.entries[0].text == "修改后"

def test_undo_redo_split():
    sl = SubtitleList()
    sl.add(SubtitleEntry(0.0, 4.0, "AB"))
    sl.split(0, 2.0)
    assert len(sl.entries) == 2
    sl.undo()
    assert len(sl.entries) == 1
    assert sl.entries[0].text == "AB"
    sl.redo()
    assert len(sl.entries) == 2

def test_undo_redo_merge():
    sl = SubtitleList()
    sl.add(SubtitleEntry(0.0, 2.0, "A"))
    sl.add(SubtitleEntry(2.0, 4.0, "B"))
    sl.merge(0, 1)
    assert len(sl.entries) == 1
    sl.undo()
    assert len(sl.entries) == 2
    assert sl.entries[0].text == "A"
    assert sl.entries[1].text == "B"
    sl.redo()
    assert len(sl.entries) == 1

def test_multiple_undo():
    sl = SubtitleList()
    sl.add(SubtitleEntry(1.0, 2.0, "A"))
    sl.add(SubtitleEntry(2.0, 3.0, "B"))
    sl.add(SubtitleEntry(3.0, 4.0, "C"))
    sl.undo()
    assert len(sl.entries) == 2
    sl.undo()
    assert len(sl.entries) == 1
    sl.undo()
    assert len(sl.entries) == 0

def test_multiple_redo():
    sl = SubtitleList()
    sl.add(SubtitleEntry(1.0, 2.0, "A"))
    sl.add(SubtitleEntry(2.0, 3.0, "B"))
    sl.add(SubtitleEntry(3.0, 4.0, "C"))
    sl.undo()
    sl.undo()
    sl.undo()
    assert len(sl.entries) == 0
    sl.redo()
    assert len(sl.entries) == 1
    sl.redo()
    assert len(sl.entries) == 2
    sl.redo()
    assert len(sl.entries) == 3

def test_new_action_clears_redo():
    """新操作后，重做栈应被清空"""
    sl = SubtitleList()
    sl.add(SubtitleEntry(1.0, 2.0, "A"))
    sl.add(SubtitleEntry(2.0, 3.0, "B"))
    sl.undo()
    assert len(sl.entries) == 1
    # 执行新操作，重做栈应被清空
    sl.add(SubtitleEntry(3.0, 4.0, "C"))
    sl.redo()
    # redo 不应生效，因为重做栈已被清空
    assert len(sl.entries) == 2

def test_undo_on_empty():
    """空操作时撤销不应报错"""
    sl = SubtitleList()
    sl.undo()  # 不应抛出异常
    assert len(sl.entries) == 0

def test_redo_on_empty():
    """空操作时重做不应报错"""
    sl = SubtitleList()
    sl.redo()  # 不应抛出异常
    assert len(sl.entries) == 0

def test_replace_with_entries():
    """测试 replace 用 entries 列表替换字幕"""
    sl = SubtitleList()
    sl.add(SubtitleEntry(1.0, 2.0, "旧条目"))

    new_sl = SubtitleList()
    new_sl.add(SubtitleEntry(3.0, 4.0, "新条目"))

    # replace 接收 list[SubtitleEntry]，应传入 .entries
    sl.replace(new_sl.entries)
    assert len(sl.entries) == 1
    assert sl.entries[0].text == "新条目"

    # 撤销后恢复旧条目
    sl.undo()
    assert len(sl.entries) == 1
    assert sl.entries[0].text == "旧条目"
