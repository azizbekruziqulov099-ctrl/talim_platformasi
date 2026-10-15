// REV123: test variantining rasmi — bog'cha darsi va «O'ynaymiz» testida bir xil qoida.
import { pictureFor, stickerKeys } from "./kidStageRules.js";
import { stickerUrl } from "./stickers.js";
import { emojiRasm } from "./rasmHarakat.js";
import { RASMLAR } from "./xonalar/rasmlar.js";

/** Variant so'zi/emojisiga mos kitob rasmi (emoji+so'z → emoji), bo'lmasa so'zga mos ichki rasm, bo'lmasa null. */
export function kidOptionPic(o, rasmlar, mediaUrl, rasmSozlar = null) {
  const own = pictureFor(o?.picture, o?.word, rasmlar, rasmSozlar);
  if (own) return mediaUrl ? mediaUrl(own) : own;
  const chizilgan = emojiRasm(o?.picture, RASMLAR);   // REV144: emoji o'rniga rassom chizgan rasm
  if (chizilgan) return chizilgan.src;
  const key = stickerKeys(o?.word || "", 1)[0];
  return key ? stickerUrl(key) : null;
}

export { keycapNumber } from "./sanKarta.js";
