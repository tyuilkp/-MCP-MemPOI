# MCP Tools 规范

## 工具列表

### 1. 会话管理工具

#### mempoi_create_session
创建新会话

**输入**:
```json
{
  "user_id": "default_user"
}
```

**输出**:
```json
{
  "session_id": "session_default_user_20260430092100",
  "user_id": "default_user",
  "created_at": "2026-04-30 09:21:00"
}
```

#### mempoi_get_session
获取会话信息

**输入**:
```json
{
  "session_id": "session_default_user_20260430092100"
}
```

**输出**:
```json
{
  "session_id": "session_default_user_20260430092100",
  "user_id": "default_user",
  "created_at": "2026-04-30 09:21:00",
  "updated_at": "2026-04-30 09:21:00"
}
```

---

### 2. 记忆管理工具

#### mempoi_save_memory
保存用户记忆

**输入**:
```json
{
  "user_id": "default_user",
  "category": "cafe",
  "keywords": ["安静", "独立"],
  "weight": 1.0
}
```

**输出**:
```json
{
  "success": true,
  "memory_id": 1
}
```

#### mempoi_retrieve_memory
检索用户记忆

**输入**:
```json
{
  "user_id": "default_user",
  "category": "cafe"
}
```

**输出**:
```json
{
  "memories": [
    {
      "category": "cafe",
      "keywords": ["安静", "独立"],
      "weight": 0.9
    }
  ]
}
```

---

### 3. POI 搜索工具

#### mempoi_parse_intent
解析用户意图

**输入**:
```json
{
  "user_input": "附近2公里内的咖啡馆"
}
```

**输出**:
```json
{
  "category": "cafe",
  "max_distance_km": 2.0,
  "price_level": null,
  "keywords": []
}
```

#### mempoi_search_pois
搜索 POI

**输入**:
```json
{
  "category": "cafe",
  "max_distance_km": 2.0,
  "price_level": null,
  "limit": 20
}
```

**输出**:
```json
{
  "pois": [
    {
      "id": 1,
      "name": "星巴克",
      "category": "cafe",
      "distance_km": 1.2,
      "rating": 4.5,
      "price_level": 3,
      "tags": ["连锁", "有wifi"]
    }
  ]
}
```

---

### 4. 排序推荐工具

#### mempoi_rank_recommendations
排序推荐结果

**评分公式**:
```
score = 0.4 * rating_score + 0.3 * distance_score + 0.3 * preference_score
```

**输入**:
```json
{
  "pois": [...],
  "memories": [...],
  "top_k": 5
}
```

**输出**:
```json
{
  "ranked_pois": [
    {
      "poi": {...},
      "score": 0.85,
      "score_breakdown": {
        "rating_score": 0.9,
        "distance_score": 0.8,
        "preference_score": 0.6
      },
      "matched_keywords": ["安静", "独立"]
    }
  ]
}
```

#### mempoi_generate_explanation
生成推荐理由

**输入**:
```json
{
  "poi": {
    "name": "小隐咖啡",
    "distance_km": 2.5,
    "rating": 4.7,
    "price_level": 2
  },
  "matched_keywords": ["安静", "独立"]
}
```

**输出**:
```json
{
  "explanation": "小隐咖啡距离你2.5km，评分4.7，价格等级2/4，符合你喜欢的安静、独立"
}
```

---

### 5. 反馈处理工具

#### mempoi_save_feedback
保存用户反馈

**输入**:
```json
{
  "user_id": "default_user",
  "session_id": "session_default_user_20260430092100",
  "poi_id": 5,
  "rating": 5,
  "feedback_text": "这家不错"
}
```

**输出**:
```json
{
  "success": true,
  "feedback_id": 1,
  "memory_updated": true
}
```

**副作用**:
- 写入 `feedback` 表
- 如果 `rating >= 4`，更新 `memories` 表：
  - 同类别旧记忆权重 *= 0.9
  - 插入新记忆（weight=1.0）
  - 删除 weight < 0.1 的记录
