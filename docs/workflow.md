# MCP-MemPOI Workflow

## 单 Agent 工作流程

MCP-MemPOI 提供了一个完整的 POI 推荐工作流，Agent 通过调用 6 个 MCP Tools 完成从意图解析到反馈更新的全流程。

## 核心流程

### 阶段 1: 推荐生成

```
用户查询
    ↓
1. parse_and_save_session_intent (解析意图)
    ↓
2. retrieve_user_preference_memory (检索偏好)
    ↓
3. retrieve_candidate_pois (检索候选)
    ↓
4. rank_candidate_pois (排序打分)
    ↓
5. save_recommendation_log (保存日志)
    ↓
返回推荐结果
```

### 阶段 2: 反馈处理

```
用户反馈
    ↓
6. update_preference_from_feedback (更新偏好)
    ↓
返回更新结果
```

## 详细步骤

### Step 1: 解析并保存会话意图

**Tool:** `parse_and_save_session_intent`

**输入:**
- `user_id`: 用户唯一标识
- `session_id`: 会话唯一标识
- `raw_query`: 用户原始查询文本
- `parsed_intent`: Agent 解析后的结构化意图
  - `poi_type`: POI 类型 (cafe/restaurant/attraction)
  - `location`: 位置信息 {latitude, longitude}
  - `scenario`: 使用场景（如"写论文"、"约会"、"商务会议"）
  - `constraints`: 约束条件
    - `max_distance_km`: 最大距离
    - `price_level`: 价格等级
    - `tags`: 必需标签（如"安静"、"有wifi"）

**输出:**
```json
{
  "success": true,
  "session_id": "session_001",
  "intent": {
    "poi_type": "cafe",
    "location": {"latitude": 39.9889, "longitude": 116.3298},
    "scenario": "写论文",
    "constraints": {
      "max_distance_km": 2.0,
      "price_level": 2,
      "tags": ["安静"]
    }
  }
}
```

**Agent 职责:**
- 从用户自然语言中提取关键信息
- 将地点名称转换为经纬度坐标
- 识别隐含约束（如"预算别太高" → price_level: 2）
- 提取场景和标签（如"写论文" → tags: ["安静"]）

---

### Step 2: 检索用户偏好记忆

**Tool:** `retrieve_user_preference_memory`

**输入:**
- `user_id`: 用户唯一标识
- `intent`: 当前意图（包含 poi_type）

**输出:**
```json
{
  "stable_preferences": [
    {
      "keywords": ["安静", "独立"],
      "weight": 0.9,
      "source": "positive_feedback",
      "updated_at": "2026-04-20 10:30:00"
    }
  ],
  "recent_preferences": [
    {
      "keywords": ["有wifi"],
      "weight": 0.5,
      "source": "positive_feedback",
      "updated_at": "2026-04-28 15:20:00"
    }
  ],
  "negative_preferences": [
    {
      "keywords": ["连锁", "网红"],
      "weight": 0.2,
      "source": "negative_feedback",
      "updated_at": "2026-04-25 09:15:00"
    }
  ],
  "default_memory": false
}
```

**偏好分类:**
- **稳定偏好** (weight ≥ 0.7): 长期稳定的喜好
- **近期偏好** (0.3 ≤ weight < 0.7): 最近的偏好趋势
- **负向偏好** (weight < 0.3): 不喜欢的特征

**冷启动处理:**
- 如果 `default_memory: true`，表示用户无历史偏好
- 系统将基于评分和距离进行推荐

---

### Step 3: 检索候选 POI

**Tool:** `retrieve_candidate_pois`

**输入:**
- `location`: 位置信息 {latitude, longitude}
- `poi_type`: POI 类型
- `constraints`: 约束条件
  - `max_distance_km`: 最大距离
  - `price_level`: 价格等级（可选）
  - `tags`: 必需标签（可选）
- `top_k`: 返回数量限制（默认 20）

**输出:**
```json
{
  "candidates": [
    {
      "id": 1,
      "name": "小隐咖啡",
      "category": "cafe",
      "latitude": 39.9889,
      "longitude": 116.3298,
      "distance_km": 0.5,
      "rating": 4.7,
      "price_level": 2,
      "tags": ["安静", "独立", "有wifi"],
      "address": "五道口华清嘉园15号楼",
      "description": "独立咖啡馆，环境安静"
    },
    {
      "id": 2,
      "name": "星巴克五道口店",
      "category": "cafe",
      "distance_km": 0.3,
      "rating": 4.5,
      "price_level": 3,
      "tags": ["连锁", "有wifi"],
      "address": "五道口购物中心1层",
      "description": "连锁咖啡品牌"
    }
  ],
  "total_count": 2,
  "empty_result": false
}
```

**检索逻辑:**
1. 基于位置和距离过滤
2. 基于 POI 类型过滤
3. 基于价格等级过滤（如果指定）
4. 基于必需标签过滤（如果指定）
5. 按距离升序、评分降序排序

---

### Step 4: 对候选 POI 进行排序

**Tool:** `rank_candidate_pois`

**输入:**
- `candidates`: 候选 POI 列表
- `user_preferences`: 用户偏好（来自 Step 2）
- `intent`: 当前意图
- `top_k`: 返回 Top-K 结果（默认 5）

**输出:**
```json
{
  "ranked_results": [
    {
      "poi": {
        "id": 1,
        "name": "小隐咖啡",
        "distance_km": 0.5,
        "rating": 4.7,
        "price_level": 2,
        "tags": ["安静", "独立", "有wifi"]
      },
      "total_score": 0.7850,
      "score_breakdown": {
        "rating_score": 0.94,
        "distance_score": 0.67,
        "stable_preference_score": 0.90,
        "recent_preference_score": 0.50,
        "negative_penalty": 0.0
      },
      "matched_preferences": {
        "stable": ["安静", "独立"],
        "recent": ["有wifi"],
        "negative": []
      }
    },
    {
      "poi": {
        "id": 2,
        "name": "星巴克五道口店",
        "distance_km": 0.3,
        "rating": 4.5,
        "price_level": 3,
        "tags": ["连锁", "有wifi"]
      },
      "total_score": 0.5420,
      "score_breakdown": {
        "rating_score": 0.90,
        "distance_score": 0.77,
        "stable_preference_score": 0.0,
        "recent_preference_score": 0.50,
        "negative_penalty": 0.30
      },
      "matched_preferences": {
        "stable": [],
        "recent": ["有wifi"],
        "negative": ["连锁"]
      }
    }
  ],
  "total_candidates": 2
}
```

**评分规则（可解释）:**
```
总分 = 0.30 × 评分分数
     + 0.25 × 距离分数
     + 0.25 × 稳定偏好匹配分数
     + 0.15 × 近期偏好匹配分数
     - 0.05 × 负向偏好惩罚
```

**分项计算:**
- **评分分数**: rating / 5.0
- **距离分数**: 1.0 / (1.0 + distance_km)
- **稳定偏好匹配**: 匹配标签权重之和 / 稳定偏好总数
- **近期偏好匹配**: 匹配标签权重之和 / 近期偏好总数
- **负向惩罚**: 每匹配一个负向标签 +0.3（最大 1.0）

**排序策略:**
- 按总分降序排列
- 总分相同时按距离升序排列

---

### Step 5: 保存推荐日志

**Tool:** `save_recommendation_log`

**输入:**
- `session_id`: 会话 ID
- `user_id`: 用户 ID
- `ranked_results`: 排序后的推荐结果（来自 Step 4）

**输出:**
```json
{
  "success": true,
  "saved_count": 2
}
```

**日志内容:**
- 每个推荐的 POI ID、排名、分数
- 分项分数明细
- 匹配的偏好关键词
- 推荐解释文本

**用途:**
- 追溯推荐历史
- 分析推荐效果
- 支持 A/B 测试
- 用户反馈关联

---

### Step 6: 根据反馈更新偏好

**Tool:** `update_preference_from_feedback`

**输入:**
- `user_id`: 用户 ID
- `poi_id`: 用户反馈的 POI ID
- `feedback_type`: 反馈类型
  - `positive`: 正向反馈（喜欢）
  - `negative`: 负向反馈（不喜欢）
  - `correction`: 修正反馈（提供正确标签）
- `feedback_details`: 反馈详情（可选）
  - `corrected_tags`: 修正后的标签（用于 correction 类型）
  - `reason`: 反馈原因

**输出:**
```json
{
  "success": true,
  "updated_preferences": [
    {
      "tag": "网红",
      "action": "decreased",
      "old_weight": 0.5,
      "new_weight": 0.3
    },
    {
      "tag": "安静",
      "action": "increased",
      "old_weight": 0.8,
      "new_weight": 0.9
    }
  ],
  "evidence": "用户对 星巴克五道口店 给予负向反馈",
  "source": "negative_feedback",
  "timestamp": "2026-04-30 09:53:46"
}
```

**更新策略:**

| 反馈类型 | 权重变化 | 新建权重 |
|---------|---------|---------|
| positive | +0.1 (最大 1.0) | 0.7 |
| negative | -0.2 (最小 0.1) | 0.2 |
| correction | 原标签 -0.15，修正标签 +0.15 | 0.75 |

**特点:**
- 所有更新都记录 evidence、source、timestamp
- 不删除历史记忆，只追加或降权
- 支持完整的偏好演化追溯

---

## Agent 实现要点

### 1. 意图理解
Agent 需要从自然语言中提取：
- 地点名称 → 经纬度坐标
- 隐含约束（"预算别太高" → price_level: 2）
- 场景标签（"写论文" → ["安静"]）
- 距离范围（"附近" → 2km，"很近" → 1km）

### 2. 结果呈现
Agent 应该：
- 按排名顺序展示推荐
- 解释推荐理由（匹配了哪些偏好）
- 说明分数构成（评分、距离、偏好匹配）
- 提供地址和描述信息

### 3. 反馈处理
Agent 需要：
- 识别反馈类型（positive/negative/correction）
- 提取反馈原因和修正标签
- 调用更新工具
- 向用户确认偏好已更新

### 4. 错误处理
- 候选为空时提示放宽约束条件
- 冷启动用户说明基于评分和距离推荐
- 工具调用失败时给出明确错误信息

---

## 工作流特点

### 可解释性
- 每个分数都有明确的计算规则
- 偏好匹配可追溯到具体标签
- 所有更新都有 evidence 和 timestamp

### 可复现性
- 相同输入产生相同输出
- 无随机性，无黑盒模型
- 排序规则完全透明

### 可追溯性
- 推荐日志记录完整推荐过程
- 偏好记忆记录所有更新历史
- 支持时间序列分析

### 隐私保护
- 所有数据存储在本地 SQLite
- 不调用外部 API
- 用户完全控制数据
