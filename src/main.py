"""MaHaLuDa主应用程序入口"""
import sys
from pathlib import Path
from typing import Optional
from loguru import logger

from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog, QSystemTrayIcon
from PyQt6.QtCore import Qt

from src.core.config_manager import Config
from src.core.hotkey_manager import HotkeyManager
from src.core.screenshot_capture import ScreenshotCapture
from src.core.git_operations import GitOperations
from src.core.link_generator import LinkGenerator
from src.core.image_processor import ImageProcessor
from src.gui.overlay_window import OverlayWindow
from src.gui.preview_window import PreviewWindow
from src.gui.tray_icon import TrayIcon
from src.gui.settings_dialog import SettingsDialog
from src.utils.logger import setup_logger
from src.utils.clipboard import copy_to_clipboard
from src.utils.naming import generate_filename, get_full_path, ensure_unique_filename
from PIL import Image


class MaHaLuDaApp:
    """MaHaLuDa应用程序主类"""

    def __init__(self):
        """初始化应用程序"""
        self.app: Optional[QApplication] = None
        self.config: Optional[Config] = None
        self.hotkey_manager: Optional[HotkeyManager] = None
        self.tray_icon: Optional[TrayIcon] = None
        self.overlay_window: Optional[OverlayWindow] = None
        self.preview_window: Optional[PreviewWindow] = None
        self.captured_image: Optional[Image.Image] = None

    def initialize(self) -> bool:
        """
        初始化应用程序

        Returns:
            bool: 是否成功初始化
        """
        try:
            # 创建Qt应用
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("MaHaLuDa")
            self.app.setApplicationVersion("1.0.0")
            # 让应用在没有窗口时也保持运行（托盘应用常见行为）
            self.app.setQuitOnLastWindowClosed(False)

            # 加载配置
            logger.info("加载配置...")
            self.config = Config.load()

            # 设置日志
            log_dir = Config.get_log_dir()
            setup_logger(
                log_dir=log_dir,
                log_level=self.config.logging.level,
                rotation=self.config.logging.rotation,
                retention=self.config.logging.retention
            )
            logger.info("日志系统已初始化")

            # 验证配置
            is_valid, errors = self.config.validate()
            if not is_valid:
                error_msg = "配置验证失败:\n\n" + "\n".join(errors)
                logger.error(error_msg)

                # 显示错误对话框
                if self.app:
                    QMessageBox.warning(
                        None,
                        "配置错误",
                        error_msg + "\n\n请编辑配置文件后重新启动应用程序。"
                    )

                # 保存默认配置以便用户编辑
                self.config.save()
                logger.info(f"已创建默认配置文件: {Config.get_config_file()}")

            # 初始化热键管理器
            logger.info("初始化热键管理器...")
            self.hotkey_manager = HotkeyManager(self.config.hotkey.key)
            self.hotkey_manager.set_callback(self._on_hotkey_pressed)

            # 注册热键
            if self.config.hotkey.enabled:
                if not self.hotkey_manager.start():
                    logger.warning("热键注册失败，可能需要管理员权限")
                    if self.app:
                        QMessageBox.warning(
                            None,
                            "热键注册失败",
                            f"无法注册热键 {self.config.hotkey.key}\n\n"
                            "可能需要以管理员身份运行应用程序。"
                        )
                else:
                    logger.info(f"热键已注册: {self.config.hotkey.key}")

            # 初始化系统托盘图标
            logger.info("初始化系统托盘图标...")
            if QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon = TrayIcon(self.config)
                self.tray_icon.screenshot_requested.connect(self._on_hotkey_pressed)
                self.tray_icon.settings_requested.connect(self._on_settings_requested)
                self.tray_icon.quit_requested.connect(self._on_quit_requested)
                self.tray_icon.show()
            else:
                logger.warning("系统托盘不可用：将不显示托盘图标")

            logger.info("应用程序初始化完成")
            return True

        except Exception as e:
            logger.error(f"应用程序初始化失败: {e}")
            return False

    def _on_hotkey_pressed(self):
        """热键按下回调"""
        try:
            logger.info("热键触发，开始截图流程")

            # 1. 显示区域选择覆盖层
            if not self.overlay_window:
                self.overlay_window = OverlayWindow()

            self.overlay_window.set_callbacks(
                on_selection=self._on_region_selected,
                on_cancel=self._on_selection_cancelled
            )
            self.overlay_window.show_overlay()

        except Exception as e:
            logger.error(f"处理热键时发生错误: {e}")

    def _on_region_selected(self, region: tuple[int, int, int, int]):
        """区域选择完成回调"""
        try:
            logger.info(f"区域已选择: {region}")

            # 隐藏覆盖层
            if self.overlay_window:
                self.overlay_window.hide_overlay()

            # 2. 捕获截图
            with ScreenshotCapture() as capture:
                self.captured_image = capture.capture_region(region)

            if not self.captured_image:
                logger.error("截图捕获失败")
                self.tray_icon.show_error("错误", "截图捕获失败")
                return

            # 3. 显示预览窗口
            logger.debug(f"show_preview: {self.config.ui.show_preview}")
            logger.debug(f"confirm_before_upload: {self.config.ui.confirm_before_upload}")

            if self.config.ui.show_preview:
                self._show_preview()
            else:
                # 直接保存和上传（可选：上传前确认）
                if self._confirm_upload_if_needed():
                    self._save_and_upload()
                else:
                    logger.info("用户取消上传")
                    self.captured_image = None

        except Exception as e:
            logger.error(f"处理区域选择时发生错误: {e}")

    def _confirm_upload_if_needed(self) -> bool:
        """在无需预览时，按配置弹出上传确认框"""
        logger.debug(f"_confirm_upload_if_needed called")

        if not self.app or not self.config:
            logger.warning("app or config is None, skipping confirmation")
            return True

        confirm_before_upload = getattr(self.config.ui, "confirm_before_upload", True)
        logger.debug(f"confirm_before_upload value: {confirm_before_upload}")

        if not confirm_before_upload:
            logger.info("confirm_before_upload is False, skipping confirmation dialog")
            return True

        logger.info("Showing confirmation dialog")
        result = QMessageBox.question(
            None,
            "确认上传",
            "是否确认上传这张截图？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        user_confirmed = result == QMessageBox.StandardButton.Yes
        logger.info(f"User response: {'Yes' if user_confirmed else 'No'}")
        return user_confirmed

    def _on_selection_cancelled(self):
        """选择取消回调"""
        logger.info("用户取消了区域选择")
        if self.overlay_window:
            self.overlay_window.hide_overlay()

    def _show_preview(self):
        """显示预览窗口"""
        try:
            if not self.preview_window:
                self.preview_window = PreviewWindow(self.config)

            # 生成文件名和路径
            filename = generate_filename(self.config.naming)
            file_path = get_full_path(
                self.config.git.repo_path,
                self.config.git.target_folder,
                filename
            )

            # 生成GitHub链接预览
            link_gen = LinkGenerator(self.config.github)
            relative_path = f"{self.config.git.target_folder}/{filename}"
            github_url = link_gen.generate_raw_url(relative_path, branch=self.config.git.branch)

            # 设置预览窗口
            self.preview_window.set_image(self.captured_image)
            self.preview_window.set_file_info(file_path, github_url)

            # 显示窗口并等待用户决策
            confirmed = self.preview_window.show_and_wait()

            if confirmed:
                self._save_and_upload()
            else:
                logger.info("用户取消了上传")
                self.captured_image = None

        except Exception as e:
            logger.error(f"显示预览窗口时发生错误: {e}")

    def _save_and_upload(self):
        """保存截图并上传到GitHub"""
        try:
            if not self.captured_image:
                logger.error("没有可保存的截图")
                return

            # 生成文件名
            filename = generate_filename(self.config.naming)
            file_path = get_full_path(
                self.config.git.repo_path,
                self.config.git.target_folder,
                filename
            )

            # 确保文件名唯一
            file_path = ensure_unique_filename(file_path)

            # 处理并保存图像
            save_result = ImageProcessor.save_with_config(
                self.captured_image,
                file_path,
                self.config.image
            )

            if not save_result:
                logger.error("保存截图失败")
                if self.tray_icon:
                    self.tray_icon.show_error("错误", "保存截图失败")
                return

            logger.info(f"截图已保存: {file_path}")

            # Git操作
            git_ops = GitOperations(self.config.git.repo_path)

            # 可选：推送前拉取
            if self.config.git.auto_pull:
                logger.info("自动拉取远程更改...")
                git_ops.pull_from_remote(branch=self.config.git.branch)

            # 添加并提交
            commit_message = f"Add screenshot: {filename}"
            commit_result = git_ops.add_and_commit(file_path, commit_message)

            if not commit_result:
                logger.error("Git提交失败")
                if self.tray_icon:
                    self.tray_icon.show_error("错误", "Git提交失败")
                return

            # 推送到远程
            push_result = git_ops.push_to_remote(branch=self.config.git.branch)

            if not push_result:
                logger.error("Git推送失败")
                if self.tray_icon:
                    self.tray_icon.show_error("错误", "Git推送失败")
                return

            # 生成GitHub链接
            link_gen = LinkGenerator(self.config.github)
            relative_path = f"{self.config.git.target_folder}/{file_path.name}"
            github_url = link_gen.generate_raw_url(relative_path, branch=self.config.git.branch)

            # 复制链接到剪贴板
            if self.config.ui.auto_copy:
                copy_to_clipboard(github_url)
                logger.info(f"链接已复制到剪贴板: {github_url}")

            # 显示成功通知
            if self.config.ui.show_notification and self.tray_icon:
                self.tray_icon.show_success(
                    "截图上传成功",
                    f"链接已复制到剪贴板\n{github_url}"
                )

            # 清理
            self.captured_image = None

        except Exception as e:
            logger.error(f"保存和上传时发生错误: {e}")
            if self.tray_icon:
                self.tray_icon.show_error("错误", f"上传失败: {e}")

    def _on_settings_requested(self):
        """设置请求回调"""
        try:
            dialog = SettingsDialog(self.config)
            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                # 重新注册热键
                if self.hotkey_manager:
                    self.hotkey_manager.update_hotkey(self.config.hotkey.key)
                    self.hotkey_manager.start()

                logger.info("配置已更新")

        except Exception as e:
            logger.error(f"打开设置对话框时发生错误: {e}")

    def _on_quit_requested(self):
        """退出请求回调"""
        if self.app:
            self.app.quit()

    def run(self) -> int:
        """
        运行应用程序

        Returns:
            int: 退出代码
        """
        try:
            if not self.app:
                logger.error("应用程序未初始化")
                return 1

            logger.info("启动应用程序主循环")
            return self.app.exec()

        except Exception as e:
            logger.error(f"应用程序运行错误: {e}")
            return 1

    def cleanup(self):
        """清理资源"""
        try:
            logger.info("清理应用程序资源...")

            # 注销热键
            if self.hotkey_manager:
                self.hotkey_manager.stop()

            # 清理系统托盘
            if self.tray_icon:
                self.tray_icon.cleanup()

            # 清理窗口
            if self.overlay_window:
                self.overlay_window.close()

            if self.preview_window:
                self.preview_window.close()

            logger.info("资源清理完成")

        except Exception as e:
            logger.error(f"清理资源时发生错误: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.cleanup()
        return False


def main():
    """主函数"""
    # 创建应用程序实例
    with MaHaLuDaApp() as app:
        # 初始化
        if not app.initialize():
            return 1

        # 运行
        return app.run()


if __name__ == "__main__":
    sys.exit(main())