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

import sys
import os
import argparse
import logging
from datetime import datetime
from config import APP_INFO

# 程序启动模式检测
def detect_startup_mode():
    """
    检测程序启动模式
    
    Returns:
        str: 启动模式 ('gui', 'cli', 'auto')
    """
    # 检查命令行参数
    if "--gui" in sys.argv:
        return "gui"
    elif "--cli" in sys.argv:
        return "cli"
    else:
        # 自动检测模式：如果在终端环境中启动，默认CLI；否则GUI
        try:
            # 检查是否有交互式终端
            if hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                # 检查是否有显示环境
                if os.environ.get('DISPLAY') or os.name == 'nt':
                    return "gui"  # Windows或有显示的Unix系统，默认GUI
                else:
                    return "cli"  # 无显示环境，使用CLI
            else:
                return "gui"  # 非交互式环境，默认GUI
        except Exception:
            return "gui"  # 异常情况下默认GUI

def parse_command_line_args():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description=f"{APP_INFO['name']} - {APP_INFO['description']}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
示例:
  python main.py                    # 自动检测模式
  python main.py --gui             # 强制GUI模式
  python main.py --cli             # 强制CLI模式
  python main.py --cli --guided    # CLI引导模式
  python main.py --debug           # 启用调试日志
  python main.py --config config.py # 使用自定义配置文件

版本: {APP_INFO['version']}
作者: {APP_INFO['author']}
        """
    )
    
    # 界面模式选择
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--gui', 
        action='store_true',
        help='强制使用图形用户界面模式'
    )
    mode_group.add_argument(
        '--cli', 
        action='store_true',
        help='强制使用命令行界面模式'
    )
    
    # CLI特定选项
    parser.add_argument(
        '--guided', '--setup',
        action='store_true',
        help='使用引导式设置（仅CLI模式）'
    )
    
    # 调试和日志选项
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试日志输出'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        help='指定日志文件路径'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='设置日志级别 (默认: INFO)'
    )
    
    # 配置选项
    parser.add_argument(
        '--config',
        type=str,
        help='指定配置文件路径'
    )
    parser.add_argument(
        '--no-config',
        action='store_true',
        help='不加载配置文件，使用默认设置'
    )
    
    # API相关选项
    parser.add_argument(
        '--api-key',
        type=str,
        help='直接指定API密钥（不建议在共享环境中使用）'
    )
    parser.add_argument(
        '--api-base',
        type=str,
        help='指定API基础URL'
    )
    
    # 快速操作选项
    parser.add_argument(
        '--balance',
        action='store_true',
        help='快速查询余额并退出'
    )
    parser.add_argument(
        '--models',
        action='store_true',
        help='列出可用模型并退出'
    )
    parser.add_argument(
        '--chat',
        type=str,
        metavar='MODEL',
        help='直接开始与指定模型聊天'
    )
    
    # 版本和帮助
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f"{APP_INFO['name']} {APP_INFO['version']}"
    )
    
    return parser.parse_args()

def setup_logging(args):
    """
    设置日志系统
    
    Args:
        args: 命令行参数
    """
    # 确定日志级别
    log_level = getattr(logging, args.log_level.upper())
    if args.debug:
        log_level = logging.DEBUG
    
    # 设置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 配置日志处理器
    handlers = []
    
    # 控制台处理器
    if not args.log_file or args.debug:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(log_format, date_format)
        console_handler.setFormatter(console_formatter)
        handlers.append(console_handler)
    
    # 文件处理器
    if args.log_file:
        try:
            # 确保日志目录存在
            log_dir = os.path.dirname(args.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            file_handler = logging.FileHandler(args.log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(log_format, date_format)
            file_handler.setFormatter(file_formatter)
            handlers.append(file_handler)
        except Exception as e:
            print(f"警告: 无法创建日志文件 {args.log_file}: {e}")
    
    # 配置根日志器
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
        force=True
    )
    
    # 记录启动信息
    logger = logging.getLogger(__name__)
    logger.info(f"启动 {APP_INFO['name']} {APP_INFO['version']}")
    logger.debug(f"命令行参数: {vars(args)}")

def validate_dependencies():
    """
    验证程序依赖
    
    Returns:
        tuple: (success, missing_deps, error_message)
    """
    missing_deps = []
    optional_missing = []
    
    # 检查必需依赖
    required_deps = {
        'openai': 'openai',
        'requests': 'requests'
    }
    
    for import_name, package_name in required_deps.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_deps.append(package_name)
    
    # 检查可选依赖
    optional_deps = {
        'cryptography': 'cryptography'
    }
    
    for import_name, package_name in optional_deps.items():
        try:
            __import__(import_name)
        except ImportError:
            optional_missing.append(package_name)
    
    if missing_deps:
        error_msg = f"缺少必需依赖: {', '.join(missing_deps)}\n"
        error_msg += f"请运行: pip install {' '.join(missing_deps)}"
        return False, missing_deps, error_msg
    
    if optional_missing:
        warning_msg = f"缺少可选依赖: {', '.join(optional_missing)}\n"
        warning_msg += "部分功能可能不可用（如API密钥加密）\n"
        warning_msg += f"建议安装: pip install {' '.join(optional_missing)}"
        print(f"警告: {warning_msg}")
    
    return True, [], None

def load_custom_config(config_path):
    """
    加载自定义配置文件
    
    Args:
        config_path (str): 配置文件路径
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    # 动态导入配置模块
    import importlib.util
    spec = importlib.util.spec_from_file_location("custom_config", config_path)
    custom_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(custom_config)
    
    # 更新全局配置
    import config
    for attr_name in dir(custom_config):
        if not attr_name.startswith('_'):
            setattr(config, attr_name, getattr(custom_config, attr_name))
    
    logging.getLogger(__name__).info(f"已加载自定义配置: {config_path}")

def handle_quick_operations(args):
    """处理快速操作（不启动主界面）"""
    logger = logging.getLogger(__name__)
    
    # 快速余额查询
    if args.balance:
        logger.info("执行快速余额查询")
        try:
            # 修复：使用正确的函数名
            from balance_service import query_balance_simple
            api_key = args.api_key
            if not api_key:
                from crypto_utils import load_api_key_from_file
                api_key = load_api_key_from_file()
            
            if not api_key:
                print("错误: 未找到API密钥")
                print("请使用 --api-key 参数或先运行程序设置API密钥")
                return True
            
            # 修复：使用正确的函数调用
            success, balance_data, error_msg = query_balance_simple(api_key)
            if success:
                from balance_service import format_balance_simple
                print(format_balance_simple(balance_data))
            else:
                print(f"余额查询失败: {error_msg}")
            return True
        except Exception as e:
            logger.error(f"余额查询失败: {e}")
            print(f"余额查询失败: {e}")
            return True
    
    # 快速模型列表
    if args.models:
        logger.info("执行快速模型列表查询")
        try:
            from openai import OpenAI
            from config import DEEPSEEK_API_BASE_URL_V1
            from model_manager import filter_model_list
            
            api_key = args.api_key
            if not api_key:
                from crypto_utils import load_api_key_from_file
                api_key = load_api_key_from_file()
            
            if not api_key:
                print("错误: 未找到API密钥")
                print("请使用 --api-key 参数或先运行程序设置API密钥")
                return True
            
            # 获取模型列表
            client = OpenAI(api_key=api_key, base_url=DEEPSEEK_API_BASE_URL_V1)
            models_response = client.models.list()
            raw_models = [model.id for model in models_response.data]
            filtered_models = filter_model_list(raw_models)
            
            print(f"可用模型 (共 {len(filtered_models)} 个):")
            for i, model in enumerate(filtered_models, 1):
                print(f"  {i:2d}. {model}")
            
            if len(raw_models) != len(filtered_models):
                print(f"\n注意: 总共 {len(raw_models)} 个模型，已过滤显示 {len(filtered_models)} 个")
            
            return True
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            print(f"获取模型列表失败: {e}")
            return True
    
    # 快速聊天
    if args.chat:
        logger.info(f"执行快速聊天: {args.chat}")
        try:
            # 修复：使用正确的导入
            from chat_handler import run_cli_chat
            from client_manager import create_client_manager
            from config import DEEPSEEK_API_BASE_URL_V1
            
            api_key = args.api_key
            if not api_key:
                from crypto_utils import load_api_key_from_file
                api_key = load_api_key_from_file()
            
            if not api_key:
                print("错误: 未找到API密钥")
                return True
            
            # 创建客户端
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=DEEPSEEK_API_BASE_URL_V1)
            
            # 运行CLI聊天
            run_cli_chat(client, args.chat)
            return True
        except Exception as e:
            logger.error(f"快速聊天失败: {e}")
            print(f"快速聊天失败: {e}")
            return True
    
    return False

def run_gui_mode(args):
    """运行GUI模式"""
    logger = logging.getLogger(__name__)
    logger.info("启动GUI模式")
    
    try:
        # 检查GUI依赖
        import tkinter as tk
        from tkinter import messagebox
        
        # 导入GUI模块
        from gui_main import DeepSeekGUI
        
        # 创建主窗口
        root = tk.Tk()
        root.title(f"{APP_INFO['name']} {APP_INFO['version']}")
        
        # 设置窗口图标（如果存在）
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except Exception:
            pass
        
        # 创建GUI应用，添加详细错误处理
        try:
            app = DeepSeekGUI(root)
        except Exception as e:
            logger.error(f"创建GUI应用失败: {e}", exc_info=True)
            print(f"详细错误信息: {e}")
            
            # 检查具体的错误类型
            error_str = str(e)
            if "MarkdownText" in error_str:
                print("可能是markdown_widget模块有问题")
            elif "status_monitor" in error_str or "StatusMonitorController" in error_str:
                print("可能是status_monitor模块有问题")
            elif "config" in error_str:
                print("可能是config模块有问题")
            elif "AttributeError" in error_str and "status" in error_str:
                print("可能是状态监控系统集成问题")
            elif "ImportError" in error_str:
                print("可能是依赖模块缺失")
            
            # 尝试显示错误对话框
            try:
                messagebox.showerror("错误", f"GUI创建失败: {e}\n\n请检查相关模块是否正确安装")
            except:
                pass
            
            # 提供解决建议
            print("\n解决建议:")
            print("1. 检查所有模块文件是否存在且语法正确")
            print("2. 尝试运行: python main.py --test-modules")
            print("3. 如果状态监控有问题，可以临时禁用高级功能")
            print("4. 使用 --debug 参数获取更详细的错误信息")
            
            sys.exit(1)
        
        # 检查必要的依赖模块
        try:
            # 测试导入关键模块
            import markdown_widget
            import crypto_utils
            logger.info("核心GUI依赖模块检查通过")
            
            # 尝试导入状态监控模块
            try:
                import status_monitor
                logger.info("状态监控模块可用")
            except ImportError as ie:
                logger.warning(f"状态监控模块不可用: {ie}")
                print(f"警告: 状态监控功能可能不可用: {ie}")
                
        except ImportError as ie:
            logger.warning(f"部分GUI模块不可用: {ie}")
            print(f"警告: 部分GUI功能可能不可用: {ie}")
        
        # 修复：创建管理器并正确集成
        try:
            from client_manager import create_client_manager
            from model_manager import create_model_manager  
            from chat_handler import create_chat_handler
            from balance_service import create_balance_service
            from http_utils import create_http_error_handler
            
            # 创建各个管理器并绑定到GUI
            client_manager = create_client_manager(app)
            app.client_manager = client_manager
            
            model_manager = create_model_manager(app, client_manager)
            app.model_manager = model_manager
            
            chat_handler = create_chat_handler(app, client_manager, model_manager)
            app.chat_handler = chat_handler
            
            balance_service = create_balance_service(app, client_manager)
            app.balance_service = balance_service
            
            http_error_handler = create_http_error_handler(app)
            app.http_error_handler = http_error_handler
            
            # 重写GUI的关键方法以使用管理器
            def enhanced_initialize_client():
                try:
                    api_key = app.get_api_key_from_entry()
                    if not api_key:
                        app.show_error_message("错误", "请输入API密钥")
                        if hasattr(app, 'status_controller'):
                            app.status_controller.update_client_status(False, False)
                        return
                    
                    # 使用客户端管理器初始化
                    success = app.client_manager.initialize_client(api_key)
                    if success:
                        app.print_out("客户端初始化成功！")
                        # 更新状态
                        if hasattr(app, 'status_controller'):
                            app.status_controller.update_client_status(True, True)
                        app.update_buttons_state()
                        # 启用刷新模型按钮
                        if hasattr(app, 'refresh_models_btn'):
                            app.refresh_models_btn.config(state=tk.NORMAL)
                    else:
                        app.print_out("客户端初始化失败！")
                        if hasattr(app, 'status_controller'):
                            app.status_controller.update_client_status(True, False)
                except Exception as e:
                    app.print_out(f"初始化过程中发生错误: {e}")
                    if hasattr(app, 'status_controller'):
                        app.status_controller.update_client_status(True, False)
            
            def enhanced_refresh_models():
                try:
                    if not hasattr(app, 'model_manager'):
                        app.show_error_message("错误", "模型管理器未初始化")
                        return
                    
                    success = app.model_manager.refresh_models()
                    if success:
                        app.print_out("模型列表刷新成功")
                    else:
                        app.print_out("模型列表刷新失败")
                except Exception as e:
                    app.print_out(f"刷新模型时发生错误: {e}")
            
            def enhanced_on_model_selected(event=None):
                try:
                    if not hasattr(app, 'model_manager'):
                        return
                    
                    selected = app.get_selected_model()
                    if selected:
                        success = app.model_manager.select_model(selected)
                        if success:
                            app.print_out(f"已选择模型: {selected}")
                            # 启用聊天相关功能
                            if hasattr(app, 'update_chat_status'):
                                app.update_chat_status("ready")
                            app.update_buttons_state()
                except Exception as e:
                    app.print_out(f"选择模型时发生错误: {e}")
            
            # 替换GUI的方法
            app.initialize_client = enhanced_initialize_client
            app.refresh_models = enhanced_refresh_models
            app.on_model_selected = enhanced_on_model_selected
            
            logger.info("所有管理器创建并集成成功")
            
        except ImportError as ie:
            logger.warning(f"部分管理器创建失败: {ie}")
            print(f"警告: 部分功能可能不可用: {ie}")
            
            # 创建基本的客户端管理器
            try:
                from client_manager import ClientManager
                app.client_manager = ClientManager(app)
                logger.info("创建了基本客户端管理器")
            except Exception as e:
                logger.error(f"无法创建客户端管理器: {e}")
        except Exception as e:
            logger.error(f"创建管理器时发生错误: {e}")
            print(f"警告: 管理器创建失败，某些功能可能不可用: {e}")
        
        # 应用命令行参数
        if args.api_key:
            try:
                app.api_key_entry.delete(0, tk.END)
                app.api_key_entry.insert(0, args.api_key)
                # 立即更新状态
                if hasattr(app, 'status_controller'):
                    app.status_controller.update_client_status(True, False)
            except Exception as e:
                logger.warning(f"设置API密钥时出错: {e}")
        
        if args.api_base:
            # 更新API基础URL
            import config
            config.DEEPSEEK_API_BASE_URL_V1 = args.api_base
            logger.info(f"使用自定义API基础URL: {args.api_base}")
        
        # 设置窗口关闭事件
        def on_closing():
            logger.info("用户关闭GUI窗口")
            try:
                # 停止网络监控线程
                if hasattr(app, 'status_controller'):
                    app.status_controller.destroy()
                
                # 清理聊天处理器
                if hasattr(app, 'chat_handler') and hasattr(app.chat_handler, 'destroy'):
                    app.chat_handler.destroy()
                
                # 清理余额服务
                if hasattr(app, 'balance_service') and hasattr(app.balance_service, 'destroy'):
                    app.balance_service.destroy()
                
            except Exception as e:
                logger.error(f"清理资源时出错: {e}")
            finally:
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # 显示启动信息
        try:
            app.print_out(f"欢迎使用 {APP_INFO['name']} {APP_INFO['version']}")
            app.print_out(f"构建日期: {APP_INFO['build_date']}")
            
            if args.debug:
                app.print_out("调试模式已启用")
                
            # 提示用户下一步操作
            app.print_out("请输入API密钥并点击'初始化'按钮开始使用")
            
        except Exception as e:
            logger.warning(f"显示启动信息时出错: {e}")
        
        logger.info("GUI初始化完成，开始主循环")
        
        # 启动主循环
        root.mainloop()
        
    except ImportError as e:
        error_msg = f"GUI依赖不可用: {e}\n请安装tkinter或使用 --cli 参数"
        logger.error(error_msg)
        print(error_msg)
        
        # 检查具体缺失的模块
        if "tkinter" in str(e):
            print("Tkinter未安装，请安装Python的Tkinter模块")
        elif "markdown" in str(e):
            print("Markdown相关模块缺失，请检查markdown_widget.py")
        
        sys.exit(1)
    except Exception as e:
        logger.error(f"GUI模式启动失败: {e}", exc_info=True)
        print(f"GUI模式启动失败: {e}")
        
        # 在调试模式下显示完整堆栈跟踪
        if args.debug:
            import traceback
            traceback.print_exc()
        
        sys.exit(1)

def run_cli_mode(args):
    """运行CLI模式"""
    logger = logging.getLogger(__name__)
    logger.info("启动CLI模式")
    
    try:
        # 修复：使用正确的CLI模块导入
        from cli_client import DeepSeekCLI
        
        # 创建CLI客户端
        cli = DeepSeekCLI()
        
        # 应用命令行参数
        if args.api_key:
            cli.api_key = args.api_key
            logger.info("使用命令行提供的API密钥")
        
        if args.api_base:
            # 更新API基础URL
            import config
            config.DEEPSEEK_API_BASE_URL_V1 = args.api_base
            logger.info(f"使用自定义API基础URL: {args.api_base}")
        
        # 显示启动信息
        print(f"\n{APP_INFO['name']} {APP_INFO['version']}")
        print(f"构建日期: {APP_INFO['build_date']}")
        print(f"运行模式: CLI")
        
        if args.debug:
            print("调试模式已启用")
        
        # 运行CLI
        guided_mode = args.guided
        cli.run(guided_mode=guided_mode)
        
    except KeyboardInterrupt:
        logger.info("用户中断CLI程序")
        print("\n\n程序被用户中断")
    except Exception as e:
        logger.error(f"CLI模式运行失败: {e}")
        print(f"CLI模式运行失败: {e}")
        sys.exit(1)

def check_environment():
    """
    检查运行环境
    
    Returns:
        dict: 环境信息
    """
    env_info = {
        'python_version': sys.version,
        'platform': sys.platform,
        'executable': sys.executable,
        'has_display': bool(os.environ.get('DISPLAY') or os.name == 'nt'),
        'is_interactive': hasattr(sys.stdin, 'isatty') and sys.stdin.isatty(),
        'encoding': sys.getdefaultencoding()
    }
    
    return env_info

def print_environment_info(env_info):
    """
    打印环境信息（调试模式）
    
    Args:
        env_info (dict): 环境信息
    """
    print("运行环境信息:")
    print(f"  Python版本: {env_info['python_version'].split()[0]}")
    print(f"  平台: {env_info['platform']}")
    print(f"  显示环境: {'是' if env_info['has_display'] else '否'}")
    print(f"  交互式终端: {'是' if env_info['is_interactive'] else '否'}")
    print(f"  字符编码: {env_info['encoding']}")
    print()

def main():
    """主程序入口"""
    try:
        # 解析命令行参数
        args = parse_command_line_args()
        
        # 设置日志
        setup_logging(args)
        logger = logging.getLogger(__name__)
        
        # 检查环境
        env_info = check_environment()
        logger.debug(f"运行环境: {env_info}")
        
        if args.debug:
            print_environment_info(env_info)
        
        # 验证依赖
        success, missing_deps, error_msg = validate_dependencies()
        if not success:
            logger.error(f"依赖检查失败: {error_msg}")
            print(f"错误: {error_msg}")
            sys.exit(1)
        
        # 加载自定义配置
        if args.config and not args.no_config:
            try:
                load_custom_config(args.config)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                print(f"错误: 加载配置文件失败: {e}")
                sys.exit(1)
        
        # 处理快速操作
        if handle_quick_operations(args):
            logger.info("快速操作完成，程序退出")
            sys.exit(0)
        
        # 确定运行模式
        if args.gui:
            mode = "gui"
        elif args.cli:
            mode = "cli"
        else:
            mode = detect_startup_mode()
        
        logger.info(f"确定运行模式: {mode}")
        
        # 启动对应模式
        if mode == "gui":
            run_gui_mode(args)
        else:
            run_cli_mode(args)
        
        logger.info("程序正常退出")
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except SystemExit:
        # 重新抛出SystemExit，避免被捕获
        raise
    except Exception as e:
        # 捕获所有未处理的异常
        try:
            logger = logging.getLogger(__name__)
            logger.critical(f"程序发生致命错误: {e}", exc_info=True)
        except:
            pass
        
        print(f"致命错误: {e}")
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)

# 便捷函数
def run_gui():
    """直接启动GUI模式的便捷函数"""
    sys.argv.extend(['--gui'])
    main()

def run_cli():
    """直接启动CLI模式的便捷函数"""
    sys.argv.extend(['--cli'])
    main()

def run_guided_setup():
    """直接启动引导设置的便捷函数"""
    sys.argv.extend(['--cli', '--guided'])
    main()

# 兼容性入口点
def gui_main():
    """GUI模式入口点（向后兼容）"""
    run_gui()

def cli_main():
    """CLI模式入口点（向后兼容）"""
    run_cli()

# 调试和测试函数
def test_dependencies():
    """测试依赖项"""
    print("测试程序依赖项...")
    success, missing, error = validate_dependencies()
    
    if success:
        print("✓ 所有必需依赖项都已安装")
    else:
        print(f"✗ 依赖项检查失败: {error}")
    
    return success

def test_modules():
    """测试模块导入"""
    modules_to_test = [
        'config',
        'crypto_utils', 
        'client_manager',
        'model_manager',
        'chat_handler',
        'balance_service',
        'http_utils',
        'gui_main',
        'cli_client'
    ]
    
    print("测试模块导入...")
    failed_modules = []
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except ImportError as e:
            print(f"✗ {module_name}: {e}")
            failed_modules.append(module_name)
    
    if failed_modules:
        print(f"\n失败的模块: {', '.join(failed_modules)}")
        return False
    else:
        print("\n所有模块导入成功")
        return True

def show_system_info():
    """显示系统信息"""
    env_info = check_environment()
    
    print(f"{APP_INFO['name']} 系统信息")
    print("=" * 40)
    print(f"程序版本: {APP_INFO['version']}")
    print(f"构建日期: {APP_INFO['build_date']}")
    print(f"作者: {APP_INFO['author']}")
    print()
    
    print_environment_info(env_info)
    
    print("依赖项检查:")
    test_dependencies()
    print()
    
    print("模块检查:")
    test_modules()

# 程序信息显示
def show_version():
    """显示版本信息"""
    print(f"{APP_INFO['name']} {APP_INFO['version']}")
    print(f"构建日期: {APP_INFO['build_date']}")
    print(f"作者: {APP_INFO['author']}")
    print(f"许可证: {APP_INFO['license']}")

def show_help():
    """显示帮助信息"""
    help_text = f"""
{APP_INFO['name']} - {APP_INFO['description']}

用法:
    python main.py [选项]

模式选择:
    --gui               强制使用图形界面模式
    --cli               强制使用命令行模式
    
CLI选项:
    --guided            使用引导式设置（仅CLI模式）
    
快速操作:
    --balance           快速查询余额并退出
    --models            列出可用模型并退出
    --chat MODEL        直接开始与指定模型聊天
    
配置选项:
    --config FILE       使用指定的配置文件
    --no-config         不加载配置文件
    --api-key KEY       直接指定API密钥
    --api-base URL      指定API基础URL
    
调试选项:
    --debug             启用调试模式
    --log-file FILE     指定日志文件
    --log-level LEVEL   设置日志级别
    
其他:
    --version, -v       显示版本信息
    --help, -h          显示此帮助信息

示例:
    python main.py                      # 自动检测模式
    python main.py --gui               # GUI模式
    python main.py --cli --guided      # CLI引导模式
    python main.py --balance           # 快速余额查询
    python main.py --debug             # 调试模式

更多信息请访问: {APP_INFO.get('url', 'https://github.com/your-repo')}
"""
    print(help_text)

# 入口点检查
if __name__ == "__main__":
    # 特殊命令处理
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test-deps':
            test_dependencies()
            sys.exit(0)
        elif sys.argv[1] == '--test-modules':
            test_modules()
            sys.exit(0)
        elif sys.argv[1] == '--system-info':
            show_system_info()
            sys.exit(0)
        elif sys.argv[1] == '--version-only':
            show_version()
            sys.exit(0)
        elif sys.argv[1] == '--help-only':
            show_help()
            sys.exit(0)
    
    # 运行主程序
    main()

# 模块级别的元数据（供其他模块查询）
__version__ = APP_INFO['version']
__author__ = APP_INFO['author']
__license__ = APP_INFO['license']
__description__ = APP_INFO['description']

# 导出的公共接口
__all__ = [
    'main',
    'run_gui', 
    'run_cli', 
    'run_guided_setup',
    'gui_main', 
    'cli_main',
    'test_dependencies',
    'test_modules',
    'show_system_info',
    'show_version',
    'show_help'
]