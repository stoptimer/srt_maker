# srt_maker/speech/cloud_recognizer.py
import requests

from srt_maker.speech.base import SpeechRecognizer
from srt_maker.core.subtitle_list import SubtitleList
from srt_maker.core.subtitle_model import SubtitleEntry


class CloudSpeechRecognizer(SpeechRecognizer):
    """云端语音识别 API 适配器"""

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://nls-api.aliyun.com",
    ):
        self._api_key = api_key
        self._api_url = api_url

    def name(self) -> str:
        return "云端 API"

    def recognize(self, audio_path: str, language: str) -> SubtitleList:
        """识别音频并返回字幕列表"""
        subtitles = SubtitleList()

        with open(audio_path, "rb") as f:
            response = requests.post(
                self._api_url,
                headers={"Authorization": self._api_key},
                files={"audio": ("audio.wav", f, "audio/wav")},
                data={"language": language},
                timeout=300,
            )

        response.raise_for_status()
        data = response.json()

        # 假设返回格式: {"results": [{"start": 0.0, "end": 2.0, "text": "..."}]}
        for item in data.get("results", []):
            entry = SubtitleEntry(
                start_time=item["start"],
                end_time=item["end"],
                text=item["text"].strip(),
            )
            subtitles.entries.append(entry)

        return subtitles
