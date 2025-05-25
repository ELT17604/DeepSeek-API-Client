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

import tkinter as tk
import threading
import time
import socket
from config import (
    STATUS_COLORS, STATUS_TYPES, NETWORK_STATUS_CONFIG, 
    NETWORK_CHECK_HOST, NETWORK_CHECK_PORT, WINDOW_CONFIG
)

class StatusIndicator(tk.Frame):
    """状态指示器控件，每行显示状态文本和一个彩色指示灯"""
    
    def __init__(self, master, label_text, **kwargs):
        """
        初始化状态指示器
        
        Args:
            master: 父控件
            label_text (str): 状态标签文本
            **kwargs: 传递给Frame的其他参数
        """
        super().__init__(master, **kwargs)
        self.label_text = label_text
        self.status_var = tk.StringVar(value=f"{label_text}: 未初始化")
        
        # 状态文本标签 - 增加宽度以容纳延迟信息
        self.label = tk.Label(
            self, 
            textvariable=self.status_var, 
            anchor="w", 
            width=28, 
            font=("Arial", 9)
        )
        self.label.pack(side=tk.LEFT, padx=(2, 5))
        
        # 彩色指示灯
        self.canvas = tk.Canvas(
            self, 
            width=16, 
            height=16, 
            highlightthickness=0, 
            bg="white"
        )
        self.canvas.pack(side=tk.LEFT, padx=2)
        self.indicator = self.canvas.create_oval(
            2, 2, 14, 14, 
            fill="gray", 
            outline="darkgray", 
            width=1
        )

    def set_status(self, text, color):
        """
        设置状态文本和指示灯颜色
        
        Args:
            text (str): 状态文本
            color (str): 指示灯颜色
        """
        self.status_var.set(f"{self.label_text}: {text}")
        
        # 确保颜色映射正确
        indicator_color = STATUS_COLORS.get(color.lower(), color)
        self.canvas.itemconfig(self.indicator, fill=indicator_color)
    
    def get_status_text(self):
        """
        获取当前状态文本
        
        Returns:
            str: 当前状态文本
        """
        return self.status_var.get()
    
    def get_label_text(self):
        """
        获取标签文本
        
        Returns:
            str: 标签文本
        """
        return self.label_text
    
    def set_font(self, font_spec):
        """
        设置状态文本字体
        
        Args:
            font_spec: 字体规格 (family, size, style)
        """
        self.label.config(font=font_spec)

class StatusMonitorWindow:
    """独立的状态监控窗口"""
    
    def __init__(self, master, status_manager):
        """
        初始化状态监控窗口
        
        Args:
            master: 主窗口
            status_manager: 状态管理器实例
        """
        self.master = master
        self.status_manager = status_manager
        self.window = None
        self.indicators = {}
        self.is_visible = False
        
    def create_window(self):
        """创建独立的状态监控窗口"""
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()  # 如果窗口已存在，提升到前台
            return
            
        self.window = tk.Toplevel(self.master)
        config = WINDOW_CONFIG["status_window"]
        self.window.title(config["title"])
        self.window.geometry(config["geometry"])
        
        if not config["resizable"]:
            self.window.resizable(False, False)
        
        if config.get("topmost", False):
            self.window.attributes("-topmost", True)
        
        # 隐藏窗口的关闭按钮和标题栏（可选）
        # self.window.overrideredirect(True)
        
        # 设置窗口位置（在主窗口右侧）
        self._position_window()
        
        # 添加标题栏（如果使用overrideredirect）
        # self._create_title_bar()
        
        # 内容区域
        content_frame = tk.Frame(self.window, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 创建状态指示器
        self._create_status_indicators(content_frame)
        
        # 更新所有状态显示
        self._update_all_indicators()
        
        # 绑定窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        self.is_visible = True
    
    def _position_window(self):
        """设置窗口位置"""
        try:
            # 获取主窗口位置和大小
            self.master.update_idletasks()  # 确保几何信息是最新的
            main_x = self.master.winfo_x()
            main_y = self.master.winfo_y()
            main_width = self.master.winfo_width()
            
            # 计算状态窗口位置
            status_x = main_x + main_width + 10
            status_y = main_y
            
            self.window.geometry(f"320x160+{status_x}+{status_y}")
        except Exception as e:
            print(f"设置状态窗口位置时出错: {e}")
            # 使用默认位置
            self.window.geometry("320x160+100+100")
    
    def _create_title_bar(self):
        """创建自定义标题栏（当使用overrideredirect时）"""
        title_frame = tk.Frame(self.window, bg="darkgray", height=25)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="状态监控", 
            bg="darkgray", 
            fg="white", 
            font=("Arial", 9, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=5, pady=3)
        
        # 添加关闭按钮
        close_btn = tk.Button(
            title_frame,
            text="×",
            bg="darkgray",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            width=2,
            command=self.hide_window
        )
        close_btn.pack(side=tk.RIGHT, padx=2, pady=2)
    
    def _create_status_indicators(self, parent):
        """创建状态指示器"""
        # 按照特定顺序创建指示器
        status_order = ["client", "network", "model", "http", "chat"]
        
        for status_type in status_order:
            if status_type in STATUS_TYPES:
                label_text = STATUS_TYPES[status_type]
                indicator = StatusIndicator(parent, label_text)
                indicator.pack(fill=tk.X, padx=5, pady=2)
                self.indicators[status_type] = indicator
    
    def _update_all_indicators(self):
        """更新所有状态指示器"""
        for status_type, indicator in self.indicators.items():
            status_data = self.status_manager.get_status(status_type)
            if status_data:
                indicator.set_status(status_data["text"], status_data["color"])
    
    def update_indicator(self, status_type, text, color):
        """
        更新特定的状态指示器
        
        Args:
            status_type (str): 状态类型
            text (str): 状态文本
            color (str): 状态颜色
        """
        if (self.window and self.window.winfo_exists() and 
            status_type in self.indicators):
            self.indicators[status_type].set_status(text, color)
    
    def show_window(self):
        """显示状态监控窗口"""
        if self.window is None or not self.window.winfo_exists():
            self.create_window()
        else:
            self.window.deiconify()
            self.window.lift()
        self.is_visible = True
    
    def hide_window(self):
        """隐藏状态监控窗口"""
        if self.window and self.window.winfo_exists():
            self.window.withdraw()
        self.is_visible = False
    
    def destroy_window(self):
        """销毁状态监控窗口"""
        if self.window and self.window.winfo_exists():
            self.window.destroy()
        self.window = None
        self.indicators = {}
        self.is_visible = False
    
    def toggle_window(self):
        """切换窗口显示/隐藏状态"""
        if self.is_visible:
            self.hide_window()
        else:
            self.show_window()
    
    def is_window_visible(self):
        """
        检查窗口是否可见
        
        Returns:
            bool: 窗口是否可见
        """
        return (self.window is not None and 
                self.window.winfo_exists() and 
                self.is_visible)

class StatusManager:
    """状态管理器 - 管理所有状态数据和通知"""
    
    def __init__(self):
        """初始化状态管理器"""
        # 状态数据存储
        self.status_data = {
            "client": {"text": "无API密钥", "color": "red"},
            "network": {"text": "检查中...", "color": "gray"},
            "model": {"text": "未选择", "color": "red"},
            "http": {"text": "正常", "color": "green"},
            "chat": {"text": "未就绪", "color": "red"}
        }
        
        # 状态变化回调函数列表
        self.status_callbacks = []
        
        # 网络监控相关
        self.network_monitor = None
        
    def register_callback(self, callback):
        """
        注册状态变化回调函数
        
        Args:
            callback: 回调函数，接收 (status_type, text, color) 参数
        """
        if callback not in self.status_callbacks:
            self.status_callbacks.append(callback)
    
    def unregister_callback(self, callback):
        """
        注销状态变化回调函数
        
        Args:
            callback: 要注销的回调函数
        """
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
    
    def update_status(self, status_type, text, color):
        """
        更新状态并通知所有监听器
        
        Args:
            status_type (str): 状态类型
            text (str): 状态文本
            color (str): 状态颜色
        """
        # 更新状态数据
        self.status_data[status_type] = {"text": text, "color": color}
        
        # 通知所有回调函数
        for callback in self.status_callbacks:
            try:
                callback(status_type, text, color)
            except Exception as e:
                print(f"状态回调函数执行失败: {e}")
    
    def get_status(self, status_type):
        """
        获取特定类型的状态数据
        
        Args:
            status_type (str): 状态类型
            
        Returns:
            dict: 状态数据字典，包含 text 和 color 键
        """
        return self.status_data.get(status_type, {"text": "未知", "color": "gray"})
    
    def get_all_status(self):
        """
        获取所有状态数据
        
        Returns:
            dict: 所有状态数据
        """
        return self.status_data.copy()
    
    def start_network_monitor(self, master_widget=None):
        """
        启动网络状态监控
        
        Args:
            master_widget: 主控件，用于线程安全的UI更新
        """
        if self.network_monitor is None:
            self.network_monitor = NetworkMonitor(self, master_widget)
            self.network_monitor.start()
    
    def stop_network_monitor(self):
        """停止网络状态监控"""
        if self.network_monitor:
            self.network_monitor.stop()
            self.network_monitor = None

class NetworkMonitor:
    """网络状态监控器"""
    
    def __init__(self, status_manager, master_widget=None):
        """
        初始化网络监控器
        
        Args:
            status_manager: 状态管理器实例
            master_widget: 主控件，用于线程安全的UI更新
        """
        self.status_manager = status_manager
        self.master_widget = master_widget
        self.monitoring_thread = None
        self.stop_flag = False
        
    def start(self):
        """启动网络监控"""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.stop_flag = False
            self.monitoring_thread = threading.Thread(
                target=self._monitor_loop, 
                daemon=True
            )
            self.monitoring_thread.start()
    
    def stop(self):
        """停止网络监控"""
        self.stop_flag = True
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=1)
    
    def _monitor_loop(self):
        """网络监控循环"""
        while not self.stop_flag:
            try:
                # 测量网络延迟
                start_time = time.time()
                socket.create_connection(
                    (NETWORK_CHECK_HOST, NETWORK_CHECK_PORT), 
                    timeout=NETWORK_STATUS_CONFIG["timeout"]
                )
                end_time = time.time()
                
                # 计算延迟（毫秒）
                latency_ms = round((end_time - start_time) * 1000, 1)
                
                # 根据延迟确定状态颜色
                thresholds = NETWORK_STATUS_CONFIG["latency_thresholds"]
                if latency_ms < thresholds["good"]:
                    color = "green"
                elif latency_ms < thresholds["warning"]:
                    color = "yellow"
                else:
                    color = "red"
                
                status_text = f"已连接 ({latency_ms}ms)"
                
                # 线程安全的状态更新
                self._safe_update_status("network", status_text, color)
                
            except socket.timeout:
                self._safe_update_status("network", "超时", "red")
            except Exception as e:
                print(f"网络监控错误: {e}")
                self._safe_update_status("network", "已断开", "red")
            
            # 等待指定间隔后再次检查
            for _ in range(NETWORK_STATUS_CONFIG["check_interval"]):
                if self.stop_flag:
                    break
                time.sleep(1)
    
    def _safe_update_status(self, status_type, text, color):
        """
        线程安全的状态更新
        
        Args:
            status_type (str): 状态类型
            text (str): 状态文本
            color (str): 状态颜色
        """
        if self.master_widget:
            # 使用主线程更新UI
            try:
                self.master_widget.after(
                    0, 
                    lambda: self.status_manager.update_status(status_type, text, color)
                )
            except Exception:
                # 如果主控件不可用，直接更新状态
                self.status_manager.update_status(status_type, text, color)
        else:
            # 直接更新状态
            self.status_manager.update_status(status_type, text, color)

class MainIndicators:
    """主界面状态指示灯管理器"""
    
    def __init__(self, parent_frame, status_manager):
        """
        初始化主界面指示灯
        
        Args:
            parent_frame: 父框架
            status_manager: 状态管理器实例
        """
        self.parent_frame = parent_frame
        self.status_manager = status_manager
        
        # 创建指示灯画布
        self._create_indicators()
        
        # 注册状态变化回调
        self.status_manager.register_callback(self._on_status_changed)
        
    def _create_indicators(self):
        """创建主界面指示灯"""
        # 右侧指示灯 - 跟随chat状态
        self.chat_indicator_canvas = tk.Canvas(
            self.parent_frame, 
            width=16, 
            height=16, 
            highlightthickness=0, 
            bg="white"
        )
        self.chat_indicator_canvas.pack(side=tk.RIGHT, padx=2)
        self.chat_indicator = self.chat_indicator_canvas.create_oval(
            2, 2, 14, 14, 
            fill="red", 
            outline="darkgray", 
            width=1
        )

        # 左侧指示灯 - 综合状态
        self.overall_indicator_canvas = tk.Canvas(
            self.parent_frame, 
            width=16, 
            height=16, 
            highlightthickness=0, 
            bg="white"
        )
        self.overall_indicator_canvas.pack(side=tk.RIGHT, padx=2)
        self.overall_indicator = self.overall_indicator_canvas.create_oval(
            2, 2, 14, 14, 
            fill="red", 
            outline="darkgray", 
            width=1
        )
    
    def _on_status_changed(self, status_type, text, color):
        """
        状态变化回调处理
        
        Args:
            status_type (str): 状态类型
            text (str): 状态文本
            color (str): 状态颜色
        """
        self._update_indicators()
    
    def _update_indicators(self):
        """更新主界面上的状态指示灯"""
        # 右侧指示灯 - 跟随chat状态
        chat_status = self.status_manager.get_status("chat")
        chat_color = STATUS_COLORS.get(chat_status["color"].lower(), chat_status["color"])
        self.chat_indicator_canvas.itemconfig(self.chat_indicator, fill=chat_color)
        
        # 左侧指示灯 - 综合状态逻辑
        all_status = self.status_manager.get_all_status()
        
        client_color = all_status.get("client", {}).get("color", "red")
        network_color = all_status.get("network", {}).get("color", "red")
        model_color = all_status.get("model", {}).get("color", "red")
        http_color = all_status.get("http", {}).get("color", "red")
        
        # 检查除chat外的四个指示灯是否均为绿色
        all_green = all(color == "green" for color in [client_color, network_color, model_color, http_color])
        
        # 检查除chat外的四个指示灯中，除了网络外的三个是否均为绿色
        three_green_without_network = all(color == "green" for color in [client_color, model_color, http_color])
        
        # 检查除chat和model外的三个指示灯是否均为绿色
        three_green_without_model = all(color == "green" for color in [client_color, network_color, http_color])
        
        if all_green:
            overall_color = STATUS_COLORS["green"]  # 绿色 - 所有状态都是绿色
        elif three_green_without_network and network_color == "yellow":
            overall_color = STATUS_COLORS["yellow"]  # 黄色 - 网络是黄色，其他都是绿色
        elif three_green_without_model:
            overall_color = STATUS_COLORS["yellow"]  # 黄色 - model不是绿色，其他都是绿色
        else:
            overall_color = STATUS_COLORS["red"]  # 红色 - 其他情况
            
        self.overall_indicator_canvas.itemconfig(self.overall_indicator, fill=overall_color)
    
    def destroy(self):
        """销毁指示灯并清理资源"""
        # 注销回调
        self.status_manager.unregister_callback(self._on_status_changed)
        
        # 销毁控件
        if hasattr(self, 'chat_indicator_canvas'):
            self.chat_indicator_canvas.destroy()
        if hasattr(self, 'overall_indicator_canvas'):
            self.overall_indicator_canvas.destroy()

class StatusMonitorController:
    """状态监控控制器 - 统一管理所有状态相关组件"""
    
    def __init__(self, master):
        """
        初始化状态监控控制器
        
        Args:
            master: 主窗口
        """
        self.master = master
        
        # 创建状态管理器
        self.status_manager = StatusManager()
        
        # 创建状态监控窗口
        self.monitor_window = StatusMonitorWindow(master, self.status_manager)
        
        # 主界面指示灯（需要在创建控制按钮时初始化）
        self.main_indicators = None
        
        # 启动网络监控
        self.status_manager.start_network_monitor(master)
    
    def create_main_indicators(self, parent_frame):
        """
        创建主界面指示灯
        
        Args:
            parent_frame: 父框架
            
        Returns:
            MainIndicators: 主界面指示灯实例
        """
        if self.main_indicators is None:
            self.main_indicators = MainIndicators(parent_frame, self.status_manager)
        return self.main_indicators
    
    def create_toggle_button(self, parent_frame):
        """
        创建状态监控切换按钮
        
        Args:
            parent_frame: 父框架
            
        Returns:
            tk.Button: 切换按钮
        """
        button = tk.Button(
            parent_frame, 
            text="状态监控", 
            command=self._toggle_status_window
        )
        return button
    
    def _toggle_status_window(self):
        """切换状态监控窗口显示/隐藏"""
        self.monitor_window.toggle_window()
    
    def update_client_status(self, api_key_available=False, client_initialized=False):
        """
        更新客户端状态
        
        Args:
            api_key_available (bool): API密钥是否可用
            client_initialized (bool): 客户端是否已初始化
        """
        if client_initialized:
            self.status_manager.update_status("client", "已初始化", "green")
        elif api_key_available:
            self.status_manager.update_status("client", "已输入API密钥", "yellow")
        else:
            self.status_manager.update_status("client", "无API密钥", "red")
    
    def update_model_status(self, models_available=False, model_selected=None, fetch_failed=False):
        """
        更新模型状态
        
        Args:
            models_available (bool): 模型是否可用
            model_selected (str): 选中的模型名称
            fetch_failed (bool): 获取模型是否失败
        """
        if fetch_failed:
            self.status_manager.update_status("model", "获取失败", "red")
        elif model_selected:
            self.status_manager.update_status("model", f"已选择: {model_selected}", "green")
        elif models_available:
            self.status_manager.update_status("model", "可用 (未选择)", "yellow")
        else:
            self.status_manager.update_status("model", "未选择", "red")
    
    def update_http_status(self, status_code=None, operation=None):
        """
        更新HTTP状态
        
        Args:
            status_code (int): HTTP状态码
            operation (str): 操作描述
        """
        if status_code is None:
            self.status_manager.update_status("http", "OK", "green")
            return
            
        operation_text = f" ({operation})" if operation else ""
        
        status_messages = {
            200: ("正常", "green"),
            400: ("格式错误", "red"),
            401: ("认证失败", "red"),
            402: ("余额不足", "red"),
            403: ("访问被禁", "red"),
            404: ("未找到", "red"),
            422: ("参数错误", "red"),
            429: ("请求限制", "red"),
            500: ("服务器错误", "yellow"),
            502: ("网关错误", "yellow"),
            503: ("服务器繁忙", "yellow"),
            0: ("网络错误", "red")
        }
        
        if status_code in status_messages:
            text, color = status_messages[status_code]
            self.status_manager.update_status("http", f"{text} ({status_code}){operation_text}", color)
        elif 400 <= status_code <= 499:
            self.status_manager.update_status("http", f"客户端错误 ({status_code}){operation_text}", "red")
        elif 500 <= status_code <= 599:
            self.status_manager.update_status("http", f"服务器错误 ({status_code}){operation_text}", "yellow")
        else:
            self.status_manager.update_status("http", f"状态 {status_code}{operation_text}", "yellow")
    
    def update_chat_status(self, status):
        """
        更新聊天状态
        
        Args:
            status (str): 聊天状态 (not_ready, ready, chatting, streaming)
        """
        status_map = {
            "not_ready": ("未就绪", "red"),
            "ready": ("就绪", "green"),
            "chatting": ("聊天中", "yellow"),
            "streaming": ("流式输出中", "yellow")
        }
        text, color = status_map.get(status, ("未知", "gray"))
        self.status_manager.update_status("chat", text, color)
    
    def get_status_data(self, status_type):
        """
        获取状态数据
        
        Args:
            status_type (str): 状态类型
            
        Returns:
            dict: 状态数据
        """
        return self.status_manager.get_status(status_type)
    
    def is_monitor_window_visible(self):
        """
        检查监控窗口是否可见
        
        Returns:
            bool: 窗口是否可见
        """
        return self.monitor_window.is_window_visible()
    
    def destroy(self):
        """销毁状态监控控制器并清理资源"""
        # 停止网络监控
        self.status_manager.stop_network_monitor()
        
        # 销毁主界面指示灯
        if self.main_indicators:
            self.main_indicators.destroy()
        
        # 销毁监控窗口
        self.monitor_window.destroy_window()

# 便捷函数
def create_status_controller(master):
    """
    创建状态监控控制器的便捷函数
    
    Args:
        master: 主窗口
        
    Returns:
        StatusMonitorController: 状态监控控制器实例
    """
    return StatusMonitorController(master)

def create_status_indicator(parent, label_text, **kwargs):
    """
    创建状态指示器的便捷函数
    
    Args:
        parent: 父控件
        label_text (str): 标签文本
        **kwargs: 传递给StatusIndicator的其他参数
        
    Returns:
        StatusIndicator: 状态指示器实例
    """
    return StatusIndicator(parent, label_text, **kwargs)

# 测试和示例代码
if __name__ == "__main__":
    # 创建测试窗口
    root = tk.Tk()
    root.title("Status Monitor Test")
    root.geometry("400x300")
    
    # 创建状态监控控制器
    controller = create_status_controller(root)
    
    # 创建控制按钮框架
    button_frame = tk.Frame(root)
    button_frame.pack(fill=tk.X, padx=10, pady=10)
    
    # 创建主界面指示灯
    indicators_frame = tk.Frame(button_frame)
    indicators_frame.pack(side=tk.RIGHT)
    controller.create_main_indicators(indicators_frame)
    
    # 创建切换按钮
    toggle_btn = controller.create_toggle_button(button_frame)
    toggle_btn.pack(side=tk.LEFT)
    
    # 创建测试按钮
    def test_status_updates():
        """测试状态更新"""
        import random
        statuses = ["red", "yellow", "green"]
        
        controller.update_client_status(True, True)
        controller.update_model_status(True, "test-model")
        controller.update_http_status(200, "测试")
        controller.update_chat_status("ready")
    
    test_btn = tk.Button(button_frame, text="测试状态", command=test_status_updates)
    test_btn.pack(side=tk.LEFT, padx=5)
    
    # 显示状态监控窗口
    controller.monitor_window.show_window()
    
    # 测试状态更新
    test_status_updates()
    
    # 设置窗口关闭事件
    def on_closing():
        controller.destroy()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()