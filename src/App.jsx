import { prepareSpeech, SPEECH_REVISION } from "./speech/pronunciation.js";
import { lessonDownloadUrl } from "./lesson/darsXonasiRules.js";
import { captureTelegramArrival, clearTelegramLinkIntent, readTelegramLinkIntent } from "./auth/telegramCodeClient.js";
import { splitSpeechText, selectBrowserVoice } from "./speech/language.js";
import {EducationHome} from './workspace/EducationSetup.jsx';
import {educationRole, initialEducationTab, needsEducation, roleDetail} from './workspace/educationRules.js';
import {useTranslatedContent,ContentTranslationStatus} from './interface/TranslatedContent.jsx';
import {setTranslationSession} from './interface/interfaceRuntime.js';
import {uiText as __kbUi, interfaceLocaleTag as __kbLocaleTag} from './interface/interfaceRuntime.js';
import {useInterface as useKbInterfaceLocale} from './interface/InterfacePreferences.jsx';
import LearnerTopics from './curriculum/LearnerTopics.jsx';
import AdminSpeechStudio from './admin/AdminSpeechStudio.jsx';
import Kutubxonam from './teacher/Kutubxonam.jsx';
import TogarakJurnal from './teacher/TogarakJurnal.jsx';
import SectionErrorBoundary from './workspace/AppErrorBoundary.jsx';
import {LearnerCurriculumHeader} from './curriculum/CurriculumTabs.jsx';
import {matchingSubjects,gradeLabel,semesterPairLabel,institutionLabel,lessonLabel,profileInstitutionType} from './curriculum/catalog.js';
import CurriculumBoundary, { useCurriculum } from "./curriculum/CurriculumScope.jsx";
import AdminTestBrowser from './curriculum/AdminTestBrowser.jsx';
// REV52: live auth and membership modules share one implementation.
// REV42: personal curriculum planner and database-grounded assistant.
// REV38: archive-filtered institutions and explicit account/activity counts.
// REV35: new components included so existing-file uploads keep every dependency.
import * as __kbRev35_external0 from "react";
import * as __kbRev35_external1 from "lucide-react";
import * as __kbRev35_external2 from "react-dom";
import KabutarAssistant, { KabutarAssistantButton } from "./assistant/KabutarAssistant.jsx";
import KitobKodQidiruv from "./lesson/KitobKod.jsx";
import { kitobKodimi } from "./lesson/kitobKodRules.js";
import AccountNotice from "./auth/AccountNotice.jsx";
import { clearFamily, isFamilyProfileUser, isProfileSession, readFamily, writeFamily } from "./auth/familyProfiles.js";
import { LOGIN_ROLES, ROLE_NAMES as LOGIN_ROLE_NAMES, accountRole as loginAccountRole, dropToken as dropSavedToken, keepsSessionOnLogout as keepsQuickSession, loginRole as savedLoginRole, rememberAccount, saveLoginRole, takeLoginMethod } from "./auth/loginMemory.js";
const CourseWorkspace = __kbRev35_external0.lazy(() => import("./courses/CourseWorkspace.jsx"));
const FamilyProfiles = __kbRev35_external0.lazy(() => import("./auth/FamilyProfiles.jsx"));
const TeacherSubjects = __kbRev35_external0.lazy(() => import("./teacher/TeacherSubjects.jsx"));
const PresentationStudio = __kbRev35_external0.lazy(() => import("./presentations/PresentationStudio.jsx"));
import { InterfaceText, InterfaceSettingsButton, useInterface } from "./interface/InterfacePreferences.jsx";
import * as __kbRev35_module1 from "./auth/authClient.js";

import * as __kbRev35_module0 from "./auth/KabutarLogin.jsx";

import * as __kbRev35_module2 from "./auth/KabutarRegistration.jsx";

import * as __kbRev35_module4 from "./workspace/kabutarWorkspaceClient.js";

import * as __kbRev35_module3 from "./workspace/EducationSetup.jsx";
import JoinInstitution from "./workspace/JoinInstitution.jsx";
import MeningInstitutim, { AdminInstitutHayoti, AdminInstitutTanlash } from "./institute/InstitutHayoti.jsx";
import { accountRole as _kbAccountRole } from "./auth/loginMemory.js";

// Included from workspace/AccountSecurity.jsx; implementation preserved.
const __kbRev35_module5 = (() => {
const React = __kbRev35_external0["default"];
const useEffect = __kbRev35_external0["useEffect"];
const useRef = __kbRev35_external0["useRef"];
const useState = __kbRev35_external0["useState"];
const createPortal = __kbRev35_external2["createPortal"];
const AtSign = __kbRev35_external1["AtSign"];
const CheckCircle2 = __kbRev35_external1["CheckCircle2"];
const ChevronRight = __kbRev35_external1["ChevronRight"];
const Eye = __kbRev35_external1["Eye"];
const EyeOff = __kbRev35_external1["EyeOff"];
const KeyRound = __kbRev35_external1["KeyRound"];
const LoaderCircle = __kbRev35_external1["LoaderCircle"];
const LogOut = __kbRev35_external1["LogOut"];
const Send = __kbRev35_external1["Send"];
const ShieldCheck = __kbRev35_external1["ShieldCheck"];
const X = __kbRev35_external1["X"];
const TelegramSignIn = __kbRev35_module0["TelegramSignIn"];
const authEndpoint = __kbRev35_module1["authEndpoint"];
const workspaceRequest = __kbRev35_module4["workspaceRequest"];


function AccountSecurity({ apiBase, token, onToken, onClose, onLogout, initialTelegramOpen = false, onChangeRole }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [profile, setProfile] = useState(null);
  const [discovery, setDiscovery] = useState(null);
  const [discoveryError, setDiscoveryError] = useState("");
  const [nickname, setNickname] = useState("");
  const [phoneDiscoverable, setPhoneDiscoverable] = useState(false);
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [telegramOpen, setTelegramOpen] = useState(initialTelegramOpen);
  const [currentPassword, setCurrentPassword] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [resetPassword, setResetPassword] = useState(false);
  const [busy, setBusy] = useState("");
  const panel = useRef(null);
  const closeButton = useRef(null);
  const mounted = useRef(false);
  const request = useRef(null);
  const close = useRef(onClose);
  useEffect(() => { close.current = onClose; }, [onClose]);

  useEffect(() => {
    mounted.current = true;
    const previous = document.activeElement;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButton.current?.focus();
    const keydown = (event) => {
      if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); close.current?.(); return; }
      if (event.key !== "Tab") return;
      const elements = [...(panel.current?.querySelectorAll('button:not(:disabled), a[href], input:not(:disabled), [tabindex="0"]') || [])].filter((element) => element.getClientRects().length);
      const first = elements[0], last = elements[elements.length - 1];
      if (!first) { event.preventDefault(); panel.current?.focus(); return; }
      if (event.shiftKey && (document.activeElement === first || !panel.current?.contains(document.activeElement))) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && (document.activeElement === last || !panel.current?.contains(document.activeElement))) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", keydown, true);
    return () => {
      mounted.current = false;
      request.current?.abort();
      document.removeEventListener("keydown", keydown, true);
      document.body.style.overflow = overflow;
      if (previous?.isConnected) previous.focus?.();
    };
  }, []);

  useEffect(() => {
    request.current?.abort();
    setBusy("");
    setCurrentPassword("");
    setPassword("");
    setConfirmation("");
    setResetPassword(false);
    setTelegramOpen(false);
    setProfile(null);
    setDiscovery(null);
  }, [token]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    setDiscoveryError("");
    Promise.allSettled([
      workspaceRequest(apiBase, "/auth/profile/status", token, { signal: controller.signal }),
      workspaceRequest(apiBase, "/auth/profile/discovery", token, { signal: controller.signal }),
    ])
      .then(([accountResult, discoveryResult]) => {
        if (controller.signal.aborted) return;
        if (accountResult.status === "fulfilled") setProfile(accountResult.value);
        else setError(accountResult.reason.message);
        if (discoveryResult.status === "fulfilled") {
          const data = discoveryResult.value;
          setDiscovery(data);
          setNickname(data.nickname || "");
          setPhoneDiscoverable(data.phone_discoverable === true);
        } else setDiscoveryError(discoveryResult.reason.message);
      })
      .catch((err) => { if (!controller.signal.aborted) setError(err.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [apiBase, token, retry]);

  async function changePassword(event) {
    event.preventDefault();
    if (busy) return;
    setNotice("");
    setError("");
    if (!profile) { setError("Avval hisob ma’lumotlari yuklanishini kuting."); return; }
    if (password.length < 10 || password.length > 128) { setError("Yangi parol 10–128 belgidan iborat bo‘lsin."); return; }
    if (password !== confirmation) { setError("Yangi parol va tasdiqlash bir xil emas."); return; }
    if (profile.has_password && !resetPassword && !currentPassword) { setError("Amaldagi parolingizni kiriting."); return; }
    const controller = new AbortController();
    request.current?.abort();
    request.current = controller;
    setBusy("password");
    try {
      const data = await workspaceRequest(apiBase, "/auth/password/set", token, {
        method: "POST", signal: controller.signal,
        body: { password, reset: resetPassword, ...(profile.has_password && !resetPassword ? { current_password: currentPassword } : {}) },
      });
      if (!mounted.current || controller.signal.aborted) return;
      if (!data.ok) throw new Error("Parol saqlangani tasdiqlanmadi. Qayta urinib ko‘ring.");
      setCurrentPassword(""); setPassword(""); setConfirmation(""); setShowPassword(false);
      setResetPassword(false);
      setNotice("Parol saqlandi. Boshqa qurilmalardagi kirish seanslari tugatildi.");
      setProfile((old) => ({ ...old, has_password: true }));
      if (data.token) onToken?.(data.token);
    } catch (err) {
      if (mounted.current && !controller.signal.aborted) setError(err.message);
    } finally {
      if (mounted.current && !controller.signal.aborted) setBusy("");
    }
  }

  async function saveDiscovery(event) {
    event.preventDefault();
    if (busy || !discovery) return;
    const clean = nickname.trim().replace(/^@/, "");
    setNotice(""); setError(""); setDiscoveryError("");
    if (clean && !/^[A-Za-z][A-Za-z0-9_]{4,31}$/.test(clean)) {
      setDiscoveryError("Nik 5–32 belgidan iborat bo‘lsin: avval lotin harfi, keyin harf, raqam yoki pastki chiziq (_).");
      return;
    }
    if (phoneDiscoverable && !discovery.phone_verified) {
      setDiscoveryError("Telefon bo‘yicha topilish uchun avval o‘z raqamingizni Telegram orqali tasdiqlang.");
      return;
    }
    const controller = new AbortController();
    request.current?.abort(); request.current = controller;
    setBusy("discovery");
    try {
      const data = await workspaceRequest(apiBase, "/auth/profile/discovery", token, {
        method: "POST", signal: controller.signal,
        body: { nickname: clean || null, phone_discoverable: phoneDiscoverable },
      });
      if (!mounted.current || controller.signal.aborted) return;
      setDiscovery(data); setNickname(data.nickname || ""); setPhoneDiscoverable(data.phone_discoverable === true);
      setNotice("Qidiruv sozlamalari saqlandi. KB raqamingiz o‘zgarmadi.");
    } catch (err) {
      if (mounted.current && !controller.signal.aborted) setDiscoveryError(err.message);
    } finally {
      if (mounted.current && !controller.signal.aborted) setBusy("");
    }
  }

  function linkGoogle() {
    setError("");
    try { window.sessionStorage.setItem("kabutar_google_link_intent", JSON.stringify({ session: token, createdAt: Date.now() })); }
    catch { setError("Brauzer ulash so‘rovini saqlay olmadi. Brauzerda sayt ma’lumotlarini saqlashga ruxsat bering va qayta urinib ko‘ring."); return; }
    window.location.assign(authEndpoint(apiBase, "/auth/google/login?intent=link"));
  }

  async function logout(allDevices) {
    if (busy) return;
    setBusy(allDevices ? "logout-all" : "logout"); setError(""); setNotice("");
    try { await onLogout?.(allDevices); }
    catch (err) { if (mounted.current) setError(err?.message || "Chiqish tasdiqlanmadi. Qayta urinib ko‘ring."); }
    finally { if (mounted.current) setBusy(""); }
  }

  const telegramLinked = profile?.identities?.telegram === true;
  const googleLinked = profile?.identities?.google === true;

  return createPortal(<div className="kb-security-overlay" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose?.(); }}>
    <div className="kb-security-panel" role="dialog" aria-modal="true" aria-labelledby="kb-security-title" aria-describedby="kb-security-description" tabIndex={-1} ref={panel}>
      <header><div><span className="kb-security-eyebrow"><ShieldCheck size={15}/>{__kbUi(" SIZNING HISOBINGIZ")}</span><h2 id="kb-security-title">{__kbUi("Kirish va xavfsizlik")}</h2></div><button className="kb-security-close" type="button" onClick={onClose} aria-label={__kbUi("Xavfsizlik oynasini yopish")} ref={closeButton}><X size={20}/></button></header>
      <p id="kb-security-description" className="kb-work-note">{__kbUi("Kirish usullarini bitta hisobingizga ulang. KB raqamingiz va suhbatlaringiz shu hisobda qoladi.")}</p>
      {error && <div className="kb-work-error" role="alert">{__kbUi(error)}</div>}
      {notice && <div className="kb-security-notice" role="status"><CheckCircle2 size={17}/>{__kbUi(notice)}</div>}
      {loading ? <p className="kb-security-loading" role="status"><LoaderCircle size={18} className="kb-login-spin"/>{__kbUi(" Hisob ma’lumotlari yuklanmoqda…")}</p> : !profile ? <button type="button" onClick={() => setRetry((value) => value + 1)}><InterfaceText text={__kbUi("Qayta yuklash")}/></button> : <>
        <section aria-label={__kbUi("Ulangan kirish usullari")}>
          <h3>{__kbUi("Ulangan hisoblar")}</h3>
          <div className="kb-security-identities">
            <div><span className="kb-security-provider-icon"><Send size={19}/></span><div><strong>{__kbUi("Telegram")}</strong><small>{telegramLinked ? profile.phone_masked || __kbUi("Telefon tasdiqlangan") : __kbUi("Telefon raqamingiz bilan tasdiqlash")}</small></div>{telegramLinked ? <span className="kb-security-linked"><CheckCircle2 size={14}/>{__kbUi(" Ulangan")}</span> : <button type="button" onClick={() => setTelegramOpen(true)} disabled={Boolean(busy)}>{__kbUi("Ulash ")}<ChevronRight size={14}/></button>}</div>
            <div><span className="kb-security-provider-icon kb-security-google-mark">{__kbUi("G")}</span><div><strong>{__kbUi("Google")}</strong><small>{googleLinked ? __kbUi("Google hisobingiz ulangan") : __kbUi("Google hisobingiz orqali qayta kirish")}</small></div>{googleLinked ? <span className="kb-security-linked"><CheckCircle2 size={14}/>{__kbUi(" Ulangan")}</span> : <button type="button" onClick={linkGoogle} disabled={Boolean(busy)}>{__kbUi("Ulash ")}<ChevronRight size={14}/></button>}</div>
          </div>
          {telegramOpen && <TelegramSignIn apiBase={apiBase} token={token} mode="link" onCancel={() => setTelegramOpen(false)} onAuthenticated={(data) => {
            setTelegramOpen(false);
            if (data?.switched && data?.token) {
              // REV79: bu Telegram eski akkauntga tegishli — bo'sh tez akkauntdan o'sha akkauntga o'tamiz.
              try { window.sessionStorage.setItem("kabutar:switched-notice", "Bu Telegram eski akkauntingizga ulangan edi — o‘sha akkauntga o‘tdingiz. Testlaringiz va natijalaringiz joyida."); } catch { /* ixtiyoriy */ }
              onToken?.(data.token);
              return;
            }
            setNotice("Telegram shu hisobingizga ulandi.");
            if (data?.token) onToken?.(data.token);
            setRetry((value) => value + 1);
          }}/>} 
          <p className="kb-work-note">{__kbUi("Google yoki Telegram boshqa Kabutar hisobiga ulangan bo‘lsa, hisoblar avtomatik birlashtirilmaydi.")}</p>
        </section>
        {onChangeRole && <section aria-labelledby="kb-role-heading">
          <h3 id="kb-role-heading">{__kbUi("Rolim")}</h3>
          <p className="kb-work-note">{__kbUi("Hozirgi rol: ")}<b>{__kbUi(LOGIN_ROLE_NAMES[profile.education_role === "talaba" || profile.learning_profile?.role === "talaba" ? "talaba" : profile.education_role] || "—")}</b>{__kbUi(". Xohlagan paytda almashtirasiz.")}</p>
          {profile.role_locked ? <p className="kb-role-locked">🔒 {__kbUi(profile.role_lock_reason === "admin" ? "Administrator rolini bu yerdan almashtirib bo‘lmaydi." : profile.role_lock_reason === "institut" ? "Siz institutga talaba sifatida ulangansiz. Rolni almashtirish uchun avval Profil → «Institut va kurs» bo‘limidan institutdan chiqing." : "Akkauntingiz muassasaga ulangan — rolingizni muassasa belgilaydi. O‘zgartirish uchun muassasa rahbariga murojaat qiling.")}</p> : <><div className="kb-security-roles" role="group" aria-label={__kbUi("Rolni tanlash")}>
            {LOGIN_ROLES.map(([id, name, icon]) => { const current = (profile.learning_profile?.role === "talaba" ? "talaba" : profile.education_role) === id; return <button key={id} type="button" aria-pressed={current} disabled={Boolean(busy)} onClick={() => { if (!current) onChangeRole(id); }}>{icon} {__kbUi(name)}</button>; })}
          </div>
          <p className="kb-work-note">{__kbUi("Diqqat: rol o‘zgarsa, sinf/kurs va til sozlamalarini ham to‘ldirasiz. To‘ldirilmasa testlar va mavzular sizga mos chiqmaydi. Muassasaga ulangan hisobda rolni muassasa belgilaydi.")}</p>
        </>}</section>}
        <section aria-labelledby="kb-discovery-heading">
          <h3 id="kb-discovery-heading"><AtSign size={18}/>{__kbUi(" Sizni qanday topishsin?")}</h3>
          <p className="kb-work-note">{__kbUi("KB raqamingiz doimiy qoladi. Nik qo‘shsangiz, odamlar sizni @nik orqali ham topadi.")}</p>
          {discoveryError && <div className="kb-work-error" role="alert">{__kbUi(discoveryError)}</div>}
          {discovery ? <form onSubmit={saveDiscovery}>
            <label htmlFor="kb-public-nickname">{__kbUi("Kabutar niki ")}<span className="kb-security-optional">{__kbUi("ixtiyoriy")}</span><div className="kb-security-nickname-field"><span aria-hidden="true">@</span><input id="kb-public-nickname" type="text" value={nickname} onChange={(event) => setNickname(event.target.value)} autoComplete="off" autoCapitalize="none" spellCheck={false} maxLength={33} placeholder={__kbUi("azizustoz")} disabled={Boolean(busy)} aria-describedby="kb-nickname-help"/></div></label>
            <p id="kb-nickname-help" className="kb-work-note">{__kbUi("5–32 belgi: lotin harflari, raqamlar va _. Nik harf bilan boshlanadi. Profilingizdagi haqiqiy ism saqlanadi.")}</p>
            <label className="kb-security-phone-toggle" htmlFor="kb-phone-discovery"><input id="kb-phone-discovery" type="checkbox" checked={phoneDiscoverable} onChange={(event) => setPhoneDiscoverable(event.target.checked)} disabled={Boolean(busy) || !discovery.phone_verified}/><span><strong>{__kbUi("Telefon raqamim orqali topish mumkin")}</strong><small>{discovery.phone_verified ? __kbUi(`${discovery.phone_masked || "Tasdiqlangan raqam"} ni biladigan odamlar meni Kabutarda topishi mumkin.`) : __kbUi("Buning uchun telefoningizni yuqoridagi Telegram orqali tasdiqlang.")}</small></span></label>
            <button type="submit" className="kb-work-primary" disabled={Boolean(busy)}>{busy === "discovery" ? uiT("Saqlanmoqda…") : __kbUi("Qidiruv sozlamalarini saqlash")}</button>
          </form> : <button type="button" onClick={() => setRetry((value) => value + 1)}>{__kbUi("Qidiruv sozlamalarini qayta yuklash")}</button>}
        </section>
        <section aria-labelledby="kb-password-heading">
          <h3 id="kb-password-heading"><KeyRound size={17}/> {resetPassword ? __kbUi("Unutilgan parolni tiklash") : profile.has_password ? __kbUi("Parolni o‘zgartirish") : __kbUi("Kirish uchun parol qo‘yish")}</h3>
          {profile.has_password && <button type="button" className="kb-security-reset-choice" onClick={() => { setResetPassword((value) => !value); setCurrentPassword(""); setError(""); setNotice(""); }} disabled={Boolean(busy)}>{resetPassword ? __kbUi("Amaldagi parolimni bilaman") : __kbUi("Parolimni unutdim")}</button>}
          {resetPassword && <p className="kb-security-recovery-info">{__kbUi("Tiklash uchun oxirgi 10 daqiqa ichida shu hisobga ulangan Telegram yoki Google orqali qayta kirgan bo‘lishingiz kerak. Server tasdiqlasa, eski parolsiz yangisini qo‘yasiz. Faqat parol bilan kirilgan seansda bu amal bajarilmaydi.")}</p>}
          <form onSubmit={changePassword}>
            {profile.has_password && !resetPassword && <label htmlFor="kb-current-password">{__kbUi("Amaldagi parol")}<input id="kb-current-password" type="password" autoComplete="current-password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} maxLength={128} required disabled={Boolean(busy)}/></label>}
            <label htmlFor="kb-new-password"><InterfaceText text={__kbUi("Yangi parol")}/><div className="kb-security-password-field"><input id="kb-new-password" type={showPassword ? "text" : "password"} autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={10} maxLength={128} required aria-describedby="kb-password-help" disabled={Boolean(busy)}/><button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? __kbUi("Yangi parolni yashirish") : __kbUi("Yangi parolni ko‘rsatish")} aria-pressed={showPassword}>{showPassword ? <EyeOff size={18}/> : <Eye size={18}/>}</button></div></label>
            <label htmlFor="kb-confirm-password">{__kbUi("Yangi parolni takrorlang")}<input id="kb-confirm-password" type={showPassword ? "text" : "password"} autoComplete="new-password" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} minLength={10} maxLength={128} required disabled={Boolean(busy)}/></label>
            <p id="kb-password-help" className="kb-work-note">{__kbUi("Kamida 10 belgi. Boshqa saytlarda ishlatmaydigan parol tanlang. Parol saqlanganda boshqa qurilmalardagi seanslar tugaydi.")}</p>
            <button className="kb-work-primary" type="submit" disabled={Boolean(busy) || !password || !confirmation}>{busy === "password" ? uiT("Saqlanmoqda…") : resetPassword ? __kbUi("Parolni tiklash") : profile.has_password ? __kbUi("Parolni yangilash") : __kbUi("Parolni saqlash")}</button>
          </form>
          {!profile.has_password && <p className="kb-work-note">{__kbUi("Parolni ilk marta qo‘yish uchun oxirgi 10 daqiqa ichida Telegram yoki Google orqali kirgan bo‘lishingiz kerak.")}</p>}
        </section>
      </>}
      <section aria-labelledby="kb-sessions-heading"><h3 id="kb-sessions-heading">{__kbUi("Qurilmalardagi kirish")}</h3><p>{__kbUi("“Chiqish” bosilganda qayta kirish uchun tasdiqlash yoki parol kerak bo‘ladi.")}</p><div className="kb-security-logout-actions"><button type="button" onClick={() => logout(false)} disabled={Boolean(busy)}><LogOut size={16}/>{busy === "logout" ? __kbUi("Chiqilmoqda…") : __kbUi("Shu qurilmadan chiqish")}</button><button type="button" className="kb-danger" onClick={() => logout(true)} disabled={Boolean(busy)}>{busy === "logout-all" ? __kbUi("Seanslar tugatilmoqda…") : __kbUi("Barcha qurilmalardan chiqish")}</button></div></section>
    </div>
  </div>, document.body);
}

return { "default": AccountSecurity };
})();

// Included from kabutar/kabutarPolling.js; implementation preserved.
const __kbRev35_module7 = (() => {
// Serialized foreground polling: next request starts only after the prior one
// settled. React owns foreground/active gating and calls stop() on hide/logout.
function startKabutarPoll(task, {
  interval, maxDelay = 60000, setTimer = setTimeout, clearTimer = clearTimeout,
} = {}) {
  if (!(interval > 0) || maxDelay < interval) throw new Error("Polling interval noto‘g‘ri");
  const controller = new AbortController();
  let timer = null;
  let failures = 0;
  let stopped = false;
  const run = async () => {
    if (stopped) return;
    let succeeded = false;
    try { succeeded = (await task(controller.signal)) !== false; }
    catch { /* The request owner exposes the useful error to the UI. */ }
    if (stopped) return;
    failures = succeeded ? 0 : Math.min(failures + 1, 8);
    const delay = Math.min(maxDelay, interval * (2 ** failures));
    timer = setTimer(run, delay);
  };
  run();
  return () => {
    stopped = true;
    if (timer !== null) clearTimer(timer);
    controller.abort();
  };
}

// Merge server refreshes and optimistic sends without duplicate bubbles.
function mergeKabutarMessages(current, incoming) {
  const rows = new Map(current.map(message => [String(message.id), message]));
  incoming.forEach(message => rows.set(String(message.id), { ...rows.get(String(message.id)), ...message }));
  return [...rows.values()].sort((a, b) => Number(a.id) - Number(b.id));
}

return { "startKabutarPoll": startKabutarPoll, "mergeKabutarMessages": mergeKabutarMessages };
})();

// Included from workspace/AudiencePanel.jsx; implementation preserved.
const __kbRev35_module6 = (() => {
const React = __kbRev35_external0["default"];
const useEffect = __kbRev35_external0["useEffect"];
const useState = __kbRev35_external0["useState"];
const workspaceRequest = __kbRev35_module4["workspaceRequest"];

const startKabutarPoll = __kbRev35_module7["startKabutarPoll"];

function useVisibleDocument() {
  const [visible, setVisible] = useState(() => typeof document === 'undefined' || document.visibilityState !== 'hidden');
  useEffect(() => {
    const update = () => setVisible(document.visibilityState !== 'hidden');
    document.addEventListener('visibilitychange', update);
    return () => document.removeEventListener('visibilitychange', update);
  }, []);
  return visible;
}

function useAudiencePresence(apiBase, token, enabled = true) {
  const visible = useVisibleDocument();
  useEffect(() => {
    if (!enabled || !token || !visible) return undefined;
    return startKabutarPoll(async signal => {
      try {
        await workspaceRequest(apiBase, '/api/presence', token, { method: 'POST', body: {}, signal });
        return true;
      } catch { return false; /* Presence never blocks the user's work. */ }
    }, { interval: 60000, maxDelay: 300000 });
  }, [apiBase, token, enabled, visible]);
}
function AudiencePanel({ apiBase, token, active = true }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [data, setData] = useState(null), [error, setError] = useState(''), [reload, setReload] = useState(0);
  const visible = useVisibleDocument();
  useEffect(() => {
    if (!active || !visible || !token) return undefined;
    return startKabutarPoll(async signal => {
      try {
        const result = await workspaceRequest(apiBase, '/api/admin/audience?days=14', token, { signal });
        if (!signal.aborted) { setData(result); setError(''); }
        return true;
      } catch (e) {
        if (!signal.aborted) setError(e.message);
        return false;
      }
    }, { interval: 60000, maxDelay: 300000 });
  }, [apiBase, token, active, visible, reload]);
  const format = value => new Intl.NumberFormat('uz-UZ').format(Number(value || 0));
  return <section className="kb-audience"><header><div><small>{__kbUi("KABUTAR · ADMIN")}</small><h2>{__kbUi("Platforma faolligi")}</h2><p>{__kbUi("Kimlar foydalanyapti va bugun qancha kirish bo‘ldi?")}</p></div><button onClick={() => setReload(n => n + 1)}>{__kbUi("Yangilash ↻")}</button></header>
    {error && <p role="alert" className="kb-work-error">{__kbUi(error)}</p>}
    {!data && !error ? <p>{__kbUi("Statistika olinmoqda…")}</p> : data && <>
      <div className="kb-metric-grid">{[['Jami akkauntlar', data.summary.registered_users], ['Hozir faol', data.summary.online_users], ['Bugun faol odamlar', data.summary.active_today], ['Bugungi kirishlar', data.summary.logins_today]].map(([label, value]) => <div key={label}><span>{__kbUi(label)}</span><strong>{__kbUi(format(value))}</strong></div>)}</div>
      <p className="kb-work-note">{__kbUi("“Jami akkauntlar” bazadagi hisoblar soni, faollik ko‘rsatkichi emas. “Hozir faol” — oxirgi ")}{Math.round((data.online_window_seconds || 180) / 60)}{__kbUi(" daqiqada kirish yoki ochiq sahifadan signal kelgan odamlar. “Bugun faol”da bir odam kuniga bir marta sanaladi. Arxivdagi muassasa a’zosi saytga kirib ishlatsa, u ham hisoblanadi; shunchaki ro‘yxatda turgani uchun faol bo‘lmaydi. Sana: Toshkent vaqti.")}</p>
      <details><summary>{__kbUi("Kunlar bo‘yicha hisob va hozir faol foydalanuvchilar")}</summary><div className="kb-audience-tables"><table><thead><tr><th><InterfaceText text={__kbUi("Sana")}/></th><th>{__kbUi("Faol odamlar")}</th><th>{__kbUi("Kirishlar")}</th></tr></thead><tbody>{(data.daily || []).map(day => <tr key={day.date}><td>{day.date}</td><td>{__kbUi(format(day.active_users))}</td><td>{__kbUi(format(day.logins))}</td></tr>)}</tbody></table><div><h3>{__kbUi("Hozir faol")}</h3>{!(data.online || []).length ? <p>{__kbUi("Hozircha signal yo‘q.")}</p> : <ul>{data.online.map(person => <li key={person.user_id}><b>{person.full_name || uiT("Foydalanuvchi")}</b><small>{__kbUi(new Date(person.last_seen_at).toLocaleTimeString(__kbLocaleTag(), { timeZone: 'Asia/Tashkent', hour: '2-digit', minute: '2-digit' }))}</small></li>)}</ul>}</div></div></details>
      <small>{__kbUi("Hisob boshlanishi: ")}{data.measurement_started_at ? __kbUi(new Date(data.measurement_started_at).toLocaleDateString(__kbLocaleTag(), { timeZone: 'Asia/Tashkent' })) : __kbUi('yangi o‘rnatishdan boshlab')}{__kbUi(". Oldingi davr uchun sonlar taxmin qilinmaydi.")}</small>
    </>}
  </section>;
}

return { "useAudiencePresence": useAudiencePresence, "default": AudiencePanel };
})();

// Install included styles once; refresh their text on a development reload.
if (typeof document !== "undefined" && document.head) {
  {
    const id = "kabutar-rev35-style-auth-kabutar-login-css";
    let sheet = document.getElementById(id);
    if (!sheet) { sheet = document.createElement("style"); sheet.id = id; document.head.appendChild(sheet); }
    sheet.textContent = ".kb-login-page{--kb-ink:#183d42;--kb-muted:#627b7c;--kb-teal:#087b74;--kb-line:#dce7e2;--kb-paper:#fafbf6;color:var(--kb-ink);background:var(--kb-paper);min-height:100dvh;font-family:Inter,Manrope,\"Segoe UI\",sans-serif;isolation:isolate;overflow-x:clip}\n.kb-login-page *{box-sizing:border-box}\n.kb-login-page.kb-login-compact{min-height:0;background:transparent;padding:0;overflow:visible}\n.kb-login-page a{color:inherit;text-decoration:none}\n.kb-login-page button,.kb-login-page input{font:inherit}\n.kb-login-page button{cursor:pointer}\n.kb-login-page button:disabled{cursor:not-allowed;opacity:.55}\n.kb-login-page :is(a,button,input):focus-visible{outline:3px solid #26b6a6;outline-offset:4px}\n.kb-login-page :is(h1,h2,h3,p){margin:0}\n.kb-login-shell{max-width:1320px;padding:0 56px;margin:auto}\n.kb-login-header{height:108px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--kb-line);gap:24px}\n.kb-login-brand{display:flex;align-items:center;gap:12px;font-size:27px;font-weight:800;letter-spacing:-1px;line-height:1.12}\n.kb-login-brand-mark{height:47px;width:47px;display:grid;place-items:center;border-radius:15px 15px 15px 5px;background:var(--kb-teal);color:white;flex:none}\n.kb-login-brand-caption{display:block;margin-top:7px;letter-spacing:1.3px;font-size:8px;font-weight:700;color:var(--kb-muted)}\n.kb-login-header nav{display:flex;align-items:center;gap:31px;font-size:13px;font-weight:600}\n.kb-login-header nav a{display:flex;align-items:center;gap:8px;padding:9px 0}\n.kb-login-header nav .kb-login-header-enter{border:1px solid #c5d7d1;border-radius:30px;padding:11px 20px;transition:background .15s}\n.kb-login-header nav .kb-login-header-enter:hover{background:#e7f0e9}\n.kb-login-main{display:grid;grid-template-columns:minmax(0,1.12fr) minmax(380px,.88fr);gap:68px;align-items:start;padding:68px 0 60px;position:relative}\n.kb-login-intro{padding-top:4px}\n.kb-login-eyebrow{font-size:10px;font-weight:750;letter-spacing:1.6px;display:flex;align-items:center;gap:9px;color:var(--kb-teal);margin-bottom:25px}\n.kb-login-eyebrow>span{width:7px;height:7px;border-radius:50%;background:var(--kb-teal);box-shadow:0 0 0 5px #dceee1}\n.kb-login-intro h1{font-size:clamp(44px,4.25vw,61px);font-weight:650;letter-spacing:-2.9px;line-height:1.09;max-width:620px}\n.kb-login-intro h1 em{font-style:normal;color:var(--kb-teal)}\n.kb-login-lead{font-size:15px;line-height:1.85;color:var(--kb-muted);max-width:405px;margin-top:26px!important}\n.kb-login-paths{margin-top:33px;display:flex;flex-direction:column;max-width:435px}\n.kb-login-paths article{display:flex;align-items:center;gap:15px;padding:19px 0;border-bottom:1px solid var(--kb-line)}\n.kb-login-paths article:first-child{border-top:1px solid var(--kb-line)}\n.kb-login-path-icon{display:grid;place-items:center;width:43px;height:43px;flex:none;color:var(--kb-teal);background:#e4efe5;border-radius:13px}\n.kb-login-path-education{background:#eff0d8;color:#73723d}\n.kb-login-paths article>svg{margin-left:auto;color:#89a49c;flex:none}\n.kb-login-paths h2{font-size:15px;font-weight:750;line-height:1.4}\n.kb-login-paths p{font-size:12px;line-height:1.55;margin-top:4px;color:var(--kb-muted)}\n.kb-login-intro-note{display:flex;align-items:flex-start;gap:8px;font-size:11px;line-height:1.7;color:var(--kb-muted);margin-top:23px!important}\n.kb-login-intro-note svg{flex:none;margin-top:2px;color:#879b70}\n.kb-login-access{position:relative;padding-top:3px;scroll-margin-top:24px}\n.kb-login-access:before{content:\"\";position:absolute;width:250px;height:250px;background:#e5edda;border-radius:50%;right:-60px;top:14px;z-index:-1}\n.kb-login-access:after{content:\"\";position:absolute;width:170px;height:160px;left:-20px;bottom:70px;border-radius:45% 55% 58% 42%;background:#dfebe6;transform:rotate(-18deg);z-index:-1}\n.kb-login-card{background:white;border:1px solid #e3e9e2;border-radius:26px;padding:32px;box-shadow:0 18px 55px #274b3821;position:relative}\n.kb-login-card-top{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:24px}\n.kb-login-card-symbol{height:48px;width:48px;border-radius:15px;background:#e9f3ee;color:var(--kb-teal);display:grid;place-items:center}\n.kb-login-card-top>span:last-child{font-size:8px;letter-spacing:1.3px;font-weight:750;color:#708781}\n.kb-login-card h2{font-size:33px;font-weight:700;letter-spacing:-1.2px;line-height:1.3}\n.kb-login-card-description{font-size:12px;line-height:1.9;color:var(--kb-muted);margin-top:9px!important}\n.kb-login-methods{display:flex;gap:5px;background:#f0f4ef;border:1px solid #e8ede6;padding:5px;border-radius:12px;margin-top:24px;margin-bottom:18px}\n.kb-login-methods button{display:flex;gap:8px;align-items:center;justify-content:center;width:50%;padding:10px 6px;border:0;border-radius:8px;color:#68817b;background:none;font-size:12px;font-weight:650;transition:background .15s,color .15s}\n.kb-login-methods button.is-selected{background:white;color:var(--kb-ink);box-shadow:0 2px 6px #142b3212}\n.kb-login-method-copy{font-size:12px;line-height:1.7;color:var(--kb-muted);margin-bottom:18px!important}\n.kb-login-primary{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;min-height:50px;padding:14px 17px;background:var(--kb-teal)!important;color:#fff!important;border:1px solid transparent;border-radius:12px;font-size:13px;font-weight:700;line-height:1.35;box-shadow:0 5px 12px #087b7418;transition:background .18s,transform .18s}\n.kb-login-primary:not(:disabled):hover{background:#09665f!important;transform:translateY(-1px)}\n.kb-login-primary>svg:last-child:not(:first-child){margin-left:auto}\n.kb-login-under-button{display:flex;align-items:center;justify-content:center;gap:6px;font-size:10px;line-height:1.55;color:var(--kb-muted);text-align:center;margin-top:11px!important}\n.kb-login-under-button svg{flex:none;color:var(--kb-teal)}\n.kb-login-divider{display:flex;align-items:center;gap:13px;font-size:10px;color:#8b9a97;margin:22px 0}\n.kb-login-divider span{height:1px;background:#e6ebe6;flex:1}\n.kb-login-google{display:flex;align-items:center;gap:12px;background:white;border:1px solid #dce5e0;border-radius:12px;padding:13px 17px;min-height:48px;width:100%;font-size:12px;font-weight:650;color:var(--kb-ink);transition:background .15s}\n.kb-login-google:hover:not(:disabled){background:#f5f8f4}\n.kb-login-google span{flex:1;text-align:center}\n.kb-login-google>svg{flex:none}\n.kb-login-account-note{font-size:10px;color:#7f918b;line-height:1.7;text-align:center;margin-top:16px!important}\n.kb-login-card-foot{display:flex;align-items:center;justify-content:center;gap:7px;font-size:10px;color:var(--kb-muted);line-height:1.5;margin:21px 0 0}\n.kb-login-card-foot svg{flex:none;color:var(--kb-teal)}\n.kb-login-error,.kb-login-service-error{padding:12px;border:1px solid #efc5bc;border-radius:10px;background:#fff5ef;color:#a34831;font-size:12px;line-height:1.6;margin:0 0 15px;overflow-wrap:anywhere}\n.kb-login-error{display:flex;align-items:flex-start;gap:7px}\n.kb-login-error button{display:grid;place-items:center;flex:none;background:none;border:0;color:inherit;margin-left:auto;padding:3px}\n.kb-login-service-error button{background:none;border:0;padding:8px 0 0;font-size:12px;color:inherit;text-decoration:underline;font-weight:650}\n.kb-login-pending-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;font-size:11px;font-weight:650;color:var(--kb-teal);margin-bottom:16px}\n.kb-login-pending-heading>span{display:flex;align-items:center;gap:7px}\n.kb-login-pending-heading time{font-variant-numeric:tabular-nums;flex:none;letter-spacing:.4px;background:#e9f3ee;padding:3px 6px;border-radius:5px}\n.kb-login-telegram-pending ol{margin:0 0 16px;padding:0 0 0 18px;font-size:12px;line-height:1.75;color:var(--kb-muted)}\n.kb-login-telegram-pending li{margin-bottom:7px;padding-left:3px}\n.kb-login-telegram-pending li::marker{color:var(--kb-teal);font-weight:750}\n.kb-login-verification{background:#f4f7ef;border:1px dashed #c5d6c6;border-radius:11px;margin-bottom:15px;padding:12px;text-align:center}\n.kb-login-verification span{display:block;font-size:10px;color:var(--kb-muted);line-height:1.5}\n.kb-login-verification strong{display:block;letter-spacing:6px;padding-left:6px;font-size:26px;font-weight:750;line-height:1.5;margin-top:5px;font-variant-numeric:tabular-nums}\n.kb-login-pending-note,.kb-login-recovery-note{font-size:10px;line-height:1.7;text-align:center;color:var(--kb-muted);margin-top:10px!important}\n.kb-login-poll-notice{font-size:11px;line-height:1.6;color:#986023;margin-top:12px!important}\n.kb-login-text-button{background:none;border:0;color:var(--kb-teal);display:block;font-size:11px;line-height:1.6;text-align:center;margin:14px auto 0;padding:4px 0;text-decoration:underline;text-underline-offset:3px}\n.kb-login-password-form label{font-size:11px;font-weight:650;display:block;margin:15px 0 7px}\n.kb-login-password-form input{width:100%;min-height:46px;padding:12px 13px;font-size:13px;border:1px solid #d6e1da;border-radius:9px;outline:none;background:#fdfefb;color:var(--kb-ink)}\n.kb-login-password-form input::placeholder{color:#95a49e;font-size:12px}\n.kb-login-password-form input:focus{border-color:var(--kb-teal);box-shadow:0 0 0 3px #087b7411}\n.kb-login-password-input{position:relative;margin-bottom:20px}\n.kb-login-password-input input{padding-right:44px}\n.kb-login-password-input button{position:absolute;right:0;top:0;bottom:0;display:grid;place-items:center;width:44px;color:var(--kb-muted);background:none;border:0}\n.kb-login-success{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:55px 10px;color:var(--kb-teal);gap:12px}\n.kb-login-success h3{font-size:19px}.kb-login-success p{font-size:13px;color:var(--kb-muted)}\n.kb-login-footer{padding:25px 0 29px;border-top:1px solid var(--kb-line);display:flex;justify-content:space-between;gap:20px;font-size:11px;color:#7c9189;line-height:1.7}\n.kb-login-footer>span:last-child{display:flex;align-items:center;gap:7px}\n.kb-login-footer-dot{padding:0 8px}\n.kb-login-spin{animation:kb-login-turn 1s linear infinite;flex:none}\n@keyframes kb-login-turn{to{transform:rotate(360deg)}}\n@media(min-width:1450px){.kb-login-main{padding-top:90px;padding-bottom:85px}}\n@media(max-width:1080px){.kb-login-shell{padding:0 34px}.kb-login-main{gap:35px;grid-template-columns:minmax(0,1fr) minmax(355px,1fr);padding-top:48px}.kb-login-intro h1{font-size:49px}.kb-login-card{padding:26px}.kb-login-eyebrow{font-size:9px;letter-spacing:1px}.kb-login-lead{font-size:14px}}\n@media(max-width:790px){.kb-login-shell{padding:0 22px;max-width:620px}.kb-login-header{height:87px}.kb-login-brand{font-size:24px}.kb-login-brand-mark{height:43px;width:43px}.kb-login-brand-caption{font-size:7px;letter-spacing:.9px}.kb-login-header nav>a:first-child{display:none}.kb-login-header nav{gap:0}.kb-login-header nav .kb-login-header-enter{font-size:12px;padding:9px 13px}.kb-login-main{display:flex;flex-direction:column;padding:35px 0 38px;gap:29px}.kb-login-intro{width:100%;padding-top:0}.kb-login-eyebrow{margin-bottom:20px;font-size:8px;letter-spacing:1.2px}.kb-login-intro h1{font-size:43px;letter-spacing:-1.8px;line-height:1.12}.kb-login-intro h1 br:nth-of-type(1),.kb-login-intro h1 em br{display:none}.kb-login-intro h1 em{display:block;margin-top:4px}.kb-login-lead{font-size:13px;line-height:1.8;margin-top:16px!important;max-width:410px}.kb-login-paths{display:none}.kb-login-intro-note{display:none}.kb-login-access{width:100%;padding-top:0}.kb-login-card{padding:27px;border-radius:22px}.kb-login-access:before{width:155px;height:155px;right:-25px;top:-26px}.kb-login-access:after{left:-20px;bottom:30px;width:110px;height:110px}.kb-login-card-top{margin-bottom:19px}.kb-login-card h2{font-size:30px}.kb-login-card-foot{font-size:9px;margin-top:17px}.kb-login-footer{font-size:10px;flex-wrap:wrap;gap:7px;padding:20px 0}.kb-login-footer>span:last-child{display:none}.kb-login-password-form input{font-size:16px}.kb-login-password-form input::placeholder{font-size:13px}}\n@media(max-width:375px){.kb-login-shell{padding:0 16px}.kb-login-card{padding:22px}.kb-login-brand-caption{display:none}.kb-login-intro h1{font-size:37px}.kb-login-card-top>span:last-child{font-size:7px;letter-spacing:1px}.kb-login-primary{font-size:12px}.kb-login-eyebrow{font-size:7px;letter-spacing:.7px}}\n@media(prefers-reduced-motion:reduce){.kb-login-page *{animation:none!important;transition:none!important;scroll-behavior:auto!important}}\n\n.kb-registration-page{display:grid;place-items:center;padding:42px 20px}.kb-registration-shell{width:min(470px,100%)}.kb-registration-shell>.kb-login-brand{justify-content:center;margin-bottom:30px}.kb-registration-card h1{font-size:29px;letter-spacing:-1px;line-height:1.25;margin:15px 0!important;font-weight:750}.kb-registration-verified{display:flex;align-items:center;gap:6px;color:var(--kb-teal);font-size:11px;font-weight:650}.kb-registration-email{overflow-wrap:anywhere;background:#f0f6ef;border-radius:9px;color:#496c60;padding:10px 13px;font-size:12px;margin:16px 0}.kb-registration-note{display:flex;align-items:center;gap:6px;font-size:10px;color:var(--kb-muted);line-height:1.6;margin:10px 0 22px!important}.kb-registration-existing{margin-top:25px;padding-top:21px;border-top:1px solid var(--kb-line)}.kb-registration-existing strong{font-size:11px;color:var(--kb-ink)}.kb-registration-existing p{font-size:11px;line-height:1.75;margin-top:8px;color:var(--kb-muted)}.kb-registration-existing .kb-login-text-button{display:flex;align-items:center;justify-content:center;gap:6px;font-size:11px;margin-top:15px}@media(max-width:480px){.kb-registration-page{padding:26px 16px}.kb-registration-card h1{font-size:27px}.kb-registration-card{padding:24px}}\n.kb-registration-invite{padding:11px 13px;background:#f7f9f3;border:1px solid #e2e9dc;border-radius:10px;margin:17px 0}.kb-registration-invite summary{font-size:11px;font-weight:650;color:var(--kb-teal);cursor:pointer;line-height:1.6}.kb-registration-invite p{font-size:10px;line-height:1.7;color:var(--kb-muted);margin-top:9px}.kb-registration-invite input{text-transform:uppercase;letter-spacing:.8px}\n";
  } // auth/kabutar-login.css
  {
    const id = "kabutar-rev35-style-workspace-workspace-css";
    let sheet = document.getElementById(id);
    if (!sheet) { sheet = document.createElement("style"); sheet.id = id; document.head.appendChild(sheet); }
    sheet.textContent = ".kb-audience,.kb-education-setup,.kb-security-panel{--kb-ink:#153843;--kb-teal:#087f78;color:var(--kb-ink);font-family:inherit}.kb-audience{padding:24px;border:1px solid #d5e6e2;border-radius:24px;background:#fff;margin:0 0 24px}.kb-audience header{display:flex;justify-content:space-between;gap:16px;align-items:center}.kb-audience h2{font-size:25px;margin:4px 0}.kb-audience p,.kb-education-setup>p{color:#607a80;line-height:1.65}.kb-audience header small,.kb-education-setup>small{color:#087f78;font-size:11px;font-weight:800;letter-spacing:.16em}.kb-audience button,.kb-work-back{padding:10px 14px;border-radius:12px;background:#eaf5f2;border:1px solid #cfe4de;color:#08786f;font-weight:700}.kb-metric-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:20px 0}.kb-metric-grid>div{display:flex;flex-direction:column;gap:12px;padding:18px;border:1px solid #e1ece8;border-radius:17px;background:#f5faf8}.kb-metric-grid span{font-size:12px;color:#627c7f}.kb-metric-grid strong{font-size:32px;letter-spacing:-.04em}.kb-work-note{font-size:12px!important;line-height:1.6!important;color:#667e84!important}.kb-work-error{padding:12px;background:#fff1ee;border:1px solid #edb9ad;color:#9b382b!important;border-radius:12px;font-size:13px}.kb-audience details{margin:18px 0}.kb-audience summary{cursor:pointer;font-weight:700}.kb-audience-tables{display:grid;grid-template-columns:1fr 1fr;gap:25px;margin-top:16px;overflow:auto}.kb-audience table{border-collapse:collapse;width:100%;font-size:12px}.kb-audience th,.kb-audience td{text-align:left;border-bottom:1px solid #e2ece8;padding:10px}.kb-audience-tables ul{list-style:none;padding:0}.kb-audience-tables li{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #e2ece8;font-size:12px}.kb-audience>small{font-size:11px;color:#6e8689}.kb-education-setup{max-width:920px;margin:0 auto;padding:30px 22px 80px}.kb-education-setup>.kb-work-back{display:block;margin:0 0 32px}.kb-education-setup h1{font-size:clamp(28px,5vw,45px);letter-spacing:-.04em;margin:10px 0}.kb-education-roles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:30px 0}.kb-education-roles button{padding:20px 14px;text-align:left;display:flex;flex-direction:column;gap:9px;border:1px solid #d9e7e4;border-radius:20px;background:#fff;color:#153843;cursor:pointer}.kb-education-roles button.selected{background:#eaf8f1;border:2px solid #087f78;padding:19px 13px;box-shadow:0 10px 30px #0a7e7510}.kb-education-roles button>span{font-size:24px}.kb-education-roles small{font-size:11px;line-height:1.6;color:#617e80}.kb-education-fields{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin:20px 0}.kb-education-fields label,.kb-security-panel label{display:flex;flex-direction:column;gap:8px;font-size:12px;font-weight:700}.kb-education-fields select,.kb-education-fields input,.kb-security-panel input{padding:12px;border:1px solid #ccdeda;border-radius:11px;background:white;font:inherit}.kb-work-primary{background:#087f78!important;color:white!important;border:0;border-radius:12px;padding:14px 20px;font-weight:800;cursor:pointer}.kb-education-setup .kb-work-primary{margin-top:20px}.kb-work-primary:disabled{opacity:.5}.kb-security-overlay{position:fixed;inset:0;background:#062e3d88;z-index:1500;padding:20px;display:grid;place-items:center}.kb-security-panel{width:min(540px,100%);max-height:90dvh;overflow:auto;border-radius:24px;background:#fff;padding:24px;box-shadow:0 30px 80px #072e3f40}.kb-security-panel header{display:flex;justify-content:space-between;align-items:center}.kb-security-panel h2{font-size:24px}.kb-security-panel button{border:1px solid #d4e4df;padding:10px 13px;border-radius:12px;background:#edf5f2;color:#1d5156;font-weight:700;cursor:pointer}.kb-security-panel button:disabled{opacity:.5;cursor:wait}.kb-security-panel form{display:grid;gap:14px;margin:20px 0}.kb-security-panel section{margin-top:20px;border-top:1px solid #dfebe6;padding-top:18px}.kb-security-panel section p{font-size:12px;color:#617a7e}.kb-security-panel .kb-danger{background:#fff0eb;color:#9b382b}.kb-security-panel .kb-security-rows{display:grid;gap:10px}.kb-security-rows>div{display:flex;justify-content:space-between;font-size:12px}.kb-account-top-button{flex:0 0 44px!important;max-width:44px!important;min-width:44px!important}.kb-app-error{padding:40px 24px;text-align:center;background:#f1f8f5;min-height:70vh;color:#153843}.kb-app-error button{padding:13px 20px;border:0;border-radius:12px;background:#087f78;color:white;margin:8px}.kb-workspace-brand{letter-spacing:-.02em}@media(max-width:650px){.kb-audience{padding:17px}.kb-metric-grid{grid-template-columns:1fr 1fr}.kb-metric-grid strong{font-size:27px}.kb-audience-tables{grid-template-columns:1fr}.kb-education-roles{grid-template-columns:1fr 1fr}.kb-security-overlay{padding:0;align-items:end}.kb-security-panel{border-radius:24px 24px 0 0;padding:20px 20px max(20px,env(safe-area-inset-bottom))}.kb-audience header{align-items:flex-start}.kb-audience h2{font-size:21px}}\n\n.kb-app-notice{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);width:min(640px,94vw);display:flex;align-items:center;gap:16px;background:#123843;color:#fff;border-radius:16px;padding:16px 20px;z-index:2147483600;box-shadow:0 10px 50px #09202d33}.kb-app-notice span{flex:1}.kb-app-notice button{font-size:24px;background:none;border:0;color:inherit}\n\n/* Kabutar account security: self-contained dialog content. */\n.kb-security-panel:focus{outline:none}.kb-security-panel :is(button,input,a):focus-visible{outline:3px solid #25a89d;outline-offset:3px}.kb-security-panel header{align-items:flex-start;gap:12px;margin-bottom:12px}.kb-security-panel h2{margin:7px 0 0;letter-spacing:-.6px;line-height:1.25}.kb-security-panel h3{display:flex;align-items:center;gap:8px;margin:0 0 13px;font-size:14px}.kb-security-eyebrow{display:flex;align-items:center;gap:6px;font-size:9px;letter-spacing:1.2px;font-weight:800;color:#087f78}.kb-security-panel .kb-security-close{display:grid;place-items:center;padding:9px;flex:none;border:0;background:#eef5f1}.kb-security-panel>.kb-work-error{margin-top:14px}.kb-security-notice{display:flex;align-items:flex-start;gap:8px;padding:12px;border:1px solid #bddfc9;background:#f0faf2;color:#2b6848;border-radius:11px;line-height:1.6;font-size:12px;margin-top:14px}.kb-security-notice svg{flex:none;margin-top:2px}.kb-security-loading{display:flex;align-items:center;gap:9px;margin:23px 0;color:#607a80;font-size:13px}.kb-security-identities{display:grid;gap:10px}.kb-security-identities>div{display:flex;align-items:center;gap:10px;padding:12px 0;border-bottom:1px solid #e9efeb}.kb-security-provider-icon{display:grid;place-items:center;flex:none;width:36px;height:36px;background:#edf6f0;border-radius:11px;color:#087f78}.kb-security-google-mark{font-size:20px;font-weight:800;color:#4285f4}.kb-security-identities>div>div{flex:1;min-width:0}.kb-security-identities strong{display:block;font-size:13px;font-weight:750}.kb-security-identities small{display:block;font-size:11px;line-height:1.6;color:#6e8485;margin-top:3px;overflow-wrap:anywhere}.kb-security-identities button{display:flex;align-items:center;gap:3px;padding:8px 10px;flex:none;font-size:11px}.kb-security-linked{display:flex;align-items:center;gap:4px;color:#3d765b;font-size:10px;flex:none}.kb-security-password-field{position:relative}.kb-security-password-field input{width:100%;padding-right:46px}.kb-security-panel .kb-security-password-field button{position:absolute;right:0;top:0;bottom:0;display:grid;place-items:center;background:none;border:0;padding:10px 12px;color:#7b9090}.kb-security-panel input{min-height:44px;font-size:14px}.kb-security-panel form p{margin:0}.kb-security-panel section>p{line-height:1.7;margin:11px 0}.kb-security-panel .kb-login-compact{margin-top:15px;padding-top:15px}.kb-security-panel .kb-login-compact .kb-login-primary{font-size:12px}.kb-security-panel .kb-login-compact .kb-login-text-button{background:none;border:0;color:#087f78;padding:4px}.kb-security-logout-actions{display:flex;flex-wrap:wrap;gap:9px;margin-top:13px}.kb-security-logout-actions button{display:flex;align-items:center;justify-content:center;gap:7px;font-size:11px;flex:1;white-space:normal;line-height:1.6}.kb-security-panel .kb-work-primary{min-height:46px}.kb-security-panel button:disabled{cursor:not-allowed}@media(max-width:650px){.kb-security-panel input{font-size:16px}.kb-security-panel{max-height:92dvh}.kb-security-logout-actions{flex-direction:column}.kb-security-linked{font-size:9px}}\n.kb-security-optional{font-size:10px;font-weight:400;color:#82958e}.kb-security-nickname-field{position:relative}.kb-security-nickname-field>span{position:absolute;left:13px;top:50%;transform:translateY(-50%);color:#81958b;font-size:16px}.kb-security-nickname-field input{width:100%;padding-left:32px}.kb-security-panel label.kb-security-phone-toggle{display:flex;flex-direction:row;align-items:flex-start;gap:11px;padding:13px;border:1px solid #dce8e1;border-radius:12px;background:#f6faf5;cursor:pointer}.kb-security-phone-toggle input{width:18px;height:18px;min-height:18px;padding:0;margin:1px 0 0;flex:none;accent-color:#087f78}.kb-security-phone-toggle strong{display:block;font-size:12px;line-height:1.6}.kb-security-phone-toggle small{display:block;font-size:10px;line-height:1.7;color:#748880;font-weight:400;margin-top:4px}\n.kb-security-panel button.kb-security-reset-choice{border:0;background:none;padding:2px 0;color:#087f78;text-decoration:underline;text-underline-offset:3px;font-size:11px;font-weight:600}.kb-security-panel p.kb-security-recovery-info{padding:12px;border:1px solid #dccfb0;background:#fffbef;color:#816634;border-radius:10px;font-size:11px;line-height:1.7}\n";
  } // workspace/workspace.css
}

// Existing application implementation.
// SamTM V19.2 — 1–14 to‘liq: o‘qituvchi-asosli yuklama va aqlli almashtirish.
// SAMTM V19.0 — clean-scale frontend; lazy workspaces preserved.
import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import katex from "katex";
const KabutarLogin = __kbRev35_module0["default"];
const KabutarRegistration = __kbRev35_module2["default"];
const EducationSetup = __kbRev35_module3["default"];
const AccountSecurity = __kbRev35_module5["default"];
const AudiencePanel = __kbRev35_module6["default"];
const useAudiencePresence = __kbRev35_module6["useAudiencePresence"];
const workspaceRequest = __kbRev35_module4["workspaceRequest"];

import { HUDUDLAR, VILOYATLAR } from "./hududlar.js";
import {
  CLUB_STUDENT_LIMIT,
  SECOND_CLUB_PRICE_UZS,
  apiErrorMessage,
  formatTopicTitle,
  freeClubAvailable,
  groupTypeLabel,
  normalizedClubCapacity,
  topicName,
} from "./teacherRules.js";
import {
  ORGANIZATION_ACTIVATION_PRICE_UZS,
  ORGANIZATION_TRIAL_DAYS,
  ORGANIZATION_TYPES,
  buildAdminWalletCreditPayload,
  buildActivationPayload,
  buildTrialStartPayload,
  formatTrialEnd,
  formatUzs,
  makeOrganizationIdempotencyKey,
  organizationCanActivate,
  organizationIsReadOnly,
  organizationToLegacyMembership,
  organizationTrialErrorMessage,
  organizationTrialState,
  organizationTypeMeta,
} from "./organizationTrialRules.js";
import { initializeSamtmPwa, registerPhoneBackHandler } from "./pwa/samtmPwa.js";
import { BATTLE_CODE_KEY, normalizeCode } from "./battle/battleRules.js";
import { SHASHKA_CODE_KEY } from "./games/shashkaRules.js";
import { SHAXMAT_CODE_KEY } from "./games/chessRules.js";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import {
  ChevronRight, ChevronDown, ChevronLeft, TrendingUp, BarChart3, Bell, User,
  Loader2, WifiOff, KeyRound, UserPlus, PencilLine, Users, FileSpreadsheet, Heart, BookOpen,
  Flame, Star, CalendarCheck, Trophy, Swords, Gamepad2, Building2, Settings, Video, X, RotateCcw, Send, Mic, Trash2,
  Wallet, Folder, Calendar, Brain, GraduationCap, ClipboardList, Bot, AlertTriangle, Search, Baby,
  UserRoundPlus, MessageCircle, Eye,
} from "lucide-react";

// Deploydan keyin brauzer eski chunk nomini eslab qolsa oq ekran bermaydi:
// bir marta yangilanadi, qayta xato bo'lsa haqiqiy xato ko'rsatiladi.
const _samtmLazyRetry = (loader) => React.lazy(() => loader().then((mod) => {
  try { window.sessionStorage.removeItem("samtm_chunk_reload"); } catch { /* jim */ }
  return mod;
}).catch((err) => {
  let already = false;
  try {
    already = window.sessionStorage.getItem("samtm_chunk_reload") === "1";
    if (!already) window.sessionStorage.setItem("samtm_chunk_reload", "1");
  } catch { /* jim */ }
  if (!already) { window.location.reload(); return new Promise(() => {}); }
  throw err;
}));

const lazyAnalytics = (exportName) =>
  _samtmLazyRetry(() =>
    import("./Analytics.jsx").then((module) => ({
      default: module[exportName],
    })),
  );
const AdminStatisticsTab = lazyAnalytics("AdminStatisticsTab");
const StudentAnalyticsDashboard = lazyAnalytics("StudentAnalyticsDashboard");
const StudentLearningPathDashboard = lazyAnalytics("StudentLearningPathDashboard");
const TeacherAnalyticsPanel = lazyAnalytics("TeacherAnalyticsPanel");
const LazyTestTab = _samtmLazyRetry(() => import("./TestTab.jsx"));
const LazyOquvchiKorinishi = _samtmLazyRetry(() => import("./admin/OquvchiKorinishi.jsx"));
const LazyBellashuv = _samtmLazyRetry(() => import("./battle/Bellashuv.jsx"));
const LazyShashka = _samtmLazyRetry(() => import("./games/Shashka.jsx"));
const LazyShaxmat = _samtmLazyRetry(() => import("./games/Shaxmat.jsx"));
const LazyOyinlarMarkazi = _samtmLazyRetry(() => import("./games/OyinlarMarkazi.jsx"));
const LazyChempionat = _samtmLazyRetry(() => import("./chempionat/Chempionat.jsx"));
const StudentScheduleWorkspace = _samtmLazyRetry(() => import("./student/StudentScheduleWorkspace.jsx"));
// Talaba (1–11 sinfdan tashqari): qo'shilish oqimi, profil kartasi va o'z paralar jadvali
const TalabaQoshilish = _samtmLazyRetry(() => import("./student/TalabaQoshilish.jsx"));
const TalabaProfilKartasi = _samtmLazyRetry(() => import("./student/TalabaQoshilish.jsx").then((m) => ({ default: m.TalabaProfilKartasi })));
const TalabaHaftalikJadval = _samtmLazyRetry(() => import("./student/TalabaHaftalikJadval.jsx"));
// users.class "2 kurs" / "1 kurs magistr" — talaba; maktab jadvali va 1–11 tugmalari ularga tegmaydi
const sinfTalabaMi = (qiymat) => /^\s*[1-6]\s*-?\s*kurs(?:\s+magistr)?\s*$/i.test(String(qiymat || ""));
const MilitaryRoutine = _samtmLazyRetry(() => import("./school/MilitaryRoutine.jsx"));
// REV91: ota-ona — farzandning bugungi darslari jonli.
const FarzandFaollik = _samtmLazyRetry(() => import("./parent/FarzandFaollik.jsx"));
// REV103: bog'cha bolasining kunlik vaqti (dars + erkin o'yin) — vaqt tugasa ekran yopiladi, «Ertaga uchrashamiz».
const KidTimeGuard = _samtmLazyRetry(() => import("./kid/KidTimeGuard.jsx"));
const lazyAdminTestTool = (exportName) =>
  _samtmLazyRetry(() =>
    import("./AdminTestTools.jsx").then((module) => ({ default: module[exportName] })),
  );
const LazyTopikMavzularTab = lazyAdminTestTool("TopikMavzularTab");
const LazyModeratsiyaTab = lazyAdminTestTool("ModeratsiyaTab");
const LazyKitobMiyaBolimi = lazyAdminTestTool("KitobMiyaBolimi");
const LazyTestShablonBolimi = lazyAdminTestTool("TestShablonBolimi");
const LazyTopikShablonBolimi = lazyAdminTestTool("TopikShablonBolimi");
const LazyTushuntirishBolimi = lazyAdminTestTool("TushuntirishBolimi");

function OgirBolimYuklanmoqda() {
  useKbInterfaceLocale();
  return (
    <div className="px-5 py-12 text-center" role="status" aria-live="polite">
      <Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} />
      <p className="text-xs mt-2" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bo'lim yuklanmoqda...")}</p>
    </div>
  );
}

function lazyPanel(Component, props) {
  return (
    <React.Suspense fallback={<OgirBolimYuklanmoqda />}>
      <Component {...props} />
    </React.Suspense>
  );
}

function TestTab(props) { return lazyPanel(LazyTestTab, props); }
function Bellashuv(props) { return lazyPanel(LazyBellashuv, props); }
function Shashka(props) { return lazyPanel(LazyShashka, props); }
function Shaxmat(props) { return lazyPanel(LazyShaxmat, props); }
function OyinlarMarkazi(props) { return lazyPanel(LazyOyinlarMarkazi, props); }
function Chempionat(props) { return lazyPanel(LazyChempionat, props); }
const OYIN_TABLARI = new Set(["oyinlar", "bellashuv", "shashka", "shaxmat", "til_xonalari", "til_mashqi", "til_maktab", "chempionat"]);
const LazyTilTanlov = _samtmLazyRetry(() => import("./til/TilTanlov.jsx"));   // REV128: til o'yin xonalari va kattalar mashqi
function DtsNomTahrirlash({ token }) {
  useKbInterfaceLocale();
  const { fetch: scopedFetch, scope } = useCurriculum();
  const { t: uiT } = useInterface();
  const [ochiq, setOchiq] = useState(false);
  const [sinf, setSinf] = useState(scope.grade || (scope.institution_type==='maktab'?'1':''));
  const [fanlar, setFanlar] = useState([]);
  const [fan, setFan] = useState("");
  const [mavzular, setMavzular] = useState([]);
  const [xato, setXato] = useState("");
  const [yuklanmoqda, setYuklanmoqda] = useState(false);

  const jsonOl = async (url, options) => {
    const res = await scopedFetch(url, options);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Server xatosi");
    return data;
  };
  const fanlarniYukla = async (joriySinf = sinf) => {
    setYuklanmoqda(true); setXato(""); setFan(""); setMavzular([]);
    try {
      const d = await jsonOl(`${API_BASE}/api/admin/topik_fanlar?sinf=${encodeURIComponent(joriySinf)}&token=${encodeURIComponent(token)}`);
      setFanlar(d.fanlar || []);
    } catch (e) { setXato(e.message); }
    finally { setYuklanmoqda(false); }
  };
  const mavzularniYukla = async (joriyFan) => {
    setYuklanmoqda(true); setXato(""); setFan(joriyFan);
    try {
      const d = await jsonOl(`${API_BASE}/api/admin/topik_royxat?sinf=${encodeURIComponent(sinf)}&fan=${encodeURIComponent(joriyFan)}&token=${encodeURIComponent(token)}`);
      setMavzular(d.mavzular || []);
    } catch (e) { setXato(e.message); }
    finally { setYuklanmoqda(false); }
  };
  const fanTahrirla = async (eskiFan) => {
    const yangiFan = window.prompt(__kbUi("Fan nomini tahrirlang. Mavzu kodlari va testlar o‘zgarmaydi:"), eskiFan)?.trim();
    if (!yangiFan || yangiFan === eskiFan) return;
    setYuklanmoqda(true); setXato("");
    try {
      const q = new URLSearchParams({ token, sinf, eski_fan: eskiFan, yangi_fan: yangiFan });
      await jsonOl(`${API_BASE}/api/admin/topik_fan_nomini_tahrirla?${q}`, { method: "PUT" });
      await fanlarniYukla(sinf);
    } catch (e) { setXato(e.message); setYuklanmoqda(false); }
  };
  const mavzuTahrirla = async (mavzu) => {
    const yangiMavzu = window.prompt(__kbUi("Mavzu nomini tahrirlang. Testlar o‘chmaydi:"), mavzu.nomi || "")?.trim();
    if (!yangiMavzu || yangiMavzu === mavzu.nomi) return;
    setYuklanmoqda(true); setXato("");
    try {
      const q = new URLSearchParams({ token, topic_codes: (mavzu.topic_codes || [mavzu.topic_code]).join(","), yangi_mavzu: yangiMavzu });
      await jsonOl(`${API_BASE}/api/admin/topik_mavzu_nomini_tahrirla?${q}`, { method: "PUT" });
      await mavzularniYukla(fan);
    } catch (e) { setXato(e.message); setYuklanmoqda(false); }
  };

  return <div className="mb-4 rounded-2xl border bg-white p-4" style={{ borderColor: "#d5e1e7" }}>
    <button type="button" onClick={() => { const n = !ochiq; setOchiq(n); if (n && sinf && !fanlar.length) fanlarniYukla(); }}
      className="w-full flex items-center justify-between font-semibold" style={{ color: "#12324b" }}>
      <span>{__kbUi("✎ DTS fan va mavzu nomlarini tahrirlash")}</span><span>{ochiq ? __kbUi("▲") : __kbUi("▼")}</span>
    </button>
    {ochiq && <div className="mt-4">
      {scope.institution_type==='maktab'?<div className="flex flex-wrap gap-2 mb-4">{Array.from({ length: 11 }, (_, i) => String(i + 1)).map((g) =>
        <button key={g} type="button" onClick={() => { setSinf(g); fanlarniYukla(g); }}
          className="px-3 py-2 rounded-xl border font-semibold" style={{ background: sinf === g ? "#155f78" : "#f4f8fa", color: sinf === g ? "white" : "#12324b" }}>{g}{__kbUi("-sinf")}</button>
      )}</div>:scope.institution_type==='universitet'?<p className="mb-4 text-sm font-semibold">{__kbUi(scope.grade)} · {__kbUi(semesterPairLabel(scope.kurs))} · {__kbUi(lessonLabel(scope.dars_turi))}</p>
       :<div className="mb-4 flex gap-2"><label className="text-sm">{__kbUi("Guruh yoki daraja")}<input className="ml-2 rounded-xl border p-2" value={sinf} onChange={e=>{setSinf(e.target.value);setFan('');setFanlar([]);setMavzular([]);}} placeholder={scope.institution_type==='bogcha'?__kbUi('5-6 yosh'):__kbUi('A1')}/></label><button type="button" className="rounded-xl border px-3" disabled={!sinf.trim()||yuklanmoqda} onClick={()=>fanlarniYukla()}>{__kbUi("Ko‘rsatish")}</button></div>}
      {xato && <div className="p-3 mb-3 rounded-xl" style={{ background: "#fff0f0", color: "#b42318" }}>{__kbUi(xato)}</div>}
      {yuklanmoqda && <div className="py-3 text-sm"><InterfaceText text={__kbUi("Yuklanmoqda...")}/></div>}
      {!fan && !yuklanmoqda && <div className="space-y-2">{fanlar.map((f) =>
        <div key={f.nom} className="flex items-center gap-2 border rounded-xl p-3">
          <button type="button" onClick={() => mavzularniYukla(f.nom)} className="flex-1 text-left font-semibold">{f.nom} <span className="font-normal text-xs">({f.mavzu_soni}{__kbUi(" yozuv)")}</span></button>
          <button type="button" aria-label={__kbUi(`${f.nom}ni tahrirlash`)} title={uiT("Tahrirlash")} onClick={() => fanTahrirla(f.nom)} className="px-3 py-2 rounded-lg border font-bold">⋮</button>
        </div>)}</div>}
      {fan && <div>
        <button type="button" onClick={() => { setFan(""); setMavzular([]); }} className="mb-3 font-semibold">{__kbUi("← Fanlarga qaytish")}</button>
        <h3 className="font-bold mb-3">{fan}</h3>
        <div className="space-y-2">{mavzular.map((m) => <div key={m.topic_code} className="flex items-center gap-2 border rounded-xl p-3">
          <div className="flex-1"><div className="font-semibold">{m.nomi}</div><div className="text-xs opacity-70">{m.topic_code} · {m.kichik_soni}{__kbUi(" kichik mavzu")}</div></div>
          <button type="button" aria-label={__kbUi(`${m.nomi}ni tahrirlash`)} title={uiT("Tahrirlash")} onClick={() => mavzuTahrirla(m)} className="px-3 py-2 rounded-lg border font-bold">⋮</button>
        </div>)}</div>
      </div>}
    </div>}
  </div>;
}
function TopikMavzularTab(props) {
  useKbInterfaceLocale();
  return <CurriculumBoundary token={props.token} title={__kbUi("Mavzular")}><DtsNomTahrirlash token={props.token} />{__kbUi(lazyPanel(LazyTopikMavzularTab, props))}</CurriculumBoundary>;
}
function ModeratsiyaTab(props) { return lazyPanel(LazyModeratsiyaTab, props); }
function KitobMiyaBolimi(props) { return lazyPanel(LazyKitobMiyaBolimi, props); }
function TestShablonBolimi(props) {
  useKbInterfaceLocale(); return <CurriculumBoundary token={props.token} title={props.mode === "import" ? __kbUi("Test importi") : __kbUi("Test tuzish")}>{__kbUi(lazyPanel(LazyTestShablonBolimi, props))}</CurriculumBoundary>; }
function TopikShablonBolimi(props) {
  useKbInterfaceLocale(); return <CurriculumBoundary token={props.token} title={__kbUi("Mavzu yaratish")}>{__kbUi(lazyPanel(LazyTopikShablonBolimi, props))}</CurriculumBoundary>; }
function TushuntirishBolimi(props) {
  useKbInterfaceLocale(); return <CurriculumBoundary token={props.token} title={__kbUi("Mavzu tushuntirishlari")}>{__kbUi(lazyPanel(LazyTushuntirishBolimi, props))}</CurriculumBoundary>; }
const AdminInstitutionSecurity = _samtmLazyRetry(() => import("./AdminInstitutionSecurity.jsx"));
const AdminSchoolWizard = _samtmLazyRetry(() => import("./AdminSchoolWizard.jsx"));
const KindergartenWorkspace = _samtmLazyRetry(
  () => import("./kindergarten/KindergartenWorkspace.jsx"),
);
const SchoolWorkspace = _samtmLazyRetry(
  () => import("./school/SchoolWorkspace.jsx"),
);
const LearningCenterWorkspace = _samtmLazyRetry(
  () => import("./center/LearningCenterWorkspace.jsx"),
);
const InstituteWorkspace = _samtmLazyRetry(
  () => import("./institute/InstituteWorkspace.jsx"),
);
const KabutarPanel = _samtmLazyRetry(() => import("./kabutar/KabutarPanel.jsx"));
const DarsXonasi = _samtmLazyRetry(() => import("./lesson/DarsXonasi.jsx"));
const MUASSASA_TURI_RANG = {
  maktab: { ikon: "🏫", nom: "Maktab", rang: "#1B4B7A", yengil: "#EAF1F7", korinish: "maktab_rahbariyat" },
  universitet: { ikon: "🎓", nom: "Institut", rang: "#5B4B8A", yengil: "#F1EEF8", korinish: "institut_workspace" },
  bogcha: { ikon: "🧸", nom: "Bog‘cha", rang: "#B0553A", yengil: "#FFF0EC", korinish: "bogcha" },
  markaz: { ikon: "📚", nom: "Ta’lim markazi", rang: "#0D7A77", yengil: "#E8F5F4", korinish: "markaz_workspace" },
};

const API_BASE =
  import.meta.env.VITE_API_BASE ||
  "https://talimplatformasi-production.up.railway.app";

// ═══════════════════════════════════════════════════════════
// DIZAYN TIZIMI — rol/jins/fanga qarab shaxsiylashtirilgan rang
// ═══════════════════════════════════════════════════════════

// O'quvchi uchun — jinsiga qarab ILIQ, ZAMONAVIY palitra (ikkalasi ham
// bir xil darajada "jiddiy"/chiroyli — biri ikkinchisidan kamroq
// ko'rinmasin degan niyatda tanlangan).
const QIZ_RANGI = "#A8527A";   // iliq to'q pushti-binafsha (mavj/berry)
const OGIL_RANGI = "#2D6E8B";  // chuqur ko'k-firuza

// Ota-ona uchun — issiq, "oilaviy" tuyg'u beruvchi neytral rang.
const OTA_ONA_RANGI = "#6E8B4A"; // iliq zaytun-yashil

// O'qituvchi uchun — o'zi o'qitadigan FANGA mos rang. Fan nomidan
// barqaror (deterministik) rang hisoblanadi — shu sabab yangi fan
// qo'shilsa ham, doim BIR XIL rangni oladi, qo'lda ro'yxat yuritish
// shart emas.
const FAN_RANGLAR_KENGAYTIRILGAN = [
  "#C89B3C", "#2D8B8B", "#8B5FBF", "#B0553A", "#4A7C9E", "#7C9E4A",
  "#A8527A", "#5C7F9E", "#9E7C4A", "#4A9E8C", "#9E4A6E", "#6E9E4A", "#2D6E8B",
];
function fanRangiOl(fanNomi) {
  if (!fanNomi) return "#1B4B7A";
  let hash = 0;
  for (let i = 0; i < fanNomi.length; i++) hash = fanNomi.charCodeAt(i) + ((hash << 5) - hash);
  return FAN_RANGLAR_KENGAYTIRILGAN[Math.abs(hash) % FAN_RANGLAR_KENGAYTIRILGAN.length];
}

// Rol + jins + (o'qituvchi bo'lsa) fanga qarab YAGONA "joriy rang"ni
// hisoblaydi — Kabinet shundan foydalanib butun ilovaga shaxsiylashtirilgan
// rang beradi (pastki menyu, Bilim boshi, Profil rasmi va h.k.).
function joriyRangniHisobla(foydalanuvchi, korinishRoli) {
  if (korinishRoli === "oquvchi") {
    if (foydalanuvchi?.jins === "qiz") return QIZ_RANGI;
    if (foydalanuvchi?.jins === "ogil") return OGIL_RANGI;
    return "#1B4B7A";
  }
  if (korinishRoli === "oqituvchi") return fanRangiOl(foydalanuvchi?.oqituvchi_fani);
  if (korinishRoli === "ota-ona") return OTA_ONA_RANGI;
  return "#1B4B7A"; // admin va standart
}

// O'qituvchi profilida tanlash uchun — BARCHA maktab fanlari (mavjud
// test-kontentdan qat'i nazar, chunki o'qituvchi o'zi qaysi fanni
// o'qitishini tanlashi kerak, hali test yaratilmagan fan bo'lsa ham).
const BARCHA_MAKTAB_FANLARI = [
  "Matematika", "Algebra", "Geometriya", "Ona tili", "Adabiyot",
  "Ingliz tili", "Rus tili", "Nemis tili", "Fransuz tili",
  "Tarix", "O'zbekiston tarixi", "Jahon tarixi", "Geografiya",
  "Biologiya", "Fizika", "Kimyo", "Informatika", "Chizmachilik",
  "Tasviriy san'at", "Musiqa", "Jismoniy tarbiya", "Astronomiya",
  "Huquq", "Iqtisodiyot asoslari", "Milliy g'oya va ma'naviyat asoslari",
  "Texnologiya", "Ona Vatan", "Atrofimizdagi olam", "O'qish savodxonligi",
];


// Haqiqiy rasm kodi ("11-04-1-01-01-03-001-1" kabi — sinf-fan-chorak-bob-
// bolim-mavzu-ketma_ket-rasm_raqami, 7-9 ta FAQAT-RAQAM bo'lak, tire bilan
// ajratilgan) bilan LaTeX ifodani ("273\div 7+8", "4{,}(4)" kabi — harflar,
// qavslar, matematik belgilar bor) ISHONCHLI ajratadi. Bu farqni bilish
// MUHIM: image_url ba'zan haqiqiy rasm o'rniga ko'rsatiladigan matematik
// ifodani saqlaydi (rasm chizib bo'lmaydigan holatlarda) — bunday holda
// uni RASM DEB SO'RAMASDAN, KaTeX bilan FORMULA sifatida chizish kerak.
function haqiqiyRasmKodimi(qiymat) {
  if (!qiymat) return false;
  const q = String(qiymat).trim();
  if (q.startsWith("/api/")) return true; // Excel'ga joylashtirilgan rasm — to'g'ridan-to'g'ri yo'l
  if (/^https?:\/\//i.test(q)) return true; // to'liq tashqi URL
  return /^\d+(-\d+){5,9}$/.test(q);
}

// Token ICHIDAGI user_id'ni o'qish uchun — imzo TEKSHIRILMAYDI (bu
// faqat "shu xabar MENIKIMI" kabi ko'RINISH qarorlari uchun, haqiqiy
// xavfsizlik har doim backend'da, har bir so'rovda tekshiriladi).
function _tokenDanUserIdOl(token) {
  try {
    const qism = token.split(".")[1];
    const toldirilgan = qism.replace(/-/g, "+").replace(/_/g, "/").padEnd(qism.length + (4 - (qism.length % 4)) % 4, "=");
    const payload = JSON.parse(atob(toldirilgan));
    return payload.user_id ?? null;
  } catch {
    return null;
  }
}

function SavolFormulasi({ ifoda }) {
  const qiymat = String(ifoda || "");
  const aralash = /\[lat\]|\$|\\\(|\\\[/.test(qiymat);
  const html = useMemo(() => {
    if (aralash) return null;
    try {
      return katex.renderToString(qiymat, { throwOnError: false, output: "html", displayMode: true });
    } catch {
      return null;
    }
  }, [aralash, qiymat]);

  return (
    <div className="w-full rounded-xl mb-4 flex items-center justify-center py-6 px-4"
      style={{ backgroundColor: "#F1EFE8", border: "1px solid #E5E1D8" }}>
      {aralash ? (
        <AralashMatn matn={qiymat} className="m-0 text-lg" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }} />
      ) : html ? (
        <span dangerouslySetInnerHTML={{ __html: html }} style={{ fontSize: "1.3rem", color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }} />
      ) : (
        <span style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{qiymat}</span>
      )}
    </div>
  );
}

// Oddiy so'z-matn ICHIDA $...$ bilan belgilangan formulalarni ham
// ko'rsatish uchun — SavolFormulasi'dan farqli, BUTUN matnni formula
// deb hisoblamaydi (aks holda oddiy so'zlar harflarga bo'linib,
// noto'g'ri chiqib qolar edi), faqat $...$ ICHIDAGI qismni formulaga
// aylantiradi, qolgani oddiy matn bo'lib qoladi.
// LaTeX qismlarni ajratish uchun UMUMIY naqsh — uch xil holatni ham
// qamrab oladi: $...$ ichida, [lat]...[/lat] ichida, YOKI hech qanday
// belgisiz XOM LaTeX buyrug'i (\tfrac{a}{b}, \sqrt{a}, \times va h.k.) —
// AI ba'zan teglarni butunlay unutib qo'yadi, shuning uchun buyruqning
// o'zini ham (belgisiz holda) tanib, chizadi.
const _LATEX_QISM_NAQSHI = "\\[lat\\][^]*?\\[\\/lat\\]|\\$[^$]+\\$|\\\\\\([^]*?\\\\\\)|\\\\\\[[^]*?\\\\\\]|\\\\(?:tfrac|dfrac|frac)\\{[^{}]*\\}\\{[^{}]*\\}|\\\\sqrt\\{[^{}]*\\}|\\\\(?:lim|sum|prod|int)(?:_\\{[^{}]*\\})?(?:\\^\\{[^{}]*\\})?|\\\\(?:to|times|div|cdot|pm|leq|geq|neq|infty|approx)(?![a-zA-Z])";
const _LATEX_BOLISH_REGEX = new RegExp(`(${_LATEX_QISM_NAQSHI})`, "g");

function _latexMatniniAjrat(qism) {
  if (qism.startsWith("$") && qism.endsWith("$") && qism.length > 2) return qism.slice(1, -1);
  if (qism.startsWith("[lat]") && qism.endsWith("[/lat]")) return qism.slice(5, -6);
  if (qism.startsWith("\\(") && qism.endsWith("\\)")) return qism.slice(2, -2);
  if (qism.startsWith("\\[") && qism.endsWith("\\]")) return qism.slice(2, -2);
  if (qism.startsWith("\\")) return qism; // xom LaTeX buyrug'i — belgisiz, to'g'ridan-to'g'ri KaTeX'ga beriladi
  return null;
}

const AralashMatn = React.memo(function AralashMatn({ matn, className, style }) {
  const translation=useTranslatedContent(matn);
  matn=translation.text;
  // $...$ , [lat]...[/lat] VA belgisiz xom LaTeX buyrug'i — uchalasi ham
  // xuddi shu tarzda chiroyli (KaTeX) render qilinadi.
  const qismlar = useMemo(() => (matn || "").split(_LATEX_BOLISH_REGEX), [matn]);
  return (
    <p className={className} style={{ whiteSpace: "pre-wrap", ...style }}>
      {qismlar.map((qism, i) => {
        const latexMatni = _latexMatniniAjrat(qism);
        if (latexMatni !== null) {
          try {
            const html = katex.renderToString(latexMatni, { throwOnError: false, output: "html", displayMode: false });
            return <span key={i} dangerouslySetInnerHTML={{ __html: html }} />;
          } catch {
            return <span key={i}>{latexMatni}</span>;
          }
        }
        return <span key={i}>{qism}</span>;
      })}
    <ContentTranslationStatus translation={translation}/></p>
  );
});

// LaTeX ifodani OVOZLI O'QISH uchun, tabiiy o'zbekcha gapga aylantiradi.
// Eng ko'p uchraydigan naqshlarni (kasr, daraja, ildiz, asosiy amallar)
// qamrab oladi — juda murakkab/ichma-ich formulalarda mukammal
// bo'lmasligi mumkin, lekin odatiy o'quv formulalari uchun ishlaydi.
function latexniOzbekchaOqishga(latex) {
  let m = latex || "";
  m = m.replace(/\\frac\{([^{}]+)\}\{([^{}]+)\}/g, " $1 bo'lak $2 dan ");
  m = m.replace(/\\sqrt\{([^{}]+)\}/g, " $1 dan kvadrat ildiz ");
  m = m.replace(/([a-zA-Z0-9]+)\^\{([^{}]+)\}/g, " $1 ning $2 darajasi ");
  m = m.replace(/([a-zA-Z0-9]+)\^([a-zA-Z0-9])/g, " $1 ning $2 darajasi ");
  m = m.replace(/([a-zA-Z0-9]+)_\{([^{}]+)\}/g, " $1 indeks $2 ");
  m = m.replace(/\\times|\\cdot/g, " ko'paytirish ");
  m = m.replace(/\\div/g, " bo'lish ");
  m = m.replace(/\\pi/g, " pi ");
  m = m.replace(/\\pm/g, " plyus-minus ");
  m = m.replace(/\\leq/g, " kichik yoki teng ");
  m = m.replace(/\\geq/g, " katta yoki teng ");
  m = m.replace(/\+/g, " qo'shish ");
  m = m.replace(/(?<!\d)-(?!\d)/g, " minus ");
  m = m.replace(/=/g, " teng ");
  m = m.replace(/[{}\\$]/g, " ");
  return m.replace(/\s+/g, " ").trim();
}

// Matnni SO'ZMA-SO'Z, joriy o'qilayotgan so'z BELGILANGAN holda
// ko'rsatadi — Web Speech API'ning "boundary" hodisasi bilan bog'lanadi
// (tashqi, pullik TTS xizmat SHART emas — brauzerning o'zi o'qiydi).
function OqiladiganMatn({ matn, joriySozIndeksi }) {
  useKbInterfaceLocale();
  const sozlar = useMemo(() => matn.split(/(\s+)/), [matn]);
  return (
    <p className="text-sm leading-relaxed whitespace-pre-line" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>
      {sozlar.map((soz, i) => (
        <span key={i} style={i === joriySozIndeksi
          ? { backgroundColor: "#FDE8B8", fontWeight: 700, borderRadius: 4, padding: "0 2px" }
          : {}}>
          {soz}
        </span>
      ))}
    </p>
  );
}

const OVOZ_TIL_LANG = { uz: "uz-UZ", en: "en-US", ru: "ru-RU", de: "de-DE", fr: "fr-FR", es: "es-ES", ar: "ar-SA", tr: "tr-TR", zh: "zh-CN", ja: "ja-JP", ko: "ko-KR" };

function _ovozTiliniTuzat(til) {
  const kalit = String(til || "").trim().toLowerCase().replace("_", "-").split("-", 1)[0];
  return Object.prototype.hasOwnProperty.call(OVOZ_TIL_LANG, kalit) ? kalit : "uz";
}

function _ovozJinsiniTuzat(jins) {
  return ["ogil", "o'g'il", "erkak", "male", "boy"].includes(String(jins || "").trim().toLowerCase()) ? "ogil" : "qiz";
}

function _ovozQismlargaBol(matn) {
  return splitSpeechText(matn);
}

function _brauzerOvoziniTanla(til, jins) {
  return selectBrowserVoice(globalThis.speechSynthesis?.getVoices?.() || [], _ovozTiliniTuzat(til), _ovozJinsiniTuzat(jins));
}

function _matnniOvozgaTayyorla(matn, til = "uz") {
  return prepareSpeech(matn, _ovozTiliniTuzat(til));
}

function OvozliOqishTugmasi({
  matn,
  kontentId,
  oqilayotganId,
  setOqilayotganId,
  joriySozIndeksi,
  setJoriySozIndeksi,
  asosiyTil = "uz",
  ovozJinsi = "qiz",
}) {
  useKbInterfaceLocale();
  const [tezlik, setTezlik] = useState(1);
  const [pauzada, setPauzada] = useState(false);
  const [talaffuzXatosi, setTalaffuzXatosi] = useState("");
  const audioRef = useRef(null);
  const speechRunRef = useRef(0);
  const oqilyaptimi = oqilayotganId === kontentId;

  const boshla = (boshlanishTezligi) => {
    const run = ++speechRunRef.current;
    const current = () => speechRunRef.current === run;
    window.speechSynthesis?.cancel();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setPauzada(false);
    setTalaffuzXatosi("");
    let qismlar;
    try { qismlar = _ovozQismlargaBol(matn, asosiyTil)
      .map((qism) => ({ ...qism, tayyor: _matnniOvozgaTayyorla(qism.matn, qism.til) }))
      .filter((qism) => qism.tayyor);
    } catch(error) { setTalaffuzXatosi(error.message); return; }
    const brauzerOvozlari = qismlar.map((qism) => _brauzerOvoziniTanla(qism.til, ovozJinsi));
    let qismIndeksi = 0;
    const tugadi = () => {
      if (!current()) return;
      audioRef.current = null;
      setOqilayotganId(null);
      setJoriySozIndeksi(-1);
      setPauzada(false);
    };
    if (!brauzerOvozlari.every(Boolean)) {
      const qs = new URLSearchParams({
        matn: String(matn || ""),
        jins: _ovozJinsiniTuzat(ovozJinsi),
        asosiy_til: "uz",
        revision: SPEECH_REVISION,
      });
      const audio = new Audio(`${API_BASE}/api/ovoz?${qs.toString()}`);
      audio.playbackRate = boshlanishTezligi;
      audio.onended = tugadi;
      audio.onerror = tugadi;
      audioRef.current = audio;
      setOqilayotganId(kontentId);
      audio.play().catch(tugadi);
      return;
    }
    const keyingisiniOqi = () => {
      if (!current()) return;
      if (qismIndeksi >= qismlar.length) { tugadi(); return; }
      const joriyQismIndeksi = qismIndeksi++;
      const qism = qismlar[joriyQismIndeksi];
      const sozlar = qism.tayyor.split(/(\s+)/);
      let pozitsiya = 0;
      const sozPozitsiyalari = sozlar.map((s) => { const p = pozitsiya; pozitsiya += s.length; return p; });
      const utterance = new SpeechSynthesisUtterance(qism.tayyor);
      utterance.lang = OVOZ_TIL_LANG[qism.til];
      utterance.voice = brauzerOvozlari[joriyQismIndeksi];
      utterance.rate = boshlanishTezligi;
      utterance.pitch = _ovozJinsiniTuzat(ovozJinsi) === "ogil" ? 0.92 : 1.04;
      utterance.onboundary = (e) => {
        if (!current()) return;
        if (e.name && e.name !== "word") return;
        let idx = 0;
        for (let i = 0; i < sozPozitsiyalari.length; i++) {
          if (sozPozitsiyalari[i] <= e.charIndex) idx = i; else break;
        }
        setJoriySozIndeksi(idx);
      };
      utterance.onend = keyingisiniOqi;
      utterance.onerror = tugadi;
      window.speechSynthesis?.speak(utterance);
    };
    setOqilayotganId(kontentId);
    keyingisiniOqi();
  };

  const pauzaYokiDavomEttir = () => {
    if (audioRef.current) {
      if (pauzada) audioRef.current.play();
      else audioRef.current.pause();
      setPauzada(!pauzada);
      return;
    }
    if (pauzada) { window.speechSynthesis?.resume(); setPauzada(false); }
    else { window.speechSynthesis?.pause(); setPauzada(true); }
  };

  const toxtat = () => {
    speechRunRef.current++;
    window.speechSynthesis?.cancel();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setOqilayotganId(null);
    setJoriySozIndeksi(-1);
    setPauzada(false);
  };

  const tezlikOzgar = (yangiTezlik) => {
    setTezlik(yangiTezlik);
    if (audioRef.current) {
      audioRef.current.playbackRate = yangiTezlik;
      return;
    }
    if (oqilyaptimi) boshla(yangiTezlik); // o'qish davomida tezlik o'zgarsa, shu joydan emas, boshidan qayta — brauzerlar tezlikni jonli o'zgartirishni qo'llamaydi
  };

  useEffect(() => () => {
    speechRunRef.current++;
    window.speechSynthesis?.cancel();
    if (audioRef.current) audioRef.current.pause();
  }, []);

  return (
    <div className="flex items-center gap-1.5 mt-2 flex-wrap">
      {talaffuzXatosi && <span role="alert" className="text-xs text-red-700">{talaffuzXatosi}</span>}
      <button onClick={() => (oqilyaptimi ? toxtat() : boshla(tezlik))}
        className="text-xs font-semibold px-3 py-1.5 rounded-lg" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
        {oqilyaptimi ? __kbUi("⏹ To'xtatish") : __kbUi("🔊 O'qib berish")}
      </button>
      {oqilyaptimi && (
        <button onClick={pauzaYokiDavomEttir}
          className="text-xs font-semibold px-3 py-1.5 rounded-lg" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
          {pauzada ? __kbUi("▶ Davom") : __kbUi("⏸ Pauza")}
        </button>
      )}
      {[0.75, 1, 1.25, 1.5].map((t) => (
        <button key={t} onClick={() => tezlikOzgar(t)}
          className="text-xs font-semibold px-2.5 py-1.5 rounded-lg"
          style={tezlik === t ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#8A8578" }}>
          {__kbUi(t)}{__kbUi("x")}</button>
      ))}
    </div>
  );
}

function SavolRasmi({ rasmId }) {
  useKbInterfaceLocale();
  const [holat, setHolat] = useState("yuklanmoqda"); // yuklanmoqda | tayyor | xato
  useEffect(() => { setHolat("yuklanmoqda"); }, [rasmId]);

  if (holat === "xato") {
    return null; // rasm topilmasa/yuklanmasa — hech narsa ko'rsatilmaydi, joy egallamaydi
  }
  return (
    <div className="relative mb-4">
      {holat === "yuklanmoqda" && (
        <div className="w-full rounded-xl flex items-center justify-center py-10" style={{ backgroundColor: "#F1EFE8" }}>
          <Loader2 size={20} className="animate-spin" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
        </div>
      )}
      <img src={
          String(rasmId).startsWith("/api/") ? `${API_BASE}${rasmId}`
          : /^https?:\/\//i.test(String(rasmId)) ? rasmId
          : `${API_BASE}/api/rasm/${rasmId}`
        } alt={__kbUi("")}
        className="w-full rounded-xl object-contain"
        style={{ maxHeight: "260px", backgroundColor: "var(--ui-legacy-background-efebe1, #EFEBE1)", display: holat === "yuklanmoqda" ? "none" : "block" }}
        onLoad={() => setHolat("tayyor")}
        onError={() => setHolat("xato")} />
    </div>
  );
}

function tegsizKorsat(matn) {
  // Ko'rsatishda [ru]so'z[/ru] kabi teglarni yashiradi (faqat ichidagi matnni qoldiradi) —
  // ovozga esa XOM matn (teg bilan) beriladi, shunda mos tilda o'qiladi.
  if (!matn) return matn;
  return matn.replace(/\[\/?[a-zA-Z]+\]/g, "");
}

function Matn({ matn, latex }) {
  const translation=useTranslatedContent(matn);
  matn=translation.text;
  useKbInterfaceLocale();
  // Umumiy yordamchidan foydalanadi — $...$, [lat]...[/lat] va belgisiz
  // xom LaTeX buyrug'ini ham taniydi. is_latex bayrog'iga qaramay, TEGLAR/
  // buyruq o'zi bor-yo'qligini ham tekshiradi — AI ba'zan bayroqni to'g'ri
  // qo'ymasligi yoki teglarni butunlay unutishi mumkin.
  const toza = tegsizKorsat(matn) || "";
  const bormi = toza.includes("$") || toza.includes("[lat]") || toza.includes("\\");
  if (!bormi) return <>{toza}<ContentTranslationStatus translation={translation}/></>;
  const qismlar = toza.split(_LATEX_BOLISH_REGEX);
  return (
    <>
      {qismlar.map((q, i) => {
        const latexMatni = _latexMatniniAjrat(q);
        if (latexMatni !== null) {
          try {
            const html = katex.renderToString(latexMatni, { throwOnError: false, output: "html" });
            return <span key={i} dangerouslySetInnerHTML={{ __html: html }} />;
          } catch {
            return <span key={i}>{latexMatni}</span>;
          }
        }
        return <span key={i}>{q}</span>;
      })}
    <ContentTranslationStatus translation={translation}/></>
  );
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

function Logotip({ compact = false, light = false }) {
  return (
    <div
      className={`${compact ? "w-11 h-11 rounded-xl" : "w-14 h-14 rounded-2xl mx-auto mb-4"} grid grid-cols-2 grid-rows-2 gap-0.5 p-1.5`}
      style={{
        background: light
          ? "linear-gradient(145deg, #FFFFFF, #BFECE7)"
          : "linear-gradient(145deg, #123F61, #08283F)",
        boxShadow: light ? "0 8px 22px rgba(0,0,0,.18)" : "0 10px 28px rgba(8,40,63,.18)",
      }}
    >
      <div className="rounded-sm" style={{ backgroundColor: "#C89B3C" }} />
      <div className="rounded-sm" style={{ backgroundColor: "#2D8B8B" }} />
      <div className="rounded-sm" style={{ backgroundColor: "#2D8B8B" }} />
      <div className="rounded-sm" style={{ backgroundColor: "#C89B3C" }} />
    </div>
  );
}

function Qobiq({ children }) {
  return (
    <div className="premium-auth-page">
      <div className="premium-auth-glow premium-auth-glow-one" />
      <div className="premium-auth-glow premium-auth-glow-two" />
      <div className="premium-auth-card">
        {children}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// 1) KIRISH — Google tugmasi, yoki telefon raqami orqali
// ═══════════════════════════════════════════════════════════
function TelefonKirish({ onOrtga, onKirdi }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [bosqich, setBosqich] = useState("telefon"); // "telefon" | "kod" | "royxat"
  const [telefon, setTelefon] = useState("");
  const [kod, setKod] = useState("");
  const [usul, setUsul] = useState(null); // "telegram" | "sms" — kod qanday yuborilgani
  const [yuklanmoqda, setYuklanmoqda] = useState(false);
  const [xato, setXato] = useState("");
  const [ism, setIsm] = useState("");
  const [rol, setRol] = useState("oquvchi");
  const [sinf, setSinf] = useState("");

  const kodSora = async () => {
    if (!telefon.trim()) { setXato("Telefon raqamini kiriting"); return; }
    setYuklanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/auth/telefon_kod_sorash`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telefon: telefon.trim() }),
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Xato");
      setUsul(d.usul);
      setBosqich("kod");
    } catch (e) { setXato(e.message); } finally { setYuklanmoqda(false); }
  };

  const kodTasdiqla = async () => {
    if (!kod.trim()) { setXato("Kodni kiriting"); return; }
    setYuklanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/auth/telefon_kod_tasdiqla`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telefon: telefon.trim(), kod: kod.trim() }),
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Xato");
      if (d.holat === "kirdi") onKirdi(d.token);
      else setBosqich("royxat");
    } catch (e) { setXato(e.message); } finally { setYuklanmoqda(false); }
  };

  const royxatdanOt = async () => {
    if (!ism.trim()) { setXato("Ismingizni kiriting"); return; }
    setYuklanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/auth/telefon_royxat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          telefon: telefon.trim(), kod: kod.trim(), ism: ism.trim(), rol,
          sinf: rol === "oquvchi" ? sinf.trim() : undefined,
        }),
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Xato");
      onKirdi(d.token);
    } catch (e) { setXato(e.message); } finally { setYuklanmoqda(false); }
  };

  return (
    <Qobiq>
      <button onClick={onOrtga} className="flex items-center gap-1.5 mb-5 text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
        <ChevronLeft size={16} /><InterfaceText text={__kbUi(" Ortga")}/></button>

      {bosqich === "telefon" && (
        <>
          <h2 className="text-lg font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Telefon raqamingiz")}</h2>
          <p className="text-xs mb-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Tasdiqlash kodi yuboramiz (Telegram orqali, bepul — yoki SMS orqali)")}</p>
          <input type="tel" value={telefon} onChange={(e) => setTelefon(e.target.value)} placeholder={__kbUi("+998 90 123 45 67")}
            className="w-full px-4 py-3 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} autoFocus />
          {xato && <p className="text-xs mb-3" style={{ color: "#A32D2D" }}>{__kbUi(xato)}</p>}
          <button onClick={kodSora} disabled={yuklanmoqda}
            className="w-full py-3.5 rounded-xl font-semibold text-white flex items-center justify-center gap-2" style={{ backgroundColor: "#1B4B7A" }}>
            {yuklanmoqda ? <Loader2 size={18} className="animate-spin" /> : __kbUi("Kod yuborish")}
          </button>
        </>
      )}

      {bosqich === "kod" && (
        <>
          <h2 className="text-lg font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Tasdiqlash kodi")}</h2>
          <p className="text-xs mb-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
            {usul === "telegram" ? __kbUi("Kod Telegram botingizga yuborildi.") : __kbUi("Kod SMS orqali yuborildi.")} {telefon}
          </p>
          <input type="text" inputMode="numeric" value={kod} onChange={(e) => setKod(e.target.value)} placeholder={__kbUi("000000")}
            className="w-full px-4 py-3 rounded-xl border text-center text-lg tracking-widest mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} autoFocus />
          {xato && <p className="text-xs mb-3" style={{ color: "#A32D2D" }}>{__kbUi(xato)}</p>}
          <button onClick={kodTasdiqla} disabled={yuklanmoqda}
            className="w-full py-3.5 rounded-xl font-semibold text-white flex items-center justify-center gap-2" style={{ backgroundColor: "#1B4B7A" }}>
            {yuklanmoqda ? <Loader2 size={18} className="animate-spin" /> : uiT("Tasdiqlash")}
          </button>
        </>
      )}

      {bosqich === "royxat" && (
        <>
          <h2 className="text-lg font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Siz haqingizda")}</h2>
          <p className="text-xs mb-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Telefon tasdiqlandi — endi ismingiz va rolingizni ayting")}</p>
          <input type="text" value={ism} onChange={(e) => setIsm(e.target.value)} placeholder={__kbUi("F.I.Sh")}
            className="w-full px-4 py-3 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} autoFocus />
          <div className="flex rounded-full p-1 gap-0.5 mb-3" style={{ backgroundColor: "#F0EDE5" }}>
            {[["oquvchi", "O'quvchi"], ["ota-ona", "Ota-ona"], ["oqituvchi", "O'qituvchi"]].map(([qiymat, nomi]) => (
              <button key={qiymat} onClick={() => setRol(qiymat)} className="flex-1 py-2 rounded-full text-xs font-semibold"
                style={rol === qiymat ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>
                {__kbUi(nomi)}
              </button>
            ))}
          </div>
          {rol === "oquvchi" && (
            <input type="text" value={sinf} onChange={(e) => setSinf(e.target.value)} placeholder={__kbUi("Sinf (masalan: 5)")}
              className="w-full px-4 py-3 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          )}
          {xato && <p className="text-xs mb-3" style={{ color: "#A32D2D" }}>{__kbUi(xato)}</p>}
          <button onClick={royxatdanOt} disabled={yuklanmoqda}
            className="w-full py-3.5 rounded-xl font-semibold text-white flex items-center justify-center gap-2" style={{ backgroundColor: "#1B4B7A" }}>
            {yuklanmoqda ? <Loader2 size={18} className="animate-spin" /> : __kbUi("Yakunlash")}
          </button>
        </>
      )}
    </Qobiq>
  );
}

function LoginEkrani() {
  useKbInterfaceLocale();
  return (
    <div className="premium-login">
      <section className="premium-login-story">
        <div className="premium-login-brand">
          <Logotip compact light />
          <div>
            <strong>{__kbUi("TA'LIM AI")}</strong>
            <span>{__kbUi("Yagona ta'lim ekotizimi")}</span>
          </div>
        </div>

        <div className="premium-login-copy">
          <span className="premium-eyebrow">{__kbUi("MAKTABDAN INDIVIDUAL RIVOJGACHA")}</span>
          <h1>{__kbUi("Har bir o‘quvchining bilim yo‘li bitta joyda.")}</h1>
          <p>{__kbUi("Maktab, o‘quv markazi, to‘garak va AI dars natijalarini aralashtirmasdan kuzating. O‘quvchiga mos dars, ustozga aniq tahlil, ota-onaga tushunarli xulosa.")}</p>
          <div className="premium-login-features">
            <div>
              <span><BarChart3 size={18} /></span>
              <p><b>{__kbUi("Ichma-ich analitika")}</b><small><InterfaceText text={__kbUi("Tizimdan aniq o‘quvchigacha")}/></small></p>
            </div>
            <div>
              <span><Brain size={18} /></span>
              <p><b>{__kbUi("AI pedagog")}</b><small>{__kbUi("Bilimiga qarab o‘rgatadi")}</small></p>
            </div>
            <div>
              <span><Users size={18} /></span>
              <p><b>{__kbUi("Barcha rollar bog‘langan")}</b><small>{__kbUi("O‘quvchi, ustoz va ota-ona")}</small></p>
            </div>
          </div>
        </div>

        <div className="premium-login-foot">
          <span className="premium-live-dot" />{__kbUi("Xavfsiz va uzluksiz ta’lim muhiti")}</div>
      </section>

      <section className="premium-login-action">
        <div className="premium-login-card">
          <div className="premium-mobile-brand">
            <Logotip compact />
            <div><b>{__kbUi("TA'LIM AI")}</b><span>{__kbUi("Yagona ta'lim ekotizimi")}</span></div>
          </div>
          <span className="premium-eyebrow">{__kbUi("SHAXSIY KABINET")}</span>
          <h2><InterfaceText text={__kbUi("Xush kelibsiz")}/></h2>
          <p className="premium-login-note">{__kbUi("Davom etish uchun Google hisobingiz orqali xavfsiz kiring.")}</p>
          <button
            onClick={() => { window.location.href = `${API_BASE}/auth/google/login`; }}
            className="premium-google-button"
          >
            <span className="premium-google-mark">{__kbUi("G")}</span><InterfaceText text={__kbUi("Google orqali kirish")}/><ChevronRight size={18} />
          </button>
          <div className="premium-trust-row">
            <span>{__kbUi("✓ Bitta profil")}</span>
            <span>{__kbUi("✓ Barcha ta’lim muhiti")}</span>
          </div>
          <p className="premium-first-time">{__kbUi("Birinchi marta kirsangiz, keyingi ekranda rolingiz va ta’lim muassasangizni tanlaysiz.")}</p>
        </div>
      </section>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// 2) ULASH — Google email topildi, lekin bot hisobiga ULANMAGAN
// ═══════════════════════════════════════════════════════════
function UlashEkrani({ email, ism, oauthGrant, onUlandi }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
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
        body: JSON.stringify({ email, kod: kod.trim(), oauth_grant: oauthGrant }),
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
          email, ism: ismInput.trim(), rol, oauth_grant: oauthGrant,
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
          <h1 className="text-lg font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Xush kelibsiz!")}</h1>
          <p className="text-sm mt-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{email}</p>
        </div>
        <button onClick={() => setRejim("kod")}
          className="w-full py-4 rounded-xl border flex items-center gap-3 mb-3 text-left"
          style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", backgroundColor: "var(--ui-legacy-background-ffffff, #FFFFFF)" }}>
          <KeyRound size={20} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} />
          <div>
            <p className="font-medium text-sm" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Bot orqali ulash kodim bor")}</p>
            <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Botda \"🔗 Saytga ulanish kodi\" bosgan bo'lsangiz")}</p>
          </div>
        </button>
        <button onClick={() => setRejim("royxat")}
          className="w-full py-4 rounded-xl border flex items-center gap-3 text-left"
          style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", backgroundColor: "var(--ui-legacy-background-ffffff, #FFFFFF)" }}>
          <UserPlus size={20} style={{ color: "#2D8B8B" }} />
          <div>
            <p className="font-medium text-sm" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Yangi ro'yxatdan o'taman")}</p>
            <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Botdan foydalanmagan bo'lsangiz")}</p>
          </div>
        </button>
      </Qobiq>
    );
  }

  if (rejim === "kod") {
    return (
      <Qobiq>
        <button onClick={() => setRejim(null)} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Ortga")}/></button>
        <h1 className="text-lg font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Ulash kodini kiriting")}</h1>
        <p className="text-sm mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Botdagi \"👤 Kabinet → 🔗 Saytga ulanish kodi\"")}</p>
        <input type="text" value={kod} onChange={(e) => setKod(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && kodBilan()}
          placeholder={__kbUi("masalan: UU62JX")}
          className="w-full px-4 py-3 rounded-xl border text-base mb-3 tracking-widest text-center font-semibold"
          style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", backgroundColor: "var(--ui-legacy-background-ffffff, #FFFFFF)" }} />
        {xato && <div className="flex items-center gap-2 text-sm mb-3" style={{ color: "#B0553A" }}><WifiOff size={15} /> {__kbUi(xato)}</div>}
        <button onClick={kodBilan} disabled={yuklanmoqda}
          className="w-full py-3.5 rounded-xl font-semibold text-white flex items-center justify-center gap-2"
          style={{ backgroundColor: "#1B4B7A", opacity: yuklanmoqda ? 0.7 : 1 }}>
          {yuklanmoqda ? <Loader2 size={18} className="animate-spin" /> : __kbUi("Ulash")}
        </button>
      </Qobiq>
    );
  }

  return (
    <Qobiq>
      <button onClick={() => setRejim(null)} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Ortga")}/></button>
      <h1 className="text-lg font-bold mb-5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}><InterfaceText text={__kbUi("Ro'yxatdan o'tish")}/></h1>

      <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Ismingiz")}</label>
      <input type="text" value={ismInput} onChange={(e) => setIsmInput(e.target.value)}
        className="w-full px-4 py-3 rounded-xl border text-base mb-2"
        style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", backgroundColor: "var(--ui-legacy-background-ffffff, #FFFFFF)" }} />

      {oxshashlar.length > 0 && (
        <div className="rounded-xl p-3.5 mb-4" style={{ backgroundColor: "#FFF8E8", border: "1px solid #EEDFB0" }}>
          <p className="text-xs font-medium mb-1" style={{ color: "#6B5B2E" }}>{__kbUi("Botda shunga o'xshash ism topildi:")}</p>
          {oxshashlar.map((o, i) => (
            <p key={i} className="text-xs" style={{ color: "#8A7642" }}>• {o.full_name} ({__kbUi(o.role)})</p>
          ))}
          <p className="text-xs mt-1.5" style={{ color: "#6B5B2E" }}>{__kbUi("Bu sizmi? Bo'lsa, ortga qaytib \"Bot kodim bor\" ni tanlang — aks holda ikkita akkaunt paydo bo'ladi.")}</p>
        </div>
      )}

      <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Kimsiz?")}</label>
      <div className="grid grid-cols-3 gap-2 mb-4">
        {[["oquvchi", "O'quvchi"], ["ota-ona", "Ota-ona"], ["oqituvchi", "O'qituvchi"]].map(([v, l]) => (
          <button key={v} onClick={() => setRol(v)}
            className="py-2.5 rounded-lg border text-xs font-medium"
            style={{
              borderColor: rol === v ? "#1B4B7A" : "#E5E1D8",
              backgroundColor: rol === v ? "#1B4B7A" : "#FFFFFF",
              color: rol === v ? "#FFFFFF" : "#5A5648",
            }}>
            {__kbUi(l)}
          </button>
        ))}
      </div>

      {rol === "oquvchi" && (
        <>
          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Sinf")}/></label>
          <select value={sinf} onChange={(e) => setSinf(e.target.value)}
            className="w-full px-4 py-3 rounded-xl border text-base mb-4"
            style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", backgroundColor: "var(--ui-legacy-background-ffffff, #FFFFFF)" }}>
            {Array.from({ length: 11 }, (_, i) => i + 1).map((n) => (
              <option key={n} value={n}>{n}{__kbUi("-sinf")}</option>
            ))}
          </select>

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Maktab raqami")}</label>
          <input type="text" value={maktabRaqami} onChange={(e) => setMaktabRaqami(e.target.value)}
            placeholder={__kbUi("masalan: 21")}
            className="w-full px-4 py-3 rounded-xl border text-base mb-4"
            style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", backgroundColor: "var(--ui-legacy-background-ffffff, #FFFFFF)" }} />
        </>
      )}

      <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Viloyat")}/></label>
      <select value={viloyat} onChange={(e) => { setViloyat(e.target.value); setTuman(""); }}
        className="w-full px-4 py-3 rounded-xl border text-base mb-4"
        style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", backgroundColor: "var(--ui-legacy-background-ffffff, #FFFFFF)" }}>
        <option value="">{__kbUi("Tanlanmagan")}</option>
        {VILOYATLAR.map((v) => <option key={v} value={v}>{__kbUi(v)}</option>)}
      </select>

      {viloyat && (
        <>
          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Tuman")}/></label>
          <select value={tuman} onChange={(e) => setTuman(e.target.value)}
            className="w-full px-4 py-3 rounded-xl border text-base mb-4"
            style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", backgroundColor: "var(--ui-legacy-background-ffffff, #FFFFFF)" }}>
            <option value="">{__kbUi("Tanlanmagan")}</option>
            {(HUDUDLAR[viloyat] || []).map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </>
      )}

      <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Tug'ilgan sana")}</label>
      <input type="date" value={tugilganSana} onChange={(e) => setTugilganYil(e.target.value)}
        min="1950-01-01" max={new Date().toISOString().split("T")[0]}
        className="w-full px-4 py-3 rounded-xl border text-base mb-4"
        style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", backgroundColor: "var(--ui-legacy-background-ffffff, #FFFFFF)" }} />

      {xato && <div className="flex items-center gap-2 text-sm mb-3" style={{ color: "#B0553A" }}><WifiOff size={15} /> {__kbUi(xato)}</div>}

      <button onClick={royxatBilan} disabled={yuklanmoqda}
        className="w-full py-3.5 rounded-xl font-semibold text-white flex items-center justify-center gap-2"
        style={{ backgroundColor: "#1B4B7A", opacity: yuklanmoqda ? 0.7 : 1 }}>
        {yuklanmoqda ? <Loader2 size={18} className="animate-spin" /> : uiT("Ro'yxatdan o'tish")}
      </button>
    </Qobiq>
  );
}

// ═══════════════════════════════════════════════════════════
// 3) KABINET — token bilan kirilgach
// ═══════════════════════════════════════════════════════════
function MavzularYoliVizual({ mavzular, rang }) {
  useKbInterfaceLocale();
  const [tanlangan, setTanlangan] = useState(null); // ochilgan tugma indeksi | null
  const QADAM = 78, ENI = 260, AMPLITUDA = 78, YUQORI = 46, PASTKI = 46;
  const asosiyRang = rang || "#1B4B7A";

  const nuqtalar = mavzular.map((m, i) => ({
    ...m, x: ENI / 2 + AMPLITUDA * Math.sin(i * 1.05), y: YUQORI + i * QADAM,
  }));
  const balandlik = YUQORI + Math.max(0, mavzular.length - 1) * QADAM + PASTKI;
  const yoliChizigi = nuqtalar.map((n, i) => `${i === 0 ? "M" : "L"} ${n.x.toFixed(1)} ${n.y.toFixed(1)}`).join(" ");
  const hammasiTugagan = mavzular.length > 0 && mavzular.every((m) => m.otilgan_kichik === m.jami_kichik);

  return (
    <div className="relative mx-auto" style={{ width: ENI, height: balandlik + 60 }}>
      <svg viewBox={`0 0 ${ENI} ${balandlik + 60}`} width={ENI} height={balandlik + 60} className="absolute inset-0">
        <text x={ENI / 2} y="26" textAnchor="middle" fontSize="26">🏁</text>
        <path d={yoliChizigi ? `M ${ENI / 2} 34 ${yoliChizigi.slice(2)}` : ""} fill="none" stroke="#E5E1D8" strokeWidth="6" strokeLinecap="round" strokeDasharray="1,14" />
        <text x={ENI / 2} y={balandlik + 42} textAnchor="middle" fontSize="26" opacity={hammasiTugagan ? 1 : 0.35}>🏆</text>
      </svg>
      {nuqtalar.map((n, i) => {
        const holat = n.otilgan_kichik === 0 ? "boshlanmagan" : n.otilgan_kichik < n.jami_kichik ? "jarayonda" : "tugagan";
        const fonRang = holat === "tugagan" ? asosiyRang : holat === "jarayonda" ? "#C89B3C" : "#FFFFFF";
        const chegara = holat === "boshlanmagan" ? "#C4BFAF" : fonRang;
        const matnRang = holat === "boshlanmagan" ? "#8A8578" : "#FFFFFF";
        return (
          <div key={n.topic_code} className="absolute" style={{ left: n.x - 24, top: n.y - 24 }}>
            <button onClick={() => setTanlangan(tanlangan === i ? null : i)}
              className="w-12 h-12 rounded-full flex items-center justify-center font-bold text-base shadow-sm"
              style={{ backgroundColor: fonRang, border: `3px solid ${chegara}`, color: matnRang }}>
              {holat === "tugagan" ? __kbUi("✓") : i + 1}
            </button>
            {tanlangan === i && (
              <div className="absolute z-10 top-14 -left-16 w-40 rounded-xl p-2.5 text-center shadow-lg bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                <p className="text-xs font-medium mb-0.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{n.nomi}</p>
                {n.score !== null && <p className="text-xs font-bold" style={{ color: asosiyRang }}>{n.score}%</p>}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function MavzuQatori({ m, i, sinf, fan, rang, token }) {
  useKbInterfaceLocale();
  const holat = m.otilgan_kichik === 0 ? "boshlanmagan" : m.otilgan_kichik < m.jami_kichik ? "jarayonda" : "tugagan";
  const ikon = holat === "tugagan" ? "✅" : holat === "jarayonda" ? "🟡" : "⬜";
  const fonRang = holat === "tugagan" ? "#EAF3DE" : holat === "jarayonda" ? "#FDF3E0" : "#FFFFFF";
  const chegaraRang = holat === "tugagan" ? "#C9E4B0" : holat === "jarayonda" ? "#F5DFA3" : "#E5E1D8";

  const [ochiq, setOchiq] = useState(false);
  const [tushuntirish, setTushuntirish] = useState(null); // null=hali so'ralmagan, ""=topilmadi, matn=bor
  const [yuklanmoqda, setYuklanmoqda] = useState(false);

  const bosildi = () => {
    if (ochiq) { setOchiq(false); return; }
    setOchiq(true);
    if (tushuntirish !== null) return; // allaqachon yuklangan — qayta so'ramaymiz
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/mavzu_tushuntirish?sinf=${encodeURIComponent(sinf)}&fan=${encodeURIComponent(fan)}&mavzu=${encodeURIComponent(m.nomi)}&topic_code=${encodeURIComponent(m.topic_code)}${token ? `&token=${encodeURIComponent(token)}` : ""}`)
      .then((r) => r.json())
      .then((d) => { setTushuntirish(d.topildi ? d.tushuntirish : ""); setYuklanmoqda(false); })
      .catch(() => { setTushuntirish(""); setYuklanmoqda(false); });
  };

  return (
    <div className="rounded-xl border overflow-hidden" style={{ backgroundColor: fonRang, borderColor: chegaraRang }}>
      <button onClick={bosildi} className="w-full p-3.5 flex items-center gap-3 text-left">
        <span className="text-lg shrink-0">{ikon}</span>
        <span className="text-sm flex-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{i + 1}. {m.nomi}</span>
        {m.score !== null && <span className="text-xs font-semibold shrink-0" style={{ color: "#3B6D11" }}>{m.score}%</span>}
        <span className="text-sm shrink-0">🤖</span>
      </button>
      {ochiq && (
        <div className="px-3.5 pb-3.5">
          {yuklanmoqda ? (
            <div className="py-2"><Loader2 size={16} className="animate-spin" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} /></div>
          ) : tushuntirish ? (
            <AralashMatn matn={tushuntirish} className="text-sm p-3 rounded-lg leading-relaxed" style={{ backgroundColor: "var(--ui-legacy-background-ffffff, #FFFFFF)", color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }} />
          ) : (
            <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bu mavzu uchun hali AI tushuntirishi tayyorlanmagan.")}</p>
          )}
        </div>
      )}
    </div>
  );
}

function TalimYoli({ bolaId, fan, rang, onYopish, token }) {
  useKbInterfaceLocale();
  const [malumot, setMalumot] = useState(null);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");
  const [korinish, setKorinish] = useState("royxat"); // "royxat" | "yol"

  useEffect(() => {
    fetch(`${API_BASE}/api/bola/${bolaId}/yol?fan=${encodeURIComponent(fan)}`)
      .then((r) => r.json())
      .then((d) => { if (d.detail) throw new Error(d.detail); setMalumot(d); setYuklanmoqda(false); })
      .catch((e) => { setXato(e.message || "Yuklab bo'lmadi"); setYuklanmoqda(false); });
  }, [bolaId, fan]);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
      <div className="px-5 pt-6 pb-10 max-w-md mx-auto">
        <button onClick={onYopish} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Ortga")}/></button>
        <div className="flex items-center gap-3 mb-5">
          <div className="w-11 h-11 rounded-2xl flex items-center justify-center text-white font-bold shrink-0" style={{ backgroundColor: rang || "#1B4B7A" }}>
            {__kbUi(fan.slice(0, 1))}
          </div>
          <div>
            <h1 className="text-xl font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{fan}</h1>
            <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}><InterfaceText text={__kbUi("Ta'lim yo'li")}/></p>
          </div>
        </div>

        {yuklanmoqda ? (
          <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
        ) : xato ? (
          <p className="text-sm" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>
        ) : (
          <>
            <div className="rounded-2xl p-5 bg-white border mb-5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Yo'lning bosib o'tilgan qismi")}</p>
                <p className="text-sm font-bold" style={{ color: rang || "#1B4B7A" }}>{malumot.otilgan_mavzu} / {malumot.jami_mavzu}</p>
              </div>
              <div className="h-2.5 rounded-full overflow-hidden mb-1" style={{ backgroundColor: "var(--ui-legacy-background-efebe1, #EFEBE1)" }}>
                <div className="h-full rounded-full transition-all" style={{ width: `${malumot.yol_foizi}%`, backgroundColor: rang || "#1B4B7A" }} />
              </div>
              <p className="text-xs mb-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{malumot.yol_foizi}{__kbUi("% yo'l bosib o'tilgan")}</p>

              <div className="flex items-center justify-between">
                <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Bilimlar samaradorligi")}</p>
                <p className="text-sm font-bold" style={{ color: "#C89B3C" }}>{malumot.samaradorlik_foizi}%</p>
              </div>
            </div>

            {malumot.choraklar && malumot.choraklar.length > 0 && (
              <div className="grid gap-2 mb-5" style={{ gridTemplateColumns: `repeat(${malumot.choraklar.length}, minmax(0, 1fr))` }}>
                {malumot.choraklar.map((ch) => {
                  const ikon = ch.foiz === 100 ? "✅" : ch.foiz > 0 ? "🟡" : "⚪";
                  return (
                    <div key={ch.chorak} className="rounded-xl p-3 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                      <p className="text-xs font-medium mb-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{ch.chorak}{__kbUi("-chorak")}</p>
                      <p className="text-lg mb-0.5">{ikon}</p>
                      <p className="text-xs font-bold" style={{ color: ch.foiz === 100 ? "#3B6D11" : ch.foiz > 0 ? "#8A5A1C" : "#8A8578" }}>{ch.foiz}%</p>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="flex gap-2 mb-5">
              <button onClick={() => setKorinish("royxat")}
                className="flex-1 py-2 rounded-xl text-xs font-semibold"
                style={korinish === "royxat" ? { backgroundColor: rang || "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>{__kbUi("📋 Ro'yxat")}</button>
              <button onClick={() => setKorinish("yol")}
                className="flex-1 py-2 rounded-xl text-xs font-semibold"
                style={korinish === "yol" ? { backgroundColor: rang || "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>{__kbUi("🛤️ Yo'l")}</button>
            </div>

            {korinish === "yol" ? (
              <div className="py-2 overflow-x-auto"><MavzularYoliVizual mavzular={malumot.mavzular} rang={rang} /></div>
            ) : (
              <div className="space-y-2">
                {malumot.mavzular.map((m, i) => (
                  <MavzuQatori token={token} key={m.topic_code} m={m} i={i} sinf={malumot.sinf} fan={fan} rang={rang} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function TogarakYoli({ bolaId, togarakId, onYopish }) {
  useKbInterfaceLocale();
  const [malumot, setMalumot] = useState(null);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");
  const [korinish, setKorinish] = useState("royxat"); // "royxat" | "yol"

  useEffect(() => {
    fetch(`${API_BASE}/api/bola/${bolaId}/togarak_yoli/${togarakId}`)
      .then((r) => r.json())
      .then((d) => { if (d.detail) throw new Error(d.detail); setMalumot(d); setYuklanmoqda(false); })
      .catch((e) => { setXato(e.message || "Yuklab bo'lmadi"); setYuklanmoqda(false); });
  }, [bolaId, togarakId]);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
      <div className="px-5 pt-6 pb-10 max-w-md mx-auto">
        <button onClick={onYopish} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Ortga")}/></button>
        {yuklanmoqda ? (
          <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
        ) : xato ? (
          <p className="text-sm" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>
        ) : (
          <>
            <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>🔀 {malumot.togarak_nomi}</h1>
            <p className="text-sm mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{malumot.fan}{__kbUi(" · To'garak yo'li")}</p>

            <div className="rounded-2xl p-5 bg-white border mb-5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Yo'lning bosib o'tilgan qismi")}</p>
                <p className="text-sm font-bold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{malumot.otilgan_mavzu} / {malumot.jami_mavzu}</p>
              </div>
              <div className="h-2.5 rounded-full overflow-hidden mb-1" style={{ backgroundColor: "var(--ui-legacy-background-efebe1, #EFEBE1)" }}>
                <div className="h-full rounded-full transition-all" style={{ width: `${malumot.yol_foizi}%`, backgroundColor: "#1B4B7A" }} />
              </div>
              <p className="text-xs mb-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{malumot.yol_foizi}{__kbUi("% yo'l bosib o'tilgan")}</p>
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Bilimlar samaradorligi")}</p>
                <p className="text-sm font-bold" style={{ color: "#C89B3C" }}>{malumot.samaradorlik_foizi}%</p>
              </div>
            </div>

            {malumot.choraklar && malumot.choraklar.length > 0 && (
              <div className="grid gap-2 mb-5" style={{ gridTemplateColumns: `repeat(${malumot.choraklar.length}, minmax(0, 1fr))` }}>
                {malumot.choraklar.map((ch) => {
                  const ikon = ch.foiz === 100 ? "✅" : ch.foiz > 0 ? "🟡" : "⚪";
                  return (
                    <div key={ch.chorak} className="rounded-xl p-3 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                      <p className="text-xs font-medium mb-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{ch.chorak}{__kbUi("-chorak")}</p>
                      <p className="text-lg mb-0.5">{ikon}</p>
                      <p className="text-xs font-bold" style={{ color: ch.foiz === 100 ? "#3B6D11" : ch.foiz > 0 ? "#8A5A1C" : "#8A8578" }}>{ch.foiz}%</p>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="flex gap-2 mb-5">
              <button onClick={() => setKorinish("royxat")}
                className="flex-1 py-2 rounded-xl text-xs font-semibold"
                style={korinish === "royxat" ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>{__kbUi("📋 Ro'yxat")}</button>
              <button onClick={() => setKorinish("yol")}
                className="flex-1 py-2 rounded-xl text-xs font-semibold"
                style={korinish === "yol" ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>{__kbUi("🛤️ Yo'l")}</button>
            </div>

            {korinish === "yol" ? (
              <div className="py-2 overflow-x-auto"><MavzularYoliVizual mavzular={malumot.mavzular} rang="#1B4B7A" /></div>
            ) : (
              <div className="space-y-2">
                {malumot.mavzular.map((m, i) => {
                  const holat = m.otilgan_kichik === 0 ? "boshlanmagan" : m.otilgan_kichik < m.jami_kichik ? "jarayonda" : "tugagan";
                  const ikon = holat === "tugagan" ? "✅" : holat === "jarayonda" ? "🟡" : "⬜";
                  const fonRang = holat === "tugagan" ? "#EAF3DE" : holat === "jarayonda" ? "#FDF3E0" : "#FFFFFF";
                  const chegaraRang = holat === "tugagan" ? "#C9E4B0" : holat === "jarayonda" ? "#F5DFA3" : "#E5E1D8";
                  return (
                  <div key={m.topic_code} className="rounded-xl p-3.5 flex items-center gap-3 border" style={{ backgroundColor: fonRang, borderColor: chegaraRang }}>
                    <span className="text-lg shrink-0">{ikon}</span>
                    <span className="text-sm flex-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{i + 1}. {m.nomi}</span>
                    {m.score !== null && <span className="text-xs font-semibold shrink-0" style={{ color: "#3B6D11" }}>{m.score}%</span>}
                  </div>
                );
              })}
            </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function StatKartochka({ ikon, qiymat, yorliq, rang, fon }) {
  useKbInterfaceLocale();
  return (
    <div className="rounded-xl p-3 flex items-center gap-2.5" style={{ backgroundColor: fon }}>
      <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0 bg-white">
        {React.cloneElement(ikon, { color: rang })}
      </div>
      <div className="min-w-0">
        <p className="text-base font-bold leading-tight truncate" style={{ color: rang }}>{qiymat}</p>
        <p className="text-xs leading-tight truncate" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{yorliq}</p>
      </div>
    </div>
  );
}

function FanBolimi({ fan, onBosildi }) {
  useKbInterfaceLocale();
  return (
    <button onClick={onBosildi}
      className="w-full rounded-2xl border bg-white p-5 flex items-center gap-4 text-left transition-transform active:scale-[0.98]"
      style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
      <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-xs shrink-0" style={{ backgroundColor: fan.rang }}>{fan.qisqa}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-2">
          <h3 className="font-semibold text-lg" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{fan.nom}</h3>
          <span className="text-2xl font-bold shrink-0" style={{ color: fan.rang }}>{fan.foiz}%</span>
        </div>
        <div className="mt-2 h-2 rounded-full overflow-hidden" style={{ backgroundColor: "var(--ui-legacy-background-efebe1, #EFEBE1)" }}>
          <div className="h-full rounded-full transition-all duration-700" style={{ width: `${fan.foiz}%`, backgroundColor: fan.rang }} />
        </div>
      </div>
      <ChevronRight size={20} className="shrink-0" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
    </button>
  );
}

function ReaksiyaOyini({ token, bolaId, onYopish }) {
  useKbInterfaceLocale();
  const [holat, setHolat] = useState("boshlanmagan"); // boshlanmagan | kutish | tayyor | erta | natija
  const [natija, setNatija] = useState(null); // millisekund
  const [tarix, setTarix] = useState(null);
  const boshlanishVaqtiRef = useRef(0);
  const kutishTaymerRef = useRef(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/bola/${bolaId}/reaksiya_tarixi`)
      .then((r) => r.json())
      .then(setTarix)
      .catch(() => {});
    return () => clearTimeout(kutishTaymerRef.current);
  }, [bolaId]);

  const boshlash = () => {
    setHolat("kutish");
    setNatija(null);
    const kutish = 1000 + Math.random() * 2000; // 1-3 soniya
    kutishTaymerRef.current = setTimeout(() => {
      boshlanishVaqtiRef.current = performance.now();
      setHolat("tayyor");
    }, kutish);
  };

  const bosildi = async () => {
    if (holat === "kutish") {
      clearTimeout(kutishTaymerRef.current);
      setHolat("erta");
      return;
    }
    if (holat !== "tayyor") return;
    const ms = Math.round(performance.now() - boshlanishVaqtiRef.current);
    setNatija(ms);
    setHolat("natija");
    try {
      await fetch(`${API_BASE}/api/bola/reaksiya_natija_saqla`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, millisekund: ms }),
      });
      const yangiTarix = await fetch(`${API_BASE}/api/bola/${bolaId}/reaksiya_tarixi`).then((r) => r.json());
      setTarix(yangiTarix);
    } catch { /* natija saqlanmasa ham o'yin davom etaveradi */ }
  };

  const rangi = { boshlanmagan: "#F0EDE5", kutish: "#E24B4A", tayyor: "#3B6D11", erta: "#8A5A1C", natija: "#1B4B7A" }[holat];

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center px-6" style={{ backgroundColor: "rgba(43,43,43,0.92)" }}>
      <button onClick={onYopish} className="absolute top-6 right-6 w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.15)" }}>
        <X size={18} style={{ color: "#fff" }} />
      </button>
      <p className="text-white text-sm mb-6 text-center">{__kbUi("🎮 Reaksiya o'yini — qiziqarli tezlik sinovi (ilmiy o'lchov emas)")}</p>
      <button onClick={holat === "tayyor" || holat === "kutish" ? bosildi : boshlash}
        className="w-56 h-56 rounded-full flex flex-col items-center justify-center text-center px-4 transition-colors"
        style={{ backgroundColor: rangi }}>
        {holat === "boshlanmagan" && <span className="text-white font-bold text-lg">{__kbUi("Boshlash")}</span>}
        {holat === "kutish" && <span className="text-white font-semibold">{__kbUi("Kuting...")}</span>}
        {holat === "tayyor" && <span className="text-white font-bold text-lg">{__kbUi("HOZIR BOSING!")}</span>}
        {holat === "erta" && <span className="text-white font-semibold">{__kbUi("Juda erta! Qayta urining")}</span>}
        {holat === "natija" && (
          <>
            <span className="text-white font-bold text-3xl">{natija}</span>
            <span className="text-white text-sm">{__kbUi("millisekund")}</span>
          </>
        )}
      </button>
      {(holat === "erta" || holat === "natija") && (
        <button onClick={boshlash} className="mt-6 px-5 py-2.5 rounded-full text-sm font-semibold text-white" style={{ backgroundColor: "#1B4B7A" }}><InterfaceText text={__kbUi("Qayta urinish")}/></button>
      )}
      {tarix && tarix.jami_urinish > 0 && (
        <div className="mt-8 flex gap-4">
          <div className="text-center">
            <p className="text-white text-xl font-bold">{tarix.eng_yaxshi}</p>
            <p className="text-white text-xs" style={{ opacity: 0.7 }}>{__kbUi("eng yaxshi (ms)")}</p>
          </div>
          <div className="text-center">
            <p className="text-white text-xl font-bold">{tarix.ortacha}</p>
            <p className="text-white text-xs" style={{ opacity: 0.7 }}>{__kbUi("o'rtacha (ms)")}</p>
          </div>
          <div className="text-center">
            <p className="text-white text-xl font-bold">{tarix.jami_urinish}</p>
            <p className="text-white text-xs" style={{ opacity: 0.7 }}>{__kbUi("jami urinish")}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function BilimTab({ data, bolaId, rang, token, otaOnaUchun }) {
  useKbInterfaceLocale();
  const heroRang = rang || "#1B4B7A";
  const [yolFani, setYolFani] = useState(null); // {fan, rang} | null
  const [togarakYoliId, setTogarakYoliId] = useState(null); // ochilgan to'garak yo'li id | null
  const [mengaTogaraklarim, setMenTogaraklarim] = useState([]);
  const [bugungiTavsiya, setBugungiTavsiya] = useState(null); // {tavsiyalar: [...]} | null (hali yuklanmagan)
  const [haftalik, setHaftalik] = useState(null); // {jami_mavzu, ortacha_ball, ...} | null (hali yuklanmagan)
  const [davomat, setDavomat] = useState(null); // {jami_kun, keldi, kelmadi, ketma_ket_kelmagan} | null
  const [qiyinlikTahlili, setQiyinlikTahlili] = useState(null); // {darajalar, javob_turlari} | null
  const [reaksiyaOyiniOchiq, setReaksiyaOyiniOchiq] = useState(false);
  const [mosSinf, setMosSinf] = useState(null); // {sinf_id, sinf_nomi, maktab_nomi, rahbar_ismi} | null
  const [qoshilishParoli, setQoshilishParoli] = useState("");
  const [qoshilinmoqda, setQoshilinmoqda] = useState(false);
  const [qoshilishXato, setQoshilishXato] = useState("");
  const radarData = data.fanlar.map((f) => ({ fan: f.qisqa, foiz: f.foiz }));

  useEffect(() => {
    if (!bolaId) return;
    fetch(`${API_BASE}/api/bola/${bolaId}/togaraklarim`)
      .then((r) => r.json())
      .then((d) => setMenTogaraklarim(d.togaraklar || []))
      .catch(() => {});
  }, [bolaId]);

  useEffect(() => {
    if (!bolaId) return;
    fetch(`${API_BASE}/api/bola/${bolaId}/bugungi_tavsiya`)
      .then((r) => r.json())
      .then((d) => setBugungiTavsiya(d))
      .catch(() => setBugungiTavsiya({ tavsiyalar: [] }));
  }, [bolaId]);

  useEffect(() => {
    if (!bolaId) return;
    fetch(`${API_BASE}/api/bola/${bolaId}/haftalik_xulosa`)
      .then((r) => r.json())
      .then((d) => setHaftalik(d))
      .catch(() => {});
  }, [bolaId]);

  useEffect(() => {
    if (!bolaId || !token) return;
    fetch(`${API_BASE}/api/bola/${bolaId}/davomat_xulosa?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => setDavomat(d))
      .catch(() => {});
  }, [bolaId, token]);

  useEffect(() => {
    if (!bolaId) return;
    fetch(`${API_BASE}/api/bola/${bolaId}/qiyinlik_tahlili`)
      .then((r) => r.json())
      .then((d) => setQiyinlikTahlili(d))
      .catch(() => {});
  }, [bolaId]);

  // FAQAT o'quvchining O'Z Bilim ekranida (token mavjud VA ota-ona
  // ko'rinishidan EMAS) — ota-ona farzandini ko'rayotganda BU banner
  // ko'rinmaydi, chunki sinfga qo'shilishni faqat o'quvchining o'zi
  // tasdiqlashi kerak. (token endi davomat uchun ota-ona ko'rinishida
  // ham uzatiladi, shu sabab bu tekshiruv otaOnaUchun bilan alohida.)
  useEffect(() => {
    if (!token || otaOnaUchun) return;
    fetch(`${API_BASE}/api/oquvchi/mos_sinf?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => setMosSinf(d.topildi ? d : null))
      .catch(() => {});
  }, [token, otaOnaUchun]);

  const sinfgaQoshil = async () => {
    if (!qoshilishParoli.trim()) { setQoshilishXato("Parolni kiriting"); return; }
    setQoshilinmoqda(true); setQoshilishXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oquvchi/sinfga_qoshil?token=${encodeURIComponent(token)}&sinf_id=${mosSinf.sinf_id}&parol=${encodeURIComponent(qoshilishParoli.trim())}`, {
        method: "POST",
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Xato");
      setMosSinf(null);
      setQoshilishParoli("");
    } catch (e) {
      setQoshilishXato(e.message);
    } finally { setQoshilinmoqda(false); }
  };

  const fanRangiTop = (fanNomi) => data.fanlar.find((f) => f.nom === fanNomi)?.rang || fanRangiOl(fanNomi);

  return (
    <div>
      <div className="relative overflow-hidden px-5 pt-6 pb-8" style={{ backgroundColor: heroRang }}>
        <div className="relative">
          <h1 className="mt-1 text-2xl font-bold text-white">{data.bola?.ism || __kbUi("Sizning bilimingiz")}</h1>
          <div className="mt-6 flex items-end gap-4">
            <div>
              <div className="flex items-baseline gap-1">
                <span className="text-5xl font-bold text-white">{data.umumiy_foiz}</span>
                <span className="text-xl font-bold" style={{ color: "#C89B3C" }}>%</span>
              </div>
              <p className="text-xs mt-1 flex items-center gap-1" style={{ color: "#B8CBDA" }}><TrendingUp size={12} /> {__kbUi(darajaNom(data.umumiy_foiz))}</p>
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

          {data.jami_mavzu > 0 && (
            <div className="mt-5">
              <div className="flex items-center justify-between mb-1.5">
                <p className="text-xs font-medium" style={{ color: "#B8CBDA" }}>{__kbUi("🛤️ Umumiy ta'lim yo'li")}</p>
                <p className="text-xs font-semibold text-white">{data.otilgan_mavzu} / {data.jami_mavzu}{__kbUi(" mavzu")}</p>
              </div>
              <div className="h-2 rounded-full overflow-hidden" style={{ backgroundColor: "rgba(255,255,255,0.15)" }}>
                <div className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${Math.round((data.otilgan_mavzu / data.jami_mavzu) * 100)}%`, backgroundColor: "#C89B3C" }} />
              </div>
            </div>
          )}
        </div>
      </div>
      <div className="px-5 -mt-3 pb-4 space-y-3">
        <div className="rounded-2xl p-3.5 bg-white border shadow-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <div className="grid grid-cols-2 gap-2.5">
            <StatKartochka ikon={<Flame size={18} />} rang="#C89B3C" fon="#FDF3E0"
              qiymat={haftalik ? (haftalik.ketma_ket_kun > 0 ? haftalik.ketma_ket_kun : "0") : "—"}
              yorliq="kun ketma-ket" />
            <StatKartochka ikon={<BookOpen size={18} />} rang="#1B4B7A" fon="#EAF1F7"
              qiymat={data.jami_mavzu > 0 ? `${data.otilgan_mavzu}/${data.jami_mavzu}` : "0"}
              yorliq="mavzu o'rganilgan" />
            <StatKartochka ikon={<CalendarCheck size={18} />} rang="#3B6D11" fon="#EAF3DE"
              qiymat={davomat && davomat.jami_kun > 0 ? `${Math.round((davomat.keldi / davomat.jami_kun) * 100)}%` : "—"}
              yorliq="davomat (30 kun)" />
            <StatKartochka ikon={<Users size={18} />} rang="#8B5FBF" fon="#F3EEFA"
              qiymat={mengaTogaraklarim.length}
              yorliq="faol to'garak" />
          </div>
        </div>

        {mosSinf && (
          <div className="rounded-2xl p-4 border mb-1" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", borderColor: "#1B4B7A" }}>
            <p className="text-sm font-bold mb-1" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("🏫 Sinfingiz topildi!")}</p>
            <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
              {mosSinf.maktab_nomi} — {mosSinf.sinf_nomi}{mosSinf.rahbar_ismi ? __kbUi(` (rahbar: ${mosSinf.rahbar_ismi})`) : __kbUi("")}{__kbUi(" tomonidan tuzilgan. Qo'shilish uchun sinf rahbaringizdan olgan 4 xonali parolni kiriting.")}</p>
            <div className="flex gap-2">
              <input type="text" value={qoshilishParoli} onChange={(e) => setQoshilishParoli(e.target.value)}
                placeholder={__kbUi("4 xonali parol")} maxLength={4}
                className="flex-1 px-3.5 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              <button onClick={sinfgaQoshil} disabled={qoshilinmoqda}
                className="px-4 py-2.5 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: qoshilinmoqda ? 0.7 : 1 }}>
                {qoshilinmoqda ? __kbUi("...") : __kbUi("Qo'shilish")}
              </button>
            </div>
            {qoshilishXato && <p className="text-xs mt-2" style={{ color: "#A32D2D" }}>{__kbUi(qoshilishXato)}</p>}
          </div>
        )}

        {bugungiTavsiya && bugungiTavsiya.tavsiyalar && bugungiTavsiya.tavsiyalar.length > 0 && (
          <div className="rounded-2xl p-4 bg-white border mb-1" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <p className="text-sm font-bold mb-0.5 flex items-center gap-1.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📅 Bugungi tavsiya")}</p>
            <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bu mavzular eslaringizdan chiqishi mumkin — takrorlab qo'ying.")}</p>
            <div className="space-y-2">
              {bugungiTavsiya.tavsiyalar.map((t, i) => {
                const bRang = fanRangiTop(t.fan);
                const daraja_ikon = t.daraja === "yuqori" ? "🔴" : "🟡";
                return (
                  <button key={i} onClick={() => setYolFani({ fan: t.fan, rang: bRang })}
                    className="w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-left"
                    style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                    <span className="text-base shrink-0">{daraja_ikon}</span>
                    <span className="flex-1 min-w-0">
                      <span className="text-sm font-medium block truncate" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{t.nomi}</span>
                      <span className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{t.fan} · {t.kunlar_otgan}{__kbUi(" kun oldin")}{t.oxirgi_ball !== null ? __kbUi(` · ${t.oxirgi_ball}%`) : __kbUi("")}</span>
                    </span>
                    <ChevronRight size={16} className="shrink-0" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {haftalik && (haftalik.jami_mavzu > 0 || haftalik.ketma_ket_kun > 0) && (
          <div className="rounded-2xl p-4 bg-white border mb-1" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <p className="text-sm font-bold mb-3 flex items-center gap-1.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📊 Haftalik xulosa")}</p>
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="rounded-xl p-2.5 text-center" style={{ backgroundColor: "#FDF3E0" }}>
                <p className="text-lg font-bold" style={{ color: "#8A5A1C" }}>{haftalik.ketma_ket_kun > 0 ? __kbUi(`🔥${haftalik.ketma_ket_kun}`) : __kbUi("—")}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("kun ketma-ket")}</p>
              </div>
              <div className="rounded-xl p-2.5 text-center" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
                <p className="text-lg font-bold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{haftalik.jami_mavzu}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("mavzu (hafta)")}</p>
              </div>
              <div className="rounded-xl p-2.5 text-center" style={{ backgroundColor: "#EAF3DE" }}>
                <p className="text-lg font-bold" style={{ color: "#3B6D11" }}>{haftalik.jami_mavzu > 0 ? __kbUi(`${haftalik.ortacha_ball}%`) : __kbUi("—")}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("o'rtacha ball")}</p>
              </div>
            </div>
            {haftalik.yangi_mavzular_soni > 0 && (
              <p className="text-xs mb-1.5" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("⭐ Bu hafta ")}{haftalik.yangi_mavzular_soni}{__kbUi(" ta yangi mavzu: ")}<b>{__kbUi(haftalik.yangi_mavzular.join(", "))}</b>
              </p>
            )}
            {haftalik.zaif_mavzular.length > 0 && (
              <p className="text-xs" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("💪 Ko'proq e'tibor kerak: ")}<b>{__kbUi(haftalik.zaif_mavzular.map((z) => `${z.nomi} (${z.ball}%)`).join(", "))}</b>
              </p>
            )}
          </div>
        )}

        {davomat && davomat.jami_kun > 0 && (
          <div className="rounded-2xl p-4 bg-white border mb-1" style={{ borderColor: davomat.ketma_ket_kelmagan >= 2 ? "#E8A0A0" : "#E5E1D8" }}>
            <p className="text-sm font-bold mb-3 flex items-center gap-1.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📋 Davomat (oxirgi 30 kun)")}</p>
            {davomat.ketma_ket_kelmagan >= 2 && (
              <p className="text-xs font-medium mb-3" style={{ color: "#A32D2D" }}>⚠️ {davomat.ketma_ket_kelmagan}{__kbUi(" kun ketma-ket kelmagan")}</p>
            )}
            <div className="grid grid-cols-3 gap-2">
              <div className="rounded-xl p-2.5 text-center" style={{ backgroundColor: "#EAF3DE" }}>
                <p className="text-lg font-bold" style={{ color: "#3B6D11" }}>{davomat.keldi}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("keldi")}</p>
              </div>
              <div className="rounded-xl p-2.5 text-center" style={{ backgroundColor: "#FCEBEB" }}>
                <p className="text-lg font-bold" style={{ color: "#A32D2D" }}>{davomat.kelmadi}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("kelmadi")}</p>
              </div>
              <div className="rounded-xl p-2.5 text-center" style={{ backgroundColor: "#FDF3E0" }}>
                <p className="text-lg font-bold" style={{ color: "#8A5A1C" }}>{davomat.kechikdi}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("kechikdi")}</p>
              </div>
            </div>
          </div>
        )}

        {qiyinlikTahlili && qiyinlikTahlili.darajalar.length > 0 && (
          <div className="rounded-2xl p-4 bg-white border mb-1" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <p className="text-sm font-bold mb-3 flex items-center gap-1.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🎯 Qiyinlik darajasi bo'yicha natijam")}</p>
            <div className="space-y-2.5 mb-3">
              {qiyinlikTahlili.darajalar.map((d) => {
                const rangi = { oson: "#3B6D11", "o'rta": "#8A5A1C", qiyin: "#B0553A", murakkab: "#A32D2D" }[d.daraja] || "#8A8578";
                const fonRangi = { oson: "#EAF3DE", "o'rta": "#FDF3E0", qiyin: "#FBE4D8", murakkab: "#FCEBEB" }[d.daraja] || "#F0EDE5";
                return (
                  <div key={d.daraja}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-medium capitalize" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{d.daraja}</span>
                      <span style={{ color: rangi }}>{d.togri}/{d.jami} ({d.foiz}%)</span>
                    </div>
                    <div className="h-2 rounded-full overflow-hidden" style={{ backgroundColor: fonRangi }}>
                      <div className="h-full rounded-full" style={{ width: `${d.foiz}%`, backgroundColor: rangi }} />
                    </div>
                  </div>
                );
              })}
            </div>
            {qiyinlikTahlili.javob_turlari.length > 1 && (
              <div className="flex gap-2 pt-2 border-t" style={{ borderColor: "#F0EDE5" }}>
                {qiyinlikTahlili.javob_turlari.map((t) => (
                  <div key={t.turi} className="flex-1 rounded-xl p-2.5 text-center" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                    <p className="text-xs font-medium mb-0.5" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{t.turi === "write_answer" ? __kbUi("✍️ Yozma") : __kbUi("🔘 Tugmali")}</p>
                    <p className="text-sm font-bold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{t.foiz}%</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {bolaId && (
          <button onClick={() => setReaksiyaOyiniOchiq(true)}
            className="rounded-2xl p-4 bg-white border mb-1 flex items-center justify-between text-left" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <div>
              <p className="text-sm font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🎮 Reaksiya o'yini")}</p>
              <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Tezligingizni sinab ko'ring — qiziqarli sinov")}</p>
            </div>
            <ChevronRight size={18} style={{ color: "var(--ui-legacy-color-b0aa98, #B0AA98)" }} />
          </button>
        )}
        {reaksiyaOyiniOchiq && <ReaksiyaOyini token={token} bolaId={bolaId} onYopish={() => setReaksiyaOyiniOchiq(false)} />}

        {data.sinf_sozlanmagan ? (
          <div className="rounded-2xl p-6 text-center bg-white border mt-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <p className="text-sm font-medium mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Sinf sozlanmagan")}</p>
            <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Profilda sinf tanlangach, shu sinfning fan/mavzulari shu yerda ko'rinadi.")}</p>
          </div>
        ) : data.fanlar.length === 0 ? (
          <div className="rounded-2xl p-6 text-center bg-white border mt-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali birorta ham mavzu o'rganilmagan.")}</p>
          </div>
        ) : (
          data.fanlar.map((fan) => (
            <FanBolimi key={fan.nom} fan={fan} onBosildi={() => setYolFani({ fan: fan.nom, rang: fan.rang })} />
          ))
        )}

        {mengaTogaraklarim.length > 0 && (
          <div className="pt-2">
            <p className="text-sm font-semibold mb-2" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🔀 To'garak yo'llarim")}</p>
            <div className="space-y-2">
              {mengaTogaraklarim.map((t) => (
                <button key={t.id} onClick={() => setTogarakYoliId(t.id)}
                  className="w-full flex items-center justify-between px-4 py-3.5 rounded-xl bg-white border text-left"
                  style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                  <span>
                    <span className="text-sm font-medium block" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{t.nomi}</span>
                    <span className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{t.fan}{t.sinf ? __kbUi(` · ${t.sinf}-sinf`) : __kbUi("")}</span>
                  </span>
                  <ChevronRight size={18} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {yolFani && bolaId && <TalimYoli token={token} bolaId={bolaId} fan={yolFani.fan} rang={yolFani.rang} onYopish={() => setYolFani(null)} />}
      {togarakYoliId && bolaId && <TogarakYoli bolaId={bolaId} togarakId={togarakYoliId} onYopish={() => setTogarakYoliId(null)} />}
    </div>
  );
}

function TashkilotsizOquvchiBoshSahifa({ foydalanuvchi, bilimData, rang, onTest, onProfil }) {
  useKbInterfaceLocale();
  const fanlar = Array.isArray(bilimData?.fanlar) ? bilimData.fanlar : [];
  const urinishlar = Number(bilimData?.otilgan_mavzu || 0);
  const jamiMavzu = Number(bilimData?.jami_mavzu || 0);
  const umumiy = Number(bilimData?.umumiy_foiz || 0);
  const ism = String(foydalanuvchi?.full_name || "O‘quvchi").trim().split(/\s+/)[0];
  return <div className="px-4 md:px-6 py-5 max-w-5xl mx-auto">
    <section className="rounded-3xl p-5 md:p-7 text-white overflow-hidden relative" style={{ background: `linear-gradient(135deg,${rang},#183B5B)` }}>
      <div className="relative z-10 max-w-2xl">
        <div className="text-[11px] font-black uppercase tracking-[.14em] opacity-80">{__kbUi("Mustaqil ta’lim maydoni")}</div>
        <h2 className="text-2xl md:text-3xl font-black mt-2">{__kbUi("Salom, ")}{ism}{__kbUi(". Bilimingiz yo‘qolmaydi.")}</h2>
        <p className="text-sm mt-2 opacity-90">{__kbUi("Hali maktab yoki markaz ulanmagan. Siz hozirdanoq sinfingizni tanlab mavzularni takrorlashingiz, test yechishingiz va shaxsiy bilim xaritangizni yaratishingiz mumkin.")}</p>
        <div className="flex flex-wrap gap-2 mt-5">
          <button onClick={onTest} className="px-4 py-2.5 rounded-xl bg-white font-black text-sm" style={{ color: rang }}>{__kbUi("Bilimni tekshirish")}</button>
          <button onClick={onProfil} className="px-4 py-2.5 rounded-xl border border-white/40 bg-white/10 font-black text-sm text-white">{__kbUi("Sinf va profilni sozlash")}</button>
        </div>
      </div>
      <div className="absolute -right-10 -bottom-16 w-52 h-52 rounded-full bg-white/10" />
    </section>

    <div className="grid grid-cols-3 gap-2 md:gap-4 mt-4">
      {[["Bilim darajasi", `${umumiy}%`], ["O‘tilgan mavzu", urinishlar], ["Fanlar", fanlar.length]].map(([label,value]) => <div key={label} className="rounded-2xl border bg-white p-3 md:p-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}><div className="text-lg md:text-2xl font-black" style={{ color: rang }}>{value}</div><div className="text-[10px] md:text-xs mt-1" style={{ color: "var(--ui-legacy-color-7a8794, #7A8794)" }}>{__kbUi(label)}</div></div>)}
    </div>

    <section className="mt-4 rounded-3xl border bg-white p-4 md:p-5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
      <div className="flex items-start justify-between gap-3">
        <div><h3 className="font-black" style={{ color: "var(--ui-legacy-color-21384c, #21384C)" }}>{__kbUi("Tashkilotga ulanish")}</h3><p className="text-xs mt-1" style={{ color: "var(--ui-legacy-color-7a8794, #7A8794)" }}>{__kbUi("Maktab yoki markaz bergan rasmiy taklif kodini Profil bo‘limida kiriting. Ulangach jadval, o‘qituvchi topshiriqlari va tashkilot natijalari shu yerga qo‘shiladi.")}</p></div>
        <span className="text-2xl">🔗</span>
      </div>
      <button onClick={onProfil} className="mt-3 px-4 py-2.5 rounded-xl text-sm font-black text-white" style={{ background: rang }}>{__kbUi("Ulanish kodini kiritish")}</button>
    </section>


    <div className="grid md:grid-cols-2 gap-3 mt-4">
      <button onClick={onTest} className="rounded-2xl border bg-white p-4 text-left" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}><div className="text-xl">🧠</div><div className="font-black mt-2" style={{ color: "var(--ui-legacy-color-21384c, #21384C)" }}>{__kbUi("Boshlang‘ich diagnostika")}</div><div className="text-xs mt-1" style={{ color: "var(--ui-legacy-color-7a8794, #7A8794)" }}>{__kbUi("Sinf va fan bo‘yicha qisqa test. Natijadan zaif mavzular aniqlanadi.")}</div></button>
      <button onClick={onTest} className="rounded-2xl border bg-white p-4 text-left" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}><div className="text-xl">🔁</div><div className="font-black mt-2" style={{ color: "var(--ui-legacy-color-21384c, #21384C)" }}>{__kbUi("Bugungi takrorlash")}</div><div className="text-xs mt-1" style={{ color: "var(--ui-legacy-color-7a8794, #7A8794)" }}>{urinishlar ? __kbUi(`${urinishlar} ta o‘tilgan mavzudan navbatdagi takrorlashni boshlang.`) : __kbUi("Birinchi testni ishlang — tizim keyingi takrorlashlarni o‘zi rejalaydi.")}</div></button>
    </div>

    {jamiMavzu > 0 && <div className="mt-4 rounded-2xl p-3 text-xs font-bold" style={{ background: "#EEF6F1", color: "#2E6C55" }}>{__kbUi("Natijalar shu hisobda saqlanadi. Keyin maktab yoki markazga ulansangiz ham avvalgi ")}{jamiMavzu}{__kbUi(" ta mavzu tarixi yo‘qolmaydi.")}</div>}
  </div>;
}

function BilimMarkazi({
  token,
  data,
  bolaId,
  rang,
  viewer = "student",
  otaOnaUchun = false,
  analyticsCompact = false,
  onOpenTest = null,
  onOpenLesson = null,
}) {
  useKbInterfaceLocale();
  const [ichkiTab, setIchkiTab] = useState("tahlil");
  return (
    <div>
      {data && (
        <div className="px-5 pt-3 pb-2">
          <div className="grid grid-cols-2 gap-1 rounded-xl p-1" style={{ backgroundColor: "#EEEAE1" }}>
            <button onClick={() => setIchkiTab("tahlil")}
              className="rounded-lg py-2 text-xs font-semibold"
              style={ichkiTab === "tahlil"
                ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 4px rgba(0,0,0,.08)" }
                : { color: "#6F6859" }}><InterfaceText text={__kbUi("Tahlil")}/></button>
            <button onClick={() => setIchkiTab("talim_yoli")}
              className="rounded-lg py-2 text-xs font-semibold"
              style={ichkiTab === "talim_yoli"
                ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 4px rgba(0,0,0,.08)" }
                : { color: "#6F6859" }}><InterfaceText text={__kbUi("Ta'lim yo'li")}/></button>
          </div>
        </div>
      )}
      {ichkiTab === "talim_yoli" && data ? (
        <StudentLearningPathDashboard
          token={token}
          studentId={viewer === "student" ? null : bolaId}
          viewer={viewer}
          accent={rang}
          onOpenTest={onOpenTest}
          onOpenLesson={onOpenLesson}
        />
      ) : (
        <div className={analyticsCompact ? "px-5 pb-4" : ""}>
          <StudentAnalyticsDashboard
            token={token}
            studentId={viewer === "student" ? null : bolaId}
            viewer={viewer}
            accent={rang}
            compact={analyticsCompact}
            fallbackData={data}
          />
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// 4) TEST YECHISH
// ═══════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════
// 5) O'QITUVCHI — guruhlarim, baholash
// ═══════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════
// 7) ADMIN — Test shablon yuklab olish / import qilish
// ═══════════════════════════════════════════════════════════
function AdminTestlarTab({ token }) {
  useKbInterfaceLocale();
  return <AdminTestBrowser token={token} Tests={TestTab}/>;
}

function AdminTab({ token, oldindanTanlangan }) {
  useKbInterfaceLocale();
  // Shablonlar sahifasiga kirilganda hech qaysi ish oynasi o'z-o'zidan
  // ochilmaydi. Mavzular sahifasidan kelgan kodlar esa yo'qolmaydi: foydalanuvchi
  // keyin "Shablon"ni tanlaganda TestShablonBolimi'ga uzatiladi.
  const [bolim, setBolim] = useState(null); // null | "miya" | "test" | "topik" | ...
  const [testRejimi, setTestRejimi] = useState(null); // null | "shablon" | "import"

  const bolimniOch = (yangiBolim) => {
    setBolim(yangiBolim);
    setTestRejimi(null);
  };

  const testMenyusiniAlmashtir = () => {
    if (bolim === "test") {
      setBolim(null);
      setTestRejimi(null);
      return;
    }
    setBolim("test");
    setTestRejimi(null);
  };

  return (
    <div className="px-5 pt-6 pb-4 shablon-v79">
      <header className="shablon-hero">
        <span className="shablon-hero-icon" aria-hidden="true">🧩</span>
        <div>
          <h1><InterfaceText text={__kbUi("Shablonlar")}/></h1>
          <p>{__kbUi("Tartib: 1) mavzular ro‘yxati → 2) kitob darslari → 3) testlar. Hammasi DTS mavzu kodi orqali bog‘lanadi va o‘quvchining «O‘rganish» bo‘limida birga chiqadi.")}</p>
        </div>
      </header>
      <div className="grid gap-2.5 mb-5 sm:grid-cols-2 shablon-steps">
        {[
          ["topik", "📋 1. Mavzular ro‘yxati", "DTS mavzu kodlari va nomlari (topik shablon). Kitob darsi va testlar shu kodlarga ulanadi.", "#1B4B7A"],
          ["miya", "📘 2. Kitob darslari (AI miya)", "KITOB + MAVZULAR shabloni: tushuntirish, doska, rasm, misollar, «Tushunmadim». Nashrdan keyin dars xonasida chiqadi.", "#2D8B8B"],
          ["test", "🧪 3. Test shablon va import", "Mavzu kodi bo‘yicha savollar. Dars oxirida va «Testlar» bo‘limida chiqadi.", "#1B4B7A"],
          ["tushuntirish", "🤖 AI tushuntirishlar", "Kitob darsi bo‘lmagan mavzular uchun AI ustoz tushuntirishlari.", "#6E45A1"],
          ["sinov", "🧪 Sinov muhiti", "O‘zgarishlarni o‘quvchi ko‘zi bilan sinab ko‘rish.", "#C89B3C"],
        ].map(([key, title, hint, color]) => {
          const active = bolim === key;
          return (
            <button key={key} type="button" aria-pressed={active}
              {...(key === "test" ? { "aria-expanded": bolim === "test", "aria-controls": "test-shablon-import-tanlov" } : {})}
              onClick={() => (key === "test" ? testMenyusiniAlmashtir() : bolimniOch(key))}
              className={`shablon-step text-left rounded-2xl p-3.5 border ${active ? "is-active" : ""} ${key === "miya" ? "sm:col-span-2" : ""}`}
              style={active ? { "--step": color, backgroundColor: color, borderColor: color, color: "#fff" } : { "--step": color, backgroundColor: "#fff", borderColor: "#E5E1D8", color: "#2B2B2B" }}>
              <span className="block text-sm font-semibold">{__kbUi(title)}</span>
              <span className="block text-xs mt-1" style={{ opacity: .8 }}>{__kbUi(hint)}</span>
            </button>
          );
        })}
        {bolim === "test" && (
          <div id="test-shablon-import-tanlov" className="sm:col-span-2 grid grid-cols-2 gap-2 rounded-xl p-2"
            style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
            <button type="button" onClick={() => setTestRejimi("shablon")}
              className="py-2.5 rounded-xl font-semibold text-sm"
              style={testRejimi === "shablon"
                ? { backgroundColor: "#2D8B8B", color: "#fff" }
                : { backgroundColor: "#fff", color: "#1B4B7A", border: "1px solid #B7D3E8" }}>📄 <InterfaceText text={__kbUi("Shablon")}/></button>
            <button type="button" onClick={() => setTestRejimi("import")}
              className="py-2.5 rounded-xl font-semibold text-sm"
              style={testRejimi === "import"
                ? { backgroundColor: "#2D8B8B", color: "#fff" }
                : { backgroundColor: "#fff", color: "#1B4B7A", border: "1px solid #B7D3E8" }}>{__kbUi("📤 Import")}</button>
          </div>
        )}
      </div>

      {bolim === "miya" && (
        <CurriculumBoundary token={token} title={__kbUi("Kitob darslari: qaysi o‘quvchilar uchun?")}>
          <KitobMiyaBolimi token={token} fanTanlash />
        </CurriculumBoundary>
      )}
      {bolim === "test" && testRejimi === "shablon" && (
        <TestShablonBolimi key="shablon" token={token} oldindanTanlangan={oldindanTanlangan} mode="shablon" />
      )}
      {bolim === "test" && testRejimi === "import" && (
        <TestShablonBolimi key="import" token={token} oldindanTanlangan={oldindanTanlangan} mode="import" />
      )}
      {bolim === "topik" && <TopikShablonBolimi token={token} />}
      {bolim === "tushuntirish" && <TushuntirishBolimi token={token} />}
      {bolim === "sinov" && <SinovMuhitiBolimi token={token} />}
    </div>
  );
}

const ADMIN_ANDOZA_TILLARI = [["uz", "UZ · O‘zbek sinflari"], ["ru", "RU · Rus sinflari"], ["en", "EN · Ingliz sinflari"]];
function AdminMaktabMarkaziySozlamalari({ token, onOrtga }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [language, setLanguage] = useState("uz");
  const [approvalsByLanguage, setApprovalsByLanguage] = useState({});
  const [rowsByLanguage, setRowsByLanguage] = useState({});
  const [canonicalBySubject, setCanonicalBySubject] = useState({});
  const [rows, setRows] = useState([]);
  const [grade, setGrade] = useState(1);
  const [section, setSection] = useState("fanlar");
  const [approvals, setApprovals] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const days = ["", "Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"];
  const load = async () => {
    setLoading(true); setError("");
    try {
      const response = await fetch(`${API_BASE}/api/admin/maktab_markaziy_sozlamalari?token=${encodeURIComponent(token)}&talim_tili=${encodeURIComponent(language)}`, { cache: "no-store" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Markaziy sozlamani yuklab bo‘lmadi");
      setRows((data.qatorlar || []).map(item => ({ ...item, haftalik_soat: Number(item.haftalik_soat || 0) })));
      setApprovals(data.tasdiqlar || {});
      setApprovalsByLanguage(data.tasdiqlar_til_boyicha || {});
      setRowsByLanguage(data.til_boyicha || {});
      setCanonicalBySubject(data.fan_kanonik || {});
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };
  useEffect(() => { setMessage(""); load(); }, [token, language]);
  const current = rows.map((row, index) => ({ row, index })).filter(item => Number(item.row.sinf_darajasi) === grade);
  const update = (index, field, value) => setRows(old => old.map((row, i) => i === index ? { ...row, [field]: value } : row));
  const normalizeSubjectName = value => String(value || "").trim().toLocaleLowerCase("uz");
  const canonicalOf = subject => normalizeSubjectName(canonicalBySubject[subject] || canonicalBySubject[String(subject || "").trim()] || subject);
  const autoMethodDaysFromUz = () => {
    const uzRows = rowsByLanguage.uz || [];
    if (!uzRows.length) { setError("O‘zbek andozasi topilmadi — avval UZ metod kunlarini belgilang."); return; }
    const uzDayByCanonical = {};
    uzRows.forEach(row => { if (row.metod_kuni) uzDayByCanonical[canonicalOf(row.fan_nomi)] = Number(row.metod_kuni); });
    let matched = 0; let missed = [];
    const seen = new Set();
    setRows(old => old.map(row => {
      const day = uzDayByCanonical[canonicalOf(row.fan_nomi)];
      if (!seen.has(row.fan_nomi)) { seen.add(row.fan_nomi); if (day) matched += 1; else missed.push(row.fan_nomi); }
      return day ? { ...row, metod_kuni: day } : row;
    }));
    setError("");
    setMessage(`✅ ${matched} ta fanga o‘zbek andozasidagi metod kuni qo‘yildi${missed.length ? `; mos topilmagan: ${missed.slice(0, 5).join(", ")}${missed.length > 5 ? "..." : ""}` : ""}. Tekshirib “Saqlash va tasdiqlash”ni bosing.`);
  };
  const updateSubjectRule = (subject, field, value) => {
    const key = String(subject || "").trim().toLocaleLowerCase("uz");
    setRows(old => old.map(row => String(row.fan_nomi || "").trim().toLocaleLowerCase("uz") === key ? { ...row, [field]: value } : row));
  };
  const add = () => setRows(old => [...old, { sinf_darajasi: grade, fan_nomi: language === "ru" ? "Новый предмет" : language === "en" ? "New subject" : "Yangi fan", haftalik_soat: 1, metod_kuni: null, kunlik_max: 1 }]);
  const remove = index => setRows(old => old.filter((_, i) => i !== index));
  const save = async () => {
    setSaving(true); setMessage(""); setError("");
    try {
      const qatorlar = rows.map(row => ({
        sinf_darajasi: Number(row.sinf_darajasi), fan_nomi: String(row.fan_nomi || "").trim(),
        haftalik_soat: Number(row.haftalik_soat || 0), metod_kuni: row.metod_kuni ? Number(row.metod_kuni) : null,
        kunlik_max: Number(row.kunlik_max || 1),
      }));
      const response = await fetch(`${API_BASE}/api/admin/maktab_markaziy_sozlamalari?token=${encodeURIComponent(token)}`, {
        method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ talim_tili: language, qatorlar, bolim: section === "metod" ? "metod" : "fanlar", tasdiqlash: true }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Saqlab bo‘lmadi");
      setMessage(`✅ ${ADMIN_ANDOZA_TILLARI.find(([k]) => k === language)?.[1] || language}: ${section === "fanlar" ? "fanlar va o‘quv reja" : section === "yuklama" ? "o‘quv reja" : "metod kunlari"} tasdiqlandi. Shu tildagi sinflari bor maktablar avtomatik oladi.`);
      await load();
    } catch (e) { setError(e.message); }
    finally { setSaving(false); }
  };
  const tabs = [
    ["fanlar", "1. Fanlar", "1–11-sinf uchun tasdiqlangan fanlar"],
    ["yuklama", "2. O‘quv reja", "1–11-sinfda har fan necha soat o‘tiladi"],
    ["metod", "3. Metod kunlari", "Fan o‘qituvchilarining metod kuni"],
  ];
  const uniqueSubjects = Array.from(new Map(rows.map(row => [String(row.fan_nomi || "").trim().toLocaleLowerCase("uz"), row])).values()).sort((a, b) => String(a.fan_nomi).localeCompare(String(b.fan_nomi), "uz"));
  const approved = Boolean(approvals?.[section === "yuklama" ? "fanlar" : section]?.tasdiqlangan);
  return <div className="px-5 pt-6 pb-8">
    <button type="button" onClick={onOrtga} className="flex items-center gap-2 mb-4" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><ChevronLeft size={16}/>{__kbUi(" Muassasa turlari")}</button>
    <div className="rounded-3xl border bg-white p-5" style={{ borderColor: "#D8E2E8" }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div><span className="premium-eyebrow">{__kbUi("MUASSASA SOZLAMALARI · MAKTAB")}</span><h1 className="text-2xl font-black mt-1">{__kbUi("Maktablar uchun yagona andoza")}</h1><p className="text-sm mt-1" style={{ color: "#6F777B" }}>{__kbUi("Fanlar, o‘quv reja va metod kunlari bir-biriga bog‘langan. Maktab alohida o‘zgartirmagan bo‘lsa, tasdiqlangan andozani avtomatik oladi.")}</p></div>
        <span className="px-3 py-2 rounded-xl text-xs font-black" style={{ background: approved ? "#EAF7EF" : "#FFF2DB", color: approved ? "#28734B" : "#9A6718" }}>{approved ? __kbUi("✓ Tasdiqlangan") : __kbUi("Tasdiqlanmagan")}</span>
      </div>
      <div className="mt-5 p-3 rounded-2xl border" style={{ borderColor: "#D8E2E8", background: "#FBFCFD" }}>
        <p className="text-xs font-black mb-2" style={{ color: "#38505E" }}>{__kbUi("Andoza tili · har til alohida saqlanadi va tasdiqlanadi")}</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">{ADMIN_ANDOZA_TILLARI.map(([key, label]) => {
          const active = language === key;
          const ok = Boolean(approvalsByLanguage?.[key]?.fanlar?.tasdiqlangan);
          return <button key={key} type="button" disabled={saving} onClick={() => setLanguage(key)} className="text-left px-4 py-3 rounded-xl border" style={{ borderColor: active ? "#1B4B7A" : "#D8E2E8", background: active ? "#1B4B7A" : "#fff", color: active ? "#fff" : "#38505E" }}>
            <b className="block text-sm">{__kbUi(label)}</b>
            <small style={{ opacity: 0.85 }}>{ok ? __kbUi("✓ tasdiqlangan") : __kbUi("tasdiqlanmagan")}</small>
          </button>;
        })}</div>
        <p className="text-[11px] mt-2" style={{ color: "#6F777B" }}>{__kbUi("Rus yoki ingliz sinfi bor maktab uchun jadval chiqishi shu tildagi fanlar va soatlar tasdiqlanishiga bog‘liq. Bir tilni tahrirlash boshqasini o‘zgartirmaydi.")}</p>
      </div>
      {error && <div className="mt-4 rounded-xl p-3 text-sm" style={{ background: "#FDECEC", color: "#B83C3C" }}>{__kbUi(error)}</div>}
      {message && <div className="mt-4 rounded-xl p-3 text-sm" style={{ background: "#EAF7EF", color: "#28734B" }}>{message}</div>}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-5">{tabs.map(([key, title, text]) => <button key={key} onClick={() => { setSection(key); setMessage(""); setError(""); }} className="text-left p-4 rounded-2xl border" style={{ borderColor: section === key ? "#176B75" : "#D8E2E8", background: section === key ? "#EAF7F6" : "#fff" }}><b>{__kbUi(title)}</b><small className="block mt-1" style={{ color: "#6F777B" }}>{__kbUi(text)}</small></button>)}</div>
      {section !== "metod" && <div className="flex flex-wrap gap-2 mt-5">{Array.from({ length: 11 }, (_, i) => i + 1).map(item => <button key={item} onClick={() => setGrade(item)} className="px-3 py-2 rounded-xl text-xs font-black" style={{ background: grade === item ? "#1B4B7A" : "#EEF4F7", color: grade === item ? "#fff" : "#38505E" }}>{item}{__kbUi("-sinf")}</button>)}</div>}
      {section === "fanlar" && <><div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">{current.map(({ row, index }) => <div key={`${grade}-${index}`} className="flex gap-2 p-3 rounded-xl border"><input value={row.fan_nomi} onChange={e => update(index, "fan_nomi", e.target.value)} className="min-w-0 flex-1 p-2 rounded-lg border"/><button onClick={() => remove(index)} className="px-3 rounded-lg font-black" style={{ color: "#B83C3C", background: "#FDECEC" }}>×</button></div>)}</div><button onClick={add} className="mt-4 px-4 py-2.5 rounded-xl font-black" style={{ background: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>+ {grade}{__kbUi("-sinfga fan qo‘shish")}</button></>}
      {section === "yuklama" && <div className="mt-4 overflow-auto"><table className="min-w-[620px] w-full text-sm"><thead><tr className="text-left"><th className="p-3">{__kbUi("Tasdiqlangan fan")}</th><th>{__kbUi("Haftalik soat")}</th></tr></thead><tbody>{current.map(({ row, index }) => <tr key={`${grade}-${row.fan_nomi}`} className="border-t"><td className="p-3 font-bold">{row.fan_nomi}</td><td><input type="number" min="0" max="20" step="0.5" value={row.haftalik_soat} onChange={e => update(index, "haftalik_soat", e.target.value)} className="w-32 p-2 rounded-lg border"/></td></tr>)}</tbody><tfoot><tr className="border-t"><td className="p-3 font-black">{__kbUi("Jami")}</td><td className="font-black">{current.reduce((sum, item) => sum + Number(item.row.haftalik_soat || 0), 0)}{__kbUi(" soat")}</td></tr></tfoot></table></div>}
      {section === "metod" && language !== "uz" && <div className="mt-4 flex flex-wrap items-center gap-2 rounded-xl border p-3" style={{ borderColor: "#D8E2E8", background: "#F7FAFC" }}><button type="button" onClick={autoMethodDaysFromUz} disabled={saving || loading} className="px-3 py-2 rounded-lg text-xs font-black text-white disabled:opacity-50" style={{ background: "#1B4B7A" }}>{__kbUi("⚡ O‘zbek andozasiga moslab avto tanlash")}</button><span className="text-xs" style={{ color: "#6F777B" }}>{__kbUi("Har fan uchun o‘zbek andozasidagi metod kuni olinadi (Алгебра ↔ Algebra, Mathematics ↔ Matematika). Keyin “Saqlash va tasdiqlash”ni bosing.")}</span></div>}
      {section === "metod" && <div className="mt-4 overflow-auto"><table className="min-w-[620px] w-full text-sm"><thead><tr className="text-left"><th className="p-3">{__kbUi("Tasdiqlangan fan")}</th><th>{__kbUi("Metod kuni")}</th></tr></thead><tbody>{uniqueSubjects.map(row => <tr key={row.fan_nomi} className="border-t"><td className="p-3 font-bold">{row.fan_nomi}</td><td><select value={row.metod_kuni || ""} onChange={e => updateSubjectRule(row.fan_nomi, "metod_kuni", e.target.value || null)} className="w-44 p-2 rounded-lg border bg-white"><option value="">{__kbUi("Belgilanmagan")}</option>{days.slice(1).map((day, i) => <option key={day} value={i + 1}>{__kbUi(day)}</option>)}</select></td></tr>)}</tbody></table></div>}
      {!loading && section !== "metod" && !current.length && <div className="rounded-xl p-4 mt-3" style={{ background: "#FFF6E7", color: "#8A5A1C" }}>{__kbUi("Bu sinf uchun tasdiqlangan fan yo‘q.")}</div>}
      <div className="mt-5 p-4 rounded-2xl" style={{ background: "#F4F8FA" }}><p className="text-sm mb-3">{__kbUi("Tasdiqlashdan keyin bu bo‘lim alohida sozlama qilmagan barcha maktablarga ulanadi.")}</p><button onClick={save} disabled={saving || loading} className="px-5 py-3 rounded-xl text-white font-black" style={{ background: "#176B75" }}>{saving ? uiT("Saqlanmoqda…") : __kbUi("Saqlash va tasdiqlash")}</button></div>
    </div>
  </div>;
}

function AdminMuassasaSozlamalari({ token, onOrtga }) {
  useKbInterfaceLocale();
  const [type, setType] = useState(null);
  const types = [
    ["maktab", "🏫", "Maktab", "1–11-sinf fanlari, o‘quv reja va metod kunlari"],
    ["bogcha", "🧸", "Bog‘cha", "Bog‘cha uchun alohida markaziy andoza"],
    ["markaz", "🎓", "O‘quv markazi", "Markazlar uchun alohida markaziy andoza"],
    ["universitet", "🏛️", "Institut / universitet", "Institut sahifasi, muqova rasmi va muhim sanalar"],
  ];
  useEffect(() => registerPhoneBackHandler("admin-muassasa-settings", () => {
    if (!type) return false;
    setType(null);
    return true;
  }, 110), [type]);
  if (type === "maktab") return <AdminMaktabMarkaziySozlamalari token={token} onOrtga={() => setType(null)} />;
  if (type === "universitet") return <AdminInstitutTanlash token={token} apiBase={API_BASE} onBack={() => setType(null)} />;
  return <div className="px-5 pt-6 pb-8"><button type="button" onClick={onOrtga} className="flex items-center gap-2 mb-4"><ChevronLeft size={16}/><InterfaceText text={__kbUi(" Muassasalar")}/></button><div className="rounded-3xl border bg-white p-5"><span className="premium-eyebrow">{__kbUi("ADMIN MARKAZI")}</span><h1 className="text-2xl font-black mt-1">{__kbUi("Muassasa sozlamalari")}</h1><p className="text-sm mt-1" style={{ color: "#6F777B" }}>{__kbUi("Muassasa turini tanlang. Har bir tur o‘z sozlamasiga ega; ma’lumotlar bir-biriga aralashmaydi.")}</p><div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-5">{types.map(([key, icon, title, text]) => <button key={key} onClick={() => setType(key)} className="text-left p-5 rounded-2xl border"><span className="text-2xl">{__kbUi(icon)}</span><b className="block mt-2">{__kbUi(title)}</b><small style={{ color: "#6F777B" }}>{__kbUi(text)}</small></button>)}</div>{type && type !== "maktab" && type !== "universitet" && <div className="mt-4 p-4 rounded-xl" style={{ background: "#FFF6E7", color: "#8A5A1C" }}>{__kbUi("Bu muassasa turi uchun sozlama alohida yaratiladi. Hozir Maktab sozlamasi faol.")}</div>}</div></div>;
}

function AdminMuassasalarTab({ token }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [bolim, setBolim] = useState(null);
  const [yangiOchiq, setYangiOchiq] = useState(false);
  const [yangiTuri, setYangiTuri] = useState("maktab");
  const [hamyonUserId, setHamyonUserId] = useState("");
  const [hamyonMiqdori, setHamyonMiqdori] = useState(String(ORGANIZATION_ACTIVATION_PRICE_UZS));
  const [hamyonReference, setHamyonReference] = useState("");
  const [hamyonIzoh, setHamyonIzoh] = useState("");
  const [hamyonTasdiqlandi, setHamyonTasdiqlandi] = useState(false);
  const [hamyonJarayon, setHamyonJarayon] = useState(false);
  const [hamyonXato, setHamyonXato] = useState("");
  const [hamyonNatija, setHamyonNatija] = useState(null);
  const hamyonKalitiRef = useRef("");

  const turlar = [
    { kalit: "maktab", nom: "Maktablar", ikon: "🏫", izoh: "Mavjud maktablar ro'yxati va boshqaruvi" },
    { kalit: "bogcha", nom: "Bog'chalar", ikon: "🧸", izoh: "Mavjud bog'chalar ro'yxati va boshqaruvi" },
    { kalit: "markaz", nom: "O'quv markazlari", ikon: "🎓", izoh: "Mavjud markazlar ro'yxati va boshqaruvi" },
    { kalit: "universitet", nom: "Universitet / Institut", ikon: "🏛️", izoh: "Mavjud oliy ta'lim muassasalari" },
  ];

  useEffect(() => registerPhoneBackHandler("admin-muassasalar-section", () => {
    if (yangiOchiq) {
      setYangiOchiq(false);
      return true;
    }
    if (bolim) {
      setBolim(null);
      return true;
    }
    return false;
  }, 90), [bolim, yangiOchiq]);

  const hamyonMaydoniOzgardi = (setter) => (event) => {
    setter(event.target.value);
    hamyonKalitiRef.current = "";
    setHamyonTasdiqlandi(false);
    setHamyonXato("");
    setHamyonNatija(null);
  };

  const hamyonniToldirish = async () => {
    const userId = Number(hamyonUserId);
    const amountUzs = Number(hamyonMiqdori);
    if (!Number.isInteger(userId) || userId < 1) {
      setHamyonXato("To'g'ri user_id kiriting");
      return;
    }
    if (!Number.isInteger(amountUzs) || amountUzs < 1 || amountUzs > 100_000_000) {
      setHamyonXato("amount_uzs 1 dan 100 000 000 gacha bo'lishi kerak");
      return;
    }
    if (hamyonReference.trim().length < 3) {
      setHamyonXato("Audit uchun kamida 3 belgili reference kiriting");
      return;
    }
    if (!hamyonTasdiqlandi || hamyonJarayon) return;
    setHamyonJarayon(true);
    setHamyonXato("");
    setHamyonNatija(null);
    try {
      if (!hamyonKalitiRef.current) {
        hamyonKalitiRef.current = makeOrganizationIdempotencyKey(`admin-wallet-${userId}`);
      }
      const payload = buildAdminWalletCreditPayload({
        userId,
        amountUzs,
        reference: hamyonReference,
        note: hamyonIzoh,
        confirmed: hamyonTasdiqlandi,
        idempotencyKey: hamyonKalitiRef.current,
      });
      const data = await muassasaV17Sorov("/admin/hamyon-toldirish", token, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setHamyonNatija(data);
      hamyonKalitiRef.current = "";
      setHamyonTasdiqlandi(false);
      setHamyonReference("");
      setHamyonIzoh("");
    } catch (error) {
      setHamyonXato(organizationTrialErrorMessage(error.payload || error.message));
    } finally {
      setHamyonJarayon(false);
    }
  };

  if (bolim === "muassasa_sozlamalari") {
    return <AdminMuassasaSozlamalari token={token} onOrtga={() => setBolim(null)} />;
  }

  if (bolim) {
    return (
      <div className="px-5 pt-6 pb-4">
        <button type="button" onClick={() => setBolim(null)} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
          <span className="w-7 h-7 rounded-xl flex items-center justify-center" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} /></span><InterfaceText text={__kbUi("Muassasalar")}/></button>
        {bolim === "maktab" && <MaktablarBolimi token={token} />}
        {bolim === "markaz" && <MarkazlarBolimi token={token} />}
        {bolim === "bogcha" && <BogchalarBolimi token={token} />}
        {bolim === "universitet" && <UniversitetlarBolimi token={token} />}
      </div>
    );
  }

  return (
    <div className="admin-organizations px-5 pt-6 pb-4">
      <div className="admin-organizations__header">
        <div>
          <span className="premium-eyebrow">{__kbUi("ADMINISTRATOR MARKAZI")}</span>
          <h1><InterfaceText text={__kbUi("Muassasalar")}/></h1>
          <p>{__kbUi("Mavjud muassasalarni alohida boshqaring yoki yangi muassasa turini tanlang.")}</p>
        </div>
        <button type="button" onClick={() => setYangiOchiq(true)}>
          <Building2 size={17} />{__kbUi(" Yangi muassasa")}</button>
      </div>

      <div className="admin-organizations__section-title">
        <h2>{__kbUi("Mavjud muassasalar")}</h2>
        <p>{__kbUi("Turini tanlab, muassasalarning to'liq ro'yxati va boshqaruvini oching.")}</p>
      </div>
      <section className="admin-organizations__list" aria-label={__kbUi("Mavjud muassasa turlari")}>
        {turlar.map((tur) => (
          <button type="button" key={tur.kalit} onClick={() => setBolim(tur.kalit)}>
            <span>{__kbUi(tur.ikon)}</span>
            <div>
              <b>{__kbUi(tur.nom)}</b>
              <small>{__kbUi(tur.izoh)}</small>
            </div>
            <ChevronRight size={18} />
          </button>
        ))}
      </section>
      <section className="admin-organizations__section-title"><h2>{__kbUi("Muassasa sozlamalari")}</h2><p>{__kbUi("4 xil muassasa uchun bir-biridan ajratilgan markaziy sozlamalar.")}</p></section>
      <section className="admin-organizations__list">
        <button type="button" onClick={() => setBolim("muassasa_sozlamalari")}><span>⚙️</span><div><b>{__kbUi("Muassasa sozlamalari")}</b><small>{__kbUi("Maktab · bog‘cha · o‘quv markazi · institut/universitet")}</small></div><ChevronRight size={18}/></button>
      </section>

      <section className="admin-wallet-credit" aria-labelledby="admin-wallet-title">
        <div className="admin-wallet-credit__head">
          <span><Wallet size={18} /></span>
          <div>
            <h2 id="admin-wallet-title">{__kbUi("Tasdiqlangan hamyon to'ldirish")}</h2>
            <p>{__kbUi("To'lov provayderi hozircha ulanmagan. Bu blok pul qabul qilmaydi; administrator tashqarida tasdiqlangan to'lovni audit ma'lumoti bilan qo'lda kreditlaydi.")}</p>
          </div>
        </div>
        <div className="admin-wallet-credit__grid">
          <label className="org-trial-field">
            <span>{__kbUi("Foydalanuvchi ID · user_id")}</span>
            <input type="number" min="1" step="1" inputMode="numeric" value={hamyonUserId} onChange={hamyonMaydoniOzgardi(setHamyonUserId)} placeholder={__kbUi("Masalan: 1842")} />
          </label>
          <label className="org-trial-field">
            <span>{__kbUi("Miqdor · amount_uzs")}</span>
            <input type="number" min="1" max="100000000" step="1" inputMode="numeric" value={hamyonMiqdori} onChange={hamyonMaydoniOzgardi(setHamyonMiqdori)} />
          </label>
          <label className="org-trial-field">
            <span>{__kbUi("To'lov reference")}</span>
            <input value={hamyonReference} onChange={hamyonMaydoniOzgardi(setHamyonReference)} minLength={3} maxLength={160} placeholder={__kbUi("Chek, o'tkazma yoki ichki hujjat raqami")} />
          </label>
          <label className="org-trial-field">
            <span>{__kbUi("Izoh · note")}</span>
            <input value={hamyonIzoh} onChange={hamyonMaydoniOzgardi(setHamyonIzoh)} maxLength={240} placeholder={__kbUi("Ixtiyoriy audit izohi")} />
          </label>
        </div>
        {hamyonXato && <div className="org-trial-notice error" role="alert">{__kbUi(hamyonXato)}</div>}
        {hamyonNatija && (
          <div className="org-trial-notice success" role="status">{__kbUi("Hamyon to'ldirildi. Yangi balans: ")}{__kbUi(formatUzs(hamyonNatija.wallet?.balance_uzs ?? hamyonNatija.balance_uzs))}{hamyonNatija.reused ? __kbUi(" · avvalgi so'rov xavfsiz qaytarildi") : __kbUi("")}.
          </div>
        )}
        <label className="org-trial-checkbox charge">
          <input type="checkbox" checked={hamyonTasdiqlandi} onChange={(event) => setHamyonTasdiqlandi(event.target.checked)} />
          <span><b>{__kbUi(formatUzs(Number(hamyonMiqdori) || 0))}</b>{__kbUi(" summani user_id ")}<b>{hamyonUserId || __kbUi("—")}</b>{__kbUi(" hamyoniga qo'shishni aniq tasdiqlayman. Reference audit jurnalida saqlanadi.")}</span>
        </label>
        <button type="button" className="admin-wallet-credit__submit" disabled={!hamyonTasdiqlandi || hamyonJarayon} onClick={hamyonniToldirish}>
          {hamyonJarayon ? <><Loader2 size={17} className="animate-spin" />{__kbUi(" Kreditlanmoqda...")}</> : __kbUi("Tasdiqlangan mablag'ni hamyonga qo'shish")}
        </button>
      </section>

      {yangiOchiq && (
        <div className="org-trial-modal-backdrop" role="presentation" onMouseDown={() => setYangiOchiq(false)}>
          <section className="org-trial-modal" role="dialog" aria-modal="true" aria-labelledby="admin-new-organization-title" onMouseDown={(event) => event.stopPropagation()}>
            <button type="button" className="org-trial-modal__close" onClick={() => setYangiOchiq(false)} aria-label={uiT("Yopish")}><X size={18} /></button>
            <span className="premium-eyebrow">{__kbUi("YANGI MUASSASA")}</span>
            <h2 id="admin-new-organization-title">{__kbUi("Qaysi turdagi muassasa?")}</h2>
            <p>{__kbUi("Davlat va ommaviy muassasalar faqat administrator oqimi orqali yaratiladi.")}</p>
            <label className="org-trial-field">
              <span>{__kbUi("Muassasa turi")}</span>
              <select value={yangiTuri} onChange={(event) => setYangiTuri(event.target.value)}>
                {turlar.map((tur) => <option key={tur.kalit} value={tur.kalit}>{__kbUi(tur.nom)}</option>)}
              </select>
            </label>
            <div className="org-trial-modal__actions">
              <button type="button" className="secondary" onClick={() => setYangiOchiq(false)}><InterfaceText text={__kbUi("Bekor qilish")}/></button>
              <button type="button" className="primary" onClick={() => { setBolim(yangiTuri); setYangiOchiq(false); }}><InterfaceText text={__kbUi("Davom etish")}/></button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

const SINF_HARFLARI = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"];

const LAVOZIM_NOMLARI = {
  direktor: "Direktor",
  zam_direktor_uquv: "O'quv ishlari bo'yicha direktor o'rinbosari",
  zam_direktor_tarbiya: "Ma'naviy-ma'rifiy ishlar bo'yicha direktor o'rinbosari",
  psixolog: "Psixolog",
  kotib: "Kotib",
  fan_oqituvchisi: "Fan o'qituvchisi",
  markaz_direktor: "Markaz direktori",
  administrator: "Administrator",
  bogcha_direktor: "Bog'cha direktori",
  bogcha_zam: "Bog'cha zam direktori",
  bogcha_opa: "Bog'cha opasi (tarbiyachi)",
};

function MaktabQidiruvi({ tanlanganMaktab, onTanla }) {
  useKbInterfaceLocale();
  const [nomi, setNomi] = useState("");
  const [natijalar, setNatijalar] = useState([]);
  const [qidirilmoqda, setQidirilmoqda] = useState(false);

  useEffect(() => {
    if (nomi.trim().length < 2) { setNatijalar([]); return; }
    setQidirilmoqda(true);
    const kechiktirish = setTimeout(() => {
      fetch(`${API_BASE}/api/maktab_qidir?nomi=${encodeURIComponent(nomi.trim())}`)
        .then((r) => r.json())
        .then((d) => { setNatijalar(d.natijalar || []); setQidirilmoqda(false); })
        .catch(() => setQidirilmoqda(false));
    }, 400);
    return () => clearTimeout(kechiktirish);
  }, [nomi]);

  if (tanlanganMaktab) {
    return (
      <div className="flex items-center justify-between px-3.5 py-2.5 rounded-xl border mb-3" style={{ borderColor: "#1B4B7A", backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
        <span className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>🏫 {tanlanganMaktab.nomi}</span>
        <button onClick={() => onTanla(null)} className="text-xs font-medium" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("✕ O'zgartirish")}</button>
      </div>
    );
  }

  return (
    <div className="mb-3">
      <input type="text" value={nomi} onChange={(e) => setNomi(e.target.value)}
        placeholder={__kbUi("Maktabingiz nomini yozing (ro'yxatda bo'lsa, aniqroq bo'ladi)...")}
        className="w-full px-3.5 py-2.5 rounded-xl border text-sm"
        style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
      {qidirilmoqda && <p className="text-xs mt-1.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Qidirilmoqda...")}</p>}
      {natijalar.length > 0 && (
        <div className="mt-1.5 space-y-1">
          {natijalar.map((m) => (
            <button key={m.id} onClick={() => { onTanla(m); setNomi(""); setNatijalar([]); }}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-left" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
              <span className="text-sm" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{m.nomi}</span>
              <span className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi([m.viloyat, m.tuman].filter(Boolean).join(", "))}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function SinovMuhitiBolimi({ token }) {
  useKbInterfaceLocale();
  const [yaratilmoqda, setYaratilmoqda] = useState(false);
  const [natija, setNatija] = useState(null);
  const [xato, setXato] = useState("");
  const [kirilmoqdaId, setKirilmoqdaId] = useState(null);

  const muhitYarat = async () => {
    setYaratilmoqda(true); setXato(""); setNatija(null);
    try {
      const res = await fetch(`${API_BASE}/api/admin/sinov_muhit_yarat?token=${encodeURIComponent(token)}`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setNatija(data);
    } catch (e) {
      setXato(e.message);
    } finally { setYaratilmoqda(false); }
  };

  const shuHisobBilanKir = async (hisobUserId) => {
    setKirilmoqdaId(hisobUserId);
    try {
      const res = await fetch(`${API_BASE}/api/admin/sifatida_kirish?token=${encodeURIComponent(token)}&user_id=${hisobUserId}`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      window.open(`/kabinet?token=${encodeURIComponent(data.token)}`, "_blank");
    } catch (e) {
      setXato(e.message);
    } finally { setKirilmoqdaId(null); }
  };

  return (
    <div>
      <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "#F5DFA3", backgroundColor: "#FFFDF7" }}>
        <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🧪 Sinov muhiti")}</p>
        <p className="text-xs mb-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bitta bosishda — sinov maktabi, bog'chasi, markazi va universiteti, ularning direktori/o'qituvchisi/ opasi/professori va o'quvchilari — HAMMASI soxta, tayyor holda yaratiladi. Google orqali kirish shart emas — har biriga \"Bu sifatida kirish\" bilan darhol kirasiz.")}</p>
        <button onClick={muhitYarat} disabled={yaratilmoqda}
          className="w-full py-3 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#C89B3C", opacity: yaratilmoqda ? 0.7 : 1 }}>
          {yaratilmoqda ? __kbUi("Yaratilmoqda...") : __kbUi("🧪 Yangi sinov muhitini yaratish")}
        </button>
        {xato && <p className="text-sm mt-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
      </div>

      {natija && (
        <div className="rounded-2xl p-5 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("✅ Tayyor — ")}{natija.hisoblar.length}{__kbUi(" ta sinov hisobi")}</p>
          <p className="text-xs mb-4" style={{ color: "#8A5A1C" }}>{natija.izoh}</p>
          <div className="space-y-2">
            {natija.hisoblar.map((h) => (
              <div key={h.user_id} className="rounded-xl p-3 flex items-center justify-between" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                <div>
                  <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{h.full_name}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{h.izoh}</p>
                </div>
                <button onClick={() => shuHisobBilanKir(h.user_id)} disabled={kirilmoqdaId === h.user_id}
                  className="text-xs font-semibold px-3 py-1.5 rounded-lg text-white shrink-0" style={{ backgroundColor: "#1B4B7A", opacity: kirilmoqdaId === h.user_id ? 0.7 : 1 }}>
                  {kirilmoqdaId === h.user_id ? __kbUi("...") : __kbUi("→ Shu sifatida kirish")}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function DirektorQidiruvi({ token, tanlanganDirektor, onTanla, onYangiIsm }) {
  useKbInterfaceLocale();
  const [ism, setIsm] = useState("");
  const [natijalar, setNatijalar] = useState([]);
  const [qidirilmoqda, setQidirilmoqda] = useState(false);

  useEffect(() => {
    if (ism.trim().length < 2) { setNatijalar([]); return; }
    setQidirilmoqda(true);
    const kechiktirish = setTimeout(() => {
      fetch(`${API_BASE}/api/admin/foydalanuvchi_qidir?token=${encodeURIComponent(token)}&ism=${encodeURIComponent(ism.trim())}`)
        .then((r) => r.json())
        .then((d) => { setNatijalar(d.natijalar || []); setQidirilmoqda(false); })
        .catch(() => setQidirilmoqda(false));
    }, 400);
    return () => clearTimeout(kechiktirish);
  }, [ism, token]);

  if (tanlanganDirektor) {
    return (
      <div className="flex items-center justify-between px-3.5 py-2.5 rounded-xl border mb-3" style={{ borderColor: "#1B4B7A", backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
        <span className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>👤 {tanlanganDirektor.full_name}</span>
        <button onClick={() => onTanla(null)} className="text-xs font-medium" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("✕ O'zgartirish")}</button>
      </div>
    );
  }

  return (
    <div className="mb-3">
      <input type="text" value={ism} onChange={(e) => { setIsm(e.target.value); onYangiIsm?.(e.target.value); }}
        placeholder={__kbUi("Rahbar F.I.Sh.ini yozing yoki ro‘yxatdan tanlang...")}
        className="w-full px-3.5 py-2.5 rounded-xl border text-sm"
        style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
      {qidirilmoqda && <p className="text-xs mt-1.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Qidirilmoqda...")}</p>}
      {natijalar.length > 0 && (
        <div className="mt-1.5 space-y-1">
          {natijalar.map((n) => (
            <button key={n.user_id} onClick={() => { onTanla(n); onYangiIsm?.(""); setIsm(""); setNatijalar([]); }}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-left" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
              <span className="text-sm" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{n.full_name}</span>
              <span className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi(n.role)}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function SinfGuruhBoshqaruvi({ token, sinf, fanlar = [], onSaved, ochiq = false, onToggle, yangilashVersiyasi = 0 }) {
  useKbInterfaceLocale();
  const [tizimlar, setTizimlar] = useState([]);
  const [azolar, setAzolar] = useState([]);
  const [boshqaraOladi, setBoshqaraOladi] = useState(false);
  const [yuklangan, setYuklangan] = useState(false);
  const [yuklanmoqda, setYuklanmoqda] = useState(false);
  const [saqlanmoqda, setSaqlanmoqda] = useState(false);
  const [tanlanganlar, setTanlanganlar] = useState(() => new Set());
  const [guruhNomi, setGuruhNomi] = useState("");
  const [xabar, setXabar] = useState("");
  const [xato, setXato] = useState("");

  const turMalumoti = {
    gender: { nomi: "O‘g‘il / Qiz", izoh: "Jismoniy tarbiya va texnologiya uchun", rang: "#EAF4DF" },
    alphabet: { nomi: "Alifbo 1 / 2", izoh: "Til va informatika uchun", rang: "#EAF1F7" },
    manual: { nomi: "Mustaqil guruhlar", izoh: "O‘quvchilarni o‘zingiz belgilaysiz", rang: "#FFF5E2" },
  };

  const tizimlarniYukla = async (majburiy = false) => {
    if (yuklangan && !majburiy) return;
    setYuklanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/maktab/sinf_guruh_tizimlari?token=${encodeURIComponent(token)}&sinf_id=${sinf.id}`);
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Guruhlarni yuklab bo‘lmadi");
      setTizimlar(data.tizimlar || []);
      setAzolar(data.azolar || []);
      setBoshqaraOladi(Boolean(data.boshqara_oladi));
      setYuklangan(true);
    } catch (error) {
      setXato(error.message);
    } finally {
      setYuklanmoqda(false);
    }
  };

  useEffect(() => {
    setYuklangan(false);
    setTizimlar([]);
    tizimlarniYukla(true);
  }, [sinf.id, token, yangilashVersiyasi]);

  const ochibYop = () => {
    onToggle?.();
    if (!ochiq) tizimlarniYukla();
  };

  const tizimniAlmashtir = async (turi) => {
    if (saqlanmoqda || !boshqaraOladi) return;
    const mavjud = tizimlar.find((tizim) => tizim.turi === turi);
    setSaqlanmoqda(true); setXato(""); setXabar("");
    try {
      const res = await fetch(`${API_BASE}/api/maktab/sinf_guruh_tizimi`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, sinf_id: sinf.id, turi, faol: !mavjud, fanlar: mavjud?.fanlar || [] }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Guruhlash tizimini saqlab bo‘lmadi");
      setTizimlar(data.tizimlar || []);
      setTanlanganlar(new Set());
      setXabar(mavjud ? `✅ ${turMalumoti[turi].nomi} vaqtincha o‘chirildi; tarkibi saqlandi.` : `✅ ${turMalumoti[turi].nomi} qo‘shildi. Boshqa tizimlar saqlandi.`);
      onSaved?.();
      await tizimlarniYukla(true);
    } catch (error) {
      setXato(error.message);
    } finally {
      setSaqlanmoqda(false);
    }
  };

  const fanTanlashniAlmashtir = async (tizim, fan) => {
    if (saqlanmoqda || !boshqaraOladi) return;
    const yangiFanlar = (tizim.fanlar || []).includes(fan)
      ? (tizim.fanlar || []).filter((nom) => nom !== fan)
      : [...(tizim.fanlar || []), fan];
    setSaqlanmoqda(true); setXato(""); setXabar("");
    try {
      const res = await fetch(`${API_BASE}/api/maktab/sinf_guruh_tizimi`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, sinf_id: sinf.id, turi: tizim.turi, faol: true, fanlar: yangiFanlar }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Fan birikmasini saqlab bo‘lmadi");
      setTizimlar(data.tizimlar || []);
      setXabar("✅ Fan–guruh birikmasi saqlandi.");
    } catch (error) {
      setXato(error.message);
    } finally {
      setSaqlanmoqda(false);
    }
  };

  const belgilashniAlmashtir = (userId) => setTanlanganlar((avvalgi) => {
    const yangi = new Set(avvalgi);
    if (yangi.has(userId)) yangi.delete(userId); else yangi.add(userId);
    return yangi;
  });

  const barchasiniAlmashtir = () => setTanlanganlar((avvalgi) =>
    avvalgi.size === azolar.length ? new Set() : new Set(azolar.map((azo) => azo.user_id)));

  const manualTizim = tizimlar.find((tizim) => tizim.turi === "manual");
  const genderTizim = tizimlar.find((tizim) => tizim.turi === "gender");

  const jinsniSaqla = async (amal) => {
    if (!tanlanganlar.size) { setXato("Kamida bitta o‘quvchini belgilang"); return; }
    setSaqlanmoqda(true); setXato(""); setXabar("");
    try {
      const res = await fetch(`${API_BASE}/api/maktab/sinf_azolarini_guruhla`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, sinf_id: sinf.id, user_ids: [...tanlanganlar], amal }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Jins belgisini saqlab bo‘lmadi");
      setTanlanganlar(new Set());
      setXabar(`✅ ${data.yangilangan || 0} ta o‘quvchining jinsi belgilandi; O‘g‘il/Qiz guruhi qayta hisoblandi.`);
      await tizimlarniYukla(true);
      onSaved?.();
    } catch (error) {
      setXato(error.message);
    } finally {
      setSaqlanmoqda(false);
    }
  };

  const mustaqilGuruhniSaqla = async (tozalash = false) => {
    if (!manualTizim || !tanlanganlar.size) { setXato("Kamida bitta o‘quvchini belgilang"); return; }
    if (!tozalash && guruhNomi.trim().length < 2) { setXato("Mustaqil guruh nomini yozing"); return; }
    setSaqlanmoqda(true); setXato(""); setXabar("");
    try {
      const res = await fetch(`${API_BASE}/api/maktab/sinf_mustaqil_guruh`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, sinf_id: sinf.id, tizim_id: manualTizim.id, user_ids: [...tanlanganlar], guruh_nomi: guruhNomi.trim() || null, tozalash }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Mustaqil guruhni saqlab bo‘lmadi");
      setTizimlar(data.tizimlar || []);
      setTanlanganlar(new Set());
      setXabar(tozalash ? "✅ Tanlangan o‘quvchilar mustaqil guruhdan chiqarildi." : `✅ ${data.yangilangan || 0} ta o‘quvchi “${guruhNomi.trim()}” guruhiga qo‘yildi.`);
      onSaved?.();
    } catch (error) {
      setXato(error.message);
    } finally {
      setSaqlanmoqda(false);
    }
  };

  const jinsNomi = (jins) => {
    const kalit = String(jins || "").toLocaleLowerCase("uz").replace(/[’']/g, "");
    if (["ogil", "erkak", "male", "boy"].includes(kalit)) return "O‘g‘il";
    if (["qiz", "ayol", "female", "girl"].includes(kalit)) return "Qiz";
    return "Jinsi belgilanmagan";
  };

  const azoGuruhMatni = (userId) => tizimlar.flatMap((tizim) =>
    (tizim.azolar || []).filter((azo) => Number(azo.user_id) === Number(userId)).map((azo) => `${turMalumoti[tizim.turi]?.nomi || tizim.nomi}: ${azo.guruh_nomi}`));

  return (
    <div className="mt-2 border-t pt-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
      <button type="button" onClick={ochibYop} className="w-full flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg text-xs font-semibold" style={{ backgroundColor: ochiq ? "#DDEBF4" : tizimlar.length ? "#EAF4DF" : "#fff", color: tizimlar.length ? "#315F18" : "#1B4B7A", border: `1px solid ${tizimlar.length ? "#9FC47F" : "#E5E1D8"}` }}>
        <span>{tizimlar.length ? __kbUi(`✅ Guruhga bo‘lingan · ${tizimlar.length} ta faol`) : __kbUi("👥 Guruhga bo‘lish")}</span><span>{ochiq ? __kbUi("▲ Yopish") : __kbUi("▼ Ochish")}</span>
      </button>
      {ochiq && <div className="mt-2 rounded-xl border p-3" style={{ backgroundColor: "var(--ui-legacy-background-fff, #fff)", borderColor: "#B9CCDC", contentVisibility: "auto", containIntrinsicSize: "1px 520px" }}>
        <p className="text-[11px] mb-3" style={{ color: "#6F6859" }}>{__kbUi("Bitta sinfda 2 ta yoki uchala usulni ham bir vaqtda belgilash mumkin. Bittasini belgilash boshqasini o‘chirmaydi; har biri alohida saqlanadi.")}</p>
        {yuklanmoqda ? <div className="py-6"><Loader2 size={18} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div> : <>
          <div className="grid sm:grid-cols-3 gap-2">
            {Object.entries(turMalumoti).map(([turi, malumot]) => {
              const tizim = tizimlar.find((item) => item.turi === turi);
              return <label key={turi} className="rounded-xl border p-3 text-left cursor-pointer" style={{ backgroundColor: tizim ? malumot.rang : "#fff", borderColor: tizim ? "#1B4B7A" : "#E5E1D8", opacity: boshqaraOladi ? 1 : 0.72 }}>
                <span className="flex items-start gap-2.5"><input type="checkbox" checked={Boolean(tizim)} disabled={saqlanmoqda || !boshqaraOladi} onChange={() => tizimniAlmashtir(turi)} className="mt-0.5" /><span className="min-w-0 flex-1"><span className="flex items-center justify-between gap-2"><b className="text-xs" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(malumot.nomi)}</b><span className="text-xs font-bold" style={{ color: tizim ? "#3B6D11" : "#A39D8E" }}>{tizim ? __kbUi("✓ FAOL") : __kbUi("BELGILASH")}</span></span><small className="block mt-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi(malumot.izoh)}</small></span></span>
              </label>;
            })}
          </div>

          {tizimlar.map((tizim) => <div key={tizim.id} className="mt-3 rounded-xl border p-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", backgroundColor: "#FCFBF8" }}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <b className="text-xs" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{turMalumoti[tizim.turi]?.nomi || tizim.nomi}</b>
              <div className="flex flex-wrap gap-1.5">{(tizim.guruhlar || []).map((guruh) => <span key={guruh.guruh_kaliti} className="px-2 py-1 rounded-full text-[10px]" style={{ backgroundColor: "var(--ui-legacy-background-fff, #fff)", color: "var(--ui-legacy-color-5a5648, #5A5648)", border: "1px solid #E5E1D8" }}>{guruh.guruh_nomi}: {guruh.soni}</span>)}</div>
            </div>
            {fanlar.length > 0 && <details className="mt-2">
              <summary className="text-[11px] cursor-pointer font-semibold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Fanlarga bog‘lash (ixtiyoriy) · ")}{(tizim.fanlar || []).length}{__kbUi(" ta")}</summary>
              <div className="flex flex-wrap gap-1.5 mt-2">{fanlar.map((fan) => {
                const tanlangan = (tizim.fanlar || []).includes(fan);
                return <button key={fan} type="button" disabled={saqlanmoqda || !boshqaraOladi} onClick={() => fanTanlashniAlmashtir(tizim, fan)} className="px-2 py-1 rounded-lg text-[10px]" style={{ backgroundColor: tanlangan ? "#1B4B7A" : "#fff", color: tanlangan ? "#fff" : "#5A5648", border: "1px solid #D9D4C8" }}>{tanlangan ? __kbUi("✓ ") : __kbUi("")}{fan}</button>;
              })}</div>
            </details>}
          </div>)}

          {(manualTizim || genderTizim) && boshqaraOladi && <div className="mt-3 rounded-xl border p-3" style={{ borderColor: "#D9D4C8" }}>
            <div className="flex items-center justify-between gap-2 mb-2">
              <button type="button" onClick={barchasiniAlmashtir} disabled={!azolar.length} className="px-2.5 py-1.5 rounded-lg text-[11px] font-semibold" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{tanlanganlar.size === azolar.length && azolar.length ? __kbUi("Tanlovni tozalash") : __kbUi("Barchasini belgilash")}</button>
              <span className="text-[11px] font-semibold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{tanlanganlar.size}/{azolar.length}{__kbUi(" tanlandi")}</span>
            </div>
            {!azolar.length ? <p className="text-xs py-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bu sinfda hali o‘quvchi yo‘q.")}</p> : <div className="max-h-64 overflow-y-auto rounded-lg border divide-y" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              {azolar.map((azo) => {
                const belgilar = azoGuruhMatni(azo.user_id);
                return <label key={azo.user_id} className="flex items-center gap-2.5 px-3 py-2 cursor-pointer" style={{ backgroundColor: tanlanganlar.has(azo.user_id) ? "#F1F7FB" : "#fff", borderColor: "#F0ECE3" }}>
                  <input type="checkbox" checked={tanlanganlar.has(azo.user_id)} onChange={() => belgilashniAlmashtir(azo.user_id)} />
                  <span className="flex-1 min-w-0"><b className="block text-xs truncate" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{azo.full_name}</b><small className="block truncate" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi(jinsNomi(azo.jins))}{belgilar.length ? __kbUi(` · ${belgilar.join(" · ")}`) : __kbUi(" · Guruh belgilanmagan")}</small></span>
                </label>;
              })}
            </div>}
            {genderTizim && <div className="grid grid-cols-2 gap-2 mt-3">
              <button type="button" onClick={() => jinsniSaqla("boys")} disabled={saqlanmoqda || !tanlanganlar.size} className="px-3.5 py-2 rounded-lg text-xs font-bold" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)", opacity: saqlanmoqda || !tanlanganlar.size ? 0.55 : 1 }}>{__kbUi("Tanlanganlar — O‘g‘il")}</button>
              <button type="button" onClick={() => jinsniSaqla("girls")} disabled={saqlanmoqda || !tanlanganlar.size} className="px-3.5 py-2 rounded-lg text-xs font-bold" style={{ backgroundColor: "#F7EAF1", color: "#A8527A", opacity: saqlanmoqda || !tanlanganlar.size ? 0.55 : 1 }}>{__kbUi("Tanlanganlar — Qiz")}</button>
            </div>}
            {manualTizim && <div className="grid sm:grid-cols-[1fr_auto_auto] gap-2 mt-3">
              <input value={guruhNomi} onChange={(event) => setGuruhNomi(event.target.value)} placeholder={__kbUi("Mustaqil guruh nomi, masalan: Kuchli guruh")} maxLength={50} className="px-3 py-2 rounded-lg border text-xs" style={{ borderColor: "#D9D4C8" }} />
              <button type="button" onClick={() => mustaqilGuruhniSaqla(false)} disabled={saqlanmoqda || !tanlanganlar.size} className="px-3.5 py-2 rounded-lg text-xs font-bold text-white" style={{ backgroundColor: "#1B4B7A", opacity: saqlanmoqda || !tanlanganlar.size ? 0.55 : 1 }}>{__kbUi("Guruhga qo‘yish")}</button>
              <button type="button" onClick={() => mustaqilGuruhniSaqla(true)} disabled={saqlanmoqda || !tanlanganlar.size} className="px-3.5 py-2 rounded-lg text-xs font-bold" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "#B0553A", opacity: saqlanmoqda || !tanlanganlar.size ? 0.55 : 1 }}>{__kbUi("Guruhdan chiqarish")}</button>
            </div>}
          </div>}
          {!boshqaraOladi && <p className="text-[11px] mt-3 p-2.5 rounded-lg" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Ko‘rish mumkin. O‘zgartirish faqat admin yoki o‘quv ishlari zavuchiga ruxsat etilgan.")}</p>}
        </>}
        {xato && <p className="text-xs mt-2" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
        {xabar && <p className="text-xs mt-2" style={{ color: "#3B6D11" }}>{xabar}</p>}
      </div>}
    </div>
  );
}

// SAMTM APP V22.48 — mavjud maktab va yangi maktab oqimlari qat'iy ajratilgan.
function v2248AdminMaktabniNormallashtir(maktab) {
  if (!maktab || typeof maktab !== "object") return null;
  const id = [
    maktab.id,
    maktab.maktab_id,
    maktab.school_id,
    maktab.legacy_maktab_id,
    maktab.external_id,
  ].map((value) => Number(value)).find((value) => Number.isInteger(value) && value > 0);
  if (!id) return null;
  return {
    ...maktab,
    id,
    maktab_id: id,
    nomi: maktab.nomi || maktab.maktab_nomi || maktab.muassasa_nomi || `Maktab #${id}`,
  };
}

function MaktablarBolimi({ token }) {
  useKbInterfaceLocale();
  const [maktablar, setMaktablar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [formOchiq, setFormOchiq] = useState(false);
  const [tanlanganMaktab, setTanlanganMaktab] = useState(null); // maktab obyekti | null
  const [sozlamalarOchiq, setSozlamalarOchiq] = useState(false);
  const [rejaOchiq, setRejaOchiq] = useState(false);
  const [maktabOchishXatosi, setMaktabOchishXatosi] = useState("");

  const mavjudMaktabniOch = (maktab) => {
    const tozaMaktab = v2248AdminMaktabniNormallashtir(maktab);
    setFormOchiq(false);
    setSozlamalarOchiq(false);
    setRejaOchiq(false);
    if (!tozaMaktab) {
      setTanlanganMaktab(null);
      setMaktabOchishXatosi("Mavjud maktabning haqiqiy ID raqami serverdan kelmadi. Yangi maktab oynasi ochilmadi; sahifani yangilab yana tanlang.");
      return;
    }
    setMaktabOchishXatosi("");
    setTanlanganMaktab(tozaMaktab);
  };

  const maktablarniYukla = () => {
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/admin/maktablar?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => { setMaktablar(d.maktablar || []); setYuklanmoqda(false); })
      .catch(() => setYuklanmoqda(false));
  };

  useEffect(() => {
    // Maktablar bo‘limi har safar ochilganda avval mavjud maktablar
    // ro‘yxati ko‘rinsin. Yaratish oynasi faqat foydalanuvchi
    // “+ Yangi maktab” tugmasini bosgandagina ochiladi.
    setFormOchiq(false);
    maktablarniYukla();
  }, [token]);

  if (tanlanganMaktab) {
    if (rejaOchiq) {
      return <RejalashtirishBolimi token={token} maktabId={tanlanganMaktab.id} onOrtga={() => setRejaOchiq(false)} />;
    }
    if (sozlamalarOchiq) {
      return <MaktabTafsiloti
        token={token}
        maktab={tanlanganMaktab}
        onOrtga={() => { setSozlamalarOchiq(false); maktablarniYukla(); }}
      />;
    }
    return (
      <React.Suspense fallback={<div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>}>
        <SchoolWorkspace
          key={`admin-school-${tanlanganMaktab.id}`}
          token={token}
          apiBase={API_BASE}
          initialWorkspace={{
            ...tanlanganMaktab,
            turi: "maktab",
            muassasa_id: tanlanganMaktab.id,
            maktab_id: tanlanganMaktab.id,
            existing_only: true,
            muassasa_nomi: tanlanganMaktab.nomi,
            nomi: tanlanganMaktab.nomi,
            lavozim: "direktor",
          }}
          onBack={() => {
            setFormOchiq(false);
            setTanlanganMaktab(null);
            setSozlamalarOchiq(false);
            setRejaOchiq(false);
            maktablarniYukla();
          }}
          onLegacy={() => setSozlamalarOchiq(true)}
          onRejalashtirish={() => setRejaOchiq(true)}
          adminPreview={true}
          initialView="dashboard"
        />
      </React.Suspense>
    );
  }

  return (
    <div>
      <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <div className="flex items-center justify-between mb-1">
          <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>🏫 <InterfaceText text={__kbUi("Maktablar")}/></p>
          <button type="button" onClick={() => {
            setTanlanganMaktab(null);
            setSozlamalarOchiq(false);
            setMaktabOchishXatosi("");
            setFormOchiq((ochiq) => !ochiq);
          }} className="text-xs font-semibold px-3.5 py-1.5 rounded-full" style={{ backgroundColor: "#1B4B7A", color: "#fff" }}>
            {formOchiq ? __kbUi("✕ Yopish") : __kbUi("+ Yangi maktab")}
          </button>
        </div>
        <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bino va xonalarni ommaviy yarating, so‘ng 1–11-sinflarning parallel sonini alohida kiriting. 50–100 ta sinf bir bosishda hisoblanadi.")}</p>
      </div>

      {maktabOchishXatosi && <div className="rounded-xl border px-4 py-3 mb-3 text-sm font-semibold" style={{ borderColor: "#D67A72", backgroundColor: "#FCECEC", color: "#A54242" }}>{__kbUi(maktabOchishXatosi)}</div>}

      {formOchiq && !tanlanganMaktab && (
        <React.Suspense fallback={<div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>}>
          <AdminSchoolWizard
            token={token}
            apiBase={API_BASE}
            regions={VILOYATLAR}
            districtsByRegion={HUDUDLAR}
            onCancel={() => setFormOchiq(false)}
            onCreated={(school, response) => {
              const yangiMaktab = v2248AdminMaktabniNormallashtir(school)
                || v2248AdminMaktabniNormallashtir(response?.school)
                || v2248AdminMaktabniNormallashtir(response?.maktab)
                || v2248AdminMaktabniNormallashtir(response);
              setFormOchiq(false);
              setSozlamalarOchiq(false);
              if (yangiMaktab) {
                setMaktabOchishXatosi("");
                setTanlanganMaktab(yangiMaktab);
              } else {
                setTanlanganMaktab(null);
                setMaktabOchishXatosi("Maktab yaratildi, ammo server uning ID raqamini qaytarmadi. Ro‘yxat yangilandi; mavjud maktabni qayta tanlang.");
              }
              maktablarniYukla();
            }}
          />
        </React.Suspense>
      )}

      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : maktablar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali maktab qo'shilmagan.")}</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {maktablar.map((m) => (
            <button type="button" key={m.id ?? m.maktab_id ?? m.external_id ?? m.nomi} onClick={() => mavjudMaktabniOch(m)}
              className="w-full text-left rounded-xl p-4 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{m.maktab_raqami ? __kbUi(`${m.maktab_raqami}-sonli ${m.nomi}`) : m.nomi}</p>
                <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
              </div>
              <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
                {[m.viloyat, m.tuman].filter(Boolean).join(", ") || __kbUi("Hudud ko'rsatilmagan")} · {m.smena_soni}{__kbUi(" smenali")}</p>
              <p className="text-xs mt-1" style={{ color: m.direktor_ismi ? "#3B6D11" : "#B0553A" }}>
                {m.direktor_ismi ? __kbUi(`👤 Direktor: ${m.direktor_ismi}`) : __kbUi("⚠️ Direktor hali belgilanmagan")}
              </p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function SinfAsosiyTahriri({ token, sinf, ochiq, onToggle, onSaved }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [harf, setHarf] = useState(sinf.harf || "A");
  const [smena, setSmena] = useState(Number(sinf.smena || 1));
  const [bino, setBino] = useState(sinf.bino || "");
  const [xona, setXona] = useState(sinf.xona || "");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    setHarf(sinf.harf || "A"); setSmena(Number(sinf.smena || 1));
    setBino(sinf.bino || ""); setXona(sinf.xona || "");
  }, [sinf.id, sinf.harf, sinf.smena, sinf.bino, sinf.xona]);
  const save = async () => {
    setSaving(true); setMessage(""); setError("");
    try {
      const response = await fetch(`${API_BASE}/api/admin/maktab_sinf_tahrirla`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, sinf_id: sinf.id, harf, smena: Number(smena), bino: bino.trim() || null, xona: xona.trim() || null }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Sinf ma’lumotini saqlab bo‘lmadi");
      setMessage(`✅ ${data.sinf?.sinf || sinf.sinf}-${data.sinf?.harf || harf} yangilandi.`);
      onSaved?.();
    } catch (e) { setError(e.message); }
    finally { setSaving(false); }
  };
  return <div className="mt-2 border-t pt-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
    <button type="button" onClick={onToggle} className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-bold" style={{ background: ochiq ? "#EAF1F7" : "#fff", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}><span>{__kbUi("✏️ Harf · smena · xona")}</span><span>{ochiq ? __kbUi("Yopish ▲") : __kbUi("O‘zgartirish ▼")}</span></button>
    {ochiq && <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 mt-3 p-3 rounded-xl" style={{ background: "var(--ui-legacy-background-fff, #fff)" }}>
      <label className="text-xs font-bold">{__kbUi("Sinf harfi")}<input value={harf} maxLength={8} onChange={e => setHarf(e.target.value)} placeholder={__kbUi("A yoki А")} className="block w-full mt-1 p-2.5 rounded-lg border font-normal"/></label>
      <label className="text-xs font-bold">{__kbUi("Smena")}<select value={smena} onChange={e => setSmena(Number(e.target.value))} className="block w-full mt-1 p-2.5 rounded-lg border bg-white font-normal"><option value={1}>{__kbUi("1-smena")}</option><option value={2}>{__kbUi("2-smena")}</option></select></label>
      <label className="text-xs font-bold">{__kbUi("Bino")}<input value={bino} onChange={e => setBino(e.target.value)} placeholder={__kbUi("Masalan: Asosiy bino")} className="block w-full mt-1 p-2.5 rounded-lg border font-normal"/></label>
      <label className="text-xs font-bold">{__kbUi("Xona")}<input value={xona} onChange={e => setXona(e.target.value)} placeholder={__kbUi("Masalan: 101")} className="block w-full mt-1 p-2.5 rounded-lg border font-normal"/></label>
      <div className="sm:col-span-2 xl:col-span-4 flex flex-wrap items-center gap-3"><button type="button" disabled={saving || !String(harf).trim()} onClick={save} className="px-4 py-2.5 rounded-xl text-xs font-black text-white" style={{ background: "#087F8C", opacity: saving ? .6 : 1 }}>{saving ? uiT("Saqlanmoqda...") : __kbUi("Sinf ma’lumotini saqlash")}</button>{message && <span className="text-xs font-bold" style={{ color: "#28734B" }}>{message}</span>}{error && <span className="text-xs font-bold" style={{ color: "#B0553A" }}>❌ {__kbUi(error)}</span>}</div>
    </div>}
  </div>;
}

function MaktabTafsiloti({ token, maktab, onOrtga }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [boshSahifa, setBoshSahifa] = useState(false);
  const [workspaceStartView, setWorkspaceStartView] = useState("dashboard");
  const [fanBosqichiOchiq, setFanBosqichiOchiq] = useState(false);
  const [ochiqSinfDarajasi, setOchiqSinfDarajasi] = useState(1);
  const [dtsSinfFanlari, setDtsSinfFanlari] = useState({});
  const [sinfFanlari, setSinfFanlari] = useState({});
  const [yangiSinfFani, setYangiSinfFani] = useState({});
  const [importlanmoqda, setImportlanmoqda] = useState(false);
  const [xato, setXato] = useState("");
  const [importXabari, setImportXabari] = useState("");
  const [sinflar, setSinflar] = useState([]);
  const [sinflarYuklanmoqda, setSinflarYuklanmoqda] = useState(true);
  const [ochiqSinfGuruhId, setOchiqSinfGuruhId] = useState(null);
  const [ochiqSinfTahrirId, setOchiqSinfTahrirId] = useState(null);
  const [tanlanganGuruhSinflari, setTanlanganGuruhSinflari] = useState(() => new Set());
  const [ommaviyGuruhTurlari, setOmmaviyGuruhTurlari] = useState(() => new Set(["alphabet"]));
  const [ommaviyGuruhSaqlanmoqda, setOmmaviyGuruhSaqlanmoqda] = useState(false);
  const [ommaviyGuruhXabar, setOmmaviyGuruhXabar] = useState("");
  const [guruhYangilashVersiyasi, setGuruhYangilashVersiyasi] = useState(0);
  const [pulli, setPulli] = useState(maktab.pulli || false);
  const [oylikTolov, setOylikTolov] = useState(maktab.oylik_tolov ? String(maktab.oylik_tolov) : "");
  const [tolovSaqlanmoqda, setTolovSaqlanmoqda] = useState(false);
  const [fanKatalogi, setFanKatalogi] = useState([]);
  const [tanlanganFanlar, setTanlanganFanlar] = useState([]);
  const [saqlanganFanlar, setSaqlanganFanlar] = useState([]);
  const [fanlarYuklanmoqda, setFanlarYuklanmoqda] = useState(true);
  const [fanlarSaqlanmoqda, setFanlarSaqlanmoqda] = useState(false);
  const [fanXato, setFanXato] = useState("");
  const [fanXabar, setFanXabar] = useState("");
  const [yangiFanNomi, setYangiFanNomi] = useState("");

  const fanApiXatosi = (detail, fallback) => {
    if (typeof detail === "string" && detail.trim()) return detail;
    if (Array.isArray(detail)) return detail.map(item => item?.msg || JSON.stringify(item)).join("; ");
    if (detail && typeof detail === "object") {
      const message = detail.message || detail.detail || detail.error;
      const errorId = detail.error_id ? ` (xato kodi: ${detail.error_id})` : "";
      return `${message || fallback}${errorId}`;
    }
    return fallback;
  };

  const sinfFanKaliti = (nom) => {
    const kalit = String(nom || "")
    .normalize("NFKD")
    .toLocaleLowerCase("uz")
    .replace(/[ʻʼ’`´]/g, "'")
    .replace(/[^a-z0-9а-яёқғҳў' ]/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
    // TTS, eski maktab sozlamasi va admin andozasida bir fan turlicha
    // yozilgan bo‘lsa ham bitta fan hisoblanadi.
    if (/^informatika( va axborot texnologiyalari)?$/.test(kalit)) return "informatika";
    if (/^tabiiy fan(lar)?( science)?$/.test(kalit)) return "tabiiy fan";
    if (/^musiqa( madaniyati)?$/.test(kalit)) return "musiqa";
    if (/^ona tili( va yozuv)?$/.test(kalit)) return "ona tili";
    if (/^o'qish savodxonligi( va alifbe)?$/.test(kalit)) return "o'qish savodxonligi";
    if (/^chaqiruvga qadar boshlang'ich tayyorgarlik$/.test(kalit) || kalit === "chqbt") return "chqbt";
    if (/^texn[ao]logiya o?'?g'?il( bolalar)?$/.test(kalit)) return "texnologiya o'g'il";
    if (/^texn[ao]logiya qizlar$/.test(kalit)) return "texnologiya qizlar";
    return kalit;
  };

  const takrorsizSinfFanlari = (fanlar, asosiyFanlar = []) => {
    const asosiyNomlar = new Map();
    asosiyFanlar.forEach((fan) => {
      const kalit = sinfFanKaliti(fan);
      if (kalit && !asosiyNomlar.has(kalit)) asosiyNomlar.set(kalit, fan);
    });
    const natija = new Map();
    fanlar.forEach((fan) => {
      const kalit = sinfFanKaliti(fan);
      if (kalit && !natija.has(kalit)) natija.set(kalit, asosiyNomlar.get(kalit) || fan);
    });
    return [...natija.values()];
  };

  const sinflarniYukla = (sokin = false) => {
    if (!sokin) setSinflarYuklanmoqda(true);
    fetch(`${API_BASE}/api/admin/maktab_sinflari?token=${encodeURIComponent(token)}&maktab_id=${maktab.id}`)
      .then((r) => r.json())
      .then((d) => { setSinflar(d.sinflar || []); setSinflarYuklanmoqda(false); })
      .catch(() => setSinflarYuklanmoqda(false));
  };

  const guruhSinfiniTanlash = (sinfId) => setTanlanganGuruhSinflari((avvalgi) => {
    const yangi = new Set(avvalgi);
    if (yangi.has(sinfId)) yangi.delete(sinfId); else yangi.add(sinfId);
    return yangi;
  });

  const ommaviyGuruhTuriniTanlash = (turi) => setOmmaviyGuruhTurlari((avvalgi) => {
    const yangi = new Set(avvalgi);
    if (yangi.has(turi)) yangi.delete(turi); else yangi.add(turi);
    return yangi;
  });

  const tanlanganSinflarniGuruhlash = async () => {
    if (!tanlanganGuruhSinflari.size) return setOmmaviyGuruhXabar("Avval guruhlanadigan sinflarni ptichka bilan tanlang.");
    if (!ommaviyGuruhTurlari.size) return setOmmaviyGuruhXabar("1/2 guruh yoki O‘g‘il/Qiz turidan kamida bittasini tanlang.");
    setOmmaviyGuruhSaqlanmoqda(true); setOmmaviyGuruhXabar("");
    try {
      const vazifalar = [];
      const mavjudTizimlar = new Map();
      await Promise.all([...tanlanganGuruhSinflari].map(async (sinfId) => {
        const res = await fetch(`${API_BASE}/api/maktab/sinf_guruh_tizimlari?token=${encodeURIComponent(token)}&sinf_id=${sinfId}`);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || "Sinfning mavjud guruhlarini o‘qib bo‘lmadi");
        mavjudTizimlar.set(sinfId, data.tizimlar || []);
      }));
      tanlanganGuruhSinflari.forEach((sinfId) => ommaviyGuruhTurlari.forEach((turi) => {
        const mavjud = (mavjudTizimlar.get(sinfId) || []).find((tizim) => tizim.turi === turi);
        vazifalar.push(fetch(`${API_BASE}/api/maktab/sinf_guruh_tizimi`, {
          method: "PUT", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token, sinf_id: sinfId, turi, faol: true, fanlar: mavjud?.fanlar || [] }),
        }).then(async (res) => {
          const data = await res.json().catch(() => ({}));
          if (!res.ok) throw new Error(data.detail || "Guruhlashni saqlab bo‘lmadi");
          return data;
        }));
      }));
      await Promise.all(vazifalar);
      const sinfSoni = tanlanganGuruhSinflari.size;
      const turlar = [...ommaviyGuruhTurlari].map((turi) => turi === "alphabet" ? "1/2 guruh" : "O‘g‘il/Qiz").join(" va ");
      setOmmaviyGuruhXabar(`✅ ${sinfSoni} ta sinfga ${turlar} qo‘llandi.`);
      setGuruhYangilashVersiyasi((qiymat) => qiymat + 1);
      sinflarniYukla(true);
    } catch (error) {
      setOmmaviyGuruhXabar(`❌ ${error.message}`);
    } finally {
      setOmmaviyGuruhSaqlanmoqda(false);
    }
  };
  useEffect(sinflarniYukla, [token, maktab.id]);

  const fanlarniYukla = () => {
    setFanlarYuklanmoqda(true); setFanXato("");
    fetch(`${API_BASE}/api/admin/maktab_fan_sozlamalari?token=${encodeURIComponent(token)}&maktab_id=${maktab.id}`)
      .then(async (r) => {
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(fanApiXatosi(d.detail, "Fanlarni yuklab bo'lmadi"));
        return d;
      })
      .then((d) => {
        const markaziy = d.dts_sinf_fanlari || {};
        const saqlangan = d.sinf_fanlari || {};
        const tozaMarkaziy = {};
        const tozaSaqlangan = {};
        for (let daraja = 1; daraja <= 11; daraja += 1) {
          const kalit = String(daraja);
          tozaMarkaziy[kalit] = takrorsizSinfFanlari(markaziy[kalit] || []);
          tozaSaqlangan[kalit] = takrorsizSinfFanlari(saqlangan[kalit] || [], tozaMarkaziy[kalit]);
        }
        setFanKatalogi(d.fanlar || []);
        setTanlanganFanlar(d.tanlangan_fanlar || []);
        setSaqlanganFanlar(d.tanlangan_fanlar || []);
        setDtsSinfFanlari(tozaMarkaziy);
        setSinfFanlari(tozaSaqlangan);
        setFanlarYuklanmoqda(false);
      })
      .catch((e) => { setFanXato(e.message); setFanlarYuklanmoqda(false); });
  };

  const sinfFaniniAlmashtir = (daraja, fan) => {
    const kalit = String(daraja);
    setSinfFanlari((avvalgi) => {
      const royxat = avvalgi[kalit] || [];
      const fanKaliti = sinfFanKaliti(fan);
      const tanlangan = royxat.some((nom) => sinfFanKaliti(nom) === fanKaliti);
      return {
        ...avvalgi,
        [kalit]: tanlangan
          ? royxat.filter((nom) => sinfFanKaliti(nom) !== fanKaliti)
          : takrorsizSinfFanlari([...royxat, fan], dtsSinfFanlari[kalit] || []),
      };
    });
  };

  const sinfgaYangiFanQosh = (daraja) => {
    const kalit = String(daraja);
    const fan = String(yangiSinfFani[kalit] || "").trim().replace(/\s+/g, " ");
    if (fan.length < 2) return;
    setSinfFanlari((avvalgi) => ({
      ...avvalgi,
      [kalit]: (avvalgi[kalit] || []).some((nom) => sinfFanKaliti(nom) === sinfFanKaliti(fan))
        ? avvalgi[kalit]
        : takrorsizSinfFanlari([...(avvalgi[kalit] || []), fan], dtsSinfFanlari[kalit] || []),
    }));
    setYangiSinfFani((avvalgi) => ({ ...avvalgi, [kalit]: "" }));
  };

  const sinfFanlariniSaqla = async () => {
    setFanlarSaqlanmoqda(true); setFanXato(""); setFanXabar("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/maktab_fan_sozlamalari`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, maktab_id: maktab.id, fanlar: [], sinf_fanlari: sinfFanlari }),
      });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(fanApiXatosi(d.detail, "Sinf fanlarini saqlab bo‘lmadi"));
      setSinfFanlari(d.sinf_fanlari || sinfFanlari);
      setTanlanganFanlar(d.tanlangan_fanlar || []);
      setSaqlanganFanlar(d.tanlangan_fanlar || []);
      setFanXabar("✅ 1–11-sinflarning fanlari saqlandi.");
    } catch (e) { setFanXato(e.message); }
    finally { setFanlarSaqlanmoqda(false); }
  };
  useEffect(fanlarniYukla, [token, maktab.id]);

  const fanTanlashniAlmashtir = (fanNomi) => {
    setFanXabar("");
    setTanlanganFanlar((avvalgi) => avvalgi.includes(fanNomi)
      ? avvalgi.filter((nom) => nom !== fanNomi)
      : [...avvalgi, fanNomi]);
  };

  const yangiFanQosh = () => {
    const toza = yangiFanNomi.trim().replace(/\s+/g, " ");
    if (toza.length < 2) { setFanXato("Yangi fan nomini kiriting"); return; }
    const mavjud = fanKatalogi.find((fan) => fan.nomi.toLocaleLowerCase("uz") === toza.toLocaleLowerCase("uz"));
    const nomi = mavjud?.nomi || toza;
    if (!mavjud) setFanKatalogi((avvalgi) => [...avvalgi, { nomi, manba: "Maktab qo‘shgan" }]);
    setTanlanganFanlar((avvalgi) => avvalgi.includes(nomi) ? avvalgi : [...avvalgi, nomi]);
    setYangiFanNomi(""); setFanXato(""); setFanXabar("Yangi fan tanlovga qo‘shildi. Endi saqlang.");
  };

  const fanlarniSaqla = async () => {
    if (!tanlanganFanlar.length) { setFanXato("Kamida bitta maktab fanini tanlang"); return; }
    setFanlarSaqlanmoqda(true); setFanXato(""); setFanXabar("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/maktab_fan_sozlamalari`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, maktab_id: maktab.id, fanlar: tanlanganFanlar }),
      });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(d.detail || "Fanlarni saqlab bo'lmadi");
      setTanlanganFanlar(d.tanlangan_fanlar || []);
      setSaqlanganFanlar(d.tanlangan_fanlar || []);
      setFanXabar(`✅ ${d.tanlangan_fanlar?.length || 0} ta fan saqlandi. Endi aqlli shablonni olishingiz mumkin.`);
    } catch (e) {
      setFanXato(e.message);
    } finally {
      setFanlarSaqlanmoqda(false);
    }
  };

  const fanlarOzgargan = JSON.stringify([...tanlanganFanlar].sort()) !== JSON.stringify([...saqlanganFanlar].sort());
  const fanlarTayyor = saqlanganFanlar.length > 0 && !fanlarOzgargan;

  const parolniTashla = async (sinfId) => {
    await fetch(`${API_BASE}/api/admin/sinf_parolini_tashla?token=${encodeURIComponent(token)}&sinf_id=${sinfId}`, { method: "PUT" });
    sinflarniYukla();
  };

  const tolovSozlashniSaqla = async () => {
    setTolovSaqlanmoqda(true);
    try {
      await fetch(`${API_BASE}/api/admin/maktab_tolov_sozlash`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, maktab_id: maktab.id, pulli, oylik_tolov: pulli ? parseInt(oylikTolov, 10) || null : null }),
      });
    } finally { setTolovSaqlanmoqda(false); }
  };

  const shablonYukla = () => {
    if (!fanlarTayyor) { setFanXato("Avval maktab fanlarini tanlab saqlang"); return; }
    const cacheBuster = Date.now();
    window.open(`${API_BASE}/api/admin/xodim_shablon?token=${encodeURIComponent(token)}&maktab_id=${maktab.id}&_=${cacheBuster}`, "_blank", "noopener,noreferrer");
  };

  const faylTanlandi = async (e) => {
    const fayl = e.target.files[0];
    if (!fayl) return;
    if (!fanlarTayyor) {
      setXato("Avval maktab fanlarini tanlab saqlang");
      e.target.value = "";
      return;
    }
    setImportlanmoqda(true); setXato(""); setImportXabari("");
    try {
      const formData = new FormData();
      formData.append("fayl", fayl);
      const res = await fetch(`${API_BASE}/api/admin/xodim_import?token=${encodeURIComponent(token)}&maktab_id=${maktab.id}`, {
        method: "POST", body: formData,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Xato");
      }
      // Parollar ekranga chiqarilmaydi — to'g'ridan-to'g'ri Word hujjat qilib yuklab olinadi.
      const blob = await res.blob();
      const dlUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = dlUrl; a.download = "xodimlar_kirish_kodlari.docx";
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(dlUrl);
      setImportXabari("✅ Import yakunlandi — kirish kodlari Word fayl qilib yuklab olindi.");
      sinflarniYukla();
      setBoshSahifa(true);
    } catch (e) {
      setXato(e.message);
    } finally {
      setImportlanmoqda(false);
      e.target.value = "";
    }
  };

  if (boshSahifa) {
    return (
      <SchoolWorkspace
        token={token}
        apiBase={API_BASE}
        initialWorkspace={{ muassasa_id: maktab.id, muassasa_nomi: maktab.nomi, lavozim: "direktor" }}
        onBack={() => setBoshSahifa(false)}
        onLegacy={() => setBoshSahifa(false)}
        adminPreview={true}
        initialView={workspaceStartView}
      />
    );
  }

  return (
    <div>
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("Maktab bosh sahifasiga qaytish")}</button>
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-4">
        <div>
          <h1 className="text-lg font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{maktab.maktab_raqami ? __kbUi(`${maktab.maktab_raqami}-sonli ${maktab.nomi}`) : maktab.nomi}</h1>
          <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
            {[maktab.viloyat, maktab.tuman].filter(Boolean).join(", ") || __kbUi("Hudud ko'rsatilmagan")} · {maktab.smena_soni}{__kbUi(" smenali")}</p>
        </div>
        <button onClick={() => { setWorkspaceStartView("dashboard"); setBoshSahifa(true); }} className="px-4 py-2.5 rounded-xl text-sm font-bold text-white shadow-sm" style={{ background: "linear-gradient(135deg,#1B4B7A,#0F7C82)" }}>{__kbUi("🏫 Maktab bosh sahifasi")}</button>
      </div>
      <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <p className="text-sm font-semibold mb-3" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("💳 To'lov sozlamalari")}</p>
        <div className="flex gap-2 mb-3">
          <button onClick={() => setPulli(false)}
            className="flex-1 py-2.5 rounded-xl border text-sm font-semibold"
            style={!pulli ? { backgroundColor: "#1B4B7A", color: "#fff", borderColor: "#1B4B7A" } : { backgroundColor: "#fff", color: "#5A5648", borderColor: "#E5E1D8" }}>{__kbUi("Bepul (davlat)")}</button>
          <button onClick={() => setPulli(true)}
            className="flex-1 py-2.5 rounded-xl border text-sm font-semibold"
            style={pulli ? { backgroundColor: "#1B4B7A", color: "#fff", borderColor: "#1B4B7A" } : { backgroundColor: "#fff", color: "#5A5648", borderColor: "#E5E1D8" }}>{__kbUi("Pulli (xususiy)")}</button>
        </div>
        {pulli && (
          <>
            <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Oylik to'lov (so'm)")}</label>
            <input type="number" value={oylikTolov} onChange={(e) => setOylikTolov(e.target.value)}
              placeholder={__kbUi("masalan: 500000")}
              className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          </>
        )}
        <button onClick={tolovSozlashniSaqla} disabled={tolovSaqlanmoqda}
          className="w-full py-2.5 rounded-xl font-semibold text-sm" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)", opacity: tolovSaqlanmoqda ? 0.7 : 1 }}>
          {tolovSaqlanmoqda ? uiT("Saqlanmoqda...") : uiT("Saqlash")}
        </button>
      </div>

      <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "#BFD5AA" }}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("2-bosqich — 1–11-sinflarga fanlarni biriktirish")}</p><p className="text-xs mt-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Har bir sinfda super-admin sozlagan fanlar avtomatik chiqadi. Keraksizini olib tashlang yoki faqat shu sinfga yangi fan qo‘shing. O‘quv reja fanlari va boshlang‘ich soatlari shu tanlov hamda admin andozasidan olinadi.")}</p></div>
          <button type="button" onClick={() => setFanBosqichiOchiq((ochiq) => !ochiq)} className="px-4 py-2.5 rounded-xl text-sm font-bold text-white" style={{ backgroundColor: "#1B4B7A" }}>{fanBosqichiOchiq ? __kbUi("✕ Fanlarni yopish") : __kbUi("1–11-sinf fanlarini tanlash →")}</button>
        </div>
        {fanBosqichiOchiq && <div className="mt-4 border-t pt-4" style={{ borderColor: "#DDE8D4" }}>
          <div className="flex flex-wrap gap-2 mb-4">{Array.from({ length: 11 }, (_, i) => i + 1).map((daraja) => <button key={daraja} type="button" onClick={() => setOchiqSinfDarajasi(daraja)} className="px-3 py-2 rounded-xl text-xs font-bold" style={{ backgroundColor: ochiqSinfDarajasi === daraja ? "#1B4B7A" : "#EAF1F7", color: ochiqSinfDarajasi === daraja ? "#fff" : "#1B4B7A" }}>{daraja}{__kbUi("-sinf")}</button>)}</div>
          <div className="rounded-xl border p-4" style={{ borderColor: "#D9E5EA" }}>
            <div className="flex items-center justify-between gap-2"><b>{ochiqSinfDarajasi}{__kbUi("-sinf fanlari")}</b><span className="text-xs" style={{ color: "#63808D" }}>{(sinfFanlari[String(ochiqSinfDarajasi)] || []).length}{__kbUi(" ta tanlangan")}</span></div>
            <div className="grid sm:grid-cols-[1fr_auto] gap-2 mt-3"><input value={yangiSinfFani[String(ochiqSinfDarajasi)] || ""} onChange={(e) => setYangiSinfFani((a) => ({ ...a, [String(ochiqSinfDarajasi)]: e.target.value }))} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); sinfgaYangiFanQosh(ochiqSinfDarajasi); } }} placeholder={__kbUi(`${ochiqSinfDarajasi}-sinfga yangi fan qo‘shish...`)} className="px-3 py-2.5 rounded-xl border text-sm"/><button type="button" onClick={() => sinfgaYangiFanQosh(ochiqSinfDarajasi)} className="px-4 py-2.5 rounded-xl text-sm font-bold text-white" style={{ backgroundColor: "#087F8C" }}>{__kbUi("+ Fan qo‘shish")}</button></div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2 mt-4">{takrorsizSinfFanlari([...(dtsSinfFanlari[String(ochiqSinfDarajasi)] || []), ...(sinfFanlari[String(ochiqSinfDarajasi)] || [])], dtsSinfFanlari[String(ochiqSinfDarajasi)] || []).map((fan) => { const tanlanganKalitlar = new Set((sinfFanlari[String(ochiqSinfDarajasi)] || []).map(sinfFanKaliti)); const tanlangan = tanlanganKalitlar.has(sinfFanKaliti(fan)); return <button key={sinfFanKaliti(fan)} type="button" onClick={() => sinfFaniniAlmashtir(ochiqSinfDarajasi, fan)} className="text-left px-3 py-3 rounded-xl border text-sm font-semibold" style={{ backgroundColor: tanlangan ? "#EAF4DF" : "#fff", borderColor: tanlangan ? "#8CB76D" : "#D9E5EA", color: tanlangan ? "#315F18" : "#526875" }}>{tanlangan ? __kbUi("✓ ") : __kbUi("")}{fan}</button>; })}</div>
          </div>
          {fanXato && <p className="text-xs mt-3" style={{ color: "#B0553A" }}>{__kbUi(fanXato)}</p>}{fanXabar && <p className="text-xs mt-3" style={{ color: "#3B6D11" }}>{fanXabar}</p>}
          <button type="button" onClick={sinfFanlariniSaqla} disabled={fanlarSaqlanmoqda} className="w-full mt-4 py-3 rounded-xl text-sm font-bold text-white" style={{ backgroundColor: "#1B4B7A" }}>{fanlarSaqlanmoqda ? uiT("Saqlanmoqda...") : __kbUi("1–11-sinf fanlarini saqlash")}</button>
        </div>}
      </div>

      {false && <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: fanlarTayyor ? "#BFD5AA" : "#E5E1D8" }}>
        <div className="flex items-start justify-between gap-3 mb-1">
          <div>
            <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("2-bosqich — Maktab fanlarini tanlash")}</p>
            <p className="text-xs mt-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Shu maktabda o‘tiladigan barcha fanlarni belgilang. Faqat saqlangan fanlar xodim Excelidagi aqlli tanlovga tushadi.")}</p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full shrink-0"
            style={{ backgroundColor: fanlarTayyor ? "#EAF4DF" : "#F7F5F0", color: fanlarTayyor ? "#3B6D11" : "#8A8578" }}>
            {fanlarTayyor ? __kbUi(`${saqlanganFanlar.length} ta saqlangan`) : __kbUi("Saqlanmagan")}
          </span>
        </div>

        <div className="grid sm:grid-cols-[1fr_auto] gap-2 mt-4">
          <input value={yangiFanNomi} onChange={(e) => setYangiFanNomi(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); yangiFanQosh(); } }} placeholder={__kbUi("Ro‘yxatda yo‘q fan nomini yozing...")} className="px-3.5 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          <button type="button" onClick={yangiFanQosh} className="px-4 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ backgroundColor: "#1B4B7A" }}>{__kbUi("＋ Fan qo‘shish")}</button>
        </div>
        {fanlarYuklanmoqda ? (
          <div className="py-8 text-center"><Loader2 size={20} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
        ) : fanKatalogi.length === 0 ? (
          <p className="text-xs mt-4 p-3 rounded-xl" style={{ backgroundColor: "#FFF5E2", color: "#8A5A1C" }}>{__kbUi("Tavsiya fanlari topilmadi. Yuqoridagi maydondan fanlarni qo‘lda kiriting.")}</p>
        ) : (
          <>
            <div className="flex flex-wrap gap-2 mt-4 mb-3">
              <button type="button" onClick={() => { setTanlanganFanlar(fanKatalogi.map((fan) => fan.nomi)); setFanXabar(""); }}
                className="px-3 py-2 rounded-xl text-xs font-semibold" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("✓ Barchasini tanlash")}</button>
              <button type="button" onClick={() => { setTanlanganFanlar([]); setFanXabar(""); }}
                className="px-3 py-2 rounded-xl text-xs font-semibold" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Tanlovni tozalash")}</button>
              <span className="px-3 py-2 text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Tanlandi: ")}{tanlanganFanlar.length}/{fanKatalogi.length}
              </span>
            </div>
            <div className="grid sm:grid-cols-2 gap-2 max-h-72 overflow-y-auto pr-1">
              {fanKatalogi.map((fan) => {
                const tanlangan = tanlanganFanlar.includes(fan.nomi);
                return (
                  <button key={fan.nomi} type="button" onClick={() => fanTanlashniAlmashtir(fan.nomi)}
                    className="text-left rounded-xl border p-3 flex items-start gap-2.5"
                    style={tanlangan
                      ? { backgroundColor: "#EAF1F7", borderColor: "#1B4B7A", color: "#1B4B7A" }
                      : { backgroundColor: "#fff", borderColor: "#E5E1D8", color: "#5A5648" }}>
                    <span className="w-5 h-5 rounded-md flex items-center justify-center shrink-0 text-xs font-bold"
                      style={{ backgroundColor: tanlangan ? "#1B4B7A" : "#F7F5F0", color: tanlangan ? "#fff" : "#A39D8E" }}>
                      {tanlangan ? __kbUi("✓") : __kbUi("")}
                    </span>
                    <span>
                      <span className="block text-sm font-semibold">{fan.nomi}</span>
                      <span className="block text-xs mt-0.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
                        {fan.manba || __kbUi("DTS tavsiyasi")}{__kbUi(" · sinfga avtomatik biriktirilmaydi")}</span>
                    </span>
                  </button>
                );
              })}
            </div>
            <button type="button" onClick={fanlarniSaqla}
              disabled={fanlarSaqlanmoqda || !tanlanganFanlar.length || (!fanlarOzgargan && fanlarTayyor)}
              className="w-full py-3 rounded-xl font-semibold text-sm mt-4"
              style={{
                backgroundColor: fanlarOzgargan ? "#1B4B7A" : "#D7E0E7",
                color: "#fff",
                opacity: fanlarSaqlanmoqda || !tanlanganFanlar.length ? 0.65 : 1,
              }}>
              {fanlarSaqlanmoqda ? uiT("Saqlanmoqda...") : fanlarOzgargan ? __kbUi("Tanlangan fanlarni saqlash") : __kbUi("Fanlar saqlangan")}
            </button>
          </>
        )}
        {fanXato && <p className="text-sm mt-3" style={{ color: "#B0553A" }}>{__kbUi(fanXato)}</p>}
        {fanXabar && <p className="text-sm mt-3" style={{ color: "#3B6D11" }}>{fanXabar}</p>}
      </div>}

      <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("3-bosqich — Xodimlarni kiritish · V19.2")}</p>
        <p className="text-xs mb-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Katakni bosib lavozim, sinf, fan va toifani tayyor ro‘yxatdan tanlang. Yangi shablonda butun sinf va barcha 1/2-guruh, o‘g‘il/qiz hamda mustaqil guruhlar bitta ")}<b>{__kbUi("XODIMLAR")}</b>{__kbUi(" varag‘ida aniq fan bilan chiqadi. Alohida GURUHLI_DARSLAR varag‘i yo‘q. Saytda esa “Aqlli jadval → O‘qituvchi + fan-soat” oynasidan shu ma’lumotlarni Excelsiz ham kiritish mumkin. Har bir qatorda fan–sinf–guruh–soat aniq saqlanadi, shuning uchun bir o‘qituvchining fanlari aralashmaydi. Yangi o‘qituvchining o‘zini ham shu oynadagi “Qo‘lda kiritish” tugmasi orqali yaratish mumkin.")}</p>
        {!fanlarTayyor && <p className="text-xs mb-3 p-3 rounded-xl" style={{ backgroundColor: "#FFF5E2", color: "#8A5A1C" }}>{__kbUi("Avval yuqoridagi maktab fanlarini tanlab saqlang.")}</p>}
        <button onClick={shablonYukla} disabled={!fanlarTayyor}
          className="w-full py-3 rounded-xl font-semibold text-sm mb-2.5 flex items-center justify-center gap-2"
          style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)", opacity: fanlarTayyor ? 1 : 0.5 }}>{__kbUi("📥 Shablonni yuklab olish")}</button>
        <label className="w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 cursor-pointer border-2 border-dashed"
          style={{ borderColor: "#C4BFAF", color: "var(--ui-legacy-color-5a5648, #5A5648)", opacity: fanlarTayyor ? 1 : 0.5, cursor: fanlarTayyor ? "pointer" : "not-allowed" }}>
          {importlanmoqda ? <Loader2 size={16} className="animate-spin" /> : __kbUi("📤 To'ldirilgan faylni yuklash")}
          <input type="file" accept=".xlsx" onChange={faylTanlandi} disabled={importlanmoqda || !fanlarTayyor} className="hidden" />
        </label>
        {xato && <p className="text-sm mt-3 whitespace-pre-line" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
      </div>

      {importXabari && (
        <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm font-semibold" style={{ color: "#3B6D11" }}>{importXabari}</p>
        </div>
      )}

      <div className="rounded-2xl p-5 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("4-bosqich — Sinflar")}</p>
        <p className="text-xs mb-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Sinflar avval yaratiladi. Xodim importi yangi sinf yaratmaydi; mavjud sinfga rahbar va dars beruvchi xodimlarni bog‘laydi.")}</p>
        {!!sinflar.length && <div className="rounded-xl border p-3.5 mb-4" style={{ backgroundColor: "#F1F7FB", borderColor: "#B9CCDC" }}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div><b className="text-sm" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Sinflarni ommaviy guruhlash")}</b><p className="text-[11px] mt-0.5" style={{ color: "#63808D" }}>{__kbUi("Pastdan kerakli sinflarni ptichka bilan tanlang, guruh turini belgilang va qo‘llang.")}</p></div>
            <span className="px-3 py-1.5 rounded-full text-xs font-bold" style={{ backgroundColor: "var(--ui-legacy-background-fff, #fff)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{tanlanganGuruhSinflari.size}{__kbUi(" ta sinf tanlandi")}</span>
          </div>
          <div className="flex flex-wrap items-center gap-2 mt-3">
            <button type="button" onClick={() => setTanlanganGuruhSinflari(new Set(sinflar.map((sinf) => sinf.id)))} className="px-3 py-2 rounded-lg text-xs font-semibold" style={{ backgroundColor: "var(--ui-legacy-background-fff, #fff)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)", border: "1px solid #B9CCDC" }}>{__kbUi("✓ Barcha sinflar")}</button>
            <button type="button" onClick={() => setTanlanganGuruhSinflari(new Set())} className="px-3 py-2 rounded-lg text-xs font-semibold" style={{ backgroundColor: "var(--ui-legacy-background-fff, #fff)", color: "#8A5A1C", border: "1px solid #E5D1A5" }}>{__kbUi("Tanlovni tozalash")}</button>
            <label className="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-xs font-bold" style={{ backgroundColor: ommaviyGuruhTurlari.has("alphabet") ? "#DDEBF4" : "#fff", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)", border: "1px solid #B9CCDC" }}><input type="checkbox" checked={ommaviyGuruhTurlari.has("alphabet")} onChange={() => ommaviyGuruhTuriniTanlash("alphabet")}/>{__kbUi(" 1/2 guruh")}</label>
            <label className="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-xs font-bold" style={{ backgroundColor: ommaviyGuruhTurlari.has("gender") ? "#F4E6EF" : "#fff", color: "#934A70", border: "1px solid #DDB9CC" }}><input type="checkbox" checked={ommaviyGuruhTurlari.has("gender")} onChange={() => ommaviyGuruhTuriniTanlash("gender")}/>{__kbUi(" O‘g‘il/Qiz")}</label>
            <button type="button" disabled={ommaviyGuruhSaqlanmoqda || !tanlanganGuruhSinflari.size || !ommaviyGuruhTurlari.size} onClick={tanlanganSinflarniGuruhlash} className="px-4 py-2 rounded-lg text-xs font-bold text-white" style={{ backgroundColor: "#087F8C", opacity: ommaviyGuruhSaqlanmoqda || !tanlanganGuruhSinflari.size || !ommaviyGuruhTurlari.size ? .5 : 1 }}>{ommaviyGuruhSaqlanmoqda ? uiT("Saqlanmoqda...") : __kbUi("Tanlangan sinflarga qo‘llash")}</button>
          </div>
          {ommaviyGuruhXabar && <p className="text-xs font-semibold mt-2" style={{ color: ommaviyGuruhXabar.startsWith("❌") ? "#B0553A" : "#3B6D11" }}>{ommaviyGuruhXabar}</p>}
        </div>}
        {sinflarYuklanmoqda ? (
          <div className="py-6 text-center"><Loader2 size={20} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
        ) : sinflar.length === 0 ? (
          <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali sinf yo‘q — avval maktab yaratish oynasida sinflarni yarating.")}</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 items-start">
            {sinflar.map((s) => (
              <div key={s.id} className={`rounded-xl p-3.5 transition-all ${String(ochiqSinfGuruhId) === String(s.id) || String(ochiqSinfTahrirId) === String(s.id) ? "md:col-span-2 xl:col-span-4" : ""}`} style={{ backgroundColor: tanlanganGuruhSinflari.has(s.id) ? "#EDF5FA" : "#F7F5F0", border: String(ochiqSinfGuruhId) === String(s.id) || String(ochiqSinfTahrirId) === String(s.id) ? "2px solid #1B4B7A" : tanlanganGuruhSinflari.has(s.id) ? "2px solid #5C94B7" : "1px solid #E5E1D8", boxShadow: String(ochiqSinfGuruhId) === String(s.id) || String(ochiqSinfTahrirId) === String(s.id) ? "0 10px 28px rgba(27,75,122,.14)" : "none" }}>
                <div className="grid sm:grid-cols-[1fr_auto] gap-3 items-center">
                  <div>
                  <label className="flex items-center gap-2 text-sm font-bold cursor-pointer" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}><input type="checkbox" checked={tanlanganGuruhSinflari.has(s.id)} onChange={() => guruhSinfiniTanlash(s.id)}/>{s.sinf}-{s.harf}</label>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{s.rahbar_ismi || __kbUi("Rahbar belgilanmagan")} · {s.psixolog_ismi || __kbUi("Psixolog belgilanmagan")}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{s.smena || 1}{__kbUi("-smena")}{s.bino ? __kbUi(` · ${s.bino}`) : __kbUi("")}{s.xona ? __kbUi(` · ${s.xona}-xona`) : __kbUi("")}</p>
                  <p className="text-xs font-mono mt-0.5" style={{ color: "#8A5A1C" }}>🔐 {__kbUi(s.qoshilish_paroli)}</p>
                  </div>
                  <button onClick={() => parolniTashla(s.id)} className="text-xs font-medium px-2.5 py-1.5 rounded-lg" style={{ backgroundColor: "var(--ui-legacy-background-fff, #fff)", color: "var(--ui-legacy-color-5a5648, #5A5648)", border: "1px solid #E5E1D8" }}>{__kbUi("↻ Parolni tashlash")}</button>
                </div>
                <SinfAsosiyTahriri
                  token={token}
                  sinf={s}
                  ochiq={String(ochiqSinfTahrirId) === String(s.id)}
                  onToggle={() => { setOchiqSinfGuruhId(null); setOchiqSinfTahrirId((avvalgi) => String(avvalgi) === String(s.id) ? null : s.id); }}
                  onSaved={() => sinflarniYukla(true)}
                />
                <SinfGuruhBoshqaruvi
                  token={token}
                  sinf={s}
                  fanlar={saqlanganFanlar}
                  ochiq={String(ochiqSinfGuruhId) === String(s.id)}
                  onToggle={() => { setOchiqSinfTahrirId(null); setOchiqSinfGuruhId((avvalgi) => String(avvalgi) === String(s.id) ? null : s.id); }}
                  onSaved={() => sinflarniYukla(true)}
                  yangilashVersiyasi={guruhYangilashVersiyasi}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function MarkazlarBolimi({ token }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [markazlar, setMarkazlar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [formOchiq, setFormOchiq] = useState(false);
  const [nomi, setNomi] = useState("");
  const [viloyat, setViloyat] = useState("");
  const [tuman, setTuman] = useState("");
  const [direktor, setDirektor] = useState(null);
  const [saqlanmoqda, setSaqlanmoqda] = useState(false);
  const [xato, setXato] = useState("");
  const [tanlanganMarkaz, setTanlanganMarkaz] = useState(null);

  const markazlarniYukla = () => {
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/admin/markazlar?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => { setMarkazlar(d.markazlar || []); setYuklanmoqda(false); })
      .catch(() => setYuklanmoqda(false));
  };
  useEffect(markazlarniYukla, [token]);

  const markazSaqla = async () => {
    if (!nomi.trim()) { setXato("Markaz nomini kiriting"); return; }
    setSaqlanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/markaz_yarat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token, nomi: nomi.trim(), viloyat: viloyat || undefined, tuman: tuman || undefined,
          direktor_user_id: direktor ? direktor.user_id : undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setNomi(""); setViloyat(""); setTuman(""); setDirektor(null); setFormOchiq(false);
      markazlarniYukla();
    } catch (e) {
      setXato(e.message);
    } finally { setSaqlanmoqda(false); }
  };

  if (tanlanganMarkaz) {
    return <MarkazTafsiloti token={token} markaz={tanlanganMarkaz} onOrtga={() => { setTanlanganMarkaz(null); markazlarniYukla(); }} />;
  }

  return (
    <div>
      <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <div className="flex items-center justify-between mb-1">
          <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🎓 O'quv markazlari")}</p>
          <button onClick={() => setFormOchiq(!formOchiq)} className="text-xs font-semibold px-3.5 py-1.5 rounded-full" style={{ backgroundColor: "#1B4B7A", color: "#fff" }}>
            {formOchiq ? __kbUi("✕ Yopish") : __kbUi("+ Yangi markaz")}
          </button>
        </div>
        <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Repetitorlik/o'quv markazlari uchun — guruhlar mavjud to'garak tizimi orqali ishlaydi.")}</p>
      </div>

      {formOchiq && (
        <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Markaz nomi")}</label>
          <input type="text" value={nomi} onChange={(e) => setNomi(e.target.value)}
            placeholder={__kbUi("masalan: Iqbol o'quv markazi")}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
            style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />

          <div className="grid grid-cols-2 gap-2.5 mb-3">
            <div>
              <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Viloyat")}/></label>
              <select value={viloyat} onChange={(e) => { setViloyat(e.target.value); setTuman(""); }}
                className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                <option value="">—</option>
                {VILOYATLAR.map((v) => <option key={v} value={v}>{__kbUi(v)}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Tuman")}/></label>
              <select value={tuman} onChange={(e) => setTuman(e.target.value)} disabled={!viloyat}
                className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", opacity: viloyat ? 1 : 0.5 }}>
                <option value="">—</option>
                {(HUDUDLAR[viloyat] || []).map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Direktor (ixtiyoriy)")}</label>
          <DirektorQidiruvi token={token} tanlanganDirektor={direktor} onTanla={setDirektor} />

          {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
          <button onClick={markazSaqla} disabled={saqlanmoqda}
            className="w-full py-3 rounded-xl font-semibold text-white text-sm"
            style={{ backgroundColor: "#1B4B7A", opacity: saqlanmoqda ? 0.7 : 1 }}>
            {saqlanmoqda ? uiT("Saqlanmoqda...") : __kbUi("Markazni yaratish")}
          </button>
        </div>
      )}

      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : markazlar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali markaz qo'shilmagan.")}</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {markazlar.map((m) => (
            <button key={m.id} onClick={() => setTanlanganMarkaz(m)}
              className="w-full text-left rounded-xl p-4 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div>
                <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{m.nomi}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{[m.viloyat, m.tuman].filter(Boolean).join(", ") || __kbUi("Hudud ko'rsatilmagan")}</p>
                <p className="text-xs mt-1" style={{ color: m.direktor_ismi ? "#3B6D11" : "#B0553A" }}>
                  {m.direktor_ismi ? __kbUi(`👤 Direktor: ${m.direktor_ismi}`) : __kbUi("⚠️ Direktor hali belgilanmagan")}
                </p>
              </div>
              <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function MarkazTafsiloti({ token, markaz, onOrtga }) {
  useKbInterfaceLocale();
  const [importlanmoqda, setImportlanmoqda] = useState(false);
  const [xato, setXato] = useState("");
  const [natijalar, setNatijalar] = useState(null);

  const shablonYukla = () => {
    window.open(`${API_BASE}/api/admin/markaz_xodim_shablon?token=${encodeURIComponent(token)}`, "_blank");
  };

  const faylTanlandi = async (e) => {
    const fayl = e.target.files[0];
    if (!fayl) return;
    setImportlanmoqda(true); setXato(""); setNatijalar(null);
    try {
      const formData = new FormData();
      formData.append("fayl", fayl);
      const res = await fetch(`${API_BASE}/api/admin/markaz_xodim_import?token=${encodeURIComponent(token)}&markaz_id=${markaz.id}`, {
        method: "POST", body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setNatijalar(data.natijalar || []);
    } catch (e) {
      setXato(e.message);
    } finally {
      setImportlanmoqda(false);
      e.target.value = "";
    }
  };

  return (
    <div>
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Markazlar")}/></button>
      <h1 className="text-lg font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{markaz.nomi}</h1>
      <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{[markaz.viloyat, markaz.tuman].filter(Boolean).join(", ") || __kbUi("Hudud ko'rsatilmagan")}</p>

      <div className="rounded-2xl p-5 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Xodimlarni kiritish")}</p>
        <p className="text-xs mb-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Shablonni yuklab, F.I.Sh / Lavozimni to'ldirib, qayta yuklang. \"Fan o'qituvchisi\" bo'lganlar keyin to'garak (guruh) yaratganda, u avtomatik shu markazga bog'lanadi — alohida ulash shart emas.")}</p>
        <button onClick={shablonYukla}
          className="w-full py-3 rounded-xl font-semibold text-sm mb-2.5 flex items-center justify-center gap-2"
          style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("📥 Shablonni yuklab olish")}</button>
        <label className="w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 cursor-pointer border-2 border-dashed"
          style={{ borderColor: "#C4BFAF", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
          {importlanmoqda ? <Loader2 size={16} className="animate-spin" /> : __kbUi("📤 To'ldirilgan faylni yuklash")}
          <input type="file" accept=".xlsx" onChange={faylTanlandi} disabled={importlanmoqda} className="hidden" />
        </label>
        {xato && <p className="text-sm mt-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
      </div>

      {natijalar && (
        <div className="rounded-2xl p-5 bg-white border mt-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>✅ {natijalar.length}{__kbUi(" ta xodim qo'shildi")}</p>
          <p className="text-xs mb-4" style={{ color: "#B0553A" }}>{__kbUi("Diqqat: bu kodlarni endi shu yerdan nusxalab, har bir xodimga yuboring — bu ekranga qayta qaytib bo'lmaydi!")}</p>
          <div className="space-y-2.5">
            {natijalar.map((n, i) => (
              <div key={i} className="rounded-xl p-3.5" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{n.fish}</p>
                <p className="text-xs mb-1.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{n.lavozim}</p>
                <p className="text-xs font-mono" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("🔑 Kirish kodi: ")}<b>{n.kirish_kodi}</b></p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function BogchalarBolimi({ token }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [bogchalar, setBogchalar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [formOchiq, setFormOchiq] = useState(false);
  const [nomi, setNomi] = useState("");
  const [turi, setTuri] = useState("xususiy");
  const [viloyat, setViloyat] = useState("");
  const [tuman, setTuman] = useState("");
  const [direktor, setDirektor] = useState(null);
  const [saqlanmoqda, setSaqlanmoqda] = useState(false);
  const [xato, setXato] = useState("");
  const [tanlanganBogcha, setTanlanganBogcha] = useState(null);

  const bogchalarniYukla = () => {
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/admin/bogchalar`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
      credentials: "omit",
    })
      .then((r) => r.json())
      .then((d) => { setBogchalar(d.bogchalar || []); setYuklanmoqda(false); })
      .catch(() => setYuklanmoqda(false));
  };
  useEffect(bogchalarniYukla, [token]);

  const bogchaSaqla = async () => {
    if (!nomi.trim()) { setXato("Bog'cha nomini kiriting"); return; }
    setSaqlanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/bogcha_yarat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token, nomi: nomi.trim(), turi, viloyat: viloyat || undefined, tuman: tuman || undefined,
          direktor_user_id: direktor ? direktor.user_id : undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setNomi(""); setTuri("xususiy"); setViloyat(""); setTuman(""); setDirektor(null); setFormOchiq(false);
      bogchalarniYukla();
    } catch (e) {
      setXato(e.message);
    } finally { setSaqlanmoqda(false); }
  };

  if (tanlanganBogcha) {
    return <BogchaTafsiloti token={token} bogcha={tanlanganBogcha} onOrtga={() => { setTanlanganBogcha(null); bogchalarniYukla(); }} />;
  }

  return (
    <div>
      <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <div className="flex items-center justify-between mb-1">
          <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>🧸 <InterfaceText text={__kbUi("Bog'chalar")}/></p>
          <button onClick={() => setFormOchiq(!formOchiq)} className="text-xs font-semibold px-3.5 py-1.5 rounded-full" style={{ backgroundColor: "#1B4B7A", color: "#fff" }}>
            {formOchiq ? __kbUi("✕ Yopish") : __kbUi("+ Yangi bog'cha")}
          </button>
        </div>
        <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Xususiy/davlat bog'chalar — direktor, zam, opalar va guruhlar bilan.")}</p>
      </div>

      {formOchiq && (
        <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Bog'cha nomi")}</label>
          <input type="text" value={nomi} onChange={(e) => setNomi(e.target.value)}
            placeholder={__kbUi("masalan: Quyoshcha bog'chasi")}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
            style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Turi")}</label>
          <div className="flex gap-2 mb-3">
            {Object.entries({ xususiy: "Xususiy", davlat: "Davlat" }).map(([k, v]) => (
              <button key={k} onClick={() => setTuri(k)}
                className="flex-1 py-2.5 rounded-xl border text-sm font-semibold"
                style={turi === k ? { backgroundColor: "#1B4B7A", color: "#fff", borderColor: "#1B4B7A" } : { backgroundColor: "#fff", color: "#5A5648", borderColor: "#E5E1D8" }}>
                {__kbUi(v)}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-2.5 mb-3">
            <div>
              <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Viloyat")}/></label>
              <select value={viloyat} onChange={(e) => { setViloyat(e.target.value); setTuman(""); }}
                className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                <option value="">—</option>
                {VILOYATLAR.map((v) => <option key={v} value={v}>{__kbUi(v)}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Tuman")}/></label>
              <select value={tuman} onChange={(e) => setTuman(e.target.value)} disabled={!viloyat}
                className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", opacity: viloyat ? 1 : 0.5 }}>
                <option value="">—</option>
                {(HUDUDLAR[viloyat] || []).map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Direktor (ixtiyoriy)")}</label>
          <DirektorQidiruvi token={token} tanlanganDirektor={direktor} onTanla={setDirektor} />

          {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
          <button onClick={bogchaSaqla} disabled={saqlanmoqda}
            className="w-full py-3 rounded-xl font-semibold text-white text-sm"
            style={{ backgroundColor: "#1B4B7A", opacity: saqlanmoqda ? 0.7 : 1 }}>
            {saqlanmoqda ? uiT("Saqlanmoqda...") : __kbUi("Bog'chani yaratish")}
          </button>
        </div>
      )}

      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : bogchalar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali bog'cha qo'shilmagan.")}</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {bogchalar.map((b) => (
            <button key={b.id} onClick={() => setTanlanganBogcha(b)}
              className="w-full text-left rounded-xl p-4 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div>
                <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{b.nomi}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
                  {b.turi === "xususiy" ? __kbUi("Xususiy") : __kbUi("Davlat")} · {[b.viloyat, b.tuman].filter(Boolean).join(", ") || __kbUi("Hudud ko'rsatilmagan")}
                </p>
                <p className="text-xs mt-1" style={{ color: b.direktor_ismi ? "#3B6D11" : "#B0553A" }}>
                  {b.direktor_ismi ? __kbUi(`👤 Direktor: ${b.direktor_ismi}`) : __kbUi("⚠️ Direktor hali belgilanmagan")}
                </p>
              </div>
              <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function BogchaTafsiloti({ token, bogcha, onOrtga }) {
  useKbInterfaceLocale();
  const [importlanmoqda, setImportlanmoqda] = useState(false);
  const [xato, setXato] = useState("");
  const [natijalar, setNatijalar] = useState(null);

  const shablonYukla = async () => {
    setXato("");
    try {
      const response = await fetch(`${API_BASE}/api/admin/bogcha_xodim_shablon`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
        credentials: "omit",
      });
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.detail || "Shablonni yuklab bo‘lmadi");
      }
      const blobUrl = URL.createObjectURL(await response.blob());
      const download = document.createElement("a");
      download.href = blobUrl;
      download.download = "bogcha_xodimlar_shablon.xlsx";
      download.click();
      URL.revokeObjectURL(blobUrl);
    } catch (error) {
      setXato(error.message);
    }
  };

  const faylTanlandi = async (e) => {
    const fayl = e.target.files[0];
    if (!fayl) return;
    setImportlanmoqda(true); setXato(""); setNatijalar(null);
    try {
      const formData = new FormData();
      formData.append("fayl", fayl);
      const res = await fetch(`${API_BASE}/api/admin/bogcha_xodim_import?bogcha_id=${bogcha.id}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
        cache: "no-store",
        credentials: "omit",
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setNatijalar(data.natijalar || []);
    } catch (e) {
      setXato(e.message);
    } finally {
      setImportlanmoqda(false);
      e.target.value = "";
    }
  };

  return (
    <div>
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Bog'chalar")}/></button>
      <h1 className="text-lg font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{bogcha.nomi}</h1>
      <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
        {bogcha.turi === "xususiy" ? __kbUi("Xususiy") : __kbUi("Davlat")} · {[bogcha.viloyat, bogcha.tuman].filter(Boolean).join(", ") || __kbUi("Hudud ko'rsatilmagan")}
      </p>

      <div className="rounded-2xl p-5 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Xodimlarni kiritish")}</p>
        <p className="text-xs mb-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Shablonni yuklab, F.I.Sh / Lavozim / Guruh rahbarligini to'ldirib, qayta yuklang. \"Bog'cha opasi\" bo'lganlar uchun guruh nomini yozsangiz, o'sha guruh avtomatik yaratiladi.")}</p>
        <button onClick={shablonYukla}
          className="w-full py-3 rounded-xl font-semibold text-sm mb-2.5 flex items-center justify-center gap-2"
          style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("📥 Shablonni yuklab olish")}</button>
        <label className="w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 cursor-pointer border-2 border-dashed"
          style={{ borderColor: "#C4BFAF", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
          {importlanmoqda ? <Loader2 size={16} className="animate-spin" /> : __kbUi("📤 To'ldirilgan faylni yuklash")}
          <input type="file" accept=".xlsx" onChange={faylTanlandi} disabled={importlanmoqda} className="hidden" />
        </label>
        {xato && <p className="text-sm mt-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
      </div>

      {natijalar && (
        <div className="rounded-2xl p-5 bg-white border mt-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>✅ {natijalar.length}{__kbUi(" ta xodim qo'shildi")}</p>
          <p className="text-xs mb-4" style={{ color: "#B0553A" }}>{__kbUi("Diqqat: bu kodlarni endi shu yerdan nusxalab, har bir xodimga yuboring — bu ekranga qayta qaytib bo'lmaydi!")}</p>
          <div className="space-y-2.5">
            {natijalar.map((n, i) => (
              <div key={i} className="rounded-xl p-3.5" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{n.fish}</p>
                <p className="text-xs mb-1.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{n.lavozim}{n.guruh_nomi ? __kbUi(` · ${n.guruh_nomi}`) : __kbUi("")}</p>
                <p className="text-xs font-mono" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("🔑 Kirish kodi: ")}<b>{n.kirish_kodi}</b></p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Muassasaga TALABA paroli — faqat super admin (admin_akkaunt) qo'yadi.
// Talaba shu 4 belgi bilan Profil → "Men 1–11 sinf emasman" orqali qo'shiladi.
function TalabaParolQatori({ token, universitet, onYangilandi }) {
  useKbInterfaceLocale();
  const [rejim, setRejim] = useState(null); // null | "qolda"
  const [qiymat, setQiymat] = useState("");
  const [band, setBand] = useState(false);
  const [xato, setXato] = useState("");
  const [nusxalandi, setNusxalandi] = useState(false);

  const yubor = async (body) => {
    setBand(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/universitet_talaba_paroli`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, universitet_id: universitet.id, ...body }),
      });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof d.detail === "string" ? d.detail : `Server xatosi (${res.status})`);
      onYangilandi({ id: universitet.id, talaba_paroli: d.talaba_paroli });
      setRejim(null); setQiymat("");
    } catch (e) { setXato(e.message); } finally { setBand(false); }
  };
  const nusxala = async () => {
    try { await navigator.clipboard.writeText(universitet.talaba_paroli); setNusxalandi(true); setTimeout(() => setNusxalandi(false), 1500); } catch { /* jim */ }
  };

  return (
    <div className="px-4 pb-3 pt-2 border-t" style={{ borderColor: "#EFECE6" }} onClick={(e) => e.stopPropagation()}>
      <div className="flex flex-wrap items-center gap-2">
        {universitet.talaba_paroli ? (
          <>
            <span className="text-xs" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("🔐 Talaba paroli:")}</span>
            <button type="button" onClick={nusxala} title={__kbUi("Nusxalash")} className="font-mono font-bold text-sm px-2 py-0.5 rounded-lg" style={{ backgroundColor: "#F1EEF8", color: "#5B4B8A", letterSpacing: "0.15em" }}>{__kbUi(universitet.talaba_paroli)}</button>
            {nusxalandi && <span className="text-[11px]" style={{ color: "#3B6D11" }}>{__kbUi("nusxalandi")}</span>}
            <span className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>· 👥 {Number(universitet.talaba_soni) || 0}{__kbUi(" talaba")}</span>
          </>
        ) : (
          <span className="text-xs" style={{ color: "#B0553A" }}>{__kbUi("🔓 Talabalar uchun parol qo'yilmagan — talaba qo'shila olmaydi")}</span>
        )}
        <span className="ml-auto flex flex-wrap gap-1.5">
          <button type="button" disabled={band} onClick={() => yubor({})} className="text-[11px] font-semibold px-2.5 py-1 rounded-full border" style={{ borderColor: "#D9D2EA", color: "#5B4B8A", backgroundColor: "#fff" }}>{universitet.talaba_paroli ? __kbUi("Yangi parol") : __kbUi("Parol yaratish")}</button>
          <button type="button" disabled={band} onClick={() => { setRejim(rejim === "qolda" ? null : "qolda"); setXato(""); }} className="text-[11px] font-semibold px-2.5 py-1 rounded-full border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", color: "var(--ui-legacy-color-5a5648, #5A5648)", backgroundColor: "#fff" }}>{__kbUi("Qo'lda")}</button>
          {universitet.talaba_paroli && <button type="button" disabled={band} onClick={() => { if (window.confirm(__kbUi(`${universitet.nomi}: talaba parolini o'chirasizmi? Yangi talabalar qo'shila olmaydi (mavjudlar qoladi).`))) yubor({ ochirish: true }); }} className="text-[11px] font-semibold px-2.5 py-1 rounded-full border" style={{ borderColor: "#F1D5CC", color: "#B0553A", backgroundColor: "#fff" }}>{__kbUi("O'chirish")}</button>}
        </span>
      </div>
      {rejim === "qolda" && (
        <div className="flex items-center gap-2 mt-2">
          <input value={qiymat} maxLength={4} autoFocus placeholder={__kbUi("A7K2")} aria-label={__kbUi("4 belgili parol")}
            onChange={(e) => setQiymat(e.target.value.replace(/[^0-9a-zA-Z]/g, "").toUpperCase())}
            onKeyDown={(e) => e.key === "Enter" && qiymat.length === 4 && yubor({ parol: qiymat })}
            className="font-mono font-bold text-sm px-3 py-1.5 rounded-lg border w-24 text-center" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", letterSpacing: "0.2em" }} />
          <button type="button" disabled={band || qiymat.length !== 4} onClick={() => yubor({ parol: qiymat })} className="text-xs font-semibold px-3 py-1.5 rounded-lg text-white" style={{ backgroundColor: "#5B4B8A", opacity: band || qiymat.length !== 4 ? 0.6 : 1 }}>{band ? __kbUi("…") : __kbUi("Saqlash")}</button>
          <span className="text-[11px]" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("4 belgi: harf + raqam aralash")}</span>
        </div>
      )}
      {xato && <p className="text-xs mt-1.5" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
    </div>
  );
}

function UniversitetlarBolimi({ token }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [holat, setHolat] = useState("universitet"); // universitet | fakultet | kafedra | guruh
  const [workspaceUniversity, setWorkspaceUniversity] = useState(null);
  const [universitetlar, setUniversitetlar] = useState([]);
  const [eskiKorsat, setEskiKorsat] = useState(false);
  const [fakultetlar, setFakultetlar] = useState([]);
  const [kafedralar, setKafedralar] = useState([]);
  const [yonalishlar, setYonalishlar] = useState([]);
  const [guruhlar, setGuruhlar] = useState([]);
  const [tUniversitet, setTUniversitet] = useState(null);
  const [tFakultet, setTFakultet] = useState(null);
  const [tKafedra, setTKafedra] = useState(null);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [formOchiq, setFormOchiq] = useState(false);
  const [xato, setXato] = useState("");
  const [saqlanmoqda, setSaqlanmoqda] = useState(false);

  const [nomi, setNomi] = useState("");
  const [viloyat, setViloyat] = useState("");
  const [tuman, setTuman] = useState("");
  const [kurs, setKurs] = useState("");
  const [yonalish, setYonalish] = useState("");
  const [rahbar, setRahbar] = useState(null);
  const [rahbarIsmi, setRahbarIsmi] = useState("");
  const [kirishNatija, setKirishNatija] = useState(null);
  const [hayot, setHayot] = useState(null); // REV79: { universitet, tab } — talabalar / sahifa

  const formniTozala = () => { setNomi(""); setViloyat(""); setTuman(""); setKurs(""); setYonalish(""); setRahbar(null); setRahbarIsmi(""); setFormOchiq(false); setXato(""); };

  const universitetRequestRef = useRef(0);
  const universitetlarniYukla = () => {
    const requestId = ++universitetRequestRef.current;
    setYuklanmoqda(true);
    setXato("");
    fetch(`${API_BASE}/api/admin/universitetlar?token=${encodeURIComponent(token)}`, { cache: "no-store" })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Muassasalar yuklanmadi. Qayta urinib ko‘ring.");
        return data;
      })
      .then((data) => {
        if (requestId !== universitetRequestRef.current) return;
        const rows = Array.isArray(data.universitetlar) ? data.universitetlar : [];
        const seen = new Set();
        setUniversitetlar(rows.filter(item => {
          if (!muassasaFaolmi(item) || item.id == null || seen.has(String(item.id))) return false;
          seen.add(String(item.id));
          return true;
        }));
      })
      .catch((error) => {
        if (requestId !== universitetRequestRef.current) return;
        setUniversitetlar([]);
        setXato(error.message || "Muassasalar yuklanmadi");
      })
      .finally(() => { if (requestId === universitetRequestRef.current) setYuklanmoqda(false); });
  };
  useEffect(() => {
    universitetlarniYukla();
    return () => { universitetRequestRef.current += 1; };
  }, [token]);

  const fakultetlarniYukla = (universitetId) => {
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/admin/fakultetlar?token=${encodeURIComponent(token)}&universitet_id=${universitetId}`)
      .then((r) => r.json()).then((d) => { setFakultetlar(d.fakultetlar || []); setYuklanmoqda(false); }).catch(() => setYuklanmoqda(false));
  };
  const kafedralarniYukla = (fakultetId) => {
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/admin/kafedralar?token=${encodeURIComponent(token)}&fakultet_id=${fakultetId}`)
      .then((r) => r.json()).then((d) => { setKafedralar(d.kafedralar || []); setYuklanmoqda(false); }).catch(() => setYuklanmoqda(false));
  };
  const yonalishlarniYukla = (fakultetId) => {
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/institut/v20/fakultet/${fakultetId}/yonalishlar?token=${encodeURIComponent(token)}`)
      .then(async (r) => { const d = await r.json(); if (!r.ok) throw new Error(d.detail || "Yo‘nalishlar yuklanmadi"); return d; })
      .then((d) => { setYonalishlar(d.yonalishlar || []); setYuklanmoqda(false); })
      .catch((e) => { setXato(e.message); setYonalishlar([]); setYuklanmoqda(false); });
  };
  const guruhlarniYukla = (kafedraId) => {
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/admin/universitet_guruhlari?token=${encodeURIComponent(token)}&kafedra_id=${kafedraId}`)
      .then((r) => r.json()).then((d) => { setGuruhlar(d.guruhlar || []); setYuklanmoqda(false); }).catch(() => setYuklanmoqda(false));
  };

  const universitetOch = (u) => { setTUniversitet(u); setHolat("fakultet"); formniTozala(); fakultetlarniYukla(u.id); };
  const fakultetOch = (f) => {
    setTFakultet(f);
    setHolat("fakultet");
    formniTozala();
    // Fakultetdan institut ish maydoniga to'g'ridan-to'g'ri kiriladi.
    // `holat` ataylab "fakultet" bo'lib qoladi: institutdan qaytilganda
    // foydalanuvchi aynan o'zi kirgan fakultetlar ro'yxatini ko'radi.
    setWorkspaceUniversity({ ...tUniversitet, importFacultyId: f.id });
  };
  const kafedraOch = (k) => { setTKafedra(k); setHolat("guruh"); formniTozala(); guruhlarniYukla(k.id); };

  const universitetSaqla = async () => {
    if (!nomi.trim()) { setXato("Nomini kiriting"); return; }
    setSaqlanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/universitet_yarat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, nomi: nomi.trim(), viloyat: viloyat || undefined, tuman: tuman || undefined, rektor_user_id: rahbar ? rahbar.user_id : undefined, rektor_ismi: !rahbar ? rahbarIsmi.trim() || undefined : undefined }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      if (data.kirish_kodi) setKirishNatija({ fish: rahbarIsmi.trim(), lavozim: "Rektor", kod: data.kirish_kodi });
      formniTozala(); universitetlarniYukla();
    } catch (e) { setXato(e.message); } finally { setSaqlanmoqda(false); }
  };

  const fakultetSaqla = async () => {
    if (!nomi.trim()) { setXato("Nomini kiriting"); return; }
    setSaqlanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/fakultet_yarat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, universitet_id: tUniversitet.id, nomi: nomi.trim(), dekan_user_id: rahbar ? rahbar.user_id : undefined, dekan_ismi: !rahbar ? rahbarIsmi.trim() || undefined : undefined }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      if (data.kirish_kodi) setKirishNatija({ fish: rahbarIsmi.trim(), lavozim: "Dekan", kod: data.kirish_kodi });
      formniTozala(); fakultetlarniYukla(tUniversitet.id);
    } catch (e) { setXato(e.message); } finally { setSaqlanmoqda(false); }
  };

  const kafedraSaqla = async () => {
    if (!nomi.trim()) { setXato("Nomini kiriting"); return; }
    setSaqlanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/kafedra_yarat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, fakultet_id: tFakultet.id, nomi: nomi.trim(), mudir_user_id: rahbar ? rahbar.user_id : undefined, mudir_ismi: !rahbar ? rahbarIsmi.trim() || undefined : undefined }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      if (data.kirish_kodi) setKirishNatija({ fish: rahbarIsmi.trim(), lavozim: "Kafedra mudiri", kod: data.kirish_kodi });
      formniTozala(); kafedralarniYukla(tFakultet.id);
    } catch (e) { setXato(e.message); } finally { setSaqlanmoqda(false); }
  };

  const guruhSaqla = async () => {
    if (!nomi.trim()) { setXato("Nomini kiriting"); return; }
    setSaqlanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/universitet_guruh_yarat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token, kafedra_id: tKafedra.id, nomi: nomi.trim(),
          kurs: kurs ? parseInt(kurs, 10) : undefined, yonalish: yonalish || undefined,
          rahbar_user_id: rahbar ? rahbar.user_id : undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      formniTozala(); guruhlarniYukla(tKafedra.id);
    } catch (e) { setXato(e.message); } finally { setSaqlanmoqda(false); }
  };

  const ortgaQaytish = () => {
    if (holat === "guruh") { setHolat("kafedra"); formniTozala(); }
    else if (holat === "kafedra") { setHolat("fakultet"); formniTozala(); }
    else if (holat === "fakultet") { setHolat("universitet"); formniTozala(); universitetlarniYukla(); }
  };

  useEffect(() => registerPhoneBackHandler("admin-universitetlar-tree", () => {
    // Institut ish maydoni ochiq bo'lsa hodisani uning ichki handlerlariga
    // beramiz. Uning onBack'i workspaceUniversity'ni yopib, shu komponent
    // saqlab turgan fakultetlar ro'yxatiga qaytaradi.
    if (workspaceUniversity) return false;
    if (hayot) { setHayot(null); return true; }
    if (formOchiq) {
      formniTozala();
      return true;
    }
    if (holat !== "universitet") {
      ortgaQaytish();
      return true;
    }
    // Universitetlar ildizida Kabinet o'zining real tab tarixiga qaytadi.
    return false;
  }), [formOchiq, holat, workspaceUniversity, hayot]);

  if (hayot) return <AdminInstitutHayoti token={token} apiBase={API_BASE} universitet={hayot.universitet} initialTab={hayot.tab} onBack={() => { setHayot(null); universitetlarniYukla(); }} />;

  if (workspaceUniversity) {
    return (
      <React.Suspense fallback={<div className="py-12 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>}>
        <InstituteWorkspace
          token={token}
          apiBase={API_BASE}
          initialWorkspace={workspaceUniversity?.turi === "universitet" || !workspaceUniversity?.turi
            ? { turi: "universitet", muassasa_id: workspaceUniversity.id, nomi: workspaceUniversity.nomi }
            : null}
          initialFacultyId={workspaceUniversity.importFacultyId || null}
          onBack={() => setWorkspaceUniversity(null)}
          assignedOnly={false}
          canCreateInstitution={true}
        />
      </React.Suspense>
    );
  }

  const sarlavhalar = { universitet: "🎓 Universitet / Institut", fakultet: `📚 ${tUniversitet?.nomi} — Fakultetlar`, kafedra: `🎓 ${tFakultet?.nomi} — Yo‘nalishlar`, guruh: `👥 ${tKafedra?.nomi} — Guruhlar` };
  const royxat = holat === "universitet" ? universitetlar : holat === "fakultet" ? fakultetlar : holat === "kafedra" ? yonalishlar : guruhlar;

  return (
    <div>
      {holat !== "universitet" && (
        <button onClick={ortgaQaytish} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Ortga")}/></button>
      )}
      <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
          <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{sarlavhalar[holat]}</p>
          <div className="flex flex-wrap gap-2">
            {holat === "kafedra" && tUniversitet && tFakultet && <button onClick={() => setWorkspaceUniversity({ ...tUniversitet, importFacultyId: tFakultet.id })} className="text-xs font-semibold px-3.5 py-1.5 rounded-full border" style={{ borderColor: "#0D7A77", backgroundColor: "#ECF8F4", color: "#0D7A77" }}>{__kbUi("📥 Talabalar va import")}</button>}
            {holat !== "kafedra" && <button onClick={() => setFormOchiq(!formOchiq)} className="text-xs font-semibold px-3.5 py-1.5 rounded-full" style={{ backgroundColor: "#1B4B7A", color: "#fff" }}>
              {formOchiq ? __kbUi("✕ Yopish") : __kbUi("+ Yangi")}
            </button>}
          </div>
        </div>
        {holat === "universitet" && <div className="flex items-center justify-between gap-3 mt-2"><p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Arxivlanmagan universitet va institutlar. Arxiv ro‘yxati profil sozlamalarida.")}</p><button type="button" onClick={universitetlarniYukla} disabled={yuklanmoqda} className="text-xs font-semibold px-3 py-2 rounded-xl border" style={{ borderColor: "#DCE6EA", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Yangilash ↻")}</button></div>}
      </div>

      {formOchiq && (
        <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Nomi")}</label>
          <input type="text" value={nomi} onChange={(e) => setNomi(e.target.value)}
            placeholder={holat === "universitet" ? __kbUi("masalan: Samarqand Davlat Universiteti") : holat === "fakultet" ? __kbUi("masalan: Matematika fakulteti") : holat === "kafedra" ? __kbUi("masalan: Algebra va geometriya kafedrasi") : __kbUi("masalan: 201-guruh")}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />

          {holat === "universitet" && (
            <div className="grid grid-cols-2 gap-2.5 mb-3">
              <div>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Viloyat")}/></label>
                <select value={viloyat} onChange={(e) => { setViloyat(e.target.value); setTuman(""); }}
                  className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                  <option value="">—</option>
                  {VILOYATLAR.map((v) => <option key={v} value={v}>{__kbUi(v)}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Tuman")}/></label>
                <select value={tuman} onChange={(e) => setTuman(e.target.value)} disabled={!viloyat}
                  className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", opacity: viloyat ? 1 : 0.5 }}>
                  <option value="">—</option>
                  {(HUDUDLAR[viloyat] || []).map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            </div>
          )}

          {holat === "guruh" && (
            <div className="grid grid-cols-2 gap-2.5 mb-3">
              <div>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Kurs")}</label>
                <select value={kurs} onChange={(e) => setKurs(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                  <option value="">—</option>
                  {[1, 2, 3, 4, 5, 6].map((k) => <option key={k} value={k}>{__kbUi(k)}{__kbUi("-kurs")}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Yo'nalish")}</label>
                <input type="text" value={yonalish} onChange={(e) => setYonalish(e.target.value)}
                  placeholder={__kbUi("masalan: Matematika")}
                  className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              </div>
            </div>
          )}

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
            {holat === "universitet" ? __kbUi("Rektor (ixtiyoriy)") : holat === "fakultet" ? __kbUi("Dekan (ixtiyoriy)") : holat === "kafedra" ? __kbUi("Kafedra mudiri (ixtiyoriy)") : __kbUi("Guruh kuratori (ixtiyoriy)")}
          </label>
          <DirektorQidiruvi token={token} tanlanganDirektor={rahbar} onTanla={setRahbar} onYangiIsm={setRahbarIsmi} />
          {!rahbar && rahbarIsmi.trim() && <p className="text-xs mb-3" style={{ color: "#0D7A77" }}>{__kbUi("Yangi hisob yaratiladi va 2 oylik bir martalik kirish kodi beriladi.")}</p>}

          {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
          <button onClick={holat === "universitet" ? universitetSaqla : holat === "fakultet" ? fakultetSaqla : holat === "kafedra" ? kafedraSaqla : guruhSaqla}
            disabled={saqlanmoqda}
            className="w-full py-3 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: saqlanmoqda ? 0.7 : 1 }}>
            {saqlanmoqda ? uiT("Saqlanmoqda...") : __kbUi("Yaratish")}
          </button>
        </div>
      )}

      {kirishNatija && <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "#B8DCC8" }}><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold" style={{ color: "#2E7356" }}>{__kbUi("✅ Rahbar biriktirildi")}</p><p className="text-xs mt-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{kirishNatija.fish} · {kirishNatija.lavozim}</p><p className="font-mono font-bold mt-2" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Kirish kodi: ")}{kirishNatija.kod}</p><p className="text-xs mt-1" style={{ color: "#B0553A" }}>{__kbUi("Kod 2 oy amal qiladi. Hozir nusxalab oling.")}</p></div><button onClick={() => setKirishNatija(null)} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>✕</button></div></div>}

      {!formOchiq && xato && <p role="alert" className="rounded-xl border p-3 mb-3 text-sm" style={{ borderColor: "#E8BABA", color: "#B0553A", backgroundColor: "#FFF5F2" }}>{__kbUi(xato)}</p>}
      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : xato && !formOchiq ? null : royxat.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali qo'shilmagan.")}</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {holat === "universitet" && universitetlar.filter((u) => eskiKorsat || Number(u.fakultet_soni) > 0 || u.rektor_ismi || u.talaba_paroli || Number(u.talaba_soni) > 0).map((u) => (
            <div key={u.id} className="rounded-xl bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <button onClick={() => universitetOch(u)} className="w-full text-left rounded-xl p-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{u.nomi}{!Number(u.fakultet_soni) && !u.rektor_ismi && <span className="ml-2 text-[10px] font-bold px-1.5 py-0.5 rounded" style={{ background: "var(--ui-legacy-background-f1efe9, #F1EFE9)", color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("bo‘sh")}</span>}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{[u.viloyat, u.tuman].filter(Boolean).join(", ") || __kbUi("Hudud ko'rsatilmagan")} · {u.fakultet_soni}{__kbUi(" fakultet")}</p>
                <p className="text-xs mt-1" style={{ color: u.rektor_ismi ? "#3B6D11" : "#B0553A" }}>{u.rektor_ismi ? __kbUi(`👤 Rektor: ${u.rektor_ismi}`) : __kbUi("⚠️ Rektor belgilanmagan")}</p>
              </div>
              <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
            </button>
            <div className="flex flex-wrap gap-2 px-4 pb-3">
              <button type="button" onClick={() => setHayot({ universitet: u, tab: "talabalar" })} className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-xl" style={{ background: "#F1ECFB", color: "#5B3FA0" }}>👥 {__kbUi("Talabalar — kurs va guruhlar")}<b className="ml-1 px-1.5 rounded-full" style={{ background: "#fff" }}>{Number(u.talaba_soni) || 0}</b></button>
              <button type="button" onClick={() => setHayot({ universitet: u, tab: "sahifa" })} className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-xl" style={{ background: "#FFF4DE", color: "#94600F" }}>📅 {__kbUi("Muhim sanalar va sahifa")}</button>
            </div>
            <TalabaParolQatori token={token} universitet={u} onYangilandi={(yangi) => setUniversitetlar((old) => old.map((x) => (x.id === yangi.id ? { ...x, ...yangi } : x)))} />
            </div>
          ))}
          {holat === "universitet" && universitetlar.some((u) => !Number(u.fakultet_soni) && !u.rektor_ismi) && <button type="button" onClick={() => setEskiKorsat((v) => !v)} className="w-full text-xs font-semibold py-2 rounded-xl border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", color: "var(--ui-legacy-color-8a8578, #8A8578)", background: "var(--ui-legacy-background-faf9f6, #FAF9F6)" }}>{eskiKorsat ? __kbUi("Bo‘sh yozuvlarni yashirish") : __kbUi(`Bo‘sh yozuvlarni ko‘rsatish — fakultetsiz va rektorsiz (${universitetlar.filter((u) => !Number(u.fakultet_soni) && !u.rektor_ismi).length})`)}</button>}
          {holat === "fakultet" && fakultetlar.map((f) => (
            <button key={f.id} onClick={() => fakultetOch(f)} className="w-full text-left rounded-xl p-4 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div>
                <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{f.nomi}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{f.kafedra_soni}{__kbUi(" kafedra")}</p>
                <p className="text-xs mt-1" style={{ color: f.dekan_ismi ? "#3B6D11" : "#B0553A" }}>{f.dekan_ismi ? __kbUi(`👤 Dekan: ${f.dekan_ismi}`) : __kbUi("⚠️ Dekan belgilanmagan")}</p>
              </div>
              <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
            </button>
          ))}
          {holat === "kafedra" && yonalishlar.map((y) => (
            <button key={y.id} onClick={() => setWorkspaceUniversity({ ...tUniversitet, importFacultyId: tFakultet.id })} className="w-full text-left rounded-xl p-4 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div>
                <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{y.nomi}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{y.daraja || __kbUi("Bakalavriat")} · {y.talim_shakllari || __kbUi("Shakl belgilanmagan")} · {y.talim_tillari || __kbUi("Til belgilanmagan")}</p>
                <p className="text-xs mt-1 font-semibold" style={{ color: "#0D7A77" }}>👥 {y.talaba_soni || 0}{__kbUi(" talaba · 📄 ")}{y.hujjat_soni || 0}{__kbUi(" hujjat · ✅ ")}{y.baza_soni || 0}{__kbUi(" bazada")}</p>
              </div>
              <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
            </button>
          ))}
          {holat === "guruh" && guruhlar.map((g) => (
            <div key={g.id} className="rounded-xl p-4 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{g.nomi}</p>
              <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
                {g.kurs ? __kbUi(`${g.kurs}-kurs`) : __kbUi("")}{g.yonalish ? __kbUi(` · ${g.yonalish}`) : __kbUi("")} · {g.talaba_soni}{__kbUi(" talaba")}</p>
              <p className="text-xs mt-1" style={{ color: g.rahbar_ismi ? "#3B6D11" : "#B0553A" }}>{g.rahbar_ismi ? __kbUi(`👤 Kurator: ${g.rahbar_ismi}`) : __kbUi("⚠️ Kurator belgilanmagan")}</p>
              <p className="text-xs font-mono mt-1" style={{ color: "#8A5A1C" }}>{__kbUi("🔐 Qo'shilish paroli: ")}{__kbUi(g.qoshilish_paroli)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MaktabOdamQidiruvi({ token, maktabId, tanlanganOdam, onTanla }) {
  useKbInterfaceLocale();
  const [ism, setIsm] = useState("");
  const [natijalar, setNatijalar] = useState([]);

  useEffect(() => {
    if (ism.trim().length < 2) { setNatijalar([]); return; }
    const kechiktirish = setTimeout(() => {
      fetch(`${API_BASE}/api/maktab/odam_qidir?token=${encodeURIComponent(token)}&maktab_id=${maktabId}&ism=${encodeURIComponent(ism.trim())}`)
        .then((r) => r.json())
        .then((d) => setNatijalar(d.natijalar || []))
        .catch(() => {});
    }, 400);
    return () => clearTimeout(kechiktirish);
  }, [ism, token, maktabId]);

  if (tanlanganOdam) {
    return (
      <div className="flex items-center justify-between px-3 py-2 rounded-lg mb-2" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
        <span className="text-xs font-medium" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>👤 {tanlanganOdam.full_name}</span>
        <button onClick={() => onTanla(null)} className="text-xs font-medium" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>✕</button>
      </div>
    );
  }

  return (
    <div className="mb-2">
      <input type="text" value={ism} onChange={(e) => setIsm(e.target.value)}
        placeholder={__kbUi("Ism bo'yicha qidiring...")}
        className="w-full px-3.5 py-2 rounded-lg border text-xs" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
      {natijalar.length > 0 && (
        <div className="mt-1 space-y-1">
          {natijalar.map((o) => (
            <button key={o.user_id} onClick={() => { onTanla(o); setIsm(""); setNatijalar([]); }}
              className="w-full flex items-center px-3 py-1.5 rounded-lg text-left" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
              <span className="text-xs" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{o.full_name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

const HAFTA_KUNLARI_RO = [
  { raqam: 1, nomi: "Dushanba" }, { raqam: 2, nomi: "Seshanba" }, { raqam: 3, nomi: "Chorshanba" },
  { raqam: 4, nomi: "Payshanba" }, { raqam: 5, nomi: "Juma" }, { raqam: 6, nomi: "Shanba" },
];
const TADBIR_TURLARI_RO = { tadbir: "🎉 Tadbir", majlis: "👥 Majlis", tatil: "🏖 Ta'til" };

function RejalashtirishBolimi({ token, maktabId, onOrtga }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [tepaKorinish, setTepaKorinish] = useState("taqvim"); // "taqvim" | "jadval"

  const [tadbirlar, setTadbirlar] = useState([]);
  const [tadbirYuklanmoqda, setTadbirYuklanmoqda] = useState(true);
  const [formOchiq, setFormOchiq] = useState(false);
  const [turi, setTuri] = useState("tadbir");
  const [sarlavha, setSarlavha] = useState("");
  const [tavsif, setTavsif] = useState("");
  const [boshlanishSana, setBoshlanishSana] = useState("");
  const [tugashSana, setTugashSana] = useState("");
  const [vaqt, setVaqt] = useState("");
  const [saqlanmoqda, setSaqlanmoqda] = useState(false);
  const [xato, setXato] = useState("");

  const [sinflar, setSinflar] = useState([]);
  const [sinflarYuklanmoqda, setSinflarYuklanmoqda] = useState(true);
  const [tanlanganSinf, setTanlanganSinf] = useState(null);
  const [jadval, setJadval] = useState(null);
  const [jadvalYuklanmoqda, setJadvalYuklanmoqda] = useState(false);
  const [tahrirlanayotganSlot, setTahrirlanayotganSlot] = useState(null);
  const [slotFan, setSlotFan] = useState("");
  const [slotXona, setSlotXona] = useState("");
  const [slotDavri, setSlotDavri] = useState("haftalik");
  const [slotSana, setSlotSana] = useState(new Date().toISOString().slice(0, 10));
  const [slotChorak, setSlotChorak] = useState("1");

  const tadbirlarniYukla = () => {
    setTadbirYuklanmoqda(true);
    fetch(`${API_BASE}/api/maktab/tadbirlar?token=${encodeURIComponent(token)}&maktab_id=${maktabId}`)
      .then((r) => r.json())
      .then((d) => { setTadbirlar(d.tadbirlar || []); setTadbirYuklanmoqda(false); })
      .catch(() => setTadbirYuklanmoqda(false));
  };
  useEffect(tadbirlarniYukla, [token, maktabId]);

  useEffect(() => {
    setSinflarYuklanmoqda(true);
    fetch(`${API_BASE}/api/maktab/dashboard?token=${encodeURIComponent(token)}&maktab_id=${maktabId}`)
      .then((r) => r.json())
      .then((d) => { setSinflar(d.sinflar || []); setSinflarYuklanmoqda(false); })
      .catch(() => setSinflarYuklanmoqda(false));
  }, [token, maktabId]);

  const tadbirSaqla = async () => {
    if (!sarlavha.trim()) { setXato("Sarlavhani kiriting"); return; }
    if (!boshlanishSana) { setXato("Sanani tanlang"); return; }
    setSaqlanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/maktab/tadbir_qosh`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token, maktab_id: maktabId, turi, sarlavha: sarlavha.trim(), tavsif: tavsif || undefined,
          boshlanish_sana: boshlanishSana, tugash_sana: tugashSana || undefined, vaqt: vaqt || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setSarlavha(""); setTavsif(""); setBoshlanishSana(""); setTugashSana(""); setVaqt(""); setFormOchiq(false);
      tadbirlarniYukla();
    } catch (e) { setXato(e.message); } finally { setSaqlanmoqda(false); }
  };

  const tadbirOchir = async (id) => {
    await fetch(`${API_BASE}/api/maktab/tadbir_ochir?token=${encodeURIComponent(token)}&tadbir_id=${id}`, { method: "DELETE" });
    tadbirlarniYukla();
  };

  const sinfOch = (s) => {
    setTanlanganSinf(s);
    setJadvalYuklanmoqda(true);
    fetch(`${API_BASE}/api/maktab/dars_jadvali?token=${encodeURIComponent(token)}&sinf_id=${s.id}`)
      .then((r) => r.json())
      .then((d) => { setJadval(d); setJadvalYuklanmoqda(false); })
      .catch(() => setJadvalYuklanmoqda(false));
  };

  const slotniOch = (kun, darsRaqami, mavjudSlot) => {
    setTahrirlanayotganSlot({ kun, dars_raqami: darsRaqami });
    setSlotFan(mavjudSlot ? mavjudSlot.fan : "");
    setSlotXona(mavjudSlot ? mavjudSlot.xona || "" : "");
    setSlotDavri(mavjudSlot?.amal_turi || "haftalik");
    setSlotSana(mavjudSlot?.amal_sana || new Date().toISOString().slice(0, 10));
    setSlotChorak(String(mavjudSlot?.chorak || 1));
  };

  const slotSaqla = async () => {
    if (!slotFan.trim()) return;
    await fetch(`${API_BASE}/api/maktab/dars_jadvali_belgila`, {
      method: "PUT", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token, sinf_id: tanlanganSinf.id, kun: tahrirlanayotganSlot.kun,
        dars_raqami: tahrirlanayotganSlot.dars_raqami, fan: slotFan.trim(), xona: slotXona || undefined,
        amal_turi: slotDavri,
        amal_sana: slotDavri === "kunlik" ? slotSana : undefined,
        chorak: slotDavri === "choraklik" ? Number(slotChorak) : undefined,
      }),
    });
    setTahrirlanayotganSlot(null);
    sinfOch(tanlanganSinf);
  };

  const slotOchir = async () => {
    await fetch(`${API_BASE}/api/maktab/dars_jadvali_ochir?token=${encodeURIComponent(token)}&sinf_id=${tanlanganSinf.id}&kun=${tahrirlanayotganSlot.kun}&dars_raqami=${tahrirlanayotganSlot.dars_raqami}`, { method: "DELETE" });
    setTahrirlanayotganSlot(null);
    sinfOch(tanlanganSinf);
  };

  if (tanlanganSinf) {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => { setTanlanganSinf(null); setJadval(null); }} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Sinflar")}/></button>
        <h1 className="text-xl font-bold mb-5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>🗓 {tanlanganSinf.sinf}-{tanlanganSinf.harf}{__kbUi(" jadvali")}</h1>

        {tahrirlanayotganSlot && (
          <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "#1B4B7A" }}>
            <p className="text-xs font-semibold mb-2" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
              {__kbUi(HAFTA_KUNLARI_RO.find((k) => k.raqam === tahrirlanayotganSlot.kun)?.nomi)} · {tahrirlanayotganSlot.dars_raqami}{__kbUi("-dars")}</p>
            <input type="text" value={slotFan} onChange={(e) => setSlotFan(e.target.value)} placeholder={__kbUi("Fan nomi")}
              className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            <input type="text" value={slotXona} onChange={(e) => setSlotXona(e.target.value)} placeholder={__kbUi("Xona (ixtiyoriy)")}
              className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            <p className="text-xs font-semibold mb-2" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Dars qancha muddat ko‘rinsin?")}</p>
            <div className="grid grid-cols-3 gap-1.5 mb-3">
              {[["kunlik","Bir kun"],["haftalik","Har hafta"],["choraklik","Chorak"]].map(([k,n]) => <button key={k} type="button" onClick={() => setSlotDavri(k)} className="rounded-lg py-2 text-xs font-semibold" style={slotDavri === k ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>{slotDavri === k ? __kbUi("✓ ") : __kbUi("")}{__kbUi(n)}</button>)}
            </div>
            {slotDavri === "kunlik" && <input type="date" value={slotSana} onChange={(e) => setSlotSana(e.target.value)} className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />}
            {slotDavri === "choraklik" && <select value={slotChorak} onChange={(e) => setSlotChorak(e.target.value)} className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3 bg-white" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}><option value="1">{__kbUi("1-chorak")}</option><option value="2">{__kbUi("2-chorak")}</option><option value="3">{__kbUi("3-chorak")}</option><option value="4">{__kbUi("4-chorak")}</option></select>}
            <div className="flex gap-2">
              <button onClick={slotSaqla} className="flex-1 py-2.5 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A" }}><InterfaceText text={__kbUi("Saqlash")}/></button>
              <button onClick={slotOchir} className="px-4 py-2.5 rounded-xl font-medium text-sm" style={{ backgroundColor: "var(--ui-legacy-background-fff, #fff)", color: "#A32D2D", border: "1px solid #E5E1D8" }}>{__kbUi("Tozalash")}</button>
              <button onClick={() => setTahrirlanayotganSlot(null)} className="px-4 py-2.5 rounded-xl font-medium text-sm" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Bekor")}</button>
            </div>
          </div>
        )}

        {jadvalYuklanmoqda ? (
          <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
        ) : (
          <div className="space-y-4">
            {HAFTA_KUNLARI_RO.map((kun) => (
              <div key={kun.raqam}>
                <p className="text-sm font-semibold mb-2" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(kun.nomi)}</p>
                <div className="space-y-1.5">
                  {[1, 2, 3, 4, 5, 6, 7].map((darsRaqami) => {
                    const slot = (jadval?.slotlar || []).find((s) => s.kun === kun.raqam && s.dars_raqami === darsRaqami);
                    return (
                      <button key={darsRaqami} onClick={() => slotniOch(kun.raqam, darsRaqami, slot)}
                        className="w-full text-left rounded-lg px-3 py-2 flex items-center gap-2"
                        style={{ backgroundColor: slot ? "#EAF1F7" : "#F7F5F0" }}>
                        <span className="text-xs font-bold w-4 shrink-0" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi(darsRaqami)}</span>
                        <span className="text-xs" style={{ color: slot ? "#1B4B7A" : "#8A8578" }}>
                          {slot ? __kbUi(`${slot.fan}${slot.xona ? ` · ${slot.xona}` : ""} · ${slot.amal_turi === "kunlik" ? slot.amal_sana : slot.amal_turi === "choraklik" ? `${slot.chorak}-chorak` : "har hafta"}`) : __kbUi("— bo'sh —")}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("To'garaklarim")}</button>
      <h1 className="text-xl font-bold mb-4" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📅 Rejalashtirish")}</h1>

      <div className="flex gap-2 mb-4">
        <button onClick={() => setTepaKorinish("taqvim")}
          className="flex-1 py-2 rounded-lg text-xs font-semibold"
          style={tepaKorinish === "taqvim" ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>{__kbUi("📅 Taqvim")}</button>
        <button onClick={() => setTepaKorinish("jadval")}
          className="flex-1 py-2 rounded-lg text-xs font-semibold"
          style={tepaKorinish === "jadval" ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>{__kbUi("🗓 Dars jadvali")}</button>
      </div>

      {tepaKorinish === "taqvim" ? (
        <>
          <div className="flex items-center justify-between mb-2.5">
            <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Kelayotgan tadbirlar")}</p>
            <button onClick={() => setFormOchiq(!formOchiq)} className="text-xs font-semibold px-3.5 py-1.5 rounded-full" style={{ backgroundColor: "#1B4B7A", color: "#fff" }}>
              {formOchiq ? __kbUi("✕ Yopish") : __kbUi("+ Yangi")}
            </button>
          </div>

          {formOchiq && (
            <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div className="flex gap-1.5 mb-2.5">
                {Object.entries(TADBIR_TURLARI_RO).map(([k, v]) => (
                  <button key={k} onClick={() => setTuri(k)}
                    className="flex-1 py-2 rounded-lg text-xs font-semibold"
                    style={turi === k ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>
                    {__kbUi(v)}
                  </button>
                ))}
              </div>
              <input type="text" value={sarlavha} onChange={(e) => setSarlavha(e.target.value)} placeholder={__kbUi("Sarlavha")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              <input type="text" value={tavsif} onChange={(e) => setTavsif(e.target.value)} placeholder={__kbUi("Tavsif (ixtiyoriy)")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              <div className="grid grid-cols-2 gap-2.5 mb-2.5">
                <div>
                  <label className="text-xs font-medium mb-1 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Boshlanish sanasi")}</label>
                  <input type="date" value={boshlanishSana} onChange={(e) => setBoshlanishSana(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                </div>
                <div>
                  <label className="text-xs font-medium mb-1 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Tugash sanasi (ixtiyoriy)")}</label>
                  <input type="date" value={tugashSana} onChange={(e) => setTugashSana(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                </div>
              </div>
              {turi !== "tatil" && (
                <input type="text" value={vaqt} onChange={(e) => setVaqt(e.target.value)} placeholder={__kbUi("Vaqt (masalan 14:00, ixtiyoriy)")}
                  className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              )}
              {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
              <button onClick={tadbirSaqla} disabled={saqlanmoqda}
                className="w-full py-3 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: saqlanmoqda ? 0.7 : 1 }}>
                {saqlanmoqda ? uiT("Saqlanmoqda...") : uiT("Qo'shish")}
              </button>
            </div>
          )}

          {tadbirYuklanmoqda ? (
            <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
          ) : tadbirlar.length === 0 ? (
            <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Kelayotgan tadbir yo'q.")}</p>
            </div>
          ) : (
            <div className="space-y-2">
              {tadbirlar.map((t) => (
                <div key={t.id} className="rounded-xl p-3.5 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(TADBIR_TURLARI_RO[t.turi])} · {t.sarlavha}</p>
                    <button onClick={() => tadbirOchir(t.id)} className="text-xs" style={{ color: "#A32D2D" }}>✕</button>
                  </div>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
                    {t.boshlanish_sana}{t.tugash_sana ? __kbUi(` — ${t.tugash_sana}`) : __kbUi("")}{t.vaqt ? __kbUi(` · ${t.vaqt}`) : __kbUi("")}
                  </p>
                  {t.tavsif && <p className="text-xs mt-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{t.tavsif}</p>}
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        <>
          <p className="text-sm font-semibold mb-2.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Sinfni tanlang")}</p>
          {sinflarYuklanmoqda ? (
            <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
          ) : (
            <div className="space-y-2">
              {sinflar.map((s) => (
                <button key={s.id} onClick={() => sinfOch(s)}
                  className="w-full text-left rounded-xl p-3.5 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                  <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{s.sinf}-{s.harf}</p>
                  <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function HujjatlarBolimi({ token, maktabId, onOrtga }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [hujjatlar, setHujjatlar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [formOchiq, setFormOchiq] = useState(false);
  const [nomi, setNomi] = useState("");
  const [turi, setTuri] = useState("buyruq");
  const [izoh, setIzoh] = useState("");
  const [tanlanganFayl, setTanlanganFayl] = useState(null);
  const [yuklanyapti, setYuklanyapti] = useState(false);
  const [xato, setXato] = useState("");

  const TURLAR = {
    buyruq: "📋 Buyruq", hisobot: "📊 Hisobot", sertifikat: "🏅 Sertifikat",
    xodim_hujjati: "👤 Xodim hujjati", oquvchi_hujjati: "🎓 O'quvchi hujjati", boshqa: "📁 Boshqa",
  };

  const yukla = () => {
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/maktab/hujjatlar?token=${encodeURIComponent(token)}&maktab_id=${maktabId}`)
      .then((r) => r.json())
      .then((d) => { setHujjatlar(d.hujjatlar || []); setYuklanmoqda(false); })
      .catch(() => setYuklanmoqda(false));
  };
  useEffect(yukla, [token, maktabId]);

  const hujjatYukla = async () => {
    if (!nomi.trim()) { setXato("Hujjat nomini kiriting"); return; }
    if (!tanlanganFayl) { setXato("Faylni tanlang"); return; }
    setYuklanyapti(true); setXato("");
    try {
      const formData = new FormData();
      formData.append("fayl", tanlanganFayl);
      const params = new URLSearchParams({ token, maktab_id: maktabId, nomi: nomi.trim(), turi, izoh: izoh || "" });
      const res = await fetch(`${API_BASE}/api/maktab/hujjat_yukla?${params.toString()}`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setNomi(""); setIzoh(""); setTanlanganFayl(null); setFormOchiq(false);
      yukla();
    } catch (e) { setXato(e.message); } finally { setYuklanyapti(false); }
  };

  const hujjatniYukleboLish = (h) => {
    window.open(`${API_BASE}/api/maktab/hujjat_yukleb_olish?token=${encodeURIComponent(token)}&hujjat_id=${h.id}`, "_blank");
  };

  const hujjatOchir = async (id) => {
    await fetch(`${API_BASE}/api/maktab/hujjat_ochir?token=${encodeURIComponent(token)}&hujjat_id=${id}`, { method: "DELETE" });
    yukla();
  };

  const hajmFormat = (baytlar) => {
    if (!baytlar) return "";
    if (baytlar < 1024 * 1024) return `${Math.round(baytlar / 1024)} KB`;
    return `${(baytlar / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("To'garaklarim")}</button>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-xl font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>🗂 <InterfaceText text={__kbUi("Hujjatlar")}/></h1>
        <button onClick={() => setFormOchiq(!formOchiq)} className="text-xs font-semibold px-3.5 py-1.5 rounded-full" style={{ backgroundColor: "#1B4B7A", color: "#fff" }}>
          {formOchiq ? __kbUi("✕ Yopish") : __kbUi("+ Yuklash")}
        </button>
      </div>
      <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{hujjatlar.length}{__kbUi(" ta hujjat.")}</p>

      {formOchiq && (
        <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <input type="text" value={nomi} onChange={(e) => setNomi(e.target.value)} placeholder={__kbUi("Hujjat nomi")}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          <select value={turi} onChange={(e) => setTuri(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            {Object.entries(TURLAR).map(([k, v]) => <option key={k} value={k}>{__kbUi(v)}</option>)}
          </select>
          <input type="text" value={izoh} onChange={(e) => setIzoh(e.target.value)} placeholder={__kbUi("Izoh (ixtiyoriy)")}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          <label className="w-full py-3 rounded-xl font-medium text-sm flex items-center justify-center gap-2 cursor-pointer border-2 border-dashed mb-3"
            style={{ borderColor: "#C4BFAF", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
            {tanlanganFayl ? __kbUi(`📎 ${tanlanganFayl.name}`) : __kbUi("📤 Fayl tanlash (10 MB gacha)")}
            <input type="file" onChange={(e) => setTanlanganFayl(e.target.files[0] || null)} className="hidden" />
          </label>
          {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
          <button onClick={hujjatYukla} disabled={yuklanyapti}
            className="w-full py-3 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: yuklanyapti ? 0.7 : 1 }}>
            {yuklanyapti ? uiT("Yuklanmoqda...") : uiT("Yuklash")}
          </button>
        </div>
      )}

      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : hujjatlar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali hujjat yuklanmagan.")}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {hujjatlar.map((h) => (
            <div key={h.id} className="rounded-xl p-3.5 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{TURLAR[h.turi] || h.turi} · {h.nomi}</p>
              </div>
              <p className="text-xs mb-2.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
                {h.fayl_nomi} · {__kbUi(hajmFormat(h.fayl_hajmi))} · {h.yuklagan_ismi || __kbUi("?")}{h.izoh ? __kbUi(` · ${h.izoh}`) : __kbUi("")}
              </p>
              <div className="flex gap-2">
                <button onClick={() => hujjatniYukleboLish(h)} className="flex-1 py-1.5 rounded-lg text-xs font-semibold" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>⬇ <InterfaceText text={__kbUi("Yuklab olish")}/></button>
                <button onClick={() => hujjatOchir(h.id)} className="px-3 py-1.5 rounded-lg text-xs font-medium" style={{ backgroundColor: "var(--ui-legacy-background-fff, #fff)", color: "#A32D2D", border: "1px solid #E5E1D8" }}>
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MoliyaBolimi({ token, maktabId, onOrtga }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [oy, setOy] = useState(new Date().toISOString().slice(0, 7));
  const [malumot, setMalumot] = useState(null);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [formOchiq, setFormOchiq] = useState(false);
  const [turi, setTuri] = useState("chiqim");
  const [kategoriya, setKategoriya] = useState("");
  const [summa, setSumma] = useState("");
  const [izoh, setIzoh] = useState("");
  const [saqlanmoqda, setSaqlanmoqda] = useState(false);
  const [xato, setXato] = useState("");

  const KATEGORIYALAR = {
    kirim: ["Homiylik", "Grant", "Boshqa kirim"],
    chiqim: ["Ish haqi", "Jihoz/inventar", "Ta'mirlash", "Kommunal", "O'quv materiallari", "Boshqa chiqim"],
  };

  const yukla = () => {
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/maktab/moliya?token=${encodeURIComponent(token)}&maktab_id=${maktabId}&oy=${oy}`)
      .then((r) => r.json())
      .then((d) => { setMalumot(d); setYuklanmoqda(false); })
      .catch(() => setYuklanmoqda(false));
  };
  useEffect(yukla, [token, maktabId, oy]);

  const yozuvSaqla = async () => {
    if (!kategoriya) { setXato("Kategoriyani tanlang"); return; }
    if (!summa || parseInt(summa, 10) <= 0) { setXato("Summani kiriting"); return; }
    setSaqlanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/maktab/moliya_yozuv_qosh`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, maktab_id: maktabId, turi, kategoriya, summa: parseInt(summa, 10), izoh: izoh || undefined }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setKategoriya(""); setSumma(""); setIzoh(""); setFormOchiq(false);
      yukla();
    } catch (e) { setXato(e.message); } finally { setSaqlanmoqda(false); }
  };

  const yozuvOchir = async (id) => {
    await fetch(`${API_BASE}/api/maktab/moliya_yozuv_ochir?token=${encodeURIComponent(token)}&yozuv_id=${id}`, { method: "DELETE" });
    yukla();
  };

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("To'garaklarim")}</button>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>💰 <InterfaceText text={__kbUi("Moliya")}/></h1>
        <input type="month" value={oy} onChange={(e) => setOy(e.target.value)}
          className="px-3 py-1.5 rounded-lg border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
      </div>

      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : (
        <>
          <div className="rounded-2xl p-4 mb-4" style={{ backgroundColor: malumot.balans >= 0 ? "#EAF3DE" : "#FCEBEB" }}>
            <p className="text-xs font-medium mb-1" style={{ color: malumot.balans >= 0 ? "#3B6D11" : "#A32D2D" }}>{__kbUi("Oylik balans")}</p>
            <p className="text-2xl font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(malumot.balans.toLocaleString())}{__kbUi(" so'm")}</p>
          </div>

          <div className="grid grid-cols-2 gap-2.5 mb-4">
            <div className="rounded-xl p-3.5 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <p className="text-xs mb-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Jami kirim")}</p>
              <p className="text-lg font-bold" style={{ color: "#3B6D11" }}>{__kbUi(malumot.jami_kirim.toLocaleString())}</p>
              <p className="text-xs mt-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("O'quvchi: ")}{__kbUi(malumot.oquvchi_kirim.toLocaleString())}{__kbUi(" · Boshqa: ")}{__kbUi(malumot.boshqa_kirim.toLocaleString())}
              </p>
            </div>
            <div className="rounded-xl p-3.5 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <p className="text-xs mb-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Chiqim")}</p>
              <p className="text-lg font-bold" style={{ color: "#A32D2D" }}>{__kbUi(malumot.chiqim.toLocaleString())}</p>
            </div>
          </div>

          <div className="flex items-center justify-between mb-2.5">
            <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📝 Qo'lda kiritilgan yozuvlar")}</p>
            <button onClick={() => setFormOchiq(!formOchiq)} className="text-xs font-semibold px-3.5 py-1.5 rounded-full" style={{ backgroundColor: "#1B4B7A", color: "#fff" }}>
              {formOchiq ? __kbUi("✕ Yopish") : __kbUi("+ Yozuv")}
            </button>
          </div>

          {formOchiq && (
            <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div className="flex gap-2 mb-2.5">
                <button onClick={() => { setTuri("kirim"); setKategoriya(""); }}
                  className="flex-1 py-2 rounded-lg text-xs font-semibold"
                  style={turi === "kirim" ? { backgroundColor: "#3B6D11", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>{__kbUi("➕ Kirim")}</button>
                <button onClick={() => { setTuri("chiqim"); setKategoriya(""); }}
                  className="flex-1 py-2 rounded-lg text-xs font-semibold"
                  style={turi === "chiqim" ? { backgroundColor: "#A32D2D", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>{__kbUi("➖ Chiqim")}</button>
              </div>
              <select value={kategoriya} onChange={(e) => setKategoriya(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                <option value="">{__kbUi("Kategoriyani tanlang")}</option>
                {KATEGORIYALAR[turi].map((k) => <option key={k} value={k}>{__kbUi(k)}</option>)}
              </select>
              <input type="number" min="1" value={summa} onChange={(e) => setSumma(e.target.value)} placeholder={__kbUi("Summa (so'm)")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              <input type="text" value={izoh} onChange={(e) => setIzoh(e.target.value)} placeholder={__kbUi("Izoh (ixtiyoriy)")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
              <button onClick={yozuvSaqla} disabled={saqlanmoqda}
                className="w-full py-3 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: saqlanmoqda ? 0.7 : 1 }}>
                {saqlanmoqda ? uiT("Saqlanmoqda...") : uiT("Qo'shish")}
              </button>
            </div>
          )}

          <div className="space-y-2">
            {malumot.yozuvlar.map((y) => (
              <div key={y.id} className="rounded-xl p-3.5 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                <div>
                  <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{y.kategoriya}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{y.sana}{y.izoh ? __kbUi(` · ${y.izoh}`) : __kbUi("")}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold" style={{ color: y.turi === "kirim" ? "#3B6D11" : "#A32D2D" }}>
                    {y.turi === "kirim" ? __kbUi("+") : __kbUi("-")}{__kbUi(y.summa.toLocaleString())}
                  </span>
                  <button onClick={() => yozuvOchir(y.id)} className="text-xs" style={{ color: "#A32D2D" }}>✕</button>
                </div>
              </div>
            ))}
            {malumot.yozuvlar.length === 0 && <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bu oy uchun qo'lda kiritilgan yozuv yo'q.")}</p>}
          </div>
        </>
      )}
    </div>
  );
}

function KutubxonaBolimi({ token, maktabId, onOrtga }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [kitoblar, setKitoblar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [formOchiq, setFormOchiq] = useState(false);
  const [nomi, setNomi] = useState("");
  const [muallif, setMuallif] = useState("");
  const [janr, setJanr] = useState("");
  const [nusxaSoni, setNusxaSoni] = useState("1");
  const [elektronHavola, setElektronHavola] = useState("");
  const [saqlanmoqda, setSaqlanmoqda] = useState(false);
  const [xato, setXato] = useState("");
  const [tanlanganKitob, setTanlanganKitob] = useState(null);
  const [tarix, setTarix] = useState(null);
  const [berishOchiq, setBerishOchiq] = useState(false);
  const [tanlanganOdam, setTanlanganOdam] = useState(null);

  const kitoblarniYukla = () => {
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/maktab/kutubxona?token=${encodeURIComponent(token)}&maktab_id=${maktabId}`)
      .then((r) => r.json())
      .then((d) => { setKitoblar(d.kitoblar || []); setYuklanmoqda(false); })
      .catch(() => setYuklanmoqda(false));
  };
  useEffect(kitoblarniYukla, [token, maktabId]);

  const kitobSaqla = async () => {
    if (!nomi.trim()) { setXato("Kitob nomini kiriting"); return; }
    setSaqlanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/maktab/kitob_qosh`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token, maktab_id: maktabId, nomi: nomi.trim(), muallif: muallif || undefined,
          janr: janr || undefined, nusxa_soni: parseInt(nusxaSoni, 10) || 1, elektron_havola: elektronHavola || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setNomi(""); setMuallif(""); setJanr(""); setNusxaSoni("1"); setElektronHavola(""); setFormOchiq(false);
      kitoblarniYukla();
    } catch (e) { setXato(e.message); } finally { setSaqlanmoqda(false); }
  };

  const tarixniYukla = (kitobId) => {
    fetch(`${API_BASE}/api/maktab/kitob_tarixi?token=${encodeURIComponent(token)}&kitob_id=${kitobId}`)
      .then((r) => r.json())
      .then((d) => setTarix(d.tarix || []))
      .catch(() => {});
  };

  const kitobOch = (k) => { setTanlanganKitob(k); tarixniYukla(k.id); };

  const kitobBer = async () => {
    if (!tanlanganOdam) return;
    setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/maktab/kitob_berish`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, kitob_id: tanlanganKitob.id, user_id: tanlanganOdam.user_id }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setBerishOchiq(false); setTanlanganOdam(null);
      tarixniYukla(tanlanganKitob.id); kitoblarniYukla();
    } catch (e) { setXato(e.message); }
  };

  const kitobniQaytar = async (ijaraId) => {
    await fetch(`${API_BASE}/api/maktab/kitob_qaytarish?token=${encodeURIComponent(token)}&ijara_id=${ijaraId}`, { method: "POST" });
    tarixniYukla(tanlanganKitob.id); kitoblarniYukla();
  };

  if (tanlanganKitob) {
    const bosh = tanlanganKitob.nusxa_soni - tanlanganKitob.band_soni;
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => { setTanlanganKitob(null); setTarix(null); setBerishOchiq(false); setTanlanganOdam(null); }} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Kutubxona")}/></button>
        <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{tanlanganKitob.nomi}</h1>
        <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
          {tanlanganKitob.muallif || __kbUi("Muallif noma'lum")}{tanlanganKitob.janr ? __kbUi(` · ${tanlanganKitob.janr}`) : __kbUi("")} · {bosh}/{tanlanganKitob.nusxa_soni}{__kbUi(" nusxa bo'sh")}</p>
        {tanlanganKitob.elektron_havola && (
          <a href={tanlanganKitob.elektron_havola} target="_blank" rel="noreferrer" className="block text-xs mb-4" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("🔗 Elektron nusxa havolasi")}</a>
        )}

        {bosh > 0 && (
          <>
            <button onClick={() => setBerishOchiq(!berishOchiq)}
              className="w-full py-2.5 rounded-xl font-semibold text-sm mb-3" style={{ backgroundColor: "#1B4B7A", color: "#fff" }}>{__kbUi("📤 Kitob berish")}</button>
            {berishOchiq && (
              <div className="rounded-xl p-3.5 mb-4" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                <MaktabOdamQidiruvi token={token} maktabId={maktabId} tanlanganOdam={tanlanganOdam} onTanla={setTanlanganOdam} />
                <button onClick={kitobBer} disabled={!tanlanganOdam}
                  className="w-full py-2.5 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: tanlanganOdam ? 1 : 0.5 }}>{__kbUi("Berish")}</button>
                {xato && <p className="text-xs mt-2" style={{ color: "#A32D2D" }}>{__kbUi(xato)}</p>}
              </div>
            )}
          </>
        )}

        <p className="text-sm font-semibold mb-2.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📖 Tarix")}</p>
        <div className="space-y-2">
          {(tarix || []).map((t) => (
            <div key={t.ijara_id} className="rounded-xl p-3.5 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div>
                <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{t.full_name}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
                  {t.olingan_sana}{__kbUi(" dan ")}{t.qaytarilgan_sana ? __kbUi(` — qaytardi: ${t.qaytarilgan_sana}`) : __kbUi(" — hali qaytarmagan")}
                </p>
              </div>
              {!t.qaytarilgan_sana && (
                <button onClick={() => kitobniQaytar(t.ijara_id)} className="text-xs font-semibold px-2.5 py-1.5 rounded-lg text-white shrink-0" style={{ backgroundColor: "#3B6D11" }}>{__kbUi("Qaytardi")}</button>
              )}
            </div>
          ))}
          {(tarix || []).length === 0 && <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali hech kim olmagan.")}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("To'garaklarim")}</button>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-xl font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>📖 <InterfaceText text={__kbUi("Kutubxona")}/></h1>
        <button onClick={() => setFormOchiq(!formOchiq)} className="text-xs font-semibold px-3.5 py-1.5 rounded-full" style={{ backgroundColor: "#1B4B7A", color: "#fff" }}>
          {formOchiq ? __kbUi("✕ Yopish") : __kbUi("+ Yangi kitob")}
        </button>
      </div>
      <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{kitoblar.length}{__kbUi(" ta kitob.")}</p>

      {formOchiq && (
        <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <input type="text" value={nomi} onChange={(e) => setNomi(e.target.value)} placeholder={__kbUi("Kitob nomi")}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          <input type="text" value={muallif} onChange={(e) => setMuallif(e.target.value)} placeholder={__kbUi("Muallif (ixtiyoriy)")}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          <div className="grid grid-cols-2 gap-2.5 mb-2.5">
            <input type="text" value={janr} onChange={(e) => setJanr(e.target.value)} placeholder={__kbUi("Janr")}
              className="px-3.5 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            <input type="number" min="1" value={nusxaSoni} onChange={(e) => setNusxaSoni(e.target.value)} placeholder={__kbUi("Nusxa soni")}
              className="px-3.5 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          </div>
          <input type="text" value={elektronHavola} onChange={(e) => setElektronHavola(e.target.value)} placeholder={__kbUi("Elektron nusxa havolasi (ixtiyoriy)")}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
          <button onClick={kitobSaqla} disabled={saqlanmoqda}
            className="w-full py-3 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: saqlanmoqda ? 0.7 : 1 }}>
            {saqlanmoqda ? uiT("Saqlanmoqda...") : uiT("Qo'shish")}
          </button>
        </div>
      )}

      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : kitoblar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali kitob qo'shilmagan.")}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {kitoblar.map((k) => {
            const bosh = k.nusxa_soni - k.band_soni;
            return (
              <button key={k.id} onClick={() => kitobOch(k)}
                className="w-full text-left rounded-xl p-3.5 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                <div>
                  <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{k.nomi}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{k.muallif || __kbUi("Muallif noma'lum")}</p>
                </div>
                <span className="text-xs font-bold px-2.5 py-1 rounded-full shrink-0 ml-2" style={{ backgroundColor: bosh > 0 ? "#EAF3DE" : "#FCEBEB", color: bosh > 0 ? "#3B6D11" : "#A32D2D" }}>
                  {bosh}/{k.nusxa_soni}{__kbUi(" bo'sh")}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function OquvchiProfili({ token, userId, onOrtga }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [malumot, setMalumot] = useState(null);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");
  const [sogliq, setSogliq] = useState(null);
  const [sogliqTahrir, setSogliqTahrir] = useState(false);
  const [allergiyalar, setAllergiyalar] = useState("");
  const [qonGuruhi, setQonGuruhi] = useState("");
  const [aloqaIsmi, setAloqaIsmi] = useState("");
  const [aloqaTelefoni, setAloqaTelefoni] = useState("");
  const [boshqaEslatma, setBoshqaEslatma] = useState("");
  const [sogliqSaqlanmoqda, setSogliqSaqlanmoqda] = useState(false);
  const [psixologYozuvlar, setPsixologYozuvlar] = useState(null);
  const [yangiKuzatuv, setYangiKuzatuv] = useState("");
  const [kuzatuvSaqlanmoqda, setKuzatuvSaqlanmoqda] = useState(false);

  useEffect(() => {
    setYuklanmoqda(true); setXato("");
    fetch(`${API_BASE}/api/oqituvchi/oquvchi_profili?token=${encodeURIComponent(token)}&user_id=${userId}`)
      .then((r) => r.json())
      .then((d) => {
        if (d.detail) { setXato(d.detail); setYuklanmoqda(false); return; }
        setMalumot(d);
        setYuklanmoqda(false);
        fetch(`${API_BASE}/api/bola/${userId}/favqulodda_malumot?token=${encodeURIComponent(token)}`)
          .then((r) => r.json())
          .then((sd) => {
            setSogliq(sd);
            setAllergiyalar(sd.allergiyalar || ""); setQonGuruhi(sd.qon_guruhi || "");
            setAloqaIsmi(sd.aloqa_ismi || ""); setAloqaTelefoni(sd.aloqa_telefoni || ""); setBoshqaEslatma(sd.boshqa_eslatma || "");
          })
          .catch(() => {});
        if (d.maktab_id) {
          fetch(`${API_BASE}/api/maktab/psixolog_yozuvlari?token=${encodeURIComponent(token)}&bola_user_id=${userId}&maktab_id=${d.maktab_id}`)
            .then((r) => r.json())
            .then((pd) => setPsixologYozuvlar(pd.yozuvlar || []))
            .catch(() => {});
        }
      })
      .catch(() => { setXato("Yuklab bo'lmadi"); setYuklanmoqda(false); });
  }, [token, userId]);

  const sogliqSaqla = async () => {
    setSogliqSaqlanmoqda(true);
    try {
      await fetch(`${API_BASE}/api/bola/favqulodda_malumot`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, bola_user_id: userId, allergiyalar: allergiyalar || undefined, qon_guruhi: qonGuruhi || undefined, aloqa_ismi: aloqaIsmi || undefined, aloqa_telefoni: aloqaTelefoni || undefined, boshqa_eslatma: boshqaEslatma || undefined }),
      });
      setSogliq({ allergiyalar, qon_guruhi: qonGuruhi, aloqa_ismi: aloqaIsmi, aloqa_telefoni: aloqaTelefoni, boshqa_eslatma: boshqaEslatma });
      setSogliqTahrir(false);
    } finally { setSogliqSaqlanmoqda(false); }
  };

  const kuzatuvQosh = async () => {
    if (!yangiKuzatuv.trim() || !malumot?.maktab_id) return;
    setKuzatuvSaqlanmoqda(true);
    try {
      await fetch(`${API_BASE}/api/maktab/psixolog_yozuv_qosh`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, bola_user_id: userId, maktab_id: malumot.maktab_id, matn: yangiKuzatuv.trim() }),
      });
      setYangiKuzatuv("");
      const r = await fetch(`${API_BASE}/api/maktab/psixolog_yozuvlari?token=${encodeURIComponent(token)}&bola_user_id=${userId}&maktab_id=${malumot.maktab_id}`);
      const d = await r.json();
      setPsixologYozuvlar(d.yozuvlar || []);
    } finally { setKuzatuvSaqlanmoqda(false); }
  };

  const foizRangi = (foiz) => (foiz >= 70 ? "#3B6D11" : foiz >= 40 ? "#8A5A1C" : "#A32D2D");
  const foizFoni = (foiz) => (foiz >= 70 ? "#EAF3DE" : foiz >= 40 ? "#FDF3E0" : "#FCEBEB");

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Ortga")}/></button>
      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : xato ? (
        <p className="text-sm" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>
      ) : (
        <>
          <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{malumot.full_name}</h1>
          <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
            {malumot.sinf ? __kbUi(`${malumot.sinf}-${malumot.harf} sinf`) : __kbUi("")}{malumot.maktab_nomi ? __kbUi(` · ${malumot.maktab_nomi}`) : __kbUi("")}
          </p>

          <div className="rounded-2xl p-4 bg-white border mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📚 Bilim")}</p>
              {malumot.bilim.fanlar.length > 0 && (
                <span className="text-sm font-bold px-2.5 py-1 rounded-full" style={{ backgroundColor: foizFoni(malumot.bilim.umumiy_foiz), color: foizRangi(malumot.bilim.umumiy_foiz) }}>{__kbUi("Umumiy: ")}{malumot.bilim.umumiy_foiz}%
                </span>
              )}
            </div>
            {malumot.bilim.fanlar.length === 0 ? (
              <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali birorta test yechilmagan.")}</p>
            ) : (
              <div className="space-y-1.5">
                {malumot.bilim.fanlar.map((f) => (
                  <div key={f.qisqa} className="flex items-center justify-between">
                    <span className="text-xs" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{f.nom}</span>
                    <span className="text-xs font-semibold" style={{ color: foizRangi(f.foiz) }}>{f.foiz}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-2xl p-4 bg-white border mb-3" style={{ borderColor: malumot.davomat.ketma_ket_kelmagan >= 2 ? "#E8A0A0" : "#E5E1D8" }}>
            <p className="text-sm font-bold mb-3" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📋 Davomat (30 kun)")}</p>
            {malumot.davomat.ketma_ket_kelmagan >= 2 && (
              <p className="text-xs font-medium mb-3" style={{ color: "#A32D2D" }}>⚠️ {malumot.davomat.ketma_ket_kelmagan}{__kbUi(" kun ketma-ket kelmagan")}</p>
            )}
            {malumot.davomat.jami_kun === 0 ? (
              <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali davomat belgilanmagan.")}</p>
            ) : (
              <div className="grid grid-cols-3 gap-2">
                <div className="rounded-xl p-2.5 text-center" style={{ backgroundColor: "#EAF3DE" }}>
                  <p className="text-lg font-bold" style={{ color: "#3B6D11" }}>{malumot.davomat.keldi}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("keldi")}</p>
                </div>
                <div className="rounded-xl p-2.5 text-center" style={{ backgroundColor: "#FCEBEB" }}>
                  <p className="text-lg font-bold" style={{ color: "#A32D2D" }}>{malumot.davomat.kelmadi}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("kelmadi")}</p>
                </div>
                <div className="rounded-xl p-2.5 text-center" style={{ backgroundColor: "#FDF3E0" }}>
                  <p className="text-lg font-bold" style={{ color: "#8A5A1C" }}>{malumot.davomat.kechikdi}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("kechikdi")}</p>
                </div>
              </div>
            )}
          </div>

          {malumot.pulli && (
            <div className="rounded-2xl p-4 bg-white border mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <p className="text-sm font-bold mb-3" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("💳 To'lov tarixi")}</p>
              {malumot.tolov_tarixi.length === 0 ? (
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali to'lov qilinmagan.")}</p>
              ) : (
                <div className="space-y-1.5">
                  {malumot.tolov_tarixi.map((t) => (
                    <div key={t.oy} className="flex items-center justify-between">
                      <span className="text-xs" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{t.oy}</span>
                      <span className="text-xs font-semibold" style={{ color: t.tolangan_summa >= malumot.oylik_tolov ? "#3B6D11" : "#A32D2D" }}>
                        {__kbUi(t.tolangan_summa.toLocaleString())}{__kbUi(" so'm")}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="rounded-2xl p-4 bg-white border mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🚑 Favqulodda ma'lumot")}</p>
              <button onClick={() => setSogliqTahrir(!sogliqTahrir)} className="text-xs font-semibold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
                {sogliqTahrir ? __kbUi("Bekor") : __kbUi("✎ Tahrirlash")}
              </button>
            </div>
            {sogliqTahrir ? (
              <div>
                <input type="text" value={allergiyalar} onChange={(e) => setAllergiyalar(e.target.value)} placeholder={__kbUi("Allergiyalar")}
                  className="w-full px-3 py-2 rounded-lg border text-xs mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                <input type="text" value={qonGuruhi} onChange={(e) => setQonGuruhi(e.target.value)} placeholder={__kbUi("Qon guruhi (masalan A+)")}
                  className="w-full px-3 py-2 rounded-lg border text-xs mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                <input type="text" value={aloqaIsmi} onChange={(e) => setAloqaIsmi(e.target.value)} placeholder={__kbUi("Favqulodda aloqa ismi")}
                  className="w-full px-3 py-2 rounded-lg border text-xs mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                <input type="text" value={aloqaTelefoni} onChange={(e) => setAloqaTelefoni(e.target.value)} placeholder={__kbUi("Favqulodda aloqa telefoni")}
                  className="w-full px-3 py-2 rounded-lg border text-xs mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                <input type="text" value={boshqaEslatma} onChange={(e) => setBoshqaEslatma(e.target.value)} placeholder={__kbUi("Boshqa muhim eslatma")}
                  className="w-full px-3 py-2 rounded-lg border text-xs mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                <button onClick={sogliqSaqla} disabled={sogliqSaqlanmoqda} className="w-full py-2 rounded-lg font-semibold text-white text-xs" style={{ backgroundColor: "#1B4B7A" }}>
                  {sogliqSaqlanmoqda ? uiT("Saqlanmoqda...") : uiT("Saqlash")}
                </button>
              </div>
            ) : !sogliq || (!sogliq.allergiyalar && !sogliq.qon_guruhi && !sogliq.aloqa_ismi) ? (
              <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali kiritilmagan.")}</p>
            ) : (
              <div className="space-y-1 text-xs" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
                {sogliq.allergiyalar && <p>{__kbUi("🩹 Allergiya: ")}{sogliq.allergiyalar}</p>}
                {sogliq.qon_guruhi && <p>{__kbUi("🩸 Qon guruhi: ")}{sogliq.qon_guruhi}</p>}
                {sogliq.aloqa_ismi && <p>📞 {sogliq.aloqa_ismi}{sogliq.aloqa_telefoni ? __kbUi(` — ${sogliq.aloqa_telefoni}`) : __kbUi("")}</p>}
                {sogliq.boshqa_eslatma && <p>{__kbUi("ℹ️ ")}{sogliq.boshqa_eslatma}</p>}
              </div>
            )}
          </div>

          {psixologYozuvlar !== null && (
            <div className="rounded-2xl p-4 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <p className="text-sm font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🧠 Psixolog kuzatuvlari")}</p>
              <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Faqat psixolog, sinf rahbari va rahbariyatga ko'rinadi.")}</p>
              <div className="flex gap-2 mb-3">
                <input type="text" value={yangiKuzatuv} onChange={(e) => setYangiKuzatuv(e.target.value)} placeholder={__kbUi("Yangi kuzatuv yozing...")}
                  className="flex-1 px-3 py-2 rounded-lg border text-xs" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                <button onClick={kuzatuvQosh} disabled={kuzatuvSaqlanmoqda || !yangiKuzatuv.trim()} className="px-3 py-2 rounded-lg font-semibold text-white text-xs" style={{ backgroundColor: "#5A3D9E" }}>
                  +
                </button>
              </div>
              {psixologYozuvlar.length === 0 ? (
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali kuzatuv yozilmagan.")}</p>
              ) : (
                <div className="space-y-2">
                  {psixologYozuvlar.map((k) => (
                    <div key={k.id} className="rounded-lg p-2.5" style={{ backgroundColor: "#F3F0FF" }}>
                      <p className="text-xs" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{k.matn}</p>
                      <p className="text-xs mt-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{k.yozgan_ismi} · {__kbUi(new Date(k.yaratilgan_at).toLocaleDateString(__kbLocaleTag()))}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function XodimDavomatBelgilash({ token, maktabId, onOrtga }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const bugun = new Date().toISOString().slice(0, 10);
  const [sana, setSana] = useState(bugun);
  const [xodimlar, setXodimlar] = useState(null);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [saqlanmoqda, setSaqlanmoqda] = useState(false);
  const [saqlandi, setSaqlandi] = useState(false);

  const HOLATLAR = [
    { kalit: "keldi", belgi: "✅", rang: "#3B6D11", fon: "#EAF3DE" },
    { kalit: "kelmadi", belgi: "❌", rang: "#A32D2D", fon: "#FCEBEB" },
    { kalit: "kechikdi", belgi: "⏰", rang: "#8A5A1C", fon: "#FDF3E0" },
    { kalit: "sababli", belgi: "📋", rang: "#5A5648", fon: "#F7F5F0" },
  ];

  const yukla = () => {
    setYuklanmoqda(true); setSaqlandi(false);
    fetch(`${API_BASE}/api/maktab/xodim_davomat_royxati?token=${encodeURIComponent(token)}&maktab_id=${maktabId}&sana=${sana}`)
      .then((r) => r.json())
      .then((d) => { setXodimlar((d.xodimlar || []).map((x) => ({ ...x, holat: x.holat || "keldi" }))); setYuklanmoqda(false); })
      .catch(() => setYuklanmoqda(false));
  };
  useEffect(yukla, [sana, maktabId, token]);

  const holatOzgartir = (userId, holat) => {
    setXodimlar((prev) => prev.map((x) => (x.user_id === userId ? { ...x, holat } : x)));
  };

  const saqla = async () => {
    setSaqlanmoqda(true); setSaqlandi(false);
    try {
      await fetch(`${API_BASE}/api/maktab/xodim_davomat_belgila`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token, maktab_id: maktabId, sana,
          yozuvlar: xodimlar.map((x) => ({ user_id: x.user_id, holat: x.holat })),
        }),
      });
      setSaqlandi(true);
    } finally { setSaqlanmoqda(false); }
  };

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Ortga")}/></button>
      <h1 className="text-xl font-bold mb-4" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🧑‍🏫 Xodim davomati")}</h1>
      <input type="date" value={sana} onChange={(e) => setSana(e.target.value)} max={bugun}
        className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />

      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : (
        <div className="space-y-2 mb-5">
          {(xodimlar || []).map((x) => (
            <div key={x.user_id} className="rounded-xl p-3 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <p className="text-sm font-medium mb-0.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{x.full_name}</p>
              <p className="text-xs mb-2" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{LAVOZIM_NOMLARI[x.lavozim] || x.lavozim}</p>
              <div className="flex gap-1.5">
                {HOLATLAR.map((h) => (
                  <button key={h.kalit} onClick={() => holatOzgartir(x.user_id, h.kalit)}
                    className="flex-1 py-1.5 rounded-lg text-xs font-semibold"
                    style={x.holat === h.kalit ? { backgroundColor: h.rang, color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#8A8578" }}>
                    {__kbUi(h.belgi)}
                  </button>
                ))}
              </div>
            </div>
          ))}
          {(xodimlar || []).length === 0 && <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Xodim topilmadi.")}</p>}
        </div>
      )}

      {saqlandi && <p className="text-sm mb-3" style={{ color: "#3B6D11" }}>{__kbUi("✅ Saqlandi")}</p>}
      <button onClick={saqla} disabled={saqlanmoqda || yuklanmoqda}
        className="w-full py-3 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: saqlanmoqda ? 0.7 : 1 }}>
        {saqlanmoqda ? uiT("Saqlanmoqda...") : uiT("Saqlash")}
      </button>
    </div>
  );
}

function FanlarTahliliBolimi({ token, maktabId, onOrtga }) {
  useKbInterfaceLocale();
  const [fanlar, setFanlar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/maktab/fanlar_tahlili?token=${encodeURIComponent(token)}&maktab_id=${maktabId}`)
      .then((r) => r.json())
      .then((d) => { setFanlar(d.fanlar || []); setYuklanmoqda(false); })
      .catch(() => setYuklanmoqda(false));
  }, [token, maktabId]);

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("To'garaklarim")}</button>
      <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📊 Fanlar tahlili")}</h1>
      <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Butun maktab kesimida, har fandan necha o'quvchi qanday natijada.")}</p>

      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : fanlar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali test yechilmagan — tahlil uchun ma'lumot yo'q.")}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {fanlar.map((f) => {
            const jami = f.yaxshi + f.ortacha + f.past;
            return (
              <div key={f.subject_name} className="rounded-2xl p-4 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                <div className="flex items-center justify-between mb-2.5">
                  <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{f.subject_name}</p>
                  <span className="text-xs font-bold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("o'rtacha ")}{f.umumiy_ortacha}%</span>
                </div>
                <div className="flex h-2.5 rounded-full overflow-hidden mb-2">
                  {f.yaxshi > 0 && <div style={{ width: `${(f.yaxshi / jami) * 100}%`, backgroundColor: "#3B6D11" }} />}
                  {f.ortacha > 0 && <div style={{ width: `${(f.ortacha / jami) * 100}%`, backgroundColor: "#C89B3C" }} />}
                  {f.past > 0 && <div style={{ width: `${(f.past / jami) * 100}%`, backgroundColor: "#A32D2D" }} />}
                </div>
                <div className="flex gap-3 text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
                  <span>🟢 {f.yaxshi}{__kbUi(" yaxshi")}</span>
                  <span>🟡 {f.ortacha}{__kbUi(" o'rtacha")}</span>
                  <span>🔴 {f.past}{__kbUi(" past")}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function MeningKalendarim({ token, togarak, onOrtga, onMavzuOchish }) {
  useKbInterfaceLocale();
  const [korinishTuri, setKorinishTuri] = useState("hafta");
  const [ankor, setAnkor] = useState(() => new Date());
  const [darsKunlari, setDarsKunlari] = useState(null); // null=hali yuklanmagan, []=hali tanlanmagan
  const [rejaBormi, setRejaBormi] = useState(true);
  const [kunlarTanlovOchiq, setKunlarTanlovOchiq] = useState(false);
  const [vaqtinchaKunlar, setVaqtinchaKunlar] = useState([]);
  const [kunlarSaqlanmoqda, setKunlarSaqlanmoqda] = useState(false);
  const [toldirishXabari, setToldirishXabari] = useState("");
  const [sanalar, setSanalar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/togarak_azo/mening_dars_kunlarim?token=${encodeURIComponent(token)}&togarak_id=${togarak.id}`)
      .then((r) => r.json())
      .then((d) => { setDarsKunlari(d.kunlar || []); setRejaBormi(d.reja_bormi !== false); })
      .catch(() => setDarsKunlari([]));
  }, [token, togarak.id]);

  const { boshlanish, tugash } = useMemo(() => {
    if (korinishTuri === "hafta") {
      const b = _haftaBoshi(ankor);
      const t = new Date(b); t.setDate(t.getDate() + 6);
      return { boshlanish: b, tugash: t };
    }
    const b = new Date(ankor.getFullYear(), ankor.getMonth(), 1);
    const t = new Date(ankor.getFullYear(), ankor.getMonth() + 1, 0);
    return { boshlanish: b, tugash: t };
  }, [ankor, korinishTuri]);

  const kalendarniYukla = () => {
    setYuklanmoqda(true); setXato("");
    fetch(`${API_BASE}/api/togarak_azo/mening_kalendarim?token=${encodeURIComponent(token)}&togarak_id=${togarak.id}&boshlanish=${_sanaFmt(boshlanish)}&tugash=${_sanaFmt(tugash)}`)
      .then((r) => r.json())
      .then((d) => { if (d.detail) throw new Error(d.detail); setSanalar(d.sanalar || []); setYuklanmoqda(false); })
      .catch((e) => { setXato(e.message || "Yuklab bo'lmadi"); setYuklanmoqda(false); });
  };

  useEffect(() => {
    if (darsKunlari === null || darsKunlari.length === 0) return;
    kalendarniYukla();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [darsKunlari, boshlanish.getTime(), tugash.getTime()]);

  const kunlarSaqla = async () => {
    setKunlarSaqlanmoqda(true); setToldirishXabari("");
    try {
      const res = await fetch(`${API_BASE}/api/togarak_azo/dars_kunlarimni_belgila`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, togarak_id: togarak.id, kunlar: vaqtinchaKunlar }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setDarsKunlari(data.kunlar);
      setKunlarTanlovOchiq(false);
      if (data.toldirilgan_soni > 0) setToldirishXabari(`✓ ${data.toldirilgan_soni} ta darsingiz rejalashtirildi`);
    } catch (e) { setXato(e.message); } finally { setKunlarSaqlanmoqda(false); }
  };

  const davrLabel = korinishTuri === "hafta"
    ? `${boshlanish.getDate()}-${tugash.getDate()} ${OY_NOMLARI[tugash.getMonth()]}`
    : `${OY_NOMLARI[ankor.getMonth()]} ${ankor.getFullYear()}`;

  const davrniSurish = (yonalish) => {
    const yangi = new Date(ankor);
    if (korinishTuri === "hafta") yangi.setDate(yangi.getDate() + yonalish * 7);
    else yangi.setMonth(yangi.getMonth() + yonalish);
    setAnkor(yangi);
  };

  const kunBosildi = (sana) => {
    const s = sanalar.find((x) => x.sana === sana);
    if (s?.topic_code) onMavzuOchish(s.topic_code);
  };

  const kunKartasiChiqar = (haftaKuni, keng) => {
    const d = new Date(boshlanish);
    d.setDate(d.getDate() + (haftaKuni - 1));
    const sana = _sanaFmt(d);
    const darsKunimi = darsKunlari.includes(haftaKuni);
    const s = sanalar.find((x) => x.sana === sana);
    const bugunmi = sana === _sanaFmt(new Date());
    const mavzuBormi = !!s?.mavzu_nomi;

    if (!darsKunimi) {
      return (
        <div key={sana} className={`rounded-xl px-3 py-2.5 ${keng ? "flex items-center gap-2" : ""}`} style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
          <p className="text-xs font-medium" style={{ color: "var(--ui-legacy-color-b0aa98, #B0AA98)" }}>{keng ? __kbUi(HAFTA_KUN_TOLIQ[haftaKuni]) : __kbUi(HAFTA_KUN_QISQA[haftaKuni])}, {__kbUi(d.getDate())}</p>
          <p className="text-[11px] italic" style={{ color: "#C4BFAF" }}>{__kbUi("dars yo'q")}</p>
        </div>
      );
    }
    return (
      <button key={sana} onClick={() => mavzuBormi && kunBosildi(sana)} disabled={!mavzuBormi}
        className={`w-full rounded-xl bg-white border text-left ${keng ? "flex items-center gap-3.5 p-3.5" : "p-3"}`}
        style={{ borderColor: bugunmi ? "#1B4B7A" : "#E5E1D8", borderWidth: bugunmi ? 2 : 1, opacity: mavzuBormi ? 1 : 0.7 }}>
        <div className={`rounded-lg flex items-center justify-center shrink-0 ${keng ? "w-12 h-12 flex-col gap-0" : "w-full mb-1.5 py-1.5 gap-1.5"}`}
          style={{ backgroundColor: mavzuBormi ? "#EAF3DE" : "#EAF1F7" }}>
          <span className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: mavzuBormi ? "#3B6D11" : "#1B4B7A" }}>{__kbUi(HAFTA_KUN_QISQA[haftaKuni])}</span>
          <span className={`font-bold leading-tight ${keng ? "text-base" : "text-sm"}`} style={{ color: mavzuBormi ? "#3B6D11" : "#1B4B7A" }}>{__kbUi(d.getDate())}</span>
        </div>
        <div className="min-w-0 flex-1">
          {keng && <p className="text-[11px] font-medium mb-0.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi(HAFTA_KUN_TOLIQ[haftaKuni])}{bugunmi ? __kbUi(" · bugun") : __kbUi("")}</p>}
          {mavzuBormi ? (
            <p className={`font-semibold truncate ${keng ? "text-sm" : "text-xs"}`} style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{s.mavzu_nomi}</p>
          ) : (
            <p className={`font-medium ${keng ? "text-sm" : "text-xs"}`} style={{ color: "var(--ui-legacy-color-b0aa98, #B0AA98)" }}>{__kbUi("hali mavzu yo'q")}</p>
          )}
        </div>
      </button>
    );
  };

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{togarak.nomi}</button>
      <h1 className="text-xl font-bold mb-4" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📅 Mening kalendarim")}</h1>

      {darsKunlari !== null && darsKunlari.length === 0 && !kunlarTanlovOchiq && (
        <div className="rounded-2xl p-4 border mb-4" style={{ backgroundColor: "#FDF3E0", borderColor: "#C89B3C" }}>
          <p className="text-sm font-bold mb-1" style={{ color: "#8A5A1C" }}>{__kbUi("Mustaqil o'rganish kunlaringizni tanlang")}</p>
          <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
            {rejaBormi ? __kbUi("Qaysi kunlari o'rganishni xohlaysiz? Tanlaganingizdan so'ng, darslar shu kunlaringizga avtomatik taqsimlanadi — bugundan boshlab, o'z sur'atingizda.") : __kbUi("Bu to'garakka hali dastur bog'lanmagan — o'qituvchingizga murojaat qiling.")}
          </p>
          {rejaBormi && (
            <button onClick={() => { setVaqtinchaKunlar([]); setKunlarTanlovOchiq(true); }}
              className="w-full py-2.5 rounded-xl font-semibold text-sm text-white" style={{ backgroundColor: "#C89B3C" }}>{__kbUi("Kunlarni tanlash")}</button>
          )}
        </div>
      )}

      {kunlarTanlovOchiq && (
        <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-xs font-semibold mb-3" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Qaysi kunlari mustaqil o'rganasiz?")}</p>
          <div className="grid grid-cols-4 gap-1.5 mb-3">
            {[1, 2, 3, 4, 5, 6, 7].map((k) => (
              <button key={k} type="button"
                onClick={() => setVaqtinchaKunlar((prev) => prev.includes(k) ? prev.filter((x) => x !== k) : [...prev, k])}
                className="py-2 rounded-lg border text-xs font-semibold text-center"
                style={{
                  borderColor: vaqtinchaKunlar.includes(k) ? "#1B4B7A" : "#E5E1D8",
                  backgroundColor: vaqtinchaKunlar.includes(k) ? "#1B4B7A" : "#FFFFFF",
                  color: vaqtinchaKunlar.includes(k) ? "#FFFFFF" : "#5A5648",
                }}>
                {__kbUi(HAFTA_KUN_QISQA[k])}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            {darsKunlari && darsKunlari.length > 0 && (
              <button onClick={() => setKunlarTanlovOchiq(false)} className="flex-1 py-2.5 rounded-xl border text-sm font-medium" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Bekor")}</button>
            )}
            <button onClick={kunlarSaqla} disabled={kunlarSaqlanmoqda || vaqtinchaKunlar.length === 0}
              className="flex-1 py-2.5 rounded-xl font-semibold text-white text-sm"
              style={{ backgroundColor: "#1B4B7A", opacity: (kunlarSaqlanmoqda || vaqtinchaKunlar.length === 0) ? 0.6 : 1 }}>
              {kunlarSaqlanmoqda ? __kbUi("...") : __kbUi("Saqlash va boshlash")}
            </button>
          </div>
        </div>
      )}

      {toldirishXabari && <p className="text-sm mb-3 text-center" style={{ color: "#3B6D11" }}>{toldirishXabari}</p>}

      {darsKunlari !== null && darsKunlari.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-3">
            <div className="flex rounded-full p-1 gap-0.5" style={{ backgroundColor: "#F0EDE5" }}>
              <button onClick={() => setKorinishTuri("hafta")} className="px-3.5 py-1.5 rounded-full text-xs font-semibold"
                style={korinishTuri === "hafta" ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>{__kbUi("Haftalik")}</button>
              <button onClick={() => setKorinishTuri("oy")} className="px-3.5 py-1.5 rounded-full text-xs font-semibold"
                style={korinishTuri === "oy" ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>{__kbUi("Oylik")}</button>
            </div>
            <button onClick={() => { setVaqtinchaKunlar(darsKunlari); setKunlarTanlovOchiq(true); }} className="text-xs font-medium" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
              {__kbUi(darsKunlari.map((k) => HAFTA_KUN_QISQA[k]).join(", "))} ✏️
            </button>
          </div>

          <div className="flex items-center justify-between mb-3">
            <button onClick={() => davrniSurish(-1)} className="w-8 h-8 rounded-full flex items-center justify-center border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>‹</button>
            <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(davrLabel)}</p>
            <button onClick={() => davrniSurish(1)} className="w-8 h-8 rounded-full flex items-center justify-center border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>›</button>
          </div>

          {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}

          {yuklanmoqda ? (
            <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
          ) : korinishTuri === "hafta" ? (
            <div className="space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-2">{[1, 3, 5].map((hk) => kunKartasiChiqar(hk, false))}</div>
                <div className="space-y-2">{[2, 4, 6].map((hk) => kunKartasiChiqar(hk, false))}</div>
              </div>
              {__kbUi(kunKartasiChiqar(7, true))}
            </div>
          ) : (
            <div className="rounded-2xl bg-white border p-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div className="grid grid-cols-7 mb-2">
                {[1, 2, 3, 4, 5, 6, 7].map((k) => (
                  <p key={k} className="text-[10px] text-center font-semibold uppercase tracking-wide" style={{ color: darsKunlari.includes(k) ? "#1B4B7A" : "#D8D3C7" }}>
                    {__kbUi(HAFTA_KUN_QISQA[k].slice(0, 2))}
                  </p>
                ))}
              </div>
              <div className="grid grid-cols-7 gap-y-1.5 justify-items-center">
                {__kbUi((() => {
                  const oyBoshi = new Date(ankor.getFullYear(), ankor.getMonth(), 1);
                  const boshiKun = oyBoshi.getDay() === 0 ? 7 : oyBoshi.getDay();
                  const boshlangichBosh = [];
                  for (let i = 1; i < boshiKun; i++) boshlangichBosh.push(<div key={`b${i}`} />);
                  const sanaMap = Object.fromEntries(sanalar.map((s) => [s.sana, s]));
                  const bugunKey = _sanaFmt(new Date());
                  const kunlar = [];
                  const jamiKun = new Date(ankor.getFullYear(), ankor.getMonth() + 1, 0).getDate();
                  for (let kun = 1; kun <= jamiKun; kun++) {
                    const d = new Date(ankor.getFullYear(), ankor.getMonth(), kun);
                    const key = _sanaFmt(d);
                    const s = sanaMap[key];
                    const haftaKuni = d.getDay() === 0 ? 7 : d.getDay();
                    const darsKunimi = darsKunlari.includes(haftaKuni);
                    const bugunmi = key === bugunKey;
                    const mavzuBormi = darsKunimi && s?.mavzu_nomi;
                    kunlar.push(
                      <button key={key} onClick={() => mavzuBormi && kunBosildi(key)} disabled={!mavzuBormi}
                        className="w-8 h-8 rounded-full flex items-center justify-center relative"
                        style={{
                          backgroundColor: mavzuBormi ? "#3B6D11" : "transparent",
                          border: bugunmi ? "1.5px solid #1B4B7A" : "1.5px solid transparent",
                        }}>
                        <span className="text-xs font-semibold" style={{ color: mavzuBormi ? "#FFFFFF" : darsKunimi ? "#2B2B2B" : "#D8D3C7" }}>{kun}</span>
                        {darsKunimi && !mavzuBormi && (
                          <span className="absolute bottom-0.5 w-1 h-1 rounded-full" style={{ backgroundColor: "#C89B3C" }} />
                        )}
                      </button>,
                    );
                  }
                  return [...boshlangichBosh, ...kunlar];
                })())}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function OquvchiKitobKorish({ token, togarak, topicCode, mavzuNomi, onOrtga, foydalanuvchi = null }) {
  useKbInterfaceLocale();
  const [videolar, setVideolar] = useState([]);
  const [misollar, setMisollar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");
  const [ochilganYechimlar, setOchilganYechimlar] = useState({});
  const [ochilganVideoSoniya, setOchilganVideoSoniya] = useState({});
  const [oqilayotganId, setOqilayotganId] = useState(null);
  const [joriySozIndeksi, setJoriySozIndeksi] = useState(-1);
  const ovozAsosiyTil = _ovozTiliniTuzat(foydalanuvchi?.asosiy_til || "uz");
  const tanlanganOvozJinsi = _ovozJinsiniTuzat(foydalanuvchi?.ovoz_jinsi || foydalanuvchi?.jins || "qiz");

  const [mustaqilIshlar, setMustaqilIshlar] = useState([]);
  const [javobQoralamalari, setJavobQoralamalari] = useState({}); // {ishId: matn}
  const [topshirilmoqda, setTopshirilmoqda] = useState({}); // {ishId: true}

  const ishlarniYukla = () => {
    fetch(`${API_BASE}/api/togarak_azo/mustaqil_ishlar?token=${encodeURIComponent(token)}&togarak_id=${togarak.id}&topic_code=${encodeURIComponent(topicCode)}`)
      .then((r) => r.json())
      .then((d) => setMustaqilIshlar(d.ishlar || []))
      .catch(() => {});
  };

  const javobTopshir = async (ishId) => {
    const matn = (javobQoralamalari[ishId] || "").trim();
    if (!matn) return;
    setTopshirilmoqda((p) => ({ ...p, [ishId]: true }));
    try {
      await fetch(`${API_BASE}/api/togarak_azo/mustaqil_ish_topshir`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, ish_id: ishId, javob_matni: matn }),
      });
      ishlarniYukla();
    } finally { setTopshirilmoqda((p) => ({ ...p, [ishId]: false })); }
  };

  useEffect(() => {
    fetch(`${API_BASE}/api/togarak_azo/mavzu_kitobi?token=${encodeURIComponent(token)}&togarak_id=${togarak.id}&topic_code=${encodeURIComponent(topicCode)}`)
      .then(async (r) => {
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.detail || `Server xatosi (${r.status})`);
        return d;
      })
      .then((d) => { setVideolar(d.videolar || []); setMisollar(d.misollar || []); setYuklanmoqda(false); })
      .catch((e) => { setXato(e.message || "Yuklab bo'lmadi"); setYuklanmoqda(false); });
    ishlarniYukla();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, togarak.id, topicCode]);

  useEffect(() => () => window.speechSynthesis?.cancel(), []);

  const youtubeIdOl = (url) => {
    const m = (url || "").match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/))([\w-]{11})/);
    return m ? m[1] : null;
  };

  const misolKartasiChiqar = (m, i, videoHavola) => (
    <div key={m.id} className="rounded-2xl p-4 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
      <p className="text-xs font-semibold mb-1.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{i + 1}{__kbUi("-misol")}</p>
      <AralashMatn matn={m.masala_matni} className="text-sm font-medium mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }} />
      <OvozliOqishTugmasi matn={m.masala_matni} kontentId={`masala-${m.id}`} oqilayotganId={oqilayotganId} setOqilayotganId={setOqilayotganId}
        joriySozIndeksi={joriySozIndeksi} setJoriySozIndeksi={setJoriySozIndeksi} asosiyTil={ovozAsosiyTil} ovozJinsi={tanlanganOvozJinsi} />
      {!ochilganYechimlar[m.id] ? (
        <button onClick={() => setOchilganYechimlar((p) => ({ ...p, [m.id]: true }))}
          className="w-full py-2.5 rounded-xl font-semibold text-sm mt-3" style={{ backgroundColor: "#FDF3E0", color: "#8A5A1C" }}>{__kbUi("🤔 Tushunmadim — yechimni ko'rsat")}</button>
      ) : (
        <div className="rounded-xl p-3 mt-3" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
          {m.yechim_matni ? (
            <>
              <AralashMatn matn={m.yechim_matni} className="text-sm" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }} />
              <OvozliOqishTugmasi matn={m.yechim_matni} kontentId={`yechim-${m.id}`} oqilayotganId={oqilayotganId} setOqilayotganId={setOqilayotganId}
                joriySozIndeksi={joriySozIndeksi} setJoriySozIndeksi={setJoriySozIndeksi} asosiyTil={ovozAsosiyTil} ovozJinsi={tanlanganOvozJinsi} />
            </>
          ) : (
            <p className="text-xs italic" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bu misol uchun tushuntirish yozilmagan.")}</p>
          )}
          {m.video_soniya != null && youtubeIdOl(videoHavola) && (
            !ochilganVideoSoniya[m.id] ? (
              <button onClick={() => setOchilganVideoSoniya((p) => ({ ...p, [m.id]: true }))}
                className="text-xs font-semibold mt-2" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("▶️ Videoning shu qismini qayta ko'rish")}</button>
            ) : (
              <div className="rounded-lg overflow-hidden mt-2" style={{ aspectRatio: "16/9" }}>
                <iframe className="w-full h-full" src={`https://www.youtube.com/embed/${youtubeIdOl(videoHavola)}?start=${m.video_soniya}${m.video_tugash_soniya != null ? `&end=${m.video_tugash_soniya}` : ""}&autoplay=1`}
                  title={__kbUi("tushuntirish")} allowFullScreen />
              </div>
            )
          )}
        </div>
      )}
    </div>
  );

  if (yuklanmoqda) {
    return (
      <div className="px-5 pt-6 pb-4">
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      </div>
    );
  }
  if (xato) {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Ortga")}/></button>
        <p className="text-sm" style={{ color: "#A32D2D" }}>⚠️ {__kbUi(xato)}</p>
      </div>
    );
  }
  if (videolar.length === 0 && misollar.length === 0 && mustaqilIshlar.length === 0) {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Ortga")}/></button>
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bu mavzu uchun hali kitob tayyorlanmagan.")}</p>
        </div>
      </div>
    );
  }

  const guruhlar = videolar.map((v) => ({ video: v, misollar: misollar.filter((m) => m.video_id === v.id) }));
  const boglanmaganMisollar = misollar.filter((m) => !m.video_id);

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{mavzuNomi}</button>
      <h1 className="text-xl font-bold mb-5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📖 Kitob")}</h1>

      <div className="space-y-6">
        {guruhlar.map((g) => (
          <div key={g.video.id}>
            {g.video.sarlavha && <p className="text-sm font-semibold mb-2" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{g.video.sarlavha}</p>}
            {youtubeIdOl(g.video.video_havola) ? (
              <div className="rounded-xl overflow-hidden mb-3" style={{ aspectRatio: "16/9" }}>
                <iframe className="w-full h-full" src={`https://www.youtube.com/embed/${youtubeIdOl(g.video.video_havola)}`}
                  title={g.video.sarlavha || __kbUi("video")} allowFullScreen />
              </div>
            ) : (
              <a href={g.video.video_havola} target="_blank" rel="noreferrer"
                className="block text-center text-xs font-semibold py-2.5 rounded-lg mb-3" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("▶️ Videoni ochish")}</a>
            )}
            <div className="space-y-2.5">
              {g.misollar.map((m, i) => misolKartasiChiqar(m, i, g.video.video_havola))}
            </div>
          </div>
        ))}

        {boglanmaganMisollar.length > 0 && (
          <div>
            <p className="text-sm font-semibold mb-2" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Boshqa misollar")}</p>
            <div className="space-y-2.5">
              {boglanmaganMisollar.map((m, i) => misolKartasiChiqar(m, i, null))}
            </div>
          </div>
        )}

        {mustaqilIshlar.length > 0 && (
          <div>
            <p className="text-sm font-semibold mb-2" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📝 Mustaqil ishlar")}</p>
            <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Kitobni o'rgangach, shu savollarga o'z so'zlaringiz bilan javob yozing.")}</p>
            <div className="space-y-3">
              {mustaqilIshlar.map((ish, i) => {
                const oxirgi = ish.oxirgi_javob;
                return (
                  <div key={ish.id} className="rounded-2xl p-4 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                    <AralashMatn matn={`${i + 1}. ${ish.savol_matni}`} className="text-sm font-medium mb-3" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }} />
                    {oxirgi && (
                      <div className="rounded-xl p-3 mb-3" style={{ backgroundColor: oxirgi.togrimi === true ? "#EAF3DE" : oxirgi.togrimi === false ? "#FCEBEB" : "#F7F5F0" }}>
                        <p className="text-xs font-semibold mb-1" style={{ color: oxirgi.togrimi === true ? "#3B6D11" : oxirgi.togrimi === false ? "#A32D2D" : "#5A5648" }}>
                          {oxirgi.togrimi === true ? __kbUi("✓ To'g'ri") : oxirgi.togrimi === false ? __kbUi("✕ Noto'g'ri") : __kbUi("Yuborilgan")}
                        </p>
                        <p className="text-xs mb-1.5" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Sizning javobingiz: ")}{oxirgi.javob_matni}</p>
                        {oxirgi.ai_izohi && <p className="text-xs" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{oxirgi.ai_izohi}</p>}
                      </div>
                    )}
                    <textarea value={javobQoralamalari[ish.id] || ""} onChange={(e) => setJavobQoralamalari((p) => ({ ...p, [ish.id]: e.target.value }))}
                      rows={3} placeholder={oxirgi ? __kbUi("Qayta yechib, qayta topshirish uchun yozing...") : __kbUi("Javobingizni shu yerga yozing...")}
                      className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                    <button onClick={() => javobTopshir(ish.id)} disabled={topshirilmoqda[ish.id] || !(javobQoralamalari[ish.id] || "").trim()}
                      className="w-full py-2.5 rounded-xl font-semibold text-sm text-white"
                      style={{ backgroundColor: "#1B4B7A", opacity: (topshirilmoqda[ish.id] || !(javobQoralamalari[ish.id] || "").trim()) ? 0.6 : 1 }}>
                      {topshirilmoqda[ish.id] ? __kbUi("Tekshirilmoqda...") : oxirgi ? __kbUi("Qayta topshirish") : __kbUi("Topshirish")}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function MustahkamlashTestOynasi({ token, mavzu, togarakId, onOrtga }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [test, setTest] = useState(null);
  const [indeks, setIndeks] = useState(0);
  const [javoblar, setJavoblar] = useState([]);
  const [tanlangan, setTanlangan] = useState("");
  const [tekshiruv, setTekshiruv] = useState(null);
  const [natija, setNatija] = useState(null);
  const [xato, setXato] = useState("");
  const [band, setBand] = useState(true);
  const boshlangan = useRef(Date.now());

  useEffect(() => {
    setBand(true); setXato("");
    fetch(`${API_BASE}/api/oquvchi/mustahkamlash-test`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, topic_code: mavzu.topic_code, togarak_id: togarakId }),
    }).then(async (r) => {
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof d.detail === "string" ? d.detail : "Test ochilmadi");
      return d;
    }).then(setTest).catch((e) => setXato(e.message)).finally(() => setBand(false));
  }, [token, mavzu.topic_code, togarakId]);

  const savol = test?.savollar?.[indeks];
  const javobniTekshir = async (qiymat) => {
    if (!qiymat || !savol || tekshiruv) return;
    setTanlangan(qiymat); setBand(true); setXato("");
    try {
      const r = await fetch(`${API_BASE}/api/test/javob_tekshir`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, attempt_id: test.attempt_id, savol_id: savol.id, tanlangan: qiymat }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof d.detail === "string" ? d.detail : "Javob tekshirilmadi");
      setTekshiruv(d);
      setJavoblar((old) => [...old, { savol_id: savol.id, tanlangan: qiymat }]);
    } catch (e) { setXato(e.message); } finally { setBand(false); }
  };

  const keyingi = async () => {
    if (indeks + 1 < test.savollar.length) {
      setIndeks((v) => v + 1); setTanlangan(""); setTekshiruv(null); return;
    }
    setBand(true); setXato("");
    try {
      const r = await fetch(`${API_BASE}/api/test/natija`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, topic_code: mavzu.topic_code, topic_codes: test.topic_codes,
          javoblar, attempt_id: test.attempt_id, jami_savol_soni: test.savollar.length,
          source_type: "club_online", duration_seconds: Math.max(1, Math.round((Date.now() - boshlangan.current) / 1000)) }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof d.detail === "string" ? d.detail : "Natija saqlanmadi");
      setNatija(d);
    } catch (e) { setXato(e.message); } finally { setBand(false); }
  };

  if (band && !test) return <div className="px-5 py-12 text-center"><Loader2 size={24} className="animate-spin mx-auto"/><p className="text-xs mt-2">{__kbUi("Mustahkamlash testi tuzilmoqda…")}</p></div>;
  if (xato && !test) return <div className="px-5 py-8"><button onClick={onOrtga} className="font-bold mb-4">{__kbUi("← Mavzuga qaytish")}</button><p className="rounded-xl bg-red-50 text-red-700 p-4 text-sm">{__kbUi(xato)}</p></div>;
  if (natija) {
    const foiz = Number(natija.foiz ?? natija.umumiy_foiz ?? natija.natija_foizi ?? 0);
    return <div className="px-5 py-10 max-w-xl mx-auto text-center"><div className="text-5xl">{foiz >= 80 ? __kbUi("🏆") : foiz >= 65 ? __kbUi("✅") : __kbUi("🔁")}</div><h2 className="text-3xl font-black mt-3">{foiz}%</h2><p className="text-sm mt-2" style={{ color: "#687987" }}>{foiz >= 80 ? __kbUi("Mavzu mustahkamlandi.") : foiz >= 65 ? __kbUi("Yaxshi. Bu mavzu spiral takrorlashda yana chiqadi.") : __kbUi("Mavzuni qayta ko‘rib, yana bir bor ishlang.")}</p><button onClick={onOrtga} className="mt-5 px-5 py-3 rounded-xl text-white font-black" style={{ background: "#1B4B7A" }}>{__kbUi("Mavzuga qaytish")}</button></div>;
  }
  if (!savol) return null;
  const bolim = { asosiy: ["Bugungi mavzu", "#1B4B7A"], spiral: ["Spiral takrorlash", "#8A5A1C"], erkin: ["Erkin takrorlash", "#6B4AA0"] }[savol.bolim];
  const variantlar = [["A", savol.option_a], ["B", savol.option_b], ["C", savol.option_c], ["D", savol.option_d]].filter(([, qiymat]) => qiymat);
  return <div className="px-4 py-5 max-w-2xl mx-auto">
    <div className="flex justify-between mb-3"><button onClick={onOrtga} className="text-sm font-bold">← <InterfaceText text={__kbUi("Chiqish")}/></button><b className="text-sm">{indeks + 1}/{test.savollar.length}</b></div>
    <div className="h-2 rounded-full bg-slate-200 overflow-hidden mb-4"><div className="h-full" style={{ width: `${(indeks + 1) * 100 / test.savollar.length}%`, background: bolim[1] }}/></div>
    <div className="flex flex-wrap gap-2 mb-3"><span className="px-2.5 py-1 rounded-full text-[11px] font-black text-white" style={{ background: bolim[1] }}>{__kbUi(bolim[0])}</span><span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-slate-100">{test.tarkib.asosiy} + {test.tarkib.spiral} + {test.tarkib.erkin}</span></div>
    <div className="rounded-2xl border bg-white p-4 md:p-6" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
      {savol.rasm_id && <img src={savol.rasm_id.startsWith("/") ? `${API_BASE}${savol.rasm_id}` : savol.rasm_id} alt={uiT("Savol")} className="max-h-72 mx-auto rounded-xl mb-4"/>}
      <div className="font-bold text-base"><SavolFormulasi ifoda={savol.question}/></div>
      {savol.question_type === "write_answer" ? <div className="flex gap-2 mt-4"><input value={tanlangan} disabled={Boolean(tekshiruv)} onChange={(e) => setTanlangan(e.target.value)} placeholder={__kbUi("Javobni yozing")} className="min-w-0 flex-1 rounded-xl border px-3 py-2"/><button disabled={!tanlangan || band || Boolean(tekshiruv)} onClick={() => javobniTekshir(tanlangan)} className="px-3 rounded-xl text-white font-bold" style={{ background: bolim[1] }}>{__kbUi("Tekshirish")}</button></div>
      : <div className="grid gap-2 mt-4">{variantlar.map(([harf, matn]) => <button key={harf} disabled={band || Boolean(tekshiruv)} onClick={() => javobniTekshir(harf)} className="rounded-xl border p-3 text-left text-sm" style={{ borderColor: tanlangan === harf ? bolim[1] : "#E5E1D8", background: tanlangan === harf ? "#EEF4F8" : "white" }}><b className="mr-2">{harf}.</b>{matn}</button>)}</div>}
      {xato && <p className="text-xs text-red-700 mt-3">{__kbUi(xato)}</p>}
      {tekshiruv && <div className="mt-4 rounded-xl p-3 text-sm" style={{ background: tekshiruv.togrimi ? "#EDF8F1" : "#FFF0EE", color: tekshiruv.togrimi ? "#2E6C55" : "#A32D2D" }}><b>{tekshiruv.togrimi ? __kbUi("To‘g‘ri!") : __kbUi(`Noto‘g‘ri. To‘g‘ri javob: ${tekshiruv.togri_javob}`)}</b>{tekshiruv.tushuntirish && <p className="mt-1">{tekshiruv.tushuntirish}</p>}<button disabled={band} onClick={keyingi} className="w-full mt-3 py-2 rounded-lg text-white font-black" style={{ background: bolim[1] }}>{indeks + 1 === test.savollar.length ? __kbUi("Natijani ko‘rish") : __kbUi("Keyingi savol")}</button></div>}
    </div>
  </div>;
}

function TogarakAzoMavzulari({ token, togarak, onOrtga, onKalendar, ochiladiganTopicCode, ochilganiBildir, foydalanuvchi = null }) {
  useKbInterfaceLocale();
  const [mavzular, setMavzular] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");
  const [tanlanganMavzu, setTanlanganMavzu] = useState(null);
  const [kontentlar, setKontentlar] = useState(null);
  const [kitobOchiq, setKitobOchiq] = useState(false);
  const [testOchiq, setTestOchiq] = useState(false);
  const [oqilayotganId, setOqilayotganId] = useState(null);
  const [joriySozIndeksi, setJoriySozIndeksi] = useState(-1);
  const ovozAsosiyTil = _ovozTiliniTuzat(foydalanuvchi?.asosiy_til || "uz");
  const tanlanganOvozJinsi = _ovozJinsiniTuzat(foydalanuvchi?.ovoz_jinsi || foydalanuvchi?.jins || "qiz");
  const korilganVideolar = useRef(new Set());

  useEffect(() => {
    fetch(`${API_BASE}/api/togarak_azo/mavzularim?token=${encodeURIComponent(token)}&togarak_id=${togarak.id}`)
      .then(async (r) => {
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.detail || `Server xatosi (${r.status})`);
        return d;
      })
      .then((d) => { setMavzular(d.mavzular || []); setYuklanmoqda(false); })
      .catch((e) => { setXato(e.message || "Yuklab bo'lmadi"); setYuklanmoqda(false); });
  }, [token, togarak.id]);

  const mavzuOch = (m) => {
    setTanlanganMavzu(m); setKontentlar(null);
    fetch(`${API_BASE}/api/togarak_azo/mavzu_kontentlari?token=${encodeURIComponent(token)}&togarak_id=${togarak.id}&topic_code=${encodeURIComponent(m.topic_code)}`)
      .then((r) => r.json())
      .then((d) => setKontentlar(d.kontentlar || []))
      .catch(() => setKontentlar([]));
  };

  // Kalendardan "shu kunning mavzusi"ni bosib kirilganda — ro'yxat
  // yuklangach, o'sha mavzuni avtomatik ochamiz.
  useEffect(() => {
    if (!ochiladiganTopicCode || mavzular.length === 0) return;
    const m = mavzular.find((x) => x.topic_code === ochiladiganTopicCode);
    if (m) mavzuOch(m);
    ochilganiBildir?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ochiladiganTopicCode, mavzular]);

  const videoKorildi = (biriktirmaId) => {
    if (korilganVideolar.current.has(biriktirmaId)) return;
    korilganVideolar.current.add(biriktirmaId);
    fetch(`${API_BASE}/api/togarak_azo/video_korildi?token=${encodeURIComponent(token)}&biriktirma_id=${biriktirmaId}`, { method: "POST" }).catch(() => {});
  };

  const youtubeIdOl = (url) => {
    const m = (url || "").match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/))([\w-]{11})/);
    return m ? m[1] : null;
  };

  if (tanlanganMavzu && kitobOchiq) {
    return (
      <OquvchiKitobKorish token={token} togarak={togarak} topicCode={tanlanganMavzu.topic_code} mavzuNomi={formatTopicTitle(0, tanlanganMavzu)}
        onOrtga={() => setKitobOchiq(false)} foydalanuvchi={foydalanuvchi} />
    );
  }

  if (tanlanganMavzu && testOchiq) {
    return <MustahkamlashTestOynasi token={token} mavzu={tanlanganMavzu} togarakId={togarak.id} onOrtga={() => setTestOchiq(false)} />;
  }

  if (tanlanganMavzu) {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => { setTanlanganMavzu(null); setKontentlar(null); window.speechSynthesis?.cancel(); setOqilayotganId(null); }}
          className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Mavzular")}/></button>
        <h1 className="text-xl font-bold mb-3" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(formatTopicTitle(0, tanlanganMavzu))}</h1>
        <button onClick={() => setKitobOchiq(true)} className="w-full rounded-2xl bg-white border flex items-center gap-3 px-4 py-3.5 mb-5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <span className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: "#EAF3DE" }}>
            <BookOpen size={18} style={{ color: "#3B6D11" }} />
          </span>
          <span className="text-sm font-semibold flex-1 text-left" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Kitobni ochish")}</span>
          <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
        </button>

        <button onClick={() => setTestOchiq(true)} className="w-full rounded-2xl border flex items-center gap-3 px-4 py-3.5 mb-5 text-left" style={{ borderColor: "#B9CCE0", background: "#EEF4F8" }}>
          <span className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 text-white font-black" style={{ backgroundColor: "#1B4B7A" }}>✓</span>
          <span className="flex-1"><span className="text-sm font-black block" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Mavzuni mustahkamlash")}</span><span className="text-[11px] block mt-0.5" style={{ color: "#687987" }}>{__kbUi("Asosiy test + 5 spiral + 3 erkin takrorlash")}</span></span>
          <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} />
        </button>

        {kontentlar === null ? (
          <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
        ) : kontentlar.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bu mavzuga hali kontent qo'shilmagan.")}</p>
        ) : (
          <div className="space-y-4">
            {kontentlar.map((k) => (
              <div key={k.id} className="rounded-2xl p-4 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                {k.sarlavha && <p className="text-sm font-semibold mb-2" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{k.sarlavha}</p>}

                {k.kontent_turi === "matn" && (
                  <>
                    <OqiladiganMatn matn={k.matn} joriySozIndeksi={oqilayotganId === k.id ? joriySozIndeksi : -1} />
                    <OvozliOqishTugmasi matn={k.matn} kontentId={k.id} oqilayotganId={oqilayotganId} setOqilayotganId={setOqilayotganId}
                      joriySozIndeksi={joriySozIndeksi} setJoriySozIndeksi={setJoriySozIndeksi} asosiyTil={ovozAsosiyTil} ovozJinsi={tanlanganOvozJinsi} />
                  </>
                )}

                {k.kontent_turi === "latex" && (
                  <>
                    <SavolFormulasi ifoda={k.matn} />
                    <OvozliOqishTugmasi matn={k.matn} kontentId={k.id} oqilayotganId={oqilayotganId} setOqilayotganId={setOqilayotganId}
                      joriySozIndeksi={joriySozIndeksi} setJoriySozIndeksi={setJoriySozIndeksi} asosiyTil={ovozAsosiyTil} ovozJinsi={tanlanganOvozJinsi} />
                  </>
                )}

                {k.kontent_turi === "rasm" && (
                  <img src={`${API_BASE}/api/oqituvchi/togarak_kontent_fayl?biriktirma_id=${k.id}&token=${encodeURIComponent(token)}`}
                    alt={k.sarlavha || __kbUi("rasm")} className="w-full rounded-xl" />
                )}

                {k.kontent_turi === "pdf" && (
                  <a href={`${API_BASE}/api/oqituvchi/togarak_kontent_fayl?biriktirma_id=${k.id}&token=${encodeURIComponent(token)}`}
                    target="_blank" rel="noreferrer"
                    className="block text-center text-xs font-semibold py-2.5 rounded-lg" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("📄 PDF'ni ochish")}</a>
                )}

                {k.kontent_turi === "word" && (
                  <>
                    {k.matn ? (
                      <>
                        <OqiladiganMatn matn={k.matn} joriySozIndeksi={oqilayotganId === k.id ? joriySozIndeksi : -1} />
                        <OvozliOqishTugmasi matn={k.matn} kontentId={k.id} oqilayotganId={oqilayotganId} setOqilayotganId={setOqilayotganId}
                          joriySozIndeksi={joriySozIndeksi} setJoriySozIndeksi={setJoriySozIndeksi} asosiyTil={ovozAsosiyTil} ovozJinsi={tanlanganOvozJinsi} />
                      </>
                    ) : (
                      <a href={`${API_BASE}/api/oqituvchi/togarak_kontent_fayl?biriktirma_id=${k.id}&token=${encodeURIComponent(token)}`}
                        target="_blank" rel="noreferrer"
                        className="block text-center text-xs font-semibold py-2.5 rounded-lg" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("📝 Word faylni ochish")}</a>
                    )}
                  </>
                )}

                {k.kontent_turi === "video" && (
                  <div>
                    {youtubeIdOl(k.video_havola) ? (
                      <div className="rounded-xl overflow-hidden mb-2" style={{ aspectRatio: "16/9" }}>
                        <iframe className="w-full h-full" src={`https://www.youtube.com/embed/${youtubeIdOl(k.video_havola)}`}
                          title={k.sarlavha || __kbUi("video")} allowFullScreen />
                      </div>
                    ) : (
                      <a href={k.video_havola} target="_blank" rel="noreferrer" onClick={() => videoKorildi(k.id)}
                        className="block text-center text-xs font-semibold py-2.5 rounded-lg mb-2" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("▶️ Videoni ochish")}</a>
                    )}
                    <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>👁 {k.korilish_soni}{__kbUi(" marta ko'rilgan")}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Profil")}/></button>
      <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>📚 <InterfaceText text={__kbUi("Mavzular")}/></h1>
      <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{togarak.nomi}</p>
      {onKalendar && (
        <button onClick={onKalendar} className="w-full rounded-2xl bg-white border flex items-center gap-3 px-4 py-3.5 mb-5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <span className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
            <Calendar size={18} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} />
          </span>
          <span className="text-sm font-semibold flex-1 text-left" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Mening kalendarim")}</span>
          <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
        </button>
      )}
      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : xato ? (
        <p className="text-sm font-medium" style={{ color: "#A32D2D" }}>⚠️ {__kbUi(xato)}</p>
      ) : mavzular.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali mavzu qo'shilmagan.")}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {mavzular.map((m, index) => (
            <button key={m.topic_code} onClick={() => mavzuOch({ ...m, tartib_raqami: index + 1 })}
              className="w-full text-left rounded-xl p-3.5 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div>
                <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(formatTopicTitle(index, m))}</p>
              </div>
              <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

const HAFTA_KUN_QISQA = { 1: "Dush", 2: "Sesh", 3: "Chor", 4: "Pay", 5: "Juma", 6: "Shan", 7: "Yak" };
const HAFTA_KUN_TOLIQ = { 1: "Dushanba", 2: "Seshanba", 3: "Chorshanba", 4: "Payshanba", 5: "Juma", 6: "Shanba", 7: "Yakshanba" };
const OY_NOMLARI = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"];

function _sanaFmt(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function _haftaBoshi(d) {
  const n = new Date(d);
  const kun = n.getDay() === 0 ? 7 : n.getDay(); // 1=Dush...7=Yak
  n.setDate(n.getDate() - (kun - 1));
  n.setHours(0, 0, 0, 0);
  return n;
}

function TogarakKalendarReja({ token, togarakId, togarakNomi, onOrtga, onAzolar, onMavzular, onSozlamalar, onJurnal }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [korinishTuri, setKorinishTuri] = useState("hafta"); // "hafta" | "oy"
  const [ankor, setAnkor] = useState(() => new Date()); // hafta yoki oyni belgilaydigan sana
  const [darsKunlari, setDarsKunlari] = useState(null); // [1,3,5] | null (hali yuklanmagan)
  const [kunlarTanlovOchiq, setKunlarTanlovOchiq] = useState(false);
  const [vaqtinchaKunlar, setVaqtinchaKunlar] = useState([]);
  const [kunlarSaqlanmoqda, setKunlarSaqlanmoqda] = useState(false);
  const [sanalar, setSanalar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");
  const [tanlanganSana, setTanlanganSana] = useState(null); // mavzu tanlash uchun ochilgan sana
  const [togarakMavzulari, setTogarakMavzulari] = useState(null); // to'garakning o'z mavzulari (lazy)
  const [mavzuQidiruv, setMavzuQidiruv] = useState("");
  const [biriktirilmoqda, setBiriktirilmoqda] = useState(false);
  const [avtomatikToldirilmoqda, setAvtomatikToldirilmoqda] = useState(false);
  const [avtomatikXabar, setAvtomatikXabar] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/oqituvchi/togarak_dars_kunlari?token=${encodeURIComponent(token)}&togarak_id=${togarakId}`)
      .then((r) => r.json())
      .then((d) => setDarsKunlari(d.kunlar || []))
      .catch(() => setDarsKunlari([]));
  }, [token, togarakId]);

  const { boshlanish, tugash } = useMemo(() => {
    if (korinishTuri === "hafta") {
      const b = _haftaBoshi(ankor);
      const t = new Date(b); t.setDate(t.getDate() + 6);
      return { boshlanish: b, tugash: t };
    }
    const b = new Date(ankor.getFullYear(), ankor.getMonth(), 1);
    const t = new Date(ankor.getFullYear(), ankor.getMonth() + 1, 0);
    return { boshlanish: b, tugash: t };
  }, [ankor, korinishTuri]);

  const kalendarniYukla = () => {
    setYuklanmoqda(true); setXato("");
    fetch(`${API_BASE}/api/oqituvchi/togarak_kalendar?token=${encodeURIComponent(token)}&togarak_id=${togarakId}&boshlanish=${_sanaFmt(boshlanish)}&tugash=${_sanaFmt(tugash)}`)
      .then((r) => r.json())
      .then((d) => { if (d.detail) throw new Error(d.detail); setSanalar(d.sanalar || []); setYuklanmoqda(false); })
      .catch((e) => { setXato(e.message || "Yuklab bo'lmadi"); setYuklanmoqda(false); });
  };

  useEffect(() => {
    if (darsKunlari === null) return;
    kalendarniYukla();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [darsKunlari, boshlanish.getTime(), tugash.getTime()]);

  const kunlarSaqla = async () => {
    setKunlarSaqlanmoqda(true);
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/togarak_dars_kunlari_belgila`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, togarak_id: togarakId, kunlar: vaqtinchaKunlar }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setDarsKunlari(data.kunlar);
      setKunlarTanlovOchiq(false);
    } catch (e) { setXato(e.message); } finally { setKunlarSaqlanmoqda(false); }
  };

  const sanaBosildi = (sana) => {
    setTanlanganSana(sana);
    setMavzuQidiruv("");
    if (togarakMavzulari === null) {
      fetch(`${API_BASE}/api/oqituvchi/togarak_barcha_mavzular?token=${encodeURIComponent(token)}&togarak_id=${togarakId}`)
        .then((r) => r.json())
        .then((d) => setTogarakMavzulari(d.mavzular || []))
        .catch(() => setTogarakMavzulari([]));
    }
  };

  const mavzuBiriktir = async (topicCode) => {
    setBiriktirilmoqda(true);
    try {
      await fetch(`${API_BASE}/api/oqituvchi/togarak_dars_mavzu_biriktir`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, togarak_id: togarakId, sana: tanlanganSana, topic_code: topicCode }),
      });
      setTanlanganSana(null);
      kalendarniYukla();
    } finally { setBiriktirilmoqda(false); }
  };

  const avtomatikToldir = async () => {
    setAvtomatikToldirilmoqda(true); setAvtomatikXabar("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/togarak_dars_avtomatik_toldir?token=${encodeURIComponent(token)}&togarak_id=${togarakId}&boshlanish=${_sanaFmt(boshlanish)}&tugash=${_sanaFmt(tugash)}`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setAvtomatikXabar(`✓ ${data.toldirilgan_soni} ta kunga mavzu joylashtirildi`);
      kalendarniYukla();
    } catch (e) { setAvtomatikXabar(e.message); } finally { setAvtomatikToldirilmoqda(false); }
  };

  const davrLabel = korinishTuri === "hafta"
    ? `${boshlanish.getDate()}-${tugash.getDate()} ${OY_NOMLARI[tugash.getMonth()]}`
    : `${OY_NOMLARI[ankor.getMonth()]} ${ankor.getFullYear()}`;

  const davrniSurish = (yonalish) => {
    const yangi = new Date(ankor);
    if (korinishTuri === "hafta") yangi.setDate(yangi.getDate() + yonalish * 7);
    else yangi.setMonth(yangi.getMonth() + yonalish);
    setAnkor(yangi);
  };

  const filtrlanganMavzular = (togarakMavzulari || []).filter((m) => {
    if (!mavzuQidiruv.trim()) return true;
    const nomi = topicName(m).toLowerCase();
    return nomi.includes(mavzuQidiruv.trim().toLowerCase());
  });

  const kunKartasiChiqar = (haftaKuni, keng) => {
    const d = new Date(boshlanish);
    d.setDate(d.getDate() + (haftaKuni - 1));
    const sana = _sanaFmt(d);
    const darsKunimi = darsKunlari.includes(haftaKuni);
    const s = sanalar.find((x) => x.sana === sana);
    const bugunmi = sana === _sanaFmt(new Date());

    if (!darsKunimi) {
      return (
        <div key={sana} className={`rounded-xl px-3 py-2.5 ${keng ? "flex items-center gap-2" : ""}`} style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
          <p className="text-xs font-medium" style={{ color: "var(--ui-legacy-color-b0aa98, #B0AA98)" }}>{keng ? __kbUi(HAFTA_KUN_TOLIQ[haftaKuni]) : __kbUi(HAFTA_KUN_QISQA[haftaKuni])}, {__kbUi(d.getDate())}</p>
          <p className="text-[11px] italic" style={{ color: "#C4BFAF" }}>{__kbUi("dars yo'q")}</p>
        </div>
      );
    }
    return (
      <button key={sana} onClick={() => sanaBosildi(sana)}
        className={`w-full rounded-xl bg-white border text-left ${keng ? "flex items-center gap-3.5 p-3.5" : "p-3"}`}
        style={{ borderColor: bugunmi ? "#1B4B7A" : "#E5E1D8", borderWidth: bugunmi ? 2 : 1 }}>
        <div className={`rounded-lg flex items-center justify-center shrink-0 ${keng ? "w-12 h-12 flex-col gap-0" : "w-full mb-1.5 py-1.5 gap-1.5"}`}
          style={{ backgroundColor: s?.mavzu_nomi ? "#EAF3DE" : "#EAF1F7" }}>
          <span className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: s?.mavzu_nomi ? "#3B6D11" : "#1B4B7A" }}>{__kbUi(HAFTA_KUN_QISQA[haftaKuni])}</span>
          <span className={`font-bold leading-tight ${keng ? "text-base" : "text-sm"}`} style={{ color: s?.mavzu_nomi ? "#3B6D11" : "#1B4B7A" }}>{__kbUi(d.getDate())}</span>
        </div>
        <div className="min-w-0 flex-1">
          {!keng && <p className="text-[10px] font-medium mb-0.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{bugunmi ? __kbUi("bugun") : __kbUi("\u00A0")}</p>}
          {keng && <p className="text-[11px] font-medium mb-0.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi(HAFTA_KUN_TOLIQ[haftaKuni])}{bugunmi ? __kbUi(" · bugun") : __kbUi("")}</p>}
          {s?.mavzu_nomi ? (
            <p className={`font-semibold truncate ${keng ? "text-sm" : "text-xs"}`} style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(topicName({ mavzu_name: s.mavzu_nomi }))}</p>
          ) : (
            <p className={`font-medium ${keng ? "text-sm" : "text-xs"}`} style={{ color: "#C89B3C" }}>+ <InterfaceText text={__kbUi("Tanlash")}/></p>
          )}
        </div>
      </button>
    );
  };

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("To'garaklarim")}</button>
      <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{togarakNomi}</h1>
      {onJurnal && <button onClick={onJurnal} className="w-full rounded-2xl px-4 py-3 mb-2 text-left text-white flex items-center gap-3" style={{ backgroundColor: "#28735A" }}>
        <span className="text-2xl" aria-hidden="true">📋</span>
        <span><b className="block text-sm">{__kbUi("Davomat va to‘lovlar")}</b><small className="text-xs opacity-90">{__kbUi("Bugungi yo‘qlama · oylik to‘lov · kim qarzdor")}</small></span>
      </button>}
      <div className="grid grid-cols-3 gap-2 mb-5">
        <button onClick={onAzolar} className="rounded-2xl bg-white border flex flex-col items-center justify-center gap-1.5 py-3.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <span className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
            <Users size={18} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} />
          </span>
          <span className="text-xs font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Talabalar")}</span>
        </button>
        <button onClick={onMavzular} className="rounded-2xl bg-white border flex flex-col items-center justify-center gap-1.5 py-3.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <span className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: "#EAF3DE" }}>
            <BookOpen size={18} style={{ color: "#3B6D11" }} />
          </span>
          <span className="text-xs font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}><InterfaceText text={__kbUi("Mavzular")}/></span>
        </button>
        <button onClick={onSozlamalar} className="rounded-2xl bg-white border flex flex-col items-center justify-center gap-1.5 py-3.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <span className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: "#FDF3E0" }}>
            <Settings size={18} style={{ color: "#8A5A1C" }} />
          </span>
          <span className="text-xs font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}><InterfaceText text={__kbUi("Sozlamalar")}/></span>
        </button>
      </div>

      {darsKunlari !== null && darsKunlari.length === 0 && !kunlarTanlovOchiq && (
        <div className="rounded-2xl p-4 border mb-4" style={{ backgroundColor: "#FDF3E0", borderColor: "#C89B3C" }}>
          <p className="text-sm font-bold mb-1" style={{ color: "#8A5A1C" }}>{__kbUi("📅 Dars kunlarini belgilang")}</p>
          <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Qaysi kunlari dars o'tishingizni belgilasangiz, shu kunlarga mavzu tayinlab chiqishingiz mumkin.")}</p>
          <button onClick={() => { setVaqtinchaKunlar(darsKunlari); setKunlarTanlovOchiq(true); }}
            className="w-full py-2.5 rounded-xl font-semibold text-sm text-white" style={{ backgroundColor: "#C89B3C" }}>{__kbUi("Kunlarni tanlash")}</button>
        </div>
      )}

      {kunlarTanlovOchiq && (
        <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-xs font-semibold mb-3" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Qaysi kunlari dars bo'ladi?")}</p>
          <div className="grid grid-cols-4 gap-1.5 mb-3">
            {[1, 2, 3, 4, 5, 6, 7].map((k) => (
              <button key={k} type="button"
                onClick={() => setVaqtinchaKunlar((prev) => prev.includes(k) ? prev.filter((x) => x !== k) : [...prev, k])}
                className="py-2 rounded-lg border text-xs font-semibold text-center"
                style={{
                  borderColor: vaqtinchaKunlar.includes(k) ? "#1B4B7A" : "#E5E1D8",
                  backgroundColor: vaqtinchaKunlar.includes(k) ? "#1B4B7A" : "#FFFFFF",
                  color: vaqtinchaKunlar.includes(k) ? "#FFFFFF" : "#5A5648",
                }}>
                {__kbUi(HAFTA_KUN_QISQA[k])}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <button onClick={() => setKunlarTanlovOchiq(false)} className="flex-1 py-2.5 rounded-xl border text-sm font-medium" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Bekor")}</button>
            <button onClick={kunlarSaqla} disabled={kunlarSaqlanmoqda || vaqtinchaKunlar.length === 0}
              className="flex-1 py-2.5 rounded-xl font-semibold text-white text-sm"
              style={{ backgroundColor: "#1B4B7A", opacity: (kunlarSaqlanmoqda || vaqtinchaKunlar.length === 0) ? 0.6 : 1 }}>
              {kunlarSaqlanmoqda ? __kbUi("...") : uiT("Saqlash")}
            </button>
          </div>
        </div>
      )}

      {darsKunlari !== null && darsKunlari.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-3">
            <div className="flex rounded-full p-1 gap-0.5" style={{ backgroundColor: "#F0EDE5" }}>
              <button onClick={() => setKorinishTuri("hafta")} className="px-3.5 py-1.5 rounded-full text-xs font-semibold"
                style={korinishTuri === "hafta" ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>{__kbUi("Haftalik")}</button>
              <button onClick={() => setKorinishTuri("oy")} className="px-3.5 py-1.5 rounded-full text-xs font-semibold"
                style={korinishTuri === "oy" ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>{__kbUi("Oylik")}</button>
            </div>
            <button onClick={() => { setVaqtinchaKunlar(darsKunlari); setKunlarTanlovOchiq(true); }} className="text-xs font-medium" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
              {__kbUi(darsKunlari.map((k) => HAFTA_KUN_QISQA[k]).join(", "))} ✏️
            </button>
          </div>

          <div className="flex items-center justify-between mb-3">
            <button onClick={() => davrniSurish(-1)} className="w-8 h-8 rounded-full flex items-center justify-center border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>‹</button>
            <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(davrLabel)}</p>
            <button onClick={() => davrniSurish(1)} className="w-8 h-8 rounded-full flex items-center justify-center border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>›</button>
          </div>

          <button onClick={avtomatikToldir} disabled={avtomatikToldirilmoqda}
            className="w-full py-2.5 rounded-xl font-semibold text-sm mb-3" style={{ backgroundColor: "#EAF3DE", color: "#3B6D11", opacity: avtomatikToldirilmoqda ? 0.7 : 1 }}>
            {avtomatikToldirilmoqda ? __kbUi("...") : __kbUi("🪄 Rejadan avtomatik to'ldirish")}
          </button>
          {avtomatikXabar && <p className="text-xs mb-3 text-center" style={{ color: avtomatikXabar.startsWith("✓") ? "#3B6D11" : "#B0553A" }}>{avtomatikXabar}</p>}

          {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}

          {yuklanmoqda ? (
            <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
          ) : korinishTuri === "hafta" ? (
            <div className="space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-2">
                  {[1, 3, 5].map((hk) => kunKartasiChiqar(hk, false))}
                </div>
                <div className="space-y-2">
                  {[2, 4, 6].map((hk) => kunKartasiChiqar(hk, false))}
                </div>
              </div>
              {__kbUi(kunKartasiChiqar(7, true))}
            </div>
          ) : (
            <div className="rounded-2xl bg-white border p-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div className="grid grid-cols-7 mb-2">
                {[1, 2, 3, 4, 5, 6, 7].map((k) => (
                  <p key={k} className="text-[10px] text-center font-semibold uppercase tracking-wide" style={{ color: darsKunlari.includes(k) ? "#1B4B7A" : "#D8D3C7" }}>
                    {__kbUi(HAFTA_KUN_QISQA[k].slice(0, 2))}
                  </p>
                ))}
              </div>
              <div className="grid grid-cols-7 gap-y-1.5 justify-items-center">
                {__kbUi((() => {
                  const oyBoshi = new Date(ankor.getFullYear(), ankor.getMonth(), 1);
                  const boshiKun = oyBoshi.getDay() === 0 ? 7 : oyBoshi.getDay();
                  const boshlangichBosh = [];
                  for (let i = 1; i < boshiKun; i++) boshlangichBosh.push(<div key={`b${i}`} />);
                  const sanaMap = Object.fromEntries(sanalar.map((s) => [s.sana, s]));
                  const bugunKey = _sanaFmt(new Date());
                  const kunlar = [];
                  const jamiKun = new Date(ankor.getFullYear(), ankor.getMonth() + 1, 0).getDate();
                  for (let kun = 1; kun <= jamiKun; kun++) {
                    const d = new Date(ankor.getFullYear(), ankor.getMonth(), kun);
                    const key = _sanaFmt(d);
                    const s = sanaMap[key];
                    const haftaKuni = d.getDay() === 0 ? 7 : d.getDay();
                    const darsKunimi = darsKunlari.includes(haftaKuni);
                    const bugunmi = key === bugunKey;
                    const mavzuBormi = darsKunimi && s?.mavzu_nomi;
                    kunlar.push(
                      <button key={key} onClick={() => darsKunimi && sanaBosildi(key)} disabled={!darsKunimi}
                        className="w-8 h-8 rounded-full flex items-center justify-center relative"
                        style={{
                          backgroundColor: mavzuBormi ? "#3B6D11" : "transparent",
                          border: bugunmi ? "1.5px solid #1B4B7A" : "1.5px solid transparent",
                        }}>
                        <span className="text-xs font-semibold" style={{ color: mavzuBormi ? "#FFFFFF" : darsKunimi ? "#2B2B2B" : "#D8D3C7" }}>{kun}</span>
                        {darsKunimi && !mavzuBormi && (
                          <span className="absolute bottom-0.5 w-1 h-1 rounded-full" style={{ backgroundColor: "#C89B3C" }} />
                        )}
                      </button>,
                    );
                  }
                  return [...boshlangichBosh, ...kunlar];
                })())}
              </div>
              <div className="flex items-center gap-3.5 mt-3.5 pt-3 border-t" style={{ borderColor: "#F0EDE5" }}>
                <span className="flex items-center gap-1.5 text-[10px]" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
                  <span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: "#3B6D11" }} />{__kbUi(" Mavzu bor")}</span>
                <span className="flex items-center gap-1.5 text-[10px]" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
                  <span className="w-3 h-3 rounded-full inline-flex items-center justify-center" style={{ border: "1px solid #E5E1D8" }}><span className="w-1 h-1 rounded-full" style={{ backgroundColor: "#C89B3C" }} /></span>{__kbUi(" Bo'sh dars kuni")}</span>
              </div>
            </div>
          )}
        </>
      )}

      {tanlanganSana && (
        <div className="fixed inset-0 z-50 flex items-end justify-center" style={{ backgroundColor: "rgba(0,0,0,0.4)" }}>
          <div className="w-full max-w-md rounded-t-2xl p-5 max-h-[80vh] overflow-y-auto" style={{ backgroundColor: "var(--ui-legacy-background-ffffff, #FFFFFF)", boxShadow: "0 -8px 32px rgba(43,43,43,0.18)" }}>
            <div className="w-10 h-1.5 rounded-full mx-auto mb-4" style={{ backgroundColor: "#E5E1D8" }} />
            <div className="flex items-center justify-between mb-3">
              <p className="font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{tanlanganSana}{__kbUi(" uchun mavzu")}</p>
              <button onClick={() => setTanlanganSana(null)} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>✕</button>
            </div>
            {sanalar.find((s) => s.sana === tanlanganSana)?.mavzu_nomi && (
              <button onClick={() => mavzuBiriktir(null)} disabled={biriktirilmoqda}
                className="w-full py-2.5 rounded-xl font-medium text-sm mb-3" style={{ backgroundColor: "#FCEBEB", color: "#A32D2D" }}>{__kbUi("Mavzuni olib tashlash")}</button>
            )}
            <input type="text" value={mavzuQidiruv} onChange={(e) => setMavzuQidiruv(e.target.value)}
              placeholder={__kbUi("Mavzu qidirish...")} className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            {togarakMavzulari === null ? (
              <div className="py-6 text-center"><Loader2 size={20} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
            ) : filtrlanganMavzular.length === 0 ? (
              <p className="text-sm text-center py-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Mavzu topilmadi. Avval \"Mavzular\" bo'limidan to'garakka mavzu qo'shing.")}</p>
            ) : (
              <div className="space-y-1.5">
                {filtrlanganMavzular.map((m, index) => (
                  <button key={m.topic_code} onClick={() => mavzuBiriktir(m.topic_code)} disabled={biriktirilmoqda}
                    className="w-full text-left px-3.5 py-2.5 rounded-xl" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                    <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(formatTopicTitle(index, m))}</p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function MavzuKitobiTahrirlash({ token, togarakId, mavzu, onOrtga }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [videolar, setVideolar] = useState([]);
  const [misollar, setMisollar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");

  const [videoFormaOchiq, setVideoFormaOchiq] = useState(false);
  const [videoSarlavha, setVideoSarlavha] = useState("");
  const [videoHavola, setVideoHavola] = useState("");
  const [videoSaqlanmoqda, setVideoSaqlanmoqda] = useState(false);

  const [misolFormaOchiq, setMisolFormaOchiq] = useState(false);
  const [tahrirlanayotganMisolId, setTahrirlanayotganMisolId] = useState(null);
  const [misolVideoId, setMisolVideoId] = useState("");
  const [misolMasala, setMisolMasala] = useState("");
  const [misolYechim, setMisolYechim] = useState("");
  const [misolSoniya, setMisolSoniya] = useState("");
  const [misolTugashSoniya, setMisolTugashSoniya] = useState("");
  const [misolSaqlanmoqda, setMisolSaqlanmoqda] = useState(false);
  const [kengaytirilganMisolId, setKengaytirilganMisolId] = useState(null);

  const [mustaqilIshlar, setMustaqilIshlar] = useState([]);
  const [ishFormaOchiq, setIshFormaOchiq] = useState(false);
  const [ishSavol, setIshSavol] = useState("");
  const [ishMezon, setIshMezon] = useState("");
  const [ishSaqlanmoqda, setIshSaqlanmoqda] = useState(false);

  const ishlarniYukla = () => {
    fetch(`${API_BASE}/api/oqituvchi/mustaqil_ishlar?token=${encodeURIComponent(token)}&togarak_id=${togarakId}&topic_code=${encodeURIComponent(mavzu.topic_code)}`)
      .then((r) => r.json())
      .then((d) => setMustaqilIshlar(d.ishlar || []))
      .catch(() => {});
  };

  const ishQosh = async () => {
    if (!ishSavol.trim() || !ishMezon.trim()) { setXato("Savol va to'g'ri javob mezonini kiriting"); return; }
    setIshSaqlanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/mustaqil_ish_qosh`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, togarak_id: togarakId, topic_code: mavzu.topic_code, savol_matni: ishSavol.trim(), togri_javob_mezoni: ishMezon.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setIshSavol(""); setIshMezon(""); setIshFormaOchiq(false);
      ishlarniYukla();
    } catch (e) { setXato(e.message); } finally { setIshSaqlanmoqda(false); }
  };

  const ishOchir = async (ishId) => {
    await fetch(`${API_BASE}/api/oqituvchi/mustaqil_ish_ochir?token=${encodeURIComponent(token)}&ish_id=${ishId}`, { method: "DELETE" });
    ishlarniYukla();
  };

  const yukla = () => {
    setYuklanmoqda(true); setXato("");
    fetch(`${API_BASE}/api/oqituvchi/mavzu_kitobi?token=${encodeURIComponent(token)}&togarak_id=${togarakId}&topic_code=${encodeURIComponent(mavzu.topic_code)}`)
      .then(async (r) => {
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.detail || `Server xatosi (${r.status})`);
        return d;
      })
      .then((d) => { setVideolar(d.videolar || []); setMisollar(d.misollar || []); setYuklanmoqda(false); })
      .catch((e) => { setXato(e.message || "Yuklab bo'lmadi"); setYuklanmoqda(false); });
  };

  useEffect(() => { yukla(); ishlarniYukla(); }, [token, togarakId, mavzu.topic_code]); // eslint-disable-line react-hooks/exhaustive-deps

  const videoQosh = async () => {
    if (!videoHavola.trim()) { setXato("Video havolasini kiriting"); return; }
    setVideoSaqlanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/mavzu_video_qosh`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, togarak_id: togarakId, topic_code: mavzu.topic_code, sarlavha: videoSarlavha.trim() || null, video_havola: videoHavola.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setVideoSarlavha(""); setVideoHavola(""); setVideoFormaOchiq(false);
      yukla();
    } catch (e) { setXato(e.message); } finally { setVideoSaqlanmoqda(false); }
  };

  const videoOchir = async (videoId) => {
    await fetch(`${API_BASE}/api/oqituvchi/mavzu_video_ochir?token=${encodeURIComponent(token)}&video_id=${videoId}`, { method: "DELETE" });
    yukla();
  };

  const misolFormaniOch = (misol) => {
    if (misol) {
      setTahrirlanayotganMisolId(misol.id);
      setMisolVideoId(misol.video_id ? String(misol.video_id) : "");
      setMisolMasala(misol.masala_matni);
      setMisolYechim(misol.yechim_matni || "");
      setMisolSoniya(misol.video_soniya != null ? String(misol.video_soniya) : "");
      setMisolTugashSoniya(misol.video_tugash_soniya != null ? String(misol.video_tugash_soniya) : "");
    } else {
      setTahrirlanayotganMisolId(null);
      setMisolVideoId(videolar.length > 0 ? String(videolar[videolar.length - 1].id) : "");
      setMisolMasala(""); setMisolYechim(""); setMisolSoniya(""); setMisolTugashSoniya("");
    }
    setMisolFormaOchiq(true);
  };

  const misolSaqla = async () => {
    if (!misolMasala.trim()) { setXato("Masala matnini kiriting"); return; }
    setMisolSaqlanmoqda(true); setXato("");
    const goVideoId = misolVideoId ? Number(misolVideoId) : null;
    const goSoniya = misolSoniya.trim() ? Number(misolSoniya) : null;
    const goTugashSoniya = misolTugashSoniya.trim() ? Number(misolTugashSoniya) : null;
    try {
      const yol = tahrirlanayotganMisolId ? "mavzu_misol_tahrirlash" : "mavzu_misol_qosh";
      const tana = tahrirlanayotganMisolId
        ? { token, misol_id: tahrirlanayotganMisolId, video_id: goVideoId, masala_matni: misolMasala.trim(), yechim_matni: misolYechim.trim() || null, video_soniya: goSoniya, video_tugash_soniya: goTugashSoniya }
        : { token, togarak_id: togarakId, topic_code: mavzu.topic_code, video_id: goVideoId, masala_matni: misolMasala.trim(), yechim_matni: misolYechim.trim() || null, video_soniya: goSoniya, video_tugash_soniya: goTugashSoniya };
      const res = await fetch(`${API_BASE}/api/oqituvchi/${yol}`, {
        method: tahrirlanayotganMisolId ? "PUT" : "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(tana),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setMisolFormaOchiq(false); setTahrirlanayotganMisolId(null);
      yukla();
    } catch (e) { setXato(e.message); } finally { setMisolSaqlanmoqda(false); }
  };

  const misolOchir = async (misolId) => {
    await fetch(`${API_BASE}/api/oqituvchi/mavzu_misol_ochir?token=${encodeURIComponent(token)}&misol_id=${misolId}`, { method: "DELETE" });
    yukla();
  };

  const misolSur = async (misolId, yonalish) => {
    await fetch(`${API_BASE}/api/oqituvchi/mavzu_misol_surish`, {
      method: "PUT", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, misol_id: misolId, yonalish }),
    });
    yukla();
  };

  const soniyaniVaqtga = (s) => {
    if (s == null) return null;
    const daq = Math.floor(s / 60); const son = s % 60;
    return `${daq}:${String(son).padStart(2, "0")}`;
  };

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi(topicName(mavzu))}</button>
      <h1 className="text-xl font-bold mb-5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📖 Kitob tuzish")}</h1>

      {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>⚠️ {__kbUi(xato)}</p>}
      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : (
        <>
          <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-semibold" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("🎬 Videolar")}</p>
              <button onClick={() => setVideoFormaOchiq(!videoFormaOchiq)} className="text-xs font-semibold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
                {videoFormaOchiq ? __kbUi("✕ Yopish") : __kbUi("+ Video")}
              </button>
            </div>
            {videoFormaOchiq && (
              <div className="rounded-xl p-3 mb-3" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                <input type="text" value={videoSarlavha} onChange={(e) => setVideoSarlavha(e.target.value)} placeholder={__kbUi("Sarlavha (ixtiyoriy)")}
                  className="w-full px-3 py-2 rounded-lg border text-sm mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                <input type="text" value={videoHavola} onChange={(e) => setVideoHavola(e.target.value)} placeholder={__kbUi("Video havolasi (YouTube yoki boshqa)")}
                  className="w-full px-3 py-2 rounded-lg border text-sm mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                <button onClick={videoQosh} disabled={videoSaqlanmoqda}
                  className="w-full py-2 rounded-lg font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: videoSaqlanmoqda ? 0.7 : 1 }}>
                  {videoSaqlanmoqda ? __kbUi("...") : uiT("Qo'shish")}
                </button>
              </div>
            )}
            {videolar.length === 0 ? (
              <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali video qo'shilmagan.")}</p>
            ) : (
              <div className="space-y-1.5">
                {videolar.map((v, i) => (
                  <div key={v.id} className="flex items-center justify-between gap-2 rounded-lg px-3 py-2" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold truncate" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{i + 1}. {v.sarlavha || uiT("Video")}</p>
                      <p className="text-[11px] truncate" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{v.video_havola}</p>
                    </div>
                    <button onClick={() => videoOchir(v.id)} className="text-xs font-semibold shrink-0" style={{ color: "#A32D2D" }}>✕</button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-semibold" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("📚 Misollar (")}{misollar.length})</p>
              <button onClick={() => misolFormaniOch(null)} className="text-xs font-semibold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("+ Misol")}</button>
            </div>

            {misolFormaOchiq && (
              <div className="rounded-xl p-3 mb-3" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                <label className="text-[11px] font-medium mb-1 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Qaysi videoga tegishli (ixtiyoriy)")}</label>
                <select value={misolVideoId} onChange={(e) => setMisolVideoId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border text-sm mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                  <option value="">{__kbUi("— Bog'lanmagan —")}</option>
                  {videolar.map((v, i) => <option key={v.id} value={v.id}>{i + 1}. {v.sarlavha || uiT("Video")}</option>)}
                </select>
                <label className="text-[11px] font-medium mb-1 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Masala matni (LaTeX: $...$ ishlatishingiz mumkin)")}</label>
                <textarea value={misolMasala} onChange={(e) => setMisolMasala(e.target.value)} rows={3}
                  className="w-full px-3 py-2 rounded-lg border text-sm mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                <label className="text-[11px] font-medium mb-1 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Yechim / tushuntirish")}</label>
                <textarea value={misolYechim} onChange={(e) => setMisolYechim(e.target.value)} rows={3}
                  className="w-full px-3 py-2 rounded-lg border text-sm mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                <label className="text-[11px] font-medium mb-1 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Videoning qaysi qismi (soniyada, ixtiyoriy)")}</label>
                <div className="flex items-center gap-2 mb-2">
                  <input type="number" min="0" value={misolSoniya} onChange={(e) => setMisolSoniya(e.target.value)} placeholder={__kbUi("boshlanishi, masalan 245")}
                    className="flex-1 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                  <span className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>—</span>
                  <input type="number" min="0" value={misolTugashSoniya} onChange={(e) => setMisolTugashSoniya(e.target.value)} placeholder={__kbUi("tugashi, masalan 310")}
                    className="flex-1 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                </div>
                <div className="flex gap-2">
                  <button onClick={() => { setMisolFormaOchiq(false); setTahrirlanayotganMisolId(null); }} className="flex-1 py-2 rounded-lg border text-sm font-medium" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Bekor")}</button>
                  <button onClick={misolSaqla} disabled={misolSaqlanmoqda}
                    className="flex-1 py-2 rounded-lg font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: misolSaqlanmoqda ? 0.7 : 1 }}>
                    {misolSaqlanmoqda ? __kbUi("...") : tahrirlanayotganMisolId ? uiT("Saqlash") : uiT("Qo'shish")}
                  </button>
                </div>
              </div>
            )}

            {misollar.length === 0 ? (
              <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali misol qo'shilmagan.")}</p>
            ) : (
              <div className="space-y-2">
                {misollar.map((m, i) => {
                  const videoNomi = videolar.find((v) => v.id === m.video_id);
                  const ochiqmi = kengaytirilganMisolId === m.id;
                  return (
                    <div key={m.id} className="rounded-xl border overflow-hidden" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                      <button onClick={() => setKengaytirilganMisolId(ochiqmi ? null : m.id)} className="w-full text-left px-3.5 py-3">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-bold shrink-0" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{i + 1}.</span>
                          {videoNomi && (
                            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
                              🎬 {soniyaniVaqtga(m.video_soniya) ? __kbUi(`${soniyaniVaqtga(m.video_soniya)}${m.video_tugash_soniya != null ? `–${soniyaniVaqtga(m.video_tugash_soniya)}` : ""}`) : (videoNomi.sarlavha || __kbUi("video"))}
                            </span>
                          )}
                        </div>
                        <AralashMatn matn={m.masala_matni} className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }} />
                      </button>
                      {ochiqmi && (
                        <div className="px-3.5 pb-3.5 pt-1 space-y-2.5" style={{ borderTop: "1px solid #F0EDE5" }}>
                          {m.yechim_matni && (
                            <div className="rounded-lg p-2.5 mt-2" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                              <p className="text-[10px] font-semibold mb-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("YECHIM")}</p>
                              <AralashMatn matn={m.yechim_matni} className="text-sm" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }} />
                            </div>
                          )}
                          <div className="flex items-center gap-2 pt-1">
                            <button onClick={() => misolSur(m.id, "yuqori")} disabled={i === 0} className="w-7 h-7 rounded-full border flex items-center justify-center text-xs" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", opacity: i === 0 ? 0.3 : 1 }}>↑</button>
                            <button onClick={() => misolSur(m.id, "pastga")} disabled={i === misollar.length - 1} className="w-7 h-7 rounded-full border flex items-center justify-center text-xs" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", opacity: i === misollar.length - 1 ? 0.3 : 1 }}>↓</button>
                            <button onClick={() => misolFormaniOch(m)} className="text-xs font-semibold ml-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}><InterfaceText text={__kbUi("Tahrirlash")}/></button>
                            <button onClick={() => misolOchir(m.id)} className="text-xs font-semibold" style={{ color: "#A32D2D" }}><InterfaceText text={__kbUi("O'chirish")}/></button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-semibold" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("📝 Mustaqil ishlar (")}{mustaqilIshlar.length})</p>
              <button onClick={() => setIshFormaOchiq(!ishFormaOchiq)} className="text-xs font-semibold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
                {ishFormaOchiq ? __kbUi("✕ Yopish") : __kbUi("+ Topshiriq")}
              </button>
            </div>
            <p className="text-[11px] mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("O'quvchi kitobni o'rgangach, shu savollarga ERKIN matnda javob yozadi — AI sizning yozgan mezoningiz asosida tekshiradi.")}</p>

            {ishFormaOchiq && (
              <div className="rounded-xl p-3 mb-3" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                <label className="text-[11px] font-medium mb-1 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Savol matni")}</label>
                <textarea value={ishSavol} onChange={(e) => setIshSavol(e.target.value)} rows={2}
                  placeholder={__kbUi("masalan: 12 va 18 sonlarining EKUBini toping va yechim yo'lini tushuntiring")}
                  className="w-full px-3 py-2 rounded-lg border text-sm mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                <label className="text-[11px] font-medium mb-1 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("To'g'ri javob mezoni (AI shunga qarab tekshiradi)")}</label>
                <textarea value={ishMezon} onChange={(e) => setIshMezon(e.target.value)} rows={2}
                  placeholder={__kbUi("masalan: To'g'ri javob 6. O'quvchi ikkala sonni tub ko'paytuvchilarga ajratib, umumiy ko'paytuvchilarni topgan bo'lishi kerak.")}
                  className="w-full px-3 py-2 rounded-lg border text-sm mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                <button onClick={ishQosh} disabled={ishSaqlanmoqda}
                  className="w-full py-2 rounded-lg font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: ishSaqlanmoqda ? 0.7 : 1 }}>
                  {ishSaqlanmoqda ? __kbUi("...") : uiT("Qo'shish")}
                </button>
              </div>
            )}

            {mustaqilIshlar.length === 0 ? (
              <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali topshiriq qo'shilmagan.")}</p>
            ) : (
              <div className="space-y-2">
                {mustaqilIshlar.map((ish, i) => (
                  <div key={ish.id} className="rounded-xl p-3" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                    <div className="flex items-start justify-between gap-2">
                      <AralashMatn matn={`${i + 1}. ${ish.savol_matni}`} className="text-sm font-medium flex-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }} />
                      <button onClick={() => ishOchir(ish.id)} className="text-xs font-semibold shrink-0" style={{ color: "#A32D2D" }}>✕</button>
                    </div>
                    <p className="text-[11px] mt-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Mezon: ")}{ish.togri_javob_mezoni}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function TogarakMavzularBoshqarish({ token, togarakId, onOrtga }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [mavzular, setMavzular] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [qidiruvOchiq, setQidiruvOchiq] = useState(false);
  const [qidiruv, setQidiruv] = useState("");
  const [qidiruvNatijalari, setQidiruvNatijalari] = useState(null);
  const [qidirilmoqda, setQidirilmoqda] = useState(false);

  const [tanlanganMavzu, setTanlanganMavzu] = useState(null);
  const [kontentlar, setKontentlar] = useState(null);
  const [kitobOchiq, setKitobOchiq] = useState(false);
  const [kontentTuriFormasi, setKontentTuriFormasi] = useState(null); // "matn" | "latex" | "video" | "fayl" | null
  const [sarlavha, setSarlavha] = useState("");
  const [matn, setMatn] = useState("");
  const [videoHavola, setVideoHavola] = useState("");
  const [saqlanmoqda, setSaqlanmoqda] = useState(false);
  const [xato, setXato] = useState("");

  const [testShablonOchiq, setTestShablonOchiq] = useState(false);
  const [testTanlanganKodlar, setTestTanlanganKodlar] = useState({}); // {topic_code: soni}
  const [testYuklanmoqda, setTestYuklanmoqda] = useState(false);
  const [testImportlanmoqda, setTestImportlanmoqda] = useState(false);
  const [testNatija, setTestNatija] = useState(null);

  const [yangiMavzuOchiq, setYangiMavzuOchiq] = useState(false);
  const [yangiMavzuNomi, setYangiMavzuNomi] = useState("");
  const [yangiMavzuBob, setYangiMavzuBob] = useState("");
  const [yangiMavzuYaratilmoqda, setYangiMavzuYaratilmoqda] = useState(false);
  const [kopMavzuRejimi, setKopMavzuRejimi] = useState(false);
  const [kopMavzuMatni, setKopMavzuMatni] = useState("");
  const [kopMavzuYaratilmoqda, setKopMavzuYaratilmoqda] = useState(false);
  const [kopMavzuProgress, setKopMavzuProgress] = useState("");

  const mavzularniYukla = () => {
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/oqituvchi/togarak_barcha_mavzular?token=${encodeURIComponent(token)}&togarak_id=${togarakId}`)
      .then(async (r) => {
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.detail || `Server xatosi (${r.status})`);
        return d;
      })
      .then((d) => { setMavzular(d.mavzular || []); setXato(""); setYuklanmoqda(false); })
      .catch((e) => { setXato(e.message || "Yuklab bo'lmadi"); setYuklanmoqda(false); });
  };
  useEffect(mavzularniYukla, [token, togarakId]);

  const [qidiruvXato, setQidiruvXato] = useState("");

  useEffect(() => {
    if (!qidiruvOchiq) return;
    setQidirilmoqda(true);
    const kechiktirish = setTimeout(() => {
      fetch(`${API_BASE}/api/oqituvchi/togarak_milliy_mavzular_qidir?token=${encodeURIComponent(token)}&togarak_id=${togarakId}${qidiruv.trim() ? `&qidiruv=${encodeURIComponent(qidiruv.trim())}` : ""}`)
        .then(async (r) => {
          const d = await r.json().catch(() => ({}));
          if (!r.ok) throw new Error(d.detail || `Server xatosi (${r.status})`);
          return d;
        })
        .then((d) => { setQidiruvNatijalari(d.mavzular || []); setQidiruvXato(""); setQidirilmoqda(false); })
        .catch((e) => { setQidiruvXato(e.message || "Yuklab bo'lmadi"); setQidirilmoqda(false); });
    }, 350);
    return () => clearTimeout(kechiktirish);
  }, [qidiruv, qidiruvOchiq, token, togarakId]);

  const mavzuBiriktir = async (topicCode) => {
    await fetch(`${API_BASE}/api/oqituvchi/togarak_milliy_mavzu_biriktir`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, togarak_id: togarakId, topic_code: topicCode }),
    });
    mavzularniYukla();
  };

  const [barchasiniQoshishYuklanmoqda, setBarchasiniQoshishYuklanmoqda] = useState(false);
  const barchasiniQoshish = async () => {
    const yangilari = (qidiruvNatijalari || []).filter((m) => !mavzular.some((x) => x.topic_code === m.topic_code));
    if (yangilari.length === 0) return;
    setBarchasiniQoshishYuklanmoqda(true);
    try {
      await Promise.all(yangilari.map((m) =>
        fetch(`${API_BASE}/api/oqituvchi/togarak_milliy_mavzu_biriktir`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token, togarak_id: togarakId, topic_code: m.topic_code }),
        })
      ));
      mavzularniYukla();
    } finally { setBarchasiniQoshishYuklanmoqda(false); }
  };

  const mavzuniOlibTashla = async (topicCode) => {
    await fetch(`${API_BASE}/api/oqituvchi/togarak_mavzu_biriktirmasini_ochir?token=${encodeURIComponent(token)}&togarak_id=${togarakId}&topic_code=${encodeURIComponent(topicCode)}`, { method: "DELETE" });
    mavzularniYukla();
    if (tanlanganMavzu?.topic_code === topicCode) setTanlanganMavzu(null);
  };

  const kontentlarniYukla = (topicCode) => {
    fetch(`${API_BASE}/api/oqituvchi/togarak_mavzu_kontentlari?token=${encodeURIComponent(token)}&togarak_id=${togarakId}&topic_code=${encodeURIComponent(topicCode)}`)
      .then((r) => r.json())
      .then((d) => setKontentlar(d.kontentlar || []))
      .catch(() => setKontentlar([]));
  };

  const mavzuOch = (m) => { setTanlanganMavzu(m); setKontentlar(null); kontentlarniYukla(m.topic_code); };

  const formaniTozala = () => { setSarlavha(""); setMatn(""); setVideoHavola(""); setKontentTuriFormasi(null); setXato(""); };

  const matnKontentSaqla = async () => {
    setSaqlanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/togarak_matn_kontent_qosh`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token, togarak_id: togarakId, topic_code: tanlanganMavzu.topic_code, kontent_turi: kontentTuriFormasi,
          sarlavha: sarlavha || undefined, matn: kontentTuriFormasi !== "video" ? matn : undefined,
          video_havola: kontentTuriFormasi === "video" ? videoHavola : undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      formaniTozala();
      kontentlarniYukla(tanlanganMavzu.topic_code);
      mavzularniYukla();
    } catch (e) { setXato(e.message); } finally { setSaqlanmoqda(false); }
  };

  const faylTanlandi = async (e) => {
    const fayl = e.target.files[0];
    if (!fayl) return;
    setSaqlanmoqda(true); setXato("");
    try {
      const formData = new FormData();
      formData.append("fayl", fayl);
      const q = new URLSearchParams({ token, togarak_id: togarakId, topic_code: tanlanganMavzu.topic_code, sarlavha: sarlavha || "" });
      const res = await fetch(`${API_BASE}/api/oqituvchi/togarak_fayl_kontent_qosh?${q.toString()}`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      formaniTozala();
      kontentlarniYukla(tanlanganMavzu.topic_code);
      mavzularniYukla();
    } catch (e) { setXato(e.message); } finally { setSaqlanmoqda(false); e.target.value = ""; }
  };

  const kontentOchir = async (id) => {
    await fetch(`${API_BASE}/api/oqituvchi/togarak_kontent_ochir?token=${encodeURIComponent(token)}&biriktirma_id=${id}`, { method: "DELETE" });
    kontentlarniYukla(tanlanganMavzu.topic_code);
    mavzularniYukla();
  };

  const [testHammasigaSoni, setTestHammasigaSoni] = useState("");

  const testKodBelgila = (topicCode, soni) => {
    setTestTanlanganKodlar((prev) => {
      const yangi = { ...prev };
      if (soni <= 0) delete yangi[topicCode];
      else yangi[topicCode] = soni;
      return yangi;
    });
  };

  const testShablonYukla = async () => {
    const guruhlar = Object.entries(testTanlanganKodlar).map(([topic_code, soni]) => ({ topic_code, soni }));
    if (guruhlar.length === 0) { setXato("Kamida bitta mavzudan son tanlang"); return; }
    setTestYuklanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/togarak_test_shablon`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, togarak_id: togarakId, guruhlar }),
      });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || "Xato"); }
      const blob = await res.blob();
      const dlUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = dlUrl; a.download = "togarak_test_shablon.xlsx";
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(dlUrl);
    } catch (e) { setXato(e.message); } finally { setTestYuklanmoqda(false); }
  };

  const testFaylTanlandi = async (e) => {
    const fayl = e.target.files[0];
    if (!fayl) return;
    setTestImportlanmoqda(true); setXato(""); setTestNatija(null);
    try {
      const formData = new FormData();
      formData.append("fayl", fayl);
      const res = await fetch(`${API_BASE}/api/oqituvchi/togarak_test_import?token=${encodeURIComponent(token)}&togarak_id=${togarakId}`, {
        method: "POST", body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setTestNatija(data);
      mavzularniYukla();
    } catch (e) { setXato(e.message); } finally { setTestImportlanmoqda(false); e.target.value = ""; }
  };

  const yangiMavzuYarat = async () => {
    if (!yangiMavzuNomi.trim()) { setXato("Mavzu nomini kiriting"); return; }
    setYangiMavzuYaratilmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/togarak_yangi_mavzu_yarat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, togarak_id: togarakId, nomi: yangiMavzuNomi.trim(), bob: yangiMavzuBob.trim() || undefined }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setYangiMavzuNomi(""); setYangiMavzuBob(""); setYangiMavzuOchiq(false);
      mavzularniYukla();
    } catch (e) { setXato(e.message); } finally { setYangiMavzuYaratilmoqda(false); }
  };

  const kopMavzuYarat = async () => {
    const nomlar = kopMavzuMatni.split("\n").map((s) => s.trim()).filter(Boolean);
    if (nomlar.length === 0) { setXato("Kamida bitta mavzu nomi yozing"); return; }
    setKopMavzuYaratilmoqda(true); setXato("");
    try {
      for (let i = 0; i < nomlar.length; i++) {
        setKopMavzuProgress(`${i + 1} / ${nomlar.length}: ${nomlar[i]}`);
        // eslint-disable-next-line no-await-in-loop
        const res = await fetch(`${API_BASE}/api/oqituvchi/togarak_yangi_mavzu_yarat`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token, togarak_id: togarakId, nomi: nomlar[i] }),
        });
        // eslint-disable-next-line no-await-in-loop
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(`"${nomlar[i]}" qo'shilmadi: ${data.detail || "xato"}`);
      }
      setKopMavzuMatni(""); setKopMavzuRejimi(false); setYangiMavzuOchiq(false);
      mavzularniYukla();
    } catch (e) { setXato(e.message); } finally { setKopMavzuYaratilmoqda(false); setKopMavzuProgress(""); }
  };

  const KONTENT_YORLIQ = { matn: "📝 Matn", latex: "🧮 LaTeX", rasm: "🖼 Rasm", pdf: "📄 PDF", word: "📃 Word", video: "🎬 Video" };

  if (tanlanganMavzu && kitobOchiq) {
    return (
      <MavzuKitobiTahrirlash token={token} togarakId={togarakId} mavzu={tanlanganMavzu}
        onOrtga={() => setKitobOchiq(false)} />
    );
  }

  if (tanlanganMavzu) {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => { setTanlanganMavzu(null); setKontentlar(null); formaniTozala(); }} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Mavzular")}/></button>
        <h1 className="text-xl font-bold mb-3" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(formatTopicTitle(0, tanlanganMavzu))}</h1>

        <button onClick={() => setKitobOchiq(true)} className="w-full rounded-2xl bg-white border flex items-center gap-3 px-4 py-3.5 mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <span className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: "#EAF3DE" }}>
            <BookOpen size={18} style={{ color: "#3B6D11" }} />
          </span>
          <div className="flex-1 text-left">
            <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Kitob tuzish")}</p>
            <p className="text-[11px]" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Video + misollar")}</p>
          </div>
          <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
        </button>

        <div className="flex gap-2 flex-wrap mb-4">
          {[["matn", "📝 Matn"], ["latex", "🧮 LaTeX"], ["video", "🎬 Video"]].map(([turi, yorliq]) => (
            <button key={turi} onClick={() => { formaniTozala(); setKontentTuriFormasi(turi); }}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg"
              style={kontentTuriFormasi === turi ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>
              + {__kbUi(yorliq)}
            </button>
          ))}
          <label className="text-xs font-semibold px-3 py-1.5 rounded-lg cursor-pointer" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>+ 🖼📄📃 <InterfaceText text={__kbUi("Fayl")}/><input type="file" accept=".png,.jpg,.jpeg,.gif,.webp,.pdf,.docx" onChange={faylTanlandi} className="hidden" />
          </label>
        </div>

        {(kontentTuriFormasi === "matn" || kontentTuriFormasi === "latex" || kontentTuriFormasi === "video") && (
          <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <input type="text" value={sarlavha} onChange={(e) => setSarlavha(e.target.value)} placeholder={__kbUi("Sarlavha (ixtiyoriy)")}
              className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            {kontentTuriFormasi === "video" ? (
              <input type="text" value={videoHavola} onChange={(e) => setVideoHavola(e.target.value)} placeholder={__kbUi("Video havolasi (YouTube yoki boshqa)")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            ) : (
              <>
                <textarea value={matn} onChange={(e) => setMatn(e.target.value)}
                  placeholder={kontentTuriFormasi === "latex" ? __kbUi("LaTeX formula, masalan: \\frac{1}{2}") : __kbUi("Matn")} rows={5}
                  className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5 font-mono" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                {kontentTuriFormasi === "latex" && matn.trim() && <SavolFormulasi ifoda={matn} />}
              </>
            )}
            {xato && <p className="text-sm mb-2.5" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
            <button onClick={matnKontentSaqla} disabled={saqlanmoqda}
              className="w-full py-2.5 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: saqlanmoqda ? 0.7 : 1 }}>
              {saqlanmoqda ? uiT("Saqlanmoqda...") : uiT("Qo'shish")}
            </button>
          </div>
        )}
        {saqlanmoqda && !kontentTuriFormasi && <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Fayl yuklanmoqda...")}</p>}
        {xato && !kontentTuriFormasi && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}

        <p className="text-sm font-semibold mb-2.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Qo'shilgan kontentlar (")}{(kontentlar || []).length})</p>
        {kontentlar === null ? (
          <div className="py-6 text-center"><Loader2 size={20} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
        ) : (
          <div className="space-y-2">
            {kontentlar.map((k) => (
              <div key={k.id} className="rounded-xl p-3 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                <div className="min-w-0">
                  <p className="text-xs font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(KONTENT_YORLIQ[k.kontent_turi])} {k.sarlavha ? __kbUi(`— ${k.sarlavha}`) : __kbUi("")}</p>
                  <p className="text-xs truncate" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
                    {k.kontent_turi === "video" ? __kbUi(`👁 ${k.korilish_soni} ko'rilgan`) : __kbUi((k.matn || k.fayl_nomi || "").slice(0, 60))}
                  </p>
                </div>
                <button onClick={() => kontentOchir(k.id)} className="text-xs px-2 shrink-0" style={{ color: "#A32D2D" }}>✕</button>
              </div>
            ))}
            {kontentlar.length === 0 && <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali kontent qo'shilmagan.")}</p>}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Guruh")}/></button>
      <div className="flex items-center justify-between mb-1 gap-2">
        <h1 className="text-xl font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📖 To'garak mavzulari")}</h1>
        <div className="flex gap-2 shrink-0 flex-wrap justify-end">
          <button onClick={() => { setYangiMavzuOchiq(!yangiMavzuOchiq); setQidiruvOchiq(false); setTestShablonOchiq(false); }}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
            {yangiMavzuOchiq ? __kbUi("✕ Yopish") : __kbUi("✏️ Yangi mavzu")}
          </button>
          <button onClick={() => { setTestShablonOchiq(!testShablonOchiq); setQidiruvOchiq(false); setYangiMavzuOchiq(false); }}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
            {testShablonOchiq ? __kbUi("✕ Yopish") : __kbUi("🧪 Test shablon")}
          </button>
          <button onClick={() => { setQidiruvOchiq(!qidiruvOchiq); setQidiruv(""); setQidiruvNatijalari(null); setTestShablonOchiq(false); setYangiMavzuOchiq(false); }}
            className="text-xs font-semibold px-3.5 py-1.5 rounded-full" style={{ backgroundColor: "#1B4B7A", color: "#fff" }}>
            {qidiruvOchiq ? __kbUi("✕ Yopish") : __kbUi("+ Mavzu qo'shish")}
          </button>
        </div>
      </div>
      <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Milliy bazadan mavzu tanlab, har biriga matn/LaTeX/rasm/PDF/Word/video biriktiring.")}</p>

      {yangiMavzuOchiq && (
        <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-xs font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Yangi mavzu qo'shish")}</p>
          <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Milliy bazada mos mavzu topilmasa (masalan yangi maxsus guruh uchun) — shu yerda nomini yozib, o'zingiz qo'shing. Kod avtomatik yaratiladi.")}</p>
          <div className="flex gap-1.5 mb-3">
            <button type="button" onClick={() => setKopMavzuRejimi(false)}
              className="flex-1 py-2 rounded-lg text-xs font-semibold"
              style={!kopMavzuRejimi ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>{__kbUi("Bittalab")}</button>
            <button type="button" onClick={() => setKopMavzuRejimi(true)}
              className="flex-1 py-2 rounded-lg text-xs font-semibold"
              style={kopMavzuRejimi ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>{__kbUi("Bir nechtasini birdan")}</button>
          </div>

          {kopMavzuRejimi ? (
            <>
              <p className="text-xs mb-2" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Har bir mavzuni YANGI qatorga yozing.")}</p>
              <textarea value={kopMavzuMatni} onChange={(e) => setKopMavzuMatni(e.target.value)}
                placeholder={__kbUi("1-mavzu nomi\n2-mavzu nomi\n3-mavzu nomi\n...")} rows={8}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              <button onClick={kopMavzuYarat} disabled={kopMavzuYaratilmoqda || !kopMavzuMatni.trim()}
                className="w-full py-3 rounded-xl font-semibold text-white text-sm flex items-center justify-center gap-2"
                style={{ backgroundColor: "#1B4B7A", opacity: (kopMavzuYaratilmoqda || !kopMavzuMatni.trim()) ? 0.6 : 1 }}>
                {kopMavzuYaratilmoqda
                  ? <><Loader2 size={16} className="animate-spin" /> {kopMavzuProgress}</>
                  : __kbUi(`+ Barchasini qo'shish (${kopMavzuMatni.split("\n").map((s) => s.trim()).filter(Boolean).length} ta)`)}
              </button>
            </>
          ) : (
            <>
              <input type="text" value={yangiMavzuBob} onChange={(e) => setYangiMavzuBob(e.target.value)}
                placeholder={__kbUi("Bob nomi (ixtiyoriy)")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              <input type="text" value={yangiMavzuNomi} onChange={(e) => setYangiMavzuNomi(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && yangiMavzuYarat()}
                placeholder={__kbUi("Mavzu nomi")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              <button onClick={yangiMavzuYarat} disabled={yangiMavzuYaratilmoqda || !yangiMavzuNomi.trim()}
                className="w-full py-3 rounded-xl font-semibold text-white text-sm flex items-center justify-center gap-2"
                style={{ backgroundColor: "#1B4B7A", opacity: (yangiMavzuYaratilmoqda || !yangiMavzuNomi.trim()) ? 0.6 : 1 }}>
                {yangiMavzuYaratilmoqda ? <Loader2 size={16} className="animate-spin" /> : __kbUi("+ Mavzu qo'shish")}
              </button>
            </>
          )}
          {xato && <p className="text-sm mt-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
        </div>
      )}

      {testShablonOchiq && (
        <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-xs font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Ko'p savolni bir martada Excel orqali qo'shish")}</p>
          <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Mavzu(lar)ni tanlab, har biriga necha savol kerakligini yozing.")}</p>
          {mavzular.length > 0 && (
            <div className="flex items-center gap-2 mb-3">
              <input type="number" min="0" value={testHammasigaSoni} onChange={(e) => setTestHammasigaSoni(e.target.value)}
                placeholder={__kbUi("0")} className="w-16 px-2 py-1.5 rounded-lg border text-xs text-center" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              <button onClick={() => {
                  const soni = parseInt(testHammasigaSoni, 10) || 0;
                  setTestTanlanganKodlar(Object.fromEntries(mavzular.map((m) => [m.topic_code, soni]).filter(([, s]) => s > 0)));
                }}
                className="text-xs font-semibold px-3 py-1.5 rounded-lg" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Hammasiga qo'llash (")}{mavzular.length}{__kbUi(" ta)")}</button>
            </div>
          )}
          <div className="space-y-2 mb-3 max-h-56 overflow-y-auto">
            {mavzular.map((m, index) => (
              <div key={m.topic_code} className="flex items-center gap-2 rounded-lg p-2" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                <span className="flex-1 text-xs truncate" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(formatTopicTitle(index, m))}</span>
                <input type="number" min="0" value={testTanlanganKodlar[m.topic_code] || ""}
                  onChange={(e) => testKodBelgila(m.topic_code, parseInt(e.target.value, 10) || 0)}
                  placeholder={__kbUi("0")} className="w-16 px-2 py-1 rounded-lg border text-xs text-center" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              </div>
            ))}
            {mavzular.length === 0 && <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Avval \"+ Mavzu qo'shish\" yoki \"✏️ Yangi mavzu\" orqali mavzu qo'shing.")}</p>}
          </div>
          <button onClick={testShablonYukla} disabled={testYuklanmoqda}
            className="w-full py-3 rounded-xl font-semibold text-sm mb-2.5 flex items-center justify-center gap-2"
            style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
            {testYuklanmoqda ? <Loader2 size={16} className="animate-spin" /> : __kbUi("📥 Shablon yuklab olish")}
          </button>
          <label className="w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 cursor-pointer border-2 border-dashed"
            style={{ borderColor: "#C4BFAF", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
            {testImportlanmoqda ? <Loader2 size={16} className="animate-spin" /> : __kbUi("📤 To'ldirilgan faylni yuklash")}
            <input type="file" accept=".xlsx" onChange={testFaylTanlandi} disabled={testImportlanmoqda} className="hidden" />
          </label>
          {testNatija && (
            <p className="text-xs mt-3" style={{ color: "#3B6D11" }}>
              ✅ {testNatija.saved}{__kbUi(" ta savol qo'shildi")}{testNatija.errors > 0 ? __kbUi(`, ${testNatija.errors} ta xato`) : __kbUi("")}
            </p>
          )}
          {xato && <p className="text-sm mt-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
        </div>
      )}

      {qidiruvOchiq && (
        <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <input type="text" value={qidiruv} onChange={(e) => setQidiruv(e.target.value)} placeholder={__kbUi("Mavzu nomi bo'yicha qidirish (bo'sh — o'z sinf/faningiz)")}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          {!qidirilmoqda && !qidiruvXato && (qidiruvNatijalari || []).some((m) => !mavzular.some((x) => x.topic_code === m.topic_code)) && (
            <button onClick={barchasiniQoshish} disabled={barchasiniQoshishYuklanmoqda}
              className="w-full py-2.5 rounded-xl font-semibold text-sm mb-3 flex items-center justify-center gap-2"
              style={{ backgroundColor: "#EAF3DE", color: "#3B6D11", opacity: barchasiniQoshishYuklanmoqda ? 0.7 : 1 }}>
              {barchasiniQoshishYuklanmoqda ? <Loader2 size={16} className="animate-spin" /> :
                __kbUi(`✓✓ Barchasini qo'shish (${(qidiruvNatijalari || []).filter((m) => !mavzular.some((x) => x.topic_code === m.topic_code)).length} ta)`)}
            </button>
          )}
          {qidirilmoqda ? (
            <div className="py-4 text-center"><Loader2 size={18} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
          ) : qidiruvXato ? (
            <p className="text-xs font-medium" style={{ color: "#A32D2D" }}>⚠️ {__kbUi(qidiruvXato)}</p>
          ) : (
            <div className="space-y-1.5 max-h-64 overflow-y-auto">
              {(qidiruvNatijalari || []).map((m) => {
                const biriktirilganmi = mavzular.some((x) => x.topic_code === m.topic_code);
                return (
                  <div key={m.topic_code} className="flex items-center justify-between gap-2 rounded-lg p-2" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                    <div className="min-w-0">
                      <p className="text-xs font-medium truncate" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(topicName(m))}</p>
                      <p className="text-xs truncate" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{m.subject_name} · {m.grade}{__kbUi("-sinf ")}{m.bob_name ? __kbUi(`· ${m.bob_name}`) : __kbUi("")}</p>
                    </div>
                    <button onClick={() => mavzuBiriktir(m.topic_code)} disabled={biriktirilganmi}
                      className="text-xs font-semibold px-2.5 py-1.5 rounded-lg shrink-0"
                      style={biriktirilganmi ? { backgroundColor: "#EAF3DE", color: "#3B6D11" } : { backgroundColor: "#1B4B7A", color: "#fff" }}>
                      {biriktirilganmi ? __kbUi("✓ Qo'shilgan") : __kbUi("+ Qo'shish")}
                    </button>
                  </div>
                );
              })}
              {(qidiruvNatijalari || []).length === 0 && <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hech narsa topilmadi. Boshqa nom bilan qidirib ko'ring.")}</p>}
            </div>
          )}
        </div>
      )}

      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : xato ? (
        <p className="text-sm mb-3 font-medium" style={{ color: "#A32D2D" }}>⚠️ {__kbUi(xato)}</p>
      ) : mavzular.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali mavzu qo'shilmagan.")}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {mavzular.map((m, index) => (
            <div key={m.topic_code} className="rounded-xl p-3.5 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <button onClick={() => mavzuOch({ ...m, tartib_raqami: index + 1 })} className="flex-1 text-left min-w-0">
                <p className="text-sm font-semibold truncate" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(formatTopicTitle(index, m))}</p>
                <p className="text-xs truncate" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{m.kontent_soni}{__kbUi(" kontent")}</p>
              </button>
              <button onClick={() => mavzuniOlibTashla(m.topic_code)} className="text-xs px-2 shrink-0" style={{ color: "#A32D2D" }}>✕</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TogarakGuruhSozlamalari({ token, togarak, onOrtga, onOchirildi }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [parolKorinmoqda, setParolKorinmoqda] = useState(false);
  const [joriyParol, setJoriyParol] = useState(null);
  const [parolYuklanmoqda, setParolYuklanmoqda] = useState(false);
  const [yangiParol, setYangiParol] = useState("");
  const [parolSaqlanmoqda, setParolSaqlanmoqda] = useState(false);
  const [parolSaqlandi, setParolSaqlandi] = useState(false);

  const [ochirishBosqichida, setOchirishBosqichida] = useState(false);
  const [ochirishParoli, setOchirishParoli] = useState("");
  const [ochirilmoqda, setOchirilmoqda] = useState(false);
  const [xato, setXato] = useState("");

  const parolniKorsat = () => {
    if (parolKorinmoqda) { setParolKorinmoqda(false); return; }
    setParolYuklanmoqda(true);
    fetch(`${API_BASE}/api/oqituvchi/togarak_parolini_kor?token=${encodeURIComponent(token)}&togarak_id=${togarak.id}`)
      .then((r) => r.json())
      .then((d) => { setJoriyParol(d.parol); setParolKorinmoqda(true); setParolYuklanmoqda(false); })
      .catch(() => setParolYuklanmoqda(false));
  };

  const parolAlmashtir = async () => {
    if (!yangiParol.trim()) return;
    setParolSaqlanmoqda(true); setParolSaqlandi(false);
    try {
      await fetch(`${API_BASE}/api/oqituvchi/togarak_parol_almashtir`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, togarak_id: togarak.id, yangi_parol: yangiParol.trim() }),
      });
      setJoriyParol(yangiParol.trim()); setYangiParol(""); setParolSaqlandi(true);
    } finally { setParolSaqlanmoqda(false); }
  };

  const guruhniOchir = async () => {
    if (!ochirishParoli.trim()) { setXato("Parolni kiriting"); return; }
    setOchirilmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/togarak_ochir?token=${encodeURIComponent(token)}&togarak_id=${togarak.id}&parol=${encodeURIComponent(ochirishParoli.trim())}`, {
        method: "DELETE",
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      onOchirildi();
    } catch (e) {
      setXato(e.message);
      setOchirilmoqda(false);
    }
  };

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Ortga")}/></button>
      <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("⚙️ Guruh sozlamalari")}</h1>
      <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{togarak.nomi}</p>

      <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <p className="text-sm font-semibold mb-3" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🔑 Qo'shilish paroli")}</p>
        <button onClick={parolniKorsat} disabled={parolYuklanmoqda}
          className="w-full py-2.5 rounded-xl font-semibold text-sm mb-3" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
          {parolYuklanmoqda ? uiT("Yuklanmoqda...") : parolKorinmoqda ? __kbUi(`Parol: ${joriyParol || "(belgilanmagan)"} — yashirish`) : uiT("Parolni ko'rsatish")}
        </button>
        <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Yangi parol belgilash")}</label>
        <div className="flex gap-2">
          <input type="text" value={yangiParol} onChange={(e) => setYangiParol(e.target.value)} placeholder={uiT("Yangi parol")}
            className="flex-1 px-3.5 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          <button onClick={parolAlmashtir} disabled={parolSaqlanmoqda || !yangiParol.trim()}
            className="px-4 py-2.5 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: parolSaqlanmoqda || !yangiParol.trim() ? 0.5 : 1 }}>
            {parolSaqlanmoqda ? __kbUi("...") : uiT("Saqlash")}
          </button>
        </div>
        {parolSaqlandi && <p className="text-xs mt-2" style={{ color: "#3B6D11" }}>{__kbUi("✅ Parol yangilandi")}</p>}
      </div>

      <div className="rounded-2xl p-4 border" style={{ backgroundColor: "#FCEBEB", borderColor: "#E8A0A0" }}>
        <p className="text-sm font-semibold mb-1" style={{ color: "#A32D2D" }}>{__kbUi("⚠️ Xavfli hudud")}</p>
        <p className="text-xs mb-3" style={{ color: "#8A5A5A" }}>{__kbUi("Guruhni o'chirsangiz — barcha a'zolar, o'z mavzu/testlaringiz va to'lov tarixi butunlay o'chadi. Bu amalni ORQAGA QAYTARIB BO'LMAYDI.")}</p>
        {!ochirishBosqichida ? (
          <button onClick={() => setOchirishBosqichida(true)}
            className="w-full py-2.5 rounded-xl font-semibold text-sm text-white" style={{ backgroundColor: "#A32D2D" }}>{__kbUi("🗑 Guruhni o'chirish")}</button>
        ) : (
          <div>
            <p className="text-xs font-medium mb-2" style={{ color: "#A32D2D" }}>{__kbUi("Tasdiqlash uchun guruh parolini kiriting:")}</p>
            <input type="text" value={ochirishParoli} onChange={(e) => setOchirishParoli(e.target.value)} placeholder={__kbUi("Guruh paroli")}
              className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5" style={{ borderColor: "#E8A0A0" }} />
            {xato && <p className="text-xs mb-2" style={{ color: "#A32D2D" }}>{__kbUi(xato)}</p>}
            <div className="flex gap-2">
              <button onClick={() => { setOchirishBosqichida(false); setOchirishParoli(""); setXato(""); }}
                className="flex-1 py-2.5 rounded-xl font-medium text-sm" style={{ backgroundColor: "var(--ui-legacy-background-fff, #fff)", color: "var(--ui-legacy-color-5a5648, #5A5648)", border: "1px solid #E5E1D8" }}><InterfaceText text={__kbUi("Bekor qilish")}/></button>
              <button onClick={guruhniOchir} disabled={ochirilmoqda}
                className="flex-1 py-2.5 rounded-xl font-semibold text-sm text-white" style={{ backgroundColor: "#A32D2D", opacity: ochirilmoqda ? 0.7 : 1 }}>
                {ochirilmoqda ? __kbUi("O'chirilmoqda...") : __kbUi("Ha, butunlay o'chirish")}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


function DavomatBelgilash({ token, sinfId, onOrtga }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const bugun = new Date().toISOString().slice(0, 10);
  const [sana, setSana] = useState(bugun);
  const [oquvchilar, setOquvchilar] = useState(null);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [saqlanmoqda, setSaqlanmoqda] = useState(false);
  const [xato, setXato] = useState("");
  const [saqlandi, setSaqlandi] = useState(false);

  const HOLATLAR = [
    { kalit: "keldi", belgi: "✅", nomi: "Keldi", rang: "#3B6D11", fon: "#EAF3DE" },
    { kalit: "kelmadi", belgi: "❌", nomi: "Kelmadi", rang: "#A32D2D", fon: "#FCEBEB" },
    { kalit: "kechikdi", belgi: "⏰", nomi: "Kechikdi", rang: "#8A5A1C", fon: "#FDF3E0" },
    { kalit: "sababli", belgi: "📋", nomi: "Sababli", rang: "#5A5648", fon: "#F7F5F0" },
  ];

  const yukla = () => {
    setYuklanmoqda(true); setSaqlandi(false);
    fetch(`${API_BASE}/api/oqituvchi/davomat_royxati?token=${encodeURIComponent(token)}&sinf_id=${sinfId}&sana=${sana}`)
      .then((r) => r.json())
      .then((d) => {
        setOquvchilar((d.oquvchilar || []).map((o) => ({ ...o, holat: o.holat || "keldi" })));
        setYuklanmoqda(false);
      })
      .catch(() => setYuklanmoqda(false));
  };
  useEffect(yukla, [sana, sinfId, token]);

  const holatOzgartir = (userId, holat) => {
    setOquvchilar((prev) => prev.map((o) => (o.user_id === userId ? { ...o, holat } : o)));
  };

  const barchasiniBelgila = (holat) => {
    setOquvchilar((prev) => prev.map((o) => ({ ...o, holat })));
  };

  const saqla = async () => {
    setSaqlanmoqda(true); setXato(""); setSaqlandi(false);
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/davomat_belgila`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token, sinf_id: sinfId, sana,
          yozuvlar: oquvchilar.map((o) => ({ user_id: o.user_id, holat: o.holat })),
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setSaqlandi(true);
    } catch (e) {
      setXato(e.message);
    } finally { setSaqlanmoqda(false); }
  };

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Ortga")}/></button>
      <h1 className="text-xl font-bold mb-4" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>📋 <InterfaceText text={__kbUi("Davomat")}/></h1>

      <input type="date" value={sana} onChange={(e) => setSana(e.target.value)} max={bugun}
        className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />

      <div className="flex gap-1.5 mb-4">
        {HOLATLAR.map((h) => (
          <button key={h.kalit} onClick={() => barchasiniBelgila(h.kalit)}
            className="flex-1 py-2 rounded-lg text-xs font-medium" style={{ backgroundColor: h.fon, color: h.rang }}><InterfaceText text={__kbUi("Hammasi ")}/>{__kbUi(h.belgi)}
          </button>
        ))}
      </div>

      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : (
        <div className="space-y-2 mb-5">
          {(oquvchilar || []).map((o) => (
            <div key={o.user_id} className="rounded-xl p-3 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <p className="text-sm font-medium mb-2" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{o.full_name}</p>
              <div className="flex gap-1.5">
                {HOLATLAR.map((h) => (
                  <button key={h.kalit} onClick={() => holatOzgartir(o.user_id, h.kalit)}
                    className="flex-1 py-1.5 rounded-lg text-xs font-semibold"
                    style={o.holat === h.kalit ? { backgroundColor: h.rang, color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#8A8578" }}>
                    {__kbUi(h.belgi)}
                  </button>
                ))}
              </div>
            </div>
          ))}
          {(oquvchilar || []).length === 0 && <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Sinfda o'quvchi yo'q.")}</p>}
        </div>
      )}

      {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
      {saqlandi && <p className="text-sm mb-3" style={{ color: "#3B6D11" }}>{__kbUi("✅ Saqlandi")}</p>}
      <button onClick={saqla} disabled={saqlanmoqda || yuklanmoqda}
        className="w-full py-3 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: saqlanmoqda ? 0.7 : 1 }}>
        {saqlanmoqda ? uiT("Saqlanmoqda...") : uiT("Saqlash")}
      </button>
    </div>
  );
}

function KirishKodiFormasi({ token, onOrtga, onComplete }) {
  return <div className="px-5 pt-6 pb-4"><JoinInstitution apiBase={API_BASE} token={token} onBack={onOrtga} onComplete={onComplete}/></div>;
}

function RasmiySinflarim({ token, onOrtga }) {
  useKbInterfaceLocale();
  const [sinflar, setSinflar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [tanlanganSinf, setTanlanganSinf] = useState(null);
  const [oquvchilar, setOquvchilar] = useState(null);
  const [oquvchilarYuklanmoqda, setOquvchilarYuklanmoqda] = useState(false);
  const [azolar, setAzolar] = useState(null);
  const [azolarYuklanmoqda, setAzolarYuklanmoqda] = useState(false);
  const [davomatKorinishi, setDavomatKorinishi] = useState(false);
  const [tanlanganOquvchiId, setTanlanganOquvchiId] = useState(null);
  const [otaOnaOquvchi, setOtaOnaOquvchi] = useState(null);
  const [otaOnaQidiruv, setOtaOnaQidiruv] = useState("");
  const [otaOnaNatijalar, setOtaOnaNatijalar] = useState([]);
  const [otaOnaXabar, setOtaOnaXabar] = useState("");
  const joriyOy = new Date().toISOString().slice(0, 7); // "2026-07"

  useEffect(() => {
    fetch(`${API_BASE}/api/oqituvchi/mening_sinflarim?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => { setSinflar(d.sinflar || []); setYuklanmoqda(false); })
      .catch(() => setYuklanmoqda(false));
  }, [token]);

  const azolarniYukla = (sinfId) => {
    setAzolarYuklanmoqda(true);
    fetch(`${API_BASE}/api/oqituvchi/sinf_azolari?token=${encodeURIComponent(token)}&sinf_id=${sinfId}`)
      .then((r) => r.json())
      .then((d) => { setAzolar(d.azolar || []); setAzolarYuklanmoqda(false); })
      .catch(() => setAzolarYuklanmoqda(false));
  };

  const azoniChiqar = async (azolikId, sinfId) => {
    await fetch(`${API_BASE}/api/oqituvchi/sinf_azosini_chiqar?token=${encodeURIComponent(token)}&azolik_id=${azolikId}`, { method: "DELETE" });
    azolarniYukla(sinfId);
  };

  const otaOnaQidir = async () => {
    if (!otaOnaOquvchi || otaOnaQidiruv.trim().length < 2) return;
    const res = await fetch(`${API_BASE}/api/maktab/ota_ona_qidir?token=${encodeURIComponent(token)}&sinf_id=${tanlanganSinf.id}&ism=${encodeURIComponent(otaOnaQidiruv.trim())}`);
    const data = await res.json().catch(() => ({}));
    setOtaOnaNatijalar(res.ok ? (data.natijalar || []) : []);
    setOtaOnaXabar(res.ok ? "" : (data.detail || "Ota-onani qidirib bo‘lmadi"));
  };

  const otaOnaBogla = async (otaOna) => {
    const res = await fetch(`${API_BASE}/api/maktab/oquvchiga_ota_ona_bogla`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, sinf_id: tanlanganSinf.id, oquvchi_user_id: otaOnaOquvchi.user_id, ota_ona_user_id: otaOna.user_id }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) { setOtaOnaXabar(data.detail || "Ota-onani bog‘lab bo‘lmadi"); return; }
    setOtaOnaXabar(`✅ ${otaOna.full_name} — ${otaOnaOquvchi.full_name}ga bog‘landi.`);
    setOtaOnaNatijalar([]); setOtaOnaQidiruv("");
  };

  const sinfOch = (s) => {
    setTanlanganSinf(s);
    azolarniYukla(s.id);
    if (!s.pulli) return;
    setOquvchilarYuklanmoqda(true);
    fetch(`${API_BASE}/api/oqituvchi/sinf_tolovlari?token=${encodeURIComponent(token)}&sinf_id=${s.id}&oy=${joriyOy}`)
      .then((r) => r.json())
      .then((d) => { setOquvchilar(d.oquvchilar || []); setOquvchilarYuklanmoqda(false); })
      .catch(() => setOquvchilarYuklanmoqda(false));
  };

  const tolovBelgila = async (oquvchi) => {
    await fetch(`${API_BASE}/api/oqituvchi/tolov_belgila`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token, user_id: oquvchi.user_id, maktab_id: tanlanganSinf.maktab_id || tanlanganSinf.id,
        oy: joriyOy, tolangan_summa: tanlanganSinf.oylik_tolov,
      }),
    });
    sinfOch(tanlanganSinf);
  };

  if (tanlanganOquvchiId) {
    return <OquvchiProfili token={token} userId={tanlanganOquvchiId} onOrtga={() => setTanlanganOquvchiId(null)} />;
  }

  if (tanlanganSinf && davomatKorinishi) {
    return <DavomatBelgilash token={token} sinfId={tanlanganSinf.id} onOrtga={() => setDavomatKorinishi(false)} />;
  }

  if (tanlanganSinf) {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => setTanlanganSinf(null)} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("Sinflarim")}</button>
        <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{tanlanganSinf.sinf}-{tanlanganSinf.harf}</h1>
        <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{tanlanganSinf.maktab_nomi} · {tanlanganSinf.oquvchi_soni}{__kbUi(" o'quvchi")}</p>
        <button onClick={() => setDavomatKorinishi(true)}
          className="w-full py-2.5 rounded-xl font-semibold text-sm mb-3" style={{ backgroundColor: "#1B4B7A", color: "#fff" }}>{__kbUi("📋 Davomat belgilash")}</button>

        <div className="rounded-xl p-3.5 mb-4" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
          <p className="text-xs" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("🔐 Qo'shilish paroli: ")}<b>{__kbUi(tanlanganSinf.qoshilish_paroli)}</b></p>
        </div>

        {tanlanganSinf.sinf_boshqara_oladi && (
          <div className="rounded-xl p-3.5 mb-4" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
            <SinfGuruhBoshqaruvi token={token} sinf={tanlanganSinf} onSaved={() => azolarniYukla(tanlanganSinf.id)} />
          </div>
        )}

        {!tanlanganSinf.pulli ? (
          <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bu maktab bepul — to'lov kuzatuvi kerak emas.")}</p>
          </div>
        ) : oquvchilarYuklanmoqda ? (
          <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
        ) : (
          <>
            <p className="text-sm font-semibold mb-2.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>💳 {joriyOy}{__kbUi(" oyi to'lovlari")}</p>
            <div className="space-y-2">
              {(oquvchilar || []).map((o) => (
                <div key={o.user_id} className="rounded-xl p-3.5 flex items-center justify-between" style={{ backgroundColor: o.qarzdor ? "#FCEBEB" : "#EAF3DE" }}>
                  <div>
                    <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{o.full_name}</p>
                    <p className="text-xs" style={{ color: o.qarzdor ? "#A32D2D" : "#3B6D11" }}>
                      {o.qarzdor ? __kbUi(`⚠️ Qarzdor (${o.tolangan_summa.toLocaleString()} / ${o.kerakli_summa.toLocaleString()} so'm)`) : __kbUi("✅ To'langan")}
                    </p>
                  </div>
                  {o.qarzdor && (
                    <button onClick={() => tolovBelgila(o)} className="text-xs font-semibold px-3 py-1.5 rounded-lg text-white" style={{ backgroundColor: "#1B4B7A" }}>{__kbUi("To'landi deb belgilash")}</button>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        <p className="text-sm font-semibold mb-2.5 mt-5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("👥 Sinf a'zolari")}</p>
        {azolarYuklanmoqda ? (
          <div className="py-6 text-center"><Loader2 size={20} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
        ) : !azolar || azolar.length === 0 ? (
          <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali hech kim qo'shilmagan — o'quvchilar parolni kiritganda shu yerda ko'rinadi.")}</p>
        ) : (
          <div className="space-y-2">
            {azolar.map((a) => (
              <div key={a.azolik_id} className="rounded-xl p-3.5 flex items-center justify-between" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                <div><button onClick={() => setTanlanganOquvchiId(a.user_id)} className="text-sm font-medium text-left" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{a.full_name}</button><p className="text-[11px] mt-0.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{[a.jins === "ogil" ? "O‘g‘il" : a.jins === "qiz" ? "Qiz" : null, a.guruh_raqami ? `${a.guruh_raqami}-guruh` : null, a.guruh_nomi].filter(Boolean).join(" · ") || __kbUi("Guruh belgilanmagan")}</p></div>
                <div className="flex gap-1.5"><button onClick={() => { setOtaOnaOquvchi(a); setOtaOnaQidiruv(""); setOtaOnaNatijalar([]); setOtaOnaXabar(""); }} className="text-xs font-medium px-2.5 py-1.5 rounded-lg" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Ota-ona bog‘lash")}</button><button onClick={() => azoniChiqar(a.azolik_id, tanlanganSinf.id)} className="text-xs font-medium px-2.5 py-1.5 rounded-lg shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-fff, #fff)", color: "#A32D2D", border: "1px solid #E5E1D8" }}>{__kbUi("✕ Chiqarish")}</button></div>
              </div>
            ))}
          </div>
        )}
        {otaOnaOquvchi && <div className="rounded-2xl p-4 mt-4 border" style={{ backgroundColor: "var(--ui-legacy-background-fff, #fff)", borderColor: "#B9CCDC" }}><div className="flex items-center justify-between gap-2 mb-2"><p className="text-sm font-bold">{otaOnaOquvchi.full_name}{__kbUi(" uchun ota-ona")}</p><button onClick={() => setOtaOnaOquvchi(null)} className="text-xs">✕</button></div><div className="flex gap-2"><input value={otaOnaQidiruv} onChange={(e) => setOtaOnaQidiruv(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") otaOnaQidir(); }} placeholder={__kbUi("Ota-ona F.I.Sh...")} className="flex-1 px-3 py-2 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} /><button onClick={otaOnaQidir} className="px-3 py-2 rounded-xl text-xs font-bold text-white" style={{ backgroundColor: "#1B4B7A" }}><InterfaceText text={__kbUi("Qidirish")}/></button></div>{otaOnaNatijalar.map((otaOna) => <button key={otaOna.user_id} onClick={() => otaOnaBogla(otaOna)} className="w-full text-left mt-2 px-3 py-2 rounded-xl text-sm" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>{otaOna.full_name}<span className="float-right text-xs" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Bog‘lash")}</span></button>)}{otaOnaXabar && <p className="text-xs mt-2" style={{ color: otaOnaXabar.startsWith("✅") ? "#3B6D11" : "#B0553A" }}>{otaOnaXabar}</p>}</div>}
      </div>
    );
  }

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("To'garaklarim")}</button>
      <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🏫 Maktab sinflari")}</h1>
      <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Barcha xodim sinflarni ko‘radi; faqat vakolati bor xodim sinf ichini boshqaradi.")}</p>
      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : sinflar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Maktab sinflari topilmadi")}</p>
          <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hisobingiz avval maktab xodimi sifatida bog‘lanishi kerak.")}</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {sinflar.map((s) => (
            <button key={s.id} onClick={() => { if (s.batafsil_ochadi) sinfOch(s); }} disabled={!s.batafsil_ochadi}
              className="w-full text-left rounded-xl p-4 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", opacity: s.batafsil_ochadi ? 1 : 0.82 }}>
              <div>
                <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{s.sinf}-{s.harf}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{s.maktab_nomi} · {s.oquvchi_soni}{__kbUi(" o'quvchi")}{s.pulli ? __kbUi(" · 💳 pulli") : __kbUi("")}</p>
                <p className="text-[11px] mt-0.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{s.smena || 1}{__kbUi("-smena")}{s.xona ? __kbUi(` · ${s.xona}-xona`) : __kbUi("")} · {s.rahbar_ismi || __kbUi("rahbarsiz")}{s.dars_beradi ? __kbUi(" · siz dars berasiz") : __kbUi("")}</p>
              </div>
              {s.batafsil_ochadi ? <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} /> : <span className="text-[10px] px-2 py-1 rounded-full" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Ko‘rish")}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function MaktabBoshqaruvi({ token, maktabId, onOrtga }) {
  useKbInterfaceLocale();
  const [malumot, setMalumot] = useState(null);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");
  const [tanlanganSinf, setTanlanganSinf] = useState(null);
  const [azolar, setAzolar] = useState(null);
  const [oquvchilar, setOquvchilar] = useState(null);
  const [ichkiYuklanmoqda, setIchkiYuklanmoqda] = useState(false);
  const [davomatKorinishi, setDavomatKorinishi] = useState(false);
  const [tepaKorinish, setTepaKorinish] = useState("sinflar"); // "sinflar" | "oqituvchilar" | "reyting"
  const [tanlanganOquvchiId, setTanlanganOquvchiId] = useState(null);
  const [xodimDavomatKorinishi, setXodimDavomatKorinishi] = useState(false);
  const joriyOy = new Date().toISOString().slice(0, 7);

  useEffect(() => {
    if (!maktabId) { setYuklanmoqda(false); return; }
    fetch(`${API_BASE}/api/maktab/dashboard?token=${encodeURIComponent(token)}&maktab_id=${maktabId}`)
      .then((r) => r.json())
      .then((d) => { if (!d.detail) setMalumot(d); else setXato(d.detail); setYuklanmoqda(false); })
      .catch(() => { setXato("Yuklab bo'lmadi"); setYuklanmoqda(false); });
  }, [token, maktabId]);

  const sinfOch = (s) => {
    setTanlanganSinf(s);
    setIchkiYuklanmoqda(true);
    fetch(`${API_BASE}/api/oqituvchi/sinf_azolari?token=${encodeURIComponent(token)}&sinf_id=${s.id}`)
      .then((r) => r.json())
      .then((d) => setAzolar(d.azolar || []))
      .catch(() => {});
    if (malumot.pulli) {
      fetch(`${API_BASE}/api/oqituvchi/sinf_tolovlari?token=${encodeURIComponent(token)}&sinf_id=${s.id}&oy=${joriyOy}`)
        .then((r) => r.json())
        .then((d) => { setOquvchilar(d.oquvchilar || []); setIchkiYuklanmoqda(false); })
        .catch(() => setIchkiYuklanmoqda(false));
    } else {
      setIchkiYuklanmoqda(false);
    }
  };

  const tolovBelgila = async (o) => {
    await fetch(`${API_BASE}/api/oqituvchi/tolov_belgila`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, user_id: o.user_id, maktab_id: maktabId, oy: joriyOy, tolangan_summa: malumot.oylik_tolov }),
    });
    sinfOch(tanlanganSinf);
  };

  if (!maktabId) {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("To'garaklarim")}</button>
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Siz hech qanday maktabga bog'lanmagansiz.")}</p>
        </div>
      </div>
    );
  }

  if (tanlanganOquvchiId) {
    return <OquvchiProfili token={token} userId={tanlanganOquvchiId} onOrtga={() => setTanlanganOquvchiId(null)} />;
  }

  if (xodimDavomatKorinishi) {
    return <XodimDavomatBelgilash token={token} maktabId={maktabId} onOrtga={() => setXodimDavomatKorinishi(false)} />;
  }

  if (tanlanganSinf && davomatKorinishi) {
    return <DavomatBelgilash token={token} sinfId={tanlanganSinf.id} onOrtga={() => setDavomatKorinishi(false)} />;
  }

  if (tanlanganSinf) {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => { setTanlanganSinf(null); setAzolar(null); setOquvchilar(null); }} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Sinflar")}/></button>
        <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{tanlanganSinf.sinf}-{tanlanganSinf.harf}</h1>
        <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{tanlanganSinf.rahbar_ismi || __kbUi("Rahbar belgilanmagan")} · {tanlanganSinf.oquvchi_soni}{__kbUi(" o'quvchi")}</p>
        <button onClick={() => setDavomatKorinishi(true)}
          className="w-full py-2.5 rounded-xl font-semibold text-sm mb-5" style={{ backgroundColor: "#1B4B7A", color: "#fff" }}>{__kbUi("📋 Davomat belgilash")}</button>

        {ichkiYuklanmoqda ? (
          <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
        ) : (
          <>
            {malumot.pulli && (
              <>
                <p className="text-sm font-semibold mb-2.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>💳 {joriyOy}{__kbUi(" oyi to'lovlari")}</p>
                <div className="space-y-2 mb-5">
                  {(oquvchilar || []).map((o) => (
                    <div key={o.user_id} className="rounded-xl p-3.5 flex items-center justify-between" style={{ backgroundColor: o.qarzdor ? "#FCEBEB" : "#EAF3DE" }}>
                      <div>
                        <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{o.full_name}</p>
                        <p className="text-xs" style={{ color: o.qarzdor ? "#A32D2D" : "#3B6D11" }}>
                          {o.qarzdor ? __kbUi(`⚠️ Qarzdor (${o.tolangan_summa.toLocaleString()} / ${o.kerakli_summa.toLocaleString()} so'm)`) : __kbUi("✅ To'langan")}
                        </p>
                      </div>
                      {o.qarzdor && (
                        <button onClick={() => tolovBelgila(o)} className="text-xs font-semibold px-3 py-1.5 rounded-lg text-white" style={{ backgroundColor: "#1B4B7A" }}>{__kbUi("To'landi")}</button>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}
            <p className="text-sm font-semibold mb-2.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("👥 Sinf a'zolari")}</p>
            <div className="space-y-2">
              {(azolar || []).map((a) => (
                <button key={a.azolik_id} onClick={() => setTanlanganOquvchiId(a.user_id)}
                  className="w-full text-left rounded-xl p-3.5 flex items-center justify-between" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                  <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{a.full_name}</p>
                  <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
                </button>
              ))}
              {(azolar || []).length === 0 && <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali hech kim qo'shilmagan.")}</p>}
            </div>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("To'garaklarim")}</button>
      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : xato ? (
        <p className="text-sm" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>
      ) : (
        <>
          <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>🏫 {malumot.maktab_nomi}</h1>
          <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Butun maktab — bir ekranda.")}</p>

          {malumot.bugungi_davomat && (
            <div className="rounded-2xl p-4 mb-4" style={{ backgroundColor: "#FFFDF7", border: "1px solid #F5DFA3" }}>
              <p className="text-sm font-bold mb-2" style={{ color: "#8A5A1C" }}>{__kbUi("📋 Bugungi davomat")}</p>
              <div className="grid grid-cols-3 gap-2">
                <div className="rounded-xl p-2.5 text-center bg-white">
                  <p className="text-lg font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{malumot.bugungi_davomat.jami_oquvchi}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("jami o'quvchi")}</p>
                </div>
                <div className="rounded-xl p-2.5 text-center bg-white">
                  <p className="text-lg font-bold" style={{ color: "#3B6D11" }}>{malumot.bugungi_davomat.kelgan}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("keldi")}</p>
                </div>
                <div className="rounded-xl p-2.5 text-center bg-white">
                  <p className="text-lg font-bold" style={{ color: "#A32D2D" }}>{malumot.bugungi_davomat.sinflar_belgilamagan}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("sinf hali belgilamagan")}</p>
                </div>
              </div>
            </div>
          )}

          {malumot.xodim_bugungi_davomat && (
            <div className="rounded-2xl p-4 mb-4" style={{ backgroundColor: "#F3F0FF", border: "1px solid #D8CCF5" }}>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-bold" style={{ color: "#5A3D9E" }}>{__kbUi("🧑‍🏫 Bugungi xodim davomati")}</p>
                <button onClick={() => setXodimDavomatKorinishi(true)} className="text-xs font-semibold px-2.5 py-1 rounded-lg text-white" style={{ backgroundColor: "#5A3D9E" }}>{__kbUi("Belgilash")}</button>
              </div>
              <p className="text-sm" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>
                {malumot.xodim_bugungi_davomat.keldi} / {malumot.xodim_bugungi_davomat.jami}{__kbUi(" xodim keldi")}</p>
            </div>
          )}

          {malumot.tolov_xulosasi && (
            <div className="rounded-2xl p-4 mb-4" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
              <p className="text-sm font-bold mb-2" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>💳 {joriyOy}{__kbUi(" — umumiy to'lov holati")}</p>
              <div className="grid grid-cols-3 gap-2">
                <div className="rounded-xl p-2.5 text-center bg-white">
                  <p className="text-lg font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{malumot.tolov_xulosasi.jami_oquvchi}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("jami o'quvchi")}</p>
                </div>
                <div className="rounded-xl p-2.5 text-center bg-white">
                  <p className="text-lg font-bold" style={{ color: "#3B6D11" }}>{malumot.tolov_xulosasi.tolagan}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("to'lagan")}</p>
                </div>
                <div className="rounded-xl p-2.5 text-center bg-white">
                  <p className="text-lg font-bold" style={{ color: "#A32D2D" }}>{malumot.tolov_xulosasi.qarzdor}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("qarzdor")}</p>
                </div>
              </div>
            </div>
          )}

          {(malumot.reyting?.eng_yaxshi_sinf || malumot.reyting?.etibor_kerak_sinf) && (
            <div className="grid grid-cols-2 gap-2.5 mb-4">
              {malumot.reyting.eng_yaxshi_sinf && (
                <div className="rounded-2xl p-3.5" style={{ backgroundColor: "#EAF3DE" }}>
                  <p className="text-xs font-semibold mb-1" style={{ color: "#3B6D11" }}>{__kbUi("🏆 Eng yaxshi sinf")}</p>
                  <p className="text-sm font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{malumot.reyting.eng_yaxshi_sinf.sinf}-{malumot.reyting.eng_yaxshi_sinf.harf}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{malumot.reyting.eng_yaxshi_sinf.ortacha_bilim}{__kbUi("% bilim")}</p>
                </div>
              )}
              {malumot.reyting.etibor_kerak_sinf && (
                <div className="rounded-2xl p-3.5" style={{ backgroundColor: "#FDF3E0" }}>
                  <p className="text-xs font-semibold mb-1" style={{ color: "#8A5A1C" }}>{__kbUi("💪 E'tibor kerak")}</p>
                  <p className="text-sm font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{malumot.reyting.etibor_kerak_sinf.sinf}-{malumot.reyting.etibor_kerak_sinf.harf}</p>
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{malumot.reyting.etibor_kerak_sinf.ortacha_bilim}{__kbUi("% bilim")}</p>
                </div>
              )}
            </div>
          )}

          {malumot.muammoli_oquvchilar && malumot.muammoli_oquvchilar.length > 0 && (
            <div className="rounded-2xl p-4 mb-4 border" style={{ backgroundColor: "#FCEBEB", borderColor: "#E8A0A0" }}>
              <p className="text-sm font-bold mb-1" style={{ color: "#A32D2D" }}>{__kbUi("⚠️ Muammoli o'quvchilar")}</p>
              <p className="text-xs mb-3" style={{ color: "#8A5A5A" }}>{__kbUi("Oxirgi 7 kunda 2+ marta kelmagan")}</p>
              <div className="space-y-1.5">
                {malumot.muammoli_oquvchilar.map((o) => (
                  <button key={o.user_id} onClick={() => setTanlanganOquvchiId(o.user_id)}
                    className="w-full flex items-center justify-between bg-white rounded-lg px-3 py-2">
                    <span className="text-sm" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{o.full_name}</span>
                    <span className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{o.sinf}-{o.harf} · {o.songi_hafta_kelmagan}{__kbUi(" kun")}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-2 mb-2.5">
            <button onClick={() => setTepaKorinish("sinflar")}
              className="flex-1 py-2 rounded-lg text-xs font-semibold"
              style={tepaKorinish === "sinflar" ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>📚 <InterfaceText text={__kbUi("Sinflar")}/></button>
            <button onClick={() => setTepaKorinish("oqituvchilar")}
              className="flex-1 py-2 rounded-lg text-xs font-semibold"
              style={tepaKorinish === "oqituvchilar" ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>👩‍🏫 <InterfaceText text={__kbUi("O'qituvchilar")}/></button>
            <button onClick={() => setTepaKorinish("reyting")}
              className="flex-1 py-2 rounded-lg text-xs font-semibold"
              style={tepaKorinish === "reyting" ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>{__kbUi("🏆 Reyting")}</button>
          </div>

          {tepaKorinish === "reyting" && (
            <>
              <p className="text-sm font-semibold mb-2.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🏆 Sinflar reytingi (bilim bo'yicha)")}</p>
              <div className="space-y-2">
                {[...malumot.sinflar].filter((s) => s.ortacha_bilim !== null).sort((a, b) => b.ortacha_bilim - a.ortacha_bilim).map((s, i) => (
                  <button key={s.id} onClick={() => sinfOch(s)}
                    className="w-full text-left rounded-xl p-3.5 bg-white border flex items-center gap-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                    <span className="text-sm font-bold w-6 text-center shrink-0" style={{ color: i === 0 ? "#C89B3C" : "#8A8578" }}>
                      {i === 0 ? __kbUi("🥇") : i === 1 ? __kbUi("🥈") : i === 2 ? __kbUi("🥉") : i + 1}
                    </span>
                    <div className="flex-1">
                      <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{s.sinf}-{s.harf}</p>
                      <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{s.rahbar_ismi || __kbUi("Rahbar yo'q")} · {s.oquvchi_soni}{__kbUi(" o'quvchi")}</p>
                    </div>
                    <span className="text-sm font-bold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{s.ortacha_bilim}%</span>
                  </button>
                ))}
                {malumot.sinflar.filter((s) => s.ortacha_bilim !== null).length === 0 && (
                  <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali hech bir sinfda test yechilmagan — reyting uchun ma'lumot yo'q.")}</p>
                )}
              </div>
            </>
          )}

          {tepaKorinish === "sinflar" ? (
            <>
              <p className="text-sm font-semibold mb-2.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📚 Sinflar (")}{malumot.sinflar.length})</p>
              <div className="space-y-2">
                {malumot.sinflar.map((s) => (
                  <button key={s.id} onClick={() => sinfOch(s)}
                    className="w-full text-left rounded-xl p-3.5 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                    <div>
                      <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{s.sinf}-{s.harf}</p>
                      <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
                        {s.rahbar_ismi || __kbUi("Rahbar yo'q")} · {s.oquvchi_soni}{__kbUi(" o'quvchi")}{malumot.pulli ? __kbUi(` · ${s.tolagan_soni}/${s.oquvchi_soni} to'lagan`) : __kbUi("")}
                        {s.ortacha_bilim !== null ? __kbUi(` · ${s.ortacha_bilim}% bilim`) : __kbUi("")}
                      </p>
                    </div>
                    <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
                  </button>
                ))}
              </div>
            </>
          ) : (
            <>
              <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("👩‍🏫 Sinf rahbarlari (")}{malumot.sinflar.filter((s) => s.rahbar_ismi).length})</p>
              <p className="text-xs mb-2.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Davomatni oxirgi 7 kunda necha kun belgilagani — intizom ko'rsatkichi sifatida.")}</p>
              <div className="space-y-2">
                {[...malumot.sinflar].filter((s) => s.rahbar_ismi).sort((a, b) => b.davomat_kun_7 - a.davomat_kun_7).map((s) => {
                  const rang = s.davomat_kun_7 >= 5 ? "#3B6D11" : s.davomat_kun_7 >= 3 ? "#8A5A1C" : "#A32D2D";
                  const fon = s.davomat_kun_7 >= 5 ? "#EAF3DE" : s.davomat_kun_7 >= 3 ? "#FDF3E0" : "#FCEBEB";
                  return (
                    <button key={s.id} onClick={() => sinfOch(s)}
                      className="w-full text-left rounded-xl p-3.5 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                      <div>
                        <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{s.rahbar_ismi}</p>
                        <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
                          {s.sinf}-{s.harf}{__kbUi(" sinf rahbari · ")}{s.oquvchi_soni}{__kbUi(" o'quvchi")}{s.ortacha_bilim !== null ? __kbUi(` · ${s.ortacha_bilim}% bilim`) : __kbUi("")}
                        </p>
                      </div>
                      <span className="text-xs font-bold px-2.5 py-1 rounded-full shrink-0 ml-2" style={{ backgroundColor: fon, color: rang }}>
                        {s.davomat_kun_7}{__kbUi("/7 kun")}</span>
                    </button>
                  );
                })}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

function MarkazBoshqaruvi({ token, markazId, onOrtga }) {
  useKbInterfaceLocale();
  const [guruhlar, setGuruhlar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");
  const [tanlanganGuruh, setTanlanganGuruh] = useState(null);
  const [oquvchilar, setOquvchilar] = useState(null);
  const [oquvchilarYuklanmoqda, setOquvchilarYuklanmoqda] = useState(false);
  const joriyOy = new Date().toISOString().slice(0, 7);

  useEffect(() => {
    if (!markazId) { setYuklanmoqda(false); return; }
    fetch(`${API_BASE}/api/markaz/dashboard?token=${encodeURIComponent(token)}&markaz_id=${markazId}`)
      .then((r) => r.json())
      .then((d) => { setGuruhlar(d.guruhlar || []); setYuklanmoqda(false); })
      .catch(() => { setXato("Yuklab bo'lmadi"); setYuklanmoqda(false); });
  }, [token, markazId]);

  const guruhOch = (g) => {
    setTanlanganGuruh(g);
    if (!g.oylik_summa) return;
    setOquvchilarYuklanmoqda(true);
    fetch(`${API_BASE}/api/markaz/guruh_tolovlari?token=${encodeURIComponent(token)}&togarak_id=${g.id}&oy=${joriyOy}`)
      .then((r) => r.json())
      .then((d) => { setOquvchilar(d.oquvchilar || []); setOquvchilarYuklanmoqda(false); })
      .catch(() => setOquvchilarYuklanmoqda(false));
  };

  const tolovBelgila = async (o) => {
    await fetch(`${API_BASE}/api/markaz/tolov_belgila`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, user_id: o.user_id, togarak_id: tanlanganGuruh.id, oy: joriyOy, tolangan_summa: tanlanganGuruh.oylik_summa }),
    });
    guruhOch(tanlanganGuruh);
  };

  if (!markazId) {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("To'garaklarim")}</button>
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Siz hech qanday markazga bog'lanmagansiz.")}</p>
        </div>
      </div>
    );
  }

  if (tanlanganGuruh) {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => setTanlanganGuruh(null)} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Guruhlar")}/></button>
        <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{tanlanganGuruh.nomi}</h1>
        <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{tanlanganGuruh.fan} · {tanlanganGuruh.oqituvchi_ismi} · {tanlanganGuruh.azo_soni}{__kbUi(" a'zo")}</p>

        {!tanlanganGuruh.oylik_summa ? (
          <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bu guruh uchun oylik to'lov summasi belgilanmagan.")}</p>
          </div>
        ) : oquvchilarYuklanmoqda ? (
          <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
        ) : (
          <>
            <p className="text-sm font-semibold mb-2.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>💳 {joriyOy}{__kbUi(" oyi to'lovlari")}</p>
            <div className="space-y-2">
              {(oquvchilar || []).map((o) => (
                <div key={o.user_id} className="rounded-xl p-3.5 flex items-center justify-between" style={{ backgroundColor: o.qarzdor ? "#FCEBEB" : "#EAF3DE" }}>
                  <div>
                    <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{o.full_name}</p>
                    <p className="text-xs" style={{ color: o.qarzdor ? "#A32D2D" : "#3B6D11" }}>
                      {o.qarzdor ? __kbUi(`⚠️ Qarzdor (${o.tolangan_summa.toLocaleString()} / ${o.kerakli_summa.toLocaleString()} so'm)`) : __kbUi("✅ To'langan")}
                    </p>
                  </div>
                  {o.qarzdor && (
                    <button onClick={() => tolovBelgila(o)} className="text-xs font-semibold px-3 py-1.5 rounded-lg text-white" style={{ backgroundColor: "#1B4B7A" }}>{__kbUi("To'landi deb belgilash")}</button>
                  )}
                </div>
              ))}
              {(oquvchilar || []).length === 0 && <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bu guruhda hali tasdiqlangan a'zo yo'q.")}</p>}
            </div>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("To'garaklarim")}</button>
      <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🎓 Markaz boshqaruvi")}</h1>
      <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Markazingizga bog'langan barcha guruhlar — bitta ekranda.")}</p>
      {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : guruhlar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali markazga bog'langan guruh yo'q — fan o'qituvchilaringiz to'garak yaratganda, avtomatik shu yerga qo'shiladi.")}</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {guruhlar.map((g) => (
            <button key={g.id} onClick={() => guruhOch(g)}
              className="w-full text-left rounded-xl p-4 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div>
                <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{g.nomi}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
                  {g.fan} · {g.oqituvchi_ismi || __kbUi("O'qituvchi yo'q")} · {g.azo_soni}{__kbUi(" a'zo")}{g.oylik_summa ? __kbUi(` · ${g.oylik_summa.toLocaleString()} so'm/oy`) : __kbUi("")}
                </p>
              </div>
              <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function OtaOnaQidiruvi({ token, guruhId, tanlanganOtaOna, onTanla }) {
  useKbInterfaceLocale();
  const [ism, setIsm] = useState("");
  const [natijalar, setNatijalar] = useState([]);
  const [qidirilmoqda, setQidirilmoqda] = useState(false);

  useEffect(() => {
    if (ism.trim().length < 2) { setNatijalar([]); return; }
    setQidirilmoqda(true);
    const kechiktirish = setTimeout(() => {
      fetch(`${API_BASE}/api/opa/ota_ona_qidir?ism=${encodeURIComponent(ism.trim())}&guruh_id=${guruhId}`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
        credentials: "omit",
      })
        .then((r) => r.json())
        .then((d) => { setNatijalar(d.natijalar || []); setQidirilmoqda(false); })
        .catch(() => setQidirilmoqda(false));
    }, 400);
    return () => clearTimeout(kechiktirish);
  }, [guruhId, ism, token]);

  if (tanlanganOtaOna) {
    return (
      <div className="flex items-center justify-between px-3 py-2 rounded-lg mb-2" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
        <span className="text-xs font-medium" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>👤 {tanlanganOtaOna.full_name}</span>
        <button onClick={() => onTanla(null)} className="text-xs font-medium" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>✕</button>
      </div>
    );
  }

  return (
    <div className="mb-2">
      <input type="text" value={ism} onChange={(e) => setIsm(e.target.value)}
        placeholder={__kbUi("Ota-onasini qidiring (ixtiyoriy)...")}
        className="w-full px-3.5 py-2 rounded-lg border text-xs"
        style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
      {qidirilmoqda && <p className="text-xs mt-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Qidirilmoqda...")}</p>}
      {natijalar.length > 0 && (
        <div className="mt-1 space-y-1">
          {natijalar.map((o) => (
            <button key={o.user_id} onClick={() => { onTanla(o); setIsm(""); setNatijalar([]); }}
              className="w-full flex items-center px-3 py-1.5 rounded-lg text-left" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
              <span className="text-xs" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{o.full_name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function BogchaGuruhim({ token, onOrtga }) {
  useKbInterfaceLocale();
  const [guruhlar, setGuruhlar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [tanlanganGuruh, setTanlanganGuruh] = useState(null);
  const [bolalar, setBolalar] = useState(null);
  const [bolalarYuklanmoqda, setBolalarYuklanmoqda] = useState(false);
  const [yangiBolaIsmi, setYangiBolaIsmi] = useState("");
  const [tanlanganOtaOna, setTanlanganOtaOna] = useState(null);
  const [qoshilmoqda, setQoshilmoqda] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/opa/mening_guruhlarim`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
      credentials: "omit",
    })
      .then((r) => r.json())
      .then((d) => { setGuruhlar(d.guruhlar || []); setYuklanmoqda(false); })
      .catch(() => setYuklanmoqda(false));
  }, [token]);

  const bolalarniYukla = (guruhId) => {
    setBolalarYuklanmoqda(true);
    fetch(`${API_BASE}/api/opa/guruh_bolalari?guruh_id=${guruhId}`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
      credentials: "omit",
    })
      .then((r) => r.json())
      .then((d) => { setBolalar(d.bolalar || []); setBolalarYuklanmoqda(false); })
      .catch(() => setBolalarYuklanmoqda(false));
  };

  const guruhOch = (g) => { setTanlanganGuruh(g); bolalarniYukla(g.id); };

  const bolaQosh = async () => {
    if (!yangiBolaIsmi.trim()) return;
    setQoshilmoqda(true);
    try {
      await fetch(`${API_BASE}/api/opa/bola_qoshish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token, guruh_id: tanlanganGuruh.id, bola_ismi: yangiBolaIsmi.trim(),
          ota_ona_user_id: tanlanganOtaOna ? tanlanganOtaOna.user_id : undefined,
        }),
      });
      setYangiBolaIsmi(""); setTanlanganOtaOna(null);
      bolalarniYukla(tanlanganGuruh.id);
    } finally { setQoshilmoqda(false); }
  };

  const bolaniChiqar = async (rosterId) => {
    await fetch(`${API_BASE}/api/opa/bolani_chiqar?roster_id=${rosterId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
      credentials: "omit",
    });
    bolalarniYukla(tanlanganGuruh.id);
  };

  if (tanlanganGuruh) {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => setTanlanganGuruh(null)} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("Guruhlarim")}</button>
        <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{tanlanganGuruh.nomi}</h1>
        <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{tanlanganGuruh.bogcha_nomi}</p>

        <div className="rounded-xl p-3.5 mb-4" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Yangi bola qo'shish")}</label>
          <OtaOnaQidiruvi
            token={token}
            guruhId={tanlanganGuruh.id}
            tanlanganOtaOna={tanlanganOtaOna}
            onTanla={setTanlanganOtaOna}
          />
          <div className="flex gap-2">
            <input type="text" value={yangiBolaIsmi} onChange={(e) => setYangiBolaIsmi(e.target.value)}
              placeholder={__kbUi("Bolaning ismi va familiyasi")}
              className="flex-1 px-3.5 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            <button onClick={bolaQosh} disabled={qoshilmoqda}
              className="px-4 py-2.5 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: qoshilmoqda ? 0.7 : 1 }}>
              {qoshilmoqda ? __kbUi("...") : __kbUi("+ Qo'shish")}
            </button>
          </div>
        </div>

        {bolalarYuklanmoqda ? (
          <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
        ) : !bolalar || bolalar.length === 0 ? (
          <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali guruhda bola yo'q.")}</p>
        ) : (
          <>
            <p className="text-sm font-semibold mb-2.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("👶 Guruh ro‘yxati")}</p>
            <div className="space-y-2">
              {bolalar.map((b) => (
                <div key={b.roster_id} className="rounded-xl p-3.5 flex items-center justify-between"
                  style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                  <div>
                    <p className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{b.full_name}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => bolaniChiqar(b.roster_id)} className="text-xs font-medium px-2.5 py-1.5 rounded-lg" style={{ backgroundColor: "var(--ui-legacy-background-fff, #fff)", color: "#A32D2D", border: "1px solid #E5E1D8" }}>
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("Guruhlarim")}</button>
      <h1 className="text-xl font-bold mb-5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🧸 Bog'cha guruhim")}</h1>
      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : guruhlar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Sizga hali guruh biriktirilmagan.")}</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {guruhlar.map((g) => (
            <button key={g.id} onClick={() => guruhOch(g)}
              className="w-full text-left rounded-xl p-4 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div>
                <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{g.nomi}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{g.bogcha_nomi} · {g.bola_soni}{__kbUi(" bola")}</p>
              </div>
              <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function UniversitetGuruhimBilimi({ token, onOrtga }) {
  useKbInterfaceLocale();
  const [guruhlar, setGuruhlar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [tanlanganGuruh, setTanlanganGuruh] = useState(null);
  const [bilim, setBilim] = useState(null);
  const [bilimYuklanmoqda, setBilimYuklanmoqda] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/universitet/mening_guruhlarim?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => { setGuruhlar(d.guruhlar || []); setYuklanmoqda(false); })
      .catch(() => setYuklanmoqda(false));
  }, [token]);

  const guruhOch = (g) => {
    setTanlanganGuruh(g);
    setBilimYuklanmoqda(true);
    fetch(`${API_BASE}/api/universitet/guruh_bilimi?token=${encodeURIComponent(token)}&guruh_id=${g.id}`)
      .then((r) => r.json())
      .then((d) => { setBilim(d); setBilimYuklanmoqda(false); })
      .catch(() => setBilimYuklanmoqda(false));
  };

  const foizRangi = (foiz) => (foiz >= 70 ? "#3B6D11" : foiz >= 40 ? "#8A5A1C" : "#A32D2D");
  const foizFoni = (foiz) => (foiz >= 70 ? "#EAF3DE" : foiz >= 40 ? "#FDF3E0" : "#FCEBEB");

  if (tanlanganGuruh) {
    // Kurslar (fan-birinchi) ma'lumotini talaba-birinchi ko'rinishga aylantiramiz —
    // har bir talaba kartochkasida BARCHA fanlari bir joyda ko'rinishi uchun.
    const talabaMap = {};
    if (bilim) {
      for (const k of bilim.kurslar) {
        for (const t of k.talabalar) {
          if (!talabaMap[t.user_id]) talabaMap[t.user_id] = { full_name: t.full_name, fanlar: [] };
          talabaMap[t.user_id].fanlar.push({ fan: k.fan, foiz: t.otilgan_foiz, ball: t.ortacha_ball });
        }
      }
    }
    const talabalarRoyxati = Object.values(talabaMap);

    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => setTanlanganGuruh(null)} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("Guruhlarim")}</button>
        <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>📊 {tanlanganGuruh.nomi}{__kbUi(" — bilim ko'rsatkichi")}</h1>
        <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Silabus mavzulari bo'yicha, har fandan alohida — GPA emas, aniq bilim darajasi.")}</p>

        {bilimYuklanmoqda ? (
          <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
        ) : !bilim || bilim.kurslar.length === 0 ? (
          <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <p className="text-sm mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Hali bu guruhga bog'langan fan yo'q.")}</p>
            <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Professor to'garak (kurs) yaratganda, shu guruhni tanlashi kerak.")}</p>
          </div>
        ) : talabalarRoyxati.length === 0 ? (
          <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali hech bir talaba fanlarga qo'shilmagan.")}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {talabalarRoyxati.map((t, i) => {
              const ortachaFoiz = Math.round(t.fanlar.reduce((s, f) => s + f.foiz, 0) / t.fanlar.length);
              return (
                <div key={i} className="rounded-2xl p-4 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{t.full_name}</p>
                    <span className="text-xs font-bold px-2.5 py-1 rounded-full" style={{ backgroundColor: foizFoni(ortachaFoiz), color: foizRangi(ortachaFoiz) }}>{__kbUi("Umumiy: ")}{ortachaFoiz}%
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {t.fanlar.map((f, j) => (
                      <span key={j} className="text-xs font-medium px-2.5 py-1.5 rounded-lg" style={{ backgroundColor: foizFoni(f.foiz), color: foizRangi(f.foiz) }}>
                        {__kbUi(f.fan)}: {__kbUi(f.foiz)}%{f.ball !== null ? __kbUi(` (o'rtacha ${f.ball} ball)`) : __kbUi("")}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("Guruhlarim")}</button>
      <h1 className="text-xl font-bold mb-5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🎓 Kurator bo'lgan guruhlarim")}</h1>
      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : guruhlar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Sizga hali guruh biriktirilmagan.")}</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {guruhlar.map((g) => (
            <button key={g.id} onClick={() => guruhOch(g)}
              className="w-full text-left rounded-xl p-4 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div>
                <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{g.nomi}</p>
                <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{g.kurs ? __kbUi(`${g.kurs}-kurs`) : __kbUi("")}{g.yonalish ? __kbUi(` · ${g.yonalish}`) : __kbUi("")} · {g.talaba_soni}{__kbUi(" talaba")}</p>
              </div>
              <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

const AI_USTOZ_REJIMLARI = [
  { kalit: "diagnostika", nom: "Aniqlash", emoji: "🔍", boshlash: "Bu mavzu bo'yicha bilimimni aniqlang." },
  { kalit: "orgatish", nom: "O'rgatish", emoji: "💡", boshlash: "Mavzuni yoshimga mos qilib tushuntiring." },
  { kalit: "mashq", nom: "Mashq", emoji: "✍️", boshlash: "Menga mustaqil ishlash uchun bitta mashq bering." },
  { kalit: "takrorlash", nom: "Takrorlash", emoji: "🔁", boshlash: "Mavzuni xotiradan eslashim uchun savol bering." },
  { kalit: "test", nom: "Test", emoji: "✅", boshlash: "Menga bitta test savoli bering, javobni aytmang." },
  { kalit: "togarak", nom: "To'garak", emoji: "🌟", boshlash: "Menga qiziqarli va izlanishli topshiriq bering." },
];

const AI_BLOK_RANGLARI = {
  maqsad: { fon: "#EAF1F7", rang: "#1B4B7A" },
  qiziqish: { fon: "#FDF3E0", rang: "#8A5A1C" },
  tushuntirish: { fon: "#F3EEFA", rang: "#6E45A1" },
  qoida: { fon: "#EAF1F7", rang: "#1B4B7A" },
  misol: { fon: "#EAF3DE", rang: "#3B6D11" },
  savol: { fon: "#FDF3E0", rang: "#8A5A1C" },
  mashq: { fon: "#EAF3DE", rang: "#3B6D11" },
  ishora: { fon: "#FFF8D6", rang: "#7A5A00" },
  togri: { fon: "#EAF3DE", rang: "#2E6B2E" },
  xato: { fon: "#FCEBEB", rang: "#A32D2D" },
  ogohlantirish: { fon: "#FCEBEB", rang: "#A32D2D" },
  xulosa: { fon: "#EAF1F7", rang: "#1B4B7A" },
};

function AiJavobBloklari({ javob, onQuickReply }) {
  useKbInterfaceLocale();
  if (!javob?.bloklar?.length) return null;
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-1.5 px-1">
        <span className="text-[10px] font-semibold px-2 py-1 rounded-full"
          style={javob.knowledge_status === "published"
            ? { backgroundColor: "#E7F4EC", color: "#25683B" }
            : { backgroundColor: "#FFF4D8", color: "#8A5A1C" }}>
          {javob.knowledge_status === "published" ? __kbUi("✓ Tasdiqlangan kitob bazasi") : __kbUi("⚠ Bilim hali nashr qilinmagan")}
        </span>
        {javob.engine === "rules" && (
          <span className="text-[10px] px-2 py-1 rounded-full" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("API kalitsiz pedagogik miya")}</span>
        )}
      </div>
      {javob.bloklar.map((blok, i) => {
        const uslub = AI_BLOK_RANGLARI[blok.tur] || AI_BLOK_RANGLARI.tushuntirish;
        return (
          <div key={i} className="rounded-xl p-3.5 flex items-start gap-2.5"
            style={{ backgroundColor: uslub.fon, color: uslub.rang }}>
            <span className="text-lg shrink-0" aria-hidden="true">{blok.emoji || __kbUi("💡")}</span>
            <div className="text-sm leading-relaxed min-w-0">
              <Matn matn={blok.matn} />
            </div>
          </div>
        );
      })}
      {javob.manba_kodlari?.length > 0 && (
        <p className="text-[10px] px-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Baza manbasi: ")}{__kbUi(javob.manba_kodlari.join(", "))}
        </p>
      )}
      {(javob.sources || []).length > 0 && (
        <div className="rounded-xl p-2.5 space-y-1" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
          {(javob.sources || []).slice(0, 3).map((s, i) => (
            <p key={`${s.source_code || "source"}-${s.page || i}`} className="text-[10px]" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
              📚 {s.book || s.source_code || __kbUi("Kitob")}{s.page ? __kbUi(` · ${s.page}-bet`) : __kbUi("")}{s.year ? __kbUi(` · ${s.year}`) : __kbUi("")}
            </p>
          ))}
        </div>
      )}
      {(javob.quick_replies || []).length > 0 && onQuickReply && (
        <div className="flex flex-wrap gap-1.5 px-1">
          {javob.quick_replies.map((reply) => (
            <button key={reply} onClick={() => onQuickReply(reply)}
              className="min-w-9 px-3 py-2 rounded-xl text-xs font-bold border"
              style={{ borderColor: "#9DB8CE", backgroundColor: "var(--ui-legacy-background-f4f8fb, #F4F8FB)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
              {reply}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function AiOquvchiUstozBolimi({ token, initialTarget = null, foydalanuvchi = null, onOpenTest = null }) {
  useKbInterfaceLocale();
  const [sozlama, setSozlama] = useState(null);
  const fallbackType=profileInstitutionType(foydalanuvchi);
  const [catalogType,setCatalogType]=useState(fallbackType);
  const [catalogLesson,setCatalogLesson]=useState('maruza');
  const sectionChosen=useRef(false);

  const [fan, setFan] = useState("");
  const [topicCode, setTopicCode] = useState("");
  const [rejim, setRejim] = useState("orgatish");
  const [suhbatId, setSuhbatId] = useState(null);
  const [xabarlar, setXabarlar] = useState([]);
  const [matn, setMatn] = useState("");
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [yuborilmoqda, setYuborilmoqda] = useState(false);
  const [xato, setXato] = useState("");
  const [darsXonasi, setDarsXonasi] = useState(() => Boolean(initialTarget?.topic_code));
  const oxiriRef = useRef(null);

  useEffect(()=>{
    sectionChosen.current=false;
    if(initialTarget?.institution_type)setCatalogType(initialTarget.institution_type);
    if(initialTarget?.dars_turi)setCatalogLesson(initialTarget.dars_turi);
    // «O'rganish» tugmasidan kelinsa — avval dars xonasi (doska) ochiladi.
    if(initialTarget?.topic_code)setDarsXonasi(true);
  },[initialTarget?.nonce]);

  useEffect(() => {
    const controller=new AbortController();
    const params=new URLSearchParams({token,institution_type:catalogType});
    if(initialTarget?.grade&&!sectionChosen.current)params.set('grade',String(initialTarget.grade));
    setYuklanmoqda(true);setXato('');setSozlama(null);setFan('');setTopicCode('');setSuhbatId(null);setXabarlar([]);
    fetch(`${API_BASE}/api/ai/ustoz/fan_mavzular?${params}`,{signal:controller.signal})
      .then(async response=>{const data=await response.json();if(!response.ok)throw new Error(data.detail||'Mavzular yuklanmadi');return data;})
      .then(data=>{
        if(controller.signal.aborted)return;
        setSozlama(data);
        if(data.viewer?.preferred_type&&((!sectionChosen.current&&!initialTarget?.institution_type)||!data.viewer.types.includes(catalogType))&&catalogType!==data.viewer.preferred_type){setCatalogType(data.viewer.preferred_type);return;}
        const all=data.fanlar||[];
        const targeted=!sectionChosen.current&&initialTarget?.topic_code?all.find(subject=>subject.mavzular.some(topic=>topic.topic_code===initialTarget.topic_code)):null;
        const selectedLesson=targeted?.dars_turi || catalogLesson;
        if(targeted?.dars_turi)setCatalogLesson(targeted.dars_turi);
        const visible=matchingSubjects(all,catalogType,selectedLesson);
        const subject=targeted||visible.find(subject=>subject.fan===initialTarget?.subject)||visible[0];
        const topic=subject?.mavzular.find(topic=>topic.topic_code===initialTarget?.topic_code)||subject?.mavzular[0];
        setFan(subject?.kalit||'');setTopicCode(topic?.topic_code||'');
      }).catch(error=>{if(!controller.signal.aborted)setXato(error.message);})
      .finally(()=>{if(!controller.signal.aborted)setYuklanmoqda(false);});
    return()=>controller.abort();
  },[token,catalogType,initialTarget?.nonce,foydalanuvchi?.talaba_profili?.yangilangan_at]);

  useEffect(() => {
    oxiriRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [xabarlar, yuborilmoqda]);

  const visibleSubjects=matchingSubjects(sozlama?.fanlar||[],catalogType,catalogLesson);
  const joriyFan = visibleSubjects.find((f) => f.kalit === fan);
  const joriyMavzu = joriyFan?.mavzular?.find((m) => m.topic_code === topicCode);

  const fanOzgar = (yangiFan) => {
    const f = visibleSubjects.find((x) => x.kalit === yangiFan);
    setFan(yangiFan);
    setTopicCode(f?.mavzular?.[0]?.topic_code || "");
    setSuhbatId(null);
    setXabarlar([]);
  };

  const changeCatalog=(type,lesson='maruza')=>{
    sectionChosen.current=true;setCatalogType(type);setCatalogLesson(lesson);
    const subject=matchingSubjects(sozlama?.fanlar||[],type,lesson)[0];
    setFan(subject?.kalit||'');setTopicCode(subject?.mavzular[0]?.topic_code||'');
    setSuhbatId(null);setXabarlar([]);setMatn('');setXato('');
  };
  const catalogHeader=<LearnerCurriculumHeader viewer={sozlama?.viewer} type={catalogType} lesson={catalogLesson} fallbackType={fallbackType} onType={type=>changeCatalog(type)} onLesson={lesson=>changeCatalog(catalogType,lesson)} disabled={yuborilmoqda}/>;

  const mavzuOzgar = (kod) => {
    setTopicCode(kod);
    setSuhbatId(null);
    setXabarlar([]);
  };

  const rejimOzgar = (kalit) => {
    setRejim(kalit);
    setSuhbatId(null);
    setXabarlar([]);
  };

  const yubor = async (tayyorMatn = null) => {
    const yuboriladigan = (tayyorMatn || matn).trim();
    if (!yuboriladigan || !fan || !topicCode || yuborilmoqda) return;
    setMatn("");
    setXato("");
    setXabarlar((oldin) => [...oldin, { muallif: "oquvchi", matn: yuboriladigan }]);
    setYuborilmoqda(true);
    try {
      const res = await fetch(`${API_BASE}/api/ai/ustoz/sorash`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token, fan: joriyFan?.fan, topic_code: topicCode, grade: joriyMavzu?.grade || sozlama?.sinf || initialTarget?.grade || undefined,
          rejim, savol: yuboriladigan,
          suhbat_id: suhbatId,
        }),
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "AI ustoz javob bermadi");
      setSuhbatId(d.suhbat_id);
      setXabarlar((oldin) => [...oldin, { muallif: "ai", javob: d.javob }]);
    } catch (e) {
      setXato(e.message);
      setXabarlar((oldin) => [...oldin, { muallif: "xato", matn: e.message }]);
    } finally {
      setYuborilmoqda(false);
    }
  };

  if (yuklanmoqda) {
    return <div className="py-16 text-center"><Loader2 size={26} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>;
  }

  if (sozlama?.sinf_sozlanmagan) {
    return (
      <div className="px-5 pt-6">
        {catalogHeader}
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Profil ma’lumotlarini to‘ldiring")}</p>
          <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Profil bo‘limida muassasa, yo‘nalish, ta’lim shakli, kurs va semestrni to‘g‘ri saqlang.")}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 pt-5 pb-4">
      {catalogHeader}
      <div className="rounded-2xl p-4 mb-3 text-white overflow-hidden relative"
        style={{ background: "linear-gradient(135deg,#1B4B7A,#2D6E8B)" }}>
        <div className="relative z-10">
          <p className="text-xs opacity-80">{__kbUi("Sizning shaxsiy yordamchingiz")}</p>
          <h1 className="text-xl font-bold mt-0.5" style={{ color: "#fff" }}>🧠 <InterfaceText text={__kbUi("AI Ustoz")}/></h1>
          <p className="text-xs mt-1 opacity-90">
            {__kbUi(gradeLabel(catalogType,sozlama?.sinf))} · {catalogType==='universitet'?__kbUi(lessonLabel(catalogLesson)):__kbUi(institutionLabel(catalogType))}
          </p>
        </div>
      </div>

      {!visibleSubjects.length&&<p className="mb-3 rounded-xl bg-amber-50 p-3 text-sm text-amber-900">{__kbUi("Tanlangan bo‘limda profilingizga mos mavzu hali kiritilmagan.")}</p>}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <select value={fan} onChange={(e) => fanOzgar(e.target.value)}
          className="px-3 py-2.5 rounded-xl border text-xs bg-white" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          {visibleSubjects.map((f) => <option key={f.kalit} value={f.kalit}>{f.fan}</option>)}
        </select>
        <select value={topicCode} onChange={(e) => mavzuOzgar(e.target.value)}
          className="px-3 py-2.5 rounded-xl border text-xs bg-white" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          {(joriyFan?.mavzular || []).map((m) => <option key={m.topic_code} value={m.topic_code}>{m.mavzu}</option>)}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-3" role="group" aria-label={__kbUi("O‘rganish usuli")}>
        {[[true, "🏫 Dars xonasi"], [false, "💬 AI ustoz suhbati"]].map(([value, label]) => (
          <button key={label} type="button" onClick={() => setDarsXonasi(value)} aria-pressed={darsXonasi === value}
            className="px-3 py-2.5 rounded-xl text-xs font-semibold border"
            style={darsXonasi === value
              ? { backgroundColor: "#1E3A32", color: "#F2F0E6", borderColor: "#1E3A32" }
              : { backgroundColor: "#fff", color: "#5A5648", borderColor: "#E5E1D8" }}>
            {__kbUi(label)}
          </button>
        ))}
      </div>

      {darsXonasi && topicCode ? (
        <React.Suspense fallback={<div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>}>
          <DarsXonasi apiBase={API_BASE} token={token} topicCode={topicCode} fan={joriyFan?.fan || ""}
            grade={joriyMavzu?.grade || sozlama?.sinf || initialTarget?.grade || ""}
            jins={_ovozJinsiniTuzat(foydalanuvchi?.ovoz_jinsi || foydalanuvchi?.jins || "qiz")}
            learnerGender={foydalanuvchi?.jins || ""} learnerRole={loginAccountRole(foydalanuvchi)}
            onChat={() => setDarsXonasi(false)}
            onOpenTest={onOpenTest ? () => onOpenTest({ topic_code: topicCode, grade: joriyMavzu?.grade || sozlama?.sinf || initialTarget?.grade, subject: joriyFan?.fan }) : undefined}
            onOpenTopic={(code) => { const f = visibleSubjects.find((x) => x.mavzular.some((m) => m.topic_code === code)); if (f) { setFan(f.kalit); setTopicCode(code); } }} />
        </React.Suspense>
      ) : <>
      <div className="flex gap-1.5 overflow-x-auto pb-2 mb-2">
        {AI_USTOZ_REJIMLARI.map((r) => (
          <button key={r.kalit} onClick={() => rejimOzgar(r.kalit)}
            className="shrink-0 px-3 py-2 rounded-full text-xs font-semibold"
            style={rejim === r.kalit
              ? { backgroundColor: "#1B4B7A", color: "#fff" }
              : { backgroundColor: "#fff", color: "#5A5648", border: "1px solid #E5E1D8" }}>
            {__kbUi(r.emoji)} {__kbUi(r.nom)}
          </button>
        ))}
      </div>

      <div className="rounded-2xl bg-white border p-3.5 mb-3 min-h-[310px]" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        {xabarlar.length === 0 && (
          <div className="py-8 text-center">
            <div className="w-12 h-12 mx-auto rounded-full flex items-center justify-center text-2xl mb-3" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>🤖</div>
            <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{joriyMavzu?.mavzu || __kbUi("Mavzu tanlang")}</p>
            <p className="text-xs mb-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Men javobni darhol berib qo'ymayman — o'zingiz tushunib olishingizga yordam beraman.")}</p>
            <button onClick={() => yubor(AI_USTOZ_REJIMLARI.find((r) => r.kalit === rejim)?.boshlash)}
              disabled={!topicCode}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold text-white" style={{ backgroundColor: "#1B4B7A" }}>
              {__kbUi(AI_USTOZ_REJIMLARI.find((r) => r.kalit === rejim)?.emoji)}{__kbUi(" Boshlash")}</button>
          </div>
        )}

        <div className="space-y-3">
          {xabarlar.map((x, i) => (
            <div key={i}>
              {x.muallif === "oquvchi" ? (
                <div className="ml-8 rounded-2xl rounded-br-md px-3.5 py-3 text-sm text-white" style={{ backgroundColor: "#1B4B7A" }}>
                  {x.matn}
                </div>
              ) : x.muallif === "ai" ? (
                <div className="mr-4"><AiJavobBloklari javob={x.javob} onQuickReply={(reply) => yubor(reply)} /></div>
              ) : (
                <div className="rounded-xl p-3 text-sm" style={{ backgroundColor: "#FCEBEB", color: "#A32D2D" }}>{x.matn}</div>
              )}
            </div>
          ))}
          {yuborilmoqda && (
            <div className="flex items-center gap-2 text-xs p-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
              <Loader2 size={15} className="animate-spin" />{__kbUi(" Bazadagi bilimlardan javob tayyorlanmoqda…")}</div>
          )}
          <div ref={oxiriRef} />
        </div>
      </div>

      {xato && <p className="text-xs mb-2" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
      <div className="flex gap-2 sticky bottom-20 p-2 rounded-2xl z-10" style={{ background: "rgba(247,245,240,.96)", boxShadow: "0 -6px 18px -12px rgba(16,42,67,.35)", backdropFilter: "blur(6px)" }}>
        <textarea value={matn} onChange={(e) => setMatn(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); yubor(); } }}
          rows={2} placeholder={__kbUi("Savol yoki javobingizni yozing…")}
          className="flex-1 px-3.5 py-2.5 rounded-xl border text-sm bg-white resize-none"
          style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
        <button onClick={() => yubor()} disabled={!matn.trim() || yuborilmoqda}
          className="w-12 rounded-xl text-white flex items-center justify-center"
          style={{ backgroundColor: "#1B4B7A", opacity: !matn.trim() || yuborilmoqda ? 0.5 : 1 }}>
          <Send size={18} />
        </button>
      </div>
      </>}
    </div>
  );
}

const OCHIQ_DARS_METODIKALARI = [
  "Avtomatik",
  "5E (Engage–Explore–Explain–Elaborate–Evaluate)",
  "Muammoli ta'lim + I do–We do–You do",
  "PPP + kommunikativ yondashuv",
  "Loyiha asosida o'qitish",
  "Hamkorlikdagi ta'lim",
  "O'yinli va multisensor ta'lim",
];

function AiOchiqDarsKonstruktori({ token, onOrtga }) {
  useKbInterfaceLocale();
  const [sinf, setSinf] = useState("5");
  const [fan, setFan] = useState("Matematika");
  const [mavzu, setMavzu] = useState("");
  const [topicCode, setTopicCode] = useState("");
  const [katalog, setKatalog] = useState(null);
  const [maqsad, setMaqsad] = useState("");
  const [metodika, setMetodika] = useState("Avtomatik");
  const [jihozlar, setJihozlar] = useState("");
  const [sinfHajmi, setSinfHajmi] = useState(25);
  const [reja, setReja] = useState(null);
  const [darsId, setDarsId] = useState(null);
  const [yaratilmoqda, setYaratilmoqda] = useState(false);
  const [xato, setXato] = useState("");

  useEffect(() => {
    let bekor = false;
    fetch(`${API_BASE}/api/ai/pedagog/katalog?token=${encodeURIComponent(token)}&sinf=${encodeURIComponent(sinf)}`)
      .then(async (r) => {
        const d = await r.json();
        if (!r.ok) throw new Error(d.detail || "Kitob katalogi yuklanmadi");
        if (bekor) return;
        setKatalog(d);
        if (d.fanlar?.length > 0) {
          const birinchiFan = d.fanlar[0];
          const birinchiMavzu = birinchiFan.mavzular?.[0];
          setFan(birinchiFan.fan);
          setMavzu(birinchiMavzu?.mavzu || "");
          setTopicCode(birinchiMavzu?.topic_code || "");
        } else {
          setTopicCode("");
        }
      })
      .catch(() => { if (!bekor) setKatalog({ fanlar: [] }); });
    return () => { bekor = true; };
  }, [token, sinf]);

  const joriyFan = katalog?.fanlar?.find((f) => f.fan === fan);

  const katalogFanOzgar = (yangiFan) => {
    const topilgan = katalog?.fanlar?.find((f) => f.fan === yangiFan);
    const birinchi = topilgan?.mavzular?.[0];
    setFan(yangiFan);
    setMavzu(birinchi?.mavzu || "");
    setTopicCode(birinchi?.topic_code || "");
  };

  const katalogMavzuOzgar = (kod) => {
    const topilgan = joriyFan?.mavzular?.find((m) => m.topic_code === kod);
    setTopicCode(kod);
    setMavzu(topilgan?.mavzu || "");
  };

  const yarat = async () => {
    if (!fan.trim() || !mavzu.trim() || yaratilmoqda) return;
    setYaratilmoqda(true);
    setXato("");
    setReja(null);
    try {
      const res = await fetch(`${API_BASE}/api/ai/ochiq_dars/yarat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token, sinf, fan: fan.trim(), mavzu: mavzu.trim(),
          topic_code: topicCode || null,
          maqsad: maqsad.trim() || null,
          metodika,
          sinf_hajmi: Number(sinfHajmi) || 25,
          jihozlar: jihozlar.trim() || null,
          davomiylik_daq: 45,
        }),
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Ochiq dars yaratilmadi");
      setReja(d.reja);
      setDarsId(d.dars_id);
    } catch (e) {
      setXato(e.message);
    } finally {
      setYaratilmoqda(false);
    }
  };

  return (
    <div className="px-5 pt-6 pb-5">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
        <span className="w-7 h-7 rounded-xl flex items-center justify-center" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
          <ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} />
        </span><InterfaceText text={__kbUi("Ortga")}/></button>

      <div className="rounded-2xl p-4 mb-4 text-white" style={{ background: "linear-gradient(135deg,#6E45A1,#8B5FBF)" }}>
        <p className="text-xs opacity-80">{__kbUi("O'qituvchi uchun metodik konstruktor")}</p>
        <h1 className="text-xl font-bold mt-0.5">{__kbUi("🪄 45 daqiqalik ochiq dars")}</h1>
        <p className="text-xs mt-1 opacity-90">{__kbUi("Bazadagi bilim, misol va testlar asosida")}</p>
      </div>

      <div className="rounded-2xl bg-white border p-4 space-y-3 mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs font-medium block mb-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Sinf")}/></label>
            <select value={sinf} onChange={(e) => setSinf(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              {Array.from({ length: 11 }, (_, i) => i + 1).map((s) => <option key={s} value={String(s)}>{s}{__kbUi("-sinf")}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium block mb-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("O'quvchi soni")}</label>
            <input type="number" min="1" max="60" value={sinfHajmi} onChange={(e) => setSinfHajmi(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          </div>
        </div>
        <div>
          <label className="text-xs font-medium block mb-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Fan")}/></label>
          {katalog?.fanlar?.length > 0 ? (
            <select value={fan} onChange={(e) => katalogFanOzgar(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              {katalog.fanlar.map((f) => <option key={f.fan} value={f.fan}>{f.fan}</option>)}
            </select>
          ) : (
            <input value={fan} onChange={(e) => setFan(e.target.value)} placeholder={__kbUi("Masalan: Matematika")}
              className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          )}
        </div>
        <div>
          <label className="text-xs font-medium block mb-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Nashr qilingan kitob mavzusi")}</label>
          {joriyFan?.mavzular?.length > 0 ? (
            <select value={topicCode} onChange={(e) => katalogMavzuOzgar(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              {joriyFan.mavzular.map((m) => <option key={m.topic_code} value={m.topic_code}>{m.mavzu}</option>)}
            </select>
          ) : (
            <>
              <input value={mavzu} onChange={(e) => setMavzu(e.target.value)} placeholder={__kbUi("Masalan: 9 ga bo'linish alomati")}
                className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              <p className="text-[10px] mt-1" style={{ color: "#A16B22" }}>{__kbUi("Bu sinfda nashr qilingan Kitob miyasi topilmadi; admin avval import va nashr qilishi kerak.")}</p>
            </>
          )}
          {topicCode && (
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <span className="text-[11px]" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Kitobdagi tayyor dars:")}</span>
              {[["pdf", "⬇ PDF"], ["docx", "⬇ Word"]].map(([format, label]) => (
                <a key={format} href={lessonDownloadUrl(API_BASE, token, topicCode, format)} download
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold border" style={{ borderColor: "#C9D3CE", color: "#1E3A32", backgroundColor: "#fff" }}>{__kbUi(label)}</a>
              ))}
            </div>
          )}
        </div>
        <div>
          <label className="text-xs font-medium block mb-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("O'quv maqsadi")}</label>
          <textarea value={maqsad} onChange={(e) => setMaqsad(e.target.value)} rows={2}
            placeholder={__kbUi("Bo'sh qoldirilsa, AI bazadagi mavzuga qarab o'lchanadigan maqsad tuzadi.")}
            className="w-full px-3 py-2.5 rounded-xl border text-sm resize-none" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
        </div>
        <div>
          <label className="text-xs font-medium block mb-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Metodika")}</label>
          <select value={metodika} onChange={(e) => setMetodika(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            {OCHIQ_DARS_METODIKALARI.map((m) => <option key={m} value={m}>{__kbUi(m)}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs font-medium block mb-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Mavjud jihozlar")}</label>
          <input value={jihozlar} onChange={(e) => setJihozlar(e.target.value)}
            placeholder={__kbUi("Doska, proyektor, kartochka, laboratoriya jihozi…")}
            className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
        </div>
        <button onClick={yarat} disabled={yaratilmoqda || !fan.trim() || !mavzu.trim()}
          className="w-full py-3 rounded-xl font-semibold text-white flex items-center justify-center gap-2"
          style={{ backgroundColor: "#8B5FBF", opacity: yaratilmoqda || !fan.trim() || !mavzu.trim() ? 0.5 : 1 }}>
          {yaratilmoqda ? <><Loader2 size={17} className="animate-spin" />{__kbUi(" Metodik reja tuzilmoqda…")}</> : <>{__kbUi("🪄 Ochiq darsni yaratish")}</>}
        </button>
      </div>

      {xato && (
        <div className="rounded-xl p-3.5 mb-4 text-sm" style={{ backgroundColor: "#FCEBEB", color: "#A32D2D" }}>
          {__kbUi(xato)}
        </div>
      )}

      {reja && (
        <div id="ochiq-dars-reja" className="space-y-3">
          <div className="rounded-2xl bg-white border p-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <div className="flex justify-between gap-3">
              <div>
                <p className="text-xs mb-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Ochiq dars #")}{darsId}</p>
                <h2 className="text-lg font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{reja.sarlavha || reja.mavzu}</h2>
                <p className="text-xs mt-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{reja.sinf}{__kbUi("-sinf · ")}{reja.fan} · {reja.jami_daqiqa}{__kbUi(" daqiqa")}</p>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  <span className="text-[10px] px-2 py-1 rounded-full" style={{ backgroundColor: "#E7F4EC", color: "#25683B" }}>{__kbUi("✓ Tasdiqlangan kitob bazasi")}</span>
                  {reja.engine === "rules" && (
                    <span className="text-[10px] px-2 py-1 rounded-full" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("API kalitsiz")}</span>
                  )}
                </div>
              </div>
              <button onClick={() => window.print()} className="h-9 px-3 rounded-xl text-xs font-semibold"
                style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("🖨 Chop etish")}</button>
            </div>
          </div>

          <div className="rounded-2xl bg-white border p-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <h3 className="text-sm font-bold mb-2" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🎯 O'quv maqsadlari")}</h3>
            <ul className="space-y-1.5">
              {(reja.oquv_maqsadlari || []).map((m, i) => <li key={i} className="text-sm flex gap-2"><span>•</span><span>{m}</span></li>)}
            </ul>
            {(reja.metodikalar || []).length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-3">
                {reja.metodikalar.map((m, i) => <span key={i} className="text-[11px] px-2.5 py-1 rounded-full" style={{ backgroundColor: "#F3EEFA", color: "#6E45A1" }}>{m}</span>)}
              </div>
            )}
          </div>

          {(reja.bosqichlar || []).map((b, i) => (
            <div key={i} className="rounded-2xl bg-white border overflow-hidden" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div className="px-4 py-3 flex items-center justify-between" style={{ backgroundColor: i % 2 === 0 ? "#EAF1F7" : "#F3EEFA" }}>
                <h3 className="text-sm font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{b.emoji} {b.tartib}. {b.nomi}</h3>
                <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-white" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{b.daqiqa}{__kbUi(" daqiqa")}</span>
              </div>
              <div className="p-4 grid gap-3">
                <div><p className="text-[11px] font-bold mb-1" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("O'QITUVCHI HARAKATI")}</p><p className="text-sm whitespace-pre-line">{b.oqituvchi_harakati}</p></div>
                <div><p className="text-[11px] font-bold mb-1" style={{ color: "#3B6D11" }}>{__kbUi("O'QUVCHI HARAKATI")}</p><p className="text-sm whitespace-pre-line">{b.oquvchi_harakati}</p></div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-xl p-2.5" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}><b>{__kbUi("Metod:")}</b><br />{b.metod}</div>
                  <div className="rounded-xl p-2.5" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}><b>{__kbUi("Baholash:")}</b><br />{b.baholash}</div>
                </div>
              </div>
            </div>
          ))}

          {reja.differensial_yondashuv && (
            <div className="rounded-2xl bg-white border p-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <h3 className="text-sm font-bold mb-3">{__kbUi("🧩 Differensial yondashuv")}</h3>
              <p className="text-sm mb-2"><b>{__kbUi("Qo'llab-quvvatlash:")}</b> {reja.differensial_yondashuv.qollab_quvvatlash}</p>
              <p className="text-sm mb-2"><b>{__kbUi("Kuchli o'quvchi:")}</b> {reja.differensial_yondashuv.kuchli_oquvchi}</p>
              <p className="text-sm"><b>{__kbUi("Inklyuziv moslashuv:")}</b> {reja.differensial_yondashuv.inklyuziv_moslashuv}</p>
            </div>
          )}

          <div className="rounded-2xl p-4" style={{ backgroundColor: "#EAF3DE", color: "#2E5A24" }}>
            <p className="text-sm"><b>{__kbUi("🏠 Uy vazifasi:")}</b> {reja.uy_vazifasi}</p>
            <p className="text-sm mt-2"><b>{__kbUi("🏁 Refleksiya:")}</b> {reja.refleksiya}</p>
          </div>
          {(reja.sources || []).length > 0 && (
            <div className="rounded-2xl bg-white border p-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <h3 className="text-sm font-bold mb-2">{__kbUi("📚 Foydalanilgan manbalar")}</h3>
              {(reja.sources || []).map((s, i) => (
                <p key={`${s.source_code || "source"}-${s.page || i}`} className="text-xs py-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
                  {s.book || s.source_code || __kbUi("Kitob")}{s.page ? __kbUi(` · ${s.page}-bet`) : __kbUi("")}{s.year ? __kbUi(` · ${s.year}`) : __kbUi("")}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function AiTogarakRejaKonstruktori({ token, onOrtga }) {
  useKbInterfaceLocale();
  const [sinf, setSinf] = useState("5");
  const [katalog, setKatalog] = useState(null);
  const [fan, setFan] = useState("");
  const [topicCode, setTopicCode] = useState("");
  const [yonalish, setYonalish] = useState("Qiziqarli fan to'garagi");
  const [mashgulotSoni, setMashgulotSoni] = useState(12);
  const [reja, setReja] = useState(null);
  const [rejaId, setRejaId] = useState(null);
  const [yuklanmoqda, setYuklanmoqda] = useState(false);
  const [xato, setXato] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/ai/pedagog/katalog?token=${encodeURIComponent(token)}&sinf=${encodeURIComponent(sinf)}`)
      .then(async (r) => {
        const d = await r.json();
        if (!r.ok) throw new Error(d.detail || "Katalog yuklanmadi");
        setKatalog(d);
        const f = d.fanlar?.[0];
        setFan(f?.fan || "");
        setTopicCode(f?.mavzular?.[0]?.topic_code || "");
      })
      .catch((e) => { setKatalog({ fanlar: [] }); setXato(e.message); });
  }, [token, sinf]);

  const joriyFan = katalog?.fanlar?.find((f) => f.fan === fan);
  const fanOzgar = (value) => {
    const f = katalog?.fanlar?.find((x) => x.fan === value);
    setFan(value);
    setTopicCode(f?.mavzular?.[0]?.topic_code || "");
  };

  const yarat = async () => {
    if (!fan || !topicCode || yuklanmoqda) return;
    setYuklanmoqda(true);
    setXato("");
    setReja(null);
    try {
      const res = await fetch(`${API_BASE}/api/ai/togarak/yarat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token,
          sinf,
          fan,
          yonalish: yonalish.trim() || "Fan to'garagi",
          topic_codes: [topicCode],
          mashgulot_soni: Number(mashgulotSoni) || 12,
          davomiylik_daq: 45,
        }),
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "To'garak rejasi yaratilmadi");
      setReja(d.reja);
      setRejaId(d.reja_id);
    } catch (e) {
      setXato(e.message);
    } finally {
      setYuklanmoqda(false);
    }
  };

  return (
    <div className="px-5 pt-6 pb-5">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
        <span className="w-7 h-7 rounded-xl flex items-center justify-center" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
          <ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} />
        </span><InterfaceText text={__kbUi("Ortga")}/></button>

      <div className="rounded-2xl p-4 mb-4 text-white"
        style={{ background: "linear-gradient(135deg,#246D6D,#2D8B8B)" }}>
        <p className="text-xs opacity-80">{__kbUi("Nashr qilingan kitob miyasi asosida")}</p>
        <h1 className="text-xl font-bold mt-0.5">{__kbUi("🧭 AI To'garak konstruktori")}</h1>
        <p className="text-xs mt-1 opacity-90">{__kbUi("1–48 ta 45 daqiqalik mashg'ulot rejasini API kalitsiz tuzadi")}</p>
      </div>

      <div className="rounded-2xl bg-white border p-4 space-y-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs font-medium block mb-1"><InterfaceText text={__kbUi("Sinf")}/></label>
            <select value={sinf} onChange={(e) => setSinf(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              {Array.from({ length: 11 }, (_, i) => i + 1).map((s) => <option key={s} value={String(s)}>{s}{__kbUi("-sinf")}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium block mb-1">{__kbUi("Mashg'ulot soni")}</label>
            <input type="number" min="1" max="48" value={mashgulotSoni} onChange={(e) => setMashgulotSoni(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          </div>
        </div>
        <div>
          <label className="text-xs font-medium block mb-1">{__kbUi("Yo'nalish nomi")}</label>
          <input value={yonalish} onChange={(e) => setYonalish(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
        </div>
        <div>
          <label className="text-xs font-medium block mb-1"><InterfaceText text={__kbUi("Fan")}/></label>
          <select value={fan} onChange={(e) => fanOzgar(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            {(katalog?.fanlar || []).map((f) => <option key={f.fan} value={f.fan}>{f.fan}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs font-medium block mb-1">{__kbUi("Boshlang'ich mavzu")}</label>
          <select value={topicCode} onChange={(e) => setTopicCode(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            {(joriyFan?.mavzular || []).map((m) => <option key={m.topic_code} value={m.topic_code}>{m.mavzu}</option>)}
          </select>
          {!topicCode && <p className="text-[10px] mt-1" style={{ color: "#A16B22" }}>{__kbUi("Bu sinfda nashr qilingan kitob mavzusi yo'q.")}</p>}
        </div>
        <button onClick={yarat} disabled={!topicCode || yuklanmoqda}
          className="w-full py-3 rounded-xl font-semibold text-white flex items-center justify-center gap-2"
          style={{ backgroundColor: "#2D8B8B", opacity: !topicCode || yuklanmoqda ? .5 : 1 }}>
          {yuklanmoqda ? <><Loader2 size={17} className="animate-spin" />{__kbUi(" Reja tuzilmoqda…")}</> : __kbUi("🧭 To'garak rejasini yaratish")}
        </button>
      </div>

      {xato && <div className="rounded-xl p-3.5 mt-3 text-sm" style={{ backgroundColor: "#FCEBEB", color: "#A32D2D" }}>{__kbUi(xato)}</div>}

      {reja && (
        <div className="space-y-3 mt-4">
          <div className="rounded-2xl bg-white border p-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <p className="text-[10px]" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("To'garak rejasi #")}{rejaId}</p>
            <h2 className="font-bold mt-1">{reja.sarlavha}</h2>
            <div className="flex gap-1.5 mt-2">
              <span className="text-[10px] px-2 py-1 rounded-full" style={{ backgroundColor: "#E7F4EC", color: "#25683B" }}>{__kbUi("✓ Tasdiqlangan baza")}</span>
              <span className="text-[10px] px-2 py-1 rounded-full" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("API kalitsiz")}</span>
            </div>
          </div>
          {(reja.mashgulotlar || []).map((m) => (
            <div key={m.tartib} className="rounded-2xl bg-white border overflow-hidden" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div className="px-4 py-3" style={{ backgroundColor: "#EEF7F5" }}>
                <p className="text-[10px] font-bold" style={{ color: "#246D6D" }}>{m.tartib}{__kbUi("-MASHG'ULOT · ")}{reja.davomiylik_daq}{__kbUi(" DAQIQA")}</p>
                <h3 className="font-bold text-sm mt-0.5">{m.mavzu}</h3>
                <p className="text-xs mt-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{m.maqsad}</p>
              </div>
              <div className="p-4 space-y-2">
                {(m.bosqichlar || []).map((b) => (
                  <div key={b.tartib} className="flex gap-3 text-xs">
                    <span className="font-bold w-14 shrink-0" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{b.daqiqa}{__kbUi(" daq")}</span>
                    <span><b>{b.nomi}:</b> {b.faoliyat}</span>
                  </div>
                ))}
                {m.mustaqil_vazifa && <p className="text-xs rounded-xl p-2.5 mt-2" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}><b>{__kbUi("Mustaqil vazifa:")}</b> {m.mustaqil_vazifa}</p>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AiYordamchiBolimi({ token, onOrtga }) {
  useKbInterfaceLocale();
  const [suhbat, setSuhbat] = useState([]); // [{savol, javob, xato}]
  const [savol, setSavol] = useState("");
  const [yuborilmoqda, setYuborilmoqda] = useState(false);
  const oxiriRef = useRef(null);

  useEffect(() => {
    oxiriRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [suhbat]);

  const yubor = async () => {
    if (!savol.trim() || yuborilmoqda) return;
    const soralganSavol = savol.trim();
    setSavol("");
    setSuhbat((prev) => [...prev, { savol: soralganSavol, javob: null, xato: null }]);
    setYuborilmoqda(true);
    try {
      const res = await fetch(`${API_BASE}/api/ai/sorash`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, savol: soralganSavol }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setSuhbat((prev) => prev.map((s, i) => (i === prev.length - 1 ? { ...s, javob: data.javob } : s)));
    } catch (e) {
      setSuhbat((prev) => prev.map((s, i) => (i === prev.length - 1 ? { ...s, xato: e.message } : s)));
    } finally {
      setYuborilmoqda(false);
    }
  };

  return (
    <div className="px-5 pt-6 pb-4 flex flex-col" style={{ minHeight: "80vh" }}>
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Ortga")}/></button>
      <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🤖 AI Yordamchi")}</h1>
      <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Masalan: \"2-A sinfning bugungi davomati qanday?\" yoki \"Farzandim qaysi fandan orqada qolmoqda?\"")}</p>

      <div className="flex-1 space-y-3 mb-4">
        {suhbat.length === 0 && (
          <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Savolingizni pastdan yozing.")}</p>
          </div>
        )}
        {suhbat.map((s, i) => (
          <div key={i}>
            <div className="rounded-2xl rounded-br-md p-3.5 mb-2 ml-8" style={{ backgroundColor: "#1B4B7A" }}>
              <p className="text-sm text-white">{s.savol}</p>
            </div>
            <div className="rounded-2xl rounded-bl-md p-3.5 mr-8 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              {s.xato ? (
                <p className="text-sm" style={{ color: "#B0553A" }}>{__kbUi(s.xato)}</p>
              ) : s.javob ? (
                <p className="text-sm whitespace-pre-line" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{s.javob}</p>
              ) : (
                <Loader2 size={16} className="animate-spin" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} />
              )}
            </div>
          </div>
        ))}
        <div ref={oxiriRef} />
      </div>

      <div className="flex gap-2 sticky bottom-4">
        <input type="text" value={savol} onChange={(e) => setSavol(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") yubor(); }}
          placeholder={__kbUi("Savolingizni yozing...")}
          className="flex-1 px-3.5 py-3 rounded-xl border text-sm bg-white" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
        <button onClick={yubor} disabled={yuborilmoqda || !savol.trim()}
          className="px-5 py-3 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: yuborilmoqda || !savol.trim() ? 0.5 : 1 }}>
          →
        </button>
      </div>
    </div>
  );
}

function PsixologQidiruv({ token, maktabId, onOrtga }) {
  useKbInterfaceLocale();
  const [tanlanganOquvchi, setTanlanganOquvchi] = useState(null);

  if (tanlanganOquvchi) {
    return <OquvchiProfili token={token} userId={tanlanganOquvchi.user_id} onOrtga={() => setTanlanganOquvchi(null)} />;
  }

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("To'garaklarim")}</button>
      <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🧠 Psixolog")}</h1>
      <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("O'quvchini qidirib, uning kuzatuv yozuvlarini ko'ring yoki yangi qo'shing.")}</p>
      <MaktabOdamQidiruvi token={token} maktabId={maktabId} tanlanganOdam={null} onTanla={setTanlanganOquvchi} />
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// TOPIK MAVZU REJASI — o'qituvchi BIR MARTA yaratadigan, tartibli
// mavzular ketma-ketligi, keyin bir nechta to'garakda qayta
// ishlatiladigan "dastur".
// ═══════════════════════════════════════════════════════════
function RejaDetali({ token, rejaId, onOrtga }) {
  useKbInterfaceLocale();
  const [reja, setReja] = useState(null);
  const [qatorlar, setQatorlar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");

  const [qidiruvOchiq, setQidiruvOchiq] = useState(false);
  const [qidiruv, setQidiruv] = useState("");
  const [qidiruvNatijalari, setQidiruvNatijalari] = useState(null);
  const [qidirilmoqda, setQidirilmoqda] = useState(false);
  const [qidiruvXato, setQidiruvXato] = useState("");

  const [yangiMavzuOchiq, setYangiMavzuOchiq] = useState(false);
  const [yangiMavzuNomi, setYangiMavzuNomi] = useState("");
  const [yangiMavzuBob, setYangiMavzuBob] = useState("");
  const [yangiMavzuYaratilmoqda, setYangiMavzuYaratilmoqda] = useState(false);
  const [kopMavzuRejimi, setKopMavzuRejimi] = useState(false);
  const [kopMavzuMatni, setKopMavzuMatni] = useState("");
  const [kopMavzuYaratilmoqda, setKopMavzuYaratilmoqda] = useState(false);
  const [kopMavzuProgress, setKopMavzuProgress] = useState("");

  const yukla = () => {
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/oqituvchi/reja_korish?token=${encodeURIComponent(token)}&reja_id=${rejaId}`)
      .then(async (r) => {
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.detail || `Server xatosi (${r.status})`);
        return d;
      })
      .then((d) => { setReja(d.reja); setQatorlar(d.qatorlar || []); setXato(""); setYuklanmoqda(false); })
      .catch((e) => { setXato(e.message || "Yuklab bo'lmadi"); setYuklanmoqda(false); });
  };
  useEffect(yukla, [token, rejaId]);

  useEffect(() => {
    if (!qidiruvOchiq) return;
    setQidirilmoqda(true);
    const kechiktirish = setTimeout(() => {
      fetch(`${API_BASE}/api/oqituvchi/reja_mavzu_qidir?token=${encodeURIComponent(token)}&reja_id=${rejaId}${qidiruv.trim() ? `&qidiruv=${encodeURIComponent(qidiruv.trim())}` : ""}`)
        .then(async (r) => {
          const d = await r.json().catch(() => ({}));
          if (!r.ok) throw new Error(d.detail || `Server xatosi (${r.status})`);
          return d;
        })
        .then((d) => { setQidiruvNatijalari(d.mavzular || []); setQidiruvXato(""); setQidirilmoqda(false); })
        .catch((e) => { setQidiruvXato(e.message || "Yuklab bo'lmadi"); setQidirilmoqda(false); });
    }, 350);
    return () => clearTimeout(kechiktirish);
  }, [qidiruv, qidiruvOchiq, token, rejaId]);

  const [belgilanganKodlar, setBelgilanganKodlar] = useState({}); // {topic_code: true}
  const kodBelgila = (topicCode) => {
    setBelgilanganKodlar((prev) => ({ ...prev, [topicCode]: !prev[topicCode] }));
  };

  const [tanlanganlarniQoshishYuklanmoqda, setTanlanganlarniQoshishYuklanmoqda] = useState(false);
  const tanlanganlarniQoshish = async () => {
    const kodlar = Object.keys(belgilanganKodlar).filter((k) => belgilanganKodlar[k]);
    if (kodlar.length === 0) return;
    setTanlanganlarniQoshishYuklanmoqda(true);
    try {
      for (const kod of kodlar) {
        // eslint-disable-next-line no-await-in-loop
        await fetch(`${API_BASE}/api/oqituvchi/reja_mavzu_qosh`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token, reja_id: rejaId, topic_code: kod }),
        });
      }
      setBelgilanganKodlar({});
      yukla();
    } finally { setTanlanganlarniQoshishYuklanmoqda(false); }
  };

  const yangiMavzuYarat = async () => {
    if (!yangiMavzuNomi.trim()) { setXato("Mavzu nomini kiriting"); return; }
    setYangiMavzuYaratilmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/reja_yangi_mavzu_yarat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, reja_id: rejaId, nomi: yangiMavzuNomi.trim(), bob: yangiMavzuBob.trim() || undefined }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setYangiMavzuNomi(""); setYangiMavzuBob(""); setYangiMavzuOchiq(false);
      yukla();
    } catch (e) { setXato(e.message); } finally { setYangiMavzuYaratilmoqda(false); }
  };

  const kopMavzuYarat = async () => {
    const nomlar = kopMavzuMatni.split("\n").map((s) => s.trim()).filter(Boolean);
    if (nomlar.length === 0) { setXato("Kamida bitta mavzu nomi yozing"); return; }
    setKopMavzuYaratilmoqda(true); setXato("");
    try {
      for (let i = 0; i < nomlar.length; i++) {
        setKopMavzuProgress(`${i + 1} / ${nomlar.length}: ${nomlar[i]}`);
        // eslint-disable-next-line no-await-in-loop
        const res = await fetch(`${API_BASE}/api/oqituvchi/reja_yangi_mavzu_yarat`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token, reja_id: rejaId, nomi: nomlar[i] }),
        });
        // eslint-disable-next-line no-await-in-loop
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(`"${nomlar[i]}" qo'shilmadi: ${data.detail || "xato"}`);
      }
      setKopMavzuMatni(""); setKopMavzuRejimi(false); setYangiMavzuOchiq(false);
      yukla();
    } catch (e) { setXato(e.message); } finally { setKopMavzuYaratilmoqda(false); setKopMavzuProgress(""); }
  };

  const olibTashla = async (qatorId) => {
    await fetch(`${API_BASE}/api/oqituvchi/reja_mavzu_ochir?token=${encodeURIComponent(token)}&reja_id=${rejaId}&qator_id=${qatorId}`, { method: "DELETE" });
    yukla();
  };

  const surish = async (qatorId, yonalish) => {
    await fetch(`${API_BASE}/api/oqituvchi/reja_qator_surish`, {
      method: "PUT", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, reja_id: rejaId, qator_id: qatorId, yonalish }),
    });
    yukla();
  };

  if (yuklanmoqda) {
    return <div className="px-5 pt-16 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>;
  }

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("Rejalarim")}</button>
      <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>📋 {reja?.nomi}</h1>
      <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{reja?.sinf}-{reja?.fan} · {qatorlar.length}{__kbUi(" ta mavzu, tartib bilan")}</p>

      <div className="flex gap-2 mb-4">
        <button onClick={() => { setYangiMavzuOchiq(!yangiMavzuOchiq); setQidiruvOchiq(false); }}
          className="flex-1 text-xs font-semibold px-3 py-2 rounded-lg" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
          {yangiMavzuOchiq ? __kbUi("✕ Yopish") : __kbUi("✏️ Yangi mavzu")}
        </button>
        <button onClick={() => { setQidiruvOchiq(!qidiruvOchiq); setQidiruv(""); setQidiruvNatijalari(null); setYangiMavzuOchiq(false); setBelgilanganKodlar({}); }}
          className="flex-1 text-xs font-semibold px-3 py-2 rounded-lg" style={{ backgroundColor: "#1B4B7A", color: "#fff" }}>
          {qidiruvOchiq ? __kbUi("✕ Yopish") : __kbUi("+ Mavzu qo'shish")}
        </button>
      </div>

      {yangiMavzuOchiq && (
        <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Milliy bazada mos mavzu topilmasa — shu yerda nomini yozib, o'zingiz qo'shing.")}</p>
          <div className="flex gap-1.5 mb-3">
            <button type="button" onClick={() => setKopMavzuRejimi(false)}
              className="flex-1 py-2 rounded-lg text-xs font-semibold"
              style={!kopMavzuRejimi ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>{__kbUi("Bittalab")}</button>
            <button type="button" onClick={() => setKopMavzuRejimi(true)}
              className="flex-1 py-2 rounded-lg text-xs font-semibold"
              style={kopMavzuRejimi ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>{__kbUi("Bir nechtasini birdan")}</button>
          </div>

          {kopMavzuRejimi ? (
            <>
              <p className="text-xs mb-2" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Har bir mavzuni YANGI qatorga yozing — tartib bilan qo'shiladi.")}</p>
              <textarea value={kopMavzuMatni} onChange={(e) => setKopMavzuMatni(e.target.value)}
                placeholder={__kbUi("1-mavzu nomi\n2-mavzu nomi\n3-mavzu nomi\n...")} rows={8}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              <button onClick={kopMavzuYarat} disabled={kopMavzuYaratilmoqda || !kopMavzuMatni.trim()}
                className="w-full py-3 rounded-xl font-semibold text-white text-sm flex items-center justify-center gap-2"
                style={{ backgroundColor: "#1B4B7A", opacity: (kopMavzuYaratilmoqda || !kopMavzuMatni.trim()) ? 0.6 : 1 }}>
                {kopMavzuYaratilmoqda
                  ? <><Loader2 size={16} className="animate-spin" /> {kopMavzuProgress}</>
                  : __kbUi(`+ Barchasini qo'shish (${kopMavzuMatni.split("\n").map((s) => s.trim()).filter(Boolean).length} ta)`)}
              </button>
            </>
          ) : (
            <>
              <input type="text" value={yangiMavzuBob} onChange={(e) => setYangiMavzuBob(e.target.value)}
                placeholder={__kbUi("Bob nomi (ixtiyoriy)")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              <input type="text" value={yangiMavzuNomi} onChange={(e) => setYangiMavzuNomi(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && yangiMavzuYarat()}
                placeholder={__kbUi("Mavzu nomi")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              <button onClick={yangiMavzuYarat} disabled={yangiMavzuYaratilmoqda || !yangiMavzuNomi.trim()}
                className="w-full py-3 rounded-xl font-semibold text-white text-sm flex items-center justify-center gap-2"
                style={{ backgroundColor: "#1B4B7A", opacity: (yangiMavzuYaratilmoqda || !yangiMavzuNomi.trim()) ? 0.6 : 1 }}>
                {yangiMavzuYaratilmoqda ? <Loader2 size={16} className="animate-spin" /> : __kbUi("+ Ketma-ketlikka qo'shish")}
              </button>
            </>
          )}
        </div>
      )}

      {qidiruvOchiq && (
        <div className="rounded-2xl p-4 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <input type="text" value={qidiruv} onChange={(e) => { setQidiruv(e.target.value); setBelgilanganKodlar({}); }} placeholder={__kbUi("Mavzu nomi bo'yicha qidirish (bo'sh — reja sinf/fani)")}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          {qidirilmoqda ? (
            <div className="py-4 text-center"><Loader2 size={18} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
          ) : qidiruvXato ? (
            <p className="text-xs font-medium" style={{ color: "#A32D2D" }}>⚠️ {__kbUi(qidiruvXato)}</p>
          ) : (
            <>
              {(qidiruvNatijalari || []).some((m) => !qatorlar.some((q) => q.topic_code === m.topic_code)) && (
                <button onClick={() => {
                    const qoshilmaganlar = (qidiruvNatijalari || []).filter((m) => !qatorlar.some((q) => q.topic_code === m.topic_code));
                    const hammasiBelgilangan = qoshilmaganlar.every((m) => belgilanganKodlar[m.topic_code]);
                    setBelgilanganKodlar(Object.fromEntries(qoshilmaganlar.map((m) => [m.topic_code, !hammasiBelgilangan])));
                  }}
                  className="text-xs font-medium mb-2" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
                  {(qidiruvNatijalari || []).filter((m) => !qatorlar.some((q) => q.topic_code === m.topic_code)).every((m) => belgilanganKodlar[m.topic_code])
                    ? __kbUi("Hech birini belgilamaslik") : __kbUi("Barchasini belgilash")}
                </button>
              )}
              <div className="space-y-1.5 max-h-64 overflow-y-auto mb-3">
                {(qidiruvNatijalari || []).map((m) => {
                  const qoshilganmi = qatorlar.some((q) => q.topic_code === m.topic_code);
                  return (
                    <label key={m.topic_code} className="flex items-center gap-2.5 rounded-lg p-2 cursor-pointer"
                      style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", opacity: qoshilganmi ? 0.6 : 1 }}>
                      <input type="checkbox" checked={qoshilganmi || !!belgilanganKodlar[m.topic_code]} disabled={qoshilganmi}
                        onChange={() => kodBelgila(m.topic_code)} />
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-medium truncate" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(topicName(m))}</p>
                        <p className="text-xs truncate" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{m.subject_name} · {m.grade}{__kbUi("-sinf ")}{m.bob_name ? __kbUi(`· ${m.bob_name}`) : __kbUi("")}</p>
                      </div>
                      {qoshilganmi && <span className="text-xs font-semibold shrink-0" style={{ color: "#3B6D11" }}>{__kbUi("✓ Qo'shilgan")}</span>}
                    </label>
                  );
                })}
              {(qidiruvNatijalari || []).length === 0 && <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hech narsa topilmadi.")}</p>}
              </div>
              {Object.values(belgilanganKodlar).some(Boolean) && (
                <button onClick={tanlanganlarniQoshish} disabled={tanlanganlarniQoshishYuklanmoqda}
                  className="w-full py-2.5 rounded-xl font-semibold text-sm flex items-center justify-center gap-2"
                  style={{ backgroundColor: "#1B4B7A", color: "#fff", opacity: tanlanganlarniQoshishYuklanmoqda ? 0.7 : 1 }}>
                  {tanlanganlarniQoshishYuklanmoqda ? <Loader2 size={16} className="animate-spin" /> :
                    __kbUi(`+ Tanlanganlarni qo'shish (${Object.values(belgilanganKodlar).filter(Boolean).length} ta)`)}
                </button>
              )}
            </>
          )}
        </div>
      )}

      {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}

      {qatorlar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali mavzu qo'shilmagan. Yuqoridagi tugmalardan birini bosing.")}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {qatorlar.map((q, i) => (
            <div key={q.qator_id} className="rounded-xl p-3 bg-white border flex items-center gap-2.5" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi(formatTopicTitle(i, q))}</p>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <button onClick={() => surish(q.qator_id, "yuqori")} disabled={i === 0}
                  className="w-7 h-7 rounded-lg flex items-center justify-center text-sm" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: i === 0 ? "#C4BFAF" : "#1B4B7A" }}>↑</button>
                <button onClick={() => surish(q.qator_id, "pastga")} disabled={i === qatorlar.length - 1}
                  className="w-7 h-7 rounded-lg flex items-center justify-center text-sm" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: i === qatorlar.length - 1 ? "#C4BFAF" : "#1B4B7A" }}>↓</button>
                <button onClick={() => olibTashla(q.qator_id)} className="w-7 h-7 rounded-lg flex items-center justify-center text-sm" style={{ backgroundColor: "#FCEBEB", color: "#A32D2D" }}>✕</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function RejalarimBolimi({ token, onOrtga }) {
  useKbInterfaceLocale();
  const [rejalar, setRejalar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");
  const [tanlanganRejaId, setTanlanganRejaId] = useState(null);

  const [formOchiq, setFormOchiq] = useState(false);
  const [yangiNomi, setYangiNomi] = useState("");
  const [yangiSinf, setYangiSinf] = useState("");
  const [yangiMaxsusSinf, setYangiMaxsusSinf] = useState(false);
  const [yangiSinfTuri, setYangiSinfTuri] = useState("guruh"); // "guruh" (bog'cha) | "grupa" (universitet/markaz)
  const [yangiSinfMatni, setYangiSinfMatni] = useState("");
  const [meningSinflarim, setMeningSinflarim] = useState([]); // avval o'zi yozgan maxsus sinflar — qayta yozib adashmasin
  const [yangiFanTanlash, setYangiFanTanlash] = useState(true); // true=ro'yxatdan, false=o'zi yozadi
  const [yangiFan, setYangiFan] = useState("");
  const [yangiFanMatni, setYangiFanMatni] = useState("");
  const [meningFanlarim, setMeningFanlarim] = useState([]); // avval o'zi yozgan fanlar — qayta yozib adashmasin
  const [yangiMavzular, setYangiMavzular] = useState("");
  const [yaratilmoqda, setYaratilmoqda] = useState(false);
  const [yaratishProgress, setYaratishProgress] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/oqituvchi/mening_fanlarim?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => setMeningFanlarim(d.fanlar || []))
      .catch(() => {});
    fetch(`${API_BASE}/api/oqituvchi/mening_maxsus_sinflarim?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => setMeningSinflarim(d.sinflar || []))
      .catch(() => {});
  }, [token]);

  const yukla = () => {
    setYuklanmoqda(true);
    fetch(`${API_BASE}/api/oqituvchi/rejalarim?token=${encodeURIComponent(token)}`)
      .then(async (r) => {
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.detail || `Server xatosi (${r.status})`);
        return d;
      })
      .then((d) => { setRejalar(d.rejalar || []); setXato(""); setYuklanmoqda(false); })
      .catch((e) => { setXato(e.message || "Yuklab bo'lmadi"); setYuklanmoqda(false); });
  };
  useEffect(yukla, [token]);

  const rejaYarat = async () => {
    const sinfQiymati = yangiMaxsusSinf ? yangiSinfMatni.trim() : yangiSinf;
    const fanQiymati = yangiFanTanlash ? yangiFan : yangiFanMatni.trim();
    if (!yangiNomi.trim()) { setXato("Reja nomini kiriting"); return; }
    if (!sinfQiymati) { setXato("Sinfni tanlang"); return; }
    if (!fanQiymati) { setXato("Fanni tanlang yoki yozing"); return; }
    if (fanQiymati.trim().split(/\s+/).length > 1) { setXato("Fan nomi bitta so'zdan oshmasligi kerak"); return; }
    const mavzuNomlari = yangiMavzular.split("\n").map((s) => s.trim()).filter(Boolean);
    setYaratilmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/reja_yarat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token,
          nomi: yangiNomi.trim(),
          sinf: sinfQiymati,
          fan: fanQiymati.trim(),
          guruh_turi: yangiMaxsusSinf ? yangiSinfTuri : "sinf",
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      const rejaId = data.reja_id;
      for (let i = 0; i < mavzuNomlari.length; i++) {
        setYaratishProgress(`Mavzular qo'shilmoqda: ${i + 1} / ${mavzuNomlari.length}`);
        // eslint-disable-next-line no-await-in-loop
        const mres = await fetch(`${API_BASE}/api/oqituvchi/reja_yangi_mavzu_yarat`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token, reja_id: rejaId, nomi: mavzuNomlari[i] }),
        });
        // eslint-disable-next-line no-await-in-loop
        if (!mres.ok) { const md = await mres.json().catch(() => ({})); throw new Error(`"${mavzuNomlari[i]}" qo'shilmadi: ${md.detail || "xato"}`); }
      }
      setYangiNomi(""); setYangiSinf(""); setYangiMaxsusSinf(false); setYangiSinfMatni("");
      setYangiFan(""); setYangiFanMatni(""); setYangiMavzular(""); setFormOchiq(false);
      setTanlanganRejaId(rejaId);
    } catch (e) { setXato(e.message); } finally { setYaratilmoqda(false); setYaratishProgress(""); }
  };

  if (tanlanganRejaId) {
    return <RejaDetali token={token} rejaId={tanlanganRejaId} onOrtga={() => { setTanlanganRejaId(null); yukla(); }} />;
  }

  return (
    <div className="px-5 pt-6 pb-4">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span>{__kbUi("To'garaklarim")}</button>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-xl font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📋 Rejalarim")}</h1>
        <button onClick={() => setFormOchiq(!formOchiq)} className="text-xs font-semibold px-3.5 py-1.5 rounded-full" style={{ backgroundColor: "#1B4B7A", color: "#fff" }}>
          {formOchiq ? __kbUi("✕ Yopish") : __kbUi("+ Yangi reja")}
        </button>
      </div>
      <p className="text-xs mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bir marta tartibli mavzular ketma-ketligini tuzib qo'ying — keyin bir nechta to'garak guruhida qayta ishlatasiz.")}</p>

      {formOchiq && (
        <div className="rounded-2xl p-5 bg-white border mb-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Reja nomi")}</label>
          <input type="text" value={yangiNomi} onChange={(e) => setYangiNomi(e.target.value)}
            placeholder={__kbUi("masalan: 9-sinf Algebra dasturi")}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Sinf / Guruh / Grupa / Repetitor")}</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 rounded-2xl p-1 gap-0.5 mb-2" style={{ backgroundColor: "#F0EDE5" }}>
            <button type="button" onClick={() => { setYangiMaxsusSinf(false); setYangiSinfMatni(""); }}
              className="flex-1 py-2 rounded-full text-xs font-semibold"
              style={!yangiMaxsusSinf ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>🏫 <InterfaceText text={__kbUi("Sinf")}/></button>
            <button type="button" onClick={() => { setYangiMaxsusSinf(true); setYangiSinfTuri("guruh"); setYangiSinf(""); }}
              className="flex-1 py-2 rounded-full text-xs font-semibold"
              style={(yangiMaxsusSinf && yangiSinfTuri === "guruh") ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>🧸 <InterfaceText text={__kbUi("Guruh")}/></button>
            <button type="button" onClick={() => { setYangiMaxsusSinf(true); setYangiSinfTuri("grupa"); setYangiSinf(""); }}
              className="flex-1 py-2 rounded-full text-xs font-semibold"
              style={(yangiMaxsusSinf && yangiSinfTuri === "grupa") ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>{__kbUi("🎓 Grupa")}</button>
            <button type="button" onClick={() => { setYangiMaxsusSinf(true); setYangiSinfTuri("repetitor"); setYangiSinf(""); }}
              className="flex-1 py-2 rounded-full text-xs font-semibold"
              style={(yangiMaxsusSinf && yangiSinfTuri === "repetitor") ? { backgroundColor: "#fff", color: "#28735A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>{__kbUi("🧑‍🏫 Repetitor")}</button>
          </div>
          {!yangiMaxsusSinf ? (
            <div className="grid grid-cols-6 gap-1.5 mb-3">
              {Array.from({ length: 11 }, (_, i) => String(i + 1)).map((n) => (
                <button key={n} type="button" onClick={() => setYangiSinf(n)}
                  className="py-2 rounded-lg border text-sm font-semibold text-center"
                  style={{
                    borderColor: yangiSinf === n ? "#1B4B7A" : "#E5E1D8",
                    backgroundColor: yangiSinf === n ? "#1B4B7A" : "#FFFFFF",
                    color: yangiSinf === n ? "#FFFFFF" : "#5A5648",
                  }}>
                  {n}
                </button>
              ))}
            </div>
          ) : (
            <>
              {meningSinflarim.length > 0 && (
                <>
                  <p className="text-xs mb-1.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Avval o'zingiz yozgan ")}{__kbUi(groupTypeLabel(yangiSinfTuri).toLowerCase())}:</p>
                  <div className="flex gap-1.5 flex-wrap mb-2">
                    {meningSinflarim.map((s) => (
                      <button key={s} type="button" onClick={() => setYangiSinfMatni(s)}
                        className="px-3 py-1.5 rounded-lg border text-xs font-medium"
                        style={{
                          borderColor: yangiSinfMatni === s ? "#1B4B7A" : "#E5E1D8",
                          backgroundColor: yangiSinfMatni === s ? "#1B4B7A" : "#FFFFFF",
                          color: yangiSinfMatni === s ? "#FFFFFF" : "#5A5648",
                        }}>
                        {s}
                      </button>
                    ))}
                  </div>
                </>
              )}
              <input type="text" value={yangiSinfMatni} onChange={(e) => setYangiSinfMatni(e.target.value)}
                placeholder={yangiSinfTuri === "grupa" ? __kbUi("masalan: 205-guruh, 3-kurs") : yangiSinfTuri === "repetitor" ? __kbUi("masalan: IELTS B2 kechki guruh") : __kbUi("masalan: Kichik guruh, Abituriyent")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            </>
          )}

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Fan")}/></label>
          {yangiFanTanlash ? (
            <>
              <div className="flex gap-1.5 flex-wrap mb-2">
                {BARCHA_MAKTAB_FANLARI.map((f) => (
                  <button key={f} type="button" onClick={() => setYangiFan(f)}
                    className="px-3 py-2 rounded-lg border text-sm font-medium"
                    style={{
                      borderColor: yangiFan === f ? "#1B4B7A" : "#E5E1D8",
                      backgroundColor: yangiFan === f ? "#1B4B7A" : "#FFFFFF",
                      color: yangiFan === f ? "#FFFFFF" : "#5A5648",
                    }}>
                    {__kbUi(f)}
                  </button>
                ))}
              </div>
              <button type="button" onClick={() => { setYangiFanTanlash(false); setYangiFan(""); }}
                className="text-xs font-medium mb-3" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Ro'yxatda yo'q fan — o'zim yozaman →")}</button>
            </>
          ) : (
            <>
              {meningFanlarim.length > 0 && (
                <>
                  <p className="text-xs mb-1.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Avval o'zingiz yozgan fanlar:")}</p>
                  <div className="flex gap-1.5 flex-wrap mb-2">
                    {meningFanlarim.map((f) => (
                      <button key={f} type="button" onClick={() => setYangiFanMatni(f)}
                        className="px-3 py-1.5 rounded-lg border text-xs font-medium"
                        style={{
                          borderColor: yangiFanMatni === f ? "#1B4B7A" : "#E5E1D8",
                          backgroundColor: yangiFanMatni === f ? "#1B4B7A" : "#FFFFFF",
                          color: yangiFanMatni === f ? "#FFFFFF" : "#5A5648",
                        }}>
                        {f}
                      </button>
                    ))}
                  </div>
                </>
              )}
              <input type="text" value={yangiFanMatni} onChange={(e) => setYangiFanMatni(e.target.value)}
                placeholder={__kbUi("Bitta so'z, masalan: Robototexnika")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              <button type="button" onClick={() => { setYangiFanTanlash(true); setYangiFanMatni(""); }}
                className="text-xs font-medium mb-3" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("← Ro'yxatdan tanlashga qaytish")}</button>
            </>
          )}

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Mavzular (har birini yangi qatorga yozing — tartib bilan qo'shiladi, ixtiyoriy)")}</label>
          <textarea value={yangiMavzular} onChange={(e) => setYangiMavzular(e.target.value)}
            placeholder={__kbUi("1-mavzu nomi\n2-mavzu nomi\n3-mavzu nomi\n...")} rows={8}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3 font-mono" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />

          {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
          <button onClick={rejaYarat} disabled={yaratilmoqda}
            className="w-full py-3 rounded-xl font-semibold text-white text-sm flex items-center justify-center gap-2"
            style={{ backgroundColor: "#1B4B7A", opacity: yaratilmoqda ? 0.7 : 1 }}>
            {yaratilmoqda
              ? <><Loader2 size={16} className="animate-spin" /> {yaratishProgress || __kbUi("Yaratilmoqda...")}</>
              : __kbUi("Rejani yaratish")}
          </button>
        </div>
      )}

      {!formOchiq && xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}

      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : rejalar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali reja yaratilmagan.")}</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {rejalar.map((r) => (
            <button key={r.id} onClick={() => setTanlanganRejaId(r.id)}
              className="w-full text-left rounded-xl p-4 bg-white border flex items-center justify-between" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div>
                <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{r.nomi}</p>
                <p className="text-xs mt-0.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi(groupTypeLabel(r.guruh_turi))} · {r.sinf} · {r.fan} · {r.mavzu_soni}{__kbUi(" ta mavzu")}</p>
              </div>
              <ChevronRight size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

async function muassasaV17Sorov(path, token, options = {}) {
  const response = await fetch(`${API_BASE}/api/muassasa-v17${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
  });
  const raw = await response.text();
  let data = {};
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    data = raw ? { detail: raw } : {};
  }
  if (!response.ok) {
    const error = new Error(organizationTrialErrorMessage(data));
    error.status = response.status;
    error.payload = data;
    throw error;
  }
  return data;
}

function MuassasaV17ReadOnlyBanner({ organization }) {
  useKbInterfaceLocale();
  if (!organizationIsReadOnly(organization)) return null;
  return (
    <div className="org-trial-readonly-banner" role="status">
      <KeyRound size={19} />
      <div>
        <b>{__kbUi("Faqat ko'rish rejimi")}</b>
        <p>{__kbUi("30 kunlik sinov tugagan. Barcha ma'lumotlar saqlangan; tahrirlash bir martalik faollashtirishdan keyin ochiladi.")}</p>
      </div>
    </div>
  );
}

function MuassasaV17Markazi({ token, onBack, onWorkspaceOpen }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [jarayon, setJarayon] = useState("");
  const [xato, setXato] = useState("");
  const [muvaffaqiyat, setMuvaffaqiyat] = useState("");
  const [tashkilotlar, setTashkilotlar] = useState([]);
  const [hamyon, setHamyon] = useState({ balance_uzs: 0 });
  const [sinovKunlari, setSinovKunlari] = useState(ORGANIZATION_TRIAL_DAYS);
  const [faollashtirishNarxi, setFaollashtirishNarxi] = useState(ORGANIZATION_ACTIVATION_PRICE_UZS);
  const [qadam, setQadam] = useState("royxat");
  const [yangiTuri, setYangiTuri] = useState("school");
  const [yangiNomi, setYangiNomi] = useState("");
  const [sinovTasdiqlandi, setSinovTasdiqlandi] = useState(false);
  const [faollashtiriladigan, setFaollashtiriladigan] = useState(null);
  const [tolovTasdiqlandi, setTolovTasdiqlandi] = useState(false);
  const [modalXato, setModalXato] = useState("");
  const yaratishKalitiRef = useRef("");
  const faollashtirishKalitlariRef = useRef(new Map());

  const yukla = async ({ sokin = false } = {}) => {
    if (!sokin) setYuklanmoqda(true);
    setXato("");
    try {
      const data = await muassasaV17Sorov("/meniki", token);
      setTashkilotlar(Array.isArray(data.organizations) ? data.organizations : []);
      setHamyon(data.wallet || { balance_uzs: 0 });
      setSinovKunlari(Number(data.trial_days) || ORGANIZATION_TRIAL_DAYS);
      setFaollashtirishNarxi(Number(data.activation_price_uzs) || ORGANIZATION_ACTIVATION_PRICE_UZS);
    } catch (error) {
      setXato(error.message);
    } finally {
      setYuklanmoqda(false);
    }
  };

  useEffect(() => {
    yukla();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const yangiMuassasaOch = () => {
    setQadam("malumot");
    setYangiTuri("school");
    setYangiNomi("");
    setSinovTasdiqlandi(false);
    setXato("");
    setMuvaffaqiyat("");
    yaratishKalitiRef.current = "";
  };

  const tafsilotdanTasdiqqa = () => {
    if (yangiNomi.trim().length < 2) {
      setXato("Muassasa nomini kiriting");
      return;
    }
    setXato("");
    setQadam("tasdiq");
  };

  const sinovniBoshlash = async () => {
    if (!sinovTasdiqlandi || jarayon) return;
    setJarayon("sinov");
    setXato("");
    setMuvaffaqiyat("");
    try {
      if (!yaratishKalitiRef.current) {
        yaratishKalitiRef.current = makeOrganizationIdempotencyKey("trial-start");
      }
      const payload = buildTrialStartPayload({
        organizationType: yangiTuri,
        name: yangiNomi,
        idempotencyKey: yaratishKalitiRef.current,
      });
      const organization = await muassasaV17Sorov("/sinov-boshlash", token, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setTashkilotlar((current) => [organization, ...current.filter((item) => Number(item.id) !== Number(organization.id))]);
      yaratishKalitiRef.current = "";
      setQadam("royxat");
      setSinovTasdiqlandi(false);
      setMuvaffaqiyat(`${organization.name || yangiNomi} uchun ${sinovKunlari} kunlik bepul sinov boshlandi.`);
      await yukla({ sokin: true });
    } catch (error) {
      setXato(error.message);
    } finally {
      setJarayon("");
    }
  };

  const faollashtirishniOch = (organization) => {
    setFaollashtiriladigan(organization);
    setTolovTasdiqlandi(false);
    setModalXato("");
  };

  const faollashtirish = async () => {
    if (!faollashtiriladigan || !tolovTasdiqlandi || jarayon) return;
    setJarayon("faollashtirish");
    setModalXato("");
    try {
      const organizationId = faollashtiriladigan.id;
      if (!faollashtirishKalitlariRef.current.has(organizationId)) {
        faollashtirishKalitlariRef.current.set(
          organizationId,
          makeOrganizationIdempotencyKey(`activation-${organizationId}`),
        );
      }
      const payload = buildActivationPayload({
        confirmed: tolovTasdiqlandi,
        idempotencyKey: faollashtirishKalitlariRef.current.get(organizationId),
      });
      const data = await muassasaV17Sorov(`/${organizationId}/faollashtirish`, token, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setTashkilotlar((current) => current.map((item) => (
        Number(item.id) === Number(organizationId) ? data.organization : item
      )));
      if (data.wallet) setHamyon(data.wallet);
      faollashtirishKalitlariRef.current.delete(organizationId);
      setFaollashtiriladigan(null);
      setTolovTasdiqlandi(false);
      setMuvaffaqiyat(`${data.organization?.name || faollashtiriladigan.name} faollashtirildi. ${formatUzs(data.charged_uzs || faollashtirishNarxi)} bir marta yechildi.`);
      await yukla({ sokin: true });
    } catch (error) {
      setModalXato(organizationTrialErrorMessage(error.payload || error.message));
    } finally {
      setJarayon("");
    }
  };

  const ishMaydoniniOch = (organization) => {
    const membership = organizationToLegacyMembership(organization);
    if (membership) onWorkspaceOpen?.(membership, organizationTypeMeta(organization.organization_type).workspace);
  };

  const joriyNarx = Number(faollashtiriladigan?.activation_price_uzs) || faollashtirishNarxi;

  if (yuklanmoqda) {
    return (
      <div className="org-trial-shell px-5 pt-6 pb-4">
        <button type="button" onClick={onBack} className="org-trial-back"><ChevronLeft size={16} />{__kbUi(" Ish maydoniga qaytish")}</button>
        <div className="org-trial-loading"><Loader2 size={25} className="animate-spin" /><p>{__kbUi("Muassasalar yuklanmoqda...")}</p></div>
      </div>
    );
  }

  return (
    <div className="org-trial-shell px-5 pt-6 pb-4">
      <button type="button" onClick={qadam === "royxat" ? onBack : () => { setQadam(qadam === "tasdiq" ? "malumot" : "royxat"); setSinovTasdiqlandi(false); setXato(""); }} className="org-trial-back">
        <ChevronLeft size={16} /> {qadam === "royxat" ? __kbUi("Ish maydoniga qaytish") : uiT("Orqaga")}
      </button>

      <header className="org-trial-hero">
        <div className="org-trial-hero__icon"><Building2 size={27} /></div>
        <div>
          <span className="premium-eyebrow">{__kbUi("XUSUSIY MUASSASA")}</span>
          <h1>{__kbUi("Bitta sodda oqimda muassasa oching")}</h1>
          <p>{sinovKunlari}{__kbUi(" kun bepul foydalaning. Davom ettirish uchun keyin ")}{__kbUi(formatUzs(faollashtirishNarxi))}{__kbUi(" bir martalik faollashtirish bor — avtomatik yechim yo'q.")}</p>
        </div>
        <div className="org-trial-wallet"><Wallet size={16} /><span>{__kbUi("Hamyon")}</span><b>{__kbUi(formatUzs(hamyon.balance_uzs))}</b></div>
      </header>

      {xato && <div className="org-trial-notice error" role="alert">{__kbUi(xato)}{qadam === "royxat" && <button type="button" onClick={() => yukla()}><InterfaceText text={__kbUi("Qayta urinish")}/></button>}</div>}
      {muvaffaqiyat && <div className="org-trial-notice success" role="status">{muvaffaqiyat}</div>}

      {qadam === "malumot" && (
        <section className="org-trial-wizard" aria-labelledby="new-org-title">
          <div className="org-trial-step"><span>1</span><b>{__kbUi("Muassasa ma'lumoti")}</b><small>{__kbUi("1 / 2 bosqich")}</small></div>
          <h2 id="new-org-title">{__kbUi("Yangi xususiy muassasa")}</h2>
          <p>{__kbUi("Bu o'qituvchilar uchun yagona sinov oqimi. Davlat yoki ommaviy muassasa yaratish administrator orqali bajariladi.")}</p>
          <label className="org-trial-field">
            <span>{__kbUi("Muassasa turi")}</span>
            <select value={yangiTuri} onChange={(event) => { setYangiTuri(event.target.value); setSinovTasdiqlandi(false); yaratishKalitiRef.current = ""; }}>
              {ORGANIZATION_TYPES.map((item) => <option key={item.value} value={item.value}>{__kbUi(item.icon)} {__kbUi(item.label)}</option>)}
            </select>
          </label>
          <label className="org-trial-field">
            <span>{__kbUi("Muassasa nomi")}</span>
            <input value={yangiNomi} onChange={(event) => { setYangiNomi(event.target.value); setSinovTasdiqlandi(false); yaratishKalitiRef.current = ""; }} placeholder={__kbUi("Masalan: Ziyo xususiy maktabi")} maxLength={160} autoFocus />
          </label>
          <button type="button" className="org-trial-primary" onClick={tafsilotdanTasdiqqa}><InterfaceText text={__kbUi("Davom etish ")}/><ChevronRight size={17} /></button>
        </section>
      )}

      {qadam === "tasdiq" && (
        <section className="org-trial-wizard" aria-labelledby="trial-confirm-title">
          <div className="org-trial-step"><span>2</span><b>{__kbUi("Sinovni tasdiqlash")}</b><small>{__kbUi("2 / 2 bosqich")}</small></div>
          <h2 id="trial-confirm-title">{__kbUi(yangiNomi.trim())}</h2>
          <div className="org-trial-summary">
            <div><span>{__kbUi("Tur")}</span><b>{organizationTypeMeta(yangiTuri).icon} {__kbUi(organizationTypeMeta(yangiTuri).label)}</b></div>
            <div><span>{__kbUi("Egalik")}</span><b>{__kbUi("Xususiy")}</b></div>
            <div><span>{__kbUi("Bepul muddat")}</span><b>{sinovKunlari}{__kbUi(" kun")}</b></div>
            <div><span>{__kbUi("Keyingi faollashtirish")}</span><b>{__kbUi(formatUzs(faollashtirishNarxi))}{__kbUi(" · bir marta")}</b></div>
          </div>
          <div className="org-trial-terms">
            <b>{__kbUi("Sinov hozir bepul boshlanadi")}</b>
            <p>{__kbUi("Hozir hamyondan pul yechilmaydi. ")}{sinovKunlari}{__kbUi(" kundan keyin to'lanmasa, muassasa faqat ko'rish rejimiga o'tadi; barcha ma'lumotlar saqlanadi.")}</p>
          </div>
          <label className="org-trial-checkbox">
            <input type="checkbox" checked={sinovTasdiqlandi} onChange={(event) => setSinovTasdiqlandi(event.target.checked)} />
            <span>{sinovKunlari}{__kbUi(" kunlik bepul sinovni boshlash va undan keyingi faqat ko'rish qoidasini tushundim.")}</span>
          </label>
          <button type="button" className="org-trial-primary" disabled={!sinovTasdiqlandi || jarayon === "sinov"} onClick={sinovniBoshlash}>
            {jarayon === "sinov" ? <><Loader2 size={17} className="animate-spin" />{__kbUi(" Sinov boshlanmoqda...")}</> : __kbUi(`${sinovKunlari} kunlik bepul sinovni boshlash`)}
          </button>
        </section>
      )}

      {qadam === "royxat" && (
        <>
          <div className="org-trial-list-head">
            <div><span className="premium-eyebrow">{__kbUi("MUASSASALARIM")}</span><h2>{__kbUi("Xususiy muassasalar")}</h2></div>
            <button type="button" onClick={yangiMuassasaOch}><Building2 size={17} />{__kbUi(" Yangi muassasa")}</button>
          </div>
          {tashkilotlar.length === 0 ? (
            <section className="org-trial-empty">
              <Building2 size={28} />
              <h3>{__kbUi("Hali xususiy muassasa ochilmagan")}</h3>
              <p>{__kbUi("Bitta “Yangi muassasa” tugmasi orqali bog'cha, maktab, o'quv markazi yoki institut tanlanadi.")}</p>
              <button type="button" onClick={yangiMuassasaOch}>{__kbUi("Yangi muassasa")}</button>
            </section>
          ) : (
            <section className="org-trial-list">
              {tashkilotlar.map((organization) => {
                const meta = organizationTypeMeta(organization.organization_type);
                const state = organizationTrialState(organization);
                return (
                  <article key={organization.id} className={`org-trial-card ${state.key}`}>
                    <div className="org-trial-card__main">
                      <span className="org-trial-card__icon">{meta.icon}</span>
                      <div>
                        <div className="org-trial-card__title"><h3>{organization.name}</h3><span className={`org-trial-badge ${state.key}`}>{__kbUi(state.label)}</span></div>
                        <p>{__kbUi(meta.label)}{__kbUi(" · Xususiy muassasa")}</p>
                      </div>
                    </div>
                    {state.key === "trial" && (
                      <div className="org-trial-card__timeline">
                        <CalendarCheck size={17} />
                        <div><b>{state.detail}</b><span>{__kbUi("Sinov tugashi: ")}{__kbUi(formatTrialEnd(organization.trial_ends_at))}</span></div>
                      </div>
                    )}
                    {state.key === "read_only" && (
                      <div className="org-trial-card__readonly"><KeyRound size={17} /><p><b>{__kbUi("Sinov muddati tugagan — faqat ko'rish.")}</b>{__kbUi(" Barcha ma'lumot saqlangan va faollashtirilgach yana tahrirlanadi.")}</p></div>
                    )}
                    {state.key === "active" && <p className="org-trial-card__active">{__kbUi("✓ Bir martalik faollashtirish bajarilgan")}</p>}
                    <div className="org-trial-card__actions">
                      <button type="button" className="secondary" onClick={() => ishMaydoniniOch(organization)}>{__kbUi("Ish maydonini ochish")}</button>
                      {organizationCanActivate(organization) && <button type="button" className="primary" onClick={() => faollashtirishniOch(organization)}>{__kbUi("Faollashtirish")}</button>}
                    </div>
                  </article>
                );
              })}
            </section>
          )}
          <p className="org-trial-retention"><KeyRound size={15} />{__kbUi(" To'lanmagan muassasa o'chirilmaydi: sinovdan keyin ma'lumotlar saqlanib, faqat ko'rish rejimida qoladi.")}</p>
        </>
      )}

      {faollashtiriladigan && (
        <div className="org-trial-modal-backdrop" role="presentation" onMouseDown={() => jarayon !== "faollashtirish" && setFaollashtiriladigan(null)}>
          <section className="org-trial-modal" role="dialog" aria-modal="true" aria-labelledby="activation-title" onMouseDown={(event) => event.stopPropagation()}>
            <button type="button" className="org-trial-modal__close" disabled={jarayon === "faollashtirish"} onClick={() => setFaollashtiriladigan(null)} aria-label={uiT("Yopish")}><X size={18} /></button>
            <span className="premium-eyebrow">{__kbUi("BIR MARTALIK FAOLLASHTIRISH")}</span>
            <h2 id="activation-title">{faollashtiriladigan.name}</h2>
            <p>{__kbUi("Bu obuna emas. Faqat quyidagi tasdiqdan keyin hamyoningizdan bir marta mablag' yechiladi.")}</p>
            <div className="org-trial-charge">
              <div><span>{__kbUi("Faollashtirish narxi")}</span><b>{__kbUi(formatUzs(joriyNarx))}</b></div>
              <div><span>{__kbUi("Hamyondagi mablag'")}</span><b>{__kbUi(formatUzs(hamyon.balance_uzs))}</b></div>
              <div><span>{__kbUi("To'lov turi")}</span><b>{__kbUi("Bir martalik")}</b></div>
            </div>
            {Number(hamyon.balance_uzs) < joriyNarx && <div className="org-trial-balance-warning">{__kbUi("Hamyondagi mablag' yetarli emas. Tasdiqlashdan oldin balansni to'ldiring.")}</div>}
            {modalXato && <div className="org-trial-notice error" role="alert">{__kbUi(modalXato)}</div>}
            <label className="org-trial-checkbox charge">
              <input type="checkbox" checked={tolovTasdiqlandi} onChange={(event) => setTolovTasdiqlandi(event.target.checked)} />
              <span><b>{__kbUi(formatUzs(joriyNarx))}</b>{__kbUi(" hamyonimdan bir marta yechilishiga aniq roziman.")}</span>
            </label>
            <div className="org-trial-modal__actions">
              <button type="button" className="secondary" disabled={jarayon === "faollashtirish"} onClick={() => setFaollashtiriladigan(null)}>{__kbUi("Hozir emas")}</button>
              <button type="button" className="primary" disabled={!tolovTasdiqlandi || jarayon === "faollashtirish"} onClick={faollashtirish}>
                {jarayon === "faollashtirish" ? <><Loader2 size={17} className="animate-spin" />{__kbUi(" Tasdiqlanmoqda...")}</> : __kbUi(`${formatUzs(joriyNarx)}ni bir marta yechish`)}
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

function muassasaBarqarorKaliti(item) {
  if (!item?.turi) return "";
  const id = item.muassasa_id ?? item.context_id ?? item.organization_v17_id;
  return id == null ? "" : `${item.turi}:${id}`;
}

function muassasaFaolmi(item) {
  if (!item || typeof item !== "object") return false;
  const disabled = value => value === false || value === 0 || ["false", "0", "f"].includes(String(value).trim().toLowerCase());
  const inactiveStatuses = ["archived", "deleted", "inactive", "arxiv", "arxivlangan"];
  return !disabled(item.faol)
    && !disabled(item.is_active)
    && !item.archived_at
    && !item.arxiv_at
    && !item.deleted_at
    && ![item.lifecycle_status, item.status].some(value => inactiveStatuses.includes(String(value || "").trim().toLowerCase()));
}

function faolMuassasalarRoyxati(muassasalar = []) {
  return muassasalar.filter(item => muassasaBarqarorKaliti(item) && muassasaFaolmi(item));
}

function faolMuassasaniTanla({ muassasalar = [], tanlanganKalit = "", kerakliTuri = "" }) {
  const faol = faolMuassasalarRoyxati(muassasalar);
  const turdagilar = kerakliTuri ? faol.filter((item) => item.turi === kerakliTuri) : faol;
  return turdagilar.find((item) => muassasaBarqarorKaliti(item) === tanlanganKalit)
    || turdagilar[0]
    || (!kerakliTuri ? faol[0] : null)
    || null;
}

function OqituvchiBoshEkran({ token, maktabId, onOrtga, readOnly = false }) {
  useKbInterfaceLocale();
  const personalPlannerRef = useRef(null);
  const [personalGrade, setPersonalGrade] = useState(null);
  const [malumot, setMalumot] = useState(null);
  const [xato, setXato] = useState("");
  const [tasdiqlandi, setTasdiqlandi] = useState(true); // jadvalni admin belgilaydi; o'qituvchi faqat ko'radi
  const [tanlanganKunlar, setTanlanganKunlar] = useState([]);
  const [davomatSinfi, setDavomatSinfi] = useState(null);
  const kunNomlari = ["", "Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"];

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    let timedOut = false;
    const timeout = setTimeout(() => { timedOut = true; controller.abort(); }, 20000);
    setMalumot(null); setXato(""); setTasdiqlandi(true); setPersonalGrade(null);
    fetch(`${API_BASE}/api/oqituvchi/bosh_ekran?token=${encodeURIComponent(token)}${maktabId ? `&maktab_id=${encodeURIComponent(maktabId)}` : ""}`, { signal: controller.signal, cache: "no-store" })
      .then(async (r) => { const d = await r.json(); if (!r.ok) throw new Error(typeof d.detail === "string" ? d.detail : d.detail?.message || "O‘qituvchi ma’lumoti yuklanmadi"); return d; })
      .then((d) => {
        if (!active) return;
        setMalumot(d);
        setTanlanganKunlar([...new Set((d.hafta || []).map((x) => Number(x.hafta_kuni)))].sort());
      })
      .catch((e) => { if (active) setXato(timedOut ? "Jadvalni olish cho‘zildi. Ortga qaytib, yana oching." : e.message); })
      .finally(() => clearTimeout(timeout));
    return () => { active = false; clearTimeout(timeout); controller.abort(); };
  }, [token, maktabId]);

  const kunniAlmashtir = (kun) => setTanlanganKunlar((old) => old.includes(kun) ? old.filter((x) => x !== kun) : [...old, kun].sort());
  const kunDarslari = (kun) => (malumot?.hafta || []).filter((x) => Number(x.hafta_kuni) === kun);
  const rahbarSinfmi = (sinfId) => (malumot?.rahbar_sinflar || []).some((x) => Number(x.id) === Number(sinfId));

  if (davomatSinfi) return <DavomatBelgilash token={token} sinfId={davomatSinfi.id} onOrtga={() => setDavomatSinfi(null)} />;
  if (xato) return <div className="px-5 pt-6"><button onClick={onOrtga} className="mb-4 text-sm font-semibold">← <InterfaceText text={__kbUi("Ortga")}/></button><div className="rounded-2xl border p-5 bg-white" style={{ borderColor: "#E8A0A0", color: "#A32D2D" }}>{__kbUi(xato)}</div></div>;
  if (!malumot) return <div className="px-5 pt-16 text-center"><Loader2 size={26} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>;

  if (!tasdiqlandi) return (
    <div className="px-5 pt-6 pb-5">
      <button onClick={onOrtga} className="flex items-center gap-2 mb-4 text-sm font-semibold" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("← Dars guruhlarimga qaytish")}</button>
      <div className="rounded-3xl p-5 text-white" style={{ background: "linear-gradient(135deg,#173247,#1B6B83)" }}>
        <p className="text-xs font-bold tracking-wider mb-1" style={{ color: "#9EDDE0" }}>{__kbUi("MAKTAB JADVALIDAN AVTOMATIK")}</p>
        <h1 className="text-2xl font-bold mb-1">{__kbUi("Haftalik darslaringizni tasdiqlang")}</h1>
        <p className="text-sm mb-5" style={{ color: "#D9E9ED" }}>{malumot.maktab?.nomi} · {malumot.oqituvchi?.full_name} · {malumot.haftalik_soat}{__kbUi(" soat")}</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mb-5">
          {[1,2,3,4,5,6].map((kun) => {
            const darslar = kunDarslari(kun); const tanlangan = tanlanganKunlar.includes(kun); const metod = (malumot.metod_kunlari || []).includes(kun);
            return <button key={kun} onClick={() => kunniAlmashtir(kun)} className="rounded-2xl p-3 text-left border-2" style={tanlangan ? { backgroundColor: "#FFFFFF", color: "#173247", borderColor: "#FFFFFF" } : { backgroundColor: "#FFFFFF12", color: "#FFFFFF", borderColor: "#FFFFFF35" }}>
              <span className="float-right font-black">{tanlangan ? __kbUi("✓") : __kbUi("○")}</span><b className="block">{__kbUi(kunNomlari[kun])}</b><small className="block mt-2 opacity-75">{metod ? __kbUi("Metod kuni") : __kbUi(`${darslar.length} dars`)}</small>
            </button>;
          })}
        </div>
        <div className="grid md:grid-cols-3 gap-2 mb-4 text-sm"><div className="rounded-xl p-3 bg-white/10"><small className="block opacity-70">{__kbUi("FANLAR")}</small><b>{malumot.oqituvchi?.fanlari || __kbUi("Biriktirilgan fanlar")}</b></div><div className="rounded-xl p-3 bg-white/10"><small className="block opacity-70">{__kbUi("SINF RAHBARLIGI")}</small><b>{(malumot.rahbar_sinflar || []).map((x) => x.sinf_nomi).join(", ") || __kbUi("Biriktirilmagan")}</b></div><div className="rounded-xl p-3 bg-white/10"><small className="block opacity-70">{__kbUi("JADVAL HOLATI")}</small><b>{malumot.jadval_tasdiqlangan ? __kbUi("✓ Tasdiqlangan") : __kbUi("Jadval tasdiqlanmagan")}</b></div></div>
        <button disabled={!tanlanganKunlar.length || !malumot.jadval_tasdiqlangan} onClick={() => setTasdiqlandi(true)} className="w-full rounded-xl py-3 font-bold disabled:opacity-50" style={{ backgroundColor: "#55D6A7", color: "#083B32" }}>{__kbUi("Tasdiqlash va Ta’lim maydonini ochish →")}</button>
      </div>
    </div>
  );

  const hozirgi = malumot.bugun?.hozirgi || malumot.bugun?.keyingi;
  return (
    <div className="px-5 pt-6 pb-6">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4"><div><button onClick={onOrtga} className="text-sm font-semibold mb-2" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("← Dars guruhlarim")}</button><h1 className="text-2xl font-bold" style={{ color: "var(--ui-legacy-color-21384c, #21384C)" }}>{__kbUi("O‘qituvchining Ta’lim maydoni")}</h1><p className="text-sm" style={{ color: "var(--ui-legacy-color-7a8794, #7A8794)" }}>{malumot.maktab?.nomi} · {malumot.kun_nomi} · {malumot.hozir}</p></div><span className="rounded-xl px-4 py-2.5 text-sm font-bold border bg-white" style={{ borderColor: "#DCE6EA", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Admin belgilagan jadval")}</span></div>
      <div ref={personalPlannerRef} style={{ scrollMarginTop: "calc(var(--samtm-portal-top, 64px) + 16px)" }}>
        <React.Suspense fallback={<OgirBolimYuklanmoqda />}>
          <StudentScheduleWorkspace token={token} apiBase={API_BASE} mode="teacher" schoolId={maktabId} compactTitle readOnly={readOnly}
            student={{ full_name: malumot.oqituvchi?.full_name }}
            initialGrade={personalGrade || Number(String((malumot.rahbar_sinflar || [])[0]?.sinf_nomi || hozirgi?.sinf_nomi || "").match(/(?:^|\D)(1[01]|[1-9])(?:\D|$)/)?.[1]) || undefined}
          />
        </React.Suspense>
      </div>
      {hozirgi ? <section className="rounded-3xl p-5 mb-4 text-white" style={{ background: "linear-gradient(135deg,#1B4B7A,#0D7A77)" }}><span className="text-xs font-bold">{malumot.bugun?.hozirgi ? __kbUi("HOZIRGI DARS") : __kbUi("KEYINGI DARS")}</span><h2 className="text-2xl font-bold mt-1">{hozirgi.sinf_nomi} · {hozirgi.fan}</h2><p className="text-sm opacity-80">{hozirgi.boshlanish_vaqti}–{hozirgi.tugash_vaqti} · {hozirgi.xona || __kbUi("Xona ko‘rsatilmagan")}</p><div className="mt-4 rounded-2xl p-4 bg-white/10"><small className="block opacity-70">{__kbUi("MAVZU")}</small><b>{hozirgi.mavzu || __kbUi("Taqvim-mavzu rejasida mavzu biriktirilmagan")}</b></div><div className="flex flex-wrap gap-2 mt-4"><button onClick={() => { const nextGrade = Number(String(hozirgi.sinf_nomi || "").match(/(?:^|\D)(1[01]|[1-9])(?:\D|$)/)?.[1]); if (nextGrade) setPersonalGrade(nextGrade); personalPlannerRef.current?.scrollIntoView({ behavior: "auto", block: "start" }); }} className="rounded-xl bg-white px-4 py-2.5 font-bold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Sinf rejasini moslash")}</button>{rahbarSinfmi(hozirgi.sinf_id) && <button onClick={() => setDavomatSinfi({ id: hozirgi.sinf_id })} className="rounded-xl px-4 py-2.5 font-bold border border-white/40"><InterfaceText text={__kbUi("Davomat")}/></button>}</div></section> : <div className="rounded-2xl border bg-white p-5 mb-4"><b>{__kbUi("Hozir dars yo‘q")}</b><p className="text-sm text-gray-500">{__kbUi("Keyingi dars jadvaldan avtomatik chiqadi.")}</p></div>}
      <div className="grid lg:grid-cols-2 gap-4">
        <section className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}><div className="flex justify-between mb-3"><h2 className="font-bold">{__kbUi("Bugungi jadvalim")}</h2><span className="text-xs font-semibold">{malumot.bugun?.darslar?.length || 0}{__kbUi(" dars")}</span></div><div className="space-y-2">{(malumot.bugun?.darslar || []).map((d) => <div key={d.slot_id} className="rounded-xl p-3 flex justify-between gap-3" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}><div><b className="text-sm">{d.boshlanish_vaqti} · {d.sinf_nomi} · {d.fan}</b><small className="block" style={{ color: "var(--ui-legacy-color-7a8794, #7A8794)" }}>{d.xona || __kbUi("Xona yo‘q")} · {d.mavzu || __kbUi("Mavzu biriktirilmagan")}</small></div><span className="text-xs">{d.smena}{__kbUi("-smena")}</span></div>)}</div></section>
        <section className="rounded-2xl border bg-white p-4" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}><div className="flex justify-between mb-3"><h2 className="font-bold">{__kbUi("Ertangi darslar")}</h2><span className="text-xs font-semibold">{malumot.ertaga?.kun_nomi}</span></div><div className="space-y-2">{(malumot.ertaga?.darslar || []).map((d) => <div key={d.slot_id} className="rounded-xl p-3" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><b className="text-sm">{d.boshlanish_vaqti} · {d.sinf_nomi} · {d.fan}</b><small className="block" style={{ color: "var(--ui-legacy-color-7a8794, #7A8794)" }}>{d.mavzu || __kbUi("Mavzu rejasidan kutilmoqda")}</small></div>)}</div></section>
      </div>
      {(malumot.rahbar_sinflar || []).length > 0 && <section className="rounded-2xl border bg-white p-4 mt-4" style={{ borderColor: "#DCE6EA" }}><h2 className="font-bold mb-3">{__kbUi("Sinf rahbarligi")}</h2>{malumot.rahbar_sinflar.map((s) => <div key={s.id} className="flex items-center justify-between gap-3 rounded-xl p-3" style={{ backgroundColor: "#EEF6F1" }}><div><b>{s.sinf_nomi}{__kbUi(" sinf")}</b><small className="block" style={{ color: "#6E7F89" }}>{s.oquvchilar}{__kbUi(" o‘quvchi · ")}{s.smena}{__kbUi("-smena")}</small></div><button onClick={() => setDavomatSinfi(s)} className="rounded-lg px-3 py-2 text-sm font-bold text-white" style={{ backgroundColor: "#2E6C55" }}>{__kbUi("Davomatni ochish")}</button></div>)}</section>}
      {malumot.kundalik_eslatma && <div className="rounded-2xl p-4 mt-4" style={{ backgroundColor: "#FDF3E0", color: "#8A5A1C" }}><b>{__kbUi("Kundalik eslatmasi")}</b><p className="text-sm">{__kbUi("Bugungi darslaringiz bo‘yicha baholarni kiritishni unutmadingizmi?")}</p></div>}
    </div>
  );
}

function OqituvchiTab({ token, foydalanuvchi, boshlanishKorinishi, birInstitutAvtoOchishRef, readOnly = false, onOpenCourses }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [holat, setHolat] = useState("togaraklar"); // togaraklar | azolar | yaratish
  const [togaraklar, setTogaraklar] = useState([]);
  const [togarakKvota, setTogarakKvota] = useState(null);
  const [tanlangan, setTanlangan] = useState(null);
  const [azolar, setAzolar] = useState([]);
  const [kutilayotganAzolar, setKutilayotganAzolar] = useState([]);
  const [bahoQoyilayotgan, setBahoQoyilayotgan] = useState(null); // user_id | null
  const [bahoQiymati, setBahoQiymati] = useState("");
  const [bahoTopicCode, setBahoTopicCode] = useState("");
  const [bahoMavzulari, setBahoMavzulari] = useState([]);
  const [izohQiymati, setIzohQiymati] = useState("");
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");
  const [korinish, setKorinish] = useState(() => foydalanuvchi?.maktab_id ? "oqituvchi_bosh_ekran" : "togarak"); // maktab o'qituvchisi avval bugungi Ta'lim maydoniga kiradi
  const [muassasalar, setMuassasalar] = useState([]);
  const [muassasalarYuklanmoqda, setMuassasalarYuklanmoqda] = useState(true);
  const [muassasalarJavobiOlindi, setMuassasalarJavobiOlindi] = useState(false);
  const [muassasalarXato, setMuassasalarXato] = useState("");
  const [muassasalarQaytaYuklash, setMuassasalarQaytaYuklash] = useState(0);
  const [aktivMuassasaKaliti, setAktivMuassasaKaliti] = useState("");

  // Pastki menyudan ("Maktabim"/"Bog'cham"/"Universitetim"/"Markazim")
  // to'g'ridan-to'g'ri kelgan bo'lsa — o'sha ekranga o'tamiz. "vaqt"
  // maydoni — bir xil ekran ketma-ket ikki marta bosilsa ham qayta
  // ishga tushishi uchun (aks holda useEffect qayta chaqirilmas edi).
  useEffect(() => {
    if (boshlanishKorinishi?.korinish) setKorinish(boshlanishKorinishi.korinish);
    const requestedKey = muassasaBarqarorKaliti(boshlanishKorinishi?.muassasa);
    if (requestedKey) setAktivMuassasaKaliti(requestedKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [boshlanishKorinishi?.vaqt]);

  const [yangiNomi, setYangiNomi] = useState("");
  const [yangiTuri, setYangiTuri] = useState("oddiy"); // "oddiy" | "avto"
  const [yangiGuruhTuri, setYangiGuruhTuri] = useState("togarak"); // "togarak" | "repetitor"
  const [yangiFan, setYangiFan] = useState("");
  const [yangiFanOzicha, setYangiFanOzicha] = useState(false); // true bo'lsa o'qituvchi ro'yxatda yo'q fanni o'zi yozadi
  const [meningFanlarim, setMeningFanlarim] = useState([]); // avval o'zi yozgan fanlar — qayta yozib adashmasin
  const [yangiSinf, setYangiSinf] = useState("");         // "1".."11"
  const [yangiMaxsusSinf, setYangiMaxsusSinf] = useState(false); // true bo'lsa to'garak guruhi (masalan "3-4")
  const [yangiSinfTuri, setYangiSinfTuri] = useState("guruh"); // "guruh" | "grupa" | "repetitor"
  const [yangiSinfMatni, setYangiSinfMatni] = useState(""); // tanlangan to'garak sinfi (masalan "3-4")
  const [meningSinflarim, setMeningSinflarim] = useState([]); // avval o'zi yozgan maxsus sinflar — qayta yozib adashmasin
  const [togarakSinflari, setTogarakSinflari] = useState([]); // mavjud to'garak sinflari ro'yxati
  const [togarakSinflariYuklanmoqda, setTogarakSinflariYuklanmoqda] = useState(false);
  const [sinfFanlari, setSinfFanlari] = useState([]); // tanlangan sinf uchun MAVJUD fanlar ro'yxati
  const [sinfFanlariYuklanmoqda, setSinfFanlariYuklanmoqda] = useState(false);
  const [yangiMavjudRejalar, setYangiMavjudRejalar] = useState([]);
  const [yangiRejalarYuklanmoqda, setYangiRejalarYuklanmoqda] = useState(false);
  const [yangiTanlanganRejaId, setYangiTanlanganRejaId] = useState(null); // null = rejasiz (eski avtomatik usul)
  const [yangiRejaQurishOchiq, setYangiRejaQurishOchiq] = useState(null); // reja_id | null — bo'lsa RejaDetali ko'rsatiladi
  const [yangiRejaNomi, setYangiRejaNomi] = useState("");
  const [yangiRejaYaratilmoqda, setYangiRejaYaratilmoqda] = useState(false);
  const [yangiParol, setYangiParol] = useState("");
  const [yangiMaxTalaba, setYangiMaxTalaba] = useState(String(CLUB_STUDENT_LIMIT));
  const [yangiOylikSumma, setYangiOylikSumma] = useState("");
  const [uniGuruhIzlash, setUniGuruhIzlash] = useState("");
  const [uniGuruhNatijalar, setUniGuruhNatijalar] = useState([]);
  const [tanlanganUniGuruh, setTanlanganUniGuruh] = useState(null);
  const [yaratilmoqda, setYaratilmoqda] = useState(false);

  // "Aralash to'garak guruhi" yoqilganda — mavjud to'garak sinflari ro'yxatini yuklaymiz
  useEffect(() => {
    if (!yangiMaxsusSinf || togarakSinflari.length > 0) return;
    setTogarakSinflariYuklanmoqda(true);
    fetch(`${API_BASE}/api/mavzular?turi=togarak&token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => {
        const sinflar = new Set();
        (d.fanlar || []).forEach((f) => f.sinflar.forEach((s) => sinflar.add(s.sinf)));
        setTogarakSinflari(Array.from(sinflar).sort());
      })
      .finally(() => setTogarakSinflariYuklanmoqda(false));
  }, [yangiMaxsusSinf]);

  // Sinf (oddiy yoki to'garak) tanlangach — o'sha sinfda MAVJUD fanlar ro'yxatini yuklaymiz
  useEffect(() => {
    const sinfQiymati = yangiMaxsusSinf ? yangiSinfMatni : yangiSinf;
    setYangiFan("");
    setSinfFanlari([]);
    if (!sinfQiymati) return;
    setSinfFanlariYuklanmoqda(true);
    const turi = yangiMaxsusSinf ? "togarak" : "oddiy";
    fetch(`${API_BASE}/api/mavzular?sinf=${encodeURIComponent(sinfQiymati)}&turi=${turi}&token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => setSinfFanlari((d.fanlar || []).map((f) => f.nom)))
      .finally(() => setSinfFanlariYuklanmoqda(false));
  }, [yangiSinf, yangiSinfMatni, yangiMaxsusSinf]);

  const rejalarniQaytaYukla = () => {
    const sinfQiymati = yangiMaxsusSinf ? yangiSinfMatni : yangiSinf;
    if (!sinfQiymati || !yangiFan) { setYangiMavjudRejalar([]); return; }
    setYangiRejalarYuklanmoqda(true);
    fetch(`${API_BASE}/api/oqituvchi/rejalarim?token=${encodeURIComponent(token)}&sinf=${encodeURIComponent(sinfQiymati)}&fan=${encodeURIComponent(yangiFan)}`)
      .then((r) => r.json())
      .then((d) => setYangiMavjudRejalar(d.rejalar || []))
      .catch(() => setYangiMavjudRejalar([]))
      .finally(() => setYangiRejalarYuklanmoqda(false));
  };
  useEffect(() => {
    setYangiTanlanganRejaId(null);
    rejalarniQaytaYukla();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [yangiSinf, yangiSinfMatni, yangiMaxsusSinf, yangiFan, token]);

  const yangiRejaYaratishBoshla = async () => {
    const sinfQiymati = yangiMaxsusSinf ? yangiSinfMatni.trim() : yangiSinf;
    if (!yangiRejaNomi.trim() || !sinfQiymati || !yangiFan) return;
    setYangiRejaYaratilmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/reja_yarat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token,
          nomi: yangiRejaNomi.trim(),
          sinf: sinfQiymati,
          fan: yangiFan,
          guruh_turi: yangiMaxsusSinf ? yangiSinfTuri : "sinf",
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setYangiRejaNomi("");
      setYangiRejaQurishOchiq(data.reja_id);
    } catch (e) { setXato(e.message); } finally { setYangiRejaYaratilmoqda(false); }
  };

  useEffect(() => {
    if (uniGuruhIzlash.trim().length < 1) { setUniGuruhNatijalar([]); return; }
    const kechiktirish = setTimeout(() => {
      fetch(`${API_BASE}/api/oqituvchi/universitet_guruh_qidir?token=${encodeURIComponent(token)}&nomi=${encodeURIComponent(uniGuruhIzlash.trim())}`)
        .then((r) => r.json())
        .then((d) => setUniGuruhNatijalar(d.natijalar || []))
        .catch(() => {});
    }, 400);
    return () => clearTimeout(kechiktirish);
  }, [uniGuruhIzlash, token]);

  useEffect(() => {
    fetch(`${API_BASE}/api/oqituvchi/togaraklar?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => {
        setTogaraklar(d.togaraklar || []);
        setTogarakKvota(d.kvota || null);
        setYuklanmoqda(false);
      })
      .catch(() => { setXato("Yuklab bo'lmadi"); setYuklanmoqda(false); });
  }, [token]);

  useEffect(() => {
    setMuassasalarYuklanmoqda(true);
    setMuassasalarJavobiOlindi(false);
    setMuassasalarXato("");
    fetch(`${API_BASE}/api/auth/muassasalarim?token=${encodeURIComponent(token)}`)
      .then(async (r) => {
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || "Muassasalar yuklanmadi");
        return data;
      })
      .then((d) => {
        setMuassasalar(d.muassasalar || []);
        setMuassasalarJavobiOlindi(true);
      })
      .catch((error) => {
        setMuassasalar([]);
        setMuassasalarJavobiOlindi(true);
        setMuassasalarXato(error?.message || "Muassasalar ro'yxati yuklanmadi");
      })
      .finally(() => setMuassasalarYuklanmoqda(false));
  }, [token, muassasalarQaytaYuklash]);

  useEffect(() => {
    fetch(`${API_BASE}/api/oqituvchi/mening_fanlarim?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => setMeningFanlarim(d.fanlar || []))
      .catch(() => {});
    fetch(`${API_BASE}/api/oqituvchi/mening_maxsus_sinflarim?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => setMeningSinflarim(d.sinflar || []))
      .catch(() => {});
  }, [token]);

  const togarakOch = async (t) => {
    setYuklanmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/togarak/${t.id}/azolar?token=${encodeURIComponent(token)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : (data.detail?.message || "Guruhni ochib bo‘lmadi"));
      setAzolar(data.azolar || []);
      setTanlangan(t);
      setHolat("kalendar_reja");
      fetch(`${API_BASE}/api/oqituvchi/togarak_barcha_mavzular?token=${encodeURIComponent(token)}&togarak_id=${t.id}`)
        .then((r) => r.json())
        .then((body) => setBahoMavzulari(body.mavzular || []))
        .catch(() => setBahoMavzulari([]));
    } catch (e) {
      setXato(e.message);
    } finally { setYuklanmoqda(false); }
  };

  const kutilayotganAzolarniYukla = () => {
    if (!tanlangan) return;
    fetch(`${API_BASE}/api/oqituvchi/togarak/${tanlangan.id}/kutilayotgan_azolar?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => setKutilayotganAzolar(d.azolar || []))
      .catch(() => {});
  };

  useEffect(() => {
    if (holat === "azolar") kutilayotganAzolarniYukla();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [holat, tanlangan]);

  const azolarniQaytaYukla = () => {
    if (!tanlangan) return;
    fetch(`${API_BASE}/api/oqituvchi/togarak/${tanlangan.id}/azolar?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => setAzolar(d.azolar || []))
      .catch(() => {});
  };

  const azoTasdiqla = async (azolikId) => {
    setXato("");
    const res = await fetch(`${API_BASE}/api/oqituvchi/azo_tasdiqla?token=${encodeURIComponent(token)}&azolik_id=${azolikId}`, { method: "PUT" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setXato(apiErrorMessage(data.detail, "O'quvchini tasdiqlab bo'lmadi"));
      return;
    }
    kutilayotganAzolarniYukla();
    azolarniQaytaYukla();
  };

  const azoRadEt = async (azolikId) => {
    await fetch(`${API_BASE}/api/oqituvchi/azo_rad_etish?token=${encodeURIComponent(token)}&azolik_id=${azolikId}`, { method: "DELETE" });
    kutilayotganAzolarniYukla();
  };

  const bahoBoshla = (azo) => {
    setBahoQoyilayotgan(azo.user_id);
    setBahoQiymati(azo.oxirgi_baho != null ? String(azo.oxirgi_baho) : "");
    setBahoTopicCode("");
    setIzohQiymati("");
  };

  const bahoSaqla = async (userId) => {
    const baho = parseInt(bahoQiymati, 10);
    if (isNaN(baho) || baho < 0 || baho > 100) {
      setXato("Baho 0-100 oralig'ida bo'lishi kerak");
      return;
    }
    if (!bahoTopicCode) {
      setXato("Baho qaysi mavzuga tegishli ekanini tanlang");
      return;
    }
    setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/baho_qoy`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, togarak_id: tanlangan.id, user_id: userId, baho, topic_code: bahoTopicCode, izoh: izohQiymati || null }),
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
    const sinfQiymati = yangiMaxsusSinf ? yangiSinfMatni.trim() : yangiSinf;
    if (!sinfQiymati) {
      setXato("Sinfni tanlang (yoki to'garak guruhini kiriting)");
      return;
    }
    const sigim = Number.parseInt(yangiMaxTalaba, 10);
    if (!Number.isFinite(sigim) || sigim < 1 || sigim > CLUB_STUDENT_LIMIT) {
      setXato(`Guruh sig'imi 1–${CLUB_STUDENT_LIMIT} oralig'ida bo'lishi kerak`);
      return;
    }
    setYaratilmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/oqituvchi/togarak_yarat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token,
          nomi: yangiNomi.trim(),
          fan: yangiFan.trim(),
          sinf: sinfQiymati,
          turi: yangiTuri,
          guruh_turi: yangiGuruhTuri,
          parol: yangiParol || undefined,
          max_talaba: normalizedClubCapacity(yangiMaxTalaba),
          oylik_summa: yangiOylikSumma ? parseInt(yangiOylikSumma, 10) : undefined,
          universitet_guruh_id: tanlanganUniGuruh ? tanlanganUniGuruh.id : undefined,
          reja_id: yangiTanlanganRejaId || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(apiErrorMessage(data.detail, "To'garak yaratilmadi"));
      const yangiTogarak = { id: data.togarak_id, nomi: yangiNomi.trim(), fan: yangiFan.trim(), sinf: sinfQiymati, turi: yangiTuri, guruh_turi: data.guruh_turi || yangiGuruhTuri, max_talaba: data.max_talaba || CLUB_STUDENT_LIMIT, azo_soni: 0 };
      setTogaraklar((prev) => [...prev, yangiTogarak]);
      setTogarakKvota(data.kvota || togarakKvota);
      setYangiNomi(""); setYangiTuri("oddiy"); setYangiGuruhTuri("togarak"); setYangiFan(""); setYangiFanOzicha(false); setYangiSinf(""); setYangiMaxsusSinf(false); setYangiSinfMatni("");
      setTogarakSinflari([]); setSinfFanlari([]);
      setYangiMavjudRejalar([]); setYangiTanlanganRejaId(null); setYangiRejaNomi("");
      setYangiParol(""); setYangiMaxTalaba(String(CLUB_STUDENT_LIMIT)); setYangiOylikSumma("");
      setUniGuruhIzlash(""); setUniGuruhNatijalar([]); setTanlanganUniGuruh(null);
      setTanlangan(yangiTogarak);
      setAzolar([]);
      setHolat("mavzular_boshqarish");
    } catch (e) {
      setXato(e.message);
    } finally { setYaratilmoqda(false); }
  };

  const [togarakRuxsati, setTogarakRuxsati] = useState({ ruxsat: true, izoh: "" }); // admin "kim nima yarata oladi" kaliti
  useEffect(() => {
    if (!token) return;
    fetch(`${API_BASE}/api/xususiyat_ruxsatlarim?token=${encodeURIComponent(token)}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (d?.ruxsatlar?.togarak) setTogarakRuxsati(d.ruxsatlar.togarak); })
      .catch(() => {});
  }, [token]);
  const yaratishniOch = ({ turi = "oddiy", guruhTuri = null, guruhMaqsadi = "togarak" } = {}) => {
    if (!togarakRuxsati.ruxsat) { setXato(togarakRuxsati.izoh || "To'garak yaratish hozircha yopiq."); return; }
    setXato("");
    setYangiTuri(turi);
    setYangiGuruhTuri(guruhMaqsadi);
    setYangiMaxTalaba(String(CLUB_STUDENT_LIMIT));
    if (guruhTuri) {
      setYangiMaxsusSinf(true);
      setYangiSinfTuri(guruhTuri);
      setYangiSinf("");
    }
    setHolat("yaratish");
  };

  if (korinish === "muassasa_v17") {
    return (
      <MuassasaV17Markazi
        token={token}
        onBack={() => setKorinish("togarak")}
        onWorkspaceOpen={(membership, workspace) => {
          setMuassasalar((current) => [
            membership,
            ...current.filter((item) => !(
              item.organization_v17_id === membership.organization_v17_id
              || (item.turi === membership.turi && Number(item.muassasa_id) === Number(membership.muassasa_id))
            )),
          ]);
          setMuassasalarJavobiOlindi(true);
          setAktivMuassasaKaliti(muassasaBarqarorKaliti(membership));
          setKorinish(workspace || "togarak");
        }}
      />
    );
  }

  const profilMuassasalar = [
    foydalanuvchi?.universitet_id && { turi: "universitet", muassasa_id: foydalanuvchi.universitet_id, muassasa_nomi: foydalanuvchi.universitet_nomi, lavozim: foydalanuvchi.lavozim },
    foydalanuvchi?.maktab_id && { turi: "maktab", muassasa_id: foydalanuvchi.maktab_id, muassasa_nomi: foydalanuvchi.maktab_nomi, lavozim: foydalanuvchi.lavozim },
    foydalanuvchi?.markaz_id && { turi: "markaz", muassasa_id: foydalanuvchi.markaz_id, muassasa_nomi: foydalanuvchi.markaz_nomi, lavozim: foydalanuvchi.lavozim },
    foydalanuvchi?.bogcha_id && { turi: "bogcha", muassasa_id: foydalanuvchi.bogcha_id, muassasa_nomi: foydalanuvchi.bogcha_nomi, lavozim: foydalanuvchi.lavozim },
  ].filter(Boolean);
  const samariMuassasalarAsos = muassasalarJavobiOlindi ? muassasalar : profilMuassasalar;
  // Kirishda aniqlangan ishxona (masalan institut bootstrap orqali) ro'yxatda bo'lmasa — qo'shamiz.
  const boshlanishMuassasasi = boshlanishKorinishi?.muassasa;
  const samariMuassasalar = boshlanishMuassasasi && !samariMuassasalarAsos.some((m) => muassasaBarqarorKaliti(m) === muassasaBarqarorKaliti(boshlanishMuassasasi))
    ? [...samariMuassasalarAsos, boshlanishMuassasasi]
    : samariMuassasalarAsos;
  const faolSamariMuassasalar = faolMuassasalarRoyxati(samariMuassasalar);
  const kerakliTuri = ({ institut_workspace: "universitet", universitet: "universitet", universitet_legacy: "universitet",
    maktab_rahbariyat: "maktab", maktab_workspace: "maktab", maktab_legacy: "maktab",
    markaz: "markaz", markaz_workspace: "markaz", markaz_legacy: "markaz",
    bogcha: "bogcha", bogcha_workspace: "bogcha", bogcha_legacy: "bogcha",
  })[korinish] || "";
  const aktivMuassasa = faolMuassasaniTanla({
    muassasalar: faolSamariMuassasalar,
    tanlanganKalit: aktivMuassasaKaliti,
    kerakliTuri,
  });
  const kvotaBloklangan = Boolean(
    !freeClubAvailable(togarakKvota) &&
    !foydalanuvchi?.is_admin &&
    aktivMuassasa?.turi !== "markaz" &&
    !tanlanganUniGuruh
  );
  const tanlanganSigim = normalizedClubCapacity(tanlangan?.max_talaba);
  const tanlanganGuruhToliq = Boolean(tanlangan && azolar.length >= tanlanganSigim);
  const MUASSASA_IKONKA = { maktab: "🏫", markaz: "🎓", bogcha: "🧸", universitet: "🎓" };
  const MUASSASA_BOSHQARUVCHI_LAVOZIM = {
    maktab: ["direktor", "zam_direktor_uquv", "zam_direktor_tarbiya"],
    markaz: ["markaz_direktor", "administrator"],
    bogcha: ["bogcha_direktor", "bogcha_zam"],
    universitet: ["rektor", "prorektor"],
  };
  const muassasagaRuxsatBor = (turi) => Boolean(
    foydalanuvchi?.is_admin || faolSamariMuassasalar.some((m) => m.turi === turi)
  );
  const himoyalanganMuassasaKorinishi = {
    markaz: "markaz",
    markaz_workspace: "markaz",
    markaz_legacy: "markaz",
    maktab_rahbariyat: "maktab",
    maktab_workspace: "maktab",
    maktab_legacy: "maktab",
    bogcha: "bogcha",
    bogcha_workspace: "bogcha",
    bogcha_legacy: "bogcha",
    institut_workspace: "universitet",
    universitet: "universitet",
    universitet_legacy: "universitet",
  }[korinish];

  if (himoyalanganMuassasaKorinishi && muassasalarYuklanmoqda) {
    return <div className="px-5 pt-16 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>;
  }

  if (himoyalanganMuassasaKorinishi && muassasalarXato) {
    return <div className="px-5 pt-6 pb-4"><div className="mx-auto max-w-xl rounded-3xl border bg-white p-7 text-center" style={{ borderColor: "#E8BABA" }}>
      <AlertTriangle size={30} className="mx-auto mb-3" style={{ color: "#B42318" }} />
      <h2 className="text-lg font-bold mb-2">{__kbUi("Muassasalar ro'yxati yuklanmadi")}</h2>
      <p className="text-sm leading-relaxed" style={{ color: "#6F6859" }}>{__kbUi(muassasalarXato)}</p>
      <button onClick={() => setMuassasalarQaytaYuklash((value) => value + 1)} className="mt-4 rounded-xl px-4 py-2 text-sm font-bold text-white" style={{ backgroundColor: "#1B6B83" }}><InterfaceText text={__kbUi("Qayta urinish")}/></button>
    </div></div>;
  }

  if (himoyalanganMuassasaKorinishi && !muassasagaRuxsatBor(himoyalanganMuassasaKorinishi)) {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => setKorinish("togarak")} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
          <span className="w-7 h-7 rounded-xl flex items-center justify-center" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} /></span>{__kbUi("Ish maydoniga qaytish")}</button>
        <div className="rounded-3xl border bg-white p-7 text-center" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <Building2 size={30} className="mx-auto mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
          <h2 className="text-lg font-bold mb-2">{__kbUi("Bu muassasaga ruxsat yo'q")}</h2>
          <p className="text-sm leading-relaxed" style={{ color: "#6F6859" }}>{__kbUi("Oddiy o'qituvchi bog'cha, maktab, markaz yoki institut yarata olmaydi. Muassasa faqat Administrator markazida ochiladi; xodim esa taklif kodi bilan o'z ish joyiga ulanadi.")}</p>
        </div>
      </div>
    );
  }

  if (korinish === "oqituvchi_analitika") {
    return <TeacherAnalyticsPanel token={token} initialWorkplace={aktivMuassasa}
      onBack={() => setKorinish("togarak")} />;
  }

  if (korinish === "markaz" || korinish === "markaz_workspace") {
    return (
      <div className="org-v17-workspace-wrap">
        <MuassasaV17ReadOnlyBanner organization={aktivMuassasa} />
        <React.Suspense fallback={<div className="px-5 pt-16 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>}>
          <LearningCenterWorkspace
            token={token}
            apiBase={API_BASE}
            initialWorkspace={aktivMuassasa?.turi === "markaz" ? aktivMuassasa : null}
            onBack={() => setKorinish("togarak")}
            onLegacy={() => setKorinish("markaz_legacy")}
            assignedOnly={!foydalanuvchi?.is_admin}
            canCreateInstitution={Boolean(foydalanuvchi?.is_admin)}
          />
        </React.Suspense>
      </div>
    );
  }

  if (korinish === "markaz_legacy") {
    return <MarkazBoshqaruvi token={token} markazId={aktivMuassasa?.turi === "markaz" ? aktivMuassasa.muassasa_id : foydalanuvchi?.markaz_id} onOrtga={() => setKorinish("markaz_workspace")} />;
  }

  const aktivMaktabId = aktivMuassasa?.turi === "maktab" ? aktivMuassasa.muassasa_id : foydalanuvchi?.maktab_id;

  if (korinish === "oqituvchi_bosh_ekran") {
    return <OqituvchiBoshEkran token={token} maktabId={aktivMaktabId} readOnly={readOnly} onOrtga={() => setKorinish("togarak")} />;
  }

  if (korinish === "maktab_rahbariyat" || korinish === "maktab_workspace") {
    return (
      <div className="org-v17-workspace-wrap">
        <MuassasaV17ReadOnlyBanner organization={aktivMuassasa} />
        <React.Suspense fallback={<div className="px-5 pt-16 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>}>
          <SchoolWorkspace
            token={token}
            apiBase={API_BASE}
            initialWorkspace={aktivMuassasa?.turi === "maktab" ? aktivMuassasa : null}
            onBack={() => setKorinish("togarak")}
            onLegacy={() => setKorinish("maktab_legacy")}
            assignedOnly={!foydalanuvchi?.is_admin}
            canCreateInstitution={Boolean(foydalanuvchi?.is_admin)}
          />
        </React.Suspense>
      </div>
    );
  }

  if (korinish === "maktab_legacy") {
    return <MaktabBoshqaruvi token={token} maktabId={aktivMaktabId} onOrtga={() => setKorinish("maktab_workspace")} />;
  }

  if (korinish === "kutubxona") {
    return <KutubxonaBolimi token={token} maktabId={aktivMaktabId} onOrtga={() => setKorinish("togarak")} />;
  }

  if (korinish === "moliya") {
    return <MoliyaBolimi token={token} maktabId={aktivMaktabId} onOrtga={() => setKorinish("togarak")} />;
  }

  if (korinish === "hujjatlar") {
    return <HujjatlarBolimi token={token} maktabId={aktivMaktabId} onOrtga={() => setKorinish("togarak")} />;
  }

  if (korinish === "rejalashtirish") {
    return <RejalashtirishBolimi token={token} maktabId={aktivMaktabId} onOrtga={() => setKorinish("togarak")} />;
  }

  if (korinish === "ai_yordamchi") {
    return <AiYordamchiBolimi token={token} onOrtga={() => setKorinish("togarak")} />;
  }

  if (korinish === "ai_dars") {
    return <AiOchiqDarsKonstruktori token={token} onOrtga={() => setKorinish("togarak")} />;
  }
  if (korinish === "ai_togarak") {
    return <AiTogarakRejaKonstruktori token={token} onOrtga={() => setKorinish("togarak")} />;
  }

  if (korinish === "rejalarim") {
    return <RejalarimBolimi token={token} onOrtga={() => setKorinish("togarak")} />;
  }

  if (korinish === "fanlar_tahlili") {
    return <FanlarTahliliBolimi token={token} maktabId={aktivMaktabId} onOrtga={() => setKorinish("togarak")} />;
  }

  if (korinish === "psixolog") {
    return <PsixologQidiruv token={token} maktabId={aktivMaktabId} onOrtga={() => setKorinish("togarak")} />;
  }

  if (korinish === "bogcha" || korinish === "bogcha_workspace") {
    return (
      <div className="org-v17-workspace-wrap">
        <MuassasaV17ReadOnlyBanner organization={aktivMuassasa} />
        <React.Suspense fallback={<div className="px-5 pt-16 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>}>
          <KindergartenWorkspace
            token={token}
            apiBase={API_BASE}
            initialWorkspace={aktivMuassasa?.turi === "bogcha" ? aktivMuassasa : null}
            onBack={() => setKorinish("togarak")}
            onLegacy={() => setKorinish("bogcha_legacy")}
            assignedOnly={!foydalanuvchi?.is_admin}
            canCreateInstitution={Boolean(foydalanuvchi?.is_admin)}
          />
        </React.Suspense>
      </div>
    );
  }

  if (korinish === "bogcha_legacy") {
    return <BogchaGuruhim token={token} onOrtga={() => setKorinish("bogcha_workspace")} />;
  }

  if (korinish === "institut_workspace" || korinish === "universitet") {
    return (
      <div className="org-v17-workspace-wrap">
        <MuassasaV17ReadOnlyBanner organization={aktivMuassasa} />
        <React.Suspense fallback={<div className="px-5 pt-16 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>}>
          <InstituteWorkspace
            token={token}
            apiBase={API_BASE}
            initialWorkspace={aktivMuassasa?.turi === "universitet" ? aktivMuassasa : null}
            onBack={() => setKorinish("togarak")}
            onLegacy={() => setKorinish("universitet_legacy")}
            assignedOnly={!foydalanuvchi?.is_admin}
            canCreateInstitution={Boolean(foydalanuvchi?.is_admin)}
          />
        </React.Suspense>
      </div>
    );
  }

  if (korinish === "universitet_legacy") {
    return <UniversitetGuruhimBilimi token={token} onOrtga={() => setKorinish("institut_workspace")} />;
  }

  if (yuklanmoqda) {
    return <div className="px-5 pt-16 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>;
  }

  if (holat === "yaratish" && yangiRejaQurishOchiq) {
    return <RejaDetali token={token} rejaId={yangiRejaQurishOchiq}
      onOrtga={() => { const rid = yangiRejaQurishOchiq; setYangiRejaQurishOchiq(null); rejalarniQaytaYukla(); setYangiTanlanganRejaId(rid); }} />;
  }

  if (holat === "yaratish") {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => setHolat("togaraklar")} className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Ortga")}/></button>
        <h1 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{yangiGuruhTuri === "repetitor" ? __kbUi("Yangi repetitor guruhi") : __kbUi("Yangi to'garak")}</h1>
        <p className="text-sm mb-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bot va saytda bir xil ko'rinadi · eng ko'pi ")}{__kbUi(CLUB_STUDENT_LIMIT)}{__kbUi(" o'quvchi")}</p>

        {togarakKvota && !togarakKvota.admin && (
          <div className="rounded-2xl p-4 mb-4 border" style={{ backgroundColor: kvotaBloklangan ? "#FDF3E0" : "#E7F4EE", borderColor: kvotaBloklangan ? "#E7BD73" : "#A9D8C5" }}>
            <p className="text-sm font-bold" style={{ color: kvotaBloklangan ? "#8A5A1C" : "#28735A" }}>
              {kvotaBloklangan ? __kbUi("Bepul guruh ishlatilgan") : __kbUi("Birinchi shaxsiy guruh bepul")}
            </p>
            <p className="text-xs mt-1 leading-relaxed" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
              {kvotaBloklangan
                ? __kbUi(`Ikkinchi to'garak yoki repetitor guruhi — ${SECOND_CLUB_PRICE_UZS.toLocaleString(__kbLocaleTag())} so'm. To'lov oynasi keyingi bosqichda ulanadi.`)
                : __kbUi(`Bitta shaxsiy guruhni bepul ochasiz. Har bir guruhda qat'iy ${CLUB_STUDENT_LIMIT} ta o'rin bor.`)}
            </p>
          </div>
        )}

        <div className="rounded-2xl p-5 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("To'garak turi")}</label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-4">
            <button type="button" onClick={() => { setYangiTuri("oddiy"); setYangiGuruhTuri("togarak"); }}
              className="rounded-xl p-3 text-left border-2"
              style={{ borderColor: yangiTuri === "oddiy" && yangiGuruhTuri === "togarak" ? "#1B4B7A" : "#E5E1D8", backgroundColor: yangiTuri === "oddiy" && yangiGuruhTuri === "togarak" ? "#EAF1F7" : "#FFFFFF" }}>
              <p className="text-sm font-semibold mb-0.5" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>🎓 <InterfaceText text={__kbUi("Oddiy")}/></p>
              <p className="text-[11px]" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Siz jonli dars o'tasiz, kalendar bilan")}</p>
            </button>
            <button type="button" onClick={() => { setYangiTuri("avto"); setYangiGuruhTuri("togarak"); }}
              className="rounded-xl p-3 text-left border-2"
              style={{ borderColor: yangiTuri === "avto" ? "#8B5FBF" : "#E5E1D8", backgroundColor: yangiTuri === "avto" ? "#F3EEFA" : "#FFFFFF" }}>
              <p className="text-sm font-semibold mb-0.5" style={{ color: "#8B5FBF" }}>{__kbUi("🤖 Avto")}</p>
              <p className="text-[11px]" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("O'quvchi mustaqil, kitob orqali o'qiydi")}</p>
            </button>
            <button type="button" onClick={() => { setYangiTuri("oddiy"); setYangiGuruhTuri("repetitor"); setYangiMaxsusSinf(true); setYangiSinfTuri("repetitor"); setYangiSinf(""); }}
              className="rounded-xl p-3 text-left border-2"
              style={{ borderColor: yangiGuruhTuri === "repetitor" ? "#28735A" : "#E5E1D8", backgroundColor: yangiGuruhTuri === "repetitor" ? "#E7F4EE" : "#FFFFFF" }}>
              <p className="text-sm font-semibold mb-0.5" style={{ color: "#28735A" }}>{__kbUi("🧑‍🏫 Repetitor")}</p>
              <p className="text-[11px]" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Yakka ustozning dars guruhi va reja yo'li")}</p>
            </button>
          </div>

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("To'garak nomi")}</label>
          <input type="text" value={yangiNomi} onChange={(e) => setYangiNomi(e.target.value)}
            placeholder={__kbUi("masalan: Matematik to'garak")}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
            style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Sinf / Guruh / Grupa / Repetitor")}</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 rounded-2xl p-1 gap-0.5 mb-2" style={{ backgroundColor: "#F0EDE5" }}>
            <button type="button" onClick={() => { setYangiMaxsusSinf(false); setYangiSinfMatni(""); setYangiGuruhTuri("togarak"); }}
              className="flex-1 py-2.5 rounded-full text-xs font-semibold"
              style={!yangiMaxsusSinf ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>🏫 <InterfaceText text={__kbUi("Sinf")}/></button>
            <button type="button" onClick={() => { setYangiMaxsusSinf(true); setYangiSinfTuri("guruh"); setYangiGuruhTuri("togarak"); setYangiSinf(""); }}
              className="flex-1 py-2.5 rounded-full text-xs font-semibold"
              style={(yangiMaxsusSinf && yangiSinfTuri === "guruh") ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>🧸 <InterfaceText text={__kbUi("Guruh")}/></button>
            <button type="button" onClick={() => { setYangiMaxsusSinf(true); setYangiSinfTuri("grupa"); setYangiGuruhTuri("togarak"); setYangiSinf(""); }}
              className="flex-1 py-2.5 rounded-full text-xs font-semibold"
              style={(yangiMaxsusSinf && yangiSinfTuri === "grupa") ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>{__kbUi("🎓 Grupa")}</button>
            <button type="button" onClick={() => { setYangiMaxsusSinf(true); setYangiSinfTuri("repetitor"); setYangiGuruhTuri("repetitor"); setYangiTuri("oddiy"); setYangiSinf(""); }}
              className="py-2.5 rounded-full text-xs font-semibold"
              style={(yangiMaxsusSinf && yangiSinfTuri === "repetitor") ? { backgroundColor: "#fff", color: "#28735A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>{__kbUi("🧑‍🏫 Repetitor")}</button>
          </div>
          {!yangiMaxsusSinf ? (
            <div className="grid grid-cols-6 gap-1.5 mb-3">
              {Array.from({ length: 11 }, (_, i) => String(i + 1)).map((n) => (
                <button key={n} type="button" onClick={() => setYangiSinf(n)}
                  className="py-2.5 rounded-lg border text-sm font-semibold text-center"
                  style={{
                    borderColor: yangiSinf === n ? "#1B4B7A" : "#E5E1D8",
                    backgroundColor: yangiSinf === n ? "#1B4B7A" : "#FFFFFF",
                    color: yangiSinf === n ? "#FFFFFF" : "#5A5648",
                  }}>
                  {n}
                </button>
              ))}
            </div>
          ) : (
            <>
              {togarakSinflariYuklanmoqda ? (
                <div className="py-3"><Loader2 size={16} className="animate-spin" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} /></div>
              ) : togarakSinflari.length > 0 ? (
                <div className="flex gap-1.5 flex-wrap mb-2">
                  {togarakSinflari.map((s) => (
                    <button key={s} type="button" onClick={() => setYangiSinfMatni(s)}
                      className="px-3 py-2 rounded-lg border text-sm font-medium"
                      style={{
                        borderColor: yangiSinfMatni === s ? "#1B4B7A" : "#E5E1D8",
                        backgroundColor: yangiSinfMatni === s ? "#1B4B7A" : "#FFFFFF",
                        color: yangiSinfMatni === s ? "#FFFFFF" : "#5A5648",
                      }}>
                      {s}
                    </button>
                  ))}
                </div>
              ) : null}
              {meningSinflarim.filter((s) => !togarakSinflari.includes(s)).length > 0 && (
                <>
                  <p className="text-xs mb-1.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Avval o'zingiz yozgan ")}{__kbUi(groupTypeLabel(yangiSinfTuri).toLowerCase())}{__kbUi("lar:")}</p>
                  <div className="flex gap-1.5 flex-wrap mb-2">
                    {meningSinflarim.filter((s) => !togarakSinflari.includes(s)).map((s) => (
                      <button key={s} type="button" onClick={() => setYangiSinfMatni(s)}
                        className="px-3 py-2 rounded-lg border text-sm font-medium"
                        style={{
                          borderColor: yangiSinfMatni === s ? "#1B4B7A" : "#E5E1D8",
                          backgroundColor: yangiSinfMatni === s ? "#1B4B7A" : "#FFFFFF",
                          color: yangiSinfMatni === s ? "#FFFFFF" : "#5A5648",
                        }}>
                        {s}
                      </button>
                    ))}
                  </div>
                </>
              )}
              <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
                {(togarakSinflari.length > 0 || meningSinflarim.length > 0) ? __kbUi(`yoki yangi ${groupTypeLabel(yangiSinfTuri).toLowerCase()} nomini kiriting`) : __kbUi(`${groupTypeLabel(yangiSinfTuri)} nomini kiriting`)}
              </label>
              <input type="text" value={yangiSinfMatni} onChange={(e) => setYangiSinfMatni(e.target.value)}
                placeholder={yangiSinfTuri === "grupa" ? __kbUi("masalan: 205-guruh, 3-kurs") : yangiSinfTuri === "repetitor" ? __kbUi("masalan: IELTS B2 kechki guruh") : __kbUi("masalan: Abituriyent, 3-4, IDUM tayyorlov")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
                style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            </>
          )}

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Fan")}/></label>
          {!(yangiMaxsusSinf ? yangiSinfMatni : yangiSinf) ? (
            <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Avval sinfni tanlang")}</p>
          ) : yangiFanOzicha ? (
            <>
              {meningFanlarim.length > 0 && (
                <>
                  <p className="text-xs mb-1.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Avval o'zingiz yozgan fanlar:")}</p>
                  <div className="flex gap-1.5 flex-wrap mb-2">
                    {meningFanlarim.map((f) => (
                      <button key={f} type="button" onClick={() => setYangiFan(f)}
                        className="px-3 py-1.5 rounded-lg border text-xs font-medium"
                        style={{
                          borderColor: yangiFan === f ? "#1B4B7A" : "#E5E1D8",
                          backgroundColor: yangiFan === f ? "#1B4B7A" : "#FFFFFF",
                          color: yangiFan === f ? "#FFFFFF" : "#5A5648",
                        }}>
                        {f}
                      </button>
                    ))}
                  </div>
                </>
              )}
              <input type="text" value={yangiFan} onChange={(e) => setYangiFan(e.target.value)}
                placeholder={__kbUi("Bitta so'z, masalan: Robototexnika")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              <button type="button" onClick={() => { setYangiFanOzicha(false); setYangiFan(""); }}
                className="text-xs font-medium mb-3" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("← Ro'yxatdan tanlashga qaytish")}</button>
            </>
          ) : sinfFanlariYuklanmoqda ? (
            <div className="py-3 mb-2"><Loader2 size={16} className="animate-spin" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} /></div>
          ) : (
            <>
              <div className="flex gap-1.5 flex-wrap mb-2">
                {(sinfFanlari.length > 0 ? sinfFanlari : BARCHA_MAKTAB_FANLARI).map((f) => (
                  <button key={f} type="button" onClick={() => setYangiFan(f)}
                    className="px-3 py-2 rounded-lg border text-sm font-medium"
                    style={{
                      borderColor: yangiFan === f ? "#1B4B7A" : "#E5E1D8",
                      backgroundColor: yangiFan === f ? "#1B4B7A" : "#FFFFFF",
                      color: yangiFan === f ? "#FFFFFF" : "#5A5648",
                    }}>
                    {f}
                  </button>
                ))}
              </div>
              <button type="button" onClick={() => { setYangiFanOzicha(true); setYangiFan(""); }}
                className="text-xs font-medium mb-3" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Ro'yxatda yo'q fan — o'zim yozaman →")}</button>
            </>
          )}
          {sinfFanlari.length === 0 && (yangiMaxsusSinf ? yangiSinfMatni : yangiSinf) && !sinfFanlariYuklanmoqda && !yangiFanOzicha && (
            <p className="text-xs -mt-2 mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bu guruh uchun hali mavzu/test yo'q — fan tanlansa, keyinroq shablon orqali test qo'shishingiz mumkin.")}</p>
          )}

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Topik mavzu rejasi")}</label>
          <p className="text-xs mb-2" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Reja — o'quvchi o'rganadigan mavzularning tartibli yo'li. Bir marta tuzib, boshqa guruhlarda ham qayta ishlatasiz.")}</p>
          {!(yangiMaxsusSinf ? yangiSinfMatni : yangiSinf) ? (
            <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Avval sinfni tanlang")}</p>
          ) : !yangiFan ? (
            <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Avval fanni tanlang")}</p>
          ) : yangiRejalarYuklanmoqda ? (
            <div className="py-3 mb-3"><Loader2 size={16} className="animate-spin" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} /></div>
          ) : (
            <>
              {yangiMavjudRejalar.length > 0 && (
                <div className="space-y-1.5 mb-3">
                  {yangiMavjudRejalar.map((r) => (
                    <button key={r.id} type="button" onClick={() => setYangiTanlanganRejaId(r.id)}
                      className="w-full text-left rounded-xl p-3 border-2 flex items-center justify-between"
                      style={yangiTanlanganRejaId === r.id
                        ? { borderColor: "#1B4B7A", backgroundColor: "#EAF1F7" }
                        : { borderColor: "#E5E1D8", backgroundColor: "#FFFFFF" }}>
                      <span className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{r.nomi}</span>
                      <span className="text-xs shrink-0" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{r.mavzu_soni}{__kbUi(" ta mavzu")}</span>
                    </button>
                  ))}
                </div>
              )}
              <div className="flex gap-2 mb-2">
                <input type="text" value={yangiRejaNomi} onChange={(e) => setYangiRejaNomi(e.target.value)}
                  placeholder={__kbUi("Yangi reja nomi, masalan: 9-sinf Algebra")}
                  className="flex-1 px-3.5 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                <button type="button" onClick={yangiRejaYaratishBoshla} disabled={yangiRejaYaratilmoqda || !yangiRejaNomi.trim()}
                  className="px-4 py-2.5 rounded-xl font-semibold text-white text-sm shrink-0"
                  style={{ backgroundColor: "#1B4B7A", opacity: (yangiRejaYaratilmoqda || !yangiRejaNomi.trim()) ? 0.6 : 1 }}>
                  {yangiRejaYaratilmoqda ? __kbUi("...") : __kbUi("+ Yaratish")}
                </button>
              </div>
              {yangiMavjudRejalar.length === 0 && (
                <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali reja yo'q — yangi yarating, keyin mavzularni tartib bilan qo'shasiz.")}</p>
              )}
              {yangiTanlanganRejaId && (
                <p className="text-xs mb-3" style={{ color: "#3B6D11" }}>{__kbUi("✓ Reja tanlandi — shu rejadagi mavzular avtomatik ulanadi.")}</p>
              )}
              {!yangiTanlanganRejaId && (
                <button type="button" onClick={() => setYangiTanlanganRejaId(null)} className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hozircha rejasiz davom etaman →")}</button>
              )}
            </>
          )}

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Qo'shilish paroli (ixtiyoriy)")}</label>
          <input type="text" value={yangiParol} onChange={(e) => setYangiParol(e.target.value)}
            placeholder={__kbUi("o'quvchilar shu bilan qo'shiladi")}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
            style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Maks. talaba")}</label>
              <input type="number" min="1" max={CLUB_STUDENT_LIMIT} value={yangiMaxTalaba} onChange={(e) => setYangiMaxTalaba(e.target.value)}
                placeholder={__kbUi(String(CLUB_STUDENT_LIMIT))}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm"
                style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            </div>
            <div>
              <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Oylik (so'm)")}</label>
              <input type="number" min="0" value={yangiOylikSumma} onChange={(e) => setYangiOylikSumma(e.target.value)}
                placeholder={__kbUi("50000")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm"
                style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            </div>
          </div>

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Universitet guruhi (ixtiyoriy — agar bu kursni ma'lum guruh uchun o'qitsangiz)")}</label>
          {tanlanganUniGuruh ? (
            <div className="flex items-center justify-between px-3.5 py-2.5 rounded-xl border mb-3" style={{ borderColor: "#1B4B7A", backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
              <span className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
                🎓 {tanlanganUniGuruh.nomi}{tanlanganUniGuruh.kurs ? __kbUi(` · ${tanlanganUniGuruh.kurs}-kurs`) : __kbUi("")}
              </span>
              <button onClick={() => setTanlanganUniGuruh(null)} className="text-xs font-medium" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>✕</button>
            </div>
          ) : (
            <div className="mb-3">
              <input type="text" value={uniGuruhIzlash} onChange={(e) => setUniGuruhIzlash(e.target.value)}
                placeholder={__kbUi("Guruh nomini yozing (masalan: 201-guruh)...")}
                className="w-full px-3.5 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
              {uniGuruhNatijalar.length > 0 && (
                <div className="mt-1.5 space-y-1">
                  {uniGuruhNatijalar.map((g) => (
                    <button key={g.id} onClick={() => { setTanlanganUniGuruh(g); setUniGuruhIzlash(""); setUniGuruhNatijalar([]); }}
                      className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-left" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                      <span className="text-sm" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{g.nomi}</span>
                      <span className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{g.kafedra_nomi}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}

          <button onClick={yaratishSaqla} disabled={yaratilmoqda || kvotaBloklangan}
            className="w-full py-3 rounded-xl font-semibold text-white text-sm flex items-center justify-center gap-2"
            style={{ backgroundColor: kvotaBloklangan ? "#B0AA98" : "#1B4B7A", opacity: yaratilmoqda ? 0.7 : 1 }}>
            {yaratilmoqda ? <Loader2 size={16} className="animate-spin" /> : kvotaBloklangan ? __kbUi(`Ikkinchi guruh — ${SECOND_CLUB_PRICE_UZS.toLocaleString(__kbLocaleTag())} so'm (tez orada)`) : yangiGuruhTuri === "repetitor" ? __kbUi("Repetitor guruhini yaratish") : __kbUi("To'garak yaratish")}
          </button>
        </div>
      </div>
    );
  }

  if (holat === "azolar") {
    return (
      <div className="px-5 pt-6 pb-4">
        <button onClick={() => setHolat("kalendar_reja")}
          className="flex items-center gap-2 mb-4 -ml-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><span className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}><ChevronLeft size={15} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} /></span><InterfaceText text={__kbUi("Ortga")}/></button>
        <h1 className="text-xl font-bold mb-3" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{tanlangan.nomi}</h1>
        <div className="grid grid-cols-2 gap-2 mb-4">
          <button onClick={() => setHolat("mavzular_boshqarish")} className="rounded-2xl bg-white border flex items-center gap-2.5 px-3.5 py-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <span className="w-8 h-8 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: "#EAF3DE" }}>
              <BookOpen size={16} style={{ color: "#3B6D11" }} />
            </span>
            <span className="text-xs font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}><InterfaceText text={__kbUi("Mavzular")}/></span>
          </button>
          <button onClick={() => setHolat("sozlamalar")} className="rounded-2xl bg-white border flex items-center gap-2.5 px-3.5 py-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <span className="w-8 h-8 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: "#FDF3E0" }}>
              <Settings size={16} style={{ color: "#8A5A1C" }} />
            </span>
            <span className="text-xs font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}><InterfaceText text={__kbUi("Sozlamalar")}/></span>
          </button>
        </div>
        {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}

        {kutilayotganAzolar.length > 0 && (
          <div className="rounded-2xl p-4 mb-4" style={{ backgroundColor: "#FDF3E0", border: "1px solid #C89B3C" }}>
            <p className="text-xs font-bold mb-3" style={{ color: "#8A5A1C" }}>{__kbUi("⏳ Kutilayotgan so'rovlar (")}{kutilayotganAzolar.length})</p>
            <div className="space-y-2">
              {kutilayotganAzolar.map((a) => (
                <div key={a.azolik_id} className="flex items-center justify-between gap-2 rounded-xl bg-white px-3.5 py-2.5">
                  <span className="text-sm font-medium truncate" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{a.full_name}</span>
                  <div className="flex gap-1.5 shrink-0">
                    <button onClick={() => azoTasdiqla(a.azolik_id)} disabled={tanlanganGuruhToliq}
                      className="text-xs font-semibold px-3 py-1.5 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed" style={{ backgroundColor: "#EAF3DE", color: "#3B6D11" }}>
                      {tanlanganGuruhToliq ? __kbUi(`${tanlanganSigim}/${tanlanganSigim} — joy yo'q`) : __kbUi("✓ Tasdiqlash")}
                    </button>
                    <button onClick={() => azoRadEt(a.azolik_id)}
                      className="text-xs font-semibold px-3 py-1.5 rounded-lg" style={{ backgroundColor: "#FCEBEB", color: "#A32D2D" }}>✕ <InterfaceText text={__kbUi("Rad etish")}/></button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {azolar.length === 0 ? (
          <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bu to'garakda hali a'zo yo'q.")}</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {azolar.map((a) => (
              <div key={a.user_id} className="rounded-2xl bg-white border overflow-hidden" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                <button onClick={() => (bahoQoyilayotgan === a.user_id ? setBahoQoyilayotgan(null) : bahoBoshla(a))}
                  className="w-full flex items-center justify-between px-4 py-3.5">
                  <span className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{a.full_name}</span>
                  <span className="text-sm font-semibold" style={{ color: a.oxirgi_baho != null ? "#2D8B8B" : "#B0AA98" }}>
                    {a.oxirgi_baho != null ? __kbUi(`${a.oxirgi_baho}`) : __kbUi("Baholanmagan")}
                  </span>
                </button>
                {bahoQoyilayotgan === a.user_id && (
                  <div className="px-4 pb-4 pt-1 space-y-2.5">
                    <select value={bahoTopicCode} onChange={(e) => setBahoTopicCode(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl border text-sm bg-white"
                      style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", color: bahoTopicCode ? "#2B2B2B" : "#8A8578" }}>
                      <option value="">{__kbUi("Baholanayotgan mavzuni tanlang")}</option>
                      {bahoMavzulari.map((m, index) => (
                        <option key={m.topic_code} value={m.topic_code}>{__kbUi(formatTopicTitle(index, m))}</option>
                      ))}
                    </select>
                    <input type="number" min="0" max="100" value={bahoQiymati}
                      onChange={(e) => setBahoQiymati(e.target.value)}
                      placeholder={__kbUi("Baho (0-100)")}
                      className="w-full px-3.5 py-2.5 rounded-xl border text-sm"
                      style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                    <input type="text" value={izohQiymati} onChange={(e) => setIzohQiymati(e.target.value)}
                      placeholder={__kbUi("Izoh (ixtiyoriy)")}
                      className="w-full px-3.5 py-2.5 rounded-xl border text-sm"
                      style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                    <button onClick={() => bahoSaqla(a.user_id)}
                      className="w-full py-2.5 rounded-xl font-semibold text-white text-sm"
                      style={{ backgroundColor: "#1B4B7A" }}><InterfaceText text={__kbUi("Saqlash")}/></button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (holat === "kalendar_reja") {
    return (
      <TogarakKalendarReja token={token} togarakId={tanlangan.id} togarakNomi={tanlangan.nomi}
        onOrtga={() => { setHolat("togaraklar"); setTanlangan(null); setBahoQoyilayotgan(null); }}
        onAzolar={() => setHolat("azolar")}
        onJurnal={() => setHolat("jurnal")}
        onMavzular={() => setHolat("mavzular_boshqarish")}
        onSozlamalar={() => setHolat("sozlamalar")} />
    );
  }

  if (holat === "jurnal") {
    return <TogarakJurnal apiBase={API_BASE} token={token} togarakId={tanlangan.id} onOrtga={() => setHolat("kalendar_reja")} />;
  }

  if (holat === "mavzular_boshqarish") {
    return <TogarakMavzularBoshqarish token={token} togarakId={tanlangan.id} onOrtga={() => setHolat("kalendar_reja")} />;
  }

  if (holat === "sozlamalar") {
    return <TogarakGuruhSozlamalari token={token} togarak={tanlangan} onOrtga={() => setHolat("kalendar_reja")} onOchirildi={() => window.location.reload()} />;
  }

  // holat === "togaraklar"
  return (
    <div className="px-5 pt-6 pb-4">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Guruhlarim")}</h1>
      </div>
      {/* REV96: to'garaklar endi eng tepada — qidirib yurish shart emas */}
      <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi(`Har guruhda ${CLUB_STUDENT_LIMIT} tagacha o‘quvchi. Guruhni bossangiz — o‘quvchilar, darslar (mavzular), davomat va to‘lovlar.`)}</p>
      <div className="grid grid-cols-2 gap-2 mb-3">
        <button onClick={() => yaratishniOch()} className="rounded-2xl px-3 py-3 text-sm font-bold text-white" style={{ backgroundColor: "#C89B3C" }}>+ {__kbUi("To‘garak ochish")}</button>
        <button onClick={() => yaratishniOch({ guruhTuri: "repetitor", guruhMaqsadi: "repetitor" })} className="rounded-2xl px-3 py-3 text-sm font-bold text-white" style={{ backgroundColor: "#28735A" }}>+ {__kbUi("Repetitor guruhi")}</button>
      </div>
      {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
      {togaraklar.length === 0 ? (
        <button onClick={() => yaratishniOch()}
          className="w-full rounded-2xl p-8 text-center border-2 border-dashed"
          style={{ borderColor: "#C4BFAF" }}>
          <p className="text-sm font-medium mb-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Hali to'garagingiz yo'q")}</p>
          <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bosib, birinchisini yarating")}</p>
        </button>
      ) : (
        <div className="space-y-2.5 mb-5">
          {togaraklar.map((t) => (
            <button key={t.id} onClick={() => togarakOch(t)}
              className="w-full flex items-center justify-between px-4 py-4 rounded-2xl bg-white border text-left"
              style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <div>
                <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{t.nomi}</p>
                <p className="text-xs mt-0.5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi(groupTypeLabel(t.guruh_turi))} · {t.fan}</p>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-full" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
                {t.azo_soni || 0}/{__kbUi(normalizedClubCapacity(t.max_talaba))}{__kbUi(" o‘quvchi")}</span>
            </button>
          ))}
        </div>
      )}
      <h2 className="text-sm font-bold mt-5 mb-2" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Ish joyi va AI vositalari")}</h2>

      {faolSamariMuassasalar.length > 1 && (
        <div className="flex gap-2 mb-3 overflow-x-auto pb-1">
          {faolSamariMuassasalar.map((m) => {
            const itemKey = muassasaBarqarorKaliti(m);
            return <button key={itemKey} onClick={() => setAktivMuassasaKaliti(itemKey)}
              className="shrink-0 px-3.5 py-2 rounded-full text-xs font-semibold whitespace-nowrap"
              style={itemKey === muassasaBarqarorKaliti(aktivMuassasa) ? { backgroundColor: "#1B4B7A", color: "#fff" } : { backgroundColor: "#F7F5F0", color: "#5A5648" }}>
              {MUASSASA_IKONKA[m.turi] || __kbUi("📍")} {m.muassasa_nomi || (m.turi === "maktab" ? uiT("Maktabim") : m.turi === "markaz" ? uiT("Markazim") : m.turi === "bogcha" ? uiT("Bog'cham") : uiT("Institutim"))}
            </button>;
          })}
        </div>
      )}

      {__kbUi((() => {
        const bandlar = [];
        const muassasaBandi = {
          maktab: { kalit: "maktab_workspace", nom: "Maktab ish maydoni", ikon: Building2, fon: "#E8F2FF", rang: "#185FA5" },
          markaz: { kalit: "markaz_workspace", nom: "Markaz ish maydoni", ikon: GraduationCap, fon: "#E7F7EE", rang: "#167D4A" },
          bogcha: { kalit: "bogcha_workspace", nom: "Bog‘cha ish maydoni", ikon: Baby, fon: "#FFF0F4", rang: "#B53B67" },
          universitet: { kalit: "institut_workspace", nom: "Institut ish maydoni", ikon: GraduationCap, fon: "#F1EEFF", rang: "#6146A5" },
        }[aktivMuassasa?.turi];
        if (aktivMuassasa?.turi === "maktab") {
          bandlar.push({ kalit: "oqituvchi_bosh_ekran", nom: "Bugungi ta’lim maydoni", ikon: CalendarCheck, fon: "#EAF1F7", rang: "#1B4B7A" });
        }
        if (muassasaBandi) bandlar.push(muassasaBandi);

        if (aktivMuassasa?.turi === "maktab" && MUASSASA_BOSHQARUVCHI_LAVOZIM.maktab.includes(aktivMuassasa.lavozim)) {
          bandlar.push(
            { kalit: "kutubxona", nom: "Kutubxona", ikon: BookOpen, fon: "#EAF3DE", rang: "#3B6D11" },
            { kalit: "moliya", nom: "Moliya", ikon: Wallet, fon: "#FDF3E0", rang: "#8A5A1C" },
            { kalit: "hujjatlar", nom: "Hujjatlar", ikon: Folder, fon: "#F3EEFA", rang: "#8B5FBF" },
            { kalit: "rejalashtirish", nom: "Rejalashtirish", ikon: Calendar, fon: "#EAF1F7", rang: "#1B4B7A" },
            { kalit: "fanlar_tahlili", nom: "Fanlar tahlili", ikon: BarChart3, fon: "#FCEBEB", rang: "#A32D2D" },
          );
        }
        if (aktivMuassasa?.turi === "maktab" && aktivMuassasa.lavozim === "psixolog") {
          bandlar.push({ kalit: "psixolog", nom: "Psixolog", ikon: Brain, fon: "#F3EEFA", rang: "#8B5FBF" });
        }
        bandlar.push(
          {
            kalit: "muassasa_v17",
            nom: "Yangi muassasa",
            ikon: Building2,
            fon: "#E7F7F4",
            rang: "#087F79",
          },
          {
            kalit: "repetitor_workspace",
            nom: "Repetitorlik ochish",
            ikon: UserRoundPlus,
            fon: "#FFF4DF",
            rang: "#A05A00",
            amal: () => onOpenCourses ? onOpenCourses("teaching") : yaratishniOch({ guruhTuri: "repetitor", guruhMaqsadi: "repetitor" }),
          },
          { kalit: "oqituvchi_analitika", nom: "Statistikalar", ikon: BarChart3, fon: "#EAF1F7", rang: "#1B4B7A" },
          { kalit: "rejalarim", nom: "Rejalarim", ikon: ClipboardList, fon: "#EAF3DE", rang: "#3B6D11" },
          { kalit: "ai_yordamchi", nom: "AI Yordamchi", ikon: Bot, fon: "#F3EEFA", rang: "#8B5FBF" },
          { kalit: "ai_dars", nom: "AI Ochiq dars", ikon: Brain, fon: "#F3EEFA", rang: "#8B5FBF" },
          { kalit: "ai_togarak", nom: "AI To'garak reja", ikon: GraduationCap, fon: "#EEF7F5", rang: "#246D6D" },
        );
        return (
          <div className="grid grid-cols-2 gap-2 mb-4">
            {bandlar.map((b) => (
              <button key={b.kalit} onClick={() => (b.amal ? b.amal() : setKorinish(b.kalit))}
                className="rounded-2xl bg-white border flex items-center gap-2.5 px-3.5 py-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
                <span className="w-8 h-8 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: b.fon }}>
                  <b.ikon size={16} style={{ color: b.rang }} />
                </span>
                <span className="text-xs font-semibold text-left" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{b.nom}</span>
              </button>
            ))}
          </div>
        );
      })())}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// 5.5) OTA-ONA — farzand(lar)ning bilim darajasi
// ═══════════════════════════════════════════════════════════
function OtaOnaTab({ token, foydalanuvchi, rang }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [farzandlar, setFarzandlar] = useState([]);
  const [tanlanganBola, setTanlanganBola] = useState(null);
  const [bilimData, setBilimData] = useState(null);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [xato, setXato] = useState("");
  const [korinish, setKorinish] = useState("bilim"); // "bilim" | "ai_yordamchi" | "sogliq"
  const [sogliq, setSogliq] = useState(null);
  const [allergiyalar, setAllergiyalar] = useState("");
  const [qonGuruhi, setQonGuruhi] = useState("");
  const [aloqaIsmi, setAloqaIsmi] = useState("");
  const [aloqaTelefoni, setAloqaTelefoni] = useState("");
  const [boshqaEslatma, setBoshqaEslatma] = useState("");
  const [sogliqSaqlanmoqda, setSogliqSaqlanmoqda] = useState(false);
  const [sogliqSaqlandi, setSogliqSaqlandi] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/ota/${foydalanuvchi.user_id}/farzandlar`)
      .then((r) => r.json())
      .then((d) => {
        const royxat = d.farzandlar || [];
        setFarzandlar(royxat);
        if (royxat.length > 0) setTanlanganBola((oldin) => oldin || royxat[0].user_id);
        setYuklanmoqda(false);
      })
      .catch(() => { setXato("Farzandlar ro'yxatini yuklab bo'lmadi"); setYuklanmoqda(false); });
  }, [foydalanuvchi.user_id]);

  useEffect(() => {
    if (!tanlanganBola) return;
    setBilimData(null);
    fetch(`${API_BASE}/api/bola/${tanlanganBola}/bilim`)
      .then((r) => r.json())
      .then((d) => setBilimData(d))
      .catch(() => setBilimData(null));
    fetch(`${API_BASE}/api/bola/${tanlanganBola}/favqulodda_malumot?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => {
        setSogliq(d);
        setAllergiyalar(d.allergiyalar || ""); setQonGuruhi(d.qon_guruhi || "");
        setAloqaIsmi(d.aloqa_ismi || ""); setAloqaTelefoni(d.aloqa_telefoni || ""); setBoshqaEslatma(d.boshqa_eslatma || "");
      })
      .catch(() => {});
  }, [tanlanganBola, token]);

  const sogliqSaqla = async () => {
    setSogliqSaqlanmoqda(true); setSogliqSaqlandi(false);
    try {
      await fetch(`${API_BASE}/api/bola/favqulodda_malumot`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token, bola_user_id: tanlanganBola, allergiyalar: allergiyalar || undefined, qon_guruhi: qonGuruhi || undefined,
          aloqa_ismi: aloqaIsmi || undefined, aloqa_telefoni: aloqaTelefoni || undefined, boshqa_eslatma: boshqaEslatma || undefined,
        }),
      });
      setSogliqSaqlandi(true);
    } finally { setSogliqSaqlanmoqda(false); }
  };

  if (farzandlar.length === 0 && !yuklanmoqda) {
    return (
      <div className="px-5 pt-6 pb-4">
        <h1 className="text-2xl font-bold mb-5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Farzandim")}</h1>
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm font-medium mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Hali farzand ulanmagan")}</p>
          <p className="text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Profil bo'limidan farzandingizning kodi bilan ulang.")}</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="px-5 pt-6 pb-2">
        <h1 className="text-2xl font-bold mb-4" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Farzandim")}</h1>
        {farzandlar.length > 1 && (
          <div className="flex gap-2 flex-wrap mb-3">
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
        )}

        <div className="grid grid-cols-2 gap-2 mb-4">
          <button onClick={() => setKorinish(korinish === "ai_yordamchi" ? "bilim" : "ai_yordamchi")}
            className="rounded-2xl bg-white border flex items-center gap-2.5 px-3.5 py-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <span className="w-8 h-8 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: "#F3EEFA" }}>
              {korinish === "ai_yordamchi" ? <ChevronLeft size={16} style={{ color: "#8B5FBF" }} strokeWidth={2.5} /> : <Bot size={16} style={{ color: "#8B5FBF" }} />}
            </span>
            <span className="text-xs font-semibold text-left" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{korinish === "ai_yordamchi" ? uiT("Orqaga") : __kbUi("AI Yordamchi")}</span>
          </button>
          <button onClick={() => setKorinish(korinish === "sogliq" ? "bilim" : "sogliq")}
            className="rounded-2xl bg-white border flex items-center gap-2.5 px-3.5 py-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <span className="w-8 h-8 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: "#FCEBEB" }}>
              {korinish === "sogliq" ? <ChevronLeft size={16} style={{ color: "#A32D2D" }} strokeWidth={2.5} /> : <AlertTriangle size={16} style={{ color: "#A32D2D" }} />}
            </span>
            <span className="text-xs font-semibold text-left" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{korinish === "sogliq" ? uiT("Orqaga") : __kbUi("Favqulodda")}</span>
          </button>
        </div>

        {korinish !== "ai_yordamchi" && korinish !== "sogliq" && (
          <div className="rounded-xl px-4 py-3 mb-1 flex items-start gap-2.5" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
            <span className="text-base shrink-0">💡</span>
            <p className="text-xs" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Bu yerda farzandingizning ")}<b>{__kbUi("bilim darajasini")}</b>{__kbUi(", har fan bo'yicha ")}<b>{__kbUi("ta'lim yo'lini")}</b>{__kbUi(" (qaysi mavzular o'tilgan, qaysilari qolgan) va agar to'garakka a'zo bo'lsa — ")}<b>{__kbUi("to'garak yutuqlarini")}</b>{__kbUi(" ham kuzatib borishingiz mumkin. Yana farzand qo'shish yoki ulanishni uzish uchun — Profil bo'limiga o'ting.")}</p>
          </div>
        )}
      </div>
      {korinish === "ai_yordamchi" ? (
        <AiYordamchiBolimi token={token} onOrtga={() => setKorinish("bilim")} />
      ) : korinish === "sogliq" ? (
        <div className="px-5 pb-4">
          <p className="text-xs mb-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bu ma'lumot favqulodda holatda maktab xodimlariga tezkor ko'rinadi (sinf rahbari, rahbariyat).")}</p>
          <div className="rounded-2xl p-4 bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
            <label className="text-xs font-medium mb-1 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Allergiyalar")}</label>
            <input type="text" value={allergiyalar} onChange={(e) => setAllergiyalar(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            <label className="text-xs font-medium mb-1 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Qon guruhi")}</label>
            <input type="text" value={qonGuruhi} onChange={(e) => setQonGuruhi(e.target.value)} placeholder={__kbUi("masalan A+")}
              className="w-full px-3 py-2.5 rounded-lg border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            <label className="text-xs font-medium mb-1 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Favqulodda aloqa ismi")}</label>
            <input type="text" value={aloqaIsmi} onChange={(e) => setAloqaIsmi(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            <label className="text-xs font-medium mb-1 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Favqulodda aloqa telefoni")}</label>
            <input type="text" value={aloqaTelefoni} onChange={(e) => setAloqaTelefoni(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            <label className="text-xs font-medium mb-1 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Boshqa muhim eslatma")}</label>
            <input type="text" value={boshqaEslatma} onChange={(e) => setBoshqaEslatma(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            {sogliqSaqlandi && <p className="text-xs mb-2" style={{ color: "#3B6D11" }}>{__kbUi("✅ Saqlandi")}</p>}
            <button onClick={sogliqSaqla} disabled={sogliqSaqlanmoqda}
              className="w-full py-3 rounded-xl font-semibold text-white text-sm" style={{ backgroundColor: "#1B4B7A", opacity: sogliqSaqlanmoqda ? 0.7 : 1 }}>
              {sogliqSaqlanmoqda ? uiT("Saqlanmoqda...") : uiT("Saqlash")}
            </button>
          </div>
        </div>
      ) : yuklanmoqda ? (
        <div className="px-5 pt-10 text-center">
          <Loader2 size={28} className="animate-spin mx-auto mb-3" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} />
        </div>
      ) : xato ? (
        <p className="px-5 text-sm" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>
      ) : tanlanganBola ? (
        <>
          <div className="px-3 sm:px-5 pt-3">
            <FarzandFaollik apiBase={API_BASE} token={token} childId={tanlanganBola} />
            <MilitaryRoutine token={token} apiBase={API_BASE} childId={tanlanganBola} readOnly />
            {sinfTalabaMi(farzandlar.find((bola) => Number(bola.user_id) === Number(tanlanganBola))?.class) ? (
              <p className="rounded-2xl border bg-white p-4 text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("🎓 Farzandingiz talaba — paralar jadvalini o'zi boshqaradi, maktab jadvali tuzilmaydi.")}</p>
            ) : (
            <StudentScheduleWorkspace
              token={token}
              student={farzandlar.find((bola) => Number(bola.user_id) === Number(tanlanganBola)) || { user_id: tanlanganBola }}
              apiBase={API_BASE}
              readOnly
              compactTitle
            />
            )}
          </div>
          <BilimMarkazi
            token={token}
            data={bilimData}
            bolaId={tanlanganBola}
            viewer="parent"
            rang={rang}
            otaOnaUchun
            analyticsCompact
          />
        </>
      ) : null}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// 6) PROFIL — tahrirlash va rol almashtirish
// ═══════════════════════════════════════════════════════════
function ProfileAccordion({ icon, title, summary, children, nested = false }) {
  useKbInterfaceLocale();
  const [ochiq, setOchiq] = useState(false);
  return (
    <details
      className={`${nested ? "rounded-xl" : "rounded-2xl shadow-sm"} bg-white border mb-3 overflow-visible`}
      style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}
      onToggle={(event) => setOchiq(event.currentTarget.open)}
    >
      <summary
        className={`${nested ? "px-3.5 py-3" : "px-4 py-3.5"} flex items-center gap-3 cursor-pointer select-none [&::-webkit-details-marker]:hidden`}
        style={{ listStyle: "none" }}
      >
        <span className={`${nested ? "w-8 h-8" : "w-10 h-10"} rounded-xl flex items-center justify-center shrink-0 text-base`} style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>{icon}</span>
        <span className="flex-1 min-w-0">
          <b className="block text-sm" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{title}</b>
          {summary && <small className="block text-[11px] mt-0.5 truncate" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{summary}</small>}
        </span>
        <ChevronDown size={17} className="shrink-0 transition-transform" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)", transform: ochiq ? "rotate(180deg)" : "none" }} />
      </summary>
      <div className={`${nested ? "px-3.5 pb-3.5" : "px-4 pb-4"} border-t pt-3`} style={{ borderColor: "#F0ECE3" }}>
        {ochiq ? children : null}
      </div>
    </details>
  );
}

// Admin: "Kim nima yarata oladi" — taqdimot va to'garak yaratishni rollarga
// qarab ochish/yopish. Yopilganda foydalanuvchi shu yerdagi izohni ko'radi.
function AdminRuxsatlarBolimi({ token }) {
  useKbInterfaceLocale();
  const [data, setData] = useState(null);
  const [xato, setXato] = useState("");
  const [saqlanmoqda, setSaqlanmoqda] = useState("");
  const [xabar, setXabar] = useState("");
  useEffect(() => {
    fetch(`${API_BASE}/api/admin/xususiyat_ruxsatlari?token=${encodeURIComponent(token)}`)
      .then((r) => r.json()).then((d) => { if (d.xususiyatlar) setData(d); else setXato(d.detail || "Yuklab bo'lmadi"); })
      .catch(() => setXato("Ruxsatlarni yuklab bo'lmadi"));
  }, [token]);
  const yangila = (kod, patch) => setData((old) => ({ ...old, xususiyatlar: old.xususiyatlar.map((x) => (x.kod === kod ? { ...x, ...patch } : x)) }));
  const saqla = async (x) => {
    setSaqlanmoqda(x.kod); setXato(""); setXabar("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/xususiyat_ruxsatlari`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, xususiyat: x.kod, rollar: x.rollar, izoh: x.izoh || "" }),
      });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(d.detail || `Server xatosi (${res.status})`);
      setXabar(`${x.nomi} — saqlandi. O'zgarish darhol kuchga kiradi.`);
    } catch (e) { setXato(e.message); } finally { setSaqlanmoqda(""); }
  };
  if (xato && !data) return <p className="text-sm" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>;
  if (!data) return <div className="py-6 text-center"><Loader2 size={22} className="animate-spin mx-auto" style={{ color: "#1B4B7A" }} /></div>;
  return (
    <div className="space-y-3">
      <p className="text-xs" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Kalit yopiq bo'lsa, o'sha roldagi foydalanuvchi tugmani bosganda pastdagi ")}<b>{__kbUi("izoh")}</b>{__kbUi("ni ko'radi. Siz (admin) uchun hamma narsa doim ochiq.")}</p>
      {data.xususiyatlar.map((x) => (
        <div key={x.kod} className="rounded-2xl p-4 bg-white border shadow-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm font-semibold" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{x.kod === "taqdimot" ? __kbUi("🎞️") : __kbUi("🎯")} {x.nomi}</p>
          <p className="text-xs mt-0.5 mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{x.tavsif}</p>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(data.rol_nomlari).map(([rol, nom]) => {
              const on = !!x.rollar[rol];
              return (
                <button type="button" key={rol} role="switch" aria-checked={on} onClick={() => yangila(x.kod, { rollar: { ...x.rollar, [rol]: !on } })}
                  className="flex items-center justify-between gap-2 rounded-xl px-3 py-2.5 border text-left"
                  style={{ borderColor: on ? "#BFD9C7" : "#E5E1D8", backgroundColor: on ? "#EAF3DE" : "#F7F5F0" }}>
                  <span className="text-xs font-semibold" style={{ color: on ? "#3B6D11" : "#5A5648" }}>{nom}</span>
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-full" style={{ backgroundColor: on ? "#3B6D11" : "#8A8578", color: "#fff" }}>{on ? __kbUi("Ochiq") : __kbUi("Yopiq")}</span>
                </button>
              );
            })}
          </div>
          <label className="block mt-3">
            <span className="text-xs font-semibold" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Yopilganda ko'rinadigan izoh (ixtiyoriy)")}</span>
            <input value={x.izoh || ""} maxLength={300} onChange={(e) => yangila(x.kod, { izoh: e.target.value })}
              placeholder={__kbUi(`Masalan: ${x.nomi} faqat 1-oktabrdan ochiladi`)} className="w-full mt-1 px-3 py-2 rounded-xl border text-sm" style={{ borderColor: "#E5E1D8" }} />
          </label>
          <div className="flex items-center gap-3 mt-3">
            <button type="button" onClick={() => saqla(x)} disabled={saqlanmoqda === x.kod} className="px-4 py-2 rounded-xl text-sm font-semibold text-white" style={{ backgroundColor: "#1B4B7A", opacity: saqlanmoqda === x.kod ? 0.6 : 1 }}>{saqlanmoqda === x.kod ? __kbUi("…") : __kbUi("Saqlash")}</button>
            <button type="button" onClick={() => yangila(x.kod, { rollar: { ...x.standart } })} className="text-xs underline" style={{ color: "#8A8578" }}>{__kbUi("Standart holatga")}</button>
          </div>
        </div>
      ))}
      {xato && <p className="text-sm" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
      {xabar && <p className="text-sm" style={{ color: "#3B6D11" }}>✓ {xabar}</p>}
    </div>
  );
}

function ProfilTab({ token, foydalanuvchi, onYangilandi, onInstitutionJoined, adminKorinish, onKorinishOzgar, rang, onRolAlmashtir, onOquvchiKorinishi }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const profilRangi = rang || "#1B4B7A";
  const [ism, setIsm] = useState(foydalanuvchi?.full_name || "");
  const [rasmVersiyasi, setRasmVersiyasi] = useState(0); // yuklangach rasmni qayta so'ratish uchun
  const [rasmYuklanmoqda, setRasmYuklanmoqda] = useState(false);
  const [rasmXato, setRasmXato] = useState("");
  const rasmInputRef = useRef(null);
  const otaOnaKartaRef = useRef(null);

  const rasmTanlandi = async (e) => {
    const fayl = e.target.files?.[0];
    if (!fayl) return;
    setRasmYuklanmoqda(true); setRasmXato("");
    try {
      const forma = new FormData();
      forma.append("fayl", fayl);
      const res = await fetch(`${API_BASE}/api/profil_rasm_yukla?token=${encodeURIComponent(token)}`, {
        method: "POST", body: forma,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      onYangilandi({ ...foydalanuvchi, rasm_bormi: true });
      setRasmVersiyasi((v) => v + 1);
    } catch (err) {
      setRasmXato(err.message);
    } finally { setRasmYuklanmoqda(false); }
  };

  const [viloyat, setViloyat] = useState(foydalanuvchi?.region || "");
  const [tuman, setTuman] = useState(foydalanuvchi?.district || "");
  const [tugilganSana, setTugilganYil] = useState(foydalanuvchi?.tugilgan_sana || "");
  const [maktabRaqami, setMaktabRaqami] = useState(foydalanuvchi?.maktab_raqami || "");
  const [royxatdagiMaktab, setRoyxatdagiMaktab] = useState(
    foydalanuvchi?.maktab_id && foydalanuvchi?.maktab_nomi ? { id: foydalanuvchi.maktab_id, nomi: foydalanuvchi.maktab_nomi } : null
  );
  const [maktabTuri, setMaktabTuri] = useState(foydalanuvchi?.maktab_turi_kaliti || "oddiy");
  const [sinfSozlamalariOchiq, setSinfSozlamalariOchiq] = useState(false);
  const [sinf, setSinf] = useState(foydalanuvchi?.class ? String(foydalanuvchi.class).replace(/-sinf$/i, "") : "");
  const [sinfHarfi, setSinfHarfi] = useState(foydalanuvchi?.class_letter || "");
  const [talabaProfili, setTalabaProfili] = useState(foydalanuvchi?.talaba_profili || null);
  const [talabaOqimi, setTalabaOqimi] = useState(false);
  const [talabaChiqilmoqda, setTalabaChiqilmoqda] = useState(false);
  const talabaMi = !!talabaProfili || sinfTalabaMi(foydalanuvchi?.class);
  useEffect(() => {
    // Profil yuklanganda talaba ma'lumoti bo'lmasa (eski token) — alohida so'raymiz
    if (foydalanuvchi?.role !== "oquvchi" || talabaProfili || !sinfTalabaMi(foydalanuvchi?.class)) return;
    fetch(`${API_BASE}/api/talaba/profil?token=${encodeURIComponent(token)}`)
      .then((r) => r.json()).then((d) => { if (d.talaba_profili) setTalabaProfili(d.talaba_profili); }).catch(() => {});
  }, [foydalanuvchi?.role, foydalanuvchi?.class, talabaProfili, token]);
  const talabaSaqlandi = (d) => {
    if (d.profile) { setTalabaOqimi(false); if (onInstitutionJoined) onInstitutionJoined(d); return; }
    setTalabaProfili(d.talaba_profili || null); setTalabaOqimi(false); setSinf(d.sinf || ""); setSinfHarfi("");
    const yangiProfil = { ...foydalanuvchi, role: "oquvchi", class: d.sinf, class_letter: null, talaba_profili: d.talaba_profili, talaba_mi: true,
      universitet_id: d.talaba_profili?.universitet_id ?? foydalanuvchi?.universitet_id, education_ready: true };
    if (onInstitutionJoined) onInstitutionJoined({ profile: yangiProfil, result: { joy_nomi: d.talaba_profili?.universitet_nomi } });
    else onYangilandi(yangiProfil);
  };
  const talabadanChiqish = async () => {
    if (!window.confirm(__kbUi("Muassasadan chiqasizmi? Kurs mavzulari va testlari yopiladi, keyin 1–11 sinfni qayta tanlaysiz."))) return;
    setTalabaChiqilmoqda(true); setXato("");
    try {
      const res = await fetch(`${API_BASE}/api/talaba/profil?token=${encodeURIComponent(token)}`, { method: "DELETE" });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(d.detail || "Xato");
      setTalabaProfili(null); setSinf("");
      const yangiProfil = { ...foydalanuvchi, class: null, talaba_profili: null, talaba_mi: false };
      if (onInstitutionJoined) onInstitutionJoined({ profile: yangiProfil, result: { joy_nomi: null } }); else onYangilandi(yangiProfil);
    } catch (e) { setXato(e.message); } finally { setTalabaChiqilmoqda(false); }
  };
  const [jins, setJins] = useState(foydalanuvchi?.jins || "");
  const [ovozJinsi, setOvozJinsi] = useState(_ovozJinsiniTuzat(foydalanuvchi?.ovoz_jinsi || foydalanuvchi?.jins || "qiz"));
  const [oqituvchiFani, setOqituvchiFani] = useState(foydalanuvchi?.oqituvchi_fani || "");
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
  const [korinish, setKorinish] = useState("profil"); // "profil" | "rasmiy_sinf" | "kirish_kodi" | "togarak_mavzular" | "mening_kalendarim"
  const [tanlanganTogarak, setTanlanganTogarak] = useState(null);
  const [ochiladiganTopicCode, setOchiladiganTopicCode] = useState(null);

  const [otaKod, setOtaKod] = useState(null); // {kod, amal_qilish_daqiqasi} | null
  const [otaKodOlinmoqda, setOtaKodOlinmoqda] = useState(false);
  const [otaKodXato, setOtaKodXato] = useState("");
  const [otaOnalarim, setOtaOnalarim] = useState([]); // allaqachon ulangan ota-onalar

  useEffect(() => {
    if (foydalanuvchi?.role !== "oquvchi") return;
    fetch(`${API_BASE}/api/oquvchi/ota_onalarim?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => setOtaOnalarim(d.ota_onalar || []))
      .catch(() => {});
  }, [foydalanuvchi?.role, token]);

  const [farzandlar, setFarzandlar] = useState([]);
  const [farzandKodi, setFarzandKodi] = useState("");
  const [farzandQoshilmoqda, setFarzandQoshilmoqda] = useState(false);
  const [farzandXato, setFarzandXato] = useState("");
  const [farzandMuvaffaqiyat, setFarzandMuvaffaqiyat] = useState("");

  const farzandlarniYukla = () => {
    fetch(`${API_BASE}/api/ota/${foydalanuvchi.user_id}/farzandlar`)
      .then((r) => r.json())
      .then((d) => setFarzandlar(d.farzandlar || []))
      .catch(() => {});
  };

  useEffect(() => {
    if (foydalanuvchi?.role === "ota-ona") farzandlarniYukla();
  }, [foydalanuvchi?.role, foydalanuvchi?.user_id]);

  const farzandQoshish = async () => {
    if (!farzandKodi.trim()) return;
    setFarzandQoshilmoqda(true); setFarzandXato(""); setFarzandMuvaffaqiyat("");
    try {
      const res = await fetch(`${API_BASE}/api/ota/farzand_boglash?token=${encodeURIComponent(token)}&kod=${encodeURIComponent(farzandKodi.trim())}`, {
        method: "POST",
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setFarzandMuvaffaqiyat(data.holat === "allaqachon_ulangan" ? "Bu farzand allaqachon ulangan" : `✓ ${data.farzand_ismi} ulandi`);
      setFarzandKodi("");
      farzandlarniYukla();
    } catch (e) {
      setFarzandXato(e.message);
    } finally { setFarzandQoshilmoqda(false); }
  };

  const farzandniUzish = async (bolaId) => {
    try {
      await fetch(`${API_BASE}/api/ota/farzand_uzish?token=${encodeURIComponent(token)}&farzand_id=${bolaId}`, { method: "DELETE" });
      setFarzandlar((prev) => prev.filter((f) => f.user_id !== bolaId));
    } catch { /* jim */ }
  };

  const otaKodOl = async () => {
    setOtaKodOlinmoqda(true); setOtaKodXato("");
    try {
      const res = await fetch(`${API_BASE}/api/farzand/kod_yarat?token=${encodeURIComponent(token)}`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setOtaKod(data);
    } catch (e) {
      setOtaKodXato(e.message);
    } finally { setOtaKodOlinmoqda(false); }
  };

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
      const listResponse = await fetch(`${API_BASE}/api/mening_togaraklarim?token=${encodeURIComponent(token)}`, { cache: "no-store" });
      const listData = await listResponse.json();
      if (!listResponse.ok) throw new Error("So‘rov yuborildi, lekin ro‘yxat yangilanmadi. Profilni qayta oching.");
      setTogaraklarim(Array.isArray(listData.togaraklar) ? listData.togaraklar : []);
      setQoshilishMuvaffaqiyat(`"${data.togarak_nomi}" — so'rovingiz yuborildi, o'qituvchi tasdiqlashini kuting.`);
      setQoshilishParol("");
      setTimeout(() => setQoshilishMuvaffaqiyat(""), 5000);
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
          maktab_turi: foydalanuvchi?.role === "oquvchi" && !talabaMi ? maktabTuri : undefined,
          sinf: foydalanuvchi?.role === "oquvchi" && sinf && !talabaMi ? sinf : undefined,
          sinf_harfi: foydalanuvchi?.role === "oquvchi" && sinfHarfi && !talabaMi ? sinfHarfi : undefined,
          jins: (foydalanuvchi?.role === "oquvchi" || foydalanuvchi?.role === "oqituvchi") && jins ? jins : undefined,
          oqituvchi_fani: foydalanuvchi?.role === "oqituvchi" && oqituvchiFani ? oqituvchiFani : undefined,
          ovoz_jinsi: ovozJinsi,
          maktab_id: royxatdagiMaktab ? royxatdagiMaktab.id : undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      onYangilandi({
        ...foydalanuvchi, full_name: ism, region: viloyat, district: tuman,
        tugilgan_sana: tugilganSana, maktab_raqami: maktabRaqami,
        maktab_turi_kaliti: maktabTuri, class: talabaMi ? foydalanuvchi?.class : sinf, class_letter: talabaMi ? null : sinfHarfi,
        jins, oqituvchi_fani: oqituvchiFani, ovoz_jinsi: ovozJinsi,
        maktab_id: royxatdagiMaktab ? royxatdagiMaktab.id : foydalanuvchi?.maktab_id,
        maktab_nomi: royxatdagiMaktab ? royxatdagiMaktab.nomi : foydalanuvchi?.maktab_nomi,
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

  if (korinish === "rasmiy_sinf") {
    return <RasmiySinflarim token={token} onOrtga={() => setKorinish("profil")} />;
  }
  if (korinish === "kirish_kodi") {
    return <KirishKodiFormasi token={token} onOrtga={() => setKorinish("profil")} onComplete={onInstitutionJoined} />;
  }
  if (korinish === "mening_kalendarim") {
    return (
      <MeningKalendarim token={token} togarak={tanlanganTogarak}
        onOrtga={() => setKorinish(tanlanganTogarak?.turi === "avto" ? "profil" : "togarak_mavzular")}
        onMavzuOchish={(topicCode) => { setOchiladiganTopicCode(topicCode); setKorinish("togarak_mavzular"); }} />
    );
  }
  if (korinish === "togarak_mavzular") {
    return (
      <TogarakAzoMavzulari token={token} togarak={tanlanganTogarak} onOrtga={() => setKorinish("profil")}
        onKalendar={() => setKorinish("mening_kalendarim")}
        ochiladiganTopicCode={ochiladiganTopicCode} ochilganiBildir={() => setOchiladiganTopicCode(null)}
        foydalanuvchi={foydalanuvchi} />
    );
  }

  return (
    <div className="pb-4">
      <div className="relative px-5 pt-8 pb-12 mb-3 overflow-hidden"
        style={{ background: `linear-gradient(135deg, ${profilRangi} 0%, ${profilRangi}CC 100%)` }}>
        <div className="absolute -right-8 -top-8 w-32 h-32 rounded-full" style={{ backgroundColor: "rgba(255,255,255,0.08)" }} />
        <div className="absolute right-10 bottom-0 w-16 h-16 rounded-full" style={{ backgroundColor: "rgba(255,255,255,0.06)" }} />
        <div className="relative flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <button type="button" onClick={() => rasmInputRef.current?.click()} disabled={rasmYuklanmoqda}
              className="relative w-16 h-16 rounded-2xl flex items-center justify-center font-bold text-2xl shrink-0 overflow-hidden"
              style={{ backgroundColor: "rgba(255,255,255,0.18)", color: "#fff", border: "2px solid rgba(255,255,255,0.35)" }}>
              {foydalanuvchi?.rasm_bormi ? (
                <img src={`${API_BASE}/api/profil_rasm/${foydalanuvchi.user_id}?v=${rasmVersiyasi}`} alt={__kbUi("")} className="w-full h-full object-cover" />
              ) : __kbUi((ism || "?").trim().slice(0, 1).toUpperCase())}
              <span className="absolute bottom-0 inset-x-0 text-center text-[9px] font-semibold py-0.5" style={{ backgroundColor: "rgba(0,0,0,0.4)", color: "#fff" }}>
                {rasmYuklanmoqda ? __kbUi("...") : __kbUi("✏️")}
              </span>
            </button>
            <input ref={rasmInputRef} type="file" accept="image/png,image/jpeg,image/webp" onChange={rasmTanlandi} className="hidden" />
            <div className="min-w-0">
              <h1 className="text-xl font-bold truncate" style={{ color: "#fff" }}>{ism || uiT("Profil")}</h1>
              <p className="text-xs" style={{ color: "rgba(255,255,255,0.8)" }}>
                {foydalanuvchi?.is_admin ? __kbUi("🛠 Admin") : rolNomlari[foydalanuvchi?.role] || uiT("Foydalanuvchi")}
                {foydalanuvchi?.role === "oquvchi" && talabaMi ? __kbUi(` · ${talabaProfili ? `${talabaProfili.kurs}-kurs · ${talabaProfili.guruh}` : sinf}`) : foydalanuvchi?.role === "oquvchi" && sinf ? __kbUi(` · ${sinf}${sinfHarfi ? `-${sinfHarfi}` : ""}-sinf`) : __kbUi("")}
              </p>
            </div>
          </div>
          {foydalanuvchi?.role === "oquvchi" && (
            <button type="button" onClick={() => otaOnaKartaRef.current?.scrollIntoView({ behavior: "smooth", block: "center" })}
              className="flex items-center gap-1.5 pl-1 pr-2.5 py-1 rounded-full shrink-0" style={{ backgroundColor: "rgba(255,255,255,0.18)" }}>
              <span className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold overflow-hidden shrink-0" style={{ backgroundColor: "rgba(255,255,255,0.9)", color: profilRangi }}>
                {otaOnalarim[0]?.rasm_bormi ? (
                  <img src={`${API_BASE}/api/profil_rasm/${otaOnalarim[0].user_id}`} alt={__kbUi("")} className="w-full h-full object-cover" />
                ) : otaOnalarim[0] ? __kbUi(otaOnalarim[0].full_name.trim().slice(0, 1).toUpperCase()) : __kbUi("👤")}
              </span>
              <span className="text-xs font-medium" style={{ color: "#fff" }}>{otaOnalarim[0] ? otaOnalarim[0].full_name.split(" ")[0] : __kbUi("Ulash")}</span>
            </button>
          )}
        </div>
      </div>

      <div className="px-5 -mt-8">
      {rasmXato && <p className="text-xs mb-3" style={{ color: "#B0553A" }}>{__kbUi(rasmXato)}</p>}

      <ProfileAccordion icon="⚙️" title={__kbUi("Profil sozlamalari")} summary="Shaxsiy ma'lumot, maktab, fan, dizayn, ovoz va til">
      <ProfileAccordion nested icon="👤" title={uiT("Shaxsiy ma'lumotlar")} summary="Ism, tug'ilgan sana va hudud">
      <div className="rounded-2xl p-4 bg-white border mb-3 shadow-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <p className="text-xs font-semibold mb-3 flex items-center gap-1.5" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>👤 <InterfaceText text={__kbUi("Shaxsiy ma'lumotlar")}/></p>

        <div className="grid grid-cols-2 gap-2.5">
          <div>
            <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Ism")}/></label>
            <input type="text" value={ism} onChange={(e) => setIsm(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border text-sm"
              style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          </div>
          <div>
            <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Viloyat")}/></label>
            <select value={viloyat} onChange={(e) => { setViloyat(e.target.value); setTuman(""); }}
              className="w-full px-3 py-2.5 rounded-xl border text-sm"
              style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <option value="">—</option>
              {VILOYATLAR.map((v) => <option key={v} value={v}>{__kbUi(v)}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Tug'ilgan sana")}</label>
            <input type="date" value={tugilganSana} onChange={(e) => setTugilganYil(e.target.value)}
              min="1950-01-01" max={new Date().toISOString().split("T")[0]}
              className="w-full px-3.5 py-2.5 rounded-xl border text-sm"
              style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          </div>
          <div>
            <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Tuman")}/></label>
            <select value={tuman} onChange={(e) => setTuman(e.target.value)} disabled={!viloyat}
              className="w-full px-3 py-2.5 rounded-xl border text-sm"
              style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", opacity: viloyat ? 1 : 0.5 }}>
              <option value="">—</option>
              {(HUDUDLAR[viloyat] || []).map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
        </div>
      </div>
      </ProfileAccordion>

      {foydalanuvchi?.role === "oquvchi" && (talabaOqimi || talabaMi) && (
        <ProfileAccordion nested icon="🎓" title={__kbUi("Institut va kurs")} summary={talabaProfili ? `${talabaProfili.universitet_nomi} · ${talabaProfili.kurs}-kurs · ${talabaProfili.guruh}` : talabaOqimi ? "Muassasaga qo'shilish" : sinf}>
        <div className="mb-3">
          <React.Suspense fallback={<div className="py-8 text-center"><Loader2 size={22} className="animate-spin mx-auto" style={{ color: "#5B4B8A" }} /></div>}>
            {talabaOqimi ? (
              <TalabaQoshilish token={token} apiBase={API_BASE} onSaqlandi={talabaSaqlandi} onBekor={() => setTalabaOqimi(false)} />
            ) : (
              <>
                <TalabaProfilKartasi profil={talabaProfili} onOzgartir={() => setTalabaOqimi(true)} onChiqish={talabadanChiqish} chiqilmoqda={talabaChiqilmoqda} />
                {!talabaProfili && <p className="text-xs mt-2" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Sinf: ")}<b>{sinf}</b>{__kbUi(". To'liq talaba ma'lumotini kiritish uchun ")}<button type="button" className="underline font-semibold" style={{ color: "#5B4B8A" }} onClick={() => setTalabaOqimi(true)}>{__kbUi("muassasaga qo'shiling")}</button>.</p>}
                <p className="text-xs mt-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Mavzular, testlar va AI ustoz ")}<b>{talabaProfili?.sinf || sinf}</b>{__kbUi(" Sinf'i bo'yicha ochiladi. Kurs o'zgarsa — \"Ma'lumotni o'zgartirish\".")}</p>
              </>
            )}
          </React.Suspense>
        </div>
        </ProfileAccordion>
      )}

      {foydalanuvchi?.role === "oquvchi" && !talabaOqimi && !talabaMi && (
        <ProfileAccordion nested icon="🏫" title={__kbUi("Maktab va sinf")} summary={sinf ? `${sinf}${sinfHarfi ? `-${sinfHarfi}` : ""}-sinf` : "Sinf tanlanmagan"}>
        <button type="button" onClick={() => setTalabaOqimi(true)}
          className="w-full flex items-center gap-3 rounded-2xl px-4 py-3 mb-3 text-left border"
          style={{ borderColor: "#D9D2EA", backgroundColor: "#F1EEF8" }}>
          <span className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 text-lg" style={{ backgroundColor: "#fff" }}>🎓</span>
          <span>
            <span className="block text-sm font-semibold" style={{ color: "#5B4B8A" }}>{__kbUi("Men 1–11 sinf emasman — talabaman")}</span>
            <span className="block text-xs" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Institutga ulaning yoki institut tanlamasdan kurs, shakl va tilingizni saqlang")}</span>
          </span>
          <ChevronRight size={16} className="ml-auto shrink-0" style={{ color: "#5B4B8A" }} />
        </button>
        <div className="rounded-2xl p-4 bg-white border mb-3 shadow-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-xs font-semibold mb-3 flex items-center gap-1.5" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("🏫 Maktab ma'lumotlari")}</p>

          <button type="button" onClick={() => setSinfSozlamalariOchiq(!sinfSozlamalariOchiq)}
            className="w-full flex items-center justify-between rounded-xl px-3.5 py-2.5 mb-3" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
            <span className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>
              {[["oddiy", "🏫 Oddiy"], ["xususiy", "🏢 Xususiy"], ["ixtisoslashgan", "⭐ IDUM"], ["prezident", "🏆 Prezident"]].find(([k]) => k === maktabTuri)?.[1] || __kbUi("Maktab turi")}
              {sinf ? __kbUi(` · ${sinf}${sinfHarfi ? `-${sinfHarfi}` : ""}-sinf`) : __kbUi(" · sinf tanlanmagan")}
            </span>
            <ChevronDown size={16} className="shrink-0 transition-transform" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)", transform: sinfSozlamalariOchiq ? "rotate(180deg)" : "none" }} />
          </button>

          {sinfSozlamalariOchiq && (
            <>
              <div className="grid grid-cols-2 gap-2.5 mb-3">
                {[
                  ["oddiy", "🏫 Oddiy"], ["xususiy", "🏢 Xususiy"],
                  ["ixtisoslashgan", "⭐ IDUM"], ["prezident", "🏆 Prezident"],
                ].map(([kalit, nom]) => (
                  <button key={kalit} type="button" onClick={() => setMaktabTuri(kalit)}
                    className="py-2 rounded-lg border text-xs font-medium text-center"
                    style={{
                      borderColor: maktabTuri === kalit ? "#1B4B7A" : "#E5E1D8",
                      backgroundColor: maktabTuri === kalit ? "#1B4B7A" : "#FFFFFF",
                      color: maktabTuri === kalit ? "#FFFFFF" : "#5A5648",
                    }}>
                    {__kbUi(nom)}
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Sinf")}/></label>
                  <div className="grid grid-cols-4 gap-1.5">
                    {Array.from({ length: 11 }, (_, i) => String(i + 1)).map((n) => (
                      <button key={n} type="button" onClick={() => setSinf(n)}
                        className="py-2 rounded-lg border text-sm font-semibold text-center"
                        style={{
                          borderColor: sinf === n ? "#1B4B7A" : "#E5E1D8",
                          backgroundColor: sinf === n ? "#1B4B7A" : "#FFFFFF",
                          color: sinf === n ? "#FFFFFF" : "#5A5648",
                        }}>
                        {n}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Sinf harfi")}</label>
                  <div className="grid grid-cols-5 gap-1.5">
                    {SINF_HARFLARI.map((h) => (
                      <button key={h} type="button" onClick={() => setSinfHarfi(sinfHarfi === h ? "" : h)}
                        className="py-2 rounded-lg border text-sm font-semibold text-center"
                        style={{
                          borderColor: sinfHarfi === h ? "#C89B3C" : "#E5E1D8",
                          backgroundColor: sinfHarfi === h ? "#C89B3C" : "#FFFFFF",
                          color: sinfHarfi === h ? "#FFFFFF" : "#5A5648",
                        }}>
                        {__kbUi(h)}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Ro'yxatdagi maktab (bo'lsa — tanlang, aniqroq bo'ladi)")}</label>
          <MaktabQidiruvi tanlanganMaktab={royxatdagiMaktab} onTanla={setRoyxatdagiMaktab} />

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Maktab raqami")}</label>
          <input type="text" value={maktabRaqami} onChange={(e) => setMaktabRaqami(e.target.value)}
            placeholder={__kbUi("masalan: 21")}
            className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3"
            style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />

          <label className="text-xs font-medium mb-1.5 mt-3 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Dizayn uchun (ixtiyoriy)")}</label>
          <div className="grid grid-cols-2 gap-2.5">
            <button type="button" onClick={() => setJins(jins === "ogil" ? "" : "ogil")}
              className="py-3 rounded-xl border-2 text-sm font-semibold text-center flex items-center justify-center gap-1.5"
              style={{
                borderColor: jins === "ogil" ? OGIL_RANGI : "#E5E1D8",
                backgroundColor: jins === "ogil" ? OGIL_RANGI : "#FFFFFF",
                color: jins === "ogil" ? "#FFFFFF" : "#5A5648",
              }}>{__kbUi("👦 O'g'il")}</button>
            <button type="button" onClick={() => setJins(jins === "qiz" ? "" : "qiz")}
              className="py-3 rounded-xl border-2 text-sm font-semibold text-center flex items-center justify-center gap-1.5"
              style={{
                borderColor: jins === "qiz" ? QIZ_RANGI : "#E5E1D8",
                backgroundColor: jins === "qiz" ? QIZ_RANGI : "#FFFFFF",
                color: jins === "qiz" ? "#FFFFFF" : "#5A5648",
              }}>{__kbUi("👧 Qiz")}</button>
          </div>
        </div>
        </ProfileAccordion>
      )}

      {foydalanuvchi?.role === "oqituvchi" && (
        <ProfileAccordion nested icon="📚" title={__kbUi("O'qituvchi ma'lumotlari")} summary={oqituvchiFani || "Fan tanlanmagan"}>
        <div className="rounded-2xl p-4 bg-white border mb-3 shadow-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-xs font-semibold mb-3 flex items-center gap-1.5" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("📚 O'qituvchi ma'lumotlari")}</p>

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Qaysi fanni o'qitasiz?")}</label>
          <div className="flex flex-wrap gap-1.5 mb-4">
            {BARCHA_MAKTAB_FANLARI.map((f) => {
              const bu_rang = fanRangiOl(f);
              const tanlanganmi = oqituvchiFani === f;
              return (
                <button key={f} type="button" onClick={() => setOqituvchiFani(tanlanganmi ? "" : f)}
                  className="px-3 py-1.5 rounded-full text-xs font-medium border"
                  style={{
                    borderColor: tanlanganmi ? bu_rang : "#E5E1D8",
                    backgroundColor: tanlanganmi ? bu_rang : "#FFFFFF",
                    color: tanlanganmi ? "#FFFFFF" : "#5A5648",
                  }}>
                  {__kbUi(f)}
                </button>
              );
            })}
          </div>

          <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Dizayn uchun (ixtiyoriy)")}</label>
          <div className="grid grid-cols-2 gap-2.5">
            <button type="button" onClick={() => setJins(jins === "ogil" ? "" : "ogil")}
              className="py-3 rounded-xl border-2 text-sm font-semibold text-center flex items-center justify-center gap-1.5"
              style={{
                borderColor: jins === "ogil" ? OGIL_RANGI : "#E5E1D8",
                backgroundColor: jins === "ogil" ? OGIL_RANGI : "#FFFFFF",
                color: jins === "ogil" ? "#FFFFFF" : "#5A5648",
              }}>{__kbUi("👨 Erkak")}</button>
            <button type="button" onClick={() => setJins(jins === "qiz" ? "" : "qiz")}
              className="py-3 rounded-xl border-2 text-sm font-semibold text-center flex items-center justify-center gap-1.5"
              style={{
                borderColor: jins === "qiz" ? QIZ_RANGI : "#E5E1D8",
                backgroundColor: jins === "qiz" ? QIZ_RANGI : "#FFFFFF",
                color: jins === "qiz" ? "#FFFFFF" : "#5A5648",
              }}>{__kbUi("👩 Ayol")}</button>
          </div>
          {oqituvchiFani && (
            <p className="text-xs mt-3 text-center" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Profilingiz \"")}{oqituvchiFani}{__kbUi("\" rangida bezatiladi.")}</p>
          )}
        </div>
        </ProfileAccordion>
      )}

        <ProfileAccordion nested icon="🔗" title={__kbUi("Muassasaga ulanish")} summary="Admin bergan shaxsiy kod bilan ulanish">
        <div className="rounded-2xl p-3 bg-white border mb-4 shadow-sm space-y-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          {foydalanuvchi?.role === "oqituvchi" && <button onClick={() => setKorinish("rasmiy_sinf")} className="w-full flex items-center gap-3 rounded-xl px-3 py-2.5" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
            <span className="w-8 h-8 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
              <GraduationCap size={16} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} />
            </span>
            <span className="text-xs font-semibold flex-1 text-left" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Rasmiy maktab sinfim bormi?")}</span>
            <ChevronRight size={15} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
          </button>}
          <button onClick={() => setKorinish("kirish_kodi")} className="w-full flex items-center gap-3 rounded-xl px-3 py-2.5" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
            <span className="w-8 h-8 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: "#FDF3E0" }}>
              <KeyRound size={16} style={{ color: "#8A5A1C" }} />
            </span>
            <span className="text-xs font-semibold flex-1 text-left" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Admin bergan ulanish kodim bor")}</span>
            <ChevronRight size={15} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
          </button>
        </div>
        </ProfileAccordion>

      <ProfileAccordion nested icon="🔊" title={__kbUi("Ovoz")} summary={ovozJinsi === "qiz" ? __kbUi("Qiz ovozi") : __kbUi("O‘g‘il ovozi")}>
      <div className="rounded-2xl p-4 bg-white border mb-3 shadow-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <p className="text-xs mb-3 leading-relaxed" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Matnning o‘zbekcha, ruscha yoki inglizcha tili avtomatik aniqlanadi. Faqat ovozni tanlang.")}</p>
        <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Ovoz")}/></label>
        <div className="grid grid-cols-2 gap-2.5">
          <button type="button" onClick={() => setOvozJinsi("ogil")}
            className="py-2.5 rounded-xl border text-sm font-semibold"
            style={{ borderColor: ovozJinsi === "ogil" ? OGIL_RANGI : "#E5E1D8", backgroundColor: ovozJinsi === "ogil" ? OGIL_RANGI : "#fff", color: ovozJinsi === "ogil" ? "#fff" : "#5A5648" }}>{__kbUi("👨 O‘g‘il ovozi")}</button>
          <button type="button" onClick={() => setOvozJinsi("qiz")}
            className="py-2.5 rounded-xl border text-sm font-semibold"
            style={{ borderColor: ovozJinsi === "qiz" ? QIZ_RANGI : "#E5E1D8", backgroundColor: ovozJinsi === "qiz" ? QIZ_RANGI : "#fff", color: ovozJinsi === "qiz" ? "#fff" : "#5A5648" }}>{__kbUi("👩 Qiz ovozi")}</button>
        </div>
      </div>
      </ProfileAccordion>

      {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
      {muvaffaqiyat && <p className="text-sm mb-3" style={{ color: "#3B6D11" }}>{__kbUi("✓ Saqlandi")}</p>}

      <button onClick={profilSaqla} disabled={saqlanmoqda}
        className="w-full py-3 rounded-xl font-semibold text-white text-sm mb-4"
        style={{ backgroundColor: profilRangi, opacity: saqlanmoqda ? 0.7 : 1 }}>
        {saqlanmoqda ? uiT("Saqlanmoqda...") : uiT("Saqlash")}
      </button>
      </ProfileAccordion>

      {foydalanuvchi?.role === "oquvchi" && (
        <div ref={otaOnaKartaRef}>
        <ProfileAccordion icon="🔗" title={__kbUi("Ota-onani ulash")} summary={otaOnalarim.length ? `${otaOnalarim.length} ta ota-ona ulangan` : "Kod orqali ulash"}>
        <div className="rounded-2xl p-4 bg-white border mb-3 shadow-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("🔗 Ota-onani ulash")}</p>
          {otaOnalarim.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-2 mt-2">
              {otaOnalarim.map((o) => (
                <span key={o.user_id} className="text-xs font-medium px-3 py-1 rounded-full" style={{ backgroundColor: "#EAF3DE", color: "#3B6D11" }}>
                  ✓ {o.full_name}
                </span>
              ))}
            </div>
          )}
          <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>
            {otaOnalarim.length > 0 ? __kbUi("Yana bittasini ulash uchun kod oling:") : __kbUi("Kod oling va uni ota-onangizga ayting — u shu kodni o'z profilida kiritib, sizning bilim ko'rsatkichlaringizni ko'ra oladi.")}
          </p>
          {otaKod ? (
            <div className="rounded-xl p-3 text-center mb-2" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
              <p className="text-2xl font-bold tracking-widest mb-0.5" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{otaKod.kod}</p>
              <p className="text-xs" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{otaKod.amal_qilish_daqiqasi}{__kbUi(" daqiqa amal qiladi")}</p>
            </div>
          ) : null}
          {otaKodXato && <p className="text-sm mb-2" style={{ color: "#B0553A" }}>{__kbUi(otaKodXato)}</p>}
          <button onClick={otaKodOl} disabled={otaKodOlinmoqda}
            className="w-full py-2.5 rounded-xl font-semibold text-sm"
            style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)", opacity: otaKodOlinmoqda ? 0.7 : 1 }}>
            {otaKodOlinmoqda ? __kbUi("...") : otaKod ? __kbUi("🔄 Yangi kod olish") : __kbUi("Kod olish")}
          </button>
        </div>
        </ProfileAccordion>
        </div>
      )}

      {foydalanuvchi?.role === "ota-ona" && (
        <ProfileAccordion icon="👨‍👩‍👧" title={__kbUi("Farzandlarim")} summary={farzandlar.length ? `${farzandlar.length} ta farzand ulangan` : "Farzand kodini kiriting"}>
        <div className="rounded-2xl p-4 bg-white border mb-3 shadow-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm font-semibold mb-2" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("👨‍👩‍👧 Farzandlarim")}</p>

          {farzandlar.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-3">
              {farzandlar.map((f) => (
                <span key={f.user_id} className="flex items-center gap-1.5 pl-3 pr-1.5 py-1 rounded-full" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                  <span className="text-xs font-medium" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{f.full_name}</span>
                  <button onClick={() => farzandniUzish(f.user_id)}
                    className="w-4.5 h-4.5 rounded-full flex items-center justify-center text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} title={__kbUi("Uzish")}>✕</button>
                </span>
              ))}
            </div>
          )}

          <div className="flex gap-2">
            <input type="text" value={farzandKodi} onChange={(e) => setFarzandKodi(e.target.value.replace(/\D/g, "").slice(0, 6))}
              placeholder={__kbUi("farzand kodi (123456)")} maxLength={6}
              className="flex-1 px-3.5 py-2.5 rounded-xl border text-sm"
              style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
            <button onClick={farzandQoshish} disabled={farzandQoshilmoqda || !farzandKodi.trim()}
              className="px-4 rounded-xl font-semibold text-white text-sm shrink-0"
              style={{ backgroundColor: "#1B4B7A", opacity: (farzandQoshilmoqda || !farzandKodi.trim()) ? 0.6 : 1 }}>
              {farzandQoshilmoqda ? __kbUi("...") : uiT("Qo'shish")}
            </button>
          </div>
          {farzandXato && <p className="text-sm mt-2" style={{ color: "#B0553A" }}>{__kbUi(farzandXato)}</p>}
          {farzandMuvaffaqiyat && <p className="text-sm mt-2" style={{ color: "#3B6D11" }}>{farzandMuvaffaqiyat}</p>}
        </div>
        </ProfileAccordion>
      )}

      <ProfileAccordion icon="🎯" title={__kbUi("Mening to'garaklarim")} summary={togaraklarim.length ? `${togaraklarim.length} ta to'garak` : "Parol bilan qo'shilish"}>
      <div className="rounded-2xl p-4 bg-white border mb-3 shadow-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
        <p className="text-xs font-medium mb-3" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Mening to'garaklarim")}</p>

        {togaraklarYuklanmoqda ? (
          <Loader2 size={18} className="animate-spin" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} />
        ) : togaraklarim.length === 0 ? (
          <p className="text-sm mb-4" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali hech qaysi to'garakka qo'shilmagansiz.")}</p>
        ) : (
          <div className="flex flex-wrap gap-2 mb-4">
            {togaraklarim.map((t) => (
              t.tasdiqlangan === false ? (
                <span key={t.id} className="text-xs px-3 py-1.5 rounded-full font-medium" style={{ backgroundColor: "#FDF3E0", color: "#8A5A1C" }}>
                  ⏳ {t.nomi}{__kbUi(" — kutilmoqda")}</span>
              ) : (
                <button key={t.id} onClick={() => { setTanlanganTogarak(t); setKorinish(t.turi === "avto" ? "mening_kalendarim" : "togarak_mavzular"); }}
                  className="text-xs px-3 py-1.5 rounded-full font-medium"
                  style={t.turi === "avto" ? { backgroundColor: "#F3EEFA", color: "#8B5FBF" } : { backgroundColor: "#EAF1F7", color: "#1B4B7A" }}>
                  {t.turi === "avto" ? __kbUi("🤖 ") : __kbUi("")}{t.nomi} →
                </button>
              )
            ))}
          </div>
        )}

        <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Parol bilan qo'shilish")}</label>
        <div className="flex gap-2">
          <input type="text" value={qoshilishParol} onChange={(e) => setQoshilishParol(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && togarakkaQoshil()}
            placeholder={__kbUi("to'garak paroli")}
            className="flex-1 px-3.5 py-2.5 rounded-xl border text-sm"
            style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          <button onClick={togarakkaQoshil} disabled={qoshilinmoqda}
            className="px-4 py-2.5 rounded-xl font-semibold text-white text-sm shrink-0"
            style={{ backgroundColor: "#C89B3C", opacity: qoshilinmoqda ? 0.7 : 1 }}>
            {qoshilinmoqda ? __kbUi("...") : __kbUi("Qo'shilish")}
          </button>
        </div>
        {qoshilishXato && <p className="text-sm mt-2" style={{ color: "#B0553A" }}>{__kbUi(qoshilishXato)}</p>}
        {qoshilishMuvaffaqiyat && <p className="text-sm mt-2" style={{ color: "#3B6D11" }}>✓ {qoshilishMuvaffaqiyat}</p>}
      </div>
      </ProfileAccordion>

      {foydalanuvchi?.is_admin && (
        <ProfileAccordion icon="🔑" title={__kbUi("Kim nima yarata oladi")} summary="Taqdimot va to'garak yaratish — rollar bo'yicha ochish/yopish">
          <AdminRuxsatlarBolimi token={token} />
        </ProfileAccordion>
      )}

      {foydalanuvchi?.is_admin && (
        <ProfileAccordion icon="🛡️" title={__kbUi("Admin xavfsizligi va arxiv")} summary="Parol, faol muassasalar va arxiv">
        <React.Suspense fallback={<div className="py-6 text-center"><Loader2 size={22} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>}>
          <AdminInstitutionSecurity token={token} apiBase={API_BASE} />
        </React.Suspense>
        </ProfileAccordion>
      )}

      <ProfileAccordion icon="🎭" title={foydalanuvchi?.is_admin ? __kbUi("Kabinet ko'rinishi") : __kbUi("Rol sozlamalari")} summary={foydalanuvchi?.is_admin ? "Admin, o'quvchi, ota-ona yoki o'qituvchi" : `${__kbUi("Joriy rol:")} ${roleDetail(foydalanuvchi, __kbUi) || "—"}`}>
      {foydalanuvchi?.is_admin ? (
        <div className="rounded-2xl p-4 bg-white border mb-4 shadow-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-xs font-medium mb-1" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Rol ko‘rinishini almashtirish")}</p>
          <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Admin, o‘quvchi, ota-ona va o‘qituvchi kabinetlarini alohida sinang. Bu administrator huquqingizni o‘chirmaydi.")}</p>
          {onOquvchiKorinishi && <button type="button" onClick={onOquvchiKorinishi}
            className="w-full mb-3 py-3 rounded-xl text-sm font-semibold text-white" style={{ backgroundColor: "#E8743B" }}>
            {__kbUi("👁 Bog‘cha, maktab, markaz yoki institut o‘quvchisi ko‘zi bilan ko‘rish →")}</button>}
          <div className="grid grid-cols-2 gap-2">
            {[["admin", "🛠 Admin"], ["oquvchi", "O'quvchi"], ["ota-ona", "Ota-ona"], ["oqituvchi", "O'qituvchi"]].map(([v, l]) => (
              <button key={v} onClick={() => onKorinishOzgar(v)}
                className="py-2.5 rounded-lg border text-xs font-medium"
                style={{
                  borderColor: adminKorinish === v ? "#1B4B7A" : "#E5E1D8",
                  backgroundColor: adminKorinish === v ? "#1B4B7A" : "#FFFFFF",
                  color: adminKorinish === v ? "#FFFFFF" : "#5A5648",
                }}>
                {__kbUi(l)}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="rounded-2xl p-4 bg-white border mb-4 shadow-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-xs font-medium mb-2" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Rolingiz")}</p>
          {onRolAlmashtir && foydalanuvchi?.role_locked ? <p className="text-xs leading-relaxed" style={{ color: "#5A5648" }}>🔒 {__kbUi(foydalanuvchi.role_lock_reason === "institut" ? "Siz institutga talaba sifatida ulangansiz. Rolni almashtirish uchun avval pastdagi «Institut va kurs» bo‘limidan institutdan chiqing." : "Akkauntingiz muassasaga ulangan — rolingizni muassasa belgilaydi.")}</p> : onRolAlmashtir ? <><div className="grid grid-cols-2 gap-2">
            {LOGIN_ROLES.map(([v, l, icon]) => { const joriy = loginAccountRole(foydalanuvchi) === v; return (
              <button key={v} type="button" aria-pressed={joriy} onClick={() => onRolAlmashtir(v)}
                className="py-2.5 rounded-lg border text-xs font-medium"
                style={{ borderColor: joriy ? "#1B4B7A" : "#E5E1D8", backgroundColor: joriy ? "#1B4B7A" : "#FFFFFF", color: joriy ? "#FFFFFF" : "#5A5648" }}>
                {icon} {__kbUi(l)}
              </button>); })}
          </div>
          {roleDetail(foydalanuvchi, __kbUi) && <div className="mt-3 flex flex-wrap items-center gap-2 rounded-xl px-3 py-2" style={{ backgroundColor: "#EAF1F7" }}>
            <span className="text-xs font-semibold flex-1 min-w-0" style={{ color: "#1B4B7A" }}>{__kbUi("Hozir:")} {roleDetail(foydalanuvchi, __kbUi)}</span>
            {["bogcha", "oquvchi", "talaba"].includes(loginAccountRole(foydalanuvchi)) && <button type="button" onClick={() => onRolAlmashtir(loginAccountRole(foydalanuvchi))}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg text-white" style={{ backgroundColor: "#1B4B7A" }}>
              {__kbUi(loginAccountRole(foydalanuvchi) === "bogcha" ? "✏️ Yoshni o‘zgartirish" : loginAccountRole(foydalanuvchi) === "talaba" ? "✏️ Kursni o‘zgartirish" : "✏️ Sinfni o‘zgartirish")}</button>}
          </div>}
          <p className="text-xs mt-2" style={{ color: "#8A8578" }}>{__kbUi("Rol xohlagan paytda almashadi. Keyin sinf/kurs sozlamalarini to‘ldiring — aks holda testlar va mavzular mos chiqmaydi.")}</p></> :
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(rolNomlari).map(([v, l]) => (
              <button key={v} onClick={() => rolTanlandi(v)}
                className="py-2.5 rounded-lg border text-xs font-medium"
                style={{
                  borderColor: foydalanuvchi?.role === v ? "#1B4B7A" : "#E5E1D8",
                  backgroundColor: foydalanuvchi?.role === v ? "#1B4B7A" : "#FFFFFF",
                  color: foydalanuvchi?.role === v ? "#FFFFFF" : "#5A5648",
                }}>
                {__kbUi(l)}
              </button>
            ))}
          </div>}
        </div>
      )}
      </ProfileAccordion>

      {rolTanlov && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-6" style={{ backgroundColor: "rgba(0,0,0,0.4)" }}>
          <div className="w-full max-w-sm rounded-2xl p-5" style={{ backgroundColor: "var(--ui-legacy-background-ffffff, #FFFFFF)", boxShadow: "0 12px 32px rgba(43,43,43,0.18)" }}>
            {rolSurishNatija === "yuklanmoqda" ? (
              <div className="py-4 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
            ) : kodBosqichida ? (
              <>
                <p className="font-semibold mb-2" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("📧 Tasdiqlash kodi kerak")}</p>
                <p className="text-sm mb-4" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Bepul rol almashtirish imkoniyatingiz tugagan. \"")}{__kbUi(rolNomlari[rolTanlov])}{__kbUi("\"ga o'zgartirish uchun Gmail hisobingizga (")}{kodEmail || __kbUi("...")}{__kbUi(") yuborilgan 6 xonali kodni kiriting.")}</p>
                {kodYuklanmoqda ? (
                  <div className="py-2 text-center"><Loader2 size={20} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
                ) : (
                  <>
                    <input type="text" value={kodQiymati} onChange={(e) => setKodQiymati(e.target.value.replace(/\D/g, "").slice(0, 6))}
                      placeholder={__kbUi("123456")} maxLength={6}
                      className="w-full px-3.5 py-2.5 rounded-xl border text-center text-lg tracking-widest mb-3"
                      style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
                    <button onClick={kodSora} className="text-xs mb-4" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Kodni qayta yuborish")}</button>
                  </>
                )}
                {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
                <div className="flex gap-2.5">
                  <button onClick={rolModalniYop}
                    className="flex-1 py-2.5 rounded-xl border text-sm font-medium" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Bekor qilish")}/></button>
                  <button onClick={kodTasdiqla} disabled={rolOzgartirilmoqda || !kodQiymati.trim()}
                    className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white"
                    style={{ backgroundColor: "#1B4B7A", opacity: (rolOzgartirilmoqda || !kodQiymati.trim()) ? 0.6 : 1 }}>
                    {rolOzgartirilmoqda ? __kbUi("...") : uiT("Tasdiqlash")}
                  </button>
                </div>
              </>
            ) : (
              <>
                <p className="font-semibold mb-2" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("⚠️ Rolni o'zgartirasizmi?")}</p>
                <p className="text-sm mb-3" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{__kbUi("Rolingiz \"")}{__kbUi(rolNomlari[rolTanlov])}{__kbUi("\"ga o'zgaradi. Bu ko'rinadigan ma'lumot va imkoniyatlaringizga butunlay ta'sir qiladi — masalan o'quvchi test/bilim ma'lumotlari, o'qituvchi guruhlari.")}</p>
                {rolSurishNatija?.admin_test ? (
                  <p className="text-xs mb-5 font-medium" style={{ color: "#2D8B8B" }}>{__kbUi("✓ Admin sifatida cheklovsiz sinab ko'rishingiz mumkin.")}</p>
                ) : (
                  <p className="text-xs mb-5 font-semibold p-3 rounded-xl" style={{ color: "#8A5A1C", backgroundColor: "#FDF3E3" }}>{__kbUi("DIQQAT: rolni FAQAT 2 marta bepul o'zgartirish mumkin. Sizda ")}{rolSurishNatija?.qolgan_bepul ?? __kbUi("?")}{__kbUi(" ta bepul imkoniyat qoldi. Shundan keyin har safar Gmail orqali tasdiqlash kodi va 30 kunlik kutish talab qilinadi.")}</p>
                )}
                {xato && <p className="text-sm mb-3" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}
                <div className="flex gap-2.5">
                  <button onClick={rolModalniYop}
                    className="flex-1 py-2.5 rounded-xl border text-sm font-medium" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Bekor qilish")}/></button>
                  <button onClick={rolTasdiqla} disabled={rolOzgartirilmoqda}
                    className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ backgroundColor: "#1B4B7A" }}>
                    {rolOzgartirilmoqda ? __kbUi("...") : uiT("Tasdiqlash")}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
      </div>
    </div>
  );
}

function menyuBandlariniOl(rol, qoshimchaBand) {
  if (rol === "admin") {
    return [
      { kalit: "kurslar", nom: "Kurslar va to‘garaklar", ikon: BookOpen },
      { kalit: "admin", nom: "Shablon", ikon: FileSpreadsheet },
      { kalit: "admin_muassasalar", nom: "Muassasalar", ikon: Building2 },
      { kalit: "admin_testlar", nom: "Testlar", ikon: PencilLine },
      { kalit: "admin_mavzular", nom: "Mavzular", ikon: BookOpen },
      { kalit: "admin_korinish", nom: "O‘quvchi ko‘zi bilan", ikon: Eye },
      { kalit: "oyinlar", nom: "O‘yinlar", ikon: Gamepad2 },   // REV129: admin ham barcha o'yinlarni ko'radi (cheklovsiz)
      { kalit: "admin_ovoz", nom: "Ovozli matn", ikon: Mic },
      { kalit: "admin_statistikalar", nom: "Statistikalar", ikon: BarChart3 },
      { kalit: "admin_moderatsiya", nom: "Moderatsiya", ikon: AlertTriangle },
            { kalit: "profil", nom: "Profil va sozlamalar", ikon: Settings },
    ];
  }
  if (rol === "oqituvchi") {
    // Muassasasi bor xodim (dekan, direktor, o'qituvchi...) uchun asosiy ish joyi — muassasasi.
    // Umumiy "Ish maydoni" (to'garak, repetitorlik, AI vositalari) qo'shimcha bo'lib pastda turadi.
    return [
      { kalit: "kurslar", nom: "Kurslar va to‘garaklar", ikon: BookOpen },
      ...(qoshimchaBand ? [qoshimchaBand] : []),
      // REV96: to'garak endi aniq nom bilan ko'rinadi; kutubxona va ovoz vositasi alohida band.
      { kalit: "oqituvchi", nom: "To‘garak va repetitorlik", ikon: Users },
      { kalit: "kutubxonam", nom: "Kutubxonam", ikon: Folder },
      { kalit: "ovoz", nom: "Ovoz ⇄ Matn", ikon: Mic },
      { kalit: "oqituvchi_analitika", nom: "Statistikalar", ikon: BarChart3 },
      { kalit: "mavzular", nom: "Mavzular", ikon: BookOpen },
      { kalit: "test", nom: "Testlar", ikon: PencilLine },
      { kalit: "oyinlar", nom: "O‘yinlar", ikon: Gamepad2 },
            { kalit: "profil", nom: "Profil", ikon: User },
    ];
  }
  if (rol === "ota-ona") {
    return [
      { kalit: "kurslar", nom: "Kurslar va to‘garaklar", ikon: BookOpen },
      { kalit: "farzand", nom: "Farzand tahlili", ikon: Heart },
            { kalit: "profil", nom: "Profil", ikon: User },
    ];
  }
  // O'quvchi / talaba / bog'cha / markaz: asosiy yo'l — O'rganish (fan → mavzu → dars → test).
  return [
    { kalit: "mavzular", nom: "O‘rganish", ikon: BookOpen },
    { kalit: "test", nom: "Testlar", ikon: PencilLine },
    { kalit: "oyinlar", nom: "O‘yinlar", ikon: Gamepad2 },
    { kalit: "ai_ustoz", nom: "AI Ustoz", ikon: Bot },
    { kalit: "bilim", nom: "Mening tahlilim", ikon: BarChart3 },
    { kalit: "kurslar", nom: "Kurslar va to‘garaklar", ikon: BookOpen },
    { kalit: "profil", nom: "Profil", ikon: User },
  ];
}

function PastkiMenyu({
  faol,
  onTanlash,
  rol,
  rang,
  bloklangan,
  qoshimchaBand,
  foydalanuvchi,
  taqdimotMavjud = false,
}) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const aktivRang = rang || "#1B4B7A";
  const bandlar = menyuBandlariniOl(rol, qoshimchaBand);
  // REV79: talabaga «Mening institutim» (guruhim, kursim, muhim sanalar).
  const talabaMi = rol !== "admin" && rol !== "oqituvchi" && rol !== "ota-ona" && (_kbAccountRole(foydalanuvchi) === "talaba" || /kurs/i.test(String(foydalanuvchi?.class || "")));
  if (talabaMi) bandlar.splice(1, 0, { kalit: "institutim", nom: "Mening institutim", ikon: GraduationCap });
  // REV80: bog'cha bolasi — sodda menyu: o'rganamiz, o'yin-testlar, to'garaklar, profil.
  const bogchaMi = rol !== "admin" && rol !== "oqituvchi" && rol !== "ota-ona" && _kbAccountRole(foydalanuvchi) === "bogcha";
  if (bogchaMi) {
    bandlar.splice(0, bandlar.length,
      { kalit: "mavzular", nom: "O‘rganamiz", ikon: BookOpen },
      { kalit: "test", nom: "O‘yin va testlar", ikon: PencilLine },
      { kalit: "oyinlar", nom: "O‘yinlar", ikon: Gamepad2 },
      { kalit: "kurslar", nom: "To‘garaklar", ikon: BookOpen },
      { kalit: "profil", nom: "Profil", ikon: User });
  }
  if (taqdimotMavjud) bandlar.splice(1, 0, { kalit: "taqdimotlar", nom: "Taqdimot yaratish", ikon: FileSpreadsheet });
  const profilBandi = bandlar.find((band) => band.kalit === "profil");
  const asosiyBandlar = bandlar.filter((band) => band.kalit !== "profil");
  const rolNomi = rol === "admin"
    ? "Administrator"
    : rol === "oqituvchi"
      ? "O‘qituvchi"
      : rol === "ota-ona"
        ? "Ota-ona"
        : talabaMi ? "Talaba" : bogchaMi ? "Bog‘cha bolasi" : "O‘quvchi";
  const ism = foydalanuvchi?.full_name || rolNomi;
  const boshHarf = ism.trim().split(/\s+/).slice(0, 2).map((q) => q[0]).join("").toUpperCase() || "TA";

  const bandTugmasi = ({ kalit, nom, ikon: Ikon }, desktop = false) => {
    const aktiv = faol === kalit;
    const taqiqlangan = bloklangan && !aktiv;
    return (
      <button
        key={`${desktop ? "desktop" : "mobile"}-${kalit}`}
        onClick={() => !taqiqlangan && onTanlash(kalit)}
        className={desktop
          ? `premium-side-link${aktiv ? " active" : ""}`
          : `premium-mobile-link${aktiv ? " active" : ""}`}
        style={{
          "--nav-accent": aktivRang,
          opacity: taqiqlangan ? 0.35 : 1,
          cursor: taqiqlangan ? "not-allowed" : "pointer",
        }}
        title={taqiqlangan ? uiT("Avval testni yakunlang yoki to‘xtating") : nom}
      >
        <span className={desktop ? "premium-side-icon" : "premium-mobile-icon"}>
          <Ikon size={desktop ? 18 : 21} strokeWidth={aktiv ? 2.5 : 2} />
        </span>
        <span>{uiT(nom)}</span>
      </button>
    );
  };

  return (
    <>
      <aside className="premium-sidebar">
        <div className="premium-side-brand">
          <Logotip compact light />
          <div>
            <strong>{__kbUi("KABUTAR")}</strong>
            <span><InterfaceText text={__kbUi("Ta’lim ekotizimi")}/></span>
          </div>
        </div>
        <div className="premium-role-card">
          <span className="premium-role-avatar" style={{ background: `linear-gradient(135deg, ${aktivRang}, #0B7978)` }}>{boshHarf}</span>
          <div>
            <strong>{ism}</strong>
            <span>{uiT(rolNomi)}</span>
          </div>
        </div>
        <nav className="premium-side-nav">
          <p><InterfaceText text={__kbUi("ASOSIY MENYU")}/></p>
          {asosiyBandlar.map((band) => bandTugmasi(band, true))}
        </nav>
        {profilBandi && (
          <div className="premium-side-profile">
            {__kbUi(bandTugmasi(profilBandi, true))}
          </div>
        )}
        <div className="premium-side-status">
          <span className="premium-live-dot" />
          <div><strong>{__kbUi("Kabutar")}</strong><small>{uiT("Suhbat va ta’lim maydoni")}</small></div>
        </div>
      </aside>

      <nav className="premium-mobile-nav">
        <div style={{ gridTemplateColumns: `repeat(${bandlar.length}, minmax(${bandlar.length > 6 ? 56 : 0}px, 1fr))` }}>
          {bandlar.map((band) => bandTugmasi(band, false))}
        </div>
      </nav>
    </>
  );
}

function XabarlarTab({ token }) {
  useKbInterfaceLocale();
  const [bildirishnomalar, setBildirishnomalar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [korinish, setKorinish] = useState("bildirishnoma"); // "bildirishnoma" | "suhbatlar"
  const [tanlanganSuhbat, setTanlanganSuhbat] = useState(null); // { guruh_id } | { boshqa_user_id, boshqa_ismi }

  useEffect(() => {
    fetch(`${API_BASE}/api/bildirishnomalar?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => { setBildirishnomalar(d.bildirishnomalar || []); setYuklanmoqda(false); })
      .catch(() => setYuklanmoqda(false));
  }, [token]);

  const vaqtniKorsat = (izo) => {
    const sana = new Date(izo);
    const kunlar = Math.floor((Date.now() - sana.getTime()) / 86400000);
    if (kunlar === 0) return "Bugun";
    if (kunlar === 1) return "Kecha";
    return `${kunlar} kun oldin`;
  };

  if (korinish === "suhbatlar" && tanlanganSuhbat) {
    return <SuhbatOynasi token={token} suhbat={tanlanganSuhbat} onOrtga={() => setTanlanganSuhbat(null)} />;
  }

  return (
    <div className="px-5 pt-6 pb-4">
      <h1 className="text-2xl font-bold mb-4" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}><InterfaceText text={__kbUi("Xabarlar")}/></h1>
      <div className="flex rounded-full p-1 gap-0.5 mb-5" style={{ backgroundColor: "#F0EDE5" }}>
        <button onClick={() => setKorinish("bildirishnoma")} className="flex-1 py-2 rounded-full text-sm font-semibold"
          style={korinish === "bildirishnoma" ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>🔔 <InterfaceText text={__kbUi("Bildirishnomalar")}/></button>
        <button onClick={() => setKorinish("suhbatlar")} className="flex-1 py-2 rounded-full text-sm font-semibold"
          style={korinish === "suhbatlar" ? { backgroundColor: "#fff", color: "#1B4B7A", boxShadow: "0 1px 3px rgba(43,43,43,0.12)" } : { backgroundColor: "transparent", color: "#8A8578" }}>💬 <InterfaceText text={__kbUi("Suhbatlar")}/></button>
      </div>

      {korinish === "suhbatlar" ? (
        <SuhbatlarRoyxati token={token} onSuhbatOch={setTanlanganSuhbat} />
      ) : yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : bildirishnomalar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hozircha bildirishnoma yo'q.")}</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {bildirishnomalar.map((b) => (
            <div key={b.id} className="rounded-xl p-4 bg-white border" style={{ borderColor: b.oqildimi ? "#E5E1D8" : "#F5DFA3" }}>
              <div className="flex items-start gap-2.5">
                <span className="text-lg shrink-0">{b.turi === "tolov" ? __kbUi("💳") : __kbUi("🔔")}</span>
                <div className="flex-1">
                  <p className="text-sm" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{b.matn}</p>
                  <p className="text-xs mt-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi(vaqtniKorsat(b.yaratildi))}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SuhbatlarRoyxati({ token, onSuhbatOch }) {
  useKbInterfaceLocale();
  const [guruhlar, setGuruhlar] = useState([]);
  const [shaxsiylar, setShaxsiylar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [qidiruvOchiq, setQidiruvOchiq] = useState(false);
  const [qidiruvMatni, setQidiruvMatni] = useState("");
  const [qidiruvNatijalari, setQidiruvNatijalari] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/api/chat/guruhlarim?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => { setGuruhlar(d.guruhlar || []); setShaxsiylar(d.shaxsiylar || []); setYuklanmoqda(false); })
      .catch(() => setYuklanmoqda(false));
  }, [token]);

  useEffect(() => {
    if (qidiruvMatni.trim().length < 2) { setQidiruvNatijalari([]); return; }
    const vaqt = setTimeout(() => {
      fetch(`${API_BASE}/api/chat/foydalanuvchi_qidir?token=${encodeURIComponent(token)}&ism=${encodeURIComponent(qidiruvMatni.trim())}`)
        .then((r) => r.json())
        .then((d) => setQidiruvNatijalari(d.natijalar || []))
        .catch(() => {});
    }, 350);
    return () => clearTimeout(vaqt);
  }, [qidiruvMatni, token]);

  const vaqtQisqa = (izo) => {
    if (!izo) return "";
    const sana = new Date(izo);
    const bugun = new Date();
    if (sana.toDateString() === bugun.toDateString()) return sana.toLocaleTimeString(__kbLocaleTag(), { hour: "2-digit", minute: "2-digit" });
    return sana.toLocaleDateString(__kbLocaleTag(), { day: "2-digit", month: "2-digit" });
  };

  const oxirgiMatnKorsat = (matn, faylTuri) => {
    if (matn) return matn;
    if (faylTuri === "audio") return "🎤 Ovozli xabar";
    if (faylTuri === "video") return "🎬 Video";
    if (faylTuri === "video_doira") return "⭕ Video xabar";
    if (faylTuri === "hujjat") return "📎 Fayl";
    return "";
  };

  if (qidiruvOchiq) {
    return (
      <div>
        <div className="flex items-center gap-2 mb-4">
          <input type="text" autoFocus value={qidiruvMatni} onChange={(e) => setQidiruvMatni(e.target.value)}
            placeholder={__kbUi("Ism bo'yicha qidirish...")} className="flex-1 px-3.5 py-2.5 rounded-xl border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          <button onClick={() => { setQidiruvOchiq(false); setQidiruvMatni(""); }} className="text-sm font-medium" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bekor")}</button>
        </div>
        <div className="space-y-1.5">
          {qidiruvNatijalari.map((n) => (
            <button key={n.user_id} onClick={() => { setQidiruvOchiq(false); setQidiruvMatni(""); onSuhbatOch({ boshqa_user_id: n.user_id, boshqa_ismi: n.full_name }); }}
              className="w-full flex items-center gap-3 rounded-xl p-3 bg-white border text-left" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <span className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)", color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
                {__kbUi(n.full_name.trim().slice(0, 1).toUpperCase())}
              </span>
              <span className="text-sm font-medium truncate" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{n.full_name}</span>
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <button onClick={() => setQidiruvOchiq(true)} className="w-full flex items-center gap-2 rounded-xl px-3.5 py-2.5 mb-4" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
        <UserPlus size={16} style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }} />
        <span className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Yangi shaxsiy xabar...")}</span>
      </button>

      {yuklanmoqda ? (
        <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
      ) : guruhlar.length === 0 && shaxsiylar.length === 0 ? (
        <div className="rounded-2xl p-6 text-center bg-white border" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hozircha suhbat yo'q.")}</p>
        </div>
      ) : (
        <div className="space-y-1.5">
          {guruhlar.map((g) => (
            <button key={`g${g.id}`} onClick={() => onSuhbatOch({ guruh_id: g.id, guruh_nomi: g.nomi })}
              className="w-full flex items-center gap-3 rounded-xl p-3 bg-white border text-left" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <span className="w-11 h-11 rounded-full flex items-center justify-center text-lg shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-eaf1f7, #EAF1F7)" }}>
                {__kbUi(g.nomi.trim().slice(0, 2))}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold truncate" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{g.nomi}</p>
                <p className="text-xs truncate" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{oxirgiMatnKorsat(g.oxirgi_matn, g.oxirgi_fayl_turi) || __kbUi("Hali xabar yo'q")}</p>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0">
                {g.oxirgi_vaqt && <span className="text-[11px]" style={{ color: "var(--ui-legacy-color-b0aa98, #B0AA98)" }}>{__kbUi(vaqtQisqa(g.oxirgi_vaqt))}</span>}
                {g.okilmagan_soni > 0 && (
                  <span className="min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-bold text-white flex items-center justify-center" style={{ backgroundColor: "#1B4B7A" }}>
                    {g.okilmagan_soni}
                  </span>
                )}
              </div>
            </button>
          ))}
          {shaxsiylar.map((s) => (
            <button key={`s${s.user_id}`} onClick={() => onSuhbatOch({ boshqa_user_id: s.user_id, boshqa_ismi: s.full_name })}
              className="w-full flex items-center gap-3 rounded-xl p-3 bg-white border text-left" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              <span className="w-11 h-11 rounded-full flex items-center justify-center text-sm font-bold shrink-0" style={{ backgroundColor: "#F3EEFA", color: "#8B5FBF" }}>
                {__kbUi(s.full_name.trim().slice(0, 1).toUpperCase())}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold truncate" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{s.full_name}</p>
                <p className="text-xs truncate" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi(oxirgiMatnKorsat(s.matn, s.fayl_turi))}</p>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0">
                {s.yaratilgan_at && <span className="text-[11px]" style={{ color: "var(--ui-legacy-color-b0aa98, #B0AA98)" }}>{__kbUi(vaqtQisqa(s.yaratilgan_at))}</span>}
                {s.okilmagan_soni > 0 && (
                  <span className="min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-bold text-white flex items-center justify-center" style={{ backgroundColor: "#1B4B7A" }}>
                    {s.okilmagan_soni}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function DoiraVideoYozish({ onYubor, onBekor }) {
  useKbInterfaceLocale();
  const MAX_SONIYA = 60;
  const [holat, setHolat] = useState("tayyorlanmoqda"); // tayyorlanmoqda | tayyor | yozilmoqda | korib_chiqish | xato
  const [xatoMatni, setXatoMatni] = useState("");
  const [yozilganUrl, setYozilganUrl] = useState(null);
  const [sekund, setSekund] = useState(0);
  const [qulflandi, setQulflandi] = useState(false);
  const jonliVideoRef = useRef(null);
  const koribChiqishVideoRef = useRef(null);
  const recorderRef = useRef(null);
  const streamRef = useRef(null);
  const boglamlarRef = useRef([]);
  const taymerRef = useRef(null);
  const boshlanishYRef = useRef(0);
  const QULF_MASOFASI = 45;

  const kameraniOch = () => {
    setHolat("tayyorlanmoqda");
    navigator.mediaDevices.getUserMedia({ video: { facingMode: "user", width: 480, height: 480 }, audio: true })
      .then((stream) => {
        streamRef.current = stream;
        if (jonliVideoRef.current) jonliVideoRef.current.srcObject = stream;
        setHolat("tayyor");
      })
      .catch(() => { setXatoMatni("Kameraga ruxsat berilmadi — brauzer sozlamalaridan ruxsat bering."); setHolat("xato"); });
  };

  useEffect(() => {
    kameraniOch();
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      clearInterval(taymerRef.current);
      if (yozilganUrl) URL.revokeObjectURL(yozilganUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const qulflandiRef = useRef(false);

  const yozishToxtat = () => {
    clearInterval(taymerRef.current);
    if (recorderRef.current && recorderRef.current.state !== "inactive") recorderRef.current.stop();
    streamRef.current?.getTracks().forEach((t) => t.stop());
  };

  const yozishBoshla = () => {
    if (!streamRef.current) return;
    boglamlarRef.current = [];
    const turi = MediaRecorder.isTypeSupported("video/webm;codecs=vp8,opus") ? "video/webm;codecs=vp8,opus" : "video/webm";
    const recorder = new MediaRecorder(streamRef.current, { mimeType: turi });
    recorder.ondataavailable = (e) => { if (e.data.size > 0) boglamlarRef.current.push(e.data); };
    recorder.onstop = () => {
      const blob = new Blob(boglamlarRef.current, { type: "video/webm" });
      if (qulflandiRef.current) {
        // Qulflangan — qo'lda ko'rib chiqish/yuborish uchun preview'ga o'tadi
        setYozilganUrl(URL.createObjectURL(blob));
        setHolat("korib_chiqish");
      } else {
        // Qulflanmagan — qo'yib yuborilganda DARHOL jo'natiladi (ovozli xabar kabi)
        onYubor(new File([blob], "doira_video.webm", { type: "video/webm" }));
      }
    };
    recorderRef.current = recorder;
    recorder.start();
    setSekund(0);
    setHolat("yozilmoqda");
    taymerRef.current = setInterval(() => {
      setSekund((prev) => {
        if (prev + 1 >= MAX_SONIYA) { yozishToxtat(); return prev; }
        return prev + 1;
      });
    }, 1000);
  };

  // Bosib turib yozish, qo'yib yuborsa DARHOL jo'natiladi. Yozayotganda
  // yuqoriga surilsa — qulflanadi, qo'lni olib qo'ysa ham davom etadi
  // (keyin qo'lda ko'rib chiqib yuborish/qayta yozish kerak).
  useEffect(() => {
    if (holat !== "yozilmoqda") return;
    const harakat = (e) => {
      const y = e.touches ? e.touches[0].clientY : e.clientY;
      if (boshlanishYRef.current - y > QULF_MASOFASI) { qulflandiRef.current = true; setQulflandi(true); }
    };
    const qoyildi = () => {
      if (!qulflandiRef.current) yozishToxtat();
    };
    window.addEventListener("mousemove", harakat);
    window.addEventListener("touchmove", harakat, { passive: true });
    window.addEventListener("mouseup", qoyildi);
    window.addEventListener("touchend", qoyildi);
    return () => {
      window.removeEventListener("mousemove", harakat);
      window.removeEventListener("touchmove", harakat);
      window.removeEventListener("mouseup", qoyildi);
      window.removeEventListener("touchend", qoyildi);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [holat]);

  const bosishBoshlandi = (e) => {
    e.preventDefault();
    const y = e.touches ? e.touches[0].clientY : e.clientY;
    boshlanishYRef.current = y;
    qulflandiRef.current = false;
    setQulflandi(false);
    yozishBoshla();
  };

  const qaytaYoz = () => {
    if (yozilganUrl) URL.revokeObjectURL(yozilganUrl);
    setYozilganUrl(null);
    setSekund(0);
    kameraniOch();
  };

  const yuborish = async () => {
    const javob = await fetch(yozilganUrl);
    const blob = await javob.blob();
    onYubor(new File([blob], "doira_video.webm", { type: "video/webm" }));
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-6" style={{ backgroundColor: "rgba(20,20,18,0.92)" }}>
      <button onClick={() => { streamRef.current?.getTracks().forEach((t) => t.stop()); onBekor(); }}
        className="absolute top-6 right-5 w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.15)" }}>
        <X size={18} style={{ color: "#fff" }} />
      </button>

      {holat === "xato" ? (
        <p className="text-sm text-center px-8" style={{ color: "#fff" }}>{__kbUi(xatoMatni)}</p>
      ) : (
        <>
          <div className="relative" style={{ width: 260, height: 260 }}>
            <div className="rounded-full overflow-hidden w-full h-full" style={{ border: holat === "yozilmoqda" ? "3px solid #E24B4A" : "3px solid rgba(255,255,255,0.3)" }}>
              {holat === "korib_chiqish" ? (
                <video ref={koribChiqishVideoRef} src={yozilganUrl} autoPlay loop playsInline className="w-full h-full object-cover" />
              ) : (
                <video ref={jonliVideoRef} autoPlay muted playsInline className="w-full h-full object-cover" style={{ transform: "scaleX(-1)" }} />
              )}
            </div>
            {holat === "yozilmoqda" && (
              <span className="absolute top-2 left-1/2 -translate-x-1/2 px-2.5 py-0.5 rounded-full text-xs font-bold" style={{ backgroundColor: "#E24B4A", color: "#fff" }}>
                {String(Math.floor(sekund / 60)).padStart(2, "0")}:{__kbUi(String(sekund % 60).padStart(2, "0"))}
              </span>
            )}
          </div>

          {holat === "korib_chiqish" ? (
            <div className="flex items-center gap-5">
              <button onClick={qaytaYoz} className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.15)" }}>
                <RotateCcw size={20} style={{ color: "#fff" }} />
              </button>
              <button onClick={yuborish} className="w-16 h-16 rounded-full flex items-center justify-center" style={{ backgroundColor: "#1B4B7A" }}>
                <Send size={24} style={{ color: "#fff" }} />
              </button>
            </div>
          ) : (
            <button onMouseDown={holat === "yozilmoqda" ? undefined : bosishBoshlandi}
              onTouchStart={holat === "yozilmoqda" ? undefined : bosishBoshlandi}
              onClick={qulflandi && holat === "yozilmoqda" ? yozishToxtat : undefined}
              disabled={holat === "tayyorlanmoqda"}
              className="w-16 h-16 rounded-full flex items-center justify-center select-none" style={{ backgroundColor: holat === "yozilmoqda" ? "#fff" : "#E24B4A", opacity: holat === "tayyorlanmoqda" ? 0.5 : 1, touchAction: "none" }}>
              {holat === "yozilmoqda" ? <span className="w-5 h-5 rounded-sm" style={{ backgroundColor: "#E24B4A" }} /> : <span className="w-6 h-6 rounded-full" style={{ backgroundColor: "var(--ui-legacy-background-fff, #fff)" }} />}
            </button>
          )}
          <p className="text-xs" style={{ color: "rgba(255,255,255,0.6)" }}>
            {holat === "korib_chiqish" ? __kbUi("Ko'rib chiqing va yuboring") : holat === "yozilmoqda" ? (qulflandi ? __kbUi("🔒 Qulflandi — tugatish uchun bosing") : __kbUi("⬆ Qulflash uchun suring · qo'yib yuborsangiz jo'natiladi")) : __kbUi("Yozish uchun bosib turing")}
          </p>
        </>
      )}
    </div>
  );
}

function SuhbatOynasi({ token, suhbat, onOrtga }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [xabarlar, setXabarlar] = useState([]);
  const [yuklanmoqda, setYuklanmoqda] = useState(true);
  const [matn, setMatn] = useState("");
  const [yuborilmoqda, setYuborilmoqda] = useState(false);
  const [xato, setXato] = useState("");
  const [doiraVideoOchiq, setDoiraVideoOchiq] = useState(false);
  const [ovozYozilmoqda, setOvozYozilmoqda] = useState(false);
  const [ovozQulflandi, setOvozQulflandi] = useState(false);
  const [ovozSekund, setOvozSekund] = useState(0);
  const [tanlanganXabar, setTanlanganXabar] = useState(null); // uzoq bosilgan xabar obyekti | null
  const [tahrirlanayotganXabar, setTahrirlanayotganXabar] = useState(null); // xabar obyekti | null
  const [tahrirMatni, setTahrirMatni] = useState("");
  const [ochirishTasdiqi, setOchirishTasdiqi] = useState(null); // xabar obyekti | null
  const oxiriRef = useRef(null);
  const faylInputRef = useRef(null);
  const ovozRecorderRef = useRef(null);
  const ovozStreamRef = useRef(null);
  const ovozBoglamlarRef = useRef([]);
  const ovozTaymerRef = useRef(null);
  const ovozBoshlanishYRef = useRef(0);
  const joriyUserId = useMemo(() => _tokenDanUserIdOl(token), [token]);
  const [reaksiyaTanlanayotgan, setReaksiyaTanlanayotgan] = useState(null); // xabar obyekti | null
  const [forwardQilinayotgan, setForwardQilinayotgan] = useState(null); // xabar obyekti | null
  const [forwardSuhbatlar, setForwardSuhbatlar] = useState(null); // {guruhlar, shaxsiylar} | null
  const [qidiruvOchiq, setQidiruvOchiq] = useState(false);
  const [qidiruvMatni, setQidiruvMatni] = useState("");
  const [qidiruvNatijalari, setQidiruvNatijalari] = useState(null);
  const [kimYozmoqda, setKimYozmoqda] = useState([]);
  const xabarAbortRef = useRef(null);
  const qidiruvAbortRef = useRef(null);
  const qidiruvTaymerRef = useRef(null);
  const oxirgiKorildiRef = useRef(null);
  const REAKSIYA_EMOJILARI = ["👍", "❤️", "😂", "😮", "😢", "🙏"];

  const reaksiyaQoy = async (xabar, emoji) => {
    setReaksiyaTanlanayotgan(null);
    const mavjud = (xabar.reaksiyalar || []).find((r) => r.meniki);
    try {
      if (mavjud && mavjud.emoji === emoji) {
        await fetch(`${API_BASE}/api/chat/reaksiya_olib_tashla?token=${encodeURIComponent(token)}&xabar_id=${xabar.id}`, { method: "DELETE" });
      } else {
        await fetch(`${API_BASE}/api/chat/reaksiya_qoy?token=${encodeURIComponent(token)}&xabar_id=${xabar.id}&emoji=${encodeURIComponent(emoji)}`, { method: "PUT" });
      }
      yukla();
    } catch {
      setXato("Reaksiya qo'yib bo'lmadi");
    }
  };

  const forwardBoshla = (x) => {
    setTanlanganXabar(null);
    setForwardQilinayotgan(x);
    fetch(`${API_BASE}/api/chat/guruhlarim?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((d) => setForwardSuhbatlar({ guruhlar: d.guruhlar || [], shaxsiylar: d.shaxsiylar || [] }))
      .catch(() => setXato("Suhbatlar ro'yxatini yuklab bo'lmadi"));
  };

  const forwardYubor = async (maqsad) => {
    try {
      const params = new URLSearchParams({ token, xabar_id: forwardQilinayotgan.id });
      if (maqsad.guruh_id) params.append("guruh_id", maqsad.guruh_id);
      else params.append("qabul_qiluvchi_user_id", maqsad.user_id);
      const res = await fetch(`${API_BASE}/api/chat/xabar_forward?${params}`, { method: "POST" });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Xato");
      setForwardQilinayotgan(null);
      setForwardSuhbatlar(null);
    } catch (e) {
      setXato(e.message);
    }
  };

  const qidir = (matnQiymat) => {
    setQidiruvMatni(matnQiymat);
    clearTimeout(qidiruvTaymerRef.current);
    qidiruvAbortRef.current?.abort();
    if (matnQiymat.trim().length < 2) { setQidiruvNatijalari(null); return; }
    qidiruvTaymerRef.current = setTimeout(() => {
      const controller = new AbortController();
      qidiruvAbortRef.current = controller;
      const parametr = suhbat.guruh_id ? `guruh_id=${suhbat.guruh_id}` : `boshqa_user_id=${suhbat.boshqa_user_id}`;
      fetch(`${API_BASE}/api/chat/qidir?token=${encodeURIComponent(token)}&${parametr}&matn=${encodeURIComponent(matnQiymat.trim())}`, { signal: controller.signal })
        .then((r) => r.json())
        .then((d) => setQidiruvNatijalari(d.natijalar || []))
        .catch((e) => { if (e.name !== "AbortError") setQidiruvNatijalari([]); });
    }, 300);
  };

  const xabarTahrirlashniBoshla = (x) => {
    setTanlanganXabar(null);
    setTahrirlanayotganXabar(x);
    setTahrirMatni(x.matn || "");
  };

  const xabarTahrirlashniSaqla = async () => {
    if (!tahrirMatni.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/api/chat/xabar_tahrirla`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, xabar_id: tahrirlanayotganXabar.id, yangi_matn: tahrirMatni.trim() }),
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Xato");
      setTahrirlanayotganXabar(null);
      yukla();
    } catch (e) {
      setXato(e.message);
    }
  };

  const xabarniOchir = async (x) => {
    setTanlanganXabar(null);
    try {
      const res = await fetch(`${API_BASE}/api/chat/xabar_ochir?token=${encodeURIComponent(token)}&xabar_id=${x.id}`, { method: "DELETE" });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Xato");
      setOchirishTasdiqi(null);
      yukla();
    } catch (e) {
      setXato(e.message);
    }
  };


  const [boshqaTomonKorganId, setBoshqaTomonKorganId] = useState(null);
  const [javobBerilayotgan, setJavobBerilayotgan] = useState(null); // xabar obyekti | null

  const yukla = () => {
    xabarAbortRef.current?.abort();
    const controller = new AbortController();
    xabarAbortRef.current = controller;
    const parametr = suhbat.guruh_id ? `guruh_id=${suhbat.guruh_id}` : `boshqa_user_id=${suhbat.boshqa_user_id}`;
    fetch(`${API_BASE}/api/chat/xabarlar?token=${encodeURIComponent(token)}&${parametr}`, { signal: controller.signal })
      .then((r) => r.json())
      .then((d) => {
        const royxat = d.xabarlar || [];
        setXabarlar(royxat);
        setBoshqaTomonKorganId(d.boshqa_tomon_korgan_id ?? null);
        setYuklanmoqda(false);
        setTimeout(() => oxiriRef.current?.scrollIntoView(), 50);
        if (royxat.length > 0) {
          const engSonggisi = royxat[royxat.length - 1].id;
          if (oxirgiKorildiRef.current !== engSonggisi) {
            oxirgiKorildiRef.current = engSonggisi;
            const kp = suhbat.guruh_id ? `guruh_id=${suhbat.guruh_id}` : `boshqa_user_id=${suhbat.boshqa_user_id}`;
            fetch(`${API_BASE}/api/chat/korildi_belgila?token=${encodeURIComponent(token)}&oxirgi_xabar_id=${engSonggisi}&${kp}`, { method: "POST" }).catch(() => {});
          }
        }
      })
      .catch((e) => { if (e.name !== "AbortError") setYuklanmoqda(false); });
  };

  useEffect(() => {
    oxirgiKorildiRef.current = null;
    yukla();
    return () => xabarAbortRef.current?.abort();
  }, [token, suhbat.guruh_id, suhbat.boshqa_user_id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const parametr = suhbat.guruh_id ? `guruh_id=${suhbat.guruh_id}` : `boshqa_user_id=${suhbat.boshqa_user_id}`;
    let controller = null;
    const tekshir = () => {
      if (document.visibilityState !== "visible") return;
      controller?.abort();
      controller = new AbortController();
      fetch(`${API_BASE}/api/chat/kim_yozmoqda?token=${encodeURIComponent(token)}&${parametr}`, { signal: controller.signal })
        .then((r) => r.json())
        .then((d) => setKimYozmoqda(d.ismlar || []))
        .catch(() => {});
    };
    const korinishOzgardi = () => {
      if (document.visibilityState === "visible") tekshir();
      else setKimYozmoqda([]);
    };
    tekshir();
    const oraliq = setInterval(tekshir, 6000);
    document.addEventListener("visibilitychange", korinishOzgardi);
    return () => {
      clearInterval(oraliq);
      controller?.abort();
      document.removeEventListener("visibilitychange", korinishOzgardi);
    };
  }, [token, suhbat.guruh_id, suhbat.boshqa_user_id]);

  useEffect(() => () => {
    clearTimeout(qidiruvTaymerRef.current);
    qidiruvAbortRef.current?.abort();
  }, []);

  const yozmoqdaRef = useRef(0);
  const yozayotganiniBildir = () => {
    const hozir = Date.now();
    if (hozir - yozmoqdaRef.current < 3000) return; // ortiqcha parallel so'rov yubormaydi
    yozmoqdaRef.current = hozir;
    const parametr = suhbat.guruh_id ? `guruh_id=${suhbat.guruh_id}` : `boshqa_user_id=${suhbat.boshqa_user_id}`;
    fetch(`${API_BASE}/api/chat/yozmoqda?token=${encodeURIComponent(token)}&${parametr}`, { method: "POST" }).catch(() => {});
  };

  const matnYubor = async () => {
    if (!matn.trim() || yuborilmoqda) return;
    setYuborilmoqda(true); setXato("");
    try {
      const forma = new FormData();
      forma.append("token", token);
      if (suhbat.guruh_id) forma.append("guruh_id", suhbat.guruh_id);
      else forma.append("qabul_qiluvchi_user_id", suhbat.boshqa_user_id);
      forma.append("matn", matn.trim());
      if (javobBerilayotgan) forma.append("javob_xabar_id", javobBerilayotgan.id);
      const res = await fetch(`${API_BASE}/api/chat/xabar_yubor`, { method: "POST", body: forma });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      setMatn("");
      setJavobBerilayotgan(null);
      yukla();
    } catch (e) { setXato(e.message); } finally { setYuborilmoqda(false); }
  };

  const faylniYubor = async (fayl, faylTuri) => {
    setYuborilmoqda(true); setXato("");
    try {
      const forma = new FormData();
      forma.append("token", token);
      if (suhbat.guruh_id) forma.append("guruh_id", suhbat.guruh_id);
      else forma.append("qabul_qiluvchi_user_id", suhbat.boshqa_user_id);
      forma.append("fayl_turi", faylTuri);
      forma.append("fayl", fayl);
      const res = await fetch(`${API_BASE}/api/chat/xabar_yubor`, { method: "POST", body: forma });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Xato");
      yukla();
    } catch (e) { setXato(e.message); } finally { setYuborilmoqda(false); }
  };

  const faylTanlandi = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    e.target.value = "";
    const faylTuri = f.type.startsWith("audio/") ? "audio" : f.type.startsWith("video/") ? "video" : "hujjat";
    faylniYubor(f, faylTuri);
  };

  const doiraVideoYuborildi = (fayl) => {
    setDoiraVideoOchiq(false);
    faylniYubor(fayl, "video_doira");
  };

  useEffect(() => () => {
    ovozStreamRef.current?.getTracks().forEach((t) => t.stop());
    clearInterval(ovozTaymerRef.current);
  }, []);

  const OVOZ_QULF_MASOFASI = 45; // shuncha piksel yuqoriga surilsa — qulflanadi

  const ovozYozishBoshla = () => {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then((stream) => {
        ovozStreamRef.current = stream;
        ovozBoglamlarRef.current = [];
        const recorder = new MediaRecorder(stream);
        recorder.ondataavailable = (e) => { if (e.data.size > 0) ovozBoglamlarRef.current.push(e.data); };
        ovozRecorderRef.current = recorder;
        recorder.start();
        setOvozSekund(0);
        setOvozYozilmoqda(true);
        ovozTaymerRef.current = setInterval(() => setOvozSekund((p) => p + 1), 1000);
      })
      .catch(() => setXato("Mikrofonga ruxsat berilmadi — brauzer sozlamalaridan ruxsat bering."));
  };

  const ovozYozishToxtat = () => {
    clearInterval(ovozTaymerRef.current);
    ovozStreamRef.current?.getTracks().forEach((t) => t.stop());
    setOvozYozilmoqda(false);
  };

  const ovozBekorQil = () => {
    if (ovozRecorderRef.current && ovozRecorderRef.current.state !== "inactive") {
      ovozRecorderRef.current.onstop = null;
      ovozRecorderRef.current.stop();
    }
    ovozYozishToxtat();
  };

  const ovozYuborish = () => {
    const recorder = ovozRecorderRef.current;
    if (!recorder || recorder.state === "inactive") { ovozYozishToxtat(); return; }
    recorder.onstop = () => {
      const blob = new Blob(ovozBoglamlarRef.current, { type: "audio/webm" });
      faylniYubor(new File([blob], "ovozli_xabar.webm", { type: "audio/webm" }), "audio");
    };
    recorder.stop();
    ovozYozishToxtat();
  };

  // Bosib turib yozish, qo'yib yuborsa yuboriladi — WhatsApp uslubi.
  // Yozayotganda biroz yuqoriga surilsa — "qulflanadi", shundan keyin
  // qo'lni olib qo'ysa ham yozish davom etadi (qo'lda yuborish/bekor
  // qilish kerak bo'ladi).
  useEffect(() => {
    if (!ovozYozilmoqda) return;
    const harakat = (e) => {
      const y = e.touches ? e.touches[0].clientY : e.clientY;
      if (ovozBoshlanishYRef.current - y > OVOZ_QULF_MASOFASI) setOvozQulflandi(true);
    };
    const qoyildi = () => {
      setOvozQulflandi((qulf) => {
        if (!qulf) ovozYuborish();
        return qulf;
      });
    };
    window.addEventListener("mousemove", harakat);
    window.addEventListener("touchmove", harakat, { passive: true });
    window.addEventListener("mouseup", qoyildi);
    window.addEventListener("touchend", qoyildi);
    return () => {
      window.removeEventListener("mousemove", harakat);
      window.removeEventListener("touchmove", harakat);
      window.removeEventListener("mouseup", qoyildi);
      window.removeEventListener("touchend", qoyildi);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ovozYozilmoqda]);

  const ovozBosishBoshlandi = (e) => {
    e.preventDefault();
    const y = e.touches ? e.touches[0].clientY : e.clientY;
    ovozBoshlanishYRef.current = y;
    setOvozQulflandi(false);
    ovozYozishBoshla();
  };

  return (
    <div className="px-5 pt-6 pb-4 flex flex-col" style={{ minHeight: "80vh" }}>
      {doiraVideoOchiq && <DoiraVideoYozish onYubor={doiraVideoYuborildi} onBekor={() => setDoiraVideoOchiq(false)} />}
      <div className="flex items-center justify-between mb-4">
        <button onClick={onOrtga} className="flex items-center gap-1 -ml-1.5 px-2 py-1 rounded-lg transition-colors" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>
          <ChevronLeft size={16} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} strokeWidth={2.5} />
          {suhbat.guruh_nomi || suhbat.boshqa_ismi || __kbUi("Suhbat")}
        </button>
        <button onClick={() => { setQidiruvOchiq((o) => !o); setQidiruvMatni(""); setQidiruvNatijalari(null); }}
          className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: qidiruvOchiq ? "#EAF1F7" : "transparent" }}>
          <Search size={16} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} />
        </button>
      </div>

      {qidiruvOchiq && (
        <div className="mb-3">
          <input type="text" value={qidiruvMatni} onChange={(e) => qidir(e.target.value)} autoFocus
            placeholder={__kbUi("Suhbat ichida qidirish...")} className="w-full px-3.5 py-2.5 rounded-full border text-sm mb-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          {qidiruvNatijalari && (
            <div className="space-y-1.5 max-h-52 overflow-y-auto rounded-xl border p-2" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
              {qidiruvNatijalari.length === 0 ? (
                <p className="text-xs text-center py-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hech narsa topilmadi")}</p>
              ) : (
                qidiruvNatijalari.map((n) => (
                  <div key={n.id} className="px-2.5 py-2 rounded-lg" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
                    {suhbat.guruh_id && <p className="text-[11px] font-semibold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{n.yuboruvchi_ismi}</p>}
                    <p className="text-xs" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{n.matn}</p>
                    <p className="text-[10px] mt-0.5" style={{ color: "var(--ui-legacy-color-b0aa98, #B0AA98)" }}>{__kbUi(new Date(n.yaratilgan_at).toLocaleDateString(__kbLocaleTag()))}</p>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}

      <div className="flex-1 space-y-2.5 mb-3 overflow-y-auto">
        {yuklanmoqda ? (
          <div className="py-10 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
        ) : xabarlar.length === 0 ? (
          <p className="text-sm text-center py-10" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Hali xabar yo'q — birinchi bo'lib yozing.")}</p>
        ) : (
          xabarlar.map((x) => {
            const meniki = x.yuboruvchi_user_id === joriyUserId;
            if (x.ochirilgan) {
              return (
                <div key={x.id} className="rounded-2xl px-4 py-2.5 max-w-[80%]" style={{ backgroundColor: "#F1EFE8", border: "1px solid #E5E1D8" }}>
                  <p className="text-sm italic" style={{ color: "var(--ui-legacy-color-b0aa98, #B0AA98)" }}>{__kbUi("🚫 Xabar o'chirildi")}</p>
                </div>
              );
            }
            return (
              <div key={x.id} onContextMenu={(e) => { e.preventDefault(); setTanlanganXabar(x); }}
                onTouchStart={() => { const t = setTimeout(() => setTanlanganXabar(x), 500); const tozala = () => { clearTimeout(t); window.removeEventListener("touchend", tozala); }; window.addEventListener("touchend", tozala); }}
                className="rounded-2xl px-4 py-2.5 max-w-[80%] select-none" style={{ backgroundColor: "var(--ui-legacy-background-ffffff, #FFFFFF)", border: "1px solid #E5E1D8" }}>
                {suhbat.guruh_id && <p className="text-[11px] font-semibold mb-0.5" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{x.yuboruvchi_ismi}</p>}
                {x.javob_xabar_id && (
                  <div className="rounded-lg px-2 py-1 mb-1.5 border-l-2" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", borderColor: "#1B4B7A" }}>
                    <p className="text-[11px] font-semibold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{x.javob_yuboruvchi_ismi}</p>
                    <p className="text-xs truncate" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{x.javob_matn_qisqa || (x.javob_fayl_turi ? __kbUi("📎 Fayl") : __kbUi(""))}</p>
                  </div>
                )}
                {x.matn && <p className="text-sm" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{x.matn}</p>}
                {x.fayl_turi === "audio" && (
                  <audio controls className="mt-1" style={{ height: 36 }} src={`${API_BASE}/api/chat/fayl/${x.id}?token=${encodeURIComponent(token)}`} />
                )}
                {(x.fayl_turi === "video" || x.fayl_turi === "video_doira") && (
                  <video controls className="mt-1 rounded-lg" style={{ maxWidth: 220, borderRadius: x.fayl_turi === "video_doira" ? 28 : 12 }}
                    src={`${API_BASE}/api/chat/fayl/${x.id}?token=${encodeURIComponent(token)}`} />
                )}
                {x.fayl_turi === "hujjat" && (
                  <a href={`${API_BASE}/api/chat/fayl/${x.id}?token=${encodeURIComponent(token)}`} target="_blank" rel="noreferrer"
                    className="flex items-center gap-1.5 mt-1 text-xs font-medium" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>
                    <FileSpreadsheet size={14} /> {x.fayl_nomi || uiT("Fayl")}
                  </a>
                )}
                {x.reaksiyalar && x.reaksiyalar.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {x.reaksiyalar.map((r) => (
                      <button key={r.emoji} onClick={() => reaksiyaQoy(x, r.emoji)}
                        className="text-xs px-1.5 py-0.5 rounded-full border flex items-center gap-1"
                        style={{ borderColor: r.meniki ? "#1B4B7A" : "#E5E1D8", backgroundColor: r.meniki ? "#EAF1F7" : "#F7F5F0" }}>
                        {r.emoji} {r.soni > 1 && <span style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{r.soni}</span>}
                      </button>
                    ))}
                  </div>
                )}
                <p className="text-[10px] mt-1 text-right flex items-center justify-end gap-1" style={{ color: "var(--ui-legacy-color-b0aa98, #B0AA98)" }}>
                  {x.tahrirlangan && __kbUi("tahrirlangan · ")}
                  {__kbUi(new Date(x.yaratilgan_at).toLocaleTimeString(__kbLocaleTag(), { hour: "2-digit", minute: "2-digit" }))}
                  {meniki && suhbat.boshqa_user_id && (
                    <span style={{ color: boshqaTomonKorganId && x.id <= boshqaTomonKorganId ? "#1B4B7A" : "#B0AA98" }}>
                      {boshqaTomonKorganId && x.id <= boshqaTomonKorganId ? __kbUi("✓✓") : __kbUi("✓")}
                    </span>
                  )}
                </p>
              </div>
            );
          })
        )}
        {kimYozmoqda.length > 0 && (
          <p className="text-xs italic px-1" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi(kimYozmoqda.join(", "))}{__kbUi(" yozmoqda...")}</p>
        )}
        <div ref={oxiriRef} />
      </div>

      {xato && <p className="text-xs mb-2" style={{ color: "#B0553A" }}>{__kbUi(xato)}</p>}

      {javobBerilayotgan && (
        <div className="flex items-center gap-2 mb-2 rounded-xl px-3 py-2 border-l-2" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", borderColor: "#1B4B7A" }}>
          <div className="flex-1 min-w-0">
            <p className="text-[11px] font-semibold" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{javobBerilayotgan.yuboruvchi_ismi}{__kbUi("ga javob")}</p>
            <p className="text-xs truncate" style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }}>{javobBerilayotgan.matn || (javobBerilayotgan.fayl_turi ? __kbUi("📎 Fayl") : __kbUi(""))}</p>
          </div>
          <button onClick={() => setJavobBerilayotgan(null)} className="shrink-0 w-6 h-6 rounded-full flex items-center justify-center" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>✕</button>
        </div>
      )}

      {ovozYozilmoqda ? (
        ovozQulflandi ? (
          <div className="flex items-center gap-2">
            <button onClick={ovozBekorQil} className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: "#FCEBEB" }}>
              <Trash2 size={16} style={{ color: "#A32D2D" }} />
            </button>
            <div className="flex-1 flex items-center gap-2 px-3.5 py-2.5 rounded-full" style={{ backgroundColor: "#FCEBEB" }}>
              <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: "#E24B4A" }} />
              <span className="text-sm font-semibold" style={{ color: "#A32D2D" }}>{__kbUi("🔒 Ovoz yozilmoqda — ")}{String(Math.floor(ovozSekund / 60)).padStart(2, "0")}:{__kbUi(String(ovozSekund % 60).padStart(2, "0"))}
              </span>
            </div>
            <button onClick={ovozYuborish} className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: "#1B4B7A" }}>
              <Send size={16} style={{ color: "#fff" }} />
            </button>
          </div>
        ) : (
          <div className="flex-1 flex items-center gap-2 px-3.5 py-2.5 rounded-full select-none" style={{ backgroundColor: "#FCEBEB" }}>
            <span className="w-2 h-2 rounded-full animate-pulse shrink-0" style={{ backgroundColor: "#E24B4A" }} />
            <span className="text-sm font-semibold shrink-0" style={{ color: "#A32D2D" }}>
              {String(Math.floor(ovozSekund / 60)).padStart(2, "0")}:{__kbUi(String(ovozSekund % 60).padStart(2, "0"))}
            </span>
            <span className="text-xs flex-1 text-right" style={{ color: "#A32D2D" }}>{__kbUi("⬆ qulflash uchun suring · qo'yib yuborsangiz jo'natiladi")}</span>
          </div>
        )
      ) : (
        <div className="flex items-center gap-2">
          <button onClick={() => faylInputRef.current?.click()} disabled={yuborilmoqda}
            className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
            📎
          </button>
          <button onClick={() => setDoiraVideoOchiq(true)} disabled={yuborilmoqda}
            className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)" }}>
            <Video size={17} style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }} />
          </button>
          <input ref={faylInputRef} type="file" accept="audio/*,video/*,.pdf,.doc,.docx,.xlsx" onChange={faylTanlandi} className="hidden" />
          <input type="text" value={matn} onChange={(e) => { setMatn(e.target.value); yozayotganiniBildir(); }}
            onKeyDown={(e) => { if (e.key === "Enter") matnYubor(); }}
            placeholder={uiT("Xabar yozing...")} className="flex-1 px-3.5 py-2.5 rounded-full border text-sm" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} />
          {matn.trim() ? (
            <button onClick={matnYubor} disabled={yuborilmoqda}
              className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 font-semibold text-white"
              style={{ backgroundColor: "#1B4B7A", opacity: yuborilmoqda ? 0.5 : 1 }}>
              ➤
            </button>
          ) : (
            <button onMouseDown={ovozBosishBoshlandi} onTouchStart={ovozBosishBoshlandi} disabled={yuborilmoqda}
              className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 select-none" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", touchAction: "none" }}>
              <Mic size={17} style={{ color: "var(--ui-legacy-color-5a5648, #5A5648)" }} />
            </button>
          )}
        </div>
      )}

      {tanlanganXabar && (
        <div className="fixed inset-0 z-50 flex items-end justify-center" style={{ backgroundColor: "rgba(43,43,43,0.35)" }} onClick={() => setTanlanganXabar(null)}>
          <div onClick={(e) => e.stopPropagation()} className="w-full max-w-md rounded-t-2xl bg-white p-2 pb-6" style={{ boxShadow: "0 -12px 32px rgba(43,43,43,0.18)" }}>
            <div className="w-10 h-1 rounded-full mx-auto mb-3 mt-1" style={{ backgroundColor: "#E5E1D8" }} />
            <div className="flex justify-around py-2 mb-1">
              {REAKSIYA_EMOJILARI.map((emoji) => (
                <button key={emoji} onClick={() => reaksiyaQoy(tanlanganXabar, emoji)} className="text-2xl active:scale-125 transition-transform">
                  {__kbUi(emoji)}
                </button>
              ))}
            </div>
            <button onClick={() => { setJavobBerilayotgan(tanlanganXabar); setTanlanganXabar(null); }}
              className="w-full text-left px-4 py-3 rounded-xl text-sm font-medium flex items-center gap-2.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>↩️ <InterfaceText text={__kbUi("Javob berish")}/></button>
            <button onClick={() => forwardBoshla(tanlanganXabar)}
              className="w-full text-left px-4 py-3 rounded-xl text-sm font-medium flex items-center gap-2.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("↗️ Boshqa suhbatga yuborish")}</button>
            {tanlanganXabar.yuboruvchi_user_id === joriyUserId && tanlanganXabar.matn && (
              <button onClick={() => xabarTahrirlashniBoshla(tanlanganXabar)}
                className="w-full text-left px-4 py-3 rounded-xl text-sm font-medium flex items-center gap-2.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>
                <PencilLine size={16} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /><InterfaceText text={__kbUi(" Tahrirlash")}/></button>
            )}
            {tanlanganXabar.yuboruvchi_user_id === joriyUserId && (
              <button onClick={() => { setOchirishTasdiqi(tanlanganXabar); setTanlanganXabar(null); }}
                className="w-full text-left px-4 py-3 rounded-xl text-sm font-medium flex items-center gap-2.5" style={{ color: "#A32D2D" }}>
                <Trash2 size={16} /><InterfaceText text={__kbUi(" O'chirish")}/></button>
            )}
          </div>
        </div>
      )}

      {tahrirlanayotganXabar && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-5" style={{ backgroundColor: "rgba(43,43,43,0.35)" }}>
          <div className="w-full max-w-md rounded-2xl bg-white p-4" style={{ boxShadow: "0 12px 32px rgba(43,43,43,0.18)" }}>
            <p className="text-sm font-semibold mb-2.5" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Xabarni tahrirlash")}</p>
            <textarea value={tahrirMatni} onChange={(e) => setTahrirMatni(e.target.value)} rows={3}
              className="w-full px-3.5 py-2.5 rounded-xl border text-sm mb-3" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }} autoFocus />
            <div className="flex gap-2">
              <button onClick={() => setTahrirlanayotganXabar(null)}
                className="flex-1 py-2.5 rounded-xl text-sm font-semibold" style={{ backgroundColor: "var(--ui-legacy-background-efebe1, #EFEBE1)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Bekor qilish")}/></button>
              <button onClick={xabarTahrirlashniSaqla}
                className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ backgroundColor: "#1B4B7A" }}><InterfaceText text={__kbUi("Saqlash")}/></button>
            </div>
          </div>
        </div>
      )}

      {ochirishTasdiqi && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-5" style={{ backgroundColor: "rgba(43,43,43,0.35)" }}>
          <div className="w-full max-w-md rounded-2xl bg-white p-4" style={{ boxShadow: "0 12px 32px rgba(43,43,43,0.18)" }}>
            <p className="text-sm font-semibold mb-1" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Xabarni o'chirasizmi?")}</p>
            <p className="text-xs mb-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Bu amalni qaytarib bo'lmaydi.")}</p>
            <div className="flex gap-2">
              <button onClick={() => setOchirishTasdiqi(null)}
                className="flex-1 py-2.5 rounded-xl text-sm font-semibold" style={{ backgroundColor: "var(--ui-legacy-background-efebe1, #EFEBE1)", color: "var(--ui-legacy-color-5a5648, #5A5648)" }}><InterfaceText text={__kbUi("Bekor qilish")}/></button>
              <button onClick={() => xabarniOchir(ochirishTasdiqi)}
                className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ backgroundColor: "#A32D2D" }}><InterfaceText text={__kbUi("O'chirish")}/></button>
            </div>
          </div>
        </div>
      )}

      {forwardQilinayotgan && (
        <div className="fixed inset-0 z-50 flex items-end justify-center" style={{ backgroundColor: "rgba(43,43,43,0.35)" }} onClick={() => { setForwardQilinayotgan(null); setForwardSuhbatlar(null); }}>
          <div onClick={(e) => e.stopPropagation()} className="w-full max-w-md rounded-t-2xl bg-white p-4 max-h-[70vh] overflow-y-auto" style={{ boxShadow: "0 -12px 32px rgba(43,43,43,0.18)" }}>
            <div className="w-10 h-1 rounded-full mx-auto mb-3" style={{ backgroundColor: "#E5E1D8" }} />
            <p className="text-sm font-semibold mb-3" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{__kbUi("Qayerga yuborilsin?")}</p>
            {!forwardSuhbatlar ? (
              <div className="py-6 text-center"><Loader2 size={20} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>
            ) : (
              <div className="space-y-1.5">
                {forwardSuhbatlar.guruhlar.map((g) => (
                  <button key={`g${g.id}`} onClick={() => forwardYubor({ guruh_id: g.id })}
                    className="w-full text-left px-3.5 py-2.5 rounded-xl text-sm font-medium" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>
                    {g.nomi}
                  </button>
                ))}
                {forwardSuhbatlar.shaxsiylar.map((s) => (
                  <button key={`s${s.user_id}`} onClick={() => forwardYubor({ user_id: s.user_id })}
                    className="w-full text-left px-3.5 py-2.5 rounded-xl text-sm font-medium" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>
                    {s.full_name}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// REV125: «Yordamchi» va «Kod» — bitta maydon. Kitob kodi (XB-03-A01) yozilsa — yechim, boshqa matn — yordamchiga savol.
function YordamchiKod({ open, onAssistant, onCode }) {
  useKbInterfaceLocale();
  const [value, setValue] = useState("");
  const submit = (event) => {
    event.preventDefault();
    const v = value.trim();
    if (!v) { onAssistant(""); return; }
    if (kitobKodimi(v)) onCode(v); else onAssistant(v);
    setValue("");
  };
  return <form className={`samtm-help ${open ? "is-open" : ""}`} role="search" onSubmit={submit}>
    <button type="button" className="samtm-help-bot" onClick={() => onAssistant("")} aria-expanded={Boolean(open)} title={__kbUi("AI yordamchi")} aria-label={__kbUi("AI yordamchi")}>🤖<span>{__kbUi("Yordamchi")}</span></button>
    <input value={value} onChange={(e) => setValue(e.target.value)} placeholder={__kbUi("Savol yoki kitobdagi kod…")} aria-label={__kbUi("Yordamchiga savol yoki kitobdagi kod")} autoComplete="off" spellCheck={false} />
    <button type="submit" className="samtm-help-go" aria-label={__kbUi("Yuborish")} title={__kbUi("Kod bo‘lsa — yechim, savol bo‘lsa — yordamchi javobi")}>➜</button>
  </form>;
}

function Kabinet({ token, onSessionExpired, onLogout, onToken, onProfiles, readOnly = false, initialCourses = false, initialCourseId = null }) {
  useKbInterfaceLocale();
  const { t: uiT } = useInterface();
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [membershipNotice, setMembershipNotice] = useState("");
  const [membershipRevision, setMembershipRevision] = useState(0);
  const [profileReload, setProfileReload] = useState(0);
  const [educationLoadError, setEducationLoadError] = useState("");
  const [educationReload, setEducationReload] = useState(0);
  const [talimYuklangan, setTalimYuklangan] = useState(true);
  const [educationEditing, setEducationEditing] = useState(false);
  const [assistantSeed, setAssistantSeed] = useState(null);   // REV125: yagona «Yordamchi / Kod» maydonidan savol
  const [kodTrigger, setKodTrigger] = useState(null);
  const [educationRoleChoice, setEducationRoleChoice] = useState("");
  // Rol faqat Sozlamalardan o'zgaradi: tanlangan rol bilan ta'lim sozlamalari oynasi ochiladi.
  const rolniAlmashtir = useCallback((role) => { setAccountOpen(false); setEducationRoleChoice(role); setEducationEditing(true); setTab("home"); }, []);
  const [courseNavigation, setCourseNavigation] = useState({ courseId: initialCourseId, mode: "catalog", nonce: 0 });
  const [coursesOpened, setCoursesOpened] = useState(Boolean(initialCourses || initialCourseId));
  const [presentationsOpened, setPresentationsOpened] = useState(false);
  const [presentationsAllowed, setPresentationsAllowed] = useState(false);
  const [presentationsReason, setPresentationsReason] = useState(""); // ruxsat yo'q yoki server javob bermagan sababi
  useAudiencePresence(API_BASE, token, !readOnly);
  const [holat, setHolat] = useState("yuklanmoqda");
  const [foydalanuvchi, setFoydalanuvchi] = useState(null);
  const [fanTanlash, setFanTanlash] = useState(false);   // REV106: o'qituvchi «Fanlarim»
  useEffect(() => {
    setPresentationsAllowed(false);
    if (!token || !foydalanuvchi?.user_id || readOnly) return;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 12000);
    fetch(`${String(API_BASE || "").replace(/\/+$/, "")}/api/taqdimotlar/capabilities`, {
      headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
      signal: controller.signal, cache: "no-store", credentials: "omit",
    }).then(async (response) => response.ok ? response.json() : { xato: `Taqdimot xizmati javob bermadi (${response.status}) — backend yangilanganini tekshiring.` }).then((data) => {
      if (controller.signal.aborted) return;
      const ok = data?.allowed === true || data?.admin === true || !!foydalanuvchi?.is_admin; // admin doim kira oladi — ustaxona o'zi aniq xatoni ko'rsatadi
      setPresentationsAllowed(ok);
      setPresentationsReason(ok ? "" : (data?.xato || data?.reason || "Taqdimot yaratish hisobingiz uchun hali ochilmagan."));
    }).catch(() => { if (!controller.signal.aborted) { setPresentationsAllowed(!!foydalanuvchi?.is_admin); setPresentationsReason("Taqdimot xizmatiga ulanib bo'lmadi — internet yoki backendni tekshiring."); } }).finally(() => clearTimeout(timer));
    return () => { clearTimeout(timer); controller.abort(); };
  }, [token, foydalanuvchi?.user_id, foydalanuvchi?.role, foydalanuvchi?.class, foydalanuvchi?.is_admin, readOnly, profileReload, membershipRevision]);
  const [bilimData, setBilimData] = useState(null);
  const [tab, setTab] = useState(null); // rol aniqlangach o'rnatiladi
  // REV82: onlayn bellashuv — havola kodi (#bellashuv=KOD) yoki testdagi mavzudan xona ochish.
  const [bellashuv, setBellashuv] = useState(() => ({ kod: peekGameCode(BATTLE_CODE_KEY), createFrom: null, nonce: 0 }));
  // REV83: shashka — do'st taklifi havolasi (#shashka=KOD).
  const [shashka, setShashka] = useState(() => ({ kod: peekGameCode(SHASHKA_CODE_KEY), nonce: 0 }));
  // REV85: shaxmat — do'st taklifi havolasi (#shaxmat=KOD).
  const [shaxmat, setShaxmat] = useState(() => ({ kod: peekGameCode(SHAXMAT_CODE_KEY), nonce: 0 }));
  useEffect(() => {
    const key = tab === "bellashuv" ? BATTLE_CODE_KEY : tab === "shashka" ? SHASHKA_CODE_KEY : tab === "shaxmat" ? SHAXMAT_CODE_KEY : "";
    if (key) { try { window.sessionStorage.removeItem(key); } catch { /* ixtiyoriy */ } }
  }, [tab]);
  useEffect(() => {
    const hashChanged = () => {
      const battle = gameCodeFromHash(window.location.hash, "bellashuv");
      const checkers = gameCodeFromHash(window.location.hash, "shashka");
      const chess = gameCodeFromHash(window.location.hash, "shaxmat");
      if (!battle && !checkers && !chess) return;
      window.history.replaceState({}, document.title, window.location.pathname + window.location.search);
      if (battle) { setBellashuv({ kod: battle, createFrom: null, nonce: Date.now() }); setTab("bellashuv"); }
      else if (checkers) { setShashka({ kod: checkers, nonce: Date.now() }); setTab("shashka"); }
      else { setShaxmat({ kod: chess, nonce: Date.now() }); setTab("shaxmat"); }
    };
    window.addEventListener("hashchange", hashChanged);
    return () => window.removeEventListener("hashchange", hashChanged);
  }, []);
  const [xatoMatn, setXatoMatn] = useState("");
  const [muassasalarim, setMuassasalarim] = useState([]);
  const [muassasalarYuklandi, setMuassasalarYuklandi] = useState(false);
  const [oqituvchiBoshlanishKorinishi, setOqituvchiBoshlanishKorinishi] = useState(null);
  const [ishxonaTanlash, setIshxonaTanlash] = useState(null); // bir necha ishxona bo'lsa kirishda tanlash
  const [ishJoyiAniqlandi, setIshJoyiAniqlandi] = useState(false);
  const [yonMenyuOchiq, setYonMenyuOchiq] = useState(() => {
    try { return window.localStorage.getItem("samtm_yon_menyu") !== "0"; } catch { return true; }
  });
  const yonMenyuniAlmashtir = useCallback(() => setYonMenyuOchiq((joriy) => {
    const yangi = !joriy;
    try { window.localStorage.setItem("samtm_yon_menyu", yangi ? "1" : "0"); } catch { /* jim */ }
    return yangi;
  }), []);
  // Tepada ikki bo'lim: [Ish joyim] va [Kabutar]. Bittasi ko'rinadi, ikkinchisi yashirin turadi (holati saqlanadi).
  // Kirganda avval Ta'lim maydoni ochiladi; Kabutar — tepadagi tugma bilan.
  const [kabutarOchiq, setKabutarOchiq] = useState(false);
  const [kabutarYuklangan, setKabutarYuklangan] = useState(false);
  // Admin Kabutarni butun platforma uchun o'chirsa — boshqalar "Tez kunda" ko'radi.
  const [kabutarHolati, setKabutarHolati] = useState({ yoqilgan: true, xabar: "" });
  useEffect(() => {
    let tirik = true;
    const yukla = () => fetch(`${API_BASE}/api/kabutar_holati`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (tirik && d && typeof d.yoqilgan === "boolean") setKabutarHolati({ yoqilgan: d.yoqilgan, xabar: d.xabar || "" }); })
      .catch(() => {});
    yukla();
    const yangilandi = (event) => { if (event.detail && typeof event.detail.yoqilgan === "boolean") setKabutarHolati({ yoqilgan: event.detail.yoqilgan, xabar: event.detail.xabar || "" }); };
    window.addEventListener("kabutar:holat", yangilandi);
    return () => { tirik = false; window.removeEventListener("kabutar:holat", yangilandi); };
  }, []);
  const kabutarTezKunda = !kabutarHolati.yoqilgan && !foydalanuvchi?.is_admin;
  const [kabutarOqilmagan, setKabutarOqilmagan] = useState(0);
  const [kabutarContactRequest, setKabutarContactRequest] = useState(null);
  const kabutarniOch = useCallback((ochiq) => { setKabutarOchiq(ochiq); if (ochiq) setKabutarYuklangan(true); else setTalimYuklangan(true); try { window.sessionStorage.setItem("samtm_kabutar_ochiq", ochiq ? "1" : "0"); } catch { /* jim */ } }, []);
  const kabutarOqilmaganniOl = useCallback((n) => setKabutarOqilmagan(n), []);
  const openCourses = (mode = "catalog") => {
    // Returning from chat or another tab keeps the current lesson and draft.
    if (!coursesOpened) setCourseNavigation({ courseId: null, mode, nonce: 0 });
    setCoursesOpened(true);
    setIshxonaTanlash(null); setTab("kurslar"); kabutarniOch(false);
  };
  useEffect(() => {
    setKabutarContactRequest(null);
    const openContact = (event) => {
      const userId = Number(event.detail?.userId);
      const schoolId = Number(event.detail?.schoolId);
      if (!token || !Number.isSafeInteger(userId) || userId <= 0 || !Number.isSafeInteger(schoolId) || schoolId <= 0) return;
      // The panel resolves this request against its current authorized directory.
      setKabutarContactRequest({ userId, schoolId, requestId: `${Date.now()}-${Math.random().toString(36).slice(2)}` });
      kabutarniOch(true);
    };
    window.addEventListener("kabutar:open-contact", openContact);
    return () => window.removeEventListener("kabutar:open-contact", openContact);
  }, [token, kabutarniOch]);
  // To'liq ekran ish maydonlari (portal) tepadagi "Ta'lim maydoni | Kabutar" qatorini yopmasin
  const topSwitchObsRef = useRef(null);
  const topSwitchRef = useCallback((el) => {
    if (topSwitchObsRef.current) { topSwitchObsRef.current.disconnect(); topSwitchObsRef.current = null; }
    if (!el) { document.documentElement.style.setProperty("--samtm-portal-top", "0px"); return; }
    const apply = () => {
      const base = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--samtm-top-offset")) || 0;
      document.documentElement.style.setProperty("--samtm-portal-top", `${Math.round(el.getBoundingClientRect().height + base)}px`);
    };
    apply();
    const ro = new ResizeObserver(apply);
    ro.observe(el);
    topSwitchObsRef.current = ro;
  }, []);
  useEffect(() => () => {
    document.documentElement.style.setProperty("--samtm-portal-top", "0px");
    if (topSwitchObsRef.current) topSwitchObsRef.current.disconnect();
  }, []);
  const [tanlanganMuassasa, setTanlanganMuassasa] = useState(null); // {turi, muassasa_id, muassasa_nomi, lavozim}
  const mavjudMuassasalar = (muassasalarim || []).filter((m) => MUASSASA_TURI_RANG[m.turi]);
  const faolMuassasa = tanlanganMuassasa || mavjudMuassasalar[0] || null;
  const muassasaniTanla = useCallback((m) => {
    setTanlanganMuassasa(m);
    setOqituvchiBoshlanishKorinishi({ korinish: MUASSASA_TURI_RANG[m.turi].korinish, muassasa: m, vaqt: Date.now() });
    setTab("oqituvchi");
    kabutarniOch(false);
  }, [kabutarniOch]);
  const [oyinProfil, setOyinProfil] = useState(null);
  const [kunlikMukofot, setKunlikMukofot] = useState(0);
  // Admin uchun — bazadagi haqiqiy `role`ga TEGMAYDIGAN, faqat shu qurilmada
  // ko'rinadigan "ko'rinish rejimi". Shu orqali admin har rolni (o'quvchi/
  // ota-ona/o'qituvchi/admin) BIR-BIRIGA ARALASHMASDAN, to'liq alohida
  // sinab ko'radi.
  const [adminKorinish, setAdminKorinish] = useState("admin");
  const [shablonOldindanTanlangan, setShablonOldindanTanlangan] = useState([]);
  // Test yechish jarayonida (savollar ekranida) TRUE bo'ladi — shu payt
  // pastki menyu orqali boshqa bo'limga o'tib bo'lmaydi, avval test
  // "To'xtatish" yoki "Yakunlash" bilan yakunlanishi kerak.
  const [testDavomida, setTestDavomida] = useState(false);
  // REV106: test yechilayotganda — faqat test: menyular, yon panel va yordamchilar yashiriladi.
  useEffect(() => {
    if (readOnly) return undefined;
    document.body.classList.toggle("kb-focus-test", testDavomida);
    return () => document.body.classList.remove("kb-focus-test");
  }, [testDavomida, readOnly]);
  const [talimYoliTestNishoni, setTalimYoliTestNishoni] = useState(null);
  const [talimYoliDarsNishoni, setTalimYoliDarsNishoni] = useState(null);
  const kabinetHistoryRef = useRef([]);
  const kabinetBackInProgressRef = useRef(false);
  const birInstitutAvtoOchishRef = useRef(true);

  useEffect(() => {
    if (!tab) return;
    if (kabinetBackInProgressRef.current) {
      kabinetBackInProgressRef.current = false;
      return;
    }
    const history = kabinetHistoryRef.current;
    const last = history[history.length - 1];
    if (
      !last ||
      last.tab !== tab ||
      last.adminKorinish !== adminKorinish ||
      last.oqituvchiBoshlanishKorinishi !== oqituvchiBoshlanishKorinishi
    ) {
      history.push({ tab, adminKorinish, oqituvchiBoshlanishKorinishi });
    }
  }, [adminKorinish, oqituvchiBoshlanishKorinishi, tab]);

  const kabinetTarixdanQayt = useCallback(() => {
    const history = kabinetHistoryRef.current;
    if (history.length <= 1) return false;
    history.pop();
    const previous = history[history.length - 1];
    kabinetBackInProgressRef.current = true;
    setAdminKorinish(previous.adminKorinish);
    setOqituvchiBoshlanishKorinishi(previous.oqituvchiBoshlanishKorinishi);
    setTab(previous.tab);
    return true;
  }, []);

  useEffect(() => registerPhoneBackHandler("kabinet-tab", () => {
    // Test ketayotgan paytda tasodifiy telefon "orqaga" tugmasi testni
    // tashlab yubormaydi. Test o'zining To'xtatish/Yakunlash amali bilan yopiladi.
    if (testDavomida) return true;
    return kabinetTarixdanQayt();
  }), [kabinetTarixdanQayt, testDavomida]);

  useEffect(() => {
    const controller = new AbortController();
    setHolat("yuklanmoqda");
    workspaceRequest(API_BASE, "/auth/men", token, { signal: controller.signal })
      .then((u) => {
        if (controller.signal.aborted) return;
        if (!readOnly) { rememberAccount(u, token, takeLoginMethod()); if (loginAccountRole(u)) saveLoginRole(loginAccountRole(u)); }
        setFoydalanuvchi(u);
        setTab(current => current || ((initialCourses || initialCourseId) ? "kurslar" : botStartTab() || (!readOnly && bellashuv.kod ? "bellashuv" : !readOnly && shashka.kod ? "shashka" : !readOnly && shaxmat.kod ? "shaxmat" : "") || initialEducationTab(u)));
        setHolat("tayyor");
      }).catch((error) => {
        if (controller.signal.aborted) return;
        if (error.status === 401) { onSessionExpired?.(token); return; }
        setXatoMatn(error.message || "Hisobingizni yuklab bo‘lmadi. Qayta urinib ko‘ring.");
        setHolat("xato");
      });
    return () => controller.abort();
  }, [token, onSessionExpired, profileReload]);

  // Ta’lim ma’lumotlari shu bo‘lim ochilgandagina yuklanadi.
  useEffect(() => {
    if (kabutarOchiq || tab === "kurslar" || !foydalanuvchi || muassasalarYuklandi) return;
    const controller = new AbortController();
    const user = foydalanuvchi;
    setEducationLoadError("");
    const get = (path) => workspaceRequest(API_BASE, `${path}${path.includes("?") ? "&" : "?"}token=${encodeURIComponent(token)}`, token, { signal: controller.signal });
    let membershipReady = false;
    const membership = get("/api/auth/muassasalarim")
      .then((payload) => {
        if (controller.signal.aborted) return;
        membershipReady = true;
        const list = payload.muassasalar || [];
        setMuassasalarim(list);
        if (user.role === "oqituvchi" && !user.is_admin) {
          const modes = { maktab: "maktab_rahbariyat", bogcha: "bogcha", universitet: "institut_workspace", markaz: "markaz_workspace" };
          const available = list.filter((m) => modes[m.turi]);
          if (available.length === 1) {
            setOqituvchiBoshlanishKorinishi({ korinish: modes[available[0].turi], muassasa: available[0], vaqt: Date.now() });
            setTanlanganMuassasa(available[0]);
          } else if (available.length > 1) setIshxonaTanlash(available);
        }
      }).catch((error) => { if (!controller.signal.aborted) setEducationLoadError(error.message || "Ta’lim ma’lumotlarini olib bo‘lmadi."); });
    const knowledge = get(`/api/bola/${user.user_id}/bilim`).then((data) => { if (!controller.signal.aborted) setBilimData(data); });
    const reward = readOnly ? Promise.resolve() : workspaceRequest(API_BASE, "/api/oyin/kunlik-kirish", token, { method: "POST", body: { token }, signal: controller.signal })
      .then((data) => { if (!controller.signal.aborted && data.profile) setOyinProfil(data.profile); });
    Promise.allSettled([membership, knowledge, reward]).then(() => {
      if (!controller.signal.aborted && membershipReady) { setMuassasalarYuklandi(true); setIshJoyiAniqlandi(true); }
    });
    return () => controller.abort();
  }, [kabutarOchiq, tab, foydalanuvchi, token, muassasalarYuklandi, readOnly, educationReload]);

  const institutionJoined = ({ profile, result } = {}) => {
    setMembershipRevision((current) => current + 1);
    setMuassasalarYuklandi(false);
    setMuassasalarim([]); setTanlanganMuassasa(null); setIshxonaTanlash(null);
    setOqituvchiBoshlanishKorinishi(null);
    setMembershipNotice(result?.joy_nomi ? `${result.joy_nomi} — muassasaga ulandingiz.` : "Muassasaga ulandingiz.");
    if (profile) {
      setFoydalanuvchi(profile);
      setTab(profile.is_admin || ["oqituvchi", "ota-ona"].includes(profile.role) ? initialEducationTab(profile) : ["test", "mavzular", "ai_ustoz"].includes(tab) ? tab : initialEducationTab(profile));
    } else setProfileReload((n) => n + 1);
    kabutarniOch(false);
  };

  if (holat === "yuklanmoqda") {
    return <Qobiq><div className="text-center"><Loader2 size={28} className="animate-spin mx-auto mb-3" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /><p className="text-sm" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}><InterfaceText text={__kbUi("Yuklanmoqda...")}/></p></div></Qobiq>;
  }
  if (holat === "xato") {
    return <Qobiq><div className="text-center"><WifiOff size={28} className="mx-auto mb-3" style={{ color: "#B0553A" }} /><p className="text-sm" role="alert" style={{ color: "#B0553A" }}>{__kbUi(xatoMatn)}</p><button className="kb-work-primary" onClick={() => setProfileReload((n) => n + 1)}><InterfaceText text={__kbUi("Qayta urinish")}/></button><button className="mt-3 block mx-auto" onClick={() => setAccountOpen(true)}><InterfaceText text={__kbUi("Kirish sozlamalari")}/></button>{accountOpen && <AccountSecurity apiBase={API_BASE} token={token} onToken={onToken} onLogout={onLogout} onClose={() => setAccountOpen(false)} />}</div></Qobiq>;
  }
  if (!kabutarOchiq && tab !== "kurslar" && ishxonaTanlash && ishxonaTanlash.length > 1) {
    const IKON = { maktab: "🏫", bogcha: "🧸", universitet: "🎓", markaz: "📚" };
    const TUR = { maktab: "Maktab", bogcha: "Bog‘cha", universitet: "Institut / universitet", markaz: "O‘quv markazi" };
    const KORINISH = { maktab: "maktab_rahbariyat", bogcha: "bogcha", universitet: "institut_workspace", markaz: "markaz_workspace" };
    return <Qobiq><div className="w-full max-w-lg">
      <h2 className="text-xl font-bold mb-1" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }}>{__kbUi("Ishxonani tanlang")}</h2>
      <p className="text-sm mb-5" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Siz bir necha muassasada ishlaysiz. Qaysi biriga kirmoqchisiz?")}</p>
      <div className="space-y-2">
        {ishxonaTanlash.map((m, i) => <button key={`${m.turi}-${m.muassasa_id}-${i}`} type="button" onClick={() => { setOqituvchiBoshlanishKorinishi({ korinish: KORINISH[m.turi], muassasa: m, vaqt: Date.now() }); setTanlanganMuassasa(m); setTab("oqituvchi"); setIshxonaTanlash(null); }} className="w-full flex items-center gap-3 rounded-2xl border bg-white p-4 text-left hover:shadow-md" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)" }}>
          <span className="text-2xl">{IKON[m.turi] || __kbUi("🏢")}</span>
          <span className="min-w-0 flex-1"><span className="block font-bold truncate" style={{ color: "var(--ui-legacy-color-2b2b2b, #2B2B2B)" }}>{m.muassasa_nomi || m.display_name || m.nomi || __kbUi(TUR[m.turi])}</span><span className="block text-xs" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi(TUR[m.turi])}{m.lavozim ? __kbUi(` · ${m.lavozim}`) : __kbUi("")}</span></span>
          <ChevronRight size={18} style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} />
        </button>)}
        <button type="button" onClick={() => setIshxonaTanlash(null)} className="w-full rounded-2xl border p-3 text-sm font-semibold" style={{ borderColor: "var(--ui-legacy-borderColor-e5e1d8, #E5E1D8)", color: "var(--ui-legacy-color-5a5648, #5A5648)", background: "var(--ui-legacy-background-faf9f6, #FAF9F6)" }}>{__kbUi("Umumiy ish maydoni (to‘garaklar)")}</button>
      </div>
    </div></Qobiq>;
  }

  // Admin uchun — mahalliy ko'rinish rejimi; boshqalar uchun — haqiqiy rol
  const korinishRoli = foydalanuvchi?.is_admin ? adminKorinish : (foydalanuvchi?.role || "oquvchi");
  // REV106: o'qituvchi kirishda fanlarini tanlaydi; tanlamaguncha boshqa bo'limlar ochilmaydi.
  const oqituvchiMi = !readOnly && !foydalanuvchi?.is_admin && foydalanuvchi?.role === "oqituvchi";
  const oqituvchiFanlari = foydalanuvchi?.learning_profile?.fanlar || [];
  const fanSorash = oqituvchiMi && (fanTanlash || !oqituvchiFanlari.length);
  // REV103: kunlik vaqt faqat bog'cha bolasining o'z hisobida (admin ko'rish rejimida hisoblanmaydi).
  const bogchaVaqti = !readOnly && !foydalanuvchi?.is_admin && korinishRoli !== "admin" && korinishRoli !== "oqituvchi" && korinishRoli !== "ota-ona"
    && _kbAccountRole(foydalanuvchi) === "bogcha";
  const joriyRang = joriyRangniHisobla(foydalanuvchi, korinishRoli);

  // O'qituvchining pastki menyusiga MUASSASA turiga qarab moslashuvchan
  // 1 ta qo'shimcha tugma — "Maktabim"/"Bog'cham"/"Universitetim"/
  // "Markazim" (rahbariyat bo'lsa — boshqaruv ekraniga, oddiy xodim
  // bo'lsa — o'z guruhi/sinfiga olib boradi).
  const MUASSASA_LABELLARI = {
    maktab: { nom: "Maktabim", korinish: "maktab_rahbariyat" },
    bogcha: { nom: "Bog'cham", korinish: "bogcha" },
    universitet: { nom: "Institutim", korinish: "institut_workspace" },
    markaz: { nom: "Markazim", korinish: "markaz_workspace" },
  };
  const birinchiMuassasa = muassasalarim[0];
  const muassasaBandi = birinchiMuassasa && MUASSASA_LABELLARI[birinchiMuassasa.turi]
    ? { kalit: "oqituvchi_muassasa", nom: MUASSASA_LABELLARI[birinchiMuassasa.turi].nom, ikon: Building2, korinish: MUASSASA_LABELLARI[birinchiMuassasa.turi].korinish }
    : null;

  const tabTanlandi = (yangiTab) => {
    if (yangiTab === "kurslar") { openCourses("catalog"); return; }
    if (yangiTab === "taqdimotlar") {
      if (readOnly) return;
      if (!presentationsAllowed) { setMembershipNotice(presentationsReason || "Taqdimot yaratish hisobingiz uchun hali ochilmagan."); return; } // jim qolmasin
      setPresentationsOpened(true); setIshxonaTanlash(null); setTab("taqdimotlar"); kabutarniOch(false); return;
    }
    if (yangiTab === "oqituvchi_muassasa" && muassasaBandi) {
      setOqituvchiBoshlanishKorinishi({ korinish: muassasaBandi.korinish, vaqt: Date.now() });
      setTab("oqituvchi");
    } else {
      if (yangiTab === "oqituvchi") setOqituvchiBoshlanishKorinishi({ korinish: "togarak", vaqt: Date.now() });
      setTab(yangiTab);
    }
  };

  const korinishOzgardi = (yangi) => {
    setAdminKorinish(yangi);
    setTab(yangi === "admin" ? "admin" : yangi === "oqituvchi" ? "oqituvchi" : yangi === "ota-ona" ? "farzand" : "bilim");
  };

  const tabMalumoti = {
    taqdimotlar: ["Taqdimot yaratish", "Mavzu, dizayn va tayyor slaydlar"],
    kurslar: ["Kurslar va to‘garaklar", "Darslar, mashqlar va mustaqil o‘qish"],
    admin: ["Kontent boshqaruvi", "Shablon va import markazi"],
    admin_muassasalar: ["Muassasalar", "Ro'yxat, yaratish va boshqaruv markazi"],
    admin_testlar: ["Testlar", "Savollar va natijalarni boshqarish"],
    admin_mavzular: ["Mavzular", "DTS va ta’lim mazmuni"],
    admin_korinish: ["O‘quvchi ko‘zi bilan", "Bog‘cha, maktab, markaz yoki institut o‘quvchisi ko‘rinishi"],
    admin_ovoz: ["Ovozli matn", "O‘zbekcha o‘qish va gapirib yozish"],
    admin_statistikalar: ["Statistikalar", "Tizimdan aniq o‘quvchigacha"],
    admin_moderatsiya: ["Moderatsiya", "Sifat va xavfsizlik nazorati"],
    oqituvchi: ["To‘garak va repetitorlik", "Guruhlar (50 tagacha o‘quvchi), darslar, to‘lov va davomat"],
    kutubxonam: ["Kutubxonam", "Hujjatlaringiz polka va qatorlarda — AI yordamchi topib beradi"],
    ovoz: ["Ovoz ⇄ Matn", "Matnni ovozga, ovozni matnga"],
    oqituvchi_analitika: ["Statistikalar", "Ish joyi, guruh va o‘quvchi tahlili"],
    farzand: ["Farzand tahlili", "Bilim, faollik va keyingi qadamlar"],
    bilim: ["Mening tahlilim", "Barcha ta’lim muhitlaridagi rivojim"],
    institutim: ["Mening institutim", "Guruhim, kursim va muhim sanalar"],
    bellashuv: ["Bellashuv", "Do‘stlar bilan onlayn test o‘yini"],
    oyinlar: ["O‘yinlar", "Bellashuv, shashka va aql o‘yinlari"],
    shashka: ["Shashka", "Bot, onlayn raqib yoki do‘st bilan"],
    shaxmat: ["Shaxmat", "Bot, onlayn raqib yoki do‘st bilan"],
    chempionat: ["Bolalar ligasi", "Jamoaviy chempionatlar va kuboklar"],
    ai_ustoz: ["AI Ustoz", "Sizga mos individual dars"],
    mavzular: ["Mavzular", "Ta’limingizga mos fan va mavzular"],
    test: ["Test markazi", "Bilimni tekshirish va mustahkamlash"],
    xabar: ["Xabarlar", "Bildirishnoma va suhbatlar"],
    profil: ["Profil", "Shaxsiy ma’lumot va ulanishlar"],
  }[tab] || ["Kabutar Ta’lim", "Sizning ta’lim maydoningiz"];

  return (
    <div className="min-h-screen pb-20" style={{ backgroundColor: "var(--ui-legacy-background-f7f5f0, #F7F5F0)", backgroundImage: "url(\"data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%22260%22%20height%3D%22260%22%20viewBox%3D%220%200%20260%20260%22%3E%3Cg%20fill%3D%22none%22%20stroke%3D%22%23E3DECE%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cg%20transform%3D%22translate%2818%2C24%29%20rotate%28-12%29%22%3E%3Crect%20x%3D%220%22%20y%3D%220%22%20width%3D%2230%22%20height%3D%2222%22%20rx%3D%222%22/%3E%3Cline%20x1%3D%2215%22%20y1%3D%220%22%20x2%3D%2215%22%20y2%3D%2222%22/%3E%3Cline%20x1%3D%224%22%20y1%3D%226%22%20x2%3D%2212%22%20y2%3D%226%22/%3E%3Cline%20x1%3D%224%22%20y1%3D%2211%22%20x2%3D%2212%22%20y2%3D%2211%22/%3E%3Cline%20x1%3D%2218%22%20y1%3D%226%22%20x2%3D%2226%22%20y2%3D%226%22/%3E%3Cline%20x1%3D%2218%22%20y1%3D%2211%22%20x2%3D%2226%22%20y2%3D%2211%22/%3E%3C/g%3E%3Cg%20transform%3D%22translate%28160%2C20%29%20rotate%2838%29%22%3E%3Crect%20x%3D%220%22%20y%3D%220%22%20width%3D%227%22%20height%3D%2232%22%20rx%3D%221.5%22/%3E%3Cpath%20d%3D%22M0%2032%20L3.5%2040%20L7%2032%20Z%22/%3E%3Cline%20x1%3D%220%22%20y1%3D%226%22%20x2%3D%227%22%20y2%3D%226%22/%3E%3C/g%3E%3Cg%20transform%3D%22translate%2870%2C110%29%20rotate%288%29%22%3E%3Crect%20x%3D%220%22%20y%3D%220%22%20width%3D%2246%22%20height%3D%2210%22%20rx%3D%221.5%22/%3E%3Cline%20x1%3D%228%22%20y1%3D%220%22%20x2%3D%228%22%20y2%3D%225%22/%3E%3Cline%20x1%3D%2216%22%20y1%3D%220%22%20x2%3D%2216%22%20y2%3D%225%22/%3E%3Cline%20x1%3D%2224%22%20y1%3D%220%22%20x2%3D%2224%22%20y2%3D%225%22/%3E%3Cline%20x1%3D%2232%22%20y1%3D%220%22%20x2%3D%2232%22%20y2%3D%225%22/%3E%3Cline%20x1%3D%2240%22%20y1%3D%220%22%20x2%3D%2240%22%20y2%3D%225%22/%3E%3C/g%3E%3Cg%20transform%3D%22translate%28185%2C140%29%22%3E%3Crect%20x%3D%220%22%20y%3D%2210%22%20width%3D%2230%22%20height%3D%2234%22%20rx%3D%227%22/%3E%3Crect%20x%3D%227%22%20y%3D%220%22%20width%3D%2216%22%20height%3D%2214%22%20rx%3D%223%22/%3E%3Cline%20x1%3D%2215%22%20y1%3D%2220%22%20x2%3D%2215%22%20y2%3D%2234%22/%3E%3Ccircle%20cx%3D%2215%22%20cy%3D%2227%22%20r%3D%221.5%22%20fill%3D%22%23E3DECE%22%20stroke%3D%22none%22/%3E%3C/g%3E%3Cg%20transform%3D%22translate%2830%2C175%29%20rotate%28-25%29%22%3E%3Crect%20x%3D%220%22%20y%3D%220%22%20width%3D%226%22%20height%3D%2228%22%20rx%3D%222%22/%3E%3Cpath%20d%3D%22M0%2028%20L3%2035%20L6%2028%20Z%22/%3E%3Crect%20x%3D%220%22%20y%3D%22-4%22%20width%3D%226%22%20height%3D%225%22/%3E%3C/g%3E%3Cg%20transform%3D%22translate%28120%2C200%29%20rotate%28-10%29%22%3E%3Ccircle%20cx%3D%2210%22%20cy%3D%2210%22%20r%3D%2210%22/%3E%3Cline%20x1%3D%2210%22%20y1%3D%224%22%20x2%3D%2210%22%20y2%3D%2210%22/%3E%3Cline%20x1%3D%2210%22%20y1%3D%2210%22%20x2%3D%2214%22%20y2%3D%2213%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")", backgroundRepeat: "repeat", fontFamily: "'Inter', system-ui, sans-serif" }}>
      {kunlikMukofot > 0 && (
        <div className="fixed z-[100] top-4 left-1/2 -translate-x-1/2 px-4 py-2.5 rounded-full text-sm font-bold text-white shadow-xl" style={{ backgroundColor: "#7A5412" }} role="status">
          🔥 +{kunlikMukofot}{__kbUi(" kunlik ochko")}</div>
      )}
      <style>{`
        button:not(:disabled) { transition: transform 0.12s ease, opacity 0.12s ease, box-shadow 0.15s ease, background-color 0.15s ease, border-color 0.15s ease; }
        button:not(:disabled):active { transform: scale(0.97); }
        button:disabled { cursor: not-allowed; }
        input, textarea, select {
          transition: border-color 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease;
        }
        input:focus-visible, textarea:focus-visible, select:focus-visible,
        input:focus, textarea:focus, select:focus {
          outline: none;
          border-color: #1B4B7A !important;
          box-shadow: 0 0 0 3px rgba(27,75,122,0.14);
          background-color: #FFFFFF;
        }
        /* Barcha chegarali kirish maydonlari — bir xil, nozik iliq fon
           (oq kartochkadan bir oz ajralib turadi), hover'da chegara
           bir oz to'qroq bo'ladi */
        input.border, textarea.border, select.border {
          background-color: #FAF8F2;
        }
        input.border:hover:not(:focus), textarea.border:hover:not(:focus), select.border:hover:not(:focus) {
          border-color: #C4BFAF;
        }
        input.border::placeholder, textarea.border::placeholder {
          color: #B0AA98;
        }
        button:focus-visible {
          outline: 2px solid #1B4B7A;
          outline-offset: 2px;
        }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #D8D3C7; border-radius: 999px; }
        ::-webkit-scrollbar-thumb:hover { background: #C4BFAF; }
        /* Oq fonli kartochkalar — butun ilova bo'ylab bir xil, nozik
           "ko'tarilgan" ko'rinish (allaqachon shadow-sm bo'lganlarga
           ham zid kelmaydi, faqat kuchsizroq bazasini beradi) */
        .rounded-2xl.bg-white.border, .rounded-xl.bg-white.border {
          box-shadow: 0 1px 2px rgba(43,43,43,0.03), 0 2px 6px rgba(43,43,43,0.045);
        }
        /* "Bo'sh holat" kartochkalari (p-6 + text-center + oq fon) —
           barchasiga bir xil, nozik quti-ikonka, alohida-alohida
           yozib chiqmasdan */
        .rounded-2xl.p-6.text-center.bg-white.border::before {
          content: "";
          display: block;
          width: 44px;
          height: 44px;
          margin: 0 auto 12px;
          border-radius: 999px;
          background-color: #EAF1F7;
          background-image: url('data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%231B4B7A" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"%3E%3Cpolyline points="22 12 16 12 14 15 10 15 8 12 2 12"/%3E%3Cpath d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/%3E%3C/svg%3E');
          background-repeat: no-repeat;
          background-position: center;
          background-size: 20px 20px;
        }
        /* Asosiy (oq matnli, qalin) tugmalar — butun ilova bo'ylab bir xil
           chuqurlik/soya, alohida-alohida yozib chiqmasdan */
        button.font-semibold.text-white:not(:disabled) {
          box-shadow: 0 1px 2px rgba(0,0,0,0.06), 0 3px 10px rgba(0,0,0,0.10);
        }
        button.font-semibold.text-white:not(:disabled):hover {
          box-shadow: 0 2px 4px rgba(0,0,0,0.08), 0 5px 16px rgba(0,0,0,0.15);
          filter: brightness(1.04);
        }
        button.font-semibold.text-white:not(:disabled):active {
          box-shadow: 0 1px 2px rgba(0,0,0,0.08);
          filter: brightness(0.96);
        }
        /* Ikkinchi darajali (chegarali, oq fon) tugmalar — nozik hover */
        button.border:not(:disabled):hover {
          filter: brightness(0.98);
        }
        @media (prefers-reduced-motion: reduce) {
          button:not(:disabled) { transition: none; }
          button:not(:disabled):active { transform: none; }
        }
      `}</style>
      <style>{`
        .samtm-top-switch{position:fixed;left:0;right:0;top:var(--samtm-top-offset,0px);z-index:2147483100;display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr) auto;gap:6px;padding:8px 10px;background:rgba(247,245,240,.92);backdrop-filter:blur(8px);border-bottom:1px solid #E5E1D8}
        .samtm-top-switch{grid-template-columns:auto minmax(0,1fr) auto auto!important;align-items:center;border-bottom:3px solid var(--space-color,#1B4B7A)!important}
        .samtm-top-switch.is-talim{--space-color:#1B4B7A}
        .samtm-top-switch.is-kabutar{--space-color:#0D7A77}
        .samtm-space{display:flex;gap:0;padding:3px;border-radius:16px;background:#EEEAE0;border:1px solid #E0DACC}
        .samtm-space button{border:0!important;border-radius:13px!important;background:transparent!important;color:#6B6658!important;box-shadow:none!important;padding:9px 14px!important}
        .samtm-space button.on{background:var(--space-color)!important;color:#fff!important;box-shadow:0 6px 18px rgba(0,0,0,.18)!important;transform:translateY(-1px)}
        .samtm-help{display:flex;align-items:center;gap:4px;min-width:0;max-width:560px;width:100%;justify-self:center;padding:3px;border-radius:16px;background:#fff;border:1.5px solid #D9E3EA}
        .samtm-help:focus-within,.samtm-help.is-open{border-color:var(--space-color);box-shadow:0 0 0 3px rgba(27,75,122,.12)}
        .samtm-help .samtm-help-bot{flex:none;border:0!important;background:#EAF4F2!important;color:#0D7A77!important;padding:7px 11px!important;border-radius:12px!important;font-size:13px!important;gap:5px!important}
        .samtm-help input{flex:1;min-width:0;border:0;outline:0;background:transparent;font:600 14px/1.2 system-ui,sans-serif;color:#21384C;padding:8px 6px}
        .samtm-help .samtm-help-go{flex:none;border:0!important;background:var(--space-color)!important;color:#fff!important;padding:7px 12px!important;border-radius:12px!important}
        @media(max-width:720px){.samtm-top-switch{grid-template-columns:auto auto auto!important}.samtm-help{grid-column:1/-1;grid-row:2;max-width:none}.samtm-help .samtm-help-bot span{display:none}.samtm-space button{padding:8px 10px!important;font-size:13px!important}}
        .samtm-top-switch button{display:flex;align-items:center;justify-content:center;gap:8px;padding:11px 14px;border-radius:14px;font-weight:900;font-size:14px;border:1px solid #E5E1D8;background:#fff;color:#5A5648;transition:all .15s}
        .samtm-top-switch button.on{background:#1B4B7A;color:#fff;border-color:#1B4B7A;box-shadow:0 8px 24px rgba(27,75,122,.25)}
        .samtm-top-switch b{min-width:22px;height:22px;padding:0 6px;border-radius:999px;background:#B0553A;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:11px}
        .premium-sidebar{top:var(--samtm-portal-top,64px) !important;height:calc(100vh - var(--samtm-portal-top,64px));inset:auto auto 0 0 !important}
        .premium-topbar{top:var(--samtm-portal-top,64px) !important}
        .samtm-kabutar-full{min-height:calc(100vh - var(--samtm-portal-top,64px))}
        .samtm-tez-kunda{margin-left:6px;font-size:10px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;padding:2px 7px;border-radius:999px;background:#FDF3E0;color:#8A5A1C;vertical-align:middle}
        .samtm-tez-kunda-panel{max-width:520px;margin:12vh auto 0;padding:32px 28px;text-align:center;background:#fff;border:1px solid #E5E1D8;border-radius:24px;box-shadow:0 12px 40px rgba(27,75,122,.08)}
        .samtm-tez-kunda-panel>span{display:block;font-size:44px;margin-bottom:8px}
        .samtm-tez-kunda-panel>h2{font-size:22px;font-weight:800;color:#1B4B7A;margin:0 0 8px}
        .samtm-tez-kunda-panel>p{font-size:14px;line-height:1.55;color:#5A5648;margin:0 0 20px}
        .samtm-top-spacer{height:calc(var(--samtm-portal-top,64px) - var(--samtm-top-offset,0px))}
        .samtm-test-active .samtm-top-switch,.samtm-test-active .samtm-top-spacer{display:none!important}
        .samtm-test-active{--samtm-portal-top:0px!important}
        .samtm-muassasa-strip{display:flex;gap:8px;padding:10px 12px 4px;overflow-x:auto;align-items:stretch;margin-left:264px}
        .samtm-muassasa-strip.yon-yopiq{margin-left:0}
        @media (max-width:1120px) and (min-width:821px){.samtm-muassasa-strip{margin-left:92px}}
        @media (max-width:820px){.samtm-muassasa-strip{margin-left:0}}
        .samtm-yon-yopiq .premium-sidebar{display:none !important}.samtm-yon-yopiq .premium-app-main{margin-left:0 !important}
        .samtm-yon-toggle{position:fixed;left:8px;bottom:14px;z-index:2147483050;width:40px;height:40px;border-radius:12px;border:1px solid #E5E1D8;background:#fff;color:#1B4B7A;font-weight:900;box-shadow:0 6px 20px rgba(23,50,75,.15)}
        @media (max-width:820px){.samtm-yon-toggle{display:none}}
        .samtm-muassasa-card{display:flex;align-items:stretch;flex:0 0 auto;min-width:140px;max-width:220px;border-radius:16px;border:1px solid #E5E1D8;background:#fff;transition:all .18s;overflow:hidden}
        .samtm-muassasa-card.on{flex:1 1 320px;max-width:none;background:var(--m-rang);border-color:var(--m-rang);color:#fff;box-shadow:0 12px 30px rgba(0,0,0,.14);transform:translateY(-2px)}
        .samtm-muassasa-main{display:flex;align-items:center;gap:10px;flex:1;min-width:0;padding:10px 12px;text-align:left;background:transparent;border:0;color:inherit}
        .samtm-muassasa-ikon{width:38px;height:38px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:20px;background:var(--m-yengil);flex-shrink:0}
        .samtm-muassasa-card.on .samtm-muassasa-ikon{background:rgba(255,255,255,.18)}
        .samtm-muassasa-matn{display:flex;flex-direction:column;min-width:0}
        .samtm-muassasa-matn b{font-size:13px;font-weight:900;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:inherit}
        .samtm-muassasa-matn small{font-size:10px;font-weight:700;opacity:.8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .samtm-muassasa-card:not(.on) .samtm-muassasa-matn b{color:#21384C}.samtm-muassasa-card:not(.on) .samtm-muassasa-matn small{color:#7A8794}

      `}</style>
      {tab !== "test" && !testDavomida && <>
        <div className="samtm-top-spacer" aria-hidden="true" />
        {/* REV125: qayerda turganingiz aniq — «Ta'lim maydoni | Kabutar» bitta yorliqli tanlov, faoli rangli va ostidagi chiziq shu rangda.
            «Yordamchi» va «Kod» — bitta maydon: kitob kodi yozilsa yechim ochiladi, oddiy savol yozilsa — yordamchiga boradi. */}
        <div className={`samtm-top-switch ${kabutarOchiq ? "is-kabutar" : "is-talim"}`} ref={topSwitchRef}>
          <div className="samtm-space" role="tablist" aria-label={uiT("Bo‘lim")}>
            <button type="button" role="tab" aria-selected={!kabutarOchiq} className={kabutarOchiq ? "" : "on"} onClick={() => kabutarniOch(false)} title={uiT("Ta’lim maydoni — turgan joyingiz saqlanadi")}>🧭 <InterfaceText text={__kbUi("Ta’lim maydoni")}/></button>
            <button type="button" role="tab" aria-selected={kabutarOchiq} className={kabutarOchiq ? "on" : ""} onClick={() => kabutarniOch(true)} title={kabutarTezKunda ? uiT("Kabutar — tez kunda") : uiT("Kabutar — suhbatlar")}><MessageCircle size={16} />{__kbUi(" Kabutar")}{kabutarTezKunda ? <span className="samtm-tez-kunda">{uiT("tez kunda")}</span> : kabutarOqilmagan > 0 && <b>{kabutarOqilmagan}</b>}</button>
          </div>
          <YordamchiKod open={assistantOpen} onAssistant={(text) => { setAssistantSeed(text ? { text, n: Date.now() } : null); setAssistantOpen(text ? true : (v) => !v); }}
            onCode={(code) => setKodTrigger({ code, n: Date.now() })} />
          <KitobKodQidiruv apiBase={API_BASE} token={token} hideBar trigger={kodTrigger} />
          <InterfaceSettingsButton/>
          {!readOnly && <button type="button" className="kb-account-top-button" aria-label={uiT("Akkaunt va kirish sozlamalari")} title={uiT("Akkaunt va kirish")} onClick={() => setAccountOpen(true)}><User size={18} /></button>}
        </div>
      </>}
      <KabutarAssistant open={assistantOpen && !testDavomida && tab !== "test"} onClose={() => setAssistantOpen(false)} token={token} apiBase={API_BASE} user={foydalanuvchi} readOnly={readOnly} seed={assistantSeed} />
      {bogchaVaqti && token && <React.Suspense fallback={null}>
        <KidTimeGuard apiBase={API_BASE} token={token} userId={foydalanuvchi?.user_id || ""} tab={tab} overlay={kabutarOchiq ? "Kabutar" : ""} busy={testDavomida}
          jins={_ovozJinsiniTuzat(foydalanuvchi?.ovoz_jinsi || foydalanuvchi?.jins || "qiz")} grade={foydalanuvchi?.class || ""}
          onGo={(keyingi) => { kabutarniOch(false); tabTanlandi(keyingi); }} onLogout={onLogout} />
      </React.Suspense>}
      {accountOpen && !readOnly && <AccountSecurity apiBase={API_BASE} token={token} onToken={onToken} onLogout={onLogout} onClose={() => setAccountOpen(false)} onChangeRole={foydalanuvchi?.is_admin ? undefined : rolniAlmashtir} />}
      {kabutarYuklangan && kabutarTezKunda && <div className="samtm-kabutar-full" style={{ display: kabutarOchiq ? "block" : "none" }}>
        <div className="samtm-tez-kunda-panel" role="status">
          <span aria-hidden="true">🕊️</span>
          <h2>{uiT("Kabutar — tez kunda")}</h2>
          <p>{kabutarHolati.xabar || uiT("Suhbatlar bo‘limi tez kunda ishga tushadi.")}</p>
          <button type="button" className="kb-work-primary" onClick={() => kabutarniOch(false)}>🧭 <InterfaceText text={__kbUi("Ta’lim maydoniga qaytish")} /></button>
        </div>
      </div>}
      {kabutarYuklangan && !kabutarTezKunda && <div className="samtm-kabutar-full" style={{ display: kabutarOchiq ? "block" : "none" }}>
        {!kabutarHolati.yoqilgan && <div className="kb-app-notice" role="status"><span>{__kbUi("🔒 Kabutar boshqa foydalanuvchilar uchun o‘chirilgan — ular «Tez kunda» ko‘radi. Siz admin sifatida ko‘rmoqdasiz.")}</span></div>}
        <React.Suspense fallback={<div className="py-10 text-center"><Loader2 size={26} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /></div>}>
          <KabutarPanel
            token={token}
            apiBase={API_BASE}
            title={uiT("Suhbatlar")}
            active={kabutarOchiq}
            requestedContact={kabutarContactRequest}
            maktabId={null}
            scope={null}
            onClose={() => kabutarniOch(false)}
            onUnread={kabutarOqilmaganniOl}
          />
        </React.Suspense>
      </div>}
      {talimYuklangan && <div style={{ display: kabutarOchiq ? "none" : "block" }}>
      {!readOnly && <AccountNotice user={foydalanuvchi} onOpenSettings={() => setAccountOpen(true)} />}
      {membershipNotice && <div className="kb-app-notice" role="status"><span>{__kbUi(membershipNotice)}</span><button type="button" aria-label={__kbUi("Xabarni yopish")} onClick={() => setMembershipNotice("")}>×</button></div>}
      {educationLoadError && <div className="kb-app-error" role="alert"><p>{__kbUi(educationLoadError)}</p><button className="kb-work-primary" onClick={() => setEducationReload((n) => n + 1)}><InterfaceText text={__kbUi("Qayta urinish")}/></button></div>}
      {fanSorash && !(educationEditing || needsEducation(foydalanuvchi, tab)) ? <React.Suspense fallback={<p className="p-6" role="status">{__kbUi("Yuklanmoqda…")}</p>}>
        <TeacherSubjects apiBase={API_BASE} token={token} required={!oqituvchiFanlari.length} onClose={() => setFanTanlash(false)}
          onSaved={(fanlar) => { setFoydalanuvchi((u) => ({ ...u, learning_profile: { ...(u?.learning_profile || {}), fanlar } })); setFanTanlash(false); window.location.reload(); }} />
      </React.Suspense> : (educationEditing || needsEducation(foydalanuvchi, tab)) && !foydalanuvchi?.is_admin ?
        <EducationSetup key={educationRoleChoice || "setup"} apiBase={API_BASE} token={token} user={foydalanuvchi} target={tab} initialRole={educationRoleChoice || (loginAccountRole(foydalanuvchi) ? "" : savedLoginRole())} onBack={() => { setEducationEditing(false); setEducationRoleChoice(""); setTab("home"); }} onComplete={(joined) => { setEducationEditing(false); setEducationRoleChoice(""); if (joined?.profile) { institutionJoined(joined); setMembershipNotice(""); } else { setMuassasalarYuklandi(false); setProfileReload((n) => n + 1); } }} /> : <>
      {mavjudMuassasalar.length > 0 && !foydalanuvchi?.is_admin && <div className={`samtm-muassasa-strip ${yonMenyuOchiq ? "" : "yon-yopiq"}`}>
        {mavjudMuassasalar.map((m, i) => { const meta = MUASSASA_TURI_RANG[m.turi]; const on = faolMuassasa && faolMuassasa.turi === m.turi && String(faolMuassasa.muassasa_id) === String(m.muassasa_id); return <div key={`${m.turi}-${m.muassasa_id}-${i}`} className={`samtm-muassasa-card ${on ? "on" : ""}`} style={{ "--m-rang": meta.rang, "--m-yengil": meta.yengil }}>
          <button type="button" className="samtm-muassasa-main" onClick={() => { if (korinishRoli === "oquvchi") { setTanlanganMuassasa(m); setTab("bilim"); kabutarniOch(false); } else muassasaniTanla(m); }} title={__kbUi(`${m.muassasa_nomi || meta.nom} — ${meta.nom} ta’lim maydoni`)}>
            <span className="samtm-muassasa-ikon">{__kbUi(meta.ikon)}</span>
            <span className="samtm-muassasa-matn"><b>{m.muassasa_nomi || m.display_name || meta.nom}</b><small>{__kbUi(meta.nom)}{m.lavozim ? __kbUi(` · ${m.lavozim}`) : __kbUi("")}{on ? __kbUi(" · siz shu yerdasiz") : __kbUi("")}</small></span>
          </button>
        </div>; })}
      </div>}
      <button type="button" className="samtm-yon-toggle" onClick={yonMenyuniAlmashtir} title={yonMenyuOchiq ? uiT("Yon menyuni yopish") : uiT("Yon menyuni ochish")}>{yonMenyuOchiq ? __kbUi("‹") : __kbUi("›")}</button>
      <div className={`premium-app-shell ${yonMenyuOchiq ? "" : "samtm-yon-yopiq"}`} style={{ "--role-accent": faolMuassasa ? MUASSASA_TURI_RANG[faolMuassasa.turi].rang : joriyRang }}>
        <main className="premium-app-main">
          <header className="premium-topbar">
            <div>
              <p>{uiT(tabMalumoti[1])}</p>
              <h1>{uiT(tabMalumoti[0])}</h1>
            </div>
            <div className="premium-top-actions">
              <span className="premium-role-pill">{korinishRoli === "admin" ? uiT("Administrator") : korinishRoli === "oqituvchi" ? uiT("O‘qituvchi") : korinishRoli === "ota-ona" ? uiT("Ota-ona") : educationRole(foydalanuvchi) === "talaba" ? uiT("Talaba") : educationRole(foydalanuvchi) === "bogcha" ? uiT("Bog‘cha bolasi") : uiT("O‘quvchi")}</span>
              {!readOnly && onProfiles && (isFamilyProfileUser(foydalanuvchi)
                ? <button type="button" className="kb-family-switch" onClick={() => onProfiles(foydalanuvchi)} aria-label={uiT("Profilni almashtirish")} title={uiT("Profilni almashtirish")}><Users size={16} /><span>{(foydalanuvchi?.full_name || "").split(/\s+/)[0]}</span></button>
                : <button type="button" onClick={() => onProfiles(foydalanuvchi)} aria-label={uiT("Profillar")} title={uiT("Profillar: bitta akkauntda 10 tagacha")}><Users size={18} /></button>)}
              {oqituvchiMi && oqituvchiFanlari.length > 0 && <button type="button" className="kb-family-switch" onClick={() => setFanTanlash(true)} title={oqituvchiFanlari.join(", ")} aria-label={uiT("Fanlarim")}><BookOpen size={16} /><span>{uiT("Fanlarim")}</span></button>}
              <button onClick={() => tabTanlandi("xabar")} aria-label={uiT("Xabarlar")}><Bell size={18} /></button>
              <button onClick={() => tabTanlandi("profil")} className="premium-top-avatar"
                aria-label={uiT("Profil va sozlamalar")} title={uiT("Profil va sozlamalar")}>
                {__kbUi((foydalanuvchi?.full_name || "TA").trim().split(/\s+/).slice(0, 2).map((q) => q[0]).join("").toUpperCase())}
              </button>
            </div>
          </header>
          <div className="premium-page-stage">
      <SectionErrorBoundary resetKey={`${korinishRoli}:${tab}`}>
      {tab === "home" && <EducationHome onOpen={tabTanlandi}/>}

      {presentationsOpened && !readOnly && <div hidden={tab !== "taqdimotlar"}>
        <React.Suspense fallback={<p className="p-6" role="status">{__kbUi("Taqdimot ustaxonasi yuklanmoqda…")}</p>}>
          <PresentationStudio key={token} apiBase={API_BASE} token={token} user={foydalanuvchi}
            active={tab === "taqdimotlar" && !kabutarOchiq}
            onClose={() => setTab(korinishRoli === "oqituvchi" ? "oqituvchi" : korinishRoli === "ota-ona" ? "farzand" : korinishRoli === "admin" ? "admin" : "bilim")} />
        </React.Suspense>
      </div>}
      {coursesOpened && <div style={{ display: tab === "kurslar" ? "block" : "none" }}>
        {readOnly ? <p className="p-6" role="status">{__kbUi("Kurslarni shaxsiy hisobingizdan oching. Ko‘rish rejimida pulli darslar va o‘zgarishlar yopiq.")}</p> :
          <React.Suspense fallback={<p className="p-6" role="status">{__kbUi("Kurslar yuklanmoqda…")}</p>}>
            <CourseWorkspace key={token} apiBase={API_BASE} token={token} user={foydalanuvchi} active={tab === "kurslar" && !kabutarOchiq} initialCourseId={courseNavigation.courseId} initialMode={courseNavigation.mode} onClose={() => { setCoursesOpened(false); setTab(korinishRoli === "oqituvchi" ? "oqituvchi" : korinishRoli === "ota-ona" ? "farzand" : korinishRoli === "admin" ? "admin" : "bilim"); }} />
          </React.Suspense>}
      </div>}
      {korinishRoli === "admin" && tab === "admin" && <AdminTab token={token} oldindanTanlangan={shablonOldindanTanlangan} />}
      {korinishRoli === "admin" && tab === "admin_muassasalar" && <AdminMuassasalarTab token={token} />}
      {korinishRoli === "admin" && tab === "admin_testlar" && <AdminTestlarTab token={token} />}
      {korinishRoli === "admin" && tab === "admin_ovoz" && <AdminSpeechStudio apiBase={API_BASE} token={token} />}
      {korinishRoli === "admin" && tab === "admin_mavzular" && (
        <TopikMavzularTab token={token} onTestYarat={(topicCode, scopeId) => { setShablonOldindanTanlangan({scopeId,codes:[topicCode]}); setTab("admin"); }} />
      )}
      {korinishRoli === "admin" && tab === "admin_statistikalar" && (
        <><AudiencePanel apiBase={API_BASE} token={token} active={!kabutarOchiq} /><AdminStatisticsTab token={token} /></>
      )}
      {korinishRoli === "admin" && tab === "admin_moderatsiya" && <ModeratsiyaTab token={token} />}
      {korinishRoli === "admin" && tab === "admin_korinish" && lazyPanel(LazyOquvchiKorinishi, { apiBase: API_BASE, token, admin: foydalanuvchi, Tests: TestTab,
        jins: _ovozJinsiniTuzat(foydalanuvchi?.ovoz_jinsi || foydalanuvchi?.jins || "qiz") })}
      {korinishRoli === "oqituvchi" && tab === "oqituvchi" && (
        ishJoyiAniqlandi ? <OqituvchiTab onOpenCourses={openCourses}
          token={token}
          readOnly={readOnly}
          foydalanuvchi={foydalanuvchi}
          boshlanishKorinishi={oqituvchiBoshlanishKorinishi}
          birInstitutAvtoOchishRef={birInstitutAvtoOchishRef}
        /> : <div className="py-16 text-center"><Loader2 size={26} className="animate-spin mx-auto" style={{ color: "var(--ui-legacy-color-1b4b7a, #1B4B7A)" }} /><p className="text-sm mt-3" style={{ color: "var(--ui-legacy-color-8a8578, #8A8578)" }}>{__kbUi("Ish joyingiz aniqlanmoqda…")}</p></div>
      )}
      {korinishRoli === "oqituvchi" && tab === "kutubxonam" && <Kutubxonam apiBase={API_BASE} token={token} />}
      {korinishRoli === "oqituvchi" && tab === "ovoz" && <AdminSpeechStudio apiBase={API_BASE} token={token} basePath="/api/speech" title="Ovoz ⇄ Matn" />}
      {korinishRoli === "oqituvchi" && tab === "oqituvchi_analitika" && (
        <TeacherAnalyticsPanel
          token={token}
          initialWorkplace={birinchiMuassasa}
          onBack={() => { if (!kabinetTarixdanQayt()) setTab("oqituvchi"); }}
        />
      )}
      {korinishRoli === "ota-ona" && tab === "farzand" && <OtaOnaTab token={token} foydalanuvchi={foydalanuvchi} rang={joriyRang} />}
      {korinishRoli !== "admin" && korinishRoli !== "oqituvchi" && korinishRoli !== "ota-ona" && tab === "bilim" && (
        !muassasalarYuklandi ? <div className="py-12 text-center"><Loader2 size={24} className="animate-spin mx-auto" style={{ color: joriyRang }}/><p className="text-xs mt-2" style={{ color: "var(--ui-legacy-color-7a8794, #7A8794)" }}>{__kbUi("Ta’lim holati aniqlanmoqda…")}</p></div>
        : <>
          {mavjudMuassasalar.length > 0 && <MilitaryRoutine token={token} apiBase={API_BASE} readOnly />}
          {mavjudMuassasalar.length === 0 ? null : (foydalanuvchi?.talaba_mi || sinfTalabaMi(foydalanuvchi?.class)) ? (
            <TalabaHaftalikJadval token={token} apiBase={API_BASE} talabaProfili={foydalanuvchi?.talaba_profili} readOnly={readOnly} />
          ) : (
          <StudentScheduleWorkspace
            token={token}
            student={foydalanuvchi}
            onFindCourses={() => openCourses("catalog")}
            apiBase={API_BASE}
            readOnly={readOnly}
            onOpenTest={(topic) => {
              setTalimYoliTestNishoni({ ...topic, nonce: Date.now() });
              setTab("test");
            }}
          />
          )}
          {mavjudMuassasalar.length === 0 ? <TashkilotsizOquvchiBoshSahifa
            foydalanuvchi={foydalanuvchi}
            bilimData={bilimData}
            rang={joriyRang}
            onTest={() => setTab("test")}
            onProfil={() => setTab("profil")}
          />
        : <BilimMarkazi
            token={token}
            data={bilimData}
            bolaId={foydalanuvchi?.user_id}
            rang={joriyRang}
            onOpenTest={(topic) => {
              setTalimYoliTestNishoni({ ...topic, nonce: Date.now() });
              setTab("test");
            }}
            onOpenLesson={(topic) => {
              setTalimYoliDarsNishoni({ ...topic, nonce: Date.now() });
              setTab("ai_ustoz");
            }}
          />
          }
        </>
      )}
      {korinishRoli !== "admin" && korinishRoli !== "ota-ona" && tab === "mavzular" && (
        <LearnerTopics apiBase={API_BASE} token={token} user={foydalanuvchi}
          onEducationSetup={foydalanuvchi?.is_admin || foydalanuvchi?.talaba_profili ? undefined : () => setEducationEditing(true)}
          jins={_ovozJinsiniTuzat(foydalanuvchi?.ovoz_jinsi || foydalanuvchi?.jins || "qiz")}
          onOpenLesson={korinishRoli === "oqituvchi" ? null : (topic) => {
            setTalimYoliDarsNishoni({...topic,nonce:Date.now()});setTab("ai_ustoz");
          }}
          onOpenTest={(topic) => {
            setTalimYoliTestNishoni({...topic,nonce:Date.now()});setTab("test");
          }} />
      )}
      {korinishRoli !== "admin" && korinishRoli !== "oqituvchi" && korinishRoli !== "ota-ona" && tab === "institutim" && (
        <MeningInstitutim token={token} apiBase={API_BASE} onOpenProfile={() => setTab("profil")} />
      )}
      {korinishRoli !== "admin" && korinishRoli !== "oqituvchi" && korinishRoli !== "ota-ona" && tab === "ai_ustoz" && (
        <AiOquvchiUstozBolimi token={token} foydalanuvchi={foydalanuvchi} initialTarget={talimYoliDarsNishoni} onOpenTest={(topic) => { setTalimYoliTestNishoni({ ...topic, nonce: Date.now() }); setTab("test"); }} />
      )}
      {korinishRoli !== "admin" && korinishRoli !== "ota-ona" && tab === "test" && (
        <TestTab
          token={token}
          onEducationSetup={korinishRoli === "oquvchi" && !foydalanuvchi?.talaba_profili && !foydalanuvchi?.maktab_id ? () => setEducationEditing(true) : undefined}
          sinf={korinishRoli === "oqituvchi" ? null : foydalanuvchi?.class}
          foydalanuvchi={foydalanuvchi}
          rang={joriyRang}
          oyinProfil={oyinProfil}
          onOyinProfilYangilandi={setOyinProfil}
          onTestFaollik={setTestDavomida}
          initialTarget={talimYoliTestNishoni}
          onBattle={readOnly ? undefined : (createFrom) => { setBellashuv({ kod: "", createFrom, nonce: Date.now() }); setTab("bellashuv"); }}
        />
      )}
      {korinishRoli !== "ota-ona" && tab === "oyinlar" && (
        <OyinlarMarkazi kid={korinishRoli !== "oqituvchi" && _kbAccountRole(foydalanuvchi) === "bogcha"} admin={Boolean(foydalanuvchi?.is_admin)} onOpen={(key) => {
          if (key === "bellashuv") setBellashuv({ kod: "", createFrom: null, nonce: Date.now() });
          if (key === "shashka") setShashka({ kod: "", nonce: Date.now() });
          if (key === "shaxmat" || key === "shaxmat_maktab") setShaxmat({ kod: "", nonce: Date.now(), maktab: key === "shaxmat_maktab" });
          setTab(key === "shaxmat_maktab" ? "shaxmat" : key);
        }} />
      )}
      {korinishRoli !== "ota-ona" && (tab === "til_xonalari" || tab === "til_mashqi" || tab === "til_maktab") && (
        <React.Suspense fallback={<p className="p-6 text-center text-slate-500">⏳</p>}>
          <LazyTilTanlov tur={tab === "til_mashqi" ? "mashq" : tab === "til_maktab" ? "maktab" : "xonalar"} apiBase={API_BASE}
            sinf={foydalanuvchi?.class || foydalanuvchi?.sinf || foydalanuvchi?.learning_profile?.class || ""}
            grade={foydalanuvchi?.yosh_guruhi || foydalanuvchi?.learning_profile?.age_group || foydalanuvchi?.class || ""}
            cheklovsiz={Boolean(foydalanuvchi?.is_admin)} onClose={() => setTab("oyinlar")} />
        </React.Suspense>
      )}
      {korinishRoli !== "ota-ona" && tab === "shaxmat" && (
        <Shaxmat key={shaxmat.nonce} apiBase={API_BASE} token={token}
          kid={korinishRoli !== "oqituvchi" && _kbAccountRole(foydalanuvchi) === "bogcha"}
          initialCode={shaxmat.kod} startInSchool={Boolean(shaxmat.maktab)} onClose={() => { setShaxmat({ kod: "", nonce: Date.now() }); setTab("oyinlar"); }} />
      )}
      {korinishRoli !== "ota-ona" && tab === "shashka" && (
        <Shashka key={shashka.nonce} apiBase={API_BASE} token={token}
          kid={korinishRoli !== "oqituvchi" && _kbAccountRole(foydalanuvchi) === "bogcha"}
          initialCode={shashka.kod} onClose={() => { setShashka({ kod: "", nonce: Date.now() }); setTab("oyinlar"); }} />
      )}
      {korinishRoli !== "ota-ona" && tab === "chempionat" && (
        <Chempionat apiBase={API_BASE} token={token} onClose={() => setTab("oyinlar")} />
      )}
      {korinishRoli !== "ota-ona" && tab === "bellashuv" && (
        <Bellashuv key={bellashuv.nonce} apiBase={API_BASE} token={token}
          kid={korinishRoli !== "oqituvchi" && _kbAccountRole(foydalanuvchi) === "bogcha"}
          initialCode={bellashuv.kod} createFrom={bellashuv.createFrom}
          onClose={() => { setBellashuv({ kod: "", createFrom: null, nonce: Date.now() }); setTab("oyinlar"); }}
          onPickTopic={() => setTab("test")} />
      )}

      {tab === "profil" && (
        <ProfilTab token={token} foydalanuvchi={foydalanuvchi} onYangilandi={setFoydalanuvchi} onInstitutionJoined={institutionJoined}
          adminKorinish={adminKorinish} onKorinishOzgar={korinishOzgardi} rang={joriyRang} onRolAlmashtir={rolniAlmashtir}
          onOquvchiKorinishi={foydalanuvchi?.is_admin ? () => { setAdminKorinish("admin"); setTab("admin_korinish"); } : undefined} />
      )}
      </SectionErrorBoundary>
          </div>
        </main>
      <PastkiMenyu faol={tab === "oqituvchi" && muassasaBandi && oqituvchiBoshlanishKorinishi?.korinish === muassasaBandi.korinish ? "oqituvchi_muassasa" : OYIN_TABLARI.has(tab) ? "oyinlar" : tab}
        onTanlash={tabTanlandi} rol={korinishRoli} rang={joriyRang} bloklangan={testDavomida}
        qoshimchaBand={muassasaBandi} foydalanuvchi={foydalanuvchi} taqdimotMavjud={presentationsAllowed && !readOnly} />
      </div>
      </>}
      </div>}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// ASOSIY — URL manziliga qarab qaysi ekranni ko'rsatishni hal qiladi
// ═══════════════════════════════════════════════════════════
let _boshlangichYolKeshi = null;

function _boshlangichYolniOl() {
  // React StrictMode initializer'ni development'da ikki marta chaqiradi.
  // Birinchi chaqiriqda URL tozalangandan keyin OAuth signalini yo'qotmaslik
  // uchun bir marta o'qilgan qiymatni modul doirasida saqlaymiz.
  if (_boshlangichYolKeshi) return _boshlangichYolKeshi;
  const p = window.location.pathname;
  const q = new URLSearchParams(window.location.search);
  const fragment = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  _boshlangichYolKeshi = {
    p,
    courseId: /^[1-9]\d{0,14}$/.test(q.get("kurs") || "") ? Number(q.get("kurs")) : null,
    courses: q.get("kurslar") === "1" || /^[1-9]\d{0,14}$/.test(q.get("kurs") || ""),
    // Eski query token kirish sifatida qabul qilinmaydi.
    email: q.get("email"),
    ism: q.get("ism"),
    oauthTicket: fragment.get("oauth_ticket"),
    oauthXato: fragment.get("oauth_xato"),
    // Admin “ko'rish rejimi”: #korish_token=... — faqat shu oyna uchun, saqlanmaydi.
    korishToken: fragment.get("korish_token"),
    korishIsm: fragment.get("korish_ism"),
    korishYozish: fragment.get("korish_yozish") === "1",
    // Botdagi «Test ishlash / Mavzu o'rganish» tugmasi: bir martalik chipta bilan kodsiz kirish.
    tgTicket: /^[A-Za-z0-9_-]{24,80}$/.test(fragment.get("tg_ticket") || "") ? fragment.get("tg_ticket") : null,
    tgGo: fragment.get("go") || "",
  };
  // REV82: #bellashuv=KOD — kirishdan (Telegram/Google) keyin ham yo'qolmasin.
  const battleKod = gameCodeFromHash(window.location.hash, "bellashuv");
  if (battleKod) { try { window.sessionStorage.setItem(BATTLE_CODE_KEY, battleKod); } catch { /* shu oynada qoladi */ } }
  const shashkaKod = gameCodeFromHash(window.location.hash, "shashka");
  if (shashkaKod) { try { window.sessionStorage.setItem(SHASHKA_CODE_KEY, shashkaKod); } catch { /* shu oynada qoladi */ } }
  const shaxmatKod = gameCodeFromHash(window.location.hash, "shaxmat");
  if (shaxmatKod) { try { window.sessionStorage.setItem(SHAXMAT_CODE_KEY, shaxmatKod); } catch { /* shu oynada qoladi */ } }
  // 60 soniyalik OAuth ticket fragmenti (va eski oqimdan qolishi mumkin
  // bo'lgan sezgir query'lar) birinchi render boshlanishidayoq tarixdan o'chadi.
  if (
    ["token", "email", "ism"].some((key) => q.has(key))
    || ["oauth_ticket", "oauth_xato", "korish_token", "korish_ism", "korish_yozish", "tg_ticket", "go", "bellashuv", "shashka", "shaxmat"].some((key) => fragment.has(key))
  ) {
    window.history.replaceState({}, document.title, p);
  }
  return _boshlangichYolKeshi;
}

const SAMTM_TOKEN_STORAGE_KEY = "samtm_login_token_v1";
const BOT_START_TAB_KEY = "kabutar:bot-start-tab:v1";
function gameCodeFromHash(hash, key) {
  const kod = normalizeCode(new URLSearchParams(String(hash || "").replace(/^#/, "")).get(key) || "");
  return kod.length === 6 ? kod : "";
}
// O'qish toza (StrictMode initializer'ni ikki marta chaqiradi); kalit ochilgandan keyin effektda o'chiriladi.
function peekGameCode(storageKey) {
  try { return normalizeCode(window.sessionStorage.getItem(storageKey) || ""); } catch { return ""; }
}
const BOT_TABS = { test: "test", organish: "mavzular", mavzular: "mavzular", natija: "home", home: "home" };
function botStartTab() {
  try { const tab = window.sessionStorage.getItem(BOT_START_TAB_KEY) || ""; window.sessionStorage.removeItem(BOT_START_TAB_KEY); return tab; } catch { return ""; }
}
const telegramTicketPromises = new Map();
function redeemTelegramTicket(ticket) {
  if (telegramTicketPromises.has(ticket)) return telegramTicketPromises.get(ticket);
  const pending = fetch(`${API_BASE}/auth/telegram/ticket/redeem`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ticket }),
  }).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data.token) throw new Error(typeof data.detail === "string" ? data.detail : "Botdagi havola eskirgan. Botda /kabinet bosib yangisini oling.");
    return data;
  });
  telegramTicketPromises.set(ticket, pending);
  return pending;
}
const COURSE_RETURN_KEY = "kabutar:course-return:v47";
function readCourseReturn() {
  try { const value = JSON.parse(window.sessionStorage.getItem(COURSE_RETURN_KEY) || "null");
    if (value && Number.isFinite(value.at) && Date.now() >= value.at && Date.now() - value.at < 600000 && (value.courseId === null || Number.isSafeInteger(value.courseId) && value.courseId > 0)) return value;
  } catch { /* public route only */ }
  return null;
}

function _saqlanganTokenniOl() {
  try {
    return window.localStorage.getItem(SAMTM_TOKEN_STORAGE_KEY);
  } catch {
    // Maxfiylik rejimi yoki yopiq WebView localStorage'ni bloklasa ham
    // ilova oddiy bir martalik kirish rejimida ishlashda davom etadi.
    return null;
  }
}

// StrictMode qayta effect boshlasa, bir martalik Google ticket qayta sarflanmaydi.
const googleExchangePromises = new Map();
function exchangeGoogleTicket(ticket) {
  if (googleExchangePromises.has(ticket)) return googleExchangePromises.get(ticket);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  const pending = fetch(`${API_BASE}/auth/google/exchange`, {
    method: "POST", credentials: "include", signal: controller.signal,
    headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ticket }),
  }).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Google tasdig‘i tugagan. Qayta kiring.");
    return data;
  }).catch((error) => {
    if (error.name === "AbortError") throw new Error("Google javobini kutish tugadi. Qayta kiring.");
    throw error;
  }).finally(() => clearTimeout(timer));
  googleExchangePromises.set(ticket, pending);
  return pending;
}

export default function App() {
  useKbInterfaceLocale();
  const [yol] = useState(_boshlangichYolniOl);
  const [courseReturn, setCourseReturn] = useState(() => yol.courses ? { courseId: yol.courseId, at: Date.now() } : readCourseReturn());
  const [publicCourses, setPublicCourses] = useState(Boolean(yol.courses));
  const courseLogin = (courseId) => {
    const intent = { courseId: Number.isSafeInteger(Number(courseId)) && Number(courseId) > 0 ? Number(courseId) : null, at: Date.now() };
    setCourseReturn(intent); setPublicCourses(false);
    try { window.sessionStorage.setItem(COURSE_RETURN_KEY, JSON.stringify(intent)); } catch { /* same-tab login works */ }
  };
  const korishRejimi = Boolean(yol.korishToken);
  const [token, setToken] = useState(() => yol.korishToken || _saqlanganTokenniOl());
  useEffect(()=>{setTranslationSession(token);return()=>setTranslationSession(null);},[token]);
  const [oauthYuklanmoqda, setOauthYuklanmoqda] = useState(Boolean(yol.oauthTicket));
  const [tgYuklanmoqda, setTgYuklanmoqda] = useState(Boolean(yol.tgTicket));
  const [oauthProfil, setOauthProfil] = useState(null);
  const [loginError, setLoginError] = useState(yol.oauthXato || "");
  const [notice, setNotice] = useState(yol.oauthXato || "");
  const [telegramLinkOpen, setTelegramLinkOpen] = useState(() => Boolean(readTelegramLinkIntent()));
  useEffect(() => {
    const arrived = () => {
      const fragment = new URLSearchParams(window.location.hash.replace(/^#/, ""));
      if (!fragment.has("telegram_phone") && !fragment.has("telegram_link")) return;
      captureTelegramArrival(window.location.hash);
      if (fragment.get("telegram_link") === "1") setTelegramLinkOpen(true);
    };
    window.addEventListener("hashchange", arrived);
    return () => window.removeEventListener("hashchange", arrived);
  }, []);
  const closeTelegramLink = () => { clearTelegramLinkIntent(); setTelegramLinkOpen(false); };
  const sessionEpoch = useRef(0);
  const persistSession = useCallback((value) => {
    if (korishRejimi) return;
    try { if (value) window.localStorage.setItem(SAMTM_TOKEN_STORAGE_KEY, value); else window.localStorage.removeItem(SAMTM_TOKEN_STORAGE_KEY); } catch { /* current tab still works */ }
  }, [korishRejimi]);
  const [familyOpen, setFamilyOpen] = useState(false);   // REV104: «Kim o‘rganadi?» oynasi
  const sessiyaniTozala = useCallback((expiredToken) => {
    if (!korishRejimi && expiredToken && _saqlanganTokenniOl() && _saqlanganTokenniOl() !== expiredToken) return;
    const family = korishRejimi ? null : readFamily();
    if (family && expiredToken && family.profileToken === expiredToken && family.ownerToken !== expiredToken) {
      // Profil sessiyasi tugadi — asosiy akkauntga qaytib, profil tanlash oynasini ochamiz.
      writeFamily({ ...family, profileToken: "" });
      sessionEpoch.current += 1; persistSession(family.ownerToken); setToken(family.ownerToken); setFamilyOpen(true);
      return;
    }
    if (family && expiredToken && family.ownerToken === expiredToken) clearFamily();
    sessionEpoch.current += 1; persistSession(null); setToken(null);
    if (!korishRejimi) dropSavedToken(expiredToken);
    setLoginError("Sessiyangiz yakunlandi. Pastdagi ro‘yxatdan akkauntingizni bosib qayta kiring.");
  }, [korishRejimi, persistSession]);
  const kirildi = useCallback((nextToken) => {
    try { const switchedNotice = window.sessionStorage.getItem("kabutar:switched-notice"); if (switchedNotice) { window.sessionStorage.removeItem("kabutar:switched-notice"); setNotice(switchedNotice); } } catch { /* ixtiyoriy */ }
    sessionEpoch.current += 1; persistSession(nextToken);
    setLoginError(""); setOauthProfil(null); setToken(nextToken);
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
    try { window.sessionStorage.removeItem(COURSE_RETURN_KEY); } catch { /* optional continuation */ }
  }, [persistSession]);
  const chiqish = useCallback(async (allDevices = false) => {
    const startedEpoch = sessionEpoch.current;
    // REV104: profildan chiqish = profil sessiyasini yopib, «Kim o‘rganadi?» oynasiga qaytish.
    if (!korishRejimi && isProfileSession(token)) {
      const family = readFamily();
      try { await workspaceRequest(API_BASE, "/auth/logout", token, { method: "POST", body: { all_devices: false } }); }
      catch (error) { if (error.status !== 401) throw error; }
      writeFamily({ ...family, profileToken: "" });
      sessionEpoch.current += 1; persistSession(family.ownerToken); setToken(family.ownerToken); setFamilyOpen(true);
      return;
    }
    // REV94: Telegram/Gmail'siz «tez» akkaunt shu qurilmadan chiqilganda o'chirilmaydi — ro'yxatdan qaytib kiriladi.
    const keepQuick = !allDevices && !korishRejimi && keepsQuickSession(token);
    if (token && !keepQuick) {
      try { await workspaceRequest(API_BASE, "/auth/logout", token, { method: "POST", body: { all_devices: allDevices } }); }
      catch (error) { if (error.status !== 401) throw error; }
    }
    if (sessionEpoch.current !== startedEpoch || (_saqlanganTokenniOl() && _saqlanganTokenniOl() !== token)) return;
    try { window.sessionStorage.removeItem("kabutar_google_link_intent"); } catch { /* blocked storage */ }
    clearTelegramLinkIntent(); setTelegramLinkOpen(false);
    if (!korishRejimi && !keepQuick) dropSavedToken(token);
    if (!korishRejimi) { const family = readFamily(); if (family && family.ownerToken === token) clearFamily(); }
    sessionEpoch.current += 1; persistSession(null);
    setOauthProfil(null); setNotice(""); setLoginError(""); setToken(null);
  }, [token, persistSession]);

  // REV104: profillar — ega tokeni bilan ochiladi; profil ichidan ham (almashtirish uchun).
  const profillarniOch = useCallback(() => {
    if (korishRejimi || !token) return;
    const family = readFamily();
    if (!(family && family.profileToken === token)) writeFamily({ ownerToken: token, profileToken: "" });
    setFamilyOpen(true);
  }, [korishRejimi, token]);
  const profilYopilsin = async (family) => {
    if (family?.profileToken && family.profileToken !== family.ownerToken) {
      try { await workspaceRequest(API_BASE, "/auth/logout", family.profileToken, { method: "POST", body: { all_devices: false } }); } catch { /* sessiya baribir tugaydi */ }
    }
  };
  const profilgaKir = async (profileToken) => {
    const family = readFamily();
    if (!family) return;
    if (family.profileToken) await profilYopilsin(family);   // oldingi profil sessiyasi yopiladi
    writeFamily({ ...family, profileToken });
    setFamilyOpen(false);
    kirildi(profileToken);
  };
  const egagaQayt = async () => {
    const family = readFamily();
    setFamilyOpen(false);
    if (!family || family.ownerToken === token) return;
    await profilYopilsin(family);
    writeFamily({ ...family, profileToken: "" });
    kirildi(family.ownerToken);
  };
  const egaChiqsin = async () => {
    const family = readFamily();
    setFamilyOpen(false);
    if (family && family.profileToken && family.profileToken === token) {
      await profilYopilsin(family);
      try { await workspaceRequest(API_BASE, "/auth/logout", family.ownerToken, { method: "POST", body: { all_devices: false } }); } catch { /* eskirgan bo'lsa ham chiqamiz */ }
      dropSavedToken(family.ownerToken); clearFamily();
      sessionEpoch.current += 1; persistSession(null); setNotice(""); setLoginError(""); setToken(null);
      return;
    }
    await chiqish(false);
  };
  const familyFromProfile = isProfileSession(token);

  useEffect(() => { initializeSamtmPwa(); }, []);
  useEffect(() => {
    if (korishRejimi) return;
    const changed = (event) => {
      if (event.storageArea === window.localStorage && (event.key === SAMTM_TOKEN_STORAGE_KEY || event.key === null)) {
        sessionEpoch.current += 1;
        setToken(event.key === null ? null : event.newValue);
        setOauthProfil(null);
      }
    };
    window.addEventListener("storage", changed);
    return () => window.removeEventListener("storage", changed);
  }, [korishRejimi]);

  useEffect(() => {
    if (!yol.tgTicket) return undefined;
    let cancelled = false;
    redeemTelegramTicket(yol.tgTicket).then((data) => {
      if (cancelled) return;
      const tab = BOT_TABS[yol.tgGo];
      if (tab) { try { window.sessionStorage.setItem(BOT_START_TAB_KEY, tab); } catch { /* bosh sahifa ochiladi */ } }
      kirildi(data.token);
    }).catch((error) => { if (!cancelled) { setLoginError(error.message); setNotice(error.message); } })
      .finally(() => { if (!cancelled) setTgYuklanmoqda(false); });
    return () => { cancelled = true; };
  }, [yol.tgTicket, yol.tgGo, kirildi]);

  useEffect(() => {
    if (!yol.oauthTicket) return;
    let cancelled = false;
    const startedEpoch = sessionEpoch.current;
    let linkIntent = null;
    try { linkIntent = JSON.parse(window.sessionStorage.getItem("kabutar_google_link_intent") || "null"); } catch { /* the initiating browser state is required below */ }
    exchangeGoogleTicket(yol.oauthTicket).then(async (data) => {
      if (cancelled || sessionEpoch.current !== startedEpoch) return;
      if (data.intent === "link") {
        const currentToken = _saqlanganTokenniOl();
        if (!currentToken || !linkIntent || linkIntent.session !== currentToken || Date.now() - Number(linkIntent.createdAt) > 600000 || !Number.isFinite(Number(linkIntent.createdAt))) throw new Error("Kirish sessiyasi o‘zgargan yoki ulash muddati tugagan. Profil sozlamalaridan Google ulashni qayta boshlang.");
        if (!data.oauth_grant || !data.email) throw new Error("Google hisobini ulash tasdig‘i olinmadi. Profil sozlamalaridan qayta boshlang.");
        const linked = await workspaceRequest(API_BASE, "/auth/google/link", currentToken, { method: "POST", body: { email: data.email, oauth_grant: data.oauth_grant } });
        if (!cancelled && sessionEpoch.current === startedEpoch && _saqlanganTokenniOl() === currentToken) {
          if (linked?.switched && linked?.token) { kirildi(linked.token); setNotice("Bu Gmail eski akkauntingizga ulangan edi — o‘sha akkauntga o‘tdingiz. Testlaringiz va natijalaringiz joyida."); }
          else setNotice("Google hisobi akkauntingizga ulandi.");
        }
      } else if (data.holat === "kirdi" && data.token) {
        if (data.intent === "telegram") setTelegramLinkOpen(true);
        kirildi(data.token);
      } else if (data.holat === "ulash" && data.email && data.oauth_grant) {
        if (data.intent === "telegram") setTelegramLinkOpen(true);
        setOauthProfil({ email: data.email, ism: data.ism || "", oauthGrant: data.oauth_grant });
      } else throw new Error("Google kirish javobi noto‘g‘ri. Qayta urinib ko‘ring.");
    }).catch((error) => {
      if (!cancelled) { setLoginError(error.message); if (_saqlanganTokenniOl()) setNotice(error.message); }
    }).finally(() => {
      if (!cancelled) {
        setOauthYuklanmoqda(false);
        try { window.sessionStorage.removeItem("kabutar_google_link_intent"); } catch { /* blocked storage */ }
      }
    });
    return () => { cancelled = true; };
  }, [yol.oauthTicket, kirildi]);

  if (tgYuklanmoqda) return <Qobiq><div className="py-10 text-center" role="status"><Loader2 size={26} className="animate-spin mx-auto mb-3" /><p>{__kbUi("Telegram orqali kirilmoqda…")}</p></div></Qobiq>;
  if (oauthYuklanmoqda) return <Qobiq><div className="py-10 text-center" role="status"><Loader2 size={26} className="animate-spin mx-auto mb-3" /><p>{__kbUi("Google tasdig‘i tekshirilmoqda…")}</p></div></Qobiq>;
  if (oauthProfil) return <KabutarRegistration {...oauthProfil} apiBase={API_BASE} onAuthenticated={kirildi} onCancel={() => { setOauthProfil(null); setLoginError(""); }} />;
  if (token && korishRejimi) return <div style={{ paddingTop: 42 }} ref={(el) => { if (el) document.documentElement.style.setProperty("--samtm-top-offset", "42px"); }}>
    <div className="fixed top-0 left-0 right-0 z-[9999] flex items-center justify-between gap-3 px-4 text-xs font-black text-white" style={{ height: 42, background: yol.korishYozish ? "#206647" : "#9c332b" }}>
      <span>{yol.korishYozish ? __kbUi("SINOV REJIMI: amallar haqiqiy bajariladi.") : __kbUi("ADMIN KO‘RISH REJIMI: o‘zgartirishlar bloklangan.")} {yol.korishIsm || __kbUi("")}</span>
      <button type="button" onClick={() => window.location.replace("/")}><InterfaceText text={__kbUi("Yopish")}/></button>
    </div>
    <Kabinet key={token} token={token} onSessionExpired={sessiyaniTozala} readOnly />
  </div>;
  if (token) return <>{notice && <div className="kb-app-notice" role="status"><span>{__kbUi(notice)}</span><button aria-label={__kbUi("Xabarni yopish")} onClick={() => setNotice("")}>×</button></div>}{telegramLinkOpen && <AccountSecurity apiBase={API_BASE} token={token} onToken={kirildi} onLogout={chiqish} onClose={closeTelegramLink} initialTelegramOpen/>}<Kabinet key={token} token={token} initialCourses={Boolean(courseReturn)} initialCourseId={courseReturn?.courseId} onSessionExpired={sessiyaniTozala} onLogout={chiqish} onToken={kirildi} onProfiles={profillarniOch} />{familyOpen && readFamily() && <React.Suspense fallback={null}><FamilyProfiles apiBase={API_BASE} ownerToken={readFamily().ownerToken} closable={familyFromProfile || readFamily().ownerToken === token} onEnter={profilgaKir} onOwner={egagaQayt} onLogout={egaChiqsin} onClose={() => setFamilyOpen(false)} /></React.Suspense>}</>;
  if (publicCourses) return <React.Suspense fallback={<p className="p-6" role="status">{__kbUi("Kurslar yuklanmoqda…")}</p>}><CourseWorkspace apiBase={API_BASE} token={null} user={null} initialCourseId={courseReturn?.courseId ?? yol.courseId} onLogin={courseLogin} onClose={() => { setPublicCourses(false); setCourseReturn(null); }} /></React.Suspense>;
  return <KabutarLogin apiBase={API_BASE} onAuthenticated={kirildi} initialError={loginError} onCourses={() => setPublicCourses(true)} />;
}
