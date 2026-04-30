"""
测试 poi_tools.py 中的 retrieve_candidate_pois 函数
"""

import sys
import os
import json

# 设置 UTF-8 输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.poi_tools import retrieve_candidate_pois
import sqlite3


def setup_test_data():
    """准备测试数据"""
    db_path = "database/mempoi.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 清空旧的测试数据
    cursor.execute("DELETE FROM poi_info")

    # 插入测试 POI 数据
    test_pois = [
        # 咖啡馆
        ("星巴克", "cafe", 39.9142, 116.4174, 1.2, 4.5, 3, json.dumps(["连锁", "有wifi"], ensure_ascii=False), "朝阳区", "连锁咖啡"),
        ("小隐咖啡", "cafe", 39.9242, 116.4274, 2.5, 4.7, 2, json.dumps(["安静", "独立"], ensure_ascii=False), "朝阳区", "独立咖啡馆"),
        ("瑞幸咖啡", "cafe", 39.9092, 116.4124, 0.8, 4.3, 2, json.dumps(["连锁", "便宜"], ensure_ascii=False), "朝阳区", "平价咖啡"),
        ("猫的天空之城", "cafe", 39.9262, 116.4294, 2.8, 4.8, 2, json.dumps(["安静", "独立", "有wifi"], ensure_ascii=False), "朝阳区", "书店咖啡"),

        # 餐厅
        ("川味观", "restaurant", 39.9042, 116.4074, 0.5, 4.6, 2, json.dumps(["辣", "川菜"], ensure_ascii=False), "朝阳区", "川菜馆"),
        ("海底捞", "restaurant", 39.9102, 116.4134, 0.9, 4.7, 3, json.dumps(["辣", "火锅", "高档"], ensure_ascii=False), "朝阳区", "火锅"),
        ("西贝莜面村", "restaurant", 39.9162, 116.4204, 1.6, 4.5, 3, json.dumps(["清淡", "西北菜"], ensure_ascii=False), "朝阳区", "西北菜"),

        # 景点
        ("故宫博物院", "attraction", 39.9163, 116.3972, 1.5, 4.9, 2, json.dumps(["室内", "收费", "历史"], ensure_ascii=False), "东城区", "历史景点"),
        ("天坛公园", "attraction", 39.8825, 116.4074, 2.4, 4.7, 1, json.dumps(["室外", "收费", "历史"], ensure_ascii=False), "东城区", "公园"),
    ]

    for poi in test_pois:
        cursor.execute("""
            INSERT INTO poi_info (name, category, latitude, longitude, distance_km, rating, price_level, tags, address, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, poi)

    conn.commit()
    conn.close()
    print("✓ 测试数据准备完成\n")


def test_retrieve_candidate_pois():
    """测试 retrieve_candidate_pois 函数"""

    print("=== 测试 retrieve_candidate_pois ===\n")

    # 测试 1: 正常检索咖啡馆
    print("测试 1: 正常检索咖啡馆（距离 <= 3km）")
    result = retrieve_candidate_pois(
        location={"latitude": 39.9042, "longitude": 116.4074},
        poi_type="cafe",
        constraints={"max_distance_km": 3.0},
        top_k=10
    )
    print(f"empty_result: {result['empty_result']}")
    print(f"total_count: {result['total_count']}")
    if result['candidates']:
        print(f"第一个候选: {result['candidates'][0]['name']} - {result['candidates'][0]['distance_km']}km")
    print()

    # 测试 2: 带价格等级过滤
    print("测试 2: 检索价格等级为2的咖啡馆")
    result = retrieve_candidate_pois(
        location={"latitude": 39.9042, "longitude": 116.4074},
        poi_type="cafe",
        constraints={"max_distance_km": 5.0, "price_level": 2},
        top_k=10
    )
    print(f"total_count: {result['total_count']}")
    for poi in result['candidates']:
        print(f"  - {poi['name']}: 价格等级 {poi['price_level']}")
    print()

    # 测试 3: 带标签过滤
    print("测试 3: 检索带有'安静'和'独立'标签的咖啡馆")
    result = retrieve_candidate_pois(
        location={"latitude": 39.9042, "longitude": 116.4074},
        poi_type="cafe",
        constraints={"max_distance_km": 5.0, "tags": ["安静", "独立"]},
        top_k=10
    )
    print(f"total_count: {result['total_count']}")
    for poi in result['candidates']:
        print(f"  - {poi['name']}: {poi['tags']}")
    print()

    # 测试 4: top_k 限制
    print("测试 4: 限制返回 top_k=2")
    result = retrieve_candidate_pois(
        location={"latitude": 39.9042, "longitude": 116.4074},
        poi_type="cafe",
        constraints={"max_distance_km": 10.0},
        top_k=2
    )
    print(f"total_count: {result['total_count']}")
    print(f"返回数量: {len(result['candidates'])}")
    print()

    # 测试 5: 空结果
    print("测试 5: 距离过小导致空结果")
    result = retrieve_candidate_pois(
        location={"latitude": 39.9042, "longitude": 116.4074},
        poi_type="cafe",
        constraints={"max_distance_km": 0.5},
        top_k=10
    )
    print(f"empty_result: {result['empty_result']}")
    print(f"total_count: {result['total_count']}")
    print()

    # 测试 6: 无效的 poi_type
    print("测试 6: 无效的 poi_type")
    result = retrieve_candidate_pois(
        location={"latitude": 39.9042, "longitude": 116.4074},
        poi_type="hotel",
        constraints={},
        top_k=10
    )
    print(f"empty_result: {result['empty_result']}")
    print(f"error: {result.get('error', 'None')}")
    print()

    # 测试 7: 缺少 location 字段
    print("测试 7: 缺少 location 字段")
    result = retrieve_candidate_pois(
        location={"latitude": 39.9042},
        poi_type="cafe",
        constraints={},
        top_k=10
    )
    print(f"empty_result: {result['empty_result']}")
    print(f"error: {result.get('error', 'None')}")
    print()

    # 测试 8: 检索餐厅
    print("测试 8: 检索餐厅")
    result = retrieve_candidate_pois(
        location={"latitude": 39.9042, "longitude": 116.4074},
        poi_type="restaurant",
        constraints={"max_distance_km": 2.0},
        top_k=10
    )
    print(f"total_count: {result['total_count']}")
    for poi in result['candidates']:
        print(f"  - {poi['name']}: {poi['distance_km']}km, 评分 {poi['rating']}")
    print()


if __name__ == "__main__":
    setup_test_data()
    test_retrieve_candidate_pois()
