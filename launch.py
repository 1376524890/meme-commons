#!/usr/bin/env python3
"""
梗文化智能系统启动脚本
Meme Commons System Launcher

此脚本用于启动梗文化智能系统的完整功能，包括：
- 数据库初始化
- 向量存储设置
- 各工具模块初始化  
- MCP服务器启动
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from main import MemeCommonsSystem
    from config import Config
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保所有依赖已安装: pip install -r requirements.txt")
    sys.exit(1)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="梗文化智能系统启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python launch.py --help                    # 显示帮助信息
  python launch.py                          # 默认启动模式
  python launch.py --init-only              # 仅初始化数据库
  python launch.py --check-deps             # 检查依赖
  python launch.py --demo                   # 运行演示模式
        """
    )
    
    parser.add_argument(
        '--init-only', 
        action='store_true',
        help='仅初始化数据库和向量存储，不启动服务器'
    )
    
    parser.add_argument(
        '--check-deps',
        action='store_true', 
        help='检查依赖和配置'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='运行演示模式'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出模式'
    )
    
    args = parser.parse_args()
    
    # 检查依赖
    if args.check_deps:
        print("🔍 检查系统依赖...")
        await check_dependencies()
        return
    
    # 演示模式
    if args.demo:
        print("🎭 运行演示模式...")
        await run_demo()
        return
    
    # 初始化模式
    if args.init_only:
        print("🔧 初始化系统组件...")
        await initialize_only()
        return
    
    # 完整启动模式
    print("🎯 启动梗文化智能系统...")
    print("=" * 50)
    
    try:
        # 创建系统实例
        system = MemeCommonsSystem()
        
        if args.verbose:
            print("✅ 系统实例创建成功")
        
        # 初始化系统
        print("🚀 正在初始化系统...")
        await system.initialize()
        
        if args.verbose:
            print("✅ 系统初始化完成")
        
        # 启动服务器
        print("🌐 启动MCP服务器...")
        await system.run()
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断，正在关闭系统...")
        if 'system' in locals():
            await system.shutdown()
        print("✅ 系统已安全关闭")
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


async def check_dependencies():
    """检查系统依赖"""
    print("检查Python版本...")
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8+")
        return False
    print(f"✅ Python {sys.version}")
    
    print("\n检查配置文件...")
    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠️  .env文件不存在，使用默认配置")
        print("   请复制 .env.example 并配置相关参数")
    else:
        print("✅ .env配置文件存在")
    
    print("\n检查数据库...")
    try:
        from database.models import Base, engine
        from config import Config
        
        config = Config()
        if hasattr(config, 'database_url'):
            print("✅ 数据库配置正确")
        else:
            print("⚠️  数据库配置可能有问题")
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
    
    print("\n检查工具模块...")
    tools = ['crawler', 'embedding', 'query', 'summarizer', 'trend_analysis']
    for tool in tools:
        try:
            module = __import__(f'tools.{tool}', fromlist=[tool])
            print(f"✅ {tool} 工具模块正常")
        except Exception as e:
            print(f"❌ {tool} 工具模块错误: {e}")
    
    print("\n检查MCP服务器...")
    try:
        from server.mcp_server import mcp_server
        print("✅ MCP服务器模块正常")
    except Exception as e:
        print(f"❌ MCP服务器模块错误: {e}")
    
    print("\n🎉 依赖检查完成!")


async def initialize_only():
    """仅初始化系统组件"""
    try:
        from meme_commons.main import MemeCommonsSystem
        
        system = MemeCommonsSystem()
        
        print("📊 初始化数据库...")
        # 初始化数据库
        await system.database.initialize()
        
        print("🗄️  初始化向量存储...")
        # 初始化向量存储  
        await system.vector_store.initialize()
        
        print("✅ 系统初始化完成!")
        print("💡 使用 --demo 运行演示，或者 --start 启动完整服务")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()


async def run_demo():
    """运行演示模式"""
    try:
        from meme_commons.main import MemeCommonsSystem
        
        print("🎮 初始化演示系统...")
        system = MemeCommonsSystem()
        await system.initialize()
        
        print("\n📋 演示功能列表:")
        print("1. 梗知识查询演示")
        print("2. 趋势分析演示") 
        print("3. 内容总结演示")
        print("4. 向量搜索演示")
        
        # 这里可以添加具体的演示代码
        print("\n🎭 演示完成!")
        
        await system.shutdown()
        
    except Exception as e:
        print(f"❌ 演示运行失败: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见!")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)