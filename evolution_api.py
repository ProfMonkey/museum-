"""V18 civilization evolution: bounded, deterministic, creator-controlled fictional timelines.

No background tasks, currency, real-world history or edits to another user's lore.
All state changes are opt-in and every year is an immutable SQLite snapshot.
"""
from __future__ import annotations

import json
from hashlib import sha256
from typing import Literal

from fastapi import Depends, Query
from pydantic import BaseModel, Field, field_validator

NOTICE = "【纯虚构文明推演】人口、天象与文明史均为创作模拟，非真实数据或历史预测。"
POLICIES = {
    "开垦": {"food": 12, "ecology": -4, "energy": -2, "stability": 1},
    "求知": {"knowledge": 10, "energy": -8, "food": -3, "culture": 2},
    "守护": {"ecology": 10, "stability": 5, "food": -3, "knowledge": -1},
    "通商": {"food": 4, "knowledge": 4, "culture": 7, "energy": -4, "stability": -2},
}
INITIAL = {"population": 12000, "food": 65, "knowledge": 28, "ecology": 75,
           "stability": 70, "culture": 40, "energy": 50}
EVENTS = (
    ("虚构的丰收季", {"food": 8, "culture": 1}, "丰收传说令谷仓重新充盈。"),
    ("天工学派诞生", {"knowledge": 7, "energy": -3}, "新学派以奇特的方式重写了器物图谱。"),
    ("古老航道重现", {"culture": 5, "food": 2}, "远方来客带来了未经证实的异域传说。"),
    ("灵潮逆转", {"energy": 8, "ecology": -4}, "奇异灵潮照亮天幕，也改变了大地的脉动。"),
    ("边境纷争", {"stability": -9, "food": -4}, "边境起了争执，文明不得不重新分配资源。"),
    ("青空异象", {"culture": 4, "stability": -3}, "史官把一场异象记入了尚未完成的编年史。"),
)


class NewTimeline(BaseModel):
    civilization_id: int = Field(ge=1)
    name: str = Field(min_length=2, max_length=60)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("纪元名称至少两个字")
        return value


class Advance(BaseModel):
    policy: Literal["开垦", "求知", "守护", "通商"]
    relation_id: int | None = Field(default=None, ge=1)


class Fork(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    year: int = Field(ge=0, le=100)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        return NewTimeline.clean_name(value)


class Visibility(BaseModel):
    visibility: Literal["private", "public"]


def bounded(value):
    return max(0, min(100, int(value)))


def evolve(old, policy, law, timeline_id, year, influence=None):
    """Pure function: identical snapshot, policy, law, identity and year => identical year."""
    value = dict(old)
    for key, delta in POLICIES[policy].items():
        value[key] += delta
    # Resource upkeep prevents endless cost-free growth.
    value["food"] -= 4
    value["energy"] -= 2
    value["ecology"] += 1
    value["culture"] += 1
    # The first law remains immutable; only simulated costs vary.
    if law == "灵气必须守恒" and policy == "求知":
        value["ecology"] -= 3
    elif law == "记忆可以抵押" and policy == "求知":
        value["culture"] -= 4
    elif law == "因果可被倒写" and policy == "通商":
        value["stability"] -= 3
    elif law == "万物皆能修行" and policy == "守护":
        value["knowledge"] += 2
    elif law == "名字蕴藏真形" and policy == "通商":
        value["culture"] += 2
    elif law == "时间由梦供养" and policy == "求知":
        value["stability"] -= 2

    digest = sha256(f"{timeline_id}|{year}|{law}|{policy}".encode()).digest()
    event = None
    if digest[1] % 3 == 0:
        label, changes, description = EVENTS[digest[0] % len(EVENTS)]
        for key, delta in changes.items():
            value[key] += delta
        event = {"name": label, "description": description}
    # Only an explicitly selected, accepted relation adds a bounded fictional effect.
    if influence:
        for key,delta in influence.items():
            value[key] += delta
    for key in INITIAL:
        if key != "population":
            value[key] = bounded(value[key])
    growth = ((value["food"] - 45) * .0008 + (value["stability"] - 45) * .0004)
    growth = min(.035, max(-.04, growth))
    value["population"] = max(100, min(10000000, int(old["population"] * (1 + growth))))
    return value, event


def mount_evolution(app, db, require_user, maybe_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS fantasy_evolution_timelines(
          id INTEGER PRIMARY KEY,
          civilization_id INTEGER NOT NULL REFERENCES fantasy_civilizations(id) ON DELETE CASCADE,
          owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          name TEXT NOT NULL,
          visibility TEXT NOT NULL DEFAULT 'private' CHECK(visibility IN ('private','public')),
          parent_timeline_id INTEGER REFERENCES fantasy_evolution_timelines(id) ON DELETE SET NULL,
          forked_from_year INTEGER,
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_evolution_civ ON fantasy_evolution_timelines(civilization_id,id DESC);
        CREATE TABLE IF NOT EXISTS fantasy_evolution_years(
          id INTEGER PRIMARY KEY,
          timeline_id INTEGER NOT NULL REFERENCES fantasy_evolution_timelines(id) ON DELETE CASCADE,
          year INTEGER NOT NULL CHECK(year BETWEEN 0 AND 100),
          policy TEXT NOT NULL,
          state_json TEXT NOT NULL,
          event_name TEXT,
          event_text TEXT,
          created_at TEXT NOT NULL,
          UNIQUE(timeline_id,year)
        );
        CREATE INDEX IF NOT EXISTS ix_evolution_year ON fantasy_evolution_years(timeline_id,year);
        """)
        # Upgrade pre-existing V18 archives safely without resetting their history.
        columns={row["name"] for row in c.execute("PRAGMA table_info(fantasy_evolution_years)")}
        if "influence_kind" not in columns:
            c.execute("ALTER TABLE fantasy_evolution_years ADD COLUMN influence_kind TEXT")

    def civilization(c, civilization_id):
        return c.execute("""SELECT cv.id,cv.world_id,cv.user_id,cv.name,cv.style,
            cv.visibility civilization_visibility,w.name world_name,w.theme,w.law,
            w.visibility world_visibility,u.username creator
            FROM fantasy_civilizations cv JOIN fantasy_worlds w ON w.id=cv.world_id
            JOIN users u ON u.id=cv.user_id WHERE cv.id=?""",(civilization_id,)).fetchone()

    def accessible(c, civilization_id, user, owner_only=False):
        cv = civilization(c, civilization_id)
        if not cv:
            fail(404,"文明不存在")
        owner = bool(user and user["id"] == cv["user_id"])
        public = cv["civilization_visibility"] == "public" and cv["world_visibility"] == "public"
        if (owner_only and not owner) or (not owner and not public):
            fail(404,"文明不存在或尚未公开")
        return cv, owner, public

    def timeline(c, timeline_id, user, owner_only=False):
        item = c.execute("SELECT * FROM fantasy_evolution_timelines WHERE id=?",(timeline_id,)).fetchone()
        if not item:
            fail(404,"纪元不存在")
        cv, owner, public = accessible(c,item["civilization_id"],user,owner_only)
        if not owner and (not public or item["visibility"] != "public"):
            fail(404,"纪元不存在或尚未公开")
        if owner_only and (not owner or item["owner_id"] != user["id"]):
            fail(404,"不能修改其他馆长的纪元")
        return item, cv, owner, public

    def read_years(c, timeline_id):
        rows = c.execute("""SELECT year,policy,state_json,event_name,event_text,influence_kind,created_at
            FROM fantasy_evolution_years WHERE timeline_id=? ORDER BY year ASC LIMIT 101""",
            (timeline_id,)).fetchall()
        return [{"year":row["year"],"policy":row["policy"],
                 "stats":json.loads(row["state_json"]),
                 "event":({"name":row["event_name"],"description":row["event_text"]}
                          if row["event_name"] else None),
                 "influence":row["influence_kind"],"created_at":row["created_at"]} for row in rows]

    def timeline_card(item, cv, owner, years=None):
        data = {"id":item["id"],"civilization_id":item["civilization_id"],"name":item["name"],
                "visibility":item["visibility"],"parent_timeline_id":item["parent_timeline_id"],
                "forked_from_year":item["forked_from_year"],"created_at":item["created_at"],
                "civilization":cv["name"],"world":cv["world_name"],"law":cv["law"],
                "creator":cv["creator"],"is_owner":owner,"fictional":True,"notice":NOTICE}
        if years is not None:
            data["years"] = years
            data["current"] = years[-1] if years else None
        return data

    def limit(c, civilization_id):
        if c.execute("SELECT COUNT(*) FROM fantasy_evolution_timelines WHERE civilization_id=?",
                     (civilization_id,)).fetchone()[0] >= 3:
            fail(429,"每个文明最多有三条命运支线")

    def add_year(c, tid, year, policy, state, event, influence_kind=None):
        c.execute("""INSERT INTO fantasy_evolution_years
            (timeline_id,year,policy,state_json,event_name,event_text,created_at,influence_kind)
            VALUES(?,?,?,?,?,?,?,?)""",(tid,year,policy,json.dumps(state,ensure_ascii=False,sort_keys=True),
                        event["name"] if event else None,
                        event["description"] if event else None,now(),influence_kind))

    @app.get("/api/fantasy/evolution/config")
    def config():
        return {"policies":[{"name":name,"effects":delta} for name,delta in POLICIES.items()],
                "initial":INITIAL,"max_year":100,"max_timelines":3,"notice":NOTICE}

    @app.get("/api/fantasy/evolution/civilizations")
    def list_civilizations(scope:Literal["mine","public"]="mine",user=Depends(maybe_user)):
        if scope=="mine" and not user:
            fail(401,"请先登录")
        with db() as c:
            if scope=="mine":
                rows=c.execute("""SELECT cv.id,cv.name,cv.style,w.name world_name,
                    w.law,w.visibility world_visibility,cv.visibility civilization_visibility
                    FROM fantasy_civilizations cv JOIN fantasy_worlds w ON w.id=cv.world_id
                    WHERE cv.user_id=? ORDER BY cv.id DESC LIMIT 180""",(user["id"],)).fetchall()
            else:
                rows=c.execute("""SELECT cv.id,cv.name,cv.style,w.name world_name,
                    w.law,w.visibility world_visibility,cv.visibility civilization_visibility
                    FROM fantasy_civilizations cv JOIN fantasy_worlds w ON w.id=cv.world_id
                    WHERE cv.visibility='public' AND w.visibility='public'
                    ORDER BY cv.id DESC LIMIT 180""").fetchall()
        return {"items":[dict(row) for row in rows],"fictional":True}

    @app.get("/api/fantasy/evolution/timelines")
    def list_timelines(civilization_id:int=Query(ge=1),user=Depends(maybe_user)):
        with db() as c:
            cv,owner,public=accessible(c,civilization_id,user)
            if owner:
                rows=c.execute("""SELECT * FROM fantasy_evolution_timelines WHERE civilization_id=?
                    ORDER BY id DESC LIMIT 3""",(civilization_id,)).fetchall()
            else:
                rows=c.execute("""SELECT * FROM fantasy_evolution_timelines WHERE civilization_id=?
                    AND visibility='public' ORDER BY id DESC LIMIT 3""",(civilization_id,)).fetchall()
            return {"items":[timeline_card(x,cv,owner) for x in rows],"fictional":True}

    @app.post("/api/fantasy/evolution/timelines",status_code=201)
    def create_timeline(draft:NewTimeline,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            cv,_,_=accessible(c,draft.civilization_id,user,True)
            limit(c,cv["id"])
            cur=c.execute("""INSERT INTO fantasy_evolution_timelines
                (civilization_id,owner_id,name,created_at) VALUES(?,?,?,?)""",
                (cv["id"],user["id"],draft.name,now()))
            add_year(c,cur.lastrowid,0,"起源",INITIAL,{"name":"文明初生","description":
                     f"「{cv['name']}」诞生于原创架空世界「{cv['world_name']}」，开启虚构纪元。"})
            return {"id":cur.lastrowid,"visibility":"private","fictional":True}

    @app.get("/api/fantasy/evolution/timelines/{timeline_id}")
    def get_timeline(timeline_id:int,user=Depends(maybe_user)):
        with db() as c:
            item,cv,owner,_=timeline(c,timeline_id,user)
            return timeline_card(item,cv,owner,read_years(c,timeline_id))

    @app.post("/api/fantasy/evolution/timelines/{timeline_id}/advance",status_code=201)
    def advance(timeline_id:int,draft:Advance,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            item,cv,_,_=timeline(c,timeline_id,user,True)
            previous=c.execute("""SELECT year,state_json FROM fantasy_evolution_years
                WHERE timeline_id=? ORDER BY year DESC LIMIT 1""",(item["id"],)).fetchone()
            if not previous or previous["year"] >= 100:
                fail(409,"该纪元已到达一百年上限")
            year=previous["year"]+1
            influence_kind=None
            influence_effect=None
            if draft.relation_id is not None:
                from relations_api import KINDS
                # Only the current owner may apply a tie to their own future year.
                relation=c.execute("""SELECT r.*,a.visibility a_visible,b.visibility b_visible,
                    wa.visibility a_world,wb.visibility b_world
                    FROM fantasy_civilization_relations r
                    JOIN fantasy_civilizations a ON a.id=r.source_id
                    JOIN fantasy_civilizations b ON b.id=r.target_id
                    JOIN fantasy_worlds wa ON wa.id=a.world_id
                    JOIN fantasy_worlds wb ON wb.id=b.world_id
                    WHERE r.id=?""",(draft.relation_id,)).fetchone()
                if not relation or relation["status"]!="accepted" or \
                   cv["id"] not in (relation["source_id"],relation["target_id"]) or \
                   any(relation[k]!="public" for k in ("a_visible","b_visible","a_world","b_world")):
                    fail(409,"该文明关系无效、已撤回或未获双方公开同意")
                influence_kind=relation["kind"]
                influence_effect=KINDS[influence_kind]
            state,event=evolve(json.loads(previous["state_json"]),draft.policy,cv["law"],timeline_id,year,influence_effect)
            add_year(c,timeline_id,year,draft.policy,state,event,influence_kind)
            return {"year":year,"stats":state,"policy":draft.policy,"event":event,"influence":influence_kind,
                    "fictional":True,"notice":NOTICE}

    @app.post("/api/fantasy/evolution/timelines/{timeline_id}/fork",status_code=201)
    def fork_timeline(timeline_id:int,draft:Fork,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            item,cv,_,_=timeline(c,timeline_id,user,True)
            limit(c,cv["id"])
            chosen=c.execute("""SELECT state_json FROM fantasy_evolution_years
                WHERE timeline_id=? AND year=?""",(timeline_id,draft.year)).fetchone()
            if not chosen:
                fail(422,"只能从已发生的纪年创建分支")
            cur=c.execute("""INSERT INTO fantasy_evolution_timelines
                (civilization_id,owner_id,name,parent_timeline_id,forked_from_year,created_at)
                VALUES(?,?,?,?,?,?)""",(cv["id"],user["id"],draft.name,timeline_id,draft.year,now()))
            add_year(c,cur.lastrowid,draft.year,"分支",json.loads(chosen["state_json"]),
                     {"name":"命运分岔","description":f"从第 {draft.year} 年另开一条虚构历史；原有年历不被修改。"})
            return {"id":cur.lastrowid,"forked_from_year":draft.year,
                    "visibility":"private","fictional":True}

    @app.patch("/api/fantasy/evolution/timelines/{timeline_id}/visibility")
    def set_visibility(timeline_id:int,draft:Visibility,user=Depends(require_user)):
        with db() as c:
            item,cv,_,public=timeline(c,timeline_id,user,True)
            if draft.visibility=="public" and not public:
                fail(409,"需先公开所属世界和文明，才能公开这条虚构年历")
            c.execute("UPDATE fantasy_evolution_timelines SET visibility=? WHERE id=?",
                      (draft.visibility,item["id"]))
            return {"visibility":draft.visibility,"fictional":True}

    @app.delete("/api/fantasy/evolution/timelines/{timeline_id}")
    def delete_timeline(timeline_id:int,user=Depends(require_user)):
        with db() as c:
            item,_,_,_=timeline(c,timeline_id,user,True)
            c.execute("DELETE FROM fantasy_evolution_timelines WHERE id=?",(item["id"],))
            return {"ok":True}
