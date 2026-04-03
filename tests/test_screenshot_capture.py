"""截图捕获测试"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import tempfile

from src.core.screenshot_capture import ScreenshotCapture


class TestScreenshotCapture:
    """截图捕获测试类"""

    def test_context_manager(self):
        """测试上下文管理器"""
        with ScreenshotCapture() as capture:
            assert capture.sct is not None

    def test_get_monitors_info(self):
        """测试获取显示器信息"""
        with ScreenshotCapture() as capture:
            monitors = capture.get_monitors_info()

            assert isinstance(monitors, list)
            assert len(monitors) > 0

            # 第一个应该是虚拟屏幕（所有显示器）
            assert 'index' in monitors[0]
            assert 'width' in monitors[0]
            assert 'height' in monitors[0]

    @patch('mss.mss')
    def test_capture_fullscreen(self, mock_mss):
        """测试全屏截图"""
        # 模拟mss
        mock_sct = MagicMock()
        mock_mss.return_value.__enter__.return_value = mock_sct

        # 模拟截图结果
        mock_screenshot = MagicMock()
        mock_screenshot.size = (1920, 1080)
        mock_screenshot.rgb = b'\x00' * (1920 * 1080 * 3)
        mock_sct.grab.return_value = mock_screenshot

        # 模拟显示器信息
        mock_sct.monitors = [
            {'left': 0, 'top': 0, 'width': 1920, 'height': 1080},
            {'left': 0, 'top': 0, 'width': 1920, 'height': 1080},
        ]

        with ScreenshotCapture() as capture:
            image = capture.capture_fullscreen(monitor_index=1)

            assert image is not None
            assert isinstance(image, Image.Image)
            assert image.size == (1920, 1080)

    def test_capture_region(self):
        """测试区域截图"""
        with ScreenshotCapture() as capture:
            # 捕获一个小区域
            region = (0, 0, 100, 100)
            image = capture.capture_region(region)

            # 如果有显示器，应该能捕获
            if image is not None:
                assert isinstance(image, Image.Image)
                assert image.size == (100, 100)

    def test_capture_invalid_region(self):
        """测试无效区域"""
        with ScreenshotCapture() as capture:
            # 宽度为0的区域
            region = (0, 0, 0, 100)
            image = capture.capture_region(region)

            assert image is None

    def test_save_screenshot(self):
        """测试保存截图"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建一个测试图像
            image = Image.new('RGB', (100, 100), color='red')
            file_path = Path(temp_dir) / "test_screenshot.png"

            # 保存
            result = ScreenshotCapture.save_screenshot(image, file_path)

            assert result is True
            assert file_path.exists()

            # 验证图像
            with Image.open(file_path) as loaded_image:
                assert loaded_image.size == (100, 100)

    def test_save_screenshot_jpeg(self):
        """测试保存JPEG格式"""
        with tempfile.TemporaryDirectory() as temp_dir:
            image = Image.new('RGB', (100, 100), color='blue')
            file_path = Path(temp_dir) / "test.jpg"

            result = ScreenshotCapture.save_screenshot(
                image, file_path, format='JPEG', quality=90
            )

            assert result is True
            assert file_path.exists()

    def test_save_screenshot_create_directory(self):
        """测试保存时创建目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            image = Image.new('RGB', (50, 50), color='green')
            file_path = Path(temp_dir) / "subdir" / "test.png"

            result = ScreenshotCapture.save_screenshot(image, file_path)

            assert result is True
            assert file_path.exists()
            assert file_path.parent.exists()

    def test_save_screenshot_invalid_path(self):
        """测试保存到无效路径"""
        import os

        image = Image.new('RGB', (10, 10))
        if os.name == 'nt':
            file_path = Path("Z:/nonexistent_drive_1234567890/test.png")
        else:
            file_path = Path("/root/non_writable_dir/test.png")

        result = ScreenshotCapture.save_screenshot(image, file_path)

        assert result is False