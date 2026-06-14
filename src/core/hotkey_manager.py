"""全局热键管理模块 (Headless 版本)。"""
import time
import threading
from typing import Callable, Optional
import keyboard
from loguru import logger

from src.core.config_manager import HotkeyConfig


class HotkeyManager:
    """全局热键管理器"""

    DEBOUNCE_INTERVAL_S = 0.5

    def __init__(self, config: HotkeyConfig, callback: Optional[Callable[[], None]] = None):
        """
        初始化热键管理器

        Args:
            config: 热键配置对象
            callback: 热键触发时回调
        """
        self.config = config
        self.hotkey = config.key
        self.callback = callback
        self.is_registered = False
        self._last_triggered = 0.0

    def set_callback(self, callback: Callable[[], None]) -> None:
        """设置回调函数"""
        self.callback = callback

    def register(self) -> bool:
        """注册全局热键"""
        if not self.config.enabled:
            logger.info(f"热键未启用: {self.config.key}")
            return False

        if self.is_registered:
            logger.warning(f"热键已注册: {self.hotkey}")
            return True

        try:
            if hasattr(keyboard, 'is_hotkey_registered') and keyboard.is_hotkey_registered(self.hotkey):
                logger.warning(f"热键已被其他程序注册: {self.hotkey}")
                return False

            keyboard.add_hotkey(self.hotkey, self._on_hotkey_pressed)
            self.is_registered = True
            logger.info(f"热键已注册: {self.hotkey}")
            return True

        except Exception as e:
            logger.error(f"注册热键失败 {self.hotkey}: {e}")
            self.is_registered = False
            return False

    def unregister(self) -> None:
        """注销热键"""
        if not self.is_registered:
            return

        try:
            keyboard.remove_hotkey(self.hotkey)
            self.is_registered = False
            logger.info(f"热键已注销: {self.hotkey}")

        except Exception as e:
            logger.error(f"注销热键失败: {e}")
            self.is_registered = False

    def start(self) -> bool:
        """兼容旧接口：启动热键监听。"""
        return self.register()

    def stop(self) -> None:
        """兼容旧接口：停止热键监听。"""
        self.unregister()

    def update_hotkey(self, new_config: HotkeyConfig) -> bool:
        """更新热键配置并重新注册"""
        self.unregister()
        self.config = new_config
        self.hotkey = new_config.key
        return self.register()

    def _on_hotkey_pressed(self) -> None:
        """热键触发回调"""
        now = time.time()
        if now - self._last_triggered < self.DEBOUNCE_INTERVAL_S:
            logger.debug(f"热键防抖：忽略过快触发")
            return
        self._last_triggered = now
        logger.debug(f"热键触发: {self.hotkey}")
        if self.callback:
            threading.Thread(target=self._execute_callback, daemon=True).start()

    def _execute_callback(self) -> None:
        """执行回调函数（新线程）"""
        try:
            if self.callback:
                self.callback()
        except Exception as e:
            logger.error(f"执行热键回调失败: {e}")

    @staticmethod
    def check_hotkey_available(hotkey: str) -> bool:
        """检查热键是否可用"""
        try:
            keyboard.add_hotkey(hotkey, lambda: None)
            try:
                keyboard.remove_hotkey(hotkey)
            except Exception:
                pass
            return True
        except Exception:
            return False


