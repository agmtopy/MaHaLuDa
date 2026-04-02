"""Git操作测试"""
import pytest
from pathlib import Path
import tempfile
import subprocess
from unittest.mock import Mock, patch, MagicMock

from src.core.git_operations import GitOperations


class TestGitOperations:
    """Git操作测试类"""

    @pytest.fixture
    def temp_git_repo(self):
        """创建临时Git仓库"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # 初始化Git仓库
            subprocess.run(['git', 'init'], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=repo_path, check=True, capture_output=True)

            # 创建一个测试文件并提交
            test_file = repo_path / "README.md"
            test_file.write_text("# Test Repository")
            subprocess.run(['git', 'add', 'README.md'], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_path, check=True, capture_output=True)

            yield repo_path

    def test_init(self, temp_git_repo):
        """测试初始化"""
        git_ops = GitOperations(temp_git_repo)
        assert git_ops.repo_path == temp_git_repo

    def test_is_git_repo_valid(self, temp_git_repo):
        """测试验证有效的Git仓库"""
        git_ops = GitOperations(temp_git_repo)
        assert git_ops.is_git_repo() is True

    def test_is_git_repo_invalid(self):
        """测试验证无效的Git仓库"""
        with tempfile.TemporaryDirectory() as temp_dir:
            git_ops = GitOperations(temp_dir)
            assert git_ops.is_git_repo() is False

    def test_add_and_commit(self, temp_git_repo):
        """测试添加和提交文件"""
        git_ops = GitOperations(temp_git_repo)

        # 创建新文件
        new_file = temp_git_repo / "test.txt"
        new_file.write_text("Test content")

        # 添加并提交
        result = git_ops.add_and_commit(new_file, "Add test file")

        assert result is True

        # 验证文件已提交
        status = git_ops.get_git_status()
        assert len(status['staged']) == 0
        assert len(status['unstaged']) == 0

    def test_add_and_commit_nonexistent_file(self, temp_git_repo):
        """测试添加不存在的文件"""
        git_ops = GitOperations(temp_git_repo)

        result = git_ops.add_and_commit("nonexistent.txt", "Add nonexistent file")

        assert result is False

    def test_get_git_status(self, temp_git_repo):
        """测试获取Git状态"""
        git_ops = GitOperations(temp_git_repo)

        # 创建未跟踪文件
        untracked_file = temp_git_repo / "untracked.txt"
        untracked_file.write_text("Untracked")

        status = git_ops.get_git_status()

        assert 'branch' in status
        assert 'staged' in status
        assert 'unstaged' in status
        assert 'untracked' in status
        assert status['branch'] != ''

    def test_get_current_branch(self, temp_git_repo):
        """测试获取当前分支"""
        git_ops = GitOperations(temp_git_repo)

        branch = git_ops.get_current_branch()

        assert branch is not None
        assert branch in ['main', 'master']  # 根据Git版本可能是main或master

    def test_has_uncommitted_changes_false(self, temp_git_repo):
        """测试检查未提交更改（无更改）"""
        git_ops = GitOperations(temp_git_repo)

        has_changes = git_ops.has_uncommitted_changes()

        assert has_changes is False

    def test_has_uncommitted_changes_true(self, temp_git_repo):
        """测试检查未提交更改（有更改）"""
        git_ops = GitOperations(temp_git_repo)

        # 创建新文件
        new_file = temp_git_repo / "new_file.txt"
        new_file.write_text("New content")

        has_changes = git_ops.has_uncommitted_changes()

        assert has_changes is True

    @patch('subprocess.run')
    def test_push_to_remote_mock(self, mock_run, temp_git_repo):
        """测试推送到远程仓库（Mock）"""
        # 模拟成功推送
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

        git_ops = GitOperations(temp_git_repo)
        result = git_ops.push_to_remote('origin', 'main')

        assert result is True
        mock_run.assert_called()

    @patch('subprocess.run')
    def test_pull_from_remote_mock(self, mock_run, temp_git_repo):
        """测试从远程仓库拉取（Mock）"""
        # 模拟成功拉取
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

        git_ops = GitOperations(temp_git_repo)
        result = git_ops.pull_from_remote('origin', 'main')

        assert result is True
        mock_run.assert_called()

    def test_add_and_commit_with_absolute_path(self, temp_git_repo):
        """测试使用绝对路径添加文件"""
        git_ops = GitOperations(temp_git_repo)

        # 创建文件
        new_file = temp_git_repo / "absolute_test.txt"
        new_file.write_text("Absolute path test")

        # 使用绝对路径
        result = git_ops.add_and_commit(new_file.absolute(), "Add with absolute path")

        assert result is True

    def test_add_and_commit_outside_repo(self, temp_git_repo):
        """测试添加仓库外的文件"""
        git_ops = GitOperations(temp_git_repo)

        # 创建仓库外的文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Outside repo")
            outside_file = Path(f.name)

        try:
            result = git_ops.add_and_commit(outside_file, "Add outside file")
            assert result is False
        finally:
            outside_file.unlink()