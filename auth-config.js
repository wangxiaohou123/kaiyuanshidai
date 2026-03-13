/**
 * 开元时代 · 工作台访问配置
 * ──────────────────────────────
 * 修改密码：只需更改 PASSWORD 值，然后运行 ./auto-sync.sh 推送更新
 * session 有效期：7天（可调整 SESSION_DAYS）
 */
const KAIYUAN_AUTH = {
  // ── 访问密码 ──────────────────────────────────
  PASSWORD: "kaiyuan2026",

  // ── Session 有效期（天）────────────────────────
  SESSION_DAYS: 7,

  // ── 站点信息 ──────────────────────────────────
  SITE_NAME: "开元时代 · 内部工作台",
  SITE_SUBTITLE: "CEO战略看板 · 班子作业系统",

  // ── 存储 Key ──────────────────────────────────
  STORAGE_KEY: "kaiyuan_auth_token",
  EXPIRE_KEY:  "kaiyuan_auth_expire",
};
