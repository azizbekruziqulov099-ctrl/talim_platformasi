import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { HARAKATLAR, BOLIMLAR, IZOH_H, BOLIM_XONA } from './kid/harakat/harakatLugat.js';
import { TILLAR, XONALAR } from './kid/xonalar/xonaLugat.js';
import {
  buyruq, manosi, izohGap, imoKalit, yolTugunlari, yolHolati, raundlar, juftmi, yulduzHisob, cheksizVaqt,
  kuchYangila, bugungiTakror, tilNatija, organdi, yulduzYoz, kuchYoz, cheksizYoz, imoTanish, takrorHarakatlari,
} from './kid/harakat/harakatRules.js';

const mem = () => { const m = new Map(); return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)) }; };
const rng = (() => { let s = 11; return () => ((s = (s * 16807) % 2147483647) / 2147483647); })();

test('REV141: 5 bo‘lim × 4 harakat; har buyruq 11 tilda, qisqa va to‘liq shaklda', () => {
  assert.equal(BOLIMLAR.length, 5);
  assert.equal(HARAKATLAR.length, 20);
  for (const b of BOLIMLAR) assert.equal(HARAKATLAR.filter((h) => h.bolim === b.id).length, 4, b.id);
  for (const h of HARAKATLAR) for (const l of TILLAR) {
    assert.ok(String(h.s[l] || '').trim(), `${h.id} s ${l}`);
    assert.ok(String(h.g[l] || '').trim(), `${h.id} g ${l}`);
  }
  // bitta bo'limda ikki harakatning qisqa buyrug'i bir xil bo'lmasin (bola adashmasin)
  for (const b of BOLIMLAR) for (const l of TILLAR) {
    const s = HARAKATLAR.filter((h) => h.bolim === b.id).map((h) => h.s[l]);
    assert.equal(new Set(s).size, s.length, `${b.id} ${l}: ${s}`);
  }
  for (const x of Object.values(BOLIM_XONA)) assert.ok(XONALAR.some((r) => r.id === x), x);
});

test('REV141: har harakatning sahnasi va imo-ishora maslahati bor (uz, ru, en)', () => {
  const sahna = fs.readFileSync(new URL('./kid/harakat/sahnalar.jsx', import.meta.url), 'utf8');
  for (const h of HARAKATLAR) {
    assert.ok(new RegExp(`\\b${h.id}: \\{ C:`).test(sahna), `${h.id} sahnasi`);
    for (const l of ['uz', 'ru', 'en']) assert.ok(IZOH_H[imoKalit(h.imo)]?.[l], `${h.id} ${imoKalit(h.imo)} ${l}`);
  }
});

test('REV141: tushuntirish kursning izoh tilida, buyruq o‘rganilayotgan tilda', () => {
  assert.equal(izohGap('manosi', 'uz', { t: buyruq('open', 'en'), til: 'en', i: manosi('open', 'uz', false) }), 'Och! — [en]Open![/en]');
  assert.equal(izohGap('manosi', 'ru', { t: buyruq('open', 'en'), til: 'en', i: manosi('open', 'ru', false) }), '[ru]Открой![/ru] [ru]—[/ru] [en]Open![/en]'.replace('[ru]Открой![/ru] [ru]—[/ru]', '[ru]Открой! —[/ru]'));
  assert.equal(izohGap('sen', 'en'), '[en]Now you![/en]');
  assert.equal(buyruq('kick', 'de', true), 'Schieß den Ball!');
  assert.equal(manosi('kick', 'tr'), 'To‘pni tep!');   // izoh faqat uz/ru/en — boshqasi o'zbekchaga tushadi
});

test('REV141: yo‘l bosqichma-bosqich ochiladi; takror bo‘limlar orasida; oxirida cheksiz o‘yin', () => {
  const t = yolTugunlari();
  assert.equal(t[0].id, 'organ:uy');
  assert.equal(t[1].id, 'oyna:uy');
  assert.equal(t[t.length - 1].id, 'cheksiz');
  assert.ok(t.findIndex((x) => x.id === 'takror:2') > t.findIndex((x) => x.id === 'oyna:hovli'));
  assert.deepEqual(takrorHarakatlari(2).length, 8);
  const st = mem();
  let h = yolHolati(tilNatija('en', st));
  assert.deepEqual(h.slice(0, 3).map((x) => x.holat), ['ochiq', 'qulf', 'qulf']);
  for (const x of ['open', 'close', 'lighton', 'lightoff']) organdi('en', x, st);
  h = yolHolati(tilNatija('en', st));
  assert.deepEqual(h.slice(0, 3).map((x) => x.holat), ['tugadi', 'ochiq', 'qulf']);
  yulduzYoz('en', 'oyna:uy', 2, st);
  yulduzYoz('en', 'oyna:uy', 1, st);   // pastroq natija eng yaxshisini o'chirmaydi
  assert.equal(tilNatija('en', st).yulduz['oyna:uy'], 2);
  h = yolHolati(tilNatija('en', st), (x) => (x === 'bolalar' ? 3 : 0));
  assert.equal(h.find((x) => x.holat === 'ochiq').id, 'organ:hovli');
  assert.deepEqual(tilNatija('ru', st).organ, {});   // har til alohida
});

test('REV141: raundlar — har harakat kamida bir marta, ketma-ket takror yo‘q, juftlar bir raundda emas', () => {
  const pool = ['open', 'close', 'lighton', 'lightoff'];
  for (const yosh of ['kichik', 'orta', 'katta']) {
    const r = raundlar(pool, { yosh, rng });
    assert.equal(r.length, yosh === 'kichik' ? 6 : yosh === 'orta' ? 8 : 10);
    for (const id of pool) assert.ok(r.some((x) => x.id === id), `${yosh} ${id}`);
    for (let i = 1; i < r.length; i++) assert.notEqual(r[i].id, r[i - 1].id);
    for (const q of r) {
      assert.ok(q.kartalar.includes(q.id));
      assert.equal(new Set(q.kartalar).size, q.kartalar.length);
      for (const k of q.kartalar) if (k !== q.id) assert.ok(!juftmi(k, q.id), `${q.id}/${k}`);
    }
  }
  assert.equal(yulduzHisob(9, 10), 3);
  assert.equal(yulduzHisob(5, 10), 1);
  assert.equal(cheksizVaqt(0, 'orta'), 11);
  assert.equal(cheksizVaqt(300, 'orta'), 4);
});

test('REV141: takrorlash — to‘g‘ri bo‘lsa keyinroq, xato bo‘lsa ertaga', () => {
  assert.deepEqual(kuchYangila(undefined, true, 100), { k: 1, due: 102 });
  assert.deepEqual(kuchYangila({ k: 3, due: 0 }, false, 100), { k: 1, due: 101 });
  const st = mem();
  organdi('en', 'kick', st); organdi('en', 'run', st);
  kuchYoz('en', 'kick', false, st, 100);
  assert.deepEqual(bugungiTakror(tilNatija('en', st), 101), ['kick']);
  cheksizYoz('en', 7, st); cheksizYoz('en', 3, st);
  assert.equal(tilNatija('en', st).cheksiz, 7);
});

test('REV141: barmoq harakatlari tanib olinadi', () => {
  const o = { w: 400, h: 300 };
  const bos = imoTanish({ tur: 'bos' }, o); bos.down(100, 100, 0); assert.equal(bos.up(102, 101, 120).tayyor, true);
  const surib = imoTanish({ tur: 'bos' }, o); surib.down(100, 100, 0); assert.equal(surib.up(200, 100, 120).tayyor, false);   // surish — bosish emas
  const ikki = imoTanish({ tur: 'ikki' }, o);
  ikki.down(1, 1, 0); ikki.up(1, 1, 50); ikki.down(1, 1, 200); assert.equal(ikki.up(1, 1, 260).tayyor, true);
  const sekin = imoTanish({ tur: 'ikki' }, o);
  sekin.down(1, 1, 0); sekin.up(1, 1, 50); sekin.down(1, 1, 1500); assert.equal(sekin.up(1, 1, 1560).tayyor, false);
  const up = imoTanish({ tur: 'sur', yon: 'up' }, o); up.down(200, 250, 0); up.move(200, 200, 10); assert.equal(up.move(200, 160, 20).tayyor, true);
  const pastga = imoTanish({ tur: 'sur', yon: 'up' }, o); pastga.down(200, 100, 0); assert.equal(pastga.move(200, 260, 20).tayyor, false);
  const tez = imoTanish({ tur: 'tez', n: 7 }, o);
  let r; for (let i = 0; i < 7; i++) { tez.down(5, 5, i * 200); r = tez.up(5, 5, i * 200 + 50); } assert.equal(r.tayyor, true);
  const ushla = imoTanish({ tur: 'ushla', ms: 1000 }, o); ushla.down(5, 5, 0);
  for (let t = 0; t <= 1100; t += 50) r = ushla.tick(t); assert.equal(r.tayyor, true);
  const qisqa = imoTanish({ tur: 'ushla', ms: 1000 }, o); qisqa.down(5, 5, 0); for (let t = 0; t <= 300; t += 50) qisqa.tick(t); qisqa.up(5, 5, 300);
  for (let t = 300; t <= 1500; t += 50) r = qisqa.tick(t); assert.equal(r.tayyor, false);
  const ayl = imoTanish({ tur: 'aylantir', deg: 180 }, o);
  ayl.down(300, 150, 0); for (let a = 0; a <= 200; a += 10) r = ayl.move(200 + 100 * Math.cos(a * Math.PI / 180), 150 + 100 * Math.sin(a * Math.PI / 180), a);
  assert.equal(r.tayyor, true);
  const ish = imoTanish({ tur: 'ishqala', n: 4 }, o); ish.down(200, 150, 0);
  for (const x of [240, 200, 160, 200, 240, 200, 160, 200, 240]) r = ish.move(x, 150, 1); assert.equal(r.tayyor, true);
  const olib = imoTanish({ tur: 'olib' }, o, { boshi: { x: 0.25, y: 0.6, r: 0.2 }, nishon: { x: 0.72, y: 0.5, r: 0.13 } });
  olib.down(100, 180, 0); r = olib.move(288, 150, 5); assert.equal(r.tayyor, true);
  const chetdan = imoTanish({ tur: 'olib' }, o); chetdan.down(380, 20, 0); assert.equal(chetdan.move(288, 150, 5).tayyor, false);   // narsani ushlamasdan emas
});

test('REV141: o‘yin xonalari bosh sahifasi — avval harakat yo‘li, xonalar yo‘l bosqichlari', () => {
  const tx = fs.readFileSync(new URL('./kid/xonalar/TilXonalari.jsx', import.meta.url), 'utf8');
  assert.ok(/<HarakatYoli /.test(tx) && /onXona=\{xonagaKir\}/.test(tx));
  for (const f of ['HarakatYoli.jsx', 'HarakatSahna.jsx', 'sahnalar.jsx', 'harakat.css']) assert.ok(fs.existsSync(new URL(`./kid/harakat/${f}`, import.meta.url)), f);
});

test('REV142: kuniga 2–3 ta yangi bosqich; ertaga keyingisi ochiladi; admin cheklovsiz', async () => {
  const { kunlikLimit, kunBelgila, bugunBajarilgan } = await import('./kid/harakat/harakatRules.js');
  assert.equal(kunlikLimit('kichik'), 2);
  assert.equal(kunlikLimit('orta'), 3);
  const st = mem();
  const D = 500;
  kunBelgila('en', () => 0, st, D);                    // yangi bola: kun belgilari boshlanadi
  for (const x of ['open', 'close', 'lighton', 'lightoff']) organdi('en', x, st);
  kunBelgila('en', () => 0, st, D);
  yulduzYoz('en', 'oyna:uy', 2, st);
  kunBelgila('en', () => 0, st, D);
  let p = tilNatija('en', st);
  assert.equal(bugunBajarilgan(p, () => 0, D), 2);
  let h = yolHolati(p, () => 0, { limit: 2, bugun: D });
  assert.equal(h.find((x) => x.holat !== 'tugadi').holat, 'ertaga');   // kichik: 2 ta — bugunga yetadi
  assert.ok(!h.some((x) => x.holat === 'ochiq'));
  h = yolHolati(p, () => 0, { limit: 3, bugun: D });
  assert.equal(h.find((x) => x.holat === 'ochiq').id, 'xona:bolalar');   // orta: yana bittasi mumkin
  h = yolHolati(p, () => 0, { limit: 2, bugun: D + 1 });
  assert.equal(h.find((x) => x.holat === 'ochiq').id, 'xona:bolalar');   // ertasi kuni ochiladi
  h = yolHolati(p, () => 0, { limit: 2, bugun: D, cheklovsiz: true });
  assert.ok(!h.some((x) => x.holat === 'ertaga' || x.holat === 'qulf'));   // admin hammasini ochiq ko'radi
  // eski natija (kun belgisisiz) bugungi limitni yemaydi
  const st2 = mem();
  for (const x of ['open', 'close', 'lighton', 'lightoff']) organdi('en', x, st2);
  yulduzYoz('en', 'oyna:uy', 3, st2);
  kunBelgila('en', () => 0, st2, D);
  assert.equal(bugunBajarilgan(tilNatija('en', st2), () => 0, D), 0);
  // yo'ldan tashqarida (ro'yxatdan) o'ynalgan xona ham limitni yemaydi
  const st3 = mem(); kunBelgila('en', () => 0, st3, D);
  kunBelgila('en', (x) => (x === 'havo' ? 3 : 0), st3, D);
  assert.equal(bugunBajarilgan(tilNatija('en', st3), (x) => (x === 'havo' ? 3 : 0), D), 0);
});
