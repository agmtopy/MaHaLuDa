"""日志管理模块"""
import sys
from pathlib import Path
from loguru import logger


def setup_logger(log_dir: Path, log_level: str = "INFO", rotation: str = "10 MB", retention: str = "7 days"):
    """
    配置日志系统

    Args:
        log_dir: 日志目录路径
        log_level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
        rotation: 日志轮转大小
        retention: 日志保留时间
    """
    # 移除默认处理器
    logger.remove()

    # 添加控制台输出（彩色）- 仅在有控制台时添加
    if sys.stdout is not None:
        logger.add(
            sys.stdout,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )

    # 添加文件输出
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_dir / "mahaluda.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=rotation,
        retention=retention,
        encoding="utf-8"
    )

    logger.info("日志系统初始化完成")
    return logger