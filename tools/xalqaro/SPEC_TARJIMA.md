# Translating the «Xalqaro baholash» content (uz → ru / en)

The content is our own original material: TIMSS/PISA-style parallel items, PISA-style units, and Kabu teacher lessons, written in Uzbek for students aged 9–16. It is shown on a school platform in the student's chosen language, so the translation must read as if it had been written in that language. Do not copy any official TIMSS/PISA wording — translate only our text.

## Files
- Input: `tr/src/<name>.json` — a list of `{"k": "s0001", "maydon": <field>, "tur": "matn"|"svg", "uz": <text>}`. The entries are in content order, so neighbouring entries give you context. The full source item is in `content/<name with __ → />.json` if you need more.
- Output: `tr/<lang>/<name>.json` — a single JSON object `{"s0001": "<translation>", ...}` with **every** key from the input and no others.
- Check: `python3 -I tools/tarjima.py check <lang> <name>` must print `OK`.
- Write large files in parts (for example `tr/<lang>/_parts/<name>.01.json` …), then merge them with a short Python script. Do not use machine translation (none is available). You translate everything yourself.

## Rules that the checker enforces
1. Keep every `$...$` formula exactly as it is (LaTeX unchanged). The only exception is **English**, where decimal commas become points: `5{,}87` → `5.87` and `0,5` → `0.5`, both in formulas and in text. In Russian, keep the decimal comma. In both languages, keep thousands separators as spaces (`1 248`).
2. Keep `[1]`, `[2]`, … markers in the same order and number. They synchronize the voice with the board lines.
3. Keep the same number of line breaks (`\n`) in each text.
4. No Uzbek words may remain in the translation.

## Field meanings
- `doska`: what is written on the board. Keep it short.
- `ovoz`: what the teacher says aloud. It must sound natural when read by text-to-speech. Uzbek writes numbers as words there; you may use digits or words.
- `savol`: the question. `javoblar`: the four options; keep their order.
- `xatolar` "0"–"3": why a student chose that wrong option.
- `javob`: accepted open answers separated by `|`. Translate the words and keep the numbers. You may add natural alternatives, for example `fotosintez` → `фотосинтез`.
- `kalit_sozlar`: keywords used to match school textbook topic titles. Use the standard textbook term in the target language.
- `tur: "svg"`: a label inside a picture. Keep it as short as the original (±30%), and use abbreviations for units (см, кг / cm, kg).
- `kunikma` / `usul` / `maslahat` / `strategiyalar` / `tipik_xatolar` / `umumiy` / `maqsad` / `sarlavha` / `nom` / `stimul` / `fan`: plain text — translate it.

## Style
- **Russian:** standard school textbook Russian, addressing the student as «вы». Use the standard terms of the Russian school curriculum (e.g. «десятичная дробь», «площадь», «агрегатное состояние», «уравнение»).
- **English:** clear international school English (as in TIMSS/PISA released materials), addressing the student as «you». Use US spelling.
- **Answer letters:** A, B, C, D stay Latin letters in both languages («Ответ: C», «Answer: C»).
- **Names and places:** people's names stay as they are (Sardor → Сардор / Sardor). For Uzbek places, use standard exonyms:
  - Russian: Ташкент, Самарканд, Бухара, Термез, Наманган, Андижан, Фергана, Нукус, Аральское море, Чимган.
  - English: Tashkent, Samarkand, Bukhara, Termez, Namangan, Andijan, Fergana, Nukus, Aral Sea, Chimgan.
- **Currency:** so‘m → сум / soum (sums).
- **Assessment terms:**

  | Uzbek | Russian | English |
  |---|---|---|
  | TIMSS darajalari: Ilg‘or / Yuqori / O‘rta / Past | Продвинутый / Высокий / Средний / Низкий | Advanced / High / Intermediate / Low |
  | PISA darajasi | уровень PISA | PISA level |
  | Tayanch daraja | базовый уровень | baseline level |
  | OECD o‘rtachasi | среднее по ОЭСР | OECD average |
  | Xalqaro o‘rtacha | международное среднее | international average |

- **Cultural content:** keep everything that is culturally Uzbek (plov, mahalla, bazaar, Navruz). Do not replace it.
