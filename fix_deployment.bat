@echo off
setlocal enabledelayedexpansion

:: SoftLink项目部署修复脚本 (Windows版本)
:: 用于修复Windows测试环境中的部署问题

echo [*] SoftLink项目部署修复脚本 (Windows版本)
echo [*] 用于修复Windows测试环境中的部署问题

:: 设置颜色
set GREEN=[92m
set YELLOW=[93m
set RED=[91m
set BLUE=[94m
set NC=[0m

:: 项目根目录
set PROJECT_ROOT=%~dp0
set BACKEND_DIR=%PROJECT_ROOT%backend
set FRONTEND_DIR=%PROJECT_ROOT%frontend
set FRONTEND_BUILD_DIR=%FRONTEND_DIR%\softlink-f

echo %BLUE%[*] 当前目录: %PROJECT_ROOT%%NC%

:: 检查并修复前端目录名称问题
echo %BLUE%[*] 检查前端构建目录...%NC%
if not exist "%FRONTEND_BUILD_DIR%" (
    echo %YELLOW%[!] 前端构建目录不存在: %FRONTEND_BUILD_DIR%%NC%
    
    :: 检查是否存在名称错误的目录
    if exist "%FRONTEND_DIR%\softlin-f" (
        echo %BLUE%[*] 发现错误命名的目录，尝试修复...%NC%
        ren "%FRONTEND_DIR%\softlin-f" "softlink-f"
        echo %GREEN%[✓] 已将softlin-f重命名为softlink-f%NC%
    ) else (
        echo %RED%[✗] 无法找到前端构建目录，请确保前端代码已构建%NC%
    )
) else (
    echo %GREEN%[✓] 前端构建目录存在: %FRONTEND_BUILD_DIR%%NC%
)

:: 修复Nginx配置文件
echo %BLUE%[*] 检查Nginx配置文件...%NC%
set NGINX_CONF=%FRONTEND_DIR%\nginx.softlink.conf

if not exist "%NGINX_CONF%" (
    echo %RED%[✗] Nginx配置文件不存在: %NGINX_CONF%%NC%
) else (
    echo %BLUE%[*] 修复Nginx配置文件中的路径问题...%NC%
    
    :: 备份原始配置
    copy /Y "%NGINX_CONF%" "%NGINX_CONF%.backup" > nul
    
    :: 将正斜杠替换为反斜杠，以便Windows路径能正常工作
    set PROJECT_ROOT_ESCAPED=%PROJECT_ROOT:\=/%
    
    powershell -Command "(Get-Content '%NGINX_CONF%') -replace '/root/softlink/frontend/softlink-f', '%PROJECT_ROOT_ESCAPED%/frontend/softlink-f' | Set-Content '%NGINX_CONF%'"
    
    echo %GREEN%[✓] Nginx配置文件已修复%NC%
)

:: 检查和修复批处理脚本
echo %BLUE%[*] 检查部署批处理脚本...%NC%
set DEPLOY_BAT=%PROJECT_ROOT%deploy_softlink.bat

if exist "%DEPLOY_BAT%" (
    echo %BLUE%[*] 修复部署批处理脚本中的目录名称问题...%NC%
    
    :: 备份原始脚本
    copy /Y "%DEPLOY_BAT%" "%DEPLOY_BAT%.backup" > nul
    
    :: 修复目录名称问题
    powershell -Command "(Get-Content '%DEPLOY_BAT%') -replace 'softlin-f', 'softlink-f' | Set-Content '%DEPLOY_BAT%'"
    
    echo %GREEN%[✓] 部署批处理脚本已修复%NC%
) else (
    echo %YELLOW%[!] 未找到部署批处理脚本: %DEPLOY_BAT%%NC%
)

:: 检查和修复.env文件
echo %BLUE%[*] 检查.env配置文件...%NC%
set ENV_FILE=%PROJECT_ROOT%.env

if not exist "%ENV_FILE%" (
    echo %YELLOW%[!] .env文件不存在，尝试创建...%NC%
    
    :: 检查示例文件
    if exist "%PROJECT_ROOT%.env.example" (
        copy /Y "%PROJECT_ROOT%.env.example" "%ENV_FILE%" > nul
        echo %GREEN%[✓] 已从.env.example创建.env文件%NC%
    ) else (
        echo %BLUE%[*] 创建新的.env文件...%NC%
        
        :: 使用随机字符串作为密钥
        set SECRET_KEY=
        set JWT_KEY=
        for /L %%i in (1,1,32) do (
            set /a "rand=!random! %% 16"
            set "hex=0123456789abcdef"
            set "SECRET_KEY=!SECRET_KEY!!hex:~%rand%,1!"
            
            set /a "rand=!random! %% 16"
            set "JWT_KEY=!JWT_KEY!!hex:~%rand%,1!"
        )
        
        (
            echo # Flask配置
            echo FLASK_ENV=production
            echo FLASK_APP=app.py
            echo FLASK_RUN_PORT=5000
            echo.
            echo # 数据库配置
            echo DATABASE_URL=postgresql://postgres:123.123.MengLi@localhost:5432/softlink?client_encoding=utf8
            echo.
            echo # Redis配置
            echo REDIS_URL=redis://localhost:6379/0
            echo.
            echo # 安全配置
            echo SECRET_KEY=!SECRET_KEY!
            echo JWT_SECRET_KEY=!JWT_KEY!
            echo.
            echo # 其他配置
            echo DEBUG=False
            echo TESTING=False
        ) > "%ENV_FILE%"
        
        echo %GREEN%[✓] 已创建新的.env文件%NC%
    )
) else (
    echo %GREEN%[✓] 发现.env文件%NC%
    
    :: 检查数据库连接配置
    findstr /C:"DATABASE_URL" "%ENV_FILE%" > nul
    if %ERRORLEVEL% NEQ 0 (
        echo %YELLOW%[!] .env文件中缺少数据库连接配置，将添加...%NC%
        echo. >> "%ENV_FILE%"
        echo # 数据库配置 >> "%ENV_FILE%"
        echo DATABASE_URL=postgresql://postgres:123.123.MengLi@localhost:5432/softlink?client_encoding=utf8 >> "%ENV_FILE%"
    )
    
    :: 确保使用localhost连接数据库
    powershell -Command "(Get-Content '%ENV_FILE%') -replace 'DATABASE_URL=postgresql://[^@]*@(?!localhost)[^:]+', 'DATABASE_URL=postgresql://postgres:123.123.MengLi@localhost' | Set-Content '%ENV_FILE%'"
)

:: 创建修复后的部署脚本
echo %BLUE%[*] 创建修复后的部署脚本...%NC%
set NEW_DEPLOY_BAT=%PROJECT_ROOT%deploy_softlink_fixed.bat

(
    echo @echo off
    echo setlocal enabledelayedexpansion
    echo.
    echo :: SoftLink项目一键部署脚本 ^(Windows版本 - 修复版^)
    echo :: 用于在Windows环境部署测试环境
    echo.
    echo :: 设置颜色
    echo set GREEN=[92m
    echo set YELLOW=[93m
    echo set RED=[91m
    echo set BLUE=[94m
    echo set NC=[0m
    echo.
    echo echo %%BLUE%%[*] 开始部署SoftLink项目...%%NC%%
    echo.
    echo :: 项目根目录
    echo set PROJECT_ROOT=%%~dp0
    echo set BACKEND_DIR=%%PROJECT_ROOT%%backend
    echo set FRONTEND_DIR=%%PROJECT_ROOT%%frontend
    echo set FRONTEND_BUILD_DIR=%%FRONTEND_DIR%%\softlink-f
    echo.
    echo :: 检查端口占用
    echo echo %%BLUE%%[*] 检查端口占用情况...%%NC%%
    echo.
    echo :: 检查后端端口 5000
    echo powershell -Command "if ((Test-NetConnection localhost -Port 5000 -WarningAction SilentlyContinue).TcpTestSucceeded) { exit 1 } else { exit 0 }"
    echo if %%ERRORLEVEL%% EQU 1 (
    echo     echo %%YELLOW%%[!] 端口5000已被占用%%NC%%
    echo     echo 请选择操作:
    echo     echo   [t] 终止占用进程
    echo     echo   [c] 更改使用的端口
    echo     echo   [s] 跳过并退出
    echo     set /p PORT_ACTION="您的选择 [t/c/s]: "
    echo.
    echo     if "%%PORT_ACTION%%"=="t" (
    echo         echo %%BLUE%%[*] 尝试终止占用端口5000的进程...%%NC%%
    echo         for /f "tokens=5" %%%%a in ('netstat -ano ^| findstr ":5000"') do taskkill /F /PID %%%%a
    echo     ) else if "%%PORT_ACTION%%"=="c" (
    echo         set /p NEW_PORT="请输入新的端口号: "
    echo         set BACKEND_PORT=%%NEW_PORT%%
    echo         echo %%BLUE%%[*] 将使用端口 %%BACKEND_PORT%%...%%NC%%
    echo     ) else (
    echo         echo %%BLUE%%[*] 用户选择退出部署%%NC%%
    echo         goto :eof
    echo     )
    echo ) else (
    echo     echo %%GREEN%%[✓] 端口5000可用%%NC%%
    echo     set BACKEND_PORT=5000
    echo )
    echo.
    echo :: 设置后端环境
    echo echo %%BLUE%%[*] 设置后端环境...%%NC%%
    echo cd /d %%BACKEND_DIR%%
    echo.
    echo :: 检查虚拟环境
    echo if not exist "venv" (
    echo     echo %%BLUE%%[*] 创建Python虚拟环境...%%NC%%
    echo     python -m venv venv
    echo     if %%ERRORLEVEL%% NEQ 0 (
    echo         echo %%RED%%[✗] 创建虚拟环境失败%%NC%%
    echo         exit /b 1
    echo     )
    echo ) else (
    echo     echo %%GREEN%%[✓] 已存在虚拟环境%%NC%%
    echo )
    echo.
    echo :: 激活虚拟环境
    echo call venv\Scripts\activate.bat
    echo.
    echo :: 安装依赖
    echo echo %%BLUE%%[*] 安装Python依赖...%%NC%%
    echo pip install -r requirements.txt
    echo if %%ERRORLEVEL%% NEQ 0 (
    echo     echo %%RED%%[✗] 安装依赖失败%%NC%%
    echo     exit /b 1
    echo )
    echo.
    echo :: 配置Nginx
    echo echo %%BLUE%%[*] 配置Nginx...%%NC%%
    echo.
    echo :: 检查Nginx安装
    echo if not exist "C:\nginx\nginx.exe" (
    echo     echo %%YELLOW%%[!] 未找到Nginx，请确保Nginx已安装在C:\nginx目录%%NC%%
    echo     echo Nginx下载地址: http://nginx.org/en/download.html
    echo     set /p INSTALL_NGINX="是否继续部署? (y/n): "
    echo     if /i "%%INSTALL_NGINX%%" NEQ "y" (
    echo         echo %%BLUE%%[*] 用户选择退出部署%%NC%%
    echo         goto :eof
    echo     )
    echo )
    echo.
    echo :: 更新Nginx配置文件
    echo echo %%BLUE%%[*] 更新Nginx配置文件...%%NC%%
    echo set PROJECT_ROOT_ESCAPED=%%PROJECT_ROOT:\=/%%
    echo powershell -Command "(Get-Content '%%FRONTEND_DIR%%\nginx.softlink.conf') -replace '/root/softlink/frontend/softlink-f', '%%PROJECT_ROOT_ESCAPED%%/frontend/softlink-f' | Set-Content '%%FRONTEND_DIR%%\nginx.temp.conf'"
    echo.
    echo :: 使用新的Nginx配置
    echo mkdir C:\nginx\conf\softlink >nul 2>&1
    echo copy /Y "%%FRONTEND_DIR%%\nginx.temp.conf" "C:\nginx\conf\nginx.conf" >nul
    echo.
    echo :: 启动后端服务
    echo echo %%BLUE%%[*] 启动后端服务...%%NC%%
    echo cd /d %%BACKEND_DIR%%
    echo.
    echo :: 启动后端服务
    echo start /B python startup.py --port %%BACKEND_PORT%%
    echo.
    echo :: 启动Nginx
    echo echo %%BLUE%%[*] 启动Nginx服务...%%NC%%
    echo taskkill /F /IM nginx.exe >nul 2>&1
    echo cd /d C:\nginx
    echo start nginx
    echo.
    echo :: 等待服务启动
    echo timeout /t 3 /nobreak > nul
    echo.
    echo :: 创建停止脚本
    echo (
    echo     echo @echo off
    echo     echo echo 正在停止SoftLink服务...
    echo     echo.
    echo     echo echo 停止后端服务...
    echo     echo taskkill /F /FI "WINDOWTITLE eq startup.py*" /T
    echo     echo taskkill /F /FI "IMAGENAME eq python.exe" /T
    echo     echo.
    echo     echo echo 停止Nginx服务...
    echo     echo cd /d C:\nginx
    echo     echo nginx -s stop
    echo     echo.
    echo     echo echo SoftLink服务已停止
    echo     echo pause
    echo ) > "%%PROJECT_ROOT%%stop_softlink.bat"
    echo.
    echo echo %%GREEN%%===== SoftLink部署完成 =====%%NC%%
    echo echo %%GREEN%%前端访问地址: http://localhost%%NC%%
    echo echo %%GREEN%%后端API地址: http://localhost:%%BACKEND_PORT%%%%NC%%
    echo echo %%GREEN%%如需停止服务，请运行: %%PROJECT_ROOT%%stop_softlink.bat%%NC%%
    echo.
    echo pause
) > "%NEW_DEPLOY_BAT%"

echo %GREEN%[✓] 创建了修复后的部署脚本: %NEW_DEPLOY_BAT%%NC%

:: 创建README文件
echo %BLUE%[*] 创建部署说明文件...%NC%
set README_FILE=%PROJECT_ROOT%部署说明.txt

(
    echo SoftLink项目部署说明
    echo ====================
    echo.
    echo 1. Windows测试环境部署
    echo ---------------------
    echo.
    echo 前置条件:
    echo - 安装Python 3.6+ (https://www.python.org/downloads/)
    echo - 安装Nginx (http://nginx.org/en/download.html)
    echo - 安装PostgreSQL (https://www.postgresql.org/download/windows/)
    echo.
    echo 部署步骤:
    echo 1. 运行fix_deployment.bat修复部署文件
    echo 2. 创建PostgreSQL数据库:
    echo    - 用户名: postgres
    echo    - 密码: 123.123.MengLi
    echo    - 数据库名: softlink
    echo 3. 运行deploy_softlink_fixed.bat进行部署
    echo 4. 访问http://localhost查看前端页面
    echo 5. 需要停止服务时运行stop_softlink.bat
    echo.
    echo.
    echo 2. CentOS腾讯云部署
    echo ------------------
    echo.
    echo 前置条件:
    echo - CentOS 7+
    echo - root权限
    echo.
    echo 部署步骤:
    echo 1. 上传项目代码到腾讯云服务器
    echo 2. 运行以下命令添加执行权限:
    echo    chmod +x deploy_modified.sh
    echo 3. 执行部署脚本:
    echo    ./deploy_modified.sh
    echo 4. 通过服务器IP访问应用
    echo 5. 需要停止服务时运行:
    echo    ./stop_softlink.sh
    echo.
    echo 注意事项:
    echo - 确保5000端口未被占用
    echo - 如遇部署问题，检查日志目录下的日志文件
    echo - 防火墙需开放80和5000端口
) > "%README_FILE%"

echo %GREEN%[✓] 创建了部署说明文件: %README_FILE%%NC%

echo %GREEN%===== 修复完成 =====%NC%
echo %GREEN%请按照部署说明文件中的步骤进行部署%NC%

pause 