#!/bin/bash

# meme-commons 系统状态诊断脚本

echo "🔍 meme-commons 梗知识智能系统状态诊断"
echo "=================================================="
echo

# 检查conda环境
echo "📋 环境检查："
echo "1. conda环境状态："
if conda env list | grep -q "meme"; then
    echo "   ✅ meme环境存在"
    echo "   当前活跃环境: $(conda info --envs | grep '*')"
else
    echo "   ❌ meme环境不存在"
fi
echo

# 检查服务进程
echo "2. 服务进程状态："
BACKEND_PIDS=$(ps aux | grep -E "meme_commons\.main" | grep -v grep | awk '{print $2}')
FRONTEND_PIDS=$(ps aux | grep -E "streamlit.*8501" | grep -v grep | awk '{print $2}')

if [ -n "$BACKEND_PIDS" ]; then
    echo "   ✅ 后端MCP服务器运行中 (PID: $BACKEND_PIDS)"
else
    echo "   ❌ 后端MCP服务器未运行"
fi

if [ -n "$FRONTEND_PIDS" ]; then
    echo "   ✅ 前端Streamlit应用运行中 (PID: $FRONTEND_PIDS)"
else
    echo "   ❌ 前端Streamlit应用未运行"
fi
echo

# 检查端口占用
echo "3. 端口状态："
if netstat -tulpn 2>/dev/null | grep -q ":8002"; then
    echo "   ✅ 后端端口8002已监听"
else
    echo "   ❌ 后端端口8002未监听"
fi

if netstat -tulpn 2>/dev/null | grep -q ":8501"; then
    echo "   ✅ 前端端口8501已监听"
else
    echo "   ❌ 前端端口8501未监听"
fi
echo

# API连接测试
echo "4. API连接测试："
echo "   测试后端健康检查..."
if curl -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "   ✅ 后端API响应正常"
    echo "   健康状态: $(curl -s http://localhost:8002/health | jq -r '.status' 2>/dev/null || echo "无法解析")"
else
    echo "   ❌ 后端API无响应"
fi

echo "   测试梗知识查询..."
if curl -s "http://localhost:8002/mcp/knowledge?q=test" > /dev/null 2>&1; then
    echo "   ✅ 梗知识查询接口正常"
else
    echo "   ❌ 梗知识查询接口异常"
fi
echo

# 文件和目录检查
echo "5. 文件系统检查："
if [ -d "/home/codeserver/codes/meme_commons" ]; then
    echo "   ✅ meme_commons目录存在"
else
    echo "   ❌ meme_commons目录不存在"
fi

if [ -f "/home/codeserver/codes/meme_commons/start_meme_commons.sh" ]; then
    echo "   ✅ 启动脚本存在"
else
    echo "   ❌ 启动脚本不存在"
fi

if [ -f "/home/codeserver/codes/backend.pid" ]; then
    echo "   ✅ 后端PID文件存在"
    echo "   PID文件内容: $(cat /home/codeserver/codes/backend.pid)"
else
    echo "   ⚠️  后端PID文件不存在"
fi

if [ -f "/home/codeserver/codes/meme_commons/frontend.pid" ]; then
    echo "   ✅ 前端PID文件存在"
    echo "   PID文件内容: $(cat /home/codeserver/codes/meme_commons/frontend.pid)"
else
    echo "   ⚠️  前端PID文件不存在"
fi
echo

# 日志检查
echo "6. 最近日志检查："
if [ -f "/home/codeserver/codes/backend.log" ]; then
    echo "   后端日志最后5行："
    tail -5 /home/codeserver/codes/backend.log | sed 's/^/   /'
else
    echo "   ⚠️  后端日志文件不存在"
fi

if [ -f "/home/codeserver/codes/meme_commons/frontend.log" ]; then
    echo "   前端日志最后5行："
    tail -5 /home/codeserver/codes/meme_commons/frontend.log | sed 's/^/   /'
else
    echo "   ⚠️  前端日志文件不存在"
fi
echo

# 建议的操作
echo "💡 建议操作："
if [ -z "$BACKEND_PIDS" ] || [ -z "$FRONTEND_PIDS" ]; then
    echo "   🔄 运行启动脚本："
    echo "      cd /home/codeserver/codes/meme_commons"
    echo "      ./start_meme_commons.sh"
fi

if [ -f "/home/codeserver/codes/meme_commons/streamlit_app.py" ]; then
    echo "   🌐 访问前端界面：http://localhost:8501"
fi

if [ -f "/home/codeserver/codes/meme_commons/main.py" ]; then
    echo "   📚 查看API文档：http://localhost:8002/docs"
fi

echo
echo "=================================================="
echo "🎯 系统诊断完成！如需启动系统，请运行启动脚本。"