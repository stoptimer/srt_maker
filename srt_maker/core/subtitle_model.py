from dataclasses import dataclass

from srt_maker.core.timecode import seconds_to_srt


@dataclass
class SubtitleEntry:
    """字幕条目数据模型"""
    start_time: float
    end_time: float
    text: str

    def to_srt(self, index: int) -> str:
        """将字幕条目转换为SRT格式字符串"""
        start = seconds_to_srt(self.start_time)
        end = seconds_to_srt(self.end_time)
        return f"{index}\n{start} --> {end}\n{self.text}"
