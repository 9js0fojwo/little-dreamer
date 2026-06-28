"""
AI 引擎 — DeepSeek 解析描述 + 通义万相生成图片
"""

import json
import re
import time
import uuid
from pathlib import Path
from typing import Optional

import requests
from openai import OpenAI

from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DASHSCOPE_API_KEY,
    IMAGE_CACHE_DIR,
)

# DeepSeek 客户端（懒加载，缺 Key 也能正常 import）
_ds_client = None


def _get_ds_client():
    global _ds_client
    if _ds_client is None:
        _ds_client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )
    return _ds_client

# 图片缓存目录
image_dir = Path(IMAGE_CACHE_DIR)
image_dir.mkdir(parents=True, exist_ok=True)


# DeepSeek 系统提示词
SYSTEM_PROMPT = """你是一个儿童想象力助手，帮 5-12 岁的孩子把天马行空的想法变成结构化的角色/场景数据。

孩子的描述可能很简单（"一个会飞的猫"），也可能很丰富。你需要：

1. 理解孩子的意图：是创建一个**角色**（人物/动物/生物）、**建筑**（城堡/学校/医院）、**场景**（天气/地形），还是**物品**（魔法棒/宝石）？
2. 给孩子想象中的事物取一个好听的中文名字（2-4 字）
3. 用生动有趣的语言描述外表（让孩子读了会开心）
4. 列出能力/特点（2-4 个）
5. 写一句简短的背景故事（20 字以内，像童话）
6. 生成一个适合 AI 画图的场景描述（儿童绘本风格，可爱Q版，彩色）

**必须严格输出以下 JSON 格式（不要输出其他内容）：**

{
  "type": "character",
  "name": "星儿",
  "appearance": "一个穿着粉色蓬蓬裙的小仙女，有一对闪闪发光的透明翅膀，头发是彩虹色的",
  "abilities": ["飞行", "彩虹魔法", "让花朵盛开"],
  "scene_desc": "儿童绘本风格，可爱Q版小仙女，粉色蓬蓬裙，透明翅膀，彩虹色头发，站在云朵上，温馨梦幻",
  "story": "星儿是彩虹王国的守护小仙女，每天都在云朵上跳舞"
}

type 可选值：character（角色）、building（建筑）、creature（生物）、scene（场景）、item（物品）
"""


def parse_description(user_input: str) -> dict:
    """
    调用 DeepSeek 解析孩子的描述，返回结构化实体数据
    """
    try:
        resp = _get_ds_client().chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            temperature=0.9,
            max_tokens=1000,
        )
        content = resp.choices[0].message.content.strip()

        # 提取 JSON（可能包裹在 ```json ``` 里）
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            entity = json.loads(json_match.group())
            return entity
        else:
            return {"error": "AI 未能解析", "raw": content[:200]}

    except Exception as e:
        return {"error": f"AI 解析失败: {str(e)}"}


def generate_image(scene_desc: str, style: str = "children_book") -> Optional[str]:
    """
    调用通义万相生成图片，返回本地图片路径
    使用最新 wan2.6-t2i 模型，每天免费 50 次
    """
    try:
        full_prompt = f"儿童绘本风格，可爱Q版卡通，色彩明亮温馨柔和，{scene_desc}"

        # 通义万相最新 API（2026）
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        headers = {
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "model": "wan2.2-t2i-flash",  # 免费额度：每天 50 次
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": full_prompt}],
                    }
                ]
            },
            "parameters": {
                "size": "1024*1024",
                "n": 1,
                "watermark": False,
                "prompt_extend": True,
            },
        }

        # 同步调用
        resp = requests.post(url, headers=headers, json=body, timeout=60)
        if resp.status_code != 200:
            return None

        result = resp.json()
        # 提取图片 URL
        output = result.get("output", {})
        choices = output.get("choices", [])
        if not choices:
            return None

        img_url = choices[0].get("message", {}).get("content", [])
        if isinstance(img_url, list):
            img_url = img_url[0].get("image", "") if img_url else ""
        if not img_url:
            return None

        # 下载图片到本地
        img_data = requests.get(img_url, timeout=30).content
        img_id = uuid.uuid4().hex[:8]
        img_path = image_dir / f"dreamer_{img_id}.png"
        with open(img_path, "wb") as f:
            f.write(img_data)
        return str(img_path)

    except Exception:
        return None


def create_entity(user_input: str, generate_img: bool = True) -> dict:
    """
    一站式：描述 → 解析 + 生图 → 返回实体
    """
    # 1. AI 解析
    entity = parse_description(user_input)

    if "error" in entity:
        return entity

    # 2. 生成图片
    entity["image_path"] = None
    if generate_img and "scene_desc" in entity:
        img_path = generate_image(entity["scene_desc"])
        if img_path:
            entity["image_path"] = img_path

    # 3. 记录原始输入
    entity["created_by"] = user_input

    return entity
