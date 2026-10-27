"""V25 命运接力: stage-by-stage adventures built only from your own real wheels.

Visitors can view explicitly published completed cards; otherwise each user's
wheel choices and results remain private. Stage picks share V24's server-side
fairness and wheel history. Public exhibit titles are always re-resolved live.
"""
from __future__ import annotations

import secrets
from html import escape
from typing import Literal

from fastapi import Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from wheel_api import TOPICS, draw_index

MAX_CARDS = 30
MAX_STAGES = 5
MAX_HISTORY = 20
WITHDRAWN = "已撤回的馆藏"


class AdventureCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=2, max_length=70)
    wheel_ids: list[int] = Field(min_length=2, max_length=MAX_STAGES)

    @field_validator("title")
    @classmethod
    def title_clean(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("奇遇名称至少 2 字")
        return value

    @field_validator("wheel_ids")
    @classmethod
    def distinct_wheels(cls, values):
        if any(isinstance(x, bool) or x <= 0 for x in values) or len(set(values)) != len(values):
            raise ValueError("一条奇遇必须按顺序选 2–5 个不同的私人转盘")
        return values


class AdventureVisibility(BaseModel):
    model_config = ConfigDict(extra="forbid")
    visibility: Literal["private", "public"]


def mount_adventures(app, db, require_user, maybe_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS wonder_adventures(
          id INTEGER PRIMARY KEY,
          owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          title TEXT NOT NULL,
          visibility TEXT NOT NULL DEFAULT 'private'
            CHECK(visibility IN ('private','public')),
          share_token TEXT UNIQUE,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS wonder_adventure_steps(
          id INTEGER PRIMARY KEY,
          adventure_id INTEGER NOT NULL REFERENCES wonder_adventures(id) ON DELETE CASCADE,
          step_number INTEGER NOT NULL CHECK(step_number BETWEEN 1 AND 5),
          wheel_id INTEGER REFERENCES wonder_wheels(id) ON DELETE SET NULL,
          wheel_title TEXT NOT NULL,
          topic TEXT NOT NULL,
          chosen_item_id INTEGER REFERENCES wonder_wheel_items(id) ON DELETE SET NULL,
          chosen_kind TEXT NOT NULL DEFAULT '' CHECK(chosen_kind IN ('','manual','exhibit')),
          manual_label TEXT NOT NULL DEFAULT '',
          chosen_exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
          drawn_at TEXT,
          UNIQUE(adventure_id,step_number)
        );
        CREATE INDEX IF NOT EXISTS ix_adventure_owner ON wonder_adventures(owner_id,id DESC);
        CREATE INDEX IF NOT EXISTS ix_adventure_step ON wonder_adventure_steps(adventure_id,step_number);
        """)

    def permitted_exhibit(c, eid):
        if eid is None:
            return None
        return c.execute("""SELECT e.id,e.title FROM exhibits e
            LEFT JOIN fantasy_relics fr ON fr.exhibit_id=e.id
            LEFT JOIN fantasy_worlds fw ON fw.id=fr.world_id
            WHERE e.id=? AND e.visibility='public'
              AND (fr.id IS NULL OR fw.visibility='public')""", (eid,)).fetchone()

    def eligible(c, wheel_id):
        rows = c.execute("""SELECT id,kind,label,exhibit_id FROM wonder_wheel_items
            WHERE wheel_id=? ORDER BY id""", (wheel_id,)).fetchall()
        options = []
        for item in rows:
            if item["kind"] == "manual":
                options.append(item)
            elif permitted_exhibit(c, item["exhibit_id"]):
                options.append(item)
        return options

    def owned(c, card_id, user_id):
        card = c.execute("""SELECT * FROM wonder_adventures
            WHERE id=? AND owner_id=?""", (card_id, user_id)).fetchone()
        if card is None:
            fail(404, "奇遇卡不存在或不属于你")
        return card

    def steps(c, card_id):
        return c.execute("""SELECT * FROM wonder_adventure_steps
           WHERE adventure_id=? ORDER BY step_number""", (card_id,)).fetchall()

    def visible_stage(c, step):
        chosen = step["drawn_at"] is not None
        result = {"number": step["step_number"], "topic": step["topic"],
                  "topic_label": TOPICS.get(step["topic"], TOPICS["custom"]),
                  "wheel_title": step["wheel_title"], "completed": chosen,
                  "drawn_at": step["drawn_at"], "label": None, "exhibit_id": None,
                  "available": None}
        if not chosen:
            return result
        if step["chosen_kind"] == "manual":
            result.update(label=step["manual_label"], available=True)
        elif step["chosen_kind"] == "exhibit":
            source = permitted_exhibit(c, step["chosen_exhibit_id"])
            result.update(label=source["title"] if source else WITHDRAWN,
                          exhibit_id=source["id"] if source else None,
                          available=bool(source))
        return result

    def card_view(c, card, include_steps=False, public=False):
        rows = steps(c, card["id"])
        completed = sum(x["drawn_at"] is not None for x in rows)
        finished = completed == len(rows)
        response = {"id": card["id"], "title": card["title"],
                    "visibility": card["visibility"],
                    "created_at": card["created_at"],
                    "stage_count": len(rows), "completed_count": completed,
                    "finished": finished, "is_public": card["visibility"] == "public" and finished,
                    "share_path": ("/adventure/" + card["share_token"])
                        if card["visibility"] == "public" and finished and card["share_token"]
                        else None}
        if include_steps:
            response["stages"] = [visible_stage(c, row) for row in rows]
        return response

    @app.get("/api/adventures/config")
    def config():
        return {"stages_min":2, "stages_max":MAX_STAGES,
                "max_cards":MAX_CARDS, "topics": TOPICS,
                "notice":"每站从本人选择的独立转盘公平抽取。奇遇卡默认私人，分享须明确授权；已撤回馆藏内容会自动隐藏。"}

    @app.get("/api/adventures")
    def list_cards(user=Depends(require_user)):
        with db() as c:
            rows = c.execute("""SELECT * FROM wonder_adventures
                WHERE owner_id=? ORDER BY id DESC LIMIT ?""",
                (user["id"], MAX_CARDS)).fetchall()
            return {"items":[card_view(c,row) for row in rows]}

    @app.post("/api/adventures", status_code=201)
    def create(payload:AdventureCreate, user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            n=c.execute("SELECT COUNT(*) FROM wonder_adventures WHERE owner_id=?",
                        (user["id"],)).fetchone()[0]
            if n >= MAX_CARDS: fail(429, "每位馆长最多保存三十张命运奇遇卡")
            selected=[]
            for wid in payload.wheel_ids:
                wheel=c.execute("""SELECT id,title,topic FROM wonder_wheels
                    WHERE id=? AND owner_id=?""",(wid,user["id"])).fetchone()
                if not wheel: fail(404,"奇遇路线只能使用你自己的真实转盘")
                if len(eligible(c,wid)) < 2: fail(409,"选中的转盘至少需要两个仍有效的选项")
                selected.append(wheel)
            t=now()
            result=c.execute("""INSERT INTO wonder_adventures
                (owner_id,title,created_at,updated_at) VALUES(?,?,?,?)""",
                (user["id"],payload.title,t,t))
            card_id=result.lastrowid
            for i, wheel in enumerate(selected, start=1):
                c.execute("""INSERT INTO wonder_adventure_steps
                    (adventure_id,step_number,wheel_id,wheel_title,topic)
                    VALUES(?,?,?,?,?)""",
                    (card_id,i,wheel["id"],wheel["title"],wheel["topic"]))
            return {"id":card_id,"visibility":"private",
                    "stage_count":len(selected),"notice":"私人奇遇已创建，按顺序开始每一站的随机抽取。"}

    @app.get("/api/adventures/share/{share_token}")
    def shared_card(share_token:str):
        if not 24 <= len(share_token) <= 80:
            fail(404,"分享卡不存在")
        with db() as c:
            card=c.execute("""SELECT * FROM wonder_adventures
                WHERE share_token=? AND visibility='public'""",(share_token,)).fetchone()
            if not card: fail(404,"分享卡不存在或已撤回")
            data=card_view(c,card,True,public=True)
            if not data["finished"]: fail(404,"尚未完成的奇遇不能分享")
            # No private wheel IDs, owner IDs, or internal item IDs exposed.
            data.pop("id",None)
            data.pop("visibility",None)
            return data

    @app.get("/api/adventures/{card_id}")
    def detail(card_id:int,user=Depends(require_user)):
        with db() as c:
            return card_view(c,owned(c,card_id,user["id"]),True)

    @app.post("/api/adventures/{card_id}/advance")
    def advance(card_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            card=owned(c,card_id,user["id"])
            if card["visibility"]=="public":
                fail(409,"已公开的奇遇不可改写结果，请先撤回或创建新的一张")
            row=c.execute("""SELECT * FROM wonder_adventure_steps
                WHERE adventure_id=? AND drawn_at IS NULL
                ORDER BY step_number LIMIT 1""",(card_id,)).fetchone()
            if row is None: fail(409,"所有阶段已抽取完成")
            if not row["wheel_id"]:fail(409,"本阶段转盘已被删除，请删除这张未完成的奇遇并重新安排")
            wheel=c.execute("""SELECT * FROM wonder_wheels
                WHERE id=? AND owner_id=?""",(row["wheel_id"],user["id"])).fetchone()
            if not wheel:fail(409,"当前转盘已被删除，无法继续抽取")
            candidates=eligible(c,wheel["id"])
            if len(candidates)<2:fail(409,"当前转盘有效选项不足两个，先补充选项后再继续")
            last_row=c.execute("""SELECT item_id FROM wonder_wheel_draws
                WHERE wheel_id=? ORDER BY id DESC LIMIT 1""",(wheel["id"],)).fetchone()
            last_id=last_row["item_id"] if last_row else None
            last=next((i for i,x in enumerate(candidates) if x["id"]==last_id),None)
            index,denom=draw_index(len(candidates),last,bool(wheel["no_repeat"]))
            candidate=candidates[index]
            kind=candidate["kind"]
            manual_label=candidate["label"] if kind=="manual" else ""
            eid=candidate["exhibit_id"] if kind=="exhibit" else None
            stamp=now()
            c.execute("""UPDATE wonder_adventure_steps SET
                chosen_item_id=?,chosen_kind=?,manual_label=?,chosen_exhibit_id=?,drawn_at=?
                WHERE id=? AND drawn_at IS NULL""",
                (candidate["id"],kind,manual_label,eid,stamp,row["id"]))
            c.execute("""INSERT INTO wonder_wheel_draws(wheel_id,item_id,drawn_at)
                VALUES(?,?,?)""",(wheel["id"],candidate["id"],stamp))
            c.execute("""DELETE FROM wonder_wheel_draws WHERE wheel_id=? AND id NOT IN
                (SELECT id FROM wonder_wheel_draws WHERE wheel_id=?
                ORDER BY id DESC LIMIT ?)""",(wheel["id"],wheel["id"],MAX_HISTORY))
            c.execute("UPDATE wonder_adventures SET updated_at=? WHERE id=?",(stamp,card_id))
            # Resolve active exhibit title again; original private exhibit title was
            # never snapshotted, so a later privacy change redacts every view.
            selection=visible_stage(c,c.execute("""SELECT * FROM wonder_adventure_steps
                WHERE id=?""",(row["id"],)).fetchone())
            return {"stage":selection,"stage_number":row["step_number"],
                    "chance_denominator":denom,
                    "card":card_view(c,card,True),
                    "notice":"本阶段从转盘当前有效选项等概率抽取，并同步记入该转盘私人历史。"}

    @app.patch("/api/adventures/{card_id}/visibility")
    def set_visibility(card_id:int,payload:AdventureVisibility,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            card=owned(c,card_id,user["id"])
            data=card_view(c,card)
            if payload.visibility=="public" and not data["finished"]:
                fail(409,"奇遇完成所有阶段后才能主动分享")
            if payload.visibility=="public" and card["visibility"]=="public" and card["share_token"]:
                return {"visibility":"public","share_path":"/adventure/"+card["share_token"]}
            token=secrets.token_urlsafe(27) if payload.visibility=="public" else None
            c.execute("""UPDATE wonder_adventures SET visibility=?,share_token=?,updated_at=?
                WHERE id=?""",(payload.visibility,token,now(),card_id))
            return {"visibility":payload.visibility,
                    "share_path":"/adventure/"+token if token else None,
                    "notice":"撤回后旧链接立即失效；重新分享会生成新的随机链接。"}

    @app.delete("/api/adventures/{card_id}")
    def delete(card_id:int,user=Depends(require_user)):
        with db() as c:
            owned(c,card_id,user["id"])
            c.execute("DELETE FROM wonder_adventures WHERE id=?",(card_id,))
            return {"ok":True}

    @app.get("/adventure/{share_token}",response_class=HTMLResponse)
    def public_page(share_token:str):
        card=shared_card(share_token)
        headline=escape(card["title"])
        chunks=[]
        for s in card["stages"]:
            if not s["completed"]:continue
            chapter=escape(s["topic_label"])
            chosen=escape(s["label"] or "未抽取")
            link=(f'<a href="/?source={s["exhibit_id"]}">查看公开的原始藏品 ↗</a>'
                  if s["exhibit_id"] else "")
            chunks.append(f'<section class="step"><small>第 {s["number"]} 站 · {chapter}</small>'
                          f'<h2>{chosen}</h2>{link}</section>')
        body="\n".join(chunks)
        page=f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{headline} · 万物奇遇卡</title>
<style>
:root{{color-scheme:dark}}*{{box-sizing:border-box}}body{{margin:0;background:#091321;
color:#f2dfbd;font-family:system-ui,-apple-system,'Noto Sans SC',sans-serif;padding:24px}}
main{{width:min(580px,100%);margin:28px auto;padding:29px;border:1px solid #c4a77999;
border-radius:21px;background:radial-gradient(circle at 80% 3%,#ca945350,transparent 48%),#17253a}}
.logo{{font-size:12px;letter-spacing:.13em;color:#e7c589}}h1{{font-size:clamp(27px,5vw,42px);
line-height:1.4;margin:15px 0 10px}}.subtitle{{color:#b7c6d5;font-size:13px;line-height:1.8}}
.step{{border:1px solid #d7b98366;background:#172639;padding:15px 21px;margin:13px 0;
border-radius:14px}}.step small{{color:#dfbe82;font-size:12px}}
.step h2{{font-size:23px;color:#fff0cd;margin:10px 0;overflow-wrap:anywhere}}
a{{color:#d8c393}}.step a{{font-size:12px}}footer{{text-align:center;margin:23px 0;color:#a8b9c9;font-size:11px}}
</style></head><body><main><div class="logo">✳ WONDER ATLAS · 万物命运接力</div>
<h1>✨ {headline}</h1><p class="subtitle">真实馆长亲手挑选转盘，随机抽取后组合成的今日奇遇。
这是娱乐性随机选择，不代表本站推荐；馆藏已撤回会被自动隐藏。</p>
{body}<footer>每一步都是随机决定的 · 收藏万物，发现下一站</footer>
<a href="/">← 探索万物博物馆</a></main></body></html>"""
        return HTMLResponse(page,headers={"Cache-Control":"no-store",
          "Content-Security-Policy":"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
          "X-Content-Type-Options":"nosniff"})
