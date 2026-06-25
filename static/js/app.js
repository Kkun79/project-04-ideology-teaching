// ============================================================
//  思政教学程序 - 主交互脚本
// ============================================================

// ─── 导航 ───
document.querySelectorAll(".nav-tree .node").forEach(el => {
 el.addEventListener("click", e => {
   const section = el.dataset.section;
   if (!section) return;
   // 处理父节点展开/折叠
   const li = el.closest(".has-children");
   if (li && el.classList.contains("parent")) {
     li.classList.toggle("expanded");
     if (section === "theory" || section === "practice") return;
   }
   navigateTo(section);
 });
});

function navigateTo(section) {
 // 更新导航高亮
 document.querySelectorAll(".nav-tree .node").forEach(n => n.classList.remove("active"));
 const target = document.querySelector(`.nav-tree .node[data-section="${section}"]`);
 if (target) target.classList.add("active");

 // 切换到对应面板
 document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
 const panel = document.getElementById(`panel-${section}`);
 if (panel) {
   panel.classList.add("active");
   // 更新标题
   const title = target ? target.textContent.trim() : section;
   document.getElementById("pageTitle").textContent = title;
   // 按需加载数据
   loadPanelData(section);
 }
 // 移动端自动收起侧栏
 if (window.innerWidth <= 768) {
   document.getElementById("sidebar").classList.add("collapsed");
 }
}

function loadPanelData(section) {
 const loaders = {
   "textbooks":     () => fetchData("/api/textbooks", "textbook-list", renderTextbookItem),
   "courseware":    () => fetchData("/api/courseware", "courseware-list", renderCoursewareItem),
   "syllabus":      () => fetchData("/api/syllabus", "syllabus-list", renderSyllabusItem),
   "references":    () => fetchData("/api/references", "reference-list", renderReferenceItem),
   "politics-list": () => fetchData("/api/current-politics", "politics-list", renderPoliticsItem),
   "cases-list":    () => loadCases(),
   "keyterms-list": () => fetchData("/api/key-terms", "keyterm-list", renderKeyTermItem),
   "studytour-list":() => fetchData("/api/study-tours", "studytour-list", renderStudyTourItem),
   "exhibition-view":() => loadExhibition(),
   "scripts-list":  () => fetchData("/api/scripts", "script-list", renderScriptItem),
 };
 if (loaders[section]) loaders[section]();
}

// ─── API 通用 ───
async function api(url, method = "GET", body = null) {
 const opts = { headers: { "Content-Type": "application/json" } };
 if (body && method !== "PUT") { opts.method = "POST"; opts.body = JSON.stringify(body); }
 if (method === "DELETE") opts.method = "DELETE";
 if (method === "PUT") { opts.method = "PUT"; opts.body = JSON.stringify(body); }
 try {
   const res = await fetch(url, opts);
   if (!res.ok) {
     const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
     if (typeof showError === 'function') showError(err.detail || '请求失败');
     throw new Error(err.detail || `API error: ${res.status}`);
   }
   return res.json();
 } catch (e) {
   if (e.name !== 'Error' || !e.message.includes('API error')) {
     if (typeof showError === 'function') showError(e.message);
   }
   throw e;
 }
}

async function fetchData(url, listId, renderFn) {
 const container = document.getElementById(listId);
 if (!container) return;
 if (typeof showLoading === 'function') showLoading(listId);
 try {
   const data = await api(url);
   if (!data || data.length === 0) {
     container.innerHTML = '<div class="empty-state"><p>暂无数据</p></div>';
     return;
   }
   container.innerHTML = data.map(renderFn).join("");
 } catch (e) {
   container.innerHTML = '<div class="empty-state"><p>加载失败，请刷新重试</p></div>';
 }
}

function showForm(id) {
 document.getElementById(id).classList.remove("hidden");
}
function closeForm(id) {
 document.getElementById(id).classList.add("hidden");
}

// ─── 教材 ───
function renderTextbookItem(d) {
 return `<div class="data-item"><div class="data-item-header">
   <div><div class="data-item-title">${esc(d.name)}</div>
   <div class="data-item-meta"><span>${esc(d.author)}</span><span>${esc(d.publisher)}</span><span>${esc(d.year)}</span></div></div>
   <div class="data-item-actions">
     <button class="btn btn-danger btn-sm" onclick="deleteItem('/api/textbooks','${d.id}','textbook-list',renderTextbookItem)">删除</button>
   </div></div>
   ${d.description ? `<div class="data-item-body">${esc(d.description)}</div>` : ""}
 </div>`;
}
function showTextbookForm() { showForm("textbook-form"); }
async function saveTextbook() {
 const item = { name: g("tb-name"), author: g("tb-author"), publisher: g("tb-publisher"), year: g("tb-year"), isbn: g("tb-isbn"), description: g("tb-desc") };
 await api("/api/textbooks", "POST", item);
 closeForm("textbook-form"); fetchData("/api/textbooks", "textbook-list", renderTextbookItem);
}

// ─── 课件 ───
function renderCoursewareItem(d) {
 return `<div class="data-item"><div class="data-item-header">
   <div><div class="data-item-title">${esc(d.title)}</div>
   <div class="data-item-meta"><span>${esc(d.chapter)}</span>${d.description ? `<span>${esc(d.description)}</span>` : ""}</div></div>
   <div class="data-item-actions">
     <button class="btn btn-danger btn-sm" onclick="deleteItem('/api/courseware','${d.id}','courseware-list',renderCoursewareItem)">删除</button>
   </div></div>
 </div>`;
}
function showCoursewareForm() { showForm("courseware-form"); }
async function saveCourseware() {
 const item = { title: g("cw-title"), chapter: g("cw-chapter"), description: g("cw-desc") };
 await api("/api/courseware", "POST", item);
 closeForm("courseware-form"); fetchData("/api/courseware", "courseware-list", renderCoursewareItem);
}

// ─── 教学大纲 ───
function renderSyllabusItem(d) {
 return `<div class="data-item"><div class="data-item-header">
   <div><div class="data-item-title">${esc(d.title)}</div>
   <div class="data-item-meta"><span>${esc(d.semester)}</span>${d.total_hours ? `<span>${d.total_hours} 学时</span>` : ""}</div></div>
   <div class="data-item-actions">
     <button class="btn btn-danger btn-sm" onclick="deleteItem('/api/syllabus','${d.id}','syllabus-list',renderSyllabusItem)">删除</button>
   </div></div>
   ${d.content ? `<div class="data-item-body">${esc(d.content).replace(/\n/g, "<br>")}</div>` : ""}
 </div>`;
}
function showSyllabusForm() { showForm("syllabus-form"); }
async function saveSyllabus() {
 const item = { title: g("sy-title"), semester: g("sy-semester"), total_hours: parseInt(g("sy-hours")) || 0, content: g("sy-content") };
 await api("/api/syllabus", "POST", item);
 closeForm("syllabus-form"); fetchData("/api/syllabus", "syllabus-list", renderSyllabusItem);
}

// ─── 参考书目 ───
function renderReferenceItem(d) {
 return `<div class="data-item"><div class="data-item-header">
   <div><div class="data-item-title">${esc(d.title)}</div>
   <div class="data-item-meta"><span>${esc(d.author)}</span><span>${esc(d.publisher)}</span><span>${esc(d.year)}</span></div></div>
   <div class="data-item-actions">
     <button class="btn btn-danger btn-sm" onclick="deleteItem('/api/references','${d.id}','reference-list',renderReferenceItem)">删除</button>
   </div></div>
   ${d.description ? `<div class="data-item-body">${esc(d.description)}</div>` : ""}
 </div>`;
}
function showReferenceForm() { showForm("reference-form"); }
async function saveReference() {
 const item = { title: g("ref-title"), author: g("ref-author"), publisher: g("ref-publisher"), year: g("ref-year"), isbn: g("ref-isbn"), description: g("ref-desc") };
 await api("/api/references", "POST", item);
 closeForm("reference-form"); fetchData("/api/references", "reference-list", renderReferenceItem);
}

// ─── 时政 ───
function renderPoliticsItem(d) {
 const tags = (d.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join("");
 return `<div class="data-item"><div class="data-item-header">
   <div><div class="data-item-title">${esc(d.title)}</div>
   <div class="data-item-meta"><span>${esc(d.source)}</span><span>${esc(d.date)}</span>${tags}</div></div>
   <div class="data-item-actions">
     <button class="btn btn-danger btn-sm" onclick="deleteItem('/api/current-politics','${d.id}','politics-list',renderPoliticsItem)">删除</button>
   </div></div>
   <div class="data-item-body">${esc(d.summary)}</div>
   ${d.url ? `<div class="mt-8"><a href="${esc(d.url)}" target="_blank">查看原文 &rarr;</a></div>` : ""}
 </div>`;
}
function showPoliticsForm() { showForm("politics-form"); }
async function savePolitics() {
 const tags = g("cp-tags").split(",").map(s => s.trim()).filter(Boolean);
 const item = { title: g("cp-title"), source: g("cp-source"), date: g("cp-date"), summary: g("cp-summary"), content: g("cp-content"), url: g("cp-url"), tags };
 await api("/api/current-politics", "POST", item);
 closeForm("politics-form"); fetchData("/api/current-politics", "politics-list", renderPoliticsItem);
}

// ─── 案例 ───
function loadCases() {
 const category = document.getElementById("case-filter-category")?.value || "";
 const era = document.getElementById("case-filter-era")?.value || "";
 const keyword = document.getElementById("case-filter-keyword")?.value || "";
 const params = new URLSearchParams();
 if (category) params.set("category", category);
 if (era) params.set("era", era);
 if (keyword) params.set("keyword", keyword);
 const url = `/api/cases${params.toString() ? "?" + params.toString() : ""}`;
 fetchData(url, "case-list", renderCaseItem);
}
function renderCaseItem(d) {
 const tags = (d.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join("");
 return `<div class="data-item"><div class="data-item-header">
   <div><div class="data-item-title">${esc(d.title)}</div>
   <div class="data-item-meta"><span class="tag">${esc(d.category)}</span><span class="tag">${esc(d.era)}</span>${tags}</div></div>
   <div class="data-item-actions">
     <button class="btn btn-danger btn-sm" onclick="deleteItem('/api/cases','${d.id}','case-list',renderCaseItem)">删除</button>
   </div></div>
   <div class="data-item-body">${esc(d.summary)}</div>
 </div>`;
}
function showCaseForm() { showForm("case-form"); }
async function saveCase() {
 const tags = g("case-tags").split(",").map(s => s.trim()).filter(Boolean);
 const item = { title: g("case-title"), category: g("case-category"), era: g("case-era"), summary: g("case-summary"), content: g("case-content"), tags, source: g("case-source") };
 await api("/api/cases", "POST", item);
 closeForm("case-form"); loadCases();
}

// ─── 关键词条 ───
function renderKeyTermItem(d) {
 const related = (d.related_terms || []).map(t => `<span class="tag">${esc(t)}</span>`).join("");
 const linkIcon = d.url ? ` <a href="${esc(d.url)}" target="_blank" title="查看原文">&#128279;</a>` : "";
 return `<div class="term-card">
   <h4>${esc(d.term)}${linkIcon}</h4>
   <div class="term-time">&#128197; ${esc(d.proposed_time)}</div>
   <div class="term-section"><strong>内涵/含义：</strong><p>${esc(d.meaning)}</p></div>
   <div class="term-section"><strong>意义：</strong><p>${esc(d.significance)}</p></div>
   <div class="term-source">&#128218; 来源：${esc(d.source_publication)}${d.url ? ` · <a href="${esc(d.url)}" target="_blank">查看原文</a>` : ""}</div>
   ${related ? `<div class="term-related">${related}</div>` : ""}
   <div class="mt-8"><button class="btn btn-danger btn-sm" onclick="deleteItem('/api/key-terms','${d.id}','keyterm-list',renderKeyTermItem)">删除</button></div>
 </div>`;
}
function showKeyTermForm() { showForm("keyterm-form"); }
async function saveKeyTerm() {
 const related = g("kt-related").split(",").map(s => s.trim()).filter(Boolean);
 const item = { term: g("kt-term"), proposed_time: g("kt-time"), meaning: g("kt-meaning"), significance: g("kt-significance"), source_publication: g("kt-source"), url: g("kt-url"), related_terms: related };
 await api("/api/key-terms", "POST", item);
 closeForm("keyterm-form"); fetchData("/api/key-terms", "keyterm-list", renderKeyTermItem);
}

// ─── 研学规划 ───
function renderStudyTourItem(d) {
 const aiTag = d.ai_generated ? `<span class="ai-badge">AI</span>` : "";
 return `<div class="data-item"><div class="data-item-header">
   <div><div class="data-item-title">${aiTag}${esc(d.title)}</div>
   <div class="data-item-meta"><span>&#128205; ${esc(d.destination)}</span><span>&#128197; ${esc(d.duration)}</span></div></div>
   <div class="data-item-actions">
     <button class="btn btn-danger btn-sm" onclick="deleteItem('/api/study-tours','${d.id}','studytour-list',renderStudyTourItem)">删除</button>
   </div></div>
   <div class="data-item-body">
     <strong>目标：</strong>${esc(d.objectives)}<br>
     ${d.itinerary ? `<strong>行程：</strong><br>${esc(d.itinerary).replace(/\n/g, "<br>")}<br>` : ""}
     ${d.budget ? `<strong>预算：</strong>${esc(d.budget)}` : ""}
     ${d.notes ? `<br><em>${esc(d.notes)}</em>` : ""}
   </div>
 </div>`;
}
function showAIGenerateTour() { showForm("studytour-ai-form"); }
async function generateStudyTour() {
 const data = { destination: g("st-ai-dest"), duration: g("st-ai-duration"), theme: document.getElementById("st-ai-theme")?.value || "红色" };
 await api("/api/study-tours/generate", "POST", data);
 closeForm("studytour-ai-form");
 fetchData("/api/study-tours", "studytour-list", renderStudyTourItem);
 updateBadge("AI 方案已生成");
}

// ─── 虚拟展馆 ───
let exhibitHierarchy = [];
// selectProvince removed - all provinces+sites visible simultaneously
function selectProvince(t) { loadExhibition(); }
function showProvinceSites(provinceTitle) {
  var p = null;
  for (var i = 0; i < exhibitHierarchy.length; i++) {
    if (exhibitHierarchy[i].province.title === provinceTitle) {
      p = exhibitHierarchy[i]; break;
    }
  }
  if (!p) return;
  var stage = document.getElementById("exhibit-stage");
  if (!stage) return;
  var pname = provinceTitle.replace(/——.*$/, "").replace(/—.*$/, "");
  var html = '<div class="ps-topbar">';
  html += '  <div class="ps-title">◆ ' + esc(pname) + ' —— 红色景点</div>';
  html += '  <div class="ps-count">共 ' + p.sites.length + ' 个展点</div>';
  html += '</div>';
  if (p.sites.length === 0) {
    html += '<div class="exhibit-placeholder">该省份暂无具体景点</div>';
  } else {
    p.sites.forEach(function(s) {
      var sname = esc(s.title).replace(/.*?——/, "").replace(/.*?—/, "");
      html += '<div class="ps-card" data-siteid="' + s.id + '">';
      html += '  <div class="ps-card-header">';
      html += '    <span class="ps-card-name">' + sname + '</span>';
      html += '    <span class="ps-card-era">' + esc(s.era) + '</span>';
      html += '  </div>';
      html += '  <div class="ps-card-desc">' + esc(s.description).substring(0, 100) + '...</div>';
      html += '  <div class="ps-card-action">查看详情 →</div>';
      html += '</div>';
    });
  }
  stage.innerHTML = html;
  // Delegate site card clicks
  stage.onclick = function(e) {
    var card = e.target.closest(".ps-card");
    if (card) {
      var sid = card.getAttribute("data-siteid");
      if (sid) {
        var site = null;
        for (var i = 0; i < exhibitHierarchy.length; i++) {
          for (var j = 0; j < exhibitHierarchy[i].sites.length; j++) {
            if (exhibitHierarchy[i].sites[j].id === sid) {
              site = exhibitHierarchy[i].sites[j]; break;
            }
          }
          if (site) break;
        }
        if (site) showExhibit(site);
      }
    }
  };
}
function showProvinceList() {
  loadExhibition();
}
function selectSite(siteId) {
  // Find site in hierarchy
  let site = null;
  for (const p of exhibitHierarchy) {
    for (const s of p.sites) {
      if (s.id === siteId) { site = s; break; }
    }
    if (site) break;
  }
  if (!site) {
    // Try flat lookup
    site = { id: siteId };
  }
  document.querySelectorAll(".exhibit-nav-item").forEach(el => el.classList.remove("active"));
  const navItem = document.querySelector(`.exhibit-nav-item[onclick="selectSite('${siteId}')"]`);
  if (navItem) navItem.classList.add("active");
  showExhibit(site);
}
let exhibitsData = [];
async function loadExhibition() {
 try {
   var data = await api("/api/exhibits/hierarchy");
   exhibitHierarchy = data;
   var nav = document.getElementById("exhibit-nav");
   var stage = document.getElementById("exhibit-stage");
   if (!nav) { return; }
   if (!data || data.length === 0) {
     nav.innerHTML = "<div class='empty-state'><p>暂无展品</p></div>";
     if (stage) { stage.innerHTML = '<div class="exhibit-placeholder">暂无展品</div>'; }
     return;
   }
   var regionOrder = ["华北地区","东北地区","华东地区","华中地区","华南地区","西南地区","西北地区","台湾地区"];
   var regions = {};
   data.forEach(function(p) {
     var r = p.province.region || "其他地区";
     if (!regions[r]) { regions[r] = []; }
     regions[r].push(p);
   });
   var html = "";
   regionOrder.forEach(function(r) {
     if (!regions[r]) { return; }
     html += '<div class="exhibit-region-label">' + r + '</div>';
     regions[r].forEach(function(p) {
       var pn = p.province.title.replace(/——.*$/,"").replace(/—.*$/,"");
       html += '<div class="province-item" data-province="' + esc(p.province.title) + '">';
       html += '  <span class="province-item-name">' + esc(pn) + '</span>';
       html += '  <span class="province-item-count">' + p.sites.length + '个景点 ▶</span>';
       html += '</div>';
     });
   });
   nav.innerHTML = html;
   nav.onclick = function(e) {
     var item = e.target.closest(".province-item");
     if (item) {
       document.querySelectorAll(".province-item").forEach(function(el) { el.classList.remove("active"); });
       item.classList.add("active");
       showProvinceSites(item.getAttribute("data-province"));
     }
   };
   if (data.length > 0) {
     var first = nav.querySelector(".province-item");
     if (first) {
       first.classList.add("active");
       showProvinceSites(first.getAttribute("data-province"));
     }
   }
 } catch (e) { console.error(e); }
}

function showExhibit(site) {
 if (!site) return;
 var stage = document.getElementById("exhibit-stage");
 var activeProvince = document.querySelector(".province-item.active");
 var backTitle = activeProvince ? activeProvince.getAttribute("data-province") : "";
 var regionTag = site.region ? '<span class="tag">' + esc(site.region) + '</span>' : "";
 var dialogueHtml = site.dialogue ? '<div class="ex-dialogue">' + esc(site.dialogue).replace(/\n/g, "<br>") + '</div>' : "";
 var backBtn = backTitle ? '<div class="ex-back" data-back="1">\u2190 \u8fd4\u56de\u666f\u70b9\u5217\u8868</div>' : "";
 stage.innerHTML = backBtn + '<div class="ex-title">' + esc(site.title) + '</div>' + '<div class="ex-era">' + regionTag + ' ' + esc(site.era) + '</div>' + '<div class="ex-desc">' + esc(site.description) + '</div>' + dialogueHtml;
 // Attach back button handler
 var be = stage.querySelector(".ex-back");
 if (be) {
   be.onclick = function() { showProvinceSites(backTitle); };
 }
}

function showScriptForm() { showForm("script-form"); }
async function saveScript() {
 const item = { title: g("sc-title"), type: document.getElementById("sc-type")?.value || "情景剧", theme: g("sc-theme"), characters: g("sc-characters"), content: g("sc-content"), notes: g("sc-notes") };
 await api("/api/scripts", "POST", item);
 closeForm("script-form"); fetchData("/api/scripts", "script-list", renderScriptItem);
}
function showAIScriptForm() { showForm("script-ai-form"); }
async function generateScript() {
 const data = { type: document.getElementById("sc-ai-type")?.value || "演讲稿", theme: g("sc-ai-theme"), characters: g("sc-ai-characters") };
 await api("/api/scripts/generate", "POST", data);
 closeForm("script-ai-form");
 fetchData("/api/scripts", "script-list", renderScriptItem);
 updateBadge("AI 作品已生成");
}

// ─── 通用删除 ───
function deleteItem(baseUrl, id, listId, renderFn) {
 if (!confirm("确定要删除吗？")) return;
 api(`${baseUrl}/${id}`, "DELETE").then(() => {
   if (typeof showSuccess === 'function') showSuccess('删除成功');
   fetchData(baseUrl, listId, renderFn);
 }).catch(() => {});
}

// ─── 辅助 ───
function g(id) { return document.getElementById(id)?.value?.trim() || ""; }
function esc(s) { if (!s) return ""; const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
function updateBadge(msg) {
 const badge = document.getElementById("statusBadge");
 if (!badge) return;
 badge.textContent = msg;
 badge.style.background = "var(--accent)";
 badge.style.color = "#fff";
 setTimeout(() => { badge.textContent = "就绪"; badge.style.background = ""; badge.style.color = ""; }, 2500);
}

// ─── 侧边栏折叠 ───
document.getElementById("collapseBtn")?.addEventListener("click", () => {
 document.getElementById("sidebar").classList.toggle("collapsed");
});
document.getElementById("menuBtn")?.addEventListener("click", () => {
 document.getElementById("sidebar").classList.toggle("collapsed");
});

// ─── 主题切换 ───
document.querySelectorAll(".theme-card").forEach(el => {
 el.addEventListener("click", () => {
   document.querySelectorAll(".theme-card").forEach(c => c.classList.remove("selected"));
   el.classList.add("selected");
   const theme = el.dataset.theme;
   document.body.className = theme === "default" ? "" : `theme-${theme}`;
   localStorage.setItem("sz-theme", theme);
 });
});

function setSidebarMode(mode) {
 const sidebar = document.getElementById("sidebar");
 sidebar.classList.remove("compact", "icon-only");
 if (mode !== "normal") sidebar.classList.add(mode);
 localStorage.setItem("sz-sidebar-mode", mode);
}

function toggleShowIds() {
 const show = document.getElementById("show-ids")?.checked || false;
 localStorage.setItem("sz-show-ids", show ? "1" : "0");
 // ID display handled by render functions when enabled
}

// ─── 加载设置 ───
(function loadSettings() {
 const theme = localStorage.getItem("sz-theme") || "default";
 if (theme !== "default") document.body.className = `theme-${theme}`;
 document.querySelectorAll(".theme-card").forEach(el => {
   if (el.dataset.theme === theme) el.classList.add("selected");
 });
 const sidebarMode = localStorage.getItem("sz-sidebar-mode") || "normal";
 const smSelect = document.getElementById("sidebar-mode");
 if (smSelect) smSelect.value = sidebarMode;
 const showIds = localStorage.getItem("sz-show-ids") === "1";
 const cb = document.getElementById("show-ids");
 if (cb) cb.checked = showIds;
})();

// ─── 初始化默认面板 ───
document.addEventListener("DOMContentLoaded", () => {
 // 默认显示首页
});

// 暴露到全局 (供 onclick 调用)
window.navigateTo = navigateTo;
window.deleteItem = deleteItem;
window.loadCases = loadCases;
window.showTextbookForm = showTextbookForm;
window.saveTextbook = saveTextbook;
window.showCoursewareForm = showCoursewareForm;
window.saveCourseware = saveCourseware;
window.showSyllabusForm = showSyllabusForm;
window.saveSyllabus = saveSyllabus;
window.showReferenceForm = showReferenceForm;
window.saveReference = saveReference;
window.showPoliticsForm = showPoliticsForm;
window.savePolitics = savePolitics;
window.showCaseForm = showCaseForm;
window.saveCase = saveCase;
window.showKeyTermForm = showKeyTermForm;
window.saveKeyTerm = saveKeyTerm;
window.showAIGenerateTour = showAIGenerateTour;
window.generateStudyTour = generateStudyTour;
window.showExhibit = showExhibit;
window.selectProvince = selectProvince;
window.selectSite = selectSite;
// window.showProvinceList removed
window.showScriptForm = showScriptForm;
window.saveScript = saveScript;
window.showAIScriptForm = showAIScriptForm;
window.generateScript = generateScript;
window.showForm = showForm;
window.closeForm = closeForm;
window.setSidebarMode = setSidebarMode;
window.toggleShowIds = toggleShowIds;
window.selectProvince = selectProvince;
window.selectSite = selectSite;
// window.showProvinceList removed
