@echo off
echo 正在启动SoftLink前端服务...

REM 设置Nginx路径变量（需要修改为你的Nginx安装位置）
set NGINX_PATH=C:\nginx

REM 检查Nginx是否已安装
if not exist "%NGINX_PATH%\nginx.exe" (
    echo 错误: 在 %NGINX_PATH% 未找到Nginx。请修改脚本中的NGINX_PATH变量为你的Nginx安装路径。
    pause
    exit /b 1
)

REM 停止可能已经运行的Nginx进程
echo 停止现有Nginx进程...
taskkill /F /IM nginx.exe /T >nul 2>&1

REM 复制配置文件到Nginx配置目录
echo 正在应用SoftLink配置...
copy /Y "%~dp0nginx.softlink.conf" "%NGINX_PATH%\conf\nginx.conf"

REM 启动Nginx
echo 启动Nginx...
cd /d "%NGINX_PATH%"
start nginx

echo.
echo SoftLink前端服务已启动成功！
echo 请访问: http://localhost
echo.
echo 按任意键退出此窗口...
pause > nul 