# MaHaLuDa - Windows截图自动上传GitHub工具

一个轻量级的Windows截图工具，支持全局快捷键截图、自动上传到GitHub并复制链接。

## 功能特性

- **全局快捷键截图**: 按 `Ctrl+Shift+A` 触发系统截图工具
- **系统集成**: 调用 Windows 系统截图（Win+Shift+S），支持区域选择、窗口截图、全屏截图
- **多显示器支持**: 完美支持多显示器环境
- **自动上传**: 通过本地Git自动上传到GitHub
- **链接复制**: 上传成功后自动复制GitHub Raw链接到剪贴板
- **系统托盘**: 最小化到系统托盘，后台运行
- **轻量级**: 无GUI依赖，不依赖PyQt6，使用系统托盘交互

## 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.10 或更高版本
- **权限**: 需要管理员权限（全局热键监听需要）
- **Git**: 需要安装并配置好 Git

## 安装

### 从源码安装

1. 克隆仓库
```bash
git clone https://github.com/your-username/MaHaLuDa.git
cd MaHaLuDa
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行程序（需要管理员权限）
```bash
# Windows CMD（管理员）
python src/main.py

# 或 PowerShell（管理员）
python src\main.py
```

### 使用打包版本

直接下载发布页面的 `MaHaLuDa.exe` 可执行文件，以管理员身份运行。

## 配置

首次运行会在 `%LOCALAPPDATA%/MaHaLuDa/config.yaml` 创建配置文件。

### 必填配置项

```yaml
git:
  repo_path: "E:/Project/BlogImages"  # 本地Git仓库路径（绝对路径）
  target_folder: "screenshots"         # 仓库内目标文件夹
  branch: "main"                       # 分支名称

github:
  username: "your-username"            # GitHub用户名
  repo_name: "BlogImages"              # GitHub仓库名
```

### 可选配置项

```yaml
hotkey:
  key: "ctrl+shift+a"     # 全局热键（默认: Ctrl+Shift+A）

git:
  auto_pull: false        # 推送前是否自动拉取（默认: false）

naming:
  format: "%Y-%m-%d_%H-%M-%S"  # 文件名时间格式

image:
  format: "png"           # 图片格式（png/jpg）
  quality: 95             # 图片质量（jpg格式时有效）

ui:
  show_preview: false     # 是否显示预览窗口（默认: false，无GUI版本不支持）
  confirm_before_upload: true  # 上传前确认（默认: true）

logging:
  level: "INFO"           # 日志级别
  rotation: "10 MB"       # 日志轮转大小
  retention: "7 days"     # 日志保留时间
```

## 使用方法

### 基本工作流程

1. **启动程序**（需要管理员权限）
   - 程序启动后会在系统托盘显示图标
   - 托盘图标提供右键菜单

2. **触发截图**
   - 按 `Ctrl+Shift+A` 触发截图
   - 或右键托盘图标 → "截图"

3. **选择区域**
   - 系统截图工具自动启动（Win+Shift+S）
   - 选择截图区域、窗口或全屏

4. **自动处理**
   - 程序自动检测剪贴板中的截图
   - 保存到配置的Git仓库
   - 自动执行 `git add`、`git commit`、`git push`
   - 生成GitHub Raw URL并复制到剪贴板

5. **获取链接**
   - 链接已自动复制到剪贴板
   - 直接粘贴使用（Ctrl+V）

### 托盘菜单功能

- **截图**: 手动触发截图
- **打开配置目录**: 打开配置文件所在目录
- **查看日志**: 打开日志文件
- **退出**: 退出程序

## 工作原理

1. **热键监听**: 使用 `keyboard` 库监听全局热键（需要管理员权限）
2. **系统截图**: 触发 Windows 系统截图工具（Win+Shift+S）
3. **剪贴板轮询**: 轮询剪贴板检测截图数据（最长等待30秒）
4. **图像处理**: 使用 Pillow 保存图像到指定格式
5. **Git 操作**: 自动执行 `git add`、`commit`、`push`
6. **链接生成**: 根据配置生成 GitHub Raw URL

## 故障排除

### 热键无响应

**原因**: `keyboard` 库需要管理员权限

**解决方案**:
- 以管理员身份运行程序
- 或使用托盘菜单手动触发截图

### WSL 环境问题

**原因**: WSL 中 `keyboard` 库无法监听 Windows 全局热键

**解决方案**:
- 在 Windows 原生环境中运行程序
- 参考 `diagnose.py` 诊断脚本

### 剪贴板检测失败

**可能原因**:
- 截图时间过长（超过30秒）
- 其他程序占用剪贴板

**解决方案**:
- 截图后尽快完成选择
- 检查是否有剪贴板管理工具冲突

### Git 操作失败

**可能原因**:
- Git 仓库未初始化
- 远程仓库配置错误
- 网络连接问题

**解决方案**:
- 确保 `git repo_path` 指向有效的 Git 仓库
- 检查 `git branch` 配置是否正确
- 验证网络连接和 Git 凭据

### 诊断工具

运行诊断脚本检查环境：
```bash
python diagnose.py
```

诊断内容包括：
- 运行环境检测（WSL/Windows）
- 依赖库检查
- PyQt6 GUI 功能检测（如果使用）
- 键盘热键功能检测
- 截图功能检测
- 配置文件验证

## 开发

### 项目结构

```
MaHaLuDa/
├── src/
│   ├── main.py                 # 程序入口
│   ├── headless_main.py        # 无GUI版本主程序
│   ├── core/                   # 核心业务逻辑
│   │   ├── config_manager.py   # 配置管理
│   │   ├── hotkey_manager.py   # 热键管理
│   │   ├── git_operations.py   # Git操作
│   │   ├── image_processor.py  # 图像处理
│   │   └── link_generator.py   # 链接生成
│   └── utils/                  # 工具函数
│       ├── clipboard.py        # 剪贴板操作
│       ├── dialogs.py          # 对话框
│       ├── file_utils.py       # 文件操作
│       ├── logger.py           # 日志配置
│       └── naming.py           # 文件命名
├── config/
│   └── config.yaml             # 配置模板
├── tests/                      # 测试文件
├── build.spec                  # PyInstaller打包配置
├── diagnose.py                 # 环境诊断脚本
└── requirements.txt            # 依赖列表
```

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black src/
```

### 类型检查

```bash
mypy src/
```

### 打包可执行文件

```bash
pyinstaller build.spec
```

打包后的可执行文件位于 `dist/` 目录。

## 技术栈

- **Python 3.10+**
- **keyboard**: 全局热键监听
- **Pillow**: 图像处理
- **pystray**: 系统托盘图标
- **pyperclip**: 剪贴板操作
- **PyYAML**: 配置管理
- **loguru**: 日志系统
- **mss**: 截图功能（核心模块依赖）

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v2.0.0 (当前版本)
- 重构为无GUI版本（Headless）
- 移除 PyQt6 依赖
- 使用系统截图工具（Win+Shift+S）
- 添加系统托盘支持
- 优化剪贴板轮询机制
- 改进配置管理和日志系统

### v1.0.0
- 初始版本
- PyQt6 GUI 截图功能
- 区域选择和预览窗口
