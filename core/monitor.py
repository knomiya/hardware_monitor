# core/monitor.py
"""
硬件温度监控核心模块
负责定时采集硬件温度数据、检查告警阈值、记录日志和协调UI更新
"""

import time
import threading
import logging
from datetime import datetime
from typing import Dict, Optional, Callable

class HardwareMonitor:
    def __init__(self, config_manager, hardware_reader, alert_system):
        """
        初始化硬件监控器
        
        :param config_manager: 配置管理实例
        :param hardware_reader: 硬件数据读取器实例
        :param alert_system: 告警系统实例
        """
        self.logger = logging.getLogger("HardwareMonitor")
        self.config = config_manager
        self.hardware_reader = hardware_reader
        self.alert_system = alert_system
        
        # 监控状态
        self.is_running = False
        self.last_temperatures = {}
        self.current_temperatures = {}
        self.last_alert_time = {}
        
        # 回调函数
        self.ui_update_callback = None
        self.alert_callback = None
        self.log_callback = None
        
        # 监控线程
        self.monitor_thread = None
        self.update_interval = self.config.get_update_interval()
        
        self.logger.info("硬件监控器初始化完成")

    def start_monitoring(self):
        """启动监控循环"""
        if self.is_running:
            self.logger.warning("监控已启动，无需重复启动")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="HardwareMonitorThread"
        )
        self.monitor_thread.start()
        self.logger.info("硬件监控已启动")

    def stop_monitoring(self):
        """停止监控循环"""
        if not self.is_running:
            self.logger.warning("监控未运行，无需停止")
            return
        
        self.is_running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        self.logger.info("硬件监控已停止")

    def _monitor_loop(self):
        """监控主循环"""
        self.logger.info("监控循环开始运行")
        
        # 初始化上次温度记录
        self.last_temperatures = self.hardware_reader.get_all_temperatures()
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # 获取当前温度
                self.current_temperatures = self.hardware_reader.get_all_temperatures()
                
                # 检查数据有效性
                if not self._validate_temperatures():
                    time.sleep(self.update_interval)
                    continue
                
                # 更新UI
                self._update_ui()
                
                # 检查告警
                self._check_alerts()
                
                # 记录温度数据
                self._log_temperatures()
                
                # 更新上次温度记录
                self.last_temperatures = self.current_temperatures.copy()
                
                # 计算实际休眠时间（考虑操作耗时）
                elapsed = time.time() - start_time
                sleep_time = max(0.5, self.update_interval - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"监控循环异常: {str(e)}", exc_info=True)
                time.sleep(5)  # 出错后短暂休眠
        
        self.logger.info("监控循环退出")

    def _validate_temperatures(self) -> bool:
        """验证温度数据有效性"""
        # 检查是否有有效数据
        if not any(temp is not None for temp in self.current_temperatures.values()):
            self.logger.warning("未获取到有效温度数据")
            return False
        
        # 检查数据异常波动（可选功能）
        for device, temp in self.current_temperatures.items():
            last_temp = self.last_temperatures.get(device)
            
            if temp is None or last_temp is None:
                continue
                
            # 温度在1秒内变化超过20°C视为异常
            if abs(temp - last_temp) > 20:
                self.logger.warning(
                    f"{device}温度异常波动: {last_temp}°C → {temp}°C"
                )
                return False
        
        return True

    def _update_ui(self):
        """触发UI更新回调"""
        if callable(self.ui_update_callback):
            try:
                self.ui_update_callback(self.current_temperatures)
            except Exception as e:
                self.logger.error(f"UI更新回调失败: {str(e)}")

    def _check_alerts(self):
        """检查并处理告警"""
        alerts = self.alert_system.check_thresholds(self.current_temperatures)
        
        for alert in alerts:
            device = alert.split()[0]  # 提取设备名
            
            # 避免重复告警
            last_alert = self.last_alert_time.get(device, 0)
            cooldown = self.config.get_alert_cooldown()
            
            if time.time() - last_alert < cooldown:
                self.logger.debug(f"跳过重复告警: {alert}")
                continue
                
            # 记录告警时间
            self.last_alert_time[device] = time.time()
            
            # 触发告警回调
            if callable(self.alert_callback):
                try:
                    self.alert_callback(alert)
                except Exception as e:
                    self.logger.error(f"告警回调失败: {str(e)}")
            
            self.logger.warning(alert)

    def _log_temperatures(self):
        """记录温度数据"""
        if not self.config.get_log_temperatures():
            return
            
        if callable(self.log_callback):
            try:
                self.log_callback(self.current_temperatures)
            except Exception as e:
                self.logger.error(f"日志记录回调失败: {str(e)}")

    def get_current_temperatures(self) -> Dict[str, Optional[float]]:
        """获取当前温度数据"""
        return self.current_temperatures.copy()

    def set_ui_update_callback(self, callback: Callable[[Dict[str, float]], None]):
        """设置UI更新回调函数"""
        self.ui_update_callback = callback

    def set_alert_callback(self, callback: Callable[[str], None]):
        """设置告警回调函数"""
        self.alert_callback = callback

    def set_log_callback(self, callback: Callable[[Dict[str, float]], None]):
        """设置日志记录回调函数"""
        self.log_callback = callback

    def set_update_interval(self, interval: float):
        """设置监控更新间隔（秒）"""
        if interval < 1:
            self.logger.warning(f"更新间隔过短: {interval}秒，已设置为最小值1秒")
            self.update_interval = 1.0
        else:
            self.update_interval = float(interval)
        self.logger.info(f"更新间隔设置为: {self.update_interval}秒")