"""V31 · 万物活体博物馆 — transparent, curator-written change chronicles.

A 'living' exhibit is NOT a periodically scraped external page: the curator must
manually record every change, and linked sources are NOT automatically verified.
All public views resolve present permissions and exhibit titles live; followers
never receive snapshots of withdrawn/private records. The watchlist is an
in-app unread counter (not push notifications or a scheduled monitor).
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal
from urllib.parse import urlsplit

from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from parallel_universes import PUBLIC_SCOPE

MAX_ENTRIES = 120
MAX_WATCHES = 120
RECENT_FEED = 28

class ChronicalEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["observation", "milestone", "correction", "discovery"]
    headline: str = Field(min_length=2, max_length=100)
    note: str = Field(min_length=8, max_length=700)
    observed_on: date
    source_url: str = Field(default="", max_length=500)

    @field_validator("source_url")
    @classmethod
    def source_http_only(cls, val):
        v=val.strip()
        if v:
            p=urlsplit(v)
            if p.scheme not in ("https","http") or not p.netloc or p.username or p.password:
                raise ValueError("来源链接只接受无账号密码的 HTTP(S) URL")
        return v

    @model_validator(mode="after")
    def normalize(self):
        self.headline=self.headline.strip()
        self.note=self.note.strip()
        if len(self.headline)<2 or len(self.note)<8:
            raise ValueError("标题至少2字，说明至少8字")
        if self.observed_on>datetime.now(timezone.utc).date():
            raise ValueError("观察日期不能在未来；计划中的事件不能写成已经发生")
        return self

def mount_living_museum(app, db, require_user, maybe_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS living_entries(
          id INTEGER PRIMARY KEY,
          exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          curator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          kind TEXT NOT NULL CHECK(kind IN('observation','milestone','correction','discovery')),
          headline TEXT NOT NULL,
          note TEXT NOT NULL,
          observed_on TEXT NOT NULL,
          source_url TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL,
          withdrawn INTEGER NOT NULL DEFAULT 0 CHECK(withdrawn IN (0,1)),
          withdrawn_at TEXT
        );
        CREATE INDEX IF NOT EXISTS ix_living_entries_exhibit
          ON living_entries(exhibit_id,withdrawn,id DESC);
        CREATE INDEX IF NOT EXISTS ix_living_entries_public
          ON living_entries(withdrawn,id DESC);
        CREATE TABLE IF NOT EXISTS living_watches(
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          last_seen_id INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL,
          PRIMARY KEY(user_id,exhibit_id)
        );
        CREATE INDEX IF NOT EXISTS ix_living_watches_user
          ON living_watches(user_id,exhibit_id);
        """)

    def actual_public(c, exhibit_id):
        return c.execute("""SELECT e.id,e.user_id,e.title,e.description,
            e.domain,e.category,e.time_bucket,e.image_url,u.username AS curator
            FROM exhibits e JOIN users u ON u.id=e.user_id
            WHERE e.id=? AND """+PUBLIC_SCOPE, (exhibit_id,)).fetchone()

    def own(c, exhibit_id, user):
        x=c.execute("""SELECT e.id,e.user_id,e.title,e.description,
            e.domain,e.category,e.time_bucket,e.image_url,u.username AS curator
            FROM exhibits e JOIN users u ON u.id=e.user_id
            WHERE e.id=?""", (exhibit_id,)).fetchone()
        if not x or x["user_id"]!=user["id"]:
            fail(404,"只有原作者可以维护该藏品的变化档案")
        return x

    def visible(c, exhibit_id, user):
        x=actual_public(c,exhibit_id)
        if x: return x
        if user:
            own_row=c.execute("""SELECT e.id,e.user_id,e.title,e.description,
              e.domain,e.category,e.time_bucket,e.image_url,u.username AS curator
              FROM exhibits e JOIN users u ON u.id=e.user_id
              WHERE e.id=? AND e.user_id=?""", (exhibit_id,user["id"])).fetchone()
            if own_row: return own_row
        fail(404,"藏品或公开变化档案不存在")

    def item(x):
        return {"id":x["id"],"title":x["title"],"description":x["description"][:240],
            "domain":x["domain"],"category":x["category"],"time_bucket":x["time_bucket"],
            "image_url":x["image_url"],"curator":x["curator"]}

    def entry(x):
        return {"id":x["id"],"exhibit_id":x["exhibit_id"],
            "kind":x["kind"],"headline":x["headline"],"note":x["note"],
            "observed_on":x["observed_on"],"source_url":x["source_url"],
            "created_at":x["created_at"],
            "source_label":("馆长提供来源链接（未经平台核验）" if x["source_url"]
                            else "馆长自述观察（未附外部来源）")}

    def changes(c, exhibit_id, limit=MAX_ENTRIES):
        return c.execute("""SELECT * FROM living_entries
          WHERE exhibit_id=? AND withdrawn=0
          ORDER BY observed_on DESC,id DESC LIMIT ?""",
          (exhibit_id,limit)).fetchall()

    def last_id(c,exhibit_id):
        return c.execute("""SELECT COALESCE(MAX(id),0) FROM living_entries
          WHERE exhibit_id=? AND withdrawn=0""",(exhibit_id,)).fetchone()[0]

    @app.get("/api/living/feed")
    def feed(user=Depends(maybe_user)):
        with db() as c:
            rows=c.execute("""SELECT l.*,
               e.title,e.domain,e.category,e.time_bucket,e.description,e.image_url,
               u.username AS curator
               FROM living_entries l JOIN exhibits e ON e.id=l.exhibit_id
               JOIN users u ON u.id=e.user_id
               WHERE l.withdrawn=0 AND l.curator_id=e.user_id AND """+PUBLIC_SCOPE+"""
               ORDER BY l.id DESC LIMIT ?""",(RECENT_FEED,)).fetchall()
            return {"items":[{"exhibit":item(x),"entry":entry(x)} for x in rows],
                "notice":"这是馆长主动记录的变化，按录入时间排序，不是实时数据抓取。链接仅供读者核验，平台未自动核实事实。"}

    @app.get("/api/living/pulse")
    def pulse():
        with db() as c:
            rows=c.execute("""SELECT l.id,e.id AS exhibit_id,e.domain
                 FROM living_entries l JOIN exhibits e ON e.id=l.exhibit_id
                 WHERE l.withdrawn=0 AND l.curator_id=e.user_id AND """+PUBLIC_SCOPE+"""
                  AND l.created_at>=datetime('now','-30 days')
                 ORDER BY l.id DESC LIMIT 10000""").fetchall()
            domains={}
            for r in rows: domains[r["domain"]]=domains.get(r["domain"],0)+1
            return {"recorded_changes_30d":len(rows),
                "active_exhibits_30d":len({r["exhibit_id"] for r in rows}),
                "domains":[{"domain":name,"count":num} for name,num in
                           sorted(domains.items(),key=lambda p:(-p[1],p[0]))[:8]],
                "notice":"30天数字代表馆长录入的公开观察记录；不是现实事件总量或世界实时监测。最多统计最近1万条。"}

    @app.get("/api/living/watchlist")
    def watchlist(user=Depends(require_user)):
        with db() as c:
            rows=c.execute("""SELECT * FROM living_watches WHERE user_id=?
                ORDER BY created_at DESC,exhibit_id DESC LIMIT ?""",
                (user["id"],MAX_WATCHES)).fetchall()
            result=[]
            for w in rows:
                source=actual_public(c,w["exhibit_id"])
                if source is None:
                    result.append({"exhibit_id":w["exhibit_id"],"available":False,
                        "exhibit":None,"unread":0,"last_seen_id":w["last_seen_id"]})
                    continue
                unread=c.execute("""SELECT COUNT(*) FROM living_entries
                    WHERE exhibit_id=? AND withdrawn=0 AND id>?""",
                    (w["exhibit_id"],w["last_seen_id"])).fetchone()[0]
                result.append({"exhibit_id":w["exhibit_id"],"available":True,
                    "exhibit":item(source),"unread":unread,"last_seen_id":w["last_seen_id"]})
            return {"items":result,"unread":sum(x["unread"] for x in result),
                "notice":"仅站内待阅数字；没有后台定时爬取或自动推送。撤回公开的来源不显示旧标题。"}

    @app.get("/api/living/compare")
    def compare(left_id:int=Query(ge=1),right_id:int=Query(ge=1),user=Depends(maybe_user)):
        if left_id==right_id:
            fail(400,"请选择两件不同的公开藏品")
        with db() as c:
            left=actual_public(c,left_id)
            right=actual_public(c,right_id)
            if left is None or right is None:
                fail(404,"仅能对比两件目前真正公开的藏品")
            a=changes(c,left_id,30)
            b=changes(c,right_id,30)
            return {"left":{"exhibit":item(left),"entries":[entry(x) for x in a]},
                "right":{"exhibit":item(right),"entries":[entry(x) for x in b]},
                "notice":"两条时间线仅按馆长所填观察日期并列展示；不推断因果、不核验来源，也不称为自动同步。"}

    @app.get("/api/living/exhibits/{exhibit_id}")
    def detail(exhibit_id:int,user=Depends(maybe_user)):
        with db() as c:
            src=visible(c,exhibit_id,user)
            owner=bool(user and src["user_id"]==user["id"])
            watch=None
            if user:
                watch=c.execute("""SELECT * FROM living_watches WHERE user_id=? AND exhibit_id=?""",
                                (user["id"],exhibit_id)).fetchone()
            events=changes(c,exhibit_id)
            return {"exhibit":item(src),
                "entries":[entry(x) for x in events],
                "is_owner":owner,
                "watching":bool(watch),
                "unread":sum(x["id"]>watch["last_seen_id"] for x in events) if watch else 0,
                "max_entries":MAX_ENTRIES,
                "notice":"时间线是原作者自行维护的档案；来源链接未经平台验证，观察日期不是原始作品的年代。"}

    @app.post("/api/living/exhibits/{exhibit_id}/entries",status_code=201)
    def record(exhibit_id:int,payload:ChronicalEntry,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            own(c,exhibit_id,user)
            count=c.execute("""SELECT COUNT(*) FROM living_entries WHERE exhibit_id=?""",
                            (exhibit_id,)).fetchone()[0]
            if count>=MAX_ENTRIES:
                fail(429,"单件藏品最多120条变化记录（包含已撤回的记录）")
            cur=c.execute("""INSERT INTO living_entries(
                exhibit_id,curator_id,kind,headline,note,observed_on,source_url,created_at)
                VALUES(?,?,?,?,?,?,?,?)""",
                (exhibit_id,user["id"],payload.kind,payload.headline,payload.note,
                 payload.observed_on.isoformat(),payload.source_url,now()))
            row=c.execute("SELECT * FROM living_entries WHERE id=?",(cur.lastrowid,)).fetchone()
            return {"entry":entry(row),
                "notice":"变化已由作者录入；未自动验证外部来源或实际发生时间。"}

    @app.post("/api/living/entries/{entry_id}/withdraw")
    def withdraw(entry_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            x=c.execute("SELECT * FROM living_entries WHERE id=?",(entry_id,)).fetchone()
            if not x or x["curator_id"]!=user["id"]:
                fail(404,"只能撤回自己提交的变化记录")
            if x["withdrawn"]:
                fail(409,"记录已撤回")
            c.execute("""UPDATE living_entries SET withdrawn=1,withdrawn_at=?
                WHERE id=?""",(now(),entry_id))
            return {"ok":True,"notice":"记录已隐藏；保留内部撤回标记以防误计数。"}

    @app.post("/api/living/exhibits/{exhibit_id}/watch")
    def watch(exhibit_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            x=actual_public(c,exhibit_id)
            if not x: fail(404,"只能关注当前确实公开的活体展品")
            saved=c.execute("""SELECT * FROM living_watches
               WHERE user_id=? AND exhibit_id=?""",(user["id"],exhibit_id)).fetchone()
            if saved:
                return {"watching":True,"notice":"已在你的变化观察清单中"}
            count=c.execute("SELECT COUNT(*) FROM living_watches WHERE user_id=?",
                            (user["id"],)).fetchone()[0]
            if count>=MAX_WATCHES: fail(429,"最多同时关注120件展品")
            c.execute("""INSERT INTO living_watches(user_id,exhibit_id,last_seen_id,created_at)
                VALUES(?,?,?,?)""",(user["id"],exhibit_id,last_id(c,exhibit_id),now()))
            return {"watching":True,"notice":"开始关注此刻以后的馆长更新；既有记录不算未读。"}

    @app.delete("/api/living/exhibits/{exhibit_id}/watch")
    def unwatch(exhibit_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            c.execute("DELETE FROM living_watches WHERE user_id=? AND exhibit_id=?",
                      (user["id"],exhibit_id))
            return {"watching":False}

    @app.post("/api/living/exhibits/{exhibit_id}/seen")
    def mark_seen(exhibit_id:int,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            if actual_public(c,exhibit_id) is None:
                fail(404,"来源已经不公开，不能标记为已阅")
            watch=c.execute("""SELECT * FROM living_watches
                WHERE user_id=? AND exhibit_id=?""",(user["id"],exhibit_id)).fetchone()
            if watch is None: fail(404,"尚未关注该展品")
            c.execute("""UPDATE living_watches SET last_seen_id=?
                WHERE user_id=? AND exhibit_id=?""",
                (last_id(c,exhibit_id),user["id"],exhibit_id))
            return {"ok":True,"notice":"当前公开变更已标为已阅；以后新增的馆长更新将重新计入。"}
