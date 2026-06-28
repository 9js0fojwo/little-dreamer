"""
配置文件 — 从环境变量读取 API Key
"""

import os

# DeepSeek API
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 通义万相 API（阿里云 DashScope）
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")

# 应用配置
MAX_ENTITIES_PER_WORLD = 50
MAX_WORLDS = 10
IMAGE_CACHE_DIR = "images"
WORLDS_DIR = "worlds"
