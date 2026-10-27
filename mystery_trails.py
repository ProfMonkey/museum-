"""V32 · 万物谜案馆: curator-built treasure hunts across genuine public exhibits.

Every clue and its solution references a live public museum exhibit. No automatic
AI provenance, fabricated submissions or snapshots of withdrawn items.
Anonymous visitors see only public introductions; individual puzzle progress
belongs to the authenticated player. No GitHub Actions required to use this.
"""
from __future__ import annotations

import hashlib
from pydantic import BaseModel, ConfigDict, Field, model_validator
from fastapi import Depends
from parallel_universes import PUBLIC_SCOPE

MAX_TRAILS = 15
MAX_STAGES = 6
MIN_STAGES = 2
MAX_CHOICES = 4


class TrailIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=3, max_length=80)
    premise: str = Field(min_length=15, max_length=600)

    @model_validator(mode="after")
    def clean(self):
        self.title = self.title.strip()
        self.premise = self.premise.strip()
        if len(self.title) < 3 or len(self.premise) < 15:
            raise ValueError("谜案标题至少三字，引子至少十五字")
        return self


class StageIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    clue: str = Field(min_length=12, max_length=360)
    hint: str = Field(min_length=6, max_length=200)
    answer_exhibit_id: int = Field(ge=1)
    distractor_ids: list[int] = Field(min_length=2, max_length=3)

    @model_validator(mode="after")
    def clean(self):
        self.clue = self.clue.strip()
        self.hint = self.hint.strip()
        if len(self.clue) < 12 or len(self.hint) < 6:
            raise ValueError("线索至少十二字，提示至少六字")
        ids = [self.answer_exhibit_id, *self.distractor_ids]
        if len(ids) != len(set(ids)):
            raise ValueError("每个谜题的选项必须指向不同的真实藏品")
        return self


class GuessIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exhibit_id: int = Field(ge=1)


def mount_mystery_trails(app, db, require_user, maybe_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS mystery_trails(
          id INTEGER PRIMARY KEY,
          owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          title TEXT NOT NULL,
          premise TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'draft'
            CHECK(status IN ('draft','published')),
          revision INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_mystery_trails_status
          ON mystery_trails(status,id DESC);
        CREATE INDEX IF NOT EXISTS ix_mystery_trails_owner
          ON mystery_trails(owner_id,id DESC);
        CREATE TABLE IF NOT EXISTS mystery_stages(
          id INTEGER PRIMARY KEY,
          trail_id INTEGER NOT NULL REFERENCES mystery_trails(id) ON DELETE CASCADE,
          clue TEXT NOT NULL,
          hint TEXT NOT NULL,
          answer_exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_mystery_stages_trail
          ON mystery_stages(trail_id,id);
        CREATE TABLE IF NOT EXISTS mystery_choices(
          stage_id INTEGER NOT NULL REFERENCES mystery_stages(id) ON DELETE CASCADE,
          exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          is_answer INTEGER NOT NULL CHECK(is_answer IN (0,1)),
          PRIMARY KEY(stage_id,exhibit_id)
        );
        CREATE TABLE IF NOT EXISTS mystery_progress(
          trail_id INTEGER NOT NULL REFERENCES mystery_trails(id) ON DELETE CASCADE,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          revision INTEGER NOT NULL,
          solved INTEGER NOT NULL DEFAULT 0,
          wrong INTEGER NOT NULL DEFAULT 0,
          stage_wrong INTEGER NOT NULL DEFAULT 0,
          completed_at TEXT,
          updated_at TEXT NOT NULL,
          PRIMARY KEY(trail_id,user_id)
        );
        CREATE INDEX IF NOT EXISTS ix_mystery_progress_user
          ON mystery_progress(user_id,updated_at DESC);
        """)

    def live(c, exhibit_id):
        if not exhibit_id:
            return None
        return c.execute("""SELECT e.id,e.user_id,e.title,e.domain,e.category,
               e.time_bucket,e.image_url,u.username AS curator
          FROM exhibits e JOIN users u ON u.id=e.user_id
          WHERE e.id=? AND """+PUBLIC_SCOPE, (exhibit_id,)).fetchone()

    def exhibit_card(row):
        return {"id":row["id"],"title":row["title"],"domain":row["domain"],
                "category":row["category"],"curator":row["curator"],
                "image_url":row["image_url"],"time_bucket":row["time_bucket"]}

    def trail(c, trail_id):
        return c.execute("""SELECT m.*,u.username AS curator
          FROM mystery_trails m JOIN users u ON u.id=m.owner_id
          WHERE m.id=?""", (trail_id,)).fetchone()

    def owned(c, trail_id, user):
        row = trail(c,trail_id)
        if not row or row["owner_id"] != user["id"]:
            fail(404, "只能管理自己创建的谜案")
        return row

    def stages(c,trail_id):
        return c.execute("""SELECT * FROM mystery_stages
          WHERE trail_id=? ORDER BY id""",(trail_id,)).fetchall()

    def choices(c,stage_id):
        return c.execute("""SELECT * FROM mystery_choices WHERE stage_id=?""",
                         (stage_id,)).fetchall()

    def valid(c, row):
        if row["status"]!="published":
            return False
        all_stages=stages(c,row["id"])
        if not MIN_STAGES<=len(all_stages)<=MAX_STAGES:
            return False
        answers=set()
        for stage in all_stages:
            opts=choices(c,stage["id"])
            correct=[o for o in opts if o["is_answer"]]
            if not 3<=len(opts)<=MAX_CHOICES or len(correct)!=1:
                return False
            if not stage["answer_exhibit_id"] or correct[0]["exhibit_id"]!=stage["answer_exhibit_id"]:
                return False
            if stage["answer_exhibit_id"] in answers:
                return False
            answers.add(stage["answer_exhibit_id"])
            if any(live(c,x["exhibit_id"]) is None for x in opts):
                return False
        return True

    def score(wrong,stage_count):
        return max(1, 3 - wrong//max(1,stage_count))

    def status_view(c,row,check=True):
        good=valid(c,row) if check else False
        completed=c.execute("""SELECT COUNT(*) FROM mystery_progress
           WHERE trail_id=? AND revision=? AND completed_at IS NOT NULL""",
           (row["id"],row["revision"])).fetchone()[0] if good else 0
        return {"id":row["id"],"title":row["title"] if good else "公开来源已不可用",
                "premise":row["premise"] if good else "",
                "curator":row["curator"],"stages":len(stages(c,row["id"])),
                "status":row["status"],"available":good,
                "completions":completed}

    def stable_options(c, stage_id):
        current=choices(c,stage_id)
        ordered=sorted(current,key=lambda r:hashlib.sha256(
            f"{stage_id}:{r['exhibit_id']}".encode()).hexdigest())
        cards=[]
        for r in ordered:
            src=live(c,r["exhibit_id"])
            if not src:
                return None
            cards.append(exhibit_card(src))
        return cards

    def progress(c,row,user,create=False):
        p=c.execute("""SELECT * FROM mystery_progress WHERE trail_id=? AND user_id=?""",
                    (row["id"],user["id"])).fetchone()
        if p is not None and p["revision"]==row["revision"]:
            return dict(p)
        if not create:
            return {"trail_id":row["id"],"user_id":user["id"],
                    "revision":row["revision"],"solved":0,"wrong":0,
                    "stage_wrong":0,"completed_at":None}
        c.execute("""INSERT INTO mystery_progress
          (trail_id,user_id,revision,solved,wrong,stage_wrong,completed_at,updated_at)
          VALUES(?,?,?,0,0,0,NULL,?)
          ON CONFLICT(trail_id,user_id) DO UPDATE SET
           revision=excluded.revision,solved=0,wrong=0,stage_wrong=0,
           completed_at=NULL,updated_at=excluded.updated_at""",
          (row["id"],user["id"],row["revision"],now()))
        return progress(c,row,user)

    def open_play(c,row,user):
        all_stages=stages(c,row["id"])
        p=progress(c,row,user)
        total=len(all_stages)
        base={"id":row["id"],"title":row["title"],"premise":row["premise"],
              "curator":row["curator"],"total":total,"solved":p["solved"],
              "wrong":p["wrong"],"completed":p["solved"]>=total}
        if p["solved"]>=total:
            revealed=[]
            for s in all_stages:
                original=live(c,s["answer_exhibit_id"])
                if original is None:
                    fail(409,"原始藏品暂不可用")
                revealed.append({"clue":s["clue"],"exhibit":exhibit_card(original)})
            return {**base,"stage":None,"stars":score(p["wrong"],total),
                    "route":revealed}
        s=all_stages[p["solved"]]
        ordered=stable_options(c,s["id"])
        if ordered is None:
            fail(409,"此关所需的公开藏品已不可用")
        return {**base,"stars":None,"route":None,
                "stage":{"index":p["solved"]+1,"clue":s["clue"],
                    "hint":s["hint"] if p["stage_wrong"]>0 else None,
                    "wrong_on_stage":p["stage_wrong"],
                    "options":ordered}}

    def ensure_playable(c,trail_id):
        row=trail(c,trail_id)
        if not row or not valid(c,row):
            fail(404,"谜案尚未发布或原始公开藏品已不可用")
        return row

    def draft_revision(c,trail_id):
        c.execute("""UPDATE mystery_trails SET status='draft',revision=revision+1,
            updated_at=? WHERE id=?""",(now(),trail_id))

    @app.get("/api/mysteries")
    def gallery():
        with db() as c:
            rows=c.execute("""SELECT m.*,u.username AS curator FROM mystery_trails m
              JOIN users u ON u.id=m.owner_id WHERE m.status='published'
              ORDER BY m.id DESC LIMIT 80""").fetchall()
            return {"items":[status_view(c,r) for r in rows if valid(c,r)][:40],
                    "notice":"所有谜题选项来自目前真实公开的藏品。路线由真实馆长编写，线索和解释没有经过平台事实核验。"}

    @app.get("/api/mysteries/random")
    def random_mystery():
        with db() as c:
            rows=c.execute("""SELECT m.*,u.username AS curator FROM mystery_trails m
              JOIN users u ON u.id=m.owner_id WHERE m.status='published'
              ORDER BY RANDOM() LIMIT 30""").fetchall()
            for row in rows:
                if valid(c,row):
                    return status_view(c,row)
            return {"trail":None,"notice":"目前没有可用的真实公开谜案，不会制造虚假的推荐。"}

    @app.get("/api/mysteries/sources")
    def search_sources(q:str=""):
        keyword=q.strip()[:60]
        with db() as c:
            where=PUBLIC_SCOPE
            args=[]
            if keyword:
                where+=" AND (e.title LIKE ? OR e.category LIKE ? OR e.tags LIKE ?)"
                args.extend(["%"+keyword+"%"]*3)
            rows=c.execute("""SELECT e.id,e.user_id,e.title,e.domain,e.category,
                 e.time_bucket,e.image_url,u.username AS curator
                 FROM exhibits e JOIN users u ON u.id=e.user_id
                 WHERE """+where+" ORDER BY e.id DESC LIMIT 24",args).fetchall()
            return {"items":[exhibit_card(x) for x in rows],
                    "notice":"仅检索仍然公开的真实藏品；这些选项由作者主动筛选成谜题，没有系统伪造的其他用户。"}

    @app.get("/api/mysteries/mine")
    def my_mysteries(user=Depends(require_user)):
        with db() as c:
            rows=c.execute("""SELECT m.*,u.username AS curator FROM mystery_trails m
              JOIN users u ON u.id=m.owner_id WHERE m.owner_id=? ORDER BY m.id DESC
              LIMIT 30""",(user["id"],)).fetchall()
            result=[]
            for row in rows:
                parts=[]
                for stage in stages(c,row["id"]):
                    opts=[]
                    for o in choices(c,stage["id"]):
                        src=live(c,o["exhibit_id"])
                        opts.append({"exhibit":exhibit_card(src) if src else None,
                                     "available":bool(src),"is_answer":bool(o["is_answer"])})
                    parts.append({"id":stage["id"],"clue":stage["clue"],"hint":stage["hint"],
                        "options":opts})
                result.append({"id":row["id"],"title":row["title"],
                    "premise":row["premise"],"status":row["status"],
                    "revision":row["revision"],"available":valid(c,row),
                    "stages":parts})
            return {"items":result,"notice":"编辑或撤下任何关卡后会进入私密草稿，新版本需作者重新发布；玩家旧进度不会迁入新版本。"}

    @app.post("/api/mysteries",status_code=201)
    def create(payload:TrailIn,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            n=c.execute("SELECT COUNT(*) FROM mystery_trails WHERE owner_id=?",
                        (user["id"],)).fetchone()[0]
            if n>=MAX_TRAILS:fail(429,"每位馆长最多创建15条谜案路线")
            cur=c.execute("""INSERT INTO mystery_trails
              (owner_id,title,premise,created_at,updated_at)
              VALUES(?,?,?,?,?)""",(user["id"],payload.title,payload.premise,now(),now()))
            return {"id":cur.lastrowid,"status":"draft"}

    @app.put("/api/mysteries/{trail_id}")
    def edit(trail_id:int,payload:TrailIn,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            owned(c,trail_id,user)
            c.execute("UPDATE mystery_trails SET title=?,premise=? WHERE id=?",
                      (payload.title,payload.premise,trail_id))
            draft_revision(c,trail_id)
            return {"ok":True,"notice":"已保存新私密草稿；重新发布前不会出现在公开谜案馆。"}

    @app.post("/api/mysteries/{trail_id}/stages",status_code=201)
    def add_stage(trail_id:int,payload:StageIn,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            owned(c,trail_id,user)
            s=stages(c,trail_id)
            if len(s)>=MAX_STAGES:
                fail(429,"一条谜案路线最多六关")
            ids=[payload.answer_exhibit_id,*payload.distractor_ids]
            if any(live(c,i) is None for i in ids):
                fail(404,"所有候选选项都必须是当下真正公开的原始藏品")
            existing={r["answer_exhibit_id"] for r in s}
            if payload.answer_exhibit_id in existing:
                fail(409,"不同关卡需要使用不同的答案藏品")
            cur=c.execute("""INSERT INTO mystery_stages(
                trail_id,clue,hint,answer_exhibit_id,created_at)
                VALUES(?,?,?,?,?)""",
                (trail_id,payload.clue,payload.hint,payload.answer_exhibit_id,now()))
            for e in ids:
                c.execute("""INSERT INTO mystery_choices(stage_id,exhibit_id,is_answer)
                  VALUES(?,?,?)""",(cur.lastrowid,e,int(e==payload.answer_exhibit_id)))
            draft_revision(c,trail_id)
            return {"id":cur.lastrowid,"stage_count":len(s)+1,
                    "notice":"新关卡已存入私密草稿，公开前仍需重新发布。"}

    @app.delete("/api/mysteries/{trail_id}/stages/{stage_id}")
    def remove_stage(trail_id:int,stage_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            owned(c,trail_id,user)
            deleted=c.execute("DELETE FROM mystery_stages WHERE id=? AND trail_id=?",
                              (stage_id,trail_id))
            if deleted.rowcount!=1:
                fail(404,"没有这一个关卡")
            draft_revision(c,trail_id)
            return {"ok":True}

    @app.post("/api/mysteries/{trail_id}/publish")
    def publish(trail_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=owned(c,trail_id,user)
            group=stages(c,trail_id)
            if not MIN_STAGES<=len(group)<=MAX_STAGES:
                fail(409,"必须至少添加两关且最多六关才能公开")
            for stage in group:
                opts=choices(c,stage["id"])
                if len(opts)<3 or len(opts)>MAX_CHOICES or sum(x["is_answer"] for x in opts)!=1:
                    fail(409,"每关必须包含一个答案及两到三个不同公开藏品选项")
                if not stage["answer_exhibit_id"] or any(live(c,x["exhibit_id"]) is None for x in opts):
                    fail(409,"有来源已撤回公开，不能发布；请重设该关")
            c.execute("""UPDATE mystery_trails SET status='published',updated_at=?
                 WHERE id=?""",(now(),trail_id))
            return {"ok":True,"notice":"所有选项均通过实时公开权限核验，已正式公开谜案。"}

    @app.post("/api/mysteries/{trail_id}/unpublish")
    def unpublish(trail_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            owned(c,trail_id,user)
            draft_revision(c,trail_id)
            return {"ok":True,"notice":"谜案已下架，新版本进度将重新开始。"}

    @app.delete("/api/mysteries/{trail_id}")
    def delete_trail(trail_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            owned(c,trail_id,user)
            c.execute("DELETE FROM mystery_trails WHERE id=?",(trail_id,))
            return {"ok":True}

    @app.get("/api/mysteries/{trail_id}")
    def preview(trail_id:int,user=Depends(maybe_user)):
        with db() as c:
            row=trail(c,trail_id)
            if not row:
                fail(404,"谜案不存在")
            if not valid(c,row):
                if not user or row["owner_id"]!=user["id"]:
                    fail(404,"谜案尚未公开或源作品已撤回")
                return {"id":row["id"],"title":row["title"],
                    "premise":row["premise"],"curator":row["curator"],
                    "stages":len(stages(c,trail_id)),"available":False,
                    "status":row["status"]}
            return status_view(c,row)

    @app.get("/api/mysteries/{trail_id}/play")
    def play(trail_id:int,user=Depends(require_user)):
        with db() as c:
            row=ensure_playable(c,trail_id)
            return open_play(c,row,user)

    @app.post("/api/mysteries/{trail_id}/guess")
    def guess(trail_id:int,payload:GuessIn,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=ensure_playable(c,trail_id)
            p=progress(c,row,user,True)
            all_stages=stages(c,trail_id)
            if p["solved"]>=len(all_stages):
                fail(409,"你已经完成这条谜案；可选择重新开始")
            stage=all_stages[p["solved"]]
            available=choices(c,stage["id"])
            candidate={r["exhibit_id"]:bool(r["is_answer"]) for r in available}
            if payload.exhibit_id not in candidate:
                fail(400,"请选择当前关卡真正列出的选项")
            if candidate[payload.exhibit_id]:
                next_count=p["solved"]+1
                completed=next_count==len(all_stages)
                c.execute("""UPDATE mystery_progress
                   SET solved=?,stage_wrong=0,completed_at=?,updated_at=?
                   WHERE trail_id=? AND user_id=?""",
                   (next_count,now() if completed else None,now(),trail_id,user["id"]))
                src=live(c,payload.exhibit_id)
                return {"correct":True,"completed":completed,"solved":next_count,
                    "total":len(all_stages),"revealed":exhibit_card(src),
                    "stars":score(p["wrong"],len(all_stages)) if completed else None,
                    "notice":"谜案线索由馆长设计，正确答案只意味着符合此关的预设选项，并非真实知识认证。"}
            c.execute("""UPDATE mystery_progress
                SET wrong=wrong+1,stage_wrong=stage_wrong+1,updated_at=?
                WHERE trail_id=? AND user_id=?""",(now(),trail_id,user["id"]))
            return {"correct":False,"completed":False,
                "solved":p["solved"],"total":len(all_stages),
                "hint":stage["hint"],"wrong_on_stage":p["stage_wrong"]+1,
                "notice":"线索不匹配，查看馆长提供的提示后再试一次。"}

    @app.post("/api/mysteries/{trail_id}/restart")
    def restart(trail_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=ensure_playable(c,trail_id)
            c.execute("""DELETE FROM mystery_progress WHERE trail_id=? AND user_id=?""",
                      (trail_id,user["id"]))
            return {"ok":True,"notice":"你已自行重置这条谜案的私人进度。"}
