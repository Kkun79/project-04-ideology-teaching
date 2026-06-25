// ════════════════════════════════════════════
//  Toast 通知系统 + 路由增强
// ════════════════════════════════════════════

// ── Toast ──
function ensureToastContainer() {
  let c = document.getElementById('toast-container');
  if (!c) {
    c = document.createElement('div');
    c.id = 'toast-container';
    document.body.appendChild(c);
  }
  return c;
}

function showToast(msg, type = 'info', duration = 4000) {
  const container = ensureToastContainer();
  const t = document.createElement('div');
  t.className = 'toast toast-' + type;
  t.textContent = msg;
  container.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity 0.3s'; setTimeout(() => t.remove(), 300); }, duration);
}

function showError(msg) { showToast(msg, 'error', 5000); }
function showSuccess(msg) { showToast(msg, 'success', 3000); }

// ── Loading ──
function showLoading(containerId, msg = '加载中...') {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = `<div class="loading-overlay">${msg}</div>`;
}

// ── Hash 路由 ──
// 支持 URL hash 指向模块： #textbooks, #cases-list 等
// 页面加载时和 hashchange 时自动导航
window.addEventListener('hashchange', () => {
  const hash = location.hash.replace('#', '');
  if (hash) navigateTo(hash);
});

// 页面加载后检查 hash
document.addEventListener('DOMContentLoaded', () => {
  const hash = location.hash.replace('#', '');
  if (hash && typeof navigateTo === 'function') {
    // 延迟等页面渲染完毕
    setTimeout(() => navigateTo(hash), 200);
  }
});

// ── 增强 fetch：出错时 toast ──
async function safeFetch(url, opts = {}) {
  try {
    const res = await fetch(url, opts);
    if (!res.ok) {
      const detail = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(detail.detail || `请求失败 (${res.status})`);
    }
    return res.json();
  } catch (e) {
    if (!opts._silent) showError(e.message);
    throw e;
  }
}

window.showToast = showToast;
window.showError = showError;
window.showSuccess = showSuccess;
window.showLoading = showLoading;
window.safeFetch = safeFetch;
