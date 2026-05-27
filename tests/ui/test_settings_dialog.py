import pytest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from srt_maker.ui.settings_dialog import SettingsDialog


@pytest.mark.qt_no_exception_capture
def test_settings_dialog_creation(qtbot):
    """测试设置对话框可以正常创建"""
    with patch('srt_maker.core.config._CONFIG_FILE') as mock_file:
        mock_file.exists.return_value = False
        dialog = SettingsDialog()
        qtbot.add_widget(dialog)
        assert dialog is not None


@pytest.mark.qt_no_exception_capture
def test_settings_dialog_save_valid_path(qtbot, tmp_path):
    """测试保存有效的 FFmpeg 路径"""
    # 创建模拟的 ffmpeg.exe
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    (fake_bin / "ffmpeg.exe").touch()

    # Mock config 文件
    fake_config = tmp_path / "config.json"

    with patch('srt_maker.core.config._CONFIG_FILE', fake_config):
        dialog = SettingsDialog()
        qtbot.add_widget(dialog)

        # 模拟设置路径
        dialog._path_edit.setText(str(fake_bin))

        # Mock QMessageBox.information 以避免对话框阻塞
        with patch('srt_maker.ui.settings_dialog.QMessageBox.information'):
            dialog._save()

        # 验证配置已保存
        saved = __import__('srt_maker.core.config', fromlist=['load_config']).load_config()
        assert saved["ffmpeg_dir"] == str(fake_bin)


@pytest.mark.qt_no_exception_capture
def test_settings_dialog_reject_invalid_path(qtbot, tmp_path):
    """测试不含 ffmpeg.exe 的路径被拒绝"""
    # 创建不含 ffmpeg.exe 的目录
    fake_bin = tmp_path / "no_ffmpeg"
    fake_bin.mkdir()

    fake_config = tmp_path / "config.json"

    with patch('srt_maker.core.config._CONFIG_FILE', fake_config):
        dialog = SettingsDialog()
        qtbot.add_widget(dialog)
        dialog._path_edit.setText(str(fake_bin))

        # Mock QMessageBox.warning 以避免对话框阻塞
        with patch('srt_maker.ui.settings_dialog.QMessageBox.warning') as mock_warning:
            dialog._save()
            # 应该弹出警告
            mock_warning.assert_called_once()
