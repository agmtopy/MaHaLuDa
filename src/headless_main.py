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
from src.utils.dialogs import confirm_yes_no, confirm_yes_no_cancel


class HeadlessMainWindow:
    """Headless 版本的主窗口（使用 Tkinter）"""

    def __init__(self, config: Config, on_screenshot: callable, on_quit: callable):
        self.config = config
        self.on_screenshot = on_screenshot
        self.on_quit = on_quit
        self.root = None
        self._is_visible = False

    def create(self):
        """创建主窗口"""
        import tkinter as tk
        from tkinter import ttk

        self.root = tk.Tk()
        self.root.title("MaHaLuDa - 截图工具 (Headless)")
        self.root.geometry("450x350")

        # 设置窗口图标（如果有）
        try:
            # Windows 下可以设置任务栏图标
            pass
        except Exception:
            pass

        # 标题
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        title_label = ttk.Label(
            title_frame,
            text="MaHaLuDa",
            font=("Microsoft YaHei", 16, "bold")
        )
        title_label.pack()

        # 状态区域
        status_frame = ttk.LabelFrame(self.root, text="状态", padding="10")
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        # 热键状态
        hotkey_text = f"✓ {self.config.hotkey.key}" if self.config.hotkey.enabled else "✗ 未启用"
        ttk.Label(status_frame, text=f"全局热键: {hotkey_text}").pack(anchor=tk.W)

        # Git 状态
        git_status = "✓ 已配置" if self.config.git.repo_path else "✗ 未配置"
        ttk.Label(status_frame, text=f"Git仓库: {git_status}").pack(anchor=tk.W)

        # GitHub 状态
        github_status = f"✓ {self.config.github.username}/{self.config.github.repo_name}" if self.config.github.username else "✗ 未配置"
        ttk.Label(status_frame, text=f"GitHub: {github_status}").pack(anchor=tk.W)

        # 操作区域
        action_frame = ttk.Frame(self.root, padding="10")
        action_frame.pack(fill=tk.BOTH, expand=True)

        # 截图按钮
        screenshot_btn = ttk.Button(
            action_frame,
            text="截图 (Ctrl+Shift+A)",
            command=self._on_screenshot_click
        )
        screenshot_btn.pack(fill=tk.X, pady=5)

        # 提示
        tip_label = ttk.Label(
            action_frame,
            text="提示：关闭窗口将最小化到系统托盘\n使用托盘菜单可重新打开窗口或退出程序",
            font=("Microsoft YaHei", 9),
            foreground="gray"
        )
        tip_label.pack(pady=20)

        # 处理关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._is_visible = True

    def show(self):
        """显示窗口"""
        if self.root:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self._is_visible = True

    def hide(self):
        """隐藏窗口"""
        if self.root:
            self.root.withdraw()
            self._is_visible = False

    def toggle(self):
        """切换显示/隐藏"""
        if self._is_visible:
            self.hide()
        else:
            self.show()

    def _on_screenshot_click(self):
        """截图按钮点击"""
        if self.on_screenshot:
            threading.Thread(target=self.on_screenshot, daemon=True).start()

    def _on_close(self):
        """关闭按钮点击 - 最小化到托盘"""
        if self.config.ui.minimize_to_tray:
            self.hide()
            logger.info("主窗口已最小化到托盘")
        else:
            self._quit()

    def _quit(self):
        """退出程序"""
        if self.on_quit:
            self.on_quit()

    def run(self):
        """运行主循环"""
        if self.root:
            self.root.mainloop()

    def stop(self):
        """停止主循环"""
        if self.root:
            self.root.quit()


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
        self.main_window: Optional[HeadlessMainWindow] = None

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

        # 创建主窗口（如果配置启用）
        if getattr(self.config.ui, 'show_main_window_on_start', True):
            self._create_main_window()

        self._maybe_start_tray()

        logger.info("MaHaLuDa 无GUI版已启动。按热键触发系统截图。按 Ctrl+C 或托盘菜单退出。")

        # 运行主循环
        if self.main_window and self.main_window.root:
            # 有主窗口时，运行 Tkinter 主循环
            try:
                self.main_window.run()
            except KeyboardInterrupt:
                logger.info("退出中...")
            finally:
                self._cleanup()
        else:
            # 无主窗口时，使用简单的循环等待
            try:
                while not self._stop_event.is_set():
                    time.sleep(0.5)
            except KeyboardInterrupt:
                logger.info("退出中...")
            finally:
                self._cleanup()
        return 0

    def _create_main_window(self):
        """创建主窗口"""
        try:
            self.main_window = HeadlessMainWindow(
                config=self.config,
                on_screenshot=self.on_hotkey,
                on_quit=self._quit
            )
            self.main_window.create()
            logger.info("主窗口已创建")
        except Exception as e:
            logger.error(f"创建主窗口失败: {e}")
            self.main_window = None

    def _quit(self):
        """退出程序"""
        self._stop_event.set()
        if self.main_window:
            self.main_window.stop()

    def _cleanup(self):
        """清理资源"""
        self.hotkey.stop()
        self._stop_tray()

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

        def _on_tray_show_window(_icon, _item):
            """显示/隐藏主窗口"""
            if self.main_window:
                self.main_window.toggle()

        def _on_tray_open_config(_icon, _item):
            try:
                config_path = Config.get_config_file()
                os.startfile(str(config_path))  # type: ignore[attr-defined]
            except Exception as e:
                logger.error(f"打开配置文件失败: {e}")

        def _on_tray_quit(icon, _item):
            self._stop_event.set()
            if self.main_window:
                self.main_window.stop()
            try:
                icon.stop()
            except Exception:
                pass

        # 构建菜单
        menu_items = [
            pystray.MenuItem("显示主窗口", _on_tray_show_window, default=True),
            pystray.Menu.SEPARATOR,
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
                size_kb = file_size / 1024
                message = (
                    f"文件已保存\n"
                    f"路径: {file_path.name}\n"
                    f"大小: {size_kb:.1f} KB\n\n"
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
                    try:
                        file_path.unlink()
                        logger.info(f"已删除文件: {file_path}")
                    except Exception as e:
                        logger.warning(f"删除文件失败: {e}")
                    return
                if result is False:  # 否 - 仅本地保存，不执行 Git 操作
                    logger.info(f"文件已本地保存，跳过上传: {file_path}")
                    return
                # result is True - 继续执行 Git 操作

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

