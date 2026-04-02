"""配置管理器测试"""
import pytest
from pathlib import Path
import tempfile
import yaml

from src.core.config_manager import Config, HotkeyConfig, GitConfig, GitHubConfig


class TestConfigManager:
    """配置管理器测试类"""

    def test_default_config(self):
        """测试默认配置"""
        config = Config()

        assert config.hotkey.key == "ctrl+shift+a"
        assert config.hotkey.enabled is True
        assert config.git.repo_path == ""
        assert config.git.target_folder == "screenshots"
        assert config.github.username == ""

    def test_config_to_dict(self):
        """测试配置转换为字典"""
        config = Config()
        config.hotkey.key = "ctrl+f1"
        config.git.repo_path = "/path/to/repo"

        data = config.to_dict()

        assert data['hotkey']['key'] == "ctrl+f1"
        assert data['git']['repo_path'] == "/path/to/repo"

    def test_config_from_dict(self):
        """测试从字典创建配置"""
        data = {
            'hotkey': {
                'key': 'alt+a',
                'enabled': False,
            },
            'git': {
                'repo_path': '/test/path',
                'target_folder': 'images',
                'branch': 'master',
                'auto_pull': True,
            },
        }

        config = Config.from_dict(data)

        assert config.hotkey.key == 'alt+a'
        assert config.hotkey.enabled is False
        assert config.git.repo_path == '/test/path'
        assert config.git.target_folder == 'images'
        assert config.git.branch == 'master'
        assert config.git.auto_pull is True

    def test_config_save_and_load(self):
        """测试保存和加载配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"

            # 创建配置并保存
            config = Config()
            config.hotkey.key = "ctrl+alt+s"
            config.git.repo_path = "/my/repo"
            config.save(config_path)

            # 验证文件已创建
            assert config_path.exists()

            # 加载配置
            loaded_config = Config.load(config_path)

            assert loaded_config.hotkey.key == "ctrl+alt+s"
            assert loaded_config.git.repo_path == "/my/repo"

    def test_config_validate_empty_repo_path(self):
        """测试验证空仓库路径"""
        config = Config()
        config.git.repo_path = ""

        is_valid, errors = config.validate()

        assert is_valid is False
        assert any("Git仓库路径不能为空" in error for error in errors)

    def test_config_validate_invalid_repo_path(self):
        """测试验证无效仓库路径"""
        config = Config()
        config.git.repo_path = "/nonexistent/path"
        config.github.username = "user"
        config.github.repo_name = "repo"

        is_valid, errors = config.validate()

        assert is_valid is False
        assert any("Git仓库路径不存在" in error for error in errors)

    def test_config_validate_missing_github_info(self):
        """测试验证缺少GitHub信息"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建临时的git仓库
            repo_path = Path(temp_dir)
            (repo_path / ".git").mkdir()

            config = Config()
            config.git.repo_path = str(repo_path)
            config.github.username = ""
            config.github.repo_name = ""

            is_valid, errors = config.validate()

            assert is_valid is False
            assert any("GitHub用户名不能为空" in error for error in errors)

    def test_config_get_config_dir(self):
        """测试获取配置目录"""
        config_dir = Config.get_config_dir()

        assert isinstance(config_dir, Path)
        assert "MaHaLuDa" in str(config_dir) or ".mahaluda" in str(config_dir)

    def test_hotkey_config_dataclass(self):
        """测试热键配置数据类"""
        hotkey = HotkeyConfig(key="f1", enabled=False)

        assert hotkey.key == "f1"
        assert hotkey.enabled is False

    def test_git_config_dataclass(self):
        """测试Git配置数据类"""
        git = GitConfig(
            repo_path="/path",
            target_folder="images",
            branch="develop",
            auto_pull=True
        )

        assert git.repo_path == "/path"
        assert git.target_folder == "images"
        assert git.branch == "develop"
        assert git.auto_pull is True

    def test_github_config_dataclass(self):
        """测试GitHub配置数据类"""
        github = GitHubConfig(username="testuser", repo_name="testrepo")

        assert github.username == "testuser"
        assert github.repo_name == "testrepo"