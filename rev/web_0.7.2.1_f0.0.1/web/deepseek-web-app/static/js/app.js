/**
 * DeepSeek Web Client - 主应用程序
 * 提供与Python GUI应用相同的功能
 */

class DeepSeekWebClient {
    constructor() {
        this.apiKey = '';
        this.selectedModel = '';
        this.availableModels = [];
        this.messages = [];
        this.isStreaming = false;
        this.isMarkdownEnabled = true;
        this.isStreamEnabled = true;
        this.currentFontSize = 14;
        this.currentFontFamily = 'system-ui';
        this.abortController = null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.loadSettings();
        this.checkConnection();
    }

    /**
     * 初始化DOM元素引用
     */
    initializeElements() {
        this.elements = {
            // 状态相关
            statusDot: document.getElementById('status-dot'),
            statusText: document.getElementById('status-text'),
            
            // API密钥相关
            apiKeyInput: document.getElementById('api-key'),
            initBtn: document.getElementById('init-btn'),
            deleteKeyBtn: document.getElementById('delete-key-btn'),
            apiKeyStatus: document.getElementById('api-key-status'),
            balanceInfo: document.getElementById('balance-info'),
            balanceAmount: document.getElementById('balance-amount'),
            
            // 模型选择相关
            modelSelect: document.getElementById('model-select'),
            refreshModelsBtn: document.getElementById('refresh-models-btn'),
            
            // 参数控制
            temperatureSlider: document.getElementById('temperature'),
            temperatureValue: document.getElementById('temperature-value'),
            maxTokensInput: document.getElementById('max-tokens'),
            topPSlider: document.getElementById('top-p'),
            topPValue: document.getElementById('top-p-value'),
            frequencyPenaltySlider: document.getElementById('frequency-penalty'),
            frequencyPenaltyValue: document.getElementById('frequency-penalty-value'),
            
            // 聊天相关
            systemPrompt: document.getElementById('system-prompt'),
            chatHistory: document.getElementById('chat-history'),
            userInput: document.getElementById('user-input'),
            sendBtn: document.getElementById('send-btn'),
            clearBtn: document.getElementById('clear-btn'),
            stopBtn: document.getElementById('stop-btn'),
            
            // 渲染控制
            markdownToggle: document.getElementById('markdown-toggle'),
            streamToggle: document.getElementById('stream-toggle'),
            
            // 工具栏
            exportBtn: document.getElementById('export-btn'),
            importBtn: document.getElementById('import-btn'),
            importFile: document.getElementById('import-file'),
            fontIncreaseBtn: document.getElementById('font-increase-btn'),
            fontDecreaseBtn: document.getElementById('font-decrease-btn'),
            fontFamilySelect: document.getElementById('font-family-select'),
            
            // 模态框
            loadingOverlay: document.getElementById('loading-overlay'),
            errorModal: document.getElementById('error-modal'),
            errorMessage: document.getElementById('error-message')
        };
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // API密钥相关
        this.elements.initBtn.addEventListener('click', () => this.handleInitialize());
        this.elements.deleteKeyBtn.addEventListener('click', () => this.handleDeleteKey());
        this.elements.apiKeyInput.addEventListener('input', () => this.handleApiKeyInput());
        this.elements.apiKeyInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleInitialize();
        });

        // 模型相关
        this.elements.refreshModelsBtn.addEventListener('click', () => this.refreshModels());
        this.elements.modelSelect.addEventListener('change', () => this.handleModelSelect());

        // 参数控制
        this.elements.temperatureSlider.addEventListener('input', () => this.updateParameterValue('temperature'));
        this.elements.topPSlider.addEventListener('input', () => this.updateParameterValue('top-p'));
        this.elements.frequencyPenaltySlider.addEventListener('input', () => this.updateParameterValue('frequency-penalty'));

        // 聊天相关
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.clearBtn.addEventListener('click', () => this.clearChat());
        this.elements.stopBtn.addEventListener('click', () => this.stopGeneration());
        this.elements.userInput.addEventListener('input', () => this.handleUserInput());
        this.elements.userInput.addEventListener('keydown', (e) => this.handleKeyDown(e));

        // 渲染控制
        this.elements.markdownToggle.addEventListener('change', () => this.toggleMarkdown());
        this.elements.streamToggle.addEventListener('change', () => this.toggleStream());

        // 工具栏
        this.elements.exportBtn.addEventListener('click', () => this.exportChat());
        this.elements.importBtn.addEventListener('click', () => this.elements.importFile.click());
        this.elements.importFile.addEventListener('change', () => this.importChat());
        this.elements.fontIncreaseBtn.addEventListener('click', () => this.changeFontSize(1));
        this.elements.fontDecreaseBtn.addEventListener('click', () => this.changeFontSize(-1));
        this.elements.fontFamilySelect.addEventListener('change', () => this.changeFontFamily());

        // 模态框
        if (this.elements.errorModal) {
            this.elements.errorModal.addEventListener('click', (e) => {
                if (e.target === this.elements.errorModal) this.closeErrorModal();
            });
        }

        // 窗口事件
        window.addEventListener('beforeunload', () => this.saveSettings());
    }

    /**
     * 加载保存的设置
     */
    loadSettings() {
        try {
            const settings = JSON.parse(localStorage.getItem('deepseek-web-settings') || '{}');
            
            // 加载API密钥
            if (settings.apiKey) {
                this.elements.apiKeyInput.value = this.decryptApiKey(settings.apiKey);
            }
            
            // 加载参数设置
            if (settings.temperature !== undefined) {
                this.elements.temperatureSlider.value = settings.temperature;
                this.updateParameterValue('temperature');
            }
            if (settings.maxTokens !== undefined) {
                this.elements.maxTokensInput.value = settings.maxTokens;
            }
            if (settings.topP !== undefined) {
                this.elements.topPSlider.value = settings.topP;
                this.updateParameterValue('top-p');
            }
            if (settings.frequencyPenalty !== undefined) {
                this.elements.frequencyPenaltySlider.value = settings.frequencyPenalty;
                this.updateParameterValue('frequency-penalty');
            }
            
            // 加载系统提示词
            if (settings.systemPrompt) {
                this.elements.systemPrompt.value = settings.systemPrompt;
            }
            
            // 加载渲染设置
            if (settings.markdownEnabled !== undefined) {
                this.elements.markdownToggle.checked = settings.markdownEnabled;
                this.isMarkdownEnabled = settings.markdownEnabled;
                window.setMarkdownEnabled(this.isMarkdownEnabled);
            }
            if (settings.streamEnabled !== undefined) {
                this.elements.streamToggle.checked = settings.streamEnabled;
                this.isStreamEnabled = settings.streamEnabled;
            }
            
            // 加载字体设置
            if (settings.fontSize) {
                this.currentFontSize = settings.fontSize;
                this.applyFontSize();
            }
            if (settings.fontFamily) {
                this.currentFontFamily = settings.fontFamily;
                this.elements.fontFamilySelect.value = settings.fontFamily;
                this.applyFontFamily();
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    /**
     * 保存设置
     */
    saveSettings() {
        try {
            const settings = {
                apiKey: this.apiKey ? this.encryptApiKey(this.apiKey) : '',
                temperature: parseFloat(this.elements.temperatureSlider.value),
                maxTokens: parseInt(this.elements.maxTokensInput.value),
                topP: parseFloat(this.elements.topPSlider.value),
                frequencyPenalty: parseFloat(this.elements.frequencyPenaltySlider.value),
                systemPrompt: this.elements.systemPrompt.value,
                markdownEnabled: this.isMarkdownEnabled,
                streamEnabled: this.isStreamEnabled,
                fontSize: this.currentFontSize,
                fontFamily: this.currentFontFamily
            };
            
            localStorage.setItem('deepseek-web-settings', JSON.stringify(settings));
        } catch (error) {
            console.error('Error saving settings:', error);
        }
    }

    /**
     * 简单的API密钥加密/解密
     */
    encryptApiKey(key) {
        return btoa(key); // 实际应用中应使用更安全的加密方法
    }

    decryptApiKey(encrypted) {
        try {
            return atob(encrypted);
        } catch {
            return '';
        }
    }

    /**
     * 检查网络连接
     */
    async checkConnection() {
        try {
            const response = await fetch('/api/ping', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                this.updateStatus('connected', '已连接');
            } else {
                this.updateStatus('disconnected', '连接失败');
            }
        } catch (error) {
            this.updateStatus('disconnected', '网络错误');
        }
    }

    /**
     * 更新连接状态
     */
    updateStatus(status, text) {
        this.elements.statusDot.className = `status-dot ${status}`;
        this.elements.statusText.textContent = text;
    }

    /**
     * 处理API密钥输入
     */
    handleApiKeyInput() {
        const hasKey = this.elements.apiKeyInput.value.trim().length > 0;
        this.elements.initBtn.disabled = !hasKey;
        this.elements.initBtn.textContent = this.apiKey ? '重新初始化' : '初始化';
    }

    /**
     * 处理初始化
     */
    async handleInitialize() {
        const apiKey = this.elements.apiKeyInput.value.trim();
        if (!apiKey) {
            this.showError('请输入API密钥');
            return;
        }

        this.showLoading('正在初始化...');
        this.updateStatus('connecting', '初始化中...');

        try {
            const response = await fetch('/api/initialize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey })
            });

            const result = await response.json();

            if (result.success) {
                this.apiKey = apiKey;
                this.showApiKeyStatus('success', '初始化成功');
                this.updateStatus('connected', '已连接');
                
                // 隐藏API密钥输入，显示删除按钮
                this.elements.apiKeyInput.type = 'text';
                this.elements.apiKeyInput.value = this.maskApiKey(apiKey);
                this.elements.apiKeyInput.disabled = true;
                this.elements.deleteKeyBtn.style.display = 'inline-block';
                this.elements.initBtn.textContent = '修改密钥';
                
                // 启用相关功能
                this.elements.refreshModelsBtn.disabled = false;
                this.elements.userInput.disabled = false;
                
                // 自动刷新模型和查询余额
                await Promise.all([
                    this.refreshModels(),
                    this.queryBalance()
                ]);
                
                this.saveSettings();
            } else {
                throw new Error(result.error || '初始化失败');
            }
        } catch (error) {
            this.showApiKeyStatus('error', `初始化失败: ${error.message}`);
            this.updateStatus('disconnected', '初始化失败');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 处理删除密钥
     */
    handleDeleteKey() {
        if (confirm('确定要删除API密钥吗？这将清除所有相关数据。')) {
            this.apiKey = '';
            this.selectedModel = '';
            this.availableModels = [];
            this.messages = [];
            
            // 重置UI
            this.elements.apiKeyInput.type = 'password';
            this.elements.apiKeyInput.value = '';
            this.elements.apiKeyInput.disabled = false;
            this.elements.deleteKeyBtn.style.display = 'none';
            this.elements.initBtn.textContent = '初始化';
            
            // 禁用相关功能
            this.elements.refreshModelsBtn.disabled = true;
            this.elements.modelSelect.disabled = true;
            this.elements.userInput.disabled = true;
            this.elements.sendBtn.disabled = true;
            
            // 重置模型选择
            this.elements.modelSelect.innerHTML = '<option value="">请先初始化API密钥...</option>';
            
            // 隐藏余额信息
            this.elements.balanceInfo.style.display = 'none';
            
            // 清除状态消息
            this.hideApiKeyStatus();
            this.updateStatus('disconnected', '未连接');
            
            // 清除保存的设置
            localStorage.removeItem('deepseek-web-settings');
            
            this.showApiKeyStatus('info', '已清除API密钥');
        }
    }

    /**
     * 掩码显示API密钥
     */
    maskApiKey(key) {
        if (key.length <= 8) return '*'.repeat(key.length);
        return key.substring(0, 4) + '*'.repeat(key.length - 8) + key.substring(key.length - 4);
    }

    /**
     * 刷新模型列表
     */
    async refreshModels() {
        if (!this.apiKey) return;

        this.showLoading('正在获取模型列表...');
        this.elements.refreshModelsBtn.disabled = true;

        try {
            const response = await fetch('/api/models', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: this.apiKey })
            });

            const result = await response.json();

            if (result.success) {
                this.availableModels = result.models;
                this.updateModelSelect();
                this.showApiKeyStatus('success', `获取到 ${result.models.length} 个模型`);
            } else {
                throw new Error(result.error || '获取模型失败');
            }
        } catch (error) {
            this.showApiKeyStatus('error', `获取模型失败: ${error.message}`);
        } finally {
            this.elements.refreshModelsBtn.disabled = false;
            this.hideLoading();
        }
    }

    /**
     * 更新模型选择下拉框
     */
    updateModelSelect() {
        this.elements.modelSelect.innerHTML = '<option value="">请选择一个模型...</option>';
        
        this.availableModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            this.elements.modelSelect.appendChild(option);
        });
        
        this.elements.modelSelect.disabled = false;
    }

    /**
     * 处理模型选择
     */
    handleModelSelect() {
        this.selectedModel = this.elements.modelSelect.value;
        this.updateSendButtonState();
        
        if (this.selectedModel) {
            this.showApiKeyStatus('success', `已选择模型: ${this.selectedModel}`);
        }
    }

    /**
     * 查询账户余额
     */
    async queryBalance() {
        if (!this.apiKey) return;

        try {
            const response = await fetch('/api/balance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: this.apiKey })
            });

            const result = await response.json();

            if (result.success && result.balance_data) {
                const balanceData = result.balance_data;
                
                if (balanceData.is_available && balanceData.balance_infos && balanceData.balance_infos.length > 0) {
                    const mainBalance = balanceData.balance_infos[0];
                    const amount = mainBalance.total_balance || mainBalance.granted_balance || 'N/A';
                    const currency = mainBalance.currency || 'USD';
                    
                    this.elements.balanceAmount.textContent = `${amount} ${currency}`;
                    this.elements.balanceInfo.style.display = 'block';
                } else {
                    this.elements.balanceAmount.textContent = '服务不可用';
                    this.elements.balanceInfo.style.display = 'block';
                }
            }
        } catch (error) {
            console.error('Error querying balance:', error);
        }
    }

    /**
     * 更新参数显示值
     */
    updateParameterValue(parameterName) {
        const slider = this.elements[parameterName.replace('-', '') + 'Slider'];
        const valueElement = this.elements[parameterName.replace('-', '') + 'Value'];
        
        if (slider && valueElement) {
            valueElement.textContent = parseFloat(slider.value).toFixed(parameterName === 'temperature' || parameterName === 'frequency-penalty' ? 1 : 2);
        }
    }

    /**
     * 处理用户输入
     */
    handleUserInput() {
        this.updateSendButtonState();
    }

    /**
     * 处理键盘事件
     */
    handleKeyDown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            if (!this.elements.sendBtn.disabled) {
                this.sendMessage();
            }
        }
    }

    /**
     * 更新发送按钮状态
     */
    updateSendButtonState() {
        const hasInput = this.elements.userInput.value.trim().length > 0;
        const canSend = hasInput && this.apiKey && this.selectedModel && !this.isStreaming;
        this.elements.sendBtn.disabled = !canSend;
    }

    /**
     * 发送消息
     */
    async sendMessage() {
        const userMessage = this.elements.userInput.value.trim();
        if (!userMessage || !this.apiKey || !this.selectedModel) return;

        // 清空输入框
        this.elements.userInput.value = '';
        this.updateSendButtonState();

        // 添加用户消息到对话历史
        this.addMessageToHistory('user', userMessage);

        // 准备消息列表
        const messages = [...this.messages];
        const systemPrompt = this.elements.systemPrompt.value.trim();
        
        if (systemPrompt && messages.length === 0) {
            messages.unshift({ role: 'system', content: systemPrompt });
        }
        
        messages.push({ role: 'user', content: userMessage });

        // 开始生成回复
        this.isStreaming = true;
        this.elements.sendBtn.disabled = true;
        this.elements.stopBtn.style.display = 'inline-block';
        this.elements.userInput.disabled = true;

        try {
            if (this.isStreamEnabled) {
                await this.streamResponse(messages);
            } else {
                await this.getCompleteResponse(messages);
            }
        } catch (error) {
            this.addMessageToHistory('system', `错误: ${error.message}`, 'error');
        } finally {
            this.isStreaming = false;
            this.elements.sendBtn.disabled = false;
            this.elements.stopBtn.style.display = 'none';
            this.elements.userInput.disabled = false;
            this.elements.userInput.focus();
            this.updateSendButtonState();
        }
    }

    /**
     * 流式响应处理
     */
    async streamResponse(messages) {
        this.abortController = new AbortController();
        
        const requestBody = {
            api_key: this.apiKey,
            model: this.selectedModel,
            messages: messages,
            temperature: parseFloat(this.elements.temperatureSlider.value),
            max_tokens: parseInt(this.elements.maxTokensInput.value),
            top_p: parseFloat(this.elements.topPSlider.value),
            frequency_penalty: parseFloat(this.elements.frequencyPenaltySlider.value),
            stream: true
        };

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
            signal: this.abortController.signal
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantMessage = '';
        let messageElement = null;

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done || !this.isStreaming) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.content) {
                                assistantMessage += data.content;
                                
                                if (!messageElement) {
                                    messageElement = this.addMessageToHistory('assistant', '', 'streaming');
                                }
                                
                                this.updateStreamingMessage(messageElement, assistantMessage);
                            }
                        } catch (e) {
                            console.error('Error parsing stream data:', e);
                        }
                    }
                }
            }

            if (assistantMessage && messageElement) {
                this.finalizeStreamingMessage(messageElement, assistantMessage);
                this.messages.push({ role: 'user', content: messages[messages.length - 1].content });
                this.messages.push({ role: 'assistant', content: assistantMessage });
            }
        } finally {
            reader.releaseLock();
        }
    }

    /**
     * 非流式响应处理
     */
    async getCompleteResponse(messages) {
        const requestBody = {
            api_key: this.apiKey,
            model: this.selectedModel,
            messages: messages,
            temperature: parseFloat(this.elements.temperatureSlider.value),
            max_tokens: parseInt(this.elements.maxTokensInput.value),
            top_p: parseFloat(this.elements.topPSlider.value),
            frequency_penalty: parseFloat(this.elements.frequencyPenaltySlider.value),
            stream: false
        };

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const result = await response.json();

        if (result.success && result.content) {
            this.addMessageToHistory('assistant', result.content);
            this.messages.push({ role: 'user', content: messages[messages.length - 1].content });
            this.messages.push({ role: 'assistant', content: result.content });
        } else {
            throw new Error(result.error || '获取回复失败');
        }
    }

    /**
     * 停止生成
     */
    stopGeneration() {
        this.isStreaming = false;
        if (this.abortController) {
            this.abortController.abort();
        }
    }

    /**
     * 添加消息到对话历史
     */
    addMessageToHistory(role, content, type = 'normal') {
        // 移除欢迎消息
        const welcomeMessage = this.elements.chatHistory.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        const messageElement = document.createElement('div');
        messageElement.className = `message ${role}`;
        
        const timestamp = new Date().toLocaleTimeString();
        
        const roleNames = {
            'user': '用户',
            'assistant': '助手',
            'system': '系统'
        };

        messageElement.innerHTML = `
            <div class="message-header">
                <span class="message-role ${role}">${roleNames[role] || role}</span>
                <span class="message-timestamp">${timestamp}</span>
            </div>
            <div class="message-content" data-role="${role}">
                ${type === 'streaming' ? '<div class="typing-indicator">正在输入...</div>' : this.renderContent(content, role)}
            </div>
        `;

        this.elements.chatHistory.appendChild(messageElement);
        this.scrollToBottom();
        
        return messageElement;
    }

    /**
     * 更新流式消息
     */
    updateStreamingMessage(messageElement, content) {
        const contentElement = messageElement.querySelector('.message-content');
        contentElement.innerHTML = this.renderContent(content, 'assistant');
        this.scrollToBottom();
    }

    /**
     * 完成流式消息
     */
    finalizeStreamingMessage(messageElement, content) {
        const contentElement = messageElement.querySelector('.message-content');
        contentElement.innerHTML = this.renderContent(content, 'assistant');
        messageElement.classList.remove('streaming');
    }

    /**
     * 渲染消息内容
     */
    renderContent(content, role) {
        if (role === 'system' || !this.isMarkdownEnabled) {
            return `<pre class="plain-text">${this.escapeHtml(content)}</pre>`;
        }
        
        return window.renderMarkdown ? window.renderMarkdown(content) : this.escapeHtml(content);
    }

    /**
     * 转义HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 滚动到底部
     */
    scrollToBottom() {
        this.elements.chatHistory.scrollTop = this.elements.chatHistory.scrollHeight;
    }

    /**
     * 清空对话
     */
    clearChat() {
        if (this.messages.length > 0) {
            if (!confirm('确定要清空所有对话内容吗？')) return;
        }
        
        this.messages = [];
        this.elements.chatHistory.innerHTML = `
            <div class="welcome-message">
                <p>对话已清空</p>
                <p>请输入新的消息开始对话。</p>
            </div>
        `;
    }

    /**
     * 切换Markdown渲染
     */
    toggleMarkdown() {
        this.isMarkdownEnabled = this.elements.markdownToggle.checked;
        if (window.setMarkdownEnabled) {
            window.setMarkdownEnabled(this.isMarkdownEnabled);
        }
        this.saveSettings();
        
        // 重新渲染所有消息
        this.reRenderMessages();
    }

    /**
     * 切换流式输出
     */
    toggleStream() {
        this.isStreamEnabled = this.elements.streamToggle.checked;
        this.saveSettings();
    }

    /**
     * 重新渲染所有消息
     */
    reRenderMessages() {
        const messageElements = this.elements.chatHistory.querySelectorAll('.message-content');
        messageElements.forEach((element, index) => {
            const role = element.getAttribute('data-role');
            const messageIndex = Math.floor(index / 2); // 假设消息成对出现
            
            if (this.messages[messageIndex]) {
                const content = this.messages[messageIndex].content;
                element.innerHTML = this.renderContent(content, role);
            }
        });
    }

    /**
     * 导出对话
     */
    exportChat() {
        if (this.messages.length === 0) {
            this.showError('没有对话内容可以导出');
            return;
        }

        const exportData = {
            timestamp: new Date().toISOString(),
            model: this.selectedModel,
            systemPrompt: this.elements.systemPrompt.value,
            messages: this.messages
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `deepseek-chat-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * 导入对话
     */
    importChat() {
        const file = this.elements.importFile.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                
                if (data.messages && Array.isArray(data.messages)) {
                    if (this.messages.length > 0) {
                        if (!confirm('这将替换当前的对话内容，确定要继续吗？')) return;
                    }
                    
                    this.messages = data.messages;
                    
                    // 设置系统提示词
                    if (data.systemPrompt) {
                        this.elements.systemPrompt.value = data.systemPrompt;
                    }
                    
                    // 重新渲染对话历史
                    this.renderImportedMessages();
                    
                    this.showApiKeyStatus('success', '对话导入成功');
                } else {
                    throw new Error('无效的对话文件格式');
                }
            } catch (error) {
                this.showError(`导入失败: ${error.message}`);
            }
        };
        
        reader.readAsText(file);
        this.elements.importFile.value = ''; // 清空文件选择
    }

    /**
     * 渲染导入的消息
     */
    renderImportedMessages() {
        this.elements.chatHistory.innerHTML = '';
        
        this.messages.forEach(message => {
            this.addMessageToHistory(message.role, message.content);
        });
        
        if (this.messages.length === 0) {
            this.elements.chatHistory.innerHTML = `
                <div class="welcome-message">
                    <p>欢迎使用 DeepSeek API 客户端！</p>
                    <p>请先输入您的 API 密钥并选择模型开始对话。</p>
                </div>
            `;
        }
    }

    /**
     * 改变字体大小
     */
    changeFontSize(delta) {
        const newSize = this.currentFontSize + delta;
        if (newSize >= 10 && newSize <= 24) {
            this.currentFontSize = newSize;
            this.applyFontSize();
            this.saveSettings();
        }
    }

    /**
     * 改变字体族
     */
    changeFontFamily() {
        this.currentFontFamily = this.elements.fontFamilySelect.value;
        this.applyFontFamily();
        this.saveSettings();
    }

    /**
     * 应用字体大小
     */
    applyFontSize() {
        this.elements.chatHistory.style.fontSize = `${this.currentFontSize}px`;
    }

    /**
     * 应用字体族
     */
    applyFontFamily() {
        this.elements.chatHistory.style.fontFamily = this.currentFontFamily;
    }

    /**
     * 显示API密钥状态
     */
    showApiKeyStatus(type, message) {
        this.elements.apiKeyStatus.className = `status-message ${type}`;
        this.elements.apiKeyStatus.textContent = message;
        this.elements.apiKeyStatus.style.display = 'block';
        
        // 3秒后自动隐藏成功和信息消息
        if (type === 'success' || type === 'info') {
            setTimeout(() => this.hideApiKeyStatus(), 3000);
        }
    }

    /**
     * 隐藏API密钥状态
     */
    hideApiKeyStatus() {
        this.elements.apiKeyStatus.style.display = 'none';
    }

    /**
     * 显示加载状态
     */
    showLoading(text = '正在处理...') {
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.querySelector('.loading-text').textContent = text;
            this.elements.loadingOverlay.style.display = 'flex';
        }
    }

    /**
     * 隐藏加载状态
     */
    hideLoading() {
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.style.display = 'none';
        }
    }

    /**
     * 显示错误模态框
     */
    showError(message) {
        if (this.elements.errorModal && this.elements.errorMessage) {
            this.elements.errorMessage.textContent = message;
            this.elements.errorModal.style.display = 'flex';
        } else {
            alert(message); // 备用方案
        }
    }

    /**
     * 关闭错误模态框
     */
    closeErrorModal() {
        if (this.elements.errorModal) {
            this.elements.errorModal.style.display = 'none';
        }
    }
}

/**
 * 关闭错误模态框的全局函数
 */
window.closeErrorModal = function() {
    if (window.deepSeekClient) {
        window.deepSeekClient.closeErrorModal();
    }
};

/**
 * 应用程序初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    window.deepSeekClient = new DeepSeekWebClient();
    
    // 添加错误处理
    window.addEventListener('error', function(event) {
        console.error('Unhandled error:', event.error);
    });
    
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
    });
});