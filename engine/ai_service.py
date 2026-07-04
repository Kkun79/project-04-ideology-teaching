"""
AI 服务模块 - 提供研学规划、情景剧编写、演讲稿撰写等 AI 生成功能。
支持真实大模型 API（兼容 OpenAI 接口格式）和本地模拟回退。

环境变量配置：
OPENAI_API_KEY   - API 密钥（必填才启用真实 API）
OPENAI_API_BASE  - API 端点地址，默认 https://api.openai.com/v1
                    可改为其他兼容接口（如 DeepSeek、通义千问等）
OPENAI_MODEL     - 模型名，默认 gpt-4o-mini

未配置 API Key 时自动使用本地模拟方案。
"""
import json
import os
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional
import random
from datetime import datetime


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError as exc:
        print(f"[AI Service] local env load failed ({type(exc).__name__}): {exc}")


_load_local_env()

# API 配置
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")
API_BASE = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1").rstrip("/")
API_MODEL = os.getenv("OPENAI_MODEL", "deepseek-chat")
_HAS_API = bool(API_KEY)


def _call_llm(
    messages: list,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> Optional[str]:
    if not _HAS_API:
        return None

    body = {
        "model": API_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        f"{API_BASE}/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, OSError) as e:
        print(f"[AI Service] API 调用失败 ({type(e).__name__}): {e}")
        return None


def _llm_json(messages: list, temperature: float = 0.7) -> Optional[dict]:
    result = _call_llm(messages, temperature=temperature, max_tokens=2048)
    if not result:
        return None
    cleaned = result.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned[3:]
        cleaned = cleaned.rsplit("```", 1)[0].strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return None


def _simulate_study_plan(destination: str, duration: str, theme: str) -> dict:
    """模拟生成研学方案"""
    plans = {
        "红色": {
        "title": f"{destination}红色研学之旅",
        "target_grade": "大一至大三（本科生）",
        "related_courses": ["中国近现代史纲要", "毛泽东思想和中国特色社会主义理论体系概论", "思想道德与法治"],
        "core_competencies": "政治认同、科学精神、法治意识、公共参与",
        "itinerary": (
            f"第1天：抵达{destination}，开营仪式，参观红色纪念馆\n"
            f"第2天：实地走访革命旧址，聆听专题讲座《{theme}》\n"
            f"第3天：分组研讨，撰写研学报告，结营汇报\n"
            f"第4天：成果展示、交流分享、返程"
        ),
        "preparation": f"1. 行前阅读：了解{theme}历史背景和{destination}革命史\n2. 物资准备：笔记本、录音笔、相机、急救包\n3. 分组安排：每5人为一组，设组长、记录员、摄影师各一名\n4. 背景学习：提前观看《{theme}》纪录片一小时\n5. 安全动员：出发前进行安全教育与纪律宣讲",
        "tasks": f"1. 每日研学日志：每人每天撰写不少于300字的研学日志\n2. 小组课题：每组自选1个与{theme}相关的研究课题\n3. 口述史访谈：采访1位当地见证人或后人\n4. 影像记录：每组完成一个5分钟短视频短片\n5. 结营汇报：制作PPT并做10分钟小组汇报",
        "evaluation": f"1. 过程评价（60%）：每日日志质量、团队协作、任务完成度\n2. 成果评价（40%）：研学报告、汇报展示、影像作品\n3. 自评与互评：每位学生提交个人总结\n4. 教师评语：带队教师根据全程表现给出综合性评语",
        "safety": "1. 购买人身意外保险和医疗保险\n2. 每15人配备1名带队教师\n3. 每日清点人数并报告出行状况\n4. 随队携带急救药品并指定安全员\n5. 提前了解目的地急救资源分布",
        "expected_outcomes": f"1. 完成一份不少于3000字的主题研学报告\n2. 产出5分钟纪实短视频\n3. 收集不少于20张原始照片并整理为影集\n4. 在校内举办一次研学成果展或分享会",
        "resources": f"1. 推荐书目：《{theme}》专题读物、《中国共产党历史》\n2. 推荐影片：《{destination}》主题纪录片\n3. 网络资源：学习强国平台{destination}专题\n4. 实地资源：{destination}纪念馆、旧址群、历史陈列",
        "objectives": f"通过实地走访{destination}红色教育基地，深入了解{theme}的历史背景与时代价值，"
                        "培养学生的爱国情怀和理想信念。",
        "budget": "交通、食宿、门票、保险等预计人均 800-1500 元（视具体行程调整）",
        },
        "传统文化": {
        "title": f"{destination}传统文化研学之旅",
        "target_grade": "大一至大四（本科生）",
        "related_courses": ["中国文化概论", "马克思主义基本原理", "思想道德与法治"],
        "core_competencies": "文化自信、科学精神、劳动意识、实践创新",
        "itinerary": (
            f"第1天：抵达{destination}，参观博物馆、非遗展示中心\n"
            f"第2天：体验传统手工艺，文化讲座《{theme}》\n"
            f"第3天：成果展示，交流分享，返程"
        ),
        "preparation": f"1. 查阅{destination}地方志和传统文化典籍\n2. 准备写生本、相机、录音笔\n3. 分组预研：每组掌握一项当地非遗技艺的背景",
        "tasks": f"1. 非遗体验日志\n2. 小组课题《{destination}传统文化保护与传承》\n3. 记录至少一项非遗技艺制作过程\n4. 结营展示非遗手作成果",
        "evaluation": f"1. 过程评价（60%）：参与度、体验日志质量\n2. 成果评价（40%）：课题报告、手作成品\n3. 互评+教师评语",
        "safety": "1. 购买旅行保险；2. 每15名学生至少1名带队教师；3. 每日安全巡查点名；4. 随队医药包备用",
        "expected_outcomes": f"1. 非遗技艺手作成品一件\n2. 传统文化调研报告（2000字以上）\n3. 体验日志合集\n4. 校园传统文化展示活动方案",
        "resources": f"1. 推荐书目：《中国传统文化概论》\n2. 影视：{destination}纪录片\n3. 线上：中国非遗数字博物馆\n4. 实地：{destination}博物馆、非遗工作室",
        "objectives": f"通过沉浸式体验{destination}传统文化资源，加深对{theme}的理解与认同。",
        "budget": "交通、食宿、体验项目等预计人均 600-1200 元",
        },
        "改革开放": {
        "title": f"{destination}改革开放发展成就研学",
        "target_grade": "大二至大四（本科生）",
        "related_courses": ["毛泽东思想和中国特色社会主义理论体系概论", "习近平新时代中国特色社会主义思想概论", "形势与政策"],
        "core_competencies": "政治认同、科学精神、法治意识、公共参与",
        "itinerary": (
            f"第1天：抵达{destination}，参观改革开放展览馆\n"
            f"第2天：走访高新技术企业/自贸区，专题研讨《{theme}》\n"
            f"第3天：分组成果汇报，返程"
        ),
        "preparation": f"1. 研读{destination}改革开放史相关资料\n2. 观看《{theme}》专题纪录片\n3. 准备访谈提纲和记录本\n4. 分工商定：组长、访谈员、记录员、素材采集",
        "tasks": f"1. 采访至少1位改革开放亲历者或企业家\n2. 小组课题：{destination}改革开放40年对比研究\n3. 每日观察笔记（200字以上）\n4. 创作一份新媒体图文作品（公众号/短视频）",
        "evaluation": f"1. 过程评价（50%）：参与度、访谈记录、观察笔记\n2. 成果评价（50%）：调研报告、新媒体作品\n3. 小组互评+教师评语",
        "safety": "1. 购买旅行保险；2. 每15人配备1名教师；3. 企业参访中遵守安全规范；4. 每日健康监测和点名",
        "expected_outcomes": f"1. 改革开放专题调研报告（3000字）\n2. 访谈记录合集\n3. 新媒体作品（公众号/短视频）\n4. 校内改革开放主题展览",
        "resources": f"1. 书籍：《改革开放口述史》、《{destination}发展纪实》\n2. 影视：《必由之路》、《我们走在大路上》\n3. 网络：{destination}政府官网、改革开放专题数据库\n4. 实地：{destination}展览馆、科技园、自贸区",
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
    plan.setdefault("target_grade", "大一至大三（本科生）")
    plan.setdefault("related_courses", ["中国近现代史纲要", "思想道德与法治"])
    plan.setdefault("core_competencies", "政治认同、科学精神")
    plan.setdefault("preparation", f"1. 行前阅读{theme}相关背景材料\n2. 准备笔记本和摄影设备\n3. 分组和教师带队安排")
    plan.setdefault("tasks", f"1. 每日撰写研学日志\n2. 小组课题《{destination}研学专题》\n3. 结营汇报展示")
    plan.setdefault("evaluation", "1. 过程评价（日志+参与度+协作）\n2. 成果评价（报告+展示）\n3. 自评与互评")
    plan.setdefault("safety", "1. 购买旅行保险\n2. 教师全程带队\n3. 每日点名和应急预案")
    plan.setdefault("expected_outcomes", "1. 研学报告\n2. 成果展示\n3. 影像记录")
    plan.setdefault("resources", f"推荐书籍和纪录片，{destination}纪念馆和线上资源")
    return plan


def _split_keywords(keywords: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,，、;；\s]+", keywords or "") if part.strip()]


LEADER_PROFILES = {
    "毛泽东": {
        "name": "毛泽东",
        "identity": "中国共产党、中国人民解放军和中华人民共和国的主要缔造者和领导人",
        "period": "新民主主义革命与社会主义建设时期",
        "keywords": ["人民立场", "实事求是", "独立自主", "艰苦奋斗", "调查研究"],
        "tone": "视野宏阔、善于从人民和实际出发，语言有力量但不空泛",
        "anchor": "把个人理想放到人民事业和中国实际中去检验。",
        "personality_analysis": {
            "temperament": "胸怀全局、善抓主要矛盾，谈青年问题时常把个人选择放到人民、国家和时代大势中考量。",
            "reasoning": "先问立场和实际，再问方法和行动；不满足于抽象表态，强调调查研究、独立思考和实践检验。",
            "voice": "有长者的坚定和鼓动性，句式可以有节奏感，但要避免口号堆砌和诗词化仿写。",
            "care": "面对迷茫时先肯定青年愿意思考，再把困惑引向人民立场、实际问题和长期奋斗。",
            "avoid": "不要编造具体讲话、私人回忆或过度使用领袖式标语。",
        },
        "fallback": {
            "ideal": [
                "同学，理想不能只放在心里，更要放到人民中间去检验。",
                "一个人的志向，只有同国家前途、民族命运连在一起，才会有真正的力量。",
                "你今天读书求知，也要问一问：这些本领将来能不能为人民解决问题，能不能推动中国向前走。",
            ],
            "difficulty": [
                "困难并不可怕。中国革命走过的路，从来不是一帆风顺的。",
                "关键是把情况弄清楚，知道矛盾在哪里，再用坚定的信念和科学的方法去解决。",
                "青年遇到挫折，不要只看一时得失，要在实践中锻炼自己。",
            ],
            "practice": [
                "课堂学习不能停在书本上。",
                "要把书本知识同社会实际结合起来，学会从真实问题出发思考。",
                "实事求是，就是既不空喊，也不盲从，而是从事实中找规律，从行动中见担当。",
            ],
            "general": [
                "不要把历史看成远处的故事。",
                "历史里的信念、方法和担当，都可以变成今天的行动。",
                "只要心里装着人民，脚下踩着实际，就能在自己的岗位上做出有价值的事情。",
            ],
        },
    },
    "邓小平": {
        "name": "邓小平",
        "identity": "中国社会主义改革开放和现代化建设的总设计师",
        "period": "改革开放和社会主义现代化建设新时期",
        "keywords": ["解放思想", "实事求是", "改革开放", "实践标准", "发展"],
        "tone": "务实、清醒、重视实践效果，鼓励敢闯敢试",
        "anchor": "把理想落实到解决实际问题和推动发展上。",
        "personality_analysis": {
            "temperament": "冷静务实、抓关键、重结果，面对青年问题时更关心能否从空想走向能力和成效。",
            "reasoning": "先破除思想包袱，再回到实践标准；鼓励试、改、再试，强调发展和解决问题。",
            "voice": "短句清楚、有判断力，不绕弯，不做空泛抒情，给出的建议要能执行、能检验。",
            "care": "面对焦虑时不渲染情绪，而是把问题拆小，鼓励在实践中找到答案。",
            "avoid": "不要把改革开放讲成概念背诵，不要使用夸张神化或虚构历史细节。",
        },
        "fallback": {
            "ideal": [
                "理想要坚定，但实现理想不能靠空谈。",
                "中国的发展靠的是一步一步干出来的。",
                "青年把个人理想同国家需要结合起来，就要看自己能不能在真实岗位上解决问题、创造价值。",
            ],
            "difficulty": [
                "遇到困难时，不要怕试，也不要怕改。",
                "实践是检验真理的标准。路走不通，就总结经验再往前走。",
                "青年最宝贵的是敢闯敢干，但也要讲实效。",
            ],
            "practice": [
                "学习最终要落到本领上。",
                "课堂里的知识，只有同现实问题结合，才能变成能力。",
                "你要多问一句：这个知识能解决什么问题？这个方案有没有效果？",
            ],
            "reform": [
                "改革开放告诉我们，思想不能封闭，发展不能僵化。",
                "看准的事情就大胆试，试了以后看效果，效果好就坚持，效果不好就调整。",
                "青年既要有开放眼光，也要有务实精神。",
            ],
            "general": [
                "讲道理要联系实际，做事情要看结果。",
                "把理想落实为能力，把热情落实为行动。",
                "把个人成长放到国家发展的大局中，你就能走得稳、走得远。",
            ],
        },
    },
    "周恩来": {
        "name": "周恩来",
        "identity": "党和国家卓越领导人，人民的好总理",
        "period": "革命、建设与外交实践",
        "keywords": ["为中华之崛起而读书", "严于律己", "服务人民", "责任担当", "团结协作"],
        "tone": "亲切、诚恳、细致，强调修身、责任和服务人民",
        "anchor": "把远大志向落实到每天认真、可靠、负责的行动里。",
        "personality_analysis": {
            "temperament": "温和克制、细致周全、严于律己，谈青年成长时常把宏大志向落到品格、责任和日常行动。",
            "reasoning": "先体察学生处境，再提醒立志、修身、尽责；强调把小事做可靠，把集体和人民放在心上。",
            "voice": "像认真倾听后的谈心，语气亲切而有分寸，少用硬口号，多用具体生活场景。",
            "care": "面对压力时给人稳定感，帮助学生把事情理清楚，把该承担的责任一步步做好。",
            "avoid": "不要把温和写成软弱，不要堆砌赞美，不要虚构私人谈话场景。",
        },
        "fallback": {
            "ideal": [
                "我少年时说过，为中华之崛起而读书。",
                "今天这句话仍然可以问每一位同学：你为什么学习？为了谁成长？",
                "如果心中有国家、有人民，学习就不会只是为了分数，而会成为担当责任的准备。",
            ],
            "difficulty": [
                "困难面前，最能看出一个人的品格。",
                "越是复杂的时候，越要沉着、细致、守住原则。",
                "青年遇到压力，不妨先把事情一件一件理清，把能做的做好，把该担的责任担起来。",
            ],
            "practice": [
                "课堂和岗位都能体现担当。",
                "认真听一堂课、完成一项任务、帮助一个同伴，看似平常，却是在训练责任心。",
                "真正服务人民，不只在宏大的誓言里，也在每天踏实可靠的行动里。",
            ],
            "general": [
                "真正的崇高不是离生活很远，而是在日复一日的认真、克制、负责中形成的。",
                "愿你既有远大志向，也能从今天这一件小事做起。",
                "把家国情怀落到行动里，才是青年最可贵的成长。",
            ],
        },
    },
}


def _infer_dialogue_theme(question: str) -> str:
    text = question or ""
    if re.search(r"你好|您好|在吗|聊聊|随便聊|唠|家常|近况|吃饭|宿舍|睡不着|有点累|有些累", text):
        return "casual"
    if re.search(r"累|乱|难受|孤独|烦|委屈|低落|撑不住|想家|没劲|没动力", text):
        return "emotion"
    if re.search(r"理想|国家|人民|初心|信仰|使命|志向", text):
        return "ideal"
    if re.search(r"困难|挫折|迷茫|选择|压力|失败|焦虑", text):
        return "difficulty"
    if re.search(r"学习|课堂|岗位|实践|行动|落实|怎么做|集体|稳重|责任|负责|服务", text):
        return "practice"
    if re.search(r"改革|创新|开放|发展|变化", text):
        return "reform"
    return "general"


def _ancestor_dialogue_policy(question: str) -> dict:
    text = (question or "").strip()
    theme = _infer_dialogue_theme(text)
    question_marks = len(re.findall(r"[?？]", text))
    asks_many = bool(re.search(r"同时|分别|以及|还有|一方面|另一方面|既.*又|如何.*如何", text))
    is_complex = len(text) >= 90 or question_marks >= 2 or asks_many
    if is_complex:
        return {
            "theme": theme,
            "mode": "复杂追问",
            "min_len": 260,
            "max_len": 720,
            "guidance": "学生的问题包含多个层次，需要先接住核心关切，再分层回答。可以展开，但每一段都要有具体指向。",
        }
    if theme == "casual":
        return {
            "theme": theme,
            "mode": "家常短聊",
            "min_len": 35,
            "max_len": 180,
            "guidance": "学生只是想亲切聊几句，不要拔高成讲稿。像长辈坐下来听他说近况，可以短一些、暖一些。",
        }
    if theme in {"emotion", "difficulty"}:
        return {
            "theme": theme,
            "mode": "情绪安放",
            "min_len": 60,
            "max_len": 360,
            "guidance": "学生带着疲惫、迷茫或压力，先让他觉得被理解，再给一个能马上做的小办法。",
        }
    if theme in {"ideal", "practice", "reform"}:
        return {
            "theme": theme,
            "mode": "理想与行动",
            "min_len": 170,
            "max_len": 520,
            "guidance": "学生在谈理想、方法或时代变化，需要结合人物气质给出有思想深度、也能落地的回答。",
        }
    return {
        "theme": theme,
        "mode": "自然谈心",
        "min_len": 90,
        "max_len": 320,
        "guidance": "按学生问题自然回应。能简短就简短，需要解释再展开，不要为了庄重而生硬拔高。",
    }


def _profile_context(profile: dict) -> str:
    analysis = profile.get("personality_analysis", {})
    lines = [
        f"人物：{profile['name']}",
        f"身份定位：{profile['identity']}",
        f"时代语境：{profile['period']}",
        f"思想关键词：{'、'.join(profile['keywords'])}",
        f"表达风格：{profile['tone']}",
        f"核心锚点：{profile['anchor']}",
    ]
    for key, label in (
        ("temperament", "性格气质"),
        ("reasoning", "思考路径"),
        ("voice", "说话方式"),
        ("care", "回应学生的方式"),
        ("avoid", "必须避免"),
    ):
        if analysis.get(key):
            lines.append(f"{label}：{analysis[key]}")
    return "\n".join(lines)


def _clean_ancestor_text(text: str) -> str:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned).strip()
    banned_openers = (
        "作为AI",
        "作为一个AI",
        "作为语言模型",
        "以下是",
        "内部分析",
        "人物分析",
        "性格分析",
    )
    for opener in banned_openers:
        if cleaned.startswith(opener):
            cleaned = cleaned.split("\n", 1)[-1].strip() if "\n" in cleaned else ""
    return cleaned


def _is_ancestor_text_usable(text: str, min_len: int, max_len: int | None = None) -> bool:
    return not _ancestor_text_issues(text, min_len, max_len)


def _ancestor_text_issues(text: str, min_len: int, max_len: int | None = None) -> list[str]:
    cleaned = _clean_ancestor_text(text)
    issues = []
    if len(cleaned) < min_len:
        issues.append("回答过短，没有充分接住学生问题")
    if max_len and len(cleaned) > max_len:
        issues.append("回答过长，不像自然谈话")
    risky_claims = (
        "年轻时",
        "我年轻时",
        "我年轻那会儿",
        "我那时候",
        "我那会儿",
        "那时我",
        "那会儿我",
        "那时候我",
        "我当年",
        "我曾经也",
        "我也曾",
        "我也常",
        "我也会",
        "以前我也",
        "我也遇到过",
        "我也碰到过",
        "我曾遇到",
        "我遇到过",
        "我碰到过",
        "我经历过",
        "我总跟",
        "我总对",
        "我总是",
        "我过去",
        "我常说",
        "我常讲",
        "我曾说",
        "我讲过",
        "我深有体会",
        "我的体会",
        "在我年轻的时候",
        "我们那时候",
        "我们那会儿",
        "我们当年",
        "当年我们",
        "当年我们",
        "那时候我们",
        "我的一生",
        "我亲眼看到",
    )
    if any(mark in cleaned for mark in risky_claims):
        issues.append("含有未经题目提供的私人经历式表达")
    if re.search(r"(我看你|我瞧你|看你|瞧你).{0,18}(眼睛|黑眼圈|脸色|神情|样子|面色|表情)", cleaned):
        issues.append("含有未经提供的现场外貌或状态观察")
    stale_openers = (
        "你这个问题问得好",
        "你这个问题问到了点子上",
        "你这个问题问到点子上了",
        "你这个问题问到点子上",
        "这个问题问到了点子上",
        "这个问题问到点子上了",
        "抓到了点子上",
        "抓到点子上",
        "你能问出这个问题",
        "你问了一个很实在的问题",
        "你这个问题提得实在",
        "说明你已经在认真思考",
        "说明你在认真思考",
    )
    if any(mark in cleaned[:40] for mark in stale_openers):
        issues.append("开头套话感较强")
    forbidden_meta = ("人物分析", "内部分析", "性格分析", "作为AI", "作为语言模型", "提示词")
    if any(mark in cleaned for mark in forbidden_meta):
        issues.append("暴露了后端分析或 AI 元信息")
    return issues


def _ancestor_ai_unavailable(leader: str, reason: str = "") -> dict:
    suffix = f"（{reason}）" if reason else ""
    return {
        "ok": False,
        "leader": leader,
        "answer": "对话 AI 暂时没有接通，刚才的问题我不能用固定模板冒充回答。请稍后再试一次。",
        "follow_up": "AI 接通后，你可以继续按刚才的方式提问。",
        "source": "ai_unavailable",
        "error": f"ancestor dialogue ai unavailable{suffix}",
    }


def _student_state(question: str) -> str:
    text = question or ""
    if re.search(r"你好|您好|在吗|聊聊|随便聊|唠|家常|近况|吃饭|宿舍", text):
        return "学生想像和长辈聊天一样亲切说几句，需要自然、放松，不必每句话都上升到宏大主题。"
    if re.search(r"累|乱|难受|孤独|烦|委屈|低落|撑不住|想家|没劲|没动力", text):
        return "学生带着生活或学习中的疲惫感，需要先被安放情绪，再得到一个具体、温和、能马上做的小建议。"
    if re.search(r"迷茫|不知道|困惑|看不清|没方向", text):
        return "学生正处在方向感不清的状态，需要先被理解，再被引向可执行的选择。"
    if re.search(r"焦虑|压力|害怕|担心|失败|挫折", text):
        return "学生有压力和受挫感，需要稳定情绪，再把困难拆成可面对的问题。"
    if re.search(r"怎么做|如何|怎样|落实|行动|集体|稳重|责任|负责|服务", text):
        return "学生想要具体做法，需要给出从课堂、集体、实践入手的行动建议。"
    return "学生希望获得一次有温度的历史对话，需要先接住问题，再给出价值和行动方向。"


def _student_care_line(profile: dict, question: str) -> str:
    text = question or ""
    name = profile["name"]
    if re.search(r"你好|您好|在吗|聊聊|随便聊|唠|家常|近况|吃饭|宿舍", text):
        return {
            "毛泽东": "同学，那我们就不端着说大道理，先像坐在一张桌旁一样，慢慢聊几句。",
            "邓小平": "年轻朋友，随便聊也很好。很多问题不用先想得太大，把眼前事说清楚，办法就会露出来。",
            "周恩来": "同学，我愿意听你说说近况。学习也好，生活也好，心里有话就慢慢讲。",
        }.get(name, "我们就像平常谈心一样聊几句。")
    if re.search(r"累|乱|难受|孤独|烦|委屈|低落|撑不住|想家|没劲|没动力", text):
        return {
            "毛泽东": "人有疲惫的时候，不必把自己逼得太紧。先把心稳住，再看主要矛盾在哪里。",
            "邓小平": "累了就先承认累，不要硬撑着装没事。把事情分一分，先处理最要紧、最能见效的一件。",
            "周恩来": "你说累，我听得出来。先让自己缓一缓，喝口水、理一理心绪，再把该做的事一件件摆好。",
        }.get(name, "你愿意把疲惫说出来，这本身就是在认真照看自己。")
    if re.search(r"迷茫|不知道|困惑|看不清|没方向", text):
        return {
            "毛泽东": "你说迷茫，我能理解。方向不是凭空想出来的，常常要在接触实际、了解人民需要的过程中慢慢清楚起来。",
            "邓小平": "有些迷茫很正常，关键是别让迷茫停在心里打转。把问题摆出来，先找一个能做的小切口。",
            "周恩来": "青年人有迷茫，并不丢人。愿意认真追问自己的方向，说明你已经在为成长负责。",
        }.get(name, "你愿意把困惑说出来，这本身就是认真面对成长。")
    if re.search(r"焦虑|压力|害怕|担心|失败|挫折", text):
        return {
            "毛泽东": "压力面前，先不要被情绪牵着走。把矛盾弄清楚，把主要问题抓住，心里就会稳一些。",
            "邓小平": "压力越大，越要把事情拆开看。能试的先试，能改的马上改，路就是这样走出来的。",
            "周恩来": "越有压力，越要沉住气。把眼前的事理清楚，把该做的一件件做好，人就会慢慢稳下来。",
        }.get(name, "压力来了，先把能做的事看清楚。")
    if re.search(r"怎么做|如何|怎样|落实|行动|集体|稳重|责任|负责|服务", text):
        return {
            "毛泽东": "你问怎样做，这很好。道理只有落到行动里，才算真正站住了。",
            "邓小平": "问做法，就要回到实际效果。先别把目标说得太大，把第一步走扎实。",
            "周恩来": "做法往往就在日常小事里。把一件普通事情做可靠，就是在训练担当。",
        }.get(name, "我们就从能落地的一步谈起。")
    return "你把问题说出来，我们就可以顺着这个问题往深处谈。"


def _fallback_opening(profile: dict) -> dict:
    openings = {
        "毛泽东": (
            "同学，坐下来慢慢谈。青年人心里有问题，是好事，说明你在认真想自己的路。"
            "我更愿意先问一句：你的志向准备放到哪里去检验？如果只放在个人得失里，天地就小；"
            "如果放到人民中间、放到中国实际中去，你读书、做事、选择方向，就会有更坚实的根。"
        ),
        "邓小平": (
            "年轻朋友，问题摆在面前，不要先怕。很多事在纸上想不透，要放到实践里试一试、看一看。"
            "理想当然要有，但理想要变成本领、效率和结果。你今天学到的知识，最后要回答一个朴素的问题："
            "它能不能解决实际问题，能不能让生活和社会向前走一步。"
        ),
        "周恩来": (
            "同学，我愿意像和一位年轻朋友谈心那样同你说几句。立志要高远，做事要踏实。"
            "把“为中华之崛起而读书”放到今天，就是在课堂、集体和岗位中认真负责。"
            "真正的担当，常常不在豪言壮语里，而在你每天是否可靠、是否克制、是否愿意服务他人。"
        ),
    }
    return {
        "ok": True,
        "leader": profile["name"],
        "answer": openings.get(profile["name"], profile["anchor"]),
        "follow_up": "你可以把现在最想问的一件事告诉我，我们接着谈。",
        "source": "local",
    }


def _simulate_ancestor_reply(leader: str, question: str, history: list | None = None) -> dict:
    profile = LEADER_PROFILES.get(leader) or LEADER_PROFILES["毛泽东"]
    policy = _ancestor_dialogue_policy(question)
    theme = policy["theme"]
    if theme == "casual":
        casual = {
            "毛泽东": "同学，就这么聊也很好。学习累了、心里有点乱，都可以说出来。人不是铁打的，歇一歇、想一想，再往前走，反而更有劲。你今天最想说的，是学习上的事，还是生活里的事？",
            "邓小平": "年轻朋友，那就不讲空话。最近累也好、乱也好，先别急着给自己下结论。把今天最烦的一件事挑出来，看看能不能先做一个小调整。我们就从这一点聊起。",
            "周恩来": "同学，我愿意陪你慢慢聊。学习、宿舍、生活里的小烦恼，都不是小事。一个人能把心里的话讲清楚，就已经在整理自己了。你先说，我认真听着。",
        }
        return {
            "ok": True,
            "leader": leader,
            "answer": casual.get(profile["name"], "我们就像平常谈心一样聊几句。你先说说，最近最牵动你的是什么？"),
            "follow_up": "你可以接着说说最近最想聊的一件小事。",
            "source": "local",
        }
    if theme == "emotion":
        emotion = {
            "毛泽东": (
                "同学，累了、乱了，先不要怕。人的精神也要经过休整，才能继续打硬仗。你先把眼前的事情分一分：哪些是真正要紧的，哪些只是情绪把它放大了。\n\n"
                "今晚不必一下子解决所有问题。先做一件小事：把明天最该完成的一项写下来，再给自己留一点休息。路不是一口气走完的，是一步一步走出来的。"
            ),
            "邓小平": (
                "年轻朋友，状态乱的时候，最忌讳在脑子里空转。先别问自己是不是不行，先问：眼前哪一件事能动手改一改？\n\n"
                "能睡一觉就先睡一觉，能整理一页笔记就整理一页，能和同学说清一个误会就先说清。办法不是想出来摆着看的，是试出来、改出来的。"
            ),
            "周恩来": (
                "同学，听你这样说，我更想先劝你把心放缓一点。学习和生活搅在一起时，人很容易觉得哪一头都抓不住，这并不说明你差，只说明你需要重新整理。\n\n"
                "今晚可以先做三件小事：把桌面收一收，把明天最重要的一件事写下来，再好好休息。一个人可靠的力量，常常就是从照顾好当下开始的。"
            ),
        }
        return {
            "ok": True,
            "leader": leader,
            "answer": emotion.get(profile["name"], _student_care_line(profile, question)),
            "follow_up": "你愿意的话，可以继续说说最让你累的那件事。",
            "source": "local",
        }
    parts = profile["fallback"].get(theme) or profile["fallback"]["general"]
    if history:
        bridge_map = {
            "毛泽东": "你前面的话里，已经触到了一个要紧处：青年不能只在心里打转，要到实际中去看问题。",
            "邓小平": "你前面问得很实在。问题不怕摆出来，怕的是只停在想法里，不去试、不去改。",
            "周恩来": "我听得出来，你不是随便问问，而是在认真整理自己的方向和责任。",
        }
        bridge = bridge_map.get(profile["name"], "你前面的问题里，其实已经触到一个关键点：真正的成长要回到行动。")
    else:
        bridge = {
            "毛泽东": "我愿意把这个问题当作一次面对面的谈心。先不要急着找漂亮答案，要把问题放到人民和实际中看。",
            "邓小平": "这个问题很实际。我们谈事情，就从实际出发，看怎样把想法变成办法。",
            "周恩来": "我愿意认真听你把心里的话说出来。青年成长中的许多问题，都要在立志、修身和尽责中慢慢回答。",
        }.get(profile["name"], "我愿意把这个问题当作一次面对面的谈心。")
    care = _student_care_line(profile, question)
    answer = bridge + "\n\n" + care + "\n\n" + "\n".join(parts)
    if len(answer) < 190:
        closing = {
            "毛泽东": "你可以先从身边真实的人和事看起，少一点空想，多一点调查；少一点犹豫，多一点实践。方向不是喊出来的，是在一次次为集体、为他人解决问题时长出来的。",
            "邓小平": "不要把答案想得太玄。先定一个小目标，做完看效果，发现问题就改。青年最怕的不是走得慢，而是只停在想法里不往前迈。",
            "周恩来": "你不妨从今天开始，选一件集体中需要有人认真做的小事，把它做细、做稳、做到底。一个人可靠的品格，常常就是在这些不起眼的坚持里形成的。",
        }.get(profile["name"], "把问题落到今天能做的一步，认真做下去，路就会慢慢清楚。")
        answer += "\n\n" + closing
    followups = {
        "ideal": "你可以再问我：怎样判断自己的理想是不是同人民需要连在一起？",
        "difficulty": "你可以再问我：面对长期看不到结果的努力，怎样坚持下去？",
        "practice": "你可以再问我：今天的课堂学习怎样转化为服务社会的能力？",
        "reform": "你可以再问我：青年如何在变化的时代保持清醒和勇气？",
        "general": "你可以再问我：今天的青年最需要守住什么、锻炼什么？",
    }
    return {
        "ok": True,
        "leader": leader,
        "answer": answer,
        "follow_up": followups.get(theme, followups["general"]),
        "source": "local",
    }


def generate_ancestor_dialogue(leader: str, question: str, history: list | None = None) -> dict:
    """Generate immersive first-person classroom dialogue with a selected leader."""
    profile = LEADER_PROFILES.get(leader)
    if not profile:
        raise ValueError("不支持的对话对象")
    clean_question = str(question or "").strip()
    if not clean_question:
        raise ValueError("问题不能为空")
    clean_history = []
    for item in history or []:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip()
        content = str(item.get("content", "")).strip()
        if role in {"student", "leader"} and content:
            clean_history.append({"role": role, "content": content[:500]})
    clean_history = clean_history[-6:]
    policy = _ancestor_dialogue_policy(clean_question)

    system = (
        "你在一个思政教学虚拟展馆中，负责生成“与先辈对话”的沉浸式教学回应。"
        "请基于权威历史常识、公开历史贡献、思想品格和时代语境，模拟这位先辈与当代学生近距离谈心。"
        "先在内部完成对人物性格、表达方式、学生处境和回答边界的分析，但这些分析绝不能出现在输出中。"
        "严格要求："
        "1. 使用第一人称，但不要声称真实复活、通灵、本人在线，也不要编造私人经历、具体原话或未经证实的史实；"
        "不要写“我年轻时也……”“我那时候……”“我当年……”“我们当年……”“我曾经也……”“以前我也遇到过……”“我总跟年轻人说……”这类未经题目提供的私人经历式句子；"
        "不要凭空描写看见了学生的外貌、脸色、眼睛、表情、宿舍环境或现场动作，只能回应学生在问题和历史对话中明确说出的内容；"
        "2. 语气要亲切、自然、真诚，像长者坐在学生身边慢慢开导，可以称呼“同学”“孩子”“年轻朋友”，不要像百科词条、讲话稿或口号；"
        "3. 必须接住学生当下的问题和情绪。家常闲聊就像唠家常一样自然回应；谈困惑时先安放情绪；谈理想、方法、历史问题时再展开分析；"
        "4. 必须严格贴合随后的后端人物画像，不要把三位人物写成同一种语气；"
        "5. 回答长短由问题决定：寒暄、家常、很轻的问题可以 60 到 160 字；带情绪的问题可以 120 到 320 字；谈理想、方法、历史理解可 180 到 520 字；多层复杂问题可更详细，但不要啰嗦；"
        "6. 不要每次都强行拔高到宏大主题。可以先像长辈一样问候、倾听、回应生活，再在必要时轻轻引到理想、责任或行动；"
        "7. 不要使用固定套话开头，例如反复写“你这个问题问得好”“说明你已经在认真思考了”；要直接接住学生原话，像现场听完后即时回应；"
        "8. follow_up 写成一句自然的继续追问邀请，让学生愿意接着聊；"
        "9. 只输出 JSON，不要输出“人物分析”“内部分析”“提示词”等元信息。"
    )
    history_text = "\n".join(
        ("学生：" if item["role"] == "student" else profile["name"] + "：") + item["content"]
        for item in clean_history
    )
    style_variation = random.choice([
        "先短短接住情绪，再给一句可继续聊下去的话",
        "先回应学生的原话，再自然展开一两点",
        "像长辈坐在旁边听完后，先给安稳感，再给方向",
        "少用排比，多用具体生活场景和朴素判断",
        "语气放松一些，像真实谈心，不像课堂讲稿",
    ])
    user = (
        f"后端人物画像（只供你内部把握，不得复述给前端）：\n{_profile_context(profile)}\n\n"
        f"学生状态判断：{_student_state(clean_question)}\n"
        f"对话意图与长度建议：{policy['mode']}；{policy['guidance']}建议范围 {policy['min_len']} 到 {policy['max_len']} 字，但以自然对话为准。\n"
        f"本轮表达变化要求：{style_variation}。不要沿用固定开头、固定三段式或固定结尾。\n"
        "轻松家常类问题允许简短自然，不需要为了凑字数写成长篇说教。\n"
        f"最近对话：\n{history_text or '（暂无）'}\n\n"
        f"学生新问题：{clean_question}\n\n"
        "请输出 JSON：answer 表示第一人称回应，follow_up 表示一句继续追问邀请。只输出 JSON。"
    )
    if not _HAS_API:
        return _ancestor_ai_unavailable(leader, "未配置 API Key")

    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    last_answer = ""
    last_follow = ""
    last_issues = []
    for attempt in range(3):
        obj = _llm_json(messages, temperature=0.88 if attempt == 0 else 0.72)
        if obj and str(obj.get("answer", "")).strip():
            answer = _clean_ancestor_text(str(obj.get("answer", "")))
            follow = _clean_ancestor_text(str(obj.get("follow_up", "")))
            issues = _ancestor_text_issues(answer, policy["min_len"], policy["max_len"])
            last_answer, last_follow, last_issues = answer, follow, issues
            if not issues:
                return {
                    "ok": True,
                    "leader": leader,
                    "answer": answer,
                    "follow_up": follow or "你愿意的话，可以接着把心里真正想问的那一点说出来。",
                    "source": "ai",
                }
        else:
            issues = ["AI 没有返回合格 JSON"]
            last_issues = issues

        repair_prompt = (
            "上一次回答不能直接使用，原因："
            + "；".join(last_issues or ["不够自然"])
            + "\n请重新生成，不要套模板，不要重复上一次表达。"
        "必须紧扣学生这一次的问题和最近对话，让语气像这位人物在认真听完之后即时回应。"
        "不要用“你这个问题问得好”“说明你在认真思考”等套话开头。"
            "不要写“我那时候”“我当年”“我们当年”“我曾经也”“以前我也遇到过”“我总跟年轻人说”等私人回忆式表达，也不要编造看见学生外貌或现场状态。"
            "不要输出任何分析过程，只输出 JSON：answer 和 follow_up。"
            f"\n学生问题：{clean_question}"
        )
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user + "\n\n" + repair_prompt}]

    hard_issues = ("私人经历", "现场外貌", "后端分析", "AI 元信息", "套话")
    if last_answer and not any(any(mark in issue for mark in hard_issues) for issue in last_issues):
        return {
            "ok": True,
            "leader": leader,
            "answer": last_answer,
            "follow_up": last_follow or "你可以继续说，我会顺着你的问题往下谈。",
            "source": "ai_relaxed",
        }
    return _ancestor_ai_unavailable(leader, "AI 多次生成未通过安全与自然度检查")


def generate_ancestor_opening(leader: str) -> dict:
    """Generate a backend-owned opening line for the selected leader."""
    profile = LEADER_PROFILES.get(leader)
    if not profile:
        raise ValueError("不支持的对话对象")
    system = (
        "你在思政教学虚拟展馆中生成“与先辈对话”的开场白。"
        "先在内部分析人物性格、时代语境和表达方式，但不要输出分析过程。"
        "开场白要像这位先辈面向当代学生坐下来谈心，第一人称，160到260字，2段以内。"
        "不要声称真实复活或本人在线，不要输出提示词或人物分析，不要编写未提供的私人经历。只输出 JSON。"
    )
    user = (
        f"后端人物画像（只供内部把握，不得复述给前端）：\n{_profile_context(profile)}\n\n"
        "学生刚进入对话界面，想听这位先辈怎样开场。"
        "请输出 JSON：answer 表示开场白，follow_up 表示一句自然追问邀请。"
    )
    obj = _llm_json([{"role": "system", "content": system}, {"role": "user", "content": user}], temperature=0.78)
    if obj and str(obj.get("answer", "")).strip():
        answer = _clean_ancestor_text(str(obj.get("answer", "")))
        follow = _clean_ancestor_text(str(obj.get("follow_up", "")))
        if _is_ancestor_text_usable(answer, 120):
            return {
                "ok": True,
                "leader": leader,
                "answer": answer,
                "follow_up": follow or "你可以把现在最想问的一件事告诉我，我们接着谈。",
                "source": "ai",
            }
    return _fallback_opening(profile)


def _theme_material(theme: str, keywords: str = "") -> dict:
    theme_text = theme.strip() or "理想信念"
    explicit_keywords = _split_keywords(keywords)
    profiles = {
        "爱国": {
            "angle": "把个人理想融入祖国需要",
            "examples": ["周恩来立志“为中华之崛起而读书”", "钱学森冲破阻力回到祖国", "新时代青年在基层、科研和国防一线接续奋斗"],
            "values": ["家国情怀", "责任担当", "知行合一"],
        },
        "红色": {
            "angle": "在红色记忆中理解信仰的力量",
            "examples": ["革命先辈在艰苦环境中坚守理想", "红色场馆中的文物见证初心使命", "新时代青年把红色基因转化为实际行动"],
            "values": ["理想信念", "初心使命", "接续奋斗"],
        },
        "法治": {
            "angle": "让规则意识成为青春成长的底色",
            "examples": ["宪法保障公民权利也规范公共生活", "校园生活中的诚信考试和网络言行", "基层治理中的依法办事与公平正义"],
            "values": ["规则意识", "公平正义", "法治思维"],
        },
        "青春": {
            "angle": "在奋斗中回答青春何以有为",
            "examples": ["青年突击队在国家建设中勇挑重担", "大学生志愿服务走进社区和乡村", "科技创新竞赛中的反复试验与团队协作"],
            "values": ["奋斗精神", "团队协作", "创新担当"],
        },
        "劳动": {
            "angle": "在平凡岗位中理解创造价值",
            "examples": ["劳动模范在一线精益求精", "工匠精神支撑中国制造", "校园劳动教育连接课堂与生活"],
            "values": ["劳动精神", "工匠精神", "服务意识"],
        },
        "共同体": {
            "angle": "从中国发展看世界责任",
            "examples": ["构建人类命运共同体理念回应时代之问", "共建“一带一路”推动互利合作", "青年以开放视野参与文明交流"],
            "values": ["胸怀天下", "合作共赢", "文明互鉴"],
        },
    }
    selected = None
    for key, profile in profiles.items():
        if key in theme_text:
            selected = profile
            break
    if not selected:
        selected = {
            "angle": f"从真实生活中理解{theme_text}的时代价值",
            "examples": [f"课堂学习中认识{theme_text}", f"社会实践中观察{theme_text}", f"个人成长中践行{theme_text}"],
            "values": explicit_keywords[:3] or ["政治认同", "责任担当", "实践能力"],
        }
    if explicit_keywords:
        selected = dict(selected)
        selected["values"] = list(dict.fromkeys(explicit_keywords + selected["values"]))[:4]
    return selected


def _simulate_script(
    script_type: str,
    theme: str,
    characters: str = "",
    usage: str = "",
    audience: str = "",
    duration: str = "",
    style: str = "",
    keywords: str = "",
) -> dict:
    """生成本地兜底作品，确保无外部 AI 时也能按主题产出可用内容。"""
    usage = usage or "课堂导入"
    audience = audience or "大学生"
    duration = duration or ("8分钟" if script_type == "情景剧" else "5分钟")
    style = style or ("沉浸对话" if script_type == "情景剧" else "青春励志")
    material = _theme_material(theme, keywords)
    examples = material["examples"]
    values = "、".join(material["values"])
    if script_type == "情景剧":
        role_line = characters or f"学生甲、学生乙、教师、旁白（适合{audience}）"
        content = (
            f"《把{theme}讲给青春听》\n\n"
            f"【作品定位】{usage}，预计{duration}，风格为{style}。\n\n"
            f"【角色】{role_line}\n\n"
            f"【第一幕：问题出现】\n"
            f"场景：教室或主题活动现场。屏幕上出现“{theme}”几个字。\n\n"
            f"学生甲：这个主题我们经常听到，可如果要把它讲给同学听，我总觉得还差一点真实感。\n"
            f"学生乙：也许它不只在书本里。比如，{examples[0]}，这就是一代人对时代的回答。\n"
            f"教师：好的作品不是背概念，而是把概念放回人的选择、时代的需要和自己的行动中。\n\n"
            f"【第二幕：走进故事】\n"
            f"旁白：灯光转暗，舞台从现实课堂切换到历史与现实交织的空间。\n\n"
            f"学生甲：如果我是故事中的人，我会怎样选择？\n"
            f"学生乙：{examples[1]}。他们不是没有困难，而是在困难面前仍然选择向前。\n"
            f"教师：这正是{theme}的力量。它让我们理解{material['angle']}。\n\n"
            f"【第三幕：回到当下】\n"
            f"学生甲：那我们今天能做什么？\n"
            f"学生乙：从诚信学习、认真实践、服务集体开始，把{values}落到每天的行动里。\n"
            f"教师：{examples[2]}。时代给青年提供了舞台，也要求青年拿出担当。\n\n"
            f"【结尾】\n"
            f"旁白：{theme}不是遥远的口号，而是每一次选择中的方向。愿我们把课堂上的理解，变成脚下真实的行动。\n"
        )
        script = {"type": "情景剧", "characters": role_line, "content": content}
    else:
        speech = (
            f"尊敬的老师，亲爱的同学们：\n\n"
            f"大家好！今天我演讲的题目是《在{theme}中读懂青春担当》。\n\n"
            f"这是一篇用于{usage}的{duration}演讲稿，面向{audience}，整体风格为{style}。"
            f"我想从一个问题讲起：{theme}离我们远吗？如果它只停留在口号里，当然会显得遥远；"
            f"但当我们把它放进历史、现实和个人成长中，就会发现它其实就在每一次选择里。\n\n"
            f"第一，理解{theme}，要从真实故事中看见方向。{examples[0]}。"
            f"这些故事告诉我们，真正有力量的价值不是写在纸上，而是在关键时刻经得起选择。\n\n"
            f"第二，践行{theme}，要把课堂学习同社会实践连接起来。{examples[1]}。"
            f"对今天的青年而言，{theme}意味着{material['angle']}，也意味着在专业学习、集体生活和社会服务中不断校准自己的方向。\n\n"
            f"第三，弘扬{theme}，要落到可持续的行动。{examples[2]}。"
            f"我们不一定每天都面对宏大的考验，但我们每天都可以做出具体的努力：认真完成一次调研，真诚参与一次志愿服务，"
            f"在团队协作中守信负责，在面对困难时不轻易退缩。\n\n"
            f"同学们，{values}不是抽象词语，而是青年成长的坐标。愿我们把对{theme}的理解，"
            f"转化为课堂上的专注、实践中的担当和人生道路上的坚定选择。\n\n"
            f"我的演讲完毕，谢谢大家！"
        )
        script = {
            "type": "演讲稿",
            "characters": "",
            "content": speech,
        }

    script["title"] = theme
    script["theme"] = theme
    script["usage"] = usage
    script["audience"] = audience
    script["duration"] = duration
    script["style"] = style
    script["keywords"] = keywords
    script["notes"] = f"适用于{usage}；可根据班级人数、真实案例和课堂时间继续压缩或扩展。"
    script["ai_generated"] = True
    return script
def generate_study_plan(destination: str, duration: str, theme: str) -> dict:
    """
    生成研学方案。
    优先使用大模型 API，失败或无 API Key 时回退到本地模拟。
    """
    plan = _call_llm_study_plan(destination, duration, theme)
    if plan:
        return plan
    return _simulate_study_plan(destination, duration, theme)


def _call_llm_study_plan(destination: str, duration: str, theme: str) -> Optional[dict]:
    system = "你是一位思政教育实践教学专家。根据输入生成完整研学方案，覆盖课前准备、实施过程、课后评价、成果产出，只输出 JSON。"
    user = (
        f"目的地：{destination}\n时长：{duration}\n主题：{theme}\n\n"
        f"请输出 JSON，字段如下：\n"
        f"- title: 方案标题\n"
        f"- destination: 目的地\n"
        f"- duration: 时长\n"
        f"- theme: 主题\n"
        f"- itinerary: 详细行程安排\n"
        f"- objectives: 教学目标\n"
        f"- budget: 预算说明\n"
        f"- notes: 注意事项\n"
        f"- target_grade: 适用年级\n"
        f"- related_courses: 关联的思政课程列表\n"
        f"- core_competencies: 核心素养目标\n"
        f"- preparation: 行前准备（知识储备、物资准备、分组安排）\n"
        f"- tasks: 研学任务（学生各环节需完成的任务清单）\n"
        f"- evaluation: 评价方式（过程评价+成果评价+自评互评）\n"
        f"- safety: 安全预案\n"
        f"- expected_outcomes: 预期成果\n"
        f"- resources: 推荐资源（书籍、影视、网络、实地）\n"
        f"只输出 JSON，不要 Markdown 包裹。"
    )
    obj = _llm_json([{"role": "system", "content": system}, {"role": "user", "content": user}])
    if obj:
        obj.setdefault("destination", destination)
        obj.setdefault("duration", duration)
        obj.setdefault("theme", theme)
        obj["ai_generated"] = True
        # Normalize: LLM may return lists, frontend expects strings
        if isinstance(obj.get("objectives"), list):
            obj["objectives"] = "\n".join("- " + str(o) for o in obj["objectives"])
        if isinstance(obj.get("itinerary"), list):
            lines = []
            for day in obj["itinerary"]:
                if isinstance(day, dict):
                    d = day.get("day", "")
                    lines.append("第{}天：".format(d) if d else "")
                    for part in ("morning", "afternoon", "evening"):
                        if day.get(part):
                            lines.append(day[part])
                else:
                    lines.append(str(day))
            obj["itinerary"] = "\n".join(lines)
        if isinstance(obj.get("notes"), list):
            obj["notes"] = "\n".join("- " + str(n) for n in obj["notes"])
    return obj


def generate_script(
    script_type: str,
    theme: str,
    characters: str = "",
    *,
    usage: str = "",
    audience: str = "",
    duration: str = "",
    style: str = "",
    keywords: str = "",
) -> dict:
    """
    生成情景剧或演讲稿。
    优先使用大模型 API，失败或无 API Key 时回退到本地模拟。
    """
    script = _call_llm_script(script_type, theme, characters, usage, audience, duration, style, keywords)
    content = str(script.get("content", "") if script else "").strip()
    has_placeholder = any(mark in content for mark in ("角色A：……", "角色B：……", "旁白：……", "????"))
    if script and len(content) >= 180 and not has_placeholder:
        return script
    return _simulate_script(script_type, theme, characters, usage, audience, duration, style, keywords)


def _call_llm_script(
    script_type: str,
    theme: str,
    characters: str = "",
    usage: str = "",
    audience: str = "",
    duration: str = "",
    style: str = "",
    keywords: str = "",
) -> Optional[dict]:
    type_label = "情景剧" if script_type == "情景剧" else "演讲稿"
    system = f"你是一位思政教育{type_label}创作专家。根据用户输入生成{type_label}，输出 JSON。"
    char_line = f"\n- characters: 角色设定（含角色名和身份）" if type_label == "情景剧" else "\n- characters: 留空"
    user = (
        f"主题：{theme}\n"
        f"课堂用途：{usage or '课堂导入'}\n"
        f"适用对象：{audience or '大学生'}\n"
        f"预计时长：{duration or ('8分钟' if type_label == '情景剧' else '5分钟')}\n"
        f"表达风格：{style or ('沉浸对话' if type_label == '情景剧' else '青春励志')}\n"
        + (f"关键词：{keywords}\n" if keywords else "")
        + (f"角色：{characters}\n" if characters else "")
        + f"请输出 JSON，字段如下：\n"
        f"- title: {type_label}标题\n"
        f"- type: {type_label}\n"
        f"- theme: 主题\n"
        f"- usage: 课堂用途\n"
        f"- audience: 适用对象\n"
        f"- duration: 预计时长\n"
        f"- style: 表达风格\n"
        f"- keywords: 关键词\n"
        f"{char_line}\n"
        f"- content: {type_label}完整内容，必须可直接用于课堂或活动展示，包含清晰开头、主体、结尾\n"
        f"- notes: 使用建议\n"
        f"只输出 JSON，不要 Markdown 包裹。"
    )
    obj = _llm_json([{"role": "system", "content": system}, {"role": "user", "content": user}])
    if obj:
        obj["ai_generated"] = True
        obj.setdefault("theme", theme)
        obj.setdefault("usage", usage)
        obj.setdefault("audience", audience)
        obj.setdefault("duration", duration)
        obj.setdefault("style", style)
        obj.setdefault("keywords", keywords)
        # Normalize lists to strings for frontend
        if isinstance(obj.get("characters"), list):
            obj["characters"] = "\n".join(str(c) for c in obj["characters"])
        if isinstance(obj.get("content"), list):
            obj["content"] = "\n\n".join(str(p) for p in obj["content"])
        if isinstance(obj.get("notes"), list):
            obj["notes"] = "\n".join("- " + str(n) for n in obj["notes"])
    return obj
