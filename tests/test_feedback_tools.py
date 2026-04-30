"""
测试 feedback_tools.py 中的函数
"""

import sys
import os
import json

# 设置 UTF-8 输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.feedback_tools import save_recommendation_log, update_preference_from_feedback
import sqlite3


def setup_test_data():
    """准备测试数据"""
    db_path = "database/mempoi.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 插入测试会话
    cursor.execute("""
        INSERT OR IGNORE INTO session_intent (session_id, user_id, intent_category, raw_input)
        VALUES (?, ?, ?, ?)
    """, ("test_session_feedback", "test_user", "cafe", "找咖啡馆"))

    conn.commit()
    conn.close()
    print("✓ 测试数据准备完成\n")


def test_save_recommendation_log():
    """测试 save_recommendation_log 函数"""

    print("=== 测试 save_recommendation_log ===\n")

    # 测试 1: 正常保存推荐日志
    print("测试 1: 正常保存推荐日志")
    ranked_results = [
        {
            "poi": {"id": 1, "name": "星巴克", "distance_km": 1.2},
            "total_score": 0.85,
            "score_breakdown": {
                "rating_score": 0.9,
                "distance_score": 0.45,
                "stable_preference_score": 0.8,
                "recent_preference_score": 0.5
            },
            "matched_preferences": {
                "stable": ["安静", "独立"],
                "recent": ["有wifi"]
            }
        },
        {
            "poi": {"id": 2, "name": "小隐咖啡", "distance_km": 2.5},
            "total_score": 0.75,
            "score_breakdown": {
                "rating_score": 0.94,
                "distance_score": 0.29,
                "stable_preference_score": 0.9,
                "recent_preference_score": 0.0
            },
            "matched_preferences": {
                "stable": ["安静"],
                "recent": []
            }
        }
    ]

    result = save_recommendation_log(
        session_id="test_session_feedback",
        user_id="test_user",
        ranked_results=ranked_results
    )
    print(f"success: {result['success']}")
    print(f"saved_count: {result['saved_count']}")
    print()

    # 测试 2: 空结果列表
    print("测试 2: 空结果列表")
    result = save_recommendation_log(
        session_id="test_session_feedback",
        user_id="test_user",
        ranked_results=[]
    )
    print(f"success: {result['success']}")
    print(f"saved_count: {result['saved_count']}")
    print()

    # 测试 3: 无效参数
    print("测试 3: 无效参数（非列表）")
    result = save_recommendation_log(
        session_id="test_session_feedback",
        user_id="test_user",
        ranked_results="not a list"
    )
    print(f"success: {result['success']}")
    print(f"error: {result.get('error', 'None')}")
    print()


def test_update_preference_from_feedback():
    """测试 update_preference_from_feedback 函数"""

    print("=== 测试 update_preference_from_feedback ===\n")

    # 测试 1: 正向反馈
    print("测试 1: 正向反馈")
    result = update_preference_from_feedback(
        user_id="test_user",
        poi_id=2,  # 小隐咖啡
        feedback_type="positive"
    )
    print(f"success: {result['success']}")
    print(f"evidence: {result.get('evidence', 'None')}")
    print(f"updated_preferences: {len(result.get('updated_preferences', []))} 条")
    if result.get('updated_preferences'):
        print(f"  示例: {result['updated_preferences'][0]}")
    print()

    # 测试 2: 负向反馈
    print("测试 2: 负向反馈")
    result = update_preference_from_feedback(
        user_id="test_user",
        poi_id=1,  # 星巴克
        feedback_type="negative"
    )
    print(f"success: {result['success']}")
    print(f"evidence: {result.get('evidence', 'None')}")
    print(f"updated_preferences: {len(result.get('updated_preferences', []))} 条")
    if result.get('updated_preferences'):
        for pref in result['updated_preferences'][:2]:
            print(f"  - {pref}")
    print()

    # 测试 3: 修正反馈
    print("测试 3: 修正反馈")
    result = update_preference_from_feedback(
        user_id="test_user",
        poi_id=1,
        feedback_type="correction",
        feedback_details={"corrected_tags": ["舒适", "现代"]}
    )
    print(f"success: {result['success']}")
    print(f"evidence: {result.get('evidence', 'None')}")
    print(f"updated_preferences: {len(result.get('updated_preferences', []))} 条")
    if result.get('updated_preferences'):
        for pref in result['updated_preferences']:
            print(f"  - {pref}")
    print()

    # 测试 4: 无效的反馈类型
    print("测试 4: 无效的反馈类型")
    result = update_preference_from_feedback(
        user_id="test_user",
        poi_id=1,
        feedback_type="invalid_type"
    )
    print(f"success: {result['success']}")
    print(f"error: {result.get('error', 'None')}")
    print()

    # 测试 5: 修正反馈缺少 corrected_tags
    print("测试 5: 修正反馈缺少 corrected_tags")
    result = update_preference_from_feedback(
        user_id="test_user",
        poi_id=1,
        feedback_type="correction"
    )
    print(f"success: {result['success']}")
    print(f"error: {result.get('error', 'None')}")
    print()

    # 测试 6: 不存在的 POI
    print("测试 6: 不存在的 POI")
    result = update_preference_from_feedback(
        user_id="test_user",
        poi_id=9999,
        feedback_type="positive"
    )
    print(f"success: {result['success']}")
    print(f"error: {result.get('error', 'None')}")
    print()


if __name__ == "__main__":
    setup_test_data()
    test_save_recommendation_log()
    test_update_preference_from_feedback()
