#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SoftLink 开发模式启动脚本
- 同时启动前端和后端服务
- 监控并显示两者的输出
"""

import os
import sys
import subprocess
import threading
import time
import signal
import platform

# 设置颜色输出
class Colors:
    HEADER = '\033[95m'
    BACKEND = '\033[94m'
    FRONTEND = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

# 打印带有颜色的消息
def print_colored(message, color):
    print(f"{color}{message}{Colors.END}")

# 监控子进程输出的线程函数
def monitor_output(process, prefix, color):
    for line in iter(process.stdout.readline, b''):
        try:
            decoded_line = line.decode('utf-8').rstrip()
            print(f"{color}[{prefix}] {decoded_line}{Colors.END}")
        except UnicodeDecodeError:
            # 如果出现解码错误，尝试使用系统默认编码
            decoded_line = line.decode(sys.stdout.encoding, errors='replace').rstrip()
            print(f"{color}[{prefix}] {decoded_line}{Colors.END}")

# 获取当前项目根目录
def get_project_root():
    # 获取当前脚本的绝对路径
    script_path = os.path.abspath(__file__)
    # 返回脚本所在目录
    return os.path.dirname(script_path)

# 启动后端服务
def start_backend(root_dir):
    backend_dir = os.path.join(root_dir, 'backend')
    print_colored("正在启动后端服务...", Colors.BACKEND)
    
    # 构建命令，针对不同操作系统
    cmd = [sys.executable, 'startup.py']
    
    # 启动后端进程
    try:
        process = subprocess.Popen(
            cmd,
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
            bufsize=1,
            universal_newlines=False
        )
        return process
    except Exception as e:
        print_colored(f"启动后端服务失败: {str(e)}", Colors.ERROR)
        return None

# 启动前端服务
def start_frontend(root_dir):
    frontend_dir = os.path.join(root_dir, 'frontend')
    print_colored("正在启动前端服务...", Colors.FRONTEND)
    
    # 构建命令，针对不同操作系统
    if platform.system() == "Windows":
        cmd = ["npm.cmd", "start"]
    else:
        cmd = ["npm", "start"]
    
    # 启动前端进程
    try:
        process = subprocess.Popen(
            cmd,
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
            bufsize=1,
            universal_newlines=False
        )
        return process
    except Exception as e:
        print_colored(f"启动前端服务失败: {str(e)}", Colors.ERROR)
        return None

# 清理方法，用于关闭进程
def cleanup(backend_process, frontend_process):
    print_colored("\n正在清理进程...", Colors.WARNING)
    
    if backend_process and backend_process.poll() is None:
        print_colored("正在停止后端服务...", Colors.BACKEND)
        if platform.system() == "Windows":
            # Windows下使用taskkill强制结束进程树
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(backend_process.pid)])
        else:
            # Unix系统下发送SIGTERM信号
            os.killpg(os.getpgid(backend_process.pid), signal.SIGTERM)
    
    if frontend_process and frontend_process.poll() is None:
        print_colored("正在停止前端服务...", Colors.FRONTEND)
        if platform.system() == "Windows":
            # Windows下使用taskkill强制结束进程树
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(frontend_process.pid)])
        else:
            # Unix系统下发送SIGTERM信号
            os.killpg(os.getpgid(frontend_process.pid), signal.SIGTERM)
    
    print_colored("清理完成", Colors.WARNING)

def main():
    print_colored(f"{Colors.BOLD}=== SoftLink 开发环境启动 ==={Colors.END}", Colors.HEADER)
    
    # 获取项目根目录
    root_dir = get_project_root()
    print_colored(f"项目根目录: {root_dir}", Colors.HEADER)
    
    try:
        # 启动后端服务
        backend_process = start_backend(root_dir)
        if not backend_process:
            print_colored("后端服务启动失败，退出程序", Colors.ERROR)
            return
        
        # 启动监控后端输出的线程
        backend_thread = threading.Thread(
            target=monitor_output,
            args=(backend_process, "后端", Colors.BACKEND),
            daemon=True
        )
        backend_thread.start()
        
        # 等待几秒，确保后端启动正常
        time.sleep(5)
        
        # 启动前端服务
        frontend_process = start_frontend(root_dir)
        if not frontend_process:
            print_colored("前端服务启动失败", Colors.ERROR)
            cleanup(backend_process, None)
            return
        
        # 启动监控前端输出的线程
        frontend_thread = threading.Thread(
            target=monitor_output,
            args=(frontend_process, "前端", Colors.FRONTEND),
            daemon=True
        )
        frontend_thread.start()
        
        print_colored(f"{Colors.BOLD}=== 服务已启动 ==={Colors.END}", Colors.HEADER)
        print_colored("按 Ctrl+C 停止所有服务", Colors.WARNING)
        
        # 等待两个进程结束或用户中断
        while True:
            if backend_process.poll() is not None:
                print_colored("后端服务已终止", Colors.ERROR)
                break
            if frontend_process.poll() is not None:
                print_colored("前端服务已终止", Colors.ERROR)
                break
            time.sleep(0.5)
        
    except KeyboardInterrupt:
        print_colored("\n检测到用户中断", Colors.WARNING)
    finally:
        # 确保进程被清理
        cleanup(backend_process if 'backend_process' in locals() else None,
               frontend_process if 'frontend_process' in locals() else None)

if __name__ == "__main__":
    main() 