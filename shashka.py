"""REV83/REV84: Shashka — umumiy o'yin xizmatiga (modules/oyin_sessiya.py) ulangan qoidalar adapteri.

Rejimlar, vaqt nazorati, Elo reyting, onlayn juftlash, durang taklifi, revansh — oyin_sessiya'da.
Bu yerda faqat shashka qoidalari (modules/shashka_engine.py) o'yin xizmatiga moslanadi.
"""
try:
    from . import shashka_engine as eng
    from .oyin_sessiya import create_game_router
except ImportError:  # pragma: no cover
    from modules import shashka_engine as eng
    from modules.oyin_sessiya import create_game_router


class ShashkaAdapter:
    key = "shashka"
    prefix = "/api/shashka"

    @staticmethod
    def initial():
        return eng.initial_board()

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
        return [eng.sq_name(c) for c in move["caps"]]

    @staticmethod
    def notation(pos, move):
        return eng.notation(move)

    @staticmethod
    def update_meta(pos, move, meta):
        quiet_king = pos[move["path"][0]].isupper() and not move["caps"]
        meta["tinch"] = int(meta.get("tinch") or 0) + 1 if quiet_king else 0
        return meta

    @staticmethod
    def outcome(pos, side, meta, plies):
        return eng.outcome(pos, side, int(meta.get("tinch") or 0), plies)

    @staticmethod
    def choose(pos, side, level, time_limit, meta=None):
        return eng.choose_move(pos, side, level, time_limit=time_limit)

    @staticmethod
    def evaluate(pos, side):
        return eng.evaluate(pos, side)

    @staticmethod
    def counts(pos):
        return eng.counts(pos)

    @staticmethod
    def hint(pos, side, legal):
        return {"urish_majburiy": any(m["caps"] for m in legal)}

    @staticmethod
    def illegal_message(pos, side):
        must = any(m["caps"] for m in eng.legal_moves(pos, side))
        return "Bu yurish qoidaga to'g'ri kelmaydi" + (" — urish majburiy!" if must else "")


def create_router(platform):
    return create_game_router(platform, ShashkaAdapter())
