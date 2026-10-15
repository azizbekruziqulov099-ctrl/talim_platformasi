import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { sahnaKorinish, qutiga, sahnaga } from './kid/harakat/harakatRules.js';
import { XONALAR } from './kid/xonalar/xonaLugat.js';

const src = (p) => fs.readFileSync(new URL(p, import.meta.url), 'utf8');

test('REV144: telefon ekrani — sahna kvadrat qutida qirqiladi, barmoq koordinatalari to‘g‘ri o‘giriladi', () => {
  assert.deepEqual(sahnaKorinish(400, 300), { x0: 0, y0: 0, vw: 400, vh: 300 });
  const k = sahnaKorinish(300, 300);           // kvadrat: 50..350 ko'rinadi
  assert.equal(k.x0, 50); assert.equal(k.vw, 300);
  const b = qutiga({ x: 0.68, y: 0.62, r: 0.12 }, k);
  assert.ok(Math.abs(b.x - (0.68 * 400 - 50) / 300) < 1e-9 && Math.abs(b.r - 0.16) < 1e-9);
  const s = sahnaga({ x: b.x, y: b.y }, k);
  assert.ok(Math.abs(s.x - 0.68) < 1e-9 && Math.abs(s.y - 0.62) < 1e-9);
  const keng = sahnaKorinish(800, 300);         // keng ekran: tepa-past qirqiladi
  assert.equal(keng.vw, 400); assert.ok(keng.y0 > 0);
});

test('REV144: sahnalardagi barcha rasmlar ro‘yxatda bor; muhim nuqtalar kvadrat qirqimda ko‘rinadi', () => {
  const sah = src('./kid/harakat/sahnalar.jsx');
  const ras = src('./kid/harakat/rasmlar.js');
  const nomlar = new Set([...sah.matchAll(/\bn(?:=|: )"([a-z0-9_]+)"/g)].map((m) => m[1]).concat([...sah.matchAll(/HR\.([a-z0-9_]+)/g)].map((m) => m[1])));
  for (const kadr of ['raqs1', 'raqs2', 'raqs3']) nomlar.add(kadr);
  for (const n of nomlar) {
    assert.ok(new RegExp(`\\b${n}: \\{ src: r_${n},`).test(ras), `rasm yo'q: ${n}`);
    assert.ok(fs.existsSync(new URL(`./kid/harakat/rasm/${n}.webp`, import.meta.url)), `fayl yo'q: ${n}`);
  }
  const k = sahnaKorinish(1, 1);
  for (const m of sah.matchAll(/(boshi|nishon|markaz): \{ x: ([\d.]+), y: ([\d.]+)/g)) {
    const b = qutiga({ x: +m[2], y: +m[3] }, k);
    assert.ok(b.x > 0.05 && b.x < 0.95 && b.y > 0.05 && b.y < 0.95, `${m[0]} kvadratda ko'rinmaydi`);
  }
  assert.ok(/createPortal/.test(src('./kid/harakat/HarakatYoli.jsx')) && /createPortal/.test(src('./kid/xonalar/TilXonalari.jsx')));
});

test('REV144: xonalar — yangi chizilgan fonlar (7 ta) va narsalar rasmi bor', () => {
  const ras = src('./kid/xonalar/rasmlar.js');
  for (const x of XONALAR) {
    assert.ok(x.fon, x.id);
    assert.ok(new RegExp(`\\b${x.fon}: f_${x.fon}`).test(ras), `fon: ${x.id}`);
    assert.ok(fs.existsSync(new URL(`./kid/xonalar/fon/${x.fon}.webp`, import.meta.url)), x.fon);
    for (const id of x.narsalar) assert.ok(!x.odamlar.includes(id), `${x.id}: ${id} ikki marta`);
  }
});

test('REV144: darsda emoji o‘rniga chizilgan rasm va so‘zga mos harakat', async () => {
  const { emojiRasm, harakatTuri, sozId, HARAKAT_TURLARI } = await import('./kid/rasmHarakat.js');
  const R = { cat: '/cat.webp', apple: '/apple.webp' };
  assert.deepEqual(emojiRasm('🍎', R), { id: 'apple', src: '/apple.webp' });
  assert.equal(emojiRasm('🍎🍎🍎', R), null);          // sanoq kartasi — emoji qoladi
  assert.equal(emojiRasm('🍎 🍎', R), null);
  assert.equal(sozId({ soz: 'Apple', emoji: '' }), 'apple');
  assert.equal(harakatTuri('jump'), 'sakra');
  assert.equal(harakatTuri('bus'), 'yur');
  assert.equal(harakatTuri('apple'), 'dumala');
  assert.equal(harakatTuri(null), 'chiq');
  const css = src('./kid/ustozSahna.css');
  for (const t of HARAKAT_TURLARI) assert.ok(new RegExp(`\\.us-pic \\.an-${t}[,{]`).test(css), `css: ${t}`);
});
