# utils/notification.py
"""
系统通知管理模块
支持Windows通知中心、托盘图标闪烁和声音告警
"""

import logging
import platform
import time
import threading
from win10toast import ToastNotifier
from pystray import Icon

class NotificationManager:
    def __init__(self, app_name: str = "硬件监控"):
        """
        初始化通知管理器
        
        :param app_name: 应用名称（显示在通知中）
        """
        self.logger = logging.getLogger("NotificationManager")
        self.app_name = app_name
        self.sent_alerts = set()
        self.sound_enabled = True
        self.tray_icon = None
        
        # 初始化平台相关通知
        self.toaster = None
        if platform.system() == "Windows":
            try:
                self.toaster = ToastNotifier()
            except Exception as e:
                self.logger.error(f"初始化通知系统失败: {str(e)}")
                self.toaster = None
        
        self.logger.info(f"通知管理器初始化完成，系统: {platform.system()}")

    def send_alert(self, message: str, duration: int = 10):
        """
        发送系统通知
        
        :param message: 通知消息内容
        :param duration: 通知显示时间（秒）
        """
        if not message:
            return
            
        # 避免重复通知
        if message in self.sent_alerts:
            self.logger.debug(f"跳过重复通知: {message}")
            return
            
        self.logger.info(f"发送通知: {message}")
        self.sent_alerts.add(message)
        
        # 发送系统通知
        if self.toaster:
            try:
                self.toaster.show_toast(
                    self.app_name,
                    message,
                    duration=duration,
                    threaded=True
                )
            except Exception as e:
                self.logger.error(f"发送通知失败: {str(e)}")
        
        # 播放声音提示
        if self.sound_enabled:
            self.play_alert_sound()
        
        # 闪烁托盘图标（如果已设置）
        if self.tray_icon:
            self.blink_tray_icon(message)

    def reset_alerts(self):
        """重置已发送的告警记录"""
        self.sent_alerts.clear()
        self.logger.info("已重置通知记录")

    def play_alert_sound(self):
        """播放告警声音"""
        try:
            # Windows系统播放默认声音
            if platform.system() == "Windows":
                import winsound
                winsound.MessageBeep(winsound.MB_ICONWARNING)
            # macOS系统
            elif platform.system() == "Darwin":
                import os
                os.system('afplay /System/Library/Sounds/Ping.aiff &')
            # Linux系统
            else:
                import os
                os.system('paplay /usr/share/sounds/freedesktop/stereo/complete.oga &')
        except Exception as e:
            self.logger.error(f"播放声音失败: {str(e)}")

    def set_tray_icon(self, tray_icon: Icon):
        """设置托盘图标引用（用于闪烁效果）"""
        self.tray_icon = tray_icon

    def blink_tray_icon(self, message: str, times: int = 5, interval: float = 0.5):
        """
        闪烁托盘图标
        
        :param message: 鼠标悬停时显示的消息
        :param times: 闪烁次数
        :param interval: 闪烁间隔（秒）
        """
        if not self.tray_icon:
            return
            
        def blink_task():
            original_icon = self.tray_icon.icon
            alert_icon = self.create_alert_icon()
            
            for _ in range(times):
                try:
                    self.tray_icon.icon = alert_icon
                    self.tray_icon.title = f"⚠️ {message}"
                    time.sleep(interval)
                    
                    self.tray_icon.icon = original_icon
                    self.tray_icon.title = self.app_name
                    time.sleep(interval)
                except Exception as e:
                    self.logger.error(f"闪烁托盘图标失败: {str(e)}")
                    break
            
            # 恢复原始状态
            try:
                self.tray_icon.icon = original_icon
                self.tray_icon.title = self.app_name
            except:
                pass
        
        # 在后台线程中运行闪烁
        threading.Thread(target=blink_task, daemon=True).start()

    def create_alert_icon(self):
        """创建告警图标（红色背景）"""
        from PIL import Image, ImageDraw
        width, height = 64, 64
        image = Image.new('RGB', (width, height), "red")
        dc = ImageDraw.Draw(image)
        dc.rectangle([0, 0, width-1, height-1], outline="white")
        dc.text((width//2, height//2), "!", fill="white", anchor="mm", font_size=40)
        return image

    def enable_sound(self, enabled: bool):
        """启用或禁用声音提示"""
        self.sound_enabled = enabled
        self.logger.info(f"声音提示 {'启用' if enabled else '禁用'}")

# 测试通知功能
if __name__ == "__main__":
    import logging
    from utils.logger import setup_logging, get_logger
    
    setup_logging(log_level="DEBUG")
    logger = get_logger("TestNotification")
    
    notifier = NotificationManager("测试应用")
    notifier.send_alert("这是一条测试通知消息")
    
    # 测试闪烁效果
    from PIL import Image
    from pystray import Icon, Menu, MenuItem
    
    def setup_icon():
        image = Image.new('RGB', (64, 64), "blue")
        return image
    
    def on_quit():
        icon.stop()
    
    menu = Menu(MenuItem('退出', on_quit))
    icon = Icon("测试图标", setup_icon(), menu=menu)
    notifier.set_tray_icon(icon)
    
    # 启动图标和通知测试
    threading.Thread(target=icon.run, daemon=True).start()
    notifier.blink_tray_icon("测试闪烁消息")
    
    # 保持运行一段时间
    time.sleep(10)