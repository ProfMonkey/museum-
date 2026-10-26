"""V11: explainable object classification paths and bounded, privacy-safe museum links.

A curator's manual link is a *claim by that curator*, never platform verification.
System suggestions are mechanically derived from common domain/category/tags only.
This module intentionally reuses the existing exhibit records; no content copies.
"""
from __future__ import annotations

import sqlite3
from typing import Literal

from fastapi import Depends, Query
from pydantic import BaseModel, Field

LINK_KINDS = {
    "same_topic": "主题相近",
    "materials": "材料或工艺",
    "influence": "影响或启发",
    "historical": "历史脉络",
    "contrast": "相互对照",
    "curiosity": "意外关联",
}
MAX_NODES = 32


class ManualLink(BaseModel):
    target_id: int = Field(ge=1)
    kind: Literal["same_topic", "materials", "influence", "historical", "contrast", "curiosity"]
    explanation: str = Field(min_length=8, max_length=280)


def accessible(item, user):
    return item and (item["visibility"] == "public" or (user and item["user_id"] == user["id"]))


def node(row):
    x = dict(row)
    return {
        "id": x["id"], "title": x["title"], "category": x["category"],
        "series": x.get("series", "民间奇趣"), "domain": x.get("domain", "其他"),
        "time_bucket": x.get("time_bucket", "时间不详"),
        "time_basis": x.get("time_basis", "不详"), "time_note": x.get("time_note", ""),
        "visibility": x["visibility"],
        "tags": [a for a in x["tags"].split(",") if a],
        "source_url": x["source_url"], "image_url": x["image_url"],
        "owner": x.get("owner", ""),
    }


def taxonomy_path(item):
    return {
        "collection": [item.get("series", "民间奇趣"), item.get("domain", "其他"), item["category"]],
        "time": [item.get("time_bucket", "时间不详"), item.get("time_basis", "不详")],
        "time_note": item.get("time_note", ""),
        "source_status": "附有来源链接" if item["source_url"] else "尚未附来源链接",
        "notice": "分类是检索路径，不代表内容经过机构认证；时间口径详见该展品的资料来源。",
    }


def suggestion(a, b):
    # A suggestion must explain the actual equality that caused it. No LLM-generated causal claims.
    common = sorted(set(a["tags"]) & set(b["tags"]))[:3]
    reasons = []
    if common:
        reasons.append("共同标签：" + "、".join(common))
    if a["category"] == b["category"] and a["category"] != "其他":
        reasons.append("同属「" + a["category"] + "」细分类别")
    if a["domain"] == b["domain"] and a["domain"] != "其他":
        reasons.append("同属「" + a["domain"] + "」领域")
    if not reasons:
        return None
    return {
        "weight": 5 * len(common) + (4 if a["category"] == b["category"] and a["category"] != "其他" else 0)
                          + (2 if a["domain"] == b["domain"] and a["domain"] != "其他" else 0),
        "explanation": "；".join(reasons),
    }


def mount_connections(app, db, read_exhibit, maybe_user, require_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS exhibit_links (
          id INTEGER PRIMARY KEY,
          from_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          to_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          kind TEXT NOT NULL,
          explanation TEXT NOT NULL,
          created_at TEXT NOT NULL,
          UNIQUE(from_id, to_id, kind)
        );
        CREATE INDEX IF NOT EXISTS ix_exhibit_links_from ON exhibit_links(from_id);
        CREATE INDEX IF NOT EXISTS ix_exhibit_links_to ON exhibit_links(to_id);
        """)

    def item_row(c, eid, user):
        row = c.execute("""SELECT e.*, u.username owner FROM exhibits e
            JOIN users u ON u.id=e.user_id WHERE e.id=?""", (eid,)).fetchone()
        if not accessible(row, user):
            return None
        result = node(row)
        result["is_mine"] = bool(user and user["id"] == row["user_id"])
        return result

    @app.get("/api/exhibits/{exhibit_id}/connections")
    def get_connections(exhibit_id: int, depth: int = Query(1, ge=1, le=2), user=Depends(maybe_user)):
        with db() as c:
            read_exhibit(c, exhibit_id, user)
            root = item_row(c, exhibit_id, user)
            if root is None:
                fail(404, "展品不存在或没有访问权限")
            viewer = user["id"] if user else -1
            nodes = {root["id"]: root}
            levels = {exhibit_id: 0}
            result_edges = {}
            frontier = [exhibit_id]
            for level in range(depth):
                if not frontier or len(nodes) >= MAX_NODES:
                    break
                marks = ",".join("?" for _ in frontier)
                # Each step queries only the current frontier, not all global links.
                manual = c.execute(f"""SELECT l.*,u.username author FROM exhibit_links l
                    JOIN users u ON u.id=l.author_id
                    WHERE l.from_id IN ({marks}) OR l.to_id IN ({marks})
                    ORDER BY l.created_at DESC LIMIT 120""", (*frontier, *frontier)).fetchall()
                next_frontier = []
                for link in manual:
                    for eid in (link["from_id"], link["to_id"]):
                        if eid not in nodes and len(nodes) < MAX_NODES:
                            x = item_row(c, eid, user)
                            if x is not None:
                                nodes[eid] = x
                                levels[eid] = level + 1
                                next_frontier.append(eid)
                    left, right = link["from_id"], link["to_id"]
                    if left in nodes and right in nodes:
                        result_edges["manual:" + str(link["id"])] = {
                            "id": link["id"], "from": left, "to": right,
                            "source": "curator", "kind": link["kind"],
                            "label": LINK_KINDS.get(link["kind"], "馆长关联"),
                            "explanation": link["explanation"], "author": link["author"],
                            "editable": bool(user and link["author_id"] == user["id"]),
                        }
                # Recommendations: a bounded recent sample, only visible exhibits.
                if len(nodes) < MAX_NODES:
                    sample = c.execute("""SELECT e.*,u.username owner FROM exhibits e
                        JOIN users u ON u.id=e.user_id
                        WHERE e.visibility='public' OR e.user_id=?
                        ORDER BY e.created_at DESC LIMIT 450""", (viewer,)).fetchall()
                    suggestions = []
                    for raw in sample:
                        candidate = node(raw)
                        candidate["is_mine"] = bool(user and user["id"] == raw["user_id"])
                        if candidate["id"] in nodes:
                            continue
                        for old_id in frontier:
                            info = suggestion(nodes[old_id], candidate)
                            if info:
                                suggestions.append((info["weight"], old_id, candidate, info["explanation"]))
                    # stable tie-breaking for reproducible routes
                    suggestions.sort(key=lambda x: (-x[0], x[2]["id"], x[1]))
                    seen = set()
                    # Limit auto recommendations per hop; avoid flooding the screen.
                    max_suggest = min(MAX_NODES - len(nodes), 9 if level == 0 else 7)
                    for _, anchor, target, reason in suggestions:
                        if target["id"] in seen or len(seen) >= max_suggest:
                            continue
                        seen.add(target["id"])
                        nodes[target["id"]] = target
                        levels[target["id"]] = level + 1
                        next_frontier.append(target["id"])
                        result_edges["suggested:%s:%s" % (anchor, target["id"])] = {
                            "id": None, "from": anchor, "to": target["id"],
                            "source": "suggestion", "kind": "similarity", "label": "分类相似",
                            "explanation": reason, "author": None, "editable": False,
                        }
                frontier = list(dict.fromkeys(next_frontier))
            # Other users' private exhibits never appear in nodes or edges.
            return {"focus": root, "path": taxonomy_path(root),
                    "nodes": list(nodes.values()), "edges": list(result_edges.values()),
                    "depth": depth, "max_nodes": MAX_NODES,
                    "disclaimer": "金色线条为馆长手动提交的联系（未经平台核验）；虚线为分类或标签相同产生的推荐，不等于历史因果关系。"}

    @app.post("/api/exhibits/{exhibit_id}/connections", status_code=201)
    def add_connection(exhibit_id: int, data: ManualLink, user=Depends(require_user)):
        if exhibit_id == data.target_id:
            fail(400, "不能将展品连接到自己")
        with db() as c:
            source = read_exhibit(c, exhibit_id, user)
            if source["user_id"] != user["id"]:
                fail(403, "只有起点展品的馆长可以创建关联")
            read_exhibit(c, data.target_id, user)
            existing = c.execute("SELECT COUNT(*) FROM exhibit_links WHERE from_id=?", (exhibit_id,)).fetchone()[0]
            if existing >= 60:
                fail(400, "一件展品最多添加 60 条手动关联")
            try:
                cur = c.execute("""INSERT INTO exhibit_links(from_id,to_id,author_id,kind,explanation,created_at)
                    VALUES(?,?,?,?,?,?)""", (exhibit_id, data.target_id, user["id"], data.kind,
                                          data.explanation.strip(), now()))
            except sqlite3.IntegrityError:
                fail(409, "这条同类型关联已经存在")
        return {"ok": True, "id": cur.lastrowid, "notice": "关联由馆长提出，未经过平台事实核验。"}

    @app.delete("/api/exhibits/{exhibit_id}/connections/{link_id}")
    def remove_connection(exhibit_id: int, link_id: int, user=Depends(require_user)):
        with db() as c:
            link = c.execute("SELECT * FROM exhibit_links WHERE id=? AND from_id=?", (link_id, exhibit_id)).fetchone()
            if not link:
                fail(404, "关联不存在")
            if link["author_id"] != user["id"]:
                fail(403, "只有创建者可以删除关联")
            c.execute("DELETE FROM exhibit_links WHERE id=?", (link_id,))
        return {"ok": True}