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
