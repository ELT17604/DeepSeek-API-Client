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

import os
import base64
import hashlib
import uuid
from config import API_KEY_FILENAME, ENCRYPTION_SALT, DEFAULT_ENCRYPTION_SEED, SECURITY_CONFIG

# 确保导入config模块
from config import SECURITY_CONFIG

# 尝试导入加密库
try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    print("cryptography库未安装，API Key将无法加密。请使用 pip install cryptography 安装。")

def get_machine_id():
    """获取机器特定标识符"""
    try:
        # 使用机器ID作为硬件特征
        machine_id = uuid.getnode()
        return str(machine_id)
    except Exception:
        # 如果无法获取机器ID，使用默认值
        return "default_machine_id"

def generate_encryption_key():
    """基于机器特定信息生成稳定的加密密钥"""
    try:
        # 获取机器ID
        machine_id = get_machine_id()
        
        # 组合机器ID和盐值创建密钥材料
        key_material = f"{ENCRYPTION_SALT}-{machine_id}".encode()
        
        # 生成符合Fernet要求的32字节密钥并进行base64编码
        key = base64.urlsafe_b64encode(hashlib.sha256(key_material).digest())
        return key
    except Exception as e:
        print(f"生成加密密钥时出错: {e}")
        # 如果出错，使用默认密钥（这不够安全，但比没有加密好）
        fallback_material = DEFAULT_ENCRYPTION_SEED.encode()
        return base64.urlsafe_b64encode(hashlib.sha256(fallback_material).digest())

def encrypt_api_key(api_key):
    """
    加密API密钥
    
    Args:
        api_key (str): 要加密的API密钥
        
    Returns:
        str: 加密后的密钥字符串，如果加密失败返回None
    """
    if not api_key:
        return None
        
    if not HAS_CRYPTO:
        print("警告: 加密库不可用，API Key将以明文形式存储（不安全）")
        return api_key  # 降级到明文存储
        
    try:
        key = generate_encryption_key()
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(api_key.encode())
        return encrypted_data.decode()
    except Exception as e:
        print(f"加密API密钥时出错: {e}")
        return None

def decrypt_api_key(encrypted_api_key):
    """
    解密API密钥
    
    Args:
        encrypted_api_key (str): 加密的API密钥
        
    Returns:
        str: 解密后的API密钥，如果解密失败返回None
    """
    if not encrypted_api_key:
        return None
        
    if not HAS_CRYPTO:
        # 如果没有加密库，假设存储的是明文
        return encrypted_api_key
        
    try:
        key = generate_encryption_key()
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_api_key.encode())
        return decrypted_data.decode()
    except Exception as e:
        print(f"解密API密钥时出错: {e}")
        # 尝试将其作为明文返回（兼容性处理）
        try:
            # 检查是否是有效的明文API密钥格式
            if encrypted_api_key.startswith(('sk-', 'api-')):
                print("检测到可能的明文API密钥，正在以明文模式加载")
                return encrypted_api_key
        except Exception:
            pass
        return None

def save_api_key_to_file(api_key):
    """
    将API密钥加密后保存到文件
    
    Args:
        api_key (str): 要保存的API密钥
        
    Returns:
        bool: 保存成功返回True，失败返回False
    """
    if not api_key:
        print("错误: 空API密钥无法保存")
        return False
        
    try:
        # 确保目录存在
        api_key_dir = os.path.dirname(API_KEY_FILENAME)
        if api_key_dir and not os.path.exists(api_key_dir):
            os.makedirs(api_key_dir, mode=0o700)  # 创建目录，仅当前用户可访问
            
        # 加密API密钥
        encrypted_key = encrypt_api_key(api_key)
        if encrypted_key is None:
            print("错误: API密钥加密失败")
            return False
            
        # 写入文件
        with open(API_KEY_FILENAME, "w", encoding='utf-8') as f:
            f.write(encrypted_key)
            
        # 设置文件权限（仅当前用户可读写）
        try:
            if hasattr(os, 'chmod'):
                os.chmod(API_KEY_FILENAME, SECURITY_CONFIG["file_permissions"]["api_key_file"])
        except Exception as perm_error:
            print(f"警告: 无法设置文件权限: {perm_error}")
            
        return True
        
    except Exception as e:
        print(f"保存API密钥时出错: {e}")
        return False

def load_api_key_from_file():
    """
    从文件加载并解密API密钥
    
    Returns:
        str: 解密后的API密钥，如果加载失败返回None
    """
    try:
        if not os.path.exists(API_KEY_FILENAME):
            return None
            
        # 检查文件权限
        try:
            file_stat = os.stat(API_KEY_FILENAME)
            file_mode = file_stat.st_mode & 0o777
            expected_mode = SECURITY_CONFIG["file_permissions"]["api_key_file"]
            
            if file_mode != expected_mode:
                print(f"警告: API密钥文件权限不安全 ({oct(file_mode)})，建议权限: {oct(expected_mode)}")
        except Exception:
            pass  # 权限检查失败不影响加载
            
        # 读取并解密
        with open(API_KEY_FILENAME, "r", encoding='utf-8') as f:
            encrypted_content = f.read().strip()
            
        if not encrypted_content:
            print("警告: API密钥文件为空")
            return None
            
        decrypted_key = decrypt_api_key(encrypted_content)
        
        if decrypted_key is None:
            print("警告: API密钥解密失败")
            return None
            
        return decrypted_key
        
    except FileNotFoundError:
        return None
    except PermissionError as e:
        print(f"权限错误: 无法读取API密钥文件: {e}")
        return None
    except Exception as e:
        print(f"加载API密钥时出错: {e}")
        return None

def delete_api_key_file():
    """
    安全删除存储API密钥的文件
    
    Returns:
        bool: 删除成功返回True，失败返回False
    """
    if not os.path.exists(API_KEY_FILENAME):
        return True  # 文件不存在视为删除成功
        
    try:
        # 安全删除：先用随机数据覆写文件
        try:
            file_size = os.path.getsize(API_KEY_FILENAME)
            if file_size > 0:
                with open(API_KEY_FILENAME, "r+b") as f:
                    # 写入随机数据覆盖原内容
                    import secrets
                    random_data = secrets.token_bytes(file_size)
                    f.write(random_data)
                    f.flush()
                    os.fsync(f.fileno())  # 强制写入磁盘
        except Exception as overwrite_error:
            print(f"警告: 无法安全覆写文件内容: {overwrite_error}")
            
        # 删除文件
        os.remove(API_KEY_FILENAME)
        return True
        
    except PermissionError as e:
        print(f"权限错误: 无法删除API密钥文件: {e}")
        return False
    except Exception as e:
        print(f"删除API密钥文件时出错: {e}")
        return False

def validate_api_key_format(api_key):
    """
    验证API密钥格式是否有效
    
    Args:
        api_key (str): 要验证的API密钥
        
    Returns:
        bool: 格式有效返回True，否则返回False
    """
    if not api_key or not isinstance(api_key, str):
        return False
        
    # 基本长度检查
    if len(api_key) < 10:
        return False
        
    # 检查是否包含常见的API密钥前缀
    valid_prefixes = ['sk-', 'api-', 'key-']
    has_valid_prefix = any(api_key.startswith(prefix) for prefix in valid_prefixes)
    
    # 检查是否只包含有效字符（字母、数字、短横线、下划线）
    import re
    valid_chars = re.match(r'^[a-zA-Z0-9_-]+$', api_key)
    
    return has_valid_prefix and bool(valid_chars)

def mask_api_key(api_key, show_prefix=None, show_suffix=None, mask_char=None):
    """
    掩码显示API密钥
    
    Args:
        api_key (str): 要掩码的API密钥
        show_prefix (int): 显示前几位明文，默认从配置读取
        show_suffix (int): 显示后几位明文，默认从配置读取
        mask_char (str): 掩码字符，默认从配置读取
        
    Returns:
        str: 掩码后的API密钥
    """
    if not api_key:
        return ""
        
    # 使用配置中的默认值
    if show_prefix is None:
        show_prefix = SECURITY_CONFIG["api_key_mask"]["show_prefix"]
    if show_suffix is None:
        show_suffix = SECURITY_CONFIG["api_key_mask"]["show_suffix"]
    if mask_char is None:
        mask_char = SECURITY_CONFIG["api_key_mask"]["mask_char"]
        
    # 如果密钥长度太短，全部掩码
    total_show_chars = show_prefix + show_suffix
    if len(api_key) <= total_show_chars:
        return mask_char * len(api_key)
        
    # 生成掩码
    prefix = api_key[:show_prefix]
    suffix = api_key[-show_suffix:] if show_suffix > 0 else ""
    mask_length = len(api_key) - show_prefix - show_suffix
    mask = mask_char * mask_length
    
    return prefix + mask + suffix

def get_api_key_info():
    """
    获取API密钥文件信息
    
    Returns:
        dict: 包含文件信息的字典
    """
    info = {
        "file_exists": False,
        "file_path": API_KEY_FILENAME,
        "file_size": 0,
        "is_encrypted": False,
        "encryption_available": HAS_CRYPTO,
        "last_modified": None
    }
    
    try:
        if os.path.exists(API_KEY_FILENAME):
            info["file_exists"] = True
            
            # 获取文件大小
            info["file_size"] = os.path.getsize(API_KEY_FILENAME)
            
            # 获取修改时间
            import datetime
            mtime = os.path.getmtime(API_KEY_FILENAME)
            info["last_modified"] = datetime.datetime.fromtimestamp(mtime)
            
            # 尝试检测是否是加密内容
            with open(API_KEY_FILENAME, "r", encoding='utf-8') as f:
                content = f.read().strip()
                
            # 简单检测：如果内容不是明文API密钥格式，认为是加密的
            if content and not validate_api_key_format(content):
                info["is_encrypted"] = True
                
    except Exception as e:
        print(f"获取API密钥文件信息时出错: {e}")
        
    return info

def backup_api_key_file(backup_path=None):
    """
    备份API密钥文件
    
    Args:
        backup_path (str): 备份文件路径，如果为None则自动生成
        
    Returns:
        str: 备份文件路径，如果备份失败返回None
    """
    if not os.path.exists(API_KEY_FILENAME):
        print("错误: API密钥文件不存在，无法备份")
        return None
        
    try:
        if backup_path is None:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{API_KEY_FILENAME}.backup_{timestamp}"
            
        # 复制文件
        import shutil
        shutil.copy2(API_KEY_FILENAME, backup_path)
        
        # 设置备份文件权限
        try:
            if hasattr(os, 'chmod'):
                os.chmod(backup_path, SECURITY_CONFIG["file_permissions"]["api_key_file"])
        except Exception:
            pass
            
        print(f"API密钥文件已备份到: {backup_path}")
        return backup_path
        
    except Exception as e:
        print(f"备份API密钥文件时出错: {e}")
        return None

def restore_api_key_file(backup_path):
    """
    从备份恢复API密钥文件
    
    Args:
        backup_path (str): 备份文件路径
        
    Returns:
        bool: 恢复成功返回True，失败返回False
    """
    if not os.path.exists(backup_path):
        print(f"错误: 备份文件不存在: {backup_path}")
        return False
        
    try:
        # 如果原文件存在，先备份
        if os.path.exists(API_KEY_FILENAME):
            current_backup = backup_api_key_file()
            if current_backup:
                print(f"原API密钥文件已备份到: {current_backup}")
                
        # 复制备份文件到原位置
        import shutil
        shutil.copy2(backup_path, API_KEY_FILENAME)
        
        # 设置文件权限
        try:
            if hasattr(os, 'chmod'):
                os.chmod(API_KEY_FILENAME, SECURITY_CONFIG["file_permissions"]["api_key_file"])
        except Exception:
            pass
            
        print(f"API密钥文件已从备份恢复: {backup_path}")
        return True
        
    except Exception as e:
        print(f"恢复API密钥文件时出错: {e}")
        return False

# 兼容性检查函数
def check_crypto_compatibility():
    """
    检查加密功能兼容性
    
    Returns:
        dict: 兼容性检查结果
    """
    result = {
        "crypto_available": HAS_CRYPTO,
        "can_encrypt": False,
        "can_decrypt": False,
        "error_message": None
    }
    
    if not HAS_CRYPTO:
        result["error_message"] = "cryptography库未安装"
        return result
        
    try:
        # 测试加密解密功能
        test_data = "test_api_key_sk-1234567890"
        encrypted = encrypt_api_key(test_data)
        
        if encrypted is not None:
            result["can_encrypt"] = True
            
            decrypted = decrypt_api_key(encrypted)
            if decrypted == test_data:
                result["can_decrypt"] = True
            else:
                result["error_message"] = "解密测试失败"
        else:
            result["error_message"] = "加密测试失败"
            
    except Exception as e:
        result["error_message"] = f"兼容性测试异常: {e}"
        
    return result

# 模块初始化时的自检
def _self_check():
    """模块自检"""
    try:
        compat = check_crypto_compatibility()
        if not compat["crypto_available"]:
            print("警告: 加密功能不可用，API密钥将以明文存储")
        elif not (compat["can_encrypt"] and compat["can_decrypt"]):
            print(f"警告: 加密功能异常 - {compat.get('error_message', '未知错误')}")
    except Exception:
        pass  # 自检失败不影响模块加载

# 执行自检
_self_check()