"""V28 · Private constellation voyages, built solely from the owner's saved edges.

A journey is a live shortest path, not an AI inference or a verified fact. We save
node IDs and private checkpoint times, never third-party exhibit title snapshots.
"""
from __future__ import annotations

from collections import deque
from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_ROUTES = 20


class VoyageEndpoints(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_node_id: int = Field(ge=1)
    end_node_id: int = Field(ge=1)

    @model_validator(mode="after")
    def distinct(self):
        if self.start_node_id == self.end_node_id:
            raise ValueError("起点和终点不能相同")
        return self


class SaveVoyage(VoyageEndpoints):
    name: str = Field(min_length=1, max_length=60)

    @model_validator(mode="after")
    def clean_name(self):
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("航线名称不能为空")
        return self


def shortest_path(graph, start, end):
    """Use ONLY live, manually persisted user edges. No automatic suggestions."""
    nodes = {n["id"]: n for n in graph["nodes"] if not n.get("source_unavailable")}
    if start not in nodes or end not in nodes:
        return None
    adjacency = {nid: [] for nid in nodes}
    for edge in sorted(graph["edges"], key=lambda e: e["id"]):
        a, b = edge["from_node_id"], edge["to_node_id"]
        if a in nodes and b in nodes and a != b:
            adjacency[a].append((b, edge))
            adjacency[b].append((a, edge))
    seen = {start: None}
    queue = deque([start])
    while queue and end not in seen:
        current = queue.popleft()
        for neighbor, edge in adjacency[current]:
            if neighbor not in seen:
                seen[neighbor] = (current, edge)
                queue.append(neighbor)
    if end not in seen:
        return None

    node_ids = [end]
    edges = []
    while node_ids[-1] != start:
        previous, edge = seen[node_ids[-1]]
        edges.append({
            "id": edge["id"], "kind": edge["kind"], "label": edge["label"],
            "note": edge["note"], "source": "user", "verified": False,
        })
        node_ids.append(previous)
    node_ids.reverse()
    edges.reverse()
    return {
        "path": [{
            "node_id": n, "title": nodes[n]["title"], "kind": nodes[n]["kind"],
            "exhibit_id": nodes[n].get("exhibit_id"),
            "domain": nodes[n].get("domain", ""),
        } for n in node_ids],
        "legs": edges,
    }


def mount_constellation_voyages(app, db, require_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS constellation_voyages(
          id INTEGER PRIMARY KEY,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          start_node_id INTEGER NOT NULL REFERENCES constellation_nodes(id) ON DELETE CASCADE,
          end_node_id INTEGER NOT NULL REFERENCES constellation_nodes(id) ON DELETE CASCADE,
          name TEXT NOT NULL,
          created_at TEXT NOT NULL,
          CHECK(start_node_id <> end_node_id)
        );
        CREATE INDEX IF NOT EXISTS ix_voyages_owner
          ON constellation_voyages(user_id, created_at DESC);
        CREATE TABLE IF NOT EXISTS constellation_voyage_checkpoints(
          voyage_id INTEGER NOT NULL REFERENCES constellation_voyages(id) ON DELETE CASCADE,
          node_id INTEGER NOT NULL REFERENCES constellation_nodes(id) ON DELETE CASCADE,
          marked_at TEXT NOT NULL,
          PRIMARY KEY(voyage_id, node_id)
        );
        """)

    # Graph serialization in V27 already enforces per-user access and
    # live fantasy/studio/sandbox visibility revocations.
    get_graph = app.state.constellation_graph

    def owned(c, voyage_id, user):
        row = c.execute(
            "SELECT * FROM constellation_voyages WHERE id=? AND user_id=?",
            (voyage_id, user["id"])).fetchone()
        if row is None:
            fail(404, "私人航线不存在或不属于你")
        return row

    def current(c, user, start, end, graph=None):
        graph = graph if graph is not None else get_graph(c, user)
        live_ids = {n["id"] for n in graph["nodes"]
                    if not n.get("source_unavailable")}
        if start not in live_ids or end not in live_ids:
            return None, "端点已不可见或不存在"
        result = shortest_path(graph, start, end)
        if not result:
            return None, "当前没有仅由已保存个人连线组成的路径"
        return result, None

    def view(c, row, user, graph):
        result, reason = current(c, user, row["start_node_id"],
                                 row["end_node_id"], graph)
        if result is None:
            # Never return a stored route caption or old connected-leg notes
            # while a source is unavailable or the route is disconnected.
            return {"id": row["id"], "connected": False, "name": "航线暂不可用",
                    "path": [], "legs": [], "marked_count": 0,
                    "created_at": row["created_at"], "reason": reason}
        checkpoints = {r["node_id"]: r["marked_at"] for r in c.execute(
            "SELECT node_id,marked_at FROM constellation_voyage_checkpoints WHERE voyage_id=?",
            (row["id"],)).fetchall()}
        path = [{**n, "marked": n["node_id"] in checkpoints,
                 "marked_at": checkpoints.get(n["node_id"])} for n in result["path"]]
        return {
            "id": row["id"], "connected": True, "name": row["name"],
            "path": path, "legs": result["legs"],
            "marked_count": sum(bool(n["marked"]) for n in path),
            "created_at": row["created_at"], "reason": None,
        }

    @app.post("/api/constellation/voyages/preview")
    def preview(payload: VoyageEndpoints, user=Depends(require_user)):
        with db() as c:
            route, reason = current(c, user, payload.start_node_id, payload.end_node_id)
            if route is None:
                return {"connected": False, "path": [], "legs": [], "reason": reason,
                        "notice": "只沿本人已保存的关联寻找路径，不使用系统建议或推断。"}
            return {"connected": True, **route, "reason": None,
                    "notice": "仅由个人连线形成的最短步数路线，不代表事实因果或证据链。"}

    @app.get("/api/constellation/voyages")
    def list_voyages(user=Depends(require_user)):
        with db() as c:
            graph = get_graph(c, user)
            rows = c.execute("""SELECT * FROM constellation_voyages
                WHERE user_id=? ORDER BY created_at DESC,id DESC LIMIT ?""",
                (user["id"], MAX_ROUTES)).fetchall()
            return {"items": [view(c, row, user, graph) for row in rows],
                    "max_routes": MAX_ROUTES,
                    "notice": "航线和打卡仅本人可见；打卡由本人手动标记，不验证实际参观或知识正确性。"}

    @app.post("/api/constellation/voyages", status_code=201)
    def save_voyage(payload: SaveVoyage, user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT COUNT(*) FROM constellation_voyages WHERE user_id=?",
                         (user["id"],)).fetchone()[0] >= MAX_ROUTES:
                fail(429, "个人最多保存 20 条星图航线")
            route, reason = current(c, user, payload.start_node_id, payload.end_node_id)
            if not route:
                fail(409, reason or "当前无法创建航线")
            cur = c.execute("""INSERT INTO constellation_voyages
                (user_id,start_node_id,end_node_id,name,created_at)
                VALUES(?,?,?,?,?)""", (user["id"], payload.start_node_id,
                     payload.end_node_id, payload.name, now()))
            row = owned(c, cur.lastrowid, user)
            graph = get_graph(c, user)
            return {"voyage": view(c, row, user, graph)}

    @app.get("/api/constellation/voyages/{voyage_id}")
    def get_voyage(voyage_id: int, user=Depends(require_user)):
        with db() as c:
            row = owned(c, voyage_id, user)
            return view(c, row, user, get_graph(c, user))

    @app.put("/api/constellation/voyages/{voyage_id}/checkpoints/{node_id}")
    def mark_checkpoint(voyage_id: int, node_id: int, user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            row = owned(c, voyage_id, user)
            route, reason = current(c, user, row["start_node_id"], row["end_node_id"])
            if not route or node_id not in {x["node_id"] for x in route["path"]}:
                fail(409, "只能标记当前连通且可访问的航线节点")
            c.execute("""INSERT INTO constellation_voyage_checkpoints(voyage_id,node_id,marked_at)
                VALUES(?,?,?) ON CONFLICT(voyage_id,node_id)
                DO UPDATE SET marked_at=excluded.marked_at""",
                (voyage_id, node_id, now()))
            return {"ok": True, "notice": "这只是你的私人探索标记，不代表实际参观认证。"}

    @app.delete("/api/constellation/voyages/{voyage_id}/checkpoints/{node_id}")
    def unmark_checkpoint(voyage_id: int, node_id: int, user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            owned(c, voyage_id, user)
            c.execute("""DELETE FROM constellation_voyage_checkpoints
                WHERE voyage_id=? AND node_id=?""", (voyage_id, node_id))
        return {"ok": True}

    @app.delete("/api/constellation/voyages/{voyage_id}")
    def delete_voyage(voyage_id: int, user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            owned(c, voyage_id, user)
            c.execute("DELETE FROM constellation_voyages WHERE id=? AND user_id=?",
                      (voyage_id, user["id"]))
        return {"ok": True, "notice": "航线和私人进度已删除，星图节点与连线保持不变。"}
