from srt_maker.core.timecode import seconds_to_srt, srt_to_seconds

def test_seconds_to_srt_zero():
    assert seconds_to_srt(0) == "00:00:00,000"

def test_seconds_to_srt_basic():
    assert seconds_to_srt(1234.567) == "00:20:34,567"

def test_srt_to_seconds():
    assert srt_to_seconds("00:20:34,567") == 1234.567

def test_roundtrip():
    original = 3600.999
    assert srt_to_seconds(seconds_to_srt(original)) == original
