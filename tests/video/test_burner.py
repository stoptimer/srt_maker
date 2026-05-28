import os
import pytest

from srt_maker.video.burner import SubtitleBurner
from srt_maker.video.ffmpeg_wrapper import FFmpegWrapper
from srt_maker.core.subtitle_model import SubtitleEntry
from srt_maker.io.srt_parser import write_srt

wrapper = FFmpegWrapper()
ffmpeg_available = wrapper.is_available()

@pytest.mark.skipif(not ffmpeg_available, reason="FFmpeg 未安装")
def test_burn_subtitles(tmp_path):
    """测试字幕烧录"""
    video = str(tmp_path / "input.mp4")
    FFmpegWrapper().create_test_video(video, duration=3.0)

    srt_content = write_srt([SubtitleEntry(0.5, 1.5, "测试字幕")])
    srt_path = str(tmp_path / "sub.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    output = str(tmp_path / "output.mp4")
    burner = SubtitleBurner()
    burner.burn(video, srt_path, output)

    assert os.path.exists(output)
    assert os.path.getsize(output) > 0
