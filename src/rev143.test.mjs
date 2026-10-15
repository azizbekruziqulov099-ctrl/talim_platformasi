import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { JAMOA_NOM, jamoaNomi, pleyoffUstunlar, qolganVaqt, javon, yulduzlar, sanoqOlcham, KUBOK } from './chempionat/chempionatRules.js';

test('REV143: jamoa nomlari uz/ru/en; admin bergan nom ustun', () => {
  for (const [k, v] of Object.entries(JAMOA_NOM)) for (const l of ['uz', 'ru', 'en']) assert.ok(v[l], `${k} ${l}`);
  assert.equal(jamoaNomi({ kalit: 'sherlar' }, 'ru'), 'Львы');
  assert.equal(jamoaNomi({ kalit: 'sherlar', nomi: 'Quyoshlar' }, 'en'), 'Quyoshlar');
  assert.equal(jamoaNomi({ kalit: 'sherlar', nomi: '21' }, 'uz'), 'Sherlar 21');
});

test('REV143: pley-off ustunlari tartibda, 3-o‘rin alohida', () => {
  const u = [{ bosqich: 'guruh', tartib: 0 }, { bosqich: 'final', tartib: 0 }, { bosqich: '1/2', tartib: 1 }, { bosqich: '1/2', tartib: 0 }, { bosqich: '3-orin', tartib: 0 }];
  const r = pleyoffUstunlar(u);
  assert.deepEqual(r.ustun.map((x) => x.bosqich), ['1/2', 'final']);
  assert.deepEqual(r.ustun[0].uchrashuvlar.map((x) => x.tartib), [0, 1]);
  assert.equal(r.uchinchi.bosqich, '3-orin');
});

test('REV143: vaqt, javon, yulduz, sanash o‘lchami', () => {
  assert.equal(qolganVaqt(26 * 3600000), '1 kun 2 soat');
  assert.equal(qolganVaqt(10 * 60000), '10 daq.');
  assert.deepEqual(javon([{ kubok: 'ishtirok' }, { kubok: 'oltin' }, { kubok: 'bronza' }]).map((k) => k.kubok), ['oltin', 'bronza', 'ishtirok']);
  assert.equal(yulduzlar(10, 10), 3); assert.equal(yulduzlar(0, 10), 0);
  for (let n = 1; n <= 10; n++) {   // n ta narsa 4:3 kartaga sig'adi
    const s = sanoqOlcham(n); const c = Math.floor(100 / s); const r = Math.ceil(n / c);
    assert.ok(r * s <= 75, `${n}: ${s}`);
  }
  for (const k of ['oltin', 'kumush', 'bronza', 'yulduz', 'ishtirok']) assert.ok(KUBOK[k]);
});

test('REV143: O‘yinlar markazi va App chempionatni ochadi', () => {
  const app = fs.readFileSync(new URL('./App.jsx', import.meta.url), 'utf8');
  const hub = fs.readFileSync(new URL('./games/OyinlarMarkazi.jsx', import.meta.url), 'utf8');
  assert.ok(/import\("\.\/chempionat\/Chempionat\.jsx"\)/.test(app));
  assert.ok(/tab === "chempionat"/.test(app) && /"chempionat"\]\)/.test(app));
  assert.ok(/key: "chempionat"/.test(hub) && /admin = false/.test(hub));
});
