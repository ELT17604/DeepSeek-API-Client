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
# API Key 存储文件名 - 修改路径到用户主目录
API_KEY_DIR = os.path.join(os.path.expanduser("~"), ".DS_API_CLI")
API_KEY_FILENAME = os.path.join(API_KEY_DIR, "API_KEY")

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
        # 确保目录存在
        if not os.path.exists(API_KEY_DIR):
            os.makedirs(API_KEY_DIR)
            
        encrypted = encrypt_api_key(api_key)
        if encrypted:
            with open(API_KEY_FILENAME, "w") as f:
                f.write(encrypted)
            return True
        return False
    except Exception as e:
        print(f"Error saving API key: {e}")
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
        print(f"Error loading API key: {e}")
        return None

def delete_api_key_file():
    """删除存储API密钥的文件"""
    if os.path.exists(API_KEY_FILENAME):
        try:
            os.remove(API_KEY_FILENAME)
            return True
        except Exception as e:
            print(f"Error deleting API key file: {e}")
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
            self.status_var = tk.StringVar(value=f"{label_text}: 未初始化")
            
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
            master.title("DeepSeek API 客户端 GUI")

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

            self.api_label = tk.Label(self.api_frame, text="API密钥:", font=("Arial", 10))
            self.api_label.pack(side=tk.LEFT)

            self.api_key_entry = tk.Entry(self.api_frame, show="*", font=("Arial", 10))
            self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
            # 移除不存在的方法绑定，或者添加该方法
            # self.api_key_entry.bind("<KeyRelease>", self.on_api_key_change)

            # 尝试加载保存的API Key
            saved_key = load_api_key_from_file()
            if saved_key:
                self.api_key_entry.insert(0, saved_key)
                # 不要在这里自动初始化，让用户手动点击Initialize按钮

            self.init_btn = tk.Button(self.api_frame, text="初始化", command=self.initialize_client)
            self.init_btn.pack(side=tk.RIGHT, padx=(5, 0))

            self.api_key_masked_label = tk.Label(self.api_frame, text="", font=("Arial", 10))

            # ========== 模型选择区域 ==========
            self.model_frame = tk.Frame(master)
            self.model_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

            self.model_label = tk.Label(self.model_frame, text="模型:", font=("Arial", 10))
            self.model_label.pack(side=tk.LEFT)

            # 初始化时的模型变量设置
            self.model_var = tk.StringVar(value="请选择一个模型...")
            self.model_combobox = ttk.Combobox(self.model_frame, textvariable=self.model_var, 
                                               state="readonly", font=("Arial", 10), width=30)
            self.model_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
            self.model_combobox.bind("<<ComboboxSelected>>", self.on_model_selected)

            self.refresh_models_btn = tk.Button(self.model_frame, text="刷新模型", 
                                                command=self.refresh_models, state=tk.DISABLED)
            self.refresh_models_btn.pack(side=tk.RIGHT)

            # ========== 控制按钮区域 ==========
            self.control_frame = tk.Frame(master)
            self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

            self.balance_btn = tk.Button(self.control_frame, text="查询余额", command=self.query_balance, state=tk.DISABLED)
            self.balance_btn.pack(side=tk.LEFT, padx=(0, 5))

            # 修改：Start Chat 按钮初始状态为不可用
            self.chat_btn = tk.Button(self.control_frame, text="开始聊天", command=self.start_chat, state=tk.DISABLED)
            self.chat_btn.pack(side=tk.LEFT, padx=(0, 5))

            self.clear_btn = tk.Button(self.control_frame, text="清空输出", command=self.clear_output)
            self.clear_btn.pack(side=tk.LEFT, padx=(0, 5))

            # 新增：Markdown渲染切换按钮
            self.markdown_enabled = True  # 默认启用Markdown渲染
            self.markdown_btn = tk.Button(self.control_frame, text="Markdown: 开", command=self.toggle_markdown_rendering)
            self.markdown_btn.pack(side=tk.LEFT, padx=(0, 5))

            # 右侧状态监控按钮
            self.status_btn = tk.Button(self.control_frame, text="状态监控", command=self.toggle_status_window)
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

            self.input_label = tk.Label(self.input_frame, text="您:", font=("Arial", 10))
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

            self.send_btn = tk.Button(self.input_btn_frame, text="发送", command=self.send_user_input, state=tk.DISABLED)
            self.send_btn.pack(side=tk.RIGHT, padx=(5, 0))

            # 添加停止按钮
            self.stop_btn = tk.Button(self.input_btn_frame, text="停止", command=self.stop_streaming, state=tk.DISABLED)
            self.stop_btn.pack(side=tk.RIGHT, padx=(5, 0))

            self.new_btn = tk.Button(self.input_btn_frame, text="新会话", command=self.start_new_session, state=tk.DISABLED)
            self.new_btn.pack(side=tk.RIGHT, padx=(5, 0))

            self.end_btn = tk.Button(self.input_btn_frame, text="结束聊天", command=self.end_chat, state=tk.NORMAL)
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

            self.clear_apikey_btn = tk.Button(self.api_manage_frame, text="清除API密钥", command=self.clear_api_key, state=tk.DISABLED)
            self.clear_apikey_btn.pack(side=tk.LEFT)

            # ========== 独立状态监控窗口相关 ==========
            self.status_window = None
            self.status_indicators = {}

            # 初始化状态监控数据
            self.status_data = {
                "client": {"text": "无API密钥", "color": "red"},
                "network": {"text": "检查中...", "color": "gray"},
                "model": {"text": "未选择", "color": "red"},
                "http": {"text": "正常", "color": "green"},  # 默认HTTP状态设为绿色
                "chat": {"text": "未就绪", "color": "red"}
            }

            # 初始化状态
            self.update_client_status()
            self.update_network_status()
            self.update_model_status()
            self.update_http_status()
            self.update_chat_status("not_ready")
            # 确保按钮状态正确初始化
            self.update_buttons_state()

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

        def show_http_error_dialog(self, status_code, operation, details=None):
            """显示HTTP错误对话框"""
            title = f"HTTP错误: {status_code} ({operation})"
            message = f"在操作 '{operation}' 期间发生HTTP错误。\n状态码: {status_code}\n\n"
            
            error_map = {
                400: "请求格式错误 (Bad Request)。请检查您的请求参数。",
                401: "API密钥无效或未授权 (Unauthorized)。请检查您的API密钥是否正确且有权限访问该服务。",
                402: "余额不足 (Payment Required)。您的账户余额可能不足以完成此操作。",
                403: "禁止访问 (Forbidden)。您没有权限执行此操作。",
                404: "未找到资源 (Not Found)。请求的资源不存在。",
                422: "无法处理的实体 (Unprocessable Entity)。通常表示请求参数不符合API要求。",
                429: "请求过于频繁 (Too Many Requests)。请稍后再试。",
                500: "服务器内部错误 (Internal Server Error)。请稍后再试。",
                502: "网关错误 (Bad Gateway)。上游服务器返回无效响应。",
                503: "服务不可用 (Service Unavailable)。服务器当前无法处理请求，请稍后再试。"
            }
            
            message += error_map.get(status_code, "发生未知HTTP错误。")
            
            if details:
                try:
                    # 尝试格式化JSON细节
                    if isinstance(details, str):
                        details_obj = json.loads(details)
                        details_str = json.dumps(details_obj, indent=2, ensure_ascii=False)
                    elif isinstance(details, dict):
                        details_str = json.dumps(details, indent=2, ensure_ascii=False)
                    else:
                        details_str = str(details)
                    message += f"\n\n详细信息:\n{details_str}"
                except Exception:
                    message += f"\n\n详细信息:\n{details}"
            
            messagebox.showerror(title, message)

        def toggle_status_window(self):
            """切换状态监控窗口的显示/隐藏"""
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

        def on_status_window_close(self):
            """状态窗口关闭时的处理"""
            self.status_window = None
            self.status_btn.config(text="状态监控")

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
                messagebox.showerror("错误", "请输入API密钥")
                return

            try:
                # 更新状态为初始化中
                self.update_status_display("client", "初始化中...", "yellow")
                
                # 创建客户端
                test_client = OpenAI(api_key=api_key, base_url=DEEPSEEK_API_BASE_URL_V1)
                
                # 测试客户端连接 - 尝试获取模型列表来验证API Key
                self.print_out("正在测试客户端连接...")
                try:
                    models_response = test_client.models.list()
                    # 如果成功获取模型列表，说明初始化成功
                    self.update_http_status(200, "初始化")
                    
                except Exception as test_error:
                    # 解析测试连接时的HTTP错误
                    error_msg = str(test_error)
                    
                    # 尝试从错误消息中提取HTTP状态码
                    import re
                    status_match = re.search(r'status_code:\s*(\d+)', error_msg)
                    if status_match:
                        status_code = int(status_match.group(1))
                        self.update_http_status(status_code, "初始化")
                        
                        # 显示HTTP错误对话框
                        self.show_http_error_dialog(status_code, "客户端初始化")
                        
                        # 更新客户端状态为初始化失败
                        self.update_status_display("client", "初始化失败", "red")
                        self.print_out(f"客户端初始化失败: HTTP {status_code}")
                        return
                    else:
                        # 根据错误类型推断状态码
                        if "401" in error_msg or "Unauthorized" in error_msg:
                            self.update_http_status(401, "初始化")
                            self.show_http_error_dialog(401, "客户端初始化")
                            status_text = "认证失败"
                        elif "403" in error_msg or "Forbidden" in error_msg:
                            self.update_http_status(403, "初始化")
                            self.show_http_error_dialog(403, "客户端初始化")
                            status_text = "访问被禁"
                        elif "429" in error_msg or "rate" in error_msg.lower():
                            self.update_http_status(429, "初始化")
                            self.show_http_error_dialog(429, "客户端初始化")
                            status_text = "请求限制"
                        elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                            self.update_http_status(0, "初始化")
                            status_text = "网络错误"
                            self.print_out(f"初始化时网络错误: {error_msg}")
                        else:
                            self.update_http_status(0, "初始化")
                            status_text = "未知错误"
                            self.print_out(f"初始化时未知错误: {error_msg}")
                        
                        # 更新客户端状态为初始化失败
                        self.update_status_display("client", status_text, "red")
                        self.print_out(f"客户端初始化失败: {status_text}")
                        return
                        
                # 如果测试连接成功，设置客户端
                self.client = test_client
                self.api_key = api_key
                
                # 保存API Key
                if save_api_key_to_file(api_key):
                    self.print_out("API Key已安全加密并保存到本地文件。")
                
                # 隐藏输入框，显示掩码标签
                self.api_key_entry.pack_forget()
                
                # 改进的掩码显示逻辑：前后各显示2位明文
                masked_key = self.mask_api_key(api_key)
                self.api_key_masked_label.config(text=masked_key, anchor="w")  # 左对齐
                self.api_key_masked_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
                
                # 将初始化按钮改为修改按钮
                self.init_btn.config(text="修改", command=self.change_api_key)
                
                # 启用相关功能
                self.refresh_models_btn.config(state=tk.NORMAL)
                self.clear_apikey_btn.config(state=tk.NORMAL)
                
                # 更新状态
                self.update_client_status()
                self.print_out("客户端初始化成功!")
                self.update_buttons_state()
                
                # 自动刷新模型列表（使用已验证的客户端）
                self.refresh_models()
                
            except Exception as e:
                # 捕获其他初始化异常
                error_msg = str(e)
                self.update_http_status(0, "初始化")
                self.update_status_display("client", "初始化失败", "red")
                
                # 恢复API Key输入框状态
                self.api_key_entry.config(state=tk.NORMAL)
                self.init_btn.config(state=tk.NORMAL, text="初始化")
                
                messagebox.showerror("错误", f"客户端初始化失败: {error_msg}")
                self.print_out(f"客户端初始化失败: {error_msg}")
                self.update_buttons_state()

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

        def mask_api_key(self, api_key):
            """掩码API Key，前后各保留2位明文"""
            if not api_key:
                return ""
            if len(api_key) <= 4:
                return "*" * len(api_key)  # 如果长度小于等于4，全部掩码
            return api_key[:2] + "*" * (len(api_key) - 4) + api_key[-2:]

        def update_buttons_state(self):
            """更新按钮状态"""
            # Query Balance 按钮：只要客户端初始化完成就可用
            if hasattr(self, 'balance_btn'):
                can_query_balance = bool(self.client)
                self.balance_btn.config(state=tk.NORMAL if can_query_balance else tk.DISABLED)

            # Start Chat 按钮：只有客户端初始化且模型已选择才可用
            if hasattr(self, 'chat_btn'):
                can_start_chat = bool(self.client and self.selected_model)
                self.chat_btn.config(state=tk.NORMAL if can_start_chat else tk.DISABLED)

            # New Session 按钮依然依赖模型和客户端
            if hasattr(self, 'new_btn'):
                can_new = bool(self.client and self.selected_model)
                self.new_btn.config(state=tk.NORMAL if can_new else tk.DISABLED)

            # 发送按钮状态（需要同时检查输入框内容和模型、客户端）
            if hasattr(self, 'send_btn'):
                content = ""
                try:
                    content = self.user_input.get("1.0", tk.END).strip()
                except:
                    pass
                send_enabled = bool(self.client and self.selected_model and content)
                self.send_btn.config(state=tk.NORMAL if send_enabled else tk.DISABLED)

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
                    
                    status_text = f"已连接 ({latency_ms}ms)"
                    
                    # 修复lambda闭包问题 - 使用函数而不是lambda
                    def update_network_status(text, c):
                        self.update_status_display("network", text, c)
                    
                    self.master.after(0, lambda: update_network_status(status_text, color))
                    
                    # 网络连接成功时也更新HTTP状态为连接正常
                    self.master.after(0, lambda: self.update_http_status(200, "网络"))
                    
                except socket.timeout:
                    self.master.after(0, lambda: self.update_status_display("network", "超时", "red"))
                    self.master.after(0, lambda: self.update_http_status(0, "网络"))
                except Exception:
                    self.master.after(0, lambda: self.update_status_display("network", "已断开", "red"))
                    self.master.after(0, lambda: self.update_http_status(0, "网络"))
                
                # 等待30秒再次检查
                for _ in range(30):
                    if self.network_thread_stop:
                        break
                    time.sleep(1)

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
            self.update_status_display("network", "检查中...", "gray")

        def update_http_status(self, status_code=None, operation=None):
            """更新HTTP状态"""
            if status_code is None:
                # 默认状态设为绿色
                self.update_status_display("http", "OK", "green")
            elif status_code == 200:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"正常 (200){operation_text}", "green")
            elif status_code == 400:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"格式错误 (400){operation_text}", "red")
            elif status_code == 401:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"认证失败 (401){operation_text}", "red")
            elif status_code == 402:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"余额不足 (402){operation_text}", "red")
            elif status_code == 403:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"访问被禁 (403){operation_text}", "red")
            elif status_code == 404:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"未找到 (404){operation_text}", "red")
            elif status_code == 422:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"参数错误 (422){operation_text}", "red")
            elif status_code == 429:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"请求限制 (429){operation_text}", "red")
            elif status_code == 500:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"服务器错误 (500){operation_text}", "yellow")
            elif status_code == 502:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"网关错误 (502){operation_text}", "yellow")
            elif status_code == 503:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"服务器繁忙 (503){operation_text}", "yellow")
            elif 400 <= status_code <= 499:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"客户端错误 ({status_code}){operation_text}", "red")
            elif 500 <= status_code <= 599:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"服务器错误 ({status_code}){operation_text}", "yellow")
            elif status_code == 0:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"网络错误{operation_text}", "red")
            else:
                operation_text = f" ({operation})" if operation else ""
                self.update_status_display("http", f"状态 {status_code}{operation_text}", "yellow")

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

        def update_buttons_state(self):
            """更新按钮状态"""
            # Query Balance 按钮：只要客户端初始化完成就可用
            if hasattr(self, 'balance_btn'):
                can_query_balance = bool(self.client)
                self.balance_btn.config(state=tk.NORMAL if can_query_balance else tk.DISABLED)

            # Start Chat 按钮：只有客户端初始化且模型已选择才可用
            if hasattr(self, 'chat_btn'):
                can_start_chat = bool(self.client and self.selected_model)
                self.chat_btn.config(state=tk.NORMAL if can_start_chat else tk.DISABLED)

            # New Session 按钮依然依赖模型和客户端
            if hasattr(self, 'new_btn'):
                can_new = bool(self.client and self.selected_model)
                self.new_btn.config(state=tk.NORMAL if can_new else tk.DISABLED)

            # 发送按钮状态（需要同时检查输入框内容和模型、客户端）
            if hasattr(self, 'send_btn'):
                content = ""
                try:
                    content = self.user_input.get("1.0", tk.END).strip()
                except:
                    pass
                send_enabled = bool(self.client and self.selected_model and content)
                self.send_btn.config(state=tk.NORMAL if send_enabled else tk.DISABLED)

        def query_balance(self):
            """查询余额"""
            if not self.client or not self.api_key:
                messagebox.showerror("错误", "请先初始化客户端")
                return
                
            try:
                self.print_out("正在查询账户余额...")
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json"
                }
                response = requests.get(DEEPSEEK_BALANCE_URL, headers=headers, timeout=10)
                
                # 更新HTTP状态
                self.update_http_status(response.status_code, "余额查询")
                
                if response.status_code == 200:
                    balance_data = response.json()
                    
                    # 检查服务可用性
                    if balance_data.get("is_available", False):
                        self.print_out("服务可用: 是")
                        balance_infos_list = balance_data.get("balance_infos", [])
                        
                        if balance_infos_list:
                            for idx, info in enumerate(balance_infos_list):
                                self.print_out(f"余额信息 #{idx+1}:")
                                self.print_out(f"  货币: {info.get('currency', 'N/A')}")
                                self.print_out(f"  总余额: {info.get('total_balance', 'N/A')}")
                                self.print_out(f"  授权余额: {info.get('granted_balance', 'N/A')}")
                                self.print_out(f"  充值余额: {info.get('topped_up_balance', 'N/A')}")
                                
                            # 在输出区域显示主要余额信息，不使用弹窗
                            main_balance = balance_infos_list[0].get('total_balance', 'N/A')
                            currency = balance_infos_list[0].get('currency', 'USD')
                            self.print_out(f"**总余额: {main_balance} {currency}**")
                        else:
                            self.print_out("未找到详细余额信息。")
                    else:
                        self.print_out("服务可用: 否")
                        if "message" in balance_data:
                            self.print_out(f"API消息: {balance_data['message']}")
                        else:
                            self.print_out("服务不可用 - 可能由于服务未开启或没有余额信息。")
                else:
                    # 处理非200状态码 - 弹出错误对话框而不是在输出区域显示JSON
                    self.print_out(f"查询余额失败: HTTP {response.status_code}")
                    
                    try:
                        error_details = response.json()
                        self.show_http_error_dialog(response.status_code, "余额查询", error_details)
                    except json.JSONDecodeError:
                        self.show_http_error_dialog(response.status_code, "余额查询")
                    
            except requests.exceptions.HTTPError as http_err:
                code = http_err.response.status_code if http_err.response is not None else None
                self.update_http_status(code, "余额查询")
                
                if http_err.response is not None:
                    try:
                        error_details = http_err.response.json()
                        self.show_http_error_dialog(http_err.response.status_code, "余额查询", error_details)
                    except json.JSONDecodeError:
                        self.show_http_error_dialog(http_err.response.status_code, "余额查询")
                else:
                    error_msg = f"HTTP error: {http_err}"
                    self.print_out(error_msg)
                
            except requests.exceptions.RequestException as e:
                self.update_http_status(0, "余额查询")
                error_msg = f"请求失败: {e}"
                self.print_out(error_msg)
                
            except json.JSONDecodeError:
                self.update_http_status(0, "余额查询")
                error_msg = "余额响应不是有效的JSON。"
                self.print_out(error_msg)
                
            except Exception as e:
                self.update_http_status(0, "余额查询")
                error_msg = f"未知错误: {e}"
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
            status_text = "开" if self.markdown_enabled else "关"
            self.markdown_btn.config(text=f"Markdown: {status_text}")
            
            # 立即切换当前输出的渲染模式
            if hasattr(self.output, 'switch_render_mode'):
                self.output.switch_render_mode(self.markdown_enabled)
            
            self.print_out(f"Markdown渲染: {status_text}")

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
                
                # 更新HTTP状态 - 聊天请求成功
                self.master.after(0, lambda: self.update_http_status(200, "聊天"))
                
                assistant_message = ""
                self.master.after(0, lambda: self.print_out("助手: ", end=""))
                
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
                # 捕获聊天API的异常并解析HTTP状态
                error_msg = str(e)
                
                # 尝试从错误消息中提取HTTP状态码
                import re
                status_match = re.search(r'status_code:\s*(\d+)', error_msg)
                if status_match:
                    status_code = int(status_match.group(1))
                    self.master.after(0, lambda: self.update_http_status(status_code, "聊天"))
                    self.master.after(0, lambda: self.show_http_error_dialog(status_code, "聊天"))
                else:
                    # 根据错误类型推断状态码
                    if "401" in error_msg or "Unauthorized" in error_msg:
                        self.master.after(0, lambda: self.update_http_status(401, "聊天"))
                        self.master.after(0, lambda: self.show_http_error_dialog(401, "聊天"))
                    elif "403" in error_msg or "Forbidden" in error_msg:
                        self.master.after(0, lambda: self.update_http_status(403, "聊天"))
                        self.master.after(0, lambda: self.show_http_error_dialog(403, "聊天"))
                    elif "429" in error_msg or "rate" in error_msg.lower():
                        self.master.after(0, lambda: self.update_http_status(429, "聊天"))
                        self.master.after(0, lambda: self.show_http_error_dialog(429, "聊天"))
                    elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                        self.master.after(0, lambda: self.update_http_status(0, "聊天"))
                        self.master.after(0, lambda: self.print_out(f"网络错误: {error_msg}"))
                    else:
                        self.master.after(0, lambda: self.update_http_status(0, "聊天"))
                        self.master.after(0, lambda: self.print_out(f"未知错误: {error_msg}"))
                
                self.master.after(0, lambda: self.print_out("聊天发生错误"))
                
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

        def on_api_key_change(self, event=None):
            """API密钥输入框内容改变事件"""
            # 当API密钥输入框内容改变时，更新客户端状态
            self.update_client_status()

        def increase_font_size(self):
            """增加字体大小"""
            if self.output_font_size < 24:  # 设置字体大小上限
                self.output_font_size += 1
                self.update_output_font()

        def decrease_font_size(self):
            """减少字体大小"""
            if self.output_font_size > 8:  # 设置字体大小下限
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
                    self.font_size_var.set(self.output_font_size)  # 恢复到旧值
            except tk.TclError: # 处理无效输入，例如非整数
                messagebox.showerror("错误", "请输入有效的字体大小 (8-24)")
                self.font_size_var.set(self.output_font_size) # 恢复到旧值
            except Exception:
                self.font_size_var.set(self.output_font_size) # 其他异常也恢复

        def update_output_font(self):
            """更新输出区域字体"""
            self.font_size_var.set(self.output_font_size)
            new_font = (self.output_font_family, self.output_font_size)
            
            try:
                self.output.configure(font=new_font)
                if hasattr(self.output, 'update_markdown_font'):
                    self.output.update_markdown_font(self.output_font_family, self.output_font_size)
                # 重新渲染以应用新的字体大小到现有内容
                if hasattr(self.output, 'switch_render_mode'):
                    self.output.switch_render_mode(self.markdown_enabled)

            except Exception as e:
                print(f"更新字体时出错: {e}")

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

        def refresh_models(self):
            """刷新模型列表（GUI版本）"""
            if not self.client:
                messagebox.showerror("错误", "请先初始化客户端")
                return
                
            try:
                self.print_out("正在获取可用模型...")
                models_response = self.client.models.list()
                
                # 更新HTTP状态
                self.update_http_status(200, "模型获取")
                
                # 过滤模型
                available_models = [model.id for model in models_response.data if
                                  "chat" in model.id.lower() or "coder" in model.id.lower() or len(models_response.data) < 10]
                
                if not available_models:
                    available_models = [model.id for model in models_response.data]
                
                if not available_models:
                    self.print_out("未找到模型。请检查您的API密钥。")
                    self.update_model_status("fetch_fail")
                    return
                
                self.available_models = available_models
                self.model_combobox['values'] = available_models
                
                # 如果当前选择的模型不在新列表中，则重置为未选择状态
                if self.selected_model and self.selected_model not in available_models:
                    self.selected_model = None
                    self.model_var.set("请选择一个模型...")
                
                # 更新模型状态
                self.update_model_status()
                
                self.print_out(f"找到 {len(available_models)} 个模型。请选择一个以继续。")
                self.update_buttons_state()
                
            except Exception as e:
                error_msg = str(e)
                
                # 尝试从错误消息中提取HTTP状态码
                import re
                status_match = re.search(r'status_code:\s*(\d+)', error_msg)
                if status_match:
                    status_code = int(status_match.group(1))
                    self.update_http_status(status_code, "模型获取")
                    self.show_http_error_dialog(status_code, "模型获取")
                else:
                    # 根据错误类型推断状态码
                    if "401" in error_msg or "Unauthorized" in error_msg:
                        self.update_http_status(401, "模型获取")
                        self.show_http_error_dialog(401, "模型获取")
                    elif "403" in error_msg or "Forbidden" in error_msg:
                        self.update_http_status(403, "模型获取")
                        self.show_http_error_dialog(403, "模型获取")
                    elif "429" in error_msg or "rate" in error_msg.lower():
                        self.update_http_status(429, "模型获取")
                        self.show_http_error_dialog(429, "模型获取")
                    else:
                        self.update_http_status(0, "模型获取")
                        self.print_out(f"获取模型时发生错误: {error_msg}")
                
                self.print_out(f"获取模型失败: {error_msg}")
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
            """开始聊天（GUI）"""
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

        def clear_api_key(self):
            """清除API密钥"""
            result = messagebox.askyesno("确认", "您确定要清除保存的API密钥吗？")
            if result:
                if delete_api_key_file():
                    self.print_out("API密钥清除成功。")
                    messagebox.showinfo("成功", "API密钥清除成功。")
                else:
                    messagebox.showerror("错误", "清除API密钥失败。")

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
            print("找到保存的API密钥，正在加载...")
            self.api_key = saved_key
            return True
        
        # 如果没有保存的密钥，提示用户输入
        print("未找到保存的API密钥。")
        while not self.api_key:
            self.api_key = input("请输入您的DeepSeek API密钥: ").strip()
            if self.api_key:
                # 询问是否保存
                save_choice = input("是否保存API密钥以供将来使用？ (y/n): ").strip().lower()
                if save_choice == 'y':
                    if save_api_key_to_file(self.api_key):
                        print("API密钥保存成功。")
                    else:
                        print("API密钥保存失败。")
                return True
        return False

    def initialize_client(self):
        """初始化客户端"""
        try:
            self.client = OpenAI(api_key=self.api_key, base_url=DEEPSEEK_API_BASE_URL_V1)
            print("客户端初始化成功!")
            return True
        except Exception as e:
            print(f"客户端初始化失败: {e}")
            return False

    def fetch_models(self):
        """获取可用模型"""
        try:
            print("正在获取可用模型...")
            models_response = self.client.models.list()

            
            # 过滤模型
            available_models = [model.id for model in models_response.data if
                              "chat" in model.id.lower() or "coder" in model.id.lower() or len(models_response.data) < 10]
            
            if not available_models:
                available_models = [model.id for model in models_response.data]
            
            self.available_models = available_models
            print(f"找到 {len(available_models)} 个模型:")
            for i, model in enumerate(available_models, 1):
                print(f"  {i}. {model}")
            
            return True
        except Exception as e:
            print(f"获取模型失败: {e}")
            return False

    def select_model(self):
        """选择模型"""
        while True:
            try:
                choice = input(f"选择一个模型 (1-{len(self.available_models)}): ").strip()
                model_index = int(choice) - 1
                if 0 <= model_index < len(self.available_models):
                    self.selected_model = self.available_models[model_index]
                    print(f"已选择模型: {self.selected_model}")
                    return True
                else:
                    print("无效选择，请重试。")
            except ValueError:
                print("请输入有效数字。")
            except KeyboardInterrupt:
                print("\n正在退出...")
                return False

    def start_chat(self):
        """开始聊天会话"""
        print(f"开始与 {self.selected_model} 聊天")
        print("输入 'quit' 退出，'new' 开始新会话")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("您: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'new':
                    self.messages = []
                    print("开始新聊天会话。")
                    continue
                elif not user_input:
                    continue
                
                # 添加用户消息
                self.messages.append({"role": "user", "content": user_input})
                
                # 获取AI回复
                print("助手: ", end="", flush=True)
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
                print("\n再见!")
                break
            except Exception as e:
                print(f"错误: {e}")

    def run(self):
        """运行CLI版本"""
        print("DeepSeek CLI 客户端 v0.7.2")
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
