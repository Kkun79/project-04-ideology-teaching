// ============================================================
//  思政教学程序 - 通用前端辅助
// ============================================================

const AUTH_TOKEN_KEY = "project04_auth_token";
const AUTH_USER_KEY = "project04_auth_user";
let authMode = "login";
let authConfig = {
  registration_mode: "open",
  registration_enabled: true,
  invite_required: false
};
let currentAuthUser = null;
let currentAuthToken = "";

function getAuthToken() {
  return currentAuthToken || "";
}

function authHeaders(extra = {}) {
  const headers = Object.assign({}, extra);
  const token = getAuthToken();
  if (token) headers.Authorization = "Bearer " + token;
  return headers;
}

function setAuthSession(payload) {
  currentAuthUser = payload.user || null;
  currentAuthToken = payload.token || "";
  clearStoredAuthSession();
  unlockApp(currentAuthUser || {});
}

function clearAuthSession() {
  currentAuthUser = null;
  currentAuthToken = "";
  clearStoredAuthSession();
}

function clearStoredAuthSession() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
  sessionStorage.removeItem(AUTH_TOKEN_KEY);
  sessionStorage.removeItem(AUTH_USER_KEY);
}

function getAuthUser() {
  return currentAuthUser;
}

function isAdminUser() {
  const user = getAuthUser();
  return !!(user && user.is_admin);
}

function syncAdminEntryVisibility() {
  const navItem = document.getElementById("admin-nav-item");
  const quickEntry = document.getElementById("admin-users-entry");
  const allowed = isAdminUser();
  if (navItem) navItem.classList.toggle("hidden", !allowed);
  if (quickEntry) quickEntry.classList.toggle("hidden", !allowed);
  if (!allowed) {
    const panel = document.getElementById("panel-admin-users");
    if (panel && panel.classList.contains("active") && typeof navigateTo === "function") {
      navigateTo("dashboard");
    }
  }
}

function setAuthMessage(message, isError = false) {
  const box = document.getElementById("auth-message");
  if (!box) return;
  box.textContent = message || "";
  box.classList.toggle("auth-error", !!isError);
}

function setAuthMode(mode) {
  if (mode === "register" && !authConfig.registration_enabled) {
    authMode = "login";
  } else {
    authMode = mode === "register" ? "register" : "login";
  }
  const title = document.getElementById("auth-title");
  const subtitle = document.getElementById("auth-subtitle");
  const submit = document.getElementById("auth-submit");
  const switchBtn = document.getElementById("auth-switch");
  const password = document.getElementById("auth-password");
  const inviteWrap = document.getElementById("auth-invite-wrap");
  const inviteInput = document.getElementById("auth-invite-code");
  if (title) title.textContent = authMode === "register" ? "注册账号" : "账号登录";
  if (subtitle) {
    if (authMode === "register" && authConfig.invite_required) {
      subtitle.textContent = "仅限已获批准的用户注册，请输入邀请码";
    } else if (authMode === "register") {
      subtitle.textContent = "创建账号后直接进入教学工作台";
    } else if (authConfig.registration_mode === "closed") {
      subtitle.textContent = "当前不开放公开注册";
    } else if (authConfig.invite_required) {
      subtitle.textContent = "登录后进入教学工作台，如需注册请先获取邀请码";
    } else {
      subtitle.textContent = "登录后进入教学工作台";
    }
  }
  if (submit) submit.textContent = authMode === "register" ? "注册并进入" : "登录";
  if (switchBtn) {
    if (!authConfig.registration_enabled) {
      switchBtn.classList.add("hidden");
      switchBtn.disabled = true;
    } else {
      switchBtn.classList.remove("hidden");
      switchBtn.disabled = false;
      switchBtn.textContent = authMode === "register"
        ? "已有账号？返回登录"
        : (authConfig.invite_required ? "没有账号？输入邀请码注册" : "还没有账号？注册账号");
    }
  }
  if (password) password.autocomplete = authMode === "register" ? "new-password" : "current-password";
  if (inviteWrap) inviteWrap.classList.toggle("hidden", !(authMode === "register" && authConfig.invite_required));
  if (inviteInput) {
    inviteInput.required = authMode === "register" && authConfig.invite_required;
    if (authMode !== "register" || !authConfig.invite_required) inviteInput.value = "";
  }
  setAuthMessage("");
}

async function loadAuthConfig() {
  try {
    const res = await fetch("/api/auth/config");
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "读取注册配置失败");
    authConfig = Object.assign({}, authConfig, data || {});
  } catch (e) {
    authConfig = {
      registration_mode: "open",
      registration_enabled: true,
      invite_required: false
    };
  }
}

function lockAppForAuth(message = "") {
  currentAuthUser = null;
  currentAuthToken = "";
  clearStoredAuthSession();
  const badge = document.getElementById("currentUserBadge");
  if (badge) badge.textContent = "";
  document.body.classList.remove("auth-pending");
  document.body.classList.remove("auth-unlocked");
  document.body.classList.add("auth-locked");
  syncAdminEntryVisibility();
  if (message) setAuthMessage(message, true);
}

function unlockApp(user) {
  currentAuthUser = user || null;
  document.body.classList.remove("auth-pending", "auth-locked");
  document.body.classList.add("auth-unlocked");
  const badge = document.getElementById("currentUserBadge");
  if (badge) {
    const label = currentAuthUser?.username ? "当前账号：" + currentAuthUser.username : "";
    badge.textContent = currentAuthUser?.is_admin ? (label ? label + " · 管理员" : "管理员") : label;
  }
  syncAdminEntryVisibility();
  setAuthMessage("");
}

async function submitAuthForm(event) {
  event.preventDefault();
  const username = document.getElementById("auth-username")?.value?.trim() || "";
  const password = document.getElementById("auth-password")?.value || "";
  const inviteCode = document.getElementById("auth-invite-code")?.value?.trim() || "";
  const btn = document.getElementById("auth-submit");
  if (!username || !password) {
    setAuthMessage("请填写账号和密码", true);
    return;
  }
  if (authMode === "register" && authConfig.invite_required && !inviteCode) {
    setAuthMessage("请输入邀请码", true);
    return;
  }
  if (btn) btn.disabled = true;
  setAuthMessage(authMode === "register" ? "正在注册..." : "正在登录...");
  try {
    const payload = { username, password };
    if (authMode === "register" && authConfig.invite_required) payload.invite_code = inviteCode;
    const res = await fetch(authMode === "register" ? "/api/auth/register" : "/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
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
  clearAuthSession();
  lockAppForAuth("");
}

async function logoutAccount() {
  const token = getAuthToken();
  if (token) {
    await fetch("/api/auth/logout", { method: "POST", headers: authHeaders() }).catch(() => {});
  }
  clearAuthSession();
  lockAppForAuth("已退出登录");
}

function showDeleteAccountForm() {
  if (isAdminUser()) {
    if (typeof showError === "function") showError("管理员账号不能在这里注销");
    return;
  }
  const form = document.getElementById("delete-account-form");
  const password = document.getElementById("delete-account-password");
  const confirmation = document.getElementById("delete-account-confirmation");
  if (password) password.value = "";
  if (confirmation) confirmation.value = "";
  if (form) form.classList.remove("hidden");
}

function closeDeleteAccountForm() {
  const form = document.getElementById("delete-account-form");
  if (form) form.classList.add("hidden");
}

async function submitDeleteAccount() {
  const password = document.getElementById("delete-account-password")?.value || "";
  const confirmation = document.getElementById("delete-account-confirmation")?.value?.trim() || "";
  const btn = document.getElementById("delete-account-submit");
  if (!password || confirmation !== "注销账号") {
    if (typeof showError === "function") showError("请输入当前密码，并在确认框输入“注销账号”");
    return;
  }
  if (!confirm("确认注销当前账号？注销后该账号将不能再登录。")) return;
  if (btn) btn.disabled = true;
  try {
    const res = await fetch("/api/auth/delete-account", {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ password, confirmation })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "注销账号失败");
    clearAuthSession();
    closeDeleteAccountForm();
    lockAppForAuth("账号已注销，请使用其他账号登录");
  } catch (e) {
    if (typeof showError === "function") showError(e.message || "注销账号失败");
  } finally {
    if (btn) btn.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", async function() {
  const form = document.getElementById("auth-form");
  const switchBtn = document.getElementById("auth-switch");
  if (form) form.addEventListener("submit", submitAuthForm);
  if (switchBtn) switchBtn.addEventListener("click", function() {
    setAuthMode(authMode === "register" ? "login" : "register");
  });
  await loadAuthConfig();
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
window.clearAuthSession = clearAuthSession;
window.lockAppForAuth = lockAppForAuth;
window.logoutAccount = logoutAccount;
window.showDeleteAccountForm = showDeleteAccountForm;
window.closeDeleteAccountForm = closeDeleteAccountForm;
window.submitDeleteAccount = submitDeleteAccount;
window.getAuthUser = getAuthUser;
window.isAdminUser = isAdminUser;
window.syncAdminEntryVisibility = syncAdminEntryVisibility;
