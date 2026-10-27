"""V33 — 万物碰撞机 · 两件真实藏品碰撞出用户原创的平行世界。

This is a *fictional thought-experiment* studio, not an AI factual generator.
No private exhibits or old source snapshots are published. Public collision
pages and family trees recheck BOTH source visibility on each read.
"""
from __future__ import annotations

from hashlib import sha256
from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal
from parallel_universes import PUBLIC_SCOPE

MAX_PER_OWNER = 24
LAW_TITLES = {
    "time_reverse": "时间逆流",
    "size_swap": "大小互换",
    "memory_trade": "记忆交易",
    "material_exchange": "物质交换",
    "world_merge": "世界融合",
    "cause_reverse": "因果倒置",
}
LAW_PROMPTS = {
    "time_reverse": "假设两件事物所处的时间方向互换，最初会发生什么？",
    "size_swap": "假设两件事物突然交换体量与尺度，世界会怎样适应？",
    "memory_trade": "假设两件事物能交换彼此见证过的记忆，会留下什么秘密？",
    "material_exchange": "假设两件事物的物质结构互换，谁还能保持原来的身份？",
    "world_merge": "假设原本无关的两种世界规则突然相遇，会出现什么新文明？",
    "cause_reverse": "假设结果先于原因出现，观察者会如何重新理解它们？",
}


class CollisionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    left_id: int = Field(ge=1)
    right_id: int = Field(ge=1)
    law: Literal["time_reverse","size_swap","memory_trade",
                 "material_exchange","world_merge","cause_reverse"]
    title: str = Field(min_length=3, max_length=80)
    premise: str = Field(min_length=20, max_length=480)
    choice_a: str = Field(min_length=2, max_length=60)
    ending_a: str = Field(min_length=15, max_length=900)
    choice_b: str = Field(min_length=2, max_length=60)
    ending_b: str = Field(min_length=15, max_length=900)

    @model_validator(mode="after")
    def normalize(self):
        for field in ("title","premise","choice_a","choice_b","ending_a","ending_b"):
            setattr(self,field,getattr(self,field).strip())
        if self.left_id == self.right_id:
            raise ValueError("两件碰撞藏品必须不同")
        if len(self.title)<3 or len(self.premise)<20 or min(len(self.ending_a),len(self.ending_b))<15:
            raise ValueError("请完整填写原创世界的主题、假设与两个结局")
        if min(len(self.choice_a),len(self.choice_b))<2 or self.choice_a==self.choice_b:
            raise ValueError("两种分岔选择必须不同，且至少两个字符")
        return self


def mount_collision_universes(app, db, require_user, maybe_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS collision_worlds(
          id INTEGER PRIMARY KEY,
          owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          left_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
          right_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
          law TEXT NOT NULL,
          title TEXT NOT NULL,
          premise TEXT NOT NULL,
          choice_a TEXT NOT NULL,
          ending_a TEXT NOT NULL,
          choice_b TEXT NOT NULL,
          ending_b TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','public')),
          revision INTEGER NOT NULL DEFAULT 1,
          parent_id INTEGER REFERENCES collision_worlds(id) ON DELETE SET NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          CHECK(left_id <> right_id),
          CHECK(owner_id > 0)
        );
        CREATE INDEX IF NOT EXISTS ix_collision_owner ON collision_worlds(owner_id,id DESC);
        CREATE INDEX IF NOT EXISTS ix_collision_status ON collision_worlds(status,id DESC);
        CREATE INDEX IF NOT EXISTS ix_collision_sources ON collision_worlds(left_id,right_id,status);
        CREATE TABLE IF NOT EXISTS collision_choices(
          world_id INTEGER NOT NULL REFERENCES collision_worlds(id) ON DELETE CASCADE,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          picked TEXT NOT NULL CHECK(picked IN ('a','b')),
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          PRIMARY KEY(world_id,user_id)
        );
        """)

    def src(c,eid):
        if not eid: return None
        return c.execute("""SELECT e.id,e.title,e.category,e.domain,
             e.image_url,e.tags,u.username AS curator
             FROM exhibits e JOIN users u ON u.id=e.user_id
             WHERE e.id=? AND """+PUBLIC_SCOPE,(eid,)).fetchone()

    def card(r):
        return {"id":r["id"],"title":r["title"],"category":r["category"],
                "domain":r["domain"],"image_url":r["image_url"],"curator":r["curator"]}

    def world(c,wid):
        return c.execute("""SELECT w.*,u.username AS author FROM collision_worlds w
          JOIN users u ON u.id=w.owner_id WHERE w.id=?""",(wid,)).fetchone()

    def authorized(c,wid,user):
        row=world(c,wid)
        if not row or row["owner_id"]!=user["id"]:
            fail(404,"只能管理自己的原创碰撞世界")
        return row

    def sources(c,row):
        a=src(c,row["left_id"])
        b=src(c,row["right_id"])
        return (a,b) if a is not None and b is not None and a["id"]!=b["id"] else (None,None)

    def public(c,row):
        a,b=sources(c,row)
        return row["status"]=="public" and a is not None and b is not None

    def counts(c,wid):
        counts={"a":0,"b":0}
        rows=c.execute("""SELECT picked,COUNT(*) AS n FROM collision_choices
           WHERE world_id=? GROUP BY picked""",(wid,)).fetchall()
        for r in rows:counts[r["picked"]]=r["n"]
        return counts

    def data(c,row,user=None):
        a,b=sources(c,row)
        is_owner=bool(user and user["id"]==row["owner_id"])
        valid=a is not None and b is not None
        # If a source becomes unavailable, hide BOTH old source titles and
        # all author-written premises/endings (they may quote the withdrawn title).
        response={"id":row["id"],"status":row["status"],"available":valid,
                  "revision":row["revision"],"author":row["author"],
                  "is_owner":is_owner,"left":card(a) if valid else None,
                  "right":card(b) if valid else None,
                  "law":row["law"],"law_title":LAW_TITLES[row["law"]],
                  "title":row["title"] if valid else "失效的平行世界",
                  "premise":row["premise"] if valid else "",
                  "choice_a":row["choice_a"] if valid else "",
                  "ending_a":row["ending_a"] if valid else "",
                  "choice_b":row["choice_b"] if valid else "",
                  "ending_b":row["ending_b"] if valid else "",
                  "parent_id":None,
                  "created_at":row["created_at"],
                  "votes":{"a":0,"b":0},"my_choice":None,
                  "notice":"两个结局是馆长原创的思想实验，不代表科学事实、真实未来或两件藏品之间的因果关系。"}
        if row["status"]=="public" and valid:
            response["votes"]=counts(c,row["id"])
            if row["parent_id"]:
                parent=world(c,row["parent_id"])
                if parent and public(c,parent):
                    response["parent_id"]=parent["id"]
            if user:
                choice=c.execute("SELECT picked FROM collision_choices WHERE world_id=? AND user_id=?",
                                 (row["id"],user["id"])).fetchone()
                if choice: response["my_choice"]=choice["picked"]
        return response

    def create(c,payload,owner,parent_id=None):
        n=c.execute("SELECT COUNT(*) FROM collision_worlds WHERE owner_id=?",
                    (owner["id"],)).fetchone()[0]
        if n>=MAX_PER_OWNER:fail(429,"每名馆长最多创作24个平行实验")
        a=src(c,payload.left_id)
        b=src(c,payload.right_id)
        if not a or not b:fail(404,"必须选择两件当前真正公开的原始藏品")
        cur=c.execute("""INSERT INTO collision_worlds(
          owner_id,left_id,right_id,law,title,premise,choice_a,ending_a,
          choice_b,ending_b,parent_id,created_at,updated_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (owner["id"],payload.left_id,payload.right_id,payload.law,
           payload.title,payload.premise,payload.choice_a,payload.ending_a,
           payload.choice_b,payload.ending_b,parent_id,now(),now()))
        return cur.lastrowid

    def set_draft(c,wid):
        c.execute("""UPDATE collision_worlds SET status='draft',
            revision=revision+1,updated_at=? WHERE id=?""",(now(),wid))
        c.execute("DELETE FROM collision_choices WHERE world_id=?",(wid,))

    @app.get("/api/collisions/laws")
    def laws():
        return {"items":[{"id":k,"title":v,"prompt":LAW_PROMPTS[k]}
                        for k,v in LAW_TITLES.items()],
                "notice":"规则只是架空世界的创作提示，不是实际物理定律。"}

    @app.get("/api/collisions/sources")
    def source_picker(q:str=""):
        keyword=q.strip()[:60]
        with db() as c:
            where=PUBLIC_SCOPE
            args=[]
            if keyword:
                where+=" AND (e.title LIKE ? OR e.tags LIKE ? OR e.category LIKE ?)"
                args.extend(["%"+keyword+"%"]*3)
            rows=c.execute("""SELECT e.id,e.title,e.category,e.domain,e.image_url,
                        e.tags,u.username AS curator
                        FROM exhibits e JOIN users u ON u.id=e.user_id
                        WHERE """+where+" ORDER BY e.id DESC LIMIT 40",args).fetchall()
            return {"items":[card(x) for x in rows]}

    @app.get("/api/collisions/preview")
    def preview(left_id:int=Query(ge=1),right_id:int=Query(ge=1),
                law:str=Query(default="world_merge")):
        if law not in LAW_TITLES:fail(422,"无效的架空世界法则")
        if left_id==right_id:fail(400,"请选择两件不同的藏品")
        with db() as c:
            a=src(c,left_id);b=src(c,right_id)
            if not a or not b:fail(404,"原始藏品已经不存在或不允许公开访问")
            seed=sha256(f"{min(left_id,right_id)}:{max(left_id,right_id)}:{law}".encode()).hexdigest()[:12]
            return {"left":card(a),"right":card(b),"law":law,"law_title":LAW_TITLES[law],
                    "seed":seed,
                    "prompt":"假设「"+a["title"]+"」与「"+b["title"]+"」进入同一个世界。"+LAW_PROMPTS[law],
                    "notice":"这是可重复的模板式创作开场（由物件与法则确定），不会自动生成事实或作者原创结局。"}

    @app.get("/api/collisions")
    def gallery():
        with db() as c:
            rows=c.execute("""SELECT w.*,u.username AS author FROM collision_worlds w
                JOIN users u ON u.id=w.owner_id
                WHERE w.status='public' ORDER BY w.id DESC LIMIT 80""").fetchall()
            found=[]
            for row in rows:
                a,b=sources(c,row)
                if a is None or b is None:
                    continue
                found.append({"id":row["id"],"title":row["title"],
                              "author":row["author"],"left":card(a),"right":card(b),
                              "law":row["law"],"law_title":LAW_TITLES[row["law"]]})
                if len(found)>=36:
                    break
            return {"items":found,
                    "notice":"只展示真实馆长自愿公开的虚构思想实验；原始藏品权限每次即时重验。"}

    @app.get("/api/collisions/mine")
    def mine(user=Depends(require_user)):
        with db() as c:
            rows=c.execute("""SELECT w.*,u.username AS author FROM collision_worlds w
                JOIN users u ON u.id=w.owner_id WHERE w.owner_id=? ORDER BY w.id DESC""",
                (user["id"],)).fetchall()
            return {"items":[data(c,r,user) for r in rows],
                    "notice":"默认私密草稿，只有你亲自点击公开后才加入公共世界目录。"}

    @app.get("/api/collisions/echoes")
    def echoes(left_id:int=Query(ge=1),right_id:int=Query(ge=1)):
        if left_id==right_id:fail(400,"必须选择不同来源")
        with db() as c:
            a=src(c,left_id);b=src(c,right_id)
            if not a or not b:fail(404,"只对真正公开的原始藏品展示平行谱系")
            rows=c.execute("""SELECT w.*,u.username AS author FROM collision_worlds w
                JOIN users u ON u.id=w.owner_id
                WHERE w.status='public'
                  AND ((w.left_id=? AND w.right_id=?)
                    OR (w.left_id=? AND w.right_id=?))
                ORDER BY w.id DESC LIMIT 40""",
                (left_id,right_id,right_id,left_id)).fetchall()
            return {"source":[card(a),card(b)],
                    "items":[{"id":x["id"],"title":x["title"],"author":x["author"],
                        "law_title":LAW_TITLES[x["law"]]} for x in rows if public(c,x)],
                    "notice":"同一对真实物件可以诞生多个互不相同的原创假设世界。"}

    @app.post("/api/collisions",status_code=201)
    def add(payload:CollisionIn,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            wid=create(c,payload,user)
            return {"id":wid,"status":"draft"}

    @app.get("/api/collisions/{world_id}")
    def detail(world_id:int,user=Depends(maybe_user)):
        with db() as c:
            row=world(c,world_id)
            if not row:fail(404,"平行实验不存在")
            if not user or row["owner_id"]!=user["id"]:
                if not public(c,row):fail(404,"该思想实验尚未公开或原始藏品已撤回")
            return data(c,row,user)

    @app.put("/api/collisions/{world_id}")
    def edit(world_id:int,payload:CollisionIn,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            authorized(c,world_id,user)
            if not src(c,payload.left_id) or not src(c,payload.right_id):
                fail(404,"必须选择当前合法公开的原始藏品")
            c.execute("""UPDATE collision_worlds SET left_id=?,right_id=?,
                law=?,title=?,premise=?,choice_a=?,ending_a=?,choice_b=?,ending_b=?
                WHERE id=?""",
                (payload.left_id,payload.right_id,payload.law,payload.title,
                 payload.premise,payload.choice_a,payload.ending_a,
                 payload.choice_b,payload.ending_b,world_id))
            set_draft(c,world_id)
            return {"world":data(c,world(c,world_id),user),
                    "notice":"草稿已更新。所有旧版分支投票已清除，须重新公开。"}

    @app.post("/api/collisions/{world_id}/publish")
    def publish(world_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=authorized(c,world_id,user)
            a,b=sources(c,row)
            if not a or not b:fail(409,"两件真实原始藏品不再同时公开")
            c.execute("""UPDATE collision_worlds SET status='public',updated_at=?
                WHERE id=?""",(now(),world_id))
            return {"world":data(c,world(c,world_id),user)}

    @app.post("/api/collisions/{world_id}/unpublish")
    def unpublish(world_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            authorized(c,world_id,user)
            set_draft(c,world_id)
            return {"ok":True,"notice":"实验已恢复私密草稿，旧版投票已清零。"}

    @app.delete("/api/collisions/{world_id}")
    def delete(world_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            authorized(c,world_id,user)
            c.execute("DELETE FROM collision_worlds WHERE id=?",(world_id,))
            return {"ok":True}

    @app.post("/api/collisions/{world_id}/choose/{branch}")
    def choose(world_id:int,branch:Literal["a","b"],user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=world(c,world_id)
            if not row or not public(c,row):
                fail(404,"实验未公开或来源已失效")
            c.execute("""INSERT INTO collision_choices(world_id,user_id,picked,created_at,updated_at)
                VALUES(?,?,?,?,?) ON CONFLICT(world_id,user_id)
                DO UPDATE SET picked=excluded.picked,updated_at=excluded.updated_at""",
                (world_id,user["id"],branch,now(),now()))
            return {"choice":branch,"votes":counts(c,world_id),
                    "notice":"只是你的虚构分支选择，不代表真实世界会发生这些结果。"}

    @app.post("/api/collisions/{world_id}/remix",status_code=201)
    def remix(world_id:int,payload:CollisionIn,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            parent=world(c,world_id)
            if not parent or not public(c,parent):
                fail(404,"只能改写当下公开且所有来源仍合法的思想实验")
            if {payload.left_id,payload.right_id}!={parent["left_id"],parent["right_id"]}:
                fail(400,"同源改写必须保留两件真实藏品；可以重新制定法则和全部分岔")
            wid=create(c,payload,user,parent_id=parent["id"])
            return {"id":wid,"status":"draft","parent_id":parent["id"],
                    "notice":"你的独立创作已保存为私密草稿。原作者不为新世界承担事实责任。"}
