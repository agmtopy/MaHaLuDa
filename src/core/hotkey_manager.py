"""全局热键管理模块"""
import threading
from typing import Callable, Optional
import keyboard
from loguru import logger


class HotkeyManager:
    """全局热键管理器"""

    def __init__(self, hotkey: str = "ctrl+shift+a", callback: Optional[Callable[[], None]] = None):
        """
        初始化热键管理器

        Args:
            hotkey: 热键组合 (如 "ctrl+shift+a")
            callback: 热键触发时的回调函数
        """
        self.hotkey = hotkey
        self.callback = callback
        self.is_registered = False

    def set_callback(self, callback: Callable[[], None]) -> None:
        """
        设置回调函数

        Args:
            callback: 回调函数
        """
        self.callback = callback

    def start(self) -> bool:
        """
        注册全局热键

        Returns:
            bool: 是否成功注册
        """
        if self.is_registered:
            logger.warning(f"热键已注册: {self.hotkey}")
            return True

        try:
            keyboard.add_hotkey(self.hotkey, self._on_hotkey_triggered)
            self.is_registered = True
            logger.info(f"热键已注册: {self.hotkey}")
            return True

        except Exception as e:
            logger.error(f"注册热键失败 {self.hotkey}: {e}")
            return False

    def stop(self) -> None:
        """注销热键"""
        if not self.is_registered:
            return

        try:
            keyboard.remove_hotkey(self.hotkey)
            self.is_registered = False
            logger.info(f"热键已注销: {self.hotkey}")

        except Exception as e:
            logger.error(f"注销热键失败: {e}")

    def update_hotkey(self, new_hotkey: str) -> bool:
        """
        更新热键

        Args:
            new_hotkey: 新的热键组合

        Returns:
            bool: 是否成功更新
        """
        # 先注销旧热键
        self.stop()

        # 更新热键
        old_hotkey = self.hotkey
        self.hotkey = new_hotkey

        # 重新注册
        if self.start():
            logger.info(f"热键已更新: {old_hotkey} -> {new_hotkey}")
            return True
        else:
            # 如果注册失败，恢复旧热键
            logger.error(f"注册新热键失败，恢复旧热键: {old_hotkey}")
            self.hotkey = old_hotkey
            self.start()
            return False

    def _on_hotkey_triggered(self) -> None:
        """热键触发时的处理函数"""
        logger.debug(f"热键触发: {self.hotkey}")

        if self.callback:
            # 在新线程中执行回调，避免阻塞热键监听
            threading.Thread(target=self._execute_callback, daemon=True).start()

    def _execute_callback(self) -> None:
        """执行回调函数"""
        try:
            if self.callback:
                self.callback()
        except Exception as e:
            logger.error(f"执行热键回调失败: {e}")

    @staticmethod
    def check_hotkey_available(hotkey: str) -> bool:
        """
        检查热键是否可用

        Args:
            hotkey: 热键组合

        Returns:
            bool: 热键是否可用
        """
        try:
            # 尝试注册并立即注销
            keyboard.add_hotkey(hotkey, lambda: None)
            keyboard.remove_hotkey(hotkey)
            return True
        except Exception:
            return False

    def __del__(self):
        """析构函数，确保注销热键"""
        self.stop()