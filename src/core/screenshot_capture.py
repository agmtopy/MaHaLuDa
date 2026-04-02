"""截图捕获模块"""
import mss
from mss.base import MSSBase
from PIL import Image
from pathlib import Path
from typing import Optional
from loguru import logger


class ScreenshotCapture:
    """截图捕获类，支持多显示器和区域选择"""

    def __init__(self):
        """初始化截图捕获器"""
        self.sct: Optional[MSSBase] = None

    def __enter__(self):
        """上下文管理器入口"""
        self.sct = mss.mss()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if self.sct:
            self.sct.close()
        return False

    def get_monitors_info(self) -> list[dict]:
        """
        获取显示器信息

        Returns:
            list[dict]: 显示器信息列表，每个字典包含:
                - index: 显示器索引（0为所有显示器）
                - left: 左边界坐标
                - top: 上边界坐标
                - width: 宽度
                - height: 高度
        """
        if not self.sct:
            self.sct = mss.mss()

        monitors = []
        for i, monitor in enumerate(self.sct.monitors):
            monitors.append({
                'index': i,
                'left': monitor['left'],
                'top': monitor['top'],
                'width': monitor['width'],
                'height': monitor['height'],
            })

        logger.debug(f"检测到 {len(monitors) - 1} 个显示器")
        return monitors

    def capture_fullscreen(self, monitor_index: int = 1) -> Optional[Image.Image]:
        """
        捕获指定显示器的全屏截图

        Args:
            monitor_index: 显示器索引，1为第一个显示器

        Returns:
            Image.Image: PIL图像对象，失败返回None
        """
        try:
            if not self.sct:
                self.sct = mss.mss()

            # 获取显示器信息
            monitors = self.sct.monitors
            if monitor_index < 0 or monitor_index >= len(monitors):
                logger.error(f"无效的显示器索引: {monitor_index}")
                return None

            # 捕获截图
            monitor = monitors[monitor_index]
            screenshot = self.sct.grab(monitor)

            # 转换为PIL Image
            image = Image.frombytes('RGB', screenshot.size, screenshot.rgb)

            logger.info(f"已捕获显示器 {monitor_index} 的全屏截图: {image.size}")
            return image

        except Exception as e:
            logger.error(f"全屏截图失败: {e}")
            return None

    def capture_region(self, region: tuple[int, int, int, int]) -> Optional[Image.Image]:
        """
        捕获指定区域的截图

        Args:
            region: 截图区域 (left, top, right, bottom)

        Returns:
            Image.Image: PIL图像对象，失败返回None
        """
        try:
            if not self.sct:
                self.sct = mss.mss()

            left, top, right, bottom = region
            width = right - left
            height = bottom - top

            if width <= 0 or height <= 0:
                logger.error(f"无效的截图区域: {region}")
                return None

            # 构建mss需要的monitor字典
            monitor = {
                'left': left,
                'top': top,
                'width': width,
                'height': height,
            }

            # 捕获截图
            screenshot = self.sct.grab(monitor)

            # 转换为PIL Image
            image = Image.frombytes('RGB', screenshot.size, screenshot.rgb)

            logger.info(f"已捕获区域截图: 区域={region}, 大小={image.size}")
            return image

        except Exception as e:
            logger.error(f"区域截图失败: {e}")
            return None

    @staticmethod
    def save_screenshot(image: Image.Image, file_path: Path, format: str = 'PNG', quality: int = 95, optimize: bool = True) -> bool:
        """
        保存截图到文件

        Args:
            image: PIL图像对象
            file_path: 保存路径
            format: 图像格式（PNG, JPEG等）
            quality: 图像质量（1-100，仅对JPEG有效）
            optimize: 是否优化图像

        Returns:
            bool: 是否成功
        """
        try:
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存图像
            save_kwargs = {
                'format': format,
                'optimize': optimize,
            }

            if format.upper() == 'JPEG':
                save_kwargs['quality'] = quality

            image.save(file_path, **save_kwargs)

            logger.info(f"截图已保存: {file_path}")
            return True

        except Exception as e:
            logger.error(f"保存截图失败: {e}")
            return False