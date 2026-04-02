"""区域选择覆盖层窗口"""
from typing import Optional, Callable
from loguru import logger

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QScreen


class OverlayWindow(QWidget):
    """全屏透明覆盖层，用于选择截图区域"""

    # 信号：选择完成，传递区域坐标 (left, top, right, bottom)
    selection_completed = pyqtSignal(tuple)
    # 信号：选择取消
    selection_cancelled = pyqtSignal()

    def __init__(self, monitor_index: int = 1):
        """
        初始化覆盖层窗口

        Args:
            monitor_index: 显示器索引（1为第一个显示器）
        """
        super().__init__()

        self.monitor_index = monitor_index

        # 选择状态
        self.is_selecting = False
        self.start_pos: Optional[QPoint] = None
        self.current_pos: Optional[QPoint] = None
        self.selected_rect: Optional[QRect] = None

        # 回调函数（可选）
        self.on_selection_callback: Optional[Callable[[tuple[int, int, int, int]], None]] = None
        self.on_cancel_callback: Optional[Callable[[], None]] = None

        # 初始化UI
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        # 设置窗口透明
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # 设置鼠标追踪
        self.setMouseTracking(True)

        # 获取屏幕几何信息并设置窗口
        self._setup_screen_geometry()

        logger.debug(f"覆盖层窗口已初始化，显示器索引: {self.monitor_index}")

    def _setup_screen_geometry(self):
        """设置屏幕几何信息"""
        screens = QApplication.screens()

        if not screens:
            logger.error("未检测到显示器")
            return

        # monitor_index为0表示所有显示器
        if self.monitor_index == 0:
            # 使用虚拟屏幕（包含所有显示器）
            virtual_geometry = QApplication.primaryScreen().virtualGeometry()
            self.setGeometry(virtual_geometry)
            logger.debug(f"使用虚拟屏幕: {virtual_geometry}")
        else:
            # 使用指定显示器
            index = self.monitor_index - 1
            if index < len(screens):
                screen = screens[index]
                self.setGeometry(screen.geometry())
                logger.debug(f"使用显示器 {self.monitor_index}: {screen.geometry()}")
            else:
                # 回退到主显示器
                logger.warning(f"显示器索引 {self.monitor_index} 不存在，使用主显示器")
                primary_screen = QApplication.primaryScreen()
                self.setGeometry(primary_screen.geometry())

    def show_overlay(self):
        """显示覆盖层"""
        self._setup_screen_geometry()  # 重新设置屏幕几何信息
        self.show()
        self.activateWindow()
        self.setFocus()
        self.grabMouse()  # 捕获鼠标事件
        logger.info("覆盖层已显示")

    def hide_overlay(self):
        """隐藏覆盖层"""
        self.releaseMouse()
        self.hide()
        self.reset_state()
        logger.info("覆盖层已隐藏")

    def reset_state(self):
        """重置选择状态"""
        self.is_selecting = False
        self.start_pos = None
        self.current_pos = None
        self.selected_rect = None
        self.update()

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制半透明背景
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        # 绘制选择区域
        if self.is_selecting and self.start_pos and self.current_pos:
            selection_rect = QRect(self.start_pos, self.current_pos).normalized()

            # 清除选择区域的遮罩（显示清晰图像）
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            painter.fillRect(selection_rect, Qt.GlobalColor.transparent)

            # 恢复正常绘制模式
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # 绘制选择区域边框
            pen = QPen(QColor(30, 144, 255), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(selection_rect)

            # 绘制尺寸信息
            self._draw_selection_info(painter, selection_rect)

        # 绘制提示文本
        self._draw_hint_text(painter)

    def _draw_selection_info(self, painter: QPainter, rect: QRect):
        """绘制选择区域信息"""
        # 计算尺寸
        width = rect.width()
        height = rect.height()

        # 准备文本
        info_text = f"{width} × {height}"

        # 设置字体
        font = QFont("Arial", 12, QFont.Weight.Bold)
        painter.setFont(font)

        # 设置文本颜色和背景
        painter.setPen(QPen(Qt.GlobalColor.white))

        # 在选择区域上方绘制信息
        text_pos = rect.topLeft() + QPoint(5, -5)
        if text_pos.y() < 20:
            text_pos.setY(rect.bottom() + 20)

        # 绘制背景
        from PyQt6.QtGui import QFontMetrics
        font_metrics = QFontMetrics(font)
        text_rect = font_metrics.boundingRect(info_text)
        bg_rect = text_rect.translated(text_pos).adjusted(-5, -2, 5, 2)
        painter.fillRect(bg_rect, QColor(30, 144, 255, 200))

        # 绘制文本
        painter.drawText(text_pos, info_text)

    def _draw_hint_text(self, painter: QPainter):
        """绘制提示文本"""
        # 设置字体
        font = QFont("Arial", 14)
        painter.setFont(font)
        painter.setPen(QPen(Qt.GlobalColor.white))

        # 提示文本
        hint_text = "按住鼠标左键拖动选择区域 | ESC 取消"

        # 计算文本位置（居中显示）
        from PyQt6.QtGui import QFontMetrics
        font_metrics = QFontMetrics(font)
        text_width = font_metrics.horizontalAdvance(hint_text)
        text_height = font_metrics.height()

        x = (self.width() - text_width) // 2
        y = self.height() - 50

        # 绘制背景
        bg_rect = QRect(x - 10, y - text_height - 5, text_width + 20, text_height + 10)
        painter.fillRect(bg_rect, QColor(0, 0, 0, 150))

        # 绘制文本
        painter.drawText(x, y, hint_text)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_selecting = True
            self.start_pos = event.pos()
            self.current_pos = event.pos()
            self.update()
            logger.debug(f"开始选择: {self.start_pos}")

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.is_selecting:
            self.current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False

            if self.start_pos and self.current_pos:
                # 计算选择区域
                selection_rect = QRect(self.start_pos, self.current_pos).normalized()

                # 检查是否选择了有效区域
                if selection_rect.width() > 5 and selection_rect.height() > 5:
                    # 保存选择的区域
                    self.selected_rect = selection_rect

                    # 转换为桌面绝对坐标 (left, top, right, bottom)
                    # event.pos()/QRect 是窗口内坐标；mss 需要虚拟桌面坐标（多屏/负坐标）。
                    window_geo = self.geometry()
                    abs_left = window_geo.left() + selection_rect.left()
                    abs_top = window_geo.top() + selection_rect.top()
                    abs_right = window_geo.left() + selection_rect.right()
                    abs_bottom = window_geo.top() + selection_rect.bottom()

                    region = (
                        abs_left,
                        abs_top,
                        abs_right,
                        abs_bottom,
                    )

                    logger.info(f"选择完成: 区域={region}, 大小={selection_rect.width()}x{selection_rect.height()}")

                    # 发送信号
                    self.selection_completed.emit(region)

                    # 调用回调函数
                    if self.on_selection_callback:
                        self.on_selection_callback(region)
                else:
                    logger.debug("选择区域太小，忽略")

            self.update()

    def keyPressEvent(self, event):
        """键盘按下事件"""
        if event.key() == Qt.Key.Key_Escape:
            logger.info("用户取消选择")
            self.selection_cancelled.emit()

            if self.on_cancel_callback:
                self.on_cancel_callback()

            self.hide_overlay()

    def set_callbacks(self, on_selection: Optional[Callable[[tuple[int, int, int, int]], None]] = None,
                      on_cancel: Optional[Callable[[], None]] = None):
        """
        设置回调函数

        Args:
            on_selection: 选择完成回调
            on_cancel: 取消选择回调
        """
        self.on_selection_callback = on_selection
        self.on_cancel_callback = on_cancel