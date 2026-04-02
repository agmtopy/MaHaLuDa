"""GitHub链接生成模块"""
import urllib.parse
from typing import Optional
from loguru import logger

from .config_manager import GitHubConfig


class LinkGenerator:
    """GitHub链接生成器"""

    BASE_RAW_URL = "https://raw.githubusercontent.com"
    BASE_GITHUB_URL = "https://github.com"

    def __init__(self, config: GitHubConfig):
        """
        初始化链接生成器

        Args:
            config: GitHub配置
        """
        self.username = config.username
        self.repo_name = config.repo_name

    def generate_raw_url(self, file_path: str, branch: str = "main") -> str:
        """
        生成GitHub Raw链接

        Args:
            file_path: 文件相对路径
            branch: 分支名称

        Returns:
            str: GitHub Raw链接

        Example:
            >>> config = GitHubConfig(username="user", repo_name="repo")
            >>> generator = LinkGenerator(config)
            >>> generator.generate_raw_url("images/test.png", "main")
            'https://raw.githubusercontent.com/user/repo/main/images/test.png'
        """
        # URL编码处理特殊字符
        encoded_path = urllib.parse.quote(file_path, safe="/")

        url = f"{self.BASE_RAW_URL}/{self.username}/{self.repo_name}/{branch}/{encoded_path}"

        logger.debug(f"生成Raw链接: {url}")
        return url

    def generate_github_url(self, file_path: str, branch: str = "main") -> str:
        """
        生成GitHub页面链接

        Args:
            file_path: 文件相对路径
            branch: 分支名称

        Returns:
            str: GitHub页面链接

        Example:
            >>> config = GitHubConfig(username="user", repo_name="repo")
            >>> generator = LinkGenerator(config)
            >>> generator.generate_github_url("images/test.png", "main")
            'https://github.com/user/repo/blob/main/images/test.png'
        """
        encoded_path = urllib.parse.quote(file_path, safe="/")

        url = f"{self.BASE_GITHUB_URL}/{self.username}/{self.repo_name}/blob/{branch}/{encoded_path}"

        logger.debug(f"生成GitHub链接: {url}")
        return url

    def generate_markdown_link(self, url: str, alt_text: str = "image") -> str:
        """
        生成Markdown格式链接

        Args:
            url: 图片URL
            alt_text: 替代文本

        Returns:
            str: Markdown格式链接

        Example:
            >>> generator.generate_markdown_link("https://example.com/image.png", "screenshot")
            '![screenshot](https://example.com/image.png)'
        """
        markdown = f"![{alt_text}]({url})"
        logger.debug(f"生成Markdown链接: {markdown}")
        return markdown

    def generate_html_link(self, url: str, alt_text: str = "image") -> str:
        """
        生成HTML格式链接

        Args:
            url: 图片URL
            alt_text: 替代文本

        Returns:
            str: HTML格式链接

        Example:
            >>> generator.generate_html_link("https://example.com/image.png", "screenshot")
            '<img src="https://example.com/image.png" alt="screenshot">'
        """
        html = f'<img src="{url}" alt="{alt_text}">'
        logger.debug(f"生成HTML链接: {html}")
        return html