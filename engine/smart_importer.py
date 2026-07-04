import re
from pathlib import Path

try:
    import pdfplumber
    HAS_PDF = True
except Exception:
    HAS_PDF = False

from engine.docx_parser import parse_docx, save_content
from engine import data_manager as dm


CATEGORY_KEYWORDS = {
    "syllabus": ["大纲", "课时", "周次", "学时", "学期", "教学计划", "课程安排", "目录", "目 录"],
    "courseware": ["课件", "ppt", "PPT", "教案", "讲义", "幻灯片", "授课"],
    "references": ["参考", "书目", "文献", "索引", "推荐阅读"],
}

REFERENCE_TITLE_HINTS = ["参考书目", "推荐阅读", "参考文献", "文献目录", "书目"]
REFERENCE_META_HINTS = ["作者", "主编", "编著", "出版社", "出版", "ISBN", "版次", "书目"]
SYLLABUS_CONTENT_HINTS = ["教学目标", "教学重点", "教学难点", "课程安排", "考核方式", "学时分配", "教学要求"]
COURSEWARE_CONTENT_HINTS = ["课堂导入", "学习目标", "重点难点", "课堂小结", "思考题", "幻灯片", "PPT", "第1页"]


IDEOLOGY_LAW_SYLLABUS = """课程名称：思想道德与法治
适用对象：高等学校本专科学生
建议学时：48学时

一、课程性质与定位
《思想道德与法治》是落实立德树人根本任务的高校思想政治理论课必修课程。课程以马克思主义为指导，以习近平新时代中国特色社会主义思想为引领，围绕新时代大学生成长成才中的理想信念、人生价值、中国精神、社会主义核心价值观、道德修养和法治素养等核心问题，帮助学生夯实思想道德基础，提升法治意识和实践能力。

二、课程目标
1. 知识目标：理解人生观、价值观、理想信念、中国精神、社会主义核心价值观、社会主义道德和社会主义法治的基本理论。
2. 能力目标：能够运用马克思主义立场观点方法分析个人成长、社会责任、道德选择和法治实践中的现实问题。
3. 素养目标：坚定理想信念，厚植爱国情怀，增强社会责任感、道德判断力、法治意识和实践担当。

三、教学重点
1. 正确认识个人与社会、人生目的、人生态度和人生价值的关系。
2. 坚定马克思主义信仰、中国特色社会主义信念和中华民族伟大复兴信心。
3. 深刻理解中国精神、爱国主义、改革创新和社会主义核心价值观。
4. 把握社会主义道德的核心、原则、规范和实践要求。
5. 理解习近平法治思想、社会主义法律的特征运行和全面依法治国的实践要求。

四、教学难点
1. 引导学生把个人理想融入国家前途、民族命运和人民幸福。
2. 引导学生在多元社会思潮中形成正确价值判断。
3. 引导学生把道德认知、法治意识转化为日常行为和社会实践。

五、教学内容与学时安排
绪论 担当复兴大任 成就时代新人（2学时）
教学要点：认识新时代大学生的历史方位和使命担当；理解思想道德素质与法治素养对成长成才的重要意义。

第一章 领悟人生真谛 把握人生方向（7学时）
第一节 人生观是对人生的总看法
第二节 正确的人生观
第三节 创造有意义的人生
教学要点：理解人的本质、人生目的、人生态度和人生价值；能够辨析拜金主义、享乐主义、极端个人主义等错误人生观；引导学生在服务人民、奉献社会中成就出彩人生。

第二章 追求远大理想 坚定崇高信念（7学时）
第一节 理想信念的内涵及重要性
第二节 坚定信仰信念信心
第三节 在实现中国梦的实践中放飞青春梦想
教学要点：理解理想信念的内涵、类型和作用；坚定马克思主义信仰、中国特色社会主义信念、中华民族伟大复兴信心；把个人理想同中国梦结合起来。

第三章 继承优良传统 弘扬中国精神（7学时）
第一节 中国精神是兴国强国之魂
第二节 做新时代的忠诚爱国者
第三节 让改革创新成为青春远航的动力
教学要点：理解中国精神的丰富内涵；把握爱国主义的时代要求；理解改革创新精神对新时代青年成长的重要意义。

第四章 明确价值要求 践行价值准则（6学时）
第一节 全体人民共同的价值追求
第二节 社会主义核心价值观的显著特征
第三节 积极践行社会主义核心价值观
教学要点：理解社会主义核心价值观的基本内容、时代意义和实践要求；引导学生把价值准则落实到学习生活、职业发展和社会交往中。

第五章 遵守道德规范 锤炼道德品格（9学时）
第一节 社会主义道德的核心与原则
第二节 吸收借鉴优秀道德成果
第三节 投身崇德向善的道德实践
教学要点：理解社会主义道德建设的核心和原则；继承中华传统美德、弘扬中国革命道德、借鉴人类文明优秀道德成果；掌握社会公德、职业道德、家庭美德、个人品德的实践要求。

第六章 学习法治思想 提升法治素养（8学时）
第一节 社会主义法律的特征和运行
第二节 坚持全面依法治国
第三节 维护宪法权威
第四节 自觉尊法学法守法用法
教学要点：理解社会主义法律的本质特征和运行机制；学习习近平法治思想；理解宪法精神和全面依法治国要求；提升法治思维和依法办事能力。

实践教学与综合复习（2学时）
教学要点：围绕红色资源、志愿服务、法治实践、道德观察、主题调研等开展课堂展示或实践交流，完成课程总结与综合提升。

六、教学方法
采用专题讲授、案例教学、课堂讨论、情景分析、实践研学、主题展示和线上线下混合学习等方式，突出问题导向、价值引领和实践转化。

七、考核方式
建议采用过程性评价与终结性评价相结合的方式。过程性评价可包括课堂表现、主题讨论、实践报告、学习笔记、小组展示等；终结性评价可采用课程论文、闭卷或开卷测试、综合展示等形式。建议过程性评价占60%，终结性评价占40%，具体比例可根据教学安排调整。

八、教学资源
1. 《思想道德与法治（2023年版）》教材。
2. 习近平新时代中国特色社会主义思想相关重要文献。
3. 新华社、人民网、学习强国等权威时政与案例资源。
4. 红色场馆、法治教育基地、志愿服务和社会实践资源。
"""


def section_text(sec, limit=16):
    lines = []
    for item in sec.get("content", []):
        text = normalize_space(item.get("text", ""))
        if text:
            lines.append(text)
        if len(lines) >= limit:
            break
    return "\n".join(lines)


def section_lines(sec, limit=80):
    lines = []
    for item in sec.get("content", []):
        text = normalize_space(item.get("text", ""))
        if text:
            lines.append(text)
        if len(lines) >= limit:
            break
    return lines


def looks_like_reference_line(text):
    text = normalize_space(text)
    if not text:
        return False
    if any(token in text for token in REFERENCE_META_HINTS):
        return True
    if re.search(r"\bISBN\b", text, flags=re.IGNORECASE):
        return True
    if re.search(r"[A-Za-z].*\d{4}", text):
        return True
    return False


def looks_like_outline_line(text):
    text = normalize_space(text)
    if not text:
        return False
    if re.match(r"^(第[一二三四五六七八九十百千万0-9]+[章节讲单元]|[0-9]+[.、])", text):
        return True
    if text.startswith(("专题", "模块", "单元", "绪论", "导论")):
        return True
    return False


def classify_section(ch_heading, sec_heading, sec):
    heading_text = normalize_space(" ".join([ch_heading or "", sec_heading or ""]))
    body = section_text(sec)
    body_lines = section_lines(sec)
    scores = {"references": 0, "syllabus": 0, "courseware": 0}

    for category, words in CATEGORY_KEYWORDS.items():
        for word in words:
            if word and word in heading_text:
                scores[category] += 6
            if word and word in body:
                scores[category] += 2

    ref_line_hits = sum(1 for line in body_lines[:20] if looks_like_reference_line(line))
    if ref_line_hits >= 2:
        scores["references"] += 6

    outline_hits = sum(1 for line in body_lines[:30] if looks_like_outline_line(line))
    syllabus_hits = sum(1 for word in SYLLABUS_CONTENT_HINTS if word in body)
    courseware_hits = sum(1 for word in COURSEWARE_CONTENT_HINTS if word in body)

    if outline_hits >= 3:
        scores["syllabus"] += 4
    if syllabus_hits >= 2:
        scores["syllabus"] += 5
    if courseware_hits >= 2:
        scores["courseware"] += 5

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]
    return best_category if best_score >= 5 else None


def normalize_space(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def categorize(text):
    text = normalize_space(text)
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                return cat
    return None


def parse_pdf(fp, book_id):
    if not HAS_PDF:
        return None
    chapters = []
    with pdfplumber.open(fp) as pdf:
        for idx, pg in enumerate(pdf.pages, start=1):
            text = pg.extract_text()
            if not text:
                continue
            content = []
            for line in text.split("\n"):
                line = normalize_space(line)
                if not line:
                    continue
                content.append({
                    "text": line,
                    "style": "Normal",
                    "level": 0,
                    "bold": False,
                    "italic": False,
                })
            if content:
                chapters.append({
                    "heading": f"第{idx}页",
                    "level": 1,
                    "sections": [{"heading": "", "level": 2, "content": content}],
                })
    title = Path(fp).stem
    save_content(book_id, title, chapters)
    return {"id": book_id, "title": title, "chapters": chapters}


def first_nonempty_lines(layout, limit=18):
    lines = []
    for ch in layout.get("chapters", []):
        heading = normalize_space(ch.get("heading", ""))
        if heading:
            lines.append(heading)
        for sec in ch.get("sections", []):
            sec_heading = normalize_space(sec.get("heading", ""))
            if sec_heading:
                lines.append(sec_heading)
            for item in sec.get("content", []):
                text = normalize_space(item.get("text", ""))
                if text:
                    lines.append(text)
                if len(lines) >= limit:
                    return lines
    return lines


def build_reference_text(layout, title, sections=None):
    lines = []
    if sections:
        for sec in sections:
            heading = normalize_space(sec.get("heading", ""))
            if heading:
                lines.append(heading)
            lines.extend(section_lines(sec, 24))
    if not lines:
        lines = first_nonempty_lines(layout, 20)
    selected = []
    for line in lines:
        if any(hint in line for hint in REFERENCE_TITLE_HINTS):
            selected.append(line)
            continue
        if looks_like_reference_line(line):
            selected.append(line)
    if not selected:
        selected = lines[:8]
    result = [title] if title else []
    result.extend(selected)
    return "\n".join(dict.fromkeys([x for x in result if x]))


def _layout_plain_text(layout, limit=12000):
    lines = first_nonempty_lines(layout, 120)
    text = "\n".join(lines)
    return text[:limit]


def build_syllabus_text(layout, sections=None, title=""):
    source_text = title + "\n" + _layout_plain_text(layout)
    if "思想道德与法治" in source_text or "德法" in source_text:
        return IDEOLOGY_LAW_SYLLABUS
    if sections:
        outline = []
        for idx, sec in enumerate(sections, start=1):
            sec_title = normalize_space(sec.get("heading", "")) or f"第{idx}部分"
            outline.append(sec_title)
            for line in section_lines(sec, 80):
                if looks_like_outline_line(line) or any(word in line for word in SYLLABUS_CONTENT_HINTS):
                    outline.append(f"  - {line}")
        if len(outline) >= 12:
            return "\n".join(outline[:300])
    outline = []
    for ci, ch in enumerate(layout.get("chapters", []), start=1):
        chapter_title = normalize_space(ch.get("heading", "")) or f"第{ci}章"
        outline.append(chapter_title)
        for si, sec in enumerate(ch.get("sections", []), start=1):
            sec_title = normalize_space(sec.get("heading", ""))
            if sec_title:
                outline.append(f"  {si}. {sec_title}")
    return "\n".join(outline[:300])


def extract_textbook_chapters(layout, excluded_sections=None):
    chapters = []
    excluded_sections = excluded_sections or set()
    for ci, ch in enumerate(layout.get("chapters", []), start=1):
        chapter_heading = normalize_space(ch.get("heading", "")) or f"第{ci}章"
        sections = []
        leading_content = []
        for si, sec in enumerate(ch.get("sections", []), start=1):
            if (ci - 1, si - 1) in excluded_sections:
                continue
            sec_heading = normalize_space(sec.get("heading", ""))
            content = []
            for item in sec.get("content", []):
                text = normalize_space(item.get("text", ""))
                if not text:
                    continue
                content.append({
                    "text": text,
                    "style": item.get("style", "Normal"),
                    "level": item.get("level", 0),
                    "bold": bool(item.get("bold")),
                    "italic": bool(item.get("italic")),
                })
            if not content:
                continue
            if sec_heading:
                sections.append({
                    "heading": sec_heading,
                    "level": sec.get("level", 2),
                    "content": content,
                })
            else:
                leading_content.extend(content)
        if leading_content:
            sections.insert(0, {"heading": "", "level": 2, "content": leading_content})
        if sections:
            chapters.append({"heading": chapter_heading, "level": 1, "sections": sections})
    return chapters


def _load_layout(filepath, book_id):
    ext = Path(filepath).suffix.lower()
    if ext == ".docx":
        layout, _ = parse_docx(filepath, book_id)
        return layout, None
    if ext == ".pdf":
        layout = parse_pdf(filepath, book_id)
        if layout is None:
            return None, "PDF support requires pdfplumber"
        return layout, None
    return None, "Unsupported: " + ext


def _categorize_layout(layout):
    categorized = {"textbook": [], "courseware": [], "syllabus": [], "references": []}
    excluded_sections = set()
    for ci, ch in enumerate(layout.get("chapters", [])):
        ch_heading = normalize_space(ch.get("heading", ""))
        for si, sec in enumerate(ch.get("sections", [])):
            sec_heading = normalize_space(sec.get("heading", ""))
            target = categorize(sec_heading) or categorize(ch_heading) or classify_section(ch_heading, sec_heading, sec)
            if target:
                categorized[target].append(sec)
                excluded_sections.add((ci, si))

    categorized["references_text"] = build_reference_text(layout, layout.get("title", ""), categorized["references"])
    categorized["syllabus_text"] = build_syllabus_text(layout, categorized["syllabus"], layout.get("title", ""))
    categorized["textbook_chapters"] = extract_textbook_chapters(layout, excluded_sections)
    return categorized


def _save_reference_resource(result, categorized, title):
    references_text = categorized.get("references_text", "")
    if not references_text:
        return
    reference_title = title + " \u53c2\u8003\u4e66\u76ee"
    reference_payload = {
        "title": reference_title,
        "author": "\u6587\u6863\u63d0\u53d6",
        "publisher": "",
        "year": "",
        "description": references_text[:500],
        "file_path": "",
    }
    existing_reference = dm.find_reference_by_title(reference_title)
    item = dm.update_reference(existing_reference["id"], reference_payload) if existing_reference else dm.add_reference(reference_payload)
    result["references"] = 1
    result["items"]["references"] = item.get("id")


def _save_syllabus_resource(result, categorized, title):
    syllabus_text = categorized.get("syllabus_text", "")
    if not syllabus_text:
        return
    syllabus_title = title + " \u6559\u5b66\u5927\u7eb2"
    syllabus_payload = {
        "title": syllabus_title,
        "semester": "\u5f53\u524d\u5b66\u671f",
        "total_hours": 48,
        "content": syllabus_text,
    }
    existing_syllabus = dm.find_syllabus_by_title(syllabus_title)
    item = dm.update_syllabus(existing_syllabus["id"], syllabus_payload) if existing_syllabus else dm.add_syllabus(syllabus_payload)
    result["syllabus"] = 1
    result["items"]["syllabus"] = item.get("id")


def _save_courseware_resources(result, categorized, title):
    if not categorized["courseware"]:
        return
    ids = []
    for sec in categorized["courseware"]:
        chapter = sec.get("heading", "\u8bfe\u4ef6")
        desc = "\n".join(p["text"] for p in sec.get("content", []))[:200]
        payload = {
            "title": title + "-" + chapter,
            "chapter": chapter,
            "description": desc,
        }
        existing_courseware = dm.find_courseware_by_title(payload["title"])
        item = dm.update_courseware(existing_courseware["id"], payload) if existing_courseware else dm.add_courseware(payload)
        ids.append(item.get("id"))
    result["courseware"] = len(ids)
    result["items"]["courseware"] = ids


def _save_textbook_resource(result, categorized, title, book_id, now):
    textbook_chapters = categorized.get("textbook_chapters", [])
    final_book_id = book_id or ("tb_" + now)
    existing_textbook = dm.find_textbook_by_name(title)
    if existing_textbook:
        final_book_id = existing_textbook["id"]

    if textbook_chapters and final_book_id:
        save_content(final_book_id, title, textbook_chapters)

    if textbook_chapters or final_book_id:
        payload = {
            "name": title,
            "author": "\u667a\u80fd\u5bfc\u5165",
            "publisher": "",
            "year": "",
            "description": "\u667a\u80fd\u5bfc\u5165: " + title,
            "file_path": "",
            "has_content": True,
        }
        item = dm.update_textbook(final_book_id, payload) if existing_textbook else dm.add_textbook({"id": final_book_id, **payload})
        result["textbook"] = max(1, len(textbook_chapters))
        result["items"]["textbook"] = item.get("id")


def smart_import(filepath, book_id=None):
    book_id = book_id or ("tb_" + dm._make_id())
    layout, error = _load_layout(filepath, book_id)
    if error:
        return {"ok": False, "error": error}
    categorized = _categorize_layout(layout)

    return {
        "ok": True,
        "book_id": book_id,
        "title": layout.get("title", ""),
        "chapters": len(layout.get("chapters", [])),
        "categorized": categorized,
    }


def save_categorized(categorized, title, book_id=None):
    from datetime import datetime

    now = datetime.now().strftime("%Y%m%d%H%M%S")
    result = {"items": {}}
    _save_reference_resource(result, categorized, title)
    _save_syllabus_resource(result, categorized, title)
    _save_courseware_resources(result, categorized, title)
    _save_textbook_resource(result, categorized, title, book_id, now)
    return result
