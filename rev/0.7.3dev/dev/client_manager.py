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

import re
import json
from openai import OpenAI
from config import DEEPSEEK_API_BASE_URL_V1, HTTP_CONFIG
from crypto_utils import save_api_key_to_file, validate_api_key_format, mask_api_key

class ClientManager:
    """DeepSeek API 客户端管理器"""
    
    def __init__(self, gui_instance=None):
        """
        初始化客户端管理器
        
        Args:
            gui_instance: GUI实例，用于状态更新和用户交互
        """
        self.gui = gui_instance
        self.client = None
        self.api_key = ""
        self.is_initialized = False
        
    def validate_api_key_input(self, api_key):
        """
        验证API密钥输入
        
        Args:
            api_key (str): 要验证的API密钥
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not api_key:
            return False, "API密钥不能为空"
        
        api_key = api_key.strip()
        
        if len(api_key) < 10:
            return False, "API密钥长度太短"
        
        if not validate_api_key_format(api_key):
            return False, "API密钥格式无效"
        
        return True, None
    
    def create_client(self, api_key):
        """
        创建OpenAI客户端实例
        
        Args:
            api_key (str): API密钥
            
        Returns:
            OpenAI: 客户端实例，如果创建失败返回None
        """
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=DEEPSEEK_API_BASE_URL_V1,
                timeout=HTTP_CONFIG.get("timeout", 30)
            )
            return client
        except Exception as e:
            if self.gui:
                self.gui.print_out(f"创建客户端时出错: {e}")
            return None
    
    def test_client_connection(self, client):
        """
        测试客户端连接有效性
        
        Args:
            client: OpenAI客户端实例
            
        Returns:
            tuple: (success, status_code, error_message)
        """
        try:
            # 尝试获取模型列表来验证连接
            models_response = client.models.list()
            
            # 如果成功获取模型列表，说明连接有效
            if models_response and hasattr(models_response, 'data'):
                return True, 200, None
            else:
                return False, 0, "获取模型列表失败"
                
        except Exception as e:
            error_msg = str(e)
            status_code = self._extract_status_code_from_error(error_msg)
            return False, status_code, error_msg
    
    def _extract_status_code_from_error(self, error_msg):
        """
        从错误消息中提取HTTP状态码
        
        Args:
            error_msg (str): 错误消息
            
        Returns:
            int: HTTP状态码，如果无法提取返回0
        """
        # 尝试从错误消息中提取HTTP状态码
        status_match = re.search(r'status_code:\s*(\d+)', error_msg)
        if status_match:
            return int(status_match.group(1))
        
        # 根据错误关键词推断状态码
        error_keywords = {
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
        
        error_lower = error_msg.lower()
        for keyword, code in error_keywords.items():
            if keyword in error_lower:
                return code
        
        # 如果包含网络相关关键词，返回0表示网络错误
        network_keywords = ['timeout', 'connection', 'network', 'resolve']
        for keyword in network_keywords:
            if keyword in error_lower:
                return 0
        
        return 0  # 默认返回0表示未知错误
    
    def initialize_client(self, api_key=None):
        """
        初始化客户端
        
        Args:
            api_key (str): API密钥，如果为None则从GUI获取
            
        Returns:
            bool: 初始化是否成功
        """
        # 从GUI获取API密钥（如果未提供）
        if api_key is None and self.gui:
            api_key = self.gui.get_api_key_from_entry()
        
        if not api_key:
            if self.gui:
                self.gui.show_error_message("错误", "请输入API密钥")
            return False
        
        # 验证API密钥格式
        is_valid, error_msg = self.validate_api_key_input(api_key)
        if not is_valid:
            if self.gui:
                self.gui.show_error_message("错误", f"API密钥验证失败: {error_msg}")
            return False
        
        # 更新状态为初始化中
        if self.gui:
            self.gui.update_client_status()
            self.gui.print_out("正在初始化客户端...")
        
        # 创建客户端
        test_client = self.create_client(api_key)
        if not test_client:
            if self.gui:
                self.gui.update_client_status()
                self.gui.show_error_message("错误", "客户端创建失败")
            return False
        
        # 测试客户端连接
        if self.gui:
            self.gui.print_out("正在测试客户端连接...")
        
        success, status_code, error_message = self.test_client_connection(test_client)
        
        if not success:
            # 连接测试失败
            if self.gui:
                self.gui.update_http_status(status_code, "初始化")
                
                # 显示相应的错误信息
                if status_code == 401:
                    self.gui.show_error_message("认证失败", 
                        "API密钥无效或未授权。请检查您的API密钥是否正确且有权限访问该服务。")
                elif status_code == 403:
                    self.gui.show_error_message("访问被禁", 
                        "您没有权限访问该服务。请检查您的账户状态。")
                elif status_code == 429:
                    self.gui.show_error_message("请求限制", 
                        "请求过于频繁。请稍后再试。")
                elif status_code == 0:
                    self.gui.show_error_message("网络错误", 
                        f"网络连接失败: {error_message}")
                else:
                    self.gui.show_error_message("连接失败", 
                        f"客户端连接测试失败 (HTTP {status_code}): {error_message}")
                
                self.gui.update_client_status()
                self.gui.print_out(f"客户端初始化失败: HTTP {status_code}")
            
            return False
        
        # 连接测试成功，保存客户端和API密钥
        self.client = test_client
        self.api_key = api_key
        self.is_initialized = True
        
        # 更新HTTP状态为成功
        if self.gui:
            self.gui.update_http_status(200, "初始化")
        
        # 保存API密钥到文件
        try:
            if save_api_key_to_file(api_key):
                if self.gui:
                    self.gui.print_out("API Key已安全加密并保存到本地文件。")
        except Exception as e:
            if self.gui:
                self.gui.print_out(f"保存API密钥时出错: {e}")
        
        # 更新GUI状态
        if self.gui:
            self._update_gui_after_initialization()
        
        if self.gui:
            self.gui.print_out("客户端初始化成功!")
        
        return True
    
    def _update_gui_after_initialization(self):
        """初始化成功后更新GUI状态"""
        if not self.gui:
            return
        
        try:
            # 隐藏API密钥输入框，显示掩码
            self.gui.api_key_entry.pack_forget()
            
            # 显示掩码后的API密钥
            masked_key = mask_api_key(self.api_key)
            self.gui.api_key_masked_label.config(text=masked_key, anchor="w")
            self.gui.api_key_masked_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
            
            # 将初始化按钮改为修改按钮
            self.gui.init_btn.config(text="修改", command=self.gui.change_api_key)
            
            # 启用相关控件
            if hasattr(self.gui, 'enable_control'):
                self.gui.enable_control('refresh_models', True)
                self.gui.enable_control('clear_api', True)
            else:
                # 回退方法
                if hasattr(self.gui, 'refresh_models_btn'):
                    self.gui.refresh_models_btn.config(state=tk.NORMAL)
                if hasattr(self.gui, 'clear_apikey_btn'):
                    self.gui.clear_apikey_btn.config(state=tk.NORMAL)
            
            # 设置客户端引用
            self.gui.client = self.client
            self.gui.api_key = self.api_key
            
            # 更新客户端状态
            if hasattr(self.gui, 'update_client_status'):
                self.gui.update_client_status()
            if hasattr(self.gui, 'update_buttons_state'):
                self.gui.update_buttons_state()
                
        except Exception as e:
            print(f"更新GUI状态时出错: {e}")

    
    def reset_client(self):
        """重置客户端状态"""
        self.client = None
        self.api_key = ""
        self.is_initialized = False
        
        if self.gui:
            self.gui.client = None
            self.gui.api_key = ""
    
    def get_client(self):
        """
        获取当前客户端实例
        
        Returns:
            OpenAI: 客户端实例，如果未初始化返回None
        """
        return self.client if self.is_initialized else None
    
    def get_api_key(self):
        """
        获取当前API密钥
        
        Returns:
            str: API密钥，如果未初始化返回空字符串
        """
        return self.api_key if self.is_initialized else ""
    
    def is_client_ready(self):
        """
        检查客户端是否就绪
        
        Returns:
            bool: 客户端是否已初始化且可用
        """
        return self.is_initialized and self.client is not None
    
    def test_current_client(self):
        """
        测试当前客户端连接
        
        Returns:
            bool: 连接是否正常
        """
        if not self.is_client_ready():
            return False
        
        success, status_code, error_message = self.test_client_connection(self.client)
        
        if self.gui:
            self.gui.update_http_status(status_code, "连接测试")
            if not success:
                self.gui.print_out(f"连接测试失败: {error_message}")
            else:
                self.gui.print_out("连接测试成功")
        
        return success
    
    def handle_api_error(self, error, operation="未知操作"):
        """
        处理API调用错误
        
        Args:
            error: 异常对象
            operation (str): 操作描述
        """
        error_msg = str(error)
        status_code = self._extract_status_code_from_error(error_msg)
        
        if self.gui:
            self.gui.update_http_status(status_code, operation)
            
            # 根据状态码显示相应的错误对话框
            if status_code in [400, 401, 402, 403, 404, 422, 429, 500, 502, 503]:
                self.gui.show_http_error_dialog(status_code, operation)
            elif status_code == 0:
                self.gui.print_out(f"网络错误 ({operation}): {error_msg}")
            else:
                self.gui.print_out(f"未知错误 ({operation}): {error_msg}")
    
    def get_client_info(self):
        """
        获取客户端信息
        
        Returns:
            dict: 客户端信息字典
        """
        return {
            "is_initialized": self.is_initialized,
            "has_client": self.client is not None,
            "has_api_key": bool(self.api_key),
            "api_key_masked": mask_api_key(self.api_key) if self.api_key else "",
            "base_url": DEEPSEEK_API_BASE_URL_V1,
            "timeout": HTTP_CONFIG.get("timeout", 30)
        }
    
    def update_client_settings(self, timeout=None):
        """
        更新客户端设置
        
        Args:
            timeout (int): 新的超时时间
        """
        if timeout is not None and self.client:
            try:
                # 重新创建客户端以应用新设置
                new_client = OpenAI(
                    api_key=self.api_key,
                    base_url=DEEPSEEK_API_BASE_URL_V1,
                    timeout=timeout
                )
                self.client = new_client
                
                if self.gui:
                    self.gui.client = self.client
                    self.gui.print_out(f"客户端超时设置已更新为 {timeout} 秒")
                    
            except Exception as e:
                if self.gui:
                    self.gui.print_out(f"更新客户端设置失败: {e}")
    
    def validate_client_health(self):
        """
        验证客户端健康状态
        
        Returns:
            dict: 健康检查结果
        """
        result = {
            "healthy": False,
            "errors": [],
            "warnings": [],
            "info": {}
        }
        
        # 检查基本状态
        if not self.is_initialized:
            result["errors"].append("客户端未初始化")
            return result
        
        if not self.client:
            result["errors"].append("客户端实例不存在")
            return result
        
        if not self.api_key:
            result["errors"].append("API密钥为空")
            return result
        
        # 测试连接
        try:
            success, status_code, error_message = self.test_client_connection(self.client)
            
            if success:
                result["healthy"] = True
                result["info"]["status_code"] = status_code
                result["info"]["connection"] = "正常"
            else:
                result["errors"].append(f"连接测试失败: {error_message}")
                result["info"]["status_code"] = status_code
                result["info"]["connection"] = "失败"
                
        except Exception as e:
            result["errors"].append(f"健康检查异常: {e}")
        
        # 检查API密钥格式
        is_valid, error_msg = self.validate_api_key_input(self.api_key)
        if not is_valid:
            result["warnings"].append(f"API密钥格式警告: {error_msg}")
        
        return result
    
    def reinitialize_client(self):
        """
        重新初始化客户端（使用当前API密钥）
        
        Returns:
            bool: 重新初始化是否成功
        """
        if not self.api_key:
            if self.gui:
                self.gui.show_error_message("错误", "没有可用的API密钥进行重新初始化")
            return False
        
        if self.gui:
            self.gui.print_out("正在重新初始化客户端...")
        
        # 重置当前状态
        old_client = self.client
        self.reset_client()
        
        # 尝试重新初始化
        success = self.initialize_client(self.api_key)
        
        if not success and old_client:
            # 如果重新初始化失败，恢复旧客户端
            self.client = old_client
            self.is_initialized = True
            if self.gui:
                self.gui.client = self.client
                self.gui.print_out("重新初始化失败，已恢复到之前的客户端状态")
        
        return success
    
    def destroy(self):
        """销毁客户端管理器并清理资源"""
        self.reset_client()
        self.gui = None

# 便捷函数
def create_client_manager(gui_instance=None):
    """
    创建客户端管理器的便捷函数
    
    Args:
        gui_instance: GUI实例
        
    Returns:
        ClientManager: 客户端管理器实例
    """
    return ClientManager(gui_instance)

def validate_deepseek_api_key(api_key):
    """
    验证DeepSeek API密钥格式
    
    Args:
        api_key (str): API密钥
        
    Returns:
        bool: 是否有效
    """
    manager = ClientManager()
    is_valid, _ = manager.validate_api_key_input(api_key)
    return is_valid

def test_deepseek_connection(api_key):
    """
    测试DeepSeek API连接
    
    Args:
        api_key (str): API密钥
        
    Returns:
        tuple: (success, status_code, error_message)
    """
    manager = ClientManager()
    client = manager.create_client(api_key)
    
    if not client:
        return False, 0, "客户端创建失败"
    
    return manager.test_client_connection(client)

# GUI集成函数
def integrate_client_manager_with_gui(gui_instance):
    """
    将客户端管理器集成到GUI实例中
    
    Args:
        gui_instance: GUI实例
    """
    # 创建客户端管理器
    client_manager = create_client_manager(gui_instance)
    
    # 将管理器绑定到GUI
    gui_instance.client_manager = client_manager
    
    # 重写GUI的initialize_client方法
    def new_initialize_client():
        return client_manager.initialize_client()
    
    gui_instance.initialize_client = new_initialize_client
    
    # 添加客户端管理相关方法到GUI
    gui_instance.get_client_manager = lambda: client_manager
    gui_instance.test_client_connection = lambda: client_manager.test_current_client()
    gui_instance.reinitialize_client = lambda: client_manager.reinitialize_client()
    gui_instance.get_client_info = lambda: client_manager.get_client_info()
    gui_instance.validate_client_health = lambda: client_manager.validate_client_health()
    
    return client_manager

# 错误处理装饰器
def handle_client_errors(operation="API操作"):
    """
    客户端错误处理装饰器
    
    Args:
        operation (str): 操作描述
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                if hasattr(self, 'client_manager'):
                    self.client_manager.handle_api_error(e, operation)
                elif hasattr(self, 'gui') and self.gui:
                    # 直接处理错误
                    error_msg = str(e)
                    status_code = 0
                    
                    # 简单的状态码提取
                    if 'status_code:' in error_msg:
                        try:
                            status_code = int(re.search(r'status_code:\s*(\d+)', error_msg).group(1))
                        except:
                            pass
                    
                    self.gui.update_http_status(status_code, operation)
                    self.gui.print_out(f"{operation}失败: {error_msg}")
                else:
                    print(f"{operation}失败: {e}")
                return None
        return wrapper
    return decorator

# 测试和示例代码
if __name__ == "__main__":
    # 创建客户端管理器进行测试
    print("客户端管理器测试")
    print("=" * 30)
    
    manager = create_client_manager()
    
    # 测试API密钥验证
    test_keys = [
        "",
        "sk-123",
        "sk-" + "a" * 40,
        "invalid-key"
    ]
    
    for key in test_keys:
        is_valid, error = manager.validate_api_key_input(key)
        print(f"密钥: {key[:10]}... -> 有效: {is_valid}, 错误: {error}")
    
    # 测试客户端信息
    info = manager.get_client_info()
    print(f"\n客户端信息: {info}")
    
    # 测试健康检查
    health = manager.validate_client_health()
    print(f"\n健康检查: {health}")