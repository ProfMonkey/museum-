"""V24 万物转盘: private curated decision wheels grounded in real museum exhibits.

No fake community content, gambling, paid draws or manufactured outcomes.
Results use the server's secrets.randbelow for a uniform random selection.
Public exhibit references are resolved live: hidden/deleted sources cannot be drawn,
and their former titles are never leaked through saved wheels or draw history.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Literal
from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TOPICS={"food":"🍜 今天吃什么","travel":"🧭 去哪里玩","watch":"🎬 今天看什么",
        "activity":"🎲 现在做什么","custom":"✦ 万物由你决定"}
THEMES={"amber","nebula","mint","rose"}
MAX_WHEELS=12
MAX_ITEMS=24
MAX_HISTORY=20


class WheelDraft(BaseModel):
    model_config=ConfigDict(extra="forbid")
    title: str=Field(min_length=2,max_length=60)
    topic: Literal["food","travel","watch","activity","custom"]="custom"
    theme: Literal["amber","nebula","mint","rose"]="amber"
    no_repeat: bool=True

    @field_validator("title")
    @classmethod
    def cleaned(cls,value):
        value=value.strip()
        if len(value)<2:raise ValueError("转盘名称至少两个字")
        return value


class EntryDraft(BaseModel):
    model_config=ConfigDict(extra="forbid")
    kind: Literal["manual","exhibit"]="manual"
    label: str=Field(default="",max_length=75)
    exhibit_id: int|None=Field(default=None,ge=1)

    @model_validator(mode="after")
    def check(self):
        self.label=self.label.strip()
        if self.kind=="manual":
            if not 1<=len(self.label)<=75 or self.exhibit_id is not None:
                raise ValueError("手动选项需要 1–75 字名称，且不能附带藏品 ID")
        elif not self.exhibit_id or self.label:
            raise ValueError("馆藏选项必须仅填写公开藏品 ID")
        return self


class GuestSpin(BaseModel):
    model_config=ConfigDict(extra="forbid")
    options: list[str]=Field(min_length=2,max_length=MAX_ITEMS)
    last_index: int|None=Field(default=None,ge=0,le=MAX_ITEMS-1)
    no_repeat: bool=True

    @field_validator("options")
    @classmethod
    def validate_options(cls,values):
        result=[v.strip() for v in values]
        if any(not 1<=len(v)<=75 for v in result):
            raise ValueError("每一项须为 1–75 字")
        if len(set(v.casefold() for v in result))!=len(result):
            raise ValueError("同一个内容不能在转盘中重复出现")
        return result


def draw_index(size,last,no_repeat):
    candidates=list(range(size))
    if no_repeat and size>1 and last is not None and 0<=last<size:
        candidates.remove(last)
    return candidates[secrets.randbelow(len(candidates))],len(candidates)


def mount_wheels(app,db,require_user,maybe_user,now,fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS wonder_wheels(
          id INTEGER PRIMARY KEY,
          owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          title TEXT NOT NULL,topic TEXT NOT NULL,theme TEXT NOT NULL,
          no_repeat INTEGER NOT NULL DEFAULT 1 CHECK(no_repeat IN (0,1)),
          created_at TEXT NOT NULL,updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS wonder_wheel_items(
          id INTEGER PRIMARY KEY,
          wheel_id INTEGER NOT NULL REFERENCES wonder_wheels(id) ON DELETE CASCADE,
          kind TEXT NOT NULL CHECK(kind IN ('manual','exhibit')),
          label TEXT NOT NULL DEFAULT '',
          exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS wonder_wheel_draws(
          id INTEGER PRIMARY KEY,
          wheel_id INTEGER NOT NULL REFERENCES wonder_wheels(id) ON DELETE CASCADE,
          item_id INTEGER REFERENCES wonder_wheel_items(id) ON DELETE SET NULL,
          drawn_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_wheel_owner ON wonder_wheels(owner_id,id DESC);
        CREATE INDEX IF NOT EXISTS ix_wheel_items ON wonder_wheel_items(wheel_id,id);
        CREATE INDEX IF NOT EXISTS ix_wheel_draws ON wonder_wheel_draws(wheel_id,id DESC);
        """)

    def owner(c,userid,wheel_id):
        row=c.execute("SELECT * FROM wonder_wheels WHERE id=? AND owner_id=?",
                      (wheel_id,userid)).fetchone()
        if not row:fail(404,"没有找到你的转盘")
        return row

    def exhibit(c,exhibit_id):
        if not exhibit_id:return None
        return c.execute("""SELECT e.id,e.title,e.domain,e.category,e.visibility
            FROM exhibits e
            LEFT JOIN fantasy_relics fr ON fr.exhibit_id=e.id
            LEFT JOIN fantasy_worlds fw ON fw.id=fr.world_id
            WHERE e.id=? AND e.visibility='public'
              AND (fr.id IS NULL OR fw.visibility='public')""",
            (exhibit_id,)).fetchone()

    def entries(c,wheel_id):
        rows=c.execute("""SELECT * FROM wonder_wheel_items
                           WHERE wheel_id=? ORDER BY id""",(wheel_id,)).fetchall()
        good=[]
        invalid=0
        for row in rows:
            if row["kind"]=="manual":
                good.append({"id":row["id"],"kind":"manual",
                             "label":row["label"],"exhibit_id":None})
            else:
                e=exhibit(c,row["exhibit_id"])
                if e:
                    good.append({"id":row["id"],"kind":"exhibit",
                                 "label":e["title"],"exhibit_id":e["id"],
                                 "domain":e["domain"],"category":e["category"]})
                else:
                    invalid+=1
        return good,invalid

    def history(c,wheel_id,good):
        by_id={e["id"]:e for e in good}
        rows=c.execute("""SELECT id,item_id,drawn_at FROM wonder_wheel_draws
              WHERE wheel_id=? ORDER BY id DESC LIMIT ?""",
              (wheel_id,MAX_HISTORY)).fetchall()
        return [{"id":r["id"],"drawn_at":r["drawn_at"],
                 "label":by_id[r["item_id"]]["label"] if r["item_id"] in by_id else "已移除或撤回的选项",
                 "available":r["item_id"] in by_id,
                 "exhibit_id":by_id[r["item_id"]].get("exhibit_id") if r["item_id"] in by_id else None}
                for r in rows]

    def view(c,row,details=False):
        good,invalid=entries(c,row["id"])
        obj={"id":row["id"],"title":row["title"],"topic":row["topic"],
             "topic_label":TOPICS[row["topic"]],"theme":row["theme"],
             "no_repeat":bool(row["no_repeat"]),"count":len(good),
             "unavailable_count":invalid,"created_at":row["created_at"]}
        if details:
            obj["items"]=good
            obj["history"]=history(c,row["id"],good)
        return obj

    @app.get("/api/wheels/config")
    def config():
        return {"topics":[{"key":k,"label":v} for k,v in TOPICS.items()],
                "themes":sorted(THEMES),"max_wheels":MAX_WHEELS,"max_items":MAX_ITEMS,
                "notice":"公平随机抽取，非付费抽奖或博彩；转盘会等概率选择每个有效选项。关闭重复保护后，连续抽到同一项是正常的。"}

    @app.get("/api/wheels/sources")
    def sources(q:str=Query(default="",max_length=70)):
        pattern="%"+q.strip()+"%"
        with db() as c:
            rows=c.execute("""SELECT e.id FROM exhibits e
                LEFT JOIN fantasy_relics fr ON fr.exhibit_id=e.id
                LEFT JOIN fantasy_worlds fw ON fw.id=fr.world_id
                WHERE e.visibility='public' AND (fr.id IS NULL OR fw.visibility='public')
                  AND (e.title LIKE ? OR e.description LIKE ? OR e.category LIKE ? OR e.domain LIKE ? OR e.tags LIKE ?)
                ORDER BY e.id DESC LIMIT 30""",(pattern,pattern,pattern,pattern,pattern)).fetchall()
            return {"items":[{"id":e["id"],"title":e["title"],"domain":e["domain"],
                              "category":e["category"]} for x in rows
                              if (e:=exhibit(c,x["id"])) is not None]}

    @app.post("/api/wheels/preview")
    def preview(payload:GuestSpin):
        i,n=draw_index(len(payload.options),payload.last_index,payload.no_repeat)
        return {"index":i,"label":payload.options[i],"chance_denominator":n,
                "count":len(payload.options),
                "notice":"游客临时转盘不会写入服务器个人数据。"}

    @app.get("/api/wheels")
    def mine(user=Depends(require_user)):
        with db() as c:
            rows=c.execute("SELECT * FROM wonder_wheels WHERE owner_id=? ORDER BY id DESC",
                           (user["id"],)).fetchall()
            return {"items":[view(c,r) for r in rows]}

    @app.post("/api/wheels",status_code=201)
    def create(payload:WheelDraft,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            count=c.execute("SELECT COUNT(*) FROM wonder_wheels WHERE owner_id=?",
                            (user["id"],)).fetchone()[0]
            if count>=MAX_WHEELS:fail(429,"每人最多创建十二个万物转盘")
            cur=c.execute("""INSERT INTO wonder_wheels
                (owner_id,title,topic,theme,no_repeat,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?)""",
                (user["id"],payload.title,payload.topic,payload.theme,
                 int(payload.no_repeat),now(),now()))
            return {"id":cur.lastrowid}

    @app.get("/api/wheels/{wheel_id}")
    def detail(wheel_id:int,user=Depends(require_user)):
        with db() as c:
            return view(c,owner(c,user["id"],wheel_id),True)

    @app.patch("/api/wheels/{wheel_id}")
    def update(wheel_id:int,payload:WheelDraft,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            owner(c,user["id"],wheel_id)
            c.execute("""UPDATE wonder_wheels SET title=?,topic=?,theme=?,no_repeat=?,updated_at=?
                WHERE id=?""",(payload.title,payload.topic,payload.theme,
                               int(payload.no_repeat),now(),wheel_id))
            return {"ok":True}

    @app.delete("/api/wheels/{wheel_id}")
    def delete(wheel_id:int,user=Depends(require_user)):
        with db() as c:
            owner(c,user["id"],wheel_id)
            c.execute("DELETE FROM wonder_wheels WHERE id=?",(wheel_id,))
            return {"ok":True}

    @app.post("/api/wheels/{wheel_id}/items",status_code=201)
    def add_item(wheel_id:int,payload:EntryDraft,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            owner(c,user["id"],wheel_id)
            items=c.execute("""SELECT id,kind,label,exhibit_id FROM wonder_wheel_items
                WHERE wheel_id=?""",(wheel_id,)).fetchall()
            if len(items)>=MAX_ITEMS:fail(429,"一个转盘最多放入二十四个选项")
            if payload.kind=="exhibit" and not exhibit(c,payload.exhibit_id):
                fail(404,"只有当前公开的真实馆藏可以加入转盘")
            if payload.kind=="manual" and any(r["kind"]=="manual"
                and r["label"].casefold()==payload.label.casefold() for r in items):
                fail(409,"不能重复加入相同的自定义选项")
            if payload.kind=="exhibit" and any(r["kind"]=="exhibit"
                and r["exhibit_id"]==payload.exhibit_id for r in items):
                fail(409,"这件馆藏已经在当前转盘中")
            cur=c.execute("""INSERT INTO wonder_wheel_items(wheel_id,kind,label,exhibit_id,created_at)
                VALUES(?,?,?,?,?)""",(wheel_id,payload.kind,
                                        payload.label if payload.kind=="manual" else "",
                                        payload.exhibit_id,now()))
            return {"id":cur.lastrowid}

    @app.delete("/api/wheels/{wheel_id}/items/{item_id}")
    def remove_item(wheel_id:int,item_id:int,user=Depends(require_user)):
        with db() as c:
            owner(c,user["id"],wheel_id)
            result=c.execute("DELETE FROM wonder_wheel_items WHERE id=? AND wheel_id=?",
                             (item_id,wheel_id))
            if not result.rowcount:fail(404,"该选项不在当前转盘中")
            return {"ok":True}

    @app.post("/api/wheels/{wheel_id}/spin")
    def spin(wheel_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            wheel=owner(c,user["id"],wheel_id)
            good,invalid=entries(c,wheel_id)
            if len(good)<2:fail(409,"至少需要两个仍有效的选项才能转动转盘")
            recent=c.execute("""SELECT item_id FROM wonder_wheel_draws
                WHERE wheel_id=? ORDER BY id DESC LIMIT 1""",(wheel_id,)).fetchone()
            last_id=recent["item_id"] if recent else None
            # Remove invalidated prior picks from repeat suppression.
            last=next((i for i,x in enumerate(good) if x["id"]==last_id),None)
            idx,denom=draw_index(len(good),last,bool(wheel["no_repeat"]))
            winner=good[idx]
            cur=c.execute("""INSERT INTO wonder_wheel_draws(wheel_id,item_id,drawn_at)
                VALUES(?,?,?)""",(wheel_id,winner["id"],now()))
            # Keep actual history bounded, per wheel, without leaking withdrawn names.
            c.execute("""DELETE FROM wonder_wheel_draws WHERE wheel_id=? AND id NOT IN
                (SELECT id FROM wonder_wheel_draws WHERE wheel_id=? ORDER BY id DESC LIMIT ?)""",
                (wheel_id,wheel_id,MAX_HISTORY))
            return {"draw_id":cur.lastrowid,"winner":winner,"winner_index":idx,
                    "entry_count":len(good),"chance_denominator":denom,
                    "no_repeat":bool(wheel["no_repeat"]),"notice":"由服务器等概率随机选择，结果不是前端转盘动画预先决定的。"}
