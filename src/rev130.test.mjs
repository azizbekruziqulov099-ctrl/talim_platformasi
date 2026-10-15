import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { darsBoshi, stepKind } from './kid/kidStageRules.js';

const st = (sarlavha, turi = 'tushuncha', sahna) => ({ sarlavha, turi, ...(sahna ? { sahna } : {}) });

test('REV130: only the previous topic is reviewed — later review blocks are dropped and moved to the start', () => {
  const steps = [
    st('🍂 Qish', 'kirish'),
    st('🔁 Eslaymiz: 🍁 barg 🧺 savat'),            // 1 dars oldingi — qoladi
    st('🔁 Eslaymiz: ⭐ yulduz 😴 uyqu'),            // 3 dars oldingi — olib tashlanadi
    st('❄️ qor'), st('⛄ qorbobo'), st('🎲 Top-chi', 'topshiriq'), st('🌟 Bugun o‘rgandik', 'xulosa'),
  ];
  const { takror, qolgan } = darsBoshi(steps, 'Qish');
  assert.deepEqual(takror.map((s) => s.sarlavha), ['🔁 Eslaymiz: 🍁 barg 🧺 savat']);
  assert.deepEqual(qolgan.map((s) => s.sarlavha), ['🍂 Qish', '❄️ qor', '⛄ qorbobo', '🎲 Top-chi', '🌟 Bugun o‘rgandik']);
  assert.ok(!qolgan.some((s) => stepKind(s) === 'review'));
});

test('REV130: split review chunks (no title, same scene) stay together; English titles too', () => {
  const steps = [st('Intro', 'kirish'), { sarlavha: '🔁 Remember: cat', turi: 'tushuncha', sahna: 'r1' }, { turi: 'tushuncha', sahna: 'r1' },
    { sarlavha: '🔁 Remember: dog', turi: 'tushuncha', sahna: 'r2' }, { turi: 'tushuncha', sahna: 'r2' }, st('🐦 bird')];
  const { takror, qolgan } = darsBoshi(steps, 'Animals');
  assert.equal(takror.length, 2);
  assert.deepEqual(qolgan.map((s) => s.sarlavha), ['Intro', '🐦 bird']);
});

test('REV130: a whole review topic and lessons without review are unchanged', () => {
  const steps = [st('🔁 1-bo‘lim: takrorlaymiz', 'kirish'), st('🔁 Eslaymiz: a'), st('🔁 Eslaymiz: b')];
  assert.deepEqual(darsBoshi(steps, '1-bo‘lim takrori: salom, yana!'), { takror: [], qolgan: steps });
  const oddiy = [st('Salom', 'kirish'), st('🐱 mushuk')];
  assert.deepEqual(darsBoshi(oddiy, 'Hayvonlar'), { takror: [], qolgan: oddiy });
  assert.deepEqual(darsBoshi(undefined, 'x'), { takror: [], qolgan: [] });
});

test('REV130: kindergarten home is a simple subject list — no heavy building/corridor pictures', () => {
  const src = fs.readFileSync(new URL('./kid/BogchaOlami.jsx', import.meta.url), 'utf8');
  assert.ok(!/\.webp/.test(src), 'rasm importi qolmasin');
  assert.ok(!/olamRules/.test(src));
  assert.match(src, /ol-grid/);
});

test('REV130: fast game polling skips hidden pages and overlapping requests', () => {
  for (const f of ['./battle/Bellashuv.jsx', './games/Turnir.jsx', './games/BoardGame.jsx']) {
    const src = fs.readFileSync(new URL(f, import.meta.url), 'utf8');
    assert.match(src, /band\.v \|\| globalThis\.document\?\.hidden/, f);
  }
});

test('REV130: production static server — compression, long cache for hashed assets, SPA fallback, no path escape', async () => {
  const { spawn } = await import('node:child_process');
  const os = await import('node:os');
  const path = await import('node:path');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'srv130-'));
  fs.mkdirSync(path.join(dir, 'assets'));
  fs.writeFileSync(path.join(dir, 'index.html'), '<html>' + 'x'.repeat(3000) + '</html>');
  fs.writeFileSync(path.join(dir, 'assets', 'main-AbC12345.js'), 'console.log(1);'.repeat(400));
  const port = 18000 + Math.floor(Math.random() * 1000);
  const srv = spawn(process.execPath, [new URL('../server.mjs', import.meta.url).pathname, '--host', '127.0.0.1', '--port', String(port)], { env: { ...process.env, STATIC_DIR: dir } });
  try {
    for (let i = 0; i < 50; i++) { try { await fetch(`http://127.0.0.1:${port}/healthz`); break; } catch { await new Promise((r) => setTimeout(r, 100)); } }
    const a = await fetch(`http://127.0.0.1:${port}/assets/main-AbC12345.js`, { headers: { 'accept-encoding': 'gzip' } });
    assert.equal(a.status, 200);
    assert.match(a.headers.get('cache-control'), /immutable/);
    assert.equal(a.headers.get('content-encoding'), 'gzip');
    const spa = await fetch(`http://127.0.0.1:${port}/maktab/5`);
    assert.equal(spa.status, 200);
    assert.equal(spa.headers.get('cache-control'), 'no-cache');
    assert.equal((await fetch(`http://127.0.0.1:${port}/assets/yoq-AAAAAAAA.js`)).status, 404);
    const etag = spa.headers.get('etag');
    assert.equal((await fetch(`http://127.0.0.1:${port}/`, { headers: { 'if-none-match': etag } })).status, 304);
  } finally {
    srv.kill();
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('REV130: Railway start command keeps working — preview script now runs the static server', () => {
  const pkg = JSON.parse(fs.readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
  assert.equal(pkg.scripts.preview, 'node server.mjs');
  assert.match(pkg.scripts.start, /^node server\.mjs/);
});

test('REV138: izoh variant with lessons wins when the interface-language variant has none', async () => {
  const { izohTanla } = await import('./curriculum/izohTanlov.js');
  const fan = (nom, dars) => ({ nom, dars_turi: '', institution_type: 'bogcha', sinflar: [{ sinf: '4-5 yosh', mavzular: [{ nomi: 'Salom', dars_bor: dars }] }] });
  const list = [fan('Ingliz tili', false), fan('Ingliz tili (izoh: rus)', true), fan('Ingliz tili (izoh: ingliz)', false), fan('Mantiq', true)];
  assert.deepEqual(izohTanla(list, 'uz').map((f) => f.nom), ['Ingliz tili (izoh: rus)', 'Mantiq']);
  // haqiqiy holat: o'zbekcha izohli kitob yo'q, ruscha va inglizchasi bor — o'zbek interfeysida ruscha izoh
  const arab = [fan('Arab tili', false), fan('Arab tili (izoh: ingliz)', true), fan('Arab tili (izoh: rus)', true)];
  assert.deepEqual(izohTanla(arab, 'uz').map((f) => f.nom), ['Arab tili (izoh: rus)']);
  assert.deepEqual(izohTanla(arab, 'en').map((f) => f.nom), ['Arab tili (izoh: ingliz)']);
  const hamma = [fan('Arab tili', true), fan('Arab tili (izoh: rus)', true)];
  assert.deepEqual(izohTanla(hamma, 'ru').map((f) => f.nom), ['Arab tili (izoh: rus)']);   // mos variantda dars bor — o'sha
  assert.deepEqual(izohTanla(hamma, 'uz').map((f) => f.nom), ['Arab tili']);
  const yoq = [fan('Turk tili', false), fan('Turk tili (izoh: rus)', false)];
  assert.deepEqual(izohTanla(yoq, 'uz').map((f) => f.nom), ['Turk tili']);                // hech birida dars yo'q — avvalgidek
});

test('REV139: mixed speech — Uzbek parts go to the server, foreign words to the device voice when it has one', async () => {
  const { segmentlar, reja, aralashKerak, brauzerOvozi } = await import('./speech/aralashOvoz.js');
  const ovozlar = [{ name: 'Google US English', lang: 'en-US', localService: false }, { name: 'Microsoft Irina', lang: 'ru-RU', localService: true },
    { name: 'Google русский', lang: 'ru-RU', localService: false }];
  assert.deepEqual(segmentlar('Salom! [en]Good morning![/en] Endi sen ayt: [en]Hello[/en] ⏸'), [
    { til: 'uz', matn: 'Salom!' }, { til: 'en', matn: 'Good morning!' }, { til: 'uz', matn: 'Endi sen ayt:' }, { til: 'en', matn: 'Hello' }, { til: 'uz', matn: '⏸' }]);
  // REV140: rus tili har doim serverning tabiiy ovozida; robot (oddiy) ovozlar ishlatilmaydi
  assert.equal(brauzerOvozi('ru', ovozlar), null);
  assert.equal(brauzerOvozi('en', ovozlar).name, 'Google US English');
  assert.equal(brauzerOvozi('en', [{ name: 'Microsoft David', lang: 'en-US', localService: true }]), null);
  assert.equal(brauzerOvozi('en', [{ name: 'Microsoft Aria Online (Natural)', lang: 'en-US', localService: false }]).name, 'Microsoft Aria Online (Natural)');
  assert.equal(aralashKerak('Bu — [ru]Привет![/ru]', ovozlar, { qurilma: true }), false);
  assert.equal(brauzerOvozi('ko', ovozlar), null);
  const r = reja('Salom! [en]Good morning![/en] Endi sen ayt: [en]Hello[/en] ⏸', { ovozlar, takror: true, qurilma: true });
  assert.deepEqual(r.map((q) => q.tur), ['server', 'brauzer', 'server', 'brauzer', 'pauza']);
  assert.equal(r[4].ms, 1800);
  // qurilmada koreyscha ovoz yo'q — koreys so'zi o'zbekcha bilan birga serverga (teg saqlanadi)
  const k = reja('Bu — [ko]안녕[/ko]! Yana ayt.', { ovozlar, qurilma: true });
  assert.deepEqual(k, [{ tur: 'server', matn: 'Bu — [ko]안녕[/ko] ! Yana ayt.' }]);
  assert.equal(aralashKerak('Faqat o\'zbekcha gap.', ovozlar, { qurilma: true }), false);
  assert.equal(aralashKerak('[en]Apple[/en]', ovozlar, { qurilma: true }), true);
  assert.equal(aralashKerak('[en]Apple[/en]', ovozlar), false);   // REV145: odatda hamma tillar serverda
  assert.equal(aralashKerak('[en]Apple[/en]', [], { qurilma: true }), false);   // ovoz yo'q qurilma — avvalgidek server
});
