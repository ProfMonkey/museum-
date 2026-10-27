"""V21 万物皆可玩: bounded interactive models and opt-in real-user discovery relays.

Simulations are simplified demonstrations, not scientific measurement. Links express
creative association unless the contributor supplies an unverified HTTPS reference.
All relay nodes resolve live visibility so withdrawn items never leak through chains.
"""
from __future__ import annotations

import math
from urllib.parse import urlsplit
from typing import Literal
from fastapi import Depends, Query
from pydantic import BaseModel, Field, ConfigDict, field_validator

DISCLAIMER = "教育性简化互动模型；非实测、非轨道预测或专业工程设计。"
KINDS = {
    "orbit": {"title": "引力与轨道", "domain": "天文与航天", "category": "天体与星系"},
    "gears": {"title": "齿轮传动", "domain": "工程与发明", "category": "机械装置"},
    "fractal": {"title": "分形宇宙", "domain": "物理与数学", "category": "数学与几何"},
}


class Experiment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["orbit", "gears", "fractal"]
    a: float = Field(default=1.0, allow_inf_nan=False)
    b: float = Field(default=1.0, allow_inf_nan=False)
    c: float = Field(default=1.0, allow_inf_nan=False)
    iterations: int = Field(default=55, ge=20, le=90)


class NewRelay(BaseModel):
    source_id: int = Field(ge=1)
    title: str = Field(min_length=2, max_length=60)

    @field_validator("title")
    @classmethod
    def name(cls, value):
        value=value.strip()
        if len(value)<2:raise ValueError("路线名称至少两字")
        return value


class RelayLink(BaseModel):
    source_id: int = Field(ge=1)
    reason: str = Field(min_length=8, max_length=280)
    relation: Literal["创意联想", "来源线索"] = "创意联想"
    source_url: str = Field(default="", max_length=320)

    @field_validator("reason")
    @classmethod
    def reason_text(cls, value):
        value=value.strip()
        if len(value)<8:raise ValueError("请解释这两个事物的联系")
        return value

    @field_validator("source_url")
    @classmethod
    def safe_source(cls, value):
        value=value.strip()
        if value:
            parsed=urlsplit(value)
            if parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password or any(
                ord(ch)<32 for ch in value):
                raise ValueError("只允许使用不含账号密码的 HTTPS 来源链接")
        return value


class RelayState(BaseModel):
    open: bool


def simulate(data: Experiment, fail):
    a,b,c=data.a,data.b,data.c
    if data.kind=="orbit":
        if not 0.3<=a<=6 or not 0.1<=b<=3 or c!=1:
            fail(422,"轨道模型：半径 0.3–6 AU，恒星质量 0.1–3 倍太阳；c 应为 1")
        period=math.sqrt(a*a*a/b)
        velocity=29.7847*math.sqrt(b/a)
        return {"kind":"orbit","name":"轨道探索","params":{"radius_au":a,"mass_solar":b},
                "outcome":{"period_years":round(period,4),"speed_kms":round(velocity,3)},
                "formula":"T ≈ √(a³/M)，v ≈ 29.78√(M/a) km/s",
                "note":"仅适用近似圆轨道、二体牛顿引力与太阳单位，忽略摄动和相对论。"}
    if data.kind=="gears":
        if not (8<=a<=120 and 8<=b<=120 and a.is_integer() and b.is_integer()
                and 5<=c<=120):
            fail(422,"齿轮模型：两齿数须为 8–120 的整数，输入转速 5–120 rpm")
        driven=-c*a/b
        return {"kind":"gears","name":"齿轮传动","params":{"driver_teeth":int(a),
                "driven_teeth":int(b),"input_rpm":c},
                "outcome":{"output_rpm":round(driven,3),"ideal_torque_ratio":round(b/a,4)},
                "formula":"输出转速 = −输入转速 × 主齿数/从齿数",
                "note":"仅代表理想外啮合齿轮；负号表示反向。未计摩擦、载荷、机械强度。"}
    if not (-2<=a<=1 and -1.5<=b<=1.5 and 0.8<=c<=5):
        fail(422,"分形模型：横坐标 -2–1，纵坐标 -1.5–1.5，放大 0.8–5")
    return {"kind":"fractal","name":"曼德博分形","params":{"center_x":a,"center_y":b,
            "zoom":c,"iterations":data.iterations},
            "outcome":{"max_iterations":data.iterations,"window_width":round(3.4/c,4)},
            "formula":"z₀ = 0；zₙ₊₁ = zₙ² + c，超出 |z| > 2 时判定逃逸",
            "note":"有限迭代的逃逸时间可视化，不是无限精度的数学判定。"}


def mount_play(app, db, require_user, maybe_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS play_relays(
          id INTEGER PRIMARY KEY,
          owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          title TEXT NOT NULL,
          is_open INTEGER NOT NULL DEFAULT 1 CHECK(is_open IN (0,1)),
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS play_relay_steps(
          id INTEGER PRIMARY KEY,
          relay_id INTEGER NOT NULL REFERENCES play_relays(id) ON DELETE CASCADE,
          position INTEGER NOT NULL CHECK(position BETWEEN 0 AND 11),
          exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          contributor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          relation TEXT NOT NULL,
          reason TEXT NOT NULL,
          source_url TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL,
          UNIQUE(relay_id,position), UNIQUE(relay_id,exhibit_id)
        );
        CREATE INDEX IF NOT EXISTS ix_play_relay_steps ON play_relay_steps(relay_id,position);
        CREATE INDEX IF NOT EXISTS ix_play_relay_owner ON play_relays(owner_id,id DESC);
        """)

    def public_exhibit(c, eid):
        # World-linked objects must remain in a published world, not merely a public exhibit.
        return c.execute("""SELECT e.id,e.title,e.category,e.domain,e.description,
            u.username curator FROM exhibits e
            JOIN users u ON u.id=e.user_id
            LEFT JOIN fantasy_relics fr ON fr.exhibit_id=e.id
            LEFT JOIN fantasy_worlds w ON w.id=fr.world_id
            WHERE e.id=? AND e.visibility='public'
            AND (fr.id IS NULL OR w.visibility='public')""",(eid,)).fetchone()

    def relay(c, rid):
        row=c.execute("""SELECT r.*,u.username creator FROM play_relays r
            JOIN users u ON u.id=r.owner_id WHERE r.id=?""",(rid,)).fetchone()
        if not row: fail(404,"接力路线不存在")
        return row

    def visible_steps(c, rid):
        rows=c.execute("""SELECT s.*,u.username contributor FROM play_relay_steps s
            JOIN users u ON u.id=s.contributor_id
            WHERE s.relay_id=? ORDER BY s.position ASC LIMIT 12""",(rid,)).fetchall()
        result=[]
        for row in rows:
            if row["position"]!=len(result):break  # A deleted/hidden middle node breaks the chain.
            source=public_exhibit(c,row["exhibit_id"])
            if source is None:break
            result.append({"id":row["id"],"position":row["position"],
                "exhibit_id":row["exhibit_id"],"title":source["title"],
                "category":source["category"],"domain":source["domain"],
                "description":source["description"],"curator":source["curator"],
                "contributor":row["contributor"],"relation":row["relation"],
                "reason":row["reason"],"source_url":row["source_url"]})
        return result

    def card(c,row,include_steps=False,user=None):
        steps=visible_steps(c,row["id"])
        if not steps:return None
        obj={"id":row["id"],"title":row["title"],"creator":row["creator"],
             "is_open":bool(row["is_open"]),"is_owner":bool(user and user["id"]==row["owner_id"]),"count":len(steps),
             "first":steps[0]["title"],"last":steps[-1]["title"],
             "created_at":row["created_at"],"notice":"联想不等于科学因果；外部来源链接由投稿者提供，未经本站核实。"}
        if include_steps:obj["steps"]=steps
        return obj

    @app.get("/api/play/config")
    def config():
        return {"models":[{"kind":kind,**details} for kind,details in KINDS.items()],
                "max_relays":10,"max_steps":12,"notice":DISCLAIMER}

    @app.post("/api/play/preview")
    def preview(data:Experiment):
        return {"result":simulate(data,fail),"notice":DISCLAIMER}

    @app.post("/api/play/records",status_code=201)
    def record(data:Experiment,user=Depends(require_user)):
        result=simulate(data,fail)
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            count=c.execute("""SELECT COUNT(*) FROM exhibits WHERE user_id=?
                AND title LIKE '互动实验｜%'""",(user["id"],)).fetchone()[0]
            if count>=30:fail(429,"最多收藏三十条实验结果")
            # Fully computed by server. Clients cannot submit allegedly measured results.
            import json
            raw=json.dumps(result,ensure_ascii=False,sort_keys=True)
            cur=c.execute("""INSERT INTO exhibits(
                user_id,title,description,story,category,series,domain,
                time_bucket,time_basis,time_note,tags,image_url,source_url,visibility,
                created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (user["id"],"互动实验｜"+result["name"],
                 result["note"],"【互动模型推演／非真实测量】\n"+result["formula"]+"\n"+raw,
                 KINDS[data.kind]["category"],"民间奇趣",KINDS[data.kind]["domain"],
                 "此刻/实时","事件发生","本站简化参数实验",
                 "互动实验,科学教育,参数模型","","","private",now(),now()))
            return {"id":cur.lastrowid,"visibility":"private","result":result,
                    "notice":"已存入私人藏品；公开分享需要馆长在编辑界面另行主动授权。"}

    @app.get("/api/play/sources")
    def sources(q:str=Query(default="",max_length=70)):
        q=q.strip()
        with db() as c:
            rows=c.execute("""SELECT e.id FROM exhibits e
                LEFT JOIN fantasy_relics fr ON fr.exhibit_id=e.id
                LEFT JOIN fantasy_worlds w ON w.id=fr.world_id
                WHERE e.visibility='public' AND (fr.id IS NULL OR w.visibility='public')
                AND (e.title LIKE ? OR e.description LIKE ?)
                ORDER BY e.id DESC LIMIT 35""",('%'+q+'%', '%'+q+'%')).fetchall()
            return {"items":[dict(public_exhibit(c,row["id"])) for row in rows],
                    "notice":"真实社区展品；不保证投稿事实已独立查证。"}

    @app.get("/api/play/relays")
    def list_relays():
        with db() as c:
            rows=c.execute("""SELECT r.*,u.username creator FROM play_relays r
                JOIN users u ON u.id=r.owner_id ORDER BY r.id DESC LIMIT 100""").fetchall()
            return {"items":[v for row in rows if (v:=card(c,row)) is not None]}

    @app.post("/api/play/relays",status_code=201)
    def create_relay(data:NewRelay,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            if not public_exhibit(c,data.source_id):
                fail(404,"只能从仍公开的藏品开始接力")
            if c.execute("SELECT COUNT(*) FROM play_relays WHERE owner_id=?",
                         (user["id"],)).fetchone()[0]>=10:
                fail(429,"每位馆长最多开启十条接力")
            at=now()
            cur=c.execute("INSERT INTO play_relays(owner_id,title,created_at) VALUES(?,?,?)",
                          (user["id"],data.title,at))
            c.execute("""INSERT INTO play_relay_steps
                (relay_id,position,exhibit_id,contributor_id,relation,reason,created_at)
                VALUES(?,0,?,?,'创意联想','起始展品',?)""",
                (cur.lastrowid,data.source_id,user["id"],at))
            return {"id":cur.lastrowid,"count":1}

    @app.get("/api/play/relays/{relay_id}")
    def get_relay(relay_id:int,user=Depends(maybe_user)):
        with db() as c:
            r=relay(c,relay_id)
            result=card(c,r,True,user)
            if result is None:fail(404,"起点已经撤回公开，这条路线暂时不可见")
            return result

    @app.post("/api/play/relays/{relay_id}/steps",status_code=201)
    def add_relay_step(relay_id:int,data:RelayLink,user=Depends(require_user)):
        if data.relation=="来源线索" and not data.source_url:
            fail(422,"来源线索需要提供 HTTPS 参考链接（本站不保证其正确性）")
        if data.relation=="创意联想" and data.source_url:
            fail(422,"创意联想无需添加来源链接")
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            r=relay(c,relay_id)
            if not r["is_open"]:fail(409,"这条接力已经由创建者收官")
            if not public_exhibit(c,data.source_id):
                fail(404,"只能接上仍公开的藏品")
            raw=c.execute("""SELECT * FROM play_relay_steps
                WHERE relay_id=? ORDER BY position""",(relay_id,)).fetchall()
            chain=visible_steps(c,relay_id)
            if not chain or len(chain)!=len(raw):fail(409,"中间的展品已撤回公开或被删除，路线停止接力")
            if len(chain)>=12:fail(429,"接力最多十二站")
            if any(s["exhibit_id"]==data.source_id for s in chain):fail(409,"不能重复接上同一件展品")
            if c.execute("""SELECT COUNT(*) FROM play_relay_steps
                WHERE relay_id=? AND contributor_id=?""",(relay_id,user["id"])).fetchone()[0]>=3:
                fail(429,"每位馆长在同一条路线最多贡献三站")
            cur=c.execute("""INSERT INTO play_relay_steps
                (relay_id,position,exhibit_id,contributor_id,relation,reason,source_url,created_at)
                VALUES(?,?,?,?,?,?,?,?)""",
                (relay_id,len(chain),data.source_id,user["id"],data.relation,
                 data.reason,data.source_url,now()))
            return {"id":cur.lastrowid,"position":len(chain),"count":len(chain)+1}

    @app.patch("/api/play/relays/{relay_id}")
    def close_relay(relay_id:int,data:RelayState,user=Depends(require_user)):
        with db() as c:
            row=relay(c,relay_id)
            if row["owner_id"]!=user["id"]:fail(403,"只有发起者能设置接力状态")
            c.execute("UPDATE play_relays SET is_open=? WHERE id=?",
                      (1 if data.open else 0,relay_id))
            return {"open":data.open}

    @app.delete("/api/play/relays/{relay_id}")
    def delete_relay(relay_id:int,user=Depends(require_user)):
        with db() as c:
            row=relay(c,relay_id)
            if row["owner_id"]!=user["id"]:fail(403,"只能删除自己发起的路线")
            c.execute("DELETE FROM play_relays WHERE id=?",(relay_id,))
            return {"ok":True}
