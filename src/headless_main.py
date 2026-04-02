"""MaHaLuDa 无GUI版本入口（不依赖 PyQt6）。

工作流：
1) 热键触发后调用系统截图（Win+Shift+S）
2) 轮询剪贴板，读取截图图片
3) 保存到 git repo → add/commit/push
4) 生成 GitHub Raw URL 并复制到剪贴板
"""

from __future__ import annotations

import os
import sys
import time
import threading
from pathlib import Path
from typing import Optional

from loguru import logger
from PIL import Image, ImageGrab

from src.core.config_manager import Config
from src.core.git_operations import GitOperations
from src.core.image_processor import ImageProcessor
from src.core.link_generator import LinkGenerator
from src.core.hotkey_manager import HotkeyManager
from src.utils.clipboard import copy_to_clipboard
from src.utils.logger import setup_logger
from src.utils.naming import ensure_unique_filename, generate_filename, get_full_path


def _grab_clipboard_image(timeout_s: float, poll_interval_s: float = 0.2) -> Optional[Image.Image]:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            data = ImageGrab.grabclipboard()
        except Exception as e:
            logger.debug(f"读取剪贴板失败（将重试）: {e}")
            data = None

        if isinstance(data, Image.Image):
            return data

        # 某些情况下 grabclipboard() 会返回文件路径列表
        if isinstance(data, list) and data:
            for p in data:
                try:
                    path = Path(p)
                    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"} and path.exists():
                        return Image.open(path)
                except Exception:
                    continue

        time.sleep(poll_interval_s)

    return None


def _build_tray_image() -> Image.Image:
    # 简单生成一个 64x64 图标（避免依赖额外资源文件）
    img = Image.new("RGBA", (64, 64), (32, 32, 32, 255))
    # 画一个浅色圆点作为“相机镜头”的感觉
    for y in range(18, 46):
        for x in range(18, 46):
            dx = x - 32
            dy = y - 32
            if dx * dx + dy * dy <= 13 * 13:
                img.putpixel((x, y), (230, 230, 230, 255))
    return img


class HeadlessMaHaLuDa:
    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config = Config.load(config_path)

        setup_logger(
            log_dir=Config.get_log_dir(),
            log_level=self.config.logging.level,
            rotation=self.config.logging.rotation,
            retention=self.config.logging.retention,
        )

        self.hotkey = HotkeyManager(self.config.hotkey.key)
        self.hotkey.set_callback(self.on_hotkey)

        self._run_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._tray_icon = None

    def start(self) -> int:
        valid, errors = self.config.validate()
        if not valid:
            logger.error("配置验证失败:\n" + "\n".join(f"- {e}" for e in errors))
            self.config.save()
            return 2

        if self.config.hotkey.enabled:
            if not self.hotkey.start():
                logger.error("热键注册失败（可能需要管理员权限）")
                return 3

        self._maybe_start_tray()

        logger.info("MaHaLuDa 无GUI版已启动。按热键触发系统截图。按 Ctrl+C 或托盘菜单退出。")
        try:
            while not self._stop_event.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("退出中...")
        finally:
            self.hotkey.stop()
            self._stop_tray()
        return 0

    def _maybe_start_tray(self) -> None:
        if not self.config.ui.minimize_to_tray:
            return

        try:
            import pystray
        except Exception as e:
            logger.warning(f"无法启用托盘（pystray 不可用）: {e}")
            return

        def _on_tray_screenshot(_icon, _item):
            # 与热键一致：触发同一套流程
            threading.Thread(target=self.on_hotkey, daemon=True).start()

        def _on_tray_open_config(_icon, _item):
            try:
                # headless_main 允许 --config 指定路径；这里优先打开标准配置位置
                config_path = Config.get_config_file()
                os.startfile(str(config_path))  # type: ignore[attr-defined]
            except Exception as e:
                logger.error(f"打开配置文件失败: {e}")

        def _on_tray_quit(icon, _item):
            self._stop_event.set()
            try:
                icon.stop()
            except Exception:
                pass

        menu = pystray.Menu(
            pystray.MenuItem("截图", _on_tray_screenshot),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("打开配置", _on_tray_open_config),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", _on_tray_quit),
        )

        try:
            self._tray_icon = pystray.Icon("MaHaLuDa", _build_tray_image(), "MaHaLuDa", menu)
            self._tray_icon.run_detached()
            logger.info("系统托盘图标（headless）已显示")
        except Exception as e:
            logger.warning(f"启动托盘失败: {e}")
            self._tray_icon = None

    def _stop_tray(self) -> None:
        icon = self._tray_icon
        self._tray_icon = None
        if not icon:
            return
        try:
            icon.stop()
        except Exception:
            pass

    def on_hotkey(self) -> None:
        if not self._run_lock.acquire(blocking=False):
            logger.warning("正在处理上一次截图，忽略本次触发")
            return

        try:
            # 触发系统截图 UI（等同 Win+Shift+S）
            logger.info("触发系统截图（Win+Shift+S），请完成选区…")
            try:
                import keyboard

                keyboard.send("windows+shift+s")
            except Exception as e:
                logger.error(f"无法触发系统截图快捷键: {e}")
                return

            # 等待剪贴板出现图片
            img = _grab_clipboard_image(timeout_s=30.0)
            if img is None:
                logger.error("超时：未从剪贴板获取到截图（可能取消了截图或剪贴板被拦截）")
                return

            filename = generate_filename(self.config.naming)
            file_path = get_full_path(self.config.git.repo_path, self.config.git.target_folder, filename)
            file_path = ensure_unique_filename(file_path)

            if not ImageProcessor.save_with_config(img, file_path, self.config.image):
                logger.error("保存截图失败")
                return

            git_ops = GitOperations(self.config.git.repo_path)

            if self.config.git.auto_pull:
                git_ops.pull_from_remote(branch=self.config.git.branch)

            commit_message = f"Add screenshot: {file_path.name}"
            if not git_ops.add_and_commit(file_path, commit_message):
                logger.error("Git 提交失败")
                return

            if not git_ops.push_to_remote(branch=self.config.git.branch):
                logger.error("Git 推送失败")
                return

            link_gen = LinkGenerator(self.config.github)
            relative_path = f"{self.config.git.target_folder}/{file_path.name}"
            url = link_gen.generate_raw_url(relative_path, branch=self.config.git.branch)

            if self.config.ui.auto_copy:
                copy_to_clipboard(url)

            logger.info(f"完成：{url}")

        finally:
            self._run_lock.release()


def main() -> int:
    config_path: Optional[Path] = None
    argv = sys.argv[1:]
    if len(argv) >= 2 and argv[0] in {"--config", "-c"}:
        config_path = Path(argv[1]).expanduser()
    return HeadlessMaHaLuDa(config_path=config_path).start()


if __name__ == "__main__":
    sys.exit(main())

