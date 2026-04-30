"""
记忆管理工具

提供用户偏好记忆的保存和检索功能
"""

import sqlite3
import json
from typing import List, Optional


def save_memory(
    user_id: str,
    category: str,
    keywords: List[str],
    weight: float = 1.0,
    db_path: str = "database/mempoi.sqlite"
) -> dict:
    """
    保存用户记忆

    Args:
        user_id: 用户ID
        category: POI类别 (cafe/restaurant/attraction)
        keywords: 关键词列表
        weight: 权重 (0.0-1.0)
        db_path: 数据库路径

    Returns:
        {
            "success": bool,
            "memory_id": int
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO memories (user_id, category, keywords, weight)
        VALUES (?, ?, ?, ?)
    """, (user_id, category, json.dumps(keywords, ensure_ascii=False), weight))

    memory_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "success": True,
        "memory_id": memory_id
    }


def retrieve_memory(
    user_id: str,
    category: Optional[str] = None,
    db_path: str = "database/mempoi.sqlite"
) -> dict:
    """
    检索用户记忆

    Args:
        user_id: 用户ID
        category: 可选，过滤特定类别
        db_path: 数据库路径

    Returns:
        {
            "memories": [
                {
                    "category": str,
                    "keywords": List[str],
                    "weight": float
                }
            ]
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if category:
        cursor.execute("""
            SELECT category, keywords, weight
            FROM memories
            WHERE user_id = ? AND category = ? AND weight >= 0.1
            ORDER BY weight DESC, created_at DESC
            LIMIT 10
        """, (user_id, category))
    else:
        cursor.execute("""
            SELECT category, keywords, weight
            FROM memories
            WHERE user_id = ? AND weight >= 0.1
            ORDER BY weight DESC, created_at DESC
            LIMIT 10
        """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    memories = []
    for row in rows:
        memories.append({
            "category": row[0],
            "keywords": json.loads(row[1]),
            "weight": row[2]
        })

    return {"memories": memories}


def update_memory_weights(
    user_id: str,
    category: str,
    decay_factor: float = 0.9,
    min_weight: float = 0.1,
    db_path: str = "database/mempoi.sqlite"
) -> dict:
    """
    更新记忆权重（衰减旧记忆）

    Args:
        user_id: 用户ID
        category: POI类别
        decay_factor: 衰减因子
        min_weight: 最小权重阈值
        db_path: 数据库路径

    Returns:
        {
            "updated_count": int,
            "deleted_count": int
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 衰减权重
    cursor.execute("""
        UPDATE memories
        SET weight = weight * ?
        WHERE user_id = ? AND category = ?
    """, (decay_factor, user_id, category))

    updated_count = cursor.rowcount

    # 删除低权重记忆
    cursor.execute("""
        DELETE FROM memories
        WHERE user_id = ? AND weight < ?
    """, (user_id, min_weight))

    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    return {
        "updated_count": updated_count,
        "deleted_count": deleted_count
    }


def retrieve_user_preference_memory(
    user_id: str,
    intent: dict,
    db_path: str = "database/mempoi.sqlite"
) -> dict:
    """
    根据用户ID和当前意图检索偏好记忆

    Args:
        user_id: 用户ID
        intent: 当前意图，必须包含 poi_type 字段
        db_path: 数据库路径

    Returns:
        {
            "stable_preferences": List[dict],
            "recent_preferences": List[dict],
            "negative_preferences": List[dict],
            "default_memory": bool
        }
    """
    # 校验参数
    if not user_id or not isinstance(user_id, str):
        return {
            "stable_preferences": [],
            "recent_preferences": [],
            "negative_preferences": [],
            "default_memory": True,
            "error": "user_id 必须是非空字符串"
        }

    if not isinstance(intent, dict) or "poi_type" not in intent:
        return {
            "stable_preferences": [],
            "recent_preferences": [],
            "negative_preferences": [],
            "default_memory": True,
            "error": "intent 必须包含 poi_type 字段"
        }

    poi_type = intent.get("poi_type")
    if poi_type not in ["cafe", "restaurant", "attraction"]:
        return {
            "stable_preferences": [],
            "recent_preferences": [],
            "negative_preferences": [],
            "default_memory": True,
            "error": f"无效的 poi_type: {poi_type}"
        }

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查用户是否存在
        cursor.execute("SELECT user_id FROM user_profile WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            conn.close()
            return {
                "stable_preferences": [],
                "recent_preferences": [],
                "negative_preferences": [],
                "default_memory": True,
                "error": f"用户 {user_id} 不存在"
            }

        # 查询稳定偏好 (weight >= 0.7)
        cursor.execute("""
            SELECT keywords, weight, source, created_at
            FROM preference_memory
            WHERE user_id = ? AND category = ? AND weight >= 0.7
            ORDER BY weight DESC, created_at DESC
            LIMIT 10
        """, (user_id, poi_type))

        stable_preferences = []
        for row in cursor.fetchall():
            stable_preferences.append({
                "keywords": json.loads(row[0]),
                "weight": row[1],
                "source": row[2],
                "created_at": row[3]
            })

        # 查询近期偏好 (0.3 <= weight < 0.7)
        cursor.execute("""
            SELECT keywords, weight, source, created_at
            FROM preference_memory
            WHERE user_id = ? AND category = ? AND weight >= 0.3 AND weight < 0.7
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id, poi_type))

        recent_preferences = []
        for row in cursor.fetchall():
            recent_preferences.append({
                "keywords": json.loads(row[0]),
                "weight": row[1],
                "source": row[2],
                "created_at": row[3]
            })

        # 查询负向偏好 (weight < 0.3)
        cursor.execute("""
            SELECT keywords, weight, source, created_at
            FROM preference_memory
            WHERE user_id = ? AND category = ? AND weight < 0.3 AND weight > 0
            ORDER BY weight ASC, created_at DESC
            LIMIT 5
        """, (user_id, poi_type))

        negative_preferences = []
        for row in cursor.fetchall():
            negative_preferences.append({
                "keywords": json.loads(row[0]),
                "weight": row[1],
                "source": row[2],
                "created_at": row[3]
            })

        conn.close()

        # 判断是否为默认记忆（无任何历史偏好）
        has_preferences = (
            len(stable_preferences) > 0 or
            len(recent_preferences) > 0 or
            len(negative_preferences) > 0
        )

        return {
            "stable_preferences": stable_preferences,
            "recent_preferences": recent_preferences,
            "negative_preferences": negative_preferences,
            "default_memory": not has_preferences
        }

    except Exception as e:
        return {
            "stable_preferences": [],
            "recent_preferences": [],
            "negative_preferences": [],
            "default_memory": True,
            "error": f"检索偏好记忆失败: {str(e)}"
        }
