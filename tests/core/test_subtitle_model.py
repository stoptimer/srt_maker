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
