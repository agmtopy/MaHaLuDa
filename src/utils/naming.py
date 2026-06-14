"""文件名生成工具"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from loguru import logger

from src.core.config_manager import NamingConfig


def generate_filename(config: NamingConfig) -> str:
    """
    根据配置生成唯一的文件名

    Args:
        config: 命名配置对象

    Returns:
        str: 生成的文件名（包含扩展名）
    """
    # 生成时间戳
    timestamp = datetime.now().strftime(config.format)

    # 构建文件名
    parts = []

    if config.prefix:
        parts.append(config.prefix)

    parts.append(timestamp)

    if config.suffix:
        parts.append(config.suffix)

    # 组合文件名
    filename = '_'.join(parts)

    # 添加扩展名
    if not config.extension.startswith('.'):
        extension = '.' + config.extension
    else:
        extension = config.extension

    filename += extension

    logger.debug(f"生成文件名: {filename}")
    return filename


def get_full_path(repo_path: Path | str, target_folder: str, filename: str) -> Path:
    """
    获取完整的文件保存路径

    Args:
        repo_path: Git仓库路径
        target_folder: 目标文件夹名称
        filename: 文件名

    Returns:
        Path: 完整的文件路径
    """
    repo_path = Path(repo_path)

    # 构建目标文件夹路径
    # 注意：如果 target_folder 以 "/" 或 "\\" 开头，Path 会把它当成"绝对路径"，从而丢弃 repo_path。
    # 这会导致文件被保存到盘符根目录（例如 E:\\png\\...），并触发后续 Git 提交"文件不在仓库中"。
    safe_target_folder = (target_folder or "").lstrip("/\\")
    # 防止路径穿越
    if ".." in Path(safe_target_folder).parts:
        raise ValueError(f"target_folder 包含路径穿越: {target_folder}")
    folder_path = repo_path / safe_target_folder
    # 最终检查：解析后的路径必须在 repo 内
    resolved = folder_path.resolve()
    if not resolved.is_relative_to(repo_path.resolve()):
        raise ValueError(f"解析后的路径逃逸出仓库目录: {resolved}")

    # 构建完整文件路径
    file_path = folder_path / filename

    logger.debug(f"完整文件路径: {file_path}")
    return file_path


def ensure_unique_filename(file_path: Path) -> Path:
    if not file_path.exists():
        return file_path

    stem = file_path.stem
    suffix = file_path.suffix
    parent = file_path.parent

    for counter in range(1, 101):
        new_path = parent / f"{stem}_{counter:03d}{suffix}"
        if not new_path.exists():
            return new_path

    # 兜底：使用 UUID 避免碰撞
    unique_id = uuid.uuid4().hex[:8]
    return parent / f"{stem}_{unique_id}{suffix}"
