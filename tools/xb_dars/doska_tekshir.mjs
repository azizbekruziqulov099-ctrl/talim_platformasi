// Doska buyruqlarini haqiqiy tahlilchilar bilan tekshiradi. Ishlatish: node tools/xb_dars/doska_tekshir.mjs fayl.txt ...
import fs from "node:fs";
const FR = "/home/claude/talim_platformasi_frontend/src/lesson/";
const M = await import(FR + "matDoska.js");
const P = await import(FR + "pedDoska.js");
const T = { ustun: M.ustunTahlil, bolish: M.bolishTahlil, qisqart: M.qisqartTahlil, son_oqi: M.sonOqiTahlil, grafik: M.grafikTahlil, chiz: M.chizTahlil,
  kasr_model: M.kasrModelTahlil, doira_kasr: M.doiraKasrTahlil, venn: M.vennTahlil, daraxt: M.daraxtTahlil, tarozi: M.taroziTahlil, ish: M.ishTahlil,
  ketma: M.ketmaTahlil, elak: M.elakTahlil, amal: M.amalTahlil, kod: P.kodTahlil, sxema: P.sxemaTahlil, zanjir: P.zanjirTahlil, jadval: P.jadvalTahlil };
let bad = 0, n = 0;
for (const f of process.argv.slice(2)) {
  let mavzu = "";
  for (const [i, l] of fs.readFileSync(f, "utf8").split("\n").entries()) {
    if (l.startsWith("## ")) mavzu = l.slice(3).trim();
    const m = l.match(/^DOSKA:\s*(.*)$/); if (!m) continue;
    const kw = m[1].match(/^\s*([A-Za-z_]+)\s*:/);
    const b = M.buyruq(m[1]);
    if (kw && kw[1] !== kw[1].toUpperCase() && !["yoz","qoida","belgila","davom"].includes(b.tur)) { bad++; console.log(`${f}:${i + 1} [${mavzu}] kichik harfli so'z buyruq bo'lib ketadi: ${m[1].slice(0, 40)}`); }
    const fn = T[b.tur]; if (!fn) continue;
    n++;
    let r = null; try { r = fn(b.arg); } catch (e) { r = null; }
    if (!r) { bad++; console.log(`${f}:${i + 1} [${mavzu}] ${b.tur.toUpperCase()}: ${b.arg}`); }
  }
}
console.log(`buyruqli qator: ${n}, yaroqsiz: ${bad}`);
process.exit(bad ? 1 : 0);
