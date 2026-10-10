"""REV85: Shaxmat — to'liq qoidalar va 4 darajali bot. Sof Python, tashqi kutubxonasiz.

Pozitsiya FEN satrida saqlanadi. Qoidalar: rokirovka (shax ostida va urilgan katakdan o'tib bo'lmaydi),
o'tib urish (en passant), piyodaning aylanishi (farzin/ruh/fil/ot), shax, mat, pat, 50 yurish qoidasi,
uch marta takror va mat qilishga kuch yetmasligi (K–K, K+fil/ot–K, bir xil rangli fillar).
Yurish generatori perft sonlari bilan tekshirilgan (tests/test_shaxmat_rev85.py).

Bot: alfa-beta qidiruv + tinch holatgacha urishlarni hisoblash (quiescence), MVV-LVA tartiblash,
transpozitsiya jadvali va figura-katak jadvallari. Darajalar: 1 Oson · 2 O'rta · 3 Qiyin · 4 Usta.
"""
import random
import time

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
FILES = "abcdefgh"
VALUES = {"p": 100, "n": 320, "b": 330, "r": 500, "q": 900, "k": 0}
KNIGHT = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
KING = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
DIAG = ((1, 1), (1, -1), (-1, 1), (-1, -1))
ORTHO = ((1, 0), (-1, 0), (0, 1), (0, -1))
MAX_PLIES = 600

LEVELS = {
    1: {"nomi": "Oson", "emoji": "🐣"},
    2: {"nomi": "O'rta", "emoji": "🙂"},
    3: {"nomi": "Qiyin", "emoji": "😎"},
    4: {"nomi": "Usta", "emoji": "🧠"},
}


def sq_name(i):
    return f"{FILES[i % 8]}{i // 8 + 1}"


def sq_index(name):
    name = str(name or "").strip().lower()
    if len(name) != 2 or name[0] not in FILES or name[1] not in "12345678":
        raise ValueError(f"Noto'g'ri katak: {name}")
    return (int(name[1]) - 1) * 8 + FILES.index(name[0])


def color_of(p):
    return None if p == "." else ("w" if p.isupper() else "b")


def other(side):
    return "b" if side == "w" else "w"


# Figura-katak jadvallari (oq nuqtai nazaridan, a8..h8 birinchi qator — o'qish qulayligi uchun).
_PST_TEXT = {
    "p": """ 0  0  0  0  0  0  0  0
            50 50 50 50 50 50 50 50
            10 10 20 30 30 20 10 10
             5  5 10 25 25 10  5  5
             0  0  0 20 20  0  0  0
             5 -5-10  0  0-10 -5  5
             5 10 10-20-20 10 10  5
             0  0  0  0  0  0  0  0""",
    "n": """-50-40-30-30-30-30-40-50
            -40-20  0  0  0  0-20-40
            -30  0 10 15 15 10  0-30
            -30  5 15 20 20 15  5-30
            -30  0 15 20 20 15  0-30
            -30  5 10 15 15 10  5-30
            -40-20  0  5  5  0-20-40
            -50-40-30-30-30-30-40-50""",
    "b": """-20-10-10-10-10-10-10-20
            -10  0  0  0  0  0  0-10
            -10  0  5 10 10  5  0-10
            -10  5  5 10 10  5  5-10
            -10  0 10 10 10 10  0-10
            -10 10 10 10 10 10 10-10
            -10  5  0  0  0  0  5-10
            -20-10-10-10-10-10-10-20""",
    "r": """ 0  0  0  0  0  0  0  0
             5 10 10 10 10 10 10  5
            -5  0  0  0  0  0  0 -5
            -5  0  0  0  0  0  0 -5
            -5  0  0  0  0  0  0 -5
            -5  0  0  0  0  0  0 -5
            -5  0  0  0  0  0  0 -5
             0  0  0  5  5  0  0  0""",
    "q": """-20-10-10 -5 -5-10-10-20
            -10  0  0  0  0  0  0-10
            -10  0  5  5  5  5  0-10
             -5  0  5  5  5  5  0 -5
              0  0  5  5  5  5  0 -5
            -10  5  5  5  5  5  0-10
            -10  0  5  0  0  0  0-10
            -20-10-10 -5 -5-10-10-20""",
    "k": """-30-40-40-50-50-40-40-30
            -30-40-40-50-50-40-40-30
            -30-40-40-50-50-40-40-30
            -30-40-40-50-50-40-40-30
            -20-30-30-40-40-30-30-20
            -10-20-20-20-20-20-20-10
             20 20  0  0  0  0 20 20
             20 30 10  0  0 10 30 20""",
    "K": """-50-40-30-20-20-30-40-50
            -30-20-10  0  0-10-20-30
            -30-10 20 30 30 20-10-30
            -30-10 30 40 40 30-10-30
            -30-10 30 40 40 30-10-30
            -30-10 20 30 30 20-10-30
            -30-30  0  0  0  0-30-30
            -50-30-30-30-30-30-30-50""",
}


def _parse_pst(text):
    import re
    nums = [int(x) for x in re.findall(r"-?\d+", text)]
    assert len(nums) == 64
    table = [0] * 64
    for row in range(8):          # row 0 = 8-qator
        for f in range(8):
            table[(7 - row) * 8 + f] = nums[row * 8 + f]
    return table


PST = {k: _parse_pst(v) for k, v in _PST_TEXT.items()}


class Board:
    __slots__ = ("sq", "side", "castle", "ep", "half", "full", "kings")

    def __init__(self, fen=START_FEN):
        parts = fen.split()
        rows = parts[0].split("/")
        sq = ["."] * 64
        for r, row in enumerate(rows):
            f = 0
            for ch in row:
                if ch.isdigit():
                    f += int(ch)
                else:
                    sq[(7 - r) * 8 + f] = ch
                    f += 1
        self.sq = sq
        self.side = parts[1] if len(parts) > 1 else "w"
        self.castle = parts[2] if len(parts) > 2 and parts[2] != "-" else ""
        self.ep = sq_index(parts[3]) if len(parts) > 3 and parts[3] != "-" else -1
        self.half = int(parts[4]) if len(parts) > 4 else 0
        self.full = int(parts[5]) if len(parts) > 5 else 1
        self.kings = {"w": sq.index("K") if "K" in sq else -1, "b": sq.index("k") if "k" in sq else -1}

    def fen(self):
        rows = []
        for r in range(7, -1, -1):
            row, empty = "", 0
            for f in range(8):
                p = self.sq[r * 8 + f]
                if p == ".":
                    empty += 1
                else:
                    row += (str(empty) if empty else "") + p
                    empty = 0
            rows.append(row + (str(empty) if empty else ""))
        return f"{'/'.join(rows)} {self.side} {self.castle or '-'} {sq_name(self.ep) if self.ep >= 0 else '-'} {self.half} {self.full}"

    def key(self):
        """Takrorni aniqlash uchun kalit (soatlar hisobga olinmaydi; o'tib urish faqat mumkin bo'lsa)."""
        ep = "-"
        if self.ep >= 0 and any(m[1] == self.ep and self.sq[m[0]].lower() == "p" for m in self.legal()):
            ep = sq_name(self.ep)
        return f"{''.join(self.sq)} {self.side} {self.castle or '-'} {ep}"

    # ── hujum ──
    def attacked(self, s, by):
        sq = self.sq
        r, f = divmod(s, 8)
        pawn = "P" if by == "w" else "p"
        pr = r - 1 if by == "w" else r + 1
        if 0 <= pr < 8:
            for df in (-1, 1):
                if 0 <= f + df < 8 and sq[pr * 8 + f + df] == pawn:
                    return True
        knight = "N" if by == "w" else "n"
        for dr, df in KNIGHT:
            rr, ff = r + dr, f + df
            if 0 <= rr < 8 and 0 <= ff < 8 and sq[rr * 8 + ff] == knight:
                return True
        king = "K" if by == "w" else "k"
        for dr, df in KING:
            rr, ff = r + dr, f + df
            if 0 <= rr < 8 and 0 <= ff < 8 and sq[rr * 8 + ff] == king:
                return True
        bq = ("B", "Q") if by == "w" else ("b", "q")
        for dr, df in DIAG:
            rr, ff = r + dr, f + df
            while 0 <= rr < 8 and 0 <= ff < 8:
                p = sq[rr * 8 + ff]
                if p != ".":
                    if p in bq:
                        return True
                    break
                rr += dr
                ff += df
        rq = ("R", "Q") if by == "w" else ("r", "q")
        for dr, df in ORTHO:
            rr, ff = r + dr, f + df
            while 0 <= rr < 8 and 0 <= ff < 8:
                p = sq[rr * 8 + ff]
                if p != ".":
                    if p in rq:
                        return True
                    break
                rr += dr
                ff += df
        return False

    def in_check(self, side=None):
        side = side or self.side
        k = self.kings[side]
        return k >= 0 and self.attacked(k, other(side))

    # ── yurishlar ──
    def pseudo(self, captures_only=False):
        sq, side = self.sq, self.side
        out = []
        white = side == "w"
        for s in range(64):
            p = sq[s]
            if p == "." or (p.isupper() != white):
                continue
            t = p.lower()
            r, f = divmod(s, 8)
            if t == "p":
                d = 1 if white else -1
                last = 7 if white else 0
                start = 1 if white else 6
                r1 = r + d
                if 0 <= r1 < 8:
                    to = r1 * 8 + f
                    if not captures_only or r1 == last:
                        if sq[to] == ".":
                            if r1 == last:
                                out.extend((s, to, pr) for pr in "qrbn")
                            else:
                                out.append((s, to, ""))
                                if r == start and sq[to + 8 * d] == ".":
                                    out.append((s, to + 8 * d, ""))
                    for df in (-1, 1):
                        ff = f + df
                        if 0 <= ff < 8:
                            to = r1 * 8 + ff
                            q = sq[to]
                            if (q != "." and q.isupper() != white) or to == self.ep:
                                if r1 == last:
                                    out.extend((s, to, pr) for pr in "qrbn")
                                else:
                                    out.append((s, to, ""))
            elif t == "n" or t == "k":
                for dr, df in (KNIGHT if t == "n" else KING):
                    rr, ff = r + dr, f + df
                    if 0 <= rr < 8 and 0 <= ff < 8:
                        to = rr * 8 + ff
                        q = sq[to]
                        if q == ".":
                            if not captures_only:
                                out.append((s, to, ""))
                        elif q.isupper() != white:
                            out.append((s, to, ""))
                if t == "k" and not captures_only:
                    out.extend(self._castles())
            else:
                dirs = DIAG if t == "b" else ORTHO if t == "r" else DIAG + ORTHO
                for dr, df in dirs:
                    rr, ff = r + dr, f + df
                    while 0 <= rr < 8 and 0 <= ff < 8:
                        to = rr * 8 + ff
                        q = sq[to]
                        if q == ".":
                            if not captures_only:
                                out.append((s, to, ""))
                        else:
                            if q.isupper() != white:
                                out.append((s, to, ""))
                            break
                        rr += dr
                        ff += df
        return out

    def _castles(self):
        out = []
        sq, c = self.sq, self.castle
        if self.side == "w":
            if sq[4] != "K":
                return out
            enemy = "b"
            if "K" in c and sq[7] == "R" and sq[5] == sq[6] == "." and not any(self.attacked(x, enemy) for x in (4, 5, 6)):
                out.append((4, 6, ""))
            if "Q" in c and sq[0] == "R" and sq[1] == sq[2] == sq[3] == "." and not any(self.attacked(x, enemy) for x in (4, 3, 2)):
                out.append((4, 2, ""))
        else:
            if sq[60] != "k":
                return out
            enemy = "w"
            if "k" in c and sq[63] == "r" and sq[61] == sq[62] == "." and not any(self.attacked(x, enemy) for x in (60, 61, 62)):
                out.append((60, 62, ""))
            if "q" in c and sq[56] == "r" and sq[57] == sq[58] == sq[59] == "." and not any(self.attacked(x, enemy) for x in (60, 59, 58)):
                out.append((60, 58, ""))
        return out

    def make(self, m):
        frm, to, promo = m
        sq = self.sq
        p = sq[frm]
        cap = sq[to]
        t = p.lower()
        ep_cap = -1
        if t == "p" and to == self.ep and cap == ".":
            ep_cap = to - 8 if p == "P" else to + 8
            cap = sq[ep_cap]
            sq[ep_cap] = "."
        undo = (frm, to, promo, p, cap, self.castle, self.ep, self.half, self.full, ep_cap, dict(self.kings))
        sq[to] = (promo.upper() if p.isupper() else promo) if promo else p
        sq[frm] = "."
        if t == "k":
            self.kings[self.side] = to
            if abs(to - frm) == 2:   # rokirovka — ruh ham ko'chadi
                if to == frm + 2:
                    sq[frm + 1], sq[frm + 3] = sq[frm + 3], "."
                else:
                    sq[frm - 1], sq[frm - 4] = sq[frm - 4], "."
        # rokirovka huquqlari
        c = self.castle
        if c:
            for s, flags in ((4, "KQ"), (60, "kq"), (0, "Q"), (7, "K"), (56, "q"), (63, "k")):
                if frm == s or to == s:
                    for ch in flags:
                        c = c.replace(ch, "")
            self.castle = c
        self.ep = (frm + to) // 2 if t == "p" and abs(to - frm) == 16 else -1
        self.half = 0 if t == "p" or cap != "." else self.half + 1
        if self.side == "b":
            self.full += 1
        self.side = other(self.side)
        return undo

    def unmake(self, undo):
        frm, to, promo, p, cap, castle, ep, half, full, ep_cap, kings = undo
        sq = self.sq
        sq[frm] = p
        if ep_cap >= 0:
            sq[to] = "."
            sq[ep_cap] = cap
        else:
            sq[to] = cap
        if p.lower() == "k" and abs(to - frm) == 2:
            if to == frm + 2:
                sq[frm + 3], sq[frm + 1] = sq[frm + 1], "."
            else:
                sq[frm - 4], sq[frm - 1] = sq[frm - 1], "."
        self.castle, self.ep, self.half, self.full, self.kings = castle, ep, half, full, kings
        self.side = other(self.side)

    def legal(self, captures_only=False):
        out = []
        me = self.side
        for m in self.pseudo(captures_only):
            u = self.make(m)
            if not self.in_check(me):
                out.append(m)
            self.unmake(u)
        return out

    def copy(self):
        b = Board.__new__(Board)
        b.sq, b.side, b.castle, b.ep, b.half, b.full, b.kings = self.sq[:], self.side, self.castle, self.ep, self.half, self.full, dict(self.kings)
        return b

    # ── yozuv (SAN) ──
    def san(self, m):
        frm, to, promo = m
        p = self.sq[frm]
        t = p.lower()
        if t == "k" and abs(to - frm) == 2:
            text = "O-O" if to > frm else "O-O-O"
        else:
            capture = self.sq[to] != "." or (t == "p" and to == self.ep)
            if t == "p":
                text = (FILES[frm % 8] + "x" if capture else "") + sq_name(to)
                if promo:
                    text += "=" + promo.upper()
            else:
                text = t.upper()
                rivals = [o for o in self.legal() if o[1] == to and o[0] != frm and self.sq[o[0]] == p]
                if rivals:
                    if all(o[0] % 8 != frm % 8 for o in rivals):
                        text += FILES[frm % 8]
                    elif all(o[0] // 8 != frm // 8 for o in rivals):
                        text += str(frm // 8 + 1)
                    else:
                        text += sq_name(frm)
                text += ("x" if capture else "") + sq_name(to)
        u = self.make(m)
        if self.in_check():
            text += "#" if not self.legal() else "+"
        self.unmake(u)
        return text


# ── Tashqi (sessiya) interfeysi ─────────────────────────────────
def initial():
    return START_FEN


def side_to_move(fen):
    return fen.split()[1]


def legal_moves(fen, side=None):
    b = Board(fen)
    if side and b.side != side:
        return []
    return [{"from": m[0], "to": m[1], "promo": m[2]} for m in b.legal()]


def move_names(move):
    names = [sq_name(move["from"]), sq_name(move["to"])]
    return names + [move["promo"]] if move.get("promo") else names


def find_move(fen, side, path):
    try:
        frm, to = sq_index(path[0]), sq_index(path[1])
    except (ValueError, IndexError):
        return None
    promo = str(path[2]).lower()[:1] if len(path) > 2 else ""
    for m in legal_moves(fen, side):
        if m["from"] == frm and m["to"] == to and m["promo"] == promo:
            return m
    return None


def apply_move(fen, move):
    b = Board(fen)
    b.make((move["from"], move["to"], move.get("promo") or ""))
    return b.fen()


def san(fen, move):
    return Board(fen).san((move["from"], move["to"], move.get("promo") or ""))


def captured_square(fen, move):
    """Urilgan figura turgan katak (o'tib urishda — boshqa katak)."""
    b = Board(fen)
    if b.sq[move["to"]] != ".":
        return sq_name(move["to"])
    if b.sq[move["from"]].lower() == "p" and move["to"] == b.ep:
        return sq_name(move["to"] - 8 if b.side == "w" else move["to"] + 8)
    return None


def position_key(fen):
    return Board(fen).key()


def insufficient(b):
    pieces = [(p, i) for i, p in enumerate(b.sq) if p not in ".Kk"]
    if not pieces:
        return True
    if len(pieces) == 1 and pieces[0][0].lower() in "bn":
        return True
    if all(p.lower() == "b" for p, _ in pieces):
        colors = {(i // 8 + i % 8) % 2 for _, i in pieces}
        return len(colors) == 1
    return False


def outcome(fen, side=None, meta=None, plies=0):
    """(tugadimi, g'olib 'w'|'b'|None, sabab)."""
    b = Board(fen)
    if not b.legal():
        if b.in_check():
            return True, other(b.side), "mat"
        return True, None, "pat"
    if insufficient(b):
        return True, None, "kuch_yetmaydi"
    if b.half >= 100:
        return True, None, "ellik_yurish"
    if meta and (meta.get("rep") or {}).get(b.key(), 0) >= 3:
        return True, None, "takror"
    if plies >= MAX_PLIES:
        return True, None, "uzun_oyin"
    return False, None, ""


def material(fen):
    b = Board(fen)
    out = {"w": 0, "b": 0}
    for p in b.sq:
        if p != ".":
            out[color_of(p)] += VALUES[p.lower()]
    return out


def counts(fen):
    b = Board(fen)
    return {"w": sum(1 for p in b.sq if p.isupper()), "b": sum(1 for p in b.sq if p.islower())}


def status(fen):
    b = Board(fen)
    check = b.in_check()
    mat = material(fen)
    return {"shax": check, "shax_katak": sq_name(b.kings[b.side]) if check and b.kings[b.side] >= 0 else None,
            "ustunlik": (mat["w"] - mat["b"]) // 100}


# ── Baho va qidiruv ─────────────────────────────────────────────
def evaluate_board(b):
    """Navbatdagi tomon nuqtai nazaridan baho (santipeshka)."""
    sq = b.sq
    heavy = sum(VALUES[p.lower()] for p in sq if p not in ".pPkK")
    endgame = heavy <= 1300
    score = 0
    bishops = {"w": 0, "b": 0}
    for i, p in enumerate(sq):
        if p == ".":
            continue
        t = p.lower()
        white = p.isupper()
        idx = i if white else (7 - i // 8) * 8 + i % 8
        table = PST["K"] if t == "k" and endgame else PST[t]
        v = VALUES[t] + table[idx]
        if t == "b":
            bishops["w" if white else "b"] += 1
        score += v if white else -v
    score += 30 * ((bishops["w"] >= 2) - (bishops["b"] >= 2))
    return score if b.side == "w" else -score


def evaluate(fen, side):
    b = Board(fen)
    v = evaluate_board(b)
    return v if b.side == side else -v


MATE = 100000


class _Timeout(Exception):
    pass


class Searcher:
    def __init__(self, deadline, rng=None):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        self.rng = rng or random.Random()

    def order(self, b, moves, best=None):
        def key(m):
            if best is not None and m == best:
                return -10**6
            victim = b.sq[m[1]]
            s = 0
            if victim != ".":
                s -= 10 * VALUES[victim.lower()] - VALUES[b.sq[m[0]].lower()]
            if m[2]:
                s -= VALUES[m[2]]
            return s
        return sorted(moves, key=key)

    def tick(self):
        self.nodes += 1
        if self.nodes & 1023 == 0 and time.monotonic() > self.deadline:
            raise _Timeout()

    def quiesce(self, b, alpha, beta, depth=0):
        self.tick()
        stand = evaluate_board(b)
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand
        if depth > 6:
            return alpha
        for m in self.order(b, b.legal(captures_only=True)):
            u = b.make(m)
            v = -self.quiesce(b, -beta, -alpha, depth + 1)
            b.unmake(u)
            if v >= beta:
                return beta
            if v > alpha:
                alpha = v
        return alpha

    def search(self, b, depth, alpha, beta, ply):
        self.tick()
        key = (tuple(b.sq), b.side, b.castle, b.ep)
        hit = self.tt.get(key)
        best_move = hit[2] if hit else None
        if hit and hit[0] >= depth and ply > 0:
            return hit[1]
        moves = b.legal()
        if not moves:
            return -MATE + ply if b.in_check() else 0
        if b.half >= 100:
            return 0
        if depth <= 0:
            return self.quiesce(b, alpha, beta)
        best = -10**9
        for m in self.order(b, moves, best_move):
            u = b.make(m)
            v = -self.search(b, depth - 1, -beta, -alpha, ply + 1)
            b.unmake(u)
            if v > best:
                best, best_move = v, m
            if v > alpha:
                alpha = v
            if alpha >= beta:
                break
        self.tt[key] = (depth, best, best_move)
        return best

    def root(self, b, depth):
        """Har bir yurish bahosi: [(baho, yurish)]."""
        out = []
        for m in self.order(b, b.legal()):
            u = b.make(m)
            v = -self.search(b, depth - 1, -10**9, 10**9, 1)
            b.unmake(u)
            out.append((v, m))
        return out


def _pick(scored, tolerance, rng):
    top = max(s for s, _ in scored)
    good = [m for s, m in scored if s >= top - tolerance]
    return rng.choice(good)


def _repetition_adjust(b, scored, history):
    """Takror hisobi: yutayotgan bot bir xil holatni qaytarmaydi, yutqazayotgani esa durangni qidiradi."""
    if not history:
        return scored
    out = []
    for v, m in scored:
        u = b.make(m)
        seen = history.get(b.key(), 0)
        b.unmake(u)
        if seen >= 2:
            v = 0                      # uchinchi takror — durang
        elif seen >= 1 and v > 0:
            v = v // 3                 # takrorlashdan ko'ra oldinga intilish afzal
        out.append((v, m))
    return out


def choose_move(fen, side=None, level=2, rng=None, time_limit=1.0, history=None):
    rng = rng or random.Random()
    b = Board(fen)
    moves = b.legal()
    if not moves:
        return None
    level = max(1, min(4, int(level or 2)))

    def wrap(m):
        return {"from": m[0], "to": m[1], "promo": m[2]}
    if len(moves) == 1:
        return wrap(moves[0])
    if level == 1:
        s = Searcher(time.monotonic() + 5, rng)
        if rng.random() < 0.45:
            return wrap(rng.choice(moves))
        return wrap(_pick(s.root(b, 1), 120, rng))
    # Usta eng ko'p vaqt oladi (soatli o'yinda — qolgan vaqtiga qarab), Qiyin — 3 yurish chuqurlikda.
    budget = {2: 0.6, 3: 1.0, 4: min(2.5, max(1.5, time_limit * 2))}[level]
    max_depth = {2: 2, 3: 3, 4: 8}[level]
    tolerance = {2: 45, 3: 12, 4: 0}[level]
    s = Searcher(time.monotonic() + budget, rng)
    scored = s.root(b, 1)
    depth = 2
    while depth <= max_depth:
        try:
            scored = s.root(b, depth)
        except _Timeout:
            break
        if max(v for v, _ in scored) >= MATE - 100:
            break
        depth += 1
    return wrap(_pick(_repetition_adjust(b, scored, history), tolerance, rng))


def perft(b, depth):
    if depth == 0:
        return 1
    n = 0
    for m in b.legal():
        u = b.make(m)
        n += perft(b, depth - 1)
        b.unmake(u)
    return n
