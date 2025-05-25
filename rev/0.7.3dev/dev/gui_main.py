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
from tkinter import messagebox, scrolledtext, ttk, font
import threading
import datetime
import json
import time
import socket

try:
    from config import APP_INFO, WINDOW_CONFIG, FONT_CONFIG, APP_COPYRIGHT
except ImportError:
    # 如果配置模块不可用，使用默认值
    APP_INFO = {
        'name': 'DeepSeek API Client',
        'version': '0.7.3',
        'build_date': '2025-01-25'
    }
    WINDOW_CONFIG = {'main_window': {'title': 'DeepSeek API Client', 'geometry': '800x600'}}
    FONT_CONFIG = {'default_family': 'TkDefaultFont', 'default_size': 11}
    APP_COPYRIGHT = '© 2025 1f84@ELT Group'

try:
    from crypto_utils import load_api_key_from_file, save_api_key_to_file, delete_api_key_file
except ImportError:
    # 如果加密模块不可用，提供基本实现
    def load_api_key_from_file():
        return None
    def save_api_key_to_file(key):
        return False
    def delete_api_key_file():
        return True

try:
    from markdown_widget import MarkdownText
except ImportError:
    # 如果Markdown控件不可用，使用普通文本控件
    class MarkdownText(scrolledtext.ScrolledText):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        
        def append_and_render(self, text, end="\n", markdown_enabled=True):
            self.insert(tk.END, text + end)
            self.see(tk.END)
        
        def clear_all(self):
            self.delete(1.0, tk.END)

class StatusIndicator(tk.Frame):
    """状态指示器控件"""
    def __init__(self, master, label_text, **kwargs):
        super().__init__(master, **kwargs)
        self.label_text = label_text
        self.status_var = tk.StringVar(value=f"{label_text}: 未初始化")
        
        # 状态文本标签
        self.label = tk.Label(self, textvariable=self.status_var, anchor="w", width=28, font=("Arial", 9))
        self.label.pack(side=tk.LEFT, padx=(2, 5))
        
        # 彩色指示灯
        self.canvas = tk.Canvas(self, width=16, height=16, highlightthickness=0, bg="white")
        self.canvas.pack(side=tk.LEFT, padx=2)
        self.indicator = self.canvas.create_oval(2, 2, 14, 14, fill="gray", outline="darkgray", width=1)

    def set_status(self, text, color):
        """设置状态文本和指示灯颜色"""
        self.status_var.set(f"{self.label_text}: {text}")
        color_map = {
            "red": "#ff4444",
            "green": "#44ff44", 
            "yellow": "#ffcc00",
            "gray": "#888888",
            "grey": "#888888"
        }
        indicator_color = color_map.get(color.lower(), color)
        self.canvas.itemconfig(self.indicator, fill=indicator_color)

class DeepSeekGUI:
    def __init__(self, master):
        self.master = master
        self._setup_window()
        self._initialize_variables()
        self._create_widgets()
        self._initialize_status_system()
        self._load_saved_data()
        self._finalize_initialization()

    def _setup_window(self):
        """设置主窗口属性"""
        try:
            config = WINDOW_CONFIG["main_window"]
            self.master.title(config["title"])
            self.master.geometry(config.get("geometry", "800x600"))
            if "min_size" in config:
                self.master.minsize(*config["min_size"])
        except Exception:
            self.master.title("DeepSeek API Client")
            self.master.geometry("800x600")
            self.master.minsize(600, 400)

    def _initialize_variables(self):
        """初始化变量"""
        # 核心功能变量
        self.api_key = ""
        self.client = None
        self.selected_model = None
        self.messages = []
        self.available_models = []
        
        # UI控制变量
        self.markdown_enabled = True
        self.streaming_stopped = False
        
        # 字体相关变量
        try:
            self.output_font_size = FONT_CONFIG["default_size"]
            self.output_font_family = FONT_CONFIG["default_family"]
        except:
            self.output_font_size = 11
            self.output_font_family = "TkDefaultFont"
        
        self.output_font = (self.output_font_family, self.output_font_size)
        
        # Tkinter变量
        self.model_var = tk.StringVar(value="请选择一个模型...")
        self.font_size_var = tk.IntVar(value=self.output_font_size)

    def _create_widgets(self):
        """创建所有UI组件"""
        # 从下往上创建
        self._create_footer_section()
        self._create_api_management_section()
        self._create_font_control_section()
        
        # 从上往下创建
        self._create_api_key_section()
        self._create_model_selection_section()
        self._create_control_buttons_section()
        self._create_output_section()
        self._create_input_section()
        self._create_input_control_section()

    def _create_api_key_section(self):
        """创建API Key输入区域"""
        self.api_frame = tk.Frame(self.master)
        self.api_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.api_label = tk.Label(self.api_frame, text="API密钥:", font=("Arial", 10))
        self.api_label.pack(side=tk.LEFT)

        self.api_key_entry = tk.Entry(self.api_frame, show="*", font=("Arial", 10))
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.api_key_entry.bind('<KeyRelease>', self._on_api_key_change)
        self.api_key_entry.bind('<FocusOut>', self._on_api_key_change)

        self.init_btn = tk.Button(self.api_frame, text="初始化", command=self.initialize_client)
        self.init_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # 掩码标签（初始时隐藏）
        self.api_key_masked_label = tk.Label(self.api_frame, text="", font=("Arial", 10))

    def _create_model_selection_section(self):
        """创建模型选择区域"""
        self.model_frame = tk.Frame(self.master)
        self.model_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

        self.model_label = tk.Label(self.model_frame, text="模型:", font=("Arial", 10))
        self.model_label.pack(side=tk.LEFT)

        self.model_combobox = ttk.Combobox(
            self.model_frame, 
            textvariable=self.model_var, 
            state="readonly",
            font=("Arial", 10), 
            width=30
        )
        self.model_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        self.model_combobox.bind("<<ComboboxSelected>>", self.on_model_selected)

        self.refresh_models_btn = tk.Button(
            self.model_frame, 
            text="刷新模型", 
            command=self.refresh_models, 
            state=tk.DISABLED
        )
        self.refresh_models_btn.pack(side=tk.RIGHT)

    def _create_control_buttons_section(self):
        """创建控制按钮区域"""
        self.control_frame = tk.Frame(self.master)
        self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

        self.balance_btn = tk.Button(
            self.control_frame, 
            text="查询余额", 
            command=self.query_balance, 
            state=tk.DISABLED
        )
        self.balance_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.chat_btn = tk.Button(
            self.control_frame, 
            text="开始聊天", 
            command=self.start_chat, 
            state=tk.DISABLED
        )
        self.chat_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.clear_btn = tk.Button(
            self.control_frame, 
            text="清空输出", 
            command=self.clear_output
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.markdown_btn = tk.Button(
            self.control_frame, 
            text="Markdown: 开", 
            command=self.toggle_markdown_rendering
        )
        self.markdown_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 右侧状态监控按钮
        self.status_btn = tk.Button(
            self.control_frame, 
            text="状态监控", 
            command=self.toggle_status_window
        )
        self.status_btn.pack(side=tk.RIGHT)

        # 状态指示灯框架
        self.status_indicators_frame = tk.Frame(self.control_frame)
        self.status_indicators_frame.pack(side=tk.RIGHT, padx=(0, 5))

        # 右侧指示灯 - 聊天状态
        self.chat_indicator_canvas = tk.Canvas(
            self.status_indicators_frame, 
            width=16, height=16, 
            highlightthickness=0, bg="white"
        )
        self.chat_indicator_canvas.pack(side=tk.RIGHT, padx=2)
        self.chat_indicator = self.chat_indicator_canvas.create_oval(
            2, 2, 14, 14, fill="red", outline="darkgray", width=1
        )

        # 左侧指示灯 - 综合状态
        self.overall_indicator_canvas = tk.Canvas(
            self.status_indicators_frame, 
            width=16, height=16, 
            highlightthickness=0, bg="white"
        )
        self.overall_indicator_canvas.pack(side=tk.RIGHT, padx=2)
        self.overall_indicator = self.overall_indicator_canvas.create_oval(
            2, 2, 14, 14, fill="red", outline="darkgray", width=1
        )

    def _create_output_section(self):
        """创建输出区域"""
        try:
            self.output = MarkdownText(
                self.master, 
                width=80, 
                height=20, 
                state='normal',
                font=self.output_font
            )
        except Exception:
            # 如果MarkdownText失败，使用普通Text控件
            self.output = scrolledtext.ScrolledText(
                self.master, 
                width=80, 
                height=20, 
                state='normal',
                wrap=tk.WORD,
                font=self.output_font
            )
        
        self.output.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

    def _create_input_section(self):
        """创建用户输入区域"""
        self.input_frame = tk.Frame(self.master)
        self.input_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 2))

        self.input_label = tk.Label(self.input_frame, text="您:", font=("Arial", 10))
        self.input_label.pack(side=tk.LEFT, anchor="s", pady=2)

        self.user_input = tk.Text(
            self.input_frame, 
            height=3, 
            wrap="word", 
            state=tk.DISABLED
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        self.user_input.bind("<KeyRelease>", self.on_input_change)
        self.user_input.bind("<Return>", self.send_user_input)
        self.user_input.bind("<Control-Return>", lambda e: self.user_input.insert(tk.INSERT, "\n"))

    def _create_input_control_section(self):
        """创建输入控制区域"""
        self.input_btn_frame = tk.Frame(self.master)
        self.input_btn_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 4))

        self.btn_spacer = tk.Label(self.input_btn_frame)
        self.btn_spacer.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.send_btn = tk.Button(
            self.input_btn_frame, 
            text="发送", 
            command=self.send_user_input, 
            state=tk.DISABLED
        )
        self.send_btn.pack(side=tk.RIGHT, padx=(5, 0))

        self.stop_btn = tk.Button(
            self.input_btn_frame, 
            text="停止", 
            command=self.stop_streaming, 
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.RIGHT, padx=(5, 0))

        self.new_btn = tk.Button(
            self.input_btn_frame, 
            text="新会话", 
            command=self.start_new_session, 
            state=tk.DISABLED
        )
        self.new_btn.pack(side=tk.RIGHT, padx=(5, 0))

        self.end_btn = tk.Button(
            self.input_btn_frame, 
            text="结束聊天", 
            command=self.end_chat, 
            state=tk.NORMAL
        )
        self.end_btn.pack(side=tk.RIGHT, padx=(8, 0))

    def _create_font_control_section(self):
        """创建字体大小调节控件"""
        self.font_frame = tk.Frame(self.master)
        self.font_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 2))

        self.font_label = tk.Label(self.font_frame, text="输出栏字体大小:", font=("Arial", 9))
        self.font_label.pack(side=tk.LEFT)

        self.font_minus_btn = tk.Button(
            self.font_frame, 
            text="－", 
            width=2, 
            command=self.decrease_font_size
        )
        self.font_minus_btn.pack(side=tk.LEFT, padx=(2, 0))

        self.font_size_entry = tk.Entry(
            self.font_frame, 
            width=3, 
            textvariable=self.font_size_var, 
            justify="center"
        )
        self.font_size_entry.pack(side=tk.LEFT, padx=(2, 0))
        self.font_size_entry.bind("<Return>", self.set_font_size_from_entry)

        self.font_plus_btn = tk.Button(
            self.font_frame, 
            text="＋", 
            width=2, 
            command=self.increase_font_size
        )
        self.font_plus_btn.pack(side=tk.LEFT, padx=(2, 0))

    def _create_api_management_section(self):
        """创建API Key管理控件"""
        self.api_manage_frame = tk.Frame(self.master)
        self.api_manage_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 2))

        self.clear_apikey_btn = tk.Button(
            self.api_manage_frame, 
            text="清除API密钥", 
            command=self.clear_api_key, 
            state=tk.DISABLED
        )
        self.clear_apikey_btn.pack(side=tk.LEFT)

    def _create_footer_section(self):
        """创建底部版权信息"""
        try:
            copyright_text = APP_COPYRIGHT
        except:
            copyright_text = "© 2025 1f84@ELT Group"

        self.footer_label = tk.Label(
            self.master,
            text=f"DeepSeek API Client GUI {APP_INFO.get('version', '0.7.3')} {copyright_text}",
            font=("Arial", 8),
            fg="gray"
        )
        self.footer_label.pack(side=tk.BOTTOM, pady=(0, 3))

    def _initialize_status_system(self):
        """初始化状态监控系统"""
        try:
            # 尝试使用专用的状态监控控制器
            try:
                from status_monitor import create_status_controller
                self.status_controller = create_status_controller(self.master)
                
                # 集成状态控制器到主界面
                self._integrate_status_controller()
                print("使用高级状态监控系统")
                
            except ImportError:
                # 回退到基本状态系统
                self._initialize_basic_status_system()
                print("使用基本状态监控系统")
                
        except Exception as e:
            print(f"初始化状态系统失败: {e}")
            # 创建最基本的状态数据结构
            self._initialize_minimal_status_system()

    def _integrate_status_controller(self):
        """集成状态监控控制器"""
        try:
            # 在控制按钮区域添加主界面指示灯
            if hasattr(self, 'status_indicators_frame'):
                self.status_controller.create_main_indicators(self.status_indicators_frame)
            
            # 更新状态按钮功能
            if hasattr(self, 'status_btn'):
                self.status_btn.config(command=self._toggle_status_window_advanced)
            
            # 重写状态更新方法
            self.update_status_display = self._update_status_advanced
            self.update_client_status = self._update_client_status_advanced
            self.update_model_status = self._update_model_status_advanced
            self.update_chat_status = self._update_chat_status_advanced
            self.update_http_status = self._update_http_status_advanced
            
        except Exception as e:
            print(f"集成状态控制器失败: {e}")
            self._initialize_basic_status_system()

    def _initialize_basic_status_system(self):
        """初始化基本状态监控系统"""
        # 独立状态监控窗口相关
        self.status_window = None
        self.status_indicators = {}

        # 初始化状态监控数据
        self.status_data = {
            "client": {"text": "无API密钥", "color": "red"},
            "network": {"text": "检查中...", "color": "gray"},
            "model": {"text": "未选择", "color": "red"},
            "http": {"text": "正常", "color": "green"},
            "chat": {"text": "未就绪", "color": "red"}
        }

        # 启动网络状态定时刷新线程
        self.network_thread_stop = False
        self.network_thread = threading.Thread(target=self.network_status_loop, daemon=True)
        self.network_thread.start()

    def _initialize_minimal_status_system(self):
        """初始化最小状态系统（确保基本功能可用）"""
        self.status_window = None
        self.status_indicators = {}
        self.status_data = {
            "client": {"text": "未知", "color": "gray"},
            "network": {"text": "未知", "color": "gray"},
            "model": {"text": "未知", "color": "gray"},
            "http": {"text": "未知", "color": "gray"},
            "chat": {"text": "未知", "color": "gray"}
        }
        self.network_thread_stop = True  # 禁用网络监控以避免错误

    # 高级状态更新方法（使用status_controller）
    def _update_status_advanced(self, status_type, text, color):
        """使用状态控制器更新状态"""
        try:
            if hasattr(self, 'status_controller'):
                # 使用对应的更新方法
                if status_type == "client":
                    api_key_available = "API密钥" in text or "已初始化" in text
                    client_initialized = "已初始化" in text
                    self.status_controller.update_client_status(api_key_available, client_initialized)
                elif status_type == "model":
                    models_available = "可用" in text or "已选择" in text
                    model_selected = text if "已选择" in text else None
                    fetch_failed = "获取失败" in text
                    self.status_controller.update_model_status(models_available, model_selected, fetch_failed)
                elif status_type == "chat":
                    status_map = {
                        "未就绪": "not_ready",
                        "就绪": "ready", 
                        "聊天中": "chatting",
                        "流式输出中": "streaming"
                    }
                    status_key = status_map.get(text, "not_ready")
                    self.status_controller.update_chat_status(status_key)
                elif status_type == "http":
                    # 从文本中提取状态码
                    import re
                    match = re.search(r'\((\d+)\)', text)
                    status_code = int(match.group(1)) if match else None
                    operation = text.split('(')[0].strip() if '(' in text else None
                    self.status_controller.update_http_status(status_code, operation)
        except Exception as e:
            print(f"高级状态更新失败，回退到基本方法: {e}")
            self._update_status_basic(status_type, text, color)

    def _update_status_basic(self, status_type, text, color):
        """基本状态更新方法"""
        self.status_data[status_type] = {"text": text, "color": color}
        
        # 如果状态窗口存在，更新显示
        if (self.status_window is not None and 
            self.status_window.winfo_exists() and 
            status_type in self.status_indicators):
            self.status_indicators[status_type].set_status(text, color)
        
        # 更新主界面的指示灯
        if hasattr(self, 'update_main_indicators'):
            self.update_main_indicators()

    def _update_client_status_advanced(self):
        """使用状态控制器更新客户端状态"""
        try:
            if hasattr(self, 'status_controller'):
                if self.client and self.api_key:
                    self.status_controller.update_client_status(True, True)
                elif hasattr(self, 'api_key_entry') and self.api_key_entry.winfo_exists():
                    api_key_entered = bool(self.api_key_entry.get().strip())
                    self.status_controller.update_client_status(api_key_entered, False)
                else:
                    self.status_controller.update_client_status(False, False)
        except Exception as e:
            print(f"高级客户端状态更新失败: {e}")
            self._update_client_status_basic()

    def _update_client_status_basic(self):
        """基本客户端状态更新"""
        if self.client and self.api_key:
            self.update_status_display("client", "已初始化", "green")
        elif hasattr(self, 'api_key_entry') and self.api_key_entry.winfo_exists():
            api_key_entered = bool(self.api_key_entry.get().strip())
            if api_key_entered:
                self.update_status_display("client", "已输入API密钥", "yellow")
            else:
                self.update_status_display("client", "无API密钥", "red")
        else:
            self.update_status_display("client", "无API密钥", "red")

    def _update_model_status_advanced(self, status=None):
        """使用状态控制器更新模型状态"""
        try:
            if hasattr(self, 'status_controller'):
                if not self.client:
                    self.status_controller.update_model_status(False, None, False)
                elif status == "fetch_fail":
                    self.status_controller.update_model_status(False, None, True)
                elif self.selected_model:
                    self.status_controller.update_model_status(True, self.selected_model, False)
                elif self.available_models:
                    self.status_controller.update_model_status(True, None, False)
                else:
                    self.status_controller.update_model_status(False, None, False)
        except Exception as e:
            print(f"高级模型状态更新失败: {e}")
            self._update_model_status_basic(status)

    def _update_model_status_basic(self, status=None):
        """基本模型状态更新"""
        if not self.client:
            self.update_status_display("model", "不可用", "red")
        elif status == "fetch_fail":
            self.update_status_display("model", "获取失败", "red")
        elif self.selected_model:
            self.update_status_display("model", f"已选择: {self.selected_model}", "green")
        elif self.available_models:
            self.update_status_display("model", "可用 (未选择)", "yellow")
        else:
            self.update_status_display("model", "未选择", "red")

    def _update_chat_status_advanced(self, status):
        """使用状态控制器更新聊天状态"""
        try:
            if hasattr(self, 'status_controller'):
                self.status_controller.update_chat_status(status)
        except Exception as e:
            print(f"高级聊天状态更新失败: {e}")
            self._update_chat_status_basic(status)

    def _update_chat_status_basic(self, status):
        """基本聊天状态更新"""
        status_map = {
            "not_ready": ("未就绪", "red"),
            "ready": ("就绪", "green"),
            "chatting": ("聊天中", "yellow"),
            "streaming": ("流式输出中", "yellow")
        }
        text, color = status_map.get(status, ("未知", "gray"))
        self.update_status_display("chat", text, color)

    def _update_http_status_advanced(self, status_code=None, operation=None):
        """使用状态控制器更新HTTP状态"""
        try:
            if hasattr(self, 'status_controller'):
                self.status_controller.update_http_status(status_code, operation)
        except Exception as e:
            print(f"高级HTTP状态更新失败: {e}")
            self._update_http_status_basic(status_code, operation)

    def _update_http_status_basic(self, status_code=None, operation=None):
        """基本HTTP状态更新"""
        if status_code is None:
            self.update_status_display("http", "OK", "green")
        elif status_code == 200:
            self.update_status_display("http", "正常 (200)", "green")
        else:
            self.update_status_display("http", f"错误 ({status_code})", "red")

    def _toggle_status_window_advanced(self):
        """使用状态控制器切换状态窗口"""
        try:
            if hasattr(self, 'status_controller'):
                if self.status_controller.is_monitor_window_visible():
                    self.status_btn.config(text="状态监控")
                else:
                    self.status_btn.config(text="隐藏状态")
                self.status_controller._toggle_status_window()
        except Exception as e:
            print(f"高级状态窗口切换失败: {e}")
            self.toggle_status_window()

    # 确保原有方法存在（向后兼容）
    def update_status_display(self, status_type, text, color):
        """更新状态显示（默认使用基本方法）"""
        self._update_status_basic(status_type, text, color)

    def update_client_status(self):
        """更新客户端状态（默认使用基本方法）"""
        self._update_client_status_basic()

    def update_model_status(self, status=None):
        """更新模型状态（默认使用基本方法）"""
        self._update_model_status_basic(status)

    def update_chat_status(self, status):
        """更新聊天状态（默认使用基本方法）"""
        self._update_chat_status_basic(status)

    def update_http_status(self, status_code=None, operation=None):
        """更新HTTP状态（默认使用基本方法）"""
        self._update_http_status_basic(status_code, operation)

    def _load_saved_data(self):
        """加载保存的数据"""
        try:
            # 尝试加载保存的API密钥
            from crypto_utils import load_api_key_from_file
            saved_key = load_api_key_from_file()
            if saved_key:
                self.api_key = saved_key
                self.api_key_entry.delete(0, tk.END)
                self.api_key_entry.insert(0, saved_key)
                # 更新客户端状态
                if hasattr(self, 'update_client_status'):
                    self.update_client_status()
                self.print_out("已加载保存的API密钥")
        except Exception as e:
            # 如果加载失败，不影响程序运行
            print(f"加载保存数据时出错: {e}")
    
    def _finalize_initialization(self):
        """完成初始化"""
        try:
            # 更新初始状态
            if hasattr(self, 'update_client_status'):
                self.update_client_status()
            if hasattr(self, 'update_model_status'):
                self.update_model_status()
            if hasattr(self, 'update_chat_status'):
                self.update_chat_status("not_ready")
            if hasattr(self, 'update_buttons_state'):
                self.update_buttons_state()
                
            # 设置输入框变化监听
            if hasattr(self, 'api_key_entry'):
                self.api_key_entry.bind('<KeyRelease>', self._on_api_key_change)
                
            # 显示欢迎信息
            try:
                welcome_msg = f"欢迎使用 {APP_INFO.get('name', 'DeepSeek API Client')} {APP_INFO.get('version', '0.7.3')}"
                self.print_out(welcome_msg)
            except:
                self.print_out("欢迎使用 DeepSeek API Client")
                
        except Exception as e:
            print(f"完成初始化时出错: {e}")

    def _on_api_key_change(self, event=None):
        """API密钥输入框变化事件"""
        try:
            # 更新客户端状态
            if hasattr(self, 'update_client_status'):
                self.update_client_status()
        except Exception as e:
            print(f"API密钥变化事件处理失败: {e}")

    def initialize_client(self):
        """初始化客户端"""
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请输入API密钥")
            return

        try:
            from openai import OpenAI
            from config import DEEPSEEK_API_BASE_URL_V1
            
            # 更新状态为初始化中
            self.update_status_display("client", "初始化中...", "yellow")
            
            # 创建客户端
            test_client = OpenAI(api_key=api_key, base_url=DEEPSEEK_API_BASE_URL_V1)
            
            # 测试客户端连接
            self.print_out("正在测试客户端连接...")
            models_response = test_client.models.list()
            
            # 初始化成功
            self.client = test_client
            self.api_key = api_key
            
            # 保存API Key
            if save_api_key_to_file(api_key):
                self.print_out("API Key已安全加密并保存到本地文件。")
            
            # 掩码显示API密钥
            self.mask_api_key_display(api_key)
            
            # 启用相关功能
            self.refresh_models_btn.config(state=tk.NORMAL)
            self.clear_apikey_btn.config(state=tk.NORMAL)
            
            # 更新状态
            self.update_client_status()
            self.print_out("客户端初始化成功!")
            self.update_buttons_state()
            
            # 自动刷新模型列表
            self.refresh_models()
            
        except Exception as e:
            error_msg = str(e)
            self.update_status_display("client", "初始化失败", "red")
            messagebox.showerror("错误", f"客户端初始化失败: {error_msg}")
            self.print_out(f"客户端初始化失败: {error_msg}")

    def mask_api_key_display(self, api_key):
        """显示掩码后的API密钥"""
        try:
            # 隐藏输入框
            self.api_key_entry.pack_forget()
            
            # 显示掩码标签
            masked_key = self.mask_api_key(api_key)
            self.api_key_masked_label.config(text=masked_key, anchor="w")
            self.api_key_masked_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
            
            # 将初始化按钮改为修改按钮
            self.init_btn.config(text="修改", command=self.change_api_key)
            
        except Exception as e:
            print(f"显示掩码API密钥时出错: {e}")

    def mask_api_key(self, api_key):
        """掩码API Key，前后各保留2位明文"""
        if not api_key:
            return ""
        if len(api_key) <= 4:
            return "*" * len(api_key)
        return api_key[:2] + "*" * (len(api_key) - 4) + api_key[-2:]

    def change_api_key(self):
        """修改API Key"""
        # 隐藏掩码标签
        self.api_key_masked_label.pack_forget()
        
        # 显示输入框
        self.api_key_entry.delete(0, tk.END)
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 将修改按钮改回初始化按钮
        self.init_btn.config(text="初始化", command=self.initialize_client)
        
        # 重置状态
        self.client = None
        self.api_key = ""
        self.selected_model = None
        self.model_var.set("请选择一个模型...")
        self.model_combobox['values'] = ()
        self.available_models = []
        
        # 禁用相关功能
        self.refresh_models_btn.config(state=tk.DISABLED)
        self.clear_apikey_btn.config(state=tk.DISABLED)
        
        # 禁用输入框
        self.user_input.config(state=tk.DISABLED)
        self.user_input.delete("1.0", tk.END)
        
        # 更新状态
        self.update_client_status()
        self.update_model_status()
        self.update_chat_status("not_ready")
        self.update_buttons_state()

    def refresh_models(self):
        """刷新模型列表"""
        if not self.client:
            messagebox.showerror("错误", "请先初始化客户端")
            return
            
        try:
            self.print_out("正在获取可用模型...")
            models_response = self.client.models.list()
            
            # 过滤模型
            from model_manager import filter_model_list
            raw_models = [model.id for model in models_response.data]
            available_models = filter_model_list(raw_models)
            
            self.available_models = available_models
            self.model_combobox['values'] = available_models
            
            # 如果当前选择的模型不在新列表中，则重置
            if self.selected_model and self.selected_model not in available_models:
                self.selected_model = None
                self.model_var.set("请选择一个模型...")
            
            # 更新模型状态
            self.update_model_status()
            
            self.print_out(f"找到 {len(available_models)} 个模型。请选择一个以继续。")
            self.update_buttons_state()
            
        except Exception as e:
            self.print_out(f"获取模型失败: {str(e)}")
            self.update_model_status("fetch_fail")

    def on_model_selected(self, event=None):
        """模型选择事件处理"""
        selected = self.model_var.get()
        if selected and selected != "请选择一个模型...":
            self.selected_model = selected
            self.update_model_status()
            self.update_buttons_state()
            self.print_out(f"已选择模型: {selected}")

    def start_chat(self):
        """开始聊天"""
        if not self.client:
            messagebox.showerror("错误", "请先初始化客户端")
            return
        if not self.selected_model:
            messagebox.showerror("错误", "请先选择一个模型")
            return

        self.messages = []
        self.user_input.config(state=tk.NORMAL)
        self.user_input.focus_set()
        self.update_chat_status("ready")
        self.update_buttons_state()
        self.print_out(f"开始与模型 {self.selected_model} 聊天")
        self.print_out("输入您的消息并按发送或回车键开始对话。")

    def query_balance(self):
        """查询余额"""
        if not self.client or not self.api_key:
            messagebox.showerror("错误", "请先初始化客户端")
            return
            
        try:
            from balance_service import query_balance_simple, format_balance_simple
            
            self.print_out("正在查询账户余额...")
            success, balance_data, error_msg = query_balance_simple(self.api_key)
            
            if success:
                formatted_balance = format_balance_simple(balance_data)
                self.print_out(f"账户余额: {formatted_balance}")
            else:
                self.print_out(f"余额查询失败: {error_msg}")
                
        except Exception as e:
            self.print_out(f"查询余额时发生错误: {str(e)}")

    def send_user_input(self, event=None):
        """发送用户输入"""
        if event and event.keysym == "Return" and not (event.state & 0x4):
            if event.state & 0x1:  # Shift+Enter，插入换行
                return "break"
        
        user_message = self.user_input.get("1.0", tk.END).strip()
        if not user_message:
            return "break"
            
        if not self.client or not self.selected_model:
            messagebox.showerror("错误", "请先初始化客户端并选择模型")
            return "break"
            
        # 清空输入框
        self.user_input.delete("1.0", tk.END)
        
        # 添加用户消息到对话历史
        self.messages.append({"role": "user", "content": user_message})
        
        # 显示用户输入
        self.print_out(f"您: {user_message}")
        
        # 开始流式对话
        self.start_streaming_chat()
        
        return "break"

    def start_streaming_chat(self):
        """开始流式聊天"""
        self.streaming_stopped = False
        self.update_chat_status("streaming")
        
        # 禁用发送按钮，启用停止按钮
        self.send_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # 在新线程中进行API调用
        thread = threading.Thread(target=self._streaming_chat_worker, daemon=True)
        thread.start()

    def _streaming_chat_worker(self):
        """流式聊天工作线程"""
        try:
            response = self.client.chat.completions.create(
                model=self.selected_model,
                messages=self.messages,
                stream=True,
                max_tokens=4096,
                temperature=0.7
            )
            
            assistant_message = ""
            self.master.after(0, lambda: self.print_out("助手: ", end=""))
            
            for chunk in response:
                if self.streaming_stopped:
                    break
                    
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    assistant_message += content
                    self.master.after(0, lambda c=content: self._append_streaming_content(c))
            
            if not self.streaming_stopped:
                # 添加助手回复到对话历史
                self.messages.append({"role": "assistant", "content": assistant_message})
                self.master.after(0, lambda: self.print_out("", end="\n"))
                
        except Exception as e:
            self.master.after(0, lambda: self.print_out(f"聊天发生错误: {str(e)}"))
            
        finally:
            self.master.after(0, self._restore_chat_buttons)

    def _append_streaming_content(self, content):
        """在主线程中追加流式内容"""
        if hasattr(self.output, 'append_and_render'):
            # 使用MarkdownText的方法
            self.output.insert(tk.END, content)
            self.output.see(tk.END)
        else:
            # 使用普通Text控件
            self.output.insert(tk.END, content)
            self.output.see(tk.END)

    def _restore_chat_buttons(self):
        """恢复聊天按钮状态"""
        self.send_btn.config(state=tk.NORMAL if self.user_input.get("1.0", tk.END).strip() else tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_chat_status("ready")

    def stop_streaming(self):
        """停止流式输出"""
        self.streaming_stopped = True
        self.print_out("用户停止了流式输出。")

    def start_new_session(self):
        """开始新会话"""
        self.messages = []
        self.print_out("开始新聊天会话。")
        if self.selected_model:
            self.print_out(f"当前模型: {self.selected_model}")

    def end_chat(self):
        """结束聊天"""
        self.messages = []
        self.user_input.config(state=tk.DISABLED)
        self.update_chat_status("not_ready")
        self.update_buttons_state()
        self.print_out("聊天已结束。")

    def clear_output(self):
        """清空输出区域"""
        if hasattr(self.output, 'clear_all'):
            self.output.clear_all()
        else:
            self.output.delete(1.0, tk.END)

    def clear_api_key(self):
        """清除API密钥"""
        result = messagebox.askyesno("确认", "您确定要清除保存的API密钥吗？")
        if result:
            if delete_api_key_file():
                self.print_out("API密钥清除成功。")
                messagebox.showinfo("成功", "API密钥清除成功。")
            else:
                messagebox.showerror("错误", "清除API密钥失败。")

    def toggle_markdown_rendering(self):
        """切换Markdown渲染"""
        self.markdown_enabled = not self.markdown_enabled
        status_text = "开" if self.markdown_enabled else "关"
        self.markdown_btn.config(text=f"Markdown: {status_text}")
        self.print_out(f"Markdown渲染: {status_text}")

    def print_out(self, message, end="\n"):
        """输出信息到输出区域"""
        if not hasattr(self, 'output'):
            return
            
        # 添加时间戳
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
        full_message = timestamp + str(message)
        
        # 输出到控件
        if hasattr(self.output, 'append_and_render'):
            self.output.append_and_render(full_message, end, self.markdown_enabled)
        else:
            self.output.insert(tk.END, full_message + end)
            self.output.see(tk.END)

    def on_input_change(self, event=None):
        """输入框内容改变事件"""
        content = ""
        try:
            content = self.user_input.get("1.0", tk.END).strip()
        except:
            pass
        
        if content and self.client and self.selected_model:
            self.send_btn.config(state=tk.NORMAL)
        else:
            self.send_btn.config(state=tk.DISABLED)

    def increase_font_size(self):
        """增加字体大小"""
        if self.output_font_size < 24:
            self.output_font_size += 1
            self.update_output_font()

    def decrease_font_size(self):
        """减少字体大小"""
        if self.output_font_size > 8:
            self.output_font_size -= 1
            self.update_output_font()

    def set_font_size_from_entry(self, event=None):
        """从输入框设置字体大小"""
        try:
            new_size = self.font_size_var.get()
            if 8 <= new_size <= 24:
                self.output_font_size = new_size
                self.update_output_font()
            else:
                messagebox.showerror("错误", "字体大小必须在 8 和 24 之间")
                self.font_size_var.set(self.output_font_size)
        except tk.TclError:
            messagebox.showerror("错误", "请输入有效的字体大小 (8-24)")
            self.font_size_var.set(self.output_font_size)

    def update_output_font(self):
        """更新输出区域字体"""
        self.font_size_var.set(self.output_font_size)
        new_font = (self.output_font_family, self.output_font_size)
        
        try:
            self.output.configure(font=new_font)
            if hasattr(self.output, 'update_markdown_font'):
                self.output.update_markdown_font(self.output_font_family, self.output_font_size)
        except Exception as e:
            print(f"更新字体时出错: {e}")

    def update_buttons_state(self):
        """更新按钮状态"""
        # Query Balance 按钮
        can_query_balance = bool(self.client)
        self.balance_btn.config(state=tk.NORMAL if can_query_balance else tk.DISABLED)

        # Start Chat 按钮
        can_start_chat = bool(self.client and self.selected_model)
        self.chat_btn.config(state=tk.NORMAL if can_start_chat else tk.DISABLED)

        # New Session 按钮
        can_new = bool(self.client and self.selected_model)
        self.new_btn.config(state=tk.NORMAL if can_new else tk.DISABLED)

        # 发送按钮状态
        content = ""
        try:
            content = self.user_input.get("1.0", tk.END).strip()
        except:
            pass
        send_enabled = bool(self.client and self.selected_model and content)
        self.send_btn.config(state=tk.NORMAL if send_enabled else tk.DISABLED)

    # 状态管理相关方法
    def update_status_display(self, status_type, text, color):
        """更新状态显示"""
        self.status_data[status_type] = {"text": text, "color": color}
        
        # 如果状态窗口存在，更新显示
        if (self.status_window is not None and 
            self.status_window.winfo_exists() and 
            status_type in self.status_indicators):
            self.status_indicators[status_type].set_status(text, color)
        
        # 更新主界面的指示灯
        self.update_main_indicators()

    def update_main_indicators(self):
        """更新主界面上的状态指示灯"""
        color_map = {
            "red": "#ff4444",
            "green": "#44ff44", 
            "yellow": "#ffcc00",
            "gray": "#888888",
            "grey": "#888888"
        }
        
        # 右侧指示灯 - 聊天状态
        chat_color = self.status_data.get("chat", {}).get("color", "red")
        chat_indicator_color = color_map.get(chat_color.lower(), chat_color)
        self.chat_indicator_canvas.itemconfig(self.chat_indicator, fill=chat_indicator_color)
        
        # 左侧指示灯 - 综合状态
        client_color = self.status_data.get("client", {}).get("color", "red")
        network_color = self.status_data.get("network", {}).get("color", "red")
        model_color = self.status_data.get("model", {}).get("color", "red")
        http_color = self.status_data.get("http", {}).get("color", "red")
        
        all_green = all(color == "green" for color in [client_color, network_color, model_color, http_color])
        three_green_without_network = all(color == "green" for color in [client_color, model_color, http_color])
        
        if all_green:
            overall_color = "#44ff44"
        elif three_green_without_network and network_color == "yellow":
            overall_color = "#ffcc00"
        else:
            overall_color = "#ff4444"
            
        self.overall_indicator_canvas.itemconfig(self.overall_indicator, fill=overall_color)

    def update_client_status(self):
        """更新客户端状态"""
        if self.client and self.api_key:
            self.update_status_display("client", "已初始化", "green")
        elif hasattr(self, 'api_key_entry') and self.api_key_entry.winfo_exists():
            api_key_entered = bool(self.api_key_entry.get().strip())
            if api_key_entered:
                self.update_status_display("client", "已输入API密钥", "yellow")
            else:
                self.update_status_display("client", "无API密钥", "red")
        else:
            self.update_status_display("client", "无API密钥", "red")

    def update_model_status(self, status=None):
        """更新模型状态"""
        if not self.client:
            self.update_status_display("model", "不可用", "red")
        elif status == "fetch_fail":
            self.update_status_display("model", "获取失败", "red")
        elif self.selected_model:
            self.update_status_display("model", f"已选择: {self.selected_model}", "green")
        elif self.available_models:
            self.update_status_display("model", "可用 (未选择)", "yellow")
        else:
            self.update_status_display("model", "未选择", "red")

    def update_network_status(self):
        """更新网络状态"""
        try:
            self.update_status_display("network", "检查中...", "gray")
        except Exception as e:
            print(f"更新网络状态失败: {e}")

    def update_http_status(self, status_code=None, operation=None):
        """更新HTTP状态"""
        if status_code is None:
            self.update_status_display("http", "OK", "green")
        elif status_code == 200:
            self.update_status_display("http", "正常 (200)", "green")
        else:
            self.update_status_display("http", f"错误 ({status_code})", "red")

    def update_chat_status(self, status):
        """更新聊天状态"""
        status_map = {
            "not_ready": ("未就绪", "red"),
            "ready": ("就绪", "green"),
            "chatting": ("聊天中", "yellow"),
            "streaming": ("流式输出中", "yellow")
        }
        text, color = status_map.get(status, ("未知", "gray"))
        self.update_status_display("chat", text, color)

    def network_status_loop(self):
        """网络状态检查循环"""
        if hasattr(self, 'network_thread_stop') and self.network_thread_stop:
            return
            
        while not getattr(self, 'network_thread_stop', True):
            try:
                start_time = time.time()
                socket.create_connection(("api.deepseek.com", 443), timeout=5)
                end_time = time.time()
                
                latency_ms = round((end_time - start_time) * 1000, 1)
                
                if latency_ms < 200:
                    color = "green"
                elif latency_ms < 500:
                    color = "yellow"
                else:
                    color = "red"
                
                status_text = f"已连接 ({latency_ms}ms)"
                self.master.after(0, lambda: self.update_status_display("network", status_text, color))
                
            except socket.timeout:
                self.master.after(0, lambda: self.update_status_display("network", "超时", "red"))
            except Exception:
                self.master.after(0, lambda: self.update_status_display("network", "已断开", "red"))
            
            # 等待30秒再次检查
            for _ in range(30):
                if getattr(self, 'network_thread_stop', True):
                    break
                time.sleep(1)

    def toggle_status_window(self):
        """切换状态监控窗口的显示/隐藏（基本版本）"""
        if self.status_window is None or not self.status_window.winfo_exists():
            self.create_status_window()
            self.status_btn.config(text="隐藏状态")
        else:
            self.status_window.destroy()
            self.status_window = None
            self.status_btn.config(text="状态监控")

    def create_status_window(self):
        """创建独立的状态监控窗口"""
        self.status_window = tk.Toplevel(self.master)
        self.status_window.title("状态监控")
        self.status_window.geometry("320x160")
        self.status_window.resizable(False, False)
        
        # 设置窗口位置
        main_x = self.master.winfo_x()
        main_y = self.master.winfo_y()
        main_width = self.master.winfo_width()
        self.status_window.geometry(f"320x160+{main_x + main_width + 10}+{main_y}")
        
        # 添加标题栏
        title_frame = tk.Frame(self.status_window, bg="darkgray", height=25)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="状态监控", bg="darkgray", fg="white", font=("Arial", 9, "bold"))
        title_label.pack(side=tk.LEFT, padx=5, pady=3)
        
        # 内容区域
        content_frame = tk.Frame(self.status_window, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 创建状态指示器
        self.status_indicators["client"] = StatusIndicator(content_frame, "客户端")
        self.status_indicators["client"].pack(fill=tk.X, padx=5, pady=2)

        self.status_indicators["network"] = StatusIndicator(content_frame, "网络")
        self.status_indicators["network"].pack(fill=tk.X, padx=5, pady=2)

        self.status_indicators["model"] = StatusIndicator(content_frame, "模型")
        self.status_indicators["model"].pack(fill=tk.X, padx=5, pady=2)

        self.status_indicators["http"] = StatusIndicator(content_frame, "HTTP")
        self.status_indicators["http"].pack(fill=tk.X, padx=5, pady=2)

        self.status_indicators["chat"] = StatusIndicator(content_frame, "聊天")
        self.status_indicators["chat"].pack(fill=tk.X, padx=5, pady=2)

        # 更新所有状态显示
        for key, data in self.status_data.items():
            if key in self.status_indicators:
                self.status_indicators[key].set_status(data["text"], data["color"])

        # 使窗口始终在最前面
        self.status_window.attributes("-topmost", True)

    # 添加一些必要的方法以兼容管理器
    def get_api_key_from_entry(self):
        """从输入框获取API密钥"""
        try:
            return self.api_key_entry.get().strip()
        except:
            return ""

    def show_error_message(self, title, message):
        """显示错误消息对话框"""
        messagebox.showerror(title, message)

    def get_selected_model(self):
        """获取当前选中的模型"""
        try:
            selected = self.model_var.get()
            return selected if selected != "请选择一个模型..." else None
        except:
            return None

    def set_model_list(self, models_list):
        """设置模型列表到下拉框"""
        try:
            self.model_combobox['values'] = models_list
            if not models_list:
                self.model_var.set("暂无可用模型")
            elif self.selected_model not in models_list:
                self.model_var.set("请选择一个模型...")
        except Exception as e:
            print(f"设置模型列表失败: {e}")

    def enable_control(self, control_name, enabled=True):
        """启用/禁用控件"""
        try:
            state = tk.NORMAL if enabled else tk.DISABLED
            
            control_mapping = {
                'refresh_models': 'refresh_models_btn',
                'clear_api': 'clear_apikey_btn',
                'balance': 'balance_btn',
                'chat': 'chat_btn',
                'send': 'send_btn',
                'stop': 'stop_btn',
                'user_input': 'user_input'
            }
            
            widget_name = control_mapping.get(control_name, control_name)
            
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                widget.config(state=state)
                
        except Exception as e:
            print(f"控制控件状态失败: {e}")

    # 清理资源方法
    def destroy(self):
        """清理GUI资源"""
        try:
            # 停止网络监控线程
            if hasattr(self, 'network_thread_stop'):
                self.network_thread_stop = True
            
            # 清理状态控制器
            if hasattr(self, 'status_controller'):
                self.status_controller.destroy()
                
            # 清理状态窗口
            if hasattr(self, 'status_window') and self.status_window:
                self.status_window.destroy()
                
        except Exception as e:
            print(f"清理GUI资源时出错: {e}")