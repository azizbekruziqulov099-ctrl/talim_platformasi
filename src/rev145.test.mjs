import test from 'node:test';
import assert from 'node:assert/strict';
import { aytdiMi, aytiladiganSozlar, pauzasiz, sozBolaklari, tingla } from './lesson/sozAytish.js';
import { kidRepeatSpeech, ismOldin } from './lesson/kidLessonRules.js';
import { QURILMA_OVOZI, aralashKerak } from './speech/aralashOvoz.js';
import { gap } from './kid/izohTil.js';
import fs from 'node:fs';

test('REV145: o‘rgatilgan so‘z gap bo‘laklaridan topiladi — buyruq iboralar emas, bir so‘z bir marta', () => {
  const sp = 'Bu qizil: [en]Red[/en]. [en]Red[/en]! Endi sen ayt! ⏸ [en]Say it with me[/en] ⏸ Yana: [en]Red[/en]! ⏸ [en]Green[/en]! ⏸ Barakalla!';
  const b = sozBolaklari(sp, 'en');
  assert.deepEqual(b.map((x) => x.soz?.phrase || null), ['Red', null, null, 'Green', null]);
  assert.equal(b.at(-1).matn, 'Barakalla!');
  assert.deepEqual(aytiladiganSozlar(sp, 'en').map((x) => x.phrase), ['Red', 'Green']);
  assert.deepEqual(aytiladiganSozlar(sp, ''), []);
  assert.deepEqual(aytiladiganSozlar('[en]Red[/en] — qizil.', 'en'), []);   // pauza yo'q — so'ralmaydi
  assert.equal(pauzasiz('A ⏸ B ⏸'), 'A B');
});

test('REV145: haqiqiy dars gapi (kidRepeatSpeech/ismOldin) — har so‘z alohida so‘raladi, ko‘pi bilan 3', () => {
  const sp = ismOldin(kidRepeatSpeech('Ranglar: [en]Red[/en], [en]Blue[/en], [en]Green[/en], [en]Pink[/en]. Qani, birga aytamiz!', { doska: '' }));
  const sozlar = aytiladiganSozlar(sp, 'en').map((x) => x.phrase);
  assert.deepEqual(sozlar, ['Red', 'Blue', 'Green'], sp);
  assert.ok(sozlar.every((w) => ['Red', 'Blue', 'Green', 'Pink'].includes(w)));
});

test('REV145: 2 urinish — birinchisida aniq, ikkinchisida «yaqin» ham qabul', () => {
  const item = { lang: 'en', phrase: 'Green' };
  assert.equal(aytdiMi(['green'], item, 0).ok, true);
  assert.equal(aytdiMi([], item, 0).ok, false);
  assert.equal(aytdiMi([], item, 1).ok, false);
});

test('REV145: mikrofon bo‘lmasa tingla() darhol «yoq» qaytaradi, stop() — toxtatildi', async () => {
  const r = await tingla('en').promise;
  assert.equal(r.xato, 'yoq');
  class Fake { start() {} abort() {} }
  globalThis.SpeechRecognition = Fake;
  try {
    const t = tingla('en', { kutish: 5000 });
    t.stop();
    assert.deepEqual(await t.promise, { alts: [], toxtatildi: true });
    const t2 = tingla('en', { kutish: 10 });
    assert.deepEqual(await t2.promise, { alts: [] });
  } finally { delete globalThis.SpeechRecognition; }
});

test('REV145: ovozlar — hammasi serverdan (tabiiy), Kabu bitta ovozda, Sardor — erkak', () => {
  assert.equal(QURILMA_OVOZI, false);
  assert.equal(aralashKerak('Bu [en]Red[/en]'), false);
  const src = fs.readFileSync(new URL('./lesson/DarsXonasi.jsx', import.meta.url), 'utf8');
  assert.match(src, /ustozRef\.current === "sardor" \? "ogil" : "qiz"/);
  assert.match(src, /if \(kid && !darsTil\) return \[\];/);
});

test('REV145: yangi gaplar uz/ru/en', () => {
  for (const l of ['ru', 'en']) assert.doesNotMatch(gap(l, 'Yaxshi harakat! Mana bunday: {p}', { p: 'X' }), /Mana bunday/);
});

test('REV145: ota-ona hisoboti — baho, kun xulosasi va maslahat', async () => {
  const { bahoInfo, kunXulosa, maslahat } = await import('./parent/farzandVaqtRules.js');
  assert.equal(bahoInfo({ tugadi: '10:00', togri: 4, jami: 5 }).matn, 'A’lo');
  assert.equal(bahoInfo({ tugadi: '10:00', togri: 1, jami: 4, baho: 'mashq' }).matn, 'Mashq kerak');
  assert.equal(bahoInfo({ tugadi: null }).matn, 'Tugallanmagan');
  assert.equal(bahoInfo({ tugadi: '10:00', jami: 0 }).matn, 'Tugatdi');
  const x = kunXulosa([{ tugadi: 'a', togri: 3, jami: 4, daqiqa: 5, sozlar: [{ soz: 'apple', aytdi: true }, { soz: 'Banana', aytdi: false }] },
    { tugadi: null, togri: null, jami: null, daqiqa: 2, sozlar: [{ soz: 'banana', aytdi: true }] }], null);
  assert.deepEqual([x.darslar, x.tugadi, x.foiz, x.sozJami, x.sozAytdi, x.daqiqa], [2, 1, 75, 2, 2, 7]);
  assert.deepEqual(maslahat({ tugadi: 'a', sozlar: [{ soz: 'juice', aytdi: false }] }), { matn: 'Uyda shu so‘zlarni birga ayting:', sozlar: ['juice'] });
  assert.equal(maslahat({ tugadi: 'a', togri: 4, jami: 4, sozlar: [] }), null);
  assert.match(maslahat({ tugadi: null }).matn, /yarim qoldi/);
});

test('REV145: dars natijasi so‘zlari serverga xavfsiz paketda', async () => {
  const { sozlarPaketi } = await import('./kid/kidActivity.js');
  const p = sozlarPaketi([{ soz: ' apple ', emoji: '🍎', aytdi: true }, { soz: '' }, { soz: 'x'.repeat(90), aytdi: 'ha' }, ...Array.from({ length: 20 }, (_, i) => ({ soz: `w${i}` }))]);
  assert.equal(p.length, 12);
  assert.deepEqual(p[0], { soz: 'apple', emoji: '🍎', aytdi: true });
  assert.equal(p[1].soz.length, 60);
  assert.equal(p[1].aytdi, null);
});
