import React, { useEffect, useRef, useState } from "react";
import { SAHNA } from "./sahnalar.jsx";
import { harakat, imoTanish, sahnaKorinish, qutiga, sahnaga } from "./harakatRules.js";

const ONIY = new Set(["bos", "ikki"]);
const foiz = (v) => `${(v * 100).toFixed(1)}%`;
/** Ko'rsatkich qo'l joyi (qutiga nisbatan): aylantirish markazi yoki olib borish boshi → nishon. */
function qolJoyi(S, k) {
  const st = {};
  if (S?.markaz) { const m = qutiga(S.markaz, k); st["--mx"] = foiz(m.x); st["--my"] = foiz(m.y); }
  if (S?.boshi && S?.nishon) {
    const b = qutiga(S.boshi, k), n = qutiga(S.nishon, k);
    st["--bx"] = foiz(b.x); st["--by"] = foiz(b.y); st["--nx"] = foiz(n.x); st["--ny"] = foiz(n.y);
  }
  return st;
}   // bir zumda bajariladigan harakatlar — sahna o'zi silliq o'ynaydi

/**
 * REV141: bitta harakat sahnasi. Bola barmog'i bilan harakatni bajaradi (bosish, surish, aylantirish, ushlab turish…),
 * sahna shunga qarab jonlanadi. demo — ustoz ko'rsatadi (qo'l belgisi harakatni bajaradi, bola tegsa ham o'zgarmaydi).
 * onTayyor — harakat bajarilib, sahna oxirigacha o'ynagach bir marta chaqiriladi. yordam — qo'l belgisi maslahat beradi.
 */
export default function HarakatSahna({ id, demo = false, faol = true, yordam = false, onTayyor, onDemo, onFaollik }) {
  const h = harakat(id);
  const S = SAHNA[id];
  const quti = useRef(null);
  const tanish = useRef(null);
  const [holat, setHolat] = useState({ a: 0, tayyor: false, joy: null });
  const kor = useRef(sahnaKorinish(400, 300));   // ko'rinadigan qism (telefonda chetlar qirqiladi)
  const maqsad = useRef(0);
  const aRef = useRef(0);
  const tayyorRef = useRef(false);
  const chaqirildi = useRef(false);
  const cb = useRef({});
  cb.current = { onTayyor, onDemo, onFaollik };

  // har yangi harakat (yoki demo/o'yin almashinuvi) — sahna boshidan
  useEffect(() => {
    maqsad.current = 0; aRef.current = 0; tayyorRef.current = false; chaqirildi.current = false;
    setHolat({ a: 0, tayyor: false, joy: null });
    const r = quti.current?.getBoundingClientRect?.() || { width: 400, height: 300 };
    const k = sahnaKorinish(r.width || 400, r.height || 300);
    kor.current = k;
    tanish.current = h ? imoTanish(h.imo, { w: r.width || 400, h: r.height || 300 },
      { markaz: qutiga(S?.markaz, k), boshi: qutiga(S?.boshi, k), nishon: qutiga(S?.nishon, k) }) : null;
  }, [id, demo, h, S]);

  // animatsiya: a (ko'rinadigan holat) maqsadga silliq yetadi; demo — vaqt bo'yicha
  useEffect(() => {
    let raf = 0;
    const bosh = performance.now();
    const DEMO_KUT = 700, DEMO_UZ = 2300;
    const loop = (now) => {
      let joy = null;
      if (demo) {
        const t = Math.max(0, Math.min(1, (now - bosh - DEMO_KUT) / DEMO_UZ));
        maqsad.current = t;
        if (t >= 1) tayyorRef.current = true;
        if (S?.boshi && S?.nishon) joy = { x: S.boshi.x + (S.nishon.x - S.boshi.x) * t, y: S.boshi.y + (S.nishon.y - S.boshi.y) * t };
      } else if (tanish.current) {
        const r = tanish.current.tick(now);
        if (!ONIY.has(h?.imo.tur)) maqsad.current = r.p;
        if (r.tayyor) tayyorRef.current = true;
        joy = sahnaga(tanish.current.joy, kor.current);
      }
      if (ONIY.has(h?.imo.tur) && tayyorRef.current && !demo) maqsad.current = 1;
      const tez = ONIY.has(h?.imo.tur) ? 0.07 : 0.22;
      const keyingi = aRef.current + (maqsad.current - aRef.current) * tez;
      aRef.current = Math.abs(maqsad.current - keyingi) < 0.004 ? maqsad.current : keyingi;
      const tamom = tayyorRef.current && aRef.current >= 0.995;
      setHolat((p) => (Math.abs(p.a - aRef.current) < 0.002 && p.tayyor === tamom && p.joy?.x === joy?.x && p.joy?.y === joy?.y ? p : { a: aRef.current, tayyor: tamom, joy }));
      if (tamom && !chaqirildi.current) {
        chaqirildi.current = true;
        setTimeout(() => { (demo ? cb.current.onDemo : cb.current.onTayyor)?.(); }, demo ? 900 : 1100);
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [demo, id, h, S]);

  if (!h || !S) return null;
  const nuqta = (e) => { const r = quti.current.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top, performance.now()]; };
  const qabul = faol && !demo && !tayyorRef.current;
  const down = (e) => { if (!qabul) return; try { e.currentTarget.setPointerCapture(e.pointerId); } catch { /* */ } cb.current.onFaollik?.(); tanish.current?.down(...nuqta(e)); };
  const move = (e) => { if (!qabul) return; tanish.current?.move(...nuqta(e)); };
  const up = (e) => { if (!qabul) return; tanish.current?.up(...nuqta(e)); };
  const imo = h.imo.tur === "sur" ? `sur-${h.imo.yon}` : h.imo.tur;
  return <div ref={quti} className={`hs-sahna ${demo ? "is-demo" : ""} ${holat.tayyor ? "is-tayyor" : ""}`}
    onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up} style={{ touchAction: "none" }}>
    <svg viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
      {S.C({ a: holat.a, tayyor: holat.tayyor, joy: holat.joy })}
    </svg>
    {(demo || (yordam && !holat.tayyor)) && <span className={`hs-qol hs-qol--${imo} ${demo ? "" : "is-yordam"}`}
      style={qolJoyi(S, kor.current)} aria-hidden="true">👆</span>}
    {!demo && h.imo.tur === "ushla" && !holat.tayyor && <span className="hs-halqa" style={{ "--p": holat.a }} aria-hidden="true" />}
    {!demo && h.imo.tur === "tez" && !holat.tayyor && holat.a > 0 && <span className="hs-chiziq" style={{ "--p": holat.a }} aria-hidden="true" />}
  </div>;
}
