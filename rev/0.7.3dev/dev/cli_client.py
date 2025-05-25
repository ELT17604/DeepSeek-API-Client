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

import sys
import time
import signal
import os
from openai import OpenAI
from config import DEEPSEEK_API_BASE_URL_V1
from crypto_utils import save_api_key_to_file, load_api_key_from_file, delete_api_key_file
from model_manager import filter_model_list, search_models_by_keyword
from balance_service import query_balance_simple, format_balance_simple
from chat_handler import create_chat_session
from http_utils import extract_http_status_code

class CLIInputHandler:
    """CLI输入处理器，提供各种输入验证和处理功能"""
    
    def __init__(self):
        """初始化CLI输入处理器"""
        self.interrupted = False
        
        # 设置信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """处理Ctrl+C信号"""
        self.interrupted = True
        print("\n正在退出...")
        sys.exit(0)
    
    def get_user_input(self, prompt, allow_empty=False, validator=None):
        """
        获取用户输入
        
        Args:
            prompt (str): 提示信息
            allow_empty (bool): 是否允许空输入
            validator (callable): 验证函数，返回(is_valid, error_message)
            
        Returns:
            str: 用户输入，如果被中断返回None
        """
        while True:
            try:
                user_input = input(prompt).strip()
                
                if not user_input and not allow_empty:
                    print("输入不能为空，请重试。")
                    continue
                
                if validator:
                    is_valid, error_msg = validator(user_input)
                    if not is_valid:
                        print(f"输入无效: {error_msg}")
                        continue
                
                return user_input
                
            except KeyboardInterrupt:
                self.interrupted = True
                print("\n操作已取消。")
                return None
            except EOFError:
                print("\n输入结束。")
                return None
    
    def get_yes_no_input(self, prompt, default=None):
        """
        获取是/否输入
        
        Args:
            prompt (str): 提示信息
            default (bool): 默认值，None表示必须选择
            
        Returns:
            bool: 用户选择，如果被中断返回None
        """
        if default is True:
            choices = " (Y/n)"
        elif default is False:
            choices = " (y/N)"
        else:
            choices = " (y/n)"
        
        while True:
            response = self.get_user_input(prompt + choices, allow_empty=(default is not None))
            
            if response is None:
                return None
            
            if not response and default is not None:
                return default
            
            if response.lower() in ['y', 'yes', '是', '1']:
                return True
            elif response.lower() in ['n', 'no', '否', '0']:
                return False
            else:
                print("请输入 'y' (是) 或 'n' (否)。")
    
    def get_choice_input(self, prompt, choices, default=None):
        """
        获取选择输入
        
        Args:
            prompt (str): 提示信息
            choices (list): 选择列表
            default (int): 默认选择索引
            
        Returns:
            int: 选择索引，如果被中断返回None
        """
        print(prompt)
        for i, choice in enumerate(choices, 1):
            marker = " (默认)" if default and i == default else ""
            print(f"  {i}. {choice}{marker}")
        
        while True:
            choice_prompt = f"请选择 (1-{len(choices)})"
            if default:
                choice_prompt += f" [默认: {default}]"
            choice_prompt += ": "
            
            response = self.get_user_input(choice_prompt, allow_empty=(default is not None))
            
            if response is None:
                return None
            
            if not response and default is not None:
                return default - 1  # 转换为0基索引
            
            try:
                choice_index = int(response) - 1
                if 0 <= choice_index < len(choices):
                    return choice_index
                else:
                    print(f"请输入 1 到 {len(choices)} 之间的数字。")
            except ValueError:
                print("请输入有效数字。")
    
    def get_password_input(self, prompt):
        """
        获取密码输入（隐藏输入）
        
        Args:
            prompt (str): 提示信息
            
        Returns:
            str: 用户输入，如果被中断返回None
        """
        try:
            import getpass
            return getpass.getpass(prompt)
        except KeyboardInterrupt:
            self.interrupted = True
            print("\n操作已取消。")
            return None
        except EOFError:
            print("\n输入结束。")
            return None
        except Exception:
            # 如果getpass不可用，降级到普通输入
            print("注意: 输入将以明文显示")
            return self.get_user_input(prompt)

class CLIOutputFormatter:
    """CLI输出格式化器，提供统一的输出格式"""
    
    def __init__(self, enable_colors=True):
        """
        初始化输出格式化器
        
        Args:
            enable_colors (bool): 是否启用颜色输出
        """
        self.enable_colors = enable_colors and self._supports_color()
        
        # ANSI颜色代码
        self.colors = {
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'magenta': '\033[35m',
            'cyan': '\033[36m',
            'white': '\033[37m',
            'bold': '\033[1m',
            'reset': '\033[0m'
        }
    
    def _supports_color(self):
        """检查终端是否支持颜色"""
        return (
            hasattr(sys.stdout, 'isatty') and sys.stdout.isatty() and
            os.environ.get('TERM') != 'dumb'
        )
    
    def colorize(self, text, color):
        """
        给文本添加颜色
        
        Args:
            text (str): 文本内容
            color (str): 颜色名称
            
        Returns:
            str: 格式化后的文本
        """
        if not self.enable_colors or color not in self.colors:
            return text
        
        return f"{self.colors[color]}{text}{self.colors['reset']}"
    
    def print_header(self, text):
        """打印标题"""
        print()
        print(self.colorize("=" * 50, 'cyan'))
        print(self.colorize(text.center(50), 'bold'))
        print(self.colorize("=" * 50, 'cyan'))
        print()
    
    def print_section(self, text):
        """打印章节标题"""
        print()
        print(self.colorize(f"--- {text} ---", 'blue'))
        print()
    
    def print_success(self, text):
        """打印成功信息"""
        print(self.colorize(f"✓ {text}", 'green'))
    
    def print_error(self, text):
        """打印错误信息"""
        print(self.colorize(f"✗ {text}", 'red'))
    
    def print_warning(self, text):
        """打印警告信息"""
        print(self.colorize(f"⚠ {text}", 'yellow'))
    
    def print_info(self, text):
        """打印信息"""
        print(self.colorize(f"ℹ {text}", 'cyan'))
    
    def print_status(self, status, message):
        """
        打印状态信息
        
        Args:
            status (str): 状态类型 ('success', 'error', 'warning', 'info')
            message (str): 消息内容
        """
        method_map = {
            'success': self.print_success,
            'error': self.print_error,
            'warning': self.print_warning,
            'info': self.print_info
        }
        
        method = method_map.get(status, print)
        method(message)

class CLIProgressIndicator:
    """CLI进度指示器"""
    
    def __init__(self, message="处理中"):
        """
        初始化进度指示器
        
        Args:
            message (str): 显示消息
        """
        self.message = message
        self.is_running = False
        self.spinner_chars = "|/-\\"
        self.current_char = 0
    
    def start(self):
        """开始显示进度"""
        self.is_running = True
        print(f"{self.message}...", end="", flush=True)
    
    def update(self):
        """更新进度显示"""
        if self.is_running:
            print(f"\r{self.message}... {self.spinner_chars[self.current_char]}", end="", flush=True)
            self.current_char = (self.current_char + 1) % len(self.spinner_chars)
    
    def stop(self, success=True, final_message=None):
        """
        停止进度显示
        
        Args:
            success (bool): 是否成功
            final_message (str): 最终消息
        """
        if self.is_running:
            self.is_running = False
            if final_message:
                print(f"\r{final_message}")
            elif success:
                print(f"\r{self.message}... 完成")
            else:
                print(f"\r{self.message}... 失败")

class DeepSeekCLI:
    """命令行版本的DeepSeek客户端"""
    
    def __init__(self):
        """初始化CLI客户端"""
        self.api_key = ""
        self.client = None
        self.selected_model = None
        self.messages = []
        self.available_models = []
        self.session = None
        
        # 初始化组件
        self.input_handler = CLIInputHandler()
        self.output_formatter = CLIOutputFormatter()
        
        # 应用信息
        self.app_name = "DeepSeek CLI 客户端"
        self.app_version = "v0.7.3"
    
    def show_welcome(self):
        """显示欢迎信息"""
        self.output_formatter.print_header(f"{self.app_name} {self.app_version}")
        print("欢迎使用DeepSeek API命令行客户端！")
        print("输入 'help' 查看可用命令，输入 'quit' 退出。")
        print()
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
可用命令:
  help        - 显示此帮助信息
  status      - 显示客户端状态
  models      - 获取和选择模型
  balance     - 查询账户余额
  chat        - 开始聊天会话
  session     - 会话管理 (new/info/clear)
  config      - 配置管理
  quit/exit   - 退出程序

聊天命令 (在聊天模式中):
  /quit       - 退出聊天
  /new        - 开始新会话
  /info       - 显示会话信息
  /help       - 显示聊天帮助
"""
        print(help_text)
    
    def load_api_key(self):
        """加载API密钥"""
        # 首先尝试从文件加载
        saved_key = load_api_key_from_file()
        if saved_key:
            self.output_formatter.print_info("找到保存的API密钥，正在加载...")
            self.api_key = saved_key
            return True
        
        # 如果没有保存的密钥，提示用户输入
        self.output_formatter.print_warning("未找到保存的API密钥。")
        
        while not self.api_key:
            api_key = self.input_handler.get_password_input("请输入您的DeepSeek API密钥: ")
            
            if api_key is None:  # 用户取消
                return False
            
            if not api_key.strip():
                self.output_formatter.print_error("API密钥不能为空")
                continue
            
            self.api_key = api_key.strip()
            
            # 询问是否保存
            save_choice = self.input_handler.get_yes_no_input("是否保存API密钥以供将来使用？", default=True)
            
            if save_choice is None:  # 用户取消
                return False
            
            if save_choice:
                if save_api_key_to_file(self.api_key):
                    self.output_formatter.print_success("API密钥保存成功")
                else:
                    self.output_formatter.print_error("API密钥保存失败")
            
            return True
        
        return False
    
    def initialize_client(self):
        """初始化客户端"""
        progress = CLIProgressIndicator("正在初始化客户端")
        progress.start()
        
        try:
            # 创建客户端
            self.client = OpenAI(api_key=self.api_key, base_url=DEEPSEEK_API_BASE_URL_V1)
            
            # 测试连接
            time.sleep(0.5)  # 模拟处理时间
            models_response = self.client.models.list()
            
            progress.stop(success=True, final_message="客户端初始化成功!")
            return True
            
        except Exception as e:
            progress.stop(success=False, final_message="客户端初始化失败")
            
            error_msg = str(e)
            status_code = extract_http_status_code(error_msg)
            
            if status_code == 401:
                self.output_formatter.print_error("认证失败: API密钥无效")
            elif status_code == 403:
                self.output_formatter.print_error("访问被禁: 请检查账户状态")
            elif status_code == 429:
                self.output_formatter.print_error("请求过于频繁: 请稍后重试")
            elif status_code == 0:
                self.output_formatter.print_error(f"网络错误: {error_msg}")
            else:
                self.output_formatter.print_error(f"初始化失败: {error_msg}")
            
            return False
    
    def fetch_models(self):
        """获取可用模型"""
        if not self.client:
            self.output_formatter.print_error("请先初始化客户端")
            return False
        
        progress = CLIProgressIndicator("正在获取可用模型")
        progress.start()
        
        try:
            models_response = self.client.models.list()
            raw_models = [model.id for model in models_response.data]
            
            # 使用模型管理器的过滤功能
            filtered_models = filter_model_list(raw_models)
            
            progress.stop(success=True, final_message=f"获取到 {len(filtered_models)} 个模型")
            
            if not filtered_models:
                self.output_formatter.print_warning("未找到可用模型")
                return False
            
            self.available_models = filtered_models
            
            # 显示模型列表
            print("\n可用模型:")
            for i, model in enumerate(filtered_models, 1):
                marker = " (已选择)" if model == self.selected_model else ""
                print(f"  {i:2d}. {model}{marker}")
            
            if len(raw_models) != len(filtered_models):
                print(f"\n注意: 共有 {len(raw_models)} 个模型，已过滤显示 {len(filtered_models)} 个")
            
            return True
            
        except Exception as e:
            progress.stop(success=False, final_message="获取模型失败")
            
            error_msg = str(e)
            status_code = extract_http_status_code(error_msg)
            
            if status_code == 401:
                self.output_formatter.print_error("认证失败: 请检查API密钥")
            elif status_code == 429:
                self.output_formatter.print_error("请求过于频繁: 请稍后重试")
            else:
                self.output_formatter.print_error(f"获取模型失败: {error_msg}")
            
            return False
    
    def select_model(self):
        """选择模型"""
        if not self.available_models:
            self.output_formatter.print_warning("没有可用模型，请先获取模型列表")
            return False
        
        # 显示当前选择
        if self.selected_model:
            print(f"当前选择: {self.selected_model}")
        
        # 获取用户选择
        choice_index = self.input_handler.get_choice_input(
            "请选择一个模型:",
            self.available_models
        )
        
        if choice_index is None:  # 用户取消
            return False
        
        self.selected_model = self.available_models[choice_index]
        self.output_formatter.print_success(f"已选择模型: {self.selected_model}")
        return True
    
    def search_and_select_model(self):
        """搜索并选择模型"""
        if not self.available_models:
            self.output_formatter.print_warning("没有可用模型，请先获取模型列表")
            return False
        
        keyword = self.input_handler.get_user_input("请输入搜索关键词: ", allow_empty=True)
        
        if keyword is None:  # 用户取消
            return False
        
        if not keyword:
            # 显示所有模型
            matching_models = self.available_models
        else:
            # 使用模型管理器的搜索功能
            matching_models = search_models_by_keyword(self.available_models, keyword)
        
        if not matching_models:
            self.output_formatter.print_warning(f"未找到包含 '{keyword}' 的模型")
            return False
        
        print(f"\n找到 {len(matching_models)} 个匹配的模型:")
        choice_index = self.input_handler.get_choice_input(
            "请选择一个模型:",
            matching_models
        )
        
        if choice_index is None:  # 用户取消
            return False
        
        self.selected_model = matching_models[choice_index]
        self.output_formatter.print_success(f"已选择模型: {self.selected_model}")
        return True
    
    def query_balance(self):
        """查询账户余额"""
        if not self.api_key:
            self.output_formatter.print_error("请先设置API密钥")
            return False
        
        progress = CLIProgressIndicator("正在查询账户余额")
        progress.start()
        
        try:
            success, balance_data, error = query_balance_simple(self.api_key)
            
            if success:
                progress.stop(success=True, final_message="余额查询成功")
                
                if balance_data.get("is_available", False):
                    self.output_formatter.print_success("服务状态: 可用")
                    
                    balance_infos = balance_data.get("balance_infos", [])
                    if balance_infos:
                        print("\n详细余额信息:")
                        for idx, info in enumerate(balance_infos, 1):
                            print(f"  余额 #{idx}:")
                            print(f"    货币: {info.get('currency', 'N/A')}")
                            print(f"    总余额: {info.get('total_balance', 'N/A')}")
                            print(f"    授权余额: {info.get('granted_balance', 'N/A')}")
                            print(f"    充值余额: {info.get('topped_up_balance', 'N/A')}")
                        
                        # 显示主要余额
                        main_balance = format_balance_simple(balance_data)
                        print(f"\n主要余额: {self.output_formatter.colorize(main_balance, 'bold')}")
                        
                        # 检查低余额警告
                        primary_balance = balance_infos[0].get('total_balance', 0)
                        try:
                            if float(primary_balance) < 1.0:
                                self.output_formatter.print_warning("账户余额较低，建议及时充值！")
                        except (ValueError, TypeError):
                            pass
                    else:
                        self.output_formatter.print_warning("未找到详细余额信息")
                else:
                    self.output_formatter.print_warning("服务状态: 不可用")
                    message = balance_data.get("message", "")
                    if message:
                        print(f"API消息: {message}")
                
                return True
            else:
                progress.stop(success=False, final_message="余额查询失败")
                self.output_formatter.print_error(f"查询失败: {error}")
                return False
                
        except Exception as e:
            progress.stop(success=False, final_message="余额查询异常")
            self.output_formatter.print_error(f"查询异常: {e}")
            return False
    
    def show_status(self):
        """显示客户端状态"""
        self.output_formatter.print_section("客户端状态")
        
        # API密钥状态
        if self.api_key:
            masked_key = self.api_key[:4] + "*" * (len(self.api_key) - 8) + self.api_key[-4:]
            print(f"API密钥: {masked_key}")
        else:
            print("API密钥: 未设置")
        
        # 客户端状态
        client_status = "已初始化" if self.client else "未初始化"
        print(f"客户端: {client_status}")
        
        # 模型状态
        model_status = f"已选择 ({self.selected_model})" if self.selected_model else "未选择"
        available_count = f" (可用: {len(self.available_models)})" if self.available_models else ""
        print(f"模型: {model_status}{available_count}")
        
        # 会话状态
        if self.session:
            session_info = self.session.get_session_info()
            print(f"会话: 活跃 (消息: {session_info['message_count']}, 令牌: {session_info['total_tokens']})")
        else:
            print("会话: 无")
        
        print()
    
    def manage_session(self, action=None):
        """会话管理"""
        if action is None:
            actions = ["新建会话", "会话信息", "清空会话", "取消"]
            choice_index = self.input_handler.get_choice_input("会话管理:", actions)
            
            if choice_index is None or choice_index == 3:  # 取消
                return
            
            action_map = ["new", "info", "clear"]
            action = action_map[choice_index]
        
        if action == "new":
            self.session = create_chat_session(self.selected_model)
            self.messages = []
            self.output_formatter.print_success("已创建新会话")
            
        elif action == "info":
            if self.session:
                info = self.session.get_session_info()
                print(f"\n会话信息:")
                print(f"  会话ID: {info['session_id']}")
                print(f"  模型: {info['model_name']}")
                print(f"  消息数: {info['message_count']}")
                print(f"  总令牌: {info['total_tokens']}")
                print(f"  持续时间: {round(info['duration']/60, 1)} 分钟")
            else:
                self.output_formatter.print_warning("没有活跃的会话")
                
        elif action == "clear":
            if self.session:
                self.session.clear_messages()
                self.messages = []
                self.output_formatter.print_success("会话已清空")
            else:
                self.output_formatter.print_warning("没有活跃的会话")
    
    def start_chat(self):
        """开始聊天会话"""
        if not self.client:
            self.output_formatter.print_error("请先初始化客户端")
            return False
        
        if not self.selected_model:
            self.output_formatter.print_error("请先选择模型")
            return False
        
        # 创建会话（如果没有）
        if not self.session:
            self.session = create_chat_session(self.selected_model)
            self.messages = []
        
        self.output_formatter.print_header(f"与 {self.selected_model} 聊天")
        print("聊天命令:")
        print("  /quit   - 退出聊天")
        print("  /new    - 开始新会话")
        print("  /info   - 显示会话信息")
        print("  /help   - 显示帮助")
        print()
        print("开始对话...")
        print("-" * 50)
        
        while True:
            try:
                # 获取用户输入
                user_input = input(f"\n{self.output_formatter.colorize('您', 'cyan')}: ").strip()
                
                # 处理聊天命令
                if user_input.startswith('/'):
                    command = user_input[1:].lower()
                    
                    if command == 'quit':
                        break
                    elif command == 'new':
                        self.session = create_chat_session(self.selected_model)
                        self.messages = []
                        self.output_formatter.print_success("开始新会话")
                        continue
                    elif command == 'info':
                        if self.session:
                            info = self.session.get_session_info()
                            print(f"会话信息: {info['message_count']} 条消息, "
                                  f"{info['total_tokens']} 令牌, "
                                  f"{round(info['duration']/60, 1)} 分钟")
                        else:
                            print("没有活跃的会话")
                        continue
                    elif command == 'help':
                        print("聊天命令:")
                        print("  /quit   - 退出聊天")
                        print("  /new    - 开始新会话")
                        print("  /info   - 显示会话信息")
                        print("  /help   - 显示此帮助")
                        continue
                    else:
                        print(f"未知命令: {command}")
                        continue
                
                if not user_input:
                    continue
                
                # 添加用户消息到会话
                if self.session:
                    self.session.add_message("user", user_input)
                
                # 添加到消息历史
                self.messages.append({"role": "user", "content": user_input})
                
                # 获取AI回复
                print(f"{self.output_formatter.colorize('助手', 'green')}: ", end="", flush=True)
                
                response = self.client.chat.completions.create(
                    model=self.selected_model,
                    messages=self.messages,
                    stream=True,
                    max_tokens=4096,
                    temperature=0.7
                )
                
                assistant_message = ""
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        assistant_message += content
                
                print()  # 换行
                
                # 添加助手回复到会话和消息历史
                if self.session:
                    self.session.add_message("assistant", assistant_message)
                
                self.messages.append({"role": "assistant", "content": assistant_message})
                
            except KeyboardInterrupt:
                print("\n\n聊天已中断。")
                break
            except Exception as e:
                error_msg = str(e)
                status_code = extract_http_status_code(error_msg)
                
                if status_code == 401:
                    self.output_formatter.print_error("认证失败: 请检查API密钥")
                elif status_code == 402:
                    self.output_formatter.print_error("余额不足: 请充值账户")
                elif status_code == 429:
                    self.output_formatter.print_error("请求过于频繁: 请稍后重试")
                elif status_code == 0:
                    self.output_formatter.print_error(f"网络错误: {error_msg}")
                else:
                    self.output_formatter.print_error(f"聊天错误: {error_msg}")
        
        self.output_formatter.print_info("聊天已结束")
        return True
    
    def manage_config(self):
        """配置管理"""
        config_options = [
            "查看API密钥",
            "更改API密钥", 
            "删除保存的API密钥",
            "切换颜色输出",
            "返回"
        ]
        
        while True:
            choice_index = self.input_handler.get_choice_input("配置管理:", config_options)
            
            if choice_index is None or choice_index == 4:  # 返回
                break
            
            if choice_index == 0:  # 查看API密钥
                if self.api_key:
                    masked_key = self.api_key[:4] + "*" * (len(self.api_key) - 8) + self.api_key[-4:]
                    print(f"当前API密钥: {masked_key}")
                else:
                    print("未设置API密钥")
            
            elif choice_index == 1:  # 更改API密钥
                new_key = self.input_handler.get_password_input("请输入新的API密钥: ")
                if new_key and new_key.strip():
                    self.api_key = new_key.strip()
                    self.client = None  # 重置客户端
                    self.output_formatter.print_success("API密钥已更新，请重新初始化客户端")
                    
                    # 询问是否保存
                    save_choice = self.input_handler.get_yes_no_input("是否保存新的API密钥？", default=True)
                    if save_choice:
                        if save_api_key_to_file(self.api_key):
                            self.output_formatter.print_success("API密钥已保存")
                        else:
                            self.output_formatter.print_error("API密钥保存失败")
            
            elif choice_index == 2:  # 删除保存的API密钥
                confirm = self.input_handler.get_yes_no_input("确定要删除保存的API密钥吗？", default=False)
                if confirm:
                    if delete_api_key_file():
                        self.output_formatter.print_success("已删除保存的API密钥")
                    else:
                        self.output_formatter.print_error("删除失败")
            
            elif choice_index == 3:  # 切换颜色输出
                self.output_formatter.enable_colors = not self.output_formatter.enable_colors
                status = "启用" if self.output_formatter.enable_colors else "禁用"
                self.output_formatter.print_info(f"颜色输出已{status}")
    
    def run_interactive_mode(self):
        """运行交互模式"""
        self.show_welcome()
        
        while True:
            try:
                command = self.input_handler.get_user_input("\n> ", allow_empty=True)
                
                if command is None:  # Ctrl+C
                    break
                
                if not command:
                    continue
                
                command = command.lower()
                
                if command in ['quit', 'exit', 'q']:
                    break
                elif command in ['help', 'h', '?']:
                    self.show_help()
                elif command == 'status':
                    self.show_status()
                elif command == 'models':
                    self.handle_models_command()
                elif command == 'balance':
                    self.query_balance()
                elif command == 'chat':
                    self.start_chat()
                elif command == 'session':
                    self.manage_session()
                elif command == 'config':
                    self.manage_config()
                else:
                    print(f"未知命令: {command}")
                    print("输入 'help' 查看可用命令")
                    
            except KeyboardInterrupt:
                print("\n\n再见!")
                break
            except Exception as e:
                self.output_formatter.print_error(f"发生错误: {e}")
        
        self.output_formatter.print_info("感谢使用 DeepSeek CLI 客户端!")
    
    def handle_models_command(self):
        """处理模型相关命令"""
        model_options = [
            "获取模型列表",
            "选择模型",
            "搜索模型",
            "返回"
        ]
        
        choice_index = self.input_handler.get_choice_input("模型管理:", model_options)
        
        if choice_index is None or choice_index == 3:  # 返回
            return
        
        if choice_index == 0:  # 获取模型列表
            self.fetch_models()
        elif choice_index == 1:  # 选择模型
            self.select_model()
        elif choice_index == 2:  # 搜索模型
            self.search_and_select_model()
    
    def run_guided_setup(self):
        """运行引导式设置"""
        self.output_formatter.print_header("DeepSeek CLI 客户端设置向导")
        
        # 步骤1: 加载或输入API密钥
        self.output_formatter.print_section("步骤 1: API密钥")
        if not self.load_api_key():
            self.output_formatter.print_error("API密钥设置失败")
            return False
        
        # 步骤2: 初始化客户端
        self.output_formatter.print_section("步骤 2: 初始化客户端")
        if not self.initialize_client():
            self.output_formatter.print_error("客户端初始化失败")
            return False
        
        # 步骤3: 获取模型
        self.output_formatter.print_section("步骤 3: 获取模型")
        if not self.fetch_models():
            self.output_formatter.print_error("获取模型失败")
            return False
        
        # 步骤4: 选择模型
        self.output_formatter.print_section("步骤 4: 选择模型")
        if not self.select_model():
            self.output_formatter.print_warning("未选择模型，稍后可以手动选择")
        
        # 步骤5: 完成设置
        self.output_formatter.print_section("设置完成")
        self.output_formatter.print_success("设置向导完成!")
        
        # 询问下一步操作
        next_actions = ["开始聊天", "查询余额", "进入交互模式", "退出"]
        choice_index = self.input_handler.get_choice_input("请选择下一步操作:", next_actions)
        
        if choice_index == 0:  # 开始聊天
            if self.selected_model:
                self.start_chat()
            else:
                self.output_formatter.print_error("请先选择模型")
        elif choice_index == 1:  # 查询余额
            self.query_balance()
        elif choice_index == 2:  # 进入交互模式
            self.run_interactive_mode()
        # choice_index == 3 或 None: 退出
        
        return True
    
    def run(self, guided_mode=False):
        """
        运行CLI客户端
        
        Args:
            guided_mode (bool): 是否使用引导模式
        """
        try:
            if guided_mode:
                self.run_guided_setup()
            else:
                # 快速模式：加载API密钥和初始化客户端
                if self.load_api_key() and self.initialize_client():
                    self.run_interactive_mode()
                else:
                    self.output_formatter.print_error("初始化失败")
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
        except Exception as e:
            self.output_formatter.print_error(f"程序运行时发生错误: {e}")

# 便捷函数
def create_cli_client():
    """
    创建CLI客户端的便捷函数
    
    Returns:
        DeepSeekCLI: CLI客户端实例
    """
    return DeepSeekCLI()

def run_cli_with_args(args):
    """
    根据命令行参数运行CLI
    
    Args:
        args (list): 命令行参数列表
    """
    cli = create_cli_client()
    
    # 解析命令行参数
    guided_mode = "--guided" in args or "--setup" in args
    
    if "--help" in args or "-h" in args:
        print(f"""
{cli.app_name} {cli.app_version}

用法: python cli_client.py [选项]

选项:
  --guided, --setup    使用引导式设置
  --help, -h          显示此帮助信息
  --version, -v       显示版本信息

示例:
  python cli_client.py              # 快速模式
  python cli_client.py --guided     # 引导模式
        """)
        return
    
    if "--version" in args or "-v" in args:
        print(f"{cli.app_name} {cli.app_version}")
        return
    
    # 运行CLI
    cli.run(guided_mode=guided_mode)

# CLI专用的快捷命令
def quick_chat(api_key=None, model=None):
    """
    快速聊天函数
    
    Args:
        api_key (str): API密钥，如果为None则从文件加载或提示输入
        model (str): 模型名称，如果为None则提示选择
    """
    cli = create_cli_client()
    
    # 设置API密钥
    if api_key:
        cli.api_key = api_key
    elif not cli.load_api_key():
        return
    
    # 初始化客户端
    if not cli.initialize_client():
        return
    
    # 获取模型
    if not cli.fetch_models():
        return
    
    # 选择模型
    if model and model in cli.available_models:
        cli.selected_model = model
        cli.output_formatter.print_success(f"已选择模型: {model}")
    elif not cli.select_model():
        return
    
    # 开始聊天
    cli.start_chat()

def quick_balance(api_key=None):
    """
    快速余额查询函数
    
    Args:
        api_key (str): API密钥，如果为None则从文件加载或提示输入
    """
    cli = create_cli_client()
    
    # 设置API密钥
    if api_key:
        cli.api_key = api_key
    elif not cli.load_api_key():
        return
    
    # 查询余额
    cli.query_balance()

# 测试和示例代码
if __name__ == "__main__":
    # 如果直接运行此文件，根据命令行参数执行
    run_cli_with_args(sys.argv[1:])