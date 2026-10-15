import {uiText as __kbUi} from '../interface/interfaceRuntime.js';
import {useInterface as useKbInterfaceLocale} from '../interface/InterfacePreferences.jsx';
import React, { useCallback, useEffect, useRef, useState } from "react";
import { ArrowRight, Bird, Check, CheckCircle2, ChevronRight, Eye, EyeOff, LoaderCircle, LockKeyhole, Send, X } from "lucide-react";
import { authEndpoint, authRequest, challengeStorageKey } from "./authClient.js";
import { redirectIfWrongSite } from "./siteGuard.js";
import "./kabutar-login.css";
import TelegramCodeLogin from "./TelegramCodeLogin.jsx";
import { readTelegramLinkIntent } from "./telegramCodeClient.js";
import { InterfaceText, InterfaceSettingsButton, useInterface } from "../interface/InterfacePreferences.jsx";
import { LOGIN_ROLES, ROLE_NAMES, cachedAuthConfig, dropToken, forgetAccount, loginRole, methodLabel, rememberLoginMethod, saveAuthConfig, saveLoginRole, savedAccounts } from "./loginMemory.js";
import { saveTelegramPhone } from "./telegramCodeClient.js";
import { PRESCHOOL_GROUPS } from "../workspace/educationRules.js";

function GoogleMark() {
  return <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true"><path fill="#4285F4" d="M21.6 12.23c0-.71-.06-1.39-.18-2.05H12v3.88h5.38a4.6 4.6 0 0 1-2 3.02v2.51h3.24c1.9-1.75 2.98-4.33 2.98-7.36Z"/><path fill="#34A853" d="M12 22c2.7 0 4.96-.9 6.62-2.41l-3.24-2.51c-.9.6-2.05.97-3.38.97-2.6 0-4.8-1.76-5.6-4.12H3.06v2.59A10 10 0 0 0 12 22Z"/><path fill="#FBBC05" d="M6.4 13.93a6 6 0 0 1 0-3.86V7.48H3.06a10 10 0 0 0 0 9.04l3.34-2.59Z"/><path fill="#EA4335" d="M12 5.95c1.47 0 2.79.5 3.83 1.5l2.87-2.87A9.6 9.6 0 0 0 12 2a10 10 0 0 0-8.94 5.48l3.34 2.59c.8-2.36 3-4.12 5.6-4.12Z"/></svg>;
}

function safeStorage() {
  try { return window.sessionStorage; } catch { return null; }
}

function savePending(key, value) {
  try {
    const storage = safeStorage();
    if (value) storage?.setItem(key, JSON.stringify(value));
    else storage?.removeItem(key);
  } catch { /* Private browsing can restrict storage; this tab can still finish sign-in. */ }
}

// Both account linking and login use the code actually issued by the bot.
export function TelegramSignIn(props) {
  return <TelegramCodeLogin {...props}/>;
}

// REV146: server javob bermaganda ko'rsatiladigan bitta, tushunarli xabar (tarmoq xatosi bilan bir xil matn)
const SERVER_DOWN = "Server hozir javob bermadi (yangilanish yoki qayta ishga tushish bo‘lishi mumkin). 10–20 soniyadan keyin qayta bosing.";
const isServerDownText = (text) => text === SERVER_DOWN;

export default function KabutarLogin({ apiBase = "", onAuthenticated, initialError = "", onCourses }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const storageKey = challengeStorageKey(apiBase);
  // Oxirgi /auth/config keshdan darhol olinadi — kirish oynasi server javobini kutmaydi.
  const [config, setConfig] = useState(() => cachedAuthConfig());
  const [configLoading, setConfigLoading] = useState(() => !cachedAuthConfig());
  const [role, setRole] = useState(() => loginRole());
  const [accounts, setAccounts] = useState(() => savedAccounts());
  const [resuming, setResuming] = useState("");
  const [telegramKey, setTelegramKey] = useState(0);
  const [, setConfigError] = useState("");
  const [configAttempt, setConfigAttempt] = useState(0);
  const [method, setMethod] = useState("");
  const [quickRole, setQuickRole] = useState("");
  const [ageOpen, setAgeOpen] = useState(false);
  // REV94: rolni bosganda — shu roldagi eski akkauntga kiradi (yangi akkaunt faqat «➕ Yangi akkaunt» bilan).
  const [newMode, setNewMode] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(initialError);
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [success, setSuccess] = useState(false);
  const mounted = useRef(false);
  const command = useRef(null);
  const commandId = useRef(0);
  const authenticatedRef = useRef(onAuthenticated);
  const completed = useRef(false);
  const commandBusy = useRef(false);

  useEffect(() => { authenticatedRef.current = onAuthenticated; }, [onAuthenticated]);
  useEffect(() => { if (initialError) setError(initialError); }, [initialError]);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      commandId.current += 1;
      command.current?.abort();
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setConfigLoading(true);
    setConfigError("");
    let retry = null;
    authRequest(apiBase, "/auth/config", { signal: controller.signal })
      .then((data) => {
        if (controller.signal.aborted) return;
        // REV147: sahifa boshqa (ruxsat etilmagan) manzildan ochilgan — kirish bu yerda ishlamaydi, asosiy saytga o'tamiz
        if (redirectIfWrongSite(data)) { setError("Asosiy saytga o‘tilmoqda…"); return; }
        setConfig(data); saveAuthConfig(data); setConfigError(""); setError((e) => (isServerDownText(e) ? "" : e));
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setConfigError(err.message);
        // REV146: server qayta ishga tushayotgan bo'lsa — o'zi har 8 soniyada tekshiradi (2 daqiqagacha), tugma bosish shart emas
        if (configAttempt < 15) retry = setTimeout(() => setConfigAttempt((n) => n + 1), 8000);
      })
      .finally(() => { if (!controller.signal.aborted) setConfigLoading(false); });
    return () => { controller.abort(); clearTimeout(retry); };
  }, [apiBase, configAttempt]);

  const finish = useCallback((data) => {
    if (!mounted.current || completed.current) return;
    if (typeof data?.token !== "string" || !data.token) throw new Error("Kirish tasdiqlanmadi. Qayta urinib ko‘ring.");
    completed.current = true;
    if (data?.method) rememberLoginMethod(data.method, data.identifier || "");
    savePending(storageKey, null);
    setBusy(false);
    setPassword("");
    setSuccess(true);
    commandBusy.current = false;
    authenticatedRef.current?.(data.token);
  }, [storageKey]);

  useEffect(() => { savePending(storageKey, null); }, [storageKey]);

  const chooseMethod = (next) => {
    commandId.current += 1;
    command.current?.abort();
    commandBusy.current = false;
    setBusy(false);
    setMethod(next);
    setError("");
    setPassword("");
  };

  const loginWithPassword = async (event) => {
    event.preventDefault();
    if (commandBusy.current || !identifier.trim() || !password) return;
    commandBusy.current = true;
    const id = ++commandId.current;
    command.current?.abort();
    const controller = new AbortController();
    command.current = controller;
    setBusy(true);
    setError("");
    try {
      const data = await authRequest(apiBase, "/auth/password/login", { body: { identifier: identifier.trim(), password }, signal: controller.signal });
      if (mounted.current && id === commandId.current) finish({ ...data, method: "password", identifier: identifier.trim() });
    } catch (err) {
      if (mounted.current && id === commandId.current && !controller.signal.aborted) setError(err.message);
    } finally {
      if (mounted.current && id === commandId.current) { commandBusy.current = false; setBusy(false); }
    }
  };

  // Konfiguratsiya hali kelmagan bo'lsa ham tugmalar ochiq: server o'zi tekshiradi.
  const passwordEnabled = config ? config?.password?.enabled === true : true;
  const googleEnabled = config ? config?.google?.enabled === true : true;
  const pickRole = (next) => { setRole(next); saveLoginRole(next); };
  const startGoogle = () => { rememberLoginMethod("google"); window.location.assign(authEndpoint(apiBase, readTelegramLinkIntent() ? "/auth/google/login?intent=telegram" : "/auth/google/login")); };

  // Oldin shu qurilmada kirgan akkaunt: sessiya tirik bo'lsa bir bosishda kiradi,
  // tugagan bo'lsa kirish usuli va login oldindan to'ldiriladi.
  const resume = async (account) => {
    if (resuming) return;
    setError("");
    if (account.role) pickRole(account.role);
    if (account.token) {
      setResuming(String(account.user_id));
      // REV146: server javob bermasa — bosish «osilib» qolmaydi: 12 soniyada to'xtaydi, 2 marta o'zi qayta uradi.
      // Token FAQAT server «sessiya tugagan» (401/403) desa o'chadi — 502/503 (server qayta ishga tushyapti) da saqlanadi,
      // aks holda Telegram/Gmail'ga ulanmagan akkaunt butunlay yo'qolardi.
      let natija = "tarmoq";
      try {
        for (let urinish = 0; urinish < 3 && mounted.current; urinish += 1) {
          if (urinish) await new Promise((resolve) => setTimeout(resolve, 2500 * urinish));
          const controller = new AbortController();
          const timer = setTimeout(() => controller.abort(), 12000);
          try {
            const response = await fetch(authEndpoint(apiBase, "/auth/men"), { headers: { Authorization: `Bearer ${account.token}`, Accept: "application/json" }, cache: "no-store", signal: controller.signal });
            if (response.ok) { natija = "ok"; break; }
            if (response.status === 401 || response.status === 403) { natija = "tugagan"; break; }
            natija = "tarmoq";   // 5xx — server hali tayyor emas
          } catch { natija = "tarmoq"; }
          finally { clearTimeout(timer); }
        }
      } finally { if (mounted.current) setResuming(""); }
      if (!mounted.current) return;
      if (natija === "ok") { finish({ token: account.token }); return; }
      if (natija === "tarmoq") { setError(SERVER_DOWN); return; }
      setAccounts(dropToken(account.token));
    }
    if (account.method === "google" && googleEnabled) { startGoogle(); return; }
    if (account.method === "password") { chooseMethod("password"); setIdentifier(account.identifier || ""); return; }
    if (account.method === "quick") { setError("Bu akkaunt Telegram yoki Gmail’ga ulanmagan edi va sessiyasi tugagan. Rolni bosib yangidan boshlang yoki Telegram orqali kiring."); return; }
    chooseMethod("telegram"); setTelegramKey((value) => value + 1);
    setError("Sessiya tugagan. Telegram botdan yangi kod olib kiring — bir daqiqa.");
  };

  // REV79: rolni bosish — darhol kirish (shu qurilmada yangi akkaunt). Oldin kirganlar pastdan.
  const quickStart = async (next, ageGroup = "") => {
    if (commandBusy.current || resuming) return;
    const existing = !newMode && accounts.find((a) => a.role === next && a.token);
    if (existing) { resume(existing); return; }
    if (next === "bogcha" && !ageGroup) { setAgeOpen(true); pickRole(next); return; }
    pickRole(next);
    commandBusy.current = true;
    const id = ++commandId.current;
    command.current?.abort();
    const controller = new AbortController();
    command.current = controller;
    setBusy(true); setQuickRole(next); setError("");
    try {
      const body = { role: next, age_group: ageGroup || undefined };
      let data;
      // REV107/146: server bir lahza javob bermasa — o'zi yana 2 marta (2.5 va 5 soniyadan keyin) qayta urinadi.
      for (let urinish = 0; ; urinish += 1) {
        try { data = await authRequest(apiBase, "/auth/quick/start", { body, signal: controller.signal }); break; }
        catch (err) {
          if (!err?.network || controller.signal.aborted || urinish >= 2) throw err;
          await new Promise((resolve) => setTimeout(resolve, 2500 * (urinish + 1)));
          if (controller.signal.aborted) throw err;
        }
      }
      if (mounted.current && id === commandId.current) finish({ ...data, method: "quick" });
    } catch (err) {
      if (mounted.current && id === commandId.current && !controller.signal.aborted) setError(err.message);
    } finally {
      if (mounted.current && id === commandId.current) { commandBusy.current = false; setBusy(false); setQuickRole(""); }
    }
  };
  const toggleMethod = (next) => { if (method === next) chooseMethod(""); else chooseMethod(next); };

  return <main className="kb-login-page kb-login-compact kb-login-v79">
    <div className="kb-login-shell">
      <header className="kb-login-header">
        <a className="kb-login-brand" href="#kabutar-signin" aria-label={uiT("Kabutar bosh sahifasi")}>
          <span className="kb-login-brand-mark"><Bird size={29} strokeWidth={1.8}/></span>
          <span>{__kbUi("Kabutar")}<span className="kb-login-brand-caption"><InterfaceText text={__kbUi("SUHBAT VA TA’LIM")}/></span></span>
        </a>
        <nav aria-label={uiT("Bosh sahifa")}>{onCourses && <button type="button" className="kb-login-courses" onClick={onCourses}><InterfaceText text={__kbUi("Kurslar")}/></button>}<InterfaceSettingsButton/></nav>
      </header>

      <div className="kb-login-main kb-login-main-single">
        <section className="kb-login-access" id="kabutar-signin" aria-labelledby="kabutar-signin-title">
          <div className="kb-login-card">
            {success ? <div className="kb-login-success" role="status"><CheckCircle2 size={36}/><h3><InterfaceText text={__kbUi("Xush kelibsiz!")}/></h3><p><InterfaceText text={__kbUi("Sahifa ochilmoqda…")}/></p></div> : <>
              <h2 id="kabutar-signin-title"><InterfaceText text={__kbUi("Kim sifatida kirasiz?")}/></h2>
              <p className="kb-login-lead-v79"><InterfaceText text={__kbUi("Yangi bo‘lsangiz — bosing va darhol kirasiz.")}/></p>

              {error && <div className="kb-login-error" role="alert">{__kbUi(error)}<button type="button" onClick={() => setError("")} aria-label={uiT("Xato xabarini yopish")}><X size={16}/></button></div>}

              {accounts.length > 0 && <div className="kb-login-saved" aria-label={uiT("Shu qurilmada kirgan akkauntlar")}>
                <p className="kb-login-step"><InterfaceText text={__kbUi("Oldin kirgansiz — shu yerdan davom eting:")}/></p>
                {accounts.map((account) => <div key={account.user_id} className="kb-login-saved-item">
                  <button type="button" onClick={() => resume(account)} disabled={Boolean(resuming) || busy}>
                    <span className="kb-login-avatar" aria-hidden="true">{String(account.name || "?").trim().charAt(0).toUpperCase()}</span>
                    <span className="kb-login-saved-text"><b>{account.name}</b><small>{[ROLE_NAMES[account.role] && uiT(ROLE_NAMES[account.role]), account.token ? uiT("bir bosishda") : methodLabel(account.method)].filter(Boolean).join(" · ")}</small></span>
                    {resuming === String(account.user_id) ? <LoaderCircle size={17} className="kb-login-spin"/> : <ChevronRight size={17}/>}
                  </button>
                  <button type="button" className="kb-login-saved-remove" aria-label={uiT("Bu qurilmadan olib tashlash")} title={uiT("Bu qurilmadan olib tashlash")} onClick={() => setAccounts(forgetAccount(account.user_id))}><X size={14}/></button>
                </div>)}
              </div>}
              {accounts.length === 0 && <button type="button" className="kb-login-old-hint" onClick={() => { chooseMethod("telegram"); setTimeout(() => document.querySelector(".kb-login-method-panel")?.scrollIntoView({ behavior: "smooth", block: "center" }), 60); }}>
                <span aria-hidden="true">👋</span><span><b>{__kbUi("Oldin ro‘yxatdan o‘tganmisiz?")}</b> {__kbUi("Telegram bilan kiring — testlaringiz va natijalaringiz o‘sha akkauntda.")}</span><ChevronRight size={16}/>
              </button>}

              {accounts.some((a) => a.token) && <p className="kb-login-new-hint">
                {newMode
                  ? <>{__kbUi("Yangi akkaunt ochiladi — rolni tanlang.")} <button type="button" onClick={() => setNewMode(false)}>{__kbUi("Bekor")}</button></>
                  : <>{__kbUi("Rolni bossangiz — shu roldagi akkauntingizga kirasiz.")} <button type="button" onClick={() => setNewMode(true)}>➕ {__kbUi("Yangi akkaunt ochish")}</button></>}
              </p>}
              <div className="kb-login-role-cards" role="group" aria-label={uiT("Rol")}>
                {LOGIN_ROLES.map(([id, name, icon, hint]) => <button key={id} type="button" className={`kb-login-role-card kb-role-${id}${role === id ? " is-last" : ""}`} onClick={() => quickStart(id)} disabled={busy || Boolean(resuming)}>
                  <span className="kb-login-role-emoji" aria-hidden="true">{icon}</span>
                  <b>{uiT(name)}</b>
                  <small>{uiT(hint)}</small>
                  <span className="kb-login-role-go" aria-hidden="true">{quickRole === id ? <LoaderCircle size={16} className="kb-login-spin"/> : <ArrowRight size={16}/>}</span>
                </button>)}
              </div>
              {ageOpen && <div className="kb-login-age" role="group" aria-label={uiT("Bolaning yoshi")}>
                <p>🧸 {__kbUi("Bolangiz necha yoshda?")}</p>
                <div>{PRESCHOOL_GROUPS.map((g) => <button key={g} type="button" disabled={busy} onClick={() => quickStart("bogcha", g)}>{quickRole === "bogcha" && busy ? <LoaderCircle size={14} className="kb-login-spin"/> : null}{g.replace("-", "–")}</button>)}</div>
              </div>}


              <div className="kb-login-divider"><span/><InterfaceText text={__kbUi("Akkauntingiz bormi? Shu orqali kiring")}/><span/></div>
              <div className="kb-login-mini-methods" role="group" aria-label={uiT("Kirish usuli")}>
                <button type="button" className={`kb-mini-tg${method === "telegram" ? " is-open" : ""}`} onClick={() => toggleMethod("telegram")} aria-expanded={method === "telegram"}><Send size={15}/>{__kbUi("Telegram")}</button>
                <button type="button" className="kb-mini-google" disabled={busy || !googleEnabled} onClick={startGoogle}><GoogleMark/>{__kbUi("Google")}</button>
                <button type="button" className={`kb-mini-pass${method === "password" ? " is-open" : ""}`} onClick={() => toggleMethod("password")} aria-expanded={method === "password"}><LockKeyhole size={15}/><InterfaceText text={__kbUi("Parol")}/></button>
              </div>
              {/* REV146: sozlama kelmasa ham qizil xato ko'rsatilmaydi — tugmalar baribir ishlaydi, sozlama fonda o'zi qayta so'raladi */}
              {config && !googleEnabled && method === "google" && <p className="kb-login-poll-notice"><InterfaceText text={__kbUi("Google orqali kirish hozir sozlanmagan.")}/></p>}

              {method === "telegram" && <div className="kb-login-method-panel"><TelegramCodeLogin key={telegramKey} apiBase={apiBase} config={config} onAuthenticated={(data) => finish({ ...data, method: "telegram" })}/></div>}

              {method === "password" && <form className="kb-login-password-form kb-login-method-panel" onSubmit={loginWithPassword}>
                <label htmlFor="kabutar-login-identifier"><InterfaceText text={__kbUi("Telefon, KB raqami, nik yoki email")}/></label>
                <input id="kabutar-login-identifier" name="username" type="text" autoComplete="username" autoCapitalize="none" spellCheck={false} value={identifier} onChange={(event) => setIdentifier(event.target.value)} placeholder={uiT("+998… yoki KB-123456")} maxLength={254} required disabled={busy}/>
                <label htmlFor="kabutar-login-password"><InterfaceText text={__kbUi("Parol")}/></label>
                <div className="kb-login-password-input"><input id="kabutar-login-password" name="password" type={showPassword ? "text" : "password"} autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder={uiT("Parolingizni kiriting")} maxLength={128} required disabled={busy}/><button type="button" aria-label={showPassword ? uiT("Parolni yashirish") : uiT("Parolni ko‘rsatish")} aria-pressed={showPassword} onClick={() => setShowPassword((visible) => !visible)}>{showPassword ? <EyeOff size={19}/> : <Eye size={19}/>}</button></div>
                <button className="kb-login-primary" type="submit" disabled={busy || !passwordEnabled || !identifier.trim() || !password}>{busy ? <LoaderCircle size={19} className="kb-login-spin"/> : <LockKeyhole size={19}/>} {busy ? uiT("Tekshirilmoqda…") : uiT("Kirish")}{!busy && <ArrowRight size={18}/>}</button>
                {config && !passwordEnabled && <p className="kb-login-poll-notice"><InterfaceText text={__kbUi("Parol orqali kirish hozir mavjud emas.")}/></p>}
                <button type="button" className="kb-login-text-button" onClick={() => chooseMethod("telegram")}><InterfaceText text={__kbUi("Parol esingizdan chiqdimi? Telegram orqali kiring")}/></button>
              </form>}
            </>}
          </div>
          <div className="kb-login-card-foot"><Check size={15}/><span><InterfaceText text={__kbUi("Kirgach Telegram yoki Gmail ulang — akkauntingiz va natijalaringiz hech qachon yo‘qolmaydi.")}/></span></div>
        </section>
      </div>
    </div>
  </main>;
}
