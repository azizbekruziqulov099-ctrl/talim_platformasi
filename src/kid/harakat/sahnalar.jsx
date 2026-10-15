import React from "react";
import { RASMLAR } from "../xonalar/rasmlar.js";
import { HR } from "./rasmlar.js";

// REV144: harakat sahnalari — rassom chizgan rasmlar (fon + harakatlanuvchi qismlar), SVG 400×300 ichida.
// Har sahna a (0..1 — harakat qanchalik bajarilgani, silliqlangan) va tayyor (bajarildi) bilan chiziladi:
// eshik ochiladi, to'p darvozaga uchadi, mashina yo'l bo'ylab yuradi, shar kattalashadi…

const lerp = (a, b, t) => a + (b - a) * t;
const cl = (t) => Math.max(0, Math.min(1, t));
const ease = (t) => (t < 0.5 ? 2 * t * t : 1 - ((-2 * t + 2) ** 2) / 2);

/** Fon: butun sahnani qoplaydi. */
const Fon = ({ n, ...rest }) => <image href={HR[n].src} x="0" y="0" width="400" height="300" preserveAspectRatio="xMidYMid slice" {...rest} />;
/** Sprayt: cx — markaz, by — pastki chegara, h — balandlik (kenglik rasm nisbatidan). */
function Sp({ n, cx, by, h, op = 1, rot = 0, sx = 1, sy = 1, ox = 0.5, oy = 0.5, style }) {
  const r = HR[n];
  if (!r) return null;
  const w = (h * r.w) / r.h;
  const x = cx - w / 2, y = by - h;
  const px = x + w * ox, py = y + h * oy;
  const tf = rot || sx !== 1 || sy !== 1 ? `translate(${px} ${py}) rotate(${rot}) scale(${sx} ${sy}) translate(${-px} ${-py})` : undefined;
  return <image href={r.src} x={x} y={y} width={w} height={h} opacity={op} transform={tf} style={style} />;
}
const Soya = ({ cx, cy, rx, op = 0.22 }) => <ellipse cx={cx} cy={cy} rx={rx} ry={rx * 0.22} fill="#000" opacity={op} />;

function Konfetti() {
  return <g className="hs-konfetti">{Array.from({ length: 18 }, (_, i) => <rect key={i} x={20 + (i * 53) % 360} y={-10 - (i * 37) % 60} width="8" height="12" rx="2"
    fill={["#FF6B8A", "#FFC542", "#4CC6A1", "#5B8DEF", "#B76DF2"][i % 5]} style={{ "--d": `${(i % 6) * 0.08}s`, "--r": `${(i * 47) % 360}deg` }} />)}</g>;
}
const Yulduzcha = ({ x, y, s = 1 }) => <path className="hs-yulduzcha" transform={`translate(${x} ${y}) scale(${s})`}
  d="M0 -14 L4 -4 L14 -4 L6 3 L9 13 L0 7 L-9 13 L-6 3 L-14 -4 L-4 -4Z" fill="#FFD84A" stroke="#E0A800" strokeWidth="1.5" />;

// ── uy ──
function Eshik({ a, tayyor, yop }) {
  const t = yop ? 1 - a : a;                       // ochiqlik
  const h = 262, w = (h * HR.eshik.w) / HR.eshik.h, x0 = 200 - w / 2;
  return <g>
    <Fon n="fon_och" />
    <rect width="400" height="300" fill="#2b1a0a" opacity={0.18 * (1 - t)} />
    <Sp n="mushuk" cx={200} by={292} h={262} op={cl(t * 1.6 - 0.2)} />
    <g transform={`translate(${x0} 0) scale(${1 - 0.86 * t} 1) translate(${-x0} 0)`} opacity={t > 0.93 ? (1 - t) * 14 : 1}>
      <image href={HR.eshik.src} x={x0} y={292 - h} width={w} height={h} />
    </g>
    {tayyor && !yop && <Yulduzcha x={300} y={70} />}
  </g>;
}
function Chiroq({ a, tayyor, ochir }) {
  const on = ochir ? 1 - a : a;
  return <g>
    <Fon n="fon_yoq" />
    <rect width="400" height="300" fill="#0b1236" opacity={0.5 * (1 - on)} />
    <rect width="400" height="300" fill="#ffd36a" opacity={0.14 * on} />
    <Sp n="nur" cx={288} by={235} h={235} op={on * 0.9} style={{ mixBlendMode: "screen" }} />
    <Sp n="chiroq" cx={292} by={294} h={150} />
    <Sp n="tugma0" cx={115} by={205} h={112} op={1 - on} />
    <Sp n="tugma1" cx={115} by={185} h={64} op={on} />
    {tayyor && on > 0.5 && <Yulduzcha x={150} y={60} />}
  </g>;
}
// ── hovli ──
function Tep({ a, tayyor }) {
  const t = ease(a);
  return <g>
    <Fon n="fon_tep" />
    <Soya cx={lerp(200, 214, t)} cy={lerp(290, 128, t)} rx={lerp(36, 12, t)} op={0.25 * (1 - t)} />
    <Sp n="top" cx={lerp(200, 214, t)} by={lerp(292, 118, t) - Math.sin(Math.PI * t) * 40} h={lerp(84, 26, t)} rot={t * 720} />
    {tayyor && <Konfetti />}
  </g>;
}
function Ot({ a, tayyor }) {
  const t = ease(a);
  // savat fonning o'zida (o'ng-yuqori); to'r sprayti ustidan qo'yiladi — to'p to'r ichidan o'tgandek ko'rinadi
  const x = lerp(110, 313, t), y = lerp(288, tayyor ? 112 : 84, t) - Math.sin(Math.PI * t) * 70;
  return <g>
    <Fon n="fon_ot" />
    <Sp n="top2" cx={x} by={y} h={lerp(72, 34, t)} rot={t * 540} />
    <Sp n="tor" cx={313} by={113} h={87} />
    {tayyor && <Konfetti />}
  </g>;
}
function Sakra({ a, tayyor }) {
  const k = Math.sin(Math.PI * a);
  return <g>
    <Fon n="fon_sakra" />
    <Soya cx={200} cy={290} rx={lerp(48, 26, k)} />
    <Sp n="quyon" cx={200} by={290 - k * 120} h={172} sy={1 - 0.08 * Math.sin(2 * Math.PI * a)} oy={1} />
    {tayyor && <Yulduzcha x={290} y={70} />}
  </g>;
}
function Yugur({ a, tayyor }) {
  const x = lerp(100, 300, a);
  const bob = Math.abs(Math.sin(a * Math.PI * 9)) * 12;
  return <g>
    <Fon n="fon_yugur" />
    <Soya cx={x} cy={286} rx={34} />
    <Sp n="bola1" cx={x} by={286 - bob} h={150} rot={Math.sin(a * Math.PI * 9) * 4} oy={1} />
    {tayyor && <Konfetti />}
  </g>;
}
// ── yo'l ──
function Hayda({ a, tayyor }) {
  const pan = -lerp(0, 224, ease(a));
  const bob = Math.sin(a * Math.PI * 16) * 1.2;
  return <g>
    <image href={HR.fon_hayda.src} x={pan} y="0" width="624" height="300" preserveAspectRatio="none" />
    <Sp n="mashina" cx={lerp(140, 230, ease(a))} by={232 + bob} h={96} />
    {tayyor && <Yulduzcha x={330} y={60} />}
  </g>;
}
function Rul({ a, tayyor }) {
  const k = Math.sin(Math.PI * a);
  return <g transform={`translate(200 150) rotate(${-5 * k}) scale(${1 + 0.13 * k}) translate(-200 -150)`}>
    <Fon n="fon_bura" />
    <Fon n="fon_burilish" opacity={ease(a)} />
    {tayyor && <Yulduzcha x={330} y={50} />}
  </g>;
}
function Toxta({ a, tayyor }) {
  const t = ease(a);
  return <g>
    <Fon n="fon_toxta" />
    <Sp n="svetofor_y" cx={318} by={210} h={140} op={1 - t} />
    <Sp n="svetofor_q" cx={282} by={262} h={150} op={t} />
    <g className={a < 0.02 ? "hs-titra" : undefined}><Sp n="mashina2" cx={lerp(120, 150, t)} by={292} h={110} /></g>
    {tayyor && <Yulduzcha x={200} y={50} />}
  </g>;
}
function Velik({ a, tayyor }) {
  const x = lerp(105, 295, a);
  return <g>
    <Fon n="fon_velik" />
    <Soya cx={x} cy={288} rx={46} />
    <Sp n="velik1" cx={x} by={288 - Math.abs(Math.sin(a * Math.PI * 10)) * 3} h={150} />
    {tayyor && <Konfetti />}
  </g>;
}
// ── bayram ──
function Shar({ a, tayyor, yor }) {
  if (yor) {
    const portla = cl((a - 0.3) / 0.7);
    return <g>
      <Fon n="fon_bayram" />
      {portla < 0.15 && <Sp n="shar" cx={200} by={262} h={205} sx={1 + 0.06 * Math.sin(a * 40)} sy={1 + 0.06 * Math.sin(a * 40)} />}
      {portla > 0 && <Sp n="portlash" cx={200} by={270} h={lerp(140, 250, portla)} op={portla < 0.85 ? 1 : (1 - portla) * 6.6} />}
      {tayyor && <Konfetti />}
    </g>;
  }
  const h = lerp(46, 190, ease(a));
  return <g>
    <Fon n="fon_bayram" />
    <Sp n="nasos_bola" cx={140} by={292} h={200} />
    <Sp n="shar" cx={254} by={260} h={h * 0.95} rot={Math.sin(a * 12) * 3} oy={1} />
    {tayyor && <Yulduzcha x={330} y={50} />}
  </g>;
}
function Qarsak({ a, tayyor }) {
  const t = ease(a);
  return <g>
    <Fon n="fon_bayram" />
    <Sp n="qarsak_chap" cx={lerp(128, 168, t)} by={295} h={195} />
    <Sp n="qarsak_ong" cx={lerp(272, 232, t)} by={295} h={195} />
    {tayyor && <><Yulduzcha x={200} y={120} s={1.4} /><Yulduzcha x={170} y={95} s={0.8} /><Yulduzcha x={232} y={95} s={0.8} /></>}
  </g>;
}
function Raqs({ a, tayyor }) {
  const kadr = ["raqs1", "raqs2", "raqs3"][Math.floor(a * 9) % 3];
  return <g>
    <Fon n="fon_raqs" />
    <rect width="400" height="300" fill="#000" opacity="0.25" />
    <Sp n={kadr} cx={200} by={294} h={215} rot={Math.sin(a * Math.PI * 6) * 5} oy={1} />
    {tayyor && <Konfetti />}
  </g>;
}
// ── oshxona ──
function Quy({ a, tayyor }) {
  const burchak = 58 * ease(a);
  const k = HR.koza, h = 118, w = (h * k.w) / k.h, cx = 140, by = 190;
  const px = cx, py = by - h / 2;
  // jo'mrak uchi (rasmda o'ng-yuqori) — burilishdan keyingi o'rni
  const sx0 = cx + w * 0.46, sy0 = by - h * 0.78;
  const r = (burchak * Math.PI) / 180;
  const sx = px + (sx0 - px) * Math.cos(r) - (sy0 - py) * Math.sin(r), sy = py + (sx0 - px) * Math.sin(r) + (sy0 - py) * Math.cos(r);
  const toliq = cl((a - 0.45) / 0.55);
  const gw = 86, gx = 282, gb = 276, gh = (gw * HR.stakan.h) / HR.stakan.w;
  return <g>
    <Fon n="fon_quy" />
    <Sp n="stakan" cx={gx} by={gb} h={gh} />
    {toliq > 0 && <rect x={gx - gw * 0.34} y={gb - 12 - (gh - 26) * toliq} width={gw * 0.68} height={(gh - 26) * toliq} rx="4" fill="#4FB3F6" opacity="0.6" />}
    {a > 0.4 && !tayyor && <path className="hs-oqim" d={`M${sx} ${sy} Q ${(sx + gx) / 2 + 10} ${sy - 10}, ${gx} ${gb - gh + 10}`} stroke="#6EC6FF" strokeWidth="7" fill="none" strokeLinecap="round" strokeDasharray="10 4" />}
    <Sp n="koza" cx={cx} by={by} h={h} rot={burchak} />
    {tayyor && <Yulduzcha x={330} y={60} />}
  </g>;
}
function Yuv({ a, tayyor }) {
  const toza = cl((a - 0.55) / 0.3);
  return <g>
    <Fon n="fon_yuv" />
    <rect width="400" height="300" fill="#fff" opacity="0.25" />
    <Sp n="iflos" cx={200} by={292} h={205} op={1 - toza} />
    <Sp n="toza" cx={200} by={295} h={235} op={toza} />
    <Sp n="kopik" cx={200} by={280} h={190} op={Math.sin(Math.PI * cl(a * 1.25)) * 0.95} />
    {tayyor && <Yulduzcha x={340} y={55} />}
  </g>;
}
function Kes({ a, tayyor }) {
  const kesildi = cl((a - 0.8) / 0.2);
  return <g>
    <Fon n="fon_kes" />
    <Sp n="non" cx={200} by={268} h={92} op={1 - kesildi} />
    <Sp n="pichoq" cx={200} by={lerp(130, 238, ease(cl(a / 0.85)))} h={128} op={1 - kesildi} />
    <Sp n="non_ikki" cx={200} by={276} h={140} op={kesildi} />
    {tayyor && <Yulduzcha x={330} y={60} />}
  </g>;
}
function Ye({ a, tayyor, joy }) {
  const x = joy ? joy.x * 400 : lerp(112, 272, a), y = joy ? joy.y * 300 : 180;
  return <g>
    <Fon n="fon_ye" />
    <rect width="400" height="300" fill="#fff" opacity="0.18" />
    {!tayyor && <Sp n="yuz_kut" cx={272} by={298} h={232} />}
    {!tayyor && RASMLAR.apple && <image href={RASMLAR.apple} x={x - 34} y={y - 36} width="68" height="72" />}
    {tayyor && <Sp n="ye_bola" cx={262} by={298} h={240} />}
    {tayyor && <Sp n="olma_tish" cx={112} by={250} h={90} />}
    {tayyor && <Konfetti />}
  </g>;
}

/** Sahna komponentlari va ular uchun imo-ishora sozlamalari (olib borish — boshi va nishon). */
export const SAHNA = {
  open: { C: (p) => <Eshik {...p} /> },
  close: { C: (p) => <Eshik {...p} yop /> },
  lighton: { C: (p) => <Chiroq {...p} /> },
  lightoff: { C: (p) => <Chiroq {...p} ochir /> },
  kick: { C: (p) => <Tep {...p} /> },
  throw: { C: (p) => <Ot {...p} /> },
  jump: { C: (p) => <Sakra {...p} /> },
  run: { C: (p) => <Yugur {...p} /> },
  drive: { C: (p) => <Hayda {...p} /> },
  turn: { C: (p) => <Rul {...p} />, markaz: { x: 0.5, y: 0.6 } },
  stop: { C: (p) => <Toxta {...p} /> },
  ride: { C: (p) => <Velik {...p} /> },
  blow: { C: (p) => <Shar {...p} /> },
  pop: { C: (p) => <Shar {...p} yor /> },
  clap: { C: (p) => <Qarsak {...p} /> },
  dance: { C: (p) => <Raqs {...p} /> },
  pour: { C: (p) => <Quy {...p} />, markaz: { x: 0.35, y: 0.45 } },
  wash: { C: (p) => <Yuv {...p} /> },
  cut: { C: (p) => <Kes {...p} /> },
  eat: { C: (p) => <Ye {...p} />, boshi: { x: 0.28, y: 0.6, r: 0.16 }, nishon: { x: 0.68, y: 0.62, r: 0.12 } },
};

/** Kichik ko'rinish (tanlash kartasi uchun): sahna boshlang'ich holatda. */
export function SahnaRasm({ id }) {
  const S = SAHNA[id];
  if (!S) return null;
  return <svg viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" className="hs-mini" aria-hidden="true" focusable="false">{S.C({ a: 0, tayyor: false })}</svg>;
}
