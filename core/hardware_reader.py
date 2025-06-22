# core/hardware_reader.py
"""
硬件数据读取器
负责从系统获取CPU、GPU和SSD的温度数据
"""

import wmi
import GPUtil
import psutil
import logging
import subprocess
import re
import threading
import time
from utils.helpers import bytes_to_human

class HardwareReader:
    def __init__(self):
        """
        初始化硬件读取器
        """
        self.logger = logging.getLogger("HardwareReader")
        self.cpu_temp = None
        self.gpu_temp = None
        self.ssd_temp = None
        self.last_update = 0
        self.update_interval = 2  # 最小更新间隔（秒）
        
        # 初始化WMI连接
        self.wmi_conn = None
        self._init_wmi()
        
        # 检测硬件可用性
        self.has_cpu = True
        self.has_gpu = True
        self.has_ssd = True
        
        # 初始化硬件信息
        self.cpu_name = "未知CPU"
        self.gpu_name = "未知GPU"
        self.ssd_name = "未知SSD"
        self._detect_hardware()
        
        self.logger.info("硬件读取器初始化完成")

    def _init_wmi(self):
        """初始化WMI连接"""
        try:
            self.wmi_conn = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            self.logger.info("WMI连接已建立")
        except Exception as e:
            self.logger.error(f"无法建立WMI连接: {str(e)}")
            self.wmi_conn = None

    def _detect_ssd(self):
        """检测SSD并确定温度读取方法"""
        self.has_ssd = False
        self.ssd_temp_method = None
        
        try:
            # Windows 系统使用 smartctl
            if sys.platform == "win32":
                # 检查 smartctl 是否可用
                result = subprocess.run(
                    ["smartctl", "--version"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self.has_ssd = True
                    self.ssd_temp_method = "smartctl"
                    self.logger.info("检测到 smartctl，将用于读取SSD温度")
                else:
                    self.logger.warning("未找到 smartctl，无法读取SSD温度")
            
            # Linux 系统使用 /sys/class/hwmon
            elif sys.platform.startswith("linux"):
                if os.path.exists("/sys/class/hwmon"):
                    self.has_ssd = True
                    self.ssd_temp_method = "hwmon"
                    self.logger.info("将使用 hwmon 读取SSD温度")
                else:
                    self.logger.warning("未找到 hwmon，无法读取SSD温度")
            
            # macOS 系统使用 system_profiler
            elif sys.platform == "darwin":
                result = subprocess.run(
                    ["system_profiler", "SPSerialATADataType"],
                    capture_output=True,
                    text=True
                )
                if "SSD" in result.stdout:
                    self.has_ssd = True
                    self.ssd_temp_method = "system_profiler"
                    self.logger.info("将使用 system_profiler 读取SSD温度")
            
            if not self.has_ssd:
                self.logger.warning("未检测到SSD或无法读取SSD温度")
                
        except Exception as e:
            self.logger.error(f"检测SSD失败: {str(e)}")
            self.has_ssd = False

    def get_ssd_temp(self) -> float:
        """获取SSD温度"""
        if not self.has_ssd:
            return None
            
        try:
            # Windows 系统使用 smartctl
            if self.ssd_temp_method == "smartctl":
                # 尝试不同的设备路径
                devices = [r"\\.\nvme0", r"\\.\physicaldrive0"]
                for device in devices:
                    try:
                        result = subprocess.run(
                            ["smartctl", "-A", device],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            for line in result.stdout.splitlines():
                                if "Temperature" in line:
                                    match = re.search(r"(\d+)\s+Celsius", line)
                                    if match:
                                        return float(match.group(1))
                    except:
                        continue
            
            # Linux 系统使用 hwmon
            elif self.ssd_temp_method == "hwmon":
                for hwmon_dir in os.listdir("/sys/class/hwmon"):
                    path = os.path.join("/sys/class/hwmon", hwmon_dir)
                    if os.path.exists(os.path.join(path, "temp1_input")):
                        try:
                            with open(os.path.join(path, "temp1_input"), "r") as f:
                                temp = float(f.read().strip()) / 1000
                                return temp
                        except:
                            continue
            
            # macOS 系统使用 system_profiler
            elif self.ssd_temp_method == "system_profiler":
                result = subprocess.run(
                    ["system_profiler", "SPSerialATADataType"],
                    capture_output=True,
                    text=True
                )
                match = re.search(r"Temperature: (\d+) C", result.stdout)
                if match:
                    return float(match.group(1))
            
            return None
        except Exception as e:
            self.logger.error(f"获取SSD温度失败: {str(e)}")
            return None

    def get_cpu_temp(self) -> float:
        """获取CPU温度"""
        if not self.has_cpu or not self.wmi_conn:
            return None
            
        try:
            sensors = self.wmi_conn.Sensor(SensorType="Temperature")
            for sensor in sensors:
                if "CPU" in sensor.Name and sensor.Value is not None:
                    return float(sensor.Value)
            return None
        except Exception as e:
            self.logger.error(f"获取CPU温度失败: {str(e)}")
            return None

    def get_gpu_temp(self) -> float:
        """获取GPU温度"""
        if not self.has_gpu:
            return None
            
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                return gpus[0].temperature
            return None
        except Exception as e:
            self.logger.error(f"获取GPU温度失败: {str(e)}")
            return None

    def get_ssd_temp(self) -> float:
        """获取SSD温度"""
        if not self.has_ssd:
            return None
            
        try:
            # 使用smartctl获取SSD温度
            result = subprocess.run(
                ["smartctl", "-A", "/dev/nvme0"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # 解析温度数据
                for line in result.stdout.splitlines():
                    if "Temperature" in line:
                        match = re.search(r"(\d+)\s+Celsius", line)
                        if match:
                            return float(match.group(1))
            
            return None
        except Exception as e:
            self.logger.error(f"获取SSD温度失败: {str(e)}")
            return None

    def get_all_temperatures(self) -> dict:
        """
        获取所有硬件温度
        带有缓存机制避免频繁读取
        """
        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return {
                'CPU': self.cpu_temp,
                'GPU': self.gpu_temp,
                'SSD': self.ssd_temp
            }
            
        try:
            self.cpu_temp = self.get_cpu_temp()
            self.gpu_temp = self.get_gpu_temp()
            self.ssd_temp = self.get_ssd_temp()
            self.last_update = current_time
            
            return {
                'CPU': self.cpu_temp,
                'GPU': self.gpu_temp,
                'SSD': self.ssd_temp
            }
        except Exception as e:
            self.logger.error(f"获取温度数据失败: {str(e)}")
            return {
                'CPU': None,
                'GPU': None,
                'SSD': None
            }

    def get_hardware_names(self) -> dict:
        """获取硬件名称"""
        return {
            'CPU': self.cpu_name,
            'GPU': self.gpu_name,
            'SSD': self.ssd_name
        }

# 测试硬件读取
if __name__ == "__main__":
    import logging
    from utils.logger import setup_logging
    
    setup_logging(log_level="DEBUG")
    reader = HardwareReader()
    
    print("硬件名称:")
    names = reader.get_hardware_names()
    for device, name in names.items():
        print(f"{device}: {name}")
    
    print("\n当前温度:")
    temps = reader.get_all_temperatures()
    for device, temp in temps.items():
        print(f"{device}: {temp if temp is not None else 'N/A'}°C")