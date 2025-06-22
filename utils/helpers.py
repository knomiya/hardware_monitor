# utils/helpers.py
"""
通用辅助函数集合
包含各种工具函数，用于系统信息、单位转换等
"""

import os
import sys
import platform
import ctypes
import psutil
import logging
from typing import Dict, Any, Optional, Union

# 获取记录器
logger = logging.getLogger("Helpers")

def get_system_info() -> Dict[str, Any]:
    """获取详细的系统信息"""
    try:
        info = {}
        uname = platform.uname()
        
        # 系统信息
        info['system'] = uname.system
        info['node_name'] = uname.node
        info['release'] = uname.release
        info['version'] = uname.version
        info['machine'] = uname.machine
        info['processor'] = uname.processor
        
        # CPU信息
        info['cpu_cores'] = psutil.cpu_count(logical=False)
        info['cpu_threads'] = psutil.cpu_count(logical=True)
        
        # 内存信息
        mem = psutil.virtual_memory()
        info['total_memory'] = mem.total
        info['available_memory'] = mem.available
        
        # 磁盘信息
        disks = []
        for part in psutil.disk_partitions(all=False):
            if 'fixed' in part.opts:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    'device': part.device,
                    'mountpoint': part.mountpoint,
                    'fstype': part.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free
                })
        info['disks'] = disks
        
        # GPU信息（Windows特定）
        if platform.system() == "Windows":
            try:
                import wmi
                w = wmi.WMI()
                gpus = []
                for gpu in w.Win32_VideoController():
                    gpus.append({
                        'name': gpu.Name,
                        'adapter_ram': gpu.AdapterRAM,
                        'driver_version': gpu.DriverVersion
                    })
                info['gpus'] = gpus
            except ImportError:
                logger.warning("无法获取GPU信息: wmi模块未安装")
        
        return info
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        return {}

def bytes_to_human(size: int, precision: int = 2) -> str:
    """将字节大小转换为易读格式"""
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    size = float(size)
    
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            break
        size /= 1024.0
    
    return f"{size:.{precision}f} {unit}"

def celsius_to_fahrenheit(c: float) -> float:
    """摄氏度转华氏度"""
    return (c * 9/5) + 32

def is_admin() -> bool:
    """检查程序是否以管理员权限运行"""
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.getuid() == 0  # Unix系统检查root
    except Exception:
        return False

def run_as_admin():
    """以管理员权限重新运行程序（仅Windows）"""
    if platform.system() != "Windows":
        logger.warning("仅支持Windows系统的管理员权限提升")
        return False
    
    if is_admin():
        return True
        
    try:
        # 请求UAC提升
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)  # 退出当前实例
    except Exception as e:
        logger.error(f"请求管理员权限失败: {str(e)}")
        return False

def create_tray_image(text: str, size: tuple = (64, 64), bg_color: str = "black", text_color: str = "white") -> Any:
    """
    创建托盘图标图像（带温度文本）
    
    :param text: 显示的文本
    :param size: 图像尺寸
    :param bg_color: 背景颜色
    :param text_color: 文本颜色
    :return: PIL.Image对象
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.error("PIL模块未安装，无法创建托盘图标")
        return None
    
    try:
        # 创建图像
        image = Image.new('RGB', size, bg_color)
        dc = ImageDraw.Draw(image)
        
        # 尝试加载字体
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            # 回退到默认字体
            font = ImageFont.load_default()
        
        # 计算文本位置（居中）
        text_width, text_height = dc.textsize(text, font=font)
        position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
        
        # 绘制文本
        dc.text(position, text, fill=text_color, font=font)
        
        return image
    except Exception as e:
        logger.error(f"创建托盘图标失败: {str(e)}")
        return None

def get_resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径（支持PyInstaller打包）
    
    :param relative_path: 资源文件相对路径
    :return: 资源文件绝对路径
    """
    try:
        # PyInstaller创建的临时文件夹
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def validate_email(email: str) -> bool:
    """验证电子邮件格式（简单版）"""
    import re
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """将值限制在[min_val, max_val]范围内"""
    return max(min_val, min(value, max_val))

# 测试辅助函数
if __name__ == "__main__":
    import logging
    from utils.logger import setup_logging
    
    setup_logging(log_level="DEBUG")
    
    # 测试系统信息获取
    sys_info = get_system_info()
    print("系统信息:")
    for key, value in sys_info.items():
        print(f"{key}: {value}")
    
    # 测试单位转换
    print("\n单位转换:")
    print(f"1024 -> {bytes_to_human(1024)}")
    print(f"2048 -> {bytes_to_human(2048)}")
    print(f"1500000 -> {bytes_to_human(1500000)}")
    print(f"25°C -> {celsius_to_fahrenheit(25):.1f}°F")
    
    # 测试管理员权限
    print(f"\n管理员权限: {'是' if is_admin() else '否'}")
    
    # 测试托盘图标创建
    image = create_tray_image("75°C")
    if image:
        image.save("tray_icon.png")
        print("托盘图标已保存为 tray_icon.png")
    
    # 测试资源路径获取
    print(f"资源路径示例: {get_resource_path('resources/icon.png')}")
    
    # 测试邮箱验证
    print(f"邮箱验证: test@example.com -> {validate_email('test@example.com')}")
    print(f"邮箱验证: invalid-email -> {validate_email('invalid-email')}")
    
    # 测试值限制
    print(f"值限制 (10, 0, 5): {clamp(10, 0, 5)}")
    print(f"值限制 (-5, 0, 5): {clamp(-5, 0, 5)}")
    print(f"值限制 (3, 0, 5): {clamp(3, 0, 5)}")