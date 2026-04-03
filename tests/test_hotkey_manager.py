"""热键管理器测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.hotkey_manager import HotkeyManager
from src.core.config_manager import HotkeyConfig


class TestHotkeyManager:
    """热键管理器测试类"""

    def test_init(self):
        """测试初始化"""
        config = HotkeyConfig(key="ctrl+a", enabled=True)
        manager = HotkeyManager(config)

        assert manager.config == config
        assert manager.callback is None
        assert manager.is_registered is False

    def test_set_callback(self):
        """测试设置回调函数"""
        config = HotkeyConfig()
        manager = HotkeyManager(config)

        callback = Mock()
        manager.set_callback(callback)

        assert manager.callback == callback

    @patch('keyboard.add_hotkey')
    @patch('keyboard.is_hotkey_registered', create=True)
    def test_register_success(self, mock_is_registered, mock_add_hotkey):
        """测试成功注册热键"""
        mock_is_registered.return_value = False
        mock_add_hotkey.return_value = True

        config = HotkeyConfig(key="ctrl+shift+a", enabled=True)
        manager = HotkeyManager(config)

        result = manager.register()

        assert result is True
        assert manager.is_registered is True
        mock_add_hotkey.assert_called_once()

    @patch('keyboard.remove_hotkey')
    def test_unregister(self, mock_remove_hotkey):
        """测试注销热键"""
        config = HotkeyConfig()
        manager = HotkeyManager(config)
        manager.is_registered = True

        manager.unregister()

        assert manager.is_registered is False
        mock_remove_hotkey.assert_called_once()

    def test_unregister_when_not_registered(self):
        """测试未注册时注销"""
        config = HotkeyConfig()
        manager = HotkeyManager(config)
        manager.is_registered = False

        # 不应该抛出异常
        manager.unregister()

        assert manager.is_registered is False

    def test_disabled_hotkey(self):
        """测试禁用热键"""
        config = HotkeyConfig(key="ctrl+a", enabled=False)
        manager = HotkeyManager(config)

        result = manager.register()

        assert result is False
        assert manager.is_registered is False

    @patch('keyboard.add_hotkey')
    @patch('keyboard.is_hotkey_registered', create=True)
    def test_reregister(self, mock_is_registered, mock_add_hotkey):
        """测试重复注册"""
        mock_is_registered.return_value = False
        mock_add_hotkey.return_value = True

        config = HotkeyConfig()
        manager = HotkeyManager(config)

        # 第一次注册
        result1 = manager.register()
        assert result1 is True

        # 重置mock
        mock_add_hotkey.reset_mock()

        # 第二次注册（应该先注销旧的）
        result2 = manager.register()
        assert result2 is True

    def test_trigger_callback(self):
        """测试触发回调"""
        config = HotkeyConfig()
        manager = HotkeyManager(config)

        callback = Mock()
        manager.set_callback(callback)

        manager._on_hotkey_pressed()

        callback.assert_called_once()

    def test_trigger_callback_when_none(self):
        """测试回调为None时触发"""
        config = HotkeyConfig()
        manager = HotkeyManager(config)

        # 不应该抛出异常
        manager._on_hotkey_pressed()

    @patch('keyboard.add_hotkey')
    @patch('keyboard.is_hotkey_registered', create=True)
    def test_update_hotkey(self, mock_is_registered, mock_add_hotkey):
        """测试更新热键"""
        mock_is_registered.return_value = False
        mock_add_hotkey.return_value = True

        config = HotkeyConfig(key="ctrl+a")
        manager = HotkeyManager(config)

        manager.register()

        # 更新热键
        new_config = HotkeyConfig(key="ctrl+b")
        manager.update_hotkey(new_config)

        assert manager.config == new_config

    @patch('keyboard.add_hotkey')
    def test_register_failure(self, mock_add_hotkey):
        """测试注册失败"""
        mock_add_hotkey.side_effect = Exception("Failed to register")

        config = HotkeyConfig()
        manager = HotkeyManager(config)

        result = manager.register()

        assert result is False
        assert manager.is_registered is False