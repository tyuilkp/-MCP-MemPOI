"""
反馈处理工具

提供用户反馈保存和偏好更新功能
"""

import sqlite3
import json
from typing import Optional, List, Dict
from datetime import datetime


def save_feedback(
    user_id: str,
    session_id: str,
    poi_id: int,
    rating: int,
    feedback_text: Optional[str] = None,
    db_path: str = "database/mempoi.sqlite"
) -> dict:
    """
    保存用户反馈

    Args:
        user_id: 用户ID
        session_id: 会话ID
        poi_id: POI ID
        rating: 评分 (1-5)
        feedback_text: 可选，反馈文本
        db_path: 数据库路径

    Returns:
        {
            "success": bool,
            "feedback_id": int,
            "memory_updated": bool
        }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 保存反馈
    cursor.execute("""
        INSERT INTO feedback (user_id, session_id, poi_id, rating, feedback_text)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, session_id, poi_id, rating, feedback_text))

    feedback_id = cursor.lastrowid

    # 如果评分 >= 4，更新记忆
    memory_updated = False
    if rating >= 4:
        # 获取 POI 信息
        cursor.execute("""
            SELECT category, tags FROM pois WHERE id = ?
        """, (poi_id,))

        row = cursor.fetchone()
        if row:
            category = row[0]
            tags = json.loads(row[1])

            # 衰减旧记忆
            cursor.execute("""
                UPDATE memories
                SET weight = weight * 0.9
                WHERE user_id = ? AND category = ?
            """, (user_id, category))

            # 添加新记忆
            cursor.execute("""
                INSERT INTO memories (user_id, category, keywords, weight)
                VALUES (?, ?, ?, 1.0)
            """, (user_id, category, json.dumps(tags, ensure_ascii=False)))

            # 删除低权重记忆
            cursor.execute("""
                DELETE FROM memories
                WHERE user_id = ? AND weight < 0.1
            """, (user_id,))

            memory_updated = True

    conn.commit()
    conn.close()

    return {
        "success": True,
        "feedback_id": feedback_id,
        "memory_updated": memory_updated
    }


def save_recommendation_log(
    session_id: str,
    user_id: str,
    ranked_results: List[Dict],
    db_path: str = "database/mempoi.sqlite"
) -> dict:
    """
    保存推荐日志

    Args:
        session_id: 会话ID
        user_id: 用户ID
        ranked_results: 排序后的推荐结果列表，每项包含:
            - poi: POI 信息
            - total_score: 总分
            - score_breakdown: 分项分数
            - matched_preferences: 匹配的偏好
        db_path: 数据库路径

    Returns:
        {
            "success": bool,
            "saved_count": int
        }
    """
    if not isinstance(ranked_results, list):
        return {
            "success": False,
            "saved_count": 0,
            "error": "ranked_results 必须是列表类型"
        }

    if not ranked_results:
        return {
            "success": True,
            "saved_count": 0
        }

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        saved_count = 0
        for rank_position, result in enumerate(ranked_results, 1):
            poi = result.get("poi", {})
            poi_id = poi.get("id")

            if not poi_id:
                continue

            score_breakdown = result.get("score_breakdown", {})
            matched_prefs = result.get("matched_preferences", {})

            # 生成解释文本
            explanation_parts = [
                f"排名第 {rank_position}",
                f"总分 {result.get('total_score', 0):.2f}"
            ]

            if matched_prefs.get("stable"):
                explanation_parts.append(f"匹配稳定偏好: {', '.join(matched_prefs['stable'])}")
            if matched_prefs.get("recent"):
                explanation_parts.append(f"匹配近期偏好: {', '.join(matched_prefs['recent'])}")

            explanation = " | ".join(explanation_parts)

            # 保存到 recommendation_log 表
            cursor.execute("""
                INSERT INTO recommendation_log (
                    session_id, user_id, poi_id, rank_position, score,
                    rating_score, distance_score, preference_score,
                    matched_keywords, explanation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                user_id,
                poi_id,
                rank_position,
                result.get("total_score", 0),
                score_breakdown.get("rating_score", 0),
                score_breakdown.get("distance_score", 0),
                score_breakdown.get("stable_preference_score", 0) + score_breakdown.get("recent_preference_score", 0),
                json.dumps(matched_prefs.get("stable", []) + matched_prefs.get("recent", []), ensure_ascii=False),
                explanation
            ))

            saved_count += 1

        conn.commit()
        conn.close()

        return {
            "success": True,
            "saved_count": saved_count
        }

    except Exception as e:
        return {
            "success": False,
            "saved_count": 0,
            "error": f"保存推荐日志失败: {str(e)}"
        }


def update_preference_from_feedback(
    user_id: str,
    poi_id: int,
    feedback_type: str,
    feedback_details: Optional[Dict] = None,
    db_path: str = "database/mempoi.sqlite"
) -> dict:
    """
    根据反馈更新用户偏好记忆

    Args:
        user_id: 用户ID
        poi_id: POI ID
        feedback_type: 反馈类型 (positive/negative/correction)
        feedback_details: 可选，反馈详情，可包含:
            - corrected_tags: 修正后的标签（用于 correction 类型）
            - reason: 反馈原因
        db_path: 数据库路径

    Returns:
        {
            "success": bool,
            "updated_preferences": List[dict],
            "evidence": str,
            "timestamp": str
        }
    """
    # 校验参数
    if feedback_type not in ["positive", "negative", "correction"]:
        return {
            "success": False,
            "updated_preferences": [],
            "error": f"无效的 feedback_type: {feedback_type}，必须是 positive/negative/correction"
        }

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 获取 POI 信息
        cursor.execute("""
            SELECT category, tags, name FROM poi_info WHERE id = ?
        """, (poi_id,))

        poi_row = cursor.fetchone()
        if not poi_row:
            conn.close()
            return {
                "success": False,
                "updated_preferences": [],
                "error": f"POI {poi_id} 不存在"
            }

        category = poi_row[0]
        poi_tags = json.loads(poi_row[1])
        poi_name = poi_row[2]

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_preferences = []

        # 根据反馈类型处理
        if feedback_type == "positive":
            # 正向反馈：提升相关标签的权重
            evidence = f"用户对 {poi_name} 给予正向反馈"
            source = "positive_feedback"

            for tag in poi_tags:
                # 检查是否已存在该偏好
                cursor.execute("""
                    SELECT id, weight FROM preference_memory
                    WHERE user_id = ? AND category = ? AND keywords = ?
                """, (user_id, category, json.dumps([tag], ensure_ascii=False)))

                existing = cursor.fetchone()

                if existing:
                    # 更新现有偏好权重（增加 0.1，最大 1.0）
                    new_weight = min(existing[1] + 0.1, 1.0)
                    cursor.execute("""
                        UPDATE preference_memory
                        SET weight = ?, source = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (new_weight, source, existing[0]))

                    updated_preferences.append({
                        "tag": tag,
                        "action": "increased",
                        "old_weight": existing[1],
                        "new_weight": new_weight
                    })
                else:
                    # 创建新偏好
                    cursor.execute("""
                        INSERT INTO preference_memory (user_id, category, keywords, weight, source)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, category, json.dumps([tag], ensure_ascii=False), 0.7, source))

                    updated_preferences.append({
                        "tag": tag,
                        "action": "created",
                        "new_weight": 0.7
                    })

        elif feedback_type == "negative":
            # 负向反馈：降低相关标签的权重
            evidence = f"用户对 {poi_name} 给予负向反馈"
            source = "negative_feedback"

            for tag in poi_tags:
                cursor.execute("""
                    SELECT id, weight FROM preference_memory
                    WHERE user_id = ? AND category = ? AND keywords = ?
                """, (user_id, category, json.dumps([tag], ensure_ascii=False)))

                existing = cursor.fetchone()

                if existing:
                    # 降低权重（减少 0.2，最小 0.1）
                    new_weight = max(existing[1] - 0.2, 0.1)
                    cursor.execute("""
                        UPDATE preference_memory
                        SET weight = ?, source = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (new_weight, source, existing[0]))

                    updated_preferences.append({
                        "tag": tag,
                        "action": "decreased",
                        "old_weight": existing[1],
                        "new_weight": new_weight
                    })
                else:
                    # 创建负向偏好
                    cursor.execute("""
                        INSERT INTO preference_memory (user_id, category, keywords, weight, source)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, category, json.dumps([tag], ensure_ascii=False), 0.2, source))

                    updated_preferences.append({
                        "tag": tag,
                        "action": "created_negative",
                        "new_weight": 0.2
                    })

        elif feedback_type == "correction":
            # 修正反馈：根据用户提供的修正标签更新偏好
            corrected_tags = feedback_details.get("corrected_tags", []) if feedback_details else []

            if not corrected_tags:
                conn.close()
                return {
                    "success": False,
                    "updated_preferences": [],
                    "error": "correction 类型需要提供 corrected_tags"
                }

            evidence = f"用户对 {poi_name} 提供修正标签: {', '.join(corrected_tags)}"
            source = "correction_feedback"

            # 降低原标签权重
            for tag in poi_tags:
                cursor.execute("""
                    SELECT id, weight FROM preference_memory
                    WHERE user_id = ? AND category = ? AND keywords = ?
                """, (user_id, category, json.dumps([tag], ensure_ascii=False)))

                existing = cursor.fetchone()
                if existing:
                    new_weight = max(existing[1] - 0.15, 0.1)
                    cursor.execute("""
                        UPDATE preference_memory
                        SET weight = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (new_weight, existing[0]))

            # 提升修正标签权重
            for tag in corrected_tags:
                cursor.execute("""
                    SELECT id, weight FROM preference_memory
                    WHERE user_id = ? AND category = ? AND keywords = ?
                """, (user_id, category, json.dumps([tag], ensure_ascii=False)))

                existing = cursor.fetchone()

                if existing:
                    new_weight = min(existing[1] + 0.15, 1.0)
                    cursor.execute("""
                        UPDATE preference_memory
                        SET weight = ?, source = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (new_weight, source, existing[0]))

                    updated_preferences.append({
                        "tag": tag,
                        "action": "corrected_increased",
                        "old_weight": existing[1],
                        "new_weight": new_weight
                    })
                else:
                    cursor.execute("""
                        INSERT INTO preference_memory (user_id, category, keywords, weight, source)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, category, json.dumps([tag], ensure_ascii=False), 0.75, source))

                    updated_preferences.append({
                        "tag": tag,
                        "action": "corrected_created",
                        "new_weight": 0.75
                    })

        conn.commit()
        conn.close()

        return {
            "success": True,
            "updated_preferences": updated_preferences,
            "evidence": evidence,
            "source": source,
            "timestamp": timestamp
        }

    except Exception as e:
        return {
            "success": False,
            "updated_preferences": [],
            "error": f"更新偏好失败: {str(e)}"
        }
