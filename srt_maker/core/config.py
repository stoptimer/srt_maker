import json
import os
from pathlib import Path
from typing import Any

_CONFIG_DIR = Path(os.environ.get("USERPROFILE", Path.home())) / ".srt_maker"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

_DEFAULTS = {
    "ffmpeg_dir": "",
}


def load_config() -> dict[str, Any]:
    """加载配置文件，不存在则返回默认值"""
    if _CONFIG_FILE.exists():
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        # 合并默认值，确保新增字段有默认值
        return {**_DEFAULTS, **saved}
    return _DEFAULTS.copy()


def save_config(data: dict[str, Any]) -> None:
    """保存配置到文件"""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
