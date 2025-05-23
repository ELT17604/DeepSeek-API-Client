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
import re

# 判断是否需要导入tkinter
USE_GUI = "--gui" in sys.argv or (not "--cli" in sys.argv)

if USE_GUI:
    import tkinter as tk
    from tkinter import messagebox, simpledialog, scrolledtext, ttk, font  # 添加font导入
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
    class MarkdownText(scrolledtext.ScrolledText):
        """支持Markdown渲染的文本控件"""
        def __init__(self, master, **kwargs):
            super().__init__(master, **kwargs)
            
            # 配置文本样式标签
            self.configure_markdown_tags()
            
            # 当前文本缓冲区 - 存储原始文本内容
            self.raw_content = ""
            
        def configure_markdown_tags(self):
            """配置Markdown样式标签"""
            # 获取默认字体 - 修复字体获取问题
            try:
                # 先尝试获取控件的当前字体
                current_font = self.cget("font")
                if isinstance(current_font, tuple):
                    # 如果是元组形式 (family, size, style)
                    font_family = current_font[0]
                    font_size = current_font[1] if len(current_font) > 1 else 11
                elif isinstance(current_font, str):
                    # 如果是字符串形式，尝试解析
                    parts = current_font.split()
                    if len(parts) >= 2:
                        font_family = parts[0]
                        try:
                            font_size = int(parts[1])
                        except ValueError:
                            font_size = 11
                    else:
                        font_family = current_font
                        font_size = 11
                else:
                    # 使用默认值
                    font_family = "TkDefaultFont"
                    font_size = 11
                    
                # 如果获取的字体不合理，使用系统默认字体
                if not font_family or font_family in ["", "none"]:
                    font_family = "TkDefaultFont"
                    
            except Exception:
                # 如果获取字体失败，使用默认值
                font_family = "TkDefaultFont"
                font_size = 11
            
            # 标题样式
            self.tag_configure("h1", font=(font_family, font_size + 6, "bold"), foreground="#2E86AB", spacing1=10, spacing3=5)
            self.tag_configure("h2", font=(font_family, font_size + 4, "bold"), foreground="#A23B72", spacing1=8, spacing3=4)
            self.tag_configure("h3", font=(font_family, font_size + 2, "bold"), foreground="#F18F01", spacing1=6, spacing3=3)
            self.tag_configure("h4", font=(font_family, font_size + 1, "bold"), foreground="#C73E1D", spacing1=4, spacing3=2)
            
            # 代码块样式 - 使用等宽字体
            code_font_family = "Consolas"
            # 在Windows上检查Consolas是否可用，如果不可用则使用Courier New
            try:
                test_font = font.Font(family=code_font_family, size=font_size)
                test_font.actual()  # 测试字体是否可用
            except Exception:
                code_font_family = "Courier New"
                
            self.tag_configure("code_block", 
                             font=(code_font_family, font_size, "normal"),
                             background="#f6f8fa",
                             foreground="#24292e",
                             relief="solid",
                             borderwidth=1,
                             lmargin1=20,
                             lmargin2=20,
                             rmargin=20,
                             spacing1=5,
                             spacing3=5)
            
            # 内联代码样式
            self.tag_configure("inline_code",
                             font=(code_font_family, font_size - 1, "normal"),
                             background="#f3f4f6",
                             foreground="#e11d48",
                             relief="solid",
                             borderwidth=1)
            
            # 粗体和斜体
            self.tag_configure("bold", font=(font_family, font_size, "bold"))
            self.tag_configure("italic", font=(font_family, font_size, "italic"))
            self.tag_configure("bold_italic", font=(font_family, font_size, "bold italic"))
            
            # 列表样式
            self.tag_configure("list_item", lmargin1=20, lmargin2=40)
            
            # 引用样式
            self.tag_configure("blockquote",
                             background="#f8f9fa",
                             foreground="#6a737d",
                             lmargin1=20,
                             lmargin2=20,
                             rmargin=20,
                             relief="solid",
                             borderwidth=1,
                             spacing1=5,
                             spacing3=5)
            
            # 普通文本样式
            self.tag_configure("normal", font=(font_family, font_size, "normal"))
            
        def update_markdown_font(self, new_font_family, new_font_size):
            """更新Markdown样式的字体"""
            # 检查代码字体是否可用
            code_font_family = "Consolas"
            try:
                test_font = font.Font(family=code_font_family, size=new_font_size)
                test_font.actual()
            except Exception:
                code_font_family = "Courier New"
                
            # 重新配置所有标签的字体
            self.tag_configure("h1", font=(new_font_family, new_font_size + 6, "bold"))
            self.tag_configure("h2", font=(new_font_family, new_font_size + 4, "bold"))
            self.tag_configure("h3", font=(new_font_family, new_font_size + 2, "bold"))
            self.tag_configure("h4", font=(new_font_family, new_font_size + 1, "bold"))
            self.tag_configure("code_block", font=(code_font_family, new_font_size, "normal"))
            self.tag_configure("inline_code", font=(code_font_family, new_font_size - 1, "normal"))
            self.tag_configure("bold", font=(new_font_family, new_font_size, "bold"))
            self.tag_configure("italic", font=(new_font_family, new_font_size, "italic"))
            self.tag_configure("bold_italic", font=(new_font_family, new_font_size, "bold italic"))
            self.tag_configure("normal", font=(new_font_family, new_font_size, "normal"))
            
        def append_raw_text(self, text, end="\n"):
            """追加原始文本到缓冲区"""
            self.raw_content += text
            if end:
                self.raw_content += end
                
        def get_raw_content(self):
            """获取原始文本内容"""
            return self.raw_content
            
        def set_raw_content(self, content):
            """设置原始文本内容"""
            self.raw_content = content
            
        def clear_all(self):
            """清空所有内容"""
            self.raw_content = ""
            self.delete(1.0, tk.END)
            
        def _render_markdown_text(self, text):
            """渲染Markdown文本的核心方法"""
            if not text:
                return
                
            lines = text.split('\n')
            current_pos = 1.0
            
            i = 0
            while i < len(lines):
                line = lines[i]
                line_start = current_pos
                
                # 处理代码块
                if line.strip().startswith('```'):
                    # 找到代码块结束
                    code_lines = []
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith('```'):
                        code_lines.append(lines[i])
                        i += 1
                    
                    # 插入代码块（不包含```标记）
                    if code_lines:
                        code_text = '\n'.join(code_lines) + '\n'
                        self.insert(current_pos, code_text)
                        end_pos = f"{line_start}+{len(code_text)}c"
                        self.tag_add("code_block", line_start, end_pos)
                        current_pos = end_pos
                    i += 1
                    continue
                
                # 处理标题
                if line.strip().startswith('#'):
                    hash_count = 0
                    for char in line:
                        if char == '#':
                            hash_count += 1
                        else:
                            break
                    
                    if hash_count <= 4:
                        title_text = line.strip('#').strip()  # 移除#号和空格
                        if title_text:
                            display_text = title_text + '\n'
                            self.insert(current_pos, display_text)
                            end_pos = f"{line_start}+{len(display_text)}c"
                            self.tag_add(f"h{hash_count}", line_start, end_pos)
                            current_pos = end_pos
                            i += 1
                            continue
                
                # 处理引用块
                if line.strip().startswith('>'):
                    quote_lines = []
                    while i < len(lines) and lines[i].strip().startswith('>'):
                        quote_text = lines[i].strip().lstrip('>').strip()  # 移除>号和空格
                        quote_lines.append(quote_text)
                        i += 1
                    
                    if quote_lines:
                        quote_text = '\n'.join(quote_lines) + '\n'
                        self.insert(current_pos, quote_text)
                        end_pos = f"{line_start}+{len(quote_text)}c"
                        self.tag_add("blockquote", line_start, end_pos)
                        current_pos = end_pos
                    continue
                
                # 处理列表项
                if re.match(r'^\s*[-*+]\s+', line) or re.match(r'^\s*\d+\.\s+', line):
                    # 移除列表标记，保留缩进
                    clean_line = re.sub(r'^(\s*)[-*+]\s+', r'\1• ', line)  # 将-*+替换为•
                    clean_line = re.sub(r'^(\s*)\d+\.\s+', r'\1\g<0>', clean_line)  # 保留数字列表
                    display_text = clean_line + '\n'
                    self.insert(current_pos, display_text)
                    end_pos = f"{line_start}+{len(display_text)}c"
                    self.tag_add("list_item", line_start, end_pos)
                    current_pos = end_pos
                    i += 1
                    continue
                
                # 处理普通文本（包含内联格式）
                processed_line = self._process_inline_formatting(line)
                display_text = processed_line['text'] + '\n'
                self.insert(current_pos, display_text)
                
                # 应用格式标签
                self._apply_format_tags(line_start, processed_line['formats'])
                
                current_pos = f"{line_start}+{len(display_text)}c"
                i += 1
        
        def _process_inline_formatting(self, text):
            """处理内联格式并返回处理后的文本和格式信息"""
            processed_text = text
            formats = []
            offset = 0  # 跟踪文本长度变化
            
            # 处理顺序：先处理最长的格式（粗体斜体），然后是粗体，最后是斜体
            # 这样可以避免格式冲突
            
            # 1. 处理内联代码（最高优先级，不被其他格式影响）
            code_pattern = r'`([^`]+)`'
            code_matches = list(re.finditer(code_pattern, text))
            # 记录代码区域，避免在代码中处理其他格式
            code_ranges = [(match.start(), match.end()) for match in code_matches]
            
            for match in reversed(code_matches):  # 从后往前处理，避免位置偏移
                start, end = match.span()
                content = match.group(1)
                # 替换`code`为code，并记录格式
                processed_text = processed_text[:start] + content + processed_text[end:]
                formats.append({
                    'start': start - offset,
                    'end': start - offset + len(content),
                    'type': 'inline_code'
                })
                offset += 2  # 减去两个`符号
            
            # 2. 处理粗体斜体 ***text***
            bold_italic_pattern = r'\*\*\*([^*]+?)\*\*\*'
            bold_italic_matches = list(re.finditer(bold_italic_pattern, processed_text))
            
            for match in reversed(bold_italic_matches):
                start, end = match.span()
                # 检查是否与代码区域重叠
                if not self._position_in_ranges(start, end, code_ranges, offset):
                    content = match.group(1)
                    processed_text = processed_text[:start] + content + processed_text[end:]
                    formats.append({
                        'start': start,
                        'end': start + len(content),
                        'type': 'bold_italic'
                    })
                    offset += 6  # 减去六个*符号
            
            # 3. 处理粗体 **text**
            bold_pattern = r'\*\*([^*]+?)\*\*'
            bold_matches = list(re.finditer(bold_pattern, processed_text))
            
            for match in reversed(bold_matches):
                start, end = match.span()
                # 检查是否与代码区域或已处理的粗体斜体重叠
                if not self._position_in_ranges(start, end, code_ranges, offset):
                    content = match.group(1)
                    processed_text = processed_text[:start] + content + processed_text[end:]
                    formats.append({
                        'start': start,
                        'end': start + len(content),
                        'type': 'bold'
                    })
                    offset += 4  # 减去四个*符号
            
            # 4. 处理斜体 *text*
            italic_pattern = r'\*([^*]+?)\*'
            italic_matches = list(re.finditer(italic_pattern, processed_text))
            
            for match in reversed(italic_matches):
                start, end = match.span()
                # 检查是否与其他格式重叠
                if not self._position_in_ranges(start, end, code_ranges, offset):
                    content = match.group(1)
                    processed_text = processed_text[:start] + content + processed_text[end:]
                    formats.append({
                        'start': start,
                        'end': start + len(content),
                        'type': 'italic'
                    })
                    offset += 2  # 减去两个*符号
            
            return {
                'text': processed_text,
                'formats': formats
            }
        
        def _position_in_ranges(self, start, end, ranges, offset):
            """检查位置是否在指定范围内（考虑偏移量）"""
            adjusted_start = start + offset
            adjusted_end = end + offset
            
            for range_start, range_end in ranges:
                if (adjusted_start < range_end and adjusted_end > range_start):
                    return True
            return False
        
        def _apply_format_tags(self, line_start_pos, formats):
            """应用格式标签到文本"""
            for fmt in formats:
                start_pos = f"{line_start_pos}+{fmt['start']}c"
                end_pos = f"{line_start_pos}+{fmt['end']}c"
                self.tag_add(fmt['type'], start_pos, end_pos)
        
        def _apply_inline_formatting(self, start_pos, end_pos, text):
            """应用内联格式（粗体、斜体、代码等）- 保留原方法作为备用"""
            # 这个方法现在由新的处理逻辑替代，但保留以防兼容性问题
            pass
                    
        def _overlaps_with_matches(self, match, other_matches):
            """检查当前匹配是否与其他匹配重叠"""
            for other_match in other_matches:
                if (match.start() < other_match.end() and match.end() > other_match.start()):
                    return True
            return False

        def render_as_markdown(self):
            """将当前原始内容渲染为Markdown"""
            # 保存当前滚动位置
            current_pos = self.yview()
            
            # 清空显示区域并重新渲染
            self.delete(1.0, tk.END)
            self._render_markdown_text(self.raw_content)
            
            # 滚动到底部
            self.see(tk.END)
            
        def render_as_plain_text(self):
            """将当前原始内容渲染为纯文本"""
            # 保存当前滚动位置
            current_pos = self.yview()
            
            # 清空显示区域并插入纯文本
            self.delete(1.0, tk.END)
            self.insert(1.0, self.raw_content)
            
            # 滚动到底部
            self.see(tk.END)
            
        def append_and_render(self, text, end="\n", markdown_enabled=True):
            """追加文本并根据模式渲染"""
            self.append_raw_text(text, end)
            
            if markdown_enabled:
                self.render_as_markdown()
            else:
                self.render_as_plain_text()
            
        def switch_render_mode(self, markdown_enabled):
            """切换渲染模式（保持内容不变）"""
            if markdown_enabled:
                self.render_as_markdown()
            else:
                self.render_as_plain_text()

    class StatusIndicator(tk.Frame):
        """状态指示器控件，每行显示状态文本和一个彩色指示灯"""
        def __init__(self, master, label_text, **kwargs):
            super().__init__(master, **kwargs)
            self.label_text = label_text
            self.status_var = tk.StringVar(value=f"{label_text}: Not initialized")
            
            # 状态文本标签 - 增加宽度以容纳延迟信息
            self.label = tk.Label(self, textvariable=self.status_var, anchor="w", width=28, font=("Arial", 9))
            self.label.pack(side=tk.LEFT, padx=(2, 5))
            
            # 彩色指示灯
            self.canvas = tk.Canvas(self, width=16, height=16, highlightthickness=0, bg="white")
            self.canvas.pack(side=tk.LEFT, padx=2)
            self.indicator = self.canvas.create_oval(2, 2, 14, 14, fill="gray", outline="darkgray", width=1)

        def set_status(self, text, color):
            """设置状态文本和指示灯颜色"""
            self.status_var.set(f"{self.label_text}: {text}")
            # 确保颜色映射正确
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
            master.title("DeepSeek API Client GUI")

            self.api_key = ""
            self.client = None
            self.selected_model = None
            self.messages = []
            self.available_models = []  # 添加模型列表存储

            # ========== 新增：输出栏字体大小相关 ==========
            self.output_font_size = 11  # 默认字体大小
            # 修改默认字体为系统字体，避免字体不存在的问题
            self.output_font_family = "TkDefaultFont"
            self.output_font = (self.output_font_family, self.output_font_size)

            # ========== API Key输入区域 ==========
            self.api_frame = tk.Frame(master)
            self.api_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

            self.api_label = tk.Label(self.api_frame, text="API Key:", font=("Arial", 10))
            self.api_label.pack(side=tk.LEFT)

            self.api_key_entry = tk.Entry(self.api_frame, show="*", font=("Arial", 10))
            self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
            self.api_key_entry.bind("<KeyRelease>", self.on_api_key_change)  # 添加这行

            # 尝试加载保存的API Key
            saved_key = load_api_key_from_file()
            if saved_key:
                self.api_key_entry.insert(0, saved_key)
                # 不要在这里自动初始化，让用户手动点击Initialize按钮

            self.init_btn = tk.Button(self.api_frame, text="Initialize", command=self.initialize_client)
            self.init_btn.pack(side=tk.RIGHT, padx=(5, 0))

            self.api_key_masked_label = tk.Label(self.api_frame, text="", font=("Arial", 10))

            # ========== 模型选择区域 ==========
            self.model_frame = tk.Frame(master)
            self.model_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

            self.model_label = tk.Label(self.model_frame, text="Model:", font=("Arial", 10))
            self.model_label.pack(side=tk.LEFT)

            # 初始化时的模型变量设置
            self.model_var = tk.StringVar(value="Please select a model...")
            self.model_combobox = ttk.Combobox(self.model_frame, textvariable=self.model_var, 
                                               state="readonly", font=("Arial", 10), width=30)
            self.model_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
            self.model_combobox.bind("<<ComboboxSelected>>", self.on_model_selected)

            self.refresh_models_btn = tk.Button(self.model_frame, text="Refresh Models", 
                                                command=self.refresh_models, state=tk.DISABLED)
            self.refresh_models_btn.pack(side=tk.RIGHT)

            # ========== 控制按钮区域 ==========
            self.control_frame = tk.Frame(master)
            self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

            self.balance_btn = tk.Button(self.control_frame, text="Query Balance", command=self.query_balance)
            self.balance_btn.pack(side=tk.LEFT)

            self.chat_btn = tk.Button(self.control_frame, text="Start Chat", command=self.start_chat)
            self.chat_btn.pack(side=tk.LEFT, padx=(5, 0))

            self.clear_btn = tk.Button(self.control_frame, text="Clear Output", command=self.clear_output)
            self.clear_btn.pack(side=tk.LEFT, padx=(5, 0))

            # 新增：Markdown渲染切换按钮
            self.markdown_enabled = True  # 默认启用Markdown渲染
            self.markdown_btn = tk.Button(self.control_frame, text="Markdown: ON", command=self.toggle_markdown_rendering)
            self.markdown_btn.pack(side=tk.LEFT, padx=(5, 0))

            # 右侧状态监控按钮
            self.status_btn = tk.Button(self.control_frame, text="Status Monitor", command=self.toggle_status_window)
            self.status_btn.pack(side=tk.RIGHT)

            # 添加状态指示灯到按钮左侧
            self.status_indicators_frame = tk.Frame(self.control_frame)
            self.status_indicators_frame.pack(side=tk.RIGHT, padx=(0, 5))

            # 右侧指示灯 - 跟随chat状态
            self.chat_indicator_canvas = tk.Canvas(self.status_indicators_frame, width=16, height=16, highlightthickness=0, bg="white")
            self.chat_indicator_canvas.pack(side=tk.RIGHT, padx=2)
            self.chat_indicator = self.chat_indicator_canvas.create_oval(2, 2, 14, 14, fill="red", outline="darkgray", width=1)

            # 左侧指示灯 - 综合状态
            self.overall_indicator_canvas = tk.Canvas(self.status_indicators_frame, width=16, height=16, highlightthickness=0, bg="white")
            self.overall_indicator_canvas.pack(side=tk.RIGHT, padx=2)
            self.overall_indicator = self.overall_indicator_canvas.create_oval(2, 2, 14, 14, fill="red", outline="darkgray", width=1)

            # ========== 输出区域 ==========
            # 修改输出区域的字体设置，使用更安全的默认字体
            try:
                self.output = MarkdownText(master, width=80, height=20, state='normal', 
                                         font=("TkDefaultFont", self.output_font_size))
            except Exception as e:
                print(f"Warning: Could not create MarkdownText with specified font: {e}")
                # 如果仍然失败，使用最基本的设置
                self.output = MarkdownText(master, width=80, height=20, state='normal')
            
            self.output.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

            # ========== 用户输入区 ==========
            self.input_frame = tk.Frame(master)
            self.input_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 2))

            self.input_label = tk.Label(self.input_frame, text="You:", font=("Arial", 10))
            self.input_label.pack(side=tk.LEFT, anchor="s", pady=2)

            self.user_input = tk.Text(self.input_frame, height=3, wrap="word", state=tk.DISABLED)
            self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
            self.user_input.bind("<KeyRelease>", self.on_input_change)
            self.user_input.bind("<Return>", self.send_user_input)
            self.user_input.bind("<Control-Return>", lambda e: self.user_input.insert(tk.INSERT, "\n"))

            # ========== 输入控制按钮 ==========
            self.input_btn_frame = tk.Frame(master)
            self.input_btn_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 4))

            self.btn_spacer = tk.Label(self.input_btn_frame)
            self.btn_spacer.pack(side=tk.LEFT, fill=tk.X, expand=True)

            self.send_btn = tk.Button(self.input_btn_frame, text="Send", command=self.send_user_input, state=tk.DISABLED)
            self.send_btn.pack(side=tk.RIGHT, padx=(8, 0))

            # 添加停止按钮
            self.stop_btn = tk.Button(self.input_btn_frame, text="Stop", command=self.stop_streaming, state=tk.DISABLED)
            self.stop_btn.pack(side=tk.RIGHT, padx=(8, 0))

            self.new_btn = tk.Button(self.input_btn_frame, text="New Session", command=self.start_new_session, state=tk.DISABLED)
            self.new_btn.pack(side=tk.RIGHT, padx=(8, 0))

            self.end_btn = tk.Button(self.input_btn_frame, text="End Chat", command=self.end_chat, state=tk.NORMAL)
            self.end_btn.pack(side=tk.RIGHT, padx=(8, 0))
            
            # 添加停止标志
            self.streaming_stopped = False

            # ========== 版权信息（放在最底部） ==========
            self.footer_label = tk.Label(
                master,
                text="DeepSeek API Client GUI v0.7.2 © 2025 ELT Group",
                font=("Arial", 8),
                fg="gray"
            )
            self.footer_label.pack(side=tk.BOTTOM, pady=(0, 3))

            # ========== 字体大小调节控件（移至版权信息上方） ==========
            self.font_frame = tk.Frame(master)
            self.font_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 2))

            self.font_label = tk.Label(self.font_frame, text="输出栏字体大小:", font=("Arial", 9))
            self.font_label.pack(side=tk.LEFT)

            self.font_minus_btn = tk.Button(self.font_frame, text="－", width=2, command=self.decrease_font_size)
            self.font_minus_btn.pack(side=tk.LEFT, padx=(2, 0))

            self.font_size_var = tk.IntVar(value=self.output_font_size)
            self.font_size_entry = tk.Entry(self.font_frame, width=3, textvariable=self.font_size_var, justify="center")
            self.font_size_entry.pack(side=tk.LEFT, padx=(2, 0))
            self.font_size_entry.bind("<Return>", self.set_font_size_from_entry)

            self.font_plus_btn = tk.Button(self.font_frame, text="＋", width=2, command=self.increase_font_size)
            self.font_plus_btn.pack(side=tk.LEFT, padx=(2, 0))

            # ========== API Key 管理控件（移至字体调节上方） ==========
            self.api_manage_frame = tk.Frame(master)
            self.api_manage_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 2))

            self.clear_apikey_btn = tk.Button(self.api_manage_frame, text="Clear API Key", command=self.clear_api_key, state=tk.DISABLED)
            self.clear_apikey_btn.pack(side=tk.LEFT)

            # ========== 独立状态监控窗口相关 ==========
            self.status_window = None
            self.status_indicators = {}

            # 初始化状态监控数据
            self.status_data = {
                "client": {"text": "No API Key", "color": "red"},
                "network": {"text": "Checking...", "color": "gray"},
                "model": {"text": "Not selected", "color": "red"},
                "http": {"text": "OK", "color": "green"},  # 默认HTTP状态设为绿色
                "chat": {"text": "Not ready", "color": "red"}
            }

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

            # 在创建完所有指示灯控件后再初始化状态
            # 初始化状态
            self.update_client_status()
            self.update_network_status()
            self.update_model_status()
            self.update_http_status()
            self.update_chat_status("not_ready")

        def toggle_status_window(self):
            """切换状态监控窗口的显示/隐藏"""
            if self.status_window is None or not self.status_window.winfo_exists():
                self.create_status_window()
                self.status_btn.config(text="Hide Status")
            else:
                self.status_window.destroy()
                self.status_window = None
                self.status_btn.config(text="Status Monitor")

        def create_status_window(self):
            """创建独立的状态监控窗口"""
            self.status_window = tk.Toplevel(self.master)
            self.status_window.title("Status Monitor")
            self.status_window.geometry("320x160")  # 稍微增加宽度以容纳延迟数据
            self.status_window.resizable(False, False)
            
            # 隐藏窗口的关闭按钮和标题栏
            self.status_window.overrideredirect(True)
            
            # 设置窗口位置（在主窗口右侧）
            main_x = self.master.winfo_x()
            main_y = self.master.winfo_y()
            main_width = self.master.winfo_width()
            self.status_window.geometry(f"320x160+{main_x + main_width + 10}+{main_y}")
            
            # 添加标题栏
            title_frame = tk.Frame(self.status_window, bg="darkgray", height=25)
            title_frame.pack(fill=tk.X)
            title_frame.pack_propagate(False)
            
            title_label = tk.Label(title_frame, text="Status Monitor", bg="darkgray", fg="white", font=("Arial", 9, "bold"))
            title_label.pack(side=tk.LEFT, padx=5, pady=3)
            
            # 内容区域
            content_frame = tk.Frame(self.status_window, bg="white")
            content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            # 创建状态指示器
            self.status_indicators["client"] = StatusIndicator(content_frame, "Client")
            self.status_indicators["client"].pack(anchor="w", padx=5, pady=2)

            self.status_indicators["network"] = StatusIndicator(content_frame, "Network")
            self.status_indicators["network"].pack(anchor="w", padx=5, pady=2)

            self.status_indicators["model"] = StatusIndicator(content_frame, "Model")
            self.status_indicators["model"].pack(anchor="w", padx=5, pady=2)

            self.status_indicators["http"] = StatusIndicator(content_frame, "HTTP")
            self.status_indicators["http"].pack(anchor="w", padx=5, pady=2)

            self.status_indicators["chat"] = StatusIndicator(content_frame, "Chat")
            self.status_indicators["chat"].pack(anchor="w", padx=5, pady=2)

            # 更新所有状态显示
            for key, data in self.status_data.items():
                if key in self.status_indicators:
                    self.status_indicators[key].set_status(data["text"], data["color"])

            # 使窗口始终在最前面
            self.status_window.attributes("-topmost", True)

        def on_status_window_close(self):
            """状态窗口关闭时的处理"""
            self.status_window = None
            self.status_btn.config(text="Status Monitor")

        def update_status_display(self, status_type, text, color):
            """更新状态显示（同时更新数据和窗口显示）"""
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
            # 颜色映射
            color_map = {
                "red": "#ff4444",
                "green": "#44ff44", 
                "yellow": "#ffcc00",
                "gray": "#888888",
                "grey": "#888888"
            }
            
            # 右侧指示灯 - 跟随chat状态
            chat_color = self.status_data.get("chat", {}).get("color", "red")
            chat_indicator_color = color_map.get(chat_color.lower(), chat_color)
            self.chat_indicator_canvas.itemconfig(self.chat_indicator, fill=chat_indicator_color)
            
            # 左侧指示灯 - 综合状态逻辑
            client_color = self.status_data.get("client", {}).get("color", "red")
            network_color = self.status_data.get("network", {}).get("color", "red")
            model_color = self.status_data.get("model", {}).get("color", "red")
            http_color = self.status_data.get("http", {}).get("color", "red")
            
            # 检查除chat外的四个指示灯是否均为绿色
            all_green = all(color == "green" for color in [client_color, network_color, model_color, http_color])
            
            # 检查除chat外的四个指示灯中，除了网络外的三个是否均为绿色
            three_green_without_network = all(color == "green" for color in [client_color, model_color, http_color])
            
            # 检查除chat和model外的三个指示灯是否均为绿色
            three_green_without_model = all(color == "green" for color in [client_color, network_color, http_color])
            
            if all_green:
                overall_color = "#44ff44"  # 绿色 - 所有状态都是绿色
            elif three_green_without_network and network_color == "yellow":
                overall_color = "#ffcc00"  # 黄色 - 网络是黄色，其他都是绿色
            elif three_green_without_model:
                overall_color = "#ffcc00"  # 黄色 - model不是绿色，其他都是绿色
            else:
                overall_color = "#ff4444"  # 红色 - 其他情况
                
            self.overall_indicator_canvas.itemconfig(self.overall_indicator, fill=overall_color)

        def initialize_client(self):
            """初始化客户端"""
            api_key = self.api_key_entry.get().strip()
            if not api_key:
                messagebox.showerror("Error", "Please enter an API key")
                return

            try:
                self.client = OpenAI(api_key=api_key, base_url=DEEPSEEK_API_BASE_URL_V1)
                self.api_key = api_key
                
                # 保存API Key
                if save_api_key_to_file(api_key):
                    self.print_out("API Key已安全加密并保存到本地文件。")
                
                # 隐藏输入框，显示掩码标签（左对齐）
                self.api_key_entry.pack_forget()
                
                # 修改为完全星号显示，左对齐
                masked_key = "*" * min(len(api_key), 32)  # 显示更多星号以便识别
                self.api_key_masked_label.config(text=masked_key, anchor="w")  # 左对齐
                self.api_key_masked_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
                
                # 冻结初始化按钮而不是隐藏
                self.init_btn.config(state=tk.DISABLED, text="Initialized")
                
                # 启用相关功能
                self.refresh_models_btn.config(state=tk.NORMAL)
                self.clear_apikey_btn.config(state=tk.NORMAL)
                
                # 更新状态
                self.update_client_status()
                self.print_out("Client initialized successfully!")
                
                # 自动刷新模型列表
                self.refresh_models()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize client: {str(e)}")
                self.print_out(f"Client initialization failed: {str(e)}")

        def clear_api_key(self):
            """清除API Key"""
            result = messagebox.askyesno("Confirm", "Are you sure you want to clear the saved API key?\nThis will reset the client and require re-initialization.")
            if result:
                try:
                    # 删除保存的API Key文件
                    if delete_api_key_file():
                        self.print_out("API Key file deleted successfully.")
                    
                    # 重置客户端状态
                    self.client = None
                    self.api_key = ""
                    self.selected_model = None
                    self.messages = []
                    self.available_models = []
                    
                    # 恢复UI到初始状态
                    self.api_key_masked_label.pack_forget()
                    self.api_key_entry.delete(0, tk.END)
                    self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
                    
                    # 恢复初始化按钮
                    self.init_btn.config(state=tk.NORMAL, text="Initialize")
                    
                    # 重置模型选择
                    self.model_var.set("Please select a model...")
                    self.model_combobox['values'] = ()
                    
                    # 禁用相关功能
                    self.refresh_models_btn.config(state=tk.DISABLED)
                    self.clear_apikey_btn.config(state=tk.DISABLED)
                    
                    # 禁用输入框
                    self.user_input.config(state=tk.DISABLED)
                    self.user_input.delete("1.0", tk.END)
                    
                    # 更新所有状态
                    self.update_client_status()
                    self.update_model_status()
                    self.update_chat_status("not_ready")
                    self.update_buttons_state()
                    
                    self.print_out("API Key cleared. Please enter a new API key and initialize the client.")
                    messagebox.showinfo("Success", "API Key cleared successfully. Please enter a new API key.")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to clear API key: {str(e)}")
                    self.print_out(f"Error clearing API key: {str(e)}")

        # ===================== API 调用相关 =====================
        def start_chat(self):
            """开始聊天（GUI）"""
            if not self.client:
                messagebox.showerror("Error", "Please initialize client first")
                return
            if not self.selected_model:
                messagebox.showerror("Error", "Please select a model first")
                return

            self.messages = []
            self.user_input.config(state=tk.NORMAL)
            self.user_input.focus_set()
            self.update_chat_status("ready")
            self.update_buttons_state()
            self.print_out(f"Chat started with model: {self.selected_model}")
            self.print_out("Type your message and press Send or Enter to chat.")

        def refresh_models(self):
            """刷新模型列表（GUI版本）"""
            if not self.client:
                messagebox.showerror("Error", "Please initialize client first")
                return
                
            try:
                self.print_out("Fetching available models...")
                models_response = self.client.models.list()
                
                # 过滤模型
                available_models = [model.id for model in models_response.data if
                                  "chat" in model.id.lower() or "coder" in model.id.lower() or len(models_response.data) < 10]
                
                if not available_models:
                    available_models = [model.id for model in models_response.data]
                
                if not available_models:
                    self.print_out("No models found. Please check your API key.")
                    self.update_model_status("fetch_fail")
                    return
                
                self.available_models = available_models
                self.model_combobox['values'] = available_models
                
                # 移除自动选择逻辑，保持未选择状态
                # 如果当前选择的模型不在新列表中，则重置为未选择状态
                if self.selected_model and self.selected_model not in available_models:
                    self.selected_model = None
                    self.model_var.set("Please select a model...")
                
                # 更新模型状态
                self.update_model_status()
                
                self.print_out(f"Found {len(available_models)} models. Please select one to continue.")
                self.update_buttons_state()
                
            except Exception as e:
                error_msg = str(e)
                self.print_out(f"Failed to fetch models: {error_msg}")
                self.update_model_status("fetch_fail")
                messagebox.showerror("Error", f"Failed to fetch models: {error_msg}")

        def on_model_selected(self, event=None):
            """模型选择事件处理"""
            selected = self.model_var.get()
            if selected and selected != "Please select a model...":
                self.selected_model = selected
                self.update_model_status()
                self.update_buttons_state()
                self.print_out(f"Selected model: {selected}")

        def update_client_status(self):
            """更新客户端状态"""
            api_key_entered = bool(self.api_key_entry.get().strip())
            
            if self.client and self.api_key:
                self.update_status_display("client", "Initialized", "green")
            elif api_key_entered:
                self.update_status_display("client", "API Key entered", "yellow")
            else:
                self.update_status_display("client", "No API Key", "red")

        def network_status_loop(self):
            """网络状态检查循环"""
            while not self.network_thread_stop:
                try:
                    # 测量网络延迟
                    import socket
                    import time
                    
                    start_time = time.time()
                    socket.create_connection(("api.deepseek.com", 443), timeout=5)
                    end_time = time.time()
                    
                    # 计算延迟（毫秒）
                    latency_ms = round((end_time - start_time) * 1000, 1)
                    
                    # 根据延迟确定状态颜色
                    if latency_ms < 200:
                        color = "green"
                    elif latency_ms < 500:
                        color = "yellow"
                    else:
                        color = "red"
                    
                    status_text = f"Connected ({latency_ms}ms)"
                    
                    # 修复lambda闭包问题 - 使用函数而不是lambda
                    def update_network_status(text, c):
                        self.update_status_display("network", text, c)
                    
                    self.master.after(0, lambda: update_network_status(status_text, color))
                    
                except socket.timeout:
                    self.master.after(0, lambda: self.update_status_display("network", "Timeout", "red"))
                except Exception:
                    self.master.after(0, lambda: self.update_status_display("network", "Disconnected", "red"))
                
                # 等待30秒再次检查
                for _ in range(30):
                    if self.network_thread_stop:
                        break
                    time.sleep(1)

        def update_model_status(self, status=None):
            """更新模型状态"""
            if not self.client:
                self.update_status_display("model", "Not available", "red")
            elif status == "fetch_fail":
                self.update_status_display("model", "Failed to fetch", "yellow")
            elif self.selected_model:
                self.update_status_display("model", f"Selected: {self.selected_model}", "green")
            elif self.available_models:
                self.update_status_display("model", "Available (none selected)", "red")
            else:
                self.update_status_display("model", "Not selected", "red")

        def update_network_status(self):
            """更新网络状态"""
            self.update_status_display("network", "Checking...", "gray")

        def update_http_status(self, status_code=None):
            """更新HTTP状态"""
            if status_code is None:
                # 默认状态设为绿色
                self.update_status_display("http", "OK", "green")
            elif status_code == 200:
                self.update_status_display("http", "OK (200)", "green")
            elif 400 <= status_code <= 499:
                self.update_status_display("http", f"Client Error ({status_code})", "red")
            elif 500 <= status_code <= 599:
                self.update_status_display("http", f"Server Error ({status_code})", "yellow")
            elif status_code == 0:
                self.update_status_display("http", "Network Error", "red")
            else:
                self.update_status_display("http", f"Status {status_code}", "yellow")

        def update_chat_status(self, status):
            """更新聊天状态"""
            status_map = {
                "not_ready": ("Not ready", "red"),
                "ready": ("Ready", "green"),
                "chatting": ("Chatting", "yellow"),
                "streaming": ("Streaming", "yellow")
            }
            text, color = status_map.get(status, ("Unknown", "gray"))
            self.update_status_display("chat", text, color)

        def update_buttons_state(self):
            """更新按钮状态"""
            # 检查是否可以开始聊天
            can_chat = bool(self.client and self.selected_model)
            
            # 更新聊天相关按钮状态
            if hasattr(self, 'chat_btn'):
                self.chat_btn.config(state=tk.NORMAL if can_chat else tk.DISABLED)
            
            if hasattr(self, 'new_btn'):
                self.new_btn.config(state=tk.NORMAL if can_chat else tk.DISABLED)
            
            # 发送按钮状态（需要同时检查输入框内容）
            if hasattr(self, 'send_btn'):
                content = ""
                try:
                    content = self.user_input.get("1.0", tk.END).strip()
                except:
                    pass
                send_enabled = can_chat and bool(content)
                self.send_btn.config(state=tk.NORMAL if send_enabled else tk.DISABLED)

        def query_balance(self):
            """查询余额"""
            if not self.client or not self.api_key:
                messagebox.showerror("Error", "Please initialize client first")
                return
                
            try:
                self.print_out("Querying account balance...")
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json"
                }
                response = requests.get(DEEPSEEK_BALANCE_URL, headers=headers, timeout=10)
                
                # 更新HTTP状态
                self.update_http_status(response.status_code)
                
                if response.status_code == 200:
                    balance_data = response.json()
                    
                    # 检查服务可用性
                    if balance_data.get("is_available", False):
                        self.print_out("Service Available: Yes")
                        balance_infos_list = balance_data.get("balance_infos", [])
                        
                        if balance_infos_list:
                            for idx, info in enumerate(balance_infos_list):
                                self.print_out(f"Balance Info #{idx+1}:")
                                self.print_out(f"  Currency: {info.get('currency', 'N/A')}")
                                self.print_out(f"  Total Balance: {info.get('total_balance', 'N/A')}")
                                self.print_out(f"  Granted Balance: {info.get('granted_balance', 'N/A')}")
                                self.print_out(f"  Topped-up Balance: {info.get('topped_up_balance', 'N/A')}")
                                
                            # 在输出区域显示主要余额信息，不使用弹窗
                            main_balance = balance_infos_list[0].get('total_balance', 'N/A')
                            currency = balance_infos_list[0].get('currency', 'USD')
                            self.print_out(f"**Total Balance: {main_balance} {currency}**")
                        else:
                            self.print_out("No detailed balance information found.")
                    else:
                        self.print_out("Service Available: No")
                        if "message" in balance_data:
                            self.print_out(f"API Message: {balance_data['message']}")
                        else:
                            self.print_out("Service not available - possibly due to service unavailability or no balance info.")
                else:
                    # 处理非200状态码
                    error_msg = f"HTTP {response.status_code}"
                    self.print_out(f"Failed to query balance: {error_msg}")
                    
                    try:
                        error_details = response.json()
                        if "message" in error_details:
                            error_msg += f" - {error_details['message']}"
                        self.print_out(f"Error details: {json.dumps(error_details, indent=2, ensure_ascii=False)}")
                    except json.JSONDecodeError:
                        self.print_out(f"Response content: {response.text}")
                    
            except requests.exceptions.HTTPError as http_err:
                code = http_err.response.status_code if http_err.response is not None else None
                self.update_http_status(code)
                error_msg = f"HTTP error: {http_err}"
                self.print_out(error_msg)
                
                if http_err.response is not None:
                    self.print_out(f"Status code: {http_err.response.status_code}")
                    try:
                        error_details = http_err.response.json()
                        self.print_out(f"Error details: {json.dumps(error_details, indent=2, ensure_ascii=False)}")
                    except json.JSONDecodeError:
                        self.print_out(f"Response content: {http_err.response.text}")
                
            except requests.exceptions.RequestException as e:
                self.update_http_status(0)
                error_msg = f"Request failed: {e}"
                self.print_out(error_msg)
                
            except json.JSONDecodeError:
                self.update_http_status(0)
                error_msg = "Balance response is not valid JSON."
                self.print_out(error_msg)
                
            except Exception as e:
                self.update_http_status(0)
                error_msg = f"Unknown error: {e}"
                self.print_out(error_msg)

        def clear_output(self):
            """清空输出区域"""
            if hasattr(self.output, 'clear_all'):
                self.output.clear_all()
            else:
                self.output.delete(1.0, tk.END)

        def toggle_markdown_rendering(self):
            """切换Markdown渲染"""
            self.markdown_enabled = not self.markdown_enabled
            status_text = "ON" if self.markdown_enabled else "OFF"
            self.markdown_btn.config(text=f"Markdown: {status_text}")
            
            # 立即切换当前输出的渲染模式
            if hasattr(self.output, 'switch_render_mode'):
                self.output.switch_render_mode(self.markdown_enabled)
            
            self.print_out(f"Markdown rendering: {status_text}")

        def print_out(self, message, end="\n"):
            """输出信息到输出区域"""
            if not hasattr(self, 'output'):
                return
                
            # 添加时间戳
            import datetime
            timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
            full_message = timestamp + str(message)
            
            # 使用新的渲染方法
            if hasattr(self.output, 'append_and_render'):
                self.output.append_and_render(full_message, end, self.markdown_enabled)
            else:
                # 回退到普通文本模式
                self.output.insert(tk.END, full_message + end)
                self.output.see(tk.END)

        def send_user_input(self, event=None):
            """发送用户输入"""
            if event and event.keysym == "Return" and not (event.state & 0x4):  # 不是Ctrl+Enter
                # 检查是否按下了Shift
                if event.state & 0x1:  # Shift+Enter，插入换行
                    return "break"
            
            user_message = self.user_input.get("1.0", tk.END).strip()
            if not user_message:
                return "break"
                
            if not self.client or not self.selected_model:
                messagebox.showerror("Error", "Please initialize client and select model first")
                return "break"
                
            # 清空输入框
            self.user_input.delete("1.0", tk.END)
            
            # 添加用户消息到对话历史
            self.messages.append({"role": "user", "content": user_message})
            
            # 显示用户输入
            self.print_out(f"You: {user_message}")
            
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
                self.master.after(0, lambda: self.print_out("Assistant: ", end=""))
                
                for chunk in response:
                    if self.streaming_stopped:
                        break
                        
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        assistant_message += content
                        # 在主线程中更新UI
                        self.master.after(0, lambda c=content: self._append_streaming_content(c))
                
                if not self.streaming_stopped:
                    # 添加助手回复到对话历史
                    self.messages.append({"role": "assistant", "content": assistant_message})
                    self.master.after(0, lambda: self.print_out("", end="\n"))  # 换行
                    
            except Exception as e:
                error_msg = f"Streaming chat error: {str(e)}"
                self.master.after(0, lambda: self.print_out(error_msg))
                
            finally:
                # 恢复按钮状态
                self.master.after(0, self._restore_chat_buttons)

        def _append_streaming_content(self, content):
            """在主线程中追加流式内容"""
            if hasattr(self.output, 'append_raw_text'):
                self.output.append_raw_text(content, end="")
                # 根据当前渲染模式重新渲染
                if self.markdown_enabled:
                    self.output.render_as_markdown()
                else:
                    self.output.render_as_plain_text()
            else:
                self.output.insert(tk.END, content)
                self.output.see(tk.END)

        def _restore_chat_buttons(self):
            """恢复聊天按钮状态"""
            self.send_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.update_chat_status("ready")

        def stop_streaming(self):
            """停止流式输出"""
            self.streaming_stopped = True
            self.print_out("Streaming stopped by user.")
            self._restore_chat_buttons()

        def start_new_session(self):
            """开始新会话"""
            self.messages = []
            self.print_out("Started new chat session.")
            if self.selected_model:
                self.print_out(f"Current model: {self.selected_model}")

        def end_chat(self):
            """结束聊天"""
            self.messages = []
            self.user_input.config(state=tk.DISABLED)
            self.update_chat_status("not_ready")
            self.update_buttons_state()
            self.print_out("Chat ended.")

        def on_input_change(self, event=None):
            """输入框内容改变事件"""
            # 检查输入框是否有内容来控制发送按钮
            content = ""
            try:
                content = self.user_input.get("1.0", tk.END).strip()
            except:
                pass
            
            if content and self.client and self.selected_model:
                self.send_btn.config(state=tk.NORMAL)
            else:
                self.send_btn.config(state=tk.DISABLED)
            
            # 更新客户端状态（检查API Key输入）
            self.update_client_status()

        def on_api_key_change(self, event=None):
            """API Key输入框内容改变事件"""
            self.update_client_status()

        # ========== 字体大小调节方法 ==========
        def decrease_font_size(self):
            """减小字体大小"""
            if self.output_font_size > 8:
                self.output_font_size -= 1
                self.update_output_font()

        def increase_font_size(self):
            """增大字体大小"""
            if self.output_font_size < 24:
                self.output_font_size += 1
                self.update_output_font()

        def set_font_size_from_entry(self, event=None):
            """从输入框设置字体大小"""
            try:
                new_size = self.font_size_var.get()
                if 8 <= new_size <= 24:
                    self.output_font_size = new_size
                    self.update_output_font()
                else:
                    # 如果输入的大小超出范围，恢复为当前大小
                    self.font_size_var.set(self.output_font_size)
            except tk.TclError:
                # 如果输入的不是数字，恢复为当前大小
                self.font_size_var.set(self.output_font_size)

        def update_output_font(self):
            """更新输出区域字体"""
            try:
                # 更新字体大小变量显示
                self.font_size_var.set(self.output_font_size)
                
                # 更新输出区域字体
                new_font = (self.output_font_family, self.output_font_size)
                self.output.config(font=new_font)
                
                # 如果是MarkdownText，还需要更新Markdown样式字体
                if hasattr(self.output, 'update_markdown_font'):
                    self.output.update_markdown_font(self.output_font_family, self.output_font_size)
                    # 重新渲染以应用新字体
                    if self.markdown_enabled:
                        self.output.render_as_markdown()
                    else:
                        self.output.render_as_plain_text()
                        
            except Exception as e:
                print(f"Error updating font: {e}")

# ===================== CLI 部分 =====================
class DeepSeekCLI:
    """命令行版本的DeepSeek客户端"""
    def __init__(self):
        self.api_key = ""
        self.client = None
        self.selected_model = None
        self.messages = []
        self.available_models = []

    def load_api_key(self):
        """加载API密钥"""
        # 首先尝试从文件加载
        saved_key = load_api_key_from_file()
        if saved_key:
            self.api_key = saved_key
            return True
        
        # 如果没有保存的密钥，提示用户输入
        while not self.api_key:
            self.api_key = input("Please enter your DeepSeek API key: ").strip()
            if self.api_key:
                # 询问是否保存
                save_choice = input("Save API key for future use? (y/n): ").strip().lower()
                if save_choice == 'y':
                    if save_api_key_to_file(self.api_key):
                        print("API key saved successfully.")
                    else:
                        print("Failed to save API key.")
                return True
        return False

    def initialize_client(self):
        """初始化客户端"""
        try:
            self.client = OpenAI(api_key=self.api_key, base_url=DEEPSEEK_API_BASE_URL_V1)
            print("Client initialized successfully!")
            return True
        except Exception as e:
            print(f"Failed to initialize client: {e}")
            return False

    def fetch_models(self):
        """获取可用模型"""
        try:
            print("Fetching available models...")
            models_response = self.client.models.list()
            
            # 过滤模型
            available_models = [model.id for model in models_response.data if
                              "chat" in model.id.lower() or "coder" in model.id.lower() or len(models_response.data) < 10]
            
            if not available_models:
                available_models = [model.id for model in models_response.data]
            
            self.available_models = available_models
            print(f"Found {len(available_models)} models:")
            for i, model in enumerate(available_models, 1):
                print(f"  {i}. {model}")
            
            return True
        except Exception as e:
            print(f"Failed to fetch models: {e}")
            return False

    def select_model(self):
        """选择模型"""
        while True:
            try:
                choice = input(f"Select a model (1-{len(self.available_models)}): ").strip()
                model_index = int(choice) - 1
                if 0 <= model_index < len(self.available_models):
                    self.selected_model = self.available_models[model_index]
                    print(f"Selected model: {self.selected_model}")
                    return True
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
            except KeyboardInterrupt:
                print("\nExiting...")
                return False

    def start_chat(self):
        """开始聊天会话"""
        print(f"Starting chat with {self.selected_model}")
        print("Type 'quit' to exit, 'new' to start a new session")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'new':
                    self.messages = []
                    print("Started new chat session.")
                    continue
                elif not user_input:
                    continue
                
                # 添加用户消息
                self.messages.append({"role": "user", "content": user_input})
                
                # 获取AI回复
                print("Assistant: ", end="", flush=True)
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
                
                # 添加助手回复到对话历史
                self.messages.append({"role": "assistant", "content": assistant_message})
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

    def run(self):
        """运行CLI版本"""
        print("DeepSeek CLI Client v0.7.2")
        print("=" * 30)
        
        # 加载API密钥
        if not self.load_api_key():
            return
        
        # 初始化客户端
        if not self.initialize_client():
            return
        
        # 获取模型列表
        if not self.fetch_models():
            return
        
        # 选择模型
        if not self.select_model():
            return
        
        # 开始聊天
        self.start_chat()

# ===================== 主程序入口 =====================
def main():
    if USE_GUI:
        root = tk.Tk()
        app = DeepSeekGUI(root)
        
        # 设置窗口关闭事件
        def on_closing():
            if hasattr(app, 'network_thread_stop'):
                app.network_thread_stop = True
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    else:
        cli = DeepSeekCLI()
        cli.run()

if __name__ == "__main__":
    main()
