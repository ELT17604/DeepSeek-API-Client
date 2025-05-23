# DeepSeek API Client

本项目包含两个主要程序：

- `main.py`：基于命令行的 DeepSeek API 客户端
- `main-gui.py`：基于 Tkinter 的图形界面 DeepSeek API 客户端

## 声明

- **0, 使用本项目即代表用户承诺遵守其国家/地区的相关法律法规。**
- **1, 一切用户行为与开发者无关。**
- **2, 本项目禁止用于盈利商用。**

## 功能简介

- 支持 DeepSeek API Key 管理与初始化
- 支持模型列表获取与选择
- 支持账户余额查询
- 支持与模型的多轮对话（流式输出）
- GUI 版本提供状态指示、输入区、输出区、会话管理等功能

## 依赖环境

运行前请确保已安装以下依赖包：

```sh
pip install openai requests
```

GUI 版本基于 Python 标准库的 `tkinter`，一般无需额外安装。

## 使用方法

### 1. 命令行版本

```sh
python main.py
```

- 按提示输入 DeepSeek API Key
- 可选择模型、查询余额、发起对话

### 2. 图形界面版本

```sh
python main-gui.py
```

- 在底部输入栏输入 API Key 并点击“Initialize Client”
- 点击“List and Select Model”选择模型
- 点击“Query Account Balance”查询余额
- 点击“Start Chat”后可在输入区输入内容并与模型对话
- 支持新会话、结束会话、清空输出等操作
- 状态面板实时显示客户端、网络、模型、HTTP、聊天服务状态

## 按钮功能说明

- **Initialize Client**：使用输入栏中的 API Key 初始化客户端，成功后隐藏输入栏并显示星号遮盖的 Key。
- **Clear API Key**：清除当前 API Key，恢复输入栏，需重新初始化。
- **List and Select Model**：获取并选择可用模型，需先初始化客户端。
- **Query Account Balance**：查询当前账户余额信息。
- **Start Chat**：激活聊天输入区，准备与模型对话。
- **Send**：发送输入区内容到模型，获取回复（回车键也可发送，Ctrl+Enter 换行）。
- **New Session**：清空当前会话历史，开启新会话。
- **End Chat**：结束当前聊天，输入区可重新输入。
- **Clear Output**：清空输出显示区域。

## 状态监视窗口说明

图形界面版本会自动弹出一个“Status Panel”状态监视窗口，实时显示程序各项关键状态。窗口包含五个状态指示器，每个指示器由状态文本和一个彩色圆形指示灯组成：

1. **Client Init**  
   - 绿色：客户端已初始化
   - 黄色：已输入 API Key 但未初始化
   - 红色：未输入 API Key

2. **Network**  
   - 绿色：网络正常，延迟低
   - 黄色：网络延迟较高或非常高
   - 红色：无法连接 DeepSeek 服务器

3. **Model Select**  
   - 绿色：已选择模型
   - 黄色：获取模型列表失败
   - 红色：未选择模型

4. **HTTP Error**  
   - 绿色：HTTP 状态正常
   - 黄色：服务器错误（5xx）
   - 红色：客户端错误（4xx）

5. **Chat Service**  
   - 绿色：聊天服务就绪，可以输入
   - 黄色：正在流式输出回复
   - 红色：未准备好（未初始化或未选模型）

状态监视窗口可用于快速判断当前客户端、网络、模型、API 及聊天服务的健康状况，便于排查问题。

## 典型聊天流程（GUI 版）

1. 启动程序：`python main-gui.py`
2. 在底部输入栏输入你的 DeepSeek API Key，点击 **Initialize Client**。
3. 客户端初始化成功后，点击 **List and Select Model**，在弹窗中选择一个模型。
4. 可选：点击 **Query Account Balance** 查询余额。
5. 点击 **Start Chat**，激活输入区。
6. 在输入区输入你的问题，点击 **Send** 或直接按回车发送（Ctrl+Enter 换行）。
7. 等待模型回复，回复内容会实时显示在输出区。
8. 可随时点击 **New Session** 开启新会话，或点击 **End Chat** 结束当前聊天。
9. 点击 **Clear Output** 可清空输出内容。
10. 如需切换 API Key，可点击 **Clear API Key**，重新输入并初始化。

## 注意事项

- 需要有效的 DeepSeek API Key
- 若遇到网络或 API 错误，请检查网络连接和 API Key 是否正确
- **请自觉遵守所在国家/地区的相关法律法规，开发者不对用户行为负责。**

---

*Readme by Copilot
如有问题欢迎反馈！