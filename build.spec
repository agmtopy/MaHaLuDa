# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller构建配置文件"""

import sys
from pathlib import Path
# 无GUI版：不依赖 PyQt6，因此不收集 Qt 相关内容

# 项目根目录
project_root = Path(SPECPATH)

# 分析项目文件
a = Analysis(
    ['src/headless_main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # 包含配置模板文件
        ('config/config.yaml', 'config'),
        # 包含图标文件（如果存在）
        # ('assets/icon.ico', 'assets'),
    ],
    hiddenimports=[
        # 其他依赖
        'keyboard',
        'mss',
        'PIL',
        'PIL.Image',
        'PIL.ImageGrab',
        'pyperclip',
        'yaml',
        'loguru',

        # 项目模块
        'src.core.config_manager',
        'src.core.hotkey_manager',
        'src.core.link_generator',
        'src.core.git_operations',
        'src.core.image_processor',
        'src.utils.logger',
        'src.utils.clipboard',
        'src.utils.file_utils',
        'src.utils.naming',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ压缩包
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MaHaLuDa',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 无GUI版需要控制台输出/报错信息
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 图标文件（如果存在）
    # icon='assets/icon.ico',
    version='version_info.txt' if (project_root / 'version_info.txt').exists() else None,
)

# 更稳的 one-dir 输出：Qt DLL/插件以目录形式存在，减少 one-file 临时解压导致的 DLL 查找问题。
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='MaHaLuDa',
)