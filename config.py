# 博客系统配置文件
# Blog System Configuration

from pathlib import Path
from typing import List

# 项目根目录
BASE_DIR = Path(__file__).parent

# 数据库配置
DATABASE_URL = f"sqlite:///{BASE_DIR}/blog.db"

# FastAPI 配置
APP_NAME = "个人博客系统"
APP_VERSION = "1.0.0"
DEBUG = True
SECRET_KEY = "your-secret-key-change-in-production"

# 服务器配置
HOST = "0.0.0.0"
PORT = 8000

# 主题配置
DEFAULT_THEME = "light"
AVAILABLE_THEMES = ["light", "dark", "forest", "ocean", "earth", "twilight", "ink"]

# CSRF 配置
CSRF_SECRET_KEY = "your-secret-key-change-in-production"
CSRF_COOKIE_NAME = "csrftoken"

# 登录安全配置
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_DURATION = 900  # 15分钟（秒）

# 同步服务配置
SYNC_MAX_RETRIES = 3
SYNC_RETRY_DELAY = 30  # 秒
SYNC_LONG_RETRY_DELAY = 300  # 5分钟
SYNC_TIMEOUT = 60  # 秒

# 评论配置
CAPTCHA_SITE_KEY = ""  # Google reCAPTCHA site key
CAPTCHA_SECRET_KEY = ""  # Google reCAPTCHA secret key

# 可用的同步平台
SYNC_PLATFORMS = ["csdn", "wechat"]

# Jinja2 模板配置
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR = BASE_DIR / "app" / "static"

# 静态文件路由
STATIC_URL = "/static"