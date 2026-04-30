# MCP-MemPOI Demo Script

本文档演示如何使用 MCP-MemPOI 完成一个完整的 POI 推荐流程。

## 场景设定

**用户:** 张三，研究生，经常需要找地方写论文

**查询:** "我今天下午想在五道口附近找一个安静、适合写论文的咖啡馆，预算别太高。"

**后续反馈:** "不要这种网红店，我想要更安静一点。"

---

## Demo 流程

### 第一轮：推荐生成

#### Step 1: 解析并保存会话意图

**用户输入:**
```
我今天下午想在五道口附近找一个安静、适合写论文的咖啡馆，预算别太高。
```

**Agent 解析:**
- 地点: 五道口 → (39.9889, 116.3298)
- POI 类型: 咖啡馆 → cafe
- 场景: 写论文
- 约束条件:
  - 距离: "附近" → 2.0km
  - 价格: "预算别太高" → price_level: 2
  - 标签: "安静" → tags: ["安静"]

**Tool Call:**
```python
parse_and_save_session_intent(
    user_id="user_zhangsan",
    session_id="session_20260430_001",
    raw_query="我今天下午想在五道口附近找一个安静、适合写论文的咖啡馆，预算别太高。",
    parsed_intent={
        "poi_type": "cafe",
        "location": {
            "latitude": 39.9889,
            "longitude": 116.3298
        },
        "scenario": "写论文",
        "constraints": {
            "max_distance_km": 2.0,
            "price_level": 2,
            "tags": ["安静"]
        }
    }
)
```

**返回:**
```json
{
  "success": true,
  "session_id": "session_20260430_001",
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

---

#### Step 2: 检索用户偏好记忆

**Tool Call:**
```python
retrieve_user_preference_memory(
    user_id="user_zhangsan",
    intent={"poi_type": "cafe"}
)
```

**返回:**
```json
{
  "stable_preferences": [
    {
      "keywords": ["安静", "独立"],
      "weight": 0.85,
      "source": "positive_feedback",
      "updated_at": "2026-04-20 14:30:00"
    }
  ],
  "recent_preferences": [
    {
      "keywords": ["有wifi", "插座多"],
      "weight": 0.6,
      "source": "positive_feedback",
      "updated_at": "2026-04-28 16:45:00"
    }
  ],
  "negative_preferences": [
    {
      "keywords": ["连锁"],
      "weight": 0.25,
      "source": "negative_feedback",
      "updated_at": "2026-04-25 10:20:00"
    }
  ],
  "default_memory": false
}
```

**解读:**
- 张三长期喜欢安静、独立的咖啡馆
- 最近关注有 wifi 和插座
- 不太喜欢连锁咖啡馆

---

#### Step 3: 检索候选 POI

**Tool Call:**
```python
retrieve_candidate_pois(
    location={"latitude": 39.9889, "longitude": 116.3298},
    poi_type="cafe",
    constraints={
        "max_distance_km": 2.0,
        "price_level": 2,
        "tags": ["安静"]
    },
    top_k=20
)
```

**返回:**
```json
{
  "candidates": [
    {
      "id": 101,
      "name": "小隐咖啡",
      "category": "cafe",
      "latitude": 39.9895,
      "longitude": 116.3305,
      "distance_km": 0.5,
      "rating": 4.7,
      "price_level": 2,
      "tags": ["安静", "独立", "有wifi", "插座多"],
      "address": "五道口华清嘉园15号楼1层",
      "description": "独立咖啡馆，环境安静，适合学习工作"
    },
    {
      "id": 102,
      "name": "时光书店咖啡",
      "category": "cafe",
      "latitude": 39.9910,
      "longitude": 116.3280,
      "distance_km": 0.8,
      "rating": 4.6,
      "price_level": 2,
      "tags": ["安静", "独立", "有wifi", "书店"],
      "address": "五道口城铁站西侧200米",
      "description": "书店+咖啡馆，文艺氛围浓厚"
    },
    {
      "id": 103,
      "name": "漫咖啡五道口店",
      "category": "cafe",
      "latitude": 39.9870,
      "longitude": 116.3320,
      "distance_km": 1.2,
      "rating": 4.4,
      "price_level": 2,
      "tags": ["安静", "连锁", "有wifi", "网红"],
      "address": "五道口购物中心3层",
      "description": "连锁咖啡品牌，装修网红风"
    },
    {
      "id": 104,
      "name": "星巴克五道口店",
      "category": "cafe",
      "latitude": 39.9880,
      "longitude": 116.3290,
      "distance_km": 0.3,
      "rating": 4.5,
      "price_level": 3,
      "tags": ["连锁", "有wifi"],
      "address": "五道口购物中心1层",
      "description": "连锁咖啡品牌"
    }
  ],
  "total_count": 4,
  "empty_result": false
}
```

**说明:**
- 找到 4 个候选咖啡馆
- 星巴克因为 price_level=3 超出预算，但距离很近所以也被检索出来
- 漫咖啡虽然是连锁，但满足"安静"标签

---

#### Step 4: 对候选 POI 进行排序

**Tool Call:**
```python
rank_candidate_pois(
    candidates=[...],  # 上一步的候选列表
    user_preferences={
        "stable_preferences": [...],
        "recent_preferences": [...],
        "negative_preferences": [...]
    },
    intent={"poi_type": "cafe"},
    top_k=3
)
```

**返回:**
```json
{
  "ranked_results": [
    {
      "poi": {
        "id": 101,
        "name": "小隐咖啡",
        "distance_km": 0.5,
        "rating": 4.7,
        "price_level": 2,
        "tags": ["安静", "独立", "有wifi", "插座多"],
        "address": "五道口华清嘉园15号楼1层",
        "description": "独立咖啡馆，环境安静，适合学习工作"
      },
      "total_score": 0.8125,
      "score_breakdown": {
        "rating_score": 0.94,
        "distance_score": 0.67,
        "stable_preference_score": 0.90,
        "recent_preference_score": 0.60,
        "negative_penalty": 0.0
      },
      "matched_preferences": {
        "stable": ["安静", "独立"],
        "recent": ["有wifi", "插座多"],
        "negative": []
      }
    },
    {
      "poi": {
        "id": 102,
        "name": "时光书店咖啡",
        "distance_km": 0.8,
        "rating": 4.6,
        "price_level": 2,
        "tags": ["安静", "独立", "有wifi", "书店"],
        "address": "五道口城铁站西侧200米",
        "description": "书店+咖啡馆，文艺氛围浓厚"
      },
      "total_score": 0.7580,
      "score_breakdown": {
        "rating_score": 0.92,
        "distance_score": 0.56,
        "stable_preference_score": 0.90,
        "recent_preference_score": 0.30,
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
        "id": 103,
        "name": "漫咖啡五道口店",
        "distance_km": 1.2,
        "rating": 4.4,
        "price_level": 2,
        "tags": ["安静", "连锁", "有wifi", "网红"],
        "address": "五道口购物中心3层",
        "description": "连锁咖啡品牌，装修网红风"
      },
      "total_score": 0.5890,
      "score_breakdown": {
        "rating_score": 0.88,
        "distance_score": 0.45,
        "stable_preference_score": 0.45,
        "recent_preference_score": 0.30,
        "negative_penalty": 0.30
      },
      "matched_preferences": {
        "stable": ["安静"],
        "recent": ["有wifi"],
        "negative": ["连锁"]
      }
    }
  ],
  "total_candidates": 4
}
```

**排序分析:**
1. **小隐咖啡 (0.8125)**: 完美匹配所有偏好，距离适中，评分高
2. **时光书店咖啡 (0.7580)**: 匹配稳定偏好，但缺少"插座多"
3. **漫咖啡 (0.5890)**: 虽然安静，但因为是连锁和网红店被扣分

---

#### Step 5: 保存推荐日志

**Tool Call:**
```python
save_recommendation_log(
    session_id="session_20260430_001",
    user_id="user_zhangsan",
    ranked_results=[...]  # 上一步的排序结果
)
```

**返回:**
```json
{
  "success": true,
  "saved_count": 3
}
```

---

#### Agent 呈现给用户

```
根据您的需求，为您推荐以下咖啡馆：

🥇 小隐咖啡 (综合评分 0.81)
📍 五道口华清嘉园15号楼1层 (距离 0.5km)
⭐ 评分 4.7 | 💰 人均 ¥30-50
✨ 推荐理由：
   - 完美匹配您的偏好：安静、独立咖啡馆
   - 有 wifi 和充足插座，适合写论文
   - 距离适中，环境安静

🥈 时光书店咖啡 (综合评分 0.76)
📍 五道口城铁站西侧200米 (距离 0.8km)
⭐ 评分 4.6 | 💰 人均 ¥30-50
✨ 推荐理由：
   - 符合您喜欢的安静、独立咖啡馆
   - 书店氛围，文艺气息浓厚
   - 有 wifi，适合长时间学习

🥉 漫咖啡五道口店 (综合评分 0.59)
📍 五道口购物中心3层 (距离 1.2km)
⭐ 评分 4.4 | 💰 人均 ¥30-50
⚠️ 注意：这是连锁咖啡馆，可能不如前两家安静
```

---

### 第二轮：反馈处理

#### 用户反馈

```
不要这种网红店，我想要更安静一点。
```

**Agent 理解:**
- 用户对第3个推荐（漫咖啡）不满意
- 原因：网红店、不够安静
- 反馈类型：negative

---

#### Step 6: 根据反馈更新偏好

**Tool Call:**
```python
update_preference_from_feedback(
    user_id="user_zhangsan",
    poi_id=103,  # 漫咖啡
    feedback_type="negative",
    feedback_details={
        "reason": "网红店，不够安静"
    }
)
```

**返回:**
```json
{
  "success": true,
  "updated_preferences": [
    {
      "tag": "安静",
      "action": "increased",
      "old_weight": 0.85,
      "new_weight": 0.95
    },
    {
      "tag": "连锁",
      "action": "decreased",
      "old_weight": 0.25,
      "new_weight": 0.1
    },
    {
      "tag": "网红",
      "action": "created_negative",
      "new_weight": 0.2
    }
  ],
  "evidence": "用户对 漫咖啡五道口店 给予负向反馈",
  "source": "negative_feedback",
  "timestamp": "2026-04-30 09:53:46"
}
```

**偏好更新说明:**
- "安静"标签权重提升：0.85 → 0.95（更强调安静）
- "连锁"标签权重降低：0.25 → 0.1（更不喜欢连锁）
- "网红"标签新增为负向偏好：0.2（不喜欢网红店）

---

#### Agent 回复用户

```
✅ 已更新您的偏好：

📈 更加重视：
   - 安静环境 (权重 0.85 → 0.95)

📉 降低偏好：
   - 连锁咖啡馆 (权重 0.25 → 0.1)
   - 网红店 (新增负向偏好)

下次推荐时会更加注重安静、独立的咖啡馆，避免网红店。

基于更新后的偏好，我建议您选择：
🎯 小隐咖啡 或 时光书店咖啡
这两家都是独立咖啡馆，环境安静，非常适合写论文。
```

---

## 完整流程总结

```
用户查询
    ↓
[1] parse_and_save_session_intent
    → 解析：五道口、咖啡馆、安静、预算低
    ↓
[2] retrieve_user_preference_memory
    → 获取：喜欢安静/独立，不喜欢连锁
    ↓
[3] retrieve_candidate_pois
    → 检索：4个候选咖啡馆
    ↓
[4] rank_candidate_pois
    → 排序：小隐咖啡 > 时光书店 > 漫咖啡
    ↓
[5] save_recommendation_log
    → 保存：推荐日志
    ↓
返回推荐结果
    ↓
用户反馈："不要网红店"
    ↓
[6] update_preference_from_feedback
    → 更新：降低连锁/网红权重，提升安静权重
    ↓
确认偏好已更新
```

---

## 关键特性展示

### 1. 可解释性
每个推荐都有明确的评分构成：
- 评分分数：基于用户评价
- 距离分数：基于地理位置
- 偏好匹配：基于历史行为
- 负向惩罚：基于不喜欢的特征

### 2. 可追溯性
所有偏好更新都记录：
- evidence: 更新原因
- source: 更新来源
- timestamp: 更新时间
- old_weight / new_weight: 权重变化

### 3. 个性化
- 冷启动：基于评分和距离
- 有历史：结合稳定偏好和近期偏好
- 持续学习：根据反馈不断优化

### 4. 透明度
用户可以清楚看到：
- 为什么推荐这个 POI
- 匹配了哪些偏好
- 分数是如何计算的
- 偏好如何被更新
