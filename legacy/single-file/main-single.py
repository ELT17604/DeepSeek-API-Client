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
import sys
import json
import requests
import threading
import subprocess
import time
import base64
import hashlib

# 判断是否需要导入tkinter
USE_GUI = "--gui" in sys.argv or (not "--cli" in sys.argv)

if USE_GUI:
    import tkinter as tk
    from tkinter import messagebox, simpledialog, scrolledtext
    # 导入加密需要的库
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        print("cryptography库未安装，API Key将无法加密。请使用 pip install cryptography 安装。")
        # 继续执行，但加密功能将降级

from openai import OpenAI

DEEPSEEK_API_BASE_URL_V1 = "https://api.deepseek.com/v1"
DEEPSEEK_BALANCE_URL = "https://api.deepseek.com/user/balance"
API_KEY_FILENAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key")  # API Key 存储文件名

# ===================== API Key 存储加密功能 =====================
def get_encryption_key():
    """基于机器特定信息生成稳定的加密密钥"""
    try:
        # 使用机器ID作为密钥材料的一部分
        import uuid
        machine_id = uuid.getnode()
        # 使用固定的盐值和机器ID创建密钥材料
        key_material = f"deepseek-client-{machine_id}-salt-v1".encode()
        # 生成符合Fernet要求的32字节密钥并进行base64编码
        key = base64.urlsafe_b64encode(hashlib.sha256(key_material).digest())
        return key
    except Exception:
        # 如果出错，使用一个默认密钥（这不够安全，但比没有加密好）
        return base64.urlsafe_b64encode(hashlib.sha256(b"default-salt-key").digest())

def encrypt_api_key(api_key):
    """加密API密钥"""
    if not api_key:
        return None
    try:
        key = get_encryption_key()
        f = Fernet(key)
        return f.encrypt(api_key.encode()).decode()
    except Exception as e:
        print(f"加密API密钥时出错: {e}")
        return None

def decrypt_api_key(encrypted_api_key):
    """解密API密钥"""
    if not encrypted_api_key:
        return None
    try:
        key = get_encryption_key()
        f = Fernet(key)
        return f.decrypt(encrypted_api_key.encode()).decode()
    except Exception as e:
        print(f"解密API密钥时出错: {e}")
        return None

def save_api_key_to_file(api_key):
    """将API密钥加密后保存到文件"""
    try:
        encrypted = encrypt_api_key(api_key)
        if encrypted:
            with open(API_KEY_FILENAME, "w") as f:
                f.write(encrypted)
            return True
        return False
    except Exception as e:
        print(f"保存API密钥时出错: {e}")
        return False

def load_api_key_from_file():
    """从文件加载并解密API密钥"""
    try:
        if os.path.exists(API_KEY_FILENAME):
            with open(API_KEY_FILENAME, "r") as f:
                encrypted = f.read().strip()
                return decrypt_api_key(encrypted)
        return None
    except Exception as e:
        print(f"加载API密钥时出错: {e}")
        return None

def delete_api_key_file():
    """删除存储API密钥的文件"""
    if os.path.exists(API_KEY_FILENAME):
        try:
            os.remove(API_KEY_FILENAME)
            return True
        except Exception as e:
            print(f"删除API密钥文件时出错: {e}")
            return False
    return True

# ===================== GUI 部分 =====================
if USE_GUI:
    class StatusIndicator(tk.Frame):
        """状态指示器控件，每行显示状态文本和一个彩色指示灯"""
        def __init__(self, master, label_text, **kwargs):
            super().__init__(master, **kwargs)
            self.label_text = label_text
            self.status_var = tk.StringVar(value=label_text)
            self.label = tk.Label(self, textvariable=self.status_var, anchor="w", width=38)
            self.label.pack(side=tk.LEFT, padx=(2, 0))
            self.canvas = tk.Canvas(self, width=16, height=16, highlightthickness=0)
            self.canvas.pack(side=tk.LEFT, padx=2)
            self.indicator = self.canvas.create_oval(2, 2, 14, 14, fill="gray", outline="black")

        def set_status(self, text, color):
            """设置状态文本和指示灯颜色"""
            self.status_var.set(f"{self.label_text}: {text}")
            self.canvas.itemconfig(self.indicator, fill=color)

    class DeepSeekGUI:
        def __init__(self, master):
            self.master = master
            master.title("DeepSeek API Client GUI")

            self.api_key = ""
            self.client = None
            self.selected_model = None
            self.messages = []

            # 独立状态指示器窗口
            self.status_window = tk.Toplevel(master)
            self.status_window.title("Status Panel")
            self.status_window.geometry("350x160")
            self.status_window.resizable(False, False)
            self.status_window.protocol("WM_DELETE_WINDOW", lambda: self.status_window.withdraw())  # 关闭时隐藏
            self.status_window.attributes("-topmost", True)  # 始终置顶

            # 状态指示窗口内容
            self.status_frame = tk.LabelFrame(self.status_window, text="Status Panel", padx=4, pady=2)
            self.status_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=4)

            # 五个状态指示器
            self.status_client = StatusIndicator(self.status_frame, "Client Init")
            self.status_client.pack(anchor="w")
            self.status_network = StatusIndicator(self.status_frame, "Network")
            self.status_network.pack(anchor="w")
            self.status_model = StatusIndicator(self.status_frame, "Model Select")
            self.status_model.pack(anchor="w")
            self.status_http = StatusIndicator(self.status_frame, "HTTP Error")
            self.status_http.pack(anchor="w")
            self.status_chat = StatusIndicator(self.status_frame, "Chat Service")
            self.status_chat.pack(anchor="w")

            # 主窗口其余内容
            self.footer_label = tk.Label(
                master,
                text="DeepSeek API Client GUI v0.6.1 © 2025 ELT Group",
                font=("Arial", 8),
                fg="gray"
            )
            self.footer_label.pack(side=tk.BOTTOM, pady=(0, 3))

            # API Key输入栏
            self.api_key_entry = tk.Entry(master, width=60, show="")
            self.api_key_entry.pack(side=tk.BOTTOM, fill=tk.X)
            
            # 尝试从文件中加载API Key
            saved_api_key = load_api_key_from_file()
            if saved_api_key:
                self.api_key_entry.insert(0, saved_api_key)
                self.api_key_entry.config(fg="black")
            else:
                self.api_key_entry.insert(0, "API KEY HERE")
                self.api_key_entry.config(fg="gray")

            def on_entry_click(event):
                if self.api_key_entry.get() == "API KEY HERE":
                    self.api_key_entry.delete(0, tk.END)
                    self.api_key_entry.config(fg="black")
            def on_focusout(event):
                if not self.api_key_entry.get():
                    self.api_key_entry.insert(0, "API KEY HERE")
                    self.api_key_entry.config(fg="gray")

            self.api_key_entry.bind('<FocusIn>', on_entry_click)
            self.api_key_entry.bind('<FocusOut>', on_focusout)

            self.api_key_masked_label = tk.Label(master, text="", font=("Arial", 10), fg="gray")
            self.api_key_masked_label.pack(side=tk.BOTTOM)
            self.api_key_masked_label.pack_forget()

            self.button_frame = tk.Frame(master)
            self.button_frame.pack(side=tk.BOTTOM, pady=2)

            self.init_btn = tk.Button(self.button_frame, text="Initialize Client", command=self.initialize_client, state=tk.NORMAL)
            self.init_btn.pack(side=tk.LEFT, padx=5)

            self.clear_apikey_btn = tk.Button(self.button_frame, text="Remove API Key", command=self.clear_api_key, 
                                             state=tk.DISABLED if not saved_api_key else tk.NORMAL)
            self.clear_apikey_btn.pack(side=tk.LEFT, padx=5)

            self.model_btn = tk.Button(master, text="List and Select Model", command=self.list_and_select_model)
            self.model_btn.pack(pady=2)

            self.balance_btn = tk.Button(master, text="Query Account Balance", command=self.query_balance)
            self.balance_btn.pack(pady=2)

            self.chat_btn = tk.Button(master, text="Start Chat", command=self.start_chat)
            self.chat_btn.pack(pady=2)

            self.clear_btn = tk.Button(master, text="Clear Output", command=self.clear_output)
            self.clear_btn.pack(pady=2)

            self.output = scrolledtext.ScrolledText(master, width=80, height=20, state='normal')
            self.output.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

            # 用户输入区
            self.input_frame = tk.Frame(master)
            self.input_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 2))

            self.input_label = tk.Label(self.input_frame, text="You:", font=("Arial", 10))
            self.input_label.pack(side=tk.LEFT, anchor="s", pady=2)

            self.user_input = tk.Text(self.input_frame, height=3, wrap="word", state=tk.DISABLED)
            self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
            self.user_input.bind("<KeyRelease>", self.on_input_change)
            self.user_input.bind("<Return>", self.send_user_input)
            self.user_input.bind("<Control-Return>", lambda e: self.user_input.insert(tk.INSERT, "\n"))

            self.input_btn_frame = tk.Frame(master)
            self.input_btn_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 4))

            self.btn_spacer = tk.Label(self.input_btn_frame)
            self.btn_spacer.pack(side=tk.LEFT, fill=tk.X, expand=True)

            self.send_btn = tk.Button(self.input_btn_frame, text="Send", command=self.send_user_input, state=tk.DISABLED)
            self.send_btn.pack(side=tk.RIGHT, padx=(8, 0))

            self.new_btn = tk.Button(self.input_btn_frame, text="New Session", command=self.start_new_session, state=tk.DISABLED)
            self.new_btn.pack(side=tk.RIGHT, padx=(8, 0))

            self.end_btn = tk.Button(self.input_btn_frame, text="End Chat", command=self.end_chat, state=tk.NORMAL)
            self.end_btn.pack(side=tk.RIGHT, padx=(8, 0))

            # 初始化状态
            self.update_client_status()
            self.update_network_status()
            self.update_model_status()
            self.update_http_status()
            self.update_chat_status("not_ready")

            # 启动网络状态定时刷新线程
            self.network_thread_stop = False
            self.network_thread = threading.Thread(target=self.network_status_loop, daemon=True)
            self.network_thread.start()

        def disable_copy(self, event):
            return "break"

        def print_out(self, text):
            self.output.insert(tk.END, text + "\n")
            self.output.see(tk.END)

        def clear_output(self):
            self.output.delete(1.0, tk.END)

        def initialize_client(self):
            api_key = self.api_key_entry.get().strip()
            if not api_key:
                messagebox.showerror("Error", "Please enter your API Key.")
                self.update_client_status()
                return
            try:
                self.client = OpenAI(api_key=api_key, base_url=DEEPSEEK_API_BASE_URL_V1)
                self.api_key = api_key
                self.print_out("Client initialized successfully.")
                
                # 保存API Key到加密文件
                if save_api_key_to_file(api_key):
                    self.print_out("API Key已安全加密保存到本地。")
                else:
                    self.print_out("注意：无法保存API Key到本地文件。")

                masked = "*" * len(api_key)
                self.api_key_masked_label.config(text=f"API Key: {masked}")
                self.api_key_masked_label.pack()
                self.api_key_entry.pack_forget()
                self.api_key_masked_label.bind("<Button-3>", self.disable_copy)
                self.api_key_masked_label.bind("<Control-c>", self.disable_copy)
                self.api_key_masked_label.bind("<Control-Insert>", self.disable_copy)
                self.clear_apikey_btn.config(state=tk.NORMAL)
                self.init_btn.config(state=tk.DISABLED)
                self.update_client_status()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize client: {e}")
                self.update_client_status()

        def clear_api_key(self):
            result = delete_api_key_file()
            if result:
                self.print_out("API Key已从本地文件移除。")
            else:
                self.print_out("无法删除API Key文件。")
                
            self.api_key = ""
            self.client = None
            self.selected_model = None
            self.messages = []
            self.api_key_masked_label.pack_forget()
            self.api_key_entry.pack()
            self.api_key_entry.delete(0, tk.END)
            self.clear_apikey_btn.config(state=tk.DISABLED)
            self.init_btn.config(state=tk.NORMAL)
            self.print_out("API Key cleared. Please enter a new API Key and initialize the client.")
            self.update_client_status()
            self.update_model_status()
            self.update_chat_status("not_ready")

        def list_and_select_model(self):
            if not self.client:
                messagebox.showerror("Error", "Please initialize the client first.")
                self.update_model_status()
                return
            try:
                self.print_out("Fetching model list...")
                models_response = self.client.models.list()
                available_models = [model.id for model in models_response.data if
                                    "chat" in model.id.lower() or "coder" in model.id.lower() or len(models_response.data) < 10]
                if not available_models:
                    available_models = [model.id for model in models_response.data]
                if not available_models:
                    self.update_model_status("fetch_fail")
                    manual_model = simpledialog.askstring("Enter Model Name", "No models found. Please enter model name (e.g., deepseek-chat):")
                    if manual_model:
                        self.selected_model = manual_model
                        self.print_out(f"Model selected manually: {manual_model}")
                        self.update_model_status()
                    else:
                        self.print_out("No model selected.")
                        self.update_model_status()
                    return
                model_choice = simpledialog.askinteger(
                    "Select Model",
                    "Available models:\n" + "\n".join([f"{i+1}. {mid}" for i, mid in enumerate(available_models)]) +
                    f"\nEnter number (1-{len(available_models)}):"
                )
                if model_choice and 1 <= model_choice <= len(available_models):
                    self.selected_model = available_models[model_choice-1]
                    self.print_out(f"Model selected: {self.selected_model}")
                    self.update_model_status()
                else:
                    self.print_out("No model selected.")
                    self.update_model_status()
            except Exception as e:
                self.update_model_status("fetch_fail")
                manual_model = simpledialog.askstring("Enter Model Name", f"Failed to fetch models: {e}\nYou can enter model name manually (e.g., deepseek-chat):")
                if manual_model:
                    self.selected_model = manual_model
                    self.print_out(f"Model selected manually: {manual_model}")
                    self.update_model_status()
                else:
                    self.update_model_status("fetch_fail")

        def query_balance(self):
            if not self.api_key:
                messagebox.showerror("Error", "Please initialize the client first.")
                return
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json"
            }
            try:
                self.print_out("Querying account balance...")
                response = requests.get(DEEPSEEK_BALANCE_URL, headers=headers)
                self.update_http_status(response.status_code)
                response.raise_for_status()
                balance_data = response.json()
                if balance_data.get("is_available", False):
                    self.print_out("Service available.")
                    balance_infos_list = balance_data.get("balance_infos", [])
                    if balance_infos_list:
                        for idx, info in enumerate(balance_infos_list):
                            self.print_out(f"Balance Info #{idx+1}:")
                            self.print_out(f"  Currency: {info.get('currency', 'N/A')}")
                            self.print_out(f"  Total Balance: {info.get('total_balance', 'N/A')}")
                            self.print_out(f"  Granted Balance: {info.get('granted_balance', 'N/A')}")
                            self.print_out(f"  Topped-up Balance: {info.get('topped_up_balance', 'N/A')}")
                    else:
                        self.print_out("No detailed balance information found.")
                else:
                    self.print_out("Service not available.")
                    if "message" in balance_data:
                        self.print_out(f"API Message: {balance_data['message']}")
                    elif not balance_data.get("balance_infos") and not balance_data.get("is_available", True):
                        self.print_out("Possibly due to service unavailability or no balance info.")
            except requests.exceptions.HTTPError as http_err:
                code = http_err.response.status_code if http_err.response is not None else None
                self.update_http_status(code)
                self.print_out(f"HTTP error: {http_err}")
                if http_err.response is not None:
                    self.print_out(f"Status code: {http_err.response.status_code}")
                    try:
                        error_details = http_err.response.json()
                        self.print_out(f"Error details: {json.dumps(error_details, indent=2, ensure_ascii=False)}")
                    except json.JSONDecodeError:
                        self.print_out(f"Response content: {http_err.response.text}")
            except requests.exceptions.RequestException as e:
                self.update_http_status(0)
                self.print_out(f"Request failed: {e}")
            except json.JSONDecodeError:
                self.update_http_status(0)
                self.print_out("Balance response is not valid JSON.")
            except Exception as e:
                self.update_http_status(0)
                self.print_out(f"Unknown error: {e}")

        def start_chat(self):
            if not self.client:
                self.print_out("Please initialize the client first.")
                self.update_chat_status("not_ready")
                self.user_input.config(state=tk.DISABLED)
                self.update_buttons_state()
                return
            if not self.selected_model:
                self.print_out("Please select a model first.")
                self.update_chat_status("not_ready")
                self.user_input.config(state=tk.DISABLED)
                self.update_buttons_state()
                return
            self.print_out(f"\nStarting chat with model '{self.selected_model}' (Enter to send, Ctrl+Enter for newline)")
            self.messages = []
            self.user_input.config(state=tk.NORMAL)
            self.user_input.delete("1.0", tk.END)
            self.user_input.focus_set()
            self.update_chat_status("ready")
            self.update_buttons_state()

        def send_user_input(self, event=None):
            if self.user_input["state"] != tk.NORMAL:
                return "break"
            if event and (event.state & 0x0004 or event.state & 0x0001):  # Ctrl或Shift
                return
            text = self.user_input.get("1.0", tk.END).strip()
            if text:
                self.handle_user_input(text)
                self.user_input.delete("1.0", tk.END)
                self.send_btn.config(state=tk.DISABLED)
            return "break"

        def handle_user_input(self, text):
            if not self.client:
                self.print_out("Please initialize the client first.")
                self.update_chat_status("not_ready")
                self.user_input.config(state=tk.DISABLED)
                self.update_buttons_state()
                return
            if not self.selected_model:
                self.print_out("Please select a model first.")
                self.update_chat_status("not_ready")
                self.user_input.config(state=tk.DISABLED)
                self.update_buttons_state()
                return
            self.user_input.config(state=tk.NORMAL)
            self.messages.append({"role": "user", "content": text})
            self.print_out(f"You: {text}")
            self.update_buttons_state()
            try:
                self.print_out("Model: ")
                assistant_response_content = ""
                self.update_chat_status("streaming")
                stream = self.client.chat.completions.create(
                    model=self.selected_model,
                    messages=self.messages,
                    stream=True,
                    max_tokens=2048,
                    temperature=1.1
                )
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        content_piece = chunk.choices[0].delta.content
                        self.output.insert(tk.END, content_piece)
                        self.output.see(tk.END)
                        self.master.update_idletasks()
                        assistant_response_content += content_piece
                self.print_out("")
                if assistant_response_content:
                    self.messages.append({"role": "assistant", "content": assistant_response_content})
                self.update_chat_status("ready")
                self.user_input.config(state=tk.NORMAL)
                self.user_input.focus_set()
                self.update_buttons_state()
            except Exception as e:
                self.print_out(f"\nChat error: {e}")
                if "Incorrect API key" in str(e) or "authentication" in str(e).lower():
                    self.print_out("Please check if your API Key is correct.")
                self.print_out("You can retry or type /exit or /new.")
                self.update_chat_status("not_ready")
                self.user_input.config(state=tk.NORMAL)
                self.update_buttons_state()

        def on_input_change(self, event=None):
            content = self.user_input.get("1.0", tk.END).strip()
            if content and self.user_input["state"] == tk.NORMAL:
                self.send_btn.config(state=tk.NORMAL)
            else:
                self.send_btn.config(state=tk.DISABLED)

        def update_buttons_state(self):
            content = self.user_input.get("1.0", tk.END).strip()
            if self.user_input["state"] == tk.NORMAL and content:
                self.send_btn.config(state=tk.NORMAL)
            else:
                self.send_btn.config(state=tk.DISABLED)
            self.end_btn.config(state=tk.NORMAL)
            if self.messages:
                self.new_btn.config(state=tk.NORMAL)
            else:
                self.new_btn.config(state=tk.DISABLED)

        def end_chat(self):
            self.print_out("Chat ended.")
            self.update_chat_status("not_ready")
            self.user_input.delete("1.0", tk.END)
            if not self.client:
                self.user_input.config(state=tk.DISABLED)
            else:
                self.user_input.config(state=tk.NORMAL)
            self.update_buttons_state()

        def start_new_session(self):
            self.print_out("New session started.")
            self.messages = []
            self.user_input.delete("1.0", tk.END)
            self.user_input.config(state=tk.NORMAL)
            self.user_input.focus_set()
            self.update_chat_status("ready")
            self.update_buttons_state()

        def update_client_status(self):
            if not self.api_key_entry.get().strip() or self.api_key_entry.get().strip() == "API KEY HERE":
                self.status_client.set_status("No API Key", "red")
            elif self.client is None:
                self.status_client.set_status("API Key entered", "yellow")
            else:
                self.status_client.set_status("Initialized", "green")

        def update_network_status(self, latency=None, status=None):
            if status == "fail":
                self.status_network.set_status("Unreachable", "red")
            elif latency is not None:
                if latency < 200:
                    self.status_network.set_status(f"OK ({latency} ms)", "green")
                elif latency < 600:
                    self.status_network.set_status(f"High latency ({latency} ms)", "yellow")
                else:
                    self.status_network.set_status(f"Very high latency ({latency} ms)", "yellow")
            else:
                self.status_network.set_status("Checking...", "gray")

        def update_model_status(self, error=None):
            if error == "fetch_fail":
                self.status_model.set_status("Failed to fetch", "yellow")
            elif self.selected_model:
                self.status_model.set_status(f"Selected ({self.selected_model})", "green")
            else:
                self.status_model.set_status("Not selected", "red")

        def update_http_status(self, code=None):
            if code is None:
                self.status_http.set_status("OK", "green")
            elif 400 <= code <= 499:
                self.status_http.set_status(f"Client Error ({code})", "red")
            elif 500 <= code <= 599:
                self.status_http.set_status(f"Server Error ({code})", "yellow")
            else:
                self.status_http.set_status(f"OK ({code})", "green")

        def update_chat_status(self, state):
            if state == "not_ready":
                self.status_chat.set_status("Not ready", "red")
            elif state == "streaming":
                self.status_chat.set_status("Streaming...", "yellow")
            elif state == "ready":
                self.status_chat.set_status("Ready", "green")
            else:
                self.status_chat.set_status("Unknown", "gray")

        def network_status_loop(self):
            while not self.network_thread_stop:
                latency = None
                status = None
                try:
                    import urllib.parse
                    url = urllib.parse.urlparse(DEEPSEEK_API_BASE_URL_V1)
                    host = url.hostname
                    result = subprocess.run(
                        ["ping", "-n", "1", "-w", "1000", host],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    if result.returncode == 0:
                        for line in result.stdout.splitlines():
                            if "平均" in line or "Average" in line:
                                ms = [int(s.replace("ms", "").replace("毫秒", "").strip()) for s in line.split() if s.replace("ms", "").replace("毫秒", "").strip().isdigit()]
                                if ms:
                                    latency = ms[-1]
                                    break
                            elif "TTL=" in line and "time=" in line:
                                idx = line.find("time=")
                                if idx != -1:
                                    time_part = line[idx+5:].split()[0]
                                    latency = int(time_part.replace("ms", ""))
                                    break
                        if latency is None:
                            latency = 0
                    else:
                        status = "fail"
                except Exception:
                    status = "fail"
                self.master.after(0, self.update_network_status, latency, status)
                time.sleep(5)

# ===================== CLI 部分 =====================
def get_api_key():
    # 首先尝试从文件加载
    saved_api_key = load_api_key_from_file()
    if saved_api_key:
        print(f"已从本地文件加载API Key (已加密保存)")
        use_saved = input("是否使用已保存的API Key? (y/n): ").lower().strip()
        if use_saved == 'y' or use_saved == '':
            return saved_api_key
    
    api_key = input("Enter your DeepSeek API Key: ").strip()
    while not api_key:
        print("API Key cannot be empty.")
        api_key = input("Enter your DeepSeek API Key: ").strip()
    
    # 询问是否保存API Key
    save_key = input("是否保存API Key到本地文件? (y/n): ").lower().strip()
    if save_key == 'y' or save_key == '':
        if save_api_key_to_file(api_key):
            print("API Key已安全加密并保存到本地文件。")
        else:
            print("保存API Key失败。")
    
    return api_key

def initialize_client(api_key):
    try:
        return OpenAI(api_key=api_key, base_url=DEEPSEEK_API_BASE_URL_V1)
    except Exception as e:
        print(f"Client initialization failed: {e}")
        return None

def list_and_select_model(client):
    if not client:
        print("Client not initialized.")
        return None
    try:
        print("\nFetching available models...")
        models_response = client.models.list()
        available_models = [model.id for model in models_response.data if
                            "chat" in model.id.lower() or "coder" in model.id.lower() or len(models_response.data) < 10]
        if not available_models:
            available_models = [model.id for model in models_response.data]
        if not available_models:
            print("Failed to fetch model list. Check API key and connection.")
            manual_model = input("Enter model name (e.g., deepseek-chat): ")
            return manual_model if manual_model else None
        print("Available models:")
        for i, model_id in enumerate(available_models):
            print(f"{i + 1}. {model_id}")
        while True:
            try:
                choice_input = input(f"Select a model by number 1-{len(available_models)}: ")
                if not choice_input:
                    print("No model selected, using last selected or default.")
                    return None
                choice = int(choice_input)
                if 1 <= choice <= len(available_models):
                    selected_model = available_models[choice - 1]
                    print(f"Model selected: {selected_model}")
                    return selected_model
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Please enter a number.")
    except Exception as e:
        print(f"Failed to fetch model list: {e}")
        manual_model = input("Enter model name (leave blank to cancel): ")
        return manual_model if manual_model else None

def query_balance(api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    try:
        print("\nQuerying account balance...")
        response = requests.get(DEEPSEEK_BALANCE_URL, headers=headers)
        response.raise_for_status()
        balance_data = response.json()
        print("Account Balance Information:")
        if balance_data.get("is_available", False):
            print("  Service Available: Yes")
            balance_infos_list = balance_data.get("balance_infos", [])
            if balance_infos_list:
                for idx, info in enumerate(balance_infos_list):
                    print(f"\n  Balance Info #{idx + 1}:")
                    print(f"    Currency: {info.get('currency', 'N/A')}")
                    print(f"    Total Balance: {info.get('total_balance', 'N/A')}")
                    print(f"    Granted Balance: {info.get('granted_balance', 'N/A')}")
                    print(f"    Topped-up Balance: {info.get('topped_up_balance', 'N/A')}")
            else:
                print("  Could not retrieve detailed balance entries.")
        else:
            print("  Service Available: No")
            if "message" in balance_data:
                print(f"  API Message: {balance_data['message']}")
            elif not balance_data.get("balance_infos") and not balance_data.get("is_available", True):
                print("  Possibly due to service unavailability or no balance info.")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred while querying balance: {http_err}")
        if http_err.response is not None:
            print(f"Response status code: {http_err.response.status_code}")
            try:
                error_details = http_err.response.json()
                print(f"Error details: {json.dumps(error_details, indent=2)}")
            except json.JSONDecodeError:
                print(f"Response content: {http_err.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to query balance: {e}")
    except json.JSONDecodeError:
        error_response_text = "N/A"
        response = 'null'
        if 'response' in locals() and hasattr(response, 'text'):
            error_response_text = response.text
        print(f"Failed to parse balance response, not valid JSON:\n{error_response_text}")
    except Exception as e:
        print(f"Unknown error occurred while querying balance: {e}")

def stream_chat(client, model_id):
    if not client:
        print("Client not initialized.")
        return
    if not model_id or model_id == 'null':
        print("No model selected. Please choose a model first.")
        return
    print(f"\nStarting chat with model '{model_id}' (type '/exit' to end, '/new' for a new conversation)...")
    messages = []
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() == '/exit':
                print("Ending conversation.")
                break
            if user_input.lower() == '/new':
                print("Starting new conversation...")
                messages = []
                continue
            messages.append({"role": "user", "content": user_input})
            print("Model: ", end="", flush=True)
            assistant_response_content = ""
            stream = client.chat.completions.create(
                model=model_id,
                messages=messages,
                stream=True,
                max_tokens=2048,
                temperature=1.1
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    content_piece = chunk.choices[0].delta.content
                    print(content_piece, end="", flush=True)
                    assistant_response_content += content_piece
            print()
            if assistant_response_content:
                messages.append({"role": "assistant", "content": assistant_response_content})
        except Exception as e:
            print(f"\nError during chat: {e}")
            if "Incorrect API key" in str(e) or "authentication" in str(e).lower():
                print("Please check if your API key is correct.")
            print("Try again or type '/exit' or '/new'.")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main_cli():
    print("DeepSeek API client Version 0.2.1")
    api_key = get_api_key()
    if not api_key:
        print("No API key provided, exiting.")
        return
    client = initialize_client(api_key)
    if not client:
        return
    selected_model = None
    print(f"Default model set to: {selected_model}")
    while True:
        clear_screen()
        print("\nPlease select an option:")
        print("1. List and select model")
        print("2. Query account balance")
        print(f"3. Start chat (Current model: {selected_model})")
        print("4. Exit")
        choice = input("Enter your choice (1-4): ")
        if choice == '1':
            clear_screen()
            new_model = list_and_select_model(client)
            if new_model:
                selected_model = new_model
        elif choice == '2':
            clear_screen()
            query_balance(api_key)
            input("\nPress any key to return to the main menu...")
            clear_screen()
        elif choice == '3':
            if not selected_model:
                clear_screen()
                print("Please select a model first (option 1).")
                new_model = list_and_select_model(client)
                if new_model:
                    selected_model = new_model
                else:
                    print("Cannot start chat, no model selected.")
                    continue
            stream_chat(client, selected_model)
        elif choice == '4':
            break
        elif choice == '/clear':
            clear_screen()
        else:
            clear_screen()
            print("[error] Invalid option, please try again.")

def main():
    if USE_GUI:
        root = tk.Tk()
        app = DeepSeekGUI(root)
        root.mainloop()
    else:
        main_cli()

if __name__ == "__main__":
    main()