# tests/speech/test_base.py
from srt_maker.speech.base import SpeechRecognizer


def test_abstract_cannot_instantiate():
    """测试抽象类不能直接实例化"""
    try:
        SpeechRecognizer()  # type: ignore
        assert False, "不应能实例化抽象类"
    except TypeError:
        pass
