from srt_maker.io.ass_parser import parse_ass


def test_parse_ass_dialogue():
    ass = "[Script Info]\nTitle=Test\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,第一条字幕"
    entries = parse_ass(ass)
    assert len(entries) == 1
    assert entries[0].text == "第一条字幕"
    assert entries[0].start_time == 1.0
    assert entries[0].end_time == 4.0


def test_parse_ass_empty():
    entries = parse_ass("")
    assert len(entries) == 0


def test_parse_ass_multiple():
    ass = "[Script Info]\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,A\nDialogue: 0,0:00:04.00,0:00:06.00,Default,,0,0,0,,B"
    entries = parse_ass(ass)
    assert len(entries) == 2
    assert entries[0].text == "A"
    assert entries[1].text == "B"
