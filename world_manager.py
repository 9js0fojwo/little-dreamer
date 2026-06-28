"""
世界状态管理器 — 保存/加载/列出世界
"""

import json
import uuid
import time
from pathlib import Path
from typing import Dict, List, Optional

from config import WORLDS_DIR, MAX_ENTITIES_PER_WORLD, MAX_WORLDS


class WorldManager:
    def __init__(self, base_dir: str = WORLDS_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, world_id: str) -> Path:
        return self.base_dir / f"{world_id}.json"

    def create_world(self, name: str) -> dict:
        """创建新世界"""
        # 限制世界数量
        existing = self.list_worlds()
        if len(existing) >= MAX_WORLDS:
            # 删除最旧的世界
            oldest = existing[-1]
            self._path(oldest["world_id"]).unlink(missing_ok=True)

        world = {
            "world_id": uuid.uuid4().hex[:8],
            "name": name,
            "created_at": time.strftime("%Y-%m-%d %H:%M"),
            "updated_at": time.strftime("%Y-%m-%d %H:%M"),
            "entities": [],
        }
        self._save(world)
        return world

    def _save(self, world: dict):
        world["updated_at"] = time.strftime("%Y-%m-%d %H:%M")
        with open(self._path(world["world_id"]), "w", encoding="utf-8") as f:
            json.dump(world, f, ensure_ascii=False, indent=2)

    def load_world(self, world_id: str) -> Optional[dict]:
        """加载世界"""
        path = self._path(world_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_worlds(self) -> List[dict]:
        """列出所有世界（按更新时间倒序）"""
        worlds = []
        for path in sorted(
            self.base_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    w = json.load(f)
                worlds.append({
                    "world_id": w["world_id"],
                    "name": w["name"],
                    "entity_count": len(w.get("entities", [])),
                    "updated_at": w.get("updated_at", ""),
                })
            except Exception:
                continue
        return worlds

    def add_entity(self, world_id: str, entity: dict) -> Optional[dict]:
        """添加实体到世界"""
        world = self.load_world(world_id)
        if not world:
            return None
        if len(world.get("entities", [])) >= MAX_ENTITIES_PER_WORLD:
            return None
        entity["id"] = entity.get("id") or uuid.uuid4().hex[:6]
        entity.setdefault("x", 200 + len(world["entities"]) * 50)
        entity.setdefault("y", 200 + len(world["entities"]) * 30)
        world.setdefault("entities", []).append(entity)
        self._save(world)
        return world

    def update_entity(self, world_id: str, entity_id: str, updates: dict) -> Optional[dict]:
        """更新实体（位置、名称等）"""
        world = self.load_world(world_id)
        if not world:
            return None
        for e in world.get("entities", []):
            if e["id"] == entity_id:
                e.update(updates)
                self._save(world)
                return world
        return None

    def remove_entity(self, world_id: str, entity_id: str) -> Optional[dict]:
        """删除实体"""
        world = self.load_world(world_id)
        if not world:
            return None
        world["entities"] = [e for e in world.get("entities", []) if e["id"] != entity_id]
        self._save(world)
        return world

    def save_full_world(self, world_id: str, data: dict) -> bool:
        """全量保存世界（前端拖拽后批量更新）"""
        world = self.load_world(world_id)
        if not world:
            return False
        world["entities"] = data.get("entities", world["entities"])
        world["name"] = data.get("name", world["name"])
        self._save(world)
        return True
