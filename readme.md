# DeepSeek API Client GUI 使用说明（v0.7.2.1）

## 简要说明

本项目为 DeepSeek API 的图形界面客户端，支持模型选择、聊天、余额查询、状态监控、Markdown 渲染等功能。**最新版本为 v0.7.2.1**，主程序文件为根目录下的 `main-single-CN.py` 和 `main-single-CN-exe.py`。详细的简明操作指南请参见根目录下的 [BriefGuide.md](BriefGuide.md)。

---

## 主要启动文件

### 1. `main-single-CN.py`

- **推荐用法**：适合大多数用户，依赖较少，启动方式灵活。
- **启动方式**：
  ```bash
  python main-single-CN.py         # 默认GUI模式
  python main-single-CN.py --gui   # 强制GUI模式
  python main-single-CN.py --cli   # 终端模式（无图形界面）
  ```
- **特点**：
  - 依赖标准 Python 3.7+ 环境，需安装 `tkinter`、`requests`、`openai`，可选 `cryptography`（用于API Key加密）。
  - 支持完整的图形界面和命令行两种模式。
  - 推荐在需要跨平台或环境兼容性更强时使用。

### 2. `main-single-CN-exe.py`

- **推荐用法**：适合希望直接打包为 Windows 可执行文件（exe）的用户。
- **启动方式**：
  ```bash
  python main-single-CN-exe.py         # 默认GUI模式
  python main-single-CN-exe.py --gui   # 强制GUI模式
  python main-single-CN-exe.py --cli   # 终端模式
  ```
- **特点**：
  - 代码结构针对 PyInstaller 等工具优化，便于一键打包为独立 exe 文件。
  - 功能与 `main-single-CN.py` 基本一致，界面和体验无明显差异。
  - 推荐用于需要分发给非开发用户或无 Python 环境的场景。

### 两者区别

| 文件名                | 适用场景         | 依赖/打包         | 备注                       |
|----------------------|------------------|-------------------|----------------------------|
| main-single-CN.py    | 通用/开发环境     | 直接运行 .py 文件  | 跨平台，依赖更灵活         |
| main-single-CN-exe.py| 打包为 Windows EXE| 适合 PyInstaller   | 适合分发，无需 Python 环境  |

---

## 其他文件与文件夹说明

- **BriefGuide.md**  
  简明操作指南，适合新手快速上手，包含界面按钮说明、常见问题等。

- **LICENSE**  
  项目开源协议（GPL v3）。

- **ds_api_guide.mp4**  
  视频演示或操作指南。

- **legacy/**  
  历史版本归档，包含早期的多版本实现（如 `v0.2.1`、`v0.5.4` 等），仅供参考或回溯，不建议用于生产环境。

- **rev/**  
  旧版或测试用的开发分支文件，可忽略。

---

## 依赖环境

- Python 3.7 及以上
- 必需依赖：`tkinter`、`requests`、`openai`
- 可选依赖：`cryptography`（用于本地加密存储 API Key）

---

## 常见问题

- 启动或使用问题、指示灯含义、API Key 管理、模型选择、Markdown 渲染、字体调节等，请参见 [BriefGuide.md](BriefGuide.md)。

---

## 版权信息

**DeepSeek API Client GUI v0.7.2.1** © 2025 ELT Group  
Licensed under GNU General Public License v3.0  
Email: elt17604@outlook.com
