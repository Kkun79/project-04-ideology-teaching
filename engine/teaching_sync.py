from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from engine import data_manager as dm
from engine import news_service


DATA_DIR = Path(__file__).parent.parent / "data"
TEACHING_SYNC_META_FILE = DATA_DIR / "teaching_sync_meta.json"

CASE_LIMIT = 6
CASE_AUTO_INTERVAL_DAYS = 1
TERM_AUTO_INTERVAL_DAYS = 7
TERM_SYNC_LIMIT = 14
TERM_POLICY_MATCH_LIMIT = 8

EXCLUDED_CASE_KEYWORDS = [
    "世界杯",
    "足球",
    "篮球",
    "网球",
    "羽毛球",
    "比赛",
    "晋级",
    "淘汰赛",
    "娱乐",
    "明星",
    "票房",
    "演唱会",
    "综艺",
    "电影",
    "电视剧",
    "游戏",
    "电竞",
    "粉丝",
    "评分",
    "app store",
    "天气",
    "预警",
    "暴雨",
    "高温",
    "台风",
    "航班",
    "机场",
    "食谱",
    "皮肤",
    "不良反应",
    "手机",
    "原油出口",
]

CASE_CATEGORY_RULES = [
    ("党史事件", ["中国共产党", "党的十九大", "党建", "党章", "伟大建党精神", "红船", "长征", "党史"]),
    ("红色场馆", ["红色地标", "红军街", "革命烈士", "故居", "会址", "纪念馆", "革命遗址", "红色文旅"]),
    ("先进人物", ["烈士", "楷模", "榜样", "先进", "英雄", "模范", "坚守", "奉献"]),
    ("脱贫攻坚", ["脱贫攻坚", "扶贫", "共同富裕", "增收", "乡村振兴", "基层"]),
    ("科技报国", ["科技", "创新", "航天", "卫星", "芯片", "人工智能", "数字经济", "工业", "实验室"]),
    ("生态文明", ["生态", "环境", "绿色", "低碳", "减排", "污染", "湿地", "能源", "气候", "美丽中国"]),
    ("法治教育", ["法治", "法律", "司法", "法院", "检察", "治理", "执法", "安全", "反诈", "国家安全"]),
    ("乡村振兴", ["乡村振兴", "三农", "脱贫", "县域", "农业", "农村", "农民", "共同富裕"]),
    ("改革开放", ["改革", "开放", "经济", "外贸", "营商", "自贸", "发展", "合作", "外资", "产业"]),
]

TERM_TEMPLATES = [
    {
        "term": "高质量发展",
        "book": "《习概》",
        "proposer": "习近平",
        "proposed_time": "2017年10月18日",
        "proposed_context": "党的十九大报告明确我国经济已由高速增长阶段转向高质量发展阶段。",
        "meaning": "高质量发展强调把发展质量摆在更加突出的位置，要求在创新、协调、绿色、开放、共享的发展中提升经济体系整体效能，实现更有效率、更加公平、更可持续、更为安全的发展。",
        "significance": "它明确了新时代我国经济社会发展的战略导向，是推进现代化建设、产业升级、区域协调和民生改善的重要遵循。",
        "source_publication": "《决胜全面建成小康社会 夺取新时代中国特色社会主义伟大胜利》",
        "url": "https://www.gov.cn/zhuanti/2017-10/27/content_5234876.htm",
        "related_terms": ["新发展理念", "中国式现代化", "新质生产力"],
        "keywords": ["高质量发展", "发展质量", "产业升级", "现代化产业体系"],
    },
    {
        "term": "习近平新时代中国特色社会主义思想",
        "book": "《习概》",
        "proposer": "习近平",
        "proposed_time": "2017年10月18日",
        "proposed_context": "党的十九大系统阐述并将其确立为党必须长期坚持的指导思想。",
        "meaning": "习近平新时代中国特色社会主义思想是当代中国马克思主义、二十一世纪马克思主义，是中华文化和中国精神的时代精华，系统回答新时代坚持和发展什么样的中国特色社会主义、怎样坚持和发展中国特色社会主义等重大时代课题。",
        "significance": "它是全党全国人民为实现中华民族伟大复兴而奋斗的行动指南，是新时代党和国家事业发展的根本遵循。",
        "source_publication": "党的十九大报告及《中国共产党章程（修正案）》",
        "url": "https://www.gov.cn/zhuanti/2017-10/27/content_5234876.htm",
        "related_terms": ["中国式现代化", "党的领导", "马克思主义中国化时代化"],
        "keywords": ["习近平新时代中国特色社会主义思想", "党的十九大", "指导思想", "党章"],
    },
    {
        "term": "一国两制",
        "book": "《习概》",
        "proposer": "邓小平",
        "proposed_time": "20世纪80年代",
        "proposed_context": "为解决香港、澳门、台湾问题，实现祖国和平统一而提出的科学构想。",
        "meaning": "“一国两制”是在一个中国前提下，国家主体坚持社会主义制度，香港、澳门、台湾保持原有资本主义制度和生活方式长期不变。",
        "significance": "它是中国特色社会主义的伟大创举，为香港、澳门长期繁荣稳定和推进祖国统一提供了制度安排。",
        "source_publication": "宪法、香港基本法、澳门基本法及中央有关重要文件",
        "url": "",
        "related_terms": ["爱国者治港", "国家统一", "民族复兴"],
        "keywords": ["一国两制", "香港", "澳门", "港澳", "爱国者治港"],
    },
    {
        "term": "党的领导",
        "book": "《习概》",
        "proposer": "中国共产党",
        "proposed_time": "贯穿中国革命、建设、改革全过程",
        "proposed_context": "党的领导是中国特色社会主义最本质的特征，是中国特色社会主义制度的最大优势。",
        "meaning": "党的领导强调党总揽全局、协调各方，把方向、谋大局、定政策、促改革，确保党和国家事业沿着正确方向前进。",
        "significance": "坚持党的领导是推进中国式现代化、实现民族复兴、应对风险挑战的根本保证。",
        "source_publication": "党的十九大、二十大报告及相关重要讲话",
        "url": "",
        "related_terms": ["全面从严治党", "中国式现代化", "民族复兴"],
        "keywords": ["党的领导", "中国共产党", "党中央", "总书记", "领导核心"],
    },
    {
        "term": "伟大建党精神",
        "book": "《习概》",
        "proposer": "习近平",
        "proposed_time": "2021年7月1日",
        "proposed_context": "习近平在庆祝中国共产党成立100周年大会上首次概括提出伟大建党精神。",
        "meaning": "伟大建党精神的基本内涵是坚持真理、坚守理想，践行初心、担当使命，不怕牺牲、英勇斗争，对党忠诚、不负人民。",
        "significance": "它是中国共产党的精神之源，是新时代赓续红色血脉、坚定理想信念的重要精神坐标。",
        "source_publication": "习近平在庆祝中国共产党成立100周年大会上的重要讲话",
        "url": "https://www.gov.cn/xinwen/2021-07/01/content_5621847.htm",
        "related_terms": ["中国共产党人精神谱系", "理想信念", "初心使命"],
        "keywords": ["伟大建党精神", "精神谱系", "红色", "革命", "党史"],
    },
    {
        "term": "乡村振兴",
        "book": "《习概》",
        "proposer": "中国共产党",
        "proposed_time": "2017年10月18日",
        "proposed_context": "党的十九大报告提出实施乡村振兴战略。",
        "meaning": "乡村振兴强调产业兴旺、生态宜居、乡风文明、治理有效、生活富裕，推动农业农村现代化。",
        "significance": "它是解决新时代“三农”问题、促进城乡融合发展、推进共同富裕的重要战略。",
        "source_publication": "党的十九大报告及乡村振兴战略规划",
        "url": "",
        "related_terms": ["共同富裕", "人民立场", "农业农村现代化"],
        "keywords": ["乡村振兴", "农村", "农业", "农民", "增收", "县域"],
    },
    {
        "term": "新质生产力",
        "book": "《习概》",
        "proposer": "习近平",
        "proposed_time": "2023年9月",
        "proposed_context": "习近平在黑龙江考察调研期间首次系统提出“新质生产力”。",
        "meaning": "新质生产力是以科技创新为主导、摆脱传统增长路径和生产力发展方式的新型生产力，核心在于形成高科技、高效能、高质量的发展动能。",
        "significance": "它为推动科技创新和产业创新深度融合、加快建设现代化产业体系、培育发展新动能提供了重要理论指引。",
        "source_publication": "新华社关于习近平在黑龙江考察调研报道",
        "url": "https://www.gov.cn/yaowen/liebiao/202309/content_6902869.htm",
        "related_terms": ["高质量发展", "科技创新", "现代化产业体系"],
        "keywords": ["新质生产力", "科技创新", "产业创新", "现代化产业体系"],
    },
    {
        "term": "中国式现代化",
        "book": "《习概》",
        "proposer": "习近平",
        "proposed_time": "2022年10月16日",
        "proposed_context": "党的二十大报告对中国式现代化作出系统阐述。",
        "meaning": "中国式现代化是中国共产党领导的社会主义现代化，既有各国现代化的共同特征，更有基于中国国情的鲜明特色，强调人口规模巨大、全体人民共同富裕、物质文明和精神文明相协调、人与自然和谐共生、走和平发展道路。",
        "significance": "它拓展了发展中国家走向现代化的路径选择，为全面推进强国建设和民族复兴提供了总体框架。",
        "source_publication": "《高举中国特色社会主义伟大旗帜 为全面建设社会主义现代化国家而团结奋斗》",
        "url": "https://www.gov.cn/xinwen/2022-10/25/content_5721685.htm",
        "related_terms": ["高质量发展", "共同富裕", "新发展格局"],
        "keywords": ["中国式现代化", "现代化", "强国建设", "民族复兴"],
    },
    {
        "term": "生态文明",
        "book": "《习概》",
        "proposer": "中国共产党",
        "proposed_time": "2012年11月",
        "proposed_context": "党的十八大把生态文明建设纳入中国特色社会主义事业总体布局。",
        "meaning": "生态文明强调尊重自然、顺应自然、保护自然，把绿色发展理念贯穿经济社会建设全过程，推动形成节约资源和保护环境的空间格局、产业结构、生产方式、生活方式。",
        "significance": "它把人与自然和谐共生提升到国家发展战略高度，是建设美丽中国和实现可持续发展的重要保障。",
        "source_publication": "党的十八大报告及后续中央文件",
        "url": "https://www.gov.cn/ldhd/2012-11/17/content_2268826.htm",
        "related_terms": ["绿色发展", "双碳目标", "美丽中国"],
        "keywords": ["生态文明", "绿色发展", "低碳", "环境", "美丽中国"],
    },
    {
        "term": "共同富裕",
        "book": "《习概》",
        "proposer": "中国共产党",
        "proposed_time": "新时代持续深化阐述",
        "proposed_context": "习近平围绕扎实推动共同富裕作出一系列重要论述。",
        "meaning": "共同富裕不是少数人的富裕，也不是整齐划一的平均主义，而是在高质量发展基础上，通过勤劳创新、制度安排和公共服务优化，让全体人民共享现代化成果。",
        "significance": "它体现社会主义本质要求，是增进民生福祉、促进社会公平正义、增强人民获得感的重要目标。",
        "source_publication": "《扎实推动共同富裕》及相关重要讲话",
        "url": "https://www.gov.cn/xinwen/2021-10/15/content_5642813.htm",
        "related_terms": ["高质量发展", "乡村振兴", "民生保障"],
        "keywords": ["共同富裕", "民生", "收入分配", "县域", "三次分配"],
    },
    {
        "term": "总体国家安全观",
        "book": "《习概》",
        "proposer": "习近平",
        "proposed_time": "2014年4月15日",
        "proposed_context": "习近平在中央国家安全委员会第一次会议上提出总体国家安全观。",
        "meaning": "总体国家安全观强调以人民安全为宗旨、以政治安全为根本、以经济安全为基础、以军事科技文化社会安全为保障、以促进国际安全为依托，统筹发展和安全。",
        "significance": "它为新时代国家安全工作提供了总遵循，有助于增强风险意识、底线思维和系统治理能力。",
        "source_publication": "新华社有关中央国家安全委员会第一次会议报道",
        "url": "https://www.gov.cn/xinwen/2014-04/15/content_2660378.htm",
        "related_terms": ["国家安全", "法治教育", "底线思维"],
        "keywords": ["国家安全", "总体国家安全观", "安全", "风险", "底线思维"],
    },
    {
        "term": "人类命运共同体",
        "book": "《习概》",
        "proposer": "习近平",
        "proposed_time": "2013年3月23日",
        "proposed_context": "习近平在莫斯科国际关系学院演讲中提出共同体理念的重要表述。",
        "meaning": "人类命运共同体倡导各国相互依存、休戚与共，通过对话协商、合作共赢来应对全球性挑战，推动建设持久和平、普遍安全、共同繁荣、开放包容、清洁美丽的世界。",
        "significance": "它体现了中国推动全球治理体系变革、坚持和平发展和合作共赢的重要理念。",
        "source_publication": "习近平在莫斯科国际关系学院的演讲及联合国讲话",
        "url": "https://www.gov.cn/ldhd/2013-03/24/content_2360829.htm",
        "related_terms": ["一带一路", "全球治理", "和平发展"],
        "keywords": ["人类命运共同体", "全球治理", "合作共赢", "国际合作"],
    },
    {
        "term": "新发展理念",
        "book": "《习概》",
        "proposer": "习近平",
        "proposed_time": "2015年10月29日",
        "proposed_context": "党的十八届五中全会通过“十三五”规划建议时提出。",
        "meaning": "新发展理念包括创新、协调、绿色、开放、共享五个方面，集中回答了实现什么样的发展、怎样实现发展的问题。",
        "significance": "它是关系我国发展全局的一场深刻变革，为推动高质量发展、构建新发展格局提供了科学指引。",
        "source_publication": "《中共中央关于制定国民经济和社会发展第十三个五年规划的建议》",
        "url": "https://www.gov.cn/xinwen/2015-11/03/content_5004093.htm",
        "related_terms": ["高质量发展", "新发展格局", "中国式现代化"],
        "keywords": ["新发展理念", "创新", "协调", "绿色", "开放", "共享"],
    },
    {
        "term": "新发展格局",
        "book": "《习概》",
        "proposer": "习近平",
        "proposed_time": "2020年4月",
        "proposed_context": "中央财经委员会会议等重要场合提出要构建以国内大循环为主体、国内国际双循环相互促进的新发展格局。",
        "meaning": "新发展格局强调立足国内大市场和完整产业体系，以国内大循环吸引全球资源要素，更好联通国内国际两个市场两种资源。",
        "significance": "它是把握发展主动权、应对外部环境变化、推动高质量发展的重大战略部署。",
        "source_publication": "中央财经委员会会议等重要文件",
        "url": "",
        "related_terms": ["双循环", "高质量发展", "扩大内需"],
        "keywords": ["新发展格局", "国内大循环", "国际循环", "双循环", "扩大内需"],
    },
    {
        "term": "创新驱动发展战略",
        "book": "《习概》",
        "proposer": "中国共产党",
        "proposed_time": "2012年11月后持续深化",
        "proposed_context": "党的十八大以来，中央多次强调实施创新驱动发展战略。",
        "meaning": "创新驱动发展战略强调把科技创新摆在国家发展全局的核心位置，以创新培育新动能、塑造新优势。",
        "significance": "它是建设科技强国、实现产业升级和发展方式转变的重要抓手。",
        "source_publication": "党的十八大报告及国家创新驱动发展战略纲要",
        "url": "",
        "related_terms": ["新质生产力", "科技自立自强", "科教兴国战略"],
        "keywords": ["创新驱动", "科技创新", "科技自立自强", "实验室", "研发"],
    },
    {
        "term": "科教兴国战略",
        "book": "《习概》",
        "proposer": "中国共产党",
        "proposed_time": "1995年5月",
        "proposed_context": "《中共中央、国务院关于加速科学技术进步的决定》正式提出实施科教兴国战略。",
        "meaning": "科教兴国战略强调把科技和教育摆在优先发展的战略地位，通过提高国民素质和创新能力支撑国家现代化建设。",
        "significance": "它奠定了教育、科技、人才协同支撑国家发展的基本思路，是建设创新型国家的重要基础。",
        "source_publication": "《中共中央、国务院关于加速科学技术进步的决定》",
        "url": "",
        "related_terms": ["人才强国战略", "创新驱动发展战略", "教育现代化"],
        "keywords": ["科教兴国", "教育强国", "科技强国", "基础研究", "人才培养"],
    },
    {
        "term": "人才强国战略",
        "book": "《习概》",
        "proposer": "中国共产党",
        "proposed_time": "2003年后持续推进",
        "proposed_context": "新世纪以来党中央持续推进人才强国战略，新时代进一步把人才工作摆在突出位置。",
        "meaning": "人才强国战略强调人才是第一资源，要完善人才培养、引进、使用、评价、激励机制，建设规模宏大、结构合理、素质优良的人才队伍。",
        "significance": "它是推动高水平科技自立自强、建设现代化强国的重要支撑。",
        "source_publication": "中央人才工作会议等重要文件",
        "url": "",
        "related_terms": ["科教兴国战略", "创新驱动发展战略", "教育强国"],
        "keywords": ["人才强国", "人才工作", "第一资源", "高层次人才", "青年人才"],
    },
    {
        "term": "一带一路",
        "book": "《习概》",
        "proposer": "习近平",
        "proposed_time": "2013年9月、10月",
        "proposed_context": "习近平在哈萨克斯坦和印度尼西亚分别提出共建丝绸之路经济带和21世纪海上丝绸之路倡议。",
        "meaning": "一带一路倡议以政策沟通、设施联通、贸易畅通、资金融通、民心相通为重点，推动更高水平开放合作。",
        "significance": "它是新时代中国扩大对外开放、推动构建人类命运共同体的重要实践平台。",
        "source_publication": "习近平关于共建“一带一路”的重要讲话",
        "url": "",
        "related_terms": ["人类命运共同体", "高水平对外开放", "合作共赢"],
        "keywords": ["一带一路", "国际合作", "互联互通", "合作共赢"],
    },
    {
        "term": "文化自信",
        "book": "《习概》",
        "proposer": "习近平",
        "proposed_time": "2016年7月1日",
        "proposed_context": "庆祝中国共产党成立95周年大会讲话中强调文化自信。",
        "meaning": "文化自信是对中国特色社会主义文化发展道路、文化价值和文化生命力的坚定信念。",
        "significance": "它是更基础、更广泛、更深厚的自信，是道路自信、理论自信、制度自信的重要支撑。",
        "source_publication": "庆祝中国共产党成立95周年大会讲话",
        "url": "",
        "related_terms": ["四个自信", "两个结合", "社会主义核心价值观"],
        "keywords": ["文化自信", "中华优秀传统文化", "文化强国", "精神力量"],
    },
    {
        "term": "社会主义核心价值观",
        "book": "《习概》",
        "proposer": "中国共产党",
        "proposed_time": "2012年11月后系统凝练",
        "proposed_context": "党的十八大提出倡导富强、民主、文明、和谐，自由、平等、公正、法治，爱国、敬业、诚信、友善。",
        "meaning": "社会主义核心价值观从国家、社会、公民三个层面凝练了社会主义价值目标、价值取向和价值准则。",
        "significance": "它是凝魂聚气、强基固本的基础工程，对青年学生价值塑造和社会文明建设具有重要引领作用。",
        "source_publication": "党的十八大报告及中央相关文件",
        "url": "",
        "related_terms": ["文化自信", "立德树人", "精神文明建设"],
        "keywords": ["核心价值观", "爱国", "敬业", "诚信", "友善", "法治"],
    },
]

EXPANDED_TERM_TEMPLATES = [
    {
        "term": "立德树人",
        "book": "《习近平关于教育的重要论述》《思想道德与法治》",
        "proposer": "中国共产党",
        "proposed_time": "新时代教育实践中持续深化",
        "proposed_context": "围绕培养什么人、怎样培养人、为谁培养人这一教育根本问题提出并不断深化。",
        "meaning": "立德树人强调把思想政治教育、品德养成和知识能力培养统一起来，把学生成长成才同国家发展、民族复兴和社会进步联系起来。",
        "significance": "它是高校思想政治教育的根本任务，有助于引导学生坚定理想信念、厚植家国情怀、提升道德修养和责任意识。",
        "source_publication": "全国高校思想政治工作会议、全国教育大会相关重要论述",
        "url": "",
        "related_terms": ["理想信念", "社会主义核心价值观", "时代新人"],
        "keywords": ["立德树人", "教育强国", "思政课", "时代新人", "高校思想政治工作"],
        "source_scope": "expanded-positive",
    },
    {
        "term": "马克思主义中国化时代化",
        "book": "《马克思主义基本原理》《毛概》《习概》",
        "proposer": "中国共产党",
        "proposed_time": "中国革命、建设、改革和新时代实践中不断推进",
        "proposed_context": "中国共产党把马克思主义基本原理同中国具体实际相结合、同中华优秀传统文化相结合的历史进程中形成。",
        "meaning": "马克思主义中国化时代化强调坚持马克思主义基本立场观点方法，同时立足中国实际、回答时代课题、吸收中华文明智慧，形成具有中国特色和时代特征的理论成果。",
        "significance": "它说明党的理论创新不是照搬照抄，而是在实践中不断发展，为理解中国道路、中国制度和中国式现代化提供了思想基础。",
        "source_publication": "党的二十大报告及马克思主义理论相关教材",
        "url": "https://www.gov.cn/xinwen/2022-10/25/content_5721685.htm",
        "related_terms": ["两个结合", "实事求是", "理论创新"],
        "keywords": ["马克思主义中国化时代化", "两个结合", "理论创新", "中国具体实际"],
        "source_scope": "expanded-positive",
    },
    {
        "term": "中华优秀传统文化",
        "book": "《中华文明简史》《思想道德与法治》《习近平文化思想学习纲要》",
        "proposer": "中华民族长期历史实践",
        "proposed_time": "中华文明发展进程中长期形成",
        "proposed_context": "中华文明在长期延续、创新和融合中形成的思想观念、人文精神、道德规范和文化传统。",
        "meaning": "中华优秀传统文化包含讲仁爱、重民本、守诚信、崇正义、尚和合、求大同等价值追求，是中华民族精神品格的重要来源。",
        "significance": "它为当代青年理解文化自信、涵养道德品质、增强民族认同和文明交流互鉴意识提供了深厚根基。",
        "source_publication": "中华优秀传统文化传承发展工程相关文件及文化建设重要论述",
        "url": "",
        "related_terms": ["文化自信", "两个结合", "家国情怀"],
        "keywords": ["中华优秀传统文化", "文化自信", "文明传承", "家国情怀", "中华文明"],
        "source_scope": "expanded-positive",
    },
    {
        "term": "中国共产党人精神谱系",
        "book": "《中国近现代史纲要》《中国共产党简史》",
        "proposer": "中国共产党",
        "proposed_time": "党史学习教育和新时代精神文明建设中系统阐发",
        "proposed_context": "中国共产党在百余年奋斗历程中形成的一系列伟大精神，被系统梳理为中国共产党人精神谱系。",
        "meaning": "中国共产党人精神谱系以伟大建党精神为源头，涵盖井冈山精神、长征精神、延安精神、抗美援朝精神、雷锋精神、改革开放精神、脱贫攻坚精神等。",
        "significance": "它为思政课开展理想信念教育、党史教育和实践育人提供了鲜活资源，有助于学生理解精神力量怎样转化为现实行动。",
        "source_publication": "中国共产党人精神谱系相关权威发布和党史学习教育资料",
        "url": "",
        "related_terms": ["伟大建党精神", "理想信念", "红色资源"],
        "keywords": ["中国共产党人精神谱系", "伟大精神", "党史学习教育", "红色资源", "理想信念"],
        "source_scope": "expanded-positive",
    },
    {
        "term": "人民至上",
        "book": "《习概》《新时代中国特色社会主义理论与实践》",
        "proposer": "中国共产党",
        "proposed_time": "新时代治国理政实践中持续深化",
        "proposed_context": "围绕坚持以人民为中心的发展思想，在发展、治理、民生和改革实践中不断强调。",
        "meaning": "人民至上强调把人民放在最高位置，把人民对美好生活的向往作为奋斗目标，坚持发展为了人民、发展依靠人民、发展成果由人民共享。",
        "significance": "它有助于学生理解中国共产党人的初心使命和公共责任意识，形成服务人民、奉献社会的价值取向。",
        "source_publication": "党的二十大报告及相关重要论述",
        "url": "https://www.gov.cn/xinwen/2022-10/25/content_5721685.htm",
        "related_terms": ["以人民为中心的发展思想", "共同富裕", "民生福祉"],
        "keywords": ["人民至上", "以人民为中心", "民生", "公共服务", "美好生活"],
        "source_scope": "expanded-positive",
    },
    {
        "term": "全过程人民民主",
        "book": "《习概》《政治学概论》",
        "proposer": "中国共产党",
        "proposed_time": "新时代民主政治建设中系统阐述",
        "proposed_context": "围绕发展社会主义民主政治、保障人民当家作主提出并不断完善。",
        "meaning": "全过程人民民主强调民主选举、民主协商、民主决策、民主管理、民主监督各环节贯通，注重人民依法有序参与国家和社会治理。",
        "significance": "它有助于学生理解社会主义民主政治的制度优势，增强公共参与意识、法治意识和责任意识。",
        "source_publication": "《中国的民主》白皮书及党的二十大报告",
        "url": "https://www.gov.cn/zhengce/2021-12/04/content_5655727.htm",
        "related_terms": ["人民当家作主", "法治中国", "基层治理"],
        "keywords": ["全过程人民民主", "民主协商", "基层治理", "人民当家作主"],
        "source_scope": "expanded-positive",
    },
    {
        "term": "法治中国",
        "book": "《思想道德与法治》《习近平法治思想学习纲要》",
        "proposer": "中国共产党",
        "proposed_time": "全面依法治国实践中持续推进",
        "proposed_context": "围绕建设中国特色社会主义法治体系、建设社会主义法治国家的总体目标提出。",
        "meaning": "法治中国强调科学立法、严格执法、公正司法、全民守法共同推进，把国家各方面工作纳入法治轨道。",
        "significance": "它是大学生提升法治素养、树立规则意识、依法参与社会生活的重要学习主题。",
        "source_publication": "《法治中国建设规划（2020-2025年）》及习近平法治思想相关资料",
        "url": "https://www.gov.cn/zhengce/2021-01/10/content_5578659.htm",
        "related_terms": ["全面依法治国", "宪法精神", "法治素养"],
        "keywords": ["法治中国", "全面依法治国", "宪法", "法治素养", "规则意识"],
        "source_scope": "expanded-positive",
    },
    {
        "term": "教育强国",
        "book": "《习近平关于教育的重要论述》《教育学原理》",
        "proposer": "中国共产党",
        "proposed_time": "新时代教育现代化进程中持续推进",
        "proposed_context": "围绕建设社会主义现代化强国的基础性、战略性支撑，把教育摆在优先发展的战略位置。",
        "meaning": "教育强国强调以高质量教育体系支撑人的全面发展、科技创新、人才培养和现代化建设。",
        "significance": "它把学生个人成长同国家人才培养和民族复兴联系起来，有助于增强学习动力、专业责任和报国意识。",
        "source_publication": "全国教育大会及教育强国建设相关权威文件",
        "url": "",
        "related_terms": ["立德树人", "科教兴国战略", "人才强国战略"],
        "keywords": ["教育强国", "高质量教育", "人才培养", "立德树人", "教育现代化"],
        "source_scope": "expanded-positive",
    },
    {
        "term": "科技自立自强",
        "book": "《习概》《科技创新与国家发展》",
        "proposer": "中国共产党",
        "proposed_time": "新时代科技创新实践中持续强调",
        "proposed_context": "面对新一轮科技革命和产业变革，国家把科技自立自强作为现代化建设的重要支撑。",
        "meaning": "科技自立自强强调增强原始创新能力、关键核心技术攻关能力和高水平科技人才培养能力，以科技创新支撑高质量发展。",
        "significance": "它能引导学生把专业学习、创新实践和国家需要结合起来，理解青年在科技强国建设中的责任。",
        "source_publication": "党的二十大报告及科技创新相关重要论述",
        "url": "https://www.gov.cn/xinwen/2022-10/25/content_5721685.htm",
        "related_terms": ["新质生产力", "创新驱动发展战略", "教育强国"],
        "keywords": ["科技自立自强", "科技创新", "关键核心技术", "创新驱动", "新质生产力"],
        "source_scope": "expanded-positive",
    },
    {
        "term": "劳动精神",
        "book": "《思想道德与法治》《新时代劳动教育论》",
        "proposer": "中华民族劳动实践和新时代劳动教育",
        "proposed_time": "长期实践形成，新时代劳动教育中进一步强调",
        "proposed_context": "围绕崇尚劳动、尊重劳动、热爱劳动和提升实践能力的育人要求提出。",
        "meaning": "劳动精神强调诚实劳动、勤勉奋斗、精益求精和创造价值，倡导在劳动中认识社会、锤炼品格、服务他人。",
        "significance": "它有助于学生克服浮躁心态，把个人理想落实到踏实学习、专业训练和社会实践中。",
        "source_publication": "新时代大中小学劳动教育相关文件",
        "url": "",
        "related_terms": ["工匠精神", "实践育人", "职业道德"],
        "keywords": ["劳动精神", "劳动教育", "实践育人", "职业道德", "奋斗"],
        "source_scope": "expanded-positive",
    },
    {
        "term": "工匠精神",
        "book": "《思想道德与法治》《职业发展与就业指导》",
        "proposer": "劳动实践和职业伦理建设",
        "proposed_time": "新时代产业升级和职业教育发展中广泛强调",
        "proposed_context": "围绕建设制造强国、质量强国和培养高素质技术技能人才的实践提出。",
        "meaning": "工匠精神强调执着专注、精益求精、一丝不苟、追求卓越，是职业道德、专业能力和责任意识的统一。",
        "significance": "它适合引导学生尊重专业、重视细节、提升本领，把职业选择同服务社会和国家发展结合起来。",
        "source_publication": "政府工作报告、职业教育和产业发展相关权威资料",
        "url": "",
        "related_terms": ["劳动精神", "职业道德", "高质量发展"],
        "keywords": ["工匠精神", "职业教育", "技能人才", "精益求精", "质量强国"],
        "source_scope": "expanded-positive",
    },
    {
        "term": "志愿服务精神",
        "book": "《思想道德与法治》《新时代公民道德建设实施纲要》",
        "proposer": "社会主义精神文明建设实践",
        "proposed_time": "新时代志愿服务制度化发展中不断深化",
        "proposed_context": "围绕培育时代新人、弘扬社会文明风尚和推进志愿服务制度化常态化提出。",
        "meaning": "志愿服务精神强调奉献、友爱、互助、进步，倡导在服务他人和社会中实现自我成长。",
        "significance": "它能引导学生把道德认知转化为行动，在社区服务、校园互助和社会实践中增强责任感。",
        "source_publication": "新时代公民道德建设和志愿服务相关文件",
        "url": "",
        "related_terms": ["社会公德", "实践育人", "责任担当"],
        "keywords": ["志愿服务", "奉献", "友爱", "互助", "社会实践", "文明实践"],
        "source_scope": "expanded-positive",
    },
    {
        "term": "网络文明",
        "book": "《思想道德与法治》《新时代公民道德建设实施纲要》",
        "proposer": "网络强国和精神文明建设实践",
        "proposed_time": "数字社会发展进程中持续推进",
        "proposed_context": "围绕提升全民网络素养、建设清朗网络空间和培育健康向上的网络文化提出。",
        "meaning": "网络文明强调依法上网、文明表达、理性交流、尊重他人和共同维护良好网络秩序。",
        "significance": "它适合引导学生在数字生活中守住道德和法治边界，提升媒介素养和公共表达能力。",
        "source_publication": "网络文明建设相关权威文件和公民道德建设资料",
        "url": "",
        "related_terms": ["法治素养", "媒介素养", "社会公德"],
        "keywords": ["网络文明", "网络素养", "清朗网络空间", "文明上网", "数字社会"],
        "source_scope": "expanded-positive",
    },
]

TERM_TEMPLATES = TERM_TEMPLATES + EXPANDED_TERM_TEMPLATES

UNSUITABLE_TERM_KEYWORDS = [
    "仇恨",
    "歧视",
    "色情",
    "赌博",
    "毒品",
    "诈骗",
    "传销",
    "极端主义",
    "恐怖主义",
    "自残",
    "低俗",
    "饭圈",
    "炫富",
    "恶意炒作",
    "网络暴力",
    "封建迷信",
]


def _normalize(text: Any) -> str:
    return str(text or "").strip().lower()


def _contains_any(text: str, keywords: list[str]) -> bool:
    lowered = _normalize(text)
    return any(keyword.lower() in lowered for keyword in keywords)


def _term_search_text(template: dict) -> str:
    return "\n".join(
        str(template.get(key, ""))
        for key in (
            "term",
            "book",
            "proposer",
            "proposed_time",
            "proposed_context",
            "meaning",
            "significance",
            "source_publication",
        )
    )


def _is_safe_term_template(template: dict) -> bool:
    required = ["term", "book", "meaning", "significance", "source_publication"]
    if any(not str(template.get(key, "")).strip() for key in required):
        return False
    if len(str(template.get("meaning", "")).strip()) < 24:
        return False
    if len(str(template.get("significance", "")).strip()) < 24:
        return False
    return not _contains_any(_term_search_text(template), UNSUITABLE_TERM_KEYWORDS)


def _read_meta() -> dict:
    if not TEACHING_SYNC_META_FILE.exists():
        return {}
    try:
        return json.loads(TEACHING_SYNC_META_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_meta(meta: dict) -> None:
    TEACHING_SYNC_META_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEACHING_SYNC_META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_stamp(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _days_since(value: str) -> int | None:
    parsed = _parse_stamp(value)
    if not parsed:
        return None
    return (datetime.now() - parsed).days


def _is_due(last_sync: str, interval_days: int) -> bool:
    days = _days_since(last_sync)
    return days is None or days >= interval_days


def _update_meta(section: str, result: dict) -> None:
    meta = _read_meta()
    now = _now_stamp()
    section_meta = {
        "last_sync": now,
        "last_count": int(result.get("count") or 0),
        "last_updated": bool(result.get("updated")),
        "last_message": str(result.get("message", "")),
    }
    meta[section] = section_meta
    meta["updated_at"] = now
    _write_meta(meta)


def get_sync_status() -> dict:
    meta = _read_meta()
    cases = meta.get("cases") or {}
    terms = meta.get("key_terms") or {}
    return {
        "ok": True,
        "cases": {
            "interval_days": CASE_AUTO_INTERVAL_DAYS,
            "last_sync": cases.get("last_sync", ""),
            "last_count": cases.get("last_count", 0),
            "due": _is_due(cases.get("last_sync", ""), CASE_AUTO_INTERVAL_DAYS),
        },
        "key_terms": {
            "interval_days": TERM_AUTO_INTERVAL_DAYS,
            "last_sync": terms.get("last_sync", ""),
            "last_count": terms.get("last_count", 0),
            "due": _is_due(terms.get("last_sync", ""), TERM_AUTO_INTERVAL_DAYS),
        },
    }


def _policy_text(item: dict) -> str:
    return " ".join(
        [
            str(item.get("title", "")),
            str(item.get("summary", "")),
            str(item.get("content", "")),
            " ".join(item.get("tags", []) or []),
        ]
    )


def _article_date(item: dict) -> str:
    return str(item.get("date", "") or item.get("published_at", "")[:10])


def _case_score(item: dict) -> int:
    text = _policy_text(item)
    score = int(item.get("sync_rank") or 0)
    high_value = [
        "习近平",
        "中国共产党",
        "党的十九大",
        "党建",
        "重要讲话",
        "民族复兴",
        "红色地标",
        "红军街",
        "革命烈士",
        "故居",
        "会址",
        "纪念馆",
        "长征",
        "精神",
        "青年",
        "基层",
        "乡村振兴",
        "科技报国",
        "中国式现代化",
        "一国两制",
    ]
    durable = ["系列", "专题", "纪实", "故事", "地标", "精神", "实践", "样本", "经验"]
    score += sum(4 for keyword in high_value if keyword in text)
    score += sum(2 for keyword in durable if keyword in text)
    score -= sum(3 for keyword in EXCLUDED_CASE_KEYWORDS if keyword in text)
    if len(str(item.get("content", ""))) >= 500:
        score += 3
    if str(item.get("url", "")).startswith(("https://www.news.cn/", "https://www.xinhuanet.com/")):
        score += 2
    return score


def _is_case_candidate(item: dict) -> bool:
    text = _policy_text(item)
    if not text.strip():
        return False
    if _contains_any(text, EXCLUDED_CASE_KEYWORDS):
        return False
    if _case_score(item) < 8:
        return False
    return _contains_any(
        text,
        [
            "习近平",
            "中国共产党",
            "红色",
            "革命",
            "烈士",
            "精神",
            "发展",
            "创新",
            "治理",
            "法治",
            "生态",
            "科技",
            "教育",
            "乡村",
            "合作",
            "产业",
            "安全",
            "民生",
            "改革",
            "现代化",
            "绿色",
            "强国",
            "振兴",
        ],
    )


def _pick_case_category(text: str) -> str:
    for category, keywords in CASE_CATEGORY_RULES:
        if _contains_any(text, keywords):
            return category
    return "改革开放"


def _case_topics(category: str) -> list[str]:
    mapping = {
        "党史事件": ["党的领导", "理想信念", "历史主动精神"],
        "红色场馆": ["红色基因", "革命精神", "实践育人"],
        "先进人物": ["榜样力量", "责任担当", "初心使命"],
        "脱贫攻坚": ["人民立场", "共同富裕", "乡村振兴"],
        "科技报国": ["科技创新", "使命担当", "强国建设"],
        "生态文明": ["绿色发展", "人与自然和谐共生", "责任意识"],
        "法治教育": ["法治思维", "规则意识", "国家安全"],
        "乡村振兴": ["人民立场", "乡村振兴", "共同富裕"],
        "改革开放": ["高质量发展", "开放合作", "中国式现代化"],
    }
    return mapping.get(category, ["中国式现代化", "责任担当", "实践育人"])


def _now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _case_questions(category: str, title: str) -> list[str]:
    mapping = {
        "党史事件": [
            f"从{title}中可以怎样理解中国共产党为什么能？",
            "这类党史材料对当代青年坚定理想信念有什么启示？",
        ],
        "红色场馆": [
            f"{title}为什么适合作为红色研学或课堂案例？",
            "红色地标如何把历史记忆转化为现实行动力量？",
        ],
        "先进人物": [
            f"{title}体现了怎样的初心使命和责任担当？",
            "青年学生应如何把榜样力量转化为日常学习和实践？",
        ],
        "脱贫攻坚": [
            f"{title}体现了怎样的人民立场和共同富裕追求？",
            "从基层实践中可以怎样理解中国式现代化？",
        ],
        "科技报国": [
            f"{title}体现了怎样的科技报国精神？",
            "青年学生应如何把个人成长与科技强国建设结合起来？",
        ],
        "生态文明": [
            f"{title}对理解绿色发展有哪些启示？",
            "在校园和日常生活中，怎样把生态文明理念落到行动上？",
        ],
        "法治教育": [
            f"{title}说明了法治建设中的哪些关键问题？",
            "为什么规则意识和国家安全意识需要在青年阶段强化？",
        ],
        "乡村振兴": [
            f"{title}与人民立场、共同富裕之间有什么联系？",
            "青年学生可以怎样理解乡村振兴的时代价值？",
        ],
        "改革开放": [
            f"{title}反映了新时代中国发展的哪些特点？",
            "如何从现实新闻中理解中国式现代化的实践路径？",
        ],
    }
    return mapping.get(category, [f"{title}反映了怎样的时代主题？", "这则时政材料对课堂思政学习有什么启发？"])


def _case_teaching_value(category: str) -> str:
    mapping = {
        "党史事件": "有助于引导学生从具体历史节点理解党的领导、理论创新和历史主动精神，增强道路自信、理论自信和制度自信。",
        "红色场馆": "有助于把红色资源转化为可感可学的课堂材料，引导学生在真实地标与具体人物中理解革命精神和理想信念。",
        "先进人物": "有助于通过真实人物事迹引导学生理解初心使命、责任担当和奉献精神，形成见贤思齐的价值认同。",
        "脱贫攻坚": "有助于引导学生理解人民立场、共同富裕和基层治理的实践逻辑，增强服务社会与关注民生的责任感。",
        "科技报国": "有助于引导学生理解科技自立自强与国家发展的紧密联系，增强使命意识、创新意识和报国情怀。",
        "生态文明": "有助于引导学生树立绿色发展观、生态责任观和可持续发展意识，把个人行为与国家生态文明建设联系起来。",
        "法治教育": "有助于引导学生理解依法治国、总体国家安全观和社会治理的现实意义，增强规则意识与底线思维。",
        "乡村振兴": "有助于引导学生理解人民立场、共同富裕和乡村振兴的实践逻辑，增强服务社会与关注民生的责任感。",
        "改革开放": "有助于引导学生从现实发展成就中理解中国式现代化、高质量发展和开放合作，增强道路自信与制度自信。",
    }
    return mapping.get(category, "有助于引导学生把时政事实与理论学习结合起来，增强历史主动精神和现实责任意识。")


def _case_recommended_usage(category: str) -> str:
    mapping = {
        "党史事件": "适合用于“党的领导”“马克思主义中国化时代化”“理想信念教育”等主题课堂，可作为导入材料或课堂讨论案例。",
        "红色场馆": "适合用于红色研学、实践教学和主题班会，可引导学生围绕地标、人物、精神三条线索开展探究。",
        "先进人物": "适合用于榜样教育、青年使命和职业理想主题课堂，可结合人物选择、时代背景和现实行动进行讨论。",
        "脱贫攻坚": "适合用于“人民至上”“共同富裕”“乡村振兴”主题课堂，可引导学生从基层实践理解国家战略。",
        "科技报国": "适合用于“科技强国”“创新驱动发展”“青年使命”等主题课堂，可结合科研人物、产业升级和国家战略展开讨论。",
        "生态文明": "适合用于“生态文明建设”“绿色发展”“人与自然和谐共生”等主题课堂，可结合生活实践和地方治理展开讨论。",
        "法治教育": "适合用于“全面依法治国”“国家安全教育”“规则意识养成”等主题课堂，可结合典型治理场景开展研讨。",
        "乡村振兴": "适合用于“人民立场”“共同富裕”“乡村振兴”主题课堂，可引导学生从国家战略与基层实践两个层面理解问题。",
        "改革开放": "适合用于“高质量发展”“改革开放”“中国式现代化”等主题课堂，可作为课前导入、课堂研讨或课后写作素材。",
    }
    return mapping.get(category, "适合用于课堂导入、时政讨论和课后反思写作。")


def _build_case_item(item: dict) -> dict:
    text = _policy_text(item)
    category = _pick_case_category(text)
    topics = _case_topics(category)
    title = str(item.get("title", "")).strip()
    source_line = str(item.get("source", "")).strip() or "新闻来源待补充"
    url = str(item.get("url", "")).strip()
    source = f"时政自动转化；新闻来源：{source_line}" + (f"；原文链接：{url}" if url else "")
    raw_summary = str(item.get("summary", "")).strip()
    raw_content = str(item.get("content", "")).strip()
    if len(raw_summary) < 20:
        raw_summary = f"{title}。{raw_content[:120]}" if raw_content else title
    summary = raw_summary[:180]
    fact_excerpt = raw_content[:520] if raw_content else raw_summary
    content = (
        f"【事实材料】\n{fact_excerpt}\n\n"
        f"【案例转化】\n该材料发布于{item.get('date', '') or '近期'}，来源为{source_line}。"
        f"它不是单纯新闻摘录，而是可以沉淀为“{category}”主题的教学案例：一方面有真实事件、人物或政策场景作支撑，"
        f"另一方面能够与{'、'.join(topics[:2])}等思政教学主题形成对应，适合引导学生从现实材料中理解理论、从具体案例中形成价值判断。"
    ).strip()
    return {
        "title": title,
        "category": category,
        "era": "新时代",
        "summary": summary,
        "content": content,
        "teaching_value": _case_teaching_value(category),
        "recommended_usage": _case_recommended_usage(category),
        "teaching_topics": topics,
        "discussion_questions": _case_questions(category, item.get("title", "").strip()),
        "tags": ["时政转化", "自动同步", category] + [tag for tag in (item.get("tags") or []) if tag],
        "source": source,
        "sync_origin": "current-politics-auto",
        "synced_at": _now_stamp(),
        "case_rank": _case_score(item),
    }


def _collect_case_candidates(politics: list[dict]) -> list[dict]:
    candidates = [item for item in politics if _is_case_candidate(item)]
    candidates.sort(key=lambda item: (_article_date(item), _case_score(item), str(item.get("id", ""))), reverse=True)
    return candidates[:CASE_LIMIT]


def _case_sync_response(created: list[dict], skipped: list[dict]) -> dict:
    return {
        "ok": True,
        "updated": bool(created),
        "count": len(created),
        "message": (
            f"\u6848\u4f8b\u540c\u6b65\u5b8c\u6210\uff0c\u5df2\u66f4\u65b0 {len(created)} \u6761\u6559\u5b66\u6848\u4f8b\u3002"
            if created
            else "\u6848\u4f8b\u540c\u6b65\u5b8c\u6210\uff0c\u5f53\u524d\u6700\u65b0\u65f6\u653f\u4e2d\u6682\u65e0\u9002\u5408\u8f6c\u5316\u7684\u6559\u5b66\u6848\u4f8b\u3002"
        ),
        "items": created,
        "skipped": skipped,
    }


def _build_term_payload(template: dict) -> dict:
    return {
        "term": template["term"],
        "book": template["book"],
        "proposer": template["proposer"],
        "proposed_time": template["proposed_time"],
        "proposed_context": template["proposed_context"],
        "meaning": template["meaning"],
        "significance": template["significance"],
        "source_publication": template["source_publication"],
        "url": template["url"],
        "related_terms": template["related_terms"],
        "sync_origin": "current-politics-auto",
        "synced_at": _now_stamp(),
        "source_scope": template.get("source_scope", "policy-current"),
    }


def _term_sync_response(matched: list[dict]) -> dict:
    return {
        "ok": True,
        "updated": bool(matched),
        "count": len(matched),
        "message": (
            f"\u8bcd\u6761\u540c\u6b65\u5b8c\u6210\uff0c\u5df2\u66f4\u65b0 {len(matched)} \u6761\u6b63\u5411\u601d\u653f\u5173\u952e\u8bcd\u6761\u3002"
            if matched
            else "\u8bcd\u6761\u540c\u6b65\u5b8c\u6210\uff0c\u5f53\u524d\u6682\u65e0\u7b26\u5408\u8bfe\u5802\u4f7f\u7528\u548c\u6b63\u5411\u7b5b\u9009\u8981\u6c42\u7684\u65b0\u8bcd\u6761\u3002"
        ),
        "items": matched,
    }


def _not_due_response(section: str, last_sync: str, interval_days: int) -> dict:
    label = "经典案例" if section == "cases" else "思政关键词条"
    cadence = "每日" if section == "cases" else "每周"
    return {
        "ok": True,
        "updated": False,
        "count": 0,
        "last_sync": last_sync,
        "interval_days": interval_days,
        "message": f"{label}{cadence}自动检查已完成，最近同步时间：{last_sync}。",
        "items": [],
        "skipped": [],
    }


def _refresh_current_politics(force: bool) -> dict:
    try:
        return news_service.refresh_current_politics(force=force)
    except Exception as exc:
        return {"ok": False, "message": f"时政刷新失败，已改用本地现有时政内容：{exc}"}


def _attach_refresh_notice(result: dict, refresh_result: dict) -> dict:
    if not refresh_result:
        return result
    result["politics_refresh"] = {
        "ok": bool(refresh_result.get("ok")),
        "updated": bool(refresh_result.get("updated")),
        "latest_date": refresh_result.get("latest_date", ""),
        "latest_title": refresh_result.get("latest_title", ""),
    }
    if not refresh_result.get("ok"):
        notice = refresh_result.get("message") or refresh_result.get("error") or "时政刷新失败，已使用本地内容。"
        result["message"] = f"{result.get('message', '')}（{notice}）"
    return result


def sync_cases_from_current_politics(force: bool = True, refresh_politics: bool = True) -> dict:
    refresh_result = _refresh_current_politics(force=force) if refresh_politics else {}
    politics = dm.get_current_politics()
    candidates = _collect_case_candidates(politics)
    skipped = []
    case_items = []
    for item in candidates:
        try:
            case_item = _build_case_item(item)
            case_items.append(case_item)
        except ValueError as exc:
            skipped.append({"title": item.get("title", ""), "reason": str(exc)})
    saved_items = dm.replace_auto_cases(case_items)
    created = [{"id": saved.get("id"), "title": saved.get("title")} for saved in saved_items]
    result = _case_sync_response(created, skipped)
    _attach_refresh_notice(result, refresh_result)
    _update_meta("cases", result)
    return result


def auto_sync_cases_if_due() -> dict:
    meta = _read_meta().get("cases") or {}
    last_sync = meta.get("last_sync", "")
    if not _is_due(last_sync, CASE_AUTO_INTERVAL_DAYS):
        return _not_due_response("cases", last_sync, CASE_AUTO_INTERVAL_DAYS)
    return sync_cases_from_current_politics(force=False, refresh_politics=True)


def sync_key_terms_from_current_politics(force: bool = True, refresh_politics: bool = True) -> dict:
    refresh_result = _refresh_current_politics(force=force) if refresh_politics else {}
    politics = dm.get_current_politics()
    existing_terms = {str(item.get("term", "")).strip() for item in dm.get_key_terms()}
    text = "\n".join(_policy_text(item) for item in politics[:20])
    matched = []
    seen_terms = set()
    for template in TERM_TEMPLATES:
        if not _is_safe_term_template(template):
            continue
        if not _contains_any(text, template["keywords"]):
            continue
        saved = dm.add_key_term(_build_term_payload(template))
        seen_terms.add(saved.get("term"))
        matched.append({"id": saved.get("id"), "term": saved.get("term"), "source_scope": saved.get("source_scope", "")})
        if len(matched) >= TERM_POLICY_MATCH_LIMIT:
            break
    if len(matched) < TERM_SYNC_LIMIT:
        expanded_candidates = [
            template
            for template in TERM_TEMPLATES
            if template.get("source_scope") == "expanded-positive"
        ]
        expanded_candidates.sort(key=lambda template: template.get("term") in existing_terms)
        for template in expanded_candidates:
            if len(matched) >= TERM_SYNC_LIMIT:
                break
            if not _is_safe_term_template(template):
                continue
            if template.get("term") in seen_terms:
                continue
            saved = dm.add_key_term(_build_term_payload(template))
            seen_terms.add(saved.get("term"))
            matched.append({"id": saved.get("id"), "term": saved.get("term"), "source_scope": saved.get("source_scope", "")})
    result = _term_sync_response(matched)
    _attach_refresh_notice(result, refresh_result)
    _update_meta("key_terms", result)
    return result


def auto_sync_key_terms_if_due() -> dict:
    meta = _read_meta().get("key_terms") or {}
    last_sync = meta.get("last_sync", "")
    if not _is_due(last_sync, TERM_AUTO_INTERVAL_DAYS):
        return _not_due_response("key_terms", last_sync, TERM_AUTO_INTERVAL_DAYS)
    return sync_key_terms_from_current_politics(force=False, refresh_politics=True)
