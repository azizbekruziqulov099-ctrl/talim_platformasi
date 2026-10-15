import test from 'node:test';
import assert from 'node:assert/strict';
import { authRequest } from './auth/authClient.js';
import fs from 'node:fs';

test('REV146: 502/503/504 — server qayta ishga tushmoqda: tarmoq xatosi (kirish o‘zi qayta urinadi)', async () => {
  const old = globalThis.fetch;
  try {
    globalThis.fetch = async () => ({ ok: false, status: 503, json: async () => null });
    await assert.rejects(authRequest('https://x', '/auth/config'), (e) => e.network === true && /javob bermadi/.test(e.message));
    globalThis.fetch = async () => ({ ok: false, status: 500, json: async () => ({ detail: 'Ichki xato' }) });
    await assert.rejects(authRequest('https://x', '/auth/config'), (e) => !e.network && e.message === 'Ichki xato');
  } finally { globalThis.fetch = old; }
});

test('REV146: saqlangan akkaunt tokeni faqat 401/403 da o‘chadi, so‘rov osilib qolmaydi', () => {
  const src = fs.readFileSync(new URL('./auth/KabutarLogin.jsx', import.meta.url), 'utf8');
  assert.match(src, /response\.status === 401 \|\| response\.status === 403\) \{ natija = "tugagan"/);
  assert.match(src, /setTimeout\(\(\) => controller\.abort\(\), 12000\)/);
  assert.match(src, /retry = setTimeout\(\(\) => setConfigAttempt/);
});

test('REV147: boshqa manzildan ochilgan ilova asosiy saytga o‘tadi (bir marta), to‘g‘ri manzilda — o‘tmaydi', async () => {
  const { wrongSite, redirectIfWrongSite } = await import('./auth/siteGuard.js');
  const cfg = { site: 'https://talimplatformasi-frontend-production.up.railway.app', origins: ['https://talimplatformasi-frontend-production.up.railway.app', 'https://talimkabutar.uz'] };
  assert.equal(wrongSite(cfg, 'https://talimkabutar.uz'), '');
  assert.equal(wrongSite(cfg, 'https://talimplatformasi-frontend-production.up.railway.app/'), '');
  assert.equal(wrongSite(cfg, 'https://eski-manzil.up.railway.app'), cfg.site);
  assert.equal(wrongSite({}, 'https://eski-manzil.up.railway.app'), '');
  assert.equal(wrongSite(cfg, 'http://localhost:5173'), '');
  const store = new Map(); const storage = { getItem: (k) => store.get(k), setItem: (k, v) => store.set(k, v) };
  let went = '';
  const location = { origin: 'https://eski-manzil.up.railway.app', hash: '', assign: (u) => { went = u; } };
  assert.equal(redirectIfWrongSite(cfg, { location, storage }), true);
  assert.equal(went, cfg.site + '/');
  assert.equal(redirectIfWrongSite(cfg, { location, storage }), false);   // aylanib qolmaydi
});
