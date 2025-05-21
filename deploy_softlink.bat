@echo off
setlocal enabledelayedexpansion

:: SoftLink项目一键部署脚本 (Windows版本)
:: 用于在Windows服务器上快速部署整个项目环境

:: 设置颜色
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set BLUE=[94m
set NC=[0m

:: 项目根目录
set PROJECT_ROOT=%~dp0
set BACKEND_DIR=%PROJECT_ROOT%backend
set FRONTEND_DIR=%PROJECT_ROOT%frontend
set FRONTEND_BUILD_DIR=%FRONTEND_DIR%\softlink-f
set LOG_FILE=%PROJECT_ROOT%deploy_log.txt

:: 服务配置
set NGINX_PATH=C:\nginx
set BACKEND_PORT=5000
set FRONTEND_PORT=80

:: 清空日志文件
echo. > %LOG_FILE%

:: 输出标题
echo %BLUE%===== SoftLink项目部署脚本 (Windows版本) =====%NC%
echo %BLUE%开始时间: %date% %time%%NC%
echo %BLUE%===== SoftLink项目部署脚本 (Windows版本) =====%NC% >> %LOG_FILE%
echo %BLUE%开始时间: %date% %time%%NC% >> %LOG_FILE%

:: 检查系统环境
call :log "检查系统环境..."

:: 检查Python
call :check_command python "请安装Python 3.6+: https://www.python.org/downloads/"
if %ERRORLEVEL% neq 0 goto :error_exit

:: 检查pip
call :check_command pip "pip未安装，请重新安装Python并确保勾选pip选项"
if %ERRORLEVEL% neq 0 goto :error_exit

:: 检查Nginx
call :check_file "%NGINX_PATH%\nginx.exe" "Nginx未安装，请从http://nginx.org/en/download.html下载并安装"
if %ERRORLEVEL% neq 0 goto :error_exit

:: 检查端口占用
call :check_port %BACKEND_PORT%
call :check_port %FRONTEND_PORT%

:: 设置后端环境
call :log "设置后端环境..."
cd /d %BACKEND_DIR%

:: 检查虚拟环境
if not exist "venv" (
    call :log "创建Python虚拟环境..."
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        call :error "创建虚拟环境失败"
        goto :error_exit
    )
) else (
    call :log "已存在虚拟环境"
)

:: 激活虚拟环境
call :log "激活虚拟环境..."
call venv\Scripts\activate.bat

:: 安装依赖
call :log "安装Python依赖..."
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    call :error "安装依赖失败"
    goto :error_exit
)

call :success "后端环境设置完成"

:: 配置Nginx
call :log "配置Nginx..."

:: 检查Nginx配置文件
if not exist "%FRONTEND_DIR%\nginx.softlink.conf" (
    call :error "未找到Nginx配置文件: %FRONTEND_DIR%\nginx.softlink.conf"
    goto :error_exit
)

:: 更新Nginx配置文件中的路径
call :log "更新Nginx配置文件..."
set PROJECT_ROOT_ESCAPED=%PROJECT_ROOT:\=/%
powershell -Command "(Get-Content '%FRONTEND_DIR%\nginx.softlink.conf') -replace 'D:/workplace/SoftLink/SoftLink-0517', '%PROJECT_ROOT_ESCAPED%' | Set-Content '%FRONTEND_DIR%\nginx.softlink.conf'"

:: 复制配置文件
call :log "应用Nginx配置..."
copy /Y "%FRONTEND_DIR%\nginx.softlink.conf" "%NGINX_PATH%\conf\nginx.conf"
if %ERRORLEVEL% neq 0 (
    call :error "复制Nginx配置文件失败"
    goto :error_exit
)

call :success "Nginx配置完成"

:: 启动后端服务
call :log "启动后端服务..."
cd /d %BACKEND_DIR%

:: 检查后端启动脚本
if not exist "startup.py" (
    call :error "未找到后端启动脚本: startup.py"
    goto :error_exit
)

:: 启动后端服务
call :log "启动后端服务..."
start /B python startup.py > backend.log 2>&1
if %ERRORLEVEL% neq 0 (
    call :error "后端服务启动失败，请检查backend.log文件"
    goto :error_exit
)

:: 等待服务启动
call :log "等待后端服务启动..."
timeout /t 5 /nobreak > nul

:: 检查后端服务是否正常运行
call :log "检查后端服务是否正常运行..."
powershell -Command "if ((Test-NetConnection localhost -Port %BACKEND_PORT% -WarningAction SilentlyContinue).TcpTestSucceeded) { exit 0 } else { exit 1 }"
if %ERRORLEVEL% equ 0 (
    call :success "后端服务正在监听端口 %BACKEND_PORT%"
) else (
    call :warn "后端服务可能未正确监听端口 %BACKEND_PORT%"
)

:: 启动前端服务
call :log "启动前端服务..."

:: 检查前端构建目录
if not exist "%FRONTEND_BUILD_DIR%" (
    call :error "未找到前端构建目录: %FRONTEND_BUILD_DIR%"
    goto :error_exit
)

:: 检查index.html
if not exist "%FRONTEND_BUILD_DIR%\index.html" (
    call :error "前端构建目录中未找到index.html文件"
    goto :error_exit
)

:: 停止可能已经运行的Nginx进程
call :log "停止现有Nginx进程..."
taskkill /F /IM nginx.exe /T > nul 2>&1

:: 启动Nginx
call :log "启动Nginx服务..."
cd /d "%NGINX_PATH%"
start nginx
if %ERRORLEVEL% neq 0 (
    call :error "Nginx启动失败"
    goto :error_exit
)

:: 等待Nginx启动
timeout /t 2 /nobreak > nul

:: 检查Nginx是否正常运行
call :log "检查Nginx服务是否正常运行..."
tasklist /FI "IMAGENAME eq nginx.exe" 2>nul | find /i "nginx.exe" > nul
if %ERRORLEVEL% equ 0 (
    call :success "Nginx服务启动成功"
) else (
    call :error "Nginx服务启动失败"
    goto :error_exit
)

:: 创建停止脚本
call :log "创建停止脚本..."
(
echo @echo off
echo echo 正在停止SoftLink服务...
echo.
echo echo 停止后端服务...
echo taskkill /F /FI "WINDOWTITLE eq startup.py*" /T
echo taskkill /F /FI "IMAGENAME eq python.exe" /T
echo.
echo echo 停止Nginx服务...
echo taskkill /F /IM nginx.exe /T
echo.
echo echo SoftLink服务已停止
echo pause
) > "%PROJECT_ROOT%stop_softlink.bat"

call :success "已创建停止脚本: %PROJECT_ROOT%stop_softlink.bat"

:: 健康检查
call :log "系统健康检查..."

:: 检查后端API可访问性
call :log "检查后端API可访问性..."
powershell -Command "try { $response = Invoke-WebRequest -Uri http://localhost:%BACKEND_PORT% -Method Head -UseBasicParsing -TimeoutSec 5; if ($response.StatusCode -lt 400) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %ERRORLEVEL% equ 0 (
    call :success "后端API可以访问"
) else (
    call :error "无法访问后端API"
    call :warn "可能原因: 1.后端服务未启动 2.防火墙阻止 3.端口配置错误"
    call :warn "解决方案: 检查backend.log文件，确保服务正常启动且监听正确端口"
)

:: 检查前端可访问性
call :log "检查前端可访问性..."
powershell -Command "try { $response = Invoke-WebRequest -Uri http://localhost -Method Head -UseBasicParsing -TimeoutSec 5; if ($response.StatusCode -lt 400) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %ERRORLEVEL% equ 0 (
    call :success "前端页面可以访问"
) else (
    call :error "无法访问前端页面"
    call :warn "可能原因: 1.Nginx配置错误 2.防火墙阻止 3.前端文件路径错误"
    call :warn "解决方案: 检查Nginx错误日志(%NGINX_PATH%\logs\error.log)，确保配置正确"
)

:: 显示系统信息
call :log "SoftLink系统信息..."

:: 获取服务器IP
for /f "tokens=1-2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do (
    set IP=%%b
    set IP=!IP:~1!
    goto :got_ip
)
:got_ip

echo.
echo %GREEN%==================================%NC%
echo %GREEN%  SoftLink系统部署完成%NC%
echo %GREEN%==================================%NC%
echo 前端访问地址: %BLUE%http://%IP%%NC%
echo 后端API地址: %BLUE%http://%IP%:%BACKEND_PORT%%NC%
echo 部署日志文件: %YELLOW%%LOG_FILE%%NC%
echo.
echo 如需停止服务，请运行: %YELLOW%%PROJECT_ROOT%stop_softlink.bat%NC%
echo %GREEN%==================================%NC%
echo.

call :log "SoftLink项目部署完成"
goto :eof

:: ===== 辅助函数 =====

:log
echo %BLUE%[%date% %time%]%NC% %~1
echo %BLUE%[%date% %time%]%NC% %~1 >> %LOG_FILE%
goto :eof

:success
echo %GREEN%[成功]%NC% %~1
echo %GREEN%[成功]%NC% %~1 >> %LOG_FILE%
goto :eof

:warn
echo %YELLOW%[警告]%NC% %~1
echo %YELLOW%[警告]%NC% %~1 >> %LOG_FILE%
goto :eof

:error
echo %RED%[错误]%NC% %~1
echo %RED%[错误]%NC% %~1 >> %LOG_FILE%
goto :eof

:check_command
where %~1 > nul 2>&1
if %ERRORLEVEL% neq 0 (
    call :error "%~1 未安装。请安装后重试。"
    echo   安装方法: %~2
    echo   安装方法: %~2 >> %LOG_FILE%
    exit /b 1
) else (
    call :success "%~1 已安装"
    exit /b 0
)
goto :eof

:check_file
if not exist "%~1" (
    call :error "%~1 不存在。"
    echo   解决方法: %~2
    echo   解决方法: %~2 >> %LOG_FILE%
    exit /b 1
) else (
    call :success "%~1 已存在"
    exit /b 0
)
goto :eof

:check_port
powershell -Command "$port = %~1; $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue; if ($connections) { exit 1 } else { exit 0 }"
if %ERRORLEVEL% neq 0 (
    call :warn "端口 %~1 已被占用，可能会导致服务启动失败"
    exit /b 1
) else (
    call :success "端口 %~1 可用"
    exit /b 0
)
goto :eof

:error_exit
call :error "部署过程中出现错误，请查看以上日志解决问题后重试"
pause
exit /b 1 