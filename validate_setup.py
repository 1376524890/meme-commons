#!/usr/bin/env python3
"""
meme-commons 环境验证脚本
用于验证系统环境和依赖是否正确配置
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - 符合要求")
        return True
    else:
        print(f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print("   需要 Python 3.8 或更高版本")
        return False

def check_conda_env():
    """检查conda环境"""
    print("\n🔍 检查conda环境...")
    try:
        result = subprocess.run(['conda', 'env', 'list'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and 'meme' in result.stdout:
            print("✅ meme conda环境存在")
            return True
        else:
            print("❌ meme conda环境不存在")
            print("   请运行: conda create -n meme python=3.11 -y")
            return False
    except FileNotFoundError:
        print("❌ conda未安装")
        return False

def check_requirements_file():
    """检查requirements.txt文件"""
    print("\n🔍 检查requirements.txt...")
    req_file = Path(__file__).parent / "requirements.txt"
    if req_file.exists():
        print("✅ requirements.txt文件存在")
        return True
    else:
        print("❌ requirements.txt文件不存在")
        return False

def check_core_dependencies():
    """检查核心依赖包"""
    print("\n🔍 检查核心依赖包...")
    
    dependencies = [
        ('aiohttp', 'Web框架'),
        ('sqlalchemy', '数据库ORM'),
        ('streamlit', '前端框架'),
        ('requests', 'HTTP客户端'),
        ('pandas', '数据处理'),
        ('plotly', '数据可视化'),
        ('bs4', '网页解析'),  # beautifulsoup4导入名是bs4
        ('dotenv', '环境变量'),
        ('redis', '缓存'),
        ('numpy', '数值计算'),
        ('sklearn', '机器学习')  # scikit-learn导入名是sklearn
    ]
    
    missing = []
    
    for dep_name, description in dependencies:
        try:
            importlib.import_module(dep_name)
            print(f"✅ {dep_name} - {description}")
        except ImportError:
            print(f"❌ {dep_name} - {description}")
            missing.append(dep_name)
    
    if missing:
        print(f"\n⚠️  缺少依赖包: {', '.join(missing)}")
        print("   请运行: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ 所有核心依赖已安装")
        return True

def check_config_files():
    """检查配置文件"""
    print("\n🔍 检查配置文件...")
    
    config_files = ['.env.example']
    missing_files = []
    
    for config_file in config_files:
        file_path = Path(__file__).parent / config_file
        if file_path.exists():
            print(f"✅ {config_file} 存在")
        else:
            print(f"❌ {config_file} 不存在")
            missing_files.append(config_file)
    
    if missing_files:
        return False
    
    # 检查.env文件
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print("✅ .env文件存在")
    else:
        print("⚠️  .env文件不存在，使用默认配置")
        print("   建议复制.env.example并配置相关参数")
    
    return True

def check_directory_structure():
    """检查目录结构"""
    print("\n🔍 检查目录结构...")
    
    required_dirs = [
        'database',
        'tools', 
        'server',
        'docs'
    ]
    
    missing_dirs = []
    
    for dir_name in required_dirs:
        dir_path = Path(__file__).parent / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"✅ {dir_name}/ 目录存在")
        else:
            print(f"❌ {dir_name}/ 目录不存在")
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"\n⚠️  缺少目录: {', '.join(missing_dirs)}")
        return False
    else:
        print("\n✅ 目录结构完整")
        return True

def check_scripts():
    """检查脚本文件"""
    print("\n🔍 检查脚本文件...")
    
    scripts = [
        ('start_meme_commons.sh', '启动脚本'),
        ('launch.py', 'Python启动器'),
        ('main.py', '主程序'),
        ('streamlit_app.py', '前端应用')
    ]
    
    missing_scripts = []
    
    for script_name, description in scripts:
        script_path = Path(__file__).parent / script_name
        if script_path.exists():
            print(f"✅ {script_name} - {description}")
        else:
            print(f"❌ {script_name} - {description}")
            missing_scripts.append(script_name)
    
    if missing_scripts:
        print(f"\n⚠️  缺少脚本: {', '.join(missing_scripts)}")
        return False
    else:
        print("\n✅ 脚本文件完整")
        return True

def run_dependency_installation_guide():
    """提供依赖安装指南"""
    print("\n" + "="*60)
    print("📦 依赖安装指南")
    print("="*60)
    print("1. 安装conda环境:")
    print("   conda create -n meme python=3.11 -y")
    print("   conda activate meme")
    print()
    print("2. 安装依赖包:")
    print("   pip install -r requirements.txt")
    print()
    print("3. 配置环境变量:")
    print("   cp .env.example .env")
    print("   # 编辑.env文件，配置相关参数")
    print()
    print("4. 启动系统:")
    print("   ./start_meme_commons.sh")
    print("="*60)

def main():
    """主函数"""
    print("🎯 meme-commons 环境验证")
    print("="*60)
    
    # 运行所有检查
    checks = [
        check_python_version(),
        check_conda_env(),
        check_requirements_file(),
        check_core_dependencies(),
        check_config_files(),
        check_directory_structure(),
        check_scripts()
    ]
    
    print("\n" + "="*60)
    print("📊 检查结果汇总")
    print("="*60)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"🎉 所有检查通过 ({passed}/{total})")
        print("✅ 系统环境配置正确，可以启动服务")
        print("\n🚀 启动命令:")
        print("   ./start_meme_commons.sh")
    else:
        print(f"⚠️  部分检查失败 ({passed}/{total})")
        print("❌ 系统环境需要修复")
        run_dependency_installation_guide()
    
    print("="*60)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)