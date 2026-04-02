"""配置管理模块"""
import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import yaml
from loguru import logger


@dataclass
class HotkeyConfig:
    """热键配置"""
    key: str = "ctrl+shift+a"
    enabled: bool = True


@dataclass
class GitConfig:
    """Git配置"""
    repo_path: str = ""
    target_folder: str = "screenshots"
    branch: str = "main"
    auto_pull: bool = False


@dataclass
class GitHubConfig:
    """GitHub配置"""
    username: str = ""
    repo_name: str = ""


@dataclass
class NamingConfig:
    """命名配置"""
    format: str = "%Y-%m-%d_%H-%M-%S"
    prefix: str = ""
    suffix: str = ""
    extension: str = ".png"


@dataclass
class ImageConfig:
    """图片配置"""
    format: str = "PNG"
    quality: int = 95
    optimize: bool = True


@dataclass
class HeadlessUIConfig:
    """Headless 版本专用 UI 配置"""
    confirm_after_capture: bool = True  # 截图后确认
    confirm_before_upload: bool = True  # 上传前确认
    use_native_dialog: bool = True  # 使用 Windows 原生对话框


@dataclass
class UIConfig:
    """界面配置"""
    show_preview: bool = True
    preview_max_width: int = 800
    preview_max_height: int = 600
    confirm_before_upload: bool = True
    auto_copy: bool = True
    show_notification: bool = True
    notification_duration: int = 3000
    minimize_to_tray: bool = True
    start_minimized: bool = False
    headless: HeadlessUIConfig = field(default_factory=HeadlessUIConfig)


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    rotation: str = "10 MB"
    retention: str = "7 days"


@dataclass
class Config:
    """应用配置"""
    hotkey: HotkeyConfig = field(default_factory=HotkeyConfig)
    git: GitConfig = field(default_factory=GitConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    naming: NamingConfig = field(default_factory=NamingConfig)
    image: ImageConfig = field(default_factory=ImageConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def get_config_dir(cls) -> Path:
        """获取配置文件目录"""
        # Windows: %LOCALAPPDATA%/MaHaLuDa
        if os.name == 'nt':
            local_app_data = os.getenv('LOCALAPPDATA', '')
            if local_app_data:
                return Path(local_app_data) / "MaHaLuDa"

        # 其他平台: ~/.mahaluda
        return Path.home() / ".mahaluda"

    @classmethod
    def get_config_file(cls) -> Path:
        """获取配置文件路径"""
        return cls.get_config_dir() / "config.yaml"

    @classmethod
    def get_log_dir(cls) -> Path:
        """获取日志目录"""
        return cls.get_config_dir() / "logs"

    @classmethod
    def get_template_config_file(cls) -> Optional[Path]:
        """
        获取配置模板文件路径（优先用于首次启动时生成本地配置）

        查找顺序：
        1) 打包后：exe 同级的 config/config.yaml
        2) 源码运行：项目根目录的 config/config.yaml
        """
        # PyInstaller one-dir/one-file：sys.executable 指向 exe
        exe_dir = Path(sys.executable).resolve().parent
        for candidate in (
            exe_dir / "config" / "config.yaml",
            exe_dir / "_internal" / "config" / "config.yaml",
        ):
            if candidate.exists():
                return candidate

        # 源码运行：.../src/core/config_manager.py -> 项目根目录在 parents[2]
        try:
            repo_root = Path(__file__).resolve().parents[2]
            candidate = repo_root / "config" / "config.yaml"
            if candidate.exists():
                return candidate
        except Exception:
            pass

        return None

    @classmethod
    def _load_yaml_dict(cls, path: Path) -> Optional[dict]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else None
        except Exception as e:
            logger.error(f"加载YAML失败: {path} - {e}")
            return None

    @classmethod
    def _merge_dict_prefer_non_empty(cls, base: dict, override: dict) -> dict:
        """
        合并两个 dict（override 覆盖 base），但当 override 的值为空（''/None）时不覆盖。
        支持递归合并嵌套 dict。
        """
        merged: dict = dict(base)
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(merged.get(k), dict):
                merged[k] = cls._merge_dict_prefer_non_empty(merged[k], v)  # type: ignore[arg-type]
                continue

            if v is None:
                continue
            if isinstance(v, str) and v.strip() == "":
                continue

            merged[k] = v
        return merged

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'Config':
        """
        从YAML文件加载配置

        Args:
            config_path: 配置文件路径，默认使用标准路径

        Returns:
            Config: 配置对象
        """
        if config_path is None:
            config_path = cls.get_config_file()

        # 如果配置文件不存在，创建默认配置
        if not config_path.exists():
            template_path = cls.get_template_config_file()
            if template_path:
                logger.info(f"配置文件不存在，使用模板创建: {config_path} (模板: {template_path})")
                data = cls._load_yaml_dict(template_path)
                config = cls.from_dict(data or {})
                config.save(config_path)
                return config

            logger.info(f"配置文件不存在，创建默认配置: {config_path}")
            config = cls()
            config.save(config_path)
            return config

        try:
            data = cls._load_yaml_dict(config_path)

            if data is None:
                logger.warning("配置文件为空，使用默认配置")
                return cls()

            # 如果本地配置缺少关键字段，尝试用模板补全（用户可能只修改了仓库里的 config/config.yaml）
            template_path = cls.get_template_config_file()
            if template_path:
                template_data = cls._load_yaml_dict(template_path) or {}
                # 模板作为基底，本地配置覆盖模板；但本地的空值不应覆盖模板的有效值
                merged = cls._merge_dict_prefer_non_empty(template_data, data)
                config = cls.from_dict(merged)
                is_valid, _ = config.validate()
                if is_valid:
                    logger.info(f"已加载配置文件: {config_path} (已使用模板补全: {template_path})")
                    # 将补全后的配置写回本地，方便后续直接读取
                    config.save(config_path)
                    return config

            config = cls.from_dict(data)
            logger.info(f"已加载配置文件: {config_path}")
            return config

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return cls()

    def save(self, config_path: Optional[Path] = None) -> bool:
        """
        保存配置到YAML文件

        Args:
            config_path: 配置文件路径，默认使用标准路径

        Returns:
            bool: 是否成功
        """
        if config_path is None:
            config_path = self.get_config_file()

        try:
            # 确保目录存在
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # 转换为字典
            data = self.to_dict()

            # 写入文件
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            logger.info(f"配置已保存: {config_path}")
            return True

        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'hotkey': {
                'key': self.hotkey.key,
                'enabled': self.hotkey.enabled,
            },
            'git': {
                'repo_path': self.git.repo_path,
                'target_folder': self.git.target_folder,
                'branch': self.git.branch,
                'auto_pull': self.git.auto_pull,
            },
            'github': {
                'username': self.github.username,
                'repo_name': self.github.repo_name,
            },
            'naming': {
                'format': self.naming.format,
                'prefix': self.naming.prefix,
                'suffix': self.naming.suffix,
                'extension': self.naming.extension,
            },
            'image': {
                'format': self.image.format,
                'quality': self.image.quality,
                'optimize': self.image.optimize,
            },
            'ui': {
                'show_preview': self.ui.show_preview,
                'preview_max_width': self.ui.preview_max_width,
                'preview_max_height': self.ui.preview_max_height,
                'confirm_before_upload': self.ui.confirm_before_upload,
                'auto_copy': self.ui.auto_copy,
                'show_notification': self.ui.show_notification,
                'notification_duration': self.ui.notification_duration,
                'minimize_to_tray': self.ui.minimize_to_tray,
                'start_minimized': self.ui.start_minimized,
                'headless': {
                    'confirm_after_capture': self.ui.headless.confirm_after_capture,
                    'confirm_before_upload': self.ui.headless.confirm_before_upload,
                    'use_native_dialog': self.ui.headless.use_native_dialog,
                },
            },
            'logging': {
                'level': self.logging.level,
                'rotation': self.logging.rotation,
                'retention': self.logging.retention,
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        """从字典创建配置对象"""
        config = cls()

        # 热键配置
        if 'hotkey' in data:
            hotkey_data = data['hotkey']
            config.hotkey = HotkeyConfig(
                key=hotkey_data.get('key', 'ctrl+shift+a'),
                enabled=hotkey_data.get('enabled', True),
            )

        # Git配置
        if 'git' in data:
            git_data = data['git']
            config.git = GitConfig(
                repo_path=git_data.get('repo_path', ''),
                target_folder=git_data.get('target_folder', 'screenshots'),
                branch=git_data.get('branch', 'main'),
                auto_pull=git_data.get('auto_pull', False),
            )

        # GitHub配置
        if 'github' in data:
            github_data = data['github']
            config.github = GitHubConfig(
                username=github_data.get('username', ''),
                repo_name=github_data.get('repo_name', ''),
            )

        # 命名配置
        if 'naming' in data:
            naming_data = data['naming']
            config.naming = NamingConfig(
                format=naming_data.get('format', '%Y-%m-%d_%H-%M-%S'),
                prefix=naming_data.get('prefix', ''),
                suffix=naming_data.get('suffix', ''),
                extension=naming_data.get('extension', '.png'),
            )

        # 图片配置
        if 'image' in data:
            image_data = data['image']
            config.image = ImageConfig(
                format=image_data.get('format', 'PNG'),
                quality=image_data.get('quality', 95),
                optimize=image_data.get('optimize', True),
            )

        # UI配置
        if 'ui' in data:
            ui_data = data['ui']
            # 解析 headless 子配置
            headless_data = ui_data.get('headless', {}) if isinstance(ui_data.get('headless'), dict) else {}
            headless_config = HeadlessUIConfig(
                confirm_after_capture=headless_data.get('confirm_after_capture', True),
                confirm_before_upload=headless_data.get('confirm_before_upload', True),
                use_native_dialog=headless_data.get('use_native_dialog', True),
            )
            config.ui = UIConfig(
                show_preview=ui_data.get('show_preview', True),
                preview_max_width=ui_data.get('preview_max_width', 800),
                preview_max_height=ui_data.get('preview_max_height', 600),
                confirm_before_upload=ui_data.get('confirm_before_upload', True),
                auto_copy=ui_data.get('auto_copy', True),
                show_notification=ui_data.get('show_notification', True),
                notification_duration=ui_data.get('notification_duration', 3000),
                minimize_to_tray=ui_data.get('minimize_to_tray', True),
                start_minimized=ui_data.get('start_minimized', False),
                headless=headless_config,
            )

        # 日志配置
        if 'logging' in data:
            logging_data = data['logging']
            config.logging = LoggingConfig(
                level=logging_data.get('level', 'INFO'),
                rotation=logging_data.get('rotation', '10 MB'),
                retention=logging_data.get('retention', '7 days'),
            )

        return config

    def validate(self) -> tuple[bool, list[str]]:
        """
        验证配置

        Returns:
            tuple[bool, list[str]]: (是否有效, 错误消息列表)
        """
        errors = []

        # 检查必填字段
        if not self.git.repo_path:
            errors.append("Git仓库路径不能为空")

        if not self.github.username:
            errors.append("GitHub用户名不能为空")

        if not self.github.repo_name:
            errors.append("GitHub仓库名不能为空")

        # 检查仓库路径是否存在
        if self.git.repo_path:
            repo_path = Path(self.git.repo_path)
            if not repo_path.exists():
                errors.append(f"Git仓库路径不存在: {self.git.repo_path}")
            elif not (repo_path / '.git').exists():
                errors.append(f"路径不是Git仓库: {self.git.repo_path}")

        # 检查时间戳格式
        if self.naming.format:
            try:
                from datetime import datetime
                datetime.now().strftime(self.naming.format)
            except Exception as e:
                errors.append(f"时间戳格式无效: {e}")

        return len(errors) == 0, errors