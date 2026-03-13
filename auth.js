/**
 * 开元时代 · 认证模块
 * 所有需要保护的页面在 <head> 末尾引入此文件即可
 * <script src="auth-config.js"></script>
 * <script src="auth.js"></script>
 */
(function () {
  'use strict';

  const cfg = window.KAIYUAN_AUTH;
  if (!cfg) return; // 未配置则跳过

  // ── 工具函数 ─────────────────────────────────────
  function getToken()  { return localStorage.getItem(cfg.STORAGE_KEY); }
  function getExpire() { return parseInt(localStorage.getItem(cfg.EXPIRE_KEY) || '0', 10); }

  function saveSession() {
    const expire = Date.now() + cfg.SESSION_DAYS * 86400 * 1000;
    localStorage.setItem(cfg.STORAGE_KEY,  'authenticated');
    localStorage.setItem(cfg.EXPIRE_KEY,   expire.toString());
  }

  function clearSession() {
    localStorage.removeItem(cfg.STORAGE_KEY);
    localStorage.removeItem(cfg.EXPIRE_KEY);
  }

  function isAuthenticated() {
    return getToken() === 'authenticated' && getExpire() > Date.now();
  }

  // ── 验证已登录 → 直接放行 ─────────────────────────
  if (isAuthenticated()) return;

  // ── 未登录 → 注入登录遮罩 ─────────────────────────
  // 先隐藏 body 内容，避免闪烁
  document.documentElement.style.visibility = 'hidden';

  window.addEventListener('DOMContentLoaded', function () {
    document.documentElement.style.visibility = '';

    const overlay = document.createElement('div');
    overlay.id = 'ky-auth-overlay';
    overlay.innerHTML = `
      <style>
        #ky-auth-overlay {
          position: fixed; inset: 0; z-index: 99999;
          background: linear-gradient(160deg, #F8F6F2 0%, #F0EAE0 100%);
          display: flex; align-items: center; justify-content: center;
          font-family: "PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,sans-serif;
        }
        #ky-auth-box {
          background: #fff;
          border: 1px solid rgba(155,123,58,0.2);
          border-radius: 20px;
          padding: 2.8rem 2.4rem 2.4rem;
          width: 100%; max-width: 380px;
          box-shadow: 0 8px 40px rgba(100,80,40,0.12);
          text-align: center;
        }
        #ky-auth-logo {
          font-size: 2rem;
          margin-bottom: 0.4rem;
          letter-spacing: 0.05em;
        }
        #ky-auth-title {
          font-size: 1.1rem; font-weight: 700;
          color: #2C2A26; margin-bottom: 0.3rem;
        }
        #ky-auth-sub {
          font-size: 0.78rem; color: #8A8070; margin-bottom: 2rem;
        }
        #ky-auth-input {
          width: 100%;
          border: 1.5px solid rgba(155,123,58,0.3);
          border-radius: 10px;
          padding: 0.75rem 1rem;
          font-size: 1rem;
          color: #2C2A26;
          background: #FDFCF9;
          outline: none;
          text-align: center;
          letter-spacing: 0.12em;
          transition: border-color 0.2s;
          box-sizing: border-box;
        }
        #ky-auth-input:focus {
          border-color: rgba(155,123,58,0.7);
        }
        #ky-auth-btn {
          width: 100%; margin-top: 1rem;
          background: linear-gradient(135deg, #9B7B3A, #C9A84C);
          color: #fff; border: none;
          border-radius: 10px; padding: 0.75rem;
          font-size: 0.92rem; font-weight: 600;
          cursor: pointer; letter-spacing: 0.05em;
          transition: opacity 0.2s;
        }
        #ky-auth-btn:hover { opacity: 0.88; }
        #ky-auth-err {
          color: #C0392B; font-size: 0.8rem;
          margin-top: 0.7rem; min-height: 1.2em;
        }
        #ky-auth-hint {
          font-size: 0.72rem; color: rgba(138,128,112,0.6);
          margin-top: 1.8rem;
        }
      </style>
      <div id="ky-auth-box">
        <div id="ky-auth-logo">🏛️</div>
        <div id="ky-auth-title">${cfg.SITE_NAME}</div>
        <div id="ky-auth-sub">${cfg.SITE_SUBTITLE}</div>
        <input id="ky-auth-input" type="password"
               placeholder="请输入访问密码"
               autocomplete="current-password" />
        <button id="ky-auth-btn">进入工作台</button>
        <div id="ky-auth-err"></div>
        <div id="ky-auth-hint">session 有效期 ${cfg.SESSION_DAYS} 天 · 内部人员专属</div>
      </div>
    `;
    document.body.appendChild(overlay);

    const input = document.getElementById('ky-auth-input');
    const btn   = document.getElementById('ky-auth-btn');
    const err   = document.getElementById('ky-auth-err');

    function tryLogin() {
      const val = input.value.trim();
      if (val === cfg.PASSWORD) {
        saveSession();
        overlay.style.transition = 'opacity 0.4s';
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 400);
      } else {
        err.textContent = '密码错误，请重试';
        input.value = '';
        input.focus();
        // 抖动动画
        input.style.borderColor = '#C0392B';
        setTimeout(() => { input.style.borderColor = ''; }, 1200);
      }
    }

    btn.addEventListener('click', tryLogin);
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') tryLogin();
    });
    input.focus();
  });

  // ── 全局登出函数（可在控制台调用 kaiyuanLogout()）──
  window.kaiyuanLogout = function () {
    clearSession();
    location.reload();
  };
})();
