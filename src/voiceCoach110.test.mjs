import test from 'node:test';
import assert from 'node:assert/strict';
import { VOICE_LIMITS, voiceCoach, voiceGiveUp } from './lesson/voiceCheckRules.js';
import { recorderSupported } from './speech/childRecorder.js';

const item = { lang: 'en', phrase: 'Thank you' };

test('bog‘cha: ko‘proq gapiradi; REV145 — 3 emas, 2 marta urinadi', () => {
  assert.equal(VOICE_LIMITS.bogcha.tries, 2);
  assert.ok(VOICE_LIMITS.bogcha.count >= 5);
});

test('xato: avval bolaning o‘z ovozi, keyin to‘g‘risi', () => {
  const c = voiceCoach(item, true, { heard: 'sank you', stars: 1, hasClip: true });
  assert.match(c.before, /Sen shunday aytding/);
  assert.match(c.after, /Men esa shunday aytaman: \[en\]Thank you\[\/en\]/);
  assert.match(c.after, /Yana bir bor ayt/);
});

test('ovoz eshitilmasa — yozuv qo‘yilmaydi, balandroq aytishga undaydi', () => {
  const c = voiceCoach(item, true, { heard: '', stars: 0, hasClip: false });
  assert.equal(c.before, '');
  assert.match(c.after, /Balandroq/);
});

test('oxirida ham maqtaydi', () => {
  assert.match(voiceGiveUp(item, true), /zo‘r harakat/);
});

test('yozish qurilmada o‘chirilgan bo‘lsa — ishlatilmaydi', () => {
  const win = { MediaRecorder: function () {}, navigator: { mediaDevices: { getUserMedia() {} } }, localStorage: { getItem: () => '1' } };
  assert.equal(recorderSupported(win), false);
  assert.equal(recorderSupported({}), false);
  assert.equal(recorderSupported({ ...win, localStorage: { getItem: () => null } }), true);
});
