"""Private, explicitly opt-in exhibit viewing history and saved memory films.

No passive analytics: client must call POST /seen after user enables recording.
History and reels are readable only by their authenticated owner.
"""
import json
from typing import Literal
from fastapi import Depends, Query
from pydantic import BaseModel, Field, field_validator


class ReelIn(BaseModel):
    title: str = Field(min_length=1, max_length=60)
    exhibit_ids: list[int] = Field(min_length=1, max_length=40)
    music: Literal['silent', 'starlight', 'piano', 'journey'] = 'piano'

    @field_validator('title')
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError('影片名称不能为空')
        return value.strip()


def mount_memories(app, db, read_exhibit, require_user, now, fail):
    with db() as c:
        c.executescript('''
          CREATE TABLE IF NOT EXISTS memory_views (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            exhibit_id INTEGER NOT NULL REFERENCES exhibits(id) ON DELETE CASCADE,
            first_at TEXT NOT NULL, last_at TEXT NOT NULL,
            views INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY(user_id, exhibit_id)
          );
          CREATE INDEX IF NOT EXISTS ix_memory_views_last ON memory_views(user_id,last_at DESC);
          CREATE TABLE IF NOT EXISTS memory_reels (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL, exhibit_ids TEXT NOT NULL,
            music TEXT NOT NULL DEFAULT 'piano', created_at TEXT NOT NULL
          );
          CREATE INDEX IF NOT EXISTS ix_memory_reels_owner ON memory_reels(user_id,created_at DESC);
        ''')

    def allowed(c, exhibit_id, user):
        try:
            return read_exhibit(c, exhibit_id, user)
        except Exception as exc:
            # read_exhibit raises HTTPException on inaccessible or deleted items.
            if getattr(exc, 'status_code', None) == 404:
                return None
            raise

    @app.post('/api/memories/seen/{exhibit_id}')
    def record_visit(exhibit_id: int, user=Depends(require_user)):
        with db() as c:
            if not allowed(c, exhibit_id, user):
                fail(404, '展品不存在或已无权访问')
            c.execute('''INSERT INTO memory_views(user_id,exhibit_id,first_at,last_at,views)
                VALUES(?,?,?,?,1)
                ON CONFLICT(user_id,exhibit_id) DO UPDATE SET
                last_at=excluded.last_at, views=memory_views.views+1''',
                (user['id'], exhibit_id, now(), now()))
        return {'recorded': True}

    @app.get('/api/memories/history')
    def history(limit: int = Query(100, ge=1, le=200), user=Depends(require_user)):
        with db() as c:
            rows = c.execute('''SELECT exhibit_id, first_at, last_at, views
                FROM memory_views WHERE user_id=? ORDER BY last_at DESC LIMIT ?''',
                (user['id'], limit)).fetchall()
            items = []
            for row in rows:
                exhibit = allowed(c, row['exhibit_id'], user)
                if exhibit:
                    items.append({**exhibit, 'first_seen_at': row['first_at'],
                                  'last_seen_at': row['last_at'], 'view_count': row['views']})
        return {'items': items}

    @app.delete('/api/memories/history')
    def clear_history(user=Depends(require_user)):
        with db() as c:
            c.execute('DELETE FROM memory_views WHERE user_id=?', (user['id'],))
        return {'ok': True}

    @app.delete('/api/memories/history/{exhibit_id}')
    def delete_history_item(exhibit_id: int, user=Depends(require_user)):
        with db() as c:
            c.execute('DELETE FROM memory_views WHERE user_id=? AND exhibit_id=?',
                      (user['id'], exhibit_id))
        return {'ok': True}

    def shape_reel(c, row, user):
        ids = json.loads(row['exhibit_ids'])
        items = [allowed(c, eid, user) for eid in ids]
        # A user may have saved another curator's public exhibit that was later made private.
        # Exclude that exhibit, and never return its title/media/metadata.
        return {'id': row['id'], 'title': row['title'], 'music': row['music'],
                'created_at': row['created_at'], 'items': [x for x in items if x]}

    @app.get('/api/memories/reels')
    def list_reels(user=Depends(require_user)):
        with db() as c:
            rows = c.execute('''SELECT * FROM memory_reels WHERE user_id=?
                ORDER BY created_at DESC,id DESC LIMIT 50''', (user['id'],)).fetchall()
            return [shape_reel(c, row, user) for row in rows]

    @app.post('/api/memories/reels', status_code=201)
    def create_reel(payload: ReelIn, user=Depends(require_user)):
        ids = list(dict.fromkeys(payload.exhibit_ids))
        with db() as c:
            count = c.execute('SELECT COUNT(*) FROM memory_reels WHERE user_id=?',
                              (user['id'],)).fetchone()[0]
            if count >= 50: fail(400, '最多保留50部回忆影片')
            for eid in ids:
                if not allowed(c, eid, user):
                    fail(404, '影片包含不存在或无权访问的展品')
            row = c.execute('''INSERT INTO memory_reels(user_id,title,exhibit_ids,music,created_at)
                VALUES(?,?,?,?,?)''', (user['id'],payload.title.strip(),
                                      json.dumps(ids), payload.music, now()))
            created = c.execute('SELECT * FROM memory_reels WHERE id=?', (row.lastrowid,)).fetchone()
            return shape_reel(c, created, user)

    @app.delete('/api/memories/reels/{reel_id}')
    def delete_reel(reel_id: int, user=Depends(require_user)):
        with db() as c:
            deleted = c.execute('DELETE FROM memory_reels WHERE id=? AND user_id=?',
                                (reel_id,user['id']))
            if deleted.rowcount == 0: fail(404, '影片不存在')
        return {'ok': True}