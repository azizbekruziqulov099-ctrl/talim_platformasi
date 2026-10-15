import React, { useEffect, useRef, useState } from "react";
import { uiText as __kbUi } from "../interface/interfaceRuntime.js";
import { gameLink, normalizeGameCode } from "./gameRules.js";
import { MEDALS, TOURNAMENT_STATES, countdownText, formatPoints, roundMarks } from "./turnirRules.js";
import { jamoaNomi } from "../chempionat/chempionatRules.js";
import { useInterface } from "../interface/InterfacePreferences.jsx";

const ROUNDS = [3, 5, 7, 9];
const STARTS = [{ kod: 5, nomi: "5 daqiqadan keyin" }, { kod: 15, nomi: "15 daqiqa" }, { kod: 60, nomi: "1 soat" }, { kod: 1440, nomi: "Ertaga" }];

/** REV90: turnirlar ro'yxati — chempionatlar (hammaga ochiq), mening turnirlarim, yaratish va kod bilan qo'shilish. */
export function TournamentList({ call, P, title, onOpen, onBack }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ nomi: "", nazorat: "5+0", turlar: 5, boshlanish_daqiqa: 15, ochiq: false, izoh: "", jamoa_hajmi: 0 });
  const [joinCode, setJoinCode] = useState("");
  useEffect(() => { call(`${P}/turnir`).then(setData).catch((e) => setError(e.message)); }, [call, P]);

  const create = async (e) => {
    e.preventDefault(); setBusy(true); setError("");
    try { const d = await call(`${P}/turnir`, form); onOpen(d.kod); } catch (err) { setError(err.message); } finally { setBusy(false); }
  };
  const row = (t) => {
    const st = TOURNAMENT_STATES[t.holat] || TOURNAMENT_STATES.royxat;
    return <li key={t.kod}><button type="button" className="tr-item" onClick={() => onOpen(t.kod)}>
      <span className="tr-item-emoji" aria-hidden="true">{t.jamoa_hajmi ? "👥" : t.ochiq ? "🏆" : "🎯"}</span>
      <span className="tr-item-main"><b>{t.nomi}</b>
        <small>{st.emoji} {__kbUi(st.nomi)}{t.jamoa_hajmi ? ` · 👥 ${__kbUi("Jamoaviy liga")}` : ""} · {__kbUi(t.nazorat_nomi)} · {t.turlar} {__kbUi("tur")} · 👥 {t.ishtirokchilar}</small></span>
      {t.qatnashaman && <em className="tr-badge">{__kbUi("Qatnashaman")}</em>}
    </button></li>;
  };
  return <div className="tr-root">
    <button type="button" className="sh-back" onClick={onBack}>← {__kbUi("Orqaga")}</button>
    <header className="sh-hero"><div className="sh-hero-icon" aria-hidden="true">🏆</div>
      <div><h2>{__kbUi(`${title} turnirlari`)}</h2><p>{__kbUi("Chempionatlar, sinf va to‘garak turnirlari — har turda yangi raqib, oxirida g‘oliblar.")}</p></div></header>
    <form className="sh-join" onSubmit={(e) => { e.preventDefault(); if (joinCode.length === 6) onOpen(joinCode); }}>
      <input value={joinCode} onChange={(e) => setJoinCode(normalizeGameCode(e.target.value))} placeholder="T12345" maxLength={6} aria-label={__kbUi("Turnir kodi")} />
      <button type="submit" className="sh-secondary" disabled={joinCode.length < 6}>{__kbUi("Turnirni ochish")}</button>
    </form>
    {!data && !error && <p className="sh-muted" role="status">{__kbUi("Yuklanmoqda…")}</p>}
    {data && <>
      <h3 className="sh-section-title">🏆 {__kbUi("Chempionatlar")}</h3>
      {data.ochiq.length ? <ul className="tr-list">{data.ochiq.map(row)}</ul> : <p className="sh-muted">{__kbUi("Hozircha e’lon qilingan chempionat yo‘q.")}</p>}
      <h3 className="sh-section-title">🎯 {__kbUi("Mening turnirlarim")}</h3>
      {data.meniki.length ? <ul className="tr-list">{data.meniki.map(row)}</ul> : <p className="sh-muted">{__kbUi("Siz hali turnirda qatnashmagansiz. Sinfdoshlaringiz uchun turnir yarating!")}</p>}
    </>}
    {!creating ? <button type="button" className="sh-primary tr-create-btn" onClick={() => setCreating(true)}>➕ {__kbUi("Turnir yaratish")}</button>
      : <form className="sh-card tr-form" onSubmit={create}>
        <h3>➕ {__kbUi("Yangi turnir")}</h3>
        <label>{__kbUi("Nomi")}<input required minLength={3} maxLength={60} value={form.nomi} onChange={(e) => setForm({ ...form, nomi: e.target.value })} placeholder={__kbUi("Masalan: 3-«A» sinf turniri")} /></label>
        <div className="tr-field"><span>{__kbUi("Vaqt nazorati")}</span><div className="sh-colors">
          {(data?.nazoratlar || []).map((c) => <button key={c.kod} type="button" className={form.nazorat === c.kod ? "is-on" : ""} onClick={() => setForm({ ...form, nazorat: c.kod })}>{__kbUi(c.nomi)}</button>)}</div></div>
        <div className="tr-field"><span>{__kbUi("Turlar soni")}</span><div className="sh-colors">
          {ROUNDS.map((n) => <button key={n} type="button" className={form.turlar === n ? "is-on" : ""} onClick={() => setForm({ ...form, turlar: n })}>{n}</button>)}</div></div>
        <div className="tr-field"><span>{__kbUi("Boshlanishi")}</span><div className="sh-colors">
          {STARTS.map((s) => <button key={s.kod} type="button" className={form.boshlanish_daqiqa === s.kod ? "is-on" : ""} onClick={() => setForm({ ...form, boshlanish_daqiqa: s.kod })}>{__kbUi(s.nomi)}</button>)}</div></div>
        <label>{__kbUi("Izoh (ixtiyoriy)")}<input maxLength={240} value={form.izoh} onChange={(e) => setForm({ ...form, izoh: e.target.value })} placeholder={__kbUi("Masalan: g‘olibga sovg‘a bor!")} /></label>
        {data?.admin && <label className="tr-check"><input type="checkbox" checked={form.ochiq} onChange={(e) => setForm({ ...form, ochiq: e.target.checked })} /> {__kbUi("Hammaga ochiq chempionat (ro‘yxatda hamma ko‘radi)")}</label>}
        {data?.admin && <div className="tr-field"><span>{__kbUi("Format")}</span><div className="sh-colors">
          {[0, 2, 3, 4, 5].map((n) => <button key={n} type="button" className={form.jamoa_hajmi === n ? "is-on" : ""} onClick={() => setForm({ ...form, jamoa_hajmi: n, ochiq: n ? true : form.ochiq, qatnashaman: !n })}>
            {n ? `👥 ${n} ${__kbUi("kishilik jamoa")}` : `👤 ${__kbUi("Yakka")}`}</button>)}</div></div>}
        {form.jamoa_hajmi > 0 && <p className="sh-muted">{__kbUi("Jamoaviy liga: boshlanishda o‘yinchilar reyting bo‘yicha teng kuchli jamoalarga bo‘linadi. Jamoalar har kim har kim bilan uchrashadi, 1-doska 1-doska bilan o‘ynaydi; uchrashuv g‘olibi — doskalarda ko‘p ochko olgan jamoa.")}</p>}
        <p className="sh-muted">{__kbUi("Hamma yig‘ilsa, «Boshlash» tugmasi bilan vaqtidan oldin ham boshlash mumkin.")}</p>
        <div className="sh-row"><button type="submit" className="sh-primary" disabled={busy}>{__kbUi("Yaratish")}</button>
          <button type="button" className="sh-secondary" onClick={() => setCreating(false)}>{__kbUi("Bekor qilish")}</button></div>
      </form>}
    {error && <p className="sh-note">{__kbUi(error)}</p>}
  </div>;
}

/** REV90: bitta turnir — ro'yxat, joriy tur juftlari, jadval, g'oliblar. O'yinim boshlansa o'zi ochiladi. */
export function TournamentView({ call, P, game, title, tkod, onOpenGame, onBack, onMissing, autoOpened }) {
  const { locale } = useInterface();
  const [t, setT] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  const [, setTick] = useState(0);
  const offset = useRef(0);
  const ownRef = useRef(new Set());
  const opened = autoOpened || ownRef;
  useEffect(() => {
    let stop = false;
    const load = async () => {
      try {
        const sent = Date.now();
        const d = await call(`${P}/turnir/${tkod}`);
        if (stop) return;
        offset.current = d.server_now - Math.round((sent + Date.now()) / 2);
        setT(d); setError("");
      } catch (e) {
        if (stop) return;
        if (/topilmadi/i.test(e.message) && onMissing) { onMissing(); return; }
        setError(e.message);
      }
    };
    load();
    // REV130: sahifa yashirin bo'lsa yoki oldingi so'rov hali qaytmagan bo'lsa — yangi so'rov yuborilmaydi
    // (sekin internetda so'rovlar to'planib, ilova qotib qolmasin; serverga ham ortiqcha yuk tushmasin).
    const band = { v: false };
    const id = setInterval(() => {
      if (band.v || globalThis.document?.hidden) return;
      band.v = true;
      Promise.resolve(load()).finally(() => { band.v = false; });
    }, 2500);
    const tick = setInterval(() => setTick((x) => x + 1), 1000);
    return () => { stop = true; clearInterval(id); clearInterval(tick); };
  }, [call, P, tkod]); // eslint-disable-line react-hooks/exhaustive-deps
  // Mening o'yinim boshlandi — o'zi ochiladi (har o'yin uchun bir marta).
  useEffect(() => {
    if (t?.mening_oyinim && !opened.current.has(t.mening_oyinim)) { opened.current.add(t.mening_oyinim); onOpenGame(t.mening_oyinim); }
  }, [t?.mening_oyinim]); // eslint-disable-line react-hooks/exhaustive-deps

  const act = (path) => async () => {
    setBusy(true); setError("");
    try { setT(await call(`${P}/turnir/${tkod}/${path}`, {})); } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const share = async () => {
    const link = gameLink(window.location.origin, game, tkod);
    try { if (navigator.share) { await navigator.share({ title: t?.nomi || title, text: `${t?.nomi || title} — turnirga qo'shiling! Kod: ${tkod}`, url: link }); return; } } catch { /* bekor */ }
    try { await navigator.clipboard.writeText(link); setNote("Havola nusxalandi ✓"); } catch { setNote(link); }
  };

  if (!t) return <div className="tr-root"><button type="button" className="sh-back" onClick={onBack}>← {__kbUi("Turnirlar")}</button>
    <p className="sh-muted" role="status">{error ? __kbUi(error) : __kbUi("Yuklanmoqda…")}</p></div>;

  const st = TOURNAMENT_STATES[t.holat] || TOURNAMENT_STATES.royxat;
  const now = Date.now() + offset.current;
  const myRow = t.jadval.find((r) => r.men);
  const jm = Object.fromEntries((t.jamoalar || []).map((j) => [j.id, j]));
  const jNom = (id) => (jm[id] ? `${jm[id].emoji} ${jamoaNomi(jm[id], locale)}` : "");
  const myTeam = t.mening_jamoam ? jm[t.mening_jamoam] : null;
  return <div className="tr-root">
    <button type="button" className="sh-back" onClick={onBack}>← {__kbUi("Turnirlar")}</button>
    <header className="tr-head">
      <span className="tr-head-emoji" aria-hidden="true">{t.ochiq ? "🏆" : "🎯"}</span>
      <div><h2>{t.nomi}</h2>
        <p className="sh-muted">{st.emoji} {__kbUi(st.nomi)}{t.jamoa_hajmi ? ` · 👥 ${__kbUi("Jamoaviy liga")}` : ""} · {__kbUi(t.nazorat_nomi)} · {t.turlar} {__kbUi("tur")} · 👥 {t.ishtirokchilar}/{t.max_ishtirokchi}</p>
        {t.izoh && <p className="tr-note">{t.izoh}</p>}</div>
    </header>

    {t.holat === "royxat" && <div className="sh-card tr-wait">
      <p className="tr-count">⏳ {__kbUi("Boshlanishiga")}: <b>{countdownText(t.boshlanish, now)}</b></p>
      <div className="sh-bigcode">{t.kod}</div>
      <div className="sh-row">
        {t.qatnashaman
          ? <button type="button" className="sh-secondary" disabled={busy} onClick={act("chiq")}>{__kbUi("Ro‘yxatdan chiqish")}</button>
          : <button type="button" className="sh-primary" disabled={busy} onClick={act("qoshil")}>✋ {__kbUi("Qatnashaman")}</button>}
        <button type="button" className="sh-secondary" onClick={share}>🔗 {__kbUi("Taklif qilish")}</button>
        {t.yaratuvchi && <button type="button" className="sh-primary" disabled={busy || t.ishtirokchilar < 2} onClick={act("boshla")}>▶ {__kbUi("Hozir boshlash")}</button>}
      </div>
      <p className="sh-muted">{__kbUi("Vaqt kelganda 1-tur o‘zi boshlanadi va o‘yiningiz o‘zi ochiladi. Shu sahifani ochiq qoldiring.")}</p>
    </div>}

    {myTeam && t.holat !== "tugadi" && <div className="sh-card tr-team-me">
      <h3>{myTeam.emoji} {__kbUi("Mening jamoam")}: {jamoaNomi(myTeam, locale)}</h3>
      <p className="tr-team-members">{myTeam.azolar.map((a, i) => <span key={a.user_id} className={a.men ? "is-me" : ""}>{i + 1}. {a.ism}</span>)}</p>
    </div>}
    {t.holat === "davom" && <div className="sh-card">
      <h3>⚔️ {t.joriy_tur}-{__kbUi("tur")} / {t.turlar}</h3>
      {t.mening_oyinim && <button type="button" className="sh-primary" onClick={() => onOpenGame(t.mening_oyinim)}>▶ {__kbUi("O‘yinimga o‘tish")}</button>}
      {t.dam_olaman && <p className="tr-note">☕ {__kbUi("Bu turda siz dam olasiz va 1 ochko olasiz. Keyingi tur o‘zi boshlanadi.")}</p>}
      {!t.mening_oyinim && !t.dam_olaman && t.qatnashaman && <p className="sh-muted">⏳ {__kbUi("O‘yiningiz tugadi. Boshqalar tugatishi bilan keyingi tur boshlanadi.")}</p>}
      <ul className="tr-pairs">{t.juftlar.map((j, i) => <li key={j.kod} className={j.men ? "is-me" : ""}>
        <span className="tr-board">{i + 1}</span><b>⚪ {j.oq_jamoa ? <small className="tr-team-tag">{jm[j.oq_jamoa]?.emoji}</small> : null}{j.oq}</b><em>{j.natija}</em><b>⚫ {j.qora_jamoa ? <small className="tr-team-tag">{jm[j.qora_jamoa]?.emoji}</small> : null}{j.qora}</b></li>)}</ul>
      {t.qatnashaman && <button type="button" className="sh-secondary tr-leave" disabled={busy} onClick={act("chiq")}>{__kbUi("Turnirdan chiqish")}</button>}
    </div>}

    {t.holat === "tugadi" && <div className="sh-card tr-podium">
      <h3>🏁 {__kbUi("Turnir tugadi!")}</h3>
      {t.golib_jamoalar ? <ol>{t.golib_jamoalar.map((g, i) => <li key={g.jamoa_id}><span>{["🏆", "🥈", "🥉"][i]}</span><b>{jNom(g.jamoa_id)}</b><em>{formatPoints(g.ochko)}</em></li>)}</ol>
        : <ol>{(t.golib || []).map((g, i) => <li key={g.orin}><span>{MEDALS[i]}</span><b>{g.ism}</b><em>{formatPoints(g.ochko)}</em></li>)}</ol>}
      {myRow && <p className="tr-note">{myRow.orin <= 3 ? `${MEDALS[myRow.orin - 1]} ` : ""}{__kbUi("Sizning o‘rningiz")}: <b>{myRow.orin}</b> · {formatPoints(myRow.ochko)} {__kbUi("ochko")}</p>}
    </div>}
    {t.holat === "bekor" && <p className="sh-note">{__kbUi("Ishtirokchilar yetarli bo‘lmagani uchun turnir bekor qilindi.")}</p>}

    {t.jamoa_jadval && <div className="tr-table-wrap">
      <h3 className="sh-section-title">👥 {__kbUi("Jamoalar jadvali")}</h3>
      <table className="tr-table">
        <thead><tr><th>#</th><th>{__kbUi("Jamoa")}</th>{roundMarks({}, t.turlar).map((_, i) => <th key={i}>{i + 1}</th>)}<th>{__kbUi("Ochko")}</th><th title={__kbUi("Doskalarda olingan ochkolar")}>{__kbUi("Doska")}</th></tr></thead>
        <tbody>{t.jamoa_jadval.map((r) => <tr key={r.jamoa_id} className={r.jamoa_id === t.mening_jamoam ? "is-me" : ""}>
          <td>{t.holat === "tugadi" && r.orin <= 3 ? ["🏆", "🥈", "🥉"][r.orin - 1] : r.orin}</td>
          <td className="tr-name">{jNom(r.jamoa_id)}<small>{(jm[r.jamoa_id]?.azolar || []).map((a) => a.ism).join(", ")}</small></td>
          {roundMarks({}, t.turlar).map((_, i) => { const m = r.natijalar[String(i + 1)]; const k = m ? m.split(":")[0] : ""; return <td key={i}
            className={`tr-mark is-${k === "1" ? "win" : k === "0" ? "loss" : k === "½" ? "draw" : k === "dam" ? "bye" : "none"}`} title={m && m.includes(":") ? m.split(":")[1] : ""}>{k === "dam" ? "☕" : k}</td>; })}
          <td><b>{formatPoints(r.ochko)}</b></td><td>{formatPoints(r.doska)}</td>
        </tr>)}</tbody>
      </table>
    </div>}
    {t.jadval.length > 0 && <div className="tr-table-wrap">
      <table className="tr-table">
        <thead><tr><th>#</th><th>{__kbUi("O‘yinchi")}</th>{roundMarks({}, t.turlar).map((_, i) => <th key={i}>{i + 1}</th>)}<th>{__kbUi("Ochko")}</th><th title={__kbUi("Buxgolts — raqiblar ochkolari yig‘indisi")}>{__kbUi("Bux.")}</th></tr></thead>
        <tbody>{t.jadval.map((r) => <tr key={r.user_id} className={`${r.men ? "is-me" : ""} ${r.chiqdi ? "is-out" : ""}`}>
          <td>{t.holat === "tugadi" && r.orin <= 3 ? MEDALS[r.orin - 1] : r.orin}</td>
          <td className="tr-name">{r.ism}<small>{r.reyting}</small></td>
          {roundMarks(r.natijalar, t.turlar).map((m, i) => <td key={i} className={`tr-mark is-${m === "1" ? "win" : m === "0" ? "loss" : m === "½" ? "draw" : m === "dam" ? "bye" : "none"}`}>{m === "dam" ? "☕" : m}</td>)}
          <td><b>{formatPoints(r.ochko)}</b></td><td>{formatPoints(r.buxgolts)}</td>
        </tr>)}</tbody>
      </table>
    </div>}
    {(error || note) && <p className="sh-note">{__kbUi(error || note)}</p>}
  </div>;
}
