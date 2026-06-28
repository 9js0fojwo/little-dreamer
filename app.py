"""
小小梦想家 — Flask 后端
儿童 AI 虚拟世界构建器
"""

import os
import sys
from pathlib import Path

from flask import Flask, request, jsonify, render_template, send_from_directory

from world_manager import WorldManager
from ai_engine import create_entity

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

# 初始化
wm = WorldManager()

# 静态文件服务
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

@app.route("/images/<path:filename>")
def image_files(filename):
    return send_from_directory("images", filename)


# ==================== 页面 ====================

@app.route("/")
def index():
    return render_template("index.html")


# ==================== AI 创建 ====================

@app.route("/api/create", methods=["POST"])
def api_create():
    """孩子输入描述 → AI 生成实体"""
    data = request.get_json(silent=True) or {}
    user_input = data.get("description", "").strip()
    world_id = data.get("world_id", "").strip()

    if not user_input:
        return jsonify({"error": "说说你想创造什么吧~"}), 400
    if len(user_input) > 500:
        return jsonify({"error": "描述太长啦，简短一点就好~"}), 400

    # 确保有世界
    if not world_id:
        world = wm.create_world("我的梦想世界")
        world_id = world["world_id"]
    elif not wm.load_world(world_id):
        world = wm.create_world("我的梦想世界")
        world_id = world["world_id"]

    # AI 创建
    entity = create_entity(user_input, generate_img=True)

    if "error" in entity:
        return jsonify({"error": entity["error"]}), 500

    # 添加到世界
    wm.add_entity(world_id, entity)

    return jsonify({
        "world_id": world_id,
        "entity": entity,
    })


# ==================== 世界管理 ====================

@app.route("/api/worlds", methods=["GET"])
def api_list_worlds():
    """列出所有世界"""
    return jsonify({"worlds": wm.list_worlds()})


@app.route("/api/world/<world_id>", methods=["GET"])
def api_load_world(world_id):
    """加载世界"""
    world = wm.load_world(world_id)
    if not world:
        return jsonify({"error": "世界不见了..."}), 404
    return jsonify(world)


@app.route("/api/world/<world_id>", methods=["DELETE"])
def api_delete_world(world_id):
    """删除世界"""
    path = wm._path(world_id)
    if path.exists():
        path.unlink()
    return jsonify({"ok": True})


@app.route("/api/world/save", methods=["POST"])
def api_save_world():
    """保存世界（全量，拖拽后用）"""
    data = request.get_json(silent=True) or {}
    world_id = data.get("world_id", "")
    if not wm.save_full_world(world_id, data):
        return jsonify({"error": "保存失败"}), 400
    return jsonify({"ok": True})


@app.route("/api/world/new", methods=["POST"])
def api_new_world():
    """新建世界"""
    data = request.get_json(silent=True) or {}
    name = data.get("name", "我的梦想世界")
    world = wm.create_world(name)
    return jsonify(world)


# ==================== 实体操作 ====================

@app.route("/api/entity/move", methods=["POST"])
def api_move_entity():
    """移动实体"""
    data = request.get_json(silent=True) or {}
    world_id = data.get("world_id")
    entity_id = data.get("entity_id")
    x = data.get("x")
    y = data.get("y")
    if not all([world_id, entity_id, x is not None, y is not None]):
        return jsonify({"error": "参数不完整"}), 400
    wm.update_entity(world_id, entity_id, {"x": x, "y": y})
    return jsonify({"ok": True})


@app.route("/api/entity/<world_id>/<entity_id>", methods=["DELETE"])
def api_delete_entity(world_id, entity_id):
    """删除实体"""
    wm.remove_entity(world_id, entity_id)
    return jsonify({"ok": True})


# ==================== 启动 ====================

if __name__ == "__main__":
    port = 8080
    print(f"\n{'='*50}")
    print(f"  🌟 小小梦想家 v1.0 MVP")
    print(f"  打开浏览器: http://127.0.0.1:{port}")
    print(f"{'='*50}\n")
    app.run(host="127.0.0.1", port=port, debug=True)
