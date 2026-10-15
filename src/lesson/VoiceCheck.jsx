import React, { useCallback, useEffect, useRef, useState } from "react";
import { uiText as __kbUi } from "../interface/interfaceRuntime.js";
import { CONTENT_LOCALES } from "../speech/language.js";
import KidStage from "../kid/KidStage.jsx";
import { chime, soft } from "../kid/kidSounds.js";
import { VOICE_LIMITS, gradeVoice, voiceCoach, voiceGiveUp, voicePassed, voicePrompt, voiceSummary } from "./voiceCheckRules.js";
import { disableRecorder, dropClip, playClip, startClip } from "../speech/childRecorder.js";
import { suhbatJavob, tahlil } from "../kid/suhbat.js";
import { gap } from "../kid/izohTil.js";

const PRAISE_KID = ["Barakalla! Juda to‘g‘ri aytding!", "Zo‘r! Ana shunday!", "Ofarin! Sen zo‘rsan!"];
const PRAISE = ["To‘g‘ri! Aniq aytdingiz.", "Barakalla, to‘g‘ri.", "Yaxshi, to‘g‘ri takrorladingiz."];

/**
 * REV105: dars oxiridagi ovozli tekshiruv. Ustoz iborani aytadi, mikrofon o'zi yoqiladi,
 * bola/o'quvchi/talaba takrorlaydi — brauzer tanib, yulduz beradi. Har iboraga 2 urinish.
 * REV110: xato bo'lsa ustoz bolaning O'Z ovozini qayta eshittiradi («Sen shunday aytding…»), keyin to'g'risini aytib,
 * yana urinishga undaydi. Yozuv faqat qurilma xotirasida, serverga yuborilmaydi. REV145: bog'chada ham 2 urinish;
 * natija ro'yxati (qaysi so'zni aytdi) onDone ning ikkinchi argumenti — ota-ona hisobotiga boradi.
 */
export default function VoiceCheck({ items, audience = "oquvchi", say, hush, speaking = false, onDone, bilgan = [], izoh = "uz" }) {
  const kid = audience === "bogcha";
  const tries = (VOICE_LIMITS[audience] || VOICE_LIMITS.oquvchi).tries;
  const [i, setI] = useState(0);
  const [phase, setPhase] = useState("prompt");   // prompt | listen | graded | tap | denied | done
  const [attempt, setAttempt] = useState(0);
  const [last, setLast] = useState(null);         // {stars, heard}
  const [results, setResults] = useState([]);
  const [celebrate, setCelebrate] = useState(0);
  const rec = useRef(null);
  const clipRef = useRef(null);       // REV110: hozirgi yozuv (MediaRecorder)
  const [myClip, setMyClip] = useState(null);   // bolaning oxirgi yozuvi — «🔊 o'zimni eshitaman»
  const myClipRef = useRef(null);
  const alive = useRef(true);
  const resultsRef = useRef([]);
  resultsRef.current = results;
  const item = items[i];

  const stopRec = () => {
    try { rec.current?.abort(); } catch { /* yopilgan */ }
    rec.current = null;
    clipRef.current?.cancel(); clipRef.current = null;
  };
  const keepClip = (url) => { dropClip(myClipRef.current); myClipRef.current = url || null; setMyClip(url || null); };
  useEffect(() => { alive.current = true; return () => { alive.current = false; stopRec(); dropClip(myClipRef.current); }; }, []);

  const finishAll = useCallback((list) => {
    setPhase("done");
    const sum = voiceSummary(list);
    const good = sum.jami && sum.togri / sum.jami >= 0.67;
    say(kid
      ? (izoh !== "uz" ? gap(izoh, good ? "Barakalla! Hammasini aytding!" : "Yaxshi harakat! Keyingi safar yana aytamiz.")
        : good ? __kbUi("Barakalla! Hammasini aytding!") : __kbUi("Yaxshi harakat! Keyingi safar yana aytamiz."))
      : __kbUi(`Ovozli tekshiruv tugadi: ${sum.togri} / ${sum.jami}.`),
      () => setTimeout(() => { if (alive.current) onDone?.(sum, list); }, 500));
  }, [kid, say, onDone]);

  const record = useCallback((ok, heard, stars, g = null) => {
    const list = [...resultsRef.current, { phrase: item.phrase, lang: item.lang, ok, heard, stars }];
    setResults(list);
    const next = () => {
      if (!alive.current) return;
      if (i + 1 >= items.length) { finishAll(list); return; }
      setI(i + 1); setAttempt(0); setLast(null); setPhase("prompt");
    };
    if (ok) {
      setCelebrate((c) => c + 1); chime();
      const list2 = kid ? PRAISE_KID : PRAISE;
      // REV110: suhbatda — maqtab, javobni to'liq namuna bilan qaytaradi («Barakalla! I'm fine, thank you!»)
      const praise = item.turi === "suhbat" ? suhbatJavob(item, g || { stars: 3 }, kid, izoh)
        : izoh !== "uz" ? gap(izoh, list2[i % list2.length]) : __kbUi(list2[i % list2.length]);
      say(praise, () => setTimeout(next, 400));
    } else {
      soft();
      say(voiceGiveUp(item, kid, izoh), () => setTimeout(next, 500));
    }
  }, [i, item, items.length, kid, say, finishAll, izoh]);

  const listen = useCallback(async (noClip = false) => {
    const Recognition = globalThis.SpeechRecognition || globalThis.webkitSpeechRecognition;
    if (!Recognition || !item) { setPhase("denied"); return; }
    hush?.();
    stopRec();
    // REV110: bolaning ovozini ham yozib boramiz (xato bo'lsa o'ziga eshittirish uchun).
    const clip = noClip ? null : await startClip().catch(() => null);
    if (!alive.current) { clip?.cancel(); return; }
    clipRef.current = clip;
    const r = new Recognition();
    rec.current = r;
    r.lang = CONTENT_LOCALES[item.lang] || "uz-UZ";
    r.interimResults = false;
    r.maxAlternatives = 5;
    let handled = false;
    const coach = (g, heard, url) => {
      const c = voiceCoach(item, kid, { attempt: attempt + 1, heard, stars: g.stars, hasClip: Boolean(url), izoh });
      if (item.turi === "suhbat" && g.boshqa) c.after = suhbatJavob(item, g, kid, izoh);
      const again = () => { if (alive.current) setPhase("again"); };
      if (!c.before) { say(c.after, again); return; }
      say(c.before, () => {
        if (!alive.current) return;
        playClip(url).then(() => { if (alive.current) say(c.after, again); });
      });
    };
    const graded = async (alts) => {
      if (handled || !alive.current) return;
      handled = true;
      const url = clipRef.current ? await clipRef.current.stop().catch(() => null) : null;
      clipRef.current = null;
      if (!alive.current) { dropClip(url); return; }
      keepClip(url);
      const g = item.turi === "suhbat" ? tahlil(alts, item, bilgan) : gradeVoice(alts, item);
      const heard = alts[0] || "";
      setLast({ ...g, heard });
      setPhase("graded");
      if (voicePassed(g)) { record(true, heard, g.stars, g); return; }
      if (attempt + 1 < tries) {
        setAttempt(attempt + 1);
        coach(g, heard, url);
        return;
      }
      record(false, heard, g.stars);
    };
    r.onresult = (event) => graded(Array.from(event.results?.[0] || []).map((a) => a.transcript));
    r.onerror = (event) => {
      if (event?.error === "not-allowed" || event?.error === "service-not-allowed") { handled = true; clipRef.current?.cancel(); setPhase("denied"); return; }
      if (event?.error === "audio-capture" && clip) {
        // Mikrofonni bir vaqtda yozish va tanish bo'lmadi — shu qurilmada faqat tanish qoladi.
        handled = true; clipRef.current?.cancel(); clipRef.current = null; disableRecorder();
        setTimeout(() => { if (alive.current) listen(true); }, 150);
        return;
      }
      if (event?.error === "aborted") return;
      graded([]);   // no-speech / network — eshitilmadi
    };
    r.onend = () => { if (!handled && alive.current) graded([]); };
    try { r.start(); setPhase("listen"); } catch { clipRef.current?.cancel(); clipRef.current = null; setPhase("tap"); }
  }, [item, attempt, tries, kid, say, hush, record, izoh, bilgan]);

  // Har ibora: ustoz aytadi → mikrofon o'zi yoqiladi.
  useEffect(() => {
    if (!item || phase !== "prompt") return;
    say(item.ask ? item.ask : voicePrompt(item, kid, 0, izoh), () => { if (alive.current) listen(); });
  }, [i, phase]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (phase === "again") listen(); }, [phase]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { keepClip(null); }, [i]); // eslint-disable-line react-hooks/exhaustive-deps

  const hearMe = () => { if (myClip && !speaking && phase !== "listen") { hush?.(); playClip(myClip); } };

  const skip = () => { stopRec(); hush?.(); record(false, "", 0); };
  const stopAll = () => {
    stopRec(); hush?.();
    const list = [...resultsRef.current];
    onDone?.(voiceSummary(list), list);
  };

  if (!item && phase !== "done") return null;
  const mood = phase === "listen" ? "think" : speaking ? "talk" : last && voicePassed(last) ? "happy" : "wave";
  const listening = phase === "listen";

  return <div className={`dx-voice ${kid ? "is-kid" : ""}`} aria-live="polite">
    {kid
      ? <div className="dx-voice-kid"><KidStage compact mood={mood} celebrate={celebrate} speaking={speaking} /></div>
      : <h3 className="dx-title">{__kbUi("Ovozli tekshiruv")} · {Math.min(i + 1, items.length)} / {items.length}</h3>}

    {kid && item?.emoji && phase !== "done" && <div className="dx-voice-emoji" aria-hidden="true">{item.emoji}</div>}
    {!kid && item && phase !== "done" && <div className="dx-voice-phrase">
      <small>{__kbUi("Takrorlang:")}</small>
      <b lang={item.lang}>{item.phrase}</b>
    </div>}

    <div className="dx-voice-dots" aria-label={__kbUi(`${results.filter((r) => r.ok).length} ta to‘g‘ri`)}>
      {items.map((it, k) => <span key={k} className={k < results.length ? (results[k].ok ? "is-ok" : "is-no") : k === i ? "is-now" : ""}>{k < results.length ? (results[k].ok ? "⭐" : "•") : "🎤"}</span>)}
    </div>

    {phase !== "done" && <button type="button" className={`dx-voice-mic ${listening ? "is-on" : ""}`}
      onClick={() => listen()} disabled={listening || speaking} aria-label={__kbUi(listening ? "Eshityapman" : "Mikrofonni yoqish")}>
      <span aria-hidden="true">{listening ? "👂" : "🎤"}</span>
      {!kid && <b>{__kbUi(listening ? "Eshityapman… ayting" : speaking ? "Tinglang…" : "Mikrofonni bosib ayting")}</b>}
    </button>}

    {phase === "denied" && <p className="dx-voice-note">{__kbUi("Mikrofonga ruxsat bering: brauzer tepasidagi 🎤 belgisini bosing va «Ruxsat»ni tanlang, keyin mikrofon tugmasini bosing.")}</p>}
    {phase === "tap" && <p className="dx-voice-note">{__kbUi("Mikrofon tugmasini bosing.")}</p>}

    {last && !kid && phase !== "listen" && <p className={`dx-voice-heard is-${last.stars}`}>
      <span aria-label={`${last.stars} / 3`}>{"⭐".repeat(last.stars)}{"☆".repeat(3 - last.stars)}</span>
      {last.heard ? <> {__kbUi("Eshitildi:")} «{last.heard}»</> : <> {__kbUi("Ovoz eshitilmadi — balandroq va aniqroq ayting.")}</>}
    </p>}
    {last && kid && phase !== "listen" && <p className="dx-voice-stars" aria-label={`${last.stars} / 3`}>{"⭐".repeat(Math.max(0, last.stars))}</p>}

    {phase !== "done" && <div className="dx-row dx-voice-actions">
      <button type="button" className="dx-btn" onClick={() => { stopRec(); say(item.ask && !attempt ? item.ask : voicePrompt(item, kid, attempt, izoh)); }} disabled={listening}>
        {kid ? "🔁" : __kbUi("↻ Yana eshitish")}
      </button>
      {myClip && <button type="button" className="dx-btn" onClick={hearMe} disabled={listening || speaking} aria-label={__kbUi("O‘z ovozimni eshitish")}>
        {kid ? "🔊" : __kbUi("🔊 O‘z ovozimni eshitish")}
      </button>}
      <button type="button" className="dx-btn" onClick={skip}>{kid ? "⏭️" : __kbUi("O‘tkazib yuborish")}</button>
      {!kid && <button type="button" className="dx-btn" onClick={stopAll}>{__kbUi("Tekshiruvni tugatish")}</button>}
    </div>}
  </div>;
}
