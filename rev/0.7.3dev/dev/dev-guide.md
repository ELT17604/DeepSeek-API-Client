# DeepSeek API 客户端开发指南

## 版本信息
- **版本**: v0.7.3  
- **作者**: 1f84@ELT Group  
- **邮箱**: elt17604@outlook.com  
- **许可证**: GNU General Public License v3  

## 1. 模块概述
DeepSeek API 客户端采用模块化架构设计，将原始的单一文件拆分为 8 个独立的功能模块，每个模块负责特定的功能领域。

### 模块列表
- **config.py** – 配置管理模块，负责全局配置、常量定义和环境管理  
- **crypto_utils.py** – 加密工具模块，负责 API 密钥的安全存储和加密解密  
- **client_manager.py** – 客户端管理模块，负责 OpenAI 客户端的创建、管理和连接测试  
- **model_manager.py** – 模型管理模块，负责模型列表获取、过滤、搜索和选择  
- **chat_handler.py** – 聊天处理模块，负责对话会话管理、流式输出和消息处理  
- **http_utils.py** – HTTP 错误处理模块，负责 HTTP 状态码解析、错误处理和用户反馈  
- **balance_service.py** – 余额查询模块，负责账户余额查询、缓存和监控  
- **cli_client.py** – CLI 版本模块，负责命令行界面的交互和操作  

每个模块都具有独立的功能边界，通过明确的接口进行交互，支持单独使用或组合使用。

## 2. 各模块详细介绍

### 2.1 config.py – 配置管理模块
**主要特征**  
- 集中管理全局配置和常量  
- 支持环境检测和动态配置  
- 提供应用程序元信息管理  
- 支持模块间的配置共享  

**核心功能**  
- 全局常量定义：API 端点、超时设置、重试次数等  
- 应用信息管理：版本号、构建日期、作者信息等  
- HTTP 配置：请求超时、重试策略、缓存设置  
- 环境检测：操作系统、Python 版本、依赖检查  

**核心方法**  
```python
# 配置访问
APP_INFO = {
    'name': 'DeepSeek API Client',
    'version': 'v0.7.3',
    'description': 'DeepSeek API 的图形和命令行客户端',
    'author': '1f84@ELT Group',
    'build_date': '2025-01-25',
    'license': 'GPL-3.0'
}

DEEPSEEK_API_BASE_URL_V1 = "https://api.deepseek.com/v1"
DEEPSEEK_BALANCE_URL     = "https://api.deepseek.com/user/balance"

HTTP_CONFIG = {
    "timeout": 30,
    "max_retries": 3,
    "balance_cache_expiry": 300
}
```

**使用方式**
```python
from config import APP_INFO, DEEPSEEK_API_BASE_URL_V1, HTTP_CONFIG

app_name = APP_INFO['name']
version  = APP_INFO['version']

api_url  = DEEPSEEK_API_BASE_URL_V1
timeout  = HTTP_CONFIG['timeout']
```

### 2.2 crypto_utils.py – 加密工具模块
**主要特征**  
- 基于机器特征的密钥生成  
- AES-256 加密算法  
- 自动加密密钥管理  
- 跨平台兼容性  

**核心功能 & 方法**
```python
def get_encryption_key() -> bytes
def encrypt_api_key(api_key: str) -> str
def decrypt_api_key(encrypted_api_key: str) -> str
def save_api_key_to_file(api_key: str) -> bool
def load_api_key_from_file() -> str
def delete_api_key_file() -> bool
def generate_secure_key() -> bytes
def create_key_manager() -> KeyManager

class KeyManager:
    def __init__(self, key_file_path: str = None)
    def save_key(self, key: str, identifier: str = "default") -> bool
    def load_key(self, identifier: str = "default") -> str
    def delete_key(self, identifier: str = "default") -> bool
    def list_keys(self) -> List[str]
    def key_exists(self, identifier: str = "default") -> bool
```

**使用方式**
```python
from crypto_utils import save_api_key_to_file, load_api_key_from_file

# 保存API密钥
if save_api_key_to_file("your-api-key"):
    print("密钥保存成功")

# 加载API密钥
api_key = load_api_key_from_file()
if api_key:
    print(f"密钥已加载: {api_key[:4]}****")
```

### 2.3 client_manager.py – 客户端管理模块
**主要特征**  
- OpenAI 客户端的统一管理  
- 连接状态监控和验证  
- 自动重连机制  
- 多客户端实例支持  

**核心类 & 方法**
```python
class ClientManager:
    def __init__(self, gui_instance=None)
    def create_client(self, api_key: str, base_url: str = None) -> bool
    def test_client_connection(self, client=None) -> Tuple[bool, str]
    def validate_api_key(self, api_key: str) -> Tuple[bool, str]
    def get_client(self) -> OpenAI
    def get_api_key(self) -> str
    def is_client_ready(self) -> bool
    def destroy_client(self)
    def get_client_status(self) -> Dict
    def reconnect(self) -> bool
    def update_api_key(self, new_api_key: str) -> bool

def create_client_manager(gui_instance=None) -> ClientManager
def validate_api_key_simple(api_key: str) -> bool
def integrate_client_manager_with_gui(gui_instance) -> ClientManager
def test_api_connection(api_key: str, base_url: str = None) -> Tuple[bool, str]
```

**使用方式**
```python
from client_manager import create_client_manager

# 创建客户端管理器
manager = create_client_manager()

# 创建客户端
success = manager.create_client("your-api-key")
if success:
    client = manager.get_client()
    print("客户端创建成功")
```

### 2.4 model_manager.py – 模型管理模块
**主要特征**  
- 智能模型过滤算法  
- 多维度搜索功能  
- 缓存机制优化  
- 灵活的排序策略  

**核心类 & 方法**
```python
class ModelManager:
    def __init__(self, client_manager=None, gui_instance=None)
    def fetch_models(self, force_refresh: bool = False) -> Tuple[bool, List[str], str]
    def filter_models(self, models: List[str], filter_rules: Dict = None) -> List[str]
    def search_models(self, keyword: str, search_in: List[str] = None) -> List[str]
    def get_available_models(self) -> List[str]
    def select_model(self, model_name: str) -> bool
    def get_selected_model(self) -> str
    def get_model_info(self, model_name: str) -> Dict
    def clear_cache(self)
    def refresh_models_async(self, callback=None)

def filter_model_list(models: List[str], custom_keywords: List[str] = None) -> List[str]
def search_models_by_keyword(models: List[str], keyword: str) -> List[str]
def sort_models_by_relevance(models: List[str], keyword: str = None) -> List[str]
def get_model_category(model_name: str) -> str
def create_model_manager(client_manager=None, gui_instance=None) -> ModelManager
def integrate_model_manager_with_gui(gui_instance, client_manager) -> ModelManager
```

**使用方式**
```python
from model_manager import create_model_manager, filter_model_list

# 创建模型管理器
manager = create_model_manager(client_manager)

# 获取并过滤模型
success = manager.fetch_models()
if success:
    models = manager.get_available_models()
    chat_models = filter_model_list(models, ["chat"])
```

### 2.5 chat_handler.py – 聊天处理模块
**主要特征**  
- 完整的会话生命周期管理  
- 流式输出支持  
- 多会话并发处理  
- 丰富的统计信息  

**核心类 & 方法**
```python
class ChatSession:
    def __init__(self, model_name: str, session_id: str = None)
    def add_message(self, role: str, content: str)
    def get_messages(self) -> List[Dict]
    def clear_messages(self)
    def get_session_info(self) -> Dict
    def calculate_tokens(self, text: str) -> int
    def export_session(self, format: str = 'json') -> str
    def get_last_message(self, role: str = None) -> Dict

class ChatHandler:
    def __init__(self, client_manager=None, model_manager=None, gui_instance=None)
    def create_session(self, model_name: str = None) -> str
    def switch_session(self, session_id: str) -> bool
    def send_message(self, content: str, stream: bool = True) -> Tuple[bool, str, str]
    def handle_streaming_response(self, response, callback=None)
    def stop_streaming(self)
    def get_active_session(self) -> ChatSession
    def delete_session(self, session_id: str) -> bool
    def get_session_list(self) -> List[str]

def create_chat_session(model_name: str) -> ChatSession
def create_chat_handler(client_manager, model_manager, gui_instance=None) -> ChatHandler
def handle_streaming_chat(client, model: str, messages: List[Dict], callback=None)
def integrate_chat_handler_with_gui(gui_instance, client_manager, model_manager) -> ChatHandler
```

**使用方式**
```python
from chat_handler import create_chat_session, create_chat_handler

# 创建会话
session = create_chat_session("deepseek-chat")
session.add_message("user", "Hello")

# 创建聊天处理器
handler = create_chat_handler(client_manager, model_manager)
success, response, error = handler.send_message("How are you?")
```

### 2.6 http_utils.py – HTTP 错误处理模块
**主要特征**  
- 智能 HTTP 状态码识别  
- 用户友好的错误消息  
- 统一的错误处理接口  
- 详细的错误统计  

**核心类 & 方法**
```python
class HTTPErrorParser:
    def extract_status_code_from_error(self, error_msg: str) -> int
    def categorize_error(self, status_code: int) -> str
    def get_error_severity(self, status_code: int) -> str
    def parse_error_details(self, error_msg: str, response_data=None) -> Dict

class HTTPErrorMessages:
    def get_error_message(self, status_code: int, operation: str = None) -> Dict

class HTTPErrorDialog:
    def show_error_dialog(self, status_code: int, operation: str = None, details=None)
    def show_simple_error(self, title: str, message: str)
    def ask_yes_no(self, title: str, message: str) -> bool

class HTTPStatusTracker:
    def update_status(self, status_code: int, operation: str = None)
    def handle_error(self, error, operation: str = None, show_dialog: bool = True)
    def get_status_summary(self) -> Dict
    def reset_statistics(self)

def extract_http_status_code(error_msg: str) -> int
def show_http_error_dialog(status_code: int, operation: str = None, details=None)
def create_http_error_handler(gui_instance=None) -> HTTPErrorHandler
def handle_http_errors(operation: str = "HTTP操作", show_dialog: bool = True)
class HTTPErrorContext:
    def __init__(self, operation: str, error_handler=None, show_dialog: bool = True)
    def __enter__(self)
    def __exit__(self, exc_type, exc_val, exc_tb)
```

**使用方式**
```python
from http_utils import create_http_error_handler, handle_http_errors

# 创建错误处理器
handler = create_http_error_handler(gui_instance)

# 处理错误
handler.handle_api_error(exception, "模型获取")

# 使用装饰器
@handle_http_errors("余额查询")
def query_balance(self):
    pass

# 上下文管理器
with HTTPErrorContext("API 调用", handler):
    # 可能抛出异常的代码
    balance_service.query_balance()
```

### 2.7 balance_service.py – 余额查询模块
**主要特征**  
- 完整的余额信息管理  
- 智能缓存机制  
- 自动刷新策略  
- 详细的余额分析  

**核心类 & 方法**
```python
class BalanceInfo:
    def __init__(self, currency: str = "USD", total_balance: float = 0.0,
                 granted_balance: float = 0.0, topped_up_balance: float = 0.0)
    def format_display(self) -> str
    def format_detailed_display(self) -> str
    def is_low_balance(self, threshold: float = 1.0) -> bool
    def is_expired(self, max_age_seconds: int = 300) -> bool
    @classmethod
    def from_api_data(cls, api_data: Dict) -> BalanceInfo

class BalanceService:
    def __init__(self, gui_instance=None, client_manager=None)
    def query_balance(self, force_refresh: bool = False, use_cache: bool = True) -> Tuple[bool, BalanceResponse, str]
    def get_cached_balance(self) -> BalanceResponse
    def format_balance_for_display(self, balance_response=None) -> str
    def validate_balance_threshold(self, threshold: float = 1.0) -> Tuple[bool, float, str]
    def query_balance_async(self, callback=None, force_refresh: bool = False)
    def get_balance_summary(self) -> Dict
    def clear_cache(self)

class BalanceMonitor:
    def __init__(self, balance_service, check_interval: int = 3600, low_balance_threshold: float = 1.0)
    def start_monitoring(self)
    def stop_monitoring(self)
    def add_callback(self, callback)

def query_balance_simple(api_key: str, timeout: int = 30) -> Tuple[bool, Dict, str]
def format_balance_simple(balance_data: Dict) -> str
def create_balance_service(gui_instance=None, client_manager=None) -> BalanceService
def integrate_balance_service_with_gui(gui_instance, client_manager=None) -> BalanceService
def handle_balance_errors(operation: str = "余额查询")
```

**使用方式**
```python
from balance_service import create_balance_service, query_balance_simple

# 创建余额服务
service = create_balance_service(gui_instance, client_manager)

# 查询余额
success, response, error = service.query_balance()
if success:
    print(service.format_balance_for_display(response))

success, data, error = query_balance_simple("your-api-key")
```

### 2.8 cli_client.py – CLI 版本模块
**主要特征**  
- 完整的命令行交互界面  
- 彩色输出支持  
- 进度指示器  
- 丰富的命令集合  

**核心类 & 方法**
```python
class CLIInputHandler:
    def get_user_input(self, prompt: str, allow_empty: bool = False, validator=None) -> str
    def get_yes_no_input(self, prompt: str, default: bool = None) -> bool
    def get_choice_input(self, prompt: str, choices: List[str], default: int = None) -> int
    def get_password_input(self, prompt: str) -> str

class CLIOutputFormatter:
    def __init__(self, enable_colors: bool = True)
    def colorize(self, text: str, color: str) -> str
    def print_header(self, text: str)
    def print_success(self, text: str)
    def print_error(self, text: str)
    def print_warning(self, text: str)
    def print_info(self, text: str)

class DeepSeekCLI:
    def __init__(self)
    def load_api_key(self) -> bool
    def initialize_client(self) -> bool
    def fetch_models(self) -> bool
    def select_model(self) -> bool
    def start_chat(self) -> bool
    def query_balance(self) -> bool
    def run_interactive_mode(self)
    def run_guided_setup(self) -> bool
    def manage_config(self)
    def show_status(self)

def create_cli_client() -> DeepSeekCLI
def run_cli_with_args(args: List[str])
def quick_chat(api_key: str = None, model: str = None)
def quick_balance(api_key: str = None)
```

**使用方式**
```bash
# 命令行使用
python cli_client.py           # 快速模式
python cli_client.py --guided  # 引导模式
python cli_client.py --help    # 显示帮助

# 编程方式
from cli_client import create_cli_client, quick_chat

cli = create_cli_client()
cli.run(guided_mode=True)

quick_balance("your-api-key")
quick_chat("your-api-key", "deepseek-chat")
```

## 3. 各模块方法详细说明
### 3.1 config.py 导入和使用
```python
from config import APP_INFO, DEEPSEEK_API_BASE_URL_V1, DEEPSEEK_BALANCE_URL, HTTP_CONFIG

# 可用配置项说明...
```
*(其余详见上文模块介绍)*

### 3.2 crypto_utils.py 方法详解
```python
def get_encryption_key() -> bytes:
    """基于机器特定信息生成稳定的加密密钥"""
# … 更多函数和类说明 …
```

*(其余模块方法请参照第 2 节对应小节)*

## 4. 集成和使用示例

### 4.1 GUI 集成示例
```python
from gui_main import DeepSeekGUI
from client_manager import integrate_client_manager_with_gui
from model_manager import integrate_model_manager_with_gui
from chat_handler import integrate_chat_handler_with_gui
from balance_service import integrate_balance_service_with_gui
from http_utils import integrate_http_error_handler_with_gui
import tkinter as tk

root = tk.Tk()
app  = DeepSeekGUI(root)

client_manager    = integrate_client_manager_with_gui(app)
model_manager     = integrate_model_manager_with_gui(app, client_manager)
chat_handler      = integrate_chat_handler_with_gui(app, client_manager, model_manager)
balance_service   = integrate_balance_service_with_gui(app, client_manager)
http_error_handler = integrate_http_error_error_handler_with_gui(app)

root.mainloop()
```

### 4.2 CLI 应用示例
```python
from cli_client import create_cli_client, quick_chat, quick_balance

cli = create_cli_client()
cli.run(guided_mode=True)

quick_balance("your-api-key")
quick_chat("your-api-key", "deepseek-chat")
```

### 4.3 独立模块使用示例
```python
from client_manager import create_client_manager
from model_manager import create_model_manager
from chat_handler import create_chat_handler
from balance_service import create_balance_service

client_manager = create_client_manager()
model_manager  = create_model_manager(client_manager)
chat_handler   = create_chat_handler(client_manager, model_manager)
balance_service= create_balance_service(None, client_manager)

success = client_manager.create_client("your-api-key")
if success:
    manager.fetch_models()
    models = model_manager.get_available_models()
    model_manager.select_model(models[0])

    session_id = chat_handler.create_session()
    success, response, error = chat_handler.send_message("Hello!")

    success, balance, error = balance_service.query_balance()
```

## 5. 错误处理和调试

### 5.1 错误处理最佳实践
```python
from http_utils import handle_http_errors, HTTPErrorContext

class MyAPIClient:
    @handle_http_errors("模型获取")
    def fetch_models(self):
        pass

with HTTPErrorContext("余额查询", error_handler):
    balance_service.query_balance()
```

### 5.2 日志和调试
```python
import logging
from config import APP_INFO

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info(f"启动 {APP_INFO['name']} {APP_INFO['version']}")
```

### 5.3 测试和验证
```python
from crypto_utils import validate_encryption
from client_manager import test_api_connection
from model_manager import validate_model_list

if validate_encryption():
    print("加密功能正常")

success, error = test_api_connection("your-api-key")
if success:
    print("API 连接正常")

models = ["deepseek-chat", "deepseek-coder"]
if validate_model_list(models):
    print("模型列表有效")
```
