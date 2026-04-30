"""
排序推荐工具

提供 POI 排序和推荐理由生成功能
"""

from typing import List, Dict, Optional


def calculate_score(
    poi: dict,
    memories: List[dict],
    rating_weight: float = 0.4,
    distance_weight: float = 0.3,
    preference_weight: float = 0.3
) -> dict:
    """
    计算 POI 评分

    Args:
        poi: POI 对象
        memories: 用户记忆列表
        rating_weight: 评分权重
        distance_weight: 距离权重
        preference_weight: 偏好权重

    Returns:
        {
            "score": float,
            "rating_score": float,
            "distance_score": float,
            "preference_score": float,
            "matched_keywords": List[str]
        }
    """
    # 评分归一化
    rating_score = poi["rating"] / 5.0

    # 距离归一化
    distance_score = 1 / (1 + poi["distance_km"])

    # 偏好匹配
    preference_score = 0.0
    matched_keywords = []

    if memories:
        all_keywords = []
        for memory in memories:
            all_keywords.extend(memory["keywords"])

        unique_keywords = list(set(all_keywords))

        if unique_keywords:
            for keyword in unique_keywords:
                if keyword in poi["tags"]:
                    matched_keywords.append(keyword)

            preference_score = len(matched_keywords) / len(unique_keywords)

    # 综合评分
    final_score = (
        rating_weight * rating_score +
        distance_weight * distance_score +
        preference_weight * preference_score
    )

    return {
        "score": final_score,
        "rating_score": rating_score,
        "distance_score": distance_score,
        "preference_score": preference_score,
        "matched_keywords": matched_keywords
    }


def rank_recommendations(
    pois: List[dict],
    memories: Optional[List[dict]] = None,
    top_k: int = 5,
    rating_weight: float = 0.4,
    distance_weight: float = 0.3,
    preference_weight: float = 0.3
) -> dict:
    """
    排序推荐结果

    Args:
        pois: POI 列表
        memories: 用户记忆列表
        top_k: 返回 Top-K 结果
        rating_weight: 评分权重
        distance_weight: 距离权重
        preference_weight: 偏好权重

    Returns:
        {
            "ranked_pois": [
                {
                    "poi": dict,
                    "score": float,
                    "score_breakdown": dict,
                    "matched_keywords": List[str]
                }
            ]
        }
    """
    if not pois:
        return {"ranked_pois": []}

    memories = memories or []

    ranked_pois = []
    for poi in pois:
        score_result = calculate_score(
            poi, memories, rating_weight, distance_weight, preference_weight
        )

        ranked_pois.append({
            "poi": poi,
            "score": score_result["score"],
            "score_breakdown": {
                "rating_score": score_result["rating_score"],
                "distance_score": score_result["distance_score"],
                "preference_score": score_result["preference_score"]
            },
            "matched_keywords": score_result["matched_keywords"]
        })

    # 按评分降序排序
    ranked_pois.sort(key=lambda x: x["score"], reverse=True)

    return {"ranked_pois": ranked_pois[:top_k]}


def generate_explanation(
    poi: dict,
    matched_keywords: Optional[List[str]] = None
) -> dict:
    """
    生成推荐理由

    Args:
        poi: POI 对象
        matched_keywords: 匹配的关键词

    Returns:
        {
            "explanation": str
        }
    """
    text = f"{poi['name']}距离你{poi['distance_km']}km，评分{poi['rating']}"

    if poi.get("price_level"):
        text += f"，价格等级{poi['price_level']}/4"

    if matched_keywords:
        text += f"，符合你喜欢的{'、'.join(matched_keywords)}"

    return {"explanation": text}


def rank_candidate_pois(
    candidates: List[dict],
    user_preferences: dict,
    intent: dict,
    top_k: int = 5
) -> dict:
    """
    使用可解释规则对候选 POI 进行排序

    Args:
        candidates: 候选 POI 列表
        user_preferences: 用户偏好，包含:
            - stable_preferences: 稳定偏好列表
            - recent_preferences: 近期偏好列表
            - negative_preferences: 负向偏好列表
        intent: 当前意图
        top_k: 返回 Top-K 结果

    Returns:
        {
            "ranked_results": List[dict],
            "total_candidates": int
        }
    """
    # 校验参数
    if not isinstance(candidates, list):
        return {
            "ranked_results": [],
            "total_candidates": 0,
            "error": "candidates 必须是列表类型"
        }

    if not candidates:
        return {
            "ranked_results": [],
            "total_candidates": 0
        }

    if not isinstance(user_preferences, dict):
        return {
            "ranked_results": [],
            "total_candidates": 0,
            "error": "user_preferences 必须是字典类型"
        }

    if not isinstance(intent, dict):
        return {
            "ranked_results": [],
            "total_candidates": 0,
            "error": "intent 必须是字典类型"
        }

    # 提取偏好
    stable_prefs = user_preferences.get("stable_preferences", [])
    recent_prefs = user_preferences.get("recent_preferences", [])
    negative_prefs = user_preferences.get("negative_preferences", [])

    # 构建偏好关键词集合（带权重）
    stable_keywords = {}
    for pref in stable_prefs:
        for kw in pref.get("keywords", []):
            stable_keywords[kw] = pref.get("weight", 0.9)

    recent_keywords = {}
    for pref in recent_prefs:
        for kw in pref.get("keywords", []):
            recent_keywords[kw] = pref.get("weight", 0.5)

    negative_keywords = set()
    for pref in negative_prefs:
        negative_keywords.update(pref.get("keywords", []))

    # 对每个候选 POI 计算分数
    scored_candidates = []
    for poi in candidates:
        # 1. 评分分数 (0-1)
        rating_score = poi.get("rating", 4.0) / 5.0

        # 2. 距离分数 (0-1)
        distance_km = poi.get("distance_km", 5.0)
        distance_score = 1.0 / (1.0 + distance_km)

        # 3. 稳定偏好匹配分数 (0-1)
        stable_match_score = 0.0
        stable_matched = []
        poi_tags = poi.get("tags", [])

        for tag in poi_tags:
            if tag in stable_keywords:
                stable_matched.append(tag)
                stable_match_score += stable_keywords[tag]

        if stable_keywords:
            stable_match_score = min(stable_match_score / len(stable_keywords), 1.0)

        # 4. 近期偏好匹配分数 (0-1)
        recent_match_score = 0.0
        recent_matched = []

        for tag in poi_tags:
            if tag in recent_keywords:
                recent_matched.append(tag)
                recent_match_score += recent_keywords[tag]

        if recent_keywords:
            recent_match_score = min(recent_match_score / len(recent_keywords), 1.0)

        # 5. 负向偏好惩罚 (0-1)
        negative_penalty = 0.0
        negative_matched = []

        for tag in poi_tags:
            if tag in negative_keywords:
                negative_matched.append(tag)
                negative_penalty += 0.3

        negative_penalty = min(negative_penalty, 1.0)

        # 6. 综合评分（可解释规则）
        # 权重分配：评分 30%，距离 25%，稳定偏好 25%，近期偏好 15%，负向惩罚 5%
        total_score = (
            0.30 * rating_score +
            0.25 * distance_score +
            0.25 * stable_match_score +
            0.15 * recent_match_score -
            0.05 * negative_penalty
        )

        # 确保分数在 [0, 1] 范围内
        total_score = max(0.0, min(1.0, total_score))

        scored_candidates.append({
            "poi": poi,
            "total_score": round(total_score, 4),
            "score_breakdown": {
                "rating_score": round(rating_score, 4),
                "distance_score": round(distance_score, 4),
                "stable_preference_score": round(stable_match_score, 4),
                "recent_preference_score": round(recent_match_score, 4),
                "negative_penalty": round(negative_penalty, 4)
            },
            "matched_preferences": {
                "stable": stable_matched,
                "recent": recent_matched,
                "negative": negative_matched
            }
        })

    # 排序：按总分降序，总分相同时按距离升序
    scored_candidates.sort(
        key=lambda x: (-x["total_score"], x["poi"].get("distance_km", 999)),
        reverse=False
    )

    # 返回 Top-K
    return {
        "ranked_results": scored_candidates[:top_k],
        "total_candidates": len(candidates)
    }
