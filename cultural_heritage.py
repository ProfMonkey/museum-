"""V36 · 万界遗产交换站: voluntary, two-author virtual cultural gifts.

An exchange is a FICTIONAL shared exhibition between two real curators who have
an already-public, double-approved V35 embassy. Each chooses one of their own
currently public exhibits, writes their own explanation and independently
approves the final revision. Ownership is NEVER transferred. Parent embassy
consent is checked with V35's exact visibility validator on every public read.
"""
from __future__ import annotations

from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from parallel_universes import PUBLIC_SCOPE

MAX_PER_EMBASSY = 10
NOTE_MIN = 12


class ExchangeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    embassy_id: int = Field(ge=1)
    a_exhibit_id: int = Field(ge=1)
    b_exhibit_id: int = Field(ge=1)
    title: str = Field(min_length=3,max_length=90)
    premise: str = Field(min_length=20,max_length=560)

    @model_validator(mode="after")
    def normalize(self):
        self.title=self.title.strip()
        self.premise=self.premise.strip()
        if len(self.title)<3 or len(self.premise)<20:
            raise ValueError("交换主题至少3字，联合背景至少20字")
        if self.a_exhibit_id==self.b_exhibit_id:
            raise ValueError("两件文化礼物必须不同")
        return self


class NoteIn(BaseModel):
    model_config=ConfigDict(extra="forbid")
    text: str = Field(min_length=NOTE_MIN,max_length=680)

    @model_validator(mode="after")
    def normalize(self):
        self.text=self.text.strip()
        if len(self.text)<NOTE_MIN:
            raise ValueError("馆长自己的文化解释至少12字")
        return self


class TopicIn(BaseModel):
    model_config=ConfigDict(extra="forbid")
    title: str = Field(min_length=3,max_length=90)
    premise: str = Field(min_length=20,max_length=560)

    @model_validator(mode="after")
    def normalize(self):
        self.title=self.title.strip()
        self.premise=self.premise.strip()
        if len(self.title)<3 or len(self.premise)<20:
            raise ValueError("主题及背景不能过短")
        return self


def mount_cultural_heritage(app,db,require_user,maybe_user,now,fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS cultural_exchanges(
            id INTEGER PRIMARY KEY,
            embassy_id INTEGER NOT NULL REFERENCES civilization_embassies(id) ON DELETE CASCADE,
            creator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            a_exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
            b_exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            premise TEXT NOT NULL,
            a_note TEXT NOT NULL DEFAULT '',
            b_note TEXT NOT NULL DEFAULT '',
            state TEXT NOT NULL DEFAULT 'draft'
                CHECK(state IN('draft','public','closed')),
            embassy_revision INTEGER NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            a_vote INTEGER NOT NULL DEFAULT 0,
            b_vote INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            CHECK(a_exhibit_id <> b_exhibit_id)
        );
        CREATE INDEX IF NOT EXISTS ix_exchange_embassy ON cultural_exchanges(embassy_id,id DESC);
        CREATE INDEX IF NOT EXISTS ix_exchange_state ON cultural_exchanges(state,id DESC);
        CREATE TABLE IF NOT EXISTS exchange_passports(
            exchange_id INTEGER NOT NULL REFERENCES cultural_exchanges(id) ON DELETE CASCADE,
            visitor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            version INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(exchange_id,visitor_id)
        );
        """)

    def embassy(c,eid):
        return c.execute("""SELECT * FROM civilization_embassies WHERE id=?""",(eid,)).fetchone()

    def validated_embassy(c,eid):
        r=embassy(c,eid)
        return r if r is not None and app.state.embassy_public_validator(c,r) else None

    def exhibit(c,eid):
        if not eid:
            return None
        return c.execute("""SELECT e.id,e.title,e.domain,e.category,e.image_url,
                    e.user_id,u.username AS curator
                  FROM exhibits e JOIN users u ON u.id=e.user_id
                  WHERE e.id=? AND """+PUBLIC_SCOPE,(eid,)).fetchone()

    def card(x):
        return {"id":x["id"],"title":x["title"],"domain":x["domain"],
                "category":x["category"],"image_url":x["image_url"],
                "curator":x["curator"]}

    def get(c,eid):
        return c.execute("""SELECT * FROM cultural_exchanges WHERE id=?""",(eid,)).fetchone()

    def participant(r,u):
        return bool(r and u and u["id"] in (r["sender_id"],r["recipient_id"]))

    def owned(c,eid,u):
        x=get(c,eid)
        if x is None:
            fail(404,"没有这次虚构遗产交换")
        r=embassy(c,x["embassy_id"])
        if not participant(r,u):
            fail(404,"不是这座真实使馆的合作馆长")
        return x,r

    def context(c,x):
        r=validated_embassy(c,x["embassy_id"])
        if r is None or r["revision"]!=x["embassy_revision"]:
            return None
        a,b=exhibit(c,x["a_exhibit_id"]),exhibit(c,x["b_exhibit_id"])
        if a is None or b is None or a["id"]==b["id"]:
            return None
        if a["user_id"]!=r["sender_id"] or b["user_id"]!=r["recipient_id"]:
            return None
        return r,a,b

    def publishable(c,x):
        return (x is not None and x["state"]=="public" and
                x["a_vote"]==x["version"] and x["b_vote"]==x["version"] and
                len(x["a_note"].strip())>=NOTE_MIN and
                len(x["b_note"].strip())>=NOTE_MIN and
                context(c,x) is not None)

    def count_passports(c,x):
        return c.execute("""SELECT COUNT(*) FROM exchange_passports
                      WHERE exchange_id=? AND version=?""",
                      (x["id"],x["version"])).fetchone()[0]

    def encode(c,x,u=None):
        available=context(c,x)
        if available is None:
            # Do not show old title/notes, even to participating users, since
            # author text may contain now-private exhibit names.
            return {"id":x["id"],"available":False,"state":x["state"],
                    "title":"原始馆藏或外交授权已变化","embassy_id":None,
                    "a":None,"b":None,"premise":"","a_note":"","b_note":"",
                    "my_side":None,"version":x["version"]}
        r,a,b=available
        public=publishable(c,x)
        my_side=("a" if u and u["id"]==r["sender_id"] else
                 "b" if u and u["id"]==r["recipient_id"] else None)
        return {"id":x["id"],"available":True,"state":x["state"],
                "embassy_id":r["id"],"embassy_revision":x["embassy_revision"],
                "title":x["title"],"premise":x["premise"],
                "a":card(a),"b":card(b),"a_note":x["a_note"],"b_note":x["b_note"],
                "authors":[a["curator"],b["curator"]],
                "version":x["version"],"my_side":my_side,
                "approved":{"a":x["a_vote"]==x["version"],
                            "b":x["b_vote"]==x["version"]},
                "passports":count_passports(c,x) if public else 0,
                "my_passport":bool(public and u and c.execute(
                     """SELECT 1 FROM exchange_passports WHERE exchange_id=?
                        AND visitor_id=? AND version=?""",
                     (x["id"],u["id"],x["version"])).fetchone()),
                "notice":"这仅是象征性的跨文明文化互赠展览。原始藏品的所有权永远留在原馆长手里；没有发生实物或数字产权转移。"}

    def reset(c,eid):
        c.execute("""UPDATE cultural_exchanges SET version=version+1,
                 state='draft',a_vote=0,b_vote=0,updated_at=?
                 WHERE id=?""",(now(),eid))
        c.execute("DELETE FROM exchange_passports WHERE exchange_id=?",(eid,))

    def need_live(c,x):
        if x["state"]=="closed":
            fail(409,"这次交换已终止")
        if context(c,x) is None:
            fail(409,"源作品或使馆授权变更，需重新确认来源后才能编辑")

    @app.get("/api/heritage/embassies")
    def my_embassies(u=Depends(require_user)):
        with db() as c:
            rows=c.execute("""SELECT * FROM civilization_embassies WHERE
                     sender_id=? OR recipient_id=? ORDER BY id DESC LIMIT 60""",
                     (u["id"],u["id"])).fetchall()
            good=[r for r in rows if app.state.embassy_public_validator(c,r)]
            return {"items":[{"id":r["id"],"title":r["title"],
                      "side":"a" if r["sender_id"]==u["id"] else "b",
                      "revision":r["revision"]} for r in good]}

    @app.get("/api/heritage/sources")
    def sources(embassy_id:int=Query(ge=1),u=Depends(require_user)):
        with db() as c:
            r=validated_embassy(c,embassy_id)
            if r is None or not participant(r,u):
                fail(404,"仅合作双方可以给当前双方批准公开的使馆挑选藏品")
            rows=c.execute("""SELECT e.id,e.title,e.domain,e.category,e.image_url,
                     e.user_id,u.username AS curator
                     FROM exhibits e JOIN users u ON u.id=e.user_id
                     WHERE e.user_id IN (?,?) AND """+PUBLIC_SCOPE+"""
                     ORDER BY e.id DESC LIMIT 120""",
                     (r["sender_id"],r["recipient_id"])).fetchall()
            return {"a":[card(x) for x in rows if x["user_id"]==r["sender_id"]][:30],
                    "b":[card(x) for x in rows if x["user_id"]==r["recipient_id"]][:30],
                    "notice":"只能选择双方自己当前公开的真实馆藏；挑选素材不等于对方同意发布。"}

    @app.get("/api/heritage/public")
    def gallery():
        with db() as c:
            rows=c.execute("""SELECT * FROM cultural_exchanges
                         WHERE state='public' ORDER BY id DESC LIMIT 80""").fetchall()
            result=[]
            for x in rows:
                if not publishable(c,x):
                    continue
                v=encode(c,x)
                result.append({"id":x["id"],"title":v["title"],
                    "a":v["a"],"b":v["b"],"authors":v["authors"],
                    "passports":v["passports"]})
                if len(result)>=36:
                    break
            return {"items":result,
                    "notice":"公开的文化遗产互赠需两位真实馆长各自撰文并批准同一个版本。没有物权转移。"}

    @app.get("/api/heritage/mine")
    def mine(u=Depends(require_user)):
        with db() as c:
            rows=c.execute("""SELECT x.* FROM cultural_exchanges x
                 JOIN civilization_embassies e ON e.id=x.embassy_id
                 WHERE e.sender_id=? OR e.recipient_id=?
                 ORDER BY x.id DESC LIMIT 100""",(u["id"],u["id"])).fetchall()
            return {"items":[encode(c,x,u) for x in rows]}

    @app.post("/api/heritage",status_code=201)
    def create(payload:ExchangeIn,u=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=validated_embassy(c,payload.embassy_id)
            if r is None or not participant(r,u):
                fail(404,"必须是两位馆长均已批准公开的使馆参与者")
            count=c.execute("SELECT COUNT(*) FROM cultural_exchanges WHERE embassy_id=?",
                            (r["id"],)).fetchone()[0]
            if count>=MAX_PER_EMBASSY:
                fail(409,"每座使馆最多创建10件共同遗产")
            a,b=exhibit(c,payload.a_exhibit_id),exhibit(c,payload.b_exhibit_id)
            if a is None or b is None or a["user_id"]!=r["sender_id"] or b["user_id"]!=r["recipient_id"]:
                fail(404,"双方必须分别拿出自己当前公开的真实藏品")
            cur=c.execute("""INSERT INTO cultural_exchanges(
                 embassy_id,creator_id,a_exhibit_id,b_exhibit_id,title,premise,
                 embassy_revision,created_at,updated_at)
                 VALUES(?,?,?,?,?,?,?,?,?)""",
                 (r["id"],u["id"],a["id"],b["id"],payload.title,payload.premise,
                  r["revision"],now(),now()))
            return {"id":cur.lastrowid,"state":"draft",
                    "notice":"只有双方合作馆长能看到当前私密交换草稿。双方各自撰写文化意义并批准同一版本才公开。"}

    @app.get("/api/heritage/{exchange_id}")
    def detail(exchange_id:int,u=Depends(maybe_user)):
        with db() as c:
            x=get(c,exchange_id)
            if x is None:
                fail(404,"不存在这件共同文化遗产")
            r=embassy(c,x["embassy_id"])
            if not participant(r,u) and not publishable(c,x):
                fail(404,"这件文化互赠仍为私密，或任一原始作品已撤回")
            return encode(c,x,u)

    @app.put("/api/heritage/{exchange_id}/note")
    def change_note(exchange_id:int,payload:NoteIn,u=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            x,r=owned(c,exchange_id,u)
            need_live(c,x)
            col="a_note" if u["id"]==r["sender_id"] else "b_note"
            c.execute("UPDATE cultural_exchanges SET "+col+"=? WHERE id=?",
                      (payload.text,exchange_id))
            reset(c,exchange_id)
            return {"state":"draft","notice":"已由你本人署名写下藏品文化诠释；之前的双方批准已失效。"}

    @app.put("/api/heritage/{exchange_id}/topic")
    def change_topic(exchange_id:int,payload:TopicIn,u=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            x,_=owned(c,exchange_id,u)
            need_live(c,x)
            c.execute("""UPDATE cultural_exchanges SET title=?,premise=? WHERE id=?""",
                      (payload.title,payload.premise,exchange_id))
            reset(c,exchange_id)
            return {"state":"draft"}

    @app.post("/api/heritage/{exchange_id}/approve")
    def approve(exchange_id:int,u=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            x,r=owned(c,exchange_id,u)
            need_live(c,x)
            if len(x["a_note"].strip())<NOTE_MIN or len(x["b_note"].strip())<NOTE_MIN:
                fail(409,"必须由两位馆长分别为自己的原始藏品写下文化意义说明")
            col="a_vote" if u["id"]==r["sender_id"] else "b_vote"
            c.execute("UPDATE cultural_exchanges SET "+col+"=?,updated_at=? WHERE id=?",
                      (x["version"],now(),exchange_id))
            updated=get(c,exchange_id)
            complete=updated["a_vote"]==updated["version"] and updated["b_vote"]==updated["version"]
            if complete:
                c.execute("""UPDATE cultural_exchanges SET state='public',
                     updated_at=? WHERE id=?""",(now(),exchange_id))
            return {"published":complete,"state":"public" if complete else "draft",
                    "notice":"双方批准了同一版真实来源的象征文化互赠。" if complete
                              else "已记录你的独立批准，尚需另一位真实馆长确认。"}

    @app.post("/api/heritage/{exchange_id}/retract")
    def retract(exchange_id:int,u=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            x,_=owned(c,exchange_id,u)
            if x["state"]=="closed":
                fail(409,"这项遗产交换已经终止")
            reset(c,exchange_id)
            return {"state":"draft","notice":"已撤回共同公开及旧版双方批准，不删除原始藏品。"}

    @app.post("/api/heritage/{exchange_id}/rebase")
    def rebase(exchange_id:int,u=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            x,r=owned(c,exchange_id,u)
            if x["state"]=="closed":
                fail(409,"已终止的交换不能重启")
            current=validated_embassy(c,x["embassy_id"])
            if current is None:
                fail(409,"双方需先让源使馆重新合法公开并批准")
            a,b=exhibit(c,x["a_exhibit_id"]),exhibit(c,x["b_exhibit_id"])
            if a is None or b is None or a["user_id"]!=current["sender_id"] or b["user_id"]!=current["recipient_id"]:
                fail(409,"两个原始藏品必须仍然公开且归原馆长所有")
            c.execute("""UPDATE cultural_exchanges SET embassy_revision=?
                  WHERE id=?""",(current["revision"],exchange_id))
            reset(c,exchange_id)
            return {"state":"draft",
                    "notice":"重新校验双馆长授权与两件公开藏品成功；全部旧批准失效，须双方重新批准。"}

    @app.post("/api/heritage/{exchange_id}/close")
    def close(exchange_id:int,u=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            x,_=owned(c,exchange_id,u)
            if x["state"]=="closed":
                fail(409,"这次交换已经终止")
            c.execute("""UPDATE cultural_exchanges SET state='closed',
                a_vote=0,b_vote=0,version=version+1,updated_at=?
                WHERE id=?""",(now(),exchange_id))
            c.execute("DELETE FROM exchange_passports WHERE exchange_id=?",(exchange_id,))
            return {"state":"closed"}

    @app.post("/api/heritage/{exchange_id}/passport")
    def passport(exchange_id:int,u=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            x=get(c,exchange_id)
            if not publishable(c,x):
                fail(404,"只允许为当前双方批准且真实源仍合法的文化互赠盖章")
            c.execute("""INSERT INTO exchange_passports
                (exchange_id,visitor_id,version,created_at)
                VALUES(?,?,?,?) ON CONFLICT(exchange_id,visitor_id)
                DO UPDATE SET version=excluded.version,created_at=excluded.created_at""",
                (exchange_id,u["id"],x["version"],now()))
            return {"ok":True,"passports":count_passports(c,x),
                    "notice":"只是这个登录账号在站内领取一次虚拟访问章，不代表双方藏品或产权发生移交。"}
