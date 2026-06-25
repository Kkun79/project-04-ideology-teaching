"""
AI 服务模块 - 提供研学规划、情景剧编写、演讲稿撰写等 AI 生成功能。
本模块提供本地模拟实现，也可接入真实大模型 API。
"""
import json
import random
from datetime import datetime
from typing import Optional

# 当需要真实 API 时，可在此配置
# API_KEY = os.getenv("OPENAI_API_KEY", "")
# API_URL = "https://api.openai.com/v1/chat/completions"


def _simulate_study_plan(destination: str, duration: str, theme: str) -> dict:
    """模拟生成研学方案"""
    plans = {
        "红色": {
            "title": f"{destination}红色研学之旅",
            "itinerary": (
                f"第1天：抵达{destination}，开营仪式，参观红色纪念馆\n"
                f"第2天：实地走访革命旧址，聆听专题讲座《{theme}》\n"
                f"第3天：分组研讨，撰写研学报告，结营汇报"
            ),
            "objectives": f"通过实地走访{destination}红色教育基地，深入了解{theme}的历史背景与时代价值，"
                          "培养学生的爱国情怀和理想信念。",
            "budget": "交通、食宿、门票、保险等预计人均 800-1500 元（视具体行程调整）",
        },
        "传统文化": {
            "title": f"{destination}传统文化研学之旅",
            "itinerary": (
                f"第1天：抵达{destination}，参观博物馆、非遗展示中心\n"
                f"第2天：体验传统手工艺，文化讲座《{theme}》\n"
                f"第3天：成果展示，交流分享，返程"
            ),
            "objectives": f"通过沉浸式体验{destination}传统文化资源，加深对{theme}的理解与认同。",
            "budget": "交通、食宿、体验项目等预计人均 600-1200 元",
        },
        "改革开放": {
            "title": f"{destination}改革开放发展成就研学",
            "itinerary": (
                f"第1天：抵达{destination}，参观改革开放展览馆\n"
                f"第2天：走访高新技术企业/自贸区，专题研讨《{theme}》\n"
                f"第3天：分组成果汇报，返程"
            ),
            "objectives": f"实地感受{destination}改革开放以来的巨大变化，深刻理解{theme}的伟大意义。",
            "budget": "交通、食宿、企业参访等预计人均 1000-2000 元",
        },
    }
    default = {
        "title": f"{destination}研学方案",
        "itinerary": f"第1天：抵达{destination}，开营仪式\n第2天：主题学习与实地考察\n第3天：总结汇报，返程",
        "objectives": f"通过{destination}研学活动，深化对{theme}的认识。",
        "budget": "根据实际情况核算",
    }
    plan = plans.get(theme, default)
    plan["destination"] = destination
    plan["duration"] = duration
    plan["theme"] = theme
    plan["notes"] = "（AI 生成方案，建议结合实际情况调整）"
    plan["ai_generated"] = True
    return plan


def _simulate_script(script_type: str, theme: str, characters: str = "") -> dict:
    """模拟生成情景剧或演讲稿"""
    if script_type == "情景剧":
        outlines = {
            "红色家书": {
                "characters": "爷爷（老革命）、孙子（大学生）、旁白",
                "content": (
                    "【场景：家中书房，孙子整理旧物时发现一箱信件】\n\n"
                    "孙子：（拿起一封信）爷爷，这些信是……？\n\n"
                    "爷爷：（缓缓坐下）那是你曾祖父写给我的家书……\n\n"
                    "旁白：烽火连三月，家书抵万金。这些泛黄的信纸，"
                    "承载着一段波澜壮阔的历史。\n\n"
                    "【灯光渐暗，投影展示历史画面】\n\n"
                    "爷爷：你的曾祖父当年离家参加革命时，"
                    "你奶奶才刚刚怀上我。他在信中写道……\n\n"
                    "孙子：（念信）'吾儿亲启：若他日你读到这封信，'\n"
                    "父亲或许已不在人世。但请你记住，父亲是为千千万万"
                    "人的幸福而战，此生无憾。\n\n"
                    "【音乐起，全场肃穆】\n\n"
                    "孙子：（眼含热泪）爷爷，我懂了。这不仅是家书，"
                    "更是一个时代的信仰。"
                ),
            },
            "青春奋斗": {
                "characters": "小陈（大学生）、导师、同学甲、乙",
                "content": (
                    "【场景：大学实验室，深夜】\n\n"
                    "小陈：（盯着屏幕叹气）还是不对……已经失败二十次了。\n\n"
                    "同学甲：放弃吧，这个课题太难了。\n\n"
                    "小陈：不，老师说科研就是九十九次失败换一次成功。\n\n"
                    "【导师走进来】\n\n"
                    "导师：还在？很好。你知道吗，当年我们的前辈在"
                    "那么艰苦的条件下都能造出两弹一星，这点困难算什么？\n\n"
                    "小陈：老师，我明白了。青春就是用来奋斗的！\n\n"
                    "【三个月后，实验成功，全场欢呼】\n\n"
                    "旁白：青春由磨砺而出彩，人生因奋斗而升华。"
                ),
            },
        }
        script = outlines.get(theme, {
            "characters": "角色A、角色B、旁白",
            "content": f"【场景：舞台中央】\n\n（{theme}主题情景剧）\n\n角色A：……\n角色B：……\n\n旁白：……",
        })
        if characters:
            script["characters"] = characters
        script["type"] = "情景剧"
    else:
        speeches = {
            "中国梦": (
                "尊敬的老师们，亲爱的同学们：\n\n"
                "大家好！今天我演讲的题目是《以青春之我，筑中国梦》。\n\n"
                "中国梦，是中华民族伟大复兴的梦想，是每一个中国人的梦想。"
                "回望历史，从鸦片战争到新中国成立，从改革开放到新时代，"
                "中华民族走过了漫漫长夜，迎来了伟大复兴的曙光。\n\n"
                "作为新时代的青年，我们生逢其时，重任在肩。"
                "我们应当把个人的理想追求融入国家和民族的事业中，"
                "用青春和汗水书写无愧于时代的华彩篇章。\n\n"
                "同学们，让我们以青春之我、奋斗之我，"
                "为实现中华民族伟大复兴的中国梦贡献力量！\n\n"
                "谢谢大家！"
            ),
            "爱国主义": (
                "尊敬的老师，亲爱的同学们：\n\n"
                "今天我演讲的题目是《爱国，是青春最亮丽的底色》。\n\n"
                "爱国，是人世间最深层、最持久的情感。"
                "从屈原的虽九死其犹未悔，到林则徐的苟利国家生死以，"
                "从周恩来的为中华之崛起而读书，到钱学森的毅然归国，"
                "一代代中华儿女用行动诠释着爱国的真谛。\n\n"
                "爱国不是空洞的口号，而是实实在在的行动。"
                "它可以是课堂上的刻苦钻研，可以是实验室里的精益求精，"
                "可以是志愿服务中的默默奉献。\n\n"
                "让我们把爱国之情化为报国之行，用奋斗书写最美的青春！\n\n"
                "谢谢大家！"
            ),
        }
        speech = speeches.get(theme, (
            f"尊敬的老师，亲爱的同学们：\n\n"
            f"大家好！今天我演讲的主题是《{theme}》。\n\n"
            f"……（此处为AI生成的演讲稿内容，建议进一步润色和完善）……\n\n"
            f"谢谢大家！"
        ))
        script = {
            "type": "演讲稿",
            "characters": "",
            "content": speech,
        }

    script["title"] = theme
    script["theme"] = theme
    script["notes"] = "（AI 生成内容，建议根据实际需要修改完善）"
    script["ai_generated"] = True
    return script


def generate_study_plan(destination: str, duration: str, theme: str) -> dict:
    """生成研学方案 - API版可替换为真实大模型调用"""
    return _simulate_study_plan(destination, duration, theme)


def generate_script(script_type: str, theme: str, characters: str = "") -> dict:
    """生成情景剧或演讲稿 - API版可替换为真实大模型调用"""
    return _simulate_script(script_type, theme, characters)
