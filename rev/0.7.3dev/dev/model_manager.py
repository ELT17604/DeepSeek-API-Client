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

# 确保导入正确
import re
import json
import time
from config import MODEL_FILTER_CONFIG, HTTP_CONFIG

class ModelManager:
    """DeepSeek 模型管理器"""
    
    def __init__(self, gui_instance=None, client_manager=None):
        """
        初始化模型管理器
        
        Args:
            gui_instance: GUI实例，用于状态更新和用户交互
            client_manager: 客户端管理器实例
        """
        self.gui = gui_instance
        self.client_manager = client_manager
        self.available_models = []
        self.selected_model = None
        self.models_cache = {}  # 模型缓存
        self.last_fetch_time = None
        
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
    
    def filter_models(self, models_list):
        """
        过滤模型列表
        
        Args:
            models_list (list): 原始模型列表
            
        Returns:
            list: 过滤后的模型列表
        """
        if not models_list:
            return []
        
        config = MODEL_FILTER_CONFIG
        
        # 如果模型数量少于阈值，显示所有模型
        if len(models_list) < config["show_all_threshold"]:
            return models_list
        
        # 过滤包含优先关键词的模型
        priority_keywords = config["priority_keywords"]
        filtered_models = []
        
        for model in models_list:
            model_lower = model.lower()
            # 检查是否包含优先关键词
            if any(keyword in model_lower for keyword in priority_keywords):
                filtered_models.append(model)
        
        # 如果过滤后没有模型，返回原列表
        if not filtered_models:
            filtered_models = models_list
        
        # 应用排除模式（如果配置了的话）
        exclude_patterns = config.get("exclude_patterns", [])
        if exclude_patterns:
            final_models = []
            for model in filtered_models:
                excluded = False
                for pattern in exclude_patterns:
                    if re.search(pattern, model, re.IGNORECASE):
                        excluded = True
                        break
                if not excluded:
                    final_models.append(model)
            return final_models
        
        return filtered_models
    
    def fetch_models(self, force_refresh=False):
        """
        获取可用模型列表
        
        Args:
            force_refresh (bool): 是否强制刷新，忽略缓存
            
        Returns:
            tuple: (success, models_list, error_message)
        """
        # 检查客户端是否可用
        client = None
        if self.client_manager:
            client = self.client_manager.get_client()
        elif self.gui and hasattr(self.gui, 'client'):
            client = self.gui.client
        
        if not client:
            error_msg = "客户端未初始化"
            if self.gui:
                self.gui.update_http_status(0, "模型获取")
                self.gui.update_model_status("fetch_fail")
            return False, [], error_msg
        
        # 检查缓存（如果不强制刷新）
        if not force_refresh and self.available_models:
            return True, self.available_models, None
        
        try:
            if self.gui:
                self.gui.print_out("正在获取可用模型...")
            
            # 调用API获取模型列表
            models_response = client.models.list()
            
            # 更新HTTP状态为成功
            if self.gui:
                self.gui.update_http_status(200, "模型获取")
            
            # 提取模型ID列表
            raw_models = [model.id for model in models_response.data]
            
            # 过滤模型
            filtered_models = self.filter_models(raw_models)
            
            if not filtered_models:
                error_msg = "未找到可用模型"
                if self.gui:
                    self.gui.print_out("未找到模型。请检查您的API密钥。")
                    self.gui.update_model_status("fetch_fail")
                return False, [], error_msg
            
            # 更新缓存
            self.available_models = filtered_models
            self.models_cache = {
                'models': filtered_models,
                'raw_count': len(raw_models),
                'filtered_count': len(filtered_models)
            }
            
            import time
            self.last_fetch_time = time.time()
            
            # 更新GUI状态
            if self.gui:
                self._update_gui_after_fetch(filtered_models)
            
            return True, filtered_models, None
            
        except Exception as e:
            error_msg = str(e)
            status_code = self.extract_status_code_from_error(error_msg)
            
            if self.gui:
                self.gui.update_http_status(status_code, "模型获取")
                self._handle_fetch_error(status_code, error_msg)
                self.gui.update_model_status("fetch_fail")
            
            return False, [], error_msg
    
    def _update_gui_after_fetch(self, models_list):
        """获取模型成功后更新GUI"""
        if not self.gui:
            return
        
        # 更新模型下拉框
        self.gui.set_model_list(models_list)
        
        # 检查当前选择的模型是否还在新列表中
        current_selected = self.gui.get_selected_model()
        if current_selected and current_selected not in models_list:
            self.selected_model = None
            self.gui.set_selected_model(None)
        
        # 更新模型状态
        self.gui.update_model_status()
        
        # 显示获取结果
        raw_count = self.models_cache.get('raw_count', len(models_list))
        filtered_count = len(models_list)
        
        if raw_count != filtered_count:
            self.gui.print_out(f"找到 {raw_count} 个模型，过滤后显示 {filtered_count} 个。请选择一个以继续。")
        else:
            self.gui.print_out(f"找到 {filtered_count} 个模型。请选择一个以继续。")
        
        # 更新按钮状态
        self.gui.update_buttons_state()
    
    def _handle_fetch_error(self, status_code, error_msg):
        """处理获取模型时的错误"""
        if not self.gui:
            return
        
        if status_code in [400, 401, 402, 403, 404, 422, 429, 500, 502, 503]:
            self.gui.show_http_error_dialog(status_code, "模型获取")
        elif status_code == 0:
            if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                self.gui.print_out(f"网络错误 (模型获取): {error_msg}")
            else:
                self.gui.print_out(f"未知错误 (模型获取): {error_msg}")
        else:
            self.gui.print_out(f"获取模型时发生错误: {error_msg}")
        
        self.gui.print_out(f"获取模型失败: {error_msg}")
    
    def select_model(self, model_name):
        """
        选择模型
        
        Args:
            model_name (str): 模型名称
            
        Returns:
            bool: 选择是否成功
        """
        if not model_name or model_name == "请选择一个模型...":
            self.selected_model = None
            if self.gui:
                self.gui.set_selected_model(None)
                self.gui.update_model_status()
                self.gui.update_buttons_state()
            return False
        
        if model_name not in self.available_models:
            if self.gui:
                self.gui.show_error_message("错误", f"模型 '{model_name}' 不在可用列表中")
            return False
        
        self.selected_model = model_name
        
        if self.gui:
            self.gui.set_selected_model(model_name)
            self.gui.update_model_status()
            self.gui.update_buttons_state()
            self.gui.print_out(f"已选择模型: {model_name}")
            
            # 同步到GUI的selected_model变量
            self.gui.selected_model = model_name
        
        return True
    
    def get_selected_model(self):
        """
        获取当前选择的模型
        
        Returns:
            str: 当前选择的模型名称，如果未选择返回None
        """
        return self.selected_model
    
    def get_available_models(self):
        """
        获取可用模型列表
        
        Returns:
            list: 可用模型列表
        """
        return self.available_models.copy()
    
    def is_model_available(self, model_name):
        """
        检查模型是否可用
        
        Args:
            model_name (str): 模型名称
            
        Returns:
            bool: 模型是否可用
        """
        return model_name in self.available_models
    
    def get_model_info(self, model_name=None):
        """
        获取模型信息
        
        Args:
            model_name (str): 模型名称，如果为None则返回当前选择的模型信息
            
        Returns:
            dict: 模型信息字典
        """
        target_model = model_name or self.selected_model
        
        info = {
            "name": target_model,
            "is_available": target_model in self.available_models if target_model else False,
            "is_selected": target_model == self.selected_model,
            "total_available": len(self.available_models),
            "last_fetch_time": self.last_fetch_time
        }
        
        # 添加缓存信息
        if self.models_cache:
            info.update({
                "raw_model_count": self.models_cache.get('raw_count', 0),
                "filtered_model_count": self.models_cache.get('filtered_count', 0)
            })
        
        return info
    
    def refresh_models(self):
        """
        刷新模型列表（强制重新获取）
        
        Returns:
            bool: 刷新是否成功
        """
        success, models, error = self.fetch_models(force_refresh=True)
        return success
    
    def validate_model_selection(self):
        """
        验证当前模型选择的有效性
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.selected_model:
            return False, "未选择模型"
        
        if not self.available_models:
            return False, "模型列表为空，请先获取模型列表"
        
        if self.selected_model not in self.available_models:
            return False, f"选择的模型 '{self.selected_model}' 不在可用列表中"
        
        return True, None
    
    def search_models(self, keyword):
        """
        搜索模型
        
        Args:
            keyword (str): 搜索关键词
            
        Returns:
            list: 匹配的模型列表
        """
        if not keyword:
            return self.available_models.copy()
        
        keyword_lower = keyword.lower()
        matching_models = []
        
        for model in self.available_models:
            if keyword_lower in model.lower():
                matching_models.append(model)
        
        return matching_models
    
    def get_model_categories(self):
        """
        获取模型分类
        
        Returns:
            dict: 模型分类字典
        """
        categories = {
            "chat": [],
            "coder": [],
            "other": []
        }
        
        for model in self.available_models:
            model_lower = model.lower()
            if "chat" in model_lower:
                categories["chat"].append(model)
            elif "coder" in model_lower or "code" in model_lower:
                categories["coder"].append(model)
            else:
                categories["other"].append(model)
        
        return categories
    
    def reset_model_selection(self):
        """重置模型选择"""
        self.selected_model = None
        if self.gui:
            self.gui.set_selected_model(None)
            self.gui.update_model_status()
            self.gui.update_buttons_state()
    
    def clear_models_cache(self):
        """清空模型缓存"""
        self.available_models = []
        self.models_cache = {}
        self.last_fetch_time = None
        self.selected_model = None
        
        if self.gui:
            self.gui.set_model_list([])
            self.gui.set_selected_model(None)
            self.gui.update_model_status()
            self.gui.update_buttons_state()
    
    def get_cache_info(self):
        """
        获取缓存信息
        
        Returns:
            dict: 缓存信息字典
        """
        import time
        current_time = time.time()
        
        return {
            "has_cache": bool(self.available_models),
            "model_count": len(self.available_models),
            "last_fetch_time": self.last_fetch_time,
            "cache_age_seconds": current_time - self.last_fetch_time if self.last_fetch_time else None,
            "cache_data": self.models_cache.copy()
        }
    
    def export_models_list(self, format_type="json"):
        """
        导出模型列表
        
        Args:
            format_type (str): 导出格式 ("json", "text", "csv")
            
        Returns:
            str: 导出的字符串内容
        """
        if format_type == "json":
            export_data = {
                "models": self.available_models,
                "selected_model": self.selected_model,
                "cache_info": self.models_cache,
                "export_time": time.time() if 'time' in globals() else None
            }
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        
        elif format_type == "text":
            lines = ["DeepSeek 可用模型列表", "=" * 30]
            for i, model in enumerate(self.available_models, 1):
                marker = " (已选择)" if model == self.selected_model else ""
                lines.append(f"{i:2d}. {model}{marker}")
            return "\n".join(lines)
        
        elif format_type == "csv":
            lines = ["序号,模型名称,是否选择"]
            for i, model in enumerate(self.available_models, 1):
                is_selected = "是" if model == self.selected_model else "否"
                lines.append(f"{i},{model},{is_selected}")
            return "\n".join(lines)
        
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")
    
    def destroy(self):
        """销毁模型管理器并清理资源"""
        self.clear_models_cache()
        self.gui = None
        self.client_manager = None

# 便捷函数
def create_model_manager(gui_instance=None, client_manager=None):
    """
    创建模型管理器
    
    Args:
        gui_instance: GUI实例
        client_manager: 客户端管理器实例
        
    Returns:
        ModelManager: 模型管理器实例
    """
    manager = ModelManager(gui_instance, client_manager)
    
    # 如果有GUI实例，集成相关方法
    if gui_instance:
        # 备份原始方法（如果存在）
        original_refresh = getattr(gui_instance, 'refresh_models', None)
        original_select = getattr(gui_instance, 'on_model_selected', None)
        
        # 重写刷新方法
        def enhanced_refresh_models():
            try:
                success = manager.refresh_models()
                return success
            except Exception as e:
                gui_instance.print_out(f"刷新模型失败: {e}")
                return False
        
        # 重写选择方法
        def enhanced_on_model_selected(event=None):
            try:
                selected = gui_instance.get_selected_model()
                if selected:
                    success = manager.select_model(selected)
                    return success
                return False
            except Exception as e:
                gui_instance.print_out(f"选择模型失败: {e}")
                return False
        
        # 绑定增强的方法
        gui_instance.refresh_models_enhanced = enhanced_refresh_models
        gui_instance.on_model_selected_enhanced = enhanced_on_model_selected
    
    return manager

def filter_model_list(models_list, keywords=None):
    """
    过滤模型列表的独立函数
    
    Args:
        models_list (list): 模型列表
        keywords (list): 过滤关键词，如果为None则使用配置文件的设置
        
    Returns:
        list: 过滤后的模型列表
    """
    if not models_list:
        return []
    
    if keywords is None:
        keywords = MODEL_FILTER_CONFIG["priority_keywords"]
    
    if len(models_list) < MODEL_FILTER_CONFIG["show_all_threshold"]:
        return models_list
    
    filtered = []
    for model in models_list:
        model_lower = model.lower()
        if any(keyword in model_lower for keyword in keywords):
            filtered.append(model)
    
    return filtered if filtered else models_list

def search_models_by_keyword(models_list, keyword):
    """
    根据关键词搜索模型的独立函数
    
    Args:
        models_list (list): 模型列表
        keyword (str): 搜索关键词
        
    Returns:
        list: 匹配的模型列表
    """
    if not keyword:
        return models_list
    
    keyword_lower = keyword.lower()
    return [model for model in models_list if keyword_lower in model.lower()]

# GUI集成函数
def integrate_model_manager_with_gui(gui_instance, client_manager=None):
    """
    将模型管理器集成到GUI实例中
    
    Args:
        gui_instance: GUI实例
        client_manager: 客户端管理器实例
    """
    # 创建模型管理器
    model_manager = create_model_manager(gui_instance, client_manager)
    
    # 将管理器绑定到GUI
    gui_instance.model_manager = model_manager
    
    # 重写GUI的相关方法
    def new_refresh_models():
        return model_manager.refresh_models()
    
    def new_on_model_selected(event=None):
        selected = gui_instance.model_var.get()
        return model_manager.select_model(selected)
    
    gui_instance.refresh_models = new_refresh_models
    gui_instance.on_model_selected = new_on_model_selected
    
    # 添加模型管理相关方法到GUI
    gui_instance.get_model_manager = lambda: model_manager
    gui_instance.search_models = lambda keyword: model_manager.search_models(keyword)
    gui_instance.get_model_categories = lambda: model_manager.get_model_categories()
    gui_instance.export_models_list = lambda fmt="json": model_manager.export_models_list(fmt)
    gui_instance.get_model_info = lambda model=None: model_manager.get_model_info(model)
    
    return model_manager

# CLI支持函数
def select_model_from_list_cli(models_list):
    """
    命令行界面中选择模型的函数
    
    Args:
        models_list (list): 可用模型列表
        
    Returns:
        str: 选择的模型名称，如果取消返回None
    """
    if not models_list:
        print("没有可用的模型。")
        return None
    
    print(f"找到 {len(models_list)} 个模型:")
    for i, model in enumerate(models_list, 1):
        print(f"  {i:2d}. {model}")
    
    while True:
        try:
            choice = input(f"选择一个模型 (1-{len(models_list)}): ").strip()
            if not choice:
                return None
            
            model_index = int(choice) - 1
            if 0 <= model_index < len(models_list):
                selected_model = models_list[model_index]
                print(f"已选择模型: {selected_model}")
                return selected_model
            else:
                print("无效选择，请重试。")
        except ValueError:
            print("请输入有效数字。")
        except KeyboardInterrupt:
            print("\n取消选择。")
            return None

def fetch_models_cli(client):
    """
    命令行界面中获取模型的函数
    
    Args:
        client: OpenAI客户端实例
        
    Returns:
        list: 模型列表，如果失败返回空列表
    """
    try:
        print("正在获取可用模型...")
        models_response = client.models.list()
        
        # 提取模型ID列表
        raw_models = [model.id for model in models_response.data]
        
        # 过滤模型
        filtered_models = filter_model_list(raw_models)
        
        if not filtered_models:
            print("未找到可用模型。")
            return []
        
        return filtered_models
        
    except Exception as e:
        print(f"获取模型失败: {e}")
        return []

# 错误处理装饰器
def handle_model_errors(operation="模型操作"):
    """
    模型管理错误处理装饰器
    
    Args:
        operation (str): 操作描述
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                error_msg = str(e)
                if hasattr(self, 'gui') and self.gui:
                    status_code = self.extract_status_code_from_error(error_msg)
                    self.gui.update_http_status(status_code, operation)
                    self.gui.print_out(f"{operation}失败: {error_msg}")
                    self.gui.update_model_status("fetch_fail")
                else:
                    print(f"{operation}失败: {error_msg}")
                return False
        return wrapper
    return decorator

# 测试和示例代码
if __name__ == "__main__":
    # 创建模型管理器进行测试
    print("模型管理器测试")
    print("=" * 30)
    
    manager = create_model_manager()
    
    # 测试模型过滤
    test_models = [
        "deepseek-chat",
        "deepseek-coder",
        "deepseek-math",
        "gpt-4",
        "claude-3",
        "deepseek-reasoner"
    ]
    
    filtered = filter_model_list(test_models)
    print(f"原始模型: {test_models}")
    print(f"过滤后模型: {filtered}")
    
    # 测试搜索功能
    search_result = search_models_by_keyword(test_models, "deepseek")
    print(f"搜索'deepseek': {search_result}")
    
    # 测试模型信息
    manager.available_models = test_models
    manager.select_model("deepseek-chat")
    info = manager.get_model_info()
    print(f"模型信息: {info}")
    
    # 测试导出功能
    exported_json = manager.export_models_list("json")
    print(f"导出JSON: {exported_json}")