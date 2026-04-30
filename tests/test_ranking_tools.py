"""
测试 ranking_tools.py 中的 rank_candidate_pois 函数
"""

import sys
import os

# 设置 UTF-8 输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.ranking_tools import rank_candidate_pois


def test_rank_candidate_pois():
    """测试 rank_candidate_pois 函数"""

    print("=== 测试 rank_candidate_pois ===\n")

    # 准备测试数据
    candidates = [
        {
            "id": 1,
            "name": "星巴克",
            "category": "cafe",
            "distance_km": 1.2,
            "rating": 4.5,
            "price_level": 3,
            "tags": ["连锁", "有wifi"]
        },
        {
            "id": 2,
            "name": "小隐咖啡",
            "category": "cafe",
            "distance_km": 2.5,
            "rating": 4.7,
            "price_level": 2,
            "tags": ["安静", "独立"]
        },
        {
            "id": 3,
            "name": "瑞幸咖啡",
            "category": "cafe",
            "distance_km": 0.8,
            "rating": 4.3,
            "price_level": 2,
            "tags": ["连锁", "便宜"]
        },
        {
            "id": 4,
            "name": "猫的天空之城",
            "category": "cafe",
            "distance_km": 2.8,
            "rating": 4.8,
            "price_level": 2,
            "tags": ["安静", "独立", "有wifi"]
        }
    ]

    # 测试 1: 有稳定偏好的用户
    print("测试 1: 有稳定偏好的用户（喜欢安静、独立）")
    user_preferences = {
        "stable_preferences": [
            {"keywords": ["安静", "独立"], "weight": 0.9}
        ],
        "recent_preferences": [],
        "negative_preferences": []
    }
    result = rank_candidate_pois(
        candidates=candidates,
        user_preferences=user_preferences,
        intent={"poi_type": "cafe"},
        top_k=3
    )
    print(f"total_candidates: {result['total_candidates']}")
    for i, item in enumerate(result['ranked_results'], 1):
        print(f"{i}. {item['poi']['name']}: 总分 {item['total_score']}")
        print(f"   分项: rating={item['score_breakdown']['rating_score']}, "
              f"distance={item['score_breakdown']['distance_score']}, "
              f"stable={item['score_breakdown']['stable_preference_score']}")
        print(f"   匹配偏好: {item['matched_preferences']['stable']}")
    print()

    # 测试 2: 有负向偏好的用户
    print("测试 2: 有负向偏好的用户（不喜欢连锁）")
    user_preferences = {
        "stable_preferences": [],
        "recent_preferences": [],
        "negative_preferences": [
            {"keywords": ["连锁"], "weight": 0.2}
        ]
    }
    result = rank_candidate_pois(
        candidates=candidates,
        user_preferences=user_preferences,
        intent={"poi_type": "cafe"},
        top_k=3
    )
    print(f"total_candidates: {result['total_candidates']}")
    for i, item in enumerate(result['ranked_results'], 1):
        print(f"{i}. {item['poi']['name']}: 总分 {item['total_score']}")
        print(f"   负向惩罚: {item['score_breakdown']['negative_penalty']}")
        print(f"   负向匹配: {item['matched_preferences']['negative']}")
    print()

    # 测试 3: 冷启动（无偏好）
    print("测试 3: 冷启动用户（无偏好）")
    user_preferences = {
        "stable_preferences": [],
        "recent_preferences": [],
        "negative_preferences": []
    }
    result = rank_candidate_pois(
        candidates=candidates,
        user_preferences=user_preferences,
        intent={"poi_type": "cafe"},
        top_k=3
    )
    print(f"total_candidates: {result['total_candidates']}")
    for i, item in enumerate(result['ranked_results'], 1):
        print(f"{i}. {item['poi']['name']}: 总分 {item['total_score']}")
        print(f"   主要因素: rating={item['score_breakdown']['rating_score']}, "
              f"distance={item['score_breakdown']['distance_score']}")
    print()

    # 测试 4: 空候选列表
    print("测试 4: 空候选列表")
    result = rank_candidate_pois(
        candidates=[],
        user_preferences=user_preferences,
        intent={"poi_type": "cafe"},
        top_k=3
    )
    print(f"total_candidates: {result['total_candidates']}")
    print(f"ranked_results: {len(result['ranked_results'])} 条")
    print()

    # 测试 5: 可复现性测试
    print("测试 5: 可复现性测试（运行两次应得到相同结果）")
    user_preferences = {
        "stable_preferences": [
            {"keywords": ["安静"], "weight": 0.8}
        ],
        "recent_preferences": [
            {"keywords": ["有wifi"], "weight": 0.5}
        ],
        "negative_preferences": []
    }

    result1 = rank_candidate_pois(candidates, user_preferences, {"poi_type": "cafe"}, 3)
    result2 = rank_candidate_pois(candidates, user_preferences, {"poi_type": "cafe"}, 3)

    scores1 = [r['total_score'] for r in result1['ranked_results']]
    scores2 = [r['total_score'] for r in result2['ranked_results']]

    print(f"第一次运行: {scores1}")
    print(f"第二次运行: {scores2}")
    print(f"结果一致: {scores1 == scores2}")
    print()


if __name__ == "__main__":
    test_rank_candidate_pois()
