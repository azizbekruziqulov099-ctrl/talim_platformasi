"""Private, paginated discussions built from the existing reply links.

No message contents are copied into another table. Both ancestor and descendant
walks are constrained to the already authorized conversation, detect cycles and
stop at 32 levels. PostgreSQL timeouts bound a very large legacy discussion; a
timeout produces a retryable error, never an unbounded application traversal.
"""
from contextlib import contextmanager
from threading import Lock

from fastapi import HTTPException


MAX_DEPTH = 32
MAX_PAGE = 50
QUERY_TIMEOUT = "2500ms"
META_COLUMNS = "id,guruh_id,yuboruvchi_user_id,qabul_qiluvchi_user_id,javob_xabar_id,ochirilgan"


def conversation_sql(alias, row):
    """Only internal aliases are used; all identifiers remain bound values."""
    if row.get("guruh_id"):
        return f"{alias}.guruh_id=%s", [int(row["guruh_id"])]
    sender = int(row.get("yuboruvchi_user_id") or 0)
    recipient = int(row.get("qabul_qiluvchi_user_id") or 0)
    if not sender or not recipient:
        raise HTTPException(404, "Suhbat topilmadi")
    return (
        f"{alias}.guruh_id IS NULL AND (({alias}.yuboruvchi_user_id=%s AND {alias}.qabul_qiluvchi_user_id=%s) "
        f"OR ({alias}.yuboruvchi_user_id=%s AND {alias}.qabul_qiluvchi_user_id=%s))",
        [sender, recipient, recipient, sender],
    )


def resolve_root(cur, row):
    """Resolve a validated message, including a tombstoned original post.

    A broken/cross-conversation parent is an error instead of silently creating
    an unrelated post. The common root case costs no additional query.
    """
    if not row.get("javob_xabar_id"):
        return int(row["id"])
    seed_scope, seed_args = conversation_sql("m", row)
    parent_scope, parent_args = conversation_sql("p", row)
    cur.execute(f"""
        WITH RECURSIVE ancestors AS (
          SELECT m.id,m.javob_xabar_id,ARRAY[m.id] AS trail,0 AS depth
          FROM chat_xabarlari m WHERE m.id=%s AND ({seed_scope})
          UNION ALL
          SELECT p.id,p.javob_xabar_id,a.trail || p.id,a.depth+1
          FROM chat_xabarlari p JOIN ancestors a ON p.id=a.javob_xabar_id
          WHERE ({parent_scope}) AND a.depth < %s AND NOT (p.id=ANY(a.trail))
        )
        SELECT id,javob_xabar_id,depth,trail FROM ancestors ORDER BY depth DESC LIMIT 1
    """, [int(row["id"]), *seed_args, *parent_args, MAX_DEPTH])
    root = cur.fetchone()
    if not root or root.get("javob_xabar_id"):
        raise HTTPException(409, "Bu eski muhokamaning javob bog‘lanishi noto‘g‘ri. Asosiy xabarni tanlang.")
    return int(root["id"])


def normalise_group_reply(cur, row):
    """Future group comments always attach to their original discussion post."""
    if row.get("guruh_id") and row.get("javob_xabar_id"):
        # This setting is transaction-local and cannot leak into the pool.
        try:
            cur.execute("SELECT set_config('statement_timeout',%s,true)", (QUERY_TIMEOUT,))
            return resolve_root(cur, row)
        except Exception as exc:
            if getattr(exc, "pgcode", None) in {"57014", "55P03"}:
                raise HTTPException(503, "Muhokama hozir band. Xabaringizni birozdan keyin yuboring.") from None
            raise
    return int(row["id"])


def _message(row, user_id):
    item = dict(row)
    item.pop("thread_reply_count", None)
    item.pop("thread_truncated", None)
    item["meniki"] = int(item["yuboruvchi_user_id"]) == int(user_id)
    item["reply_count"] = int(item.get("reply_count") or 0)
    item["reaksiyalar"] = []
    if item.get("ochirilgan"):
        item.update(matn=None, fayl_turi=None, fayl_nomi=None, fayl_hajmi_kb=None,
                    javob_xabar_id=None, javob_matn_qisqa=None, javob_fayl_turi=None,
                    javob_yuboruvchi_ismi=None)
    return item


class ThreadService:
    def __init__(self, platform):
        self.platform = platform
        self._ready = False
        self._lock = Lock()

    @contextmanager
    def database(self):
        conn = self.platform._db()
        cur = None
        try:
            cur = conn.cursor()
            yield cur
        finally:
            if cur is not None:
                cur.close()
            conn.close()

    def migrate(self):
        if self._ready:
            return
        with self._lock:
            if self._ready:
                return
            conn = self.platform._db()
            cur = None
            try:
                cur = conn.cursor()
                cur.execute("SELECT pg_advisory_xact_lock(46091011)")
                self.platform._chat_jadvallari(cur)
                cur.execute("""CREATE INDEX IF NOT EXISTS chat_xabarlari_thread_parent_id_idx
                    ON chat_xabarlari(javob_xabar_id,id) WHERE javob_xabar_id IS NOT NULL""")
                conn.commit()
                self._ready = True
            except Exception:
                conn.rollback()
                raise
            finally:
                if cur is not None:
                    cur.close()
                conn.close()

    def read(self, token, message_id, limit=MAX_PAGE, after_id=0):
        if type(message_id) is not int or not 0 < message_id <= 2147483647:
            raise HTTPException(422, "Xabar raqami noto‘g‘ri")
        if type(limit) is not int or not 1 <= limit <= MAX_PAGE:
            raise HTTPException(422, "Sahifa hajmi 1 dan 50 gacha bo‘lishi kerak")
        if type(after_id) is not int or not 0 <= after_id <= 2147483647:
            raise HTTPException(422, "Sahifa raqami noto‘g‘ri")
        # Existing authentication rejects revoked sessions and admin preview.
        user_id = self.platform._chat_actor(token)
        try:
            with self.database() as cur:
                cur.execute("SELECT set_config('statement_timeout',%s,true)", (QUERY_TIMEOUT,))
                cur.execute("SELECT set_config('lock_timeout','750ms',true)")
                cur.execute(f"SELECT {META_COLUMNS} FROM chat_xabarlari WHERE id=%s", (message_id,))
                seed = cur.fetchone()
                if not seed:
                    raise HTTPException(404, "Xabar topilmadi")
                # A deleted original post may still have valid comments. Check
                # its conversation normally, then return only a tombstone.
                if seed.get("guruh_id"):
                    self.platform._chat_suhbat_ruxsat(cur, user_id, guruh_id=int(seed["guruh_id"]))
                else:
                    sender = int(seed["yuboruvchi_user_id"])
                    recipient = int(seed.get("qabul_qiluvchi_user_id") or 0)
                    if int(user_id) not in (sender, recipient):
                        raise HTTPException(403, "Bu xabar sizga tegishli emas")
                    peer = recipient if int(user_id) == sender else sender
                    self.platform._chat_suhbat_ruxsat(cur, user_id, boshqa_user_id=peer)
                root_id = resolve_root(cur, seed)
                rows = self._page(cur, seed, root_id, limit, after_id)
                if not rows:
                    raise HTTPException(404, "Asosiy xabar topilmadi")
                total = int(rows[0].get("thread_reply_count") or 0)
                truncated = bool(rows[0].get("thread_truncated"))
                root = _message(rows[0], user_id)
                root["reply_count"] = total
                comments = [_message(row, user_id) for row in rows[1:limit + 1]]
                selected = [root, *comments]
                self._reactions(cur, selected, user_id)
                for item in selected:
                    item["thread_root_id"] = root_id
                return {"root": root, "xabarlar": comments, "reply_count": total,
                        "has_more": len(rows) > limit + 1,
                        "last_id": comments[-1]["id"] if comments else after_id,
                        "truncated": truncated}
        except Exception as exc:
            if getattr(exc, "pgcode", None) in {"57014", "55P03"}:
                raise HTTPException(503, "Muhokama hozir band. Birozdan keyin qayta oching.") from None
            raise

    def _page(self, cur, seed, root_id, limit, after_id):
        seed_scope, seed_args = conversation_sql("m", seed)
        child_scope, child_args = conversation_sql("c", seed)
        overflow_scope, overflow_args = conversation_sql("overflow_child", seed)
        count_scope, count_args = conversation_sql("child", seed)
        quote_scope, quote_args = conversation_sql("jx", seed)
        cur.execute(f"""
          WITH RECURSIVE discussion AS (
            SELECT m.id,m.ochirilgan,ARRAY[m.id] AS trail,0 AS depth
            FROM chat_xabarlari m WHERE m.id=%s AND ({seed_scope})
            UNION ALL
            SELECT c.id,c.ochirilgan,d.trail || c.id,d.depth+1
            FROM chat_xabarlari c JOIN discussion d ON c.javob_xabar_id=d.id
            WHERE ({child_scope}) AND d.depth < %s AND NOT (c.id=ANY(d.trail))
          ), summary AS (
            SELECT COUNT(*) FILTER (WHERE id<>%s AND NOT COALESCE(ochirilgan,FALSE)) AS reply_count,
              EXISTS(SELECT 1 FROM discussion boundary
                JOIN chat_xabarlari overflow_child ON overflow_child.javob_xabar_id=boundary.id
                WHERE boundary.depth=%s AND ({overflow_scope})
                  AND NOT (overflow_child.id=ANY(boundary.trail))) AS truncated
            FROM discussion
          ), page AS (
            SELECT id FROM discussion WHERE id<>%s AND id>%s ORDER BY id ASC LIMIT %s
          ), wanted AS (
            SELECT %s::integer AS id UNION ALL SELECT id FROM page
          )
          SELECT cx.id,cx.yuboruvchi_user_id,u.full_name AS yuboruvchi_ismi,cx.matn,cx.fayl_turi,
            cx.fayl_nomi,cx.fayl_hajmi_kb,cx.yaratilgan_at,cx.tahrirlangan,cx.ochirilgan,
            cx.javob_xabar_id,ju.full_name AS javob_yuboruvchi_ismi,
            LEFT(jx.matn,100) AS javob_matn_qisqa,jx.fayl_turi AS javob_fayl_turi,
            (SELECT COUNT(*) FROM chat_xabarlari child WHERE child.javob_xabar_id=cx.id
              AND NOT COALESCE(child.ochirilgan,FALSE) AND ({count_scope})) AS reply_count,
            summary.reply_count AS thread_reply_count,summary.truncated AS thread_truncated
          FROM wanted JOIN chat_xabarlari cx ON cx.id=wanted.id
          LEFT JOIN users u ON u.user_id=cx.yuboruvchi_user_id
          LEFT JOIN chat_xabarlari jx ON jx.id=cx.javob_xabar_id
            AND NOT COALESCE(jx.ochirilgan,FALSE) AND ({quote_scope})
          LEFT JOIN users ju ON ju.user_id=jx.yuboruvchi_user_id
          CROSS JOIN summary
          ORDER BY (cx.id=%s) DESC,cx.id ASC
        """, [root_id, *seed_args, *child_args, MAX_DEPTH, root_id, MAX_DEPTH, *overflow_args,
              root_id, after_id, limit + 1, root_id, *count_args, *quote_args, root_id])
        return cur.fetchall()

    def _reactions(self, cur, messages, user_id):
        # Bounded to the selected page; never fetch file bytes for a preview.
        self.platform._reaksiya_jadvali(cur)
        visible = {int(item["id"]): item for item in messages if not item.get("ochirilgan")}
        if not visible:
            return
        cur.execute("SELECT xabar_id,user_id,emoji FROM chat_reaksiyalar WHERE xabar_id=ANY(%s)", (list(visible),))
        counts = {}
        for row in cur.fetchall():
            key = (int(row["xabar_id"]), row["emoji"])
            value = counts.setdefault(key, {"emoji": row["emoji"], "soni": 0, "meniki": False})
            value["soni"] += 1
            value["meniki"] = value["meniki"] or int(row["user_id"]) == int(user_id)
        for (message_id, _), value in counts.items():
            visible[message_id]["reaksiyalar"].append(value)


def register_threads(app, platform):
    from fastapi import APIRouter, Query, Response
    router = APIRouter(prefix="/api/chat")
    service = ThreadService(platform)

    @router.get("/thread")
    def thread(response: Response, token: str, message_id: int = Query(..., ge=1, le=2147483647),
               limit: int = Query(MAX_PAGE, ge=1, le=MAX_PAGE),
               after_id: int = Query(0, ge=0, le=2147483647)):
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["Pragma"] = "no-cache"
        return service.read(token, message_id, limit, after_id)

    app.include_router(router)
    return service
