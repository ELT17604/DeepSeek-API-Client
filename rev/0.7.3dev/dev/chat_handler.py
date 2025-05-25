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

import threading
import re
import time
import json
from config import CHAT_CONFIG, HTTP_CONFIG

class ChatSession:
    """聊天会话类，管理单个聊天会话的消息历史"""
    
    def __init__(self, session_id=None, model_name=None):
        """
        初始化聊天会话
        
        Args:
            session_id (str): 会话ID，如果为None则自动生成
            model_name (str): 使用的模型名称
        """
        self.session_id = session_id or self._generate_session_id()
        self.model_name = model_name
        self.messages = []
        self.created_time = time.time()
        self.last_activity = time.time()
        self.message_count = 0
        self.total_tokens = 0
        
    def _generate_session_id(self):
        """生成会话ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def add_message(self, role, content, tokens=0):
        """
        添加消息到会话
        
        Args:
            role (str): 消息角色 (user/assistant)
            content (str): 消息内容
            tokens (int): 消息令牌数
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "tokens": tokens
        }
        self.messages.append(message)
        self.message_count += 1
        self.total_tokens += tokens
        self.last_activity = time.time()
    
    def get_api_messages(self):
        """
        获取用于API调用的消息格式
        
        Returns:
            list: 适用于OpenAI API的消息列表
        """
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
    
    def clear_messages(self):
        """清空会话消息"""
        self.messages = []
        self.message_count = 0
        self.total_tokens = 0
        self.last_activity = time.time()
    
    def get_session_info(self):
        """
        获取会话信息
        
        Returns:
            dict: 会话信息字典
        """
        return {
            "session_id": self.session_id,
            "model_name": self.model_name,
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "created_time": self.created_time,
            "last_activity": self.last_activity,
            "duration": time.time() - self.created_time
        }
    
    def export_messages(self, format_type="json"):
        """
        导出会话消息
        
        Args:
            format_type (str): 导出格式 ("json", "text", "markdown")
            
        Returns:
            str: 导出的字符串内容
        """
        if format_type == "json":
            export_data = {
                "session_info": self.get_session_info(),
                "messages": self.messages
            }
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        
        elif format_type == "text":
            lines = [f"聊天会话 {self.session_id}", "=" * 30]
            for msg in self.messages:
                timestamp = time.strftime("%H:%M:%S", time.localtime(msg["timestamp"]))
                role_name = "用户" if msg["role"] == "user" else "助手"
                lines.append(f"[{timestamp}] {role_name}: {msg['content']}")
            return "\n".join(lines)
        
        elif format_type == "markdown":
            lines = [f"# 聊天会话 {self.session_id}", ""]
            for msg in self.messages:
                timestamp = time.strftime("%H:%M:%S", time.localtime(msg["timestamp"]))
                if msg["role"] == "user":
                    lines.append(f"**[{timestamp}] 用户**: {msg['content']}")
                else:
                    lines.append(f"**[{timestamp}] 助手**: {msg['content']}")
                lines.append("")
            return "\n".join(lines)
        
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")

class StreamingHandler:
    """流式输出处理器"""
    
    def __init__(self, gui_instance=None, output_callback=None):
        """
        初始化流式处理器
        
        Args:
            gui_instance: GUI实例
            output_callback: 输出回调函数
        """
        self.gui = gui_instance
        self.output_callback = output_callback
        self.is_streaming = False
        self.should_stop = False
        self.current_content = ""
        
    def start_streaming(self, response_stream):
        """
        开始处理流式响应
        
        Args:
            response_stream: OpenAI流式响应对象
            
        Returns:
            str: 完整的回复内容
        """
        self.is_streaming = True
        self.should_stop = False
        self.current_content = ""
        
        try:
            for chunk in response_stream:
                if self.should_stop:
                    break
                
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    self.current_content += content
                    
                    # 调用输出回调
                    if self.output_callback:
                        self.output_callback(content)
                    elif self.gui:
                        self._gui_append_content(content)
            
            return self.current_content
            
        except Exception as e:
            if self.gui:
                self.gui.print_out(f"流式输出错误: {e}")
            raise
        finally:
            self.is_streaming = False
    
    def stop_streaming(self):
        """停止流式输出"""
        self.should_stop = True
    
    def _gui_append_content(self, content):
        """在GUI中追加内容"""
        if self.gui and hasattr(self.gui, 'master'):
            self.gui.master.after(0, lambda: self._append_streaming_content(content))
    
    def _append_streaming_content(self, content):
        """在主线程中追加流式内容"""
        if self.gui and hasattr(self.gui.output, 'append_raw_text'):
            self.gui.output.append_raw_text(content, end="")
            # 根据当前渲染模式重新渲染
            if hasattr(self.gui, 'markdown_enabled') and self.gui.markdown_enabled:
                self.gui.output.render_as_markdown()
            else:
                self.gui.output.render_as_plain_text()
        elif self.gui and hasattr(self.gui, 'output'):
            self.gui.output.insert("end", content)
            self.gui.output.see("end")

class ChatHandler:
    """聊天处理器 - 管理聊天功能和会话"""
    
    def __init__(self, gui_instance=None, client_manager=None, model_manager=None):
        """
        初始化聊天处理器
        
        Args:
            gui_instance: GUI实例
            client_manager: 客户端管理器
            model_manager: 模型管理器
        """
        self.gui = gui_instance
        self.client_manager = client_manager
        self.model_manager = model_manager
        
        # 当前会话
        self.current_session = None
        
        # 流式处理器
        self.streaming_handler = StreamingHandler(gui_instance)
        
        # 聊天状态
        self.is_chatting = False
        self.is_streaming = False
        
        # 聊天配置
        self.chat_config = CHAT_CONFIG.copy()
    
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
    
    def start_chat(self):
        """开始聊天会话"""
        # 验证前置条件
        if not self._validate_chat_prerequisites():
            return False
        
        # 获取当前模型
        model_name = None
        if self.model_manager:
            model_name = self.model_manager.get_selected_model()
        elif self.gui and hasattr(self.gui, 'selected_model'):
            model_name = self.gui.selected_model
        
        if not model_name:
            if self.gui:
                self.gui.show_error_message("错误", "请先选择一个模型")
            return False
        
        # 创建新会话
        self.current_session = ChatSession(model_name=model_name)
        self.is_chatting = True
        
        # 更新GUI状态
        if self.gui:
            self.gui.user_input.config(state="normal")
            self.gui.user_input.focus_set()
            self.gui.update_chat_status("ready")
            self.gui.update_buttons_state()
            self.gui.print_out(f"开始与模型 {model_name} 聊天")
            self.gui.print_out("输入您的消息并按发送或回车键开始对话。")
        
        return True
    
    def _validate_chat_prerequisites(self):
        """验证聊天前置条件"""
        # 检查客户端
        client = None
        if self.client_manager:
            client = self.client_manager.get_client()
        elif self.gui and hasattr(self.gui, 'client'):
            client = self.gui.client
        
        if not client:
            if self.gui:
                self.gui.show_error_message("错误", "请先初始化客户端")
            return False
        
        # 检查模型
        model = None
        if self.model_manager:
            model = self.model_manager.get_selected_model()
        elif self.gui and hasattr(self.gui, 'selected_model'):
            model = self.gui.selected_model
        
        if not model:
            if self.gui:
                self.gui.show_error_message("错误", "请先选择一个模型")
            return False
        
        return True
    
    def send_message(self, user_message):
        """
        发送用户消息并获取回复
        
        Args:
            user_message (str): 用户输入的消息
            
        Returns:
            bool: 发送是否成功
        """
        if not user_message or not user_message.strip():
            return False
        
        if not self.current_session:
            if self.gui:
                self.gui.show_error_message("错误", "请先开始聊天会话")
            return False
        
        user_message = user_message.strip()
        
        # 添加用户消息到会话
        self.current_session.add_message("user", user_message)
        
        # 显示用户输入
        if self.gui:
            self.gui.print_out(f"您: {user_message}")
        
        # 开始流式对话
        return self._start_streaming_chat()
    
    def _start_streaming_chat(self):
        """开始流式聊天"""
        if not self.current_session:
            return False
        
        self.is_streaming = True
        self.streaming_handler.should_stop = False
        
        # 更新GUI状态
        if self.gui:
            self.gui.update_chat_status("streaming")
            self.gui.enable_control('send', False)
            self.gui.enable_control('stop', True)
        
        # 在新线程中进行API调用
        thread = threading.Thread(target=self._streaming_chat_worker, daemon=True)
        thread.start()
        
        return True
    
    def _streaming_chat_worker(self):
        """流式聊天工作线程"""
        try:
            # 获取客户端
            client = None
            if self.client_manager:
                client = self.client_manager.get_client()
            elif self.gui and hasattr(self.gui, 'client'):
                client = self.gui.client
            
            if not client:
                raise Exception("客户端不可用")
            
            # 准备API参数
            api_params = {
                "model": self.current_session.model_name,
                "messages": self.current_session.get_api_messages(),
                "stream": True
            }
            
            # 应用聊天配置
            api_params.update({
                "max_tokens": self.chat_config.get("max_tokens", 4096),
                "temperature": self.chat_config.get("temperature", 0.7),
                "top_p": self.chat_config.get("top_p", 1.0),
                "frequency_penalty": self.chat_config.get("frequency_penalty", 0.0),
                "presence_penalty": self.chat_config.get("presence_penalty", 0.0)
            })
            
            # 调用API
            response = client.chat.completions.create(**api_params)
            
            # 更新HTTP状态 - 聊天请求成功
            if self.gui:
                self.gui.master.after(0, lambda: self.gui.update_http_status(200, "聊天"))
                self.gui.master.after(0, lambda: self.gui.print_out("助手: ", end=""))
            
            # 处理流式响应
            assistant_message = self.streaming_handler.start_streaming(response)
            
            if not self.streaming_handler.should_stop and assistant_message:
                # 添加助手回复到对话历史
                self.current_session.add_message("assistant", assistant_message)
                
                if self.gui:
                    self.gui.master.after(0, lambda: self.gui.print_out("", end="\n"))  # 换行
            
        except Exception as e:
            # 捕获聊天API的异常并解析HTTP状态
            error_msg = str(e)
            status_code = self.extract_status_code_from_error(error_msg)
            
            if self.gui:
                self.gui.master.after(0, lambda: self.gui.update_http_status(status_code, "聊天"))
                
                if status_code in [400, 401, 402, 403, 404, 422, 429, 500, 502, 503]:
                    self.gui.master.after(0, lambda: self.gui.show_http_error_dialog(status_code, "聊天"))
                elif status_code == 0:
                    if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                        self.gui.master.after(0, lambda: self.gui.print_out(f"网络错误: {error_msg}"))
                    else:
                        self.gui.master.after(0, lambda: self.gui.print_out(f"未知错误: {error_msg}"))
                
                self.gui.master.after(0, lambda: self.gui.print_out("聊天发生错误"))
        
        finally:
            # 恢复按钮状态
            if self.gui:
                self.gui.master.after(0, self._restore_chat_buttons)
    
    def _restore_chat_buttons(self):
        """恢复聊天按钮状态"""
        self.is_streaming = False
        if self.gui:
            self.gui.enable_control('send', True)
            self.gui.enable_control('stop', False)
            self.gui.update_chat_status("ready")
            self.gui.update_buttons_state()
    
    def stop_streaming(self):
        """停止流式输出"""
        self.streaming_handler.stop_streaming()
        
        if self.gui:
            self.gui.print_out("用户停止了流式输出。")
        
        # 立即恢复按钮状态
        self._restore_chat_buttons()
    
    def start_new_session(self):
        """开始新会话"""
        # 获取当前模型
        model_name = None
        if self.model_manager:
            model_name = self.model_manager.get_selected_model()
        elif self.gui and hasattr(self.gui, 'selected_model'):
            model_name = self.gui.selected_model
        
        # 创建新会话
        self.current_session = ChatSession(model_name=model_name)
        
        if self.gui:
            self.gui.print_out("开始新聊天会话。")
            if model_name:
                self.gui.print_out(f"当前模型: {model_name}")
    
    def end_chat(self):
        """结束聊天"""
        self.current_session = None
        self.is_chatting = False
        self.is_streaming = False
        
        # 停止任何正在进行的流式输出
        self.streaming_handler.stop_streaming()
        
        if self.gui:
            self.gui.user_input.config(state="disabled")
            self.gui.user_input.delete("1.0", "end")
            self.gui.update_chat_status("not_ready")
            self.gui.update_buttons_state()
            self.gui.print_out("聊天已结束。")
    
    def send_user_input_from_gui(self, event=None):
        """从GUI发送用户输入"""
        if not self.gui:
            return "break"
        
        # 处理键盘事件
        if event and event.keysym == "Return":
            if not (event.state & 0x4):  # 不是Ctrl+Enter
                if event.state & 0x1:  # Shift+Enter，插入换行
                    return "break"
        
        # 获取用户输入
        user_message = ""
        try:
            user_message = self.gui.user_input.get("1.0", "end").strip()
        except:
            pass
        
        if not user_message:
            return "break"
        
        if not self._validate_chat_prerequisites():
            return "break"
        
        # 清空输入框
        try:
            self.gui.user_input.delete("1.0", "end")
        except:
            pass
        
        # 发送消息
        self.send_message(user_message)
        
        return "break"
    
    def get_session_info(self):
        """
        获取当前会话信息
        
        Returns:
            dict: 会话信息，如果没有会话返回None
        """
        if self.current_session:
            return self.current_session.get_session_info()
        return None
    
    def export_current_session(self, format_type="json"):
        """
        导出当前会话
        
        Args:
            format_type (str): 导出格式
            
        Returns:
            str: 导出内容，如果没有会话返回None
        """
        if self.current_session:
            return self.current_session.export_messages(format_type)
        return None
    
    def update_chat_config(self, **kwargs):
        """
        更新聊天配置
        
        Args:
            **kwargs: 配置参数
        """
        for key, value in kwargs.items():
            if key in self.chat_config:
                self.chat_config[key] = value
        
        if self.gui:
            self.gui.print_out("聊天配置已更新")
    
    def get_chat_config(self):
        """
        获取当前聊天配置
        
        Returns:
            dict: 聊天配置字典
        """
        return self.chat_config.copy()
    
    def is_chat_active(self):
        """
        检查聊天是否活跃
        
        Returns:
            bool: 是否有活跃的聊天会话
        """
        return self.is_chatting and self.current_session is not None
    
    def is_streaming_active(self):
        """
        检查是否正在流式输出
        
        Returns:
            bool: 是否正在流式输出
        """
        return self.is_streaming
    
    def get_message_count(self):
        """
        获取当前会话的消息数量
        
        Returns:
            int: 消息数量，如果没有会话返回0
        """
        if self.current_session:
            return self.current_session.message_count
        return 0
    
    def get_total_tokens(self):
        """
        获取当前会话的总令牌数
        
        Returns:
            int: 总令牌数，如果没有会话返回0
        """
        if self.current_session:
            return self.current_session.total_tokens
        return 0
    
    def clear_current_session(self):
        """清空当前会话的消息历史"""
        if self.current_session:
            self.current_session.clear_messages()
            if self.gui:
                self.gui.print_out("当前会话消息已清空")
    
    def set_streaming_callback(self, callback):
        """
        设置流式输出回调函数
        
        Args:
            callback: 回调函数，接收内容参数
        """
        self.streaming_handler.output_callback = callback
    
    def validate_message_length(self, message):
        """
        验证消息长度
        
        Args:
            message (str): 要验证的消息
            
        Returns:
            tuple: (is_valid, error_message)
        """
        max_length = self.chat_config.get("max_message_length", 8000)
        
        if len(message) > max_length:
            return False, f"消息长度超过限制 ({len(message)}/{max_length} 字符)"
        
        if not message.strip():
            return False, "消息不能为空"
        
        return True, None
    
    def get_conversation_summary(self):
        """
        获取对话摘要
        
        Returns:
            dict: 对话摘要信息
        """
        if not self.current_session:
            return {"error": "没有活跃的会话"}
        
        info = self.current_session.get_session_info()
        user_messages = sum(1 for msg in self.current_session.messages if msg["role"] == "user")
        assistant_messages = sum(1 for msg in self.current_session.messages if msg["role"] == "assistant")
        
        return {
            "session_id": info["session_id"],
            "model": info["model_name"],
            "total_messages": info["message_count"],
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "total_tokens": info["total_tokens"],
            "duration_minutes": round(info["duration"] / 60, 2),
            "avg_message_length": round(
                sum(len(msg["content"]) for msg in self.current_session.messages) / max(1, info["message_count"])
            )
        }
    
    def destroy(self):
        """销毁聊天处理器并清理资源"""
        # 停止任何正在进行的流式输出
        if self.is_streaming:
            self.stop_streaming()
        
        # 结束聊天
        self.end_chat()
        
        # 清理引用
        self.gui = None
        self.client_manager = None
        self.model_manager = None
        self.streaming_handler = None

# 便捷函数
def create_chat_handler(gui_instance=None, client_manager=None, model_manager=None):
    """
    创建聊天处理器的便捷函数
    
    Args:
        gui_instance: GUI实例
        client_manager: 客户端管理器
        model_manager: 模型管理器
        
    Returns:
        ChatHandler: 聊天处理器实例
    """
    return ChatHandler(gui_instance, client_manager, model_manager)

def create_chat_session(model_name=None):
    """
    创建聊天会话的便捷函数
    
    Args:
        model_name (str): 模型名称
        
    Returns:
        ChatSession: 聊天会话实例
    """
    return ChatSession(model_name=model_name)

# GUI集成函数
def integrate_chat_handler_with_gui(gui_instance, client_manager=None, model_manager=None):
    """
    将聊天处理器集成到GUI实例中
    
    Args:
        gui_instance: GUI实例
        client_manager: 客户端管理器
        model_manager: 模型管理器
    """
    # 创建聊天处理器
    chat_handler = create_chat_handler(gui_instance, client_manager, model_manager)
    
    # 将处理器绑定到GUI
    gui_instance.chat_handler = chat_handler
    
    # 重写GUI的相关方法
    def new_start_chat():
        return chat_handler.start_chat()
    
    def new_send_user_input(event=None):
        return chat_handler.send_user_input_from_gui(event)
    
    def new_stop_streaming():
        return chat_handler.stop_streaming()
    
    def new_start_new_session():
        return chat_handler.start_new_session()
    
    def new_end_chat():
        return chat_handler.end_chat()
    
    # 绑定方法到GUI
    gui_instance.start_chat = new_start_chat
    gui_instance.send_user_input = new_send_user_input
    gui_instance.stop_streaming = new_stop_streaming
    gui_instance.start_new_session = new_start_new_session
    gui_instance.end_chat = new_end_chat
    
    # 添加聊天管理相关方法到GUI
    gui_instance.get_chat_handler = lambda: chat_handler
    gui_instance.get_session_info = lambda: chat_handler.get_session_info()
    gui_instance.export_chat_session = lambda fmt="json": chat_handler.export_current_session(fmt)
    gui_instance.get_conversation_summary = lambda: chat_handler.get_conversation_summary()
    gui_instance.update_chat_config = lambda **kwargs: chat_handler.update_chat_config(**kwargs)
    gui_instance.is_chat_active = lambda: chat_handler.is_chat_active()
    gui_instance.is_streaming_active = lambda: chat_handler.is_streaming_active()
    
    return chat_handler

# CLI支持函数
def run_cli_chat(client, model_name):
    """
    运行命令行聊天
    
    Args:
        client: OpenAI客户端实例
        model_name (str): 模型名称
    """
    session = ChatSession(model_name=model_name)
    
    print(f"开始与 {model_name} 聊天")
    print("输入 'quit' 退出，'new' 开始新会话，'info' 查看会话信息")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("您: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'new':
                session.clear_messages()
                print("开始新聊天会话。")
                continue
            elif user_input.lower() == 'info':
                info = session.get_session_info()
                print(f"会话信息: {info['message_count']} 条消息, "
                      f"{info['total_tokens']} 令牌, "
                      f"{round(info['duration']/60, 1)} 分钟")
                continue
            elif not user_input:
                continue
            
            # 添加用户消息
            session.add_message("user", user_input)
            
            # 获取AI回复
            print("助手: ", end="", flush=True)
            
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=session.get_api_messages(),
                    stream=True,
                    max_tokens=CHAT_CONFIG.get("max_tokens", 4096),
                    temperature=CHAT_CONFIG.get("temperature", 0.7)
                )
                
                assistant_message = ""
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        assistant_message += content
                
                print()  # 换行
                
                # 添加助手回复到对话历史
                session.add_message("assistant", assistant_message)
                
            except Exception as e:
                print(f"错误: {e}")
                
        except KeyboardInterrupt:
            print("\n再见!")
            break
        except Exception as e:
            print(f"错误: {e}")

# 错误处理装饰器
def handle_chat_errors(operation="聊天操作"):
    """
    聊天错误处理装饰器
    
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
                else:
                    print(f"{operation}失败: {error_msg}")
                return False
        return wrapper
    return decorator

# 测试和示例代码
if __name__ == "__main__":
    # 创建聊天处理器进行测试
    print("聊天处理器测试")
    print("=" * 30)
    
    handler = create_chat_handler()
    
    # 测试会话创建
    session = create_chat_session("test-model")
    print(f"创建会话: {session.session_id}")
    
    # 测试消息添加
    session.add_message("user", "Hello")
    session.add_message("assistant", "Hi there!")
    
    # 测试会话信息
    info = session.get_session_info()
    print(f"会话信息: {info}")
    
    # 测试导出功能
    exported = session.export_messages("text")
    print(f"导出文本:\n{exported}")
    
    # 测试配置
    config = handler.get_chat_config()
    print(f"聊天配置: {config}")
    
    # 测试消息验证
    is_valid, error = handler.validate_message_length("测试消息")
    print(f"消息验证: 有效={is_valid}, 错误={error}")