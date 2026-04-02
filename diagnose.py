"""诊断脚本 - 检测截图功能问题"""
import sys
import os

print("=" * 70)
print("MaHaLuDa 截图功能诊断")
print("=" * 70)

# 1. 检测运行环境
print(f"\n1. 运行环境:")
print(f"   操作系统: {os.name}")
print(f"   系统: {sys.platform}")
try:
    uname_release = os.uname().release.lower()  # type: ignore[attr-defined]
    is_wsl_runtime = "microsoft" in uname_release
except Exception:
    is_wsl_runtime = False
print(f"   WSL环境: {'是' if is_wsl_runtime else '否'}")
print(f"   Python版本: {sys.version}")

# 2. 检测依赖库
print(f"\n2. 依赖库检查:")
dependencies = {
    'PyQt6': 'GUI框架',
    'keyboard': '全局热键',
    'mss': '截图捕获',
    'PIL': '图像处理',
    'loguru': '日志系统',
    'yaml': '配置文件',
    'pyperclip': '剪贴板'
}

missing = []
for module, desc in dependencies.items():
    try:
        __import__(module)
        print(f"   ✓ {module:15s} - {desc}")
    except ImportError:
        print(f"   ✗ {module:15s} - {desc} [未安装]")
        missing.append(module)

# 3. 检测PyQt6 GUI功能
print(f"\n3. PyQt6 GUI功能检测:")
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QT_VERSION_STR

    print(f"   Qt版本: {QT_VERSION_STR}")

    # 尝试创建QApplication（需要DISPLAY）
    try:
        app = QApplication([])
        print(f"   ✓ QApplication创建成功")

        # 检测显示器
        screens = app.screens()
        print(f"   检测到 {len(screens)} 个显示器")
        for i, screen in enumerate(screens):
            geometry = screen.geometry()
            print(f"      显示器 {i}: {geometry.width()}x{geometry.height()} @ ({geometry.x()}, {geometry.y()})")

        app.quit()
    except Exception as e:
        print(f"   ✗ GUI初始化失败: {e}")
        if "could not connect to display" in str(e).lower():
            print(f"      原因: 未检测到显示器（可能需要X11服务器）")

except ImportError as e:
    print(f"   ✗ PyQt6未安装: {e}")

# 4. 检测keyboard库
print(f"\n4. 键盘热键检测:")
try:
    import keyboard
    print(f"   ✓ keyboard库已导入")

    # 测试热键功能
    try:
        # 尝试添加测试热键
        keyboard.add_hotkey('f13', lambda: None)  # F13通常不存在，用于测试
        keyboard.remove_hotkey('f13')
        print(f"   ✓ 热键注册功能正常")
    except Exception as e:
        print(f"   ✗ 热键注册失败: {e}")
        if "may need root" in str(e).lower() or "permission" in str(e).lower():
            print(f"      原因: 可能需要管理员/ROOT权限")

except ImportError as e:
    print(f"   ✗ keyboard库未安装: {e}")

# 5. 检测mss截图功能
print(f"\n5. 截图功能检测:")
try:
    import mss

    print(f"   ✓ mss库已导入")

    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            print(f"   检测到 {len(monitors) - 1} 个显示器")

            # 尝试截图
            try:
                screenshot = sct.grab(sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0])
                print(f"   ✓ 截图功能正常: {screenshot.size}")
            except Exception as e:
                print(f"   ✗ 截图失败: {e}")

    except Exception as e:
        print(f"   ✗ mss初始化失败: {e}")

except ImportError as e:
    print(f"   ✗ mss库未安装: {e}")

# 6. 检测配置文件
print(f"\n6. 配置文件检测:")
try:
    from src.core.config_manager import Config

    config_file = Config.get_config_file()
    config_dir = Config.get_config_dir()

    print(f"   配置目录: {config_dir}")
    print(f"   配置文件: {config_file}")

    if config_file.exists():
        print(f"   ✓ 配置文件存在")
        config = Config.load()
        print(f"   热键: {config.hotkey.key}")
        print(f"   Git仓库: {config.git.repo_path or '未配置'}")
        print(f"   GitHub用户: {config.github.username or '未配置'}")

        # 验证配置
        is_valid, errors = config.validate()
        if is_valid:
            print(f"   ✓ 配置验证通过")
        else:
            print(f"   ✗ 配置验证失败:")
            for error in errors:
                print(f"      - {error}")
    else:
        print(f"   ✗ 配置文件不存在")

except Exception as e:
    print(f"   ✗ 配置加载失败: {e}")

# 7. 问题诊断总结
print(f"\n" + "=" * 70)
print("诊断总结:")
print("=" * 70)

# WSL环境检测
is_wsl = is_wsl_runtime

if is_wsl:
    print("\n⚠ 检测到WSL环境!")
    print("\n问题分析:")
    print("1. WSL环境中keyboard库无法监听Windows全局热键")
    print("2. WSL环境中mss无法截取Windows屏幕")
    print("3. WSL环境中PyQt6需要X11服务器才能显示GUI")
    print("\n解决方案:")
    print("方案1: 在Windows原生Python环境中运行程序")
    print("       - 安装Windows版Python")
    print("       - 使用Windows命令提示符或PowerShell运行")
    print("       - pip install -r requirements.txt")
    print("       - python -m src.main")
    print("\n方案2: 如果必须在WSL中开发，需要:")
    print("       - 安装X11服务器（如VcXsrv, X410）")
    print("       - 配置DISPLAY环境变量")
    print("       - 但keyboard库和mss库仍无法在WSL中正常工作")
    print("\n推荐: 使用方案1，在Windows原生环境中运行此程序")

if missing:
    print(f"\n⚠ 缺少依赖库: {', '.join(missing)}")
    print(f"   运行: pip install -r requirements.txt")

print("\n" + "=" * 70)