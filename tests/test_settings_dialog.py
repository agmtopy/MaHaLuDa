"""SettingsDialog 配置修复测试"""
import pytest
from pathlib import Path
import tempfile

from PyQt6.QtWidgets import QDialogButtonBox
from PyQt6.QtCore import Qt

from src.core.config_manager import Config
from src.gui.settings_dialog import SettingsDialog


class TestSettingsDialog:
    """SettingsDialog 测试类"""

    def test_apply_valid_settings(self, qtbot, tmp_path):
        """验证有效设置能正确应用"""
        # 创建临时git仓库
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # 创建配置文件路径
        config_path = tmp_path / "config.yaml"

        # 创建初始配置
        config = Config()
        config.git.repo_path = str(repo_path)
        config.github.username = "testuser"
        config.github.repo_name = "testrepo"
        config.hotkey.key = "ctrl+shift+a"

        # 创建对话框
        dialog = SettingsDialog(config)
        qtbot.addWidget(dialog)

        # 修改UI值
        dialog.hotkey_edit.setText("ctrl+f1")
        dialog.username_edit.setText("newuser")
        dialog.repo_name_edit.setText("newrepo")

        # 应用设置
        result = dialog._apply_settings()

        # 断言
        assert result is True
        assert config.hotkey.key == "ctrl+f1"
        assert config.github.username == "newuser"
        assert config.github.repo_name == "newrepo"

    def test_apply_invalid_settings(self, qtbot, tmp_path):
        """验证无效设置不会污染原配置"""
        # 创建临时git仓库
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # 创建有效的初始配置
        config = Config()
        config.git.repo_path = str(repo_path)
        config.github.username = "testuser"
        config.github.repo_name = "testrepo"
        config.hotkey.key = "ctrl+shift+a"

        # 记录原始值
        original_key = config.hotkey.key
        original_username = config.github.username

        # 创建对话框
        dialog = SettingsDialog(config)
        qtbot.addWidget(dialog)

        # 在UI中输入无效值（空仓库路径）
        dialog.repo_path_edit.setText("")
        dialog.hotkey_edit.setText("ctrl+f2")

        # 尝试应用设置
        result = dialog._apply_settings()

        # 断言
        assert result is False
        # 原始配置值应保持不变
        assert config.hotkey.key == original_key
        assert config.github.username == original_username
        assert config.git.repo_path == str(repo_path)

    def test_cancel_restores_original_config(self, qtbot, tmp_path):
        """验证取消按钮能恢复原始配置"""
        # 创建临时git仓库
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # 创建配置
        config = Config()
        config.git.repo_path = str(repo_path)
        config.github.username = "testuser"
        config.github.repo_name = "testrepo"
        config.hotkey.key = "ctrl+shift+a"
        config.git.target_folder = "screenshots"
        config.git.branch = "main"

        # 记录所有初始值
        original_values = {
            "hotkey_key": config.hotkey.key,
            "hotkey_enabled": config.hotkey.enabled,
            "git_repo_path": config.git.repo_path,
            "git_target_folder": config.git.target_folder,
            "git_branch": config.git.branch,
            "git_auto_pull": config.git.auto_pull,
            "github_username": config.github.username,
            "github_repo_name": config.github.repo_name,
        }

        # 创建对话框
        dialog = SettingsDialog(config)
        qtbot.addWidget(dialog)

        # 修改多个UI字段
        dialog.hotkey_edit.setText("ctrl+alt+x")
        dialog.hotkey_enabled_check.setChecked(False)
        dialog.target_folder_edit.setText("images")
        dialog.branch_edit.setText("develop")
        dialog.username_edit.setText("changeduser")
        dialog.repo_name_edit.setText("changedrepo")

        # 调用取消
        dialog._on_cancel()

        # 断言配置恢复到初始状态
        assert config.hotkey.key == original_values["hotkey_key"]
        assert config.hotkey.enabled == original_values["hotkey_enabled"]
        assert config.git.repo_path == original_values["git_repo_path"]
        assert config.git.target_folder == original_values["git_target_folder"]
        assert config.git.branch == original_values["git_branch"]
        assert config.git.auto_pull == original_values["git_auto_pull"]
        assert config.github.username == original_values["github_username"]
        assert config.github.repo_name == original_values["github_repo_name"]

    def test_collect_settings_creates_new_config(self, qtbot, tmp_path):
        """验证 _collect_settings 创建独立对象"""
        # 创建临时git仓库
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # 创建配置
        config = Config()
        config.git.repo_path = str(repo_path)
        config.github.username = "testuser"
        config.github.repo_name = "testrepo"

        # 创建对话框
        dialog = SettingsDialog(config)
        qtbot.addWidget(dialog)

        # 记录原始对象id
        original_config_id = id(dialog.config)

        # 修改UI值
        dialog.hotkey_edit.setText("alt+f12")
        dialog.username_edit.setText("collecteduser")
        dialog.quality_spin.setValue(85)

        # 收集设置
        new_config = dialog._collect_settings()

        # 断言
        assert new_config is not None
        assert id(new_config) != original_config_id  # 新对象
        assert new_config.hotkey.key == "alt+f12"
        assert new_config.github.username == "collecteduser"
        assert new_config.image.quality == 85
        # 原config对象未被修改
        assert config.hotkey.key == "ctrl+shift+a"  # 默认值
        assert config.github.username == "testuser"

    def test_copy_config_values(self, qtbot, tmp_path):
        """验证 _copy_config_values 正确复制所有字段"""
        # 创建临时git仓库
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # 创建源配置，设置所有字段为特定值
        source = Config()
        source.hotkey.key = "ctrl+f9"
        source.hotkey.enabled = False
        source.git.repo_path = str(repo_path)
        source.git.target_folder = "my_images"
        source.git.branch = "release"
        source.git.auto_pull = True
        source.github.username = "sourceuser"
        source.github.repo_name = "sourcerepo"
        source.naming.format = "%Y%m%d_%H%M%S"
        source.naming.prefix = "pre_"
        source.naming.suffix = "_suf"
        source.naming.extension = ".jpg"
        source.image.format = "JPEG"
        source.image.quality = 80
        source.image.optimize = False
        source.ui.show_preview = False
        source.ui.preview_max_width = 1024
        source.ui.preview_max_height = 768
        source.ui.confirm_before_upload = False
        source.ui.auto_copy = False
        source.ui.show_notification = False
        source.ui.notification_duration = 5000
        source.ui.minimize_to_tray = False
        source.ui.start_minimized = True

        # 创建目标配置，使用默认值
        target = Config()

        # 创建对话框（用于访问方法）
        dialog = SettingsDialog(Config())
        qtbot.addWidget(dialog)

        # 复制配置值
        dialog._copy_config_values(source, target)

        # 断言目标对象的所有字段与源对象一致
        assert target.hotkey.key == source.hotkey.key
        assert target.hotkey.enabled == source.hotkey.enabled
        assert target.git.repo_path == source.git.repo_path
        assert target.git.target_folder == source.git.target_folder
        assert target.git.branch == source.git.branch
        assert target.git.auto_pull == source.git.auto_pull
        assert target.github.username == source.github.username
        assert target.github.repo_name == source.github.repo_name
        assert target.naming.format == source.naming.format
        assert target.naming.prefix == source.naming.prefix
        assert target.naming.suffix == source.naming.suffix
        assert target.naming.extension == source.naming.extension
        assert target.image.format == source.image.format
        assert target.image.quality == source.image.quality
        assert target.image.optimize == source.image.optimize
        assert target.ui.show_preview == source.ui.show_preview
        assert target.ui.preview_max_width == source.ui.preview_max_width
        assert target.ui.preview_max_height == source.ui.preview_max_height
        assert target.ui.confirm_before_upload == source.ui.confirm_before_upload
        assert target.ui.auto_copy == source.ui.auto_copy
        assert target.ui.show_notification == source.ui.show_notification
        assert target.ui.notification_duration == source.ui.notification_duration
        assert target.ui.minimize_to_tray == source.ui.minimize_to_tray
        assert target.ui.start_minimized == source.ui.start_minimized

    def test_restore_config(self, qtbot, tmp_path):
        """验证 _restore_config 正确恢复所有字段"""
        # 创建临时git仓库
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # 创建原始配置
        original = Config()
        original.hotkey.key = "ctrl+f9"
        original.hotkey.enabled = False
        original.git.repo_path = str(repo_path)
        original.git.target_folder = "my_images"
        original.git.branch = "release"
        original.git.auto_pull = True
        original.github.username = "originaluser"
        original.github.repo_name = "originalrepo"
        original.naming.format = "%Y%m%d_%H%M%S"
        original.naming.prefix = "pre_"
        original.naming.suffix = "_suf"
        original.naming.extension = ".jpg"
        original.image.format = "JPEG"
        original.image.quality = 80
        original.image.optimize = False
        original.ui.show_preview = False
        original.ui.preview_max_width = 1024
        original.ui.preview_max_height = 768
        original.ui.confirm_before_upload = False
        original.ui.auto_copy = False
        original.ui.show_notification = False
        original.ui.notification_duration = 5000
        original.ui.minimize_to_tray = False
        original.ui.start_minimized = True

        # 创建当前配置（将被修改）
        config = Config()
        config.git.repo_path = str(repo_path)  # 需要有效路径用于验证
        config.github.username = "temp"
        config.github.repo_name = "temp"

        # 创建对话框
        dialog = SettingsDialog(config)
        qtbot.addWidget(dialog)

        # 修改config的所有字段
        config.hotkey.key = "changed"
        config.hotkey.enabled = True
        config.git.target_folder = "changed"
        config.git.branch = "changed"
        config.git.auto_pull = False
        config.github.username = "changed"
        config.github.repo_name = "changed"
        config.naming.format = "changed"
        config.naming.prefix = "changed"
        config.naming.suffix = "changed"
        config.naming.extension = "changed"
        config.image.format = "PNG"
        config.image.quality = 50
        config.image.optimize = True
        config.ui.show_preview = True
        config.ui.preview_max_width = 100
        config.ui.preview_max_height = 100
        config.ui.auto_copy = True
        config.ui.show_notification = True
        config.ui.notification_duration = 1000
        config.ui.minimize_to_tray = True
        config.ui.start_minimized = False

        # 恢复配置
        dialog._restore_config(original)

        # 断言config的所有字段恢复到原始值
        assert config.hotkey.key == original.hotkey.key
        assert config.hotkey.enabled == original.hotkey.enabled
        assert config.git.repo_path == original.git.repo_path
        assert config.git.target_folder == original.git.target_folder
        assert config.git.branch == original.git.branch
        assert config.git.auto_pull == original.git.auto_pull
        assert config.github.username == original.github.username
        assert config.github.repo_name == original.github.repo_name
        assert config.naming.format == original.naming.format
        assert config.naming.prefix == original.naming.prefix
        assert config.naming.suffix == original.naming.suffix
        assert config.naming.extension == original.naming.extension
        assert config.image.format == original.image.format
        assert config.image.quality == original.image.quality
        assert config.image.optimize == original.image.optimize
        assert config.ui.show_preview == original.ui.show_preview
        assert config.ui.preview_max_width == original.ui.preview_max_width
        assert config.ui.preview_max_height == original.ui.preview_max_height
        assert config.ui.auto_copy == original.ui.auto_copy
        assert config.ui.show_notification == original.ui.show_notification
        assert config.ui.notification_duration == original.ui.notification_duration
        assert config.ui.minimize_to_tray == original.ui.minimize_to_tray
        assert config.ui.start_minimized == original.ui.start_minimized

    def test_ok_button_applies_settings(self, qtbot, tmp_path):
        """验证点击确定按钮应用设置（集成测试）"""
        # 创建临时git仓库
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # 创建配置
        config = Config()
        config.git.repo_path = str(repo_path)
        config.github.username = "testuser"
        config.github.repo_name = "testrepo"

        # 创建对话框
        dialog = SettingsDialog(config)
        qtbot.addWidget(dialog)

        # 修改UI字段
        dialog.hotkey_edit.setText("ctrl+alt+o")
        dialog.username_edit.setText("okuser")

        # 点击确定按钮
        ok_button = dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok)
        qtbot.mouseClick(ok_button, Qt.MouseButton.LeftButton)

        # 断言
        assert dialog.result() == SettingsDialog.DialogCode.Accepted
        assert config.hotkey.key == "ctrl+alt+o"
        assert config.github.username == "okuser"

    def test_cancel_button_restores_settings(self, qtbot, tmp_path):
        """验证点击取消按钮恢复设置（集成测试）"""
        # 创建临时git仓库
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # 创建配置
        config = Config()
        config.git.repo_path = str(repo_path)
        config.github.username = "testuser"
        config.github.repo_name = "testrepo"
        config.hotkey.key = "ctrl+shift+c"

        # 记录原始值
        original_key = config.hotkey.key
        original_username = config.github.username

        # 创建对话框
        dialog = SettingsDialog(config)
        qtbot.addWidget(dialog)

        # 修改UI字段
        dialog.hotkey_edit.setText("ctrl+alt+c")
        dialog.username_edit.setText("canceluser")

        # 点击取消按钮
        cancel_button = dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Cancel)
        qtbot.mouseClick(cancel_button, Qt.MouseButton.LeftButton)

        # 断言
        assert dialog.result() == SettingsDialog.DialogCode.Rejected
        assert config.hotkey.key == original_key
        assert config.github.username == original_username
