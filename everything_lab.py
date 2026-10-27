"""V20 万物实验室: mixed-media curated atlases, sealed time capsules and daily real-source discovery.

Reality and original fiction are always separately attributed; no fake users,
institution endorsements, automatic history, or exposure of withdrawn collections.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from typing import Literal
from fastapi import Depends, Query
from pydantic import BaseModel, Field, field_validator
from taxonomy import DOMAINS

NOTICE = "现实投稿未经本站独立考证；原创世界明确标注虚构。收藏不转移所有权。"
CURATION_STYLES = ("星际档案", "古典陈列", "数字考古", "奇物手札", "自然秘境", "未来实验室")


def strip_nonempty(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("内容不能为空")
    return value


class AlbumDraft(BaseModel):
    title: str = Field(min_length=2, max_length=70)
    description: str = Field(default="", max_length=500)
    style: Literal[CURATION_STYLES] = "星际档案"

    @field_validator("title")
    @classmethod
    def title_required(cls, value):
        return strip_nonempty(value)


class AlbumVisibility(BaseModel):
    visibility: Literal["private", "public"]


class AlbumEntry(BaseModel):
    kind: Literal["exhibit", "world"]
    source_id: int = Field(ge=1)


class CapsuleDraft(BaseModel):
    title: str = Field(min_length=2, max_length=70)
    body: str = Field(min_length=20, max_length=1800)
    unlock_date: date

    @field_validator("title", "body")
    @classmethod
    def validate_nonempty(cls, value):
        return strip_nonempty(value)


def mount_everything_lab(app, db, require_user, maybe_user, now, fail):
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS lab_albums(
          id INTEGER PRIMARY KEY,
          owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
          style TEXT NOT NULL,
          visibility TEXT NOT NULL DEFAULT 'private'
            CHECK(visibility IN ('private','public')),
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_lab_albums_public ON lab_albums(visibility,id DESC);
        CREATE TABLE IF NOT EXISTS lab_entries(
          id INTEGER PRIMARY KEY,
          album_id INTEGER NOT NULL REFERENCES lab_albums(id) ON DELETE CASCADE,
          kind TEXT NOT NULL CHECK(kind IN ('exhibit','world')),
          exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE CASCADE,
          world_id INTEGER REFERENCES fantasy_worlds(id) ON DELETE CASCADE,
          created_at TEXT NOT NULL,
          CHECK ((kind='exhibit' AND exhibit_id IS NOT NULL AND world_id IS NULL)
              OR (kind='world' AND world_id IS NOT NULL AND exhibit_id IS NULL)),
          UNIQUE(album_id,exhibit_id), UNIQUE(album_id,world_id)
        );
        CREATE INDEX IF NOT EXISTS ix_lab_entries_album ON lab_entries(album_id,id);
        CREATE TABLE IF NOT EXISTS lab_capsules(
          id INTEGER PRIMARY KEY,
          owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          title TEXT NOT NULL, body TEXT NOT NULL, unlock_date TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_lab_capsule_owner ON lab_capsules(owner_id,id DESC);
        CREATE TABLE IF NOT EXISTS lab_stamps(
          id INTEGER PRIMARY KEY,
          owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          stamped_date TEXT NOT NULL,
          domain TEXT NOT NULL,
          kind TEXT NOT NULL CHECK(kind IN ('exhibit','world')),
          exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE CASCADE,
          world_id INTEGER REFERENCES fantasy_worlds(id) ON DELETE CASCADE,
          created_at TEXT NOT NULL,
          CHECK ((kind='exhibit' AND exhibit_id IS NOT NULL AND world_id IS NULL)
              OR (kind='world' AND world_id IS NOT NULL AND exhibit_id IS NULL)),
          UNIQUE(owner_id,stamped_date)
        );
        CREATE INDEX IF NOT EXISTS ix_lab_stamps_owner ON lab_stamps(owner_id,id DESC);
        """)

    def today():
        return datetime.fromisoformat(now().replace("Z", "+00:00")).astimezone(timezone.utc).date()

    def album_owner(c, album_id, user):
        row=c.execute("SELECT * FROM lab_albums WHERE id=? AND owner_id=?",
                      (album_id,user["id"])).fetchone()
        if not row: fail(404,"图鉴不存在或不是你的")
        return row

    def album_visible(c, album_id, user):
        row=c.execute("""SELECT a.*,u.username creator FROM lab_albums a
            JOIN users u ON u.id=a.owner_id WHERE a.id=?""",(album_id,)).fetchone()
        if not row or (row["visibility"]!="public" and
                       (not user or row["owner_id"]!=user["id"])):
            fail(404,"图鉴不存在或未公开")
        return row

    def source_data(c, kind, source_id, user, public_only=False):
        if kind=="exhibit":
            row=c.execute("""SELECT e.id,e.title,e.description,e.category,e.domain,e.time_bucket,
                e.visibility,e.user_id,e.image_url,e.source_url,u.username creator,
                fw.visibility fantasy_world_visibility
                FROM exhibits e JOIN users u ON u.id=e.user_id
                LEFT JOIN fantasy_relics fr ON fr.exhibit_id=e.id
                LEFT JOIN fantasy_worlds fw ON fw.id=fr.world_id WHERE e.id=?""",
                (source_id,)).fetchone()
            if not row: return None
            public=(row["visibility"]=="public" and
                    row["fantasy_world_visibility"] in (None,"public"))
            if not public and (public_only or not user or row["user_id"]!=user["id"]):
                return None
            return {"kind":"exhibit","id":source_id,"title":row["title"],
                    "description":row["description"],"category":row["category"],
                    "domain":row["domain"],"time_bucket":row["time_bucket"],
                    "creator":row["creator"],"image_url":row["image_url"] if public else "",
                    "fictional":row["fantasy_world_visibility"] is not None,
                    "public":public,"provenance":"虚构世界奇物" if row["fantasy_world_visibility"] is not None else "社区投稿／未独立核验"}
        row=c.execute("""SELECT w.id,w.name,w.theme,w.law,w.intro,w.visibility,
            w.user_id,u.username creator FROM fantasy_worlds w
            JOIN users u ON u.id=w.user_id WHERE w.id=?""",(source_id,)).fetchone()
        if not row: return None
        public=row["visibility"]=="public"
        if not public and (public_only or not user or row["user_id"]!=user["id"]):
            return None
        return {"kind":"world","id":source_id,"title":row["name"],
                "description":row["intro"],"category":row["theme"],"domain":"原创与个人创作",
                "time_bucket":"虚构世界纪年","creator":row["creator"],
                "image_url":"","law":row["law"],"fictional":True,"public":public,
                "provenance":"原创虚构世界"}

    def serialize_album(c, row, user, details=False):
        owner=bool(user and row["owner_id"]==user["id"])
        out={"id":row["id"],"title":row["title"],"description":row["description"],
             "style":row["style"],"visibility":row["visibility"],
             "creator":row["creator"] if "creator" in row.keys() else None,
             "is_owner":owner,"created_at":row["created_at"],"fictional":False}
        if details:
            entries=c.execute("""SELECT id,kind,exhibit_id,world_id FROM lab_entries
                WHERE album_id=? ORDER BY id ASC LIMIT 24""",(row["id"],)).fetchall()
            resolved=[]
            for entry in entries:
                src=source_data(c,entry["kind"],
                                entry["exhibit_id"] if entry["kind"]=="exhibit" else entry["world_id"],
                                user,public_only=not owner)
                if src is not None:
                    resolved.append({"entry_id":entry["id"],**src})
            out["items"]=resolved
            out["visible_count"]=len(resolved)
        return out

    def daily_pick(c, domain, kind, current):
        if domain!="全部" and domain not in DOMAINS:
            fail(422,"无效的主题领域")
        candidates=[]
        if kind in ("all","exhibit"):
            if domain=="全部":
                posts=c.execute("""SELECT id FROM exhibits WHERE visibility='public'
                    ORDER BY id DESC LIMIT 400""").fetchall()
            else:
                posts=c.execute("""SELECT id FROM exhibits WHERE visibility='public' AND domain=?
                    ORDER BY id DESC LIMIT 400""",(domain,)).fetchall()
            for post in posts:
                src=source_data(c,"exhibit",post["id"],None,public_only=True)
                if src:candidates.append(src)
        if domain=="全部" and kind in ("all","world"):
            worlds=c.execute("""SELECT id FROM fantasy_worlds WHERE visibility='public'
                ORDER BY id DESC LIMIT 120""").fetchall()
            for w in worlds:
                src=source_data(c,"world",w["id"],None,public_only=True)
                if src:candidates.append(src)
        if not candidates:return None
        candidates.sort(key=lambda x:(x["kind"],x["id"]))
        code=f"{current.isoformat()}|{domain}|{kind}".encode("utf-8")
        return candidates[int.from_bytes(sha256(code).digest()[:8],"big")%len(candidates)]

    @app.get("/api/lab/config")
    def config():
        return {"styles":CURATION_STYLES,"domains":["全部",*DOMAINS],
                "max_albums":12,"max_album_items":24,"max_capsules":30,
                "notice":NOTICE,"today_utc":today().isoformat()}

    @app.get("/api/lab/albums")
    def albums(scope:Literal["public","mine"]="public", user=Depends(maybe_user)):
        if scope=="mine" and not user:fail(401,"登录后才能查看个人图鉴")
        with db() as c:
            if scope=="mine":
                rows=c.execute("""SELECT a.*,u.username creator FROM lab_albums a
                    JOIN users u ON u.id=a.owner_id WHERE owner_id=? ORDER BY a.id DESC LIMIT 12""",
                    (user["id"],)).fetchall()
            else:
                rows=c.execute("""SELECT a.*,u.username creator FROM lab_albums a
                    JOIN users u ON u.id=a.owner_id WHERE a.visibility='public'
                    ORDER BY a.id DESC LIMIT 60""").fetchall()
            return {"items":[serialize_album(c,r,user) for r in rows],"notice":NOTICE}

    @app.post("/api/lab/albums",status_code=201)
    def create_album(data:AlbumDraft,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT COUNT(*) FROM lab_albums WHERE owner_id=?",(user["id"],)).fetchone()[0]>=12:
                fail(429,"一个账号最多建立十二册图鉴")
            at=now()
            cur=c.execute("""INSERT INTO lab_albums
                (owner_id,title,description,style,created_at,updated_at) VALUES(?,?,?,?,?,?)""",
                (user["id"],data.title,data.description.strip(),data.style,at,at))
            return {"id":cur.lastrowid,"visibility":"private"}

    @app.get("/api/lab/albums/{album_id}")
    def album_detail(album_id:int,user=Depends(maybe_user)):
        with db() as c:
            row=album_visible(c,album_id,user)
            return {**serialize_album(c,row,user,True),"notice":NOTICE}

    @app.post("/api/lab/albums/{album_id}/entries",status_code=201)
    def add_entry(album_id:int,data:AlbumEntry,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            album=album_owner(c,album_id,user)
            src=source_data(c,data.kind,data.source_id,user)
            if not src:fail(404,"来源不存在或不可访问")
            if album["visibility"]=="public" and not src["public"]:
                fail(409,"公开图鉴只能加入仍公开的来源")
            if c.execute("SELECT COUNT(*) FROM lab_entries WHERE album_id=?",(album_id,)).fetchone()[0]>=24:
                fail(429,"每册图鉴最多二十四件事物")
            exists=c.execute("""SELECT 1 FROM lab_entries WHERE album_id=? AND kind=?
                AND COALESCE(exhibit_id,world_id)=?""",(album_id,data.kind,data.source_id)).fetchone()
            if exists:fail(409,"这一件已经在图鉴里")
            cur=c.execute("""INSERT INTO lab_entries
                (album_id,kind,exhibit_id,world_id,created_at) VALUES(?,?,?,?,?)""",
                (album_id,data.kind,data.source_id if data.kind=="exhibit" else None,
                 data.source_id if data.kind=="world" else None,now()))
            c.execute("UPDATE lab_albums SET updated_at=? WHERE id=?",(now(),album_id))
            return {"id":cur.lastrowid,"item":src}

    @app.delete("/api/lab/albums/{album_id}/entries/{entry_id}")
    def remove_entry(album_id:int,entry_id:int,user=Depends(require_user)):
        with db() as c:
            album_owner(c,album_id,user)
            if c.execute("DELETE FROM lab_entries WHERE id=? AND album_id=?",
                         (entry_id,album_id)).rowcount==0:fail(404,"该事物不在图鉴中")
            return {"ok":True}

    @app.patch("/api/lab/albums/{album_id}/visibility")
    def publish_album(album_id:int,data:AlbumVisibility,user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            album_owner(c,album_id,user)
            if data.visibility=="public":
                entries=c.execute("""SELECT kind,exhibit_id,world_id FROM lab_entries
                    WHERE album_id=?""",(album_id,)).fetchall()
                for entry in entries:
                    sid=entry["exhibit_id"] if entry["kind"]=="exhibit" else entry["world_id"]
                    if source_data(c,entry["kind"],sid,user,public_only=True) is None:
                        fail(409,"图鉴含有私人或撤回的来源，移除后才能公开")
            c.execute("UPDATE lab_albums SET visibility=?,updated_at=? WHERE id=?",
                      (data.visibility,now(),album_id))
            return {"visibility":data.visibility}

    @app.delete("/api/lab/albums/{album_id}")
    def remove_album(album_id:int,user=Depends(require_user)):
        with db() as c:
            album_owner(c,album_id,user)
            c.execute("DELETE FROM lab_albums WHERE id=?",(album_id,))
            return {"ok":True}

    @app.post("/api/lab/capsules",status_code=201)
    def create_capsule(data:CapsuleDraft,user=Depends(require_user)):
        current=today()
        if not current < data.unlock_date <= current+timedelta(days=3650):
            fail(422,"开启日期须在未来十年以内，以 UTC 日期为准")
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT COUNT(*) FROM lab_capsules WHERE owner_id=?",(user["id"],)).fetchone()[0]>=30:
                fail(429,"每人最多收藏三十枚私人时光胶囊")
            cur=c.execute("""INSERT INTO lab_capsules
                (owner_id,title,body,unlock_date,created_at) VALUES(?,?,?,?,?)""",
                (user["id"],data.title,data.body,data.unlock_date.isoformat(),now()))
            return {"id":cur.lastrowid,"sealed":True}

    def capsule_view(row):
        opened=row["unlock_date"]<=today().isoformat()
        return {"id":row["id"],"title":row["title"],"unlock_date":row["unlock_date"],
                "sealed":not opened,"body":row["body"] if opened else None,
                "created_at":row["created_at"]}

    @app.get("/api/lab/capsules")
    def capsules(user=Depends(require_user)):
        with db() as c:
            rows=c.execute("""SELECT * FROM lab_capsules WHERE owner_id=?
                ORDER BY id DESC LIMIT 30""",(user["id"],)).fetchall()
            return {"items":[capsule_view(x) for x in rows],"private":True}

    @app.get("/api/lab/capsules/{capsule_id}")
    def capsule_detail(capsule_id:int,user=Depends(require_user)):
        with db() as c:
            row=c.execute("SELECT * FROM lab_capsules WHERE id=? AND owner_id=?",
                          (capsule_id,user["id"])).fetchone()
            if not row:fail(404,"找不到这枚胶囊")
            return capsule_view(row)

    @app.delete("/api/lab/capsules/{capsule_id}")
    def remove_capsule(capsule_id:int,user=Depends(require_user)):
        with db() as c:
            if c.execute("DELETE FROM lab_capsules WHERE id=? AND owner_id=?",
                         (capsule_id,user["id"])).rowcount==0:
                fail(404,"找不到这枚胶囊")
            return {"ok":True}

    @app.get("/api/lab/surprise")
    def surprise(domain:str="全部",kind:Literal["all","exhibit","world"]="all"):
        with db() as c:
            return {"date_utc":today().isoformat(),"domain":domain,"kind":kind,
                    "item":daily_pick(c,domain,kind,today()),
                    "notice":NOTICE}

    @app.post("/api/lab/stamps",status_code=201)
    def collect_stamp(domain:str="全部",kind:Literal["all","exhibit","world"]="all",
                      user=Depends(require_user)):
        with db() as c:
            c.execute("BEGIN IMMEDIATE")
            chosen=daily_pick(c,domain,kind,today())
            if not chosen:fail(404,"今天该主题还没有公开来源")
            if c.execute("SELECT 1 FROM lab_stamps WHERE owner_id=? AND stamped_date=?",
                         (user["id"],today().isoformat())).fetchone():
                fail(409,"今天已经收集了一枚奇遇印章")
            cur=c.execute("""INSERT INTO lab_stamps
                (owner_id,stamped_date,domain,kind,exhibit_id,world_id,created_at)
                VALUES(?,?,?,?,?,?,?)""",(user["id"],today().isoformat(),domain,
                chosen["kind"],chosen["id"] if chosen["kind"]=="exhibit" else None,
                chosen["id"] if chosen["kind"]=="world" else None,now()))
            return {"id":cur.lastrowid,"date_utc":today().isoformat(),"item":chosen}

    @app.get("/api/lab/stamps")
    def stamps(user=Depends(require_user)):
        with db() as c:
            rows=c.execute("""SELECT * FROM lab_stamps WHERE owner_id=?
                ORDER BY stamped_date DESC LIMIT 100""",(user["id"],)).fetchall()
            out=[]
            for row in rows:
                sid=row["exhibit_id"] if row["kind"]=="exhibit" else row["world_id"]
                src=source_data(c,row["kind"],sid,user,public_only=True)
                out.append({"id":row["id"],"date_utc":row["stamped_date"],
                            "domain":row["domain"],"item":src if src else None,
                            "hidden":src is None})
            return {"items":out,"private":True}
