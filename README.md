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

1. 从 `dist/MaHaLuDa/` 目录获取打包好的文件：
   - `MaHaLuDa.exe` — 主程序
   - `_internal/` — 依赖文件（必须和 exe 放在同一目录）

2. **右键 `MaHaLuDa.exe` → 以管理员身份运行**

3. 程序启动后不会弹出窗口，只在**系统托盘**（任务栏右下角）显示一个相机图标

> ⚠️ **必须以管理员身份运行**，否则全局热键 `Ctrl+Shift+A` 无法注册。

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
  enabled: true            # 是否启用热键（默认: true）

git:
  auto_pull: false        # 推送前是否自动拉取（默认: false）

naming:
  format: "%Y-%m-%d_%H-%M-%S"  # 文件名时间格式
  prefix: ""              # 文件名前缀
  suffix: ""              # 文件名后缀
  extension: ".png"       # 文件扩展名

image:
  format: "PNG"           # 图片格式（PNG/JPG）
  quality: 95             # 图片质量（JPG格式时有效）
  optimize: true          # 是否优化图片大小

ui:
  confirm_before_upload: true   # 上传前弹窗确认（默认: true）
  auto_copy: true               # 自动复制链接到剪贴板（默认: true）
  show_notification: true       # 显示桌面通知（默认: true）
  minimize_to_tray: true        # 关闭时最小化到托盘（默认: true）
  headless:
    confirm_after_capture: false   # 截图后是否确认（默认: false）
    confirm_before_upload: true    # 上传前确认对话框（默认: true）
    use_native_dialog: true        # 使用 Windows 原生对话框（默认: true）

logging:
  level: "INFO"           # 日志级别（DEBUG/INFO/WARNING/ERROR）
  rotation: "10 MB"       # 日志轮转大小
  retention: "7 days"     # 日志保留时间
```

## 使用方法

### 快速开始

1. **以管理员身份运行** `MaHaLuDa.exe`
2. 任务栏右下角出现托盘图标（相机形状）
3. 按 `Ctrl+Shift+A` 触发截图
4. 在弹出的系统截图工具中选择区域
5. 程序自动上传并复制 GitHub Raw 链接到剪贴板
6. 直接 `Ctrl+V` 粘贴链接使用

### 详细工作流程

```
按 Ctrl+Shift+A
       ↓
Windows 系统截图工具启动（Win+Shift+S）
       ↓
鼠标选择截图区域
       ↓
程序自动检测剪贴板中的截图
       ↓
保存到本地 Git 仓库
       ↓
git add → git commit → git push
       ↓
生成 GitHub Raw URL → 复制到剪贴板
```

### 托盘菜单（右键托盘图标）

| 菜单项 | 功能 |
|--------|------|
| **截图** | 手动触发截图（等同按快捷键） |
| **打开配置** | 用系统编辑器打开 config.yaml |
| **退出** | 退出程序 |

### 命令行参数

```bash
MaHaLuDa.exe                    # 默认启动
MaHaLuDa.exe --config path.yaml # 指定配置文件
MaHaLuDa.exe --help             # 查看帮助
```

### 日志查看

程序运行日志保存在：
- **Windows**: `%LOCALAPPDATA%\MaHaLuDa\logs\mahaluda.log`
- **WSL/Linux**: `~/.mahaluda/logs/mahaluda.log`

## 工作原理

1. **热键监听**: 使用 `keyboard` 库监听全局热键（需要管理员权限）
2. **系统截图**: 触发 Windows 系统截图工具（Win+Shift+S）
3. **剪贴板轮询**: 轮询剪贴板检测截图数据（最长等待30秒）
4. **图像处理**: 使用 Pillow 保存图像到指定格式
5. **Git 操作**: 自动执行 `git add`、`commit`、`push`
6. **链接生成**: 根据配置生成 GitHub Raw URL

## 故障排除

### 托盘图标不显示

**原因**: 程序启动失败或依赖缺失

**排查步骤**:
1. 查看日志文件（路径见上方"日志查看"）
2. 检查是否有 `No module named 'pystray'` 错误
3. 确保以管理员身份运行

### 热键 Ctrl+Shift+A 无响应

**原因**: `keyboard` 库需要管理员权限才能注册全局热键

**解决方案**:
- **必须**以管理员身份运行程序
- 或使用托盘右键菜单 → "截图" 手动触发

### 剪贴板检测失败（超时30秒）

**可能原因**:
- 截图后超过30秒才完成选择
- 其他剪贴板管理工具拦截了截图数据
- Windows 系统截图工具未正常工作

**解决方案**:
- 截图后尽快完成区域选择
- 关闭剪贴板管理工具（如 Ditto、ClipboardFusion）后重试
- 手动按 `Win+Shift+S` 测试系统截图是否正常

### Git 推送失败

**可能原因**:
- `config.yaml` 中 `git.repo_path` 路径不存在或不是 Git 仓库
- Git 远程仓库凭据未配置
- 网络连接问题

**解决方案**:
- 确保 `repo_path` 指向有效的 Git 仓库（包含 `.git` 目录）
- 运行 `git push` 手动测试凭据和网络
- 检查 `github.username` 和 `github.repo_name` 是否正确

### WSL 环境中无法使用

**原因**: WSL 中无法调用 Windows 全局热键 API

**解决方案**:
- 直接在 Windows 中运行 exe，不要在 WSL 终端中启动

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
# 确保 pystray 已安装（托盘图标依赖）
pip install pystray

# 打包
pyinstaller build.spec --noconfirm
```

打包产物：
- `dist/MaHaLuDa.exe` — 单文件版（较大，启动稍慢）
- `dist/MaHaLuDa/MaHaLuDa.exe` — 文件夹版（推荐，启动快）

## 技术栈

- **Python 3.10+**
- **keyboard** — 全局热键监听
- **Pillow** — 图像处理和剪贴板截图获取
- **pystray** — 系统托盘图标
- **pyperclip** — 剪贴板复制
- **PyYAML** — 配置文件解析
- **loguru** — 结构化日志

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v2.1.0 (当前版本)
- 修复 Git 命令注入风险（commit_message 添加 `--` 终止符）
- 修复热键状态管理（unregister 异常后状态不一致）
- 添加路径穿越防护（target_folder 安全检查）
- 添加 HTML 转义（防止 XSS）
- 修复 PIL Image 资源泄漏
- 添加热键防抖（0.5秒间隔）
- 改进剪贴板轮询错误提示
- 使用 argparse 支持 `--help` 参数
- 优化配置加载（仅在补全时回写）

### v2.0.0
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
