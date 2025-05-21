# SoftLink 腾讯云部署指南

本文档说明如何使用云部署工具快速在腾讯云服务器上部署并访问SoftLink应用。

## 配置文件说明

使用前需要先配置`cloud_config.py`文件：

1. 打开`cloud_config.py`文件
2. 修改`PUBLIC_IP`为您的腾讯云服务器公网IP地址
3. 根据需要修改SSH连接信息：
   - `SSH_USER`: SSH用户名（默认为root）
   - `SSH_PORT`: SSH端口（默认为22）
   - `SSH_KEY_PATH`: 如果使用密钥认证，设置为密钥文件路径
4. 根据需要修改项目路径配置：
   - `PROJECT_PATH`: 项目在服务器上的路径（默认为/root/SoftLink）
   - `FRONTEND_PATH`: 前端构建目录（默认为frontend/softlin-f，注意不是softlink-f）

## 服务端准备

在使用此工具前，确保：

1. 腾讯云服务器已正确配置并可通过SSH访问
2. 已在云服务器上部署SoftLink项目（通常位于`/root/SoftLink`目录）
3. 前端文件应位于`frontend/softlin-f`目录下（注意拼写，不是softlink-f）
4. 云服务器已安装必要的组件：
   - Python 3.6+
   - Nginx
   - PostgreSQL
   - 其他SoftLink依赖项

## 使用方法

### Windows系统

双击运行`cloud_deploy.bat`文件即可启动部署工具。

或打开命令提示符执行：
```
python cloud_deploy.py
```

### Linux/macOS系统

在终端中执行：
```bash
python3 cloud_deploy.py
```

## 工作原理

部署工具会执行以下操作：

1. 检查配置文件和SSH连接
2. 停止云服务器上运行的SoftLink服务（使用stop_softlink.sh脚本）
3. 修正Nginx配置以使用正确的前端目录（frontend/softlin-f）
4. 启动云服务器上的SoftLink服务（使用deploy_softlink.sh脚本）
5. 自动打开浏览器访问应用

## 常见问题

### 无法连接到云服务器

检查以下几点：
- 确认服务器IP地址正确
- 检查SSH配置（用户名、端口等）
- 确认服务器防火墙允许SSH连接

### 服务启动失败

可能原因：
- 服务器上的SoftLink不在预期的目录
- 服务器上缺少必要的组件
- 端口5000已被占用

解决方法：
1. 登录服务器检查SoftLink目录
2. 手动执行`deploy_softlink.sh`查看详细错误信息
3. 如端口被占用，使用`netstat -anp | grep :5000`查找占用进程，并使用`kill -9 进程ID`终止

### 无法访问应用页面

检查以下几点：
- 确认服务器防火墙已开放80和5000端口
- 确认Nginx配置正确（特别是前端目录是否为softlin-f）
- 检查服务器日志查找可能的错误
- 查看`/root/SoftLink/deploy_log.txt`获取部署详细日志

### 服务未完全停止

如果使用stop_softlink.sh脚本后某些服务仍在运行：
1. 登录服务器执行以下命令停止所有相关服务：
```bash
pkill -f "python.*startup.py"
sudo systemctl stop nginx || sudo nginx -s stop
kill $(lsof -t -i:5000)
``` 