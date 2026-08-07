'use strict';

/* ══════════════════════════════════════════════════════════════
   THE LAST NOTE · admin.js
   Shared across every /admin-panel/ page: auth guard, API calls,
   toast notifications. Reuses the same 'access_token' localStorage
   key the storefront's login modal already writes to
   (templates/partials/_auth_modals.html), so logging in as an
   admin from the normal site login also gets you into the panel.
   ══════════════════════════════════════════════════════════════ */

const ADMIN_API_BASE = 'http://127.0.0.1:8000/api';

/* ── JWT decoding (client-side only, for UI — the server always
   re-checks the real role on every admin request; this just decides
   whether to show the panel or bounce to login) ── */
function decodeJwt(token) {
  try {
    const payload = token.split('.')[1];
    const json = decodeURIComponent(
      atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
        .split('')
        .map(c => '%' + c.charCodeAt(0).toString(16).padStart(2, '0'))
        .join('')
    );
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function getAdminSession() {
  const token = localStorage.getItem('access_token');
  if (!token) return null;
  const payload = decodeJwt(token);
  if (!payload) return null;
  if (payload.exp && Date.now() >= payload.exp * 1000) return null; // expired
  return { token, payload };
}

/* Every admin page except login.html calls this immediately. */
function requireAdminSession() {
  const session = getAdminSession();
  if (!session) {
    window.location.href = '/admin-panel/login/';
    return null;
  }
  renderAdminUserChip(session.payload);
  return session;
}

function renderAdminUserChip(payload) {
  const nameEl = document.getElementById('adminUserName');
  const roleEl = document.getElementById('adminUserRole');
  const avatarEl = document.getElementById('adminUserAvatar');
  const label = payload.full_name || payload.email || 'Admin';
  if (nameEl) nameEl.textContent = label;
  if (roleEl) roleEl.textContent = 'Role ID ' + (payload.role_id ?? '—');
  if (avatarEl) avatarEl.textContent = label.trim().charAt(0).toUpperCase();
}

function adminLogout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.location.href = '/admin-panel/login/';
}

/* ── API helper: attaches the JWT, handles JSON, surfaces DRF-style
   errors (field: [messages]) as a single readable string, and bounces
   to login on 401/403 so an expired/non-admin session doesn't just
   sit there silently failing every request. ── */
async function adminApi(path, { method = 'GET', body = null, isForm = false } = {}) {
  const session = getAdminSession();
  const headers = {};
  if (session) headers['Authorization'] = `Bearer ${session.token}`;
  if (!isForm && body != null) headers['Content-Type'] = 'application/json';

  const res = await fetch(`${ADMIN_API_BASE}${path}`, {
    method,
    headers,
    body: body == null ? undefined : (isForm ? body : JSON.stringify(body)),
  });

  if (res.status === 401 || res.status === 403) {
    let detail = 'Admin access required.';
    try {
      const data = await res.json();
      detail = data.detail || data.message || detail;
    } catch { /* ignore */ }
    showAdminToast(detail, 'error');
    setTimeout(() => { window.location.href = '/admin-panel/login/'; }, 1100);
    throw new Error(detail);
  }

  let data = null;
  try { data = await res.json(); } catch { /* empty body, e.g. some 204s */ }

  if (!res.ok) {
    throw new Error(formatApiError(data));
  }
  return data;
}

function formatApiError(data) {
  if (!data) return 'Something went wrong.';
  if (typeof data === 'string') return data;
  if (data.error) return data.error;
  if (data.detail) return data.detail;
  // DRF validation errors: { field: ["message", ...], ... }
  const parts = [];
  for (const [field, messages] of Object.entries(data)) {
    const msg = Array.isArray(messages) ? messages.join(' ') : String(messages);
    parts.push(field === 'non_field_errors' ? msg : `${field}: ${msg}`);
  }
  return parts.length ? parts.join(' | ') : 'Something went wrong.';
}

/* ── Toast ── */
let adminToastTimer = null;
function showAdminToast(message, type = 'default') {
  const el = document.getElementById('adminToast');
  if (!el) return;
  el.textContent = message;
  el.className = 'show' + (type !== 'default' ? ` ${type}` : '');
  clearTimeout(adminToastTimer);
  adminToastTimer = setTimeout(() => { el.className = ''; }, 3200);
}

/* ── Sidebar active-link highlight ── */
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname.replace(/\/$/, '');
  document.querySelectorAll('.admin-nav a').forEach(a => {
    const href = a.getAttribute('href').replace(/\/$/, '');
    if (href === path) a.classList.add('active');
  });
  document.getElementById('adminSidebarToggle')?.addEventListener('click', () => {
    document.querySelector('.admin-sidebar')?.classList.toggle('open');
  });
});
