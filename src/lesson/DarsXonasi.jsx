import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { uiText as __kbUi } from "../interface/interfaceRuntime.js";
import { useInterface as useKbInterfaceLocale } from "../interface/InterfacePreferences.jsx";
import AmaliyDoska, { BoardText } from "./AmaliyDoska.jsx";
import { boardCues, checkAnswer, lessonDownloadUrl, sceneRange, speakableText, visibleLines } from "./darsXonasiRules.js";
import { stripSpeechTags } from "../speech/language.js";
import { contentLanguage, dropPraiseAny, kidCorrectSpeech, kidOptions, kidPraise } from "../test/kidQuizRules.js";
import { lessonAudience, audienceLabels } from "./lessonAudience.js";
import { markLessonDone } from "../curriculum/kidProgress.js";
import { KID_PITCH, kidRate, ustozRate, kidRepeatSpeech, kidTakrorStep, kidTaskModel, ismOldin } from "./kidLessonRules.js";
import { APP_VERSION } from "../appVersion.js";
import { answerSpeed, finishLesson, kidTracker, startLesson } from "../kid/kidActivity.js";
import { screenTime } from "../kid/screenTime.js";
import { LIP_STEP, loadEnvelope } from "../kid/lipSync.js";
import { ustozNutqi } from "../kid/ustozNutqi.js";
import KidStage from "../kid/KidStage.jsx";
import UstozSahna from "../kid/UstozSahna.jsx";
import { useKeepLight } from "../kid/useKeepLight.js";
import { havoTuri, quyoshVaqti, ustozFor } from "../kid/ustozRules.js";
import { darsSozlari, ochilish } from "../kid/darsOchilishi.js";
import { darsIzohi, darsTiliIzoh, gap, izohTeg } from "../kid/izohTil.js";
import { bilganSozlar, eslab, oxirgiDars } from "../kid/sozBoyligi.js";
import { suhbatSavollari } from "../kid/suhbat.js";
import { boardCards, cardSize, emojiPictures, gameTargets, lessonWords, isReviewQuestion, kabuMood, kabuSpeech, kidStars, kindBadge, kindCue, pictureFor, questionCard, stepActions, stepKind, stickerKeys, darsBoshi, matnRasmlari } from "../kid/kidStageRules.js";
import { stickerUrl } from "../kid/stickers.js";
import { keycapNumber, kidOptionPic } from "../kid/optionPic.js";
import { emojiRasm, harakatTuri, sozId } from "../kid/rasmHarakat.js";
import { RASMLAR } from "../kid/xonalar/rasmlar.js";
import { beep, chime, pop, soft } from "../kid/kidSounds.js";
import VoiceCheck from "./VoiceCheck.jsx";
import { voiceCheckItems } from "./voiceCheckRules.js";
import { speechRecognitionAvailable } from "../speech/speakRules.js";
import { aralashKerak, aralashOqi, qurilmadaOqi, reja as ovozReja } from "../speech/aralashOvoz.js";
import { aytdiMi, sozBolaklari, tingla } from "./sozAytish.js";
import "./dars-xonasi.css";

/** REV90: bog'cha boshqaruv tugmasi — katta belgi, ostida kichik yozuv (o'qiy olmaydigan bola belgidan taniydi). */
function KidIcon({ icon, label }) {
  return <><span className="dx-kid-ico" aria-hidden="true">{icon}</span><small className="dx-kid-cap">{__kbUi(label)}</small></>;
}

function TeacherAvatar() {
  return <svg viewBox="0 0 64 64" width="60" height="60" aria-hidden="true">
    <rect width="64" height="64" fill="#E6ECE9" />
    <path d="M12 64c2-12 10-18 20-18s18 6 20 18z" fill="#2F5F7A" />
    <path d="M27 44h10v6H27z" fill="#E7B894" />
    <ellipse cx="32" cy="30" rx="12" ry="14" fill="#F0C6A2" />
    <path d="M19 27c0-10 6-15 13-15s13 5 13 15c-3-5-8-7-13-7s-10 2-13 7z" fill="#3B2A22" />
    <circle cx="27.5" cy="30" r="1.6" fill="#1C2926" /><circle cx="36.5" cy="30" r="1.6" fill="#1C2926" />
    <rect x="23.5" y="27.5" width="8" height="5.5" rx="2" fill="none" stroke="#1C2926" strokeWidth=".9" />
    <rect x="32.5" y="27.5" width="8" height="5.5" rx="2" fill="none" stroke="#1C2926" strokeWidth=".9" />
    <ellipse className="dx-mouth" cx="32" cy="38" rx="3.4" ry="1.8" fill="#9C4A3F" />
  </svg>;
}

export default function DarsXonasi({ apiBase, token, topicCode, fan = "", grade = "", jins = "qiz", learnerGender = "", learnerRole = "", nextLesson = null, oldingiKod = "", onOpenTest, onOpenTopic, onChat, kidPlan = null, onKidFinished, onClose, cheklovsiz = false }) {
  useKbInterfaceLocale();
  const [lesson, setLesson] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [idx, setIdx] = useState(-1);
  const [mode, setMode] = useState("idle"); // idle | lesson | test | result
  const [playing, setPlaying] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [bubble, setBubble] = useState("");
  const [word, setWord] = useState(-1);
  const [stepFinished, setStepFinished] = useState(true);
  const [rate, setRate] = useState(1);
  const [menu, setMenu] = useState(false);
  const [variant, setVariant] = useState(null);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [askReply, setAskReply] = useState("");
  const [testIndex, setTestIndex] = useState(0);
  const [picked, setPicked] = useState(null);
  const [score, setScore] = useState(0);
  // REV91: bog'cha — savol variantlari birma-bir aytiladi (aytilayotgani qimirlaydi), keyin hammasi kutadi.
  const [hot, setHot] = useState(-1);
  const [waiting, setWaiting] = useState(false);
  const [limitText, setLimitText] = useState("");
  const [limitKind, setLimitKind] = useState("");
  const [kidResult, setKidResult] = useState(null);
  // REV121: «Top-chi» o'yini — ustoz so'zni aytadi va bola bosishini KUTADI; to'g'ri (birinchi urinishda) — yulduz,
  // xato yoki bosmasa — yulduz yo'q. game: { stepIdx, targets, holat, kutish } · natijalar har o'yin qadami bo'yicha.
  const [game, setGame] = useState(null);
  const gameRef = useRef(null);
  const gameTimer = useRef(0);
  const gameRes = useRef({});
  const [gameScore, setGameScore] = useState(0);
  const [gameTotal, setGameTotal] = useState(0);
  // REV105: dars oxirida ovozli tekshiruv («Takrorlang!») — natija {togri, jami} yoki null.
  const [voice, setVoice] = useState(null);
  // REV110: derazadagi ob-havo (dars boshida serverdan keladi; kelguncha — fasl bo'yicha)
  const [havo, setHavo] = useState(() => havoTuri());
  const [harorat, setHarorat] = useState(null);
  const [shamol, setShamol] = useState(false);
  const [vaqt, setVaqt] = useState(() => quyoshVaqti());
  const voiceRef = useRef(null);
  voiceRef.current = voice;
  // REV98: robot Kabu — quvonish/dalda holati va sakrash; rasmni bosganda qayta jonlanadi.
  const [kidPhase, setKidPhase] = useState("");
  const [celebrate, setCelebrate] = useState(0);
  const [picRev, setPicRev] = useState(0);
  // REV145: til darsida yangi so'z o'rgatilganda bola uni mikrofonga bir marta aytadi (2 urinish)
  const [mikSoz, setMikSoz] = useState(null);   // { phrase, lang, holat: tingla | ok | yana | no }
  const mikRef = useRef(null);                  // hozirgi tinglash (stop)
  const mikYoq = useRef(false);                 // ruxsat yo'q / mikrofon yo'q / bola ikki marta jim — dars oxirigacha so'ralmaydi
  const sorilgan = useRef(new Set());           // shu darsda so'ralgan so'zlar — bir so'z bir marta
  const jimSanoq = useRef(0);
  const qadamRef = useRef(0);
  const aytganlar = useRef({});                 // so'z (kichik harf) → true (to'g'ri aytdi) | false (urindi, chiqmadi)
  const phaseTimer = useRef(0);
  const audioRef = useRef(null);
  // REV122: og'iz ovozga mos — {lv: konvert, audio} ; fallback — so'zlar jim yonganda oddiy ritm
  const lipRef = useRef(null);
  const fallbackTalk = useRef(false);
  const aralashRef = useRef(null);   // REV139: o'zbekcha — server, chet tili — brauzer ovozi
  const sozTimer = useRef(null);
  const kidRef = useRef(false);
  const gradeRef = useRef("");
  const tokenRef = useRef(0);
  const playingRef = useRef(false);
  playingRef.current = playing;
  const speakingRef = useRef(false);
  speakingRef.current = speaking;
  const modeRef = useRef(mode);
  modeRef.current = mode;
  const idxRef = useRef(idx);
  idxRef.current = idx;
  const rateRef = useRef(rate);
  rateRef.current = rate;
  const prefetched = useRef(new Set());
  // REV103: savolga javob vaqti (ota-onaga «tezlik» ko'rsatkichi): savol o'qilib, variantlar ko'rsatilgandan — bosilgunicha.
  const questionDone = useRef(0);
  const askedAt = useRef(0);
  const answerTimes = useRef([]);

  // REV80: dars maydoni tinglovchiga moslashadi — bog'cha bolasi, o'quvchi, talaba.
  const audience = lessonAudience(learnerRole, grade || lesson?.topic?.sinf);
  const kid = audience === "bogcha";
  kidRef.current = kid;
  // REV122: kim gapiryapti — sinfxonada (kutish, dars, ko'prik) jonli ustoz, test/ovoz ekranida robot Kabu
  const ustozRef = useRef("nilufar");
  ustozRef.current = ustozFor(fan || lesson?.topic?.fan);
  const ustozGapiryapti = () => ["idle", "lesson", "bridge"].includes(modeRef.current);
  useKeepLight(kid);   // REV121: tungi rejimda ham bolalar darsi yorqin
  gradeRef.current = grade || lesson?.topic?.sinf || "";
  const labels = audienceLabels(audience);
  const theme = learnerGender === "qiz" ? "girl" : learnerGender === "ogil" ? "boy" : "neutral";
  // REV110: bog'chada dars ustozning o'z salomi, bugungi ob-havo va o'tgan darsdan savol bilan boshlanadi.
  // REV130: dars boshida faqat O'TGAN mavzu (ro'yxatdagi oldingi dars) takrorlanadi — boshqa fandan yoki eski darsdan emas.
  const boshi = useMemo(() => (kid ? darsBoshi(lesson?.steps || [], lesson?.topic?.mavzu || "") : { takror: [], qolgan: lesson?.steps || [] }), [kid, lesson]);
  const oldingi = useMemo(() => {
    if (!lesson || boshi.takror.length || !oldingiKod) return null;   // miyada o'tgan mavzu takrori bo'lsa — o'shasi yetadi
    const o = oxirgiDars(topicCode);
    return o && o.code === oldingiKod ? o : null;
  }, [lesson, topicCode, oldingiKod, boshi]);
  // REV111: miya qaysi tilda tushuntirilgan (o'zbek / rus / ingliz) va qaysi til o'rgatiladi
  const izoh = useMemo(() => darsIzohi(lesson?.steps || [], fan || lesson?.topic?.fan || ""), [lesson, fan]);
  const izohRef = useRef("uz");
  izohRef.current = izoh;
  // REV121: matematika / atrof-muhit / mantiq — til darsi emas (rus izohidagi teglar «o'rganiladigan til» emas)
  const darsTil = useMemo(() => darsTiliIzoh(lesson?.steps || [], izoh, fan || lesson?.topic?.fan || ""), [lesson, izoh, fan]);
  const opening = useMemo(() => (kid && lesson?.steps?.length ? ochilish({
    ustoz: ustozFor(fan || lesson?.topic?.fan), til: darsTil, izoh, havo, harorat, oldingi, vaqt,
    grade: grade || lesson?.topic?.sinf, kun: Math.floor(Date.now() / 86400000),
  }) : []), [kid, lesson, havo, harorat, oldingi, fan, grade, darsTil, izoh, vaqt]);
  const steps = useMemo(() => [...opening, ...boshi.takror, ...boshi.qolgan], [opening, boshi]);
  const step = idx >= 0 ? steps[idx] : null;
  // REV102: har qadam turi — takror (o'tgan darslar) yoki yangi bilim; bolaga belgi, rang va ovoz bilan ko'rsatiladi.
  const kinds = useMemo(() => steps.reduce((out, s, i) => {
    // uzun tushuntirish bo'laklarga bo'linsa, keyingi bo'lak sarlavhasiz keladi — oldingisining turini oladi
    const prev = steps[i - 1];
    out.push(prev && !s.sarlavha && s.sahna && s.sahna === prev.sahna ? out[i - 1] : stepKind(s, lesson?.topic?.mavzu));
    return out;
  }, []), [steps, lesson]);
  // Shu darsda o'rgatiladigan yangi so'zlarning rasmlari — o'yin qadamida o'tgan darslar rasmi chiqmasin.
  const newPics = useMemo(() => {
    const out = new Set();
    steps.forEach((s, i) => {
      if (kinds[i] !== "new") return;
      if (s.rasm) out.add(s.rasm);
      emojiPictures(s.doska, lesson?.rasmlar, lesson?.rasm_sozlar).forEach((u) => out.add(u));
    });
    return out;
  }, [steps, kinds, lesson]);
  const questions = lesson?.savollar || [];
  // REV110: bog'chada takrorlashdan keyin ustoz bilan suhbat — faqat bola bilgan so'zlardan, yoshga qarab murakkablashadi.
  const bilgan = useMemo(() => (kid && lesson && darsTil ? bilganSozlar(darsTil) : []), [kid, lesson, darsTil]);
  const voiceItems = useMemo(() => {
    if (!lesson) return [];
    if (kid && !darsTil) return [];   // REV145: oddiy fanda (til darsi emas) mikrofon bilan tekshiruv yo'q
    const base = voiceCheckItems(lesson, audience, { izoh, tilYoq: kid && !darsTil });
    if (!kid) return base;
    const til = darsTil;
    const dars = darsSozlari(steps.slice(opening.length), kinds.slice(opening.length));
    // REV122: til darsida — avval BUGUN o'rganilgan so'zlar, darsning o'z tilida (salomlashish/eski takror emas);
    // boshqa tildagi (masalan, izoh tilidagi) iboralar aralashmaydi.
    const bugun = til ? dars.filter((w) => w.til === til).map((w) => ({ lang: til, phrase: w.say })) : [];
    const mos = til ? base.filter((x) => x.lang === til) : base;
    const seen = new Set();
    const asosiy = [...bugun, ...mos].filter((x) => { const k = x.phrase.toLowerCase(); if (seen.has(k)) return false; seen.add(k); return true; }).slice(0, 3);
    // REV145: oxirida Kabu bugungi so'zlarni yana aytdiradi (har biriga 2 urinish) + bitta qisqa suhbat savoli — uzun va zerikarli bo'lmasin
    const suhbat = suhbatSavollari({ til, grade: grade || lesson?.topic?.sinf, bilgan, dars, kun: Math.floor(Date.now() / 86400000), izoh })
      .filter((x) => !seen.has(String(x.phrase || "").toLowerCase())).slice(0, 1);
    return [...asosiy, ...suhbat];
  }, [lesson, audience, kid, steps, kinds, opening, bilgan, grade, darsTil, izoh]);
  const voiceReady = voiceItems.length > 0 && speechRecognitionAvailable(globalThis);
  const downloadUrl = (format) => lessonDownloadUrl(apiBase, token, topicCode, format);
  const mediaUrl = useCallback((url) => (!url ? null : url.startsWith("/") ? `${String(apiBase).replace(/\/+$/, "")}${url}` : url), [apiBase]);

  const hush = useCallback(() => {
    tokenRef.current += 1;
    const audio = audioRef.current; audioRef.current = null;
    if (audio) { try { audio.pause(); audio.src = ""; } catch { /* already released */ } }
    try { aralashRef.current?.stop(); } catch { /* */ } aralashRef.current = null;
    try { mikRef.current?.stop(); } catch { /* */ } mikRef.current = null;
    clearTimeout(sozTimer.current);
    setSpeaking(false); setWord(-1); lipRef.current = null; fallbackTalk.current = false;
  }, []);
  // Og'iz holati: null — jim (yopiq), 0..1 — ovoz balandligi, -1 — ovoz ketyapti, lekin tahlil hali tayyor emas.
  const mouthLevel = useCallback(() => {
    if (fallbackTalk.current) return -1;
    const a = audioRef.current;
    if (!a || a.paused || a.ended || !(a.currentTime > 0) || a.readyState < 3) return null;
    const lip = lipRef.current;
    if (!lip || lip.audio !== a) return -1;
    return lip.lv[Math.floor(a.currentTime / LIP_STEP)] ?? 0;
  }, []);

  // O'qituvchi ovozi: serverdagi TTS (/api/ovoz). REV102: ovoz yuklanmasa bir marta qayta so'raladi
  // (server uzilgan bo'lakni qayta yaratadi); baribir bo'lmasa so'zlar jim yonadi va dars to'xtab qolmaydi.
  // takror — bog'chada so'z o'rgatish qadami: «Men bilan ayt: Green» dan keyin bolaga 1.5–3 soniya vaqt.
  const ovozUrl = useCallback((clean, takror = false, attempt = 0) => {
    // REV122: jonli ustoz o'z ovozida: Sardor aka — erkak, Nilufar opa va Malika opa — ayol ovozi
    // REV145: robot Kabu har doim bitta ovozda (har darsda boshqa-boshqa ovoz bolani chalg'itardi)
    const ovozJinsi = kidRef.current ? (ustozGapiryapti() && ustozRef.current === "sardor" ? "ogil" : "qiz") : jins;
    const params = new URLSearchParams({ matn: clean.slice(0, 1500), jins: ovozJinsi,
      // REV122: ustoz — tabiiy (odam) ovozi: ohang ko'tarilmaydi, tezlik biroz tabiiyroq; robot Kabu — yuqoriroq ohang
      ...(kidRef.current ? (ustozGapiryapti() ? { tezlik: ustozRate(gradeRef.current) } : { tezlik: kidRate(gradeRef.current), ohang: KID_PITCH }) : {}),
      ...(takror ? { takror: "1" } : {}), ...(attempt ? { q: String(attempt) } : {}) });
    return `${String(apiBase).replace(/\/+$/, "")}/api/ovoz?k=133&${params}`;
  }, [apiBase, jins]);
  const spokenFor = useCallback((text) => speakableText(kidRef.current ? kabuSpeech(text) : text), []);
  // Keyingi qadam ovozi oldindan tayyorlanadi — server uni keshlaydi, bola kutmaydi.
  const prefetch = useCallback((text, takror = false) => {
    const clean = spokenFor(text);
    if (!clean.replace(/⏸/g, "").trim()) return;
    // REV139: aralash gapda faqat server o'qiydigan (o'zbekcha) bo'laklar oldindan tayyorlanadi
    const urls = aralashKerak(clean) ? ovozReja(clean, { takror }).filter((q) => q.tur === "server").map((q) => ovozUrl(q.matn, takror)) : [ovozUrl(clean, takror)];
    for (const url of urls) {
      if (prefetched.current.has(url)) continue;
      prefetched.current.add(url);
      try { fetch(url).then((r) => (r.ok ? r.arrayBuffer() : null)).catch(() => {}); } catch { /* eski brauzer */ }
    }
  }, [ovozUrl, spokenFor]);
  const say = useCallback((text, done, opts = {}) => {
    hush();
    const my = tokenRef.current;
    // REV98: qahramon — robot Kabu; REV122: sinfxonada gapiruvchi jonli ustoz — u odamdek gapiradi (robot iboralarisiz)
    if (kidRef.current) text = ustozGapiryapti() ? ustozNutqi(kabuSpeech(text), ustozRef.current) : kabuSpeech(text);
    // REV125: bog'chada tegsiz qolgan gap (interfeys tarjimasi) — izoh tilining o'z ovozida o'qiladi, o'zbek ovozida emas
    if (kidRef.current && izohRef.current !== "uz") text = izohTeg(text, izohRef.current);
    const clean = speakableText(text);
    setBubble(stripSpeechTags(text || "").replace(/\s*⏸\s*/g, " ").trim());
    if (!clean.replace(/⏸/g, "").trim()) { done?.(); return; }
    const words = String(text || "").replace(/⏸/g, " ").split(/\s+/).filter(Boolean);
    setSpeaking(true);
    const finish = () => { if (my !== tokenRef.current) return; clearTimeout(sozTimer.current); aralashRef.current = null; setSpeaking(false); setWord(-1); audioRef.current = null; lipRef.current = null; fallbackTalk.current = false; done?.(); };
    // REV139: gapda chet tildagi so'z bo'lsa — o'zbekcha bo'laklar serverdan, chet tildagilari qurilma ovozidan
    if (aralashKerak(clean)) {
      fallbackTalk.current = true;
      let w = 0;
      const sozYonsin = () => {
        if (my !== tokenRef.current || w >= words.length) return;
        setWord(w);
        sozTimer.current = setTimeout(sozYonsin, (300 + (words[w++] || "").length * 34) / rateRef.current);
      };
      sozYonsin();
      aralashRef.current = aralashOqi(clean, (m) => ovozUrl(m, opts.takror), {
        rate: (kidRef.current ? 0.85 : 0.95) * rateRef.current, playbackRate: rateRef.current, takror: Boolean(opts.takror),
        onEnd: () => { if (my === tokenRef.current) finish(); },
      });
      return;
    }
    // REV145: server ovoz bera olmasa — gap qurilma ovozida (zaxira), so'zlar navbat bilan yonadi; dars to'xtamaydi
    const fallback = () => {
      fallbackTalk.current = true;
      let i = 0, ovozTugadi = false, sozTugadi = false;
      const tamom = () => { if (ovozTugadi && sozTugadi) finish(); };
      aralashRef.current = qurilmadaOqi(clean.replace(/⏸/g, " "), { rate: (kidRef.current ? 0.85 : 0.95) * rateRef.current,
        onEnd: () => { if (my !== tokenRef.current) return; ovozTugadi = true; tamom(); } });
      const tick = () => {
        if (my !== tokenRef.current) return;
        setWord(i);
        if (++i > words.length) { sozTugadi = true; tamom(); return; }
        setTimeout(tick, (260 + (words[i - 1] || "").length * 28) / rateRef.current);
      };
      tick();
    };
    const play = (attempt) => {
      let audio;
      const src = ovozUrl(clean, opts.takror, attempt);
      try { audio = new Audio(src); } catch { fallback(); return; }
      audio.playbackRate = rateRef.current;
      audioRef.current = audio;
      let started = false, failed = false;
      const fail = (err) => {
        if (failed || my !== tokenRef.current) return;
        failed = true; clearTimeout(stall);
        if (started) { finish(); return; }   // yarmida uzildi — boshidan takrorlamaymiz, darsni davom ettiramiz
        try { audio.pause(); audio.src = ""; } catch { /* allaqachon yopilgan */ }
        if (attempt < 1 && err?.name !== "NotAllowedError") play(attempt + 1); else fallback();
      };
      const stall = setTimeout(() => { if (!started) fail(); }, 15000);
      audio.onplaying = () => {
        started = true; clearTimeout(stall);
        // og'iz uchun tahlil — ovoz boshlangach (server ovozni allaqachon tayyorlagan, ikki marta yaratilmaydi)
        if (kidRef.current && !lipRef.current) loadEnvelope(src).then((lv) => { if (lv && my === tokenRef.current && audioRef.current === audio) lipRef.current = { lv, audio }; });
      };
      audio.ontimeupdate = () => {
        if (my !== tokenRef.current || !audio.duration || !Number.isFinite(audio.duration)) return;
        setWord(Math.min(words.length - 1, Math.floor((audio.currentTime / audio.duration) * words.length)));
      };
      audio.onended = () => { clearTimeout(stall); finish(); };
      audio.onerror = () => fail();
      audio.play().catch((err) => fail(err));
    };
    play(0);
  }, [hush, ovozUrl]);

  // Qadamda aytiladigan gap (go() va oldindan yuklash uchun bir xil — server keshi mos tushadi).
  const stepSpeech = useCallback((s, i) => {
    const cue = boardCues(s.doska, s.ovoz || s.doska);
    if (!kid) return cue.spoken || s.doska;
    // REV95: eski yuklangan kitoblarda qolgan «yechimni keyin ochasiz» — bog'cha bolasiga aytilmaydi.
    const spoken = String(cue.spoken || s.doska).replace(/\s*Avval o['‘’]zingiz bajarib ko['‘’]ring, yechimni keyin ochasiz\.?/g, "");
    // REV102: takrordan yangiga o'tishda robot aytadi: «Avval o'tganlarni eslaymiz!» / «Endi — yangi so'z!»
    const lead = kindCue(kinds[i], i > 0 ? kinds[i - 1] : "", spoken, lesson?.topic?.mavzu, izoh);
    // «Qani, birga aytamiz!» dan keyin so'zlar pauza bilan; REV140: «Endi sen ayt: X» — avval ustoz X ni ikki marta aytadi
    return ismOldin(kidRepeatSpeech(lead ? `${lead} ${spoken}` : spoken, { doska: s.doska, izoh }));
  }, [kid, kinds, lesson, izoh]);
  // REV145: mikrofon bilan so'z aytish rejimi — faqat bog'cha til darsida, brauzer ovozni taniy olsa va ruxsat rad etilmagan bo'lsa.
  // Oddiy fanlarda (matematika, atrof-muhit…) mikrofon so'ralmaydi.
  const micRejim = () => Boolean(kid && darsTil && !mikYoq.current && speechRecognitionAvailable(globalThis));
  // Qadam ovozi oldindan: mikrofon rejimida gap «⏸» bo'yicha bo'laklab aytiladi — shu bo'laklar tayyorlanadi.
  const prefetchQadam = (j) => {
    const s = steps[j];
    if (!s) return;
    const spoken = stepSpeech(s, j);
    if (micRejim() && j >= opening.length && spoken.includes("⏸")) sozBolaklari(spoken, darsTil).forEach((b) => prefetch(b.matn, false));
    else if (micRejim() && j >= opening.length && kinds[j] === "new" && kidTakrorStep(s)) prefetch(spoken, false);
    else prefetch(spoken, kid && kidTakrorStep(s));
  };
  const prefetchQadamRef = useRef(prefetchQadam);
  prefetchQadamRef.current = prefetchQadam;
  // REV139: dars ochilganda birinchi ikki qadam ovozi sekin-asta (1.5 soniyadan keyin) oldindan tayyorlanadi —
  // «Boshlash» bosilganda kutilmaydi; qolganlari dars davomida navbatma-navbat (keyingi 2 qadam) tayyorlanadi.
  useEffect(() => {
    if (!steps.length || mode !== "idle") return undefined;
    const t = setTimeout(() => {
      [0, 1].forEach((j) => prefetchQadamRef.current(j));
    }, 1500);
    return () => clearTimeout(t);
  }, [steps, mode]);

  useEffect(() => {
    const controller = new AbortController();
    hush(); setLoading(true); setError(""); setLesson(null); setIdx(-1); setMode("idle"); setPlaying(false);
    setVariant(null); setMenu(false); setAskReply(""); setScore(0); setTestIndex(0); setPicked(null);
    fetch(`${String(apiBase).replace(/\/+$/, "")}/api/dars_xonasi/${encodeURIComponent(topicCode)}?${new URLSearchParams({ token })}`, { signal: controller.signal })
      .then(async (r) => { const d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.detail || "Dars yuklanmadi"); return d; })
      .then((d) => { setLesson(d); setBubble(lessonAudience(learnerRole, grade || d?.topic?.sinf) === "bogcha" ? ustozNutqi(__kbUi("Salom, do‘stim! Men robot Kabuman. Qani, boshladik!"), ustozFor(fan || d?.topic?.fan)) : __kbUi("Salom! «Darsni boshlash» tugmasini bosing — birga o‘rganamiz.")); })
      .catch((e) => { if (!controller.signal.aborted) setError(e.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => { controller.abort(); hush(); };
  }, [apiBase, token, topicCode, hush]);

  // REV110: bugungi ob-havo (server soatiga bir marta oladi va keshlaydi)
  useEffect(() => {
    if (!kid || !lesson) return undefined;
    const c = new AbortController();
    let shahar = "toshkent";
    try { shahar = globalThis.localStorage?.getItem("kabutar:shahar") || shahar; } catch { /* */ }
    fetch(`${String(apiBase).replace(/\/+$/, "")}/api/bogcha/havo?${new URLSearchParams({ shahar })}`, { signal: c.signal })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (d) { setHavo(havoTuri(d.kod)); setHarorat(d.harorat ?? null); setShamol(Number(d.shamol) >= 30); } })
      .catch(() => { /* ob-havo bo'lmasa — fasl bo'yicha */ });
    return () => c.abort();
  }, [kid, lesson, apiBase]);

  // REV111 / REV140: kun vaqti (tong/kun/kech/tun) — quyoshning haqiqiy holatidan (shahar + mutlaq vaqt), har daqiqada
  useEffect(() => {
    if (!kid) return undefined;
    const tick = () => setVaqt(quyoshVaqti(new Date()));
    tick();
    const t = setInterval(tick, 60000);
    return () => clearInterval(t);
  }, [kid]);

  useEffect(() => { if (audioRef.current) audioRef.current.playbackRate = rate; }, [rate]);

  const go = useCallback((next, autoplay = playingRef.current) => {
    qadamRef.current += 1; setMikSoz(null);
    setMenu(false); setVariant(null); setAskReply(""); setFeedback(null); setAnswer("");
    clearTimeout(gameTimer.current); gameRef.current = null; setGame(null);   // o'yin qadamidan chiqildi
    if (next >= steps.length) {
      hush(); setPlaying(false); setStepFinished(true);
      // REV105: avval ovozli tekshiruv — ustoz aytadi, mikrofon yoqiladi, takrorlanadi; keyin odatdagi davom.
      if (voiceReady && !voiceRef.current) { setMode("ovoz"); return; }
      afterLessonRef.current();
      return;
    }
    if (next < 0) return;
    if (next === 0) { sorilgan.current = new Set(); jimSanoq.current = 0; aytganlar.current = {}; voiceRef.current = null; setVoice(null); gameRes.current = {}; setGameScore(0); setGameTotal(0); }   // dars qaytadan — tekshiruv va o'yin hisobi ham qaytadan
    setIdx(next); setMode("lesson"); setStepFinished(false);
    runStepRef.current(next, autoplay);
  }, [steps, hush, voiceReady]); // eslint-disable-line react-hooks/exhaustive-deps

  const afterLesson = () => {
    {
      if (kid) {   // REV91: bog'chada tugma bosilmaydi — dars tugashi bilan o'yin o'zi boshlanadi
        answerTimes.current = [];
        if (questions.length) { say(izoh !== "uz" ? gap(izoh, "Barakalla! Endi o'ynaymiz!") : __kbUi("Barakalla! Endi o‘ynaymiz!"), () => { setMode("test"); setTestIndex(0); setScore(0); setPicked(null); }); setMode("bridge"); }
        else setMode("result");
        return;
      }
      // Dars tugadi: o'quvchi o'zi tanlaydi — shu yerda tezkor savollar yoki Test bo'limi.
      setMode("end");
      say(questions.length || onOpenTest
        ? __kbUi("Barakalla! Dars tugadi. Endi bilimingizni tekshiring: pastdan test turini tanlang.")
        : __kbUi("Barakalla! Dars tugadi."));
    }
  };
  const afterLessonRef = useRef(afterLesson);
  afterLessonRef.current = afterLesson;
  const voiceDone = (sum, list = []) => {
    // REV145: dars oxirida aytgan so'zlari ham yoziladi (darsda chiqmagan bo'lsa-yu, oxirida aytsa — «aytdi»)
    for (const r of list || []) { const k = String(r?.phrase || "").toLowerCase(); if (k) aytganlar.current[k] = Boolean(aytganlar.current[k] || r.ok); }
    setVoice(sum || { togri: 0, jami: 0 }); voiceRef.current = sum || { togri: 0, jami: 0 }; afterLesson();
  };
  // REV145: so'z rasmi — rassom chizgan rasm (inglizcha so'z yoki emoji orqali)
  const sozRasmi = (soz, emoji) => { const id = sozId({ soz: darsTil === "en" ? soz : "", emoji }); return id && RASMLAR[id] ? { id, src: RASMLAR[id] } : emojiRasm(emoji, RASMLAR); };
  // REV145: bugun o'rgangan so'zlar va bola ularni aytdimi — bola natija ekranida va ota-ona hisobotida
  const bugungiSozlar = () => (darsTil ? darsSozlari(steps.slice(opening.length), kinds.slice(opening.length)) : [])
    .map((w) => { const k = w.say.toLowerCase(); return { soz: w.say, emoji: w.emoji || "", aytdi: k in aytganlar.current ? aytganlar.current[k] : null }; });

  const MIC_MAQTOV = ["Barakalla! {p}", "Zo‘r! Ana shunday!", "Ofarin! Sen zo‘rsan!"];
  // REV145: bola so'zni mikrofonga aytadi: 1-urinish → eshitilmasa/xato bo'lsa «Yana bir bor ayt» → 2-urinish →
  // baribir bo'lmasa ustoz to'g'risini aytib, maqtab davom etadi (bola xafa bo'lmaydi, dars to'xtamaydi).
  const sozniEshit = (soz, urinish, my, keyingi) => {
    const p = `[${soz.lang}]${soz.phrase}[/${soz.lang}]`;
    setMikSoz({ ...soz, holat: "tingla", urinish });
    const t = tingla(soz.lang);
    mikRef.current = t;
    t.promise.then(({ alts, xato, toxtatildi }) => {
      if (mikRef.current === t) mikRef.current = null;
      if (toxtatildi || my !== qadamRef.current) { if (toxtatildi && my === qadamRef.current) setMikSoz(null); return; }
      if (xato) { mikYoq.current = true; setMikSoz(null); keyingi(); return; }
      sorilgan.current.add(soz.phrase.toLowerCase());
      const g = aytdiMi(alts, soz, urinish);
      const k = soz.phrase.toLowerCase();
      if (g.ok || urinish > 0) aytganlar.current[k] = aytganlar.current[k] || g.ok;
      if (g.ok) {
        jimSanoq.current = 0;
        chime(); setCelebrate((c) => c + 1);
        say(gap(izoh, MIC_MAQTOV[(sorilgan.current.size - 1) % MIC_MAQTOV.length], { p }), () => { if (my === qadamRef.current) { setMikSoz(null); keyingi(); } });
        setMikSoz({ ...soz, holat: "ok" });
        return;
      }
      if (urinish === 0) {
        soft();
        say(alts.length ? gap(izoh, "Yana bir bor ayt: {p}", { p }) : gap(izoh, "Ovozing eshitilmadi. Balandroq va dadil ayt: {p}", { p }),
          () => { if (my === qadamRef.current) sozniEshit(soz, 1, my, keyingi); });
        setMikSoz({ ...soz, holat: "yana" });
        return;
      }
      // ikki urinishda ham hech narsa eshitilmadi — ikki so'z ketma-ket shunday bo'lsa, mikrofon shu darsda boshqa so'ralmaydi
      jimSanoq.current = alts.length ? 0 : jimSanoq.current + 1;
      if (jimSanoq.current >= 2) mikYoq.current = true;
      say(gap(izoh, "Yaxshi harakat! Mana bunday: {p}", { p }), () => { if (my === qadamRef.current) { setMikSoz(null); keyingi(); } });
      setMikSoz({ ...soz, holat: "no" });
    });
  };
  // Gap bo'laklari navbat bilan: bo'lak aytiladi → bola shu so'zni aytadi → keyingi bo'lak.
  const bolaklabAyt = (list, k, my, done) => {
    const b = list[k];
    if (!b) { done(); return; }
    const keyingi = () => bolaklabAyt(list, k + 1, my, done);
    say(b.matn, () => {
      if (my !== qadamRef.current) return;
      const key = b.soz?.phrase.toLowerCase();
      if (b.soz && !mikYoq.current && !sorilgan.current.has(key)) { sozniEshit(b.soz, 0, my, keyingi); return; }
      // so'z allaqachon so'ralgan yoki mikrofon o'chgan — avvalgidek bolaga qaytarish uchun jimlik
      if (k < list.length - 1 && b.pauza !== false) setTimeout(() => { if (my === qadamRef.current) keyingi(); }, 2000); else keyingi();
    });
  };

  const runStep = (next, autoplay) => {
    const s = steps[next];
    const spoken = stepSpeech(s, next);
    [next + 1, next + 2].forEach((j) => prefetchQadam(j));
    if (kid && next > 0 && kinds[next] !== kinds[next - 1]) { if (kinds[next] === "new") chime(); else if (kinds[next] === "review") soft(); }
    let micBilan = false;
    const qadamTugadi = () => {
      setStepFinished(true);
      // «birga» va «amaliy» qadamida o'quvchi o'zi ishlaydi — dars shu yerda kutadi.
      // REV121: «Top-chi» o'yini — so'zlar bilan bog'langan rasmlar bo'lsa, bola bosishini kutadigan haqiqiy o'yin
      const targets = autoplay && kid && s.turi === "amaliy" && next >= opening.length ? gameTargets(s, steps, kinds) : [];
      if (targets.length) { gameApi.current.start(next, targets); return; }
      if (autoplay && kid && s.turi === "amaliy") {
        // REV93: bog'chada topshiriq (qo'shiq, harakat, o'yin) — bolaga bajarishga vaqt, keyin maqtov va davom. Tugma kerak emas.
        // Bajarganini tekshirib bo'lmaydi — shuning uchun «Barakalla» demaymiz, to'g'ri javobni birga aytamiz.
        const praise = kidTaskModel(s.ovoz || s.doska, izoh);
        setTimeout(() => { if (playingRef.current && idxRef.current === next) say(praise, () => setTimeout(() => { if (playingRef.current && idxRef.current === next) go(next + 1, true); }, 900)); }, 4000);
        return;
      }
      // So'z o'rgatiladigan qadam («Men bilan takrorla») — bola qaytarib aytishi uchun biroz ko'proq kutiladi
      // (mikrofon bilan aytgan bo'lsa — allaqachon aytdi, qisqa kutish).
      const pause = kid && !micBilan && /\[(en|ru|de|fr|es|ar|tr|zh|ja|ko)\]/i.test(s.ovoz || "") ? 2600 : 1000;
      if (autoplay && s.turi !== "birga" && s.turi !== "amaliy") setTimeout(() => { if (playingRef.current && idxRef.current === next) go(next + 1, true); }, pause);
    };
    // salomlashish/ob-havo suhbati (ochilish) — savol-javob, u yerda so'z aytdirilmaydi; faqat darsning o'zida
    if (micRejim() && next >= opening.length) {
      let list = spoken.includes("⏸") ? sozBolaklari(spoken, darsTil) : [];
      // yangi so'z o'rgatilgan qadamda «⏸» bo'lmasa ham — oxirida ustoz so'raydi: «Endi sen ayt: Bye» (har so'z bir marta)
      if (!list.some((b) => b.soz) && kinds[next] === "new" && kidTakrorStep(s)) {
        const yangi = darsSozlari([s], ["new"], 2).filter((w) => w.til === darsTil && !sorilgan.current.has(w.say.toLowerCase()));
        if (yangi.length) list = [{ matn: spoken.replace(/\s*⏸\s*/g, " ").trim(), soz: null, pauza: false },
          ...yangi.map((w) => ({ matn: gap(izoh, "Endi sen ayt: {p}", { p: `[${darsTil}]${w.say}[/${darsTil}]` }), soz: { lang: darsTil, phrase: w.say } }))];
      }
      if (list.some((b) => b.soz && !sorilgan.current.has(b.soz.phrase.toLowerCase()))) {
        micBilan = true;
        const my = qadamRef.current;
        bolaklabAyt(list, 0, my, () => { if (my === qadamRef.current) qadamTugadi(); });
        return;
      }
    }
    say(spoken, qadamTugadi, { takror: kid && kidTakrorStep(s) });
  };
  const runStepRef = useRef(runStep);
  runStepRef.current = runStep;

  const startQuiz = () => {
    answerTimes.current = [];
    setMode("test"); setTestIndex(0); setScore(0); setPicked(null);
    say(__kbUi("Savolni o‘qing va javobni tanlang."));
  };
  const togglePlay = () => {
    if (mode === "result" || mode === "end") { setScore(0); gameRes.current = {}; setGameScore(0); setGameTotal(0); setPlaying(true); go(0, true); return; }
    if (playing) { setPlaying(false); hush(); setStepFinished(true); return; }
    setPlaying(true);
    if (mode !== "lesson") go(0, true); else if (!variant) go(idx, true);
  };

  const openVariant = (v) => {
    setMenu(false); setVariant(v); say(v.ovoz || v.doska);
  };
  const dunno = () => {
    if (kid) {   // REV98: bog'cha bolasi menyuni o'qiy olmaydi — robot o'zi boshqacha (sekinroq) qayta tushuntiradi
      const first = (lesson?.variants?.[step?.id] || [])[0];
      setPlaying(false); setRate(0.85); rateRef.current = 0.85; setPicRev((r) => r + 1);
      if (first) { setVariant(first); say(first.ovoz || first.doska, () => { setVariant(null); setPlaying(true); go(idx + 1, true); }); return; }
      if (step) { setStepFinished(false); say(boardCues(step.doska, step.ovoz || step.doska).spoken || step.doska, () => { setStepFinished(true); setPlaying(true); go(idx + 1, true); }); }
      return;
    }
    setPlaying(false); hush(); setMenu(true);
    const list = lesson?.variants?.[step?.id] || [];
    say(list.length ? __kbUi("Hechqisi yo‘q! Qaysi usulda qayta tushuntiray?") : __kbUi("Hechqisi yo‘q. Sekinroq qayta aytaman yoki AI ustozdan so‘raymiz."));
  };

  const submitAnswer = (event) => {
    event.preventDefault();
    if (!step) return;
    if (checkAnswer(answer, step.javob)) {
      setFeedback({ ok: true, text: step.javob_izohi || __kbUi("To‘g‘ri!") });
      say(__kbUi("Barakalla, to‘g‘ri!") + " " + (step.javob_izohi || ""), () => { if (playingRef.current) setTimeout(() => go(idx + 1, true), 800); });
    } else {
      setFeedback({ ok: false, text: __kbUi("Yana bir bor urinib ko‘ring.") });
      say(__kbUi("Deyarli! Yana bir bor o‘ylab ko‘ring.") + (step.javob_izohi ? " " + __kbUi("Yordam: ") + step.javob_izohi : ""));
    }
  };

  const ask = async (text) => {
    const savol = (text ?? question).trim();
    if (!savol || asking) return;
    setAsking(true); setPlaying(false); hush(); setAskReply("");
    try {
      const r = await fetch(`${String(apiBase).replace(/\/+$/, "")}/api/ai/ustoz/sorash`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, fan: fan || lesson?.topic?.fan || "", topic_code: topicCode, grade: grade || lesson?.topic?.sinf || undefined, rejim: "orgatish", savol }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || "AI ustoz javob bermadi");
      const reply = (d.javob?.bloklar || []).map((b) => b.matn).filter(Boolean).join("\n\n") || __kbUi("Javob topilmadi.");
      setAskReply(reply); setQuestion(""); say(reply.slice(0, 900));
    } catch (e) { setAskReply(e.message); }
    finally { setAsking(false); }
  };

  // REV98: robot bir lahza quvonadi (sakraydi, yulduz sochadi) yoki dalda beradi.
  const flashPhase = useCallback((ph, ms = 1800) => {
    clearTimeout(phaseTimer.current);
    setKidPhase(ph);
    if (ph === "happy") { setCelebrate((c) => c + 1); chime(); } else if (ph === "enc") soft();
    phaseTimer.current = setTimeout(() => setKidPhase(""), ms);
  }, []);
  useEffect(() => () => clearTimeout(phaseTimer.current), []);

  // ── REV121: «Top-chi» o'yini ──
  // Ustoz so'zni aytadi → bola bosishini kutadi (9 s). Birinchi urinishda to'g'ri — ⭐; xato — «Yana qidir!» (bitta imkon),
  // ikkinchi xato yoki bosmasa — to'g'ri rasm ko'rsatiladi, yulduz berilmaydi. Hisob dars natijasiga qo'shiladi.
  const gTil = darsTil || (izoh !== "uz" ? izoh : "");
  const soz = (t) => (darsTil ? `[${darsTil}]${t.word}[/${darsTil}]` : izohTeg(t.word, izoh));
  const sonliGap = (tpl, n) => gap(izoh, tpl, { n: String(n) }).replace(new RegExp(`\\[\\/${izoh}\\](\\d+)\\[${izoh}\\]`, "g"), "$1");
  const gameApi = useRef(null);
  gameApi.current = {
    alive(g) { return g && gameRef.current === g && playingRef.current && idxRef.current === g.stepIdx && modeRef.current === "lesson"; },
    paint(g, patch = {}) { setGame((p) => (p && p.stepIdx === g.stepIdx ? { ...p, ...patch } : p)); },
    wait(g, ms, fn) { clearTimeout(gameTimer.current); gameTimer.current = setTimeout(() => { if (gameApi.current.alive(g)) fn(); }, ms); },
    totals() {
      const all = Object.values(gameRes.current);
      setGameScore(all.reduce((n, r) => n + r.found, 0));
      setGameTotal(all.reduce((n, r) => n + r.total, 0));
    },
    start(stepIdx, targets) {
      const order = targets.map((_, i) => i).sort(() => Math.random() - 0.5);
      const withPics = targets.map((t) => {
        const own = pictureFor(t.emoji, t.word, lesson?.rasmlar, lesson?.rasm_sozlar);
        return { ...t, src: own ? mediaUrl(own) : "" };
      });
      const g = { stepIdx, targets: withPics, order, k: 0, tries: 0, found: 0, waiting: false, again: false };
      gameRef.current = g;
      gameRes.current[stepIdx] = { found: 0, total: targets.length };
      gameApi.current.totals();
      setGame({ stepIdx, targets: withPics, holat: {}, kutish: false });
      setTimeout(() => { if (gameApi.current.alive(g)) gameApi.current.round(g); }, 600);
    },
    round(g) {
      if (!gameApi.current.alive(g)) return;
      if (g.k >= g.order.length) { gameApi.current.end(g); return; }
      const t = g.targets[g.order[g.k]];
      g.tries = 0; g.again = false;
      // REV122: bola ustoz gapini kutmasdan ham bosishi mumkin — bosish darhol qabul qilinadi
      g.waiting = true;
      gameApi.current.paint(g, { holat: {}, kutish: true });
      say(gap(izoh, "Qani, top: {p}", { p: soz(t) }), () => {
        if (!gameApi.current.alive(g) || !g.waiting) return;
        g.waiting = true; gameApi.current.paint(g, { kutish: true });
        gameApi.current.wait(g, 9000, () => gameApi.current.timeout(g));
      });
    },
    timeout(g) {
      const t = g.targets[g.order[g.k]];
      g.waiting = false; gameApi.current.paint(g, { kutish: false });
      if (!g.again) {   // bir marta qayta so'raymiz
        g.again = true;
        g.waiting = true; gameApi.current.paint(g, { kutish: true });
        say(gap(izoh, "Barmog'ing bilan bos: {p}", { p: soz(t) }), () => {
          if (!gameApi.current.alive(g) || !g.waiting) return;
          g.waiting = true; gameApi.current.paint(g, { kutish: true });
          gameApi.current.wait(g, 7000, () => gameApi.current.reveal(g));
        });
        return;
      }
      gameApi.current.reveal(g);
    },
    reveal(g) {
      const i = g.order[g.k];
      g.waiting = false; clearTimeout(gameTimer.current);
      gameApi.current.paint(g, { holat: { [i]: "hint" }, kutish: false });
      say(gap(izoh, "Mana u: {p}", { p: soz(g.targets[i]) }), () => gameApi.current.wait(g, 900, () => { g.k += 1; gameApi.current.round(g); }));
    },
    tap(i) {
      const g = gameRef.current;
      if (!g || !g.waiting || !gameApi.current.alive(g)) return false;
      const want = g.order[g.k];
      clearTimeout(gameTimer.current);
      g.waiting = false;
      if (i === want) {
        const first = g.tries === 0;
        if (first) { g.found += 1; gameRes.current[g.stepIdx] = { found: g.found, total: g.targets.length }; gameApi.current.totals(); }
        flashPhase("happy");
        gameApi.current.paint(g, { holat: { [i]: "ok" }, kutish: false });
        const praise = kidPraise(g.k + g.found, gTil);
        say(first ? `${praise} ${gap(izoh, "Topding! Yulduzcha seniki!")}` : praise, () => gameApi.current.wait(g, 700, () => { g.k += 1; gameApi.current.round(g); }));
        return true;
      }
      g.tries += 1;
      flashPhase("enc");
      gameApi.current.paint(g, { holat: { [i]: "no" }, kutish: false });
      if (g.tries >= 2) { setTimeout(() => { if (gameApi.current.alive(g)) gameApi.current.reveal(g); }, 500); return true; }
      setTimeout(() => { if (gameApi.current.alive(g) && !g.waiting && g.tries < 2) { g.waiting = true; gameApi.current.paint(g, { holat: {}, kutish: true }); } }, 450);
      say(gap(izoh, "Bu emas. Yana qidir!"), () => {
        if (!gameApi.current.alive(g)) return;
        g.waiting = true; gameApi.current.paint(g, { holat: {}, kutish: true });
        gameApi.current.wait(g, 8000, () => gameApi.current.timeout(g));
      });
      return true;
    },
    end(g) {
      const n = g.found;
      gameApi.current.paint(g, { holat: {}, kutish: false });
      const text = n > 0 ? sonliGap("Barakalla! O'yinda {n} ta yulduzcha yig'ding!", n) : gap(izoh, "Hechqisi yo'q, keyingi safar albatta topasan!");
      if (n > 0) flashPhase("happy", 2200);
      say(text, () => gameApi.current.wait(g, 800, () => { gameRef.current = null; setGame(null); go(g.stepIdx + 1, true); }));
    },
  };
  const pick = (k) => {
    if (picked !== null) return;
    if (kid) {
      const q = questions[testIndex];
      const from = askedAt.current || questionDone.current;   // savol o'qilayotganda bosilgani — tezlikka kirmaydi
      if (from) answerTimes.current.push(Date.now() - from);
      askedAt.current = 0; questionDone.current = 0;
      setPicked(k);
      setHot(-1); setWaiting(false);
      const after = () => setTimeout(() => { if (modeRef.current === "test") nextQuestion(); }, 900);
      // REV102: til darsida maqtov o'sha tilda («Well done!»). REV121: boshqa fanlarda — izoh tilida (izohning o'zi maqtov bilan boshlanadi)
      if (k === q.togri) {
        setScore((x) => x + 1); flashPhase("happy");
        const speech = darsTil ? kidCorrectSpeech(testIndex, contentLanguage(q.savol, q.variantlar), q.izoh)
          : (q.izoh || (izoh !== "uz" ? gap(izoh, "Barakalla! To'g'ri!") : __kbUi("Barakalla! To‘g‘ri!")));
        say(speech || __kbUi("Barakalla! To‘g‘ri!"), after);
      } else {
        // xato javobdan keyin «Barakalla» aytilmaydi — izohdan maqtov olib tashlanadi
        flashPhase("enc");
        say(`${izoh !== "uz" ? gap(izoh, "Hechqisi yo'q! To'g'ri javob yashil rasmda.") : __kbUi("Hechqisi yo‘q! To‘g‘ri javob yashil rasmda.")} ${dropPraiseAny(q.izoh || "")}`.trim(), after);
      }
      return;
    }
    const q = questions[testIndex];
    setPicked(k);
    if (k === q.togri) { setScore((x) => x + 1); say(__kbUi("To‘g‘ri!"), () => setTimeout(() => nextQuestion(), 700)); }
    else say(q.izoh || __kbUi("Javob noto‘g‘ri. To‘g‘ri variant yashil bilan belgilandi."));
  };
  const nextQuestion = () => {
    setPicked(null);
    setTestIndex((i) => {
      if (i + 1 >= questions.length) { setMode("result"); return i; }
      return i + 1;
    });
  };
  const readQuestion = useCallback((qq) => {
    if (!qq) return;
    const opts = kidOptions(Object.fromEntries(qq.variantlar.map((o, k) => [`option_${"abcd"[k]}`, o])), qq.savol);
    const audio = opts.map((o, k) => ({ k, o })).filter(({ o }) => o.listen === "audio");
    setHot(-1); setWaiting(false);
    askedAt.current = 0; questionDone.current = 0;
    const next = (i) => {
      if (i >= audio.length) { setHot(-1); setWaiting(true); askedAt.current = Date.now(); return; }
      setHot(audio[i].k);
      say(audio[i].o.speech, () => setTimeout(() => next(i + 1), 250));
    };
    say(qq.savol, () => { questionDone.current = Date.now(); setTimeout(() => next(0), 300); });
  }, [say]);
  useEffect(() => {
    if (!kid || mode !== "test" || !questions[testIndex]) return;
    const t = setTimeout(() => readQuestion(questions[testIndex]), 300);
    return () => clearTimeout(t);
  }, [kid, mode, testIndex]); // eslint-disable-line react-hooks/exhaustive-deps
  // REV91: bog'cha — dars o'zi boshlanadi; kunlik reja tugagan bo'lsa aytiladi. Faollik ota-onaga boradi.
  useEffect(() => {
    if (!kid || !lesson || mode !== "idle") return undefined;
    let stop = false;
    (async () => {
      const today = screenTime.current();
      const res = kidPlan ? await startLesson(apiBase, token, { darsKod: topicCode, fan: kidPlan.fan, mavzu: kidPlan.mavzu || lesson.topic?.mavzu, jamiQadam: steps.length })
        : !cheklovsiz && today?.tugadi?.dars && !today.kuzatilmaydi   // REV103: reja tashqarisidan ochilgan dars ham dars vaqti tugagan bo'lsa ochilmaydi
          ? { ok: false, limit: true, vaqt: true, xabar: __kbUi("Bugungi dars vaqti tugadi. Barakalla! Endi biroz o‘ynasang bo‘ladi.") }
          : { ok: true, tracked: false };
      if (stop) return;
      if (res.limit) {
        setLimitText(res.xabar); setLimitKind(res.vaqt ? "vaqt" : "limit"); setMode("limit");
        // REV103: bugungi dars VAQTI tugagan — robot shuni aytadi (o'yin vaqti bo'lsa, o'yinlar ochiq)
        say(res.vaqt ? (res.xabar || __kbUi("Bugungi dars vaqti tugadi. Endi biroz o‘ynasang bo‘ladi."))
          : __kbUi("Bugungi yangi darslar tugadi. Ertaga yana o‘ynaymiz! Hozir o‘tilgan darslarni takrorlasang bo‘ladi."));
        return;
      }
      if (res.tracked) kidTracker.start({ apiBase, token, darsKod: topicCode, isPlaying: () => playingRef.current || speakingRef.current || modeRef.current === "test" || modeRef.current === "ovoz" });
      setTimeout(() => { if (!stop && modeRef.current === "idle") { beep(); setPlaying(true); go(0, true); } }, 700);
    })();
    return () => { stop = true; };
  }, [kid, lesson]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (kid && idx >= 0) kidTracker.step(idx + 1); }, [kid, idx]);
  // REV103: kunlik vaqt — ota-ona «nima qildi» ro'yxatida dars nomi; dars ketayotganda vaqt tugasa, tugatib olishiga imkon;
  // to'liq tugaganda (10 daqiqadan keyin) ovoz to'xtaydi.
  useEffect(() => {
    if (!kid || !lesson) return undefined;
    screenTime.setDetail(`Dars: «${lesson.topic?.mavzu || topicCode}»`);
    return () => screenTime.setDetail("");
  }, [kid, lesson, topicCode]);
  useEffect(() => { if (kid) screenTime.setBusy("dars", ["lesson", "test", "bridge", "ovoz"].includes(mode)); }, [kid, mode]);
  useEffect(() => () => screenTime.setBusy("dars", false), []);
  useEffect(() => screenTime.onBlock((view) => {
    hush(); setPlaying(false);
    // vaqt to'liq tugadi (10 daqiqalik kutishdan keyin) — dars shu yerda yopiladi, qayta ochilsa ham davom etmaydi
    if (kidRef.current && (view === "dars" || view === "jami") && ["idle", "lesson", "test", "bridge", "ovoz"].includes(modeRef.current)) {
      setLimitText(__kbUi(view === "jami" ? "Bugun vaqting tugadi. Ertaga uchrashamiz!" : "Bugungi dars vaqti tugadi. Endi biroz o‘ynasang bo‘ladi."));
      setLimitKind("vaqt"); setMode("limit");
    }
  }), [hush]);
  useEffect(() => () => { if (kidTracker.active() === topicCode) kidTracker.detach(); }, [topicCode]);
  // REV106: dars boshlangach — faqat dars: butun ekran, menyular, yon panel va yordamchilar yashiriladi.
  const focus = ["lesson", "ovoz", "test", "bridge", "end", "result", "limit"].includes(mode);
  useEffect(() => {
    document.body.classList.toggle("kb-focus-dars", focus);
    return () => document.body.classList.remove("kb-focus-dars");
  }, [focus]);
  useEffect(() => {
    if (!focus) return undefined;
    const key = (e) => { if (e.key === "Escape" && !kidRef.current) exitRef.current?.(); };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [focus]);
  const exitLesson = () => {
    hush(); setPlaying(false); setMenu(false); setVariant(null);
    if (kid && onClose) { onClose(); return; }
    setMode("idle"); setIdx(-1);
    setBubble(__kbUi(kid ? "Yana o‘ynaymizmi? ▶ ni bos!" : "Dars to‘xtatildi. «Darsni boshlash» bilan qaytadan boshlang."));
  };
  const exitRef = useRef(exitLesson);
  exitRef.current = exitLesson;
  useEffect(() => {
    if (!kid || mode !== "result") return;
    // REV121: yulduz — test va «Top-chi» o'yinidagi to'g'ri javoblar ulushi; hech biri to'g'ri bo'lmasa — 0 yulduz
    const all = Object.values(gameRes.current);
    const togri = score + all.reduce((n, r) => n + r.found, 0);
    const jami = questions.length + all.reduce((n, r) => n + r.total, 0);
    const local = kidStars(togri, jami);
    markLessonDone(topicCode, local);
    // REV110: o'rgangan so'zlarini eslab qolamiz — keyingi dars boshida ustoz shulardan so'raydi (faqat til darsida)
    eslab({ code: topicCode, mavzu: lesson?.topic?.mavzu || "", sozlar: darsTil ? darsSozlari(steps.slice(opening.length), kinds.slice(opening.length)) : [] });
    const sozlar = bugungiSozlar();
    setKidResult({ yulduz: local, sozlar });
    const wasTracked = kidTracker.active() === topicCode;
    if (wasTracked) kidTracker.finish();
    (async () => {
      const res = wasTracked || kidPlan ? await finishLesson(apiBase, token, { darsKod: topicCode, togri, jami, ortachaMs: answerSpeed(answerTimes.current), ovozTogri: voiceRef.current?.togri || 0, ovozJami: voiceRef.current?.jami || 0, sozlar }) : null;
      const out = { yulduz: Number.isFinite(Number(res?.yulduz)) ? Number(res.yulduz) : local, bugunTugadi: Boolean(res?.bugun_tugadi), qoldi: res?.qoldi, sozlar };
      setKidResult(out);
      onKidFinished?.(out, res?.reja || null);
    })();
    if (local > 0) flashPhase("happy", 3200); else flashPhase("enc", 2400);
    const g3 = (uz, key) => (izoh !== "uz" ? gap(izoh, key) : __kbUi(uz));
    say(local === 3 ? g3("Barakalla! Uchta yulduz! Sen zo‘rsan!", "Barakalla! Uchta yulduz! Sen zo'rsan!")
      : local > 0 ? g3("Yaxshi harakat! Yana o‘ynasak, yulduzlar ko‘payadi!", "Yaxshi harakat! Yana o'ynasak, yulduzlar ko'payadi!")
        : g3("Bu safar yulduzcha yo‘q. Qani, yana bir bor urinib ko‘ramiz!", "Bu safar yulduzcha yo'q. Qani, yana bir bor urinib ko'ramiz!"));
  }, [mode]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (kid || mode !== "result" || !questions.length) return;
    const pass = score / questions.length >= 0.7;
    say(pass ? __kbUi("Barakalla! Siz mavzuni o‘zlashtirdingiz.") : __kbUi("Yaxshi harakat! Keling, asosiy qismni yana bir bor ko‘rib chiqamiz."));
  }, [mode]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) return <div className="dx-status">{__kbUi("Dars yuklanmoqda…")}</div>;
  if (error) return <div className="dx-empty"><p>{__kbUi(error)}</p>{onChat && <button type="button" className="dx-btn dx-primary" onClick={onChat}>{__kbUi("AI ustoz bilan suhbatda o‘rganish")}</button>}</div>;

  const range = step ? sceneRange(steps, idx) : [];
  const list = lesson?.variants?.[step?.id] || [];
  const words = bubble.split(/\s+/).filter(Boolean);
  const q = mode === "test" ? questions[testIndex] : null;
  const pass = questions.length ? score / questions.length >= 0.7 : true;
  // REV98: bog'cha sahnasi — yozuv yo'q: robot, jonli rasm va harakat belgilari.
  const kidSrc = kid && step ? `${step.ovoz || ""} ${step.doska || ""}` : "";
  const kidActs = kid && step && mode === "lesson" ? stepActions(kidSrc) : [];
  const kidKind = kid && mode === "lesson" ? kinds[idx] || "" : "";
  // Rasm manzili → {belgi (emoji), soz}: kitobdagi rasm_sozlar («🍎|apple») yoki rasmlar («🍎»)
  const picWord = (u) => {
    for (const [k, v] of Object.entries(lesson?.rasm_sozlar || {})) if (v === u) { const [belgi, soz = ""] = k.split("|"); return { belgi, soz }; }
    for (const [k, v] of Object.entries(lesson?.rasmlar || {})) if (v === u) return { belgi: k, soz: "" };
    return {};
  };
  const kidPics = (() => {
    if (!kid || !step || mode !== "lesson") return [];
    // REV122: rasm qaysi so'zniki ekanini eslab qolamiz — bosilganda nomi aytiladi
    // REV144: har rasm o'z ma'nosiga mos 1–2 soniyalik harakat qiladi (anim); emoji karta — chizilgan rasm bilan
    const pic = (u, i) => { const w = picWord(u); return { src: mediaUrl(u), rev: picRev, label: `rasm ${i + 1}`, ...w, anim: harakatTuri(sozId({ soz: w.soz, emoji: w.belgi })) }; };
    const karta = (e, extra = {}) => { const r = emojiRasm(e, RASMLAR); return { emoji: e, src: r?.src || "", anim: harakatTuri(r?.id || sozId({ emoji: e })), rev: picRev, ...extra }; };
    if (variant?.rasm) return [pic(variant.rasm, 0)];
    // REV140: salomlashish va ob-havo qadamida doskaga belgi-stikerlar (👋 🙂 😊) chiqmaydi — ustoz qo'l silkitadi,
    // ob-havoda bola derazaga qaraydi (deraza nurlanadi)
    if (step._ochilish === "salom" || step._ochilish === "havo") return [];
    // REV121: o'yin — nishonlar (rasm yoki emoji karta), holati bilan: kutilmoqda / to'g'ri / xato / mana u
    if (game && game.stepIdx === idx) {
      return game.targets.map((t, i) => {
        const r = t.src ? null : emojiRasm(t.emoji, RASMLAR);
        return { src: t.src || r?.src || "", emoji: t.src || r ? "" : t.emoji, rev: picRev, label: t.word,
          anim: harakatTuri(sozId({ soz: t.word, emoji: t.emoji })), holat: game.holat[i] || (game.kutish ? "wait" : "") };
      });
    }
    // REV99: doskadagi emojilar (masalan «Top-chi» o'yini: 👋 🙋 🐱) → kitobdagi jonli rasmlar, bosib o'ynaladi
    const board = emojiPictures(step.doska, lesson?.rasmlar, lesson?.rasm_sozlar);
    // REV121: rasm bo'lmasa — doskadagi emoji kartalar, sanoq saqlanadi («🍎🍎🍎» — uchta olma, «🔴🔵🔴🔵» — naqsh)
    const cards = boardCards(step.doska).map((e, i) => karta(e, { label: `rasm ${i + 1}` }));
    if (kidKind === "game") {
      // REV102: yangi darsdagi o'yinda faqat shu darsda o'rgatilgan so'zlarning rasmlari (o'tgan darslar rasmi chalg'itardi)
      const mine = board.filter((u) => newPics.has(u));
      const list = (mine.length ? mine : [...newPics]).slice(0, 3);
      if (list.length) return list.map(pic);
      if (cards.length) return cards;
    } else if (board.length >= 2) {
      return board.slice(0, 3).map(pic);   // bir qadamda 2–3 so'z («🟢 Green, 👏 Clap») — hammasining rasmi
    }
    if (step.rasm) return [pic(step.rasm, 0)];
    if (board.length) return board.slice(0, 3).map(pic);
    if (cards.length) return cards;
    // REV140: doska bo'sh qolmasin — ustoz aytayotgan so'zlarning kitobdagi rasmlari; kirish va xulosada — bugungi rasmlar
    const aytilgan = matnRasmlari(`${step.sarlavha || ""} ${kidSrc}`, lesson?.rasm_sozlar);
    if (aytilgan.length) return aytilgan.map(pic);
    if ((kidKind === "intro" || kidKind === "summary") && !step._ochilish && newPics.size) return [...newPics].slice(0, 3).map(pic);
    if (kidKind !== "new") return [];   // takror, o'yin — begona stiker chiqmaydi
    return stickerKeys(kidSrc).map((key) => ({ src: stickerUrl(key), svg: true, key, label: key, rev: picRev })).filter((x) => x.src);
  })();
  const badge = kindBadge(kidKind);
  const kidMood = kidPhase || (mode === "idle" || mode === "bridge" ? "wave" : speaking ? kabuMood(step, "speaking") : mode === "lesson" ? kabuMood(step, "waiting") : mode === "result" ? "happy" : "");
  const STICKER_SAY = { hello: "Hello!", red: "Red!", three: "Three!", big: "Big!", small: "Small!", cat: "Cat!", apple: "Apple!", jump: "I can jump!" };
  const tapKid = (i) => {
    const p = kidPics[i];
    if (!p) return;
    // REV121: o'yinda — javob sifatida tekshiriladi (to'g'ri — yulduz, xato — yulduz yo'q)
    if (game && game.stepIdx === idx) { if (!gameApi.current.tap(i)) pop(); return; }
    // O'yindan tashqarida bosish — maqtov emas: rasm silkinadi va (bilsa) nomi aytiladi
    setPicRev((r) => r + 1); pop();
    if (speakingRef.current) return;   // ustoz gapirayotgan bo'lsa — darsni bo'lmaydi
    if (p?.key) { say(`[en]${STICKER_SAY[p.key]}[/en]`); return; }
    const belgi = String(p?.emoji || p?.belgi || "").replace(/\uFE0F/g, "");
    const name = (belgi && lessonWords(steps, kinds).get(belgi)) || p?.soz || "";
    if (name) say(darsTil ? `[${darsTil}]${name}[/${darsTil}]` : izohTeg(name, izoh));
  };

  return <section className={`dx-root dx-aud-${audience} dx-theme-${theme} ${focus ? "dx-focus" : ""}`} aria-label={__kbUi("Dars xonasi")}>
    <header className="dx-head">
      {focus && <button type="button" className="dx-exit" onClick={exitLesson} aria-label={__kbUi("Darsni yopish")} title={__kbUi("Darsni yopish")}>{kid ? "🏠" : "✕"}</button>}
      <div>
        <h2>{lesson.topic?.mavzu || topicCode}</h2>
        {!kid && <p>{[lesson.topic?.fan, lesson.topic?.sinf && (/^\d+$/.test(String(lesson.topic.sinf)) ? `${lesson.topic.sinf}-sinf` : String(lesson.topic.sinf)), lesson.topic?.daraja && `${__kbUi("Daraja")} ${lesson.topic.daraja} / 30`].filter(Boolean).join(" · ")}</p>}
      </div>
      <div className="dx-head-actions">
        {!kid && <a className="dx-btn dx-link" href={downloadUrl("pdf")} download title={__kbUi("Ochiq dars ishlanmasi")}>{__kbUi("⬇ PDF")}</a>}
        {!kid && <a className="dx-btn dx-link" href={downloadUrl("docx")} download title={__kbUi("Ochiq dars ishlanmasi")}>{__kbUi("⬇ Word")}</a>}
        {kid && (questions.length > 0 || gameTotal > 0) && <span className="dx-chip dx-stars" aria-label={`${score + gameScore} ⭐`}>⭐ {score + gameScore}</span>}
        <span className="dx-chip">{mode === "test" ? __kbUi("Test") : mode === "ovoz" ? "🎤" : `${Math.max(1, idx + 1)} / ${steps.length}`}</span>
      </div>
    </header>
    <div className="dx-steps" role="group" aria-label={__kbUi("Dars qadamlari")}>
      {steps.map((s, i) => <button key={s.id} type="button" aria-label={`${i + 1}`} onClick={() => { setPlaying(false); go(i, false); }}
        className={`dx-step ${i < idx || ["test", "result", "end", "ovoz"].includes(mode) ? "is-done" : i === idx ? "is-now" : ""} ${kid ? `k-${kinds[i]}` : ""}`} />)}
    </div>

    <div className="dx-room">
      <div className="dx-frame">
        <div className="dx-board" aria-live="polite">
          {kid && badge && <div className={`dx-kind is-${kidKind}`} role="status"><span aria-hidden="true">{badge[0]}</span><small>{__kbUi(badge[1])}</small></div>}
          {kid && ["idle", "lesson", "bridge"].includes(mode) && <div className={`dx-kind-frame k-${kidKind || "none"}`}>{/* REV110: jonli ustoz va haqiqiy sinfxona */}<UstozSahna ustoz={ustozFor(fan || lesson?.topic?.fan)} mood={kidMood} celebrate={celebrate} pictures={kidPics} havo={havo} derazaga={mode === "lesson" && step?._ochilish === "havo"} doskaYoq={mode === "lesson" && Boolean(step?._ochilish)} vaqt={vaqt} shamol={shamol} speaking={speaking} mouth={mouthLevel} onTap={tapKid} />
            {mikSoz && mode === "lesson" && <div className={`dx-mic-soz is-${mikSoz.holat}`} role="status" aria-live="polite">
              <span className="dx-mic-ikon" aria-hidden="true">{mikSoz.holat === "ok" ? "⭐" : mikSoz.holat === "no" ? "💛" : "🎤"}</span>
              <b lang={mikSoz.lang}>{mikSoz.phrase}</b>
              {mikSoz.holat === "tingla" && <small>{__kbUi(mikSoz.urinish ? "Yana bir bor ayt!" : "Endi sen ayt!")}</small>}
            </div>}</div>}
          {/* REV145: dars boshida (salomlashish va kirish qismida) — bugun nimani o'rganadi (bola ham, yonidagi ota-ona ham aniq ko'radi) */}
          {kid && (mode === "idle" || (mode === "lesson" && idx <= opening.length)) && (() => {
            const sozlar = darsTil ? darsSozlari(steps.slice(opening.length), kinds.slice(opening.length)).slice(0, 5) : [];
            const maqsad = !sozlar.length && izoh === "uz" ? String(lesson.topic?.maqsad || "").trim() : "";
            if (!sozlar.length && !maqsad) return null;
            return <div className="dx-goal" aria-label={__kbUi("Bugun o‘rganamiz")}>
              <small>🎯 {__kbUi("Bugun o‘rganamiz")}</small>
              {sozlar.length ? <ul>{sozlar.map((w) => { const r = sozRasmi(w.say, w.emoji); return <li key={w.say}>
                {r ? <img src={r.src} alt="" draggable="false" /> : w.emoji ? <span aria-hidden="true">{w.emoji}</span> : null}<b lang={darsTil}>{w.say}</b></li>; })}</ul>
                : <p>{maqsad}</p>}
            </div>;
          })()}
          {!kid && mode === "idle" && <>
            <h3 className="dx-title">{__kbUi("Bugungi dars")}</h3>
            <div className="dx-line">{lesson.topic?.mavzu}</div>
            {lesson.topic?.maqsad && <div className="dx-line dx-small">{lesson.topic.maqsad}</div>}
            <div className="dx-line dx-small">{steps.length}{__kbUi(" qadam")}{questions.length ? ` · ${questions.length}${__kbUi(" ta savol")}` : ""}</div>
          </>}
          {!kid && mode === "lesson" && step && step.turi === "amaliy" && <>
            {step.sarlavha && <h3 className="dx-title"><BoardText text={step.sarlavha} /></h3>}
            <AmaliyDoska item={{ ...step, shart: step.doska, turi_nomi: step.turi_nomi }} say={say} hush={hush} mediaUrl={mediaUrl} kid={kid} />
          </>}
          {!kid && mode === "lesson" && step && step.turi !== "amaliy" && <>
            {steps[range[0]]?.sarlavha && <h3 className="dx-title"><BoardText text={steps[range[0]].sarlavha} /></h3>}
            <div className="dx-lines">
              {range.flatMap((i) => {
                const cue = boardCues(steps[i].doska, steps[i].ovoz || steps[i].doska);
                const shown = i === idx ? visibleLines(cue.cues, word, stepFinished || !speaking) : cue.lines.length;
                return cue.lines.slice(0, shown).map((line, n) => <div key={`${steps[i].id}-${n}`}
                  className={`dx-line ${i === idx ? "is-new" : ""} ${["qoida", "xulosa"].includes(steps[i].turi) ? "dx-rule" : ""}`}><BoardText text={line} /></div>);
              })}
            </div>
            {range.filter((i) => steps[i].rasm).map((i) => <img key={`img-${steps[i].id}`} className="dx-pic" src={mediaUrl(steps[i].rasm)} alt="" loading="lazy" />)}
            {/* REV89: til darsida bola iborani o'zi aytadi — mikrofon tanib, yulduz beradi */}
            {step.turi === "birga" && step.javob && <form className="dx-answer" onSubmit={submitAnswer}>
              <input value={answer} onChange={(e) => setAnswer(e.target.value)} aria-label={__kbUi("Javobingiz")} placeholder={step.savol || __kbUi("Javob")} autoComplete="off" />
              <button type="submit" className="dx-btn dx-primary">{__kbUi("Tekshirish")}</button>
              {feedback && <span className={feedback.ok ? "dx-ok" : "dx-no"}>{feedback.text}</span>}
            </form>}
            {variant && <div className="dx-variant">
              <span className="dx-tag">{variant.nom}</span>
              {variant.doska && <div className="dx-variant-board"><BoardText text={variant.doska} /></div>}
              {variant.rasm && <img className="dx-pic" src={mediaUrl(variant.rasm)} alt="" loading="lazy" />}
              <p>{variant.ovoz}</p>
              <div className="dx-row">
                {variant.takrorlash_topic_code && onOpenTopic && <button type="button" className="dx-btn" onClick={() => onOpenTopic(variant.takrorlash_topic_code)}>{__kbUi("Mavzuni ochish")}{variant.takrorlash_nomi ? `: ${variant.takrorlash_nomi}` : ""}</button>}
                <button type="button" className="dx-btn dx-primary" onClick={() => { setVariant(null); setPlaying(true); go(idx + 1, true); }}>{__kbUi("Tushundim, davom etamiz")}</button>
                <button type="button" className="dx-btn" onClick={dunno}>{__kbUi("Boshqa usul")}</button>
              </div>
            </div>}
          </>}
          {mode === "ovoz" && <VoiceCheck key={topicCode} items={voiceItems} audience={audience} say={say} hush={hush} speaking={speaking} onDone={voiceDone} bilgan={bilgan} izoh={izoh} />}
          {mode === "test" && q && <div className="dx-test">
            {kid && isReviewQuestion(q) && <div className="dx-kind is-review" role="status"><span aria-hidden="true">🔁</span><small>{__kbUi("Takrorlash")}</small></div>}
            {kid ? <div className="dx-kid-ask"><KidStage compact mood={kidPhase || (speaking ? "talk" : "think")} celebrate={celebrate} speaking={speaking} />
              {/* REV121: savoldagi rasmlar (naqsh, sanoq, ortiqchasi) — bola ko'rib o'ylaydi */}
              {questionCard(q.savol) && <div className={`dx-kid-qcard sz-${cardSize(questionCard(q.savol))}`} aria-hidden="true">{questionCard(q.savol)}</div>}
              <button type="button" className="dx-listen dx-listen-big" onClick={() => readQuestion(q)} aria-label={__kbUi("Qayta eshitish")}>🔊</button></div>
              : <><h3 className="dx-title">{__kbUi("Test")} · {testIndex + 1} / {questions.length}</h3>
                <div className="dx-q"><BoardText text={stripSpeechTags(q.savol)} /></div></>}
            {kid ? <div className={`dx-kid-opts dx-n${q.variantlar.length}`}>{kidOptions(Object.fromEntries(q.variantlar.map((o, k) => [`option_${"abcd"[k]}`, o])), q.savol).map((o, k) => <div key={k} className="dx-kid-wrap"><button type="button" onClick={() => pick(k)} disabled={picked !== null}
              className={picked === null ? `${hot === k ? "is-hot" : ""} ${waiting ? "is-waiting" : ""}` : k === q.togri ? "is-ok" : k === picked ? "is-no" : "is-dim"} style={{ "--i": k }}>{kidOptionPic(o, lesson?.rasmlar, mediaUrl, lesson?.rasm_sozlar) ? <img className="dx-kid-img" src={kidOptionPic(o, lesson?.rasmlar, mediaUrl, lesson?.rasm_sozlar)} alt="" draggable="false" /> : (keycapNumber(o.picture) ? <span className="dx-kid-pic kb-num">{keycapNumber(o.picture)}</span> : <span className={`dx-kid-pic sz-${cardSize(o.picture || "x")}`}>{o.picture || (o.listen ? k + 1 : o.letter)}</span>)}</button>
</div>)}</div>
            : <div className="dx-opts">{q.variantlar.map((o, k) => <button key={k} type="button" onClick={() => pick(k)}
              className={picked === null ? "" : k === q.togri ? "is-ok" : k === picked ? "is-no" : ""}>{"ABCD"[k]}) <BoardText text={stripSpeechTags(o)} /></button>)}</div>}
            {picked !== null && !kid && picked !== q.togri && <div className="dx-why">{!kid && <p>{q.izoh}</p>}<button type="button" className="dx-btn dx-primary" onClick={nextQuestion}>{__kbUi(testIndex + 1 >= questions.length ? (kid ? "Yulduzlarni ko‘rish ⭐" : "Natija") : (kid ? "Keyingisi ➜" : "Keyingi savol"))}</button></div>}
          </div>}
          {mode === "end" && <div className="dx-test">
            <h3 className="dx-title">{__kbUi("Dars tugadi")}</h3>
            {voice?.jami > 0 && <p className="dx-voice-score">🎤 {__kbUi("Ovozli tekshiruv")}: {voice.togri} / {voice.jami}</p>}
            <p className="dx-why">{__kbUi("Bilimingizni tekshiring. Savollar shu mavzuning Test bazasidan olinadi.")}</p>
            <div className="dx-row">
              {questions.length > 0 && <button type="button" className="dx-btn dx-primary" onClick={startQuiz}>{__kbUi(`Shu yerda ${questions.length} ta savol`)}</button>}
              {onOpenTest && <button type="button" className="dx-btn" onClick={onOpenTest}>{__kbUi("Test bo‘limida to‘liq test")}</button>}
              {voiceReady && <button type="button" className="dx-btn" onClick={() => { hush(); setVoice(null); voiceRef.current = null; setMode("ovoz"); }}>🎤 {__kbUi("Ovozli tekshiruvni qayta o‘tish")}</button>}
              <button type="button" className="dx-btn" onClick={() => { setPlaying(false); go(0, false); }}>{__kbUi("Darsni qaytadan ko‘rish")}</button>
              {nextLesson && <button type="button" className="dx-btn dx-next" onClick={() => { hush(); nextLesson.open(); }}>{__kbUi("Keyingi dars")}: {nextLesson.title} ➜</button>}
            </div>
            {!questions.length && !onOpenTest && <p className="dx-why">{__kbUi("Bu mavzu uchun Test bazasida savol hali yo‘q.")}</p>}
          </div>}
          {kid && mode === "limit" && <div className="dx-kid-end">
            <span className="dx-kid-big" aria-hidden="true">{limitKind === "vaqt" ? "⏰" : "🌙"}</span>
            <h3 className="dx-title">{__kbUi(limitKind === "vaqt" ? "Bugungi dars vaqti tugadi" : "Bugungi yangi darslar tugadi")}</h3>
            <p className="dx-kid-note">{__kbUi(limitText || "Yangi dars ertaga ochiladi. O‘tilgan darslarni takrorlash va o‘yinlar ochiq.")}</p>
            {onClose && <button type="button" className="dx-kid-go" onClick={() => { hush(); onClose(); }}>🏠 {__kbUi("Darslarga qaytish")}</button>}
          </div>}
          {kid && mode === "result" && <div className="dx-kid-end">
            <KidStage compact mood={kidMood} celebrate={celebrate} speaking={speaking} />
            <div className="dx-kid-stars" aria-label={`${kidResult?.yulduz ?? 0} ⭐`}>{[1, 2, 3].map((n) => <span key={n} className={n <= (kidResult?.yulduz ?? 0) ? "is-on" : ""} style={{ "--i": n }}>⭐</span>)}</div>
            {(questions.length > 0 || gameTotal > 0) && <p className="dx-kid-note">{score + gameScore} / {questions.length + gameTotal} ✓</p>}
            {voice?.jami > 0 && <p className="dx-kid-note">🎤 {voice.togri} / {voice.jami}</p>}
            {/* REV145: «Bugun o'rgandim» — har so'z rasmi bilan; aytgan so'ziga yulduz */}
            {kidResult?.sozlar?.length > 0 && <div className="dx-kid-words" aria-label={__kbUi("Bugun o‘rgandim")}>
              <small>{__kbUi("Bugun o‘rgandim")}</small>
              <ul>{kidResult.sozlar.map((w) => { const r = sozRasmi(w.soz, w.emoji); return <li key={w.soz} className={w.aytdi ? "is-ok" : ""}>
                {r ? <img src={r.src} alt="" draggable="false" /> : w.emoji ? <span aria-hidden="true">{w.emoji}</span> : null}
                <b lang={darsTil}>{w.soz}</b>{w.aytdi && <i aria-label={__kbUi("aytdi")}>⭐</i>}</li>; })}</ul>
            </div>}
            {nextLesson && !kidResult?.bugunTugadi
              ? <button type="button" className="dx-kid-go" onClick={() => { hush(); nextLesson.open(); }}>▶ {__kbUi("Keyingi dars")}</button>
              : <p className="dx-kid-note">🌙 {__kbUi("Bugungi darslar tugadi. Ertaga yangi dars ochiladi!")}</p>}
            <div className="dx-row">
              <button type="button" className="dx-btn" onClick={() => { setScore(0); setKidResult(null); gameRes.current = {}; setGameScore(0); setGameTotal(0); setPlaying(true); go(0, true); }}>🔁 {__kbUi("Yana bir bor")}</button>
              {onClose && <button type="button" className="dx-btn" onClick={() => { hush(); onClose(); }}>🏠 {__kbUi("Darslar")}</button>}
            </div>
          </div>}
          {!kid && mode === "result" && <div className="dx-test">
            <h3 className="dx-title">{__kbUi("Natija")}</h3>
            {questions.length > 0 && <div className="dx-score">{score} / {questions.length}</div>}
            {voice?.jami > 0 && <p className="dx-voice-score">🎤 {__kbUi("Ovozli tekshiruv")}: {voice.togri} / {voice.jami}</p>}
            <p className="dx-why">{pass ? __kbUi("Zo‘r! Mavzu o‘zlashtirildi.") : __kbUi("Asosiy qismni yana bir bor ko‘rib chiqamiz.")}</p>
            <div className="dx-row">
              {!pass && <button type="button" className="dx-btn dx-primary" onClick={() => { setPlaying(false); go(Math.max(0, steps.findIndex((s) => s.turi === "qoida")), false); }}>{__kbUi("Qoidani qayta ko‘rish")}</button>}
              {onOpenTest && <button type="button" className="dx-btn" onClick={onOpenTest}>{__kbUi("To‘liq testni ishlash")}</button>}
              {nextLesson && <button type="button" className="dx-btn dx-next" onClick={() => { hush(); nextLesson.open(); }}>{__kbUi("Keyingi dars")}: {nextLesson.title} ➜</button>}
            </div>
          </div>}
        </div>
        <div className="dx-ledge" aria-hidden="true" />
      </div>

      {!kid && <aside className={`dx-teacher ${speaking ? "is-speaking" : ""}`} aria-label={__kbUi("O‘qituvchi")}>
        <div className="dx-teacher-head">
          <div className="dx-avatar">{kid ? <span className="dx-bird" aria-hidden="true">🕊️</span> : <TeacherAvatar />}</div>
          <div><strong>{__kbUi(labels.teacher)}</strong><span className="dx-state"><i />{speaking ? __kbUi("Gapirmoqda…") : playing ? __kbUi("Tinglayapti") : __kbUi("Pauza")}</span></div>
        </div>
        <div className="dx-bubble">{words.map((w, i) => <span key={i} className={i === word ? "is-on" : ""}>{w} </span>)}</div>
        {!kid && <form className="dx-ask" onSubmit={(e) => { e.preventDefault(); ask(); }}>
          <label htmlFor={`dx-ask-${topicCode}`}>{__kbUi("O‘qituvchiga savol")}</label>
          <div className="dx-row"><input id={`dx-ask-${topicCode}`} value={question} onChange={(e) => setQuestion(e.target.value)} placeholder={__kbUi("Masalan: nega maxraj o‘zgarmaydi?")} disabled={asking} />
            <button type="submit" className="dx-btn" disabled={asking || !question.trim()}>{asking ? "…" : __kbUi("So‘rash")}</button></div>
          {askReply && <p className="dx-reply">{askReply}</p>}
        </form>}
        {lesson.manba?.kitob && <p className="dx-source">{__kbUi("Manba: ")}{lesson.manba.kitob}{lesson.auto ? __kbUi(" · kitob asosida avtomatik yig‘ilgan dars") : ""} · {APP_VERSION}</p>}
      </aside>}
    </div>

    {kid && <p className="dx-kid-ver" aria-hidden="true">{APP_VERSION}</p>}
    {menu && <div className="dx-menu" role="group" aria-label={__kbUi("Qayta tushuntirish usuli")}>
      <p>{__kbUi("Qaysi usulda qayta tushuntiray?")}</p>
      {list.map((v) => <button key={v.id} type="button" className="dx-btn" onClick={() => openVariant(v)}>{__kbUi(v.nom)}</button>)}
      <button type="button" className="dx-btn" onClick={() => { setMenu(false); setRate(0.85); rateRef.current = 0.85; if (step) { setStepFinished(false); say(boardCues(step.doska, step.ovoz || step.doska).spoken || step.doska, () => setStepFinished(true)); } }}>{__kbUi("Sekinroq qayta ayt")}</button>
      <button type="button" className="dx-btn" onClick={() => { setMenu(false); ask(`${__kbUi("Shu qismni tushunmadim, boshqacha tushuntiring")}: ${step?.doska || ""} ${step?.ovoz || ""}`.slice(0, 900)); }}>{__kbUi("AI ustozdan so‘rash")}</button>
    </div>}

    {mode !== "ovoz" && !(kid && ["test", "result", "limit", "bridge"].includes(mode)) && <div className={`dx-controls ${kid ? "dx-kid-controls" : ""}`}>
      <button type="button" className="dx-btn dx-primary" disabled={mode === "test"} onClick={togglePlay}>{kid
        ? <KidIcon icon={playing ? "⏸️" : "▶️"} label={playing ? "Pauza" : "Davom"} />
        : playing ? __kbUi("❚❚ Pauza") : mode === "idle" ? __kbUi(labels.start) : mode === "result" || mode === "end" ? __kbUi("↺ Qaytadan") : __kbUi("▶ Davom etish")}</button>
      {!kid && <button type="button" className="dx-btn" disabled={idx <= 0 || mode !== "lesson"} onClick={() => { setPlaying(false); go(idx - 1, false); }}>{__kbUi("‹ Oldingi")}</button>}
      {!kid && <button type="button" className="dx-btn" disabled={mode !== "lesson"} onClick={() => go(idx + 1)}>{__kbUi("Keyingi ›")}</button>}
      <button type="button" className="dx-btn" disabled={!step && !variant} onClick={() => { if (variant) { say(variant.ovoz); return; } if (step) { setStepFinished(false); say(boardCues(step.doska, step.ovoz || step.doska).spoken || step.doska, () => setStepFinished(true)); } }}>{kid ? <KidIcon icon="🔁" label="Yana ayt" /> : __kbUi("↻ Qayta ayt")}</button>
      <button type="button" className="dx-btn dx-help" disabled={mode !== "lesson"} onClick={dunno}>{kid ? <KidIcon icon="🙋" label="Tushuntir" /> : __kbUi("Tushunmadim")}</button>
      <span className="dx-spacer" />
      {!kid && <label className="dx-speed">{__kbUi("Tezlik")}
        <select value={rate} onChange={(e) => setRate(Number(e.target.value))}>
          <option value={0.85}>{__kbUi("Sekin")}</option><option value={1}>{__kbUi("O‘rtacha")}</option><option value={1.2}>{__kbUi("Tez")}</option>
        </select>
      </label>}
    </div>}
  </section>;
}
