# main.py
"""
硬件温度监控系统 - 主程序
"""

import sys
import os
import time
import threading
import logging
from datetime import datetime
from core import hardware_reader, config_manager, alert_system
from gui import tray_icon, floating_window, settings_window
from utils import notification, logger as log_util

# 简化的虚拟环境检查
def in_virtual_environment():
    """检查是否在虚拟环境中运行"""
    # 检查 Conda 环境变量
    if os.environ.get('CONDA_DEFAULT_ENV'):
        return True
    
    # 检查虚拟环境目录是否存在
    if hasattr(sys, 'real_prefix'):
        return True
    
    # 检查 base_prefix 是否与 prefix 不同
    if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
        return True
    
    # 检查虚拟环境目录是否存在（备用方法）
    if 'VIRTUAL_ENV' in os.environ:
        return True
    
    return False

# 显示虚拟环境警告
if not in_virtual_environment():
    print("警告：未在虚拟环境中运行！")
    print("这可能导致依赖冲突和不可预测的行为。")
    print("请使用以下命令激活虚拟环境：")
    print("  conda activate hardware-monitor")
    print("或使用 run.bat 脚本启动程序")
    
    # 等待用户确认
    if sys.platform == "win32":
        input("按 Enter 继续运行（不推荐）或 Ctrl+C 退出...")
    else:
        print("按 Enter 继续运行（不推荐）或 Ctrl+C 退出...")
        input()

# 解决Windows系统DPI缩放问题
if sys.platform == "win32":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception as e:
        print(f"DPI设置失败: {str(e)}")

# 创建并运行应用
class MonitorApp:
    def __init__(self):
        # 初始化日志系统
        log_util.setup_logging(log_dir="logs")
        self.logger = logging.getLogger("MonitorApp")
        self.logger.info("应用程序启动中...")
        
        # 检查管理员权限（Windows需要管理员权限读取硬件）
        if sys.platform == "win32" and not self.is_admin():
            self.logger.warning("尝试以管理员权限重新运行")
            self.run_as_admin()
        
        # 加载配置
        self.config = config_manager.ConfigManager()
        
        # 初始化硬件监控
        self.hardware_reader = hardware_reader.HardwareReader()
        self.hardware_names = self.hardware_reader.get_hardware_names()
        self.logger.info(f"检测到的硬件: {self.hardware_names}")
        
        # 初始化告警系统
        self.alert_system = alert_system.AlertSystem(self.config)
        
        # 初始化通知系统
        self.notifier = notification.NotificationManager("硬件温度监控")
        
        # 初始化GUI组件
        self.tray_icon = tray_icon.TrayIconManager(self, self.config.get_update_interval())
        self.floating_win = floating_window.FloatingWindow(self, self.on_floating_window_close)
        self.settings_win = None
        
        # 监控状态
        self.is_running = True
        self.last_update_time = 0
        self.current_temps = {}
        self.alert_history = []
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(
            target=self.monitor_loop, 
            daemon=True,
            name="MonitorThread"
        )
        self.monitor_thread.start()
        
        # 启动系统托盘
        self.tray_icon.run()
        
        # 设置通知系统的托盘图标引用
        self.notifier.set_tray_icon(self.tray_icon.icon)
        
        # 检查是否最小化启动
        if not self.config.get_start_minimized():
            self.show_floating_window()
        
        self.logger.info("应用程序启动完成")

    def monitor_loop(self):
        """主监控循环"""
        while self.is_running:
            try:
                # 获取当前温度
                self.current_temps = self.hardware_reader.get_all_temperatures()
                self.logger.debug(f"当前温度: {self.current_temps}")
                
                # 更新UI
                self.update_ui()
                
                # 检查告警
                self.check_alerts()
                
                # 记录温度（如果配置启用）
                if self.config.get_log_temperatures():
                    self.log_temperatures()
                
            except Exception as e:
                self.logger.error(f"监控循环出错: {str(e)}", exc_info=True)
            
            # 按配置间隔休眠
            time.sleep(self.config.get_update_interval())
    
    def update_ui(self):
        """更新所有UI元素"""
        try:
            # 更新悬浮窗
            if self.floating_win.window.winfo_exists():
                self.floating_win.update_temps(self.current_temps)
            
            # 更新托盘图标（每10次更新一次）
            current_time = time.time()
            if current_time - self.last_update_time > 10:
                cpu_temp = self.current_temps.get('CPU', '--')
                tray_text = f"CPU: {cpu_temp}°C"
                self.tray_icon.update_icon(tray_text)
                self.last_update_time = current_time
        
        except Exception as e:
            self.logger.error(f"更新UI出错: {str(e)}")
    
    def check_alerts(self):
        """检查并处理告警"""
        alerts = self.alert_system.check_thresholds(self.current_temps)
        for alert in alerts:
            # 记录告警历史
            self.alert_history.append({
                'time': datetime.now(),
                'message': alert
            })
            
            # 保留最近100条告警
            if len(self.alert_history) > 100:
                self.alert_history.pop(0)
            
            self.logger.warning(alert)
            self.notifier.send_alert(alert)
            
            # 如果悬浮窗未显示，闪烁托盘图标
            if not self.floating_win.window.winfo_exists():
                self.tray_icon.blink_icon(alert)
    
    def log_temperatures(self):
        """记录温度到CSV文件"""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = f"{timestamp}, "
            log_entry += f"{self.current_temps.get('CPU', '')}, "
            log_entry += f"{self.current_temps.get('GPU', '')}, "
            log_entry += f"{self.current_temps.get('SSD', '')}\n"
            
            # 确保数据目录存在
            if not os.path.exists("data"):
                os.makedirs("data")
            
            with open(self.config.get_log_path(), "a", encoding="utf-8") as log_file:
                log_file.write(log_entry)
        except Exception as e:
            self.logger.error(f"记录温度失败: {str(e)}")
    
    def show_floating_window(self):
        """显示悬浮窗"""
        self.floating_win.show()
        self.floating_win.update_temps(self.current_temps)
        self.logger.info("显示悬浮窗")
    
    def on_floating_window_close(self):
        """悬浮窗关闭时的回调"""
        self.logger.info("悬浮窗已关闭")
    
    def show_settings(self):
        """显示设置窗口"""
        if self.settings_win is None or not self.settings_win.window.winfo_exists():
            self.settings_win = settings_window.SettingsWindow(
                self,
                on_save=self.on_settings_saved
            )
        self.settings_win.show()
        self.logger.info("显示设置窗口")
    
    def on_settings_saved(self):
        """设置保存后的回调"""
        self.logger.info("配置已更新")
        
        # 重置告警状态
        self.alert_system.update_config()
        self.notifier.reset_alerts()
        
        # 更新监控间隔
        self.tray_icon.update_interval = self.config.get_update_interval()
        
        # 更新悬浮窗（如果显示）
        if self.floating_win.window.winfo_exists():
            self.floating_win.update_temps(self.current_temps)
    
    def show_about(self):
        """显示关于窗口"""
        # 在实际实现中，这里会显示一个关于对话框
        self.logger.info("显示关于信息")
        self.notifier.send_alert("硬件温度监控 v1.0\n作者: 您的名字")
    
    def quit(self):
        """退出应用程序"""
        self.logger.info("正在退出应用程序...")
        self.is_running = False
        
        # 保存配置
        self.config.save()
        
        # 关闭所有窗口
        if self.floating_win.window.winfo_exists():
            self.floating_win.close()
        
        if self.settings_win and self.settings_win.window.winfo_exists():
            self.settings_win.close()
        
        # 关闭托盘图标
        self.tray_icon.stop()
        
        self.logger.info("应用程序已退出")
        sys.exit(0)
    
    def is_admin(self) -> bool:
        """检查是否以管理员权限运行（仅Windows）"""
        if sys.platform != "win32":
            return True
            
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def run_as_admin(self):
        """以管理员权限重新运行程序（仅Windows）"""
        if sys.platform != "win32":
            return
            
        try:
            import ctypes
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)
        except Exception as e:
            self.logger.error(f"请求管理员权限失败: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    # 创建并运行应用
    try:
        app = MonitorApp()
        
        # 启动tkinter主循环（如果使用tkinter）
        if app.floating_win.window.winfo_exists():
            app.floating_win.window.mainloop()
        else:
            # 如果没有显示悬浮窗，保持主线程运行
            while app.is_running:
                time.sleep(1)
    except Exception as e:
        import traceback
        print(f"应用程序崩溃: {str(e)}")
        print(traceback.format_exc())
        input("按 Enter 退出...")
        sys.exit(1)