"""集成测试"""
import pytest
from pathlib import Path
import tempfile
import subprocess
from PIL import Image

from src.core.config_manager import Config
from src.core.screenshot_capture import ScreenshotCapture
from src.core.git_operations import GitOperations
from src.core.link_generator import LinkGenerator
from src.utils.naming import generate_filename, get_full_path, ensure_unique_filename


class TestIntegration:
    """集成测试类"""

    @pytest.fixture
    def temp_git_repo(self):
        """创建临时Git仓库"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # 初始化Git仓库
            subprocess.run(['git', 'init'], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=repo_path, check=True, capture_output=True)

            # 创建初始提交
            readme = repo_path / "README.md"
            readme.write_text("# Test Repo")
            subprocess.run(['git', 'add', 'README.md'], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_path, check=True, capture_output=True)

            yield repo_path

    def test_complete_workflow(self, temp_git_repo):
        """测试完整工作流程"""
        # 1. 创建配置
        config = Config()
        config.git.repo_path = str(temp_git_repo)
        config.git.target_folder = "screenshots"
        config.github.username = "testuser"
        config.github.repo_name = "testrepo"
        config.naming.format = "%Y-%m-%d_%H-%M-%S"
        config.naming.extension = ".png"

        # 2. 生成文件名
        filename = generate_filename(config.naming)
        assert filename.endswith('.png')

        # 3. 获取完整路径
        file_path = get_full_path(config.git.repo_path, config.git.target_folder, filename)
        assert config.git.target_folder in str(file_path)

        # 4. 创建测试图像
        test_image = Image.new('RGB', (200, 200), color='blue')

        # 5. 保存图像
        result = ScreenshotCapture.save_screenshot(test_image, file_path)
        assert result is True
        assert file_path.exists()

        # 6. Git操作
        git_ops = GitOperations(config.git.repo_path)

        # 添加并提交
        commit_result = git_ops.add_and_commit(file_path, f"Add screenshot: {filename}")
        assert commit_result is True

        # 检查状态
        status = git_ops.get_git_status()
        assert len(status['staged']) == 0
        assert len(status['unstaged']) == 0

        # 7. 生成GitHub链接
        link_gen = LinkGenerator(config.github)
        relative_path = f"{config.git.target_folder}/{filename}"
        github_url = link_gen.generate_raw_url(relative_path)

        assert "raw.githubusercontent.com" in github_url
        assert config.github.username in github_url
        assert config.github.repo_name in github_url
        assert filename in github_url

    def test_file_naming_uniqueness(self, temp_git_repo):
        """测试文件名唯一性"""
        config = Config()
        config.git.repo_path = str(temp_git_repo)
        config.git.target_folder = "screenshots"
        config.naming.extension = ".png"

        # 创建同名文件
        filename = "test_image.png"
        file_path = get_full_path(config.git.repo_path, config.git.target_folder, filename)

        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建第一个文件
        file_path.write_bytes(b"fake image data")

        # 测试确保唯一文件名
        unique_path = ensure_unique_filename(file_path)

        assert unique_path != file_path
        assert "_001" in unique_path.name

    def test_image_processing_pipeline(self, temp_git_repo):
        """测试图像处理流水线"""
        from src.core.image_processor import ImageProcessor
        from src.core.config_manager import ImageConfig

        # 创建配置
        image_config = ImageConfig(format='PNG', quality=95, optimize=True)

        # 创建测试图像
        test_image = Image.new('RGBA', (300, 300), color=(255, 0, 0, 128))

        # 处理图像
        processed = ImageProcessor.process_image(test_image, image_config)

        assert processed.mode == 'RGBA'

        # 保存图像
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "processed.png"
            result = ImageProcessor.save_with_config(processed, output_path, image_config)

            assert result is True
            assert output_path.exists()

    def test_config_validation_workflow(self, temp_git_repo):
        """测试配置验证工作流"""
        config = Config()
        config.git.repo_path = str(temp_git_repo)
        config.github.username = "testuser"
        config.github.repo_name = "testrepo"

        # 验证配置
        is_valid, errors = config.validate()

        assert is_valid is True
        assert len(errors) == 0

    def test_config_save_and_load_workflow(self, temp_git_repo):
        """测试配置保存和加载工作流"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"

            # 创建并保存配置
            config1 = Config()
            config1.git.repo_path = str(temp_git_repo)
            config1.github.username = "user1"
            config1.github.repo_name = "repo1"
            config1.save(config_path)

            # 加载配置
            config2 = Config.load(config_path)

            assert config2.git.repo_path == str(temp_git_repo)
            assert config2.github.username == "user1"
            assert config2.github.repo_name == "repo1"

    def test_screenshot_to_github_pipeline(self, temp_git_repo):
        """测试从截图到GitHub的完整流程"""
        config = Config()
        config.git.repo_path = str(temp_git_repo)
        config.git.target_folder = "images"
        config.github.username = "testuser"
        config.github.repo_name = "testrepo"
        config.image.format = 'PNG'

        # 创建测试截图
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建临时图像
            test_image = Image.new('RGB', (100, 100), color='red')
            temp_image_path = Path(temp_dir) / "temp.png"
            test_image.save(temp_image_path)

            # 生成文件名
            filename = generate_filename(config.naming)

            # 获取保存路径
            save_path = get_full_path(config.git.repo_path, config.git.target_folder, filename)

            # 保存到Git仓库
            save_result = ScreenshotCapture.save_screenshot(test_image, save_path, format='PNG')
            assert save_result is True

            # Git提交
            git_ops = GitOperations(config.git.repo_path)
            commit_result = git_ops.add_and_commit(save_path, f"Add screenshot {filename}")
            assert commit_result is True

            # 生成GitHub链接
            link_gen = LinkGenerator(config.github)
            relative_path = f"{config.git.target_folder}/{filename}"
            github_url = link_gen.generate_raw_url(relative_path)

            # 验证
            assert save_path.exists()
            assert "raw.githubusercontent.com" in github_url
            assert filename in github_url