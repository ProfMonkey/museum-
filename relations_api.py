"""V19 opt-in relations between different real creators' fictional civilizations.

Relations exist only after the invitee agrees. They never transfer assets, modify
world laws, touch another author's timeline, or survive a privacy revocation.
"""
from __future__ import annotations

from typing import Literal
from fastapi import Depends, Query
from pydantic import BaseModel, Field, field_validator

NOTICE = "【虚构文明联动】交流仅作为原创故事模拟，不涉及现实历史、货币或资产交易。"
KINDS = {
    "学术交流": {"knowledge": 5, "energy": -2},
    "文化共鸣": {"culture": 6, "stability": -1},
    "联合勘探": {"food": 3, "ecology": -2},
    "星门议事": {"stability": 4, "culture": 1},
}


class Invitation(BaseModel):
    source_id: int = Field(ge=1)
    target_id: int = Field(ge=1)
    kind: Literal["学术交流", "文化共鸣", "联合勘探", "星门议事"]
    message: str = Field(min_length=8, max_length=350)

    @field_validator("message")
    @classmethod
    def clean(cls, value):
        value = value.strip()
        if len(value) < 8:
            raise ValueError("邀请内容至少八个字符")
        return value


class Decision(BaseModel):
    action: Literal["accept", "decline", "withdraw"]


def mount_relations(app, db, require_user, maybe_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS fantasy_civilization_relations(
          id INTEGER PRIMARY KEY,
          source_id INTEGER NOT NULL REFERENCES fantasy_civilizations(id) ON DELETE CASCADE,
          target_id INTEGER NOT NULL REFERENCES fantasy_civilizations(id) ON DELETE CASCADE,
          proposer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          responder_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          kind TEXT NOT NULL,
          message TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending'
            CHECK (status IN ('pending','accepted','declined','withdrawn')),
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          CHECK (source_id != target_id)
        );
        CREATE INDEX IF NOT EXISTS ix_fantasy_relations_pair
          ON fantasy_civilization_relations(source_id,target_id,status);
        CREATE INDEX IF NOT EXISTS ix_fantasy_relations_user
          ON fantasy_civilization_relations(proposer_id,responder_id,status);
        """)

    def get_civ(c, cid):
        return c.execute("""SELECT cv.id,cv.user_id,cv.name,cv.visibility,
            cv.world_id,w.visibility world_visibility,w.name world_name,
            u.username creator FROM fantasy_civilizations cv
            JOIN fantasy_worlds w ON w.id=cv.world_id
            JOIN users u ON u.id=cv.user_id WHERE cv.id=?""",(cid,)).fetchone()

    def is_public(cv):
        return bool(cv and cv["visibility"]=="public" and cv["world_visibility"]=="public")

    def get_relation(c, rid):
        return c.execute("SELECT * FROM fantasy_civilization_relations WHERE id=?",(rid,)).fetchone()

    def both_public(c, relation):
        return is_public(get_civ(c,relation["source_id"])) and is_public(get_civ(c,relation["target_id"]))

    def view_relation(c, relation, user):
        source=get_civ(c,relation["source_id"])
        target=get_civ(c,relation["target_id"])
        active=relation["status"]=="accepted" and is_public(source) and is_public(target)
        mine=bool(user and user["id"] in (relation["proposer_id"],relation["responder_id"]))
        # Private world names and outgoing messages must not leak after revocation.
        visible=bool(is_public(source) and is_public(target))
        return {
            "id":relation["id"],"kind":relation["kind"],"status":relation["status"],
            "source_id":relation["source_id"] if visible else None,
            "target_id":relation["target_id"] if visible else None,
            "source_name":source["name"] if visible else "已隐藏的文明",
            "target_name":target["name"] if visible else "已隐藏的文明",
            "proposer":source["creator"] if visible else None,
            "responder":target["creator"] if visible else None,
            "message":relation["message"] if visible else None,
            "active":active,"can_accept":bool(mine and active is False and
                visible and relation["status"]=="pending" and user["id"]==relation["responder_id"]),
            "can_decline":bool(mine and relation["status"]=="pending" and user["id"]==relation["responder_id"]),
            "can_withdraw":bool(mine and (
                (relation["status"]=="pending" and user["id"]==relation["proposer_id"]) or
                relation["status"]=="accepted")),
            "created_at":relation["created_at"],"fictional":True
        }

    @app.get("/api/fantasy/relations/config")
    def config():
        return {"kinds":[{"name":name,"effects":effects} for name,effects in KINDS.items()],
                "max_pending_per_creator":10,"max_per_civilization":4,
                "notice":NOTICE}

    @app.get("/api/fantasy/relations/civilizations")
    def directory(user=Depends(maybe_user)):
        with db() as c:
            rows=c.execute("""SELECT cv.id,cv.name,cv.user_id,w.name world_name,
                u.username creator FROM fantasy_civilizations cv
                JOIN fantasy_worlds w ON w.id=cv.world_id
                JOIN users u ON u.id=cv.user_id
                WHERE cv.visibility='public' AND w.visibility='public'
                ORDER BY cv.id DESC LIMIT 180""").fetchall()
            return {"items":[{"id":r["id"],"name":r["name"],"world":r["world_name"],
                   "creator":r["creator"],"mine":bool(user and user["id"]==r["user_id"])}
                   for r in rows],"fictional":True}

    @app.post("/api/fantasy/relations",status_code=201)
    def invite(draft:Invitation,user=Depends(require_user)):
        if draft.source_id==draft.target_id:
            fail(422,"两个文明必须不同")
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            src=get_civ(c,draft.source_id)
            dst=get_civ(c,draft.target_id)
            if not src or src["user_id"]!=user["id"]:
                fail(404,"只能以自己的文明发起交流")
            if not is_public(src) or not is_public(dst):
                fail(404,"双方文明及世界都必须公开")
            if src["user_id"]==dst["user_id"]:
                fail(422,"跨界交流需要两位不同的真实馆长")
            pending=c.execute("""SELECT COUNT(*) FROM fantasy_civilization_relations
                WHERE proposer_id=? AND status='pending'""",(user["id"],)).fetchone()[0]
            if pending>=10:
                fail(429,"待答复邀请达到上限")
            sent=c.execute("""SELECT COUNT(*) FROM fantasy_civilization_relations
                WHERE proposer_id=?""",(user["id"],)).fetchone()[0]
            if sent>=100:
                fail(429,"邀请总量达到上限")
            pair=c.execute("""SELECT status FROM fantasy_civilization_relations WHERE
                (source_id=? AND target_id=?) OR (source_id=? AND target_id=?)
                ORDER BY id DESC""",(src["id"],dst["id"],dst["id"],src["id"])).fetchall()
            if any(x["status"] in ("pending","accepted") for x in pair):
                fail(409,"双方已有待审批或生效的文明关系")
            if len(pair)>=4:
                fail(429,"两文明历史邀请次数已达上限")
            for civil in (src,dst):
                count=c.execute("""SELECT COUNT(*) FROM fantasy_civilization_relations
                    WHERE status='accepted' AND (source_id=? OR target_id=?)""",
                    (civil["id"],civil["id"])).fetchone()[0]
                if count>=4:
                    fail(429,"文明的关系数量达到上限")
            at=now()
            cur=c.execute("""INSERT INTO fantasy_civilization_relations
                (source_id,target_id,proposer_id,responder_id,kind,message,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?)""",(src["id"],dst["id"],user["id"],
                dst["user_id"],draft.kind,draft.message,at,at))
            return {"id":cur.lastrowid,"status":"pending","fictional":True}

    @app.get("/api/fantasy/relations")
    def list_relations(scope:Literal["mine","public"]="public",user=Depends(maybe_user)):
        if scope=="mine" and not user:fail(401,"请先登录")
        with db() as c:
            if scope=="mine":
                rows=c.execute("""SELECT * FROM fantasy_civilization_relations
                    WHERE proposer_id=? OR responder_id=? ORDER BY id DESC LIMIT 100""",
                    (user["id"],user["id"])).fetchall()
            else:
                rows=c.execute("""SELECT * FROM fantasy_civilization_relations
                    WHERE status='accepted' ORDER BY id DESC LIMIT 120""").fetchall()
            return {"items":[view_relation(c,r,user) for r in rows if
                (scope=="mine" or both_public(c,r))],"fictional":True}

    @app.patch("/api/fantasy/relations/{relation_id}")
    def respond(relation_id:int,draft:Decision,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=get_relation(c,relation_id)
            if not row or user["id"] not in (row["proposer_id"],row["responder_id"]):
                fail(404,"无权操作关系")
            action=draft.action
            if action=="accept":
                if user["id"]!=row["responder_id"]:fail(403,"仅受邀馆长可以同意")
                if row["status"]!="pending":fail(409,"邀请状态已变化")
                if not both_public(c,row):fail(409,"双方需保持文明公开")
                for cid in (row["source_id"],row["target_id"]):
                    if c.execute("""SELECT COUNT(*) FROM fantasy_civilization_relations WHERE
                        status='accepted' AND (source_id=? OR target_id=?)""",
                        (cid,cid)).fetchone()[0]>=4:
                        fail(429,"某文明已达到四段关系上限")
                status="accepted"
            elif action=="decline":
                if user["id"]!=row["responder_id"]:fail(403,"仅受邀馆长可以拒绝")
                if row["status"]!="pending":fail(409,"邀请状态已变化")
                status="declined"
            else:
                if row["status"]=="pending" and user["id"]!=row["proposer_id"]:
                    fail(403,"只有提议者可以撤回待处理邀请")
                if row["status"] not in ("pending","accepted"):
                    fail(409,"关系已经结束")
                status="withdrawn"
            c.execute("""UPDATE fantasy_civilization_relations SET status=?,updated_at=?
                WHERE id=?""",(status,now(),relation_id))
            return {"id":relation_id,"status":status,"fictional":True}

    @app.get("/api/fantasy/relations/available")
    def available(timeline_id:int=Query(ge=1),user=Depends(require_user)):
        with db() as c:
            line=c.execute("""SELECT t.civilization_id,t.owner_id FROM fantasy_evolution_timelines t
                WHERE t.id=?""",(timeline_id,)).fetchone()
            if not line or line["owner_id"]!=user["id"]:
                fail(404,"无权管理此纪元")
            rows=c.execute("""SELECT * FROM fantasy_civilization_relations
                WHERE status='accepted' AND (source_id=? OR target_id=?)
                ORDER BY id DESC LIMIT 15""",(line["civilization_id"],line["civilization_id"])).fetchall()
            return {"items":[view_relation(c,r,user) for r in rows if both_public(c,r)],
                    "fictional":True,"notice":NOTICE}


def revoke_civilization(c, civilization_id, now):
    """Drop pending and approved relationships when either civilization revokes publicity."""
    if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='fantasy_civilization_relations'").fetchone():
        c.execute("""UPDATE fantasy_civilization_relations
            SET status='withdrawn',updated_at=? WHERE status IN ('pending','accepted')
            AND (source_id=? OR target_id=?)""",(now,civilization_id,civilization_id))


def revoke_world(c, world_id, now):
    if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='fantasy_civilization_relations'").fetchone():
        c.execute("""UPDATE fantasy_civilization_relations SET status='withdrawn',updated_at=?
          WHERE status IN ('pending','accepted')
          AND (source_id IN (SELECT id FROM fantasy_civilizations WHERE world_id=?)
          OR target_id IN (SELECT id FROM fantasy_civilizations WHERE world_id=?))""",
          (now,world_id,world_id))
