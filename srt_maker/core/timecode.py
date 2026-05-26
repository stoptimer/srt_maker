def seconds_to_srt(seconds: float) -> str:
    """秒数转 SRT 时间码格式: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds % 1) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def srt_to_seconds(srt_time: str) -> float:
    """SRT 时间码转秒数"""
    hours, minutes, rest = srt_time.split(":")
    secs, millis = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(secs) + int(millis) / 1000
