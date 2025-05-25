# Copyright (c) 2025 1f84@ELT Group
# Email: elt17604@outlook.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# Additional Terms:
# This software may not be used for commercial purposes.
# Any redistribution of this software must retain this notice.

import os

# ===================== 版本信息 =====================
APP_VERSION = "0.7.3"
APP_NAME = "DeepSeek API Client"
APP_COPYRIGHT = "© 2025 ELT Group"

# 应用程序信息字典（为了兼容其他模块）
APP_INFO = {
    'name': APP_NAME,
    'version': APP_VERSION,
    'description': 'DeepSeek API 的图形和命令行客户端',
    'author': '1f84@ELT Group',
    'build_date': '2025-01-25',
    'license': 'GPL-3.0',
    'copyright': APP_COPYRIGHT,
    'url': 'https://github.com/your-repo'  # 可选：项目URL
}

# 确保版权信息存在
if 'APP_COPYRIGHT' not in globals():
    APP_COPYRIGHT = f"© 2025 {APP_INFO.get('author', '1f84@ELT Group')}"

# 确保窗口配置存在
if 'WINDOW_CONFIG' not in globals():
    WINDOW_CONFIG = {
        "main_window": {
            "title": f"{APP_NAME} GUI",
            "geometry": "800x600",
            "min_size": (600, 400)
        }
    }

# 确保字体配置存在
if 'FONT_CONFIG' not in globals():
    FONT_CONFIG = {
        "default_family": "TkDefaultFont",
        "default_size": 11,
        "size_range": {"min": 8, "max": 24}
    }

# ===================== API 配置 =====================
# API 基础URL
DEEPSEEK_API_BASE_URL_V1 = "https://api.deepseek.com/v1"

# 余额查询URL
DEEPSEEK_BALANCE_URL = "https://api.deepseek.com/user/balance"

# 网络状态检测域名和端口
NETWORK_CHECK_HOST = "api.deepseek.com"
NETWORK_CHECK_PORT = 443

# ===================== 文件路径配置 =====================
# 脚本目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# API Key 存储文件名
API_KEY_FILENAME = os.path.join(SCRIPT_DIR, "API_KEY")

# ===================== 加密配置 =====================
# 加密盐值
ENCRYPTION_SALT = "deepseek-client-salt-v1"

# 默认加密种子（当无法获取机器ID时使用）
DEFAULT_ENCRYPTION_SEED = "default-salt-key"

# ===================== 网络请求配置 =====================
# HTTP 请求配置
HTTP_CONFIG = {
    # 请求超时设置（秒）
    "timeout": 30,
    
    # 重试次数
    "max_retries": 3,
    
    # 重试间隔（秒）
    "retry_delay": 1,
    
    # 连接超时（秒）
    "connect_timeout": 10,
    
    # 读取超时（秒）
    "read_timeout": 30
}

# 网络状态检测配置
NETWORK_STATUS_CONFIG = {
    # 检测间隔（秒）
    "check_interval": 30,
    
    # 连接超时（秒）
    "timeout": 5,
    
    # 延迟阈值设置（毫秒）
    "latency_thresholds": {
        "good": 200,      # 绿色：小于200ms
        "warning": 500    # 黄色：200-500ms，红色：大于500ms
    }
}

# ===================== API 请求头配置 =====================
# 标准请求头
DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": f"{APP_NAME}/{APP_VERSION}"
}

# 认证请求头模板（需要动态填入API Key）
def get_auth_headers(api_key):
    """获取包含认证信息的请求头"""
    headers = DEFAULT_HEADERS.copy()
    headers["Authorization"] = f"Bearer {api_key}"
    return headers

# ===================== 聊天配置 =====================
# 聊天参数配置
CHAT_CONFIG = {
    # 默认聊天参数
    "default_params": {
        "max_tokens": 4096,
        "temperature": 0.7,
        "stream": True
    },
    
    # 参数范围限制
    "param_limits": {
        "max_tokens": {"min": 1, "max": 8192},
        "temperature": {"min": 0.0, "max": 2.0}
    }
}

# ===================== UI 配置 =====================
# 字体配置
FONT_CONFIG = {
    # 默认字体设置
    "default_family": "TkDefaultFont",
    "default_size": 11,
    
    # 字体大小范围
    "size_range": {"min": 8, "max": 24},
    
    # 代码字体优先级
    "code_fonts": ["Consolas", "Courier New", "Monaco", "monospace"]
}

# 窗口配置
WINDOW_CONFIG = {
    # 主窗口
    "main_window": {
        "title": f"{APP_NAME} GUI",
        "geometry": "800x600",
        "min_size": (600, 400)
    },
    
    # 状态监控窗口
    "status_window": {
        "title": "状态监控",
        "geometry": "320x160",
        "resizable": False,
        "topmost": True
    }
}

# ===================== 状态配置 =====================
# 状态指示灯颜色映射
STATUS_COLORS = {
    "red": "#ff4444",
    "green": "#44ff44",
    "yellow": "#ffcc00",
    "gray": "#888888",
    "grey": "#888888"
}

# 状态类型定义
STATUS_TYPES = {
    "client": "客户端",
    "network": "网络",
    "model": "模型",
    "http": "HTTP",
    "chat": "聊天"
}

# HTTP 状态码映射
HTTP_STATUS_MESSAGES = {
    200: "正常",
    400: "格式错误",
    401: "认证失败",
    402: "余额不足",
    403: "访问被禁",
    404: "未找到",
    422: "参数错误",
    429: "请求限制",
    500: "服务器错误",
    502: "网关错误",
    503: "服务器繁忙"
}

# HTTP 错误详细描述
HTTP_ERROR_DESCRIPTIONS = {
    400: "请求格式错误 (Bad Request)。请检查您的请求参数。",
    401: "API密钥无效或未授权 (Unauthorized)。请检查您的API密钥是否正确且有权限访问该服务。",
    402: "余额不足 (Payment Required)。您的账户余额可能不足以完成此操作。",
    403: "禁止访问 (Forbidden)。您没有权限执行此操作。",
    404: "未找到资源 (Not Found)。请求的资源不存在。",
    422: "无法处理的实体 (Unprocessable Entity)。通常表示请求参数不符合API要求。",
    429: "请求过于频繁 (Too Many Requests)。请稍后再试。",
    500: "服务器内部错误 (Internal Server Error)。请稍后再试。",
    502: "网关错误 (Bad Gateway)。上游服务器返回无效响应。",
    503: "服务不可用 (Service Unavailable)。服务器当前无法处理请求，请稍后再试。"
}

# ===================== 模型过滤配置 =====================
# 模型过滤规则
MODEL_FILTER_CONFIG = {
    # 包含这些关键词的模型会被优先显示
    "priority_keywords": ["chat", "coder"],
    
    # 当模型数量少于此数值时，显示所有模型
    "show_all_threshold": 10,
    
    # 排除的模型名称模式（正则表达式）
    "exclude_patterns": []
}

# ===================== 日志配置 =====================
# 日志配置
LOG_CONFIG = {
    # 是否启用时间戳
    "enable_timestamp": True,
    
    # 时间戳格式
    "timestamp_format": "[%H:%M:%S]",
    
    # 日志级别
    "level": "INFO"
}

# ===================== 安全配置 =====================
# 安全相关配置
SECURITY_CONFIG = {
    # API Key 掩码配置
    "api_key_mask": {
        "show_prefix": 2,  # 显示前N位
        "show_suffix": 2,  # 显示后N位
        "mask_char": "*"   # 掩码字符
    },
    
    # 文件权限配置
    "file_permissions": {
        "api_key_file": 0o600  # 仅当前用户可读写
    }
}

# ===================== 调试配置 =====================
# 调试模式配置
DEBUG_CONFIG = {
    # 是否启用调试模式
    "enabled": False,
    
    # 详细错误信息
    "verbose_errors": False,
    
    # 网络请求日志
    "log_requests": False
}

# ===================== 自定义配置支持 =====================
def load_custom_config():
    """加载用户自定义配置文件（如果存在）"""
    custom_config_path = os.path.join(SCRIPT_DIR, "custom_config.py")
    if os.path.exists(custom_config_path):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("custom_config", custom_config_path)
            custom_config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(custom_config)
            
            # 合并自定义配置到全局配置
            globals().update({
                key: value for key, value in vars(custom_config).items()
                if not key.startswith('_')
            })
            print(f"已加载自定义配置: {custom_config_path}")
        except Exception as e:
            print(f"加载自定义配置失败: {e}")

# 自动加载自定义配置
load_custom_config()

# ===================== 配置验证 =====================
def validate_config():
    """验证配置文件的有效性"""
    errors = []
    
    # 验证URL格式
    import re
    url_pattern = re.compile(r'^https?://.+')
    
    if not url_pattern.match(DEEPSEEK_API_BASE_URL_V1):
        errors.append(f"无效的API基础URL: {DEEPSEEK_API_BASE_URL_V1}")
    
    if not url_pattern.match(DEEPSEEK_BALANCE_URL):
        errors.append(f"无效的余额查询URL: {DEEPSEEK_BALANCE_URL}")
    
    # 验证数值范围
    if not (1 <= HTTP_CONFIG["timeout"] <= 300):
        errors.append(f"HTTP超时时间应在1-300秒之间: {HTTP_CONFIG['timeout']}")
    
    if not (1 <= NETWORK_STATUS_CONFIG["check_interval"] <= 3600):
        errors.append(f"网络检测间隔应在1-3600秒之间: {NETWORK_STATUS_CONFIG['check_interval']}")
    
    # 验证字体大小范围
    if FONT_CONFIG["size_range"]["min"] >= FONT_CONFIG["size_range"]["max"]:
        errors.append("字体大小最小值应小于最大值")
    
    if errors:
        print("配置验证错误:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True

# 程序启动时验证配置
if __name__ != "__main__":
    validate_config()