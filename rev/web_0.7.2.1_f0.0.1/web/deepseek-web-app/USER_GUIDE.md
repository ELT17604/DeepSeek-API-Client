# DeepSeek Web App 使用说明 / User Guide

## 项目概述 / Project Overview

DeepSeek Web App 是一个基于 Flask 的 Web 应用程序，为 DeepSeek API 提供了直观的网页界面。该应用支持实时聊天、流式输出、Markdown 渲染等功能，让用户能够轻松地与 DeepSeek 的 AI 模型进行交互。

DeepSeek Web App is a Flask-based web application that provides an intuitive web interface for the DeepSeek API. The application supports real-time chat, streaming output, Markdown rendering, and other features that allow users to easily interact with DeepSeek's AI models.

## 功能特性 / Features

### 🎯 主要功能 / Main Features

- **API 密钥管理** / API Key Management: 安全的密钥存储和加密
- **模型选择** / Model Selection: 支持多种 DeepSeek 模型
- **实时聊天** / Real-time Chat: 流式和非流式对话模式
- **Markdown 渲染** / Markdown Rendering: 支持完整的 Markdown 语法
- **参数调节** / Parameter Tuning: 温度、Top-p、最大令牌数等参数可调
- **对话管理** / Conversation Management: 导入/导出对话记录
- **余额查询** / Balance Inquiry: 实时查看账户余额
- **响应式设计** / Responsive Design: 适配各种设备屏幕

### 🛠 技术特性 / Technical Features

- **加密存储** / Encrypted Storage: 使用 `encryption.py` 加密 API 密钥
- **流式输出** / Streaming Output: 实时显示 AI 回复内容
- **错误处理** / Error Handling: 完善的错误提示和异常处理
- **网络优化** / Network Optimization: 连接超时和重试机制

## 依赖库 / Dependencies

### 后端依赖 / Backend Dependencies

根据 `requirements.txt` 文件，项目使用以下 Python 库：

```txt
Flask==2.0.3              # Web 框架 / Web framework
requests==2.26.0          # HTTP 客户端 / HTTP client
cryptography==3.4.7       # 加密库 / Cryptography library
markdown==3.3.4           # Markdown 解析 / Markdown parsing
flask-cors==3.0.10        # 跨域支持 / CORS support
python-dotenv==0.19.2     # 环境变量 / Environment variables
```

### 前端技术 / Frontend Technologies

- **HTML5** + **CSS3**: 基础页面结构和样式
- **JavaScript (ES6+)**: 核心交互逻辑
- **Web Crypto API**: 客户端加密功能
- **SSE (Server-Sent Events)**: 流式数据传输
- **响应式设计**: 支持移动端和桌面端

## 安装和启动 / Installation and Setup

### 1. 环境准备 / Environment Setup

```bash
# 克隆项目 / Clone repository
git clone <repository-url>
cd deepseek-web-app

# 创建虚拟环境 (推荐) / Create virtual environment (recommended)
python -m venv venv

# 激活虚拟环境 / Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. 安装依赖 / Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. 启动应用 / Start Application

```bash
python run.py
```

应用将在 `http://localhost:5000` 启动。

The application will start at `http://localhost:5000`.

## 配置自定义 / Configuration and Customization

### 🔧 环境变量配置 / Environment Variables

在项目根目录创建 `.env` 文件进行配置：

Create a `.env` file in the project root for configuration:

```env
# 服务器配置 / Server Configuration
HOST=0.0.0.0
PORT=5000
DEBUG=True

# 安全配置 / Security Configuration
SECRET_KEY=your-secure-secret-key-here

# API 配置 / API Configuration
DEEPSEEK_API_BASE_URL=https://api.deepseek.com/v1
REQUEST_TIMEOUT=30
STREAM_TIMEOUT=60
```

### 🎨 界面自定义 / UI Customization

#### 样式修改 / Style Modifications

编辑 `static/css/style.css` 文件：

```css
/* 修改主题颜色 / Change theme colors */
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #27ae60;
    --error-color: #e74c3c;
}

/* 自定义字体 / Custom fonts */
body {
    font-family: 'Your Custom Font', sans-serif;
}

/* 修改背景渐变 / Change background gradient */
body {
    background: linear-gradient(135deg, #your-color1 0%, #your-color2 100%);
}
```

#### Markdown 渲染自定义 / Markdown Rendering Customization

修改 `static/js/markdown.js` 中的 `MarkdownRenderer` 类：

```javascript
// 添加自定义 Markdown 规则 / Add custom Markdown rules
renderCustomElement(text) {
    // 自定义渲染逻辑 / Custom rendering logic
    return text.replace(/\[custom\](.*?)\[\/custom\]/g, '<div class="custom-element">$1</div>');
}
```

### ⚙️ 服务器配置 / Server Configuration

#### 生产环境部署 / Production Deployment

在 `config.py` 中修改配置：

```python
class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # 其他生产环境配置 / Other production settings
```

#### API 端点自定义 / API Endpoint Customization

在 `run.py` 中的 `DeepSeekAPIClient` 类中修改 API 配置：

```python
DEEPSEEK_API_BASE_URL = "https://your-custom-api-endpoint.com/v1"
DEEPSEEK_BALANCE_URL = "https://your-custom-api-endpoint.com/user/balance"
```

## 常见问题解决方案 / Troubleshooting

### ❌ 连接问题 / Connection Issues

#### 问题：无法连接到 DeepSeek API / Issue: Cannot connect to DeepSeek API

**解决方案 / Solution:**

1. **检查网络连接** / Check network connection:
   ```bash
   ping api.deepseek.com
   ```

2. **验证 API 密钥** / Verify API key:
   - 确保 API 密钥格式正确 / Ensure API key format is correct
   - 检查密钥是否过期 / Check if key has expired
   - 验证账户余额 / Verify account balance

3. **检查防火墙设置** / Check firewall settings:
   - 允许端口 5000 的访问 / Allow access to port 5000
   - 配置代理设置（如需要）/ Configure proxy settings (if needed)

#### 问题：流式输出中断 / Issue: Streaming output interrupted

**解决方案 / Solution:**

在 `run.py` 中调整超时设置：

```python
# 增加流式请求超时时间 / Increase streaming timeout
STREAM_TIMEOUT = 120  # 从 60 秒增加到 120 秒 / Increase from 60s to 120s
```

### 🔐 安全问题 / Security Issues

#### 问题：API 密钥加密失败 / Issue: API key encryption failed

**解决方案 / Solution:**

1. **检查 cryptography 库** / Check cryptography library:
   ```bash
   pip install --upgrade cryptography
   ```

2. **重新生成加密密钥** / Regenerate encryption key:
   
   修改 `src/utils/encryption.py`：
   ```python
   def get_encryption_key():
       # 使用更安全的密钥生成方法 / Use more secure key generation
       import secrets
       return base64.urlsafe_b64encode(secrets.token_bytes(32))
   ```

### 💾 存储问题 / Storage Issues

#### 问题：API 密钥无法保存 / Issue: Cannot save API key

**解决方案 / Solution:**

1. **检查文件权限** / Check file permissions:
   ```bash
   # Linux/macOS
   chmod 600 API_KEY
   
   # Windows
   # 右键 -> 属性 -> 安全 -> 设置适当权限
   ```

2. **修改存储路径** / Change storage path:
   
   在 `config.py` 中：
   ```python
   API_KEY_FILENAME = os.path.join(os.path.expanduser("~"), ".deepseek_api_key")
   ```

### 🖥️ 界面问题 / UI Issues

#### 问题：Markdown 渲染异常 / Issue: Markdown rendering issues

**解决方案 / Solution:**

1. **检查 JavaScript 控制台错误** / Check JavaScript console errors
2. **清除浏览器缓存** / Clear browser cache
3. **验证 `markdown.js` 文件完整性** / Verify `markdown.js` file integrity

#### 问题：移动端显示异常 / Issue: Mobile display issues

**解决方案 / Solution:**

在 `static/css/style.css` 中调整媒体查询：

```css
@media (max-width: 480px) {
    .container {
        width: calc(100% - 10px);
        padding: 10px 5px;
    }
    
    .input-group {
        flex-direction: column;
    }
}
```

### 🚀 性能优化 / Performance Optimization

#### 优化建议 / Optimization Tips

1. **启用 Gzip 压缩** / Enable Gzip compression:
   ```python
   from flask_compress import Compress
   Compress(app)
   ```

2. **缓存静态资源** / Cache static resources:
   ```python
   @app.after_request
   def after_request(response):
       response.headers['Cache-Control'] = 'public, max-age=31536000'
       return response
   ```

3. **使用 CDN** / Use CDN for static assets

## 开发指南 / Development Guide

### 📂 项目结构说明 / Project Structure

```
deepseek-web-app/
├── static/                    # 静态资源 / Static assets
│   ├── css/style.css         # 样式文件 / Stylesheets
│   ├── js/                   # JavaScript 文件 / JavaScript files
│   │   ├── app.js           # 主应用逻辑 / Main application logic
│   │   ├── markdown.js      # Markdown 渲染 / Markdown rendering
│   │   └── crypto.js        # 加密功能 / Encryption functions
│   └── fonts/               # 字体文件 / Font files
├── templates/               # HTML 模板 / HTML templates
│   └── index.html          # 主页面 / Main page
├── src/                    # 源代码 / Source code
│   ├── app.py             # Flask 应用入口 / Flask app entry
│   ├── models/            # 数据模型 / Data models
│   ├── utils/             # 工具函数 / Utility functions
│   └── routes/            # 路由定义 / Route definitions
├── config.py              # 配置文件 / Configuration
├── run.py                 # 启动脚本 / Startup script
└── requirements.txt       # 依赖列表 / Dependencies
```

### 🔧 添加新功能 / Adding New Features

#### 后端 API 端点 / Backend API Endpoints:

在 `run.py` 中添加新路由：

```python
@app.route('/api/new-feature', methods=['POST'])
def new_feature():
    # 实现新功能逻辑 / Implement new feature logic
    return jsonify({'success': True})
```

#### 前端交互 / Frontend Interaction:

在 `static/js/app.js` 中添加新方法：

```javascript
async newFeature() {
    const response = await fetch('/api/new-feature', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({/* data */})
    });
    return response.json();
}
```

## 贡献指南 / Contributing

欢迎提交 Pull Request 或 Issue！请确保：

We welcome Pull Requests and Issues! Please ensure:

1. **代码风格一致** / Consistent code style
2. **添加适当的注释** / Add appropriate comments
3. **包含测试用例** / Include test cases
4. **更新文档** / Update documentation

## 许可证 / License

本项目采用 MIT 许可证。详情请参阅 LICENSE 文件。

This project is licensed under the MIT License. See the LICENSE file for details.

---

## 技术支持 / Technical Support

如果遇到问题，请：

If you encounter issues, please:

1. 检查上述故障排除指南 / Check the troubleshooting guide above
2. 在 GitHub 上提交 Issue / Submit an Issue on GitHub
3. 提供详细的错误信息和环境信息 / Provide detailed error messages and environment info

**版本信息 / Version Info:** v0.7.2.1.f.0.0.1.a  
**构建日期 / Build Date:** 2025-05-25  
**作者 / Author:** ELT Group