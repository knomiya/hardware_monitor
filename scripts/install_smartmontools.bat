@echo off
REM 安装 smartmontools 用于读取 SSD 温度
chcp 65001 > nul  // 设置控制台为UTF-8编码
echo 正在安装 smartmontools...
curl -L -o smartmontools.exe https://sourceforge.net/projects/smartmontools/files/smartmontools/7.3/smartmontools-7.3-1.win32-setup.exe/download
smartmontools.exe /SILENT
echo 添加 smartmontools 到系统 PATH...
setx PATH "%PATH%;C:\Program Files\smartmontools\bin"
echo 安装完成! 请重新启动命令提示符或系统以使更改生效。
pause