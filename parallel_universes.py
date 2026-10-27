"""V29 · 万物平行宇宙 — bilateral, opt-in bridges between real public exhibits.

Nothing here publishes a person's V27 private graph or V28 voyages. An invitation
is not a partnership until the recipient independently selects a public exhibit.
Source titles, tags and descriptions are resolved live; we never store snapshots.
"""
from __future__ import annotations

from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict, Field

MAX_OUTGOING_PENDING = 10
MAX_INCOMING_PENDING = 30
MAX_ACTIVE_BRIDGES = 20
SUGGESTION_SCAN = 300
SUGGESTION_LIMIT = 8

# Match the current public-source visibility policy of V26/V27, including the
# publishing state of a work's owning fantasy world, studio or sandbox project.
PUBLIC_SCOPE = """e.visibility='public'
 AND NOT EXISTS (
   SELECT 1 FROM fantasy_relics fr
   LEFT JOIN fantasy_worlds fw ON fw.id=fr.world_id
   WHERE fr.exhibit_id=e.id AND (fw.id IS NULL OR fw.visibility<>'public'))
 AND NOT EXISTS (
   SELECT 1 FROM creator_studio_projects sp
   WHERE sp.exhibit_id=e.id AND sp.visibility<>'public')
 AND NOT EXISTS (
   SELECT 1 FROM wonder_sandbox_projects sb
   WHERE sb.exhibit_id=e.id AND sb.visibility<>'public')"""


class InvitationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipient: str = Field(min_length=3, max_length=24)
    exhibit_id: int = Field(ge=1)


class AcceptIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exhibit_id: int = Field(ge=1)


def _tags(value: str):
    return {s.strip().casefold() for s in (value or "").replace("，", ",").split(",")
            if s.strip()}


def clue(source, candidate):
    """Transparent metadata overlap; never asserted as a proven relationship."""
    shared = sorted(_tags(source["tags"]) & _tags(candidate["tags"]))[:3]
    parts = []
    if shared:
        parts.append("共同标签：" + "、".join(shared))
    if source["category"] == candidate["category"] and source["category"] != "其他":
        parts.append("同属「" + source["category"] + "」类别")
    if source["domain"] == candidate["domain"] and source["domain"] != "其他":
        parts.append("同属「" + source["domain"] + "」领域")
    return ("；".join(parts), 5 * len(shared) +
            2 * (source["category"] == candidate["category"] and source["category"] != "其他") +
            (source["domain"] == candidate["domain"] and source["domain"] != "其他")) if parts else ("", 0)


def mount_parallel_universes(app, db, require_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS parallel_invitations(
          id INTEGER PRIMARY KEY,
          sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          sender_exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
          recipient_exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
          status TEXT NOT NULL CHECK(status IN
              ('pending','accepted','declined','cancelled','closed')),
          created_at TEXT NOT NULL,
          responded_at TEXT,
          CHECK(sender_id <> recipient_id)
        );
        CREATE INDEX IF NOT EXISTS ix_parallel_from_status
          ON parallel_invitations(sender_id,status,id DESC);
        CREATE INDEX IF NOT EXISTS ix_parallel_to_status
          ON parallel_invitations(recipient_id,status,id DESC);
        CREATE UNIQUE INDEX IF NOT EXISTS ux_parallel_pending_pair
          ON parallel_invitations(sender_id,recipient_id)
          WHERE status='pending';
        CREATE TABLE IF NOT EXISTS parallel_marks(
          invitation_id INTEGER NOT NULL REFERENCES parallel_invitations(id) ON DELETE CASCADE,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          marked_at TEXT NOT NULL,
          PRIMARY KEY(invitation_id,user_id)
        );
        """)

    def public(c, exhibit_id):
        if not exhibit_id:
            return None
        return c.execute("""SELECT e.id,e.user_id,e.title,e.category,e.domain,e.tags,
                                 u.username AS curator
                            FROM exhibits e JOIN users u ON u.id=e.user_id
                            WHERE e.id=? AND """ + PUBLIC_SCOPE, (exhibit_id,)).fetchone()

    def exhibit_card(row):
        return {"id": row["id"], "title": row["title"],
                "category": row["category"], "domain": row["domain"],
                "tags": sorted(_tags(row["tags"])), "curator": row["curator"]}

    def my_public(c, user_id):
        rows = c.execute("""SELECT e.id,e.user_id,e.title,e.category,e.domain,e.tags,
                                   u.username AS curator
                            FROM exhibits e JOIN users u ON u.id=e.user_id
                            WHERE e.user_id=? AND """ + PUBLIC_SCOPE +
                         " ORDER BY e.id DESC LIMIT 80", (user_id,)).fetchall()
        return [exhibit_card(r) for r in rows]

    def owned_invite(c, invite_id, user):
        row = c.execute("""SELECT pi.*, us.username AS sender, ur.username AS recipient
            FROM parallel_invitations pi
            JOIN users us ON us.id=pi.sender_id
            JOIN users ur ON ur.id=pi.recipient_id
            WHERE pi.id=? AND (pi.sender_id=? OR pi.recipient_id=?)""",
            (invite_id, user["id"], user["id"])).fetchone()
        if row is None:
            fail(404, "会合不存在或不属于你")
        return row

    def view(c, row, user):
        """Redact both endpoints if EITHER public source becomes unavailable."""
        result = {"id": row["id"], "status": row["status"],
                  "sender": row["sender"], "recipient": row["recipient"],
                  "is_sender": row["sender_id"] == user["id"],
                  "created_at": row["created_at"], "responded_at": row["responded_at"],
                  "available": False, "sender_exhibit": None,
                  "recipient_exhibit": None, "clue": None,
                  "progress": {"mine": False, "partner": False, "both": False}}
        a = public(c, row["sender_exhibit_id"])
        if a is None or a["user_id"] != row["sender_id"]:
            result["reason"] = "原始公开藏品已不可用，不能继续会合"
            return result
        if row["status"] == "pending":
            result["available"] = True
            result["sender_exhibit"] = exhibit_card(a)
            result["reason"] = "等待对方自愿选择自己的公开藏品"
            return result
        if row["status"] != "accepted":
            result["reason"] = "邀请已结束"
            return result
        b = public(c, row["recipient_exhibit_id"])
        if b is None or b["user_id"] != row["recipient_id"]:
            result["reason"] = "任一方撤回公开藏品，会合暂不可用"
            return result
        result["available"] = True
        result["sender_exhibit"] = exhibit_card(a)
        result["recipient_exhibit"] = exhibit_card(b)
        reason, _ = clue(a, b)
        result["clue"] = reason or None
        marks = {r["user_id"] for r in c.execute(
            "SELECT user_id FROM parallel_marks WHERE invitation_id=?",
            (row["id"],)).fetchall()}
        me = user["id"]
        other = row["recipient_id"] if me == row["sender_id"] else row["sender_id"]
        result["progress"] = {"mine": me in marks, "partner": other in marks,
                              "both": me in marks and other in marks}
        result["reason"] = "双方已同意；这是人为建立的跨馆连接，不代表事实因果"
        return result

    @app.get("/api/parallel")
    def overview(user=Depends(require_user)):
        with db() as c:
            incoming = c.execute("""SELECT pi.*,us.username AS sender,ur.username AS recipient
                FROM parallel_invitations pi JOIN users us ON us.id=pi.sender_id
                JOIN users ur ON ur.id=pi.recipient_id
                WHERE pi.recipient_id=? AND pi.status='pending'
                ORDER BY pi.id DESC LIMIT 50""", (user["id"],)).fetchall()
            outgoing = c.execute("""SELECT pi.*,us.username AS sender,ur.username AS recipient
                FROM parallel_invitations pi JOIN users us ON us.id=pi.sender_id
                JOIN users ur ON ur.id=pi.recipient_id
                WHERE pi.sender_id=? AND pi.status='pending'
                ORDER BY pi.id DESC LIMIT 50""", (user["id"],)).fetchall()
            bridges = c.execute("""SELECT pi.*,us.username AS sender,ur.username AS recipient
                FROM parallel_invitations pi JOIN users us ON us.id=pi.sender_id
                JOIN users ur ON ur.id=pi.recipient_id
                WHERE (pi.sender_id=? OR pi.recipient_id=?) AND pi.status='accepted'
                ORDER BY pi.id DESC LIMIT 50""", (user["id"], user["id"])).fetchall()
            return {"mine": my_public(c, user["id"]),
                    "incoming": [view(c, r, user) for r in incoming],
                    "outgoing": [view(c, r, user) for r in outgoing],
                    "bridges": [view(c, r, user) for r in bridges],
                    "limits": {"outgoing_pending": MAX_OUTGOING_PENDING,
                               "active_bridges": MAX_ACTIVE_BRIDGES},
                    "notice": "个人知识星图不参与跨馆公开；只有双方主动挑选的当前公开藏品才可会合。双人进度为自行标记，并非真实参观或事实核验。"}

    @app.get("/api/parallel/suggestions")
    def suggestions(exhibit_id: int = Query(ge=1), user=Depends(require_user)):
        with db() as c:
            mine = public(c, exhibit_id)
            if mine is None or mine["user_id"] != user["id"]:
                fail(404, "只能用自己当前真正公开的展品寻找跨馆线索")
            pool = c.execute("""SELECT e.id,e.user_id,e.title,e.category,e.domain,e.tags,
                                  u.username AS curator
                               FROM exhibits e JOIN users u ON u.id=e.user_id
                               WHERE e.user_id<>? AND """ + PUBLIC_SCOPE +
                             " ORDER BY e.id DESC LIMIT ?",
                             (user["id"], SUGGESTION_SCAN)).fetchall()
            ranked = []
            for row in pool:
                why, score = clue(mine, row)
                if score > 0:
                    ranked.append((score, row["id"], row, why))
            ranked.sort(key=lambda t: (-t[0], -t[1]))
            return {"source": exhibit_card(mine),
                    "items": [{**exhibit_card(r), "reason": why, "mode": "metadata_overlap"}
                              for _, _, r, why in ranked[:SUGGESTION_LIMIT]],
                    "notice": "仅对最多 300 件当前公开跨馆展品比较标签、类别与领域。不保证相关性，不代表另一位馆长已同意建立连接。"}

    @app.post("/api/parallel/invitations", status_code=201)
    def invite(payload: InvitationIn, user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            source = public(c, payload.exhibit_id)
            if source is None or source["user_id"] != user["id"]:
                fail(404, "邀请只能选择自己真实公开且仍可访问的藏品")
            recipient = c.execute(
                "SELECT id,username FROM users WHERE username=? COLLATE NOCASE",
                (payload.recipient.strip(),)).fetchone()
            if recipient is None:
                fail(404, "找不到这位馆长")
            if recipient["id"] == user["id"]:
                fail(400, "不能邀请自己建立跨馆会合")
            count = c.execute("SELECT COUNT(*) FROM parallel_invitations WHERE sender_id=? AND status='pending'",
                              (user["id"],)).fetchone()[0]
            if count >= MAX_OUTGOING_PENDING:
                fail(429, "同时最多发送 10 条待回应的跨馆邀请")
            inbound = c.execute("SELECT COUNT(*) FROM parallel_invitations WHERE recipient_id=? AND status='pending'",
                                (recipient["id"],)).fetchone()[0]
            if inbound >= MAX_INCOMING_PENDING:
                fail(429, "对方待回应邀请过多，请稍后再试")
            if not my_public(c, recipient["id"]):
                fail(409, "对方目前没有可用于会合的公开藏品")
            duplicate = c.execute("""SELECT id FROM parallel_invitations
                    WHERE sender_id=? AND recipient_id=? AND status='pending'""",
                    (user["id"], recipient["id"])).fetchone()
            if duplicate:
                fail(409, "你已向这位馆长发出一条待回应邀请")
            cur = c.execute("""INSERT INTO parallel_invitations
                (sender_id,recipient_id,sender_exhibit_id,status,created_at)
                VALUES(?,?,?,'pending',?)""",
                (user["id"], recipient["id"], source["id"], now()))
            return {"id": cur.lastrowid, "recipient": recipient["username"],
                    "notice": "已发送私密邀请；对方同意并选择自己的公开藏品后，才会产生会合。"}

    @app.post("/api/parallel/invitations/{invite_id}/accept")
    def accept(invite_id: int, payload: AcceptIn, user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row = owned_invite(c, invite_id, user)
            if row["recipient_id"] != user["id"]:
                fail(403, "只有受邀馆长可以接受")
            if row["status"] != "pending":
                fail(409, "邀请已被处理")
            a = public(c, row["sender_exhibit_id"])
            b = public(c, payload.exhibit_id)
            if a is None or a["user_id"] != row["sender_id"]:
                fail(409, "发起方的公开藏品已撤回，不能接受")
            if b is None or b["user_id"] != user["id"]:
                fail(404, "只能选择自己当前真正公开的藏品")
            count = c.execute("""SELECT COUNT(*) FROM parallel_invitations WHERE status='accepted'
                AND (sender_id=? OR recipient_id=? OR sender_id=? OR recipient_id=?)""",
                (user["id"], user["id"], row["sender_id"], row["sender_id"])).fetchone()[0]
            # Enforce separate active caps (the combined count above could double count).
            for uid in (row["sender_id"], user["id"]):
                used = c.execute("""SELECT COUNT(*) FROM parallel_invitations
                    WHERE status='accepted' AND (sender_id=? OR recipient_id=?)""",
                    (uid, uid)).fetchone()[0]
                if used >= MAX_ACTIVE_BRIDGES:
                    fail(429, "其中一位馆长的跨馆会合已达到 20 条上限")
            c.execute("""UPDATE parallel_invitations
                SET recipient_exhibit_id=?, status='accepted', responded_at=?
                WHERE id=?""", (b["id"], now(), invite_id))
            row = owned_invite(c, invite_id, user)
            return {"bridge": view(c, row, user),
                    "notice": "双方均已选择当前公开藏品，会合已建立；不公开任何私人星图。"}

    @app.post("/api/parallel/invitations/{invite_id}/decline")
    def decline(invite_id: int, user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row = owned_invite(c, invite_id, user)
            if row["recipient_id"] != user["id"]:
                fail(403, "只有受邀馆长可以拒绝")
            if row["status"] != "pending":
                fail(409, "邀请已被处理")
            c.execute("UPDATE parallel_invitations SET status='declined',responded_at=? WHERE id=?",
                      (now(), invite_id))
            return {"ok": True}

    @app.post("/api/parallel/invitations/{invite_id}/cancel")
    def cancel(invite_id: int, user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row = owned_invite(c, invite_id, user)
            if row["sender_id"] != user["id"]:
                fail(403, "只有发起方可以撤回邀请")
            if row["status"] != "pending":
                fail(409, "邀请已被处理")
            c.execute("UPDATE parallel_invitations SET status='cancelled',responded_at=? WHERE id=?",
                      (now(), invite_id))
            return {"ok": True}

    @app.get("/api/parallel/bridges/{invite_id}")
    def detail(invite_id: int, user=Depends(require_user)):
        with db() as c:
            row = owned_invite(c, invite_id, user)
            if row["status"] != "accepted":
                fail(404, "尚不存在有效会合")
            return view(c, row, user)

    @app.put("/api/parallel/bridges/{invite_id}/mark")
    def mark(invite_id: int, user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row = owned_invite(c, invite_id, user)
            if row["status"] != "accepted":
                fail(409, "会合尚未建立或已关闭")
            state = view(c, row, user)
            if not state["available"]:
                fail(409, "来源已撤回，不能标记当前跨馆探索")
            c.execute("""INSERT INTO parallel_marks(invitation_id,user_id,marked_at)
                VALUES(?,?,?) ON CONFLICT(invitation_id,user_id)
                DO UPDATE SET marked_at=excluded.marked_at""",
                (invite_id, user["id"], now()))
            return {"ok": True, "notice": "这只是你自行标记的探索，不代表实际到访或平台验证。"}

    @app.delete("/api/parallel/bridges/{invite_id}/mark")
    def unmark(invite_id: int, user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row = owned_invite(c, invite_id, user)
            if row["status"] != "accepted":
                fail(409, "会合尚未建立或已关闭")
            c.execute("DELETE FROM parallel_marks WHERE invitation_id=? AND user_id=?",
                      (invite_id, user["id"]))
            return {"ok": True}

    @app.delete("/api/parallel/bridges/{invite_id}")
    def close(invite_id: int, user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row = owned_invite(c, invite_id, user)
            if row["status"] != "accepted":
                fail(409, "会合并非进行中")
            c.execute("DELETE FROM parallel_marks WHERE invitation_id=?", (invite_id,))
            c.execute("""UPDATE parallel_invitations
                SET status='closed',responded_at=? WHERE id=?""", (now(), invite_id))
            return {"ok": True, "notice": "任何一方都可以终止会合。私人星图和原始藏品不受影响。"}
