/**
 * Markdown 渲染工具
 * 提供与Python GUI应用相同的Markdown渲染功能
 */

class MarkdownRenderer {
    constructor() {
        this.currentContent = '';
        this.isMarkdownEnabled = true;
    }

    /**
     * 渲染Markdown文本为HTML
     * @param {string} text - 要渲染的Markdown文本
     * @returns {string} - 渲染后的HTML
     */
    renderMarkdown(text) {
        if (!text) return '';
        
        let html = '';
        const lines = text.split('\n');
        let inCodeBlock = false;
        let codeBlockContent = [];
        let codeLanguage = '';
        let inList = false;
        let listItems = [];
        let listType = '';

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmedLine = line.trim();

            // 处理代码块
            if (trimmedLine.startsWith('```')) {
                if (!inCodeBlock) {
                    // 开始代码块
                    inCodeBlock = true;
                    codeLanguage = trimmedLine.substring(3).trim();
                    codeBlockContent = [];
                    continue;
                } else {
                    // 结束代码块
                    inCodeBlock = false;
                    html += this.renderCodeBlock(codeBlockContent.join('\n'), codeLanguage);
                    codeBlockContent = [];
                    codeLanguage = '';
                    continue;
                }
            }

            if (inCodeBlock) {
                codeBlockContent.push(line);
                continue;
            }

            // 处理列表结束
            if (inList && !this.isListItem(line)) {
                html += this.renderList(listItems, listType);
                listItems = [];
                inList = false;
                listType = '';
            }

            // 处理标题
            if (trimmedLine.startsWith('#')) {
                html += this.renderHeader(trimmedLine);
                continue;
            }

            // 处理引用块
            if (trimmedLine.startsWith('>')) {
                html += this.renderBlockquote(trimmedLine);
                continue;
            }

            // 处理列表
            if (this.isListItem(line)) {
                const listMatch = line.match(/^(\s*)([-*+]|\d+\.)\s+(.*)$/);
                if (listMatch) {
                    const [, indent, marker, content] = listMatch;
                    const currentListType = /\d+\./.test(marker) ? 'ol' : 'ul';
                    
                    if (!inList) {
                        inList = true;
                        listType = currentListType;
                    }
                    
                    listItems.push({
                        content: this.renderInlineFormatting(content),
                        indent: indent.length
                    });
                }
                continue;
            }

            // 处理水平分割线
            if (/^[-*_]{3,}$/.test(trimmedLine)) {
                html += '<hr class="markdown-hr">';
                continue;
            }

            // 处理空行
            if (trimmedLine === '') {
                html += '<br>';
                continue;
            }

            // 处理普通段落
            html += this.renderParagraph(line);
        }

        // 处理未结束的列表
        if (inList) {
            html += this.renderList(listItems, listType);
        }

        // 处理未结束的代码块
        if (inCodeBlock) {
            html += this.renderCodeBlock(codeBlockContent.join('\n'), codeLanguage);
        }

        return html;
    }

    /**
     * 渲染代码块
     */
    renderCodeBlock(content, language = '') {
        const escapedContent = this.escapeHtml(content);
        const langClass = language ? ` language-${language}` : '';
        return `<pre class="markdown-code-block"><code class="markdown-code${langClass}">${escapedContent}</code></pre>\n`;
    }

    /**
     * 渲染标题
     */
    renderHeader(line) {
        const match = line.match(/^(#{1,6})\s+(.*)$/);
        if (!match) return this.renderParagraph(line);
        
        const [, hashes, content] = match;
        const level = hashes.length;
        const cleanContent = this.renderInlineFormatting(content);
        return `<h${level} class="markdown-h${level}">${cleanContent}</h${level}>\n`;
    }

    /**
     * 渲染引用块
     */
    renderBlockquote(line) {
        const content = line.substring(1).trim();
        const formattedContent = this.renderInlineFormatting(content);
        return `<blockquote class="markdown-blockquote">${formattedContent}</blockquote>\n`;
    }

    /**
     * 渲染列表
     */
    renderList(items, type) {
        if (items.length === 0) return '';
        
        let html = `<${type} class="markdown-list">\n`;
        for (const item of items) {
            html += `<li class="markdown-list-item">${item.content}</li>\n`;
        }
        html += `</${type}>\n`;
        return html;
    }

    /**
     * 检查是否为列表项
     */
    isListItem(line) {
        return /^\s*[-*+]\s+/.test(line) || /^\s*\d+\.\s+/.test(line);
    }

    /**
     * 渲染段落
     */
    renderParagraph(line) {
        const content = this.renderInlineFormatting(line);
        return `<p class="markdown-paragraph">${content}</p>\n`;
    }

    /**
     * 渲染内联格式
     */
    renderInlineFormatting(text) {
        if (!text) return '';

        let result = text;

        // 处理内联代码（最高优先级）
        result = result.replace(/`([^`]+)`/g, '<code class="markdown-inline-code">$1</code>');

        // 处理粗体斜体 ***text***
        result = result.replace(/\*\*\*([^*]+?)\*\*\*/g, '<strong><em class="markdown-bold-italic">$1</em></strong>');

        // 处理粗体 **text**
        result = result.replace(/\*\*([^*]+?)\*\*/g, '<strong class="markdown-bold">$1</strong>');

        // 处理斜体 *text*
        result = result.replace(/\*([^*]+?)\*/g, '<em class="markdown-italic">$1</em>');

        // 处理删除线 ~~text~~
        result = result.replace(/~~([^~]+?)~~/g, '<del class="markdown-strikethrough">$1</del>');

        // 处理链接 [text](url)
        result = result.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="markdown-link" target="_blank">$1</a>');

        return result;
    }

    /**
     * 转义HTML字符
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 设置Markdown渲染状态
     */
    setMarkdownEnabled(enabled) {
        this.isMarkdownEnabled = enabled;
    }

    /**
     * 获取当前渲染状态
     */
    isMarkdownRenderingEnabled() {
        return this.isMarkdownEnabled;
    }

    /**
     * 渲染文本（根据当前状态选择渲染方式）
     */
    render(text) {
        if (this.isMarkdownEnabled) {
            return this.renderMarkdown(text);
        } else {
            return `<pre class="markdown-plain-text">${this.escapeHtml(text)}</pre>`;
        }
    }

    /**
     * 清空当前内容
     */
    clear() {
        this.currentContent = '';
    }

    /**
     * 追加内容
     */
    appendContent(text) {
        this.currentContent += text;
        return this.render(this.currentContent);
    }

    /**
     * 设置内容
     */
    setContent(text) {
        this.currentContent = text;
        return this.render(this.currentContent);
    }

    /**
     * 获取原始内容
     */
    getRawContent() {
        return this.currentContent;
    }
}

// 创建全局实例
window.markdownRenderer = new MarkdownRenderer();

// 导出函数供其他脚本使用
window.renderMarkdown = function(text) {
    return window.markdownRenderer.render(text);
};

window.setMarkdownEnabled = function(enabled) {
    window.markdownRenderer.setMarkdownEnabled(enabled);
};