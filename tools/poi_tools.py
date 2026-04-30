"""
POI 搜索工具

提供意图解析和 POI 搜索功能
"""

import sqlite3
import json
import re
from typing import List, Optional


def parse_intent(user_input: str) -> dict:
    """
    解析用户意图

    Args:
        user_input: 用户自然语言输入

    Returns:
        {
            "category": str,
            "max_distance_km": float,
            "price_level": Optional[int],
            "keywords": List[str]
        }
    """
    user_input_lower = user_input.lower()

    # 识别类别
    category_keywords = {
        "cafe": ["咖啡", "咖啡馆", "咖啡厅", "cafe", "coffee"],
        "restaurant": ["餐厅", "饭店", "餐馆", "restaurant", "吃饭", "美食"],
        "attraction": ["景点", "公园", "博物馆", "attraction", "旅游", "游玩"]
    }

    category = None
    for cat, keywords in category_keywords.items():
        if any(kw in user_input_lower for kw in keywords):
            category = cat
            break

    if not category:
        raise ValueError("无法识别POI类别，请在输入中包含：咖啡/餐厅/景点")

    # 提取距离
    distance_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:公里|km|千米)', user_input_lower)
    max_distance_km = float(distance_match.group(1)) if distance_match else 5.0

    # 识别价格等级
    price_keywords = {
        "cheap": ["便宜", "实惠", "平价", "经济"],
        "expensive": ["高档", "贵", "奢华", "豪华"]
    }

    price_level = None
    if any(kw in user_input_lower for kw in price_keywords["cheap"]):
        price_level = 2
    elif any(kw in user_input_lower for kw in price_keywords["expensive"]):
        price_level = 4

    # 提取关键词
    attribute_keywords = [
        "安静", "独立", "连锁", "有wifi", "辣", "清淡",
        "室内", "室外", "免费", "收费", "历史", "艺术"
    ]

    keywords = [kw for kw in attribute_keywords if kw in user_input]

    return {
        "category": category,
        "max_distance_km": max_distance_km,
        "price_level": price_level,
        "keywords": keywords
    }


def search_pois(
    category: str,
    max_distance_km: float,
    price_level: Optional[int] = None,
    limit: int = 20,
    db_path: str = "database/mempoi.sqlite"
) -> dict:
    """
    搜索 POI

    Args:
        category: POI类别
        max_distance_km: 最大距离
        price_level: 可选，价格等级
        limit: 返回数量限制
        db_path: 数据库路径

    Returns:
        {
            "pois": [
                {
                    "id": int,
                    "name": str,
                    "category": str,
                    "distance_km": float,
                    "rating": float,
                    "price_level": Optional[int],
                    "tags": List[str]
                }
            ]
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if price_level:
        cursor.execute("""
            SELECT id, name, category, distance_km, rating, price_level, tags
            FROM pois
            WHERE category = ? AND distance_km <= ? AND price_level = ?
            ORDER BY distance_km ASC
            LIMIT ?
        """, (category, max_distance_km, price_level, limit))
    else:
        cursor.execute("""
            SELECT id, name, category, distance_km, rating, price_level, tags
            FROM pois
            WHERE category = ? AND distance_km <= ?
            ORDER BY distance_km ASC
            LIMIT ?
        """, (category, max_distance_km, limit))

    rows = cursor.fetchall()
    conn.close()

    pois = []
    for row in rows:
        pois.append({
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "distance_km": row[3],
            "rating": row[4],
            "price_level": row[5],
            "tags": json.loads(row[6])
        })

    return {"pois": pois}


def retrieve_candidate_pois(
    location: dict,
    poi_type: str,
    constraints: dict,
    top_k: int = 20,
    db_path: str = "database/mempoi.sqlite"
) -> dict:
    """
    根据位置、类型和约束条件检索候选 POI

    Args:
        location: 位置信息，包含 latitude 和 longitude
        poi_type: POI类型 (cafe/restaurant/attraction)
        constraints: 约束条件，可包含:
            - max_distance_km: 最大距离
            - price_level: 价格等级
            - tags: 标签列表（用于过滤）
        top_k: 返回数量限制
        db_path: 数据库路径

    Returns:
        成功: {
            "candidates": List[dict],
            "total_count": int,
            "empty_result": bool
        }
        失败: {
            "candidates": [],
            "total_count": 0,
            "empty_result": True,
            "error": str
        }
    """
    # 1. 校验参数
    if not isinstance(location, dict) or "latitude" not in location or "longitude" not in location:
        return {
            "candidates": [],
            "total_count": 0,
            "empty_result": True,
            "error": "location 必须包含 latitude 和 longitude"
        }

    if poi_type not in ["cafe", "restaurant", "attraction"]:
        return {
            "candidates": [],
            "total_count": 0,
            "empty_result": True,
            "error": f"无效的 poi_type: {poi_type}"
        }

    if not isinstance(constraints, dict):
        return {
            "candidates": [],
            "total_count": 0,
            "empty_result": True,
            "error": "constraints 必须是字典类型"
        }

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 2. 构建查询条件
        max_distance_km = constraints.get("max_distance_km", 10.0)
        price_level = constraints.get("price_level")
        required_tags = constraints.get("tags", [])

        # 3. 基础查询
        query = """
            SELECT id, name, category, latitude, longitude, distance_km,
                   rating, price_level, tags, address, description
            FROM poi_info
            WHERE category = ? AND distance_km <= ?
        """
        params = [poi_type, max_distance_km]

        # 4. 添加价格等级过滤
        if price_level is not None:
            query += " AND price_level = ?"
            params.append(price_level)

        # 5. 排序和限制
        query += " ORDER BY distance_km ASC, rating DESC LIMIT ?"
        params.append(top_k)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # 6. 处理结果
        candidates = []
        for row in rows:
            poi_tags = json.loads(row[8])

            # 7. 标签匹配过滤
            if required_tags:
                # 检查是否包含所有必需标签
                if not all(tag in poi_tags for tag in required_tags):
                    continue

            candidates.append({
                "id": row[0],
                "name": row[1],
                "category": row[2],
                "latitude": row[3],
                "longitude": row[4],
                "distance_km": row[5],
                "rating": row[6],
                "price_level": row[7],
                "tags": poi_tags,
                "address": row[9],
                "description": row[10]
            })

        conn.close()

        # 8. 返回结果
        return {
            "candidates": candidates,
            "total_count": len(candidates),
            "empty_result": len(candidates) == 0
        }

    except Exception as e:
        return {
            "candidates": [],
            "total_count": 0,
            "empty_result": True,
            "error": f"检索候选 POI 失败: {str(e)}"
        }
