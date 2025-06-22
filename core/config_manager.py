# core/config_manager.py
"""
配置管理模块
负责加载、保存和管理应用程序配置
"""

import configparser
import os
import json
import logging
from typing import Dict, Any, Optional, Union

class ConfigManager:
    def __init__(self, config_file: str = "settings.ini"):
        """
        初始化配置管理器
        
        :param config_file: 配置文件路径
        """
        self.logger = logging.getLogger("ConfigManager")
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.defaults = self._get_default_config()
        
        # 确保配置文件存在
        if not os.path.exists(self.config_file):
            self._create_default_config()
        
        self.load_config()
        self.logger.info("配置管理器初始化完成")

    def _get_default_config(self) -> Dict[str, Dict[str, Any]]:
        """获取默认配置"""
        return {
            'Thresholds': {
                'CPU': 85.0,
                'GPU': 90.0,
                'SSD': 70.0
            },
            'General': {
                'update_interval': 5.0,
                'start_minimized': False,
                'log_temperatures': True,
                'log_file': 'temperature_log.csv',
                'alert_cooldown': 300  # 5分钟
            },
            'Appearance': {
                'theme': 'dark',
                'font_size': 10,
                'opacity': 0.85
            },
            'Hardware': {
                'monitor_cpu': True,
                'monitor_gpu': True,
                'monitor_ssd': True
            }
        }

    def _create_default_config(self):
        """创建默认配置文件"""
        self.logger.info(f"创建默认配置文件: {self.config_file}")
        self.config.read_dict(self.defaults)
        self.save_config()

    def load_config(self):
        """加载配置文件"""
        try:
            self.config.read(self.config_file)
            self.logger.info(f"配置文件加载成功: {self.config_file}")
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            # 回退到默认配置
            self.config.read_dict(self.defaults)

    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            self.logger.info(f"配置文件已保存: {self.config_file}")
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {str(e)}")

    # ================== 阈值配置方法 ==================
    def get_threshold(self, device: str) -> float:
        """
        获取设备温度阈值
        
        :param device: 设备名称（'CPU', 'GPU', 'SSD'）
        :return: 温度阈值（摄氏度）
        """
        try:
            return self.config.getfloat('Thresholds', device)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            default_value = self.defaults['Thresholds'][device]
            self.set_threshold(device, default_value)
            return default_value

    def set_threshold(self, device: str, value: float):
        """
        设置设备温度阈值
        
        :param device: 设备名称
        :param value: 温度阈值（摄氏度）
        """
        if not self.config.has_section('Thresholds'):
            self.config.add_section('Thresholds')
        self.config.set('Thresholds', device, str(value))
        self.save_config()

    # ================== 常规配置方法 ==================
    def get_update_interval(self) -> float:
        """获取更新间隔（秒）"""
        try:
            return self.config.getfloat('General', 'update_interval')
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            default_value = self.defaults['General']['update_interval']
            self.set_update_interval(default_value)
            return default_value

    def set_update_interval(self, value: float):
        """设置更新间隔（秒）"""
        if not self.config.has_section('General'):
            self.config.add_section('General')
        self.config.set('General', 'update_interval', str(value))
        self.save_config()

    def get_start_minimized(self) -> bool:
        """获取是否最小化启动"""
        try:
            return self.config.getboolean('General', 'start_minimized')
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            default_value = self.defaults['General']['start_minimized']
            self.set_start_minimized(default_value)
            return default_value

    def set_start_minimized(self, value: bool):
        """设置是否最小化启动"""
        if not self.config.has_section('General'):
            self.config.add_section('General')
        self.config.set('General', 'start_minimized', str(value).lower())
        self.save_config()

    def get_log_temperatures(self) -> bool:
        """获取是否记录温度日志"""
        try:
            return self.config.getboolean('General', 'log_temperatures')
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            default_value = self.defaults['General']['log_temperatures']
            self.set_log_temperatures(default_value)
            return default_value

    def set_log_temperatures(self, value: bool):
        """设置是否记录温度日志"""
        if not self.config.has_section('General'):
            self.config.add_section('General')
        self.config.set('General', 'log_temperatures', str(value).lower())
        self.save_config()

    def get_log_path(self) -> str:
        """获取日志文件路径"""
        try:
            return self.config.get('General', 'log_file')
        except (configparser.NoSectionError, configparser.NoOptionError):
            default_value = self.defaults['General']['log_file']
            self.set_log_path(default_value)
            return default_value

    def set_log_path(self, value: str):
        """设置日志文件路径"""
        if not self.config.has_section('General'):
            self.config.add_section('General')
        self.config.set('General', 'log_file', value)
        self.save_config()

    def get_alert_cooldown(self) -> int:
        """获取告警冷却时间（秒）"""
        try:
            return self.config.getint('General', 'alert_cooldown')
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            default_value = self.defaults['General']['alert_cooldown']
            self.set_alert_cooldown(default_value)
            return default_value

    def set_alert_cooldown(self, value: int):
        """设置告警冷却时间（秒）"""
        if not self.config.has_section('General'):
            self.config.add_section('General')
        self.config.set('General', 'alert_cooldown', str(value))
        self.save_config()

    # ================== 外观配置方法 ==================
    def get_theme(self) -> str:
        """获取当前主题"""
        try:
            return self.config.get('Appearance', 'theme')
        except (configparser.NoSectionError, configparser.NoOptionError):
            default_value = self.defaults['Appearance']['theme']
            self.set_theme(default_value)
            return default_value

    def set_theme(self, value: str):
        """设置主题"""
        if not self.config.has_section('Appearance'):
            self.config.add_section('Appearance')
        self.config.set('Appearance', 'theme', value)
        self.save_config()

    def get_font_size(self) -> int:
        """获取字体大小"""
        try:
            return self.config.getint('Appearance', 'font_size')
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            default_value = self.defaults['Appearance']['font_size']
            self.set_font_size(default_value)
            return default_value

    def set_font_size(self, value: int):
        """设置字体大小"""
        if not self.config.has_section('Appearance'):
            self.config.add_section('Appearance')
        self.config.set('Appearance', 'font_size', str(value))
        self.save_config()

    def get_opacity(self) -> float:
        """获取窗口不透明度（0.0-1.0）"""
        try:
            return self.config.getfloat('Appearance', 'opacity')
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            default_value = self.defaults['Appearance']['opacity']
            self.set_opacity(default_value)
            return default_value

    def set_opacity(self, value: float):
        """设置窗口不透明度"""
        if not self.config.has_section('Appearance'):
            self.config.add_section('Appearance')
        self.config.set('Appearance', 'opacity', str(value))
        self.save_config()

    # ================== 硬件配置方法 ==================
    def get_monitor_state(self, device: str) -> bool:
        """
        获取是否监控指定设备
        
        :param device: 设备名称（'cpu', 'gpu', 'ssd'）
        :return: 是否监控
        """
        try:
            return self.config.getboolean('Hardware', f'monitor_{device.lower()}')
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            default_value = self.defaults['Hardware'][f'monitor_{device.lower()}']
            self.set_monitor_state(device, default_value)
            return default_value

    def set_monitor_state(self, device: str, value: bool):
        """
        设置是否监控指定设备
        
        :param device: 设备名称
        :param value: 是否监控
        """
        if not self.config.has_section('Hardware'):
            self.config.add_section('Hardware')
        self.config.set('Hardware', f'monitor_{device.lower()}', str(value).lower())
        self.save_config()

    # ================== 高级配置方法 ==================
    def export_config(self, file_path: str):
        """导出配置到JSON文件"""
        try:
            config_dict = {}
            for section in self.config.sections():
                config_dict[section] = dict(self.config.items(section))
            
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=4)
            
            self.logger.info(f"配置已导出到 {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"导出配置失败: {str(e)}")
            return False

    def import_config(self, file_path: str):
        """从JSON文件导入配置"""
        try:
            with open(file_path, 'r') as f:
                config_dict = json.load(f)
            
            for section, options in config_dict.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                for key, value in options.items():
                    self.config.set(section, key, str(value))
            
            self.save_config()
            self.logger.info(f"配置已从 {file_path} 导入")
            return True
        except Exception as e:
            self.logger.error(f"导入配置失败: {str(e)}")
            return False

    def reset_to_defaults(self):
        """重置为默认配置"""
        self.config.read_dict(self.defaults)
        self.save_config()
        self.logger.info("已重置为默认配置")