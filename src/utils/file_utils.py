"""文件操作工具"""
from pathlib import Path
from typing import Optional
from loguru import logger


def ensure_dir(dir_path: Path) -> bool:
    """
    确保目录存在，不存在则创建

    Args:
        dir_path: 目录路径

    Returns:
        bool: 是否成功
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败 {dir_path}: {e}")
        return False


def get_file_size(file_path: Path) -> Optional[int]:
    """
    获取文件大小（字节）

    Args:
        file_path: 文件路径

    Returns:
        Optional[int]: 文件大小，失败返回None
    """
    try:
        return file_path.stat().st_size
    except Exception as e:
        logger.error(f"获取文件大小失败 {file_path}: {e}")
        return None


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        str: 格式化后的字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def safe_delete(file_path: Path) -> bool:
    """
    安全删除文件

    Args:
        file_path: 文件路径

    Returns:
        bool: 是否成功
    """
    try:
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"已删除文件: {file_path}")
        return True
    except Exception as e:
        logger.error(f"删除文件失败 {file_path}: {e}")
        return False


def copy_file(src: Path, dst: Path) -> bool:
    """
    复制文件

    Args:
        src: 源文件路径
        dst: 目标文件路径

    Returns:
        bool: 是否成功
    """
    try:
        import shutil
        # 确保目标目录存在
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        logger.debug(f"已复制文件: {src} -> {dst}")
        return True
    except Exception as e:
        logger.error(f"复制文件失败 {src} -> {dst}: {e}")
        return False