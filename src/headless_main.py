"""MaHaLuDa 无GUI版本入口（不依赖 PyQt6）。

工作流：
1) 热键触发后调用系统截图（Win+Shift+S）
2) 轮询剪贴板，读取截图图片
3) 保存到 git repo → add/commit/push
4) 生成 GitHub Raw URL 并复制到剪贴板
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import threading
from pathlib import Path
from typing import Optional

import keyboard
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
from src.utils.dialogs import confirm_yes_no, confirm_yes_no_cancel
from src.utils.file_utils import format_file_size, safe_delete


# 常量定义
CLIPBOARD_POLL_TIMEOUT_S = 30.0  # 等待用户完成截图的最大时间
CLIPBOARD_POLL_INTERVAL_S = 0.2  # 剪贴板轮询间隔
MAIN_LOOP_INTERVAL_S = 0.5  # 主循环休眠间隔
SYSTEM_SCREENSHOT_HOTKEY = "windows+shift+s"  # Windows 系统截图快捷键
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
COMMIT_MESSAGE_TEMPLATE = "Add screenshot: {filename}"

# 托盘图标常量
TRAY_ICON_SIZE = 64
TRAY_ICON_CENTER = 32
TRAY_ICON_LENS_RADIUS = 13  # 图标中"镜头"圆圈的半径
TRAY_ICON_LENS_Y_START = 18
TRAY_ICON_LENS_Y_END = 46
TRAY_ICON_LENS_X_START = 18
TRAY_ICON_LENS_X_END = 46


def _grab_clipboard_image(timeout_s: float, poll_interval_s: float = CLIPBOARD_POLL_INTERVAL_S) -> Optional[Image.Image]:
    deadline = time.time() + timeout_s
    consecutive_failures = 0
    while time.time() < deadline:
        try:
            data = ImageGrab.grabclipboard()
            consecutive_failures = 0
        except Exception as e:
            consecutive_failures += 1
            if consecutive_failures >= 5:
                logger.warning(f"剪贴板连续 {consecutive_failures} 次读取失败: {e}")
            else:
                logger.debug(f"读取剪贴板失败（将重试）: {e}")
            data = None

        if isinstance(data, Image.Image):
            return data

        # 某些情况下 grabclipboard() 会返回文件路径列表
        if isinstance(data, list) and data:
            for p in data:
                try:
                    path = Path(p)
                    if path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS and path.exists():
                        img = Image.open(path)
                        img.load()  # 确保数据读入内存，释放文件句柄
                        return img
                except Exception:
                    continue

        time.sleep(poll_interval_s)

    return None


def _build_tray_image() -> Image.Image:
    # 简单生成一个 64x64 图标（避免依赖额外资源文件）
    img = Image.new("RGBA", (TRAY_ICON_SIZE, TRAY_ICON_SIZE), (32, 32, 32, 255))
    for y in range(TRAY_ICON_LENS_Y_START, TRAY_ICON_LENS_Y_END):
        for x in range(TRAY_ICON_LENS_X_START, TRAY_ICON_LENS_X_END):
            dx = x - TRAY_ICON_CENTER
            dy = y - TRAY_ICON_CENTER
            if dx * dx + dy * dy <= TRAY_ICON_LENS_RADIUS * TRAY_ICON_LENS_RADIUS:
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

        self.hotkey = HotkeyManager(self.config.hotkey)
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
                time.sleep(MAIN_LOOP_INTERVAL_S)
        except KeyboardInterrupt:
            logger.info("退出中...")
        finally:
            self._cleanup()

        return 0

    def _quit(self):
        """退出程序"""
        self._stop_event.set()

    def _cleanup(self):
        """清理资源"""
        self.hotkey.stop()
        self._stop_tray()
        # 等待正在进行的截图操作完成
        if self._run_lock.locked():
            logger.info("等待正在进行的截图操作完成...")
            self._run_lock.acquire()
            self._run_lock.release()

    def _maybe_start_tray(self) -> None:
        if not self.config.ui.minimize_to_tray:
            return

        try:
            import pystray
        except Exception as e:
            logger.warning(f"无法启用托盘（pystray 不可用）: {e}")
            return

        def _on_tray_screenshot(_icon, _item):
            threading.Thread(target=self.on_hotkey, daemon=True).start()

        def _on_tray_open_config(_icon, _item):
            try:
                config_path = Config.get_config_file()
                # 跨平台打开文件
                if sys.platform == "win32":
                    os.startfile(str(config_path))  # type: ignore[attr-defined]
                elif sys.platform == "darwin":
                    import subprocess
                    subprocess.run(["open", str(config_path)])
                else:
                    import subprocess
                    subprocess.run(["xdg-open", str(config_path)])
            except Exception as e:
                logger.error(f"打开配置文件失败: {e}")

        def _on_tray_quit(icon, _item):
            self._stop_event.set()
            try:
                icon.stop()
            except Exception:
                pass

        # 构建菜单
        menu_items = [
            pystray.MenuItem("截图", _on_tray_screenshot),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("打开配置", _on_tray_open_config),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", _on_tray_quit),
        ]

        menu = pystray.Menu(*menu_items)

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
                keyboard.send(SYSTEM_SCREENSHOT_HOTKEY)
            except Exception as e:
                logger.error(f"无法触发系统截图快捷键: {e}")
                return

            # 等待剪贴板出现图片
            img = _grab_clipboard_image(timeout_s=CLIPBOARD_POLL_TIMEOUT_S)
            if img is None:
                logger.error("超时：未从剪贴板获取到截图（可能取消了截图或剪贴板被拦截）")
                return

            try:
                # 确认点1：截图后确认
                if self.config.ui.headless.confirm_after_capture:
                    width, height = img.size
                    message = f"获取到截图\n尺寸: {width} x {height}\n\n是否继续保存？"
                    if not confirm_yes_no(
                        title="MaHaLuDa - 确认截图",
                        message=message,
                        use_native=self.config.ui.headless.use_native_dialog,
                    ):
                        logger.info("用户取消了截图保存")
                        return

                filename = generate_filename(self.config.naming)
                file_path = get_full_path(self.config.git.repo_path, self.config.git.target_folder, filename)
                file_path = ensure_unique_filename(file_path)

                if not ImageProcessor.save_with_config(img, file_path, self.config.image):
                    logger.error("保存截图失败")
                    return

                # 确认点2：上传前确认
                if self.config.ui.headless.confirm_before_upload:
                    file_size = file_path.stat().st_size if file_path.exists() else 0
                    size_str = format_file_size(file_size)
                    message = (
                        f"文件已保存\n"
                        f"路径: {file_path.name}\n"
                        f"大小: {size_str}\n\n"
                        f"点击'是'保存并上传到 Git\n"
                        f"点击'否'仅本地保存\n"
                        f"点击'取消'删除文件"
                    )
                    result = confirm_yes_no_cancel(
                        title="MaHaLuDa - 确认上传",
                        message=message,
                        use_native=self.config.ui.headless.use_native_dialog,
                    )
                    if result is None:  # 取消
                        safe_delete(file_path)
                        return
                    if result is False:  # 否 - 仅本地保存，不执行 Git 操作
                        logger.info(f"文件已本地保存，跳过上传: {file_path}")
                        return
                    # result is True - 继续执行 Git 操作

                git_ops = GitOperations(self.config.git.repo_path)

                if self.config.git.auto_pull:
                    git_ops.pull_from_remote(branch=self.config.git.branch)

                commit_message = COMMIT_MESSAGE_TEMPLATE.format(filename=file_path.name)
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
                img.close()

        finally:
            self._run_lock.release()


def main() -> int:
    parser = argparse.ArgumentParser(description="MaHaLuDa 无GUI截图工具")
    parser.add_argument("--config", "-c", type=Path, help="配置文件路径")
    args = parser.parse_args()
    return HeadlessMaHaLuDa(config_path=args.config).start()


if __name__ == "__main__":
    sys.exit(main())

