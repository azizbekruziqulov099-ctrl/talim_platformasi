import React from "react";
import { uiText as __kbUi } from "../interface/interfaceRuntime.js";
import { useInterface as useKbInterfaceLocale } from "../interface/InterfacePreferences.jsx";
import "./boardGame.css";

const GAMES = [
  { key: "til_xonalari", emoji: "🏠", title: "Til o‘yin xonalari", text: "7 ta xona, 9 xil o‘yin: 10 tilda so‘z o‘rganish va gapirish (2–7 yosh)", color: "#0D7A77" },
  { key: "chempionat", emoji: "🏆", title: "Bolalar ligasi", text: "Jamoaviy chempionat: so‘z, harakat va bilim bellashuvi — kubok yut!", color: "#5b3fd6", bola: true },
  { key: "til_maktab", emoji: "📚", title: "Maktab: til o‘yinlari", text: "1–11 sinf: har sinfga bir yillik dastur — so‘z, gap, yozish va gapirish, 10 tilda", color: "#C2571B", katta: true },
  { key: "til_mashqi", emoji: "🗣️", title: "Gapirish va yozish mashqi", text: "Kattalar uchun, grammatikasiz: 12 ta hayotiy vaziyat — tinglab, takrorlab, yozib o‘rganing", color: "#1B4B7A", katta: true },
  { key: "bellashuv", emoji: "⚔️", title: "Bellashuv", text: "Do‘stlar bilan bir vaqtda test — kim birinchi to‘g‘ri topadi?", color: "#6c3ce0" },
  { key: "shashka", emoji: "⛀", title: "Shashka", text: "Bot bilan (4 daraja), onlayn raqib yoki do‘st bilan", color: "#b5541c" },
  { key: "shaxmat", emoji: "♞", title: "Shaxmat", text: "Bot bilan (4 daraja), maslahat, onlayn reyting yoki do‘st bilan", color: "#1d2733" },
  { key: "shaxmat_maktab", emoji: "🎓", title: "Shaxmat maktabi", text: "Noldan o‘rganish: figuralar, shax, mat, taktika — yulduzchalar bilan", color: "#2f7d3b" },
  { key: "mantiq", emoji: "🧩", title: "Rivojlantiruvchi o‘yinlar", text: "Xotira, mantiq, sanash — tez orada", color: "#2f9e54", soon: true },
];

/** REV83: O'yinlar markazi — bellashuv, shashka va keyingi o'yinlar bir joyda. */
export default function OyinlarMarkazi({ onOpen, kid = false, admin = false }) {
  useKbInterfaceLocale();
  return <section className="sh-root og-hub">
    <header className="sh-hero"><span className="og-hero-emoji" aria-hidden="true">🎮</span>
      <div><h2>{__kbUi("O‘yinlar")}</h2><p>{__kbUi("O‘ynab o‘rgan: aql, tezlik va mantiq o‘yinlari")}</p></div></header>
    <div className="og-grid">
      {GAMES.filter((g) => !(kid && g.katta) && !(g.bola && !kid && !admin)).map((g) => <button key={g.key} type="button" className={`og-card ${g.soon ? "is-soon" : ""}`} style={{ "--og": g.color }}
        disabled={g.soon} onClick={() => onOpen?.(g.key)}>
        <span className="og-emoji" aria-hidden="true">{g.emoji}</span>
        <b>{__kbUi(g.title)}</b>
        <small>{__kbUi(g.text)}</small>
        {g.soon && <em>{__kbUi("Tez orada")}</em>}
      </button>)}
    </div>
  </section>;
}
