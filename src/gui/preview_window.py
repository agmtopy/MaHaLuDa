"""预览窗口"""
from pathlib import Path
from typing import Optional
from loguru import logger

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QImage, QFont

from PIL import Image

from src.core.config_manager import Config


class PreviewWindow(QDialog):
    """截图预览窗口"""

    def __init__(self, config: Config, parent=None):
        """
        初始化预览窗口

        Args:
            config: 配置对象
            parent: 父窗口
        """
        super().__init__(parent)

        self.config = config
        self.image: Optional[Image.Image] = None
        self.file_path: Optional[Path] = None
        self.github_url: Optional[str] = None

        # 用户决策
        self.user_confirmed = False

        # 初始化UI
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        self.setWindowTitle("截图预览 - MaHaLuDa")
        self.setModal(True)
        self.setMinimumSize(600, 400)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # 图像预览区域
        self._setup_image_preview(layout)

        # 信息显示区域
        self._setup_info_section(layout)

        # 按钮区域
        self._setup_buttons(layout)

        logger.debug("预览窗口已初始化")

    def _setup_image_preview(self, parent_layout: QVBoxLayout):
        """设置图像预览区域"""
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # 图像标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setText("等待截图...")
        self.image_label.setStyleSheet("background-color: #f0f0f0; color: #999;")

        scroll_area.setWidget(self.image_label)
        parent_layout.addWidget(scroll_area, stretch=1)

    def _setup_info_section(self, parent_layout: QVBoxLayout):
        """设置信息显示区域"""
        # 信息框架
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(5)

        # 文件信息
        self.file_info_label = QLabel("文件: 未生成")
        self.file_info_label.setWordWrap(True)
        info_layout.addWidget(self.file_info_label)

        # GitHub链接预览
        self.url_label = QLabel("GitHub链接: 未生成")
        self.url_label.setWordWrap(True)
        self.url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        info_layout.addWidget(self.url_label)

        parent_layout.addWidget(info_frame)

    def _setup_buttons(self, parent_layout: QVBoxLayout):
        """设置按钮区域"""
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # 重新截图按钮
        self.retake_button = QPushButton("重新截图")
        self.retake_button.setMinimumWidth(100)
        self.retake_button.clicked.connect(self._on_retake)
        button_layout.addWidget(self.retake_button)

        # 弹簧
        button_layout.addStretch()

        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_button)

        # 确认上传按钮
        self.confirm_button = QPushButton("确认上传")
        self.confirm_button.setMinimumWidth(120)
        self.confirm_button.setDefault(True)
        self.confirm_button.clicked.connect(self._on_confirm)
        button_layout.addWidget(self.confirm_button)

        parent_layout.addLayout(button_layout)

    def set_image(self, image: Image.Image):
        """
        设置预览图像

        Args:
            image: PIL图像对象
        """
        self.image = image

        # 转换PIL图像为QPixmap
        qimage = self._pil_to_qimage(image)
        pixmap = QPixmap.fromImage(qimage)

        # 缩放图像以适应预览窗口
        max_width = self.config.ui.preview_max_width
        max_height = self.config.ui.preview_max_height

        if pixmap.width() > max_width or pixmap.height() > max_height:
            pixmap = pixmap.scaled(
                max_width, max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

        self.image_label.setPixmap(pixmap)
        self.image_label.setStyleSheet("")  # 清除背景样式

        logger.debug(f"预览图像已设置: 原始大小={image.size}, 显示大小={pixmap.size()}")

    def set_file_info(self, file_path: Path, github_url: str):
        """
        设置文件信息

        Args:
            file_path: 文件路径
            github_url: GitHub URL
        """
        self.file_path = file_path
        self.github_url = github_url

        # 更新显示
        self.file_info_label.setText(f"文件: {file_path.name}")
        self.url_label.setText(f"GitHub链接: {github_url}")

        logger.debug(f"文件信息已设置: {file_path.name}")

    def _pil_to_qimage(self, image: Image.Image) -> QImage:
        """
        将PIL图像转换为QImage

        Args:
            image: PIL图像对象

        Returns:
            QImage: Qt图像对象
        """
        # 确保图像是RGB模式
        if image.mode == 'RGBA':
            r, g, b, a = image.split()
            image = Image.merge('RGB', (r, g, b))
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        # 转换为QImage
        data = image.tobytes('raw', 'RGB')
        qimage = QImage(data, image.width, image.height, image.width * 3, QImage.Format.Format_RGB888)

        return qimage

    def _on_confirm(self):
        """确认按钮点击"""
        self.user_confirmed = True
        logger.info("用户确认上传")
        self.accept()

    def _on_cancel(self):
        """取消按钮点击"""
        self.user_confirmed = False
        logger.info("用户取消上传")
        self.reject()

    def _on_retake(self):
        """重新截图按钮点击"""
        self.user_confirmed = False
        logger.info("用户选择重新截图")
        self.reject()

    def show_and_wait(self) -> bool:
        """
        显示窗口并等待用户决策

        Returns:
            bool: 用户是否确认上传
        """
        self.user_confirmed = False
        result = self.exec()
        return self.user_confirmed

    def clear(self):
        """清空预览"""
        self.image = None
        self.file_path = None
        self.github_url = None

        self.image_label.clear()
        self.image_label.setText("等待截图...")
        self.image_label.setStyleSheet("background-color: #f0f0f0; color: #999;")

        self.file_info_label.setText("文件: 未生成")
        self.url_label.setText("GitHub链接: 未生成")