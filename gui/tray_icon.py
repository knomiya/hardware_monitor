# gui/tray_icon.py
"""
系统托盘图标管理器
创建和管理系统托盘图标，提供菜单控制和状态更新
"""

import threading
import logging
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw, ImageFont
from utils.helpers import create_tray_image

class TrayIconManager:
    def __init__(self, app, update_interval=10):
        """
        初始化托盘图标管理器
        
        :param app: 主应用实例
        :param update_interval: 状态更新间隔（秒）
        """
        self.logger = logging.getLogger("TrayIcon")
        self.app = app
        self.update_interval = update_interval
        self.is_running = True
        self.icon = None
        self.current_text = "初始化..."
        
        # 创建初始图像
        self.image = create_tray_image(self.current_text)
        
        # 设置菜单
        self.menu = self._create_menu()
        
        self.logger.info("托盘图标管理器初始化完成")

    def _create_menu(self) -> Menu:
        """创建托盘图标菜单"""
        return Menu(
            MenuItem('显示悬浮窗', self.app.show_floating_window),
            MenuItem('设置', self.app.show_settings),
            Menu.SEPARATOR,
            MenuItem('关于', self.app.show_about),
            MenuItem('退出', self.app.quit)
        )

    def run(self):
        """启动托盘图标"""
        self.logger.info("启动托盘图标...")
        self.icon = Icon(
            "硬件监控",
            self.image,
            menu=self.menu,
            title="硬件温度监控"
        )
        
        # 启动更新线程
        threading.Thread(target=self.update_loop, daemon=True).start()
        
        # 在单独线程中运行图标
        threading.Thread(target=self.icon.run, daemon=True).start()
        self.logger.info("托盘图标已启动")

    def update_icon(self, text: str):
        """
        更新托盘图标显示的文本
        
        :param text: 要显示的文本（如"CPU: 45°C"）
        """
        self.current_text = text
        if not self.icon:
            return
            
        try:
            new_image = create_tray_image(text)
            if new_image:
                self.icon.icon = new_image
        except Exception as e:
            self.logger.error(f"更新托盘图标失败: {str(e)}")

    def blink_icon(self, message: str, times: int = 5, interval: float = 0.5):
        """
        闪烁托盘图标以引起注意
        
        :param message: 鼠标悬停时显示的消息
        :param times: 闪烁次数
        :param interval: 闪烁间隔（秒）
        """
        if not self.icon:
            return
            
        def blink_task():
            original_icon = self.icon.icon
            alert_icon = create_tray_image("!", bg_color="red")
            
            for _ in range(times):
                try:
                    self.icon.icon = alert_icon
                    self.icon.title = f"⚠️ {message}"
                    threading.Event().wait(interval)
                    
                    self.icon.icon = original_icon
                    self.icon.title = "硬件温度监控"
                    threading.Event().wait(interval)
                except Exception as e:
                    self.logger.error(f"闪烁托盘图标失败: {str(e)}")
                    break
            
            # 恢复原始状态
            try:
                self.icon.icon = original_icon
                self.icon.title = "硬件温度监控"
            except:
                pass
        
        # 在后台线程中运行闪烁
        threading.Thread(target=blink_task, daemon=True).start()

    def update_loop(self):
        """定期更新托盘图标状态"""
        while self.is_running:
            try:
                # 获取当前温度数据
                temps = self.app.monitor.get_current_temperatures()
                
                # 格式化文本（显示CPU温度）
                cpu_temp = temps.get('CPU', '--')
                text = f"CPU: {cpu_temp}°C"
                
                # 如果有告警，添加感叹号
                if any(self.app.alert_system.is_alert_active(dev) for dev in temps):
                    text = "⚠️ " + text
                
                # 更新图标
                self.update_icon(text)
                
                # 等待更新间隔
                threading.Event().wait(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"托盘更新循环出错: {str(e)}")
                threading.Event().wait(5)  # 出错后等待5秒

    def stop(self):
        """停止托盘图标"""
        self.is_running = False
        if self.icon:
            self.icon.stop()
        self.logger.info("托盘图标已停止")