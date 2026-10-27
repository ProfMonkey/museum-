"""V26 万物奇遇任务链 — verified live museum discovery from actual wheel outcomes.

This is a transparent lexical matching layer, NOT an AI claim or a paid recommendation.
Only currently public objects are returned; manually confirmed visits remain private,
and source deletion or visibility revocation re-redacts both old and current results.
"""
from __future__ import annotations

import re
from typing import Literal
from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict, Field

CANDIDATE_LIMIT=400
MATCH_LIMIT=4
EXPAND_LIMIT=3
MAX_QUERY=60


class MarkVisit(BaseModel):
    model_config=ConfigDict(extra="forbid")
    exhibit_id: int=Field(ge=1)


def pieces(text):
    """Small explainable fragments: whole label + Han bigrams + word tokens."""
    s=(text or "").strip().casefold()
    if not s:return []
    # Never issue arbitrary SQL with user-supplied strings; this is only in-memory.
    words=re.findall(r"[a-z0-9]{2,}|[\u4e00-\u9fff]{2,}",s)
    terms=[s]
    for w in words:
        terms.append(w)
        if re.search(r"[\u4e00-\u9fff]",w) and len(w)>=3:
            terms.extend(w[i:i+2] for i in range(len(w)-1))
    return list(dict.fromkeys(t for t in terms if 2<=len(t)<=MAX_QUERY))[:36]


def label_score(label,exhibit):
    """Deterministic, intentionally modest string matching with provenance."""
    name=(exhibit["title"] or "").casefold()
    summary=(exhibit["description"] or "").casefold()
    tags=(exhibit["tags"] or "").casefold()
    words=pieces(label)
    if not words:return 0,None
    whole=words[0]
    if whole==name:
        return 100,"标题完全一致"
    if whole in name:
        return 85,"标题包含抽取词"
    if whole in tags:
        return 70,"标签包含抽取词"
    if whole in summary:
        return 60,"简介包含抽取词"
    ngrams=words[1:]
    if not ngrams:return 0,None
    title_overlap=sum(1 for w in ngrams if w in name)
    tag_overlap=sum(1 for w in ngrams if w in tags)
    summary_overlap=sum(1 for w in ngrams if w in summary)
    if title_overlap:
        return 20+min(30,title_overlap*4),"标题存在词片段重合"
    if tag_overlap:
        return 15+min(20,tag_overlap*3),"标签存在词片段重合"
    if summary_overlap:
        return 10+min(18,summary_overlap*2),"简介存在词片段重合"
    return 0,None


def mount_discovery_missions(app,db,require_user,now,fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS wonder_adventure_visits(
          id INTEGER PRIMARY KEY,
          adventure_id INTEGER NOT NULL REFERENCES wonder_adventures(id) ON DELETE CASCADE,
          step_number INTEGER NOT NULL CHECK(step_number BETWEEN 1 AND 5),
          exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
          visited_at TEXT NOT NULL,
          UNIQUE(adventure_id,step_number)
        );
        CREATE INDEX IF NOT EXISTS ix_adventure_visits_owner
            ON wonder_adventure_visits(adventure_id,step_number);
        """)

    def live_exhibits(c):
        # Retrieving a bounded set of actual, public exhibits, also respecting
        # private fantasy worlds and revocable studio/sandbox publication.
        return c.execute("""SELECT e.id,e.title,e.description,e.tags,e.category,e.domain
            FROM exhibits e
            LEFT JOIN fantasy_relics fr ON fr.exhibit_id=e.id
            LEFT JOIN fantasy_worlds fw ON fw.id=fr.world_id
            LEFT JOIN creator_studio_projects sp ON sp.exhibit_id=e.id
            LEFT JOIN wonder_sandbox_projects sb ON sb.exhibit_id=e.id
            WHERE e.visibility='public'
              AND (fr.id IS NULL OR fw.visibility='public')
              AND (sp.id IS NULL OR sp.visibility='public')
              AND (sb.id IS NULL OR sb.visibility='public')
            ORDER BY e.id DESC LIMIT ?""",(CANDIDATE_LIMIT,)).fetchall()

    def card(row,mode,reason):
        return {"id":row["id"],"title":row["title"],"domain":row["domain"],
                "category":row["category"],"mode":mode,"reason":reason}

    def picks(term,rows,origin_id=None):
        found,others=[],[]
        for row in rows:
            if origin_id is not None and row["id"]==origin_id:
                continue
            score,why=label_score(term,row)
            if score:
                found.append((score,row["id"],row,why))
            else:
                others.append(row)
        found.sort(key=lambda o:(-o[0],-o[1]))
        results=[]
        if origin_id is not None:
            source=next((x for x in rows if x["id"]==origin_id),None)
            if source:
                results.append(card(source,"source","命运抽中的原始公开藏品"))
        results.extend(card(row,"match",why) for _,_,row,why in found[:MATCH_LIMIT])
        if not found and not results:
            results.extend(card(x,"browse","无文字匹配；仅供随意探索，不声称内容相关")
                           for x in others[:EXPAND_LIMIT])
        return results

    def owned(c,card_id,user):
        row=c.execute("""SELECT id,owner_id,title FROM wonder_adventures
            WHERE id=? AND owner_id=?""",(card_id,user["id"])).fetchone()
        if not row:fail(404,"只能查看自己的奇遇任务")
        return row

    def stage_rows(c,card_id):
        return c.execute("""SELECT step_number,topic,chosen_kind,chosen_exhibit_id,
                manual_label,drawn_at FROM wonder_adventure_steps
                WHERE adventure_id=? ORDER BY step_number""",(card_id,)).fetchall()

    def current_stage(c,card_id,number):
        row=c.execute("""SELECT step_number,topic,chosen_kind,chosen_exhibit_id,
                manual_label,drawn_at FROM wonder_adventure_steps
                WHERE adventure_id=? AND step_number=?""",(card_id,number)).fetchone()
        if not row:fail(404,"奇遇不存在此站")
        if row["drawn_at"] is None:fail(409,"先抽取此站的真实结果")
        return row

    def stage_term(stage,live):
        if stage["chosen_kind"]=="manual":
            return stage["manual_label"],None,False
        if stage["chosen_kind"]=="exhibit":
            exhibit=next((r for r in live if r["id"]==stage["chosen_exhibit_id"]),None)
            # Source can be public but outside latest CANDIDATE_LIMIT; do not
            # show its stored private title from another session.
            if exhibit is None:
                return None,None,True
            return exhibit["title"],exhibit["id"],False
        return None,None,True

    def stage_view(c,card_id,stage,live,visits):
        result={"number":stage["step_number"],"topic":stage["topic"],
                "ready":stage["drawn_at"] is not None,
                "label":None,"source_unavailable":False,
                "suggestions":[],"visited":False,"visited_exhibit_id":None,
                "visited_title":None,"visited_at":None}
        if not result["ready"]:return result
        term,origin,withdrawn=stage_term(stage,live)
        result["source_unavailable"]=withdrawn
        if term is not None:
            result["label"]=term
            result["suggestions"]=picks(term,live,origin)
        visit=visits.get(stage["step_number"])
        if visit:
            # This check happens on every read, not from an old stored caption.
            x=next((x for x in live if x["id"]==visit["exhibit_id"]),None)
            if x:
                result.update(visited=True,visited_exhibit_id=x["id"],
                              visited_title=x["title"],visited_at=visit["visited_at"])
            else:
                result["visit_withdrawn"]=True
        return result

    @app.get("/api/discovery/quests/config")
    def quest_config():
        return {"modes":{"source":"抽中的原始馆藏","match":"文字相关（待判断）",
                         "browse":"随意逛逛（非相关推荐）"},
                "max_matches":MATCH_LIMIT,"max_browse":EXPAND_LIMIT,
                "notice":"仅检索真实公开展品。标题、标签与简介的词片段匹配不保证真正相关，更不代表已核验的科学或历史事实。参观完成为用户自行标记，非服务器行为验证。"}

    @app.get("/api/discovery/quests/explore")
    def public_explore(q:str=Query(min_length=2,max_length=MAX_QUERY)):
        query=q.strip()
        if len(query)<2:fail(422,"请提供至少两个字符的搜索词")
        with db() as c:
            options=picks(query,live_exhibits(c))
        return {"query":query,"items":options,
                "matched":sum(x["mode"]=="match" for x in options),
                "disclaimer":"只检索真实公开藏品，可能没有结果。随意逛逛并非匹配推荐。"}

    @app.get("/api/adventures/{card_id}/quests")
    def list_quests(card_id:int,user=Depends(require_user)):
        with db() as c:
            owned(c,card_id,user)
            live=live_exhibits(c)
            visit_rows=c.execute("""SELECT step_number,exhibit_id,visited_at FROM wonder_adventure_visits
                WHERE adventure_id=?""",(card_id,)).fetchall()
            visits={r["step_number"]:r for r in visit_rows}
            result=[stage_view(c,card_id,row,live,visits)
                    for row in stage_rows(c,card_id)]
            return {"card_id":card_id,"stages":result,
                    "visited_count":sum(1 for x in result if x["visited"]),
                    "available_stages":sum(1 for x in result if x["ready"] and x["suggestions"]),
                    "notice":"只记录本人手动标记的参观进度，不验证真实到访；结果和访问记录不会自动进入奇遇公开分享页面。"}

    @app.post("/api/adventures/{card_id}/quests/{stage_number}/visit")
    def visit(card_id:int,stage_number:int,payload:MarkVisit,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            owned(c,card_id,user)
            stage=current_stage(c,card_id,stage_number)
            live=live_exhibits(c)
            term,origin,_=stage_term(stage,live)
            if term is None:fail(409,"本次抽中的公开馆藏已撤回，无法使用它继续任务")
            allowed={x["id"] for x in picks(term,live,origin)}
            if payload.exhibit_id not in allowed:
                fail(409,"只能标记本站当前可见的真实任务藏品")
            c.execute("""INSERT INTO wonder_adventure_visits
                (adventure_id,step_number,exhibit_id,visited_at) VALUES(?,?,?,?)
                ON CONFLICT(adventure_id,step_number) DO UPDATE SET
                exhibit_id=excluded.exhibit_id,visited_at=excluded.visited_at""",
                (card_id,stage_number,payload.exhibit_id,now()))
            return {"ok":True,"stage_number":stage_number,"exhibit_id":payload.exhibit_id,
                    "notice":"已自行标记参观；不代表平台验证了实际到访或理解。"}

    @app.delete("/api/adventures/{card_id}/quests/{stage_number}/visit")
    def undo(card_id:int,stage_number:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            owned(c,card_id,user)
            current_stage(c,card_id,stage_number)
            c.execute("""DELETE FROM wonder_adventure_visits
                WHERE adventure_id=? AND step_number=?""",(card_id,stage_number))
            return {"ok":True}
