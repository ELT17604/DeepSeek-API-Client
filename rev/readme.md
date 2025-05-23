# DeepSeek API Client

## 项目简介
DeepSeek API Client 是一个用于访问 DeepSeek API 的桌面客户端，支持图形界面（GUI）和命令行（CLI）两种模式。它帮助用户便捷地与 DeepSeek 大模型进行对话、查询账户余额、管理 API Key 等操作。项目基于 Python 开发，适合个人学习和研究用途。

---

## 功能介绍

- **API Key 本地加密存储**：支持将 API Key 加密后安全地保存在本地，避免明文泄露。
- **模型列表获取与选择**：自动获取可用模型列表，支持手动输入模型名称。
- **账户余额查询**：一键查询 DeepSeek 账户余额及详细信息。
- **对话功能**：与 DeepSeek 大模型进行多轮对话，支持流式输出。
- **网络状态检测**：实时检测 DeepSeek API 网络连通性与延迟。
- **多平台支持**：支持 Windows、Linux、macOS（需 Python 3.8+ 环境）。
- **图形界面与命令行双模式**：可通过 `--gui` 或 `--cli` 参数切换。

---

## 免责声明

> 本项目仅为个人学习、研究和非商业用途开发，严禁用于任何商业用途。  
> 本项目生成的所有内容均由 AI 自动生成，不代表开发者立场，也不保证内容的准确性、合法性或适用性。  
> 用户需对使用本项目生成的内容自行负责，请勿将生成内容用于违法、违规、侵权等用途。  
> 请严格遵守您所在国家/地区的相关法律法规，因使用本项目产生的任何后果由用户自行承担。

---

## GUI 按钮说明

- **Initialize Client**：初始化 DeepSeek 客户端，加载并保存 API Key。
- **Remove API Key**：删除本地保存的 API Key 文件。
- **List and Select Model**：获取并选择可用模型，或手动输入模型名称。
- **Query Account Balance**：查询当前账户余额及详细信息。
- **Start Chat**：开始与所选模型的对话。
- **Clear Output**：清空输出窗口内容。
- **Send**：发送输入内容到模型（回车快捷键）。
- **New Session**：开启新的对话会话，清空历史消息。
- **End Chat**：结束当前对话，但不清空历史消息。

---

## 典型使用流程

### 首次运行

启动程序（推荐 GUI 模式），输入或粘贴您的 DeepSeek API Key。  
初始化客户端后，API Key 会加密保存到本地。

### 选择模型

点击“List and Select Model”获取模型列表并选择，或手动输入模型名称。

### 查询余额

点击“Query Account Balance”可随时查看账户余额和额度信息。

### 开始对话

点击“Start Chat”，在输入框输入内容并发送，与模型进行多轮对话。

### 管理 API Key

如需更换或移除 API Key，可点击“Remove API Key”并重新初始化。

---

## 关于本地存储密钥

- 程序会将 API Key 使用本机唯一标识加密后，保存到程序目录下的 `api_key` 文件。
- 加密采用 `cryptography.fernet` 算法，密钥基于本机硬件信息生成，仅当前设备可解密。
- 若删除 `api_key` 文件或更换设备，需重新输入 API Key。
- 请勿将 `api_key` 文件泄露或用于其他设备，以保障账号安全。

---

## 其他说明

- 若未安装 `cryptography` 库，API Key 将以降级方式存储（安全性降低），建议通过 `pip install cryptography` 安装。
- 本项目遵循 GPLv3 协议，禁止任何形式的商业再分发。
- 如遇到问题或建议，欢迎通过 issue 反馈。

---

ELT Group 2025