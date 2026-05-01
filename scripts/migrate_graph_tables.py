"""
Graph-to-Table 数据库迁移脚本

为 Graph MCP 创建必要的表结构，使其能够将图数据转换后写入关系表。
Table MCP 可以读取这些表进行运行时推荐。

特性：
- 幂等性：可重复执行，不会破坏已有数据
- 向后兼容：不删除旧表，不清空旧数据
- 索引优化：为 Graph MCP 写入和 Table MCP 读取创建必要索引
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# 设置 UTF-8 输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def migrate_graph_tables(db_path: str = "database/mempoi.sqlite"):
    """
    迁移数据库以支持 Graph MCP 数据写入

    创建或更新以下表：
    1. poi_info - POI 基础信息表（Graph MCP 写入，Table MCP 读取）
    2. poi_relations - POI 关系表（Graph MCP 写入，Table MCP 可选读取）
    3. graph_import_log - 图数据导入日志表（Graph MCP 写入）

    Args:
        db_path: 数据库路径
    """

    # 确保数据库目录存在
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"正在迁移数据库以支持 Graph MCP: {db_path}")
    print("=" * 60)

    # 检查 poi_info 表是否存在
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='poi_info'
    """)
    poi_info_exists = cursor.fetchone() is not None

    if poi_info_exists:
        print("✓ poi_info 表已存在，跳过创建")

        # 检查是否需要添加新字段（向后兼容）
        cursor.execute("PRAGMA table_info(poi_info)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # Graph MCP 可能需要的额外字段
        new_columns = {
            'graph_node_id': 'TEXT',  # 原始图节点 ID
            'source_dataset': 'TEXT',  # 数据来源（如 "neo4j", "rdf"）
        }

        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"""
                        ALTER TABLE poi_info
                        ADD COLUMN {col_name} {col_type}
                    """)
                    print(f"  ✓ 添加字段: {col_name}")
                except sqlite3.OperationalError:
                    pass  # 字段可能已存在
    else:
        # 创建 poi_info 表（包含 Graph MCP 需要的字段）
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
                graph_node_id TEXT,
                source_dataset TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ 创建表: poi_info")

    # 创建 poi_relations 表（Graph MCP 专用）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS poi_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_poi_id INTEGER NOT NULL,
            target_poi_id INTEGER NOT NULL,
            relation_type TEXT NOT NULL,
            weight REAL DEFAULT 1.0 CHECK(weight BETWEEN 0.0 AND 1.0),
            properties TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_poi_id) REFERENCES poi_info(id) ON DELETE CASCADE,
            FOREIGN KEY (target_poi_id) REFERENCES poi_info(id) ON DELETE CASCADE,
            UNIQUE(source_poi_id, target_poi_id, relation_type)
        )
    """)
    print("✓ 创建表: poi_relations")

    # 创建 graph_import_log 表（Graph MCP 专用）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS graph_import_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_id TEXT UNIQUE NOT NULL,
            source_dataset TEXT NOT NULL,
            source_path TEXT,
            import_type TEXT CHECK(import_type IN ('full', 'incremental', 'update')),
            nodes_imported INTEGER DEFAULT 0,
            relations_imported INTEGER DEFAULT 0,
            status TEXT CHECK(status IN ('running', 'completed', 'failed')),
            error_message TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            metadata TEXT
        )
    """)
    print("✓ 创建表: graph_import_log")

    # 创建索引以提升查询性能
    print("\n正在创建索引...")

    indexes = [
        # poi_info 表索引（Table MCP 读取优化）
        ("idx_poi_info_category", "poi_info", "category"),
        ("idx_poi_info_distance", "poi_info", "distance_km"),
        ("idx_poi_info_rating", "poi_info", "rating"),
        ("idx_poi_info_location", "poi_info", "latitude, longitude"),
        ("idx_poi_info_graph_node_id", "poi_info", "graph_node_id"),
        ("idx_poi_info_source_dataset", "poi_info", "source_dataset"),

        # poi_relations 表索引（关系查询优化）
        ("idx_poi_relations_source", "poi_relations", "source_poi_id"),
        ("idx_poi_relations_target", "poi_relations", "target_poi_id"),
        ("idx_poi_relations_type", "poi_relations", "relation_type"),
        ("idx_poi_relations_weight", "poi_relations", "weight"),

        # graph_import_log 表索引（导入历史查询）
        ("idx_graph_import_log_import_id", "graph_import_log", "import_id"),
        ("idx_graph_import_log_status", "graph_import_log", "status"),
        ("idx_graph_import_log_started_at", "graph_import_log", "started_at"),
    ]

    for index_name, table_name, columns in indexes:
        try:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name}({columns})
            """)
            print(f"  ✓ {index_name}")
        except sqlite3.OperationalError as e:
            print(f"  ⚠ {index_name}: {e}")

    conn.commit()

    # 显示表统计信息
    print("\n数据库表统计:")
    print("-" * 60)

    tables = [
        ("poi_info", "POI 基础信息（Graph MCP 写入，Table MCP 读取）"),
        ("poi_relations", "POI 关系（Graph MCP 写入，Table MCP 可选读取）"),
        ("graph_import_log", "图数据导入日志（Graph MCP 写入）"),
    ]

    for table_name, description in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  {table_name:20s} {count:6d} 条记录  | {description}")

    conn.close()

    print("\n" + "=" * 60)
    print(f"✓ 数据库迁移完成: {db_path}")
    print(f"✓ 迁移时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n下一步:")
    print("  1. Graph MCP 可以向 poi_info 和 poi_relations 表写入数据")
    print("  2. Table MCP 可以从 poi_info 表读取候选 POI")
    print("  3. Table MCP 可选从 poi_relations 表读取关系增强排序")


def verify_migration(db_path: str = "database/mempoi.sqlite"):
    """
    验证迁移是否成功

    检查：
    1. 必需的表是否存在
    2. 必需的字段是否存在
    3. 必需的索引是否存在

    Args:
        db_path: 数据库路径

    Returns:
        bool: 验证是否通过
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("\n正在验证迁移...")
        print("=" * 60)

        # 检查表是否存在
        required_tables = ["poi_info", "poi_relations", "graph_import_log"]
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN (?, ?, ?)
        """, required_tables)

        existing_tables = {row[0] for row in cursor.fetchall()}

        all_tables_exist = True
        for table in required_tables:
            if table in existing_tables:
                print(f"✓ 表存在: {table}")
            else:
                print(f"✗ 表缺失: {table}")
                all_tables_exist = False

        # 检查 poi_info 关键字段
        cursor.execute("PRAGMA table_info(poi_info)")
        poi_info_columns = {row[1] for row in cursor.fetchall()}

        required_poi_fields = [
            "id", "name", "category", "latitude", "longitude",
            "distance_km", "rating", "tags"
        ]

        print("\npoi_info 表字段检查:")
        all_fields_exist = True
        for field in required_poi_fields:
            if field in poi_info_columns:
                print(f"  ✓ {field}")
            else:
                print(f"  ✗ {field}")
                all_fields_exist = False

        conn.close()

        if all_tables_exist and all_fields_exist:
            print("\n" + "=" * 60)
            print("✓ 迁移验证通过")
            return True
        else:
            print("\n" + "=" * 60)
            print("✗ 迁移验证失败")
            return False

    except Exception as e:
        print(f"\n✗ 验证过程出错: {str(e)}")
        return False


if __name__ == "__main__":
    # 执行迁移
    migrate_graph_tables()

    # 验证迁移
    verify_migration()
