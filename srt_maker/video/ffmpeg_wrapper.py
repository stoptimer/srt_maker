import subprocess
import os
import sys
import tempfile
from pathlib import Path

from srt_maker.core.subtitle_model import SubtitleEntry

# 默认 FFmpeg 路径（可通过环境变量或构造参数覆盖）
_DEFAULT_FFMPEG_DIR = os.environ.get("FFMPEG_DIR", "")

def _bundled_ffmpeg_dir() -> str:
    """获取打包目录下的 FFmpeg 路径

    PyInstaller 打包后，_MEIPASS 指向 _internal/ 目录。
    打包目录下的 ffmpeg/ 位于 _MEIPASS 的父目录。
    开发环境下 _MEIPASS 不存在，返回空字符串。
    """
    if not hasattr(sys, "_MEIPASS"):
        return ""
    bundled = Path(sys._MEIPASS) / ".." / "ffmpeg"
    if (bundled / "ffmpeg.exe").exists():
        return str(bundled)
    return ""

def _split_long_subtitles(
    entries: list[SubtitleEntry],
    max_chars_per_line: int = 40,
) -> list[SubtitleEntry]:
    """拆分超长字幕条目，避免 libass 自动换行导致第二行被裁剪

    将超过 max_chars_per_line 字符的字幕按空格拆分为多条，
    每条平分原始时间区间，依次播放。

    如果拆分后单条时长低于 _MIN_SPLIT_DURATION 秒，则放弃拆分，
    避免产生不可读的闪烁字幕。

    Args:
        entries: 字幕条目列表
        max_chars_per_line: 单行最大字符数

    Returns:
        拆分后的字幕条目列表
    """
    _MIN_SPLIT_DURATION = 0.3  # 单条最低时长，低于此值不拆分

    result = []
    for entry in entries:
        if len(entry.text) <= max_chars_per_line:
            result.append(entry)
            continue

        # 按空格拆分
        lines = []
        remaining = entry.text
        while remaining:
            cut = min(max_chars_per_line, len(remaining))
            # 尝试在空格处断开：如果 cut 前半段有空格，优先在空格处断开
            if cut < len(remaining):
                space = remaining.rfind(" ", 0, cut)
                if space >= cut // 2:
                    cut = space
                else:
                    # 否则尝试在 cut 后找空格，允许超出 50%
                    space = remaining.find(" ", cut)
                    if space >= 0 and space <= cut * 1.5:
                        cut = space
            lines.append(remaining[:cut].strip())
            remaining = remaining[cut:].strip()

        # 每条平分原始时间区间
        duration = entry.end_time - entry.start_time
        per_duration = duration / len(lines)

        # 如果拆分后单条时长太短，放弃拆分
        if per_duration < _MIN_SPLIT_DURATION:
            result.append(entry)
            continue

        for i, line in enumerate(lines):
            start = entry.start_time + per_duration * i
            end = entry.start_time + per_duration * (i + 1)
            result.append(SubtitleEntry(start, end, line))

    return result


class FFmpegWrapper:
    """FFmpeg 命令行封装"""

    def __init__(self, ffmpeg_dir: str = ""):
        """
        初始化 FFmpeg 封装。

        Args:
            ffmpeg_dir: FFmpeg 可执行文件所在目录，默认从 FFMPEG_DIR 环境变量读取，
                        若为空则从 PATH 中查找
        """
        self._ffmpeg_dir = self._resolve_ffmpeg_dir(ffmpeg_dir)

    @staticmethod
    def _resolve_ffmpeg_dir(explicit_dir: str) -> str:
        """解析 FFmpeg 目录，按优先级查找

        优先级：显式参数 > 打包目录 > 配置文件 > 环境变量 > 空（从 PATH 查找）
        """
        if explicit_dir:
            return explicit_dir
        bundled = _bundled_ffmpeg_dir()
        if bundled:
            return bundled
        # 从配置文件读取，避免模块级 _DEFAULT_FFMPEG_DIR 在环境变量设置前就被求值的问题
        try:
            from srt_maker.core.config import load_config
            config_dir = load_config().get("ffmpeg_dir", "")
            if config_dir:
                return config_dir
        except Exception:
            pass
        if _DEFAULT_FFMPEG_DIR:
            return _DEFAULT_FFMPEG_DIR
        return ""

    def _ffmpeg_cmd(self) -> str:
        """返回 ffmpeg 可执行文件路径"""
        if self._ffmpeg_dir:
            return str(Path(self._ffmpeg_dir) / "ffmpeg.exe")
        return "ffmpeg"

    def _ffprobe_cmd(self) -> str:
        """返回 ffprobe 可执行文件路径"""
        if self._ffmpeg_dir:
            return str(Path(self._ffmpeg_dir) / "ffprobe.exe")
        return "ffprobe"

    def is_available(self) -> bool:
        """检查 FFmpeg 是否可用"""
        try:
            subprocess.run(
                [self._ffmpeg_cmd(), "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_duration(self, video_path: str) -> float:
        """获取视频时长（秒）"""
        cmd = [
            self._ffprobe_cmd(), "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip())

    def extract_audio(self, video_path: str, output_path: str) -> None:
        """从视频提取音频为 16kHz 单声道 PCM 16-bit WAV"""
        cmd = [
            self._ffmpeg_cmd(), "-i", video_path,
            "-vn", "-ac", "1", "-ar", "16000",
            "-sample_fmt", "s16", "-c:a", "pcm_s16le",
            "-y", output_path,
        ]
        subprocess.run(cmd, check=True, timeout=300)

    def create_test_video(self, output_path: str, duration: float = 5.0) -> None:
        """创建测试视频（黑色画面，静音）"""
        cmd = [
            self._ffmpeg_cmd(),
            "-f", "lavfi", "-i", f"color=c=black:s=640x480:d={duration}",
            "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={duration}",
            "-c:v", "libx264", "-c:a", "aac",
            "-shortest", "-y", output_path,
        ]
        subprocess.run(cmd, check=True, timeout=60)

    def burn_subtitles(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
        font_name: str = "微软雅黑",
        font_size: int = 24,
        color: str = "&H00FFFFFF",
    ) -> None:
        """将字幕硬编码到视频中

        将 SRT 转换为带样式的 ASS 文件，避免 force_style 参数解析问题。
        临时 ASS 文件创建在与视频文件同目录，使用相对路径避免 Windows 盘符冒号问题。
        超长字幕会在烧录前自动拆分，避免 libass 换行导致第二行被裁剪。
        """
        from srt_maker.io.srt_parser import parse_srt
        from srt_maker.core.timecode import seconds_to_srt

        # 读取并解析 SRT
        with open(srt_path, "r", encoding="utf-8") as f:
            srt_content = f.read()
        entries = parse_srt(srt_content)

        # 拆分超长字幕，避免 libass 自动换行导致第二行被裁剪
        entries = _split_long_subtitles(entries)

        # 将 SRT 内容转换为 ASS 文件（含样式信息）
        ass_content = (
            "[Script Info]\n"
            "Title: Generated by SRT Maker\n"
            "ScriptType: v4.00+\n"
            "WrapStyle:2\n"
            "PlayResX:640\n"
            "PlayResY:480\n"
            "\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "BorderStyle, Outline, Shadow, MarginL, MarginR, MarginV, Alignment, "
            "Encoding\n"
            f"Style:Default,{font_name},{font_size},{color},&H00000000,&H00000000,&H00000000,"
            "0,0,0,0,1,1,0,10,10,10,2,1\n"
            "\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )

        for entry in entries:
            start = seconds_to_srt(entry.start_time).replace(",", ".")
            end = seconds_to_srt(entry.end_time).replace(",", ".")
            text = entry.text.replace("\n", "\\N")
            ass_content += (
                f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n"
            )

        # 在视频文件同目录创建临时 ASS 文件，使用相对路径避免 Windows 盘符问题
        video_dir = str(Path(video_path).parent)
        ass_fd, ass_path = tempfile.mkstemp(
            suffix=".ass",
            prefix="srt_maker_",
            dir=video_dir,
        )
        try:
            with os.fdopen(ass_fd, "w", encoding="utf-8") as f:
                f.write(ass_content)

            # 使用相对于视频目录的文件名（无盘符，无冒号）
            ass_filename = Path(ass_path).name

            cmd = [
                self._ffmpeg_cmd(),
                "-i", video_path,
                "-vf", f"subtitles={ass_filename}",
                "-c:a", "copy",
                "-y", output_path,
            ]
            subprocess.run(cmd, check=True, timeout=600, cwd=video_dir)
        finally:
            os.unlink(ass_path)
