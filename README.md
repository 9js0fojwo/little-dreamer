# 🌟 会飞的城堡

AI 驱动的虚拟世界构建器，面向 5-12 岁儿童。

**描述即创造**——孩子说"我是一个有翅膀的公主，住在云上"，AI 就生成角色、图片、故事，放在可拖拽的画布上。

## MVP

- 单人模式，一个孩子一个世界
- 文字描述 → AI 生成角色卡 + 图片
- Canvas 画布拖拽排列
- 保存/加载世界

## 快速开始

```bash
pip install -r requirements.txt

# 配置 API Key
export DEEPSEEK_API_KEY="你的DeepSeek Key"
export DASHSCOPE_API_KEY="你的通义万相 Key"

python app.py
# 打开 http://127.0.0.1:8080
```

## API 用量

| API | 用途 | 费用 |
|-----|------|------|
| DeepSeek | 解析孩子描述 → 结构化数据 | ~¥0.001/次 |
| 通义万相 | 生成角色图片 | ~¥0.1-0.3/张 |

## 后续计划

- 多人共建世界
- NPC AI 对话
- 动态世界生长
