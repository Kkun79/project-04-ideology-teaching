// ============================================================
//  思政教学程序 - 时政 / 案例 / 词条域
// ============================================================

// ─── 时政 ───
async function loadPoliticsPanel(forceRefresh = false) {
 const status = document.getElementById("politics-status");
 const params = new URLSearchParams();
 const origin = document.getElementById("politics-filter-origin")?.value || "";
 const tag = document.getElementById("politics-filter-tag")?.value || "";
 const source = document.getElementById("politics-filter-source")?.value || "";
 const keyword = document.getElementById("politics-filter-keyword")?.value || "";
 const dateFrom = document.getElementById("politics-filter-date-from")?.value || "";
 const dateTo = document.getElementById("politics-filter-date-to")?.value || "";
 if (origin) params.set("origin", origin);
 if (tag) params.set("tag", tag);
 if (source) params.set("source", source);
 if (keyword) params.set("keyword", keyword);
 if (dateFrom) params.set("date_from", dateFrom);
 if (dateTo) params.set("date_to", dateTo);
 if (status) status.textContent = forceRefresh ? "正在刷新时政内容..." : "正在加载时政内容...";
 try {
   const [data, facets] = await Promise.all([
     api(`/api/current-politics${params.toString() ? "?" + params.toString() : ""}`),
     api("/api/current-politics-facets"),
   ]);
   renderPoliticsFilterOptions(facets);
   renderPoliticsFilterSummary(facets, data.length);
   renderListData("politics-list", data, renderPoliticsItem);
   if (status) status.textContent = `已加载 ${data.length} 条时政内容。`;
 } catch (e) {
   const container = document.getElementById("politics-list");
   if (container) container.innerHTML = '<div class="empty-state"><p>加载失败，请稍后重试</p></div>';
   if (status) status.textContent = "时政内容加载失败。";
 }
}

function renderPoliticsFilterOptions(facets) {
 const tagSelect = document.getElementById("politics-filter-tag");
 const sourceList = document.getElementById("politics-filter-source-options");
 const currentTag = tagSelect?.value || "";
 if (tagSelect) {
   const seen = new Set();
   const options = ['<option value="">全部主题</option>'];
   (facets?.tags || []).forEach(item => {
     if (!item || !item.label || seen.has(item.label)) return;
     seen.add(item.label);
     options.push(`<option value="${esc(item.label)}">${esc(item.label)}（${item.count}）</option>`);
   });
   if (currentTag && !seen.has(currentTag)) {
     options.push(`<option value="${esc(currentTag)}">${esc(currentTag)}</option>`);
   }
   tagSelect.innerHTML = options.join("");
   tagSelect.value = currentTag;
 }
 if (sourceList) {
   sourceList.innerHTML = (facets?.sources || [])
     .filter(item => item && item.label)
     .map(item => `<option value="${esc(item.label)}">${esc(item.label)}（${item.count}）</option>`)
     .join("");
 }
 const dateFrom = document.getElementById("politics-filter-date-from");
 const dateTo = document.getElementById("politics-filter-date-to");
 if (dateFrom && !dateFrom.value && facets?.date_range?.min) dateFrom.min = facets.date_range.min;
 if (dateTo && !dateTo.value && facets?.date_range?.max) dateTo.max = facets.date_range.max;
}

function renderPoliticsFilterSummary(facets, filteredCount) {
 const container = document.getElementById("politics-filter-summary");
 if (!container) return;
 const summary = facets?.summary || {};
 container.innerHTML = `
   <span class="politics-filter-pill">当前结果 ${filteredCount || 0} 条</span>
   <span class="politics-filter-pill">总量 ${summary.total || 0}</span>
   <span class="politics-filter-pill">自动同步 ${summary.auto || 0}</span>
   <span class="politics-filter-pill">手动录入 ${summary.manual || 0}</span>
   <span class="politics-filter-pill">国内时政 ${summary.domestic || 0}</span>
   <span class="politics-filter-pill">国际时政 ${summary.world || 0}</span>
 `;
}

function renderListData(listId, data, renderFn) {
 const container = document.getElementById(listId);
 if (!container) return;
 if (!data || data.length === 0) {
   container.innerHTML = '<div class="empty-state"><p>暂无数据</p></div>';
   return;
 }
 container.innerHTML = data.map(renderFn).join("");
}

function renderPoliticsItem(d) {
 const tags = (d.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join("");
 const autoOrigins = ["gnews-auto", "xinhua-auto"];
 const originTag = autoOrigins.includes(d.origin) ? '<span class="tag">自动同步</span>' : '<span class="tag">手动录入</span>';
 return `<div class="data-item"><div class="data-item-header">
   <div><div class="data-item-title">${esc(d.title)}</div>
   <div class="data-item-meta"><span>${esc(d.source)}</span><span>${esc(d.date)}</span>${originTag}${tags}</div></div>
   <div class="data-item-actions">
     <button class="btn btn-danger btn-sm" onclick="deletePoliticsItem(event,'${d.id}')">删除</button>
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
 closeForm("politics-form");
 loadPoliticsPanel(false);
}

async function deletePoliticsItem(event, itemId) {
 if (event) event.stopPropagation();
 if (!confirm("确定要删除吗？")) return;
 try {
   await api(`/api/current-politics/${itemId}`, "DELETE");
   await loadPoliticsPanel(false);
   if (typeof showSuccess === "function") showSuccess("删除成功");
 } catch (e) {}
}

async function syncPoliticsNews() {
 const status = document.getElementById("politics-status");
 if (status) status.textContent = "正在同步新华网最新内容...";
 try {
   const result = await api("/api/current-politics-sync", "POST", {});
   await loadPoliticsPanel(true);
   if (status) {
     status.textContent = result.message || ("新华网同步完成，当前共 " + (result.count || 0) + " 条。");
   }
   if (typeof showSuccess === "function") showSuccess("新华网时政同步完成");
 } catch (e) {
   if (status) status.textContent = "同步失败：" + e.message;
   if (typeof showError === "function") showError("新华网时政同步失败：" + e.message);
 }
}

async function syncCasesFromPolitics() {
 const status = document.getElementById("cases-sync-status");
 if (status) status.textContent = "正在根据最新时政同步教学案例...";
 try {
   const result = await api("/api/cases-sync", "POST", {});
   caseAutoSyncChecked = true;
   await loadCases();
   if (status) status.textContent = result.message || ("案例同步完成，当前共 " + (result.count || 0) + " 条。");
   if (typeof showSuccess === "function") showSuccess("案例同步完成");
 } catch (e) {
   if (status) status.textContent = "案例同步失败：" + e.message;
   if (typeof showError === "function") showError("案例同步失败：" + e.message);
 }
}

async function syncKeyTermsFromPolitics() {
 const status = document.getElementById("keyterms-sync-status");
 if (status) status.textContent = "正在同步适合课堂使用的正向思政关键词条...";
 try {
   const result = await api("/api/key-terms-sync", "POST", {});
   keyTermAutoSyncChecked = true;
   await loadKeyTerms();
   if (status) status.textContent = result.message || ("词条同步完成，当前共 " + (result.count || 0) + " 条。");
   if (typeof showSuccess === "function") showSuccess("词条同步完成");
 } catch (e) {
   if (status) status.textContent = "词条同步失败：" + e.message;
   if (typeof showError === "function") showError("词条同步失败：" + e.message);
 }
}

// ─── 案例 ───
var caseRecords = new Map();
var caseAutoSyncChecked = false;
var keyTermAutoSyncChecked = false;

function formatTeachingSyncStatus(result, fallback) {
 if (!result) return fallback;
 return result.message || fallback;
}

async function autoSyncCasesIfDue() {
 if (caseAutoSyncChecked) return;
 caseAutoSyncChecked = true;
 const status = document.getElementById("cases-sync-status");
 try {
   const result = await api("/api/cases-sync/auto", "POST", {});
   if (status) status.textContent = formatTeachingSyncStatus(result, "每日自动检查经典案例已完成。");
 } catch (e) {
   if (status) status.textContent = "每日自动检查暂未完成，可点击立即同步经典案例。";
 }
}

async function autoSyncKeyTermsIfDue() {
 if (keyTermAutoSyncChecked) return;
 keyTermAutoSyncChecked = true;
 const status = document.getElementById("keyterms-sync-status");
 try {
   const result = await api("/api/key-terms-sync/auto", "POST", {});
   if (status) status.textContent = formatTeachingSyncStatus(result, "每周自动检查思政关键词条已完成。");
 } catch (e) {
   if (status) status.textContent = "每周自动检查暂未完成，可点击立即同步思政关键词条。";
 }
}

async function loadCases() {
 const category = document.getElementById("case-filter-category")?.value || "";
 const era = document.getElementById("case-filter-era")?.value || "";
 const keyword = document.getElementById("case-filter-keyword")?.value || "";
 const params = new URLSearchParams();
 if (category) params.set("category", category);
 if (era) params.set("era", era);
 if (keyword) params.set("keyword", keyword);
 const url = `/api/cases${params.toString() ? "?" + params.toString() : ""}`;
 const container = document.getElementById("case-list");
 if (!container) return;
 if (typeof showLoading === "function") showLoading("case-list");
 try {
   await autoSyncCasesIfDue();
   const data = await api(url);
   caseRecords = new Map((data || []).map(item => [item.id, item]));
   if (!data || data.length === 0) {
     container.innerHTML = '<div class="empty-state"><p>暂无数据</p></div>';
     return;
   }
   container.innerHTML = data.map(renderCaseItem).join("");
 } catch (e) {
   container.innerHTML = '<div class="empty-state"><p>加载失败，请刷新重试</p></div>';
 }
}

function renderCaseItem(d) {
 const tags = (d.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join("");
 const topics = (d.teaching_topics || []).map(t => `<span class="case-topic-pill">${esc(t)}</span>`).join("");
 const questionCount = (d.discussion_questions || []).length;
 const syncTag = d.sync_origin === "current-politics-auto" ? `<span class="tag">时政同步</span>` : "";
 return `<div class="data-item case-item"><div class="data-item-header">
   <div><div class="data-item-title">${esc(d.title)}</div>
   <div class="data-item-meta"><span class="tag">${esc(d.category)}</span><span class="tag">${esc(d.era)}</span>${syncTag}${tags}</div></div>
   <div class="data-item-actions">
     <button class="btn btn-sm" onclick="showCaseDetailById('${d.id}')">展开详情</button>
     <button class="btn btn-danger btn-sm" onclick="deleteCaseItem(event,'${d.id}')">删除</button>
   </div></div>
   <div class="data-item-body">
     <div class="case-summary">${esc(d.summary)}</div>
     ${topics ? `<div class="case-topics"><span class="case-label">教学主题</span><div class="case-topic-list">${topics}</div></div>` : ""}
     ${d.teaching_value ? `<div class="case-block"><div class="case-label">育人价值</div><p class="case-preview-text">${esc(d.teaching_value)}</p></div>` : ""}
     ${d.recommended_usage ? `<div class="case-block"><div class="case-label">课堂建议</div><p class="case-preview-text">${esc(d.recommended_usage)}</p></div>` : ""}
     ${questionCount ? `<div class="case-block"><div class="case-label">讨论问题</div><p class="case-inline-note">共 ${questionCount} 个问题，点击“展开详情”查看完整教学卡片。</p></div>` : ""}
     <div class="case-footer">
       ${d.source ? `<span class="case-source">来源：${esc(d.source)}</span>` : ""}
     </div>
   </div>
 </div>`;
}

function showCaseForm() { showForm("case-form"); }

function renderCaseParagraphs(text) {
 const lines = String(text || "").split(/\r?\n/).map(line => line.trim()).filter(Boolean);
 if (!lines.length) return '<p class="case-detail-empty">暂无内容</p>';
 return lines.map(line => `<p>${esc(line)}</p>`).join("");
}

function renderCaseList(items) {
 const values = (items || []).filter(Boolean);
 if (!values.length) return '<p class="case-detail-empty">暂无内容</p>';
 return `<ul class="case-detail-list">${values.map(item => `<li>${esc(item)}</li>`).join("")}</ul>`;
}

function showCaseDetailById(caseId) {
 const item = caseRecords.get(caseId);
 const title = document.getElementById("case-detail-title");
 const meta = document.getElementById("case-detail-meta");
 const body = document.getElementById("case-detail-body");
 if (!item || !title || !meta || !body) return;
 title.textContent = item.title || "案例详情";
 meta.innerHTML = `<span class="tag">${esc(item.category || "未分类")}</span><span class="tag">${esc(item.era || "时期待补充")}</span>${(item.tags || []).map(tag => `<span class="tag">${esc(tag)}</span>`).join("")}`;
 body.innerHTML = `
   ${item.summary ? `<section class="case-detail-section"><div class="case-label">案例摘要</div><p class="case-detail-summary">${esc(item.summary)}</p></section>` : ""}
   <section class="case-detail-section">
     <div class="case-label">史实内容</div>
     <div class="case-detail-prose">${renderCaseParagraphs(item.content)}</div>
   </section>
   <section class="case-detail-grid">
     <div class="case-detail-section">
       <div class="case-label">育人价值</div>
       <div class="case-detail-prose">${renderCaseParagraphs(item.teaching_value)}</div>
     </div>
     <div class="case-detail-section">
       <div class="case-label">课堂建议</div>
       <div class="case-detail-prose">${renderCaseParagraphs(item.recommended_usage)}</div>
     </div>
   </section>
   <section class="case-detail-grid">
     <div class="case-detail-section">
       <div class="case-label">教学主题</div>
       ${(item.teaching_topics || []).length ? `<div class="case-topic-list">${(item.teaching_topics || []).map(topic => `<span class="case-topic-pill">${esc(topic)}</span>`).join("")}</div>` : '<p class="case-detail-empty">暂无内容</p>'}
     </div>
     <div class="case-detail-section">
       <div class="case-label">讨论问题</div>
       ${renderCaseList(item.discussion_questions)}
     </div>
   </section>
   ${item.source ? `<section class="case-detail-section"><div class="case-label">事实来源</div><p class="case-source">${esc(item.source)}</p></section>` : ""}
 `;
 showForm("case-detail-modal");
}

function closeCaseDetail() {
 closeForm("case-detail-modal");
}

function handleCaseDetailBackdrop(event) {
 if (event.target && event.target.id === "case-detail-modal") closeCaseDetail();
}

async function deleteCaseItem(event, caseId) {
 if (event) event.stopPropagation();
 if (!confirm("确定要删除吗？")) return;
 try {
   await api(`/api/cases/${caseId}`, "DELETE");
   caseRecords.delete(caseId);
   closeCaseDetail();
   if (typeof showSuccess === "function") showSuccess("删除成功");
   loadCases();
 } catch (e) {}
}

async function saveCase() {
 const tags = g("case-tags").split(",").map(s => s.trim()).filter(Boolean);
 const topics = g("case-topics").split(",").map(s => s.trim()).filter(Boolean);
 const questions = g("case-questions").split(",").map(s => s.trim()).filter(Boolean);
 const item = {
   title: g("case-title"),
   category: document.getElementById("case-category")?.value || "",
   era: document.getElementById("case-era")?.value || "",
   summary: g("case-summary"),
   content: g("case-content"),
   teaching_value: g("case-teaching-value"),
   recommended_usage: g("case-recommended-usage"),
   teaching_topics: topics,
   discussion_questions: questions,
   tags,
   source: g("case-source")
 };
 await api("/api/cases", "POST", item);
 closeForm("case-form");
 loadCases();
}

document.addEventListener("keydown", function(e) {
 const detailModal = document.getElementById("case-detail-modal");
 if (e.key === "Escape" && detailModal && !detailModal.classList.contains("hidden")) {
   closeCaseDetail();
 }
});

// ─── 关键词条 ───
async function loadKeyTerms() {
 await autoSyncKeyTermsIfDue();
 await fetchData("/api/key-terms", "keyterm-list", renderKeyTermItem);
}

function renderKeyTermItem(d) {
 const related = (d.related_terms || []).map(t => `<span class="tag">${esc(t)}</span>`).join("");
 const linkIcon = d.url ? ` <a href="${esc(d.url)}" target="_blank" title="查看原文">&#128279;</a>` : "";
 const syncTag = d.sync_origin === "current-politics-auto" ? `<span class="term-meta-pill">同步补充</span>` : "";
 const meta = [
   d.book ? `教材：${esc(d.book)}` : "",
   d.proposer ? `提出者：${esc(d.proposer)}` : "",
   d.proposed_time ? `时间：${esc(d.proposed_time)}` : ""
 ].filter(Boolean).map(t => `<span class="term-meta-pill">${t}</span>`).join("");
 const context = d.proposed_context ? `<div class="term-section"><strong>提出场合：</strong><p>${esc(d.proposed_context)}</p></div>` : "";
 return `<div class="term-card">
   <div class="term-card-head">
     <h4>${esc(d.term)}${linkIcon}</h4>
     ${(syncTag || meta) ? `<div class="term-meta-row">${syncTag}${meta}</div>` : ""}
   </div>
   <div class="term-time">&#128197; ${esc(d.proposed_time || "时间待补充")}</div>
   ${context}
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
 const item = {
   term: g("kt-term"),
   book: g("kt-book"),
   proposer: g("kt-proposer"),
   proposed_time: g("kt-time"),
   proposed_context: g("kt-context"),
   meaning: g("kt-meaning"),
   significance: g("kt-significance"),
   source_publication: g("kt-source"),
   url: g("kt-url"),
   related_terms: related
 };
 await api("/api/key-terms", "POST", item);
 closeForm("keyterm-form");
 loadKeyTerms();
}

window.loadPoliticsPanel = loadPoliticsPanel;
window.showPoliticsForm = showPoliticsForm;
window.savePolitics = savePolitics;
window.syncPoliticsNews = syncPoliticsNews;
window.syncCasesFromPolitics = syncCasesFromPolitics;
window.syncKeyTermsFromPolitics = syncKeyTermsFromPolitics;
window.deletePoliticsItem = deletePoliticsItem;
window.loadCases = loadCases;
window.showCaseForm = showCaseForm;
window.saveCase = saveCase;
window.showCaseDetailById = showCaseDetailById;
window.closeCaseDetail = closeCaseDetail;
window.handleCaseDetailBackdrop = handleCaseDetailBackdrop;
window.deleteCaseItem = deleteCaseItem;
window.loadKeyTerms = loadKeyTerms;
window.showKeyTermForm = showKeyTermForm;
window.saveKeyTerm = saveKeyTerm;
