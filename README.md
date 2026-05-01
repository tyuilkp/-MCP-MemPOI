# MCP-MemPOI

基于 FastMCP 的 POI 推荐系统，支持记忆和个性化推荐。

## 🏗️ 架构说明

本项目是 **Table MCP**，负责运行时推荐系统。它与 **Graph MCP** 配合工作：

- **Table MCP**（本项目）：运行时推荐、检索、排序、解释、反馈更新
- **Graph MCP**（独立项目）：将图结构 POI 数据集转换为关系表

### 数据流

```
Graph MCP → poi_info 表 → Table MCP → 用户推荐
         → poi_relations 表 ↗
```

## 项目结构

```
mcp-mempoi/
├── README.md
├── server.py              # FastMCP 服务器主入口
├── init_db.py            # 数据库初始化脚本
├── sample_data.py        # 示例数据生成
├── requirements.txt      # Python 依赖
├── config.yaml          # 配置文件
├── database/            # 数据库文件目录
│   └── mempoi.sqlite
├── scripts/             # 脚本
│   ├── run_demo.py
│   └── migrate_graph_tables.py  # Graph-to-Table 迁移脚本
├── tools/               # MCP Tools 实现
│   ├── session_tools.py    # 会话管理工具
│   ├── memory_tools.py     # 记忆管理工具
│   ├── poi_tools.py        # POI 搜索工具
│   ├── ranking_tools.py    # 排序推荐工具
│   └── feedback_tools.py   # 反馈处理工具
├── schemas/             # JSON Schema 定义
│   ├── intent_schema.json
│   ├── poi_schema.json
│   ├── memory_schema.json
│   └── feedback_schema.json
├── tests/              # 单元测试
│   ├── test_session_tools.py
│   ├── test_memory_tools.py
│   ├── test_poi_tools.py
│   ├── test_ranking_tools.py
│   └── test_feedback_tools.py
└── docs/               # 文档
    ├── tool_spec.md
    ├── workflow.md
    └── demo_script.md
```

## 快速开始

### 方式一：一键初始化（推荐）

```bash
python quickstart.py
```

这将自动完成：安装依赖、初始化数据库、生成示例数据、运行演示。

### 方式二：手动初始化

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **初始化数据库**
```bash
python init_db.py
```

3. **运行 Graph-to-Table 迁移（支持 Graph MCP 数据写入）**
```bash
python scripts/migrate_graph_tables.py
```

这将创建以下表：
- `poi_info` - POI 基础信息（Graph MCP 写入，Table MCP 读取）
- `poi_relations` - POI 关系（Graph MCP 写入，Table MCP 可选读取）
- `graph_import_log` - 图数据导入日志（Graph MCP 写入）

4. **生成示例数据（可选）**
```bash
python sample_data.py
```

5. **启动 MCP Server**
```bash
python server.py
```

服务器将以 stdio 模式启动，等待 MCP 客户端连接。

## MCP Tools

本项目提供 6 个核心 MCP Tools：

### 1. parse_and_save_session_intent
解析并保存会话意图

**参数:**
- `user_id` (str): 用户ID
- `session_id` (str): 会话ID
- `raw_query` (str): 用户原始查询文本
- `parsed_intent` (dict): 解析后的意图，包含 poi_type, location, scenario, constraints

**返回:** `{success: bool, session_id: str, intent: dict}`

### 2. retrieve_user_preference_memory
检索用户偏好记忆

**参数:**
- `user_id` (str): 用户ID
- `intent` (dict): 当前意图，必须包含 poi_type

**返回:** `{stable_preferences: list, recent_preferences: list, negative_preferences: list, default_memory: bool}`

### 3. retrieve_candidate_pois
检索候选POI

**参数:**
- `location` (dict): 位置信息 (latitude, longitude)
- `poi_type` (str): POI类型 (cafe/restaurant/attraction)
- `constraints` (dict): 约束条件 (max_distance_km, price_level, tags)
- `top_k` (int): 返回数量限制，默认20

**返回:** `{candidates: list, total_count: int, empty_result: bool}`

### 4. rank_candidate_pois
对候选POI进行排序

**参数:**
- `candidates` (list): 候选POI列表
- `user_preferences` (dict): 用户偏好
- `intent` (dict): 当前意图
- `top_k` (int): 返回Top-K结果，默认5

**返回:** `{ranked_results: list, total_candidates: int}`

**评分规则:**
- 评分分数 30%
- 距离分数 25%
- 稳定偏好匹配 25%
- 近期偏好匹配 15%
- 负向偏好惩罚 5%

### 5. save_recommendation_log
保存推荐日志

**参数:**
- `session_id` (str): 会话ID
- `user_id` (str): 用户ID
- `ranked_results` (list): 排序后的推荐结果

**返回:** `{success: bool, saved_count: int}`

### 6. update_preference_from_feedback
根据反馈更新用户偏好

**参数:**
- `user_id` (str): 用户ID
- `poi_id` (int): POI ID
- `feedback_type` (str): 反馈类型 (positive/negative/correction)
- `feedback_details` (dict, 可选): 反馈详情

**返回:** `{success: bool, updated_preferences: list, evidence: str, source: str, timestamp: str}`

## 配置 MCP 客户端

### Claude Desktop 配置

编辑 Claude Desktop 配置文件：

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

添加以下配置（将路径替换为你的实际安装路径）：

```json
{
  "mcpServers": {
    "mempoi": {
      "command": "python",
      "args": ["/path/to/mcp-mempoi/server.py"],
      "cwd": "/path/to/mcp-mempoi"
    }
  }
}
```

**Windows 示例:**
```json
{
  "mcpServers": {
    "mempoi": {
      "command": "python",
      "args": ["C:\\Users\\YourName\\mcp-mempoi\\server.py"],
      "cwd": "C:\\Users\\YourName\\mcp-mempoi"
    }
  }
}
```

重启 Claude Desktop 后即可使用 MCP-MemPOI 工具。

### Claude Code CLI 配置

在 Claude Code 中使用，编辑配置文件：

**位置:** `~/.claude/settings.json` (macOS/Linux) 或 `%USERPROFILE%\.claude\settings.json` (Windows)

添加以下配置：

```json
{
  "mcpServers": {
    "mempoi": {
      "command": "python",
      "args": ["/path/to/mcp-mempoi/server.py"],
      "cwd": "/path/to/mcp-mempoi"
    }
  }
}
```

重启 Claude Code 后即可使用。

## 开发

### 运行测试

```bash
# 运行所有测试
python tests/test_session_tools.py
python tests/test_memory_tools.py
python tests/test_poi_tools.py
python tests/test_ranking_tools.py
python tests/test_feedback_tools.py
```

### 数据库结构

#### Table MCP 运行时表（Table MCP 读写）
- `user_profile`: 用户档案
- `session_intent`: 会话意图
- `preference_memory`: 用户偏好记忆
- `recommendation_log`: 推荐日志
- `feedback_log`: 反馈日志

#### Graph MCP 数据表（Graph MCP 写入，Table MCP 读取）
- `poi_info`: POI 基础信息（Graph MCP 从图数据集转换写入）
- `poi_relations`: POI 关系（Graph MCP 从图边转换写入）
- `graph_import_log`: 图数据导入日志（Graph MCP 记录导入元数据）

详细结构见 `init_db.py` 和 `scripts/migrate_graph_tables.py`。

## 工作流程示例

```python
# 1. 解析并保存会话意图
parse_and_save_session_intent(
    user_id="user_001",
    session_id="session_001",
    raw_query="我想找附近2公里内安静的咖啡馆",
    parsed_intent={
        "poi_type": "cafe",
        "location": {"latitude": 39.9042, "longitude": 116.4074},
        "scenario": "工作",
        "constraints": {"max_distance_km": 2.0}
    }
)

# 2. 检索用户偏好
preferences = retrieve_user_preference_memory(
    user_id="user_001",
    intent={"poi_type": "cafe"}
)

# 3. 检索候选POI
candidates = retrieve_candidate_pois(
    location={"latitude": 39.9042, "longitude": 116.4074},
    poi_type="cafe",
    constraints={"max_distance_km": 2.0},
    top_k=20
)

# 4. 排序候选POI
ranked = rank_candidate_pois(
    candidates=candidates["candidates"],
    user_preferences=preferences,
    intent={"poi_type": "cafe"},
    top_k=5
)

# 5. 保存推荐日志
save_recommendation_log(
    session_id="session_001",
    user_id="user_001",
    ranked_results=ranked["ranked_results"]
)

# 6. 根据反馈更新偏好
update_preference_from_feedback(
    user_id="user_001",
    poi_id=1,
    feedback_type="positive"
)
```

## License

ISC
