@echo off
REM SoftLink 腾讯云部署批处理文件
REM 启动cloud_deploy.py脚本

echo 正在启动SoftLink腾讯云部署工具...
python cloud_deploy.py

echo.
echo 按任意键退出...
pause > nul 