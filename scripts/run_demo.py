"""
模拟完整的 MCP-MemPOI 推荐流程

演示场景：
用户："我今天下午想在五道口附近找一个安静、适合写论文的咖啡馆，预算别太高。"
后续反馈："不要这种网红店，我想要更安静一点。"
"""

import sys
import os
import json
from datetime import datetime

# 设置 UTF-8 输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.session_tools import parse_and_save_session_intent
from tools.memory_tools import retrieve_user_preference_memory
from tools.poi_tools import retrieve_candidate_pois
from tools.ranking_tools import rank_candidate_pois
from tools.feedback_tools import save_recommendation_log, update_preference_from_feedback


def print_section(title):
    """打印分隔线"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_poi(poi, rank=None):
    """格式化打印 POI 信息"""
    prefix = f"🥇 " if rank == 1 else f"🥈 " if rank == 2 else f"🥉 " if rank == 3 else ""
    print(f"{prefix}{poi['name']}")
    print(f"📍 {poi.get('address', 'N/A')} (距离 {poi['distance_km']}km)")
    print(f"⭐ 评分 {poi['rating']} | 💰 价格等级 {poi.get('price_level', 'N/A')}/4")
    print(f"🏷️  标签: {', '.join(poi.get('tags', []))}")
    if poi.get('description'):
        print(f"📝 {poi['description']}")


def run_demo():
    """运行完整演示流程"""

    # 用户信息
    user_id = "user_zhangsan"
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print_section("场景设定")
    print("用户: 张三，研究生，经常需要找地方写论文")
    print("查询: 我今天下午想在五道口附近找一个安静、适合写论文的咖啡馆，预算别太高。")

    # 准备：确保用户存在
    print_section("准备：创建测试用户")
    import sqlite3
    conn = sqlite3.connect("database/mempoi.sqlite")
    cursor = conn.cursor()

    # 检查用户是否存在
    cursor.execute("SELECT user_id FROM user_profile WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO user_profile (user_id, name, preferences)
            VALUES (?, ?, ?)
        """, (user_id, "张三", "{}"))
        conn.commit()
        print(f"✓ 创建测试用户: {user_id}")
    else:
        print(f"✓ 测试用户已存在: {user_id}")

    conn.close()

    # ========== 第一轮：推荐生成 ==========

    # Step 1: 解析并保存会话意图
    print_section("Step 1: 解析并保存会话意图")

    raw_query = "我今天下午想在五道口附近找一个安静、适合写论文的咖啡馆，预算别太高。"
    parsed_intent = {
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

    result1 = parse_and_save_session_intent(
        user_id=user_id,
        session_id=session_id,
        raw_query=raw_query,
        parsed_intent=parsed_intent
    )

    if not result1.get('success'):
        print(f"✗ 会话创建失败: {result1.get('error', 'Unknown error')}")
        return

    print(f"✓ 会话创建成功: {result1['session_id']}")
    print(f"  POI 类型: {result1['intent']['poi_type']}")
    print(f"  位置: 五道口 ({result1['intent']['location']['latitude']}, {result1['intent']['location']['longitude']})")
    print(f"  场景: {result1['intent']['scenario']}")
    print(f"  约束: 距离 {result1['intent']['constraints']['max_distance_km']}km, "
          f"价格等级 {result1['intent']['constraints']['price_level']}, "
          f"标签 {result1['intent']['constraints']['tags']}")

    # Step 2: 检索用户偏好记忆
    print_section("Step 2: 检索用户偏好记忆")

    result2 = retrieve_user_preference_memory(
        user_id=user_id,
        intent={"poi_type": "cafe"}
    )

    print(f"稳定偏好 ({len(result2['stable_preferences'])} 条):")
    for pref in result2['stable_preferences']:
        print(f"  - {pref['keywords']} (权重 {pref['weight']})")

    print(f"\n近期偏好 ({len(result2['recent_preferences'])} 条):")
    for pref in result2['recent_preferences']:
        print(f"  - {pref['keywords']} (权重 {pref['weight']})")

    print(f"\n负向偏好 ({len(result2['negative_preferences'])} 条):")
    for pref in result2['negative_preferences']:
        print(f"  - {pref['keywords']} (权重 {pref['weight']})")

    if result2['default_memory']:
        print("\n⚠️  冷启动用户（无历史偏好）")

    # Step 3: 检索候选 POI
    print_section("Step 3: 检索候选 POI")

    result3 = retrieve_candidate_pois(
        location=parsed_intent["location"],
        poi_type=parsed_intent["poi_type"],
        constraints=parsed_intent["constraints"],
        top_k=20
    )

    print(f"找到 {result3['total_count']} 个候选咖啡馆:\n")
    for i, poi in enumerate(result3['candidates'], 1):
        print(f"{i}. {poi['name']} - {poi['distance_km']}km, 评分 {poi['rating']}")

    if result3['empty_result']:
        print("⚠️  未找到符合条件的候选")
        return

    # Step 4: 对候选 POI 进行排序
    print_section("Step 4: 对候选 POI 进行排序")

    result4 = rank_candidate_pois(
        candidates=result3['candidates'],
        user_preferences=result2,
        intent=parsed_intent,
        top_k=3
    )

    print(f"Top-{len(result4['ranked_results'])} 推荐结果:\n")

    for i, item in enumerate(result4['ranked_results'], 1):
        poi = item['poi']
        score = item['total_score']
        breakdown = item['score_breakdown']
        matched = item['matched_preferences']

        print_poi(poi, rank=i)
        print(f"📊 综合评分: {score:.4f}")
        print(f"   - 评分分数: {breakdown['rating_score']:.2f}")
        print(f"   - 距离分数: {breakdown['distance_score']:.2f}")
        print(f"   - 稳定偏好: {breakdown['stable_preference_score']:.2f}")
        print(f"   - 近期偏好: {breakdown['recent_preference_score']:.2f}")
        print(f"   - 负向惩罚: {breakdown['negative_penalty']:.2f}")

        if matched['stable']:
            print(f"✨ 匹配稳定偏好: {', '.join(matched['stable'])}")
        if matched['recent']:
            print(f"✨ 匹配近期偏好: {', '.join(matched['recent'])}")
        if matched['negative']:
            print(f"⚠️  匹配负向偏好: {', '.join(matched['negative'])}")

        print()

    # Step 5: 保存推荐日志
    print_section("Step 5: 保存推荐日志")

    result5 = save_recommendation_log(
        session_id=session_id,
        user_id=user_id,
        ranked_results=result4['ranked_results']
    )

    print(f"✓ 推荐日志保存成功: {result5['saved_count']} 条记录")

    # ========== 第二轮：反馈处理 ==========

    print_section("用户反馈")
    print("用户: 不要这种网红店，我想要更安静一点。")
    print("(针对第3个推荐)")

    # Step 6: 根据反馈更新偏好
    print_section("Step 6: 根据反馈更新偏好")

    # 假设用户对第3个推荐（如果存在）给予负向反馈
    if len(result4['ranked_results']) >= 3:
        feedback_poi_id = result4['ranked_results'][2]['poi']['id']

        result6 = update_preference_from_feedback(
            user_id=user_id,
            poi_id=feedback_poi_id,
            feedback_type="negative",
            feedback_details={
                "reason": "网红店，不够安静"
            }
        )

        if result6['success']:
            print(f"✓ 偏好更新成功")
            print(f"  证据: {result6['evidence']}")
            print(f"  来源: {result6['source']}")
            print(f"  时间: {result6['timestamp']}\n")

            print(f"更新的偏好 ({len(result6['updated_preferences'])} 条):")
            for update in result6['updated_preferences']:
                tag = update['tag']
                action = update['action']

                if action == 'increased':
                    print(f"  📈 {tag}: {update['old_weight']:.2f} → {update['new_weight']:.2f} (提升)")
                elif action == 'decreased':
                    print(f"  📉 {tag}: {update['old_weight']:.2f} → {update['new_weight']:.2f} (降低)")
                elif action == 'created':
                    print(f"  ✨ {tag}: 新建正向偏好 (权重 {update['new_weight']:.2f})")
                elif action == 'created_negative':
                    print(f"  ⚠️  {tag}: 新建负向偏好 (权重 {update['new_weight']:.2f})")
        else:
            print(f"✗ 偏好更新失败: {result6.get('error', 'Unknown error')}")
    else:
        print("⚠️  推荐结果少于3个，跳过反馈演示")

    # 总结
    print_section("演示完成")
    print("✓ 完整流程演示成功")
    print(f"  会话ID: {session_id}")
    print(f"  用户ID: {user_id}")
    print(f"  推荐数量: {len(result4['ranked_results'])}")
    print(f"  日志记录: {result5['saved_count']} 条")
    print("\n推荐:")
    for i, item in enumerate(result4['ranked_results'], 1):
        print(f"  {i}. {item['poi']['name']} (评分 {item['total_score']:.4f})")


if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
