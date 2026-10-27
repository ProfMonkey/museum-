"""V22 Creator Studio: bounded, no-code interactive exhibits for real museum accounts.

Creators author a quiz, ecosystem simulation or a 16-step sound sketch. Visitors
can play published projects without executing untrusted scripts or uploading audio.
Each studio work owns a normal private exhibit and follows live source visibility.
"""
from __future__ import annotations

import json
from math import isfinite
from typing import Any, Literal

from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TEMPLATES = {
    "quiz": {"title": "奇物问答", "glyph": "🧩", "domain": "游戏与交互", "category": "互动装置",
             "intro": "由作者设计的四选一知识与脑洞小测验；答案由服务端判定。"},
    "ecology": {"title": "生命演化沙盘", "glyph": "🌱", "domain": "动物与生态", "category": "生态系统",
                "intro": "调节增长率、容纳量和损耗，观察简化的逻辑斯蒂增长曲线。"},
    "music": {"title": "16 格旋律机", "glyph": "🎹", "domain": "音乐与声音", "category": "音乐与声音",
              "intro": "16 格音符编辑器，浏览器使用 Web Audio 合成声音；不上传音乐素材。"},
}
NOTICE = ("全部交互均由真实用户创作。科普问答未经本站独立核验；"
          "生态模型是简化课堂演示，旋律使用浏览器合成音，非真实采样。")


class QuizConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=8, max_length=180)
    options: list[str] = Field(min_length=4, max_length=4)
    answer: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=10, max_length=500)

    @field_validator("question", "explanation")
    @classmethod
    def nonblank(cls, value):
        value=value.strip()
        if not value:
            raise ValueError("内容不能为空")
        return value

    @field_validator("options")
    @classmethod
    def option_integrity(cls, values):
        values=[v.strip() for v in values]
        if any(not 1<=len(v)<=90 for v in values) or len(set(values))!=4:
            raise ValueError("必须提供四个不同的、长度不超过 90 字的选项")
        return values


class EcologyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    population: int = Field(default=120, ge=1, le=1200)
    capacity: int = Field(default=600, ge=40, le=5000)
    growth: float = Field(default=0.18, ge=0, le=0.6, allow_inf_nan=False)
    loss: float = Field(default=0.03, ge=0, le=0.35, allow_inf_nan=False)
    steps: int = Field(default=40, ge=10, le=70)


class MusicConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bpm: int = Field(default=110, ge=50, le=200)
    notes: list[int] = Field(min_length=16, max_length=16)

    @field_validator("notes")
    @classmethod
    def valid_notes(cls, values):
        if any(n not in range(-1,8) for n in values):
            raise ValueError("音符只能是 -1（休止）或 0–7")
        return values


CONFIG_TYPES = {"quiz": QuizConfig, "ecology": EcologyConfig, "music": MusicConfig}


def valid_config(kind: str, value: dict[str, Any]):
    if kind not in CONFIG_TYPES:
        raise ValueError("互动模板不存在")
    return CONFIG_TYPES[kind].model_validate(value).model_dump()


class StudioDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["quiz", "ecology", "music"]
    title: str = Field(min_length=2, max_length=78)
    description: str = Field(default="", max_length=500)
    config: dict[str, Any]

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value):
        value=value.strip()
        if len(value)<2:
            raise ValueError("作品名称至少需要两个字")
        return value

    @model_validator(mode="after")
    def check_template(self):
        self.description=self.description.strip()
        if len(json.dumps(self.config,ensure_ascii=False))>7000:
            raise ValueError("互动参数超出允许大小")
        self.config=valid_config(self.kind,self.config)
        return self


class StudioVisibility(BaseModel):
    visibility: Literal["private", "public"]


class QuizAnswer(BaseModel):
    answer: int = Field(ge=0,le=3)


def ecological_curve(config):
    n=float(config["population"])
    capacity=config["capacity"]
    rate=config["growth"]
    loss=config["loss"]
    result=[round(n,3)]
    for _ in range(config["steps"]):
        n=max(0.0,min(float(capacity)*2.0,
          n+rate*n*(1.0-n/capacity)-loss*n))
        if not isfinite(n):
            raise ValueError("无效的生态演算")
        result.append(round(n,3))
    return {"series":result,"final":round(n,3),"initial":config["population"],
            "capacity":capacity,"steps":config["steps"],
            "note":"离散逻辑斯蒂增长加线性损耗的演示，未模拟物种竞争、环境噪声或疾病。"}


def mount_studio(app, db, require_user, maybe_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS creator_studio_projects(
          id INTEGER PRIMARY KEY,
          owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          exhibit_id INTEGER NOT NULL UNIQUE REFERENCES exhibits(id) ON DELETE CASCADE,
          kind TEXT NOT NULL CHECK(kind IN ('quiz','ecology','music')),
          title TEXT NOT NULL,
          description TEXT NOT NULL DEFAULT '',
          config_json TEXT NOT NULL,
          visibility TEXT NOT NULL DEFAULT 'private' CHECK(visibility IN ('private','public')),
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_creator_studio_owner
          ON creator_studio_projects(owner_id,id DESC);
        CREATE INDEX IF NOT EXISTS ix_creator_studio_public
          ON creator_studio_projects(visibility,id DESC);
        """)

    def fetch(c, pid):
        return c.execute("""SELECT p.*,e.visibility exhibit_visibility,u.username creator,
            e.user_id exhibit_owner FROM creator_studio_projects p
            JOIN exhibits e ON e.id=p.exhibit_id
            JOIN users u ON u.id=p.owner_id WHERE p.id=?""",(pid,)).fetchone()

    def owner(c,pid,user):
        p=fetch(c,pid)
        if not p or p["owner_id"]!=user["id"] or p["exhibit_owner"]!=user["id"]:
            fail(404,"互动作品不存在或无权操作")
        return p

    def visible(c,pid,user):
        p=fetch(c,pid)
        if not p:
            fail(404,"作品不存在")
        is_owner=bool(user and p["owner_id"]==user["id"])
        if not is_owner and (p["visibility"]!="public" or p["exhibit_visibility"]!="public"):
            fail(404,"此作品未公开")
        return p

    def card(row,user,details=False):
        is_owner=bool(user and row["owner_id"]==user["id"])
        public=row["visibility"]=="public" and row["exhibit_visibility"]=="public"
        result={"id":row["id"],"kind":row["kind"],"template":TEMPLATES[row["kind"]]["title"],
                "glyph":TEMPLATES[row["kind"]]["glyph"],
                "title":row["title"],"description":row["description"],"creator":row["creator"],
                "exhibit_id":row["exhibit_id"],"visibility":row["visibility"],
                "public":public,"is_owner":is_owner,
                "created_at":row["created_at"],"updated_at":row["updated_at"],
                "notice":NOTICE}
        if details:
            data=json.loads(row["config_json"])
            if row["kind"]=="quiz" and not is_owner:
                data.pop("answer",None)
            result["config"]=data
        return result

    def backing(draft):
        details=TEMPLATES[draft.kind]
        # Never serialize secret quiz answers to a public museum exhibit.
        story=("【互动展品／用户创作】此作品通过预定义安全模板进行交互，"
               "不执行用户上传的代码。\n"+details["intro"]+"\n"
               "问题与解释由作者提交，本站未进行独立事实审核。")
        return details,story

    @app.get("/api/play/studio/config")
    def config():
        return {"templates":[{"kind":kind,**value} for kind,value in TEMPLATES.items()],
                "max_projects":15,"notice":NOTICE,
                "defaults":{"quiz":{"question":"如果从化石研究过去的生命，最直接需要哪类证据？",
                           "options":["岩层中的化石记录","一本幻想小说","随机数字","电脑桌面壁纸"],
                           "answer":0,
                           "explanation":"化石记录和相关地层信息是研究古生物历史的重要证据，但仍需要科学分析。"},
                    "ecology":EcologyConfig().model_dump(),
                    "music":MusicConfig(notes=[0,-1,2,-1,4,-1,7,-1,5,-1,4,-1,2,-1,0,-1]).model_dump()}}

    @app.get("/api/play/studio")
    def list_projects(scope:Literal["public","mine"]="public",user=Depends(maybe_user)):
        if scope=="mine" and not user:fail(401,"请先登录")
        with db() as c:
            if scope=="mine":
                rows=c.execute("""SELECT p.*,e.visibility exhibit_visibility,
                    e.user_id exhibit_owner,u.username creator
                    FROM creator_studio_projects p JOIN exhibits e ON e.id=p.exhibit_id
                    JOIN users u ON u.id=p.owner_id
                    WHERE p.owner_id=? ORDER BY p.id DESC LIMIT 15""",
                    (user["id"],)).fetchall()
            else:
                rows=c.execute("""SELECT p.*,e.visibility exhibit_visibility,
                    e.user_id exhibit_owner,u.username creator
                    FROM creator_studio_projects p JOIN exhibits e ON e.id=p.exhibit_id
                    JOIN users u ON u.id=p.owner_id
                    WHERE p.visibility='public' AND e.visibility='public'
                    ORDER BY p.id DESC LIMIT 100""").fetchall()
            return {"items":[card(row,user) for row in rows if
                             row["exhibit_owner"]==row["owner_id"]],
                    "notice":NOTICE}

    @app.post("/api/play/studio",status_code=201)
    def create(draft:StudioDraft,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            count=c.execute("""SELECT COUNT(*) FROM creator_studio_projects
                WHERE owner_id=?""",(user["id"],)).fetchone()[0]
            if count>=15:fail(429,"每位馆长最多创作十五件交互展品")
            details,story=backing(draft)
            at=now()
            cur=c.execute("""INSERT INTO exhibits(user_id,title,description,story,category,series,
               domain,time_bucket,time_basis,time_note,tags,image_url,source_url,
               visibility,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
               (user["id"],"互动展品｜"+draft.title,draft.description or details["intro"],
                story,details["category"],"民间奇趣",details["domain"],
                "此刻/实时","制作/创作","V22 用户自制互动展品",
                "用户创作,互动展品,万物工坊","","","private",at,at))
            row=c.execute("""INSERT INTO creator_studio_projects(owner_id,exhibit_id,
               kind,title,description,config_json,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?)""",
               (user["id"],cur.lastrowid,draft.kind,draft.title,draft.description,
                json.dumps(draft.config,ensure_ascii=False,sort_keys=True),at,at))
            return {"id":row.lastrowid,"exhibit_id":cur.lastrowid,
                    "visibility":"private","notice":"作品已存为私人藏品，需要另行主动公开。"}

    @app.get("/api/play/studio/{project_id}")
    def detail(project_id:int,user=Depends(maybe_user)):
        with db() as c:
            return card(visible(c,project_id,user),user,True)

    @app.put("/api/play/studio/{project_id}")
    def update(project_id:int,draft:StudioDraft,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            old=owner(c,project_id,user)
            details,story=backing(draft)
            at=now()
            c.execute("""UPDATE creator_studio_projects
                SET kind=?,title=?,description=?,config_json=?,updated_at=?
                WHERE id=?""",(draft.kind,draft.title,draft.description,
                json.dumps(draft.config,ensure_ascii=False,sort_keys=True),at,project_id))
            c.execute("""UPDATE exhibits SET title=?,description=?,story=?,
                category=?,domain=?,updated_at=? WHERE id=? AND user_id=?""",
                ("互动展品｜"+draft.title,draft.description or details["intro"],
                 story,details["category"],details["domain"],at,old["exhibit_id"],user["id"]))
            return {"id":project_id,"notice":"已更新互动作品参数。"}

    @app.patch("/api/play/studio/{project_id}/visibility")
    def publish(project_id:int,draft:StudioVisibility,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            old=owner(c,project_id,user)
            at=now()
            # Both components become public/private together. Private reversal never
            # changes other users' works or previously created relay connections.
            c.execute("""UPDATE exhibits SET visibility=?,updated_at=?
                WHERE id=? AND user_id=?""",(draft.visibility,at,old["exhibit_id"],user["id"]))
            c.execute("""UPDATE creator_studio_projects SET visibility=?,updated_at=?
                WHERE id=?""",(draft.visibility,at,project_id))
            return {"visibility":draft.visibility,"exhibit_id":old["exhibit_id"]}

    @app.delete("/api/play/studio/{project_id}")
    def delete(project_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            old=owner(c,project_id,user)
            # This is the auto-created backing exhibit, not an exhibit authored by somebody else.
            c.execute("DELETE FROM exhibits WHERE id=? AND user_id=?",
                      (old["exhibit_id"],user["id"]))
            return {"ok":True}

    @app.post("/api/play/studio/{project_id}/answer")
    def answer(project_id:int,draft:QuizAnswer,user=Depends(maybe_user)):
        with db() as c:
            work=visible(c,project_id,user)
            if work["kind"]!="quiz":fail(409,"这不是问答作品")
            info=json.loads(work["config_json"])
            # The key is not in any public GET response or backing museum record.
            return {"correct":draft.answer==info["answer"],
                    "correct_answer":info["answer"],
                    "explanation":info["explanation"],
                    "notice":"答案和解释均由投稿馆长撰写，本站未独立核验。"}

    @app.post("/api/play/studio/{project_id}/simulate")
    def simulate(project_id:int,scenario:EcologyConfig,user=Depends(maybe_user)):
        with db() as c:
            work=visible(c,project_id,user)
            if work["kind"]!="ecology":fail(409,"这不是生命演化作品")
        return {"result":ecological_curve(scenario.model_dump()),"notice":NOTICE}
