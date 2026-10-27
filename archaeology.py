"""V37 · 万物文明考古局: archaeology is authored fictional interpretation.

A real curator may put a currently public museum exhibit into an OWN, currently
published V34 civilization as a symbolic archaeological relic. Three authored
clues unfold as a discoverable tale. The same original public exhibit can carry
conflicting roles in multiple independently authored fictional civilizations.

V35's validated civilization digest is reused; no copied real-source titles or
images. Changes to any upstream exhibit or the civilization never silently
restore public status: the author must revalidate AND re-publish. No AI news,
fabricated people or claims of scholarly archaeological certification.
"""
from __future__ import annotations

from typing import Literal
from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from parallel_universes import PUBLIC_SCOPE

ROLES = {
    "sacred": "神圣遗物",
    "tool": "文明工具",
    "warning": "灾厄警示",
    "currency": "交换信物",
    "memory": "历史记忆",
    "mystery": "未解之物",
}
MAX_PER_CIV = 12


class ArchaeologyIn(BaseModel):
    model_config=ConfigDict(extra="forbid")
    civilization_id: int=Field(ge=1)
    exhibit_id: int=Field(ge=1)
    era: int=Field(ge=1,le=8)
    role: Literal["sacred","tool","warning","currency","memory","mystery"]
    title: str=Field(min_length=3,max_length=90)
    introduction: str=Field(min_length=18,max_length=520)
    surface: str=Field(min_length=15,max_length=520)
    inscription: str=Field(min_length=20,max_length=720)
    interpretation: str=Field(min_length=30,max_length=1100)

    @model_validator(mode="after")
    def normalize(self):
        for key in ("title","introduction","surface","inscription","interpretation"):
            setattr(self,key,getattr(self,key).strip())
        if min(len(self.title),len(self.introduction),len(self.surface),
               len(self.inscription),len(self.interpretation))==0:
            raise ValueError("请完整写下原始物件在虚构文明中的三层考古叙事")
        if len(self.introduction)<18 or len(self.surface)<15 or len(self.inscription)<20 or len(self.interpretation)<30:
            raise ValueError("考古引子、表层痕迹、碑文与最终解释需要完整填写")
        return self


def mount_archaeology(app,db,require_user,maybe_user,now,fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS archaeology_relics(
          id INTEGER PRIMARY KEY,
          owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          civilization_id INTEGER NOT NULL REFERENCES civ_civilizations(id) ON DELETE CASCADE,
          exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
          civ_digest TEXT NOT NULL,
          exhibit_epoch INTEGER NOT NULL,
          era INTEGER NOT NULL CHECK(era BETWEEN 1 AND 8),
          role TEXT NOT NULL,
          title TEXT NOT NULL,
          introduction TEXT NOT NULL,
          surface TEXT NOT NULL,
          inscription TEXT NOT NULL,
          interpretation TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','public','closed')),
          revision INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          UNIQUE(civilization_id,exhibit_id)
        );
        CREATE INDEX IF NOT EXISTS ix_arch_public ON archaeology_relics(status,id DESC);
        CREATE INDEX IF NOT EXISTS ix_arch_exhibit ON archaeology_relics(exhibit_id,status,id DESC);
        CREATE INDEX IF NOT EXISTS ix_arch_owner ON archaeology_relics(owner_id,id DESC);
        CREATE TABLE IF NOT EXISTS archaeology_progress(
          relic_id INTEGER NOT NULL REFERENCES archaeology_relics(id) ON DELETE CASCADE,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          revision INTEGER NOT NULL,
          layer INTEGER NOT NULL DEFAULT 0 CHECK(layer BETWEEN 0 AND 3),
          updated_at TEXT NOT NULL,
          PRIMARY KEY(relic_id,user_id)
        );
        """)

    def civ(c,cid):
        return app.state.archaeology_civ_validator(c,cid)

    def source(c,eid):
        if not eid: return None
        return c.execute("""SELECT e.id,e.user_id,e.title,e.domain,e.category,
                 e.image_url,u.username AS curator,
                 COALESCE(v.epoch,0) AS epoch
             FROM exhibits e JOIN users u ON u.id=e.user_id
             LEFT JOIN embassy_exhibit_epochs v ON v.exhibit_id=e.id
             WHERE e.id=? AND """+PUBLIC_SCOPE,(eid,)).fetchone()

    def card(s):
        return {"id":s["id"],"title":s["title"],"domain":s["domain"],
                "category":s["category"],"image_url":s["image_url"],
                "curator":s["curator"]}

    def get(c,rid):
        return c.execute("""SELECT r.*,u.username AS archaeologist
                  FROM archaeology_relics r JOIN users u ON u.id=r.owner_id
                  WHERE r.id=?""",(rid,)).fetchone()

    def owner(c,rid,user):
        r=get(c,rid)
        if not r or r["owner_id"]!=user["id"]:
            fail(404,"只有该虚构考古解释的作者可以修改")
        return r

    def validated(c,r):
        if not r or r["status"]=="closed":return None
        civilization=civ(c,r["civilization_id"])
        artifact=source(c,r["exhibit_id"])
        if not civilization or not artifact:
            return None
        if civilization["owner_id"]!=r["owner_id"] or civilization["digest"]!=r["civ_digest"]:
            return None
        if artifact["epoch"]!=r["exhibit_epoch"]:
            return None
        actual=c.execute("SELECT COUNT(*) FROM civ_turns WHERE civ_id=?",
                         (r["civilization_id"],)).fetchone()[0]
        if r["era"]>actual:
            return None
        return civilization,artifact

    def live(c,r):
        return bool(r and r["status"]=="public" and validated(c,r))

    def progress(c,r,user):
        if not user:return 0
        row=c.execute("""SELECT layer FROM archaeology_progress
            WHERE relic_id=? AND user_id=? AND revision=?""",
            (r["id"],user["id"],r["revision"])).fetchone()
        return row["layer"] if row else 0

    def summary(c,r,user=None):
        pair=validated(c,r)
        if not pair:
            # The curator-authored text may quote private original titles.
            return {"id":r["id"],"available":False,"status":r["status"],
                    "title":"来源已撤回或文明历史改变","exhibit":None,"civilization":None}
        cv,artifact=pair
        return {"id":r["id"],"available":True,"status":r["status"],
                "title":r["title"],"introduction":r["introduction"],
                "role":r["role"],"role_label":ROLES[r["role"]],
                "era":r["era"],"civilization":{"id":cv["id"],"name":cv["name"]},
                "exhibit":card(artifact),"author":r["archaeologist"],
                "revision":r["revision"],"my_layer":progress(c,r,user),
                "notice":"由真实馆长独立创作的虚构文明解释，不代表原藏品作者认可，更不是历史考古研究结论。"}

    def private_detail(c,r,user):
        s=summary(c,r,user)
        if s["available"]:
            s["surface"]=r["surface"]
            s["inscription"]=r["inscription"]
            s["interpretation"]=r["interpretation"]
        return s

    def reset(c,rid):
        c.execute("""UPDATE archaeology_relics SET revision=revision+1,
                  status='draft',updated_at=? WHERE id=?""",(now(),rid))
        c.execute("DELETE FROM archaeology_progress WHERE relic_id=?",(rid,))

    def check_parent(c,cid,user):
        cv=civ(c,cid)
        if not cv or cv["owner_id"]!=user["id"]:
            fail(404,"只能以自己目前真正公开的 V34 文明撰写架空考古")
        return cv

    def check_source(c,eid):
        e=source(c,eid)
        if e is None:
            fail(404,"只能解释目前真正公开的原始博物馆藏品")
        return e

    @app.get("/api/archaeology/roles")
    def roles():
        return {"items":[{"id":k,"label":v} for k,v in ROLES.items()],
                "limits":{"per_civilization":MAX_PER_CIV,"layers":3},
                "notice":"分类是虚构文明对一件真实物件的不同解释，不是现实的考古学鉴定。"}

    @app.get("/api/archaeology/sources")
    def sources(q:str=""):
        kw=q.strip()[:60]
        with db() as c:
            clause=PUBLIC_SCOPE
            args=[]
            if kw:
                clause+=" AND (e.title LIKE ? OR e.category LIKE ? OR e.tags LIKE ?)"
                args=["%"+kw+"%"]*3
            rows=c.execute("""SELECT e.id,e.user_id,e.title,e.domain,e.category,
                     e.image_url,u.username AS curator,
                     COALESCE(v.epoch,0) AS epoch
                     FROM exhibits e JOIN users u ON u.id=e.user_id
                     LEFT JOIN embassy_exhibit_epochs v ON v.exhibit_id=e.id
                     WHERE """+clause+""" ORDER BY e.id DESC LIMIT 36""",args).fetchall()
            return {"items":[card(x) for x in rows]}

    @app.get("/api/archaeology/civilizations")
    def my_civilizations(user=Depends(require_user)):
        with db() as c:
            rows=c.execute("""SELECT id FROM civ_civilizations
                          WHERE owner_id=? AND status='public'
                          ORDER BY id DESC LIMIT 80""",(user["id"],)).fetchall()
            found=[v for x in rows if (v:=civ(c,x["id"])) is not None]
            return {"items":[{"id":v["id"],"name":v["name"],
                  "turn_count":v["turns"]} for v in found],
                  "notice":"只能向自己当前公开且上游来源有效的文明写入虚构考古解释。"}

    @app.get("/api/archaeology/public")
    def gallery():
        with db() as c:
            rows=c.execute("""SELECT r.*,u.username AS archaeologist
                 FROM archaeology_relics r JOIN users u ON u.id=r.owner_id
                 WHERE r.status='public' ORDER BY r.id DESC LIMIT 100""").fetchall()
            found=[]
            for r in rows:
                if live(c,r):
                    found.append(summary(c,r))
                if len(found)>=40:break
            return {"items":found,
                    "notice":"仅由真实作者主动公开且来源目前均有效的虚构考古叙事。"}

    @app.get("/api/archaeology/mine")
    def mine(user=Depends(require_user)):
        with db() as c:
            rows=c.execute("""SELECT r.*,u.username AS archaeologist
                 FROM archaeology_relics r JOIN users u ON u.id=r.owner_id
                 WHERE r.owner_id=? ORDER BY r.id DESC LIMIT 100""",(user["id"],)).fetchall()
            return {"items":[summary(c,r,user) for r in rows]}

    @app.get("/api/archaeology/exhibit/{exhibit_id}/echoes")
    def echoes(exhibit_id:int):
        with db() as c:
            e=check_source(c,exhibit_id)
            rows=c.execute("""SELECT r.*,u.username AS archaeologist
                   FROM archaeology_relics r JOIN users u ON u.id=r.owner_id
                   WHERE r.exhibit_id=? AND r.status='public'
                   ORDER BY r.id DESC LIMIT 90""",(exhibit_id,)).fetchall()
            result=[]
            for r in rows:
                if live(c,r):result.append(summary(c,r))
                if len(result)>=30:break
            return {"exhibit":card(e),"items":result,
                    "unique_roles":len({x["role"] for x in result}),
                    "notice":"同一件真实公开藏品在各个独立虚构文明中的多种解释；彼此并不证明对方的真实性。"}

    @app.post("/api/archaeology",status_code=201)
    def create(payload:ArchaeologyIn,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            cv=check_parent(c,payload.civilization_id,user)
            src=check_source(c,payload.exhibit_id)
            if payload.era>cv["turns"]:
                fail(422,"时代必须是该文明真实已写出的历史轮次")
            n=c.execute("SELECT COUNT(*) FROM archaeology_relics WHERE civilization_id=?",
                        (cv["id"],)).fetchone()[0]
            if n>=MAX_PER_CIV:
                fail(409,"一座文明最多为12件真实藏品编写考古解释")
            existing=c.execute("""SELECT 1 FROM archaeology_relics WHERE civilization_id=?
                             AND exhibit_id=?""",(cv["id"],src["id"])).fetchone()
            if existing:
                fail(409,"这件原始藏品在本文明中已有考古解释，可修改既有草稿")
            cur=c.execute("""INSERT INTO archaeology_relics
               (owner_id,civilization_id,exhibit_id,civ_digest,exhibit_epoch,
                era,role,title,introduction,surface,inscription,interpretation,
                created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (user["id"],cv["id"],src["id"],cv["digest"],src["epoch"],
                 payload.era,payload.role,payload.title,payload.introduction,
                 payload.surface,payload.inscription,payload.interpretation,
                 now(),now()))
            return {"id":cur.lastrowid,"status":"draft"}

    @app.get("/api/archaeology/{relic_id}")
    def detail(relic_id:int,user=Depends(maybe_user)):
        with db() as c:
            r=get(c,relic_id)
            if not r:
                fail(404,"没有这件虚构考古藏品")
            is_owner=bool(user and user["id"]==r["owner_id"])
            if not is_owner and not live(c,r):
                fail(404,"考古档案尚未公开或原始来源已失效")
            return private_detail(c,r,user) if is_owner else summary(c,r,user)

    @app.put("/api/archaeology/{relic_id}")
    def edit(relic_id:int,payload:ArchaeologyIn,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owner(c,relic_id,user)
            if r["status"]=="closed":fail(409,"已封存档案不能恢复")
            if payload.civilization_id!=r["civilization_id"] or payload.exhibit_id!=r["exhibit_id"]:
                fail(409,"已有档案只能修改叙事；更换原始文明与藏品需要创建另一档案")
            cv=check_parent(c,r["civilization_id"],user)
            src=check_source(c,r["exhibit_id"])
            if payload.era>cv["turns"]:
                fail(422,"请选择本文明确实已写下的时代")
            c.execute("""UPDATE archaeology_relics SET civ_digest=?,exhibit_epoch=?,
                 era=?,role=?,title=?,introduction=?,surface=?,inscription=?,interpretation=?
                 WHERE id=?""",
                 (cv["digest"],src["epoch"],payload.era,payload.role,
                  payload.title,payload.introduction,payload.surface,
                  payload.inscription,payload.interpretation,relic_id))
            reset(c,relic_id)
            return {"status":"draft","notice":"考古解释已修订，旧公开已撤销，游客挖掘进度因新版本而重置。"}

    @app.post("/api/archaeology/{relic_id}/rebase")
    def rebase(relic_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owner(c,relic_id,user)
            if r["status"]=="closed":fail(409,"已封存档案无法重新公开")
            cv=check_parent(c,r["civilization_id"],user)
            src=check_source(c,r["exhibit_id"])
            if r["era"]>cv["turns"]:
                fail(409,"新文明历史已没有该时代；请修改档案时代")
            c.execute("""UPDATE archaeology_relics SET civ_digest=?,exhibit_epoch=?
                       WHERE id=?""",(cv["digest"],src["epoch"],relic_id))
            reset(c,relic_id)
            return {"status":"draft","notice":"已重验文明与原展品的当前来源。必须由作者重新审阅并主动公开。"}

    @app.post("/api/archaeology/{relic_id}/publish")
    def publish(relic_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owner(c,relic_id,user)
            if not validated(c,r):
                fail(409,"原文明版本、原始藏品或引用时代已发生变化")
            c.execute("""UPDATE archaeology_relics SET status='public',updated_at=?
                        WHERE id=?""",(now(),relic_id))
            return {"status":"public","notice":"馆长自愿将原创架空解释公开。"}

    @app.post("/api/archaeology/{relic_id}/retract")
    def retract(relic_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owner(c,relic_id,user)
            if r["status"]=="closed":fail(409,"档案已封存")
            reset(c,relic_id)
            return {"status":"draft","notice":"已撤回公众阅读与旧版本的私人挖掘进度。"}

    @app.post("/api/archaeology/{relic_id}/close")
    def close(relic_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=owner(c,relic_id,user)
            if r["status"]=="closed":fail(409,"档案已封存")
            c.execute("""UPDATE archaeology_relics SET status='closed',
                        updated_at=? WHERE id=?""",(now(),relic_id))
            c.execute("DELETE FROM archaeology_progress WHERE relic_id=?",(relic_id,))
            return {"status":"closed","notice":"考古档案已封存；原始展品与 V34 文明完全保留。"}

    @app.get("/api/archaeology/{relic_id}/layer/{layer}")
    def layer(relic_id:int,layer:int,user=Depends(maybe_user)):
        if layer not in (1,2,3):
            fail(422,"只能打开三层现存档案")
        with db() as c:
            r=get(c,relic_id)
            if not r or not live(c,r):
                fail(404,"考古档案或来源已不再公开")
            # Progressive reveal is a game presentation, not a claim that public
            # text is cryptographically sealed. Guests can browse each layer
            # directly. Logged-in users progress sequentially server-side.
            previous=progress(c,r,user)
            if user and layer>previous+1:
                fail(409,"请按顺序发掘前一层考古线索")
            text_value=r[("surface","inscription","interpretation")[layer-1]]
            if user and layer>previous:
                c.execute("""INSERT INTO archaeology_progress(relic_id,user_id,revision,layer,updated_at)
                   VALUES(?,?,?,?,?) ON CONFLICT(relic_id,user_id) DO UPDATE SET
                   revision=excluded.revision,layer=excluded.layer,updated_at=excluded.updated_at""",
                   (r["id"],user["id"],r["revision"],layer,now()))
            return {"layer":layer,"title":("表层痕迹","深层碑文","馆长最终假说")[layer-1],
                    "content":text_value,
                    "my_layer":max(layer,previous) if user else layer,
                    "notice":"架空考古文本由真实馆长撰写，第三层不是现实考古学事实认证。"}
