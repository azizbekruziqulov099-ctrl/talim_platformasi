"""REV85: Shaxmat — umumiy o'yin xizmatiga (modules/oyin_sessiya.py) ulangan qoidalar adapteri.

Bot bilan / onlayn (reytingli, soat bilan) / do'st bilan, durang taklifi, revansh, maslahat va
yurishni qaytarish — hammasi oyin_sessiya'da. Bu yerda faqat shaxmat qoidalari (shaxmat_engine).
"""
try:
    from . import shaxmat_engine as eng
    from .oyin_sessiya import create_game_router
except ImportError:  # pragma: no cover
    from modules import shaxmat_engine as eng
    from modules.oyin_sessiya import create_game_router

PIECE_NAMES = {"p": "piyoda", "n": "ot", "b": "fil", "r": "ruh", "q": "farzin", "k": "shoh"}


def explain(fen, move):
    """Maslahat yurishini bolaga tushunarli qilib aytish."""
    b = eng.Board(fen)
    piece = b.sq[move["from"]].lower()
    target = b.sq[move["to"]]
    to = eng.sq_name(move["to"])
    name = PIECE_NAMES[piece].capitalize()
    text = eng.san(fen, move)
    parts = []
    if piece == "k" and abs(move["to"] - move["from"]) == 2:
        parts.append("Rokirovka qiling — shoh xavfsiz joyga o'tadi, ruh o'yinga kiradi")
    else:
        parts.append(f"{name} {to} katakka")
    if target != "." or (piece == "p" and move["to"] == b.ep):
        victim = PIECE_NAMES[target.lower()] if target != "." else "piyoda"
        parts.append(f"raqibning {victim}{'sini' if victim.endswith('a') else 'ini'} uradi")
    if move.get("promo"):
        parts.append(f"piyoda {PIECE_NAMES[move['promo']]}ga aylanadi")
    if text.endswith("#"):
        parts.append("bu MAT! 🎉")
    elif text.endswith("+"):
        parts.append("shax beradi")
    elif len(parts) == 1 and piece in "nb" and b.full <= 10:
        parts.append("figurani o'yinga olib chiqing (rivojlantirish)")
    elif len(parts) == 1 and to in ("d4", "e4", "d5", "e5"):
        parts.append("markazni egallaydi")
    return ", ".join(parts) + "."


class ShaxmatAdapter:
    key = "shaxmat"
    prefix = "/api/shaxmat"

    @staticmethod
    def initial():
        return eng.initial()

    @staticmethod
    def legal(pos, side):
        return eng.legal_moves(pos, side)

    @staticmethod
    def find(pos, side, path):
        return eng.find_move(pos, side, path)

    @staticmethod
    def apply(pos, move):
        return eng.apply_move(pos, move)

    @staticmethod
    def names(move):
        return eng.move_names(move)

    @staticmethod
    def caps(move):
        return []

    @staticmethod
    def notation(pos, move):
        return eng.san(pos, move)

    @staticmethod
    def update_meta(pos, move, meta):
        after = eng.apply_move(pos, move)
        rep = dict(meta.get("rep") or {})
        if not rep:   # boshlang'ich holat ham hisobga olinadi
            rep[eng.position_key(pos)] = 1
        key = eng.position_key(after)
        rep[key] = rep.get(key, 0) + 1
        meta["rep"] = rep
        captured = eng.captured_square(pos, move)
        meta["urildi"] = captured
        return meta

    @staticmethod
    def outcome(pos, side, meta, plies):
        return eng.outcome(pos, side, meta, plies)

    @staticmethod
    def choose(pos, side, level, time_limit, meta=None):
        return eng.choose_move(pos, side, level, time_limit=time_limit, history=(meta or {}).get("rep"))

    @staticmethod
    def evaluate(pos, side):
        return eng.evaluate(pos, side)

    @staticmethod
    def counts(pos):
        return eng.counts(pos)

    @staticmethod
    def status(pos):
        return eng.status(pos)

    @staticmethod
    def explain(pos, move):
        return explain(pos, move)

    @staticmethod
    def illegal_message(pos, side):
        b = eng.Board(pos)
        return "Bu yurish mumkin emas" + (" — shohingiz shax ostida, avval uni himoya qiling!" if b.in_check() else "")


def create_router(platform):
    return create_game_router(platform, ShaxmatAdapter())
