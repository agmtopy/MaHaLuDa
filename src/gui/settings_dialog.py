"""设置对话框"""
from pathlib import Path
from typing import Optional
from loguru import logger

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QCheckBox, QComboBox, QGroupBox,
    QFormLayout, QDialogButtonBox, QFileDialog, QMessageBox,
    QTabWidget, QWidget
)
from PyQt6.QtCore import Qt

from src.core.config_manager import Config


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, config: Config, parent=None):
        """
        初始化设置对话框

        Args:
            config: 配置对象
            parent: 父窗口
        """
        super().__init__(parent)

        self.config = config
        self.original_config = Config.from_dict(config.to_dict())  # 备份原始配置

        # 初始化UI
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("设置 - MaHaLuDa")
        self.setMinimumSize(600, 500)

        # 主布局
        layout = QVBoxLayout(self)

        # 创建选项卡
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # 添加各个选项卡
        tab_widget.addTab(self._create_hotkey_tab(), "热键")
        tab_widget.addTab(self._create_git_tab(), "Git")
        tab_widget.addTab(self._create_github_tab(), "GitHub")
        tab_widget.addTab(self._create_naming_tab(), "命名")
        tab_widget.addTab(self._create_image_tab(), "图像")
        tab_widget.addTab(self._create_ui_tab(), "界面")

        # 对话框按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self._on_ok)
        button_box.rejected.connect(self._on_cancel)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)

        layout.addWidget(button_box)

    def _create_hotkey_tab(self) -> QWidget:
        """创建热键选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # 热键输入
        self.hotkey_edit = QLineEdit(self.config.hotkey.key)
        self.hotkey_edit.setPlaceholderText("例如: ctrl+shift+a")
        layout.addRow("热键:", self.hotkey_edit)

        # 启用热键
        self.hotkey_enabled_check = QCheckBox("启用热键")
        self.hotkey_enabled_check.setChecked(self.config.hotkey.enabled)
        layout.addRow(self.hotkey_enabled_check)

        # 提示
        hint_label = QLabel(
            "提示: 热键格式为 'ctrl+shift+a'、'alt+f1' 等。\n"
            "Windows系统可能需要管理员权限才能监听全局热键。"
        )
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addRow(hint_label)

        return widget

    def _create_git_tab(self) -> QWidget:
        """创建Git选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 表单布局
        form_layout = QFormLayout()

        # 仓库路径
        repo_layout = QHBoxLayout()
        self.repo_path_edit = QLineEdit(self.config.git.repo_path)
        self.repo_path_edit.setPlaceholderText("Git仓库的绝对路径")
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self._browse_repo_path)
        repo_layout.addWidget(self.repo_path_edit)
        repo_layout.addWidget(browse_button)
        form_layout.addRow("仓库路径:", repo_layout)

        # 目标文件夹
        self.target_folder_edit = QLineEdit(self.config.git.target_folder)
        self.target_folder_edit.setPlaceholderText("例如: screenshots")
        form_layout.addRow("目标文件夹:", self.target_folder_edit)

        # 分支
        self.branch_edit = QLineEdit(self.config.git.branch)
        form_layout.addRow("分支:", self.branch_edit)

        # 自动拉取
        self.auto_pull_check = QCheckBox("推送前自动拉取")
        self.auto_pull_check.setChecked(self.config.git.auto_pull)
        form_layout.addRow(self.auto_pull_check)

        layout.addLayout(form_layout)

        # 测试按钮
        test_button = QPushButton("测试Git连接")
        test_button.clicked.connect(self._test_git_connection)
        layout.addWidget(test_button)

        return widget

    def _create_github_tab(self) -> QWidget:
        """创建GitHub选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # 用户名
        self.username_edit = QLineEdit(self.config.github.username)
        self.username_edit.setPlaceholderText("GitHub用户名")
        layout.addRow("用户名:", self.username_edit)

        # 仓库名
        self.repo_name_edit = QLineEdit(self.config.github.repo_name)
        self.repo_name_edit.setPlaceholderText("仓库名称")
        layout.addRow("仓库名:", self.repo_name_edit)

        # 提示
        hint_label = QLabel(
            "提示: 这些信息用于生成GitHub Raw链接。\n"
            "确保仓库已正确配置并具有推送权限。"
        )
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addRow(hint_label)

        return widget

    def _create_naming_tab(self) -> QWidget:
        """创建命名选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # 时间格式
        self.format_edit = QLineEdit(self.config.naming.format)
        self.format_edit.setPlaceholderText("例如: %Y-%m-%d_%H-%M-%S")
        layout.addRow("时间格式:", self.format_edit)

        # 前缀
        self.prefix_edit = QLineEdit(self.config.naming.prefix)
        self.prefix_edit.setPlaceholderText("可选前缀")
        layout.addRow("前缀:", self.prefix_edit)

        # 后缀
        self.suffix_edit = QLineEdit(self.config.naming.suffix)
        self.suffix_edit.setPlaceholderText("可选后缀")
        layout.addRow("后缀:", self.suffix_edit)

        # 扩展名
        self.extension_edit = QLineEdit(self.config.naming.extension)
        self.extension_edit.setPlaceholderText("例如: .png")
        layout.addRow("扩展名:", self.extension_edit)

        return widget

    def _create_image_tab(self) -> QWidget:
        """创建图像选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # 格式
        self.format_combo = QComboBox()
        self.format_combo.addItems(['PNG', 'JPEG', 'WEBP', 'BMP'])
        self.format_combo.setCurrentText(self.config.image.format)
        layout.addRow("图像格式:", self.format_combo)

        # 质量
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(self.config.image.quality)
        layout.addRow("图像质量:", self.quality_spin)

        # 优化
        self.optimize_check = QCheckBox("优化图像")
        self.optimize_check.setChecked(self.config.image.optimize)
        layout.addRow(self.optimize_check)

        # 提示
        hint_label = QLabel(
            "提示: PNG格式支持透明度，适合截图。\n"
            "JPEG格式文件更小，但不支持透明度。\n"
            "质量参数仅对JPEG和WEBP格式有效。"
        )
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addRow(hint_label)

        return widget

    def _create_ui_tab(self) -> QWidget:
        """创建界面选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # 显示预览
        self.show_preview_check = QCheckBox("截图前显示预览")
        self.show_preview_check.setChecked(self.config.ui.show_preview)
        layout.addRow(self.show_preview_check)

        # 上传前确认
        self.confirm_before_upload_check = QCheckBox("上传前弹出确认框")
        self.confirm_before_upload_check.setChecked(getattr(self.config.ui, "confirm_before_upload", True))
        layout.addRow(self.confirm_before_upload_check)

        # 预览窗口最大尺寸
        preview_size_layout = QHBoxLayout()
        self.preview_width_spin = QSpinBox()
        self.preview_width_spin.setRange(400, 2000)
        self.preview_width_spin.setValue(self.config.ui.preview_max_width)
        preview_size_layout.addWidget(QLabel("宽度:"))
        preview_size_layout.addWidget(self.preview_width_spin)
        preview_size_layout.addWidget(QLabel("高度:"))
        self.preview_height_spin = QSpinBox()
        self.preview_height_spin.setRange(300, 1500)
        self.preview_height_spin.setValue(self.config.ui.preview_max_height)
        preview_size_layout.addWidget(self.preview_height_spin)
        layout.addRow("预览窗口最大尺寸:", preview_size_layout)

        # 自动复制
        self.auto_copy_check = QCheckBox("自动复制链接到剪贴板")
        self.auto_copy_check.setChecked(self.config.ui.auto_copy)
        layout.addRow(self.auto_copy_check)

        # 显示通知
        self.show_notification_check = QCheckBox("显示系统通知")
        self.show_notification_check.setChecked(self.config.ui.show_notification)
        layout.addRow(self.show_notification_check)

        # 通知持续时间
        self.notification_duration_spin = QSpinBox()
        self.notification_duration_spin.setRange(1000, 10000)
        self.notification_duration_spin.setSingleStep(500)
        self.notification_duration_spin.setValue(self.config.ui.notification_duration)
        self.notification_duration_spin.setSuffix(" 毫秒")
        layout.addRow("通知持续时间:", self.notification_duration_spin)

        # 最小化到托盘
        self.minimize_to_tray_check = QCheckBox("最小化到系统托盘")
        self.minimize_to_tray_check.setChecked(self.config.ui.minimize_to_tray)
        layout.addRow(self.minimize_to_tray_check)

        # 启动时最小化
        self.start_minimized_check = QCheckBox("启动时最小化")
        self.start_minimized_check.setChecked(self.config.ui.start_minimized)
        layout.addRow(self.start_minimized_check)

        return widget

    def _browse_repo_path(self):
        """浏览仓库路径"""
        current_path = self.repo_path_edit.text()
        if not current_path:
            current_path = str(Path.home())

        directory = QFileDialog.getExistingDirectory(
            self,
            "选择Git仓库目录",
            current_path
        )

        if directory:
            self.repo_path_edit.setText(directory)

    def _test_git_connection(self):
        """测试Git连接"""
        from src.core.git_operations import GitOperations

        repo_path = self.repo_path_edit.text()
        if not repo_path:
            QMessageBox.warning(self, "错误", "请先输入仓库路径")
            return

        repo_path = Path(repo_path)
        if not repo_path.exists():
            QMessageBox.warning(self, "错误", f"路径不存在: {repo_path}")
            return

        try:
            git_ops = GitOperations(repo_path)
            if git_ops.is_git_repo():
                branch = git_ops.get_current_branch()
                QMessageBox.information(
                    self,
                    "成功",
                    f"Git仓库验证成功！\n当前分支: {branch}"
                )
            else:
                QMessageBox.warning(self, "错误", "该路径不是有效的Git仓库")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"测试失败: {e}")

    def _collect_settings(self) -> Config:
        """收集当前UI中的设置到一个新的Config对象"""
        new_config = Config()

        # 热键配置
        new_config.hotkey.key = self.hotkey_edit.text().strip()
        new_config.hotkey.enabled = self.hotkey_enabled_check.isChecked()

        # Git配置
        new_config.git.repo_path = self.repo_path_edit.text().strip()
        new_config.git.target_folder = self.target_folder_edit.text().strip()
        new_config.git.branch = self.branch_edit.text().strip()
        new_config.git.auto_pull = self.auto_pull_check.isChecked()

        # GitHub配置
        new_config.github.username = self.username_edit.text().strip()
        new_config.github.repo_name = self.repo_name_edit.text().strip()

        # 命名配置
        new_config.naming.format = self.format_edit.text().strip()
        new_config.naming.prefix = self.prefix_edit.text().strip()
        new_config.naming.suffix = self.suffix_edit.text().strip()
        new_config.naming.extension = self.extension_edit.text().strip()

        # 图像配置
        new_config.image.format = self.format_combo.currentText()
        new_config.image.quality = self.quality_spin.value()
        new_config.image.optimize = self.optimize_check.isChecked()

        # UI配置
        new_config.ui.show_preview = self.show_preview_check.isChecked()
        new_config.ui.preview_max_width = self.preview_width_spin.value()
        new_config.ui.preview_max_height = self.preview_height_spin.value()
        new_config.ui.confirm_before_upload = self.confirm_before_upload_check.isChecked()
        new_config.ui.auto_copy = self.auto_copy_check.isChecked()
        new_config.ui.show_notification = self.show_notification_check.isChecked()
        new_config.ui.notification_duration = self.notification_duration_spin.value()
        new_config.ui.minimize_to_tray = self.minimize_to_tray_check.isChecked()
        new_config.ui.start_minimized = self.start_minimized_check.isChecked()

        return new_config

    def _copy_config_values(self, source: Config, target: Config):
        """将source的配置值复制到target"""
        # 热键配置
        target.hotkey.key = source.hotkey.key
        target.hotkey.enabled = source.hotkey.enabled

        # Git配置
        target.git.repo_path = source.git.repo_path
        target.git.target_folder = source.git.target_folder
        target.git.branch = source.git.branch
        target.git.auto_pull = source.git.auto_pull

        # GitHub配置
        target.github.username = source.github.username
        target.github.repo_name = source.github.repo_name

        # 命名配置
        target.naming.format = source.naming.format
        target.naming.prefix = source.naming.prefix
        target.naming.suffix = source.naming.suffix
        target.naming.extension = source.naming.extension

        # 图像配置
        target.image.format = source.image.format
        target.image.quality = source.image.quality
        target.image.optimize = source.image.optimize

        # UI配置
        target.ui.show_preview = source.ui.show_preview
        target.ui.preview_max_width = source.ui.preview_max_width
        target.ui.preview_max_height = source.ui.preview_max_height
        target.ui.confirm_before_upload = getattr(source.ui, "confirm_before_upload", True)
        target.ui.auto_copy = source.ui.auto_copy
        target.ui.show_notification = source.ui.show_notification
        target.ui.notification_duration = source.ui.notification_duration
        target.ui.minimize_to_tray = source.ui.minimize_to_tray
        target.ui.start_minimized = source.ui.start_minimized

    def _apply_settings(self):
        """应用设置"""
        # 先收集设置到临时对象，验证通过后再应用到实际配置
        new_config = self._collect_settings()

        # 验证配置
        is_valid, errors = new_config.validate()
        if not is_valid:
            QMessageBox.warning(self, "配置验证失败", "\n".join(errors))
            return False

        # 验证通过，复制到新配置到实际配置对象
        self._copy_config_values(new_config, self.config)

        # 保存配置
        if self.config.save():
            logger.info("配置已保存")
            return True
        else:
            QMessageBox.critical(self, "错误", "保存配置失败")
            return False

    def _on_ok(self):
        """确定按钮"""
        if self._apply_settings():
            self.accept()

    def _on_apply(self):
        """应用按钮"""
        self._apply_settings()

    def _on_cancel(self):
        """取消按钮"""
        # 恢复原始配置值（直接修改原对象的属性，而不是替换对象）
        self._restore_config(self.original_config)
        self.reject()

    def _restore_config(self, original: Config):
        """从原始配置恢复所有值"""
        # 热键配置
        self.config.hotkey.key = original.hotkey.key
        self.config.hotkey.enabled = original.hotkey.enabled

        # Git配置
        self.config.git.repo_path = original.git.repo_path
        self.config.git.target_folder = original.git.target_folder
        self.config.git.branch = original.git.branch
        self.config.git.auto_pull = original.git.auto_pull

        # GitHub配置
        self.config.github.username = original.github.username
        self.config.github.repo_name = original.github.repo_name

        # 命名配置
        self.config.naming.format = original.naming.format
        self.config.naming.prefix = original.naming.prefix
        self.config.naming.suffix = original.naming.suffix
        self.config.naming.extension = original.naming.extension

        # 图像配置
        self.config.image.format = original.image.format
        self.config.image.quality = original.image.quality
        self.config.image.optimize = original.image.optimize

        # UI配置
        self.config.ui.show_preview = original.ui.show_preview
        self.config.ui.preview_max_width = original.ui.preview_max_width
        self.config.ui.preview_max_height = original.ui.preview_max_height
        self.config.ui.auto_copy = original.ui.auto_copy
        self.config.ui.show_notification = original.ui.show_notification
        self.config.ui.notification_duration = original.ui.notification_duration
        self.config.ui.minimize_to_tray = original.ui.minimize_to_tray
        self.config.ui.start_minimized = original.ui.start_minimized