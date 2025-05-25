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

import json
import re
import tkinter as tk
from tkinter import messagebox
from config import HTTP_CONFIG, HTTP_STATUS_MESSAGES, HTTP_ERROR_DESCRIPTIONS

class HTTPErrorParser:
    """HTTP错误解析器，提供错误状态码提取和分析功能"""
    
    def __init__(self):
        """初始化HTTP错误解析器"""
        # 错误关键词映射
        self.error_keywords_map = {
            'unauthorized': 401,
            '401': 401,
            'forbidden': 403,
            '403': 403,
            'not found': 404,
            '404': 404,
            'unprocessable entity': 422,
            '422': 422,
            'too many requests': 429,
            'rate limit': 429,
            '429': 429,
            'internal server error': 500,
            '500': 500,
            'bad gateway': 502,
            '502': 502,
            'service unavailable': 503,
            '503': 503
        }
        
        # 网络错误关键词
        self.network_keywords = ['timeout', 'connection', 'network', 'resolve', 'dns']
    
    def extract_status_code_from_error(self, error_msg):
        """
        从错误消息中提取HTTP状态码
        
        Args:
            error_msg (str): 错误消息
            
        Returns:
            int: HTTP状态码，如果无法提取返回0
        """
        if not error_msg:
            return 0
        
        # 尝试从错误消息中直接提取HTTP状态码
        status_match = re.search(r'status_code[:=]\s*(\d+)', error_msg, re.IGNORECASE)
        if status_match:
            return int(status_match.group(1))
        
        # 尝试匹配HTTP错误响应格式
        http_match = re.search(r'HTTP\s+(\d{3})', error_msg, re.IGNORECASE)
        if http_match:
            return int(http_match.group(1))
        
        # 尝试匹配状态码:数字格式
        code_match = re.search(r'(\d{3})\s*[:]\s*', error_msg)
        if code_match:
            code = int(code_match.group(1))
            if 100 <= code <= 599:  # 验证是有效的HTTP状态码
                return code
        
        # 根据错误关键词推断状态码
        error_lower = error_msg.lower()
        for keyword, code in self.error_keywords_map.items():
            if keyword in error_lower:
                return code
        
        # 检查是否为网络错误
        for keyword in self.network_keywords:
            if keyword in error_lower:
                return 0
        
        return 0  # 默认返回0表示未知错误
    
    def categorize_error(self, status_code):
        """
        根据状态码分类错误
        
        Args:
            status_code (int): HTTP状态码
            
        Returns:
            str: 错误类别 ('client', 'server', 'network', 'unknown')
        """
        if status_code == 0:
            return 'network'
        elif 400 <= status_code <= 499:
            return 'client'
        elif 500 <= status_code <= 599:
            return 'server'
        elif 200 <= status_code <= 299:
            return 'success'
        elif 300 <= status_code <= 399:
            return 'redirect'
        else:
            return 'unknown'
    
    def get_error_severity(self, status_code):
        """
        获取错误严重程度
        
        Args:
            status_code (int): HTTP状态码
            
        Returns:
            str: 错误严重程度 ('low', 'medium', 'high', 'critical')
        """
        if status_code == 0:
            return 'high'  # 网络错误
        elif status_code in [401, 403]:
            return 'critical'  # 认证和授权错误
        elif status_code in [429, 500, 502, 503]:
            return 'high'  # 限流和服务器错误
        elif status_code in [400, 404, 422]:
            return 'medium'  # 客户端错误
        elif status_code == 402:
            return 'critical'  # 余额不足
        else:
            return 'low'
    
    def parse_error_details(self, error_msg, response_data=None):
        """
        解析错误详情
        
        Args:
            error_msg (str): 错误消息
            response_data (dict): 响应数据
            
        Returns:
            dict: 解析后的错误信息
        """
        status_code = self.extract_status_code_from_error(error_msg)
        
        result = {
            'status_code': status_code,
            'category': self.categorize_error(status_code),
            'severity': self.get_error_severity(status_code),
            'original_message': error_msg,
            'parsed_details': None
        }
        
        # 尝试解析响应数据
        if response_data:
            if isinstance(response_data, dict):
                result['parsed_details'] = response_data
            elif isinstance(response_data, str):
                try:
                    result['parsed_details'] = json.loads(response_data)
                except json.JSONDecodeError:
                    result['parsed_details'] = {'raw_response': response_data}
        
        return result

class HTTPErrorMessages:
    """HTTP错误消息管理器，提供用户友好的错误消息"""
    
    def __init__(self):
        """初始化错误消息管理器"""
        # 标准HTTP状态码消息映射
        self.status_messages = {
            400: {
                'title': '请求格式错误',
                'message': '请求格式错误 (Bad Request)。请检查您的请求参数。',
                'suggestion': '请检查输入的参数格式是否正确。'
            },
            401: {
                'title': 'API密钥无效',
                'message': 'API密钥无效或未授权 (Unauthorized)。请检查您的API密钥是否正确且有权限访问该服务。',
                'suggestion': '请检查API密钥是否正确，或联系服务提供商确认账户状态。'
            },
            402: {
                'title': '余额不足',
                'message': '余额不足 (Payment Required)。您的账户余额可能不足以完成此操作。',
                'suggestion': '请充值您的账户或检查账户余额。'
            },
            403: {
                'title': '禁止访问',
                'message': '禁止访问 (Forbidden)。您没有权限执行此操作。',
                'suggestion': '请检查您的账户权限或联系管理员。'
            },
            404: {
                'title': '未找到资源',
                'message': '未找到资源 (Not Found)。请求的资源不存在。',
                'suggestion': '请检查请求的URL或资源名称是否正确。'
            },
            422: {
                'title': '参数错误',
                'message': '无法处理的实体 (Unprocessable Entity)。通常表示请求参数不符合API要求。',
                'suggestion': '请检查请求参数的格式和内容是否符合API规范。'
            },
            429: {
                'title': '请求过于频繁',
                'message': '请求过于频繁 (Too Many Requests)。请稍后再试。',
                'suggestion': '请降低请求频率或稍后重试。'
            },
            500: {
                'title': '服务器内部错误',
                'message': '服务器内部错误 (Internal Server Error)。请稍后再试。',
                'suggestion': '这是服务器端问题，请稍后重试或联系技术支持。'
            },
            502: {
                'title': '网关错误',
                'message': '网关错误 (Bad Gateway)。上游服务器返回无效响应。',
                'suggestion': '这是服务器网关问题，请稍后重试。'
            },
            503: {
                'title': '服务不可用',
                'message': '服务不可用 (Service Unavailable)。服务器当前无法处理请求，请稍后再试。',
                'suggestion': '服务器正在维护或过载，请稍后重试。'
            },
            0: {
                'title': '网络错误',
                'message': '网络连接失败。请检查您的网络连接。',
                'suggestion': '请检查网络连接，确认防火墙设置，或稍后重试。'
            }
        }
        
        # 操作特定的错误消息
        self.operation_specific_messages = {
            '初始化': {
                401: '初始化失败：API密钥无效。请检查您的API密钥是否正确。',
                403: '初始化失败：访问被禁止。请检查您的账户状态。',
                0: '初始化失败：网络连接错误。请检查网络连接。'
            },
            '模型获取': {
                401: '获取模型失败：API密钥无效。',
                429: '获取模型失败：请求过于频繁，请稍后再试。',
                0: '获取模型失败：网络连接错误。'
            },
            '余额查询': {
                401: '余额查询失败：API密钥无效。',
                402: '余额查询失败：账户状态异常。',
                0: '余额查询失败：网络连接错误。'
            },
            '聊天': {
                401: '聊天失败：API密钥无效。',
                402: '聊天失败：账户余额不足。',
                429: '聊天失败：请求过于频繁，请稍后再试。',
                0: '聊天失败：网络连接错误。'
            }
        }
    
    def get_error_message(self, status_code, operation=None):
        """
        获取错误消息
        
        Args:
            status_code (int): HTTP状态码
            operation (str): 操作类型
            
        Returns:
            dict: 包含title、message、suggestion的错误信息
        """
        # 优先使用操作特定的消息
        if operation and operation in self.operation_specific_messages:
            if status_code in self.operation_specific_messages[operation]:
                message = self.operation_specific_messages[operation][status_code]
                return {
                    'title': f'{operation}错误',
                    'message': message,
                    'suggestion': self.status_messages.get(status_code, {}).get('suggestion', '请稍后重试。')
                }
        
        # 使用标准消息
        if status_code in self.status_messages:
            return self.status_messages[status_code].copy()
        
        # 根据状态码范围生成通用消息
        if 400 <= status_code <= 499:
            return {
                'title': '客户端错误',
                'message': f'客户端错误 ({status_code})。请检查您的请求。',
                'suggestion': '请检查请求参数和API密钥。'
            }
        elif 500 <= status_code <= 599:
            return {
                'title': '服务器错误',
                'message': f'服务器错误 ({status_code})。这是服务器端问题。',
                'suggestion': '请稍后重试或联系技术支持。'
            }
        else:
            return {
                'title': '未知错误',
                'message': f'发生未知错误 (状态码: {status_code})。',
                'suggestion': '请稍后重试或联系技术支持。'
            }

class HTTPErrorDialog:
    """HTTP错误对话框管理器"""
    
    def __init__(self, message_manager=None):
        """
        初始化错误对话框管理器
        
        Args:
            message_manager: 错误消息管理器实例
        """
        self.message_manager = message_manager or HTTPErrorMessages()
    
    def show_error_dialog(self, status_code, operation=None, details=None):
        """
        显示HTTP错误对话框
        
        Args:
            status_code (int): HTTP状态码
            operation (str): 操作描述
            details: 错误详情（字符串或字典）
        """
        error_info = self.message_manager.get_error_message(status_code, operation)
        
        title = f"HTTP错误: {status_code}"
        if operation:
            title += f" ({operation})"
        
        # 构建消息内容
        message_parts = [
            f"在操作 '{operation}' 期间发生HTTP错误。" if operation else "发生HTTP错误。",
            f"状态码: {status_code}",
            "",
            error_info['message']
        ]
        
        # 添加建议
        if error_info.get('suggestion'):
            message_parts.extend(["", "建议:", error_info['suggestion']])
        
        # 添加详细信息
        if details:
            message_parts.extend(["", "详细信息:"])
            try:
                if isinstance(details, str):
                    # 尝试解析JSON
                    try:
                        details_obj = json.loads(details)
                        details_str = json.dumps(details_obj, indent=2, ensure_ascii=False)
                    except json.JSONDecodeError:
                        details_str = details
                elif isinstance(details, dict):
                    details_str = json.dumps(details, indent=2, ensure_ascii=False)
                else:
                    details_str = str(details)
                
                # 限制详细信息的长度
                if len(details_str) > 500:
                    details_str = details_str[:500] + "...\n(详细信息已截断)"
                
                message_parts.append(details_str)
            except Exception:
                message_parts.append(str(details))
        
        message = "\n".join(message_parts)
        
        # 显示对话框
        messagebox.showerror(title, message)
    
    def show_simple_error(self, title, message):
        """
        显示简单错误对话框
        
        Args:
            title (str): 对话框标题
            message (str): 错误消息
        """
        messagebox.showerror(title, message)
    
    def show_warning(self, title, message):
        """
        显示警告对话框
        
        Args:
            title (str): 对话框标题
            message (str): 警告消息
        """
        messagebox.showwarning(title, message)
    
    def show_info(self, title, message):
        """
        显示信息对话框
        
        Args:
            title (str): 对话框标题
            message (str): 信息内容
        """
        messagebox.showinfo(title, message)
    
    def ask_yes_no(self, title, message):
        """
        显示是否确认对话框
        
        Args:
            title (str): 对话框标题
            message (str): 询问消息
            
        Returns:
            bool: 用户选择结果
        """
        return messagebox.askyesno(title, message)

class HTTPStatusTracker:
    """HTTP状态跟踪器，用于跟踪和管理HTTP状态"""
    
    def __init__(self, gui_instance=None):
        """
        初始化HTTP状态跟踪器
        
        Args:
            gui_instance: GUI实例，用于状态更新
        """
        self.gui = gui_instance
        self.current_status = 200  # 默认状态
        self.last_operation = None
        self.error_count = 0
        self.success_count = 0
        self.status_history = []
        
        # 初始化组件
        self.parser = HTTPErrorParser()
        self.message_manager = HTTPErrorMessages()
        self.dialog = HTTPErrorDialog(self.message_manager)
    
    def update_status(self, status_code, operation=None):
        """
        更新HTTP状态
        
        Args:
            status_code (int): HTTP状态码
            operation (str): 操作描述
        """
        self.current_status = status_code
        self.last_operation = operation
        
        # 更新统计
        if 200 <= status_code <= 299:
            self.success_count += 1
        else:
            self.error_count += 1
        
        # 记录历史
        import time
        self.status_history.append({
            'timestamp': time.time(),
            'status_code': status_code,
            'operation': operation
        })
        
        # 限制历史记录数量
        if len(self.status_history) > 100:
            self.status_history = self.status_history[-50:]
        
        # 更新GUI状态（如果有）
        if self.gui and hasattr(self.gui, 'update_http_status'):
            self.gui.update_http_status(status_code, operation)
    
    def handle_error(self, error, operation=None, show_dialog=True):
        """
        处理错误
        
        Args:
            error: 异常对象或错误消息
            operation (str): 操作描述
            show_dialog (bool): 是否显示错误对话框
        """
        error_msg = str(error)
        status_code = self.parser.extract_status_code_from_error(error_msg)
        
        # 更新状态
        self.update_status(status_code, operation)
        
        # 显示错误对话框
        if show_dialog and self.gui:
            self.dialog.show_error_dialog(status_code, operation)
        
        # 记录错误日志（如果GUI有print_out方法）
        if self.gui and hasattr(self.gui, 'print_out'):
            error_info = self.message_manager.get_error_message(status_code, operation)
            self.gui.print_out(f"{operation}失败: {error_info['message']}")
    
    def get_status_summary(self):
        """
        获取状态摘要
        
        Returns:
            dict: 状态摘要信息
        """
        total_requests = self.success_count + self.error_count
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'current_status': self.current_status,
            'last_operation': self.last_operation,
            'total_requests': total_requests,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': round(success_rate, 2),
            'recent_errors': [
                h for h in self.status_history[-10:] 
                if not (200 <= h['status_code'] <= 299)
            ]
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.error_count = 0
        self.success_count = 0
        self.status_history = []

class HTTPErrorHandler:
    """HTTP错误处理器，提供统一的错误处理接口"""
    
    def __init__(self, gui_instance=None):
        """
        初始化HTTP错误处理器
        
        Args:
            gui_instance: GUI实例
        """
        self.gui = gui_instance
        self.parser = HTTPErrorParser()
        self.message_manager = HTTPErrorMessages()
        self.dialog = HTTPErrorDialog(self.message_manager)
        self.tracker = HTTPStatusTracker(gui_instance)
    
    def handle_api_error(self, error, operation="API操作", show_dialog=True):
        """
        处理API错误
        
        Args:
            error: 异常对象或错误消息
            operation (str): 操作描述
            show_dialog (bool): 是否显示错误对话框
        """
        self.tracker.handle_error(error, operation, show_dialog)
    
    def handle_response_error(self, response, operation="HTTP请求"):
        """
        处理HTTP响应错误
        
        Args:
            response: HTTP响应对象
            operation (str): 操作描述
        """
        status_code = response.status_code
        self.tracker.update_status(status_code, operation)
        
        if not (200 <= status_code <= 299):
            # 尝试获取响应详情
            details = None
            try:
                details = response.json()
            except:
                try:
                    details = response.text
                except:
                    details = None
            
            self.dialog.show_error_dialog(status_code, operation, details)
    
    def extract_status_code(self, error_msg):
        """
        提取状态码（便捷方法）
        
        Args:
            error_msg (str): 错误消息
            
        Returns:
            int: HTTP状态码
        """
        return self.parser.extract_status_code_from_error(error_msg)
    
    def get_error_message(self, status_code, operation=None):
        """
        获取错误消息（便捷方法）
        
        Args:
            status_code (int): HTTP状态码
            operation (str): 操作类型
            
        Returns:
            dict: 错误消息信息
        """
        return self.message_manager.get_error_message(status_code, operation)
    
    def show_error_dialog(self, status_code, operation=None, details=None):
        """
        显示错误对话框（便捷方法）
        
        Args:
            status_code (int): HTTP状态码
            operation (str): 操作描述
            details: 错误详情
        """
        self.dialog.show_error_dialog(status_code, operation, details)
    
    def get_status_summary(self):
        """
        获取状态摘要（便捷方法）
        
        Returns:
            dict: 状态摘要
        """
        return self.tracker.get_status_summary()

# 便捷函数
def create_http_error_handler(gui_instance=None):
    """
    创建HTTP错误处理器的便捷函数
    
    Args:
        gui_instance: GUI实例
        
    Returns:
        HTTPErrorHandler: HTTP错误处理器实例
    """
    return HTTPErrorHandler(gui_instance)

def extract_http_status_code(error_msg):
    """
    提取HTTP状态码的独立函数
    
    Args:
        error_msg (str): 错误消息
        
    Returns:
        int: HTTP状态码
    """
    parser = HTTPErrorParser()
    return parser.extract_status_code_from_error(error_msg)

def show_http_error_dialog(status_code, operation=None, details=None):
    """
    显示HTTP错误对话框的独立函数
    
    Args:
        status_code (int): HTTP状态码
        operation (str): 操作描述
        details: 错误详情
    """
    dialog = HTTPErrorDialog()
    dialog.show_error_dialog(status_code, operation, details)

def get_http_error_message(status_code, operation=None):
    """
    获取HTTP错误消息的独立函数
    
    Args:
        status_code (int): HTTP状态码
        operation (str): 操作类型
        
    Returns:
        dict: 错误消息信息
    """
    message_manager = HTTPErrorMessages()
    return message_manager.get_error_message(status_code, operation)

# GUI集成函数
def integrate_http_error_handler_with_gui(gui_instance):
    """
    将HTTP错误处理器集成到GUI实例中
    
    Args:
        gui_instance: GUI实例
    """
    # 创建HTTP错误处理器
    error_handler = create_http_error_handler(gui_instance)
    
    # 将处理器绑定到GUI
    gui_instance.http_error_handler = error_handler
    
    # 重写GUI的相关方法
    def new_show_http_error_dialog(status_code, operation, details=None):
        return error_handler.show_error_dialog(status_code, operation, details)
    
    def new_extract_status_code_from_error(error_msg):
        return error_handler.extract_status_code(error_msg)
    
    # 绑定方法到GUI
    gui_instance.show_http_error_dialog = new_show_http_error_dialog
    gui_instance.extract_status_code_from_error = new_extract_status_code_from_error
    
    # 添加HTTP错误处理相关方法到GUI
    gui_instance.get_http_error_handler = lambda: error_handler
    gui_instance.handle_api_error = lambda error, op="API操作": error_handler.handle_api_error(error, op)
    gui_instance.get_http_status_summary = lambda: error_handler.get_status_summary()
    
    return error_handler

# 错误处理装饰器
def handle_http_errors(operation="HTTP操作", show_dialog=True):
    """
    HTTP错误处理装饰器
    
    Args:
        operation (str): 操作描述
        show_dialog (bool): 是否显示错误对话框
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                if hasattr(self, 'http_error_handler'):
                    self.http_error_handler.handle_api_error(e, operation, show_dialog)
                elif hasattr(self, 'gui') and self.gui:
                    # 如果没有错误处理器，使用基本处理
                    error_msg = str(e)
                    status_code = extract_http_status_code(error_msg)
                    if self.gui and hasattr(self.gui, 'update_http_status'):
                        self.gui.update_http_status(status_code, operation)
                    if show_dialog:
                        show_http_error_dialog(status_code, operation)
                else:
                    print(f"{operation}失败: {e}")
                return None
        return wrapper
    return decorator

# 上下文管理器
class HTTPErrorContext:
    """HTTP错误上下文管理器，用于自动错误处理"""
    
    def __init__(self, operation, error_handler=None, show_dialog=True):
        """
        初始化HTTP错误上下文
        
        Args:
            operation (str): 操作描述
            error_handler: HTTP错误处理器
            show_dialog (bool): 是否显示错误对话框
        """
        self.operation = operation
        self.error_handler = error_handler or HTTPErrorHandler()
        self.show_dialog = show_dialog
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.error_handler.handle_api_error(exc_val, self.operation, self.show_dialog)
            return True  # 抑制异常
        return False

# 测试和示例代码
if __name__ == "__main__":
    # 创建HTTP错误处理器进行测试
    print("HTTP错误处理器测试")
    print("=" * 30)
    
    handler = create_http_error_handler()
    
    # 测试状态码提取
    test_errors = [
        "HTTP 401: Unauthorized",
        "status_code: 429",
        "Connection timeout error",
        "Rate limit exceeded (429)",
        "Internal server error occurred"
    ]
    
    for error in test_errors:
        status_code = handler.extract_status_code(error)
        print(f"错误: {error[:30]}... -> 状态码: {status_code}")
    
    # 测试错误消息获取
    test_codes = [401, 429, 500, 0]
    for code in test_codes:
        message = handler.get_error_message(code, "测试操作")
        print(f"状态码 {code}: {message['title']} - {message['message']}")
    
    # 测试状态跟踪
    handler.tracker.update_status(200, "成功操作")
    handler.tracker.update_status(401, "失败操作")
    summary = handler.get_status_summary()
    print(f"\n状态摘要: {summary}")
    
    # 测试上下文管理器
    try:
        with HTTPErrorContext("测试操作", handler, show_dialog=False):
            raise Exception("status_code: 401")
    except:
        pass  # 异常被上下文管理器处理
    
    print("HTTP错误处理器测试完成")