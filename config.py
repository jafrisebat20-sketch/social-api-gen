import json
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
CONFIG_PATH = Path(__file__).parent / "config.json"
_DEFAULTS = {"developer_name": "Ryuu", "developer_handle": "ryuuwaguri", "app_name": "Ryuu Social API", "base_url": "https://api.ryuuwaguri.com", "contact_email": "jafrisebat20@gmail.com", "developer_tiktok": "https://tiktok.com/@ryuu.ndivision"}
_config_cache = None
def load_config():
    global _config_cache
    if _config_cache is not None: return _config_cache
    cfg = dict(_DEFAULTS)
    env_map = {"DEV_NAME": "developer_name", "DEV_HANDLE": "developer_handle", "APP_NAME": "app_name", "BASE_URL": "base_url", "CONTACT_EMAIL": "contact_email", "DEV_TIKTOK": "developer_tiktok"}
    for env_key, cfg_key in env_map.items():
        val = os.getenv(env_key)
        if val: cfg[cfg_key] = val
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                file_cfg = json.load(f)
                cfg.update({k: v for k, v in file_cfg.items() if v})
        except: pass
    _config_cache = cfg
    return cfg
def get_public_url(): return load_config()["base_url"].rstrip("/")
