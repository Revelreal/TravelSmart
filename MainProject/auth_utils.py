# auth_utils.py
import os
import toml
import jwt
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional


# ====== 配置加载 ======
def load_config(filename="../config.toml"):
    abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
    config = toml.load(abs_path)
    return config["session"]


_cfg = load_config()
SECRET_KEY = _cfg["SECRET_KEY"]
ALGORITHM = _cfg.get("ALGORITHM", "HS256")
TOKEN_EXPIRE_MINUTES = int(_cfg.get("TOKEN_EXPIRE_MINUTES", 60))


# ====== 生成JWT token（只用用户名、角色、exp） ======
def create_token(username: str, role: str, duration_min: int = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=duration_min if duration_min is not None else TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "username": username,
        "role": role.lower(),
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ====== 校验token并解码 ======
def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    校验jwt合法性并返回claims
    返回:
        {
            "username": ...,
            "role": ...,
            "exp": ...
        }
        无效或过期时返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("username") or not payload.get("role"):
            return None
        return {
            "username": payload["username"],
            "role": payload["role"],
            "exp": payload["exp"]
        }
    except jwt.ExpiredSignatureError:
        return None
    except jwt.PyJWTError:
        return None


# ====== token 拼接查询工具 ======
def token_querystr(token: str) -> str:
    if not token:
        return ""
    from urllib.parse import quote
    return f"?token={quote(token)}"
