"""MOCK chizmalari: rasmiy namunaviy testlardagidek oddiy qora chiziqli SVG (nuqtalar A, B, C…, o'lchamlar yozilgan). Parametrlardan kod chizadi."""
import math

_LAST = []


def FIG(svg):
    """Shablon ichida chaqiriladi: shu savolga chizma biriktiradi."""
    _LAST[:] = [svg]


def olish():
    r = _LAST[0] if _LAST else None
    _LAST.clear()
    return r


def _t(x, y, s, dx=0, dy=0, it=True, anchor="middle", size=13):
    st = "italic" if it else "normal"
    return f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" font-family="Times New Roman,serif" font-size="{size}" font-style="{st}" text-anchor="{anchor}" fill="#111">{s}</text>'


def _l(p, q, w=1.3, dash=False, col="#111"):
    d = ' stroke-dasharray="4 3"' if dash else ""
    return f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" stroke="{col}" stroke-width="{w}"{d}/>'


def _poly(pts, w=1.3, fill="none"):
    return f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="{fill}" stroke="#111" stroke-width="{w}" stroke-linejoin="round"/>'


def _dot(p, r=2):
    return f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{r}" fill="#111"/>'


def _svg(body, w=300, h=200):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="chizma" style="max-width:100%;height:auto">{body}</svg>'


def _mid(p, q, t=.5):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def _out(p, c, d=13):
    """p nuqta uchun yozuv joyi: markazdan tashqariga."""
    vx, vy = p[0] - c[0], p[1] - c[1]
    n = math.hypot(vx, vy) or 1
    return p[0] + vx / n * d, p[1] + vy / n * d + 4


def _sq(p, u, v, s=9):
    """To'g'ri burchak belgisi p da, u va v yo'nalishlarda."""
    nu, nv = math.hypot(*u) or 1, math.hypot(*v) or 1
    a = (p[0] + u[0] / nu * s, p[1] + u[1] / nu * s)
    b = (p[0] + (u[0] / nu + v[0] / nv) * s, p[1] + (u[1] / nu + v[1] / nv) * s)
    c = (p[0] + v[0] / nv * s, p[1] + v[1] / nv * s)
    return f'<polyline points="{a[0]:.1f},{a[1]:.1f} {b[0]:.1f},{b[1]:.1f} {c[0]:.1f},{c[1]:.1f}" fill="none" stroke="#111" stroke-width="1"/>'


def tri_pts(a, b, c, X0=40, Y0=170, M=210):
    """a=BC, b=CA, c=AB tomonli uchburchak: B chapda pastda, C o'ngda pastda, A tepada (masshtab bilan)."""
    s = M / max(a, b, c)
    B, C = (X0, Y0), (X0 + a * s, Y0)
    x = (c * c + a * a - b * b) / (2 * a)
    h = math.sqrt(max(c * c - x * x, 0.01))
    A = (X0 + x * s, Y0 - h * s)
    return A, B, C


def uchburchak(a, b, c, belgi=(None, None, None), nom=("A", "B", "C"), r_incircle=False, tomon_yoz=True):
    A, B, C = tri_pts(a, b, c)
    cen = ((A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3)
    body = _poly([A, B, C])
    for p, n in zip((A, B, C), nom):
        q = _out(p, cen)
        body += _t(q[0], q[1], n)
    if tomon_yoz:
        for (p, q), v in (((B, C), a), ((C, A), b), ((A, B), c)):
            m = _mid(p, q)
            o = _out(m, cen, 11)
            body += _t(o[0], o[1], f"{v:g}", it=False, size=12)
    return _svg(body), (A, B, C)


def tri_oddiy(a, b, c, nom=("A", "B", "C")):
    s, _ = uchburchak(a, b, c, nom=nom)
    return s


def tri_toqri(a, b, nom=("C", "A", "B"), balandlik=False, ichki=False, mediana=False, tomonlar=True, katet_belgi=None):
    """To'g'ri burchak nom[0] da; katetlar a (CB gorizontal) va b (CA vertikal)."""
    s = 150 / max(a, b)
    C = (50, 170)
    B = (50 + a * s, 170)
    A = (50, 170 - b * s)
    body = _poly([A, B, C]) + _sq(C, (1, 0), (0, -1))
    body += _t(C[0] - 12, C[1] + 4, nom[0]) + _t(A[0] - 12, A[1] - 2, nom[1]) + _t(B[0] + 12, B[1] + 4, nom[2])
    if tomonlar:
        body += _t((C[0] + B[0]) / 2, C[1] + 16, f"{a:g}", it=False, size=12) + _t(C[0] - 14, (C[1] + A[1]) / 2, f"{b:g}", it=False, size=12)
        body += _t((A[0] + B[0]) / 2 + 12, (A[1] + B[1]) / 2 - 4, f"{math.hypot(a, b):g}", it=False, size=12)
    if balandlik:
        dx, dy = B[0] - A[0], B[1] - A[1]
        t = ((C[0] - A[0]) * dx + (C[1] - A[1]) * dy) / (dx * dx + dy * dy)
        H = (A[0] + t * dx, A[1] + t * dy)
        body += _l(C, H, dash=True) + _dot(H) + _t(H[0] + 8, H[1] + 12, "H") + _t((C[0] + H[0]) / 2 - 8, (C[1] + H[1]) / 2 + 4, "h", size=12)
        body += _sq(H, (C[0] - H[0], C[1] - H[1]), (A[0] - H[0], A[1] - H[1]), 7)
    if ichki:
        p = (a * s + b * s - math.hypot(a * s, b * s)) / 2
        body += f'<circle cx="{C[0] + p:.1f}" cy="{C[1] - p:.1f}" r="{p:.1f}" fill="none" stroke="#111" stroke-width="1.2"/>' + _dot((C[0] + p, C[1] - p)) + _t(C[0] + p + 8, C[1] - p - 3, "O", size=12)
    if mediana:
        M = _mid(A, B)
        G = ((A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3)
        body += _l(C, M, dash=True) + _dot(M) + _t(M[0] + 10, M[1] - 3, "M") + _dot(G) + _t(G[0] + 4, G[1] - 7, "G", size=12)
    return _svg(body, 280, 200)


def trapetsiya(a, b, diagonal=False, orta=False, kichik="BC", nom=("A", "B", "C", "D")):
    """Asoslari a (AD, pastda) va b (BC, tepada)."""
    a, b = max(a, b), min(a, b)
    s = 220 / a
    h = 100
    off = (a - b) * s / 2 * .7
    A, D = (40, 160), (40 + a * s, 160)
    B, C = (40 + off, 160 - h), (40 + off + b * s, 160 - h)
    body = _poly([A, B, C, D])
    cen = ((A[0] + D[0]) / 2, 130)
    for p, n in zip((A, B, C, D), nom):
        q = _out(p, cen, 12)
        body += _t(q[0], q[1], n)
    body += _t((A[0] + D[0]) / 2, A[1] + 16, f"{a:g}", it=False, size=12) + _t((B[0] + C[0]) / 2, B[1] - 6, f"{b:g}", it=False, size=12)
    if diagonal:
        # diagonallar kesishuvi: BC:AD = b:a nisbatda
        t = a / (a + b)
        O = (A[0] + (C[0] - A[0]) * t, A[1] + (C[1] - A[1]) * t)
        body += _l(A, C) + _l(B, D) + _dot(O) + _t(O[0], O[1] - 7, "O", size=12)
        y = O[1]
        body += _l((A[0] + (B[0] - A[0]) * (A[1] - y) / h, y), (D[0] + (C[0] - D[0]) * (D[1] - y) / h, y), dash=True)
    if orta:
        y = (B[1] + A[1]) / 2
        M = (A[0] + (B[0] - A[0]) / 2, y)
        N = (D[0] + (C[0] - D[0]) / 2, y)
        body += _l(M, N, dash=True) + _t(M[0] - 10, M[1] + 4, "M", size=12) + _t(N[0] + 10, N[1] + 4, "N", size=12)
    return _svg(body, 300, 190)


def toqri_tortburchak(a, b, M=None, nom=("A", "B", "C", "D")):
    s = 200 / max(a, b)
    w, h = a * s, b * s
    h = min(h, 130)
    A, B, C, D = (50, 160), (50, 160 - h), (50 + w, 160 - h), (50 + w, 160)
    body = _poly([A, B, C, D]) + _l(A, C, dash=False)
    cen = (50 + w / 2, 160 - h / 2)
    for p, n in zip((A, B, C, D), nom):
        q = _out(p, cen, 12)
        body += _t(q[0], q[1], n)
    body += _t(50 + w / 2, 176, f"{a:g}", it=False, size=12) + _t(36, 160 - h / 2, f"{b:g}", it=False, size=12)
    if M:
        P = (A[0] + (C[0] - A[0]) / (M + 1), A[1] + (C[1] - A[1]) / (M + 1))
        body += _dot(P) + _t(P[0] + 4, P[1] + 14, "M", size=12) + _l(B, P) + _l(B, C)
    return _svg(body, 300, 195)


def kopburchak(n, belgi_R=None):
    cx, cy, R = 150, 100, 80
    pts = [(cx + R * math.sin(2 * math.pi * i / n), cy - R * math.cos(2 * math.pi * i / n)) for i in range(n)]
    body = _poly(pts)
    if belgi_R is not None:
        body += _dot((cx, cy)) + _l((cx, cy), pts[0], dash=True) + _t(cx + 8, cy - R / 2, f"R={belgi_R:g}", it=False, size=12, anchor="start") + _t(cx - 6, cy + 14, "O", size=12)
        body += f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#111" stroke-width=".8" stroke-dasharray="3 3"/>'
    return _svg(body, 300, 200)


def vektorlar(A, B, th, yig=False):
    o = (90, 150)
    ang = math.radians(th)
    la, lb = 130, 130 * B / A if B <= A else 130
    a = (o[0] + 130, o[1])
    la2 = 130 * min(1.0, B / A * 1.0) if True else 0
    b = (o[0] + math.cos(ang) * 100, o[1] - math.sin(ang) * 100)
    body = _l(o, a, 1.6) + _l(o, b, 1.6)
    body += f'<polygon points="{a[0]:.1f},{a[1]:.1f} {a[0] - 9:.1f},{a[1] - 4:.1f} {a[0] - 9:.1f},{a[1] + 4:.1f}" fill="#111"/>'
    ux, uy = math.cos(ang), -math.sin(ang)
    px, py = -uy, ux
    body += f'<polygon points="{b[0]:.1f},{b[1]:.1f} {b[0] - ux * 9 + px * 4:.1f},{b[1] - uy * 9 + py * 4:.1f} {b[0] - ux * 9 - px * 4:.1f},{b[1] - uy * 9 - py * 4:.1f}" fill="#111"/>'
    body += _t(a[0] + 4, a[1] + 16, f"a = {A:g}", it=False, size=12) + _t(b[0] + 6, b[1] - 4, f"b = {B:g}", it=False, size=12, anchor="start")
    r = 28
    body += f'<path d="M {o[0] + r} {o[1]} A {r} {r} 0 0 0 {o[0] + r * math.cos(ang):.1f} {o[1] - r * math.sin(ang):.1f}" fill="none" stroke="#111" stroke-width="1"/>'
    body += _t(o[0] + 40, o[1] - 10, f"{th}°", it=False, size=12) + _t(o[0] - 10, o[1] + 14, "O")
    if yig:
        c = (a[0] + b[0] - o[0], a[1] + b[1] - o[1])
        body += _l(a, c, dash=True) + _l(b, c, dash=True) + _l(o, c, 1.6)
    return _svg(body, 300, 190)


def prizma(a, b, h):
    """To'g'ri burchakli uchburchak (katetlar a, b) asosli to'g'ri prizma."""
    C, B, A = (50, 150), (50 + 130, 150), (50 + 52, 122)
    H = 80
    up = lambda p: (p[0], p[1] - H)
    C1, B1, A1 = up(C), up(B), up(A)
    body = _l(C, B) + _l(B, A) + _l(C, A, dash=True) + _l(C, C1) + _l(B, B1) + _l(A, A1, dash=True)
    body += _l(C1, B1) + _l(B1, A1) + _l(C1, A1)
    body += _t(C[0] - 10, C[1] + 6, "C") + _t(B[0] + 10, B[1] + 6, "B") + _t(A[0] + 2, A[1] + 15, "A") + _t(C1[0] - 10, C1[1], "C₁") + _t(B1[0] + 12, B1[1], "B₁") + _t(A1[0] + 4, A1[1] - 6, "A₁")
    body += _t((C[0] + B[0]) / 2, C[1] + 17, f"CB={a:g}", it=False, size=12) + _t(A[0] + 44, A[1] - 2 + 14, f"CA={b:g}", it=False, size=12, anchor="start") + _t(C[0] - 8, C[1] - H / 2, f"h={h:g}", it=False, size=12, anchor="end")
    return _svg(body, 300, 190)


def piramida(a, h):
    A, B, C, D = (60, 150), (170, 150), (215, 120), (105, 120)
    S = (140, 30)
    body = _l(A, B) + _l(B, C) + _l(A, D, dash=True) + _l(D, C, dash=True) + _l(S, A) + _l(S, B) + _l(S, C) + _l(S, D, dash=True)
    O = ((A[0] + C[0]) / 2, (A[1] + C[1]) / 2)
    body += _l(S, O, dash=True) + _dot(O) + _t(O[0] + 10, O[1] + 4, "O", size=12) + _t(S[0] + 10, 95, f"h={h:g}", it=False, size=12, anchor="start")
    body += _t(S[0], S[1] - 6, "S") + _t(A[0] - 10, A[1] + 4, "A") + _t(B[0] + 10, B[1] + 12, "B") + _t(C[0] + 10, C[1] + 4, "C") + _t(D[0] - 6, D[1] - 6, "D")
    body += _t((A[0] + B[0]) / 2, A[1] + 16, f"{a:g}", it=False, size=12)
    return _svg(body, 300, 190)


def _ellips(cx, cy, rx, ry, dash_back=True, w=1.3):
    return (f'<path d="M {cx - rx} {cy} A {rx} {ry} 0 0 0 {cx + rx} {cy}" fill="none" stroke="#111" stroke-width="{w}"/>'
            f'<path d="M {cx - rx} {cy} A {rx} {ry} 0 0 1 {cx + rx} {cy}" fill="none" stroke="#111" stroke-width="{w}" stroke-dasharray="4 3"/>')


def silindr(r, h):
    cx, rx, ry = 150, 60, 16
    top, bot = 50, 150
    body = f'<ellipse cx="{cx}" cy="{top}" rx="{rx}" ry="{ry}" fill="none" stroke="#111" stroke-width="1.3"/>' + _ellips(cx, bot, rx, ry) + _l((cx - rx, top), (cx - rx, bot)) + _l((cx + rx, top), (cx + rx, bot))
    body += _l((cx, bot), (cx + rx, bot), dash=True) + _t(cx + rx / 2, bot + 14, f"r={r:g}", it=False, size=12) + _t(cx + rx + 22, (top + bot) / 2, f"h={h:g}", it=False, size=12) + _dot((cx, bot))
    return _svg(body, 300, 190)


def konus(r, h):
    cx, rx, ry = 150, 60, 16
    top, bot = 30, 150
    body = _ellips(cx, bot, rx, ry) + _l((cx, top), (cx - rx, bot)) + _l((cx, top), (cx + rx, bot)) + _l((cx, top), (cx, bot), dash=True) + _dot((cx, bot))
    body += _l((cx, bot), (cx + rx, bot), dash=True) + _t(cx + rx / 2, bot + 14, f"r={r:g}", it=False, size=12) + _t(cx + 8, 90, f"h={h:g}", it=False, size=12, anchor="start")
    return _svg(body, 300, 190)


def yarim_shar(R):
    cx, cy, r = 150, 130, 80
    body = f'<path d="M {cx - r} {cy} A {r} {r} 0 0 1 {cx + r} {cy}" fill="none" stroke="#111" stroke-width="1.3"/>' + _ellips(cx, cy, r, 20) + _dot((cx, cy))
    body += _l((cx, cy), (cx + r, cy), dash=True) + _t(cx + r / 2, cy + 14, f"R={R:g}", it=False, size=12) + _t(cx - 8, cy + 14, "O", size=12)
    return _svg(body, 300, 190)


def aylana_tortburchak(AC, AB, AD):
    """AC — diametr; B va D aylanada, AC ning turli tomonlarida."""
    cx, cy, R = 150, 100, 80
    A, C = (cx - R, cy), (cx + R, cy)
    t1 = math.acos(AB / AC)   # AB tomon AC bilan burchagi
    B = (A[0] + AB * (R * 2 / AC) * math.cos(t1), A[1] - AB * (R * 2 / AC) * math.sin(t1))
    t2 = math.acos(AD / AC)
    D = (A[0] + AD * (R * 2 / AC) * math.cos(t2), A[1] + AD * (R * 2 / AC) * math.sin(t2))
    body = f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#111" stroke-width="1.2"/>' + _poly([A, B, C, D]) + _l(A, C, dash=True) + _dot((cx, cy)) + _t(cx, cy + 14, "O", size=11)
    body += _t(A[0] - 12, A[1] + 4, "A") + _t(C[0] + 12, C[1] + 4, "C") + _t(B[0], B[1] - 7, "B") + _t(D[0], D[1] + 15, "D")
    body += _t((A[0] + B[0]) / 2 - 14, (A[1] + B[1]) / 2 - 4, f"{AB:g}", it=False, size=12) + _t((A[0] + D[0]) / 2 - 14, (A[1] + D[1]) / 2 + 12, f"{AD:g}", it=False, size=12)
    return _svg(body, 300, 205)


def venn(n, a, b, ab):
    body = '<circle cx="115" cy="95" r="58" fill="none" stroke="#111" stroke-width="1.3"/><circle cx="185" cy="95" r="58" fill="none" stroke="#111" stroke-width="1.3"/>'
    body += f'<rect x="20" y="20" width="260" height="150" fill="none" stroke="#111" stroke-width="1"/>'
    body += _t(150, 98, f"{ab}", it=False, size=14) + _t(88, 98, f"{a - ab}", it=False, size=14) + _t(212, 98, f"{b - ab}", it=False, size=14)
    body += _t(80, 40, "M", size=13) + _t(220, 40, "F", size=13) + _t(262, 36, f"U = {n}", it=False, size=12, anchor="end")
    return _svg(body, 300, 185)
