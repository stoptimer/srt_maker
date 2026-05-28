# SRT Maker PyInstaller 打包实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使用 PyInstaller 将 SRT Maker 打包为不依赖任何 Python 环境的独立目录，普通 Windows 用户双击即可运行。

**Architecture:** PyInstaller 目录模式打包，FFmpeg 捆绑在打包目录中，Whisper 模型按需下载。修改 `FFmpegWrapper` 增加对打包目录下 FFmpeg 的自动查找。

**Tech Stack:** PyInstaller, Python 3.10+, Windows 11

---

## 文件概览

| 操作 | 文件 | 职责 |
|------|------|------|
| 创建 | `build.py` | 自动化构建脚本：下载 FFmpeg、运行 PyInstaller |
| 创建 | `srt_maker.spec` | PyInstaller 配置文件 |
| 修改 | `srt_maker/video/ffmpeg_wrapper.py` | 增加打包目录 FFmpeg 查找逻辑 |
| 修改 | `pyproject.toml` | 添加 PyInstaller 为 dev 依赖 |
| 修改 | `.gitignore` | 忽略打包输出目录 |

---

### Task 1: 添加 PyInstaller 依赖

**Files:**
- Modify: `pyproject.toml`
- Modify: `.gitignore`

- [ ] **Step 1: 添加 PyInstaller 为 dev 依赖**

在 `pyproject.toml` 的 `[project.optional-dependencies]` 中添加：

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-qt>=4.2",
    "pyinstaller>=6.0",
]
```

- [ ] **Step 2: 更新 .gitignore**

在 `.gitignore` 中添加打包输出目录：

```
# PyInstaller 输出
dist/
build/
*.spec
```

- [ ] **Step 3: 安装依赖**

```bash
pip install -e ".[dev]"
```

- [ ] **Step 4: 验证 PyInstaller 已安装**

```bash
pyinstaller --version
```

期望输出：`6.x.x`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore
git commit -m "chore: 添加 PyInstaller 为 dev 依赖"
```

---

### Task 2: 修改 FFmpegWrapper 增加打包目录查找

**Files:**
- Modify: `srt_maker/video/ffmpeg_wrapper.py:1-27`
- Test: `tests/video/test_ffmpeg_wrapper.py`

- [ ] **Step 1: 写测试 — 验证打包目录查找逻辑**

在 `tests/video/test_ffmpeg_wrapper.py` 中添加测试：

```python
def test_bundled_ffmpeg_dir_returns_empty_when_not_found(tmp_path):
    """打包目录下没有 FFmpeg 时返回空字符串"""
    from srt_maker.video.ffmpeg_wrapper import _bundled_ffmpeg_dir
    # 不在打包环境中，_MEIPASS 不存在
    result = _bundled_ffmpeg_dir()
    assert result == ""

def test_bundled_ffmpeg_dir_finds_ffmpeg_in_meipass(tmp_path, monkeypatch):
    """打包目录下有 FFmpeg 时返回正确路径"""
    import sys
    ffmpeg_dir = tmp_path / "ffmpeg"
    ffmpeg_dir.mkdir()
    (ffmpeg_dir / "ffmpeg.exe").touch()
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path))
    from srt_maker.video.ffmpeg_wrapper import _bundled_ffmpeg_dir
    result = _bundled_ffmpeg_dir()
    assert result == str(ffmpeg_dir)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/video/test_ffmpeg_wrapper.py::test_bundled_ffmpeg_dir_returns_empty_when_not_found -v
pytest tests/video/test_ffmpeg_wrapper.py::test_bundled_ffmpeg_dir_finds_ffmpeg_in_meipass -v
```

期望：FAIL — `_bundled_ffmpeg_dir` 未定义

- [ ] **Step 3: 实现 `_bundled_ffmpeg_dir` 函数**

在 `srt_maker/video/ffmpeg_wrapper.py` 中添加：

```python
import sys
from pathlib import Path

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
```

- [ ] **Step 4: 修改 `FFmpegWrapper.__init__` 使用查找链**

将 `FFmpegWrapper.__init__` 的查找逻辑改为：用户配置 → 打包目录 → 环境变量 → 空（从 PATH 查找）

```python
_DEFAULT_FFMPEG_DIR = os.environ.get("FFMPEG_DIR", "")

class FFmpegWrapper:
    def __init__(self, ffmpeg_dir: str = ""):
        self._ffmpeg_dir = self._resolve_ffmpeg_dir(ffmpeg_dir)

    @staticmethod
    def _resolve_ffmpeg_dir(explicit_dir: str) -> str:
        """解析 FFmpeg 目录，按优先级查找

        优先级：显式参数 > 打包目录 > 环境变量 > 空（从 PATH 查找）
        """
        if explicit_dir:
            return explicit_dir
        bundled = _bundled_ffmpeg_dir()
        if bundled:
            return bundled
        if _DEFAULT_FFMPEG_DIR:
            return _DEFAULT_FFMPEG_DIR
        return ""
```

- [ ] **Step 5: 运行测试验证通过**

```bash
pytest tests/video/test_ffmpeg_wrapper.py -v
```

期望：全部 PASS

- [ ] **Step 6: Commit**

```bash
git add srt_maker/video/ffmpeg_wrapper.py tests/video/test_ffmpeg_wrapper.py
git commit -m "feat: FFmpegWrapper 增加打包目录 FFmpeg 自动查找"
```

---

### Task 3: 创建 PyInstaller Spec 文件

**Files:**
- Create: `srt_maker.spec`

- [ ] **Step 1: 创建 srt_maker.spec 文件**

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['srt_maker/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'torch',
        'torch._C',
        'whisper',
        'silero_vad',
        'pyqtgraph',
        'pyqtgraph.graphicsItems',
        'opencv_python',
        'cv2',
        'numpy',
        'ffmpeg',
        'ffmpeg._ffmpeg',
        'srt_maker',
        'srt_maker.core',
        'srt_maker.core.config',
        'srt_maker.core.subtitle_model',
        'srt_maker.core.subtitle_list',
        'srt_maker.core.timecode',
        'srt_maker.audio',
        'srt_maker.audio.extractor',
        'srt_maker.audio.vad',
        'srt_maker.speech',
        'srt_maker.speech.base',
        'srt_maker.speech.whisper_recognizer',
        'srt_maker.speech.qwen_asr_recognizer',
        'srt_maker.speech.cloud_recognizer',
        'srt_maker.video',
        'srt_maker.video.ffmpeg_wrapper',
        'srt_maker.video.player',
        'srt_maker.video.burner',
        'srt_maker.io',
        'srt_maker.io.srt_parser',
        'srt_maker.io.ass_parser',
        'srt_maker.ui',
        'srt_maker.ui.main_window',
        'srt_maker.ui.video_preview',
        'srt_maker.ui.waveform_view',
        'srt_maker.ui.subtitle_editor',
        'srt_maker.ui.style_panel',
        'srt_maker.ui.recognition_worker',
        'srt_maker.ui.settings_dialog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'tkinter',
        'unittest',
        'pytest',
        'setuptools',
        'pip',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='srt_maker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 收集 PySide6 的所有资源文件
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='srt_maker',
)
```

- [ ] **Step 2: Commit**

```bash
git add srt_maker.spec
git commit -m "feat: 创建 PyInstaller spec 文件，配置隐藏导入和排除项"
```

---

### Task 4: 创建构建脚本

**Files:**
- Create: `build.py`

- [ ] **Step 1: 创建 build.py**

```python
#!/usr/bin/env python3
"""SRT Maker 构建脚本

自动化流程：
1. 检查 Python 版本
2. 下载 FFmpeg 静态编译版本
3. 运行 PyInstaller 打包
4. 复制 FFmpeg 到打包输出目录
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
FFMPEG_BUILD_DIR = PROJECT_ROOT / "build" / "ffmpeg"
DIST_DIR = PROJECT_ROOT / "dist" / "srt_maker"
FFMPEG_URL = (
    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full-full.7z"
)

def check_python_version() -> bool:
    """检查 Python 版本 >= 3.10"""
    if sys.version_info < (3, 10):
        print("错误: 需要 Python 3.10 或更高版本")
        return False
    print(f"Python 版本: {sys.version}")
    return True

def download_ffmpeg() -> Path:
    """下载 FFmpeg 静态编译版本

    使用 FFmpeg 的 gyan.dev 预编译版本。
    由于 7z 格式需要解压工具，这里使用 requests 下载并处理。

    返回 FFmpeg 可执行文件所在目录。
    """
    if (FFMPEG_BUILD_DIR / "ffmpeg.exe").exists():
        print("FFmpeg 已存在，跳过下载")
        return FFMPEG_BUILD_DIR

    print("正在下载 FFmpeg...")
    FFMPEG_BUILD_DIR.mkdir(parents=True, exist_ok=True)

    try:
        import requests

        # 尝试下载 gyan.dev 的 7z 包
        print(f"下载: {FFMPEG_URL}")
        response = requests.get(FFMPEG_URL, stream=True, timeout=300)
        response.raise_for_status()

        archive_path = FFMPEG_BUILD_DIR / "ffmpeg.7z"
        with open(archive_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("正在解压 FFmpeg...")
        # 尝试使用 7z 解压
        try:
            subprocess.run(
                ["7z", "x", str(archive_path), f"-o{FFMPEG_BUILD_DIR}", "-y"],
                check=True,
                timeout=120,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            # 尝试使用 Python 的 py7zr
            try:
                import py7zr
                with py7zr.SevenZipFile(archive_path, "r") as archive:
                    archive.extractall(FFMPEG_BUILD_DIR)
            except ImportError:
                print("警告: 无法解压 7z 文件。请手动下载 FFmpeg 并放到 build/ffmpeg/ 目录")
                print("下载地址: https://www.gyan.dev/ffmpeg/builds/")
                raise

        archive_path.unlink()

        # 查找 ffmpeg.exe — gyan.dev 的目录结构为 ffmpeg-*/bin/
        ffmpeg_exe = list(FFMPEG_BUILD_DIR.glob("**/ffmpeg.exe"))
        if ffmpeg_exe:
            # 如果解压到子目录，将可执行文件移到顶层
            for exe in ffmpeg_exe:
                if exe.parent != FFMPEG_BUILD_DIR:
                    shutil.move(str(exe), FFMPEG_BUILD_DIR / exe.name)

        if (FFMPEG_BUILD_DIR / "ffmpeg.exe").exists():
            print("FFmpeg 下载完成")
            return FFMPEG_BUILD_DIR
        else:
            print("警告: 未找到 ffmpeg.exe，请手动放置")
            return FFMPEG_BUILD_DIR

    except Exception as e:
        print(f"下载 FFmpeg 失败: {e}")
        print("请手动下载 FFmpeg 并放到 build/ffmpeg/ 目录")
        print("下载地址: https://www.gyan.dev/ffmpeg/builds/")
        return FFMPEG_BUILD_DIR

def run_pyinstaller() -> bool:
    """运行 PyInstaller 打包"""
    print("正在运行 PyInstaller...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "srt_maker.spec", "--clean"],
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        print("PyInstaller 打包失败")
        return False
    print("PyInstaller 打包完成")
    return True

def copy_ffmpeg_to_dist() -> bool:
    """将 FFmpeg 复制到打包输出目录"""
    ffmpeg_exe = FFMPEG_BUILD_DIR / "ffmpeg.exe"
    if not ffmpeg_exe.exists():
        print("警告: build/ffmpeg/ffmpeg.exe 不存在，跳过复制")
        return False

    dist_ffmpeg = DIST_DIR / "ffmpeg"
    dist_ffmpeg.mkdir(exist_ok=True)

    for exe in ["ffmpeg.exe", "ffprobe.exe"]:
        src = FFMPEG_BUILD_DIR / exe
        dst = dist_ffmpeg / exe
        if src.exists():
            shutil.copy2(src, dst)
            print(f"已复制: {exe}")

    return True

def main():
    print("=" * 50)
    print("SRT Maker 构建脚本")
    print("=" * 50)

    # 1. 检查 Python 版本
    if not check_python_version():
        sys.exit(1)

    # 2. 下载 FFmpeg
    download_ffmpeg()

    # 3. 运行 PyInstaller
    if not run_pyinstaller():
        sys.exit(1)

    # 4. 复制 FFmpeg
    copy_ffmpeg_to_dist()

    print()
    print("=" * 50)
    print("构建完成!")
    print(f"输出目录: {DIST_DIR}")
    print("=" * 50)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证构建脚本语法**

```bash
python -c "import ast; ast.parse(open('build.py').read()); print('语法正确')"
```

- [ ] **Step 3: Commit**

```bash
git add build.py
git commit -m "feat: 创建自动化构建脚本，支持 FFmpeg 下载和 PyInstaller 打包"
```

---

### Task 5: 运行构建并验证

**Files:**
- Run: `build.py`
- Test: 手动验证打包结果

- [ ] **Step 1: 运行构建脚本**

```bash
python build.py
```

期望输出：
- Python 版本检查通过
- FFmpeg 下载成功（或跳过）
- PyInstaller 打包成功
- FFmpeg 复制到输出目录

- [ ] **Step 2: 检查打包输出结构**

```bash
ls dist/srt_maker/
```

期望看到：
- `srt_maker.exe`
- `_internal/` 目录
- `ffmpeg/` 目录（含 ffmpeg.exe, ffprobe.exe）

- [ ] **Step 3: 测试程序启动**

```bash
dist/srt_maker/srt_maker.exe
```

期望：程序正常启动，显示主窗口

- [ ] **Step 4: 测试 FFmpeg 可用性**

在程序设置中检查 FFmpeg 是否被正确识别（应自动找到打包目录下的 FFmpeg）

- [ ] **Step 5: 处理构建问题**

如果构建过程中遇到问题：
- PyInstaller 缺少隐藏导入 → 在 `srt_maker.spec` 中添加
- PySide6 平台插件缺失 → 添加 `--collect-all PySide6`
- Qt 显示错误 → 检查 `_internal/` 下是否有 `PySide6/qtplugins/platforms/`

- [ ] **Step 6: Commit 构建结果（如需要调整）**

如果 spec 文件或构建脚本需要调整，提交修复：

```bash
git add srt_maker.spec build.py
git commit -m "fix: 修复 PyInstaller 打包问题"
```

---

### Task 6: 添加 PyInstaller 到 pyproject.toml 的打包配置（可选）

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: 添加 PyInstaller 构建后端（可选）**

如果希望支持 `pip install` 后直接打包，可在 `pyproject.toml` 中添加：

```toml
[tool.pyinstaller]
# 此配置供参考，实际使用 srt_maker.spec 文件
```

此步骤为可选，因为 `srt_maker.spec` 已包含所有配置。如果不需要可跳过。

---

## 验证清单

打包完成后，在干净的 Windows 环境中验证以下功能：

- [ ] 程序能正常启动（双击 srt_maker.exe）
- [ ] 视频预览功能正常
- [ ] 音频提取功能正常（依赖打包目录下的 FFmpeg）
- [ ] Whisper 语音识别功能正常（首次运行需下载模型）
- [ ] 字幕编辑功能正常
- [ ] 字幕烧录功能正常（依赖打包目录下的 FFmpeg）
- [ ] 设置对话框中 FFmpeg 路径配置正常
