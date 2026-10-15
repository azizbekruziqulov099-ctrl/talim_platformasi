import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import HarakatSahna from "./HarakatSahna.jsx";
import { SahnaRasm } from "./sahnalar.jsx";
import { BOLIMLAR, HARAKATLAR } from "./harakatLugat.js";
import {
  harakat, bolimHarakatlari, buyruq, manosi, izohGap, izohMatn, imoKalit, teg, yoshGuruhi, raundlar, yulduzHisob,
  yolHolati, takrorHarakatlari, organilgan, bugungiTakror, cheksizVaqt, tilNatija, organdi, yulduzYoz, kuchYoz, cheksizYoz, kunBelgila, kunlikLimit, bugunBajarilgan, kunRaqami,
} from "./harakatRules.js";
import { gap as xonaGap } from "../xonalar/xonaRules.js";
import { XONALAR } from "../xonalar/xonaLugat.js";
import { HR } from "./rasmlar.js";
import { eslab } from "../sozBoyligi.js";
import { uiText as T } from "../../interface/interfaceRuntime.js";
import "./harakat.css";

/** REV144: o'yin telefonda butun ekranni egallaydi — sahifa sarlavhasi va menyular ustidan (body ichida) chiziladi. */
const ekranda = (el) => (globalThis.document?.body ? createPortal(el, globalThis.document.body) : el);
const TUGUN_BELGI = { organ: "📖", oyna: "🎮", xona: "🏠", takror: "🔁", cheksiz: "♾️" };
// REV144: rassom chizgan belgilar (emoji — zaxira)
const BELGI_RASM = { organ: "belgi_organ", oyna: "belgi_oyna", xona: "belgi_xona", takror: "belgi_takror", cheksiz: "belgi_cheksiz", qulf: "belgi_qulf" };
const Belgi = ({ k, emoji }) => (HR[BELGI_RASM[k]] ? <img className="hy-belgi" src={HR[BELGI_RASM[k]].src} alt="" draggable="false" /> : <>{emoji}</>);
const TUGUN_NOM = { organ: "O‘rgan", oyna: "O‘yna", xona: "So‘zlar xonasi", takror: "Takror", cheksiz: "Cheksiz o‘yin" };

/**
 * REV141: «Harakat o'yinlari» — bosqichma-bosqich yo'l. Har bo'limda avval 4 ta harakat o'rgatiladi (ustoz ko'rsatadi,
 * bola o'zi bajaradi), keyin o'yin (ustoz faqat o'rganilayotgan tilda buyuradi — bola tushunib bajaradi), keyin narsalar
 * nomini o'rganadigan xona. Bo'limlar orasida aralash takror, oxirida hech qachon tugamaydigan, tobora tezlashadigan o'yin.
 * Tushuntirishlar — kursning izoh tilida (o'zbek, rus yoki ingliz).
 */
export default function HarakatYoli({ til = "en", izoh = "uz", grade = "", ayt, jim, gapiryapti = false, xonaYulduz = () => 0, onXona, ochiq = true, cheklovsiz = false }) {
  const yosh = yoshGuruhi(grade);
  const toliq = yosh !== "kichik";
  const [p, setP] = useState(() => tilNatija(til));
  const [ish, setIsh] = useState(null);       // hozirgi bosqich: {tur, tugunId, ...}
  const [natijaK, setNatijaK] = useState(null);
  const ishRef = useRef(null);
  ishRef.current = ish;
  const yolRef = useRef(null);
  const tinchTimer = useRef(0);
  useEffect(() => { setP(tilNatija(til)); setIsh(null); }, [til]);
  useEffect(() => () => clearTimeout(tinchTimer.current), []);

  // kunlik tartib: har kuni 2–3 ta yangi bosqich ochiladi (admin — cheklovsiz). Kun yarim tunda o'zi almashadi.
  const [kun, setKun] = useState(() => kunRaqami());
  useEffect(() => { const t = setInterval(() => setKun(kunRaqami()), 60000); return () => clearInterval(t); }, []);
  const limit = kunlikLimit(yosh);
  useEffect(() => { const yangi = kunBelgila(til, xonaYulduz, undefined, kun); if (yangi) setP(yangi); }, [p, til, xonaYulduz, kun]);
  const tugunlar = useMemo(() => yolHolati(p, xonaYulduz, { limit, bugun: kun, cheklovsiz }), [p, xonaYulduz, limit, kun, cheklovsiz]);
  const bugunN = useMemo(() => Math.min(limit, bugunBajarilgan(p, xonaYulduz, kun)), [p, xonaYulduz, kun, limit]);
  const ertaga = tugunlar.some((t) => t.holat === "ertaga");
  const navbatdagi = tugunlar.find((t) => t.holat === "ochiq");
  const bugun = useMemo(() => bugungiTakror(p), [p]);
  // bosqichga kirganda (yoki yangi bosqich) — sahna to'liq ko'rinsin: ekran tepasiga suriladi (sarlavha ostida qolmaydi)
  const ishBor = Boolean(ish);
  const ishTur = ish?.tur;
  // o'yin ochiq paytda orqadagi sahifa aylanmasin (telefonda barmoq sahnani emas, sahifani surib yubormasin)
  useEffect(() => {
    if (!ishBor || !globalThis.document?.body) return undefined;
    const b = globalThis.document.body, eski = b.style.overflow;
    b.style.overflow = "hidden";
    return () => { b.style.overflow = eski; };
  }, [ishBor]);
  useEffect(() => {
    if (!ishBor) return;
    const el = globalThis.document?.querySelector(".hy-ish");
    try { el?.scrollIntoView({ block: "start", behavior: "smooth" }); } catch { /* eski brauzer */ }
  }, [ishBor, ishTur]);
  useEffect(() => {
    if (ish) return;
    const el = yolRef.current?.querySelector(".hy-tugun.is-ochiq, .hy-tugun.is-ertaga");
    try { el?.scrollIntoView({ block: "center", behavior: "smooth" }); } catch { /* eski brauzer */ }
  }, [ish, navbatdagi?.id]);

  const say = useCallback((text, done) => ayt?.(text, done, "teacher"), [ayt]);
  const ustozMatn = (id) => {
    const s = buyruq(id, til, false), m = manosi(id, izoh, false);
    return izoh === til ? teg(s, til) : izohGap("manosi", izoh, { t: s, til, i: m });
  };
  const maqtov = () => teg(xonaGap("barakalla", til), til);

  // ─────────── o'rganish ───────────
  const organBoshla = (bolim, tugunId) => {
    jim?.();
    const list = bolimHarakatlari(bolim).map((h) => h.id);
    setNatijaK(null);
    setIsh({ tur: "organ", tugunId, bolim, list, i: 0, faza: "demo", yordam: false });
    say(`${izohGap("organIntro", izoh)}`, () => organQadam(list, 0));   // eslint-disable-line no-use-before-define
  };
  const organQadam = (list, i) => {
    const id = list[i];
    setIsh((o) => (o?.tur === "organ" ? { ...o, i, faza: "demo", yordam: false, k: Date.now() } : o));
    say(`${ustozMatn(id)} ${izohGap("qara", izoh)}`);
  };
  const demoTugadi = () => {
    const o = ishRef.current;
    if (!o || o.tur !== "organ") return;
    const id = o.list[o.i];
    setIsh({ ...o, faza: "sen", yordam: false, k: Date.now() });
    const s = buyruq(id, til, false);
    say(`${teg(s, til)} ${teg(s, til)} ${izohGap("sen", izoh)} ${izohGap(imoKalit(harakat(id).imo), izoh)}`);
    kutishTimer();   // eslint-disable-line no-use-before-define
  };
  const organBajarildi = () => {
    const o = ishRef.current;
    if (!o || o.tur !== "organ") return;
    clearTimeout(tinchTimer.current);
    const id = o.list[o.i];
    setP(organdi(til, id));
    try { eslab({ sozlar: [{ say: buyruq(id, til, false), emoji: BOLIMLAR.find((b) => b.id === o.bolim)?.emoji || "⭐", til }] }); } catch { /* */ }
    const keyingi = o.i + 1;
    say(`${izohGap("barakalla", izoh)} ${teg(buyruq(id, til, toliq), til)}`, () => {
      if (ishRef.current?.k !== o.k) return;
      if (keyingi < o.list.length) organQadam(o.list, keyingi);
      else { setIsh(null); setNatijaK({ tur: "organ", tugunId: o.tugunId, bolim: o.bolim }); say(izohGap("bolimTugadi", izoh)); }
    });
  };
  const kutishTimer = () => {
    clearTimeout(tinchTimer.current);
    tinchTimer.current = setTimeout(() => {
      const o = ishRef.current;
      if (!o || !(o.faza === "sen" || o.faza === "bajar")) return;
      setIsh({ ...o, yordam: true });
      const id = o.tur === "organ" ? o.list[o.i] : o.raund?.[o.i]?.id;
      if (id) say(`${izohGap(imoKalit(harakat(id).imo), izoh)} ${teg(buyruq(id, til, o.tur !== "organ" && toliq), til)}`);
    }, 7000);
  };

  // ─────────── o'yin (o'yna / takror / bugungi takror / cheksiz) ───────────
  const oyinBoshla = (tur, tugunId, pool) => {
    jim?.();
    setNatijaK(null);
    const hamma = organilgan(p).length >= 4 ? organilgan(p) : pool;
    const cheksiz = tur === "cheksiz";
    const r = raundlar(pool, { yosh, kuch: p.kuch, hamma, n: cheksiz ? 30 : null });
    if (!r.length) return;
    const o = { tur, tugunId, pool, hamma, raund: r, i: 0, faza: "tanla", xato: 0, togri: 0, jon: 3, ball: 0, yordam: false, k: Date.now() };
    setIsh(o);
    const intro = tur === "cheksiz" ? "cheksizIntro" : tur === "oyna" ? "oynaIntro" : "takrorIntro";
    say(`${izohGap(intro, izoh)}${yosh !== "katta" ? ` ${izohGap("tanla", izoh)}` : ""}`, () => raundBer(o));   // eslint-disable-line no-use-before-define
  };
  const raundBer = (o) => {
    const q = o.raund[o.i];
    const n = { ...o, faza: "tanla", xato: 0, yordam: false, k: Date.now(), boshi: Date.now() };
    setIsh(n);
    say(teg(buyruq(q.id, til, toliq), til));
  };
  const kartaTanlandi = (id) => {
    const o = ishRef.current;
    if (!o || o.faza !== "tanla") return;
    const q = o.raund[o.i];
    jim?.();
    if (id === q.id) {
      setIsh({ ...o, faza: "bajar", tanlandi: id, yordam: false, k: Date.now() });
      say(teg(buyruq(q.id, til, toliq), til));
      kutishTimer();
      return;
    }
    const n = { ...o, xato: o.xato + 1, notogri: id, nk: Date.now() };
    if (o.tur === "cheksiz") { cheksizXato(n); return; }   // eslint-disable-line no-use-before-define
    setIsh({ ...n, korsat: n.xato >= 2 ? q.id : null });
    const t = buyruq(q.id, til, toliq);
    say(n.xato >= 2 ? `${teg(t, til)} ${izohGap("tanla", izoh)}` : izohGap("emas", izoh, { t, til, i: manosi(q.id, izoh, toliq) }));
  };
  const oyinBajarildi = () => {
    const o = ishRef.current;
    if (!o || o.faza !== "bajar") return;
    clearTimeout(tinchTimer.current);
    const q = o.raund[o.i];
    const birinchi = o.xato === 0 && !o.yordam;
    setP(kuchYoz(til, q.id, birinchi));
    const n = { ...o, faza: "maqtov", togri: o.togri + (birinchi ? 1 : 0), ball: o.ball + (birinchi ? 1 : 0) };
    setIsh(n);
    say(maqtov(), () => {
      if (ishRef.current?.k !== o.k) return;
      if (n.tur === "cheksiz") { const m = { ...n, i: n.i + 1 >= n.raund.length ? 0 : n.i + 1, raund: n.i + 1 >= n.raund.length ? raundlar(n.pool, { yosh, kuch: p.kuch, hamma: n.hamma, n: 30 }) : n.raund }; raundBer(m); return; }
      if (n.i + 1 < n.raund.length) raundBer({ ...n, i: n.i + 1 });
      else oyinTugadi(n);   // eslint-disable-line no-use-before-define
    });
  };
  const oyinTugadi = (o) => {
    const y = yulduzHisob(o.togri, o.raund.length);
    if (o.tugunId) setP(yulduzYoz(til, o.tugunId, Math.max(y, 1)));   // o'ynab tugatdi — yo'l davom etadi
    setIsh(null);
    setNatijaK({ tur: o.tur, tugunId: o.tugunId, yulduz: Math.max(y, 1), togri: o.togri, jami: o.raund.length, pool: o.pool });
    say(izohGap("bolimTugadi", izoh));
  };
  // cheksiz: vaqt va jonlar
  const cheksizXato = (o) => {
    const jon = o.jon - 1;
    setP(kuchYoz(til, o.raund[o.i].id, false));
    if (jon <= 0) { cheksizTamom({ ...o, jon }); return; }   // eslint-disable-line no-use-before-define
    const n = { ...o, jon, faza: "tanla", korsat: o.raund[o.i].id, k: Date.now() };
    setIsh(n);
    say(teg(buyruq(o.raund[o.i].id, til, toliq), til), () => { if (ishRef.current?.k === n.k) raundBer({ ...n, i: n.i + 1 >= n.raund.length ? 0 : n.i + 1, korsat: null }); });
  };
  const cheksizTamom = (o) => {
    clearTimeout(tinchTimer.current);
    setP(cheksizYoz(til, o.ball));
    setIsh(null);
    setNatijaK({ tur: "cheksiz", ball: o.ball, eng: Math.max(p.cheksiz || 0, o.ball) });
    say(izohGap("vaqtTugadi", izoh));
  };
  const vaqtTugadi = () => { const o = ishRef.current; if (o?.tur === "cheksiz" && o.faza === "tanla") cheksizXato({ ...o, xato: 1 }); };

  const tugunBos = (t) => {
    if (!ochiq) return;
    if (t.holat === "qulf") { say(izohGap("qulf", izoh)); return; }
    if (t.holat === "ertaga") { jim?.(); say(izohGap("ertaga", izoh)); return; }
    if (t.tur === "organ") organBoshla(t.bolim, t.id);
    else if (t.tur === "oyna") oyinBoshla("oyna", t.id, bolimHarakatlari(t.bolim).map((h) => h.id));
    else if (t.tur === "takror") oyinBoshla("takror", t.id, takrorHarakatlari(t.gacha));
    else if (t.tur === "cheksiz") oyinBoshla("cheksiz", t.id, organilgan(p).length >= 4 ? organilgan(p) : HARAKATLAR.map((h) => h.id));
    else if (t.tur === "xona") { jim?.(); say(izohGap("xonaIntro", izoh), () => onXona?.(t.xona)); }
  };
  const chiqish = () => { jim?.(); clearTimeout(tinchTimer.current); setIsh(null); setNatijaK(null); };

  // ─────────── ko'rinish ───────────
  const ustoz = HR[gapiryapti ? "ustoz_gapir" : "ustoz_jim"];
  const UstozBurchak = () => (ustoz ? <span className={`hy-ustoz ${gapiryapti ? "is-gapir" : ""}`} aria-hidden="true"><img src={ustoz.src} alt="" draggable="false" /></span> : null);

  if (ish?.tur === "organ") {
    const id = ish.list[ish.i];
    const s = buyruq(id, til, false);
    return ekranda(<div className="hy-ish" role="dialog" aria-modal="true">
      <div className="hy-bar">
        <button type="button" className="hy-back" onClick={chiqish} aria-label={T("Yo‘lga qaytish")}>⬅️</button>
        <b>📖 {BOLIMLAR.find((b) => b.id === ish.bolim)?.nom[izoh === "uz" || izoh === "ru" || izoh === "en" ? izoh : "uz"]}</b>
        <span className="hy-nuqtalar">{ish.list.map((x, i) => <i key={x} className={i < ish.i ? "is-bor" : i === ish.i ? "is-hozir" : ""} />)}</span>
      </div>
      <HarakatSahna key={`${id}-${ish.faza}`} id={id} demo={ish.faza === "demo"} faol={ish.faza === "sen"} yordam={ish.yordam}
        onDemo={demoTugadi} onTayyor={organBajarildi} onFaollik={kutishTimer} />
      <div className="hy-panel">
        <UstozBurchak />
        <div className="hy-matn"><b dir="auto">{s}</b>{izoh !== til && <small>{manosi(id, izoh, false)}</small>}
          <em>{ish.faza === "demo" ? `👀 ${izohMatn("qara", izoh)}` : `👆 ${izohMatn(imoKalit(harakat(id).imo), izoh)}`}</em></div>
        <button type="button" className="hy-again" aria-label={T("Yana eshitish")} onClick={() => say(`${teg(s, til)} ${teg(buyruq(id, til, toliq), til)}`)}>🔊</button>
      </div>
    </div>);
  }

  if (ish && ish.raund) {
    const q = ish.raund[ish.i];
    const cmd = buyruq(q.id, til, toliq);
    const cheksiz = ish.tur === "cheksiz";
    return ekranda(<div className="hy-ish" role="dialog" aria-modal="true">
      <div className="hy-bar">
        <button type="button" className="hy-back" onClick={chiqish} aria-label={T("Yo‘lga qaytish")}>⬅️</button>
        <b>{TUGUN_BELGI[ish.tur === "bugun" ? "takror" : ish.tur]} {T(ish.tur === "bugun" ? "Bugungi takror" : TUGUN_NOM[ish.tur])}</b>
        {cheksiz ? <span className="hy-hisob">{"❤️".repeat(ish.jon)}{"🤍".repeat(Math.max(0, 3 - ish.jon))} · ⭐ {ish.ball}</span>
          : <span className="hy-hisob">{ish.i + 1}/{ish.raund.length} · ⭐ {ish.togri}</span>}
      </div>
      {cheksiz && ish.faza === "tanla" && <i key={ish.k} className="hy-vaqt" style={{ "--s": `${cheksizVaqt(ish.ball, yosh)}s` }} onAnimationEnd={vaqtTugadi} aria-hidden="true" />}
      {ish.faza === "tanla" ? <div className={`hy-kartalar n${q.kartalar.length}`}>
        {q.kartalar.map((id) => <button key={`${id}-${ish.notogri === id ? ish.nk : 0}`} type="button"
          className={`hy-karta ${ish.notogri === id ? "is-xato" : ""} ${ish.korsat === id ? "is-korsat" : ""}`} onClick={() => kartaTanlandi(id)}
          aria-label={manosi(id, izoh, toliq)}><SahnaRasm id={id} /></button>)}
      </div>
        : <HarakatSahna key={`${q.id}-${ish.i}-${ish.k}`} id={q.id} faol={ish.faza === "bajar"} yordam={ish.yordam}
          onTayyor={oyinBajarildi} onFaollik={kutishTimer} />}
      <div className="hy-panel">
        <UstozBurchak />
        <div className="hy-matn"><b dir="auto">{cmd}</b>
          {ish.faza === "bajar" ? <em>👆 {izohMatn(imoKalit(harakat(q.id).imo), izoh)}</em> : <em>🖐️ {izohMatn("tanla", izoh)}</em>}</div>
        <button type="button" className="hy-again" aria-label={T("Yana eshitish")} onClick={() => say(teg(cmd, til))}>🔊</button>
      </div>
    </div>);
  }

  return <div className="hy-yol" ref={yolRef}>
    {natijaK && <div className="hy-natija" role="status">
      <span aria-hidden="true">🎉</span>
      {natijaK.tur === "cheksiz" ? <b>⭐ {natijaK.ball} · 🏆 {natijaK.eng}</b>
        : natijaK.tur === "organ" ? <b>{T("Barakalla! Yangi harakatlarni o‘rganding")}</b>
          : <b>{"⭐".repeat(natijaK.yulduz || 1)} {natijaK.togri}/{natijaK.jami}</b>}
      <div className="hy-natija-btn">
        {natijaK.tur !== "organ" && natijaK.tur !== "cheksiz" && <button type="button" onClick={() => oyinBoshla(natijaK.tur, natijaK.tugunId, natijaK.pool)}>🔁 {T("Yana o‘ynash")}</button>}
        {natijaK.tur === "cheksiz" && <button type="button" onClick={() => tugunBos({ id: "cheksiz", tur: "cheksiz", holat: "ochiq" })}>🔁 {T("Yana o‘ynash")}</button>}
        {navbatdagi && navbatdagi.tur !== "cheksiz" && <button type="button" className="is-asosiy" onClick={() => tugunBos(navbatdagi)}>▶ {T("Keyingisi")}</button>}
        <button type="button" onClick={() => setNatijaK(null)}>🗺️ {T("Yo‘lga qaytish")}</button>
      </div>
      {ertaga && <p className="hy-ertaga-matn">🌙 {izohMatn("ertaga", izoh)}</p>}
    </div>}
    {!cheklovsiz && navbatdagi?.tur !== "cheksiz" && (navbatdagi || ertaga) && <div className={`hy-kunlik ${ertaga ? "is-tolgan" : ""}`}
      role="status" aria-label={`${izohMatn("bugunDars", izoh)}: ${bugunN}/${limit}`}>
      <span>📅 {izohMatn("bugunDars", izoh)}</span>
      <span className="hy-kunlik-nuqta" aria-hidden="true">{Array.from({ length: limit }, (_, k) => <i key={k} className={k < bugunN ? "is-bor" : ""} />)}</span>
      {ertaga && <small>🌙 {izohMatn("ertagaQisqa", izoh)}</small>}
    </div>}
    {bugun.length >= 2 && <button type="button" className="hy-bugun" onClick={() => oyinBoshla("bugun", null, bugun)} disabled={!ochiq}>
      🔁 {T("Bugungi takror")} <small>({bugun.length})</small></button>}
    {BOLIMLAR.map((b, bi) => {
      const bt = tugunlar.filter((t) => t.bolim === b.id || (t.tur === "takror" && t.gacha === bi + 1));
      return <section key={b.id} className={`hy-bolim hy-bolim--${b.id}`}>
        <h3><span aria-hidden="true">{HR[`bolim_${b.id}`] ? <img className="hy-bolim-belgi" src={HR[`bolim_${b.id}`].src} alt="" draggable="false" /> : b.emoji}</span> {b.nom[["uz", "ru", "en"].includes(izoh) ? izoh : "uz"]}
          <small>{bolimHarakatlari(b.id).map((h) => <span key={h.id} dir="auto">{buyruq(h.id, til, false)}</span>)}</small></h3>
        <div className="hy-tugunlar">{bt.map((t, i) => <Tugun key={t.id} t={t} i={i} p={p} til={til} izoh={izoh} onBos={() => tugunBos(t)} xonaYulduz={xonaYulduz} />)}</div>
      </section>;
    })}
    <section className="hy-bolim hy-bolim--oxir">
      <h3><span aria-hidden="true">🏁</span> {T("Katta sinov")}</h3>
      <div className="hy-tugunlar">{tugunlar.filter((t) => !t.bolim && t.tur !== "takror").map((t, i) => <Tugun key={t.id} t={t} i={i} p={p} til={til} izoh={izoh} onBos={() => tugunBos(t)} xonaYulduz={xonaYulduz} />)}</div>
    </section>
  </div>;
}

function Tugun({ t, i, p, izoh, onBos, xonaYulduz }) {
  const y = (p.yulduz || {})[t.id] || 0;
  const xona = t.tur === "xona" ? XONALAR.find((x) => x.id === t.xona) : null;
  const nom = xona ? `${xona.emoji} ${T(xona.nom)}` : T(TUGUN_NOM[t.tur]);
  const belgi = t.holat === "qulf" ? <Belgi k="qulf" emoji="🔒" /> : t.holat === "ertaga" ? "🌙" : <Belgi k={t.tur} emoji={TUGUN_BELGI[t.tur]} />;
  return <button type="button" className={`hy-tugun is-${t.holat} hy-tugun--${t.tur}`} style={{ "--i": i }} onClick={onBos}
    aria-label={`${nom}${t.holat === "qulf" ? ` — ${T("yopiq")}` : t.holat === "ertaga" ? ` — ${izohMatn("ertagaQisqa", izoh)}` : ""}`}>
    <span className="hy-tugun-doira" aria-hidden="true">{belgi}</span>
    <b>{nom}</b>
    {t.holat === "ertaga" ? <small>{izohMatn("ertagaQisqa", izoh)}</small>
      : t.tur === "cheksiz" ? <small>🏆 {p.cheksiz || 0}</small>
      : t.tur === "xona" ? <small>⭐ {Math.min(3, xonaYulduz(t.xona))}/3</small>
        : (t.tur === "oyna" || t.tur === "takror") ? <small aria-hidden="true">{[1, 2, 3].map((k) => (k <= y ? "⭐" : "☆")).join("")}</small>
          : <small aria-hidden="true">{t.holat === "tugadi" ? "✅" : ""}</small>}
  </button>;
}
