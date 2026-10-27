"""V27 personal knowledge constellation.

A private-by-default graph owned by each curator. Exhibit titles are resolved live
from current authorized records; no title snapshots are retained for linked exhibits.
System-generated suggestions are deterministic taxonomy/tag overlaps, not verified facts.
"""
from __future__ import annotations

import re
import sqlite3
from typing import Literal

from fastapi import Depends, Query
from pydantic import BaseModel, Field, ConfigDict, model_validator

MAX_NODES = 80
MAX_EDGES = 400
MAX_IMPORT_PER_SOURCE = 80
MAX_SUGGESTIONS = 12

EDGE_KINDS = {
    "same_topic": "主题相近",
    "historical": "历史脉络",
    "influence": "影响或启发",
    "contrast": "相互对照",
    "materials": "材料或工艺",
    "curiosity": "意外关联",
    "personal": "个人联想",
}

ORIGINS = {
    "manual": "手动加入",
    "owned": "我的藏品",
    "bookmarked": "心动收藏",
    "visited": "已标记参观",
    "history": "自愿记录的浏览历史",
}


class ConstellationNodeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["exhibit", "idea"]
    exhibit_id: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, max_length=100)
    note: str = Field(default="", max_length=280)

    @model_validator(mode="after")
    def valid_node(self):
        if self.kind == "exhibit" and self.exhibit_id is None:
            raise ValueError("藏品节点必须提供展品 ID")
        if self.kind == "idea":
            if self.exhibit_id is not None:
                raise ValueError("想法节点不能绑定展品 ID")
            if not (self.title or "").strip():
                raise ValueError("想法节点需要一个名称")
        if self.title is not None:
            self.title = self.title.strip()
        self.note = self.note.strip()
        if self.kind == "idea" and not self.title:
            raise ValueError("想法名称不能为空")
        return self


class ConstellationEdgeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_node_id: int = Field(ge=1)
    to_node_id: int = Field(ge=1)
    kind: Literal["same_topic", "historical", "influence", "contrast",
                  "materials", "curiosity", "personal"] = "personal"
    note: str = Field(min_length=8, max_length=280)

    @model_validator(mode="after")
    def clean_note(self):
        self.note = self.note.strip()
        if len(self.note) < 8:
            raise ValueError("请用至少 8 个字符解释这条关联")
        return self


class ConstellationNodePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, max_length=100)
    note: str | None = Field(default=None, max_length=280)

    @model_validator(mode="after")
    def validate_patch(self):
        if self.title is None and self.note is None:
            raise ValueError("至少提供想法名称或个人注记中的一项")
        if self.title is not None:
            self.title = self.title.strip()
            if not self.title:
                raise ValueError("想法名称不能为空")
        if self.note is not None:
            self.note = self.note.strip()
        return self


def mount_constellation(app, db, read_exhibit, require_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS constellation_nodes(
          id INTEGER PRIMARY KEY,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          kind TEXT NOT NULL CHECK(kind IN ('exhibit','idea')),
          exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE SET NULL,
          title TEXT NOT NULL DEFAULT '',
          note TEXT NOT NULL DEFAULT '',
          origin TEXT NOT NULL DEFAULT 'manual',
          created_at TEXT NOT NULL,
          CHECK((kind='exhibit' AND title='') OR kind='idea')
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ux_constellation_exhibit
          ON constellation_nodes(user_id,exhibit_id)
          WHERE kind='exhibit' AND exhibit_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS ix_constellation_owner
          ON constellation_nodes(user_id,created_at DESC);
        CREATE TABLE IF NOT EXISTS constellation_edges(
          id INTEGER PRIMARY KEY,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          from_node_id INTEGER NOT NULL REFERENCES constellation_nodes(id) ON DELETE CASCADE,
          to_node_id INTEGER NOT NULL REFERENCES constellation_nodes(id) ON DELETE CASCADE,
          kind TEXT NOT NULL,
          note TEXT NOT NULL,
          created_at TEXT NOT NULL,
          CHECK(from_node_id <> to_node_id),
          UNIQUE(user_id,from_node_id,to_node_id,kind)
        );
        CREATE INDEX IF NOT EXISTS ix_constellation_edges_owner
          ON constellation_edges(user_id,created_at DESC);
        """)

    def current_exhibit(c, exhibit_id, user):
        if not exhibit_id:
            return None
        try:
            item = read_exhibit(c, exhibit_id, user)
        except Exception as exc:
            if getattr(exc, "status_code", None) == 404:
                return None
            raise
        # A non-owner must not regain access to an exhibit whose publication is
        # constrained by a private fantasy world or a withdrawn creator project.
        if item["visibility"] == "public" and item["user_id"] != user["id"]:
            row = c.execute("""SELECT
                MAX(CASE WHEN fw.id IS NOT NULL AND fw.visibility<>'public' THEN 1 ELSE 0 END) AS private_world,
                MAX(CASE WHEN sp.id IS NOT NULL AND sp.visibility<>'public' THEN 1 ELSE 0 END) AS private_studio,
                MAX(CASE WHEN sb.id IS NOT NULL AND sb.visibility<>'public' THEN 1 ELSE 0 END) AS private_sandbox
                FROM exhibits e
                LEFT JOIN fantasy_relics fr ON fr.exhibit_id=e.id
                LEFT JOIN fantasy_worlds fw ON fw.id=fr.world_id
                LEFT JOIN creator_studio_projects sp ON sp.exhibit_id=e.id
                LEFT JOIN wonder_sandbox_projects sb ON sb.exhibit_id=e.id
                WHERE e.id=?""", (exhibit_id,)).fetchone()
            if row and any(row[k] for k in ("private_world", "private_studio", "private_sandbox")):
                return None
        return item

    def node_view(c, row, user):
        base = {
            "id": row["id"], "kind": row["kind"], "note": row["note"],
            "origin": row["origin"], "origin_label": ORIGINS.get(row["origin"], "手动加入"),
            "created_at": row["created_at"],
        }
        if row["kind"] == "idea":
            base.update(title=row["title"], category="个人想法", domain="个人世界",
                        tags=[], image_url="", visibility="private", is_mine=True,
                        exhibit_id=None)
            return base
        item = current_exhibit(c, row["exhibit_id"], user)
        if item is None:
            # Keep a removable, title-free placeholder so a revoked/deleted
            # source cannot clog the owner's node quota or leak its old title.
            base.update(title="原始藏品已不可见", category="暂不可用", domain="私人星图",
                        tags=[], image_url="", visibility="unavailable", is_mine=False,
                        exhibit_id=None, owner="", description="", source_unavailable=True)
            return base
        base.update(
            title=item["title"], category=item["category"], domain=item.get("domain", "其他"),
            tags=item["tags"], image_url=item.get("image_url", ""),
            visibility=item["visibility"], is_mine=item["user_id"] == user["id"],
            exhibit_id=item["id"], owner=item.get("owner", ""),
            description=item.get("description", ""), source_unavailable=False,
        )
        return base

    def owned_node(c, node_id, user):
        row = c.execute("""SELECT * FROM constellation_nodes
            WHERE id=? AND user_id=?""", (node_id, user["id"])).fetchone()
        if row is None:
            fail(404, "星图节点不存在或不属于你")
        view = node_view(c, row, user)
        if view is None or view.get("source_unavailable"):
            fail(409, "节点对应的展品已删除、设为私密或撤回公开")
        return row

    def overlap(a, b):
        common = sorted((set(a.get("tags", [])) & set(b.get("tags", []))) - {""})[:3]
        reasons = []
        if common:
            reasons.append("共同标签：" + "、".join(common))
        if a.get("category") == b.get("category") and a.get("category") not in (None, "", "其他", "个人想法"):
            reasons.append("同属「" + a["category"] + "」细分类别")
        if a.get("domain") == b.get("domain") and a.get("domain") not in (None, "", "其他", "个人世界"):
            reasons.append("同属「" + a["domain"] + "」领域")
        if not reasons:
            return None
        return "；".join(reasons)

    def collect_live_nodes(c, user):
        rows = c.execute("""SELECT * FROM constellation_nodes
            WHERE user_id=? ORDER BY created_at DESC,id DESC LIMIT ?""",
            (user["id"], MAX_NODES)).fetchall()
        result = []
        for row in rows:
            item = node_view(c, row, user)
            if item is not None:
                result.append(item)
        return result

    def graph_payload(c, user):
        nodes = collect_live_nodes(c, user)
        node_ids = {x["id"] for x in nodes}
        rows = c.execute("""SELECT * FROM constellation_edges
            WHERE user_id=? ORDER BY created_at DESC,id DESC LIMIT ?""",
            (user["id"], MAX_EDGES)).fetchall()
        edges = [{
            "id": row["id"], "from_node_id": row["from_node_id"],
            "to_node_id": row["to_node_id"], "kind": row["kind"],
            "label": EDGE_KINDS.get(row["kind"], "个人关联"),
            "note": row["note"], "created_at": row["created_at"],
            "source": "user", "verified": False,
        } for row in rows
            if row["from_node_id"] in node_ids and row["to_node_id"] in node_ids]

        linked = {
            (min(e["from_node_id"], e["to_node_id"]),
             max(e["from_node_id"], e["to_node_id"]))
            for e in edges
        }
        exhibit_nodes = [x for x in nodes if x["kind"] == "exhibit" and not x.get("source_unavailable")]
        suggestions = []
        for i, left in enumerate(exhibit_nodes):
            for right in exhibit_nodes[i + 1:]:
                pair = (min(left["id"], right["id"]), max(left["id"], right["id"]))
                if pair in linked:
                    continue
                reason = overlap(left, right)
                if reason:
                    suggestions.append({
                        "from_node_id": left["id"], "to_node_id": right["id"],
                        "reason": reason,
                        "notice": "仅由标签或分类重合触发，需由你判断是否值得建立关联。",
                    })
        suggestions.sort(key=lambda x: (x["reason"], x["from_node_id"], x["to_node_id"]))
        return {
            "nodes": nodes, "edges": edges, "suggestions": suggestions[:MAX_SUGGESTIONS],
            "limits": {"max_nodes": MAX_NODES, "max_edges": MAX_EDGES},
            "notice": "个人星图默认仅本人可见。金色实线是你主动保存的个人关联；系统线索只说明标签或分类重合，不代表因果、事实或机构认证。",
        }

    @app.get("/api/constellation")
    def get_constellation(user=Depends(require_user)):
        with db() as c:
            return graph_payload(c, user)

    @app.post("/api/constellation/nodes", status_code=201)
    def create_node(payload: ConstellationNodeIn, user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            count = c.execute("SELECT COUNT(*) FROM constellation_nodes WHERE user_id=?",
                              (user["id"],)).fetchone()[0]
            if count >= MAX_NODES:
                fail(429, "个人星图最多保存 80 个节点；可先删除暂时不需要的节点")
            if payload.kind == "exhibit":
                item = current_exhibit(c, payload.exhibit_id, user)
                if item is None:
                    fail(404, "展品不存在、不可访问或已撤回公开")
                if c.execute("""SELECT 1 FROM constellation_nodes
                    WHERE user_id=? AND kind='exhibit' AND exhibit_id=?""",
                    (user["id"], payload.exhibit_id)).fetchone():
                    fail(409, "这件展品已经在你的星图里")
                title, exhibit_id = "", payload.exhibit_id
            else:
                title, exhibit_id = payload.title, None
            try:
                cur = c.execute("""INSERT INTO constellation_nodes
                    (user_id,kind,exhibit_id,title,note,origin,created_at)
                    VALUES(?,?,?,?,?,?,?)""",
                    (user["id"], payload.kind, exhibit_id, title, payload.note, "manual", now()))
            except sqlite3.IntegrityError:
                fail(409, "这个节点已经存在，或节点数据无效")
            row = c.execute("SELECT * FROM constellation_nodes WHERE id=?",
                            (cur.lastrowid,)).fetchone()
            return {"node": node_view(c, row, user), "notice": "已加入你的私人星图。"}

    @app.patch("/api/constellation/nodes/{node_id}")
    def update_node(node_id: int, payload: ConstellationNodePatch, user=Depends(require_user)):
        with db() as c:
            row = c.execute("""SELECT * FROM constellation_nodes
                WHERE id=? AND user_id=?""", (node_id, user["id"])).fetchone()
            if row is None:
                fail(404, "星图节点不存在或不属于你")
            view = node_view(c, row, user)
            if view is None or view.get("source_unavailable"):
                fail(409, "原始藏品已不可见；请删除失效节点")
            if payload.title is not None and row["kind"] != "idea":
                fail(400, "展品标题来自原始馆藏，不能在星图中单独改名")
            if payload.title is not None:
                c.execute("UPDATE constellation_nodes SET title=? WHERE id=? AND user_id=?",
                          (payload.title, node_id, user["id"]))
            if payload.note is not None:
                c.execute("UPDATE constellation_nodes SET note=? WHERE id=? AND user_id=?",
                          (payload.note, node_id, user["id"]))
            updated = c.execute("SELECT * FROM constellation_nodes WHERE id=?",
                                (node_id,)).fetchone()
            return {"node": node_view(c, updated, user), "notice": "个人星图档案已更新；原始展品内容未被修改。"}

    @app.delete("/api/constellation/nodes/{node_id}")
    def delete_node(node_id: int, user=Depends(require_user)):
        with db() as c:
            row = c.execute("""SELECT id FROM constellation_nodes
                WHERE id=? AND user_id=?""", (node_id, user["id"])).fetchone()
            if not row:
                fail(404, "星图节点不存在或不属于你")
            c.execute("DELETE FROM constellation_nodes WHERE id=? AND user_id=?",
                      (node_id, user["id"]))
        return {"ok": True, "notice": "节点及其个人连线已删除；原始馆藏不受影响。"}

    @app.post("/api/constellation/edges", status_code=201)
    def create_edge(payload: ConstellationEdgeIn, user=Depends(require_user)):
        if payload.from_node_id == payload.to_node_id:
            fail(400, "一个节点不能连接到自己")
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            owned_node(c, payload.from_node_id, user)
            owned_node(c, payload.to_node_id, user)
            count = c.execute("SELECT COUNT(*) FROM constellation_edges WHERE user_id=?",
                              (user["id"],)).fetchone()[0]
            if count >= MAX_EDGES:
                fail(429, "个人星图最多保存 400 条关联")
            existing = c.execute("""SELECT 1 FROM constellation_edges
                WHERE user_id=? AND kind=? AND
                ((from_node_id=? AND to_node_id=?) OR (from_node_id=? AND to_node_id=?))""",
                (user["id"], payload.kind, payload.from_node_id, payload.to_node_id,
                 payload.to_node_id, payload.from_node_id)).fetchone()
            if existing:
                fail(409, "这两个节点之间已经存在同类型关联")
            try:
                cur = c.execute("""INSERT INTO constellation_edges
                    (user_id,from_node_id,to_node_id,kind,note,created_at)
                    VALUES(?,?,?,?,?,?)""",
                    (user["id"], payload.from_node_id, payload.to_node_id,
                     payload.kind, payload.note, now()))
            except sqlite3.IntegrityError:
                fail(409, "这条关联已经存在")
            return {"id": cur.lastrowid, "notice": "关联已保存为你的个人判断，未经过平台事实核验。"}

    @app.delete("/api/constellation/edges/{edge_id}")
    def delete_edge(edge_id: int, user=Depends(require_user)):
        with db() as c:
            row = c.execute("""SELECT id FROM constellation_edges
                WHERE id=? AND user_id=?""", (edge_id, user["id"])).fetchone()
            if not row:
                fail(404, "关联不存在或不属于你")
            c.execute("DELETE FROM constellation_edges WHERE id=? AND user_id=?",
                      (edge_id, user["id"]))
        return {"ok": True}

    @app.post("/api/constellation/import")
    def import_personal_sources(user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            existing_count = c.execute("SELECT COUNT(*) FROM constellation_nodes WHERE user_id=?",
                                       (user["id"],)).fetchone()[0]
            room = max(0, MAX_NODES - existing_count)
            candidates = []

            # Own exhibits may be private; they remain visible only to their owner.
            for row in c.execute("""SELECT id FROM exhibits WHERE user_id=?
                ORDER BY updated_at DESC,id DESC LIMIT ?""",
                (user["id"], MAX_IMPORT_PER_SOURCE)).fetchall():
                candidates.append((row["id"], "owned"))

            for row in c.execute("""SELECT e.id FROM bookmarks b JOIN exhibits e ON e.id=b.exhibit_id
                WHERE b.user_id=? AND (e.visibility='public' OR e.user_id=?)
                ORDER BY e.created_at DESC,e.id DESC LIMIT ?""",
                (user["id"], user["id"], MAX_IMPORT_PER_SOURCE)).fetchall():
                candidates.append((row["id"], "bookmarked"))

            tables = {r["name"] for r in c.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            if "wonder_adventure_visits" in tables and "wonder_adventures" in tables:
                for row in c.execute("""SELECT v.exhibit_id FROM wonder_adventure_visits v
                    JOIN wonder_adventures a ON a.id=v.adventure_id
                    WHERE a.owner_id=? AND v.exhibit_id IS NOT NULL
                    ORDER BY v.visited_at DESC LIMIT ?""",
                    (user["id"], MAX_IMPORT_PER_SOURCE)).fetchall():
                    candidates.append((row["exhibit_id"], "visited"))

            # memory_views is only populated by the existing opt-in history action.
            if "memory_views" in tables:
                for row in c.execute("""SELECT exhibit_id FROM memory_views
                    WHERE user_id=? ORDER BY last_at DESC LIMIT ?""",
                    (user["id"], MAX_IMPORT_PER_SOURCE)).fetchall():
                    candidates.append((row["exhibit_id"], "history"))

            added = 0
            skipped = 0
            counts = {key: 0 for key in ORIGINS if key != "manual"}
            seen = set()
            for exhibit_id, origin in candidates:
                if exhibit_id in seen:
                    continue
                seen.add(exhibit_id)
                if added >= room:
                    skipped += 1
                    continue
                item = current_exhibit(c, exhibit_id, user)
                if item is None:
                    skipped += 1
                    continue
                if c.execute("""SELECT 1 FROM constellation_nodes
                    WHERE user_id=? AND kind='exhibit' AND exhibit_id=?""",
                    (user["id"], exhibit_id)).fetchone():
                    skipped += 1
                    continue
                c.execute("""INSERT INTO constellation_nodes
                    (user_id,kind,exhibit_id,title,note,origin,created_at)
                    VALUES(?, 'exhibit', ?, '', '', ?, ?)""",
                    (user["id"], exhibit_id, origin, now()))
                added += 1
                counts[origin] = counts.get(origin, 0) + 1
            return {"added": added, "skipped": skipped, "by_source": counts,
                    "notice": "只导入你自己的藏品、心动收藏、本人自标记的参观，以及已主动启用的浏览历史；星图仍只对你可见。"}
