"""剪贴板操作模块"""
import pyperclip
from loguru import logger


def copy_to_clipboard(text: str) -> bool:
    """
    复制文本到剪贴板

    Args:
        text: 要复制的文本

    Returns:
        bool: 是否成功
    """
    try:
        pyperclip.copy(text)
        logger.debug(f"已复制到剪贴板: {text[:50]}...")
        return True
    # pyperclip may raise various platform-specific exceptions (not just OSError)
    except Exception as e:
        logger.warning(f"复制到剪贴板失败 (非关键操作): {e}")
        return False


def get_from_clipboard() -> str:
    """
    从剪贴板获取文本

    Returns:
        str: 剪贴板中的文本，失败返回空字符串
    """
    try:
        text = pyperclip.paste()
        return text
    # pyperclip may raise various platform-specific exceptions (not just OSError)
    except Exception as e:
        logger.warning(f"从剪贴板获取失败 (非关键操作): {e}")
        return ""