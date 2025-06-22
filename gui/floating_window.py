# gui/floating_window.py
"""
悬浮窗口实现
显示硬件温度的实时数据，支持拖动和透明度调整
"""

import tkinter as tk
from tkinter import ttk
import logging
from utils.helpers import clamp

class FloatingWindow:
    def __init__(self, app, on_close=None):
        """
        初始化悬浮窗
        
        :param app: 主应用实例
        :param on_close: 窗口关闭时的回调函数
        """
        self.logger = logging.getLogger("FloatingWindow")
        self.app = app
        self.on_close = on_close or (lambda: None)
        self.window = None
        self.labels = {}
        self.temp_bars = {}
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        self._create_window()
        self.logger.info("悬浮窗初始化完成")

    def _create_window(self):
        """创建悬浮窗口"""
        self.window = tk.Tk()
        self.window.title("硬件温度监控")
        self.window.overrideredirect(True)  # 无边框
        self.window.attributes('-topmost', True)  # 置顶
        self.window.attributes('-alpha', 0.85)  # 透明度
        self.window.configure(bg='#2c3e50')  # 深蓝色背景
        
        # 关闭按钮
        close_btn = ttk.Button(
            self.window, text="×", width=2, 
            command=self.close, style='Close.TButton'
        )
        close_btn.pack(anchor='ne', padx=5, pady=5)
        
        # 设置按钮
        settings_btn = ttk.Button(
            self.window, text="⚙", width=2,
            command=self.app.show_settings, style='Settings.TButton'
        )
        settings_btn.pack(anchor='ne', padx=5, pady=5)
        
        # 添加设备温度显示
        devices = ['CPU', 'GPU', 'SSD']
        for device in devices:
            frame = ttk.Frame(self.window, padding=(10, 5))
            frame.pack(fill='x', padx=10, pady=5)
            
            # 设备标签
            label = ttk.Label(
                frame, text=f"{device}:", 
                font=("Arial", 10, "bold"), 
                foreground='#ecf0f1', background='#2c3e50'
            )
            label.pack(side='left')
            
            # 温度值
            temp_label = ttk.Label(
                frame, text="--°C", 
                font=("Arial", 10), 
                foreground='#ecf0f1', background='#2c3e50'
            )
            temp_label.pack(side='right')
            self.labels[device] = temp_label
            
            # 温度条
            bar = ttk.Progressbar(
                self.window, orient='horizontal', 
                length=200, mode='determinate'
            )
            bar.pack(fill='x', padx=10, pady=(0, 10))
            self.temp_bars[device] = bar
        
        # 样式配置
        self._configure_styles()
        
        # 绑定拖动事件
        self.window.bind("<ButtonPress-1>", self.start_drag)
        self.window.bind("<B1-Motion>", self.drag_window)
        self.window.bind("<ButtonRelease-1>", self.stop_drag)
        
        # 绑定鼠标滚轮调整透明度
        self.window.bind("<MouseWheel>", self.adjust_opacity)
        
        # 设置初始位置（屏幕右上角）
        screen_width = self.window.winfo_screenwidth()
        self.window.geometry(f"+{screen_width-320}+20")
        
        self.window.protocol("WM_DELETE_WINDOW", self.close)

    def _configure_styles(self):
        """配置窗口样式"""
        style = ttk.Style()
        
        # 关闭按钮样式
        style.configure(
            'Close.TButton', 
            background='#e74c3c', 
            foreground='white',
            font=("Arial", 8, "bold")
        )
        
        # 设置按钮样式
        style.configure(
            'Settings.TButton', 
            background='#3498db', 
            foreground='white',
            font=("Arial", 8)
        )
        
        # 温度条样式
        style.configure(
            "Horizontal.TProgressbar",
            background='#3498db',
            troughcolor='#34495e',
            thickness=10
        )

    def start_drag(self, event):
        """开始拖动窗口"""
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def drag_window(self, event):
        """拖动窗口"""
        if self.is_dragging:
            x = self.window.winfo_x() + (event.x - self.drag_start_x)
            y = self.window.winfo_y() + (event.y - self.drag_start_y)
            self.window.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        """停止拖动"""
        self.is_dragging = False

    def adjust_opacity(self, event):
        """使用鼠标滚轮调整窗口透明度"""
        current_opacity = self.window.attributes('-alpha')
        delta = 0.05 if event.delta > 0 else -0.05
        new_opacity = clamp(current_opacity + delta, 0.3, 1.0)
        self.window.attributes('-alpha', new_opacity)
        self.logger.info(f"窗口透明度调整为: {new_opacity:.2f}")

    def update_temps(self, temps: dict):
        """
        更新温度显示
        
        :param temps: 温度字典 {'CPU': 45.0, 'GPU': 60.0, 'SSD': 35.0}
        """
        if not self.window.winfo_exists():
            return
            
        try:
            for device, temp in temps.items():
                if device in self.labels:
                    # 更新温度文本
                    self.labels[device].config(text=f"{temp}°C" if temp is not None else "--°C")
                    
                    # 更新温度条
                    bar = self.temp_bars[device]
                    threshold = self.app.config.get_threshold(device)
                    
                    # 设置温度条值（0-100范围）
                    if temp is not None:
                        value = min(temp, threshold * 1.2)  # 上限为阈值的1.2倍
                        bar['value'] = (value / (threshold * 1.2)) * 100
                        
                        # 根据温度设置颜色
                        if temp > threshold:
                            bar.configure(style='Alert.Horizontal.TProgressbar')
                        else:
                            bar.configure(style='Normal.Horizontal.TProgressbar')
            
            # 更新窗口标题
            cpu_temp = temps.get('CPU', '--')
            self.window.title(f"CPU: {cpu_temp}°C")
            
        except Exception as e:
            self.logger.error(f"更新温度显示失败: {str(e)}")

    def show(self):
        """显示窗口"""
        if self.window.winfo_exists():
            self.window.deiconify()
        else:
            self._create_window()
        self.logger.info("显示悬浮窗")

    def hide(self):
        """隐藏窗口"""
        if self.window.winfo_exists():
            self.window.withdraw()
        self.logger.info("隐藏悬浮窗")

    def close(self):
        """关闭窗口（实际隐藏）"""
        self.hide()
        self.on_close()