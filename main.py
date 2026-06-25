import os
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from engine import data_manager as dm
from engine import ai_service as ai

app = FastAPI(title="思政教学程序", version="1.0.0")

ROOT = Path(__file__).parent

app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")


# ── 主页面 ──
@app.get("/", response_class=HTMLResponse)
async def index():
  try:
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)
  except Exception as e:
    return HTMLResponse(f"<h1>加载失败</h1><p>{e}</p>", status_code=500)


# ── 通用文件上传 ──
@app.post("/api/upload")
async def upload_file(data: dict):
  """接收 base64 编码的文件，不需要 python-multipart"""
  try:
    import base64
    upload_dir = ROOT / "uploads"
    upload_dir.mkdir(exist_ok=True)
    filename = data.get("filename", "unnamed")
    content_b64 = data.get("content", "")
    content = base64.b64decode(content_b64)
    dest = upload_dir / filename
    dest.write_bytes(content)
    return {"file_path": str(dest)}
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


# ════════════════════════════════════════════
#  课内知识
# ════════════════════════════════════════════
@app.get("/api/textbooks")
async def list_textbooks():
  try:
    return dm.get_textbooks()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/textbooks")
async def create_textbook(item: dict):
  try:
    return dm.add_textbook(item)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/textbooks/{item_id}")
async def update_textbook(item_id: str, item: dict):
  result = dm.update_textbook(item_id, item)
  if not result:
    raise HTTPException(status_code=404, detail="未找到该教材")
  return result

@app.delete("/api/textbooks/{item_id}")
async def remove_textbook(item_id: str):
  try:
    dm.delete_textbook(item_id)
    return {"ok": True}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# ── 课件 ──
@app.get("/api/courseware")
async def list_courseware():
  try:
    return dm.get_courseware()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/courseware")
async def create_courseware(item: dict):
  try:
    return dm.add_courseware(item)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/courseware/{item_id}")
async def update_courseware(item_id: str, item: dict):
  result = dm.update_courseware(item_id, item)
  if not result:
    raise HTTPException(status_code=404, detail="未找到该课件")
  return result

@app.delete("/api/courseware/{item_id}")
async def remove_courseware(item_id: str):
  try:
    dm.delete_courseware(item_id)
    return {"ok": True}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# ── 教学大纲 ──
@app.get("/api/syllabus")
async def list_syllabus():
  try:
    return dm.get_syllabus()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/syllabus")
async def create_syllabus(item: dict):
  try:
    return dm.add_syllabus(item)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/syllabus/{item_id}")
async def update_syllabus(item_id: str, item: dict):
  result = dm.update_syllabus(item_id, item)
  if not result:
    raise HTTPException(status_code=404, detail="未找到该大纲")
  return result

@app.delete("/api/syllabus/{item_id}")
async def remove_syllabus(item_id: str):
  try:
    dm.delete_syllabus(item_id)
    return {"ok": True}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# ── 参考书目 ──
@app.get("/api/references")
async def list_references():
  try:
    return dm.get_references()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/references")
async def create_reference(item: dict):
  try:
    return dm.add_reference(item)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/references/{item_id}")
async def update_reference(item_id: str, item: dict):
  result = dm.update_reference(item_id, item)
  if not result:
    raise HTTPException(status_code=404, detail="未找到该参考书")
  return result

@app.delete("/api/references/{item_id}")
async def remove_reference(item_id: str):
  try:
    dm.delete_reference(item_id)
    return {"ok": True}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# ════════════════════════════════════════════
#  时政
# ════════════════════════════════════════════
@app.get("/api/current-politics")
async def list_politics():
  try:
    return dm.get_current_politics()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/current-politics")
async def create_politics(item: dict):
  try:
    return dm.add_current_politics(item)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/current-politics/{item_id}")
async def update_politics(item_id: str, item: dict):
  result = dm.update_current_politics(item_id, item)
  if not result:
    raise HTTPException(status_code=404, detail="未找到该时政条目")
  return result

@app.delete("/api/current-politics/{item_id}")
async def remove_politics(item_id: str):
  try:
    dm.delete_current_politics(item_id)
    return {"ok": True}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# ════════════════════════════════════════════
#  案例
# ════════════════════════════════════════════
@app.get("/api/cases")
async def list_cases(category: str = "", era: str = "", keyword: str = ""):
  try:
    return dm.get_cases(category, era, keyword)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cases")
async def create_case(item: dict):
  try:
    return dm.add_case(item)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/cases/{item_id}")
async def update_case(item_id: str, item: dict):
  result = dm.update_case(item_id, item)
  if not result:
    raise HTTPException(status_code=404, detail="未找到该案例")
  return result

@app.delete("/api/cases/{item_id}")
async def remove_case(item_id: str):
  try:
    dm.delete_case(item_id)
    return {"ok": True}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# ════════════════════════════════════════════
#  关键词条
# ════════════════════════════════════════════
@app.get("/api/key-terms")
async def list_key_terms():
  try:
    return dm.get_key_terms()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/key-terms")
async def create_key_term(item: dict):
  try:
    return dm.add_key_term(item)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/key-terms/{item_id}")
async def update_key_term(item_id: str, item: dict):
  result = dm.update_key_term(item_id, item)
  if not result:
    raise HTTPException(status_code=404, detail="未找到该词条")
  return result

@app.delete("/api/key-terms/{item_id}")
async def remove_key_term(item_id: str):
  try:
    dm.delete_key_term(item_id)
    return {"ok": True}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# ════════════════════════════════════════════
#  研学规划
# ════════════════════════════════════════════
@app.get("/api/study-tours")
async def list_study_tours():
  try:
    return dm.get_study_tours()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/study-tours")
async def create_study_tour(item: dict):
  try:
    return dm.add_study_tour(item)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/study-tours/{item_id}")
async def update_study_tour(item_id: str, item: dict):
  result = dm.update_study_tour(item_id, item)
  if not result:
    raise HTTPException(status_code=404, detail="未找到该研学方案")
  return result

@app.delete("/api/study-tours/{item_id}")
async def remove_study_tour(item_id: str):
  try:
    dm.delete_study_tour(item_id)
    return {"ok": True}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/study-tours/generate")
async def generate_study_tour(data: dict):
  try:
    destination = data.get("destination", "")
    duration = data.get("duration", "3天")
    theme = data.get("theme", "红色")
    plan = ai.generate_study_plan(destination, duration, theme)
    saved = dm.add_study_tour(plan)
    return saved
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"AI生成失败: {str(e)}")

# ════════════════════════════════════════════
#  情景剧 / 演讲稿
# ════════════════════════════════════════════
@app.get("/api/scripts")
async def list_scripts(script_type: str = ""):
  try:
    return dm.get_scripts(script_type)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scripts")
async def create_script(item: dict):
  try:
    return dm.add_script(item)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/scripts/{item_id}")
async def update_script(item_id: str, item: dict):
  result = dm.update_script(item_id, item)
  if not result:
    raise HTTPException(status_code=404, detail="未找到该作品")
  return result

@app.delete("/api/scripts/{item_id}")
async def remove_script(item_id: str):
  try:
    dm.delete_script(item_id)
    return {"ok": True}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scripts/generate")
async def generate_script(data: dict):
  try:
    script_type = data.get("type", "演讲稿")
    theme = data.get("theme", "")
    characters = data.get("characters", "")
    script = ai.generate_script(script_type, theme, characters)
    saved = dm.add_script(script)
    return saved
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"AI生成失败: {str(e)}")

# ════════════════════════════════════════════
#  虚拟展馆
# ════════════════════════════════════════════
@app.get("/api/exhibits")
async def list_exhibits():
  try:
    return dm.get_exhibits()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/exhibits/hierarchy")
async def get_exhibits_hierarchy():
  """返回省份-景点两级结构"""
  try:
    all_items = dm.get_exhibits()
    provinces = [x for x in all_items if x.get("type") == "province"]
    sites = [x for x in all_items if x.get("type") == "site"]
    result = []
    for p in provinces:
      # Extract province name from title (before the first —— or —)
      pname = p["title"].split("——")[0].split("—")[0].strip()
      psites = [s for s in sites if s.get("province") == pname]
      result.append({"province": p, "sites": psites})
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
@app.post("/api/exhibits")
async def create_exhibit(item: dict):
  try:
    return dm.add_exhibit(item)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/exhibits/{item_id}")
async def update_exhibit(item_id: str, item: dict):
  result = dm.update_exhibit(item_id, item)
  if not result:
    raise HTTPException(status_code=404, detail="未找到该展品")
  return result

@app.delete("/api/exhibits/{item_id}")
async def remove_exhibit(item_id: str):
  try:
    dm.delete_exhibit(item_id)
    return {"ok": True}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
  import uvicorn
  import socket
  port = 28200
  for p in range(28200, 28299):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    r = sock.connect_ex(("127.0.0.1", p))
    sock.close()
    if r != 0:
      port = p
      break
  print(f"server on http://127.0.0.1:{port}")
  uvicorn.run(app, host="127.0.0.1", port=port)
