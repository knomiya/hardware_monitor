@echo off
REM ��װ smartmontools ���ڶ�ȡ SSD �¶�
chcp 65001 > nul  // ���ÿ���̨ΪUTF-8����
echo ���ڰ�װ smartmontools...
curl -L -o smartmontools.exe https://sourceforge.net/projects/smartmontools/files/smartmontools/7.3/smartmontools-7.3-1.win32-setup.exe/download
smartmontools.exe /SILENT
echo ��� smartmontools ��ϵͳ PATH...
setx PATH "%PATH%;C:\Program Files\smartmontools\bin"
echo ��װ���! ����������������ʾ����ϵͳ��ʹ������Ч��
pause