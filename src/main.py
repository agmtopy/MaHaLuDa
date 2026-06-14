"""MaHaLuDa 入口 — 无 GUI 的 headless 版本。

本文件是应用的主入口点（通过 ``python src/main.py`` 或打包后的可执行文件调用）。
它直接委托给 ``src.headless_main.main()``，该函数实现了完整的 headless 工作流：
热键触发 → 系统截图（Win+Shift+S）→ 剪贴板轮询 → Git 提交推送 → 复制 URL。

注意：项目不包含 PyQt6 GUI 组件。所有界面交互通过系统原生对话框和系统托盘完成。
"""
import sys

from src.headless_main import main


if __name__ == "__main__":
    sys.exit(main())

