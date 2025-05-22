#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复startup.py语法错误的工具
"""

import re
import os
import sys

# 读取startup.py文件
with open('backend/startup.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 创建备份
with open('backend/startup.py.bak', 'w', encoding='utf-8') as f:
    f.write(content)

print("已创建备份: backend/startup.py.bak")

# 修复第43行附近可能的f-string语法错误
# 寻找模式: print(f"{prefix}{message}")
# 或类似的格式化字符串

# 替换所有的f-string为正常格式
# 问题代码: print(f"{prefix}{message}")
# 修复后: print("{}{}".format(prefix, message))
fixed_content = re.sub(
    r'print\(f"({[^}]+})({[^}]+})"\)',
    r'print("{}{}".format(\1, \2))',
    content
)

# 第二种模式: print_status(f"xxxx {变量} xxxx", 'xxx')
fixed_content = re.sub(
    r'print_status\(f"([^"]*){([^}]+)}([^"]*)"\s*,\s*\'([^\']+)\'\)',
    r'print_status("{}\1{}\3", \'\4\')'.format(r'{}', r'{}'),
    fixed_content
)

# 更新原文件
with open('backend/startup.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("已修复语法错误，请重新运行startup.py") 