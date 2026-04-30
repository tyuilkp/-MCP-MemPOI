"""
示例数据生成脚本

生成 50 条 mock POI 数据：
- 20 咖啡馆
- 20 餐厅
- 10 景点
"""

import sqlite3
import json
import sys

# 设置 UTF-8 输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


MOCK_POIS = [
    # 咖啡馆 (20) - 五道口附近 (39.9889, 116.3298)
    {"name": "小隐咖啡", "category": "cafe", "latitude": 39.9895, "longitude": 116.3305, "distance_km": 0.5, "rating": 4.7, "price_level": 2, "tags": ["安静", "独立", "有wifi", "插座多"], "address": "五道口华清嘉园15号楼1层", "description": "独立咖啡馆，环境安静，适合学习工作"},
    {"name": "时光书店咖啡", "category": "cafe", "latitude": 39.9910, "longitude": 116.3280, "distance_km": 0.8, "rating": 4.6, "price_level": 2, "tags": ["安静", "独立", "有wifi", "书店"], "address": "五道口城铁站西侧200米", "description": "书店+咖啡馆，文艺氛围浓厚"},
    {"name": "漫咖啡五道口店", "category": "cafe", "latitude": 39.9870, "longitude": 116.3320, "distance_km": 1.2, "rating": 4.4, "price_level": 2, "tags": ["安静", "连锁", "有wifi", "网红"], "address": "五道口购物中心3层", "description": "连锁咖啡品牌，装修网红风"},
    {"name": "星巴克五道口店", "category": "cafe", "latitude": 39.9880, "longitude": 116.3290, "distance_km": 0.3, "rating": 4.5, "price_level": 3, "tags": ["连锁", "有wifi"], "address": "五道口购物中心1层", "description": "连锁咖啡品牌"},
    {"name": "太平洋咖啡", "category": "cafe", "latitude": 39.9112, "longitude": 116.4144, "distance_km": 1.0, "rating": 4.2, "price_level": 3, "tags": ["连锁", "有wifi"]},
    {"name": "猫的天空之城", "category": "cafe", "latitude": 39.9262, "longitude": 116.4294, "distance_km": 2.8, "rating": 4.8, "price_level": 2, "tags": ["安静", "独立", "有wifi"]},
    {"name": "库迪咖啡", "category": "cafe", "latitude": 39.9072, "longitude": 116.4104, "distance_km": 0.6, "rating": 4.1, "price_level": 2, "tags": ["连锁", "便宜"]},
    {"name": "Manner咖啡", "category": "cafe", "latitude": 39.9152, "longitude": 116.4194, "distance_km": 1.5, "rating": 4.6, "price_level": 2, "tags": ["独立", "便宜"]},
    {"name": "咖啡陪你", "category": "cafe", "latitude": 39.9222, "longitude": 116.4254, "distance_km": 2.2, "rating": 4.0, "price_level": 3, "tags": ["连锁", "有wifi"]},
    {"name": "雕刻时光", "category": "cafe", "latitude": 39.9282, "longitude": 116.4314, "distance_km": 3.2, "rating": 4.7, "price_level": 3, "tags": ["安静", "独立", "有wifi"]},
    {"name": "Costa咖啡", "category": "cafe", "latitude": 39.9132, "longitude": 116.4164, "distance_km": 1.3, "rating": 4.3, "price_level": 3, "tags": ["连锁", "有wifi"]},
    {"name": "Seesaw咖啡", "category": "cafe", "latitude": 39.9202, "longitude": 116.4234, "distance_km": 2.0, "rating": 4.8, "price_level": 4, "tags": ["独立", "有wifi"]},
    {"name": "麦隆咖啡", "category": "cafe", "latitude": 39.9082, "longitude": 116.4114, "distance_km": 0.7, "rating": 4.0, "price_level": 2, "tags": ["连锁", "便宜"]},
    {"name": "挪瓦咖啡", "category": "cafe", "latitude": 39.9162, "longitude": 116.4204, "distance_km": 1.6, "rating": 4.5, "price_level": 3, "tags": ["独立", "有wifi"]},
    {"name": "%Arabica", "category": "cafe", "latitude": 39.9302, "longitude": 116.4334, "distance_km": 3.5, "rating": 4.9, "price_level": 4, "tags": ["独立", "安静"]},
    {"name": "M Stand", "category": "cafe", "latitude": 39.9172, "longitude": 116.4214, "distance_km": 1.7, "rating": 4.6, "price_level": 3, "tags": ["独立", "有wifi"]},
    {"name": "Peet's Coffee", "category": "cafe", "latitude": 39.9212, "longitude": 116.4244, "distance_km": 2.1, "rating": 4.4, "price_level": 3, "tags": ["连锁", "有wifi"]},
    {"name": "鱼眼咖啡", "category": "cafe", "latitude": 39.9252, "longitude": 116.4284, "distance_km": 2.6, "rating": 4.7, "price_level": 2, "tags": ["安静", "独立"]},
    {"name": "三顿半", "category": "cafe", "latitude": 39.9182, "longitude": 116.4224, "distance_km": 1.9, "rating": 4.5, "price_level": 3, "tags": ["独立", "有wifi"]},
    {"name": "永璞咖啡", "category": "cafe", "latitude": 39.9122, "longitude": 116.4154, "distance_km": 1.1, "rating": 4.2, "price_level": 2, "tags": ["独立", "便宜"]},

    # 餐厅 (20)
    {"name": "川味观", "category": "restaurant", "latitude": 39.9042, "longitude": 116.4074, "distance_km": 0.5, "rating": 4.6, "price_level": 2, "tags": ["辣", "川菜"]},
    {"name": "海底捞", "category": "restaurant", "latitude": 39.9102, "longitude": 116.4134, "distance_km": 0.9, "rating": 4.7, "price_level": 3, "tags": ["辣", "火锅", "高档"]},
    {"name": "西贝莜面村", "category": "restaurant", "latitude": 39.9162, "longitude": 116.4204, "distance_km": 1.6, "rating": 4.5, "price_level": 3, "tags": ["清淡", "西北菜"]},
    {"name": "外婆家", "category": "restaurant", "latitude": 39.9122, "longitude": 116.4154, "distance_km": 1.1, "rating": 4.3, "price_level": 2, "tags": ["清淡", "便宜"]},
    {"name": "绿茶餐厅", "category": "restaurant", "latitude": 39.9182, "longitude": 116.4224, "distance_km": 1.9, "rating": 4.4, "price_level": 2, "tags": ["清淡", "便宜"]},
    {"name": "小龙坎", "category": "restaurant", "latitude": 39.9142, "longitude": 116.4174, "distance_km": 1.2, "rating": 4.6, "price_level": 3, "tags": ["辣", "火锅"]},
    {"name": "云海肴", "category": "restaurant", "latitude": 39.9202, "longitude": 116.4234, "distance_km": 2.0, "rating": 4.5, "price_level": 3, "tags": ["清淡", "云南菜"]},
    {"name": "呷哺呷哺", "category": "restaurant", "latitude": 39.9082, "longitude": 116.4114, "distance_km": 0.7, "rating": 4.2, "price_level": 2, "tags": ["火锅", "便宜"]},
    {"name": "大董烤鸭", "category": "restaurant", "latitude": 39.9262, "longitude": 116.4294, "distance_km": 2.8, "rating": 4.8, "price_level": 4, "tags": ["高档", "烤鸭"]},
    {"name": "全聚德", "category": "restaurant", "latitude": 39.9222, "longitude": 116.4254, "distance_km": 2.2, "rating": 4.4, "price_level": 4, "tags": ["高档", "烤鸭"]},
    {"name": "眉州东坡", "category": "restaurant", "latitude": 39.9152, "longitude": 116.4194, "distance_km": 1.5, "rating": 4.5, "price_level": 3, "tags": ["辣", "川菜"]},
    {"name": "南京大牌档", "category": "restaurant", "latitude": 39.9192, "longitude": 116.4224, "distance_km": 1.8, "rating": 4.6, "price_level": 3, "tags": ["清淡", "江浙菜"]},
    {"name": "新辣道", "category": "restaurant", "latitude": 39.9112, "longitude": 116.4144, "distance_km": 1.0, "rating": 4.3, "price_level": 2, "tags": ["辣", "火锅"]},
    {"name": "避风塘", "category": "restaurant", "latitude": 39.9172, "longitude": 116.4214, "distance_km": 1.7, "rating": 4.4, "price_level": 3, "tags": ["清淡", "粤菜"]},
    {"name": "湘鄂情", "category": "restaurant", "latitude": 39.9132, "longitude": 116.4164, "distance_km": 1.3, "rating": 4.2, "price_level": 2, "tags": ["辣", "湘菜"]},
    {"name": "金鼎轩", "category": "restaurant", "latitude": 39.9212, "longitude": 116.4244, "distance_km": 2.1, "rating": 4.5, "price_level": 2, "tags": ["清淡", "便宜"]},
    {"name": "花家怡园", "category": "restaurant", "latitude": 39.9242, "longitude": 116.4274, "distance_km": 2.5, "rating": 4.7, "price_level": 4, "tags": ["高档", "京菜"]},
    {"name": "俏江南", "category": "restaurant", "latitude": 39.9282, "longitude": 116.4314, "distance_km": 3.2, "rating": 4.6, "price_level": 4, "tags": ["高档", "川菜"]},
    {"name": "小吊梨汤", "category": "restaurant", "latitude": 39.9072, "longitude": 116.4104, "distance_km": 0.6, "rating": 4.3, "price_level": 2, "tags": ["清淡", "便宜"]},
    {"name": "局气", "category": "restaurant", "latitude": 39.9252, "longitude": 116.4284, "distance_km": 2.6, "rating": 4.7, "price_level": 3, "tags": ["京菜", "高档"]},

    # 景点 (10)
    {"name": "故宫博物院", "category": "attraction", "latitude": 39.9163, "longitude": 116.3972, "distance_km": 1.5, "rating": 4.9, "price_level": 2, "tags": ["室内", "收费", "历史"]},
    {"name": "天坛公园", "category": "attraction", "latitude": 39.8825, "longitude": 116.4074, "distance_km": 2.4, "rating": 4.7, "price_level": 1, "tags": ["室外", "收费", "历史"]},
    {"name": "颐和园", "category": "attraction", "latitude": 39.9999, "longitude": 116.2753, "distance_km": 8.5, "rating": 4.8, "price_level": 2, "tags": ["室外", "收费", "历史"]},
    {"name": "北海公园", "category": "attraction", "latitude": 39.9262, "longitude": 116.3886, "distance_km": 2.1, "rating": 4.6, "price_level": 1, "tags": ["室外", "收费"]},
    {"name": "景山公园", "category": "attraction", "latitude": 39.9282, "longitude": 116.3952, "distance_km": 2.5, "rating": 4.5, "price_level": 1, "tags": ["室外", "收费"]},
    {"name": "国家博物馆", "category": "attraction", "latitude": 39.9042, "longitude": 116.3974, "distance_km": 1.2, "rating": 4.8, "price_level": None, "tags": ["室内", "免费", "历史"]},
    {"name": "798艺术区", "category": "attraction", "latitude": 39.9842, "longitude": 116.4974, "distance_km": 9.8, "rating": 4.6, "price_level": None, "tags": ["室外", "免费", "艺术"]},
    {"name": "雍和宫", "category": "attraction", "latitude": 39.9482, "longitude": 116.4174, "distance_km": 4.9, "rating": 4.7, "price_level": 1, "tags": ["室内", "收费", "历史"]},
    {"name": "什刹海", "category": "attraction", "latitude": 39.9382, "longitude": 116.3874, "distance_km": 3.8, "rating": 4.5, "price_level": None, "tags": ["室外", "免费"]},
    {"name": "南锣鼓巷", "category": "attraction", "latitude": 39.9362, "longitude": 116.4024, "distance_km": 3.5, "rating": 4.3, "price_level": None, "tags": ["室外", "免费"]},
]


def load_sample_data(db_path: str = "database/mempoi.sqlite"):
    """加载示例 POI 数据到数据库"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM poi_info")
    count = cursor.fetchone()[0]

    if count > 0:
        print(f"数据库已有 {count} 条 POI 数据，跳过导入")
        conn.close()
        return

    # 插入 POI 数据
    for poi in MOCK_POIS:
        cursor.execute("""
            INSERT INTO poi_info (name, category, latitude, longitude, distance_km, rating, price_level, tags, address, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            poi["name"],
            poi["category"],
            poi["latitude"],
            poi["longitude"],
            poi["distance_km"],
            poi["rating"],
            poi["price_level"],
            json.dumps(poi["tags"], ensure_ascii=False),
            f"{poi['name']}附近",  # address
            f"{poi['category']} - {', '.join(poi['tags'])}"  # description
        ))

    conn.commit()
    conn.close()

    print(f"✓ 成功导入 {len(MOCK_POIS)} 条 POI 数据")


if __name__ == "__main__":
    load_sample_data()
