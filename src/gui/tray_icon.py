"""系统托盘图标"""
from typing import Optional
from loguru import logger

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, QObject

from src.core.config_manager import Config


class TrayIcon(QObject):
    """系统托盘图标管理器"""

    # 信号
    screenshot_requested = pyqtSignal()  # 请求截图
    settings_requested = pyqtSignal()  # 请求打开设置
    quit_requested = pyqtSignal()  # 请求退出

    def __init__(self, config: Config, icon_path: Optional[str] = None):
        """
        初始化系统托盘图标

        Args:
            config: 配置对象
            icon_path: 图标文件路径（可选）
        """
        super().__init__()

        self.config = config
        self.icon_path = icon_path

        # 系统托盘图标
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self.tray_menu: Optional[QMenu] = None

        # 初始化
        self._init_tray_icon()

    def _init_tray_icon(self):
        """初始化系统托盘图标"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("系统托盘不可用，托盘图标将不会显示")
            self.tray_icon = None
            self.tray_menu = None
            return

        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(parent=QApplication.instance())

        # 设置图标
        if self.icon_path:
            icon = QIcon(self.icon_path)
        else:
            # 使用默认图标（应用程序图标）
            icon = QApplication.style().standardIcon(
                QApplication.style().StandardPixmap.SP_ComputerIcon
            )

        self.tray_icon.setIcon(icon)

        # 创建右键菜单
        self._create_tray_menu()

        # 设置提示文本
        self.tray_icon.setToolTip("MaHaLuDa - 截图工具")

        # 点击行为
        self.tray_icon.activated.connect(self._on_activated)

        logger.debug("系统托盘图标已初始化")

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """托盘图标点击回调"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # 单击：默认发起截图（符合大多数截图工具习惯）
            self._on_screenshot()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # 双击：打开设置
            self._on_settings()

    def _create_tray_menu(self):
        """创建系统托盘菜单"""
        self.tray_menu = QMenu()

        # 截图动作
        screenshot_action = QAction("截图", self.tray_menu)
        screenshot_action.triggered.connect(self._on_screenshot)
        self.tray_menu.addAction(screenshot_action)

        # 分隔符
        self.tray_menu.addSeparator()

        # 设置动作
        settings_action = QAction("设置", self.tray_menu)
        settings_action.triggered.connect(self._on_settings)
        self.tray_menu.addAction(settings_action)

        # 分隔符
        self.tray_menu.addSeparator()

        # 退出动作
        quit_action = QAction("退出", self.tray_menu)
        quit_action.triggered.connect(self._on_quit)
        self.tray_menu.addAction(quit_action)

        # 设置菜单
        self.tray_icon.setContextMenu(self.tray_menu)

    def _on_screenshot(self):
        """截图菜单项点击"""
        logger.debug("托盘菜单: 截图")
        self.screenshot_requested.emit()

    def _on_settings(self):
        """设置菜单项点击"""
        logger.debug("托盘菜单: 设置")
        self.settings_requested.emit()

    def _on_quit(self):
        """退出菜单项点击"""
        logger.debug("托盘菜单: 退出")
        self.quit_requested.emit()

    def show(self):
        """显示系统托盘图标"""
        if self.tray_icon:
            self.tray_icon.show()
            logger.info("系统托盘图标已显示")

    def hide(self):
        """隐藏系统托盘图标"""
        if self.tray_icon:
            self.tray_icon.hide()
            logger.info("系统托盘图标已隐藏")

    def show_message(self, title: str, message: str,
                     icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
                     duration: Optional[int] = None):
        """
        显示系统通知

        Args:
            title: 通知标题
            message: 通知消息
            icon: 图标类型
            duration: 显示时长（毫秒），默认使用配置值
        """
        if not self.tray_icon:
            return

        if duration is None:
            duration = self.config.ui.notification_duration

        self.tray_icon.showMessage(title, message, icon, duration)
        logger.debug(f"显示通知: {title} - {message}")

    def show_success(self, title: str = "成功", message: str = ""):
        """显示成功通知"""
        self.show_message(title, message, QSystemTrayIcon.MessageIcon.Information)

    def show_error(self, title: str = "错误", message: str = ""):
        """显示错误通知"""
        self.show_message(title, message, QSystemTrayIcon.MessageIcon.Critical)

    def show_warning(self, title: str = "警告", message: str = ""):
        """显示警告通知"""
        self.show_message(title, message, QSystemTrayIcon.MessageIcon.Warning)

    def set_enabled(self, enabled: bool):
        """设置托盘图标是否可用"""
        if self.tray_icon:
            # 更新菜单项状态
            if self.tray_menu:
                for action in self.tray_menu.actions():
                    action.setEnabled(enabled)

    def cleanup(self):
        """清理资源"""
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
            self.tray_icon = None

        if self.tray_menu:
            self.tray_menu.deleteLater()
            self.tray_menu = None

        logger.debug("系统托盘资源已清理")