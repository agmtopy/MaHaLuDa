# MaHaLuDa - Windows截图自动上传GitHub工具

一个轻量级的Windows截图工具，支持全局快捷键截图、预览确认后自动上传到GitHub并复制链接。

## 功能特性

- **全局快捷键截图**: 按 `Ctrl+Shift+A` 快速截图
- **区域选择**: 支持鼠标拖拽选择截图区域
- **多显示器支持**: 完美支持多显示器环境
- **预览确认**: 截图后弹出预览窗口，确认后上传
- **自动上传**: 通过本地Git自动上传到GitHub
- **链接复制**: 上传成功后自动复制GitHub Raw链接到剪贴板
- **系统托盘**: 最小化到系统托盘，后台运行

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

3. 运行程序
```bash
python src/main.py
```

### 使用打包版本

直接下载发布页面的 `MaHaLuDa.exe` 可执行文件。

## 配置

首次运行会在 `%LOCALAPPDATA%/MaHaLuDa/config.yaml` 创建配置文件。

### 必填配置项

```yaml
git:
  repo_path: "E:/Project/BlogImages"  # 本地Git仓库路径
  target_folder: "screenshots"         # 仓库内目标文件夹
  branch: "main"                       # 分支名称

github:
  username: "your-username"            # GitHub用户名
  repo_name: "BlogImages"              # GitHub仓库名
```

## 使用方法

1. 启动程序后，图标会显示在系统托盘
2. 按 `Ctrl+Shift+A` 触发截图
3. 鼠标拖拽选择截图区域
4. 在预览窗口中点击"上传"或按 `Enter` 确认
5. 等待上传完成，链接自动复制到剪贴板

## 开发

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

### 打包
```bash
pyinstaller build.spec
```

## 技术栈

- **Python 3.10+**
- **PyQt6**: GUI框架
- **mss**: 高性能截图库
- **keyboard**: 全局热键监听
- **Pillow**: 图像处理
- **PyYAML**: 配置管理

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！