"""V41: one authentic exhibit as the center of explainable, reversible discovery.

Only read actual current exhibit records; metadata similarity is NOT historical causation.
Manual links are curator-authored *claims*, not verified facts.
PUBLIC_SCOPE is reused for every non-owned source: withdrawing an upstream
studio/fantasy/sandbox container immediately masks its former public children.
"""
from __future__ import annotations

from fastapi import Depends

from connections_api import LINK_KINDS, suggestion
from parallel_universes import PUBLIC_SCOPE

MAX_PEERS = 4
SCAN_LIMIT = 500


def mount_object_hub(app, db, maybe_user, fail):
    def row_for(c, exhibit_id, viewer):
        # Returning a row to its author is allowed; every other visitor sees
        # only sources that satisfy the full current publication envelope.
        return c.execute(
            """SELECT e.id,e.user_id,e.title,e.visibility,e.series,e.domain,
                      e.category,e.time_bucket,e.tags,u.username AS owner
               FROM exhibits e JOIN users u ON u.id=e.user_id
               WHERE e.id=? AND (e.user_id=? OR (""" + PUBLIC_SCOPE + """))""",
            (exhibit_id, viewer),
        ).fetchone()

    def slim(row):
        return {
            "id": row["id"], "title": row["title"], "owner": row["owner"],
            "domain": row["domain"], "category": row["category"],
            "series": row["series"], "time_bucket": row["time_bucket"],
        }

    def tags(row):
        return [s.strip() for s in (row["tags"] or "").replace("，", ",").split(",") if s.strip()]

    @app.get("/api/exhibits/{exhibit_id}/hub")
    def object_hub(exhibit_id: int, user=Depends(maybe_user)):
        viewer = user["id"] if user else -1
        with db() as c:
            source = row_for(c, exhibit_id, viewer)
            if source is None:
                fail(404, "展品不存在或没有访问权限")
            root = dict(source)
            public = c.execute(
                "SELECT 1 FROM exhibits e WHERE e.id=? AND " + PUBLIC_SCOPE,
                (exhibit_id,),
            ).fetchone() is not None
            root_node = slim(root)
            root_node["is_public"] = public
            groups = {"curator": [], "metadata": [], "time": []}
            seen = {exhibit_id}

            # Submitted statements from the original owner, in either direction.
            # Do not infer their truth or grant access to a hidden endpoint.
            manual = c.execute(
                """SELECT l.*, u.username AS author FROM exhibit_links l
                   JOIN users u ON u.id=l.author_id
                   WHERE l.from_id=? OR l.to_id=?
                   ORDER BY l.id DESC LIMIT 140""",
                (exhibit_id, exhibit_id),
            ).fetchall()
            for link in manual:
                other_id = link["to_id"] if link["from_id"] == exhibit_id else link["from_id"]
                if other_id in seen:
                    continue
                other = row_for(c, other_id, viewer)
                if other is None:
                    continue
                groups["curator"].append({
                    **slim(other), "source": "curator",
                    "kind": LINK_KINDS.get(link["kind"], "馆长关联"),
                    "reason": link["explanation"],
                    "author": link["author"],
                    "verified": False,
                })
                seen.add(other_id)
                if len(groups["curator"]) >= MAX_PEERS:
                    break

            # Metadata similarities are drawn ONLY from current public sources.
            # Recency bounds the scan; ranking uses deterministic score and ID.
            public_rows = c.execute(
                """SELECT e.id,e.user_id,e.title,e.visibility,e.series,e.domain,
                          e.category,e.time_bucket,e.tags,u.username AS owner
                   FROM exhibits e JOIN users u ON u.id=e.user_id
                   WHERE """ + PUBLIC_SCOPE + """
                   ORDER BY e.id DESC LIMIT ?""", (SCAN_LIMIT,)
            ).fetchall()
            ranked = []
            for other in public_rows:
                if other["id"] in seen:
                    continue
                metadata = suggestion(
                    {**root, "tags": tags(root)},
                    {**dict(other), "tags": tags(other)},
                )
                if metadata is not None:
                    ranked.append((metadata["weight"], other["id"], other, metadata["explanation"]))
            ranked.sort(key=lambda value: (-value[0], value[1]))
            for weight, _, other, reason in ranked[:MAX_PEERS]:
                groups["metadata"].append({
                    **slim(other), "source": "metadata", "kind": "元数据相似",
                    "reason": reason, "author": None, "verified": False,
                })
                seen.add(other["id"])

            era = root["time_bucket"]
            if era and era != "时间不详":
                for other in public_rows:
                    if other["id"] in seen or other["time_bucket"] != era:
                        continue
                    groups["time"].append({
                        **slim(other), "source": "time", "kind": "处于相同年代范围",
                        "reason": "两件藏品均标注为「" + era + "」，仅表示宽泛年代桶相同，不等于实际发生过联系。",
                        "author": None, "verified": False,
                    })
                    seen.add(other["id"])
                    if len(groups["time"]) >= MAX_PEERS:
                        break

            return {
                "focus": root_node,
                "groups": groups,
                "total": sum(len(x) for x in groups.values()),
                "limits": {"max_per_group": MAX_PEERS, "sample_size": SCAN_LIMIT},
                "method": "馆长关联优先；其次按共同标签、细类、领域排序；同年代单独列出。",
                "notice": (
                    "馆长关联属于作者提交、未经平台核实的陈述；元数据及年代相似并不证明因果关系。"
                    "关联仅展示当前有权访问的真实原始藏品；撤回或变私密后不再展示。"
                ),
            }
