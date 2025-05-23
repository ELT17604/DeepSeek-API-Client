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
import json
import requests
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
from openai import OpenAI
import threading
import subprocess
import time

DEEPSEEK_API_BASE_URL_V1 = "https://api.deepseek.com/v1"
DEEPSEEK_BALANCE_URL = "https://api.deepseek.com/user/balance"

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

        # 状态指示窗口
        self.status_frame = tk.LabelFrame(master, text="Status Panel", padx=4, pady=2)
        self.status_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=4)

        # 新增：五个状态指示器
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

        # Copyright and version info (small font)
        self.footer_label = tk.Label(
            master,
            text="DeepSeek API Client GUI v0.2.1 © 2025 ELT Group",
            font=("Arial", 8),
            fg="gray"
        )
        self.footer_label.pack(side=tk.BOTTOM, pady=(0, 3))

        # API Key输入和星号显示都放在底部
        self.api_key_entry = tk.Entry(master, width=60, show="")
        self.api_key_entry.pack(side=tk.BOTTOM)
        self.api_key_entry.insert(0, "")  # 保留原有插入空字符串

        # 新增：输入提示
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

        # 按钮并排放置
        self.button_frame = tk.Frame(master)
        self.button_frame.pack(side=tk.BOTTOM, pady=2)

        self.init_btn = tk.Button(self.button_frame, text="Initialize Client", command=self.initialize_client, state=tk.NORMAL)
        self.init_btn.pack(side=tk.LEFT, padx=5)

        self.clear_apikey_btn = tk.Button(self.button_frame, text="Clear API Key", command=self.clear_api_key, state=tk.DISABLED)
        self.clear_apikey_btn.pack(side=tk.LEFT, padx=5)

        self.model_btn = tk.Button(master, text="List and Select Model", command=self.list_and_select_model)
        self.model_btn.pack(pady=2)

        self.balance_btn = tk.Button(master, text="Query Account Balance", command=self.query_balance)
        self.balance_btn.pack(pady=2)

        self.chat_btn = tk.Button(master, text="Start Chat", command=self.start_chat)
        self.chat_btn.pack(pady=2)

        self.clear_btn = tk.Button(master, text="Clear Output", command=self.clear_output)
        self.clear_btn.pack(pady=2)

        # 输出区域自适应窗口大小，全部用 pack
        self.output = scrolledtext.ScrolledText(master, width=80, height=20, state='normal')
        self.output.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        # 初始化状态（必须放在所有控件初始化后）
        self.update_client_status()
        self.update_network_status()
        self.update_model_status()
        self.update_http_status()
        self.update_chat_status("not_ready")

        # 启动网络状态定时刷新线程
        self.network_thread_stop = False
        self.network_thread = threading.Thread(target=self.network_status_loop, daemon=True)
        self.network_thread.start()

    # 新增：防止复制API Key标签内容
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

            # 显示星号API Key，隐藏输入框
            masked = "*" * len(api_key)
            self.api_key_masked_label.config(text=f"API Key: {masked}")
            self.api_key_masked_label.pack()
            self.api_key_entry.pack_forget()
            # 禁止复制
            self.api_key_masked_label.bind("<Button-3>", self.disable_copy)
            self.api_key_masked_label.bind("<Control-c>", self.disable_copy)
            self.api_key_masked_label.bind("<Control-Insert>", self.disable_copy)
            # 启用清除按钮，禁用初始化按钮
            self.clear_apikey_btn.config(state=tk.NORMAL)
            self.init_btn.config(state=tk.DISABLED)
            self.update_client_status()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize client: {e}")
            self.update_client_status()

    # 新增：清除API Key功能
    def clear_api_key(self):
        self.api_key = ""
        self.client = None
        self.selected_model = None
        self.messages = []
        # 隐藏星号标签，显示输入框
        self.api_key_masked_label.pack_forget()
        self.api_key_entry.pack()
        self.api_key_entry.delete(0, tk.END)
        # 禁用清除按钮，启用初始化按钮
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
            messagebox.showerror("Error", "Please initialize the client first.")
            self.update_chat_status("not_ready")
            return
        if not self.selected_model:
            messagebox.showerror("Error", "Please select a model first.")
            self.update_chat_status("not_ready")
            return
        self.print_out(f"\nStarting chat with model '{self.selected_model}' (type /exit to end, /new for new session)")
        self.messages = []
        self.update_chat_status("ready")
        while True:
            user_input = simpledialog.askstring("You", "You:")
            if user_input is None:
                self.print_out("Chat cancelled.")
                self.update_chat_status("not_ready")
                break
            if user_input.lower() == '/exit':
                self.print_out("Chat ended.")
                self.update_chat_status("not_ready")
                break
            if user_input.lower() == '/new':
                self.print_out("New session started.")
                self.messages = []
                self.update_chat_status("ready")
                continue
            self.messages.append({"role": "user", "content": user_input})
            self.print_out(f"You: {user_input}")
            try:
                self.print_out("Model: ",)
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
                        self.master.update_idletasks()  # Force GUI refresh for streaming
                        assistant_response_content += content_piece
                self.print_out("")  # New line
                if assistant_response_content:
                    self.messages.append({"role": "assistant", "content": assistant_response_content})
                self.update_chat_status("ready")
            except Exception as e:
                self.print_out(f"\nChat error: {e}")
                if "Incorrect API key" in str(e) or "authentication" in str(e).lower():
                    self.print_out("Please check if your API Key is correct.")
                self.print_out("You can retry or type /exit or /new.")
                self.update_chat_status("not_ready")

    # 新增：客户端初始化状态更新
    def update_client_status(self):
        # 红色：无API Key，黄色：有API Key未初始化，绿色：已初始化
        if not self.api_key_entry.get().strip() or self.api_key_entry.get().strip() == "API KEY HERE":
            self.status_client.set_status("No API Key", "red")
        elif self.client is None:
            self.status_client.set_status("API Key entered", "yellow")
        else:
            self.status_client.set_status("Initialized", "green")

    # 新增：网络状态更新（ping）
    def update_network_status(self, latency=None, status=None):
        # 绿色：正常，黄色：高延迟，红色：无法连接
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

    # 新增：模型选择状态更新
    def update_model_status(self, error=None):
        # 红色：未选择，黄色：无法获取模型列表，绿色：已选择
        if error == "fetch_fail":
            self.status_model.set_status("Failed to fetch", "yellow")
        elif self.selected_model:
            self.status_model.set_status(f"Selected ({self.selected_model})", "green")
        else:
            self.status_model.set_status("Not selected", "red")

    # 新增：HTTP错误状态更新
    def update_http_status(self, code=None):
        # 红色：400-499，黄色：500-599，绿色：其他
        if code is None:
            self.status_http.set_status("OK", "green")
        elif 400 <= code <= 499:
            self.status_http.set_status(f"Client Error ({code})", "red")
        elif 500 <= code <= 599:
            self.status_http.set_status(f"Server Error ({code})", "yellow")
        else:
            self.status_http.set_status(f"OK ({code})", "green")

    # 新增：聊天服务状态更新
    def update_chat_status(self, state):
        # 红色：未进入聊天，黄色：正在输出，绿色：等待输入
        if state == "not_ready":
            self.status_chat.set_status("Not ready", "red")
        elif state == "streaming":
            self.status_chat.set_status("Streaming...", "yellow")
        elif state == "ready":
            self.status_chat.set_status("Ready", "green")
        else:
            self.status_chat.set_status("Unknown", "gray")

    # 新增：网络状态循环线程
    def network_status_loop(self):
        while not self.network_thread_stop:
            latency = None
            status = None
            try:
                # 取主机名部分用于ping
                import urllib.parse
                url = urllib.parse.urlparse(DEEPSEEK_API_BASE_URL_V1)
                host = url.hostname
                # Windows下ping命令
                result = subprocess.run(
                    ["ping", "-n", "1", "-w", "1000", host],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                if result.returncode == 0:
                    # 解析延迟
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
            # 必须在主线程更新GUI
            self.master.after(0, self.update_network_status, latency, status)
            time.sleep(5)

def main():
    root = tk.Tk()
    app = DeepSeekGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()