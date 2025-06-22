# core/alert_system.py
"""
告警系统模块
负责检查温度是否超过阈值，管理告警状态和冷却机制
"""

import time
import logging
from typing import Dict, Optional, List

class AlertSystem:
    def __init__(self, config_manager):
        """
        初始化告警系统
        
        :param config_manager: 配置管理器实例
        """
        self.logger = logging.getLogger("AlertSystem")
        self.config = config_manager
        
        # 告警状态记录
        self.alert_states = {
            'CPU': {'active': False, 'last_triggered': 0},
            'GPU': {'active': False, 'last_triggered': 0},
            'SSD': {'active': False, 'last_triggered': 0}
        }
        
        # 告警冷却时间（秒）
        self.cooldown_period = self.config.get_alert_cooldown()
        
        # 自定义告警动作
        self.custom_alert_actions = {}
        
        self.logger.info("告警系统初始化完成")

    def check_thresholds(self, temperatures: Dict[str, Optional[float]]) -> List[str]:
        """
        检查温度是否超过阈值，返回告警消息列表
        
        :param temperatures: 当前温度数据字典
        :return: 告警消息列表（如：["CPU温度过高: 90°C (阈值: 85°C)"]）
        """
        alerts = []
        current_time = time.time()
        
        for device, temp in temperatures.items():
            if temp is None:
                continue
                
            threshold = self.config.get_threshold(device)
            
            # 如果温度超过阈值
            if temp > threshold:
                # 检查是否在冷却期内
                last_triggered = self.alert_states[device]['last_triggered']
                if current_time - last_triggered < self.cooldown_period:
                    self.logger.debug(f"{device}告警在冷却期内，跳过")
                    continue
                
                # 更新告警状态
                self.alert_states[device]['active'] = True
                self.alert_states[device]['last_triggered'] = current_time
                
                # 生成告警消息
                alert_msg = f"{device}温度过高: {temp}°C (阈值: {threshold}°C)"
                alerts.append(alert_msg)
                
                # 执行自定义告警动作（如果存在）
                if device in self.custom_alert_actions:
                    self.logger.info(f"执行{device}的自定义告警动作")
                    self.custom_alert_actions[device]()
            else:
                # 如果温度恢复正常
                if self.alert_states[device]['active']:
                    self.alert_states[device]['active'] = False
                    recovery_msg = f"{device}温度已恢复正常: {temp}°C"
                    alerts.append(recovery_msg)
                    self.logger.info(recovery_msg)
        
        return alerts

    def is_alert_active(self, device: str) -> bool:
        """
        检查指定设备是否有活跃告警
        
        :param device: 设备名称（'CPU', 'GPU', 'SSD'）
        :return: 是否有活跃告警
        """
        return self.alert_states.get(device, {}).get('active', False)

    def get_last_alert_time(self, device: str) -> float:
        """
        获取设备上次触发告警的时间戳
        
        :param device: 设备名称
        :return: Unix时间戳
        """
        return self.alert_states.get(device, {}).get('last_triggered', 0)

    def reset_alert(self, device: str):
        """
        重置指定设备的告警状态
        
        :param device: 设备名称
        """
        if device in self.alert_states:
            self.alert_states[device]['active'] = False
            self.logger.info(f"已重置{device}的告警状态")

    def set_custom_alert_action(self, device: str, action: callable):
        """
        为特定设备设置自定义告警动作
        
        :param device: 设备名称
        :param action: 无参数的回调函数
        """
        self.custom_alert_actions[device] = action
        self.logger.info(f"已为{device}设置自定义告警动作")

    def update_config(self):
        """
        更新配置（当配置改变时调用）
        """
        self.cooldown_period = self.config.get_alert_cooldown()
        self.logger.info(f"告警系统配置已更新，冷却时间: {self.cooldown_period}秒")