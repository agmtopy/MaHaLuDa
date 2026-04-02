# SettingsDialog 配置修复测试计划

## 上下文

修复了 `src/gui/settings_dialog.py` 中的两个关键问题：
1. **取消按钮无法恢复配置**：`_on_cancel` 方法错误地替换对象引用而不是恢复属性值
2. **验证失败时污染配置**：`_apply_settings` 先修改配置再验证，导致验证失败时配置已被污染

修复内容：
- 添加了 `_collect_settings()` - 收集UI设置到临时Config对象
- 添加了 `_copy_config_values()` - 将配置值从一个对象复制到另一个
- 添加了 `_restore_config()` - 从备份恢复配置值
- 重构了 `_apply_settings()` - 先验证再应用
- 修复了 `_on_cancel()` - 正确恢复属性值

## 测试目标

验证修复后的 `SettingsDialog` 行为正确：
1. 点击"确定"时，验证通过后配置才生效
2. 点击"应用"时，验证通过后配置才生效
3. 点击"取消"时，配置完全恢复到修改前的状态
4. 验证失败时，原始配置不被修改
5. 配置修改正确保存到文件

## 测试策略

使用 pytest-qt 进行 Qt 组件测试，利用 `qtbot` fixture 模拟用户交互。

## 测试文件

创建 `tests/test_settings_dialog.py` ✅ **已完成**

## 测试用例设计

### 测试类：TestSettingsDialog

#### 1. test_apply_valid_settings ✅ **已完成**
**目的**: 验证有效设置能正确应用
**步骤**:
- 创建 Config 对象，设置初始值
- 创建 SettingsDialog，修改UI中的值
- 调用 `_apply_settings()`
**断言**:
- 返回 True
- 配置对象的值已更新
- 配置文件已保存

#### 2. test_apply_invalid_settings ✅ **已完成**
**目的**: 验证无效设置不会污染原配置
**步骤**:
- 创建有效的初始 Config
- 在UI中输入无效值（如空仓库路径）
- 调用 `_apply_settings()`
**断言**:
- 返回 False
- 原始配置值保持不变

#### 3. test_cancel_restores_original_config ✅ **已完成**
**目的**: 验证取消按钮能恢复原始配置
**步骤**:
- 创建 Config 对象，记录初始值
- 创建 SettingsDialog，修改多个UI字段
- 调用 `_on_cancel()`
**断言**:
- 配置对象的所有值恢复到初始状态

#### 4. test_collect_settings_creates_new_config ✅ **已完成**
**目的**: 验证 `_collect_settings` 创建独立对象
**步骤**:
- 创建 SettingsDialog
- 修改UI值
- 调用 `_collect_settings()`
**断言**:
- 返回新的 Config 对象
- 新对象的值与UI一致
- 原 config 对象未被修改

#### 5. test_copy_config_values ✅ **已完成**
**目的**: 验证 `_copy_config_values` 正确复制所有字段
**步骤**:
- 创建源 Config，设置所有字段为特定值
- 创建目标 Config，使用默认值
- 调用 `_copy_config_values(source, target)`
**断言**:
- 目标对象的所有字段与源对象一致

#### 6. test_restore_config ✅ **已完成**
**目的**: 验证 `_restore_config` 正确恢复所有字段
**步骤**:
- 创建原始 Config，设置特定值
- 修改 config 的所有字段
- 调用 `_restore_config(original)`
**断言**:
- config 的所有字段恢复到原始值

#### 7. test_ok_button_applies_settings ✅ **已完成**
**目的**: 验证点击确定按钮应用设置（集成测试）
**步骤**:
- 使用 qtbot 创建对话框
- 修改UI字段
- 点击确定按钮
**断言**:
- 对话框 accepted
- 配置已更新

#### 8. test_cancel_button_restores_settings ✅ **已完成**
**目的**: 验证点击取消按钮恢复设置（集成测试）
**步骤**:
- 使用 qtbot 创建对话框
- 记录原始值
- 修改UI字段
- 点击取消按钮
**断言**:
- 对话框 rejected
- 配置恢复到原始值

## 关键实现细节

### 测试辅助方法访问
由于 `_collect_settings`, `_copy_config_values`, `_restore_config` 是私有方法，测试中将直接调用它们来验证行为。

### Qt 测试要求
- 需要显示环境（或虚拟显示如 xvfb）
- 使用 `qtbot.addWidget(dialog)` 管理窗口生命周期
- 使用 `qtbot.mouseClick` 模拟按钮点击

### 文件系统隔离
- 使用 `tempfile.TemporaryDirectory` 创建临时配置文件
- 每个测试独立，避免相互影响

## 验证步骤

1. ✅ 创建测试文件：`tests/test_settings_dialog.py` **已完成**
2. ⏳ 运行新测试：`pytest tests/test_settings_dialog.py -v` **待执行**
   - 需要安装依赖：`pip install pytest pytest-qt PyQt6`
   - 在WSL环境需要虚拟显示或Windows环境运行
3. ⏳ 运行所有测试：`pytest tests/ -v` **待执行**
4. ⏳ 验证代码覆盖率（如配置了 pytest-cov）**待执行**

## 测试文件状态

- **文件创建**: ✅ 已完成
- **语法检查**: ✅ 已完成（通过 `python3 -m py_compile` 验证）
- **依赖安装**: ❌ 未完成
  - pytest 未安装
  - pytest-qt 未安装
  - PyQt6 未安装
- **测试执行**: ❌ 未完成（需要先安装依赖）

## 风险与注意事项

1. **Qt 测试需要显示环境**：在无头环境（如 CI）中需要使用 xvfb-run
2. **文件路径**：Windows 和 Linux 路径处理差异
3. **信号槽连接**：确保 Qt 信号正确触发

## 完成情况总结

| 任务 | 状态 | 说明 |
|------|------|------|
| 测试计划设计 | ✅ 完成 | 8个测试用例已设计 |
| 测试文件创建 | ✅ 完成 | `tests/test_settings_dialog.py` 已创建 |
| 测试代码编写 | ✅ 完成 | 所有8个测试用例代码已编写 |
| 语法验证 | ✅ 完成 | Python语法正确 |
| 依赖环境准备 | ❌ 未完成 | 需要安装pytest, pytest-qt, PyQt6 |
| 测试执行 | ❌ 未完成 | 需要在配置好环境后执行 |
| 测试通过验证 | ❌ 未完成 | 等待测试执行结果 |

## 下一步行动

1. 安装测试依赖：
   ```bash
   pip install pytest pytest-qt PyQt6
   ```

2. 在Windows环境下运行测试（推荐，因为有GUI）：
   ```bash
   pytest tests/test_settings_dialog.py -v
   ```

3. 或在WSL环境使用虚拟显示运行：
   ```bash
   xvfb-run pytest tests/test_settings_dialog.py -v
   ```

4. 验证所有测试通过后，运行完整测试套件：
   ```bash
   pytest tests/ -v
   ```