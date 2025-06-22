# gui/alert_window.py
"""
告警窗口实现
当温度超过阈值时弹出告警窗口
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import time
from utils.helpers import clamp

class AlertWindow:
    def __init__(self, app):
        """
        初始化告警窗口
        
        :param app: 主应用实例
        """
        self.logger = logging.getLogger("AlertWindow")
        self.app = app
        self.window = None
        self.active_alerts = set()
        
        self.logger.info("告警窗口初始化完成")

    def show_alert(self, message: str, duration: int = 10):
        """
        显示告警窗口
        
        :param message: 告警消息
        :param duration: 显示时间（秒），0表示一直显示
        """
        if message in self.active_alerts:
            return
            
        self.active_alerts.add(message)
        
        # 在单独线程中显示窗口
        threading.Thread(
            target=self._show_alert_thread, 
            args=(message, duration),
            daemon=True
        ).start()

    def _show_alert_thread(self, message: str, duration: int):
        """在单独线程中显示告警窗口"""
        try:
            # 创建窗口
            self.window = tk.Toplevel()
            self.window.title("温度警告!")
            self.window.attributes('-topmost', True)
            self.window.resizable(False, False)
            self.window.configure(bg='#e74c3c')  # 红色背景
            
            # 设置位置（屏幕中央）
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            window_width = 400
            window_height = 150
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # 告警图标
            icon_label = ttk.Label(
                self.window, 
                text="⚠️", 
                font=("Arial", 24),
                background='#e74c3c',
                foreground='white'
            )
            icon_label.pack(pady=(10, 0))
            
            # 告警消息
            msg_label = ttk.Label(
                self.window, 
                text=message, 
                font=("Arial", 12, "bold"),
                wraplength=380,
                justify='center',
                background='#e74c3c',
                foreground='white'
            )
            msg_label.pack(pady=10, padx=20, fill='both')
            
            # 确认按钮
            btn_frame = ttk.Frame(self.window)
            btn_frame.pack(pady=10)
            
            ok_btn = ttk.Button(
                btn_frame, 
                text="知道了", 
                command=self._close_alert,
                style='Alert.TButton'
            )
            ok_btn.pack(pady=5)
            
            # 应用样式
            self._configure_styles()
            
            # 如果设置了持续时间，自动关闭
            if duration > 0:
                self.window.after(duration * 1000, self._close_alert)
            
            self.logger.info(f"显示告警: {message}")
            self.window.mainloop()
            
        except Exception as e:
            self.logger.error(f"显示告警窗口失败: {str(e)}")
        finally:
            self.active_alerts.discard(message)

    def _configure_styles(self):
        """配置窗口样式"""
        style = ttk.Style()
        style.configure(
            'Alert.TButton', 
            background='#c0392b', 
            foreground='white',
            font=("Arial", 10, "bold")
        )

    def _close_alert(self):
        """关闭当前告警窗口"""
        if self.window and self.window.winfo_exists():
            self.window.destroy()
        self.logger.info("告警窗口已关闭")