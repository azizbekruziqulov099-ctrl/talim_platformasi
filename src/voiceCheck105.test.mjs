import test from 'node:test';
import assert from 'node:assert/strict';
import { gradeVoice, voiceCheckItems, voicePassed, voicePrompt, voiceSummary } from './lesson/voiceCheckRules.js';

test('til darsi: chet tilidagi qisqa iboralar olinadi, «repeat after me» olinmaydi', () => {
  const lesson = { steps: [
    { turi: 'qoida', ovoz: 'Bu yashil: [en]Green[/en]. [en]Repeat after me[/en]', doska: '🟢 Green — yashil' },
    { turi: 'tushuntirish', ovoz: '[en]Red[/en] — qizil. [en]Green[/en]', doska: '' },
    { turi: 'tushuntirish', ovoz: '[en]I like apples very much indeed today[/en]', doska: '' },
  ] };
  const items = voiceCheckItems(lesson, 'bogcha');
  assert.deepEqual(items, [{ lang: 'en', phrase: 'Green' }, { lang: 'en', phrase: 'Red' }]);
});

test('REV145: boshqa fan (til darsi emas) — mikrofon bilan tekshiruv yo‘q', () => {
  const lesson = { steps: [
    { turi: 'kirish', doska: 'Bugun kasrlarni o‘rganamiz' },
    { turi: 'qoida', doska: '$\\frac{a}{b}$ kasr\nKasrning maxraji nolga teng bo‘lmaydi\nSurat — yuqoridagi son' },
  ] };
  assert.deepEqual(voiceCheckItems(lesson, 'oquvchi'), []);
  assert.deepEqual(voiceCheckItems({ steps: [{ turi: 'qoida', ovoz: '[ru]Красный[/ru]', doska: 'Qizil' }] }, 'bogcha', { tilYoq: true }), []);
});

test('darsda berilgan ro‘yxat ustun turadi', () => {
  const items = voiceCheckItems({ ovozli_tekshiruv: ['Uchburchakning uchta tomoni bor', { matn: 'Cat', til: 'en' }], steps: [] }, 'talaba');
  assert.deepEqual(items, [{ lang: 'uz', phrase: 'Uchburchakning uchta tomoni bor' }, { lang: 'en', phrase: 'Cat' }]);
});

test('baholash: tutuq belgisi farqi xato emas', () => {
  const g = gradeVoice(['kasrning maxraji nolga teng bolmaydi'], { lang: 'uz', phrase: 'Kasrning maxraji nolga teng bo‘lmaydi' });
  assert.ok(voicePassed(g));
  assert.equal(voicePassed(gradeVoice([], { lang: 'en', phrase: 'Green' })), false);
});

test('ustoz gapi va yakun', () => {
  assert.equal(voicePrompt({ lang: 'en', phrase: 'Green' }, true), 'Endi sen ayt: [en]Green[/en]');
  assert.match(voicePrompt({ lang: 'uz', phrase: 'Salom' }, false, 1), /^Yana bir bor/);
  assert.deepEqual(voiceSummary([{ ok: true }, { ok: false }, { ok: true }]), { togri: 2, jami: 3 });
});
