"""
会话管理工具

提供会话创建和查询功能
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any


def create_session(user_id: str = "default_user", db_path: str = "database/mempoi.sqlite") -> dict:
    """
    创建新会话

    Args:
        user_id: 用户ID
        db_path: 数据库路径

    Returns:
        {
            "session_id": str,
            "user_id": str,
            "created_at": str
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 生成 session_id
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    session_id = f"session_{user_id}_{timestamp}"

    cursor.execute("""
        INSERT INTO sessions (session_id, user_id)
        VALUES (?, ?)
    """, (session_id, user_id))

    conn.commit()

    # 获取创建的会话
    cursor.execute("""
        SELECT session_id, user_id, created_at
        FROM sessions
        WHERE session_id = ?
    """, (session_id,))

    row = cursor.fetchone()
    conn.close()

    return {
        "session_id": row[0],
        "user_id": row[1],
        "created_at": row[2]
    }


def get_session(session_id: str, db_path: str = "database/mempoi.sqlite") -> Optional[dict]:
    """
    获取会话信息

    Args:
        session_id: 会话ID
        db_path: 数据库路径

    Returns:
        {
            "session_id": str,
            "user_id": str,
            "created_at": str,
            "updated_at": str
        } or None
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT session_id, user_id, created_at, updated_at
        FROM session_intent
        WHERE session_id = ?
    """, (session_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "session_id": row[0],
        "user_id": row[1],
        "created_at": row[2],
        "updated_at": row[3]
    }


def parse_and_save_session_intent(
    user_id: str,
    session_id: str,
    raw_query: str,
    parsed_intent: Dict[str, Any],
    db_path: str = "database/mempoi.sqlite"
) -> dict:
    """
    解析并保存会话意图

    Args:
        user_id: 用户ID
        session_id: 会话ID
        raw_query: 原始查询文本
        parsed_intent: 解析后的意图，必须包含:
            - poi_type: POI类型 (cafe/restaurant/attraction)
            - location: 位置信息
            - scenario: 使用场景
            - constraints: 约束条件
        db_path: 数据库路径

    Returns:
        成功: {
            "success": True,
            "session_id": str,
            "intent": dict
        }
        失败: {
            "success": False,
            "error": str
        }
    """
    # 1. 校验必填参数
    if not user_id or not isinstance(user_id, str):
        return {
            "success": False,
            "error": "user_id 必须是非空字符串"
        }

    if not session_id or not isinstance(session_id, str):
        return {
            "success": False,
            "error": "session_id 必须是非空字符串"
        }

    if not raw_query or not isinstance(raw_query, str):
        return {
            "success": False,
            "error": "raw_query 必须是非空字符串"
        }

    # 2. 校验 parsed_intent 结构
    if not isinstance(parsed_intent, dict):
        return {
            "success": False,
            "error": "parsed_intent 必须是字典类型"
        }

    required_fields = ["poi_type", "location", "scenario", "constraints"]
    missing_fields = [field for field in required_fields if field not in parsed_intent]

    if missing_fields:
        return {
            "success": False,
            "error": f"parsed_intent 缺少必填字段: {', '.join(missing_fields)}"
        }

    # 3. 校验 poi_type 值
    valid_poi_types = ["cafe", "restaurant", "attraction"]
    poi_type = parsed_intent.get("poi_type")

    if poi_type not in valid_poi_types:
        return {
            "success": False,
            "error": f"poi_type 必须是以下值之一: {', '.join(valid_poi_types)}"
        }

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 4. 检查 user_id 是否存在
        cursor.execute("SELECT user_id FROM user_profile WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            conn.close()
            return {
                "success": False,
                "error": f"用户 {user_id} 不存在"
            }

        # 5. 提取约束条件
        constraints = parsed_intent.get("constraints", {})
        max_distance_km = constraints.get("max_distance_km")
        price_level = constraints.get("price_level")

        # 6. 写入 session_intent 表
        cursor.execute("""
            INSERT INTO session_intent (
                session_id,
                user_id,
                intent_category,
                intent_keywords,
                max_distance_km,
                price_level,
                raw_input
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            user_id,
            poi_type,
            json.dumps(parsed_intent, ensure_ascii=False),
            max_distance_km,
            price_level,
            raw_query
        ))

        conn.commit()
        conn.close()

        # 7. 返回结构化结果
        return {
            "success": True,
            "session_id": session_id,
            "intent": {
                "poi_type": poi_type,
                "location": parsed_intent.get("location"),
                "scenario": parsed_intent.get("scenario"),
                "constraints": constraints,
                "raw_query": raw_query
            }
        }

    except sqlite3.IntegrityError as e:
        return {
            "success": False,
            "error": f"数据库完整性错误: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"保存会话意图失败: {str(e)}"
        }
