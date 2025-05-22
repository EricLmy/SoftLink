#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Python环境选择工具
- 检测可用的Python环境
- 选择合适的Python版本运行startup.py
"""

import os
import sys
import subprocess
import platform
import argparse

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='SoftLink环境选择工具')
    parser.add_argument('--port', type=int, default=5000,
                      help='指定后端服务端口（默认：5000）')
    return parser.parse_args()

def print_info(message):
    print("\033[1m[*]\033[0m {}".format(message))

def print_success(message):
    print("\033[92m[✓]\033[0m {}".format(message))

def print_error(message):
    print("\033[91m[✗]\033[0m {}".format(message))

def check_python_version(command):
    """检查Python版本是否满足要求"""
    try:
        result = subprocess.run([command, "-V"], 
                               capture_output=True, 
                               text=True, 
                               check=False)
        if result.returncode != 0:
            return None
        
        version_str = result.stdout.strip()
        print_info("找到: {}".format(version_str))
        
        # 解析版本号
        parts = version_str.split()
        if len(parts) >= 2:
            version = parts[1].split(".")
            if len(version) >= 2:
                major, minor = int(version[0]), int(version[1])
                if major >= 3 and minor >= 6:
                    return (command, major, minor)
        return None
    except Exception as e:
        print_error("检查版本时出错: {}".format(str(e)))
        return None

def find_compatible_python():
    """查找兼容的Python环境"""
    print_info("正在查找兼容的Python环境...")
    
    # 检查可能的Python命令
    commands = ["python3.9", "python3.8", "python3.7", "python3.6", "python3", "python"]
    
    # 在Windows环境中添加额外的路径检查
    if platform.system() == "Windows":
        possible_paths = [
            r"C:\Python39\python.exe",
            r"C:\Python38\python.exe",
            r"C:\Python37\python.exe",
            r"C:\Python36\python.exe",
            r"C:\Program Files\Python39\python.exe",
            r"C:\Program Files\Python38\python.exe",
            r"C:\Program Files\Python37\python.exe",
            r"C:\Program Files\Python36\python.exe",
            r"C:\Program Files (x86)\Python39\python.exe",
            r"C:\Program Files (x86)\Python38\python.exe",
            r"C:\Program Files (x86)\Python37\python.exe",
            r"C:\Program Files (x86)\Python36\python.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                commands.append(path)
    
    compatible_versions = []
    
    for cmd in commands:
        version_info = check_python_version(cmd)
        if version_info:
            compatible_versions.append(version_info)
    
    if not compatible_versions:
        print_error("未找到兼容的Python环境 (>=3.6)")
        return None
    
    # 按版本号排序，选择最高版本
    compatible_versions.sort(key=lambda x: (x[1], x[2]), reverse=True)
    best_version = compatible_versions[0]
    print_success("选择最佳Python环境: {} (v{}.{})".format(
        best_version[0], best_version[1], best_version[2]))
    
    return best_version[0]

def check_backend_dir():
    """确保backend目录存在"""
    if not os.path.exists("backend"):
        # 检查是否在backend目录内
        if os.path.exists("startup.py"):
            print_info("当前已在backend目录中")
            return True
        else:
            print_error("找不到backend目录或startup.py")
            return False
    return True

def check_port_available(port):
    """检查端口是否可用"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', port))
        sock.close()
        print_success("端口 {} 可用".format(port))
        return True
    except socket.error:
        sock.close()
        print_error("端口 {} 已被占用，请尝试其他端口".format(port))
        return False

def suggest_available_port():
    """建议可用的端口"""
    import socket
    # 尝试从5000开始找到一个可用端口
    for port in range(5000, 5100):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', port))
            sock.close()
            return port
        except socket.error:
            sock.close()
            continue
    return None

def main():
    """主函数"""
    print_info("SoftLink环境检测工具")
    
    # 解析命令行参数
    args = parse_args()
    port = args.port
    
    # 检查端口可用性
    if not check_port_available(port):
        available_port = suggest_available_port()
        if available_port:
            print_info("建议使用可用端口: {}".format(available_port))
            response = input("是否使用端口 {}? (y/n): ".format(available_port))
            if response.lower() == 'y':
                port = available_port
            else:
                print_info("请手动指定其他端口，例如: python choose_env.py --port 5001")
                sys.exit(1)
        else:
            print_error("无法找到可用端口，请尝试关闭占用端口的程序")
            sys.exit(1)
    
    # 找到合适的Python环境
    python_cmd = find_compatible_python()
    if not python_cmd:
        sys.exit(1)
    
    # 检查backend目录
    if not check_backend_dir():
        sys.exit(1)
    
    # 启动backend/startup.py
    print_info("正在启动SoftLink后端服务...")
    if os.path.exists("backend/startup.py"):
        startup_path = "backend/startup.py"
    else:
        startup_path = "startup.py"  # 假设已经在backend目录中
    
    try:
        # 启动后端服务
        print_success("使用 {} 启动 {} (端口: {})".format(python_cmd, startup_path, port))
        subprocess.run([python_cmd, startup_path, "--port", str(port)], check=True)
    except subprocess.CalledProcessError as e:
        print_error("启动服务失败: {}".format(str(e)))
        sys.exit(1)
    except KeyboardInterrupt:
        print_info("服务已被用户中断")
    
if __name__ == "__main__":
    main() 