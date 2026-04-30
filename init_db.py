"""
数据库初始化脚本

创建 SQLite 数据库表结构：
- user_profile: 用户档案表
- preference_memory: 偏好记忆表
- poi_info: POI 信息表
- session_intent: 会话意图表
- recommendation_log: 推荐日志表
- feedback_log: 反馈日志表
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# 设置 UTF-8 输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def init_database(db_path: str = "database/mempoi.sqlite"):
    """初始化数据库表结构

    支持重复执行，使用 CREATE TABLE IF NOT EXISTS
    """

    # 确保数据库目录存在
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"正在初始化数据库: {db_path}")

    # 1. 创建 user_profile 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            name TEXT,
            preferences TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ 创建表: user_profile")

    # 2. 创建 preference_memory 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preference_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            category TEXT NOT NULL CHECK(category IN ('cafe', 'restaurant', 'attraction')),
            keywords TEXT NOT NULL,
            weight REAL DEFAULT 1.0 CHECK(weight BETWEEN 0.0 AND 1.0),
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profile(user_id) ON DELETE CASCADE
        )
    """)
    print("✓ 创建表: preference_memory")

    # 3. 创建 poi_info 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS poi_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL CHECK(category IN ('cafe', 'restaurant', 'attraction')),
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            distance_km REAL NOT NULL CHECK(distance_km >= 0),
            rating REAL DEFAULT 4.0 CHECK(rating BETWEEN 0.0 AND 5.0),
            price_level INTEGER CHECK(price_level BETWEEN 1 AND 4),
            tags TEXT NOT NULL,
            address TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ 创建表: poi_info")

    # 4. 创建 session_intent 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_intent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            intent_category TEXT CHECK(intent_category IN ('cafe', 'restaurant', 'attraction')),
            intent_keywords TEXT,
            max_distance_km REAL,
            price_level INTEGER CHECK(price_level BETWEEN 1 AND 4),
            raw_input TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profile(user_id) ON DELETE CASCADE
        )
    """)
    print("✓ 创建表: session_intent")

    # 5. 创建 recommendation_log 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            poi_id INTEGER NOT NULL,
            rank_position INTEGER NOT NULL,
            score REAL NOT NULL,
            rating_score REAL,
            distance_score REAL,
            preference_score REAL,
            matched_keywords TEXT,
            explanation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES session_intent(session_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES user_profile(user_id) ON DELETE CASCADE,
            FOREIGN KEY (poi_id) REFERENCES poi_info(id) ON DELETE CASCADE
        )
    """)
    print("✓ 创建表: recommendation_log")

    # 6. 创建 feedback_log 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            poi_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            feedback_text TEXT,
            feedback_type TEXT CHECK(feedback_type IN ('positive', 'negative', 'neutral')),
            memory_updated BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profile(user_id) ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES session_intent(session_id) ON DELETE CASCADE,
            FOREIGN KEY (poi_id) REFERENCES poi_info(id) ON DELETE CASCADE
        )
    """)
    print("✓ 创建表: feedback_log")

    # 创建索引以提升查询性能
    print("\n正在创建索引...")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_profile_user_id ON user_profile(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_preference_memory_user_id ON preference_memory(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_preference_memory_category ON preference_memory(user_id, category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_preference_memory_weight ON preference_memory(weight)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_poi_info_category ON poi_info(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_poi_info_distance ON poi_info(distance_km)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_poi_info_rating ON poi_info(rating)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_intent_user_id ON session_intent(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_intent_session_id ON session_intent(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendation_log_session ON recommendation_log(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendation_log_user_poi ON recommendation_log(user_id, poi_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_log_user_id ON feedback_log(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_log_session_id ON feedback_log(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_log_poi_id ON feedback_log(poi_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_log_created_at ON feedback_log(created_at)")

    print("✓ 索引创建完成")

    conn.commit()

    # 插入默认用户（如果不存在）
    print("\n正在插入默认数据...")
    cursor.execute("""
        INSERT OR IGNORE INTO user_profile (user_id, name)
        VALUES (?, ?)
    """, ("default_user", "默认用户"))

    conn.commit()
    print("✓ 默认用户已创建")

    # 显示表统计信息
    print("\n数据库表统计:")
    tables = [
        "user_profile",
        "preference_memory",
        "poi_info",
        "session_intent",
        "recommendation_log",
        "feedback_log"
    ]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  - {table}: {count} 条记录")

    conn.close()

    print(f"\n✓ 数据库初始化完成: {db_path}")
    print(f"✓ 初始化时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    init_database()
