import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { quyoshVaqti, quyoshHolati, shaharKoord } from './kid/ustozRules.js';
import { ismOldin, kidRepeatSpeech } from './lesson/kidLessonRules.js';
import { matnRasmlari } from './kid/kidStageRules.js';
import { ustozNutqi } from './kid/ustozNutqi.js';
import { brauzerMatni, reja } from './speech/aralashOvoz.js';
import { ochilish } from './kid/darsOchilishi.js';

const T = (s) => new Date(s);

test('REV140: kun vaqti quyosh bo‘yicha — 16:40 da kunduz, qorong‘ida tun (soat mintaqasiga bog‘liq emas)', () => {
  assert.equal(quyoshVaqti(T('2026-10-13T16:40:00+05:00'), shaharKoord('toshkent')), 'kun');
  assert.equal(quyoshVaqti(T('2026-10-13T11:40:00Z'), shaharKoord('toshkent')), 'kun');   // xuddi o'sha lahza UTC da
  assert.equal(quyoshVaqti(T('2026-10-13T17:25:00+05:00'), shaharKoord('toshkent')), 'kech');
  assert.equal(quyoshVaqti(T('2026-10-13T21:00:00+05:00'), shaharKoord('toshkent')), 'tun');
  assert.equal(quyoshVaqti(T('2026-10-13T07:00:00+05:00'), shaharKoord('toshkent')), 'tong');
  assert.equal(quyoshVaqti(T('2026-06-21T20:15:00+05:00'), shaharKoord('toshkent')), 'kech');   // yozda kech yorug'
  assert.equal(quyoshVaqti(T('2026-12-21T17:45:00+05:00'), shaharKoord('toshkent')), 'tun');    // qishda erta qorong'i
  // tush payti quyosh balandligi: 90 − kenglik + og'ish (13-oktyabr ≈ −8°)
  const tush = quyoshHolati(T('2026-10-13T12:00:00+05:00'), 41.31, 69.28).balandlik;
  assert.ok(tush > 39 && tush < 42, String(tush));
  assert.deepEqual(shaharKoord('Samarqand'), [39.65, 66.96]);
  assert.deepEqual(shaharKoord('noma’lum'), shaharKoord('toshkent'));
});

test('REV140: «Endi sen ayt» — ustoz avval so‘zni o‘zi aytadi va takrorlaydi, keyin bolaga jimlik', () => {
  assert.equal(ismOldin('Bugun quyosh! Endi sen ayt: [en]Sunny[/en] ⏸'), 'Bugun quyosh! [en]Sunny.[/en] [en]Sunny![/en] Endi sen ayt! ⏸');
  // so'z buyruqdan oldin aytilgan bo'lsa — yana bir marta (jami ikki)
  assert.equal(ismOldin('[en]Hello![/en] Endi sen ayt: [en]Hello![/en] ⏸'), '[en]Hello![/en] [en]Hello![/en] Endi sen ayt! ⏸');
  // izoh rus tilida
  assert.equal(ismOldin('[ru]Теперь ты скажи:[/ru] [en]Cat[/en] ⏸'), '[en]Cat.[/en] [en]Cat![/en] [ru]Теперь ты скажи![/ru] ⏸');
  // o'zbekcha dars (tegsiz)
  assert.equal(ismOldin('Bu qorbobo. Men bilan ayt: qorbobo'), 'Bu qorbobo. Qorbobo! Men bilan ayt! ⏸');
  // buyruqsiz gap o'zgarmaydi
  assert.equal(ismOldin('Bu olma. [en]Apple[/en].'), 'Bu olma. [en]Apple[/en].');
  // o'zbekcha dars, «birga aytamiz» bilan tugasa — doskadagi so'z ikki marta
  assert.equal(kidRepeatSpeech('Bu qorbobo. Qani, birga aytamiz!', { doska: '⛄ qorbobo' }), 'Bu qorbobo. Qani, birga aytamiz! Qorbobo. Qorbobo! ⏸');
});

test('REV140: dars boshidagi takror — «Bu nima?» emas, avval nomini aytadi', () => {
  const st = ochilish({ ustoz: 'nilufar', til: 'en', havo: 'quyosh', grade: '4-5 yosh', oldingi: { mavzu: 'Ranglar', sozlar: [{ say: 'red', emoji: '🔴' }] } });
  const takror = st.find((s) => s._ochilish === 'takror');
  assert.doesNotMatch(takror.ovoz, /Bu nima/);
  assert.match(ismOldin(takror.ovoz), /Bu — \[en\]red\[\/en\]\. \[en\]red!\[\/en\] Birga aytamiz! ⏸/);
  // katta guruh salomlashuvi: «Hello» dan keyin bolaga aytish navbati bor
  assert.match(st[0].ovoz, /Endi sen ayt/);
});

test('REV140: doska bo‘sh qolmaydi — ustoz aytgan so‘zning rasmi', () => {
  const wm = { '🍎|apple': '/m/1', '🍌|banana': '/m/2', '🍎|qizil olma': '/m/9' };
  assert.deepEqual(matnRasmlari('Inglizchada [en]apple[/en]. Endi sen ayt!', wm), ['/m/1']);
  assert.deepEqual(matnRasmlari('Bu qizil olma, bu esa [en]banana[/en]', wm), ['/m/9', '/m/2']);
  assert.deepEqual(matnRasmlari('Pineapple emas', wm), []);
  assert.deepEqual(matnRasmlari('apple', null), []);
});

test('REV140: ustoz nutqida yopiluvchi tegdan keyingi nuqta saqlanadi (gaplar orasida pauza)', () => {
  assert.equal(ustozNutqi('Inglizchada [en]apple[/en]. Endi sen ayt!'), 'Inglizchada [en]apple[/en]. Endi sen ayt!');
  assert.equal(ustozNutqi('[en]Beep-beep! Hello![/en]'), '[en]Hello![/en]');
});

test('REV140: brauzer ovozi emoji nomlarini o‘qimaydi', () => {
  assert.equal(brauzerMatni('Look: 🍎🍌🍇 Apple! ⏸'), 'Look: Apple!');
  const v = [{ lang: 'en-US', name: 'Google US English', localService: false }];
  const r = reja('Qara: [en]🔴🔵 Red, blue![/en] ⏸', { ovozlar: v, qurilma: true });
  assert.deepEqual(r.map((q) => q.tur), ['server', 'brauzer', 'pauza']);
  assert.equal(r[1].matn, 'Red, blue!');
});

test('REV140: deraza — rasmdan olingan shisha niqobi; xonada begona kartochkalar (ramka, pol) chiqmaydi', () => {
  const ust = fs.readFileSync(new URL('./kid/ustozlar.js', import.meta.url), 'utf8');
  for (const x of ['onatili', 'matematika', 'atrofolam']) {
    assert.ok(fs.existsSync(new URL(`./kid/ustoz/xona/osmon_${x}.webp`, import.meta.url)), x);
    assert.ok(ust.includes(`osmon_${x}.webp`), x);
  }
  assert.ok(!/oyna:/.test(ust));
  const sahna = fs.readFileSync(new URL('./kid/UstozSahna.jsx', import.meta.url), 'utf8');
  assert.ok(!/bezak\(|us-frame|us-floor|us-shelf/.test(sahna));
  assert.ok(/maskImage/.test(sahna));
  const dx = fs.readFileSync(new URL('./lesson/DarsXonasi.jsx', import.meta.url), 'utf8');
  assert.ok(/_ochilish === "salom" \|\| step\._ochilish === "havo"\) return \[\]/.test(dx));
  assert.ok(/quyoshVaqti\(new Date\(\)\)/.test(dx) && !/kunVaqti/.test(dx));
});
