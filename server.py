"""Wonder Atlas — small self-hostable multi-user museum API, FastAPI + SQLite.

The server is deliberately a real shared service. Nothing in the public feed is
fabricated: published exhibits are contributed by registered accounts.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from fastapi import Cookie, Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

BASE = Path(__file__).resolve().parent
import restore_assets  # Extract archived artwork when cloned from GitHub.
from taxonomy import CATEGORY_TO_DOMAIN, DOMAINS, SERIES, TIME_BASES, TIME_BUCKETS
DATA = Path(os.getenv("WONDER_DATA_DIR", str(BASE / "data")))
DATA.mkdir(parents=True, exist_ok=True)
MEDIA = DATA / "media"
MEDIA.mkdir(exist_ok=True)
DATABASE = DATA / "wonder.db"
IS_SECURE = os.getenv("WONDER_COOKIE_SECURE", "0") == "1"
SESSION_SECONDS = 60 * 60 * 24 * 21

app = FastAPI(title="万物博物馆 API", version="21.0", docs_url="/api/docs", redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
app.mount("/media", StaticFiles(directory=MEDIA), name="media")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def db():
    c = sqlite3.connect(DATABASE, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA busy_timeout=8000")
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def initialize():
    with db() as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
          password_hash TEXT NOT NULL, bio TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(
          token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          expires_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS exhibits(
          id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', story TEXT NOT NULL DEFAULT '',
          category TEXT NOT NULL DEFAULT '其他',
          series TEXT NOT NULL DEFAULT '民间奇趣', domain TEXT NOT NULL DEFAULT '其他',
          time_bucket TEXT NOT NULL DEFAULT '时间不详', time_basis TEXT NOT NULL DEFAULT '不详', time_note TEXT NOT NULL DEFAULT '',
          tags TEXT NOT NULL DEFAULT '', image_url TEXT NOT NULL DEFAULT '', source_url TEXT NOT NULL DEFAULT '',
          visibility TEXT NOT NULL CHECK(visibility IN ('public','private')) DEFAULT 'private',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS ix_exhibits_public ON exhibits(visibility,created_at DESC);
        CREATE INDEX IF NOT EXISTS ix_exhibits_owner ON exhibits(user_id,created_at DESC);
        CREATE TABLE IF NOT EXISTS halls(
          id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', theme TEXT NOT NULL DEFAULT 'nebula',
          visibility TEXT NOT NULL CHECK(visibility IN ('public','private')) DEFAULT 'public',
          created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS hall_items(
          hall_id INTEGER NOT NULL REFERENCES halls(id) ON DELETE CASCADE,
          exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          pos_x REAL NOT NULL DEFAULT 15, pos_y REAL NOT NULL DEFAULT 15,
          width REAL NOT NULL DEFAULT 180,
          PRIMARY KEY(hall_id,exhibit_id));
        CREATE TABLE IF NOT EXISTS likes(
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          PRIMARY KEY(user_id,exhibit_id));
        CREATE TABLE IF NOT EXISTS bookmarks(
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          PRIMARY KEY(user_id,exhibit_id));
        CREATE TABLE IF NOT EXISTS comments(
          id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          body TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS ix_comments_item ON comments(exhibit_id,created_at DESC);
        CREATE TABLE IF NOT EXISTS follows(
          follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          followee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          PRIMARY KEY(follower_id,followee_id));
        CREATE TABLE IF NOT EXISTS notifications(
          id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          actor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          exhibit_id INTEGER REFERENCES exhibits(id) ON DELETE CASCADE,
          kind TEXT NOT NULL, is_read INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reports(
          id INTEGER PRIMARY KEY, reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
          reason TEXT NOT NULL, created_at TEXT NOT NULL,
          UNIQUE(reporter_id,exhibit_id));
        """)
        # Safe in-place migration: existing personal exhibits remain intact.
        columns = {row["name"] for row in c.execute("PRAGMA table_info(exhibits)")}
        migrate_legacy_domains = "domain" not in columns
        additions = {
            "series": "TEXT NOT NULL DEFAULT '民间奇趣'",
            "domain": "TEXT NOT NULL DEFAULT '其他'",
            "time_bucket": "TEXT NOT NULL DEFAULT '时间不详'",
            "time_basis": "TEXT NOT NULL DEFAULT '不详'",
            "time_note": "TEXT NOT NULL DEFAULT ''",
        }
        for column, declaration in additions.items():
            if column not in columns:
                c.execute(f"ALTER TABLE exhibits ADD COLUMN {column} {declaration}")
        if migrate_legacy_domains:
            for legacy_category, domain_name in CATEGORY_TO_DOMAIN.items():
                c.execute("UPDATE exhibits SET domain=? WHERE category=?", (domain_name, legacy_category))
        c.execute("CREATE INDEX IF NOT EXISTS ix_exhibits_taxonomy ON exhibits(visibility,series,domain,time_bucket)")


initialize()


def plain_row(row):
    return dict(row) if row is not None else None


def fail(code, message):
    raise HTTPException(status_code=code, detail=message)


def hash_pw(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return salt.hex() + "$" + dk.hex()


def check_pw(password: str, stored: str):
    try:
        salt, expected = stored.split("$")
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 210_000)
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False


def public_user(row):
    return {"id": row["id"], "username": row["username"], "bio": row["bio"], "created_at": row["created_at"]}


def maybe_user(wa_session: str | None = Cookie(default=None)):
    if not wa_session:
        return None
    digest = hashlib.sha256(wa_session.encode()).hexdigest()
    with db() as c:
        row = c.execute("SELECT u.* FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token_hash=? AND s.expires_at>?", (digest, int(time.time()))).fetchone()
    return plain_row(row)


def require_user(user=Depends(maybe_user)):
    if not user:
        fail(401, "请先登录")
    return user


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=24, pattern=r"^[A-Za-z0-9_\u4e00-\u9fff]+$")
    password: str = Field(min_length=8, max_length=128)


class ExhibitPayload(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=600)
    story: str = Field(default="", max_length=5000)
    category: str = Field(default="其他", max_length=48)
    series: Literal["藏品系列", "民间奇趣"] = "民间奇趣"
    domain: str = Field(default="其他", max_length=32)
    time_bucket: Literal["亿年前", "百万年前", "远古与史前", "千年至万年前", "近千年", "近现代", "近30年", "最近一年", "此刻/实时", "跨越多个时期", "时间不详"] = "时间不详"
    time_basis: Literal["形成/演化", "制作/创作", "发明/发布", "发现/出土", "走红/传播", "事件发生", "长期/跨时期", "不详"] = "不详"
    time_note: str = Field(default="", max_length=100)
    tags: str = Field(default="", max_length=200)
    image_url: str = Field(default="", max_length=500)
    source_url: str = Field(default="", max_length=500)
    visibility: Literal["public", "private"] = "private"

    @field_validator("domain")
    @classmethod
    def valid_domain(cls, v):
        v = v.strip()
        if v not in DOMAINS:
            raise ValueError("请选择有效的领域分类")
        return v

    @field_validator("image_url", "source_url")
    @classmethod
    def safe_url(cls, v):
        v = v.strip()
        if v and (urlsplit(v).scheme not in ("http", "https") or not urlsplit(v).netloc):
            # Local uploaded images have only a controlled first-party path.
            if not (v.startswith("/media/") and v[7:].replace(".", "").isalnum() and ".." not in v):
                raise ValueError("仅支持 http(s) 地址或已上传图片")
        return v


class HallPayload(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str = Field(default="", max_length=300)
    theme: Literal["nebula", "gallery", "forest", "sunset"] = "nebula"
    visibility: Literal["public", "private"] = "public"


class CommentPayload(BaseModel):
    body: str = Field(min_length=1, max_length=600)


class BioPayload(BaseModel):
    bio: str = Field(max_length=240)


class LayoutItem(BaseModel):
    exhibit_id: int
    x: float = Field(ge=0, le=850)
    y: float = Field(ge=0, le=480)
    width: float = Field(ge=120, le=320)


class LayoutPayload(BaseModel):
    positions: list[LayoutItem] = Field(max_length=150)


class AddItem(BaseModel):
    exhibit_id: int


class ReportPayload(BaseModel):
    reason: str = Field(min_length=5, max_length=300)


@app.middleware("http")
async def safe_origins(request: Request, call_next):
    # Protection against cross-origin browser form submissions; no CORS is enabled.
    if request.method in ("POST", "PATCH", "PUT", "DELETE"):
        origin = request.headers.get("origin")
        if origin:
            trusted = f"{request.url.scheme}://{request.url.netloc}"
            configured = os.getenv("WONDER_PUBLIC_ORIGIN", "")
            if origin not in (trusted, configured):
                return Response("Forbidden origin", status_code=403)
    return await call_next(request)


@app.get("/")
def homepage():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True, "version": app.version, "database": "sqlite"}


@app.get("/api/taxonomy")
def get_taxonomy():
    from taxonomy import DOMAIN_CATEGORIES
    return {
        "series": list(SERIES),
        "domains": list(DOMAINS),
        "categories": {key: list(value) for key, value in DOMAIN_CATEGORIES.items()},
        "time_buckets": list(TIME_BUCKETS),
        "time_bases": list(TIME_BASES),
    }


def set_session(c, user_id, response):
    token = secrets.token_urlsafe(36)
    c.execute("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), user_id, int(time.time()) + SESSION_SECONDS))
    response.set_cookie("wa_session", token, httponly=True, secure=IS_SECURE, samesite="strict", max_age=SESSION_SECONDS, path="/")


# Local-demo rate limits; use Redis or a reverse-proxy rate limiter for public hosting.
_attempts: dict[str, list[float]] = {}


def throttle(request, action, limit=18, window=900):
    ip = request.client.host if request.client else "unknown"
    key = action + ":" + ip
    times = [t for t in _attempts.get(key, []) if t > time.time() - window]
    if len(times) >= limit:
        fail(429, "操作过于频繁，请稍后再试")
    times.append(time.time())
    _attempts[key] = times


@app.post("/api/auth/register", status_code=201)
def register(credentials: Credentials, request: Request, response: Response):
    throttle(request, "register", 10, 3600)
    with db() as c:
        try:
            cur = c.execute("INSERT INTO users(username,password_hash,created_at) VALUES(?,?,?)", (credentials.username, hash_pw(credentials.password), now()))
        except sqlite3.IntegrityError:
            fail(409, "这个用户名已经有人使用了")
        user_id = cur.lastrowid
        c.execute("INSERT INTO halls(user_id,name,description,theme,visibility,created_at) VALUES(?,?,?,?,?,?)", (user_id, "我的万物陈列室", "这里收藏我的世界。", "nebula", "public", now()))
        set_session(c, user_id, response)
        return {"id": user_id, "username": credentials.username}


@app.post("/api/auth/login")
def login(credentials: Credentials, request: Request, response: Response):
    throttle(request, "login", 20, 900)
    with db() as c:
        row = c.execute("SELECT * FROM users WHERE username=?", (credentials.username,)).fetchone()
        if not row or not check_pw(credentials.password, row["password_hash"]):
            fail(401, "用户名或密码错误")
        set_session(c, row["id"], response)
        return public_user(row)


@app.post("/api/auth/logout")
def logout(response: Response, wa_session: str | None = Cookie(default=None)):
    if wa_session:
        with db() as c:
            c.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(wa_session.encode()).hexdigest(),))
    response.delete_cookie("wa_session", path="/")
    return {"ok": True}


@app.get("/api/me")
def me(user=Depends(maybe_user)):
    return {"user": public_user(user) if user else None}


@app.patch("/api/me")
def update_me(data: BioPayload, user=Depends(require_user)):
    with db() as c:
        c.execute("UPDATE users SET bio=? WHERE id=?", (data.bio.strip(), user["id"]))
    return {"ok": True}


def item_select(viewer_id: int):
    return """SELECT e.*, u.username AS owner,
      (SELECT COUNT(*) FROM likes l WHERE l.exhibit_id=e.id) likes_count,
      (SELECT COUNT(*) FROM comments m WHERE m.exhibit_id=e.id) comments_count,
      EXISTS(SELECT 1 FROM likes x WHERE x.exhibit_id=e.id AND x.user_id=?) liked,
      EXISTS(SELECT 1 FROM bookmarks x WHERE x.exhibit_id=e.id AND x.user_id=?) bookmarked
      FROM exhibits e JOIN users u ON e.user_id=u.id"""


def item_dict(row):
    d = plain_row(row)
    d["liked"] = bool(d["liked"])
    d["bookmarked"] = bool(d["bookmarked"])
    d["tags"] = [tag for tag in d["tags"].split(",") if tag]
    return d


def read_exhibit(c, id, user, public_only=False):
    row = c.execute(item_select(user["id"] if user else 0) + " WHERE e.id=?", (user["id"] if user else 0, user["id"] if user else 0, id)).fetchone()
    if not row or (row["visibility"] == "private" and (public_only or not user or row["user_id"] != user["id"])):
        fail(404, "展品不存在或没有访问权限")
    return item_dict(row)


@app.get("/api/feed")
def feed(q: str = "", category: str = "", domain: str = "", series: str = "", time_bucket: str = "", sort: Literal["latest", "popular"] = "latest", page: int = 1, following: bool = False, user=Depends(maybe_user)):
    page = max(1, min(page, 9999))
    sql = item_select(user["id"] if user else 0) + " WHERE e.visibility='public'"
    args = [user["id"] if user else 0, user["id"] if user else 0]
    if following:
        if not user: fail(401, "查看关注动态请先登录")
        sql += " AND EXISTS (SELECT 1 FROM follows f WHERE f.follower_id=? AND f.followee_id=e.user_id)"
        args.append(user["id"])
    if q.strip():
        sql += " AND (e.title LIKE ? OR e.description LIKE ? OR e.tags LIKE ? OR u.username LIKE ?)"
        args.extend(["%" + q.strip()[:60] + "%"] * 4)
    if category and category != "全部":
        sql += " AND e.category=?"
        args.append(category[:48])
    if domain and domain != "全部":
        if domain not in DOMAINS: fail(400, "未知领域分类")
        sql += " AND e.domain=?"
        args.append(domain)
    if series and series != "全部":
        if series not in SERIES: fail(400, "未知内容系列")
        sql += " AND e.series=?"
        args.append(series)
    if time_bucket and time_bucket != "全部":
        if time_bucket not in TIME_BUCKETS: fail(400, "未知时间分类")
        sql += " AND e.time_bucket=?"
        args.append(time_bucket)
    sql += " ORDER BY " + ("likes_count DESC, e.created_at DESC" if sort == "popular" else "e.created_at DESC")
    sql += " LIMIT 24 OFFSET ?"
    args.append((page - 1) * 24)
    with db() as c:
        rows = c.execute(sql, args).fetchall()
    return {"items": [item_dict(r) for r in rows], "page": page}


@app.get("/api/random")
def random_exhibit(user=Depends(maybe_user)):
    with db() as c:
        row = c.execute("SELECT id FROM exhibits WHERE visibility='public' ORDER BY RANDOM() LIMIT 1").fetchone()
        return read_exhibit(c, row["id"], user) if row else None


@app.get("/api/my/exhibits")
def my_exhibits(user=Depends(require_user)):
    with db() as c:
        rows = c.execute(item_select(user["id"]) + " WHERE e.user_id=? ORDER BY e.created_at DESC", (user["id"], user["id"], user["id"])).fetchall()
    return [item_dict(r) for r in rows]


@app.get("/api/my/saved")
def saved(user=Depends(require_user)):
    with db() as c:
        rows = c.execute(item_select(user["id"]) + " JOIN bookmarks b ON b.exhibit_id=e.id WHERE b.user_id=? AND (e.visibility='public' OR e.user_id=?) ORDER BY e.created_at DESC", (user["id"], user["id"], user["id"], user["id"])).fetchall()
    return [item_dict(r) for r in rows]


@app.get("/api/exhibits/{id}")
def get_exhibit(id: int, user=Depends(maybe_user)):
    with db() as c:
        return read_exhibit(c, id, user)


@app.post("/api/exhibits", status_code=201)
def create_exhibit(data: ExhibitPayload, user=Depends(require_user)):
    d = data.model_dump()
    d["tags"] = ",".join(dict.fromkeys(t.strip()[:24] for t in d["tags"].replace("，", ",").split(",") if t.strip()))[:200]
    with db() as c:
        cur = c.execute("""INSERT INTO exhibits(user_id,title,description,story,category,series,domain,time_bucket,time_basis,time_note,tags,image_url,source_url,visibility,created_at,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (user["id"], d["title"].strip(), d["description"].strip(), d["story"].strip(), d["category"].strip() or "其他", d["series"], d["domain"], d["time_bucket"], d["time_basis"], d["time_note"].strip(), d["tags"], d["image_url"], d["source_url"], d["visibility"], now(), now()))
        return read_exhibit(c, cur.lastrowid, user)


@app.patch("/api/exhibits/{id}")
def edit_exhibit(id: int, data: ExhibitPayload, user=Depends(require_user)):
    with db() as c:
        old = read_exhibit(c, id, user)
        if old["user_id"] != user["id"]:
            fail(403, "只能编辑自己的展品")
        d = data.model_dump()
        fantasy_world = c.execute("""SELECT w.visibility FROM fantasy_relics r
          JOIN fantasy_worlds w ON w.id=r.world_id WHERE r.exhibit_id=?""",(id,)).fetchone()
        if fantasy_world:
            if d['visibility']=='public' and fantasy_world['visibility']!='public':
                fail(409,'私人玄幻世界中的奇物不能单独公开')
            if not d['story'].startswith('【纯虚构／原创世界观】'):
                d['story']='【纯虚构／原创世界观】故事与超自然能力均为虚构创作。\\n'+d['story']
            d['category']='世界观设定'
            d['series']='民间奇趣'
            d['domain']='原创与个人创作'
            d['time_bucket']='时间不详'
            d['time_basis']='不详'
            d['time_note']='虚构世界纪年'
            d['source_url']=''
        d["tags"] = ",".join(dict.fromkeys(t.strip()[:24] for t in d["tags"].replace("，", ",").split(",") if t.strip()))[:200]
        c.execute("""UPDATE exhibits SET title=?,description=?,story=?,category=?,series=?,domain=?,time_bucket=?,time_basis=?,time_note=?,tags=?,image_url=?,source_url=?,visibility=?,updated_at=? WHERE id=?""",
                  (d["title"].strip(),d["description"].strip(),d["story"].strip(),d["category"].strip() or "其他",d["series"],d["domain"],d["time_bucket"],d["time_basis"],d["time_note"].strip(),d["tags"],d["image_url"],d["source_url"],d["visibility"],now(),id))
        return read_exhibit(c, id, user)


@app.delete("/api/exhibits/{id}")
def delete_exhibit(id: int, user=Depends(require_user)):
    with db() as c:
        old = read_exhibit(c, id, user)
        if old["user_id"] != user["id"]:
            fail(403, "只能删除自己的展品")
        c.execute("DELETE FROM exhibits WHERE id=?", (id,))
    return {"ok": True}


def notify(c, actor, owner, kind, exhibit_id=None):
    if actor != owner:
        c.execute("INSERT INTO notifications(user_id,actor_id,exhibit_id,kind,created_at) VALUES(?,?,?,?,?)", (owner,actor,exhibit_id,kind,now()))


@app.post("/api/exhibits/{id}/like")
def toggle_like(id: int, user=Depends(require_user)):
    with db() as c:
        item = read_exhibit(c, id, user)
        existing = c.execute("SELECT 1 FROM likes WHERE user_id=? AND exhibit_id=?", (user["id"],id)).fetchone()
        if existing:
            c.execute("DELETE FROM likes WHERE user_id=? AND exhibit_id=?", (user["id"],id))
        else:
            c.execute("INSERT INTO likes(user_id,exhibit_id) VALUES(?,?)", (user["id"],id))
            notify(c,user["id"],item["user_id"],"like",id)
        return {"liked": not bool(existing)}


@app.post("/api/exhibits/{id}/bookmark")
def toggle_bookmark(id: int, user=Depends(require_user)):
    with db() as c:
        read_exhibit(c,id,user)
        existing = c.execute("SELECT 1 FROM bookmarks WHERE user_id=? AND exhibit_id=?", (user["id"],id)).fetchone()
        if existing:
            c.execute("DELETE FROM bookmarks WHERE user_id=? AND exhibit_id=?", (user["id"],id))
        else:
            c.execute("INSERT INTO bookmarks(user_id,exhibit_id) VALUES(?,?)", (user["id"],id))
        return {"bookmarked": not bool(existing)}


@app.get("/api/exhibits/{id}/comments")
def comments(id: int, user=Depends(maybe_user)):
    with db() as c:
        read_exhibit(c,id,user)
        rows = c.execute("""SELECT m.id,m.user_id,u.username,m.body,m.created_at FROM comments m JOIN users u ON u.id=m.user_id WHERE m.exhibit_id=? ORDER BY m.id DESC LIMIT 100""", (id,)).fetchall()
        return [plain_row(r) for r in rows]


@app.post("/api/exhibits/{id}/comments", status_code=201)
def post_comment(id: int, data: CommentPayload, user=Depends(require_user)):
    with db() as c:
        item = read_exhibit(c,id,user)
        cur = c.execute("INSERT INTO comments(user_id,exhibit_id,body,created_at) VALUES(?,?,?,?)", (user["id"],id,data.body.strip(),now()))
        notify(c,user["id"],item["user_id"],"comment",id)
        return {"id":cur.lastrowid}


@app.post("/api/exhibits/{id}/report")
def report(id: int, data: ReportPayload, user=Depends(require_user)):
    with db() as c:
        item = read_exhibit(c,id,user)
        if item["user_id"] == user["id"]:
            fail(400,"不能举报自己的展品")
        c.execute("INSERT INTO reports(reporter_id,exhibit_id,reason,created_at) VALUES(?,?,?,?) ON CONFLICT(reporter_id,exhibit_id) DO UPDATE SET reason=excluded.reason", (user["id"],id,data.reason.strip(),now()))
        return {"ok":True}


@app.get("/api/my/halls")
def my_halls(user=Depends(require_user)):
    with db() as c:
        return [plain_row(x) for x in c.execute("SELECT * FROM halls WHERE user_id=? ORDER BY id", (user["id"],)).fetchall()]


@app.post("/api/halls", status_code=201)
def create_hall(data: HallPayload, user=Depends(require_user)):
    with db() as c:
        cur = c.execute("INSERT INTO halls(user_id,name,description,theme,visibility,created_at) VALUES(?,?,?,?,?,?)", (user["id"],data.name.strip(),data.description.strip(),data.theme,data.visibility,now()))
        return {"id": cur.lastrowid}


def read_hall(c,id,user):
    hall = c.execute("SELECT h.*,u.username owner FROM halls h JOIN users u ON u.id=h.user_id WHERE h.id=?",(id,)).fetchone()
    if not hall or (hall["visibility"] != "public" and (not user or hall["user_id"] != user["id"])):
        fail(404,"展厅不存在或没有访问权限")
    clause = "" if user and user["id"] == hall["user_id"] else " AND e.visibility='public'"
    items = c.execute(item_select(user["id"] if user else 0) + " JOIN hall_items hi ON hi.exhibit_id=e.id WHERE hi.hall_id=?" + clause + " ORDER BY hi.pos_y, hi.pos_x", (user["id"] if user else 0,user["id"] if user else 0,id)).fetchall()
    return {"hall": plain_row(hall), "items": [{**item_dict(item), **plain_row(c.execute("SELECT pos_x AS x,pos_y AS y,width FROM hall_items WHERE hall_id=? AND exhibit_id=?",(id,item["id"])).fetchone())} for item in items]}


@app.get("/api/halls/{id}")
def get_hall(id:int,user=Depends(maybe_user)):
    with db() as c:
        return read_hall(c,id,user)


@app.patch("/api/halls/{id}")
def edit_hall(id:int,data:HallPayload,user=Depends(require_user)):
    with db() as c:
        hall=read_hall(c,id,user)["hall"]
        if hall["user_id"]!=user["id"]:fail(403,"没有编辑权限")
        c.execute("UPDATE halls SET name=?,description=?,theme=?,visibility=? WHERE id=?",(data.name.strip(),data.description.strip(),data.theme,data.visibility,id))
    return {"ok":True}


@app.delete("/api/halls/{id}")
def delete_hall(id:int,user=Depends(require_user)):
    with db() as c:
        hall=read_hall(c,id,user)["hall"]
        if hall["user_id"]!=user["id"]:fail(403,"没有删除权限")
        c.execute("DELETE FROM halls WHERE id=?",(id,))
    return {"ok":True}


@app.post("/api/halls/{id}/items")
def hall_add(id:int,data:AddItem,user=Depends(require_user)):
    with db() as c:
        hall=read_hall(c,id,user)["hall"]
        if hall["user_id"]!=user["id"]:fail(403,"不是你的展厅")
        item=read_exhibit(c,data.exhibit_id,user)
        if item["user_id"]!=user["id"]:fail(403,"只能在自己展厅陈列自己的展品")
        count=c.execute("SELECT COUNT(*) FROM hall_items WHERE hall_id=?",(id,)).fetchone()[0]
        c.execute("INSERT OR IGNORE INTO hall_items(hall_id,exhibit_id,pos_x,pos_y) VALUES(?,?,?,?)",(id,data.exhibit_id,20+(count%4)*195,15+(count//4)*190))
    return {"ok":True}


@app.delete("/api/halls/{id}/items/{exhibit_id}")
def hall_remove(id:int,exhibit_id:int,user=Depends(require_user)):
    with db() as c:
        hall=read_hall(c,id,user)["hall"]
        if hall["user_id"]!=user["id"]:fail(403,"不是你的展厅")
        c.execute("DELETE FROM hall_items WHERE hall_id=? AND exhibit_id=?",(id,exhibit_id))
    return {"ok":True}


@app.patch("/api/halls/{id}/layout")
def hall_layout(id:int,data:LayoutPayload,user=Depends(require_user)):
    with db() as c:
        hall=read_hall(c,id,user)["hall"]
        if hall["user_id"]!=user["id"]:fail(403,"不是你的展厅")
        ids={r[0] for r in c.execute("SELECT exhibit_id FROM hall_items WHERE hall_id=?",(id,)).fetchall()}
        if any(p.exhibit_id not in ids for p in data.positions):fail(400,"包含不属于这个展厅的展品")
        for p in data.positions:
            c.execute("UPDATE hall_items SET pos_x=?,pos_y=?,width=? WHERE hall_id=? AND exhibit_id=?",(p.x,p.y,p.width,id,p.exhibit_id))
    return {"ok":True}


@app.get("/api/users/{username}")
def profile(username:str,user=Depends(maybe_user)):
    with db() as c:
        owner=c.execute("SELECT id,username,bio,created_at FROM users WHERE username=?",(username,)).fetchone()
        if not owner:fail(404,"没有这个馆长")
        own=bool(user and user["id"]==owner["id"])
        clause="" if own else " AND e.visibility='public'"
        items=c.execute(item_select(user["id"] if user else 0) + " WHERE e.user_id=?"+clause+" ORDER BY e.created_at DESC LIMIT 100",(user["id"] if user else 0,user["id"] if user else 0,owner["id"])).fetchall()
        halls=c.execute("SELECT * FROM halls WHERE user_id=?"+("" if own else " AND visibility='public'")+" ORDER BY id",(owner["id"],)).fetchall()
        followers=c.execute("SELECT COUNT(*) FROM follows WHERE followee_id=?",(owner["id"],)).fetchone()[0]
        following=c.execute("SELECT COUNT(*) FROM follows WHERE follower_id=?",(owner["id"],)).fetchone()[0]
        is_following=bool(user and c.execute("SELECT 1 FROM follows WHERE follower_id=? AND followee_id=?",(user["id"],owner["id"])).fetchone())
    return {"user":public_user(owner),"items":[item_dict(r) for r in items],"halls":[plain_row(r) for r in halls],"followers":followers,"following":following,"is_following":is_following}


@app.post("/api/users/{id}/follow")
def toggle_follow(id:int,user=Depends(require_user)):
    if id==user["id"]:fail(400,"不能关注自己")
    with db() as c:
        if not c.execute("SELECT 1 FROM users WHERE id=?",(id,)).fetchone():fail(404,"用户不存在")
        follows=bool(c.execute("SELECT 1 FROM follows WHERE follower_id=? AND followee_id=?",(user["id"],id)).fetchone())
        if follows:c.execute("DELETE FROM follows WHERE follower_id=? AND followee_id=?",(user["id"],id))
        else:
            c.execute("INSERT INTO follows(follower_id,followee_id) VALUES(?,?)",(user["id"],id))
            notify(c,user["id"],id,"follow")
    return {"following":not follows}


@app.get("/api/notifications")
def notifications(user=Depends(require_user)):
    with db() as c:
        rows=c.execute("""SELECT n.*,u.username actor FROM notifications n JOIN users u ON n.actor_id=u.id WHERE n.user_id=? ORDER BY n.id DESC LIMIT 50""",(user["id"],)).fetchall()
        return {"items":[plain_row(r) for r in rows],"unread":sum(not r["is_read"] for r in rows)}


@app.post("/api/notifications/read")
def mark_read(user=Depends(require_user)):
    with db() as c:c.execute("UPDATE notifications SET is_read=1 WHERE user_id=?",(user["id"],))
    return {"ok":True}


@app.get("/api/stats")
def stats():
    with db() as c:
        return {"curators":c.execute("SELECT COUNT(*) FROM users").fetchone()[0],
                "exhibits":c.execute("SELECT COUNT(*) FROM exhibits WHERE visibility='public'").fetchone()[0],
                "halls":c.execute("SELECT COUNT(*) FROM halls WHERE visibility='public'").fetchone()[0]}


@app.post("/api/media", status_code=201)
async def upload_media(file:UploadFile=File(...),user=Depends(require_user)):
    from PIL import Image, ImageOps, UnidentifiedImageError
    import io
    if file.content_type not in ("image/jpeg","image/png","image/webp"):
        fail(400,"仅允许 JPG/PNG/WebP 图片")
    content=await file.read(4_000_001)
    if len(content)>4_000_000:fail(413,"图片不能超过 4MB")
    try:
        with Image.open(io.BytesIO(content)) as im:
            if im.format not in ("JPEG","PNG","WEBP") or im.width*im.height>24_000_000:
                fail(400,"图片格式不合法或像素过大")
            im=ImageOps.exif_transpose(im)
            im.thumbnail((1600,1600))
            if im.mode not in ("RGB","RGBA"):im=im.convert("RGB")
            out=io.BytesIO()
            if im.mode=="RGBA":
                im.save(out,"WEBP",quality=84)
            else:
                im.convert("RGB").save(out,"WEBP",quality=84)
    except (UnidentifiedImageError, ValueError, OSError):
        fail(400,"无法读取图片")
    name=uuid.uuid4().hex+".webp"
    (MEDIA/name).write_bytes(out.getvalue())
    return {"url":"/media/"+name}


@app.post("/api/import/v1")
def import_v1(payload: dict,user=Depends(require_user)):
    # Only import user's custom items, never sample/mock exhibit IDs from old prototype.
    old=payload.get("data",payload)
    items=old.get("custom",[]) if isinstance(old,dict) else []
    if not isinstance(items,list) or len(items)>250:fail(400,"导入文件错误，或单次超过250项")
    imported=0
    with db() as c:
        for raw in items:
            if not isinstance(raw,dict) or not str(raw.get("title","")).strip():continue
            image=str(raw.get("image","")).strip()
            if image.startswith("data:"): image=""  # old embedded base64 needs manual reupload
            try:
                data=ExhibitPayload(title=str(raw.get("title",""))[:100],description=str(raw.get("description",""))[:600],story=str(raw.get("story",""))[:5000],category=str(raw.get("category","其他"))[:48],domain=CATEGORY_TO_DOMAIN.get(str(raw.get("category","其他")),"其他"),tags=",".join(str(t) for t in raw.get("tags",[])[:12])[:200] if isinstance(raw.get("tags"),list) else "",image_url=image[:500],source_url=str(raw.get("source", ""))[:500],visibility="private")
            except Exception: continue
            d=data.model_dump()
            c.execute("INSERT INTO exhibits(user_id,title,description,story,category,series,domain,time_bucket,time_basis,time_note,tags,image_url,source_url,visibility,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (user["id"],d["title"],d["description"],d["story"],d["category"],d["series"],d["domain"],d["time_bucket"],d["time_basis"],d["time_note"],d["tags"],d["image_url"],d["source_url"],"private",now(),now()))
            imported+=1
    return {"imported":imported,"notice":"导入展品默认为私密；旧版内嵌图片需重新上传。"}


@app.get("/api/exhibits/{id}/related")
def related(id: int, user=Depends(maybe_user)):
    with db() as c:
        item=read_exhibit(c,id,user)
        candidates=c.execute(item_select(user["id"] if user else 0) + " WHERE e.visibility='public' AND e.id<>? ORDER BY e.created_at DESC LIMIT 300",(user["id"] if user else 0,user["id"] if user else 0,id)).fetchall()
        tags=set(item["tags"])
        scores=[]
        for r in candidates:
            d=item_dict(r)
            score=3*len(tags.intersection(d["tags"])) + (2 if item["category"]==d["category"] else 0)
            if score:scores.append((score,d))
        scores.sort(key=lambda v:v[0],reverse=True)
        return [x for _,x in scores[:4]]


@app.get("/api/my/backup")
def full_backup(user=Depends(require_user)):
    with db() as c:
        items=c.execute(item_select(user["id"]) + " WHERE e.user_id=? ORDER BY e.id",(user["id"],user["id"],user["id"])).fetchall()
        halls=c.execute("SELECT * FROM halls WHERE user_id=? ORDER BY id",(user["id"],)).fetchall()
        rooms=[]
        for h in halls:
            room=plain_row(h)
            room["items"]=[plain_row(r) for r in c.execute("SELECT exhibit_id,pos_x AS x,pos_y AS y,width FROM hall_items WHERE hall_id=?",(h["id"],)).fetchall()]
            rooms.append(room)
        return {"format":"wonder-atlas-network-v2","exported_at":now(),"user":user["username"],"exhibits":[item_dict(r) for r in items],"halls":rooms}


@app.post("/api/import/v2")
def import_v2(payload:dict,user=Depends(require_user)):
    if payload.get("format")!="wonder-atlas-network-v2":fail(400,"不是 V2 备份格式")
    exhibits=payload.get("exhibits",[])
    halls=payload.get("halls",[])
    if not isinstance(exhibits,list) or not isinstance(halls,list) or len(exhibits)>500 or len(halls)>60:
        fail(400,"备份不合法或超出单次导入上限")
    idmap={}
    with db() as c:
        for raw in exhibits:
            if not isinstance(raw,dict):continue
            try:
                im=str(raw.get("image_url",""))
                if im.startswith('/media/') and not (MEDIA/im[7:]).is_file(): im=""
                d=ExhibitPayload(title=str(raw.get("title",""))[:100],description=str(raw.get("description",""))[:600],story=str(raw.get("story",""))[:5000],category=str(raw.get("category","其他"))[:48],series=raw.get("series","民间奇趣"),domain=raw.get("domain",CATEGORY_TO_DOMAIN.get(str(raw.get("category","其他")),"其他")),time_bucket=raw.get("time_bucket","时间不详"),time_basis=raw.get("time_basis","不详"),time_note=str(raw.get("time_note",""))[:100],tags=",".join(str(t)[:24] for t in raw.get("tags",[])[:12]) if isinstance(raw.get("tags"),list) else str(raw.get("tags", ""))[:200],image_url=im[:500],source_url=str(raw.get("source_url",""))[:500],visibility=raw.get("visibility","private"))
            except Exception:continue
            x=d.model_dump()
            # Repeat imports of the same backup should not endlessly copy identical records.
            existing=c.execute("SELECT id FROM exhibits WHERE user_id=? AND title=? AND description=? AND source_url=?",(user["id"],x["title"],x["description"],x["source_url"])).fetchone()
            if existing: new_id=existing["id"]
            else:
                cur=c.execute("""INSERT INTO exhibits(user_id,title,description,story,category,series,domain,time_bucket,time_basis,time_note,tags,image_url,source_url,visibility,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (user["id"],x["title"],x["description"],x["story"],x["category"],x["series"],x["domain"],x["time_bucket"],x["time_basis"],x["time_note"],x["tags"],x["image_url"],x["source_url"],x["visibility"],now(),now()))
                new_id=cur.lastrowid
            idmap[raw.get("id")]=new_id
        hall_count=0
        for raw in halls:
            if not isinstance(raw,dict):continue
            try:
                h=HallPayload(name=str(raw.get("name",""))[:50],description=str(raw.get("description",""))[:300],theme=raw.get("theme","nebula"),visibility=raw.get("visibility","private"))
            except Exception:continue
            info=h.model_dump()
            found=c.execute("SELECT id FROM halls WHERE user_id=? AND name=?",(user["id"],info["name"])).fetchone()
            if found:
                target_hall_id=found["id"]
                c.execute("UPDATE halls SET description=?,theme=?,visibility=? WHERE id=?",(info["description"],info["theme"],info["visibility"],target_hall_id))
            else:
                cur=c.execute("INSERT INTO halls(user_id,name,description,theme,visibility,created_at) VALUES(?,?,?,?,?,?)",(user["id"],info["name"],info["description"],info["theme"],info["visibility"],now()))
                target_hall_id=cur.lastrowid
                hall_count+=1
            for position in raw.get("items",[])[:150]:
                if not isinstance(position,dict):continue
                exhibit_id=idmap.get(position.get("exhibit_id"))
                if not exhibit_id:continue
                try:
                    x=max(0,min(850,float(position.get("x",15))))
                    y=max(0,min(480,float(position.get("y",15))))
                    width=max(120,min(320,float(position.get("width",180))))
                except (TypeError,ValueError):continue
                c.execute("INSERT OR IGNORE INTO hall_items(hall_id,exhibit_id,pos_x,pos_y,width) VALUES(?,?,?,?,?)",(target_hall_id,exhibit_id,x,y,width))
    return {"mapped_exhibits":len(idmap),"created_halls":hall_count}

# Shared feature workflows use the same accounts, exhibits, moderation boundary and database.
from features_api import mount_features
mount_features(app, db, read_exhibit, maybe_user, require_user, now, fail)

# Personal opt-in history and memory-film reels.
from memories_api import mount_memories
mount_memories(app, db, read_exhibit, require_user, now, fail)

# V7: cross-domain routes and private journey bookmarks.
from atlas_paths import mount_atlas
mount_atlas(app, db, maybe_user, require_user, now, fail)

# Read-only starter collection sourced from official open-access museum APIs.
from world_museums import mount_world_museums
mount_world_museums(app, db, maybe_user, require_user, now, fail)

# V6: broad museum directory, live curiosity radar and aggregate feature feedback.
from wonder_discovery import mount_wonder_discovery
mount_wonder_discovery(app, db, maybe_user, require_user, now, fail)

# V8: private annual growth recap derived from member records (no passive tracking).
from growth_api import mount_growth
mount_growth(app, db, read_exhibit, require_user, now, fail)
# V11: explainable, privacy-safe classification paths and exhibit networks.
from connections_api import mount_connections
mount_connections(app, db, read_exhibit, maybe_user, require_user, now, fail)

# V12: a shared world-time, evidence, and private interest-map explorer.
from cosmos_api import mount_cosmos
mount_cosmos(app, db, read_exhibit, maybe_user, require_user, now, fail)

# V13: read-only institution time catalogue and private metadata quality checklist.
from curation_api import mount_curation
mount_curation(app, db, require_user, fail)

# V14: official museum specimens and art collection discovery, private saves.
from world_sources_v14 import mount_world_sources
mount_world_sources(app, db, require_user, now, fail)

# V15: NASA and Library of Congress discovery routes with private saves.
from expeditions_v15 import mount_expeditions
mount_expeditions(app, db, require_user, now)

# V16: creator-owned original fantasy worlds and explicitly fictional relics.
from fantasy_api import mount_fantasy
mount_fantasy(app, db, require_user, maybe_user, now, fail)

# V17: consensual fiction diplomacy, civilization cards and jointly reviewed lore.
from diplomacy_api import mount_diplomacy
mount_diplomacy(app, db, require_user, maybe_user, now, fail)

# V18: deterministic, immutable, creator-owned civilization evolution.
from evolution_api import mount_evolution
mount_evolution(app, db, require_user, maybe_user, now, fail)

# V19: voluntary cross-civilization connections; revocation is enforced in world routes.
from relations_api import mount_relations
mount_relations(app, db, require_user, maybe_user, now, fail)

# V20: universal wonder albums and private future letters.
from everything_lab import mount_everything_lab
mount_everything_lab(app, db, require_user, maybe_user, now, fail)


# V21: playable math/science demonstrations and collaborative discovery relays.
from play_api import mount_play
mount_play(app, db, require_user, maybe_user, now, fail)
