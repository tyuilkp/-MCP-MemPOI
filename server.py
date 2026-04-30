"""
MCP-MemPOI Server

基于 FastMCP 的 POI 推荐系统服务器
"""

from fastmcp import FastMCP
from typing import Optional, List, Dict

# 导入工具函数
from tools.session_tools import parse_and_save_session_intent
from tools.memory_tools import retrieve_user_preference_memory
from tools.poi_tools import retrieve_candidate_pois
from tools.ranking_tools import rank_candidate_pois
from tools.feedback_tools import save_recommendation_log, update_preference_from_feedback

# 创建 FastMCP 服务器
mcp = FastMCP(
    "mempoi",
    instructions="""MCP-MemPOI 是一个基于记忆的 POI（兴趣点）推荐系统。

## 核心能力
1. **会话管理**: 解析并保存用户查询意图（位置、POI类型、约束条件）
2. **偏好记忆**: 检索用户的稳定偏好、近期偏好和负向偏好
3. **候选检索**: 根据位置、类型和约束条件检索候选 POI
4. **智能排序**: 使用可解释规则对候选进行打分排序（评分30% + 距离25% + 稳定偏好25% + 近期偏好15% - 负向惩罚5%）
5. **推荐日志**: 保存推荐结果用于后续分析
6. **偏好更新**: 根据用户反馈（positive/negative/correction）更新偏好记忆

## 典型工作流程
1. 使用 `parse_and_save_session_intent` 解析用户查询
2. 使用 `retrieve_user_preference_memory` 获取用户历史偏好
3. 使用 `retrieve_candidate_pois` 检索候选 POI
4. 使用 `rank_candidate_pois` 对候选进行排序
5. 使用 `save_recommendation_log` 保存推荐结果
6. 根据用户反馈使用 `update_preference_from_feedback` 更新偏好

## 支持的 POI 类型
- cafe: 咖啡馆
- restaurant: 餐厅
- attraction: 景点

## 特点
- 所有偏好更新都有完整的 evidence、source 和 timestamp 追溯
- 排序算法完全可解释，无黑盒模型
- 支持冷启动用户（无历史偏好时基于评分和距离推荐）
- 不删除历史记忆，只追加或降权"""
)

# 1. 会话意图解析工具
@mcp.tool()
def parse_and_save_session_intent(
    user_id: str,
    session_id: str,
    raw_query: str,
    parsed_intent: dict
) -> dict:
    """解析并保存会话意图

    将用户的原始查询解析为结构化意图并保存到数据库。

    Args:
        user_id: 用户ID
        session_id: 会话ID
        raw_query: 用户原始查询文本
        parsed_intent: 解析后的意图，必须包含:
            - poi_type: POI类型 (cafe/restaurant/attraction)
            - location: 位置信息 (包含 latitude 和 longitude)
            - scenario: 使用场景
            - constraints: 约束条件 (可包含 max_distance_km, price_level)

    Returns:
        成功: {success: True, session_id: str, intent: dict}
        失败: {success: False, error: str}
    """
    return parse_and_save_session_intent(user_id, session_id, raw_query, parsed_intent)


# 2. 用户偏好记忆检索工具
@mcp.tool()
def retrieve_user_preference_memory(
    user_id: str,
    intent: dict
) -> dict:
    """检索用户偏好记忆

    根据用户ID和当前意图检索历史偏好记忆，包括稳定偏好、近期偏好和负向偏好。

    Args:
        user_id: 用户ID
        intent: 当前意图，必须包含 poi_type 字段

    Returns:
        {
            stable_preferences: List[dict],  # 稳定的长期偏好 (weight >= 0.7)
            recent_preferences: List[dict],  # 近期偏好 (0.3 <= weight < 0.7)
            negative_preferences: List[dict], # 负向偏好 (weight < 0.3)
            default_memory: bool  # 是否为默认记忆（无历史偏好）
        }
    """
    return retrieve_user_preference_memory(user_id, intent)


# 3. 候选POI检索工具
@mcp.tool()
def retrieve_candidate_pois(
    location: dict,
    poi_type: str,
    constraints: dict,
    top_k: int = 20
) -> dict:
    """检索候选POI

    根据位置、类型和约束条件从数据库检索候选POI列表。

    Args:
        location: 位置信息，包含 latitude 和 longitude
        poi_type: POI类型 (cafe/restaurant/attraction)
        constraints: 约束条件，可包含:
            - max_distance_km: 最大距离（公里）
            - price_level: 价格等级 (1-4)
            - tags: 必需标签列表
        top_k: 返回数量限制，默认20

    Returns:
        {
            candidates: List[dict],  # 候选POI列表
            total_count: int,        # 候选总数
            empty_result: bool       # 是否为空结果
        }
    """
    return retrieve_candidate_pois(location, poi_type, constraints, top_k)


# 4. POI排序工具
@mcp.tool()
def rank_candidate_pois(
    candidates: List[dict],
    user_preferences: dict,
    intent: dict,
    top_k: int = 5
) -> dict:
    """对候选POI进行排序

    使用可解释的规则对候选POI进行打分和排序。评分规则：
    - 评分分数 30%
    - 距离分数 25%
    - 稳定偏好匹配 25%
    - 近期偏好匹配 15%
    - 负向偏好惩罚 5%

    Args:
        candidates: 候选POI列表
        user_preferences: 用户偏好，包含:
            - stable_preferences: 稳定偏好列表
            - recent_preferences: 近期偏好列表
            - negative_preferences: 负向偏好列表
        intent: 当前意图
        top_k: 返回Top-K结果，默认5

    Returns:
        {
            ranked_results: List[dict],  # 排序后的结果，每项包含:
                                         # - poi: POI信息
                                         # - total_score: 总分
                                         # - score_breakdown: 分项分数
                                         # - matched_preferences: 匹配的偏好
            total_candidates: int        # 候选总数
        }
    """
    return rank_candidate_pois(candidates, user_preferences, intent, top_k)


# 5. 推荐日志保存工具
@mcp.tool()
def save_recommendation_log(
    session_id: str,
    user_id: str,
    ranked_results: List[dict]
) -> dict:
    """保存推荐日志

    将推荐结果保存到数据库，用于后续分析和反馈处理。

    Args:
        session_id: 会话ID
        user_id: 用户ID
        ranked_results: 排序后的推荐结果列表，每项包含:
            - poi: POI信息
            - total_score: 总分
            - score_breakdown: 分项分数
            - matched_preferences: 匹配的偏好

    Returns:
        {
            success: bool,      # 是否成功
            saved_count: int    # 保存的记录数
        }
    """
    return save_recommendation_log(session_id, user_id, ranked_results)


# 6. 偏好更新工具
@mcp.tool()
def update_preference_from_feedback(
    user_id: str,
    poi_id: int,
    feedback_type: str,
    feedback_details: Optional[dict] = None
) -> dict:
    """根据反馈更新用户偏好

    根据用户对POI的反馈更新偏好记忆。所有更新都会记录evidence、source和timestamp。

    Args:
        user_id: 用户ID
        poi_id: POI ID
        feedback_type: 反馈类型，必须是以下之一:
            - positive: 正向反馈，提升相关标签权重
            - negative: 负向反馈，降低相关标签权重
            - correction: 修正反馈，根据用户提供的修正标签更新偏好
        feedback_details: 可选，反馈详情，可包含:
            - corrected_tags: 修正后的标签（用于correction类型）
            - reason: 反馈原因

    Returns:
        {
            success: bool,                    # 是否成功
            updated_preferences: List[dict],  # 更新的偏好列表
            evidence: str,                    # 更新证据
            source: str,                      # 更新来源
            timestamp: str                    # 更新时间戳
        }
    """
    return update_preference_from_feedback(user_id, poi_id, feedback_type, feedback_details)


if __name__ == "__main__":
    # 运行服务器
    mcp.run()
