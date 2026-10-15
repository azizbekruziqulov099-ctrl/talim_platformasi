import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useInterface } from "../interface/InterfacePreferences.jsx";
import { aralashKerak, aralashOqi } from "../speech/aralashOvoz.js";
import { RASMLAR } from "../kid/xonalar/rasmlar.js";
import { SOZLAR } from "../kid/xonalar/xonaLugat.js";
import { SahnaRasm } from "../kid/harakat/sahnalar.jsx";
import {
  BOSQICH_NOM, FAN, HOLAT, KUBOK, TIL, bosqichNomi, jamoaNomi, javon, pleyoffUstunlar, qolganVaqt, sanoqOlcham, yulduzlar,
} from "./chempionatRules.js";
import "../kid/harakat/harakat.css";

import "./chempionat.css";

const P = "/api/chempionat";
const RANGLAR = { red: "#E53935", blue: "#1E63D6", green: "#2EA44F", yellow: "#FFD21F", pink: "#FF7EB6", purple: "#8E44C9", black: "#222", white: "#FFFFFF" };

async function so(apiBase, path, token, body) {
  const url = `${String(apiBase).replace(/\/+$/, "")}${path}${body ? "" : `${path.includes("?") ? "&" : "?"}token=${encodeURIComponent(token)}`}`;
  const res = await fetch(url, {
    method: body ? "POST" : "GET", cache: "no-store",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: body ? JSON.stringify({ token, ...body }) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : data.detail?.message || `Server xatosi (${res.status})`);
  return data;
}

/** Ustoz ovozi: chet tildagi so'z qurilma ovozida (sifatli bo'lsa), qolgani serverdan. */
function useOvoz(apiBase) {
  const cur = useRef(null);
  const jim = useCallback(() => { try { cur.current?.pause(); } catch { /* */ } cur.current = null; }, []);
  useEffect(() => jim, [jim]);
  const ayt = useCallback((text) => {
    jim();
    const t = String(text || "").trim();
    if (!t) return;
    const url = (m) => `${String(apiBase).replace(/\/+$/, "")}/api/ovoz?k=133&${new URLSearchParams({ matn: m.slice(0, 600), jins: "qiz" })}`;
    try {
      if (aralashKerak(t)) {
        const ctl = aralashOqi(t, url, { rate: 0.85 });
        cur.current = { pause: () => ctl.stop() };
        return;
      }
      const a = new Audio(url(t));
      cur.current = a;
      a.play().catch(() => {});
    } catch { /* ovoz ixtiyoriy */ }
  }, [apiBase, jim]);
  return { ayt, jim };
}

const Rasm = ({ id }) => (RANGLAR[id]
  ? <span className="ch-rang" style={{ "--rang": RANGLAR[id] }} aria-hidden="true" />
  : RASMLAR[id] ? <img src={RASMLAR[id]} alt="" draggable="false" />
    : <span className="ch-emoji" aria-hidden="true">{SOZLAR[id]?.emoji || "⭐"}</span>);

const OY_UZ = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"];
const sana = (t, loc) => {
  try {
    const d = new Date(t);
    const hm = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
    if (loc !== "ru" && loc !== "en") return `${d.getDate()}-${OY_UZ[d.getMonth()]}, ${hm}`;
    return `${d.toLocaleDateString(loc, { day: "numeric", month: "long" })}, ${hm}`;
  } catch { return ""; }
};

/**
 * REV143: Bolalar ligasi — «Chempionlar ligasi» uslubidagi chempionatlar. Admin e'lon qiladi va jamoalarni tuzadi,
 * bolalar yoziladi va har tur o'z vaqtida o'ynaydi; guruh bosqichi → pley-off → final; kuboklar javoni.
 */
export default function Chempionat({ apiBase = "", token = "", onClose }) {
  const { t: T, locale } = useInterface();
  const izoh = locale === "ru" || locale === "en" ? locale : "uz";
  const [roy, setRoy] = useState(null);
  const [kod, setKod] = useState("");
  const [c, setC] = useState(null);
  const [oyin, setOyin] = useState(null);         // o'ynash ekrani
  const [xato, setXato] = useState("");
  const [band, setBand] = useState(false);
  const [yangi, setYangi] = useState(false);
  const ovoz = useOvoz(apiBase);
  const call = useCallback((path, body) => so(apiBase, path, token, body), [apiBase, token]);

  const royxatOl = useCallback(() => call(P).then(setRoy).catch((e) => setXato(e.message)), [call]);
  useEffect(() => { royxatOl(); }, [royxatOl]);
  const ochish = useCallback((k) => { setXato(""); setKod(k); setC(null); call(`${P}/${k}`).then(setC).catch((e) => setXato(e.message)); }, [call]);
  useEffect(() => {
    if (!kod || oyin) return undefined;
    const id = setInterval(() => { if (!document.hidden) call(`${P}/${kod}`).then(setC).catch(() => {}); }, 30000);
    return () => clearInterval(id);
  }, [kod, oyin, call]);

  const amal = async (path, body = {}) => {
    setBand(true); setXato("");
    try { setC(await call(`${P}/${kod}${path}`, body)); } catch (e) { setXato(e.message); } finally { setBand(false); }
  };
  const orqaga = () => { ovoz.jim(); if (oyin) { setOyin(null); ochish(kod); } else if (kod) { setKod(""); setC(null); royxatOl(); } else onClose?.(); };

  if (oyin) return <Oyin apiBase={apiBase} call={call} kod={kod} izoh={izoh} ovoz={ovoz} T={T} onChiq={orqaga} />;

  return <section className="ch-root">
    <div className="ch-bar">
      <button type="button" className="ch-back" onClick={orqaga} aria-label={T("Orqaga")}>⬅️</button>
      <b>🏆 {T("Bolalar ligasi")}</b>
    </div>
    {xato && <p className="ch-xato" role="alert">{xato}</p>}
    {!kod && <Bosh roy={roy} T={T} izoh={izoh} onOch={ochish} yangi={yangi} setYangi={setYangi}
      onYarat={async (body) => { setBand(true); setXato(""); try { const d = await call(P, body); setYangi(false); ochish(d.kod); } catch (e) { setXato(e.message); } finally { setBand(false); } }} band={band} />}
    {kod && !c && !xato && <p className="ch-muted" role="status">⏳ {T("Yuklanmoqda…")}</p>}
    {kod && c && <Tafsilot c={c} T={T} izoh={izoh} locale={locale} band={band} amal={amal} onOyna={() => setOyin(true)} />}
  </section>;
}

// ───────────────────────────── bosh sahifa ─────────────────────────────
function Bosh({ roy, T, izoh, onOch, yangi, setYangi, onYarat, band }) {
  if (!roy) return <p className="ch-muted" role="status">⏳ {T("Yuklanmoqda…")}</p>;
  const kub = javon(roy.kuboklar).filter((k) => k.kubok !== "ishtirok");
  const medal = roy.kuboklar.filter((k) => k.kubok === "ishtirok").length;
  const mos = (x) => roy.admin || x.qatnashaman || !roy.daraja || x.daraja === roy.daraja;
  const royxat = roy.chempionatlar.filter(mos);
  return <>
    <header className="ch-hero">
      <span className="ch-hero-kubok" aria-hidden="true">🏆</span>
      <div><h2>{T("Bolalar ligasi")}</h2><p>{T("Jamoang bilan bellash: so‘zlar, harakatlar va bilim. G‘oliblar kubok oladi!")}</p></div>
    </header>
    <section className="ch-javon" aria-label={T("Kubok javonim")}>
      <h3>🗄️ {T("Kubok javonim")}</h3>
      {kub.length || medal ? <div className="ch-javon-qator">
        {kub.map((k, i) => <figure key={`${k.kod}-${k.kubok}-${i}`} className={`ch-kubok is-${k.kubok}`} title={`${T(KUBOK[k.kubok]?.nom)} — ${k.nomi}`}>
          <span aria-hidden="true">{KUBOK[k.kubok]?.emoji}</span><figcaption>{k.nomi}</figcaption></figure>)}
        {medal > 0 && <figure className="ch-kubok is-ishtirok"><span aria-hidden="true">🎖️</span><figcaption>× {medal}</figcaption></figure>}
      </div> : <p className="ch-muted">{T("Hali kubok yo‘q. Chempionatga yozil va birinchi kubogingni yut!")}</p>}
    </section>
    {roy.admin && (yangi ? <YangiForma roy={roy} T={T} onYarat={onYarat} band={band} onBekor={() => setYangi(false)} />
      : <button type="button" className="ch-asosiy ch-yangi" onClick={() => setYangi(true)}>＋ {T("Yangi chempionat e’lon qilish")}</button>)}
    <h3 className="ch-sarlavha">⚽ {T("Chempionatlar")}</h3>
    {royxat.length ? <ul className="ch-list">{royxat.map((x) => <li key={x.kod}><Karta x={x} T={T} onOch={() => onOch(x.kod)} /></li>)}</ul>
      : <p className="ch-muted">{T("Hozircha chempionat yo‘q. Tez orada e’lon qilinadi!")}</p>}
  </>;
}

function Karta({ x, T, onOch }) {
  const h = HOLAT[x.holat] || HOLAT.royxat;
  return <button type="button" className={`ch-karta is-${x.holat}`} onClick={onOch}>
    <span className="ch-karta-belgi" aria-hidden="true">{x.holat === "tugadi" ? "🏁" : "🏆"}</span>
    <span className="ch-karta-asos">
      <b>{x.nomi}</b>
      <small>{h.emoji} {T(h.nom)}{x.holat === "davom" && x.bosqich ? ` · ${T(bosqichNomi(x.bosqich))}` : ""}</small>
      <small>👶 {T(x.daraja)} · {TIL[x.til]?.[0]} {T(TIL[x.til]?.[1] || x.til)} · {x.jamoa_hajmi > 1 ? `👥 ${x.jamoa_hajmi} ${T("kishilik jamoa")}` : `👤 ${T("Yakka")}`} · 🙋 {x.ishtirokchilar}</small>
    </span>
    {x.qatnashaman && <em className="ch-badge">{T("Qatnashaman")}</em>}
  </button>;
}

function YangiForma({ roy, T, onYarat, onBekor, band }) {
  const [f, setF] = useState({ nomi: "", izoh: "", daraja: "4-5 yosh", til: "en", fanlar: ["soz", "harakat", "bilim"], jamoa_hajmi: 5, tur_kun: 1, boshlanish_kun: 3 });
  const o = (k, v) => setF((x) => ({ ...x, [k]: v }));
  return <form className="ch-forma" onSubmit={(e) => { e.preventDefault(); onYarat(f); }}>
    <h3>🏆 {T("Yangi chempionat")}</h3>
    <label>{T("Nomi")}<input value={f.nomi} onChange={(e) => o("nomi", e.target.value)} maxLength={80} required minLength={3} placeholder={T("Masalan: Kuzgi bolalar ligasi")} /></label>
    <label>{T("Yosh guruhi")}<select value={f.daraja} onChange={(e) => o("daraja", e.target.value)}>{roy.darajalar.map((d) => <option key={d} value={d}>{T(d)}</option>)}</select></label>
    <label>{T("Til")}<select value={f.til} onChange={(e) => o("til", e.target.value)}>{roy.tillar.map((l) => <option key={l} value={l}>{TIL[l]?.[0]} {T(TIL[l]?.[1] || l)}</option>)}</select></label>
    <fieldset><legend>{T("Nima bilan bellashadi")}</legend>
      {Object.entries(FAN).map(([k, v]) => <label key={k} className="ch-check"><input type="checkbox" checked={f.fanlar.includes(k)}
        onChange={(e) => o("fanlar", e.target.checked ? [...f.fanlar, k] : f.fanlar.filter((x) => x !== k))} /> {v.emoji} {T(v.nom)}</label>)}
    </fieldset>
    <label>{T("Jamoa hajmi")}<select value={f.jamoa_hajmi} onChange={(e) => o("jamoa_hajmi", Number(e.target.value))}>
      {roy.hajmlar.map((h) => <option key={h} value={h}>{h === 1 ? `👤 ${T("Yakka (har bola o‘zi)")}` : `👥 ${h} ${T("kishilik jamoa")}`}</option>)}</select></label>
    <label>{T("Har tur necha kun ochiq")}<select value={f.tur_kun} onChange={(e) => o("tur_kun", Number(e.target.value))}>
      {[1, 2, 3, 7].map((d) => <option key={d} value={d}>{d} {T("kun")}</option>)}</select></label>
    <label>{T("Ro‘yxatdan o‘tish necha kun")}<select value={f.boshlanish_kun} onChange={(e) => o("boshlanish_kun", Number(e.target.value))}>
      {[0, 1, 2, 3, 5, 7, 14].map((d) => <option key={d} value={d}>{d ? `${d} ${T("kun")}` : T("Admin o‘zi boshlaydi")}</option>)}</select></label>
    <label>{T("Izoh (ixtiyoriy)")}<textarea value={f.izoh} onChange={(e) => o("izoh", e.target.value)} maxLength={300} rows={2} /></label>
    <p className="ch-muted">{T("Bolalar yoziladi, keyin «Jamoalarni tuzish»ni bosasiz. Boshlanish vaqti kelsa, jamoalar o‘zi tuziladi va chempionat o‘zi boshlanadi.")}</p>
    <div className="ch-qator"><button type="submit" className="ch-asosiy" disabled={band || !f.fanlar.length}>{T("E’lon qilish")}</button>
      <button type="button" className="ch-ikkinchi" onClick={onBekor}>{T("Bekor qilish")}</button></div>
  </form>;
}

// ───────────────────────────── chempionat sahifasi ─────────────────────────────
function Tafsilot({ c, T, izoh, locale, band, amal, onOyna }) {
  const jm = useMemo(() => Object.fromEntries(c.jamoalar.map((j) => [j.id, j])), [c.jamoalar]);
  const nom = (id) => (id == null ? T("Dam") : `${jm[id]?.emoji || ""} ${jamoaNomi(jm[id], izoh)}`);
  const h = HOLAT[c.holat] || HOLAT.royxat;
  const mening = c.mening_jamoam ? jm[c.mening_jamoam] : null;
  const myMatch = c.mening_oyinim ? c.uchrashuvlar.find((u) => u.id === c.mening_oyinim.uchrashuv) : null;
  return <div className="ch-tafsilot">
    <header className={`ch-sahna is-${c.holat}`}>
      <span className="ch-sahna-kubok" aria-hidden="true">{c.holat === "tugadi" ? "🏆" : "⚽"}</span>
      <div>
        <h2>{c.nomi}</h2>
        <p>{h.emoji} {T(h.nom)}{c.holat === "davom" ? ` · ${T(bosqichNomi(c.bosqich))}` : ""}</p>
        <p className="ch-teglar">
          <span>👶 {T(c.daraja)}</span><span>{TIL[c.til]?.[0]} {T(TIL[c.til]?.[1] || c.til)}</span>
          <span>{c.jamoa_hajmi > 1 ? `👥 ${c.jamoa_hajmi} ${T("kishilik jamoa")}` : `👤 ${T("Yakka")}`}</span>
          {c.fanlar.map((f) => <span key={f}>{FAN[f]?.emoji} {T(FAN[f]?.nom)}</span>)}
        </p>
        {c.izoh && <p className="ch-izoh">{c.izoh}</p>}
      </div>
    </header>

    {c.holat === "royxat" && <section className="ch-panel">
      <p>📅 {T("Boshlanish")}: <b>{sana(c.boshlanish, locale)}</b> ({qolganVaqt(c.boshlanish - c.server_now, T)})</p>
      <p>🙋 {T("Yozilganlar")}: <b>{c.ishtirokchilar}</b></p>
      {c.qatnashaman ? <><p className="ch-ok">✅ {T("Sen yozilding! Jamoalar tuzilgach, jamoang shu yerda ko‘rinadi.")}</p>
        <button type="button" className="ch-ikkinchi" disabled={band} onClick={() => amal("/chiq")}>{T("Ro‘yxatdan chiqish")}</button></>
        : <button type="button" className="ch-asosiy ch-katta" disabled={band} onClick={() => amal("/yozil")}>🙋 {T("Chempionatga yozilish")}</button>}
    </section>}

    {mening && c.holat !== "tugadi" && <section className="ch-mening">
      <h3>{mening.emoji} {c.jamoa_hajmi > 1 ? `${T("Mening jamoam")}: ${jamoaNomi(mening, izoh)}` : jamoaNomi(mening, izoh)}</h3>
      {c.jamoa_hajmi > 1 && <p className="ch-azolar">{mening.azolar.map((a) => <span key={a.user_id} className={a.men ? "is-men" : ""}>{a.ism}</span>)}</p>}
      {c.holat === "davom" && (c.mening_oyinim ? <div className="ch-oyin-karta">
        {myMatch && <p className="ch-vs"><b>{nom(myMatch.a)}</b> <i>⚔️</i> <b>{nom(myMatch.b)}</b></p>}
        {myMatch?.oynadi && <p className="ch-muted">{T("O‘ynab bo‘ldi")}: {Object.entries(myMatch.oynadi).map(([id, n]) => `${jm[id]?.emoji || ""} ${n}/${jm[id]?.azolar.length || 0}`).join(" · ")}</p>}
        {c.mening_oyinim.holat === "tugadi"
          ? <p className="ch-ok">✅ {T("Sen o‘ynab bo‘lding")}: <b>{c.mening_oyinim.ball}</b> {T("ball")}. {T("Natija tur tugaganda ochiladi.")}</p>
          : <button type="button" className="ch-asosiy ch-katta ch-play" onClick={onOyna}>▶ {T(c.mening_oyinim.holat === "davom" ? "Davom ettirish" : "O‘ynash")}</button>}
        <p className="ch-muted">⏳ {T("Tur tugashiga")}: {qolganVaqt(c.mening_oyinim.tugash - c.server_now, T)}</p>
      </div> : <p className="ch-muted">{c.keyingi_oyin ? `📅 ${T("Keyingi o‘yin")}: ${sana(c.keyingi_oyin, locale)}` : T("Jamoang bu bosqichda o‘ynamaydi. Natijalarni kuzat!")}</p>)}
    </section>}

    {c.admin && <AdminPanel c={c} T={T} izoh={izoh} band={band} amal={amal} />}

    {c.holat === "tugadi" && <Podium c={c} T={T} izoh={izoh} />}

    {c.guruhlar.length > 0 && <section className="ch-guruhlar">
      <h3>📊 {T(BOSQICH_NOM.guruh)}</h3>
      {c.guruhlar.map((g) => <GuruhJadval key={g.nomi} g={g} jm={jm} T={T} izoh={izoh} mening={c.mening_jamoam} ochiq={c.guruhlar.length > 1} />)}
    </section>}
    {c.holat !== "royxat" && c.holat !== "jamoa" && <Tor c={c} nom={nom} T={T} />}

    {c.holat === "jamoa" && !c.admin && <section className="ch-jamoalar">
      <h3>👥 {T("Jamoalar")}</h3>
      <div className="ch-jamoa-grid">{c.jamoalar.map((j) => <div key={j.id} className={`ch-jamoa ${j.id === c.mening_jamoam ? "is-men" : ""}`}>
        <b>{j.emoji} {jamoaNomi(j, izoh)}</b><small>{j.azolar.map((a) => a.ism).join(", ")}</small></div>)}</div>
      <p className="ch-muted">📅 {T("Boshlanish")}: {sana(c.boshlanish, locale)}</p>
    </section>}
  </div>;
}

function GuruhJadval({ g, jm, T, izoh, mening, ochiq }) {
  return <div className="ch-jadval-wrap">
    {ochiq && <h4>{T("Guruh")} {g.nomi}</h4>}
    <table className="ch-jadval">
      <thead><tr><th>#</th><th>{T("Jamoa")}</th><th title={T("O‘yin")}>O</th><th title={T("G‘alaba")}>G</th><th title={T("Durang")}>D</th><th title={T("Mag‘lubiyat")}>M</th><th title={T("Ballar farqi")}>±</th><th>{T("Ochko")}</th></tr></thead>
      <tbody>{g.jadval.map((r) => <tr key={r.jamoa_id} className={`${r.jamoa_id === mening ? "is-men" : ""} ${r.orin <= 2 ? "is-otadi" : ""}`}>
        <td>{r.orin}</td><td>{jm[r.jamoa_id]?.emoji} {jamoaNomi(jm[r.jamoa_id], izoh)}</td><td>{r.oyin}</td><td>{r.g}</td><td>{r.d}</td><td>{r.m}</td>
        <td>{r.farq > 0 ? `+${r.farq}` : r.farq}</td><td><b>{r.ochko}</b></td></tr>)}</tbody>
    </table>
  </div>;
}

function Tor({ c, nom, T }) {
  const { ustun, uchinchi } = pleyoffUstunlar(c.uchrashuvlar);
  if (!ustun.length) return null;
  const Juft = ({ u }) => <div className={`ch-juft is-${u.holat}`}>
    {[["a", u.a], ["b", u.b]].map(([s, id]) => <div key={s} className={`ch-juft-q ${u.golib != null && u.golib === id ? "is-golib" : ""}`}>
      <span>{nom(id)}</span>{u.holat === "tugadi" && u.b != null && <b>{u[`${s}_ball`]}</b>}</div>)}
  </div>;
  return <section className="ch-tor-wrap">
    <h3>🏟️ {T("Pley-off")}</h3>
    <div className="ch-tor">{ustun.map((s) => <div key={s.bosqich} className="ch-ustun">
      <h4>{T(bosqichNomi(s.bosqich))}</h4>
      {s.uchrashuvlar.map((u) => <Juft key={u.id} u={u} />)}
    </div>)}</div>
    {uchinchi && <div className="ch-uchinchi"><h4>🥉 {T(bosqichNomi("3-orin"))}</h4><Juft u={uchinchi} /></div>}
  </section>;
}

function Podium({ c, T, izoh }) {
  const ks = c.kuboklar || [];
  const jamoa = (k) => {
    const x = ks.find((y) => y.kubok === k);
    if (!x) return null;
    const j = c.jamoalar.find((jj) => (jj.nomi || jj.kalit) === x.jamoa);
    return j || { emoji: "🏅", nomi: x.jamoa };
  };
  const yulduz = ks.filter((k) => k.kubok === "yulduz");
  return <section className="ch-podium" aria-label={T("G‘oliblar")}>
    <h3>🎉 {T("G‘oliblar")}</h3>
    <div className="ch-podium-qator">
      {["kumush", "oltin", "bronza"].map((k) => { const j = jamoa(k); return j ? <div key={k} className={`ch-pog is-${k}`}>
        <span className="ch-pog-kubok" aria-hidden="true">{KUBOK[k].emoji}</span>
        <b>{j.emoji} {jamoaNomi(j, izoh)}</b><small>{T(KUBOK[k].nom)}</small></div> : null; })}
    </div>
    {yulduz.length > 0 && <p className="ch-yulduz">⭐ {T("Eng yaxshi o‘yinchi")}: <b>{yulduz.map((y) => y.ism).join(", ")}</b></p>}
    {c.mening_ballarim > 0 && <p className="ch-muted">{T("Sening jami balling")}: <b>{c.mening_ballarim}</b></p>}
  </section>;
}

function AdminPanel({ c, T, izoh, band, amal }) {
  const [nomlar, setNomlar] = useState({});
  return <section className="ch-admin">
    <h3>🛠️ {T("Admin boshqaruvi")}</h3>
    {c.holat === "royxat" && <div className="ch-qator">
      <button type="button" className="ch-asosiy" disabled={band || c.ishtirokchilar < 2} onClick={() => amal("/jamoalar")}>👥 {T("Jamoalarni tuzish")} ({c.ishtirokchilar})</button>
      <button type="button" className="ch-ikkinchi" disabled={band || c.ishtirokchilar < 2} onClick={() => amal("/boshla")}>▶ {T("Hozir boshlash")}</button>
    </div>}
    {c.holat === "jamoa" && <>
      <p className="ch-muted">{T("Bolani boshqa jamoaga o‘tkazish uchun uning yonidagi ro‘yxatdan jamoani tanlang. Jamoa nomini ham o‘zgartirishingiz mumkin.")}</p>
      <div className="ch-jamoa-grid">{c.jamoalar.map((j) => <div key={j.id} className="ch-jamoa is-admin">
        <div className="ch-qator">
          <span aria-hidden="true">{j.emoji}</span>
          <input value={nomlar[j.id] ?? jamoaNomi(j, izoh)} onChange={(e) => setNomlar((x) => ({ ...x, [j.id]: e.target.value }))} maxLength={40} aria-label={T("Jamoa nomi")} />
          {nomlar[j.id] != null && <button type="button" className="ch-kichik" disabled={band}
            onClick={() => { amal(`/jamoa/${j.id}`, { nomi: nomlar[j.id] }); setNomlar((x) => { const y = { ...x }; delete y[j.id]; return y; }); }}>💾</button>}
          <small>{j.azolar.length} 🙋</small>
        </div>
        <ul>{j.azolar.map((a) => <li key={a.user_id}><span>{a.ism}</span>
          <select value={j.id} disabled={band} aria-label={`${a.ism}: ${T("jamoa")}`} onChange={(e) => amal(`/jamoa/${e.target.value}`, { user_id: a.user_id })}>
            {c.jamoalar.map((x) => <option key={x.id} value={x.id}>{x.emoji} {jamoaNomi(x, izoh)}</option>)}</select></li>)}</ul>
      </div>)}</div>
      <div className="ch-qator">
        <button type="button" className="ch-asosiy" disabled={band} onClick={() => amal("/boshla")}>▶ {T("Chempionatni boshlash")}</button>
        <button type="button" className="ch-ikkinchi" disabled={band} onClick={() => amal("/jamoalar")}>🔀 {T("Qayta tuzish")}</button>
        <button type="button" className="ch-ikkinchi" disabled={band} onClick={() => amal("/royxat_och")}>📝 {T("Ro‘yxatni qayta ochish")}</button>
      </div>
    </>}
    {(c.holat === "royxat" || c.holat === "jamoa" || c.holat === "davom") && <button type="button" className="ch-xavf" disabled={band}
      onClick={() => { if (globalThis.confirm?.(T("Chempionat bekor qilinsinmi?"))) amal("/bekor"); }}>✖️ {T("Bekor qilish")}</button>}
  </section>;
}

// ───────────────────────────── o'yin ekrani ─────────────────────────────
function Oyin({ call, kod, izoh, ovoz, T, onChiq }) {
  const [st, setSt] = useState(null);
  const [fb, setFb] = useState(null);     // {tanlov, javob, togri}
  const [xato, setXato] = useState("");
  const band = useRef(false);
  const savolKey = st && !st.tugadi ? `${st.savol.i}` : "";

  useEffect(() => {
    call(`${P}/${kod}/oyna`, { izoh }).then(setSt).catch((e) => setXato(e.message));
  }, [call, kod, izoh]);
  useEffect(() => {
    if (st && !st.tugadi) ovoz.ayt(st.savol.ovoz);
    try { globalThis.document?.querySelector(".ch-oyin, .ch-yakun")?.scrollIntoView({ block: "start", behavior: "smooth" }); } catch { /* eski brauzer */ }
  }, [savolKey, st?.tugadi]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (st?.tugadi) ovoz.ayt(st.togri >= st.jami * 0.6 ? T("Barakalla! Jamoang uchun zo‘r o‘ynading!") : T("Yaxshi harakat! Jamoang senga rahmat aytadi!"));
  }, [st?.tugadi]); // eslint-disable-line react-hooks/exhaustive-deps

  const tanla = async (k) => {
    if (!st || st.tugadi || band.current) return;
    band.current = true;
    try {
      const d = await call(`${P}/${kod}/javob`, { i: st.savol.i, tanlov: String(k), izoh });
      if (d.natija) setFb({ tanlov: String(k), javob: String(d.natija.javob), togri: d.natija.togri });
      setTimeout(() => { setFb(null); setSt(d); band.current = false; }, d.natija ? 1300 : 0);
    } catch (e) { setXato(e.message); band.current = false; }
  };

  if (xato) return <section className="ch-root"><div className="ch-bar"><button type="button" className="ch-back" onClick={onChiq} aria-label={T("Orqaga")}>⬅️</button></div>
    <p className="ch-xato" role="alert">{xato}</p></section>;
  if (!st) return <section className="ch-root"><p className="ch-muted" role="status">⏳ {T("Yuklanmoqda…")}</p></section>;
  if (st.tugadi) {
    const y = yulduzlar(st.togri, st.jami);
    return <section className="ch-root ch-yakun" style={{ scrollMarginTop: 96 }}>
      <span className="ch-yakun-belgi" aria-hidden="true">{y >= 3 ? "🏆" : y === 2 ? "🎉" : "👏"}</span>
      <p className="ch-yakun-yulduz" aria-label={`${y}/3`}>{[1, 2, 3].map((k) => (k <= y ? "⭐" : "☆")).join("")}</p>
      <h2>{st.ball} {T("ball")}</h2>
      <p>{T("To‘g‘ri javoblar")}: {st.togri}/{st.jami}</p>
      <p className="ch-muted">{T("Ballaring jamoangga qo‘shildi. Natija tur tugaganda ochiladi.")}</p>
      <button type="button" className="ch-asosiy ch-katta" onClick={onChiq}>🏟️ {T("Chempionatga qaytish")}</button>
    </section>;
  }
  const q = st.savol;
  const sinf = (k) => (fb ? (String(k) === fb.javob ? "is-togri" : String(k) === fb.tanlov ? "is-xato" : "is-sonik") : "");
  return <section className="ch-root ch-oyin">
    <div className="ch-bar">
      <button type="button" className="ch-back" onClick={onChiq} aria-label={T("Orqaga")}>⬅️</button>
      <span className="ch-nuqtalar" aria-label={`${q.i + 1}/${q.jami}`}>{Array.from({ length: q.jami }, (_, i) => <i key={i} className={i < q.i ? "is-bor" : i === q.i ? "is-hozir" : ""} />)}</span>
      <span className="ch-ball">⭐ {st.ball}</span>
    </div>
    {!fb && <i key={`t${q.i}`} className="ch-vaqt" style={{ "--s": `${st.qolgan}s` }} onAnimationEnd={() => tanla("")} aria-hidden="true" />}
    <div className="ch-savol">
      {q.tur === "sana" && q.namuna && <span className="ch-namuna"><Rasm id={q.namuna} /></span>}
      <b dir="auto">{q.matn}</b>
      <button type="button" className="ch-qayta" onClick={() => ovoz.ayt(q.ovoz)} aria-label={T("Yana eshitish")}>🔊</button>
    </div>
    <div className={`ch-variantlar n${q.variantlar.length}`}>
      {q.variantlar.map((v) => <button key={v.k} type="button" className={`ch-variant ${sinf(v.k)}`} onClick={() => tanla(v.k)} disabled={Boolean(fb)}
        aria-label={v.n ? String(v.n) : v.soz ? (SOZLAR[v.soz]?.w?.[izoh] || v.soz) : v.harakat}>
        {v.harakat ? <SahnaRasm id={v.harakat} />
          : v.n ? <span className="ch-sanoq" style={{ "--w": `${sanoqOlcham(Math.max(...q.variantlar.map((x) => x.n || 0)))}%` }}>{Array.from({ length: v.n }, (_, i) => <span key={i}><Rasm id={v.soz} /></span>)}</span>
            : <Rasm id={v.soz} />}
      </button>)}
    </div>
  </section>;
}
