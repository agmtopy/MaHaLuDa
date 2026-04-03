"""主窗口模块"""
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from loguru import logger

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFrame,
    QGroupBox, QSystemTrayIcon, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QPixmap

from src.core.config_manager import Config


class ScreenshotHistoryItem:
    """截图历史记录项"""
    def __init__(self, filename: str, github_url: str, timestamp: datetime):
        self.filename = filename
        self.github_url = github_url
        self.timestamp = timestamp


class MainWindow(QMainWindow):
    """应用程序主窗口

    实现关闭时最小化到托盘的功能
    """

    # 信号
    screenshot_requested = pyqtSignal()  # 请求截图
    settings_requested = pyqtSignal()    # 请求设置
    quit_requested = pyqtSignal()        # 请求退出

    def __init__(self, config: Config, parent=None):
        """
        初始化主窗口

        Args:
            config: 配置对象
            parent: 父窗口
        """
        super().__init__(parent)

        self.config = config
        self.history: List[ScreenshotHistoryItem] = []

        # 初始化UI
        self._init_ui()

        logger.debug("主窗口已初始化")

    def _init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        self.setWindowTitle("MaHaLuDa - 截图工具")
        self.setMinimumSize(500, 450)
        self.resize(550, 500)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 标题
        title_label = QLabel("MaHaLuDa")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 状态区域
        self._setup_status_section(main_layout)

        # 历史记录区域
        self._setup_history_section(main_layout)

        # 操作按钮区域
        self._setup_action_buttons(main_layout)

    def _setup_status_section(self, parent_layout: QVBoxLayout):
        """设置状态区域"""
        status_group = QGroupBox("状态")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(8)

        # 热键状态
        hotkey_layout = QHBoxLayout()
        hotkey_layout.addWidget(QLabel("全局热键:"))
        self.hotkey_status_label = QLabel()
        hotkey_layout.addWidget(self.hotkey_status_label)
        hotkey_layout.addStretch()
        status_layout.addLayout(hotkey_layout)

        # Git 仓库状态
        git_layout = QHBoxLayout()
        git_layout.addWidget(QLabel("Git仓库:"))
        self.git_status_label = QLabel()
        git_layout.addWidget(self.git_status_label)
        git_layout.addStretch()
        status_layout.addLayout(git_layout)

        # GitHub 配置状态
        github_layout = QHBoxLayout()
        github_layout.addWidget(QLabel("GitHub配置:"))
        self.github_status_label = QLabel()
        github_layout.addWidget(self.github_status_label)
        github_layout.addStretch()
        status_layout.addLayout(github_layout)

        parent_layout.addWidget(status_group)

    def _setup_history_section(self, parent_layout: QVBoxLayout):
        """设置历史记录区域"""
        history_group = QGroupBox("最近截图")
        history_layout = QVBoxLayout(history_group)
        history_layout.setSpacing(8)

        # 历史列表
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(150)
        self.history_list.itemClicked.connect(self._on_history_item_clicked)
        history_layout.addWidget(self.history_list)

        # 链接显示
        link_layout = QHBoxLayout()
        link_layout.addWidget(QLabel("链接:"))
        self.link_label = QLabel("选择历史记录查看链接")
        self.link_label.setWordWrap(True)
        self.link_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.link_label.setStyleSheet("color: #0066cc;")
        link_layout.addWidget(self.link_label, stretch=1)

        # 复制链接按钮
        self.copy_link_button = QPushButton("复制")
        self.copy_link_button.setEnabled(False)
        self.copy_link_button.clicked.connect(self._on_copy_link)
        link_layout.addWidget(self.copy_link_button)

        history_layout.addLayout(link_layout)

        parent_layout.addWidget(history_group)

    def _setup_action_buttons(self, parent_layout: QVBoxLayout):
        """设置操作按钮区域"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # 截图按钮
        self.screenshot_button = QPushButton("截图 (Ctrl+Shift+A)")
        self.screenshot_button.setMinimumHeight(40)
        self.screenshot_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.screenshot_button.clicked.connect(self._on_screenshot)
        button_layout.addWidget(self.screenshot_button)

        # 设置按钮
        self.settings_button = QPushButton("设置")
        self.settings_button.setMinimumHeight(40)
        self.settings_button.clicked.connect(self._on_settings)
        button_layout.addWidget(self.settings_button)

        # 退出按钮
        self.quit_button = QPushButton("退出")
        self.quit_button.setMinimumHeight(40)
        self.quit_button.clicked.connect(self._on_quit)
        button_layout.addWidget(self.quit_button)

        parent_layout.addLayout(button_layout)

    def update_status(self, hotkey_active: bool = True):
        """
        更新状态显示

        Args:
            hotkey_active: 热键是否激活
        """
        # 热键状态
        if hotkey_active:
            self.hotkey_status_label.setText(f"✓ {self.config.hotkey.key}")
            self.hotkey_status_label.setStyleSheet("color: #4CAF50;")
        else:
            self.hotkey_status_label.setText("✗ 未激活")
            self.hotkey_status_label.setStyleSheet("color: #f44336;")

        # Git 状态
        if self.config.git.repo_path:
            repo_path = Path(self.config.git.repo_path)
            if repo_path.exists() and (repo_path / '.git').exists():
                self.git_status_label.setText(f"✓ {self.config.git.target_folder}")
                self.git_status_label.setStyleSheet("color: #4CAF50;")
            else:
                self.git_status_label.setText("✗ 路径无效")
                self.git_status_label.setStyleSheet("color: #f44336;")
        else:
            self.git_status_label.setText("✗ 未配置")
            self.git_status_label.setStyleSheet("color: #f44336;")

        # GitHub 状态
        if self.config.github.username and self.config.github.repo_name:
            self.github_status_label.setText(f"✓ {self.config.github.username}/{self.config.github.repo_name}")
            self.github_status_label.setStyleSheet("color: #4CAF50;")
        else:
            self.github_status_label.setText("✗ 未配置")
            self.github_status_label.setStyleSheet("color: #f44336;")

    def add_screenshot_history(self, filename: str, github_url: str):
        """
        添加截图历史记录

        Args:
            filename: 文件名
            github_url: GitHub 链接
        """
        item = ScreenshotHistoryItem(filename, github_url, datetime.now())
        self.history.insert(0, item)  # 插入到开头

        # 限制历史记录数量
        if len(self.history) > 20:
            self.history = self.history[:20]

        # 更新列表显示
        self._update_history_list()

        logger.debug(f"添加历史记录: {filename}")

    def _update_history_list(self):
        """更新历史列表显示"""
        self.history_list.clear()

        for item in self.history:
            display_text = f"{item.timestamp.strftime('%m-%d %H:%M')} - {item.filename}"
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.history_list.addItem(list_item)

    def _on_history_item_clicked(self, item: QListWidgetItem):
        """历史记录项点击"""
        screenshot_item: ScreenshotHistoryItem = item.data(Qt.ItemDataRole.UserRole)
        self.link_label.setText(screenshot_item.github_url)
        self.copy_link_button.setEnabled(True)
        self._current_url = screenshot_item.github_url

    def _on_copy_link(self):
        """复制链接按钮点击"""
        if hasattr(self, '_current_url'):
            from src.utils.clipboard import copy_to_clipboard
            copy_to_clipboard(self._current_url)
            self.link_label.setText(f"已复制: {self._current_url}")

    def _on_screenshot(self):
        """截图按钮点击"""
        logger.info("主窗口: 请求截图")
        self.screenshot_requested.emit()

    def _on_settings(self):
        """设置按钮点击"""
        logger.info("主窗口: 请求设置")
        self.settings_requested.emit()

    def _on_quit(self):
        """退出按钮点击"""
        logger.info("主窗口: 请求退出")
        self.quit_requested.emit()

    def closeEvent(self, event):
        """
        关闭事件处理

        如果配置了 minimize_to_tray，则隐藏窗口而不是退出
        """
        if self.config.ui.minimize_to_tray:
            event.ignore()
            self.hide()
            logger.info("主窗口关闭 - 最小化到托盘")

            # 显示托盘提示
            if self.parent() and hasattr(self.parent(), 'tray_icon'):
                tray_icon = self.parent().tray_icon
                if tray_icon and tray_icon.tray_icon:
                    tray_icon.show_message(
                        "MaHaLuDa",
                        "程序已最小化到系统托盘，单击托盘图标可重新显示窗口",
                        duration=2000
                    )
        else:
            event.accept()
            logger.info("主窗口关闭 - 退出程序")
            self.quit_requested.emit()

    def toggle_visibility(self):
        """切换窗口显示/隐藏"""
        if self.isVisible():
            self.hide()
            logger.debug("主窗口已隐藏")
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            logger.debug("主窗口已显示")

    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        # 更新状态显示
        self.update_status()
