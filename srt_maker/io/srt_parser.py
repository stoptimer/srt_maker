import re

from srt_maker.core.subtitle_model import SubtitleEntry
from srt_maker.core.timecode import srt_to_seconds

SRT_BLOCK_RE = re.compile(
    r"(\d+)\s*\n"
    r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*\n"
    r"([\s\S]*?)(?=\n\n|\n\d+\s*\n|$)"
)


def parse_srt(text: str) -> list[SubtitleEntry]:
    """解析 SRT 格式文本为字幕条目列表"""
    entries = []
    for match in SRT_BLOCK_RE.finditer(text):
        start = srt_to_seconds(match.group(2))
        end = srt_to_seconds(match.group(3))
        subtitle_text = match.group(4).strip()
        entries.append(SubtitleEntry(start, end, subtitle_text))
    return entries


def write_srt(entries: list[SubtitleEntry]) -> str:
    """将字幕条目列表写入 SRT 格式文本"""
    blocks = []
    for i, entry in enumerate(entries, 1):
        blocks.append(entry.to_srt(i))
    return "\n\n".join(blocks) + "\n" if blocks else ""
