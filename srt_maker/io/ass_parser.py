import re

from srt_maker.core.subtitle_model import SubtitleEntry

ASS_TIME_RE = re.compile(r"(\d+):(\d{2}):(\d{2})[.,](\d{2})")


def _ass_time_to_seconds(time_str: str) -> float:
    """ASS 时间格式转秒数"""
    m = ASS_TIME_RE.match(time_str)
    if not m:
        raise ValueError(f"无效的 ASS 时间格式: {time_str}")
    hours, minutes, secs, cs = m.groups()
    return int(hours) * 3600 + int(minutes) * 60 + int(secs) + int(cs) / 100


def parse_ass(text: str) -> list[SubtitleEntry]:
    """解析 ASS 格式文本为字幕条目列表"""
    entries = []
    in_events = False
    for line in text.splitlines():
        if line.strip() == "[Events]":
            in_events = True
            continue
        if in_events and line.startswith("Dialogue:"):
            parts = line.split(",", 10)
            if len(parts) < 10:
                continue
            start = _ass_time_to_seconds(parts[1])
            end = _ass_time_to_seconds(parts[2])
            subtitle_text = parts[9] if len(parts) > 9 else ""
            # 移除 ASS 标签（如 {\i1}...{\i0}）
            subtitle_text = re.sub(r"\{[^}]*\}", "", subtitle_text).strip()
            entries.append(SubtitleEntry(start, end, subtitle_text))
    return entries
