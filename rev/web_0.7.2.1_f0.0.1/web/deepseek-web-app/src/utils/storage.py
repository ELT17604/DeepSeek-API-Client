def save_api_key(api_key):
    """将API密钥保存到文件"""
    try:
        with open("API_KEY", "w") as f:
            f.write(api_key)
        return True
    except Exception as e:
        print(f"保存API密钥时出错: {e}")
        return False

def load_api_key():
    """从文件加载API密钥"""
    try:
        with open("API_KEY", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("API密钥文件未找到。")
        return None
    except Exception as e:
        print(f"加载API密钥时出错: {e}")
        return None

def delete_api_key():
    """删除存储API密钥的文件"""
    try:
        os.remove("API_KEY")
        return True
    except FileNotFoundError:
        print("API密钥文件未找到。")
        return False
    except Exception as e:
        print(f"删除API密钥文件时出错: {e}")
        return False