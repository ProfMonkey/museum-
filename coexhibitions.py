"""V30 — 万物联合展厅.

Two curators jointly build an exhibition from their own currently public exhibits.
Both must approve the SAME revision before visitors can see it. No exhibit titles or
old descriptions are persisted here. A single revoked source closes public access.
A visitor's stamp is self-reported, not a verified physical or digital visit.
"""
from __future__ import annotations

from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field, model_validator
from parallel_universes import PUBLIC_SCOPE

MAX_EXHIBITIONS = 10
MAX_ITEMS = 12
MAX_PUBLIC_FEED = 36

class CreateExhibition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bridge_id: int = Field(ge=1)
    title: str = Field(min_length=2, max_length=80)
    introduction: str = Field(default="", max_length=480)

    @model_validator(mode="after")
    def normalized(self):
        self.title = self.title.strip()
        self.introduction = self.introduction.strip()
        if len(self.title) < 2:
            raise ValueError("展厅名称至少两个字符")
        return self

class ExhibitionEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=2, max_length=80)
    introduction: str = Field(default="", max_length=480)

    @model_validator(mode="after")
    def normalized(self):
        self.title = self.title.strip()
        self.introduction = self.introduction.strip()
        if len(self.title) < 2:
            raise ValueError("展厅名称至少两个字符")
        return self

class ContributionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exhibit_id: int = Field(ge=1)
    commentary: str = Field(min_length=8, max_length=300)

    @model_validator(mode="after")
    def normalized(self):
        self.commentary = self.commentary.strip()
        if len(self.commentary) < 8:
            raise ValueError("请用至少八个字符介绍这件藏品与主题的关系")
        return self


def mount_coexhibitions(app, db, require_user, maybe_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS co_exhibitions(
          id INTEGER PRIMARY KEY,
          bridge_id INTEGER NOT NULL UNIQUE REFERENCES parallel_invitations(id) ON DELETE CASCADE,
          title TEXT NOT NULL,
          introduction TEXT NOT NULL DEFAULT '',
          revision INTEGER NOT NULL DEFAULT 1,
          a_approved INTEGER NOT NULL DEFAULT 0,
          b_approved INTEGER NOT NULL DEFAULT 0,
          state TEXT NOT NULL DEFAULT 'draft' CHECK(state IN ('draft','public','closed')),
          created_at TEXT NOT NULL,
          published_at TEXT
        );
        CREATE INDEX IF NOT EXISTS ix_coexhibitions_public ON co_exhibitions(state,id DESC);
        CREATE TABLE IF NOT EXISTS co_exhibition_items(
          id INTEGER PRIMARY KEY,
          exhibition_id INTEGER NOT NULL REFERENCES co_exhibitions(id) ON DELETE CASCADE,
          curator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
          commentary TEXT NOT NULL,
          slot INTEGER NOT NULL,
          created_at TEXT NOT NULL,
          UNIQUE(exhibition_id,exhibit_id)
        );
        CREATE INDEX IF NOT EXISTS ix_coexhibition_items_order ON co_exhibition_items(exhibition_id,slot,id);
        CREATE TABLE IF NOT EXISTS co_exhibition_stamps(
          exhibition_id INTEGER NOT NULL REFERENCES co_exhibitions(id) ON DELETE CASCADE,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          stamped_at TEXT NOT NULL,
          PRIMARY KEY(exhibition_id,user_id)
        );
        """)

    def live(c, exhibit_id):
        if not exhibit_id:
            return None
        return c.execute("""SELECT e.id,e.user_id,e.title,e.category,e.domain,e.tags,
                                   e.description,e.image_url,u.username AS curator
            FROM exhibits e JOIN users u ON u.id=e.user_id
            WHERE e.id=? AND """+PUBLIC_SCOPE, (exhibit_id,)).fetchone()

    def card(x):
        return {"id": x["id"], "title": x["title"],
                "category": x["category"], "domain": x["domain"],
                "curator": x["curator"], "image_url": x["image_url"],
                "tags": [v.strip() for v in x["tags"].replace("，",",").split(",") if v.strip()],
                "description": x["description"][:240]}

    def fetch_row(c, exhibition_id):
        return c.execute("""SELECT x.*,p.sender_id AS a_id,p.recipient_id AS b_id,
             p.sender_exhibit_id AS a_anchor,p.recipient_exhibit_id AS b_anchor,
             p.status AS bridge_status, a.username AS a_username,b.username AS b_username
             FROM co_exhibitions x
             JOIN parallel_invitations p ON p.id=x.bridge_id
             JOIN users a ON a.id=p.sender_id JOIN users b ON b.id=p.recipient_id
             WHERE x.id=?""", (exhibition_id,)).fetchone()

    def member(row, user):
        return bool(user and user["id"] in (row["a_id"],row["b_id"]))

    def participants(c, row):
        if row["bridge_status"] != "accepted":
            return False
        a = live(c, row["a_anchor"])
        b = live(c, row["b_anchor"])
        return bool(a is not None and b is not None and
                    a["user_id"]==row["a_id"] and b["user_id"]==row["b_id"])

    def item_records(c, row):
        return c.execute("""SELECT * FROM co_exhibition_items WHERE exhibition_id=?
             ORDER BY slot,id""", (row["id"],)).fetchall()

    def validated_items(c, row, items):
        # Unlike private V27 notes, a joint public show requires every
        # contributed exhibit to be visibly published by its original owner.
        checked = []
        for entry in items:
            x = live(c, entry["exhibit_id"])
            if x is None or x["user_id"] != entry["curator_id"] or x["user_id"] not in (row["a_id"],row["b_id"]):
                return None
            checked.append((entry, x))
        return checked

    def public_ok(c, row):
        if row["state"] != "public" or row["a_approved"] != row["revision"] or row["b_approved"] != row["revision"]:
            return False
        if not participants(c,row):
            return False
        items = item_records(c,row)
        return bool(items and validated_items(c,row,items) is not None and
                    {entry["curator_id"] for entry in items}=={row["a_id"],row["b_id"]})

    def counts(c, row):
        return c.execute("""SELECT COUNT(*) AS total,
               SUM(CASE WHEN curator_id=? THEN 1 ELSE 0 END) AS a_total,
               SUM(CASE WHEN curator_id=? THEN 1 ELSE 0 END) AS b_total
               FROM co_exhibition_items WHERE exhibition_id=?""",
               (row["a_id"],row["b_id"],row["id"])).fetchone()

    def view(c,row,user,public=False):
        is_member = member(row,user)
        if public and not public_ok(c,row):
            return None
        accessible = participants(c,row)
        items = item_records(c,row)
        checked = validated_items(c,row,items) if accessible else None
        complete = checked is not None
        # If any underlying source has been withdrawn, suppress even the authored
        # exhibition description: it may mention former third-party content.
        hidden = not accessible or not complete
        if public and hidden:
            return None
        result = {
            "id":row["id"], "bridge_id":row["bridge_id"],
            "title": "原始展品已不可用" if hidden else row["title"],
            "introduction": "" if hidden else row["introduction"],
            "curators":[row["a_username"],row["b_username"]],
            "state":row["state"],"available":not hidden,
            "revision":row["revision"],"created_at":row["created_at"],
            "published_at":row["published_at"],
            "approved":{"a":row["a_approved"]==row["revision"],
                        "b":row["b_approved"]==row["revision"]},
            "is_member":is_member,
            "my_role":("a" if user and user["id"]==row["a_id"] else
                       "b" if user and user["id"]==row["b_id"] else None),
            "items":[],"stamps":0,"stamped":False
        }
        for entry in items:
            x = live(c,entry["exhibit_id"])
            if hidden or not x or x["user_id"] != entry["curator_id"]:
                result["items"].append({
                    "id":entry["id"],"source_unavailable":True,"exhibit":None,
                    "commentary":None,"curator":None,
                    "is_mine":bool(user and user["id"]==entry["curator_id"])})
            else:
                result["items"].append({
                    "id":entry["id"],"source_unavailable":False,
                    "exhibit":card(x),"commentary":entry["commentary"],
                    "curator":x["curator"],
                    "is_mine":bool(user and user["id"]==entry["curator_id"])})
        if public_ok(c,row):
            result["stamps"]=c.execute(
                "SELECT COUNT(*) FROM co_exhibition_stamps WHERE exhibition_id=?",
                (row["id"],)).fetchone()[0]
            if user:
                result["stamped"]=bool(c.execute(
                    "SELECT 1 FROM co_exhibition_stamps WHERE exhibition_id=? AND user_id=?",
                    (row["id"],user["id"])).fetchone())
        return result

    def owned(c, exhibition_id, user, for_write=False):
        row = fetch_row(c,exhibition_id)
        if not row or not member(row,user):
            fail(404,"找不到你的联合展厅")
        if for_write and row["state"]=="closed":
            fail(409,"联合展厅已经结束")
        return row

    def new_revision(c,row):
        c.execute("""UPDATE co_exhibitions SET revision=revision+1,
          a_approved=0,b_approved=0,state='draft',published_at=NULL WHERE id=?""",
          (row["id"],))
        # Visitor stamps belong to the previously mutually approved exhibition
        # and must never count toward a changed exhibition.
        c.execute("DELETE FROM co_exhibition_stamps WHERE exhibition_id=?",(row["id"],))

    def manage_preview(c,row,user):
        return view(c,row,user)

    @app.get("/api/coexhibitions/public")
    def public_gallery(user=Depends(maybe_user)):
        with db() as c:
            rows=c.execute("""SELECT id FROM co_exhibitions WHERE state='public'
                ORDER BY published_at DESC,id DESC LIMIT ?""",(MAX_PUBLIC_FEED,)).fetchall()
            result=[]
            for r in rows:
                full=fetch_row(c,r["id"])
                x=view(c,full,user,True)
                if x is not None:
                    result.append({"id":x["id"],"title":x["title"],"introduction":x["introduction"],
                        "curators":x["curators"],"count":len(x["items"]), "stamps":x["stamps"]})
            return {"items":result,"notice":"只展示真实两位馆长共同审批、且所有原始公开藏品仍可访问的联合展览。"}

    @app.get("/api/coexhibitions/mine")
    def my_exhibitions(user=Depends(require_user)):
        with db() as c:
            rows=c.execute("""SELECT x.id FROM co_exhibitions x JOIN parallel_invitations p ON p.id=x.bridge_id
                WHERE (p.sender_id=? OR p.recipient_id=?) AND x.state<>'closed'
                ORDER BY x.id DESC LIMIT 40""",(user["id"],user["id"])).fetchall()
            options=c.execute("""SELECT p.id,p.sender_id,p.recipient_id,
                a.username AS sender,b.username AS recipient
                FROM parallel_invitations p
                JOIN users a ON a.id=p.sender_id JOIN users b ON b.id=p.recipient_id
                WHERE p.status='accepted' AND (p.sender_id=? OR p.recipient_id=?)
                 AND NOT EXISTS (SELECT 1 FROM co_exhibitions x WHERE x.bridge_id=p.id)
                ORDER BY p.id DESC LIMIT 40""",(user["id"],user["id"])).fetchall()
            available_bridges=[]
            for opt in options:
                # Reuse existing public anchor checks (otherwise a revoked
                # V29 bridge must not become a new joint gallery).
                a=c.execute("SELECT sender_exhibit_id,recipient_exhibit_id FROM parallel_invitations WHERE id=?",(opt["id"],)).fetchone()
                aa=live(c,a["sender_exhibit_id"]);bb=live(c,a["recipient_exhibit_id"])
                if aa and bb and aa["user_id"]==opt["sender_id"] and bb["user_id"]==opt["recipient_id"]:
                    available_bridges.append({"id":opt["id"],"curators":[opt["sender"],opt["recipient"]]})
            my_items=c.execute("""SELECT e.id,e.title FROM exhibits e
                 WHERE e.user_id=? AND """+PUBLIC_SCOPE+"""
                 ORDER BY e.id DESC LIMIT 80""",(user["id"],)).fetchall()
            return {"items":[manage_preview(c,fetch_row(c,r["id"]),user) for r in rows],
                    "bridge_options":available_bridges,
                    "my_public_exhibits":[{"id":x["id"],"title":x["title"]} for x in my_items],
                    "limits":{"max_per_user":MAX_EXHIBITIONS,"max_items":MAX_ITEMS},
                    "notice":"双方均需批准同一版本才能公开；任何修改都会撤销批准和旧探索印章。"}

    @app.post("/api/coexhibitions",status_code=201)
    def create(payload:CreateExhibition,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            bridge=c.execute("SELECT * FROM parallel_invitations WHERE id=?",(payload.bridge_id,)).fetchone()
            if not bridge or user["id"] not in (bridge["sender_id"],bridge["recipient_id"]):
                fail(404,"找不到双方参与的平行宇宙会合")
            if bridge["status"]!="accepted":
                fail(409,"只有仍有效的双人会合才能发起联合展厅")
            if c.execute("SELECT 1 FROM co_exhibitions WHERE bridge_id=?",(payload.bridge_id,)).fetchone():
                fail(409,"这场会合已经建立过联合展厅")
            if not participants(c,{"bridge_status":bridge["status"],
                     "a_anchor":bridge["sender_exhibit_id"],"b_anchor":bridge["recipient_exhibit_id"],
                     "a_id":bridge["sender_id"],"b_id":bridge["recipient_id"]}):
                fail(409,"双方会合使用的公开藏品已撤回")
            n=c.execute("""SELECT COUNT(*) FROM co_exhibitions x
                  JOIN parallel_invitations p ON p.id=x.bridge_id
                  WHERE x.state<>'closed' AND
                   (p.sender_id=? OR p.recipient_id=?)""",
                   (user["id"],user["id"])).fetchone()[0]
            if n>=MAX_EXHIBITIONS:
                fail(429,"每人最多管理十座进行中的联合展厅")
            cur=c.execute("""INSERT INTO co_exhibitions(bridge_id,title,introduction,created_at)
                VALUES(?,?,?,?)""",(payload.bridge_id,payload.title,payload.introduction,now()))
            return {"exhibition":manage_preview(c,fetch_row(c,cur.lastrowid),user)}

    @app.get("/api/coexhibitions/{exhibition_id}")
    def detail(exhibition_id:int,user=Depends(maybe_user)):
        with db() as c:
            row=fetch_row(c,exhibition_id)
            if row is None:
                fail(404,"展厅不存在")
            if member(row,user):
                return manage_preview(c,row,user)
            x=view(c,row,user,True)
            if x is None:
                fail(404,"展厅尚未公开、已经结束或源展品已撤回")
            return x

    @app.put("/api/coexhibitions/{exhibition_id}")
    def edit(exhibition_id:int,payload:ExhibitionEdit,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=owned(c,exhibition_id,user,True)
            c.execute("UPDATE co_exhibitions SET title=?,introduction=? WHERE id=?",
                      (payload.title,payload.introduction,exhibition_id))
            new_revision(c,row)
            return {"exhibition":manage_preview(c,fetch_row(c,exhibition_id),user)}

    @app.post("/api/coexhibitions/{exhibition_id}/items",status_code=201)
    def add_item(exhibition_id:int,payload:ContributionIn,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=owned(c,exhibition_id,user,True)
            if not participants(c,row):
                fail(409,"双方的跨馆会合或公开来源已不可用")
            x=live(c,payload.exhibit_id)
            if x is None or x["user_id"]!=user["id"]:
                fail(404,"只能贡献自己当前真正公开的藏品")
            n=c.execute("SELECT COUNT(*) FROM co_exhibition_items WHERE exhibition_id=?",
                        (exhibition_id,)).fetchone()[0]
            if n>=MAX_ITEMS:
                fail(429,"联合展厅最多放十二件展品")
            if c.execute("""SELECT 1 FROM co_exhibition_items WHERE exhibition_id=? AND exhibit_id=?""",
                         (exhibition_id,x["id"])).fetchone():
                fail(409,"这件藏品已经加入展厅")
            last=c.execute("SELECT COALESCE(MAX(slot),0) FROM co_exhibition_items WHERE exhibition_id=?",
                           (exhibition_id,)).fetchone()[0]
            cur=c.execute("""INSERT INTO co_exhibition_items
                (exhibition_id,curator_id,exhibit_id,commentary,slot,created_at)
                VALUES(?,?,?,?,?,?)""",
                (exhibition_id,user["id"],x["id"],payload.commentary,last+1,now()))
            new_revision(c,row)
            return {"id":cur.lastrowid,"exhibition":manage_preview(c,fetch_row(c,exhibition_id),user)}

    @app.delete("/api/coexhibitions/{exhibition_id}/items/{item_id}")
    def remove_item(exhibition_id:int,item_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=owned(c,exhibition_id,user,True)
            entry=c.execute("""SELECT * FROM co_exhibition_items
                WHERE id=? AND exhibition_id=?""",(item_id,exhibition_id)).fetchone()
            if not entry:
                fail(404,"联合展品不存在")
            if entry["curator_id"]!=user["id"]:
                fail(403,"只能撤下自己贡献的展品")
            c.execute("DELETE FROM co_exhibition_items WHERE id=?",(item_id,))
            new_revision(c,row)
            return {"ok":True}

    @app.post("/api/coexhibitions/{exhibition_id}/approve")
    def approve(exhibition_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=owned(c,exhibition_id,user,True)
            if not participants(c,row):
                fail(409,"跨馆会合或其公开来源已撤回，无法审批")
            items=item_records(c,row)
            if len(items)<2 or validated_items(c,row,items) is None:
                fail(409,"至少需要双方各一件仍然公开的真实藏品")
            if {e["curator_id"] for e in items}!={row["a_id"],row["b_id"]}:
                fail(409,"双方馆长必须各自贡献至少一件公开藏品")
            which="a_approved" if user["id"]==row["a_id"] else "b_approved"
            c.execute("UPDATE co_exhibitions SET "+which+"=revision WHERE id=?",(exhibition_id,))
            updated=fetch_row(c,exhibition_id)
            if updated["a_approved"]==updated["revision"] and updated["b_approved"]==updated["revision"]:
                c.execute("UPDATE co_exhibitions SET state='public',published_at=? WHERE id=?",
                          (now(),exhibition_id))
            return {"exhibition":manage_preview(c,fetch_row(c,exhibition_id),user)}

    @app.post("/api/coexhibitions/{exhibition_id}/retract")
    def retract(exhibition_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=owned(c,exhibition_id,user,True)
            new_revision(c,row)
            return {"exhibition":manage_preview(c,fetch_row(c,exhibition_id),user)}

    @app.delete("/api/coexhibitions/{exhibition_id}")
    def close(exhibition_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=owned(c,exhibition_id,user,True)
            c.execute("UPDATE co_exhibitions SET state='closed',a_approved=0,b_approved=0,published_at=NULL WHERE id=?",
                      (exhibition_id,))
            c.execute("DELETE FROM co_exhibition_stamps WHERE exhibition_id=?",(exhibition_id,))
            return {"ok":True,"notice":"联合展厅已关闭，原始藏品及私人星图不受影响。"}

    @app.post("/api/coexhibitions/{exhibition_id}/stamp")
    def stamp(exhibition_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=fetch_row(c,exhibition_id)
            if not row or not public_ok(c,row):
                fail(404,"展览当前不可参观或未获得双方批准")
            c.execute("""INSERT INTO co_exhibition_stamps(exhibition_id,user_id,stamped_at)
               VALUES(?,?,?) ON CONFLICT(exhibition_id,user_id)
               DO NOTHING""",(exhibition_id,user["id"],now()))
            return {"ok":True,"notice":"已自行领取数字印章；不代表实际到访或完整观看认证。"}

    @app.delete("/api/coexhibitions/{exhibition_id}/stamp")
    def unstamp(exhibition_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            c.execute("DELETE FROM co_exhibition_stamps WHERE exhibition_id=? AND user_id=?",
                      (exhibition_id,user["id"]))
        return {"ok":True}
