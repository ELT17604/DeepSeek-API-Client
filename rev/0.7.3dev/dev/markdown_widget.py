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
from tkinter import scrolledtext, font
import re
from config import FONT_CONFIG

class MarkdownText(scrolledtext.ScrolledText):
    """支持Markdown渲染的文本控件"""
    
    def __init__(self, master, **kwargs):
        """
        初始化Markdown文本控件
        
        Args:
            master: 父控件
            **kwargs: 传递给ScrolledText的其他参数
        """
        super().__init__(master, **kwargs)
        
        # 配置文本样式标签
        self.configure_markdown_tags()
        
        # 当前文本缓冲区 - 存储原始文本内容
        self.raw_content = ""
        
        # 当前渲染模式
        self.markdown_enabled = True
        
    def configure_markdown_tags(self):
        """配置Markdown样式标签"""
        # 获取默认字体 - 修复字体获取问题
        try:
            # 先尝试获取控件的当前字体
            current_font = self.cget("font")
            if isinstance(current_font, tuple):
                # 如果是元组形式 (family, size, style)
                font_family = current_font[0]
                font_size = current_font[1] if len(current_font) > 1 else FONT_CONFIG["default_size"]
            elif isinstance(current_font, str):
                # 如果是字符串形式，尝试解析
                parts = current_font.split()
                if len(parts) >= 2:
                    font_family = parts[0]
                    try:
                        font_size = int(parts[1])
                    except ValueError:
                        font_size = FONT_CONFIG["default_size"]
                else:
                    font_family = current_font
                    font_size = FONT_CONFIG["default_size"]
            else:
                # 使用默认值
                font_family = FONT_CONFIG["default_family"]
                font_size = FONT_CONFIG["default_size"]
                
            # 如果获取的字体不合理，使用系统默认字体
            if not font_family or font_family in ["", "none"]:
                font_family = FONT_CONFIG["default_family"]
                
        except Exception:
            # 如果获取字体失败，使用默认值
            font_family = FONT_CONFIG["default_family"]
            font_size = FONT_CONFIG["default_size"]
        
        # 验证字体大小范围
        min_size = FONT_CONFIG["size_range"]["min"]
        max_size = FONT_CONFIG["size_range"]["max"]
        if not (min_size <= font_size <= max_size):
            font_size = FONT_CONFIG["default_size"]
        
        # 标题样式
        self.tag_configure("h1", 
                          font=(font_family, font_size + 6, "bold"), 
                          foreground="#2E86AB", 
                          spacing1=10, 
                          spacing3=5)
        self.tag_configure("h2", 
                          font=(font_family, font_size + 4, "bold"), 
                          foreground="#A23B72", 
                          spacing1=8, 
                          spacing3=4)
        self.tag_configure("h3", 
                          font=(font_family, font_size + 2, "bold"), 
                          foreground="#F18F01", 
                          spacing1=6, 
                          spacing3=3)
        self.tag_configure("h4", 
                          font=(font_family, font_size + 1, "bold"), 
                          foreground="#C73E1D", 
                          spacing1=4, 
                          spacing3=2)
        
        # 代码块样式 - 使用等宽字体
        code_font_family = self._get_code_font()
        
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
        
        # 链接样式
        self.tag_configure("link",
                         font=(font_family, font_size, "underline"),
                         foreground="#0366d6")
        
        # 删除线样式
        self.tag_configure("strikethrough",
                         font=(font_family, font_size, "normal"),
                         overstrike=True)
        
    def _get_code_font(self):
        """获取可用的代码字体"""
        for font_name in FONT_CONFIG["code_fonts"]:
            try:
                test_font = font.Font(family=font_name, size=FONT_CONFIG["default_size"])
                test_font.actual()  # 测试字体是否可用
                return font_name
            except Exception:
                continue
        # 如果所有字体都不可用，返回默认字体
        return FONT_CONFIG["default_family"]
        
    def update_markdown_font(self, new_font_family, new_font_size):
        """
        更新Markdown样式的字体
        
        Args:
            new_font_family (str): 新字体名称
            new_font_size (int): 新字体大小
        """
        # 验证字体大小范围
        min_size = FONT_CONFIG["size_range"]["min"]
        max_size = FONT_CONFIG["size_range"]["max"]
        if not (min_size <= new_font_size <= max_size):
            print(f"警告: 字体大小 {new_font_size} 超出范围 [{min_size}, {max_size}]")
            return
            
        # 检查代码字体是否可用
        code_font_family = self._get_code_font()
        
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
        self.tag_configure("link", font=(new_font_family, new_font_size, "underline"))
        self.tag_configure("strikethrough", font=(new_font_family, new_font_size, "normal"))
        
    def append_raw_text(self, text, end="\n"):
        """
        追加原始文本到缓冲区
        
        Args:
            text (str): 要追加的文本
            end (str): 结束符，默认为换行符
        """
        self.raw_content += text
        if end:
            self.raw_content += end
            
    def get_raw_content(self):
        """
        获取原始文本内容
        
        Returns:
            str: 原始文本内容
        """
        return self.raw_content
        
    def set_raw_content(self, content):
        """
        设置原始文本内容
        
        Args:
            content (str): 要设置的原始文本内容
        """
        self.raw_content = content
        
    def clear_all(self):
        """清空所有内容"""
        self.raw_content = ""
        self.delete(1.0, tk.END)
        
    def _render_markdown_text(self, text):
        """
        渲染Markdown文本的核心方法
        
        Args:
            text (str): 要渲染的Markdown文本
        """
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
                language = line.strip()[3:].strip()  # 获取语言标识
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
            
            # 处理水平分割线
            if re.match(r'^\s*[-*_]{3,}\s*$', line):
                display_text = '─' * 50 + '\n'  # 使用横线字符
                self.insert(current_pos, display_text)
                end_pos = f"{line_start}+{len(display_text)}c"
                self.tag_add("normal", line_start, end_pos)
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
        """
        处理内联格式并返回处理后的文本和格式信息
        
        Args:
            text (str): 要处理的文本行
            
        Returns:
            dict: 包含处理后文本和格式信息的字典
        """
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
        
        # 2. 处理删除线 ~~text~~
        strikethrough_pattern = r'~~([^~]+?)~~'
        strikethrough_matches = list(re.finditer(strikethrough_pattern, processed_text))
        
        for match in reversed(strikethrough_matches):
            start, end = match.span()
            # 检查是否与代码区域重叠
            if not self._position_in_ranges(start, end, code_ranges, offset):
                content = match.group(1)
                processed_text = processed_text[:start] + content + processed_text[end:]
                formats.append({
                    'start': start,
                    'end': start + len(content),
                    'type': 'strikethrough'
                })
                offset += 4  # 减去四个~符号
        
        # 3. 处理粗体斜体 ***text***
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
        
        # 4. 处理粗体 **text**
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
        
        # 5. 处理斜体 *text*
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
        
        # 6. 处理链接 [text](url)
        link_pattern = r'\[([^\]]+?)\]\([^\)]+?\)'
        link_matches = list(re.finditer(link_pattern, processed_text))
        
        for match in reversed(link_matches):
            start, end = match.span()
            if not self._position_in_ranges(start, end, code_ranges, offset):
                content = match.group(1)  # 只保留链接文本
                processed_text = processed_text[:start] + content + processed_text[end:]
                formats.append({
                    'start': start,
                    'end': start + len(content),
                    'type': 'link'
                })
                offset += len(match.group(0)) - len(content)  # 减去链接标记的长度
        
        return {
            'text': processed_text,
            'formats': formats
        }
    
    def _position_in_ranges(self, start, end, ranges, offset):
        """
        检查位置是否在指定范围内（考虑偏移量）
        
        Args:
            start (int): 开始位置
            end (int): 结束位置
            ranges (list): 范围列表
            offset (int): 偏移量
            
        Returns:
            bool: 如果位置在范围内返回True，否则返回False
        """
        adjusted_start = start + offset
        adjusted_end = end + offset
        
        for range_start, range_end in ranges:
            if (adjusted_start < range_end and adjusted_end > range_start):
                return True
        return False
    
    def _apply_format_tags(self, line_start_pos, formats):
        """
        应用格式标签到文本
        
        Args:
            line_start_pos (str): 行开始位置
            formats (list): 格式信息列表
        """
        for fmt in formats:
            start_pos = f"{line_start_pos}+{fmt['start']}c"
            end_pos = f"{line_start_pos}+{fmt['end']}c"
            self.tag_add(fmt['type'], start_pos, end_pos)
    
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
        
        # 应用普通文本样式
        self.tag_add("normal", 1.0, tk.END)
        
        # 滚动到底部
        self.see(tk.END)
        
    def append_and_render(self, text, end="\n", markdown_enabled=True):
        """
        追加文本并根据模式渲染
        
        Args:
            text (str): 要追加的文本
            end (str): 结束符
            markdown_enabled (bool): 是否启用Markdown渲染
        """
        self.append_raw_text(text, end)
        
        if markdown_enabled:
            self.render_as_markdown()
        else:
            self.render_as_plain_text()
        
    def switch_render_mode(self, markdown_enabled):
        """
        切换渲染模式（保持内容不变）
        
        Args:
            markdown_enabled (bool): 是否启用Markdown渲染
        """
        self.markdown_enabled = markdown_enabled
        
        if markdown_enabled:
            self.render_as_markdown()
        else:
            self.render_as_plain_text()
    
    def export_as_html(self):
        """
        导出为HTML格式
        
        Returns:
            str: HTML格式的文本
        """
        # 简单的Markdown到HTML转换
        html_content = self.raw_content
        
        # 转换标题
        html_content = re.sub(r'^#{4}\s+(.+)$', r'<h4>\1</h4>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^#{3}\s+(.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^#{2}\s+(.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^#{1}\s+(.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
        
        # 转换粗体斜体
        html_content = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html_content)
        html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
        html_content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_content)
        
        # 转换代码
        html_content = re.sub(r'`(.+?)`', r'<code>\1</code>', html_content)
        
        # 转换代码块
        html_content = re.sub(r'```[\s\S]*?\n([\s\S]*?)```', r'<pre><code>\1</code></pre>', html_content)
        
        # 转换链接
        html_content = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html_content)
        
        # 转换删除线
        html_content = re.sub(r'~~(.+?)~~', r'<del>\1</del>', html_content)
        
        # 转换段落
        paragraphs = html_content.split('\n\n')
        html_paragraphs = []
        for p in paragraphs:
            p = p.strip()
            if p:
                if not (p.startswith('<h') or p.startswith('<pre') or p.startswith('<blockquote')):
                    p = f'<p>{p.replace(chr(10), "<br>")}</p>'
                html_paragraphs.append(p)
        
        return '\n'.join(html_paragraphs)
    
    def search_text(self, pattern, case_sensitive=False):
        """
        搜索文本
        
        Args:
            pattern (str): 搜索模式
            case_sensitive (bool): 是否区分大小写
            
        Returns:
            list: 匹配位置列表
        """
        content = self.get_raw_content()
        flags = 0 if case_sensitive else re.IGNORECASE
        
        matches = []
        for match in re.finditer(pattern, content, flags):
            matches.append({
                'start': match.start(),
                'end': match.end(),
                'text': match.group(0)
            })
        
        return matches
    
    def highlight_search_results(self, pattern, case_sensitive=False):
        """
        高亮搜索结果
        
        Args:
            pattern (str): 搜索模式
            case_sensitive (bool): 是否区分大小写
        """
        # 清除之前的搜索高亮
        self.tag_remove("search_highlight", 1.0, tk.END)
        
        # 配置搜索高亮样式
        self.tag_configure("search_highlight", background="yellow", foreground="black")
        
        # 搜索并高亮
        matches = self.search_text(pattern, case_sensitive)
        content = self.get(1.0, tk.END)
        
        for match in matches:
            # 计算在当前显示文本中的位置
            start_pos = f"1.0+{match['start']}c"
            end_pos = f"1.0+{match['end']}c"
            self.tag_add("search_highlight", start_pos, end_pos)
    
    def clear_search_highlights(self):
        """清除搜索高亮"""
        self.tag_remove("search_highlight", 1.0, tk.END)
    
    def get_line_count(self):
        """
        获取行数
        
        Returns:
            int: 行数
        """
        return len(self.raw_content.split('\n'))
    
    def get_word_count(self):
        """
        获取词数
        
        Returns:
            int: 词数
        """
        # 简单的词数统计
        words = re.findall(r'\b\w+\b', self.raw_content)
        return len(words)
    
    def get_character_count(self, include_spaces=True):
        """
        获取字符数
        
        Args:
            include_spaces (bool): 是否包含空格
            
        Returns:
            int: 字符数
        """
        if include_spaces:
            return len(self.raw_content)
        else:
            return len(re.sub(r'\s', '', self.raw_content))
    
    def save_content_to_file(self, filename, format_type="markdown"):
        """
        保存内容到文件
        
        Args:
            filename (str): 文件名
            format_type (str): 格式类型 ("markdown", "html", "plain")
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if format_type == "html":
                    f.write(self.export_as_html())
                elif format_type == "plain":
                    # 移除Markdown标记
                    plain_text = re.sub(r'[#*`~\[\]()_-]', '', self.raw_content)
                    f.write(plain_text)
                else:  # markdown
                    f.write(self.raw_content)
            return True
        except Exception as e:
            print(f"保存文件失败: {e}")
            return False
    
    def load_content_from_file(self, filename):
        """
        从文件加载内容
        
        Args:
            filename (str): 文件名
            
        Returns:
            bool: 加载是否成功
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            self.set_raw_content(content)
            if self.markdown_enabled:
                self.render_as_markdown()
            else:
                self.render_as_plain_text()
            return True
        except Exception as e:
            print(f"加载文件失败: {e}")
            return False
    
    def insert_markdown_template(self, template_type):
        """
        插入Markdown模板
        
        Args:
            template_type (str): 模板类型
        """
        templates = {
            "table": "\n| 列1 | 列2 | 列3 |\n|-----|-----|-----|\n| 行1 | 数据 | 数据 |\n| 行2 | 数据 | 数据 |\n",
            "code_block": "\n```python\n# 在此输入代码\nprint('Hello, World!')\n```\n",
            "quote": "\n> 这是一个引用块\n> 可以包含多行内容\n",
            "list": "\n- 列表项 1\n- 列表项 2\n- 列表项 3\n",
            "numbered_list": "\n1. 第一项\n2. 第二项\n3. 第三项\n",
            "link": "[链接文本](https://example.com)",
            "image": "![图片描述](image_url.jpg)",
            "horizontal_rule": "\n---\n"
        }
        
        template = templates.get(template_type, "")
        if template:
            self.append_raw_text(template)
            if self.markdown_enabled:
                self.render_as_markdown()
            else:
                self.render_as_plain_text()

# 便捷函数
def create_markdown_text(parent, **kwargs):
    """
    创建MarkdownText控件的便捷函数
    
    Args:
        parent: 父控件
        **kwargs: 传递给MarkdownText的参数
        
    Returns:
        MarkdownText: 创建的控件实例
    """
    return MarkdownText(parent, **kwargs)

# 测试和示例代码
if __name__ == "__main__":
    # 创建测试窗口
    root = tk.Tk()
    root.title("Markdown Text Widget Test")
    root.geometry("800x600")
    
    # 创建Markdown文本控件
    markdown_widget = MarkdownText(root, width=80, height=30)
    markdown_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 添加测试内容
    test_content = """# 这是一级标题

## 这是二级标题

### 这是三级标题

这是普通段落，包含**粗体文本**、*斜体文本*和***粗体斜体文本***。

还有`内联代码`和~~删除线文本~~。

> 这是一个引用块
> 可以包含多行内容

- 无序列表项1
- 无序列表项2
- 无序列表项3

1. 有序列表项1
2. 有序列表项2
3. 有序列表项3

这是一个[链接示例](https://example.com)。

```python
# 这是代码块
def hello_world():
    print("Hello, World!")
    return True
```

---

这是分割线上方的内容。
"""
    
    markdown_widget.set_raw_content(test_content)
    markdown_widget.render_as_markdown()
    
    # 创建控制按钮
    button_frame = tk.Frame(root)
    button_frame.pack(fill=tk.X, padx=10, pady=5)
    
    tk.Button(button_frame, text="切换到纯文本", 
              command=lambda: markdown_widget.switch_render_mode(False)).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="切换到Markdown", 
              command=lambda: markdown_widget.switch_render_mode(True)).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="清空内容", 
              command=markdown_widget.clear_all).pack(side=tk.LEFT, padx=5)
    
    root.mainloop()