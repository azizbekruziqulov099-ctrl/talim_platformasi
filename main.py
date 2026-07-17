import React, { useState, useEffect, useRef, useMemo } from "react";
import { HUDUDLAR, VILOYATLAR } from "./hududlar.js";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import {
  ChevronRight, ChevronDown, TrendingUp, BarChart3, Bell, User,
  Loader2, WifiOff, KeyRound, UserPlus, PencilLine, Users, FileSpreadsheet, Heart,
} from "lucide-react";

const API_BASE = "https://talimplatformasi-production.up.railway.app";

function tegsizKorsat(matn) {
  // Ko'rsatishda [ru]so'z[/ru] kabi teglarni yashiradi (faqat ichidagi matnni qoldiradi) —
  // ovozga esa XOM matn (teg bilan) beriladi, shunda mos tilda o'qiladi.
  if (!matn) return matn;
  return matn.replace(/\[\/?[a-zA-Z]+\]/g, "");
}

function darajaRang(foiz) {
  if (foiz >= 85) return "#C89B3C";
  if (foiz >= 65) return "#2D8B8B";
  if (foiz >= 45) return "#B0553A";
  return "#8A8578";
}
function darajaNom(foiz) {
  if (foiz >= 85) return "Mukammal";
  if (foiz >= 65) return "Yaxshi";
  if (foiz >= 45) return "O'rtacha";
  return "E'tibor kerak";
}

function Logotip() {
  return (
    <div className="w-14 h-14 rounded-2xl mx-auto mb-4 grid grid-cols-2 grid-rows-2 gap-0.5 p-1.5" style={{ backgroundColor: "#1B4B7A" }}>
      <div className="rounded-sm" style={{ backgroundColor: "#C89B3C" }} />
      <div className="rounded-sm" style={{ backgroundColor: "#2D8B8B" }} />
      <div className="rounded-sm" style={{ backgroundColor: "#2D8B8B" }} />
      <div className="rounded-sm" style={{ backgroundColor: "#C89B3C" }} />
    </div>
  );
}

function Qobiq({ children }) {
  return (
    <div className="min-h-screen flex items-center justify-center px-6" style={{ backgroundColor: "#F7F5F0" }}>
      <div className="w-full max-w-sm">{children}</div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// 1) KIRISH — Google tugmasi
// ═══════════════════════════════════════════════════════════
function LoginEkrani() {
  return (
    <Qobiq>
      <div className="text-center mb-8">
        <Logotip />
        <h1 className="text-xl font-bold" style={{ color: "#2B2B2B" }}>SamTM Ta'lim</h1>
        <p className="text-sm mt-1" style={{ color: "#8A8578" }}>Farzandingiz bilimini kuzating</p>
      </div>
      <button
        onClick={() => { window.location.href = `${API_BASE}/auth/google/login`; }}
        className="w-full py-3.5 rounded-xl font-semibold text-white flex items-center justify-center gap-2"
        style={{ backgroundColor: "#1B4B7A" }}
      >
        Google orqali kirish
      </button>
      <p className="text-xs text-center mt-4" style={{ color: "#B0AA98" }}>
        Birinchi marta kirsangiz, keyingi ekranda tanlov beriladi
      </p>
    </Qobiq>
  );
}

// ═══════════════════════════════════════════════════════════
// 2) ULASH — Google email topildi, lekin bot hisobiga ULANMAGAN
// ═══════════════════════════════════════════════════════════
function UlashEkrani({ email, ism, onUlandi }) {
  const [rejim, setRejim] = useState(null); // null | 'kod' | 'royxat'
  const [kod, setKod] = useState("");
  const [ismInput, setIsmInput] = useState(ism || "");
  const [rol, setRol] = useState("oquvchi");
  const [sinf, setSinf] = useState("5");
  const [viloyat, setViloyat] = useState("");
  const [tuman, setTuman] = useState("");
  const [tugilganSana, setTugilganYil] = useState("");
  const [maktabRaqami, setMaktabRaqami] = useState("");
  const [xato, setXato] = useState("");
  const [yuklanmoqda, setYuklanmoqda] = useState(false);
  const [oxshashlar, setOxshashlar] = useState([]);

  useEffect(() => {
    if (rejim !== "royxat" || ismInput.trim().length < 3) { setOxshashlar([]); return; }
    const kechiktirish = setTimeout(async () => {
      try {
        const res = await fetch(`${API_BASE}/auth/ism_tekshir?ism=${encodeURIComponent(ismInput.trim())}`);
        const data = await res.json();
        setOxshashlar(data.oxshash || []);
      } catch { /* jimgina o'tkazamiz - bu faqat ogohlantirish, ro'yxatdan o'tishni to'xtatmasin */ }
    }, 500);
    return () => clearTimeout(kechiktirish);
  }, [ismInput, rejim]);

  const kodBilan = async () => {
    if (!kod.trim()) return;
    setXato(""); setYuklanmoqda(true);
    try {
      const res = await fetch(`${API_BASE}/auth/ulash`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, kod: kod.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      onUlandi(data.token);
    } catch (e) {
      setXato(e.message === "Failed to fetch" ? "Serverga ulanib bo'lmadi" : e.message);
    } finally { setYuklanmoqda(false); }
  };

  const royxatBilan = async () => {
    if (!ismInput.trim()) return;
    setXato(""); setYuklanmoqda(true);
    try {
      const res = await fetch(`${API_BASE}/auth/royxat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email, ism: ismInput.trim(), rol,
          sinf: rol === "oquvchi" ? sinf : undefined,
          region: viloyat || undefined,
          district: tuman || undefined,
          tugilgan_sana: tugilganSana || undefined,
          maktab_raqami: rol === "oquvchi" && maktabRaqami ? maktabRaqami : undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      onUlandi(data.token);
    } catch (e) {
      setXato(e.message === "Failed to fetch" ? "Serverga ulanib bo'lmadi" : e.message);
    } finally { setYuklanmoqda(false); }
  };

  if (rejim === null) {
    return (
      <Qobiq>
        <div className="text-center mb-8">
          <Logotip />
          <h1 className="text-lg font-bold" style={{ color: "#2B2B2B" }}>Xush kelibsiz!</h1>
          <p className="text-sm mt-1" style={{ color: "#8A8578" }}>{email}</p>
        </div>
        <button onClick={() => setRejim("kod")}
          className="w-full py-4 rounded-xl border flex items-center gap-3 mb-3 text-left"
          style={{ borderColor: "#E5E1D8", backgroundColor: "#FFFFFF" }}>
          <KeyRound size={20} style={{ color: "#1B4B7A" }} />
          <div>
            <p className="font-medium text-sm" style={{ color: "#2B2B2B" }}>Bot orqali ulash kodim bor</p>
            <p className="text-xs" style={{ color: "#8A8578" }}>Botda "🔗 Saytga ulanish kodi" bosgan bo'lsangiz</p>
          </div>
        </button>
        <button onClick={() => setRejim("royxat")}
          className="w-full py-4 rounded-xl border flex items-center gap-3 text-left"
          style={{ borderColor: "#E5E1D8", backgroundColor: "#FFFFFF" }}>
          <UserPlus size={20} style={{ color: "#2D8B8B" }} />
          <div>
            <p className="font-medium text-sm" style={{ color: "#2B2B2B" }}>Yangi ro'yxatdan o'taman</p>
            <p className="text-xs" style={{ color: "#8A8578" }}>Botdan foydalanmagan bo'lsangiz</p>
          </div>
        </button>
      </Qobiq>
    );
  }

  if (rejim === "kod") {
    return (
      <Qobiq>
        <button onClick={() => setRejim(null)} className="text-sm mb-4" style={{ color: "#8A8578" }}>← Ortga</button>
        <h1 className="text-lg font-bold mb-1" style={{ color: "#2B2B2B" }}>Ulash kodini kiriting</h1>
        <p className="text-sm mb-5" style={{ color: "#8A8578" }}>Botdagi "👤 Kabinet → 🔗 Saytga ulanish kodi"</p>
        <input type="text" value={kod} onChange={(e) => setKod(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && kodBilan()}
          placeholder="masalan: UU62JX"
          className="w-full px-4 py-3 rounded-xl border text-base mb-3 tracking-widest text-center font-semibold"
          style={{ borderColor: "#E5E1D8", backgroundColor: "#FFFFFF" }} />
        {xato && <div className="flex items-center gap-2 text-sm mb-3" style={{ color: "#B0553A" }}><WifiOff size={15} /> {xato}</div>}
        <button onClick={kodBilan} disabled={yuklanmoqda}
          className="w-full py-3.5 rounded-xl font-semibold text-white flex items-center justify-center gap-2"
          style={{ backgroundColor: "#1B4B7A", opacity: yuklanmoqda ? 0.7 : 1 }}>
          {yuklanmoqda ? <Loader2 size={18} className="animate-spin" /> : "Ulash"}
        </button>
      </Qobiq>
    );
  }

  return (
    <Qobiq>
      <button onClick={() => setRejim(null)} className="text-sm mb-4" style={{ color: "#8A8578" }}>← Ortga</button>
      <h1 className="text-lg font-bold mb-5" style={{ color: "#2B2B2B" }}>Ro'yxatdan o'tish</h1>

      <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Ismingiz</label>
      <input type="text" value={ismInput} onChange={(e) => setIsmInput(e.target.value)}
        className="w-full px-4 py-3 rounded-xl border text-base mb-2"
        style={{ borderColor: "#E5E1D8", backgroundColor: "#FFFFFF" }} />

      {oxshashlar.length > 0 && (
        <div className="rounded-xl p-3.5 mb-4" style={{ backgroundColor: "#FFF8E8", border: "1px solid #EEDFB0" }}>
          <p className="text-xs font-medium mb-1" style={{ color: "#6B5B2E" }}>
            Botda shunga o'xshash ism topildi:
          </p>
          {oxshashlar.map((o, i) => (
            <p key={i} className="text-xs" style={{ color: "#8A7642" }}>• {o.full_name} ({o.role})</p>
          ))}
          <p className="text-xs mt-1.5" style={{ color: "#6B5B2E" }}>
            Bu sizmi? Bo'lsa, ortga qaytib "Bot kodim bor" ni tanlang — aks holda ikkita akkaunt paydo bo'ladi.
          </p>
        </div>
      )}

      <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Kimsiz?</label>
      <div className="grid grid-cols-3 gap-2 mb-4">
        {[["oquvchi", "O'quvchi"], ["ota-ona", "Ota-ona"], ["oqituvchi", "O'qituvchi"]].map(([v, l]) => (
          <button key={v} onClick={() => setRol(v)}
            className="py-2.5 rounded-lg border text-xs font-medium"
            style={{
              borderColor: rol === v ? "#1B4B7A" : "#E5E1D8",
              backgroundColor: rol === v ? "#1B4B7A" : "#FFFFFF",
              color: rol === v ? "#FFFFFF" : "#5A5648",
            }}>
            {l}
          </button>
        ))}
      </div>

      {rol === "oquvchi" && (
        <>
          <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Sinf</label>
          <select value={sinf} onChange={(e) => setSinf(e.target.value)}
            className="w-full px-4 py-3 rounded-xl border text-base mb-4"
            style={{ borderColor: "#E5E1D8", backgroundColor: "#FFFFFF" }}>
            {Array.from({ length: 11 }, (_, i) => i + 1).map((n) => (
              <option key={n} value={n}>{n}-sinf</option>
            ))}
          </select>

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Maktab raqami</label>
          <input type="text" value={maktabRaqami} onChange={(e) => setMaktabRaqami(e.target.value)}
            placeholder="masalan: 21"
            className="w-full px-4 py-3 rounded-xl border text-base mb-4"
            style={{ borderColor: "#E5E1D8", backgroundColor: "#FFFFFF" }} />
        </>
      )}

      <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Viloyat</label>
      <select value={viloyat} onChange={(e) => { setViloyat(e.target.value); setTuman(""); }}
        className="w-full px-4 py-3 rounded-xl border text-base mb-4"
        style={{ borderColor: "#E5E1D8", backgroundColor: "#FFFFFF" }}>
        <option value="">Tanlanmagan</option>
        {VILOYATLAR.map((v) => <option key={v} value={v}>{v}</option>)}
      </select>

      {viloyat && (
        <>
          <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Tuman</label>
          <select value={tuman} onChange={(e) => setTuman(e.target.value)}
            className="w-full px-4 py-3 rounded-xl border text-base mb-4"
            style={{ borderColor: "#E5E1D8", backgroundColor: "#FFFFFF" }}>
            <option value="">Tanlanmagan</option>
            {(HUDUDLAR[viloyat] || []).map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </>
      )}

      <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Tug'ilgan sana</label>
      <input type="date" value={tugilganSana} onChange={(e) => setTugilganYil(e.target.value)}
        min="1950-01-01" max={new Date().toISOString().split("T")[0]}
        className="w-full px-4 py-3 rounded-xl border text-base mb-4"
        style={{ borderColor: "#E5E1D8", backgroundColor: "#FFFFFF" }} />

      {xato && <div className="flex items-center gap-2 text-sm mb-3" style={{ color: "#B0553A" }}><WifiOff size={15} /> {xato}</div>}

      <button onClick={royxatBilan} disabled={yuklanmoqda}
        className="w-full py-3.5 rounded-xl font-semibold text-white flex items-center justify-center gap-2"
        style={{ backgroundColor: "#1B4B7A", opacity: yuklanmoqda ? 0.7 : 1 }}>
        {yuklanmoqda ? <Loader2 size={18} className="animate-spin" /> : "Ro'yxatdan o'tish"}
      </button>
    </Qobiq>
  );
}

// ═══════════════════════════════════════════════════════════
// 3) KABINET — token bilan kirilgach
// ═══════════════════════════════════════════════════════════
function MavzuKoshin({ mavzu }) {
  return (
    <div className="relative aspect-square rounded-lg overflow-hidden" style={{ backgroundColor: darajaRang(mavzu.foiz) }} title={`${mavzu.nom}: ${mavzu.foiz}%`}>
      <span className="absolute inset-0 flex items-center justify-center text-white font-semibold text-sm drop-shadow">{mavzu.foiz}%</span>
    </div>
  );
}

function FanBolimi({ fan, ochiq, onToggle }) {
  return (
    <div className="rounded-2xl overflow-hidden border transition-all duration-300" style={{ borderColor: ochiq ? fan.rang : "#E5E1D8", backgroundColor: "#FFFFFF" }}>
      <button onClick={onToggle} className="w-full flex items-center gap-4 p-5 text-left focus:outline-none">
        <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-xs shrink-0" style={{ backgroundColor: fan.rang }}>{fan.qisqa}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline justify-between gap-2">
            <h3 className="font-semibold text-lg" style={{ color: "#2B2B2B" }}>{fan.nom}</h3>
            <span className="text-2xl font-bold shrink-0" style={{ color: fan.rang }}>{fan.foiz}%</span>
          </div>
          <div className="mt-2 h-2 rounded-full overflow-hidden" style={{ backgroundColor: "#EFEBE1" }}>
            <div className="h-full rounded-full transition-all duration-700" style={{ width: `${fan.foiz}%`, backgroundColor: fan.rang }} />
          </div>
        </div>
        {ochiq ? <ChevronDown size={20} className="shrink-0" style={{ color: "#8A8578" }} /> : <ChevronRight size={20} className="shrink-0" style={{ color: "#8A8578" }} />}
      </button>
      {ochiq && (
        <div className="px-5 pb-5 grid grid-cols-3 sm:grid-cols-4 gap-2.5">
          {fan.mavzular.map((m) => <MavzuKoshin key={m.nom} mavzu={m} />)}
        </div>
      )}
    </div>
  );
}

function BilimTab({ data }) {
  const [ochiqFan, setOchiqFan] = useState(data.fanlar[0]?.nom || null);
  const radarData = data.fanlar.map((f) => ({ fan: f.qisqa, foiz: f.foiz }));

  return (
    <div>
      <div className="relative overflow-hidden px-5 pt-6 pb-8" style={{ backgroundColor: "#1B4B7A" }}>
        <div className="relative">
          <h1 className="mt-1 text-2xl font-bold text-white">{data.bola?.ism || "Sizning bilimingiz"}</h1>
          <div className="mt-6 flex items-end gap-4">
            <div>
              <div className="flex items-baseline gap-1">
                <span className="text-5xl font-bold text-white">{data.umumiy_foiz}</span>
                <span className="text-xl font-bold" style={{ color: "#C89B3C" }}>%</span>
              </div>
              <p className="text-xs mt-1 flex items-center gap-1" style={{ color: "#B8CBDA" }}><TrendingUp size={12} /> {darajaNom(data.umumiy_foiz)}</p>
            </div>
            {data.fanlar.length > 0 && (
              <div className="flex-1 h-24">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData} outerRadius="75%">
                    <PolarGrid stroke="rgba(255,255,255,0.15)" />
                    <PolarAngleAxis dataKey="fan" tick={{ fill: "#B8CBDA", fontSize: 10 }} />
                    <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                    <Radar dataKey="foiz" stroke="#C89B3C" fill="#C89B3C" fillOpacity={0.35} strokeWidth={2} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>
      </div>
      <div className="px-5 -mt-3 pb-4 space-y-3">
        {data.fanlar.length === 0 ? (
          <div className="rounded-2xl p-6 text-center bg-white border mt-4" style={{ borderColor: "#E5E1D8" }}>
            <p className="text-sm" style={{ color: "#8A8578" }}>Hali birorta ham mavzu o'rganilmagan.</p>
          </div>
        ) : (
          data.fanlar.map((fan) => (
            <FanBolimi key={fan.nom} fan={fan} ochiq={ochiqFan === fan.nom} onToggle={() => setOchiqFan(ochiqFan === fan.nom ? null : fan.nom)} />
          ))
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// 4) TEST YECHISH
// ═══════════════════════════════════════════════════════════
function TestTab({ token, sinf: sinfXom }) {
  // DB'da sinf ba'zan "5", ba'zan "5-sinf" shaklida saqlangan (bot tomonidan
  // turli joyda turlicha yozilgan) — shu yerda BIR MARTA tozalab, hammasi
  // shu tozalangan qiymatdan foydalanadi, aks holda solishtirish mos kelmaydi.
  const sinf = sinfXom ? String(sinfXom).replace(/-sinf$/i, "").trim() : null;

  const [holat, setHolat] = useState("mavzular"); // mavzular | songi | savollar | natija
  const [fanlar, setFanlar] = useState([]);
  const [tanlanganSinf, setTanlanganSinf] = useState(null); // admin uchun: tanlangan sinf raqami
  const [ochiqFan, setOchiqFan] = useState(null);
  const [savollar, setSavollar] = useState([]);
  const [tanlanganMavzu, setTanlanganMavzu] = useState(null);
  const [joriySavol, setJoriySavol] = useState(0);
  const [javoblar, setJavoblar] = useState({});
  const [natija, setNatija] = useState(null);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");

  useEffect(() => {
    const url = sinf ? `${API_BASE}/api/mavzular?sinf=${encodeURIComponent(sinf)}` : `${API_BASE}/api/mavzular`;
    fetch(url)
      .then((r) => r.json())
      .then((d) => { setFanlar(d.fanlar || []); setYuklanmoqda(false); })
      .catch(() => { setXato("Mavzularni yuklab bo'lmadi"); setYuklanmoqda(false); });
  }, [sinf]);

  // Fan→Sinf→Mavzu ma'lumotini Sinf→Fan→Mavzu ko'rinishiga aylantiramiz —
  // har sinfga faqat O'SHA sinfning fan/mavzulari ko'rinishi uchun.
  const sinflarRoyxati = useMemo(() => {
    const bySinf = {};
    fanlar.forEach((fan) => {
      fan.sinflar.forEach((s) => {
        if (!bySinf[s.sinf]) bySinf[s.sinf] = { sinf: s.sinf, fanlar: [] };
        bySinf[s.sinf].fanlar.push({ qisqa: fan.qisqa, nom: fan.nom, mavzular: s.mavzular });
      });
    });
    return Object.values(bySinf).sort((a, b) => parseInt(a.sinf, 10) - parseInt(b.sinf, 10));
  }, [fanlar]);

  // O'quvchi uchun sinf tashqaridan berilgan (o'z sinfi) — sinf tanlash bosqichi kerak emas.
  const joriySinfMalumoti = sinf
    ? sinflarRoyxati.find((s) => String(s.sinf) === String(sinf)) || sinflarRoyxati[0]
    : sinflarRoyxati.find((s) => String(s.sinf) === String(tanlanganSinf));

  // Mavzu bosilganda — darhol savol OLMAYMIZ, avval "nechta savol" so'raymiz
  const mavzuBoslandi = (fan, mavzu) => {
    setTanlanganMavzu({ ...mavzu, fanNomi: fan.nom });
    setHolat("songi");
  };

  const [aralashRejim, setAralashRejim] = useState(false);
  const [tanlanganKodlar, setTanlanganKodlar] = useState([]); // [{topic_code, nomi, savol_soni}]

  const aralashToggle = (m) => {
    setTanlanganKodlar((prev) =>
      prev.some((k) => k.topic_code === m.topic_code)
        ? prev.filter((k) => k.topic_code !== m.topic_code)
        : [...prev, m]
    );
  };

  const aralashTestBoshlandi = () => {
    if (tanlanganKodlar.length === 0) return;
    setTanlanganMavzu({
      aralash: true,
      kodlar: tanlanganKodlar.map((k) => k.topic_code),
      nomi: `Aralash test (${tanlanganKodlar.length} mavzu)`,
      fanNomi: joriySinfMalumoti ? `${joriySinfMalumoti.sinf}-sinf` : "",
      savol_soni: tanlanganKodlar.reduce((s, k) => s + (k.savol_soni || 0), 0),
    });
    setHolat("songi");
  };

  const [qiyinlik, setQiyinlik] = useState(""); // "" = aralash | oson | o'rta | qiyin | murakkab

  const savollarniYukla = async (soni) => {
    setYuklanmoqda(true); setXato("");
    try {
      let res;
      if (tanlanganMavzu.aralash) {
        res = await fetch(`${API_BASE}/api/test_aralash`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ topic_codes: tanlanganMavzu.kodlar, soni, qiyinlik: qiyinlik || undefined }),
        });
      } else {
        const qs = new URLSearchParams({ soni });
        if (qiyinlik) qs.set("qiyinlik", qiyinlik);
        res = await fetch(`${API_BASE}/api/test/${tanlanganMavzu.topic_code}?${qs.toString()}`);
      }
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setSavollar(data.savollar);
      setJavoblar({}); setJoriySavol(0); setHolat("savollar");
    } catch (e) {
      setXato(e.message);
    } finally { setYuklanmoqda(false); }
  };

  const [yozibJavob, setYozibJavob] = useState("");
  const [ovozOynayapti, setOvozOynayapti] = useState(false);
  const ovozRef = useRef(null);

  const ovozniOqi = (matn) => {
    if (ovozRef.current) { ovozRef.current.pause(); ovozRef.current = null; }
    setOvozOynayapti(true);
    const audio = new Audio(`${API_BASE}/api/ovoz?matn=${encodeURIComponent(matn)}`);
    ovozRef.current = audio;
    audio.onended = () => setOvozOynayapti(false);
    audio.onerror = () => setOvozOynayapti(false);
    audio.play().catch(() => setOvozOynayapti(false));
  };

  const [joriyNatija, setJoriyNatija] = useState(null); // {togrimi, togri_javob, tushuntirish} | null
  const [qolganVaqt, setQolganVaqt] = useState(null);
  const [avtoQoldi, setAvtoQoldi] = useState(null);
  const timerRef = useRef(null);
  const avtoRef = useRef(null);

  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (holat !== "savollar" || joriyNatija || !savollar[joriySavol]) return;

    const s = savollar[joriySavol];
    if (!s.time_limit) { setQolganVaqt(null); return; }
    setQolganVaqt(s.time_limit);
    timerRef.current = setInterval(() => {
      setQolganVaqt((v) => {
        if (v <= 1) {
          clearInterval(timerRef.current);
          javobBer(s.id, "");
          return 0;
        }
        return v - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [joriySavol, holat]);

  const javobBer = async (savolId, harf) => {
    if (timerRef.current) clearInterval(timerRef.current);
    setJavoblar((prev) => ({ ...prev, [savolId]: harf }));
    try {
      const res = await fetch(`${API_BASE}/api/test/javob_tekshir`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ savol_id: savolId, tanlangan: harf }),
      });
      const data = await res.json();
      setJoriyNatija(data);
    } catch {
      setJoriyNatija({ togrimi: false, togri_javob: "?", tushuntirish: "" });
    }
  };

  const keyingiSavolga = () => {
    if (avtoRef.current) clearInterval(avtoRef.current);
    setJoriyNatija(null);
    setYozibJavob("");
    if (joriySavol < savollar.length - 1) setJoriySavol(joriySavol + 1);
    else yakunla();
  };

  // Javob ko'rsatilgach (to'g'ri/noto'g'ri chiqqach), 4 soniyadan keyin
  // AVTOMATIK keyingi savolga o'tadi — foydalanuvchi tugma bosishi shart emas
  useEffect(() => {
    if (!joriyNatija) { setAvtoQoldi(null); return; }
    setAvtoQoldi(4);
    avtoRef.current = setInterval(() => {
      setAvtoQoldi((v) => {
        if (v <= 1) {
          clearInterval(avtoRef.current);
          keyingiSavolga();
          return 0;
        }
        return v - 1;
      });
    }, 1000);
    return () => clearInterval(avtoRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [joriyNatija]);

  const yakunla = async () => {
    setYuklanmoqda(true);
    const ro_yxat = Object.entries(javoblar).map(([id, tanlangan]) => ({
      savol_id: parseInt(id, 10), tanlangan,
    }));
    try {
      const res = await fetch(`${API_BASE}/api/test/natija`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          tanlanganMavzu.aralash
            ? { token, topic_codes: tanlanganMavzu.kodlar, javoblar: ro_yxat }
            : { token, topic_code: tanlanganMavzu.topic_code, javoblar: ro_yxat }
        ),
      });
      const data = await res.json();
      setNatija(data);
      setHolat("natija");
    } catch (e) {
      setXato("Natijani yuborib bo'lmadi");
    } finally { setYuklanmoqda(false); }
  };

  const qaytaBoshlash = () => {
    setHolat("mavzular"); setTanlanganMavzu(null); setSavollar([]); setNatija(null); setJoriyNatija(null);
  };

  if (yuklanmoqda) {
    return <div className="px-5 pt-16 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "#1B4B7A" }} /></div>;
  }

  if (holat === "natija") {
    const rangi = natija.foiz >= 85 ? "#C89B3C" : natija.foiz >= 65 ? "#2D8B8B" : natija.foiz >= 45 ? "#B0553A" : "#8A8578";
    return (
      <div className="px-5 pt-10 pb-6">
        <div className="text-center">
          <div className="w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center" style={{ backgroundColor: `${rangi}1A` }}>
            <span className="text-2xl font-bold" style={{ color: rangi }}>{natija.foiz}%</span>
          </div>
          <h1 className="text-xl font-bold mb-1" style={{ color: "#2B2B2B" }}>{tanlanganMavzu.nomi}</h1>
          <p className="text-sm mb-6" style={{ color: "#8A8578" }}>{natija.togri} / {natija.jami} to'g'ri</p>
        </div>

        {natija.xatolar && natija.xatolar.length > 0 && (
          <div className="mb-6">
            <p className="text-sm font-semibold mb-3" style={{ color: "#2B2B2B" }}>
              ❌ Xato javoblar ({natija.xatolar.length} ta)
            </p>
            <div className="space-y-3">
              {natija.xatolar.map((x) => (
                <div key={x.savol_id} className="rounded-xl p-4 border" style={{ borderColor: "#F3D3D3", backgroundColor: "#FCEBEB" }}>
                  <p className="text-sm font-medium mb-2" style={{ color: "#2B2B2B" }}>{x.savol}</p>
                  <p className="text-xs mb-1" style={{ color: "#A32D2D" }}>Sizning javobingiz: <b>{x.sizning_javob}</b></p>
                  <p className="text-xs" style={{ color: "#3B6D11" }}>To'g'ri javob: <b>{x.togri_javob}</b></p>
                  {x.tushuntirish && <p className="text-xs mt-1.5" style={{ color: "#5A5648" }}>{x.tushuntirish}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        <button onClick={qaytaBoshlash} className="w-full py-3.5 rounded-xl font-semibold text-white text-center" style={{ backgroundColor: "#1B4B7A" }}>
          Boshqa mavzu
        </button>
      </div>
    );
  }

  if (holat === "songi") {
    const jami = tanlanganMavzu.savol_soni || 0;
    const variantlar = [5, 10, 15].filter((n) => n < jami);
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => setHolat("mavzular")} className="text-sm mb-4" style={{ color: "#8A8578" }}>← Ortga</button>
        <h1 className="text-lg font-bold mb-1" style={{ color: "#2B2B2B" }}>{tanlanganMavzu.nomi}</h1>
        <p className="text-xs mb-5" style={{ color: "#8A8578" }}>{tanlanganMavzu.fanNomi}</p>

        <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "#E5E1D8" }}>
          <p className="text-sm font-semibold mb-3" style={{ color: "#2B2B2B" }}>🎯 Qiyinlik darajasi</p>
          <div className="flex gap-2 flex-wrap">
            {[
              ["", "🎲 Aralash"], ["oson", "🟢 Oson"], ["o'rta", "🟡 O'rta"],
              ["qiyin", "🔴 Qiyin"], ["murakkab", "⚫ Murakkab"],
            ].map(([qiym, nom]) => (
              <button key={qiym} onClick={() => setQiyinlik(qiym)}
                className="px-3.5 py-2 rounded-full text-xs font-semibold transition-colors"
                style={qiyinlik === qiym
                  ? { backgroundColor: "#1B4B7A", color: "#fff" }
                  : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>
                {nom}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-2xl p-5 bg-white border" style={{ borderColor: "#E5E1D8" }}>
          <p className="text-sm font-semibold mb-3" style={{ color: "#2B2B2B" }}>🔢 Nechta savol yechasiz?</p>
          <div className="grid grid-cols-3 gap-2 mb-2.5">
            {variantlar.map((n) => (
              <button key={n} onClick={() => savollarniYukla(n)}
                className="py-3.5 rounded-xl border font-semibold text-center text-sm"
                style={{ borderColor: "#E5E1D8", backgroundColor: "#F7F5F0", color: "#2B2B2B" }}>
                {n} ta
              </button>
            ))}
          </div>
          <button onClick={() => savollarniYukla(jami)}
            className="w-full py-3.5 rounded-xl font-semibold text-white text-center text-sm"
            style={{ backgroundColor: "#1B4B7A" }}>
            🚀 Hammasi ({jami} ta)
          </button>
        </div>
      </div>
    );
  }

  if (holat === "savollar") {
    const s = savollar[joriySavol];
    const oxirgi = joriySavol === savollar.length - 1;
    const yozuvli = s.question_type === "write_answer";
    const variantlar = [["A", s.option_a], ["B", s.option_b], ["C", s.option_c], ["D", s.option_d]];
    const javobBerilgan = !!joriyNatija;

    const variantRangi = (harf) => {
      if (!javobBerilgan) {
        return javoblar[s.id] === harf
          ? { borderColor: "#1B4B7A", backgroundColor: "#EAF1F7" }
          : { borderColor: "#E5E1D8", backgroundColor: "#FFFFFF" };
      }
      if (harf === joriyNatija.togri_javob) return { borderColor: "#639922", backgroundColor: "#EAF3DE" };
      if (harf === javoblar[s.id]) return { borderColor: "#E24B4A", backgroundColor: "#FCEBEB" };
      return { borderColor: "#E5E1D8", backgroundColor: "#FFFFFF", opacity: 0.6 };
    };

    return (
      <div className="px-5 pt-6 pb-4">
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs font-medium" style={{ color: "#8A8578" }}>{joriySavol + 1} / {savollar.length}</p>
          <div className="flex items-center gap-3">
            {qolganVaqt !== null && !javobBerilgan && (
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full"
                style={{ backgroundColor: qolganVaqt <= 5 ? "#FCEBEB" : "#F1EFE8", color: qolganVaqt <= 5 ? "#A32D2D" : "#5A5648" }}>
                ⏱ {qolganVaqt}s
              </span>
            )}
            <p className="text-xs" style={{ color: "#8A8578" }}>{tanlanganMavzu.nomi}</p>
          </div>
        </div>
        <div className="h-1.5 rounded-full overflow-hidden mb-6" style={{ backgroundColor: "#EFEBE1" }}>
          <div className="h-full rounded-full transition-all" style={{ width: `${((joriySavol + 1) / savollar.length) * 100}%`, backgroundColor: "#1B4B7A" }} />
        </div>

        {s.rasm_id && (
          <img src={`${API_BASE}/api/rasm/${s.rasm_id}`} alt=""
            className="w-full rounded-xl mb-4 object-cover"
            style={{ maxHeight: "220px", backgroundColor: "#EFEBE1" }}
            onError={(e) => { e.target.style.display = "none"; }} />
        )}

        <h2 className="text-lg font-semibold mb-5 flex items-start gap-2" style={{ color: "#2B2B2B" }}>
          <span className="flex-1">{tegsizKorsat(s.question)}</span>
          <button
            onClick={() => ovozniOqi(yozuvli
              ? s.question
              : `${s.question}. A) ${s.option_a}. B) ${s.option_b}. C) ${s.option_c}. D) ${s.option_d}`)}
            disabled={ovozOynayapti}
            className="shrink-0 w-9 h-9 rounded-full flex items-center justify-center"
            style={{ backgroundColor: "#EAF1F7", color: "#1B4B7A", opacity: ovozOynayapti ? 0.6 : 1 }}
            title="Ovoz chiqarib o'qish">
            {ovozOynayapti ? <Loader2 size={16} className="animate-spin" /> : "🔊"}
          </button>
        </h2>

        {yozuvli ? (
          <div className="mb-4">
            <input type="text" value={javobBerilgan ? (javoblar[s.id] || "") : yozibJavob}
              onChange={(e) => setYozibJavob(e.target.value)}
              disabled={javobBerilgan}
              onKeyDown={(e) => { if (e.key === "Enter" && !javobBerilgan && yozibJavob.trim()) javobBer(s.id, yozibJavob.trim()); }}
              placeholder="Javobingizni yozing..."
              className="w-full px-4 py-3.5 rounded-xl border text-sm mb-3"
              style={javobBerilgan
                ? { borderColor: joriyNatija.togrimi ? "#639922" : "#E24B4A", backgroundColor: joriyNatija.togrimi ? "#EAF3DE" : "#FCEBEB" }
                : { borderColor: "#E5E1D8" }} />
            {!javobBerilgan && (
              <button onClick={() => yozibJavob.trim() && javobBer(s.id, yozibJavob.trim())}
                disabled={!yozibJavob.trim()}
                className="w-full py-3 rounded-xl font-semibold text-white text-sm"
                style={{ backgroundColor: "#1B4B7A", opacity: yozibJavob.trim() ? 1 : 0.5 }}>
                Javobni yuborish
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-2.5 mb-4">
            {variantlar.map(([harf, matn]) => (
              <button key={harf} onClick={() => !javobBerilgan && javobBer(s.id, harf)} disabled={javobBerilgan}
                className="w-full text-left px-4 py-3.5 rounded-xl border flex items-center gap-3"
                style={variantRangi(harf)}>
                <span className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold shrink-0"
                  style={{
                    backgroundColor: javobBerilgan
                      ? (harf === joriyNatija.togri_javob ? "#639922" : harf === javoblar[s.id] ? "#E24B4A" : "#F1EFE8")
                      : (javoblar[s.id] === harf ? "#1B4B7A" : "#F1EFE8"),
                    color: (javobBerilgan && (harf === joriyNatija.togri_javob || harf === javoblar[s.id])) || (!javobBerilgan && javoblar[s.id] === harf)
                      ? "#FFFFFF" : "#5A5648",
                  }}>
                  {harf}
                </span>
                <span className="text-sm" style={{ color: "#2B2B2B" }}>{tegsizKorsat(matn)}</span>
              </button>
            ))}
          </div>
        )}

        {javobBerilgan && (
          <div className="rounded-xl p-4 mb-4" style={{ backgroundColor: joriyNatija.togrimi ? "#EAF3DE" : "#FCEBEB" }}>
            <p className="text-sm font-semibold mb-1" style={{ color: joriyNatija.togrimi ? "#3B6D11" : "#A32D2D" }}>
              {joriyNatija.togrimi ? "✓ To'g'ri!" : `✗ Noto'g'ri — to'g'ri javob: ${joriyNatija.togri_javob}`}
            </p>
            {joriyNatija.tushuntirish && (
              <p className="text-sm" style={{ color: joriyNatija.togrimi ? "#3B6D11" : "#A32D2D" }}>{joriyNatija.tushuntirish}</p>
            )}
          </div>
        )}

        {javobBerilgan ? (
          <button onClick={keyingiSavolga} className="w-full py-3.5 rounded-xl font-semibold text-white" style={{ backgroundColor: "#1B4B7A" }}>
            {(oxirgi ? "Yakunlash" : "Keyingi savol")}{avtoQoldi ? ` (${avtoQoldi})` : ""}
          </button>
        ) : (
          <p className="text-center text-xs" style={{ color: "#B0AA98" }}>Javobni tanlang</p>
        )}
      </div>
    );
  }

  // holat === "mavzular"
  // Sinf ko'rsatilmasa (admin) va hali sinf tanlanmagan bo'lsa — avval sinflar ro'yxati.
  if (!sinf && !tanlanganSinf) {
    return (
      <div className="px-5 pt-6 pb-4">
        <h1 className="text-2xl font-bold mb-5" style={{ color: "#2B2B2B" }}>Test yechish</h1>
        {xato && <p className="text-sm mb-4" style={{ color: "#B0553A" }}>{xato}</p>}
        {sinflarRoyxati.length === 0 ? (
          <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "#E5E1D8" }}>
            <p className="text-sm" style={{ color: "#8A8578" }}>Hozircha test mavjud emas.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {sinflarRoyxati.map((s) => {
              const jamiMavzu = s.fanlar.reduce((sum, f) => sum + f.mavzular.length, 0);
              return (
                <button key={s.sinf} onClick={() => setTanlanganSinf(s.sinf)}
                  className="rounded-2xl p-5 text-center bg-white border"
                  style={{ borderColor: "#E5E1D8" }}>
                  <p className="text-xl font-bold mb-1" style={{ color: "#1B4B7A" }}>{s.sinf}-sinf</p>
                  <p className="text-xs" style={{ color: "#8A8578" }}>{s.fanlar.length} fan · {jamiMavzu} mavzu</p>
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  // Sinf tanlangan (yoki o'quvchining o'z sinfi) — endi shu sinfning fanlari va mavzulari
  const sinfMalumoti = joriySinfMalumoti;
  return (
    <div className="px-5 pt-6" style={{ paddingBottom: aralashRejim && tanlanganKodlar.length > 0 ? "84px" : "16px" }}>
      {!sinf && (
        <button onClick={() => { setTanlanganSinf(null); setOchiqFan(null); }} className="text-sm mb-4" style={{ color: "#8A8578" }}>
          ← Sinflar
        </button>
      )}
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-2xl font-bold" style={{ color: "#2B2B2B" }}>
          {sinfMalumoti ? `${sinfMalumoti.sinf}-sinf testlari` : "Test yechish"}
        </h1>
        <button onClick={() => { setAralashRejim(!aralashRejim); setTanlanganKodlar([]); }}
          className="text-xs font-semibold px-3 py-1.5 rounded-full"
          style={aralashRejim
            ? { backgroundColor: "#1B4B7A", color: "#fff" }
            : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>
          {aralashRejim ? "✕ Aralash rejimi" : "🔀 Bir nechta mavzu"}
        </button>
      </div>
      {xato && <p className="text-sm mb-4" style={{ color: "#B0553A" }}>{xato}</p>}
      {!sinfMalumoti || sinfMalumoti.fanlar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "#E5E1D8" }}>
          <p className="text-sm" style={{ color: "#8A8578" }}>Bu sinfda hozircha test mavjud emas.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sinfMalumoti.fanlar.map((fan) => {
            const ochiq = ochiqFan === fan.qisqa;
            return (
              <div key={fan.qisqa} className="rounded-2xl overflow-hidden border bg-white" style={{ borderColor: "#E5E1D8" }}>
                <button onClick={() => setOchiqFan(ochiq ? null : fan.qisqa)} className="w-full flex items-center justify-between p-4">
                  <span className="font-semibold text-sm" style={{ color: "#2B2B2B" }}>{fan.nom}</span>
                  {ochiq ? <ChevronDown size={18} style={{ color: "#8A8578" }} /> : <ChevronRight size={18} style={{ color: "#8A8578" }} />}
                </button>
                {ochiq && (
                  <MavzuRoyxati fan={fan} aralashRejim={aralashRejim} tanlanganKodlar={tanlanganKodlar}
                    onToggle={aralashToggle} onTanla={mavzuBoslandi} />
                )}
              </div>
            );
          })}
        </div>
      )}

      {aralashRejim && tanlanganKodlar.length > 0 && (
        <div className="fixed bottom-16 inset-x-0 z-20 px-5 pb-3">
          <div className="max-w-md mx-auto">
            <button onClick={aralashTestBoshlandi}
              className="w-full py-3.5 rounded-xl font-semibold text-white text-sm shadow-lg"
              style={{ backgroundColor: "#1B4B7A" }}>
              🚀 Aralash test boshlash ({tanlanganKodlar.length} mavzu tanlandi)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function MavzuRoyxati({ fan, aralashRejim, tanlanganKodlar, onToggle, onTanla }) {
  const [korsatilgan, setKorsatilgan] = useState(10);
  const korinadigan = fan.mavzular.slice(0, korsatilgan);
  return (
    <div className="px-4 pb-4 space-y-2">
      {korinadigan.map((m) => {
        const tanlanganmi = tanlanganKodlar.some((k) => k.topic_code === m.topic_code);
        return (
          <button key={m.topic_code}
            onClick={() => aralashRejim ? onToggle(m) : onTanla(fan, m)}
            className="w-full flex items-center justify-between px-3.5 py-3 rounded-xl"
            style={{ backgroundColor: aralashRejim && tanlanganmi ? "#EAF1F7" : "#F7F5F0" }}>
            <span className="flex items-center gap-2.5">
              {aralashRejim && (
                <span className="w-5 h-5 rounded flex items-center justify-center shrink-0"
                  style={{ backgroundColor: tanlanganmi ? "#1B4B7A" : "#FFFFFF", border: `1.5px solid ${tanlanganmi ? "#1B4B7A" : "#C4BFAF"}` }}>
                  {tanlanganmi && <span className="text-white text-xs">✓</span>}
                </span>
              )}
              <span className="text-sm text-left" style={{ color: "#2B2B2B" }}>{m.nomi}</span>
            </span>
            <span className="text-xs shrink-0" style={{ color: "#8A8578" }}>{m.savol_soni} ta</span>
          </button>
        );
      })}
      {korsatilgan < fan.mavzular.length && (
        <button onClick={() => setKorsatilgan(korsatilgan + 10)}
          className="w-full py-2.5 rounded-xl text-xs font-medium text-center"
          style={{ backgroundColor: "#FFFFFF", border: "1px dashed #C4BFAF", color: "#5A5648" }}>
          Yana ko'rsat ({fan.mavzular.length - korsatilgan} ta qoldi)
        </button>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// 5) O'QITUVCHI — guruhlarim, baholash
// ═══════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════
// 7) ADMIN — Test shablon yuklab olish / import qilish
// ═══════════════════════════════════════════════════════════
function AdminTab({ token }) {
  const [bolim, setBolim] = useState("test"); // "test" | "topik"

  return (
    <div className="px-5 pt-6 pb-4">
      <h1 className="text-2xl font-bold mb-4" style={{ color: "#2B2B2B" }}>Shablonlar</h1>

      <div className="flex gap-2 mb-5">
        <button onClick={() => setBolim("test")}
          className="flex-1 py-2.5 rounded-xl font-semibold text-sm"
          style={bolim === "test"
            ? { backgroundColor: "#1B4B7A", color: "#fff" }
            : { backgroundColor: "#fff", color: "#5A5648", border: "1px solid #E5E1D8" }}>
          🧪 Test shablon
        </button>
        <button onClick={() => setBolim("topik")}
          className="flex-1 py-2.5 rounded-xl font-semibold text-sm"
          style={bolim === "topik"
            ? { backgroundColor: "#1B4B7A", color: "#fff" }
            : { backgroundColor: "#fff", color: "#5A5648", border: "1px solid #E5E1D8" }}>
          📋 Topik shablon
        </button>
      </div>

      {bolim === "test" && <TestShablonBolimi token={token} />}
      {bolim === "topik" && <TopikShablonBolimi token={token} />}
    </div>
  );
}

const QIYINLIK_DARAJALARI = [
  ["oson", "🟢 Oson"], ["o'rta", "🟡 O'rta"], ["qiyin", "🔴 Qiyin"], ["murakkab", "⚫ Murakkab"],
];

function TestShablonBolimi({ token }) {
  const [fanlar, setFanlar] = useState([]);
  const [ochiqFan, setOchiqFan] = useState(null);
  const [tanlanganKodlar, setTanlanganKodlar] = useState([]); // [topic_code, ...]
  const [guruhlar, setGuruhlar] = useState(
    QIYINLIK_DARAJALARI.map(([diff]) => ({ diff, turi: "single_choice", soni: 0 }))
  );
  const [yuklanmoqda, setYuklanmoqda] = useState(false);
  const [importlanmoqda, setImportlanmoqda] = useState(false);
  const [xato, setXato] = useState("");
  const [natija, setNatija] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/mavzular`)
      .then((r) => r.json())
      .then((d) => setFanlar(d.fanlar || []))
      .catch(() => setXato("Mavzularni yuklab bo'lmadi"));
  }, []);

  const kodniAlmashtir = (kod) => {
    setTanlanganKodlar((prev) => prev.includes(kod) ? prev.filter((k) => k !== kod) : [...prev, kod]);
  };

  const guruhniYangila = (diff, maydon, qiymat) => {
    setGuruhlar((prev) => prev.map((g) => g.diff === diff ? { ...g, [maydon]: qiymat } : g));
  };

  const jamiSon = guruhlar.reduce((sum, g) => sum + g.soni, 0);

  const shablonYukla = async () => {
    if (tanlanganKodlar.length === 0) { setXato("Kamida bitta mavzu tanlang"); return; }
    if (jamiSon === 0) { setXato("Kamida bitta qiyinlik darajasidan son tanlang"); return; }
    setYuklanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/shablon_yukla?token=${encodeURIComponent(token)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic_codes: tanlanganKodlar, guruhlar }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "Xato");
      }
      const blob = await res.blob();
      const dlUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = dlUrl; a.download = "test_shablon.xlsx";
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(dlUrl);
    } catch (e) {
      setXato(e.message);
    } finally { setYuklanmoqda(false); }
  };

  const faylTanlandi = async (e) => {
    const fayl = e.target.files[0];
    if (!fayl) return;
    setImportlanmoqda(true); setXato(""); setNatija(null);
    try {
      const formData = new FormData();
      formData.append("fayl", fayl);
      const res = await fetch(`${API_BASE}/api/admin/shablon_import?token=${encodeURIComponent(token)}`, {
        method: "POST", body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setNatija(data);
    } catch (e) {
      setXato(e.message);
    } finally {
      setImportlanmoqda(false);
      e.target.value = "";
    }
  };

  return (
    <>
      <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "#E5E1D8" }}>
        <label className="text-xs font-medium mb-2 block" style={{ color: "#5A5648" }}>
          1) Mavzu(lar)ni tanlang ({tanlanganKodlar.length} ta tanlandi)
        </label>
        <div className="space-y-1.5 max-h-56 overflow-y-auto mb-1">
          {fanlar.map((fan) => {
            const ochiq = ochiqFan === fan.qisqa;
            return (
              <div key={fan.qisqa} className="rounded-xl overflow-hidden" style={{ backgroundColor: "#F7F5F0" }}>
                <button onClick={() => setOchiqFan(ochiq ? null : fan.qisqa)}
                  className="w-full flex items-center justify-between px-3 py-2.5">
                  <span className="text-sm font-medium" style={{ color: "#2B2B2B" }}>{fan.nom}</span>
                  {ochiq ? <ChevronDown size={16} style={{ color: "#8A8578" }} /> : <ChevronRight size={16} style={{ color: "#8A8578" }} />}
                </button>
                {ochiq && (
                  <div className="px-3 pb-2.5 space-y-1">
                    {fan.sinflar.map((s) => (
                      <div key={s.sinf}>
                        <p className="text-xs font-medium py-1" style={{ color: "#8A8578" }}>{s.sinf}-sinf</p>
                        {s.mavzular.map((m) => (
                          <label key={m.topic_code} className="w-full flex items-center gap-2 px-2 py-2 rounded-lg bg-white mb-1 cursor-pointer">
                            <input type="checkbox" checked={tanlanganKodlar.includes(m.topic_code)}
                              onChange={() => kodniAlmashtir(m.topic_code)} />
                            <span className="text-sm flex-1" style={{ color: "#2B2B2B" }}>{m.nomi}</span>
                          </label>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "#E5E1D8" }}>
        <label className="text-xs font-medium mb-3 block" style={{ color: "#5A5648" }}>
          2) Har bir qiyinlik darajasi uchun son va turini tanlang
        </label>
        <div className="space-y-4">
          {guruhlar.map((g) => {
            const nom = QIYINLIK_DARAJALARI.find(([d]) => d === g.diff)[1];
            return (
              <div key={g.diff}>
                <p className="text-sm font-medium mb-1.5" style={{ color: "#2B2B2B" }}>{nom}</p>
                <div className="flex gap-1.5 mb-1.5 flex-wrap">
                  {[0, 5, 10, 15, 20].map((n) => (
                    <button key={n} onClick={() => guruhniYangila(g.diff, "soni", n)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium"
                      style={g.soni === n
                        ? { backgroundColor: "#1B4B7A", color: "#fff" }
                        : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>
                      {n}
                    </button>
                  ))}
                </div>
                <div className="flex gap-1.5">
                  <button onClick={() => guruhniYangila(g.diff, "turi", "single_choice")}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium"
                    style={g.turi === "single_choice"
                      ? { backgroundColor: "#2D8B8B", color: "#fff" }
                      : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>
                    🔘 Tugmali
                  </button>
                  <button onClick={() => guruhniYangila(g.diff, "turi", "write_answer")}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium"
                    style={g.turi === "write_answer"
                      ? { backgroundColor: "#2D8B8B", color: "#fff" }
                      : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>
                    ✍️ Yozuvli
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        <button onClick={shablonYukla} disabled={yuklanmoqda}
          className="w-full py-3 rounded-xl font-semibold text-white text-sm flex items-center justify-center gap-2 mt-5"
          style={{ backgroundColor: "#1B4B7A", opacity: yuklanmoqda ? 0.7 : 1 }}>
          {yuklanmoqda ? <Loader2 size={16} className="animate-spin" /> : `📥 Shablon yuklab olish (jami: ${jamiSon} ta × ${tanlanganKodlar.length} mavzu)`}
        </button>
      </div>

      <div className="rounded-2xl p-5 bg-white border" style={{ borderColor: "#E5E1D8" }}>
        <label className="text-xs font-medium mb-2 block" style={{ color: "#5A5648" }}>
          To'ldirilgan shablonni yuklash
        </label>
        <label className="w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 cursor-pointer border-2 border-dashed"
          style={{ borderColor: "#C4BFAF", color: "#5A5648" }}>
          {importlanmoqda ? <Loader2 size={16} className="animate-spin" /> : "📤 Fayl tanlash"}
          <input type="file" accept=".xlsx" onChange={faylTanlandi} disabled={importlanmoqda} className="hidden" />
        </label>

        {xato && <p className="text-sm mt-3" style={{ color: "#B0553A" }}>{xato}</p>}
        {natija && (
          <div className="mt-3 text-sm" style={{ color: "#2B2B2B" }}>
            <p>✅ Saqlandi: <b>{natija.saved}</b></p>
            <p>⚠️ Duplikat: <b>{natija.duplicates}</b></p>
            <p>❌ Xato: <b>{natija.errors}</b></p>
          </div>
        )}
      </div>
    </>
  );
}

function TopikShablonBolimi({ token }) {
  const [sinf, setSinf] = useState("");
  const [fan, setFan] = useState("");
  const [mavzular, setMavzular] = useState("");
  const [yuklanmoqda, setYuklanmoqda] = useState(false);
  const [importlanmoqda, setImportlanmoqda] = useState(false);
  const [xato, setXato] = useState("");
  const [natija, setNatija] = useState(null);

  const shablonYukla = async () => {
    if (!sinf.trim() || !fan.trim() || !mavzular.trim()) {
      setXato("Sinf, fan va mavzularni to'ldiring"); return;
    }
    setYuklanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/topik_shablon?token=${encodeURIComponent(token)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sinf: sinf.trim(), fan: fan.trim(), mavzular }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "Xato");
      }
      const blob = await res.blob();
      const dlUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = dlUrl; a.download = `shablon_${sinf}sinf_${fan}.xlsx`;
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(dlUrl);
    } catch (e) {
      setXato(e.message);
    } finally { setYuklanmoqda(false); }
  };

  const faylTanlandi = async (e) => {
    const fayl = e.target.files[0];
    if (!fayl) return;
    setImportlanmoqda(true); setXato(""); setNatija(null);
    try {
      const formData = new FormData();
      formData.append("fayl", fayl);
      const res = await fetch(`${API_BASE}/api/admin/topik_import?token=${encodeURIComponent(token)}`, {
        method: "POST", body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setNatija(data);
    } catch (e) {
      setXato(e.message);
    } finally {
      setImportlanmoqda(false);
      e.target.value = "";
    }
  };

  return (
    <>
      <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "#E5E1D8" }}>
        <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Sinf</label>
        <input type="text" value={sinf} onChange={(e) => setSinf(e.target.value)}
          placeholder="masalan: 1"
          className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
          style={{ borderColor: "#E5E1D8" }} />

        <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Fan</label>
        <input type="text" value={fan} onChange={(e) => setFan(e.target.value)}
          placeholder="masalan: Ingliz tili"
          className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
          style={{ borderColor: "#E5E1D8" }} />

        <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>
          Mavzular (har biri yangi qatorda: chorak / mavzu)
        </label>
        <textarea value={mavzular} onChange={(e) => setMavzular(e.target.value)}
          placeholder={"1 / Colours\n1 / Numbers\n2 / Animals"}
          rows={5}
          className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-4"
          style={{ borderColor: "#E5E1D8" }} />

        <button onClick={shablonYukla} disabled={yuklanmoqda}
          className="w-full py-3 rounded-xl font-semibold text-white text-sm flex items-center justify-center gap-2"
          style={{ backgroundColor: "#1B4B7A", opacity: yuklanmoqda ? 0.7 : 1 }}>
          {yuklanmoqda ? <Loader2 size={16} className="animate-spin" /> : "📥 Shablon yuklab olish"}
        </button>
      </div>

      <div className="rounded-2xl p-5 bg-white border" style={{ borderColor: "#E5E1D8" }}>
        <label className="text-xs font-medium mb-2 block" style={{ color: "#5A5648" }}>
          To'ldirilgan shablonni yuklash
        </label>
        <label className="w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 cursor-pointer border-2 border-dashed"
          style={{ borderColor: "#C4BFAF", color: "#5A5648" }}>
          {importlanmoqda ? <Loader2 size={16} className="animate-spin" /> : "📤 Fayl tanlash"}
          <input type="file" accept=".xlsx" onChange={faylTanlandi} disabled={importlanmoqda} className="hidden" />
        </label>

        {xato && <p className="text-sm mt-3" style={{ color: "#B0553A" }}>{xato}</p>}
        {natija && (
          <div className="mt-3 text-sm" style={{ color: "#2B2B2B" }}>
            <p>➕ Qo'shildi: <b>{natija.added}</b></p>
            <p>⏭ O'tkazildi: <b>{natija.skipped}</b></p>
          </div>
        )}
      </div>
    </>
  );
}

function OqituvchiTab({ token }) {
  const [holat, setHolat] = useState("togaraklar"); // togaraklar | azolar | yaratish
  const [togaraklar, setTogaraklar] = useState([]);
  const [tanlangan, setTanlangan] = useState(null);
  const [azolar, setAzolar] = useState([]);
  const [bahoQoyilayotgan, setBahoQoyilayotgan] = useState(null); // user_id | null
  const [bahoQiymati, setBahoQiymati] = useState("");
  const [izohQiymati, setIzohQiymati] = useState("");
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");

  const [yangiNomi, setYangiNomi] = useState("");
  const [yangiFan, setYangiFan] = useState("");
  const [yangiParol, setYangiParol] = useState("");
  const [yangiMaxTalaba, setYangiMaxTalaba] = useState("");
  const [yangiOylikSumma, setYangiOylikSumma] = useState("");
  const [yaratilmoqda, setYaratilmoqda] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/oqituvchi/togaraklar?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => { setTogaraklar(d.togaraklar || []); setYuklanmoqda(false); })
      .catch(() => { setXato("Yuklab bo'lmadi"); setYuklanmoqda(false); });
  }, [token]);

  const togarakOch = async (t) => {
    setYuklanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/togarak/${t.id}/azolar?token=${encodeURIComponent(token)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setAzolar(data.azolar || []);
      setTanlangan(t);
      setHolat("azolar");
    } catch (e) {
      setXato(e.message);
    } finally { setYuklanmoqda(false); }
  };

  const bahoBoshla = (azo) => {
    setBahoQoyilayotgan(azo.user_id);
    setBahoQiymati(azo.oxirgi_baho != null ? String(azo.oxirgi_baho) : "");
    setIzohQiymati("");
  };

  const bahoSaqla = async (userId) => {
    const baho = parseInt(bahoQiymati, 10);
    if (isNaN(baho) || baho < 0 || baho > 100) {
      setXato("Baho 0-100 oralig'ida bo'lishi kerak");
      return;
    }
    setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/baho_qoy`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, togarak_id: tanlangan.id, user_id: userId, baho, izoh: izohQiymati || null }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setAzolar((prev) => prev.map((a) => (a.user_id === userId ? { ...a, oxirgi_baho: baho } : a)));
      setBahoQoyilayotgan(null);
    } catch (e) {
      setXato(e.message);
    }
  };

  const yaratishSaqla = async () => {
    if (!yangiNomi.trim() || !yangiFan.trim()) {
      setXato("To'garak nomi va fan kiritilishi shart");
      return;
    }
    setYaratilmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/togarak_yarat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token, nomi: yangiNomi.trim(), fan: yangiFan.trim(),
          parol: yangiParol || undefined,
          max_talaba: yangiMaxTalaba ? parseInt(yangiMaxTalaba, 10) : undefined,
          oylik_summa: yangiOylikSumma ? parseInt(yangiOylikSumma, 10) : undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setTogaraklar((prev) => [...prev, { id: data.togarak_id, nomi: yangiNomi.trim(), fan: yangiFan.trim(), max_talaba: yangiMaxTalaba || null, azo_soni: 0 }]);
      setYangiNomi(""); setYangiFan(""); setYangiParol(""); setYangiMaxTalaba(""); setYangiOylikSumma("");
      setHolat("togaraklar");
    } catch (e) {
      setXato(e.message);
    } finally { setYaratilmoqda(false); }
  };

  if (yuklanmoqda) {
    return <div className="px-5 pt-16 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "#1B4B7A" }} /></div>;
  }

  if (holat === "yaratish") {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => setHolat("togaraklar")} className="text-sm mb-4" style={{ color: "#8A8578" }}>← Ortga</button>
        <h1 className="text-xl font-bold mb-1" style={{ color: "#2B2B2B" }}>Yangi to'garak</h1>
        <p className="text-sm mb-6" style={{ color: "#8A8578" }}>Bot va saytda bir xil ko'rinadi</p>

        <div className="rounded-2xl p-5 bg-white border" style={{ borderColor: "#E5E1D8" }}>
          <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>To'garak nomi</label>
          <input type="text" value={yangiNomi} onChange={(e) => setYangiNomi(e.target.value)}
            placeholder="masalan: Matematik to'garak"
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
            style={{ borderColor: "#E5E1D8" }} />

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Fan</label>
          <input type="text" value={yangiFan} onChange={(e) => setYangiFan(e.target.value)}
            placeholder="masalan: Matematika"
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
            style={{ borderColor: "#E5E1D8" }} />

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Qo'shilish paroli (ixtiyoriy)</label>
          <input type="text" value={yangiParol} onChange={(e) => setYangiParol(e.target.value)}
            placeholder="o'quvchilar shu bilan qo'shiladi"
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
            style={{ borderColor: "#E5E1D8" }} />

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Maks. talaba</label>
              <input type="number" min="1" value={yangiMaxTalaba} onChange={(e) => setYangiMaxTalaba(e.target.value)}
                placeholder="25"
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm"
                style={{ borderColor: "#E5E1D8" }} />
            </div>
            <div>
              <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Oylik (so'm)</label>
              <input type="number" min="0" value={yangiOylikSumma} onChange={(e) => setYangiOylikSumma(e.target.value)}
                placeholder="50000"
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm"
                style={{ borderColor: "#E5E1D8" }} />
            </div>
          </div>

          {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{xato}</p>}

          <button onClick={yaratishSaqla} disabled={yaratilmoqda}
            className="w-full py-3 rounded-xl font-semibold text-white text-sm flex items-center justify-center gap-2"
            style={{ backgroundColor: "#1B4B7A", opacity: yaratilmoqda ? 0.7 : 1 }}>
            {yaratilmoqda ? <Loader2 size={16} className="animate-spin" /> : "To'garak yaratish"}
          </button>
        </div>
      </div>
    );
  }

  if (holat === "azolar") {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => { setHolat("togaraklar"); setTanlangan(null); setBahoQoyilayotgan(null); }}
          className="text-sm mb-4" style={{ color: "#8A8578" }}>← Ortga</button>
        <h1 className="text-xl font-bold mb-5" style={{ color: "#2B2B2B" }}>{tanlangan.nomi}</h1>
        {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{xato}</p>}
        {azolar.length === 0 ? (
          <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "#E5E1D8" }}>
            <p className="text-sm" style={{ color: "#8A8578" }}>Bu to'garakda hali a'zo yo'q.</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {azolar.map((a) => (
              <div key={a.user_id} className="rounded-2xl bg-white border overflow-hidden" style={{ borderColor: "#E5E1D8" }}>
                <button onClick={() => (bahoQoyilayotgan === a.user_id ? setBahoQoyilayotgan(null) : bahoBoshla(a))}
                  className="w-full flex items-center justify-between px-4 py-3.5">
                  <span className="text-sm font-medium" style={{ color: "#2B2B2B" }}>{a.full_name}</span>
                  <span className="text-sm font-semibold" style={{ color: a.oxirgi_baho != null ? "#2D8B8B" : "#B0AA98" }}>
                    {a.oxirgi_baho != null ? `${a.oxirgi_baho}` : "Baholanmagan"}
                  </span>
                </button>
                {bahoQoyilayotgan === a.user_id && (
                  <div className="px-4 pb-4 pt-1 space-y-2.5">
                    <input type="number" min="0" max="100" value={bahoQiymati}
                      onChange={(e) => setBahoQiymati(e.target.value)}
                      placeholder="Baho (0-100)"
                      className="w-full px-3.5 py-2.5 rounded-xl border text-sm"
                      style={{ borderColor: "#E5E1D8" }} />
                    <input type="text" value={izohQiymati} onChange={(e) => setIzohQiymati(e.target.value)}
                      placeholder="Izoh (ixtiyoriy)"
                      className="w-full px-3.5 py-2.5 rounded-xl border text-sm"
                      style={{ borderColor: "#E5E1D8" }} />
                    <button onClick={() => bahoSaqla(a.user_id)}
                      className="w-full py-2.5 rounded-xl font-semibold text-white text-sm"
                      style={{ backgroundColor: "#1B4B7A" }}>
                      Saqlash
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // holat === "togaraklar"
  return (
    <div className="px-5 pt-6 pb-4">
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-2xl font-bold" style={{ color: "#2B2B2B" }}>Guruhlarim</h1>
        <button onClick={() => { setXato(""); setHolat("yaratish"); }}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-semibold text-white"
          style={{ backgroundColor: "#C89B3C" }}>
          + Yangi
        </button>
      </div>
      {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{xato}</p>}
      {togaraklar.length === 0 ? (
        <button onClick={() => { setXato(""); setHolat("yaratish"); }}
          className="w-full rounded-2xl p-8 text-center border-2 border-dashed"
          style={{ borderColor: "#C4BFAF" }}>
          <p className="text-sm font-medium mb-1" style={{ color: "#5A5648" }}>Hali to'garagingiz yo'q</p>
          <p className="text-xs" style={{ color: "#8A8578" }}>Bosib, birinchisini yarating</p>
        </button>
      ) : (
        <div className="space-y-2.5">
          {togaraklar.map((t) => (
            <button key={t.id} onClick={() => togarakOch(t)}
              className="w-full flex items-center justify-between px-4 py-4 rounded-2xl bg-white border text-left"
              style={{ borderColor: "#E5E1D8" }}>
              <div>
                <p className="text-sm font-semibold" style={{ color: "#2B2B2B" }}>{t.nomi}</p>
                <p className="text-xs mt-0.5" style={{ color: "#8A8578" }}>{t.fan}</p>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-full" style={{ backgroundColor: "#EAF1F7", color: "#1B4B7A" }}>
                {t.azo_soni} o'quvchi
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// 5.5) OTA-ONA — farzand(lar)ning bilim darajasi
// ═══════════════════════════════════════════════════════════
function OtaOnaTab({ foydalanuvchi }) {
  const [farzandlar, setFarzandlar] = useState([]);
  const [tanlanganBola, setTanlanganBola] = useState(null);
  const [bilimData, setBilimData] = useState(null);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/ota/${foydalanuvchi.user_id}/farzandlar`)
      .then((r) => r.json())
      .then((d) => {
        const royxat = d.farzandlar || [];
        setFarzandlar(royxat);
        if (royxat.length > 0) setTanlanganBola(royxat[0].user_id);
        else setYuklanmoqda(false);
      })
      .catch(() => { setXato("Farzandlar ro'yxatini yuklab bo'lmadi"); setYuklanmoqda(false); });
  }, [foydalanuvchi.user_id]);

  useEffect(() => {
    if (!tanlanganBola) return;
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/bola/${tanlanganBola}/bilim`)
      .then((r) => r.json())
      .then((d) => { setBilimData(d); setYuklanmoqda(false); })
      .catch(() => { setXato("Bilim ma'lumotini yuklab bo'lmadi"); setYuklanmoqda(false); });
  }, [tanlanganBola]);

  if (farzandlar.length === 0 && !yuklanmoqda) {
    return (
      <div className="px-5 pt-6 pb-4">
        <h1 className="text-2xl font-bold mb-5" style={{ color: "#2B2B2B" }}>Farzandim</h1>
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "#E5E1D8" }}>
          <p className="text-sm" style={{ color: "#8A8578" }}>
            Hozircha ulangan farzand yo'q. Farzandingizni botdagi kabinet orqali ulang.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {farzandlar.length > 1 && (
        <div className="px-5 pt-6 pb-2">
          <h1 className="text-2xl font-bold mb-4" style={{ color: "#2B2B2B" }}>Farzandim</h1>
          <div className="flex gap-2 flex-wrap">
            {farzandlar.map((f) => (
              <button key={f.user_id} onClick={() => setTanlanganBola(f.user_id)}
                className="px-4 py-2 rounded-full text-sm font-medium"
                style={tanlanganBola === f.user_id
                  ? { backgroundColor: "#1B4B7A", color: "#fff" }
                  : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>
                {f.full_name}
              </button>
            ))}
          </div>
        </div>
      )}
      {yuklanmoqda ? (
        <div className="px-5 pt-10 text-center">
          <Loader2 size={28} className="animate-spin mx-auto mb-3" style={{ color: "#1B4B7A" }} />
        </div>
      ) : xato ? (
        <p className="px-5 text-sm" style={{ color: "#B0553A" }}>{xato}</p>
      ) : (
        <BilimTab data={bilimData} />
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// 6) PROFIL — tahrirlash va rol almashtirish
// ═══════════════════════════════════════════════════════════
function ProfilTab({ token, foydalanuvchi, onYangilandi }) {
  const [ism, setIsm] = useState(foydalanuvchi?.full_name || "");
  const [viloyat, setViloyat] = useState(foydalanuvchi?.region || "");
  const [tuman, setTuman] = useState(foydalanuvchi?.district || "");
  const [tugilganSana, setTugilganYil] = useState(foydalanuvchi?.tugilgan_sana || "");
  const [maktabRaqami, setMaktabRaqami] = useState(foydalanuvchi?.maktab_raqami || "");
  const [maktabTuri, setMaktabTuri] = useState(foydalanuvchi?.maktab_turi_kaliti || "oddiy");
  const [sinf, setSinf] = useState(foydalanuvchi?.class ? String(foydalanuvchi.class).replace(/-sinf$/i, "") : "");
  const [sinfHarfi, setSinfHarfi] = useState(foydalanuvchi?.class_letter || "");
  const [saqlanmoqda, setSaqlanmoqda] = useState(false);
  const [xato, setXato] = useState("");
  const [muvaffaqiyat, setMuvaffaqiyat] = useState(false);
  const [rolTanlov, setRolTanlov] = useState(null);
  const [rolOzgartirilmoqda, setRolOzgartirilmoqda] = useState(false);
  const [rolSurishNatija, setRolSurishNatija] = useState(null); // {holat, qolgan_bepul, admin_test} | "yuklanmoqda" | null
  const [kodBosqichida, setKodBosqichida] = useState(false);
  const [kodEmail, setKodEmail] = useState("");
  const [kodQiymati, setKodQiymati] = useState("");
  const [kodYuklanmoqda, setKodYuklanmoqda] = useState(false);

  const [togaraklarim, setTogaraklarim] = useState([]);
  const [togaraklarYuklanmoqda, setTogaraklarYuklanmoqda] = useState(true);
  const [qoshilishParol, setQoshilishParol] = useState("");
  const [qoshilinmoqda, setQoshilinmoqda] = useState(false);
  const [qoshilishXato, setQoshilishXato] = useState("");
  const [qoshilishMuvaffaqiyat, setQoshilishMuvaffaqiyat] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/mening_togaraklarim?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => { setTogaraklarim(d.togaraklar || []); setTogaraklarYuklanmoqda(false); })
      .catch(() => setTogaraklarYuklanmoqda(false));
  }, [token]);

  const togarakkaQoshil = async () => {
    if (!qoshilishParol.trim()) return;
    setQoshilinmoqda(true); setQoshilishXato(""); setQoshilishMuvaffaqiyat("");
    try {
      const res = await fetch(`${API_BASE}/api/togarakka_qoshil`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, parol: qoshilishParol.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setTogaraklarim((prev) => [...prev, { id: Date.now(), nomi: data.togarak_nomi, fan: "" }]);
      setQoshilishMuvaffaqiyat(`"${data.togarak_nomi}" ga qo'shildingiz!`);
      setQoshilishParol("");
      setTimeout(() => setQoshilishMuvaffaqiyat(""), 3000);
    } catch (e) {
      setQoshilishXato(e.message);
    } finally { setQoshilinmoqda(false); }
  };

  const profilSaqla = async () => {
    setSaqlanmoqda(true); setXato(""); setMuvaffaqiyat(false);
    try {
      const res = await fetch(`${API_BASE}/api/profil`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token, full_name: ism, region: viloyat, district: tuman,
          tugilgan_sana: tugilganSana || undefined,
          maktab_raqami: maktabRaqami || undefined,
          maktab_turi: foydalanuvchi?.role === "oquvchi" ? maktabTuri : undefined,
          sinf: foydalanuvchi?.role === "oquvchi" && sinf ? sinf : undefined,
          sinf_harfi: foydalanuvchi?.role === "oquvchi" && sinfHarfi ? sinfHarfi : undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      onYangilandi({
        ...foydalanuvchi, full_name: ism, region: viloyat, district: tuman,
        tugilgan_sana: tugilganSana, maktab_raqami: maktabRaqami,
        maktab_turi_kaliti: maktabTuri, class: sinf, class_letter: sinfHarfi,
      });
      setMuvaffaqiyat(true);
      setTimeout(() => setMuvaffaqiyat(false), 2500);
    } catch (e) {
      setXato(e.message);
    } finally { setSaqlanmoqda(false); }
  };

  const rolModalniYop = () => {
    setRolTanlov(null); setRolSurishNatija(null); setKodBosqichida(false);
    setKodQiymati(""); setKodEmail(""); setXato("");
  };

  // Rol tugmasi bosilganda — darhol o'zgartirmaymiz, avval holatni so'raymiz
  // (nechta bepul imkoniyat qolgani, yoki kod kerakligini bilish uchun).
  const rolTanlandi = async (v) => {
    if (v === foydalanuvchi?.role) return;
    setRolTanlov(v);
    setRolSurishNatija("yuklanmoqda");
    setKodBosqichida(false); setKodQiymati(""); setKodEmail(""); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/rol_ozgartir`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, yangi_rol: v, tasdiqlayman: false }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setRolSurishNatija(data);
      if (data.holat === "kod_kerak") setKodBosqichida(true);
    } catch (e) {
      setXato(e.message); setRolTanlov(null); setRolSurishNatija(null);
    }
  };

  const rolTasdiqla = async () => {
    setRolOzgartirilmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/rol_ozgartir`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, yangi_rol: rolTanlov, tasdiqlayman: true }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      if (data.holat === "kod_kerak") {
        setKodBosqichida(true);
        await kodSora();
      } else {
        onYangilandi({ ...foydalanuvchi, role: rolTanlov });
        rolModalniYop();
      }
    } catch (e) {
      setXato(e.message);
    } finally { setRolOzgartirilmoqda(false); }
  };

  const kodSora = async () => {
    setKodYuklanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/rol_kod_yubor`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, yangi_rol: rolTanlov }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      if (data.holat === "smtp_sozlanmagan") setXato("Email yuborish hozircha sozlanmagan — administratorga murojaat qiling");
      else setKodEmail(data.email);
    } catch (e) {
      setXato(e.message);
    } finally { setKodYuklanmoqda(false); }
  };

  const kodTasdiqla = async () => {
    if (!kodQiymati.trim()) return;
    setRolOzgartirilmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/rol_kod_tasdiqla`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, kod: kodQiymati.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      onYangilandi({ ...foydalanuvchi, role: data.yangi_rol });
      rolModalniYop();
    } catch (e) {
      setXato(e.message);
    } finally { setRolOzgartirilmoqda(false); }
  };

  const rolNomlari = { oquvchi: "O'quvchi", "ota-ona": "Ota-ona", oqituvchi: "O'qituvchi" };

  return (
    <div className="px-5 pt-6 pb-4">
      <h1 className="text-2xl font-bold mb-5" style={{ color: "#2B2B2B" }}>Profil</h1>

      <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "#E5E1D8" }}>
        <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Ism</label>
        <input type="text" value={ism} onChange={(e) => setIsm(e.target.value)}
          className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
          style={{ borderColor: "#E5E1D8" }} />

        <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Viloyat</label>
        <select value={viloyat} onChange={(e) => { setViloyat(e.target.value); setTuman(""); }}
          className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
          style={{ borderColor: "#E5E1D8" }}>
          <option value="">Tanlanmagan</option>
          {VILOYATLAR.map((v) => <option key={v} value={v}>{v}</option>)}
        </select>

        {viloyat && (
          <>
            <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Tuman</label>
            <select value={tuman} onChange={(e) => setTuman(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
              style={{ borderColor: "#E5E1D8" }}>
              <option value="">Tanlanmagan</option>
              {(HUDUDLAR[viloyat] || []).map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </>
        )}

        <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Tug'ilgan sana</label>
        <input type="date" value={tugilganSana} onChange={(e) => setTugilganYil(e.target.value)}
          min="1950-01-01" max={new Date().toISOString().split("T")[0]}
          className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
          style={{ borderColor: "#E5E1D8" }} />

        {foydalanuvchi?.role === "oquvchi" && (
          <>
            <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Maktab raqami</label>
            <input type="text" value={maktabRaqami} onChange={(e) => setMaktabRaqami(e.target.value)}
              placeholder="masalan: 21"
              className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-4"
              style={{ borderColor: "#E5E1D8" }} />

            <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Maktab turi</label>
            <div className="grid grid-cols-2 gap-2 mb-4">
              {[
                ["oddiy", "🏫 Oddiy davlat"], ["xususiy", "🏢 Xususiy"],
                ["ixtisoslashgan", "⭐ Ixtisoslashgan (IDUM)"], ["prezident", "🏆 Prezident maktabi"],
              ].map(([kalit, nom]) => (
                <button key={kalit} type="button" onClick={() => setMaktabTuri(kalit)}
                  className="py-2.5 rounded-lg border text-xs font-medium text-center"
                  style={{
                    borderColor: maktabTuri === kalit ? "#1B4B7A" : "#E5E1D8",
                    backgroundColor: maktabTuri === kalit ? "#1B4B7A" : "#FFFFFF",
                    color: maktabTuri === kalit ? "#FFFFFF" : "#5A5648",
                  }}>
                  {nom}
                </button>
              ))}
            </div>

            <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Sinf</label>
            <div className="grid grid-cols-6 gap-1.5 mb-3">
              {Array.from({ length: 11 }, (_, i) => String(i + 1)).map((n) => (
                <button key={n} type="button" onClick={() => setSinf(n)}
                  className="py-2.5 rounded-lg border text-sm font-semibold text-center"
                  style={{
                    borderColor: sinf === n ? "#1B4B7A" : "#E5E1D8",
                    backgroundColor: sinf === n ? "#1B4B7A" : "#FFFFFF",
                    color: sinf === n ? "#FFFFFF" : "#5A5648",
                  }}>
                  {n}
                </button>
              ))}
            </div>

            <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Sinf harfi (ixtiyoriy)</label>
            <input type="text" value={sinfHarfi} onChange={(e) => setSinfHarfi(e.target.value.slice(0, 1).toUpperCase())}
              placeholder="masalan: A"
              className="w-24 px-3.5 py-2.5 rounded-xl border text-sm mb-4 text-center"
              style={{ borderColor: "#E5E1D8" }} />
          </>
        )}

        {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{xato}</p>}
        {muvaffaqiyat && <p className="text-sm mb-3" style={{ color: "#3B6D11" }}>✓ Saqlandi</p>}

        <button onClick={profilSaqla} disabled={saqlanmoqda}
          className="w-full py-3 rounded-xl font-semibold text-white text-sm"
          style={{ backgroundColor: "#1B4B7A", opacity: saqlanmoqda ? 0.7 : 1 }}>
          {saqlanmoqda ? "Saqlanmoqda..." : "Saqlash"}
        </button>
      </div>

      <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "#E5E1D8" }}>
        <p className="text-xs font-medium mb-3" style={{ color: "#5A5648" }}>Mening to'garaklarim</p>

        {togaraklarYuklanmoqda ? (
          <Loader2 size={18} className="animate-spin" style={{ color: "#1B4B7A" }} />
        ) : togaraklarim.length === 0 ? (
          <p className="text-sm mb-4" style={{ color: "#8A8578" }}>Hali hech qaysi to'garakka qo'shilmagansiz.</p>
        ) : (
          <div className="flex flex-wrap gap-2 mb-4">
            {togaraklarim.map((t) => (
              <span key={t.id} className="text-xs px-3 py-1.5 rounded-full font-medium"
                style={{ backgroundColor: "#EAF1F7", color: "#1B4B7A" }}>
                {t.nomi}
              </span>
            ))}
          </div>
        )}

        <label className="text-xs font-medium mb-1.5 block" style={{ color: "#5A5648" }}>Parol bilan qo'shilish</label>
        <div className="flex gap-2">
          <input type="text" value={qoshilishParol} onChange={(e) => setQoshilishParol(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && togarakkaQoshil()}
            placeholder="to'garak paroli"
            className="flex-1 px-3.5 py-2.5 rounded-xl border text-sm"
            style={{ borderColor: "#E5E1D8" }} />
          <button onClick={togarakkaQoshil} disabled={qoshilinmoqda}
            className="px-4 py-2.5 rounded-xl font-semibold text-white text-sm shrink-0"
            style={{ backgroundColor: "#C89B3C", opacity: qoshilinmoqda ? 0.7 : 1 }}>
            {qoshilinmoqda ? "..." : "Qo'shilish"}
          </button>
        </div>
        {qoshilishXato && <p className="text-sm mt-2" style={{ color: "#B0553A" }}>{qoshilishXato}</p>}
        {qoshilishMuvaffaqiyat && <p className="text-sm mt-2" style={{ color: "#3B6D11" }}>✓ {qoshilishMuvaffaqiyat}</p>}
      </div>

      <div className="rounded-2xl p-5 bg-white border" style={{ borderColor: "#E5E1D8" }}>
        <p className="text-xs font-medium mb-2" style={{ color: "#5A5648" }}>Rolingiz</p>
        <div className="grid grid-cols-3 gap-2">
          {Object.entries(rolNomlari).map(([v, l]) => (
            <button key={v} onClick={() => rolTanlandi(v)}
              className="py-2.5 rounded-lg border text-xs font-medium"
              style={{
                borderColor: foydalanuvchi?.role === v ? "#1B4B7A" : "#E5E1D8",
                backgroundColor: foydalanuvchi?.role === v ? "#1B4B7A" : "#FFFFFF",
                color: foydalanuvchi?.role === v ? "#FFFFFF" : "#5A5648",
              }}>
              {l}
            </button>
          ))}
        </div>
      </div>

      {rolTanlov && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-6" style={{ backgroundColor: "rgba(0,0,0,0.4)" }}>
          <div className="w-full max-w-sm rounded-2xl p-5" style={{ backgroundColor: "#FFFFFF" }}>
            {rolSurishNatija === "yuklanmoqda" ? (
              <div className="py-4 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "#1B4B7A" }} /></div>
            ) : kodBosqichida ? (
              <>
                <p className="font-semibold mb-2" style={{ color: "#2B2B2B" }}>📧 Tasdiqlash kodi kerak</p>
                <p className="text-sm mb-4" style={{ color: "#5A5648" }}>
                  Bepul rol almashtirish imkoniyatingiz tugagan. "{rolNomlari[rolTanlov]}"ga o'zgartirish uchun
                  Gmail hisobingizga ({kodEmail || "..."}) yuborilgan 6 xonali kodni kiriting.
                </p>
                {kodYuklanmoqda ? (
                  <div className="py-2 text-center"><Loader2 size={20} className="animate-spin mx-auto" style={{ color: "#1B4B7A" }} /></div>
                ) : (
                  <>
                    <input type="text" value={kodQiymati} onChange={(e) => setKodQiymati(e.target.value.replace(/\D/g, "").slice(0, 6))}
                      placeholder="123456" maxLength={6}
                      className="w-full px-3.5 py-2.5 rounded-xl border text-center text-lg tracking-widest mb-3"
                      style={{ borderColor: "#E5E1D8" }} />
                    <button onClick={kodSora} className="text-xs mb-4" style={{ color: "#1B4B7A" }}>Kodni qayta yuborish</button>
                  </>
                )}
                {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{xato}</p>}
                <div className="flex gap-2.5">
                  <button onClick={rolModalniYop}
                    className="flex-1 py-2.5 rounded-xl border text-sm font-medium" style={{ borderColor: "#E5E1D8", color: "#5A5648" }}>
                    Bekor qilish
                  </button>
                  <button onClick={kodTasdiqla} disabled={rolOzgartirilmoqda || !kodQiymati.trim()}
                    className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white"
                    style={{ backgroundColor: "#1B4B7A", opacity: (rolOzgartirilmoqda || !kodQiymati.trim()) ? 0.6 : 1 }}>
                    {rolOzgartirilmoqda ? "..." : "Tasdiqlash"}
                  </button>
                </div>
              </>
            ) : (
              <>
                <p className="font-semibold mb-2" style={{ color: "#2B2B2B" }}>⚠️ Rolni o'zgartirasizmi?</p>
                <p className="text-sm mb-3" style={{ color: "#5A5648" }}>
                  Rolingiz "{rolNomlari[rolTanlov]}"ga o'zgaradi. Bu ko'rinadigan ma'lumot va imkoniyatlaringizga
                  butunlay ta'sir qiladi — masalan o'quvchi test/bilim ma'lumotlari, o'qituvchi guruhlari.
                </p>
                {rolSurishNatija?.admin_test ? (
                  <p className="text-xs mb-5 font-medium" style={{ color: "#2D8B8B" }}>
                    ✓ Admin sifatida cheklovsiz sinab ko'rishingiz mumkin.
                  </p>
                ) : (
                  <p className="text-xs mb-5 font-semibold p-3 rounded-xl" style={{ color: "#8A5A1C", backgroundColor: "#FDF3E3" }}>
                    DIQQAT: rolni FAQAT 2 marta bepul o'zgartirish mumkin. Sizda {rolSurishNatija?.qolgan_bepul ?? "?"} ta
                    bepul imkoniyat qoldi. Shundan keyin har safar Gmail orqali tasdiqlash kodi va 30 kunlik kutish talab qilinadi.
                  </p>
                )}
                {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{xato}</p>}
                <div className="flex gap-2.5">
                  <button onClick={rolModalniYop}
                    className="flex-1 py-2.5 rounded-xl border text-sm font-medium" style={{ borderColor: "#E5E1D8", color: "#5A5648" }}>
                    Bekor qilish
                  </button>
                  <button onClick={rolTasdiqla} disabled={rolOzgartirilmoqda}
                    className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ backgroundColor: "#1B4B7A" }}>
                    {rolOzgartirilmoqda ? "..." : "Tasdiqlash"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function PastkiMenyu({ faol, onTanlash, rol, isAdmin }) {
  const bandlar = [
    ...(rol === "oqituvchi"
      ? [{ kalit: "oqituvchi", nom: "Guruhlarim", ikon: Users }]
      : rol === "ota-ona"
      ? [{ kalit: "farzand", nom: "Farzandim", ikon: Heart }]
      : [
          { kalit: "bilim", nom: "Bilim", ikon: BarChart3 },
          { kalit: "test", nom: "Test", ikon: PencilLine },
        ]),
    ...(isAdmin ? [{ kalit: "admin", nom: "Shablon", ikon: FileSpreadsheet }] : []),
    { kalit: "xabar", nom: "Xabarlar", ikon: Bell },
    { kalit: "profil", nom: "Profil", ikon: User },
  ];
  return (
    <nav className="fixed bottom-0 inset-x-0 z-30 border-t" style={{ backgroundColor: "rgba(255,255,255,0.97)", borderColor: "#E5E1D8" }}>
      <div className="max-w-md mx-auto grid" style={{ gridTemplateColumns: `repeat(${bandlar.length}, minmax(0, 1fr))` }}>
        {bandlar.map(({ kalit, nom, ikon: Ikon }) => {
          const aktiv = faol === kalit;
          return (
            <button key={kalit} onClick={() => onTanlash(kalit)} className="flex flex-col items-center gap-1 py-3 transition-colors">
              <Ikon size={22} strokeWidth={aktiv ? 2.5 : 2} style={{ color: aktiv ? "#1B4B7A" : "#8A8578" }} />
              <span className="text-xs" style={{ color: aktiv ? "#1B4B7A" : "#8A8578", fontWeight: aktiv ? 600 : 400 }}>{nom}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

function Kabinet({ token }) {
  const [holat, setHolat] = useState("yuklanmoqda");
  const [foydalanuvchi, setFoydalanuvchi] = useState(null);
  const [bilimData, setBilimData] = useState(null);
  const [tab, setTab] = useState(null); // rol aniqlangach o'rnatiladi
  const [xatoMatn, setXatoMatn] = useState("");

  useEffect(() => {
    async function yukla() {
      try {
        const resU = await fetch(`${API_BASE}/auth/men?token=${encodeURIComponent(token)}`);
        if (!resU.ok) throw new Error("Sessiya eskirgan");
        const u = await resU.json();
        setFoydalanuvchi(u);

        // Faqat O'QUVCHI (yoki rol hali tanlanmagan) uchun o'zining bilim
        // ma'lumotini yuklaymiz — o'qituvchi/ota-ona uchun bu ma'lumot mos emas.
        if (!u.role || u.role === "oquvchi") {
          const resB = await fetch(`${API_BASE}/api/bola/${u.user_id}/bilim`);
          const b = await resB.json();
          setBilimData(b);
        }

        // Har rol o'ziga mos boshlang'ich sahifadan boshlaydi
        if (u.role === "oqituvchi") setTab("oqituvchi");
        else if (u.role === "ota-ona") setTab("farzand");
        else setTab("bilim");

        setHolat("tayyor");
      } catch (e) {
        setXatoMatn(e.message);
        setHolat("xato");
      }
    }
    yukla();
  }, [token]);

  if (holat === "yuklanmoqda") {
    return <Qobiq><div className="text-center"><Loader2 size={28} className="animate-spin mx-auto mb-3" style={{ color: "#1B4B7A" }} /><p className="text-sm" style={{ color: "#8A8578" }}>Yuklanmoqda...</p></div></Qobiq>;
  }
  if (holat === "xato") {
    return <Qobiq><div className="text-center"><WifiOff size={28} className="mx-auto mb-3" style={{ color: "#B0553A" }} /><p className="text-sm" style={{ color: "#B0553A" }}>{xatoMatn}</p></div></Qobiq>;
  }

  return (
    <div className="min-h-screen pb-20" style={{ backgroundColor: "#F7F5F0", fontFamily: "'Inter', system-ui, sans-serif" }}>
      {tab === "bilim" && <BilimTab data={bilimData} />}
      {tab === "test" && <TestTab token={token} sinf={foydalanuvchi?.is_admin ? null : foydalanuvchi?.class} />}
      {tab === "oqituvchi" && foydalanuvchi?.role === "oqituvchi" && <OqituvchiTab token={token} />}
      {tab === "farzand" && foydalanuvchi?.role === "ota-ona" && <OtaOnaTab foydalanuvchi={foydalanuvchi} />}
      {tab === "admin" && foydalanuvchi?.is_admin && <AdminTab token={token} />}
      {tab === "xabar" && (
        <div className="px-5 pt-6"><h1 className="text-2xl font-bold mb-5" style={{ color: "#2B2B2B" }}>Bildirishnomalar</h1>
          <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "#E5E1D8" }}><p className="text-sm" style={{ color: "#8A8578" }}>Tez orada.</p></div></div>
      )}
      {tab === "profil" && <ProfilTab token={token} foydalanuvchi={foydalanuvchi} onYangilandi={setFoydalanuvchi} />}
      <PastkiMenyu faol={tab} onTanlash={setTab} rol={foydalanuvchi?.role} isAdmin={foydalanuvchi?.is_admin} />
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// ASOSIY — URL manziliga qarab qaysi ekranni ko'rsatishni hal qiladi
// ═══════════════════════════════════════════════════════════
export default function App() {
  const [token, setToken] = useState(null);
  const [yol] = useState(() => {
    const p = window.location.pathname;
    const q = new URLSearchParams(window.location.search);
    return { p, token: q.get("token"), email: q.get("email"), ism: q.get("ism") };
  });

  if (token) return <Kabinet token={token} />;
  if (yol.p === "/kabinet" && yol.token) return <Kabinet token={yol.token} />;
  if (yol.p === "/ulash" && yol.email) return <UlashEkrani email={yol.email} ism={yol.ism} onUlandi={setToken} />;
  return <LoginEkrani />;
}
