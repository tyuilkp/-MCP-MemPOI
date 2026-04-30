#!/usr/bin/env python3
"""
快速开始脚本
一键初始化 MCP-MemPOI 项目
"""

import os
import sys
import subprocess

# 设置 UTF-8 输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def run_command(cmd, description):
    """运行命令并显示进度"""
    print(f"\n{description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"失败: {result.stderr}")
        return False
    print(f"完成")
    return True


def main():
    print("=" * 60)
    print("  MCP-MemPOI 快速开始")
    print("=" * 60)

    # 检查 Python 版本
    if sys.version_info < (3, 7):
        print("❌ 需要 Python 3.7 或更高版本")
        sys.exit(1)

    # 1. 安装依赖
    if not run_command("pip install -r requirements.txt", "安装依赖包"):
        sys.exit(1)

    # 2. 初始化数据库
    if not run_command("python init_db.py", "初始化数据库"):
        sys.exit(1)

    # 3. 生成示例数据
    if not run_command("python sample_data.py", "生成示例数据"):
        sys.exit(1)

    # 4. 运行演示
    print("\n" + "=" * 60)
    print("  运行演示脚本")
    print("=" * 60)
    subprocess.run("python scripts/run_demo.py", shell=True)

    print("\n" + "=" * 60)
    print("  初始化完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 配置 MCP 客户端（参考 README.md）")
    print("2. 启动服务器: python server.py")
    print("3. 在 Claude Desktop 或 Claude Code 中使用 MCP-MemPOI 工具")


if __name__ == "__main__":
    main()
