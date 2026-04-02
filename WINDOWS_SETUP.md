# Windows 安装和运行指南

## 问题诊断

**当前问题**: 您正在WSL (Linux子系统) 中运行程序，这导致：
- ❌ 无法监听Windows全局热键
- ❌ 无法截取Windows屏幕
- ❌ 无法显示GUI窗口

**解决方案**: 在Windows原生Python环境中运行程序

---

## 安装步骤

### 1. 安装Python (Windows版)

如果尚未安装Python：
1. 访问 https://www.python.org/downloads/
2. 下载Python 3.10或更高版本（推荐3.12）
3. **重要**: 安装时勾选 "Add Python to PATH"

验证安装（在Windows命令提示符或PowerShell中）：
```powershell
python --version
# 应显示: Python 3.12.x
```

### 2. 打开Windows终端

**不要使用WSL终端！** 请使用：
- Windows命令提示符 (cmd)
- Windows PowerShell
- Windows Terminal

### 3. 导航到项目目录

```powershell
# 切换到E盘
E:

# 进入项目目录
cd E:\Project\MaHaLuDa
```

### 4. 安装依赖

```powershell
# 安装所有依赖库
pip install -r requirements.txt

# 或者使用国内镜像加速
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

验证安装：
```powershell
python check_env.py
```

应该看到所有依赖都已安装。

### 5. 配置程序

首次运行会自动创建配置文件：
```powershell
python -m src.main
```

配置文件位置：`%LOCALAPPDATA%\MaHaLuDa\config.yaml`

编辑配置文件，填入必要信息：
```yaml
git:
  repo_path: "E:\\YourRepo\\screenshots"  # 您的Git仓库路径（绝对路径）
  target_folder: "screenshots"
  branch: "main"

github:
  username: "your-username"    # 您的GitHub用户名
  repo_name: "your-repo"       # 您的GitHub仓库名
```

### 6. 运行程序

```powershell
# 正常启动
python -m src.main

# 或者直接运行主文件
python src\main.py
```

### 7. 使用截图功能

1. 程序启动后会最小化到系统托盘
2. 按 **Ctrl+Shift+A** 触发截图
3. 鼠标拖动选择截图区域
4. 预览窗口中点击确认
5. 自动上传到GitHub并复制链接

---

## 快速启动脚本

创建 `start.bat` 文件（已生成）：
```batch
@echo off
echo 启动 MaHaLuDa...
python -m src.main
pause
```

双击运行即可。

---

## 常见问题

### Q: 提示 "热键注册失败"
**A**: 需要管理员权限运行：
- 右键点击 `start.bat`
- 选择 "以管理员身份运行"

### Q: 提示配置错误
**A**: 编辑配置文件：
```powershell
notepad %LOCALAPPDATA%\MaHaLuDa\config.yaml
```

### Q: 找不到显示器
**A**: 确保您的显卡驱动已安装，并且有显示器连接。

### Q: Git推送失败
**A**: 检查：
1. Git仓库路径是否正确
2. 是否已配置Git凭证
3. 网络连接是否正常

---

## 构建可执行文件

如果要创建独立的exe文件：

```powershell
# 安装PyInstaller
pip install pyinstaller

# 构建
pyinstaller build.spec

# 生成的exe在 dist/ 目录
```

---

## 开发调试

```powershell
# 运行测试
pytest tests/

# 代码格式化
black src/

# 类型检查
mypy src/
```

---

## 重要提醒

⚠️ **不要在WSL中运行此程序！**

此程序是专门为Windows设计的桌面应用，使用了：
- Windows全局热键API
- Windows图形界面
- Windows剪贴板

只能在Windows原生环境中运行。

---

## 需要帮助？

如果遇到问题：
1. 运行诊断脚本：`python diagnose.py`
2. 查看日志：`%LOCALAPPDATA%\MaHaLuDa\logs\`
3. 检查配置：`%LOCALAPPDATA%\MaHaLuDa\config.yaml`