"""V34 — 万物文明演化实验室: bounded, curator-authorized fictional history.

A V33 collision-world OWNER may create at most SIX fictional civilizations per
world. Visitors may run a read-only counterfactual by replacing ONE policy in a
recorded 2-8 turn timeline, then replaying unchanged later policies. Numbers are
explicitly a toy game model, never empirical claims or historical projections.

All public routes revalidate world publication, world revision, BOTH source
exhibits and the seed exhibit. Any revocation masks the full authored storyline.
"""
from __future__ import annotations

import json
from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator

from civilization_engine import (
    MODEL_VERSION, STAT_KEYS, STAT_NAMES, INITIAL, POLICIES, LAW_EFFECT, apply_turn,
)
from parallel_universes import PUBLIC_SCOPE

MAX_CIVS_PER_WORLD = 6
MAX_TURNS = 8
MIN_PUBLISH_TURNS = 2


class CivilizationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    world_id: int = Field(ge=1)
    seed_exhibit_id: int = Field(ge=1)
    name: str = Field(min_length=3, max_length=80)
    charter: str = Field(min_length=20, max_length=580)

    @model_validator(mode="after")
    def normalize(self):
        self.name = self.name.strip()
        self.charter = self.charter.strip()
        if len(self.name) < 3 or len(self.charter) < 20:
            raise ValueError("文明名称至少3字，文明宣言至少20字")
        return self


class TurnIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    policy: str = Field(min_length=3, max_length=40)
    chapter: str = Field(min_length=3, max_length=90)
    narrative: str = Field(min_length=12, max_length=620)

    @model_validator(mode="after")
    def normalize(self):
        self.chapter = self.chapter.strip()
        self.narrative = self.narrative.strip()
        if self.policy not in POLICIES:
            raise ValueError("必须使用已公开说明的文明决策规则")
        if len(self.chapter) < 3 or len(self.narrative) < 12:
            raise ValueError("篇章标题至少3字，原创故事至少12字")
        return self


def mount_civilization_lab(app, db, require_user, maybe_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS civ_civilizations(
          id INTEGER PRIMARY KEY,
          owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          world_id INTEGER NOT NULL REFERENCES collision_worlds(id) ON DELETE CASCADE,
          world_revision INTEGER NOT NULL,
          seed_exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
          name TEXT NOT NULL,
          charter TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','public')),
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_civ_world ON civ_civilizations(world_id,id);
        CREATE INDEX IF NOT EXISTS ix_civ_owner ON civ_civilizations(owner_id,id DESC);
        CREATE INDEX IF NOT EXISTS ix_civ_public ON civ_civilizations(status,id DESC);
        CREATE TABLE IF NOT EXISTS civ_turns(
          id INTEGER PRIMARY KEY,
          civ_id INTEGER NOT NULL REFERENCES civ_civilizations(id) ON DELETE CASCADE,
          turn_index INTEGER NOT NULL CHECK(turn_index BETWEEN 1 AND 8),
          policy TEXT NOT NULL,
          chapter TEXT NOT NULL,
          narrative TEXT NOT NULL,
          after_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          UNIQUE(civ_id,turn_index)
        );
        CREATE INDEX IF NOT EXISTS ix_civ_turns_order ON civ_turns(civ_id,turn_index);
        """)

    def source(c, exhibit_id):
        if not exhibit_id: return None
        return c.execute("""SELECT e.id,e.title,e.user_id,e.domain,e.category,
                        e.image_url,u.username AS curator
                        FROM exhibits e JOIN users u ON u.id=e.user_id
                        WHERE e.id=? AND """ + PUBLIC_SCOPE, (exhibit_id,)).fetchone()

    def card(r):
        return {"id":r["id"],"title":r["title"],"curator":r["curator"],
                "domain":r["domain"],"category":r["category"],
                "image_url":r["image_url"]}

    def world(c, world_id):
        return c.execute("""SELECT w.*,u.username AS author
            FROM collision_worlds w JOIN users u ON u.id=w.owner_id
            WHERE w.id=?""", (world_id,)).fetchone()

    def valid_world(c, w):
        if w is None or w["status"] != "public":
            return None
        a = source(c,w["left_id"])
        b = source(c,w["right_id"])
        if a is None or b is None or a["id"] == b["id"]:
            return None
        return a,b

    def get(c, civ_id):
        return c.execute("""SELECT v.*, u.username AS owner_name
            FROM civ_civilizations v JOIN users u ON u.id=v.owner_id
            WHERE v.id=?""", (civ_id,)).fetchone()

    def own(c, civ_id, user):
        v = get(c,civ_id)
        if v is None or v["owner_id"]!=user["id"]:
            fail(404,"只能管理你自己创造的文明")
        return v

    def source_status(c, civ):
        w = world(c,civ["world_id"])
        both = valid_world(c,w)
        if w is None or both is None or w["revision"] != civ["world_revision"]:
            return None
        seed = source(c,civ["seed_exhibit_id"])
        if seed is None or seed["id"] not in (both[0]["id"],both[1]["id"]):
            return None
        return w, both, seed

    def events(c,civ_id):
        return c.execute("""SELECT * FROM civ_turns WHERE civ_id=? ORDER BY turn_index""",
                         (civ_id,)).fetchall()

    def state_from(turns):
        return json.loads(turns[-1]["after_json"]) if turns else dict(INITIAL)

    def turn_view(c, row, world_law, before):
        rule = apply_turn(before,row["policy"],world_law)
        # The rules are immutable under model_version 1; preserve recorded values
        # and make deterministic deltas auditable by every visitor.
        after = json.loads(row["after_json"])
        if rule["after"] != after:
            fail(409,"历史年轮的模型版本与当前规则不一致，已阻止展示不可信数值")
        return {"turn":row["turn_index"],"policy":row["policy"],
                "policy_label":rule["policy_label"],"chapter":row["chapter"],
                "narrative":row["narrative"],"event":rule["event"],
                "mood":rule["mood"],"before":rule["before"],
                "after":rule["after"],"delta":rule["delta"],
                "modifier":rule["modifier"],"created_at":row["created_at"]}

    def trace(c,civ,law):
        rows=events(c,civ["id"])
        before=dict(INITIAL)
        result=[]
        for row in rows:
            record=turn_view(c,row,law,before)
            result.append(record)
            before=record["after"]
        return result

    def list_card(c,v):
        related=source_status(c,v)
        if related is None:
            return {"id":v["id"],"available":False,"status":v["status"],
                    "name":"原始来源已不可用","owner":v["owner_name"],
                    "world_id":None,"seed":None,"turn_count":0}
        w,pair,seed=related
        rows=events(c,v["id"])
        return {"id":v["id"],"available":True,"status":v["status"],
                "name":v["name"],"owner":v["owner_name"],
                "world_id":w["id"],"world_title":w["title"],
                "world_law":w["law"],
                "seed":card(seed),"turn_count":len(rows),
                "final":state_from(rows)}

    def detail_data(c,v):
        context=source_status(c,v)
        if context is None:
            fail(404,"原始碰撞世界、其版本或公开种子藏品已撤回")
        w,pair,seed=context
        events_data=trace(c,v,w["law"])
        return {"id":v["id"],"owner":v["owner_name"],"world_id":w["id"],
                "world_title":w["title"],"world_law":w["law"],
                "world_revision":w["revision"],
                "name":v["name"],"charter":v["charter"],"status":v["status"],
                "seed":card(seed),"sources":[card(x) for x in pair],
                "model_version":MODEL_VERSION,"initial":dict(INITIAL),
                "turns":events_data,"final":state_from(events(c,v["id"])),
                "max_turns":MAX_TURNS,
                "notice":"所有数值由公开确定性游戏规则计算，并非历史、经济、政治、人口或生态科学预测；篇章由馆长自行编写。"}

    def public(c,civ):
        return civ is not None and civ["status"]=="public" and source_status(c,civ) is not None

    @app.get("/api/civilizations/policies")
    def policies():
        return {"model_version":MODEL_VERSION,"initial":dict(INITIAL),
                "stats":[{"key":x,"label":STAT_NAMES[x]} for x in STAT_KEYS],
                "policies":[{"id":key,"label":rule["label"],"caption":rule["caption"],
                    "delta":dict(rule["delta"])} for key,rule in POLICIES.items()],
                "law_effects":LAW_EFFECT,
                "limits":{"per_world":MAX_CIVS_PER_WORLD,"max_turns":MAX_TURNS,
                          "min_publish_turns":MIN_PUBLISH_TURNS},
                "notice":"公开的有限规则玩具模型；每项数值都不是现实文明的发展定律。"}

    @app.get("/api/civilizations/worlds")
    def eligible_worlds(user=Depends(require_user)):
        with db() as c:
            rows=c.execute("""SELECT w.*,u.username AS author FROM collision_worlds w
                JOIN users u ON u.id=w.owner_id
                WHERE w.owner_id=? AND w.status='public' ORDER BY w.id DESC LIMIT 36""",
                (user["id"],)).fetchall()
            result=[]
            for w in rows:
                pair=valid_world(c,w)
                if pair is None:continue
                n=c.execute("SELECT COUNT(*) FROM civ_civilizations WHERE world_id=?",
                            (w["id"],)).fetchone()[0]
                result.append({"id":w["id"],"title":w["title"],"law":w["law"],
                    "sources":[card(x) for x in pair],"civilization_count":n,
                    "remaining":max(0,MAX_CIVS_PER_WORLD-n)})
            return {"items":result,"notice":"仅可在你自己仍公开、双原始来源有效的 V33 碰撞世界中创建文明；每个世界最多六个文明。"}

    @app.get("/api/civilizations")
    def gallery():
        with db() as c:
            rows=c.execute("""SELECT v.*,u.username AS owner_name FROM civ_civilizations v
                 JOIN users u ON u.id=v.owner_id
                 WHERE v.status='public' ORDER BY v.id DESC LIMIT 80""").fetchall()
            items=[]
            for v in rows:
                if not public(c,v):continue
                items.append(list_card(c,v))
                if len(items)==36:break
            return {"items":items,
                    "notice":"仅展示真实作者主动发布、原始来源和 V33 世界版本仍有效的虚构文明年轮。"}

    @app.get("/api/civilizations/mine")
    def mine(user=Depends(require_user)):
        with db() as c:
            rows=c.execute("""SELECT v.*,u.username AS owner_name FROM civ_civilizations v
                 JOIN users u ON u.id=v.owner_id WHERE v.owner_id=?
                 ORDER BY v.id DESC LIMIT 200""",(user["id"],)).fetchall()
            return {"items":[list_card(c,r) for r in rows]}

    @app.post("/api/civilizations",status_code=201)
    def create(payload:CivilizationIn,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            w=world(c,payload.world_id)
            pair=valid_world(c,w)
            if w is None or w["owner_id"]!=user["id"] or pair is None:
                fail(404,"你必须拥有一座目前仍公开的 V33 碰撞世界")
            if payload.seed_exhibit_id not in (pair[0]["id"],pair[1]["id"]):
                fail(422,"文明种子只能是该碰撞世界目前公开的两件原始藏品之一")
            n=c.execute("SELECT COUNT(*) FROM civ_civilizations WHERE world_id=?",
                        (w["id"],)).fetchone()[0]
            if n>=MAX_CIVS_PER_WORLD:
                fail(409,"这个碰撞世界已经有六个文明")
            cur=c.execute("""INSERT INTO civ_civilizations(
                owner_id,world_id,world_revision,seed_exhibit_id,name,charter,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?)""",
                (user["id"],w["id"],w["revision"],payload.seed_exhibit_id,
                 payload.name,payload.charter,now(),now()))
            return {"id":cur.lastrowid,"status":"draft","model_version":MODEL_VERSION}

    @app.get("/api/civilizations/{civ_id}")
    def detail(civ_id:int,user=Depends(maybe_user)):
        with db() as c:
            civ=get(c,civ_id)
            if civ is None:
                fail(404,"文明不存在")
            if civ["status"]!="public" and (not user or user["id"]!=civ["owner_id"]):
                fail(404,"文明仍为作者私密草稿")
            return detail_data(c,civ)

    @app.post("/api/civilizations/{civ_id}/turns",status_code=201)
    def step(civ_id:int,payload:TurnIn,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            civ=own(c,civ_id,user)
            context=source_status(c,civ)
            if context is None:fail(409,"原始世界或文明种子已失效，不能继续演化")
            rows=events(c,civ_id)
            if len(rows)>=MAX_TURNS:fail(409,"单个文明最多经历八轮重大抉择")
            w,_,_=context
            result=apply_turn(state_from(rows),payload.policy,w["law"])
            c.execute("""INSERT INTO civ_turns(
                civ_id,turn_index,policy,chapter,narrative,after_json,created_at)
                VALUES(?,?,?,?,?,?,?)""",
                (civ_id,len(rows)+1,payload.policy,payload.chapter,payload.narrative,
                 json.dumps(result["after"],ensure_ascii=False,sort_keys=True),now()))
            # Appending a turn makes a previously published chronicle private;
            # author must manually approve the complete updated storyline.
            c.execute("""UPDATE civ_civilizations SET status='draft',updated_at=?
                WHERE id=?""",(now(),civ_id))
            return {"turn":len(rows)+1,"outcome":result,
                    "status":"draft","notice":"本次选择已使用显式的游戏规则计算并写入历史；须再次主动发布。"}

    @app.delete("/api/civilizations/{civ_id}/turns/latest")
    def undo(civ_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            own(c,civ_id,user)
            last=c.execute("""SELECT id FROM civ_turns WHERE civ_id=?
                      ORDER BY turn_index DESC LIMIT 1""",(civ_id,)).fetchone()
            if last is None:fail(409,"该文明还没有可以撤回的决策")
            c.execute("DELETE FROM civ_turns WHERE id=?",(last["id"],))
            c.execute("UPDATE civ_civilizations SET status='draft',updated_at=? WHERE id=?",
                      (now(),civ_id))
            return {"ok":True,"notice":"已撤回最新一轮的原创篇章；旧公开版本已下架，重新发布前仅作者可见。"}

    @app.post("/api/civilizations/{civ_id}/publish")
    def publish(civ_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            civ=own(c,civ_id,user)
            if source_status(c,civ) is None:
                fail(409,"原始世界或种子撤回，不能公开文明")
            if len(events(c,civ_id))<MIN_PUBLISH_TURNS:
                fail(409,"至少写下两轮重大决策及原创历史篇章后才能公开")
            c.execute("UPDATE civ_civilizations SET status='public',updated_at=? WHERE id=?",
                      (now(),civ_id))
            return {"ok":True,"status":"public"}

    @app.post("/api/civilizations/{civ_id}/unpublish")
    def unpublish(civ_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            own(c,civ_id,user)
            c.execute("UPDATE civ_civilizations SET status='draft',updated_at=? WHERE id=?",
                      (now(),civ_id))
            return {"ok":True}

    @app.delete("/api/civilizations/{civ_id}")
    def delete(civ_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            own(c,civ_id,user)
            c.execute("DELETE FROM civ_civilizations WHERE id=?",(civ_id,))
            return {"ok":True,"notice":"文明与作者自写的历史篇章已删除，原始 V33 世界和藏品不受影响。"}

    @app.get("/api/civilizations/{civ_id}/counterfactual")
    def counterfactual(civ_id:int,turn:int=Query(ge=1,le=MAX_TURNS),
                       policy:str=Query(min_length=3,max_length=40),
                       user=Depends(maybe_user)):
        if policy not in POLICIES:
            fail(422,"必须选择已公开定义的文明决策规则")
        with db() as c:
            civ=get(c,civ_id)
            if civ is None or (civ["status"]!="public" and
                               (user is None or civ["owner_id"]!=user["id"])):
                fail(404,"文明还未公开或不存在")
            context=source_status(c,civ)
            if context is None:fail(404,"原始世界与种子藏品已失效")
            world_row,_,_=context
            original=trace(c,civ,world_row["law"])
            if turn>len(original):
                fail(422,"选择的关键抉择轮次尚不存在")
            start=dict(INITIAL) if turn==1 else dict(original[turn-2]["after"])
            alt=[]
            before=start
            for index in range(turn-1,len(original)):
                p=policy if index==turn-1 else original[index]["policy"]
                result=apply_turn(before,p,world_row["law"])
                alt.append({"turn":index+1,"policy":p,
                            "policy_label":result["policy_label"],
                            "after":result["after"],"delta":result["delta"],
                            "event":result["event"],"mood":result["mood"]})
                before=result["after"]
            actual_final=original[-1]["after"]
            hypothetical_final=alt[-1]["after"]
            return {"civilization_id":civ_id,"turn":turn,
                    "actual_policy":original[turn-1]["policy"],
                    "alternative_policy":policy,
                    "actual_final":actual_final,
                    "alternative_final":hypothetical_final,
                    "difference":{k:hypothetical_final[k]-actual_final[k] for k in STAT_KEYS},
                    "alternative_history":alt,
                    "model_version":MODEL_VERSION,
                    "notice":"这是一项不写入数据库的反事实游戏实验：仅替换指定轮次的策略，之后沿用馆长原有策略；不代表真实因果或历史预测。"}
