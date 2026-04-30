"""
测试 memory_tools.py 中的 retrieve_user_preference_memory 函数
"""

import sys
import os
import json

# 设置 UTF-8 输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.memory_tools import retrieve_user_preference_memory
import sqlite3


def setup_test_data():
    """准备测试数据"""
    db_path = "database/mempoi.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 插入测试用户
    cursor.execute("""
        INSERT OR IGNORE INTO user_profile (user_id, name)
        VALUES (?, ?)
    """, ("test_user", "测试用户"))

    # 清空旧的测试数据
    cursor.execute("DELETE FROM preference_memory WHERE user_id = ?", ("test_user",))

    # 插入稳定偏好 (weight >= 0.7)
    cursor.execute("""
        INSERT INTO preference_memory (user_id, category, keywords, weight, source)
        VALUES (?, ?, ?, ?, ?)
    """, ("test_user", "cafe", json.dumps(["安静", "独立"], ensure_ascii=False), 0.9, "feedback"))

    cursor.execute("""
        INSERT INTO preference_memory (user_id, category, keywords, weight, source)
        VALUES (?, ?, ?, ?, ?)
    """, ("test_user", "cafe", json.dumps(["有wifi"], ensure_ascii=False), 0.8, "feedback"))

    # 插入近期偏好 (0.3 <= weight < 0.7)
    cursor.execute("""
        INSERT INTO preference_memory (user_id, category, keywords, weight, source)
        VALUES (?, ?, ?, ?, ?)
    """, ("test_user", "cafe", json.dumps(["便宜"], ensure_ascii=False), 0.5, "implicit"))

    # 插入负向偏好 (weight < 0.3)
    cursor.execute("""
        INSERT INTO preference_memory (user_id, category, keywords, weight, source)
        VALUES (?, ?, ?, ?, ?)
    """, ("test_user", "cafe", json.dumps(["连锁"], ensure_ascii=False), 0.2, "negative_feedback"))

    # 插入其他类别的偏好（不应被检索）
    cursor.execute("""
        INSERT INTO preference_memory (user_id, category, keywords, weight, source)
        VALUES (?, ?, ?, ?, ?)
    """, ("test_user", "restaurant", json.dumps(["辣"], ensure_ascii=False), 0.9, "feedback"))

    conn.commit()
    conn.close()
    print("✓ 测试数据准备完成\n")


def test_retrieve_user_preference_memory():
    """测试 retrieve_user_preference_memory 函数"""

    print("=== 测试 retrieve_user_preference_memory ===\n")

    # 测试 1: 正常检索（有历史偏好）
    print("测试 1: 正常检索用户偏好")
    result = retrieve_user_preference_memory(
        user_id="test_user",
        intent={"poi_type": "cafe"}
    )
    print(f"default_memory: {result['default_memory']}")
    print(f"stable_preferences: {len(result['stable_preferences'])} 条")
    print(f"recent_preferences: {len(result['recent_preferences'])} 条")
    print(f"negative_preferences: {len(result['negative_preferences'])} 条")
    if result['stable_preferences']:
        print(f"  示例: {result['stable_preferences'][0]}")
    print()

    # 测试 2: 无历史偏好的用户
    print("测试 2: 无历史偏好的用户")
    result = retrieve_user_preference_memory(
        user_id="default_user",
        intent={"poi_type": "cafe"}
    )
    print(f"default_memory: {result['default_memory']}")
    print(f"stable_preferences: {len(result['stable_preferences'])} 条")
    print(f"recent_preferences: {len(result['recent_preferences'])} 条")
    print(f"negative_preferences: {len(result['negative_preferences'])} 条")
    print()

    # 测试 3: 不同类别的偏好
    print("测试 3: 检索餐厅类别偏好")
    result = retrieve_user_preference_memory(
        user_id="test_user",
        intent={"poi_type": "restaurant"}
    )
    print(f"default_memory: {result['default_memory']}")
    print(f"stable_preferences: {len(result['stable_preferences'])} 条")
    if result['stable_preferences']:
        print(f"  示例: {result['stable_preferences'][0]}")
    print()

    # 测试 4: 缺少 poi_type
    print("测试 4: 缺少 poi_type")
    result = retrieve_user_preference_memory(
        user_id="test_user",
        intent={}
    )
    print(f"default_memory: {result['default_memory']}")
    print(f"error: {result.get('error', 'None')}")
    print()

    # 测试 5: 无效的 poi_type
    print("测试 5: 无效的 poi_type")
    result = retrieve_user_preference_memory(
        user_id="test_user",
        intent={"poi_type": "hotel"}
    )
    print(f"default_memory: {result['default_memory']}")
    print(f"error: {result.get('error', 'None')}")
    print()

    # 测试 6: 空的 user_id
    print("测试 6: 空的 user_id")
    result = retrieve_user_preference_memory(
        user_id="",
        intent={"poi_type": "cafe"}
    )
    print(f"default_memory: {result['default_memory']}")
    print(f"error: {result.get('error', 'None')}")
    print()

    # 测试 7: 不存在的用户
    print("测试 7: 不存在的用户")
    result = retrieve_user_preference_memory(
        user_id="nonexistent_user",
        intent={"poi_type": "cafe"}
    )
    print(f"default_memory: {result['default_memory']}")
    print(f"error: {result.get('error', 'None')}")
    print()


if __name__ == "__main__":
    setup_test_data()
    test_retrieve_user_preference_memory()
