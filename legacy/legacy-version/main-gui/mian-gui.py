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

DEEPSEEK_API_BASE_URL_V1 = "https://api.deepseek.com/v1"
DEEPSEEK_BALANCE_URL = "https://api.deepseek.com/user/balance"

class DeepSeekGUI:
    def __init__(self, master):
        self.master = master
        master.title("DeepSeek API Client GUI")

        self.api_key = ""
        self.client = None
        self.selected_model = None
        self.messages = []

        # 其它控件...

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

        # 不要再用 grid 相关代码
        # master.rowconfigure(0, weight=1)
        # master.columnconfigure(0, weight=1)
        # self.output.grid(row=0, column=0, sticky="nsew")
        # self.output.pack_forget()
        # self.output.grid(row=0, column=0, columnspan=10, sticky="nsew")

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
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize client: {e}")

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

    def list_and_select_model(self):
        if not self.client:
            messagebox.showerror("Error", "Please initialize the client first.")
            return
        try:
            self.print_out("Fetching model list...")
            models_response = self.client.models.list()
            available_models = [model.id for model in models_response.data if
                                "chat" in model.id.lower() or "coder" in model.id.lower() or len(models_response.data) < 10]
            if not available_models:
                available_models = [model.id for model in models_response.data]
            if not available_models:
                manual_model = simpledialog.askstring("Enter Model Name", "No models found. Please enter model name (e.g., deepseek-chat):")
                if manual_model:
                    self.selected_model = manual_model
                    self.print_out(f"Model selected manually: {manual_model}")
                else:
                    self.print_out("No model selected.")
                return
            model_choice = simpledialog.askinteger(
                "Select Model",
                "Available models:\n" + "\n".join([f"{i+1}. {mid}" for i, mid in enumerate(available_models)]) +
                f"\nEnter number (1-{len(available_models)}):"
            )
            if model_choice and 1 <= model_choice <= len(available_models):
                self.selected_model = available_models[model_choice-1]
                self.print_out(f"Model selected: {self.selected_model}")
            else:
                self.print_out("No model selected.")
        except Exception as e:
            manual_model = simpledialog.askstring("Enter Model Name", f"Failed to fetch models: {e}\nYou can enter model name manually (e.g., deepseek-chat):")
            if manual_model:
                self.selected_model = manual_model
                self.print_out(f"Model selected manually: {manual_model}")

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
            self.print_out(f"HTTP error: {http_err}")
            if http_err.response is not None:
                self.print_out(f"Status code: {http_err.response.status_code}")
                try:
                    error_details = http_err.response.json()
                    self.print_out(f"Error details: {json.dumps(error_details, indent=2, ensure_ascii=False)}")
                except json.JSONDecodeError:
                    self.print_out(f"Response content: {http_err.response.text}")
        except requests.exceptions.RequestException as e:
            self.print_out(f"Request failed: {e}")
        except json.JSONDecodeError:
            self.print_out("Balance response is not valid JSON.")
        except Exception as e:
            self.print_out(f"Unknown error: {e}")

    def start_chat(self):
        if not self.client:
            messagebox.showerror("Error", "Please initialize the client first.")
            return
        if not self.selected_model:
            messagebox.showerror("Error", "Please select a model first.")
            return
        self.print_out(f"\nStarting chat with model '{self.selected_model}' (type /exit to end, /new for new session)")
        self.messages = []
        while True:
            user_input = simpledialog.askstring("You", "You:")
            if user_input is None:
                self.print_out("Chat cancelled.")
                break
            if user_input.lower() == '/exit':
                self.print_out("Chat ended.")
                break
            if user_input.lower() == '/new':
                self.print_out("New session started.")
                self.messages = []
                continue
            self.messages.append({"role": "user", "content": user_input})
            self.print_out(f"You: {user_input}")
            try:
                self.print_out("Model: ",)
                assistant_response_content = ""
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
            except Exception as e:
                self.print_out(f"\nChat error: {e}")
                if "Incorrect API key" in str(e) or "authentication" in str(e).lower():
                    self.print_out("Please check if your API Key is correct.")
                self.print_out("You can retry or type /exit or /new.")

def main():
    root = tk.Tk()
    app = DeepSeekGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()