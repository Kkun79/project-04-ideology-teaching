// ============================================================
//  思政教学程序 - 主交互脚本
// ============================================================

const GREAT_LEADER_DIALOGUES = [
  {
    name: "毛泽东",
    title: "中国共产党、中国人民解放军和中华人民共和国的主要缔造者和领导人",
    bio: "毛泽东同志把马克思主义基本原理同中国具体实际相结合，领导中国人民经过长期革命斗争建立新中国，开辟了中国历史发展的新纪元。",
    detail_full: "毛泽东同志是伟大的马克思主义者，伟大的无产阶级革命家、战略家和理论家。他领导中国共产党和中国人民完成新民主主义革命，建立中华人民共和国，确立社会主义基本制度，并在长期实践中形成了毛泽东思想。",
    photo: "/static/images/leader_mao_zedong.jpg",
    siteTitle: "伟人精神谱系",
    siteEra: "新民主主义革命与社会主义建设时期"
  },
  {
    name: "邓小平",
    title: "中国社会主义改革开放和现代化建设的总设计师",
    bio: "邓小平同志坚持解放思想、实事求是，带领中国开启改革开放和社会主义现代化建设新时期，深刻改变了中国发展面貌。",
    detail_full: "邓小平同志是伟大的无产阶级革命家、政治家、军事家、外交家，是中国社会主义改革开放和现代化建设的总设计师。他强调解放思想、实事求是，提出把党和国家工作中心转移到经济建设上来，推动改革开放不断深入。",
    photo: "/static/images/leader_deng_xiaoping.jpg",
    siteTitle: "伟人精神谱系",
    siteEra: "改革开放和社会主义现代化建设新时期"
  },
  {
    name: "周恩来",
    title: "党和国家卓越领导人，人民的好总理",
    bio: "周恩来同志一生忠诚于党、忠诚于人民，以严于律己、鞠躬尽瘁的品格，生动诠释了共产党人的初心使命。",
    detail_full: "周恩来同志是伟大的马克思主义者，伟大的无产阶级革命家、政治家、军事家、外交家，是党和国家卓越领导人。他少年立志“为中华之崛起而读书”，一生勤勉工作、严于律己、服务人民。",
    photo: "/static/images/leader_zhou_enlai.png",
    siteTitle: "伟人精神谱系",
    siteEra: "革命、建设与外交实践"
  }
];

let adminPasswordTarget = null;

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
   "dashboard":     () => loadDataAssist(),
    "textbook-reader": () => {}, "smart-import":  () => resetSmartImportPanel(),
   "textbooks":     () => fetchData("/api/textbooks", "textbook-list", renderTextbookItem),
   "courseware":    () => fetchData("/api/courseware", "courseware-list", renderCoursewareItem),
   "syllabus":      () => fetchData("/api/syllabus", "syllabus-list", renderSyllabusItem),
   "references":    () => fetchData("/api/references", "reference-list", renderReferenceItem),
   "politics-list": () => loadPoliticsPanel(),
   "cases-list":    () => loadCases(),
   "keyterms-list": () => loadKeyTerms(),
   "studytour-list":() => fetchData("/api/study-tours", "studytour-list", renderStudyTourItem),
   "admin-users":   () => loadAdminUsers(),
   "exhibition-view":() => loadExhibition(),
   "ancestor-dialogue":() => loadAncestorDialogue(),
   "scripts-list":  () => loadScripts(),
  };
  if (loaders[section]) loaders[section]();
}

// ─── 大数据辅助 ───
async function loadDataAssist(showToast = false) {
 const container = document.getElementById("data-assist-overview");
 if (!container) return;
 if (typeof showLoading === "function") showLoading("data-assist-overview");
 try {
   const data = await api("/api/data-assist");
   const counts = data.resource_counts || {};
   const politics = data.politics || {};
   const cases = data.cases || {};
   const aiAssets = data.ai_assets || {};
   const hotTags = (data.hot_tags || []).map(item => `<span class="case-topic-pill">${esc(item.label)} ${item.count}</span>`).join("");
   const caseCategories = (cases.categories || []).map(item => `<li>${esc(item.label)}：${item.count}</li>`).join("");
   const caseEras = (cases.eras || []).map(item => `<li>${esc(item.label)}：${item.count}</li>`).join("");
   container.innerHTML = `
     <div class="data-assist-card">
       <h4>资源总览</h4>
       <div class="data-assist-stats">
         <div><strong>${counts.textbooks || 0}</strong><span>教材</span></div>
         <div><strong>${counts.courseware || 0}</strong><span>课件</span></div>
         <div><strong>${counts.references || 0}</strong><span>参考书目</span></div>
         <div><strong>${counts.cases || 0}</strong><span>案例</span></div>
         <div><strong>${counts.politics || 0}</strong><span>时政</span></div>
         <div><strong>${counts.sites || 0}</strong><span>展馆点位</span></div>
       </div>
     </div>
     <div class="data-assist-card">
       <h4>时政结构</h4>
       <ul class="data-assist-list">
         <li>自动同步：${politics.auto_count || 0}</li>
         <li>手动录入：${politics.manual_count || 0}</li>
         <li>国内时政：${politics.domestic_count || 0}</li>
         <li>国际时政：${politics.world_count || 0}</li>
       </ul>
     </div>
     <div class="data-assist-card">
       <h4>案例分布</h4>
       <div class="data-assist-columns">
         <ul class="data-assist-list">${caseCategories || "<li>暂无数据</li>"}</ul>
         <ul class="data-assist-list">${caseEras || "<li>暂无数据</li>"}</ul>
       </div>
     </div>
     <div class="data-assist-card">
       <h4>AI 产出占比</h4>
       <ul class="data-assist-list">
         <li>AI 研学方案：${aiAssets.study_tours || 0}</li>
         <li>AI 脚本作品：${aiAssets.scripts || 0}</li>
         <li>文物条目：${counts.artifacts || 0}</li>
         <li>更新时间：${esc(data.updated_at || "")}</li>
       </ul>
     </div>
     <div class="data-assist-card data-assist-card-wide">
       <h4>高频主题</h4>
       <div class="case-topic-list">${hotTags || '<span class="case-detail-empty">暂无数据</span>'}</div>
     </div>
   `;
   if (showToast && typeof showSuccess === "function") showSuccess("数据概览已刷新");
 } catch (e) {
   container.innerHTML = '<div class="empty-state"><p>数据概览加载失败</p></div>';
 }
}

// ─── 研学规划 ───
function renderStudyTourItem(d) {
 const aiTag = d.ai_generated ? '<span class="ai-badge">AI</span>' : "";
 const courses = (d.related_courses || []).map(function(c) { return '<span class="course-pill">' + esc(c) + '</span>'; }).join("");
 const competencies = d.core_competencies ? '<div class="st-field"><span class="st-label">核心素养：</span>' + esc(d.core_competencies) + '</div>' : "";
 const targetGrade = d.target_grade ? '<div class="st-field"><span class="st-label">适用对象：</span>' + esc(d.target_grade) + '</div>' : "";
 const preparation = d.preparation ? '<div class="st-section"><div class="st-subtitle">行前准备</div><div class="st-body">' + esc(d.preparation).replace(/\\n/g, '<br>') + '</div></div>' : "";
 const tasks = d.tasks ? '<div class="st-section"><div class="st-subtitle">研习任务</div><div class="st-body">' + esc(d.tasks).replace(/\\n/g, '<br>') + '</div></div>' : "";
 const evaluation = d.evaluation ? '<div class="st-section"><div class="st-subtitle">评价方式</div><div class="st-body">' + esc(d.evaluation).replace(/\\n/g, '<br>') + '</div></div>' : "";
 const safety = d.safety ? '<div class="st-section"><div class="st-subtitle">安全预案</div><div class="st-body">' + esc(d.safety).replace(/\\n/g, '<br>') + '</div></div>' : "";
 const outcomes = d.expected_outcomes ? '<div class="st-section"><div class="st-subtitle">预期成果</div><div class="st-body">' + esc(d.expected_outcomes).replace(/\\n/g, '<br>') + '</div></div>' : "";
 const resources = d.resources ? '<div class="st-section"><div class="st-subtitle">推荐资源</div><div class="st-body">' + esc(d.resources).replace(/\\n/g, '<br>') + '</div></div>' : "";
 const hasMore = preparation || tasks || evaluation || safety || outcomes || resources;
 const uid = 'st-' + d.id;
 return `<div class="data-item"><div class="data-item-header">
   <div>
     <div class="data-item-title">${aiTag}${esc(d.title)}</div>
     <div class="data-item-meta">
       <span>&#128205; ${esc(d.destination)}</span>
       <span>&#128197; ${esc(d.duration)}</span>
       ${targetGrade ? '<span>' + esc(d.target_grade) + '</span>' : ''}
     </div>
   </div>
   <div class="data-item-actions">
     ${hasMore ? '<button class="btn btn-sm" onclick="toggleStudyTourMore(\'' + uid + '\')" id="' + uid + '-toggle">展开准备清单</button>' : ''}
     <button class="btn btn-danger btn-sm" onclick="deleteItem(\'/api/study-tours\',\'' + d.id + '\',\'studytour-list\',renderStudyTourItem)">删除</button>
   </div></div>
   <div class="data-item-body">
     <div class="st-field"><span class="st-label">教学目标：</span>${esc(d.objectives)}</div>
     ${courses ? '<div class="st-field">' + courses + '</div>' : ""}
     ${competencies}
     <div class="st-field"><span class="st-label">行程安排：</span><br>${esc(d.itinerary).replace(/\\n/g, '<br>')}</div>
     ${d.budget ? '<div class="st-field"><span class="st-label">预算说明：</span>' + esc(d.budget) + '</div>' : ''}
     <div id="${uid}" class="st-more hidden">
       ${preparation}${tasks}${evaluation}${safety}${outcomes}${resources}
     </div>
     ${d.notes ? '<div class="st-notes">' + esc(d.notes) + '</div>' : ''}
   </div>
 </div>`;
}

function toggleStudyTourMore(uid) {
 const block = document.getElementById(uid);
 const toggle = document.getElementById(uid + '-toggle');
 if (!block) return;
 const isHidden = block.classList.contains('hidden');
 block.classList.toggle('hidden');
 if (toggle) toggle.textContent = isHidden ? '收起准备清单' : '展开准备清单';
}

function showAIGenerateTour() { showForm("studytour-ai-form"); }
async function generateStudyTour() {
 const data = { destination: g("st-ai-dest"), duration: g("st-ai-duration"), theme: document.getElementById("st-ai-theme")?.value || "红色" };
 await api("/api/study-tours/generate", "POST", data);
 closeForm("studytour-ai-form");
 fetchData("/api/study-tours", "studytour-list", renderStudyTourItem);
 updateBadge("AI 方案已生成");
}

function showStudyTourForm() { showForm("studytour-form"); }
async function saveStudyTour() {
 const courses = g("st-related-courses").split(",").map(function(s) { return s.trim(); }).filter(Boolean);
 const item = {
   title: g("st-title"),
   destination: g("st-dest"),
   duration: g("st-duration"),
   theme: g("st-theme"),
   objectives: g("st-objectives"),
   itinerary: g("st-itinerary"),
   budget: g("st-budget"),
   tasks: g("st-tasks"),
   preparation: g("st-preparation"),
   evaluation: g("st-evaluation"),
   expected_outcomes: g("st-expected-outcomes"),
   safety: g("st-safety"),
   resources: g("st-resources"),
   notes: g("st-notes"),
   target_grade: g("st-target-grade"),
   related_courses: courses,
   core_competencies: g("st-core-competencies"),
   ai_generated: false
 };
 await api("/api/study-tours", "POST", item);
 closeForm("studytour-form");
 fetchData("/api/study-tours", "studytour-list", renderStudyTourItem);
}

function renderAdminUserItem(user) {
 const isDisabled = (user.status || "") === "disabled";
 const isDeleted = (user.status || "") === "deleted";
 const isAdmin = !!user.is_admin;
 const nextStatus = isDisabled ? "active" : "disabled";
 const statusLabel = isDeleted ? "已注销" : (isDisabled ? "已停用" : "正常");
 const statusClass = isDeleted ? "is-disabled" : (isDisabled ? "is-disabled" : "is-active");
 const adminBadge = isAdmin ? '<span class="tag">管理员</span>' : "";
 const lastLogin = user.last_login_at ? esc(user.last_login_at) : "未记录";
 const createdAt = user.created_at ? esc(user.created_at) : "未记录";
 const statusButton = (isAdmin || isDeleted)
   ? ""
   : '<button class="btn btn-sm" onclick="toggleAdminUserStatus(\'' + jsArg(user.id) + '\',\'' + nextStatus + '\',\'' + jsArg(user.username) + '\')">' + (isDisabled ? "启用账号" : "停用账号") + '</button>';
 const passwordButton = isDeleted
   ? ""
   : '<button class="btn btn-secondary btn-sm" onclick="openAdminPasswordForm(\'' + jsArg(user.id) + '\',\'' + jsArg(user.username) + '\')">重置密码</button>';
 const deleteButton = (isAdmin || isDeleted)
   ? ""
   : '<button class="btn btn-danger btn-sm" onclick="cancelAdminUserAccount(\'' + jsArg(user.id) + '\',\'' + jsArg(user.username) + '\')">注销账号</button>';
 return '<div class="data-item">' +
   '<div class="data-item-header">' +
     '<div class="admin-user-header">' +
       '<div class="data-item-title">' + esc(user.username) + '</div>' +
       '<span class="admin-user-status ' + statusClass + '">' + statusLabel + '</span>' +
       adminBadge +
      '</div>' +
      '<div class="data-item-actions admin-user-actions">' +
        passwordButton +
        statusButton +
        deleteButton +
      '</div>' +
   '</div>' +
   '<div class="data-item-body">' +
     '<div class="admin-user-meta">' +
       '<div><strong>用户 ID</strong>' + esc(user.id || "") + '</div>' +
       '<div><strong>创建时间</strong>' + createdAt + '</div>' +
       '<div><strong>最近登录</strong>' + lastLogin + '</div>' +
     '</div>' +
   '</div>' +
 '</div>';
}

async function loadAdminUsers(showToast = false) {
 const container = document.getElementById("admin-users-list");
 const summary = document.getElementById("admin-users-summary");
 if (!container) return;
 if (typeof window.isAdminUser === "function" && !window.isAdminUser()) {
   if (summary) summary.textContent = "无权限";
   container.innerHTML = '<div class="admin-user-empty">只有管理员可以查看账号管理。</div>';
   if (typeof navigateTo === "function") navigateTo("dashboard");
   return;
 }
 if (typeof showLoading === "function") showLoading("admin-users-list");
 try {
   const data = await api("/api/admin/users");
   const items = Array.isArray(data.items) ? data.items : [];
   if (summary) summary.textContent = items.length + " 个账号";
   container.innerHTML = items.length
     ? items.map(renderAdminUserItem).join("")
     : '<div class="admin-user-empty">当前还没有注册账号。</div>';
   if (showToast && typeof showSuccess === "function") showSuccess("账号列表已刷新");
 } catch (e) {
   if (summary) summary.textContent = "加载失败";
   container.innerHTML = '<div class="admin-user-empty">账号列表加载失败，请稍后重试。</div>';
   if (String(e && e.message || "").includes("管理员") && typeof navigateTo === "function") {
     navigateTo("dashboard");
   }
 }
}

function openAdminPasswordForm(userId, username) {
 adminPasswordTarget = { userId: userId, username: username };
 const nameInput = document.getElementById("admin-password-username");
 const passwordInput = document.getElementById("admin-password-value");
 if (nameInput) nameInput.value = username || "";
 if (passwordInput) passwordInput.value = "";
 showForm("admin-password-form");
 if (passwordInput) passwordInput.focus();
}

function closeAdminPasswordForm() {
 adminPasswordTarget = null;
 const nameInput = document.getElementById("admin-password-username");
 const passwordInput = document.getElementById("admin-password-value");
 if (nameInput) nameInput.value = "";
 if (passwordInput) passwordInput.value = "";
 closeForm("admin-password-form");
}

async function submitAdminPasswordReset() {
 if (!adminPasswordTarget) return;
 const password = document.getElementById("admin-password-value")?.value || "";
 if (!password.trim()) {
   if (typeof showError === "function") showError("请输入新密码");
   return;
 }
 await api("/api/admin/users/" + encodeURIComponent(adminPasswordTarget.userId) + "/password", "POST", {
   password: password
 });
 closeAdminPasswordForm();
 if (typeof showSuccess === "function") showSuccess("密码已重置");
 loadAdminUsers();
}

async function toggleAdminUserStatus(userId, nextStatus, username) {
 const actionText = nextStatus === "disabled" ? "停用" : "启用";
 if (!confirm("确定要" + actionText + "账号“" + (username || "") + "”吗？")) return;
 await api("/api/admin/users/" + encodeURIComponent(userId) + "/status", "POST", {
   status: nextStatus
 });
 if (typeof showSuccess === "function") showSuccess("账号状态已更新");
 loadAdminUsers();
}

async function cancelAdminUserAccount(userId, username) {
 const name = username || "";
 if (!confirm("确定要注销账号“" + name + "”吗？注销后该账号将不能再登录，也不能再恢复为正常状态。")) return;
 await api("/api/admin/users/" + encodeURIComponent(userId) + "/delete-account", "POST", {});
 if (typeof showSuccess === "function") showSuccess("账号已注销");
 loadAdminUsers();
}

// ─── 虚拟展馆 ───
let exhibitHierarchy = [];
let ancestorDialogueHeroes = [];
let selectedAncestorHero = null;
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

function flattenAncestorHeroes() {
  var heroes = GREAT_LEADER_DIALOGUES.map(function(leader) {
    return Object.assign({}, leader);
  });
  ancestorDialogueHeroes = heroes;
  if (selectedAncestorHero) {
    selectedAncestorHero = heroes.find(function(hero) {
      return hero.name === selectedAncestorHero.name;
    }) || null;
  }
  return heroes;
}

async function loadAncestorDialogue() {
  try {
    flattenAncestorHeroes();
    renderAncestorList();
    if (!selectedAncestorHero && ancestorDialogueHeroes.length > 0) {
      selectAncestorHero(0);
    } else if (selectedAncestorHero) {
      renderAncestorChat(selectedAncestorHero);
    }
  } catch (e) {
    var list = document.getElementById("ancestor-list");
    if (list) list.innerHTML = '<div class="empty-state"><p>伟人资料加载失败</p></div>';
  }
}

function renderAncestorList() {
  var list = document.getElementById("ancestor-list");
  if (!list) return;
  var keyword = (document.getElementById("ancestor-search")?.value || "").trim();
  var source = ancestorDialogueHeroes.length ? ancestorDialogueHeroes : flattenAncestorHeroes();
  var filtered = source.filter(function(hero) {
    if (!keyword) return true;
    var text = [hero.name, hero.title, hero.bio, hero.detail_full, hero.siteTitle].join("\n");
    return text.indexOf(keyword) !== -1;
  });
  if (!filtered.length) {
    list.innerHTML = '<div class="empty-state"><p>没有匹配的伟人资料</p></div>';
    return;
  }
  list.innerHTML = filtered.map(function(hero) {
    var originalIndex = ancestorDialogueHeroes.indexOf(hero);
    var active = selectedAncestorHero === hero ? " active" : "";
    return '<button class="ancestor-card' + active + '" type="button" onclick="selectAncestorHero(' + originalIndex + ')">' +
      '<span class="ancestor-card-photo">' + (hero.photo ? '<img src="' + hero.photo + '" alt="' + esc(hero.name) + '">' : esc(hero.name).charAt(0)) + '</span>' +
      '<span class="ancestor-card-main">' +
        '<strong>' + esc(hero.name) + '</strong>' +
        '<small>' + esc(hero.title || hero.siteEra || "伟人") + '</small>' +
        '<em>' + esc(hero.siteEra || hero.siteTitle || "伟人精神谱系") + '</em>' +
      '</span>' +
    '</button>';
  }).join("");
}

function selectAncestorHero(index) {
  var hero = ancestorDialogueHeroes[index];
  if (!hero) return;
  selectedAncestorHero = hero;
  renderAncestorList();
  renderAncestorChat(hero);
}

function ancestorAiUnavailableMessage() {
  return "当前对话服务暂时没有接通。请稍后再问一次，我会继续接住你的问题。";
}

function appendAncestorChat(role, speaker, text) {
  var body = document.getElementById("ancestor-chat-body");
  if (!body) return;
  var hint = body.querySelector(".ancestor-chat-hint");
  if (hint) hint.remove();
  var className = role === "student" ? "chat-student" : (role === "guide" ? "chat-guide" : "chat-ancestor");
  var marker = role === "student" ? " data-role=\"student\"" : (role === "ancestor" ? " data-role=\"leader\"" : "");
  body.insertAdjacentHTML(
    "beforeend",
    '<div class="chat-bubble ' + className + '"' + marker + '><strong>' + esc(speaker) + '</strong><span>' + esc(text) + '</span></div>'
  );
  body.scrollTop = body.scrollHeight;
}

function collectAncestorHistory() {
  var history = [];
  document.querySelectorAll("#ancestor-chat-body .chat-bubble[data-role]").forEach(function(bubble) {
    var role = bubble.getAttribute("data-role");
    var content = bubble.querySelector("span")?.textContent || "";
    if (role && content) history.push({ role: role, content: content });
  });
  return history.slice(-8);
}

function removeAncestorThinking() {
  var thinking = document.getElementById("ancestor-thinking");
  if (thinking) thinking.remove();
}

async function askAncestorQuestion() {
  if (!selectedAncestorHero) return;
  var input = document.getElementById("ancestor-question");
  var question = (input?.value || "").trim();
  if (!question) {
    updateBadge("请先输入追问");
    return;
  }
  var history = collectAncestorHistory();
  appendAncestorChat("student", "学生", question);
  if (input) input.value = "";
  var body = document.getElementById("ancestor-chat-body");
  if (body) {
    body.insertAdjacentHTML("beforeend", '<div class="chat-bubble chat-ancestor ancestor-thinking" id="ancestor-thinking"><strong>' + esc(selectedAncestorHero.name) + '</strong><span>我在认真听你的问题，稍等片刻...</span></div>');
    body.scrollTop = body.scrollHeight;
  }
  try {
    var result = await api("/api/ancestor-dialogue", "POST", {
      leader: selectedAncestorHero.name,
      question: question,
      history: history
    });
    removeAncestorThinking();
    appendAncestorChat("ancestor", selectedAncestorHero.name, result.answer || ancestorAiUnavailableMessage());
  } catch (e) {
    removeAncestorThinking();
    appendAncestorChat("ancestor", selectedAncestorHero.name, ancestorAiUnavailableMessage());
  }
}

function renderAncestorChat(hero) {
  var panel = document.getElementById("ancestor-chat-panel");
  if (!panel) return;
  var detailButton = hero.detail_full ? '<button class="btn btn-secondary" onclick="showHeroDetail(event,\'' + jsArg(hero.name) + '\',\'' + jsArg(hero.title) + '\',\'' + jsArg(hero.detail_full) + '\',\'' + jsArg(hero.photo) + '\')">查看人物详情</button>' : "";
  panel.innerHTML =
    '<div class="ancestor-chat-hero">' +
      '<div class="ancestor-chat-photo">' + (hero.photo ? '<img src="' + hero.photo + '" alt="' + esc(hero.name) + '">' : esc(hero.name).charAt(0)) + '</div>' +
      '<div class="ancestor-chat-info">' +
        '<div class="ancestor-chat-kicker">' + esc(hero.siteTitle || "红色展馆") + '</div>' +
        '<h4>' + esc(hero.name) + '</h4>' +
        '<p>' + esc(hero.title || hero.bio) + '</p>' +
        '<div class="ancestor-chat-actions">' + detailButton + '</div>' +
      '</div>' +
    '</div>' +
    '<div class="ancestor-chat-body" id="ancestor-chat-body">' +
      '<div class="ancestor-chat-hint">输入你想聊的话，可以说近况、问理想，也可以像唠家常一样慢慢谈。</div>' +
    '</div>' +
    '<div class="ancestor-question-panel">' +
      '<label>输入问题</label>' +
      '<textarea id="ancestor-question" rows="3" placeholder="可以聊学习、生活、理想，也可以像唠家常一样说说近况，按 Ctrl + Enter 发送"></textarea>' +
    '</div>' +
    '<div class="form-actions">' +
      '<button class="btn btn-secondary" onclick="askAncestorQuestion()">发送</button>' +
    '</div>';
  bindAncestorQuestionInput();
}

function bindAncestorQuestionInput() {
  var input = document.getElementById("ancestor-question");
  if (!input) return;
  input.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      askAncestorQuestion();
    }
  });
}

function showExhibit(site) {
 if (!site) return;
 var stage = document.getElementById("exhibit-stage");
 var activeProvince = document.querySelector(".province-item.active");
 var backTitle = activeProvince ? activeProvince.getAttribute("data-province") : "";
 var backBtn = backTitle ? '<div class="ex-back" data-back="1">\u2190 \u8fd4\u56de\u666f\u70b9\u5217\u8868</div>' : "";

 // Image: carousel for ex039, SVG for others
 var imgHtml;
 if (site.id === "ex039") {
   var images = [1,2,3,4,5].map(function(n) { return "/static/images/site_ex039_0" + n + ".jpg"; });
   imgHtml = '<div class="ex-image"><div class="carousel-container" id="ex-carousel">' +
     '<div class="carousel-slides">' +
     images.map(function(src, i) { return '<img src="' + src + '" alt="' + esc(site.title) + '" data-index="' + i + '" onclick="openLightbox(' + i + ')" class="' + (i === 0 ? 'active' : '') + '" loading="lazy">'; }).join("") +
     '</div>' +
     '<button class="carousel-btn carousel-btn-prev" onclick="prevImage()">&#10094;</button>' +
     '<button class="carousel-btn carousel-btn-next" onclick="nextImage()">&#10095;</button>' +
     '<div class="carousel-dots">' +
     images.map(function(_, i) { return '<button class="carousel-dot' + (i === 0 ? ' active' : '') + '" data-index="' + i + '" onclick="goToImage(' + i + ')"></button>'; }).join("") +
     '</div></div></div>';
 } else {
   imgHtml = '<div class="ex-image"><img src="/static/images/site_' + site.id + '.svg" alt="' + esc(site.title) + '" loading="lazy"></div>';
 }

 var titleHtml = '<div class="ex-title">' + esc(site.title) + '</div>';
 var regionTag = site.region ? '<span class="tag">' + esc(site.region) + '</span>' : "";
 var metaHtml = '<div class="ex-era">' + regionTag + ' <span>' + esc(site.era) + '</span></div>';
 var featureHtml = makeFeatureTags(site);
 var descHtml = '<div class="ex-desc">' + esc(site.description) + '</div>';

 // Heroes section
 var sectionHtml = "";
 if (site.heroes && site.heroes.length > 0) {
   sectionHtml += '<div class="ex-section">';
   sectionHtml += '<div class="ex-section-nav-title">\u4fa8\u6218\u82f1\u96c4</div>';
    site.heroes.forEach(function(h) {
      var heroPhoto = resolveExhibitMediaPath(h.photo);
      var detailLink = h.detail_full ? '<button class="hero-detail-link" onclick="showHeroDetail(event,\'' + jsArg(h.name) + '\',\'' + jsArg(h.title) + '\',\'' + jsArg(h.detail_full) + '\',\'' + jsArg(heroPhoto) + '\')">\u25B6 \u67e5\u770b\u8be6\u7ec6\u4ecb\u7ecd</button>' : '';
      sectionHtml += '<div class="ex-hero-item">' +
       '<div class="ex-hero-avatar">' + (heroPhoto ? '<img src="' + heroPhoto + '" alt="' + esc(h.name) + '">' : esc(h.name).charAt(0)) + '</div>' +
       '<div class="ex-hero-info">' +
       '<div class="ex-hero-name">' + esc(h.name) + '</div>' +
       '<div class="ex-hero-title">' + esc(h.title) + '</div>' +
       '<div class="ex-hero-bio">' + esc(h.bio) + '</div>' +
       detailLink + '</div></div>';
   });
   sectionHtml += '</div>';
 }
 if (site.artifacts && site.artifacts.length > 0) {
   sectionHtml += '<div class="ex-section">';
   sectionHtml += '<div class="ex-section-nav-title">\u5386\u53f2\u6587\u7269</div>';
   site.artifacts.forEach(function(a) {
     var artifactPhoto = resolveExhibitMediaPath(a.photo);
     var artifactDetailLink = a.detail_full ? '<button class="hero-detail-link" onclick="showHeroDetail(event,\'' + jsArg(a.name) + '\',\'文物详细介绍\',\'' + jsArg(a.detail_full) + '\',\'' + jsArg(artifactPhoto) + '\')">\u25B6 \u67e5\u770b\u8be6\u7ec6\u4ecb\u7ecd</button>' : '';
     sectionHtml += '<div class="ex-artifact-item">' +
       '<div class="ex-artifact-photo">' + (artifactPhoto ? '<img src="' + artifactPhoto + '" alt="' + esc(a.name) + '">' : '<div class="ex-artifact-icon">\u25C6</div>') + '</div>' +
       '<div class="ex-artifact-body">' +
       '<div class="ex-artifact-name">' + esc(a.name) + '</div>' +
       '<div class="ex-artifact-desc">' + esc(a.description) + '</div>' +
       artifactDetailLink + '</div></div>';
   });
   sectionHtml += '</div>';
 }

 stage.innerHTML = backBtn + imgHtml + titleHtml + metaHtml + featureHtml + descHtml + sectionHtml;

 var be = stage.querySelector(".ex-back");
 if (be) { be.onclick = function() { showProvinceSites(backTitle); }; }
}


/* Extract feature tags from site data for visual highlights */
function makeFeatureTags(site) {
 var features = [];
 var text = (site.dialogue || "") + (site.description || "");

 // Determine site type
 if (/\u7eaa\u5ff5\u9986/.test(site.description)) features.push("\u2605 \u7eaa\u5ff5\u573a\u9986");
 else if (/\u535a\u7269\u9986/.test(site.description)) features.push("\u2605 \u535a\u7269\u9986\u85cf");
 else if (/\u9057\u5740/.test(site.description)) features.push("\u2605 \u5386\u53f2\u9057\u5740");
 else if (/\u6545\u5c45/.test(site.description)) features.push("\u2605 \u540d\u4eba\u6545\u5c45");
 else if (/\u9675\u56ed|\u70c8\u58eb/.test(site.description)) features.push("\u2605 \u70c8\u58eb\u9675\u56ed");
 else if (/\u65e7\u5740/.test(site.description)) features.push("\u2605 \u9769\u547d\u65e7\u5740");
 else if (/\u5e7f\u573a/.test(site.description)) features.push("\u2605 \u7eaa\u5ff5\u5e7f\u573a");
 else if (/\u6218\u5f79/.test(site.description)) features.push("\u2605 \u6218\u5f79\u9057\u5740");
 else features.push("\u2605 \u7ea2\u8272\u666f\u70b9");

 // Key figures
 var figures = ["\u6bdb\u6cfd\u4e1c","\u5468\u6069\u6765","\u6731\u5fb7","\u9093\u5c0f\u5e73","\u5218\u5c11\u5947","\u5f6d\u5fb7\u6000","\u9648\u6bc5","\u8d3a\u9f99","\u5218\u4f2f\u627f","\u5f90\u5411\u524d","\u6768\u9756\u5b87","\u8d75\u4e00\u66fc","\u96f7\u950b","\u7126\u88d5\u7984","\u738b\u8fdb\u559c","\u5218\u80e1\u5170","\u8463\u5b58\u745e","\u9ec4\u7ee7\u5149","\u674e\u5927\u949b","\u9c81\u8fc5","\u9648\u4e91"];
 var found = figures.filter(function(f) { return text.indexOf(f) !== -1; });
 if (found.length > 0) features.push("\u2606 " + found.slice(0, 3).join("\u3001"));

 // Spiritual keywords
 var kwList = ["\u7cbe\u795e","\u9769\u547d","\u6297\u6218","\u89e3\u653e","\u6539\u9769","\u5f00\u653e","\u594b\u6597","\u727a\u7272","\u5949\u732e","\u7231\u56fd","\u521d\u5fc3","\u4f7f\u547d","\u56e2\u7ed3"];
 var keywords = kwList.filter(function(kw) { return text.indexOf(kw) !== -1; });
 if (keywords.length > 0) features.push("\u25C6 " + keywords.slice(0, 4).join(" \u00B7 "));

 if (features.length === 0) return "";
 return '<div class="ex-features"><div class="ex-feature-list">' + features.map(function(f) { return '<span class="ex-feature-tag">' + f + '</span>'; }).join("") + '</div></div>';
}
var currentScriptDetail = null;

function buildScriptQuery() {
 const params = new URLSearchParams();
 const type = document.getElementById("script-filter-type")?.value || "";
 const source = document.getElementById("script-filter-source")?.value || "";
 const keyword = g("script-filter-keyword");
 if (type) params.set("type", type);
 if (source) params.set("source", source);
 if (keyword) params.set("keyword", keyword);
 const qs = params.toString();
 return "/api/scripts" + (qs ? "?" + qs : "");
}

function loadScripts() {
 return fetchData(buildScriptQuery(), "script-list", renderScriptItem);
}

function showScriptForm() { showForm("script-form"); }
async function saveScript() {
 const item = {
   title: g("sc-title"),
   type: document.getElementById("sc-type")?.value || "情景剧",
   theme: g("sc-theme"),
   usage: g("sc-usage"),
   audience: g("sc-audience"),
   duration: g("sc-duration"),
   style: g("sc-style"),
   characters: g("sc-characters"),
   content: g("sc-content"),
   notes: g("sc-notes")
 };
 await api("/api/scripts", "POST", item);
 closeForm("script-form"); loadScripts(); 
}
function showAIScriptForm() { showForm("script-ai-form"); }
async function generateScript() {
 const data = {
   type: document.getElementById("sc-ai-type")?.value || "演讲稿",
   theme: g("sc-ai-theme"),
   usage: document.getElementById("sc-ai-usage")?.value || "课堂导入",
   audience: document.getElementById("sc-ai-audience")?.value || "大学生",
   duration: document.getElementById("sc-ai-duration")?.value || "5分钟",
   style: document.getElementById("sc-ai-style")?.value || "青春励志",
   characters: g("sc-ai-characters"),
   keywords: g("sc-ai-keywords")
 };
 await api("/api/scripts/generate", "POST", data);
 closeForm("script-ai-form");
 loadScripts();
 updateBadge("AI 作品已生成");
}

async function generateQuickScript() {
 const type = document.getElementById("sc-quick-type")?.value || "演讲稿";
 const theme = g("sc-quick-theme");
 const usage = document.getElementById("sc-quick-usage")?.value || "课堂导入";
 const data = { type, theme, usage, audience: "大学生", duration: type === "情景剧" ? "8分钟" : "5分钟", style: type === "情景剧" ? "沉浸对话" : "青春励志" };
 await api("/api/scripts/generate", "POST", data);
 document.getElementById("sc-quick-theme").value = "";
 loadScripts();
 updateBadge("主题作品已生成");
}

function renderScriptItem(d) {
 const payload = encodeURIComponent(JSON.stringify(d || {})).replace(/'/g, "%27");
 const contentPayload = encodeURIComponent(d.content || "").replace(/'/g, "%27");
 const meta = [
   d.type || "",
   d.theme ? "主题：" + d.theme : "",
   d.usage ? "用途：" + d.usage : "",
   d.audience ? "对象：" + d.audience : "",
   d.duration ? "时长：" + d.duration : "",
   d.ai_generated ? "主题生成" : "手动添加"
 ].filter(Boolean).map(item => "<span>" + esc(item) + "</span>").join("");
 const preview = (d.content || "").slice(0, 220);
 return `
   <div class="data-item script-card">
     <div class="data-item-header">
       <div>
         <div class="data-item-title">${d.ai_generated ? '<span class="ai-badge">AI</span>' : ""}${esc(d.title || "未命名作品")}</div>
         <div class="data-item-meta">${meta}</div>
       </div>
       <div class="data-item-actions">
         <button class="btn btn-sm" onclick="openScriptDetailPayload('${payload}')">查看</button>
         <button class="btn btn-sm" onclick="copyScriptPayload('${contentPayload}')">复制</button>
         <button class="btn btn-danger btn-sm" onclick="deleteItem('/api/scripts','${esc(d.id)}','script-list',renderScriptItem)">删除</button>
       </div>
     </div>
     <div class="data-item-body">${esc(preview)}${(d.content || "").length > 220 ? "..." : ""}</div>
   </div>`;
}

function openScriptDetailPayload(payload) {
 try {
   openScriptDetail(JSON.parse(decodeURIComponent(payload || "")));
 } catch (e) {
   if (typeof showError === "function") showError("作品打开失败");
 }
}

function openScriptDetail(item) {
 currentScriptDetail = item || {};
 document.getElementById("script-detail-type").textContent = currentScriptDetail.type || "创作助手";
 document.getElementById("script-detail-title").textContent = currentScriptDetail.title || "作品详情";
 const meta = [
   currentScriptDetail.theme ? "主题：" + currentScriptDetail.theme : "",
   currentScriptDetail.usage ? "用途：" + currentScriptDetail.usage : "",
   currentScriptDetail.audience ? "对象：" + currentScriptDetail.audience : "",
   currentScriptDetail.duration ? "时长：" + currentScriptDetail.duration : "",
   currentScriptDetail.style ? "风格：" + currentScriptDetail.style : "",
   currentScriptDetail.characters ? "角色：" + currentScriptDetail.characters : "",
 ].filter(Boolean).map(item => "<span>" + esc(item) + "</span>").join("");
 document.getElementById("script-detail-meta").innerHTML = meta;
 var content = currentScriptDetail.content || "";
 if (currentScriptDetail.notes) content += "\n\n【使用提示】\n" + currentScriptDetail.notes;
 document.getElementById("script-detail-content").textContent = content;
 showForm("script-detail-modal");
}

function closeScriptDetail() {
 closeForm("script-detail-modal");
}

function handleScriptDetailBackdrop(event) {
 if (event.target && event.target.id === "script-detail-modal") closeScriptDetail();
}

function copyScriptText(text) {
 const value = text || "";
 if (!value) return;
 if (navigator.clipboard && navigator.clipboard.writeText) {
   navigator.clipboard.writeText(value).then(() => updateBadge("已复制作品全文")).catch(() => {});
 }
}

function copyScriptPayload(payload) {
 copyScriptText(decodeURIComponent(payload || ""));
}

function copyCurrentScript() {
 copyScriptText(currentScriptDetail?.content || "");
}

document.addEventListener("click", function(e) {
 const trigger = e.target.closest("[data-open-textbook='1']");
 if (!trigger) return;
 if (e.target.closest(".data-item-actions")) return;
 const bookId = trigger.getAttribute("data-book-id") || "";
 const bookTitle = trigger.getAttribute("data-book-title") || "";
 if (!bookId) return;
 openTextbook(bookId, bookTitle);
});

function formatDetailBody(text) {
  if (!text) return '';
  // First escape, then apply rich formatting
  var raw = esc(text);
  // Highlight 「...」 with a styled span
  raw = raw.replace(/\u300c([^\u300d]*)\u300d/g, '<b class="d-em">\u300c$1\u300d</b>');
  var lines = raw.split(/\\n/);
  var html = '';
  var inPara = false;
  var isFirstBody = true;
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i].trim();
    if (!line) {
      if (inPara) { html += '</p>'; inPara = false; }
      if (html) html += '<hr class="detail-sep">';
      continue;
    }
    if (/^[\[\(]\u3010.*\u3011[\]\)]?$/.test(line)) {
      if (inPara) { html += '</p>'; inPara = false; }
      html += '<div class="detail-section-title"><span>' + line + '</span></div>';
      isFirstBody = true;
    } else {
      if (!inPara) {
        html += '<p' + (isFirstBody ? ' class="d-lead"' : '') + '>';
        inPara = true;
        isFirstBody = false;
      }
      html += line + '<br>';
    }
  }
  if (inPara) html += '</p>';
  return html || '<p>' + esc(text) + '</p>';
}

// ─── 英雄详细介绍弹窗 ───
function showHeroDetail(event, name, title, detail, photo) {
  if (event) event.stopPropagation();
  var overlay = document.getElementById("hero-detail-modal");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "hero-detail-modal";
    overlay.className = "hero-detail-overlay";
    overlay.onclick = function(e) { if (e.target === overlay) closeHeroDetail(); };
    document.body.appendChild(overlay);
  }
  var photoHtml = photo ? '<div class="hero-detail-photo"><img src="' + photo + '" alt="' + esc(name) + '"></div>' : '';
  overlay.innerHTML =
    '<div class="hero-detail-card">' +
    '<div class="hero-detail-close" onclick="closeHeroDetail()">&times;</div>' +
    photoHtml +
    '<div class="hero-detail-content">' +
    '<h3 class="hero-detail-name">' + esc(name) + '</h3>' +
    '<div class="hero-detail-title">' + esc(title) + '</div>' +
    '<div class="hero-detail-body">' + formatDetailBody(detail) + '</div>' +
    '</div>' +
    '</div>';
  overlay.style.display = "flex";
}
function closeHeroDetail() {
  var overlay = document.getElementById("hero-detail-modal");
  if (overlay) overlay.style.display = "none";
}
document.addEventListener("keydown", function(e) {
  if (e.key === "Escape") closeHeroDetail();
});
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
function applyTheme(theme) {
  const nextTheme = theme || "default";
  document.body.className = nextTheme === "default" ? "" : `theme-${nextTheme}`;
  localStorage.setItem("sz-theme", nextTheme);
  document.querySelectorAll(".theme-card").forEach(card => {
    card.classList.toggle("selected", card.dataset.theme === nextTheme);
  });
}

document.querySelectorAll(".theme-card").forEach(el => {
 el.addEventListener("click", () => {
   applyTheme(el.dataset.theme);
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
 applyTheme(theme);
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

// ---- 教学模式功能 ----
function toggleReaderFontSize() {
  var el = document.getElementById("reader-content");
  var sizes = ["", "font-l", "font-xl"];
  var cur = 0;
  for (var i = 0; i < sizes.length; i++) {
    if (el.classList.contains(sizes[i])) cur = i;
  }
  var next = (cur + 1) % sizes.length;
  el.classList.remove(sizes[cur]);
  if (sizes[next]) el.classList.add(sizes[next]);
}
function toggleFullscreen(elId) {
  var el = document.getElementById(elId);
  if (!document.fullscreenElement) {
    if (el.requestFullscreen) {
      el.requestFullscreen();
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    }
  }
}
window.showTextbookForm = showTextbookForm;
window.esc = esc;
window.saveTextbook = saveTextbook;
window.openTextbook = openTextbook;
window.closeTextbookReader = closeTextbookReader;
window.toggleReaderFontSize = toggleReaderFontSize;
window.toggleFullscreen = toggleFullscreen;
window.loadDataAssist = loadDataAssist;
window.loadAdminUsers = loadAdminUsers;
window.openAdminPasswordForm = openAdminPasswordForm;
window.closeAdminPasswordForm = closeAdminPasswordForm;
window.submitAdminPasswordReset = submitAdminPasswordReset;
window.toggleAdminUserStatus = toggleAdminUserStatus;
window.cancelAdminUserAccount = cancelAdminUserAccount;
window.smartImportDocument = smartImportDocument;
window.showCoursewareForm = showCoursewareForm;
window.saveCourseware = saveCourseware;
window.showSyllabusForm = showSyllabusForm;
window.saveSyllabus = saveSyllabus;
window.showReferenceForm = showReferenceForm;
window.saveReference = saveReference;
window.showAIGenerateTour = showAIGenerateTour;
window.generateStudyTour = generateStudyTour;
window.showStudyTourForm = showStudyTourForm;
window.saveStudyTour = saveStudyTour;
window.toggleStudyTourMore = toggleStudyTourMore;
window.showExhibit = showExhibit;
window.selectSite = selectSite;
window.loadAncestorDialogue = loadAncestorDialogue;
window.renderAncestorList = renderAncestorList;
window.selectAncestorHero = selectAncestorHero;
window.bindAncestorQuestionInput = bindAncestorQuestionInput;
window.askAncestorQuestion = askAncestorQuestion;
window.showHeroDetail = showHeroDetail;
window.closeHeroDetail = closeHeroDetail;
window.showScriptForm = showScriptForm;
window.saveScript = saveScript;
window.showAIScriptForm = showAIScriptForm;
window.generateScript = generateScript;
window.generateQuickScript = generateQuickScript;
window.loadScripts = loadScripts;
window.openScriptDetailPayload = openScriptDetailPayload;
window.closeScriptDetail = closeScriptDetail;
window.handleScriptDetailBackdrop = handleScriptDetailBackdrop;
window.copyScriptPayload = copyScriptPayload;
window.copyCurrentScript = copyCurrentScript;
window.showForm = showForm;
window.closeForm = closeForm;
window.setSidebarMode = setSidebarMode;
window.toggleShowIds = toggleShowIds;

// ─── 轮播状态 ───
var carouselImages = [];
(function initCarouselGlobals() {
  for (var i = 1; i <= 5; i++) {
    carouselImages.push('/static/images/site_ex039_0' + i + '.jpg');
  }
})();
function showCarouselImage(index) {
  var slides = document.querySelectorAll('#ex-carousel .carousel-slides img');
  var dots = document.querySelectorAll('#ex-carousel .carousel-dot');
  slides.forEach(function(img, i) { img.classList.toggle('active', i === index); });
  dots.forEach(function(dot, i) { dot.classList.toggle('active', i === index); });
}
function goToImage(index) { showCarouselImage(index); }
function prevImage() {
  var slides = document.querySelectorAll('#ex-carousel .carousel-slides img');
  var current = -1;
  slides.forEach(function(img, i) { if (img.classList.contains('active')) current = i; });
  var next = (current - 1 + slides.length) % slides.length;
  showCarouselImage(next);
}
function nextImage() {
  var slides = document.querySelectorAll('#ex-carousel .carousel-slides img');
  var current = -1;
  slides.forEach(function(img, i) { if (img.classList.contains('active')) current = i; });
  var next = (current + 1) % slides.length;
  showCarouselImage(next);
}
function openLightbox(index) {
  var overlay = document.createElement('div');
  overlay.className = 'lightbox-overlay';
  overlay.id = 'ex-lightbox';
  overlay.innerHTML = '<button class="lightbox-close" onclick="closeLightbox()">&#10005;</button>' +
    '<img src="' + carouselImages[index] + '" alt="\u8fbd\u6c88\u6218\u5f79\u7eaa\u5ff5\u9986">';
  overlay.onclick = function(e) { if (e.target === overlay) closeLightbox(); };
  document.body.appendChild(overlay);
}
function closeLightbox() {
  var lb = document.getElementById('ex-lightbox');
  if (lb) lb.remove();
}
window.showCarouselImage = showCarouselImage;
window.goToImage = goToImage;
window.prevImage = prevImage;
window.nextImage = nextImage;
window.openLightbox = openLightbox;
window.closeLightbox = closeLightbox;
//   dead exports and unused globals were removed during 2026-07-02 cleanup.
