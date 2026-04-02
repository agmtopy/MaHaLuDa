"""PyQt6诊断脚本"""
import sys

print("=" * 60)
print("PyQt6 诊断测试")
print("=" * 60)

print(f"\n1. Python版本: {sys.version}")
print(f"   Python路径: {sys.executable}")

print("\n2. 测试PyQt6导入...")
try:
    import PyQt6
    print(f"   ✓ PyQt6包已安装")
    print(f"   PyQt6路径: {PyQt6.__file__}")
except ImportError as e:
    print(f"   ✗ PyQt6未安装: {e}")
    sys.exit(1)

print("\n3. 测试QtCore导入...")
try:
    from PyQt6.QtCore import Qt, PYQT_VERSION_STR
    print(f"   ✓ QtCore模块正常")
    print(f"   PyQt版本: {PYQT_VERSION_STR}")
except ImportError as e:
    print(f"   ✗ QtCore导入失败: {e}")
    sys.exit(1)

print("\n4. 测试QtWidgets导入...")
try:
    from PyQt6.QtWidgets import QApplication
    print(f"   ✓ QtWidgets模块正常")
except ImportError as e:
    print(f"   ✗ QtWidgets导入失败: {e}")
    sys.exit(1)

print("\n5. 测试创建QApplication...")
try:
    app = QApplication(sys.argv)
    print(f"   ✓ QApplication创建成功")
    print(f"   显示器数量: {app.screens().__len__()}")
except Exception as e:
    print(f"   ✗ QApplication创建失败: {e}")
    print(f"   错误类型: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ 所有测试通过！PyQt6工作正常")
print("=" * 60)