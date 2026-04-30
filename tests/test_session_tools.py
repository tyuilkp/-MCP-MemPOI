"""
测试 session_tools.py 中的 parse_and_save_session_intent 函数
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.session_tools import parse_and_save_session_intent


def test_parse_and_save_session_intent():
    """测试 parse_and_save_session_intent 函数"""

    print("=== 测试 parse_and_save_session_intent ===\n")

    # 测试 1: 正常情况
    print("测试 1: 正常保存会话意图")
    result = parse_and_save_session_intent(
        user_id="default_user",
        session_id="test_session_001",
        raw_query="我想找附近2公里内的咖啡馆",
        parsed_intent={
            "poi_type": "cafe",
            "location": {"latitude": 39.9042, "longitude": 116.4074},
            "scenario": "工作",
            "constraints": {
                "max_distance_km": 2.0,
                "price_level": None
            }
        }
    )
    print(f"结果: {result}\n")

    # 测试 2: 缺少必填字段
    print("测试 2: 缺少必填字段 (scenario)")
    result = parse_and_save_session_intent(
        user_id="default_user",
        session_id="test_session_002",
        raw_query="我想找餐厅",
        parsed_intent={
            "poi_type": "restaurant",
            "location": {"latitude": 39.9042, "longitude": 116.4074},
            "constraints": {}
        }
    )
    print(f"结果: {result}\n")

    # 测试 3: 无效的 poi_type
    print("测试 3: 无效的 poi_type")
    result = parse_and_save_session_intent(
        user_id="default_user",
        session_id="test_session_003",
        raw_query="我想找酒店",
        parsed_intent={
            "poi_type": "hotel",
            "location": {"latitude": 39.9042, "longitude": 116.4074},
            "scenario": "旅游",
            "constraints": {}
        }
    )
    print(f"结果: {result}\n")

    # 测试 4: 空的 user_id
    print("测试 4: 空的 user_id")
    result = parse_and_save_session_intent(
        user_id="",
        session_id="test_session_004",
        raw_query="我想找景点",
        parsed_intent={
            "poi_type": "attraction",
            "location": {"latitude": 39.9042, "longitude": 116.4074},
            "scenario": "旅游",
            "constraints": {}
        }
    )
    print(f"结果: {result}\n")

    # 测试 5: 不存在的用户
    print("测试 5: 不存在的用户")
    result = parse_and_save_session_intent(
        user_id="nonexistent_user",
        session_id="test_session_005",
        raw_query="我想找咖啡馆",
        parsed_intent={
            "poi_type": "cafe",
            "location": {"latitude": 39.9042, "longitude": 116.4074},
            "scenario": "工作",
            "constraints": {}
        }
    )
    print(f"结果: {result}\n")

    # 测试 6: 重复的 session_id
    print("测试 6: 重复的 session_id")
    result = parse_and_save_session_intent(
        user_id="default_user",
        session_id="test_session_001",  # 重复使用
        raw_query="再找一个咖啡馆",
        parsed_intent={
            "poi_type": "cafe",
            "location": {"latitude": 39.9042, "longitude": 116.4074},
            "scenario": "休闲",
            "constraints": {}
        }
    )
    print(f"结果: {result}\n")


if __name__ == "__main__":
    test_parse_and_save_session_intent()
