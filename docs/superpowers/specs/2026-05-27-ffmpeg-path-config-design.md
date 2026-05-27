# FFmpeg 路径配置设计

**目标:** 让用户通过 GUI 选择 FFmpeg 的 bin 目录路径，持久化保存，应用启动时自动加载。

**架构:** 在菜单栏新增"设置"菜单，弹出设置对话框。配置以 JSON 格式存储在 `%USERPROFILE%/.srt_maker/config.json`。应用启动时读取配置并设置 `FFMPEG_DIR` 环境变量，使所有 `FFmpegWrapper` 无参构造自动生效。

**技术栈:** PySide6 (QDialog, QFileDialog), JSON 文件读写

---

## 动机

当前 `FFmpegWrapper` 依赖 `PATH` 或 `FFMPEG_DIR` 环境变量查找 FFmpeg。普通用户安装 FFmpeg 后通常不会配置环境变量，导致应用报错 `[WinError 2] 系统找不到指定的文件`。需要提供 GUI 方式让用户指定 FFmpeg 路径。

## 设计决策

### 为什么用环境变量而非显式传参

`FFmpegWrapper` 已支持 `ffmpeg_dir` 参数，但调用链较长（MainWindow → RecognitionWorker → AudioExtractor → FFmpegWrapper）。在 `main.py` 启动时设置 `FFMPEG_DIR` 环境变量，所有无参构造的 `FFmpegWrapper()` 自动生效，无需改动调用链。

### 为什么用 JSON 而非 QSettings

用户选择 JSON 配置文件。简单直接，不依赖 Qt 的注册表机制，便于调试和手动编辑。

### 配置文件位置

`%USERPROFILE%/.srt_maker/config.json` — 用户 home 目录下，不污染项目目录，跨会话持久化。

## 组件设计

### 1. 配置管理 (`srt_maker/core/config.py`)

```python
# srt_maker/core/config.py

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
```

### 2. 设置对话框 (`srt_maker/ui/settings_dialog.py`)

简单的 QDialog，包含 FFmpeg 路径配置：

- **QLabel** "FFmpeg 路径" — 标签
- **QLineEdit** — 显示当前路径，只读
- **QPushButton** "浏览..." — 打开文件夹选择对话框
- **QPushButton** "重置" — 清空路径
- **QPushButton** "保存" — 验证并保存
- **QPushButton** "取消" — 关闭对话框

验证逻辑：保存时检查目录中是否存在 `ffmpeg.exe`，不存在则弹出提示。

保存后立即更新 `FFmpegWrapper._DEFAULT_FFMPEG_DIR`，使当前会话生效。

### 3. 主窗口集成 (`srt_maker/ui/main_window.py`)

在 `_setup_menu()` 中新增"设置"菜单：

```python
settings_menu = menu_bar.addMenu("设置")
settings_action = settings_menu.addAction("设置")
settings_action.triggered.connect(self._show_settings)
```

`_show_settings()` 方法创建并显示 `SettingsDialog`。

### 4. 应用入口 (`srt_maker/main.py`)

在 `app = QApplication(sys.argv)` 之后、`window = MainWindow()` 之前：

```python
from srt_maker.core.config import load_config

config = load_config()
if config.get("ffmpeg_dir"):
    os.environ["FFMPEG_DIR"] = config["ffmpeg_dir"]
```

## 数据流

```
应用启动
  → load_config() 读取 ~/.srt_maker/config.json
  → 设置 os.environ["FFMPEG_DIR"]
  → FFmpegWrapper 自动使用配置的路径

用户点击 设置 > 设置
  → SettingsDialog 显示当前 ffmpeg_dir
  → 用户点击浏览 → QFileDialog.getExistingDirectory
  → 选择目录 → QLineEdit 显示路径
  → 点击保存
    → 验证 ffmpeg.exe 存在
    → save_config() 写入 JSON
    → 更新 FFmpegWrapper._DEFAULT_FFMPEG_DIR（当前会话生效）
    → 关闭对话框
```

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| 配置文件不存在 | 返回默认值（空字符串） |
| 配置文件格式错误 | 提示用户，回退到默认值 |
| 选择的目录不含 ffmpeg.exe | 弹出警告，不允许保存 |
| 保存失败（权限等） | 弹出错误提示 |

## 测试策略

| 测试 | 内容 |
|------|------|
| `test_config_load_default` | 配置文件不存在时返回默认值 |
| `test_config_save_and_load` | 写入配置后能正确读取 |
| `test_config_merge_defaults` | 旧配置缺少新增字段时使用默认值 |
| `test_settings_dialog_creation` | 对话框可正常创建 |
| `test_settings_dialog_save_valid_path` | 有效路径能保存 |
| `test_settings_dialog_reject_invalid_path` | 不含 ffmpeg.exe 的路径被拒绝 |
| `test_main_window_settings_menu` | 设置菜单项存在 |
