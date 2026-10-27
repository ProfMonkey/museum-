"""Wonder Atlas V23 — universal interactive sandbox.

Owners curate two safe, bounded exhibit types: a simplified ideal DC resistor
circuit, or a narrated world-history/fiction timeline. They generate real private
museum exhibits and may explicitly publish them. No arbitrary executable code,
unverified public facts, private-source references, or simulated audience counts.
"""
from __future__ import annotations

import json
import math
from typing import Literal

from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from urllib.parse import urlsplit

NOTICE = ("电路仅为理想欧姆定律教学推演，不支持实体接线、安全认证或专业设计。"
          "时间轴由用户编辑：现实史实为待核资料，原创架空明确标注为虚构。")
KINDS = {
    "circuit": {"label": "⚡ 理想电路积木", "domain": "工程与发明",
                "category": "工程发明", "intro": "改变电压、串并联结构和电阻，观察电流及功率。"},
    "timeline": {"label": "⏳ 万物历史剧场", "domain": "历史与考古",
                 "category": "历史事件", "intro": "自己编排真实历史、个人记忆与架空世界的分镜。"},
}
MAX_PROJECTS = 12


class CircuitConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["series", "parallel"] = "series"
    voltage: float = Field(default=9, ge=.1, le=24, allow_inf_nan=False)
    resistors: list[float] = Field(default_factory=lambda:[100,220,330],
                                    min_length=2, max_length=4)

    @field_validator("resistors")
    @classmethod
    def resistor_bounds(cls, values):
        if any(isinstance(x,bool) or not math.isfinite(x) or not 1<=x<=1000 for x in values):
            raise ValueError("每个电阻必须在 1–1000 Ω 之间")
        return values


class TimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    year: int = Field(ge=-999_999_999, le=3000)
    title: str = Field(min_length=2,max_length=74)
    story: str = Field(min_length=6,max_length=350)
    nature: Literal["史料待核","个人记录","原创虚构"]
    source_url: str = Field(default="",max_length=350)

    @field_validator("title","story")
    @classmethod
    def content(cls,value):
        v=value.strip()
        if not v:raise ValueError("内容不能为空")
        return v

    @field_validator("source_url")
    @classmethod
    def url(cls,value):
        v=value.strip()
        if v:
            p=urlsplit(v)
            if p.scheme!="https" or not p.hostname or p.username or p.password or any(ord(x)<32 for x in v):
                raise ValueError("参考资料只能填写不含账号密码的 HTTPS 网址")
        return v

    @model_validator(mode="after")
    def reality_mark(self):
        if self.year==0:
            raise ValueError("历史公元纪年没有第 0 年")
        # Avoid claiming fictional materials as verifiable historical evidence.
        if self.nature!="史料待核" and self.source_url:
            raise ValueError("非史料事件无需填写参考来源网址")
        return self


class TimelineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[TimelineEvent] = Field(min_length=3,max_length=10)

    @model_validator(mode="after")
    def ordered(self):
        seq=[e.year for e in self.events]
        if seq!=sorted(seq):
            raise ValueError("请按年份从早到晚排列分镜")
        return self


class SandboxDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["circuit","timeline"]
    title: str = Field(min_length=2,max_length=80)
    description: str = Field(default="",max_length=460)
    config: dict

    @field_validator("title")
    @classmethod
    def title_nonempty(cls,value):
        v=value.strip()
        if len(v)<2:raise ValueError("作品名至少 2 字")
        return v

    @model_validator(mode="after")
    def config_valid(self):
        self.description=self.description.strip()
        if len(json.dumps(self.config,ensure_ascii=False))>8000:
            raise ValueError("配置体积过大")
        shape=CircuitConfig if self.kind=="circuit" else TimelineConfig
        self.config=shape.model_validate(self.config).model_dump()
        return self


class Visibility(BaseModel):
    visibility: Literal["public","private"]


def simulate_circuit(config: CircuitConfig):
    """Ideal DC model with series/parallel resistors only; no physical construction."""
    volt=config.voltage
    rs=config.resistors
    if config.mode=="series":
        req=sum(rs)
        current=volt/req
        currents=[current]*len(rs)
        drops=[current*r for r in rs]
    else:
        req=1/sum(1/r for r in rs)
        currents=[volt/r for r in rs]
        current=sum(currents)
        drops=[volt]*len(rs)
    powers=[currents[i]*drops[i] for i in range(len(rs))]
    def r(n):return round(n,6)
    return {"mode":config.mode,"voltage":volt,"resistors":rs,
            "equivalent_ohms":r(req),"total_amperes":r(current),
            "total_watts":r(volt*current),
            "branches":[{"ohms":v,"amperes":r(currents[i]),
                         "volts":r(drops[i]),"watts":r(powers[i])}
                        for i,v in enumerate(rs)],
            "note":"仅计算理想、稳态直流串联或并联纯电阻。忽略温度、导线损耗、短路保护和实际电源限制；禁止用于实体接线指导。"}


def mount_sandbox(app,db,require_user,maybe_user,now,fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS wonder_sandbox_projects(
            id INTEGER PRIMARY KEY,
            owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            exhibit_id INTEGER NOT NULL UNIQUE REFERENCES exhibits(id) ON DELETE CASCADE,
            kind TEXT NOT NULL CHECK(kind IN ('circuit','timeline')),
            title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
            config_json TEXT NOT NULL,
            visibility TEXT NOT NULL DEFAULT 'private'
                CHECK(visibility IN ('private','public')),
            created_at TEXT NOT NULL,updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_wonder_sandbox_owner
            ON wonder_sandbox_projects(owner_id,id DESC);
        CREATE INDEX IF NOT EXISTS ix_wonder_sandbox_public
            ON wonder_sandbox_projects(visibility,id DESC);
        """)

    def get(c,pid):
        return c.execute("""SELECT p.*,e.visibility exhibit_visibility,
                e.user_id exhibit_owner,u.username creator
            FROM wonder_sandbox_projects p JOIN exhibits e ON e.id=p.exhibit_id
            JOIN users u ON u.id=p.owner_id WHERE p.id=?""",(pid,)).fetchone()

    def belongs(c,pid,user):
        row=get(c,pid)
        if not row or row["owner_id"]!=user["id"] or row["exhibit_owner"]!=user["id"]:
            fail(404,"作品不存在或不是你的")
        return row

    def accessible(c,pid,user):
        row=get(c,pid)
        if not row:fail(404,"作品不存在")
        mine=bool(user and row["owner_id"]==user["id"])
        if not mine and (row["visibility"]!="public" or row["exhibit_visibility"]!="public"):
            fail(404,"作品尚未公开")
        return row

    def card(row,user,details=False):
        mine=bool(user and row["owner_id"]==user["id"])
        result={"id":row["id"],"exhibit_id":row["exhibit_id"],"kind":row["kind"],
                "label":KINDS[row["kind"]]["label"],"title":row["title"],
                "description":row["description"],"creator":row["creator"],
                "is_owner":mine,"visibility":row["visibility"],
                "public":row["visibility"]=="public" and row["exhibit_visibility"]=="public",
                "created_at":row["created_at"],"notice":NOTICE}
        if details:
            result["config"]=json.loads(row["config_json"])
        return result

    def exhibition(draft):
        templ=KINDS[draft.kind]
        story=("【用户自制互动展品／科普演示及创作】"+
               templ["intro"]+"\n"+NOTICE+
               "\n本作品由馆长通过受限积木模板创造；真实性、纪年及观点未经本站核验。")
        return templ,story

    @app.get("/api/play/sandbox/config")
    def sandbox_config():
        return {"templates":[{"kind":k,**v} for k,v in KINDS.items()],
                "defaults":{"circuit":CircuitConfig().model_dump(),
                    "timeline":{"events":[
                        {"year":-65000000,"title":"恐龙时代的尾声",
                         "story":"用这一幕讨论白垩纪末的生物演化与研究证据。",
                         "nature":"史料待核","source_url":""},
                        {"year":1969,"title":"载人登月",
                         "story":"由馆长撰写这件航天史事件的关联故事。",
                         "nature":"史料待核","source_url":""},
                        {"year":2200,"title":"星际博物馆",
                         "story":"一座虚构的星际城市收藏从地球带来的万物。",
                         "nature":"原创虚构","source_url":""}
                    ]}},"max_projects":MAX_PROJECTS,"notice":NOTICE}

    @app.post("/api/play/sandbox/preview")
    def sandbox_preview(config:CircuitConfig):
        return {"result":simulate_circuit(config),"notice":NOTICE}

    @app.get("/api/play/sandbox")
    def list_projects(scope:Literal["mine","public"]="public",user=Depends(maybe_user)):
        if scope=="mine" and not user:fail(401,"登录后查看自己的作品")
        with db() as c:
            sql="""SELECT p.*,e.visibility exhibit_visibility,e.user_id exhibit_owner,
                    u.username creator FROM wonder_sandbox_projects p
                JOIN exhibits e ON e.id=p.exhibit_id
                JOIN users u ON u.id=p.owner_id """
            if scope=="mine":
                rows=c.execute(sql+"WHERE p.owner_id=? ORDER BY p.id DESC LIMIT 12",
                              (user["id"],)).fetchall()
            else:
                rows=c.execute(sql+"""WHERE p.visibility='public'
                    AND e.visibility='public' ORDER BY p.id DESC LIMIT 100""").fetchall()
            return {"items":[card(x,user) for x in rows if x["owner_id"]==x["exhibit_owner"]]}

    @app.post("/api/play/sandbox",status_code=201)
    def create(draft:SandboxDraft,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            count=c.execute("SELECT COUNT(*) FROM wonder_sandbox_projects WHERE owner_id=?",
                           (user["id"],)).fetchone()[0]
            if count>=MAX_PROJECTS:fail(429,"最多保存十二件万物沙盒作品")
            templ,story=exhibition(draft)
            t=now()
            exhibit=c.execute("""INSERT INTO exhibits(
                user_id,title,description,story,category,series,domain,time_bucket,time_basis,
                time_note,tags,image_url,source_url,visibility,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (user["id"],"万物沙盒｜"+draft.title,
                 draft.description or templ["intro"],story,templ["category"],
                 "民间奇趣",templ["domain"],"此刻/实时","制作/创作",
                 "本作品创作时间，非其中历史事件真实纪年",
                 "万物沙盒,互动教育,原创收藏","","","private",t,t))
            project=c.execute("""INSERT INTO wonder_sandbox_projects(
                owner_id,exhibit_id,kind,title,description,config_json,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?)""",
                (user["id"],exhibit.lastrowid,draft.kind,draft.title,draft.description,
                 json.dumps(draft.config,ensure_ascii=False,sort_keys=True),t,t))
            return {"id":project.lastrowid,"exhibit_id":exhibit.lastrowid,"visibility":"private"}

    @app.get("/api/play/sandbox/{project_id}")
    def detail(project_id:int,user=Depends(maybe_user)):
        with db() as c:
            return card(accessible(c,project_id,user),user,True)

    @app.put("/api/play/sandbox/{project_id}")
    def update(project_id:int,draft:SandboxDraft,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=belongs(c,project_id,user)
            templ,story=exhibition(draft)
            t=now()
            c.execute("""UPDATE wonder_sandbox_projects SET kind=?,title=?,description=?,
                config_json=?,updated_at=? WHERE id=?""",
                (draft.kind,draft.title,draft.description,
                 json.dumps(draft.config,ensure_ascii=False,sort_keys=True),t,project_id))
            c.execute("""UPDATE exhibits SET title=?,description=?,story=?,category=?,domain=?,
                updated_at=? WHERE id=? AND user_id=?""",
                ("万物沙盒｜"+draft.title,draft.description or templ["intro"],
                 story,templ["category"],templ["domain"],t,row["exhibit_id"],user["id"]))
            return {"id":project_id,"notice":"已保存自制展品"}

    @app.patch("/api/play/sandbox/{project_id}/visibility")
    def visibility(project_id:int,draft:Visibility,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=belongs(c,project_id,user)
            t=now()
            c.execute("UPDATE exhibits SET visibility=?,updated_at=? WHERE id=?",
                (draft.visibility,t,row["exhibit_id"]))
            c.execute("UPDATE wonder_sandbox_projects SET visibility=?,updated_at=? WHERE id=?",
                (draft.visibility,t,project_id))
            return {"visibility":draft.visibility}

    @app.delete("/api/play/sandbox/{project_id}")
    def delete(project_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row=belongs(c,project_id,user)
            c.execute("DELETE FROM exhibits WHERE id=? AND user_id=?",
                      (row["exhibit_id"],user["id"]))
            return {"ok":True}

    @app.post("/api/play/sandbox/{project_id}/simulate")
    def project_preview(project_id:int, config:CircuitConfig,user=Depends(maybe_user)):
        with db() as c:
            row=accessible(c,project_id,user)
            if row["kind"]!="circuit":fail(409,"历史时间轴没有电路模拟功能")
        return {"result":simulate_circuit(config),"notice":NOTICE}
