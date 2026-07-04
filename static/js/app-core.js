// ============================================================
//  思政教学程序 - 通用前端辅助
// ============================================================

const AUTH_TOKEN_KEY = "project04_auth_token";
const AUTH_USER_KEY = "project04_auth_user";
let authMode = "login";

function getAuthToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY) || "";
}

function authHeaders(extra = {}) {
  const headers = Object.assign({}, extra);
  const token = getAuthToken();
  if (token) headers.Authorization = "Bearer " + token;
  return headers;
}

function setAuthSession(payload) {
  localStorage.setItem(AUTH_TOKEN_KEY, payload.token || "");
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(payload.user || {}));
  unlockApp(payload.user || {});
}

function clearAuthSession() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
}

function setAuthMessage(message, isError = false) {
  const box = document.getElementById("auth-message");
  if (!box) return;
  box.textContent = message || "";
  box.classList.toggle("auth-error", !!isError);
}

function setAuthMode(mode) {
  authMode = mode === "register" ? "register" : "login";
  const title = document.getElementById("auth-title");
  const subtitle = document.getElementById("auth-subtitle");
  const submit = document.getElementById("auth-submit");
  const switchBtn = document.getElementById("auth-switch");
  const password = document.getElementById("auth-password");
  if (title) title.textContent = authMode === "register" ? "注册账号" : "账号登录";
  if (subtitle) subtitle.textContent = authMode === "register" ? "创建账号后直接进入教学工作台" : "登录后进入教学工作台";
  if (submit) submit.textContent = authMode === "register" ? "注册并进入" : "登录";
  if (switchBtn) switchBtn.textContent = authMode === "register" ? "已有账号？返回登录" : "还没有账号？注册账号";
  if (password) password.autocomplete = authMode === "register" ? "new-password" : "current-password";
  setAuthMessage("");
}

function lockAppForAuth(message = "") {
  document.body.classList.remove("auth-unlocked");
  document.body.classList.add("auth-locked");
  if (message) setAuthMessage(message, true);
}

function unlockApp(user) {
  document.body.classList.remove("auth-pending", "auth-locked");
  document.body.classList.add("auth-unlocked");
  const badge = document.getElementById("currentUserBadge");
  if (badge) badge.textContent = user?.username ? "当前账号：" + user.username : "";
  setAuthMessage("");
}

async function submitAuthForm(event) {
  event.preventDefault();
  const username = document.getElementById("auth-username")?.value?.trim() || "";
  const password = document.getElementById("auth-password")?.value || "";
  const btn = document.getElementById("auth-submit");
  if (!username || !password) {
    setAuthMessage("请填写账号和密码", true);
    return;
  }
  if (btn) btn.disabled = true;
  setAuthMessage(authMode === "register" ? "正在注册..." : "正在登录...");
  try {
    const res = await fetch(authMode === "register" ? "/api/auth/register" : "/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "操作失败");
    setAuthSession(data);
    if (typeof showSuccess === "function") showSuccess(authMode === "register" ? "注册成功" : "登录成功");
  } catch (e) {
    setAuthMessage(e.message, true);
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function checkExistingAuth() {
  const token = getAuthToken();
  if (!token) {
    lockAppForAuth("");
    return;
  }
  try {
    const res = await fetch("/api/auth/me", { headers: authHeaders() });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "登录状态已失效");
    unlockApp(data.user || {});
  } catch (e) {
    clearAuthSession();
    lockAppForAuth("登录状态已失效，请重新登录");
  }
}

async function logoutAccount() {
  const token = getAuthToken();
  if (token) {
    await fetch("/api/auth/logout", { method: "POST", headers: authHeaders() }).catch(() => {});
  }
  clearAuthSession();
  lockAppForAuth("已退出登录");
}

document.addEventListener("DOMContentLoaded", function() {
  const form = document.getElementById("auth-form");
  const switchBtn = document.getElementById("auth-switch");
  if (form) form.addEventListener("submit", submitAuthForm);
  if (switchBtn) switchBtn.addEventListener("click", function() {
    setAuthMode(authMode === "register" ? "login" : "register");
  });
  setAuthMode("login");
  checkExistingAuth();
});

async function api(url, method = "GET", body = null) {
 const opts = { headers: authHeaders({ "Content-Type": "application/json" }) };
 if (body && method !== "PUT") { opts.method = "POST"; opts.body = JSON.stringify(body); }
 if (method === "DELETE") opts.method = "DELETE";
 if (method === "PUT") { opts.method = "PUT"; opts.body = JSON.stringify(body); }
 try {
   const res = await fetch(url, opts);
   if (res.status === 401) {
     clearAuthSession();
     lockAppForAuth("请先登录后再使用程序");
   }
   if (!res.ok) {
     const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
     if (typeof showError === "function") showError(err.detail || "请求失败");
     throw new Error(err.detail || `API error: ${res.status}`);
   }
   const data = await res.json();
   if (method !== "GET") _notifyDataChanged();
   return data;
 } catch (e) {
   if (e.name !== "Error" || !e.message.includes("API error")) {
     if (typeof showError === "function") showError(e.message);
   }
   throw e;
 }
}

var _dataChangeTimer = null;
function _notifyDataChanged() {
  if (_dataChangeTimer) clearTimeout(_dataChangeTimer);
  _dataChangeTimer = setTimeout(function() { }, 300);
}

async function fetchData(url, listId, renderFn) {
 const container = document.getElementById(listId);
 if (!container) return;
 if (typeof showLoading === "function") showLoading(listId);
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

function resolveExhibitMediaPath(rawPath, defaultPrefix = "/static/images/") {
 const value = String(rawPath || "").trim();
 if (!value) return "";
 if (/^(https?:)?\/\//i.test(value) || value.startsWith("data:")) return value;
 if (value.startsWith("/static/") || value.startsWith("/uploads/")) return value;
 return defaultPrefix + value.replace(/^\/+/, "");
}

function deleteItem(baseUrl, id, listId, renderFn) {
 if (!confirm("确定要删除吗？")) return;
 api(`${baseUrl}/${id}`, "DELETE").then(() => {
   if (typeof showSuccess === "function") showSuccess("删除成功");
   fetchData(baseUrl, listId, renderFn);
  }).catch(() => {});
}

function g(id) { return document.getElementById(id)?.value?.trim() || ""; }
function esc(s) { if (!s) return ""; const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
function jsArg(s) { return String(s || "").replace(/\\/g, "\\\\").replace(/'/g, "\\'").replace(/\r?\n/g, " "); }

window.authHeaders = authHeaders;
window.lockAppForAuth = lockAppForAuth;
window.logoutAccount = logoutAccount;
