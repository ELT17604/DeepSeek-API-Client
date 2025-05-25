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
import requests
import threading
import time
from config import DEEPSEEK_BALANCE_URL, HTTP_CONFIG

class BalanceInfo:
    """余额信息数据类"""
    
    def __init__(self, currency="USD", total_balance=0.0, granted_balance=0.0, topped_up_balance=0.0):
        """
        初始化余额信息
        
        Args:
            currency (str): 货币类型
            total_balance (float): 总余额
            granted_balance (float): 授权余额
            topped_up_balance (float): 充值余额
        """
        self.currency = currency
        self.total_balance = total_balance
        self.granted_balance = granted_balance
        self.topped_up_balance = topped_up_balance
        self.last_updated = time.time()
    
    def to_dict(self):
        """
        转换为字典格式
        
        Returns:
            dict: 余额信息字典
        """
        return {
            "currency": self.currency,
            "total_balance": self.total_balance,
            "granted_balance": self.granted_balance,
            "topped_up_balance": self.topped_up_balance,
            "last_updated": self.last_updated
        }
    
    def format_display(self):
        """
        格式化显示字符串
        
        Returns:
            str: 格式化的余额显示字符串
        """
        return f"{self.total_balance} {self.currency}"
    
    def format_detailed_display(self):
        """
        格式化详细显示字符串
        
        Returns:
            str: 格式化的详细余额显示字符串
        """
        lines = [
            f"货币: {self.currency}",
            f"总余额: {self.total_balance}",
            f"授权余额: {self.granted_balance}",
            f"充值余额: {self.topped_up_balance}"
        ]
        return "\n".join(lines)
    
    def is_low_balance(self, threshold=1.0):
        """
        检查余额是否过低
        
        Args:
            threshold (float): 低余额阈值
            
        Returns:
            bool: 是否为低余额
        """
        return self.total_balance < threshold
    
    def is_expired(self, max_age_seconds=300):
        """
        检查余额信息是否过期
        
        Args:
            max_age_seconds (int): 最大有效时间（秒）
            
        Returns:
            bool: 是否过期
        """
        return time.time() - self.last_updated > max_age_seconds
    
    @classmethod
    def from_api_data(cls, api_data):
        """
        从API响应数据创建余额信息对象
        
        Args:
            api_data (dict): API响应的余额数据
            
        Returns:
            BalanceInfo: 余额信息对象
        """
        return cls(
            currency=api_data.get('currency', 'USD'),
            total_balance=float(api_data.get('total_balance', 0.0)),
            granted_balance=float(api_data.get('granted_balance', 0.0)),
            topped_up_balance=float(api_data.get('topped_up_balance', 0.0))
        )

class BalanceResponse:
    """余额查询响应数据类"""
    
    def __init__(self, is_available=False, balance_infos=None, message="", raw_data=None):
        """
        初始化余额响应
        
        Args:
            is_available (bool): 服务是否可用
            balance_infos (list): 余额信息列表
            message (str): 响应消息
            raw_data (dict): 原始响应数据
        """
        self.is_available = is_available
        self.balance_infos = balance_infos or []
        self.message = message
        self.raw_data = raw_data or {}
        self.query_time = time.time()
    
    def get_primary_balance(self):
        """
        获取主要余额信息
        
        Returns:
            BalanceInfo: 主要余额信息，如果没有则返回None
        """
        return self.balance_infos[0] if self.balance_infos else None
    
    def get_total_balance_display(self):
        """
        获取总余额显示字符串
        
        Returns:
            str: 总余额显示字符串
        """
        primary = self.get_primary_balance()
        if primary:
            return primary.format_display()
        return "N/A"
    
    def has_balance_info(self):
        """
        检查是否有余额信息
        
        Returns:
            bool: 是否有余额信息
        """
        return len(self.balance_infos) > 0
    
    def to_dict(self):
        """
        转换为字典格式
        
        Returns:
            dict: 响应信息字典
        """
        return {
            "is_available": self.is_available,
            "balance_infos": [info.to_dict() for info in self.balance_infos],
            "message": self.message,
            "query_time": self.query_time,
            "has_balance_info": self.has_balance_info()
        }
    
    @classmethod
    def from_api_response(cls, response_data):
        """
        从API响应创建余额响应对象
        
        Args:
            response_data (dict): API响应数据
            
        Returns:
            BalanceResponse: 余额响应对象
        """
        is_available = response_data.get("is_available", False)
        message = response_data.get("message", "")
        
        balance_infos = []
        if "balance_infos" in response_data:
            for info_data in response_data["balance_infos"]:
                balance_infos.append(BalanceInfo.from_api_data(info_data))
        
        return cls(
            is_available=is_available,
            balance_infos=balance_infos,
            message=message,
            raw_data=response_data
        )

class BalanceService:
    """余额查询服务"""
    
    def __init__(self, gui_instance=None, client_manager=None):
        """
        初始化余额服务
        
        Args:
            gui_instance: GUI实例，用于状态更新和用户交互
            client_manager: 客户端管理器实例
        """
        self.gui = gui_instance
        self.client_manager = client_manager
        
        # 缓存相关
        self.last_balance_response = None
        self.cache_expiry_seconds = HTTP_CONFIG.get("balance_cache_expiry", 300)  # 5分钟缓存
        
        # 请求配置
        self.timeout = HTTP_CONFIG.get("timeout", 30)
        self.max_retries = HTTP_CONFIG.get("max_retries", 3)
        
        # 状态跟踪
        self.last_query_time = None
        self.query_count = 0
        self.error_count = 0
    
    def extract_status_code_from_error(self, error_msg):
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
    
    def get_api_key(self):
        """
        获取API密钥
        
        Returns:
            str: API密钥，如果无法获取返回None
        """
        # 从客户端管理器获取
        if self.client_manager:
            api_key = self.client_manager.get_api_key()
            if api_key:
                return api_key
        
        # 从GUI获取
        if self.gui and hasattr(self.gui, 'api_key'):
            return self.gui.api_key
        
        return None
    
    def is_cache_valid(self):
        """
        检查缓存是否有效
        
        Returns:
            bool: 缓存是否有效
        """
        if not self.last_balance_response:
            return False
        
        cache_age = time.time() - self.last_balance_response.query_time
        return cache_age < self.cache_expiry_seconds
    
    def query_balance(self, force_refresh=False, use_cache=True):
        """
        查询账户余额
        
        Args:
            force_refresh (bool): 是否强制刷新，忽略缓存
            use_cache (bool): 是否使用缓存
            
        Returns:
            tuple: (success, balance_response, error_message)
        """
        # 检查缓存
        if use_cache and not force_refresh and self.is_cache_valid():
            if self.gui:
                self.gui.print_out("使用缓存的余额信息")
            return True, self.last_balance_response, None
        
        # 获取API密钥
        api_key = self.get_api_key()
        if not api_key:
            error_msg = "未找到API密钥"
            if self.gui:
                self.gui.update_http_status(0, "余额查询")
            return False, None, error_msg
        
        # 更新统计
        self.query_count += 1
        self.last_query_time = time.time()
        
        if self.gui:
            self.gui.print_out("正在查询账户余额...")
        
        # 准备请求
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "DeepSeek-Client/1.0"
        }
        
        # 执行请求（支持重试）
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    DEEPSEEK_BALANCE_URL, 
                    headers=headers, 
                    timeout=self.timeout
                )
                
                # 更新HTTP状态
                if self.gui:
                    self.gui.update_http_status(response.status_code, "余额查询")
                
                if response.status_code == 200:
                    # 解析响应
                    balance_data = response.json()
                    balance_response = BalanceResponse.from_api_response(balance_data)
                    
                    # 更新缓存
                    self.last_balance_response = balance_response
                    
                    # 处理成功响应
                    self._handle_successful_response(balance_response)
                    
                    return True, balance_response, None
                
                else:
                    # 处理HTTP错误
                    self.error_count += 1
                    error_msg = f"HTTP {response.status_code}"
                    
                    # 尝试获取错误详情
                    error_details = None
                    try:
                        error_details = response.json()
                    except json.JSONDecodeError:
                        try:
                            error_details = response.text
                        except:
                            pass
                    
                    # 显示错误对话框
                    if self.gui and hasattr(self.gui, 'show_http_error_dialog'):
                        self.gui.show_http_error_dialog(response.status_code, "余额查询", error_details)
                    
                    return False, None, error_msg
                    
            except requests.exceptions.HTTPError as http_err:
                # HTTP错误
                self.error_count += 1
                status_code = http_err.response.status_code if http_err.response else 0
                
                if self.gui:
                    self.gui.update_http_status(status_code, "余额查询")
                
                if http_err.response:
                    try:
                        error_details = http_err.response.json()
                        if self.gui and hasattr(self.gui, 'show_http_error_dialog'):
                            self.gui.show_http_error_dialog(status_code, "余额查询", error_details)
                    except json.JSONDecodeError:
                        if self.gui and hasattr(self.gui, 'show_http_error_dialog'):
                            self.gui.show_http_error_dialog(status_code, "余额查询")
                
                return False, None, f"HTTP错误: {http_err}"
                
            except requests.exceptions.RequestException as req_err:
                # 网络错误或其他请求异常
                self.error_count += 1
                
                if self.gui:
                    self.gui.update_http_status(0, "余额查询")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < self.max_retries - 1:
                    if self.gui:
                        self.gui.print_out(f"请求失败，正在重试 ({attempt + 1}/{self.max_retries})...")
                    time.sleep(1 * (attempt + 1))  # 指数退避
                    continue
                
                return False, None, f"网络错误: {req_err}"
                
            except json.JSONDecodeError as json_err:
                # JSON解析错误
                self.error_count += 1
                
                if self.gui:
                    self.gui.update_http_status(0, "余额查询")
                
                return False, None, f"响应解析错误: {json_err}"
                
            except Exception as e:
                # 其他未知错误
                self.error_count += 1
                
                if self.gui:
                    self.gui.update_http_status(0, "余额查询")
                
                return False, None, f"未知错误: {e}"
        
        # 所有重试都失败
        return False, None, "查询失败：所有重试都失败"
    
    def _handle_successful_response(self, balance_response):
        """
        处理成功的余额查询响应
        
        Args:
            balance_response (BalanceResponse): 余额响应对象
        """
        if not self.gui:
            return
        
        # 检查服务可用性
        if balance_response.is_available:
            self.gui.print_out("服务可用: 是")
            
            if balance_response.has_balance_info():
                # 显示详细余额信息
                for idx, balance_info in enumerate(balance_response.balance_infos):
                    self.gui.print_out(f"余额信息 #{idx+1}:")
                    detailed_info = balance_info.format_detailed_display()
                    for line in detailed_info.split('\n'):
                        self.gui.print_out(f"  {line}")
                
                # 显示主要余额信息（加粗显示）
                primary_balance = balance_response.get_primary_balance()
                if primary_balance:
                    main_display = primary_balance.format_display()
                    self.gui.print_out(f"**总余额: {main_display}**")
                    
                    # 检查低余额警告
                    if primary_balance.is_low_balance(1.0):
                        self.gui.print_out("⚠️ **警告: 账户余额较低，建议及时充值！**")
            else:
                self.gui.print_out("未找到详细余额信息。")
        else:
            self.gui.print_out("服务可用: 否")
            if balance_response.message:
                self.gui.print_out(f"API消息: {balance_response.message}")
            else:
                self.gui.print_out("服务不可用 - 可能由于服务未开启或没有余额信息。")
    
    def get_cached_balance(self):
        """
        获取缓存的余额信息
        
        Returns:
            BalanceResponse: 缓存的余额响应，如果没有缓存返回None
        """
        if self.is_cache_valid():
            return self.last_balance_response
        return None
    
    def get_balance_summary(self):
        """
        获取余额摘要信息
        
        Returns:
            dict: 余额摘要字典
        """
        summary = {
            "query_count": self.query_count,
            "error_count": self.error_count,
            "success_rate": 0.0,
            "last_query_time": self.last_query_time,
            "has_cached_balance": self.last_balance_response is not None,
            "cache_valid": self.is_cache_valid(),
            "cached_balance": None
        }
        
        # 计算成功率
        if self.query_count > 0:
            success_count = self.query_count - self.error_count
            summary["success_rate"] = round((success_count / self.query_count) * 100, 2)
        
        # 添加缓存的余额信息
        if self.last_balance_response:
            summary["cached_balance"] = self.last_balance_response.to_dict()
        
        return summary
    
    def format_balance_for_display(self, balance_response=None):
        """
        格式化余额信息用于显示
        
        Args:
            balance_response (BalanceResponse): 余额响应，如果为None则使用缓存
            
        Returns:
            str: 格式化的余额显示字符串
        """
        if balance_response is None:
            balance_response = self.get_cached_balance()
        
        if not balance_response:
            return "无余额信息"
        
        if not balance_response.is_available:
            return f"服务不可用: {balance_response.message}"
        
        if not balance_response.has_balance_info():
            return "无详细余额信息"
        
        primary = balance_response.get_primary_balance()
        if primary:
            return primary.format_display()
        
        return "余额信息格式错误"
    
    def query_balance_async(self, callback=None, force_refresh=False):
        """
        异步查询余额
        
        Args:
            callback: 回调函数，接收 (success, balance_response, error_message) 参数
            force_refresh (bool): 是否强制刷新
        """
        def query_worker():
            success, response, error = self.query_balance(force_refresh=force_refresh)
            if callback:
                callback(success, response, error)
        
        thread = threading.Thread(target=query_worker, daemon=True)
        thread.start()
    
    def clear_cache(self):
        """清空缓存"""
        self.last_balance_response = None
    
    def reset_statistics(self):
        """重置统计信息"""
        self.query_count = 0
        self.error_count = 0
        self.last_query_time = None
    
    def validate_balance_threshold(self, threshold=1.0):
        """
        验证余额是否满足阈值要求
        
        Args:
            threshold (float): 余额阈值
            
        Returns:
            tuple: (is_sufficient, current_balance, message)
        """
        cached_balance = self.get_cached_balance()
        
        if not cached_balance:
            return False, 0.0, "无余额信息，请先查询余额"
        
        if not cached_balance.is_available:
            return False, 0.0, "余额服务不可用"
        
        primary = cached_balance.get_primary_balance()
        if not primary:
            return False, 0.0, "无有效余额信息"
        
        current_balance = primary.total_balance
        is_sufficient = current_balance >= threshold
        
        if is_sufficient:
            message = f"余额充足：{primary.format_display()}"
        else:
            message = f"余额不足：当前 {primary.format_display()}，需要至少 {threshold} {primary.currency}"
        
        return is_sufficient, current_balance, message
    
    def get_balance_history(self):
        """
        获取余额查询历史（简化版）
        
        Returns:
            dict: 历史信息
        """
        return {
            "total_queries": self.query_count,
            "total_errors": self.error_count,
            "last_query_time": self.last_query_time,
            "cache_info": {
                "has_cache": self.last_balance_response is not None,
                "cache_valid": self.is_cache_valid(),
                "cache_age_seconds": (
                    time.time() - self.last_balance_response.query_time 
                    if self.last_balance_response else None
                )
            }
        }
    
    def destroy(self):
        """销毁余额服务并清理资源"""
        self.clear_cache()
        self.gui = None
        self.client_manager = None

# 便捷函数
def create_balance_service(gui_instance=None, client_manager=None):
    """
    创建余额服务的便捷函数
    
    Args:
        gui_instance: GUI实例
        client_manager: 客户端管理器实例
        
    Returns:
        BalanceService: 余额服务实例
    """
    return BalanceService(gui_instance, client_manager)

def query_balance_simple(api_key, timeout=30):
    """
    简单的余额查询函数（不依赖服务类）
    
    Args:
        api_key (str): API密钥
        timeout (int): 请求超时时间
        
    Returns:
        tuple: (success, balance_data, error_message)
    """
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        
        response = requests.get(DEEPSEEK_BALANCE_URL, headers=headers, timeout=timeout)
        
        if response.status_code == 200:
            balance_data = response.json()
            return True, balance_data, None
        else:
            return False, None, f"HTTP {response.status_code}"
            
    except Exception as e:
        return False, None, str(e)

def format_balance_simple(balance_data):
    """
    简单的余额格式化函数
    
    Args:
        balance_data (dict): 余额数据
        
    Returns:
        str: 格式化的余额字符串
    """
    if not balance_data.get("is_available", False):
        return "服务不可用"
    
    balance_infos = balance_data.get("balance_infos", [])
    if not balance_infos:
        return "无余额信息"
    
    primary = balance_infos[0]
    total_balance = primary.get("total_balance", "N/A")
    currency = primary.get("currency", "USD")
    
    return f"{total_balance} {currency}"

# GUI集成函数
def integrate_balance_service_with_gui(gui_instance, client_manager=None):
    """
    将余额服务集成到GUI实例中
    
    Args:
        gui_instance: GUI实例
        client_manager: 客户端管理器实例
    """
    # 创建余额服务
    balance_service = create_balance_service(gui_instance, client_manager)
    
    # 将服务绑定到GUI
    gui_instance.balance_service = balance_service
    
    # 重写GUI的余额查询方法
    def new_query_balance():
        success, response, error = balance_service.query_balance()
        return success
    
    gui_instance.query_balance = new_query_balance
    
    # 添加余额服务相关方法到GUI
    gui_instance.get_balance_service = lambda: balance_service
    gui_instance.get_cached_balance = lambda: balance_service.get_cached_balance()
    gui_instance.get_balance_summary = lambda: balance_service.get_balance_summary()
    gui_instance.format_balance_for_display = lambda resp=None: balance_service.format_balance_for_display(resp)
    gui_instance.validate_balance_threshold = lambda threshold=1.0: balance_service.validate_balance_threshold(threshold)
    
    return balance_service

# CLI支持函数
def query_balance_cli(api_key):
    """
    CLI模式的余额查询便捷函数
    
    Args:
        api_key (str): API密钥
    """
    success, balance_data, error_msg = query_balance_simple(api_key)
    if success:
        print(format_balance_simple(balance_data))
    else:
        print(f"余额查询失败: {error_msg}")

# 错误处理装饰器
def handle_balance_errors(operation="余额查询"):
    """
    余额查询错误处理装饰器
    
    Args:
        operation (str): 操作描述
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                self.error_count += 1
                error_msg = str(e)
                
                if hasattr(self, 'gui') and self.gui:
                    status_code = self.extract_status_code_from_error(error_msg)
                    self.gui.update_http_status(status_code, operation)
                    self.gui.print_out(f"{operation}失败: {error_msg}")
                else:
                    print(f"{operation}失败: {error_msg}")
                    
                return False, None, error_msg
        return wrapper
    return decorator

# 余额监控类
class BalanceMonitor:
    """余额监控器，用于定期检查余额状态"""
    
    def __init__(self, balance_service, check_interval=3600, low_balance_threshold=1.0):
        """
        初始化余额监控器
        
        Args:
            balance_service (BalanceService): 余额服务实例
            check_interval (int): 检查间隔（秒）
            low_balance_threshold (float): 低余额阈值
        """
        self.balance_service = balance_service
        self.check_interval = check_interval
        self.low_balance_threshold = low_balance_threshold
        self.is_monitoring = False
        self.monitor_thread = None
        self.callbacks = []
    
    def add_callback(self, callback):
        """
        添加余额变化回调函数
        
        Args:
            callback: 回调函数，接收 (balance_response, is_low_balance) 参数
        """
        self.callbacks.append(callback)
    
    def start_monitoring(self):
        """开始监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                success, response, error = self.balance_service.query_balance(force_refresh=True)
                
                if success and response:
                    primary = response.get_primary_balance()
                    is_low = primary.is_low_balance(self.low_balance_threshold) if primary else False
                    
                    # 调用回调函数
                    for callback in self.callbacks:
                        try:
                            callback(response, is_low)
                        except Exception:
                            pass  # 忽略回调错误
                
                # 等待下次检查
                for _ in range(self.check_interval):
                    if not self.is_monitoring:
                        break
                    time.sleep(1)
                    
            except Exception:
                # 忽略监控错误，继续下次检查
                time.sleep(60)  # 出错时等待1分钟

# 测试和示例代码
if __name__ == "__main__":
    # 创建余额服务进行测试
    print("余额服务测试")
    print("=" * 30)
    
    service = create_balance_service()
    
    # 测试余额信息类
    test_balance_info = BalanceInfo("USD", 10.50, 5.00, 5.50)
    print(f"余额信息: {test_balance_info.format_display()}")
    print(f"详细信息:\n{test_balance_info.format_detailed_display()}")
    print(f"是否低余额: {test_balance_info.is_low_balance(1.0)}")
    
    # 测试余额摘要
    summary = service.get_balance_summary()
    print(f"服务摘要: {summary}")
    
    # 测试缓存状态
    print(f"缓存有效: {service.is_cache_valid()}")
    print(f"余额历史: {service.get_balance_history()}")
    
    print("余额服务测试完成")