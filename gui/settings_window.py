# gui/settings_window.py
"""
设置窗口实现
允许用户配置温度阈值、监控间隔等设置
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from utils.helpers import clamp

class SettingsWindow:
    def __init__(self, app, on_save=None):
        """
        初始化设置窗口
        
        :param app: 主应用实例
        :param on_save: 保存设置时的回调函数
        """
        self.logger = logging.getLogger("SettingsWindow")
        self.app = app
        self.on_save = on_save or (lambda: None)
        self.window = None
        
        self._create_window()
        self.logger.info("设置窗口初始化完成")

    def _create_window(self):
        """创建设置窗口"""
        self.window = tk.Toplevel()
        self.window.title("设置")
        self.window.geometry("400x500")
        self.window.resizable(False, False)
        self.window.transient(self.app.floating_win.window)  # 设置为主窗口的子窗口
        self.window.grab_set()  # 模态对话框
        
        # 创建标签页
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 阈值设置标签页
        thresholds_frame = ttk.Frame(notebook, padding=10)
        notebook.add(thresholds_frame, text="温度阈值")
        self._create_thresholds_tab(thresholds_frame)
        
        # 常规设置标签页
        general_frame = ttk.Frame(notebook, padding=10)
        notebook.add(general_frame, text="常规设置")
        self._create_general_tab(general_frame)
        
        # 外观设置标签页
        appearance_frame = ttk.Frame(notebook, padding=10)
        notebook.add(appearance_frame, text="外观")
        self._create_appearance_tab(appearance_frame)
        
        # 按钮框架
        btn_frame = ttk.Frame(self.window, padding=10)
        btn_frame.pack(fill='x', side='bottom')
        
        # 保存按钮
        save_btn = ttk.Button(
            btn_frame, text="保存", 
            command=self.save_settings, 
            style='Accent.TButton'
        )
        save_btn.pack(side='right', padx=5)
        
        # 取消按钮
        cancel_btn = ttk.Button(
            btn_frame, text="取消", 
            command=self.close
        )
        cancel_btn.pack(side='right', padx=5)
        
        # 应用样式
        self._configure_styles()
        
        self.window.protocol("WM_DELETE_WINDOW", self.close)

    def _create_thresholds_tab(self, parent):
        """创建阈值设置标签页"""
        # CPU阈值
        cpu_frame = ttk.Frame(parent)
        cpu_frame.pack(fill='x', pady=5)
        ttk.Label(cpu_frame, text="CPU阈值 (°C):").pack(side='left')
        self.cpu_threshold = ttk.Spinbox(
            cpu_frame, from_=50, to=100, width=5,
            validate="key", validatecommand=(parent.register(self._validate_temp), '%P')
        )
        self.cpu_threshold.pack(side='right')
        self.cpu_threshold.set(self.app.config.get_threshold('CPU'))
        
        # GPU阈值
        gpu_frame = ttk.Frame(parent)
        gpu_frame.pack(fill='x', pady=5)
        ttk.Label(gpu_frame, text="GPU阈值 (°C):").pack(side='left')
        self.gpu_threshold = ttk.Spinbox(
            gpu_frame, from_=60, to=110, width=5,
            validate="key", validatecommand=(parent.register(self._validate_temp), '%P')
        )
        self.gpu_threshold.pack(side='right')
        self.gpu_threshold.set(self.app.config.get_threshold('GPU'))
        
        # SSD阈值
        ssd_frame = ttk.Frame(parent)
        ssd_frame.pack(fill='x', pady=5)
        ttk.Label(ssd_frame, text="SSD阈值 (°C):").pack(side='left')
        self.ssd_threshold = ttk.Spinbox(
            ssd_frame, from_=40, to=80, width=5,
            validate="key", validatecommand=(parent.register(self._validate_temp), '%P')
        )
        self.ssd_threshold.pack(side='right')
        self.ssd_threshold.set(self.app.config.get_threshold('SSD'))
        
        # 告警冷却时间
        cooldown_frame = ttk.Frame(parent)
        cooldown_frame.pack(fill='x', pady=5)
        ttk.Label(cooldown_frame, text="告警冷却时间 (分钟):").pack(side='left')
        self.alert_cooldown = ttk.Spinbox(
            cooldown_frame, from_=1, to=60, width=5,
            validate="key", validatecommand=(parent.register(self._validate_int), '%P')
        )
        self.alert_cooldown.pack(side='right')
        self.alert_cooldown.set(self.app.config.get_alert_cooldown() // 60)

    def _create_general_tab(self, parent):
        """创建常规设置标签页"""
        # 更新间隔
        interval_frame = ttk.Frame(parent)
        interval_frame.pack(fill='x', pady=5)
        ttk.Label(interval_frame, text="更新间隔 (秒):").pack(side='left')
        self.update_interval = ttk.Spinbox(
            interval_frame, from_=1, to=60, width=5,
            validate="key", validatecommand=(parent.register(self._validate_int), '%P')
        )
        self.update_interval.pack(side='right')
        self.update_interval.set(self.app.config.get_update_interval())
        
        # 启动选项
        startup_frame = ttk.Frame(parent)
        startup_frame.pack(fill='x', pady=5)
        self.start_minimized = tk.BooleanVar(value=self.app.config.get_start_minimized())
        ttk.Checkbutton(
            startup_frame, text="启动时最小化到托盘",
            variable=self.start_minimized
        ).pack(anchor='w')
        
        # 日志选项
        logging_frame = ttk.Frame(parent)
        logging_frame.pack(fill='x', pady=5)
        self.log_temps = tk.BooleanVar(value=self.app.config.get_log_temperatures())
        ttk.Checkbutton(
            logging_frame, text="记录温度日志",
            variable=self.log_temps
        ).pack(anchor='w')
        
        # 声音提示
        sound_frame = ttk.Frame(parent)
        sound_frame.pack(fill='x', pady=5)
        self.enable_sound = tk.BooleanVar(value=self.app.notifier.sound_enabled)
        ttk.Checkbutton(
            sound_frame, text="启用声音提示",
            variable=self.enable_sound
        ).pack(anchor='w')

    def _create_appearance_tab(self, parent):
        """创建外观设置标签页"""
        # 主题选择
        theme_frame = ttk.Frame(parent)
        theme_frame.pack(fill='x', pady=5)
        ttk.Label(theme_frame, text="主题:").pack(side='left')
        self.theme = ttk.Combobox(
            theme_frame, 
            values=["深色", "浅色", "系统"],
            state="readonly",
            width=10
        )
        self.theme.pack(side='right')
        self.theme.set(self.app.config.get_theme().capitalize())
        
        # 字体大小
        font_frame = ttk.Frame(parent)
        font_frame.pack(fill='x', pady=5)
        ttk.Label(font_frame, text="字体大小:").pack(side='left')
        self.font_size = ttk.Spinbox(
            font_frame, from_=8, to=20, width=5,
            validate="key", validatecommand=(parent.register(self._validate_int), '%P')
        )
        self.font_size.pack(side='right')
        self.font_size.set(self.app.config.get_font_size())
        
        # 窗口透明度
        opacity_frame = ttk.Frame(parent)
        opacity_frame.pack(fill='x', pady=5)
        ttk.Label(opacity_frame, text="窗口透明度:").pack(side='left')
        self.opacity = tk.Scale(
            opacity_frame, from_=30, to=100, orient='horizontal',
            showvalue=False, length=150
        )
        self.opacity.pack(side='right')
        self.opacity.set(int(self.app.config.get_opacity() * 100))

    def _configure_styles(self):
        """配置窗口样式"""
        style = ttk.Style()
        style.configure('Accent.TButton', background='#3498db', foreground='white')

    def _validate_temp(self, value: str) -> bool:
        """验证温度值输入"""
        if value == "":
            return True
        try:
            temp = float(value)
            return 0 <= temp <= 150
        except ValueError:
            return False

    def _validate_int(self, value: str) -> bool:
        """验证整数值输入"""
        if value == "":
            return True
        try:
            num = int(value)
            return num > 0
        except ValueError:
            return False

    def save_settings(self):
        """保存设置"""
        try:
            # 保存阈值
            self.app.config.set_threshold('CPU', float(self.cpu_threshold.get()))
            self.app.config.set_threshold('GPU', float(self.gpu_threshold.get()))
            self.app.config.set_threshold('SSD', float(self.ssd_threshold.get()))
            
            # 保存常规设置
            self.app.config.set_update_interval(float(self.update_interval.get()))
            self.app.config.set_start_minimized(self.start_minimized.get())
            self.app.config.set_log_temperatures(self.log_temps.get())
            
            # 保存告警冷却时间（转换为秒）
            cooldown_minutes = int(self.alert_cooldown.get())
            self.app.config.set_alert_cooldown(cooldown_minutes * 60)
            
            # 保存外观设置
            self.app.config.set_theme(self.theme.get().lower())
            self.app.config.set_font_size(int(self.font_size.get()))
            self.app.config.set_opacity(self.opacity.get() / 100.0)
            
            # 启用/禁用声音
            self.app.notifier.enable_sound(self.enable_sound.get())
            
            # 通知主应用设置已更改
            self.on_save()
            
            # 关闭窗口
            self.close()
            
            messagebox.showinfo("设置", "设置已成功保存！")
            
        except Exception as e:
            self.logger.error(f"保存设置失败: {str(e)}")
            messagebox.showerror("错误", f"保存设置时出错: {str(e)}")

    def show(self):
        """显示窗口"""
        if self.window.winfo_exists():
            self.window.deiconify()
        else:
            self._create_window()
        self.logger.info("显示设置窗口")

    def close(self):
        """关闭窗口"""
        if self.window.winfo_exists():
            self.window.grab_release()
            self.window.destroy()
        self.logger.info("关闭设置窗口")