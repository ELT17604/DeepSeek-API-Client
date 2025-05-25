# DeepSeek Web App

**[📖 用户指南 User Guide](USER_GUIDE.md)** | **[🔧 开发者文档 Developer Guide](DEV_GUIDE.md)**

---

DeepSeek Web App 是一个基于 Web 的 DeepSeek API 客户端应用程序。该应用程序允许用户输入 API 密钥、选择模型，并以 Markdown 格式查看输出结果。

DeepSeek Web App is a web-based client for interacting with the DeepSeek API. This application allows users to input their API key, select models, and view outputs rendered in Markdown format.

## 项目结构 / Project Structure

项目组织如下：

The project is organized as follows:

```
deepseek-web-app
├── static
│   ├── css
│   │   └── style.css          # 应用程序样式 / Styles for the application
│   ├── js
│   │   ├── app.js             # 主 JavaScript 文件，用于用户交互 / Main JavaScript file for user interactions
│   │   ├── markdown.js         # Markdown 渲染功能 / Markdown rendering functions
│   │   └── crypto.js           # API 密钥加密和解密 / API key encryption and decryption
│   └── fonts
│       └── consolas.woff2     # 代码块的 Web 字体 / Web font for code blocks
├── templates
│   └── index.html             # 应用程序的主 HTML 文件 / Main HTML file for the application
├── src
│   ├── app.py                 # Flask 应用程序入口点 / Entry point for the Flask application
│   ├── models
│   │   └── deepseek_client.py  # DeepSeek API 交互的客户端模型 / Client model for DeepSeek API interaction
│   ├── utils
│   │   ├── encryption.py       # 加密和解密功能 / Encryption and decryption functions
│   │   └── storage.py          # API 密钥存储和加载功能 / API key storage and loading functions
│   └── routes
│       ├── __init__.py        # 初始化路由模块 / Initializes the routes module
│       ├── api.py             # API 相关路由 / API-related routes
│       └── chat.py            # 聊天功能路由 / Chat functionality routes
├── requirements.txt            # 所需的 Python 库和依赖项 / Required Python libraries and dependencies
├── config.py                   # 应用程序配置设置 / Application configuration settings
├── run.py                      # 启动 Flask 应用程序的脚本 / Script to start the Flask application
└── README.md                   # 项目文档和使用说明 / Project documentation and usage instructions
```

## 安装 / Installation

1. 克隆仓库：/ Clone the repository:
   ```
   git clone <repository-url>
   cd deepseek-web-app
   ```

2. 安装所需的依赖项：/ Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## 使用方法 / Usage

1. 启动应用程序：/ Start the application:
   ```
   python run.py
   ```

2. 打开您的 Web 浏览器并导航到 `http://localhost:5000`。/ Open your web browser and navigate to `http://localhost:5000`.

3. 在提供的输入字段中输入您的 API 密钥，然后点击"初始化"以初始化客户端。/ Enter your API key in the provided input field and click "初始化" to initialize the client.

4. 从下拉菜单中选择一个模型以与 DeepSeek API 交互。/ Select a model from the dropdown menu to interact with the DeepSeek API.

5. 在输出部分查看以 Markdown 格式渲染的输出。/ View the output rendered in Markdown format in the output section.

## 贡献 / Contributing

欢迎贡献！请随时提交拉取请求或为任何建议或改进提出问题。

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## 许可证 / License

该项目根据 MIT 许可证授权。有关详细信息，请参阅 LICENSE 文件。

This project is licensed under the MIT License. See the LICENSE file for details.