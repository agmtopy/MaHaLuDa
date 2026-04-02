"""图像处理模块"""
from pathlib import Path
from typing import Optional
from PIL import Image
from loguru import logger

from src.core.config_manager import ImageConfig


class ImageProcessor:
    """图像处理器，处理图像格式转换和质量调整"""

    @staticmethod
    def process_image(image: Image.Image, config: ImageConfig) -> Image.Image:
        """
        处理图像（转换格式、调整质量等）

        Args:
            image: PIL图像对象
            config: 图像配置

        Returns:
            Image.Image: 处理后的图像
        """
        try:
            # 根据配置的格式进行转换
            target_format = config.format.upper()

            # PNG格式：支持透明度
            if target_format == 'PNG':
                # 如果图像不是RGBA模式，转换为RGBA
                if image.mode != 'RGBA':
                    image = image.convert('RGBA')

            # JPEG格式：不支持透明度，需要转换为RGB
            elif target_format == 'JPEG':
                if image.mode == 'RGBA':
                    # 创建白色背景
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])  # 使用alpha通道作为mask
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')

            # 其他格式
            else:
                logger.warning(f"未知的图像格式: {target_format}，保持原始格式")
                if image.mode not in ['RGB', 'RGBA']:
                    image = image.convert('RGB')

            logger.debug(f"图像处理完成: 模式={image.mode}, 大小={image.size}")
            return image

        except Exception as e:
            logger.error(f"图像处理失败: {e}")
            return image

    @staticmethod
    def resize_for_preview(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
        """
        缩放图像以适应预览窗口

        Args:
            image: PIL图像对象
            max_width: 最大宽度
            max_height: 最大高度

        Returns:
            Image.Image: 缩放后的图像
        """
        try:
            width, height = image.size

            # 检查是否需要缩放
            if width <= max_width and height <= max_height:
                return image

            # 计算缩放比例
            ratio = min(max_width / width, max_height / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)

            # 缩放图像
            resized_image = image.resize(
                (new_width, new_height),
                Image.Resampling.LANCZOS
            )

            logger.debug(f"图像缩放完成: {width}x{height} -> {new_width}x{new_height}")
            return resized_image

        except Exception as e:
            logger.error(f"图像缩放失败: {e}")
            return image

    @staticmethod
    def save_with_config(image: Image.Image, file_path: Path, config: ImageConfig) -> bool:
        """
        根据配置保存图像

        Args:
            image: PIL图像对象
            file_path: 保存路径
            config: 图像配置

        Returns:
            bool: 是否成功
        """
        try:
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 处理图像
            processed_image = ImageProcessor.process_image(image, config)

            # 准备保存参数
            save_kwargs = {
                'format': config.format,
                'optimize': config.optimize,
            }

            # JPEG格式：设置质量
            if config.format.upper() == 'JPEG':
                save_kwargs['quality'] = config.quality

            # 保存图像
            processed_image.save(file_path, **save_kwargs)

            logger.info(f"图像已保存: {file_path}")
            return True

        except Exception as e:
            logger.error(f"保存图像失败: {e}")
            return False

    @staticmethod
    def get_image_info(image: Image.Image) -> dict:
        """
        获取图像信息

        Args:
            image: PIL图像对象

        Returns:
            dict: 图像信息
        """
        return {
            'width': image.width,
            'height': image.height,
            'mode': image.mode,
            'format': image.format if hasattr(image, 'format') else 'Unknown',
        }