from flask import Flask, render_template, request, jsonify, Response, stream_template
import json
import requests
import time
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading
import queue
import base64
from urllib.parse import urljoin

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'deepseek-web-client-secret-key-2025')

# DeepSeek API 配置
DEEPSEEK_API_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_BALANCE_URL = "https://api.deepseek.com/user/balance"
DEEPSEEK_USAGE_URL = "https://api.deepseek.com/user/usage"

# 请求超时配置
REQUEST_TIMEOUT = 30
STREAM_TIMEOUT = 60

# 存储活跃的流式连接
active_streams = {}

class DeepSeekAPIClient:
    """DeepSeek API 客户端封装类"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = DEEPSEEK_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'DeepSeek-Web-Client/0.7.2'
        })
    
    def test_connection(self) -> Dict[str, Any]:
        """测试API连接"""
        try:
            response = self.session.get(
                f"{self.base_url}/models",
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"API连接测试失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_models(self) -> Dict[str, Any]:
        """获取可用模型列表"""
        try:
            response = self.session.get(
                f"{self.base_url}/models",
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            # 提取模型名称并过滤
            models = []
            for model in data.get('data', []):
                model_id = model.get('id', '')
                # 过滤聊天模型
                if any(keyword in model_id.lower() for keyword in ['chat', 'coder', 'deepseek']):
                    models.append(model_id)
            
            # 如果没有找到聊天模型，返回所有模型
            if not models:
                models = [model.get('id', '') for model in data.get('data', [])]
            
            return {'success': True, 'models': models}
        except requests.exceptions.RequestException as e:
            logger.error(f"获取模型列表失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_balance(self) -> Dict[str, Any]:
        """获取账户余额"""
        try:
            response = self.session.get(
                DEEPSEEK_BALANCE_URL,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"获取余额失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_usage(self) -> Dict[str, Any]:
        """获取使用统计"""
        try:
            response = self.session.get(
                DEEPSEEK_USAGE_URL,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"获取使用统计失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def chat_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict[str, Any]:
        """非流式聊天完成"""
        try:
            payload = {
                'model': model,
                'messages': messages,
                'stream': False,
                **kwargs
            }
            
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"聊天完成失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def chat_completion_stream(self, messages: List[Dict], model: str, **kwargs):
        """流式聊天完成生成器"""
        try:
            payload = {
                'model': model,
                'messages': messages,
                'stream': True,
                **kwargs
            }
            
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                stream=True,
                timeout=STREAM_TIMEOUT
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            yield data
                        except json.JSONDecodeError:
                            continue
        except requests.exceptions.RequestException as e:
            logger.error(f"流式聊天失败: {e}")
            yield {'error': str(e)}

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/initialize', methods=['POST'])
def initialize_api():
    """初始化API客户端"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': '请提供有效的API密钥'
            }), 400
        
        # 创建客户端并测试连接
        client = DeepSeekAPIClient(api_key)
        result = client.test_connection()
        
        if result['success']:
            # 存储客户端信息到会话（实际应用中应该使用更安全的方式）
            return jsonify({
                'success': True,
                'message': 'API客户端初始化成功',
                'models_available': len(result['data'].get('data', []))
            })
        else:
            return jsonify({
                'success': False,
                'error': f'API密钥验证失败: {result["error"]}'
            }), 401
            
    except Exception as e:
        logger.error(f"初始化API失败: {e}")
        return jsonify({
            'success': False,
            'error': f'初始化失败: {str(e)}'
        }), 500

@app.route('/api/models', methods=['POST'])
def get_models():
    """获取可用模型列表"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': '请提供API密钥'
            }), 400
        
        client = DeepSeekAPIClient(api_key)
        result = client.get_models()
        
        if result['success']:
            return jsonify({
                'success': True,
                'models': result['models'],
                'count': len(result['models'])
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取模型失败: {str(e)}'
        }), 500

@app.route('/api/balance', methods=['POST'])
def get_balance():
    """获取账户余额"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': '请提供API密钥'
            }), 400
        
        client = DeepSeekAPIClient(api_key)
        result = client.get_balance()
        
        if result['success']:
            balance_data = result['data']
            return jsonify({
                'success': True,
                'balance': balance_data,
                'is_available': balance_data.get('is_available', False),
                'balance_infos': balance_data.get('balance_infos', [])
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"获取余额失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取余额失败: {str(e)}'
        }), 500

@app.route('/api/usage', methods=['POST'])
def get_usage():
    """获取使用统计"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': '请提供API密钥'
            }), 400
        
        client = DeepSeekAPIClient(api_key)
        result = client.get_usage()
        
        if result['success']:
            return jsonify({
                'success': True,
                'usage': result['data']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"获取使用统计失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取使用统计失败: {str(e)}'
        }), 500

@app.route('/api/chat', methods=['POST'])
def chat_completion():
    """聊天完成（非流式）"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        model = data.get('model', '').strip()
        messages = data.get('messages', [])
        
        # 验证参数
        if not api_key:
            return jsonify({
                'success': False,
                'error': '请提供API密钥'
            }), 400
        
        if not model:
            return jsonify({
                'success': False,
                'error': '请选择模型'
            }), 400
        
        if not messages:
            return jsonify({
                'success': False,
                'error': '请提供对话消息'
            }), 400
        
        # 提取其他参数
        temperature = data.get('temperature', 1.0)
        max_tokens = data.get('max_tokens', 2048)
        top_p = data.get('top_p', 0.95)
        frequency_penalty = data.get('frequency_penalty', 0.0)
        
        # 构建参数
        params = {
            'temperature': float(temperature),
            'max_tokens': int(max_tokens),
            'top_p': float(top_p),
            'frequency_penalty': float(frequency_penalty)
        }
        
        client = DeepSeekAPIClient(api_key)
        result = client.chat_completion(messages, model, **params)
        
        if result['success']:
            response_data = result['data']
            return jsonify({
                'success': True,
                'response': response_data,
                'message': response_data['choices'][0]['message']['content'],
                'usage': response_data.get('usage', {})
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"聊天完成失败: {e}")
        return jsonify({
            'success': False,
            'error': f'聊天失败: {str(e)}'
        }), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """流式聊天完成"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        model = data.get('model', '').strip()
        messages = data.get('messages', [])
        
        # 验证参数
        if not api_key:
            return jsonify({
                'success': False,
                'error': '请提供API密钥'
            }), 400
        
        if not model:
            return jsonify({
                'success': False,
                'error': '请选择模型'
            }), 400
        
        if not messages:
            return jsonify({
                'success': False,
                'error': '请提供对话消息'
            }), 400
        
        # 提取其他参数
        temperature = data.get('temperature', 1.0)
        max_tokens = data.get('max_tokens', 2048)
        top_p = data.get('top_p', 0.95)
        frequency_penalty = data.get('frequency_penalty', 0.0)
        
        # 构建参数
        params = {
            'temperature': float(temperature),
            'max_tokens': int(max_tokens),
            'top_p': float(top_p),
            'frequency_penalty': float(frequency_penalty)
        }
        
        def generate():
            """流式响应生成器"""
            try:
                client = DeepSeekAPIClient(api_key)
                
                for chunk in client.chat_completion_stream(messages, model, **params):
                    if 'error' in chunk:
                        yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                        break
                    
                    # 提取内容
                    choices = chunk.get('choices', [])
                    if choices:
                        delta = choices[0].get('delta', {})
                        content = delta.get('content', '')
                        
                        if content:
                            yield f"data: {json.dumps({'content': content})}\n\n"
                        
                        # 检查是否完成
                        if choices[0].get('finish_reason'):
                            yield f"data: {json.dumps({'finished': True, 'reason': choices[0]['finish_reason']})}\n\n"
                            break
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"流式聊天错误: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(
            generate(),
            mimetype='text/plain',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        logger.error(f"流式聊天初始化失败: {e}")
        return jsonify({
            'success': False,
            'error': f'流式聊天失败: {str(e)}'
        }), 500

@app.route('/api/ping', methods=['GET', 'POST'])
def ping():
    """健康检查和延迟测试"""
    try:
        start_time = time.time()
        
        # 简单的网络测试
        try:
            response = requests.get(
                "https://api.deepseek.com",
                timeout=5,
                headers={'User-Agent': 'DeepSeek-Web-Client/0.7.2'}
            )
            network_ok = True
            status_code = response.status_code
        except:
            network_ok = False
            status_code = 0
        
        latency = round((time.time() - start_time) * 1000, 2)
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'latency_ms': latency,
            'network_ok': network_ok,
            'status_code': status_code,
            'server': 'DeepSeek Web Client v0.7.2'
        })
        
    except Exception as e:
        logger.error(f"Ping失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/validate', methods=['POST'])
def validate_api_key():
    """验证API密钥"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({
                'success': False,
                'valid': False,
                'error': '请提供API密钥'
            }), 400
        
        client = DeepSeekAPIClient(api_key)
        result = client.test_connection()
        
        return jsonify({
            'success': True,
            'valid': result['success'],
            'error': result.get('error', None) if not result['success'] else None
        })
        
    except Exception as e:
        logger.error(f"API密钥验证失败: {e}")
        return jsonify({
            'success': False,
            'valid': False,
            'error': f'验证失败: {str(e)}'
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取服务状态"""
    try:
        return jsonify({
            'success': True,
            'status': 'running',
            'version': '0.7.2.1.f.0.0.1.a',
            'timestamp': datetime.now().isoformat(),
            'active_streams': len(active_streams),
            'uptime': time.time() - app.start_time if hasattr(app, 'start_time') else 0
        })
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'error': '页面未找到'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"内部服务器错误: {error}")
    return jsonify({
        'success': False,
        'error': '内部服务器错误'
    }), 500

def init_app():
    """初始化应用"""
    app.start_time = time.time()
    logger.info("DeepSeek Web Client 初始化完成")

# 应用上下文初始化
with app.app_context():
    init_app()

if __name__ == '__main__':
    # 配置运行参数
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    logger.info(f"DeepSeek Web Client 正在启动...")
    logger.info(f"访问地址: http://{host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )