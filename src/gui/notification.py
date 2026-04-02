"""系统通知模块"""
from typing import Optional
from loguru import logger

from PyQt6.QtWidgets import QSystemTrayIcon
from PyQt6.QtCore import QObject, pyqtSignal


class NotificationManager(QObject):
    """系统通知管理器"""

    # 信号
    notification_shown = pyqtSignal(str, str)  # 标题, 消息

    def __init__(self, tray_icon: Optional[QSystemTrayIcon] = None, default_duration: int = 3000):
        """
        初始化通知管理器

        Args:
            tray_icon: 系统托盘图标对象
            default_duration: 默认通知持续时间（毫秒）
        """
        super().__init__()

        self.tray_icon = tray_icon
        self.default_duration = default_duration

        logger.debug("通知管理器已初始化")

    def set_tray_icon(self, tray_icon: QSystemTrayIcon):
        """
        设置系统托盘图标

        Args:
            tray_icon: 系统托盘图标对象
        """
        self.tray_icon = tray_icon

    def show(self, title: str, message: str,
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
            logger.warning("系统托盘图标未设置，无法显示通知")
            return

        if duration is None:
            duration = self.default_duration

        try:
            self.tray_icon.showMessage(title, message, icon, duration)
            logger.debug(f"显示通知: {title} - {message}")

            # 发送信号
            self.notification_shown.emit(title, message)

        except Exception as e:
            logger.error(f"显示通知失败: {e}")

    def show_success(self, title: str = "成功", message: str = ""):
        """
        显示成功通知

        Args:
            title: 通知标题
            message: 通知消息
        """
        self.show(title, message, QSystemTrayIcon.MessageIcon.Information)

    def show_error(self, title: str = "错误", message: str = ""):
        """
        显示错误通知

        Args:
            title: 通知标题
            message: 通知消息
        """
        self.show(title, message, QSystemTrayIcon.MessageIcon.Critical)

    def show_warning(self, title: str = "警告", message: str = ""):
        """
        显示警告通知

        Args:
            title: 通知标题
            message: 通知消息
        """
        self.show(title, message, QSystemTrayIcon.MessageIcon.Warning)

    def show_info(self, title: str = "信息", message: str = ""):
        """
        显示信息通知

        Args:
            title: 通知标题
            message: 通知消息
        """
        self.show(title, message, QSystemTrayIcon.MessageIcon.Information)


# 便捷函数
def show_notification(title: str, message: str,
                      icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
                      duration: int = 3000,
                      tray_icon: Optional[QSystemTrayIcon] = None):
    """
    显示系统通知的便捷函数

    Args:
        title: 通知标题
        message: 通知消息
        icon: 图标类型
        duration: 显示时长（毫秒）
        tray_icon: 系统托盘图标对象
    """
    manager = NotificationManager(tray_icon, duration)
    manager.show(title, message, icon, duration)