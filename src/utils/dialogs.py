"""跨平台确认对话框工具（Windows 原生 / 命令行回退）"""

from __future__ import annotations

import os
import sys
from enum import IntEnum
from typing import Optional, Callable

from loguru import logger


class MB_RESULT(IntEnum):
    """MessageBox 返回值"""
    OK = 1
    CANCEL = 2
    ABORT = 3
    RETRY = 4
    IGNORE = 5
    YES = 6
    NO = 7
    TRYAGAIN = 10
    CONTINUE = 11


class MB_BUTTON(IntEnum):
    """MessageBox 按钮类型"""
    OK = 0
    OKCANCEL = 1
    ABORTRETRYIGNORE = 2
    YESNOCANCEL = 3
    YESNO = 4
    RETRYCANCEL = 5
    CANCELTRYAGAINCONTINUE = 6


class MB_ICON(IntEnum):
    """MessageBox 图标类型"""
    NONE = 0
    STOP = 16
    QUESTION = 32
    EXCLAMATION = 48
    INFORMATION = 64


# Windows 常量
MB_TOPMOST = 0x00040000  # 置顶显示
MB_SETFOREGROUND = 0x00010000  # 强制前台


def _is_windows() -> bool:
    """检查是否为 Windows 环境"""
    return os.name == "nt" and sys.platform == "win32"


def _show_windows_messagebox(
    title: str,
    message: str,
    button: MB_BUTTON = MB_BUTTON.OKCANCEL,
    icon: MB_ICON = MB_ICON.QUESTION,
    topmost: bool = True,
) -> MB_RESULT:
    """使用 Windows API 显示消息框

    Args:
        title: 标题
        message: 消息内容
        button: 按钮类型
        icon: 图标类型
        topmost: 是否置顶显示

    Returns:
        MB_RESULT: 用户点击的按钮
    """
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    # MessageBoxW(HWND hWnd, LPCWSTR lpText, LPCWSTR lpCaption, UINT uType)
    user32.MessageBoxW.argtypes = [
        wintypes.HWND,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.UINT,
    ]
    user32.MessageBoxW.restype = wintypes.INT

    flags = int(button) | int(icon)
    if topmost:
        flags |= MB_TOPMOST | MB_SETFOREGROUND

    result = user32.MessageBoxW(0, message, title, flags)
    return MB_RESULT(result)


def _fallback_input_dialog(
    title: str,
    message: str,
    button: MB_BUTTON = MB_BUTTON.OKCANCEL,
) -> MB_RESULT:
    """命令行回退对话框

    Args:
        title: 标题
        message: 消息内容
        button: 按钮类型（决定显示的选项）

    Returns:
        MB_RESULT: 用户选择的选项
    """
    print(f"\n{'=' * 50}")
    print(f"[{title}]")
    print(f"{'=' * 50}")
    print(message)
    print("-" * 50)

    # 根据按钮类型显示不同选项
    if button == MB_BUTTON.OKCANCEL:
        options = {"y": MB_RESULT.OK, "n": MB_RESULT.CANCEL}
        prompt = "[Y] 确定 / [N] 取消: "
    elif button == MB_BUTTON.YESNO:
        options = {"y": MB_RESULT.YES, "n": MB_RESULT.NO}
        prompt = "[Y] 是 / [N] 否: "
    elif button == MB_BUTTON.YESNOCANCEL:
        options = {"y": MB_RESULT.YES, "n": MB_RESULT.NO, "c": MB_RESULT.CANCEL}
        prompt = "[Y] 是 / [N] 否 / [C] 取消: "
    else:
        options = {"y": MB_RESULT.OK}
        prompt = "按回车继续: "

    while True:
        try:
            choice = input(prompt).strip().lower()
            if choice in options:
                return options[choice]
            if not choice and MB_RESULT.OK in options.values():
                return MB_RESULT.OK
            print("无效输入，请重试")
        except (EOFError, KeyboardInterrupt):
            return MB_RESULT.CANCEL


def show_messagebox(
    title: str,
    message: str,
    button: MB_BUTTON = MB_BUTTON.OKCANCEL,
    icon: MB_ICON = MB_ICON.QUESTION,
    use_native: bool = True,
    topmost: bool = True,
) -> MB_RESULT:
    """显示确认对话框

    Windows 环境下使用原生消息框，其他环境使用命令行回退。

    Args:
        title: 标题
        message: 消息内容
        button: 按钮类型，默认 OKCANCEL
        icon: 图标类型，默认 QUESTION
        use_native: 是否尝试使用原生对话框
        topmost: 是否置顶显示（仅 Windows）

    Returns:
        MB_RESULT: 用户点击的按钮
    """
    if use_native and _is_windows():
        try:
            return _show_windows_messagebox(title, message, button, icon, topmost)
        except Exception as e:
            logger.warning(f"Windows 消息框调用失败，使用命令行回退: {e}")

    return _fallback_input_dialog(title, message, button)


def confirm_yes_no(
    title: str,
    message: str,
    use_native: bool = True,
) -> bool:
    """简单的 是/否 确认

    Args:
        title: 标题
        message: 消息内容
        use_native: 是否使用原生对话框

    Returns:
        bool: 用户选择"是"返回 True
    """
    result = show_messagebox(
        title=title,
        message=message,
        button=MB_BUTTON.YESNO,
        icon=MB_ICON.QUESTION,
        use_native=use_native,
    )
    return result == MB_RESULT.YES


def confirm_yes_no_cancel(
    title: str,
    message: str,
    use_native: bool = True,
) -> Optional[bool]:
    """是/否/取消 三选一确认

    Args:
        title: 标题
        message: 消息内容
        use_native: 是否使用原生对话框

    Returns:
        bool: 选择"是"返回 True，选择"否"返回 False
        None: 选择"取消"
    """
    result = show_messagebox(
        title=title,
        message=message,
        button=MB_BUTTON.YESNOCANCEL,
        icon=MB_ICON.QUESTION,
        use_native=use_native,
    )
    if result == MB_RESULT.YES:
        return True
    if result == MB_RESULT.NO:
        return False
    return None


def confirm_ok_cancel(
    title: str,
    message: str,
    use_native: bool = True,
) -> bool:
    """确定/取消 确认

    Args:
        title: 标题
        message: 消息内容
        use_native: 是否使用原生对话框

    Returns:
        bool: 选择"确定"返回 True
    """
    result = show_messagebox(
        title=title,
        message=message,
        button=MB_BUTTON.OKCANCEL,
        icon=MB_ICON.INFORMATION,
        use_native=use_native,
    )
    return result == MB_RESULT.OK


def show_info(title: str, message: str, use_native: bool = True) -> None:
    """显示信息提示（仅确定按钮）

    Args:
        title: 标题
        message: 消息内容
        use_native: 是否使用原生对话框
    """
    show_messagebox(
        title=title,
        message=message,
        button=MB_BUTTON.OK,
        icon=MB_ICON.INFORMATION,
        use_native=use_native,
    )


def show_warning(title: str, message: str, use_native: bool = True) -> None:
    """显示警告提示

    Args:
        title: 标题
        message: 消息内容
        use_native: 是否使用原生对话框
    """
    show_messagebox(
        title=title,
        message=message,
        button=MB_BUTTON.OK,
        icon=MB_ICON.EXCLAMATION,
        use_native=use_native,
    )


def show_error(title: str, message: str, use_native: bool = True) -> None:
    """显示错误提示

    Args:
        title: 标题
        message: 消息内容
        use_native: 是否使用原生对话框
    """
    show_messagebox(
        title=title,
        message=message,
        button=MB_BUTTON.OK,
        icon=MB_ICON.STOP,
        use_native=use_native,
    )
