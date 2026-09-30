"""REV83: Shashka (rus shashkasi, 8×8) — qoidalar va 4 darajali bot. Sof Python, DB'siz.

Taxta: 64 belgili satr, indeks = qator*8 + ustun; 0-qator = «1» (oqlar tomoni), 0-ustun = «a».
Belgilar: '.' bo'sh, 'w' oq oddiy, 'W' oq damka, 'b' qora oddiy, 'B' qora damka. Faqat qora
kataklar (qator+ustun juft) ishlatiladi — a1 qora katak.

Qoidalar (O'zbekistonda o'ynaladigan rus shashkasi):
  • oddiy dona faqat oldinga bir katak yuradi, lekin orqaga ham urib oladi;
  • urish majburiy; boshlangan urish oxirigacha davom ettiriladi (istalgan urish yo'lini tanlash mumkin);
  • damka («uchar») diagonal bo'ylab istalgan masofaga yuradi va uradi;
  • urilgan donalar yurish tugagandagina olinadi va ikki marta sakrab o'tilmaydi (turk zarbasi yo'q);
  • urish paytida oxirgi qatorga yetgan dona o'sha zahoti damka bo'lib, damka sifatida urishni davom ettiradi;
  • damka urgandan keyin davom ettirish mumkin bo'lgan kataklar bo'lsa, faqat o'shalarga tushadi.
Yurish imkoni qolmagan tomon yutqazadi.
"""
import random
import time

DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
FILES = "abcdefgh"
KING_ONLY_DRAW = 30   # ketma-ket 30 yarim yurish faqat damkalar bilan, urishsiz — durang
MAX_PLIES = 240       # juda uzun o'yin — durang

LEVELS = {
    1: {"nomi": "Oson", "emoji": "🐣", "izoh": "Endi o'rganayotganlar uchun"},
    2: {"nomi": "O'rta", "emoji": "🙂", "izoh": "Biroz o'ylab o'ynaydi"},
    3: {"nomi": "Qiyin", "emoji": "😎", "izoh": "Tuzoqlarni ko'radi"},
    4: {"nomi": "Usta", "emoji": "🧠", "izoh": "Chuqur hisoblaydi"},
}


def side_of(ch):
    return "w" if ch in "wW" else "b" if ch in "bB" else None


def other(side):
    return "b" if side == "w" else "w"


def sq_name(i):
    return f"{FILES[i % 8]}{i // 8 + 1}"


def sq_index(name):
    name = str(name or "").strip().lower()
    if len(name) != 2 or name[0] not in FILES or name[1] not in "12345678":
        raise ValueError(f"Noto'g'ri katak: {name}")
    return (int(name[1]) - 1) * 8 + FILES.index(name[0])


def initial_board():
    cells = []
    for r in range(8):
        for c in range(8):
            dark = (r + c) % 2 == 0
            cells.append("w" if dark and r < 3 else "b" if dark and r > 4 else ".")
    return "".join(cells)


def _step(i, dr, dc):
    r, c = divmod(i, 8)
    r, c = r + dr, c + dc
    return r * 8 + c if 0 <= r < 8 and 0 <= c < 8 else None


def _promotes(i, side):
    return (side == "w" and i // 8 == 7) or (side == "b" and i // 8 == 0)


def _jumps(board, pos, side, king, captured):
    """pos'dan bitta urish: [(urilgan, [tushish kataklari])]."""
    out = []
    for dr, dc in DIRS:
        if king:
            j = _step(pos, dr, dc)
            while j is not None and board[j] == ".":
                j = _step(j, dr, dc)
            if j is None or side_of(board[j]) != other(side) or j in captured:
                continue
            lands = []
            k = _step(j, dr, dc)
            while k is not None and board[k] == ".":
                lands.append(k)
                k = _step(k, dr, dc)
            if lands:
                out.append((j, lands))
        else:
            j = _step(pos, dr, dc)
            if j is None or side_of(board[j]) != other(side) or j in captured:
                continue
            k = _step(j, dr, dc)
            if k is not None and board[k] == ".":
                out.append((j, [k]))
    return out


def _capture_sequences(board, pos, side, king, captured, path):
    results = []
    for victim, lands in _jumps(board, pos, side, king, captured):
        caps = captured + [victim]
        options = []
        for land in lands:
            now_king = king or _promotes(land, side)
            tails = _capture_sequences(board, land, side, now_king, caps, path + [land])
            options.append((land, tails))
        # Damka davom ettira oladigan katakka tushishi shart.
        continuing = [o for o in options if o[1]]
        for land, tails in (continuing or options):
            if tails:
                results.extend(tails)
            else:
                results.append({"path": path + [land], "caps": caps})
    return results


def legal_moves(board, side):
    """Barcha qonuniy yurishlar: [{"path": [indekslar], "caps": [urilgan indekslar]}]."""
    captures, simple = [], []
    for i, ch in enumerate(board):
        if side_of(ch) != side:
            continue
        king = ch.isupper()
        tmp = board[:i] + "." + board[i + 1:]   # yurayotgan dona o'z joyidan ko'tariladi
        captures.extend(_capture_sequences(tmp, i, side, king, [], [i]))
        if captures:
            continue
        forward = (1,) if side == "w" else (-1,)
        for dr, dc in DIRS:
            if not king and dr not in forward:
                continue
            j = _step(i, dr, dc)
            while j is not None and board[j] == ".":
                simple.append({"path": [i, j], "caps": []})
                if not king:
                    break
                j = _step(j, dr, dc)
    return captures if captures else simple


def apply_move(board, move):
    cells = list(board)
    start, end = move["path"][0], move["path"][-1]
    piece = cells[start]
    side = side_of(piece)
    cells[start] = "."
    for c in move["caps"]:
        cells[c] = "."
    became_king = piece.islower() and any(_promotes(p, side) for p in move["path"][1:])
    cells[end] = piece.upper() if became_king else piece
    return "".join(cells)


def move_names(move):
    return [sq_name(i) for i in move["path"]]


def notation(move):
    sep = ":" if move["caps"] else "-"
    return sep.join(move_names(move))


def find_move(board, side, names):
    """Mijoz yuborgan kataklar yo'li bo'yicha qonuniy yurishni topadi (yoki None)."""
    try:
        path = [sq_index(n) for n in names]
    except ValueError:
        return None
    for m in legal_moves(board, side):
        if m["path"] == path:
            return m
    return None


def counts(board):
    return {"w": sum(ch in "wW" for ch in board), "b": sum(ch in "bB" for ch in board),
            "W": board.count("W"), "B": board.count("B")}


def outcome(board, side_to_move, quiet_king_plies=0, plies=0):
    """(tugadimi, g'olib 'w'|'b'|None, sabab)."""
    if not legal_moves(board, side_to_move):
        return True, other(side_to_move), "yurish_yoq" if counts(board)[side_to_move] else "donalar_tugadi"
    if quiet_king_plies >= KING_ONLY_DRAW:
        return True, None, "damkalar_durang"
    if plies >= MAX_PLIES:
        return True, None, "uzun_oyin"
    return False, None, ""


# ── Bot ──────────────────────────────────────────────────────────
_CENTER = {sq_index(n) for n in ("c3", "e3", "d4", "f4", "c5", "e5", "d6", "f6")}


def evaluate(board, side):
    """side nuqtai nazaridan baho (musbat — side uchun yaxshi)."""
    score = 0
    for i, ch in enumerate(board):
        if ch == ".":
            continue
        s = side_of(ch)
        r = i // 8
        if ch.isupper():
            v = 300
        else:
            adv = r if s == "w" else 7 - r
            v = 100 + adv * 4
            if (s == "w" and r == 0) or (s == "b" and r == 7):
                v += 6   # orqa qatorni qo'riqlash (damka bo'lishiga yo'l qo'ymaydi)
        if i in _CENTER:
            v += 6
        score += v if s == side else -v
    return score


class _Timeout(Exception):
    pass


def _negamax(board, side, depth, alpha, beta, deadline, stats):
    stats[0] += 1
    if stats[0] & 255 == 0 and time.monotonic() > deadline:
        raise _Timeout()
    moves = legal_moves(board, side)
    if not moves:
        return -100000 - depth
    if depth <= 0 and not moves[0]["caps"]:
        return evaluate(board, side)
    if depth <= -6:   # urishlar zanjiri juda chuqur ketmasin
        return evaluate(board, side)
    best = -10**9
    moves.sort(key=lambda m: -len(m["caps"]))
    for m in moves:
        val = -_negamax(apply_move(board, m), other(side), depth - 1, -beta, -alpha, deadline, stats)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def score_moves(board, side, depth, deadline):
    stats = [0]
    out = []
    for m in legal_moves(board, side):
        out.append((-_negamax(apply_move(board, m), other(side), depth - 1, -10**9, 10**9, deadline, stats), m))
    return out


def choose_move(board, side, level=2, rng=None, time_limit=1.2):
    """Daraja: 1 oson, 2 o'rta, 3 qiyin, 4 usta."""
    rng = rng or random.Random()
    moves = legal_moves(board, side)
    if not moves:
        return None
    if len(moves) == 1:
        return moves[0]
    level = max(1, min(4, int(level or 2)))
    far = time.monotonic() + 30
    if level == 1:
        if rng.random() < 0.65:
            return rng.choice(moves)
        scored = score_moves(board, side, 1, far)
        return _pick(scored, 60, rng)
    if level == 2:
        return _pick(score_moves(board, side, 2, far), 35, rng)
    if level == 3:
        return _pick(score_moves(board, side, 4, far), 8, rng)
    deadline = time.monotonic() + time_limit
    best = score_moves(board, side, 2, far)
    depth = 3
    while depth <= 12:
        try:
            best = score_moves(board, side, depth, deadline)
        except _Timeout:
            break
        depth += 1
    return _pick(best, 0, rng)


def _pick(scored, tolerance, rng):
    top = max(s for s, _ in scored)
    good = [m for s, m in scored if s >= top - tolerance]
    return rng.choice(good)
