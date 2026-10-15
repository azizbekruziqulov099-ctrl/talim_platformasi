import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { aralashKerak, aralashOqi } from "../../speech/aralashOvoz.js";
import { XONALAR, SOZLAR, BUYRUQLAR, BUYRUQ_MEN } from "./xonaLugat.js";
import { RASMLAR, FONLAR } from "./rasmlar.js";
import {
  soz, manosi, teg, gap, izohGap, izohMatn, yoshGuruhi, rejimlar, savollar, buyruqVariantlari,
  baho, ovozJinsi, joylash, natija, saqlash, hammasi, xona as xonaTop, srsOl, srsYoz, xonaPuxta,
  xotiraKartalar, yoqoldiSavol, ortiqchaSavol, tartibSavol, raundSoni,
} from "./xonaRules.js";
import { tik, oqi, holat as vaqtHolati, FAOL } from "./oyinVaqti.js";
import { CONTENT_LOCALES } from "../../speech/language.js";
import { kidRate, ustozRate } from "../../lesson/kidLessonRules.js";
import { eslab } from "../sozBoyligi.js";
import { uiText as T } from "../../interface/interfaceRuntime.js";
import { useInterface } from "../../interface/InterfacePreferences.jsx";
import HarakatYoli from "../harakat/HarakatYoli.jsx";
import "./xonalar.css";

const REJIM = {
  kashf: { emoji: "🔍", nom: "Kashf qil" },
  top: { emoji: "👆", nom: "Top" },
  xotira: { emoji: "🃏", nom: "Xotira" },
  ayt: { emoji: "🗣️", nom: "Ayt" },
  yordam: { emoji: "🤝", nom: "Yordam ber" },
  buyruq: { emoji: "🧑‍🏫", nom: "Ustoz aytdi" },
  yoqoldi: { emoji: "🙈", nom: "Nima yo‘qoldi?" },
  ortiqcha: { emoji: "🧩", nom: "Ortiqchasi" },
  tartib: { emoji: "🔢", nom: "Ketma-ketlik" },
};
// Ranglar — rasm emas, toza rang dog'i (ko'ylak yoki krossovka rasmi bolani chalg'itadi)
const RANGLAR = { red: "#E53935", blue: "#1E63D6", green: "#2EA44F", yellow: "#FFD21F", pink: "#FF7EB6", purple: "#8E44C9", black: "#222", white: "#FFFFFF" };
const BUYRUQ_HAMMA = [...BUYRUQLAR, ...BUYRUQ_MEN];
const rasmBor = (id) => Boolean(RANGLAR[id] || RASMLAR[id]);
const Rasm = ({ id, className = "" }) => (RANGLAR[id]
  ? <span className={`${className} xo-rang`} style={{ "--rang": RANGLAR[id] }} aria-hidden="true" />
  : RASMLAR[id]
    ? <img className={className} src={RASMLAR[id]} alt="" draggable="false" />
    : <span className={`${className} is-emoji`} aria-hidden="true">{SOZLAR[id]?.emoji || BUYRUQ_HAMMA.find((b) => b.id === id)?.emoji || "⭐"}</span>);
/** REV144: xona telefonda butun ekranni egallaydi (sahifa sarlavhasi ostida, body ichida chiziladi). */
const ekranda = (el) => (globalThis.document?.body ? createPortal(el, globalThis.document.body) : el);
const kut = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * REV127–128: O'yin xonalari — til darsidan keyin takrorlash va gapirish uchun 7 ta tajriba xonasi
 * (oshxona, bolalar xonasi, hovli, shahar, sinfxona, tanam, ob-havo). 9 xil o'yin, so'zlar takrorlash tizimi bilan
 * haftalar davomida mustahkamlanadi. Vaqt: 1 soatdan keyin 15 daqiqa dam, kuniga ko'pi bilan 2 soat.
 * til — o'rganiladigan til (en, ru, de, fr, es, ar, tr, zh, ja, ko); izoh — tushuntirish tili (uz, ru, en).
 */
export default function TilXonalari({ apiBase = "", til = "en", izoh = "uz", grade = "", onClose, cheklovsiz = false, sarlavha = "" }) {
  useInterface();
  const yosh = yoshGuruhi(grade);
  const [xonaId, setXonaId] = useState(null);
  const [rejim, setRejim] = useState("kashf");
  const [oyin, setOyin] = useState(null);          // {rejim, list, i, xato, yulduz, ...}
  const [faol, setFaol] = useState(null);
  const [xato, setXato] = useState(null);           // {id, n}
  const [gapir, setGapir] = useState(null);
  const [matn, setMatn] = useState(null);           // {asosiy, izoh}
  const [mik, setMik] = useState("");
  const [tamom, setTamom] = useState(null);
  const [vaqt, setVaqt] = useState(() => (cheklovsiz ? { holat: "ok" } : vaqtHolati(oqi())));
  const [, setYangi] = useState(0);
  const audio = useRef(null);
  const rec = useRef(null);
  const token = useRef(0);
  const alive = useRef(true);
  const oyinRef = useRef(null);
  oyinRef.current = oyin;
  const lastTap = useRef(Date.now());
  const ogohlandi = useRef(false);
  const mikYoq = useRef(!(globalThis.SpeechRecognition || globalThis.webkitSpeechRecognition));

  useEffect(() => () => { alive.current = false; token.current++; try { audio.current?.pause(); } catch { /* */ } try { rec.current?.abort(); } catch { /* */ } }, []);

  const jim = useCallback(() => {
    token.current++;
    try { audio.current?.pause(); } catch { /* yopilgan */ }
    try { rec.current?.abort(); } catch { /* yopilgan */ }
    rec.current = null;
    setGapir(null); setMik("");
  }, []);

  // Ovoz: serverdagi TTS. Tugagach done() chaqiriladi; ovoz kelmasa ham o'yin to'xtab qolmaydi.
  const ayt = useCallback((text, done, kim = null) => {
    if (!alive.current) return;
    try { audio.current?.pause(); } catch { /* */ }
    const my = ++token.current;
    let fin = false;
    const end = () => { if (fin) return; fin = true; if (alive.current && my === token.current) { setGapir(null); done?.(); } };
    if (!String(text || "").trim()) { end(); return; }
    setGapir(kim || "ustoz");
    // REV139: chet tildagi so'zlarni qurilma ovozi o'qiydi, o'zbekchasi — serverdan (Azure limiti tejaladi)
    if (aralashKerak(text)) {
      const ctl = aralashOqi(String(text).slice(0, 1500), (m) => `${String(apiBase).replace(/\/+$/, "")}/api/ovoz?k=133&${new URLSearchParams({ ...Object.fromEntries(new URLSearchParams({ jins: ovozJinsi(kim), tezlik: kim ? ustozRate(grade) : kidRate(grade) })), matn: m })}`,
        { rate: 0.85, onEnd: end });
      audio.current = { pause: () => ctl.stop() };
      setTimeout(end, Math.min(30000, 8000 + String(text).length * 170));
      return;
    }
    try {
      const params = new URLSearchParams({ matn: String(text).slice(0, 1500), jins: ovozJinsi(kim),
        tezlik: kim ? ustozRate(grade) : kidRate(grade) });
      const a = new Audio(`${String(apiBase).replace(/\/+$/, "")}/api/ovoz?k=133&${params}`);
      audio.current = a;
      a.onended = end; a.onerror = end;
      a.play().catch(() => setTimeout(end, 1500));
      setTimeout(end, Math.min(25000, 5000 + String(text).length * 140));
    } catch { setTimeout(end, 800); }
  }, [apiBase, grade]);
  const aytP = (text, kim = null) => new Promise((r) => ayt(text, r, kim));

  // — vaqt nazorati —
  useEffect(() => {
    if (cheklovsiz) return undefined;
    const bor = () => { lastTap.current = Date.now(); };
    globalThis.addEventListener?.("pointerdown", bor, true);
    const id = setInterval(() => {
      const korinadi = (globalThis.document?.visibilityState || "visible") === "visible";
      const faolmi = Date.now() - lastTap.current < FAOL * 1000;
      const h = tik(korinadi && faolmi ? 15 : 0);
      setVaqt(h);
    }, 15000);
    return () => { clearInterval(id); globalThis.removeEventListener?.("pointerdown", bor, true); };
  }, [cheklovsiz]);
  useEffect(() => {
    if (cheklovsiz) return;
    if (vaqt.holat !== "ok") { jim(); setOyin(null); ayt(izohGap(vaqt.holat === "tanaffus" ? "tanaffus" : "kunTugadi", izoh, { til })); }
    else if (vaqt.ogoh && !ogohlandi.current) { ogohlandi.current = true; if (!oyinRef.current) ayt(izohGap("ogohlantir", izoh, { til })); }
  }, [vaqt.holat, vaqt.ogoh]); // eslint-disable-line react-hooks/exhaustive-deps

  const x = xonaTop(xonaId);
  const joylar = useMemo(() => (xonaId ? joylash(xonaId) : []), [xonaId]);
  const saqlangan = natija()[til] || {};
  const srs = srsOl(til);
  const yordamchi = (id) => (izoh !== til ? izohGap("manosi", izoh, { t: soz(id, til), til, i: manosi(id, izoh) }) : "");
  const sozMatn = (id) => ({ asosiy: soz(id, til), izoh: izoh !== til ? manosi(id, izoh) : "" });
  const rasmliPool = () => hammasi(x).filter(rasmBor);
  const qayd = (id, ok) => { if (id && SOZLAR[id]) { srsYoz(til, id, ok); if (ok) eslab({ sozlar: [{ say: soz(id, til), emoji: SOZLAR[id].emoji, til }] }); } };

  // — o'yin boshqaruvi —
  const yakunla = (o) => {
    setOyin(null); setFaol(null); setMatn(null);
    saqlash(til, xonaId, { yulduz: o.yulduz });
    setTamom({ yulduz: o.yulduz });
    ayt(izohGap("tugadi", izoh, { til }));
  };
  const keyingi = (o) => {
    const i = o.i + 1;
    if (i >= o.list.length) { yakunla(o); return; }
    const n = { ...o, i, xato: 0, variantlar: null, faza: null, bosildi: [] };
    setOyin(n);
    savolBer(n); // eslint-disable-line no-use-before-define
  };
  const togri = (o, id) => { const n = { ...o, yulduz: o.yulduz + 1 }; setOyin(n); qayd(id, true); return n; };

  const tingla = (id, o) => {
    const word = soz(id, til);
    const R = globalThis.SpeechRecognition || globalThis.webkitSpeechRecognition;
    if (!R || mikYoq.current) { setMik("tugma"); return; }
    const my = token.current;
    let done = false;
    const r = new R();
    rec.current = r;
    r.lang = CONTENT_LOCALES[til] || "en-US";
    r.interimResults = false;
    r.maxAlternatives = 5;
    const keldi = (alts) => {
      if (done) return; done = true;
      rec.current = null;
      if (!alive.current || my !== token.current) return;
      setMik("");
      if (alts === null) { mikYoq.current = true; setMik("tugma"); return; }
      const g = baho(alts, word, til);
      if (g.togri) {
        const n = togri(o, id);
        setMatn({ asosiy: `⭐ ${word}`, izoh: alts[0] || "" });
        ayt(teg(gap("barakalla", til), til), () => keyingi(n));
      } else if (o.xato < 1) {
        const n = { ...o, xato: o.xato + 1 };
        setOyin(n);
        setMatn({ asosiy: word, izoh: alts[0] ? `🎤 ${alts[0]}` : "" });
        ayt(`${teg(word, til)} ${teg(gap("ayt", til), til)}`, () => tingla(id, n));
      } else {
        qayd(id, false);
        ayt(teg(gap("mana", til, word), til), () => keyingi(o));
      }
    };
    r.onresult = (e) => keldi(Array.from(e.results?.[0] || []).map((a) => a.transcript));
    r.onerror = (e) => { if (e?.error === "not-allowed" || e?.error === "service-not-allowed" || e?.error === "audio-capture") keldi(null); else if (e?.error !== "aborted") keldi([]); };
    r.onend = () => keldi([]);
    try { r.start(); setMik("tinglayapti"); } catch { mikYoq.current = true; setMik("tugma"); }
  };

  const savolBer = async (o) => {
    const q = o.list[o.i];
    setXato(null); setMik("");
    if (o.rejim === "top") {
      setFaol(null);
      setMatn({ asosiy: gap("korsat", til, soz(q.id, til)), izoh: izoh !== til ? manosi(q.id, izoh) : "" });
      ayt(`${teg(gap("korsat", til, soz(q.id, til)), til)}${yosh !== "katta" && o.i < 2 ? ` ${yordamchi(q.id)}` : ""}`);
    } else if (o.rejim === "ayt") {
      setFaol(q.id);
      setMatn({ asosiy: gap("bunima", til), izoh: "" });
      ayt(teg(gap("bunima", til), til), () => tingla(q.id, o));
    } else if (o.rejim === "yordam") {
      setFaol(null);
      setMatn({ asosiy: q.w[til], izoh: izoh !== til ? q.w[izoh] : "" });
      const izohOvoz = izoh !== til && yosh !== "katta" ? teg(q.w[izoh], izoh) : "";
      ayt(teg(q.w[til], til), () => { if (izohOvoz) ayt(izohOvoz); }, q.kim);
    } else if (o.rejim === "buyruq") {
      setFaol(null);
      const variantlar = buyruqVariantlari(q.id, Math.random, xonaId);
      setOyin({ ...o, variantlar });
      setMatn({ asosiy: q.w[til], izoh: izoh !== til ? q.w[izoh] : "" });
      const izohOvoz = izoh !== til && yosh !== "katta" ? ` ${teg(q.w[izoh], izoh)}` : "";
      ayt(`${teg(q.w[til], til)}${izohOvoz}`, null, "teacher");
    } else if (o.rejim === "ortiqcha") {
      setOyin({ ...o, variantlar: q.variantlar });
      setMatn({ asosiy: gap("ortiqcha", til), izoh: "" });
      ayt(teg(gap("ortiqcha", til), til));
    } else if (o.rejim === "yoqoldi") {
      // 1) ko'rsatamiz va har birini aytamiz, 2) yopamiz, 3) bittasi yo'q — so'raymiz
      setOyin({ ...o, faza: "qara" });
      setMatn({ asosiy: gap("qara", til), izoh: "" });
      await aytP(teg(gap("qara", til), til));
      for (const id of q.korsat) { if (!alive.current || oyinRef.current?.rejim !== "yoqoldi") return; setFaol(id); await aytP(teg(soz(id, til), til)); }
      setFaol(null);
      await kut(1200);
      if (!alive.current || oyinRef.current?.rejim !== "yoqoldi") return;
      setOyin((p) => (p ? { ...p, faza: "yopiq" } : p));
      await kut(1300);
      if (!alive.current || oyinRef.current?.rejim !== "yoqoldi") return;
      setOyin((p) => (p ? { ...p, faza: "savol", variantlar: q.variantlar } : p));
      setMatn({ asosiy: gap("yoqoldi", til), izoh: "" });
      ayt(teg(gap("yoqoldi", til), til));
    } else if (o.rejim === "tartib") {
      setOyin({ ...o, faza: "tingla", bosildi: [] });
      setMatn({ asosiy: q.map((id) => soz(id, til)).join(" → "), izoh: "" });
      await aytP(teg(gap("tartib", til), til));
      for (const id of q) { if (!alive.current || oyinRef.current?.rejim !== "tartib") return; setFaol(id); await aytP(teg(soz(id, til), til)); await kut(250); }
      setFaol(null);
      setMatn({ asosiy: "❓ → ❓ → ❓".slice(0, q.length * 4 - 3), izoh: "" });
      setOyin((p) => (p ? { ...p, faza: "bos", bosildi: [] } : p));
    }
  };

  const boshla = (r) => {
    if (vaqt.holat !== "ok" && !cheklovsiz) return;
    jim();
    setRejim(r); setTamom(null); setFaol(null); setXato(null);
    if (r === "kashf") { setOyin(null); setMatn(null); ayt(izohGap("kashf", izoh, { til })); return; }
    const pool = rasmliPool();
    let list;
    if (r === "xotira") {
      const kartalar = xotiraKartalar(pool, yosh, Math.random, srs);
      const o = { rejim: r, list: [kartalar], i: 0, xato: 0, yulduz: 0, kartalar, ochiq: [], topilgan: [] };
      setOyin(o); setMatn({ asosiy: gap("juft", til), izoh: "" });
      ayt(`${izohGap("xotira", izoh, { til })} ${teg(gap("juft", til), til)}`);
      return;
    }
    if (r === "yoqoldi") list = Array.from({ length: Math.max(3, Math.round(raundSoni(yosh) / 2)) }, () => yoqoldiSavol(pool, yosh, Math.random, srs));
    else if (r === "ortiqcha") list = Array.from({ length: raundSoni(yosh) }, () => ortiqchaSavol(hammasi(x)));
    else if (r === "tartib") list = Array.from({ length: 5 }, (_, i) => tartibSavol(hammasi(x), 2 + Math.floor(i / 2)));
    else list = savollar(r, xonaId, yosh, Math.random, srs);
    if (!list.length) return;
    const o = { rejim: r, list, i: 0, xato: 0, yulduz: 0, variantlar: null, faza: null, bosildi: [] };
    setOyin(o);
    ayt(izohGap(r, izoh, { til }), () => savolBer(o));
  };

  const bosildi = (id) => {
    if (vaqt.holat !== "ok" && !cheklovsiz) return;
    const o = oyinRef.current;
    if (!o) {   // kashf
      jim();
      setFaol(id);
      setMatn(sozMatn(id));
      const yangi = !(saqlangan[xonaId]?.kashf || []).includes(id);
      if (yangi) { saqlash(til, xonaId, { kashf: [id] }); setYangi((v) => v + 1); }
      const kim = x?.odamlar.includes(id) ? id : null;
      ayt(teg(soz(id, til), til), () => { if (yosh !== "katta" || yangi) ayt(yordamchi(id)); }, kim);
      return;
    }
    if (o.rejim === "tartib") {
      if (o.faza !== "bos") return;
      const q = o.list[o.i];
      const kerak = q[o.bosildi.length];
      if (id === kerak) {
        const bos = [...o.bosildi, id];
        setFaol(id);
        if (bos.length === q.length) {
          jim();
          q.forEach((w) => qayd(w, true));
          const n = { ...o, bosildi: bos, faza: null, yulduz: o.yulduz + 1 };
          setOyin(n);
          ayt(`${teg(gap("barakalla", til), til)}`, () => keyingi(n));
        } else setOyin({ ...o, bosildi: bos });
      } else {
        jim();
        setXato({ id, n: Date.now() });
        qayd(kerak, false);
        setOyin({ ...o, faza: null });
        setMatn({ asosiy: q.map((w) => soz(w, til)).join(" → "), izoh: "" });
        ayt(`${teg(gap("yana", til), til)} ${q.map((w) => teg(soz(w, til), til)).join(" ")}`, () => keyingi(o));
      }
      return;
    }
    if (!["top", "yordam"].includes(o.rejim)) return;
    const q = o.list[o.i];
    const kerak = o.rejim === "yordam" ? q.javob : q.id;
    if (id === kerak) {
      jim();
      const n = togri(o, id);
      setFaol(id);
      if (o.rejim === "yordam") ayt(teg(gap("marhamat", til), til), () => ayt(teg(gap("rahmat", til), til), () => keyingi(n), q.kim));
      else ayt(`${teg(gap("barakalla", til), til)} ${teg(soz(id, til), til)}`, () => keyingi(n));
    } else {
      jim();
      setXato({ id, n: Date.now() });
      const n = { ...o, xato: o.xato + 1 };
      setOyin(n);
      if (n.xato >= 2) {
        setFaol(kerak);
        qayd(kerak, false);
        ayt(teg(gap("mana", til, soz(kerak, til)), til), () => keyingi(n));
      } else ayt(`${teg(soz(id, til), til)}? ${teg(gap("yana", til), til)}`, null, o.rejim === "yordam" ? q.kim : null);
    }
  };

  // Variantli o'yinlar: buyruq, ortiqcha, yo'qoldi
  const variantTanlandi = (id) => {
    const o = oyinRef.current;
    if (!o) return;
    const q = o.list[o.i];
    const kerak = o.rejim === "buyruq" ? q.id : o.rejim === "ortiqcha" ? q.begona : o.rejim === "yoqoldi" ? q.yoq : null;
    if (!kerak || (o.rejim === "yoqoldi" && o.faza !== "savol")) return;
    jim();
    const kim = o.rejim === "buyruq" ? "teacher" : null;
    if (id === kerak) {
      const n = togri(o, o.rejim === "buyruq" ? null : id);
      setFaol(id);
      ayt(`${teg(gap("barakalla", til), til)}${o.rejim !== "buyruq" ? ` ${teg(soz(id, til), til)}` : ""}`, () => keyingi(n), kim);
    } else {
      setXato({ id, n: Date.now() });
      const n = { ...o, xato: o.xato + 1 };
      setOyin(n);
      if (n.xato >= 2) {
        if (o.rejim !== "buyruq") qayd(kerak, false);
        setFaol(kerak);
        ayt(o.rejim === "buyruq" ? teg(q.w[til], til) : teg(gap("mana", til, soz(kerak, til)), til), () => keyingi(n), kim);
      } else ayt(teg(gap("yana", til), til), o.rejim === "buyruq" ? () => ayt(teg(q.w[til], til), null, kim) : null, kim);
    }
  };

  // Xotira kartalari
  const kartaOch = (k) => {
    const o = oyinRef.current;
    if (!o || o.rejim !== "xotira" || o.ochiq.length >= 2 || o.ochiq.includes(k)) return;
    const karta = o.kartalar.find((c) => c.k === k);
    if (!karta || o.topilgan.includes(karta.id)) return;
    const ochiq = [...o.ochiq, k];
    ayt(teg(soz(karta.id, til), til));
    if (ochiq.length < 2) { setOyin({ ...o, ochiq }); return; }
    const [a, b] = ochiq.map((kk) => o.kartalar.find((c) => c.k === kk));
    if (a.id === b.id) {
      qayd(a.id, true);
      const topilgan = [...o.topilgan, a.id];
      const n = { ...o, ochiq: [], topilgan, yulduz: o.yulduz + 1 };
      setOyin(n);
      if (topilgan.length * 2 === o.kartalar.length) setTimeout(() => { if (alive.current) yakunla(n); }, 900);
    } else {
      setOyin({ ...o, ochiq });
      setTimeout(() => { if (alive.current) setOyin((p) => (p && p.rejim === "xotira" ? { ...p, ochiq: [] } : p)); }, 1100);
    }
  };

  const aytdim = () => {   // mikrofon yo'q qurilmada: bola ovoz chiqarib aytadi va tugmani bosadi
    const o = oyinRef.current;
    if (!o) return;
    const q = o.list[o.i];
    setMik("");
    const n = togri(o, q.id);
    setMatn(sozMatn(q.id));
    ayt(`${teg(gap("mana", til, soz(q.id, til)), til)} ${teg(gap("barakalla", til), til)}`, () => keyingi(n));
  };

  const xonagaKir = (id) => {
    if (vaqt.holat !== "ok" && !cheklovsiz) return;
    jim();
    setXonaId(id); setRejim("kashf"); setOyin(null); setFaol(null); setMatn(null); setTamom(null);
    const r = XONALAR.find((v) => v.id === id);
    ayt(`${teg(gap("salom", til), til)} ${izohGap("kashf", izoh, { til })}`.trim(), null, r?.odamlar[0] || null);
  };
  const chiq = () => { jim(); if (xonaId) { setXonaId(null); setOyin(null); setMatn(null); setTamom(null); } else onClose?.(); };

  const vaqtTosiq = !cheklovsiz && vaqt.holat !== "ok" && <div className="xo-vaqt" role="alert">
    <span aria-hidden="true">{vaqt.holat === "tanaffus" ? "🧘" : "🌙"}</span>
    <b>{izohMatn(vaqt.holat === "tanaffus" ? "tanaffus" : "kunTugadi", izoh)}</b>
    {vaqt.holat === "tanaffus" && <small>⏳ {vaqt.qoldi} {T("daq.")}</small>}
  </div>;

  // — xonalar ro'yxati —
  // REV144: xona ochiq paytda orqadagi sahifa aylanmasin; ustoz ko'rsatgan narsa telefonda ekranga suriladi
  useEffect(() => {
    if (!xonaId || !globalThis.document?.body) return undefined;
    const b = globalThis.document.body, eski = b.style.overflow;
    b.style.overflow = "hidden";
    return () => { b.style.overflow = eski; };
  }, [xonaId]);
  useEffect(() => {
    if (!faol) return;
    const el = globalThis.document?.querySelector(".xo-ekran .is-faol");
    try { el?.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" }); } catch { /* eski brauzer */ }
  }, [faol]);
  if (!x) {
    return <div className="xo-root">
      <div className="xo-bar">
        <button type="button" className="xo-back" onClick={chiq} aria-label={T("Orqaga")}>⬅️</button>
        <b className="xo-title">🎮 {sarlavha || T("O‘yin xonalari")}</b>
        {!cheklovsiz && vaqt.holat === "ok" && <span className="xo-time" title={T("Bugun qolgan vaqt")}>⏳ {vaqt.qoldi}′</span>}
      </div>
      {vaqtTosiq}
      {/* REV141: asosiy — bosqichma-bosqich «Harakat o'yinlari» yo'li; so'z xonalari yo'lning bosqichlari sifatida ochiladi */}
      <HarakatYoli til={til} izoh={izoh} grade={grade} ayt={ayt} jim={jim} gapiryapti={Boolean(gapir)}
        xonaYulduz={(id) => saqlangan[id]?.yulduz || 0} onXona={xonagaKir} ochiq={cheklovsiz || vaqt.holat === "ok"} cheklovsiz={cheklovsiz} />
      <details className="xo-hamma"><summary>🏠 {T("Barcha so‘z xonalari")}</summary>
      <div className="xo-list">
        {XONALAR.map((r) => {
          const s = saqlangan[r.id] || {};
          const puxta = Math.round(xonaPuxta(r.id, srs) * 100);
          return <button key={r.id} type="button" className={`xo-card xo-card--${r.id}`} onClick={() => xonagaKir(r.id)} disabled={!cheklovsiz && vaqt.holat !== "ok"}>
            {r.fon && FONLAR[r.fon] ? <img className="xo-card-fon" src={FONLAR[r.fon]} alt="" /> : <span className="xo-card-emoji" aria-hidden="true">{r.emoji}</span>}
            <b>{r.emoji} {T(r.nom)}</b>
            <small>⭐ {s.yulduz || 0} · 🏅 {puxta}%</small>
            <i className="xo-progress" style={{ "--p": `${puxta}%` }} aria-hidden="true" />
          </button>;
        })}
      </div>
      </details>
    </div>;
  }

  const kashfQilingan = new Set(saqlangan[xonaId]?.kashf || []);
  const savol = oyin?.list[oyin.i];
  const overlay = oyin && ["xotira", "ortiqcha", "yoqoldi", "buyruq"].includes(oyin.rejim);
  return ekranda(<div className={`xo-root xo-ekran ${overlay ? "xo-fit" : ""}`} role="dialog" aria-modal="true">
    <div className="xo-bar">
      <button type="button" className="xo-back" onClick={chiq} aria-label={T("Orqaga")}>⬅️</button>
      <b className="xo-title">{x.emoji} {T(x.nom)}</b>
      {!cheklovsiz && vaqt.holat === "ok" && <span className="xo-time" title={T("Bugun qolgan vaqt")}>⏳ {vaqt.qoldi}′</span>}
      <span className="xo-stars" aria-label={T("Yulduzlar")}>⭐ {(saqlangan[xonaId]?.yulduz || 0) + (oyin?.yulduz || 0)}</span>
    </div>
    <div className="xo-modes" role="tablist">
      {rejimlar(yosh, xonaId).map((r) => <button key={r} type="button" role="tab" aria-selected={rejim === r}
        className={`xo-mode ${rejim === r ? "is-on" : ""}`} onClick={() => boshla(r)} disabled={!cheklovsiz && vaqt.holat !== "ok"}>
        <span aria-hidden="true">{REJIM[r].emoji}</span> {T(REJIM[r].nom)}
      </button>)}
    </div>
    <div className="xo-scroll">
      <div className={`xo-sahna xo-sahna--${xonaId} ${x.fon ? "has-fon" : ""}`} style={{ aspectRatio: String(x.nisbat), "--nisbat": x.nisbat }}>
        {x.fon && FONLAR[x.fon] ? <img className="xo-fon" src={FONLAR[x.fon]} alt="" draggable="false" /> : <Bezak id={xonaId} />}
        {joylar.map((p) => {
          if (p.hs) {
            const cls = ["xo-hs", faol === p.id ? "is-faol" : "", gapir === p.id ? "is-gapir" : "", xato?.id === p.id ? "is-xato" : ""].filter(Boolean).join(" ");
            return <button key={`hs-${p.id}-${xato?.id === p.id ? xato.n : 0}`} type="button" className={cls}
              style={{ left: `${p.x - p.w / 2}%`, top: `${p.y - p.h / 2}%`, width: `${p.w}%`, height: `${p.h}%` }}
              aria-label={soz(p.id, til)} onClick={() => bosildi(p.id)} />;
          }
          const odam = x.odamlar.includes(p.id);
          const cls = ["xo-item", odam ? "is-odam" : "", faol === p.id ? "is-faol" : "", gapir === p.id ? "is-gapir" : "",
            xato?.id === p.id ? "is-xato" : "", !oyin && kashfQilingan.has(p.id) ? "is-bor" : "",
            oyin?.rejim === "tartib" && oyin.bosildi?.includes(p.id) ? "is-tanlandi" : ""].filter(Boolean).join(" ");
          return <button key={`${p.id}-${xato?.id === p.id ? xato.n : 0}`} type="button" className={cls}
            style={{ left: `${p.x}%`, top: `${p.y}%`, width: `${p.s}%`, aspectRatio: String(p.a || 1), "--s": p.s }}
            aria-label={soz(p.id, til)} onClick={() => bosildi(p.id)}>
            <Rasm id={p.id} className="xo-pic" />
            {gapir === p.id && <span className="xo-bubble" aria-hidden="true">💬</span>}
          </button>;
        })}
        {overlay && <div className={`xo-tray xo-tray--${oyin.rejim}`}>
          {oyin.rejim === "xotira" && <div className={`xo-memo n${oyin.kartalar.length}`}>
            {oyin.kartalar.map((c) => {
              const ochiq = oyin.ochiq.includes(c.k) || oyin.topilgan.includes(c.id);
              return <button key={c.k} type="button" className={`xo-memo-card ${ochiq ? "is-open" : ""} ${oyin.topilgan.includes(c.id) ? "is-done" : ""}`}
                onClick={() => kartaOch(c.k)} aria-label={ochiq ? soz(c.id, til) : "?"}>
                {ochiq ? <Rasm id={c.id} className="xo-pic" /> : <span className="xo-memo-back" aria-hidden="true">🕊️</span>}
              </button>;
            })}
          </div>}
          {oyin.rejim === "yoqoldi" && savol && <div className="xo-show">
            {(oyin.faza === "savol" ? [...savol.qolgan, "__bosh"] : savol.korsat).map((id, i) => <span key={`${id}-${i}`}
              className={`xo-show-card ${oyin.faza === "yopiq" ? "is-closed" : ""} ${faol === id ? "is-faol" : ""}`}>
              {oyin.faza === "yopiq" ? <span className="xo-memo-back" aria-hidden="true">🙈</span>
                : id === "__bosh" ? <span className="xo-q" aria-hidden="true">❓</span> : <Rasm id={id} className="xo-pic" />}
            </span>)}
          </div>}
          {oyin.variantlar && (oyin.rejim !== "yoqoldi" || oyin.faza === "savol") && <div className="xo-cards">
            {oyin.variantlar.map((id) => <button key={`${id}-${xato?.id === id ? xato.n : 0}`} type="button"
              className={`xo-cmd ${xato?.id === id ? "is-xato" : ""} ${faol === id ? "is-faol" : ""}`} onClick={() => variantTanlandi(id)}
              aria-label={oyin.rejim === "buyruq" ? BUYRUQ_HAMMA.find((b) => b.id === id)?.w[til] : soz(id, til)}>
              <Rasm id={id} className="xo-pic" />
            </button>)}
          </div>}
        </div>}
        {tamom && <div className="xo-tamom" role="status">
          <span aria-hidden="true">🎉</span><b>⭐ × {tamom.yulduz}</b>
          <button type="button" onClick={() => boshla(rejim)}>🔁 {T("Yana o‘ynash")}</button>
          <button type="button" onClick={() => boshla("kashf")}>🔍 {T("Kashf qil")}</button>
        </div>}
        {vaqtTosiq}
      </div>
    </div>
    <div className="xo-panel" aria-live="polite">
      {oyin && oyin.rejim !== "xotira" && <span className="xo-step">{oyin.i + 1}/{oyin.list.length}</span>}
      <div className="xo-text">
        {matn?.asosiy ? <b dir="auto">{matn.asosiy}</b> : <b className="is-hint">{izohMatn(rejim, izoh)}</b>}
        {matn?.izoh && <small dir="auto">{matn.izoh}</small>}
      </div>
      {savol && oyin?.rejim === "ayt" && mik === "tinglayapti" && <span className="xo-mic is-on" aria-label={T("Gapir…")}>🎤</span>}
      {savol && oyin?.rejim === "ayt" && mik === "tugma" && <button type="button" className="xo-said" onClick={aytdim}>✅ {T("Aytdim")}</button>}
      {matn?.asosiy && <button type="button" className="xo-again" aria-label={T("Yana eshitish")}
        onClick={() => {
          const r = oyin?.rejim;
          const text = r === "yordam" || r === "buyruq" ? teg(savol.w[til], til)
            : r === "top" ? teg(gap("korsat", til, soz(savol.id, til)), til)
              : r === "tartib" ? savol.map((w) => teg(soz(w, til), til)).join(" ")
                : r === "ortiqcha" ? teg(gap("ortiqcha", til), til)
                  : r === "yoqoldi" ? teg(gap("yoqoldi", til), til)
                    : faol ? teg(soz(faol, til), til) : "";
          ayt(text, r === "ayt" && mik === "" ? () => tingla(savol.id, oyinRef.current) : null,
            r === "yordam" ? savol.kim : r === "buyruq" ? "teacher" : null);
        }}>🔊</button>}
    </div>
  </div>);
}

/** Fon rasmi bo'lmagan xonalar bezagi (CSS bilan chizilgan). */
function Bezak({ id }) {
  switch (id) {
    case "men": return <><i className="xb xb-devor-men" /><i className="xb xb-tokcha" style={{ top: "26%" }} /><i className="xb xb-tokcha" style={{ top: "49%" }} /><i className="xb xb-tokcha" style={{ top: "72%" }} /><i className="xb xb-gilam" style={{ top: "76%" }} /></>;
    case "havo": return <><i className="xb xb-osmon" /><i className="xb xb-maysa" style={{ top: "72%" }} /></>;
    default: return null;
  }
}
