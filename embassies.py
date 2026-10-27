"""V35 · 万界文明大使馆: bilateral, source-verified fictional diplomacy.

No simulated users, fabricated facts or background monitoring.
Only authors of two separately owned *currently public* V34 civilizations can
exchange original in-app fictional letters; neither can write for the other.
Public exposure requires BOTH authors to consent to the SAME revision.
Any V34 source-tree change invalidates publication using a content digest.
"""
from __future__ import annotations

import hashlib
import json

from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field, model_validator
from parallel_universes import PUBLIC_SCOPE

MAX_ACTIVE = 12
MAX_LETTERS = 12


class EmbassyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    my_civ_id: int = Field(ge=1)
    other_civ_id: int = Field(ge=1)
    title: str = Field(min_length=3, max_length=80)
    preface: str = Field(min_length=15, max_length=440)

    @model_validator(mode="after")
    def clean(self):
        self.title = self.title.strip()
        self.preface = self.preface.strip()
        if len(self.title) < 3 or len(self.preface) < 15:
            raise ValueError("外交标题至少3字，开场说明至少15字")
        if self.my_civ_id == self.other_civ_id:
            raise ValueError("请选两座不同真实馆长的公开文明")
        return self


class EmbassyEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=3, max_length=80)
    preface: str = Field(min_length=15, max_length=440)

    @model_validator(mode="after")
    def clean(self):
        self.title = self.title.strip()
        self.preface = self.preface.strip()
        if len(self.title) < 3 or len(self.preface) < 15:
            raise ValueError("外交标题或说明内容过短")
        return self


class LetterIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str = Field(min_length=3, max_length=80)
    message: str = Field(min_length=20, max_length=820)

    @model_validator(mode="after")
    def clean(self):
        self.subject = self.subject.strip()
        self.message = self.message.strip()
        if len(self.subject) < 3 or len(self.message) < 20:
            raise ValueError("书信主题至少3字，正文至少20字")
        return self


def mount_embassies(app, db, require_user, maybe_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS civilization_embassies(
          id INTEGER PRIMARY KEY,
          sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          a_civ_id INTEGER REFERENCES civ_civilizations(id) ON DELETE SET NULL,
          b_civ_id INTEGER REFERENCES civ_civilizations(id) ON DELETE SET NULL,
          a_digest TEXT NOT NULL,
          b_digest TEXT NOT NULL,
          title TEXT NOT NULL,
          preface TEXT NOT NULL,
          state TEXT NOT NULL DEFAULT 'pending'
             CHECK(state IN ('pending','accepted','public','declined','closed')),
          revision INTEGER NOT NULL DEFAULT 1,
          a_vote INTEGER NOT NULL DEFAULT 0,
          b_vote INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          published_at TEXT,
          CHECK(sender_id <> recipient_id)
        );
        CREATE INDEX IF NOT EXISTS ix_embassy_state ON civilization_embassies(state,id DESC);
        CREATE INDEX IF NOT EXISTS ix_embassy_sender ON civilization_embassies(sender_id,id DESC);
        CREATE INDEX IF NOT EXISTS ix_embassy_recipient ON civilization_embassies(recipient_id,id DESC);
        CREATE TABLE IF NOT EXISTS embassy_letters(
          id INTEGER PRIMARY KEY,
          embassy_id INTEGER NOT NULL REFERENCES civilization_embassies(id) ON DELETE CASCADE,
          curator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          subject TEXT NOT NULL,
          message TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_embassy_letters ON embassy_letters(embassy_id,id);
        CREATE TABLE IF NOT EXISTS embassy_source_epochs(
          civ_id INTEGER PRIMARY KEY REFERENCES civ_civilizations(id) ON DELETE CASCADE,
          epoch INTEGER NOT NULL DEFAULT 0
        );
        CREATE TRIGGER IF NOT EXISTS embassy_v34_changed
          AFTER UPDATE ON civ_civilizations
          BEGIN
            INSERT INTO embassy_source_epochs(civ_id,epoch)
            VALUES(NEW.id,1)
            ON CONFLICT(civ_id) DO UPDATE SET epoch=epoch+1;
          END;
        CREATE TABLE IF NOT EXISTS embassy_exhibit_epochs(
          exhibit_id INTEGER PRIMARY KEY REFERENCES exhibits(id) ON DELETE CASCADE,
          epoch INTEGER NOT NULL DEFAULT 0
        );
        CREATE TRIGGER IF NOT EXISTS embassy_source_exhibit_changed
          AFTER UPDATE ON exhibits
          BEGIN
            INSERT INTO embassy_exhibit_epochs(exhibit_id,epoch)
            VALUES(NEW.id,1)
            ON CONFLICT(exhibit_id) DO UPDATE SET epoch=epoch+1;
          END;
        """)

    def src(c, eid):
        if not eid:
            return None
        return c.execute("""SELECT e.id,e.title,e.user_id,e.category,e.domain,
             e.image_url,u.username AS curator,COALESCE(z.epoch,0) AS source_epoch
             FROM exhibits e JOIN users u ON u.id=e.user_id
             LEFT JOIN embassy_exhibit_epochs z ON z.exhibit_id=e.id
             WHERE e.id=? AND """ + PUBLIC_SCOPE, (eid,)).fetchone()

    def civ(c, cid):
        if not cid:
            return None
        r = c.execute("""SELECT v.*,u.username AS owner_name
            FROM civ_civilizations v JOIN users u ON u.id=v.owner_id
            WHERE v.id=? AND v.status='public'""", (cid,)).fetchone()
        if r is None:
            return None
        w = c.execute("""SELECT * FROM collision_worlds WHERE id=? AND status='public'""",
                      (r["world_id"],)).fetchone()
        if w is None or w["revision"] != r["world_revision"]:
            return None
        left, right = src(c,w["left_id"]),src(c,w["right_id"])
        seed = src(c,r["seed_exhibit_id"])
        if not left or not right or not seed or seed["id"] not in (left["id"],right["id"]):
            return None
        turns = c.execute("""SELECT id,turn_index,policy,chapter,narrative,after_json,
             has_anomaly,anomaly_exhibit_id FROM civ_turns
             WHERE civ_id=? ORDER BY turn_index""",(cid,)).fetchall()
        foreign = []
        for t in turns:
            if t["has_anomaly"]:
                x = src(c,t["anomaly_exhibit_id"])
                if x is None:
                    return None
                foreign.append([x["id"],x["title"],x["source_epoch"]])
        epoch = c.execute("""SELECT epoch FROM embassy_source_epochs WHERE civ_id=?""",
                          (cid,)).fetchone()
        fingerprint = {"civ":[r["id"],r["name"],r["charter"],r["world_revision"],
                               epoch["epoch"] if epoch else 0],
            "world":[w["id"],w["revision"],w["law"],w["title"]],
            "left":[left["id"],left["title"],left["source_epoch"]],
            "right":[right["id"],right["title"],right["source_epoch"]],
            "seed":[seed["id"],seed["title"],seed["source_epoch"]],
            "foreign":foreign,
            "turns":[[t["id"],t["turn_index"],t["policy"],t["chapter"],
                      t["narrative"],t["after_json"],t["has_anomaly"],
                      t["anomaly_exhibit_id"]] for t in turns]}
        digest = hashlib.sha256(json.dumps(fingerprint,ensure_ascii=False,
                              sort_keys=True).encode()).hexdigest()
        return {"id":r["id"],"name":r["name"],"owner":r["owner_name"],
                "owner_id":r["owner_id"],"world_name":w["title"],
                "turns":len(turns),"digest":digest}

    def row(c, eid):
        return c.execute("""SELECT e.*,a.username AS sender,b.username AS recipient
           FROM civilization_embassies e
           JOIN users a ON a.id=e.sender_id JOIN users b ON b.id=e.recipient_id
           WHERE e.id=?""",(eid,)).fetchone()

    def letters(c,eid):
        return c.execute("""SELECT l.*,u.username AS curator FROM embassy_letters l
            JOIN users u ON u.id=l.curator_id
            WHERE l.embassy_id=? ORDER BY l.id""",(eid,)).fetchall()

    def member(r,u):
        return bool(u and u["id"] in (r["sender_id"],r["recipient_id"]))

    def live_pair(c,r):
        a,b=civ(c,r["a_civ_id"]),civ(c,r["b_civ_id"])
        if not a or not b or a["owner_id"]!=r["sender_id"] or b["owner_id"]!=r["recipient_id"]:
            return None
        if a["digest"]!=r["a_digest"] or b["digest"]!=r["b_digest"]:
            return None
        return a,b

    def can_publish(c,r):
        if r["state"]!="public" or not live_pair(c,r):
            return False
        if r["a_vote"]!=r["revision"] or r["b_vote"]!=r["revision"]:
            return False
        authors={x["curator_id"] for x in letters(c,r["id"])}
        return r["sender_id"] in authors and r["recipient_id"] in authors

    def data(c,r,user=None):
        pair=live_pair(c,r)
        okay=pair is not None
        ls=letters(c,r["id"]) if okay else []
        return {"id":r["id"],"state":r["state"],
                "available":okay,"revision":r["revision"],
                "title":r["title"] if okay else "来源已经更新或撤回",
                "preface":r["preface"] if okay else "",
                "curators":[r["sender"],r["recipient"]],
                "a":pair[0] if okay else None,
                "b":pair[1] if okay else None,
                "letters":[{"id":x["id"],"subject":x["subject"],"message":x["message"],
                            "curator":x["curator"],"created_at":x["created_at"],
                            "is_mine":bool(user and user["id"]==x["curator_id"])}
                           for x in ls],
                "is_member":member(r,user),
                "my_role":("a" if user and user["id"]==r["sender_id"] else
                           "b" if user and user["id"]==r["recipient_id"] else None),
                "approved":{"a":r["a_vote"]==r["revision"],
                            "b":r["b_vote"]==r["revision"]},
                "published_at":r["published_at"] if can_publish(c,r) else None,
                "notice":"两位真实作者亲自写信、亲自同意公开同一版本；这是架空文明纪事，不代表真实历史或真实外交。"}

    def owned(c,eid,user):
        r=row(c,eid)
        if not r or not member(r,user):
            fail(404,"此使馆不属于你的合作关系")
        return r

    def active(c,r):
        if r["state"] not in ("accepted","public"):
            fail(409,"双方还未完成邀请接受，或者外交已经结束")
        if not live_pair(c,r):
            fail(409,"来源作品已变化或撤回，请重新核对公开文明")

    def reset(c,eid):
        c.execute("""UPDATE civilization_embassies SET revision=revision+1,
            a_vote=0,b_vote=0,state='accepted',published_at=NULL,updated_at=?
            WHERE id=?""",(now(),eid))

    @app.get("/api/embassies/public")
    def public():
        with db() as c:
            ids=c.execute("""SELECT id FROM civilization_embassies
                WHERE state='public' ORDER BY id DESC LIMIT 70""").fetchall()
            result=[]
            for x in ids:
                r=row(c,x["id"])
                if can_publish(c,r):
                    v=data(c,r)
                    result.append({"id":v["id"],"title":v["title"],
                                   "curators":v["curators"],
                                   "civilizations":[v["a"],v["b"]],
                                   "letters":len(v["letters"])})
                if len(result)>=36:
                    break
            return {"items":result}

    @app.get("/api/embassies/mine")
    def mine(user=Depends(require_user)):
        with db() as c:
            ids=c.execute("""SELECT id FROM civilization_embassies
                 WHERE sender_id=? OR recipient_id=? ORDER BY id DESC LIMIT 70""",
                 (user["id"],user["id"])).fetchall()
            my=c.execute("""SELECT id FROM civ_civilizations
                WHERE owner_id=? AND status='public' ORDER BY id DESC LIMIT 60""",
                (user["id"],)).fetchall()
            other=c.execute("""SELECT id FROM civ_civilizations
                WHERE owner_id<>? AND status='public' ORDER BY id DESC LIMIT 120""",
                (user["id"],)).fetchall()
            return {"items":[data(c,row(c,x["id"]),user) for x in ids],
                    "my_civilizations":[v for x in my if (v:=civ(c,x["id"])) is not None],
                    "other_civilizations":[v for x in other if (v:=civ(c,x["id"])) is not None][:50],
                    "limits":{"active":MAX_ACTIVE,"letters":MAX_LETTERS}}

    @app.post("/api/embassies",status_code=201)
    def invite(payload:EmbassyIn,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            a,b=civ(c,payload.my_civ_id),civ(c,payload.other_civ_id)
            if not a or not b or a["owner_id"]!=user["id"]:
                fail(404,"必须从自己的公开文明邀请另一位真实馆长的公开文明")
            if a["owner_id"]==b["owner_id"]:
                fail(422,"不能自己与自己建立外交使馆")
            for uid in (a["owner_id"],b["owner_id"]):
                n=c.execute("""SELECT COUNT(*) FROM civilization_embassies
                     WHERE (sender_id=? OR recipient_id=?)
                     AND state IN ('pending','accepted','public')""",(uid,uid)).fetchone()[0]
                if n>=MAX_ACTIVE:
                    fail(429,"任意一位馆长最多参与12座进行中的使馆")
            dup=c.execute("""SELECT 1 FROM civilization_embassies
                WHERE state IN ('pending','accepted','public')
                  AND ((a_civ_id=? AND b_civ_id=?) OR (a_civ_id=? AND b_civ_id=?))
                LIMIT 1""",(a["id"],b["id"],b["id"],a["id"])).fetchone()
            if dup:fail(409,"这两座文明已有进行中的使馆邀请")
            cur=c.execute("""INSERT INTO civilization_embassies(
                sender_id,recipient_id,a_civ_id,b_civ_id,a_digest,b_digest,
                title,preface,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (a["owner_id"],b["owner_id"],a["id"],b["id"],
                 a["digest"],b["digest"],payload.title,payload.preface,now(),now()))
            return {"id":cur.lastrowid,"state":"pending"}

    @app.get("/api/embassies/{embassy_id}")
    def detail(embassy_id:int,user=Depends(maybe_user)):
        with db() as c:
            r=row(c,embassy_id)
            if r is None:
                fail(404,"不存在这座使馆")
            if not member(r,user) and not can_publish(c,r):
                fail(404,"这座使馆尚未双方同意公开，或原始文明已撤回")
            return data(c,r,user)

    @app.post("/api/embassies/{embassy_id}/accept")
    def accept(embassy_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owned(c,embassy_id,user)
            if r["recipient_id"]!=user["id"] or r["state"]!="pending":
                fail(409,"只有实际被邀请的馆长可以接受仍在等待的邀请")
            if not live_pair(c,r):
                fail(409,"两座公开文明已发生变化，不能接受原版邀请")
            c.execute("""UPDATE civilization_embassies SET state='accepted',updated_at=?
                WHERE id=?""",(now(),embassy_id))
            return {"ok":True,"state":"accepted"}

    @app.post("/api/embassies/{embassy_id}/decline")
    def decline(embassy_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owned(c,embassy_id,user)
            if r["recipient_id"]!=user["id"] or r["state"]!="pending":
                fail(409,"只有被邀请人可以拒绝尚待确认的邀请")
            c.execute("""UPDATE civilization_embassies
                 SET state='declined',updated_at=? WHERE id=?""",(now(),embassy_id))
            return {"ok":True,"state":"declined"}

    @app.post("/api/embassies/{embassy_id}/cancel")
    def cancel(embassy_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owned(c,embassy_id,user)
            if r["sender_id"]!=user["id"] or r["state"]!="pending":
                fail(409,"只有邀请发起人能撤回等待中的邀请")
            c.execute("""UPDATE civilization_embassies
                SET state='closed',updated_at=? WHERE id=?""",(now(),embassy_id))
            return {"ok":True,"state":"closed"}

    @app.put("/api/embassies/{embassy_id}")
    def edit(embassy_id:int,payload:EmbassyEdit,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owned(c,embassy_id,user)
            active(c,r)
            c.execute("""UPDATE civilization_embassies SET title=?,preface=?
                 WHERE id=?""",(payload.title,payload.preface,embassy_id))
            reset(c,embassy_id)
            return {"ok":True,"state":"accepted",
                    "notice":"联名作品前言更改，原有双方发布批准已同时撤销。"}

    @app.post("/api/embassies/{embassy_id}/letters",status_code=201)
    def add_letter(embassy_id:int,payload:LetterIn,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owned(c,embassy_id,user)
            active(c,r)
            n=c.execute("SELECT COUNT(*) FROM embassy_letters WHERE embassy_id=?",
                        (embassy_id,)).fetchone()[0]
            if n>=MAX_LETTERS:
                fail(409,"每座使馆最多可共同撰写12封外交书信")
            cur=c.execute("""INSERT INTO embassy_letters(
                 embassy_id,curator_id,subject,message,created_at)
                 VALUES(?,?,?,?,?)""",
                 (embassy_id,user["id"],payload.subject,payload.message,now()))
            reset(c,embassy_id)
            return {"id":cur.lastrowid,"state":"accepted"}

    @app.delete("/api/embassies/{embassy_id}/letters/{letter_id}")
    def remove_letter(embassy_id:int,letter_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owned(c,embassy_id,user)
            active(c,r)
            x=c.execute("""SELECT curator_id FROM embassy_letters
                 WHERE id=? AND embassy_id=?""",(letter_id,embassy_id)).fetchone()
            if not x:fail(404,"找不到这封使馆书信")
            if x["curator_id"]!=user["id"]:
                fail(403,"只能撤回自己亲自撰写的外交书信")
            c.execute("DELETE FROM embassy_letters WHERE id=?",(letter_id,))
            reset(c,embassy_id)
            return {"ok":True,"state":"accepted"}

    @app.post("/api/embassies/{embassy_id}/approve")
    def approve(embassy_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owned(c,embassy_id,user)
            active(c,r)
            authors={x["curator_id"] for x in letters(c,embassy_id)}
            if not {r["sender_id"],r["recipient_id"]}.issubset(authors):
                fail(409,"两位真实馆长必须分别写过至少一封外交书信")
            side="a_vote" if user["id"]==r["sender_id"] else "b_vote"
            c.execute(f"UPDATE civilization_embassies SET {side}=?,updated_at=? WHERE id=?",
                      (r["revision"],now(),embassy_id))
            current=row(c,embassy_id)
            if current["a_vote"]==current["revision"] and current["b_vote"]==current["revision"]:
                c.execute("""UPDATE civilization_embassies SET
                    state='public',published_at=?,updated_at=? WHERE id=?""",
                    (now(),now(),embassy_id))
            return {"embassy":data(c,row(c,embassy_id),user)}

    @app.post("/api/embassies/{embassy_id}/retract")
    def retract(embassy_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owned(c,embassy_id,user)
            if r["state"] not in ("accepted","public"):
                fail(409,"当前外交纪事无法撤回批准")
            reset(c,embassy_id)
            return {"ok":True,"state":"accepted"}

    @app.post("/api/embassies/{embassy_id}/refresh")
    def refresh_source_versions(embassy_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owned(c,embassy_id,user)
            if r["state"] not in ("accepted","public"):
                fail(409,"只有已建立的使馆可以重新核验源文明")
            a,b=civ(c,r["a_civ_id"]),civ(c,r["b_civ_id"])
            if not a or not b or a["owner_id"]!=r["sender_id"] or b["owner_id"]!=r["recipient_id"]:
                fail(409,"任一源文明不再公开或不属于原有馆长")
            c.execute("""UPDATE civilization_embassies SET a_digest=?,b_digest=?
                 WHERE id=?""",(a["digest"],b["digest"],embassy_id))
            reset(c,embassy_id)
            return {"ok":True,"state":"accepted",
                    "notice":"双方原始文明已重新核验。全部旧公开批准已撤销，双方需重新确认同一个新版本。"}

    @app.post("/api/embassies/{embassy_id}/close")
    def close(embassy_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owned(c,embassy_id,user)
            if r["state"] in ("closed","declined"):
                fail(409,"该使馆已结束")
            c.execute("""UPDATE civilization_embassies SET state='closed',
                 a_vote=0,b_vote=0,published_at=NULL,updated_at=? WHERE id=?""",
                 (now(),embassy_id))
            return {"ok":True,"state":"closed"}
