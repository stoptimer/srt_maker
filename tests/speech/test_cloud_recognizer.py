# tests/speech/test_cloud_recognizer.py
from srt_maker.speech.cloud_recognizer import CloudSpeechRecognizer

def test_cloud_name():
    """测试云端识别器名称"""
    recognizer = CloudSpeechRecognizer(api_key="test", api_url="https://api.example.com")
    assert recognizer.name() == "云端 API"

def test_cloud_instance():
    """测试云端识别器实例化"""
    recognizer = CloudSpeechRecognizer(api_key="test_key", api_url="https://api.example.com")
    assert recognizer is not None
