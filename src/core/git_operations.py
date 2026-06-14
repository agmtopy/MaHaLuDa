"""Git操作模块"""
import os
import subprocess
import time
from pathlib import Path
from typing import Optional
from loguru import logger


class GitOperations:
    """Git操作类，处理自动提交和推送"""

    def __init__(self, repo_path: Path | str):
        """
        初始化Git操作器

        Args:
            repo_path: Git仓库路径
        """
        self.repo_path = Path(repo_path)
        self._branch_cache: Optional[str] = None

    def _get_current_branch_cached(self) -> str:
        """获取当前分支名（带缓存）"""
        if self._branch_cache is None:
            result = self.get_current_branch()
            if result is None:
                raise RuntimeError("无法获取当前分支名")
            self._branch_cache = result
        return self._branch_cache

    def _cleanup_stale_index_lock(self) -> bool:
        """
        清理可能遗留的 .git/index.lock（通常由崩溃/强杀的 git 进程留下）
        Returns:
            bool: 是否删除了锁文件
        """
        try:
            repo_root = self.repo_path.resolve()
            lock_path = repo_root / ".git" / "index.lock"
            if not lock_path.exists():
                return False

            # 如果锁文件很新，可能确实有 git 在跑，先不要动
            try:
                age_s = time.time() - lock_path.stat().st_mtime
            except Exception:
                age_s = 0

            if age_s < 5:
                logger.warning(f"检测到 index.lock 但过新（{age_s:.1f}s），疑似仍有 git 进程在运行：{lock_path}")
                return False

            lock_path.unlink(missing_ok=True)
            logger.warning(f"已清理遗留的 Git 锁文件: {lock_path}")
            return True
        except Exception as e:
            logger.error(f"清理 index.lock 失败: {e}")
            return False

    def _run_git_command(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """
        执行git命令

        Args:
            args: git命令参数列表
            check: 是否检查返回码

        Returns:
            subprocess.CompletedProcess: 命令执行结果
        """
        cmd = ['git'] + args
        logger.debug(f"执行git命令: {' '.join(cmd)}")

        # Windows下隐藏控制台窗口
        startupinfo = None
        creationflags = 0
        if os.name == 'nt':  # Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW

        def _run_once() -> subprocess.CompletedProcess:
            return subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
                startupinfo=startupinfo,
                creationflags=creationflags,
                env={
                    **os.environ,
                    # 避免 git 在某些场景弹出凭据/编辑器导致卡死
                    "GIT_TERMINAL_PROMPT": "0",
                },
            )

        result = _run_once()

        if check and result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            logger.error(f"Git命令失败: {error_msg}")
            # 常见：崩溃遗留 index.lock。尝试清理并重试一次。
            if (
                result.returncode == 128
                and "index.lock" in error_msg
                and "File exists" in error_msg
                and self._cleanup_stale_index_lock()
            ):
                result = _run_once()
                if result.returncode == 0 or not check:
                    return result
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.error(f"Git命令失败(重试后): {error_msg}")
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)

        return result

    def is_git_repo(self) -> bool:
        """
        检查是否为有效的Git仓库

        Returns:
            bool: 是否为Git仓库
        """
        try:
            self._run_git_command(['rev-parse', '--git-dir'], check=True)
            return True
        except (subprocess.CalledProcessError, Exception):
            return False

    def add_and_commit(self, file_path: Path | str, commit_message: str) -> bool:
        """
        添加文件并提交

        Args:
            file_path: 文件路径（相对于仓库根目录）
            commit_message: 提交消息

        Returns:
            bool: 是否成功
        """
        try:
            repo_root = self.repo_path.resolve()
            abs_input = Path(file_path)

            # 转换为相对路径（Windows 下需做规范化；Path.relative_to 是纯路径匹配，可能因大小写/符号链接导致误判）
            if abs_input.is_absolute():
                abs_path = abs_input.resolve()

                try:
                    # Python 3.9+ 支持 is_relative_to
                    if not abs_path.is_relative_to(repo_root):
                        # 兜底：使用不区分大小写的 commonpath 判断
                        repo_nc = os.path.normcase(str(repo_root))
                        file_nc = os.path.normcase(str(abs_path))
                        common = os.path.normcase(os.path.commonpath([repo_nc, file_nc]))
                        if common != repo_nc:
                            logger.error(f"文件不在仓库目录中: {file_path}")
                            return False
                    rel_path = abs_path.relative_to(repo_root)
                except Exception:
                    logger.error(f"文件不在仓库目录中: {file_path}")
                    return False
            else:
                rel_path = abs_input

            # 检查文件是否存在
            abs_path = repo_root / rel_path
            if not abs_path.exists():
                logger.error(f"文件不存在: {abs_path}")
                return False

            # Git add
            logger.info(f"添加文件到Git: {rel_path}")
            self._run_git_command(['add', '--', str(rel_path)], check=True)

            # Git commit
            logger.info(f"提交更改: {commit_message}")
            self._run_git_command(['commit', '-m', commit_message], check=True)
            self._branch_cache = None

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Git操作失败: {e}")
            return False
        except Exception as e:
            logger.error(f"添加和提交文件时发生错误: {e}")
            return False

    def push_to_remote(self, remote: str = 'origin', branch: Optional[str] = None) -> bool:
        """
        推送到远程仓库

        Args:
            remote: 远程仓库名称
            branch: 分支名称，默认使用当前分支

        Returns:
            bool: 是否成功
        """
        try:
            # 获取当前分支
            if branch is None:
                branch = self._get_current_branch_cached()

            logger.info(f"推送到远程仓库: {remote}/{branch}")
            self._run_git_command(['push', remote, branch], check=True)

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"推送到远程仓库失败: {e}")
            return False
        except Exception as e:
            logger.error(f"推送时发生错误: {e}")
            return False

    def pull_from_remote(self, remote: str = 'origin', branch: Optional[str] = None) -> bool:
        """
        从远程仓库拉取

        Args:
            remote: 远程仓库名称
            branch: 分支名称，默认使用当前分支

        Returns:
            bool: 是否成功
        """
        try:
            # 获取当前分支
            if branch is None:
                branch = self._get_current_branch_cached()

            logger.info(f"从远程仓库拉取: {remote}/{branch}")
            self._run_git_command(['pull', remote, branch], check=True)

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"从远程仓库拉取失败: {e}")
            return False
        except Exception as e:
            logger.error(f"拉取时发生错误: {e}")
            return False

    def get_git_status(self) -> dict:
        """
        获取Git状态

        Returns:
            dict: Git状态信息，包含:
                - branch: 当前分支
                - staged: 已暂存的文件列表
                - unstaged: 未暂存的文件列表
                - untracked: 未跟踪的文件列表
        """
        try:
            status = {
                'branch': '',
                'staged': [],
                'unstaged': [],
                'untracked': [],
            }

            # 获取当前分支
            status['branch'] = self._get_current_branch_cached()

            # 获取状态
            result = self._run_git_command(['status', '--porcelain'], check=True)
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []

            for line in lines:
                if not line:
                    continue

                code = line[:2]
                file_path = line[3:]

                # 已暂存
                if code[0] in 'MADRC':
                    status['staged'].append(file_path)
                # 未暂存
                elif code[1] in 'MD':
                    status['unstaged'].append(file_path)
                # 未跟踪
                elif code == '??':
                    status['untracked'].append(file_path)

            return status

        except Exception as e:
            logger.error(f"获取Git状态失败: {e}")
            return {
                'branch': '',
                'staged': [],
                'unstaged': [],
                'untracked': [],
            }

    def has_uncommitted_changes(self) -> bool:
        """
        检查是否有未提交的更改

        Returns:
            bool: 是否有未提交的更改
        """
        status = self.get_git_status()
        return bool(status['staged'] or status['unstaged'] or status['untracked'])

    def get_current_branch(self) -> Optional[str]:
        """
        获取当前分支名

        Returns:
            Optional[str]: 分支名，失败返回None
        """
        try:
            result = self._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'], check=True)
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"获取当前分支失败: {e}")
            return None