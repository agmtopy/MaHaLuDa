"""环境检查脚本"""
import sys
import subprocess

print("=" * 60)
print("环境检查")
print("=" * 60)

print(f"\n1. Python信息:")
print(f"   版本: {sys.version}")
print(f"   路径: {sys.executable}")
print(f"   架构: {sys.maxsize > 2**32 and '64位' or '32位'}")

print(f"\n2. 检查已安装的PyQt6包:")
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "|", "findstr", "PyQt"],
        capture_output=True,
        text=True,
        shell=True
    )
    print(result.stdout)
except Exception as e:
    print(f"   错误: {e}")

print(f"\n3. 检查pip:")
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True
    )
    print(f"   {result.stdout.strip()}")
except Exception as e:
    print(f"   错误: {e}")

print("\n4. 检查PyQt6安装位置:")
try:
    import PyQt6
    print(f"   PyQt6路径: {PyQt6.__file__}")

    # 检查Qt库文件
    import os
    qt_path = os.path.dirname(PyQt6.__file__)
    print(f"   PyQt6目录: {qt_path}")

    # 列出Qt DLL文件
    qt_lib_path = os.path.join(qt_path, "Qt6")
    if os.path.exists(qt_lib_path):
        print(f"   Qt6目录存在: {qt_lib_path}")
        dll_files = [f for f in os.listdir(qt_lib_path) if f.endswith('.dll')]
        print(f"   找到 {len(dll_files)} 个DLL文件")
    else:
        print(f"   ✗ Qt6目录不存在: {qt_lib_path}")

    # 检查plugins目录
    plugins_path = os.path.join(qt_path, "Qt6", "plugins")
    if os.path.exists(plugins_path):
        print(f"   plugins目录存在")
    else:
        print(f"   ✗ plugins目录不存在")

except ImportError as e:
    print(f"   ✗ PyQt6未正确安装: {e}")

print("\n" + "=" * 60)