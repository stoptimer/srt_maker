#!/usr/bin/env python3
"""SRT Maker 构建脚本

自动化流程：
1. 检查 Python 版本
2. 检查运行时依赖（PyTorch、Whisper）
3. 下载 FFmpeg 静态编译版本
4. 运行 PyInstaller 打包
5. 复制 FFmpeg 到打包输出目录

注意：PyTorch 和 Whisper 不作为打包依赖，由用户预先安装。
"""

# 必须在所有 import 之前设置，避免 OpenMP DLL 冲突
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
FFMPEG_BUILD_DIR = PROJECT_ROOT / "build" / "ffmpeg"
DIST_DIR = PROJECT_ROOT / "dist" / "srt_maker"
FFMPEG_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/"
    "ffmpeg-master-latest-win64-gpl.zip"
)

# 运行时依赖（不打包进程序，需用户预先安装）
RUNTIME_DEPENDENCIES = ["torch", "whisper"]


def check_python_version() -> bool:
    """检查 Python 版本 >= 3.10"""
    if sys.version_info < (3, 10):
        print("错误: 需要 Python 3.10 或更高版本")
        return False
    print(f"Python 版本: {sys.version}")
    return True


def check_runtime_dependencies() -> bool:
    """检查运行时依赖是否已安装

    这些依赖不打包进程序，但运行时需要存在。
    """
    missing = []
    for dep in RUNTIME_DEPENDENCIES:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            missing.append(dep)

    if missing:
        print(f"警告: 以下运行时依赖未安装: {', '.join(missing)}")
        print("程序启动后语音识别功能将不可用。")
        print(f"安装命令: pip install {' '.join(missing)}")
        return False
    print(f"运行时依赖已安装: {', '.join(RUNTIME_DEPENDENCIES)}")
    return True


def download_ffmpeg() -> Path:
    """下载 FFmpeg 静态编译版本

    使用 FFmpeg-Builds 的 GitHub Releases zip 包。

    返回 FFmpeg 可执行文件所在目录。
    """
    if (FFMPEG_BUILD_DIR / "ffmpeg.exe").exists():
        print("FFmpeg 已存在，跳过下载")
        return FFMPEG_BUILD_DIR

    print("正在下载 FFmpeg...")
    FFMPEG_BUILD_DIR.mkdir(parents=True, exist_ok=True)

    try:
        import requests
        import zipfile

        # 下载 zip 包
        print(f"下载: {FFMPEG_URL}")
        response = requests.get(FFMPEG_URL, stream=True, timeout=300)
        response.raise_for_status()

        archive_path = FFMPEG_BUILD_DIR / "ffmpeg.zip"
        with open(archive_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("正在解压 FFmpeg...")
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(FFMPEG_BUILD_DIR)

        archive_path.unlink()

        # 查找可执行文件 — zip 包的目录结构为 ffmpeg-*/bin/
        # 将 ffmpeg.exe 和 ffprobe.exe 移到顶层
        for exe_name in ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]:
            exes = list(FFMPEG_BUILD_DIR.glob(f"**/{exe_name}"))
            for exe in exes:
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
        print("下载地址: https://github.com/BtbN/FFmpeg-Builds/releases")
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

    for exe in ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]:
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

    # 2. 检查运行时依赖
    check_runtime_dependencies()

    # 3. 下载 FFmpeg
    download_ffmpeg()

    # 4. 运行 PyInstaller
    if not run_pyinstaller():
        sys.exit(1)

    # 5. 复制 FFmpeg
    copy_ffmpeg_to_dist()

    print()
    print("=" * 50)
    print("构建完成!")
    print(f"输出目录: {DIST_DIR}")
    print()
    print("注意: 运行时需要安装以下依赖:")
    print(f"  pip install {' '.join(RUNTIME_DEPENDENCIES)}")
    print("=" * 50)


if __name__ == "__main__":
    main()
